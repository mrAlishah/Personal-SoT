import os
import stat
import subprocess
import tarfile
import tempfile
import unittest
from hashlib import sha256
from io import BytesIO
from pathlib import Path
from unittest import mock

from system.tests.update.test_git_classification import _init_repo, _run, _commit
from system.update import side_by_side
from system.update.target import TargetSnapshot

_REPO_ROOT = Path(__file__).resolve().parents[3]
_VALIDATOR_FILES = {
    'system/validation/validate_v1.py':
        (_REPO_ROOT / 'system' / 'validation' / 'validate_v1.py').read_text(),
    'system/validation/validate_prompts.py':
        (_REPO_ROOT / 'system' / 'validation' / 'validate_prompts.py').read_text(),
    'system/validation/validate_public.py':
        (_REPO_ROOT / 'system' / 'validation' / 'validate_public.py').read_text(),
    'system/routing/runtime_naming.py':
        (_REPO_ROOT / 'system' / 'routing' / 'runtime_naming.py').read_text(),
}


def _write_tree(root, files: dict):
    for rel, content in files.items():
        path = Path(root, rel)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content)


def _base_target_files(extra=None):
    files = dict(_VALIDATOR_FILES)
    files['guides/placeholder.md'] = 'x\n'
    files['workspace/placeholder.md'] = 'x\n'
    if extra:
        files.update(extra)
    return files


def _build_target_repo(workdir, files):
    target_dir = str(Path(workdir, 'target'))
    _init_repo(target_dir)
    _write_tree(target_dir, files)
    _run(['git', '-C', target_dir, 'add', '-A'])
    sha = _commit(target_dir, 'target')
    return target_dir, sha


def _preview(current_root, destination, target_dir, target_sha, exclude=frozenset()):
    with mock.patch.object(side_by_side.target, 'resolve',
                            return_value=TargetSnapshot(target_sha, 'main', 'test')), \
         mock.patch.object(side_by_side.target, 'CANONICAL_URL', 'file://' + target_dir):
        return side_by_side.preview(current_root, destination, exclude=exclude)


def _migrate(current_root, destination, target_dir, target_sha, plan, digest, exclude=frozenset()):
    with mock.patch.object(side_by_side.target, 'resolve',
                            return_value=TargetSnapshot(target_sha, 'main', 'test')), \
         mock.patch.object(side_by_side.target, 'CANONICAL_URL', 'file://' + target_dir):
        return side_by_side.migrate(current_root, destination, plan, digest, exclude=exclude)


def _hash_tree(root):
    digest = sha256()
    for path in sorted(Path(root).rglob('*')):
        if path.is_file() and not path.is_symlink():
            digest.update(path.relative_to(root).as_posix().encode())
            digest.update(path.read_bytes())
    return digest.hexdigest()


