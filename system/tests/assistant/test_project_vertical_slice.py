from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from system.validation import validate_v1


PROJECT = "workspace/context/personal/projects/german_learning"
SCOPE = "personal/projects/german_learning"


class ProjectVerticalSliceTests(unittest.TestCase):
    def repository(self, root: Path) -> None:
        for name in ("workspace", "system", "guides"):
            (root / name).mkdir()

    def write_module(self, root: Path, name: str, body: str) -> None:
        path = root / PROJECT / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(f"---\nai_access: allow\n---\n{body}\n", encoding="utf-8")

    def register_scope(self, root: Path) -> None:
        path = root / "system/routing/context_registry.md"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            "# context_registry\n\n## registered_scopes\n\n```text\n"
            f"{SCOPE}\n→ {PROJECT}/\n"
            "```\n",
            encoding="utf-8",
        )

    def create_project(self, root: Path) -> None:
        self.write_module(root, "project.md", "# German learning\n\nLearn German for daily life.")
        self.write_module(root, "current_state.md", "# current_state\n\n- level: A1")

    def test_rejects_project_without_registered_scope(self):
        with TemporaryDirectory() as directory:
            root = Path(directory)
            self.repository(root)
            self.create_project(root)

            errors = validate_v1.run(root, "personal")

            self.assertTrue(any("unregistered canonical scope" in error for error in errors), errors)

    def test_rejects_project_context_without_project_owner(self):
        with TemporaryDirectory() as directory:
            root = Path(directory)
            self.repository(root)
            self.write_module(root, "current_state.md", "# current_state\n\n- level: A1")

            errors = validate_v1.run(root, "personal")

            self.assertTrue(any("without project.md owner" in error for error in errors), errors)

    def test_create_register_validate_update_validate(self):
        with TemporaryDirectory() as directory:
            root = Path(directory)
            self.repository(root)
            self.create_project(root)
            self.register_scope(root)

            self.assertEqual([], validate_v1.run(root, "personal"))

            self.write_module(
                root,
                "current_state.md",
                "# current_state\n\n- level: A2\n- current_focus: conversation practice",
            )

            self.assertEqual([], validate_v1.run(root, "personal"))


if __name__ == "__main__":
    unittest.main()
