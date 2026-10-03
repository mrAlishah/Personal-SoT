import tempfile
import unittest
from pathlib import Path

from system.assistant import update_reporting
from system.assistant.update_reporting import (
    BeginnerReport, DeploymentBinding, advanced_report, git_beginner_report,
    no_write_report, zip_beginner_report,
)
from system.tests.update import test_side_by_side as _sbs_tests
from system.update import git_update, side_by_side

_registry_text = _sbs_tests.SideBySideRegistryTests._registry_text

_SECRET = 'LOOP5-PRIVACY-SENTINEL-DO-NOT-LEAK'


def _write_tree(root, files: dict):
    for rel, content in files.items():
        path = Path(root, rel)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content)


class BeginnerReportPrivacyTests(unittest.TestCase):
    def test_beginner_report_uses_area_and_count(self):
        """Adversarial filenames encode a distinctive Personal fact
        sentinel directly in their own names. The beginner report must
        never contain that sentinel anywhere, including as a
        substring of a filename, and must use safe area/count phrasing.
        """
        kept = (
            f'workspace/context/personal/{_SECRET}_goals.md',
            f'workspace/context/personal/{_SECRET}_notes.md',
            'workspace/placeholder.md',
        )
        plan = side_by_side.SideBySidePlan(kept=kept)
        report = zip_beginner_report(plan, None)

        blob = report.headline + ' '.join(report.details)
        self.assertNotIn(_SECRET, blob)
        self.assertTrue(any('item(s)' in line for line in report.details))
        self.assertTrue(any(line.startswith('workspace:') for line in report.details))

    def test_beginner_report_privacy_holds_for_conflicts_and_unsafe(self):
        plan = side_by_side.SideBySidePlan(
            rejected_unsafe=(f'workspace/context/personal/{_SECRET}.md',))
        report = zip_beginner_report(plan, None)
        self.assertNotIn(_SECRET, report.headline)
        self.assertNotIn(_SECRET, ' '.join(report.details))
        self.assertIn('1 unsafe Personal item', report.headline)

    def test_git_beginner_report_dirty_guidance_never_names_paths(self):
        plan = git_update.Plan(
            '', '', None,
            blocked='dirty_or_untracked',
            blocked_by_area=(('workspace', 2),))
        report = git_beginner_report(plan, {}, None)
        blob = report.headline + ' '.join(report.details)
        self.assertNotIn(_SECRET, blob)
        self.assertIn('local commit', blob.lower())
        self.assertIn('do not push', blob.lower())
        self.assertIn('mrAlishah/Personal-SoT', blob)

    def test_no_write_report_literal_phrases(self):
        report = no_write_report()
        blob = report.headline + ' '.join(report.details)
        self.assertIn('nothing was written', blob)
        self.assertIn('validation was not run here', blob)


