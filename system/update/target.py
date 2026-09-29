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


@dataclass(frozen=True)
class TargetSnapshot:
    commit: str
    ref: str
    resolved_via: str


def controlled_git(*args, cwd=None, runner=subprocess.run):
    """Run one Git invocation isolated from ambient Git authority.

    Builds the child environment explicitly rather than passing the parent
    process environment through, so system/global config and injected
    GIT_CONFIG_*/GIT_DIR/GIT_WORK_TREE state cannot redirect it. When `cwd`
    is omitted, the call also runs inside a freshly created, empty,
    non-repository directory, so Git's upward repository discovery finds no
    repository-local config either. Loop 3's apply step passes an explicit
    `cwd` (the real checkout) and relies only on the environment control.
    """
    with tempfile.TemporaryDirectory(prefix='personal_sot_update_') as controlled_home:
        env = {
            'PATH': os.environ.get('PATH', '/usr/bin:/bin'),
            'HOME': controlled_home,
            'XDG_CONFIG_HOME': controlled_home,
            'GIT_CONFIG_NOSYSTEM': '1',
            'GIT_CONFIG_GLOBAL': os.devnull,
        }
        return runner(('git',) + args, cwd=cwd or controlled_home, env=env,
                       stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                       text=True, timeout=30, check=False)


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
        return _validated(GitHubSource(CANONICAL_REPOSITORY).resolve(), resolved_via='github')
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
