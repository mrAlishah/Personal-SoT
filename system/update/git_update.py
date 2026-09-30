"""Safe Update Git-clone classification and preview; see update_contract.md.

Read-only: never mutates the installed clone's ref, index, worktree, remote
configuration, remote-tracking refs, FETCH_HEAD, or object database. `T`'s
objects are materialized into an updater-owned ephemeral bare repository,
never the live checkout; the live repository's own objects are attached to
it read-only, and only after target fetch/verification finishes, so no
installed-clone object id ever reaches the canonical fetch's negotiation.
"""
from __future__ import annotations

from contextlib import contextmanager
from dataclasses import dataclass
from hashlib import sha256
from io import BytesIO
from pathlib import Path
import re
import subprocess
import sys
import tarfile
import tempfile

from system.connectors.source import SourceUnavailable
from system.update import target
from system.update.target import controlled_git

_SHA_RE = re.compile(r'[0-9a-f]{40}')
# A replace ref on the live repo's own HEAD (or an ancestor) can make `git
# status`/`rev-parse` resolve a substituted tree instead of the real one,
# corrupting dirty-state and current-commit reads; every live-repo read
# that walks a commit's tree must disable replace-object interpretation.
_NO_REPLACE = {'GIT_NO_REPLACE_OBJECTS': '1'}
# A driver subsection name may itself contain dots (`[filter "foo.bar"]`
# flattens to the config key `filter.foo.bar.clean`), so the driver-name
# group must be greedy up to the final known suffix, not a single
# dot-free segment; matched against the key alone (see `_configured_drivers`),
# never the raw "key value" line, so a value containing a dot-suffix-like
# substring can never be mistaken for part of the driver name.
_DRIVER_KEY_RE = re.compile(r'^(?:filter|diff)\.(.+)\.(?:clean|smudge|process|textconv|command)$')
_ATTRIBUTE_SCAN_KEYS = (
    r'^filter\..+\.(clean|smudge|process)$',
    r'^diff\..+\.(textconv|command)$',
)
# Closed, product-owned area vocabulary: a beginner-facing area label must
# never be derived from a user-controlled filename or directory name, so a
# user-only path can never leak into the summary via its own area label.
_KNOWN_AREAS = frozenset({'workspace', 'system', 'guides'})


@dataclass(frozen=True)
class Plan:
    current: str
    target: str
    base: str | None
    already_aligned: tuple[str, ...] = ()
    upstream_only: tuple[str, ...] = ()
    user_only: tuple[str, ...] = ()
    conflict: tuple[str, ...] = ()
    no_op: bool = False
    blocked: str | None = None
    blocked_by_area: tuple[tuple[str, int], ...] = ()


@dataclass(frozen=True)
class Preview:
    digest: str
    plan: Plan
    summary: dict


class TargetMaterializationError(Exception):
    def __init__(self, reason: str):
        self.reason = reason
        super().__init__(reason)


class _SimulatedFailure(Exception):
    """Test-only injection marker for an updater-controlled failure after
    live mutation has begun (see `apply`'s `_after_mutation` parameter).

    `apply` catches only this exception type inside its post-mutation
    window and routes it into the recovery path, matching a real
    controlled failure (e.g. a step that raises after detecting bad
    state). Any other exception propagates uncaught, exactly as a real
    process kill/crash would, so a test can tell the two situations apart
    without a second, separate simulation mechanism.
    """


@dataclass(frozen=True)
class ApplyResult:
    """Truthful outcome of one `apply()` call; see update_contract.md.

    Every field defaults to the safe/unstarted value, so a result built
    for an early abort never has to remember to clear a later field.
    `failure` is a closed, non-sensitive literal (never raw Git/validator
    output or a `workspace/` path); `commit` is the resulting SHA only on
    a successful, actually-applied update.
    """
    no_op: bool = False
    mutation_started: bool = False
    validation_ran: bool = False
    validation_passed: bool = False
    rollback_attempted: bool = False
    rollback_completed: bool = False
    concurrent_change: bool = False
    commit: str | None = None
    failure: str | None = None


