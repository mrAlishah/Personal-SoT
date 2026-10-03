"""Reuse-first preview support for Profile-only Personalization writes."""
from __future__ import annotations

from dataclasses import dataclass
from difflib import unified_diff
from hashlib import sha256
import os
from pathlib import Path
from secrets import token_hex
import stat

from system.routing.runtime_naming import profile_identity_kind
from system.validation import validate_prompts, validate_public, validate_v1


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
    validation_state_digest: str
    content: str
    diff: str
    confirmation_digest: str
    write_capable: bool
    preflight_errors: tuple[str, ...]


@dataclass(frozen=True)
class ApplyResult:
    affected_path: str
    diff: str
    write_applied: bool
    validation_ran: bool
    validation_passed: bool | None
    validation_errors: tuple[str, ...]
    success: bool


def choose_profile_action(assessment: ProfileAssessment) -> tuple[str, str | None]:
    if assessment.exact_identity:
        return "reuse_profile", assessment.exact_identity
    if assessment.direct_composition_sufficient:
        return "compose", None
    if (
        assessment.edit_identity
        and assessment.same_semantic_owner
        and profile_identity_kind(assessment.edit_identity) == "custom"
    ):
        return "edit", assessment.edit_identity
    if assessment.reusable:
        return "create", None
    return "compose", None


def _digest(value: str) -> str:
    return sha256(value.encode("utf-8")).hexdigest()


def _target(root: Path, identity: str) -> tuple[str, Path]:
    kind = profile_identity_kind(identity)
    if kind == "built_in":
        raise ValueError("The g/* Profile namespace is reserved for shipped built-ins")
    if kind != "custom":
        raise ValueError("Profile identity must use lowercase [a-z0-9]+ segment grammar")
    relative = f"workspace/profiles/{identity}.md"
    profile_root = root / "workspace" / "profiles"
    target = root / relative
    if profile_root.is_symlink() or profile_root.resolve() != profile_root:
        raise ValueError("Profile root must not contain a symbolic link")
    if target.is_symlink() or target.resolve() != target:
        raise ValueError("Profile target must not contain a symbolic link")
    return relative, target


def _confirmation_digest(
    operation: str,
    identity: str,
    before_digest: str | None,
    validation_state_digest: str,
    content: str,
) -> str:
    return _digest(
        "\0".join(
            (operation, identity, before_digest or "absent", validation_state_digest, content)
        )
    )


def _preview_diff(relative: str, before: str | None, content: str) -> str:
    diff = "\n".join(
        unified_diff(
            (before or "").splitlines(),
            content.splitlines(),
            fromfile=relative if before is not None else "/dev/null",
            tofile=relative,
            lineterm="",
        )
    )
    return f"{diff}\n" if diff else ""


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
    diff = _preview_diff(relative, before, content)
    errors = tuple(validate_v1.validate_profile_source(root, target, content))
    validation_state = validate_v1.profile_validation_state_digest(root, content)
    return ProfileProposal(
        operation,
        identity,
        relative,
        before_digest,
        before,
        validation_state,
        content,
        diff,
        _confirmation_digest(operation, identity, before_digest, validation_state, content),
        write_capable,
        errors,
    )


def _not_applied(proposal: ProfileProposal, *errors: str) -> ApplyResult:
    return ApplyResult(
        proposal.target,
        proposal.diff,
        False,
        False,
        None,
        tuple(errors),
        False,
    )


def _read_at(directory_fd: int, name: str) -> str | None:
    try:
        file_fd = os.open(name, os.O_RDONLY | os.O_NOFOLLOW, dir_fd=directory_fd)
    except FileNotFoundError:
        return None
    if not stat.S_ISREG(os.fstat(file_fd).st_mode):
        os.close(file_fd)
        raise OSError("Profile target is not a regular file")
    with os.fdopen(file_fd, "r", encoding="utf-8") as source:
        return source.read()


