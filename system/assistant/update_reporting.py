"""Loop 5 beginner/Advanced presentation glue for Safe Update.

Routes to the existing canonical owners (`system.update.git_update`,
`system.update.side_by_side`) for every classification, apply/migrate,
recovery, and validator decision; this module never reimplements any of
that. It aggregates their already-produced Plan/Preview/Result objects
into a truthful beginner report (area/count only, never a Personal path
or filename) and an Advanced detail view (Personal
`workspace/context/*.md` paths named only when `access.permitted`
returns True; product/implementation detail such as commit SHAs may
appear freely).

See `system/assistant/update_workflow.md` for the user-facing contract
this module implements.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from system.context.access import permitted
from system.update import git_update, side_by_side
from system.update.target import controlled_git
from system.validation.validate_v1 import context_registry_entries

_KNOWN_AREAS = frozenset({'workspace', 'system', 'guides'})
_HEADER_READ_LIMIT = 4096


@dataclass(frozen=True)
class HostCapability:
    """Trusted host/runtime input — supplied by the caller's own
    deployment/adapter boundary, NEVER parsed from user/chat/prompt
    text. `can_read` is source/current-installation read access,
    `can_write` is canonical write/apply capability, and
    `can_run_local_commands` is the ability to execute local
    validators/Git — these are independent: a web client may have
    `can_read` without either of the others.
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
class WorkflowResult:
    """The one object `run_update_workflow` returns. `digest` is the
    FRESH preview digest for this call — pass it back as
    `confirm_digest` on a subsequent call to actually apply/migrate;
    passing a stale one is always refused. `advanced_candidates` holds
    raw `(path, header, scope_path)` triples a caller may later pass to
    `disclosed_paths` for Advanced rendering — never pre-filtered content,
    never shown by default.
    """
    install_type: str
    digest: str | None
    ready: bool
    applied: bool
    beginner: BeginnerReport
    failure: str | None = None
    advanced_candidates: tuple[tuple[str, str, str], ...] = ()


# --- install-type routing -------------------------------------------------

def _is_git_installation(root) -> bool:
    """The smallest proof of a real Git clone/worktree at `root`: a
    successful `git rev-parse --git-dir` through the same controlled Git
    boundary every other probe in this project uses. Correct for a
    linked worktree, where `.git` is a FILE (a `gitdir: <path>`
    pointer) rather than a directory — `rev-parse` resolves that on
    Git's own authority, never by this module inspecting `.git` itself.
    """
    result = controlled_git('rev-parse', '--git-dir', cwd=str(root))
    return result.returncode == 0


def detect_install_type(root, capability: HostCapability) -> str:
    """`'git'`, `'zip'`, or `'unknown'` — from actual host/repository
    evidence only, never from how the user describes their install.
    Without proven read capability, the route cannot be determined at
    all and fails closed to `'unknown'`.
    """
    if capability.can_read is not True:
        return 'unknown'
    if _is_git_installation(root):
        return 'git'
    if Path(root).is_dir():
        return 'zip'
    return 'unknown'


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


# --- Git beginner report ---------------------------------------------------

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

    if result.concurrent_change:
        if result.rollback_completed:
            return BeginnerReport('Update failed validation; the updater restored the verified prior state.')
        return BeginnerReport(
            'Update did not complete and some updater changes could not be safely restored '
            'because the installation changed concurrently.')
    if not result.validation_ran:
        return BeginnerReport('Nothing was changed. The update could not be completed safely.')
    if not result.validation_passed:
        if result.rollback_completed:
            return BeginnerReport('Update failed validation; the updater restored the verified prior state.')
        return BeginnerReport(
            'Update did not complete and some updater changes could not be safely restored '
            'because the installation changed concurrently.')
    return BeginnerReport('Update applied and validation passed.')


# --- ZIP/side-by-side beginner report --------------------------------------

