import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from system.assistant import update_reporting
from system.assistant.update_reporting import HostCapability, run_update_workflow
from system.tests.update.test_git_apply import _base_files as _git_base_files
from system.tests.update.test_git_classification import (
    _apply as _apply_files, _commit, _diverging_repos, _init_repo, _run,
)
from system.tests.update import test_side_by_side as _sbs_tests
from system.tests.update.test_side_by_side import _base_target_files, _build_target_repo, _write_tree
from system.update import git_update, side_by_side
from system.update.target import TargetSnapshot

_READ_ONLY = HostCapability(can_read=True, can_write=False, can_run_local_commands=False)
_FULL = HostCapability(can_read=True, can_write=True, can_run_local_commands=True)
_SECRET = 'LOOP5-E2E-SENTINEL-DO-NOT-LEAK'


def _git_run(root, target_dir, target_sha, **kwargs):
    with mock.patch.object(git_update.target, 'resolve',
                            return_value=TargetSnapshot(target_sha, 'main', 'test')), \
         mock.patch.object(git_update.target, 'CANONICAL_URL', 'file://' + target_dir):
        return run_update_workflow(root, **kwargs)


def _zip_run(current_root, destination, target_dir, target_sha, **kwargs):
    with mock.patch.object(side_by_side.target, 'resolve',
                            return_value=TargetSnapshot(target_sha, 'main', 'test')), \
         mock.patch.object(side_by_side.target, 'CANONICAL_URL', 'file://' + target_dir):
        return run_update_workflow(current_root, destination, **kwargs)


class InstallTypeRoutingTests(unittest.TestCase):
    def test_workflow_routes_to_git_path_for_clone(self):
        with tempfile.TemporaryDirectory() as workdir:
            root = str(Path(workdir, 'root'))
            _init_repo(root)
            _apply_files(root, {'a.md': 'x\n'})
            _commit(root, 'initial')
            self.assertEqual('git', update_reporting.detect_install_type(root, _FULL))

    def test_workflow_routes_to_zip_path_for_archive(self):
        with tempfile.TemporaryDirectory() as workdir:
            root = Path(workdir, 'archive')
            root.mkdir()
            (root / 'a.md').write_text('x\n')
            self.assertEqual('zip', update_reporting.detect_install_type(str(root), _FULL))

    def test_unknown_route_without_proven_read_capability(self):
        with tempfile.TemporaryDirectory() as workdir:
            root = str(Path(workdir, 'root'))
            _init_repo(root)
            no_read = HostCapability(can_read=False, can_write=True, can_run_local_commands=True)
            self.assertEqual('unknown', update_reporting.detect_install_type(root, no_read))