class SideBySidePristineTests(unittest.TestCase):
    def test_pristine_distribution_built_only_from_t(self):
        with tempfile.TemporaryDirectory() as workdir:
            target_dir, target_sha = _build_target_repo(workdir, _base_target_files())
            destination = Path(workdir, 'dest')
            real_controlled_git = side_by_side.controlled_git
            archive_calls = []

            def spy(*args, **kwargs):
                if args and args[0] == 'archive':
                    archive_calls.append(args)
                return real_controlled_git(*args, **kwargs)

            with mock.patch.object(side_by_side.target, 'CANONICAL_URL', 'file://' + target_dir), \
                 mock.patch.object(side_by_side, 'controlled_git', spy):
                ok = side_by_side.build_pristine(destination, target_sha)

            self.assertTrue(ok)
            self.assertEqual(1, len(archive_calls))
            self.assertIn(target_sha, archive_calls[0])
            self.assertTrue(Path(destination, 'guides', 'placeholder.md').is_file())

    def test_destination_must_be_new_and_empty(self):
        with tempfile.TemporaryDirectory() as workdir:
            current_root = Path(workdir, 'current')
            current_root.mkdir()
            destination = Path(workdir, 'dest')
            destination.mkdir()
            Path(destination, 'preexisting.txt').write_text('already here\n')
            self.assertFalse(side_by_side._destination_safe(destination, current_root))

    def test_destination_inside_current_rejected(self):
        with tempfile.TemporaryDirectory() as workdir:
            current_root = Path(workdir, 'current')
            current_root.mkdir()
            destination = current_root / 'nested_dest'
            self.assertFalse(side_by_side._destination_safe(destination, current_root))

    def test_current_inside_destination_rejected(self):
        with tempfile.TemporaryDirectory() as workdir:
            destination = Path(workdir, 'dest')
            current_root = destination / 'nested_current'
            current_root.mkdir(parents=True)
            self.assertFalse(side_by_side._destination_safe(destination, current_root))

    def test_destination_equal_to_current_rejected(self):
        with tempfile.TemporaryDirectory() as workdir:
            current_root = Path(workdir, 'current')
            current_root.mkdir()
            self.assertFalse(side_by_side._destination_safe(current_root, current_root))

    def test_pristine_validated_before_personal_files_enter(self):
        bad_public = (
            'password: hunter2\n'
            + _VALIDATOR_FILES['system/validation/validate_public.py']
        )
        # Inject a raw-secret-shaped line into a scanned text file so
        # validate_public genuinely fails on this pristine tree.
        with tempfile.TemporaryDirectory() as workdir:
            files = _base_target_files({'system/leak.md': 'password: hunter2\n'})
            target_dir, target_sha = _build_target_repo(workdir, files)
            current_root = Path(workdir, 'current')
            current_root.mkdir()
            Path(current_root, 'workspace').mkdir()
            Path(current_root, 'workspace', 'mine.md').write_text('personal note\n')
            destination = Path(workdir, 'dest')

            result = _preview(current_root, destination, target_dir, target_sha)

            self.assertEqual('pristine_validation_failed', result.plan.blocked)
            self.assertEqual((), result.plan.kept)
            self.assertFalse(destination.exists())

    def test_pristine_uses_target_own_public_validator(self):
        """If T's own validate_public.py is deliberately broken, the
        candidate-own subprocess must actually run THAT broken version,
        not a stale already-imported copy — proving the "target may
        update validator code" requirement concretely.
        """
        with tempfile.TemporaryDirectory() as workdir:
            broken = 'import sys\nsys.exit(1)\n'
            files = _base_target_files({'system/validation/validate_public.py': broken})
            target_dir, target_sha = _build_target_repo(workdir, files)
            destination = Path(workdir, 'dest')
            with mock.patch.object(side_by_side.target, 'CANONICAL_URL', 'file://' + target_dir):
                ok = side_by_side.build_pristine(destination, target_sha)
            self.assertTrue(ok)
            self.assertFalse(side_by_side.validate_pristine(destination))

    def test_archive_member_symlink_rejected_by_materializer(self):
        buf = BytesIO()
        with tarfile.open(fileobj=buf, mode='w') as tf:
            info = tarfile.TarInfo(name='evil_link')
            info.type = tarfile.SYMTYPE
            info.linkname = '/etc/passwd'
            tf.addfile(info)
        with tempfile.TemporaryDirectory() as workdir:
            destination = Path(workdir, 'dest')
            ok = side_by_side._extract_pristine_archive(buf.getvalue(), destination)
        self.assertFalse(ok)

    def test_archive_member_traversal_rejected_by_materializer(self):
        buf = BytesIO()
        with tarfile.open(fileobj=buf, mode='w') as tf:
            data = b'malicious\n'
            info = tarfile.TarInfo(name='../../etc/evil.txt')
            info.size = len(data)
            tf.addfile(info, BytesIO(data))
        with tempfile.TemporaryDirectory() as workdir:
            destination = Path(workdir, 'dest')
            ok = side_by_side._extract_pristine_archive(buf.getvalue(), destination)
        self.assertFalse(ok)


