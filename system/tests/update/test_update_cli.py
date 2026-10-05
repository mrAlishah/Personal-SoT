from io import StringIO
import unittest
from unittest import mock

from system.assistant.update_reporting import BeginnerReport, WorkflowResult
from system.update import cli


class UpdateCliTests(unittest.TestCase):
    def test_normal_update_is_one_command_one_confirmation(self):
        preview = WorkflowResult(
            'git', 'digest-1', False, False,
            BeginnerReport('Ready to preview this update.'),
            confirmation_required=True,
        )
        applied = WorkflowResult(
            'git', 'digest-1', True, True,
            BeginnerReport('Update applied and validation passed.'),
        )
        answers = iter(['yes'])
        output = StringIO()

        with mock.patch.object(cli, 'run_update_workflow', side_effect=[preview, applied]) as workflow:
            rc = cli.run_interactive(
                '.', input_fn=lambda _prompt: next(answers), out=output)

        self.assertEqual(0, rc)
        self.assertEqual(2, workflow.call_count)
        self.assertIsNone(workflow.call_args_list[0].kwargs['confirm_digest'])
        self.assertEqual('digest-1', workflow.call_args_list[1].kwargs['confirm_digest'])
        self.assertIn('Update applied and validation passed.', output.getvalue())

    def test_stale_confirmation_refreshes_and_asks_again(self):
        preview = WorkflowResult(
            'git', 'digest-1', False, False,
            BeginnerReport('Ready to preview this update.'),
            confirmation_required=True,
        )
        refreshed = WorkflowResult(
            'git', 'digest-2', False, False,
            BeginnerReport(
                'The available update changed; review the refreshed preview before confirming.'),
            failure='stale_state',
            confirmation_required=True,
        )
        applied = WorkflowResult(
            'git', 'digest-2', True, True,
            BeginnerReport('Update applied and validation passed.'),
        )
        answers = iter(['yes', 'yes'])

        with mock.patch.object(
            cli, 'run_update_workflow', side_effect=[preview, refreshed, applied]
        ) as workflow:
            rc = cli.run_interactive(
                '.', input_fn=lambda _prompt: next(answers), out=StringIO())

        self.assertEqual(0, rc)
        self.assertEqual(3, workflow.call_count)
        self.assertEqual('digest-1', workflow.call_args_list[1].kwargs['confirm_digest'])
        self.assertEqual('digest-2', workflow.call_args_list[2].kwargs['confirm_digest'])

    def test_real_conflict_never_prompts_or_applies(self):
        blocked = WorkflowResult(
            'git', 'digest-1', False, False,
            BeginnerReport(
                'Nothing was changed. One or more local and update changes need a decision.'),
        )

        def should_not_prompt(_prompt):
            raise AssertionError('a blocked conflict must not ask for apply confirmation')

        with mock.patch.object(cli, 'run_update_workflow', return_value=blocked) as workflow:
            rc = cli.run_interactive('.', input_fn=should_not_prompt, out=StringIO())

        self.assertEqual(2, rc)
        self.assertEqual(1, workflow.call_count)

    def test_agent_preview_prints_exact_digest(self):
        preview = WorkflowResult(
            'git', 'digest-1', False, False,
            BeginnerReport('Ready to preview this update.'),
            confirmation_required=True,
        )
        output = StringIO()

        with mock.patch.object(cli, 'run_update_workflow', return_value=preview):
            rc = cli.run_non_interactive('.', out=output)

        self.assertEqual(0, rc)
        self.assertIn('confirmation_digest: digest-1', output.getvalue())


if __name__ == "__main__":
    unittest.main()
