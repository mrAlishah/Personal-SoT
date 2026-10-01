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


def _open_root_fd(root: Path):
    try:
        return os.open(str(root), os.O_RDONLY | os.O_DIRECTORY)
    except OSError:
        return None


def _safe_stat_kind(root: Path, relative: str) -> str:
    """`'absent'` if `relative` under `root` safely does not exist,
    `'regular'` if it is confirmed — root-anchored, one `openat()` per
    path component with `O_NOFOLLOW`, never a symlink anywhere along
    the way, not merely the final component — to be a regular file, or
    `'unsafe'` for anything else (a symlink anywhere in the path, a
    special file, or no safe no-follow primitive on this platform at
    all). Distinguishing "absent" from "unsafe" matters because a
    legitimately missing file (no current registry customization, say)
    must not be treated the same as one hidden behind a symlink.
    """
    if not _NOFOLLOW_SUPPORTED:
        return 'unsafe'
    parts = _root_anchored_parts(relative)
    if not parts:
        return 'unsafe'
    root_fd = _open_root_fd(root)
    if root_fd is None:
        return 'unsafe'
    opened = [root_fd]
    try:
        parent = root_fd
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


def _safe_read_regular(root: Path, relative: str) -> bytes | None:
    """Read the bytes of `relative` under `root`, root-anchored: one
    `openat(..., O_NOFOLLOW)` per path component — every intermediate
    directory and the final component alike — never a plain pathname
    open, which an intermediate symlink swapped in after some earlier
    check (or simply planted in advance) would silently follow out of
    the selected root. `fstat` on the SAME descriptor the bytes are
    read from confirms it is a regular file; there is no separate
    `lstat`-then-reopen step for a race to land in. Returns `None` —
    never raises — for any expected `OSError` anywhere along the walk
    (missing, a symlink, a special file, permission denied) or if this
    platform has no safe no-follow primitive at all, so an unsafe or
    concurrently-changed source is always a bounded failure, never an
    uncaught exception that could carry a Personal path.
    """
    if not _NOFOLLOW_SUPPORTED:
        return None
    parts = _root_anchored_parts(relative)
    if not parts:
        return None
    root_fd = _open_root_fd(root)
    if root_fd is None:
        return None
    opened = [root_fd]
    try:
        parent = root_fd
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


def _safe_create_new_regular(root: Path, relative: str, data: bytes) -> bool:
    """Create a NEW regular file at `relative` under `root`,
    root-anchored through every intermediate component (each must
    already be, or safely become, a verified real directory — never a
    symlink). `O_CREAT | O_EXCL | O_NOFOLLOW` on the final component
    means this fails closed if anything already exists there, rather
    than silently overwriting it or following a pre-planted symlink —
    correct for a kept path, which the pristine target already proved
    does not exist yet.
    """
    if not _NOFOLLOW_SUPPORTED:
        return False
    parts = _root_anchored_parts(relative)
    if not parts:
        return False
    root_fd = _open_root_fd(root)
    if root_fd is None:
        return False
    opened = [root_fd]
    try:
        parent = root_fd
        for part in parts[:-1]:
            fd = _safe_ensure_dir(parent, part)
            if fd is None:
                return False
            opened.append(fd)
            parent = fd
        try:
            final_fd = os.open(
                parts[-1], os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o644, dir_fd=parent)
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


def _safe_replace_existing_regular(root: Path, relative: str, expected_before_hash: str,
                                    new_bytes: bytes) -> bool:
    """Replace the content of an EXISTING, target-owned file (only the
    registry, currently) root-anchored and via a single read-write
    descriptor: opens it once with `O_NOFOLLOW`, confirms it is a
    regular file whose current bytes still hash to
    `expected_before_hash`, then truncates and rewrites THAT SAME
    descriptor — never a separate write-mode reopen, which would leave
    its own TOCTOU gap between verifying and writing.
    """
    if not _NOFOLLOW_SUPPORTED:
        return False
    parts = _root_anchored_parts(relative)
    if not parts:
        return False
    root_fd = _open_root_fd(root)
    if root_fd is None:
        return False
    opened = [root_fd]
    try:
        parent = root_fd
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


