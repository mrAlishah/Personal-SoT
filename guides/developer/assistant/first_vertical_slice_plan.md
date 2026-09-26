# Personal SoT Assistant First Vertical Slice Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Deliver a client-neutral, beginner-first project create/use/update workflow with truthful local-write and web-preview behavior.

**Architecture:** Canonical Assistant semantics live in four `system/assistant/` contracts. Thin local and web adapters resolve those contracts, while three reusable prompts expose the natural-language flows. Local agents perform authorized writes directly; no helper/CLI is introduced.

**Tech Stack:** Markdown, Git, Python 3 standard library tests and existing validators.

**Spec:** `guides/developer/assistant/first_vertical_slice_design.md`

## Global Constraints

- Beginner natural language is the primary interface; expert directives are optional and taught after the workflow.
- Assistant and workflow semantics remain client-neutral under `system/assistant/`.
- Adapters declare capabilities and locate the entrypoint; they do not duplicate canonical logic.
- Hosts without write capability provide preview and guidance and never claim mutation or successful validation they did not run.
- Every material canonical write requires preview, explicit confirmation, current-state recheck, authorized write, validation, and truthful report.
- Create only the minimum semantically necessary context modules.
- No standalone helper/CLI, connector, GUI, MCP server, or cloud service.
- Repository naming and Git conventions remain canonical.

## Review Focus

- Confirmation cannot grant missing host write permission.
- A stale proposal must be rechecked before write.
- Project creation cannot leave files without a matching registered scope.
- Web adapters cannot claim that writes or validators ran.
- Current-state updates must not become append-only history or silently change objectives/constraints.

---

### Task 1: Client-neutral Assistant contracts

**Files:**
- Create: `system/assistant/assistant_contract.md`
- Create: `system/assistant/guided_flow_contract.md`
- Create: `system/assistant/safe_write_contract.md`
- Create: `system/assistant/project_workflow.md`
- Create: `system/assistant/readme.md`
- Create: `system/tests/assistant/first_vertical_slice_cases.md`

**Interfaces:**
- Produces: the single semantic source used by every adapter and Assistant prompt.

- [x] Define capability negotiation, multilingual guided behavior, preview/confirmation, project creation, use, and current-state update.
- [x] Add scenario cases for local write, web preview-only, ambiguity, stale preview, and validation failure.
- [x] Run existing validators and commit as `feat(assistant): define client neutral project workflow`.

### Task 2: Thin runtime and client adapters

**Files:**
- Create: `workspace/adapters/runtime_entrypoint.md`
- Create: `workspace/adapters/public_bootstrap.md`
- Create: `workspace/adapters/chatgpt_project_instructions.md`
- Create: `workspace/adapters/claude_web_project_instructions.md`
- Create: `workspace/adapters/AGENTS.md`
- Create: `workspace/adapters/CLAUDE.md`
- Create: `AGENTS.md`
- Create: `CLAUDE.md`
- Modify: `workspace/adapters/readme.md`

**Interfaces:**
- Consumes: Task 1 contracts.
- Produces: repo-relative local write adapters and web preview-only adapters.

- [x] Add thin wrappers that reference the runtime entrypoint and declare actual host capability.
- [x] Verify adapters do not restate project/safe-write steps.
- [x] Run validators and commit as `feat(adapters): wire assistant capability boundaries`.

### Task 3: Assistant entry prompts

**Files:**
- Create: `workspace/prompts/sot/assistant.md`
- Create: `workspace/prompts/sot/create_project.md`
- Create: `workspace/prompts/sot/update_project.md`

**Interfaces:**
- Consumes: Task 1 contracts and Task 2 runtime entrypoint.
- Produces: prompt identities `sot/assistant`, `sot/create_project`, and `sot/update_project`.

- [x] Add minimal fact-free prompts that invoke canonical contracts instead of copying them.
- [x] Run prompt and repository validators and commit as `feat(prompts): add assistant project flows`.

### Task 4: Runnable vertical-slice validation

**Files:**
- Create: `system/tests/assistant/test_project_vertical_slice.py`

**Interfaces:**
- Consumes: existing `validate_v1.run(root, mode)` and the canonical project shape.
- Produces: a runnable create/register/validate/update/validate check.

- [x] Write the integration test first and verify it fails before its complete valid fixture exists.
- [x] Complete the minimum fake fixture behavior inside the test.
- [x] Run all Python tests and validators.
- [x] Commit as `test(assistant): cover project vertical slice`.

### Task 5: Beginner usage path

**Files:**
- Create: `guides/user/create_and_use_project.md`
- Modify: `guides/user/readme.md`
- Modify: `readme.md`

**Interfaces:**
- Consumes: the completed Assistant prompts and adapter capabilities.
- Produces: an honest beginner path for local write and web preview-only use.

- [x] Document natural-language create/use/update examples before optional expert syntax.
- [x] State current client capability boundaries without implementation jargon.
- [x] Run the complete validation suite, inspect the branch diff, and commit as `docs(user): explain first project workflow`.
