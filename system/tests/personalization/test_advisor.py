from pathlib import Path
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

    def test_comparison_table_remains_format_owned(self):
        result = recommend(
            ROOT,
            PersonalizationIntent(formats=("comparison_table",)),
        )

        self.assertEqual("compose", result.action)
        self.assertEqual(("comparison_table",), result.formats)
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
        self.assertEqual(("technical_learning",), result.profiles)
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
        self.assertEqual(("research",), result.profiles)
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
