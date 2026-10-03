from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from system.prompts.builder import (
    ReuseAssessment,
    apply_change,
    choose_action,
    preview_change,
)
from system.prompts.explorer import PromptQuery, search
from system.validation import validate_prompts


class PromptExplorerBuilderEndToEndTests(unittest.TestCase):
    def repository(self, root: Path) -> None:
        for name in ("workspace", "system", "guides"):
            (root / name).mkdir()

    def source(
        self,
        *,
        tags: tuple[str, ...],
        required: tuple[str, ...] = (),
        body: str,
    ) -> str:
        return "\n".join(
            (
                "---",
                "prompt_status: active",
                "prompt_tags:",
                *(f"  - {tag}" for tag in tags),
                "prompt_profiles: []",
                "prompt_formats: []",
                "required_params:",
                *(f"  - {parameter}" for parameter in required),
                "optional_params: []",
                "owned_assets: []",
                "---",
                body,
                "",
            )
        )

    def write_prompt(self, root: Path, identity: str, source: str) -> Path:
        path = root / "workspace" / "prompts" / f"{identity}.md"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(source, encoding="utf-8")
        return path

    def test_beginner_reuse_create_edit_and_stale_flow(self):
        with TemporaryDirectory() as directory:
            root = Path(directory)
            self.repository(root)
            self.write_prompt(
                root,
                "code/review",
                self.source(tags=("code", "review"), body="Review {{input}}."),
            )
            self.write_prompt(
                root,
                "writing/draftemail",
                self.source(
                    tags=("email", "writing"),
                    required=("topic",),
                    body="Draft an email about {{topic}}.",
                ),
            )

            exact = search(root, PromptQuery(identity="code/review"))
            self.assertEqual(
                ("reuse_exact", "code/review"),
                choose_action(ReuseAssessment(exact_identity=exact.matches[0].identity)),
            )

            parameterized = search(root, PromptQuery(text="draft email"))
            self.assertEqual(("topic",), parameterized.matches[0].required_params)
            self.assertEqual(
                ("reuse_parameterized", "writing/draftemail"),
                choose_action(
                    ReuseAssessment(parameterized_identity=parameterized.matches[0].identity)
                ),
            )

            unmatched = search(root, PromptQuery(text="compare budget forecast"))
            self.assertEqual((), unmatched.matches)
            self.assertEqual(("create", None), choose_action(ReuseAssessment()))

            identity = "planning/comparebudget"
            created_source = self.source(
                tags=("budget", "planning"),
                body="Compare the budget information in {{input}}.",
            )
            preview_only = preview_change(
                root,
                "create",
                identity,
                created_source,
                same_semantic_owner=False,
                fact_safe=True,
                write_capable=False,
            )
            preview_result = apply_change(root, preview_only, preview_only.confirmation_digest)
            self.assertFalse(preview_result.write_applied)
            self.assertFalse(preview_result.validation_ran)

            local = preview_change(
                root,
                "create",
                identity,
                created_source,
                same_semantic_owner=False,
                fact_safe=True,
                write_capable=True,
            )
            created = apply_change(root, local, local.confirmation_digest)
            self.assertTrue(created.success, created.validation_errors)
            self.assertEqual([], validate_prompts.run(root))

            discovered = search(root, PromptQuery(identity=identity))
            self.assertEqual([identity], [match.identity for match in discovered.matches])

            edited_source = self.source(
                tags=("budget", "planning"),
                body="Compare {{input}} and explain the most important budget trade-offs.",
            )
            edit = preview_change(
                root,
                "edit",
                identity,
                edited_source,
                same_semantic_owner=True,
                fact_safe=True,
                write_capable=True,
            )
            edited = apply_change(root, edit, edit.confirmation_digest)
            self.assertTrue(edited.success, edited.validation_errors)

            stale = preview_change(
                root,
                "edit",
                identity,
                self.source(
                    tags=("budget", "planning"),
                    body="A later proposed edit for {{input}}.",
                ),
                same_semantic_owner=True,
                fact_safe=True,
                write_capable=True,
            )
            target = root / stale.target
            target.write_text(
                self.source(
                    tags=("budget", "planning"),
                    body="A concurrent user edit for {{input}}.",
                ),
                encoding="utf-8",
            )
            stale_result = apply_change(root, stale, stale.confirmation_digest)
            self.assertFalse(stale_result.write_applied)
            self.assertIn("concurrent user edit", target.read_text(encoding="utf-8").lower())


if __name__ == "__main__":
    unittest.main()
