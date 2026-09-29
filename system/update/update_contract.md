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
empty, non-repository directory, so Git's upward repository discovery finds
no repository-local config either — system/global isolation alone does not
cover that scope. The canonical URL is passed literally on the command line,
never through a configured remote name. Apply (a later loop) reuses this
same primitive, supplying its own working directory inside the real
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

## scope

This file currently owns only target resolution and the shared
`controlled_git` primitive. Classification vocabulary, preview/confirmation
binding, apply/recovery result semantics, and side-by-side scope-carry-over
rules belong to the later loops of
`guides/developer/update/safe_update_implementation_plan.md` and extend this
file when implemented; they are not established here.