def _scan_tree(root: Path) -> tuple[dict[str, Path], tuple[str, ...]]:
    """One bounded host-side walk of `root`. Returns
    (`{relative_posix_path: absolute_path}` for every REGULAR file,
    sorted unsafe relative paths). A symlink (file or directory) or any
    other special file type (FIFO/device/socket) is never followed or
    read — only reported as unsafe. Directories are traversal structure
    only. `followlinks=False` already stops `os.walk` from descending
    into a symlinked directory; the explicit `os.path.islink` filter
    below additionally keeps it out of `dirnames` so it is never even
    `scandir`'d, and is reported once as unsafe rather than silently
    skipped. Content itself is never read through this walk — every
    actual read goes through the root-anchored `_safe_read_regular`
    separately, which closes the TOCTOU window this walk alone cannot.
    """
    root = Path(root)
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
    paths, `..` traversal, symlink members, and hardlink members —
    defense in depth even though an ordinary `git archive` of tracked
    content should not produce any of these except a tracked symlink.
    """
    try:
        with tarfile.open(fileobj=BytesIO(archive_bytes)) as tf:
            for member in tf.getmembers():
                if member.issym() or member.islnk():
                    return False
                if not (member.isfile() or member.isdir()):
                    return False
                posix = PurePosixPath(member.name)
                if posix.is_absolute() or '..' in posix.parts:
                    return False
            tf.extractall(destination, filter='data')
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


def _hash_file(root: Path, relative: str) -> str | None:
    data = _safe_read_regular(root, relative)
    if data is None:
        return None
    return sha256(data).hexdigest()


def _tree_manifest(root: Path) -> dict[str, str]:
    """`{relative_posix_path: content_hash}` for every regular file
    under `root`, read via `_safe_read_regular`; a path that fails that
    safe read (unreadable/raced/not actually regular by the time it is
    opened) is simply omitted — never silently treated as empty or as
    a cache-coherent value.
    """
    files, _unsafe = _scan_tree(root)
    manifest = {}
    for relative in files:
        digest = _hash_file(root, relative)
        if digest is not None:
            manifest[relative] = digest
    return manifest


def _fingerprint_tree(root: Path) -> str:
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


def _safe_registry_text(root: Path) -> tuple[str, bool]:
    """(`text`, `ok`) for the CURRENT installation's own registry file,
    read through the same root-anchored safe boundary as any other
    current input. A legitimately absent registry is `('', True)` — no
    customization at all. `ok=False` means the path exists but is
    unsafe (a symlink anywhere along it, or a special file) — never
    silently treated as an empty/absent registry, which would let a
    symlink-hidden registry's mappings simply vanish rather than
    blocking the migration.
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
    `workspace/context/`, including an unsafe/traversal-shaped one) is
    also a conflict and excluded from the accepted maps entirely.
    `validate_public`/`validate_v1`'s own registry check does not cover
    every one of these ownership classes, especially target-alias
    ownership, so this loop cannot assume pristine validation already
    proved registry integrity.
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


def _registry_plan(current_root: Path, pristine_root: Path, candidate_paths: frozenset[str]) -> RegistryPlan:
    """Read both registries exclusively with `context_registry_entries`
    (never a second parser) — the current one through the root-anchored
    safe read boundary, since a symlink-hidden registry must block
    migration rather than silently parse as empty; the pristine one
    directly, since it lives inside the already-validated/fingerprinted
    pristine tree. Keep only current mappings whose canonical target is
    a `workspace/context/` directory actually present in the resulting
    candidate's own file set, and fail closed on a genuine scope/target
    ownership conflict — including an exact duplicate, and a
    trailing-slash alias of an already-claimed target — within current
    entries, or against a validated target registry, rather than
    silently choosing either side.
    """
    current_text, current_registry_ok = _safe_registry_text(current_root)
    target_text = _read_text_or_empty(pristine_root / _REGISTRY_RELATIVE)
    current_entries = context_registry_entries(current_text)
    target_entries = context_registry_entries(target_text)

    accepted_scope_to_target, accepted_target_to_scope, conflicts = _validated_target_registry(target_entries)
    provided_by_target = set(accepted_scope_to_target.items())

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
        preserved = any(
            path == canonical or path.startswith(canonical + '/') for path in candidate_paths)
        if not preserved:
            dropped.append(RegistryMapping(scope, dest))
            continue
        if (scope, dest) in provided_by_target:
            continue  # already present in the target registry verbatim
        existing_target = accepted_scope_to_target.get(scope)
        if existing_target is not None and existing_target != dest:
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

