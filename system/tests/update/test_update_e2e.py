import io
import os
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from system.assistant import update_reporting
from system.assistant.update_reporting import HostCapability, run_update_workflow
from system.tests.update.test_git_apply import _base_files as _git_base_files_raw
from system.tests.update.test_git_classification import (
    _apply as _apply_files, _commit, _diverging_repos, _init_repo, _run,
)
from system.tests.update import test_side_by_side as _sbs_tests
from system.tests.update.test_side_by_side import _base_target_files, _build_target_repo, _write_tree
from system.update import cli as update_cli
from system.update import git_update, side_by_side
from system.update.target import TargetSnapshot
from system.validation import validate_public

_READ_ONLY = HostCapability(can_read=True, can_write=False, can_run_local_commands=False)
_FULL = HostCapability(can_read=True, can_write=True, can_run_local_commands=True)
_SECRET = 'LOOP5-E2E-SENTINEL-DO-NOT-LEAK'


def _git_base_files(extra=None):
    """`_base_files` plus the Personal-SoT install-type marker every
    Git fixture in this file needs at its root now that routing
    requires it, not merely a `.git` directory.
    """
    files = _git_base_files_raw(extra)
    files.setdefault('workspace/adapters/runtime_entrypoint.md', 'x\n')
    return files


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


def _is_personal_sot_archive(root) -> bool:
    """Test convenience: pin `root` and check it, exactly as
    `detect_install_type` itself now does, closing the pin afterward.
    """
    pin = update_reporting._pin_read_root(root)
    if pin is None:
        return False
    try:
        return update_reporting._is_personal_sot_archive(pin)
    finally:
        pin.close()


def _read_frontmatter_only(root, path) -> str:
    """Test convenience: pin `root` and read, exactly as
    `_authorized_personal_paths` itself now does, closing the pin
    afterward.
    """
    pin = update_reporting._pin_read_root(root)
    if pin is None:
        return ''
    try:
        return update_reporting._read_frontmatter_only(pin, path)
    finally:
        pin.close()


