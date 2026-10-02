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

Both paths consume one explicitly resolved immutable target commit `T`. One thin
target-resolution step, shared by both paths, resolves the current accepted state
from exactly `mrAlishah/Personal-SoT:main` and pins it to `T`. It reuses the
existing exact-repository ref-to-commit resolution in
`system/connectors/github.py` where that host capability exists, or reads the
same exact repository ref directly with Git; it adds no resolver of its own. A
host that cannot resolve and fetch the canonical target fails closed as
capability unavailable. A local default or arbitrary remote, PR branch, fork, user-supplied
archive, chat-supplied commit, or cached conclusion is not update authority. The
update core never discovers repositories or trusts chat memory. No package
manager, installer framework, release catalog, cache, file inventory, or
migration engine is introduced.

The side-by-side path never mutates the original installation. Its new
distribution tree is materialized from `T` and supplies product files; only
regular files under the canonical user-owned `workspace/` surface, plus the
scope registrations those preserved context scopes need, may be preserved from
the current installation. Different overlapping workspace files are conflicts.
This conservatism is the safe consequence of having no baseline, not a reason to
add a parallel inventory.

## Ownership

- `system/update/update_contract.md` owns target resolution, update
  classification, preview, confirmation, recovery, and result semantics for both
  paths.
- `system/update/git_update.py` owns Git state inspection, planning, and
  recoverable apply orchestration.
- `system/update/side_by_side.py` owns archive/no-Git comparison and copying into
  a separate destination, including scope-registration carry-over.
- Existing validators remain the only owners of repository, Prompt, and public
  distribution validation. `system/routing/context_registry.md` remains the only
  scope registry, and its existing validator parser remains the only parser.
- `system/assistant/update_workflow.md` is a thin beginner-facing workflow; it
  does not copy update logic.
- `guides/user/update.md` explains the supported user paths, including how to
  save local changes before a Git update.

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
before planning. Lineage is then decided as follows:

- `C == T`, or `T` is already an ancestor of `C`, or the candidate tree has no
  effective change: explicit already-current/no-op result. V1 never downgrades.
- `C` is an ancestor of `T`, or `C` and `T` have diverged with a valid `B` that
  is part of accepted public history (for example, the user's local commits plus
  newer upstream commits): normal classification above. This is the ordinary
  update case.
- No merge base, unrelated product lineage, or history that cannot be reconciled
  with accepted public history: fail closed. V1 does not rewrite history.

V1 intentionally treats every different both-changed path as a conflict even if
Git could text-merge it. Silent semantic merging is outside the safety boundary.

### Unstable input

Assistant writes are ordinary file changes; no product workflow commits them.
An onboarded clone is therefore normally dirty or has untracked Personal files,
and the clean-input rule still blocks preview and apply. The blocked result must
be actionable:

- the user's own changes must first be saved in local Git history;
- those commits are private local state and must never be pushed to the public
  `mrAlishah/Personal-SoT` repository;
- the updater does not commit, stash, reset, or rewrite them itself.

The beginner result reports this by area and count only. `guides/user/update.md`
owns the step-by-step user instructions.

The preview binds `C`, `T`, `B`, and the classified plan into a digest. Apply
re-resolves all three and stops on any stale state.

## Git apply and recovery

Apply requires real local Git/write/command capability, a clean checkout, no
classified conflict, and explicit confirmation of the preview digest.

```text
build the candidate tree from C + immutable T outside the live checkout
→ validate_v1 --mode personal on the candidate tree
→ validate_prompts on the candidate tree
→ advance the installed state only if every validator passes
```

The candidate is validated with the candidate's own validators against the
candidate tree. The live index, worktree, and current ref are not changed before
every validator passes.

Safe Update does not run `validate_public` on an installed Personal candidate.
Within Safe Update, `validate_public` only checks a pristine public distribution
and must never cause Personal files to be removed, redacted, or changed. This
scopes Safe Update validation only; it does not change how other owners use
that validator.

Every updater-controlled Git invocation runs with a controlled configuration: no
user Git hooks (including reference-transaction hooks), merge or diff drivers,
clean/smudge or process filters, fsmonitor commands, or URL rewriting from
repository, user, or global configuration. The canonical repository is
addressed directly, not through a configured remote. If an updater-touched path
would require an external filter, apply fails closed before mutation.

