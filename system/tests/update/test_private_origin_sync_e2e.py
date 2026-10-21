"""Real Git three-way merge of divergent local public and private origin.

No network or user repository is accessed: all remote operations are routed
to an ephemeral bare Git repository in this integration test.
"""
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest import mock

from system.update import private_origin_sync as sync


def git(root, *args, check=True):
    completed = subprocess.run(
        ["git", *args], cwd=str(root), capture_output=True,
        text=True, check=False)
    if check and completed.returncode:
        raise AssertionError("fixture Git command failed: " + " ".join(args))
    return completed.stdout.strip()


@unittest.skipUnless(shutil.which("git"), "Git required for integration test")
class PrivateOriginE2ETest(unittest.TestCase):
    def test_public_update_and_divergent_private_fullstack_merge_and_push(self):
        with tempfile.TemporaryDirectory(prefix="sot_private_sync_test_") as work:
            base = Path(work)
            local = base / "local"
            bare = base / "origin.git"
            private = base / "remote_editor"
            local.mkdir()
            git(local, "init", "-b", "main")
            git(local, "config", "user.name", "Fixture")
            git(local, "config", "user.email", "fixture@example.invalid")
            # Real validators will run under the candidate checkout.
            scripts = local / "system/validation"
            scripts.mkdir(parents=True)
            (scripts / "validate_v1.py").write_text(
                "from pathlib import Path\n"
                "p = Path('workspace/context/personal/projects/fullstack/project.md')\n"
                "r = Path('system/routing/context_registry.md').read_text()\n"
                "if p.exists():\n"
                "    assert ('personal/projects/fullstack → workspace/context/personal/projects/fullstack/' in r\n"
                "            or 'personal/projects/fullstack\\n→ workspace/context/personal/projects/fullstack/' in r)\n",
                encoding="utf-8",
            )
            (scripts / "validate_prompts.py").write_text(
                "print('prompt validation passed')\n", encoding="utf-8")
            tests = local / "system/tests/update"
            tests.mkdir(parents=True)
            (tests / "test_dummy.py").write_text(
                "import unittest\n"
                "class A(unittest.TestCase):\n"
                "    def test_ok(self): self.assertTrue(True)\n",
                encoding="utf-8",
            )
            reg = local / "system/routing/context_registry.md"
            reg.parent.mkdir(parents=True)
            reg.write_text(
                "# registry\n## registered_scopes\n\n```text\n```\n",
                encoding="utf-8",
            )
            (local / "docs.txt").write_text("base\n", encoding="utf-8")
            git(local, "add", ".")
            git(local, "commit", "-m", "Initial private installation")

            git(base, "init", "--bare", str(bare))
            git(local, "push", str(bare), "main:refs/heads/main")
            git(base, "clone", "--branch", "main", str(bare), str(private))
            git(private, "config", "user.name", "Fixture")
            git(private, "config", "user.email", "fixture@example.invalid")

            # Local machine applies a public product update first.
            (local / "docs.txt").write_text("public release\n", encoding="utf-8")
            git(local, "add", "docs.txt")
            git(local, "commit", "-m", "Safe Update: apply canonical target")
            local_head = git(local, "rev-parse", "HEAD")

            # GitHub user separately adds personal project and the legacy
            # one-line registry representation seen in the Windows incident.
            project = private / "workspace/context/personal/projects/fullstack/project.md"
            project.parent.mkdir(parents=True)
            project.write_text("# Private Fullstack\n", encoding="utf-8")
            remote_registry = private / "system/routing/context_registry.md"
            remote_registry.write_text(
                "# registry\n## registered_scopes\n\n```text\n"
                "personal/projects/fullstack → workspace/context/personal/projects/fullstack/\n"
                "```\n",
                encoding="utf-8",
            )
            git(private, "add", ".")
            git(private, "commit", "-m", "Add Fullstack user context")
            git(private, "push", "origin", "main")

            original_git = sync._run
            def fixture_git(root, hooks, *args, **kwargs):
                # Only private NETWORK requests are rerouted to the fixture.
                # For local fetch Git's file protocol is allowed only in this
                # test process, never by the production helper.
                if args and args[0] in ("fetch", "ls-remote", "push"):
                    replaced = tuple(str(bare) if arg == self.url else arg
                                     for arg in args)
                    cmd = ["git", "-c", "protocol.file.allow=always", *replaced]
                    return subprocess.run(
                        cmd, cwd=str(root), capture_output=True, text=True,
                        check=False, timeout=90)
                return original_git(root, hooks, *args, **kwargs)

            self.url = "https://github.com/FixtureOwner/myPersonal-SoT.git"
            with mock.patch.object(sync, "private_origin_url",
                                   return_value=self.url), \
                 mock.patch.object(sync, "_is_proven_private",
                                   return_value=True), \
                 mock.patch.object(sync, "_run", side_effect=fixture_git):
                outcome = sync.synchronize(local, self.url)

            self.assertEqual("synchronized", outcome.status, outcome.failure)
            merged_head = git(local, "rev-parse", "HEAD")
            self.assertNotEqual(local_head, merged_head)
            self.assertEqual(
                merged_head, git(base, "--git-dir", str(bare),
                                 "rev-parse", "refs/heads/main"))
            self.assertEqual(
                "public release\n", (local / "docs.txt").read_text(encoding="utf-8"))
            self.assertEqual(
                "# Private Fullstack\n", project.read_text(encoding="utf-8"))
            local_project = local / "workspace/context/personal/projects/fullstack/project.md"
            self.assertEqual("# Private Fullstack\n",
                             local_project.read_text(encoding="utf-8"))
            preserved = reg.read_text(encoding="utf-8")
            self.assertIn(
                "personal/projects/fullstack → workspace/context/personal/projects/fullstack/",
                preserved,
            )
            self.assertFalse(git(local, "status", "--porcelain"))


if __name__ == "__main__":
    unittest.main()
