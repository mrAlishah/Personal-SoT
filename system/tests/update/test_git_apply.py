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
            identity = _run([
                'git', '-C', root, 'show', '-s', '--format=%an%n%ae%n%cn%n%ce', 'HEAD'
            ]).stdout.splitlines()
            self.assertEqual([
                'Personal-SoT Safe Update',
                'safe-update@personal-sot.invalid',
                'Personal-SoT Safe Update',
                'safe-update@personal-sot.invalid',
            ], identity)
            status = _run(['git', '-C', root, 'status', '--porcelain']).stdout
            self.assertEqual('', status.strip())

    def test_apply_needs_no_user_git_identity(self):
        with tempfile.TemporaryDirectory() as workdir:
            base = _base_files({'system/a.md': 'shipped\n'})
            root, target_dir, base_sha, current_sha, target_sha = _diverging_repos(
                workdir, base, {}, {'system/a.md': 'shipped v2\n'})
            plan, digest = _confirm(root, target_dir, target_sha)

            # The real installer may have no repository-local identity, and
            # controlled_git intentionally hides global/system Git config.
            _run(['git', '-C', root, 'config', '--unset-all', 'user.email'], check=False)
            _run(['git', '-C', root, 'config', '--unset-all', 'user.name'], check=False)

            result = _do_apply(root, target_dir, target_sha, plan, digest)

            self.assertTrue(result.mutation_started)
            self.assertTrue(result.validation_ran)
            self.assertTrue(result.validation_passed)
            self.assertIsNotNone(result.commit)
            self.assertIsNone(result.failure)
            identity = _run([
                'git', '-C', root, 'show', '-s', '--format=%an%n%ae%n%cn%n%ce', 'HEAD'
            ]).stdout.splitlines()
            self.assertEqual([
                'Personal-SoT Safe Update',
                'safe-update@personal-sot.invalid',
                'Personal-SoT Safe Update',
                'safe-update@personal-sot.invalid',
            ], identity)

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
            concurrent_commit_holder = {}

            def move_ref_concurrently():
                # A real, independent ref advance (as another process would
                # make), touching no file — the CAS old-value check, not the
                # per-path content check, is what must catch this.
                tree = _run(['git', '-C', root, 'rev-parse', f'{current_sha}^{{tree}}']).stdout.strip()
                concurrent_commit = _run(
                    ['git', '-C', root, 'commit-tree', tree, '-p', current_sha,
                     '-m', 'concurrent update']).stdout.strip()
                _run(['git', '-C', root, 'update-ref', 'HEAD', concurrent_commit, current_sha])
                concurrent_commit_holder['sha'] = concurrent_commit

            result = _do_apply(
                root, target_dir, target_sha, plan, digest, _after_mutation=move_ref_concurrently)

            self.assertTrue(result.mutation_started)
            self.assertEqual('ref_cas_failed', result.failure)
            self.assertTrue(result.concurrent_change)
            self.assertTrue(result.rollback_attempted)
            # A concurrent ref move means the overall recovery boundary is
            # incomplete — the ref component of it can never be "restored"
            # since the updater deliberately never overwrites it — even
            # though every updater-owned worktree/index path may still be
            # safely restored.
            self.assertFalse(result.rollback_completed)
            after_head = _run(['git', '-C', root, 'rev-parse', 'HEAD']).stdout.strip()
            # Our own CAS never overwrote the concurrent process's ref move.
            self.assertEqual(concurrent_commit_holder['sha'], after_head)

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


    def test_real_filesystem_exception_on_second_path_still_recovers_the_first(self):
        """A REAL OSError (not a mocked/injected return value) raised
        inside `_write_entry`'s own filesystem operations, for the SECOND
        touched path, after the first path has already been genuinely
        mutated live. Proves the exception cannot escape `apply()`
        uncaught and skip recovery.
        """
        with tempfile.TemporaryDirectory() as workdir:
            base = _base_files({'system/a.md': 'shipped\n'})
            root, target_dir, base_sha, current_sha, target_sha = _diverging_repos(
                workdir, base, {},
                {'system/a.md': 'shipped v2\n', 'system/locked/b.md': 'new\n'})
            locked_dir = Path(root, 'system', 'locked')
            locked_dir.mkdir(parents=True, exist_ok=True)
            os.chmod(locked_dir, 0o555)  # read+execute, no write: a real PermissionError source
            plan, digest = _confirm(root, target_dir, target_sha)
            self.assertEqual(('system/a.md', 'system/locked/b.md'), plan.upstream_only)

            try:
                result = _do_apply(root, target_dir, target_sha, plan, digest)
            finally:
                os.chmod(locked_dir, 0o755)

            self.assertTrue(result.mutation_started)
            self.assertTrue(result.rollback_attempted)
            self.assertTrue(result.rollback_completed)
            self.assertEqual('shipped\n', Path(root, 'system', 'a.md').read_text())
            self.assertFalse(Path(root, 'system', 'locked', 'b.md').exists())
            status = _run(['git', '-C', root, 'status', '--porcelain']).stdout
            self.assertEqual('', status.strip())

    def test_first_path_failure_before_any_mutation_reports_mutation_started_false(self):
        """A failure resolving the FIRST touched path's own blob content
        (a pure read, before any live worktree/index write is even
        attempted) must not be reported as having started a mutation —
        nothing was actually touched, so there is nothing to roll back.
        """
        with tempfile.TemporaryDirectory() as workdir:
            base = _base_files({'system/a.md': 'shipped\n'})
            root, target_dir, base_sha, current_sha, target_sha = _diverging_repos(
                workdir, base, {}, {'system/a.md': 'shipped v2\n'})
            plan, digest = _confirm(root, target_dir, target_sha)
            real_controlled_git = git_update.controlled_git

            class _Fail:
                returncode = 1
                stdout = b''
                stderr = b'simulated read failure'

            def spy(*args, **kwargs):
                if args and args[0] == 'cat-file':
                    return _Fail()
                return real_controlled_git(*args, **kwargs)

            with mock.patch.object(git_update, 'controlled_git', spy):
                result = _do_apply(root, target_dir, target_sha, plan, digest)

            self.assertFalse(result.mutation_started)
            self.assertFalse(result.rollback_attempted)
            after_head = _run(['git', '-C', root, 'rev-parse', 'HEAD']).stdout.strip()
            self.assertEqual(current_sha, after_head)


    def test_user_only_file_with_upstream_descendant_fails_closed_before_mutation(self):
        """B has neither; C has `workspace/x` as a plain file (preserved,
        user_only); T introduces `workspace/x/y.md` (upstream_only). Both
        classify independently with no per-path conflict, but a Git tree
        cannot hold `workspace/x` as a blob AND `workspace/x/...` as a
        descendant at once — this must fail closed before any candidate
        is built or any live path is touched, not silently drop one side.
        """
        with tempfile.TemporaryDirectory() as workdir:
            base = _base_files({'system/a.md': 'shipped\n'})
            root, target_dir, base_sha, current_sha, target_sha = _diverging_repos(
                workdir, base, {'workspace/x': 'a file\n'}, {'workspace/x/y.md': 'descendant\n'})
            plan, digest = _confirm(root, target_dir, target_sha)
            self.assertEqual((), plan.conflict)
            before_head = _run(['git', '-C', root, 'rev-parse', 'HEAD']).stdout.strip()

            result = _do_apply(root, target_dir, target_sha, plan, digest)

            after_head = _run(['git', '-C', root, 'rev-parse', 'HEAD']).stdout.strip()
            self.assertFalse(result.mutation_started)
            self.assertEqual('candidate_path_conflict', result.failure)
            self.assertEqual(before_head, after_head)
            self.assertEqual('a file\n', Path(root, 'workspace', 'x').read_text())
            status = _run(['git', '-C', root, 'status', '--porcelain']).stdout
            self.assertEqual('', status.strip())

    def test_user_only_descendant_with_upstream_file_fails_closed_before_mutation(self):
        """The reverse shape: C has a descendant under `workspace/x/`
        (user_only); T replaces `workspace/x` itself with a plain file
        (upstream_only). Against current HEAD this raises an unbounded
        Python TypeError from inside `_build_tree` — must instead fail
        closed the same way as the other direction.
        """
        with tempfile.TemporaryDirectory() as workdir:
            base = _base_files({'system/a.md': 'shipped\n'})
            root, target_dir, base_sha, current_sha, target_sha = _diverging_repos(
                workdir, base, {'workspace/x/y.md': 'descendant\n'}, {'workspace/x': 'a file now\n'})
            plan, digest = _confirm(root, target_dir, target_sha)
            self.assertEqual((), plan.conflict)
            before_head = _run(['git', '-C', root, 'rev-parse', 'HEAD']).stdout.strip()

            result = _do_apply(root, target_dir, target_sha, plan, digest)

            after_head = _run(['git', '-C', root, 'rev-parse', 'HEAD']).stdout.strip()
            self.assertFalse(result.mutation_started)
            self.assertEqual('candidate_path_conflict', result.failure)
            self.assertEqual(before_head, after_head)
            self.assertEqual('descendant\n', Path(root, 'workspace', 'x', 'y.md').read_text())
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