class SideBySideClassificationTests(unittest.TestCase):
    def test_current_only_workspace_file_preserved_and_labeled_kept_not_user_created(self):
        with tempfile.TemporaryDirectory() as workdir:
            target_dir, target_sha = _build_target_repo(workdir, _base_target_files())
            current_root = Path(workdir, 'current')
            _write_tree(current_root, {'workspace/mine.md': 'my note\n'})
            destination = Path(workdir, 'dest')

            result = _preview(current_root, destination, target_dir, target_sha)

            self.assertIsNone(result.plan.blocked)
            self.assertIn('workspace/mine.md', result.plan.kept)
            # No vocabulary anywhere claims authorship/user-creation.
            self.assertNotIn('user_created', side_by_side.SideBySidePlan.__dataclass_fields__)
            self.assertNotIn('user_created', repr(result.plan).lower())

    def test_identical_workspace_overlap_needs_no_action(self):
        with tempfile.TemporaryDirectory() as workdir:
            files = _base_target_files({'workspace/shared.md': 'same text\n'})
            target_dir, target_sha = _build_target_repo(workdir, files)
            current_root = Path(workdir, 'current')
            _write_tree(current_root, {'workspace/shared.md': 'same text\n'})
            destination = Path(workdir, 'dest')

            result = _preview(current_root, destination, target_dir, target_sha)

            self.assertIn('workspace/shared.md', result.plan.identical)
            self.assertEqual((), result.plan.conflicts)
            self.assertEqual((), result.plan.kept)

    def test_different_workspace_overlap_is_conflict(self):
        with tempfile.TemporaryDirectory() as workdir:
            files = _base_target_files({'workspace/shared.md': 'target version\n'})
            target_dir, target_sha = _build_target_repo(workdir, files)
            current_root = Path(workdir, 'current')
            _write_tree(current_root, {'workspace/shared.md': 'current version\n'})
            destination = Path(workdir, 'dest')

            result = _preview(current_root, destination, target_dir, target_sha)

            self.assertIn('workspace/shared.md', result.plan.conflicts)
            self.assertEqual((), result.plan.identical)
            self.assertEqual((), result.plan.kept)

    def test_current_only_system_or_guides_file_not_copied(self):
        with tempfile.TemporaryDirectory() as workdir:
            target_dir, target_sha = _build_target_repo(workdir, _base_target_files())
            current_root = Path(workdir, 'current')
            _write_tree(current_root, {
                'system/customization.md': 'local tweak\n',
                'guides/notes.md': 'local guide tweak\n',
            })
            destination = Path(workdir, 'dest')

            result = _preview(current_root, destination, target_dir, target_sha)

            self.assertIn('system/customization.md', result.plan.manual_resolution)
            self.assertIn('guides/notes.md', result.plan.manual_resolution)
            self.assertEqual((), result.plan.kept)

    def test_changed_product_overlap_not_copied(self):
        with tempfile.TemporaryDirectory() as workdir:
            files = _base_target_files({'system/a.md': 'shipped\n'})
            target_dir, target_sha = _build_target_repo(workdir, files)
            current_root = Path(workdir, 'current')
            _write_tree(current_root, {'system/a.md': 'locally modified shipped file\n'})
            destination = Path(workdir, 'dest')

            result = _preview(current_root, destination, target_dir, target_sha)

            self.assertIn('system/a.md', result.plan.manual_resolution)

    def test_overlap_equality_uses_content_hash_not_mtime_or_size(self):
        with tempfile.TemporaryDirectory() as workdir:
            files = _base_target_files({'workspace/a.md': 'same content\n'})
            target_dir, target_sha = _build_target_repo(workdir, files)
            current_root = Path(workdir, 'current')
            _write_tree(current_root, {'workspace/a.md': 'same content\n'})
            # Force a different mtime on the current copy.
            os.utime(Path(current_root, 'workspace', 'a.md'), (0, 0))
            destination = Path(workdir, 'dest')

            result = _preview(current_root, destination, target_dir, target_sha)
            self.assertIn('workspace/a.md', result.plan.identical)

        with tempfile.TemporaryDirectory() as workdir:
            # Same size, same mtime policy, but different bytes.
            files = _base_target_files({'workspace/a.md': 'AAAAAAAAAA\n'})
            target_dir, target_sha = _build_target_repo(workdir, files)
            current_root = Path(workdir, 'current')
            _write_tree(current_root, {'workspace/a.md': 'BBBBBBBBBB\n'})
            destination = Path(workdir, 'dest')

            result = _preview(current_root, destination, target_dir, target_sha)
            self.assertIn('workspace/a.md', result.plan.conflicts)


