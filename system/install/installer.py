#!/usr/bin/env python3
"""Cross-platform Personal-SoT installer/update launcher.

Run through install.sh (Linux/macOS) or install.bat (Windows). The installer
contains no provider credentials and never treats prompt text as capability.
"""
from __future__ import annotations

import argparse
from dataclasses import dataclass
from pathlib import Path
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import urllib.error
import urllib.request
import uuid

if not __package__:
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from system.update import git_update, side_by_side, target


PUBLIC_REPOSITORY = "mrAlishah/Personal-SoT"
PUBLIC_REF = "main"
PUBLIC_URL = "https://github.com/" + PUBLIC_REPOSITORY + ".git"
ENTRYPOINT = "workspace/adapters/runtime_entrypoint.md"
REQUIRED_MARKERS = (
    ENTRYPOINT,
    "system/diagnostics/doctor.py",
    "system/update/target.py",
)
DRIVE_FOLDER_RE = re.compile(
    r"^https://drive\.google\.com/drive/(?:u/\d+/)?folders/([^/?#]+)(?:[/?#].*)?$",
    re.I,
)


class InstallError(RuntimeError):
    pass


@dataclass(frozen=True)
class CommandResult:
    returncode: int
    stdout: str = ""
    stderr: str = ""


def _run(args, *, cwd=None, input_text=None, timeout=120, env=None) -> CommandResult:
    try:
        result = subprocess.run(
            list(args),
            cwd=str(cwd) if cwd is not None else None,
            input=input_text,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=timeout,
            check=False,
            env=env,
        )
    except FileNotFoundError as exc:
        raise InstallError(f"Required command is not installed: {args[0]}") from exc
    except subprocess.TimeoutExpired as exc:
        raise InstallError(f"Command timed out: {args[0]}") from exc
    return CommandResult(result.returncode, result.stdout or "", result.stderr or "")


def _git(root: Path, *args, timeout=120) -> CommandResult:
    # Keep provider credentials available while disabling repository/user hooks
    # and replace-object interpretation for installer-owned Git operations.
    with tempfile.TemporaryDirectory(prefix="personal_sot_install_hooks_") as hooks:
        env = os.environ.copy()
        for key in tuple(env):
            if key in {
                "GIT_DIR",
                "GIT_WORK_TREE",
                "GIT_INDEX_FILE",
                "GIT_OBJECT_DIRECTORY",
                "GIT_ALTERNATE_OBJECT_DIRECTORIES",
                "GIT_COMMON_DIR",
                "GIT_CEILING_DIRECTORIES",
            } or key.startswith("GIT_CONFIG_"):
                env.pop(key, None)
        env["GIT_NO_REPLACE_OBJECTS"] = "1"
        return _run(
            (
                "git",
                "-c",
                f"core.hooksPath={hooks}",
                "-c",
                "core.fsmonitor=false",
            ) + tuple(args),
            cwd=root,
            timeout=timeout,
            env=env,
        )


def _check_python() -> None:
    if sys.version_info < (3, 10):
        raise InstallError("Python 3.10 or newer is required.")


def _require_markers(root: Path) -> None:
    if not all((root / marker).is_file() for marker in REQUIRED_MARKERS):
        raise InstallError("This folder is not a valid Personal-SoT installation.")


def _is_git_root(root: Path) -> bool:
    result = _git(root, "rev-parse", "--show-toplevel")
    if result.returncode != 0:
        return False
    try:
        return Path(result.stdout.strip()).resolve() == root.resolve()
    except OSError:
        return False


def _remote_url(root: Path, name: str, *, push: bool = False) -> str | None:
    key = f"remote.{name}.{'pushurl' if push else 'url'}"
    result = _git(root, "config", "--local", "--get", key)
    return result.stdout.strip() if result.returncode == 0 and result.stdout.strip() else None


