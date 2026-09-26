from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from system.validation import validate_public


class PublicValidationTests(unittest.TestCase):
    def validate(self, files: dict[str, str]) -> list[str]:
        with TemporaryDirectory() as directory:
            root = Path(directory)
            for relative, content in files.items():
                path = root / relative
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(content, encoding="utf-8")
            return validate_public.run(root)

    def test_rejects_private_source_identifiers_outside_migration_provenance(self):
        errors = self.validate(
            {
                "workspace/adapters/client.md": (
                    "repository: mrAlishah/obsidian-ai-context-source-of-truth\n"
                    "active_ref: v1.2_ai_personal_source_of_truth\n"
                )
            }
        )

        self.assertEqual(2, len(errors))
        self.assertTrue(all("private source identifier" in error for error in errors))

    def test_allows_private_source_identifiers_in_migration_inventory(self):
        errors = self.validate(
            {
                "guides/developer/migration/public_v1_inventory.md": (
                    "source: mrAlishah/obsidian-ai-context-source-of-truth\n"
                    "active_ref: v1.2_ai_personal_source_of_truth\n"
                )
            }
        )

        self.assertEqual([], errors)

    def test_rejects_real_home_paths_but_allows_placeholders(self):
        errors = self.validate(
            {
                "guides/user/unsafe.md": "source_root: /Users/alice/Documents/sot\n",
                "guides/user/also_unsafe.md": "source_root: /home/bob/sot\n",
                "guides/user/safe.md": "source_root: /Users/<username>/Documents/sot\n",
            }
        )

        self.assertEqual(2, len(errors))
        self.assertTrue(all("user-specific home path" in error for error in errors))

    def test_rejects_raw_secret_assignments_but_allows_safe_sentinels(self):
        errors = self.validate(
            {
                "workspace/context/unsafe.md": "api_token: sk_live_example_value\n",
                "workspace/context/safe.md": "api_token: <not_stored>\npassword: redacted\n",
            }
        )

        self.assertEqual(1, len(errors))
        self.assertIn("possible raw secret", errors[0])


if __name__ == "__main__":
    unittest.main()