class SideBySideUnsafePathTests(unittest.TestCase):
    def test_symlink_rejected(self):
        with tempfile.TemporaryDirectory() as workdir:
            target_dir, target_sha = _build_target_repo(workdir, _base_target_files())
            current_root = Path(workdir, 'current')
            current_root.mkdir()
            Path(current_root, 'workspace').mkdir()
            outside = Path(workdir, 'outside.md')
            outside.write_text('secret elsewhere\n')
            os.symlink(outside, Path(current_root, 'workspace', 'link.md'))
            destination = Path(workdir, 'dest')

            result = _preview(current_root, destination, target_dir, target_sha)

            self.assertIn('workspace/link.md', result.plan.rejected_unsafe)
            self.assertEqual((), result.plan.kept)

    def test_special_file_rejected(self):
        with tempfile.TemporaryDirectory() as workdir:
            target_dir, target_sha = _build_target_repo(workdir, _base_target_files())
            current_root = Path(workdir, 'current')
            current_root.mkdir()
            Path(current_root, 'workspace').mkdir()
            fifo_path = Path(current_root, 'workspace', 'pipe')
            try:
                os.mkfifo(fifo_path)
            except (AttributeError, OSError) as error:
                self.skipTest(f'platform does not support creating a FIFO here: {error}')
            destination = Path(workdir, 'dest')

            result = _preview(current_root, destination, target_dir, target_sha)

            self.assertIn('workspace/pipe', result.plan.rejected_unsafe)
            self.assertEqual((), result.plan.kept)

    def test_path_traversal_rejected(self):
        self.assertIsNone(side_by_side.normalize_relative('../../etc/passwd'))
        self.assertIsNone(side_by_side.normalize_relative('workspace/../../../etc/passwd'))

    def test_outside_root_path_rejected(self):
        self.assertIsNone(side_by_side.normalize_relative('/etc/passwd'))
        self.assertIsNone(side_by_side.normalize_relative(''))
        self.assertEqual('workspace/ok.md', side_by_side.normalize_relative('workspace/ok.md'))


class SideBySideOriginalUntouchedTests(unittest.TestCase):
    def test_original_installation_untouched_on_success_and_failure(self):
        with tempfile.TemporaryDirectory() as workdir:
            files = _base_target_files({'workspace/shared.md': 'target\n'})
            target_dir, target_sha = _build_target_repo(workdir, files)
            current_root = Path(workdir, 'current')
            _write_tree(current_root, {
                'workspace/mine.md': 'my note\n',
                'workspace/shared.md': 'current differs\n',  # conflict -> migrate fails
            })
            before = _hash_tree(current_root)

            destination = Path(workdir, 'dest_fail')
            result = _preview(current_root, destination, target_dir, target_sha)
            migrate_result = _migrate(
                current_root, destination, target_dir, target_sha, result.plan, result.digest)
            self.assertEqual('conflict', migrate_result.failure)
            self.assertEqual(before, _hash_tree(current_root))

        with tempfile.TemporaryDirectory() as workdir:
            files = _base_target_files()
            target_dir, target_sha = _build_target_repo(workdir, files)
            current_root = Path(workdir, 'current')
            _write_tree(current_root, {'workspace/mine.md': 'my note\n'})
            before = _hash_tree(current_root)

            destination = Path(workdir, 'dest_ok')
            result = _preview(current_root, destination, target_dir, target_sha)
            migrate_result = _migrate(
                current_root, destination, target_dir, target_sha, result.plan, result.digest)
            self.assertTrue(migrate_result.ready)
            self.assertEqual(before, _hash_tree(current_root))


