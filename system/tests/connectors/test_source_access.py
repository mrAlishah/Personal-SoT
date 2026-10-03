import unittest

from system.connectors.source import SourceBinding, Provenance, SourceSession, Snapshot, SourceUnavailable, safe_path
from system.validation.validate_v1 import RAW_SECRET_KEYS
from system.validation.validate_public import SECRET_KEYS


ENTRY = 'workspace/adapters/runtime_entrypoint.md'
ATOM = 'workspace/context/personal/goals.md'


class Transport:
    def __init__(self):
        self.binding = SourceBinding('example/instance', 'main')
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
        return Snapshot('example/instance', self.revision, self.private, selector='main')

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
        self.assertEqual(Provenance('example/instance', 'main', 'a' * 40, 'personal', ATOM), result.provenance)

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
        self.assertEqual('b' * 40, result.provenance.resolved_revision)

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

    def test_every_validator_owned_secret_key_is_blocked(self):
        for key in RAW_SECRET_KEYS | SECRET_KEYS:
            with self.subTest(key=key):
                self.transport.files[ATOM] = '---\nai_access: allow\n---\n' + key + ': SECRET_CANARY'
                result = self.lookup()
                self.assertFalse(result.success)
                self.assertEqual('', result.content)
                self.assertIsNone(result.provenance)

    def test_invalid_path_and_scope_do_not_fetch_atom(self):
        for atom in ('../goals.md', '/goals.md', 'nested/../../goals.md'):
            self.assertFalse(self.session.lookup('personal', atom).success)
        self.assertFalse(self.session.lookup('unknown', 'goals.md').success)
        self.assertNotIn((ATOM, False), self.transport.reads)

    def test_duplicate_or_cross_owner_registry_is_unavailable(self):
        registry = 'system/routing/context_registry.md'
        self.transport.files[registry] *= 2
        self.assertFalse(self.lookup().success)
        self.transport.files[registry] = '```\npersonal\n→ workspace/context/organizations/acme/\n```'
        self.assertFalse(self.lookup().success)
        self.assertNotIn((ATOM, True), self.transport.reads)

    def test_returned_body_cannot_override_denied_access(self):
        original_read = self.transport.read
        def read(snapshot, path, *, metadata_only=False):
            if path == ATOM and not metadata_only:
                return '---\nai_access: deny\n---\nBODY_CANARY'
            return original_read(snapshot, path, metadata_only=metadata_only)
        self.transport.read = read
        result = self.lookup()
        self.assertFalse(result.success)
        self.assertEqual('', result.content)

    def test_host_permission_revocation_stops_reads(self):
        self.session.host_read = False
        self.assertFalse(self.lookup().success)
        self.assertEqual([], self.transport.reads)

    def test_transport_paths_preserve_existing_profile_grammar(self):
        self.assertTrue(safe_path('workspace/profiles/architecture/review.md'))
        self.assertTrue(safe_path('workspace/profiles/customnotes.md'))
        self.assertFalse(safe_path('workspace/profiles/g/architecture_review.md'))
        self.assertFalse(safe_path('workspace/context/personal/g.architecture.review.md'))


if __name__ == '__main__':
    unittest.main()
