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


def _migrate(current_root, destination, target_dir, target_sha, plan, digest, exclude=frozenset(),
             **kwargs):
    with mock.patch.object(side_by_side.target, 'resolve',
                            return_value=TargetSnapshot(target_sha, 'main', 'test')), \
         mock.patch.object(side_by_side.target, 'CANONICAL_URL', 'file://' + target_dir):
        return side_by_side.migrate(current_root, destination, plan, digest, exclude=exclude, **kwargs)


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


    def test_root_anchored_parts_rejects_absolute_path(self):
        """`PurePosixPath('/etc/passwd').parts` is `('/', 'etc',
        'passwd')` — the leading `/` component is itself neither `.`,
        `..`, nor empty, so a component scan alone would never reject
        it. `_root_anchored_parts` must refuse it explicitly, before
        any caller's `openat()` walk ever sees that component.
        """
        self.assertIsNone(side_by_side._root_anchored_parts('/etc/passwd'))
        self.assertIsNone(side_by_side._root_anchored_parts('/'))
        self.assertEqual(['workspace', 'ok.md'], side_by_side._root_anchored_parts('workspace/ok.md'))

    def test_absolute_path_cannot_reach_os_open_through_a_root_anchored_primitive(self):
        """Real low-level proof, independent of any platform's own
        symlink layout (e.g. macOS's `/etc` -> `/private/etc`, which
        would otherwise accidentally mask this): a path entirely made
        of real, non-symlink directories this test controls, reached
        through the shared `_safe_stat_kind`/`_safe_read_regular`
        primitives via an absolute `relative` argument, must never
        escape the pinned root and read content that lives outside
        it. `PurePosixPath('/x').parts[0]` is `'/'`, and POSIX
        `openat()` treats an absolute pathname component as absolute
        in its own right, silently IGNORING `dir_fd` — so a caller
        that reached `os.open('/', ..., dir_fd=pinned_root_fd)` would
        genuinely reopen the real filesystem root, not anything
        rooted under the pinned directory.
        """
        with tempfile.TemporaryDirectory() as workdir:
            workdir = os.path.realpath(workdir)
            root = Path(workdir, 'root')
            root.mkdir()
            secret_dir = Path(workdir, 'secret')
            secret_dir.mkdir()
            secret_file = secret_dir / 'file.txt'
            secret_file.write_text('outside-root-secret\n')
            pin = side_by_side._pin_root(root)
            try:
                self.assertEqual('unsafe', side_by_side._safe_stat_kind(pin, str(secret_file)))
                self.assertIsNone(side_by_side._safe_read_regular(pin, str(secret_file)))
            finally:
                pin.close()


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

    def test_exact_duplicate_target_registry_entry_is_a_conflict(self):
        """The TARGET's own registry lists the exact same scope→target
        pair twice. A duplicate scope occurrence is a conflict
        regardless of whether its target also matches the first one.
        """
        with tempfile.TemporaryDirectory() as workdir:
            files = _base_target_files({
                'system/routing/context_registry.md':
                    self._registry_text([
                        ('alpha_scope', 'workspace/context/alpha'),
                        ('alpha_scope', 'workspace/context/alpha'),
                    ]),
            })
            target_dir, target_sha = _build_target_repo(workdir, files)
            current_root = Path(workdir, 'current')
            current_root.mkdir()
            destination = Path(workdir, 'dest')

            result = _preview(current_root, destination, target_dir, target_sha)

            self.assertTrue(any(
                c.startswith('target_registry_scope_conflict:') for c in result.plan.registry.conflicts))
            self.assertEqual((), result.plan.registry.carried)

    def test_exact_duplicate_current_registry_entry_is_a_conflict_not_two_carries(self):
        """The CURRENT registry lists the exact same preserved
        scope→target pair twice. It must be rejected as a conflict, not
        carried once (or twice).
        """
        with tempfile.TemporaryDirectory() as workdir:
            files = _base_target_files({
                'system/routing/context_registry.md': self._registry_text([]),
            })
            target_dir, target_sha = _build_target_repo(workdir, files)
            current_root = Path(workdir, 'current')
            _write_tree(current_root, {
                'workspace/context/my_project/note.md': 'kept content\n',
                'system/routing/context_registry.md':
                    self._registry_text([
                        ('my_project', 'workspace/context/my_project'),
                        ('my_project', 'workspace/context/my_project'),
                    ]),
            })
            destination = Path(workdir, 'dest')

            result = _preview(current_root, destination, target_dir, target_sha)

            self.assertTrue(any(c.startswith('scope_conflict:') for c in result.plan.registry.conflicts))
            self.assertEqual((), result.plan.registry.carried)

    def test_target_registry_trailing_slash_alias_of_already_claimed_scope_is_a_conflict(self):
        """The TARGET registry lists the same scope twice, the second
        occurrence spelled with a trailing slash — same canonical
        target identity, so still a duplicate-scope conflict, not two
        independent mappings.
        """
        with tempfile.TemporaryDirectory() as workdir:
            files = _base_target_files({
                'system/routing/context_registry.md':
                    self._registry_text([
                        ('alpha_scope', 'workspace/context/a'),
                        ('alpha_scope', 'workspace/context/a/'),
                    ]),
            })
            target_dir, target_sha = _build_target_repo(workdir, files)
            current_root = Path(workdir, 'current')
            current_root.mkdir()
            destination = Path(workdir, 'dest')

            result = _preview(current_root, destination, target_dir, target_sha)

            self.assertTrue(any(
                c.startswith('target_registry_scope_conflict:') for c in result.plan.registry.conflicts))
            self.assertEqual((), result.plan.registry.carried)

    def test_two_different_scopes_claiming_trailing_slash_variants_of_one_target_is_a_conflict(self):
        """Two DIFFERENT target-registry scopes spell the SAME target
        directory differently (one with a trailing slash) — canonical
        target identity must still treat this as one contested target,
        not two independently-owned ones.
        """
        with tempfile.TemporaryDirectory() as workdir:
            files = _base_target_files({
                'system/routing/context_registry.md':
                    self._registry_text([
                        ('alpha_scope', 'workspace/context/shared'),
                        ('beta_scope', 'workspace/context/shared/'),
                    ]),
            })
            target_dir, target_sha = _build_target_repo(workdir, files)
            current_root = Path(workdir, 'current')
            current_root.mkdir()
            destination = Path(workdir, 'dest')

            result = _preview(current_root, destination, target_dir, target_sha)

            self.assertTrue(any(
                c.startswith('target_registry_target_conflict:') for c in result.plan.registry.conflicts))
            self.assertEqual((), result.plan.registry.carried)

    def test_current_registry_hidden_behind_a_symlink_is_never_read(self):
        """The current installation's own registry path is a symlink
        to an outside secret file. It must never be parsed as the
        current registry's content (silently treated as empty would be
        just as wrong as reading through it) — it is a bounded unsafe
        condition that blocks the migration.
        """
        with tempfile.TemporaryDirectory() as workdir:
            files = _base_target_files({
                'system/routing/context_registry.md': self._registry_text([]),
            })
            target_dir, target_sha = _build_target_repo(workdir, files)
            current_root = Path(workdir, 'current')
            _write_tree(current_root, {'workspace/placeholder2.md': 'x\n'})
            outside = Path(workdir, 'outside_registry.md')
            outside.write_text(self._registry_text([('leaked_scope', 'workspace/context/leaked')]))
            registry_path = Path(current_root, 'system', 'routing', 'context_registry.md')
            registry_path.parent.mkdir(parents=True, exist_ok=True)
            os.symlink(outside, registry_path)
            destination = Path(workdir, 'dest')

            result = _preview(current_root, destination, target_dir, target_sha)

            self.assertNotIn(
                side_by_side.RegistryMapping('leaked_scope', 'workspace/context/leaked'),
                result.plan.registry.carried)
            self.assertIn('unsafe_registry', result.plan.registry.conflicts)

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

    def test_validate_public_never_runs_after_personal_copy_has_begun(self):
        """`validate_public` legitimately runs against the real
        destination too now (before any Personal file enters it, per
        the destination-pristine-validation fix) — what must never
        happen is it running AFTER the first Personal/current file has
        been written into that destination. Tracked by event order,
        using `_during_copy` (implementation-independent) rather than
        patching whatever low-level write primitive the copy happens
        to use internally.
        """
        with tempfile.TemporaryDirectory() as workdir:
            target_dir, target_sha = _build_target_repo(workdir, _base_target_files())
            current_root = Path(workdir, 'current')
            _write_tree(current_root, {'workspace/mine.md': 'note\n'})
            destination = Path(workdir, 'dest')

            result = _preview(current_root, destination, target_dir, target_sha)

            real_run = subprocess.run
            events = []

            def run_spy(args, *a, **kw):
                if args and args[0] == side_by_side.sys.executable:
                    events.append(('run', Path(args[2]).name, Path(args[2])))
                return real_run(args, *a, **kw)

            def before_copy(relative):
                events.append(('write', relative, None))

            with mock.patch.object(side_by_side.subprocess, 'run', run_spy):
                migrate_result = _migrate(
                    current_root, destination, target_dir, target_sha, result.plan, result.digest,
                    _during_copy=before_copy)

            self.assertTrue(migrate_result.ready)
            invoked_names = {name for _kind, name, _path in events if _kind == 'run'}
            self.assertIn('validate_v1.py', invoked_names)
            self.assertIn('validate_prompts.py', invoked_names)
            write_indices = [i for i, event in enumerate(events) if event[0] == 'write']
            self.assertTrue(write_indices)
            first_personal_write = write_indices[0]
            for i, (kind, name, path) in enumerate(events):
                if kind == 'run' and name == 'validate_public.py' and destination in path.parents:
                    self.assertLess(i, first_personal_write)


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

            # Simulate: after the copy loop has already copied
            # workspace/a.md, but immediately before its own turn, an
            # external process edits workspace/b.md.
            def tamper_before_b(relative):
                if relative == 'workspace/b.md':
                    Path(current_root, 'workspace', 'b.md').write_text('tampered during copy\n')

            migrate_result = _migrate(
                current_root, destination, target_dir, target_sha, result.plan, result.digest,
                _during_copy=tamper_before_b)

            self.assertEqual('concurrent_change', migrate_result.failure)
            self.assertFalse(migrate_result.ready)


