import inspect
import os
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest import mock

from system.connectors.source import Snapshot, SourceUnavailable
from system.update import target


def _run(args, cwd=None):
    return subprocess.run(args, cwd=cwd, capture_output=True, text=True, check=True)


def _make_fixture_repo(directory):
    """A real local repo standing in for an attacker-controlled rewrite target."""
    _run(['git', 'init', '-q', '-b', 'main', directory])
    Path(directory, 'marker.txt').write_text('attacker-controlled fixture; must never be resolved')
    _run(['git', '-C', directory, 'add', 'marker.txt'])
    _run(['git', '-C', directory, '-c', 'user.email=fixture@example.com', '-c', 'user.name=fixture',
          'commit', '-q', '-m', 'fixture'])
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

    def test_local_git_fallback_ignores_global_url_rewrite(self):
        with tempfile.TemporaryDirectory() as fixture_dir, tempfile.TemporaryDirectory() as attacker_home:
            fixture_sha = _make_fixture_repo(fixture_dir)
            attacker_config = Path(attacker_home, '.gitconfig')
            attacker_config.write_text(
                f'[url "file://{fixture_dir}"]\n\tinsteadOf = {target.CANONICAL_URL}\n')
            with mock.patch.dict(
                    os.environ,
                    {'HOME': attacker_home, 'GIT_CONFIG_GLOBAL': str(attacker_config)},
                    clear=False):
                result = target.controlled_git('ls-remote', target.CANONICAL_URL, target.CANONICAL_REF)
        self.assertNotIn(fixture_sha, result.stdout or '')
        reference = _run(['git', 'ls-remote', target.CANONICAL_URL, target.CANONICAL_REF]).stdout
        self.assertEqual(reference, result.stdout)

    def test_local_git_fallback_ignores_repository_local_url_rewrite(self):
        with tempfile.TemporaryDirectory() as fixture_dir, tempfile.TemporaryDirectory() as caller_repo:
            fixture_sha = _make_fixture_repo(fixture_dir)
            _run(['git', 'init', '-q', caller_repo])
            _run(['git', '-C', caller_repo, 'config',
                  f'url.file://{fixture_dir}.insteadOf', target.CANONICAL_URL])
            previous_cwd = os.getcwd()
            os.chdir(caller_repo)
            try:
                result = target.controlled_git('ls-remote', target.CANONICAL_URL, target.CANONICAL_REF)
            finally:
                os.chdir(previous_cwd)
        self.assertNotIn(fixture_sha, result.stdout or '')
        reference = _run(['git', 'ls-remote', target.CANONICAL_URL, target.CANONICAL_REF]).stdout
        self.assertEqual(reference, result.stdout)

    def test_local_git_fallback_ignores_injected_git_env_vars(self):
        with tempfile.TemporaryDirectory() as fixture_dir, tempfile.TemporaryDirectory() as other_repo:
            fixture_sha = _make_fixture_repo(fixture_dir)
            _run(['git', 'init', '-q', other_repo])
            injected = {
                'GIT_CONFIG_COUNT': '1',
                'GIT_CONFIG_KEY_0': f'url.file://{fixture_dir}.insteadOf',
                'GIT_CONFIG_VALUE_0': target.CANONICAL_URL,
                'GIT_DIR': str(Path(other_repo, '.git')),
                'GIT_WORK_TREE': other_repo,
            }
            with mock.patch.dict(os.environ, injected, clear=False):
                result = target.controlled_git('ls-remote', target.CANONICAL_URL, target.CANONICAL_REF)
        self.assertNotIn(fixture_sha, result.stdout or '')
        reference = _run(['git', 'ls-remote', target.CANONICAL_URL, target.CANONICAL_REF]).stdout
        self.assertEqual(reference, result.stdout)


if __name__ == '__main__':
    unittest.main()
