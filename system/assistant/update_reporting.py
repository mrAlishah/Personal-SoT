"""Loop 5 beginner/Advanced presentation glue for Safe Update.

Routes to the existing canonical owners (`system.update.git_update`,
`system.update.side_by_side`) for every classification, apply/migrate,
recovery, and validator decision; this module never reimplements any of
that. It aggregates their already-produced Plan/Preview/Result objects
into a truthful beginner report (area/count only, never a Personal path
or filename) and an Advanced detail view (Personal
`workspace/context/*.md` paths named only when `access.permitted`
returns True against the CANONICAL registry at the selected
installation — never caller-supplied registry text; product/
implementation detail such as commit SHAs may appear freely).

See `system/assistant/update_workflow.md` for the user-facing contract
this module implements.
"""
from __future__ import annotations

from dataclasses import dataclass
import os
from pathlib import Path, PurePosixPath
import stat

from system.context.access import permitted
from system.update import git_update, side_by_side
from system.update.target import controlled_git
from system.validation.validate_v1 import context_registry_entries

_KNOWN_AREAS = frozenset({'workspace', 'system', 'guides'})
_HEADER_READ_LIMIT = 4096
_REGISTRY_RELATIVE = Path('system', 'routing', 'context_registry.md')
# Stable, repository-owned markers a real Personal-SoT installation has
# regardless of whether it is a Git clone or a downloaded archive — the
# smallest evidence that distinguishes one from an arbitrary directory
# (including an arbitrary, unrelated Git repository), never a guess
# from user wording. Each must be a genuine REGULAR file at that exact
# path — a symlink standing in for one proves nothing about the
# installation actually being there.
_ARCHIVE_MARKERS = (
    Path('workspace', 'adapters', 'runtime_entrypoint.md'),
    Path('system', 'validation', 'validate_v1.py'),
)


@dataclass(frozen=True)
class HostCapability:
    """Trusted host/runtime input — supplied by the caller's own
    deployment/adapter boundary, NEVER parsed from user/chat/prompt
    text. `can_read` is source/current-installation read access,
    `can_write` is canonical write/apply capability, and
    `can_run_local_commands` is the ability to execute local Git/
    validator subprocesses at all — this workflow's own install-type
    detection, classification, and preview are themselves local-command
    operations, so without this capability nothing here can even be
    probed, let alone applied.
    """
    can_read: bool = False
    can_write: bool = False
    can_run_local_commands: bool = False


@dataclass(frozen=True)
class DeploymentBinding:
    """Trusted adapter/deployment state for restricted-scope Personal
    disclosure — supplied ONLY by the host boundary, never derived from
    user/chat/prompt text. Defaults to the fail-closed state.
    """
    personal_owner: bool = False
    private_instance: bool = False


@dataclass(frozen=True)
class BeginnerReport:
    """Safe for any audience: a plain-language headline plus optional
    area/count detail lines. Never a Personal path, filename, content
    fragment, or content hash.
    """
    headline: str
    details: tuple[str, ...] = ()


@dataclass(frozen=True)
class AdvancedReport:
    """Safe Advanced-tier detail: `lines` are product/implementation
    facts that were never Personal (a commit SHA, recovery flags, a
    ready/failure literal) and `personal_paths` are ONLY the
    `workspace/context/*.md` paths `access.permitted` actually
    authorized against the CANONICAL registry at the selected
    installation — never a raw frontmatter header, module body, or an
    unauthorized Personal path. Calling this function, or any
    `advanced=True`-style flag, authorizes nothing by itself.
    """
    lines: tuple[str, ...] = ()
    personal_paths: tuple[str, ...] = ()


@dataclass(frozen=True)
class WorkflowResult:
    """The one object `run_update_workflow` returns. `digest` is the
    FRESH preview digest for this call — pass it back as
    `confirm_digest` on a subsequent call to actually apply/migrate;
    passing a stale one is always refused. `confirmation_required` is
    true only when the FRESH preview is actionable and may be confirmed;
    `applied` means the update actually became the installed/ready result,
    never merely that
    `apply`/`migrate` was invoked. Carries no raw header, module body,
    or unauthorized Personal path — Advanced detail is built separately
    by `advanced_report`, only after a real `access.permitted` call.
    """
    install_type: str
    digest: str | None
    ready: bool
    applied: bool
    beginner: BeginnerReport
    failure: str | None = None
    confirmation_required: bool = False