class SideBySidePrivacyTests(unittest.TestCase):
    _SECRET = 'VERY-SECRET-SENTINEL-VALUE-DO-NOT-LEAK'

    def test_host_side_hashing_of_restricted_content_is_allowed_and_never_leaks(self):
        with tempfile.TemporaryDirectory() as workdir:
            target_dir, target_sha = _build_target_repo(workdir, _base_target_files({
                'system/routing/context_registry.md': SideBySideRegistryTests._registry_text([]),
            }))
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


class SideBySideDestinationIntegrityTests(unittest.TestCase):
    def test_real_destination_pristine_modification_before_copy_is_detected(self):
        """A target-owned file in the REAL destination is tampered with
        right after `build_pristine(destination, ...)` returns, before
        any Personal/current file is copied — no new test seam needed:
        `build_pristine` is patched to tamper immediately after the real
        (unpatched) build succeeds, for the real `destination` path
        specifically (never for the throwaway `recheck_pristine`).
        """
        with tempfile.TemporaryDirectory() as workdir:
            target_dir, target_sha = _build_target_repo(workdir, _base_target_files())
            current_root = Path(workdir, 'current')
            _write_tree(current_root, {'workspace/mine.md': 'note\n'})
            destination = Path(workdir, 'dest')

            result = _preview(current_root, destination, target_dir, target_sha)
            self.assertIsNone(result.plan.blocked)

            real_build_pristine = side_by_side.build_pristine

            def tampering_build_pristine(dest, commit):
                ok = real_build_pristine(dest, commit)
                if ok and Path(dest) == destination:
                    Path(destination, 'guides', 'placeholder.md').write_text('tampered\n')
                return ok

            with mock.patch.object(side_by_side, 'build_pristine', tampering_build_pristine):
                migrate_result = _migrate(
                    current_root, destination, target_dir, target_sha, result.plan, result.digest)

            # The tamper is detected and the candidate is never ready;
            # the destination itself is NOT reverted/cleaned — it was
            # never promised to be, only that Personal data never
            # enters it on top of an unverified pristine tree.
            self.assertFalse(migrate_result.ready)
            self.assertIn(migrate_result.failure,
                          ('stale_state', 'destination_pristine_validation_failed'))
            self.assertFalse(migrate_result.personal_validation_ran)
            self.assertFalse(Path(destination, 'workspace', 'mine.md').exists())

    def test_destination_target_owned_file_changed_during_copy_still_reports_ready(self):
        """Two kept files; between copying the first and the second, an
        external process tampers with an UNRELATED target-owned file
        already present in the real destination, injected through the
        `_during_copy` seam (the per-kept-file hook, independent of
        which low-level primitive the copy itself uses).
        """
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

            def tamper_before_b(relative):
                if relative == 'workspace/b.md':
                    Path(destination, 'guides', 'placeholder.md').write_text('tampered\n')

            migrate_result = _migrate(
                current_root, destination, target_dir, target_sha, result.plan, result.digest,
                _during_copy=tamper_before_b)

            self.assertFalse(migrate_result.ready)

    def test_kept_file_tampered_after_its_own_copy_while_a_later_file_still_copies(self):
        """Two kept files. Right after the FIRST is copied, its own
        destination copy (not the source) is modified while the SECOND
        is still being copied. A per-file post-copy check alone would
        miss this, since it only re-verifies at the moment of its own
        copy; the final manifest check (covering every kept path, not
        just the one just written) must still catch it.
        """
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

            def tamper_a_before_b(relative):
                if relative == 'workspace/b.md':
                    Path(destination, 'workspace', 'a.md').write_text('tampered a\n')

            migrate_result = _migrate(
                current_root, destination, target_dir, target_sha, result.plan, result.digest,
                _during_copy=tamper_a_before_b)

            self.assertFalse(migrate_result.ready)
            self.assertEqual('concurrent_change', migrate_result.failure)

    def test_candidate_tampered_during_the_final_personal_validators_is_detected(self):
        """After the candidate reaches final Personal validation (and
        the validators still return success), an external process
        modifies a kept workspace file. The pre-validator integrity
        check alone cannot see this, since it runs BEFORE the
        validators; a second check immediately before `ready=True` is
        required to catch tampering that lands during their own
        (possibly non-trivial) runtime.
        """
        with tempfile.TemporaryDirectory() as workdir:
            target_dir, target_sha = _build_target_repo(workdir, _base_target_files())
            current_root = Path(workdir, 'current')
            _write_tree(current_root, {'workspace/mine.md': 'note\n'})
            destination = Path(workdir, 'dest')
            result = _preview(current_root, destination, target_dir, target_sha)
            self.assertEqual(('workspace/mine.md',), result.plan.kept)

            real_validate_candidate = side_by_side.validate_candidate

            def tampering_validate_candidate(dest):
                outcome = real_validate_candidate(dest)
                Path(dest, 'workspace', 'mine.md').write_text('tampered during validation\n')
                return outcome

            with mock.patch.object(side_by_side, 'validate_candidate', tampering_validate_candidate):
                migrate_result = _migrate(
                    current_root, destination, target_dir, target_sha, result.plan, result.digest)

            self.assertFalse(migrate_result.ready)
            self.assertTrue(migrate_result.personal_validation_ran)
            self.assertTrue(migrate_result.personal_validation_passed)
            self.assertEqual('concurrent_change', migrate_result.failure)

    def test_destination_intermediate_directory_symlink_escape_on_kept_file_write_is_refused(self):
        """Target ships no `workspace/context/`; current has a kept
        file `workspace/context/mine.md`. Right before that file would
        be copied, `destination/workspace/context` is swapped for a
        symlink to an outside directory. The write must never land
        through that symlink — root-anchored directory creation refuses
        to accept a symlink as a directory component.
        """
        with tempfile.TemporaryDirectory() as workdir:
            target_dir, target_sha = _build_target_repo(workdir, _base_target_files())
            current_root = Path(workdir, 'current')
            _write_tree(current_root, {'workspace/context/mine.md': 'kept context\n'})
            destination = Path(workdir, 'dest')
            outside = Path(workdir, 'outside_context')
            outside.mkdir()

            result = _preview(current_root, destination, target_dir, target_sha)
            self.assertEqual(('workspace/context/mine.md',), result.plan.kept)

            def swap_context_for_symlink(relative):
                if relative == 'workspace/context/mine.md':
                    context_dir = Path(destination, 'workspace', 'context')
                    if context_dir.is_dir():
                        context_dir.rmdir()
                    os.symlink(outside, context_dir)

            migrate_result = _migrate(
                current_root, destination, target_dir, target_sha, result.plan, result.digest,
                _during_copy=swap_context_for_symlink)

            self.assertFalse(migrate_result.ready)
            self.assertFalse((outside / 'mine.md').exists())

    def test_destination_registry_symlink_write_escape_is_refused(self):
        """Right before the registry replacement write, the
        destination's `system/routing/context_registry.md` is swapped
        for a symlink to an outside file. The replacement must never
        follow it: it must fail closed rather than writing through the
        symlink into the outside file.
        """
        with tempfile.TemporaryDirectory() as workdir:
            files = _base_target_files({
                'system/routing/context_registry.md':
                    SideBySideRegistryTests._registry_text([]),
            })
            target_dir, target_sha = _build_target_repo(workdir, files)
            current_root = Path(workdir, 'current')
            _write_tree(current_root, {
                'workspace/context/mine/note.md': 'kept\n',
                'system/routing/context_registry.md':
                    SideBySideRegistryTests._registry_text([('mine', 'workspace/context/mine')]),
            })
            destination = Path(workdir, 'dest')
            outside_file = Path(workdir, 'outside_registry.md')
            outside_file.write_text('outside before\n')

            result = _preview(current_root, destination, target_dir, target_sha)
            self.assertEqual(('workspace/context/mine/note.md',), result.plan.kept)
            self.assertEqual(
                (side_by_side.RegistryMapping('mine', 'workspace/context/mine'),),
                result.plan.registry.carried)

            def swap_registry_for_symlink(relative):
                if relative == 'workspace/context/mine/note.md':
                    registry_path = Path(destination, 'system', 'routing', 'context_registry.md')
                    registry_path.unlink()
                    os.symlink(outside_file, registry_path)

            migrate_result = _migrate(
                current_root, destination, target_dir, target_sha, result.plan, result.digest,
                _during_copy=swap_registry_for_symlink)

            self.assertFalse(migrate_result.ready)
            self.assertEqual('outside before\n', outside_file.read_text())


