import os
import subprocess
from pathlib import Path
import tempfile
import unittest
from unittest import mock

from system.tests.update.test_git_classification import (
    _run, _apply as _apply_files, _commit, _diverging_repos,
)
from system.update import git_update
from system.update.target import TargetSnapshot

_REPO_ROOT = Path(__file__).resolve().parents[3]
_VALIDATOR_FILES = {
    'system/validation/validate_v1.py':
        (_REPO_ROOT / 'system' / 'validation' / 'validate_v1.py').read_text(),
    'system/validation/validate_prompts.py':
        (_REPO_ROOT / 'system' / 'validation' / 'validate_prompts.py').read_text(),
    'system/routing/runtime_naming.py':
        (_REPO_ROOT / 'system' / 'routing' / 'runtime_naming.py').read_text(),
}


def _base_files(extra=None):
    """A minimal but genuinely `validate_v1 --mode personal` +
    `validate_prompts`-clean tree: the three real validator/dependency
    files (so `_validate_candidate`'s subprocesses have something real to
    run) plus a real tracked file under each of the three primary
    directories (`validate_layout` requires the directory to exist, but
    Git — and so the candidate tree `apply` builds from raw blob entries —
    cannot represent an empty directory, so each needs an actual file).
    """
    files = dict(_VALIDATOR_FILES)
    files['guides/placeholder.md'] = 'x\n'
    files['workspace/placeholder.md'] = 'x\n'
    if extra:
        files.update(extra)
    return files


def _confirm(root, target_dir, target_sha):
    with mock.patch.object(git_update.target, 'resolve',
                            return_value=TargetSnapshot(target_sha, 'main', 'test')), \
         mock.patch.object(git_update.target, 'CANONICAL_URL', 'file://' + target_dir):
        plan = git_update.classify(root)
        digest = git_update.preview(plan).digest
    return plan, digest


def _do_apply(root, target_dir, target_sha, plan, digest, **kwargs):
    with mock.patch.object(git_update.target, 'resolve',
                            return_value=TargetSnapshot(target_sha, 'main', 'test')), \
         mock.patch.object(git_update.target, 'CANONICAL_URL', 'file://' + target_dir):
        return git_update.apply(root, plan, digest, **kwargs)


