import os
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest import mock

from system.update import git_update
from system.update.target import TargetSnapshot


def _run(args, cwd=None, check=True):
    return subprocess.run(args, cwd=cwd, capture_output=True, text=True, check=check)


def _init_repo(path, branch='main'):
    _run(['git', 'init', '-q', '-b', branch, path])
    _run(['git', '-C', path, 'config', 'user.email', 'fixture@example.com'])
    _run(['git', '-C', path, 'config', 'user.name', 'fixture'])


def _write(root, rel, content):
    path = Path(root, rel)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content)


def _apply(root, files):
    for rel, content in files.items():
        target_path = Path(root, rel)
        if content is None:
            if target_path.exists():
                target_path.unlink()
        else:
            _write(root, rel, content)


def _commit(root, message):
    _run(['git', '-C', root, 'add', '-A'])
    _run(['git', '-C', root, '-c', 'user.email=fixture@example.com', '-c', 'user.name=fixture',
          'commit', '-q', '--allow-empty', '-m', message])
    return _run(['git', '-C', root, 'rev-parse', 'HEAD']).stdout.strip()


def _diverging_repos(workdir, base_files, current_files, target_files):
    """A shared base commit, then current/target diverge into two separate
    repos (root, target_dir) so target really is absent from root's own
    object database, matching the real installed-clone/canonical split."""
    root = str(Path(workdir, 'root'))
    _init_repo(root)
    _apply(root, base_files)
    base_sha = _commit(root, 'base')

    _run(['git', '-C', root, 'checkout', '-q', '-b', 'current'])
    _apply(root, current_files)
    current_sha = _commit(root, 'current') if current_files else base_sha

    target_dir = str(Path(workdir, 'target'))
    _run(['git', 'clone', '-q', '--no-hardlinks', root, target_dir])
    _run(['git', '-C', target_dir, 'checkout', '-q', '-b', 'main', base_sha])
    _apply(target_dir, target_files)
    target_sha = _commit(target_dir, 'target') if target_files else base_sha

    return root, target_dir, base_sha, current_sha, target_sha


def _classify(root, target_dir, target_sha):
    with mock.patch.object(git_update.target, 'resolve',
                            return_value=TargetSnapshot(target_sha, 'main', 'test')), \
         mock.patch.object(git_update.target, 'CANONICAL_URL', 'file://' + target_dir):
        return git_update.classify(root)