def classify(root) -> Plan:
    """Resolve C, T, B and classify every path per the design's state table."""
    root = str(root)
    blocked = _preflight(root)
    if blocked is not None:
        return blocked

    current = _current_commit(root)
    if current is None:
        return Plan('', '', None, blocked='head_unresolved')

    try:
        resolved = target.resolve()
    except SourceUnavailable as error:
        return Plan(current, '', None, blocked=error.reason)

    git_dir = _git_dir(root)
    if git_dir is None:
        return Plan(current, resolved.commit, None, blocked='git_dir_unresolved')
    objects_dir = str(Path(git_dir, 'objects'))
    extra_env = {'GIT_ALTERNATE_OBJECT_DIRECTORIES': objects_dir, 'GIT_NO_REPLACE_OBJECTS': '1'}

    try:
        with _materialized_target(resolved.commit) as ephemeral:
            base = _merge_base(ephemeral, current, resolved.commit, extra_env)
            if base is None:
                return Plan(current, resolved.commit, None, blocked='unrelated_lineage')
            if base is _AMBIGUOUS:
                return Plan(current, resolved.commit, None, blocked='ambiguous_lineage')
            base_tree = _ls_tree(ephemeral, base, extra_env)
            current_tree = _ls_tree(ephemeral, current, extra_env)
            target_tree = _ls_tree(ephemeral, resolved.commit, extra_env)
    except TargetMaterializationError as error:
        return Plan(current, resolved.commit, None, blocked=error.reason)

    aligned, upstream_only, user_only, conflict = _states(base_tree, current_tree, target_tree)
    # Equivalent to (and subsumes) C == T, T ancestor of C, independently
    # converged identical trees, and a target commit with no effective
    # tree delta: no upstream-driven change remains to apply, and nothing
    # is left unresolved that a downgrade/silent-merge would paper over.
    no_op = not upstream_only and not conflict
    return Plan(current, resolved.commit, base, aligned, upstream_only, user_only, conflict, no_op)


def preview(plan: Plan) -> Preview:
    """Bind C, T, B and the classified Plan into a deterministic digest."""
    lines = [
        f'current={plan.current}',
        f'target={plan.target}',
        f'base={plan.base or ""}',
        f'no_op={int(plan.no_op)}',
        f'blocked={plan.blocked or ""}',
    ]
    for state in ('already_aligned', 'upstream_only', 'user_only', 'conflict'):
        for path in sorted(getattr(plan, state)):
            lines.append(f'{state}:{path}')
    for area, count in sorted(plan.blocked_by_area):
        lines.append(f'blocked_by_area:{area}:{count}')
    digest = sha256('\n'.join(lines).encode('utf-8')).hexdigest()
    return Preview(digest, plan, _beginner_summary(plan))


# --- dirty/untracked preflight -------------------------------------------

def _porcelain_v2_paths(stdout: str) -> list[str]:
    """The one current-path per `git status --porcelain=v2 -z` record.

    A bounded parser for exactly the record types `-z` mode (no path
    quoting, NUL-terminated) can emit without `--ignored`: ordinary
    changed (`1`), renamed/copied (`2`, whose origPath is a separate
    following NUL-terminated item that must be skipped rather than
    counted as its own record), unmerged (`u`), and untracked (`?`).
    `-z` mode is required here specifically because a path may contain
    spaces or other characters that plain porcelain output would need to
    quote/escape.
    """
    chunks = stdout.split('\0')
    if chunks and chunks[-1] == '':
        chunks = chunks[:-1]
    paths = []
    skip_next = False
    for chunk in chunks:
        if skip_next:
            skip_next = False
            continue
        if not chunk:
            continue
        kind = chunk[0]
        if kind == '1':
            paths.append(chunk.split(' ', 8)[8])
        elif kind == '2':
            paths.append(chunk.split(' ', 9)[9])
            skip_next = True
        elif kind == 'u':
            paths.append(chunk.split(' ', 10)[10])
        elif kind == '?':
            paths.append(chunk.split(' ', 1)[1])
    return paths


def _preflight(root) -> Plan | None:
    if _attribute_safety_blocked(root):
        return Plan('', '', None, blocked='unsafe_repository_state')
    status = controlled_git(
        '--no-optional-locks', '-c', 'core.fsmonitor=false',
        'status', '--porcelain=v2', '-z', '--untracked-files=all', cwd=root,
        extra_env=_NO_REPLACE)
    if status.returncode != 0:
        return Plan('', '', None, blocked='status_check_failed')
    paths = _porcelain_v2_paths(status.stdout or '')
    if not paths:
        return None
    counts: dict[str, int] = {}
    for path in paths:
        area = _area(path)
        counts[area] = counts.get(area, 0) + 1
    return Plan('', '', None, blocked='dirty_or_untracked', blocked_by_area=tuple(sorted(counts.items())))