class SideBySideSafeReadTests(unittest.TestCase):
    _SECRET = 'OUTSIDE-SYMLINK-RACE-SECRET'

    def test_lstat_then_reopen_pattern_is_race_prone_in_isolation(self):
        """Demonstrates the vulnerability class the current `migrate()`
        copy loop uses (`lstat` a path, confirm regular, THEN
        separately re-open it by pathname for `read_bytes()`): if the
        path is swapped for a symlink in between, the independent
        re-open follows it and reads the outside target. This is
        exactly the TOCTOU window a same-descriptor safe-open-and-read
        primitive closes.
        """
        with tempfile.TemporaryDirectory() as workdir:
            path = Path(workdir, 'a.md')
            path.write_text('original\n')
            outside = Path(workdir, 'outside.md')
            outside.write_text(self._SECRET + '\n')

            st = path.lstat()
            self.assertTrue(stat.S_ISREG(st.st_mode))
            path.unlink()
            os.symlink(outside, path)  # the race: swapped between check and read
            data = path.read_bytes()  # the vulnerable pattern's separate re-open

            self.assertIn(self._SECRET.encode(), data)

    @staticmethod
    def _pin(path):
        pinned = side_by_side._pin_root(path)
        assert pinned is not None
        return pinned

    def test_safe_read_regular_refuses_a_symlink_and_never_follows_it(self):
        with tempfile.TemporaryDirectory() as workdir:
            path = Path(workdir, 'a.md')
            outside = Path(workdir, 'outside.md')
            outside.write_text(self._SECRET + '\n')
            os.symlink(outside, path)

            pinned = self._pin(Path(workdir))
            try:
                result = side_by_side._safe_read_regular(pinned, 'a.md')
            finally:
                pinned.close()

            self.assertIsNone(result)

    def test_safe_read_regular_reads_a_genuine_regular_file(self):
        with tempfile.TemporaryDirectory() as workdir:
            path = Path(workdir, 'a.md')
            path.write_text('real content\n')
            pinned = self._pin(Path(workdir))
            try:
                self.assertEqual(b'real content\n', side_by_side._safe_read_regular(pinned, 'a.md'))
            finally:
                pinned.close()

    def test_safe_read_regular_returns_none_for_a_missing_path(self):
        with tempfile.TemporaryDirectory() as workdir:
            pinned = self._pin(Path(workdir))
            try:
                self.assertIsNone(side_by_side._safe_read_regular(pinned, 'absent.md'))
            finally:
                pinned.close()

    def test_safe_read_regular_rejects_an_intermediate_directory_symlink(self):
        """The defect this whole correction targets: `O_NOFOLLOW` on
        only the FINAL component does not stop an intermediate
        directory from being a symlink out of the selected root.
        """
        with tempfile.TemporaryDirectory() as workdir:
            root = Path(workdir, 'root')
            (root / 'workspace').mkdir(parents=True)
            (root / 'workspace' / 'private').mkdir()
            (root / 'workspace' / 'private' / 'a.md').write_text('inside\n')
            outside = Path(workdir, 'outside')
            outside.mkdir()
            (outside / 'a.md').write_text(self._SECRET + '\n')

            import shutil
            shutil.rmtree(root / 'workspace' / 'private')
            os.symlink(outside, root / 'workspace' / 'private')

            pinned = self._pin(root)
            try:
                result = side_by_side._safe_read_regular(pinned, 'workspace/private/a.md')
            finally:
                pinned.close()

            self.assertIsNone(result)

    def test_pin_root_refuses_a_root_that_is_itself_a_symlink(self):
        with tempfile.TemporaryDirectory() as workdir:
            real = Path(workdir, 'real')
            real.mkdir()
            link = Path(workdir, 'link')
            os.symlink(real, link)

            self.assertIsNone(side_by_side._pin_root(link))

    def test_pinned_fd_still_sees_original_directory_after_root_pathname_is_replaced(self):
        """The property root pinning exists for: once pinned, the fd
        keeps referring to the ORIGINAL directory even after its
        pathname is renamed away and replaced by a symlink to an
        outside tree — a later `_safe_read_regular` call through the
        SAME pin must still see the original content, not the outside
        secret.
        """
        import shutil
        with tempfile.TemporaryDirectory() as workdir:
            root = Path(workdir, 'root')
            root.mkdir()
            (root / 'a.md').write_text('inside\n')
            outside = Path(workdir, 'outside')
            outside.mkdir()
            (outside / 'a.md').write_text(self._SECRET + '\n')

            pinned = self._pin(root)
            try:
                shutil.move(str(root), str(Path(workdir, 'root_moved_away')))
                os.symlink(outside, root)

                result = side_by_side._safe_read_regular(pinned, 'a.md')
            finally:
                pinned.close()

            self.assertEqual(b'inside\n', result)
            self.assertNotIn(self._SECRET.encode(), result or b'')