class SideBySideRegistryTests(unittest.TestCase):
    _REGISTRY_TEMPLATE = (
        "# context_registry\n\n## registered_scopes\n\n"
        "```text\n{entries}```\n"
    )

    @staticmethod
    def _registry_text(pairs):
        body = ''.join(f'{scope}\n→ {dest}\n' for scope, dest in pairs)
        return SideBySideRegistryTests._REGISTRY_TEMPLATE.format(entries=body)

    def test_scope_registration_kept_for_preserved_scope(self):
        with tempfile.TemporaryDirectory() as workdir:
            files = _base_target_files({
                'system/routing/context_registry.md': self._registry_text([]),
            })
            target_dir, target_sha = _build_target_repo(workdir, files)
            current_root = Path(workdir, 'current')
            _write_tree(current_root, {
                'workspace/context/my_project/note.md': 'kept content\n',
                'system/routing/context_registry.md':
                    self._registry_text([('my_project', 'workspace/context/my_project')]),
            })
            destination = Path(workdir, 'dest')

            result = _preview(current_root, destination, target_dir, target_sha)

            self.assertIn(side_by_side.RegistryMapping('my_project', 'workspace/context/my_project'),
                          result.plan.registry.carried)
            self.assertEqual((), result.plan.registry.dropped)
            self.assertEqual((), result.plan.registry.conflicts)

    def test_scope_registration_dropped_for_non_preserved_scope(self):
        with tempfile.TemporaryDirectory() as workdir:
            files = _base_target_files({
                'system/routing/context_registry.md': self._registry_text([]),
            })
            target_dir, target_sha = _build_target_repo(workdir, files)
            current_root = Path(workdir, 'current')
            # The registry claims a scope directory that does not
            # actually exist/get preserved in the candidate.
            _write_tree(current_root, {
                'system/routing/context_registry.md':
                    self._registry_text([('ghost', 'workspace/context/ghost')]),
            })
            destination = Path(workdir, 'dest')

            result = _preview(current_root, destination, target_dir, target_sha)

            self.assertIn(side_by_side.RegistryMapping('ghost', 'workspace/context/ghost'),
                          result.plan.registry.dropped)
            self.assertEqual((), result.plan.registry.carried)

    def test_duplicate_scope_conflict(self):
        with tempfile.TemporaryDirectory() as workdir:
            files = _base_target_files({
                'system/routing/context_registry.md':
                    self._registry_text([('shared_scope', 'workspace/context/alpha')]),
            })
            target_dir, target_sha = _build_target_repo(workdir, files)
            current_root = Path(workdir, 'current')
            _write_tree(current_root, {
                'workspace/context/beta/note.md': 'kept\n',
                'system/routing/context_registry.md':
                    self._registry_text([('shared_scope', 'workspace/context/beta')]),
            })
            destination = Path(workdir, 'dest')

            result = _preview(current_root, destination, target_dir, target_sha)

            self.assertTrue(any(c.startswith('scope_conflict:') for c in result.plan.registry.conflicts))
            self.assertEqual((), result.plan.registry.carried)

    def test_duplicate_target_conflict(self):
        with tempfile.TemporaryDirectory() as workdir:
            files = _base_target_files({
                'system/routing/context_registry.md':
                    self._registry_text([('alpha_scope', 'workspace/context/shared')]),
            })
            target_dir, target_sha = _build_target_repo(workdir, files)
            current_root = Path(workdir, 'current')
            _write_tree(current_root, {
                'workspace/context/shared/note.md': 'kept\n',
                'system/routing/context_registry.md':
                    self._registry_text([('beta_scope', 'workspace/context/shared')]),
            })
            destination = Path(workdir, 'dest')

            result = _preview(current_root, destination, target_dir, target_sha)

            self.assertTrue(any(c.startswith('target_conflict:') for c in result.plan.registry.conflicts))
            self.assertEqual((), result.plan.registry.carried)

    def test_current_system_registry_file_not_copied_wholesale_and_round_trips(self):
        with tempfile.TemporaryDirectory() as workdir:
            files = _base_target_files({
                'system/routing/context_registry.md':
                    self._registry_text([('product_scope', 'workspace/context/product_scope')]),
                'workspace/context/product_scope/placeholder.md': 'x\n',
            })
            target_dir, target_sha = _build_target_repo(workdir, files)
            current_root = Path(workdir, 'current')
            _write_tree(current_root, {
                'workspace/context/mine/note.md': 'kept\n',
                'system/routing/context_registry.md':
                    self._registry_text([
                        ('mine', 'workspace/context/mine'),
                        ('unrelated_current_only_entry', 'workspace/context/does_not_exist'),
                    ]),
            })
            destination = Path(workdir, 'dest')

            result = _preview(current_root, destination, target_dir, target_sha)
            migrate_result = _migrate(
                current_root, destination, target_dir, target_sha, result.plan, result.digest)

            self.assertTrue(migrate_result.ready)
            written = Path(destination, 'system', 'routing', 'context_registry.md').read_text()
            parsed = dict(side_by_side.context_registry_entries(written))
            self.assertEqual('workspace/context/product_scope', parsed.get('product_scope'))
            self.assertEqual('workspace/context/mine', parsed.get('mine'))
            self.assertNotIn('unrelated_current_only_entry', parsed)