class AdvancedAuthorizationTests(unittest.TestCase):
    """Exercises the real `advanced_report` production boundary end to
    end (real files on disk, the canonical registry read from `root`
    itself) rather than any raw pre-authorization candidate transport —
    there is no longer one to call directly.
    """

    def _fixture(self, workdir, scope='personal'):
        root = Path(workdir)
        _write_tree(root, {
            'workspace/context/personal/allow_module.md':
                '---\nai_access: allow\n---\n' + _SECRET + '\n',
            'workspace/context/personal/restricted_module.md':
                '---\nai_access: restricted\n---\n' + _SECRET + '\n',
            'workspace/context/personal/deny_module.md':
                '---\nai_access: deny\n---\n' + _SECRET + '\n',
            'system/routing/context_registry.md':
                _registry_text([(scope, 'workspace/context/personal')]),
        })
        return root

    _CANDIDATES = (
        'workspace/context/personal/allow_module.md',
        'workspace/context/personal/restricted_module.md',
        'workspace/context/personal/deny_module.md',
    )

    def test_advanced_alone_never_exposes_a_path(self):
        """Calling `advanced_report` at all, with NO proven
        authorization input, must disclose nothing, for allow,
        restricted, and deny alike.
        """
        with tempfile.TemporaryDirectory() as workdir:
            root = self._fixture(workdir)
            report = advanced_report('zip', None, root=root, candidate_paths=self._CANDIDATES,
                                      host_read=False)
            self.assertEqual((), report.personal_paths)
            self.assertNotIn(_SECRET, repr(report))

    def test_permitted_allow_path_named_in_advanced_with_proven_host_read(self):
        with tempfile.TemporaryDirectory() as workdir:
            root = self._fixture(workdir)
            report = advanced_report(
                'zip', None, root=root,
                candidate_paths=('workspace/context/personal/allow_module.md',), host_read=True)
            self.assertEqual(('workspace/context/personal/allow_module.md',), report.personal_paths)
            self.assertNotIn(_SECRET, repr(report))

    def test_permitted_allow_path_withheld_without_proven_host_read(self):
        with tempfile.TemporaryDirectory() as workdir:
            root = self._fixture(workdir)
            report = advanced_report(
                'zip', None, root=root,
                candidate_paths=('workspace/context/personal/allow_module.md',), host_read=False)
            self.assertEqual((), report.personal_paths)

    def test_permitted_restricted_path_withheld_without_deployment_binding(self):
        with tempfile.TemporaryDirectory() as workdir:
            root = self._fixture(workdir)
            candidates = ('workspace/context/personal/restricted_module.md',)
            report = advanced_report('zip', None, root=root, candidate_paths=candidates, host_read=True)
            self.assertEqual((), report.personal_paths)
            report = advanced_report(
                'zip', None, root=root, candidate_paths=candidates, host_read=True,
                deployment=DeploymentBinding(personal_owner=True))
            self.assertEqual((), report.personal_paths,
                              'personal_owner alone, without private_instance, is insufficient')

    def test_permitted_restricted_path_named_with_full_trusted_deployment_binding(self):
        """Positive restricted case: a genuinely trusted
        personal_owner/private_instance binding (constructed directly
        here, exactly as `test_access.py` already does — not invented
        authority, just the same trusted-input shape a real private
        Personal deployment's own adapter would supply).
        """
        with tempfile.TemporaryDirectory() as workdir:
            root = self._fixture(workdir)
            report = advanced_report(
                'zip', None, root=root,
                candidate_paths=('workspace/context/personal/restricted_module.md',), host_read=True,
                deployment=DeploymentBinding(personal_owner=True, private_instance=True))
            self.assertEqual(('workspace/context/personal/restricted_module.md',), report.personal_paths)

    def test_permitted_deny_path_always_withheld(self):
        with tempfile.TemporaryDirectory() as workdir:
            root = self._fixture(workdir)
            report = advanced_report(
                'zip', None, root=root,
                candidate_paths=('workspace/context/personal/deny_module.md',), host_read=True,
                deployment=DeploymentBinding(personal_owner=True, private_instance=True))
            self.assertEqual((), report.personal_paths)

    def test_unclassifiable_path_fails_closed_in_advanced(self):
        """A non-context workspace file and a directory-like path
        never resolve to a registered scope at all, so they are simply
        never disclosed, with or without authorization inputs.
        """
        with tempfile.TemporaryDirectory() as workdir:
            root = Path(workdir)
            _write_tree(root, {
                'workspace/plain_note.md': f'no frontmatter at all {_SECRET}\n',
                'system/routing/context_registry.md':
                    _registry_text([('personal', 'workspace/context/personal')]),
            })
            report = advanced_report(
                'zip', None, root=root,
                candidate_paths=('workspace/plain_note.md', 'workspace/some_dir'), host_read=True,
                deployment=DeploymentBinding(personal_owner=True, private_instance=True))
            self.assertEqual((), report.personal_paths)

    def test_body_secret_never_survives_in_advanced_report_repr(self):
        """A 1MB body secret under an allow-authorized path must never
        appear anywhere in the returned report, authorized or not.
        """
        with tempfile.TemporaryDirectory() as workdir:
            root = Path(workdir)
            big_body = 'x' * 1_000_000
            _write_tree(root, {
                'workspace/context/personal/allow_module.md':
                    '---\nai_access: allow\n---\n' + _SECRET + '\n' + big_body,
                'system/routing/context_registry.md':
                    _registry_text([('personal', 'workspace/context/personal')]),
            })
            report = advanced_report(
                'zip', None, root=root,
                candidate_paths=('workspace/context/personal/allow_module.md',), host_read=True)
            self.assertEqual(('workspace/context/personal/allow_module.md',), report.personal_paths)
            self.assertNotIn(_SECRET, repr(report))
            self.assertNotIn(big_body, repr(report))


if __name__ == '__main__':
    unittest.main()
