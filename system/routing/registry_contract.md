# registry_contract

## purpose

Defines registries for deterministic discovery/validation without creating a second Source of Truth.

## core_rule

A registry indexes canonical identities; it never owns target content.

```text
registry_entry
→ points_to canonical_target

canonical_target
→ remains_authoritative
```

## registry_types

```text
system/routing/context_registry.md
system/routing/switch_registry.md
```

`context_registry.md` registers selectable factual scope identities.

`switch_registry.md` registers runtime-selectable identities that require explicit name-to-module mapping, such as formats, tones, depths, registered controls, and grammar actions whose canonical targets are not already self-addressing paths.

Profiles are intentionally not duplicated in the flat switch registry. Their runtime identity is the exact filename under `workspace/profiles/`, as defined by `system/profiles/profile_contract.md`.

## prompt_library_exception

V1.1 prompt templates are intentionally **not** registered in a flat prompt registry.

Prompt identity is already deterministic:

```text
@run:code/review
→ workspace/prompts/code/review.md
```

The same exact path rule applies to `@edit` and `@delete`.

Tags/targeted search may help discover a prompt, but discovery results do not create aliases or authority. Once selected, the exact canonical path is the identity.

This avoids duplicated path mappings, registry maintenance drift, and loading an ever-growing dynamic prompt index for exact invocation.

## grammar_value_exception

Some runtime actions use parser-validated grammar values rather than registry identities.

V1.1 example:

```text
@recap:<positive_integer>
```

The numeric count is validated by `system/routing/recap_contract.md`; it is not enumerated in a registry.

The action's canonical supporting modules remain explicit in the contract:

```text
system/behavior/conversation_recap.md
workspace/presentation/formats/cheatsheet.md
```

Do not create registry entries for every possible recap count.

## minimal_entries

Where a registry is required, entries contain only discovery information such as name/canonical path/kind. Do not copy facts, policy text, behavior instructions, presentation rules, profile contents, prompt templates, or access metadata into registries.

## context_registry

A registered scope means the resolver can recognize scope identity. Module loading still follows access/relevance/authority rules.

## switch_registry

A registered value is resolvable only when its namespace is supported, identifier is lexically valid, and target exists.

Unknown values are not fuzzy-matched or auto-corrected.

Current registry-covered identities are discovered only from `system/routing/switch_registry.md`; this generic contract does not maintain a second list of currently registered formats, tones, depths, or controls.

Profile identities remain the deliberate self-addressing exception described above.

Prompt action keywords and recap count are grammar defined by routing contracts, not registry entries.

## lifecycle

When a registry-covered target is added/renamed/removed, update its registry coherently.

Profile files remain self-addressing and follow `system/profiles/profile_contract.md`.

Prompt files follow direct path lifecycle under `workspace/prompts/` and `system/prompts/action_contract.md`.

Grammar-defined action values follow their routing contract.

## token_efficiency

Registries stay compact. Self-addressing profile and prompt identities should not require duplicated flat registry entries. Exact prompt-path invocation should not require scanning all prompt files or maintaining a duplicated prompt registry. Recap should not require enumerating numeric counts.

## acceptance

A compliant registry enables deterministic discovery where needed while preserving one authoritative source and recognizing self-addressing profile/prompt paths and grammar-valued actions as deliberate no-registry cases.
