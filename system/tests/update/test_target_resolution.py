from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import inspect
import os
from pathlib import Path
import subprocess
import tempfile
import threading
import unittest
from unittest import mock

from system.connectors.source import Snapshot, SourceUnavailable
from system.update import target


def _run(args, cwd=None):
    return subprocess.run(args, cwd=cwd, capture_output=True, text=True, check=True)


def _seed_repo(directory, message):
    """A real local repo with one distinguishing commit; returns its sha."""
    _run(['git', 'init', '-q', '-b', 'main', directory])
    Path(directory, 'marker.txt').write_text(message)
    _run(['git', '-C', directory, 'add', 'marker.txt'])
    _run(['git', '-C', directory, '-c', 'user.email=fixture@example.com', '-c', 'user.name=fixture',
          'commit', '-q', '-m', message])
    return _run(['git', '-C', directory, 'rev-parse', 'HEAD']).stdout.strip()


class TargetResolutionTests(unittest.TestCase):
    def test_resolves_canonical_repo_and_ref_to_commit(self):
        sha = 'a' * 40
        snapshot = Snapshot(source=target.CANONICAL_REPOSITORY, revision=sha,
                             private=True, selector=target.CANONICAL_REF)
        result = target.resolve(resolver=lambda: snapshot)
        self.assertEqual(sha, result.commit)
        self.assertEqual('main', result.ref)

    def test_public_api_accepts_no_repository_or_ref_argument(self):
        params = set(inspect.signature(target.resolve).parameters)
        self.assertEqual({'resolver'}, params)

    def test_default_resolution_requests_exact_repository_and_ref(self):
        """GitHubSource must be asked for ref=main explicitly, never left to
        pick up whatever the repository's default_branch happens to be."""
        captured = {}

        class SpyGitHubSource:
            def __init__(self, repository, *, ref=None, runner=None):
                captured['repository'] = repository
                captured['ref'] = ref

            def resolve(self):
                return Snapshot(source=target.CANONICAL_REPOSITORY, revision='a' * 40,
                                 private=True, selector=target.CANONICAL_REF)

        with mock.patch.object(target, 'GitHubSource', SpyGitHubSource):
            target.resolve()
        self.assertEqual(target.CANONICAL_REPOSITORY, captured['repository'])
        self.assertEqual(target.CANONICAL_REF, captured['ref'])

    def test_rejects_resolver_snapshot_for_wrong_repository(self):
        wrong = Snapshot(source='someone/else', revision='a' * 40,
                          private=True, selector=target.CANONICAL_REF)
        with self.assertRaises(SourceUnavailable) as caught:
            target.resolve(resolver=lambda: wrong)
        self.assertEqual('source_unresolved', caught.exception.reason)

    def test_rejects_resolver_snapshot_for_wrong_ref(self):
        wrong = Snapshot(source=target.CANONICAL_REPOSITORY, revision='a' * 40,
                          private=True, selector='develop')
        with self.assertRaises(SourceUnavailable) as caught:
            target.resolve(resolver=lambda: wrong)
        self.assertEqual('source_unresolved', caught.exception.reason)

    def test_capability_unavailable_fails_closed(self):
        def resolver():
            raise SourceUnavailable(reason='capability_unavailable')

        def unexpected_fallback(*args, **kwargs):
            raise AssertionError('git fallback must not run when a resolver is injected')

        with mock.patch.object(target, '_resolve_via_git', unexpected_fallback):
            with self.assertRaises(SourceUnavailable) as caught:
                target.resolve(resolver=resolver)
        self.assertEqual('capability_unavailable', caught.exception.reason)

    def test_no_fabricated_target_on_partial_response(self):
        partial = Snapshot(source=target.CANONICAL_REPOSITORY, revision=None,
                            private=True, selector=target.CANONICAL_REF)
        with self.assertRaises(SourceUnavailable) as caught:
            target.resolve(resolver=lambda: partial)
        self.assertEqual('source_unresolved', caught.exception.reason)