# --- install-type routing -------------------------------------------------

def _pinned_dotgit_kind(pin: _PinnedReadRoot) -> str:
    """`'directory'`, `'regular'`, or `'none'` for `.git` directly
    under the PINNED root — root-anchored, `O_NOFOLLOW`, read entirely
    through the pinned fd, never a pathname open. `.git` has no
    intermediate components, so this opens it in one step from
    `pin.fd`; a symlink or special file there is `'none'`, never
    treated as evidence of anything.
    """
    try:
        fd = os.open('.git', os.O_RDONLY | os.O_NOFOLLOW, dir_fd=pin.fd)
    except OSError:
        return 'none'
    try:
        st = os.fstat(fd)
    except OSError:
        return 'none'
    finally:
        try:
            os.close(fd)
        except OSError:
            pass
    if stat.S_ISDIR(st.st_mode):
        return 'directory'
    if stat.S_ISREG(st.st_mode):
        return 'regular'
    return 'none'


def _pinned_git_evidence(pin: _PinnedReadRoot) -> bool:
    """Whether the PINNED root carries valid `.git` ROUTING evidence —
    read entirely through the pinned, component-safe filesystem
    boundary, never a Git subprocess against a pathname. A subprocess
    necessarily runs against whatever physical directory the pathname
    names AT THAT MOMENT, which an ABA swap (temporarily replacing the
    selected pathname with a different real directory, running the
    probe, then restoring the original before any pathname-based
    identity recheck) can redirect to a different physical directory
    entirely while every before/after pathname check still shows the
    original restored — no amount of additional pathname checking
    closes that, since the swap-and-restore happens strictly between
    them. Reading `.git` through the already-pinned fd instead means
    there is no pathname step for an ABA swap to intercept at all.

    This is ROUTING evidence ONLY — a real directory (normal clone), or
    a linked worktree's `.git` regular file whose bounded-read content
    has the shape `gitdir: <non-empty value>`. Actual Git validity,
    current commit, merge base, dirty/clean classification, candidate
    safety, and apply all remain entirely owned by
    `system.update.git_update`, which independently re-verifies
    everything it needs against the real checkout; this function
    decides nothing beyond "does this look like a Git-managed
    directory, for routing purposes".
    """
    kind = _pinned_dotgit_kind(pin)
    if kind == 'directory':
        return True
    if kind != 'regular':
        return False
    data = _safe_read_pinned(pin, '.git', limit=4096)
    if data is None:
        return False
    try:
        text = data.decode('utf-8')
    except UnicodeDecodeError:
        return False
    lines = text.splitlines()
    first_line = lines[0] if lines else ''
    if not first_line.startswith('gitdir:'):
        return False
    return bool(first_line[len('gitdir:'):].strip())


def _is_git_installation(pin: _PinnedReadRoot) -> bool:
    """Whether the PINNED selected root is Git-managed, for routing
    purposes only — see `_pinned_git_evidence`, which this delegates
    to entirely. No Git subprocess runs against any pathname here.
    """
    return _pinned_git_evidence(pin)


def _root_anchored_parts(relative: str) -> list[str] | None:
    """The path components of `relative` for a root-anchored,
    one-component-at-a-time `openat()` walk, or `None` if it is not a
    simple, safe, relative path (empty, absolute, containing `.`/`..`,
    or any component itself containing a `/`).

    An absolute path is rejected by `is_absolute()` explicitly, not
    merely by scanning `.parts` for `.`/`..`: `PurePosixPath('/etc/
    passwd').parts` is `('/', 'etc', 'passwd')`, whose first element
    is neither `.` nor `..` nor empty, so it would otherwise slip
    through this check — and a leading `/` component reaching
    `os.open(..., dir_fd=...)` is interpreted as an ABSOLUTE path by
    POSIX `openat()`, which silently IGNORES `dir_fd` entirely and
    escapes containment outright. This primitive enforces its own
    security contract rather than relying on every caller to have
    already normalized/rejected an absolute path first.
    """
    posix = PurePosixPath(relative)
    if posix.is_absolute():
        return None
    parts = posix.parts
    if not parts:
        return None
    for part in parts:
        if part in ('.', '..') or not part or '/' in part:
            return None
    return list(parts)