def classify_workspace(current_root: Path, pristine_root: Path,
                        exclude: frozenset[str] = frozenset()) -> SideBySidePlan:
    """Classify the current installation against the pristine target
    tree. No Git baseline exists for this path, so classification never
    infers history/authorship: a current-only `workspace/` file is
    reported as kept-from-current, never as "user-created"; equality is
    decided by content hash only, never mtime/size, read through the
    same root-anchored safe primitive the copy step uses, so
    classification itself can never be tricked into following a raced
    intermediate or final symlink either.
    """
    current_root = Path(current_root)
    pristine_root = Path(pristine_root)
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
    # selected to be kept, not the kept set alone: a scope already
    # shipped by T, or identically present on both sides, is just as
    # preserved as one that only exists because of a kept file.
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

    with tempfile.TemporaryDirectory(prefix='personal_sot_side_by_side_preview_') as tmp:
        pristine_tmp = Path(tmp, 'pristine')
        pristine_tmp.mkdir()
        if not build_pristine(pristine_tmp, resolved.commit):
            plan = SideBySidePlan(target=resolved.commit, blocked='target_materialization_failed')
            return SideBySidePreview(_digest(plan), plan)
        if not validate_pristine(pristine_tmp):
            plan = SideBySidePlan(target=resolved.commit, blocked='pristine_validation_failed')
            return SideBySidePreview(_digest(plan), plan)
        plan = classify_workspace(current_root, pristine_tmp, exclude=exclude)
        plan = replace(plan, target=resolved.commit, pristine_fingerprint=_fingerprint_tree(pristine_tmp))

    return SideBySidePreview(_digest(plan), plan)


# --- migrate ---------------------------------------------------------------

def _expected_final_manifest(pristine_manifest: dict[str, str], kept_hashes: tuple[tuple[str, str], ...],
                              expected_registry_hash: str | None) -> dict[str, str]:
    """The ONE exact transient expected manifest a finished candidate
    must match: the pristine manifest, minus the registry entry (it is
    intentionally rewritten), plus every kept path's preview-bound
    content hash, plus the registry's expected reconstructed hash (or
    nothing at all for that path, if the pristine tree never shipped
    one and there is nothing to carry). Never written to disk — derived
    fresh for this one migration.
    """
    manifest = {path: digest for path, digest in pristine_manifest.items() if path != _REGISTRY_REL_POSIX}
    for relative, digest in kept_hashes:
        manifest[relative] = digest
    if expected_registry_hash is not None:
        manifest[_REGISTRY_REL_POSIX] = expected_registry_hash
    return manifest