class DirectGitFallbackIsolationTests(unittest.TestCase):
    """Real local Git fixtures only; no network, no gh. Each test patches
    target.CANONICAL_URL to a local `file://` fixture and calls the real
    fallback (_resolve_via_git via controlled_git) against a deliberate
    Git-level attack, asserting resolution still reaches the true local
    canonical fixture rather than the attacker's.
    """

    def setUp(self):
        self._stack = []

    def tearDown(self):
        for context in reversed(self._stack):
            context.__exit__(None, None, None)

    def _tempdir(self):
        context = tempfile.TemporaryDirectory()
        self._stack.append(context)
        return context.__enter__()

    def _canonical_url(self, directory):
        return mock.patch.object(target, 'CANONICAL_URL', 'file://' + directory)

    def test_local_git_fallback_ignores_global_url_rewrite(self):
        canonical_dir, attacker_dir, attacker_home = self._tempdir(), self._tempdir(), self._tempdir()
        canonical_sha = _seed_repo(canonical_dir, 'canonical')
        attacker_sha = _seed_repo(attacker_dir, 'attacker')
        attacker_config = Path(attacker_home, '.gitconfig')
        attacker_config.write_text(f'[url "file://{attacker_dir}"]\n\tinsteadOf = file://{canonical_dir}\n')
        with self._canonical_url(canonical_dir), mock.patch.dict(
                os.environ, {'HOME': attacker_home, 'GIT_CONFIG_GLOBAL': str(attacker_config)}, clear=False):
            result = target._resolve_via_git()
        self.assertEqual(canonical_sha, result.commit)
        self.assertNotEqual(attacker_sha, result.commit)

    def test_local_git_fallback_ignores_repository_local_url_rewrite(self):
        canonical_dir, attacker_dir, caller_repo = self._tempdir(), self._tempdir(), self._tempdir()
        canonical_sha = _seed_repo(canonical_dir, 'canonical')
        attacker_sha = _seed_repo(attacker_dir, 'attacker')
        _run(['git', 'init', '-q', caller_repo])
        _run(['git', '-C', caller_repo, 'config',
              f'url.file://{attacker_dir}.insteadOf', f'file://{canonical_dir}'])
        previous_cwd = os.getcwd()
        os.chdir(caller_repo)
        try:
            with self._canonical_url(canonical_dir):
                result = target._resolve_via_git()
        finally:
            os.chdir(previous_cwd)
        self.assertEqual(canonical_sha, result.commit)
        self.assertNotEqual(attacker_sha, result.commit)

    def test_local_git_fallback_ignores_injected_git_env_vars(self):
        canonical_dir, attacker_dir, other_repo = self._tempdir(), self._tempdir(), self._tempdir()
        canonical_sha = _seed_repo(canonical_dir, 'canonical')
        attacker_sha = _seed_repo(attacker_dir, 'attacker')
        _run(['git', 'init', '-q', other_repo])
        injected = {
            'GIT_CONFIG_COUNT': '1',
            'GIT_CONFIG_KEY_0': f'url.file://{attacker_dir}.insteadOf',
            'GIT_CONFIG_VALUE_0': f'file://{canonical_dir}',
            'GIT_DIR': str(Path(other_repo, '.git')),
            'GIT_WORK_TREE': other_repo,
        }
        with self._canonical_url(canonical_dir), mock.patch.dict(os.environ, injected, clear=False):
            result = target._resolve_via_git()
        self.assertEqual(canonical_sha, result.commit)
        self.assertNotEqual(attacker_sha, result.commit)

    def test_controlled_git_closes_ancestor_repository_discovery(self):
        """The controlled temp dir can land under an ancestor Git repo (e.g.
        the OS temp root happens to sit inside a worktree); upward repository
        discovery past the controlled directory must still be closed."""
        canonical_dir, attacker_dir, hostile_root = self._tempdir(), self._tempdir(), self._tempdir()
        canonical_sha = _seed_repo(canonical_dir, 'canonical')
        attacker_sha = _seed_repo(attacker_dir, 'attacker')
        _run(['git', 'init', '-q', hostile_root])
        _run(['git', '-C', hostile_root, 'config',
              f'url.file://{attacker_dir}.insteadOf', f'file://{canonical_dir}'])
        with self._canonical_url(canonical_dir), mock.patch('tempfile.gettempdir', return_value=hostile_root):
            result = target._resolve_via_git()
        self.assertEqual(canonical_sha, result.commit)
        self.assertNotEqual(attacker_sha, result.commit)


class _RedirectHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(301)
        self.send_header('Location', self.server.redirect_target)
        self.end_headers()

    def log_message(self, *args):
        pass


