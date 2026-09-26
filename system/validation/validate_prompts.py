#!/usr/bin/env python3
"""Dependency-free structural validation for reusable prompt templates."""
from __future__ import annotations
from hashlib import sha256
import re
import sys
from pathlib import Path

if __package__:
    from .validate_v1 import switch_registry_entries
else:
    from validate_v1 import switch_registry_entries

VALID_STATUS = {"active", "draft", "deprecated"}
NAME_RE = re.compile(r"^[a-z0-9]+(?:_[a-z0-9]+)*$")
VAR_RE = re.compile(r"\{\{([a-z0-9]+(?:_[a-z0-9]+)*)\}\}")
ALLOWED_FIELDS = {"prompt_status", "prompt_tags", "prompt_profiles", "prompt_formats", "prompt_tone", "prompt_depth", "required_params", "optional_params", "owned_assets"}
LIST_FIELDS = {"prompt_tags", "prompt_profiles", "prompt_formats", "required_params", "optional_params", "owned_assets"}
RAW_SECRET_KEYS = {"password", "api_token", "private_key", "recovery_code", "session_cookie", "bank_login_credentials", "card_cvv", "cvv"}
SAFE_SECRET_SENTINELS = {"not_stored", "none", "null", "redacted", "external_reference", "not_applicable"}
MAX_FRONTMATTER_LINES = 256


def text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def clean(value: str) -> str:
    return value.strip().strip("\"'")


def frontmatter(src: str):
    lines = src.splitlines()
    if not lines or lines[0].strip() != "---":
        return None, src
    for i in range(1, len(lines)):
        if lines[i].strip() == "---":
            return lines[1:i], "\n".join(lines[i + 1:]).lstrip("\n")
    return None, src


def manifest(src: str):
    fm, body = frontmatter(src)
    lists = {key: [] for key in LIST_FIELDS}
    scalars = {}
    keys = set()
    current = None
    if fm is None:
        return keys, lists, scalars, body
    for raw in fm:
        if not raw.strip() or raw.lstrip().startswith("#"):
            continue
        indent = len(raw) - len(raw.lstrip(" "))
        stripped = raw.strip()
        if indent == 0 and ":" in stripped:
            key, value = stripped.split(":", 1)
            key, value = key.strip(), clean(value)
            keys.add(key)
            current = key
            if value and value != "[]":
                scalars[key] = value
            continue
        if stripped.startswith("- ") and current in LIST_FIELDS:
            lists[current].append(clean(stripped[2:]))
    return keys, lists, scalars, body


def read_manifest(path: Path) -> tuple[set[str], dict[str, list[str]], dict[str, str]]:
    """Read and parse frontmatter without loading the prompt body."""
    lines: list[str] = []
    try:
        with path.open("rb") as source:
            first = source.readline().decode("utf-8")
            if first.strip() != "---":
                return set(), {key: [] for key in LIST_FIELDS}, {}
            lines.append(first)
            for _ in range(MAX_FRONTMATTER_LINES):
                raw = source.readline()
                if not raw:
                    break
                line = raw.decode("utf-8")
                lines.append(line)
                if line.strip() == "---":
                    keys, lists, scalars, _ = manifest("".join(lines))
                    return keys, lists, scalars
    except (OSError, UnicodeDecodeError):
        pass
    return set(), {key: [] for key in LIST_FIELDS}, {}


def prompt_files(root: Path):
    out = []
    base = root / "workspace" / "prompts"
    if base.exists():
        for path in sorted(base.rglob("*.md")):
            if path.name == "readme.md" or "_assets" in path.relative_to(base).parts:
                continue
            out.append((path, True))
    examples = root / "guides" / "developer" / "examples" / "prompts"
    if examples.exists():
        for path in sorted(examples.rglob("*.md")):
            if path.name == "readme.md":
                continue
            out.append((path, False))
    return out


def _registry_ids(root: Path, section_name: str) -> set[str]:
    return {
        identifier
        for section, identifier, target_text in switch_registry_entries(root)
        if section == section_name
        and (root / target_text).is_file()
        and not (root / target_text).is_symlink()
        and (root / target_text).resolve().is_relative_to(root.resolve())
    }


