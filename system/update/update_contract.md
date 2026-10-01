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
`--no-textconv`/`--no-ext-diff` do not close this by themselves. A driver
subsection name is not assumed to be dot-free (`[filter "foo.bar"]`
flattens to the config key `filter.foo.bar.clean`); the driver identity is
recovered as everything between the fixed `filter.`/`diff.` namespace and
the final known suffix, matched against the config key alone, never
against a raw "key value" line where the value could contain unrelated
dot-suffix-like text.

This attribute/config safety inspection is itself a live-repo read that can
run repository-configured code before the hardened `status` call below is
ever reached: both its `git ls-files -z` (listing tracked paths to check)
and its `git check-attr --all -z` (resolving each path's attributes) can
invoke a configured `core.fsmonitor` hook exactly as `git status` can, so
both run with `--no-optional-locks -c core.fsmonitor=false` as well —
disabling fsmonitor only on the later `status` call is not sufficient.
`git config --get-regexp`, used only to read `filter.*`/`diff.*` values,
does not read the index/worktree and does not need this.

Otherwise it runs `git --no-optional-locks -c core.fsmonitor=false status
--porcelain=v2 -z --untracked-files=all` through `controlled_git`.
`--no-optional-locks` is Git's own documented mechanism for preventing
`status` from refreshing the index as a side effect; `-c
core.fsmonitor=false` disables a configured fsmonitor hook/daemon for this
one invocation regardless of ambient configuration; `-z` is required so a
path containing spaces or other characters is never quoted/escaped in a
way a bounded record parser would need to unpick. Any reported change
blocks with `dirty_or_untracked`, and the blocked result carries only a
fixed, safe `(area, count)` breakdown — the same closed area vocabulary
`workspace`/`system`/`guides`/`root`/`other` the beginner summary uses
below — never a raw path; a rename/copy record's second (origPath) item is
counted once, not as a separate path.

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
never an arbitrarily chosen candidate. `no_op` is true exactly when no path
classifies as `upstream_only` or `conflict` — not only `C == T`/`B == T`,
but also independently diverged commits that converge on the same tree,
and a candidate `T` with no effective tree change relative to `B` even
though `T != B` as a commit; a real upstream-driven change or any
unresolved conflict must still leave `no_op` false. V1 never downgrades.

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

`preview(plan)` binds `C`, `T`, `B`, the complete classified plan, and any
`blocked_by_area` breakdown into a `sha256` digest over a canonically
ordered serialization (fixed field order, sorted path lists, sorted
`(area, count)` pairs), so digest equality does not depend on dict/set
iteration order.

The beginner-facing summary's naming boundary is classification state, not
location: `already_aligned`, `upstream_only`, and `conflict` paths all have
an established relationship to accepted target history — `T` changed,
converged on, or (for a delete/rename conflict) explicitly removed them —
and may be named. A `user_only` path is, by that same classification,
never present in `T`; it is reported by area/count only, wherever it sits,
including outside `workspace/`. An area label — for a `user_only` path or
for a dirty/untracked blocked result alike — is drawn only from the closed
vocabulary `workspace`/`system`/`guides`/`root`/`other`; it is never the
path's own filename or directory name, so a user-controlled path component
can never reach the summary or the digest through its label. Advanced
authorization is not decided here; see Loop 5.

## apply and recovery

`apply(root, plan, digest)` never trusts the caller's `plan`: it
re-resolves `T` and re-classifies before doing anything, and aborts before
any mutation on a digest mismatch, a `blocked` state, or a remaining
`conflict` — a confirmed preview is a claim about a past state, not an
authorization to act on whatever the live state has become by the time
`apply` runs. A `no_op` classification returns a truthful already-current
result without mutating anything or creating a commit.

The candidate tree (target's entry for `already_aligned`/`upstream_only`
paths, current's entry for `user_only` paths, per the state table above)
is built as a real Git tree object and materialized into a directory
outside the live checkout; only that directory, never the live worktree,
is validated. Validation runs `validate_v1 --mode personal` and
`validate_prompts` as separate subprocesses rooted at the *candidate's
own* copies of those files, never the live checkout's already-imported
modules, so a target that itself changes validator logic is validated
against its own rules rather than a stale cached version; `validate_public`
is never invoked on an installed Personal candidate. Building the
candidate, validating it, transferring missing objects into the live
object database, and constructing the (as yet unreachable) resulting
commit object never touch the live ref/index/worktree, so they happen
before the FINAL recheck rather than after it — that recheck (clean
tracked/index state, `HEAD` still at `C`, and target-introduced attribute
safety re-evaluated against the live repository's *current*
`.git/info/attributes` and driver config, not the one read before
validation) is the last thing before the first live write, closing the
window validation's own real work would otherwise leave open. The live
ref, index, and worktree are not touched until this FINAL recheck passes.

Only `upstream_only` paths are ever written to the live worktree/index;
`already_aligned`/`user_only` paths are left completely untouched. Every
apply-side Git invocation, including object transfer, runs through the
same `controlled_git`, which now always passes both `-c
core.hooksPath=<empty-dir>` and `-c core.fsmonitor=false` — not only on
the read-only preflight's `status`/`ls-files`/`check-attr`, but on every
live-repo command apply issues, including `update-index` and
`write-tree`, both of which can otherwise invoke a configured
`core.fsmonitor` exactly as `status` can. For any updater-touched path,
`git check-attr --source=<candidate-tree>` proves the target-introduced
attributes would not select a configured filter/diff helper before
mutation proceeds — run in the *live* repository itself (with the
candidate's and target's objects made visible read-only through
`GIT_ALTERNATE_OBJECT_DIRECTORIES`), never inside the ephemeral
materialization repository, so Git's own attribute precedence still
applies the live repository's own `.git/info/attributes`; checking only
inside the ephemeral repository would miss it entirely. Missing objects
are copied into the live object database with `rev-list --objects` +
`pack-objects` + `index-pack` — a pure content transfer with no
remote/URL argument, so no repository-local `url.*.insteadOf` rewrite has
anything to redirect.

Before the candidate tree is built, its flattened path/entry set is
checked for a structural collision: Loop 2 classifies each path
independently, so a user-only file at some path and an upstream-only
descendant below that same path (or the reverse) can each classify with
no per-path `conflict` while still being jointly impossible — no Git
tree can hold a path as a blob and as a directory of descendants at
once. Detecting this is a sorted adjacent-pair check (a colliding pair
always sorts next to each other), not a general filesystem resolver or
a rename heuristic; a collision fails closed with `candidate_path_conflict`
before any candidate tree, validation, or live mutation.

Worktree/index mutation for a touched path resolves content by the
blob's exact object identity (`git cat-file -p <sha>`, never a worktree
re-hash) and stages it with `update-index --add --cacheinfo
<mode>,<sha>,<path>` (or `--force-remove` for a deletion) — never plain
`update-index --add`, which re-hashes the worktree file through Git's
normal content-based path and could invoke a configured clean filter. A
Git symlink mode (`120000`) is materialized as a real symlink, never
collapsed to a regular file. A real filesystem error (a permission-denied
directory, a colliding path segment, etc.) raised while writing a touched
path is caught there and reported as a bounded failure, never left to
escape `apply` as an uncaught exception; `mutation_started` becomes true
only once a live worktree/index write has actually been attempted for
some path, not merely because the per-path loop was entered, so a
touched path whose failure occurs during its own read-only content
resolution (before any write) correctly reports `mutation_started=False`
with nothing to roll back.

Touched paths are written in dependency-safe order, not arbitrary or
lexical order: every deletion before every creation/modification,
deletions deepest-path-first and creations shallowest-path-first — so a
legal Git directory↔file transition (one touched path vacating a name by
being deleted, another touched path claiming that same name as a file,
or the reverse) applies without a spurious `IsADirectoryError`. Clearing
a name for reuse removes a plain file/symlink with `unlink()` or an
empty directory with `rmdir()` — which itself fails closed if that
directory is unexpectedly non-empty — never a recursive `rmtree`, and
never anything not itself one of the touched paths. Immediately before
each individual touched path is written, a per-path check compares its
current live worktree AND index identity against the verified
pre-update state recorded for it; a single recheck at the top of `apply`
cannot see a *later* path change while an *earlier* path is still being
written, so this is checked again for every path, right before that
path's own turn. A mismatch here stops further writing, and that path's
external change is never overwritten, exactly like the existing
recovery-time concurrency check. Live mutation order otherwise: write/
remove every touched path this way, verify the resulting index matches
the candidate tree exactly (`git write-tree`).

Immediately before the ref CAS — the last thing before it — a FINAL
post-mutation integrity gate re-verifies the complete live installation
against the validated candidate: configured drivers and attribute safety
are re-read first (so this gate itself can never need to execute a
configured helper), then every touched path's current worktree AND
index identity is compared against what the updater wrote, and a
`git status --porcelain=v2 -z --no-renames --untracked-files=all`
confirms every reported changed path is one of the updater's own
touched paths — no untouched tracked path and no new untracked path.
`--no-renames` is required here specifically: Git's own rename/copy
detection can otherwise present "delete an untouched path, create a
touched path with identical content" as a single porcelain-v2 type-2
record whose reported current path is the touched one, silently hiding
the untouched path's deletion from a parser (correct for Loop 2's
coarse dirty area/count semantics, which this does not change) that
reports only the current path. Being a command-level flag, this is
deterministic regardless of the repository's own
`status.renames`/`diff.renames` configuration. This closes the window a
concurrent external event in that exact spot would otherwise leave
open: such an event need not raise an exception to be dangerous, and an
exception is not the only thing this gate must catch. The gate never
resets, cleans, or deletes an external path it finds; failing it aborts
before the ref advances and routes into the same recovery behavior as
any other post-mutation failure — and `rollback_completed` is always
false for this specific kind of failure, since the gate catching
something outside the touched-path bookkeeping is precisely what the
narrower recovery attempt has no way to see for itself.