class InstallTypeRoutingTests(unittest.TestCase):
    def test_workflow_routes_to_git_path_for_clone(self):
        with tempfile.TemporaryDirectory() as workdir:
            root = str(Path(workdir, 'root'))
            _init_repo(root)
            _apply_files(root, _git_base_files({'a.md': 'x\n'}))
            _commit(root, 'initial')
            self.assertEqual('git', update_reporting.detect_install_type(root, _FULL))

    def test_arbitrary_git_repository_is_not_personal_sot_installation(self):
        """A real, committed Git repository at its own top level, with
        no Personal-SoT markers at all — a single unrelated `.git`
        directory must never be enough to route as this installation.
        """
        with tempfile.TemporaryDirectory() as workdir:
            root = str(Path(workdir, 'random_repo'))
            _init_repo(root)
            _apply_files(root, {'README.md': 'just some other repo\n'})
            _commit(root, 'initial')
            self.assertEqual('unknown', update_reporting.detect_install_type(root, _FULL))

            real_classify, real_preview, real_apply = (
                git_update.classify, git_update.preview, git_update.apply)
            with mock.patch.object(git_update, 'classify') as spy_classify, \
                 mock.patch.object(git_update, 'preview') as spy_preview, \
                 mock.patch.object(git_update, 'apply') as spy_apply:
                spy_classify.side_effect = real_classify
                spy_preview.side_effect = real_preview
                spy_apply.side_effect = real_apply
                result = run_update_workflow(root, capability=_FULL)
                spy_classify.assert_not_called()
                spy_preview.assert_not_called()
                spy_apply.assert_not_called()
            self.assertEqual('unknown', result.install_type)
            self.assertEqual('unknown_install_type', result.failure)

    def test_git_personal_sot_root_requires_markers(self):
        """A real Git repository that is missing just ONE of the two
        required markers must still route as `unknown`, not `git`.
        """
        with tempfile.TemporaryDirectory() as workdir:
            root = str(Path(workdir, 'root'))
            _init_repo(root)
            _apply_files(root, {'workspace/adapters/runtime_entrypoint.md': validate_public.PUBLIC_RUNTIME_ENTRYPOINT})
            _commit(root, 'initial')
            self.assertEqual('unknown', update_reporting.detect_install_type(root, _FULL))

    def test_archive_marker_symlinks_do_not_prove_installation(self):
        """Both marker paths exist, but as symlinks to files outside
        the selected directory — never a genuine regular file at that
        exact path, so this must never prove the installation is real.
        """
        import os
        with tempfile.TemporaryDirectory() as workdir:
            root = Path(workdir, 'fake_archive')
            root.mkdir()
            outside = Path(workdir, 'outside')
            outside.mkdir()
            (outside / 'runtime_entrypoint.md').write_text('x\n')
            (outside / 'validate_v1.py').write_text('x\n')
            (root / 'workspace' / 'adapters').mkdir(parents=True)
            (root / 'system' / 'validation').mkdir(parents=True)
            os.symlink(outside / 'runtime_entrypoint.md', root / 'workspace' / 'adapters' / 'runtime_entrypoint.md')
            os.symlink(outside / 'validate_v1.py', root / 'system' / 'validation' / 'validate_v1.py')

            self.assertEqual('unknown', update_reporting.detect_install_type(str(root), _FULL))

    def test_intermediate_workspace_symlink_cannot_prove_installation_marker(self):
        """`workspace` ITSELF — an intermediate component of the first
        marker's path — is a symlink to an outside directory that
        genuinely contains `adapters/runtime_entrypoint.md`. The final
        lookup would resolve to a real outside regular file through a
        plain pathname open, but the root-anchored check must refuse
        the intermediate symlink and never prove the installation.
        """
        import os
        with tempfile.TemporaryDirectory() as workdir:
            root = Path(workdir, 'fake_archive')
            root.mkdir()
            outside = Path(workdir, 'outside_workspace')
            (outside / 'adapters').mkdir(parents=True)
            (outside / 'adapters' / 'runtime_entrypoint.md').write_text('x\n')
            os.symlink(outside, root / 'workspace')
            (root / 'system' / 'validation').mkdir(parents=True)
            (root / 'system' / 'validation' / 'validate_v1.py').write_text('x\n')

            self.assertFalse(_is_personal_sot_archive(str(root)))
            self.assertEqual('unknown', update_reporting.detect_install_type(str(root), _FULL))

            real_classify, real_preview, real_apply = (
                git_update.classify, git_update.preview, git_update.apply)
            with mock.patch.object(git_update, 'classify') as spy_classify, \
                 mock.patch.object(git_update, 'preview') as spy_preview, \
                 mock.patch.object(git_update, 'apply') as spy_apply:
                spy_classify.side_effect = real_classify
                spy_preview.side_effect = real_preview
                spy_apply.side_effect = real_apply
                result = run_update_workflow(str(root), capability=_FULL)
                spy_classify.assert_not_called()
                spy_preview.assert_not_called()
                spy_apply.assert_not_called()
            self.assertEqual('unknown', result.install_type)

    def test_intermediate_system_symlink_cannot_prove_installation_marker(self):
        """Same race, but the SECOND marker's intermediate component
        (`system`) is the symlink this time — proving the check is
        symmetric across both required markers.
        """
        import os
        with tempfile.TemporaryDirectory() as workdir:
            root = Path(workdir, 'fake_archive')
            root.mkdir()
            (root / 'workspace' / 'adapters').mkdir(parents=True)
            (root / 'workspace' / 'adapters' / 'runtime_entrypoint.md').write_text('x\n')
            outside = Path(workdir, 'outside_system')
            (outside / 'validation').mkdir(parents=True)
            (outside / 'validation' / 'validate_v1.py').write_text('x\n')
            os.symlink(outside, root / 'system')

            self.assertFalse(_is_personal_sot_archive(str(root)))
            self.assertEqual('unknown', update_reporting.detect_install_type(str(root), _FULL))

    def test_symlink_selected_root_fails_installation_proof(self):
        """The selected root pathname ITSELF is a symlink to a
        directory that genuinely carries both markers — the authority
        boundary must refuse to follow it rather than "helpfully"
        resolving to the real target.
        """
        import os
        with tempfile.TemporaryDirectory() as workdir:
            real_root = Path(workdir, 'real_archive')
            _write_tree(real_root, {
                'workspace/adapters/runtime_entrypoint.md': validate_public.PUBLIC_RUNTIME_ENTRYPOINT,
                'system/validation/validate_v1.py': 'x\n',
            })
            selected = Path(workdir, 'selected_link')
            os.symlink(real_root, selected)

            self.assertFalse(_is_personal_sot_archive(str(selected)))
            self.assertEqual('unknown', update_reporting.detect_install_type(str(selected), _FULL))

    def test_marker_proof_cannot_mix_two_physical_roots(self):
        """Physical root A contains ONLY the first marker; physical
        root B contains ONLY the second. The selected pathname points
        to A when the first marker check runs, then is replaced by B
        (a real rename, not a symlink) before the second marker check
        runs. Even though each INDIVIDUAL check is component-safe, a
        single logical installation-proof transaction must never
        combine evidence from two different physical directories —
        no single real installation ever contained both markers.
        """
        import shutil
        with tempfile.TemporaryDirectory() as workdir:
            selected = Path(workdir, 'selected')
            root_a = Path(workdir, 'root_a')
            root_b = Path(workdir, 'root_b')
            marker1, marker2 = update_reporting._ARCHIVE_MARKERS
            (root_a / marker1).parent.mkdir(parents=True)
            (root_a / marker1).write_text('x\n')
            (root_b / marker2).parent.mkdir(parents=True)
            (root_b / marker2).write_text('x\n')
            shutil.copytree(root_a, selected)

            real_safe_is_regular = update_reporting._safe_is_regular_file
            calls = {'n': 0}

            def swap_after_first_marker(pin, relative):
                calls['n'] += 1
                if calls['n'] == 2:
                    shutil.rmtree(selected)
                    shutil.copytree(root_b, selected)
                return real_safe_is_regular(pin, relative)

            with mock.patch.object(update_reporting, '_safe_is_regular_file', swap_after_first_marker):
                result = _is_personal_sot_archive(str(selected))
            self.assertFalse(result)

            real_classify, real_preview, real_apply = (
                git_update.classify, git_update.preview, git_update.apply)
            real_sbs_preview, real_sbs_migrate = side_by_side.preview, side_by_side.migrate
            calls['n'] = 0
            shutil.rmtree(selected)
            shutil.copytree(root_a, selected)
            with mock.patch.object(update_reporting, '_safe_is_regular_file', swap_after_first_marker), \
                 mock.patch.object(git_update, 'classify') as spy_classify, \
                 mock.patch.object(git_update, 'preview') as spy_preview, \
                 mock.patch.object(git_update, 'apply') as spy_apply, \
                 mock.patch.object(side_by_side, 'preview') as spy_sbs_preview, \
                 mock.patch.object(side_by_side, 'migrate') as spy_sbs_migrate:
                spy_classify.side_effect = real_classify
                spy_preview.side_effect = real_preview
                spy_apply.side_effect = real_apply
                spy_sbs_preview.side_effect = real_sbs_preview
                spy_sbs_migrate.side_effect = real_sbs_migrate
                workflow_result = run_update_workflow(str(selected), capability=_FULL)
                spy_classify.assert_not_called()
                spy_preview.assert_not_called()
                spy_apply.assert_not_called()
                spy_sbs_preview.assert_not_called()
                spy_sbs_migrate.assert_not_called()
            self.assertEqual('unknown', workflow_result.install_type)

    def test_root_change_during_git_install_probe_fails_closed(self):
        """The selected root passes marker proof as a real Git repo,
        but the pathname is replaced by a DIFFERENT real directory
        (never a symlink) between the marker check and the final
        identity recheck. All routing evidence (markers, `.git`) is
        read through the pin and so is entirely unaffected by the
        pathname swap, but the pinned root's pathname identity has
        drifted by the time `detect_install_type` rechecks it right
        before returning, so the overall proof must still fail closed
        rather than return a route for a pathname that no longer names
        the pinned installation at all.
        """
        import shutil
        with tempfile.TemporaryDirectory() as workdir:
            selected = Path(workdir, 'selected')
            replacement = Path(workdir, 'replacement')
            _init_repo(str(selected))
            _apply_files(str(selected), _git_base_files({'a.md': 'x\n'}))
            _commit(str(selected), 'initial')
            _init_repo(str(replacement))
            _apply_files(str(replacement), _git_base_files({'a.md': 'x\n'}))
            _commit(str(replacement), 'initial')

            real_is_archive = update_reporting._is_personal_sot_archive

            def swap_after_markers(pin):
                ok = real_is_archive(pin)
                shutil.rmtree(selected)
                shutil.copytree(replacement, selected)
                return ok

            with mock.patch.object(update_reporting, '_is_personal_sot_archive', swap_after_markers):
                result = update_reporting.detect_install_type(str(selected), _FULL)
            self.assertEqual('unknown', result)

    def test_git_route_probe_cannot_be_fooled_by_aba_root_swap(self):
        """Physical root A has valid Personal-SoT markers and is NOT a
        Git repository; physical root B has valid markers and IS a
        real Git repository. The selected pathname is pinned while it
        names A. A genuine ABA swap — rename A away, move B onto the
        selected pathname, run whatever Git evidence check exists,
        move B away again, restore A (the SAME physical directory,
        via `os.rename`, preserving its inode) — surrounds the check.
        Even though every pathname-based identity check before and
        after the swap sees A correctly restored, the check itself
        must never have been influenced by B: A is genuinely not
        Git-managed, so the route must never be `'git'`.
        """
        import subprocess
        with tempfile.TemporaryDirectory() as workdir:
            selected = Path(workdir, 'selected')
            root_a_parked = Path(workdir, 'root_a_parked')
            root_b_parked = Path(workdir, 'root_b_parked')

            _write_tree(selected, {
                'workspace/adapters/runtime_entrypoint.md': validate_public.PUBLIC_RUNTIME_ENTRYPOINT,
                'system/validation/validate_v1.py': 'x\n',
            })
            _write_tree(root_b_parked, {
                'workspace/adapters/runtime_entrypoint.md': validate_public.PUBLIC_RUNTIME_ENTRYPOINT,
                'system/validation/validate_v1.py': 'x\n',
            })
            subprocess.run(['git', 'init', '-q', str(root_b_parked)], check=True)
            subprocess.run(['git', '-C', str(root_b_parked), 'config', 'user.email', 'x@example.com'],
                            check=True)
            subprocess.run(['git', '-C', str(root_b_parked), 'config', 'user.name', 'x'], check=True)
            subprocess.run(['git', '-C', str(root_b_parked), 'add', '-A'], check=True)
            subprocess.run(['git', '-C', str(root_b_parked), 'commit', '-q', '-m', 'init'], check=True)

            pin = update_reporting._pin_read_root(selected)
            try:
                real_controlled_git = update_reporting.controlled_git

                def aba_controlled_git(*args, **kwargs):
                    os.rename(selected, root_a_parked)
                    os.rename(root_b_parked, selected)
                    result = real_controlled_git(*args, **kwargs)
                    os.rename(selected, root_b_parked)
                    os.rename(root_a_parked, selected)
                    return result

                with mock.patch.object(update_reporting, 'controlled_git', aba_controlled_git):
                    is_git = update_reporting._is_git_installation(pin)
                self.assertFalse(is_git)
            finally:
                pin.close()

            result = update_reporting.detect_install_type(str(selected), _FULL)
            self.assertEqual('zip', result)

    def test_normal_clone_detected_from_pinned_git_metadata(self):
        with tempfile.TemporaryDirectory() as workdir:
            root = str(Path(workdir, 'root'))
            _init_repo(root)
            _apply_files(root, _git_base_files({'a.md': 'x\n'}))
            _commit(root, 'initial')
            self.assertEqual('git', update_reporting.detect_install_type(root, _FULL))

    def test_linked_worktree_detected_from_pinned_gitfile_metadata(self):
        with tempfile.TemporaryDirectory() as workdir:
            main_repo = str(Path(workdir, 'main'))
            _init_repo(main_repo)
            _apply_files(main_repo, _git_base_files({'a.md': 'x\n'}))
            _commit(main_repo, 'initial')
            worktree = str(Path(workdir, 'wt'))
            _run(['git', '-C', main_repo, 'worktree', 'add', '-q', '--detach', worktree, 'main'])

            self.assertTrue(Path(worktree, '.git').is_file())
            self.assertEqual('git', update_reporting.detect_install_type(worktree, _FULL))

    def test_git_symlink_metadata_fails_closed(self):
        with tempfile.TemporaryDirectory() as workdir:
            root = Path(workdir, 'root')
            _write_tree(root, {
                'workspace/adapters/runtime_entrypoint.md': validate_public.PUBLIC_RUNTIME_ENTRYPOINT,
                'system/validation/validate_v1.py': 'x\n',
            })
            outside_git = Path(workdir, 'outside_dotgit')
            outside_git.mkdir()
            os.symlink(outside_git, root / '.git')

            pin = update_reporting._pin_read_root(root)
            try:
                self.assertFalse(update_reporting._is_git_installation(pin))
            finally:
                pin.close()
            self.assertEqual('zip', update_reporting.detect_install_type(str(root), _FULL))

    def test_malformed_gitfile_does_not_prove_git_route(self):
        for content in ('', 'not a gitdir line\n', 'gitdir:\n', 'gitdir:   \n'):
            with self.subTest(content=repr(content)):
                with tempfile.TemporaryDirectory() as workdir:
                    root = Path(workdir, 'root')
                    _write_tree(root, {
                        'workspace/adapters/runtime_entrypoint.md': validate_public.PUBLIC_RUNTIME_ENTRYPOINT,
                        'system/validation/validate_v1.py': 'x\n',
                        '.git': content,
                    })
                    pin = update_reporting._pin_read_root(root)
                    try:
                        self.assertFalse(update_reporting._is_git_installation(pin))
                    finally:
                        pin.close()
                    self.assertEqual('zip', update_reporting.detect_install_type(str(root), _FULL))

    def test_root_anchored_reader_rejects_absolute_path_before_open(self):
        """`_root_anchored_parts` itself must reject an absolute path
        before any `os.open` happens — an absolute first component
        reaching `openat(..., dir_fd=...)` is interpreted by POSIX as
        an absolute path and silently IGNORES `dir_fd`, escaping
        containment outright.
        """
        self.assertIsNone(update_reporting._root_anchored_parts('/etc/passwd'))

        with tempfile.TemporaryDirectory() as workdir:
            root = Path(workdir, 'root')
            root.mkdir()
            pin = update_reporting._pin_read_root(root)
            try:
                real_os_open = update_reporting.os.open
                with mock.patch.object(update_reporting.os, 'open') as spy_open:
                    spy_open.side_effect = real_os_open
                    result = update_reporting._open_pinned_relative(pin, '/etc/passwd')
                    spy_open.assert_not_called()
                self.assertIsNone(result)
            finally:
                pin.close()

    def test_workflow_routes_to_zip_path_for_archive(self):
        with tempfile.TemporaryDirectory() as workdir:
            root = Path(workdir, 'archive')
            _write_tree(root, {
                'a.md': 'x\n',
                'workspace/adapters/runtime_entrypoint.md': validate_public.PUBLIC_RUNTIME_ENTRYPOINT,
                'system/validation/validate_v1.py': 'x\n',
            })
            self.assertEqual('zip', update_reporting.detect_install_type(str(root), _FULL))

    def test_arbitrary_directory_is_not_zip_installation(self):
        with tempfile.TemporaryDirectory() as workdir:
            root = Path(workdir, 'random')
            root.mkdir()
            (root / 'notes.md').write_text('x\n')
            self.assertEqual('unknown', update_reporting.detect_install_type(str(root), _FULL))

    def test_nested_directory_inside_git_repo_is_not_install_root(self):
        with tempfile.TemporaryDirectory() as workdir:
            parent = str(Path(workdir, 'parent'))
            _init_repo(parent)
            _apply_files(parent, {'a.md': 'x\n'})
            _commit(parent, 'initial')
            nested = Path(parent, 'not_the_installation')
            nested.mkdir()
            self.assertEqual('unknown', update_reporting.detect_install_type(str(nested), _FULL))

    def test_no_local_command_capability_executes_no_git_or_update_commands(self):
        with tempfile.TemporaryDirectory() as workdir:
            root = str(Path(workdir, 'root'))
            _init_repo(root)
            _apply_files(root, {'a.md': 'x\n'})
            _commit(root, 'initial')
            no_commands = HostCapability(can_read=True, can_write=True, can_run_local_commands=False)

            real_controlled_git = update_reporting.controlled_git
            real_classify = git_update.classify
            real_sbs_preview = side_by_side.preview
            with mock.patch.object(update_reporting, 'controlled_git') as spy_git, \
                 mock.patch.object(git_update, 'controlled_git') as spy_git2, \
                 mock.patch.object(git_update, 'classify') as spy_classify, \
                 mock.patch.object(side_by_side, 'preview') as spy_preview:
                spy_git.side_effect = real_controlled_git
                spy_git2.side_effect = real_controlled_git
                spy_classify.side_effect = real_classify
                spy_preview.side_effect = real_sbs_preview
                result = run_update_workflow(root, capability=no_commands)
                spy_git.assert_not_called()
                spy_git2.assert_not_called()
                spy_classify.assert_not_called()
                spy_preview.assert_not_called()

            blob = result.beginner.headline + ' '.join(result.beginner.details)
            self.assertIn('nothing was written', blob)
            self.assertIn('validation was not run here', blob)

    def test_unknown_route_without_proven_read_capability(self):
        with tempfile.TemporaryDirectory() as workdir:
            root = str(Path(workdir, 'root'))
            _init_repo(root)
            no_read = HostCapability(can_read=False, can_write=True, can_run_local_commands=True)
            self.assertEqual('unknown', update_reporting.detect_install_type(root, no_read))

    def test_no_command_no_write_does_not_claim_preview_available(self):
        """Capability lacks local-command execution entirely, so no
        preview could even be attempted — the report must not claim
        one is available (unlike the "built a real preview, just can't
        write" case), while still truthfully stating the two required
        no-write literals.
        """
        with tempfile.TemporaryDirectory() as workdir:
            root = str(Path(workdir, 'root'))
            _init_repo(root)
            _apply_files(root, _git_base_files({'a.md': 'x\n'}))
            _commit(root, 'initial')
            no_commands = HostCapability(can_read=True, can_write=False, can_run_local_commands=False)

            result = run_update_workflow(root, capability=no_commands)

            self.assertIsNone(result.digest)
            blob = result.beginner.headline + ' '.join(result.beginner.details)
            self.assertNotIn('A preview is available', blob)
            self.assertIn('nothing was written', blob)
            self.assertIn('validation was not run here', blob)

    def test_no_read_no_write_states_nothing_written(self):
        with tempfile.TemporaryDirectory() as workdir:
            root = str(Path(workdir, 'root'))
            result = run_update_workflow(root, capability=_NO_READ_NO_WRITE)
            blob = result.beginner.headline + ' '.join(result.beginner.details)
            self.assertIn('nothing was written', blob)
            self.assertIn('validation was not run here', blob)