def _reject_git_url_rewrites(root: Path) -> None:
    result = _git(
        root,
        "config",
        "--get-regexp",
        r"^url\..*\.(insteadof|pushinsteadof)$",
    )
    if result.returncode == 0 and result.stdout.strip():
        raise InstallError(
            "Git URL rewrite rules are configured. Disable url.*.insteadOf/pushInsteadOf "
            "for the installer so the private destination cannot be redirected."
        )
    if result.returncode not in (0, 1):
        raise InstallError("Could not verify Git URL rewrite safety.")


def _github_slug(value: str) -> str | None:
    value = value.strip()
    patterns = (
        r"https://github\.com/([A-Za-z0-9_.-]+)/([A-Za-z0-9_.-]+?)(?:\.git)?/?$",
        r"git@github\.com:([A-Za-z0-9_.-]+)/([A-Za-z0-9_.-]+?)(?:\.git)?$",
        r"ssh://git@github\.com/([A-Za-z0-9_.-]+)/([A-Za-z0-9_.-]+?)(?:\.git)?/?$",
    )
    for pattern in patterns:
        match = re.fullmatch(pattern, value)
        if match:
            return f"{match.group(1)}/{match.group(2)}"
    return None


def _is_public_remote(value: str | None) -> bool:
    slug = _github_slug(value or "")
    return slug is not None and slug.casefold() == PUBLIC_REPOSITORY.casefold()


def _drive_folder_id(value: str) -> str | None:
    match = DRIVE_FOLDER_RE.fullmatch(value.strip())
    return match.group(1) if match else None


def _confirm(message: str, *, assume_yes: bool) -> None:
    if assume_yes:
        return
    answer = input(f"{message} [y/N]: ").strip().casefold()
    if answer not in {"y", "yes"}:
        raise InstallError("Cancelled. Nothing was changed.")


def _public_validator(root: Path) -> None:
    script = root / "system" / "validation" / "validate_public.py"
    result = _run((sys.executable, "-B", str(script), "--root", str(root)), cwd=root)
    if result.stdout:
        print(result.stdout.rstrip())
    if result.returncode != 0:
        raise InstallError("Public source validation failed; installation was not started.")


def _doctor(root: Path) -> None:
    script = root / "system" / "diagnostics" / "doctor.py"
    result = _run(
        (
            sys.executable,
            "-B",
            str(script),
            "--root",
            str(root),
            "--write-capability",
            "available",
        ),
        cwd=root,
    )
    if result.stdout:
        print(result.stdout.rstrip())
    if result.returncode != 0:
        raise InstallError("Doctor found a blocking problem. Run @do:fix after opening this installation.")


def _sync_fresh_public_clone(root: Path) -> str:
    _require_markers(root)
    if not _is_git_root(root):
        raise InstallError("Initial one-click install must be run from a Git clone of sot public.")

    branch = _git(root, "branch", "--show-current")
    if branch.returncode != 0 or branch.stdout.strip() != PUBLIC_REF:
        raise InstallError(f"Initial install must start from sot public branch {PUBLIC_REF!r}.")

    origin = _remote_url(root, "origin")
    if not _is_public_remote(origin):
        raise InstallError("origin is not sot public (mrAlishah/Personal-SoT).")
    if _remote_url(root, "upstream") is not None:
        raise InstallError("An upstream remote already exists; this does not look like a fresh public clone.")

    plan = git_update.classify(root)
    if plan.blocked is not None:
        raise InstallError(
            f"The public clone is not safe/current for installation: {plan.blocked}. "
            "Use a fresh clone and retry."
        )
    if plan.conflict or plan.user_only or plan.upstream_only or plan.current != plan.target:
        raise InstallError(
            "This clone is not exactly current sot public/main. "
            "Use a fresh clone, then run the installer again."
        )
    if not re.fullmatch(r"[0-9a-f]{40}", plan.current):
        raise InstallError("Could not prove the current canonical public commit.")

    _public_validator(root)
    return plan.current

