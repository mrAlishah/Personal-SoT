"""Safe private-origin sync: ownership, privacy, rollback and staging rules."""
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest import mock
from urllib import error as urlerror

from system.update import private_origin_sync as sync
from system.validation.validate_v1 import context_registry_entries


PRIVATE = "https://github.com/ExampleOwner/myPersonal-SoT.git"
PUBLIC = "https://github.com/mrAlishah/Personal-SoT.git"
LOCAL = "a" * 40
REMOTE = "b" * 40


def completed(output="", code=0):
    return subprocess.CompletedProcess(["git"], code, stdout=output, stderr="")


class PrivateOriginSyncTests(unittest.TestCase):
    def test_canonical_public_origin_is_never_eligible(self):
        def fake_run(root, hooks, *args, **kwargs):
            if args[:3] == ("symbolic-ref", "--quiet", "--short"):
                return completed("main\n")
            return completed(PUBLIC + "\n")
        with mock.patch.object(sync, "_run", side_effect=fake_run):
            self.assertIsNone(sync.private_origin_url(Path(".")))

    def test_unexpected_origin_name_is_not_eligible(self):
        url = "https://github.com/ExampleOwner/random-repo.git"
        def fake_run(root, hooks, *args, **kwargs):
            if args[0] == "symbolic-ref":
                return completed("main\n")
            return completed(url + "\n")
        with mock.patch.object(sync, "_run", side_effect=fake_run):
            self.assertIsNone(sync.private_origin_url(Path(".")))

    def test_only_anonymous_404_can_prove_private(self):
        hidden = urlerror.HTTPError("https://api.github.com/repos/x/y", 404,
                                    "Not found", None, None)
        with mock.patch.object(sync.urlrequest, "urlopen", side_effect=hidden):
            self.assertTrue(sync._is_proven_private(PRIVATE))
        public = mock.MagicMock()
        with mock.patch.object(sync.urlrequest, "urlopen", return_value=public):
            self.assertFalse(sync._is_proven_private(PRIVATE))
        with mock.patch.object(sync.urlrequest, "urlopen", side_effect=OSError()):
            self.assertFalse(sync._is_proven_private(PRIVATE))

    def test_legacy_and_two_line_registry_formats_are_both_recognized(self):
        source = (
            "# registry\n\n## entry_shape\n\n```text\n"
            "runtime_scope → repository_relative_canonical_directory\n"
            "```\n\n## registered_scopes\n\n```text\n"
            "personal/projects/fullstack → workspace/context/personal/projects/fullstack/\n"
            "personal/projects/other\n"
            "→ workspace/context/personal/projects/other/\n"
            "```\n"
        )
        self.assertEqual(
            [
                ("personal/projects/fullstack",
                 "workspace/context/personal/projects/fullstack/"),
                ("personal/projects/other",
                 "workspace/context/personal/projects/other/"),
            ],
            context_registry_entries(source),
        )

    def test_validated_local_can_push_if_remote_is_ancestor(self):
        called = []
        def fake_run(root, hooks, *args, **kwargs):
            called.append(args)
            if args[0] == "rev-parse":
                return completed((REMOTE if "origin/main" in args[-1] else LOCAL) + "\n")
            if args[0] == "ls-remote":
                return completed(REMOTE + "\trefs/heads/main\n")
            return completed()
        with mock.patch.object(sync, "private_origin_url", return_value=PRIVATE), \
             mock.patch.object(sync.git_update, "_preflight", return_value=None), \
             mock.patch.object(sync, "_run", side_effect=fake_run), \
             mock.patch.object(sync, "_is_proven_private", return_value=True), \
             mock.patch.object(sync, "_validate", return_value=True) as validate:
            result = sync.synchronize(Path("."), PRIVATE)
        self.assertEqual("synchronized", result.status)
        validate.assert_called_once()
        self.assertTrue(any(args[0] == "push" for args in called))
        self.assertFalse(any(args[0] == "merge" for args in called))

    def test_invalid_merged_context_is_aborted_and_never_pushed(self):
        called = []
        def fake_run(root, hooks, *args, **kwargs):
            called.append(args)
            if args[0] == "rev-parse":
                return completed((REMOTE if "origin/main" in args[-1] else LOCAL) + "\n")
            if args[0] == "merge-base":
                return completed(code=1)
            if args[:2] == ("config", "--get-regexp"):
                return completed(code=1)  # no custom merge driver configured
            return completed()
        with mock.patch.object(sync, "private_origin_url", return_value=PRIVATE), \
             mock.patch.object(sync.git_update, "_preflight", return_value=None), \
             mock.patch.object(sync, "_run", side_effect=fake_run), \
             mock.patch.object(sync, "_is_proven_private", return_value=True), \
             mock.patch.object(sync, "_normalize_registry", return_value=False), \
             mock.patch.object(sync, "_validate", return_value=False):
            result = sync.synchronize(Path("."), PRIVATE)
        self.assertEqual("failed", result.status)
        self.assertEqual("final_validation_failed", result.failure)
        self.assertTrue(result.rollback_completed)
        self.assertTrue(any(args[:2] == ("merge", "--abort") for args in called))
        self.assertFalse(any(args[0] in ("commit", "push") for args in called))

    def test_push_rejection_never_force_pushes(self):
        called = []
        def fake_run(root, hooks, *args, **kwargs):
            called.append(args)
            if args[0] == "rev-parse":
                return completed((REMOTE if "origin/main" in args[-1] else LOCAL) + "\n")
            if args[0] == "ls-remote":
                return completed(REMOTE + "\trefs/heads/main\n")
            if args[0] == "push":
                return completed(code=1)
            return completed()
        with mock.patch.object(sync, "private_origin_url", return_value=PRIVATE), \
             mock.patch.object(sync.git_update, "_preflight", return_value=None), \
             mock.patch.object(sync, "_run", side_effect=fake_run), \
             mock.patch.object(sync, "_is_proven_private", return_value=True), \
             mock.patch.object(sync, "_validate", return_value=True):
            result = sync.synchronize(Path("."), PRIVATE)
        self.assertEqual("local_only", result.status)
        self.assertEqual("private_push_rejected", result.failure)
        self.assertTrue(all("--force" not in cmd for cmd in called))


if __name__ == "__main__":
    unittest.main()
