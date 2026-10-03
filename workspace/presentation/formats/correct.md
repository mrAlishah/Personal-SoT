---
format_id: correct
placement: body
---
# correct

## purpose

Render language corrections inline while preserving the user's original sentence and making each actual correction visually explicit.

## activation

This format is rendered only when selected by profile, prompt, adapter/project default, or `@fmt:correct` and when a real correction candidate exists.

If the input is already correct, omit the correction block.

## output_shape

Preserve the original sentence structure and mark each corrected span inline:

```markdown
~~incorrect~~ **correct**
```

Example:

```markdown
I ~~am agree~~ **agree** with you.
```

For multiple independent mistakes, mark each affected span in place rather than replacing the whole sentence when practical.

## rules

- preserve as much of the original sentence as possible;
- use `~~...~~` only for text that is actually incorrect in the intended meaning/register;
- place the correction immediately after the incorrect span using `**...**`;
- do not mark valid colloquial or informal wording as wrong merely because a more formal alternative exists;
- do not use this format for pure stylistic rewrites unless the user explicitly asks for polishing;
- when a sentence requires substantial restructuring and inline marking would become misleading, show the closest faithful inline correction first and optionally a separate concise natural version only when useful;
- keep punctuation/capitalization corrections proportional; avoid noisy markup for trivial typography unless it affects correctness or the user asks for full correction;
- correction markup precedes translations/replies when composed with multilingual chat behavior;
- do not add grammar explanations unless explicitly requested or another effective behavior requires them.

## boundaries

This format owns correction representation only. Error detection/correction intent belongs to the active language behavior; translation, replies, tone, depth, and vocabulary are owned elsewhere.

## acceptance

A compliant response preserves the user's original sentence, marks genuine errors with strikethrough and their corrections in bold inline, omits correction markup when no real error exists, and avoids turning stylistic preference into false error reporting.