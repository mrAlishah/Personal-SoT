"""Beginner-safe local runner for the canonical Safe Update workflow.

This module owns no classification, merge, validation, or recovery semantics.
It only renders and loops over system.assistant.update_reporting.run_update_workflow.
"""
from __future__ import annotations

import argparse
import os
from pathlib import Path
import sys

from system.assistant.update_reporting import HostCapability, WorkflowResult, run_update_workflow


_LOCAL_CAPABILITY = HostCapability(
    can_read=True,
    can_write=True,
    can_run_local_commands=True,
)


def _absolute(path) -> Path:
    """Absolute without resolving symlinks; install proof remains fail-closed."""
    return Path(os.path.abspath(os.fspath(path)))


def _render(result: WorkflowResult, out, *, show_digest: bool = False) -> None:
    print(result.beginner.headline, file=out)
    for detail in result.beginner.details:
        print(f"- {detail}", file=out)
    if show_digest and result.confirmation_required and result.digest:
        print(f"confirmation_digest: {result.digest}", file=out)


def _workflow(root: Path, destination: Path | None, confirm_digest: str | None) -> WorkflowResult:
    return run_update_workflow(
        root,
        destination,
        capability=_LOCAL_CAPABILITY,
        confirm_digest=confirm_digest,
    )


def run_interactive(root, destination=None, *, input_fn=input, out=None) -> int:
    """Preview, ask only for required human input, apply, validate, report.

    Normal Git-backed path: one command and one yes/no confirmation.
    If the exact preview becomes stale, the old confirmation is refused,
    the fresh preview is shown, and confirmation is requested again.
    """
    out = sys.stdout if out is None else out
    root = _absolute(root)
    destination = _absolute(destination) if destination is not None else None

    result = _workflow(root, destination, None)
    if result.failure == 'destination_required':
        _render(result, out)
        selected = input_fn("New side-by-side folder: ").strip()
        if not selected:
            print("Nothing was changed.", file=out)
            return 2
        destination = _absolute(selected)
        result = _workflow(root, destination, None)

    while True:
        _render(result, out)
        if result.ready:
            return 0
        if not result.confirmation_required:
            return 2

        answer = input_fn("Apply this update? [y/N] ").strip().lower()
        if answer not in {'y', 'yes'}:
            print("Nothing was changed.", file=out)
            return 0
        if not result.digest:
            print("Update not applied: no confirmable preview was available.", file=out)
            return 2

        result = _workflow(root, destination, result.digest)


def run_non_interactive(root, destination=None, *, confirm_digest: str | None = None, out=None) -> int:
    """Agent handoff: preview once, or apply one exact digest.

    A stale digest is never auto-approved. The returned fresh digest is
    printed and exit code 3 tells the caller to obtain a new confirmation.
    """
    out = sys.stdout if out is None else out
    root = _absolute(root)
    destination = _absolute(destination) if destination is not None else None
    result = _workflow(root, destination, confirm_digest)
    _render(result, out, show_digest=True)

    if confirm_digest is None:
        return 0 if (result.ready or result.confirmation_required) else 2
    if result.ready:
        return 0
    if result.failure == 'stale_state' and result.confirmation_required:
        return 3
    return 2


def main(argv=None, *, default_root=None) -> int:
    parser = argparse.ArgumentParser(
        description="Preview and safely update a Personal-SoT installation."
    )
    parser.add_argument(
        "--root",
        type=Path,
        default=Path.cwd() if default_root is None else Path(default_root),
        help="Personal-SoT root (default: this installation).",
    )
    parser.add_argument(
        "--destination",
        type=Path,
        help="Destination for a no-Git side-by-side update.",
    )
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument(
        "--preview",
        action="store_true",
        help="Print one fresh preview/digest without prompting or writing.",
    )
    mode.add_argument(
        "--confirm-digest",
        help="Apply only this exact previously-previewed digest.",
    )
    args = parser.parse_args(argv)

    if args.preview or args.confirm_digest is not None:
        return run_non_interactive(
            args.root,
            args.destination,
            confirm_digest=args.confirm_digest,
        )
    return run_interactive(args.root, args.destination)


if __name__ == "__main__":
    raise SystemExit(main())
