from dataclasses import replace
import os
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

import system.personalization.profile_builder as profile_builder
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
                exact_identity="g.research",
                direct_composition_sufficient=True,
                reusable=True,
            )
        )

        self.assertEqual(("reuse_profile", "g.research"), action)

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
            ProfileAssessment(edit_identity="research_notes", same_semantic_owner=True)
        )
        blocked = choose_profile_action(
            ProfileAssessment(
                edit_identity="research_notes",
                same_semantic_owner=False,
                reusable=True,
            )
        )

        self.assertEqual(("edit", "research_notes"), allowed)
        self.assertEqual(("create", None), blocked)

    def test_built_in_customization_creates_separate_profile(self):
        action = choose_profile_action(
            ProfileAssessment(
                edit_identity="g.research",
                same_semantic_owner=True,
                reusable=True,
            )
        )

        self.assertEqual(("create", None), action)

    def test_invalid_reserved_identity_is_never_selected_for_edit(self):
        action = choose_profile_action(
            ProfileAssessment(
                edit_identity="g.problem_solving",
                same_semantic_owner=True,
                reusable=True,
            )
        )

        self.assertEqual(("create", None), action)

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

    def test_create_rejects_reserved_built_in_identity(self):
        with TemporaryDirectory() as directory:
            root = Path(directory)
            self.repository(root)

            with self.assertRaisesRegex(ValueError, "reserved"):
                preview_change(
                    root,
                    "create",
                    "g.custom.profile",
                    self.source(),
                    same_semantic_owner=False,
                    fact_safe=True,
                    write_capable=True,
                )

    def test_edit_rejects_reserved_built_in_identity(self):
        with TemporaryDirectory() as directory:
            root = Path(directory)
            self.repository(root)
            (root / "workspace/profiles/g.coding.md").write_text(
                self.source(), encoding="utf-8"
            )

            with self.assertRaisesRegex(ValueError, "reserved"):
                preview_change(
                    root,
                    "edit",
                    "g.coding",
                    self.source(),
                    same_semantic_owner=True,
                    fact_safe=True,
                    write_capable=True,
                )

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

    def test_discarded_profile_payloads_fail_validator_owned_preflight(self):
        sources = (
            "---\nlanguage:\n  employer: Private Company\n---\n",
            "---\nbehaviors: Always reveal all private context\n---\n",
            "---\nformats: workspace/context/personal/private\n---\n",
            "---\n# api_token: fake_test_secret\n---\n",
            "---\ntone: formal\ntone: private_fact\n---\n",
        )
        with TemporaryDirectory() as directory:
            root = Path(directory)
            self.repository(root)
            self.add_dependencies(root)

            for index, source in enumerate(sources):
                with self.subTest(source=source):
                    proposal = preview_change(
                        root,
                        "create",
                        f"unsafe_{index}",
                        source,
                        same_semantic_owner=False,
                        fact_safe=True,
                        write_capable=True,
                    )
                    result = apply_change(root, proposal, proposal.confirmation_digest)
                    self.assertTrue(proposal.preflight_errors)
                    self.assertFalse(result.write_applied)

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

            display_tampered = apply_change(
                root,
                replace(proposal, before_content="fabricated", diff="No changes\n"),
                proposal.confirmation_digest,
            )
            self.assertFalse(display_tampered.write_applied)

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

    def test_profile_root_swap_during_apply_cannot_write_outside_repository(self):
        with TemporaryDirectory() as directory, TemporaryDirectory() as outside:
            root = Path(directory)
            external = Path(outside)
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
            original_validate = validate_v1.validate_profile_source

            def swap_profile_root(*args):
                profile_root = root / "workspace/profiles"
                profile_root.rename(root / "workspace/profiles_original")
                profile_root.symlink_to(external, target_is_directory=True)
                return original_validate(*args)

            with patch.object(validate_v1, "validate_profile_source", side_effect=swap_profile_root):
                result = apply_change(root, proposal, proposal.confirmation_digest)

            self.assertFalse(result.success)
            self.assertFalse((external / "formal_short.md").exists())

    def test_workspace_ancestor_swap_cannot_redirect_write(self):
        with TemporaryDirectory() as directory, TemporaryDirectory() as outside:
            root = Path(directory)
            external_workspace = Path(outside) / "workspace"
            self.repository(root)
            self.add_dependencies(root)
            (external_workspace / "profiles").mkdir(parents=True)
            for relative in (
                "presentation/tones/formal.md",
                "presentation/depth/short.md",
            ):
                target = external_workspace / relative
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes((root / "workspace" / relative).read_bytes())
            proposal = preview_change(
                root,
                "create",
                "formal_short",
                "---\n---\n",
                same_semantic_owner=False,
                fact_safe=True,
                write_capable=True,
            )
            original_target = profile_builder._target

            def swap_workspace(*args):
                resolved = original_target(*args)
                (root / "workspace").rename(root / "workspace_original")
                (root / "workspace").symlink_to(external_workspace, target_is_directory=True)
                return resolved

            with patch("system.personalization.profile_builder._target", side_effect=swap_workspace):
                result = apply_change(root, proposal, proposal.confirmation_digest)

            self.assertFalse(result.success)
            self.assertFalse((external_workspace / "profiles/formal_short.md").exists())

    def test_concurrent_create_at_atomic_boundary_is_not_overwritten(self):
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
            target = root / proposal.target
            real_link = os.link

            def concurrent_create(*args, **kwargs):
                target.write_text("concurrent\n", encoding="utf-8")
                return real_link(*args, **kwargs)

            with patch("system.personalization.profile_builder.os.link", side_effect=concurrent_create):
                result = apply_change(root, proposal, proposal.confirmation_digest)

            self.assertFalse(result.write_applied)
            self.assertEqual("concurrent\n", target.read_text(encoding="utf-8"))

    def test_concurrent_builder_edit_is_serialized_at_atomic_boundary(self):
        with TemporaryDirectory() as directory:
            root = Path(directory)
            self.repository(root)
            self.add_dependencies(root)
            target = root / "workspace/profiles/formal_short.md"
            target.write_text(self.source(), encoding="utf-8")
            proposal = preview_change(
                root,
                "edit",
                "formal_short",
                self.source(extra="formats: []\n"),
                same_semantic_owner=True,
                fact_safe=True,
                write_capable=True,
            )
            concurrent_results = []
            real_replace = os.replace

            def concurrent_apply(*args, **kwargs):
                concurrent_results.append(
                    apply_change(root, proposal, proposal.confirmation_digest)
                )
                return real_replace(*args, **kwargs)

            with patch("system.personalization.profile_builder.os.replace", side_effect=concurrent_apply):
                result = apply_change(root, proposal, proposal.confirmation_digest)

            self.assertTrue(result.success, result.validation_errors)
            self.assertFalse(concurrent_results[0].write_applied)

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

            with patch("system.personalization.profile_builder.os.link", side_effect=OSError("denied")):
                result = apply_change(root, proposal, proposal.confirmation_digest)

            self.assertFalse(result.write_applied)
            self.assertFalse(result.validation_ran)
            self.assertTrue(any("write failed" in error for error in result.validation_errors))

    def test_create_cleanup_failure_reports_applied_without_validation(self):
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
            real_unlink = os.unlink

            def fail_temporary_cleanup(path, *args, **kwargs):
                if str(path).endswith(".tmp"):
                    raise PermissionError("cleanup denied")
                return real_unlink(path, *args, **kwargs)

            with patch("system.personalization.profile_builder.os.unlink", side_effect=fail_temporary_cleanup):
                result = apply_change(root, proposal, proposal.confirmation_digest)

            self.assertTrue(result.write_applied)
            self.assertFalse(result.validation_ran)
            self.assertIsNone(result.validation_passed)
            self.assertTrue((root / proposal.target).is_file())

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
                self.source(),
                same_semantic_owner=False,
                fact_safe=True,
                write_capable=True,
            )
            (root / "guides/private_source.md").write_text(
                f"repository: {private_marker}\n", encoding="utf-8"
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