class ApplyPreconditionTests(unittest.TestCase):
    def test_no_op_does_not_mutate_or_create_commit(self):
        with tempfile.TemporaryDirectory() as workdir:
            base = _base_files({'system/a.md': 'shipped\n'})
            root, target_dir, base_sha, current_sha, target_sha = _diverging_repos(
                workdir, base, {}, {})
            plan, digest = _confirm(root, target_dir, target_sha)
            self.assertTrue(plan.no_op)
            before_head = _run(['git', '-C', root, 'rev-parse', 'HEAD']).stdout.strip()

            result = _do_apply(root, target_dir, target_sha, plan, digest)

            after_head = _run(['git', '-C', root, 'rev-parse', 'HEAD']).stdout.strip()
            self.assertTrue(result.no_op)
            self.assertFalse(result.mutation_started)
            self.assertIsNone(result.commit)
            self.assertEqual(before_head, after_head)

    def test_conflict_blocks_before_candidate_or_live_mutation(self):
        with tempfile.TemporaryDirectory() as workdir:
            base = _base_files({'system/a.md': 'shipped\n'})
            root, target_dir, base_sha, current_sha, target_sha = _diverging_repos(
                workdir, base, {'system/a.md': 'user edit\n'}, {'system/a.md': 'upstream edit\n'})
            plan, digest = _confirm(root, target_dir, target_sha)
            self.assertIn('system/a.md', plan.conflict)
            before_head = _run(['git', '-C', root, 'rev-parse', 'HEAD']).stdout.strip()

            result = _do_apply(root, target_dir, target_sha, plan, digest)

            after_head = _run(['git', '-C', root, 'rev-parse', 'HEAD']).stdout.strip()
            self.assertEqual('conflict', result.failure)
            self.assertFalse(result.mutation_started)
            self.assertEqual(before_head, after_head)
            self.assertEqual('user edit\n', Path(root, 'system/a.md').read_text())

    def test_stale_current_digest_aborts_before_mutation(self):
        with tempfile.TemporaryDirectory() as workdir:
            base = _base_files({'system/a.md': 'shipped\n'})
            root, target_dir, base_sha, current_sha, target_sha = _diverging_repos(
                workdir, base, {}, {'system/a.md': 'shipped v2\n'})
            plan, digest = _confirm(root, target_dir, target_sha)
            # C moves after the preview was computed.
            _apply_files(root, {'workspace/late.md': 'late\n'})
            _commit(root, 'late local commit')

            result = _do_apply(root, target_dir, target_sha, plan, digest)

            self.assertEqual('stale_state', result.failure)
            self.assertFalse(result.mutation_started)

    def test_stale_target_digest_aborts_before_mutation(self):
        with tempfile.TemporaryDirectory() as workdir:
            base = _base_files({'system/a.md': 'shipped\n'})
            root, target_dir, base_sha, current_sha, target_sha_1 = _diverging_repos(
                workdir, base, {}, {'system/a.md': 'shipped v2\n'})
            plan, digest = _confirm(root, target_dir, target_sha_1)
            # T moves after the preview was computed.
            _apply_files(target_dir, {'system/a.md': 'shipped v3\n'})
            target_sha_2 = _commit(target_dir, 'target moved again')

            result = _do_apply(root, target_dir, target_sha_2, plan, digest)

            self.assertEqual('stale_state', result.failure)
            self.assertFalse(result.mutation_started)

    def test_dirty_worktree_blocks_apply(self):
        with tempfile.TemporaryDirectory() as workdir:
            base = _base_files({'system/a.md': 'shipped\n'})
            root, target_dir, base_sha, current_sha, target_sha = _diverging_repos(
                workdir, base, {}, {'system/a.md': 'shipped v2\n'})
            Path(root, 'workspace').mkdir(exist_ok=True)
            Path(root, 'workspace', 'dirty.md').write_text('dirty\n')
            # Confirm the already-dirty state itself, so the resulting
            # digest matches what apply() will re-derive — this exercises
            # apply()'s own dedicated `blocked` refusal, not just a
            # stale-digest mismatch from dirtying *after* confirming.
            plan, digest = _confirm(root, target_dir, target_sha)
            self.assertEqual('dirty_or_untracked', plan.blocked)

            result = _do_apply(root, target_dir, target_sha, plan, digest)

            self.assertEqual('blocked', result.failure)
            self.assertFalse(result.mutation_started)


class ApplyCandidateTests(unittest.TestCase):
    def test_successful_apply_preserves_user_only_applies_upstream_only_and_records_provenance(self):
        with tempfile.TemporaryDirectory() as workdir:
            base = _base_files({'system/a.md': 'shipped\n', 'workspace/note.md': 'user\n'})
            root, target_dir, base_sha, current_sha, target_sha = _diverging_repos(
                workdir, base, {'workspace/note.md': 'user modified\n'},
                {'system/a.md': 'shipped v2\n', 'system/b.md': 'new upstream file\n'})
            plan, digest = _confirm(root, target_dir, target_sha)
            self.assertEqual((), plan.conflict)
            note_mtime_before = Path(root, 'workspace', 'note.md').stat().st_mtime_ns

            result = _do_apply(root, target_dir, target_sha, plan, digest)

            self.assertTrue(result.mutation_started)
            self.assertTrue(result.validation_ran)
            self.assertTrue(result.validation_passed)
            self.assertIsNotNone(result.commit)
            self.assertEqual('shipped v2\n', Path(root, 'system/a.md').read_text())
            self.assertEqual('new upstream file\n', Path(root, 'system/b.md').read_text())
            self.assertEqual('user modified\n', Path(root, 'workspace', 'note.md').read_text())
            # user_only paths are never written: mtime proves it, not just content.
            self.assertEqual(note_mtime_before, Path(root, 'workspace', 'note.md').stat().st_mtime_ns)
            parents = _run(['git', '-C', root, 'rev-parse', 'HEAD^1', 'HEAD^2']).stdout.split()
            self.assertEqual([current_sha, target_sha], parents)
            status = _run(['git', '-C', root, 'status', '--porcelain']).stdout
            self.assertEqual('', status.strip())

    def test_candidate_built_outside_live_checkout(self):
        created = []
        real_tmpdir_cls = tempfile.TemporaryDirectory

        class _Recording(real_tmpdir_cls):
            def __enter__(self):
                name = super().__enter__()
                created.append(name)
                return name

        with tempfile.TemporaryDirectory() as workdir:
            base = _base_files({'system/a.md': 'shipped\n'})
            root, target_dir, base_sha, current_sha, target_sha = _diverging_repos(
                workdir, base, {}, {'system/a.md': 'shipped v2\n'})
            plan, digest = _confirm(root, target_dir, target_sha)

            with mock.patch.object(git_update.tempfile, 'TemporaryDirectory', _Recording):
                result = _do_apply(root, target_dir, target_sha, plan, digest)

            self.assertTrue(result.mutation_started)
            self.assertTrue(created)
            for path in created:
                self.assertFalse(str(path).startswith(root))


