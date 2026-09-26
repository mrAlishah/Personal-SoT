---
format_id: concept
placement: suffix
---
# concept

## purpose

Append a compact concept-summary table at the end of the response for non-language learning, technical explanation, analysis, and knowledge-review tasks.

The format also surfaces the most useful relationship or distinction for concepts that are commonly confused with nearby concepts.

## placement

Render it after the main answer body and after any prefix formats such as `yaml`.

If multiple suffix formats are active, preserve their effective format order.

## output_shape

Use this Markdown structure:

```markdown
**مفاهیم**

| Concept | Definition | Related / Distinct From | Simple Example |
| --- | --- | --- | --- |
| <canonical concept name> | <concise definition> | <closest useful relationship or distinction> | <simple concrete example> |
```

Use `—` in `Related / Distinct From` when no nearby concept is materially useful; do not invent a comparison merely to fill the column.

## rules

- summarize only concepts materially used or taught in the current response;
- prefer canonical English technical names for `Concept` when one exists;
- localize `Definition`, `Related / Distinct From`, and `Simple Example` to the response's active primary language;
- keep definitions short but semantically correct;
- when a concept has a commonly confused sibling/parent/child/alternative materially relevant to the response, state the decisive distinction compactly;
- prefer one high-value relationship/distinction over a long taxonomy;
- use concrete examples rather than repeating the definition;
- preserve acronyms and exact technical names;
- avoid filler concepts added only to make the table longer;
- normally include roughly 3–12 high-value concepts depending on response depth and task size;
- for a very small response, a smaller table is valid;
- do not replace the main explanation with the concept appendix.

## relationship_boundary

This format summarizes relationships already established or supportable from the answer. It does not require exhaustive ontology, concept-family enumeration, or unrelated comparisons.

If explaining the distinction materially affects understanding, the main body should explain it first; this table then compresses it.

## boundaries

`concept` summarizes conceptual content already present in the answer. It does not activate teaching/research behavior, broaden factual scope, or introduce unsupported claims.
