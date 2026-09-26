---
format_id: learning_summary
placement: suffix
---
# learning_summary

## purpose

Append a compact learning-focused summary of the most reusable points taught or clarified in a non-trivial response.

## activation

This format is rendered only when explicitly selected by profile, prompt, adapter/project default, or `@fmt:learning_summary`.

When active, omit the appendix for trivial acknowledgements, isolated factual lookups, or responses where no meaningful learning point was developed.

## placement

Render it after the main answer body. When multiple suffix formats are active, preserve their effective format order.

## output_shape

Use a compact localized heading such as:

```markdown
**خلاصه‌ی یادگیری**

- <reusable point>
- <important distinction>
- <practical implication>
```

Normally include about 2–6 high-value points depending on task size and selected depth.

## rules

- summarize what the user should retain, not the chronology of the response;
- prioritize mental models, distinctions, rules, trade-offs, and reusable operational insights;
- do not introduce new facts or recommendations in the summary;
- avoid repeating sentences verbatim from the body;
- preserve exact technical names when they matter;
- keep each point independently understandable;
- do not use the appendix to compensate for an unclear main answer.

## boundaries

`learning_summary` is presentation only. It does not activate `teaching`, broaden factual scope, change depth, or modify runtime controls.

When another lane such as `controls.learning` reduces or suppresses teaching, this format summarizes only meaningful learning content that still exists in the effective response; it does not recreate suppressed teaching by itself.

## acceptance

A compliant response with `learning_summary` active ends with a compact set of genuinely reusable learning points when educational content exists and omits the appendix when it would add no value.
