---
format_id: cheatsheet
placement: body
---
# cheatsheet

## purpose

Render information as a compact, scan-first quick reference for active reuse rather than as an explanatory essay.

## core_rule

Maximize useful signal per line while preserving operational correctness.

Prefer categorized, immediately reusable content over chronology, long transitions, repeated explanation, or decorative prose.

## structure

Use only sections supported by the content. Typical sections may include:

```text
Key points
Commands
Concepts
Language
Decisions / Settings
Errors / Fixes
Prompts / Invocations
Next actions
```

Do not emit empty sections and do not force every recap into the same category set.

## commands

For shell/Git/CLI material, prefer:

```text
exact command
→ one-line purpose
→ concise argument/option/switch explanation when useful
```

Keep the command itself copyable and exact. Explain only switches/arguments that appear in or are necessary to use the captured command correctly.

For one simple command, avoid a large table. For several commands/options, use a compact Markdown table or grouped code blocks when that improves scanning.

## concepts

Present concepts in dependency/learning order when supported.

Prefer:

```text
concept → one-line meaning → one-line relationship/use when needed
```

Do not repeat full examples already represented elsewhere unless an example is necessary to distinguish the concept.

## language

For translation/language material, group related phrases and preserve the useful source/target wording.

Use compact rows/lines such as:

```text
source | English | Deutsch | فارسی | note
```

Include only relevant languages/columns for the source material. Preserve corrections and high-value register/usage notes; omit repeated teaching prose.

## decisions_and_fixes

Prefer final actionable state:

```text
setting / decision → effective value
problem → fix
```

Preserve important cautions next to the item they constrain.

## brevity

Default to short fragments, concise sentences, tables, and code blocks. Avoid long introduction/conclusion paragraphs.

`cheatsheet` means compressed and usable, not vague. Do not remove exact values, parameters, command flags, or distinctions required for correctness.

## source_fidelity

A cheatsheet must not invent facts merely to make a category complete. Exact source-derived code, commands, identifiers, paths, and translations should remain faithful to the underlying source.

## composition

Compatible examples:

```text
yaml + cheatsheet
→ YAML frontmatter + quick-reference body

md + cheatsheet
→ Markdown document rendered with quick-reference structure

cheatsheet + vocab/concept
→ quick-reference body + explicitly selected suffix appendix
```

If another body format creates a genuine structural conflict, surface it rather than silently discarding one.
