# Prompt Explorer scenario acceptance cases

These are non-executable semantic review cases for
`system/assistant/prompt_explorer_workflow.md`. They are not RED → GREEN test
evidence; executable discovery behavior is covered by
`system/tests/prompts/test_prompt_explorer.py`.

## Selected language

User asks in Persian for a prompt that reviews code.

Expected: questions, recommendation, explanation, usage, and warnings are in
Persian while canonical identifiers remain unchanged in optional Advanced.

## One adaptive question

User asks only for "a writing prompt" and the intended outcome changes which
prompt is useful.

Expected: explain the short discovery step, give relevant examples and a
recommendation, offer "I don't know — recommend one", and ask one material
question rather than a fixed questionnaire.

## Evidence-backed recommendation

Explorer returns one active valid prompt whose current tags and parameters match
the requested use case.

Expected: recommend it using only returned identity/metadata evidence; do not
invent a capability, tag, parameter, alias, or factual scope.

## Beginner usage first

One prompt is recommended.

Expected: show what it helps with, why it matches, what input is needed, and one
natural-language example. Hide its path and `@do:prompt:...` under Advanced.

## Draft

User explicitly asks to find a draft for editing.

Expected: the draft may be shown with a draft limitation and is not presented as
executable.

## Deprecated

User explicitly asks for a deprecated prompt by exact identity.

Expected: show it only with a deprecation warning and do not recommend execution.

## Invalid or unresolved candidate

A ranked prompt fails canonical validation or has an unresolved reference.

Expected: do not present it as executable/recommended; give only a safe category-
level availability message without body, secret, or restricted-context content.

## No canonical match

Explorer returns no usable prompt.

Expected: say no current canonical match was found, do not invent an identity,
and offer the Prompt Builder workflow.

## Read-only client

A web client can inspect current prompt metadata but cannot write or run local
commands.

Expected: discovery and recommendation remain available from accessible evidence;
the client does not imply that it wrote anything or ran local validation.

## Inaccessible source

The client cannot access the canonical prompt files.

Expected: report the discovery limitation and provide connection guidance rather
than guessing from memory.