class SideBySideScopePreservationTests(unittest.TestCase):
    def test_candidate_present_scope_with_no_current_only_kept_file_is_wrongly_dropped(self):
        """The scope directory `workspace/context/shared` is present in
        the resulting candidate purely because T already ships an
        identical file there — there is no current-ONLY kept file under
        it at all. The design says this still counts as preserved.
        """
        registry_text = SideBySideRegistryTests._registry_text([])
        with tempfile.TemporaryDirectory() as workdir:
            files = _base_target_files({
                'workspace/context/shared/module.md': 'shipped content\n',
                'system/routing/context_registry.md': registry_text,
            })
            target_dir, target_sha = _build_target_repo(workdir, files)
            current_root = Path(workdir, 'current')
            _write_tree(current_root, {
                'workspace/context/shared/module.md': 'shipped content\n',  # identical overlap
                'system/routing/context_registry.md':
                    SideBySideRegistryTests._registry_text([('shared', 'workspace/context/shared')]),
            })
            destination = Path(workdir, 'dest')

            result = _preview(current_root, destination, target_dir, target_sha)

            self.assertEqual((), result.plan.kept)
            self.assertIn('workspace/context/shared/module.md', result.plan.identical)
            self.assertIn(
                side_by_side.RegistryMapping('shared', 'workspace/context/shared'),
                result.plan.registry.carried)


