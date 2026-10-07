# Change policy

## Purpose

Choose the lightest safe Git and validation flow for each change before mutation.

This policy is semantic, not extension-based. A Markdown file can be help documentation or a runtime/governance contract; classify what the change means, not only where it lives.

## Decision

Every change resolves:

```text
change class
→ branch mode
→ validation level
```

Use the strongest class when one proposal contains more than one class.

| Change class | Branch | Validation | Normal target |
|---|---|---|---|
| `help_docs` | No | hygiene only | public `develop` by default; explicit docs-only `main` allowed |
| `private_context_content` | No | none | private `main` |
| `private_context_structure` | No by default | targeted if available | private `main` |
| `system_change` | Yes | full relevant | engineered public/private flow |

## Classes

### help_docs

User-facing explanatory documentation only.

Typical examples:

```text
readme.md
guides/user/**
guides/developer/**
```

Only classify as `help_docs` when the change does not alter executable behavior, machine-consumed configuration, runtime contracts, governance rules, adapters, schemas, prompts, installers, validators, or tests.

Policy:

```text
branch: not required
python tests: not required
validation: hygiene_only
```

In the public product, direct updates go to `develop` by default. A direct `main` documentation correction is allowed only when the user explicitly selects stable `main` and the change remains help-only.

Hygiene means review the diff, public/private-data boundary, and links/paths touched by the edit. Run `git diff --check` when Git command capability exists.

### private_context_content

A content-only update to existing Personal/project context owners.

This class requires all of the following:

- the canonical owner already exists;
- path, scope registration, module identity, schema/frontmatter shape, and `ai_access` are unchanged;
- the edit changes only user-owned factual/project content;
- no system/product semantic owner changes.

Policy in a private Personal-SoT repository:

```text
branch: not required
preview + explicit confirmation: required
python tests: not required
validation: none
target: current private main
persistence: commit + push when the host exposes those capabilities
```

Before writing, re-read the current owner and selected `main` revision when available. If either changed after preview, invalidate the confirmation and show a revised preview.

For a remote provider write, a successful server-side commit to private `main` is the commit/push step; no local Git process is additionally required.

### private_context_structure

A Personal/project change that changes structure rather than only existing content.

Examples:

- create/delete/move a Personal context module or project;
- register/unregister a Personal/project scope in `system/routing/context_registry.md`;
- change Personal context `ai_access`, frontmatter identity, or ownership metadata.

A registry edit belongs to this class only when it registers or unregisters private Personal context. Changing registry format, routing semantics, or reusable rules is a `system_change`.

Policy in a private Personal-SoT repository:

```text
branch: not required by default
preview + explicit confirmation: required
full unit tests: not required
validation: targeted_if_available
target: current private main
persistence: commit + push when the host exposes those capabilities
```

The normal targeted validator is:

```text
python3 -B system/validation/validate_v1.py --mode personal
```

Run it when local-command capability exists. A web client that can atomically write the confirmed private change but cannot run local Python may still apply it; it must report that targeted validation was unavailable rather than inventing a pass.

If the proposal also changes system/runtime/product semantics, reclassify the whole proposal as `system_change`.

### system_change

Changes to reusable product/runtime behavior, governance, adapters, installers, validators, tests, migrations, update machinery, schemas, prompt semantics, or product sync behavior.

Typical owners include:

```text
system/**
workspace/adapters/**
workspace/governance/**
install.*
update.*
tests / validators / migrations
```

The path list is evidence, not the classifier. A private Personal registration entry in the context registry remains `private_context_structure`; changing how the registry works is `system_change`.

Policy:

```text
branch: required
preview/acceptance: according to owning workflow
validation: full_relevant
```

For public product work, start from current `develop` and use the public branch flow. For private product/runtime maintenance or sync, start from current private `main` and use the private branch flow.

If a material mutation does not clearly satisfy `help_docs`, `private_context_content`, or `private_context_structure`, classify it as `system_change`. Do not invent a lighter class.

## Mixed changes

A proposal uses the strongest applicable class.

```text
help_docs + system_change           → system_change
private_context_content + structure → private_context_structure
private context + system semantics  → system_change
```

A destructive operation does not automatically require a branch when it remains strictly private context, but it requires exact preview, explicit confirmation, current-state re-check, and the structural class when paths/registration/access are affected.

## Capability boundary

Branch policy and validation policy never create host capability.

- read does not imply write;
- confirmation does not imply write;
- remote write does not imply local command execution;
- local command execution does not imply provider push permission.

Use only capabilities actually exposed by the current host.

## Reporting

For a normal Personal/project content update, the beginner-facing flow is:

```text
understand change
→ preview
→ confirm
→ update private main
→ commit/push
→ report
```

Do not burden the user with branch or Python-test mechanics when this policy says they are not required.

## Acceptance

Each mutation is classified before writing, uses the lightest permitted branch/validation flow, preserves preview/confirmation for Personal context, and escalates mixed system changes to the engineered flow.