class ClassificationTests(unittest.TestCase):
    def test_full_state_table_in_one_scenario(self):
        with tempfile.TemporaryDirectory() as workdir:
            root, target_dir, base_sha, current_sha, target_sha = _diverging_repos(
                workdir,
                base_files={
                    'unchanged.md': 'same everywhere\n',
                    'upstream_changes.md': 'base\n',
                    'user_changes.md': 'base\n',
                    'conflict.md': 'base\n',
                    'target_deletes_locally_modified.md': 'base\n',
                    'converge.md': 'base\n',
                },
                current_files={
                    'user_changes.md': 'user edit\n',
                    'user_created.md': 'brand new local file\n',
                    'conflict.md': 'current edit\n',
                    'target_deletes_locally_modified.md': 'current edit\n',
                    'converge.md': 'same final value\n',
                },
                target_files={
                    'upstream_changes.md': 'upstream edit\n',
                    'conflict.md': 'target edit\n',
                    'target_deletes_locally_modified.md': None,
                    'converge.md': 'same final value\n',
                },
            )
            plan = _classify(root, target_dir, target_sha)

        self.assertIsNone(plan.blocked)
        self.assertEqual(base_sha, plan.base)
        self.assertEqual(current_sha, plan.current)
        self.assertEqual(target_sha, plan.target)
        self.assertIn('unchanged.md', plan.already_aligned)
        self.assertIn('converge.md', plan.already_aligned)
        self.assertIn('upstream_changes.md', plan.upstream_only)
        self.assertIn('user_changes.md', plan.user_only)
        self.assertIn('user_created.md', plan.user_only)
        self.assertIn('conflict.md', plan.conflict)
        self.assertIn('target_deletes_locally_modified.md', plan.conflict)
        self.assertFalse(plan.no_op)

    def test_already_current_when_c_equals_t(self):
        with tempfile.TemporaryDirectory() as workdir:
            root, target_dir, base_sha, current_sha, target_sha = _diverging_repos(
                workdir, {'a.md': 'x\n'}, {}, {})
            # target has no divergent commit of its own: target_sha == base_sha == current_sha
            plan = _classify(root, target_dir, target_sha)
        self.assertIsNone(plan.blocked)
        self.assertEqual(plan.current, plan.target)
        self.assertTrue(plan.no_op)

    def test_no_op_when_t_is_ancestor_of_c(self):
        with tempfile.TemporaryDirectory() as workdir:
            root, target_dir, base_sha, current_sha, target_sha = _diverging_repos(
                workdir, {'a.md': 'x\n'}, {'a.md': 'local ahead\n'}, {})
            # target stayed at base; current moved ahead -> B == T, no downgrade
            plan = _classify(root, target_dir, target_sha)
        self.assertIsNone(plan.blocked)
        self.assertEqual(base_sha, plan.base)
        self.assertEqual(target_sha, plan.base)
        self.assertTrue(plan.no_op)
        self.assertEqual((), plan.upstream_only)
        self.assertIn('a.md', plan.user_only)

    def test_normal_update_when_diverged_with_valid_merge_base(self):
        with tempfile.TemporaryDirectory() as workdir:
            root, target_dir, base_sha, current_sha, target_sha = _diverging_repos(
                workdir, {'a.md': 'x\n'}, {'b.md': 'local\n'}, {'a.md': 'y\n'})
            plan = _classify(root, target_dir, target_sha)
        self.assertIsNone(plan.blocked)
        self.assertEqual(base_sha, plan.base)
        self.assertFalse(plan.no_op)
        self.assertIn('a.md', plan.upstream_only)
        self.assertIn('b.md', plan.user_only)

    def test_no_op_when_diverged_commits_converge_on_same_tree(self):
        """C and T are separate commits (different SHAs, both diverged from
        B) that independently reach byte-identical trees; no target-driven
        change remains, so this must be reported as no-op."""
        with tempfile.TemporaryDirectory() as workdir:
            root, target_dir, base_sha, current_sha, target_sha = _diverging_repos(
                workdir, {'a.md': 'base\n'}, {'a.md': 'converged\n'}, {'a.md': 'converged\n'})
            plan = _classify(root, target_dir, target_sha)
        self.assertIsNone(plan.blocked)
        self.assertNotEqual(current_sha, target_sha)
        self.assertTrue(plan.no_op)

    def test_no_op_when_target_commit_has_no_effective_tree_change(self):
        """T has a genuinely new commit (not == B), but that commit's tree
        is identical to B's; C carries only a preserved user-only change.
        The old `base == resolved.commit` ancestor check misses this."""
        with tempfile.TemporaryDirectory() as workdir:
            root, target_dir, base_sha, current_sha, target_sha = _diverging_repos(
                workdir, {'a.md': 'base\n'}, {'user_file.md': 'mine\n'}, {})
            _run(['git', '-C', target_dir, 'checkout', '-q', 'main'])
            new_target_sha = _commit(target_dir, 'no-op commit, same tree as base')
            self.assertNotEqual(target_sha, new_target_sha, 'fixture must add a genuinely new commit')
            plan = _classify(root, target_dir, new_target_sha)
        self.assertIsNone(plan.blocked)
        self.assertTrue(plan.no_op)
        self.assertEqual((), plan.upstream_only)
        self.assertIn('user_file.md', plan.user_only)

    def test_no_op_false_with_only_a_conflict(self):
        """Isolates the conflict-only branch: no upstream_only paths at
        all, so the old ancestor-based rule would have reported this as
        no-op too (base != resolved.commit, but nothing else checked
        conflict); the corrected rule must not."""
        with tempfile.TemporaryDirectory() as workdir:
            root, target_dir, base_sha, current_sha, target_sha = _diverging_repos(
                workdir, {'a.md': 'base\n'}, {'a.md': 'current edit\n'}, {'a.md': 'target edit\n'})
            plan = _classify(root, target_dir, target_sha)
        self.assertIsNone(plan.blocked)
        self.assertIn('a.md', plan.conflict)
        self.assertEqual((), plan.upstream_only)
        self.assertFalse(plan.no_op)

    def test_fails_closed_on_unrelated_lineage(self):
        with tempfile.TemporaryDirectory() as workdir:
            root = str(Path(workdir, 'root'))
            _init_repo(root)
            _write(root, 'a.md', 'root history\n')
            _commit(root, 'root')

            target_dir = str(Path(workdir, 'target'))
            _init_repo(target_dir, branch='main')
            _write(target_dir, 'a.md', 'unrelated history\n')
            target_sha = _commit(target_dir, 'unrelated')

            plan = _classify(root, target_dir, target_sha)
        self.assertEqual('unrelated_lineage', plan.blocked)

    def test_multiple_merge_bases_fail_closed(self):
        with tempfile.TemporaryDirectory() as workdir:
            root = str(Path(workdir, 'root'))
            _init_repo(root)
            _write(root, 'a.md', 'base\n')
            base_sha = _commit(root, 'base')

            # Classic criss-cross: two sibling commits c1/c2, then each side
            # merges the OTHER side's pre-merge tip, so neither c1 nor c2
            # dominates the other and both are valid merge bases of m1/m2.
            _run(['git', '-C', root, 'checkout', '-q', '-b', 'branch_a'])
            _write(root, 'from_a.md', 'from a\n')
            c1 = _commit(root, 'a')

            _run(['git', '-C', root, 'checkout', '-q', 'main'])
            _run(['git', '-C', root, 'checkout', '-q', '-b', 'branch_b'])
            _write(root, 'from_b.md', 'from b\n')
            c2 = _commit(root, 'b')

            _run(['git', '-C', root, 'checkout', '-q', 'branch_a'])
            _run(['git', '-C', root, '-c', 'user.email=fixture@example.com', '-c', 'user.name=fixture',
                  'merge', '-q', '--no-ff', '-m', 'm1', 'branch_b'])
            current_sha = _run(['git', '-C', root, 'rev-parse', 'HEAD']).stdout.strip()

            _run(['git', '-C', root, 'checkout', '-q', 'branch_b'])
            _run(['git', '-C', root, '-c', 'user.email=fixture@example.com', '-c', 'user.name=fixture',
                  'merge', '-q', '--no-ff', '-m', 'm2', c1])
            target_local_sha = _run(['git', '-C', root, 'rev-parse', 'HEAD']).stdout.strip()

            bases = _run(['git', '-C', root, 'merge-base', '--all', current_sha, target_local_sha]).stdout.split()
            if len(bases) < 2:
                self.skipTest('fixture did not produce a criss-cross history on this Git version')

            _run(['git', '-C', root, 'checkout', '-q', 'branch_a'])
            target_dir = str(Path(workdir, 'target'))
            _run(['git', 'clone', '-q', '--no-hardlinks', root, target_dir])
            _run(['git', '-C', target_dir, 'checkout', '-q', '-b', 'main', target_local_sha])

            plan = _classify(root, target_dir, target_local_sha)
        self.assertEqual('ambiguous_lineage', plan.blocked)


