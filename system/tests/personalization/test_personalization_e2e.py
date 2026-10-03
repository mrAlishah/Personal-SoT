from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from system.personalization.advisor import PersonalizationIntent, recommend
from system.personalization.explorer import CapabilityQuery, search
from system.personalization.profile_builder import (
    ProfileAssessment,
    apply_change,
    choose_profile_action,
    preview_change,
)


class PersonalizationEndToEndTests(unittest.TestCase):
    def repository(self, root: Path) -> None:
        for name in ("workspace/profiles", "system/routing", "system/behavior", "guides"):
            (root / name).mkdir(parents=True)
        (root / "system/behavior/reasoning.md").write_text("# reasoning\n", encoding="utf-8")
        (root / "system/behavior/module_catalog.md").write_text(
            "# modules\n\n## reasoning.md\n", encoding="utf-8"
        )
        (root / "system/routing/switch_registry.md").write_text(
            "# registry\n\n"
            "## tones\n\n```text\nformal → workspace/presentation/tones/formal.md\n```\n\n"
            "## depths\n\n```text\nshort → workspace/presentation/depth/short.md\n```\n",
            encoding="utf-8",
        )
        tone = root / "workspace/presentation/tones/formal.md"
        depth = root / "workspace/presentation/depth/short.md"
        tone.parent.mkdir(parents=True)
        depth.parent.mkdir(parents=True)
        tone.write_text("# formal\n", encoding="utf-8")
        depth.write_text("# short\n", encoding="utf-8")

    def source(self, depth: str = "short") -> str:
        return (
            "---\n"
            "behaviors:\n"
            "  - reasoning\n"
            "tone: formal\n"
            f"depth: {depth}\n"
            "---\n"
        )

    def test_beginner_discover_compose_preview_write_rediscover_edit_and_stale_flow(self):
        with TemporaryDirectory() as directory:
            root = Path(directory)
            self.repository(root)

            discovered = search(root, CapabilityQuery(text="formal short", limit=5))
            self.assertEqual(
                {("tone", "formal"), ("depth", "short")},
                {(match.lane, match.identity) for match in discovered.matches},
            )
            composition = recommend(root, PersonalizationIntent(tone="formal", depth="short"))
            self.assertEqual("compose", composition.action)
            self.assertFalse(composition.profile_creation_eligible)

            reusable = recommend(
                root,
                PersonalizationIntent(
                    tone="formal",
                    depth="short",
                    behaviors=("reasoning",),
                    reusable=True,
                ),
            )
            self.assertTrue(reusable.profile_creation_eligible)
            self.assertEqual(("create", None), choose_profile_action(ProfileAssessment(reusable=True)))

            preview_only = preview_change(
                root,
                "create",
                "formalshortreasoning",
                self.source(),
                same_semantic_owner=False,
                fact_safe=True,
                write_capable=False,
            )
            unavailable_write = apply_change(root, preview_only, preview_only.confirmation_digest)
            self.assertFalse(unavailable_write.write_applied)
            self.assertFalse(unavailable_write.validation_ran)

            local = preview_change(
                root,
                "create",
                "formalshortreasoning",
                self.source(),
                same_semantic_owner=False,
                fact_safe=True,
                write_capable=True,
            )
            created = apply_change(root, local, local.confirmation_digest)
            self.assertTrue(created.success, created.validation_errors)

            rediscovered = search(
                root,
                CapabilityQuery(identity="formalshortreasoning", lanes=("profile",), limit=1),
            )
            self.assertEqual("formalshortreasoning", rediscovered.matches[0].identity)

            edit = preview_change(
                root,
                "edit",
                "formalshortreasoning",
                self.source().replace("tone: formal", "formats: []\ntone: formal"),
                same_semantic_owner=True,
                fact_safe=True,
                write_capable=True,
            )
            self.assertTrue(apply_change(root, edit, edit.confirmation_digest).success)

            stale = preview_change(
                root,
                "edit",
                "formalshortreasoning",
                self.source(),
                same_semantic_owner=True,
                fact_safe=True,
                write_capable=True,
            )
            target = root / stale.target
            target.write_text(self.source().replace("tone: formal", "tone: neutral"), encoding="utf-8")
            stale_result = apply_change(root, stale, stale.confirmation_digest)
            self.assertFalse(stale_result.write_applied)
            self.assertIn("tone: neutral", target.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
