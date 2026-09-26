# Beginner setup workflow

## Purpose

Bring a new user from an available Personal-SoT repository to one useful Assistant task without requiring knowledge of Git, YAML, schemas, prompts, or repository paths.

## Flow

```text
[1 Repository]
→ [2 Language]
→ [3 AI client]
→ [4 Optional personal context]
→ [5 System check]
→ [6 Meet the Assistant]
→ [7 First useful task]
```

Follow `system/assistant/guided_flow_contract.md`: explain the short path, show compact progress, reuse supplied answers, and ask one material question at a time.

## 1. Repository

Confirm that the client can read the repository root and resolve `workspace/adapters/runtime_entrypoint.md`. If not, explain the smallest client-appropriate way to open, attach, or connect the repository. Do not claim setup is connected until the entrypoint is actually readable.

Downloading an archive and cloning are acquisition choices, not different product semantics. Recommend the simplest supported choice for the user's client and experience.

## 2. Language

Use the language requested by the user or the current conversation language. If neither is clear, ask which language to use and offer relevant examples plus `I don't know — recommend one`.

Conversation language is runtime state and requires no canonical write. If the user asks to persist response-language or presentation defaults, propose a profile change through the safe-write contract. Do not store language preference as a personal fact merely for setup.

## 3. AI client and capability

Identify the actual client and available repository capabilities.

```text
authorized local agent
→ may read, preview, confirm, write, and run local validation

web or read-only client
→ may guide and preview; must not claim local write or validation
```

Client choice changes only capability wiring. It does not change onboarding questions, ownership, proposal semantics, or validation requirements.

## 4. Optional personal context

Explain that the user can skip personal onboarding and start with a project. Ask only what would make the first intended task materially better.

Classify durable candidate facts through `system/context/module_catalog.md`. Create only necessary canonical owners under `workspace/context/personal/`, with explicit `ai_access`, and register the `personal` scope when its first module is created. Never create empty modules or collect sensitive details by default.

Every material personal-context write follows `system/assistant/safe_write_contract.md`. A no-write client returns the same proposal and capability limitation without mutation.

## 5. System check

On a capable local host, execute `system/diagnostics/doctor_contract.md`. Its implementation reuses the canonical validators and produces the beginner report.

```text
python3 system/diagnostics/doctor.py
```

Translate results into beginner language: ready, what failed, which area is affected, and the smallest next action. Report commands and actual results; do not convert a failure into setup success.

On a host that cannot run them, state:

```text
local system check was not run here
```

Then provide the smallest local-agent handoff guidance.

## 6. Meet the Assistant

Introduce the six categories from `system/assistant/assistant_contract.md` in the selected language. Recommend one category based on the user's stated goal rather than presenting an unexplained feature list.

## 7. First useful task

Offer a concrete natural-language next request. When the user wants a project, route to `system/assistant/project_workflow.md`. Otherwise route to the smallest existing capability and preserve reuse-before-create.

Show expert directives only after completing or recommending the beginner path.

## Acceptance

A compliant setup reaches an honest connected/not-connected state, uses the selected language, distinguishes real host capability, avoids unnecessary personal data, runs or truthfully defers the local system check, and hands the user to one useful client-neutral Assistant workflow.
