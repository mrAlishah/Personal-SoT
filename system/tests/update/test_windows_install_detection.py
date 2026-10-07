import os
from pathlib import Path
import subprocess
import tempfile
import unittest

from system.assistant import update_reporting, windows_install_detection
from system.assistant.update_reporting import HostCapability


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
    def test_valid_windows_archive_routes_to_zip(self):
        with tempfile.TemporaryDirectory() as workdir:
            root = Path(workdir, 'root')
            (root / 'workspace' / 'adapters').mkdir(parents=True)
            (root / 'workspace' / 'adapters' / 'runtime_entrypoint.md').write_text('x\n')
            (root / 'system' / 'validation').mkdir(parents=True)
            (root / 'system' / 'validation' / 'validate_v1.py').write_text('x\n')

            self.assertEqual('zip', update_reporting.detect_install_type(root, _FULL))

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
