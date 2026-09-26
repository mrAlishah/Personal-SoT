# v1_1_cheatsheet_cases

These cases validate `@fmt:cheatsheet` independently of conversation recap.

## case_01_independent_selection

```text
@fmt:cheatsheet
```

Expected: render the requested answer as a scan-first quick reference without activating conversation-history recap.

## case_02_no_history_side_effect

A normal current question uses `@fmt:cheatsheet`.

Expected: format only the current answer; do not summarize previous exchanges merely because cheatsheet is active.

## case_03_command_sheet

Current answer contains several shell commands.

Expected: exact copyable commands, one-line purpose, and concise switch/argument explanation when useful.

## case_04_command_exactness

Current answer contains `git push --force-with-lease`.

Expected: preserve exact option text and operational caveats required for safe use.

## case_05_concepts

Current answer explains related technical concepts.

Expected: compact concept/relationship ordering; avoid essay repetition.

## case_06_language

Current answer is a translation/language-learning task.

Expected: compact phrase/translation grouping using only relevant language columns/items.

## case_07_mixed_content

Current answer contains commands, decisions, and concepts.

Expected: only populated sections; no empty category boilerplate.

## case_08_single_simple_item

Current answer contains one simple command.

Expected: do not force a large table; keep representation proportional to content.

## case_09_yaml_composition

```text
@fmt:yaml
@fmt:cheatsheet
```

Expected: YAML frontmatter prefix, then quick-reference body.

## case_10_md_composition

```text
@fmt:md
@fmt:cheatsheet
```

Expected: valid Markdown document organized as a quick reference.

## case_11_suffix_composition

```text
@fmt:cheatsheet
@fmt:vocab
```

Expected: cheatsheet body followed by explicit vocabulary suffix; do not move suffix content into the body merely for compactness.

## case_12_correctness_over_density

A caveat, parameter, unit, or exact value is necessary for correct active use.

Expected: retain it even if the cheatsheet becomes slightly longer.

## case_13_no_fabricated_categories

Source answer has no commands or language material.

Expected: do not invent Commands/Language sections to satisfy a template.
