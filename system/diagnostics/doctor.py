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


def _repository_file(root: Path, value: str) -> bool:
    path = Path(value)
    target = root / path
    return (
        not path.is_absolute()
        and ".." not in path.parts
        and target.is_file()
        and target.resolve().is_relative_to(root)
    )


def _fields(path: Path) -> dict[str, str]:
    fields = {}
    for raw in path.read_text(encoding="utf-8").splitlines():
        if ":" not in raw or raw.startswith(("#", " ", "\t")):
            continue
        key, value = raw.split(":", 1)
        if value.strip():
            fields[key.strip()] = value.strip()
    return fields


def _runtime_finding(root: Path) -> Finding:
    entrypoint = root / ENTRYPOINT
    if not _repository_file(root, ENTRYPOINT):
        return Finding(
            "fail",
            "Runtime connection is broken",
            "The Personal-SoT entrypoint is missing.",
            "Your AI client cannot load the canonical runtime safely.",
            True,
            "Restore the repository entrypoint, then run Doctor again.",
            (ENTRYPOINT,),
        )

    unresolved = tuple(value for value in _fields(entrypoint).values() if not _repository_file(root, value))
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


def _adapter_findings(root: Path, adapter: str | None, write_capability: str) -> list[Finding]:
    if adapter is None:
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

    if not _repository_file(root, adapter):
        return [
            Finding(
                "fail",
                "AI client configuration is not connected",
                "The selected adapter cannot be safely resolved inside the repository.",
                "The client may answer without the canonical runtime.",
                True,
                "Select the repository-owned adapter for this client, then run Doctor again.",
                (adapter,),
            )
        ]

    config_path = adapter
    config = root / config_path
    metadata = _fields(config)
    label = metadata.get("client_name")
    surface_path = metadata.get("discovery_surface")
    surface = root / surface_path if surface_path else None
    connected = (
        bool(label)
        and bool(surface_path)
        and metadata.get("entrypoint") == ENTRYPOINT
        and _repository_file(root, surface_path)
        and (surface_path == config_path or config_path in surface.read_text(encoding="utf-8"))
    )
    if not connected:
        label = label or "AI client"
        findings = [
            Finding(
                "fail",
                f"{label} configuration is not connected",
                "The client configuration cannot resolve the Personal-SoT entrypoint.",
                "This client may answer without the canonical runtime.",
                True,
                f"Restore the standard {label} configuration, then run Doctor again.",
                (surface_path or "missing discovery_surface", config_path),
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
    adapter: str | None = None,
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
    findings.extend(_adapter_findings(root, adapter, write_capability))
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
    parser.add_argument("--adapter")
    parser.add_argument(
        "--write-capability",
        choices=("unknown", "available", "unavailable"),
        default="unknown",
    )
    parser.add_argument("--advanced", action="store_true")
    args = parser.parse_args()
    report = run(args.root, args.adapter, args.write_capability)
    print(render(report, args.advanced))
    return 1 if report.blocked else 0


if __name__ == "__main__":
    raise SystemExit(main())