def _anonymous_github_visibility(slug: str) -> str:
    request = urllib.request.Request(
        "https://api.github.com/repos/" + slug,
        headers={"User-Agent": "Personal-SoT-installer"},
    )
    try:
        with urllib.request.urlopen(request, timeout=20) as response:
            if response.status != 200:
                return "unknown"
            payload = json.loads(response.read().decode("utf-8"))
            return "private" if payload.get("private") is True else "public"
    except urllib.error.HTTPError as exc:
        if exc.code == 404:
            return "private_or_hidden"
        return "unknown"
    except (OSError, ValueError, UnicodeError):
        return "unknown"


def _prove_existing_private_github_origin(root: Path, url: str) -> str:
    _reject_git_url_rewrites(root)
    slug = _github_slug(url)
    if slug is None or slug.casefold() == PUBLIC_REPOSITORY.casefold():
        raise InstallError("Private origin is not a valid non-public GitHub repository.")

    access = _git(root, "ls-remote", url, timeout=60)
    if access.returncode != 0:
        raise InstallError("Private origin is not reachable with your current Git credentials.")

    visibility = "unknown"
    if shutil.which("gh"):
        check = _run(("gh", "api", f"repos/{slug}", "--jq", ".private"), timeout=30)
        if check.returncode == 0:
            visibility = "private" if check.stdout.strip().casefold() == "true" else "public"
    if visibility == "unknown":
        visibility = _anonymous_github_visibility(slug)

    if visibility == "public":
        raise InstallError("origin is public. Refusing to push private Personal-SoT state.")
    if visibility not in {"private", "private_or_hidden"}:
        raise InstallError("Private origin visibility could not be proven.")

    dry_run = _git(root, "push", "--dry-run", url, "HEAD:refs/heads/main", timeout=60)
    if dry_run.returncode != 0:
        raise InstallError("Write access to the private origin could not be verified.")
    return slug


def _verify_private_github_destination(root: Path, url: str) -> str:
    _reject_git_url_rewrites(root)
    slug = _github_slug(url)
    if slug is None:
        raise InstallError("Use an exact GitHub repository URL (HTTPS or SSH).")
    if slug.casefold() == PUBLIC_REPOSITORY.casefold():
        raise InstallError("The private destination cannot be sot public.")

    access = _git(root, "ls-remote", url, timeout=60)
    if access.returncode != 0:
        raise InstallError("The GitHub destination is not reachable with your current Git credentials.")
    if access.stdout.strip():
        raise InstallError("For first install, the private GitHub repository must be empty.")

    visibility = "unknown"
    if shutil.which("gh"):
        check = _run(("gh", "api", f"repos/{slug}", "--jq", ".private"), timeout=30)
        if check.returncode == 0:
            visibility = "private" if check.stdout.strip().casefold() == "true" else "public"
    if visibility == "unknown":
        visibility = _anonymous_github_visibility(slug)

    if visibility == "public":
        raise InstallError("The destination repository is public. Use a private GitHub repository.")
    if visibility not in {"private", "private_or_hidden"}:
        raise InstallError("Repository privacy could not be proven. Install/authenticate GitHub CLI and retry.")

    dry_run = _git(root, "push", "--dry-run", url, "HEAD:refs/heads/main", timeout=60)
    if dry_run.returncode != 0:
        raise InstallError("Write access to the private GitHub repository could not be verified.")
    return slug


def _rollback_remote_conversion(root: Path) -> None:
    if _remote_url(root, "origin") is not None and _remote_url(root, "upstream") is not None:
        _git(root, "remote", "remove", "origin")
    if _remote_url(root, "upstream") is not None:
        _git(root, "config", "--unset-all", "remote.upstream.pushurl")
        _git(root, "config", "--unset-all", "remote.pushDefault")
        _git(root, "remote", "rename", "upstream", "origin")


