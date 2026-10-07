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
import os
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
    root = os.path.abspath(os.fspath(root))
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


def _candidate_path_conflict(entries: dict) -> bool:
    """True when `entries` cannot form a legal Git tree: some path is a
    blob/symlink entry while another path in the same set begins with
    that path plus `/`, which would require it to also be a directory.
    Git cannot represent both at once, and ordinary per-path
    classification (Loop 2) cannot see this — it compares each flattened
    path independently, so a user-only file at `workspace/x` and an
    upstream-only descendant `workspace/x/y.md` can each classify with
    no conflict of their own while still being jointly impossible.

    Sorting first makes this an adjacent-pairs check: if `path` is a
    strict prefix (plus `/`) of another entry, that other entry sorts
    immediately after it lexicographically, with nothing able to sort
    between them.
    """
    paths = sorted(entries)
    for earlier, later in zip(paths, paths[1:]):
        if later.startswith(earlier + '/'):
            return True
    return False


def _ordered_touched_paths(touched_paths, target_tree) -> list:
    """Order `touched_paths` so a legal Git directory<->file transition
    (one touched path vacates a name by being deleted, another touched
    path claims that same name as a file, or the reverse) applies
    without a spurious `IsADirectoryError`/`FileExistsError`: every
    deletion (a path absent from `target_tree`) before every
    creation/modification, deletions ordered deepest-first and
    creations ordered shallowest-first, so a directory's descendants are
    gone before its own name is freed for reuse, and a claimed name's
    old file is gone before a descendant needs it as a directory.
    """
    deletions = [path for path in touched_paths if path not in target_tree]
    creations = [path for path in touched_paths if path in target_tree]
    deletions.sort(key=lambda path: path.count('/'), reverse=True)
    creations.sort(key=lambda path: path.count('/'))
    return deletions + creations


def _ordered_recovery_paths(record: dict) -> list:
    """The same dependency-safe ordering as `_ordered_touched_paths`, but
    toward restoring the PREVIOUS (pre-update) state: a path whose
    `before_entry` is absent needs removing (undoing a forward
    creation), deepest-first; a path whose `before_entry` exists needs
    recreating (undoing a forward deletion), shallowest-first.
    """
    removals = [path for path, (before, _written) in record.items() if before is None]
    recreations = [path for path, (before, _written) in record.items() if before is not None]
    removals.sort(key=lambda path: path.count('/'), reverse=True)
    recreations.sort(key=lambda path: path.count('/'))
    return removals + recreations


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
        # mktree consumes a Git plumbing protocol whose record terminator is
        # LF, not the host platform's text newline. Passing a str through
        # subprocess text mode on Windows translates LF to CRLF; mktree then
        # treats the stray CR bytes as part of path components and creates a
        # tree that git archive rejects as an invalid Windows path. Send the
        # protocol as bytes so its framing is identical on every platform.
        payload = ('\n'.join(lines) + '\n').encode('utf-8')
        result = controlled_git(
            'mktree', cwd=ephemeral, extra_env=extra_env, input=payload, text=False)
        if result.returncode != 0:
            raise TargetMaterializationError('candidate_tree_build_failed')
        try:
            return (result.stdout or b'').decode('ascii').strip()
        except UnicodeDecodeError as error:
            raise TargetMaterializationError('candidate_tree_build_failed') from error

    return build(root)


def _candidate_attribute_unsafe(root, ephemeral, candidate_tree_sha, touched_paths, configured) -> bool:
    """True when any updater-touched path would, under EITHER the
    candidate's own `.gitattributes` (which the update may itself
    introduce or change) OR the installed clone's own
    `.git/info/attributes` (which a tracked `.gitattributes` cannot
    override and a candidate-only check therefore cannot see), select a
    filter/diff driver this machine has configured — checked with Git's
    own attribute plumbing, never a hand-written parser, and never by
    executing the helper.

    This runs `check-attr --source=<candidate-tree>` in the LIVE repo
    itself (`root`), with the candidate's (and target's) objects made
    visible read-only through `GIT_ALTERNATE_OBJECT_DIRECTORIES` pointed
    at the ephemeral repository — never the other way around — so Git's
    own attribute-precedence rules apply `.git/info/attributes` exactly
    as a real `git status`/`checkout` in this repository would, while the
    `.gitattributes` content itself still comes from the candidate tree.
    Running the same check inside the ephemeral repository instead would
    silently miss `root`'s own `.git/info/attributes`.

    Only `upstream_only` paths are ever touched (aligned/user_only paths
    are never written), so only those need checking.
    """
    if not touched_paths or not configured:
        return False
    extra_env = {'GIT_ALTERNATE_OBJECT_DIRECTORIES': str(Path(ephemeral, 'objects')),
                 'GIT_NO_REPLACE_OBJECTS': '1'}
    check = controlled_git(
        'check-attr', '--source', candidate_tree_sha, '--all', '-z', '--', *touched_paths,
        cwd=root, extra_env=extra_env)
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


