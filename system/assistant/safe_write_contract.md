# Assistant safe-write contract

## Purpose

Define the client-neutral boundary for creating or changing canonical SoT state.

Git/validation routing is owned by `system/governance/change_policy.md`.

## Required pipeline

```text
understand intent
→ resolve scope
→ classify semantics and access
→ resolve change class / branch mode / validation level
→ inspect current owners
→ detect duplication, conflict and stale evidence
→ build proposal
→ preview
→ explicit confirmation
→ re-check current state and host permission
→ apply/persist the confirmed patch using the host's real write transaction
→ validate when policy requires and capability allows
→ report
```

No material canonical Personal mutation may skip preview and confirmation.

## Proposal

A proposal binds confirmation to one concrete change set. It includes:

- target logical scope and semantic owners;
- files and registry entries to create or modify;
- concise before/after or complete new content;
- excluded or deferred candidate facts;
- access metadata;
- resolved change class;
- branch mode and validation level from the change policy;
- a clear statement of actual host write/command/push capability.

Preview paths are supporting detail. Explain the user-visible meaning first.

## Confirmation

Confirmation authorizes only the displayed proposal. A changed scope, owner, file set, access state, current revision, or materially changed content requires a new preview.

Confirmation does not override host permissions, sandbox limits, access contracts, policies, or the resolved change policy.

## Revalidation and concurrency

Immediately before writing, re-read every affected current owner and registry entry and re-check the selected repository/ref when the host exposes revision evidence.

If relevant state changed since preview, stop, reconcile, and show a revised proposal.

Apply the confirmed files and registry entries as one coherent patch when the host supports it. Never overwrite unrelated concurrent changes.

## Apply, validation, and persistence

Write only confirmed semantic owners. Preserve explicit `ai_access`, naming, registry, prompt/profile, and access contracts.

Validation follows `system/governance/change_policy.md`:

- `none` — do not run Python tests/validators merely by habit;
- `hygiene_only` — review diff/paths/privacy and use `git diff --check` when available;
- `targeted_if_available` — run the named targeted validator when command capability exists; otherwise report it unavailable;
- `full_relevant` — the owning engineered workflow must pass its required suite before integration.

For direct private-main context writes, persist the confirmed change with a commit and push when the host exposes those capabilities. A successful remote-provider commit to private `main` already represents the remote persistence step.

Host transaction order may differ: a remote provider may create the commit as the write itself, while a local client may edit, validate when applicable, then commit/push. Do not invent a sequencing capability the host does not expose.

For `system_change`, candidate-branch commits may exist before validation, but integration into the canonical target branch still requires the owning engineered workflow's required checks.

A failed required validator means the operation is not reported as validated/successful. Report the failure truthfully and route repair through a new bounded proposal unless the correction is purely mechanical and cannot change meaning.

## No-write hosts

A host without write capability returns the proposal and the smallest practical apply guidance.

It must say that nothing was written. For validation, report the policy truthfully:

- if validation is not required, say so;
- if validation would be applicable but command capability is unavailable, say it was not run.

Never fabricate a commit, push, validator result, or file mutation.

## Report

Report only supported facts:

```text
resolved_scope
change_class
created_or_updated_owners
deferred_items
persistence_result
validation_requirement_and_result
capability_limitations
next_beginner_request
optional_expert_usage
```

Keep routine Personal/project updates beginner-simple. Branches, validators, and commit mechanics should be hidden unless they matter to the result or failed.

## Acceptance

A compliant write is preview-bound when Personal state changes, explicitly confirmed, current-state checked, authorized, minimal, conflict-aware, routed through the change policy, validated only to the required level, persisted only with real capability, and truthfully reported.
