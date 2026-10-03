# m5_registry_cases

These scenarios validate registry discovery without duplicating canonical truth.

## case_01_registry_is_index

A registry entry points to a canonical target.

Expected: target content remains authoritative; registry does not copy it.

## case_02_no_fact_duplication

A context scope is registered.

Expected: project facts remain in context modules, not the registry.

## case_03_no_access_duplication

A registered context contains modules with different `ai_access` values.

Expected: registry does not repeat or override module access metadata.

## case_04_empty_context_registry_is_valid

No real factual scopes exist yet.

Expected: context registry may remain empty rather than invent placeholder contexts.

## case_05_scope_registration_not_access

A scope is registered but one module is denied.

Expected: scope identity resolves; denied module remains unavailable.

## case_06_unknown_scope

A registry-backed resolver receives a validly shaped scope that has no registered real target.

Expected: unresolved scope; do not silently substitute another scope.

## case_07_format_resolution

`@fmt:compare` maps exactly to `workspace/presentation/formats/compare.md`.

## case_08_new_format_resolution

Expected exact mappings:

```text
@fmt:yaml     → workspace/presentation/formats/yaml.md
@fmt:md       → workspace/presentation/formats/md.md
@fmt:vocab    → workspace/presentation/formats/vocab.md
@fmt:concept  → workspace/presentation/formats/concept.md
```

## case_09_profile_self_addressing_resolution

`@profile:obsidian/note` resolves directly to `workspace/profiles/obsidian/note.md` by exact filename.

Expected: no flat switch-registry entry is required or created for the profile.

## case_10_tone_resolution

`@tone:professional` maps exactly to `workspace/presentation/tones/professional.md`.

## case_11_depth_resolution

`@depth:deep` maps exactly to `workspace/presentation/depth/deep.md` and remains inside the canonical depth set.

`@depth:summary` maps exactly to `workspace/presentation/depth/summary.md`.

## case_12_no_behavior_switch

`@behavior:research` is not registered because V1 has no behavior switch namespace.

## case_13_no_fuzzy_match

`@fmt:comparison-table` must not map to `compare`.

## case_14_case_sensitive

`@fmt:MD` must not map to `md`; `@tone:Professional` must not map to `professional`.

## case_15_stale_entry

Registry entry points to a missing canonical file.

Expected: configuration defect; do not redirect to a similar target.

## case_16_profile_lifecycle_is_path_derived

When a canonical profile is created, renamed, or removed, its runtime identity follows the exact file lifecycle under `workspace/profiles/`.

Expected: do not add or maintain a duplicated flat switch-registry entry for the profile.

## case_17_registry_does_not_change_precedence

A registered presentation module remains subject to M1 prompt/profile/default precedence.

## case_18_registry_bootstrap_cost

Resolver may load compact registry indexes without loading every target module.

Expected: selected target content is loaded only after resolution.

## case_19_single_target_identity

Within one registry namespace/section, one identifier maps to exactly one canonical target.

## case_20_target_rename

A registry-covered selectable canonical target is renamed.

Expected: registry is updated coherently; stale old identifier does not silently alias.

## case_21_quality_over_convenience

A missing required registry entry causes explicit unresolved configuration rather than a guessed nearest target.

## case_22_registry_covered_presentation_target_must_be_indexed

A canonical file is added under one of these registry-covered locations:

```text
workspace/presentation/formats/
workspace/presentation/tones/
workspace/presentation/depth/
```

but no corresponding `switch_registry` entry is added.

Expected: static validation fails. A registry-covered target lifecycle must update the compact index coherently.

## case_23_duplicate_context_scope_identity

`context_registry.md` declares the same runtime scope identifier more than once, whether the duplicate points to the same directory or a different directory.

Expected: static validation fails; one runtime scope identity must have one canonical mapping.

## case_24_invalid_context_scope_grammar

A registered runtime scope contains an invalid segment such as camelCase, kebab-case, an empty path segment, or another value outside canonical lowercase_snake_case path grammar.

Expected: static validation fails rather than normalizing or guessing the scope identity.

## case_25_correct_format_resolution

`@fmt:correct` maps exactly to `workspace/presentation/formats/correct.md`.

Expected: the selectable format is present in `switch_registry`; validation fails if that lifecycle mapping becomes stale or missing.

## case_26_registered_format_metadata_is_canonical

A target under the registry `formats` section declares:

```yaml
---
format_id: learn
placement: suffix
---
```

Expected: identity/placement consumers derive these facts from registry + canonical target metadata rather than a second current-format table.

## case_27_registry_format_id_mismatch

The registry identifier is `learn` but its target declares a different `format_id`.

Expected: static validation fails; registry identity and target metadata must agree exactly.

## case_28_invalid_or_missing_format_placement

A registered format omits `placement` or declares a value outside:

```text
prefix
body
suffix
```

Expected: static validation fails.

## case_29_profile_format_uses_registry_identity

A profile references a format identifier for which a same-named file happens to exist but no canonical `formats` registry mapping exists.

Expected: profile validation fails. Profile format references use the registry identity, not an independently inferred physical path.

## case_30_prompt_format_uses_registry_identity

A prompt manifest references a format identifier for which a same-named file happens to exist but no canonical `formats` registry mapping exists.

Expected: prompt validation fails. Prompt format references use the registry identity, not an independently inferred physical path.

## case_31_generic_consumers_do_not_own_current_registry_inventory

A registered format, tone, depth, or control is added or renamed while its generic routing/adapter contracts remain otherwise semantically unchanged.

Expected: only the canonical registry/target lifecycle and genuinely affected behavior/tests require updates. Generic contracts must discover current identities instead of maintaining duplicate current-inventory tables.

## case_32_profile_tone_and_depth_use_registry_identity

A profile references a tone or depth for which a same-named target file exists but the corresponding registry mapping is absent.

Expected: profile validation fails. Registry-covered presentation identities use the registry rather than independently inferred physical paths.

## case_33_prompt_tone_and_depth_use_registry_identity

A prompt manifest references a tone or depth for which a same-named target file exists but the corresponding registry mapping is absent.

Expected: prompt validation fails for the same registry-ownership reason as profile validation.

## case_34_same_identifier_in_different_switch_namespaces

The identifier `compact` is registered once under `formats` and once under `depths`, each to its own canonical target.

Expected: valid. Runtime namespaces are distinct (`@fmt:compact` versus `@depth:compact`), so duplicate-identifier validation is scoped to one registry section/namespace rather than globally across all sections.
