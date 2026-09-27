#!/usr/bin/env python3
"""Dependency-free static validation for the AI Source of Truth."""
from __future__ import annotations
import argparse
from dataclasses import dataclass
from hashlib import sha256
import re
import sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple

VALID_ACCESS = {"allow", "restricted", "deny"}
VALID_DECISION_STATUS = {"proposed", "accepted", "superseded", "deprecated"}
VALID_FORMAT_PLACEMENT = {"prefix", "body", "suffix"}
NAME_RE = re.compile(r"^[a-z0-9]+(?:_[a-z0-9]+)*$")
SCOPE_RE = re.compile(r"^[a-z0-9]+(?:_[a-z0-9]+)*(?:/[a-z0-9]+(?:_[a-z0-9]+)*)*$")
SWITCH_MAPPING_RE = re.compile(r"^\s*([a-z0-9_]+)\s+→\s+([a-z0-9_./]+\.md)\s*$")
EXTERNAL_FILENAMES = {"AGENTS.md", "CLAUDE.md"}
PROFILE_TOP_LEVEL = {"behaviors", "formats", "tone", "depth", "language", "controls"}
RAW_SECRET_KEYS = {"password", "bank_password", "api_token", "private_key", "recovery_code", "session_cookie", "bank_login_credentials", "card_cvv", "cvv", "full_payment_card_number", "payment_card_number"}
SAFE_SECRET_SENTINELS = {"not_stored", "none", "null", "redacted", "external_reference", "not_applicable"}
PRIMARY_DIRS = {"workspace", "system", "guides"}
LEGACY_TOP_LEVEL = {"routing", "context", "behavior", "formats", "tones", "depth", "languages", "profiles", "prompts", "migration", "adapters", "retrieval", "automation", "examples", "tests", "governance", "release", "validation"}


@dataclass(frozen=True)
class ProfileManifest:
    present: bool
    top_keys: frozenset[str]
    behaviors: tuple[str, ...]
    formats: tuple[str, ...]
    tone: Optional[str]
    depth: Optional[str]
    primary_language: Optional[str]
    supporting_languages: tuple[str, ...]
    controls: tuple[tuple[str, str], ...]
    body: str
    syntax_errors: tuple[str, ...]


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def clean_scalar(value: str) -> str:
    return value.strip().strip("\"'")


def frontmatter_lines(text: str) -> Optional[List[str]]:
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return None
    for i in range(1, len(lines)):
        if lines[i].strip() == "---":
            return lines[1:i]
    return None


def simple_frontmatter(text: str) -> Dict[str, str]:
    lines = frontmatter_lines(text)
    if lines is None:
        return {}
    result: Dict[str, str] = {}
    for raw in lines:
        if raw.startswith(" ") or ":" not in raw:
            continue
        key, value = raw.split(":", 1)
        result[key.strip()] = clean_scalar(value)
    return result


def parse_control_manifest(text: str) -> Tuple[Dict[str, str], List[str]]:
    lines = frontmatter_lines(text)
    if lines is None:
        return {}, []
    scalars: Dict[str, str] = {}
    values: List[str] = []
    current: Optional[str] = None
    for raw in lines:
        if not raw.strip() or raw.lstrip().startswith("#"):
            continue
        indent = len(raw) - len(raw.lstrip(" "))
        stripped = raw.strip()
        if indent == 0 and ":" in stripped:
            key, value = stripped.split(":", 1)
            key, value = key.strip(), clean_scalar(value)
            current = key
            if value:
                scalars[key] = value
            continue
        if current == "control_values" and stripped.startswith("- "):
            values.append(clean_scalar(stripped[2:]))
    return scalars, values


def switch_registry_entries(root: Path) -> List[Tuple[str, str, str]]:
    path = root / "system" / "routing" / "switch_registry.md"
    if not path.exists():
        return []
    entries: List[Tuple[str, str, str]] = []
    section = ""
    in_fence = False
    try:
        lines = read_text(path).splitlines()
    except (OSError, UnicodeError):
        return []
    for raw in lines:
        stripped = raw.strip()
        if stripped.startswith("## "):
            section = stripped[3:].strip()
            in_fence = False
            continue
        if stripped.startswith("```"):
            in_fence = not in_fence
            continue
        if not in_fence:
            continue
        match = SWITCH_MAPPING_RE.match(raw)
        if match:
            entries.append((section, match.group(1), match.group(2)))
    return entries


