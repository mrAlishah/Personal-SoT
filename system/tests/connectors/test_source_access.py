import unittest

from system.connectors.source import SourceSession, Snapshot, SourceUnavailable


ENTRY = 'workspace/adapters/runtime_entrypoint.md'
ATOM = 'workspace/context/personal/goals.md'


class Transport:
    def __init__(self):
        self.revision = 'a' * 40
        self.available = True
        self.private = True
        self.reads = []
        self.files = {
            ENTRY: 'runtime_contract: system/adapters/runtime_bootstrap.md\n',
            'system/adapters/runtime_bootstrap.md': '# runtime',
            'system/routing/context_registry.md': '```text\npersonal\n→ workspace/context/personal/\n```\n',
            ATOM: '---\nai_access: allow\n---\nCurrent goal',
        }

    def resolve(self):
        if not self.available:
            raise SourceUnavailable('private internal failure')
        return Snapshot('example/instance', self.revision, self.private)

    def read(self, snapshot, path, *, metadata_only=False):
        self.reads.append((path, metadata_only))
        if path not in self.files:
            raise SourceUnavailable('private missing path')
        text = self.files[path]
        if metadata_only:
            return text[:text.find('\n---', 3) + 4]
        return text


class SourceTests(unittest.TestCase):
    def setUp(self):
        self.transport = Transport()
        self.session = SourceSession(self.transport)
        self.assertTrue(self.session.reanchor().success)
        self.transport.reads.clear()

    def lookup(self, **kwargs):
        return self.session.lookup('personal', 'goals.md', **kwargs)

    def test_current_owner_lookup_with_provenance(self):
        result = self.lookup()
        self.assertTrue(result.success)
        self.assertIn('Current goal', result.content)
        self.assertEqual(('example/instance', 'a' * 40, ATOM), result.provenance)

    def test_unavailable_source_invalidates_prior_state(self):
        self.transport.available = False
        result = self.session.reanchor()
        self.assertFalse(result.success)
        self.assertFalse(self.lookup().success)
        self.assertNotIn('private', repr(result))

    def test_denied_does_not_read_body_or_disclose_provenance(self):
        self.transport.files[ATOM] = '---\nai_access: deny\n---\nDENIED_CANARY'
        result = self.lookup()
        self.assertFalse(result.success)
        self.assertEqual('', result.content)
        self.assertIsNone(result.provenance)
        self.assertEqual([(ATOM, True)], self.transport.reads[-1:])
        self.assertNotIn((ATOM, False), self.transport.reads)
        self.assertNotIn('DENIED_CANARY', repr(result))

    def test_restricted_requires_authorization(self):
        self.transport.files[ATOM] = '---\nai_access: restricted\n---\nRestricted goal'
        self.assertFalse(self.lookup().success)
        self.assertNotIn((ATOM, False), self.transport.reads)

    def test_authorized_restricted_loads_only_needed_atom(self):
        self.transport.files[ATOM] = '---\nai_access: restricted\n---\nRestricted goal'
        self.session = SourceSession(self.transport, personal_owner=True)
        self.session.reanchor()
        self.transport.reads.clear()
        self.assertTrue(self.lookup().success)
        bodies = [path for path, metadata in self.transport.reads if not metadata]
        self.assertEqual(['system/routing/context_registry.md', ATOM], bodies)

    def test_reanchor_refreshes_prior_negative_lookup(self):
        del self.transport.files[ATOM]
        self.assertFalse(self.lookup().success)
        self.transport.revision = 'b' * 40
        self.transport.files[ATOM] = '---\nai_access: allow\n---\nNew goal'
        self.assertTrue(self.session.reanchor('@do:sot').success)
        result = self.lookup()
        self.assertIn('New goal', result.content)
        self.assertEqual('b' * 40, result.provenance[1])

    def test_memory_is_not_a_lookup_input_or_fallback(self):
        memory = 'Old goal'
        self.assertNotEqual(memory, self.lookup().content)
        self.transport.available = False
        self.session.reanchor()
        self.assertEqual('', self.lookup().content)

    def test_narrow_request_never_reads_siblings(self):
        self.transport.files['workspace/context/personal/identity.md'] = 'PRIVATE_OTHER'
        self.lookup()
        self.assertFalse(any('identity.md' in path for path, _ in self.transport.reads))

    def test_read_only_never_claims_write_or_validation(self):
        result = self.lookup()
        self.assertFalse(result.write_applied)
        self.assertFalse(result.validation_ran)
        self.assertFalse(result.validation_passed)

    def test_secret_content_is_not_returned(self):
        self.transport.files[ATOM] = '---\nai_access: allow\n---\napi_' + 'token: fake_canary'
        result = self.lookup()
        self.assertFalse(result.success)
        self.assertEqual('', result.content)
        self.assertNotIn('fake_canary', repr(result))

    def test_invalid_path_and_scope_do_not_fetch_atom(self):
        for atom in ('../goals.md', '/goals.md', 'nested/../../goals.md'):
            self.assertFalse(self.session.lookup('personal', atom).success)
        self.assertFalse(self.session.lookup('unknown', 'goals.md').success)
        self.assertNotIn((ATOM, False), self.transport.reads)


if __name__ == '__main__':
    unittest.main()
