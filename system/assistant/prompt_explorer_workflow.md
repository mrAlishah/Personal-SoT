# Prompt Explorer workflow

## Purpose

Help a beginner find and use an existing canonical prompt from a natural-language
use case. This workflow is read-only.

## Flow

```text
understand the use case in the selected language
→ ask one material question only when needed
→ translate supplied intent into a PromptQuery
→ run canonical Prompt Explorer discovery
→ recommend from returned evidence
→ show simple natural-language usage
→ offer optional Advanced identity/directive
```

Use `system/assistant/guided_flow_contract.md` for questions. Reuse supplied
answers, give short examples and an evidence-supported recommendation, and offer
"I don't know — recommend one" when uncertainty is reasonable.

## Query boundary

Use `system/prompts/explorer_contract.md` and the structured
`system/prompts/explorer.py` interface when executable repository tools are
available. A client that can inspect the same canonical files but cannot run the
helper follows the same contract directly.

The Assistant may translate user language into free-text query tokens and exact
filters only when current canonical evidence supports those values. It must not
invent an identity, path, tag, parameter, profile, format, tone, depth, alias, or
capability.

If the use case is too broad for a useful query, ask one adaptive question before
searching. Do not turn discovery into a fixed questionnaire.

## Recommendation

For each usable returned match, present:

```text
what it helps with
why it matches the use case
what information the user must provide
status or real capability limitation
one simple natural-language usage example
```

Use only identity and metadata returned by Explorer as match evidence. Load a
selected body only when rendering, execution, edit preview, or real capability
analysis needs it and access permits it.

Keep the canonical identity, path, matching metadata, and
`@do:prompt:<identity>` inside optional Advanced output.

## Status and unavailable results

- Recommend `active` prompts only when canonical validation and real capability
  checks allow it.
- Show `draft` only for explicit draft/edit/build discovery and label it
  non-executable.
- Show `deprecated` only for explicit lookup, warn, and do not recommend it for
  execution.
- Do not present invalid or unresolved prompts as usable. Explain availability at
  category level without exposing unselected bodies, secrets, or restricted data.

When no usable prompt exists, say so without guessing and offer
`system/assistant/prompt_builder_workflow.md` once that workflow is available.

## Client capability

Discovery does not require write confirmation. A client without canonical source
access reports that limitation instead of using stale memory. A no-write or web
client may still discover from accessible canonical metadata, but it must not
claim a write or local validation occurred.

## Acceptance

A compliant flow gives the same evidence-backed recommendation across clients,
uses the selected language, asks only material adaptive questions, teaches simple
usage before expert syntax, and never invents prompt authority or leaks content.