class SideBySideTargetRegistryValidationTests(unittest.TestCase):
    def test_malformed_target_registry_scope_ownership_is_not_silently_accepted(self):
        """The TARGET's own registry claims one scope name for two
        different directories — a malformed/ambiguous mapping that
        `setdefault`-based loading would silently collapse to whichever
        entry it saw first.
        """
        target_registry = (
            "# context_registry\n\n## registered_scopes\n\n"
            "```text\nalpha\n→ workspace/context/alpha\nalpha\n→ workspace/context/alpha_v2\n```\n"
        )
        with tempfile.TemporaryDirectory() as workdir:
            files = _base_target_files({
                'system/routing/context_registry.md': target_registry,
                'workspace/context/alpha/x.md': 'a\n',
                'workspace/context/alpha_v2/y.md': 'b\n',
            })
            target_dir, target_sha = _build_target_repo(workdir, files)
            current_root = Path(workdir, 'current')
            current_root.mkdir()
            destination = Path(workdir, 'dest')

            result = _preview(current_root, destination, target_dir, target_sha)

            self.assertTrue(any('target_registry' in c for c in result.plan.registry.conflicts))

    def test_two_target_scopes_claiming_one_target_is_a_conflict(self):
        target_registry = (
            "# context_registry\n\n## registered_scopes\n\n"
            "```text\nalpha\n→ workspace/context/shared\nbeta\n→ workspace/context/shared\n```\n"
        )
        with tempfile.TemporaryDirectory() as workdir:
            files = _base_target_files({
                'system/routing/context_registry.md': target_registry,
                'workspace/context/shared/x.md': 'a\n',
            })
            target_dir, target_sha = _build_target_repo(workdir, files)
            current_root = Path(workdir, 'current')
            current_root.mkdir()
            destination = Path(workdir, 'dest')

            result = _preview(current_root, destination, target_dir, target_sha)

            self.assertTrue(any('target_registry' in c for c in result.plan.registry.conflicts))