def _safe_canonical_file(root: Path, path: Path) -> bool:
    try:
        return path.is_file() and not path.is_symlink() and path.resolve().is_relative_to(root.resolve())
    except OSError:
        return False


def registered_section_targets(root: Path, section_name: str) -> Dict[str, str]:
    specs: Dict[str, str] = {}
    for section, identifier, target_text in switch_registry_entries(root):
        if section == section_name and _safe_canonical_file(root, root / target_text):
            specs[identifier] = target_text
    return specs


def registered_control_specs(root: Path, errors: List[str]) -> Dict[str, set]:
    specs: Dict[str, set] = {}
    for section, identifier, target_text in switch_registry_entries(root):
        if section != "registered_controls":
            continue
        target = root / target_text
        if not _safe_canonical_file(root, target):
            continue
        source = read_text(target)
        local_errors = validate_control_source(root, target, identifier, source, target_text)
        errors.extend(local_errors)
        _, values = parse_control_manifest(source)
        if identifier not in specs and values and not local_errors:
            specs[identifier] = set(values)
    return specs


def validate_control_source(
    root: Path,
    path: Path,
    identifier: str,
    source: str,
    target_text: Optional[str] = None,
) -> List[str]:
    """Validate one registered control target with validator-owned rules."""
    errors: List[str] = []
    scalars, values = parse_control_manifest(source)
    rel = path.relative_to(root)
    control_id = scalars.get("control_id")
    default = scalars.get("control_default")
    if control_id is None:
        errors.append(f"{rel}: registered control requires frontmatter control_id")
    elif not NAME_RE.fullmatch(control_id):
        errors.append(f"{rel}: invalid control_id {control_id!r}")
    elif control_id != identifier:
        target = target_text or rel.as_posix()
        errors.append(
            f"system/routing/switch_registry.md: registered control {identifier!r} points to {target!r} "
            f"whose control_id is {control_id!r}"
        )
    if not values:
        errors.append(f"{rel}: registered control requires non-empty control_values")
    elif len(values) != len(set(values)):
        errors.append(f"{rel}: duplicate entries in control_values")
    if default is None:
        errors.append(f"{rel}: registered control requires control_default")
    elif values and default not in values:
        errors.append(f"{rel}: control_default {default!r} is not present in control_values {values!r}")
    return errors


def registered_format_specs(root: Path, errors: List[str]) -> Dict[str, str]:
    registry_path = root / "system" / "routing" / "switch_registry.md"
    specs: Dict[str, str] = {}
    for section, identifier, target_text in switch_registry_entries(root):
        if section != "formats":
            continue
        target = root / target_text
        if not _safe_canonical_file(root, target):
            continue
        metadata = simple_frontmatter(read_text(target))
        rel = target.relative_to(root)
        format_id = metadata.get("format_id")
        placement = metadata.get("placement")
        if format_id is None:
            errors.append(f"{rel}: registered format requires frontmatter format_id")
        elif not NAME_RE.fullmatch(format_id):
            errors.append(f"{rel}: invalid format_id {format_id!r}")
        elif format_id != identifier:
            errors.append(
                f"{registry_path.relative_to(root)}: registered format {identifier!r} points to {target_text!r} "
                f"whose format_id is {format_id!r}"
            )
        if placement is None:
            errors.append(f"{rel}: registered format requires placement")
        elif placement not in VALID_FORMAT_PLACEMENT:
            errors.append(
                f"{rel}: invalid format placement {placement!r}; expected one of {sorted(VALID_FORMAT_PLACEMENT)}"
            )
        if identifier not in specs and format_id == identifier and placement in VALID_FORMAT_PLACEMENT:
            specs[identifier] = target_text
    return specs


def canonical_context_files(root: Path) -> List[Path]:
    files: List[Path] = []
    base = root / "workspace" / "context"
    for scope in (base / "personal", base / "organizations"):
        if scope.exists():
            files.extend(sorted(scope.rglob("*.md")))
    return files


