from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

from system.install import installer


class InstallerParsingTests(unittest.TestCase):
    def test_github_slug_accepts_supported_exact_urls(self):
        cases = {
            "https://github.com/alice/myPersonal-SoT": "alice/myPersonal-SoT",
            "https://github.com/alice/myPersonal-SoT.git": "alice/myPersonal-SoT",
            "git@github.com:alice/myPersonal-SoT.git": "alice/myPersonal-SoT",
            "ssh://git@github.com/alice/myPersonal-SoT.git": "alice/myPersonal-SoT",
        }
        for value, expected in cases.items():
            with self.subTest(value=value):
                self.assertEqual(expected, installer._github_slug(value))

    def test_github_slug_rejects_non_github_or_embedded_credentials(self):
        for value in (
            "https://example.com/alice/repo",
            "https://user:secret@github.com/alice/repo",
            "file:///tmp/repo",
            "github.com/alice/repo",
        ):
            with self.subTest(value=value):
                self.assertIsNone(installer._github_slug(value))

    def test_public_remote_role_is_exact(self):
        self.assertTrue(
            installer._is_public_remote("https://github.com/mrAlishah/Personal-SoT.git")
        )
        self.assertTrue(
            installer._is_public_remote("git@github.com:mrAlishah/Personal-SoT.git")
        )
        self.assertFalse(
            installer._is_public_remote("https://github.com/alice/Personal-SoT.git")
        )

    def test_drive_folder_url_accepts_normal_and_account_scoped_forms(self):
        self.assertEqual(
            "folderABC123",
            installer._drive_folder_id(
                "https://drive.google.com/drive/folders/folderABC123?usp=sharing"
            ),
        )
        self.assertEqual(
            "folderABC123",
            installer._drive_folder_id(
                "https://drive.google.com/drive/u/0/folders/folderABC123"
            ),
        )

    def test_drive_folder_url_rejects_non_folder_links(self):
        for value in (
            "https://drive.google.com/file/d/abc/view",
            "https://example.com/drive/folders/abc",
            "folderABC123",
        ):
            with self.subTest(value=value):
                self.assertIsNone(installer._drive_folder_id(value))


class InstallerFreshCloneTests(unittest.TestCase):
    @patch("system.install.installer._public_validator")
    @patch("system.install.installer.git_update.classify")
    @patch("system.install.installer._remote_url")
    @patch("system.install.installer._git")
    @patch("system.install.installer._is_git_root", return_value=True)
    def test_initial_install_rejects_clone_not_exactly_current_public_main(
        self, _git_root, git, remote_url, classify, _public_validator
    ):
        git.return_value = installer.CommandResult(0, "main\n")
        remote_url.side_effect = (
            lambda _root, name, push=False:
            installer.PUBLIC_URL if name == "origin" and not push else None
        )
        classify.return_value = installer.git_update.Plan(
            "a" * 40,
            "b" * 40,
            "a" * 40,
        )

        with self.assertRaises(installer.InstallError) as raised:
            installer._sync_fresh_public_clone(Path("."))

        self.assertIn("exactly current", str(raised.exception).lower())
        _public_validator.assert_not_called()


class InstallerSafetyTests(unittest.TestCase):
    def test_next_side_by_side_destination_never_reuses_existing_folder(self):
        with TemporaryDirectory() as directory:
            root = Path(directory)
            current = root / "Personal-SoT"
            current.mkdir()
            first = root / "Personal-SoT-updated"
            first.mkdir()

            destination = installer._next_side_by_side_destination(current)

            self.assertEqual(root / "Personal-SoT-updated-2", destination)
            self.assertFalse(destination.exists())

    @patch("system.install.installer._git")
    def test_git_url_rewrite_rules_fail_closed(self, git):
        git.return_value = installer.CommandResult(
            0, "url.ssh://example.invalid/.insteadof https://github.com/\n"
        )

        with self.assertRaises(installer.InstallError) as raised:
            installer._reject_git_url_rewrites(Path("."))

        self.assertIn("rewrite", str(raised.exception).lower())

    @patch("system.install.installer._anonymous_github_visibility", return_value="public")
    @patch("system.install.installer.shutil.which", return_value=None)
    @patch("system.install.installer._git")
    def test_existing_private_origin_rejects_public_repository(
        self, git, _which, _visibility
    ):
        git.side_effect = [
            installer.CommandResult(1, ""),
            installer.CommandResult(0, "refs/heads/main\n"),
        ]

        with self.assertRaises(installer.InstallError) as raised:
            installer._prove_existing_private_github_origin(
                Path("."), "https://github.com/alice/not-private.git"
            )

        self.assertIn("public", str(raised.exception).lower())

    @patch("system.install.installer._anonymous_github_visibility", return_value="private_or_hidden")
    @patch("system.install.installer.shutil.which", return_value=None)
    @patch("system.install.installer._git")
    def test_existing_private_origin_requires_push_permission(
        self, git, _which, _visibility
    ):
        git.side_effect = [
            installer.CommandResult(1, ""),
            installer.CommandResult(0, "refs/heads/main\n"),
            installer.CommandResult(1, "", "denied"),
        ]

        with self.assertRaises(installer.InstallError) as raised:
            installer._prove_existing_private_github_origin(
                Path("."), "git@github.com:alice/private-sot.git"
            )

        self.assertIn("write access", str(raised.exception).lower())

    @patch("system.install.installer._anonymous_github_visibility", return_value="private_or_hidden")
    @patch("system.install.installer.shutil.which", return_value=None)
    @patch("system.install.installer._git")
    def test_first_github_install_requires_empty_destination(
        self, git, _which, _visibility
    ):
        git.side_effect = [
            installer.CommandResult(1, ""),
            installer.CommandResult(0, "deadbeef\trefs/heads/main\n"),
        ]

        with self.assertRaises(installer.InstallError) as raised:
            installer._verify_private_github_destination(
                Path("."), "https://github.com/alice/private-sot.git"
            )

        self.assertIn("empty", str(raised.exception).lower())


if __name__ == "__main__":
    unittest.main()
