# v1_tone_punctuation_cases

These scenarios validate the shared `plain_keyboard_punctuation` tone rule and its boundaries.

## case_01_human_em_dash

Active tone: `human`.

Generated prose candidate:

```text
Thanks for your help — I really appreciate it.
```

Expected generated prose:

```text
Thanks for your help - I really appreciate it.
```

## case_02_professional_em_dash

Active tone: `professional`.

Expected: ordinary generated prose uses `-` rather than em dash `—` or en dash `–` as a prose separator.

## case_03_plain_typographic_punctuation

Active tone: `human` or `professional`.

Expected normalization in ordinary generated prose:

```text
— → -
– → -
… → ...
“ ” → "
‘ ’ → '
```

## case_04_formal_not_forced

Active tone: `formal`.

Expected: `plain_keyboard_punctuation` is not automatically activated by the tone contract.

## case_05_neutral_not_forced

Active tone: `neutral`.

Expected: `plain_keyboard_punctuation` is not automatically activated by the tone contract.

## case_06_quoted_source_fidelity

Active tone: `human`.

Source quotation contains an em dash or smart quotes.

Expected: preserve exact source characters when quotation fidelity matters; do not rewrite the quoted source merely because the active tone uses plain keyboard punctuation.

## case_07_code_and_identifiers

Active tone: `professional`.

Code, command, URL, filesystem path, filename, identifier, or structured data contains punctuation/symbols.

Expected: preserve technically significant characters exactly.

## case_08_language_characters

Active tone: `human`.

Response contains Persian punctuation, German umlauts, accented letters, or other language-correct characters.

Expected: preserve them. The rule is not ASCII-only output.

## case_09_technical_notation

Active tone: `professional`.

Response requires mathematical or technical symbols such as `≤`, `≥`, `≠`, or a semantically meaningful arrow in technical notation.

Expected: preserve the technically meaningful symbol.

## case_10_decorative_unicode

Active tone: `human` or `professional`.

A decorative Unicode punctuation/symbol is used only for styling and has a clearer plain keyboard equivalent.

Expected: prefer the plain keyboard representation.

## case_11_correctness_over_normalization

Plain-punctuation normalization would change source meaning, technical correctness, or required literal output.

Expected: fidelity/correctness wins; do not normalize the character.