class SideBySideRootSubstitutionTests(unittest.TestCase):
    """Gap 1: the ROOT itself (not merely its descendants) must be
    pinned once and never re-derived from its pathname — otherwise a
    rename-away-then-symlink-in swap of the whole source or destination
    root, between an earlier verification and a later read/write, could
    silently redirect host-side I/O to an attacker-controlled directory
    even though every individual descendant check stays "safe".
    """
    _SECRET = 'OUTSIDE-ROOT-SUBSTITUTION-SECRET'

    def test_source_root_replaced_by_symlink_during_migrate_is_never_followed(self):
        """`current_root` is renamed away and replaced by a symlink to
        an outside tree (containing the same relative path, with a
        distinctive sentinel) between preview and the second kept
        file's copy. The pinned fd alone would keep referring to the
        ORIGINAL directory (containment), but `current_root`'s
        pathname no longer identifies the installation the caller
        selected at all — that is a concurrent change the migration
        must stop for, not silently continue past using the old fd.
        """
        with tempfile.TemporaryDirectory() as workdir:
            target_dir, target_sha = _build_target_repo(workdir, _base_target_files())
            current_root = Path(workdir, 'current')
            _write_tree(current_root, {
                'workspace/a.md': 'kept a\n',
                'workspace/b.md': 'kept b\n',
            })
            destination = Path(workdir, 'dest')
            outside = Path(workdir, 'outside_current')
            (outside / 'workspace').mkdir(parents=True)
            (outside / 'workspace' / 'b.md').write_text(self._SECRET + '\n')

            result = _preview(current_root, destination, target_dir, target_sha)
            self.assertEqual(('workspace/a.md', 'workspace/b.md'), result.plan.kept)

            def swap_current_root(relative):
                if relative == 'workspace/b.md':
                    import shutil
                    shutil.move(str(current_root), str(Path(workdir, 'current_moved_away')))
                    os.symlink(outside, current_root)

            migrate_result = _migrate(
                current_root, destination, target_dir, target_sha, result.plan, result.digest,
                _during_copy=swap_current_root)

            self.assertFalse(migrate_result.ready)
            self.assertIn(migrate_result.failure, ('concurrent_change', 'stale_state'))
            blob = repr(migrate_result)
            self.assertNotIn(self._SECRET, blob)
            # The identity check fires before b.md is ever read, so no
            # further kept file is copied past the detected mismatch.
            self.assertFalse(Path(destination, 'workspace', 'b.md').exists())

    def test_source_root_replaced_by_a_new_real_directory_during_migrate_is_rejected(self):
        """Same race, but the replacement at `current_root`'s pathname
        is an entirely different REAL directory — never a symlink at
        any point — proving the check is inode/device identity, not
        merely symlink rejection.
        """
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

            def replace_current_root_with_new_directory(relative):
                if relative == 'workspace/b.md':
                    import shutil
                    shutil.move(str(current_root), str(Path(workdir, 'current_moved_away')))
                    current_root.mkdir()
                    (current_root / 'workspace').mkdir()
                    (current_root / 'workspace' / 'b.md').write_text('kept b\n')

            migrate_result = _migrate(
                current_root, destination, target_dir, target_sha, result.plan, result.digest,
                _during_copy=replace_current_root_with_new_directory)

            self.assertFalse(migrate_result.ready)
            self.assertIn(migrate_result.failure, ('concurrent_change', 'stale_state'))
            self.assertFalse(Path(destination, 'workspace', 'b.md').exists())

    def test_destination_root_replaced_by_symlink_during_migrate_never_receives_writes(self):
        """After the real pristine destination is built and validated,
        `destination` is renamed away and replaced by a symlink to an
        outside directory right before a kept file's write. The pinned
        destination fd must keep referring to the ORIGINAL directory:
        the outside directory must never receive the write.
        """
        with tempfile.TemporaryDirectory() as workdir:
            target_dir, target_sha = _build_target_repo(workdir, _base_target_files())
            current_root = Path(workdir, 'current')
            _write_tree(current_root, {'workspace/a.md': 'kept a\n'})
            destination = Path(workdir, 'dest')
            outside = Path(workdir, 'outside_dest')
            outside.mkdir()

            result = _preview(current_root, destination, target_dir, target_sha)
            self.assertEqual(('workspace/a.md',), result.plan.kept)

            def swap_destination_root(relative):
                if relative == 'workspace/a.md':
                    import shutil
                    shutil.move(str(destination), str(Path(workdir, 'dest_moved_away')))
                    os.symlink(outside, destination)

            self.assertEqual([], list(outside.iterdir()))
            _migrate(
                current_root, destination, target_dir, target_sha, result.plan, result.digest,
                _during_copy=swap_destination_root)

            self.assertEqual([], list(outside.iterdir()))

    def test_pristine_extraction_refuses_destination_root_replaced_by_symlink(self):
        """`destination` is valid/empty, then replaced by a symlink to
        an outside directory immediately before extraction — member-
        shape validation alone does not protect the destination ROOT
        itself. A synthetic safe regular tar member (`guides/a.md`)
        must never land in the outside directory; extraction must fail
        closed instead.
        """
        with tempfile.TemporaryDirectory() as workdir:
            destination = Path(workdir, 'dest')
            destination.mkdir()
            outside = Path(workdir, 'outside')
            outside.mkdir()
            os.rmdir(destination)
            os.symlink(outside, destination)

            buf = BytesIO()
            with tarfile.open(fileobj=buf, mode='w') as tf:
                data = b'x\n'
                info = tarfile.TarInfo(name='guides/a.md')
                info.size = len(data)
                info.mode = 0o644
                tf.addfile(info, BytesIO(data))

            ok = side_by_side._extract_pristine_archive(buf.getvalue(), destination)

            self.assertFalse(ok)
            self.assertEqual([], list(outside.iterdir()))

    def test_pristine_extraction_preserves_executable_mode_bit(self):
        """A tracked executable file's mode bit must survive the
        root-anchored extractor, not be silently collapsed to a fixed
        mode.
        """
        with tempfile.TemporaryDirectory() as workdir:
            destination = Path(workdir, 'dest')
            destination.mkdir()

            buf = BytesIO()
            with tarfile.open(fileobj=buf, mode='w') as tf:
                data = b'#!/bin/sh\necho hi\n'
                info = tarfile.TarInfo(name='run.sh')
                info.size = len(data)
                info.mode = 0o755
                tf.addfile(info, BytesIO(data))

            ok = side_by_side._extract_pristine_archive(buf.getvalue(), destination)

            self.assertTrue(ok)
            mode = (destination / 'run.sh').stat().st_mode
            self.assertTrue(mode & 0o111, 'executable bit should survive extraction')

    def test_preview_rejects_root_drift_detected_during_classification(self):
        """`current_root`'s pathname is replaced by a new real
        directory partway through `classify_workspace` — after its
        scan/hash loop, before it returns — injected via a mock around
        `_registry_plan` (the last internal step classification takes)
        rather than any new production callback. The returned preview
        must never be a usable, confirmable plan for the old,
        since-replaced installation.
        """
        with tempfile.TemporaryDirectory() as workdir:
            target_dir, target_sha = _build_target_repo(workdir, _base_target_files())
            current_root = Path(workdir, 'current')
            _write_tree(current_root, {'workspace/a.md': 'kept a\n'})
            destination = Path(workdir, 'dest')

            real_registry_plan = side_by_side._registry_plan

            def drifting_registry_plan(current_pin, pristine_pin, candidate_paths):
                import shutil
                shutil.move(str(current_root), str(Path(workdir, 'current_moved_away')))
                current_root.mkdir()
                (current_root / 'workspace').mkdir()
                (current_root / 'workspace' / 'a.md').write_text('kept a\n')
                return real_registry_plan(current_pin, pristine_pin, candidate_paths)

            with mock.patch.object(side_by_side, '_registry_plan', drifting_registry_plan):
                result = _preview(current_root, destination, target_dir, target_sha)

            self.assertEqual('stale_state', result.plan.blocked)

    def test_migrate_reclassification_rejects_root_drift_detected_during_classification(self):
        """Same root-drift-during-classification race, but observed by
        `migrate`'s own fresh reclassification rather than `preview`.
        """
        with tempfile.TemporaryDirectory() as workdir:
            target_dir, target_sha = _build_target_repo(workdir, _base_target_files())
            current_root = Path(workdir, 'current')
            _write_tree(current_root, {'workspace/a.md': 'kept a\n'})
            destination = Path(workdir, 'dest')

            result = _preview(current_root, destination, target_dir, target_sha)
            self.assertEqual(('workspace/a.md',), result.plan.kept)

            real_registry_plan = side_by_side._registry_plan

            def drifting_registry_plan(current_pin, pristine_pin, candidate_paths):
                # preview() already ran outside this patch, so the ONE
                # call reachable here is migrate's own reclassification.
                import shutil
                shutil.move(str(current_root), str(Path(workdir, 'current_moved_away')))
                current_root.mkdir()
                (current_root / 'workspace').mkdir()
                (current_root / 'workspace' / 'a.md').write_text('kept a\n')
                return real_registry_plan(current_pin, pristine_pin, candidate_paths)

            with mock.patch.object(side_by_side, '_registry_plan', drifting_registry_plan):
                migrate_result = _migrate(
                    current_root, destination, target_dir, target_sha, result.plan, result.digest)

            self.assertFalse(migrate_result.ready)
            self.assertEqual('stale_state', migrate_result.failure)
            self.assertFalse(Path(destination, 'workspace', 'a.md').exists())

    def test_source_root_replaced_during_the_read_itself_is_detected_before_write(self):
        """`current_root` is renamed away and replaced by a symlink to
        an outside tree, injected immediately before the REAL
        `_safe_read_regular` delegate call for the copy loop's own
        read (not classification's earlier read of the same file) —
        proving the pinned fd still returns the OLD directory's bytes
        (containment holds), but that read must never be trusted and
        written once the pathname no longer identifies the selected
        installation.
        """
        with tempfile.TemporaryDirectory() as workdir:
            target_dir, target_sha = _build_target_repo(workdir, _base_target_files())
            current_root = Path(workdir, 'current')
            _write_tree(current_root, {'workspace/a.md': 'kept a\n'})
            destination = Path(workdir, 'dest')
            outside = Path(workdir, 'outside_current')
            (outside / 'workspace').mkdir(parents=True)
            (outside / 'workspace' / 'a.md').write_text(self._SECRET + '\n')

            result = _preview(current_root, destination, target_dir, target_sha)
            self.assertEqual(('workspace/a.md',), result.plan.kept)

            real_safe_read_regular = side_by_side._safe_read_regular
            calls = {'count': 0}

            def racing_safe_read_regular(root, relative):
                if relative == 'workspace/a.md' and root.path == current_root:
                    calls['count'] += 1
                    if calls['count'] == 2:  # 1st = classification hash, 2nd = copy-loop read
                        import shutil
                        shutil.move(str(current_root), str(Path(workdir, 'current_moved_away')))
                        os.symlink(outside, current_root)
                return real_safe_read_regular(root, relative)

            with mock.patch.object(side_by_side, '_safe_read_regular', racing_safe_read_regular):
                migrate_result = _migrate(
                    current_root, destination, target_dir, target_sha, result.plan, result.digest)

            self.assertEqual(2, calls['count'])
            self.assertFalse(migrate_result.ready)
            self.assertIn(migrate_result.failure, ('concurrent_change', 'stale_state'))
            self.assertNotIn(self._SECRET, repr(migrate_result))
            self.assertFalse(Path(destination, 'workspace', 'a.md').exists())

    def test_source_root_replaced_by_a_new_real_directory_during_the_read_itself_is_detected(self):
        """Same read-window race, but the replacement is an entirely
        different REAL directory with BYTE-IDENTICAL content at the
        same relative path — never a symlink — proving the post-read
        check is inode/device identity, not content comparison or
        symlink rejection: the hash check alone would pass.
        """
        with tempfile.TemporaryDirectory() as workdir:
            target_dir, target_sha = _build_target_repo(workdir, _base_target_files())
            current_root = Path(workdir, 'current')
            _write_tree(current_root, {'workspace/a.md': 'kept a\n'})
            destination = Path(workdir, 'dest')

            result = _preview(current_root, destination, target_dir, target_sha)
            self.assertEqual(('workspace/a.md',), result.plan.kept)

            real_safe_read_regular = side_by_side._safe_read_regular
            calls = {'count': 0}

            def racing_safe_read_regular(root, relative):
                if relative == 'workspace/a.md' and root.path == current_root:
                    calls['count'] += 1
                    if calls['count'] == 2:
                        import shutil
                        shutil.move(str(current_root), str(Path(workdir, 'current_moved_away')))
                        current_root.mkdir()
                        (current_root / 'workspace').mkdir()
                        (current_root / 'workspace' / 'a.md').write_text('kept a\n')
                return real_safe_read_regular(root, relative)

            with mock.patch.object(side_by_side, '_safe_read_regular', racing_safe_read_regular):
                migrate_result = _migrate(
                    current_root, destination, target_dir, target_sha, result.plan, result.digest)

            self.assertEqual(2, calls['count'])
            self.assertFalse(migrate_result.ready)
            self.assertIn(migrate_result.failure, ('concurrent_change', 'stale_state'))
            self.assertFalse(Path(destination, 'workspace', 'a.md').exists())


