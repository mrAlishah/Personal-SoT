# Safe Update implementation plan

## Status

Implementation plan for the approved design in
`guides/developer/update/safe_update_design.md` (approved at commit
`f2545bc3a30f1f9b00d9126cb2fc19a066ea3323`).

## How to use this plan

Five independently reviewable loops. Each loop follows:

```text
RED (failing tests) → minimal GREEN → regression validation
→ bounded review → fix substantiated findings → commit gate
```

Do not start a loop's GREEN work before its RED tests exist and fail for the
right reason. Do not advance to the next loop until the current loop's
commit gate passes. Each loop's scope is fixed; defer anything not listed as
in-scope to a later loop or to "explicitly out of scope".

## Reuse decision established for this plan

`system/routing/source_scope.py` already does:

```python
from system.validation.validate_v1 import SCOPE_RE, context_registry_entries
```

Four other production modules (`system/context/access.py`,
`system/personalization/explorer.py`, `system/personalization/profile_builder.py`,
`system/prompts/builder.py`, `system/diagnostics/doctor.py`) also import
directly from `system.validation.validate_v1`. `validate_v1.py`'s
"dependency-free" docstring means it has no *external* dependency beyond
`system.routing.runtime_naming`; it does not mean other modules may not import
its pure parsing functions and constants. Importing FROM `validate_v1` is the
established repository pattern, not a validator-depends-on-update inversion.

Loop 4 therefore imports `SCOPE_RE` and `context_registry_entries` directly
from `system.validation.validate_v1`, exactly like `source_scope.py` already
does. No extraction, no new parser, no registry framework.

## LOOP 1 — Canonical update contract + planning/classification model

### 1. Objective
Establish the shared contract and shared, host-independent data model both
update paths build on: immutable target resolution, failure classes, result
state, classification vocabulary, and preview/confirmation binding.

### 2. Canonical semantic owner(s)
`system/update/update_contract.md` (new). Owns target-resolution semantics,
classification vocabulary, preview/confirmation/result shape, and privacy
rules for both paths, per the design's Ownership section.

### 3. Exact files expected to be created or modified
- `system/update/update_contract.md` (new) — the contract prose.
- `system/update/target.py` (new) — target resolution and immutable-`T`
  pinning, shared by both paths. Also defines the one controlled-Git-
  invocation helper (`controlled_git(*args, cwd=None)`), because target
  resolution is itself security-critical and needs it from its first Git
  call, not only at apply time. No `__init__.py`: confirmed no sibling
  package (`system/connectors/`, `system/personalization/`,
  `system/tests/connectors/`) uses one; this repo relies on namespace
  packages.
- `system/tests/update/test_target_resolution.py` (new) — RED tests.

### 4. Existing code/contracts reused
- `system/connectors/github.py` (`GitHubSource.resolve`) for the
  `owner/repo` + ref → pinned commit pattern. `target.py` does not
  reimplement HTTP/`gh` calls; it either calls an injected resolver with the
  same `resolve() -> Snapshot`-shaped contract, or, when only local `git` is
  available, reads `git ls-remote https://github.com/mrAlishah/Personal-SoT
  main` for the same exact repository and ref — through the same
  `controlled_git` helper this loop introduces (see below), not a plain
  `subprocess.run`.
