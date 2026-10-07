from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from system.install import install


REPOSITORY_ROOT = Path(__file__).resolve().parents[3]


class InstallTests(unittest.TestCase):
    def test_github_slug_accepts_https_and_ssh(self):
        self.assertEqual(
            "alice/myPersonal-SoT",
            install.github_slug("https://github.com/alice/myPersonal-SoT.git"),
        )
        self.assertEqual(
            "alice/myPersonal-SoT",
            install.github_slug("git@github.com:alice/myPersonal-SoT.git"),
        )

    def test_github_slug_rejects_other_hosts(self):
        self.assertIsNone(install.github_slug("https://example.com/alice/repo.git"))

    def test_windows_launcher_forces_utf8_for_python_subprocesses(self):
        launcher = (REPOSITORY_ROOT / "install.bat").read_text(encoding="utf-8")
        self.assertIn('set "PYTHONUTF8=1"', launcher)
        self.assertIn('set "PYTHONIOENCODING=utf-8"', launcher)
        self.assertLess(launcher.index('set "PYTHONUTF8=1"'), launcher.index("where py"))

    def test_drive_copy_excludes_git_and_local_state(self):
        with TemporaryDirectory() as directory:
            base = Path(directory)
            source = base / "source"
            destination = base / "drive"
            (source / ".git").mkdir(parents=True)
            (source / ".worktrees/example").mkdir(parents=True)
            (source / ".claude").mkdir(parents=True)
            (source / "workspace").mkdir(parents=True)
            (source / ".git/config").write_text("secret", encoding="utf-8")
            (source / ".worktrees/example/file.md").write_text("local", encoding="utf-8")
            (source / ".claude/settings.local.json").write_text("local", encoding="utf-8")
            (source / "workspace/file.md").write_text("public", encoding="utf-8")

            old_root = install.ROOT
            try:
                install.ROOT = source
                old_checks = install.run_checks
                install.run_checks = lambda root: None
                result = install.copy_to_drive(destination)
            finally:
                install.ROOT = old_root
                install.run_checks = old_checks

            self.assertEqual(destination.resolve(), result)
            self.assertTrue((destination / "workspace/file.md").is_file())
            self.assertFalse((destination / ".git").exists())
            self.assertFalse((destination / ".worktrees").exists())
            self.assertFalse((destination / ".claude/settings.local.json").exists())

    def test_drive_destination_must_be_empty(self):
        with TemporaryDirectory() as directory:
            destination = Path(directory) / "drive"
            destination.mkdir()
            (destination / "existing.txt").write_text("x", encoding="utf-8")
            with self.assertRaises(install.InstallError):
                install.copy_to_drive(destination)


if __name__ == "__main__":
    unittest.main()