def _configured_drivers(root) -> set[str] | None:
    """The set of driver names any filter/diff clean/smudge/process/textconv
    hook is configured under, or `None` if the config itself could not be
    read (a fail-closed signal, distinct from an empty/legitimate set).

    Extracted so Loop 3's target-introduced-attribute safety check (which
    driver names are configured on this machine) reuses exactly this Loop 2
    logic rather than re-deriving it.
    """
    configured = set()
    for pattern in _ATTRIBUTE_SCAN_KEYS:
        config = controlled_git('config', '--get-regexp', pattern, cwd=root)
        if config.returncode not in (0, 1):
            return None
        for line in (config.stdout or '').splitlines():
            # Match only the key (everything before the first space); the
            # value may itself contain text that looks like a dot-suffix,
            # which must never be mistaken for part of the driver name.
            key = line.split(' ', 1)[0]
            match = _DRIVER_KEY_RE.match(key)
            if match:
                configured.add(match.group(1))
    return configured


def _attribute_safety_blocked(root) -> bool:
    """True when accurate dirty-state inspection would require executing a
    configured clean/smudge/process/textconv helper.

    Uses Git's own attribute-resolution plumbing (`git check-attr`), not a
    hand-written .gitattributes parser, so nested .gitattributes files and
    .git/info/attributes are resolved exactly as an actual `git status`
    invocation under the same isolated environment would resolve them.
    """
    configured = _configured_drivers(root)
    if configured is None:
        return True
    if not configured:
        return False

    files = controlled_git(
        '--no-optional-locks', '-c', 'core.fsmonitor=false', 'ls-files', '-z', cwd=root)
    if files.returncode != 0:
        return True
    paths = [path for path in (files.stdout or '').split('\0') if path]
    if not paths:
        return False

    check = controlled_git(
        '--no-optional-locks', '-c', 'core.fsmonitor=false',
        'check-attr', '--all', '-z', '--', *paths, cwd=root)
    if check.returncode != 0:
        return True
    fields = (check.stdout or '').split('\0')
    if fields and fields[-1] == '':
        fields = fields[:-1]
    for _path, attribute, info in zip(fields[0::3], fields[1::3], fields[2::3]):
        if attribute in ('filter', 'diff') and info in configured:
            return True
    return False


def _current_commit(root) -> str | None:
    result = controlled_git('rev-parse', '--verify', 'HEAD', cwd=root, extra_env=_NO_REPLACE)
    if result.returncode != 0:
        return None
    sha = (result.stdout or '').strip()
    return sha if _SHA_RE.fullmatch(sha) else None


def _git_dir(root) -> str | None:
    result = controlled_git('rev-parse', '--git-dir', cwd=root)
    if result.returncode != 0:
        return None
    path = (result.stdout or '').strip()
    if not path:
        return None
    return path if Path(path).is_absolute() else str(Path(root, path))


# --- target materialization -----------------------------------------------

@contextmanager
def _materialized_target(commit: str):
    with tempfile.TemporaryDirectory(prefix='personal_sot_update_target_') as ephemeral:
        init = controlled_git('init', '--bare', '.', cwd=ephemeral)
        if init.returncode != 0:
            raise TargetMaterializationError('ephemeral_init_failed')
        fetch = controlled_git(
            'fetch', target.CANONICAL_URL,
            'refs/heads/' + target.CANONICAL_REF + ':refs/heads/_target',
            cwd=ephemeral)
        if fetch.returncode != 0:
            raise TargetMaterializationError('target_fetch_failed')
        verify = controlled_git('rev-parse', '--verify', 'refs/heads/_target', cwd=ephemeral)
        fetched = (verify.stdout or '').strip()
        if verify.returncode != 0 or fetched != commit:
            raise TargetMaterializationError('stale_target')
        yield ephemeral


# --- classification ---------------------------------------------------------

_AMBIGUOUS = object()


