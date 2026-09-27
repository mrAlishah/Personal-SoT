# m7_profile_contract_cases

These scenarios validate V1 profile manifests, composition, and runtime resolution behavior.

## case_01_profile_is_manifest

A profile needs reasoning + teaching + communication.

Expected: references module identities; does not copy module instructions.

## case_02_profile_not_fact_store

Statement: `project database = PostgreSQL`.

Expected: project context, never profile frontmatter.

## case_03_profile_not_context_selector

`g.coding` profile is active.

Expected: profile does not silently choose a factual `@ctx` scope.

## case_04_yaml_frontmatter_schema

Profile fields are stored as YAML frontmatter inside Markdown.

Expected: deterministic machine-readable manifest with no required prose body.

## case_05_additive_behaviors

Profile A behaviors `[reasoning, teaching]`; Profile B `[reasoning, communication]`.

Expected: `[reasoning, teaching, communication]` preserving first effective order.

## case_06_additive_formats

Profile A format `yaml`; Profile B formats `[md, concept]`.

Expected: all active when compatible; placement is handled by format contracts.

## case_07_profile_tone_later_wins

Profile A tone `human`; Profile B tone `professional`.

Expected among profile defaults: `professional`.

## case_08_profile_depth_later_wins

Profile A depth `medium`; Profile B `deep`.

Expected among profile defaults: `deep`.

## case_09_language_atomic_default

Profile A defines Persian; later Profile B defines German + English/Persian supporting.

Expected: later profile replaces the whole earlier language default; do not deep-merge two language defaults.

## case_10_profile_order_not_fact_authority

Later profile contains no authority to overwrite project facts or hard policies.

## case_11_explicit_profiles_replace_default_profile

Adapter default profile is `g.coding`; prompt explicitly selects `g.research`.

Expected: use explicit `g.research`, not hidden `g.coding + g.research`.

## case_12_multiple_explicit_profiles

Prompt selects `g.technical.learning` then `g.obsidian.note`.

Expected: behaviors from `g.technical.learning` remain; formats compose to ELI5 + concept + YAML + Markdown; tone/depth remain `g.technical.learning` defaults because `g.obsidian.note` defines neither.

## case_13_prompt_tone_over_profile

Profile default tone `human`; prompt `@tone:formal`.

Expected: formal.

## case_14_prompt_depth_over_profile

Profile default depth `deep`; prompt `@depth:short`.

Expected: short.

## case_15_prompt_format_operation_over_profile

Profile supplies `concept`; prompt disables `@no:fmt:concept`.

Expected: concept disabled for current prompt.

## case_16_prompt_language_over_profile

`g.german.learning` defaults to German; current prompt explicitly requests Persian.

Expected: Persian for current prompt only.

## case_17_unknown_behavior_reference

Profile references missing behavior.

Expected: configuration error; no fuzzy resolution.

## case_18_unknown_format_reference

Profile references unknown format.

Expected: configuration error.

## case_19_unknown_language_reference

Profile language is `de` instead of canonical `german`.

Expected: configuration error unless a later adapter explicitly maps an external locale.

## case_20_nested_profile_reference

Profile references another profile.

Expected: invalid in V1; nested profiles are forbidden.

## case_21_duplicate_profile_selection

Same profile selected twice.

Expected: idempotent profile selection according to M1.

## case_22_g_technical_learning_profile

Expected canonical manifest: reasoning + teaching + communication, ELI5 + concept, human tone, deep depth.

## case_23_g_architecture_review_profile

Expected canonical manifest: reasoning + research + architecture + review + communication, comparison table, professional tone, deep depth.

## case_24_g_research_profile

Expected canonical manifest: reasoning + research + communication, professional tone, deep depth.

## case_25_g_coding_profile

Expected canonical manifest: reasoning + coding + communication, professional tone, medium depth.

## case_26_g_german_learning_profile

Expected: reasoning + teaching + communication; ELI5 + vocab; human; medium; primary German; supporting English then Persian.

## case_27_g_obsidian_note_profile

Expected canonical manifest:

```text
formats: yaml + md
```

No behavior, tone, depth, language, or context default is introduced.

## case_28_obsidian_note_composition

`g.obsidian.note` + `g.german.learning` → YAML + Markdown packaging plus German-learning ELI5/vocab/language/tone/depth defaults.

Expected: no copied instructions and no hidden context selection.

## case_29_profile_dynamic_resolution

A conforming Core profile exists at `workspace/profiles/g.technical.learning.md`.

Expected: `@profile:g.technical.learning` resolves directly to that exact file without a switch-registry entry.

## case_30_profile_not_duplicated_in_switch_registry

A profile exists under `workspace/profiles/`.

Expected: `system/routing/switch_registry.md` does not duplicate the profile name/path mapping; filename identity is canonical.

## case_31_unknown_profile_file

Prompt selects `@profile:missing_profile` and no exact `workspace/profiles/missing_profile.md` exists.

Expected: unresolved profile configuration error; no alias, case correction, or fuzzy match.

## case_32_selective_loading

Resolver reads profile manifest, then loads only referenced effective behavior/presentation modules.

## case_33_profile_without_optional_field

A profile omits behaviors, language, tone, or depth.

Expected: no artificial empty/default field is required; a presentation-only profile such as `g.obsidian.note` is valid.

## case_34_profile_cannot_weaken_policy

Profile composition conflicts with hard policy.

Expected: hard policy remains authoritative.

## case_35_profile_portability

Canonical profile contains no ChatGPT/Claude/Codex-specific UI wiring.

Expected: client-specific defaults stay in adapter configuration.

## case_36_adapter_default_profile_is_executable_configuration

Adapter/project config selects `default_profile: g.technical.learning`; the user sends an ordinary prompt with no explicit profile or presentation switches.

Expected: runtime reads `workspace/profiles/g.technical.learning.md`, resolves and applies reasoning + teaching + communication, ELI5 + concept, human tone, and deep depth before answering. `default_profile` is not a label-only hint.

## case_37_selected_profile_modules_cannot_be_silently_dropped

An effective profile references a behavior or presentation module that the active client cannot read or resolve.

Expected: surface the module/configuration limitation; do not claim the profile is active while silently omitting the referenced behavior, format, tone, depth, or language module.
