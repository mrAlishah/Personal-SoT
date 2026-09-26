# End User Guide

## What you normally edit

Use `workspace/` for day-to-day Source-of-Truth maintenance.

```text
workspace/context/       facts, projects, constraints, current state
workspace/prompts/       reusable prompts
workspace/profiles/      reusable profile combinations
workspace/presentation/  formats, tones, depth and languages
workspace/adapters/      deployable Personal/client wrappers
```

Do not edit `system/` unless intentionally changing SoT engine behavior/contracts.

## Shared bootstrap model

Common AI operating rules live once in:

```text
system/adapters/base_instruction.md
```

Client/project instructions should remain thin wrappers that provide only source identity/access, defaults or overrides, and a pointer to that shared base.

Conceptually:

```text
shared base
├─ ChatGPT global wrapper
├─ ChatGPT project wrapper
├─ chat re-anchor
├─ AGENTS.md
└─ CLAUDE.md
```

This minimizes token cost, duplication, drift, and future maintenance.

### Generic ChatGPT global wrapper

```text
Use my authorized SoT as canonical.
Read and follow `system/adapters/base_instruction.md` and current `system/` contracts.
Use the configured repository/branch and default scope.
If SoT access is unavailable, do not invent canonical facts.
```

### Generic project instruction

```text
Follow the configured SoT and `system/adapters/base_instruction.md`.
Project-owned files/code/tests/config/instructions own project-specific truth.
default_scope: <scope>
Load only materially relevant context; do not duplicate durable facts/contracts here.
```

### Chat start / context-drift re-anchor

```text
Re-anchor to the configured SoT.
Follow `system/adapters/base_instruction.md` and current `system/` contracts.
Use minimum relevant canonical context; canonical SoT overrides conversation drift/memory.
```

### Generic Codex `AGENTS.md`

```text
source_root: <AUTHORIZED_SOURCE_ROOT>
default_scope: <scope>

Read and follow `<source_root>/system/adapters/base_instruction.md` and current contracts under `<source_root>/system/`.
For repository work, repository-owned code/config/tests/instructions have authority.
```

### Generic Claude `CLAUDE.md`

```text
source_root: <AUTHORIZED_SOURCE_ROOT>
default_scope: <scope>

Read and follow `<source_root>/system/adapters/base_instruction.md` and current contracts under `<source_root>/system/`.
For repository work, repository-owned code/config/tests/instructions have authority.
```

### Maintenance rule

```text
common operating change  → system/adapters/base_instruction.md
runtime syntax/algorithm → system/
personal/project facts   → workspace/context/
reusable task recipe     → workspace/prompts/
client path/default      → thin wrapper only
```

## Common runtime directives

```text
@ctx:<scope>
@profile:<name>
@fmt:<name>
@tone:<name>
@depth:<short|medium|deep>
@no:fmt:<name>

@do:prompt:<path>
@edit:prompt:<path>
@delete:prompt:<path>
@confirm:delete:prompt:<path>
@param:<name>=[value]
@recap:<positive_integer>
```

Runtime identities do not include physical `workspace/` prefixes; the engine resolves them.

## Safety

Never store raw passwords, API tokens, private keys, recovery codes, session cookies, OTPs, or other credentials in the SoT.
