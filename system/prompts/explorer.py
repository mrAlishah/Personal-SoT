#!/usr/bin/env python3
"""Deterministic, read-only discovery over canonical prompt metadata."""
from __future__ import annotations

import argparse
from dataclasses import asdict, dataclass
import json
from pathlib import Path
import sys

if not __package__:
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from system.validation import validate_prompts


MAX_VALIDATED_CANDIDATES = 20


@dataclass(frozen=True)
class PromptQuery:
    text: str = ""
    identity: str | None = None
    path_prefix: str | None = None
    status: str = "active"
    prompt_tags: tuple[str, ...] = ()
    required_params: tuple[str, ...] = ()
    optional_params: tuple[str, ...] = ()
    prompt_profiles: tuple[str, ...] = ()
    prompt_formats: tuple[str, ...] = ()
    prompt_tone: str | None = None
    prompt_depth: str | None = None
    limit: int = 5


@dataclass(frozen=True)
class PromptMatch:
    identity: str
    status: str
    tags: tuple[str, ...]
    required_params: tuple[str, ...]
    optional_params: tuple[str, ...]
    profiles: tuple[str, ...]
    formats: tuple[str, ...]
    tone: str | None
    depth: str | None
    score: tuple[int, int, int, int, int, int]
    warning: str | None = None


@dataclass(frozen=True)
class SearchReport:
    matches: tuple[PromptMatch, ...]
    unavailable_count: int
    validated_count: int
    incomplete: bool


@dataclass(frozen=True)
class _Candidate:
    path: Path
    identity: str
    status: str
    lists: dict[str, list[str]]
    scalars: dict[str, str]
    score: tuple[int, int, int, int, int, int]


def _tokens(value: str) -> tuple[str, ...]:
    tokens: list[str] = []
    current: list[str] = []
    for character in value.casefold():
        if character.isalnum():
            current.append(character)
        elif current:
            tokens.append("".join(current))
            current = []
    if current:
        tokens.append("".join(current))
    return tuple(dict.fromkeys(tokens))


def _prompt_paths(root: Path) -> tuple[Path, ...]:
    base = root / "workspace" / "prompts"
    if not base.is_dir():
        return ()
    if base.is_symlink() or base.resolve() != base:
        return ()
    paths = []
    for path in base.rglob("*.md"):
        relative = path.relative_to(base)
        if path.name == "readme.md" or "_assets" in relative.parts or path.is_symlink():
            continue
        try:
            if not path.is_file() or not path.resolve().is_relative_to(base):
                continue
        except OSError:
            continue
        paths.append(path)
    return tuple(sorted(paths, key=lambda item: item.relative_to(base).as_posix()))


def _contains_all(actual: list[str], requested: tuple[str, ...]) -> bool:
    return set(requested).issubset(actual)


def _matches_filters(identity: str, lists: dict[str, list[str]], scalars: dict[str, str], query: PromptQuery) -> bool:
    if query.identity is not None and identity != query.identity:
        return False
    if query.path_prefix is not None and not (
        identity == query.path_prefix or identity.startswith(f"{query.path_prefix}/")
    ):
        return False
    if scalars.get("prompt_status") != query.status:
        return False
    for field, requested in (
        ("prompt_tags", query.prompt_tags),
        ("required_params", query.required_params),
        ("optional_params", query.optional_params),
        ("prompt_profiles", query.prompt_profiles),
        ("prompt_formats", query.prompt_formats),
    ):
        if not _contains_all(lists[field], requested):
            return False
    if query.prompt_tone is not None and scalars.get("prompt_tone") != query.prompt_tone:
        return False
    if query.prompt_depth is not None and scalars.get("prompt_depth") != query.prompt_depth:
        return False
    return True


