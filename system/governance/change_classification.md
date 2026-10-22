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

### 1a. User-owned workspace content change

Use for ordinary creation or editing of verified **user-owned** content in a
private Personal-SoT workspace:

```text
workspace/context/       existing non-structural context content
workspace/prompts/       user-authored Prompt templates
workspace/profiles/      custom, non-product-owned Profiles
workspace/presentation/ verified user-owned presentation content
```

Classification follows **ownership and effects**, not file path alone.
Product-shipped Prompts, Profiles, formats, and public-owned modules do not
become user-owned merely because they reside in `workspace/`. For private
presentation files without an ownership marker, verify private provenance and
absence of conflicting product ownership. Uncertain ownership must be resolved
before proposing a lightweight write.

Required rigor in a private user-owned workspace:

- show complete proposed content/diff and obtain explicit confirmation;
- re-read the latest owner, access metadata, and relevant dependencies;
- reject stale, conflicting, unsafe, unauthorized, or nonconforming writes;
- use the focused source/identity/reference validator, or an equivalent
  reliable check of the affected domain, before and after a content write;
- apply only the confirmed content directly to private `main` where
  authorized write capability and required checks are actually available;
- do not require a temporary branch, merge, full Python unit suite, or
  repository-wide validators solely for a user-owned content change;
- verify the resulting write/commit where possible and truthfully report
  what was checked and applied.

Creating/removing context owners, changing context registry/routing, or changing
`ai_access` remains a **structural context change**. The narrowly defined
standard additive Personal-project exception below uses focused structural
checks instead of a Python validator; other structural changes require their
targeted validator. Changes to adapters, governance, system implementation, schemas,
protected product-shipped content, or product-sync behavior remain
**system/runtime/governance** regardless of file location. Deletion/rename
with unresolved dependencies is not ordinary content maintenance.
Use the most protective applicable class for mixed proposals.

When required focused checks cannot be established on the active host, stop
before mutation and report the limitation. Confirmation never creates
authorization or validation capability. Public product development remains
subject to public repository governance and full required gates.

### 2. Structural context change

Use for Personal-context changes that modify context shape, routing, registration, or access semantics.

#### Standard additive private Personal project (focused-check exception)

A private, single-user Personal installation may create a new ordinary
`personal/projects/<project_id>` project or add a standard module to an
already registered ordinary Personal project **directly on private `main`
without a temporary branch or Python validator**, only when ALL of these
conditions are established by real host/repository evidence:

1. The change is additive: create new project-owned Markdown modules under
   `workspace/context/personal/projects/<project_id>/`, with no deletion,
   move, rename, or edit of existing context. A new project includes
   `project.md` with a meaningful purpose; other modules are only justified
   standard project modules from `system/context/module_catalog.md`.
2. For new projects, the only non-context edit is exactly one new
   `personal/projects/<project_id>` mapping to its matching directory in
   `system/routing/context_registry.md`. For a new module in an existing
   registered project, the registry is unchanged. Do not alter or remove any
   existing scope or mapping.
3. Validate exact lowercase_snake_case identifiers and repository paths,
   unique scope and target mappings, existing project registration where
   applicable, absence of an existing conflicting owner/path, and no
   overlapping semantic owner. Reject unexpected files or dependencies.
4. Every new module has valid Markdown/frontmatter with explicit
   `ai_access: allow`. No changed access values, restricted/deny modules,
   sensitive content, raw secrets, new policies or decisions, or product-owned
   files qualify for this shortcut. Host authorization and scope/access
   checks still apply.
5. Before writing, re-read the current registry, affected target paths and
   branch HEAD; confirm that the exact preview is still applicable. Apply
   project files and any registry addition in **one atomic commit** on
   private `main` using a current-HEAD concurrency guard; a sequence of
   unrelated per-file commits is not an equivalent safe apply.
6. Inspect the resulting committed diff and re-read the new owner/modules
   and effective registry entry to verify the exact confirmed change, access
   metadata, paths and coherent registration. Any missing capability,
   unsupported check, unexpected diff or concurrent drift blocks completion.
   Do not describe focused checks as a full Personal validator pass.

These are bounded pre/post structural checks, not permission to skip
validation. They may be carried out with repository read/write APIs (for
example, on ChatGPT Web) and require **no local Python execution**. If
the host cannot establish every condition, fail closed and use the
ordinary targeted-validator path below. The exception changes only the
validation method for this limited additive Personal-project case; it
does not turn structural changes into ordinary context updates.

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
- use the focused pre/post checks above for an eligible standard additive private Personal project; otherwise run only the targeted validator(s) owned by the affected structure;
- do not run the full system test suite merely because Personal structure changed.

For all other Personal context structure or registry/access changes, the default targeted validator is:

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
user-owned workspace content change
>
context update
```

A docs/help-only proposal remains docs/help only while every changed item is explanatory. If docs accompany a higher class, the higher class governs the complete proposal.

Do not split one coherent semantic change merely to obtain a lower validation class.

## Capability boundary

Write capability and local-command capability are independent.

A host with authorized remote repository write capability may apply a confirmed private-workspace change when the selected class does not require unavailable local commands. In particular, a normal private context update, user-owned content edit, or eligible standard additive Personal-project change does not become blocked merely because the host cannot run local Python validators, provided its required focused checks, atomicity and access protections can be established.

A host must never claim a required validator or test passed when it could not actually run it. If the selected class requires checks unavailable on the current host, leave the change in a reviewable candidate state or provide the smallest truthful handoff required by repository governance.

User confirmation never creates write capability.

## Public/private boundary

This contract is reusable product semantics and therefore ships from the public repository.

It does not make the public product repository itself use private-workspace shortcuts. Public product development continues to follow `system/governance/branch_flow.md`.

Private installations receive this contract through normal installation/update of `system/` product files. Personal facts and user-owned private workspace state remain private and are never copied back to the public repository.

## Acceptance

A compliant workflow classifies once through this contract, upgrades mixed/uncertain material changes conservatively, performs only the rigor required by the resulting class plus any stricter active-repository rule, and never duplicates a competing branch/test classification inside individual workflows.