The updater verifies the clean tracked/index state again immediately before
mutation, makes the index and worktree match the validated candidate, and
advances the current ref last with an expected-old-state check. The verified
pre-update commit, index, worktree hashes, and candidate state define the
recovery boundary.

If an updater-controlled step fails and no external change is detected, the
running updater restores that exact verified pre-update state. Before recovery
changes a path or ref, it verifies that the value still matches the
updater-written state. A concurrent or external mutation stops automatic
recovery for that affected state; the updater does not reset over it and reports
recovery as incomplete with actionable guidance. Results distinguish mutation
started, validation ran, validation passed, rollback attempted, rollback
completed, concurrent change, and a non-sensitive failure class. A failed update
is never reported as ready.

Recovery exists only while the updater is running. If the process is
interrupted or killed, no automatic rollback is claimed. Because the ref
advances last, an interruption before that step leaves the ref at `C`; the next
check reports the unstable state and actionable guidance rather than guessing or
resetting.

The resulting merge commit records the installed baseline and target provenance;
no separate installed-version metadata is required for Git clones.

## Side-by-side preservation

For ZIP/no-Git installations:

- the original tree is read-only input and remains the recovery copy;
- the destination must be new and empty;
- the pristine public distribution is materialized only from the resolved
  commit `T`, never from a user-supplied or branch-named archive, and is checked
  with `validate_public` before any Personal files enter it;
- product files under `system/`, `guides/`, and the repository root come only
  from that validated distribution; current modifications to shipped product
  files are not copied;
- current-only regular files under `workspace/` may be preserved in the new tree;
- identical `workspace/` overlaps need no action;
- different `workspace/` overlaps are conflicts and are not silently chosen;
- current-only files under `system/`, `guides/`, or the repository root are
  product-area customizations and require manual resolution rather than copying;
- symlinks, special files, path traversal, and any path escaping a selected root
  are rejected;
- after migration, `validate_v1 --mode personal` and `validate_prompts` validate
  the candidate Personal installation.

Without a baseline, a current-only `workspace/` file may be user-created or a
shipped file that `T` deleted or renamed. The preview lists such files as kept
from the current installation, not as known user-created files, and the user may
exclude them.

### Scope registrations

`workspace/` is the normal preservation surface. The one Personal-written state
outside it is the scope mappings that setup and project workflows add to
`system/routing/context_registry.md`. The target distribution's registry remains
the product owner: the current registry file is not copied, and no other current
`system/` change is carried over. The host instead:

1. reads current mappings with the existing canonical registry parser;
2. keeps only mappings whose target is a `workspace/context/` scope directory
   preserved in the new tree;
3. adds the kept mappings to the target registry's registered scopes in the
   canonical entry shape;
4. treats a duplicate scope, a scope mapped to different targets, or one target
   claimed by different scopes, across current and target mappings, as a
   conflict.

Dropped mappings are reported as excluded. The resulting registry is then
checked by `validate_v1 --mode personal`, including missing and unregistered
scopes.

Comparison and copying of Personal files and registry mappings are host-side
opaque operations. Update does not require restricted or denied content to
enter AI context, and preserving a file does not grant the AI authorization to
read its contents.

The side-by-side preview binds `T`, the pristine distribution tree, and the
exact classified plan: preserved, conflicting, excluded, and rejected paths plus
carried scope mappings. Before copying, the host re-resolves `T` and reclassifies
the current installation. A changed target or classified state stops and
requires a new preview.

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
must not expose denied content, Personal facts, credentials, or secret values.
Personal path and file names can reveal facts: beginner output reports Personal
files by area and count, and Advanced details show a Personal path only when the
existing access contract allows it.

## Acceptance

Executable evidence must cover canonical-main target pinning for both paths,
rejection of non-canonical targets and archives, invalid lineage, already-current,
ahead, and divergent states, upstream-only changes, user-only files, unchanged and
modified shipped workspace files, both-changed conflicts, upstream delete/rename
conflicts, dirty state with actionable non-leaking guidance, stale preview for
both paths, confirmation mismatch, candidate validation before live mutation,
controlled Git configuration, Personal validation, complete and incomplete
recovery under concurrent change, interrupted-process reporting, honest no-write
behavior, opaque workspace-only side-by-side preservation, scope-registration
carry-over and conflicts, reporting of kept current-only workspace files,
unsafe-file rejection, pristine distribution validation, and the original
installation remaining untouched.