def zip_beginner_report(plan: side_by_side.SideBySidePlan,
                         result: side_by_side.MigrationResult | None) -> BeginnerReport:
    """Build a beginner report from Loop 4's own `SideBySidePlan`/
    `MigrationResult`. `SideBySidePlan` has no pre-built area/count
    summary (unlike `git_update.Preview`), so the display-only grouping
    above is applied here to its raw path tuples — never a new
    classification decision.
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

    if not result.ready:
        if result.failure == 'personal_validation_failed':
            return BeginnerReport('Update did not pass validation. Nothing was changed.')
        return BeginnerReport('Nothing was changed. The update could not be completed safely.')
    details = _count_lines(_area_counts(plan.kept), 'preserved')
    return BeginnerReport(
        'Updated side-by-side copy is ready. Your original folder was not changed.', details)


def no_write_report() -> BeginnerReport:
    return BeginnerReport(
        'A preview is available, but this client cannot write or validate.',
        ('nothing was written', 'validation was not run here'))


# --- Advanced authorization -------------------------------------------------

def _read_bounded_header(path) -> str:
    """At most `_HEADER_READ_LIMIT` bytes — enough for any realistic
    frontmatter block, never the whole module body, so a programming
    error elsewhere in this presentation layer cannot pull full
    Personal content into an authorization check.
    """
    try:
        with open(path, 'rb') as handle:
            raw = handle.read(_HEADER_READ_LIMIT)
    except OSError:
        return ''
    return raw.decode('utf-8', errors='replace')


def scope_candidates(root, registry_text: str, paths) -> tuple[tuple[str, str, str], ...]:
    """Of `paths` (candidate `workspace/context/*.md` paths already
    produced by an existing Plan), the ones that fall under a scope the
    registry actually names — resolved exclusively via
    `context_registry_entries` (no second parser) — paired with a
    bounded host-side header read of each. An unclassifiable path (no
    `.md` suffix, not under any registered scope) is simply never
    included, which is what later makes `access.permitted` fail closed
    for it on its own.
    """
    entries = context_registry_entries(registry_text)
    candidates = []
    for path in paths:
        if not path.endswith('.md'):
            continue
        for _scope, target in entries:
            canonical = side_by_side.normalize_relative(target.rstrip('/'))
            if canonical is None:
                continue
            if path == canonical or path.startswith(canonical + '/'):
                header = _read_bounded_header(Path(root, path))
                candidates.append((path, header, canonical))
                break
    return tuple(candidates)


def _git_workflow(root, capability: HostCapability, confirm_digest: str | None) -> WorkflowResult:
    plan = git_update.classify(root)
    preview = git_update.preview(plan)
    fresh_digest = preview.digest
    confirmed = confirm_digest is not None and confirm_digest == fresh_digest

    if not (capability.can_write and capability.can_run_local_commands):
        if confirmed:
            # An explicit confirmation never upgrades a no-write client's
            # actual capability — apply is never called here.
            return WorkflowResult('git', fresh_digest, False, False, no_write_report())
        return WorkflowResult('git', fresh_digest, False, False,
                               git_beginner_report(plan, preview.summary, None))

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
    ready = result.validation_ran and result.validation_passed and not result.concurrent_change
    return WorkflowResult('git', fresh_digest, ready, True,
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

    if not (capability.can_write and capability.can_run_local_commands):
        if confirmed:
            return WorkflowResult('zip', fresh_digest, False, False, no_write_report())
        return WorkflowResult('zip', fresh_digest, False, False, zip_beginner_report(plan, None))

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
    return WorkflowResult('zip', fresh_digest, result.ready, True,
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
    client lacking write/local-command capability can never cause
    apply/migrate to run no matter what it passes as `confirm_digest`.
    """
    install_type = detect_install_type(root, capability)
    if install_type == 'unknown':
        return WorkflowResult(
            'unknown', None, False, False,
            BeginnerReport('This installation could not be checked safely.'),
            failure='unknown_install_type')
    if install_type == 'git':
        return _git_workflow(root, capability, confirm_digest)
    return _zip_workflow(root, destination, capability, confirm_digest, exclude)


def disclosed_paths(candidates: tuple[tuple[str, str, str], ...], *, host_read: bool,
                     deployment: DeploymentBinding = DeploymentBinding()) -> tuple[str, ...]:
    """Of `candidates` (`(path, header, scope_path)` triples), only the
    ones `access.permitted` actually authorizes — called directly, per
    path, never reimplemented. `deployment` defaults to the fail-closed
    binding, so a caller with no trusted deployment state discloses
    nothing restricted.
    """
    allowed = []
    for path, header, scope_path in candidates:
        if permitted(header, path=path, scope_path=scope_path, host_read=host_read,
                     required=True, personal_owner=deployment.personal_owner,
                     private_instance=deployment.private_instance):
            allowed.append(path)
    return tuple(allowed)