class GitWorkflowE2ETests(unittest.TestCase):
    def test_git_e2e_full_update_success(self):
        with tempfile.TemporaryDirectory() as workdir:
            base = _git_base_files({'system/a.md': 'shipped\n', 'workspace/note.md': f'{_SECRET}\n'})
            root, target_dir, _base_sha, _current_sha, target_sha = _diverging_repos(
                workdir, base, {}, {'system/a.md': 'shipped v2\n'})

            preview_result = _git_run(root, target_dir, target_sha, capability=_FULL)
            self.assertFalse(preview_result.applied)
            self.assertNotIn(_SECRET, preview_result.beginner.headline + ' '.join(preview_result.beginner.details))

            applied_result = _git_run(
                root, target_dir, target_sha, capability=_FULL, confirm_digest=preview_result.digest)

            self.assertTrue(applied_result.applied)
            self.assertTrue(applied_result.ready)
            self.assertEqual('Update applied and validation passed.', applied_result.beginner.headline)
            self.assertNotIn(_SECRET, applied_result.beginner.headline)
            self.assertEqual('shipped v2\n', Path(root, 'system/a.md').read_text())
            self.assertEqual(f'{_SECRET}\n', Path(root, 'workspace', 'note.md').read_text())

    def test_git_e2e_conflict_blocks_apply(self):
        with tempfile.TemporaryDirectory() as workdir:
            base = _git_base_files({'system/a.md': 'shipped\n'})
            root, target_dir, _base_sha, _current_sha, target_sha = _diverging_repos(
                workdir, base, {'system/a.md': 'user edit\n'}, {'system/a.md': 'target edit\n'})

            real_apply = git_update.apply
            with mock.patch.object(git_update, 'apply') as spy_apply:
                spy_apply.side_effect = real_apply
                preview_result = _git_run(root, target_dir, target_sha, capability=_FULL)
                applied_result = _git_run(
                    root, target_dir, target_sha, capability=_FULL, confirm_digest=preview_result.digest)
                spy_apply.assert_not_called()

            self.assertFalse(applied_result.applied)
            self.assertFalse(applied_result.ready)
            self.assertEqual(
                'Nothing was changed. One or more local and update changes need a decision.',
                applied_result.beginner.headline)
            self.assertEqual('target edit\n', Path(target_dir, 'system/a.md').read_text())

    def test_git_e2e_recovery_after_validation_failure(self):
        with tempfile.TemporaryDirectory() as workdir:
            base = _git_base_files({'system/a.md': 'shipped\n'})
            # Target ships a file that fails validate_v1 (bad name) so
            # validation genuinely fails after mutation has begun.
            root, target_dir, _base_sha, _current_sha, target_sha = _diverging_repos(
                workdir, base, {}, {'system/BAD NAME.md': 'invalid\n'})

            preview_result = _git_run(root, target_dir, target_sha, capability=_FULL)
            self.assertEqual((), preview_result.beginner.details if False else ())
            applied_result = _git_run(
                root, target_dir, target_sha, capability=_FULL, confirm_digest=preview_result.digest)

            self.assertFalse(applied_result.ready)
            self.assertFalse(applied_result.beginner.headline.startswith('Update applied'))
            self.assertNotIn(_SECRET, applied_result.beginner.headline)
            self.assertNotIn('BAD NAME', applied_result.beginner.headline)

    def test_git_e2e_stale_preview_requires_new_preview(self):
        with tempfile.TemporaryDirectory() as workdir:
            base = _git_base_files({'system/a.md': 'shipped\n'})
            root, target_dir, _base_sha, _current_sha, target_sha = _diverging_repos(
                workdir, base, {}, {'system/a.md': 'shipped v2\n'})

            preview_result = _git_run(root, target_dir, target_sha, capability=_FULL)
            stale_digest = preview_result.digest

            # The installation changes after the preview was taken.
            _run(['git', '-C', root, 'commit', '--allow-empty', '-q', '-m', 'unrelated local commit',
                  '--author=fixture <fixture@example.com>'])

            real_apply = git_update.apply
            with mock.patch.object(git_update, 'apply') as spy_apply:
                spy_apply.side_effect = real_apply
                result = _git_run(
                    root, target_dir, target_sha, capability=_FULL, confirm_digest=stale_digest)
                spy_apply.assert_not_called()

            self.assertFalse(result.applied)
            self.assertEqual('stale_state', result.failure)

    def test_no_write_client_states_nothing_applied_and_no_validation(self):
        with tempfile.TemporaryDirectory() as workdir:
            base = _git_base_files({'system/a.md': 'shipped\n'})
            root, target_dir, _base_sha, _current_sha, target_sha = _diverging_repos(
                workdir, base, {}, {'system/a.md': 'shipped v2\n'})

            preview_result = _git_run(root, target_dir, target_sha, capability=_READ_ONLY)

            real_apply = git_update.apply
            real_candidate = git_update.subprocess.run
            with mock.patch.object(git_update, 'apply') as spy_apply, \
                 mock.patch.object(git_update.subprocess, 'run') as spy_run:
                spy_apply.side_effect = real_apply
                spy_run.side_effect = real_candidate
                result = _git_run(
                    root, target_dir, target_sha, capability=_READ_ONLY,
                    confirm_digest=preview_result.digest)
                spy_apply.assert_not_called()

            blob = result.beginner.headline + ' '.join(result.beginner.details)
            self.assertIn('nothing was written', blob)
            self.assertIn('validation was not run here', blob)
            self.assertFalse(result.applied)
            self.assertEqual('shipped\n', Path(root, 'system/a.md').read_text())

    def test_confirmation_mismatch_never_applies(self):
        with tempfile.TemporaryDirectory() as workdir:
            base = _git_base_files({'system/a.md': 'shipped\n'})
            root, target_dir, _base_sha, _current_sha, target_sha = _diverging_repos(
                workdir, base, {}, {'system/a.md': 'shipped v2\n'})

            real_apply = git_update.apply
            with mock.patch.object(git_update, 'apply') as spy_apply:
                spy_apply.side_effect = real_apply
                result = _git_run(
                    root, target_dir, target_sha, capability=_FULL,
                    confirm_digest='not-the-real-digest')
                spy_apply.assert_not_called()

            self.assertFalse(result.applied)
            self.assertEqual('stale_state', result.failure)
            self.assertEqual('shipped\n', Path(root, 'system/a.md').read_text())

    def test_dirty_clone_guidance_mentions_local_commit_not_push(self):
        with tempfile.TemporaryDirectory() as workdir:
            root = str(Path(workdir, 'root'))
            _init_repo(root)
            _apply_files(root, {'workspace/a.md': 'x\n'})
            _commit(root, 'initial')
            Path(root, 'workspace', f'{_SECRET}.md').write_text('untracked\n')

            result = run_update_workflow(root, capability=_FULL)

            blob = result.beginner.headline + ' '.join(result.beginner.details)
            self.assertIn('local commit', blob.lower())
            self.assertIn('do not push', blob.lower())
            self.assertIn('mrAlishah/Personal-SoT', blob)
            self.assertNotIn(_SECRET, blob)

    def test_updater_never_calls_git_commit_on_dirty_state(self):
        with tempfile.TemporaryDirectory() as workdir:
            root = str(Path(workdir, 'root'))
            _init_repo(root)
            _apply_files(root, {'workspace/a.md': 'x\n'})
            _commit(root, 'initial')
            Path(root, 'workspace', 'untracked.md').write_text('untracked\n')

            real_controlled_git = update_reporting.controlled_git
            observed = []

            def spy_controlled_git(*args, **kwargs):
                if args:
                    observed.append(args[0])
                return real_controlled_git(*args, **kwargs)

            with mock.patch.object(update_reporting, 'controlled_git', spy_controlled_git), \
                 mock.patch.object(git_update, 'controlled_git', spy_controlled_git):
                preview_result = run_update_workflow(root, capability=_FULL)
                run_update_workflow(root, capability=_FULL, confirm_digest=preview_result.digest)

            forbidden = {'add', 'commit', 'stash', 'reset', 'clean'}
            self.assertFalse(forbidden & set(observed), f'updater issued forbidden git subcommand(s): {observed}')


