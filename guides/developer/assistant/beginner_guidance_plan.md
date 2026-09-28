# Beginner guidance implementation

Implement the existing Assistant and guided-flow contracts and
`system/tests/assistant/beginner_guidance_cases.md`; introduce no new semantic
framework, registry, category-selection requirement or write pipeline.

## Gaps and bounded approach

The primary `sot/assistant` prompt still asks empty-request users to choose
categories. User navigation also presents categories first. Existing Prompt
Explorer, Personalization Advisor and Profile Builder already own discovery,
composition and safe writes; reuse them.

The Assistant interprets the user's language using its existing contract.
A small read-only guidance helper consumes that classification (a canonical
PromptQuery or PersonalizationIntent), returns evidence-backed next steps,
and keeps trial composition nonpersistent. It is not a second language parser.
Actual Preview and Apply stay with the selected workflow/Builder.

## Loops

1. Implement read-only guidance helpers and tests for uncertainty, internally
   selected routes, explain/recommend clarity, trial-before-save and reuse.
   Implement bounded improvement inspection of explicitly selected capabilities
   (at most three), without context reads or repairs.
2. Wire the one Assistant entry point to these helpers and existing workflows;
   update beginner docs and examples in English and Persian. Verify real Profile
   preview/confirm/apply/validation and no-write behavior through the existing
   Builder rather than reimplementing it.
3. Run the full executable suite and three validators, independent branch
   review, RED/GREEN on actual findings, then publish a reviewable PR.

Executable tests verify helper routing/effects and real Builder integration.
They do not claim to measure a live model's language understanding. Markdown
cases remain acceptance specifications; client conversation quality requires
live observation separately.