class _RecordingHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.server.hits.append(self.path)
        self.send_response(404)
        self.end_headers()

    def log_message(self, *args):
        pass


class HttpRedirectAuthorityTests(unittest.TestCase):
    """An HTTP redirect on the initial ls-remote request must not silently
    substitute a different repository as canonical update authority."""

    def test_controlled_git_rejects_http_redirect_to_alternate_authority(self):
        target_server = ThreadingHTTPServer(('127.0.0.1', 0), _RecordingHandler)
        target_server.hits = []
        target_thread = threading.Thread(target=target_server.serve_forever, daemon=True)
        target_thread.start()
        try:
            redirect_server = ThreadingHTTPServer(('127.0.0.1', 0), _RedirectHandler)
            redirect_server.redirect_target = (
                f'http://127.0.0.1:{target_server.server_address[1]}/attacker.git/info/refs')
            redirect_thread = threading.Thread(target=redirect_server.serve_forever, daemon=True)
            redirect_thread.start()
            try:
                url = f'http://127.0.0.1:{redirect_server.server_address[1]}/canonical.git'
                result = target.controlled_git('ls-remote', url, 'main')
            finally:
                redirect_server.shutdown()
                redirect_thread.join()
                redirect_server.server_close()
        finally:
            target_server.shutdown()
            target_thread.join()
            target_server.server_close()
        self.assertNotEqual(0, result.returncode)
        self.assertEqual([], target_server.hits)


class ControlledGitExtraEnvTests(unittest.TestCase):
    """extra_env may only add the two keys Loop 2 needs; it must never be
    able to reopen an authority-bearing variable controlled_git itself
    controls."""

    def test_rejects_protected_key_override(self):
        with self.assertRaises(ValueError):
            target.controlled_git('status', extra_env={'HOME': '/tmp/attacker'})

    def test_rejects_any_key_outside_the_fixed_allowlist(self):
        with self.assertRaises(ValueError):
            target.controlled_git('status', extra_env={'GIT_DIR': '/tmp/attacker'})
        with self.assertRaises(ValueError):
            target.controlled_git('status', extra_env={'SOMETHING_ELSE': '1'})

    def test_allowlisted_keys_are_accepted_and_applied(self):
        captured = {}

        def spy(command, **kwargs):
            captured['env'] = kwargs['env']
            return subprocess.CompletedProcess(command, 0, stdout='', stderr='')

        with tempfile.TemporaryDirectory() as objects_dir:
            target.controlled_git(
                'status', runner=spy,
                extra_env={'GIT_ALTERNATE_OBJECT_DIRECTORIES': objects_dir,
                           'GIT_NO_REPLACE_OBJECTS': '1'})
        self.assertEqual(objects_dir, captured['env']['GIT_ALTERNATE_OBJECT_DIRECTORIES'])
        self.assertEqual('1', captured['env']['GIT_NO_REPLACE_OBJECTS'])

    def test_no_extra_env_leaves_loop_1_behavior_unchanged(self):
        captured = {}

        def spy(command, **kwargs):
            captured['env'] = kwargs['env']
            return subprocess.CompletedProcess(command, 0, stdout='', stderr='')

        target.controlled_git('status', runner=spy)
        self.assertNotIn('GIT_ALTERNATE_OBJECT_DIRECTORIES', captured['env'])
        self.assertNotIn('GIT_NO_REPLACE_OBJECTS', captured['env'])

    def test_windows_controlled_git_preserves_required_systemroot_without_git_authority(self):
        captured = {}

        def spy(command, **kwargs):
            captured['command'] = command
            captured['env'] = kwargs['env']
            return subprocess.CompletedProcess(command, 0, stdout='', stderr='')

        injected = {
            'SystemRoot': r'C:\\Windows',
            'GIT_DIR': r'C:\\attacker\\repo',
            'GIT_CONFIG_COUNT': '1',
        }
        with mock.patch.object(target.os, 'name', 'nt'), mock.patch.dict(
                os.environ, injected, clear=False):
            target.controlled_git('status', runner=spy)

        self.assertEqual(r'C:\\Windows', captured['env']['SystemRoot'])
        self.assertNotIn('GIT_DIR', captured['env'])
        self.assertNotIn('GIT_CONFIG_COUNT', captured['env'])
        self.assertIn('core.autocrlf=true', captured['command'])


if __name__ == '__main__':
    unittest.main()