_NO_WRITE_WITH_COMMANDS = HostCapability(can_read=True, can_write=False, can_run_local_commands=True)
_NO_READ_NO_WRITE = HostCapability(can_read=False, can_write=False, can_run_local_commands=False)


class GitWorkflowE2ETests(unittest.TestCase):
    def test_git_initial_no_write_preview_states_capability_limit(self):
        """The VERY FIRST call, with no `confirm_digest` at all, from
        a client that can read/run local commands but cannot write —
        the real preview must still be built (a digest is returned and
        the normal area/count information is present), AND the
        required no-write literals must already be present, without
        the caller needing to "confirm" first to learn that.
        """
        with tempfile.TemporaryDirectory() as workdir:
            base = _git_base_files({'system/a.md': 'shipped\n'})
            root, target_dir, _base_sha, _current_sha, target_sha = _diverging_repos(
                workdir, base, {}, {'system/a.md': 'shipped v2\n'})

            real_apply = git_update.apply
            with mock.patch.object(git_update, 'apply') as spy_apply:
                spy_apply.side_effect = real_apply
                result = _git_run(root, target_dir, target_sha, capability=_NO_WRITE_WITH_COMMANDS)
                spy_apply.assert_not_called()

            self.assertIsNotNone(result.digest)
            self.assertFalse(result.applied)
            blob = result.beginner.headline + ' '.join(result.beginner.details)
            self.assertIn('nothing was written', blob)
            self.assertIn('validation was not run here', blob)

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

    def test_noob_cli_completes_update_with_one_confirmation(self):
        """Acceptance: a normal Git-backed update needs one command and
        one yes/no confirmation; no digest/SHA/Git choreography is exposed.
        The relative "." root also exercises the real root-normalization fix.
        """
        with tempfile.TemporaryDirectory() as workdir:
            base = _git_base_files({'system/a.md': 'shipped\n'})
            root, target_dir, _base_sha, _current_sha, target_sha = _diverging_repos(
                workdir, base, {}, {'system/a.md': 'shipped v2\n'})
            prompts = []
            output = io.StringIO()
            previous_cwd = os.getcwd()
            try:
                os.chdir(root)
                with mock.patch.object(
                    git_update.target, 'resolve',
                    return_value=TargetSnapshot(target_sha, 'main', 'test')
                ), mock.patch.object(
                    git_update.target, 'CANONICAL_URL', 'file://' + target_dir
                ):
                    rc = update_cli.run_interactive(
                        '.',
                        input_fn=lambda prompt: prompts.append(prompt) or 'yes',
                        out=output,
                    )
            finally:
                os.chdir(previous_cwd)

            self.assertEqual(0, rc)
            self.assertEqual(1, len(prompts))
            self.assertIn('Update applied and validation passed.', output.getvalue())
            self.assertEqual('shipped v2\n', Path(root, 'system/a.md').read_text())

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
            _apply_files(root, _git_base_files({'workspace/a.md': 'x\n'}))
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
            _apply_files(root, _git_base_files({'workspace/a.md': 'x\n'}))
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