def _identify_worktree_entry(root, path, extra_env) -> tuple | None:
    """The `(mode, blob sha)` the live worktree path would hash to right
    now, computed by explicit blob hashing (`--no-filters`, never a
    configured clean filter) rather than by letting `update-index --add`
    re-hash it through Git's normal content-based path. `None` if the
    path does not currently exist.
    """
    file_path = Path(root, path)
    if file_path.is_symlink():
        result = controlled_git(
            'hash-object', '--stdin', '-t', 'blob', cwd=root, extra_env=extra_env,
            input=os.readlink(file_path))
        if result.returncode != 0:
            return None
        return ('120000', (result.stdout or '').strip())
    if file_path.is_file():
        result = controlled_git(
            'hash-object', '--no-filters', '--', path, cwd=root, extra_env=extra_env)
        if result.returncode != 0:
            return None
        mode = '100755' if os.access(file_path, os.X_OK) else '100644'
        return (mode, (result.stdout or '').strip())
    return None


def _identify_index_entry(root, path, extra_env) -> tuple | None:
    """The `(mode, blob sha)` the live INDEX currently has staged for
    `path`, or `None` if the path is not staged there at all.

    `git ls-files -- <path>` treats `path` as a pathspec, not a literal
    exact-path lookup: when `path` itself is absent but a descendant
    like `<path>/y.md` is tracked, it matches that descendant instead —
    so the one chunk returned is only trusted after confirming its own
    reported path is exactly `path`, never merely checking that *some*
    chunk came back.
    """
    result = controlled_git(
        '--no-optional-locks', 'ls-files', '--stage', '-z', '--', path, cwd=root, extra_env=extra_env)
    if result.returncode != 0:
        return None
    chunk = (result.stdout or '').split('\0', 1)[0]
    if not chunk:
        return None
    meta, _, reported_path = chunk.partition('\t')
    if reported_path != path:
        return None
    parts = meta.split(' ')
    if len(parts) < 2:
        return None
    return (parts[0], parts[1])


def _clear_path(file_path: Path) -> None:
    """Remove whatever currently occupies `file_path` so a new entry can
    claim that name: a plain file or symlink via `unlink()`, or a
    directory via `rmdir()` — which raises `OSError` on its own if that
    directory is not empty, the correct fail-closed outcome. Never
    `rmtree`; a directory's own descendants are always removed as their
    own touched paths first (see `_ordered_touched_paths`), never by
    recursing into unknown/untracked contents here.
    """
    if file_path.is_symlink():
        file_path.unlink()
    elif file_path.is_dir():
        file_path.rmdir()
    elif file_path.exists():
        file_path.unlink()