def _open_profile_directory(root: Path) -> tuple[int, int, int]:
    root_fd = os.open(root, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
    try:
        workspace_fd = os.open(
            "workspace",
            os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW,
            dir_fd=root_fd,
        )
        try:
            profiles_fd = os.open(
                "profiles",
                os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW,
                dir_fd=workspace_fd,
            )
        except Exception:
            os.close(workspace_fd)
            raise
    except Exception:
        os.close(root_fd)
        raise
    return root_fd, workspace_fd, profiles_fd


def _same_directory_entry(parent_fd: int, name: str, child_fd: int) -> bool:
    current = os.stat(name, dir_fd=parent_fd, follow_symlinks=False)
    opened = os.fstat(child_fd)
    return stat.S_ISDIR(current.st_mode) and (current.st_dev, current.st_ino) == (
        opened.st_dev,
        opened.st_ino,
    )


def _directory_chain_unchanged(root_fd: int, workspace_fd: int, profiles_fd: int) -> bool:
    return _same_directory_entry(root_fd, "workspace", workspace_fd) and _same_directory_entry(
        workspace_fd, "profiles", profiles_fd
    )


def apply_change(root: Path, proposal: ProfileProposal, confirmation_digest: str) -> ApplyResult:
    """Apply one confirmed Profile proposal and run the strongest relevant validators."""
    root = root.resolve()
    if not proposal.write_capable:
        return _not_applied(proposal, "client is preview-only; no write or validation was performed")
    if proposal.preflight_errors:
        return _not_applied(proposal, *proposal.preflight_errors)
    expected_before = _digest(proposal.before_content) if proposal.before_content is not None else None
    expected_diff = _preview_diff(proposal.target, proposal.before_content, proposal.content)
    if expected_before != proposal.before_digest or expected_diff != proposal.diff:
        return _not_applied(proposal, "displayed preview does not match the confirmed proposal")
    expected = _confirmation_digest(
        proposal.operation,
        proposal.identity,
        proposal.before_digest,
        proposal.validation_state_digest,
        proposal.content,
    )
    if confirmation_digest != proposal.confirmation_digest or expected != proposal.confirmation_digest:
        return _not_applied(proposal, "confirmation does not match the current proposal")

    root_fd: int | None = None
    workspace_fd: int | None = None
    directory_fd: int | None = None
    lock_name: str | None = None
    temporary_name: str | None = None
    write_applied = False
    validation_ran = False
    try:
        relative, target = _target(root, proposal.identity)
        if relative != proposal.target:
            return _not_applied(proposal, "proposal target changed; create a new preview")
        root_fd, workspace_fd, directory_fd = _open_profile_directory(root)
        candidate_lock = f".{proposal.identity}.lock"
        lock_fd = os.open(
            candidate_lock,
            os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW,
            0o600,
            dir_fd=directory_fd,
        )
        os.close(lock_fd)
        lock_name = candidate_lock
        current = _read_at(directory_fd, target.name)
        if (_digest(current) if current is not None else None) != proposal.before_digest:
            return _not_applied(proposal, "Profile changed after preview; create a new preview")
        if validate_v1.profile_validation_state_digest(root, proposal.content) != proposal.validation_state_digest:
            return _not_applied(proposal, "Profile dependencies changed after preview; create a new preview")
        errors = tuple(validate_v1.validate_profile_source(root, target, proposal.content))
        if errors:
            return _not_applied(proposal, *errors)

        temporary_name = f".{proposal.identity}.{token_hex(8)}.tmp"
        temporary_fd = os.open(
            temporary_name,
            os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW,
            0o666,
            dir_fd=directory_fd,
        )
        with os.fdopen(temporary_fd, "w", encoding="utf-8") as output:
            output.write(proposal.content)
            output.flush()
            os.fsync(output.fileno())
        current = _read_at(directory_fd, target.name)
        if (_digest(current) if current is not None else None) != proposal.before_digest:
            return _not_applied(proposal, "Profile changed during write; create a new preview")
        if validate_v1.profile_validation_state_digest(root, proposal.content) != proposal.validation_state_digest:
            return _not_applied(proposal, "Profile dependencies changed during write; create a new preview")
        if not _directory_chain_unchanged(root_fd, workspace_fd, directory_fd):
            return _not_applied(proposal, "Profile root changed during write; create a new preview")
        if proposal.operation == "create":
            os.link(
                temporary_name,
                target.name,
                src_dir_fd=directory_fd,
                dst_dir_fd=directory_fd,
                follow_symlinks=False,
            )
            write_applied = True
            os.unlink(temporary_name, dir_fd=directory_fd)
        else:
            os.replace(
                temporary_name,
                target.name,
                src_dir_fd=directory_fd,
                dst_dir_fd=directory_fd,
            )
            write_applied = True
        temporary_name = None
        if not _directory_chain_unchanged(root_fd, workspace_fd, directory_fd):
            return ApplyResult(relative, proposal.diff, True, False, None, ("Profile root changed after write",), False)
        os.unlink(lock_name, dir_fd=directory_fd)
        lock_name = None

        validation_ran = True
        validation_errors = tuple(
            f"{owner}: {error}"
            for owner, errors in (
                ("validate_v1", validate_v1.run(root, "core")),
                ("validate_prompts", validate_prompts.run(root)),
                ("validate_public", validate_public.run(root)),
            )
            for error in errors
        )
        passed = not validation_errors
        return ApplyResult(relative, proposal.diff, True, True, passed, validation_errors, passed)
    except FileExistsError:
        return _not_applied(proposal, "Profile changed during write; create a new preview")
    except (OSError, UnicodeError, ValueError) as error:
        if write_applied:
            return ApplyResult(
                proposal.target,
                proposal.diff,
                True,
                validation_ran,
                False if validation_ran else None,
                (f"{'validation' if validation_ran else 'write cleanup'} failed: {error}",),
                False,
            )
        return _not_applied(proposal, f"write failed: {error}")
    except Exception as error:  # validators are the authority; preserve an applied write on failure
        return ApplyResult(
            proposal.target,
            proposal.diff,
            write_applied,
            validation_ran,
            False if validation_ran else None,
            (f"validation failed: {error}",),
            False,
        )
    finally:
        if directory_fd is not None:
            if temporary_name is not None:
                try:
                    os.unlink(temporary_name, dir_fd=directory_fd)
                except OSError:
                    pass
            if lock_name is not None:
                try:
                    os.unlink(lock_name, dir_fd=directory_fd)
                except OSError:
                    pass
            os.close(directory_fd)
        if workspace_fd is not None:
            os.close(workspace_fd)
        if root_fd is not None:
            os.close(root_fd)