def validate_layout(root: Path, errors: List[str]) -> None:
    for name in PRIMARY_DIRS:
        if not (root / name).is_dir():
            errors.append(f"missing primary repository directory {name!r}")
    for name in LEGACY_TOP_LEVEL:
        if (root / name).exists():
            errors.append(f"legacy top-level area must be migrated under workspace/system/guides: {name!r}")


def validate_names(root: Path, errors: List[str]) -> None:
    for area_name in PRIMARY_DIRS:
        area = root / area_name
        if not area.exists():
            continue
        for path in area.rglob("*"):
            rel = path.relative_to(root)
            if "__pycache__" in rel.parts:
                continue
            directory_parts = rel.parts[:-1] if path.is_file() else rel.parts
            for part in directory_parts:
                if part.startswith("."):
                    continue
                if not NAME_RE.fullmatch(part):
                    errors.append(f"{rel}: directory segment {part!r} is not lowercase_snake_case")
                    break
            if path.is_file() and path.name not in EXTERNAL_FILENAMES and not NAME_RE.fullmatch(path.stem):
                errors.append(f"{rel}: filename stem {path.stem!r} is not lowercase_snake_case")


def validate_access(root: Path, errors: List[str]) -> None:
    for path in canonical_context_files(root):
        access = simple_frontmatter(read_text(path)).get("ai_access")
        if access not in VALID_ACCESS:
            errors.append(f"{path.relative_to(root)}: missing or invalid ai_access ({access!r})")


def validate_core_isolation(root: Path, mode: str, errors: List[str]) -> None:
    if mode != "core":
        return
    base = root / "workspace" / "context"
    for scope in (base / "personal", base / "organizations"):
        if scope.exists() and any(scope.rglob("*.md")):
            errors.append(f"{scope.relative_to(root)}: real canonical context is forbidden in generic Core")


def parse_profile_manifest(text: str) -> Tuple[set, Dict[str, List[str]], Dict[str, str]]:
    lines = frontmatter_lines(text)
    if lines is None:
        return set(), {}, {}
    top_keys = set()
    lists: Dict[str, List[str]] = {"behaviors": [], "formats": [], "language.supporting": []}
    scalars: Dict[str, str] = {}
    current: Optional[str] = None
    language_sub: Optional[str] = None
    for raw in lines:
        if not raw.strip() or raw.lstrip().startswith("#"):
            continue
        indent = len(raw) - len(raw.lstrip(" "))
        stripped = raw.strip()
        if indent == 0 and ":" in stripped:
            key, value = stripped.split(":", 1)
            key, value = key.strip(), clean_scalar(value)
            top_keys.add(key)
            current = key
            language_sub = None
            if value:
                scalars[key] = value
            continue
        if current == "language" and indent == 2 and ":" in stripped:
            key, value = stripped.split(":", 1)
            key, value = key.strip(), clean_scalar(value)
            language_sub = key
            if value:
                scalars[f"language.{key}"] = value
            continue
        if current == "controls" and indent == 2 and ":" in stripped:
            key, value = stripped.split(":", 1)
            key, value = key.strip(), clean_scalar(value)
            scalars[f"controls.{key}"] = value
            continue
        if stripped.startswith("- "):
            value = clean_scalar(stripped[2:])
            if current in {"behaviors", "formats"}:
                lists[current].append(value)
            elif current == "language" and language_sub == "supporting":
                lists["language.supporting"].append(value)
    return top_keys, lists, scalars


