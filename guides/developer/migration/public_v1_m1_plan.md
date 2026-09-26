# Public Personal-SoT V1 M1 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Bootstrap a clean, beginner-oriented public repository from the validated generic Core without leaking Personal data.

**Architecture:** Import the exact generic Core snapshot, then add one dependency-free public-distribution gate and replace only the product entrypoints needed for a beginner. Keep the three canonical roots and leave all Personal-only capabilities for later classified slices.

**Tech Stack:** Markdown, Git, Python 3 standard library.

**Spec:** `guides/developer/migration/public_v1_design.md`

## Global Constraints

- Source Core is exactly `d66dec7a94c7f79b4a5340e8c0d8c76bf5c548cb`.
- Exactly three primary roots: `workspace/`, `system/`, `guides/`; `readme.md` may remain at root.
- No real Personal facts, sensitive data, private project state, user-specific paths, private adapters, credentials, secrets, or Personal Git history.
- Branch names use `<type>_<scope>_<goal>` and repository-owned names use `lowercase_snake_case`.
- Commit messages use `<type>(<scope>): <imperative summary>` with canonical types.
- No new dependency.
- Validation claims require actual passing output.

## Review Focus

- A real macOS or Linux home path must fail public validation.
- A forbidden source repository/ref identifier must fail public validation.
- A likely credential assignment must fail public validation.
- Safe placeholder values must not fail public validation.
- Fake developer examples must remain clearly non-runtime and pass the repository validators.

---

### Task 1: Phase 0 record

**Files:**
- Create: `guides/developer/migration/public_v1_design.md`
- Create: `guides/developer/migration/public_v1_inventory.md`
- Create: `guides/developer/migration/public_v1_m1_plan.md`

**Interfaces:**
- Consumes: resolved source deployment, Core tree, and Personal/Core diff.
- Produces: authoritative M1 allow/deny map and exact Core SHA for Task 2.

- [x] Verify the three records contain no placeholder decisions and name the resolved refs/SHAs.
- [x] Commit as `docs(migration): record public v1 migration baseline`.

### Task 2: Generic Core baseline

**Files:**
- Create: the classified Core paths under `system/`, `workspace/`, and `guides/`.

**Interfaces:**
- Consumes: exact Core SHA from Task 1.
- Produces: existing `validate_v1.py` and `validate_prompts.py` commands for later tasks.

- [x] Import the exact Core tree without source history.
- [x] Run `python3 system/validation/validate_v1.py --mode core` and confirm it passes.
- [x] Run `python3 system/validation/validate_prompts.py` and confirm it passes.
- [x] Confirm no path from the inventory's `DO_NOT_MIGRATE` rows exists.
- [x] Commit as `feat(core): migrate generic v1.2 foundation`.

### Task 3: Public distribution gate

**Files:**
- Create: `system/tests/validation/test_validate_public.py`
- Create: `system/validation/validate_public.py`
- Modify: `system/validation/readme.md`

**Interfaces:**
- Consumes: repository root and text files.
- Produces: `validate_public.run(root) -> list[str]` and CLI exit status 0/1.

- [x] Write tests for forbidden Personal identifiers, home paths, credential assignments, and safe placeholders.
- [x] Run the test file and verify the expected failures occur because `validate_public` is missing.
- [x] Implement the smallest standard-library scanner that satisfies the tests.
- [x] Run the test file and full Core validators.
- [x] Commit as `test(validation): add public distribution gate`.

### Task 4: Beginner foundation

**Files:**
- Modify: `readme.md`
- Modify: `guides/readme.md`
- Modify: `guides/user/readme.md`
- Modify: `workspace/context/readme.md`
- Create: `system/governance/development_conventions.md`

**Interfaces:**
- Consumes: canonical Core contracts and public validation command.
- Produces: beginner navigation and a data-free Personal workspace entrypoint.

- [x] Replace framework-first navigation with the beginner journey and an explicit not-yet-implemented boundary.
- [x] Add the minimal starter workspace instructions without empty fact modules.
- [x] Record the generalized development convention in its system-owned destination.
- [x] Run all three validators plus the public validator.
- [x] Inspect the complete diff against the empty destination and the source inventory.
- [x] Commit as `docs(user): add beginner foundation`.
