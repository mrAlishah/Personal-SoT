# Prompt Builder scenario acceptance cases

These are non-executable semantic review cases for
`system/assistant/prompt_builder_workflow.md`. They are not RED → GREEN test
evidence; executable reuse ordering is covered by
`system/tests/prompts/test_prompt_builder.py`.

## Adaptive use-case clarification

User asks for "a good prompt" without an outcome.

Expected: explain the short path, give two or three relevant examples and a
recommendation, offer "I don't know — recommend one", and ask one material
question rather than presenting a fixed schema questionnaire.

## Exact reuse

Explorer returns an active valid prompt that exactly satisfies the outcome.

Expected: stop at reuse, show beginner usage, and do not create or edit anything.

## Parameterized reuse

An existing prompt satisfies the outcome when its declared parameters are bound.

Expected: guide only the missing parameter values and do not create a new prompt.

## Composition

The outcome is satisfied by an existing prompt plus a profile, format, tone,
depth, or registered runtime control.

Expected: prefer composition. Runtime controls remain invocation configuration
and are not written into prompt frontmatter.

## Prompt-to-prompt inheritance

User proposes making one reusable prompt include or inherit another at runtime.

Expected: reject that structure; reuse a prompt directly, parameterize it, or
compose supported profile/presentation/control owners instead.

## Similar prompt with different ownership

A highly similar prompt exists but the requested meaning is not clearly the same
semantic owner.

Expected: similarity does not authorize overwrite. Explain edit versus new,
preview both effects when useful, and ask the user to choose.

## Durable Personal fact

User includes a durable employer, project state, or private preference in a
candidate reusable prompt.

Expected: do not copy the fact into the prompt. Route varying input to a
parameter and durable truth to independently resolved canonical context. If the
classification remains uncertain, stop before preview.

## Web client

A web client completes discovery and guided Builder questions but has no
repository write capability.

Expected: provide the same classification and complete preview, then state that
nothing was written and local validation was not run.

## End-to-end beginner journey

User describes a use case in natural language, reuses an exact or parameterized
prompt when one is sufficient, then asks for an outcome no current prompt owns.

Expected: Explorer searches canonical metadata without creating an inventory;
Builder proposes the minimum new prompt, shows the complete preview, and waits
for confirmation. A write-capable local agent re-checks the proposal, writes it,
runs prompt, core, and public validation, and reports their real result. A later
same-owner edit follows a new preview and confirmation. If the file changed
after preview, the edit stops without overwriting that change and asks for a new
proposal. This scenario is executable in
`system/tests/prompts/test_prompt_explorer_builder_e2e.py`; this Markdown file
remains review guidance, not RED → GREEN evidence.
