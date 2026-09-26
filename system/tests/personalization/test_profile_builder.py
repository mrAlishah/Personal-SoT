from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from system.personalization.profile_builder import (
    ProfileAssessment,
    choose_profile_action,
    preview_change,
)


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


if __name__ == "__main__":
    unittest.main()
