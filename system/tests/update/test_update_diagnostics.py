"""Safe Update diagnostics must report stages without changing update semantics."""
import unittest
from unittest import mock

from system.assistant import update_reporting
from system.update import git_update


class UpdateDiagnosticTests(unittest.TestCase):
    def test_stale_apply_is_unchanged_if_diagnostic_sink_raises(self):
        plan = git_update.Plan('a' * 40, 'b' * 40, 'a' * 40,
                               upstream_only=('system/example.py',))
        preview = git_update.Preview('correct', plan, {})

        def broken_sink(*_args):
            raise RuntimeError('simulated diagnostic failure')

        with mock.patch.object(git_update, 'classify', return_value=plan), \
             mock.patch.object(git_update, 'preview', return_value=preview):
            result = git_update.apply('.', plan, 'stale', on_stage=broken_sink)

        self.assertEqual('stale_state', result.failure)
        self.assertFalse(result.mutation_started)

    def test_blocked_classification_exposes_failure_code(self):
        plan = git_update.Plan('', '', None, blocked='dirty_or_untracked')
        preview = git_update.Preview('digest', plan, {})
        stages = []
        capability = update_reporting.HostCapability(True, True, True)

        with mock.patch.object(git_update, 'classify', return_value=plan), \
             mock.patch.object(git_update, 'preview', return_value=preview):
            result = update_reporting._git_workflow(
                '.', capability, None, lambda stage, status: stages.append((stage, status)))

        self.assertEqual('dirty_or_untracked', result.failure)
        self.assertFalse(result.confirmation_required)
        self.assertEqual([('classification', 'started'), ('classification', 'blocked')], stages)

    def test_transfer_failure_reports_precise_stage_without_raw_output(self):
        plan = git_update.Plan('a' * 40, 'b' * 40, 'a' * 40,
                               upstream_only=('system/example.py',))
        preview = git_update.Preview('digest', plan, {'hidden_by_area': {}})
        stages = []
        capability = update_reporting.HostCapability(True, True, True)

        def failing_apply(root, plan, digest, *, on_stage):
            on_stage('object_transfer', 'started')
            on_stage('object_transfer', 'failed')
            return git_update.ApplyResult(
                validation_ran=True, validation_passed=True,
                failure='object_transfer_failed')

        with mock.patch.object(git_update, 'classify', return_value=plan), \
             mock.patch.object(git_update, 'preview', return_value=preview), \
             mock.patch.object(git_update, 'apply', side_effect=failing_apply):
            result = update_reporting._git_workflow(
                '.', capability, 'digest', lambda stage, status: stages.append((stage, status)))

        self.assertFalse(result.applied)
        self.assertEqual('object_transfer_failed', result.failure)
        self.assertIn(('object_transfer', 'failed'), stages)
        self.assertEqual(('apply', 'failed'), stages[-1])

    def test_reporting_callback_error_does_not_change_decision(self):
        def broken_sink(*_args):
            raise OSError('simulated output failure')

        update_reporting._trace(broken_sink, 'apply', 'started')


if __name__ == '__main__':
    unittest.main()
