# update_contract

## purpose

Canonical, client-neutral contract for the Safe Update Git-clone and
ZIP/no-Git paths defined in `guides/developer/update/safe_update_design.md`.
Owns target-resolution semantics, failure classes, and, as later loops
extend this file, classification vocabulary, preview/confirmation/result
shape, and privacy rules shared by both paths.

This is a companion executable contract, not a duplicate of
`system/adapters/source_access_contract.md`. That contract governs resolving
and reading canonical *factual* context for ordinary conversational use.
This contract governs resolving one *update target* commit and, in later
loops, applying it. Both reuse the same `system/connectors/` transport and
failure vocabulary rather than each defining their own.

## target_resolution

The only canonical update authority is:

```text
repository: mrAlishah/Personal-SoT
ref:        main
```

`system/update/target.py`'s `resolve()` takes no repository, ref, commit,
fork, or PR argument. There is no configuration key, prompt field, or chat
directive that can substitute a different repository, branch, or commit as
update authority. A caller that needs a different source for testing injects
a `resolver` callable returning the same `Snapshot` shape
`system.connectors.source.Snapshot`/`GitHubSource.resolve()` use; `resolve()`
still independently checks that snapshot's repository and ref against the
fixed canonical values above before trusting it, rather than assuming an
injected or transport-returned snapshot is already correct.

`resolve()` returns one `TargetSnapshot(commit, ref, resolved_via)`: an
immutable pinned commit `T`, the resolved ref (always `main`), and which
resolution path produced it. Both the Git-clone and ZIP/no-Git paths call
this same function; neither path defines its own target-resolution logic.

## controlled_git

Every Git invocation this design issues, starting with target resolution,
runs through `system/update/target.py`'s `controlled_git`, not a bare
`subprocess.run` call to `git`. It builds the child process environment
explicitly (`PATH`, plus `HOME`/`XDG_CONFIG_HOME`/`GIT_CONFIG_NOSYSTEM`/
`GIT_CONFIG_GLOBAL` pointed at an isolated controlled location) rather than
passing the parent environment through, so ambient or injected
`GIT_CONFIG_*`/`GIT_DIR`/`GIT_WORK_TREE` state cannot redirect it. When no
explicit working directory is given, it also runs inside a freshly created,
empty, non-repository directory bounded by an explicit
`GIT_CEILING_DIRECTORIES`, so Git's upward repository discovery finds no
repository-local config there and cannot walk into an ancestor repository
the controlled directory happens to be created under either — neither
system/global isolation nor an empty directory alone covers that case. Its
own isolated global config also sets `http.followRedirects = false`, so a
single HTTP redirect on the initial request — which Git's own default,
`initial`, would otherwise follow as the base for the rest of the exchange —
cannot silently substitute a different repository as the effective
resolution target. The canonical URL is passed literally on the command
line, never through a configured remote name. Apply (a later loop) reuses
this same primitive, supplying its own working directory inside the real
checkout, and adds only what apply additionally needs there; it does not
define a second controlled-execution mechanism.

## failure_vocabulary

Target resolution reuses `system.connectors.source.Failure` for the
resolution-phase reasons it can actually produce:

```text
capability_unavailable
source_unresolved
source_unavailable
```

These carry the same meaning `source.py` already defines for them. Failures
specific to later stages this contract will own — a stale preview, a
both-changed conflict, a concurrent mutation, a failed candidate validation,
an unsafe migration path — are not resolution-phase reasons and are not
defined here; a later loop adds them as new, non-overlapping literals rather
than overloading these three.

## privacy

No content is read at the target-resolution stage; only a commit id and ref
name are resolved. `SourceUnavailable` values raised here carry only a
closed failure reason, never raw transport output, matching the existing
rule in `system/connectors/source.py`.

## dirty/untracked preflight

Before any Git-clone planning proceeds, `system/update/git_update.py`
inspects the installed clone's index/worktree/untracked state and fails
closed rather than risk executing user-configured code to determine it
accurately.

First it checks, using Git's own attribute-resolution plumbing
(`git check-attr`, never a hand-written `.gitattributes` parser) together
with the effective `filter.*`/`diff.*` configuration, whether any tracked
path would require an external clean/smudge/process/textconv helper for an
accurate dirty comparison. If so, the result is `unsafe_repository_state`;
the helper is never invoked to find this out. `git status`/`git diff` apply
this normalization to decide dirtiness, not only at `add`/`commit`, so
`--no-textconv`/`--no-ext-diff` do not close this by themselves.

