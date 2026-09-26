#!/usr/bin/env python3
"""Reject private or machine-specific material in a public distribution."""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path


TEXT_SUFFIXES = {".json", ".md", ".py", ".toml", ".txt", ".yaml", ".yml"}
SKIP_PARTS = {".git", ".superpowers", "__pycache__"}
SELF_FIXTURES = {
    "system/tests/validation/test_validate_public.py",
    "system/validation/validate_public.py",
}
PRIVATE_IDENTIFIERS = {
    "mrAlishah/obsidian-ai-context-source-of-truth",
    "v1.2_ai_personal_source_of_truth",
}
SECRET_KEYS = {
    "access_token",
    "api_key",
    "api_token",
    "aws_secret_access_key",
    "bank_login_credentials",
    "card_cvv",
    "client_secret",
    "password",
    "private_key",
    "recovery_code",
    "session_cookie",
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


def candidate_files(root: Path):
    for path in sorted(root.rglob("*")):
        if not path.is_file() or path.suffix.lower() not in TEXT_SUFFIXES:
            continue
        relative = path.relative_to(root)
        if SKIP_PARTS.intersection(relative.parts) or relative.as_posix() in SELF_FIXTURES:
            continue
        yield path, relative


def run(root: Path) -> list[str]:
    errors: list[str] = []
    for path, relative in candidate_files(root):
        for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
            for identifier in PRIVATE_IDENTIFIERS:
                if identifier in line:
                    errors.append(
                        f"{relative}:{number}: private source identifier {identifier!r} is forbidden"
                    )
            if HOME_PATH_RE.search(line):
                errors.append(f"{relative}:{number}: user-specific home path is forbidden")
            if PRIVATE_KEY_RE.search(line):
                errors.append(f"{relative}:{number}: private key material is forbidden")
            match = ASSIGNMENT_RE.match(line)
            if not match or match.group(1).lower() not in SECRET_KEYS:
                continue
            value = match.group(2).strip().strip("`\"'").lower()
            if value in SAFE_SECRET_VALUES or value.startswith("<") or value.startswith("{{"):
                continue
            errors.append(f"{relative}:{number}: possible raw secret assigned to {match.group(1).lower()!r}")
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