class SideBySideFinalValidationTests(unittest.TestCase):
    def test_final_personal_validators_run_on_candidate_using_its_own_version(self):
        broken_prompts = 'import sys\nsys.exit(1)\n'
        with tempfile.TemporaryDirectory() as workdir:
            files = _base_target_files({'system/validation/validate_prompts.py': broken_prompts})
            target_dir, target_sha = _build_target_repo(workdir, files)
            current_root = Path(workdir, 'current')
            _write_tree(current_root, {'workspace/mine.md': 'note\n'})
            destination = Path(workdir, 'dest')

            result = _preview(current_root, destination, target_dir, target_sha)
            migrate_result = _migrate(
                current_root, destination, target_dir, target_sha, result.plan, result.digest)

            self.assertTrue(migrate_result.personal_validation_ran)
            self.assertFalse(migrate_result.personal_validation_passed)
            self.assertEqual('personal_validation_failed', migrate_result.failure)

    def test_validate_public_not_run_after_personal_copy(self):
        with tempfile.TemporaryDirectory() as workdir:
            target_dir, target_sha = _build_target_repo(workdir, _base_target_files())
            current_root = Path(workdir, 'current')
            _write_tree(current_root, {'workspace/mine.md': 'note\n'})
            destination = Path(workdir, 'dest')

            result = _preview(current_root, destination, target_dir, target_sha)

            real_run = subprocess.run
            invoked = []

            def spy(args, *a, **kw):
                if args and args[0] == side_by_side.sys.executable:
                    invoked.append(Path(args[2]))
                return real_run(args, *a, **kw)

            with mock.patch.object(side_by_side.subprocess, 'run', spy):
                migrate_result = _migrate(
                    current_root, destination, target_dir, target_sha, result.plan, result.digest)

            self.assertTrue(migrate_result.ready)
            invoked_names = {path.name for path in invoked}
            self.assertIn('validate_v1.py', invoked_names)
            self.assertIn('validate_prompts.py', invoked_names)
            # validate_public may legitimately run again during migrate()'s
            # own pristine re-check (always BEFORE any Personal file is
            # copied, against a throwaway recheck directory) — what must
            # never happen is validate_public running against the REAL
            # destination once Personal content has entered it.
            for path in invoked:
                if path.name == 'validate_public.py':
                    self.assertNotIn(destination, path.parents)