def _final_integrity_ok(destination: Path, expected_final_manifest: dict[str, str]) -> bool:
    """Verify the destination's CURRENT file set exactly equals
    `expected_final_manifest` — same paths, same content hashes,
    nothing missing, nothing extra, no symlink/special path anywhere —
    reading every file through the root-anchored safe primitive. Called
    both immediately before and immediately after the final Personal
    validators, since those validators' own (possibly non-trivial)
    runtime is itself a window a concurrent change could land in.
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

    The REAL destination's own just-built pristine tree is itself
    validated and fingerprint-checked before any Personal/current file
    enters it — validating only the throwaway recheck tree is not
    equivalent, since the real destination is a separate extraction
    that could itself be concurrently tampered with. Every current
    source read and every destination write (a new kept file, or the
    registry replacement) is root-anchored through the safe primitives
    above, so no intermediate symlink anywhere in either tree can be
    followed. The complete exact expected final manifest is checked
    twice — immediately before and immediately after the final Personal
    validators — closing the window their own runtime would otherwise
    leave open.

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

    with tempfile.TemporaryDirectory(prefix='personal_sot_side_by_side_recheck_') as tmp:
        recheck_pristine = Path(tmp, 'pristine')
        recheck_pristine.mkdir()
        if not build_pristine(recheck_pristine, resolved.commit):
            return MigrationResult(failure='target_materialization_failed')

        pristine_ok = validate_pristine(recheck_pristine)
        if not pristine_ok:
            return MigrationResult(
                pristine_validation_ran=True, pristine_validation_passed=False,
                failure='pristine_validation_failed')

        fresh_plan = classify_workspace(current_root, recheck_pristine, exclude=exclude)
        fresh_plan = replace(
            fresh_plan, target=resolved.commit, pristine_fingerprint=_fingerprint_tree(recheck_pristine))
        fresh_digest = _digest(fresh_plan)

        base_result = dict(pristine_validation_ran=True, pristine_validation_passed=True)

        if fresh_digest != digest:
            return MigrationResult(**base_result, failure='stale_state')
        if fresh_plan.conflicts or fresh_plan.registry.conflicts:
            return MigrationResult(**base_result, failure='conflict')
        if fresh_plan.rejected_unsafe:
            return MigrationResult(**base_result, failure='unsafe_input')

        if not build_pristine(destination, resolved.commit):
            return MigrationResult(**base_result, failure='target_materialization_failed')

        # The REAL destination is itself validated and fingerprinted —
        # a separate extraction from recheck_pristine, so validating
        # only the throwaway tree does not prove this one is genuinely
        # pristine (it may have been built concurrently-tampered-with,
        # or simply differ for any other reason).
        if not validate_pristine(destination):
            return MigrationResult(
                **base_result, failure='destination_pristine_validation_failed')
        if _fingerprint_tree(destination) != fresh_plan.pristine_fingerprint:
            return MigrationResult(**base_result, failure='stale_state')

        pristine_manifest = _tree_manifest(destination)
        expected_hashes = dict(fresh_plan.kept_hashes)

        migration_started = True
        for relative in fresh_plan.kept:
            if _during_copy is not None:
                _during_copy(relative)
            data = _safe_read_regular(current_root, relative)
            if data is None or sha256(data).hexdigest() != expected_hashes.get(relative):
                return MigrationResult(
                    **base_result, migration_started=migration_started, failure='concurrent_change')
            if not _safe_create_new_regular(destination, relative, data):
                return MigrationResult(
                    **base_result, migration_started=migration_started, failure='concurrent_change')
            if _hash_file(destination, relative) != expected_hashes.get(relative):
                return MigrationResult(
                    **base_result, migration_started=migration_started, failure='concurrent_change')

        pristine_registry_hash = pristine_manifest.get(_REGISTRY_REL_POSIX)
        if fresh_plan.registry.carried:
            if pristine_registry_hash is None:
                return MigrationResult(
                    **base_result, migration_started=migration_started, failure='concurrent_change')
            target_registry_bytes = _safe_read_regular(destination, _REGISTRY_REL_POSIX)
            if target_registry_bytes is None:
                return MigrationResult(
                    **base_result, migration_started=migration_started, failure='concurrent_change')
            registry_text = _write_registry(
                target_registry_bytes.decode('utf-8'), fresh_plan.registry.carried)
            new_registry_bytes = registry_text.encode('utf-8')
            if not _safe_replace_existing_regular(
                    destination, _REGISTRY_REL_POSIX, pristine_registry_hash, new_registry_bytes):
                return MigrationResult(
                    **base_result, migration_started=migration_started, failure='concurrent_change')
            expected_registry_hash = sha256(new_registry_bytes).hexdigest()
        else:
            expected_registry_hash = pristine_registry_hash

        expected_final = _expected_final_manifest(
            pristine_manifest, fresh_plan.kept_hashes, expected_registry_hash)

        if not _final_integrity_ok(destination, expected_final):
            return MigrationResult(
                **base_result, migration_started=migration_started, failure='concurrent_change')

        personal_ok, prompts_ok = validate_candidate(destination)
        if not (personal_ok and prompts_ok):
            return MigrationResult(
                **base_result, migration_started=migration_started,
                personal_validation_ran=True, personal_validation_passed=False,
                failure='personal_validation_failed')

        if not _final_integrity_ok(destination, expected_final):
            return MigrationResult(
                **base_result, migration_started=migration_started,
                personal_validation_ran=True, personal_validation_passed=True,
                failure='concurrent_change')

        return MigrationResult(
            **base_result, migration_started=migration_started,
            personal_validation_ran=True, personal_validation_passed=True, ready=True)
