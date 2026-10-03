# Prompt Explorer and Builder Implementation Plan

> **Status:** Historical implementation record (all tasks completed). File
> paths and prompt identities below (`sot/explore_prompts`, `sot/build_prompt`)
> reflect the naming scheme in effect at implementation time and are
> superseded by the runtime user-naming refactor; see
> `system/prompts/prompt_contract.md` for current canonical identities
> (`sot/prompt/list`, `sot/prompt/create`).

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Deliver deterministic prompt discovery and a beginner-safe reuse/create/edit flow with real local validation and truthful preview-only behavior.

**Architecture:** Add one dependency-free, on-demand Explorer under `system/prompts/` that reads canonical frontmatter and delegates candidate validity to `validate_prompts.py`. Add one Builder module that owns reuse ordering and preview-bound local create/edit application; client-neutral Markdown contracts own conversation semantics, while thin `sot` prompts route the Assistant to them.

**Tech Stack:** Python 3 standard library, Markdown/YAML-like frontmatter already parsed by repository validators, `unittest`.

**Spec:** `guides/developer/assistant/prompt_explorer_builder_design.md`

## Global Constraints

- `workspace/prompts/` paths and prompt frontmatter remain the only prompt discovery source of truth.
- Add no catalog, index, cache, database, vector store, embeddings, alias table, or fuzzy identity resolution.
- Explorer is read-only; bodies load only for bounded validation or a selected operation.
- Validation semantics remain owned by `system/validation/validate_prompts.py`; Explorer and Builder call its public per-file interface.
- Ranking uses only current canonical evidence and the exact deterministic match vector/tie-break defined by the spec.
- Builder order is exact prompt → parameterized prompt → composition → same-owner edit → create.
- Prompt-to-prompt runtime include/inheritance remains unsupported.
- Durable Personal facts stay out of reusable prompts; factual context resolves independently.
- Every material write uses complete preview, explicit confirmation, state re-check, authorized write, real validation, and truthful reporting.
- Web/read-only clients receive the same questions and preview but never claim write or validation success.
- Adapters expose capability only; they do not own Explorer, Builder, validation, or safe-write semantics.
- Use only the standard library and the current three-root repository layout.

## Review Focus

- A prompt-tree symlink escaping the repository must never expose or recommend the external file (Task 1 test).
- Malformed or unclosed frontmatter must be unavailable without scanning the rest of the prompt body (Task 1 test).
- Unicode intent tokens and shuffled filesystem enumeration must produce the same canonical ordering (Task 1 test).
- A create target appearing or an edit target changing after preview must invalidate confirmation (Task 4 tests).
- A structurally valid write followed by a repository-wide validation failure must be reported as failed, never successful (Task 4 test).

---

### Task 1: Validator-backed deterministic Prompt Explorer

**Files:**
- Create: `system/prompts/explorer.py`
- Create: `system/prompts/explorer_contract.md`
- Modify: `system/prompts/readme.md`
- Modify: `system/validation/validate_prompts.py`
- Create: `system/tests/prompts/test_prompt_explorer.py`

**Interfaces:**
- Produces: `validate_prompts.read_manifest(path: Path) -> tuple[set[str], dict[str, list[str]], dict[str, str]]`, which stops at the closing frontmatter delimiter.
- Produces: `validate_prompts.validate_path(root: Path, path: Path, canonical: bool = True) -> list[str]`, the sole per-file validity interface.
- Produces: immutable `PromptQuery`, `PromptMatch`, and `SearchReport` dataclasses.
- Produces: `search(root: Path, query: PromptQuery) -> SearchReport` and a JSON-emitting CLI `main() -> int`.

- [ ] **Step 1: Write the failing Explorer tests**

Add tests named:

```text
test_exact_identity_uses_current_canonical_path
test_exact_filters_use_and_and_list_subset_semantics
test_ranking_and_identity_tie_break_are_deterministic
test_unicode_tokens_are_deterministic
test_status_rules_hide_draft_and_deprecated_by_default
test_invalid_or_unresolved_prompt_is_not_recommended
test_owned_assets_do_not_filter_or_rank
test_unmatched_prompt_body_is_not_validated
test_validation_stops_at_twenty_candidates_and_reports_incomplete
test_does_not_create_catalog_or_change_repository_bytes
test_skips_symlink_that_escapes_prompt_root
test_unclosed_frontmatter_is_unavailable_without_body_scan
```

Use `unittest.mock.patch` around `validate_prompts.validate_path` to record exactly which ranked candidates require full validation; do not add dependency injection solely for tests.