class DirtyPreflightTests(unittest.TestCase):
    def test_dirty_worktree_blocks_before_classification(self):
        with tempfile.TemporaryDirectory() as workdir:
            root = str(Path(workdir, 'root'))
            _init_repo(root)
            _write(root, 'a.md', 'x\n')
            _commit(root, 'base')
            _write(root, 'a.md', 'dirty\n')
            plan = git_update.classify(root)
        self.assertEqual('dirty_or_untracked', plan.blocked)

    def test_dirty_index_blocks(self):
        with tempfile.TemporaryDirectory() as workdir:
            root = str(Path(workdir, 'root'))
            _init_repo(root)
            _write(root, 'a.md', 'x\n')
            _commit(root, 'base')
            _write(root, 'a.md', 'staged change\n')
            _run(['git', '-C', root, 'add', 'a.md'])
            plan = git_update.classify(root)
        self.assertEqual('dirty_or_untracked', plan.blocked)

    def test_untracked_path_blocks_before_classification(self):
        with tempfile.TemporaryDirectory() as workdir:
            root = str(Path(workdir, 'root'))
            _init_repo(root)
            _write(root, 'a.md', 'x\n')
            _commit(root, 'base')
            _write(root, 'untracked.md', 'new\n')
            plan = git_update.classify(root)
        self.assertEqual('dirty_or_untracked', plan.blocked)

    def test_dirty_result_reports_area_and_count_not_paths(self):
        with tempfile.TemporaryDirectory() as workdir:
            root = str(Path(workdir, 'root'))
            _init_repo(root)
            _write(root, 'workspace/context/personal/secret_project.md', 'x\n')
            _commit(root, 'base')
            _write(root, 'workspace/context/personal/secret_project.md', 'dirty\n')
            plan = git_update.classify(root)
        self.assertEqual('dirty_or_untracked', plan.blocked)
        self.assertNotIn('secret_project', repr(plan))
        self.assertNotIn('workspace/context/personal/secret_project.md', repr(plan))

    def test_dirty_preflight_blocks_when_filter_is_configured(self):
        with tempfile.TemporaryDirectory() as workdir:
            root = str(Path(workdir, 'root'))
            _init_repo(root)
            _write(root, '.gitattributes', '*.secret filter=redact\n')
            _write(root, 'a.secret', 'sensitive\n')
            _commit(root, 'base')
            _run(['git', '-C', root, 'config', 'filter.redact.clean', 'cat'])
            plan = git_update.classify(root)
        self.assertEqual('unsafe_repository_state', plan.blocked)

    def test_configured_but_unreferenced_filter_does_not_block(self):
        """A driver with a clean/smudge command exists in config, but no
        tracked path's attributes actually select it: no path would ever
        trigger it, so the preflight must not over-block on config alone."""
        with tempfile.TemporaryDirectory() as workdir:
            root = str(Path(workdir, 'root'))
            _init_repo(root)
            _write(root, 'a.md', 'plain\n')
            _commit(root, 'base')
            _run(['git', '-C', root, 'config', 'filter.unused.clean', 'cat'])
            blocked = git_update._preflight(root)
        self.assertIsNone(blocked)

    def test_dirty_preflight_detects_nested_gitattributes(self):
        with tempfile.TemporaryDirectory() as workdir:
            root = str(Path(workdir, 'root'))
            _init_repo(root)
            _write(root, 'nested/dir/.gitattributes', '*.secret filter=redact\n')
            _write(root, 'nested/dir/a.secret', 'sensitive\n')
            _commit(root, 'base')
            _run(['git', '-C', root, 'config', 'filter.redact.clean', 'cat'])
            plan = git_update.classify(root)
        self.assertEqual('unsafe_repository_state', plan.blocked)

    def test_dotted_filter_driver_name_is_detected(self):
        """A driver subsection name may itself contain dots (git flattens
        [filter "foo.bar"] to the config key filter.foo.bar.clean); the
        detector must not assume a single dot-free segment between the
        namespace and the known suffix."""
        with tempfile.TemporaryDirectory() as workdir:
            root = str(Path(workdir, 'root'))
            sentinel = str(Path(workdir, 'sentinel'))
            _init_repo(root)
            _write(root, '.gitattributes', '*.secret filter=foo.bar\n')
            _write(root, 'a.secret', 'sensitive\n')
            _commit(root, 'base')
            hostile = str(Path(workdir, 'hostile.sh'))
            Path(hostile).write_text(f'#!/bin/sh\ntouch {sentinel}\ncat\n')
            os.chmod(hostile, 0o755)
            _run(['git', '-C', root, 'config', 'filter.foo.bar.clean', hostile])
            plan = git_update.classify(root)
        self.assertEqual('unsafe_repository_state', plan.blocked)
        self.assertFalse(Path(sentinel).exists())

    def test_dotted_diff_driver_name_is_detected(self):
        with tempfile.TemporaryDirectory() as workdir:
            root = str(Path(workdir, 'root'))
            sentinel = str(Path(workdir, 'sentinel'))
            _init_repo(root)
            _write(root, '.gitattributes', '*.secret diff=foo.bar\n')
            _write(root, 'a.secret', 'sensitive\n')
            _commit(root, 'base')
            hostile = str(Path(workdir, 'hostile.sh'))
            Path(hostile).write_text(f'#!/bin/sh\ntouch {sentinel}\ncat\n')
            os.chmod(hostile, 0o755)
            _run(['git', '-C', root, 'config', 'diff.foo.bar.textconv', hostile])
            plan = git_update.classify(root)
        self.assertEqual('unsafe_repository_state', plan.blocked)
        self.assertFalse(Path(sentinel).exists())

    def test_dirty_preflight_never_invokes_configured_helper(self):
        with tempfile.TemporaryDirectory() as workdir:
            root = str(Path(workdir, 'root'))
            sentinel = str(Path(workdir, 'sentinel'))
            _init_repo(root)
            _write(root, '.gitattributes', '*.secret filter=redact\n')
            _write(root, 'a.secret', 'sensitive\n')
            _commit(root, 'base')
            hostile = str(Path(workdir, 'hostile.sh'))
            Path(hostile).write_text(f'#!/bin/sh\ntouch {sentinel}\ncat\n')
            os.chmod(hostile, 0o755)
            _run(['git', '-C', root, 'config', 'filter.redact.clean', hostile])
            git_update.classify(root)
        self.assertFalse(Path(sentinel).exists())

    def test_attribute_scan_disables_fsmonitor_for_unreferenced_driver(self):
        """A configured-but-unreferenced driver makes `configured` non-empty,
        so the attribute scan proceeds past its early `if not configured`
        return into `ls-files`/`check-attr` — both of which must run with
        fsmonitor disabled, or a repository-configured `core.fsmonitor` hook
        executes before the hardened `status` call is ever reached."""
        with tempfile.TemporaryDirectory() as workdir:
            root = str(Path(workdir, 'root'))
            sentinel = str(Path(workdir, 'fsmonitor_sentinel'))
            _init_repo(root)
            _write(root, 'a.md', 'plain\n')
            _commit(root, 'base')
            _run(['git', '-C', root, 'config', 'filter.unused.clean', 'cat'])
            hostile_fsmonitor = str(Path(workdir, 'fsmonitor.sh'))
            Path(hostile_fsmonitor).write_text(
                f'#!/bin/sh\ntouch {sentinel}\nprintf "1\\n"\n')
            os.chmod(hostile_fsmonitor, 0o755)
            _run(['git', '-C', root, 'config', 'core.fsmonitor', hostile_fsmonitor])
            before = Path(root, '.git', 'index').read_bytes()
            blocked = git_update._preflight(root)
            after = Path(root, '.git', 'index').read_bytes()
            # Assert before the TemporaryDirectory is cleaned up: checking
            # sentinel existence after the `with` block exits would always
            # read False (the whole directory, sentinel included, is gone
            # by then) regardless of whether it was ever actually created.
            self.assertIsNone(blocked)
            self.assertFalse(Path(sentinel).exists())
            self.assertEqual(before, after)

    def test_attribute_scan_disables_fsmonitor_with_selected_driver(self):
        with tempfile.TemporaryDirectory() as workdir:
            root = str(Path(workdir, 'root'))
            fsmonitor_sentinel = str(Path(workdir, 'fsmonitor_sentinel'))
            filter_sentinel = str(Path(workdir, 'filter_sentinel'))
            _init_repo(root)
            _write(root, '.gitattributes', '*.secret filter=redact\n')
            _write(root, 'a.secret', 'sensitive\n')
            _commit(root, 'base')
            hostile_filter = str(Path(workdir, 'filter.sh'))
            Path(hostile_filter).write_text(f'#!/bin/sh\ntouch {filter_sentinel}\ncat\n')
            os.chmod(hostile_filter, 0o755)
            _run(['git', '-C', root, 'config', 'filter.redact.clean', hostile_filter])
            hostile_fsmonitor = str(Path(workdir, 'fsmonitor.sh'))
            Path(hostile_fsmonitor).write_text(
                f'#!/bin/sh\ntouch {fsmonitor_sentinel}\nprintf "1\\n"\n')
            os.chmod(hostile_fsmonitor, 0o755)
            _run(['git', '-C', root, 'config', 'core.fsmonitor', hostile_fsmonitor])
            plan = git_update.classify(root)
            # See the sibling test above: these must run before the
            # TemporaryDirectory is cleaned up.
            self.assertEqual('unsafe_repository_state', plan.blocked)
            self.assertFalse(Path(fsmonitor_sentinel).exists())
            self.assertFalse(Path(filter_sentinel).exists())

    def test_dirty_preflight_runs_with_no_optional_locks_and_fsmonitor_disabled(self):
        captured = []
        real_controlled_git = git_update.controlled_git

        def spy(*args, **kwargs):
            captured.append(args)
            return real_controlled_git(*args, **kwargs)

        with tempfile.TemporaryDirectory() as workdir:
            root = str(Path(workdir, 'root'))
            _init_repo(root)
            _write(root, 'a.md', 'x\n')
            _commit(root, 'base')
            with mock.patch.object(git_update, 'controlled_git', spy):
                git_update._preflight(root)
        status_calls = [call for call in captured if 'status' in call]
        self.assertTrue(status_calls)
        self.assertIn('--no-optional-locks', status_calls[0])
        self.assertIn('core.fsmonitor=false', status_calls[0])

    def test_index_bytes_unchanged_by_clean_preflight(self):
        with tempfile.TemporaryDirectory() as workdir:
            root = str(Path(workdir, 'root'))
            _init_repo(root)
            _write(root, 'a.md', 'x\n')
            _commit(root, 'base')
            before = Path(root, '.git', 'index').read_bytes()
            git_update._preflight(root)
            after = Path(root, '.git', 'index').read_bytes()
        self.assertEqual(before, after)

    def test_index_bytes_unchanged_by_blocked_preflight(self):
        with tempfile.TemporaryDirectory() as workdir:
            root = str(Path(workdir, 'root'))
            _init_repo(root)
            _write(root, 'a.md', 'x\n')
            _commit(root, 'base')
            _write(root, 'a.md', 'dirty\n')
            before = Path(root, '.git', 'index').read_bytes()
            plan = git_update.classify(root)
            after = Path(root, '.git', 'index').read_bytes()
        self.assertEqual('dirty_or_untracked', plan.blocked)
        self.assertEqual(before, after)

    def test_modified_worktree_file_reports_area_and_count(self):
        with tempfile.TemporaryDirectory() as workdir:
            root = str(Path(workdir, 'root'))
            _init_repo(root)
            _write(root, 'workspace/a.md', 'x\n')
            _commit(root, 'base')
            _write(root, 'workspace/a.md', 'dirty\n')
            plan = git_update.classify(root)
        self.assertEqual('dirty_or_untracked', plan.blocked)
        self.assertEqual((('workspace', 1),), plan.blocked_by_area)

    def test_staged_file_reports_area_and_count(self):
        with tempfile.TemporaryDirectory() as workdir:
            root = str(Path(workdir, 'root'))
            _init_repo(root)
            _write(root, 'workspace/a.md', 'x\n')
            _commit(root, 'base')
            _write(root, 'workspace/a.md', 'staged\n')
            _run(['git', '-C', root, 'add', 'workspace/a.md'])
            plan = git_update.classify(root)
        self.assertEqual('dirty_or_untracked', plan.blocked)
        self.assertEqual((('workspace', 1),), plan.blocked_by_area)

    def test_untracked_file_reports_area_and_count(self):
        with tempfile.TemporaryDirectory() as workdir:
            root = str(Path(workdir, 'root'))
            _init_repo(root)
            _write(root, 'a.md', 'x\n')
            _commit(root, 'base')
            _write(root, 'untracked.md', 'new\n')
            plan = git_update.classify(root)
        self.assertEqual('dirty_or_untracked', plan.blocked)
        self.assertEqual((('root', 1),), plan.blocked_by_area)

    def test_two_dirty_files_in_same_area_aggregate_count(self):
        with tempfile.TemporaryDirectory() as workdir:
            root = str(Path(workdir, 'root'))
            _init_repo(root)
            _write(root, 'workspace/a.md', 'x\n')
            _write(root, 'workspace/b.md', 'y\n')
            _commit(root, 'base')
            _write(root, 'workspace/a.md', 'dirty a\n')
            _write(root, 'workspace/b.md', 'dirty b\n')
            plan = git_update.classify(root)
        self.assertEqual('dirty_or_untracked', plan.blocked)
        self.assertEqual((('workspace', 2),), plan.blocked_by_area)

    def test_blocked_root_filename_does_not_leak(self):
        with tempfile.TemporaryDirectory() as workdir:
            root = str(Path(workdir, 'root'))
            _init_repo(root)
            _write(root, 'a.md', 'x\n')
            _commit(root, 'base')
            _write(root, 'super_secret_root_file.md', 'personal\n')
            plan = git_update.classify(root)
            result = git_update.preview(plan)
        self.assertNotIn('super_secret_root_file.md', repr(plan))
        self.assertNotIn('super_secret_root_file.md', repr(result))
        self.assertEqual((('root', 1),), plan.blocked_by_area)

    def test_blocked_arbitrary_top_level_directory_does_not_leak(self):
        with tempfile.TemporaryDirectory() as workdir:
            root = str(Path(workdir, 'root'))
            _init_repo(root)
            _write(root, 'a.md', 'x\n')
            _commit(root, 'base')
            _write(root, 'private_project/secret.md', 'personal\n')
            plan = git_update.classify(root)
        self.assertNotIn('private_project', repr(plan))
        self.assertEqual((('other', 1),), plan.blocked_by_area)

    def test_blocked_workspace_direct_child_filename_does_not_leak(self):
        with tempfile.TemporaryDirectory() as workdir:
            root = str(Path(workdir, 'root'))
            _init_repo(root)
            _write(root, 'a.md', 'x\n')
            _commit(root, 'base')
            _write(root, 'workspace/private_notes.md', 'personal\n')
            plan = git_update.classify(root)
        self.assertNotIn('private_notes.md', repr(plan))
        self.assertEqual((('workspace', 1),), plan.blocked_by_area)

    def test_dirty_status_handles_paths_with_spaces(self):
        with tempfile.TemporaryDirectory() as workdir:
            root = str(Path(workdir, 'root'))
            _init_repo(root)
            _write(root, 'a.md', 'x\n')
            _commit(root, 'base')
            _write(root, 'a file with spaces.md', 'new\n')
            plan = git_update.classify(root)
        self.assertEqual('dirty_or_untracked', plan.blocked)
        self.assertEqual((('root', 1),), plan.blocked_by_area)


