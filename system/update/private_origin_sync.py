"""Explicit, fail-closed reconciliation of a local Git update with private origin/main.

This is NOT the canonical public update engine. It runs only after the
existing Safe Update workflow succeeded and the user separately confirms a
push to the configured GitHub origin. No remote URL is taken from prompts.
"""
from __future__ import annotations

from dataclasses import dataclass
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile
from urllib import error as urlerror, request as urlrequest

from system.update import git_update


_PRIVATE_HTTPS = re.compile(
    r"https://github[.]com/([A-Za-z0-9-]+)/([A-Za-z0-9_.-]+?)(?:[.]git)?\Z"
)
_ONE_LINE_SCOPE = re.compile(
    r"^([a-z][a-z0-9_]*(?:/[a-z][a-z0-9_]*)*) +→ +(workspace/context/[a-z0-9_/-]+/)\s*$"
)
_REGISTRY = Path("system/routing/context_registry.md")
_IDENTITY = (
    "-c", "user.name=Personal-SoT Private Sync",
    "-c", "user.email=private-sync@personal-sot.invalid",
    "-c", "user.useConfigOnly=true",
)


@dataclass(frozen=True)
class SyncResult:
    status: str  # synchronized | skipped | failed | local_only
    failure: str | None = None
    rollback_completed: bool | None = None


def _run(root: Path, hooks_dir: str, *args, timeout: int = 120):
    """Use the user's GitHub credentials, never trust hooks or inherited Git overrides.

    Local-only Git configuration may provide Git Credential Manager, which is
    needed for authenticated private HTTPS transport. Never log stdout/stderr:
    both are potentially private. No shell and no untrusted command strings.
    """
    env = {key: value for key, value in os.environ.items()
           if not key.upper().startswith("GIT_")}
    cmd = ["git", "-c", "core.hooksPath=" + hooks_dir,
           "-c", "core.fsmonitor=false",
           "-c", "protocol.ext.allow=never",
           "-c", "protocol.file.allow=never",
           "-c", "submodule.recurse=false"]
    if os.name == "nt":
        cmd += ["-c", "core.autocrlf=true"]
    cmd += list(args)
    try:
        return subprocess.run(cmd, cwd=str(root), env=env,
                              stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                              text=True, timeout=timeout, check=False)
    except (OSError, subprocess.SubprocessError):
        return None


def _ok(result) -> bool:
    return result is not None and result.returncode == 0


def _text(result) -> str:
    return result.stdout.strip() if _ok(result) else ""


def private_origin_url(root) -> str | None:
    """Accept only the fixed origin/main of a GitHub Personal-SoT Git clone.

    Never push to the public canonical repository, another branch or a
    non-GitHub transport. Caller still explicitly confirms private ownership.
    """
    root = Path(root)
    with tempfile.TemporaryDirectory(prefix="sot_sync_hooks_") as hooks:
        branch = _text(_run(root, hooks, "symbolic-ref", "--quiet", "--short", "HEAD"))
        raw = _text(_run(root, hooks, "config", "--get", "remote.origin.url"))
        expanded = _text(_run(root, hooks, "remote", "get-url", "origin"))
    if branch != "main" or not raw or expanded != raw:
        return None
    match = _PRIVATE_HTTPS.fullmatch(raw)
    if match is None:
        return None
    owner, name = match.groups()
    if owner.lower() == "mralishah" and name.lower() == "personal-sot":
        return None
    # Only a private-workspace-shaped repository is eligible for automatic
    # synchronization. This is a naming guard, not proof of GitHub privacy.
    if name.lower() not in ("mypersonal-sot", "private-personal-sot"):
        return None
    return raw


def _is_proven_private(url: str) -> bool:
    """Fail closed unless an anonymous GitHub API check returns 404.

    An authenticated fetch separately proves the repository exists. An
    anonymous 404 therefore distinguishes it from a public repository.
    No private tokens or Personal contents are sent to this endpoint.
    """
    match = _PRIVATE_HTTPS.fullmatch(url)
    if match is None:
        return False
    owner, repository = match.groups()
    req = urlrequest.Request(
        "https://api.github.com/repos/" + owner + "/" + repository,
        headers={"Accept": "application/vnd.github+json",
                 "User-Agent": "Personal-SoT-Safe-Update"},
    )
    try:
        with urlrequest.urlopen(req, timeout=12):
            return False  # Public/anonymous-readable: must never push.
    except urlerror.HTTPError as exc:
        return exc.code == 404
    except (OSError, ValueError):
        return False


def _normalize_registry(root: Path) -> bool:
    """Convert only unambiguous one-line mappings within registered_scopes.

    The original parser owns two-line entries. Never invent a scope, rewrite
    project contents, touch a symlink or alter mappings outside this section.
    """
    path = root / _REGISTRY
    if not path.is_file() or path.is_symlink():
        return False
    original = path.read_text(encoding="utf-8")
    lines = original.splitlines(keepends=True)
    in_section = False
    in_fence = False
    rewritten = []
    for line in lines:
        clean = line.strip()
        if clean.startswith("## "):
            in_section = clean == "## registered_scopes"
            in_fence = False
        elif in_section and clean.startswith("```"):
            in_fence = not in_fence
        match = _ONE_LINE_SCOPE.fullmatch(clean) if in_section and in_fence else None
        if match and (root / match.group(2).rstrip("/")).is_dir():
            suffix = "\r\n" if line.endswith("\r\n") else "\n"
            rewritten.append(match.group(1) + suffix)
            rewritten.append("→ " + match.group(2) + suffix)
        else:
            rewritten.append(line)
    changed = "".join(rewritten) != original
    if changed:
        path.write_text("".join(rewritten), encoding="utf-8", newline="")
    return changed