class ApplyValidationTests(unittest.TestCase):
    def test_candidate_validated_with_personal_mode_blocks_bad_naming(self):
        with tempfile.TemporaryDirectory() as workdir:
            base = _base_files({'system/a.md': 'shipped\n'})
            root, target_dir, base_sha, current_sha, target_sha = _diverging_repos(
                workdir, base, {}, {'system/Bad-Name.md': 'bad\n'})
            plan, digest = _confirm(root, target_dir, target_sha)
            before_head = _run(['git', '-C', root, 'rev-parse', 'HEAD']).stdout.strip()

            result = _do_apply(root, target_dir, target_sha, plan, digest)

            after_head = _run(['git', '-C', root, 'rev-parse', 'HEAD']).stdout.strip()
            self.assertTrue(result.validation_ran)
            self.assertFalse(result.validation_passed)
            self.assertFalse(result.mutation_started)
            self.assertEqual('validation_failed', result.failure)
            self.assertEqual(before_head, after_head)
            self.assertFalse(Path(root, 'system', 'Bad-Name.md').exists())

    def test_candidate_validated_with_prompts_blocks_missing_frontmatter(self):
        with tempfile.TemporaryDirectory() as workdir:
            base = _base_files({'system/a.md': 'shipped\n'})
            root, target_dir, base_sha, current_sha, target_sha = _diverging_repos(
                workdir, base, {}, {'workspace/prompts/broken.md': 'no frontmatter\n'})
            plan, digest = _confirm(root, target_dir, target_sha)

            result = _do_apply(root, target_dir, target_sha, plan, digest)

            self.assertTrue(result.validation_ran)
            self.assertFalse(result.validation_passed)
            self.assertFalse(result.mutation_started)
            self.assertEqual('validation_failed', result.failure)
            self.assertFalse(Path(root, 'workspace', 'prompts', 'broken.md').exists())

    def test_validate_public_not_invoked_and_only_the_two_personal_validators_run(self):
        with tempfile.TemporaryDirectory() as workdir:
            base = _base_files({'system/a.md': 'shipped\n'})
            root, target_dir, base_sha, current_sha, target_sha = _diverging_repos(
                workdir, base, {}, {'system/a.md': 'shipped v2\n'})
            plan, digest = _confirm(root, target_dir, target_sha)
            real_run = subprocess.run
            invoked = []

            def spy(args, *a, **kw):
                if args and args[0] == git_update.sys.executable:
                    invoked.append(Path(args[2]).name)
                return real_run(args, *a, **kw)

            with mock.patch.object(git_update.subprocess, 'run', spy):
                result = _do_apply(root, target_dir, target_sha, plan, digest)

            self.assertTrue(result.validation_passed)
            self.assertEqual({'validate_v1.py', 'validate_prompts.py'}, set(invoked))

    def test_candidate_uses_candidate_own_validator_version_not_a_stale_cached_one(self):
        broken_validate_v1 = 'import sys\nsys.exit(1)\n'
        with tempfile.TemporaryDirectory() as workdir:
            base = _base_files({'system/a.md': 'shipped\n'})
            root, target_dir, base_sha, current_sha, target_sha = _diverging_repos(
                workdir, base, {},
                {'system/validation/validate_v1.py': broken_validate_v1})
            plan, digest = _confirm(root, target_dir, target_sha)
            self.assertIn('system/validation/validate_v1.py', plan.upstream_only)

            result = _do_apply(root, target_dir, target_sha, plan, digest)

            self.assertTrue(result.validation_ran)
            self.assertFalse(result.validation_passed)
            self.assertFalse(result.mutation_started)


