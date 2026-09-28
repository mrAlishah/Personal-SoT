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
source step resolves the current accepted state from exactly
`mrAlishah/Personal-SoT:main`, then pins that state to commit `T`. A local
default or arbitrary remote, PR branch, fork, chat-supplied commit, or cached
conclusion is not update authority. The core never discovers repositories or
trusts chat memory. No package manager, installer framework, release catalog,
cache, file inventory, or migration engine is introduced.

The side-by-side path never mutates the original installation. Its new
distribution tree supplies product files; only regular files under the canonical
user-owned `workspace/` surface may be preserved from the current installation.
Different overlapping workspace files are conflicts. This conservatism is the
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

The exact canonical public repository and its `main` ref must resolve to `T`
before planning. A missing or invalid merge base, unrelated product lineage, or
installation state that cannot be reconciled with accepted public history fails
closed. V1 does not automatically downgrade or rewrite history when an installed
copy is ahead of or divergent from `T`. If `C == T` or the candidate tree has no
effective change, the plan reports an explicit already-current/no-op result.

V1 intentionally treats every different both-changed path as a conflict even if
Git could text-merge it. Silent semantic merging is outside the safety boundary.

The preview binds `C`, `T`, `B`, and the classified plan into a digest. Apply
re-resolves all three and stops on any stale state.

## Git apply and recovery

Apply requires real local Git/write/command capability, a clean checkout, no
classified conflict, and explicit confirmation of the preview digest.

```text
build candidate from C + immutable T without user hooks
→ validate_v1 --mode personal
→ validate_prompts
→ advance the installed state only if every validator passes
```

`validate_public` is not run on an installed Personal tree. It remains the owner
of pristine public-distribution checks and must never cause Personal files to be
removed, redacted, or changed.

The updater-controlled merge and commit path must not execute user Git hooks or
arbitrary external merge commands. It uses non-hooking Git primitives, verifies
the clean tracked/index state again immediately before mutation, and advances the
current ref with an expected-old-state check. The verified pre-update commit,
index, worktree hashes, and candidate state define the recovery boundary.

If an updater-controlled step fails and no external change is detected, recovery
restores that exact verified pre-update state. Before recovery changes a path or
ref, it verifies that the value still matches the updater-written state. A
concurrent or external mutation stops automatic recovery for that affected state;
the updater does not reset over it and reports recovery as incomplete with
actionable guidance. Results distinguish mutation started, validation ran,
validation passed, rollback attempted, rollback completed, concurrent change,
and a non-sensitive failure class. A failed update is never reported as ready.

The resulting merge commit records the installed baseline and target provenance;
no separate installed-version metadata is required for Git clones.

## Side-by-side preservation

For ZIP/no-Git installations:

- the original tree is read-only input and remains the recovery copy;
- the destination must be new and empty;
- the new pristine public distribution is checked with `validate_public` before
  any Personal files enter it;
- product files under `system/`, `guides/`, and the repository root come only
  from that validated distribution;
- current-only regular files under `workspace/` may be preserved in the new tree;
- identical `workspace/` overlaps need no action;
- different `workspace/` overlaps are conflicts and are not silently chosen;
- current-only files under `system/`, `guides/`, or the repository root are
  product-area customizations and require manual resolution rather than copying;
- symlinks, special files, path traversal, and any path escaping a selected root
  are rejected;
- after migration, `validate_v1 --mode personal` and `validate_prompts` validate
  the candidate Personal installation.

Comparison and copying of Personal files are host-side opaque operations. Update
does not require restricted or denied content to enter AI context, and preserving
a file does not grant the AI authorization to read its contents.

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

Executable evidence must cover canonical-main target pinning, invalid lineage,
already-current and ahead/divergent states, upstream-only changes, user-only
files, unchanged and modified shipped workspace files, both-changed conflicts,
upstream delete/rename conflicts, dirty state, stale preview, confirmation
mismatch, non-hooking apply, Personal validation, complete and incomplete
recovery under concurrent change, honest no-write behavior, opaque workspace-only
side-by-side preservation, unsafe-file rejection, pristine distribution
validation, and the original installation remaining untouched.