def _profile_syntax_errors(text: str) -> tuple[str, ...]:
    lines = frontmatter_lines(text)
    if lines is None:
        return ()
    errors: List[str] = []
    current: Optional[str] = None
    language_sub: Optional[str] = None
    top_seen: set[str] = set()
    language_seen: set[str] = set()
    controls_seen: set[str] = set()
    for number, raw in enumerate(lines, 2):
        stripped = raw.strip()
        if not stripped:
            continue
        if stripped.startswith("#"):
            errors.append(f"line {number}: comments are forbidden in Profile manifests")
            continue
        indent = len(raw) - len(raw.lstrip(" "))
        if indent == 0:
            if ":" not in stripped:
                errors.append(f"line {number}: malformed Profile field")
                current = None
                continue
            key, value = stripped.split(":", 1)
            current, value, language_sub = key.strip(), clean_scalar(value), None
            if current in top_seen:
                errors.append(f"line {number}: duplicate Profile field {current!r}")
            top_seen.add(current)
            if current in {"behaviors", "formats"} and value not in {"", "[]"}:
                errors.append(f"line {number}: {current} must be a list")
            elif current in {"language", "controls"} and value:
                errors.append(f"line {number}: {current} must be a mapping")
            elif current in {"tone", "depth"} and not value:
                errors.append(f"line {number}: {current} requires one value")
            continue
        if indent == 2 and current in {"behaviors", "formats"} and stripped.startswith("- "):
            if not clean_scalar(stripped[2:]):
                errors.append(f"line {number}: empty {current} item")
            continue
        if indent == 2 and current == "language" and ":" in stripped:
            key, value = stripped.split(":", 1)
            language_sub, value = key.strip(), clean_scalar(value)
            if language_sub in language_seen:
                errors.append(f"line {number}: duplicate language field {language_sub!r}")
            language_seen.add(language_sub)
            if language_sub == "primary" and not value:
                errors.append(f"line {number}: language.primary requires one value")
            elif language_sub == "supporting" and value not in {"", "[]"}:
                errors.append(f"line {number}: language.supporting must be a list")
            elif language_sub not in {"primary", "supporting"}:
                errors.append(f"line {number}: unsupported language field {language_sub!r}")
            continue
        if indent == 4 and current == "language" and language_sub == "supporting" and stripped.startswith("- "):
            if not clean_scalar(stripped[2:]):
                errors.append(f"line {number}: empty language.supporting item")
            continue
        if indent == 2 and current == "controls" and ":" in stripped:
            key, value = stripped.split(":", 1)
            key = key.strip()
            if key in controls_seen:
                errors.append(f"line {number}: duplicate Profile control {key!r}")
            controls_seen.add(key)
            if not key or not clean_scalar(value):
                errors.append(f"line {number}: Profile control requires an identity and value")
            continue
        errors.append(f"line {number}: unsupported Profile structure")
    return tuple(errors)


def read_profile_manifest(source: str) -> ProfileManifest:
    top_keys, lists, scalars = parse_profile_manifest(source)
    lines = source.splitlines()
    closing = next(
        (index for index, line in enumerate(lines[1:], 1) if line.strip() == "---"),
        None,
    )
    body = "\n".join(lines[closing + 1 :]) if closing is not None else ""
    return ProfileManifest(
        frontmatter_lines(source) is not None,
        frozenset(top_keys),
        tuple(lists.get("behaviors", [])),
        tuple(lists.get("formats", [])),
        scalars.get("tone"),
        scalars.get("depth"),
        scalars.get("language.primary"),
        tuple(lists.get("language.supporting", [])),
        tuple(
            (key.split(".", 1)[1], value)
            for key, value in scalars.items()
            if key.startswith("controls.")
        ),
        body,
        _profile_syntax_errors(source),
    )


