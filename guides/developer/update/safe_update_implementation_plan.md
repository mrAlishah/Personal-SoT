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
  pinning, shared by both paths. No `__init__.py`: confirmed no sibling
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
  main` for the same exact repository and ref.
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
- `test_rejects_non_canonical_repository` — resolver is asked to resolve a
  different `owner/repo` string; `target.resolve()` raises/returns a
  rejection before any resolver call, proving the repository identity is
  fixed in code, not caller-supplied.
- `test_rejects_ref_override` — a caller-supplied ref/branch/PR/commit
  argument is refused; only `main` is accepted.
- `test_capability_unavailable_fails_closed` — resolver raises "no
  capability"; `target.resolve()` returns a `capability_unavailable`-classed
  failure, not a silent fallback to a different source.
- `test_no_fabricated_target_on_partial_response` — resolver returns a
  malformed/partial snapshot (missing sha); `target.resolve()` fails closed
  rather than accepting a partial commit id.

### 6. What each RED test proves
That target authority is fixed to `mrAlishah/Personal-SoT:main` in code (not
configuration or prompt input), that no alternate remote/fork/PR/commit can
become authority, and that resolution failure is fail-closed and classified.

### 7. Minimal GREEN implementation
`target.py`: one function, `resolve(runner=None) -> TargetSnapshot | Failure`,
plus a frozen `TargetSnapshot(commit, ref, resolved_via)` dataclass, using
`system.connectors.source.Failure` for its rejection reasons rather than a
new literal type. No caller-supplied repository or
ref parameter exists in the public function signature — this is what makes
rejection of alternates structural rather than a runtime check.
`update_contract.md`: prose stating the shared target-resolution rule,
failure classes, and that both paths call the same `target.resolve()`.

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
state. No mutation.

### 2. Canonical semantic owner(s)
`system/update/git_update.py` (new), classification and preview functions
only. `update_contract.md` gets the classification-vocabulary section filled
in with the exact state names from the design table.

### 3. Exact files expected to be created or modified
- `system/update/git_update.py` (new) — `classify(root) -> Plan`,
  `preview(plan) -> Preview` (digest-bound), plus the dirty/untracked check.
- `system/tests/update/test_git_classification.py` (new).
- `system/update/update_contract.md` (extend from Loop 1).

### 4. Existing code/contracts reused
- `target.py` from Loop 1 for `T`.
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
  result's message contains no repository-relative Personal path, only a
  count/area, matching the design's non-leaking requirement.
- `test_already_current_when_c_equals_t`.
- `test_no_op_when_t_is_ancestor_of_c`.
- `test_normal_update_when_diverged_with_valid_merge_base`.
- `test_fails_closed_on_unrelated_lineage` — no merge base → fail-closed
  classification, not a downgrade or forced merge.
- `test_preview_digest_binds_c_t_b_and_plan`.
- `test_stale_preview_rejected_when_c_changes` — re-resolving after a
  simulated local commit invalidates the old digest.

### 6. What each RED test proves
Every state-table row and lineage rule from the design is exercised against
real Git tree identity, the dirty-state guidance never leaks paths, and the
preview cannot be replayed against changed state.

### 7. Minimal GREEN implementation
`classify(root, target_commit)` returns a `Plan` (frozen dataclass: tuples of
classified paths per state + a `blocked` reason or `None`). `preview(plan)`
returns a `Preview` with a `digest` (sha256 over `C`, `T`, `B`, and a
canonical serialization of the plan) and a beginner-safe summary (counts per
state, not full path lists, for anything under `workspace/context/`; shipped
non-context paths may be listed since they carry no personal-fact risk).

### 8. Regression tests/checks
```text
python3 -m unittest system.tests.update.test_target_resolution system.tests.update.test_git_classification
python3 system/validation/validate_public.py
python3 system/validation/validate_v1.py --mode core
```

### 9. Privacy/access invariants
Beginner-facing preview summary never lists a `workspace/context/` path by
name; Advanced detail may, matching the Doctor precedent ("raw validator
diagnostics only in an optional Advanced section").

### 10. Failure cases
No merge base; dirty index; dirty worktree; untracked Personal file; stale
digest reuse; `T` resolution failure propagated from Loop 1.

### 11. Explicit out-of-scope items
No apply, no mutation, no recovery, no ZIP path, no confirmation storage
beyond returning the digest for the caller to hold.

### 12. Review questions
- Does classification ever perform a text/semantic merge for a both-changed
  path? (Must not.)
- Does the blocked-dirty message leak any path under
  `workspace/context/personal` or `workspace/context/organizations`?
- Is the "ahead/divergent" lineage split from the design (no-op /
  normal-update / fail-closed) implemented as three distinct outcomes?

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
- Real temporary Git repositories, as in Loop 2, plus a real disabled-hook
  Git invocation (`git -c core.hooksPath=/dev/null` or equivalent verified
  empirically) to prove hooks do not fire — a mocked subprocess cannot prove
  this.

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
- `test_url_rewriting_ignored` — a repo/global config with
  `url.<other>.insteadOf` pointing at the canonical URL; apply still reads
  from the direct canonical address, proven by the fetched commit matching
  the resolver's target regardless of the rewrite.
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
with a disabled-hook/disabled-filter Git invocation, checks clean state
immediately before mutation, advances the ref last with an old-value check,
and on any failure attempts recovery only for paths it verifies are still in
the updater-written state.

### 8. Regression tests/checks
```text
python3 -m unittest discover system/tests/update
python3 system/validation/validate_public.py
python3 system/validation/validate_v1.py --mode core
python3 system/validation/validate_prompts.py
```

### 9. Privacy/access invariants
Apply never reads restricted/denied content to decide classification (Loop 2
already establishes this at the tree-identity level, not content level).
Failure reports contain no file content, only paths/state.

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
- `test_comparison_does_not_read_restricted_content` — spy proves file
  bytes of a `deny`/`restricted` module are never opened for comparison
  beyond identity (hash/mtime/existence), only copied opaquely.

### 6. What each RED test proves
Every side-by-side bullet in the design, the registry carry-over/conflict
rule from finding B-1, and that the reused parser's fenced-block shape is
preserved exactly, so `validate_v1.py`'s existing `validate_context_registry`
can check the result unchanged.

### 7. Minimal GREEN implementation
`build_pristine(destination, target_commit)`, `validate_pristine(destination)`
(calls `validate_public.run`), `classify_workspace(current_root,
pristine_root)` (reuses the same per-file identity comparison shape as
Loop 2's classification, applied to two trees instead of Git history),
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
Comparison and copy are byte/hash-identity operations, never content
interpretation; `test_comparison_does_not_read_restricted_content` enforces
this directly. Migrated registry contains only scope/target pairs, never
file contents or facts (matches `registry_contract.md`: "does not duplicate
facts... into registries").

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
- `system/diagnostics/doctor_contract.md`'s existing Advanced-section pattern
  ("raw validator diagnostics only in an optional Advanced section") reused
  verbatim for update diagnostics, not reinvented.
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
- `test_advanced_detail_gated_by_access` — a Personal path appears in
  Advanced output only when the existing access contract would allow
  showing that path; a `restricted`/`deny` module's path is withheld even in
  Advanced.
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
No Personal path, filename, or content appears in a beginner-level report;
Advanced detail is gated by the existing access contract, matching Doctor's
established rule exactly.

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
