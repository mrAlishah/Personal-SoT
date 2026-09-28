# Safe Update design

## Status

Approved for Public Personal-SoT V1.

## Goal

Update an installed public Personal-SoT without silently overwriting or deleting
Personal context, projects, custom prompts, custom Profiles, or user-owned
configuration.

```text
resolve current and target state
→ classify upstream and user changes
→ preview exact effects and conflicts
→ confirm the bound preview
→ apply recoverably
→ run canonical validators
→ report the truthful final state
```

## Current gap

The repository supports archive download and Git clone but has no version owner,
update workflow, updater, or installed-state inventory. Git history already
provides a deterministic baseline for clones. Archive installations have no
trusted baseline and therefore cannot safely infer whether an overlapping
workspace file is unchanged or user-modified.

No private source repository or Personal deployment is a runtime dependency.
The only upstream product identity is the public `mrAlishah/Personal-SoT`
repository.

## Architecture

V1 uses two deliberately small paths:

```text
Git clone   → Git-aware in-place update
ZIP/no-Git → conservative side-by-side migration
```

The Git core consumes an explicitly resolved immutable target commit. A thin
source step may fetch that target only from the exact public product repository;
the core never discovers repositories or trusts chat memory. No package manager,
installer framework, release catalog, cache, file inventory, or migration engine
is introduced.

The side-by-side path never mutates the original installation. Its new
distribution tree supplies product files; current-only user files may be copied;
different overlapping workspace files are conflicts. This conservatism is the
safe consequence of having no baseline, not a reason to add a parallel inventory.

## Ownership

- `system/update/update_contract.md` owns update classification, preview,
  confirmation, recovery, and result semantics.
- `system/update/git_update.py` owns Git state inspection, planning, and
  recoverable apply orchestration.
- `system/update/side_by_side.py` owns archive/no-Git comparison and copying into
  a separate destination.
- Existing validators remain the only owners of repository, Prompt, and public
  distribution validation.
- `system/assistant/update_workflow.md` is a thin beginner-facing workflow; it
  does not copy update logic.
- `guides/user/update.md` explains the supported user paths.

Public development branch governance is not installed-instance update policy.

## Git state model

For current commit `C`, target commit `T`, and `B = merge-base(C, T)`, each path
is classified from Git tree identity:

| State | Meaning | V1 action |
| --- | --- | --- |
| local equals baseline; target changed | upstream-only | update |
| target equals baseline; local changed or created | user-only | preserve |
| shipped workspace file unchanged locally | upstream-only | update |
| local and target both changed | conflict | require user decision; do not apply |
| target deletes/renames a locally modified path | conflict | preserve and report |
| clean, identical change on both sides | already aligned | no change |
| dirty index/worktree or untracked path | unstable input | block before preview/apply |

V1 intentionally treats every different both-changed path as a conflict even if
Git could text-merge it. Silent semantic merging is outside the safety boundary.

The preview binds `C`, `T`, `B`, and the classified plan into a digest. Apply
re-resolves all three and stops on any stale state.

## Git apply and recovery

Apply requires real local Git/write/command capability, a clean checkout, no
classified conflict, and explicit confirmation of the preview digest.

```text
git merge --no-commit --no-ff <immutable target>
→ validate_v1 --mode core
→ validate_prompts
→ validate_public
→ commit only if every validator passes
```

If merge preparation, validation, or commit fails, the updater aborts the merge
and restores the exact clean pre-update state. It reports whether mutation began,
validation ran, validation passed, rollback ran, and which non-sensitive failure
class occurred. A failed update is never reported as ready.

The resulting merge commit records the installed baseline and target provenance;
no separate installed-version metadata is required for Git clones.

## Side-by-side preservation

For ZIP/no-Git installations:

- the original tree is read-only input and remains the recovery copy;
- the destination must be new and empty;
- product files come from the new public distribution;
- current-only files are preserved in the new tree;
- identical overlaps need no action;
- different overlaps are reported as conflicts and are not silently chosen;
- validation runs only when the destination is complete enough to be usable.

If real usage later shows excessive false conflicts, a release-owned hash
manifest may be proposed with evidence. It is not part of V1.

## Capability and beginner UX

Local write-capable agents may check, preview, confirm, apply, and validate. Web
or no-write clients may check and preview, then provide apply guidance; they must
state that no update was applied and no local validation ran.

Default output uses user concepts:

```text
Update available
→ Your personal data is preserved
→ safe product changes
→ customized files needing a decision
→ preview
→ confirm
→ validation
→ ready or actionable failure
```

Git commits, SHAs, merge bases, and paths belong in Advanced details. Diagnostics
must not expose denied content, Personal facts, or secret values.

## Acceptance

Executable evidence must cover upstream-only changes, user-only files, unchanged
and modified shipped workspace files, both-changed conflicts, upstream
delete/rename conflicts, dirty state, stale preview, confirmation mismatch,
successful validated apply, validation rollback, honest no-write behavior, and
side-by-side preservation with the original untouched.