def validation_state_digest(root: Path, source: str) -> str:
    """Bind a preview to prompt inventory and validation dependencies."""
    root = root.resolve()
    _, lists, scalars, _ = manifest(source)
    paths = [path for path, canonical in prompt_files(root) if canonical]
    registry = root / "system/routing/switch_registry.md"
    paths.append(registry)
    paths.extend(root / "workspace/profiles" / f"{name}.md" for name in lists["prompt_profiles"])
    entries = {
        (section, identifier): root / target
        for section, identifier, target in switch_registry_entries(root)
    }
    for section, values in (
        ("formats", lists["prompt_formats"]),
        ("tones", [scalars.get("prompt_tone")]),
        ("depths", [scalars.get("prompt_depth")]),
    ):
        paths.extend(entries[(section, value)] for value in values if value and (section, value) in entries)
    digest = sha256()
    for path in sorted(set(paths), key=lambda item: item.as_posix()):
        try:
            relative = path.relative_to(root).as_posix()
            safe = not path.is_symlink() and path.resolve().is_relative_to(root)
            content = path.read_bytes() if safe and path.is_file() else b"<unavailable>"
        except (OSError, ValueError):
            relative, content = "<unsafe>", b"<unavailable>"
        digest.update(relative.encode("utf-8") + b"\0" + content + b"\0")
    return digest.hexdigest()


def _validate_source(
    root: Path,
    path: Path,
    canonical: bool,
    format_ids: set[str],
    tone_ids: set[str],
    depth_ids: set[str],
    errors: list[str],
    src: str,
):
    rel = path.relative_to(root)
    keys, lists, scalars, body = manifest(src)
    if not keys:
        errors.append(f"{rel}: prompt template requires YAML frontmatter")
        return
    if canonical and path.name == "readme.md":
        errors.append(f"{rel}: 'readme' is reserved for prompt documentation")
    unknown = keys - ALLOWED_FIELDS
    if unknown:
        errors.append(f"{rel}: unsupported prompt fields {sorted(unknown)}")
    if scalars.get("prompt_status") not in VALID_STATUS:
        errors.append(f"{rel}: missing or invalid prompt_status ({scalars.get('prompt_status')!r})")
    prompt_root = root / ("workspace/prompts" if canonical else "guides/developer/examples/prompts")
    for part in path.with_suffix("").relative_to(prompt_root).parts:
        if not NAME_RE.fullmatch(part):
            errors.append(f"{rel}: invalid prompt path segment {part!r}")
    required = set(lists["required_params"])
    optional = set(lists["optional_params"])
    for field in ("required_params", "optional_params"):
        values = lists[field]
        if len(values) != len(set(values)):
            errors.append(f"{rel}: duplicate entries in {field}")
        for value in values:
            if not NAME_RE.fullmatch(value):
                errors.append(f"{rel}: invalid parameter identifier {value!r}")
            if value == "input":
                errors.append(f"{rel}: reserved parameter 'input' must not be declared")
    overlap = required & optional
    if overlap:
        errors.append(f"{rel}: parameters both required and optional {sorted(overlap)}")
    variables = set(VAR_RE.findall(body))
    undeclared = variables - required - optional - {"input"}
    stale = (required | optional) - variables
    if undeclared:
        errors.append(f"{rel}: undeclared template variables {sorted(undeclared)}")
    if stale:
        errors.append(f"{rel}: declared parameters not used in template {sorted(stale)}")
    for tag in lists["prompt_tags"]:
        if not NAME_RE.fullmatch(tag):
            errors.append(f"{rel}: invalid prompt tag {tag!r}")
    for value in lists["prompt_formats"]:
        if not NAME_RE.fullmatch(value):
            errors.append(f"{rel}: invalid format identifier {value!r}")
        elif value not in format_ids:
            errors.append(f"{rel}: unresolved registered format reference {value!r}")
    tone = scalars.get("prompt_tone")
    if tone:
        if not NAME_RE.fullmatch(tone):
            errors.append(f"{rel}: invalid tone identifier {tone!r}")
        elif tone not in tone_ids:
            errors.append(f"{rel}: unresolved registered tone reference {tone!r}")
    depth = scalars.get("prompt_depth")
    if depth:
        if not NAME_RE.fullmatch(depth):
            errors.append(f"{rel}: invalid depth identifier {depth!r}")
        elif depth not in depth_ids:
            errors.append(f"{rel}: unresolved registered depth reference {depth!r}")
    refs = [("profile", value, root / "workspace" / "profiles" / f"{value}.md") for value in lists["prompt_profiles"]]
    for kind, value, target in refs:
        if not NAME_RE.fullmatch(value):
            errors.append(f"{rel}: invalid {kind} identifier {value!r}")
        elif not target.is_file():
            errors.append(f"{rel}: unresolved {kind} reference {value!r}")
    if canonical:
        identity = path.relative_to(root / "workspace" / "prompts").with_suffix("").as_posix()
        prefix = (root / "workspace" / "prompts" / "_assets" / identity).resolve()
        for owned in lists["owned_assets"]:
            asset = (root / owned).resolve()
            if not asset.is_relative_to(prefix):
                errors.append(f"{rel}: owned asset outside workspace/prompts/_assets/{identity}/ ({owned!r})")
            elif not asset.exists():
                errors.append(f"{rel}: owned asset does not exist ({owned!r})")
    elif lists["owned_assets"]:
        errors.append(f"{rel}: example prompts must not claim real owned_assets")
    assignment = re.compile(r"^\s*[-*]?\s*([a-z0-9_]+)\s*[:=]\s*(.+?)\s*$", re.I)
    for n, raw in enumerate(src.splitlines(), 1):
        match = assignment.match(raw)
        if not match or match.group(1).lower() not in RAW_SECRET_KEYS:
            continue
        value = clean(match.group(2)).strip("`").lower()
        if value in SAFE_SECRET_SENTINELS or value.startswith("<") or value.startswith("{{"):
            continue
        errors.append(f"{rel}:{n}: possible raw secret assignment to {match.group(1).lower()!r}")