def _score(identity: str, lists: dict[str, list[str]], scalars: dict[str, str], query: PromptQuery) -> tuple[int, int, int, int, int, int]:
    query_tokens = _tokens(query.text)
    path_tokens = set(_tokens(identity))
    tags = set(lists["prompt_tags"])
    parameters = set(lists["required_params"] + lists["optional_params"])
    composition = set(lists["prompt_profiles"] + lists["prompt_formats"])
    composition.update(
        value for value in (scalars.get("prompt_tone"), scalars.get("prompt_depth")) if value
    )
    partial = sum(
        1
        for token in query_tokens
        if len(token) >= 3
        and token not in path_tokens
        and token not in tags
        and any(token in value for value in path_tokens | tags)
    )
    return (
        int(query.identity == identity),
        sum(token in path_tokens for token in query_tokens),
        sum(token in tags for token in query_tokens),
        sum(token in parameters for token in query_tokens),
        sum(token in composition for token in query_tokens),
        partial,
    )


def search(root: Path, query: PromptQuery) -> SearchReport:
    if not 1 <= query.limit <= 10:
        raise ValueError("limit must be between 1 and 10")
    if query.status not in validate_prompts.VALID_STATUS:
        raise ValueError(f"unsupported prompt status {query.status!r}")

    root = root.resolve()
    base = root / "workspace" / "prompts"
    candidates: list[_Candidate] = []
    for path in _prompt_paths(root):
        keys, lists, scalars = validate_prompts.read_manifest(path)
        if not keys:
            continue
        identity = path.relative_to(base).with_suffix("").as_posix()
        if not _matches_filters(identity, lists, scalars, query):
            continue
        score = _score(identity, lists, scalars, query)
        has_explicit_filter = any(
            (
                query.identity,
                query.path_prefix,
                query.prompt_tags,
                query.required_params,
                query.optional_params,
                query.prompt_profiles,
                query.prompt_formats,
                query.prompt_tone,
                query.prompt_depth,
            )
        )
        if query.text and not any(score) and not has_explicit_filter:
            continue
        candidates.append(_Candidate(path, identity, scalars["prompt_status"], lists, scalars, score))

    candidates.sort(key=lambda item: (tuple(-value for value in item.score), item.identity))
    matches: list[PromptMatch] = []
    unavailable = 0
    validated = 0
    for candidate in candidates:
        if len(matches) == query.limit or validated == MAX_VALIDATED_CANDIDATES:
            break
        validated += 1
        if validate_prompts.validate_path(root, candidate.path):
            unavailable += 1
            continue
        matches.append(
            PromptMatch(
                candidate.identity,
                candidate.status,
                tuple(candidate.lists["prompt_tags"]),
                tuple(candidate.lists["required_params"]),
                tuple(candidate.lists["optional_params"]),
                tuple(candidate.lists["prompt_profiles"]),
                tuple(candidate.lists["prompt_formats"]),
                candidate.scalars.get("prompt_tone"),
                candidate.scalars.get("prompt_depth"),
                candidate.score,
                candidate.status if candidate.status != "active" else None,
            )
        )
    incomplete = (
        len(matches) < query.limit
        and validated == MAX_VALIDATED_CANDIDATES
        and len(candidates) > validated
    )
    return SearchReport(tuple(matches), unavailable, validated, incomplete)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[2])
    parser.add_argument("--query", default="")
    parser.add_argument("--identity")
    parser.add_argument("--path-prefix")
    parser.add_argument("--status", choices=sorted(validate_prompts.VALID_STATUS), default="active")
    parser.add_argument("--tag", action="append", default=[])
    parser.add_argument("--required-param", action="append", default=[])
    parser.add_argument("--optional-param", action="append", default=[])
    parser.add_argument("--profile", action="append", default=[])
    parser.add_argument("--format", action="append", default=[])
    parser.add_argument("--tone")
    parser.add_argument("--depth")
    parser.add_argument("--limit", type=int, default=5)
    args = parser.parse_args()
    report = search(
        args.root,
        PromptQuery(
            text=args.query,
            identity=args.identity,
            path_prefix=args.path_prefix,
            status=args.status,
            prompt_tags=tuple(args.tag),
            required_params=tuple(args.required_param),
            optional_params=tuple(args.optional_param),
            prompt_profiles=tuple(args.profile),
            prompt_formats=tuple(args.format),
            prompt_tone=args.tone,
            prompt_depth=args.depth,
            limit=args.limit,
        ),
    )
    print(json.dumps(asdict(report), ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
