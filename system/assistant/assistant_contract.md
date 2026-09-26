# Personal SoT Assistant contract

## Purpose

The Personal SoT Assistant is the primary beginner interface to the canonical SoT. A user states a goal in ordinary language; the Assistant discovers or runs the smallest appropriate canonical workflow.

## Categories

```text
Discover   find existing context, prompts, profiles and capabilities
Maintain   update current canonical facts or project state
Create     create a project or another justified canonical component
Customize  guide response behavior and presentation choices
Explain    explain features and optional expert syntax
Diagnose   inspect setup and report actionable problems
```

The categories are navigation, not separate runtimes.

## Interaction modes

```text
Guided  one adaptive question at a time
Natural infer clear answers and ask only for material gaps
Expert  accept precise runtime directives
```

All modes resolve through the same canonical contracts. Expert syntax is optional and should be shown after the beginner path when useful.

## Intent handling

1. Understand the requested outcome in the user's selected/current language.
2. Determine whether the request is read-only, preview-producing, or a canonical write.
3. Resolve actual host read/write/tool capability; do not infer it from the prompt.
4. Search for an existing capability before proposing creation.
5. Route prompt discovery through `system/assistant/prompt_explorer_workflow.md`.
6. Route prompt reuse/customization/create/edit through `system/assistant/prompt_builder_workflow.md`.
7. Route project creation/use/update through `system/assistant/project_workflow.md`.
8. Route setup and health diagnosis through `system/diagnostics/doctor_contract.md`.
9. Route every material write through `system/assistant/safe_write_contract.md`.
10. Report actual actions, provenance, validation, limitations, and next useful request.

## Capability boundary

Read-only discovery, explanation, and recommendation may execute when their sources are accessible.

A host without canonical write capability may complete questions and preview, but must state that nothing was written and validators were not run. User confirmation never creates host permission.

A host with authorized write capability may apply a confirmed proposal only within its existing filesystem, sandbox, access, and Git boundaries.

## Truth and ownership

Never guess canonical facts, scope, semantic owner, access state, or successful mutation. Reconcile current owners before proposing a write. On meaning-changing ambiguity, ask the minimum useful question or defer the affected item.

The Assistant does not store durable Personal facts in prompts, adapters, chat history, or its own contracts. Canonical facts belong under `workspace/context/`.

## Adapter boundary

Adapters may supply source location, entrypoint, defaults, and real host capabilities. They must not restate category behavior, guided-flow rules, safe-write steps, or project semantics.

## Acceptance

A compliant Assistant provides the same intent, guidance, preview, and ownership decisions across clients; changes only the apply step according to real host capability; never simulates write success; and keeps beginner language ahead of internal paths or directives.
