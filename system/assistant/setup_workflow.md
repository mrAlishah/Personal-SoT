# Beginner setup workflow

## Purpose

Bring a user from no installation, a partial installation, or an existing Personal-SoT installation to a healthy private `sot` and one useful Assistant task without requiring knowledge of Git, YAML, schemas, prompts, repository paths, or migration internals.

The same workflow is intentionally re-runnable. It owns initial setup guidance and setup-state recovery; it does not duplicate the Safe Update engine or Doctor.

## Expert entry action

```text
@do:setup
```

`@do:setup` is the exact expert entry point into this workflow. Natural-language setup requests remain equivalent and beginner-first.

Ordinary text after the action may describe the desired setup outcome or current problem. The action itself grants no repository, command, write, or authorization capability.

## Source terminology

Use the source roles from `system/adapters/source_access_contract.md`:

```text
sot
→ the user's private Personal-SoT installation/source binding

sot public
→ the upstream reusable public product
→ mrAlishah/Personal-SoT
```

On first installation, `sot` is the private destination being created. The source used to obtain reusable product files is `sot public`. Never treat the public repository as the user's private canonical SoT and never push Personal facts or private state to it.

## Re-runnable state routing

Every invocation first inspects what the host can actually prove. Do not assume that setup is fresh merely because the user invoked `@do:setup`.

```text
no private sot yet
→ initial install/configuration

private sot exists but setup is incomplete
→ resume from the smallest missing/broken step

private sot is healthy but reusable product is stale
→ route update work to system/assistant/update_workflow.md

private sot is healthy but configuration can be materially improved
→ recommend the smallest evidence-backed improvement
→ preview/confirm any material write

private sot is healthy and current
→ report ready
→ offer one useful next task
```

A setup rerun must preserve already-valid configuration and Personal state. Do not recreate, reset, overwrite, or duplicate healthy owners merely to make the workflow look fresh.

## Flow

The visible beginner flow remains simple:

```text
[1 Repository / installation state]
→ [2 Language]
→ [3 AI client and capability]
→ [4 Optional personal context]
→ [5 System check]
→ [6 Update or repair if needed]
→ [7 Meet the Assistant]
→ [8 First useful task]
```

Follow `system/assistant/guided_flow_contract.md`: explain the short path in ELI5-style plain language, show compact progress, reuse supplied or provable answers, and ask one material question at a time.

ELI5-style setup guidance is a workflow communication requirement, not an implicit `@fmt:eli5` presentation override.

## 1. Repository / installation state

Resolve the current source and actual host capability before deciding what setup means.

### Initial installation

When the user is starting from a local clone of `sot public`, the simplest supported mechanical path is the repository-owned one-click launcher:

```text
Linux/macOS → ./install.sh
Windows     → install.bat
```

Both route to `system/install/installer.py` and `system/install/install_contract.md`. The installer may create a private GitHub topology or a validated no-Git copy in a local Google Drive synced/mounted folder, runs Doctor, and ends by handing the user back to `@do:sot` then `@do:setup`.

Do not duplicate installer mechanics inside this conversational workflow. If the host can run the launcher, recommend it. If it cannot, continue with the equivalent guided steps below.

When the user has no private `sot` yet:

1. identify an accessible trusted `sot public` source;
2. recommend the simplest supported acquisition for the client: clone or archive;
3. create or select a private destination for the future `sot`;
4. when the user wants Git-backed remote storage, guide them to a private repository they control;
5. keep the public product source separate from the private destination;
6. verify that the resulting private root can resolve `workspace/adapters/runtime_entrypoint.md`.

For a Git-based installation, the recommended topology is conceptually:

```text
sot public
   ↓ reusable product/update source
private local sot
   ↓
optional private remote owned by the user
```

A common Git remote layout is:

```text
origin   → user's private repository
upstream → mrAlishah/Personal-SoT
```

This layout is a recommendation, not a universal requirement. Do not fabricate a GitHub account, repository name, remote URL, or permission. Creating a private remote requires real host/provider capability or explicit user action.

### Existing installation

