"""Reuse-first preview support for Profile-only Personalization writes."""
from __future__ import annotations

from dataclasses import dataclass
from difflib import unified_diff
from hashlib import sha256
from pathlib import Path

from system.validation import validate_v1


@dataclass(frozen=True)
class ProfileAssessment:
    exact_identity: str | None = None
    direct_composition_sufficient: bool = False
    reusable: bool = False
    edit_identity: str | None = None
    same_semantic_owner: bool = False


@dataclass(frozen=True)
class ProfileProposal:
    operation: str
    identity: str
    target: str
    before_digest: str | None
    before_content: str | None
    content: str
    diff: str
    confirmation_digest: str
    write_capable: bool
    preflight_errors: tuple[str, ...]


def choose_profile_action(assessment: ProfileAssessment) -> tuple[str, str | None]:
    if assessment.exact_identity:
        return "reuse_profile", assessment.exact_identity
    if assessment.direct_composition_sufficient:
        return "compose", None
    if assessment.edit_identity and assessment.same_semantic_owner:
        return "edit", assessment.edit_identity
    if assessment.reusable:
        return "create", None
    return "compose", None


def _digest(value: str) -> str:
    return sha256(value.encode("utf-8")).hexdigest()


def _target(root: Path, identity: str) -> tuple[str, Path]:
    if not validate_v1.NAME_RE.fullmatch(identity):
        raise ValueError("Profile identity must use one lowercase_snake_case name")
    relative = f"workspace/profiles/{identity}.md"
    return relative, root / relative


def _confirmation_digest(
    operation: str,
    identity: str,
    before_digest: str | None,
    content: str,
) -> str:
    return _digest("\0".join((operation, identity, before_digest or "absent", content)))


def preview_change(
    root: Path,
    operation: str,
    identity: str,
    content: str,
    *,
    same_semantic_owner: bool,
    fact_safe: bool,
    write_capable: bool,
) -> ProfileProposal:
    root = root.resolve()
    if operation not in {"create", "edit"}:
        raise ValueError("Profile operation must be 'create' or 'edit'")
    if not fact_safe:
        raise ValueError("Profile content must be classified as fact-safe")
    relative, target = _target(root, identity)
    if operation == "create" and target.exists():
        raise ValueError("create target already exists")
    if operation == "edit" and not same_semantic_owner:
        raise ValueError("edit requires the same semantic owner")
    if operation == "edit" and not target.is_file():
        raise ValueError("edit target does not exist")

    before = target.read_text(encoding="utf-8") if operation == "edit" else None
    before_digest = _digest(before) if before is not None else None
    diff = "\n".join(
        unified_diff(
            (before or "").splitlines(),
            content.splitlines(),
            fromfile=relative if before is not None else "/dev/null",
            tofile=relative,
            lineterm="",
        )
    )
    if diff:
        diff += "\n"
    errors = tuple(validate_v1.validate_profile_source(root, target, content))
    return ProfileProposal(
        operation,
        identity,
        relative,
        before_digest,
        before,
        content,
        diff,
        _confirmation_digest(operation, identity, before_digest, content),
        write_capable,
        errors,
    )
