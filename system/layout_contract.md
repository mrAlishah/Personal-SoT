# repository_layout_contract

## purpose

Defines the physical repository layout while keeping runtime identities stable and client-neutral.

## primary_roots

Exactly three primary directories own repository content:

```text
workspace/
system/
guides/
```

`readme.md` may remain at repository root as the navigation entry point.

## ownership

```text
workspace/
→ end-user managed canonical content and configuration

system/
→ runtime contracts, algorithms, validation, governance and tests

guides/
→ documentation organized by audience
```

## logical_to_physical_mapping

Runtime directives never include the physical `workspace/` prefix.

```text
context scope   → workspace/context/
prompt identity → workspace/prompts/
profile identity→ workspace/profiles/
format identity → workspace/presentation/formats/
tone identity   → workspace/presentation/tones/
depth identity  → workspace/presentation/depth/
language module → workspace/presentation/languages/
```

System contracts for those user-managed modules live under:

```text
system/context/
system/prompts/
system/profiles/
system/presentation/
```

## stable_runtime_identity

The refactor changes physical storage, not public runtime syntax.

Examples:

```text
@ctx:personal
@profile:tech/learn
@fmt:yaml
@tone:human
@depth:short
@run:chat/recap
```

No user should need to write `@ctx:workspace/context/personal` or `@run:workspace/prompts/...`.

## user_edit_boundary

Ordinary end-user maintenance should remain inside `workspace/` and should conform to contracts in `system/`.

A user may update facts, prompts, profiles, concrete presentation modules, and Personal adapter configuration without editing routing/validation/governance internals.

## developer_boundary

Changes to grammar, precedence, access semantics, schemas, validators, behavior algorithms, generic adapter semantics, governance or tests belong under `system/` and follow `system/governance/branch_flow.md`.

## guide_boundary

```text
guides/user/
→ operational instructions that do not require architecture knowledge

guides/developer/
→ architecture, extension, validation, fake examples and maintenance guidance
```

Fake examples are non-runtime and live under `guides/developer/examples/`.

## acceptance

A compliant repository has no legacy top-level implementation areas such as `context/`, `prompts/`, `routing/`, `validation/`, or `tests/`; runtime resolution still produces the same logical identities; and end-user content can be distinguished from system internals by path alone.
