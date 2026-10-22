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
# Exact GitHub SSH forms. Do not accept host aliases, custom ports, URL
# rewrites, alternate usernames or paths with additional shell arguments.
_PRIVATE_SSH_SCP = re.compile(
    r"git@github[.]com:([A-Za-z0-9-]+)/([A-Za-z0-9_.-]+?)(?:[.]git)?\Z"
)
_PRIVATE_SSH_URL = re.compile(
    r"ssh://git@github[.]com/([A-Za-z0-9-]+)/([A-Za-z0-9_.-]+?)(?:[.]git)?\Z"
)


def _github_repo_identity(url: str) -> tuple[str, str] | None:
    """Return only a literal, eligible private-workspace GitHub identity.

    Eligibility applies to both origin selection and visibility checks:
    an arbitrary/private GitHub repo must never become an approved target.
    """
    for pattern in (_PRIVATE_HTTPS, _PRIVATE_SSH_SCP, _PRIVATE_SSH_URL):
        match = pattern.fullmatch(url)
        if match is not None:
            owner, name = match.groups()
            if owner.lower() == "mralishah" and name.lower() == "personal-sot":
                return None
            if name.lower() not in ("mypersonal-sot", "private-personal-sot"):
                return None
            return owner, name
    return None


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
           "-c", "http.followRedirects=false",
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
    """Accept only literal GitHub HTTPS/SSH origin/main for a private clone.

    Never push to the public canonical repository, another branch or a
    non-GitHub transport. Caller still explicitly confirms private ownership.
    """
    root = Path(root)
    with tempfile.TemporaryDirectory(prefix="sot_sync_hooks_") as hooks:
        branch = _text(_run(root, hooks, "symbolic-ref", "--quiet", "--short", "HEAD"))
        raw = _text(_run(root, hooks, "config", "--get", "remote.origin.url"))
        expanded = _text(_run(root, hooks, "remote", "get-url", "origin"))
        push_expanded = _text(_run(root, hooks, "remote", "get-url", "--push", "origin"))
    # Separate push URL rewriting/pushInsteadOf may otherwise send Personal
    # data somewhere other than the origin that was reviewed.
    if branch != "main" or not raw or expanded != raw or push_expanded != raw:
        return None
    identity = _github_repo_identity(raw)
    if identity is None:
        return None
    # Naming is already checked by the shared identity parser. This is
    # not proof of privacy: synchronize() still requires authenticated
    # fetch and the anonymous GitHub API visibility test before push.
    return raw


def _is_proven_private(url: str) -> bool:
    """Fail closed for HTTPS and SSH unless anonymous GitHub API returns 404.

    An authenticated fetch separately proves the repository exists. An
    anonymous 404 therefore distinguishes it from a public repository.
    No private tokens or Personal contents are sent to this endpoint.
    """
    identity = _github_repo_identity(url)
    if identity is None:
        return False
    owner, repository = identity
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


def _unsafe_external_attributes(root: Path, hooks: str) -> bool:
    """Check Git's own attribute resolution before a private merge.

    Global Git Credential Manager and LFS configuration may exist without
    being selected by any affected file. Reject only a configured executable
    filter/diff driver selected by effective local or incoming attributes.
    Fail closed if any plumbing read cannot be completed.
    """
    configured = _run(
        root, hooks, "config", "--get-regexp",
        r"^(filter[.].+[.](clean|smudge|process)|diff[.].+[.](textconv|command))$")
    if configured is None or configured.returncode not in (0, 1):
        return True
    if configured.returncode == 1:
        return False

    filter_names, diff_names = set(), set()
    for item in configured.stdout.splitlines():
        key = item.split(" ", 1)[0]
        matched = re.fullmatch(
            r"(filter|diff)[.](.+)[.](clean|smudge|process|textconv|command)", key)
        if matched is None:
            return True
        (filter_names if matched.group(1) == "filter" else diff_names).add(
            matched.group(2))

    changed = _run(root, hooks, "diff", "--no-ext-diff", "--no-textconv",
                   "--name-only", "-z", "HEAD", "refs/remotes/origin/main")
    if not _ok(changed):
        return True
    paths = [p for p in changed.stdout.split("\0") if p]
    if not paths:
        return False
    for revision in ("HEAD", "refs/remotes/origin/main"):
        resolved = _run(root, hooks, "check-attr", "--source=" + revision,
                        "--all", "-z", "--", *paths)
        if not _ok(resolved):
            return True
        fields = resolved.stdout.split("\0")
        if fields and fields[-1] == "":
            fields.pop()
        if len(fields) % 3 != 0:
            return True
        for i in range(0, len(fields), 3):
            _path, attribute, value = fields[i:i+3]
            if attribute == "filter" and value in filter_names:
                return True
            if attribute == "diff" and value in diff_names:
                return True
    return False


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
            # A globally configured helper is harmless when no affected
            # path selects it; use Git's own attribute resolution instead.
            if _unsafe_external_attributes(root, hooks):
                return SyncResult("failed", "unsafe_filter_driver")

            merge = _run(root, hooks, "merge", "--no-commit", "--no-ff",
                         "refs/remotes/origin/main")
            if not _ok(merge):
                aborted = _ok(_run(root, hooks, "merge", "--abort"))
                return SyncResult("failed", "private_merge_conflict", aborted)

            try:
                if not _ok(_run(root, hooks, "diff", "--cached", "--check")):
                    raise ValueError("diff check failed")
                verified_tree = _text(_run(root, hooks, "write-tree"))
                if not re.fullmatch(r"[0-9a-f]{40}", verified_tree):
                    raise ValueError("unable to snapshot merged tree")
                if not _validate(root, hooks):
                    raise ValueError("validation failed")
                # Do not commit an index that changed during the validators,
                # or accept newly untracked files created while testing.
                if _text(_run(root, hooks, "write-tree")) != verified_tree:
                    raise ValueError("index changed during validation")
                if not _ok(_run(root, hooks, "diff", "--exit-code")):
                    raise ValueError("unstaged changes after validation")
                untracked = _run(root, hooks, "ls-files", "--others",
                                 "--exclude-standard")
                if not _ok(untracked) or untracked.stdout.strip():
                    raise ValueError("untracked changes after validation")
            except (OSError, UnicodeError, ValueError):
                aborted = _ok(_run(root, hooks, "merge", "--abort"))
                return SyncResult("failed", "final_validation_failed", aborted)

            commit = _run(root, hooks, *_IDENTITY, "commit",
                          "-m", "chore(sync): reconcile public update with private origin")
            if not _ok(commit):
                # A merge in progress can still be aborted safely.
                aborted = _ok(_run(root, hooks, "merge", "--abort"))
                return SyncResult("failed", "private_commit_failed", aborted)

        # The ref and checkout must still agree before any private upload.
        if git_update._preflight(str(root)) is not None:
            return SyncResult("local_only", "post_commit_checkout_changed")

        # A remote race is never resolved by force. GitHub may still reject
        # the non-fast-forward push after this check; report local-only then.
        latest = _run(root, hooks, "ls-remote", url, "refs/heads/main")
        if not _ok(latest) or not _text(latest).startswith(remote + "\t"):
            return SyncResult("local_only", "private_remote_changed")
        pushed = _run(root, hooks, "push", url, "HEAD:refs/heads/main")
        if not _ok(pushed):
            return SyncResult("local_only", "private_push_rejected")
        return SyncResult("synchronized")