class TargetMaterializationTests(unittest.TestCase):
    def test_target_absent_locally_is_materialized(self):
        with tempfile.TemporaryDirectory() as workdir:
            root, target_dir, base_sha, current_sha, target_sha = _diverging_repos(
                workdir, {'a.md': 'x\n'}, {}, {'a.md': 'y\n'})
            root_objects = subprocess.run(
                ['git', '-C', root, 'cat-file', '-e', target_sha], capture_output=True)
            self.assertNotEqual(0, root_objects.returncode, 'fixture invalid: target already local')
            plan = _classify(root, target_dir, target_sha)
        self.assertIsNone(plan.blocked)
        self.assertEqual(target_sha, plan.target)

    def test_materialization_fetches_exact_canonical_main_not_a_local_remote(self):
        captured = []
        real_controlled_git = git_update.controlled_git

        def spy(*args, **kwargs):
            captured.append((args, kwargs.get('cwd')))
            return real_controlled_git(*args, **kwargs)

        with tempfile.TemporaryDirectory() as workdir:
            root, target_dir, base_sha, current_sha, target_sha = _diverging_repos(
                workdir, {'a.md': 'x\n'}, {}, {'a.md': 'y\n'})
            with mock.patch.object(git_update.target, 'resolve',
                                    return_value=TargetSnapshot(target_sha, 'main', 'test')), \
                 mock.patch.object(git_update.target, 'CANONICAL_URL', 'file://' + target_dir), \
                 mock.patch.object(git_update, 'controlled_git', spy):
                git_update.classify(root)
        fetch_calls = [args for args, _cwd in captured if 'fetch' in args]
        self.assertEqual(1, len(fetch_calls))
        self.assertIn('file://' + target_dir, fetch_calls[0])
        self.assertIn('refs/heads/main:refs/heads/_target', fetch_calls[0])
        remote_add_calls = [args for args, _cwd in captured if 'remote' in args and 'add' in args]
        self.assertEqual([], remote_add_calls)

    def test_fetched_main_must_equal_already_resolved_t(self):
        with tempfile.TemporaryDirectory() as workdir:
            root, target_dir, base_sha, current_sha, target_sha = _diverging_repos(
                workdir, {'a.md': 'x\n'}, {}, {'a.md': 'y\n'})
            wrong_sha = 'a' * 40
            with mock.patch.object(git_update.target, 'resolve',
                                    return_value=TargetSnapshot(wrong_sha, 'main', 'test')), \
                 mock.patch.object(git_update.target, 'CANONICAL_URL', 'file://' + target_dir):
                plan = git_update.classify(root)
        self.assertEqual('stale_target', plan.blocked)

    def test_materialization_does_not_modify_live_ref_index_worktree_or_objects(self):
        with tempfile.TemporaryDirectory() as workdir:
            root, target_dir, base_sha, current_sha, target_sha = _diverging_repos(
                workdir, {'a.md': 'x\n'}, {}, {'a.md': 'y\n'})
            before_head = Path(root, '.git', 'HEAD').read_bytes()
            before_index = Path(root, '.git', 'index').read_bytes()
            before_worktree = Path(root, 'a.md').read_bytes()
            before_objects = sorted(str(p) for p in Path(root, '.git', 'objects').rglob('*') if p.is_file())

            _classify(root, target_dir, target_sha)

            self.assertEqual(before_head, Path(root, '.git', 'HEAD').read_bytes())
            self.assertEqual(before_index, Path(root, '.git', 'index').read_bytes())
            self.assertEqual(before_worktree, Path(root, 'a.md').read_bytes())
            after_objects = sorted(str(p) for p in Path(root, '.git', 'objects').rglob('*') if p.is_file())
            self.assertEqual(before_objects, after_objects)

    def test_materialization_does_not_modify_live_state_on_stale_target(self):
        with tempfile.TemporaryDirectory() as workdir:
            root, target_dir, base_sha, current_sha, target_sha = _diverging_repos(
                workdir, {'a.md': 'x\n'}, {}, {'a.md': 'y\n'})
            before_head = Path(root, '.git', 'HEAD').read_bytes()
            before_index = Path(root, '.git', 'index').read_bytes()
            wrong_sha = 'b' * 40
            with mock.patch.object(git_update.target, 'resolve',
                                    return_value=TargetSnapshot(wrong_sha, 'main', 'test')), \
                 mock.patch.object(git_update.target, 'CANONICAL_URL', 'file://' + target_dir):
                plan = git_update.classify(root)
            self.assertEqual('stale_target', plan.blocked)
            self.assertEqual(before_head, Path(root, '.git', 'HEAD').read_bytes())
            self.assertEqual(before_index, Path(root, '.git', 'index').read_bytes())

    def test_alternate_object_access_attached_only_after_fetch_completes(self):
        captured = []
        real_controlled_git = git_update.controlled_git

        def spy(*args, **kwargs):
            captured.append((args, kwargs.get('extra_env')))
            return real_controlled_git(*args, **kwargs)

        with tempfile.TemporaryDirectory() as workdir:
            root, target_dir, base_sha, current_sha, target_sha = _diverging_repos(
                workdir, {'a.md': 'x\n'}, {}, {'a.md': 'y\n'})
            with mock.patch.object(git_update.target, 'resolve',
                                    return_value=TargetSnapshot(target_sha, 'main', 'test')), \
                 mock.patch.object(git_update.target, 'CANONICAL_URL', 'file://' + target_dir), \
                 mock.patch.object(git_update, 'controlled_git', spy):
                git_update.classify(root)

        fetch_index = next(i for i, (args, _env) in enumerate(captured) if 'fetch' in args)
        for args, env in captured[:fetch_index + 1]:
            self.assertNotIn('GIT_ALTERNATE_OBJECT_DIRECTORIES', env or {},
                              f'{args} must not have private-object visibility before/at fetch')
        alternate_calls = [(i, args) for i, (args, env) in enumerate(captured)
                            if env and 'GIT_ALTERNATE_OBJECT_DIRECTORIES' in env]
        self.assertTrue(alternate_calls)
        first_alternate_index = alternate_calls[0][0]
        self.assertGreater(first_alternate_index, fetch_index)
        for args, _env in captured[first_alternate_index:]:
            self.assertNotIn('file://' + target_dir, args)


