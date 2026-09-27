# Runtime Naming Normalization Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make `@do:sot` and hierarchical `g.*` shipped profile identities the exact Public Personal-SoT V1 runtime names.

**Architecture:** A small routing primitive owns executable naming grammar. Existing runtime/profile contracts keep their semantic ownership, while validators and Profile Builder reuse the primitive instead of duplicating regular expressions.

**Tech Stack:** Python standard library, Markdown contracts, `unittest`.

**Spec:** `guides/developer/runtime_naming_design.md`

## Global Constraints

- Preserve the three-root repository layout.
- Keep natural-language beginner UX primary and expert directives optional.
- Do not add an alias registry or duplicate legacy profile files.
- Do not relax the repository-wide lowercase-snake-case validator.
- Keep `@do:initialSoT` as the only temporary compatibility literal.
- Do not copy or reclassify private v1.2 `gn_*` profiles.

## Review Focus

- A bootstrap directive with parameters, body text, or a companion directive must not execute.
- Case variants and unapproved short aliases must not normalize silently.
- A built-in profile with an empty, uppercase, or underscored segment must fail.
- Custom lowercase-snake-case profiles must remain valid.
- User Profile Builder writes must not create or edit reserved `g.*` identities.

---

### Task 1: Naming contract and executable grammar

**Files:**
- Create: `guides/developer/runtime_naming_design.md`
- Create: `guides/developer/runtime_naming_plan.md`
- Create: `system/routing/runtime_naming.py`
- Create: `system/tests/routing/test_runtime_naming.py`

**Interfaces:**
- Produces: `classify_bootstrap_invocation(text)`, `profile_identity_kind(identity)`, and `is_profile_identity(identity)`.

- [ ] Write executable bootstrap/profile grammar tests.
- [ ] Run them and observe import/behavior failures.
- [ ] Implement the minimum routing primitive.
- [ ] Run the focused tests and all baseline validators.
- [ ] Commit `docs(runtime): define canonical runtime naming`.

### Task 2: Canonical `@do:sot` migration

**Files:**
- Modify: `system/adapters/*.md`
- Modify: `system/routing/switch_syntax.md`
- Modify: `system/retrieval/query_planning.md`
- Modify: affected routing/adapter/retrieval scenario cases
- Test: `system/tests/routing/test_runtime_naming.py`

**Interfaces:**
- Consumes: `classify_bootstrap_invocation(text)` from Task 1.

- [ ] Add failing cases for exclusivity, legacy diagnostics, and rejected aliases.
- [ ] Confirm RED.
- [ ] Migrate canonical runtime references to `@do:sot` and retain one bounded legacy section.
- [ ] Confirm focused GREEN and run relevant validators/tests.
- [ ] Commit `refactor(runtime): canonicalize sot bootstrap action`.

### Task 3: Hierarchical shipped profile migration

**Files:**
- Rename: six shipped files under `workspace/profiles/` per the approved mapping.
- Modify: profile/prompt validators and Personalization Profile Builder.
- Modify: every maintained profile reference in prompts, adapters, docs, and tests.
- Test: validation, personalization, prompt, and runtime naming executable tests.

**Interfaces:**
- Consumes: `profile_identity_kind(identity)` and `is_profile_identity(identity)` from Task 1.

- [ ] Add failing validator and Profile Builder cases for `g.*` grammar/reservation.
- [ ] Confirm RED.
- [ ] Rename shipped profiles and reuse the shared grammar from all affected consumers.
- [ ] Migrate maintained references atomically without compatibility files.
- [ ] Confirm focused GREEN and run relevant validators/tests.
- [ ] Commit `refactor(profiles): namespace shipped profile identities`.

### Task 4: PR1 hardening and review

**Files:**
- Modify only files required by review findings.

**Interfaces:**
- Consumes: the complete naming migration from Tasks 1-3.

- [ ] Run every executable test file and the three strongest validators.
- [ ] Verify old command/profile identities remain only in bounded migration compatibility evidence.
- [ ] Review semantic ownership, duplication, leakage, and client coupling.
- [ ] Fix Critical/Important findings with RED -> GREEN evidence.
- [ ] Commit any required hardening, push the branch, and create the PR.