def _write_entry(ephemeral, root, path, entry, extra_env) -> tuple[bool, bool]:
    """Make the live worktree+index at `path` exactly match `entry` (a
    `(mode, blob sha)` tuple, or `None` for absent).

    Returns `(success, attempted_mutation)`. `attempted_mutation` is
    `False` only when the failure happened during this function's
    read-only resolution step (`cat-file`, before any live worktree/index
    write was even attempted) — this is what the caller's
    `mutation_started` truthfully depends on, not merely on having
    entered the per-path loop. Content is resolved by the blob's exact
    object identity (`git cat-file -p`) and staged with `update-index
    --add --cacheinfo <mode>,<sha>,<path>` — never plain `update-index
    --add`, which re-hashes the worktree file through Git's normal
    content-based path and can invoke a configured clean filter. A Git
    symlink mode (`120000`) is materialized as a real symlink, never
    collapsed to a regular file. Any real filesystem error (`OSError` —
    a permission-denied directory, a non-empty directory occupying a
    name a file needs to claim, etc.) encountered once a write has
    actually begun is caught here and reported as a bounded failure,
    never left to escape uncaught past the caller's mutation loop.
    """
    file_path = Path(root, path)
    if entry is None:
        try:
            _clear_path(file_path)
            result = controlled_git(
                'update-index', '--force-remove', '--', path, cwd=root, extra_env=extra_env)
        except OSError:
            return False, True
        return result.returncode == 0, True
    mode, sha = entry
    blob = controlled_git('cat-file', '-p', sha, cwd=ephemeral, extra_env=extra_env, text=False)
    if blob.returncode != 0:
        return False, False
    try:
        file_path.parent.mkdir(parents=True, exist_ok=True)
        _clear_path(file_path)
        if mode == '120000':
            os.symlink(blob.stdout.decode('utf-8'), file_path)
        else:
            file_path.write_bytes(blob.stdout)
            file_path.chmod(0o755 if mode == '100755' else 0o644)
    except OSError:
        return False, True
    result = controlled_git(
        'update-index', '--add', '--cacheinfo', f'{mode},{sha},{path}', cwd=root, extra_env=extra_env)
    return result.returncode == 0, True


def _restore_entry(ephemeral, root, path, before_entry, written_entry, extra_env) -> bool:
    """Restore `path` to `before_entry`, but only if its CURRENT worktree
    AND index state each still equal exactly `written_entry` (what the
    updater itself wrote) or already equal `before_entry` (nothing to
    do, e.g. this path was never reached before a sibling path's
    mutation failed); any other current state means an external process
    has touched it since, and it is left completely untouched — neither
    worktree nor index — rather than risk overwriting that change.
    """
    current_worktree = _identify_worktree_entry(root, path, extra_env)
    current_index = _identify_index_entry(root, path, extra_env)
    safe_states = (before_entry, written_entry)
    if current_worktree not in safe_states or current_index not in safe_states:
        return False
    if current_worktree == before_entry and current_index == before_entry:
        return True
    ok, _attempted = _write_entry(ephemeral, root, path, before_entry, extra_env)
    return ok


def _post_mutation_integrity_ok(root, ephemeral, candidate_tree_sha, touched_paths, record,
                                 extra_env) -> bool:
    """Verify, immediately before the ref CAS, that the live installation
    genuinely still equals the validated candidate and nothing else has
    drifted since the mutation loop finished — this is what closes the
    window a controlled post-mutation event that tampers with live state
    WITHOUT raising (a worktree or index change to a touched path, an
    untouched tracked path, or a new untracked file) would otherwise
    leave open for `apply` to advance the ref and report success anyway.

    Does NOT itself re-check `HEAD == current`: the ref CAS immediately
    following this is already the atomic, authoritative check for ref
    drift (a separate read-then-later-CAS here would only add its own
    TOCTOU gap); ref concurrency is `update-ref`'s job, worktree/index/
    attribute concurrency is this function's.

    Re-reads configured drivers and re-checks attribute safety (both the
    general dirty-state one and the target-introduced-path one) before
    running the one status-like command this function issues, exactly
    as the dirty/untracked preflight does, so this gate itself can never
    need to execute a configured helper to decide anything. Content
    identity only — never a text comparison.

    That one status call passes `--no-renames`: Git's own rename/copy
    detection can otherwise present "delete an untouched path, create a
    touched path with identical content" as a single porcelain-v2 type-2
    record whose reported current path is the touched one — exactly the
    shape `_porcelain_v2_paths` (correct for Loop 2's coarse area/count
    semantics, which this function does not touch) reports as only that
    one current path, silently hiding the untouched path's deletion.
    `--no-renames` is a command-level flag, so this is deterministic
    regardless of the repository's own `status.renames`/`diff.renames`
    configuration.
    """
    configured = _configured_drivers(root)
    if configured is None or _attribute_safety_blocked(root):
        return False
    if _candidate_attribute_unsafe(root, ephemeral, candidate_tree_sha, touched_paths, configured):
        return False
    for path in touched_paths:
        _before, written_entry = record[path]
        if (_identify_worktree_entry(root, path, extra_env) != written_entry
                or _identify_index_entry(root, path, extra_env) != written_entry):
            return False
    status = controlled_git(
        '--no-optional-locks', 'status', '--porcelain=v2', '-z', '--no-renames',
        '--untracked-files=all', cwd=root, extra_env=extra_env)
    if status.returncode != 0:
        return False
    changed = set(_porcelain_v2_paths(status.stdout or ''))
    return changed <= set(touched_paths)


