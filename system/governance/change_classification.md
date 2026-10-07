# Change classification

## Purpose

Define one canonical classification for Personal-SoT changes so branch rigor and validation effort scale with risk instead of treating every canonical edit like product development.

This contract owns change classification and the default rigor for private Personal-SoT workspaces. Repository-specific governance may be stricter for development of the public product itself, but individual workflows must not invent a competing category system.

## Core rule

```text
Personal context = simple and direct
System/runtime    = engineered and protected
```

Classify the complete proposed change set before apply. Mixed changes use the most protective applicable class.

## Classes

### 1. Context update

Use for ordinary edits to existing Personal context owners where the owner shape, registry mapping, and access metadata remain unchanged.

Examples:

```text
current project state changed
an existing objective changed
an existing constraint changed
an existing Personal fact was corrected
```

Required rigor in a private Personal-SoT workspace:

- preview and explicit confirmation through the safe-write contract;
- re-read the affected owners immediately before write;
- direct write to the private canonical branch is allowed;
- no Python validator or full test suite is required solely because canonical Personal content changed;
- inspect the resulting patch for the intended owner/content only.

If an edit also creates/removes an owner, changes routing/registry structure, or changes `ai_access`, classify it as a structural context change.

### 2. Structural context change

Use for Personal-context changes that modify context shape, routing, registration, or access semantics.

Examples:

```text
create or remove a project/module owner
add or change a context-registry mapping
change ai_access
move context between semantic owners
```

Required rigor in a private Personal-SoT workspace:

- preview and explicit confirmation;
- re-read all affected owners and registry/access entries before write;
- direct write to the private canonical branch is allowed;
- run only the targeted validator(s) owned by the affected structure;
- do not run the full system test suite merely because Personal structure changed.

For ordinary Personal context structure or registry/access changes, the default targeted validator is:

```text
python3 -B system/validation/validate_v1.py --mode personal
```

Add another validator only when the confirmed change touches the domain it owns.

### 3. Docs/help

Use only when the complete change is user/developer documentation or help text and does not change executable behavior, runtime semantics, schemas, routing, access, governance, adapters, installers, migrations, or tests.

Typical locations include `guides/` and README/help content, but path alone never overrides semantics.

Required rigor in a private Personal-SoT workspace:

- normal review of the material diff;
- repository hygiene checks such as whitespace/format/link/path review when available;
- no full Python test suite solely for a docs/help-only change;
- direct write to the private canonical branch is allowed.

If documentation changes a canonical contract rather than merely explaining it, classify by the contract being changed, not as docs/help.

### 4. System/runtime/governance

Use for reusable product/runtime behavior and repository mechanics, including changes under or affecting:

```text
system runtime or reusable contracts
governance
adapters
installer/update implementation
migrations
product sync semantics
validators/tests
```

Also use this class for any material change that cannot be safely classified into one of the three lower-rigor classes.

Required rigor:

- governed development branch when required by the active repository governance;
- relevant full test/validator gates for that repository;
- diff and ownership/privacy review;
- owner acceptance before the candidate reaches the canonical branch.

For the public `Personal-SoT` product repository, `system/governance/branch_flow.md` remains authoritative for branch, PR, integration, and release mechanics.

## Classification precedence

When one proposal contains more than one class, use:

```text
system/runtime/governance
>
structural context change
>
context update
```

A docs/help-only proposal remains docs/help only while every changed item is explanatory. If docs accompany a higher class, the higher class governs the complete proposal.

Do not split one coherent semantic change merely to obtain a lower validation class.

## Capability boundary

Write capability and local-command capability are independent.

A host with authorized remote repository write capability may apply a confirmed private-workspace change when the selected class does not require unavailable local commands. In particular, a normal private context update does not become blocked merely because the host cannot run local Python validators.

A host must never claim a required validator or test passed when it could not actually run it. If the selected class requires checks unavailable on the current host, leave the change in a reviewable candidate state or provide the smallest truthful handoff required by repository governance.

User confirmation never creates write capability.

## Public/private boundary

This contract is reusable product semantics and therefore ships from the public repository.

It does not make the public product repository itself use private-workspace shortcuts. Public product development continues to follow `system/governance/branch_flow.md`.

Private installations receive this contract through normal installation/update of `system/` product files. Personal facts and user-owned private workspace state remain private and are never copied back to the public repository.

## Acceptance

A compliant workflow classifies once through this contract, upgrades mixed/uncertain material changes conservatively, performs only the rigor required by the resulting class plus any stricter active-repository rule, and never duplicates a competing branch/test classification inside individual workflows.
