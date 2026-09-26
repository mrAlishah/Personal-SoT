import unittest

from system.prompts.builder import ReuseAssessment, choose_action


class PromptBuilderReuseTests(unittest.TestCase):
    def test_exact_reuse_wins_before_every_other_option(self):
        assessment = ReuseAssessment(
            exact_identity="coding/review_pr",
            parameterized_identity="coding/review_generic",
            composition=("profile:coding",),
            edit_identity="coding/old_review",
            same_semantic_owner=True,
        )

        self.assertEqual(("reuse_exact", "coding/review_pr"), choose_action(assessment))

    def test_parameterized_reuse_wins_before_composition_or_creation(self):
        assessment = ReuseAssessment(
            parameterized_identity="coding/review_pr",
            composition=("profile:coding",),
        )

        self.assertEqual(
            ("reuse_parameterized", "coding/review_pr"),
            choose_action(assessment),
        )

    def test_composition_wins_before_edit_or_creation(self):
        assessment = ReuseAssessment(
            composition=("profile:coding", "tone:professional"),
            edit_identity="coding/review_pr",
            same_semantic_owner=True,
        )

        self.assertEqual(("compose", None), choose_action(assessment))

    def test_edit_requires_the_same_semantic_owner(self):
        assessment = ReuseAssessment(
            edit_identity="coding/review_pr",
            same_semantic_owner=True,
        )

        self.assertEqual(("edit", "coding/review_pr"), choose_action(assessment))

    def test_similarity_without_same_owner_never_authorizes_overwrite(self):
        assessment = ReuseAssessment(
            edit_identity="coding/review_pr",
            same_semantic_owner=False,
        )

        self.assertEqual(("create", None), choose_action(assessment))

    def test_create_is_last_resort(self):
        self.assertEqual(("create", None), choose_action(ReuseAssessment()))


if __name__ == "__main__":
    unittest.main()