- [ ] **Step 2: Run the Explorer test module and verify RED**

Run: `python3 -m unittest system.tests.prompts.test_prompt_explorer`

Expected: FAIL because `system.prompts.explorer` and the public validator interfaces do not exist.

- [ ] **Step 3: Expose the minimum validator-owned interfaces**

Make `read_manifest()` reuse the validator's current manifest parser while reading only through the closing delimiter. Make `validate_path()` initialize the existing registry IDs and call the same validation implementation used by full-repository `run()`; do not duplicate any rule.

- [ ] **Step 4: Implement the Explorer and contract**

`PromptQuery` contains `text`, `identity`, `path_prefix`, `status`, tuple-valued exact filters, optional scalar tone/depth, and `limit=5`. Enforce limits 1–10, validate no more than 20 ranked candidates, sort the spec's match vector descending and canonical identity ascending, and return metadata-only `PromptMatch` values.

The CLI accepts the same filters, calls `search()`, and emits only structured metadata and safe availability counts as JSON. It never prints prompt bodies.

- [ ] **Step 5: Run Explorer tests and relevant validators for GREEN**

Run:

```bash
python3 -m unittest system.tests.prompts.test_prompt_explorer
python3 system/validation/validate_v1.py --mode core
python3 system/validation/validate_prompts.py
python3 system/validation/validate_public.py
```

Expected: all commands exit 0; Explorer tests report no failures.

- [ ] **Step 6: Review and commit Loop 1**

Review for validation-rule duplication, filesystem-order dependence, symlink escape, body over-reading, generated state, and leaked prompt content.

```bash
git add system/prompts/explorer.py system/prompts/explorer_contract.md system/prompts/readme.md system/validation/validate_prompts.py system/tests/prompts/test_prompt_explorer.py
git commit -m "feat(prompts): add deterministic prompt explorer"
```

### Task 2: Beginner Explorer workflow and entrypoint

**Files:**
- Create: `system/assistant/prompt_explorer_workflow.md`
- Modify: `system/assistant/assistant_contract.md`
- Modify: `system/assistant/readme.md`
- Create: `workspace/prompts/sot/explore_prompts.md`
- Modify: `workspace/prompts/sot/assistant.md`
- Create: `system/tests/assistant/prompt_explorer_cases.md`
- Create: `guides/user/find_and_use_prompts.md`
- Modify: `guides/user/readme.md`

**Interfaces:**
- Consumes: `search(root, PromptQuery) -> SearchReport` from Task 1.
- Produces: one client-neutral workflow for natural-language discovery and beginner presentation.
- Produces: thin `sot/explore_prompts` invocation with optional use-case input; no copied ranking or validation logic.

- [ ] **Step 1: Add scenario acceptance cases**

Record non-executable Markdown acceptance cases for selected-language guidance,
one adaptive question, recommendation evidence, simple usage, optional Advanced
identity/directive, draft/deprecated warnings, unavailable candidate safety, no
invented identity, and preview-only honesty. These cases guide semantic review;
do not report them as RED → GREEN executable tests.

- [ ] **Step 2: Add the minimum workflow and Assistant route**

The workflow translates intent into a `PromptQuery`, invokes Explorer when available, explains only returned evidence, and presents `recommended use / why / inputs / limitation / natural-language usage`. It keeps paths and `@do:prompt:...` in Advanced.

- [ ] **Step 3: Add the thin prompt entrypoint and beginner guide**

The prompt references the workflow and supplies only user intent. The guide teaches natural-language discovery first and expert syntax second. Do not change adapter semantics.

- [ ] **Step 4: Validate and commit Loop 2**

Run:

```bash
python3 -m unittest system.tests.prompts.test_prompt_explorer
python3 system/validation/validate_prompts.py
python3 system/validation/validate_public.py
```

Expected: all commands exit 0.

```bash
git add system/assistant workspace/prompts/sot guides/user system/tests/assistant/prompt_explorer_cases.md
git commit -m "feat(assistant): add beginner prompt discovery flow"
```

### Task 3: Prompt Builder contract and reuse planner

**Files:**
- Create: `system/prompts/builder.py`
- Create: `system/assistant/prompt_builder_workflow.md`
- Modify: `system/assistant/assistant_contract.md`
- Modify: `system/assistant/readme.md`
- Create: `workspace/prompts/sot/build_prompt.md`
- Create: `system/tests/prompts/test_prompt_builder.py`
- Create: `system/tests/assistant/prompt_builder_cases.md`