def _merge_base(ephemeral, current, commit, extra_env):
    result = controlled_git('merge-base', '--all', current, commit, cwd=ephemeral, extra_env=extra_env)
    if result.returncode not in (0, 1):
        raise TargetMaterializationError('merge_base_unavailable')
    lines = [line for line in (result.stdout or '').splitlines() if line]
    if not lines:
        return None
    if len(lines) > 1:
        return _AMBIGUOUS
    return lines[0]


def _ls_tree(ephemeral, tree_ish, extra_env):
    result = controlled_git('ls-tree', '-r', '-z', tree_ish, cwd=ephemeral, extra_env=extra_env)
    if result.returncode != 0:
        raise TargetMaterializationError('tree_unreadable')
    entries = {}
    for record in (result.stdout or '').split('\0'):
        if not record:
            continue
        meta, _, path = record.partition('\t')
        mode, obj_type, blob_sha = meta.split(' ')
        if obj_type == 'blob':
            entries[path] = (mode, blob_sha)
    return entries


def _states(base_tree, current_tree, target_tree):
    aligned, upstream_only, user_only, conflict = [], [], [], []
    for path in sorted(set(base_tree) | set(current_tree) | set(target_tree)):
        b, c, t = base_tree.get(path), current_tree.get(path), target_tree.get(path)
        if c == t:
            aligned.append(path)
        elif c == b and t != b:
            upstream_only.append(path)
        elif t == b and c != b:
            user_only.append(path)
        else:
            conflict.append(path)
    return tuple(aligned), tuple(upstream_only), tuple(user_only), tuple(conflict)


# --- beginner-safe summary ---------------------------------------------------

def _beginner_summary(plan: Plan) -> dict:
    """Naming boundary is classification state, not location: aligned,
    upstream_only, and conflict paths all have an established relationship
    to accepted target history (T changed, deleted, or converged on them);
    user_only paths never do, so they are area/count only regardless of
    where they sit, including outside workspace/.
    """
    named = tuple(sorted(plan.already_aligned + plan.upstream_only + plan.conflict))
    hidden_by_area: dict[str, int] = {}
    for path in plan.user_only:
        area = _area(path)
        hidden_by_area[area] = hidden_by_area.get(area, 0) + 1
    return {
        'named': named,
        'hidden_by_area': hidden_by_area,
        'blocked_by_area': dict(plan.blocked_by_area),
    }


def _area(path: str) -> str:
    """A closed, product-owned area label only: `workspace`/`system`/
    `guides` for those known roots, `root` for a top-level file, `other`
    for anything else — never a user-controlled filename or directory
    name, so a user-only or dirty path can never leak into the
    beginner-facing summary via its own area label.
    """
    if '/' not in path:
        return 'root'
    top = path.split('/', 1)[0]
    return top if top in _KNOWN_AREAS else 'other'


# --- Loop 3: recoverable Git apply + Personal validation -------------------

def _candidate_entries(plan: Plan, target_tree, current_tree) -> dict[str, tuple[str, str]]:
    """The final (mode, blob sha) per path the candidate tree must have:
    target's entry for already_aligned/upstream_only paths (aligned means
    they already match; upstream_only means the update introduces or
    changes them), current's entry for user_only paths (preserved exactly
    as-is). A path absent from the relevant tree is a deletion and is
    simply omitted. Never called with a non-empty `plan.conflict` — `apply`
    refuses before this point in that case.
    """
    entries: dict[str, tuple[str, str]] = {}
    for path in plan.already_aligned + plan.upstream_only:
        entry = target_tree.get(path)
        if entry is not None:
            entries[path] = entry
    for path in plan.user_only:
        entry = current_tree.get(path)
        if entry is not None:
            entries[path] = entry
    return entries


def _build_tree(entries: dict[str, tuple[str, str]], ephemeral, extra_env) -> str:
    """Build a Git tree object for exactly `entries` (path -> (mode, blob
    sha)), creating intermediate subtrees bottom-up: `git mktree` only
    accepts one non-recursive directory level per invocation, so a path
    containing `/` needs its parent subtree built first.
    """
    root: dict = {}
    for path, entry in entries.items():
        parts = path.split('/')
        node = root
        for part in parts[:-1]:
            node = node.setdefault(part, {})
        node[parts[-1]] = entry

    def build(node: dict) -> str:
        lines = []
        for name, value in node.items():
            if isinstance(value, dict):
                sub_sha = build(value)
                lines.append(f'040000 tree {sub_sha}\t{name}')
            else:
                mode, sha = value
                lines.append(f'{mode} blob {sha}\t{name}')
        result = controlled_git(
            'mktree', cwd=ephemeral, extra_env=extra_env, input='\n'.join(lines) + '\n')
        if result.returncode != 0:
            raise TargetMaterializationError('candidate_tree_build_failed')
        return (result.stdout or '').strip()

    return build(root)


