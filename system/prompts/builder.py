"""Reuse-before-create decisions for the client-neutral Prompt Builder."""
from __future__ import annotations

from dataclasses import dataclass
from difflib import unified_diff
from hashlib import sha256
import os
from pathlib import Path, PurePosixPath
from tempfile import NamedTemporaryFile

from system.validation import validate_prompts, validate_public, validate_v1


@dataclass(frozen=True)
class ReuseAssessment:
    exact_identity: str | None = None
    parameterized_identity: str | None = None
    composition: tuple[str, ...] = ()
    edit_identity: str | None = None
    same_semantic_owner: bool = False


@dataclass(frozen=True)
class PromptProposal:
    operation: str
    identity: str
    target: str
    before_digest: str | None
    before_content: str | None
    validation_state_digest: str
    content: str
    diff: str
    confirmation_digest: str
    write_capable: bool
    preflight_errors: tuple[str, ...]


@dataclass(frozen=True)
class ApplyResult:
    write_applied: bool
    validation_ran: bool
    validation_passed: bool | None
    validation_errors: tuple[str, ...]
    success: bool
    affected_path: str
    before_content: str | None
    diff: str


def choose_action(assessment: ReuseAssessment) -> tuple[str, str | None]:
    if assessment.exact_identity:
        return "reuse_exact", assessment.exact_identity
    if assessment.parameterized_identity:
        return "reuse_parameterized", assessment.parameterized_identity
    if assessment.composition:
        return "compose", None
    if assessment.edit_identity and assessment.same_semantic_owner:
        return "edit", assessment.edit_identity
    return "create", None


def _digest(value: str) -> str:
    return sha256(value.encode("utf-8")).hexdigest()


def _target(root: Path, identity: str) -> tuple[str, Path]:
    logical = PurePosixPath(identity)
    if logical.is_absolute() or not logical.parts or any(
        part in {".", ".."} or not validate_prompts.NAME_RE.fullmatch(part)
        for part in logical.parts
    ):
        raise ValueError("prompt identity must use lowercase_snake_case path segments")
    relative = (PurePosixPath("workspace/prompts") / logical).with_suffix(".md").as_posix()
    target = root / relative
    prompt_root = root / "workspace/prompts"
    if prompt_root.is_symlink() or prompt_root.resolve() != prompt_root:
        raise ValueError("prompt root must not contain a symbolic link")
    if target.resolve() != target:
        raise ValueError("prompt target ancestors must not contain a symbolic link")
    return relative, target


def _confirmation_digest(
    operation: str,
    identity: str,
    before_digest: str | None,
    validation_state_digest: str,
    content: str,
) -> str:
    return _digest(
        "\0".join((operation, identity, before_digest or "absent", validation_state_digest, content))
    )


def preview_change(
    root: Path,
    operation: str,
    identity: str,
    content: str,
    *,
    same_semantic_owner: bool,
    fact_safe: bool,
    write_capable: bool,
) -> PromptProposal:
    root = root.resolve()
    if operation not in {"create", "edit"}:
        raise ValueError("operation must be 'create' or 'edit'")
    if not fact_safe:
        raise ValueError("reusable prompt content must be classified as fact-safe")
    relative, target = _target(root, identity)
    if target.is_symlink():
        raise ValueError("prompt target must not be a symbolic link")
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
    errors = tuple(validate_prompts.validate_source(root, target, content))
    state_digest = validate_prompts.validation_state_digest(root, content)
    return PromptProposal(
        operation,
        identity,
        relative,
        before_digest,
        before,
        state_digest,
        content,
        diff,
        _confirmation_digest(operation, identity, before_digest, state_digest, content),
        write_capable,
        errors,
    )


def _not_applied(proposal: PromptProposal, error: str) -> ApplyResult:
    return ApplyResult(
        False,
        False,
        None,
        (error,),
        False,
        proposal.target,
        proposal.before_content,
        proposal.diff,
    )


def apply_change(root: Path, proposal: PromptProposal, confirmation_digest: str) -> ApplyResult:
    root = root.resolve()
    if not proposal.write_capable:
        return _not_applied(proposal, "write capability unavailable; nothing was written")
    if proposal.operation not in {"create", "edit"}:
        return _not_applied(proposal, "proposal operation is invalid")
    if proposal.preflight_errors:
        return _not_applied(proposal, "proposal has unresolved preflight errors")
    if confirmation_digest != proposal.confirmation_digest:
        return _not_applied(proposal, "confirmation does not match the preview")
    if proposal.confirmation_digest != _confirmation_digest(
        proposal.operation,
        proposal.identity,
        proposal.before_digest,
        proposal.validation_state_digest,
        proposal.content,
    ):
        return _not_applied(proposal, "proposal changed after confirmation")

    relative, target = _target(root, proposal.identity)
    if relative != proposal.target or target.is_symlink():
        return _not_applied(proposal, "proposal target no longer resolves safely")
    if proposal.operation == "create" and target.exists():
        return _not_applied(proposal, "create target appeared after preview")
    if proposal.operation == "edit":
        if not target.is_file():
            return _not_applied(proposal, "edit target disappeared after preview")
        current = target.read_text(encoding="utf-8")
        if _digest(current) != proposal.before_digest:
            return _not_applied(proposal, "edit target changed after preview")
    if validate_prompts.validation_state_digest(root, proposal.content) != proposal.validation_state_digest:
        return _not_applied(proposal, "canonical validation state changed after preview")
    if validate_prompts.validate_source(root, target, proposal.content):
        return _not_applied(proposal, "proposal no longer passes prompt preflight")
    if validate_prompts.validation_state_digest(root, proposal.content) != proposal.validation_state_digest:
        return _not_applied(proposal, "canonical validation state changed during preflight")
    relative, target = _target(root, proposal.identity)
    if proposal.operation == "create" and target.exists():
        return _not_applied(proposal, "create target appeared during preflight")
    if proposal.operation == "edit":
        if not target.is_file() or _digest(target.read_text(encoding="utf-8")) != proposal.before_digest:
            return _not_applied(proposal, "edit target changed during preflight")

    temporary = None
    try:
        target.parent.mkdir(parents=True, exist_ok=True)
        with NamedTemporaryFile(
            "w",
            encoding="utf-8",
            dir=target.parent,
            prefix=f".{target.name}.",
            suffix=".tmp",
            delete=False,
        ) as handle:
            handle.write(proposal.content)
            temporary = Path(handle.name)
        os.replace(temporary, target)
        temporary = None
    except OSError as error:
        return _not_applied(proposal, f"write failed: {error}")
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)

    try:
        errors = tuple(
            [f"prompts: {error}" for error in validate_prompts.run(root)]
            + [f"core: {error}" for error in validate_v1.run(root, "core")]
            + [f"public: {error}" for error in validate_public.run(root)]
        )
    except Exception as error:  # preserve explicit post-write state on validator failure
        return ApplyResult(
            True,
            False,
            False,
            (f"validation exception: {type(error).__name__}: {error}",),
            False,
            proposal.target,
            proposal.before_content,
            proposal.diff,
        )
    passed = not errors
    return ApplyResult(
        True,
        True,
        passed,
        errors,
        passed,
        proposal.target,
        proposal.before_content,
        proposal.diff,
    )