class SideBySidePreviewStalenessTests(unittest.TestCase):
    def test_preview_bound_to_t_and_plan(self):
        with tempfile.TemporaryDirectory() as workdir:
            target_dir, target_sha = _build_target_repo(workdir, _base_target_files())
            current_root = Path(workdir, 'current')
            _write_tree(current_root, {'workspace/mine.md': 'note\n'})
            destination = Path(workdir, 'dest')

            first = _preview(current_root, destination, target_dir, target_sha)
            second = _preview(current_root, destination, target_dir, target_sha)
            self.assertEqual(first.digest, second.digest)
            self.assertEqual(target_sha, first.plan.target)

    def test_stale_preview_rejected_on_target_change(self):
        with tempfile.TemporaryDirectory() as workdir:
            target_dir, target_sha_1 = _build_target_repo(workdir, _base_target_files())
            current_root = Path(workdir, 'current')
            _write_tree(current_root, {'workspace/mine.md': 'note\n'})
            destination = Path(workdir, 'dest')

            result = _preview(current_root, destination, target_dir, target_sha_1)
            _write_tree(target_dir, {'guides/placeholder.md': 'changed\n'})
            _run(['git', '-C', target_dir, 'add', '-A'])
            target_sha_2 = _commit(target_dir, 'target moved')

            migrate_result = _migrate(
                current_root, destination, target_dir, target_sha_2, result.plan, result.digest)
            self.assertEqual('stale_state', migrate_result.failure)
            self.assertFalse(destination.exists())

    def test_stale_preview_rejected_on_current_state_change(self):
        with tempfile.TemporaryDirectory() as workdir:
            target_dir, target_sha = _build_target_repo(workdir, _base_target_files())
            current_root = Path(workdir, 'current')
            _write_tree(current_root, {'workspace/mine.md': 'note\n'})
            destination = Path(workdir, 'dest')

            result = _preview(current_root, destination, target_dir, target_sha)
            Path(current_root, 'workspace', 'extra.md').write_text('a new file appeared\n')

            migrate_result = _migrate(
                current_root, destination, target_dir, target_sha, result.plan, result.digest)
            self.assertEqual('stale_state', migrate_result.failure)

    def test_stale_preview_rejected_on_registry_change(self):
        registry_text = SideBySideRegistryTests._registry_text([])
        with tempfile.TemporaryDirectory() as workdir:
            files = _base_target_files({'system/routing/context_registry.md': registry_text})
            target_dir, target_sha = _build_target_repo(workdir, files)
            current_root = Path(workdir, 'current')
            _write_tree(current_root, {
                'workspace/mine.md': 'note\n',
                'system/routing/context_registry.md': registry_text,
            })
            destination = Path(workdir, 'dest')

            result = _preview(current_root, destination, target_dir, target_sha)
            _write_tree(current_root, {
                'workspace/context/mine2/note.md': 'kept\n',
                'system/routing/context_registry.md':
                    SideBySideRegistryTests._registry_text([('mine2', 'workspace/context/mine2')]),
            })

            migrate_result = _migrate(
                current_root, destination, target_dir, target_sha, result.plan, result.digest)
            self.assertEqual('stale_state', migrate_result.failure)

    def test_exclusion_decision_is_digest_bound(self):
        with tempfile.TemporaryDirectory() as workdir:
            target_dir, target_sha = _build_target_repo(workdir, _base_target_files())
            current_root = Path(workdir, 'current')
            _write_tree(current_root, {'workspace/mine.md': 'note\n'})
            destination = Path(workdir, 'dest')

            no_exclude = _preview(current_root, destination, target_dir, target_sha)
            with_exclude = _preview(
                current_root, destination, target_dir, target_sha, exclude=frozenset({'workspace/mine.md'}))

            self.assertNotEqual(no_exclude.digest, with_exclude.digest)
            self.assertIn('workspace/mine.md', no_exclude.plan.kept)
            self.assertIn('workspace/mine.md', with_exclude.plan.excluded)
            self.assertNotIn('workspace/mine.md', with_exclude.plan.kept)

            # Replaying the ORIGINAL (no-exclude) plan/digest against the
            # now-different exclusion set must not silently apply either
            # the old or a mismatched plan.
            stale = _migrate(
                current_root, destination, target_dir, target_sha,
                no_exclude.plan, no_exclude.digest, exclude=frozenset({'workspace/mine.md'}))
            self.assertEqual('stale_state', stale.failure)


