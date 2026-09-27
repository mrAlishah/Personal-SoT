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
        path.write_text(source, encoding="utf-8")
        return path

    def test_discovers_each_lane_from_its_canonical_owner(self):
        expected = {
            "profile": "g.research",
            "format": "comparison_table",
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
        cases = (
            (CapabilityQuery(text="short", lanes=("depth",)), [("depth", "short")]),
            (CapabilityQuery(text="formal", lanes=("tone",)), [("tone", "formal")]),
            (
                CapabilityQuery(text="comparison_table", lanes=("format",)),
                [("format", "comparison_table")],
            ),
            (
                CapabilityQuery(
                    text="technical learning step_execution teaching",
                    lanes=("profile", "control", "behavior"),
                    limit=4,
                ),
                [
                    ("profile", "g.technical.learning"),
                    ("behavior", "teaching"),
                    ("control", "learning"),
                    ("control", "step_execution"),
                ],
            ),
            (
                CapabilityQuery(text="research deep professional", lanes=("profile",), limit=1),
                [("profile", "g.research")],
            ),
        )

        for query, expected in cases:
            with self.subTest(query=query):
                report = search(ROOT, query)
                actual = [(match.lane, match.identity) for match in report.matches]
                self.assertEqual(expected, actual)

    def test_profile_tie_break_is_deterministic(self):
        first = search(ROOT, CapabilityQuery(text="professional", lanes=("profile",), limit=10))
        second = search(ROOT, CapabilityQuery(text="professional", lanes=("profile",), limit=10))

        expected = ["g.architecture.review", "g.coding", "g.research"]
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

    def test_invalid_built_in_profile_identity_is_not_discovered(self):
        with TemporaryDirectory() as directory:
            root = Path(directory)
            self.repository(root)
            self.write_profile(root, "g.problem_solving", "---\n---\n")

            report = search(
                root,
                CapabilityQuery(identity="g.problem_solving", lanes=("profile",)),
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