def _install_github(root: Path, destination: str, *, assume_yes: bool) -> None:
    head = _sync_fresh_public_clone(root)
    slug = _verify_private_github_destination(root, destination)

    print("\nInstall preview")
    print(f"  source:      sot public @ {head[:12]}")
    print(f"  destination: private GitHub repository {slug}")
    print("  topology:    upstream=sot public, origin=private")
    print("  test:        Doctor after transfer")
    _confirm("Create the private sot with this plan?", assume_yes=assume_yes)

    fresh_head = _sync_fresh_public_clone(root)
    if fresh_head != head:
        raise InstallError("sot public changed after preview. Run the installer again.")
    fresh_slug = _verify_private_github_destination(root, destination)
    if fresh_slug != slug:
        raise InstallError("Private destination changed after preview. Run the installer again.")

    renamed = _git(root, "remote", "rename", "origin", "upstream")
    if renamed.returncode != 0:
        raise InstallError("Could not rename public origin to upstream.")
    try:
        protected = _git(root, "config", "remote.upstream.pushurl", destination)
        if protected.returncode != 0:
            raise InstallError("Could not redirect upstream pushes to the private destination.")
        added = _git(root, "remote", "add", "origin", destination)
        if added.returncode != 0:
            raise InstallError("Could not add the private origin.")
        defaulted = _git(root, "config", "remote.pushDefault", "origin")
        if defaulted.returncode != 0:
            raise InstallError("Could not make private origin the default push target.")
        pushed = _git(root, "push", "-u", "origin", f"{PUBLIC_REF}:{PUBLIC_REF}", timeout=180)
        if pushed.returncode != 0:
            raise InstallError("Initial push to the private repository failed.")
    except InstallError:
        _rollback_remote_conversion(root)
        raise

    if not _is_public_remote(_remote_url(root, "upstream")):
        raise InstallError("Post-install verification failed: upstream is not sot public.")
    if _github_slug(_remote_url(root, "origin") or "") != slug:
        raise InstallError("Post-install verification failed: origin is not the private destination.")
    if _github_slug(_remote_url(root, "upstream", push=True) or "") != slug:
        raise InstallError("Post-install verification failed: upstream push guard is not private.")

    _doctor(root)
    _print_ready(root, provider="github")


def _git_private_topology(root: Path) -> bool:
    """Recognize an installed private Git clone without requiring local-only
    remotes to survive a re-clone on another machine.

    A private clone always needs a GitHub-shaped non-public `origin`.
    `upstream` is optional because Git remotes are local configuration and
    are not transferred when the private repository is cloned elsewhere.
    When present, upstream must still be the canonical public repository.
    Actual origin privacy/write access is re-proven inside `_update_git`.
    """
    if not _is_git_root(root):
        return False
    origin = _remote_url(root, "origin")
    upstream = _remote_url(root, "upstream")
    return (
        origin is not None
        and _github_slug(origin) is not None
        and not _is_public_remote(origin)
        and (upstream is None or _is_public_remote(upstream))
    )