def _validate_profile_manifest(
    root: Path,
    path: Path,
    manifest: ProfileManifest,
    control_specs: Dict[str, set],
    format_specs: Dict[str, str],
    tone_specs: Dict[str, str],
    depth_specs: Dict[str, str],
    errors: List[str],
) -> None:
    rel = path.relative_to(root)
    if not manifest.present:
        errors.append(f"{rel}: profile requires YAML frontmatter")
        return
    if manifest.body.strip():
        errors.append(f"{rel}: Profile must remain a frontmatter-only composition manifest; body content is forbidden")
    errors.extend(f"{rel}: {error}" for error in manifest.syntax_errors)
    unknown = manifest.top_keys - PROFILE_TOP_LEVEL
    if unknown:
        errors.append(f"{rel}: unsupported profile fields {sorted(unknown)}")
    for key, value in manifest.controls:
        allowed = control_specs.get(key)
        if allowed is None:
            errors.append(f"{rel}: unsupported profile control {key!r}")
        elif value not in allowed:
            errors.append(f"{rel}: invalid value for controls.{key} ({value!r}); expected one of {sorted(allowed)}")
    for value in manifest.formats:
        if not NAME_RE.fullmatch(value):
            errors.append(f"{rel}: invalid format identifier {value!r}")
        elif value not in format_specs:
            errors.append(f"{rel}: unresolved registered format reference {value!r}")
    for field, value, specs in (
        ("tone", manifest.tone, tone_specs),
        ("depth", manifest.depth, depth_specs),
    ):
        if not value:
            continue
        if not NAME_RE.fullmatch(value):
            errors.append(f"{rel}: invalid {field} identifier {value!r}")
        elif value not in specs:
            errors.append(f"{rel}: unresolved registered {field} reference {value!r}")
    refs = [("behavior", value, root / "system/behavior" / f"{value}.md") for value in manifest.behaviors]
    if manifest.primary_language:
        refs.append(
            (
                "language",
                manifest.primary_language,
                root / "workspace/presentation/languages" / f"{manifest.primary_language}.md",
            )
        )
    refs.extend(
        ("language", value, root / "workspace/presentation/languages" / f"{value}.md")
        for value in manifest.supporting_languages
    )
    for kind, value, target in refs:
        if not NAME_RE.fullmatch(value):
            errors.append(f"{rel}: invalid {kind} identifier {value!r}")
        elif not _safe_canonical_file(root, target):
            errors.append(f"{rel}: unresolved {kind} reference {value!r} -> {target.relative_to(root)}")


def validate_profile_source(root: Path, path: Path, source: str) -> List[str]:
    """Validate one proposed Profile with the repository-owned rules."""
    errors: List[str] = []
    control_specs = registered_control_specs(root, errors)
    format_specs = registered_format_specs(root, errors)
    _validate_profile_manifest(
        root,
        path,
        read_profile_manifest(source),
        control_specs,
        format_specs,
        registered_section_targets(root, "tones"),
        registered_section_targets(root, "depths"),
        errors,
    )
    return errors


def profile_validation_state_digest(root: Path, source: str) -> str:
    """Bind a Profile preview to its canonical inventory and dependencies."""
    root = root.resolve()
    manifest = read_profile_manifest(source)
    profiles = root / "workspace" / "profiles"
    paths = list(profiles.glob("*.md")) if profiles.is_dir() and not profiles.is_symlink() else []
    registry = root / "system" / "routing" / "switch_registry.md"
    paths.append(registry)
    paths.extend(root / target for _, _, target in switch_registry_entries(root))
    paths.extend(root / "system" / "behavior" / f"{name}.md" for name in manifest.behaviors)
    languages = ([manifest.primary_language] if manifest.primary_language else []) + list(manifest.supporting_languages)
    paths.extend(root / "workspace" / "presentation" / "languages" / f"{name}.md" for name in languages)

    digest = sha256()
    for path in sorted(set(paths), key=lambda item: item.as_posix()):
        try:
            relative = path.relative_to(root).as_posix()
            content = path.read_bytes() if _safe_canonical_file(root, path) else b"<unavailable>"
        except (OSError, ValueError):
            relative, content = "<unsafe>", b"<unavailable>"
        digest.update(relative.encode("utf-8") + b"\0" + content + b"\0")
    return digest.hexdigest()


def validate_profiles(
    root: Path,
    control_specs: Dict[str, set],
    format_specs: Dict[str, str],
    tone_specs: Dict[str, str],
    depth_specs: Dict[str, str],
    errors: List[str],
) -> None:
    profiles = root / "workspace" / "profiles"
    if not profiles.exists():
        return
    for path in sorted(profiles.glob("*.md")):
        _validate_profile_manifest(
            root,
            path,
            read_profile_manifest(read_text(path)),
            control_specs,
            format_specs,
            tone_specs,
            depth_specs,
            errors,
        )


