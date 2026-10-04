# Doctor contract

## Purpose

Doctor is the read-only Diagnose workflow for explaining whether Personal-SoT is ready and what a beginner should do next.

## Authority boundary

`system/diagnostics/doctor.py` orchestrates existing canonical validators and presents their results. It does not reimplement validation owned by those validators.

Doctor-specific checks are limited to:

```text
runtime entrypoint and referenced-contract resolution
deployment/bootstrap connectivity
selected AI client configuration and declared host capability
```

Validator results remain authoritative for workspace, context, project, prompt, profile, access, reference, and public-distribution validity.

Installation/readiness diagnosis is distinct from public-distribution certification. Normal Doctor runs the inferred Core/Personal validator and Prompt validator, but does not require an installed Personal workspace to pass the public-distribution validator. Public-distribution checking is an explicit opt-in Doctor scope; when requested, `validate_public.py` remains authoritative for that finding. Public release acceptance remains owned by the canonical branch/release workflow, including its full unit-test, Core, Prompt, and Public gates; Doctor does not replace that workflow.

## Execution

On a capable local host, run Doctor from the repository root and supply the active repository-owned adapter plus the actual write capability. Add `--public-distribution` only when the strict public-distribution check is explicitly requested. The adapter owns its client label, discovery surface, and entrypoint wiring; Doctor does not maintain a client registry. The Assistant translates the report into the user's selected language without changing finding status, blocking state, or meaning.

A host that cannot run local commands may explain the workflow and capability limitation, but must state that Doctor was not run there.

## Beginner report

Lead with a compact status list:

```text
✓ ready or valid
⚠ usable with a limitation
✗ needs attention
```

For every warning or error, explain:

- what is wrong;
- why it matters to the user;
- whether it blocks safe use;
- the exact next repair action;
- a recommendation or example when useful.

Do not require the beginner to understand paths, YAML, registries, or Git. Show repository-relative paths and raw validator diagnostics only in an optional `Advanced` section.

## Privacy

Never display secret values or canonical content. Do not independently inspect or quote `restricted` or `deny` content beyond invoking its authoritative validator. A finding may identify the affected area and, in authorized Advanced output, the minimum repository-relative location needed for repair.

## Repair boundary

Doctor never mutates files, configuration, contracts, registries, or canonical data.

When repair requires a write:

```text
diagnosis
→ bounded repair proposal
→ preview
→ explicit confirmation
→ authorized write
→ relevant validation
→ report
```

The write phase is a separate operation governed by `system/assistant/safe_write_contract.md`. A diagnosis is not confirmation and a failed check is not permission to repair.

## Acceptance

A compliant Doctor is read-only, client-neutral, validator-backed, capability-honest, safe for sensitive contexts, useful without internal knowledge, and precise about blocking status and the next action.