def _update_git(root: Path, *, assume_yes: bool) -> None:
    _require_markers(root)
    if not _git_private_topology(root):
        raise InstallError("This Git installation does not have a recognizable private GitHub origin/public update topology.")

    origin = _remote_url(root, "origin")
    if origin is None:
        raise InstallError("Private origin is missing.")
    _prove_existing_private_github_origin(root, origin)

    plan = git_update.classify(root)
    preview = git_update.preview(plan)
    if plan.blocked is not None:
        raise InstallError(f"Safe Update is blocked: {plan.blocked}. Run @do:fix for guidance.")
    if plan.conflict:
        raise InstallError(
            f"Safe Update found {len(plan.conflict)} conflict(s). Run @do:fix before updating."
        )

    if plan.no_op:
        print("✓ Private sot is already current with sot public.")
        _doctor(root)
        _print_ready(root, provider="github")
        return

    print("\nUpdate preview")
    print(f"  upstream changes: {len(plan.upstream_only)}")
    print(f"  preserved private changes: {len(plan.user_only)}")
    print(f"  conflicts: {len(plan.conflict)}")
    _confirm("Apply this Safe Update?", assume_yes=assume_yes)

    result = git_update.apply(root, plan, preview.digest)
    if result.failure is not None or not result.commit:
        raise InstallError(f"Safe Update did not complete: {result.failure or 'unknown failure'}.")

    _doctor(root)

    current_origin = _remote_url(root, "origin")
    if current_origin != origin:
        raise InstallError("Private origin changed during update; nothing was pushed.")
    _prove_existing_private_github_origin(root, origin)
    pushed = _git(root, "push", origin, f"HEAD:{PUBLIC_REF}", timeout=180)
    if pushed.returncode != 0:
        raise InstallError(
            "Local Safe Update passed, but the private GitHub origin was not updated. "
            "No force-push was attempted."
        )

    print(f"✓ Safe Update applied: {result.commit[:12]}")
    _print_ready(root, provider="github")


def _next_side_by_side_destination(current: Path) -> Path:
    base = current.with_name(current.name + "-updated")
    if not base.exists():
        return base
    for number in range(2, 1000):
        candidate = current.with_name(f"{current.name}-updated-{number}")
        if not candidate.exists():
            return candidate
    raise InstallError("Could not choose an unused side-by-side update folder.")


def _initial_drive_install(
    public_root: Path,
    drive_url: str,
    destination: Path,
    *,
    assume_yes: bool,
) -> None:
    folder_id = _drive_folder_id(drive_url)
    if folder_id is None:
        raise InstallError("Use a Google Drive folder URL such as https://drive.google.com/drive/folders/<id>.")

    _sync_fresh_public_clone(public_root)
    destination_input = destination.expanduser()
    if destination_input.is_symlink():
        raise InstallError("The Drive local destination itself may not be a symlink.")
    destination = destination_input.resolve()

    if destination.exists() and any(destination.iterdir()):
        if all((destination / marker).is_file() for marker in REQUIRED_MARKERS) and not (destination / ".git").exists():
            print("Existing no-Git Personal-SoT found in the Drive-synced folder; switching to Safe Update.")
            _update_no_git(destination, assume_yes=assume_yes)
            return
        raise InstallError("The Drive-synced destination must be empty or an existing no-Git Personal-SoT.")

    resolved = target.resolve()
    parent = destination.parent
    print("\nInstall preview")
    print(f"  source:      sot public @ {resolved.commit[:12]}")
    print(f"  Drive link:  folder id ...{folder_id[-8:]}")
    print(f"  local path:  {destination}")
    print("  mode:        validated no-Git installation")
    print("  privacy:     verify in Google Drive that this folder is not public/shared-to-anyone")
    print("  test:        public validation + Doctor")
    _confirm("Create the private sot in this Drive-synced folder?", assume_yes=assume_yes)

    fresh = target.resolve()
    if fresh.commit != resolved.commit:
        raise InstallError("sot public changed after preview. Run the installer again.")
    if destination.exists() and any(destination.iterdir()):
        raise InstallError("Drive destination changed after preview. Run the installer again.")

    parent.mkdir(parents=True, exist_ok=True)
    stage = parent / f".personal-sot-install-{uuid.uuid4().hex}"
    stage.mkdir()
    try:
        if not side_by_side.build_pristine(stage, resolved.commit):
            raise InstallError("Could not materialize the canonical public distribution.")
        if not side_by_side.validate_pristine(stage):
            raise InstallError("The staged public distribution failed validation.")
        _doctor(stage)

        if destination.exists():
            destination.rmdir()
        os.replace(stage, destination)
    finally:
        if stage.exists():
            shutil.rmtree(stage, ignore_errors=True)

    _print_ready(destination, provider="google_drive")