_NOFOLLOW_SUPPORTED = (
    getattr(os, 'O_NOFOLLOW', None) is not None
    and getattr(os, 'O_DIRECTORY', None) is not None
    and os.open in os.supports_dir_fd
)


def _open_root_fd(root):
    """Open the selected root itself, root-anchored
    (`O_DIRECTORY | O_NOFOLLOW`) — the root pathname must not itself
    be a symlink; this authority boundary never follows one to "help"
    the caller, and never falls back to `Path.resolve()`.
    """
    if not _NOFOLLOW_SUPPORTED:
        return None
    try:
        return os.open(str(root), os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
    except OSError:
        return None

@dataclass
class _PinnedReadRoot:
    """A read-only root authority pin for ONE logical operation
    (installation proof, or one Advanced authorization pass): opened
    ONCE, identified by `(st_dev, st_ino)`, and reused for every
    descendant root-relative read. Re-deriving the root from its
    pathname separately for each read is what let an authority
    decision (two installation markers; a canonical registry read
    plus a module frontmatter read) silently combine evidence from
    two different physical directories if the pathname was replaced
    in between — pinning once and reusing the same fd closes that,
    the same way Loop 4's root pinning closes the equivalent gap for
    migration reads/writes.
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


def _pin_read_root(root) -> _PinnedReadRoot | None:
    """Pin `root` once, root-anchored (`O_DIRECTORY | O_NOFOLLOW` —
    the root pathname must not itself be a symlink), for the duration
    of one authority transaction.
    """
    fd = _open_root_fd(root)
    if fd is None:
        return None
    try:
        st = os.fstat(fd)
    except OSError:
        try:
            os.close(fd)
        except OSError:
            pass
        return None
    return _PinnedReadRoot(fd=fd, path=Path(root), dev=st.st_dev, ino=st.st_ino)


def _pinned_root_still_current(pin: _PinnedReadRoot) -> bool:
    """Whether `pin.path` still names the SAME physical directory the
    pinned fd was opened from — required before/after any operation
    that still needs a pathname (a Git subprocess probe) rather than
    the fd itself; a pathname that disappeared, became a symlink,
    points to a different directory, or whose device/inode changed
    all fail this closed.
    """
    try:
        st = os.stat(pin.path, follow_symlinks=False)
    except OSError:
        return False
    return stat.S_ISDIR(st.st_mode) and (st.st_dev, st.st_ino) == (pin.dev, pin.ino)


def _open_pinned_relative(pin: _PinnedReadRoot, relative: str):
    """Open `relative` under the PINNED root's fd, root-anchored
    through EVERY intermediate path component (`O_DIRECTORY |
    O_NOFOLLOW`) and the final component (`O_NOFOLLOW`) — never by
    re-deriving the root from its pathname. Returns the final open fd
    (owned by the caller, who must close it) or `None` if any
    component is missing, a symlink, or not a real directory where
    one is required — never a plain pathname open and never
    `Path.resolve()`, either of which an intermediate symlink (e.g.
    `workspace` or `system` itself swapped for one) could follow right
    past.

    This is the ONE path-walk this module performs for an authority
    boundary; installation-marker proof, the canonical registry read,
    and Personal module frontmatter reads all build on it, from the
    SAME pin for one logical operation, rather than repeating it or
    re-opening the root for each read.
    """
    parts = _root_anchored_parts(relative)
    if not parts:
        return None
    intermediate = []
    try:
        parent = pin.fd
        for part in parts[:-1]:
            try:
                fd = os.open(part, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=parent)
            except OSError:
                return None
            intermediate.append(fd)
            parent = fd
        try:
            return os.open(parts[-1], os.O_RDONLY | os.O_NOFOLLOW, dir_fd=parent)
        except OSError:
            return None
    finally:
        for fd in intermediate:
            try:
                os.close(fd)
            except OSError:
                pass


def _safe_is_regular_file(pin: _PinnedReadRoot, relative: str) -> bool:
    """Whether `relative` under the PINNED root is a genuine regular
    file, root-anchored through every path component — used for
    installation marker proof, which only needs to confirm the file
    exists as a real regular file, never its content.
    """
    fd = _open_pinned_relative(pin, relative)
    if fd is None:
        return False
    try:
        return stat.S_ISREG(os.fstat(fd).st_mode)
    except OSError:
        return False
    finally:
        try:
            os.close(fd)
        except OSError:
            pass


def _safe_read_pinned(pin: _PinnedReadRoot, relative: str, limit: int | None = None) -> bytes | None:
    """Read the bytes of `relative` under the PINNED root, root-
    anchored through every path component — the shared primitive
    behind the canonical registry read and Personal module frontmatter
    reads alike, both drawing from the SAME pin for one authority
    transaction. `None` for anything other than a genuine regular file
    reachable without following any symlink, intermediate or final.
    `limit`, when given, reads at most that many bytes (used for a
    bounded frontmatter read, so a large module body is never pulled
    fully into memory just to look for its closing `---`).
    """
    fd = _open_pinned_relative(pin, relative)
    if fd is None:
        return None
    try:
        if not stat.S_ISREG(os.fstat(fd).st_mode):
            return None
        if limit is not None:
            return os.read(fd, limit)
        chunks = []
        while True:
            chunk = os.read(fd, 65536)
            if not chunk:
                break
            chunks.append(chunk)
        return b''.join(chunks)
    except OSError:
        return None
    finally:
        try:
            os.close(fd)
        except OSError:
            pass


def _is_personal_sot_archive(pin: _PinnedReadRoot) -> bool:
    """Whether the PINNED root carries the smallest stable,
    repository-owned evidence of actually being a Personal-SoT
    installation — Git or not. Each marker must be a genuine regular
    file at that EXACT path, root-anchored through EVERY path
    component (not merely the final one — an intermediate component
    such as `workspace` or `system` itself swapped for a symlink would
    otherwise still let the final lookup resolve to an outside regular
    file): a symlink standing in for a marker, anywhere along its
    path, proves nothing about the real installation being there.
    Both markers are checked through the SAME pin, so they can never
    be satisfied by two different physical directories swapped in
    between the two checks — an arbitrary directory or an unrelated
    Git repository has no reason to carry either marker at all.
    """
    for marker in _ARCHIVE_MARKERS:
        if not _safe_is_regular_file(pin, marker.as_posix()):
            return False
    return True


def detect_install_type(root, capability: HostCapability) -> str:
    """`'git'`, `'zip'`, or `'unknown'` — from actual host/repository
    evidence only, never from how the user describes their install.
    One installation-evidence rule covers both routes: the selected
    root must carry Personal-SoT's own stable markers before either
    route is even considered, so neither an arbitrary directory nor an
    arbitrary, unrelated top-level Git repository can route as this
    installation merely by existing or by being *some* Git repo. Fails
    closed to `'unknown'` without proven read AND local-command
    capability (every check here is itself a local-command operation).

    The selected root is pinned ONCE for this entire proof. POSIX hosts
    use the openat/O_NOFOLLOW fd boundary below. Native Windows, where
    Python does not expose those primitives, routes through
    `windows_install_detection`, which uses Win32 handles that reject
    reparse points and pin accepted components against rename/delete.
    In both cases the markers and Git-vs-no-Git evidence come from one
    bounded physical installation, and root drift fails closed.
    """
    if capability.can_read is not True or capability.can_run_local_commands is not True:
        return 'unknown'

    if not _NOFOLLOW_SUPPORTED:
        if os.name == 'nt':
            from system.assistant.windows_install_detection import detect as detect_windows
            return detect_windows(root, _ARCHIVE_MARKERS)
        return 'unknown'

    pin = _pin_read_root(root)
    if pin is None:
        return 'unknown'
    try:
        if not _is_personal_sot_archive(pin):
            return 'unknown'
        is_git = _is_git_installation(pin)
        if not _pinned_root_still_current(pin):
            return 'unknown'
        return 'git' if is_git else 'zip'
    finally:
        pin.close()


# --- display-only area/count aggregation ----------------------------------
# A trivial, independent grouping for COUNTING an already-classified
# path list — never a classification decision of its own. The actual
# classification happened in git_update.py/side_by_side.py; this only
# turns their output into a safe, closed-vocabulary count.

def _area_of(path: str) -> str:
    top = path.split('/', 1)[0] if '/' in path else 'root'
    return top if top in _KNOWN_AREAS else 'other'


def _area_counts(paths) -> dict[str, int]:
    counts: dict[str, int] = {}
    for path in paths:
        area = _area_of(path)
        counts[area] = counts.get(area, 0) + 1
    return counts


def _count_lines(counts: dict[str, int], suffix: str) -> tuple[str, ...]:
    return tuple(f'{area}: {count} item(s) {suffix}' for area, count in sorted(counts.items()))


def _with_no_write_notice(report: BeginnerReport) -> BeginnerReport:
    """The SAME real, informative beginner report, with the two
    required no-write literals appended — never a generic placeholder
    substituted in their place. A client without write capability
    learns both what the real preview found AND that it cannot write
    or validate, on the very first call, not only after it "confirms".
    """
    return BeginnerReport(report.headline, report.details + ('nothing was written', 'validation was not run here'))


# --- Git beginner report ---------------------------------------------------

def _git_apply_succeeded(result: git_update.ApplyResult) -> bool:
    """The update actually became the installed result — never
    inferred from validator flags alone. A controlled failure can
    legitimately have `validation_ran=True, validation_passed=True,
    concurrent_change=False` (e.g. `object_transfer_failed`, or a
    completely rolled-back `post_mutation_failure`) without the update
    having succeeded at all; only a real resulting commit, with no
    failure literal recorded, counts as success.
    """
    return (result.failure is None and result.commit is not None
            and result.validation_ran and result.validation_passed
            and not result.concurrent_change)


def git_beginner_report(plan: git_update.Plan, summary: dict,
                         result: git_update.ApplyResult | None) -> BeginnerReport:
    """Build a beginner report from Loop 1–3's own `Plan`/`summary`
    (already the area/count-safe shape `git_update.preview` produces)
    and, once apply has actually run, its `ApplyResult`. Never re-
    derives classification state itself.
    """
    if plan.blocked == 'dirty_or_untracked':
        details = (
            'Save your local changes with a local Git commit before updating.',
            'Do not push those local commits to the public mrAlishah/Personal-SoT repository.',
            'The updater does not commit, stash, reset, or clean your changes for you.',
        ) + _count_lines(dict(plan.blocked_by_area), 'affected')
        return BeginnerReport('Nothing was changed. Save your local changes in local Git history first.', details)
    if plan.blocked is not None:
        return BeginnerReport('Nothing was changed. The update could not be checked safely.')
    if plan.conflict:
        return BeginnerReport('Nothing was changed. One or more local and update changes need a decision.')
    if plan.no_op:
        return BeginnerReport("You're already current.")

    if result is None:
        details = _count_lines(dict(summary.get('hidden_by_area', {})), 'preserved')
        return BeginnerReport('Ready to preview this update.', details)

    if _git_apply_succeeded(result):
        return BeginnerReport('Update applied and validation passed.')

    if result.mutation_started:
        if result.rollback_completed:
            return BeginnerReport(
                'Update did not complete; the updater restored the verified prior state.')
        return BeginnerReport(
            'Update did not complete and some updater changes could not be safely restored '
            'because the installation changed concurrently.')

    if result.validation_ran and not result.validation_passed:
        return BeginnerReport('Update not applied: validation failed. The installation was not changed.')

    return BeginnerReport('Update not applied. The installation was not changed by the updater.')


# --- ZIP/side-by-side beginner report --------------------------------------

def zip_beginner_report(plan: side_by_side.SideBySidePlan,
                         result: side_by_side.MigrationResult | None) -> BeginnerReport:
    """Build a beginner report from Loop 4's own `SideBySidePlan`/
    `MigrationResult`. `SideBySidePlan` has no pre-built area/count
    summary (unlike `git_update.Preview`), so the display-only grouping
    above is applied here to its raw path tuples — never a new
    classification decision.

    Once `migrate` has actually been called, "Nothing was changed" is
    never said for a failure: Loop 4 does not promise to delete a
    partially built side-by-side destination on failure (only that the
    ORIGINAL installation is never touched), so a failed result after
    `migrate` ran always says the original is unchanged and the new
    copy specifically is not ready — regardless of how far migration
    got before failing.
    """
    if plan.blocked is not None:
        return BeginnerReport('Nothing was changed. The update could not be checked safely.')
    if plan.rejected_unsafe:
        return BeginnerReport(
            f'Nothing was changed. {len(plan.rejected_unsafe)} unsafe Personal item(s) require attention.')
    if plan.conflicts or plan.registry.conflicts:
        return BeginnerReport('Nothing was changed. One or more local and update changes need a decision.')

    if result is None:
        details = _count_lines(_area_counts(plan.kept), 'to preserve')
        return BeginnerReport('Ready to preview this update.', details)

    if result.ready:
        details = _count_lines(_area_counts(plan.kept), 'preserved')
        return BeginnerReport(
            'Updated side-by-side copy is ready. Your original folder was not changed.', details)

    if result.failure == 'personal_validation_failed':
        return BeginnerReport(
            'Your original folder was not changed. The new copy did not pass validation and is not ready.')
    return BeginnerReport(
        'Your original folder was not changed. The new copy did not finish and is not ready.')


def no_write_report() -> BeginnerReport:
    return BeginnerReport(
        'A preview is available, but this client cannot write or validate.',
        ('nothing was written', 'validation was not run here'))


def _no_local_command_report() -> BeginnerReport:
    """Case B: no preview could even be attempted, because the local
    command/read capability a preview needs was never available —
    never worded as if a preview exists, unlike case A
    (`_with_no_write_notice`, where one genuinely was built).
    """
    return BeginnerReport(
        'This client cannot run the local commands needed to check or preview an update here.',
        ('nothing was written', 'validation was not run here'))


def _stale_preview_report(report: BeginnerReport) -> BeginnerReport:
    """Render a stale confirmation as a fresh, actionable preview.

    The old digest is still refused. This only packages the newly computed
    beginner-safe report so a human/agent runner can request confirmation
    again without falling back to ad-hoc Git commands.
    """
    return BeginnerReport(
        'The available update changed; review the refreshed preview before confirming.',
        (report.headline,) + report.details,
    )


# --- Advanced authorization -------------------------------------------------

def _read_frontmatter_only(pin: _PinnedReadRoot, path: str) -> str:
    """ONLY the bounded `---`-delimited frontmatter block of `path`
    under the PINNED root, read through the root-anchored safe
    primitive (every path component, not merely the final one — an
    intermediate `workspace`/`context`/scope directory swapped for a
    symlink must fail this closed too) — never module body bytes,
    even if they would fit within `_HEADER_READ_LIMIT`: the text must
    open with `---` on its own line and a matching closing `---` must
    appear within that bound, or this returns `''`. `access.permitted`
    remains the sole policy owner; this only bounds what text
    physically reaches it.
    """
    raw = _safe_read_pinned(pin, path, limit=_HEADER_READ_LIMIT)
    if raw is None:
        return ''
    text = raw.decode('utf-8', errors='replace')
    lines = text.splitlines(keepends=True)
    if not lines or lines[0].strip() != '---':
        return ''
    for index in range(1, len(lines)):
        if lines[index].strip() == '---':
            return ''.join(lines[:index + 1])
    return ''


def _canonical_registry_text(pin: _PinnedReadRoot) -> str | None:
    """The CANONICAL registry text at `system/routing/
    context_registry.md` under the PINNED root, read host-side through
    the root-anchored safe primitive (every path component, not
    merely the final one — an intermediate `system`/`routing` swapped
    for a symlink must fail this closed too) — NEVER caller-supplied
    text, which could otherwise fabricate scope ownership for a path
    the installation's own registry never actually registers. `None`
    (fail closed, meaning "no scope can be proven" — never "empty
    registry") if the path is missing, unreadable, or any component
    along it, including the final one, is a symlink.
    """
    data = _safe_read_pinned(pin, _REGISTRY_RELATIVE.as_posix())
    if data is None:
        return None
    try:
        return data.decode('utf-8')
    except UnicodeDecodeError:
        return None


def _authorized_personal_paths(root, candidate_paths, *, host_read: bool,
                                deployment: DeploymentBinding) -> tuple[str, ...]:
    """The ONE internal host-side authorization pass, never exposed as
    a public raw-candidate transport: for each candidate, validate it
    is a safe relative `.md` path (rejecting absolute/`..`/non-`.md`
    paths BEFORE any file is opened), resolve whether it falls under a
    scope the CANONICAL registry at `root` actually names, read ONLY
    its frontmatter, call `access.permitted` directly, and keep the
    path only if that call returns `True`. The frontmatter is discarded
    immediately after the call — it never survives in any returned
    value.

    `root` is pinned ONCE for this entire pass: the canonical registry
    read and every candidate's frontmatter read all draw from that
    SAME physical directory, never re-derived from the pathname in
    between — otherwise an authorization decision could combine a
    registry from one physical directory with a module's frontmatter
    from a different one, swapped in between the two reads. The
    pinned root's identity is reverified after the registry read and
    again before returning; any drift returns no Personal paths at
    all, never a partially-combined result.
    """
    pin = _pin_read_root(root)
    if pin is None:
        return ()
    try:
        registry_text = _canonical_registry_text(pin)
        if registry_text is None:
            return ()
        if not _pinned_root_still_current(pin):
            return ()
        scopes = []
        for _scope, target in context_registry_entries(registry_text):
            canonical = side_by_side.normalize_relative(target.rstrip('/'))
            if canonical is not None:
                scopes.append(canonical)

        allowed = []
        for path in candidate_paths:
            normalized = side_by_side.normalize_relative(path)
            if normalized is None or not normalized.endswith('.md'):
                continue
            scope_path = next(
                (scope for scope in scopes
                 if normalized == scope or normalized.startswith(scope + '/')), None)
            if scope_path is None:
                continue
            header = _read_frontmatter_only(pin, normalized)
            if permitted(header, path=normalized, scope_path=scope_path, host_read=host_read,
                         required=True, personal_owner=deployment.personal_owner,
                         private_instance=deployment.private_instance):
                allowed.append(normalized)

        if not _pinned_root_still_current(pin):
            return ()
        return tuple(allowed)
    finally:
        pin.close()


def _advanced_result_lines(install_type: str, result) -> tuple[str, ...]:
    """Product/implementation facts only — never Personal, never a
    raw Plan object.
    """
    if install_type == 'git' and isinstance(result, git_update.ApplyResult):
        if _git_apply_succeeded(result):
            return (f'commit: {result.commit}',)
        return (f'failure: {result.failure or "none"}',
                f'rollback_attempted: {result.rollback_attempted}',
                f'rollback_completed: {result.rollback_completed}')
    if install_type == 'zip' and isinstance(result, side_by_side.MigrationResult):
        return (f'ready: {result.ready}', f'failure: {result.failure or "none"}')
    return ()


def advanced_report(install_type: str, result=None, *, root=None, candidate_paths=(),
                     host_read: bool = False,
                     deployment: DeploymentBinding = DeploymentBinding()) -> AdvancedReport:
    """The one Advanced-tier view: safe product/result facts plus ONLY
    the `candidate_paths` that `access.permitted` actually authorizes,
    checked against the CANONICAL registry read directly from `root` —
    never a caller-supplied registry string, which would otherwise let
    a caller fabricate scope ownership for an unregistered path. Calling
    this (or an `advanced=True`-style flag anywhere upstream) authorizes
    nothing by itself — every Personal path still passes through a real
    `permitted()` call, and no raw header, module body, or unauthorized
    path ever reaches the returned object.
    """
    lines = _advanced_result_lines(install_type, result)
    personal_paths: tuple[str, ...] = ()
    if root is not None and candidate_paths:
        personal_paths = _authorized_personal_paths(
            root, candidate_paths, host_read=host_read, deployment=deployment)
    return AdvancedReport(lines=lines, personal_paths=personal_paths)


# --- workflow orchestration -------------------------------------------------

def _git_workflow(root, capability: HostCapability, confirm_digest: str | None) -> WorkflowResult:
    plan = git_update.classify(root)
    preview = git_update.preview(plan)
    fresh_digest = preview.digest
    confirmed = confirm_digest is not None and confirm_digest == fresh_digest

    if not capability.can_write:
        # Preview genuinely was built (local-command capability is
        # already guaranteed by the caller) — the real, informative
        # report is shown, with the no-write notice attached, on the
        # very first call, not only once the client "confirms".
        base_report = git_beginner_report(plan, preview.summary, None)
        return WorkflowResult('git', fresh_digest, False, False, _with_no_write_notice(base_report))

    # A blocked/conflicting/no-op fresh state is authoritative regardless
    # of any caller-held digest. In particular, "already current" needs no
    # confirmation and a real conflict must never become actionable.
    if plan.blocked is not None or plan.conflict or plan.no_op:
        return WorkflowResult('git', fresh_digest, plan.no_op, False,
                               git_beginner_report(plan, preview.summary, None))

    if confirm_digest is None:
        return WorkflowResult(
            'git', fresh_digest, False, False,
            git_beginner_report(plan, preview.summary, None),
            confirmation_required=True)

    if not confirmed:
        return WorkflowResult(
            'git', fresh_digest, False, False,
            _stale_preview_report(git_beginner_report(plan, preview.summary, None)),
            failure='stale_state', confirmation_required=True)

    result = git_update.apply(root, plan, fresh_digest)
    succeeded = _git_apply_succeeded(result)
    return WorkflowResult('git', fresh_digest, succeeded, succeeded,
                           git_beginner_report(plan, preview.summary, result), failure=result.failure)


def _zip_workflow(root, destination, capability: HostCapability, confirm_digest: str | None,
                   exclude: frozenset) -> WorkflowResult:
    if destination is None:
        return WorkflowResult(
            'zip', None, False, False,
            BeginnerReport('A new destination folder is needed to update this installation.'),
            failure='destination_required')

    sbs_preview = side_by_side.preview(root, destination, exclude=exclude)
    plan = sbs_preview.plan
    fresh_digest = sbs_preview.digest
    confirmed = confirm_digest is not None and confirm_digest == fresh_digest

    if not capability.can_write:
        base_report = zip_beginner_report(plan, None)
        return WorkflowResult('zip', fresh_digest, False, False, _with_no_write_notice(base_report))

    if plan.blocked is not None or plan.conflicts or plan.registry.conflicts or plan.rejected_unsafe:
        return WorkflowResult('zip', fresh_digest, False, False, zip_beginner_report(plan, None))

    if confirm_digest is None:
        return WorkflowResult(
            'zip', fresh_digest, False, False, zip_beginner_report(plan, None),
            confirmation_required=True)

    if not confirmed:
        return WorkflowResult(
            'zip', fresh_digest, False, False,
            _stale_preview_report(zip_beginner_report(plan, None)),
            failure='stale_state', confirmation_required=True)

    result = side_by_side.migrate(root, destination, plan, fresh_digest, exclude=exclude)
    return WorkflowResult('zip', fresh_digest, result.ready, result.ready,
                           zip_beginner_report(plan, result), failure=result.failure)


def run_update_workflow(root, destination=None, *, capability: HostCapability,
                         confirm_digest: str | None = None,
                         exclude: frozenset = frozenset()) -> WorkflowResult:
    """The one Loop 5 entry point: Explain → Recommend → Preview →
    Apply. Routes ONLY to the existing canonical owners
    (`git_update`/`side_by_side`) for every classification, apply/
    migrate, and validation decision — this function makes no
    classification or authorization decision of its own.

    Every call recomputes a FRESH preview/digest from current state
    (never trusts a caller-held plan object); `confirm_digest` must
    match THAT fresh digest for apply/migrate to even be considered —
    a stale or absent `confirm_digest` always stays preview-only, and a
    client lacking write capability can never cause apply/migrate to
    run no matter what it passes as `confirm_digest`, and is told so
    plainly on its very first call, alongside whatever real preview
    information was actually built.

    Without proven local-command capability, NOTHING in this module
    runs at all — install-type detection, classification, and preview
    are themselves local Git/validator subprocess operations, so a
    client that cannot run those gets an honest no-write report
    immediately, never a preview built on commands that could not
    actually execute.
    """
    if capability.can_run_local_commands is not True:
        return WorkflowResult('unknown', None, False, False, _no_local_command_report(),
                               failure='no_local_command_capability')

    install_type = detect_install_type(root, capability)
    if install_type == 'unknown':
        return WorkflowResult(
            'unknown', None, False, False,
            BeginnerReport('This installation could not be checked safely.'),
            failure='unknown_install_type')
    if install_type == 'git':
        return _git_workflow(root, capability, confirm_digest)
    return _zip_workflow(root, destination, capability, confirm_digest, exclude)