def _directory_to_file_repos(workdir, extra_base=None):
    """A `system/x/y.md` descendant at C, replaced at T by a plain file
    `system/x` — a legal Git directory-to-file transition that
    `_diverging_repos`' plain dict-of-files helpers cannot express
    directly (writing a file at a path that is still a live directory
    on disk raises `IsADirectoryError` in the test fixture itself).
    """
    base = _base_files({'system/x/y.md': 'descendant\n', **(extra_base or {})})
    root, target_dir, base_sha, current_sha, target_sha = _diverging_repos(workdir, base, {}, {})
    Path(target_dir, 'system', 'x', 'y.md').unlink()
    Path(target_dir, 'system', 'x').rmdir()
    Path(target_dir, 'system', 'x').write_text('now a file\n')
    _run(['git', '-C', target_dir, 'add', '-A'])
    target_sha = _commit(target_dir, 'directory to file')
    return root, target_dir, base_sha, current_sha, target_sha


def _file_to_directory_repos(workdir, extra_base=None):
    """The reverse shape: a plain file `system/x` at C, replaced at T by
    a descendant `system/x/y.md`.
    """
    base = _base_files({'system/x': 'a file\n', **(extra_base or {})})
    root, target_dir, base_sha, current_sha, target_sha = _diverging_repos(workdir, base, {}, {})
    Path(target_dir, 'system', 'x').unlink()
    Path(target_dir, 'system', 'x').mkdir()
    Path(target_dir, 'system', 'x', 'y.md').write_text('descendant\n')
    _run(['git', '-C', target_dir, 'add', '-A'])
    target_sha = _commit(target_dir, 'file to directory')
    return root, target_dir, base_sha, current_sha, target_sha