class ApplyHardeningTests(unittest.TestCase):
    def test_hooks_do_not_fire(self):
        with tempfile.TemporaryDirectory() as workdir:
            base = _base_files({'system/a.md': 'shipped\n'})
            root, target_dir, base_sha, current_sha, target_sha = _diverging_repos(
                workdir, base, {}, {'system/a.md': 'shipped v2\n'})
            sentinel = str(Path(workdir, 'hook_sentinel'))
            hooks_dir = Path(root, '.git', 'hooks')
            hooks_dir.mkdir(exist_ok=True)
            for name in ('reference-transaction', 'post-checkout', 'update'):
                hook = hooks_dir / name
                hook.write_text(f'#!/bin/sh\ntouch {sentinel}_{name}\nexit 0\n')
                hook.chmod(0o755)
            plan, digest = _confirm(root, target_dir, target_sha)

            result = _do_apply(root, target_dir, target_sha, plan, digest)

            self.assertTrue(result.mutation_started)
            self.assertTrue(result.validation_passed)
            for name in ('reference-transaction', 'post-checkout', 'update'):
                self.assertFalse(Path(f'{sentinel}_{name}').exists())


    def test_fsmonitor_does_not_fire_during_apply_mutation(self):
        with tempfile.TemporaryDirectory() as workdir:
            base = _base_files({'system/a.md': 'shipped\n'})
            root, target_dir, base_sha, current_sha, target_sha = _diverging_repos(
                workdir, base, {}, {'system/a.md': 'shipped v2\n', 'system/b.md': 'new\n'})
            sentinel = str(Path(workdir, 'fsmonitor_sentinel'))
            hostile_fsmonitor = str(Path(workdir, 'fsmonitor.sh'))
            Path(hostile_fsmonitor).write_text(f'#!/bin/sh\ntouch {sentinel}\nprintf "1\\n"\n')
            os.chmod(hostile_fsmonitor, 0o755)
            _run(['git', '-C', root, 'config', 'core.fsmonitor', hostile_fsmonitor])
            plan, digest = _confirm(root, target_dir, target_sha)

            result = _do_apply(root, target_dir, target_sha, plan, digest)

            self.assertTrue(result.mutation_started)
            self.assertTrue(result.validation_passed)
            self.assertFalse(Path(sentinel).exists())

    def test_repository_url_rewrite_cannot_redirect_apply(self):
        with tempfile.TemporaryDirectory() as workdir:
            base = _base_files({'system/a.md': 'shipped\n'})
            root, target_dir, base_sha, current_sha, target_sha = _diverging_repos(
                workdir, base, {}, {'system/a.md': 'shipped v2\n'})
            hostile_dir = str(Path(workdir, 'hostile'))
            _run(['git', 'clone', '-q', '--no-hardlinks', root, hostile_dir])
            _run(['git', '-C', root, 'config',
                  f'url.file://{hostile_dir}.insteadOf', f'file://{target_dir}'])
            plan, digest = _confirm(root, target_dir, target_sha)

            result = _do_apply(root, target_dir, target_sha, plan, digest)

            self.assertTrue(result.mutation_started)
            self.assertEqual('shipped v2\n', Path(root, 'system/a.md').read_text())
            parent2 = _run(['git', '-C', root, 'rev-parse', 'HEAD^2']).stdout.strip()
            self.assertEqual(target_sha, parent2)

    def test_apply_uses_controlled_git_for_its_mutation_invocations(self):
        with tempfile.TemporaryDirectory() as workdir:
            base = _base_files({'system/a.md': 'shipped\n'})
            root, target_dir, base_sha, current_sha, target_sha = _diverging_repos(
                workdir, base, {}, {'system/a.md': 'shipped v2\n'})
            plan, digest = _confirm(root, target_dir, target_sha)
            real_controlled_git = git_update.controlled_git
            subcommands = []

            def spy(*args, **kwargs):
                if args:
                    subcommands.append(args[0])
                return real_controlled_git(*args, **kwargs)

            with mock.patch.object(git_update, 'controlled_git', spy):
                result = _do_apply(root, target_dir, target_sha, plan, digest)

            self.assertTrue(result.mutation_started)
            for expected in ('commit-tree', 'update-ref', 'write-tree', 'mktree'):
                self.assertIn(expected, subcommands)

    def test_target_introduced_filter_on_touched_path_blocks_before_mutation(self):
        with tempfile.TemporaryDirectory() as workdir:
            base = _base_files({'system/a.md': 'shipped\n'})
            root, target_dir, base_sha, current_sha, target_sha = _diverging_repos(
                workdir, base, {},
                {'.gitattributes': '*.secret filter=redact\n', 'system/a.secret': 'sensitive\n'})
            _run(['git', '-C', root, 'config', 'filter.redact.clean', 'cat'])
            plan, digest = _confirm(root, target_dir, target_sha)
            before_head = _run(['git', '-C', root, 'rev-parse', 'HEAD']).stdout.strip()

            result = _do_apply(root, target_dir, target_sha, plan, digest)

            after_head = _run(['git', '-C', root, 'rev-parse', 'HEAD']).stdout.strip()
            self.assertEqual('unsafe_repository_state', result.failure)
            self.assertFalse(result.mutation_started)
            self.assertEqual(before_head, after_head)
            self.assertFalse(Path(root, 'system', 'a.secret').exists())


    def test_live_info_attributes_selects_helper_for_target_introduced_path(self):
        """A `filter=`/`diff=` selection can live in the installed clone's
        own `.git/info/attributes`, not only in a tracked `.gitattributes`
        the candidate tree carries. `_candidate_attribute_unsafe` must
        catch this too, or a target-introduced path sharing that pattern
        slips through and the live mutation step can invoke the helper.
        """
        with tempfile.TemporaryDirectory() as workdir:
            base = _base_files({'system/a.md': 'shipped\n'})
            root, target_dir, base_sha, current_sha, target_sha = _diverging_repos(
                workdir, base, {}, {'system/new.secret': 'sensitive\n'})
            info_attrs = Path(root, '.git', 'info', 'attributes')
            info_attrs.write_text('*.secret filter=redact\n')
            sentinel = str(Path(workdir, 'filter_sentinel'))
            hostile = str(Path(workdir, 'hostile.sh'))
            Path(hostile).write_text(f'#!/bin/sh\ntouch {sentinel}\ncat\n')
            os.chmod(hostile, 0o755)
            _run(['git', '-C', root, 'config', 'filter.redact.clean', hostile])
            plan, digest = _confirm(root, target_dir, target_sha)
            before_head = _run(['git', '-C', root, 'rev-parse', 'HEAD']).stdout.strip()

            result = _do_apply(root, target_dir, target_sha, plan, digest)

            after_head = _run(['git', '-C', root, 'rev-parse', 'HEAD']).stdout.strip()
            self.assertEqual('unsafe_repository_state', result.failure)
            self.assertFalse(result.mutation_started)
            self.assertEqual(before_head, after_head)
            self.assertFalse(Path(root, 'system', 'new.secret').exists())
            self.assertFalse(Path(sentinel).exists())


