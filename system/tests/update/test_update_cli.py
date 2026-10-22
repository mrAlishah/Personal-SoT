from io import StringIO
from pathlib import Path
import tempfile
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

    def test_guided_conflicts_choose_public_private_and_reconfirm(self):
        blocked = WorkflowResult(
            'git', 'initial-digest', False, False,
            BeginnerReport('Update needs a decision.'), failure='conflict')
        chosen = WorkflowResult(
            'git', 'chosen-digest', False, False,
            BeginnerReport('Ready to preview this update.'),
            confirmation_required=True)
        applied = WorkflowResult(
            'git', 'chosen-digest', True, True,
            BeginnerReport('Update applied and validation passed.'))
        plan = mock.Mock(blocked=None,
                         conflict=('system/contract.md', 'workspace/secret-project.md'))
        digest = mock.Mock(digest='initial-digest')
        prompts = []
        answers = iter(['y', 'p', 'k', 'y'])
        def answer(prompt):
            prompts.append(prompt)
            return next(answers)
        output = StringIO()
        with mock.patch.object(cli, 'run_update_workflow',
                               side_effect=[blocked, chosen, applied]) as workflow, \
             mock.patch.object(cli.git_update, 'classify', return_value=plan), \
             mock.patch.object(cli.git_update, 'preview', return_value=digest):
            rc = cli.run_interactive('.', input_fn=answer, out=output,
                                     private_sync=False)
        self.assertEqual(0, rc)
        choices = {'system/contract.md': 'public',
                   'workspace/secret-project.md': 'private'}
        self.assertEqual(choices, workflow.call_args_list[1].kwargs['resolutions'])
        self.assertEqual(choices, workflow.call_args_list[2].kwargs['resolutions'])
        self.assertEqual('chosen-digest', workflow.call_args_list[2].kwargs['confirm_digest'])
        self.assertEqual(4, len(prompts))
        self.assertNotIn('secret-project', output.getvalue() + ''.join(prompts))
        self.assertIn('workspace', ''.join(prompts))

    def test_conflict_cancellation_is_nonmutating(self):
        blocked = WorkflowResult('git', 'one', False, False,
                                  BeginnerReport('Conflict.'), failure='conflict')
        plan = mock.Mock(blocked=None, conflict=('system/a.md',))
        digest = mock.Mock(digest='one')
        output = StringIO()
        with mock.patch.object(cli, 'run_update_workflow', return_value=blocked) as workflow, \
             mock.patch.object(cli.git_update, 'classify', return_value=plan), \
             mock.patch.object(cli.git_update, 'preview', return_value=digest):
            rc = cli.run_interactive('.', input_fn=lambda _: 'n', out=output)
        self.assertEqual(0, rc)
        self.assertEqual(1, workflow.call_count)
        self.assertIn('Nothing was changed.', output.getvalue())

    def test_stale_resolved_preview_discards_choices(self):
        blocked = WorkflowResult('git', 'one', False, False,
                                  BeginnerReport('Conflict.'), failure='conflict')
        chosen = WorkflowResult('git', 'two', False, False,
                                BeginnerReport('Preview.'), confirmation_required=True)
        stale = WorkflowResult('git', 'three', False, False,
                               BeginnerReport('Stale.'), failure='stale_state',
                               confirmation_required=True)
        refreshed = WorkflowResult('git', None, False, False,
                                   BeginnerReport('Update blocked.'), failure='source_unavailable')
        plan = mock.Mock(blocked=None, conflict=('system/a.md',))
        digest = mock.Mock(digest='one')
        answers = iter(['y', 'p', 'y'])
        with mock.patch.object(cli, 'run_update_workflow',
                               side_effect=[blocked, chosen, stale, refreshed]) as workflow, \
             mock.patch.object(cli.git_update, 'classify', return_value=plan), \
             mock.patch.object(cli.git_update, 'preview', return_value=digest):
            rc = cli.run_interactive('.', input_fn=lambda _: next(answers),
                                     out=StringIO(), private_sync=False)
        self.assertEqual(2, rc)
        self.assertNotIn('resolutions', workflow.call_args_list[3].kwargs)

    def test_failure_code_is_visible_and_sanitized(self):
        failure = WorkflowResult('git', None, False, False,
                                 BeginnerReport('Update not applied.'),
                                 failure='object_transfer_failed')
        output = StringIO()
        cli._render(failure, output)
        self.assertIn('failure_code: object_transfer_failed', output.getvalue())
        unsafe = WorkflowResult('git', None, False, False,
                                BeginnerReport('Failed.'),
                                failure='private/path or token')
        output = StringIO()
        cli._render(unsafe, output)
        self.assertIn('failure_code: unknown', output.getvalue())
        self.assertNotIn('private/path', output.getvalue())

    def test_verbose_stage_callback_and_failure(self):
        def fake_workflow(*args, **kwargs):
            kwargs['stage_callback']('candidate_validation', 'started')
            kwargs['stage_callback']('candidate_validation', 'failed')
            return WorkflowResult('git', None, False, False,
                                  BeginnerReport('Update not applied.'),
                                  failure='validation_failed')

        output = StringIO()
        with mock.patch.object(cli, 'run_update_workflow', side_effect=fake_workflow):
            rc = cli.run_non_interactive('.', out=output, verbose=True)
        self.assertEqual(2, rc)
        self.assertIn('stage: candidate_validation = failed', output.getvalue())
        self.assertIn('failure_code: validation_failed', output.getvalue())

    def test_logging_inside_installation_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            with mock.patch.object(cli, 'run_interactive') as interactive:
                rc = cli.main(['--root', str(root),
                               '--log-file', str(root / 'update.log')])
            self.assertEqual(2, rc)
            interactive.assert_not_called()
            self.assertFalse((root / 'update.log').exists())

    def test_log_file_captures_safe_diagnostics(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / 'installed'
            root.mkdir()
            log_path = Path(directory) / 'trace.log'
            blocked = WorkflowResult('git', None, False, False,
                                     BeginnerReport('Update not applied.'),
                                     failure='object_transfer_failed')
            with mock.patch.object(cli, 'run_update_workflow', return_value=blocked):
                rc = cli.main(['--root', str(root), '--preview',
                               '--log-file', str(log_path)])
            self.assertEqual(2, rc)
            self.assertIn('failure_code: object_transfer_failed',
                          log_path.read_text(encoding='utf-8'))

    def test_ready_git_update_can_sync_private_origin_with_confirmation(self):
        ready = WorkflowResult(
            'git', 'digest-1', True, True,
            BeginnerReport('Update applied and validation passed.'),
        )
        outcome = mock.Mock(status='synchronized', failure=None,
                            rollback_completed=None)
        output = StringIO()
        answers = iter(['yes'])
        with mock.patch.object(cli, 'run_update_workflow', return_value=ready), \
             mock.patch.object(cli, 'private_origin_url',
                               return_value='https://github.com/A/myPersonal-SoT.git'), \
             mock.patch.object(cli, 'synchronize', return_value=outcome) as sync:
            rc = cli.run_interactive(
                '.', input_fn=lambda _prompt: next(answers), out=output)
        self.assertEqual(0, rc)
        sync.assert_called_once()
        self.assertIn('origin/main synchronized', output.getvalue())

    def test_declined_private_sync_leaves_local_success_untouched(self):
        ready = WorkflowResult(
            'git', 'digest-1', True, True,
            BeginnerReport('Update applied and validation passed.'),
        )
        with mock.patch.object(cli, 'run_update_workflow', return_value=ready), \
             mock.patch.object(cli, 'private_origin_url',
                               return_value='https://github.com/A/myPersonal-SoT.git'), \
             mock.patch.object(cli, 'synchronize') as sync:
            rc = cli.run_interactive('.', input_fn=lambda _prompt: 'n', out=StringIO())
        self.assertEqual(0, rc)
        sync.assert_not_called()

    def test_local_only_does_not_probe_private_origin(self):
        ready = WorkflowResult(
            'git', 'digest-1', True, True,
            BeginnerReport('Update applied and validation passed.'),
        )
        with mock.patch.object(cli, 'run_update_workflow', return_value=ready), \
             mock.patch.object(cli, 'private_origin_url') as origin:
            rc = cli.run_interactive('.', out=StringIO(), private_sync=False)
        self.assertEqual(0, rc)
        origin.assert_not_called()

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