- Controlled Git configuration is established here, at the first Git call
  this design makes, not deferred to apply. System/global config alone is
  not the whole boundary: Git also discovers a *repository-local*
  `.git/config` by walking up from the current working directory, which is
  a separate scope `GIT_CONFIG_NOSYSTEM`/`GIT_CONFIG_GLOBAL` do not touch —
  if the resolver ever ran with `cwd` inside some repository (the installed
  Personal-SoT checkout, or any other repo on the machine), that repo's
  `url.*.insteadOf` could still redirect the canonical URL. `controlled_git`
  closes this with two controls, not one:
  1. **execution directory** — every resolution-phase Git call runs with
     `cwd` set to a freshly created, empty, non-repository directory (never
     the caller's checkout), so Git's upward repository discovery finds no
     `.git` at all and there is no repository-local config to read;
  2. **explicit environment** — `controlled_git` builds the child
     environment itself (an explicit small allowlist: `PATH`, and `HOME`/
     `XDG_CONFIG_HOME` pointed at that same empty controlled directory) and
     does not pass the parent process's environment through unfiltered. It
     sets `GIT_CONFIG_NOSYSTEM=1`, an empty `GIT_CONFIG_GLOBAL` override,
     and explicitly unsets/overrides any inherited `GIT_DIR`,
     `GIT_WORK_TREE`, `GIT_CONFIG_COUNT`, and `GIT_CONFIG_KEY_*`/
     `GIT_CONFIG_VALUE_*` variables, since an inherited process environment
     can itself inject config or redirect repository discovery without
     touching any file.

  The canonical URL is passed literally on the command line, never through
  a configured remote name. This is a fixed execution boundary (controlled
  directory + explicit environment), not a general Git sandbox framework.
  Loop 3's apply step, which necessarily runs inside the real checkout,
  reuses this same helper and adds only what it additionally needs there
  (hook-disabling; apply cannot use the empty-directory control since it
  must operate on the real worktree).
- `system/connectors/source.py` exports `Failure =
  Literal['source_unavailable', 'source_unauthorized', 'source_unresolved',
  'capability_unavailable', 'partial_coverage']`. Target resolution is the
  same category of operation (resolve via a host capability) as
  `source.py`/`github.py`, so `target.py` imports this `Failure` type and
  uses only the three members a resolution call can actually produce
  (`capability_unavailable`, `source_unresolved`, `source_unavailable`)
  rather than defining a parallel vocabulary for the same three meanings.
  Apply/migration-specific reasons that do not exist in `source.py` (stale
  preview, conflict, concurrent change, validation failure, unsafe path) are
  new literals owned by `update_contract.md`/Loop 3/Loop 4 — those are not
  read-resolution reasons and reuse would misuse `source.py`'s ownership.
- `system/assistant/safe_write_contract.md` for the
  preview → confirmation → re-check → write → validate → report pipeline.

### 5. RED tests first
In `test_target_resolution.py`, using an injected resolver callable (no real
network/`gh`), matching the `runner=` injection style of
`system/tests/connectors/test_github.py`:

- `test_resolves_canonical_repo_and_ref_to_commit` — resolver returns a
  commit for `mrAlishah/Personal-SoT` at `main`; `target.resolve()` returns
  that pinned commit.
- `test_public_api_accepts_no_repository_or_ref_argument` — structural:
  `inspect.signature(target.resolve)` has no repository/ref/commit
  parameter, proving no caller can override authority through the public
  API at all (there is no argument to describe, so this replaces describing
  an impossible call).
- `test_rejects_resolver_snapshot_for_wrong_repository` — the injected
  resolver itself returns a snapshot claiming a different repository (a
  misbehaving/misconfigured resolver implementation); `target.resolve()`
  independently checks the returned identity against its own fixed constant
  and rejects it, rather than trusting the resolver blindly.
- `test_rejects_resolver_snapshot_for_wrong_ref` — the resolver returns a
  snapshot for a non-`main` ref; rejected for the same reason.
- `test_capability_unavailable_fails_closed` — resolver raises "no
  capability"; `target.resolve()` returns a `capability_unavailable`-classed
  failure, not a silent fallback to a different source.
- `test_no_fabricated_target_on_partial_response` — resolver returns a
  malformed/partial snapshot (missing sha); `target.resolve()` fails closed
  rather than accepting a partial commit id.
- `test_default_resolution_requests_exact_repository_and_ref` — a spy in
  place of `GitHubSource` proves the default (no-resolver) path constructs
  it with `ref=CANONICAL_REF` explicitly, so resolution never depends on
  whatever the repository's `default_branch` happens to report.
- `test_local_git_fallback_ignores_global_url_rewrite`,
  `test_local_git_fallback_ignores_repository_local_url_rewrite`,
  `test_local_git_fallback_ignores_injected_git_env_vars` — each seeds two
  real local Git repos (a canonical fixture and an attacker fixture) with
  `target.CANONICAL_URL` patched to the local canonical fixture's `file://`
  path, so the whole test is network-free and deterministic; each then
  applies one poisoning vector (global `$HOME`/`GIT_CONFIG_GLOBAL`, the
  calling process's own `cwd` being a rewritten repository, and injected
  `GIT_CONFIG_COUNT`/`GIT_CONFIG_KEY_*`/`GIT_DIR`/`GIT_WORK_TREE`) and calls
  `target._resolve_via_git()` directly, asserting the result is the
  canonical fixture's commit, never the attacker fixture's.
- `test_controlled_git_closes_ancestor_repository_discovery` — patches
  `tempfile.gettempdir` to a real Git repository whose `.git/config` carries
  a rewrite, simulating the OS temp root landing inside some ancestor
  worktree; proves `GIT_CEILING_DIRECTORIES` stops Git's upward discovery
  before it reaches that ancestor's config.
- `test_controlled_git_rejects_http_redirect_to_alternate_authority` — two
  local loopback HTTP servers (one issuing a 301, one recording whether it
  was ever contacted); proves `controlled_git`'s own isolated global config
  (`http.followRedirects = false`) makes the command fail closed on the
  redirect rather than following it to the second server, which Git's
  documented default (`initial`) would otherwise do.

### 6. What each RED test proves
That target authority is fixed to `mrAlishah/Personal-SoT:main` in code (not
configuration or prompt input), that no alternate remote/fork/PR/commit can
become authority, and that resolution failure is fail-closed and classified.

### 7. Minimal GREEN implementation
`target.py`: one function, `resolve(runner=None) -> TargetSnapshot | Failure`,
plus a frozen `TargetSnapshot(commit, ref, resolved_via)` dataclass, using
`system.connectors.source.Failure` for its rejection reasons rather than a
new literal type. No caller-supplied repository or ref parameter exists in
the public function signature — this is what makes rejection of alternates
structural rather than a runtime check. The default (no-resolver) path
constructs `GitHubSource(CANONICAL_REPOSITORY, ref=CANONICAL_REF)` rather
than letting it fall back to the repository's `default_branch`. Also
`controlled_git(*args, cwd=None, runner=subprocess.run)`: when `cwd` is
omitted, it creates a fresh empty temporary directory and runs there
instead of the caller's directory, with `GIT_CEILING_DIRECTORIES` set to
that directory's own parent so upward repository discovery cannot continue
past it even if the temp root itself sits inside some ancestor repository;
it always builds the child environment explicitly (`PATH`, `HOME`/
`XDG_CONFIG_HOME` pointed at that same controlled directory,
`GIT_CONFIG_NOSYSTEM=1`, `GIT_DIR`/`GIT_WORK_TREE`/`GIT_CONFIG_COUNT`/
`GIT_CONFIG_KEY_*`/`GIT_CONFIG_VALUE_*` explicitly absent) rather than
passing `os.environ` through, and points `GIT_CONFIG_GLOBAL` at its own
freshly written file containing only `http.followRedirects = false` — not
an empty file — so a single HTTP redirect on the initial request cannot
substitute a different repository as the effective target, which Git's own
default (`initial`) would otherwise allow. The direct-git fallback in
`resolve()` is its first caller, using the auto-created empty directory.
`update_contract.md`: prose stating the shared target-resolution rule,
failure classes, the controlled-Git requirement (execution directory,
ceiling boundary, explicit environment, and redirect policy) for every
updater-issued Git call starting at resolution, and that both paths call
the same `target.resolve()`.

### 8. Regression tests/checks
```text
python3 -m unittest system.tests.update.test_target_resolution
python3 system/validation/validate_public.py
python3 system/validation/validate_v1.py --mode core
```

### 9. Privacy/access invariants
No content is read yet in this loop — only a commit id and ref name are
resolved. Nothing here reads or discloses Personal content, so no
Personal-data invariant applies until Loop 2/4. `Failure` values must not
embed raw transport output (matches `source.py`'s existing rule).

### 10. Failure cases
Resolver unavailable, resolver returns wrong repository (defensive check even
though the caller cannot supply one), resolver returns a non-`main` default
branch drift (treated as `T` still being whatever `main` resolves to, not an
error — `main` is authoritative by name, not by a cached expectation).

### 11. Explicit out-of-scope items
No Git tree comparison, no classification, no preview, no ZIP handling, no
Assistant wiring. No caching of a previously resolved `T` across processes.

### 12. Review questions
- Does any code path accept a repository or ref value from outside
  `target.py`'s fixed constants?
- Does `GitHubSource` reuse avoid reimplementing HTTP/`gh` transport?
- Is the failure vocabulary closed (not a free-text string)?
- Does every Git invocation in `target.py`, including the direct-git
  fallback, go through `controlled_git`, with no direct `subprocess.run`
  call to `git` anywhere else in the module?
- Does `controlled_git` build its child environment explicitly rather than
  passing `os.environ` through, and does the resolution path run from a
  fresh empty directory rather than the caller's `cwd`?
- Does the default (no-resolver) path pin `ref=CANONICAL_REF` explicitly,
  rather than depending on `GitHubSource`'s `default_branch` fallback?
- Does `GIT_CEILING_DIRECTORIES` actually stop upward repository discovery
  when the controlled temp directory is created under an ancestor
  repository, not only when it happens to have no ancestor repository?
- Does `controlled_git`'s own global config set `http.followRedirects =
  false`, closing the one-hop redirect Git's own default would follow?

### 13. Completion gate
All Loop 1 tests pass; `validate_public.py` and `validate_v1.py --mode core`
pass on a clean export; no other file outside section 3 changed.

### 14. Intended commit boundary/message
One commit. `feat(update): add canonical target resolution contract`

---

## LOOP 2 — Git classification + preview binding

### 1. Objective
Implement the read-only Git path: resolve `C`, `T`, `B`, classify every path
per the design's state table, and produce a preview bound to that classified
state. No mutation of the installed clone.

Loop 1's `target.resolve()` returns a commit id for `T`, not its Git
objects — a stale local clone will not already have `T`'s tree/history.
This loop therefore also materializes `T` into an updater-owned ephemeral
inspection repository (never the live checkout) before `B`/tree
classification can run against it. That materialization step is itself
read-only with respect to the installed clone: it never touches its ref,
index, worktree, remote configuration, remote-tracking refs, `FETCH_HEAD`,
or object database.

### 2. Canonical semantic owner(s)
`system/update/git_update.py` (new), classification and preview functions
only. `update_contract.md` gets the classification-vocabulary section filled
in with the exact state names from the design table.

### 3. Exact files expected to be created or modified
- `system/update/git_update.py` (new) — `classify(root) -> Plan`,
  `preview(plan) -> Preview` (digest-bound), plus the dirty/untracked check
  and the target-materialization step below. The ephemeral inspection
  repository this step creates is a runtime temporary directory this
  function manages and removes within one call, exactly like Loop 1's
  `controlled_git` temp directories — not a new tracked file, not a second
  module, not a persisted inventory or cache.
- `system/tests/update/test_git_classification.py` (new).
- `system/update/update_contract.md` (extend from Loop 1).

### 4. Existing code/contracts reused
- `target.resolve()` from Loop 1 for the pinned commit `T`.
- `target.controlled_git` for every Git invocation this loop issues,
  including the target-materialization fetch and the dirty/untracked
  preflight against the live checkout. Passing an explicit `cwd` (the
  ephemeral inspection repository, or the live checkout for the preflight)
  already gets `controlled_git`'s environment isolation and redirect
  hardening without its auto-empty-directory/ceiling behavior, exactly as
  Loop 1 designed that mode for apply-phase reuse; Loop 2 is simply its
  second real caller. One small, additive, **closed** change to
  `controlled_git` itself is needed: an `extra_env: dict | None = None`
  parameter that may add only the two literal keys this loop's local-only
  classification calls need — `GIT_ALTERNATE_OBJECT_DIRECTORIES` and
  `GIT_NO_REPLACE_OBJECTS` — checked against a fixed allowlist inside
  `controlled_git` itself; any other key, including any of the
  authority-bearing variables Loop 1 already controls (`HOME`,
  `XDG_CONFIG_HOME`, `PATH`, `GIT_CONFIG_GLOBAL`, `GIT_CONFIG_NOSYSTEM`,
  `GIT_CONFIG_COUNT`, `GIT_CONFIG_KEY_*`, `GIT_CONFIG_VALUE_*`, `GIT_DIR`,
  `GIT_WORK_TREE`, `GIT_CEILING_DIRECTORIES`), makes `controlled_git` raise
  before building the process environment at all — a caller cannot reopen
  Loop 1's isolation merely by naming one of its keys in `extra_env`. This
  is not a general environment-extension framework: the allowlist is fixed
  to exactly today's two keys, and a later loop that needs a different key
  extends the allowlist itself, deliberately and reviewably, rather than
  inheriting an already-open door. Existing callers are unaffected: the
  default `None` changes nothing about Loop 1's behavior. The
  materialization fetch call itself passes no `extra_env` and gets exactly
  Loop 1's unchanged baseline — it never has alternate/private-object
  visibility. The dirty/untracked preflight needs no `extra_env` either;
  its hardening (`--no-optional-locks`, `-c core.fsmonitor=false`) is
  ordinary Git command-line arguments, already supported today through
  `controlled_git`'s existing `*args`.
- Real temporary Git repositories built with `git init`/`git commit`
  (subprocess, real Git — not a mocked runner) as fixtures, because tree
  identity, merge-base, and dirty-state detection must be verified against
  actual Git behavior; a mocked subprocess cannot prove tree-identity logic.
  This mirrors the repo's existing willingness to use real Git plumbing
  (`github.py` fakes the transport, not Git semantics).

### 5. RED tests first
Each test builds a small temp repo pair (or one repo with two branches
standing in for current/target) and calls `git_update.classify`:

- `test_upstream_only_change_is_update` — local unchanged from `B`, target
  changed → `upstream_only`.
- `test_user_only_change_is_preserved` — target unchanged from `B`, local
  changed/created → `user_only`.
- `test_shipped_workspace_file_unchanged_locally_updates`.
- `test_both_changed_is_conflict` — different content both sides → `conflict`,
  not merged.
- `test_target_deletes_locally_modified_path_is_conflict`.
- `test_identical_change_both_sides_is_no_change`.
- `test_dirty_worktree_blocks_before_classification`.
- `test_untracked_path_blocks_before_classification`.
- `test_dirty_result_reports_area_and_count_not_paths` — asserts the blocked
  result's message contains no repository-relative path under `workspace/`
  (not only `workspace/context/`), only a count/area, matching the design's
  non-leaking requirement. `workspace/` broadly can hold user-chosen names —
  projects, custom prompts, custom profiles — not only `workspace/context/`.
- `test_already_current_when_c_equals_t`.
- `test_no_op_when_t_is_ancestor_of_c`.
- `test_normal_update_when_diverged_with_valid_merge_base`.
- `test_fails_closed_on_unrelated_lineage` — no merge base → fail-closed
  classification, not a downgrade or forced merge.
- `test_preview_digest_binds_c_t_b_and_plan`.
- `test_stale_preview_rejected_when_c_changes` — re-resolving after a
  simulated local commit invalidates the old digest.
- `test_target_absent_locally_is_materialized` — `T` is a commit the
  installed clone's object database has never seen; classification still
  succeeds, proving the fetch step actually runs rather than assuming the
  object is already present.
- `test_materialization_fetches_exact_canonical_main_not_a_local_remote` — a
  spy/patched `controlled_git` call captures the fetch invocation's URL
  argument; it is the literal canonical URL, and no `git remote add`/`origin`
  is ever created in the ephemeral repository.
- `test_fetched_main_must_equal_already_resolved_t` — the fetch step is made
  to return a commit different from the `T` Loop 1 already resolved (a
  simulated race); classification stops as stale, not silently reclassified
  against the new commit.
- `test_stale_target_between_resolve_and_fetch_fails_closed` — same
  scenario end to end through `classify()`, asserting the blocked/stale
  result rather than a `Plan`.
- `test_materialization_does_not_modify_live_ref_index_worktree_or_objects`
  — snapshot the installed clone's `HEAD`, every ref, index bytes, tracked
  worktree file bytes, and the object database's file listing before
  `classify()`; assert byte-for-byte identical after, for both a successful
  and a stale/failed materialization.
- `test_alternate_object_access_attached_only_after_fetch_completes` — a
  spy on the Git-invocation environment proves no call made before the
  fetch-and-verify steps carries `GIT_ALTERNATE_OBJECT_DIRECTORIES`, and no
  further Git call carrying a remote URL argument happens after it is
  attached.
- `test_replace_refs_do_not_alter_merge_base` — a replace ref (`git replace`)
  on a fixture commit that would change its apparent parent; classification
  computes the same `B`/state as without the replace ref, proving
  `GIT_NO_REPLACE_OBJECTS=1` is honored.
- `test_multiple_merge_bases_fail_closed` — a criss-cross fixture history
  where `git merge-base --all C T` returns more than one commit; fails
  closed as ambiguous lineage rather than picking either arbitrarily.
- `test_classification_does_not_invoke_external_diff_or_filter_helpers` — a
  fixture repo configures a `.gitattributes`/`diff.*.textconv`/
  `filter.*.clean` helper that would fail loudly or write a sentinel file if
  ever invoked; classification completes without triggering it, since it
  compares tree/blob identity only.
- `test_current_only_path_outside_workspace_is_area_count_not_named` — a
  current-only file directly under the repository root (never present in
  `T`'s tree at any baseline, so classified `user_only` by the state table)
  is reported by area/count, not by name, at the default detail level, the
  same as a current-only `workspace/` path — the naming boundary is
  classification state, not location.
- `test_upstream_only_shipped_path_may_be_named` — a `system/`/`guides/`/
  root path classified `upstream_only` (present in `T`, not user-created) is
  named at the default detail level, since that classification itself
  establishes it as accepted product history, never a user-chosen path.
- `test_controlled_git_rejects_protected_key_in_extra_env` — calling
  `controlled_git(..., extra_env={'HOME': '/tmp/attacker'})` (or any other
  key `target.py` already treats as authority-bearing) raises before any
  process environment is built; the same call with only
  `GIT_ALTERNATE_OBJECT_DIRECTORIES`/`GIT_NO_REPLACE_OBJECTS` still
  succeeds.
- `test_materialization_fetch_never_receives_extra_env` — a spy on the
  fetch-phase `controlled_git` call proves it is made with no `extra_env`
  argument at all, so the fetch never has alternate/private-object
  visibility regardless of what classification later attaches.
- `test_dirty_preflight_blocks_when_filter_or_textconv_is_configured` — a
  fixture repo with a `.gitattributes` `filter=`/`diff=` attribute (or the
  matching `filter.*.clean`/`diff.*.textconv` config) declared for a tracked
  path; the preflight reports unsafe-repository-state and blocks rather
  than risking that helper's invocation to determine dirtiness.
- `test_dirty_preflight_runs_with_no_optional_locks_and_fsmonitor_disabled`
  — a spy on the preflight's Git invocation proves it always includes
  `--no-optional-locks` and `-c core.fsmonitor=false`, regardless of ambient
  repository configuration.
- `test_dirty_preflight_never_invokes_configured_helper` — same
  `.gitattributes`/filter fixture as above, but with the helper itself
  writing a sentinel file if ever executed; after a blocked preflight, the
  sentinel is absent.
- `test_index_bytes_unchanged_by_clean_preflight` and
  `test_index_bytes_unchanged_by_blocked_preflight` — byte-identical
  `.git/index` before/after, for both a clean checkout and a
  dirty/unsafe-state checkout.
- `test_preflight_worktree_ref_and_object_store_unchanged` — extends the
  existing live-mutation snapshot test to cover the preflight step
  specifically, not only the target-materialization fetch.

### 6. What each RED test proves
Every state-table row and lineage rule from the design is exercised against
real Git tree identity, the dirty-state guidance never leaks paths, the
preview cannot be replayed against changed state, target materialization
actually fetches what classification needs without ever mutating the
installed clone, local/private object ids never reach the canonical fetch's
negotiation, history cannot be reinterpreted through replace refs or an
arbitrarily chosen merge base, `extra_env` cannot reopen an authority-bearing
variable Loop 1 already controls, and the dirty/untracked preflight itself
never mutates the live checkout or risks executing a configured helper to
determine dirtiness.

### 7. Minimal GREEN implementation

**Dirty/untracked preflight**, run first, directly against the live
checkout (`cwd=root`, no `extra_env`):

1. Check whether anything could require executing user-defined code to
   determine accurate dirtiness: read `.gitattributes` (plain text, not
   through any filter machinery — reading raw bytes invokes nothing) for a
   `filter=`/`diff=` attribute on any tracked path, and read the resolved
   config for a matching `filter.<driver>.clean`/`filter.<driver>.process`/
   `diff.<driver>.textconv` value (`man gitattributes`: "$ git status # Show
   files that will be normalized" — status/diff apply the effective
   clean-equivalent transformation to decide dirtiness, not only at
   `add`/`commit`; `--no-textconv`/`--no-ext-diff` only affect *displayed*
   patch text, not this underlying comparison, so they are not a fix here).
   If any such filter/textconv is configured for a tracked path, stop and
   report unsafe-repository-state — a non-sensitive capability result, not
   a content leak — rather than risk invoking it.
2. Otherwise, `controlled_git('--no-optional-locks', '-c',
   'core.fsmonitor=false', 'status', '--porcelain=v2',
   '--untracked-files=all', cwd=root)`. `--no-optional-locks`
   (`GIT_OPTIONAL_LOCKS=0`) is documented (`man git`) specifically to
   "prevent git status from refreshing the index as a side effect" — the
   control this loop's index-unchanged invariant depends on.
   `-c core.fsmonitor=false` disables any configured fsmonitor hook/daemon
   query for this one invocation regardless of ambient repository
   configuration. With no filter/textconv configured (step 1 already ruled
   that out), the ordinary stat-based fast path this command uses cannot
   fall through to an external helper. A dirty index/worktree or untracked
   path blocks before target materialization or classification proceed, per
   the existing state table.

**Target materialization**, run only once the preflight passes, strictly in
this order:

1. `git init --bare <ephemeral>` — a fresh, empty, updater-owned temporary
   directory; not the live checkout, not a tracked file, not persisted past
   this call. Bare because only objects are needed, never a working tree.
2. `controlled_git('fetch', target.CANONICAL_URL,
   target.CANONICAL_REF + ':refs/heads/_target', cwd=ephemeral)`, fetching
   the exact and unambiguous `refs/heads/main` — the literal canonical URL,
   never a configured remote name (no `git remote add` is ever run;
   `origin` is never created as authority in the ephemeral repository). At
   this point the ephemeral repository's object database contains only what
   this one fetch brought in: it has no alternate object directory yet, so
   it has nothing of the installed clone's to advertise, and Git's fetch
   negotiation cannot include any installed-clone object id in what it
   tells the canonical remote it already "has". This call passes no
   `extra_env`; it never has alternate/private-object visibility.
3. `git rev-parse refs/heads/_target` in the ephemeral repository; if this
   does not equal the `T` Loop 1 already resolved, canonical `main` moved
   between resolution and fetch — stop and report stale target, the same
   stale-input semantics `test_stale_preview_rejected_when_c_changes`
   already covers for `C`, extended to `T`. Never silently classify against
   the newly observed commit; that would replay a different, unreviewed
   target than the one about to be bound into the preview digest.
4. Only now, with target-fetch network activity finished, attach the
   installed clone's object database to the ephemeral repository read-only,
   via `controlled_git`'s new, allowlist-checked
   `extra_env={'GIT_ALTERNATE_OBJECT_DIRECTORIES': ...}` on the
   classification-phase Git calls that follow. No further network operation
   happens after this point in the same materialization; if a later network
   call were ever needed, it would first have to detach the alternate
   again. Alternates share objects without touching the live repository's
   refs, index, worktree, or its own object database — nothing is written
   into `<root>/.git`.

**Classification**, run in the ephemeral repository via
`controlled_git(..., cwd=ephemeral, extra_env={'GIT_ALTERNATE_OBJECT_DIRECTORIES':
root/'.git/objects', 'GIT_NO_REPLACE_OBJECTS': '1'})`, so a `refs/replace/`
entry (local or, in principle, one carried in by the alternate) cannot alter
which history classification actually sees — accepted public lineage must be
judged from raw stored commit objects, not a locally rewritten view. The
legacy `.git/info/grafts` mechanism needs no separate control here: it is
read only from the repository actually being operated on, and an alternate
shares only the object database, never `.git/info/`, so nothing the live
repository might contain there can ever reach the ephemeral repository's
computation regardless.

- `B`: `git merge-base --all C T`. More than one line means multiple merge
  bases (a criss-cross history); this fails closed as unrelated/ambiguous
  lineage, the same outcome as no merge base at all — never an arbitrarily
  chosen first line.
- Per-path state: compare `git ls-tree -r`/blob-id lookups at `B`, `C`, and
  `T` — tree/blob identity only, never `git diff` or any command that would
  invoke a configured external diff/textconv/clean/smudge/fsmonitor helper.
  This is already the design's own rule (Git tree identity, not text
  merging); this loop's plumbing choice is what makes it structurally true
  rather than incidentally true. `classify(root, target_commit)` returns a
  `Plan` (frozen dataclass: tuples of classified paths per state + a
  `blocked` reason or `None`).

`preview(plan)` returns a `Preview` with a `digest` (sha256 over `C`, `T`,
`B`, and a canonical serialization of the plan) and a beginner-safe summary:
counts per state and per area for anything under `workspace/`, since any
`workspace/` path may contain a user-chosen name (a project, a custom
prompt, a custom profile), not only paths under `workspace/context/`. The
naming boundary is classification state, not location: a path classified
`upstream_only` or already-aligned is present in `T`'s tree, which itself
establishes it as accepted product history, so it may be named at the
default detail level regardless of where it sits. A `user_only`
(current-only) path is, by that same classification, never present in `T` —
it may still carry a user-chosen name, so it is reported by area/count only,
whether it sits under `workspace/` or anywhere else.

### 8. Regression tests/checks
```text
python3 -m unittest system.tests.update.test_target_resolution system.tests.update.test_git_classification
python3 system/validation/validate_public.py
python3 system/validation/validate_v1.py --mode core
```

### 9. Privacy/access invariants
Beginner-facing preview summary never lists a `workspace/` path by name —
the boundary is "user-owned surface" (all of `workspace/`), not
`workspace/context/` alone, since prompts, profiles, and presentation
overlays under `workspace/` can also carry user-chosen names. The naming
boundary is classification state, not location: a `user_only` (current-only)
path is never present in `T`, so it is area/count only wherever it sits,
including outside `workspace/`; a path present in `T` (upstream-only or
already aligned) is established as accepted product history by that
classification itself and may be named. Whether and when a path may appear
in Advanced detail is not decided in this loop; see Loop 5, which defines
the actual authorization for that (Doctor's `advanced` flag is
presentation-only and is not treated as an access decision — see Loop 5
section 4).

Target materialization is a second, independent privacy boundary: no
installed-clone object id may reach the canonical fetch's negotiation. This
is enforced by ordering, not by filtering — the ephemeral repository has no
alternate object access at all until after the fetch-and-verify steps
finish, so it has nothing of the installed clone's to advertise while
talking to the canonical remote, and no further network call happens once
the alternate is attached. `extra_env`'s fixed allowlist is a third boundary:
a caller cannot reopen any of Loop 1's authority-bearing environment
variables merely by naming them in a Loop-2-issued call.

### 10. Failure cases
No merge base; multiple merge bases (ambiguous lineage); dirty index; dirty
worktree; untracked Personal file; a configured filter/textconv that makes
accurate dirty-state inspection unsafe (reported as unsafe-repository-state,
not a content leak); stale digest reuse; canonical `main` moving between
target resolution and materialization fetch; `T` resolution failure
propagated from Loop 1.

### 11. Explicit out-of-scope items
No apply, no mutation, no recovery, no ZIP path, no confirmation storage
beyond returning the digest for the caller to hold. The ephemeral inspection
repository is not an installed-version inventory, not an updater cache, and
is not retained after the call; no persisted mapping of past resolutions is
introduced. `extra_env` is not a general subprocess-environment extension
framework: its allowlist covers exactly today's two keys, and no other key
is pre-authorized for a later loop.

### 12. Review questions
- Does classification ever perform a text/semantic merge for a both-changed
  path? (Must not.)
- Does the blocked-dirty message leak any path under `workspace/` at all
  (not only `workspace/context/personal` or `workspace/context/organizations`)?
- Is the "ahead/divergent" lineage split from the design (no-op /
  normal-update / fail-closed) implemented as three distinct outcomes?
- Does target materialization ever touch the installed clone's ref, index,
  worktree, remote configuration, remote-tracking refs, `FETCH_HEAD`, or
  object database?
- Is the installed clone's object database attached as an alternate only
  after the canonical fetch and its `T`-equality check both complete, with
  no Git call carrying a remote URL argument afterward?
- Does classification use `git merge-base --all` and fail closed on more
  than one result, rather than `git merge-base`'s arbitrary single pick?
- Does classification run with `GIT_NO_REPLACE_OBJECTS=1`, and does it use
  tree/blob identity plumbing exclusively, never a command that would invoke
  a configured external diff/textconv/clean/smudge/fsmonitor helper?
- Does `controlled_git`'s `extra_env` allowlist reject every authority-
  bearing key Loop 1 already controls, not only the two it currently adds?
- Does the dirty/untracked preflight actually check for a configured
  filter/textconv before proceeding, rather than only passing
  `--no-optional-locks`/`-c core.fsmonitor=false` and hoping nothing fires?
- Is the fetch-phase `controlled_git` call ever made with an `extra_env`
  argument? (Must not be.)

### 13. Completion gate
All Loop 1 + Loop 2 tests pass; no mutation function exists yet in
`git_update.py`; validators pass on a clean export.

### 14. Intended commit boundary/message
One commit. `feat(update): add Git classification and bound preview`

---

## LOOP 3 — Recoverable Git apply + Personal validation

### 1. Objective
Implement the mutation boundary: build a candidate outside the live
checkout, validate it with Personal validators, then advance the live state
only if every validator passes, with bounded recovery.

### 2. Canonical semantic owner(s)
`system/update/git_update.py` (extended with apply/recovery functions).

### 3. Exact files expected to be created or modified
- `system/update/git_update.py` (extend).
- `system/tests/update/test_git_apply.py` (new).

### 4. Existing code/contracts reused
- `validate_v1.run(candidate_root, "personal")` and `validate_prompts.run`,
  called against the candidate path, not the live root — reusing the exact
  functions already used by `doctor.py` and `project_workflow.md`.
- Real temporary Git repositories, as in Loop 2. All apply-side Git
  invocations reuse Loop 1's `controlled_git` helper (the same isolated-
  configuration boundary used for target resolution) rather than a second,
  apply-specific controlled-invocation mechanism; this loop adds hook-
  disabling (`core.hooksPath` pointed at an empty directory, verified
  empirically that a real hook does not fire) as an additional argument
  `controlled_git` passes, not a new wrapper.

### 5. RED tests first
- `test_candidate_built_outside_live_checkout` — live worktree files are
  unchanged while the candidate is being built and validated.
- `test_candidate_validated_with_personal_mode` — a candidate that fails
  `validate_v1 --mode personal` never reaches the live ref.
- `test_candidate_validated_with_prompts` — same, for `validate_prompts`.
- `test_validate_public_not_invoked_on_personal_candidate` — spy/patch proves
  `validate_public.run` is never called by the Git apply path.
- `test_hooks_do_not_fire` — a repo with an `update`/`post-checkout`/
  `reference-transaction` hook that writes a sentinel file; after apply, the
  sentinel is absent.
- `test_apply_uses_controlled_git_for_every_invocation` — every Git call
  `apply()` issues goes through Loop 1's `controlled_git`, not a bare
  `subprocess.run`; re-verifies (does not re-derive) that a
  `url.<other>.insteadOf` rewrite pointing at the canonical URL has no
  effect during apply, the same property Loop 1 already proved for
  resolution.
- `test_clean_state_rechecked_immediately_before_mutation` — a simulated
  external write between preview and apply aborts before mutation.
- `test_ref_advances_last_with_expected_old_value` — the ref update uses a
  compare-and-swap that fails if `C` moved concurrently.
- `test_failed_validation_restores_pre_update_state` — index/worktree/ref
  hashes match the pre-update snapshot exactly after a validator failure.
- `test_concurrent_external_change_stops_automatic_recovery` — after apply
  begins, an external process changes a file the updater also touched;
  recovery reports incomplete rather than overwriting it.
- `test_interrupted_process_leaves_ref_at_c` — killing the updater between
  candidate-build and ref-advance (simulated by raising inside that window)
  leaves the current ref unchanged, and a subsequent classify() reports
  unstable state rather than claiming success.
- `test_result_flags_are_truthful` — each combination (mutation_started,
  validation_ran, validation_passed, rollback_attempted, rollback_completed,
  concurrent_change) matches the actual sequence of calls made.

### 6. What each RED test proves
The candidate/live separation, the Personal-not-public validator boundary,
non-hooking execution, compare-and-swap ref safety, and that recovery claims
are never stronger than what was actually verified — directly answering the
design's "recovery guarantee" requirement.

### 7. Minimal GREEN implementation
`build_candidate(root, plan, target_commit) -> Path` (temp directory).
`validate_candidate(candidate_root) -> ValidationOutcome` (calls the two
Personal validators, never `validate_public`). `apply(root, plan, digest) ->
ApplyResult` — re-resolves and re-classifies, aborts on mismatch, applies
using `target.controlled_git` (Loop 1) for every Git call, with hooks
disabled, checks clean state immediately before mutation, advances the ref
last with an old-value check, and on any failure attempts recovery only for
paths it verifies are still in the updater-written state.

### 8. Regression tests/checks
```text
python3 -m unittest discover system/tests/update
python3 system/validation/validate_public.py
python3 system/validation/validate_v1.py --mode core
python3 system/validation/validate_prompts.py
```

### 9. Privacy/access invariants
Apply never reads restricted/denied content to decide classification (Loop 2
already establishes this at the tree-identity level, not content level). A
path itself can carry Personal meaning (a project name, a custom prompt or
profile name), so failure reports do not surface a `workspace/` path by
name; they report state and, for the affected area, the same area/count
shape Loop 2 defines. Only a shipped `system/`/`guides/`/root path, which is
never user-chosen, may be named in a failure report.

### 10. Failure cases
Candidate validation failure (both validators), concurrent external mutation
detected pre-mutation, concurrent external mutation detected mid-recovery,
process interruption, hook/filter attempted and blocked, ref CAS failure.

### 11. Explicit out-of-scope items
No ZIP path, no Assistant wiring, no `validate_public` call anywhere in this
loop, no commit-message/merge-message content beyond what the design already
specifies (baseline + target provenance).

### 12. Review questions
- Is there any code path where `validate_public` runs against the Personal
  candidate? (Must be none — greppable via the spy test.)
- Does recovery ever overwrite a path it did not itself write, even under
  failure?
- Are all result-flag combinations reachable by a test, or are any claimed
  by prose alone?

### 13. Completion gate
All Loop 1–3 tests pass; the `test_validate_public_not_invoked_on_personal_candidate`
spy test passes; validators pass on a clean export.

### 14. Intended commit boundary/message
One commit. `feat(update): add recoverable Git apply with Personal validation`

---

## LOOP 4 — ZIP/no-Git side-by-side migration

### 1. Objective
Implement the conservative side-by-side path: materialize a pristine
distribution from `T`, validate it as public before Personal state enters,
preserve `workspace/` files and the scope registrations they need, and leave
the original installation untouched.

### 2. Canonical semantic owner(s)
`system/update/side_by_side.py` (new).

### 3. Exact files expected to be created or modified
- `system/update/side_by_side.py` (new).
- `system/tests/update/test_side_by_side.py` (new).

### 4. Existing code/contracts reused
- `target.py` (Loop 1) for `T`.
- `validate_public.run(pristine_root)` before any Personal file is copied in.
- `validate_v1.run(candidate_root, "personal")` and `validate_prompts.run`
  after migration (same calls as Loop 3, applied to the ZIP candidate).
- **`from system.validation.validate_v1 import SCOPE_RE,
  context_registry_entries`** — the same import `system/routing/source_scope.py`
  already makes. `context_registry_entries(text)` parses the existing
  `context_registry.md` fenced-block shape (`scope` line then `→ target`
  line); `side_by_side.py` uses it to read both the current and target
  registry files, then writes kept entries back in the identical shape
  (`scope\n→ target\n`) so the existing parser round-trips them. No new
  parser, no writer framework — this is string templating of an already-
  understood two-line shape, not a schema.
- The design explicitly permits host-side opaque comparison/copying of
  Personal files ("Comparison and copying of Personal files are host-side
  opaque operations"). This loop distinguishes that permitted host-side
  byte read/hash from a different, forbidden thing: file content reaching
  AI/model context, previews, diagnostics, or logs. Trusted host code may
  read and hash full file bytes to classify overlaps correctly; only the
  resulting classification (identical/different/kept/conflict) and paths
  cross into `Plan`/`Preview`/`Result`.

### 5. RED tests first
- `test_pristine_distribution_built_only_from_t` — no path derived from an
  archive/branch/fork argument reaches the distribution build call.
- `test_pristine_validated_before_personal_files_enter` — a pristine tree
  that fails `validate_public` stops before any `workspace/` copy occurs.
- `test_original_installation_untouched` — source tree hashes are identical
  before/after a full run, including a failing run.
- `test_destination_must_be_new_and_empty` — a non-empty destination is
  rejected before any copy.
- `test_current_only_workspace_file_preserved`.
- `test_identical_workspace_overlap_needs_no_action`.
- `test_different_workspace_overlap_is_conflict`.
- `test_current_only_system_or_guides_file_not_copied` — reported as
  "requires manual resolution", never silently copied.
- `test_symlink_rejected`.
- `test_special_file_rejected` (fifo/device, where the test platform allows
  creating one; skip with a reason on platforms that don't).
- `test_path_traversal_rejected` (`../`-style entry).
- `test_outside_root_path_rejected`.
- `test_current_only_workspace_file_labeled_kept_not_user_created` — asserts
  the preview wording distinguishes "kept from current installation" from a
  confirmed user-authored file, per the design.
- `test_scope_registration_kept_for_preserved_scope` — a current registry
  entry whose target is a preserved `workspace/context/` directory appears
  in the migrated registry.
- `test_scope_registration_dropped_for_non_preserved_scope` — a current
  entry whose target is not preserved is excluded and reported.
- `test_duplicate_scope_conflict` — same scope name, different target,
  current vs. target registry → conflict, not silently overwritten.
- `test_duplicate_target_conflict` — same target claimed by two scope names
  → conflict.
- `test_current_system_registry_file_not_copied_wholesale` — the target
  registry's own product entries are unaffected by unrelated current
  entries.
- `test_migrated_registry_round_trips_through_context_registry_entries` —
  the written registry, re-parsed with `context_registry_entries`, yields
  exactly the expected kept + target entries (proves shape compatibility
  with the existing parser, satisfying the reuse requirement concretely).
- `test_final_validate_v1_personal_runs_on_candidate`.
- `test_final_validate_prompts_runs_on_candidate`.
- `test_preview_bound_to_t_and_plan`.
- `test_stale_zip_preview_rejected_on_target_or_state_change`.
- `test_overlap_equality_uses_content_hash` — two files with identical
  content but different mtimes classify as identical; two files with the
  same size/mtime but different content classify as different. Proves
  equality is decided by content hash, not by mtime or size, which the
  design's "identical overlaps need no action" / "different overlaps are
  conflicts" rule depends on for correctness.
- `test_host_side_hashing_of_restricted_content_is_allowed` — the host
  reads and hashes the full bytes of a `deny`/`restricted` module to decide
  identity/copy; this is the approved opaque host-side operation and is not
  itself a violation.
- `test_restricted_content_never_enters_plan_or_preview_or_result` — the
  `Plan`/`Preview`/migration `Result` objects for a run touching a
  `deny`/`restricted` module contain no file content anywhere in their
  fields, only paths/classification/hashes.
- `test_restricted_content_never_enters_diagnostics_or_logs` — nothing
  written to the returned report, a raised exception message, or any
  log-like output contains file content, for the same run.

### 6. What each RED test proves
Every side-by-side bullet in the design, the registry carry-over/conflict
rule from finding B-1, and that the reused parser's fenced-block shape is
preserved exactly, so `validate_v1.py`'s existing `validate_context_registry`
can check the result unchanged.

### 7. Minimal GREEN implementation
`build_pristine(destination, target_commit)`, `validate_pristine(destination)`
(calls `validate_public.run`), `classify_workspace(current_root,
pristine_root)` (compares files by content hash — reads and hashes full
bytes host-side, never by mtime/size heuristics — applied to two trees
instead of Git history; hashing is the permitted opaque host operation, the
hash and path are all that leave the function),
`migrate(current_root, destination, plan)` (copies, rejects unsafe paths,
carries scope entries using `context_registry_entries` for reading and a
two-line template for writing), `validate_candidate(destination)` (same call
as Loop 3). No new registry abstraction; the registry file remains plain
Markdown text.

### 8. Regression tests/checks
```text
python3 -m unittest discover system/tests/update
python3 system/validation/validate_public.py
python3 system/validation/validate_v1.py --mode core
python3 system/validation/validate_prompts.py
```

### 9. Privacy/access invariants
Host-side byte reads for hashing/copying are permitted and expected — that
is how correct identity comparison and preservation work at all. What must
never happen is file content reaching a `Plan`/`Preview`/`Result` field, a
diagnostic message, or a log; `test_restricted_content_never_enters_plan_or_preview_or_result`
and `test_restricted_content_never_enters_diagnostics_or_logs` enforce this
directly, while `test_host_side_hashing_of_restricted_content_is_allowed`
confirms the permitted operation is not itself broken. Migrated registry
contains only scope/target pairs, never file contents or facts (matches
`registry_contract.md`: "does not duplicate facts... into registries").

### 10. Failure cases
Pristine fails `validate_public`; non-empty destination; unsafe path
(symlink/special/traversal/outside-root); overlapping workspace conflict;
scope/target conflict; stale preview; final Personal validation failure.

### 11. Explicit out-of-scope items
No release-owned hash manifest (explicitly deferred by the design). No
migration of `system/`/`guides/` customizations (manual-resolution report
only). No live Git repository involved in this loop.

### 12. Review questions
- Does any function in `side_by_side.py` implement its own registry parser,
  or does it exclusively use `context_registry_entries` from `validate_v1`?
- Is the original tree ever opened for writing?
- Does the "kept from current installation" wording appear in the preview
  for current-only workspace files, distinct from user-created files?

### 13. Completion gate
All Loop 1–4 tests pass; `test_migrated_registry_round_trips_through_context_registry_entries`
passes, concretely proving the reuse strategy; validators pass on a clean
export.

### 14. Intended commit boundary/message
One commit. `feat(update): add ZIP side-by-side migration with scope carry-over`

---

## LOOP 5 — Assistant workflow + UX + hardening + E2E

### 1. Objective
Wire both paths into a thin, beginner-facing Assistant workflow and user
guide, complete end-to-end coverage, and verify no privacy leak across the
whole flow.

### 2. Canonical semantic owner(s)
`system/assistant/update_workflow.md` (new, thin) and `guides/user/update.md`
(new). Update logic itself stays owned by Loops 1–4; this workflow only
routes and translates.

### 3. Exact files expected to be created or modified
- `system/assistant/update_workflow.md` (new).
- `guides/user/update.md` (new).
- `system/tests/update/test_update_e2e.py` (new).
- `system/tests/update/test_update_privacy.py` (new).

### 4. Existing code/contracts reused
- `system/assistant/guided_flow_contract.md` for question/progress style.
- `system/assistant/safe_write_contract.md` for confirm/re-check/report.
- `system/diagnostics/doctor.py`'s `render(report, advanced: bool = False)`
  was inspected directly: `advanced` is a presentation flag only — when
  true it prints `finding.advanced` (raw validator error strings) with no
  reference to `ai_access` or any access contract. It is not an
  authorization mechanism, and this plan does not claim it is.
- `system/context/access_contract.md` defines effective access as
  `host_or_tool_permission + canonical_ai_access +
  trusted_adapter_authorization_when_restricted`, not the raw `ai_access`
  scalar alone — its own text states "`allow` does not mean the module
  should always be loaded." `system/context/access.py`'s `permitted(header,
  *, path, scope_path, host_read, required, personal_owner,
  private_instance)` is the existing executable form of exactly that
  formula. Safe Update reuses this function directly for the "may this
  `workspace/context/` path be named in Advanced output" decision, rather
  than re-deriving or approximating its logic from the frontmatter alone.
  It supplies honestly-sourced inputs, not assumed-true ones: `host_read`
  from the host's actual current read capability, `required=True` (the
  diagnostic is specifically asking about this path), and
  `personal_owner`/`private_instance` only from the same trusted deployment
  binding other privileged callers already use — Safe Update does not
  invent its own proof of a private single-user instance. When that binding
  is unavailable, `permitted()` returns `False` by construction for
  `restricted` content, and `allow` content is still gated on proven
  `host_read`. A path outside `permitted()`'s domain entirely — a
  directory, or a non-`workspace/context/` `workspace/` path — has no
  applicable owner to ask, so it fails closed to area/count without a
  second policy being invented for it.
- `guides/user/setup.md` / `guides/user/create_and_use_project.md` tone and
  structure for `guides/user/update.md`.

### 5. RED tests first
- `test_workflow_routes_to_git_path_for_clone` / `test_workflow_routes_to_zip_path_for_archive`.
- `test_no_write_client_states_nothing_applied_and_no_validation` — a
  simulated no-write host never calls apply/migrate and its report contains
  the literal no-write statements from `safe_write_contract.md`.
- `test_dirty_clone_guidance_mentions_local_commit_not_push` — asserts the
  beginner message tells the user to commit locally and warns against
  pushing to the public repo, and contains no repository-relative Personal
  path.
- `test_updater_never_calls_git_commit_on_dirty_state` — spy proves the
  workflow/updater issues no `git add`/`git commit` itself.
- `test_beginner_report_uses_area_and_count` — end-to-end report for a
  conflict-containing run lists counts per area, not paths, at the default
  detail level.
- `test_advanced_alone_never_exposes_a_path` — calling the report renderer
  with `advanced=True` but no proven `host_read`/deployment-binding inputs,
  against a run touching `allow`, `restricted`, and `deny` modules and
  non-context `workspace/` paths, still yields area/count only for every
  one of them; proves the Advanced flag by itself grants nothing regardless
  of `ai_access`.
- `test_permitted_allow_path_named_in_advanced_with_proven_host_read` — an
  `ai_access: allow` `workspace/context/` module is named in Advanced
  output only once real `permitted(...)` inputs (`host_read=True`,
  `required=True`, and the trusted deployment binding's actual
  `personal_owner`/`private_instance` values) are supplied, calling
  `system.context.access.permitted` itself rather than a re-derived check.
- `test_permitted_allow_path_withheld_without_proven_host_read` — the same
  `allow` module stays area/count-only when `host_read` cannot be proven,
  showing `allow` alone is not sufficient, matching
  `access_contract.md` ("`allow` does not mean the module should always be
  loaded").
- `test_permitted_restricted_path_withheld_without_deployment_binding` — an
  `ai_access: restricted` module under `workspace/context/personal/` stays
  area/count-only when Safe Update has no trusted `personal_owner`/
  `private_instance` binding to supply, even with `advanced=True` and
  `host_read=True`.
- `test_permitted_deny_path_always_withheld` — an `ai_access: deny` module
  stays area/count-only regardless of every other input.
- `test_unclassifiable_path_fails_closed_in_advanced` — a path outside
  `permitted()`'s domain (a directory, a non-`workspace/context/`
  `workspace/` path) has no applicable authorization owner to call and
  defaults to area/count-only rather than being named.
- `test_git_e2e_full_update_success` — two temp repos (current, target)
  through classify → preview → confirm → apply → validate → report,
  asserting the final tree matches the target plus preserved user files.
- `test_git_e2e_conflict_blocks_apply`.
- `test_git_e2e_recovery_after_validation_failure`.
- `test_zip_e2e_full_migration_success`.
- `test_zip_e2e_unsafe_file_rejected_end_to_end`.
- `test_zip_e2e_registry_conflict_reported_end_to_end`.
- `test_workflow_does_not_duplicate_classification_logic` — a structural
  check (e.g. `update_workflow.md` contains no restatement of the state
  table; verified by asserting the table's row labels do not appear
  duplicated outside `safe_update_design.md`/`update_contract.md`) — kept
  as a lightweight text-presence check, not a heavy prose linter.

### 6. What each RED test proves
The full user-visible slice behaves per the design end to end on both paths,
capability truthfulness holds, the dirty-state guidance is both actionable
and non-leaking, and the workflow file stays thin.

### 7. Minimal GREEN implementation
`update_workflow.md`: routes to Loop 1–4 functions by detected install type,
translates results into the beginner report shape from the design's
Capability and beginner UX section, and defers all "why blocked" detail to
the already-implemented classification/result objects. `guides/user/update.md`:
the two supported paths, what "preserved" and "conflict" mean in user terms,
and the explicit save-locally/do-not-push guidance for a dirty clone.

### 8. Regression tests/checks
```text
python3 -m unittest discover system/tests/update
python3 system/validation/validate_public.py
python3 system/validation/validate_v1.py --mode core
python3 system/validation/validate_prompts.py
git diff --check origin/main...HEAD
```

### 9. Privacy/access invariants
No Personal path, filename, or content appears in a beginner-level report.
In Advanced output, a `workspace/context/` path is named only when
`system.context.access.permitted(...)` actually returns `True` for it, fed
with honestly-sourced inputs (real `host_read`, `required=True`, the actual
trusted `personal_owner`/`private_instance` binding). Anything `permitted()`
would refuse, and anything outside its domain (a directory, a non-context
`workspace/` path), fails closed to area/count. The `advanced` flag itself
carries no authorization — see Loop 5 section 4.

### 10. Failure cases
No-write host; dirty clone; both-changed conflict; upstream delete/rename
conflict; ZIP unsafe file; ZIP registry conflict; validation failure with
recovery; validation failure with concurrent-change incomplete recovery.

### 11. Explicit out-of-scope items
No new UI/GUI. No auto-repair. No package/release catalog. No background/
autonomous update triggering — the workflow only runs on explicit user
request, per the product contract's V1 non-goals.

### 12. Review questions
- Does `update_workflow.md` route only, with zero restated classification or
  apply logic?
- Does every beginner-level report in the E2E tests avoid leaking a Personal
  path?
- Do the Git and ZIP E2E tests each cover at least one success and one
  blocked/conflict path?

### 13. Completion gate
All Loop 1–5 tests pass; full validator suite passes on a clean export;
`git diff --check` clean.

### 14. Intended commit boundary/message
One commit. `feat(update): add beginner Assistant workflow and E2E coverage`

## Ownership note

The design's Ownership section names `update_contract.md`, `git_update.py`,
and `side_by_side.py` as the `system/update/` owners. `target.py` (Loop 1) is
a small addition: the design states target resolution is "one thin ...
step, shared by both paths." Without a shared module, that resolution would
have to be duplicated inside both `git_update.py` and `side_by_side.py` —
the exact duplicate-ownership outcome the charter forbids. `target.py`
stays governed by `update_contract.md`'s prose; it does not introduce a
competing contract owner.

## Deferred naming decisions

The exact `TargetSnapshot`/`Plan`/`Preview`/`ApplyResult` dataclass field
names should be finalized during each loop's GREEN step rather than guessed
here.

## Non-goals carried from the design

No package manager, installer framework, release catalog, cache, file
inventory, or migration engine. No release-owned hash manifest (explicitly
deferred, not part of V1). No second source-access contract — target
resolution in Loop 1 is additive to, not a replacement for,
`system/adapters/source_access_contract.md`, which governs factual-context
reads, not update-target resolution.
