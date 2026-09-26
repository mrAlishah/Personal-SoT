# Beginner Personalization Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add deterministic beginner-first discovery and composition across Personalization lanes, with safe Profile-only canonical create/edit.

**Architecture:** Read current Profiles, registry-backed presentation/control targets, and the canonical behavior catalog on demand. Keep intent translation in the client-neutral Assistant workflow, keep validation in `validate_v1.py`, and implement a narrow Profile Builder without adding another inventory or a generic component mega-builder.

**Tech Stack:** Python standard library, Markdown contracts/guides, `unittest`, existing repository validators.

**Spec:** `guides/developer/assistant/personalization_design.md`

## Global Constraints

- Profile is the only Personalization lane that may create or edit canonical state.
- Format, tone, depth, registered control, and behavior are existing-only.
- Discovery reads canonical owners on demand and creates no registry, index, cache, alias map, or inventory.
- Control identities and values come only from the registry and canonical control metadata.
- Natural-language interpretation produces invocation-local query/classification, never canonical aliases.
- Direct composition and existing Profiles outrank Profile creation.
- Profiles remain compact fact-free composition manifests.
- Every Profile write follows preview, confirmation, stale-state recheck, authorized write, real validation, and truthful reporting.
- Web/no-write clients remain preview-only.
- Markdown scenarios are acceptance specifications, not RED → GREEN evidence.
- Repository-owned names and commits follow current SoT Git conventions.

## Review Focus

- A registry target changes or disappears between discovery/preview and apply: stop or mark unavailable without stale overwrite.
- A Profile or canonical root is replaced by a symlink: do not read or write outside its semantic owner.
- A multilingual intent is classified to a non-existent identity: report no match rather than inventing an alias or capability.
- A proposed Profile contains prose facts, context paths, secrets, copied module instructions, or unsupported fields: preflight must reject it.
- A no-write client or post-write validator failure: report mutation and validation state separately and truthfully.

---

### Task 1: Deterministic canonical discovery

**Files:**
- Create: `system/personalization/explorer.py`
- Create: `system/personalization/explorer_contract.md`
- Create: `system/personalization/readme.md`
- Modify: `system/validation/validate_v1.py`
- Test: `system/tests/personalization/test_explorer.py`

**Interfaces:**
- Produces: `read_profile_manifest(source: str) -> ProfileManifest`, `validate_profile_source(root: Path, path: Path, source: str) -> list[str]`, `CapabilityQuery`, `CapabilityMatch`, `SearchReport`, and `search(root: Path, query: CapabilityQuery) -> SearchReport`.
- Consumes: canonical Profile paths, `switch_registry_entries`, registry target metadata, and `system/behavior/module_catalog.md`.

- [ ] Write executable tests for exact per-lane discovery, deterministic tie-breaks, bounded/lazy target reads, missing targets, invalid Profile manifests, external symlinks, no filesystem mutation, and classified multi-lane inputs for short depth, formal tone, comparison-table format, learning/step behavior, and deep professional research.
- [ ] Run `python3 -m unittest system.tests.personalization.test_explorer` and confirm RED because the module/interfaces do not exist.
- [ ] Extract the minimum validator-owned Profile source interface without changing batch validation semantics.
- [ ] Implement on-demand discovery using only canonical owners and deterministic evidence; do not persist state.
- [ ] Run the focused suite and existing `test_validate_v1`; confirm GREEN.
- [ ] Commit with `feat(personalization): add canonical capability discovery`.

### Task 2: Beginner Advisor and Composer

**Files:**
- Create: `system/assistant/personalization_workflow.md`
- Create: `workspace/prompts/sot/personalize.md`
- Create: `system/tests/assistant/personalization_cases.md`
- Modify: `system/assistant/assistant_contract.md`
- Modify: `system/assistant/readme.md`
- Modify: `system/tests/profile/runtime_control_profile_cases.md`
- Test: `system/tests/personalization/test_advisor.py`

**Interfaces:**
- Consumes: Task 1 discovery results and exact canonical component identities/values.
- Produces: `PersonalizationIntent`, `CompositionRecommendation`, and `recommend(root: Path, intent: PersonalizationIntent) -> CompositionRecommendation`.

- [ ] Write executable tests proving direct `tone=formal + depth=short` composition creates no Profile, comparison-table selection stays format-owned, step-by-step learning composes an existing learning Profile with registered control values, and deep professional research reuses `research`.
- [ ] Run `python3 -m unittest system.tests.personalization.test_advisor` and confirm RED for missing recommendation behavior.
- [ ] Implement the smallest evidence-backed composer; it consumes classified exact identities and never maintains natural-language aliases.
- [ ] Add the multilingual beginner workflow, one-question guidance, progress, examples, recommendations, and optional Advanced directives.
- [ ] Update the stale control scenario values from boolean examples to canonical `on/off/auto`; label Markdown cases as non-executable acceptance specifications.
- [ ] Run focused Explorer/Advisor tests and confirm GREEN.
- [ ] Commit with `feat(assistant): add beginner personalization flow`.

