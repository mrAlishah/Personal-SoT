"""Canonical Safe Update target resolution; see system/update/update_contract.md."""
from __future__ import annotations

from dataclasses import dataclass
import os
import re
import subprocess
import tempfile

from system.connectors.github import GitHubSource
from system.connectors.source import Snapshot, SourceUnavailable

CANONICAL_REPOSITORY = 'mrAlishah/Personal-SoT'
CANONICAL_REF = 'main'
CANONICAL_URL = 'https://github.com/' + CANONICAL_REPOSITORY

_SHA_RE = re.compile(r'[0-9a-f]{40}')
_LS_REMOTE_RE = re.compile(r'([0-9a-f]{40})\trefs/heads/' + re.escape(CANONICAL_REF) + r'$')


_ALLOWED_EXTRA_ENV = frozenset({'GIT_ALTERNATE_OBJECT_DIRECTORIES', 'GIT_NO_REPLACE_OBJECTS'})


@dataclass(frozen=True)
class TargetSnapshot:
    commit: str
    ref: str
    resolved_via: str


def controlled_git(*args, cwd=None, extra_env=None, runner=subprocess.run, input=None, text=True):
    """Run one Git invocation isolated from ambient Git authority.

    Builds the child environment explicitly rather than passing the parent
    process environment through, so system/global config and injected
    GIT_CONFIG_*/GIT_DIR/GIT_WORK_TREE state cannot redirect it, and writes
    its own minimal global config (only `http.followRedirects = false`, so a
    single HTTP redirect on the initial request cannot silently substitute a
    different repository as the effective transport target — Git's own
    default, `initial`, would otherwise follow it). When `cwd` is omitted,
    the call also runs inside a freshly created, empty, non-repository
    directory with an explicit `GIT_CEILING_DIRECTORIES` boundary, so Git's
    upward repository discovery can neither find repository-local config
    there nor walk into an ancestor repository the controlled directory
    happens to be created under. Loop 3's apply step passes an explicit
    `cwd` (the real checkout) and relies only on the environment control,
    since discovering that real repository there is intended.

    Every invocation also runs with `-c core.hooksPath=<empty-dir>` (a
    directory this call creates and never populates) and `-c
    core.fsmonitor=false`, so no repository, user, or global hook
    (including `reference-transaction`, which ordinary ref updates invoke)
    or fsmonitor command can execute regardless of what the real checkout
    has configured; verified empirically that a real hook script and a
    real fsmonitor script do not fire under this override, including for
    `update-index`/`write-tree`/`ls-files --stage`, not only `status`. This
    applies uniformly to every caller, not only Loop 3's apply step, since
    read-only Loop 1/2 calls have no reason to risk it either — an
    individual call site may still pass its own `-c core.fsmonitor=false`
    (harmless duplication; Git accepts repeated `-c` for the same key).

    `extra_env` may add only `GIT_ALTERNATE_OBJECT_DIRECTORIES` and
    `GIT_NO_REPLACE_OBJECTS` (Loop 2's local-only classification needs);
    any other key, including any of the authority-bearing variables this
    function already controls, raises before any process environment is
    built. This is a fixed, closed allowlist, not a general environment-
    extension mechanism.

    `input`/`text` pass through to the underlying `subprocess.run` call
    unchanged (Loop 3's object-transfer step feeds NUL-separated tree
    entries and binary pack data through this same primitive rather than a
    second wrapper); omitting them preserves every existing caller's
    behavior exactly.
    """
    if extra_env:
        disallowed = set(extra_env) - _ALLOWED_EXTRA_ENV
        if disallowed:
            raise ValueError(f'extra_env may not set {sorted(disallowed)}')
    with tempfile.TemporaryDirectory(prefix='personal_sot_update_') as controlled_home:
        global_config = os.path.join(controlled_home, 'controlled_gitconfig')
        with open(global_config, 'w', encoding='utf-8') as handle:
            handle.write('[http]\n\tfollowRedirects = false\n')
        empty_hooks = os.path.join(controlled_home, 'empty_hooks')
        os.mkdir(empty_hooks)
        env = {
            'PATH': os.environ.get('PATH', '/usr/bin:/bin'),
            'HOME': controlled_home,
            'XDG_CONFIG_HOME': controlled_home,
            'GIT_CONFIG_NOSYSTEM': '1',
            'GIT_CONFIG_GLOBAL': global_config,
        }
        if cwd is None:
            cwd = controlled_home
            env['GIT_CEILING_DIRECTORIES'] = os.path.dirname(os.path.realpath(controlled_home))
        if extra_env:
            env.update(extra_env)
        full_args = ('git', '-c', 'core.hooksPath=' + empty_hooks,
                     '-c', 'core.fsmonitor=false') + args
        return runner(full_args, cwd=cwd, env=env,
                       stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                       input=input, text=text, timeout=30, check=False)


def resolve(resolver=None) -> TargetSnapshot:
    """Resolve mrAlishah/Personal-SoT:main to an immutable commit T.

    No repository/ref/commit parameter exists: callers cannot override
    update authority through this API. `resolver`, when supplied, is a
    zero-argument callable returning the same Snapshot shape
    GitHubSource.resolve() returns; it is used exactly as given, with no
    further fallback, so injecting it for a test never triggers the
    production Git fallback below. With no resolver, the default chain
    tries GitHubSource against the canonical repository and, only when that
    transport itself is unavailable, resolves the same exact target
    directly with Git instead.
    """
    if resolver is not None:
        return _validated(resolver(), resolved_via='resolver')
    try:
        source = GitHubSource(CANONICAL_REPOSITORY, ref=CANONICAL_REF)
        return _validated(source.resolve(), resolved_via='github')
    except SourceUnavailable as error:
        if error.reason != 'capability_unavailable':
            raise
        return _resolve_via_git()


def _validated(snapshot, *, resolved_via: str) -> TargetSnapshot:
    if (not isinstance(snapshot, Snapshot) or snapshot.source != CANONICAL_REPOSITORY
            or snapshot.selector != CANONICAL_REF or not isinstance(snapshot.revision, str)
            or not _SHA_RE.fullmatch(snapshot.revision)):
        raise SourceUnavailable(reason='source_unresolved')
    return TargetSnapshot(snapshot.revision, CANONICAL_REF, resolved_via)


def _resolve_via_git() -> TargetSnapshot:
    try:
        result = controlled_git('ls-remote', CANONICAL_URL, CANONICAL_REF)
    except FileNotFoundError:
        raise SourceUnavailable(reason='capability_unavailable') from None
    except (OSError, subprocess.SubprocessError):
        raise SourceUnavailable(reason='source_unavailable') from None
    if result.returncode != 0:
        raise SourceUnavailable(reason='source_unavailable')
    match = _LS_REMOTE_RE.match((result.stdout or '').strip())
    if match is None:
        raise SourceUnavailable(reason='source_unresolved')
    return TargetSnapshot(match.group(1), CANONICAL_REF, 'git')
