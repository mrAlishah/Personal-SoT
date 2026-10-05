#!/usr/bin/env python3
"""Small cross-platform bootstrap installer for Personal-SoT."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import re
import shutil
import subprocess
import sys
import urllib.error
import urllib.request


PUBLIC_REPO = "mrAlishah/Personal-SoT"
PUBLIC_URL = "https://github.com/mrAlishah/Personal-SoT.git"
ROOT = Path(__file__).resolve().parents[2]
GITHUB_RE = re.compile(
    r"^(?:https://github\.com/|git@github\.com:)"
    r"([A-Za-z0-9_.-]+)/([A-Za-z0-9_.-]+?)(?:\.git)?/?$"
)


class InstallError(RuntimeError):
    pass


def run(args: list[str], *, cwd: Path = ROOT) -> subprocess.CompletedProcess[str]:
    try:
        return subprocess.run(
            args,
            cwd=cwd,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )
    except FileNotFoundError as exc:
        raise InstallError(f"Required command is not installed: {args[0]}") from exc


def github_slug(url: str) -> str | None:
    match = GITHUB_RE.fullmatch(url.strip())
    if not match:
        return None
    return f"{match.group(1)}/{match.group(2)}"


def remote_url(name: str) -> str | None:
    result = run(["git", "remote", "get-url", name])
    if result.returncode != 0:
        return None
    return result.stdout.strip() or None


def check_public_clone() -> None:
    required = (
        ROOT / "readme.md",
        ROOT / "workspace/adapters/runtime_entrypoint.md",
        ROOT / "system/diagnostics/doctor.py",
    )
    if not all(path.is_file() for path in required):
        raise InstallError("Run the installer from the Personal-SoT repository root.")

    git_root = run(["git", "rev-parse", "--show-toplevel"])
    if git_root.returncode != 0 or Path(git_root.stdout.strip()).resolve() != ROOT.resolve():
        raise InstallError("Initial installation must run from a Git clone of sot public.")

    branch = run(["git", "branch", "--show-current"])
    if branch.returncode != 0 or branch.stdout.strip() != "main":
        raise InstallError("Initial installation must run from branch main.")

    status = run(["git", "status", "--porcelain"])
    if status.returncode != 0 or status.stdout.strip():
        raise InstallError("The public clone has local changes. Use a clean clone.")

    slug = github_slug(remote_url("origin") or "")
    if slug is None or slug.casefold() != PUBLIC_REPO.casefold():
        raise InstallError("origin must point to sot public: mrAlishah/Personal-SoT.")


def run_checks(root: Path) -> None:
    commands = (
        [
            sys.executable,
            "-B",
            str(root / "system/validation/validate_public.py"),
            "--root",
            str(root),
        ],
        [
            sys.executable,
            "-B",
            str(root / "system/validation/validate_v1.py"),
            "--mode",
            "core",
            "--root",
            str(root),
        ],
        [sys.executable, "-B", str(root / "system/validation/validate_prompts.py")],
        [
            sys.executable,
            "-B",
            str(root / "system/diagnostics/doctor.py"),
            "--root",
            str(root),
            "--write-capability",
            "available",
        ],
    )
    for command in commands:
        result = run(command, cwd=root)
        if result.stdout:
            print(result.stdout.rstrip())
        if result.returncode != 0:
            if result.stderr:
                print(result.stderr.rstrip(), file=sys.stderr)
            raise InstallError(f"Check failed: {' '.join(command[2:4])}")


def prove_private_github(url: str) -> str:
    slug = github_slug(url)
    if slug is None:
        raise InstallError("Use an HTTPS or SSH GitHub repository URL.")
    if slug.casefold() == PUBLIC_REPO.casefold():
        raise InstallError("The private destination cannot be sot public.")

    access = run(["git", "ls-remote", url])
    if access.returncode != 0:
        raise InstallError("Cannot access the destination with your current Git credentials.")
    if access.stdout.strip():
        raise InstallError("The destination GitHub repository must be empty.")

    request = urllib.request.Request(
        f"https://api.github.com/repos/{slug}",
        headers={"User-Agent": "Personal-SoT-installer"},
    )
    try:
        with urllib.request.urlopen(request, timeout=10) as response:
            data = json.loads(response.read().decode("utf-8"))
            if data.get("private") is not True:
                raise InstallError("The destination GitHub repository is public.")
    except urllib.error.HTTPError as exc:
        if exc.code != 404:
            raise InstallError("Could not verify GitHub repository privacy.") from exc
        # ls-remote succeeded but anonymous GitHub lookup returned 404:
        # this is the expected shape for an accessible private repository.
    except (OSError, ValueError, UnicodeError) as exc:
        raise InstallError("Could not verify GitHub repository privacy.") from exc

    return slug


def install_github(url: str) -> Path:
    slug = prove_private_github(url)
    print(f"Installing private sot into GitHub repository: {slug}")

    if run(["git", "remote", "rename", "origin", "upstream"]).returncode != 0:
        raise InstallError("Could not rename public origin to upstream.")

    try:
        if run(["git", "remote", "add", "origin", url]).returncode != 0:
            raise InstallError("Could not add private origin.")
        run(["git", "config", "remote.pushDefault", "origin"])
        pushed = run(["git", "push", "-u", "origin", "main"])
        if pushed.returncode != 0:
            raise InstallError("Initial push to the private repository failed.")
    except InstallError:
        run(["git", "remote", "remove", "origin"])
        run(["git", "remote", "rename", "upstream", "origin"])
        raise

    run_checks(ROOT)
    return ROOT


def copy_to_drive(destination: Path) -> Path:
    destination = destination.expanduser().resolve()
    source = ROOT.resolve()

    if destination == source or source in destination.parents:
        raise InstallError("Google Drive destination must be outside the public clone.")

    if destination.exists() and not destination.is_dir():
        raise InstallError("Google Drive destination must be a folder.")
    if destination.exists() and any(destination.iterdir()):
        raise InstallError("Google Drive destination folder must be empty.")

    destination.mkdir(parents=True, exist_ok=True)
    ignore = shutil.ignore_patterns(
        ".git",
        ".worktrees",
        "__pycache__",
        "settings.local.json",
    )
    shutil.copytree(source, destination, dirs_exist_ok=True, ignore=ignore)
    run_checks(destination)
    return destination


def choose_mode() -> str:
    print("Where should your private sot live?")
    print("  1. GitHub private repository")
    print("  2. Google Drive synced folder")
    choice = input("> ").strip()
    if choice == "1":
        return "github"
    if choice == "2":
        return "drive"
    raise InstallError("Choose 1 or 2.")


def print_ready(root: Path) -> None:
    print("\n✓ Personal-SoT installation is ready")
    print(f"Open this private sot in your AI client:\n{root}")
    print("\nFirst run:")
    print("@do:sot")
    print("\nThen run:")
    print("@do:setup")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--github", help="Empty private GitHub repository URL.")
    parser.add_argument("--drive", type=Path, help="Empty local Google Drive synced folder.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        check_public_clone()
        run_checks(ROOT)

        if args.github and args.drive:
            raise InstallError("Choose only one destination.")
        if args.github:
            destination = install_github(args.github)
        elif args.drive:
            destination = copy_to_drive(args.drive)
        else:
            mode = choose_mode()
            if mode == "github":
                destination = install_github(input("Private GitHub repository URL: ").strip())
            else:
                print("Use a local folder already synced by Google Drive Desktop or equivalent.")
                destination = copy_to_drive(Path(input("Google Drive local folder path: ").strip()))

        print_ready(destination)
        return 0
    except (InstallError, OSError) as exc:
        print(f"\n✗ {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
