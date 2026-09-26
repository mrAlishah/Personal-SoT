from contextlib import redirect_stdout
from io import StringIO
import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

from system.prompts import explorer
from system.prompts.explorer import PromptQuery, search
from system.validation import validate_prompts


class PromptExplorerTests(unittest.TestCase):
    def repository(self, root: Path) -> None:
        for name in ("workspace", "system", "guides"):
            (root / name).mkdir()

    def write_prompt(
        self,
        root: Path,
        identity: str,
        *,
        status: str = "active",
        tags: tuple[str, ...] = (),
        required: tuple[str, ...] = (),
        optional: tuple[str, ...] = (),
        profiles: tuple[str, ...] = (),
        formats: tuple[str, ...] = (),
        tone: str | None = None,
        depth: str | None = None,
        owned_assets: tuple[str, ...] = (),
        body: str = "Do the requested task.",
    ) -> Path:
        path = root / "workspace" / "prompts" / f"{identity}.md"
        path.parent.mkdir(parents=True, exist_ok=True)
        fields = [
            "---",
            f"prompt_status: {status}",
            "prompt_tags:",
            *(f"  - {value}" for value in tags),
            "prompt_profiles:",
            *(f"  - {value}" for value in profiles),
            "prompt_formats:",
            *(f"  - {value}" for value in formats),
            *( [f"prompt_tone: {tone}"] if tone else [] ),
            *( [f"prompt_depth: {depth}"] if depth else [] ),
            "required_params:",
            *(f"  - {value}" for value in required),
            "optional_params:",
            *(f"  - {value}" for value in optional),
            "owned_assets:",
            *(f"  - {value}" for value in owned_assets),
            "---",
            body,
            "",
        ]
        path.write_text("\n".join(fields), encoding="utf-8")
        return path

    def test_exact_identity_uses_current_canonical_path(self):
        with TemporaryDirectory() as directory:
            root = Path(directory)
            self.repository(root)
            self.write_prompt(root, "coding/review_pr", tags=("review",))

            report = search(root, PromptQuery(identity="coding/review_pr"))

            self.assertEqual(["coding/review_pr"], [item.identity for item in report.matches])

    def test_exact_filters_use_and_and_list_subset_semantics(self):
        with TemporaryDirectory() as directory:
            root = Path(directory)
            self.repository(root)
            self.write_prompt(
                root,
                "coding/review_pr",
                tags=("review", "code"),
                required=("diff", "goal"),
                optional=("focus",),
                body="Review {{diff}} for {{goal}} with {{focus}}.",
            )
            self.write_prompt(
                root,
                "coding/explain_pr",
                tags=("review",),
                required=("diff",),
                body="Explain {{diff}}.",
            )

            report = search(
                root,
                PromptQuery(
                    path_prefix="coding",
                    prompt_tags=("review", "code"),
                    required_params=("diff", "goal"),
                    optional_params=("focus",),
                ),
            )

            self.assertEqual(["coding/review_pr"], [item.identity for item in report.matches])

    def test_ranking_and_identity_tie_break_are_deterministic(self):
        with TemporaryDirectory() as directory:
            root = Path(directory)
            self.repository(root)
            self.write_prompt(root, "coding/review_code", tags=("review", "code"))
            self.write_prompt(root, "coding/code_review", tags=("review", "code"))

            first = search(root, PromptQuery(text="review code"))
            second = search(root, PromptQuery(text="review code"))

            expected = ["coding/code_review", "coding/review_code"]
            self.assertEqual(expected, [item.identity for item in first.matches])
            self.assertEqual(expected, [item.identity for item in second.matches])

    def test_unicode_tokens_are_deterministic(self):
        with TemporaryDirectory() as directory:
            root = Path(directory)
            self.repository(root)
            self.write_prompt(root, "coding/code_review", tags=("code",))
            self.write_prompt(root, "coding/code_translate", tags=("code",))

            first = search(root, PromptQuery(text="بررسی code"))
            second = search(root, PromptQuery(text="بررسی code"))

            expected = ["coding/code_review", "coding/code_translate"]
            self.assertEqual(expected, [item.identity for item in first.matches])
            self.assertEqual(expected, [item.identity for item in second.matches])

    def test_status_rules_hide_draft_and_deprecated_by_default(self):
        with TemporaryDirectory() as directory:
            root = Path(directory)
            self.repository(root)
            self.write_prompt(root, "status/active", tags=("status",))
            self.write_prompt(root, "status/draft", status="draft", tags=("status",))
            self.write_prompt(root, "status/deprecated", status="deprecated", tags=("status",))

            default = search(root, PromptQuery(text="status"))
            draft = search(root, PromptQuery(identity="status/draft", status="draft"))
            deprecated = search(
                root,
                PromptQuery(identity="status/deprecated", status="deprecated"),
            )

            self.assertEqual(["status/active"], [item.identity for item in default.matches])
            self.assertEqual(["status/draft"], [item.identity for item in draft.matches])
            self.assertEqual(["status/deprecated"], [item.identity for item in deprecated.matches])
            self.assertEqual("deprecated", deprecated.matches[0].warning)

    def test_invalid_or_unresolved_prompt_is_not_recommended(self):
        with TemporaryDirectory() as directory:
            root = Path(directory)
            self.repository(root)
            self.write_prompt(
                root,
                "coding/missing_profile",
                tags=("coding",),
                profiles=("does_not_exist",),
            )

            report = search(root, PromptQuery(text="coding"))

            self.assertEqual((), report.matches)
            self.assertEqual(1, report.unavailable_count)

    def test_owned_assets_do_not_filter_or_rank(self):
        with TemporaryDirectory() as directory:
            root = Path(directory)
            self.repository(root)
            asset = root / "workspace/prompts/_assets/assets/with_asset/example.txt"
            asset.parent.mkdir(parents=True)
            asset.write_text("example", encoding="utf-8")
            self.write_prompt(root, "assets/no_asset", tags=("assets",))
            self.write_prompt(
                root,
                "assets/with_asset",
                tags=("assets",),
                owned_assets=("workspace/prompts/_assets/assets/with_asset/example.txt",),
            )

            report = search(root, PromptQuery(text="assets"))

            self.assertEqual(
                ["assets/no_asset", "assets/with_asset"],
                [item.identity for item in report.matches],
            )

    def test_unmatched_prompt_body_is_not_validated(self):
        with TemporaryDirectory() as directory:
            root = Path(directory)
            self.repository(root)
            matched = self.write_prompt(root, "coding/review", tags=("review",))
            self.write_prompt(root, "language/translate", tags=("translate",))

            with patch.object(validate_prompts, "validate_path", return_value=[]) as validator:
                report = search(root, PromptQuery(text="review"))

            self.assertEqual(["coding/review"], [item.identity for item in report.matches])
            self.assertEqual([matched.resolve()], [call.args[1] for call in validator.call_args_list])

    def test_validation_stops_at_twenty_candidates_and_reports_incomplete(self):
        with TemporaryDirectory() as directory:
            root = Path(directory)
            self.repository(root)
            for number in range(25):
                self.write_prompt(root, f"bulk/match_{number:02d}", tags=("match",))

            with patch.object(validate_prompts, "validate_path", return_value=["invalid"]) as validator:
                report = search(root, PromptQuery(text="match", limit=5))

            self.assertEqual(20, validator.call_count)
            self.assertEqual(20, report.validated_count)
            self.assertEqual(20, report.unavailable_count)
            self.assertTrue(report.incomplete)

    def test_does_not_create_catalog_or_change_repository_bytes(self):
        with TemporaryDirectory() as directory:
            root = Path(directory)
            self.repository(root)
            self.write_prompt(root, "coding/review", tags=("review",))
            before = {
                path.relative_to(root).as_posix(): path.read_bytes()
                for path in root.rglob("*")
                if path.is_file()
            }

            search(root, PromptQuery(text="review"))

            after = {
                path.relative_to(root).as_posix(): path.read_bytes()
                for path in root.rglob("*")
                if path.is_file()
            }
            self.assertEqual(before, after)

    def test_skips_symlink_that_escapes_prompt_root(self):
        with TemporaryDirectory() as directory, TemporaryDirectory() as outside:
            root = Path(directory)
            self.repository(root)
            external = Path(outside) / "private.md"
            external.write_text(
                "---\nprompt_status: active\nprompt_tags:\n  - private\n---\nsecret body\n",
                encoding="utf-8",
            )
            link = root / "workspace/prompts/private/external.md"
            link.parent.mkdir(parents=True)
            link.symlink_to(external)

            report = search(root, PromptQuery(text="private"))

            self.assertEqual((), report.matches)

    def test_unclosed_frontmatter_is_unavailable_without_body_validation(self):
        with TemporaryDirectory() as directory:
            root = Path(directory)
            self.repository(root)
            path = root / "workspace/prompts/broken/unclosed.md"
            path.parent.mkdir(parents=True)
            path.write_text(
                "---\nprompt_status: active\nprompt_tags:\n  - broken\nBODY MUST NOT VALIDATE\n",
                encoding="utf-8",
            )

            with patch.object(validate_prompts, "validate_path", return_value=[]) as validator:
                report = search(root, PromptQuery(text="broken"))

            self.assertEqual((), report.matches)
            validator.assert_not_called()

    def test_unclosed_frontmatter_read_is_bounded(self):
        class Source:
            def __init__(self):
                self.calls = 0

            def __enter__(self):
                return self

            def __exit__(self, *_):
                return False

            def readline(self):
                self.calls += 1
                if self.calls == 1:
                    return b"---\n"
                if self.calls <= 257:
                    return b"# unclosed frontmatter\n"
                raise AssertionError("frontmatter reader crossed its metadata bound")

        class ManifestPath:
            def __init__(self, source):
                self.source = source

            def open(self, mode):
                self.mode = mode
                return self.source

        source = Source()

        keys, _, _ = validate_prompts.read_manifest(ManifestPath(source))

        self.assertEqual(set(), keys)
        self.assertLessEqual(source.calls, 257)

    def test_cli_emits_metadata_json_without_prompt_body(self):
        with TemporaryDirectory() as directory:
            root = Path(directory)
            self.repository(root)
            self.write_prompt(
                root,
                "coding/review",
                tags=("review",),
                body="PRIVATE BODY MARKER",
            )
            output = StringIO()

            with patch("sys.argv", ["explorer", "--root", str(root), "--query", "review"]):
                with redirect_stdout(output):
                    result = explorer.main()

            payload = json.loads(output.getvalue())
            self.assertEqual(0, result)
            self.assertEqual("coding/review", payload["matches"][0]["identity"])
            self.assertNotIn("PRIVATE BODY MARKER", output.getvalue())


if __name__ == "__main__":
    unittest.main()
