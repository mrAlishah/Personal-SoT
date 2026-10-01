"""Safe Update ZIP/no-Git side-by-side migration; see update_contract.md.

The original installation is read-only input throughout: this module never
writes, chmods, renames, unlinks, or normalizes anything under it. The
destination is always a new/empty location; the original is never mutated,
on success or on failure. There is no in-place ZIP migration in V1.
"""
from __future__ import annotations

from dataclasses import dataclass, field, replace
from hashlib import sha256
from io import BytesIO
import os
from pathlib import Path, PurePosixPath
import stat
import subprocess
import sys
import tarfile
import tempfile

from system.connectors.source import SourceUnavailable
from system.update import target
from system.update.git_update import TargetMaterializationError, _materialized_target
from system.update.target import controlled_git
from system.validation.validate_v1 import SCOPE_RE, context_registry_entries

_REGISTRY_RELATIVE = Path('system', 'routing', 'context_registry.md')
_REGISTRY_REL_POSIX = _REGISTRY_RELATIVE.as_posix()
_REGISTRY_MARKER = '## registered_scopes'
_ROOT_UNSAFE_MARKER = '<root>'


@dataclass(frozen=True)
class RegistryMapping:
    scope: str
    target: str


@dataclass(frozen=True)
class RegistryPlan:
    carried: tuple[RegistryMapping, ...] = ()
    dropped: tuple[RegistryMapping, ...] = ()
    conflicts: tuple[str, ...] = ()


@dataclass(frozen=True)
class SideBySidePlan:
    """No file content anywhere in this shape — paths, hashes (not
    content), and classification labels only.
    """
    target: str = ''
    pristine_fingerprint: str = ''
    kept: tuple[str, ...] = ()
    kept_hashes: tuple[tuple[str, str], ...] = ()
    identical: tuple[str, ...] = ()
    conflicts: tuple[str, ...] = ()
    manual_resolution: tuple[str, ...] = ()
    rejected_unsafe: tuple[str, ...] = ()
    excluded: tuple[str, ...] = ()
    registry: RegistryPlan = field(default_factory=RegistryPlan)
    blocked: str | None = None


@dataclass(frozen=True)
class SideBySidePreview:
    digest: str
    plan: SideBySidePlan


@dataclass(frozen=True)
class MigrationResult:
    pristine_validation_ran: bool = False
    pristine_validation_passed: bool = False
    personal_validation_ran: bool = False
    personal_validation_passed: bool = False
    migration_started: bool = False
    ready: bool = False
    failure: str | None = None


# --- path safety -------------------------------------------------------

def normalize_relative(path_str: str) -> str | None:
    """A safe, root-relative POSIX path string from caller-supplied input
    (e.g. an exclusion request) — `None` if it is empty, absolute, or
    contains a `..` traversal segment. Never resolves against any real
    filesystem; this is a pure string-shape check for input a caller
    controls, not a replacement for the host-side lstat-based scan.
    """
    if not path_str:
        return None
    posix = PurePosixPath(path_str)
    if posix.is_absolute() or '..' in posix.parts:
        return None
    return posix.as_posix()


def _root_anchored_parts(relative: str) -> list[str] | None:
    """The path components of `relative` for a root-anchored,
    one-component-at-a-time `openat()` walk, or `None` if it is not a
    simple, safe, relative path (empty, absolute, containing `.`/`..`,
    or any component itself containing a `/`).
    """
    parts = PurePosixPath(relative).parts
    if not parts:
        return None
    for part in parts:
        if part in ('.', '..') or not part:
            return None
    return list(parts)


_NOFOLLOW_SUPPORTED = (
    getattr(os, 'O_NOFOLLOW', None) is not None
    and getattr(os, 'O_DIRECTORY', None) is not None
    and os.open in os.supports_dir_fd
)


@dataclass
class _PinnedRoot:
    """A root directory, opened ONCE and held open for the duration of
    one logical operation (a classification, a copy loop, a candidate's
    whole build-through-ready lifecycle), identified by its
    `(st_dev, st_ino)` at the moment it was pinned.

    Every descendant read/write for that operation must go through
    `fd` via `dir_fd`-relative `openat()` calls, never by re-deriving
    the root from `path` again: an already-open fd keeps referring to
    the SAME physical directory even if `path` is later renamed away,
    replaced by a symlink, or replaced by an entirely different real
    directory at the same name — none of which a repeated
    "reopen-by-pathname" strategy could detect or resist. `path` is
    kept only for identity rechecks (`_pinned_root_still_current`) and
    for the few operations (a scan via `os.walk`, a validator
    subprocess argument) that inherently require a pathname rather
    than an fd.
    """
    fd: int
    path: Path
    dev: int
    ino: int

    def close(self) -> None:
        try:
            os.close(self.fd)
        except OSError:
            pass


