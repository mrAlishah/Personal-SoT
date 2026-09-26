#!/usr/bin/env python3
"""Read-only, beginner-friendly health report for Personal-SoT."""
from __future__ import annotations

import argparse
from dataclasses import dataclass
from pathlib import Path
import sys

if not __package__:
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from system.validation import validate_prompts, validate_public, validate_v1


ENTRYPOINT = "workspace/adapters/runtime_entrypoint.md"
CLIENT_CONFIGS = {
    "codex": ("Codex", "AGENTS.md", "workspace/adapters/AGENTS.md"),
    "claude_code": ("Claude Code", "CLAUDE.md", "workspace/adapters/CLAUDE.md"),
    "chatgpt": (
        "ChatGPT",
        "workspace/adapters/chatgpt_project_instructions.md",
        "workspace/adapters/chatgpt_project_instructions.md",
    ),
    "claude_web": (
        "Claude Web",
        "workspace/adapters/claude_web_project_instructions.md",
        "workspace/adapters/claude_web_project_instructions.md",
    ),
}
SYMBOLS = {"pass": "✓", "warn": "⚠", "fail": "✗"}


@dataclass(frozen=True)
class Finding:
    status: str
    title: str
    problem: str = ""
    importance: str = ""
    blocking: bool = False
    repair: str = ""
    advanced: tuple[str, ...] = ()


@dataclass(frozen=True)
class Report:
    findings: tuple[Finding, ...]

    @property
    def blocked(self) -> bool:
        return any(finding.blocking for finding in self.findings)


def _runtime_finding(root: Path) -> Finding:
    entrypoint = root / ENTRYPOINT
    if not entrypoint.is_file() or not entrypoint.resolve().is_relative_to(root):
        return Finding(
            "fail",
            "Runtime connection is broken",
            "The Personal-SoT entrypoint is missing.",
            "Your AI client cannot load the canonical runtime safely.",
            True,
            "Restore the repository entrypoint, then run Doctor again.",
            (ENTRYPOINT,),
        )

    references = []
    for raw in entrypoint.read_text(encoding="utf-8").splitlines():
        if ":" not in raw or raw.startswith(("#", " ", "\t")):
            continue
        _, value = raw.split(":", 1)
        value = value.strip()
        if value:
            references.append(value)

    unresolved = tuple(
        value
        for value in references
        if Path(value).is_absolute()
        or ".." in Path(value).parts
        or not (root / value).is_file()
        or not (root / value).resolve().is_relative_to(root)
    )
    if unresolved:
        return Finding(
            "fail",
            "Runtime connection is broken",
            f"{len(unresolved)} referenced runtime file(s) cannot be safely resolved inside the repository.",
            "Missing runtime contracts can make Assistant behavior incomplete or unsafe.",
            True,
            "Restore the missing runtime file from a clean repository copy, then run Doctor again.",
            unresolved,
        )
    return Finding("pass", "Runtime entrypoint resolves correctly")


def _validator_finding(
    errors: list[str],
    ok_title: str,
    fail_title: str,
    importance: str,
    repair: str,
) -> Finding:
    if not errors:
        return Finding("pass", ok_title)
    return Finding(
        "fail",
        fail_title,
        f"The canonical validator found {len(errors)} issue(s).",
        importance,
        True,
        repair,
        tuple(errors),
    )


def _client_findings(root: Path, client: str, write_capability: str) -> list[Finding]:
    if client == "unknown":
        return [
            Finding(
                "warn",
                "Active AI client was not identified",
                "Doctor could not verify the configuration used by this session.",
                "Client configuration determines which repository actions are actually available.",
                False,
                "Ask your local agent to run Doctor for the active client.",
            )
        ]

    label, surface_path, config_path = CLIENT_CONFIGS[client]
    surface = root / surface_path
    config = root / config_path
    connected = (
        surface.is_file()
        and config.is_file()
        and (surface_path == config_path or config_path in surface.read_text(encoding="utf-8"))
        and f"entrypoint: {ENTRYPOINT}" in config.read_text(encoding="utf-8")
    )
    if not connected:
        findings = [
            Finding(
                "fail",
                f"{label} configuration is not connected",
                "The client configuration cannot resolve the Personal-SoT entrypoint.",
                "This client may answer without the canonical runtime.",
                True,
                f"Restore the standard {label} configuration, then run Doctor again.",
                (surface_path, config_path),
            )
        ]
    else:
        findings = [Finding("pass", f"{label} configuration detected")]

    if write_capability == "unavailable":
        findings.append(
            Finding(
                "warn",
                f"{label} is preview-only",
                "This session cannot apply canonical changes.",
                "Guidance and previews still work, but no mutation can be reported as complete.",
                False,
                "Use an authorized local agent to apply a confirmed repair proposal.",
            )
        )
    elif write_capability == "unknown":
        findings.append(
            Finding(
                "warn",
                f"{label} write capability is unknown",
                "Repository write permission was not confirmed.",
                "Doctor will not assume that confirmation grants host permission.",
                False,
                "Let the active client report its real capability before approving a repair.",
            )
        )
    return findings


def run(
    root: Path,
    client: str = "unknown",
    write_capability: str = "unknown",
) -> Report:
    root = root.resolve()
    mode = validate_v1.infer_mode(root)
    findings = [
        _runtime_finding(root),
        _validator_finding(
            validate_v1.run(root, mode),
            "Personal workspace is valid",
            "Personal workspace has validation problems",
            "Invalid context, project, profile, access, or references can produce unreliable answers.",
            "Ask the Assistant for a repair proposal based on the validator details, then preview and confirm any write.",
        ),
        _validator_finding(
            validate_prompts.run(root),
            "Prompts are valid",
            "One or more prompts are invalid",
            "An invalid prompt may not resolve or may use unsupported configuration.",
            "Review the affected prompt with the Assistant before using or changing it.",
        ),
        _validator_finding(
            validate_public.run(root),
            "Public-distribution safety check passed",
            "Public-distribution safety check found a problem",
            "Machine-specific paths, private identifiers, or likely secrets must not enter the public product.",
            "Remove or safely replace the reported material through a confirmed repair proposal.",
        ),
    ]
    findings.extend(_client_findings(root, client, write_capability))
    return Report(tuple(findings))


def render(report: Report, advanced: bool = False) -> str:
    lines = ["✗ Setup needs attention" if report.blocked else "✓ Setup is ready"]
    for finding in report.findings:
        lines.append(f"{SYMBOLS[finding.status]} {finding.title}")
        if finding.status == "pass":
            continue
        lines.extend(
            (
                f"  What: {finding.problem}",
                f"  Why it matters: {finding.importance}",
                f"  Blocking: {'yes' if finding.blocking else 'no'}",
                f"  How to fix: {finding.repair}",
            )
        )
        if advanced and finding.advanced:
            lines.append("  Advanced:")
            lines.extend(f"    - {detail}" for detail in finding.advanced)
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[2])
    parser.add_argument("--client", choices=("unknown", *CLIENT_CONFIGS), default="unknown")
    parser.add_argument(
        "--write-capability",
        choices=("unknown", "available", "unavailable"),
        default="unknown",
    )
    parser.add_argument("--advanced", action="store_true")
    args = parser.parse_args()
    report = run(args.root, args.client, args.write_capability)
    print(render(report, args.advanced))
    return 1 if report.blocked else 0


if __name__ == "__main__":
    raise SystemExit(main())
