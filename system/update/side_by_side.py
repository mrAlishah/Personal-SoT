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
    skipped.
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


def _hash_file(path: Path) -> str:
    return sha256(path.read_bytes()).hexdigest()


def _fingerprint_tree(root: Path) -> str:
    """A deterministic hash over the pristine tree's own
    (relative_path, content_hash) pairs, sorted — the staleness signal
    for "has the materialized pristine distribution itself changed",
    bound into the preview digest.
    """
    files, _unsafe = _scan_tree(root)
    lines = [f'{relative}:{_hash_file(path)}' for relative, path in sorted(files.items())]
    return sha256('\n'.join(lines).encode('utf-8')).hexdigest()


# --- registry carry-over -------------------------------------------------

def _read_text_or_empty(path: Path) -> str:
    return path.read_text(encoding='utf-8') if path.is_file() else ''


def _registry_plan(current_root: Path, pristine_root: Path, kept_workspace: frozenset[str]) -> RegistryPlan:
    """Read both registries exclusively with `context_registry_entries`
    (never a second parser), keep only current mappings whose target is
    a preserved `workspace/context/` directory, and fail closed on a
    genuine scope/target conflict rather than silently choosing either
    side.
    """
    current_text = _read_text_or_empty(current_root / _REGISTRY_RELATIVE)
    target_text = _read_text_or_empty(pristine_root / _REGISTRY_RELATIVE)
    current_entries = context_registry_entries(current_text)
    target_entries = context_registry_entries(target_text)

    accepted_scope_to_target: dict[str, str] = {}
    accepted_target_to_scope: dict[str, str] = {}
    for scope, dest in target_entries:
        accepted_scope_to_target.setdefault(scope, dest)
        accepted_target_to_scope.setdefault(dest, scope)
    provided_by_target = set(accepted_scope_to_target.items())

    carried: list[RegistryMapping] = []
    dropped: list[RegistryMapping] = []
    conflicts: list[str] = []

    for scope, dest in current_entries:
        if not SCOPE_RE.fullmatch(scope):
            conflicts.append(f'invalid_scope:{scope}')
            continue
        normalized = dest.rstrip('/')
        if not normalized.startswith('workspace/context/'):
            dropped.append(RegistryMapping(scope, dest))
            continue
        preserved = any(
            path == normalized or path.startswith(normalized + '/') for path in kept_workspace)
        if not preserved:
            dropped.append(RegistryMapping(scope, dest))
            continue
        if (scope, dest) in provided_by_target:
            continue  # already present in the target registry verbatim
        existing_target = accepted_scope_to_target.get(scope)
        if existing_target is not None and existing_target != dest:
            conflicts.append(f'scope_conflict:{scope}')
            continue
        existing_scope = accepted_target_to_scope.get(dest)
        if existing_scope is not None and existing_scope != scope:
            conflicts.append(f'target_conflict:{dest}')
            continue
        carried.append(RegistryMapping(scope, dest))
        accepted_scope_to_target[scope] = dest
        accepted_target_to_scope[dest] = scope

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
    decided by content hash only, never mtime/size.
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

    for relative, absolute in current_files.items():
        area = relative.split('/', 1)[0]
        if relative in pristine_files:
            same = _hash_file(absolute) == _hash_file(pristine_files[relative])
            if area == 'workspace':
                (identical if same else conflicts).append(relative)
            elif not same:
                manual_resolution.append(relative)
        elif area == 'workspace':
            if relative in safe_exclude:
                excluded.append(relative)
            else:
                kept.append(relative)
                kept_hashes.append((relative, _hash_file(absolute)))
        else:
            manual_resolution.append(relative)

    registry = _registry_plan(current_root, pristine_root, frozenset(kept))

    return SideBySidePlan(
        kept=tuple(sorted(kept)),
        kept_hashes=tuple(sorted(kept_hashes)),
        identical=tuple(sorted(identical)),
        conflicts=tuple(sorted(conflicts)),
        manual_resolution=tuple(sorted(manual_resolution)),
        rejected_unsafe=tuple(sorted(set(current_unsafe))),
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

def migrate(current_root, destination, plan: SideBySidePlan, digest: str,
            exclude: frozenset[str] = frozenset()) -> MigrationResult:
    """Advance from a confirmed preview to a finished side-by-side
    candidate. Never trusts `plan`/`digest`: re-resolves `T`, rebuilds
    and revalidates the pristine distribution, and reclassifies the
    current installation before touching the real destination at all.
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

        target_registry_text = _read_text_or_empty(destination / _REGISTRY_RELATIVE)
        expected_hashes = dict(fresh_plan.kept_hashes)

        migration_started = True
        for relative in fresh_plan.kept:
            source = Path(current_root, relative)
            try:
                st = source.lstat()
            except OSError:
                return MigrationResult(
                    **base_result, migration_started=migration_started, failure='concurrent_change')
            if not stat.S_ISREG(st.st_mode):
                return MigrationResult(
                    **base_result, migration_started=migration_started, failure='concurrent_change')
            data = source.read_bytes()
            if sha256(data).hexdigest() != expected_hashes.get(relative):
                return MigrationResult(
                    **base_result, migration_started=migration_started, failure='concurrent_change')
            dest_path = Path(destination, relative)
            dest_path.parent.mkdir(parents=True, exist_ok=True)
            dest_path.write_bytes(data)
            if sha256(dest_path.read_bytes()).hexdigest() != expected_hashes.get(relative):
                return MigrationResult(
                    **base_result, migration_started=migration_started, failure='concurrent_change')

        registry_path = Path(destination, _REGISTRY_RELATIVE)
        registry_path.parent.mkdir(parents=True, exist_ok=True)
        registry_path.write_text(
            _write_registry(target_registry_text, fresh_plan.registry.carried), encoding='utf-8')

        personal_ok, prompts_ok = validate_candidate(destination)
        if not (personal_ok and prompts_ok):
            return MigrationResult(
                **base_result, migration_started=migration_started,
                personal_validation_ran=True, personal_validation_passed=False,
                failure='personal_validation_failed')

        return MigrationResult(
            **base_result, migration_started=migration_started,
            personal_validation_ran=True, personal_validation_passed=True, ready=True)