Only once that gate passes does the ref advance, last, `git update-ref
HEAD <new> <old=C>`, a compare-and-swap that fails closed if `C` moved
concurrently — ref drift itself is this CAS's own atomic job, not the
integrity gate's, so there is no separate read-then-act gap for the ref
specifically. A CAS failure never reports `rollback_completed=True`,
regardless of how much updater-owned worktree/index state the ensuing
recovery attempt can still safely restore: once another process has
moved the ref, the updater never overwrites it back to `C`, so the ref
component of the verified pre-update boundary can never be completed by
this updater, and `rollback_completed` means the *complete* boundary,
not merely "the touched files were restored." The resulting commit's
two parents are exactly `C` and `T`, and its tree is exactly the
validated candidate tree.

Recovery exists only while `apply` is running, covers every touched path
(including one never actually reached before a sibling path's mutation
failed, for which "restore" is a safe no-op), and is owned by `apply`
itself rather than lost inside a helper that might raise partway through
mutating several paths. Restoration is ordered toward the pre-update
state with the same dependency-safety as the forward write, reversed: a
path being removed (undoing a forward creation) deepest-first, a path
being recreated (undoing a forward deletion) shallowest-first — never
arbitrary dictionary order, for the same directory↔file reasons the
forward write is ordered. Before restoring a path, it verifies that path's
CURRENT worktree content *and* index entry each still equal exactly what
the updater itself wrote (or already equal the pre-update state); a path
whose worktree or index an external process has changed since — either
one — is left completely untouched, and recovery is reported incomplete
for it rather than overwritten. Restoring a path uses the same
`--cacheinfo`/`cat-file` mechanism as the forward write, and recovery is
reported complete only when every one of its own Git commands actually
succeeded — a failed recovery-side command is never papered over as
completed. A real process kill/crash claims no automatic rollback:
because the ref advances last, an interruption before that step leaves
the ref at `C`, and the next `classify()` reports the resulting
dirty/untracked state rather than success.