def _update_no_git(current: Path, *, assume_yes: bool) -> None:
    _require_markers(current)
    if (current / ".git").exists():
        raise InstallError("This is a Git installation; use the Git Safe Update path.")

    destination = _next_side_by_side_destination(current)
    preview = side_by_side.preview(current, destination)
    plan = preview.plan

    if plan.blocked is not None:
        raise InstallError(f"Safe Update is blocked: {plan.blocked}. Run @do:fix for guidance.")
    if plan.conflicts or plan.registry.conflicts:
        raise InstallError(
            f"Safe Update found {len(plan.conflicts) + len(plan.registry.conflicts)} conflict(s). "
            "Run @do:fix before updating."
        )
    if plan.rejected_unsafe or plan.manual_resolution:
        raise InstallError(
            "Safe Update found content that needs manual review. Run @do:fix before updating."
        )

    print("\nUpdate preview")
    print(f"  current:      {current}")
    print(f"  new copy:     {destination}")
    print(f"  preserved:    {len(plan.kept)}")
    print(f"  conflicts:    {len(plan.conflicts) + len(plan.registry.conflicts)}")
    print("  original:     remains unchanged")
    _confirm("Build this side-by-side Safe Update?", assume_yes=assume_yes)

    result = side_by_side.migrate(current, destination, plan, preview.digest)
    if not result.ready:
        raise InstallError(f"Side-by-side Safe Update did not complete: {result.failure or 'unknown failure'}.")

    _doctor(destination)
    print(f"✓ Updated copy is ready: {destination}")
    print(f"✓ Original copy was not changed: {current}")
    _print_ready(destination, provider="google_drive")


def _print_ready(root: Path, *, provider: str) -> None:
    print("\n✓ Personal-SoT is ready")
    print(f"  provider: {provider}")
    print(f"  open:     {root}")
    print("\nIn your AI client, open/connect this private sot and run:")
    print("\n@do:sot")
    print("\nthen:")
    print("\n@do:setup")


def _choose_target() -> str:
    print("\nWhere should your private sot live?")
    print("  1. GitHub private repository")
    print("  2. Google Drive synced/mounted folder")
    choice = input("> ").strip()
    if choice == "1":
        return "github"
    if choice == "2":
        return "drive"
    raise InstallError("Choose 1 or 2.")


def _parse_args(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--target", choices=("github", "drive"))
    parser.add_argument("--destination", help="Private GitHub URL or Google Drive folder URL.")
    parser.add_argument(
        "--drive-path",
        type=Path,
        help="Local synchronized/mounted path corresponding to the Google Drive folder.",
    )
    parser.add_argument("--update", action="store_true", help="Update an existing private installation.")
    parser.add_argument("--yes", action="store_true", help="Accept the displayed installer/update preview.")
    return parser.parse_args(argv)


def main(argv=None) -> int:
    args = _parse_args(argv)
    root = Path(__file__).resolve().parents[2]
    try:
        _check_python()
        _require_markers(root)

        if not (root / ".git").exists():
            _update_no_git(root, assume_yes=args.yes)
            return 0

        if _git_private_topology(root):
            _update_git(root, assume_yes=args.yes)
            return 0

        if args.update:
            raise InstallError("This looks like a fresh sot public clone, not an installed private sot.")

        selected = args.target or _choose_target()
        if selected == "github":
            destination = args.destination or input("Private GitHub repository URL: ").strip()
            _install_github(root, destination, assume_yes=args.yes)
        else:
            drive_url = args.destination or input("Google Drive folder URL: ").strip()
            drive_path = args.drive_path
            if drive_path is None:
                drive_path = Path(input("Local synced/mounted path for that Drive folder: ").strip())
            _initial_drive_install(root, drive_url, drive_path, assume_yes=args.yes)
        return 0
    except (InstallError, OSError) as exc:
        print(f"\n✗ {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
