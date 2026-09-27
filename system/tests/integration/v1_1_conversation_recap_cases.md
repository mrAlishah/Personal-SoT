# v1_1_conversation_recap_cases

These cases validate conversation-recap selection, source fidelity, domain adaptation, and quick-reference rendering.

## case_01_single_exchange

```text
@recap:1
```

Expected: summarize only the immediately preceding completed user/assistant exchange; exclude the recap request itself.

## case_02_five_exchanges

```text
@recap:5
```

Expected: summarize the five immediately preceding completed exchanges, not five individual messages or five assistant progress updates.

## case_03_positive_integer_only

`@recap:0`, `@recap:-1`, `@recap:2.5`, and `@recap:1-5` are invalid.

## case_04_no_summary_alias

`summary 5`, `@summary:5`, and misspelled `summay 5` are not parser aliases for `@recap:5`.

## case_05_incomplete_history

Five exchanges requested but client can access only three.

Expected: summarize three and disclose `3/5` coverage; never imply five were reviewed.

## case_06_source_only

Selected exchanges contain an outdated technical claim but no correction.

Expected: recap the source claim as source-derived content; do not silently web-search/correct it.

## case_07_later_correction

Exchange 2 gives command A; exchange 4 explicitly corrects it to command B.

Expected: effective recap emphasizes B. Mention A only if needed to prevent confusion.

## case_08_unresolved_conflict

Two selected exchanges disagree and neither resolves the disagreement.

Expected: concise conflict note; do not choose a winner from recency alone.

## case_09_bash_commands

Selected exchanges contain several Bash commands and long explanatory prose.

Expected recap keeps exact commands, one-line purposes, and supported option/argument explanations; remove repeated prose/examples.

## case_10_command_fidelity

A command contains `--force-with-lease`.

Expected: preserve exact spelling. Do not rewrite it to another Git option or invent semantics absent from source.

## case_11_concepts

Selected exchanges teach several related concepts with many examples.

Expected: compact concept sequence/relationships in learning order when supported; omit repeated examples.

## case_12_language_learning

Selected exchanges contain Persian source phrases plus English/German translations and corrections.

Expected: compact grouped phrase/translation reference with high-value usage/register notes.

## case_13_mixed_domain

Window includes Bash, architecture concepts, and German phrases.

Expected: categorize only populated groups; no empty boilerplate sections.

## case_14_decisions

Earlier selected exchange proposes option A; later exchange explicitly accepts option B.

Expected: recap final effective decision B, with A only if relevant historical contrast matters.

## case_15_error_fix

Several turns diagnose an error before finding one effective fix.

Expected: compress to problem -> effective fix/check plus essential caution; do not narrate every failed attempt unless diagnostically useful.

## case_16_focus_body

```text
@recap:8

Only keep Git/Bash commands and final settings.
```

Expected: body is a filter instruction, not an eighth/ninth source exchange.

## case_17_default_cheatsheet

`@recap:5` with no presentation override.

Expected: activate `conversation_recap`, `cheatsheet`, and recap depth default `short`.

## case_18_depth_override

```text
@recap:5
@depth:medium
```

Expected: medium depth overrides recap short default.

## case_19_format_override

```text
@recap:5
@no:fmt:cheatsheet
@fmt:md
```

Expected: no cheatsheet default; Markdown body remains active.

## case_20_yaml_composition

```text
@recap:5
@fmt:yaml
```

Expected: YAML frontmatter prefix + cheatsheet body.

## case_21_action_exclusivity

`@recap:5` plus `@do:prompt:x` in one control block.

Expected: invalid high-level action configuration; do not execute either ambiguously.

## case_22_param_invalid

`@recap:5` plus `@param:x=[y]`.

Expected: invalid; Prompt Library parameter binding does not apply to recap.

## case_23_ctx_invalid

`@recap:5` plus `@ctx:personal`.

Expected: invalid in V1.1; recap source remains selected conversation history only.

## case_24_profile_invalid

`@recap:5` plus `@profile:g.research`.

Expected: invalid in V1.1; do not silently add unrelated behavior/source acquisition.

## case_25_current_thread_only

Requested count exceeds exchanges in current thread but other chats exist.

Expected: do not retrieve other chats automatically; disclose current-thread coverage.

## case_26_progress_updates_not_counted

One previous request produced several progress updates before one final answer.

Expected: treat them as one logical exchange; ignore non-substantive progress text.

## case_27_copyable_active_use

Recap contains commands and settings.

Expected: operational items are easy to copy/use; no essay-length intro/outro.

## case_28_quality_over_compression

A short safety/correctness caveat is necessary to use a captured command correctly.

Expected: retain caveat even when recap is otherwise very short.