**Interfaces:**
- Consumes: Explorer results from Task 1 and `system/assistant/safe_write_contract.md`.
- Produces: immutable `ReuseAssessment` with `exact_identity`, `parameterized_identity`, `composition`, `edit_identity`, and `same_semantic_owner`.
- Produces: `choose_action(assessment: ReuseAssessment) -> tuple[str, str | None]`, returning exactly one of `reuse_exact`, `reuse_parameterized`, `compose`, `edit`, or `create`.

- [ ] **Step 1: Write failing executable reuse-order tests and scenario acceptance cases**

In `test_prompt_builder.py`, test exact reuse, parameterized reuse, valid
composition, same-owner edit, similarity without ownership choosing create, and
create only when every earlier rung is absent. Separately record non-executable
Markdown scenario acceptance cases for durable-fact separation, adaptive
questions, and forbidden prompt-to-prompt include/inheritance; do not report the
Markdown cases as RED → GREEN.

- [ ] **Step 2: Run Builder tests and verify RED**

Run: `python3 -m unittest system.tests.prompts.test_prompt_builder`

Expected: FAIL because `system.prompts.builder` does not exist.

- [ ] **Step 3: Implement the minimum reuse planner and workflow**

`choose_action()` is a fixed first-match decision in canonical order. It permits `edit` only when `edit_identity` is present and `same_semantic_owner` is true. Runtime control composition stays outside prompt frontmatter.

The workflow owns guided classification and routes any write to Task 4; the thin prompt entrypoint only references this workflow.

- [ ] **Step 4: Run tests and validators for GREEN, then commit Loop 3**

Run:

```bash
python3 -m unittest system.tests.prompts.test_prompt_builder
python3 system/validation/validate_prompts.py
python3 system/validation/validate_public.py
```

Expected: all commands exit 0.

```bash
git add system/prompts/builder.py system/assistant workspace/prompts/sot/build_prompt.md system/tests/prompts/test_prompt_builder.py system/tests/assistant/prompt_builder_cases.md
git commit -m "feat(prompts): add reuse first prompt builder"
```

### Task 4: Safe local create and edit

**Files:**
- Modify: `system/prompts/builder.py`
- Modify: `system/validation/validate_prompts.py`
- Modify: `system/tests/prompts/test_prompt_builder.py`

**Interfaces:**
- Produces: `validate_prompts.validate_source(root: Path, path: Path, source: str, canonical: bool = True) -> list[str]`, sharing all rules with `validate_path()` and `run()`.
- Produces: immutable `PromptProposal` containing operation, identity, repository-relative target, before digest, exact before content when editing, complete proposed content, unified diff, confirmation digest, capability, and preflight errors.
- Produces: `preview_change(root: Path, operation: str, identity: str, content: str, *, same_semantic_owner: bool, fact_safe: bool, write_capable: bool) -> PromptProposal`.
- Produces: immutable `ApplyResult` with `write_applied`, `validation_ran`, `validation_passed`, `validation_errors`, `success`, and the affected repository-relative path; `apply_change(root: Path, proposal: PromptProposal, confirmation_digest: str) -> ApplyResult`.

- [ ] **Step 1: Add failing safe-write tests**

Add tests named:

```text
test_create_preview_contains_complete_diff_and_absent_target
test_edit_requires_same_semantic_owner
test_similarity_never_authorizes_overwrite
test_unknown_prompt_include_field_fails_preflight
test_secret_or_invalid_content_fails_preflight
test_unclassified_durable_fact_candidate_cannot_reach_preview
test_preview_only_client_cannot_apply_or_claim_validation
test_wrong_confirmation_digest_cannot_apply
test_stale_edit_requires_new_preview
test_occupied_create_target_requires_new_preview
test_successful_local_create_runs_real_prompt_validation
test_successful_local_create_runs_all_relevant_validators
test_write_applied_but_repository_validation_failed_is_explicit_and_recoverable
```

- [ ] **Step 2: Run safe-write tests and verify RED**

Run: `python3 -m unittest system.tests.prompts.test_prompt_builder`

Expected: new tests fail because proposal/apply interfaces do not exist.

- [ ] **Step 3: Refactor validator input without changing rules**

Move the existing per-file prompt-rule body behind `validate_source()`; make
`validate_path()` read once and delegate, and keep `run()` behavior/output
stable. Prompt preflight calls this validator-owned interface. Do not duplicate
prompt, secret, or public-distribution rules in Builder, and do not parse
validator stdout.

- [ ] **Step 4: Implement preview and apply**

