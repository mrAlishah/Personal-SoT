import unittest

from system.connectors.source import SourceBinding, Provenance, SourceSession, Snapshot, SourceUnavailable
from system.tests.connectors.test_source_access import Transport, ATOM


class ContractAlignmentTests(unittest.TestCase):
    def setUp(self):
        self.transport = Transport()
        self.session = SourceSession(self.transport)

    def test_mapping_is_not_successful_resolution(self):
        self.transport.available = False
        result = self.session.reanchor()
        self.assertFalse(result.success)
        self.assertEqual('source_unavailable', result.failure)
        self.assertIsNone(result.provenance)

    def test_missing_or_ambiguous_binding_does_not_probe(self):
        for binding in (None, ['one', 'two'], SourceBinding('')):
            self.transport.binding = binding
            self.transport.resolve = lambda: self.fail('ambiguous binding was probed')
            result = SourceSession(self.transport).reanchor()
            self.assertEqual('source_unresolved', result.failure)

    def test_external_result_cannot_replace_selected_source(self):
        self.transport.resolve = lambda: Snapshot('other/instance', 'a' * 40, True)
        self.assertEqual('source_unresolved', self.session.reanchor().failure)
        self.assertEqual([], self.transport.reads)

    def test_typed_provenance_reports_actual_scope_selector_revision(self):
        self.assertTrue(self.session.reanchor().success)
        result = self.session.lookup('personal', 'goals.md')
        self.assertEqual(Provenance('example/instance', 'main', 'a' * 40,
                                    'personal', ATOM), result.provenance)
        self.assertFalse(result.write_applied or result.validation_ran or result.validation_passed)

    def test_classifiable_failures_remain_value_free(self):
        for reason in ('source_unavailable', 'source_unauthorized', 'source_unresolved',
                       'capability_unavailable', 'partial_coverage'):
            def fail():
                raise SourceUnavailable(reason=reason)
            self.transport.resolve = fail
            result = self.session.reanchor()
            self.assertEqual(reason, result.failure)
            self.assertEqual('', result.content)
            self.assertIsNone(result.provenance)

    def test_changed_revision_is_resolved_without_reusing_old_facts(self):
        self.session.reanchor()
        self.assertIn('Current goal', self.session.lookup('personal', 'goals.md').content)
        self.transport.revision = 'b' * 40
        self.transport.files[ATOM] = '---\nai_access: allow\n---\nChanged goal'
        result = self.session.lookup('personal', 'goals.md')
        self.assertIn('Changed goal', result.content)
        self.assertEqual('b' * 40, result.provenance.resolved_revision)

    def test_no_revision_rereads_and_never_fabricates_freshness(self):
        self.transport.revision = None
        self.session.reanchor()
        first = self.session.lookup('personal', 'goals.md')
        self.transport.files[ATOM] = '---\nai_access: allow\n---\nNew unversioned goal'
        second = self.session.lookup('personal', 'goals.md')
        self.assertIsNone(second.provenance.resolved_revision)
        self.assertNotEqual(first.content, second.content)
        self.assertTrue(second.provenance.warnings)

    def test_partial_requested_atom_is_a_limitation_not_absence(self):
        self.session.reanchor()
        original = self.transport.read
        def read(snapshot, path, **kwargs):
            if path == ATOM:
                raise SourceUnavailable(reason='partial_coverage')
            return original(snapshot, path, **kwargs)
        self.transport.read = read
        result = self.session.lookup('personal', 'goals.md')
        self.assertEqual('partial_coverage', result.failure)
        self.assertNotIn('not found', result.message)
        self.assertEqual('', result.content)


if __name__ == '__main__':
    unittest.main()
