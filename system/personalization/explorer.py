"""Deterministic, read-only discovery across canonical Personalization owners."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re

from system.routing.runtime_naming import is_profile_identity
from system.validation import validate_v1


LANES = frozenset({"profile", "format", "tone", "depth", "control", "behavior"})
MAX_VALIDATED_CANDIDATES = 20


@dataclass(frozen=True)
class CapabilityQuery:
    text: str = ""
    lanes: tuple[str, ...] = ()
    identity: str | None = None
    required_components: tuple[str, ...] = ()
    limit: int = 5


@dataclass(frozen=True)
class CapabilityMatch:
    lane: str
    identity: str
    components: tuple[str, ...]
    allowed_values: tuple[str, ...]
    default_value: str | None
    score: tuple[int, int, int]


@dataclass(frozen=True)
class SearchReport:
    matches: tuple[CapabilityMatch, ...]
    unavailable_count: int
    validated_count: int
    incomplete: bool


@dataclass(frozen=True)
class _Candidate:
    lane: str
    identity: str
    path: Path
    components: tuple[str, ...] = ()
    allowed_values: tuple[str, ...] = ()
    default_value: str | None = None


def _tokens(value: str) -> tuple[str, ...]:
    return tuple(dict.fromkeys(re.findall(r"[a-z0-9_]+", value.casefold())))


def _safe_file(root: Path, path: Path) -> bool:
    try:
        return path.is_file() and not path.is_symlink() and path.resolve().is_relative_to(root)
    except OSError:
        return False


def _profile_candidates(root: Path) -> list[_Candidate]:
    base = root / "workspace/profiles"
    if not base.is_dir() or base.is_symlink() or base.resolve() != base:
        return []
    candidates = []
    for path in sorted(base.rglob("*.md")):
        if path.name == "readme.md" or path.is_symlink():
            continue
        identity = path.relative_to(base).with_suffix("").as_posix()
        if not is_profile_identity(identity):
            continue
        try:
            source = path.read_text(encoding="utf-8")
        except (OSError, UnicodeError):
            source = ""
        manifest = validate_v1.read_profile_manifest(source)
        components = tuple(
            [*(f"behavior:{value}" for value in manifest.behaviors)]
            + [*(f"format:{value}" for value in manifest.formats)]
            + ([f"tone:{manifest.tone}"] if manifest.tone else [])
            + ([f"depth:{manifest.depth}"] if manifest.depth else [])
            + ([f"language:{manifest.primary_language}"] if manifest.primary_language else [])
            + [*(f"language:{value}" for value in manifest.supporting_languages)]
            + [*(f"control:{key}={value}" for key, value in manifest.controls)]
        )
        candidates.append(_Candidate("profile", identity, path, components))
    return candidates


def _registry_candidates(root: Path) -> list[_Candidate]:
    registry = root / "system/routing/switch_registry.md"
    if not _safe_file(root, registry):
        return []
    lane_for_section = {
        "formats": "format",
        "tones": "tone",
        "depths": "depth",
        "registered_controls": "control",
    }
    return [
        _Candidate(lane_for_section[section], identity, root / target)
        for section, identity, target in validate_v1.switch_registry_entries(root)
        if section in lane_for_section
    ]


def _behavior_candidates(root: Path) -> list[_Candidate]:
    catalog = root / "system/behavior/module_catalog.md"
    if not _safe_file(root, catalog):
        return []
    try:
        identities = re.findall(
            r"^## ([a-z0-9]+(?:_[a-z0-9]+)*)\.md$",
            catalog.read_text(encoding="utf-8"),
            re.MULTILINE,
        )
    except (OSError, UnicodeError):
        return []
    return [
        _Candidate("behavior", identity, root / "system/behavior" / f"{identity}.md")
        for identity in identities
    ]


def _score(candidate: _Candidate, query: CapabilityQuery) -> tuple[int, int, int]:
    terms = set(_tokens(candidate.identity + " " + " ".join(candidate.components)))
    requested = _tokens(query.text)
    identity_tokens = _tokens(candidate.identity)
    if candidate.lane == "profile" and identity_tokens[:1] == ("g",):
        identity_tokens = identity_tokens[1:]
    return (
        int(query.identity == candidate.identity),
        int(bool(identity_tokens) and set(identity_tokens).issubset(requested)),
        sum(token in terms for token in requested),
    )


def _validated(root: Path, candidate: _Candidate) -> CapabilityMatch | None:
    if not _safe_file(root, candidate.path):
        return None
    components = candidate.components
    allowed_values = candidate.allowed_values
    default_value = candidate.default_value
    try:
        source = candidate.path.read_text(encoding="utf-8")
    except (OSError, UnicodeError):
        return None
    if candidate.lane == "profile":
        if validate_v1.validate_profile_source(root, candidate.path, source):
            return None
    elif candidate.lane == "format":
        metadata = validate_v1.simple_frontmatter(source)
        if metadata.get("format_id") != candidate.identity or metadata.get("placement") not in validate_v1.VALID_FORMAT_PLACEMENT:
            return None
        components = (f"placement:{metadata['placement']}",)
    elif candidate.lane == "control":
        metadata, values = validate_v1.parse_control_manifest(source)
        if validate_v1.validate_control_source(root, candidate.path, candidate.identity, source):
            return None
        allowed_values = tuple(values)
        default_value = metadata["control_default"]
    return CapabilityMatch(
        candidate.lane,
        candidate.identity,
        components,
        allowed_values,
        default_value,
        (0, 0, 0),
    )


def search(root: Path, query: CapabilityQuery) -> SearchReport:
    if not 1 <= query.limit <= 10:
        raise ValueError("limit must be between 1 and 10")
    lanes = frozenset(query.lanes) if query.lanes else LANES
    unknown = lanes - LANES
    if unknown:
        raise ValueError(f"unsupported Personalization lanes {sorted(unknown)}")

    root = root.resolve()
    candidates = []
    if "profile" in lanes:
        candidates.extend(_profile_candidates(root))
    if lanes.intersection({"format", "tone", "depth", "control"}):
        candidates.extend(_registry_candidates(root))
    if "behavior" in lanes:
        candidates.extend(_behavior_candidates(root))
    required = set(query.required_components)
    ranked = []
    for candidate in candidates:
        if candidate.lane not in lanes or (query.identity is not None and candidate.identity != query.identity):
            continue
        if required and not required.issubset(candidate.components):
            continue
        score = _score(candidate, query)
        if query.text and score[2] == 0:
            continue
        ranked.append((score, candidate))
    ranked.sort(
        key=lambda item: (
            -item[0][0],
            -item[0][1],
            -item[0][2],
            len(set(item[1].components) - required) if required else 0,
            item[1].lane,
            item[1].identity,
        )
    )

    matches = []
    unavailable = 0
    validated = 0
    for score, candidate in ranked:
        if len(matches) == query.limit or validated == MAX_VALIDATED_CANDIDATES:
            break
        validated += 1
        match = _validated(root, candidate)
        if match is None:
            unavailable += 1
            continue
        matches.append(
            CapabilityMatch(
                match.lane,
                match.identity,
                match.components,
                match.allowed_values,
                match.default_value,
                score,
            )
        )
    incomplete = validated == MAX_VALIDATED_CANDIDATES and len(ranked) > validated and len(matches) < query.limit
    return SearchReport(tuple(matches), unavailable, validated, incomplete)