def validate_switch_registry(root: Path, errors: List[str]) -> None:
    path = root / "system" / "routing" / "switch_registry.md"
    if not path.exists():
        return
    seen_ids: Dict[Tuple[str, str], str] = {}
    seen_targets: Dict[str, Tuple[str, str]] = {}
    for section, identifier, target_text in switch_registry_entries(root):
        if target_text.startswith("workspace/profiles/"):
            errors.append(
                f"{path.relative_to(root)}: profile target {target_text!r} must remain self-addressing; "
                "profiles are not registered in the flat switch registry"
            )
        identity_key = (section, identifier)
        previous_target = seen_ids.get(identity_key)
        if previous_target is not None:
            errors.append(
                f"{path.relative_to(root)}: duplicate registry identifier {identifier!r} in section {section!r} "
                f"maps to both {previous_target!r} and {target_text!r}"
            )
        else:
            seen_ids[identity_key] = target_text
        previous_registration = seen_targets.get(target_text)
        if previous_registration is not None and previous_registration != identity_key:
            previous_section, previous_identifier = previous_registration
            errors.append(
                f"{path.relative_to(root)}: target {target_text!r} is registered by both "
                f"{previous_section!r}/{previous_identifier!r} and {section!r}/{identifier!r}; aliases are forbidden"
            )
        else:
            seen_targets[target_text] = identity_key
        if not (root / target_text).is_file():
            errors.append(f"{path.relative_to(root)}: missing target {target_text!r}")

    registry_covered_dirs = (
        root / "workspace" / "presentation" / "formats",
        root / "workspace" / "presentation" / "tones",
        root / "workspace" / "presentation" / "depth",
    )
    registered_targets = set(seen_targets)
    for base in registry_covered_dirs:
        if not base.exists():
            continue
        for target in sorted(base.glob("*.md")):
            if target.name == "readme.md":
                continue
            target_text = target.relative_to(root).as_posix()
            if target_text not in registered_targets:
                errors.append(
                    f"{path.relative_to(root)}: registry-covered target {target_text!r} "
                    "has no switch_registry entry"
                )


def validate_context_registry(root: Path, errors: List[str]) -> None:
    path = root / "system" / "routing" / "context_registry.md"
    seen_scopes: Dict[str, str] = {}
    if path.exists():
        in_fence = False
        pending_scope: Optional[str] = None
        for raw in read_text(path).splitlines():
            stripped = raw.strip()
            if stripped.startswith("```"):
                in_fence = not in_fence
                pending_scope = None
                continue
            if not in_fence or not stripped:
                continue
            if stripped.startswith("→ "):
                target_text = stripped[2:].strip()
                if pending_scope is None:
                    continue
                if not SCOPE_RE.fullmatch(pending_scope):
                    errors.append(f"{path.relative_to(root)}: invalid runtime scope identifier {pending_scope!r}")
                previous_target = seen_scopes.get(pending_scope)
                if previous_target is not None:
                    errors.append(
                        f"{path.relative_to(root)}: duplicate runtime scope {pending_scope!r} "
                        f"maps to both {previous_target!r} and {target_text!r}"
                    )
                else:
                    seen_scopes[pending_scope] = target_text
                if not target_text.startswith("workspace/context/"):
                    pending_scope = None
                    continue
                if "guides/developer/examples/" in target_text:
                    errors.append(f"{path.relative_to(root)}: example path registered as runtime scope")
                if not (root / target_text.rstrip("/")).is_dir():
                    errors.append(f"{path.relative_to(root)}: missing scope target {target_text!r}")
                pending_scope = None
                continue
            if "→" not in stripped and not stripped.startswith("#"):
                pending_scope = stripped

    expected_scopes: Dict[str, str] = {}
    personal = root / "workspace" / "context" / "personal"
    if personal.is_dir() and any(personal.glob("*.md")):
        expected_scopes["personal"] = "workspace/context/personal/"
    personal_projects = personal / "projects"
    if personal_projects.is_dir():
        for project_file in sorted(personal_projects.rglob("project.md")):
            project_path = project_file.parent.relative_to(personal_projects).as_posix()
            expected_scopes[f"personal/projects/{project_path}"] = (
                f"workspace/context/personal/projects/{project_path}/"
            )

    organizations = root / "workspace" / "context" / "organizations"
    if organizations.is_dir():
        for organization in sorted(path for path in organizations.iterdir() if path.is_dir()):
            if any(organization.glob("*.md")):
                expected_scopes[f"org/{organization.name}"] = (
                    f"workspace/context/organizations/{organization.name}/"
                )
            projects = organization / "projects"
            if not projects.is_dir():
                continue
            for project_file in sorted(projects.rglob("project.md")):
                project_path = project_file.parent.relative_to(projects).as_posix()
                expected_scopes[f"org/{organization.name}/projects/{project_path}"] = (
                    f"workspace/context/organizations/{organization.name}/projects/{project_path}/"
                )

    for scope, target in expected_scopes.items():
        registered_target = seen_scopes.get(scope)
        if registered_target is None:
            errors.append(f"{target}: unregistered canonical scope {scope!r}")
        elif registered_target.rstrip("/") != target.rstrip("/"):
            errors.append(
                f"{path.relative_to(root)}: canonical scope {scope!r} maps to {registered_target!r}; "
                f"expected {target!r}"
            )