Otherwise it runs `git --no-optional-locks -c core.fsmonitor=false status
--porcelain=v2 --untracked-files=all` through `controlled_git`.
`--no-optional-locks` is Git's own documented mechanism for preventing
`status` from refreshing the index as a side effect; `-c
core.fsmonitor=false` disables a configured fsmonitor hook/daemon for this
one invocation regardless of ambient configuration. Any reported change
blocks with `dirty_or_untracked`.

Every live-repo read that resolves a commit's tree — this preflight's
`status` call and the current-commit (`HEAD`) resolution below — also
disables replace-object interpretation (`GIT_NO_REPLACE_OBJECTS=1`). A
replace ref on the live repository's own `HEAD` can otherwise make `status`
compare the worktree against a substituted tree instead of the real one,
misreporting dirty state as clean or clean state as dirty.

## target materialization

`target.resolve()` returns a commit id for `T`, not its Git objects; a
stale local clone will not already have them. `git_update.py` materializes
`T` into a fresh, updater-owned, ephemeral **bare** repository — never the
live checkout, never persisted past one `classify()` call — strictly in
this order:

1. `git init --bare` the ephemeral repository.
2. `controlled_git('fetch', target.CANONICAL_URL, 'refs/heads/main:refs/heads/_target',
   cwd=ephemeral)` — the exact ref `refs/heads/main`, the literal canonical
   URL, never a configured remote name; no `git remote add` is ever run.
   At this point the ephemeral repository has no alternate object
   directory, so it has nothing of the installed clone's to advertise, and
   Git's fetch negotiation cannot include any installed-clone object id in
   what it tells the canonical remote it already "has".
3. `git rev-parse refs/heads/_target` in the ephemeral repository; if this
   does not equal the already-resolved `T`, canonical `main` moved between
   resolution and fetch. The result is `stale_target`; classification never
   silently proceeds against the newly observed commit.
4. Only now, with target-fetch network activity finished, classification
   attaches the installed clone's own object database
   (`<git-dir>/objects`, resolved via `git rev-parse --git-dir` rather than
   assumed to be `.git`) to the ephemeral repository read-only, through
   `controlled_git`'s allowlist-checked `extra_env`
   (`GIT_ALTERNATE_OBJECT_DIRECTORIES`). No further network operation
   happens after this point. Alternates share objects without touching the
   live repository's refs, index, worktree, or its own object database.

## classification

Classification runs in the ephemeral repository with the alternate
attached and `GIT_NO_REPLACE_OBJECTS=1`, so a replace ref cannot alter
which history is judged as accepted lineage. `.git/info/grafts` needs no
separate control: it is read only from the repository actually being
operated on, and an alternate shares only the object database, never
`.git/info/`.

`B = git merge-base --all C T`. Zero results is unrelated lineage; more
than one is ambiguous lineage (a criss-cross history) — both fail closed,
never an arbitrarily chosen candidate. `no_op` is true when `C == T` or
`B == T` (target has nothing new to offer); V1 never downgrades.

Per-path state uses raw tree/blob identity only — `git ls-tree -r` at `B`,
`C`, and `T`, comparing `(mode, blob sha)` per path, absence represented as
a legitimate value — never `git diff` or any command that would invoke a
configured external diff/textconv/clean/smudge/fsmonitor helper:

```text
C == T                → already_aligned
C == B and T != B     → upstream_only
T == B and C != B     → user_only
otherwise             → conflict
```

This covers creation, deletion, and modification uniformly, including
"target deletes/renames a locally modified path" (a `conflict`, since `T`'s
absence differs from both `B` and `C`) without a separate rule.

## preview and privacy

`preview(plan)` binds `C`, `T`, `B`, and the complete classified plan into
a `sha256` digest over a canonically ordered serialization (fixed field
order, sorted path lists), so digest equality does not depend on
dict/set iteration order.

The beginner-facing summary's naming boundary is classification state, not
location: `already_aligned`, `upstream_only`, and `conflict` paths all have
an established relationship to accepted target history — `T` changed,
converged on, or (for a delete/rename conflict) explicitly removed them —
and may be named. A `user_only` path is, by that same classification,
never present in `T`; it is reported by area/count only, wherever it sits,
including outside `workspace/`. Advanced authorization is not decided
here; see Loop 5.

## scope

This file currently owns target resolution, the shared `controlled_git`
primitive, the dirty/untracked preflight, target materialization, Git-clone
classification, and preview/digest binding. Apply/recovery result
semantics and side-by-side scope-carry-over rules belong to later loops of
`guides/developer/update/safe_update_implementation_plan.md` and extend
this file when implemented; they are not established here.
