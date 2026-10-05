# Fix workflow

## Purpose

Provide one safe repair path for Personal-SoT when the user reports a problem, Doctor reports a finding, or setup/update exposes a real defect.

This workflow is not an auto-repair engine. It first decides whether the user needs guidance or whether a current defect is actually proven. Real mutation remains governed by the existing semantic owner, safe-write contract, host capability, and repository governance.

## Expert entry action

```text
@do:fix
```

Ordinary text after the action is an optional problem description.

By default, `@do:fix` targets the user's private `sot`, as defined by `system/adapters/source_access_contract.md`.

An explicit request to fix `sot public` targets the upstream public product repository only when the current host/source binding actually provides authorized access to that public development repository. Public-product repair follows `system/governance/branch_flow.md`; it is never treated as an ordinary private-installation write.

## Core rule

```text
reported problem
→ understand the symptom
→ inspect current evidence
→ classify: usage confusion | current defect | unresolved
→ guide OR diagnose/repair
```

Do not mutate first and diagnose later.

A prior Doctor result, old chat conclusion, stale error message, or user belief that something is broken is evidence to inspect, not proof that the same defect still exists.

## 1. Understand the problem

Use the user's current language and explain the next step in concise ELI5-style wording.

Reuse information already present in the current accessible conversation and source. Ask one material clarification only when the ambiguity can change the repair target, authority, privacy exposure, or implementation path.

Do not require the user to know file paths, validators, adapters, Git topology, or internal contracts.

## 2. Distinguish guidance from repair

### Usage confusion

If current evidence shows the system is healthy and the problem is how to use a feature, command, client, or workflow:

```text
explain the cause
→ show the correct action/command
→ no canonical write
```

Do not manufacture a repair proposal merely because the user used the word "error".

### Suspected installation/runtime defect

When the symptom could reflect setup, runtime, adapter, prompt, profile, context, or reference failure, run or route through `system/diagnostics/doctor_contract.md` when local-command capability exists.

When Doctor cannot run on the current host, state that limitation and provide the smallest handoff needed to obtain current diagnostic evidence.

### Non-Doctor product or repository defect

When the issue is outside Doctor's diagnostic coverage, inspect the smallest current canonical owner, code, test, or repository evidence that can prove or disprove the defect. Repository evidence outranks stale conversation claims.

## 3. Select the repair owner

For a proven defect, identify the smallest semantic owner that can correct the root cause.

Examples:

```text
adapter/source binding problem → adapter/source-access owner
invalid context/profile/prompt → its canonical owner + authoritative validator
setup wiring problem → setup/runtime owner
update problem → system/update owners
reusable product defect → sot public development owner
```

Do not duplicate semantics in a new wrapper merely to make the repair convenient.

## 4. Source boundary

The default repair target is private `sot`.

Never mutate `sot public` merely because a private installation reveals a reusable product bug.

If the user explicitly requests a `sot public` fix:

1. verify that the current target is the public product repository, not the user's private installation;
2. use the current public `develop` branch as the base according to `system/governance/branch_flow.md`;
3. create a short-lived governed branch;
4. make the smallest coherent reusable fix;
5. run the public required checks;
6. review public/private leakage and semantic duplication;
7. use the public PR/release flow.

Personal facts, private project state, private adapters/deployment configuration, secrets, and Personal Git history must never be copied into `sot public`.

If source binding is ambiguous, fail closed. Do not choose between private and public repositories by recency, name similarity, or convenience.

## 5. Repair preview

Every material repair proposal must show enough information for informed confirmation:

```text
observed problem
current evidence
root cause or bounded working diagnosis
target source: sot | sot public
semantic owner / affected files
exact material change
what is intentionally excluded
validation/checks that will run
capability limitations
```

Use beginner wording first. Technical detail may follow when useful.

A recommendation or preview is not a write.

## 6. Confirmation and apply

All material writes follow `system/assistant/safe_write_contract.md`:

```text
preview
→ explicit confirmation bound to that preview
→ re-read/current-state check
→ authorized apply
→ relevant validation
→ truthful result
```

If current state changes after preview, invalidate the old confirmation and generate a new preview.

A host without real write capability cannot apply a repair. User confirmation never creates host permission.

## 7. Validation

Use the validator or test owned by the affected domain.

After a Doctor-covered repair on a capable local host, rerun Doctor and report the new state.

For a material `sot public` change, run the canonical public branch-flow checks:

```text
python3 -B -m unittest $(find system/tests -name 'test_*.py' | sed 's#/#.#g;s#\.py$##')
python3 -B system/validation/validate_public.py
python3 -B system/validation/validate_v1.py --mode core
python3 -B system/validation/validate_prompts.py
git diff --check <base>...HEAD
```

Never report repaired/ready/passed unless the required operation and validation actually succeeded.

## 8. Report

Distinguish clearly:

```text
guided_only
diagnosed
previewed
applied
validation_passed
validation_failed
blocked_by_capability
```

When repair cannot be completed, state the exact blocking condition and the smallest next action.

## Acceptance

A compliant fix workflow:

- treats user-reported errors and old Doctor findings as evidence, not automatic permission to mutate;
- guides usage confusion without unnecessary writes;
- diagnoses current installation/runtime problems before repair;
- defaults to the private `sot`;
- changes `sot public` only when explicitly targeted and governed as public development work;
- preserves public/private and authorization boundaries;
- proposes the smallest root-cause repair;
- previews every material write;
- requires exact confirmation and current-state re-check;
- validates with the canonical owner;
- reruns Doctor after Doctor-covered repairs when possible;
- never claims a fix or pass that did not actually occur.
