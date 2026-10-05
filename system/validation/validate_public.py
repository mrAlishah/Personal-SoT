#!/usr/bin/env python3
"""Reject private or machine-specific material in a public distribution."""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

if __package__:
    from .validate_v1 import RAW_SECRET_KEYS
else:
    from validate_v1 import RAW_SECRET_KEYS


TEXT_SUFFIXES = {".json", ".md", ".py", ".toml", ".txt", ".yaml", ".yml"}
SKIP_PARTS = {".git", ".superpowers", ".worktrees", "__pycache__"}
SKIP_PATHS = {
    ".claude/settings.local.json",
}
SELF_FIXTURES = {
    "system/tests/validation/test_validate_public.py",
    "system/validation/validate_public.py",
}
PRIVATE_IDENTIFIERS = {
    "mrAlishah/obsidian-ai-context-source-of-truth",
    "v1.2_ai_personal_source_of_truth",
}
SECRET_KEYS = RAW_SECRET_KEYS | {
    "access_token",
    "api_key",
    "aws_secret_access_key",
    "client_secret",
    "token",
}
SAFE_SECRET_VALUES = {
    "external_reference",
    "none",
    "not_applicable",
    "not_stored",
    "null",
    "redacted",
}
HOME_PATH_RE = re.compile(
    r"(?:/(?:Users|home)/(?!<)[A-Za-z0-9._-]+/|[A-Za-z]:\\Users\\(?!<)[^\\\s]+\\)",
    re.I,
)
PRIVATE_KEY_RE = re.compile(r"-----BEGIN [A-Z0-9 ]*PRIVATE KEY-----")
ASSIGNMENT_RE = re.compile(r"^\s*[-*]?\s*([a-z0-9_]+)\s*[:=]\s*(.+?)\s*$", re.I)


PUBLIC_RUNTIME_ENTRYPOINT_PATH = Path("workspace/adapters/runtime_entrypoint.md")
PUBLIC_RUNTIME_ENTRYPOINT = (
    "# Personal-SoT runtime\n"
    "\n"
    "deployment_config: workspace/adapters/public_bootstrap.md\n"
    "runtime_contract: system/adapters/runtime_bootstrap.md\n"
    "shared_instruction: system/adapters/base_instruction.md\n"
    "assistant_contract: system/assistant/assistant_contract.md\n"
    "guided_flow_contract: system/assistant/guided_flow_contract.md\n"
    "safe_write_contract: system/assistant/safe_write_contract.md\n"
    "setup_workflow: system/assistant/setup_workflow.md\n"
    "update_workflow: system/assistant/update_workflow.md\n"
    "fix_workflow: system/assistant/fix_workflow.md\n"
    "project_workflow: system/assistant/project_workflow.md\n"
    "doctor_contract: system/diagnostics/doctor_contract.md\n"
)


def secret_issues(source: str) -> list[tuple[int, str]]:
    """Value-free findings reusable by host-side content gates."""
    issues = []
    for number, line in enumerate(source.splitlines(), 1):
        if PRIVATE_KEY_RE.search(line):
            issues.append((number, "private key material is forbidden"))
        match = ASSIGNMENT_RE.match(line)
        if not match or match.group(1).lower() not in SECRET_KEYS:
            continue
        value = match.group(2).strip().strip("`\"'").lower()
        if value in SAFE_SECRET_VALUES or value.startswith("<") or value.startswith("{{"):
            continue
        issues.append((number, f"possible raw secret assigned to {match.group(1).lower()!r}"))
    return issues


def contains_raw_secret(source: str) -> bool:
    return bool(secret_issues(source))


def candidate_files(root: Path):
    for path in sorted(root.rglob("*")):
        if not path.is_file() or path.suffix.lower() not in TEXT_SUFFIXES:
            continue
        relative = path.relative_to(root)
        if (
            SKIP_PARTS.intersection(relative.parts)
            or relative.as_posix() in SKIP_PATHS
            or relative.as_posix() in SELF_FIXTURES
        ):
            continue
        yield path, relative


def run(root: Path) -> list[str]:
    errors: list[str] = []
    entrypoint = root / PUBLIC_RUNTIME_ENTRYPOINT_PATH
    if entrypoint.is_file():
        source = entrypoint.read_text(encoding="utf-8")
        if source != PUBLIC_RUNTIME_ENTRYPOINT:
            errors.append(
                f"{PUBLIC_RUNTIME_ENTRYPOINT_PATH}: public runtime entrypoint is a frozen "
                "deployment boundary; reusable product wiring belongs in system/"
            )
    for path, relative in candidate_files(root):
        source = path.read_text(encoding="utf-8")
        for number, message in secret_issues(source):
            errors.append(f"{relative}:{number}: {message}")
        for number, line in enumerate(source.splitlines(), 1):
            for identifier in PRIVATE_IDENTIFIERS:
                if identifier in line:
                    errors.append(
                        f"{relative}:{number}: private source identifier {identifier!r} is forbidden"
                    )
            if HOME_PATH_RE.search(line):
                errors.append(f"{relative}:{number}: user-specific home path is forbidden")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[2])
    root = parser.parse_args().root.resolve()
    errors = run(root)
    if errors:
        print(f"Public distribution validation FAILED ({len(errors)} issue(s))")
        for error in errors:
            print(f"- {error}")
        return 1
    print("Public distribution validation PASSED")
    return 0


if __name__ == "__main__":
    sys.exit(main())