def _candidate_attribute_unsafe(ephemeral, candidate_tree_sha, touched_paths, configured, extra_env) -> bool:
    """True when any updater-touched path would, under the candidate's own
    `.gitattributes` (which the update may itself introduce or change),
    select a filter/diff driver this machine has configured — checked with
    Git's own attribute plumbing directly against the candidate tree via
    `--source`, never a hand-written parser, and never by executing the
    helper. Only `upstream_only` paths are ever touched (aligned/user_only
    paths are never written), so only those need checking.
    """
    if not touched_paths or not configured:
        return False
    check = controlled_git(
        'check-attr', '--source', candidate_tree_sha, '--all', '-z', '--', *touched_paths,
        cwd=ephemeral, extra_env=extra_env)
    if check.returncode != 0:
        return True
    fields = (check.stdout or '').split('\0')
    if fields and fields[-1] == '':
        fields = fields[:-1]
    for _path, attribute, info in zip(fields[0::3], fields[1::3], fields[2::3]):
        if attribute in ('filter', 'diff') and info in configured:
            return True
    return False


@contextmanager
def _extracted_candidate(ephemeral, candidate_tree_sha, extra_env):
    """Materialize the candidate tree into a fresh directory OUTSIDE the
    live checkout (`git archive` + a real extraction, never a hand-rolled
    tree walk), alive for exactly as long as validation needs it.
    """
    archive = controlled_git(
        'archive', '--format=tar', candidate_tree_sha, cwd=ephemeral, extra_env=extra_env,
        text=False)
    if archive.returncode != 0:
        raise TargetMaterializationError('candidate_archive_failed')
    with tempfile.TemporaryDirectory(prefix='personal_sot_update_candidate_') as candidate_root:
        with tarfile.open(fileobj=BytesIO(archive.stdout)) as tf:
            tf.extractall(candidate_root, filter='data')
        yield Path(candidate_root)


def _validate_candidate(candidate_root: Path) -> tuple[bool, bool]:
    """Run the CANDIDATE's own validators, as separate subprocesses rooted
    at the candidate's own files — never `validate_public`. A subprocess
    (rather than an in-process call) guarantees `system.validation.*` and
    everything it imports resolves fresh from the candidate tree's own
    files, not from whatever version this process already has cached in
    `sys.modules` from the live checkout, so a target that itself changes
    validator logic is validated against its OWN rules, not stale ones.
    """
    personal = subprocess.run(
        [sys.executable, '-B', str(candidate_root / 'system' / 'validation' / 'validate_v1.py'),
         '--mode', 'personal'],
        cwd=str(candidate_root), capture_output=True, text=True, timeout=60)
    prompts = subprocess.run(
        [sys.executable, '-B', str(candidate_root / 'system' / 'validation' / 'validate_prompts.py')],
        cwd=str(candidate_root), capture_output=True, text=True, timeout=60)
    return personal.returncode == 0, prompts.returncode == 0


def _transfer_objects(ephemeral, current, commit_t, candidate_tree_sha, root, extra_env) -> bool:
    """Copy exactly the objects the live repo is missing (T's history not
    already reachable from C, plus the candidate tree and anything it
    references) into the live repo's own object database, using
    `rev-list --objects` + `pack-objects` + `index-pack` — a pure content
    transfer with no remote/URL argument at all, so no repository-local
    `url.*.insteadOf` rewrite has anything to redirect.
    """
    new_from_target = controlled_git(
        'rev-list', '--objects', commit_t, '--not', current, cwd=ephemeral, extra_env=extra_env)
    if new_from_target.returncode != 0:
        return False
    candidate_closure = controlled_git(
        'rev-list', '--objects', candidate_tree_sha, cwd=ephemeral, extra_env=extra_env)
    if candidate_closure.returncode != 0:
        return False
    names = set()
    for line in (new_from_target.stdout or '').splitlines() + (candidate_closure.stdout or '').splitlines():
        line = line.strip()
        if line:
            names.add(line.split(' ', 1)[0])
    if not names:
        return True
    pack = controlled_git(
        'pack-objects', '--stdout', cwd=ephemeral, extra_env=extra_env,
        input=('\n'.join(sorted(names)) + '\n').encode('utf-8'), text=False)
    if pack.returncode != 0:
        return False
    unpack = controlled_git(
        'index-pack', '--stdin', cwd=root, extra_env=extra_env, input=pack.stdout, text=False)
    return unpack.returncode == 0