`ApplyResult` reports `no_op`, `mutation_started`, `validation_ran`,
`validation_passed`, `rollback_attempted`, `rollback_completed`,
`concurrent_change`, a resulting `commit` only on an actually-applied
update, and a closed non-sensitive `failure` literal — never raw
Git/validator output or a `workspace/` path. A failed or aborted path is
never reported as `mutation_started` unless a live mutation genuinely
began, and `rollback_completed` is never true unless every touched path
was actually verified and restored.

## side-by-side migration

`system/update/side_by_side.py` owns the ZIP/no-Git conservative
side-by-side path. The original installation is read-only input
throughout — never written, chmod'd, renamed, unlinked, or normalized —
on success or on failure; recovery is never claimed for it because it was
never mutated. The destination is always a new/empty location, checked
before any pristine or Personal file is written; it may not be the
current installation, sit inside it, or have the current installation
sit inside it (checked both ways after resolving symlink indirection),
and a non-empty destination is never cleaned/deleted to "prepare" it.

The pristine distribution is materialized only from the already-resolved
`T` (`target.resolve()`; no repository, ref, branch, fork, PR, or archive
argument reaches `build_pristine`), reusing Loop 1/2's exact
`_materialized_target` fetch/verify boundary rather than a second
resolver. `git archive`'s tar stream is extracted through a bounded safe
extractor that rejects absolute paths, `..` traversal, symlink members,
and hardlink members before anything is written — defense in depth, since
an ordinary `git archive` of tracked content should not produce any of
these except a tracked symlink. `validate_public` runs against that
pristine tree, as a subprocess rooted at the pristine tree's own copy of
`validate_public.py` (never the live checkout's already-imported module,
so a target that itself changes validator logic is checked against its
own rules), before any current/Personal file enters the candidate; a
pristine validation failure stops there.

