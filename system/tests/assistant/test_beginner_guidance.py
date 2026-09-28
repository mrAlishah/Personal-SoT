from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

from system.assistant.guidance import guide, improve
from system.personalization.advisor import PersonalizationIntent
from system.prompts.explorer import PromptQuery


ROOT = Path(__file__).resolve().parents[3]


class BeginnerGuidanceTests(unittest.TestCase):
    def test_uncertainty_asks_one_outcome_question_without_category_menu(self):
        result = guide(ROOT)
        self.assertEqual('Recommend', result.level)
        self.assertIsNotNone(result.question)
        self.assertEqual((), result.evidence)
        self.assertIsNone(result.workflow)
        self.assertIn("recommend", result.question.lower())

    def test_classified_shorter_intent_routes_without_category_input(self):
        result = guide(ROOT, personalization=PersonalizationIntent(depth='short'))
        self.assertEqual('Customize', result.category)
        self.assertEqual('short', result.composition.depth)
        self.assertIsNone(result.question)
        self.assertFalse(result.composition.profile_creation_eligible)

    def test_explain_does_not_propose_or_read_canonical_changes(self):
        with patch('system.assistant.guidance.recommend', side_effect=AssertionError('unneeded read')):
            result = guide(ROOT, explain_profile=True)
        self.assertEqual('Explain', result.level)
        self.assertIsNone(result.composition)
        self.assertIsNone(result.workflow)

    def test_project_route_comes_from_valid_existing_prompt_metadata(self):
        result = guide(ROOT, prompt_query=PromptQuery(prompt_tags=('project', 'creation')))
        self.assertEqual('Create', result.category)
        self.assertEqual('sot/create_project', result.workflow)
        self.assertEqual('Recommend', result.level)

    def test_try_before_save_keeps_even_reusable_intent_transient(self):
        result = guide(ROOT, personalization=PersonalizationIntent(tone='formal', depth='short', reusable=True))
        self.assertFalse(result.composition.profile_creation_eligible)
        self.assertIn('current task', result.next_action)

    def test_explicit_save_reuses_existing_profile_first(self):
        result = guide(ROOT, personalization=PersonalizationIntent(
            behaviors=('research',), tone='professional', depth='deep'), save_requested=True)
        self.assertEqual('reuse_profile', result.composition.action)
        self.assertEqual(('g.research',), result.composition.profiles)
        self.assertNotEqual('Preview', result.level)

    def test_missing_capability_does_not_invent_identity_or_workflow(self):
        result = guide(ROOT, personalization=PersonalizationIntent(tone='imaginary'))
        self.assertEqual('unavailable', result.composition.action)
        self.assertIsNotNone(result.question)

    def test_improvement_is_bounded_and_never_reads_factual_context(self):
        original = Path.read_text
        def guarded(path, *args, **kwargs):
            if 'context' in path.parts:
                self.fail('general improvement read factual context')
            return original(path, *args, **kwargs)
        with patch.object(Path, 'read_text', guarded):
            result = improve(ROOT, ('sot/assistant', 'sot/personalize'))
        self.assertLessEqual(len(result.evidence), 3)
        self.assertEqual('Recommend', result.level)
        self.assertIsNotNone(result.next_action)
        with self.assertRaises(ValueError):
            improve(ROOT, ('a', 'b', 'c', 'd'))

    def test_missing_workflow_reports_only_observed_gap(self):
        with TemporaryDirectory() as directory:
            result = improve(Path(directory), ('sot/assistant',))
        self.assertEqual(('unavailable:sot/assistant',), result.evidence)
        self.assertIn('check', result.next_action.lower())


if __name__ == '__main__':
    unittest.main()
