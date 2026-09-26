# tone_contract

## purpose

Defines shared semantics for reusable tone modules selected through `@tone` or profile/default configuration.

Current selectable tone identities are discovered from the `tones` section of `system/routing/switch_registry.md`. Concrete tone targets own tone-specific wording/register rules; this contract does not maintain a second current-tone inventory.

## core_rule

Tone controls the interpersonal and linguistic character of the response. It does not control factual content, reasoning method, response structure, or detail level.

Tone is single-value.

## precedence

Tone precedence and source authority are owned by `system/routing/precedence.md`. This presentation contract does not duplicate that precedence chain.

Within one prompt control block, source-order handling of explicit tone directives follows `system/routing/switch_syntax.md` and the precedence contract.

## boundaries

```text
professional wording → tone
formal register → tone
comparison table → format
short response → depth
cross-check evidence → behavior
```

Tone MUST NOT weaken policies or distort technical meaning to sound friendlier, more formal, or more confident.

## plain_keyboard_punctuation

A concrete tone may explicitly activate the shared rule:

```text
plain_keyboard_punctuation
```

When active, ordinary AI-generated prose uses plain keyboard punctuation instead of typographic punctuation that can make conversational text look overly typeset or synthetic.

Canonical normalization for generated prose:

```text
— → -
– → -
… → ...
“ or ” → "
‘ or ’ → '
```

The rule also avoids decorative Unicode punctuation/symbols used only for styling when a plain keyboard equivalent is clearer.

This rule is NOT `ASCII-only` output. Do not normalize away characters that are meaningful to language, data, code, or technical notation.

Preserve exact characters when they are part of:

```text
quoted/source text
verbatim user text when fidelity matters
code or command literals
URLs
filesystem paths
identifiers
filenames
structured data values
mathematical or technical notation
Markdown syntax
language-correct letters or punctuation
```

Examples that remain valid when linguistically/technically appropriate include Persian punctuation, German umlauts, accented letters, mathematical operators, and technical symbols.

If plain punctuation conflicts with source fidelity or technical correctness, fidelity/correctness wins.

## retrieval_efficiency

Load only the effective tone module. Keep tone rules compact and avoid repeating generic communication behavior.

Shared punctuation semantics live here; concrete tone targets that activate them should reference `plain_keyboard_punctuation` rather than copy the mapping.

## acceptance

A compliant tone changes style/register while preserving meaning, authority, structure semantics, selected depth, and any source/technical character fidelity required by the task.
