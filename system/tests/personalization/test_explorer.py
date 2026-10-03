from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from system.personalization.explorer import CapabilityQuery, search


ROOT = Path(__file__).resolve().parents[3]


class PersonalizationExplorerTests(unittest.TestCase):
    def repository(self, root: Path) -> None:
        for name in ("workspace", "system", "guides"):
            (root / name).mkdir()
        (root / "workspace/profiles").mkdir()
        (root / "system/routing").mkdir(parents=True)
        (root / "system/behavior").mkdir()

    def write_profile(self, root: Path, name: str, source: str) -> Path:
        path = root / "workspace/profiles" / f"{name}.md"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(source, encoding="utf-8")
        return path

    def canonical_evidence_repository(self, root: Path) -> None:
        self.repository(root)
        for name in (
            "workspace/presentation/formats",
            "workspace/presentation/tones",
            "workspace/presentation/depth",
        ):
            (root / name).mkdir(parents=True)

        (root / "workspace/presentation/formats/compare.md").write_text(
            "---\nformat_id: compare\nplacement: body\n---\n",
            encoding="utf-8",
        )
        for name in ("formal", "professional"):
            (root / f"workspace/presentation/tones/{name}.md").write_text(
                f"# {name}\n", encoding="utf-8"
            )
        for name in ("short", "deep"):
            (root / f"workspace/presentation/depth/{name}.md").write_text(
                f"# {name}\n", encoding="utf-8"
            )

        (root / "system/behavior/module_catalog.md").write_text(
            "# modules\n\n## teaching.md\n", encoding="utf-8"
        )
        (root / "system/behavior/teaching.md").write_text("# teaching\n", encoding="utf-8")
        for name in ("learning", "steps"):
            (root / f"system/behavior/{name}.md").write_text(
                "---\n"
                f"control_id: {name}\n"
                "control_values:\n"
                '  - "on"\n'
                '  - "off"\n'
                '  - "auto"\n'
                'control_default: "auto"\n'
                "---\n",
                encoding="utf-8",
            )

        (root / "system/routing/switch_registry.md").write_text(
            "# registry\n\n"
            "## formats\n\n```text\n"
            "compare → workspace/presentation/formats/compare.md\n"
            "```\n\n"
            "## tones\n\n```text\n"
            "formal → workspace/presentation/tones/formal.md\n"
            "professional → workspace/presentation/tones/professional.md\n"
            "```\n\n"
            "## depths\n\n```text\n"
            "short → workspace/presentation/depth/short.md\n"
            "deep → workspace/presentation/depth/deep.md\n"
            "```\n\n"
            "## registered_controls\n\n```text\n"
            "learning → system/behavior/learning.md\n"
            "steps → system/behavior/steps.md\n"
            "```\n",
            encoding="utf-8",
        )

        self.write_profile(
            root,
            "tech/learn",
            "---\nbehaviors:\n  - teaching\n---\n",
        )
        self.write_profile(
            root,
            "research/deep",
            "---\ntone: professional\ndepth: deep\n---\n",
        )

    def test_discovers_each_lane_from_its_canonical_owner(self):
        expected = {
            "profile": "research/deep",
            "format": "compare",
            "tone": "formal",
            "depth": "short",
            "control": "learning",
            "behavior": "teaching",
        }

        for lane, identity in expected.items():
            with self.subTest(lane=lane):
                report = search(ROOT, CapabilityQuery(identity=identity, lanes=(lane,)))
                self.assertEqual([(lane, identity)], [(match.lane, match.identity) for match in report.matches])

    def test_classified_beginner_intents_use_only_canonical_evidence(self):
        with TemporaryDirectory() as directory:
            root = Path(directory)
            self.canonical_evidence_repository(root)
            cases = (
                (CapabilityQuery(text="short", lanes=("depth",)), [("depth", "short")]),
                (CapabilityQuery(text="formal", lanes=("tone",)), [("tone", "formal")]),
                (
                    CapabilityQuery(text="compare", lanes=("format",)),
                    [("format", "compare")],
                ),
                (
                    CapabilityQuery(
                        text="learn learning steps teaching",
                        lanes=("profile", "control", "behavior"),
                        limit=4,
                    ),
                    [
                        ("behavior", "teaching"),
                        ("control", "learning"),
                        ("control", "steps"),
                        ("profile", "tech/learn"),
                    ],
                ),
                (
                    CapabilityQuery(text="research deep professional", lanes=("profile",), limit=1),
                    [("profile", "research/deep")],
                ),
            )

            for query, expected in cases:
                with self.subTest(query=query):
                    report = search(root, query)
                    actual = [(match.lane, match.identity) for match in report.matches]
                    self.assertEqual(expected, actual)

    def test_profile_tie_break_is_deterministic(self):
        with TemporaryDirectory() as directory:
            root = Path(directory)
            self.repository(root)
            tones = root / "workspace/presentation/tones"
            tones.mkdir(parents=True)
            (tones / "professional.md").write_text("# professional\n", encoding="utf-8")
            (root / "system/routing/switch_registry.md").write_text(
                "# registry\n\n## tones\n\n```text\n"
                "professional → workspace/presentation/tones/professional.md\n"
                "```\n",
                encoding="utf-8",
            )
            for identity in ("alpha", "beta", "gamma"):
                self.write_profile(
                    root,
                    identity,
                    "---\ntone: professional\n---\n",
                )

            first = search(root, CapabilityQuery(text="professional", lanes=("profile",), limit=10))
            second = search(root, CapabilityQuery(text="professional", lanes=("profile",), limit=10))

            expected = ["alpha", "beta", "gamma"]
            self.assertEqual(expected, [match.identity for match in first.matches])
            self.assertEqual(expected, [match.identity for match in second.matches])

    def test_control_values_and_default_come_from_canonical_target(self):
        report = search(ROOT, CapabilityQuery(identity="learning", lanes=("control",)))

        match = report.matches[0]
        self.assertEqual(("on", "off", "auto"), match.allowed_values)
        self.assertEqual("auto", match.default_value)

    def test_control_rejected_by_validator_is_unavailable(self):
        with TemporaryDirectory() as directory:
            root = Path(directory)
            self.repository(root)
            (root / "system/routing/switch_registry.md").write_text(
                "# registry\n\n## registered_controls\n\n```text\n"
                "learning → system/behavior/learning.md\n```\n",
                encoding="utf-8",
            )
            (root / "system/behavior/learning.md").write_text(
                "---\ncontrol_id: learning\ncontrol_values:\n  - on\n  - on\n"
                "control_default: on\n---\n",
                encoding="utf-8",
            )

            report = search(root, CapabilityQuery(identity="learning", lanes=("control",)))

            self.assertEqual((), report.matches)
            self.assertEqual(1, report.unavailable_count)

    def test_invalid_profile_is_unavailable_not_recommended(self):
        with TemporaryDirectory() as directory:
            root = Path(directory)
            self.repository(root)
            self.write_profile(root, "broken", "---\ntone: missing\n---\n")

            report = search(root, CapabilityQuery(identity="broken", lanes=("profile",)))

            self.assertEqual((), report.matches)
            self.assertEqual(1, report.unavailable_count)

    def test_invalid_nested_profile_identity_is_not_discovered(self):
        with TemporaryDirectory() as directory:
            root = Path(directory)
            self.repository(root)
            (root / "workspace/profiles/code").mkdir()
            self.write_profile(root, "code/problem_solving", "---\n---\n")

            report = search(
                root,
                CapabilityQuery(identity="code/problem_solving", lanes=("profile",)),
            )

            self.assertEqual((), report.matches)

    def test_missing_registry_target_is_unavailable(self):
        with TemporaryDirectory() as directory:
            root = Path(directory)
            self.repository(root)
            (root / "system/routing/switch_registry.md").write_text(
                "# registry\n\n## tones\n\n```text\nformal → workspace/presentation/tones/formal.md\n```\n",
                encoding="utf-8",
            )

            report = search(root, CapabilityQuery(identity="formal", lanes=("tone",)))

            self.assertEqual((), report.matches)
            self.assertEqual(1, report.unavailable_count)

    def test_external_profile_root_symlink_is_not_scanned(self):
        with TemporaryDirectory() as directory, TemporaryDirectory() as outside:
            root = Path(directory)
            self.repository(root)
            (root / "workspace/profiles").rmdir()
            external = Path(outside)
            (external / "private.md").write_text("---\ntone: formal\n---\n", encoding="utf-8")
            (root / "workspace/profiles").symlink_to(external, target_is_directory=True)

            report = search(root, CapabilityQuery(text="private", lanes=("profile",)))

            self.assertEqual((), report.matches)

    def test_unreadable_irrelevant_registry_does_not_break_profile_search(self):
        with TemporaryDirectory() as directory:
            root = Path(directory)
            self.repository(root)
            self.write_profile(root, "empty", "---\n---\n")
            (root / "system/routing/switch_registry.md").write_bytes(b"\xff")

            report = search(root, CapabilityQuery(identity="empty", lanes=("profile",)))

            self.assertEqual(["empty"], [match.identity for match in report.matches])

    def test_unmatched_target_body_is_not_read(self):
        with TemporaryDirectory() as directory:
            root = Path(directory)
            self.repository(root)
            registry = root / "system/routing/switch_registry.md"
            registry.write_text(
                "# registry\n\n## registered_controls\n\n```text\n"
                "learning → system/behavior/learning.md\n"
                "broken → system/behavior/broken.md\n```\n",
                encoding="utf-8",
            )
            (root / "system/behavior/learning.md").write_text(
                "---\ncontrol_id: learning\ncontrol_values:\n  - \"on\"\n  - \"off\"\n"
                "control_default: \"on\"\n---\n",
                encoding="utf-8",
            )
            (root / "system/behavior/broken.md").write_bytes(b"\xff")

            report = search(root, CapabilityQuery(identity="learning", lanes=("control",)))

            self.assertEqual(["learning"], [match.identity for match in report.matches])

    def test_search_does_not_create_secondary_state(self):
        before = {
            path.relative_to(ROOT).as_posix(): path.read_bytes()
            for area in (ROOT / "workspace", ROOT / "system", ROOT / "guides")
            for path in area.rglob("*")
            if path.is_file() and "__pycache__" not in path.parts
        }

        search(ROOT, CapabilityQuery(text="professional", limit=10))

        after = {
            path.relative_to(ROOT).as_posix(): path.read_bytes()
            for area in (ROOT / "workspace", ROOT / "system", ROOT / "guides")
            for path in area.rglob("*")
            if path.is_file() and "__pycache__" not in path.parts
        }
        self.assertEqual(before, after)


if __name__ == "__main__":
    unittest.main()
