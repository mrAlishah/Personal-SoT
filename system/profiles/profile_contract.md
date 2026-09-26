# profile_contract

## purpose

Defines profiles as compact composition manifests for reusable behavior, runtime-control, and presentation defaults.

Concrete user-editable profile manifests live under:

```text
workspace/profiles/<profile_name>.md
```

The filename is the runtime profile identity; users invoke `@profile:<profile_name>` without a physical path prefix.

## runtime_resolution

Profile lookup is exact and path-derived:

```text
@profile:<profile_name>
→ workspace/profiles/<profile_name>.md
```

Profiles are not duplicated in a flat switch registry. A missing file is an unresolved profile configuration error. Case, spelling, aliases, and nearest-match normalization are not applied.

## representation

Profiles are Markdown files with YAML frontmatter. Example:

```yaml
---
behaviors:
  - reasoning
  - teaching
  - communication
formats:
  - yaml
  - eli5
  - concept
  - vocab
tone: professional
depth: deep
controls:
  <registered_control>: <allowed_value>
---
```

## allowed_fields

```text
behaviors[]
formats[]
tone
depth
language.primary
language.supporting[]
controls.<registered_control>
```

`controls` is a bounded runtime-control map, not an arbitrary key/value bag. Every control key must resolve through the canonical `registered_controls` section of `system/routing/switch_registry.md`, and every value must match the resolved control target's canonical machine-readable metadata defined by `system/behavior/control_contract.md`.

This contract does not maintain a second list of current control identities or allowed values. Registry membership owns registered control discovery; each canonical control target owns `control_id`, `control_values`, `control_default`, and behavior semantics.

Unknown control keys or invalid values are configuration errors; no fuzzy matching, aliases, or silent coercion are allowed.

Profiles MUST NOT contain canonical facts, context paths, hard policies, adapter wiring, tool credentials, nested profile references, or copied module instructions.

## reference_resolution

```text
behavior → system/behavior/<name>.md
format   → switch_registry formats entry → canonical format target metadata
tone     → switch_registry tones entry → canonical tone target
depth    → switch_registry depths entry → canonical depth target
language → workspace/presentation/languages/<name>.md
control  → switch_registry registered_controls entry → canonical control target metadata
```

Registry-covered presentation references therefore use the same selectable identity mapping as their runtime switches rather than assuming identity and physical filename can be independently re-derived by each consumer. Behavior and language remain self-addressing under their canonical paths; profile identity itself remains path-derived as defined above.

Unknown references are configuration errors; no fuzzy matching is allowed.

## multiple_profile_composition

Behaviors/formats merge and deduplicate preserving effective order. Later profile tone/depth wins among profile defaults. Later profile language replaces earlier profile language as one atomic configuration.

For a registered control, later selected profile value wins among profile defaults for that same control. Omitted controls do not invent a value and leave lower-priority defaults available.

## selection_precedence

```text
explicit_prompt_profiles
>
explicit_chat_or_session_profile_override
>
default_profile
>
no_profile
```

Profile-supplied control defaults participate only in the control-specific precedence lane defined by `system/routing/precedence.md`; they do not gain factual or policy authority.

Profiles never override hard policies or canonical facts and never select factual context.

## token_efficiency

Profiles store only identities/defaults. Resolve the manifest first and load only referenced modules and registered control contracts needed for the effective configuration.

## acceptance

A compliant profile is compact, deterministic, non-recursive, fact-free, directly resolvable from its canonical filename, resolves registry-covered presentation identities through the canonical registry, validates registered controls from registry + canonical control metadata without duplicated identity/value tables, and is explainable by module provenance.
