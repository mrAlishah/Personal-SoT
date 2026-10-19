"""Beginner-safe local runner for the canonical Safe Update workflow.

This module owns no classification, merge, validation, or recovery semantics.
It only renders and loops over system.assistant.update_reporting.run_update_workflow.
"""
from __future__ import annotations

import argparse
import os
from pathlib import Path
import re
import sys

from system.assistant.update_reporting import HostCapability, WorkflowResult, run_update_workflow


_LOCAL_CAPABILITY = HostCapability(
    can_read=True,
    can_write=True,
    can_run_local_commands=True,
)
_SAFE_TOKEN = re.compile(r'[a-z][a-z0-9_]{0,63}\Z')


def _absolute(path) -> Path:
    """Absolute without resolving symlinks; install proof remains fail-closed."""
    return Path(os.path.abspath(os.fspath(path)))


def _safe_token(value: str) -> str:
    """Never print untrusted filenames, Git output, or secret-like text."""
    return value if isinstance(value, str) and _SAFE_TOKEN.fullmatch(value) else 'unknown'


def _render(result: WorkflowResult, out, *, show_digest: bool = False) -> None:
    print(result.beginner.headline, file=out)
    for detail in result.beginner.details:
        print(f"- {detail}", file=out)
    if result.failure:
        print(f"failure_code: {_safe_token(result.failure)}", file=out)
    if show_digest and result.confirmation_required and result.digest:
        print(f"confirmation_digest: {result.digest}", file=out)


def _workflow(root: Path, destination: Path | None, confirm_digest: str | None,
              stage_callback=None) -> WorkflowResult:
    args = dict(capability=_LOCAL_CAPABILITY, confirm_digest=confirm_digest)
    if stage_callback is not None:
        args['stage_callback'] = stage_callback
    return run_update_workflow(root, destination, **args)


def _stage_output(out):
    def report(stage: str, status: str) -> None:
        # Engine emits only closed, product-owned stage and status tokens.
        print(f"stage: {_safe_token(stage)} = {_safe_token(status)}", file=out)
    return report


def run_interactive(root, destination=None, *, input_fn=input, out=None,
                    verbose: bool = False) -> int:
    """Preview once; confirm the current digest; apply and report truthfully."""
    out = sys.stdout if out is None else out
    root = _absolute(root)
    destination = _absolute(destination) if destination is not None else None
    report = _stage_output(out) if verbose else None

    result = _workflow(root, destination, None, report)
    if result.failure == 'destination_required':
        _render(result, out)
        selected = input_fn("New side-by-side folder: ").strip()
        if not selected:
            print("Nothing was changed.", file=out)
            return 2
        destination = _absolute(selected)
        result = _workflow(root, destination, None, report)

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
        result = _workflow(root, destination, result.digest, report)


def run_non_interactive(root, destination=None, *, confirm_digest: str | None = None,
                        out=None, verbose: bool = False) -> int:
    """Print preview or apply one exact digest; never silently confirm stale state."""
    out = sys.stdout if out is None else out
    root = _absolute(root)
    destination = _absolute(destination) if destination is not None else None
    report = _stage_output(out) if verbose else None
    result = _workflow(root, destination, confirm_digest, report)
    _render(result, out, show_digest=True)

    if confirm_digest is None:
        return 0 if (result.ready or result.confirmation_required) else 2
    if result.ready:
        return 0
    if result.failure == 'stale_state' and result.confirmation_required:
        return 3
    return 2


class _Tee:
    """Mirror safe CLI reporting only; a failed log cannot interrupt apply."""
    def __init__(self, primary, log):
        self.primary, self.log, self.failed = primary, log, False

    def write(self, content):
        self.primary.write(content)
        try:
            self.log.write(content)
        except OSError:
            self.failed = True

    def flush(self):
        self.primary.flush()
        try:
            self.log.flush()
        except OSError:
            self.failed = True


def _log_target(root: Path, target: Path) -> Path:
    """Reject logging within the installed tree (it would dirty the checkout)."""
    canonical_root = root.resolve()
    canonical_target = target.resolve(strict=False)
    if canonical_target == canonical_root or canonical_root in canonical_target.parents:
        raise ValueError('Diagnostic log must be outside the installation.')
    return canonical_target


def main(argv=None, *, default_root=None) -> int:
    parser = argparse.ArgumentParser(
        description="Preview and safely update a Personal-SoT installation."
    )
    parser.add_argument(
        "--root", type=Path,
        default=Path.cwd() if default_root is None else Path(default_root),
        help="Personal-SoT root (default: this installation).",
    )
    parser.add_argument(
        "--destination", type=Path,
        help="Destination for a no-Git side-by-side update.",
    )
    parser.add_argument(
        "--verbose", action="store_true",
        help="Show safe stage/status events and failure codes without private contents.",
    )
    parser.add_argument(
        "--log-file", type=Path,
        help="Create a new diagnostic log outside the installation (never overwrite).",
    )
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--preview", action="store_true",
                      help="Print one fresh preview/digest without prompting or updating.")
    mode.add_argument("--confirm-digest",
                      help="Apply only this exact previously-previewed digest.")
    args = parser.parse_args(argv)

    def run(out):
        verbose = args.verbose or args.log_file is not None
        if args.preview or args.confirm_digest is not None:
            return run_non_interactive(args.root, args.destination,
                                       confirm_digest=args.confirm_digest,
                                       out=out, verbose=verbose)
        return run_interactive(args.root, args.destination, out=out, verbose=verbose)

    if args.log_file is None:
        return run(sys.stdout)
    try:
        location = _log_target(_absolute(args.root), _absolute(args.log_file))
        log = location.open('x', encoding='utf-8')
    except (OSError, ValueError):
        print("Could not create diagnostic log outside the installation; "
              "update was not attempted.", file=sys.stderr)
        return 2

    # Never mistake a runtime/apply failure for a log creation failure.
    # In particular, no diagnostic I/O exception may suppress recovery.
    out = _Tee(sys.stdout, log)
    try:
        result = run(out)
        out.flush()
        return result
    finally:
        try:
            log.close()
        except OSError:
            out.failed = True
        if out.failed:
            print("Warning: diagnostic log could not be written completely.",
                  file=sys.stderr)


if __name__ == "__main__":
    raise SystemExit(main())
