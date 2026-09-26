# format_contract

## purpose

Defines semantics for reusable response-format modules selected through `@fmt` or profile/default/action composition.

Concrete user-editable format modules live under `workspace/presentation/formats/`.

## core_rule

A format controls response structure, placement, or representation. It does not own facts, reasoning method, tone, response depth, or factual scope. Formats are multi-value and additive.

## machine_readable_metadata

Each target registered under the `formats` section of `system/routing/switch_registry.md` MUST begin with YAML frontmatter containing:

```yaml
---
format_id: <lowercase_snake_case_identifier>
placement: <prefix|body|suffix>
---
```

Ownership rules:

- the `formats` registry section owns selectable identifier discovery and identifier-to-target mapping;
- each canonical format target owns its `format_id`, `placement`, and representation semantics;
- `format_id` MUST exactly equal the registry identifier that resolves to the target;
- `placement` MUST be exactly one of `prefix`, `body`, or `suffix`;
- validators and profile/prompt consumers SHOULD resolve format identities through the registry and consume target metadata rather than maintain independent current-format tables;
- prose may explain local rendering/ordering details, but MUST NOT become a second machine-readable owner of identity or placement.

Adding, renaming, or changing a registered format therefore updates the canonical target metadata and the compact registry mapping when its selectable identity/target lifecycle changes. Generic validators should not require source-code edits merely to learn a new format identity or placement.

## placement_model

```text
prefix → before main body
body   → main representation
suffix → appendix after main body
```

Placement order is `prefix -> body -> suffix`; within one band preserve effective format order unless the selected module's own rendering semantics require a more precise local position.

## boundaries

A format target owns only its representation and local placement behavior. Pedagogy remains behavior, professional wording remains tone, amount of detail remains depth, and factual authority remains context/policy routing.

A format must not change factual authority or hard policies.

## host_native_baseline

Normal chat uses the host/client's native presentation and formatting by default. Ordinary use of headings, emphasis, lists, tables, inline code, or other host-supported Markdown syntax for readability does not by itself activate a canonical format.

Canonical formats are bounded deltas over this baseline. Activation of one format must not suppress unrelated host-native formatting or broaden the scope of another format.

## composition

Lower-priority defaults establish a base set; explicit `@fmt` and `@no:fmt` operations apply afterward in source order. Genuine incompatibility must be surfaced or resolved explicitly.

Formats compose by their own metadata and module boundaries. Activation of one format does not broaden the scope of another format.

## token_efficiency

Resolve the compact registry first and load only selected format targets. Do not load all format modules merely to discover current identities or placement.

## acceptance

A compliant registered format has valid canonical metadata, is independently selectable through the registry, deterministic in placement, composable, separate from behavior/tone/depth/language/facts, and acts as a bounded delta over host-native presentation rather than replacing it wholesale.