def _validate(root: Path, hooks: str) -> bool:
    """Validate the FINAL merged state, not only the public-only candidate."""
    checks = [
        [sys.executable, "-B", "system/validation/validate_v1.py", "--mode", "personal"],
        [sys.executable, "-B", "system/validation/validate_prompts.py"],
    ]
    for cmd in checks:
        try:
            outcome = subprocess.run(cmd, cwd=str(root), stdin=subprocess.DEVNULL,
                                     stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                     text=True, timeout=90, check=False)
        except (OSError, subprocess.SubprocessError):
            return False
        if outcome.returncode != 0:
            return False

    # Private governed system/runtime changes require complete unit tests.
    changed = _run(root, hooks, "diff", "--cached", "--name-only", "--", "system/")
    if not _ok(changed):
        return False
    if changed.stdout.strip():
        test_paths = sorted((root / "system/tests").rglob("test_*.py"))
        if not test_paths:
            return False
        modules = [".".join(path.relative_to(root).with_suffix("").parts)
                   for path in test_paths]
        try:
            outcome = subprocess.run(
                [sys.executable, "-B", "-m", "unittest", *modules],
                cwd=str(root), stdin=subprocess.DEVNULL,
                stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                text=True, timeout=240, check=False)
        except (OSError, subprocess.SubprocessError):
            return False
        if outcome.returncode != 0 or "Ran 0 tests" in outcome.stderr:
            return False
    return True


def synchronize(root: Path, url: str) -> SyncResult:
    """Fetch, merge, validate, commit and push; never force-push.

    The public update is already a clean local commit. If private merge
    validation fails, abort the pending merge; the earlier public update
    remains available locally. A push rejection preserves the validated
    local merge and reports that publication is incomplete.
    """
    root = Path(root)
    if private_origin_url(root) != url or git_update._preflight(str(root)) is not None:
        return SyncResult("failed", "unsafe_private_origin_or_dirty_checkout")
    with tempfile.TemporaryDirectory(prefix="sot_sync_hooks_") as hooks:
        fetch = _run(root, hooks, "fetch", "--no-tags", url,
                     "+refs/heads/main:refs/remotes/origin/main")
        if not _ok(fetch):
            return SyncResult("failed", "private_fetch_failed")
        if not _is_proven_private(url):
            return SyncResult("failed", "private_visibility_unverified")

        remote = _text(_run(root, hooks, "rev-parse", "--verify", "refs/remotes/origin/main"))
        local = _text(_run(root, hooks, "rev-parse", "--verify", "HEAD"))
        if not re.fullmatch(r"[0-9a-f]{40}", remote) or not re.fullmatch(r"[0-9a-f]{40}", local):
            return SyncResult("failed", "private_ref_unresolved")

        if _ok(_run(root, hooks, "merge-base", "--is-ancestor", remote, local)):
            # No remote-only changes. Still validate before publishing.
            if not _validate(root, hooks):
                return SyncResult("failed", "final_validation_failed")
        else:
            # Never run user-defined external merge drivers.
            configured_drivers = _run(
                root, hooks, "config", "--get-regexp", r"^merge[.].+[.]driver$")
            if configured_drivers is None or configured_drivers.returncode not in (0, 1):
                return SyncResult("failed", "merge_driver_check_failed")
            if configured_drivers.returncode == 0:
                return SyncResult("failed", "unsafe_merge_driver")

            merge = _run(root, hooks, "merge", "--no-commit", "--no-ff",
                         "refs/remotes/origin/main")
            if not _ok(merge):
                aborted = _ok(_run(root, hooks, "merge", "--abort"))
                return SyncResult("failed", "private_merge_conflict", aborted)

            try:
                normalized = _normalize_registry(root)
                if normalized and not _ok(_run(
                        root, hooks, "add", "--", str(_REGISTRY))):
                    raise ValueError("registry staging failed")
                if not _ok(_run(root, hooks, "diff", "--cached", "--check")):
                    raise ValueError("diff check failed")
                if not _validate(root, hooks):
                    raise ValueError("validation failed")
            except (OSError, UnicodeError, ValueError):
                aborted = _ok(_run(root, hooks, "merge", "--abort"))
                return SyncResult("failed", "final_validation_failed", aborted)

            commit = _run(root, hooks, *_IDENTITY, "commit",
                          "-m", "chore(sync): reconcile public update with private origin")
            if not _ok(commit):
                # A merge in progress can still be aborted safely.
                aborted = _ok(_run(root, hooks, "merge", "--abort"))
                return SyncResult("failed", "private_commit_failed", aborted)

        # A remote race is never resolved by force. GitHub may still reject
        # the non-fast-forward push after this check; report local-only then.
        latest = _run(root, hooks, "ls-remote", url, "refs/heads/main")
        if not _ok(latest) or not _text(latest).startswith(remote + "\t"):
            return SyncResult("local_only", "private_remote_changed")
        pushed = _run(root, hooks, "push", url, "HEAD:refs/heads/main")
        if not _ok(pushed):
            return SyncResult("local_only", "private_push_rejected")
        return SyncResult("synchronized")
