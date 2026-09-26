#!/usr/bin/env python3
"""Dependency-free static validation for the AI Source of Truth."""
from __future__ import annotations
import argparse
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
    for raw in read_text(path).splitlines():
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


def registered_section_targets(root: Path, section_name: str) -> Dict[str, str]:
    specs: Dict[str, str] = {}
    for section, identifier, target_text in switch_registry_entries(root):
        if section == section_name and (root / target_text).is_file():
            specs[identifier] = target_text
    return specs


def registered_control_specs(root: Path, errors: List[str]) -> Dict[str, set]:
    registry_path = root / "system" / "routing" / "switch_registry.md"
    specs: Dict[str, set] = {}
    for section, identifier, target_text in switch_registry_entries(root):
        if section != "registered_controls":
            continue
        target = root / target_text
        if not target.is_file():
            continue
        scalars, values = parse_control_manifest(read_text(target))
        rel = target.relative_to(root)
        control_id = scalars.get("control_id")
        default = scalars.get("control_default")
        if control_id is None:
            errors.append(f"{rel}: registered control requires frontmatter control_id")
        elif not NAME_RE.fullmatch(control_id):
            errors.append(f"{rel}: invalid control_id {control_id!r}")
        elif control_id != identifier:
            errors.append(
                f"{registry_path.relative_to(root)}: registered control {identifier!r} points to {target_text!r} "
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
        if identifier not in specs and values:
            specs[identifier] = set(values)
    return specs


def registered_format_specs(root: Path, errors: List[str]) -> Dict[str, str]:
    registry_path = root / "system" / "routing" / "switch_registry.md"
    specs: Dict[str, str] = {}
    for section, identifier, target_text in switch_registry_entries(root):
        if section != "formats":
            continue
        target = root / target_text
        if not target.is_file():
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
        top_keys, lists, scalars = parse_profile_manifest(read_text(path))
        rel = path.relative_to(root)
        unknown = top_keys - PROFILE_TOP_LEVEL
        if unknown:
            errors.append(f"{rel}: unsupported profile fields {sorted(unknown)}")
        controls = {key.split(".", 1)[1]: value for key, value in scalars.items() if key.startswith("controls.")}
        for key, value in controls.items():
            allowed = control_specs.get(key)
            if allowed is None:
                errors.append(f"{rel}: unsupported profile control {key!r}")
            elif value not in allowed:
                errors.append(f"{rel}: invalid value for controls.{key} ({value!r}); expected one of {sorted(allowed)}")
        for value in lists["formats"]:
            if not NAME_RE.fullmatch(value):
                errors.append(f"{rel}: invalid format identifier {value!r}")
            elif value not in format_specs:
                errors.append(f"{rel}: unresolved registered format reference {value!r}")
        tone = scalars.get("tone")
        if tone:
            if not NAME_RE.fullmatch(tone):
                errors.append(f"{rel}: invalid tone identifier {tone!r}")
            elif tone not in tone_specs:
                errors.append(f"{rel}: unresolved registered tone reference {tone!r}")
        depth = scalars.get("depth")
        if depth:
            if not NAME_RE.fullmatch(depth):
                errors.append(f"{rel}: invalid depth identifier {depth!r}")
            elif depth not in depth_specs:
                errors.append(f"{rel}: unresolved registered depth reference {depth!r}")
        refs = [("behavior", v, root / "system" / "behavior" / f"{v}.md") for v in lists["behaviors"]]
        if scalars.get("language.primary"):
            value = scalars["language.primary"]
            refs.append(("language", value, root / "workspace" / "presentation" / "languages" / f"{value}.md"))
        refs += [("language", v, root / "workspace" / "presentation" / "languages" / f"{v}.md") for v in lists["language.supporting"]]
        for kind, value, target in refs:
            if not NAME_RE.fullmatch(value):
                errors.append(f"{rel}: invalid {kind} identifier {value!r}")
            elif not target.is_file():
                errors.append(f"{rel}: unresolved {kind} reference {value!r} -> {target.relative_to(root)}")


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
    if not path.exists():
        return
    in_fence = False
    pending_scope: Optional[str] = None
    seen_scopes: Dict[str, str] = {}
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