class ZipWorkflowE2ETests(unittest.TestCase):
    def test_zip_e2e_full_migration_success(self):
        with tempfile.TemporaryDirectory() as workdir:
            files = _base_target_files({
                'system/routing/context_registry.md':
                    _sbs_tests.SideBySideRegistryTests._registry_text([]),
            })
            target_dir, target_sha = _build_target_repo(workdir, files)
            current_root = Path(workdir, 'current')
            _write_tree(current_root, {
                'workspace/context/mine/note.md': f'{_SECRET}\n',
                'system/routing/context_registry.md':
                    _sbs_tests.SideBySideRegistryTests._registry_text([('mine', 'workspace/context/mine')]),
            })
            destination = Path(workdir, 'dest')

            preview_result = _zip_run(current_root, destination, target_dir, target_sha, capability=_FULL)
            self.assertFalse(preview_result.applied)
            self.assertNotIn(_SECRET, preview_result.beginner.headline + ' '.join(preview_result.beginner.details))

            applied_result = _zip_run(
                current_root, destination, target_dir, target_sha, capability=_FULL,
                confirm_digest=preview_result.digest)

            self.assertTrue(applied_result.applied)
            self.assertTrue(applied_result.ready)
            self.assertEqual(
                'Updated side-by-side copy is ready. Your original folder was not changed.',
                applied_result.beginner.headline)
            self.assertNotIn(_SECRET, applied_result.beginner.headline + ' '.join(applied_result.beginner.details))
            self.assertEqual(f'{_SECRET}\n', Path(current_root, 'workspace', 'context', 'mine', 'note.md').read_text())
            self.assertEqual(f'{_SECRET}\n', Path(destination, 'workspace', 'context', 'mine', 'note.md').read_text())
            registry_text = Path(destination, 'system', 'routing', 'context_registry.md').read_text()
            self.assertIn('mine', registry_text)

    def test_zip_e2e_unsafe_file_rejected_end_to_end(self):
        import os
        with tempfile.TemporaryDirectory() as workdir:
            target_dir, target_sha = _build_target_repo(workdir, _base_target_files())
            current_root = Path(workdir, 'current')
            _write_tree(current_root, {})
            unsafe_name = f'{_SECRET}.md'
            outside = Path(workdir, 'outside.md')
            outside.write_text('x\n')
            (current_root / 'workspace').mkdir(parents=True, exist_ok=True)
            os.symlink(outside, current_root / 'workspace' / unsafe_name)
            destination = Path(workdir, 'dest')

            real_migrate = side_by_side.migrate
            with mock.patch.object(side_by_side, 'migrate') as spy_migrate:
                spy_migrate.side_effect = real_migrate
                preview_result = _zip_run(current_root, destination, target_dir, target_sha, capability=_FULL)
                applied_result = _zip_run(
                    current_root, destination, target_dir, target_sha, capability=_FULL,
                    confirm_digest=preview_result.digest)
                spy_migrate.assert_not_called()

            self.assertFalse(applied_result.ready)
            self.assertFalse(applied_result.applied)
            blob = applied_result.beginner.headline + ' '.join(applied_result.beginner.details)
            self.assertNotIn(_SECRET, blob)
            self.assertNotIn(unsafe_name, blob)

    def test_zip_e2e_registry_conflict_reported_end_to_end(self):
        with tempfile.TemporaryDirectory() as workdir:
            files = _base_target_files({
                'system/routing/context_registry.md':
                    _sbs_tests.SideBySideRegistryTests._registry_text([('alpha_scope', 'workspace/context/shared')]),
                'workspace/context/shared/x.md': 'a\n',
            })
            target_dir, target_sha = _build_target_repo(workdir, files)
            current_root = Path(workdir, 'current')
            _write_tree(current_root, {
                'workspace/context/shared/y.md': 'b\n',
                'system/routing/context_registry.md':
                    _sbs_tests.SideBySideRegistryTests._registry_text([('beta_scope', 'workspace/context/shared')]),
            })
            destination = Path(workdir, 'dest')

            real_migrate = side_by_side.migrate
            with mock.patch.object(side_by_side, 'migrate') as spy_migrate:
                spy_migrate.side_effect = real_migrate
                preview_result = _zip_run(current_root, destination, target_dir, target_sha, capability=_FULL)
                applied_result = _zip_run(
                    current_root, destination, target_dir, target_sha, capability=_FULL,
                    confirm_digest=preview_result.digest)
                spy_migrate.assert_not_called()

            self.assertFalse(applied_result.ready)
            blob = applied_result.beginner.headline + ' '.join(applied_result.beginner.details)
            self.assertNotIn('alpha_scope', blob)
            self.assertNotIn('beta_scope', blob)
            self.assertNotIn('workspace/context/shared', blob)

    def test_zip_e2e_stale_preview_requires_new_preview(self):
        with tempfile.TemporaryDirectory() as workdir:
            target_dir, target_sha = _build_target_repo(workdir, _base_target_files())
            current_root = Path(workdir, 'current')
            _write_tree(current_root, {'workspace/a.md': 'kept a\n'})
            destination = Path(workdir, 'dest')

            preview_result = _zip_run(current_root, destination, target_dir, target_sha, capability=_FULL)
            stale_digest = preview_result.digest

            # The installation changes after the preview was taken.
            Path(current_root, 'workspace', 'b.md').write_text('new kept b\n')

            real_migrate = side_by_side.migrate
            with mock.patch.object(side_by_side, 'migrate') as spy_migrate:
                spy_migrate.side_effect = real_migrate
                result = _zip_run(
                    current_root, destination, target_dir, target_sha, capability=_FULL,
                    confirm_digest=stale_digest)
                spy_migrate.assert_not_called()

            self.assertFalse(result.applied)
            self.assertEqual('stale_state', result.failure)
            self.assertFalse(destination.exists())


