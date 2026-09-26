# m4_presentation_contract_cases

These scenarios validate V1 format, tone, depth, placement, and additive composition semantics.

## case_01_format_not_behavior

`cross-check current claims` → research behavior, not format.

## case_02_tone_not_depth

`professional` changes register, not response length.

## case_03_depth_not_scope

`@depth:deep` must not broaden factual scope or authority.

## case_04_format_additive

`@fmt:eli5` + `@fmt:comparison_table` → both active when compatible.

## case_05_duplicate_format

Repeated `@fmt:yaml` → one effective format.

## case_06_format_remove_order

`@fmt:yaml` then `@no:fmt:yaml` → YAML frontmatter disabled.

## case_07_format_reenable_order

`@no:fmt:yaml` then `@fmt:yaml` → YAML frontmatter enabled.

## case_08_yaml_is_frontmatter_prefix

`@fmt:yaml` → first response content is `---`; metadata is Obsidian YAML frontmatter, not a YAML-only response.

## case_09_yaml_canonical_fields

Active YAML frontmatter normally contains, in order:

```text
Name
Type
Subject
Status
Tags
Aliases
Date Time
```

Expected: `Status` defaults to `Reviewed`; this is note lifecycle metadata, not proof of external verification.

## case_10_yaml_timestamp_quality

Host knows current date but not reliable local clock time.

Expected: do not fabricate time precision merely to fill `Date Time`.

## case_11_yaml_plus_vocab

Both active → YAML frontmatter first, normal answer body, Markdown vocabulary table at the end.

Expected: vocabulary is NOT converted to YAML records.

## case_12_yaml_plus_comparison

Both active → YAML frontmatter first, then comparison structure in the answer body.

Expected: comparison is NOT converted to YAML records merely because `yaml` is active.

## case_13_yaml_plus_concept

Both active → YAML frontmatter first, answer body, concept table at end.

## case_14_md_document

`@fmt:md` → main answer is a coherent Markdown document suitable for direct Obsidian use.

Expected: do not wrap the entire response in one Markdown fence by default.

## case_15_yaml_plus_md

Both active → YAML frontmatter first, then Markdown body after the closing `---`.

## case_16_yaml_md_vocab

`yaml + md + vocab` → frontmatter prefix + Markdown body + vocabulary appendix.

## case_17_yaml_md_concept

`yaml + md + concept` → frontmatter prefix + Markdown body + concept appendix.

## case_18_placement_bands

Formats are activated in an order where a suffix appears before a prefix.

Expected: intrinsic placement still renders `prefix → body → suffix`; raw activation order does not put vocab/concept before YAML/body.

## case_19_suffix_order

Both `vocab` and `concept` are active.

Expected: both appear at the end; their relative order follows effective format order.

## case_20_vocab_canonical_columns

`@fmt:vocab` → end appendix uses the canonical shape owned by `workspace/presentation/formats/vocab.md`:

```text
Deutsch | English | فارسی | Wortart | اطلاعات تکمیلی
```

## case_21_vocab_selectivity

Long answer contains many common words but only a few pedagogically useful phrases.

Expected: summarize high-value/reusable language items, not every word.

## case_22_vocab_language_focus

English/German translation task + `vocab` → useful English/German words, phrases, idioms, collocations, or grammar notes are summarized at the end.

## case_23_vocab_not_concept_dump

Technical learning task has conceptual terms but no language-learning intent.

Expected: prefer `concept`; do not use vocab as a generic concept table unless explicitly selected.

## case_24_concept_canonical_columns

`@fmt:concept` → end appendix uses the canonical shape owned by `workspace/presentation/formats/concept.md`:

```text
Concept | Definition | Related / Distinct From | Simple Example
```

## case_25_concept_localization

Persian answer explains Playwright MCP.

Expected: canonical concept names may remain English; Definition, Related / Distinct From, and Simple Example are rendered in Persian.

## case_26_concept_selectivity

Deep answer contains many details.

Expected: concept appendix summarizes only high-value concepts and does not repeat the entire response.

## case_27_eli5_not_teaching

`eli5` may simplify wording but does not activate pedagogical sequencing or change depth.

## case_28_teaching_plus_eli5

Teaching behavior + ELI5 format → pedagogy comes from teaching; accessible rendering comes from ELI5.

## case_29_tone_single_value

Two explicit tones → last explicit prompt tone wins.

## case_30_tone_does_not_change_fact

Any selectable tone wording must preserve the same canonical fact.

## case_31_prompt_tone_over_profile

Explicit `@tone:formal` overrides profile default `human` for the prompt.

## case_32_prompt_depth_over_profile

Explicit `@depth:short` overrides profile default `deep`.

## case_33_short_keeps_critical_caveat

Short depth may prune background, not mandatory policy or material uncertainty.

## case_34_deep_not_repetition

Deep adds mechanisms, trade-offs, evidence, and boundaries; it must not pad with repeated content.

## case_35_german_learning_vocab

`german_learning` profile includes `vocab`.

Expected: vocabulary appendix appears at the end under the suffix semantics owned by the format target metadata.

## case_36_technical_learning_concept

`technical_learning` profile includes `concept`.

Expected: concept appendix summarizes learned technical concepts at the end.

## case_37_technical_learning_remove_concept

`@profile:technical_learning` + `@no:fmt:concept` → concept appendix disabled for that prompt while other profile defaults remain.

## case_38_obsidian_note_profile

`@profile:obsidian_note` → `yaml + md` formats enabled without changing behavior, tone, depth, language, or context.

## case_39_obsidian_plus_german

`@profile:obsidian_note` + `@profile:german_learning` → formats compose to include YAML frontmatter, Markdown-capable body, ELI5 rendering, and vocabulary suffix; language/tone/depth come from german_learning.

## case_40_invalid_format_name

Unknown `@fmt` value does not silently map to the nearest format.

## case_41_policy_over_presentation

No presentation module may weaken or hide an applicable hard policy.

## case_42_quality_over_context_cost

Presentation compactness or context-cost optimization must not remove information required for correctness.

## case_43_selective_loading

Only effective format/tone/depth modules enter runtime presentation context; contracts/tests remain design-time.

## case_44_non_md_profile_preserves_host_native_chat

Effective formats are `yaml + eli5 + concept`; canonical `md` is inactive.

Expected:

```text
YAML frontmatter
host-native normal chat body
concept table suffix
```

The host may use its ordinary headings, emphasis, lists, tables, inline code, or other native chat formatting for readability. That host formatting does not activate canonical `md`. YAML, ELI5, and concept modify only their owned prefix/rendering/suffix boundaries and must not suppress unrelated host-native formatting.

## case_45_start_language_without_prefix

Effective `start_language = fa` and no prefix/starter format is active.

Expected: the conversational body begins with at least one natural Persian sentence; after that opening, ordinary effective language rules continue.

## case_46_start_language_with_prefix

Effective `start_language = fa` and a prefix/starter format owns the beginning of the response.

Expected: preserve the prefix's mandatory structural opening and render its first eligible human-readable owned element in Persian. If the prefix cannot safely represent localized human-readable content, keep it valid and apply Persian to the first eligible human-readable element after it.

## case_47_start_language_not_direction

Effective `start_language = fa`.

Expected: this does not itself assert or configure RTL rendering; response-start language and text direction remain separate concerns.
