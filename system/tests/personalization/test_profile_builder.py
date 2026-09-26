from dataclasses import replace
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

from system.personalization.profile_builder import (
    ProfileAssessment,
    apply_change,
    choose_profile_action,
    preview_change,
)
from system.validation import validate_prompts, validate_public, validate_v1


class ProfileBuilderTests(unittest.TestCase):
    def repository(self, root: Path) -> None:
        for name in ("workspace", "system", "guides"):
            (root / name).mkdir()
        (root / "workspace/profiles").mkdir()
        (root / "system/routing").mkdir(parents=True)
        (root / "system/behavior").mkdir()

    def source(self, extra: str = "", body: str = "") -> str:
        return (
            "---\n"
            "behaviors:\n"
            "  - reasoning\n"
            "tone: formal\n"
            "depth: short\n"
            f"{extra}"
            "---\n"
            f"{body}"
        )

    def add_dependencies(self, root: Path) -> None:
        (root / "system/behavior/reasoning.md").write_text("# reasoning\n", encoding="utf-8")
        (root / "system/routing/switch_registry.md").write_text(
            "# registry\n\n## tones\n\n```text\nformal → workspace/presentation/tones/formal.md\n```\n"
            "\n## depths\n\n```text\nshort → workspace/presentation/depth/short.md\n```\n",
            encoding="utf-8",
        )
        tone = root / "workspace/presentation/tones/formal.md"
        depth = root / "workspace/presentation/depth/short.md"
        tone.parent.mkdir(parents=True)
        depth.parent.mkdir(parents=True)
        tone.write_text("# formal\n", encoding="utf-8")
        depth.write_text("# short\n", encoding="utf-8")

    def test_exact_profile_reuse_wins(self):
        action = choose_profile_action(
            ProfileAssessment(
                exact_identity="research",
                direct_composition_sufficient=True,
                reusable=True,
            )
        )

        self.assertEqual(("reuse_profile", "research"), action)

    def test_direct_composition_wins_before_creation(self):
        action = choose_profile_action(
            ProfileAssessment(direct_composition_sufficient=True, reusable=True)
        )

        self.assertEqual(("compose", None), action)

    def test_reusable_combination_can_create_only_as_last_resort(self):
        action = choose_profile_action(ProfileAssessment(reusable=True))

        self.assertEqual(("create", None), action)

    def test_edit_requires_clear_same_semantic_owner(self):
        allowed = choose_profile_action(
            ProfileAssessment(edit_identity="research", same_semantic_owner=True)
        )
        blocked = choose_profile_action(
            ProfileAssessment(
                edit_identity="research",
                same_semantic_owner=False,
                reusable=True,
            )
        )

        self.assertEqual(("edit", "research"), allowed)
        self.assertEqual(("create", None), blocked)

    def test_create_preview_contains_complete_profile_diff(self):
        with TemporaryDirectory() as directory:
            root = Path(directory)
            self.repository(root)
            self.add_dependencies(root)

            proposal = preview_change(
                root,
                "create",
                "formal_short",
                self.source(),
                same_semantic_owner=False,
                fact_safe=True,
                write_capable=True,
            )

            self.assertEqual("workspace/profiles/formal_short.md", proposal.target)
            self.assertIsNone(proposal.before_content)
            self.assertIn("tone: formal", proposal.diff)
            self.assertIn("depth: short", proposal.diff)
            self.assertEqual((), proposal.preflight_errors)

    def test_edit_preview_requires_same_owner(self):
        with TemporaryDirectory() as directory:
            root = Path(directory)
            self.repository(root)
            self.add_dependencies(root)
            (root / "workspace/profiles/formal_short.md").write_text(
                self.source(), encoding="utf-8"
            )

            with self.assertRaisesRegex(ValueError, "same semantic owner"):
                preview_change(
                    root,
                    "edit",
                    "formal_short",
                    self.source(),
                    same_semantic_owner=False,
                    fact_safe=True,
                    write_capable=True,
                )

    def test_durable_fact_classification_blocks_preview(self):
        with TemporaryDirectory() as directory:
            root = Path(directory)
            self.repository(root)

            with self.assertRaisesRegex(ValueError, "fact-safe"):
                preview_change(
                    root,
                    "create",
                    "unsafe",
                    self.source(body="Employer: Private Company\n"),
                    same_semantic_owner=False,
                    fact_safe=False,
                    write_capable=True,
                )

    def test_body_context_path_and_unknown_fields_fail_validator_owned_preflight(self):
        with TemporaryDirectory() as directory:
            root = Path(directory)
            self.repository(root)
            self.add_dependencies(root)

            body = preview_change(
                root,
                "create",
                "body_copy",
                self.source(body="Always use internal project facts.\n"),
                same_semantic_owner=False,
                fact_safe=True,
                write_capable=True,
            )
            context = preview_change(
                root,
                "create",
                "context_owner",
                self.source(extra="context: personal/projects/private\n"),
                same_semantic_owner=False,
                fact_safe=True,
                write_capable=True,
            )

            self.assertTrue(any("body" in error for error in body.preflight_errors))
            self.assertTrue(any("unsupported profile fields" in error for error in context.preflight_errors))

    def test_non_profile_mutation_is_rejected(self):
        with TemporaryDirectory() as directory:
            root = Path(directory)
            self.repository(root)

            with self.assertRaisesRegex(ValueError, "create.*edit"):
                preview_change(
                    root,
                    "create_tone",
                    "formal",
                    self.source(),
                    same_semantic_owner=False,
                    fact_safe=True,
                    write_capable=True,
                )

    def test_preview_only_client_does_not_write_or_claim_validation(self):
        with TemporaryDirectory() as directory:
            root = Path(directory)
            self.repository(root)
            self.add_dependencies(root)
            proposal = preview_change(
                root,
                "create",
                "formal_short",
                self.source(),
                same_semantic_owner=False,
                fact_safe=True,
                write_capable=False,
            )

            result = apply_change(root, proposal, proposal.confirmation_digest)

            self.assertFalse(result.write_applied)
            self.assertFalse(result.validation_ran)
            self.assertIsNone(result.validation_passed)
            self.assertFalse((root / proposal.target).exists())

    def test_confirmation_and_proposal_content_are_bound(self):
        with TemporaryDirectory() as directory:
            root = Path(directory)
            self.repository(root)
            self.add_dependencies(root)
            proposal = preview_change(
                root,
                "create",
                "formal_short",
                self.source(),
                same_semantic_owner=False,
                fact_safe=True,
                write_capable=True,
            )

            wrong = apply_change(root, proposal, "wrong")
            tampered = apply_change(
                root,
                replace(proposal, content=self.source(extra="formats:\n  - missing\n")),
                proposal.confirmation_digest,
            )

            self.assertFalse(wrong.write_applied)
            self.assertFalse(tampered.write_applied)

    def test_stale_create_and_edit_require_new_preview(self):
        for operation in ("create", "edit"):
            with self.subTest(operation=operation), TemporaryDirectory() as directory:
                root = Path(directory)
                self.repository(root)
                self.add_dependencies(root)
                path = root / "workspace/profiles/formal_short.md"
                if operation == "edit":
                    path.write_text(self.source(), encoding="utf-8")
                proposal = preview_change(
                    root,
                    operation,
                    "formal_short",
                    self.source(extra="formats: []\n"),
                    same_semantic_owner=operation == "edit",
                    fact_safe=True,
                    write_capable=True,
                )
                path.write_text(self.source(body="concurrent\n"), encoding="utf-8")

                result = apply_change(root, proposal, proposal.confirmation_digest)

                self.assertFalse(result.write_applied)
                self.assertIn("concurrent", path.read_text(encoding="utf-8"))

    def test_referenced_component_change_requires_new_preview(self):
        with TemporaryDirectory() as directory:
            root = Path(directory)
            self.repository(root)
            self.add_dependencies(root)
            proposal = preview_change(
                root,
                "create",
                "formal_short",
                self.source(),
                same_semantic_owner=False,
                fact_safe=True,
                write_capable=True,
            )
            (root / "workspace/presentation/tones/formal.md").write_text(
                "# changed formal\n", encoding="utf-8"
            )

            result = apply_change(root, proposal, proposal.confirmation_digest)

            self.assertFalse(result.write_applied)

    def test_profile_root_symlink_cannot_redirect_write(self):
        with TemporaryDirectory() as directory, TemporaryDirectory() as outside:
            root = Path(directory)
            self.repository(root)
            (root / "workspace/profiles").rmdir()
            (root / "workspace/profiles").symlink_to(Path(outside), target_is_directory=True)

            with self.assertRaisesRegex(ValueError, "symbolic link"):
                preview_change(
                    root,
                    "create",
                    "unsafe",
                    "---\n---\n",
                    same_semantic_owner=False,
                    fact_safe=True,
                    write_capable=True,
                )

    def test_atomic_write_failure_reports_not_applied(self):
        with TemporaryDirectory() as directory:
            root = Path(directory)
            self.repository(root)
            self.add_dependencies(root)
            proposal = preview_change(
                root,
                "create",
                "formal_short",
                self.source(),
                same_semantic_owner=False,
                fact_safe=True,
                write_capable=True,
            )

            with patch("system.personalization.profile_builder.os.replace", side_effect=OSError("denied")):
                result = apply_change(root, proposal, proposal.confirmation_digest)

            self.assertFalse(result.write_applied)
            self.assertFalse(result.validation_ran)
            self.assertTrue(any("write failed" in error for error in result.validation_errors))

    def test_successful_create_and_edit_run_all_relevant_validators(self):
        with TemporaryDirectory() as directory:
            root = Path(directory)
            self.repository(root)
            self.add_dependencies(root)
            create = preview_change(
                root,
                "create",
                "formal_short",
                self.source(),
                same_semantic_owner=False,
                fact_safe=True,
                write_capable=True,
            )

            with patch.object(validate_v1, "run", wraps=validate_v1.run) as core:
                with patch.object(validate_prompts, "run", wraps=validate_prompts.run) as prompts:
                    with patch.object(validate_public, "run", wraps=validate_public.run) as public:
                        created = apply_change(root, create, create.confirmation_digest)

            self.assertTrue(created.success, created.validation_errors)
            core.assert_called_once_with(root.resolve(), "core")
            prompts.assert_called_once_with(root.resolve())
            public.assert_called_once_with(root.resolve())

            edit = preview_change(
                root,
                "edit",
                "formal_short",
                self.source(extra="formats: []\n"),
                same_semantic_owner=True,
                fact_safe=True,
                write_capable=True,
            )
            edited = apply_change(root, edit, edit.confirmation_digest)
            self.assertTrue(edited.success, edited.validation_errors)

    def test_post_write_validation_failure_is_explicit_and_recoverable(self):
        with TemporaryDirectory() as directory:
            root = Path(directory)
            self.repository(root)
            self.add_dependencies(root)
            private_marker = "mrAlishah/" + "obsidian-ai-context-source-of-truth"
            proposal = preview_change(
                root,
                "create",
                "formal_short",
                self.source(extra=f"# repository: {private_marker}\n"),
                same_semantic_owner=False,
                fact_safe=True,
                write_capable=True,
            )

            result = apply_change(root, proposal, proposal.confirmation_digest)

            self.assertTrue(result.write_applied)
            self.assertTrue(result.validation_ran)
            self.assertFalse(result.validation_passed)
            self.assertFalse(result.success)
            self.assertEqual(proposal.diff, result.diff)
            self.assertTrue((root / result.affected_path).is_file())


if __name__ == "__main__":
    unittest.main()
