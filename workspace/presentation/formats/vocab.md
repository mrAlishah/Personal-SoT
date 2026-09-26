---
format_id: vocab
placement: suffix
---
# vocab

## purpose

Append a compact vocabulary-and-phrases summary at the end of the response, primarily for language learning, English/German translation, and multilingual terminology review.

## placement

It is rendered after the main answer body and after any prefix formats such as `yaml`.

If multiple suffix formats are active, preserve their effective format order.

## canonical_output

Use this Markdown shape:

```markdown
**واژگان**

| Deutsch | English | فارسی | Wortart | اطلاعات تکمیلی |
| --- | --- | --- | --- | --- |
| sicher sein | be sure | مطمئن بودن | verb phrase | معمولاً با `if / whether` می‌آید |
| jemandes Namen richtig verstehen | get someone's name right | اسم کسی را درست متوجه شدن | verb phrase | عبارت طبیعی در مکالمه |
| buchstabieren | spell | هجی کردن، درست نوشتن | v | principal forms when useful |
```

When German is not materially present in the response, preserve the same columns and use `—` rather than inventing a German equivalent merely to fill the table.

## rules

- always place the vocabulary appendix at the end when `vocab` is active;
- summarize only useful English/German words, expressions, idioms, collocations, phrases, or terminology materially present in or taught by the current response;
- when a German word or phrase is materially taught or used, include its English and Persian equivalents in the same row;
- do not annotate every German occurrence inline in the main answer; the appendix is the canonical compact multilingual surface unless the task itself requires inline translation;
- do not attempt to list every word in the answer;
- prioritize pedagogically useful or reusable items;
- keep one semantic item per row;
- preserve exact English/German spelling;
- for German nouns, include article/plural where materially useful;
- for verbs, include relevant principal forms or usage notes when useful;
- use concise `Wortart` values such as `n`, `v`, `adj`, `adv`, `phrase`, `verb phrase`, `phrasal verb`, `idiom`, or `collocation`;
- use `—` when a field is genuinely not applicable rather than inventing information;
- normally include roughly 3–12 high-value rows depending on task size/depth; a short translation may legitimately contain fewer;
- local explanations/notes may follow the primary response language;
- `vocab` does not activate teaching behavior by itself.

## scope_of_use

Typical high-value use cases:

```text
English translation
German translation
German/English learning
workplace phrases
idioms/collocations
conversation correction
multilingual terminology review
```

For non-language conceptual learning, prefer `@fmt:concept` instead of filling a vocabulary table with technical concepts that are better represented conceptually.

## composition

`yaml` does not transform this table into YAML records.

Canonical combinations:

```text
yaml + vocab
→ YAML frontmatter + answer + vocabulary table

md + vocab
→ Markdown body + vocabulary table

yaml + md + vocab
→ YAML frontmatter + Markdown body + vocabulary table
```
