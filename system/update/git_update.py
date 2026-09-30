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
from pathlib import Path
import re
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


def _attribute_safety_blocked(root) -> bool:
    """True when accurate dirty-state inspection would require executing a
    configured clean/smudge/process/textconv helper.

    Uses Git's own attribute-resolution plumbing (`git check-attr`), not a
    hand-written .gitattributes parser, so nested .gitattributes files and
    .git/info/attributes are resolved exactly as an actual `git status`
    invocation under the same isolated environment would resolve them.
    """
    configured = set()
    for pattern in _ATTRIBUTE_SCAN_KEYS:
        config = controlled_git('config', '--get-regexp', pattern, cwd=root)
        if config.returncode not in (0, 1):
            return True
        for line in (config.stdout or '').splitlines():
            # Match only the key (everything before the first space); the
            # value may itself contain text that looks like a dot-suffix,
            # which must never be mistaken for part of the driver name.
            key = line.split(' ', 1)[0]
            match = _DRIVER_KEY_RE.match(key)
            if match:
                configured.add(match.group(1))
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
