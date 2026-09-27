from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from system.validation import validate_prompts, validate_v1


class CoreValidationTests(unittest.TestCase):
    def test_ignores_python_bytecode_cache(self):
        with TemporaryDirectory() as directory:
            root = Path(directory)
            for name in ("workspace", "system", "guides"):
                (root / name).mkdir()
            cache = root / "system" / "validation" / "__pycache__"
            cache.mkdir(parents=True)
            (cache / "validator.cpython-314.pyc").write_bytes(b"generated")

            self.assertEqual([], validate_v1.run(root, "core"))

    def test_profile_filename_uses_profile_specific_identity_grammar(self):
        with TemporaryDirectory() as directory:
            root = Path(directory)
            for name in ("workspace", "system", "guides"):
                (root / name).mkdir()
            profiles = root / "workspace/profiles"
            profiles.mkdir()
            (profiles / "g.architecture.review.md").write_text("---\n---\n", encoding="utf-8")

            errors = []
            validate_v1.validate_names(root, errors)

            self.assertEqual([], errors)

    def test_profile_filename_rejects_underscored_built_in_identity(self):
        with TemporaryDirectory() as directory:
            root = Path(directory)
            for name in ("workspace", "system", "guides"):
                (root / name).mkdir()
            profiles = root / "workspace/profiles"
            profiles.mkdir()
            (profiles / "g.problem_solving.md").write_text("---\n---\n", encoding="utf-8")

            errors = []
            validate_v1.validate_names(root, errors)

            self.assertTrue(any("g.problem_solving" in error for error in errors))

    def test_dot_names_remain_invalid_outside_profiles(self):
        with TemporaryDirectory() as directory:
            root = Path(directory)
            for name in ("workspace", "system", "guides"):
                (root / name).mkdir()
            prompts = root / "workspace/prompts"
            prompts.mkdir()
            (prompts / "g.example.md").write_text("# example\n", encoding="utf-8")

            errors = []
            validate_v1.validate_names(root, errors)

            self.assertTrue(any("g.example" in error for error in errors))

    def test_prompt_profile_reference_accepts_hierarchical_built_in_identity(self):
        with TemporaryDirectory() as directory:
            root = Path(directory)
            for name in ("workspace", "system", "guides"):
                (root / name).mkdir()
            (root / "workspace/prompts").mkdir()
            (root / "workspace/profiles").mkdir()
            (root / "workspace/profiles/g.coding.md").write_text("---\n---\n", encoding="utf-8")
            source = (
                "---\n"
                "prompt_status: active\n"
                "prompt_tags: []\n"
                "prompt_profiles:\n"
                "  - g.coding\n"
                "prompt_formats: []\n"
                "required_params: []\n"
                "optional_params: []\n"
                "owned_assets: []\n"
                "---\n"
                "Do the task.\n"
            )

            errors = validate_prompts.validate_source(
                root,
                root / "workspace/prompts/example.md",
                source,
            )

            self.assertEqual([], errors)


if __name__ == "__main__":
    unittest.main()
