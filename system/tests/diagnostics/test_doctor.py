from pathlib import Path
import subprocess
import sys
from tempfile import TemporaryDirectory
import unittest

from system.diagnostics import doctor


REPOSITORY_ROOT = Path(__file__).resolve().parents[3]


class DoctorTests(unittest.TestCase):
    def minimal_repository(self, root: Path) -> None:
        for name in ("workspace", "system", "guides"):
            (root / name).mkdir()
        entrypoint = root / "workspace/adapters/runtime_entrypoint.md"
        entrypoint.parent.mkdir(parents=True)
        entrypoint.write_text(
            "# Runtime\n\n"
            "deployment_config: workspace/adapters/public_bootstrap.md\n"
            "runtime_contract: system/adapters/runtime_bootstrap.md\n",
            encoding="utf-8",
        )

    def test_ready_repository_has_beginner_summary(self):
        report = doctor.run(
            REPOSITORY_ROOT,
            adapter="workspace/adapters/AGENTS.md",
            write_capability="available",
        )

        rendered = doctor.render(report)

        self.assertFalse(report.blocked)
        self.assertIn("✓ Setup is ready", rendered)
        self.assertIn("✓ Personal workspace is valid", rendered)
        self.assertIn("✓ Codex configuration detected", rendered)
        self.assertNotIn("Advanced", rendered)

    def test_missing_runtime_reference_is_blocking(self):
        with TemporaryDirectory() as directory:
            root = Path(directory)
            self.minimal_repository(root)
            (root / "workspace/adapters/public_bootstrap.md").write_text("# Bootstrap\n", encoding="utf-8")

            report = doctor.run(root)
            rendered = doctor.render(report, advanced=True)

            self.assertTrue(report.blocked)
            self.assertIn("✗ Runtime connection is broken", rendered)
            self.assertIn("Blocking: yes", rendered)
            self.assertIn("How to fix:", rendered)
            self.assertIn("Advanced", rendered)

    def test_runtime_reference_outside_repository_is_blocking(self):
        with TemporaryDirectory() as directory:
            root = Path(directory)
            self.minimal_repository(root)
            entrypoint = root / "workspace/adapters/runtime_entrypoint.md"
            entrypoint.write_text(
                "# Runtime\n\ndeployment_config: /etc/hosts\n",
                encoding="utf-8",
            )

            report = doctor.run(root)

            self.assertTrue(report.blocked)
            self.assertIn("✗ Runtime connection is broken", doctor.render(report))

    def test_runtime_symlink_outside_repository_is_blocking(self):
        with TemporaryDirectory() as directory:
            base = Path(directory)
            root = base / "repository"
            root.mkdir()
            self.minimal_repository(root)
            bootstrap = root / "workspace/adapters/public_bootstrap.md"
            bootstrap.write_text("# Bootstrap\n", encoding="utf-8")
            outside = base / "outside_runtime.md"
            outside.write_text("# Outside\n", encoding="utf-8")
            runtime = root / "system/adapters/runtime_bootstrap.md"
            runtime.parent.mkdir(parents=True)
            runtime.symlink_to(outside)

            report = doctor.run(root)

            self.assertTrue(report.blocked)
            self.assertIn("✗ Runtime connection is broken", doctor.render(report))

    def test_web_client_without_write_capability_is_preview_only(self):
        report = doctor.run(
            REPOSITORY_ROOT,
            adapter="workspace/adapters/chatgpt_project_instructions.md",
            write_capability="unavailable",
        )

        rendered = doctor.render(report)

        self.assertFalse(report.blocked)
        self.assertIn("✓ ChatGPT configuration detected", rendered)
        self.assertIn("⚠ ChatGPT is preview-only", rendered)
        self.assertNotIn("run write validation", rendered)

    def test_client_topology_comes_from_adapter_metadata(self):
        with TemporaryDirectory() as directory:
            root = Path(directory)
            self.minimal_repository(root)
            adapter = root / "workspace/adapters/example_client.md"
            adapter.write_text(
                "# Example client\n\n"
                "client_name: Example Client\n"
                "discovery_surface: EXAMPLE.md\n"
                "entrypoint: workspace/adapters/runtime_entrypoint.md\n",
                encoding="utf-8",
            )
            (root / "EXAMPLE.md").write_text(
                "Read workspace/adapters/example_client.md\n",
                encoding="utf-8",
            )

            report = doctor.run(
                root,
                adapter="workspace/adapters/example_client.md",
                write_capability="unavailable",
            )
            rendered = doctor.render(report)

            self.assertIn("✓ Example Client configuration detected", rendered)
            self.assertIn("⚠ Example Client is preview-only", rendered)

    def test_existing_validators_own_project_profile_and_prompt_diagnosis(self):
        with TemporaryDirectory() as directory:
            root = Path(directory)
            self.minimal_repository(root)
            project = root / "workspace/context/personal/projects/broken_project/project.md"
            project.parent.mkdir(parents=True)
            project.write_text("---\nai_access: allow\n---\n# Broken project\n", encoding="utf-8")
            profile = root / "workspace/profiles/broken_profile.md"
            profile.parent.mkdir(parents=True)
            profile.write_text("---\ntone: missing_tone\n---\n", encoding="utf-8")
            prompt = root / "workspace/prompts/broken_prompt.md"
            prompt.parent.mkdir(parents=True)
            prompt.write_text("# Missing prompt manifest\n", encoding="utf-8")

            report = doctor.run(root)
            rendered = doctor.render(report)

            self.assertIn("✗ Personal workspace has validation problems", rendered)
            self.assertIn("✗ One or more prompts are invalid", rendered)

    def test_diagnostics_do_not_expose_secret_values_or_mutate_files(self):
        with TemporaryDirectory() as directory:
            root = Path(directory)
            self.minimal_repository(root)
            context = root / "workspace/context/personal/private_notes.md"
            context.parent.mkdir(parents=True)
            context.write_text("password: supersecretvalue\n", encoding="utf-8")
            before = context.read_bytes()

            report = doctor.run(root)
            rendered = doctor.render(report, advanced=True)

            self.assertTrue(report.blocked)
            self.assertNotIn("supersecretvalue", rendered)
            self.assertEqual(before, context.read_bytes())

    def test_advanced_prompt_and_public_findings_do_not_expose_secret_values(self):
        with TemporaryDirectory() as directory:
            root = Path(directory)
            self.minimal_repository(root)
            prompt = root / "workspace/prompts/unsafe_prompt.md"
            prompt.parent.mkdir(parents=True)
            prompt.write_text(
                "---\n"
                "prompt_status: active\n"
                "prompt_tags: []\n"
                "prompt_profiles: []\n"
                "prompt_formats: []\n"
                "prompt_tone: professional\n"
                "prompt_depth: medium\n"
                "required_params: []\n"
                "optional_params: []\n"
                "owned_assets: []\n"
                "---\n"
                "api_token: promptsecretvalue\n",
                encoding="utf-8",
            )

            rendered = doctor.render(doctor.run(root), advanced=True)

            self.assertIn("✗ One or more prompts are invalid", rendered)
            self.assertIn("✗ Public-distribution safety check found a problem", rendered)
            self.assertNotIn("promptsecretvalue", rendered)

    def test_direct_cli_invocation_works_from_repository_root(self):
        result = subprocess.run(
            (
                sys.executable,
                "system/diagnostics/doctor.py",
                "--adapter",
                "workspace/adapters/AGENTS.md",
                "--write-capability",
                "available",
            ),
            cwd=REPOSITORY_ROOT,
            capture_output=True,
            text=True,
            check=False,
        )

        self.assertEqual(0, result.returncode, result.stderr)
        self.assertIn("✓ Setup is ready", result.stdout)


if __name__ == "__main__":
    unittest.main()