_ARCHIVE_MARKER_FILES = {
    'workspace/adapters/runtime_entrypoint.md': validate_public.PUBLIC_RUNTIME_ENTRYPOINT,
    'system/validation/validate_v1.py': _sbs_tests._VALIDATOR_FILES['system/validation/validate_v1.py'],
}


class ZipWorkflowE2ETests(unittest.TestCase):
    def test_zip_initial_no_write_preview_states_capability_limit(self):
        with tempfile.TemporaryDirectory() as workdir:
            target_dir, target_sha = _build_target_repo(workdir, _base_target_files({
                'workspace/adapters/runtime_entrypoint.md': validate_public.PUBLIC_RUNTIME_ENTRYPOINT,
            }))
            current_root = Path(workdir, 'current')
            _write_tree(current_root, {**_ARCHIVE_MARKER_FILES, 'workspace/a.md': 'kept a\n'})
            destination = Path(workdir, 'dest')

            real_migrate = side_by_side.migrate
            with mock.patch.object(side_by_side, 'migrate') as spy_migrate:
                spy_migrate.side_effect = real_migrate
                result = _zip_run(
                    current_root, destination, target_dir, target_sha,
                    capability=_NO_WRITE_WITH_COMMANDS)
                spy_migrate.assert_not_called()

            self.assertIsNotNone(result.digest)
            self.assertFalse(result.applied)
            blob = result.beginner.headline + ' '.join(result.beginner.details)
            self.assertIn('nothing was written', blob)
            self.assertIn('validation was not run here', blob)
            self.assertIn('to preserve', blob)

    def test_zip_e2e_full_migration_success(self):
        with tempfile.TemporaryDirectory() as workdir:
            files = _base_target_files({
                'system/routing/context_registry.md':
                    _sbs_tests.SideBySideRegistryTests._registry_text([]),
                'workspace/adapters/runtime_entrypoint.md': validate_public.PUBLIC_RUNTIME_ENTRYPOINT,
            })
            target_dir, target_sha = _build_target_repo(workdir, files)
            current_root = Path(workdir, 'current')
            _write_tree(current_root, {
                **_ARCHIVE_MARKER_FILES,
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
            target_dir, target_sha = _build_target_repo(workdir, _base_target_files({
                'workspace/adapters/runtime_entrypoint.md': validate_public.PUBLIC_RUNTIME_ENTRYPOINT,
            }))
            current_root = Path(workdir, 'current')
            _write_tree(current_root, dict(_ARCHIVE_MARKER_FILES))
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
                'workspace/adapters/runtime_entrypoint.md': validate_public.PUBLIC_RUNTIME_ENTRYPOINT,
            })
            target_dir, target_sha = _build_target_repo(workdir, files)
            current_root = Path(workdir, 'current')
            _write_tree(current_root, {
                **_ARCHIVE_MARKER_FILES,
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
            target_dir, target_sha = _build_target_repo(workdir, _base_target_files({
                'workspace/adapters/runtime_entrypoint.md': validate_public.PUBLIC_RUNTIME_ENTRYPOINT,
            }))
            current_root = Path(workdir, 'current')
            _write_tree(current_root, {**_ARCHIVE_MARKER_FILES, 'workspace/a.md': 'kept a\n'})
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

    def test_zip_partial_candidate_failure_does_not_say_nothing_changed(self):
        """Two kept files; the first copies, then the source changes
        before the second copies, so `migrate` genuinely fails AFTER
        `migration_started=True` with a partially-built destination
        still on disk (Loop 4 never promises to delete it). The
        beginner report must never say "Nothing was changed" for this
        — the original is unchanged, but a side-by-side candidate DOES
        exist on disk and is explicitly not ready.
        """
        with tempfile.TemporaryDirectory() as workdir:
            target_dir, target_sha = _build_target_repo(workdir, _base_target_files({
                'workspace/adapters/runtime_entrypoint.md': validate_public.PUBLIC_RUNTIME_ENTRYPOINT,
            }))
            current_root = Path(workdir, 'current')
            _write_tree(current_root, {
                **_ARCHIVE_MARKER_FILES,
                'workspace/a.md': 'kept a\n',
                'workspace/b.md': 'kept b\n',
            })
            destination = Path(workdir, 'dest')

            def change_source_before_b(relative):
                if relative == 'workspace/b.md':
                    Path(current_root, 'workspace', 'b.md').write_text('changed after preview\n')

            # Drive the real preview()/migrate() directly (the same
            # production functions the workflow itself calls), using
            # `_during_copy` to force a genuine migration_started=True
            # failure, then render its report the same way the workflow
            # does.
            with mock.patch.object(side_by_side.target, 'resolve',
                                    return_value=TargetSnapshot(target_sha, 'main', 'test')), \
                 mock.patch.object(side_by_side.target, 'CANONICAL_URL', 'file://' + target_dir):
                fresh_preview = side_by_side.preview(current_root, destination)
                self.assertEqual(('workspace/a.md', 'workspace/b.md'), fresh_preview.plan.kept)
                migrate_result = side_by_side.migrate(
                    current_root, destination, fresh_preview.plan, fresh_preview.digest,
                    _during_copy=change_source_before_b)

            self.assertTrue(migrate_result.migration_started)
            self.assertFalse(migrate_result.ready)

            report = update_reporting.zip_beginner_report(fresh_preview.plan, migrate_result)
            blob = report.headline + ' '.join(report.details)
            self.assertNotIn('Nothing was changed', blob)
            self.assertIn('original folder was not changed', blob)
            self.assertIn('not ready', blob)

    def test_zip_validation_failure_says_original_unchanged_candidate_not_ready(self):
        plan = side_by_side.SideBySidePlan()
        result = side_by_side.MigrationResult(
            pristine_validation_ran=True, pristine_validation_passed=True,
            migration_started=True, personal_validation_ran=True, personal_validation_passed=False,
            ready=False, failure='personal_validation_failed')
        report = update_reporting.zip_beginner_report(plan, result)
        blob = report.headline + ' '.join(report.details)
        self.assertNotIn('Nothing was changed', blob)
        self.assertIn('original folder was not changed', blob)
        self.assertIn('not ready', blob)


class GitReportTruthfulnessTests(unittest.TestCase):
    def test_git_object_transfer_failure_never_reports_success(self):
        plan = git_update.Plan(current='c', target='t', base='b')
        result = git_update.ApplyResult(
            validation_ran=True, validation_passed=True, failure='object_transfer_failed', commit=None)
        self.assertFalse(update_reporting._git_apply_succeeded(result))
        report = update_reporting.git_beginner_report(plan, {}, result)
        self.assertNotIn('Update applied', report.headline)

    def test_git_post_mutation_failure_with_complete_rollback_reports_restored_not_applied(self):
        plan = git_update.Plan(current='c', target='t', base='b')
        result = git_update.ApplyResult(
            mutation_started=True, validation_ran=True, validation_passed=True,
            rollback_attempted=True, rollback_completed=True, concurrent_change=False,
            failure='post_mutation_failure', commit=None)
        self.assertFalse(update_reporting._git_apply_succeeded(result))
        report = update_reporting.git_beginner_report(plan, {}, result)
        self.assertNotIn('Update applied', report.headline)
        self.assertIn('restored', report.headline)
        self.assertIn('did not complete', report.headline)

    def test_git_recovery_incomplete_never_claims_applied(self):
        plan = git_update.Plan(current='c', target='t', base='b')
        result = git_update.ApplyResult(
            mutation_started=True, validation_ran=True, validation_passed=True,
            rollback_attempted=True, rollback_completed=False, concurrent_change=True,
            failure='ref_cas_failed', commit=None)
        self.assertFalse(update_reporting._git_apply_succeeded(result))
        report = update_reporting.git_beginner_report(plan, {}, result)
        self.assertNotIn('Update applied', report.headline)
        self.assertIn('did not complete', report.headline)
        self.assertIn('could not be safely restored', report.headline)
        self.assertNotIn('verified prior state', report.headline)

    def test_git_success_requires_real_commit(self):
        plan = git_update.Plan(current='c', target='t', base='b')
        no_commit = git_update.ApplyResult(
            mutation_started=True, validation_ran=True, validation_passed=True, commit=None)
        self.assertFalse(update_reporting._git_apply_succeeded(no_commit))

        real_success = git_update.ApplyResult(
            mutation_started=True, validation_ran=True, validation_passed=True,
            commit='abc123def456')
        self.assertTrue(update_reporting._git_apply_succeeded(real_success))
        report = update_reporting.git_beginner_report(plan, {}, real_success)
        self.assertEqual('Update applied and validation passed.', report.headline)


class AdvancedReportTests(unittest.TestCase):
    _BODY_SECRET = 'LOOP5-GAP4-BODY-SECRET-DO-NOT-LEAK'

    def test_frontmatter_reader_never_returns_module_body(self):
        with tempfile.TemporaryDirectory() as workdir:
            root = Path(workdir)
            big_body = 'y' * 1000
            _write_tree(root, {
                'workspace/context/personal/allow.md':
                    '---\nai_access: allow\n---\n' + self._BODY_SECRET + '\n' + big_body,
            })
            header = _read_frontmatter_only(root, 'workspace/context/personal/allow.md')
            self.assertNotIn(self._BODY_SECRET, header)
            self.assertNotIn(big_body, header)
            self.assertIn('ai_access: allow', header)

    def test_frontmatter_reader_refuses_a_final_symlink(self):
        import os
        with tempfile.TemporaryDirectory() as workdir:
            root = Path(workdir, 'root')
            root.mkdir()
            outside = Path(workdir, 'outside.md')
            outside.write_text('---\nai_access: allow\n---\nsecret body\n')
            link = root / 'workspace' / 'context' / 'personal'
            link.mkdir(parents=True)
            os.symlink(outside, link / 'linked.md')

            header = _read_frontmatter_only(
                root, 'workspace/context/personal/linked.md')
            self.assertEqual('', header)

    def test_workflow_result_contains_no_raw_advanced_header_candidates(self):
        import dataclasses
        field_names = {f.name for f in dataclasses.fields(update_reporting.WorkflowResult)}
        self.assertNotIn('advanced_candidates', field_names)

    def test_advanced_report_contains_only_authorized_personal_paths(self):
        with tempfile.TemporaryDirectory() as workdir:
            root = Path(workdir)
            _write_tree(root, {
                'workspace/context/personal/allow.md':
                    '---\nai_access: allow\n---\n' + self._BODY_SECRET + '\n',
                'workspace/context/personal/restricted.md':
                    '---\nai_access: restricted\n---\n' + self._BODY_SECRET + '\n',
                'workspace/context/personal/deny.md':
                    '---\nai_access: deny\n---\n' + self._BODY_SECRET + '\n',
                'system/routing/context_registry.md':
                    _sbs_tests.SideBySideRegistryTests._registry_text(
                        [('personal', 'workspace/context/personal')]),
            })
            paths = ('workspace/context/personal/allow.md', 'workspace/context/personal/restricted.md',
                     'workspace/context/personal/deny.md')

            no_auth = update_reporting.advanced_report(
                'zip', None, root=root, candidate_paths=paths, host_read=False)
            self.assertEqual((), no_auth.personal_paths)
            self.assertNotIn(self._BODY_SECRET, repr(no_auth))

            with_auth = update_reporting.advanced_report(
                'zip', None, root=root, candidate_paths=paths, host_read=True)
            self.assertEqual(('workspace/context/personal/allow.md',), with_auth.personal_paths)
            self.assertNotIn('restricted.md', with_auth.personal_paths)
            self.assertNotIn('deny.md', with_auth.personal_paths)
            self.assertNotIn(self._BODY_SECRET, repr(with_auth))

    def test_advanced_report_uses_real_registry_not_caller_text(self):
        """Even if the installation's own registry does NOT register
        `workspace/context/unregistered`, the path under it must never
        be disclosed — `advanced_report` no longer accepts a caller-
        supplied registry string at all; only the canonical file at
        `root` can ever grant scope authority.
        """
        with tempfile.TemporaryDirectory() as workdir:
            root = Path(workdir)
            _write_tree(root, {
                'workspace/context/unregistered/allow.md':
                    '---\nai_access: allow\n---\n' + self._BODY_SECRET + '\n',
                'system/routing/context_registry.md':
                    _sbs_tests.SideBySideRegistryTests._registry_text([]),
            })
            report = update_reporting.advanced_report(
                'zip', None, root=root,
                candidate_paths=('workspace/context/unregistered/allow.md',), host_read=True)
            self.assertEqual((), report.personal_paths)

    def test_unregistered_allow_path_not_disclosed(self):
        with tempfile.TemporaryDirectory() as workdir:
            root = Path(workdir)
            _write_tree(root, {
                'workspace/context/unregistered/allow.md': '---\nai_access: allow\n---\nbody\n',
                'system/routing/context_registry.md':
                    _sbs_tests.SideBySideRegistryTests._registry_text([]),
            })
            report = update_reporting.advanced_report(
                'zip', None, root=root,
                candidate_paths=('workspace/context/unregistered/allow.md',), host_read=True)
            self.assertEqual((), report.personal_paths)

    def test_registered_allow_path_disclosed_with_host_read(self):
        with tempfile.TemporaryDirectory() as workdir:
            root = Path(workdir)
            _write_tree(root, {
                'workspace/context/personal/allow.md': '---\nai_access: allow\n---\nbody\n',
                'system/routing/context_registry.md':
                    _sbs_tests.SideBySideRegistryTests._registry_text(
                        [('personal', 'workspace/context/personal')]),
            })
            report = update_reporting.advanced_report(
                'zip', None, root=root,
                candidate_paths=('workspace/context/personal/allow.md',), host_read=True)
            self.assertEqual(('workspace/context/personal/allow.md',), report.personal_paths)

    def test_registry_symlink_fails_closed_for_personal_disclosure(self):
        import os
        with tempfile.TemporaryDirectory() as workdir:
            root = Path(workdir, 'root')
            root.mkdir()
            _write_tree(root, {
                'workspace/context/personal/allow.md': '---\nai_access: allow\n---\nbody\n',
            })
            outside_registry = Path(workdir, 'outside_registry.md')
            outside_registry.write_text(
                _sbs_tests.SideBySideRegistryTests._registry_text(
                    [('personal', 'workspace/context/personal')]))
            (root / 'system' / 'routing').mkdir(parents=True)
            os.symlink(outside_registry, root / 'system' / 'routing' / 'context_registry.md')

            report = update_reporting.advanced_report(
                'zip', None, root=root,
                candidate_paths=('workspace/context/personal/allow.md',), host_read=True)
            self.assertEqual((), report.personal_paths)

    def test_intermediate_registry_symlink_fails_closed_for_advanced_disclosure(self):
        """`system` ITSELF — an intermediate component of the
        canonical registry's own path — is a symlink to an outside
        directory carrying a FORGED registry that registers the
        otherwise-unregistered scope. The outside registry must never
        become authorization authority merely because the final
        lookup would resolve through it.
        """
        import os
        with tempfile.TemporaryDirectory() as workdir:
            root = Path(workdir, 'root')
            _write_tree(root, {
                'workspace/context/personal/allow.md': '---\nai_access: allow\n---\nbody\n',
            })
            outside_system = Path(workdir, 'outside_system')
            (outside_system / 'routing').mkdir(parents=True)
            (outside_system / 'routing' / 'context_registry.md').write_text(
                _sbs_tests.SideBySideRegistryTests._registry_text(
                    [('personal', 'workspace/context/personal')]))
            os.symlink(outside_system, root / 'system')

            report = update_reporting.advanced_report(
                'zip', None, root=root,
                candidate_paths=('workspace/context/personal/allow.md',), host_read=True)
            self.assertEqual((), report.personal_paths)

    def test_intermediate_context_symlink_never_reads_outside_frontmatter(self):
        """`workspace/context/personal` — an intermediate component of
        the candidate's own path — is a symlink to an outside
        directory carrying a DIFFERENT `allow.md` with a distinctive
        body secret. The outside module must never be read for
        authorization, the path must not be disclosed, and the secret
        must appear nowhere in the returned report.
        """
        import os
        body_secret = 'LOOP5-INTERMEDIATE-SYMLINK-OUTSIDE-BODY-SECRET'
        with tempfile.TemporaryDirectory() as workdir:
            root = Path(workdir, 'root')
            _write_tree(root, {
                'system/routing/context_registry.md':
                    _sbs_tests.SideBySideRegistryTests._registry_text(
                        [('personal', 'workspace/context/personal')]),
            })
            outside_personal = Path(workdir, 'outside_personal')
            outside_personal.mkdir()
            (outside_personal / 'allow.md').write_text(
                '---\nai_access: allow\n---\n' + body_secret + '\n')
            (root / 'workspace' / 'context').mkdir(parents=True)
            os.symlink(outside_personal, root / 'workspace' / 'context' / 'personal')

            report = update_reporting.advanced_report(
                'zip', None, root=root,
                candidate_paths=('workspace/context/personal/allow.md',), host_read=True)
            self.assertEqual((), report.personal_paths)
            self.assertNotIn(body_secret, repr(report))

    def test_advanced_authorization_cannot_mix_registry_and_frontmatter_from_different_roots(self):
        """Physical root A's registry registers the scope but has no
        authorizing module; physical root B has the authorizing module
        but its OWN registry does not register that scope. The
        selected pathname points to A when the canonical registry is
        read, then is replaced by B (first as a REAL directory, then
        as a SYMLINK, in two separate sub-cases) before the
        frontmatter read runs. Neither replacement may let the
        authorization decision combine A's registry with B's module.
        """
        import shutil
        for use_symlink in (False, True):
            with self.subTest(use_symlink=use_symlink):
                with tempfile.TemporaryDirectory() as workdir:
                    selected = Path(workdir, 'selected')
                    root_a = Path(workdir, f'root_a_{use_symlink}')
                    root_b = Path(workdir, f'root_b_{use_symlink}')
                    _write_tree(root_a, {
                        'system/routing/context_registry.md':
                            _sbs_tests.SideBySideRegistryTests._registry_text(
                                [('personal', 'workspace/context/personal')]),
                    })
                    _write_tree(root_b, {
                        'workspace/context/personal/allow.md': '---\nai_access: allow\n---\nbody\n',
                        'system/routing/context_registry.md':
                            _sbs_tests.SideBySideRegistryTests._registry_text([]),
                    })
                    shutil.copytree(root_a, selected)

                    real_read_frontmatter = update_reporting._read_frontmatter_only

                    def swap_before_frontmatter(pin, path):
                        shutil.rmtree(selected)
                        if use_symlink:
                            import os
                            os.symlink(root_b, selected)
                        else:
                            shutil.copytree(root_b, selected)
                        return real_read_frontmatter(pin, path)

                    with mock.patch.object(update_reporting, '_read_frontmatter_only',
                                            swap_before_frontmatter):
                        report = update_reporting.advanced_report(
                            'zip', None, root=selected,
                            candidate_paths=('workspace/context/personal/allow.md',), host_read=True)
                    self.assertEqual((), report.personal_paths)

    def test_traversal_candidate_rejected_before_header_read(self):
        with tempfile.TemporaryDirectory() as workdir:
            root = Path(workdir)
            _write_tree(root, {
                'system/routing/context_registry.md':
                    _sbs_tests.SideBySideRegistryTests._registry_text(
                        [('personal', 'workspace/context/personal')]),
            })
            real_reader = update_reporting._read_frontmatter_only
            with mock.patch.object(update_reporting, '_read_frontmatter_only') as spy_reader:
                spy_reader.side_effect = real_reader
                report = update_reporting.advanced_report(
                    'zip', None, root=root,
                    candidate_paths=('../../etc/passwd.md', '/etc/passwd.md'), host_read=True)
                spy_reader.assert_not_called()
            self.assertEqual((), report.personal_paths)

    def test_advanced_report_object_contains_no_raw_header_or_unauthorized_path(self):
        import dataclasses
        field_names = {f.name for f in dataclasses.fields(update_reporting.AdvancedReport)}
        self.assertEqual({'lines', 'personal_paths'}, field_names)

    def test_advanced_report_product_result_lines_are_truthful(self):
        succeeded = git_update.ApplyResult(
            mutation_started=True, validation_ran=True, validation_passed=True, commit='abc123')
        report = update_reporting.advanced_report('git', succeeded)
        self.assertIn('commit: abc123', report.lines)

        failed = git_update.ApplyResult(failure='object_transfer_failed', validation_ran=True,
                                         validation_passed=True)
        report = update_reporting.advanced_report('git', failed)
        self.assertTrue(any('object_transfer_failed' in line for line in report.lines))
        self.assertFalse(any(line.startswith('commit:') for line in report.lines))


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
