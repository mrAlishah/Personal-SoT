# Assistant safe-write contract

## Purpose

Define the client-neutral boundary for creating or changing canonical SoT state.

## Required pipeline

```text
understand intent
→ resolve scope
→ classify semantics and access through `system/governance/change_classification.md`
→ inspect current owners
→ detect duplication, conflict and stale evidence
→ build proposal
→ preview
→ explicit confirmation
→ re-check current state and host permission
→ write the confirmed patch
→ validate
→ report
```

No material canonical mutation may skip preview and confirmation.

## Proposal

A proposal binds confirmation to one concrete change set. It includes:

- target logical scope and semantic owners;
- files and registry entries to create or modify;
- concise before/after or complete new content;
- excluded or deferred candidate facts;
- access metadata;
- the resolved change class from `system/governance/change_classification.md`;
- validation/checks required by that class and any stricter active-repository governance;
- a clear statement of actual host write capability and, separately, local-command/validator capability when relevant.

Preview paths are supporting detail. Explain the user-visible meaning first.

## Confirmation

Confirmation authorizes only the displayed proposal. A changed scope, owner, file set, access state, or materially changed content requires a new preview.

Confirmation does not override host permissions, sandbox limits, access contracts, policies, validation gates, or Git governance.

## Revalidation and concurrency

Immediately before writing, re-read every affected current owner and registry entry. If relevant state changed since preview, stop, reconcile, and show a revised proposal.

Apply the confirmed files and registry entry as one coherent patch when the host supports it. If the host cannot avoid a partial write, it must either use a recoverable operation or stop before mutation. Never overwrite unrelated concurrent changes.

## Apply and validation

Write only the confirmed semantic owners. Preserve explicit `ai_access`, naming, registry, prompt/profile, and access contracts.

Resolve validation rigor from `system/governance/change_classification.md` plus any stricter rule owned by the active repository. Do not automatically escalate an ordinary private context update or docs/help-only change to the full Python test suite.

Write capability and local-command capability are independent. A host with real authorized repository write capability may complete a confirmed class whose required checks do not need unavailable local commands. Conversely, when the resolved class requires validators/tests the host cannot run, do not claim the candidate is validated or accepted merely because the write succeeded.

A failed required validator means the operation is not reported as successful. Report the failure and the affected files; repair requires a new bounded proposal unless the correction is purely mechanical and cannot change meaning.

## No-write hosts

A host without write capability returns the proposal and the smallest practical apply/validation guidance. It must explicitly say:

```text
nothing was written
validation was not run here
```

It must not fabricate file links, commits, validator output, or success state.

## Report

Report only supported facts:

```text
resolved_scope
created_or_updated_owners
deferred_items
validation_command_and_result
capability_limitations
next_beginner_request
optional_expert_usage
```

## Acceptance

A compliant write is preview-bound, explicitly confirmed, current-state checked, authorized, minimal, conflict-aware, validated, and truthfully reported.
