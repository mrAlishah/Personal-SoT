from pathlib import Path
from tempfile import TemporaryDirectory
from typing import List
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
            profiles = root / "workspace/profiles/g/architecture"
            profiles.mkdir(parents=True)
            (profiles / "review.md").write_text("---\n---\n", encoding="utf-8")

            errors = []
            validate_v1.validate_names(root, errors)

            self.assertEqual([], errors)

    def test_profile_filename_rejects_underscored_built_in_identity(self):
        with TemporaryDirectory() as directory:
            root = Path(directory)
            for name in ("workspace", "system", "guides"):
                (root / name).mkdir()
            profiles = root / "workspace/profiles/g"
            profiles.mkdir(parents=True)
            (profiles / "problem_solving.md").write_text("---\n---\n", encoding="utf-8")

            errors = []
            validate_v1.validate_names(root, errors)

            self.assertTrue(any("g/problem_solving" in error for error in errors))

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

    def test_prompt_profile_reference_accepts_hierarchical_identity(self):
        with TemporaryDirectory() as directory:
            root = Path(directory)
            for name in ("workspace", "system", "guides"):
                (root / name).mkdir()
            (root / "workspace/prompts").mkdir()
            (root / "workspace/profiles").mkdir()
            (root / "workspace/profiles/code").mkdir()
            (root / "workspace/profiles/code/review.md").write_text("---\n---\n", encoding="utf-8")
            source = (
                "---\n"
                "prompt_status: active\n"
                "prompt_tags: []\n"
                "prompt_profiles:\n"
                "  - code/review\n"
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

    def test_control_id_rejects_underscore(self):
        with TemporaryDirectory() as directory:
            root = Path(directory)
            source = (
                "---\n"
                "control_id: a_b\n"
                "control_values:\n"
                "  - on\n"
                "  - off\n"
                "control_default: on\n"
                "---\n"
            )

            errors = validate_v1.validate_control_source(root, root / "system/behavior/example.md", "a_b", source)

            self.assertTrue(any("control_id" in error for error in errors))

    def test_control_id_accepts_strict_segment(self):
        with TemporaryDirectory() as directory:
            root = Path(directory)
            source = (
                "---\n"
                "control_id: clarify\n"
                "control_values:\n"
                "  - on\n"
                "  - off\n"
                "control_default: on\n"
                "---\n"
            )

            errors = validate_v1.validate_control_source(root, root / "system/behavior/example.md", "clarify", source)

            self.assertEqual([], errors)

    def test_format_id_rejects_underscore(self):
        with TemporaryDirectory() as directory:
            root = Path(directory)
            target = root / "workspace/presentation/formats/example.md"
            target.parent.mkdir(parents=True)
            target.write_text(
                "---\nformat_id: a_b\nplacement: inline\n---\n",
                encoding="utf-8",
            )
            registry = root / "system/routing"
            registry.mkdir(parents=True)
            (registry / "switch_registry.md").write_text(
                "## formats\n\n"
                "```text\n"
                "a_b → workspace/presentation/formats/example.md\n"
                "```\n",
                encoding="utf-8",
            )

            errors: List[str] = []
            validate_v1.registered_format_specs(root, errors)

            self.assertTrue(any("format_id" in error for error in errors))

    def test_prompt_path_segment_rejects_underscore(self):
        with TemporaryDirectory() as directory:
            root = Path(directory)
            source = (
                "---\n"
                "prompt_status: active\n"
                "prompt_tags: []\n"
                "prompt_profiles: []\n"
                "prompt_formats: []\n"
                "required_params: []\n"
                "optional_params: []\n"
                "owned_assets: []\n"
                "---\n"
                "Do the task.\n"
            )

            errors = validate_prompts.validate_source(
                root,
                root / "workspace/prompts/code/review_pr.md",
                source,
            )

            self.assertTrue(any("prompt path segment" in error for error in errors))

    def test_prompt_formats_rejects_underscore(self):
        with TemporaryDirectory() as directory:
            root = Path(directory)
            source = (
                "---\n"
                "prompt_status: active\n"
                "prompt_tags: []\n"
                "prompt_profiles: []\n"
                "prompt_formats:\n"
                "  - comparison_table\n"
                "required_params: []\n"
                "optional_params: []\n"
                "owned_assets: []\n"
                "---\n"
                "Do the task.\n"
            )

            errors = validate_prompts.validate_source(
                root,
                root / "workspace/prompts/code/review.md",
                source,
            )

            self.assertTrue(any("invalid format identifier" in error for error in errors))

    def test_owner_field_accepts_product_and_custom(self):
        for value in ("product", "custom"):
            with self.subTest(value=value):
                with TemporaryDirectory() as directory:
                    root = Path(directory)
                    for name in ("workspace", "system", "guides"):
                        (root / name).mkdir()
                    source = f"---\nowner: {value}\n---\n"

                    errors = validate_v1.validate_profile_source(
                        root, root / "workspace/profiles/example.md", source
                    )

                    self.assertEqual([], [error for error in errors if "owner" in error])

    def test_owner_field_rejects_unknown_value(self):
        with TemporaryDirectory() as directory:
            root = Path(directory)
            for name in ("workspace", "system", "guides"):
                (root / name).mkdir()
            source = "---\nowner: shipped\n---\n"

            errors = validate_v1.validate_profile_source(
                root, root / "workspace/profiles/example.md", source
            )

            self.assertTrue(any("owner" in error for error in errors))


if __name__ == "__main__":
    unittest.main()