class ApplyDirectoryFileTransitionTests(unittest.TestCase):
    def test_directory_to_file_transition_applies_successfully(self):
        with tempfile.TemporaryDirectory() as workdir:
            root, target_dir, base_sha, current_sha, target_sha = _directory_to_file_repos(workdir)
            plan, digest = _confirm(root, target_dir, target_sha)
            self.assertEqual((), plan.conflict)

            result = _do_apply(root, target_dir, target_sha, plan, digest)

            self.assertTrue(result.mutation_started)
            self.assertIsNotNone(result.commit)
            x_path = Path(root, 'system', 'x')
            self.assertTrue(x_path.is_file())
            self.assertEqual('now a file\n', x_path.read_text())
            write_tree = _run(['git', '-C', root, 'write-tree']).stdout.strip()
            head_tree = _run(['git', '-C', root, 'rev-parse', 'HEAD^{tree}']).stdout.strip()
            self.assertEqual(head_tree, write_tree)
            status = _run(['git', '-C', root, 'status', '--porcelain']).stdout
            self.assertEqual('', status.strip())

    def test_file_to_directory_transition_applies_successfully(self):
        with tempfile.TemporaryDirectory() as workdir:
            root, target_dir, base_sha, current_sha, target_sha = _file_to_directory_repos(workdir)
            plan, digest = _confirm(root, target_dir, target_sha)
            self.assertEqual((), plan.conflict)

            result = _do_apply(root, target_dir, target_sha, plan, digest)

            self.assertTrue(result.mutation_started)
            self.assertIsNotNone(result.commit)
            y_path = Path(root, 'system', 'x', 'y.md')
            self.assertTrue(y_path.is_file())
            self.assertEqual('descendant\n', y_path.read_text())
            status = _run(['git', '-C', root, 'status', '--porcelain']).stdout
            self.assertEqual('', status.strip())

    def test_directory_to_file_failure_recovers_exactly(self):
        with tempfile.TemporaryDirectory() as workdir:
            root, target_dir, base_sha, current_sha, target_sha = _directory_to_file_repos(workdir)
            plan, digest = _confirm(root, target_dir, target_sha)

            def fail():
                raise git_update._SimulatedFailure()

            result = _do_apply(root, target_dir, target_sha, plan, digest, _after_mutation=fail)

            self.assertTrue(result.rollback_attempted)
            self.assertTrue(result.rollback_completed)
            after_head = _run(['git', '-C', root, 'rev-parse', 'HEAD']).stdout.strip()
            self.assertEqual(current_sha, after_head)
            self.assertEqual('descendant\n', Path(root, 'system', 'x', 'y.md').read_text())
            status = _run(['git', '-C', root, 'status', '--porcelain']).stdout
            self.assertEqual('', status.strip())

    def test_file_to_directory_failure_recovers_exactly(self):
        with tempfile.TemporaryDirectory() as workdir:
            root, target_dir, base_sha, current_sha, target_sha = _file_to_directory_repos(workdir)
            plan, digest = _confirm(root, target_dir, target_sha)

            def fail():
                raise git_update._SimulatedFailure()

            result = _do_apply(root, target_dir, target_sha, plan, digest, _after_mutation=fail)

            self.assertTrue(result.rollback_attempted)
            self.assertTrue(result.rollback_completed)
            after_head = _run(['git', '-C', root, 'rev-parse', 'HEAD']).stdout.strip()
            self.assertEqual(current_sha, after_head)
            x_path = Path(root, 'system', 'x')
            self.assertTrue(x_path.is_file())
            self.assertEqual('a file\n', x_path.read_text())
            status = _run(['git', '-C', root, 'status', '--porcelain']).stdout
            self.assertEqual('', status.strip())