class GitAuthorityHistoryTests(unittest.TestCase):
    def test_replace_refs_do_not_alter_classification(self):
        with tempfile.TemporaryDirectory() as workdir:
            root, target_dir, base_sha, current_sha, target_sha = _diverging_repos(
                workdir, {'a.md': 'x\n'}, {'b.md': 'local\n'}, {'a.md': 'y\n'})
            plan_before = _classify(root, target_dir, target_sha)

            fake_parent = _run(['git', '-C', root, 'commit-tree', '-m', 'fake',
                                 base_sha + '^{tree}']).stdout.strip()
            _run(['git', '-C', root, 'replace', current_sha, fake_parent])
            plan_after = _classify(root, target_dir, target_sha)

            _run(['git', '-C', root, 'replace', '-d', current_sha])

        self.assertEqual(plan_before.base, plan_after.base)
        self.assertEqual(plan_before.upstream_only, plan_after.upstream_only)
        self.assertEqual(plan_before.user_only, plan_after.user_only)


class PreviewTests(unittest.TestCase):
    def test_digest_binds_c_t_b_and_plan(self):
        plan_a = git_update.Plan('c' * 40, 't' * 40, 'b' * 40, upstream_only=('a.md',))
        plan_b = git_update.Plan('c' * 40, 't' * 40, 'b' * 40, upstream_only=('a.md', 'x.md'))
        self.assertNotEqual(git_update.preview(plan_a).digest, git_update.preview(plan_b).digest)

    def test_digest_changes_when_current_changes(self):
        plan_a = git_update.Plan('c' * 40, 't' * 40, 'b' * 40)
        plan_b = git_update.Plan('d' * 40, 't' * 40, 'b' * 40)
        self.assertNotEqual(git_update.preview(plan_a).digest, git_update.preview(plan_b).digest)

    def test_deterministic_serialization_same_plan_same_digest(self):
        plan = git_update.Plan('c' * 40, 't' * 40, 'b' * 40, upstream_only=('a.md', 'z.md'))
        self.assertEqual(git_update.preview(plan).digest, git_update.preview(plan).digest)

    def test_path_ordering_does_not_affect_digest(self):
        plan_sorted = git_update.Plan('c' * 40, 't' * 40, 'b' * 40, upstream_only=('a.md', 'z.md'))
        plan_unsorted = git_update.Plan('c' * 40, 't' * 40, 'b' * 40, upstream_only=('z.md', 'a.md'))
        self.assertEqual(git_update.preview(plan_sorted).digest, git_update.preview(plan_unsorted).digest)

    def test_blocked_area_count_changes_the_digest(self):
        plan_a = git_update.Plan('', '', None, blocked='dirty_or_untracked',
                                  blocked_by_area=(('root', 1),))
        plan_b = git_update.Plan('', '', None, blocked='dirty_or_untracked',
                                  blocked_by_area=(('root', 2),))
        self.assertNotEqual(git_update.preview(plan_a).digest, git_update.preview(plan_b).digest)

    def test_blocked_area_count_ordering_does_not_affect_digest(self):
        plan_sorted = git_update.Plan('', '', None, blocked='dirty_or_untracked',
                                       blocked_by_area=(('other', 1), ('workspace', 2)))
        plan_unsorted = git_update.Plan('', '', None, blocked='dirty_or_untracked',
                                         blocked_by_area=(('workspace', 2), ('other', 1)))
        self.assertEqual(git_update.preview(plan_sorted).digest, git_update.preview(plan_unsorted).digest)

    def test_no_raw_dirty_path_is_serialized_into_blocked_result(self):
        plan = git_update.Plan('', '', None, blocked='dirty_or_untracked',
                                blocked_by_area=(('workspace', 1),))
        result = git_update.preview(plan)
        self.assertNotIn('.md', result.digest)
        self.assertIsInstance(result.summary['blocked_by_area'], dict)
        self.assertEqual({'workspace': 1}, result.summary['blocked_by_area'])


