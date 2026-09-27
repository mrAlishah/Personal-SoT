import base64
import hashlib
import json
from types import SimpleNamespace
import unittest

from system.connectors.github import GitHubSource
from system.connectors.source import SourceUnavailable


class GitHubTests(unittest.TestCase):
    def setUp(self):
        self.content = b'---\nai_access: deny\n---\nDENIED_CANARY'
        self.blob = hashlib.sha1(b'blob ' + str(len(self.content)).encode() + b'\0' + self.content).hexdigest()
        self.calls = []
        self.symlink = False
        self.truncated = False
        self.fail = False

    def runner(self, command, **kwargs):
        self.calls.append(command)
        route = command[-1]
        if self.fail:
            return SimpleNamespace(returncode=1, stdout='PRIVATE_ERROR')
        if route.endswith('/repos/example/instance'):
            value = dict(full_name='example/instance', private=True, default_branch='main')
        elif '/commits/' in route:
            value = dict(sha='a' * 40, commit=dict(tree=dict(sha='b' * 40)))
        elif '/trees/' in route:
            value = dict(truncated=self.truncated, tree=[
                dict(path='context.md', type='blob', mode='120000' if self.symlink else '100644', sha=self.blob)])
        else:
            value = dict(sha=self.blob, size=len(self.content), encoding='base64',
                         content=base64.b64encode(self.content).decode())
        return SimpleNamespace(returncode=0, stdout=json.dumps(value))

    def source(self):
        return GitHubSource('example/instance', runner=self.runner)

    def test_actual_resolution_and_metadata_only_result(self):
        source = self.source()
        snapshot = source.resolve()
        self.assertTrue(snapshot.private)
        self.assertEqual('a' * 40, snapshot.revision)
        value = source.read(snapshot, 'context.md', metadata_only=True)
        self.assertNotIn('DENIED_CANARY', value)
        self.assertIn('ai_access: deny', value)
        self.assertTrue(all('--hostname' in command for command in self.calls))

    def test_symlink_and_truncated_tree_fail_closed(self):
        source = self.source()
        snapshot = source.resolve()
        for flag in ('symlink', 'truncated'):
            setattr(self, flag, True)
            with self.assertRaises(SourceUnavailable):
                source.read(snapshot, 'context.md')
            setattr(self, flag, False)

    def test_transport_errors_are_sanitized(self):
        self.fail = True
        with self.assertRaises(SourceUnavailable) as raised:
            self.source().resolve()
        self.assertNotIn('PRIVATE_ERROR', str(raised.exception))

    def test_invalid_binding_and_path_are_rejected(self):
        with self.assertRaises(ValueError):
            GitHubSource('../other')
        source = self.source()
        snapshot = source.resolve()
        with self.assertRaises(SourceUnavailable):
            source.read(snapshot, '../context.md')


if __name__ == '__main__':
    unittest.main()