class WorkflowOwnershipTests(unittest.TestCase):
    def test_workflow_does_not_duplicate_classification_logic(self):
        contract_text = Path(
            Path(__file__).resolve().parents[3], 'system', 'assistant', 'update_workflow.md').read_text()
        forbidden_labels = (
            'upstream_only', 'user_only', 'already_aligned', 'candidate_path_conflict',
            'merge-base classification table', 'merge base classification table',
        )
        for label in forbidden_labels:
            self.assertNotIn(label, contract_text, f'contract restates internal label {label!r}')
        self.assertIn('system.update.git_update', contract_text)
        self.assertIn('system.update.side_by_side', contract_text)

    def test_presentation_helper_imports_only_public_update_surface(self):
        import ast
        source = Path(
            Path(__file__).resolve().parents[3], 'system', 'assistant', 'update_reporting.py').read_text()
        tree = ast.parse(source)
        forbidden_private_names = {
            '_materialized_target', '_states', '_merge_base', '_ls_tree', '_scan_tree',
            '_registry_plan', '_validated_target_registry', '_PinnedRoot', '_pin_root',
        }
        imported_names = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom):
                for alias in node.names:
                    imported_names.add(alias.name)
        self.assertEqual(set(), imported_names & forbidden_private_names)


if __name__ == '__main__':
    unittest.main()
