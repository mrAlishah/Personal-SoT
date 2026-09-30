# Find and use an existing prompt

Tell the Personal SoT Assistant what you want to accomplish. You do not need to
know prompt names, folders, tags, or special commands.

For example:

```text
Find a prompt that can review a code change and explain the biggest risks.
```

The Assistant will:

```text
[1 Understand your use case]
→ [2 Search current prompts]
→ [3 Recommend a match]
→ [4 Show how to use it]
```

If one detail materially changes the recommendation, the Assistant asks one
question and provides examples, a recommendation, and an "I don't know —
recommend one" option.

## What you will see

The default result explains:

- what the prompt helps with;
- why it matches your request;
- what information you need to provide;
- whether it is currently usable;
- one simple natural-language usage example.

Discovery is read-only and does not need confirmation. An invalid, incomplete,
draft, or deprecated prompt is never presented as a normal executable
recommendation.

If no usable prompt exists, the Assistant says so instead of inventing one and
offers the [guided Prompt Builder](build_a_prompt.md). The Builder searches
again, prefers parameters and supported customization, and creates something
new only when those options cannot satisfy the use case.

## Advanced (optional)

After the beginner explanation, you may ask to see the exact canonical identity,
matching metadata, or expert invocation:

```text
@run:<identity>
```

Expert syntax is optional. It does not bypass prompt validation, required input,
context access, or client capability.