class ApplyRecheckAndRecoveryTests(unittest.TestCase):
    def test_clean_state_rechecked_immediately_before_mutation(self):
        with tempfile.TemporaryDirectory() as workdir:
            base = _base_files({'system/a.md': 'shipped\n'})
            root, target_dir, base_sha, current_sha, target_sha = _diverging_repos(
                workdir, base, {}, {'system/a.md': 'shipped v2\n'})
            plan, digest = _confirm(root, target_dir, target_sha)

            def dirty_it():
                Path(root, 'workspace').mkdir(exist_ok=True)
                Path(root, 'workspace', 'concurrent.md').write_text('concurrent write\n')

            result = _do_apply(root, target_dir, target_sha, plan, digest, _before_recheck=dirty_it)

            self.assertFalse(result.mutation_started)
            self.assertTrue(result.concurrent_change)
            self.assertEqual('concurrent_change_pre_mutation', result.failure)
            self.assertEqual('shipped\n', Path(root, 'system', 'a.md').read_text())

    def test_failed_post_mutation_step_restores_pre_update_state(self):
        with tempfile.TemporaryDirectory() as workdir:
            base = _base_files({'system/a.md': 'shipped\n'})
            root, target_dir, base_sha, current_sha, target_sha = _diverging_repos(
                workdir, base, {},
                {'system/a.md': 'shipped v2\n', 'system/b.md': 'new\n'})
            plan, digest = _confirm(root, target_dir, target_sha)

            def fail():
                raise git_update._SimulatedFailure()

            result = _do_apply(root, target_dir, target_sha, plan, digest, _after_mutation=fail)

            self.assertTrue(result.mutation_started)
            self.assertTrue(result.rollback_attempted)
            self.assertTrue(result.rollback_completed)
            self.assertFalse(result.concurrent_change)
            after_head = _run(['git', '-C', root, 'rev-parse', 'HEAD']).stdout.strip()
            self.assertEqual(current_sha, after_head)
            self.assertEqual('shipped\n', Path(root, 'system', 'a.md').read_text())
            self.assertFalse(Path(root, 'system', 'b.md').exists())
            status = _run(['git', '-C', root, 'status', '--porcelain']).stdout
            self.assertEqual('', status.strip())

    def test_concurrent_external_change_stops_automatic_recovery(self):
        with tempfile.TemporaryDirectory() as workdir:
            base = _base_files({'system/a.md': 'shipped\n'})
            root, target_dir, base_sha, current_sha, target_sha = _diverging_repos(
                workdir, base, {}, {'system/a.md': 'shipped v2\n'})
            plan, digest = _confirm(root, target_dir, target_sha)

            def tamper():
                Path(root, 'system', 'a.md').write_text('externally changed\n')
                raise git_update._SimulatedFailure()

            result = _do_apply(root, target_dir, target_sha, plan, digest, _after_mutation=tamper)

            self.assertTrue(result.mutation_started)
            self.assertTrue(result.rollback_attempted)
            self.assertFalse(result.rollback_completed)
            self.assertTrue(result.concurrent_change)
            # Never overwrites a path an external process has since changed.
            self.assertEqual('externally changed\n', Path(root, 'system', 'a.md').read_text())


    def test_ref_cas_fails_closed_when_ref_moves_concurrently(self):
        with tempfile.TemporaryDirectory() as workdir:
            base = _base_files({'system/a.md': 'shipped\n'})
            root, target_dir, base_sha, current_sha, target_sha = _diverging_repos(
                workdir, base, {}, {'system/a.md': 'shipped v2\n'})
            plan, digest = _confirm(root, target_dir, target_sha)

            def move_ref_concurrently():
                # A real, independent ref advance (as another process would
                # make), touching no file — the CAS old-value check, not the
                # per-path content check, is what must catch this.
                tree = _run(['git', '-C', root, 'rev-parse', f'{current_sha}^{{tree}}']).stdout.strip()
                concurrent_commit = _run(
                    ['git', '-C', root, 'commit-tree', tree, '-p', current_sha,
                     '-m', 'concurrent update']).stdout.strip()
                _run(['git', '-C', root, 'update-ref', 'HEAD', concurrent_commit, current_sha])

            result = _do_apply(
                root, target_dir, target_sha, plan, digest, _after_mutation=move_ref_concurrently)

            self.assertTrue(result.mutation_started)
            self.assertEqual('ref_cas_failed', result.failure)
            self.assertTrue(result.concurrent_change)
            self.assertTrue(result.rollback_attempted)
            after_head = _run(['git', '-C', root, 'rev-parse', 'HEAD']).stdout.strip()
            # Our own CAS never overwrote the concurrent process's ref move.
            self.assertNotEqual(current_sha, after_head)

    def test_interrupted_process_leaves_ref_at_c_and_next_check_reports_unstable_state(self):
        with tempfile.TemporaryDirectory() as workdir:
            base = _base_files({'system/a.md': 'shipped\n'})
            root, target_dir, base_sha, current_sha, target_sha = _diverging_repos(
                workdir, base, {}, {'system/a.md': 'shipped v2\n'})
            plan, digest = _confirm(root, target_dir, target_sha)

            def crash():
                raise RuntimeError('simulated process kill')

            with self.assertRaises(RuntimeError):
                _do_apply(root, target_dir, target_sha, plan, digest, _after_mutation=crash)

            after_head = _run(['git', '-C', root, 'rev-parse', 'HEAD']).stdout.strip()
            self.assertEqual(current_sha, after_head)
            fresh_plan, _digest = _confirm(root, target_dir, target_sha)
            self.assertEqual('dirty_or_untracked', fresh_plan.blocked)