When a private `sot` already exists, verify its root and entrypoint before changing anything. Inspect only the minimum evidence needed to determine whether setup is complete, stale, or broken.

Downloading an archive and cloning are acquisition choices, not different product semantics. Update behavior for each install type belongs to `system/assistant/update_workflow.md` and `system/update/update_contract.md`.

## 2. Language

Use the language requested by the user or the current conversation language. If neither is clear, ask which language to use and offer relevant examples plus `I don't know — recommend one`.

Conversation language is runtime state and requires no canonical write. If the user asks to persist response-language or presentation defaults, propose a profile change through the safe-write contract. Do not store language preference as a personal fact merely for setup.

## 3. AI client and capability

Identify the actual client and available repository capabilities.

```text
authorized local agent
→ may read, preview, confirm, write, and run local validation

web or read-only client
→ may guide and preview when source access exists
→ must not claim local write or validation
```

Client choice changes only capability wiring. It does not change onboarding questions, ownership, proposal semantics, source roles, or validation requirements.

## 4. Optional personal context

Explain that the user can skip personal onboarding and start with a project. Ask only what would make the first intended task materially better.

Classify durable candidate facts through `system/context/module_catalog.md`. Create only necessary canonical owners under `workspace/context/personal/`, with explicit `ai_access`, and register the `personal` scope when its first module is created. Never create empty modules or collect sensitive details by default.

Every material personal-context write follows `system/assistant/safe_write_contract.md`. A no-write client returns the same proposal and capability limitation without mutation.

## 5. System check

Route the system check through `system/diagnostics/doctor_contract.md`.

On a capable local host, run Doctor with the active repository-owned adapter and the host's actual write capability. Do not infer either from prompt text.

```text
python3 system/diagnostics/doctor.py \
  --adapter <active_repository_adapter> \
  --write-capability <available_or_unavailable>
```

Translate results into beginner language: ready, warning/error, affected area, and smallest next action. Report commands and actual results; do not convert a failed check into setup success.

On a host that cannot run local commands, state plainly:

```text
local system check was not run here
```

Then provide the smallest local-agent handoff guidance.

## 6. Update or repair if needed

If the installation is valid but stale relative to `sot public`, route to `system/assistant/update_workflow.md`. Do not perform ad-hoc merges or copy public files manually as a substitute for the canonical update workflow.

If Doctor or current evidence shows a real setup/runtime problem, route repair through `system/assistant/fix_workflow.md`. Do not silently repair inside setup.

If the issue is only usage confusion, explain it directly and continue setup without creating a repair proposal.

## 7. Meet the Assistant

Introduce the six categories from `system/assistant/assistant_contract.md` in the selected language. Recommend one category based on the user's stated goal rather than presenting an unexplained feature list.

## 8. First useful task

Offer a concrete natural-language next request. When the user wants a project, route to `system/assistant/project_workflow.md`. Otherwise route to the smallest existing capability and preserve reuse-before-create.

Show expert directives only after completing or recommending the beginner path. Useful expert actions include:

```text
@do:sot
@do:setup
@do:doctor
@do:fix
@do:help
@do:assist
```

## Write boundary

Setup is not blanket mutation authority.

Every material canonical write follows:

```text
inspect current owner
→ classify
→ preview exact change
→ explicit confirmation
→ current-state re-check
→ authorized write
→ relevant validation
→ truthful report
```

A setup rerun must not overwrite valid Personal state just because newer reusable public product files exist.

## Acceptance

A compliant setup:

- works for first installation and later reruns;
- uses `sot` for the user's private installation and `sot public` for the public upstream product;
- never silently binds the private role to the public or a legacy repository;
- explains setup in concise beginner/ELI5-style language;
- resumes rather than restarts partial setup;
- preserves healthy private state;
- routes updates to the canonical update workflow;
- routes real repair to the canonical fix workflow;
- reaches an honest connected/not-connected and ready/not-ready state;
- uses the selected language;
- distinguishes real host capability;
- avoids unnecessary personal data;
- runs or truthfully defers Doctor;
- hands the user to one useful client-neutral Assistant workflow.
