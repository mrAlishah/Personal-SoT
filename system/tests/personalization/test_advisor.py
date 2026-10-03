from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from system.personalization.advisor import PersonalizationIntent, recommend


ROOT = Path(__file__).resolve().parents[3]


class PersonalizationAdvisorTests(unittest.TestCase):
    def test_formal_short_uses_direct_composition_without_profile_creation(self):
        result = recommend(ROOT, PersonalizationIntent(tone="formal", depth="short"))

        self.assertEqual("compose", result.action)
        self.assertEqual((), result.profiles)
        self.assertEqual("formal", result.tone)
        self.assertEqual("short", result.depth)
        self.assertFalse(result.profile_creation_eligible)

    def test_compare_remains_format_owned(self):
        result = recommend(
            ROOT,
            PersonalizationIntent(formats=("compare",)),
        )

        self.assertEqual("compose", result.action)
        self.assertEqual(("compare",), result.formats)
        self.assertEqual((), result.profiles)
        self.assertEqual((), result.behaviors)

    def test_step_by_step_learning_composes_profile_controls_and_behavior(self):
        result = recommend(
            ROOT,
            PersonalizationIntent(
                behaviors=("teaching",),
                controls=(("learning", "on"), ("step_execution", "on")),
            ),
        )

        self.assertEqual("compose", result.action)
        self.assertEqual(("g.technical.learning",), result.profiles)
        self.assertEqual(("teaching",), result.behaviors)
        self.assertEqual(
            (("learning", "on"), ("step_execution", "on")),
            result.controls,
        )

    def test_deep_professional_research_reuses_existing_profile(self):
        result = recommend(
            ROOT,
            PersonalizationIntent(
                behaviors=("research",),
                tone="professional",
                depth="deep",
            ),
        )

        self.assertEqual("reuse_profile", result.action)
        self.assertEqual(("g.research",), result.profiles)
        self.assertFalse(result.profile_creation_eligible)

    def test_existing_behavior_profile_composes_requested_overrides_before_creation(self):
        result = recommend(
            ROOT,
            PersonalizationIntent(
                behaviors=("research",),
                tone="formal",
                depth="short",
                reusable=True,
            ),
        )

        self.assertEqual("compose", result.action)
        self.assertEqual(("g.research",), result.profiles)
        self.assertFalse(result.profile_creation_eligible)

    def test_exact_profile_reuse_is_not_lost_after_ten_unrelated_profiles(self):
        with TemporaryDirectory() as directory:
            root = Path(directory)
            for name in ("workspace/profiles", "workspace/presentation/tones", "workspace/presentation/depth", "system/routing", "system/behavior", "guides"):
                (root / name).mkdir(parents=True)
            (root / "system/routing/switch_registry.md").write_text(
                "# registry\n\n## tones\n\n```text\n"
                "formal → workspace/presentation/tones/formal.md\n"
                "professional → workspace/presentation/tones/professional.md\n```\n\n"
                "## depths\n\n```text\n"
                "short → workspace/presentation/depth/short.md\n"
                "deep → workspace/presentation/depth/deep.md\n```\n",
                encoding="utf-8",
            )
            for name in ("formal", "professional"):
                (root / f"workspace/presentation/tones/{name}.md").write_text(f"# {name}\n", encoding="utf-8")
            for name in ("short", "deep"):
                (root / f"workspace/presentation/depth/{name}.md").write_text(f"# {name}\n", encoding="utf-8")
            for index in range(10):
                (root / f"workspace/profiles/a_{index}.md").write_text(
                    "---\ntone: professional\ndepth: deep\n---\n", encoding="utf-8"
                )
            (root / "workspace/profiles/z_exact.md").write_text(
                "---\ntone: formal\ndepth: short\n---\n", encoding="utf-8"
            )

            result = recommend(
                root,
                PersonalizationIntent(tone="formal", depth="short", reusable=True),
            )

            self.assertEqual("reuse_profile", result.action)
            self.assertEqual(("z_exact",), result.profiles)
            self.assertFalse(result.profile_creation_eligible)

    def test_incomplete_profile_discovery_never_authorizes_creation(self):
        with TemporaryDirectory() as directory:
            root = Path(directory)
            for name in ("workspace/profiles", "workspace/presentation/tones", "workspace/presentation/depth", "system/routing", "system/behavior", "guides"):
                (root / name).mkdir(parents=True)
            (root / "system/routing/switch_registry.md").write_text(
                "# registry\n\n## tones\n\n```text\n"
                "formal → workspace/presentation/tones/formal.md\n```\n\n"
                "## depths\n\n```text\n"
                "short → workspace/presentation/depth/short.md\n```\n",
                encoding="utf-8",
            )
            (root / "workspace/presentation/tones/formal.md").write_text("# formal\n", encoding="utf-8")
            (root / "workspace/presentation/depth/short.md").write_text("# short\n", encoding="utf-8")
            for index in range(20):
                (root / f"workspace/profiles/a_{index:02}.md").write_text(
                    "---\ntone: formal\ndepth: short\n---\ninvalid body\n", encoding="utf-8"
                )
            (root / "workspace/profiles/z_exact.md").write_text(
                "---\ntone: formal\ndepth: short\n---\n", encoding="utf-8"
            )

            result = recommend(
                root,
                PersonalizationIntent(tone="formal", depth="short", reusable=True),
            )

            self.assertEqual((), result.profiles)
            self.assertFalse(result.profile_creation_eligible)

    def test_unknown_identity_is_unavailable_not_guessed(self):
        result = recommend(ROOT, PersonalizationIntent(tone="friendliest"))

        self.assertEqual("unavailable", result.action)
        self.assertEqual(("tone:friendliest",), result.unavailable)
        self.assertEqual((), result.profiles)

    def test_invalid_control_value_is_unavailable_not_coerced(self):
        result = recommend(
            ROOT,
            PersonalizationIntent(controls=(("learning", "enabled"),)),
        )

        self.assertEqual("unavailable", result.action)
        self.assertEqual(("control:learning=enabled",), result.unavailable)


if __name__ == "__main__":
    unittest.main()