def _attempt_recovery(ephemeral, root, record: dict, extra_env) -> bool:
    """Restore every touched path in `record` to its pre-update state, in
    dependency-safe order toward that previous state (see
    `_ordered_recovery_paths` — the same reasoning `_write_entry`'s
    forward ordering uses, reversed); complete only if every single path
    was safely restorable (see `_restore_entry`) — one externally-changed
    path is enough to make this `False`, even though the other paths
    were still restored.
    """
    complete = True
    for path in _ordered_recovery_paths(record):
        before_entry, written_entry = record[path]
        if not _restore_entry(ephemeral, root, path, before_entry, written_entry, extra_env):
            complete = False
    return complete




def apply(root, plan: Plan, digest: str, _after_mutation=None, _before_recheck=None,
          _before_path=None) -> ApplyResult:
    """Advance the installed clone from `plan.current` to `plan.target`,
    recoverably, per update_contract.md's apply/recovery section.

    Never trusts the caller's `plan`: re-resolves T and re-classifies
    before doing anything, and aborts before any mutation on any mismatch
    against `digest`, on `blocked`, or on a remaining `conflict`. A no-op
    classification never mutates and never creates a commit.

    Building the candidate tree, validating it, transferring missing
    objects, and constructing the (as yet unreachable) resulting commit
    object never touch the live ref/index/worktree, so they happen before
    the FINAL recheck rather than after it — that recheck (clean tracked
    state, `HEAD` still at `C`, and target-introduced attribute safety
    re-evaluated against the live repository's current
    `.git/info/attributes`/config, not just the one taken before
    validation) is the last thing before the first live write, closing
    the window validation's own real work leaves open. A further
    per-path check immediately precedes each individual touched path's
    own write, comparing its current worktree AND index identity against
    the verified pre-update state recorded for it — a single global
    recheck cannot catch a later path changing while an earlier path is
    still being written. The ref advances last, with a compare-and-swap
    old-value check.

    `_before_recheck`, `_before_path`, and `_after_mutation`, when given,
    are test-only seams; production callers never pass them.
    `_before_recheck` is called exactly once right after validation,
    before the FINAL recheck runs. `_before_path` is called once per
    touched path, with that path, immediately before its own per-path
    concurrency check and write. `_after_mutation` is called exactly once
    after the live worktree/index have been mutated but before the ref
    advances — for simulating a concurrent external change or a
    controlled post-mutation failure (raise `_SimulatedFailure` to
    trigger the recovery path; any other exception propagates uncaught,
    exactly as a real process kill/crash would).
    """
    root = os.path.abspath(os.fspath(root))
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
            if _candidate_path_conflict(candidate_entries):
                return ApplyResult(failure='candidate_path_conflict')
            candidate_tree_sha = _build_tree(candidate_entries, ephemeral, extra_env)

            touched_paths = _ordered_touched_paths(fresh_plan.upstream_only, target_tree)
            if _candidate_attribute_unsafe(root, ephemeral, candidate_tree_sha, touched_paths, configured):
                return ApplyResult(failure='unsafe_repository_state')

            with _extracted_candidate(ephemeral, candidate_tree_sha, extra_env) as candidate_root:
                personal_ok, prompts_ok = _validate_candidate(candidate_root)
                if not (personal_ok and prompts_ok):
                    return ApplyResult(
                        validation_ran=True, validation_passed=False, failure='validation_failed')

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

                if _before_recheck is not None:
                    _before_recheck()

                # FINAL recheck, immediately before the first live write:
                # never trust anything validation/transfer/commit-tree
                # observed to still hold by the time we get here.
                final_configured = _configured_drivers(root)
                if (_preflight(root) is not None or _current_commit(root) != current
                        or final_configured is None
                        or _candidate_attribute_unsafe(
                            root, ephemeral, candidate_tree_sha, touched_paths, final_configured)):
                    return ApplyResult(
                        validation_ran=True, validation_passed=True,
                        failure='concurrent_change_pre_mutation', concurrent_change=True)

                # Record every touched path's (before, written) tree
                # identity up front — including paths not yet reached if
                # a sibling path's write fails below — so recovery can
                # treat "never actually mutated" as a trivially safe
                # no-op via the same before/written comparison, rather
                # than losing track of what happened on a partial failure.
                record = {path: (current_tree.get(path), target_tree.get(path))
                          for path in touched_paths}

                write_ok = True
                mutation_started = False
                per_path_concurrent = False
                for path in touched_paths:
                    if _before_path is not None:
                        _before_path(path)
                    before_entry, written_entry = record[path]
                    # Per-path concurrency check: a single check at the
                    # top of this function cannot see a LATER path change
                    # while an EARLIER path is still being written.
                    if (_identify_worktree_entry(root, path, extra_env) != before_entry
                            or _identify_index_entry(root, path, extra_env) != before_entry):
                        per_path_concurrent = True
                        write_ok = False
                        break
                    ok, attempted = _write_entry(ephemeral, root, path, written_entry, extra_env)
                    mutation_started = mutation_started or attempted
                    if not ok:
                        write_ok = False
                        break

                if write_ok:
                    write_tree = controlled_git('write-tree', cwd=root, extra_env=extra_env)
                    write_ok = (write_tree.returncode == 0
                                and (write_tree.stdout or '').strip() == candidate_tree_sha)

                if write_ok:
                    try:
                        if _after_mutation is not None:
                            _after_mutation()
                    except _SimulatedFailure:
                        write_ok = False

                # Final post-mutation integrity gate, after whatever
                # _after_mutation just simulated: a real concurrent event
                # in this exact window need not raise to be dangerous —
                # it must still be caught before the ref ever advances.
                integrity_failed = False
                if write_ok and not _post_mutation_integrity_ok(
                        root, ephemeral, candidate_tree_sha, touched_paths, record, extra_env):
                    write_ok = False
                    integrity_failed = True

                if not write_ok:
                    if not mutation_started:
                        # Nothing was ever actually written; there is
                        # nothing to roll back, and claiming an attempt
                        # would be untruthful.
                        return ApplyResult(
                            validation_ran=True, validation_passed=True,
                            concurrent_change=per_path_concurrent,
                            failure='concurrent_change_pre_mutation' if per_path_concurrent
                            else 'mutation_failed')
                    recovered = _attempt_recovery(ephemeral, root, record, extra_env)
                    # An integrity-gate failure means something outside
                    # the narrow touched-path bookkeeping `record` covers
                    # has drifted (that is exactly what this gate exists
                    # to catch) — `_attempt_recovery` has no way to see
                    # that, so "complete" can never be truthfully claimed
                    # here regardless of its own return value.
                    rollback_completed = recovered and not integrity_failed
                    return ApplyResult(
                        mutation_started=True, validation_ran=True, validation_passed=True,
                        rollback_attempted=True, rollback_completed=rollback_completed,
                        concurrent_change=per_path_concurrent or integrity_failed or not rollback_completed,
                        failure='post_mutation_failure')

                cas = controlled_git(
                    'update-ref', 'HEAD', new_commit, current, cwd=root, extra_env=extra_env)
                if cas.returncode != 0:
                    # Recovery may still restore every updater-written
                    # worktree/index path it can safely verify, but the
                    # ref itself is deliberately never overwritten back
                    # to C once another process has moved it — so the
                    # overall recovery boundary can never be reported
                    # complete here, regardless of how much of the
                    # touched-path state was restorable.
                    _attempt_recovery(ephemeral, root, record, extra_env)
                    return ApplyResult(
                        mutation_started=True, validation_ran=True, validation_passed=True,
                        rollback_attempted=True, rollback_completed=False,
                        concurrent_change=True, failure='ref_cas_failed')

                return ApplyResult(
                    mutation_started=True, validation_ran=True, validation_passed=True, commit=new_commit)
    except TargetMaterializationError as error:
        return ApplyResult(failure=error.reason)