def validate_decisions(root: Path, errors: List[str]) -> None:
    for base in (root / "workspace" / "context", root / "guides" / "developer" / "examples" / "context"):
        if not base.exists():
            continue
        for path in sorted(base.rglob("*.md")):
            if "decisions" not in path.parts:
                continue
            status = simple_frontmatter(read_text(path)).get("decision_status")
            if status not in VALID_DECISION_STATUS:
                errors.append(f"{path.relative_to(root)}: missing or invalid decision_status ({status!r})")


def validate_project_ownership(root: Path, errors: List[str]) -> None:
    project_roots = [root / "workspace" / "context" / "personal" / "projects"]
    organizations = root / "workspace" / "context" / "organizations"
    if organizations.is_dir():
        project_roots.extend(
            organization / "projects"
            for organization in organizations.iterdir()
            if organization.is_dir()
        )

    for projects in project_roots:
        if not projects.is_dir():
            continue
        for context_file in sorted(projects.rglob("*.md")):
            if context_file.name == "readme.md":
                continue
            directory = context_file.parent
            while directory.is_relative_to(projects):
                if (directory / "project.md").is_file():
                    break
                if directory == projects:
                    errors.append(
                        f"{context_file.relative_to(root)}: project context without project.md owner"
                    )
                    break
                directory = directory.parent


def validate_secret_guard(root: Path, errors: List[str]) -> None:
    assignment = re.compile(r"^\s*[-*]?\s*([a-z0-9_]+)\s*[:=]\s*(.+?)\s*$", re.I)
    for path in canonical_context_files(root):
        for n, raw in enumerate(read_text(path).splitlines(), 1):
            match = assignment.match(raw)
            if not match or match.group(1).lower() not in RAW_SECRET_KEYS:
                continue
            value = clean_scalar(match.group(2)).strip("`").lower()
            if value in SAFE_SECRET_SENTINELS or value.startswith("<"):
                continue
            errors.append(f"{path.relative_to(root)}:{n}: possible raw secret assigned to {match.group(1).lower()!r}")


def infer_mode(root: Path) -> str:
    personal = root / "workspace" / "context" / "personal"
    return "personal" if personal.exists() and any(personal.rglob("*.md")) else "core"


def run(root: Path, mode: str) -> List[str]:
    errors: List[str] = []
    control_specs = registered_control_specs(root, errors)
    format_specs = registered_format_specs(root, errors)
    tone_specs = registered_section_targets(root, "tones")
    depth_specs = registered_section_targets(root, "depths")
    validate_layout(root, errors)
    validate_names(root, errors)
    validate_core_isolation(root, mode, errors)
    validate_access(root, errors)
    validate_profiles(root, control_specs, format_specs, tone_specs, depth_specs, errors)
    validate_switch_registry(root, errors)
    validate_context_registry(root, errors)
    validate_decisions(root, errors)
    validate_project_ownership(root, errors)
    validate_secret_guard(root, errors)
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[2])
    parser.add_argument("--mode", choices=("auto", "core", "personal"), default="auto")
    args = parser.parse_args()
    root = args.root.resolve()
    mode = infer_mode(root) if args.mode == "auto" else args.mode
    errors = run(root, mode)
    if errors:
        print(f"V1 static validation FAILED ({len(errors)} issue(s), mode={mode})")
        for error in errors:
            print(f"- {error}")
        return 1
    print(f"V1 static validation PASSED (mode={mode})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
