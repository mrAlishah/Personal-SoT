from dataclasses import replace
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

from system.prompts.builder import (
    ReuseAssessment,
    apply_change,
    choose_action,
    preview_change,
)
from system.validation import validate_prompts, validate_public, validate_v1


class PromptBuilderReuseTests(unittest.TestCase):
    def test_exact_reuse_wins_before_every_other_option(self):
        assessment = ReuseAssessment(
            exact_identity="code/review",
            parameterized_identity="coding/review_generic",
            composition=("profile:g/coding",),
            edit_identity="coding/old_review",
            same_semantic_owner=True,
        )

        self.assertEqual(("reuse_exact", "code/review"), choose_action(assessment))

    def test_parameterized_reuse_wins_before_composition_or_creation(self):
        assessment = ReuseAssessment(
            parameterized_identity="code/review",
            composition=("profile:g/coding",),
        )

        self.assertEqual(
            ("reuse_parameterized", "code/review"),
            choose_action(assessment),
        )

    def test_composition_wins_before_edit_or_creation(self):
        assessment = ReuseAssessment(
            composition=("profile:g/coding", "tone:professional"),
            edit_identity="code/review",
            same_semantic_owner=True,
        )

        self.assertEqual(("compose", None), choose_action(assessment))

    def test_edit_requires_the_same_semantic_owner(self):
        assessment = ReuseAssessment(
            edit_identity="code/review",
            same_semantic_owner=True,
        )

        self.assertEqual(("edit", "code/review"), choose_action(assessment))

    def test_similarity_without_same_owner_never_authorizes_overwrite(self):
        assessment = ReuseAssessment(
            edit_identity="code/review",
            same_semantic_owner=False,
        )

        self.assertEqual(("create", None), choose_action(assessment))

    def test_create_is_last_resort(self):
        self.assertEqual(("create", None), choose_action(ReuseAssessment()))