class SideBySideScanTreeTests(unittest.TestCase):
    """`_scan_tree` enumerates entirely through the pinned root's own
    fd (and `dir_fd`-relative descendants), never a pathname-based
    `os.walk`/`rglob`/`iterdir` — these tests prove that directly,
    including the specific ABA swap-and-restore sequence a pathname-
    based walk could not have resisted.
    """

    def test_scan_tree_pathname_aba_swap_cannot_omit_a_pinned_file(self):
        """Reproduces the exact race: root A is pinned (it contains
        `workspace/keep.md`); while the walk is in progress the
        SELECTED PATHNAME is renamed away, a different real directory
        B (which does NOT contain `keep.md`) is renamed to that exact
        pathname, the walk proceeds, then B is renamed away and the
        SAME physical A (same inode, via `os.rename`, never a fresh
        `mkdir`) is restored before any post-check runs. Against the
        pre-fix `os.walk(pinned.path)` implementation this silently
        omitted `keep.md` from BOTH `files` and `unsafe` (confirmed
        directly against that implementation before this fix existed).
        The fix removes the pathname step entirely, so patching
        `os.walk` — which the current implementation never calls — has
        no effect at all: the mock's return value is simply never
        consulted.
        """
        with tempfile.TemporaryDirectory() as workdir:
            workdir = os.path.realpath(workdir)
            root_a = Path(workdir, 'selected')
            _write_tree(root_a, {'workspace/keep.md': 'keep me\n'})
            root_b_parked = Path(workdir, 'root_b_parked')
            _write_tree(root_b_parked, {'workspace/placeholder.md': 'no keep.md here\n'})
            root_a_parked = Path(workdir, 'root_a_parked')

            pin = side_by_side._pin_root(root_a)
            try:
                real_walk = os.walk

                def aba_walk(path, **kwargs):
                    os.rename(str(root_a), str(root_a_parked))
                    os.rename(str(root_b_parked), str(root_a))
                    materialized = list(real_walk(path, **kwargs))
                    os.rename(str(root_a), str(root_b_parked))
                    os.rename(str(root_a_parked), str(root_a))
                    return iter(materialized)

                with mock.patch('os.walk', aba_walk):
                    files, unsafe = side_by_side._scan_tree(pin)
            finally:
                pin.close()

            self.assertIn('workspace/keep.md', files)
            self.assertEqual((), unsafe)

    def test_scan_tree_never_calls_pathname_based_os_walk(self):
        """`os.walk` must never even be invoked; also doubles as a
        nested-regular-file sanity check.
        """
        with tempfile.TemporaryDirectory() as workdir:
            root = Path(workdir, 'root')
            _write_tree(root, {'workspace/a.md': 'x\n', 'workspace/sub/b.md': 'y\n'})
            pin = side_by_side._pin_root(root)
            try:
                with mock.patch('os.walk',
                                 side_effect=AssertionError('os.walk must never be called')):
                    files, unsafe = side_by_side._scan_tree(pin)
            finally:
                pin.close()
            self.assertEqual({'workspace/a.md', 'workspace/sub/b.md'}, set(files))
            self.assertEqual((), unsafe)

    def test_scan_tree_symlinked_directory_is_unsafe_and_never_descended(self):
        with tempfile.TemporaryDirectory() as workdir:
            root = Path(workdir, 'root')
            root.mkdir()
            outside = Path(workdir, 'outside')
            _write_tree(outside, {'secret.md': 'should never be reached\n'})
            os.symlink(outside, Path(root, 'workspace'))
            pin = side_by_side._pin_root(root)
            try:
                files, unsafe = side_by_side._scan_tree(pin)
            finally:
                pin.close()
            self.assertEqual({}, files)
            self.assertIn('workspace', unsafe)

    def test_scan_tree_entry_that_vanishes_between_listing_and_open_is_marked_unsafe(self):
        """A name `os.scandir` just listed but that fails to open
        moments later (deleted, permission revoked, or otherwise) must
        be reported unsafe, never silently treated as though it had
        never existed — a silently 'absent' path would be
        indistinguishable from one that legitimately never existed,
        which is exactly the hazard the old pathname-walk's own
        before/after bracketing could not prevent mid-walk.
        """
        with tempfile.TemporaryDirectory() as workdir:
            root = Path(workdir, 'root')
            _write_tree(root, {'workspace/a.md': 'x\n', 'workspace/b.md': 'y\n'})
            pin = side_by_side._pin_root(root)
            try:
                real_open = os.open

                def flaky_open(name, flags, dir_fd=None, **kwargs):
                    if name == 'b.md':
                        raise FileNotFoundError('simulated disappearance between listing and open')
                    return real_open(name, flags, dir_fd=dir_fd, **kwargs)

                with mock.patch('os.open', side_effect=flaky_open):
                    files, unsafe = side_by_side._scan_tree(pin)
            finally:
                pin.close()
            self.assertEqual({'workspace/a.md'}, set(files))
            self.assertIn('workspace/b.md', unsafe)

    def test_classify_workspace_preserves_current_only_file_despite_pathname_aba_during_scan(self):
        """Same ABA sequence, exercised through the real production
        `classify_workspace` entry point (one level above `_scan_tree`)
        rather than the private helper directly: the swap is gated to
        fire only for the exact pinned root fd `classify_workspace`
        already holds, so it affects nothing else `os.scandir` touches
        during the same call (notably the separate pristine-root scan).
        """
        with tempfile.TemporaryDirectory() as workdir:
            workdir = os.path.realpath(workdir)
            current_root = Path(workdir, 'current')
            _write_tree(current_root, {'workspace/keep.md': 'keep me\n'})
            pristine_root = Path(workdir, 'pristine')
            _write_tree(pristine_root, {'system/placeholder.txt': 'x\n'})
            root_b_parked = Path(workdir, 'root_b_parked')
            _write_tree(root_b_parked, {'workspace/placeholder.md': 'no keep.md here\n'})
            root_a_parked = Path(workdir, 'root_a_parked')

            current_pin = side_by_side._pin_root(current_root)
            pristine_pin = side_by_side._pin_root(pristine_root)
            try:
                real_scandir = os.scandir
                target_fd = current_pin.fd
                state = {'swapped': False}

                def aba_scandir(arg):
                    if arg == target_fd and not state['swapped']:
                        state['swapped'] = True
                        os.rename(str(current_root), str(root_a_parked))
                        os.rename(str(root_b_parked), str(current_root))
                        try:
                            return real_scandir(arg)
                        finally:
                            os.rename(str(current_root), str(root_b_parked))
                            os.rename(str(root_a_parked), str(current_root))
                    return real_scandir(arg)

                with mock.patch('os.scandir', aba_scandir):
                    plan = side_by_side.classify_workspace(current_pin, pristine_pin)
            finally:
                current_pin.close()
                pristine_pin.close()

            self.assertIn('workspace/keep.md', plan.kept)