def _provenance_message(current: str, commit_t: str) -> str:
    return f'Safe Update: apply canonical target\n\nbaseline={current}\ntarget={commit_t}\n'


def _mutate_touched(root, touched_paths, target_tree, candidate_root, extra_env) -> dict:
    """Write/remove exactly the updater-touched paths in the live worktree
    and index; `already_aligned`/`user_only` paths are never written, so
    their existing index entries and mtimes are left completely alone.

    Returns a recovery record `{path: (before_bytes_or_None,
    written_bytes_or_None)}` captured as each path is mutated — the sole
    basis both for restoring on a controlled failure and for detecting
    that an external process has since changed a path the updater itself
    wrote.
    """
    record: dict = {}
    for path in touched_paths:
        file_path = Path(root, path)
        before = file_path.read_bytes() if file_path.is_file() else None
        if path in target_tree:
            mode, _sha = target_tree[path]
            written = Path(candidate_root, path).read_bytes()
            file_path.parent.mkdir(parents=True, exist_ok=True)
            file_path.write_bytes(written)
            file_path.chmod(0o755 if mode == '100755' else 0o644)
            result = controlled_git('update-index', '--add', '--', path, cwd=root, extra_env=extra_env)
        else:
            written = None
            if file_path.exists():
                file_path.unlink()
            result = controlled_git('update-index', '--remove', '--', path, cwd=root, extra_env=extra_env)
        if result.returncode != 0:
            raise TargetMaterializationError('index_update_failed')
        record[path] = (before, written)
    return record


def _restore_touched(root, record: dict, extra_env) -> bool:
    """Restore each touched path to its pre-update content, but only for a
    path whose current on-disk content still equals exactly what the
    updater itself wrote; any path an external process has changed since
    is left untouched, and recovery is reported incomplete rather than
    overwriting it.
    """
    complete = True
    for path, (before, written) in record.items():
        file_path = Path(root, path)
        current_bytes = file_path.read_bytes() if file_path.is_file() else None
        if current_bytes != written:
            complete = False
            continue
        if before is None:
            if file_path.exists():
                file_path.unlink()
            controlled_git('update-index', '--remove', '--', path, cwd=root, extra_env=extra_env)
        else:
            file_path.parent.mkdir(parents=True, exist_ok=True)
            file_path.write_bytes(before)
            controlled_git('update-index', '--add', '--', path, cwd=root, extra_env=extra_env)
    return complete