class ApplyModeAndRecoveryHardeningTests(unittest.TestCase):
    def test_target_introduces_symlink_and_materializes_it_correctly(self):
        with tempfile.TemporaryDirectory() as workdir:
            base = _base_files({'system/a.md': 'shipped\n'})
            root, target_dir, base_sha, current_sha, target_sha = _diverging_repos(
                workdir, base, {}, {})
            # _diverging_repos' plain-file helpers only write regular-file
            # content; introduce a real symlink directly.
            os.symlink('a.md', Path(target_dir, 'system', 'link_to_a.md'))
            _run(['git', '-C', target_dir, 'add', '-A'])
            target_sha = _commit(target_dir, 'introduce symlink')
            plan, digest = _confirm(root, target_dir, target_sha)
            self.assertIn('system/link_to_a.md', plan.upstream_only)

            result = _do_apply(root, target_dir, target_sha, plan, digest)

            self.assertTrue(result.mutation_started)
            self.assertTrue(result.validation_passed)
            link_path = Path(root, 'system', 'link_to_a.md')
            self.assertTrue(link_path.is_symlink())
            self.assertEqual('a.md', os.readlink(link_path))

    def test_rollback_restores_executable_mode_exactly(self):
        with tempfile.TemporaryDirectory() as workdir:
            base = _base_files({'system/a.sh': 'echo hi\n'})
            root, target_dir, base_sha, current_sha, target_sha = _diverging_repos(
                workdir, base, {}, {})
            script = Path(target_dir, 'system', 'a.sh')
            script.write_text('echo hi v2\n')
            os.chmod(script, 0o755)
            _run(['git', '-C', target_dir, 'add', '-A'])
            target_sha = _commit(target_dir, 'make executable')
            plan, digest = _confirm(root, target_dir, target_sha)
            self.assertIn('system/a.sh', plan.upstream_only)

            def fail():
                raise git_update._SimulatedFailure()

            result = _do_apply(root, target_dir, target_sha, plan, digest, _after_mutation=fail)

            self.assertTrue(result.rollback_attempted)
            self.assertTrue(result.rollback_completed)
            a_sh = Path(root, 'system', 'a.sh')
            self.assertEqual('echo hi\n', a_sh.read_text())
            self.assertFalse(os.access(a_sh, os.X_OK))
            status = _run(['git', '-C', root, 'status', '--porcelain']).stdout
            self.assertEqual('', status.strip())


    def test_fsmonitor_and_hooks_do_not_fire_during_recovery(self):
        with tempfile.TemporaryDirectory() as workdir:
            base = _base_files({'system/a.md': 'shipped\n'})
            root, target_dir, base_sha, current_sha, target_sha = _diverging_repos(
                workdir, base, {}, {'system/a.md': 'shipped v2\n'})
            fsmonitor_sentinel = str(Path(workdir, 'fsmonitor_sentinel'))
            hostile_fsmonitor = str(Path(workdir, 'fsmonitor.sh'))
            Path(hostile_fsmonitor).write_text(
                f'#!/bin/sh\ntouch {fsmonitor_sentinel}\nprintf "1\\n"\n')
            os.chmod(hostile_fsmonitor, 0o755)
            _run(['git', '-C', root, 'config', 'core.fsmonitor', hostile_fsmonitor])
            hook_sentinel = str(Path(workdir, 'hook_sentinel'))
            hooks_dir = Path(root, '.git', 'hooks')
            hooks_dir.mkdir(exist_ok=True)
            hook = hooks_dir / 'reference-transaction'
            hook.write_text(f'#!/bin/sh\ntouch {hook_sentinel}\nexit 0\n')
            hook.chmod(0o755)
            plan, digest = _confirm(root, target_dir, target_sha)

            def fail():
                raise git_update._SimulatedFailure()

            result = _do_apply(root, target_dir, target_sha, plan, digest, _after_mutation=fail)

            self.assertTrue(result.rollback_attempted)
            self.assertTrue(result.rollback_completed)
            self.assertFalse(Path(fsmonitor_sentinel).exists())
            self.assertFalse(Path(hook_sentinel).exists())

    def test_second_path_failure_during_mutation_still_recovers_the_first(self):
        with tempfile.TemporaryDirectory() as workdir:
            base = _base_files({'system/a.md': 'shipped\n'})
            root, target_dir, base_sha, current_sha, target_sha = _diverging_repos(
                workdir, base, {}, {'system/a.md': 'shipped v2\n', 'system/b.md': 'new\n'})
            plan, digest = _confirm(root, target_dir, target_sha)
            # Sorted upstream_only is ('system/a.md', 'system/b.md'); fail
            # exactly the SECOND path's --cacheinfo write, after the first
            # has already genuinely mutated the live worktree/index.
            real_controlled_git = git_update.controlled_git
            counted = {'n': 0}

            class _Fail:
                returncode = 1
                stdout = ''
                stderr = 'simulated failure'

            def spy(*args, **kwargs):
                if args and args[0] == 'update-index' and '--cacheinfo' in args:
                    counted['n'] += 1
                    if counted['n'] == 2:
                        return _Fail()
                return real_controlled_git(*args, **kwargs)

            with mock.patch.object(git_update, 'controlled_git', spy):
                result = _do_apply(root, target_dir, target_sha, plan, digest)

            self.assertTrue(result.mutation_started)
            self.assertTrue(result.rollback_attempted)
            self.assertTrue(result.rollback_completed)
            self.assertEqual('shipped\n', Path(root, 'system', 'a.md').read_text())
            self.assertFalse(Path(root, 'system', 'b.md').exists())
            status = _run(['git', '-C', root, 'status', '--porcelain']).stdout
            self.assertEqual('', status.strip())

    def test_recovery_command_failure_reports_incomplete_rollback(self):
        with tempfile.TemporaryDirectory() as workdir:
            base = _base_files({'system/a.md': 'shipped\n'})
            root, target_dir, base_sha, current_sha, target_sha = _diverging_repos(
                workdir, base, {}, {'system/a.md': 'shipped v2\n'})
            plan, digest = _confirm(root, target_dir, target_sha)
            real_controlled_git = git_update.controlled_git
            counted = {'n': 0}

            class _Fail:
                returncode = 1
                stdout = ''
                stderr = 'simulated recovery failure'

            def spy(*args, **kwargs):
                if args and args[0] == 'update-index':
                    counted['n'] += 1
                    if counted['n'] == 2:  # the forward write's own call is #1
                        return _Fail()
                return real_controlled_git(*args, **kwargs)

            def fail():
                raise git_update._SimulatedFailure()

            with mock.patch.object(git_update, 'controlled_git', spy):
                result = _do_apply(root, target_dir, target_sha, plan, digest, _after_mutation=fail)

            self.assertTrue(result.rollback_attempted)
            self.assertFalse(result.rollback_completed)

    def test_external_index_only_change_stops_automatic_recovery(self):
        with tempfile.TemporaryDirectory() as workdir:
            base = _base_files({'system/a.md': 'shipped\n'})
            root, target_dir, base_sha, current_sha, target_sha = _diverging_repos(
                workdir, base, {}, {'system/a.md': 'shipped v2\n'})
            plan, digest = _confirm(root, target_dir, target_sha)

            def tamper_index_only():
                # Another process re-stages the SAME path against
                # different content without touching the worktree file
                # the updater itself already wrote there.
                other = subprocess.run(
                    ['git', '-C', root, 'hash-object', '-w', '--stdin'],
                    input='different content\n', capture_output=True, text=True, check=True)
                other_sha = other.stdout.strip()
                _run(['git', '-C', root, 'update-index', '--add', '--cacheinfo',
                      f'100644,{other_sha},system/a.md'])
                raise git_update._SimulatedFailure()

            result = _do_apply(
                root, target_dir, target_sha, plan, digest, _after_mutation=tamper_index_only)

            self.assertTrue(result.rollback_attempted)
            self.assertFalse(result.rollback_completed)
            self.assertTrue(result.concurrent_change)


if __name__ == '__main__':
    unittest.main()
