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
from pathlib import Path
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
    passing a stale one is always refused. `applied` means the update
    actually became the installed/ready result, never merely that
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


# --- install-type routing -------------------------------------------------

def _is_git_installation(root) -> bool:
    """Whether `root` itself — not merely some directory inside a
    repository — is the top level of a real Git clone/worktree.
    `git rev-parse --show-toplevel` returns the WORKING TREE root
    (correct for a linked worktree too, where `.git` is a file, not a
    directory: it resolves to the worktree's own root, never the main
    repository's), and that must be the exact same physical directory
    as `root` — otherwise an arbitrary subdirectory nested inside some
    unrelated parent repository would be misidentified as the selected
    installation, even though Git itself would resolve it to that
    parent.
    """
    result = controlled_git('rev-parse', '--show-toplevel', cwd=str(root))
    if result.returncode != 0:
        return False
    toplevel = (result.stdout or '').strip()
    if not toplevel:
        return False
    try:
        return Path(toplevel).resolve() == Path(root).resolve()
    except OSError:
        return False


def _is_personal_sot_archive(root) -> bool:
    """Whether `root` carries the smallest stable, repository-owned
    evidence of actually being a Personal-SoT installation — Git or
    not. Each marker must be a genuine regular file at that EXACT path
    (`lstat`, never a followed symlink): a symlink standing in for a
    marker proves nothing about the real installation being there, and
    an arbitrary directory or an unrelated Git repository has no reason
    to carry either marker at all.
    """
    root = Path(root)
    for marker in _ARCHIVE_MARKERS:
        try:
            st = (root / marker).lstat()
        except OSError:
            return False
        if not stat.S_ISREG(st.st_mode):
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
    """
    if capability.can_read is not True or capability.can_run_local_commands is not True:
        return 'unknown'
    if not _is_personal_sot_archive(root):
        return 'unknown'
    if _is_git_installation(root):
        return 'git'
    return 'zip'


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


# --- Advanced authorization -------------------------------------------------

def _read_frontmatter_only(root, path: str) -> str:
    """ONLY the bounded `---`-delimited frontmatter block of `path`
    under `root` — never module body bytes, even if they would fit
    within `_HEADER_READ_LIMIT`: the text must open with `---` on its
    own line and a matching closing `---` must appear within that
    bound, or this returns `''`. The final path component is refused
    if it is itself a symlink, so an obvious final-component symlink
    cannot redirect this read outside the selected root.
    `access.permitted` remains the sole policy owner; this only bounds
    what text physically reaches it.
    """
    full = Path(root, path)
    try:
        if full.is_symlink():
            return ''
        with open(full, 'rb') as handle:
            raw = handle.read(_HEADER_READ_LIMIT)
    except OSError:
        return ''
    text = raw.decode('utf-8', errors='replace')
    lines = text.splitlines(keepends=True)
    if not lines or lines[0].strip() != '---':
        return ''
    for index in range(1, len(lines)):
        if lines[index].strip() == '---':
            return ''.join(lines[:index + 1])
    return ''


def _canonical_registry_text(root) -> str | None:
    """The CANONICAL registry text at `root/system/routing/
    context_registry.md`, read host-side — NEVER caller-supplied text,
    which could otherwise fabricate scope ownership for a path the
    installation's own registry never actually registers. `None`
    (fail closed, meaning "no scope can be proven" — never "empty
    registry") if the path is missing, unreadable, or its final
    component is a symlink.
    """
    full = Path(root, _REGISTRY_RELATIVE)
    try:
        if full.is_symlink() or not full.is_file():
            return None
        return full.read_text(encoding='utf-8')
    except OSError:
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
    """
    registry_text = _canonical_registry_text(root)
    if registry_text is None:
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
            (scope for scope in scopes if normalized == scope or normalized.startswith(scope + '/')), None)
        if scope_path is None:
            continue
        header = _read_frontmatter_only(root, normalized)
        if permitted(header, path=normalized, scope_path=scope_path, host_read=host_read,
                     required=True, personal_owner=deployment.personal_owner,
                     private_instance=deployment.private_instance):
            allowed.append(normalized)
    return tuple(allowed)


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

    if confirm_digest is None:
        return WorkflowResult('git', fresh_digest, False, False,
                               git_beginner_report(plan, preview.summary, None))

    if not confirmed:
        return WorkflowResult(
            'git', fresh_digest, False, False,
            BeginnerReport('The installation changed since your last preview. '
                            'Please review a new preview before confirming.'),
            failure='stale_state')

    if plan.blocked is not None or plan.conflict or plan.no_op:
        return WorkflowResult('git', fresh_digest, plan.no_op, False,
                               git_beginner_report(plan, preview.summary, None))

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

    if confirm_digest is None:
        return WorkflowResult('zip', fresh_digest, False, False, zip_beginner_report(plan, None))

    if not confirmed:
        return WorkflowResult(
            'zip', fresh_digest, False, False,
            BeginnerReport('The installation changed since your last preview. '
                            'Please review a new preview before confirming.'),
            failure='stale_state')

    if plan.blocked is not None or plan.conflicts or plan.registry.conflicts or plan.rejected_unsafe:
        return WorkflowResult('zip', fresh_digest, False, False, zip_beginner_report(plan, None))

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