def validate_file(
    root: Path,
    path: Path,
    canonical: bool,
    format_ids: set[str],
    tone_ids: set[str],
    depth_ids: set[str],
    errors: list[str],
):
    try:
        source = text(path)
    except (OSError, UnicodeError):
        errors.append(f"{path.relative_to(root)}: prompt file is unreadable")
        return
    _validate_source(root, path, canonical, format_ids, tone_ids, depth_ids, errors, source)


def validate_source(root: Path, path: Path, source: str, canonical: bool = True) -> list[str]:
    """Validate proposed prompt content without writing it."""
    errors: list[str] = []
    _validate_source(
        root,
        path,
        canonical,
        _registry_ids(root, "formats"),
        _registry_ids(root, "tones"),
        _registry_ids(root, "depths"),
        errors,
        source,
    )
    return errors


def validate_path(root: Path, path: Path, canonical: bool = True) -> list[str]:
    """Validate one prompt with the same rules as the repository validator."""
    try:
        source = text(path)
    except (OSError, UnicodeError):
        return [f"{path.relative_to(root)}: prompt file is unreadable"]
    return validate_source(root, path, source, canonical)


def run(root: Path) -> list[str]:
    errors: list[str] = []
    format_ids = _registry_ids(root, "formats")
    tone_ids = _registry_ids(root, "tones")
    depth_ids = _registry_ids(root, "depths")
    for path, canonical in prompt_files(root):
        validate_file(root, path, canonical, format_ids, tone_ids, depth_ids, errors)
    return errors


def main() -> int:
    root = Path(__file__).resolve().parents[2]
    errors = run(root)
    if errors:
        print(f"V1.1 prompt validation FAILED ({len(errors)} issue(s))")
        for error in errors:
            print(f"- {error}")
        return 1
    print("V1.1 prompt validation PASSED")
    return 0


if __name__ == "__main__":
    sys.exit(main())