class SideBySideCopyTimeTests(unittest.TestCase):
    def test_source_change_during_copy_fails_stale_and_leaves_no_ready_candidate(self):
        with tempfile.TemporaryDirectory() as workdir:
            target_dir, target_sha = _build_target_repo(workdir, _base_target_files())
            current_root = Path(workdir, 'current')
            _write_tree(current_root, {
                'workspace/a.md': 'kept a\n',
                'workspace/b.md': 'kept b\n',
            })
            destination = Path(workdir, 'dest')
            result = _preview(current_root, destination, target_dir, target_sha)
            self.assertEqual(('workspace/a.md', 'workspace/b.md'), result.plan.kept)

            real_run = subprocess.run
            copied_first = {'done': False}

            def spy(args, *a, **kw):
                return real_run(args, *a, **kw)

            # Simulate: after classify_workspace's own fresh read inside
            # migrate() but before the copy loop reaches workspace/b.md,
            # an external process edits it.
            original_read_bytes = Path.read_bytes
            state = {'count': 0}

            def tampering_read_bytes(self_path, *a, **kw):
                if self_path.name == 'b.md' and 'current' in self_path.parts:
                    state['count'] += 1
                    if state['count'] == 2:
                        self_path.write_text('tampered during copy\n')
                return original_read_bytes(self_path, *a, **kw)

            with mock.patch.object(Path, 'read_bytes', tampering_read_bytes):
                migrate_result = _migrate(
                    current_root, destination, target_dir, target_sha, result.plan, result.digest)

            self.assertEqual('concurrent_change', migrate_result.failure)
            self.assertFalse(migrate_result.ready)


class SideBySidePrivacyTests(unittest.TestCase):
    _SECRET = 'VERY-SECRET-SENTINEL-VALUE-DO-NOT-LEAK'

    def test_host_side_hashing_of_restricted_content_is_allowed_and_never_leaks(self):
        with tempfile.TemporaryDirectory() as workdir:
            target_dir, target_sha = _build_target_repo(workdir, _base_target_files())
            current_root = Path(workdir, 'current')
            _write_tree(current_root, {
                'workspace/context/personal/deny_module.md':
                    f'---\nai_access: deny\n---\n{self._SECRET}\n',
                'system/routing/context_registry.md':
                    SideBySideRegistryTests._registry_text([('personal', 'workspace/context/personal')]),
            })
            destination = Path(workdir, 'dest')

            result = _preview(current_root, destination, target_dir, target_sha)
            self.assertIn('workspace/context/personal/deny_module.md', result.plan.kept)

            blob = repr(result.plan) + repr(result)
            self.assertNotIn(self._SECRET, blob)

            captured_log = []
            try:
                migrate_result = _migrate(
                    current_root, destination, target_dir, target_sha, result.plan, result.digest)
            except Exception as error:  # pragma: no cover - diagnostic path
                captured_log.append(str(error))
                raise
            finally:
                for entry in captured_log:
                    self.assertNotIn(self._SECRET, entry)

            self.assertNotIn(self._SECRET, repr(migrate_result))
            self.assertTrue(migrate_result.ready)
            # The content itself legitimately reaches the destination
            # (that is the whole point of preservation) — only the
            # Plan/Preview/Result surfaces must stay content-free.
            self.assertIn(self._SECRET,
                          Path(destination, 'workspace', 'context', 'personal', 'deny_module.md').read_text())


if __name__ == '__main__':
    unittest.main()