def _pin_root(path: Path) -> _PinnedRoot | None:
    """Open `path` once as a directory, root-anchored
    (`O_DIRECTORY | O_NOFOLLOW` — the root itself must not be a
    symlink, not merely its descendants), and record its identity.
    `None` if the platform has no safe no-follow primitive, or the path
    cannot be safely opened as a real directory at all.
    """
    if not _NOFOLLOW_SUPPORTED:
        return None
    try:
        fd = os.open(str(path), os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
    except OSError:
        return None
    try:
        st = os.fstat(fd)
    except OSError:
        os.close(fd)
        return None
    return _PinnedRoot(fd=fd, path=Path(path), dev=st.st_dev, ino=st.st_ino)


def _pinned_root_still_current(pinned: _PinnedRoot) -> bool:
    """Whether `pinned.path` still names the SAME physical directory
    the pinned fd was opened from. Required before and after any
    operation that must still take a pathname (an `os.walk` scan, a
    validator subprocess argument) rather than the fd itself — the
    closest available guarantee that such an operation examined the
    pinned candidate and not a directory substituted at the same name.
    """
    try:
        st = os.stat(pinned.path, follow_symlinks=False)
    except OSError:
        return False
    return stat.S_ISDIR(st.st_mode) and (st.st_dev, st.st_ino) == (pinned.dev, pinned.ino)


def _validate_pinned(pinned: _PinnedRoot, validator) -> bool:
    """Run a single-bool subprocess-backed validator against
    `pinned.path`, bracketed by root-identity checks immediately before
    and immediately after the call — a subprocess necessarily takes a
    pathname, not an fd, so this is the closest equivalent to running
    it against the pinned fd itself. A validator run against a
    substituted root is never treated as having validated the pinned
    candidate.
    """
    if not _pinned_root_still_current(pinned):
        return False
    ok = validator(pinned.path)
    if not _pinned_root_still_current(pinned):
        return False
    return ok


def _safe_stat_kind(root: _PinnedRoot, relative: str) -> str:
    """`'absent'` if `relative` under `root` safely does not exist,
    `'regular'` if it is confirmed — root-anchored, one `openat()` per
    path component with `O_NOFOLLOW`, never a symlink anywhere along
    the way, not merely the final component — to be a regular file, or
    `'unsafe'` for anything else (a symlink anywhere along its path, or
    a special file). Distinguishing "absent" from "unsafe" matters
    because a legitimately missing file (no current registry
    customization, say) must not be treated the same as one hidden
    behind a symlink.
    """
    parts = _root_anchored_parts(relative)
    if not parts:
        return 'unsafe'
    opened = []
    try:
        parent = root.fd
        for part in parts[:-1]:
            try:
                fd = os.open(part, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=parent)
            except FileNotFoundError:
                return 'absent'
            except OSError:
                return 'unsafe'
            opened.append(fd)
            parent = fd
        try:
            final_fd = os.open(parts[-1], os.O_RDONLY | os.O_NOFOLLOW, dir_fd=parent)
        except FileNotFoundError:
            return 'absent'
        except OSError:
            return 'unsafe'
        opened.append(final_fd)
        try:
            return 'regular' if stat.S_ISREG(os.fstat(final_fd).st_mode) else 'unsafe'
        except OSError:
            return 'unsafe'
    finally:
        for fd in opened:
            try:
                os.close(fd)
            except OSError:
                pass


def _safe_read_regular(root: _PinnedRoot, relative: str) -> bytes | None:
    """Read the bytes of `relative` under the pinned `root`: one
    `openat(..., O_NOFOLLOW)` per path component — every intermediate
    directory and the final component alike — starting from the
    already-open, identity-pinned root fd, never a plain pathname open
    of the root itself. `fstat` on the SAME descriptor the bytes are
    read from confirms it is a regular file; there is no separate
    `lstat`-then-reopen step for a race to land in. Returns `None` —
    never raises — for any expected `OSError` anywhere along the walk.
    """
    parts = _root_anchored_parts(relative)
    if not parts:
        return None
    opened = []
    try:
        parent = root.fd
        for part in parts[:-1]:
            try:
                fd = os.open(part, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=parent)
            except OSError:
                return None
            opened.append(fd)
            parent = fd
        try:
            final_fd = os.open(parts[-1], os.O_RDONLY | os.O_NOFOLLOW, dir_fd=parent)
        except OSError:
            return None
        opened.append(final_fd)
        try:
            if not stat.S_ISREG(os.fstat(final_fd).st_mode):
                return None
            chunks = []
            while True:
                chunk = os.read(final_fd, 65536)
                if not chunk:
                    break
                chunks.append(chunk)
            return b''.join(chunks)
        except OSError:
            return None
    finally:
        for fd in opened:
            try:
                os.close(fd)
            except OSError:
                pass


def _safe_ensure_dir(parent_fd: int, name: str):
    """A verified real-directory fd for `name` under `parent_fd`,
    creating it first if absent — `name` existing as anything other
    than a real directory (a symlink, a file) makes this fail, never
    silently accepted as traversable.
    """
    try:
        os.mkdir(name, 0o755, dir_fd=parent_fd)
    except FileExistsError:
        pass
    except OSError:
        return None
    try:
        return os.open(name, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=parent_fd)
    except OSError:
        return None


def _safe_mkdir_p(root: _PinnedRoot, relative: str) -> bool:
    """Ensure every component of `relative` under the pinned `root`
    exists as a verified real directory (creating as needed), root-
    anchored throughout — used for a directory member of a pristine
    archive, where even the FINAL component must become a directory.
    """
    parts = _root_anchored_parts(relative)
    if not parts:
        return False
    opened = []
    try:
        parent = root.fd
        for part in parts:
            fd = _safe_ensure_dir(parent, part)
            if fd is None:
                return False
            opened.append(fd)
            parent = fd
        return True
    finally:
        for fd in opened:
            try:
                os.close(fd)
            except OSError:
                pass


def _safe_create_new_regular(root: _PinnedRoot, relative: str, data: bytes, mode: int = 0o644) -> bool:
    """Create a NEW regular file at `relative` under the pinned `root`,
    root-anchored through every intermediate component (each must
    already be, or safely become, a verified real directory — never a
    symlink). `O_CREAT | O_EXCL | O_NOFOLLOW` on the final component
    means this fails closed if anything already exists there, rather
    than silently overwriting it or following a pre-planted symlink.
    """
    parts = _root_anchored_parts(relative)
    if not parts:
        return False
    opened = []
    try:
        parent = root.fd
        for part in parts[:-1]:
            fd = _safe_ensure_dir(parent, part)
            if fd is None:
                return False
            opened.append(fd)
            parent = fd
        try:
            final_fd = os.open(
                parts[-1], os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, mode, dir_fd=parent)
        except OSError:
            return False
        opened.append(final_fd)
        try:
            os.write(final_fd, data)
            return True
        except OSError:
            return False
    finally:
        for fd in opened:
            try:
                os.close(fd)
            except OSError:
                pass


def _safe_replace_existing_regular(root: _PinnedRoot, relative: str, expected_before_hash: str,
                                    new_bytes: bytes) -> bool:
    """Replace the content of an EXISTING, target-owned file (only the
    registry, currently) root-anchored and via a single read-write
    descriptor: opens it once with `O_NOFOLLOW`, confirms it is a
    regular file whose current bytes still hash to
    `expected_before_hash`, then truncates and rewrites THAT SAME
    descriptor — never a separate write-mode reopen, which would leave
    its own TOCTOU gap.
    """
    parts = _root_anchored_parts(relative)
    if not parts:
        return False
    opened = []
    try:
        parent = root.fd
        for part in parts[:-1]:
            try:
                fd = os.open(part, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=parent)
            except OSError:
                return False
            opened.append(fd)
            parent = fd
        try:
            final_fd = os.open(parts[-1], os.O_RDWR | os.O_NOFOLLOW, dir_fd=parent)
        except OSError:
            return False
        opened.append(final_fd)
        try:
            st = os.fstat(final_fd)
            if not stat.S_ISREG(st.st_mode):
                return False
            current = os.pread(final_fd, st.st_size, 0)
            if sha256(current).hexdigest() != expected_before_hash:
                return False
            os.ftruncate(final_fd, 0)
            os.pwrite(final_fd, new_bytes, 0)
            return True
        except OSError:
            return False
    finally:
        for fd in opened:
            try:
                os.close(fd)
            except OSError:
                pass


def _scan_tree(pinned: _PinnedRoot) -> tuple[dict[str, Path], tuple[str, ...]]:
    """One bounded host-side walk of the pinned root. Returns
    (`{relative_posix_path: absolute_path}` for every REGULAR file,
    sorted unsafe relative paths). A symlink (file or directory) or any
    other special file type is never followed or read — only reported
    as unsafe. `os.walk` is pathname-based, so the pinned root's
    identity is reverified immediately before and immediately after
    the walk; a mismatch on either side reports a single `'<root>'`
    sentinel rather than any file content, and the caller must treat
    that as a hard failure, not an ordinary unsafe path to skip —
    `followlinks=False` alone does not protect the WALK'S OWN top-level
    argument from being a symlink or a substituted directory, only the
    subdirectories encountered while walking it.
    """
    if not _pinned_root_still_current(pinned):
        return {}, (_ROOT_UNSAFE_MARKER,)
    root = pinned.path
    files: dict[str, Path] = {}
    unsafe: list[str] = []
    for dirpath, dirnames, filenames in os.walk(root, followlinks=False):
        safe_dirnames = []
        for name in dirnames:
            full = Path(dirpath, name)
            if os.path.islink(full):
                unsafe.append(full.relative_to(root).as_posix())
            else:
                safe_dirnames.append(name)
        dirnames[:] = safe_dirnames
        for name in filenames:
            full = Path(dirpath, name)
            relative = full.relative_to(root).as_posix()
            st = full.lstat()
            if stat.S_ISREG(st.st_mode):
                files[relative] = full
            else:
                unsafe.append(relative)
    if not _pinned_root_still_current(pinned):
        return {}, (_ROOT_UNSAFE_MARKER,)
    return files, tuple(sorted(unsafe))


def _destination_safe(destination: Path, current_root: Path) -> bool:
    """The destination must be new or an already-empty directory, must
    not be the current installation itself, must not sit inside it, and
    the current installation must not sit inside the destination either
    (checked both ways after resolving any symlink indirection) — never
    prepared by deleting/cleaning an existing non-empty location.
    """
    if destination.exists():
        if destination.is_symlink() or not destination.is_dir():
            return False
        if any(destination.iterdir()):
            return False
    dest_resolved = destination.resolve()
    current_resolved = current_root.resolve()
    if dest_resolved == current_resolved:
        return False
    for inner, outer in ((dest_resolved, current_resolved), (current_resolved, dest_resolved)):
        try:
            inner.relative_to(outer)
        except ValueError:
            continue
        return False
    return True


# --- pristine distribution ----------------------------------------------

def _extract_pristine_archive(archive_bytes: bytes, destination: Path) -> bool:
    """Extract ONLY regular files and directories from a tar stream
    produced by `git archive` into `destination`, rejecting absolute
    paths, `..` traversal, symlink members, and hardlink members before
    anything is written. The destination root itself is pinned
    (`O_DIRECTORY | O_NOFOLLOW`) before any write, and every member is
    created root-anchored through that pin — member-shape validation
    alone does not protect against the destination ROOT being replaced
    by a symlink between the earlier `_destination_safe` check and this
    extraction; pinning closes that window the same way every other
    destination write in this module does. Executable/ordinary mode
    bits are preserved from the archive (masked to plain `rwx`, like
    Python's own tar 'data' extraction filter), never silently
    collapsed to a fixed mode.
    """
    try:
        with tarfile.open(fileobj=BytesIO(archive_bytes)) as tf:
            members = tf.getmembers()
            for member in members:
                if member.issym() or member.islnk():
                    return False
                if not (member.isfile() or member.isdir()):
                    return False
                posix = PurePosixPath(member.name)
                if posix.is_absolute() or '..' in posix.parts:
                    return False

            # `destination` may be a brand-new path that does not exist
            # yet at all; `mkdir` creates it as a real directory without
            # ever following anything (it fails outright, EEXIST, if
            # ANY node — file, directory, or symlink — already sits
            # there, rather than silently treating one as acceptable).
            # If it already exists (the caller's `_destination_safe`
            # check already confirmed that), this is a no-op, and
            # `_pin_root` below independently re-verifies it is a real,
            # non-symlink directory before anything is written into it.
            try:
                os.mkdir(str(destination))
            except FileExistsError:
                pass
            except OSError:
                return False

            pinned = _pin_root(destination)
            if pinned is None:
                return False
            try:
                for member in members:
                    relative = PurePosixPath(member.name).as_posix()
                    if relative in ('', '.'):
                        continue
                    if member.isdir():
                        if not _safe_mkdir_p(pinned, relative):
                            return False
                    else:
                        extracted = tf.extractfile(member)
                        content = extracted.read() if extracted is not None else b''
                        mode = (member.mode & 0o777) or 0o644
                        if not _safe_create_new_regular(pinned, relative, content, mode=mode):
                            return False
            finally:
                pinned.close()
    except (tarfile.TarError, OSError):
        return False
    return True


def build_pristine(destination: Path, target_commit: str) -> bool:
    """Materialize exactly `target_commit` into `destination`.

    `target_commit` must already be the resolved immutable `T` from
    `system.update.target.resolve()` — this function accepts no
    repository, ref, branch, fork, PR, or archive argument; it only ever
    receives that one already-resolved commit, flowing internally. It
    reuses Loop 1/2's exact target-materialization boundary
    (`_materialized_target`: fetch only the literal canonical
    `refs/heads/main`, verify the fetched commit equals the one already
    resolved, no local/private object ever reaches that fetch's
    negotiation) rather than defining a second resolver or fetch path.
    The caller has already verified `destination` is new/empty.
    """
    destination = Path(destination)
    try:
        with _materialized_target(target_commit) as ephemeral:
            archive = controlled_git(
                'archive', '--format=tar', target_commit, cwd=ephemeral, text=False)
            if archive.returncode != 0:
                return False
            return _extract_pristine_archive(archive.stdout, destination)
    except TargetMaterializationError:
        return False


def validate_pristine(destination: Path) -> bool:
    """Run the CANDIDATE's own `validate_public.py` (a subprocess rooted
    at the pristine tree's own copy of that file, never the live
    checkout's already-imported module) against `destination`, before
    any Personal file enters it.
    """
    result = subprocess.run(
        [sys.executable, '-B', str(Path(destination, 'system', 'validation', 'validate_public.py'))],
        cwd=str(destination), capture_output=True, text=True, timeout=60)
    return result.returncode == 0


def validate_candidate(destination: Path) -> tuple[bool, bool]:
    """Run the CANDIDATE's own `validate_v1.py --mode personal` and
    `validate_prompts.py` against the finished migration candidate —
    the same candidate-own-subprocess strategy Loop 3 uses, never
    `validate_public` at this stage.
    """
    personal = subprocess.run(
        [sys.executable, '-B', str(Path(destination, 'system', 'validation', 'validate_v1.py')),
         '--mode', 'personal'],
        cwd=str(destination), capture_output=True, text=True, timeout=60)
    prompts = subprocess.run(
        [sys.executable, '-B', str(Path(destination, 'system', 'validation', 'validate_prompts.py'))],
        cwd=str(destination), capture_output=True, text=True, timeout=60)
    return personal.returncode == 0, prompts.returncode == 0


def _hash_file(root: _PinnedRoot, relative: str) -> str | None:
    data = _safe_read_regular(root, relative)
    if data is None:
        return None
    return sha256(data).hexdigest()


def _tree_manifest(root: _PinnedRoot) -> dict[str, str]:
    """`{relative_posix_path: content_hash}` for every regular file
    under the pinned root, read via `_safe_read_regular`. A path that
    fails that safe read is simply omitted. If the root's own identity
    broke during the scan, the manifest is empty outright — never a
    partial result silently mistaken for complete — so any caller
    comparing it against an expectation fails closed rather than
    succeeding against the wrong directory's content.
    """
    files, unsafe = _scan_tree(root)
    if _ROOT_UNSAFE_MARKER in unsafe:
        return {}
    manifest = {}
    for relative in files:
        digest = _hash_file(root, relative)
        if digest is not None:
            manifest[relative] = digest
    return manifest


def _fingerprint_tree(root: _PinnedRoot) -> str:
    """A deterministic hash over the pristine tree's own
    (relative_path, content_hash) pairs, sorted — the staleness signal
    for "has the materialized pristine distribution itself changed",
    bound into the preview digest.
    """
    manifest = _tree_manifest(root)
    lines = [f'{relative}:{digest}' for relative, digest in sorted(manifest.items())]
    return sha256('\n'.join(lines).encode('utf-8')).hexdigest()


# --- registry carry-over -------------------------------------------------

def _read_text_or_empty(path: Path) -> str:
    return path.read_text(encoding='utf-8') if path.is_file() else ''


def _safe_registry_text(root: _PinnedRoot) -> tuple[str, bool]:
    """(`text`, `ok`) for the CURRENT installation's own registry file,
    read through the same root-anchored safe boundary as any other
    current input. A legitimately absent registry is `('', True)` — no
    customization at all. `ok=False` means the path exists but is
    unsafe (a symlink anywhere along it, or a special file) — never
    silently treated as an empty/absent registry.
    """
    kind = _safe_stat_kind(root, _REGISTRY_REL_POSIX)
    if kind == 'absent':
        return '', True
    if kind != 'regular':
        return '', False
    data = _safe_read_regular(root, _REGISTRY_REL_POSIX)
    if data is None:
        return '', False
    try:
        return data.decode('utf-8'), True
    except UnicodeDecodeError:
        return '', False


def _canonical_target(dest: str) -> str | None:
    """The canonical identity of a registry target string for
    ownership/duplicate comparison — trailing-slash-insensitive — or
    `None` if it is not a safe `workspace/context/` path at all. Never
    used as the literal text kept in the written registry file.
    """
    canonical = normalize_relative(dest.rstrip('/'))
    if canonical is None or not canonical.startswith('workspace/context/'):
        return None
    return canonical


def _validated_target_registry(target_entries) -> tuple[dict[str, str], dict[str, str], list[str]]:
    """Validate the TARGET registry's own entries before trusting them
    as the carry-over baseline. A duplicate scope occurrence (even with
    an identical target) and a duplicate canonical target claimed by
    two different scopes (including a trailing-slash spelling
    variation) are both conflicts, exactly like an outright different
    duplicate — never silently collapsed by `dict.setdefault`. A
    malformed entry (bad scope grammar, or a target outside
    `workspace/context/`) is also a conflict and excluded entirely.
    """
    scope_to_target: dict[str, str] = {}
    target_to_scope: dict[str, str] = {}
    seen_scopes: set[str] = set()
    conflicts: list[str] = []
    for scope, dest in target_entries:
        if not SCOPE_RE.fullmatch(scope):
            conflicts.append(f'invalid_target_scope:{scope}')
            continue
        canonical = _canonical_target(dest)
        if canonical is None:
            conflicts.append(f'invalid_target_mapping:{scope}')
            continue
        if scope in seen_scopes:
            conflicts.append(f'target_registry_scope_conflict:{scope}')
            scope_to_target.pop(scope, None)
            continue
        seen_scopes.add(scope)
        existing_scope = target_to_scope.get(canonical)
        if existing_scope is not None:
            conflicts.append(f'target_registry_target_conflict:{canonical}')
            scope_to_target.pop(existing_scope, None)
            target_to_scope.pop(canonical, None)
            continue
        scope_to_target[scope] = dest
        target_to_scope[canonical] = scope
    return scope_to_target, target_to_scope, conflicts


def _registry_plan(current_root: _PinnedRoot, pristine_root: _PinnedRoot,
                    candidate_paths: frozenset[str]) -> RegistryPlan:
    """Read both registries exclusively with `context_registry_entries`
    (never a second parser) — the current one through the root-anchored
    safe read boundary, the pristine one directly (it lives inside the
    already-validated, updater-owned pristine tree). Keep only current
    mappings whose canonical target is a `workspace/context/` directory
    that actually has at least one resulting candidate file STRICTLY
    BENEATH it — a regular file sitting exactly at the mapped path does
    not make that path a directory, so it does not count as preserved.
    A current mapping that is canonically identical to one the TARGET
    registry already provides (even spelled with a different trailing
    slash) is simply not carried again — it is neither a conflict nor a
    duplicate, since the target's own verbatim text already covers it.
    A genuine scope/target ownership conflict — within current entries,
    or against the validated target registry, using canonical
    slash-insensitive identity throughout — fails closed.
    """
    current_text, current_registry_ok = _safe_registry_text(current_root)
    target_text = _read_text_or_empty(pristine_root.path / _REGISTRY_RELATIVE)
    current_entries = context_registry_entries(current_text)
    target_entries = context_registry_entries(target_text)

    target_scope_to_target, target_target_to_scope, conflicts = _validated_target_registry(target_entries)
    accepted_scope_to_target = dict(target_scope_to_target)
    accepted_target_to_scope = dict(target_target_to_scope)

    if not current_registry_ok:
        conflicts.append('unsafe_registry')

    carried: list[RegistryMapping] = []
    dropped: list[RegistryMapping] = []
    seen_current_scopes: set[str] = set()

    for scope, dest in current_entries:
        if not SCOPE_RE.fullmatch(scope):
            conflicts.append(f'invalid_scope:{scope}')
            continue
        canonical = _canonical_target(dest)
        if canonical is None:
            dropped.append(RegistryMapping(scope, dest))
            continue
        if scope in seen_current_scopes:
            conflicts.append(f'scope_conflict:{scope}')
            carried = [mapping for mapping in carried if mapping.scope != scope]
            accepted_target_to_scope = {
                t: s for t, s in accepted_target_to_scope.items() if s != scope}
            accepted_scope_to_target.pop(scope, None)
            continue
        seen_current_scopes.add(scope)
        preserved = any(path.startswith(canonical + '/') for path in candidate_paths)
        if not preserved:
            dropped.append(RegistryMapping(scope, dest))
            continue
        target_dest = target_scope_to_target.get(scope)
        if target_dest is not None and _canonical_target(target_dest) == canonical:
            continue  # already covered by the target registry's own verbatim text
        existing_target = accepted_scope_to_target.get(scope)
        if existing_target is not None and _canonical_target(existing_target) != canonical:
            conflicts.append(f'scope_conflict:{scope}')
            continue
        existing_scope = accepted_target_to_scope.get(canonical)
        if existing_scope is not None and existing_scope != scope:
            conflicts.append(f'target_conflict:{canonical}')
            continue
        carried.append(RegistryMapping(scope, dest))
        accepted_scope_to_target[scope] = dest
        accepted_target_to_scope[canonical] = scope

    return RegistryPlan(
        carried=tuple(carried), dropped=tuple(dropped), conflicts=tuple(sorted(set(conflicts))))


def _write_registry(target_text: str, carried: tuple[RegistryMapping, ...]) -> str:
    """The target registry's own text, verbatim and product-owned,
    plus — only if there is anything to carry — a fenced block of
    `scope`/`→ target` pairs (the exact two-line shape
    `context_registry_entries` already parses) inserted right after the
    `## registered_scopes` heading. No registry writer framework: this
    is string templating of an already-understood shape, not a schema.
    """
    if not carried:
        return target_text
    lines = []
    for mapping in carried:
        lines.append(mapping.scope)
        lines.append(f'→ {mapping.target}')
    block = '```text\n' + '\n'.join(lines) + '\n```\n'
    idx = target_text.find(_REGISTRY_MARKER)
    if idx == -1:
        return target_text.rstrip('\n') + '\n\n' + block
    insert_at = target_text.find('\n', idx)
    if insert_at == -1:
        insert_at = len(target_text)
    else:
        insert_at += 1
    return target_text[:insert_at] + '\n' + block + target_text[insert_at:]


# --- classification -------------------------------------------------------

def classify_workspace(current_root: _PinnedRoot, pristine_root: _PinnedRoot,
                        exclude: frozenset[str] = frozenset()) -> SideBySidePlan:
    """Classify the current installation against the pristine target
    tree. No Git baseline exists for this path, so classification never
    infers history/authorship: a current-only `workspace/` file is
    reported as kept-from-current, never as "user-created"; equality is
    decided by content hash only, never mtime/size, read through the
    same root-anchored safe primitive the copy step uses.
    """
    current_files, current_unsafe = _scan_tree(current_root)
    pristine_files, _pristine_unsafe = _scan_tree(pristine_root)

    safe_exclude = frozenset(
        normalized for normalized in (normalize_relative(entry) for entry in exclude)
        if normalized is not None)

    kept: list[str] = []
    kept_hashes: list[tuple[str, str]] = []
    identical: list[str] = []
    conflicts: list[str] = []
    manual_resolution: list[str] = []
    excluded: list[str] = []
    unsafe_late: list[str] = []

    for relative in current_files:
        area = relative.split('/', 1)[0]
        current_hash = _hash_file(current_root, relative)
        if current_hash is None:
            unsafe_late.append(relative)
            continue
        if relative in pristine_files:
            pristine_hash = _hash_file(pristine_root, relative)
            if pristine_hash is None:
                unsafe_late.append(relative)
                continue
            same = current_hash == pristine_hash
            if area == 'workspace':
                (identical if same else conflicts).append(relative)
            elif not same:
                manual_resolution.append(relative)
        elif area == 'workspace':
            if relative in safe_exclude:
                excluded.append(relative)
            else:
                kept.append(relative)
                kept_hashes.append((relative, current_hash))
        else:
            manual_resolution.append(relative)

    # The resulting candidate's own file set — what a registry scope
    # directory being "preserved" actually means — is the pristine
    # target's regular files plus the current-only workspace files
    # selected to be kept, not the kept set alone.
    candidate_paths = frozenset(pristine_files) | frozenset(kept)
    registry = _registry_plan(current_root, pristine_root, candidate_paths)

    return SideBySidePlan(
        kept=tuple(sorted(kept)),
        kept_hashes=tuple(sorted(kept_hashes)),
        identical=tuple(sorted(identical)),
        conflicts=tuple(sorted(conflicts)),
        manual_resolution=tuple(sorted(manual_resolution)),
        rejected_unsafe=tuple(sorted(set(current_unsafe) | set(unsafe_late))),
        excluded=tuple(sorted(excluded)),
        registry=registry,
    )


# --- preview / digest -----------------------------------------------------

def _digest(plan: SideBySidePlan) -> str:
    lines = [f'target={plan.target}', f'pristine={plan.pristine_fingerprint}',
             f'blocked={plan.blocked or ""}']
    for name in ('kept', 'identical', 'conflicts', 'manual_resolution', 'rejected_unsafe', 'excluded'):
        for path in sorted(getattr(plan, name)):
            lines.append(f'{name}:{path}')
    for relative, digest in sorted(plan.kept_hashes):
        lines.append(f'kept_hash:{relative}:{digest}')
    for mapping in sorted(plan.registry.carried, key=lambda m: (m.scope, m.target)):
        lines.append(f'registry_carried:{mapping.scope}:{mapping.target}')
    for mapping in sorted(plan.registry.dropped, key=lambda m: (m.scope, m.target)):
        lines.append(f'registry_dropped:{mapping.scope}:{mapping.target}')
    for conflict in sorted(plan.registry.conflicts):
        lines.append(f'registry_conflict:{conflict}')
    return sha256('\n'.join(lines).encode('utf-8')).hexdigest()


def preview(current_root, destination, exclude: frozenset[str] = frozenset()) -> SideBySidePreview:
    """Resolve `T`, materialize and validate the pristine distribution
    into a throwaway location, classify the current installation
    against it, and bind everything into a digest. Never touches the
    real `destination` beyond the new/empty safety check — building the
    real one happens only in `migrate`, after reclassification.
    """
    current_root = Path(current_root)
    destination = Path(destination)
    try:
        resolved = target.resolve()
    except SourceUnavailable as error:
        return SideBySidePreview(_digest(SideBySidePlan(blocked=error.reason)),
                                  SideBySidePlan(blocked=error.reason))

    if not _destination_safe(destination, current_root):
        plan = SideBySidePlan(target=resolved.commit, blocked='destination_unsafe')
        return SideBySidePreview(_digest(plan), plan)

    current_pin = _pin_root(current_root)
    if current_pin is None:
        plan = SideBySidePlan(target=resolved.commit, blocked='unsafe_input')
        return SideBySidePreview(_digest(plan), plan)
    try:
        with tempfile.TemporaryDirectory(prefix='personal_sot_side_by_side_preview_') as tmp:
            pristine_tmp = Path(tmp, 'pristine')
            pristine_tmp.mkdir()
            if not build_pristine(pristine_tmp, resolved.commit):
                plan = SideBySidePlan(target=resolved.commit, blocked='target_materialization_failed')
                return SideBySidePreview(_digest(plan), plan)

            pristine_pin = _pin_root(pristine_tmp)
            if pristine_pin is None:
                plan = SideBySidePlan(target=resolved.commit, blocked='unsafe_input')
                return SideBySidePreview(_digest(plan), plan)
            try:
                if not _validate_pinned(pristine_pin, validate_pristine):
                    plan = SideBySidePlan(target=resolved.commit, blocked='pristine_validation_failed')
                    return SideBySidePreview(_digest(plan), plan)
                plan = classify_workspace(current_pin, pristine_pin, exclude=exclude)
                # The pinned fd keeps classification safely contained
                # even if `current_root`'s pathname was replaced
                # mid-classification, but a replaced pathname no longer
                # identifies the installation the caller selected — a
                # Plan built against a since-replaced root must never
                # be handed back as a usable, confirmable preview.
                if not _pinned_root_still_current(current_pin):
                    plan = SideBySidePlan(target=resolved.commit, blocked='stale_state')
                    return SideBySidePreview(_digest(plan), plan)
                plan = replace(
                    plan, target=resolved.commit, pristine_fingerprint=_fingerprint_tree(pristine_pin))
            finally:
                pristine_pin.close()
    finally:
        current_pin.close()

    return SideBySidePreview(_digest(plan), plan)


# --- migrate ---------------------------------------------------------------

def _expected_final_manifest(pristine_manifest: dict[str, str], kept_hashes: tuple[tuple[str, str], ...],
                              expected_registry_hash: str | None) -> dict[str, str]:
    """The ONE exact transient expected manifest a finished candidate
    must match: the pristine manifest, minus the registry entry (it is
    intentionally rewritten), plus every kept path's preview-bound
    content hash, plus the registry's expected reconstructed hash (or
    nothing at all for that path, if the pristine tree never shipped
    one and there is nothing to carry). Never written to disk.
    """
    manifest = {path: digest for path, digest in pristine_manifest.items() if path != _REGISTRY_REL_POSIX}
    for relative, digest in kept_hashes:
        manifest[relative] = digest
    if expected_registry_hash is not None:
        manifest[_REGISTRY_REL_POSIX] = expected_registry_hash
    return manifest


def _final_integrity_ok(destination: _PinnedRoot, expected_final_manifest: dict[str, str]) -> bool:
    """Verify the pinned destination's CURRENT file set exactly equals
    `expected_final_manifest` — same paths, same content hashes,
    nothing missing, nothing extra, no symlink/special path anywhere,
    and the pinned root's own identity still intact (via `_scan_tree`).
    Called both immediately before and immediately after the final
    Personal validators, since those validators' own runtime is itself
    a window a concurrent change could land in.
    """
    current_files, unsafe = _scan_tree(destination)
    if unsafe:
        return False
    if set(current_files) != set(expected_final_manifest):
        return False
    for relative, expected_hash in expected_final_manifest.items():
        if _hash_file(destination, relative) != expected_hash:
            return False
    return True


def migrate(current_root, destination, plan: SideBySidePlan, digest: str,
            exclude: frozenset[str] = frozenset(), _during_copy=None) -> MigrationResult:
    """Advance from a confirmed preview to a finished side-by-side
    candidate. Never trusts `plan`/`digest`: re-resolves `T`, rebuilds
    and revalidates the pristine distribution, and reclassifies the
    current installation before touching the real destination at all.

    The current installation and the real destination are each pinned
    ONCE — root-anchored, `O_DIRECTORY | O_NOFOLLOW` — and that SAME
    pin is reused for reclassification, every kept-file read/write, the
    registry replacement, and both integrity checks; neither root is
    ever re-derived from its pathname mid-operation, which is what
    actually closes a root-level substitution race, not merely adding
    `O_NOFOLLOW` to a repeated reopen. Each candidate-own validator
    subprocess is bracketed by a root-identity recheck, since a
    subprocess call necessarily takes a pathname argument.

    `_during_copy`, when given, is a test-only seam called once per
    kept file, immediately before it is copied; production callers
    never pass it.
    """
    current_root = Path(current_root)
    destination = Path(destination)

    if plan.blocked is not None:
        return MigrationResult(failure='blocked')
    if plan.conflicts or plan.registry.conflicts:
        return MigrationResult(failure='conflict')
    if plan.rejected_unsafe:
        return MigrationResult(failure='unsafe_input')

    try:
        resolved = target.resolve()
    except SourceUnavailable as error:
        return MigrationResult(failure=error.reason)

    if not _destination_safe(destination, current_root):
        return MigrationResult(failure='destination_unsafe')

    current_pin = _pin_root(current_root)
    if current_pin is None:
        return MigrationResult(failure='unsafe_input')
    try:
        return _migrate_with_current_pin(
            current_pin, destination, resolved.commit, exclude, digest, _during_copy)
    finally:
        current_pin.close()


def _migrate_with_current_pin(current_pin: _PinnedRoot, destination: Path, target_commit: str,
                               exclude: frozenset[str], digest: str, _during_copy) -> MigrationResult:
    with tempfile.TemporaryDirectory(prefix='personal_sot_side_by_side_recheck_') as tmp:
        recheck_pristine = Path(tmp, 'pristine')
        recheck_pristine.mkdir()
        if not build_pristine(recheck_pristine, target_commit):
            return MigrationResult(failure='target_materialization_failed')

        recheck_pin = _pin_root(recheck_pristine)
        if recheck_pin is None:
            return MigrationResult(failure='unsafe_input')
        try:
            if not _validate_pinned(recheck_pin, validate_pristine):
                return MigrationResult(
                    pristine_validation_ran=True, pristine_validation_passed=False,
                    failure='pristine_validation_failed')

            base_result = dict(pristine_validation_ran=True, pristine_validation_passed=True)

            fresh_plan = classify_workspace(current_pin, recheck_pin, exclude=exclude)
            # The pinned fd keeps classification safely contained even
            # if `current_root`'s pathname was replaced
            # mid-classification, but a replaced pathname no longer
            # identifies the installation the caller selected — never
            # trust a Plan built against a since-replaced root.
            if not _pinned_root_still_current(current_pin):
                return MigrationResult(**base_result, failure='stale_state')
            fresh_plan = replace(
                fresh_plan, target=target_commit, pristine_fingerprint=_fingerprint_tree(recheck_pin))
            fresh_digest = _digest(fresh_plan)

            if fresh_digest != digest:
                return MigrationResult(**base_result, failure='stale_state')
            if fresh_plan.conflicts or fresh_plan.registry.conflicts:
                return MigrationResult(**base_result, failure='conflict')
            if fresh_plan.rejected_unsafe:
                return MigrationResult(**base_result, failure='unsafe_input')

            if not build_pristine(destination, target_commit):
                return MigrationResult(**base_result, failure='target_materialization_failed')

            destination_pin = _pin_root(destination)
            if destination_pin is None:
                return MigrationResult(**base_result, failure='unsafe_input')
            try:
                return _migrate_into_pinned_destination(
                    current_pin, destination_pin, fresh_plan, base_result, _during_copy)
            finally:
                destination_pin.close()
        finally:
            recheck_pin.close()


def _migrate_into_pinned_destination(current_pin: _PinnedRoot, destination_pin: _PinnedRoot,
                                      fresh_plan: SideBySidePlan, base_result: dict,
                                      _during_copy) -> MigrationResult:
    if not _validate_pinned(destination_pin, validate_pristine):
        return MigrationResult(**base_result, failure='destination_pristine_validation_failed')
    if _fingerprint_tree(destination_pin) != fresh_plan.pristine_fingerprint:
        return MigrationResult(**base_result, failure='stale_state')

    pristine_manifest = _tree_manifest(destination_pin)
    expected_hashes = dict(fresh_plan.kept_hashes)

    migration_started = True
    for relative in fresh_plan.kept:
        # Pinning prevents a replaced `current_root` pathname from
        # redirecting reads to a substituted directory, but it does
        # NOT by itself mean the pinned fd still identifies the
        # installation the caller selected — a root replaced (by a
        # symlink OR by an entirely different real directory at the
        # same name) is a concurrent change that must stop the
        # migration, not one the updater silently keeps reading
        # through via the old fd. Rechecked both immediately before
        # and immediately after the `_during_copy` seam, since that
        # seam marks exactly the race window a concurrent rename/
        # replace would land in.
        if not _pinned_root_still_current(current_pin):
            return MigrationResult(
                **base_result, migration_started=migration_started, failure='concurrent_change')
        if _during_copy is not None:
            _during_copy(relative)
        if not _pinned_root_still_current(current_pin):
            return MigrationResult(
                **base_result, migration_started=migration_started, failure='concurrent_change')
        data = _safe_read_regular(current_pin, relative)
        if data is None or sha256(data).hexdigest() != expected_hashes.get(relative):
            return MigrationResult(
                **base_result, migration_started=migration_started, failure='concurrent_change')
        if not _safe_create_new_regular(destination_pin, relative, data):
            return MigrationResult(
                **base_result, migration_started=migration_started, failure='concurrent_change')
        if _hash_file(destination_pin, relative) != expected_hashes.get(relative):
            return MigrationResult(
                **base_result, migration_started=migration_started, failure='concurrent_change')

    pristine_registry_hash = pristine_manifest.get(_REGISTRY_REL_POSIX)
    if fresh_plan.registry.carried:
        if pristine_registry_hash is None:
            return MigrationResult(
                **base_result, migration_started=migration_started, failure='concurrent_change')
        target_registry_bytes = _safe_read_regular(destination_pin, _REGISTRY_REL_POSIX)
        if target_registry_bytes is None:
            return MigrationResult(
                **base_result, migration_started=migration_started, failure='concurrent_change')
        registry_text = _write_registry(
            target_registry_bytes.decode('utf-8'), fresh_plan.registry.carried)
        new_registry_bytes = registry_text.encode('utf-8')
        if not _safe_replace_existing_regular(
                destination_pin, _REGISTRY_REL_POSIX, pristine_registry_hash, new_registry_bytes):
            return MigrationResult(
                **base_result, migration_started=migration_started, failure='concurrent_change')
        expected_registry_hash = sha256(new_registry_bytes).hexdigest()
    else:
        expected_registry_hash = pristine_registry_hash

    expected_final = _expected_final_manifest(
        pristine_manifest, fresh_plan.kept_hashes, expected_registry_hash)

    if not _final_integrity_ok(destination_pin, expected_final):
        return MigrationResult(
            **base_result, migration_started=migration_started, failure='concurrent_change')

    if not _pinned_root_still_current(destination_pin):
        return MigrationResult(
            **base_result, migration_started=migration_started, failure='concurrent_change')
    personal_ok, prompts_ok = validate_candidate(destination_pin.path)
    if not _pinned_root_still_current(destination_pin):
        return MigrationResult(
            **base_result, migration_started=migration_started,
            personal_validation_ran=True, personal_validation_passed=False,
            failure='concurrent_change')
    if not (personal_ok and prompts_ok):
        return MigrationResult(
            **base_result, migration_started=migration_started,
            personal_validation_ran=True, personal_validation_passed=False,
            failure='personal_validation_failed')

    if not _final_integrity_ok(destination_pin, expected_final):
        return MigrationResult(
            **base_result, migration_started=migration_started,
            personal_validation_ran=True, personal_validation_passed=True,
            failure='concurrent_change')

    return MigrationResult(
        **base_result, migration_started=migration_started,
        personal_validation_ran=True, personal_validation_passed=True, ready=True)