class PrivacyTests(unittest.TestCase):
    def test_root_user_only_filename_never_appears_as_or_inside_an_area_label(self):
        with tempfile.TemporaryDirectory() as workdir:
            root, target_dir, base_sha, current_sha, target_sha = _diverging_repos(
                workdir, {}, {'secret_root_file.md': 'personal\n'}, {})
            plan = _classify(root, target_dir, target_sha)
        result = git_update.preview(plan)
        self.assertNotIn('secret_root_file.md', result.summary['named'])
        self.assertIn('secret_root_file.md', plan.user_only)
        self.assertNotIn('secret_root_file.md', repr(result.summary))
        self.assertEqual({'root': 1}, result.summary['hidden_by_area'])

    def test_workspace_nested_user_only_path_hidden_regardless_of_location(self):
        with tempfile.TemporaryDirectory() as workdir:
            root, target_dir, base_sha, current_sha, target_sha = _diverging_repos(
                workdir, {}, {'workspace/context/personal/secret.md': 'personal\n'}, {})
            plan = _classify(root, target_dir, target_sha)
        result = git_update.preview(plan)
        self.assertNotIn('workspace/context/personal/secret.md', result.summary['named'])
        self.assertNotIn('secret.md', repr(result.summary))
        self.assertNotIn('context', repr(result.summary))
        self.assertEqual({'workspace': 1}, result.summary['hidden_by_area'])

    def test_workspace_direct_child_filename_never_appears_as_or_inside_an_area_label(self):
        """A direct child of workspace/ (e.g. workspace/<filename>.md, no
        further nesting) must not have its own filename embedded in the
        area label; the closed vocabulary collapses it to 'workspace'."""
        with tempfile.TemporaryDirectory() as workdir:
            root, target_dir, base_sha, current_sha, target_sha = _diverging_repos(
                workdir, {}, {'workspace/private_notes.md': 'personal\n'}, {})
            plan = _classify(root, target_dir, target_sha)
        result = git_update.preview(plan)
        self.assertNotIn('private_notes.md', repr(result.summary))
        self.assertEqual({'workspace': 1}, result.summary['hidden_by_area'])

    def test_arbitrary_top_level_user_directory_does_not_become_an_area_label(self):
        """A user-created top-level directory name (not workspace/system/
        guides) must not itself become the area label; it collapses to the
        fixed 'other' bucket instead."""
        with tempfile.TemporaryDirectory() as workdir:
            root, target_dir, base_sha, current_sha, target_sha = _diverging_repos(
                workdir, {}, {'private_project/secret.md': 'personal\n'}, {})
            plan = _classify(root, target_dir, target_sha)
        result = git_update.preview(plan)
        self.assertNotIn('private_project', repr(result.summary))
        self.assertNotIn('secret.md', repr(result.summary))
        self.assertEqual({'other': 1}, result.summary['hidden_by_area'])

    def test_upstream_established_path_may_be_named(self):
        with tempfile.TemporaryDirectory() as workdir:
            root, target_dir, base_sha, current_sha, target_sha = _diverging_repos(
                workdir, {'system/readme.md': 'x\n'}, {}, {'system/readme.md': 'y\n'})
            plan = _classify(root, target_dir, target_sha)
        result = git_update.preview(plan)
        self.assertIn('system/readme.md', result.summary['named'])

    def test_no_file_contents_in_plan_or_preview(self):
        with tempfile.TemporaryDirectory() as workdir:
            root, target_dir, base_sha, current_sha, target_sha = _diverging_repos(
                workdir, {}, {'secret.md': 'DISTINCTIVE_PERSONAL_CONTENT_MARKER'}, {})
            plan = _classify(root, target_dir, target_sha)
            result = git_update.preview(plan)
        self.assertNotIn('DISTINCTIVE_PERSONAL_CONTENT_MARKER', repr(plan))
        self.assertNotIn('DISTINCTIVE_PERSONAL_CONTENT_MARKER', repr(result))
        self.assertNotIn('DISTINCTIVE_PERSONAL_CONTENT_MARKER', repr(result.summary))


if __name__ == '__main__':
    unittest.main()
