# Build or improve a reusable prompt

Tell the Personal SoT Assistant what result you want. You do not need to know
prompt files, metadata, or repository structure.

For example:

```text
Help me make a reusable prompt that compares two plans and explains the main
trade-offs. I don't know which format is best — recommend one.
```

The Assistant follows this path:

```text
[1 Understand the outcome]
→ [2 Search existing prompts]
→ [3 Reuse or customize if possible]
→ [4 Preview a new prompt only if needed]
→ [5 Confirm, write, and validate when supported]
```

It asks one useful question at a time and stops at the first option that works:

1. use an exact existing prompt;
2. fill in parameters for an existing prompt;
3. combine it with an existing profile, format, tone, depth, or control;
4. edit it only when it clearly has the same meaning and owner;
5. create the smallest new prompt.

Similarity alone never causes an existing prompt to be overwritten.

## Before anything is saved

For a new prompt or edit, the Assistant shows the complete proposed content and
change. Nothing is written until you confirm that preview.

A write-capable local agent then checks that the preview is still current,
writes the change, and runs prompt, core, and public safety validation. Its
report says separately whether the write happened and whether validation ran
and passed. If the file changed after the preview, the write stops so that the
newer content is not lost.

ChatGPT or Claude Web can guide the same flow and produce the same preview, but
must say that nothing was written and local validation was not run when they do
not have repository write access.

## Keep facts separate

A reusable prompt may describe a method or accept parameters. Durable facts
about you, an organization, or a project stay in their own Personal context and
are resolved separately. Do not copy secrets into either place.

## Advanced (optional)

After the beginner flow, you can ask for the canonical identity and expert
invocation:

```text
@do:prompt:<identity>
```

This syntax is optional and does not bypass confirmation, access rules, or
validation.