### Task 3: Reuse-first Profile Builder

**Files:**
- Create: `system/personalization/profile_builder.py`
- Create: `system/assistant/profile_builder_workflow.md`
- Create: `system/tests/assistant/profile_builder_cases.md`
- Modify: `system/assistant/personalization_workflow.md`
- Modify: `workspace/prompts/sot/personalize.md`
- Test: `system/tests/personalization/test_profile_builder.py`

**Interfaces:**
- Consumes: Task 1 Profile manifests/validation and Task 2 `CompositionRecommendation`.
- Produces: `ProfileAssessment`, `choose_profile_action()`, and a Profile-only preview proposal.

- [ ] Write executable tests for exact Profile reuse, direct composition before creation, reusable-combination creation eligibility, same-owner edit, similarity without ownership, fact/body/context-path rejection, unsupported lane mutation, and complete diff preview.
- [ ] Run the focused test and confirm RED for the absent Builder.
- [ ] Implement only Profile reuse/create/edit decisions and preview; do not add format/tone/depth/control/behavior writers.
- [ ] Keep Profile validation entirely validator-owned and reject non-manifest body content.
- [ ] Run focused tests and regression suites; confirm GREEN.
- [ ] Commit with `feat(personalization): add reuse first profile builder`.

### Task 4: Confirmed Profile safe write

**Files:**
- Modify: `system/personalization/profile_builder.py`
- Modify: `system/validation/validate_v1.py`
- Modify: `system/assistant/profile_builder_workflow.md`
- Test: `system/tests/personalization/test_profile_builder.py`

**Interfaces:**
- Consumes: Task 3 Profile proposal.
- Produces: `ApplyResult` with `write_applied`, `validation_ran`, `validation_passed`, `validation_errors`, and `success`; `apply_change(root, proposal, confirmation_digest)`.

- [ ] Write executable tests for preview-only clients, mismatched confirmation, tampered proposal, stale create/edit, referenced component/registry changes, symlink ancestors, atomic write failure, successful create/edit, and explicit post-write validation failure state.
- [ ] Run focused tests and confirm RED for missing apply behavior.
- [ ] Implement Profile-only confirmation binding and current-state checks. Extract only a demonstrably component-neutral primitive; otherwise keep the Builder narrow and do not refactor Prompt semantics.
- [ ] After a write, call programmatic `validate_v1.run(root, "core")`, `validate_prompts.run(root)`, and `validate_public.run(root)` without stdout parsing or copied rules.
- [ ] Run focused tests and all affected existing suites; confirm GREEN.
- [ ] Commit with `feat(personalization): apply confirmed profile changes safely`.

### Task 5: End-to-end hardening and beginner documentation

**Files:**
- Create: `system/tests/personalization/test_personalization_e2e.py`
- Create: `guides/user/customize_responses.md`
- Modify: `guides/user/readme.md`
- Modify: `readme.md`
- Modify: `system/tests/assistant/personalization_cases.md`
- Modify: `system/tests/assistant/profile_builder_cases.md`

**Interfaces:**
- Consumes: all Tasks 1-4 public interfaces.
- Produces: one executable beginner journey covering discover → compose/reuse → preview-only or confirmed Profile write → validation → rediscovery/edit → stale protection.

- [ ] Write an executable end-to-end test. If it passes on first execution because Tasks 1-4 already provide the entire flow, record it as acceptance evidence rather than claiming RED → GREEN.
- [ ] Add explicitly non-executable semantic cases for multilingual guidance, optional Advanced syntax, and honest no-write behavior.
- [ ] Add beginner documentation that starts with natural-language examples and hides schemas/paths until Advanced.
- [ ] Run all validation, Doctor, project, Prompt, and Personalization suites plus `validate_v1 --mode core`, `validate_prompts`, and `validate_public`.
- [ ] Review the diff for semantic-lane mixing, duplicate inventories/values, copied component semantics, stale-state risk, fact/secret leakage, and client coupling.
- [ ] Commit with `test(personalization): cover beginner customization flow`.

## Finalization

- [ ] Build a whole-branch review package from the merge base.
- [ ] Request one fresh-context whole-branch review focused on the spec and Review Focus cases.
- [ ] Reproduce and fix Critical/Important findings in one TDD pass; ledger Minor findings without scope expansion.
- [ ] Re-run all tests and validators, inspect the final diff, push the branch, open a PR, attach it, and merge only after the evidence is green.