The current installation is scanned host-side without following
symlinks: a symlinked file or directory, or any other special file type
(FIFO/device/socket), is never read/copied/compared, only reported as
unsafe by path. Classification has no Git baseline, so it never infers
history or authorship: a current-only `workspace/` file is reported as
kept-from-current, never as user-created, since without a baseline it
may be either; overlap equality is decided by content hash only, never
mtime or size. A current-only or differently-overlapping file under
`system/`, `guides/`, or the repository root is a product-area
customization requiring manual resolution and is never copied
automatically; the pristine target's own copy of that path is
authoritative and untouched.

Every content read of a current source path — for classification
hashing and for the copy step alike — goes through one safe primitive
(`_safe_read_regular`) that opens the path once with `O_NOFOLLOW`,
confirms it is a regular file via `fstat` on that same descriptor, and
reads from that same descriptor; it never `lstat`s a path, confirms it
is regular, and then separately re-opens it by pathname for the actual
read — a path swapped for a symlink in that gap would otherwise let the
second, independent open follow it and read an outside target. A path
that fails this safe read (missing, a symlink, a special file, or the
platform has no `O_NOFOLLOW` to make the check safe at all) is a
bounded classification/migration failure, never an uncaught exception.

The one Personal-written state outside `workspace/` is the scope
mappings in `system/routing/context_registry.md`. Both the current and
target registry text are read exclusively with
`system.validation.validate_v1.context_registry_entries` (no second
parser). The target registry's own entries are validated before being
trusted as the carry-over baseline — a duplicate/ambiguous target
scope or target mapping, invalid scope grammar, or a target outside
`workspace/context/` is a conflict, never silently collapsed by
`dict.setdefault`, since neither `validate_public` nor
`validate_v1`'s own registry check covers every one of these target
alias-ownership classes. A current mapping is kept only if its target
is a `workspace/context/` directory actually present in the *resulting
candidate's own file set* — the pristine target's regular files plus
the selected current-only kept files, not the kept set alone, since a
scope already shipped by `T` or identically present on both sides is
just as preserved as one that exists only because of a kept file — and
a genuine scope/target conflict, within current entries or against the
validated target registry, fails closed rather than silently choosing
either side. The target registry's own text is written back verbatim,
with carried mappings inserted as an additional fenced `scope`/`→ target`
block — the same two-line shape the parser already understands, not a
new schema — so the migrated file round-trips through the identical
parser.

The preview binds `T`, a content-hash fingerprint of the materialized
pristine tree, the complete classified plan (including any requested
exclusions and the registry carry-over plan), into a digest exactly as
Loop 2 does. Before any Personal file enters the real destination,
`migrate` re-resolves `T`, rebuilds and revalidates the pristine
distribution into a throwaway location, reclassifies the current
installation, and recomputes the digest; any mismatch is a stale result
and no Personal file is copied. The REAL destination (a separate
extraction from that throwaway recheck tree) is then itself built,
validated with its own `validate_public.py`, and fingerprint-checked
against the same expected pristine fingerprint — validating only the
throwaway tree does not prove the real one is genuinely pristine —
before anything enters it. A manifest of the real destination's own
`(path, content hash)` pairs is captured at that point. Immediately
before copying each kept file, its live identity is re-verified against
the exact content hash the preview bound to it (never reading twice is
not assumed safe); a mismatch stops the migration as a concurrent
change rather than overwriting or silently accepting the new content,
and the destination copy's own hash is verified too before it is
accepted. Immediately before reporting the candidate ready, every
target-owned file the migration did not intentionally rewrite is
re-verified against that captured manifest, the one intentionally
rewritten product file (the registry) must have exactly the expected
reconstructed bytes, and no unexpected regular file, symlink, or special
path may have appeared anywhere in the destination — closing the window
between validating the destination and finishing the copy. After all of
that, `validate_v1 --mode personal` and `validate_prompts` run against
the candidate's own files (the same candidate-own-subprocess strategy
Loop 3 uses); `validate_public` legitimately runs against the real
destination before any Personal file enters it, but never again once
Personal content has.

Host code may read and hash full Personal/restricted/deny file bytes to
classify and copy them — this is the design's permitted opaque host-side
operation — but that content never appears in a `Plan`/`Preview`/
`MigrationResult` field, an exception message, or any diagnostic text;
only paths, classification labels, and content hashes do.

## scope

This file currently owns target resolution, the shared `controlled_git`
primitive, the dirty/untracked preflight, target materialization,
Git-clone classification, preview/digest binding, Git-clone apply and
recovery, and ZIP/no-Git side-by-side migration. Loop 5's Assistant
workflow/UX extends this file when implemented; it is not established
here.