Resolve only lowercase_snake_case identities beneath `workspace/prompts/`.
Require the Assistant workflow to classify proposed reusable content as
fact-safe before preview; uncertainty stops the write path and routes durable
truth to parameters or independently resolved context. Use
`difflib.unified_diff` for the complete preview and `hashlib.sha256` for
confirmation/current-state binding. Preflight the proposed source through the
validator-owned `validate_source()` interface.

On apply, verify capability, confirmation digest, and target existence/digest;
write one prompt file; then call the programmatic owners directly:

```text
validate_prompts.run(root)
validate_v1.run(root, "core")
validate_public.run(root)
```

Do not reimplement or parse the output of any validator. Namespace each returned
error in `validation_errors`. Set `write_applied=True` immediately after the
filesystem mutation, set `validation_ran=True` only after all three owners were
invoked, and derive `validation_passed` and `success` separately. If validation
fails after mutation, keep the exact proposal diff/before content available for
recovery, report the changed path explicitly, perform no silent repair or
rollback, and require a new proposal for any semantic repair.

- [ ] **Step 5: Run tests and validators for GREEN, then commit Loop 4**

Run:

```bash
python3 -m unittest system.tests.prompts.test_prompt_builder
python3 -m unittest system.tests.prompts.test_prompt_explorer
python3 system/validation/validate_v1.py --mode core
python3 system/validation/validate_prompts.py
python3 system/validation/validate_public.py
```

Expected: all commands exit 0.

```bash
git add system/prompts/builder.py system/validation/validate_prompts.py system/tests/prompts/test_prompt_builder.py
git commit -m "feat(prompts): apply confirmed prompt changes safely"
```

### Task 5: End-to-end beginner scenario and hardening

**Files:**
- Create: `system/tests/prompts/test_prompt_explorer_builder_e2e.py`
- Modify: `system/tests/assistant/prompt_builder_cases.md`
- Create: `guides/user/build_a_prompt.md`
- Modify: `guides/user/find_and_use_prompts.md`
- Modify: `guides/user/readme.md`
- Modify: `README.md`

**Interfaces:**
- Consumes: Explorer, Builder, safe-write, and canonical prompt validation interfaces from Tasks 1–4.
- Produces: one executable end-to-end proof and beginner documentation; no new runtime abstraction.

- [ ] **Step 1: Write the failing end-to-end test**

In one temporary three-root repository, prove: an exact existing prompt is reused; a parameterized prompt is preferred; an unmatched use case reaches create; the same proposal is preview-only with no write when capability is unavailable; a confirmed local create writes and passes the real validator; Explorer then discovers that new canonical identity; a confirmed edit succeeds; and a changed file makes the old edit proposal stale.

- [ ] **Step 2: Run the end-to-end test and verify RED**

Run: `python3 -m unittest system.tests.prompts.test_prompt_explorer_builder_e2e`

Expected: FAIL until the complete flow and fixtures use the final interfaces correctly.

- [ ] **Step 3: Complete only the missing integration and beginner docs**

Fix interface integration exposed by the test without adding a coordinator, registry, or cache. Document natural-language find/reuse/build/create/edit usage, preview/confirmation, local validation, web preview-only behavior, and optional Advanced directives.

- [ ] **Step 4: Run the full repository verification**

Run:

```bash
python3 -m unittest system.tests.validation.test_validate_v1
python3 -m unittest system.tests.validation.test_validate_public
python3 -m unittest system.tests.assistant.test_project_vertical_slice
python3 -m unittest system.tests.diagnostics.test_doctor
python3 -m unittest system.tests.prompts.test_prompt_explorer
python3 -m unittest system.tests.prompts.test_prompt_builder
python3 -m unittest system.tests.prompts.test_prompt_explorer_builder_e2e
python3 system/validation/validate_v1.py --mode core
python3 system/validation/validate_prompts.py
python3 system/validation/validate_public.py
git diff --check main...HEAD
```

Expected: every test reports 0 failures, every validator reports PASSED, and diff check is empty.

- [ ] **Step 5: Review and commit Loop 5**

Review the complete branch for semantic duplication, secondary/stale state, prompt-to-prompt coupling, unbounded body loading, public/access leakage, client-specific core logic, stale preview risk, and unnecessary indirection.

```bash
git add system/tests/prompts/test_prompt_explorer_builder_e2e.py system/tests/assistant/prompt_builder_cases.md guides/user README.md
git commit -m "test(prompts): cover beginner explorer builder flow"
```

- [ ] **Step 6: Request final code review and deliver through PR**

Address Critical/Important findings, rerun Step 4 on the final HEAD, push `feat_prompts_explorer_builder`, create a PR to `main`, and merge only after required review and validation succeed.