class SideBySideCanonicalRegistryIdentityTests(unittest.TestCase):
    """Gap 2: cross-side (target vs. current) registry comparisons must
    use canonical, trailing-slash-insensitive target identity, and a
    registry target denotes an actual DIRECTORY, not a path that merely
    happens to have a regular file sitting exactly at that name.
    """

    def test_target_trailing_slash_current_no_slash_same_mapping_is_not_a_conflict(self):
        with tempfile.TemporaryDirectory() as workdir:
            files = _base_target_files({
                'system/routing/context_registry.md':
                    SideBySideRegistryTests._registry_text([('alpha', 'workspace/context/a/')]),
                'workspace/context/a/existing.md': 'x\n',
            })
            target_dir, target_sha = _build_target_repo(workdir, files)
            current_root = Path(workdir, 'current')
            _write_tree(current_root, {
                'system/routing/context_registry.md':
                    SideBySideRegistryTests._registry_text([('alpha', 'workspace/context/a')]),
            })
            destination = Path(workdir, 'dest')

            result = _preview(current_root, destination, target_dir, target_sha)

            self.assertEqual((), result.plan.registry.conflicts)
            self.assertEqual((), result.plan.registry.carried)

            migrate_result = _migrate(
                current_root, destination, target_dir, target_sha, result.plan, result.digest)
            self.assertTrue(migrate_result.ready)
            registry_text = Path(destination, 'system', 'routing', 'context_registry.md').read_text()
            self.assertEqual(1, registry_text.count('alpha'))

    def test_target_no_slash_current_trailing_slash_same_mapping_is_not_a_conflict(self):
        with tempfile.TemporaryDirectory() as workdir:
            files = _base_target_files({
                'system/routing/context_registry.md':
                    SideBySideRegistryTests._registry_text([('alpha', 'workspace/context/a')]),
                'workspace/context/a/existing.md': 'x\n',
            })
            target_dir, target_sha = _build_target_repo(workdir, files)
            current_root = Path(workdir, 'current')
            _write_tree(current_root, {
                'system/routing/context_registry.md':
                    SideBySideRegistryTests._registry_text([('alpha', 'workspace/context/a/')]),
            })
            destination = Path(workdir, 'dest')

            result = _preview(current_root, destination, target_dir, target_sha)

            self.assertEqual((), result.plan.registry.conflicts)
            self.assertEqual((), result.plan.registry.carried)

    def test_regular_file_at_exact_scope_path_does_not_count_as_preserved_directory(self):
        """The candidate contains a regular file at EXACTLY
        `workspace/context/foo` (not a directory). The current registry
        maps `foo → workspace/context/foo`. Since no resulting candidate
        path exists STRICTLY BENEATH `workspace/context/foo/`, the
        mapping is not preserved/carriable — it must be dropped, never
        silently carried on the assumption a file-shaped path implies
        the directory it is named after.
        """
        with tempfile.TemporaryDirectory() as workdir:
            files = _base_target_files({
                'system/routing/context_registry.md': SideBySideRegistryTests._registry_text([]),
                'workspace/context/foo': 'this is a FILE, not a directory\n',
            })
            target_dir, target_sha = _build_target_repo(workdir, files)
            current_root = Path(workdir, 'current')
            _write_tree(current_root, {
                'system/routing/context_registry.md':
                    SideBySideRegistryTests._registry_text([('foo', 'workspace/context/foo')]),
            })
            destination = Path(workdir, 'dest')

            result = _preview(current_root, destination, target_dir, target_sha)

            self.assertIn(
                side_by_side.RegistryMapping('foo', 'workspace/context/foo'), result.plan.registry.dropped)
            self.assertEqual((), result.plan.registry.carried)
            self.assertEqual((), result.plan.registry.conflicts)


if __name__ == '__main__':
    unittest.main()
