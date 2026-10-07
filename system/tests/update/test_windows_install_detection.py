import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest import mock

from system.assistant import update_reporting, windows_install_detection
from system.assistant.update_reporting import HostCapability
from system.update import git_update


_FULL = HostCapability(can_read=True, can_write=True, can_run_local_commands=True)


class WindowsInstallDetectionTests(unittest.TestCase):
    def test_relative_path_parser_rejects_escape_forms(self):
        self.assertIsNone(windows_install_detection._parts('../x'))
        self.assertIsNone(windows_install_detection._parts('/absolute/x'))
        self.assertIsNone(windows_install_detection._parts('..\\x'))
        self.assertEqual(
            ('system', 'validation', 'validate_v1.py'),
            windows_install_detection._parts('system/validation/validate_v1.py'),
        )

    def test_non_windows_backend_fails_closed(self):
        if os.name == 'nt':
            self.skipTest('non-Windows assertion')
        self.assertEqual(
            'unknown',
            windows_install_detection.detect('.', update_reporting._ARCHIVE_MARKERS),
        )

    @unittest.skipUnless(os.name == 'nt', 'native Windows regression')
    def test_controlled_git_keeps_normal_crlf_checkout_clean(self):
        with tempfile.TemporaryDirectory() as workdir:
            root = Path(workdir, 'root')
            subprocess.run(['git', 'init', '-q', '-b', 'main', str(root)], check=True)
            subprocess.run(['git', '-C', str(root), 'config', 'user.email', 'x@example.com'], check=True)
            subprocess.run(['git', '-C', str(root), 'config', 'user.name', 'x'], check=True)
            text_path = root / 'sample.txt'
            text_path.write_bytes(b'line one\\r\\nline two\\r\\n')
            subprocess.run(
                ['git', '-C', str(root), '-c', 'core.autocrlf=true', 'add', 'sample.txt'],
                check=True,
            )
            subprocess.run(
                ['git', '-C', str(root), 'commit', '-q', '-m', 'initial'],
                check=True,
            )

            status = git_update.controlled_git(
                'status', '--porcelain=v2', '-z', '--untracked-files=all',
                cwd=str(root),
            )
            self.assertEqual(0, status.returncode)
            self.assertEqual('', status.stdout)

    @unittest.skipUnless(os.name == 'nt', 'native Windows regression')
    def test_raw_worktree_identity_never_executes_configured_clean_filter(self):
        with tempfile.TemporaryDirectory() as workdir:
            root = Path(workdir, 'root')
            subprocess.run(['git', 'init', '-q', '-b', 'main', str(root)], check=True)
            subprocess.run(['git', '-C', str(root), 'config', 'user.email', 'x@example.com'], check=True)
            subprocess.run(['git', '-C', str(root), 'config', 'user.name', 'x'], check=True)
            (root / '.gitattributes').write_text('sample.txt filter=evil\n')
            (root / 'sample.txt').write_bytes(b'line one\r\nline two\r\n')
            subprocess.run(['git', '-C', str(root), 'add', '-A'], check=True)
            subprocess.run(['git', '-C', str(root), 'commit', '-q', '-m', 'initial'], check=True)

            sentinel = Path(workdir, 'filter-ran')
            helper = Path(workdir, 'filter.py')
            helper.write_text(
                'import pathlib,sys\n'
                'pathlib.Path(sys.argv[1]).write_text("ran")\n'
                'sys.stdout.buffer.write(sys.stdin.buffer.read())\n'
            )
            command = f'"{sys.executable}" "{helper}" "{sentinel}"'
            subprocess.run(
                ['git', '-C', str(root), 'config', 'filter.evil.clean', command],
                check=True,
            )

            entry = git_update._identify_worktree_entry(
                str(root), 'sample.txt', {'GIT_NO_REPLACE_OBJECTS': '1'}
            )
            self.assertIsNotNone(entry)
            self.assertFalse(sentinel.exists())

    @unittest.skipUnless(os.name == 'nt', 'native Windows regression')
    def test_valid_windows_git_install_routes_to_git_without_posix_openat(self):
        self.assertFalse(update_reporting._NOFOLLOW_SUPPORTED)
        with tempfile.TemporaryDirectory() as workdir:
            root = Path(workdir, 'root')
            subprocess.run(['git', 'init', '-q', str(root)], check=True)
            (root / 'workspace' / 'adapters').mkdir(parents=True)
            (root / 'workspace' / 'adapters' / 'runtime_entrypoint.md').write_text('x\n')
            (root / 'system' / 'validation').mkdir(parents=True)
            (root / 'system' / 'validation' / 'validate_v1.py').write_text('x\n')

            self.assertEqual('git', update_reporting.detect_install_type(root, _FULL))

    @unittest.skipUnless(os.name == 'nt', 'native Windows regression')
    def test_windows_marker_walk_is_handle_relative_after_root_pin(self):
        with tempfile.TemporaryDirectory() as workdir:
            root = Path(workdir, 'root')
            (root / 'workspace' / 'adapters').mkdir(parents=True)
            marker = root / 'workspace' / 'adapters' / 'runtime_entrypoint.md'
            marker.write_text('x\n')

            pin = windows_install_detection._pin(root)
            self.assertIsNotNone(pin)
            try:
                with mock.patch.object(
                    windows_install_detection,
                    '_open',
                    side_effect=AssertionError('child walk must not reopen absolute paths'),
                ):
                    self.assertTrue(
                        windows_install_detection._regular(
                            pin, 'workspace/adapters/runtime_entrypoint.md'
                        )
                    )
            finally:
                pin.close()

    @unittest.skipUnless(os.name == 'nt', 'native Windows regression')
    def test_windows_linked_worktree_gitfile_routes_to_git(self):
        with tempfile.TemporaryDirectory() as workdir:
            main_repo = Path(workdir, 'main')
            subprocess.run(['git', 'init', '-q', '-b', 'main', str(main_repo)], check=True)
            subprocess.run(
                ['git', '-C', str(main_repo), 'config', 'user.email', 'x@example.com'],
                check=True,
            )
            subprocess.run(
                ['git', '-C', str(main_repo), 'config', 'user.name', 'x'],
                check=True,
            )
            (main_repo / 'workspace' / 'adapters').mkdir(parents=True)
            (main_repo / 'workspace' / 'adapters' / 'runtime_entrypoint.md').write_text('x\n')
            (main_repo / 'system' / 'validation').mkdir(parents=True)
            (main_repo / 'system' / 'validation' / 'validate_v1.py').write_text('x\n')
            subprocess.run(['git', '-C', str(main_repo), 'add', '-A'], check=True)
            subprocess.run(
                ['git', '-C', str(main_repo), 'commit', '-q', '-m', 'initial'],
                check=True,
            )

            worktree = Path(workdir, 'worktree')
            subprocess.run(
                [
                    'git', '-C', str(main_repo), 'worktree', 'add', '-q',
                    '--detach', str(worktree), 'main',
                ],
                check=True,
            )
            self.assertTrue((worktree / '.git').is_file())
            self.assertEqual('git', update_reporting.detect_install_type(worktree, _FULL))

    @unittest.skipUnless(os.name == 'nt', 'native Windows regression')
    def test_valid_windows_archive_routes_to_zip(self):
        with tempfile.TemporaryDirectory() as workdir:
            root = Path(workdir, 'root')
            (root / 'workspace' / 'adapters').mkdir(parents=True)
            (root / 'workspace' / 'adapters' / 'runtime_entrypoint.md').write_text('x\n')
            (root / 'system' / 'validation').mkdir(parents=True)
            (root / 'system' / 'validation' / 'validate_v1.py').write_text('x\n')

            self.assertEqual('zip', update_reporting.detect_install_type(root, _FULL))

    @unittest.skipUnless(os.name == 'nt', 'native Windows regression')
    def test_windows_marker_reparse_point_cannot_prove_installation(self):
        with tempfile.TemporaryDirectory() as workdir:
            root = Path(workdir, 'root')
            root.mkdir()
            (root / 'system' / 'validation').mkdir(parents=True)
            (root / 'system' / 'validation' / 'validate_v1.py').write_text('x\\n')
            outside = Path(workdir, 'outside_workspace')
            (outside / 'adapters').mkdir(parents=True)
            (outside / 'adapters' / 'runtime_entrypoint.md').write_text('x\\n')
            linked = subprocess.run(
                ['cmd', '/c', 'mklink', '/J', str(root / 'workspace'), str(outside)],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
            )
            if linked.returncode != 0:
                self.skipTest('junction creation unavailable on this Windows host')

            self.assertEqual('unknown', update_reporting.detect_install_type(root, _FULL))

    @unittest.skipUnless(os.name == 'nt', 'native Windows regression')
    def test_windows_git_reparse_point_is_not_followed(self):
        with tempfile.TemporaryDirectory() as workdir:
            root = Path(workdir, 'root')
            (root / 'workspace' / 'adapters').mkdir(parents=True)
            (root / 'workspace' / 'adapters' / 'runtime_entrypoint.md').write_text('x\n')
            (root / 'system' / 'validation').mkdir(parents=True)
            (root / 'system' / 'validation' / 'validate_v1.py').write_text('x\n')
            outside = Path(workdir, 'outside_git')
            outside.mkdir()
            linked = subprocess.run(
                ['cmd', '/c', 'mklink', '/J', str(root / '.git'), str(outside)],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
            )
            if linked.returncode != 0:
                self.skipTest('junction creation unavailable on this Windows host')

            self.assertEqual('zip', update_reporting.detect_install_type(root, _FULL))


if __name__ == '__main__':
    unittest.main()