class PromptBuilderSafeWriteTests(unittest.TestCase):
    def repository(self, root: Path) -> None:
        for name in ("workspace", "system", "guides"):
            (root / name).mkdir()

    def source(self, body: str = "Do the requested task.", extra: str = "") -> str:
        return (
            "---\n"
            "prompt_status: active\n"
            "prompt_tags:\n"
            "  - test\n"
            "prompt_profiles: []\n"
            "prompt_formats: []\n"
            "required_params: []\n"
            "optional_params: []\n"
            "owned_assets: []\n"
            f"{extra}"
            "---\n"
            f"{body}\n"
        )

    def write_prompt(self, root: Path, identity: str, source: str) -> Path:
        path = root / "workspace" / "prompts" / f"{identity}.md"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(source, encoding="utf-8")
        return path

    def preview(self, root: Path, operation: str = "create", **overrides):
        arguments = {
            "root": root,
            "operation": operation,
            "identity": "custom/helpfulprompt",
            "content": self.source(),
            "same_semantic_owner": operation == "edit",
            "fact_safe": True,
            "write_capable": True,
        }
        arguments.update(overrides)
        return preview_change(**arguments)

    def test_create_preview_contains_complete_diff_and_absent_target(self):
        with TemporaryDirectory() as directory:
            root = Path(directory)
            self.repository(root)

            proposal = self.preview(root)

            self.assertEqual("workspace/prompts/custom/helpfulprompt.md", proposal.target)
            self.assertIsNone(proposal.before_digest)
            self.assertIsNone(proposal.before_content)
            self.assertIn("---", proposal.diff)
            self.assertIn("Do the requested task.", proposal.diff)
            self.assertEqual((), proposal.preflight_errors)

    def test_edit_requires_same_semantic_owner(self):
        with TemporaryDirectory() as directory:
            root = Path(directory)
            self.repository(root)
            self.write_prompt(root, "custom/helpfulprompt", self.source("Before."))

            with self.assertRaisesRegex(ValueError, "same semantic owner"):
                self.preview(root, "edit", same_semantic_owner=False)

    def test_similarity_never_authorizes_overwrite(self):
        with TemporaryDirectory() as directory:
            root = Path(directory)
            self.repository(root)
            path = self.write_prompt(root, "custom/helpfulprompt", self.source("Before."))

            with self.assertRaises(ValueError):
                self.preview(root, "edit", same_semantic_owner=False, content=self.source("Similar."))

            self.assertIn("Before.", path.read_text(encoding="utf-8"))

    def test_unknown_prompt_include_field_fails_preflight(self):
        with TemporaryDirectory() as directory:
            root = Path(directory)
            self.repository(root)

            proposal = self.preview(root, content=self.source(extra="prompt_include: other/prompt\n"))

            self.assertTrue(any("unsupported prompt fields" in error for error in proposal.preflight_errors))

    def test_secret_or_invalid_content_fails_preflight(self):
        with TemporaryDirectory() as directory:
            root = Path(directory)
            self.repository(root)

            proposal = self.preview(root, content=self.source("api_token: live_secret_value"))

            self.assertTrue(any("possible raw secret" in error for error in proposal.preflight_errors))

    def test_unclassified_durable_fact_candidate_cannot_reach_preview(self):
        with TemporaryDirectory() as directory:
            root = Path(directory)
            self.repository(root)

            with self.assertRaisesRegex(ValueError, "fact-safe"):
                self.preview(root, fact_safe=False)

    def test_preview_only_client_cannot_apply_or_claim_validation(self):
        with TemporaryDirectory() as directory:
            root = Path(directory)
            self.repository(root)
            proposal = self.preview(root, write_capable=False)

            result = apply_change(root, proposal, proposal.confirmation_digest)

            self.assertFalse(result.write_applied)
            self.assertFalse(result.validation_ran)
            self.assertIsNone(result.validation_passed)
            self.assertFalse(result.success)
            self.assertFalse((root / proposal.target).exists())

    def test_filesystem_write_failure_reports_not_applied(self):
        with TemporaryDirectory() as directory:
            root = Path(directory)
            self.repository(root)
            proposal = self.preview(root)

            with patch("system.prompts.builder.os.replace", side_effect=OSError("denied")):
                result = apply_change(root, proposal, proposal.confirmation_digest)

            self.assertFalse(result.write_applied)
            self.assertFalse(result.validation_ran)
            self.assertIsNone(result.validation_passed)
            self.assertTrue(any("write failed" in error for error in result.validation_errors))
            self.assertFalse((root / proposal.target).exists())

    def test_wrong_confirmation_digest_cannot_apply(self):
        with TemporaryDirectory() as directory:
            root = Path(directory)
            self.repository(root)
            proposal = self.preview(root)

            result = apply_change(root, proposal, "wrong")

            self.assertFalse(result.write_applied)
            self.assertFalse(result.validation_ran)
            self.assertFalse((root / proposal.target).exists())

    def test_tampered_proposal_content_cannot_apply(self):
        with TemporaryDirectory() as directory:
            root = Path(directory)
            self.repository(root)
            proposal = self.preview(root)
            tampered = replace(proposal, content=self.source("Tampered after confirmation."))

            result = apply_change(root, tampered, proposal.confirmation_digest)

            self.assertFalse(result.write_applied)
            self.assertFalse((root / proposal.target).exists())

    def test_preflight_is_revalidated_before_write(self):
        with TemporaryDirectory() as directory:
            root = Path(directory)
            self.repository(root)
            invalid = self.preview(
                root,
                content=self.source(extra="prompt_include: other/prompt\n"),
            )
            tampered = replace(invalid, preflight_errors=())

            result = apply_change(root, tampered, tampered.confirmation_digest)

            self.assertFalse(result.write_applied)
            self.assertFalse((root / tampered.target).exists())

    def test_change_during_preflight_is_not_overwritten(self):
        for operation in ("create", "edit"):
            with self.subTest(operation=operation), TemporaryDirectory() as directory:
                root = Path(directory)
                self.repository(root)
                path = root / "workspace/prompts/custom/helpfulprompt.md"
                if operation == "edit":
                    self.write_prompt(root, "custom/helpfulprompt", self.source("Before."))
                proposal = self.preview(root, operation, content=self.source("Proposed."))
                original = validate_prompts.validate_source

                def concurrent_change(*args, **kwargs):
                    path.parent.mkdir(parents=True, exist_ok=True)
                    path.write_text(self.source("Concurrent change."), encoding="utf-8")
                    return original(*args, **kwargs)

                with patch.object(validate_prompts, "validate_source", side_effect=concurrent_change):
                    result = apply_change(root, proposal, proposal.confirmation_digest)

                self.assertFalse(result.write_applied)
                self.assertIn("Concurrent change.", path.read_text(encoding="utf-8"))

    def test_symlink_ancestor_cannot_redirect_prompt_write(self):
        with TemporaryDirectory() as directory:
            root = Path(directory)
            self.repository(root)
            prompt_root = root / "workspace/prompts"
            profiles = root / "workspace/profiles"
            prompt_root.mkdir()
            profiles.mkdir()
            (prompt_root / "custom").symlink_to(profiles, target_is_directory=True)

            with self.assertRaisesRegex(ValueError, "symbolic link"):
                self.preview(root)

            self.assertFalse((profiles / "helpfulprompt.md").exists())

    def test_referenced_state_change_requires_new_preview(self):
        with TemporaryDirectory() as directory:
            root = Path(directory)
            self.repository(root)
            profile = root / "workspace/profiles/helper.md"
            profile.parent.mkdir()
            profile.write_text("first behavior", encoding="utf-8")
            content = self.source().replace(
                "prompt_profiles: []", "prompt_profiles:\n  - helper"
            )
            proposal = self.preview(root, content=content)
            profile.write_text("changed behavior", encoding="utf-8")

            result = apply_change(root, proposal, proposal.confirmation_digest)

            self.assertFalse(result.write_applied)
            self.assertFalse((root / proposal.target).exists())

    def test_reserved_readme_identity_cannot_be_created(self):
        with TemporaryDirectory() as directory:
            root = Path(directory)
            self.repository(root)

            proposal = self.preview(root, identity="custom/readme")
            result = apply_change(root, proposal, proposal.confirmation_digest)

            self.assertTrue(any("reserved" in error for error in proposal.preflight_errors))
            self.assertFalse(result.write_applied)

    def test_stale_edit_requires_new_preview(self):
        with TemporaryDirectory() as directory:
            root = Path(directory)
            self.repository(root)
            path = self.write_prompt(root, "custom/helpfulprompt", self.source("Before."))
            proposal = self.preview(root, "edit", content=self.source("After."))
            path.write_text(self.source("Concurrent change."), encoding="utf-8")

            result = apply_change(root, proposal, proposal.confirmation_digest)

            self.assertFalse(result.write_applied)
            self.assertFalse(result.validation_ran)
            self.assertIn("Concurrent change.", path.read_text(encoding="utf-8"))

    def test_occupied_create_target_requires_new_preview(self):
        with TemporaryDirectory() as directory:
            root = Path(directory)
            self.repository(root)
            proposal = self.preview(root)
            path = self.write_prompt(root, "custom/helpfulprompt", self.source("Concurrent create."))

            result = apply_change(root, proposal, proposal.confirmation_digest)

            self.assertFalse(result.write_applied)
            self.assertFalse(result.validation_ran)
            self.assertIn("Concurrent create.", path.read_text(encoding="utf-8"))

    def test_successful_local_create_runs_real_prompt_validation(self):
        with TemporaryDirectory() as directory:
            root = Path(directory)
            self.repository(root)
            proposal = self.preview(root)

            result = apply_change(root, proposal, proposal.confirmation_digest)

            self.assertTrue(result.write_applied)
            self.assertTrue(result.validation_ran)
            self.assertTrue(result.validation_passed)
            self.assertTrue(result.success)
            self.assertEqual([], validate_prompts.run(root))

    def test_successful_local_create_runs_all_relevant_validators(self):
        with TemporaryDirectory() as directory:
            root = Path(directory)
            self.repository(root)
            proposal = self.preview(root)

            with patch.object(validate_prompts, "run", wraps=validate_prompts.run) as prompts:
                with patch.object(validate_v1, "run", wraps=validate_v1.run) as core:
                    with patch.object(validate_public, "run", wraps=validate_public.run) as public:
                        result = apply_change(root, proposal, proposal.confirmation_digest)

            self.assertTrue(result.success)
            prompts.assert_called_once_with(root.resolve())
            core.assert_called_once_with(root.resolve(), "core")
            public.assert_called_once_with(root.resolve())

    def test_write_applied_but_repository_validation_failed_is_explicit_and_recoverable(self):
        with TemporaryDirectory() as directory:
            root = Path(directory)
            self.repository(root)
            private_identifier = "mrAlishah/" + "obsidian-ai-context-source-of-truth"
            content = self.source(f"repository: {private_identifier}")
            proposal = self.preview(root, content=content)

            result = apply_change(root, proposal, proposal.confirmation_digest)

            self.assertTrue(result.write_applied)
            self.assertTrue(result.validation_ran)
            self.assertFalse(result.validation_passed)
            self.assertFalse(result.success)
            self.assertTrue(any(error.startswith("public: ") for error in result.validation_errors))
            self.assertEqual(proposal.before_content, result.before_content)
            self.assertEqual(proposal.diff, result.diff)
            self.assertTrue((root / result.affected_path).is_file())


if __name__ == "__main__":
    unittest.main()