class ApplyFinalRecheckAndPerPathConcurrencyTests(unittest.TestCase):
    def test_candidate_helper_safety_recheck_catches_staleness_during_validation_window(self):
        """The early `_candidate_attribute_unsafe` check runs before
        validation and is genuinely safe at that moment. Simulate the
        live repository's `.git/info/attributes` and matching driver
        config appearing DURING the validation-to-mutation window (the
        TOCTOU the early check alone cannot close) and require the FINAL
        recheck to catch it before any live write.
        """
        with tempfile.TemporaryDirectory() as workdir:
            base = _base_files({'system/a.md': 'shipped\n'})
            root, target_dir, base_sha, current_sha, target_sha = _diverging_repos(
                workdir, base, {}, {'system/new.secret': 'sensitive\n'})
            plan, digest = _confirm(root, target_dir, target_sha)
            sentinel = str(Path(workdir, 'filter_sentinel'))
            hostile = str(Path(workdir, 'hostile.sh'))
            Path(hostile).write_text(f'#!/bin/sh\ntouch {sentinel}\ncat\n')
            os.chmod(hostile, 0o755)

            def make_stale():
                Path(root, '.git', 'info', 'attributes').write_text('*.secret filter=redact\n')
                _run(['git', '-C', root, 'config', 'filter.redact.clean', hostile])

            before_head = _run(['git', '-C', root, 'rev-parse', 'HEAD']).stdout.strip()

            result = _do_apply(root, target_dir, target_sha, plan, digest, _before_recheck=make_stale)

            after_head = _run(['git', '-C', root, 'rev-parse', 'HEAD']).stdout.strip()
            self.assertFalse(result.mutation_started)
            self.assertTrue(result.concurrent_change)
            self.assertEqual(before_head, after_head)
            self.assertFalse(Path(root, 'system', 'new.secret').exists())
            self.assertFalse(Path(sentinel).exists())

    def test_external_change_to_a_later_path_during_mutation_is_never_overwritten(self):
        """Two upstream_only paths; path 1 is written normally, then,
        immediately before path 2's own turn, an external process
        changes path 2's live content. The per-path concurrency check
        must catch this — a single check at the top of `apply()` cannot,
        since path 1's own write takes real time.
        """
        with tempfile.TemporaryDirectory() as workdir:
            base = _base_files({'system/a.md': 'shipped\n', 'system/b.md': 'shipped b\n'})
            root, target_dir, base_sha, current_sha, target_sha = _diverging_repos(
                workdir, base, {}, {'system/a.md': 'shipped v2\n', 'system/b.md': 'shipped b v2\n'})
            plan, digest = _confirm(root, target_dir, target_sha)
            self.assertEqual(('system/a.md', 'system/b.md'), plan.upstream_only)

            def tamper_before_path(path):
                if path == 'system/b.md':
                    Path(root, 'system', 'b.md').write_text('externally changed\n')

            result = _do_apply(
                root, target_dir, target_sha, plan, digest, _before_path=tamper_before_path)

            self.assertTrue(result.mutation_started)
            self.assertTrue(result.concurrent_change)
            self.assertTrue(result.rollback_attempted)
            # path 2's external change is never overwritten either way.
            self.assertEqual('externally changed\n', Path(root, 'system', 'b.md').read_text())
            # path 1 (safe, untouched externally) is recovered exactly.
            self.assertEqual('shipped\n', Path(root, 'system', 'a.md').read_text())