def apply(root, plan: Plan, digest: str, _after_mutation=None, _before_recheck=None) -> ApplyResult:
    """Advance the installed clone from `plan.current` to `plan.target`,
    recoverably, per update_contract.md's apply/recovery section.

    Never trusts the caller's `plan`: re-resolves T and re-classifies
    before doing anything, and aborts before any mutation on any mismatch
    against `digest`, on `blocked`, or on a remaining `conflict`. A no-op
    classification never mutates and never creates a commit. The live
    ref/index/worktree are not touched until the candidate has passed both
    Personal validators and an immediate clean-state recheck; the ref
    advances last, with a compare-and-swap old-value check.

    `_before_recheck` and `_after_mutation`, when given, are test-only
    seams; production callers never pass them. `_before_recheck` is called
    exactly once right after validation, before the immediate pre-mutation
    recheck runs — for simulating a real external write landing in that
    window and proving the recheck actually catches it.  `_after_mutation`
    is called exactly once after the live worktree/index have been
    mutated but before the ref advances — for simulating a concurrent
    external change or a controlled post-mutation failure (raise
    `_SimulatedFailure` to trigger the recovery path; any other exception
    propagates uncaught, exactly as a real process kill/crash would).
    """
    root = str(root)
    fresh_plan = classify(root)
    fresh_preview = preview(fresh_plan)
    if fresh_preview.digest != digest:
        return ApplyResult(failure='stale_state')
    if fresh_plan.blocked is not None:
        return ApplyResult(failure='blocked')
    if fresh_plan.conflict:
        return ApplyResult(failure='conflict')
    if fresh_plan.no_op:
        return ApplyResult(no_op=True)

    current = fresh_plan.current
    commit_t = fresh_plan.target

    git_dir = _git_dir(root)
    if git_dir is None:
        return ApplyResult(failure='git_dir_unresolved')
    objects_dir = str(Path(git_dir, 'objects'))
    extra_env = {'GIT_ALTERNATE_OBJECT_DIRECTORIES': objects_dir, 'GIT_NO_REPLACE_OBJECTS': '1'}

    configured = _configured_drivers(root)
    if configured is None:
        return ApplyResult(failure='status_check_failed')

    try:
        with _materialized_target(commit_t) as ephemeral:
            target_tree = _ls_tree(ephemeral, commit_t, extra_env)
            current_tree = _ls_tree(ephemeral, current, extra_env)
            candidate_entries = _candidate_entries(fresh_plan, target_tree, current_tree)
            candidate_tree_sha = _build_tree(candidate_entries, ephemeral, extra_env)

            touched_paths = fresh_plan.upstream_only
            if _candidate_attribute_unsafe(
                    ephemeral, candidate_tree_sha, touched_paths, configured, extra_env):
                return ApplyResult(failure='unsafe_repository_state')

            with _extracted_candidate(ephemeral, candidate_tree_sha, extra_env) as candidate_root:
                personal_ok, prompts_ok = _validate_candidate(candidate_root)
                if not (personal_ok and prompts_ok):
                    return ApplyResult(
                        validation_ran=True, validation_passed=False, failure='validation_failed')

                if _before_recheck is not None:
                    _before_recheck()

                # Immediate pre-mutation recheck: never trust the state
                # validated above to still hold by the time we get here.
                if _preflight(root) is not None or _current_commit(root) != current:
                    return ApplyResult(
                        validation_ran=True, validation_passed=True,
                        failure='concurrent_change_pre_mutation', concurrent_change=True)

                if not _transfer_objects(ephemeral, current, commit_t, candidate_tree_sha, root, extra_env):
                    return ApplyResult(
                        validation_ran=True, validation_passed=True, failure='object_transfer_failed')

                commit_result = controlled_git(
                    'commit-tree', candidate_tree_sha, '-p', current, '-p', commit_t,
                    cwd=root, extra_env=extra_env, input=_provenance_message(current, commit_t))
                if commit_result.returncode != 0:
                    return ApplyResult(
                        validation_ran=True, validation_passed=True, failure='object_transfer_failed')
                new_commit = (commit_result.stdout or '').strip()

                record = _mutate_touched(root, touched_paths, target_tree, candidate_root, extra_env)

                write_tree = controlled_git('write-tree', cwd=root, extra_env=extra_env)
                if write_tree.returncode != 0 or (write_tree.stdout or '').strip() != candidate_tree_sha:
                    rollback_completed = _restore_touched(root, record, extra_env)
                    return ApplyResult(
                        mutation_started=True, validation_ran=True, validation_passed=True,
                        rollback_attempted=True, rollback_completed=rollback_completed,
                        concurrent_change=not rollback_completed, failure='index_mismatch')

                try:
                    if _after_mutation is not None:
                        _after_mutation()
                except _SimulatedFailure:
                    rollback_completed = _restore_touched(root, record, extra_env)
                    return ApplyResult(
                        mutation_started=True, validation_ran=True, validation_passed=True,
                        rollback_attempted=True, rollback_completed=rollback_completed,
                        concurrent_change=not rollback_completed, failure='post_mutation_failure')

                cas = controlled_git(
                    'update-ref', 'HEAD', new_commit, current, cwd=root, extra_env=extra_env)
                if cas.returncode != 0:
                    rollback_completed = _restore_touched(root, record, extra_env)
                    return ApplyResult(
                        mutation_started=True, validation_ran=True, validation_passed=True,
                        rollback_attempted=True, rollback_completed=rollback_completed,
                        concurrent_change=True, failure='ref_cas_failed')

                return ApplyResult(
                    mutation_started=True, validation_ran=True, validation_passed=True, commit=new_commit)
    except TargetMaterializationError as error:
        return ApplyResult(failure=error.reason)