class ApplyFinalIntegrityGateTests(unittest.TestCase):
    def test_post_mutation_worktree_tamper_without_raising_never_succeeds(self):
        """`_after_mutation` tampers with a touched live path but returns
        normally (no exception) — the final integrity gate, not an
        exception, must be what catches this before the ref ever
        advances.
        """
        with tempfile.TemporaryDirectory() as workdir:
            base = _base_files({'system/a.md': 'shipped\n'})
            root, target_dir, base_sha, current_sha, target_sha = _diverging_repos(
                workdir, base, {}, {'system/a.md': 'shipped v2\n'})
            plan, digest = _confirm(root, target_dir, target_sha)

            def tamper_worktree_no_raise():
                Path(root, 'system', 'a.md').write_text('externally changed after mutation\n')

            result = _do_apply(
                root, target_dir, target_sha, plan, digest, _after_mutation=tamper_worktree_no_raise)

            self.assertIsNone(result.commit)
            after_head = _run(['git', '-C', root, 'rev-parse', 'HEAD']).stdout.strip()
            self.assertEqual(current_sha, after_head)
            self.assertTrue(result.concurrent_change)
            self.assertTrue(result.rollback_attempted)
            self.assertFalse(result.rollback_completed)
            # The external content is never overwritten.
            self.assertEqual('externally changed after mutation\n', Path(root, 'system', 'a.md').read_text())

    def test_post_mutation_index_tamper_without_raising_never_succeeds(self):
        """`_after_mutation` re-stages a touched path against a different
        real blob (the index, not the worktree file) and returns
        normally — must be caught the same way.
        """
        with tempfile.TemporaryDirectory() as workdir:
            base = _base_files({'system/a.md': 'shipped\n'})
            root, target_dir, base_sha, current_sha, target_sha = _diverging_repos(
                workdir, base, {}, {'system/a.md': 'shipped v2\n'})
            plan, digest = _confirm(root, target_dir, target_sha)

            def tamper_index_no_raise():
                other = subprocess.run(
                    ['git', '-C', root, 'hash-object', '-w', '--stdin'],
                    input='different content\n', capture_output=True, text=True, check=True)
                other_sha = other.stdout.strip()
                _run(['git', '-C', root, 'update-index', '--add', '--cacheinfo',
                      f'100644,{other_sha},system/a.md'])

            result = _do_apply(
                root, target_dir, target_sha, plan, digest, _after_mutation=tamper_index_no_raise)

            self.assertIsNone(result.commit)
            after_head = _run(['git', '-C', root, 'rev-parse', 'HEAD']).stdout.strip()
            self.assertEqual(current_sha, after_head)
            self.assertTrue(result.concurrent_change)
            self.assertTrue(result.rollback_attempted)
            self.assertFalse(result.rollback_completed)

    def test_untouched_tracked_path_changed_during_mutation_window_never_succeeds(self):
        with tempfile.TemporaryDirectory() as workdir:
            base = _base_files({'system/a.md': 'shipped\n', 'system/untouched.md': 'leave me\n'})
            root, target_dir, base_sha, current_sha, target_sha = _diverging_repos(
                workdir, base, {}, {'system/a.md': 'shipped v2\n'})
            plan, digest = _confirm(root, target_dir, target_sha)
            self.assertEqual(('system/a.md',), plan.upstream_only)

            def tamper_untouched():
                Path(root, 'system', 'untouched.md').write_text('changed by someone else\n')

            result = _do_apply(
                root, target_dir, target_sha, plan, digest, _after_mutation=tamper_untouched)

            self.assertIsNone(result.commit)
            after_head = _run(['git', '-C', root, 'rev-parse', 'HEAD']).stdout.strip()
            self.assertEqual(current_sha, after_head)
            self.assertTrue(result.concurrent_change)
            self.assertFalse(result.rollback_completed)
            self.assertEqual('changed by someone else\n', Path(root, 'system', 'untouched.md').read_text())

    def test_untracked_path_created_during_mutation_window_never_succeeds(self):
        with tempfile.TemporaryDirectory() as workdir:
            base = _base_files({'system/a.md': 'shipped\n'})
            root, target_dir, base_sha, current_sha, target_sha = _diverging_repos(
                workdir, base, {}, {'system/a.md': 'shipped v2\n'})
            plan, digest = _confirm(root, target_dir, target_sha)

            def create_untracked():
                Path(root, 'system', 'surprise.md').write_text('new untracked file\n')

            result = _do_apply(
                root, target_dir, target_sha, plan, digest, _after_mutation=create_untracked)

            self.assertIsNone(result.commit)
            after_head = _run(['git', '-C', root, 'rev-parse', 'HEAD']).stdout.strip()
            self.assertEqual(current_sha, after_head)
            self.assertTrue(result.concurrent_change)
            self.assertFalse(result.rollback_completed)
            # Never deleted/reset; the surprise file is left exactly as-is.
            self.assertTrue(Path(root, 'system', 'surprise.md').exists())


    def test_rename_detection_cannot_hide_an_externally_deleted_untouched_path(self):
        """A touched (new, upstream_only) path and an untouched tracked
        path with IDENTICAL content let Git's own rename detection
        present "delete untouched.md, create touched.md" as a SINGLE
        porcelain-v2 type-2 rename record whose reported current path
        is the touched one — the untouched path's deletion would be
        completely invisible to a parser that only reports the current
        path and skips origPath. The final integrity gate must not be
        fooled by this.
        """
        with tempfile.TemporaryDirectory() as workdir:
            base = _base_files({'system/untouched.md': 'same content\n'})
            root, target_dir, base_sha, current_sha, target_sha = _diverging_repos(
                workdir, base, {}, {'system/touched.md': 'same content\n'})
            _run(['git', '-C', root, 'config', 'status.renames', 'true'])
            plan, digest = _confirm(root, target_dir, target_sha)
            self.assertEqual(('system/touched.md',), plan.upstream_only)

            def delete_untouched_externally():
                # Sanity-check the fixture itself actually produces a
                # type-2 rename record with the touched path as current
                # and the untouched path as origPath, before relying on
                # apply() to handle it correctly.
                before = subprocess.run(
                    ['git', '-C', root, 'status', '--porcelain=v2', '-z'],
                    capture_output=True, text=True).stdout
                assert before.startswith('1 A. '), before  # touched.md freshly staged, not yet a rename pair

                Path(root, 'system', 'untouched.md').unlink()
                _run(['git', '-C', root, 'rm', '-q', '--cached', 'system/untouched.md'])

                after = subprocess.run(
                    ['git', '-C', root, 'status', '--porcelain=v2', '-z'],
                    capture_output=True, text=True).stdout
                assert after.startswith('2 R'), after
                assert 'system/touched.md' in after and 'system/untouched.md' in after, after

                # The exact command _post_mutation_integrity_ok issues
                # must never reduce this to a single type-2 record, no
                # matter the repository's own status.renames setting.
                no_renames = subprocess.run(
                    ['git', '-C', root, '--no-optional-locks', 'status', '--porcelain=v2', '-z',
                     '--no-renames', '--untracked-files=all'],
                    capture_output=True, text=True).stdout
                assert not any(chunk.startswith('2 ') for chunk in no_renames.split('\0') if chunk), no_renames
                assert 'system/untouched.md' in no_renames, no_renames

            result = _do_apply(
                root, target_dir, target_sha, plan, digest,
                _after_mutation=delete_untouched_externally)

            self.assertIsNone(result.commit)
            after_head = _run(['git', '-C', root, 'rev-parse', 'HEAD']).stdout.strip()
            self.assertEqual(current_sha, after_head)
            self.assertTrue(result.concurrent_change)
            self.assertTrue(result.rollback_attempted)
            self.assertFalse(result.rollback_completed)
            # The external deletion is never undone by the updater.
            self.assertFalse(Path(root, 'system', 'untouched.md').exists())


if __name__ == '__main__':
    unittest.main()
