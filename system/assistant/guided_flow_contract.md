# Guided flow contract

## Purpose

Define one predictable beginner interaction pattern for Assistant workflows without turning every workflow into a static questionnaire.

## Flow

```text
understand the goal or uncertainty
→ explain the short path or recommendation boundary
→ show compact progress when useful
→ ask one useful question only when it changes the result
→ adapt from the answer
→ review the understood result
→ preview any material change
→ confirm when required
→ apply only when capable and authorized
→ validate when the resolved change policy requires
→ teach or suggest one next-best useful request when a clear continuation exists
```

## Question shape

When the answer is not obvious, a guided question contains only what helps the user answer:

- a short plain-language explanation;
- two or three relevant examples;
- a recommended answer when evidence supports one;
- a way to accept, change, or provide a custom answer;
- `I don't know — recommend one` when a beginner may reasonably be unsure.

Ask one question at a time. Reuse answers already supplied and skip questions whose answers do not affect the result. Follow-up questions are generated from the task and previous answers rather than a fixed universal questionnaire.

Do not ask a beginner to select an internal Assistant category, Profile, module path, or directive when the stated goal already determines the route. If the user explicitly says they do not know what to choose, provide the safest evidence-backed recommendation rather than repeating the same choice back to them.

## Action clarity

At material boundaries, make the current effect understandable in ordinary language:

```text
Explain → Recommend → Preview → Apply
```

Not every task uses every level. Read-only help may stop at Explain or Recommend. A Preview is still non-mutating. Apply requires explicit confirmation where the safe-write contract requires it plus real host authorization/capability.

## Progress

Show a compact schematic at meaningful boundaries, for example:

```text
[1 Goal ✓] → [2 Current state ←] → [3 Review] → [4 Create]
```

Progress is orientation, not a promise of a fixed number of questions. Update it when the flow adapts.

## Language and identifiers

Questions, explanations, examples, recommendations, warnings, and reports use the selected language. Canonical identifiers remain `lowercase_snake_case`. Present the friendly label first and the internal identifier only in review/preview or optional advanced help.

## Trial before persistence

When a customization can be used invocation-locally without changing canonical state, prefer trying the existing composition first unless the user explicitly asks to persist it. Persistence is offered only when the combination is genuinely reusable or the user asks to save it. The Personalization workflow owns the exact reuse/save order.

## Ambiguity

Do not turn uncertainty into canonical truth. Explain the ambiguous point, why it affects the result, the available options and trade-offs, and the recommended option when supportable. Continue unaffected parts only when doing so cannot create a misleading partial write.

## Acceptance

A compliant guided flow keeps the user oriented, does not require internal-category knowledge, asks only material adaptive questions, gives a recommendation when the user cannot reasonably choose, makes Explain/Recommend/Preview/Apply effects clear, prefers transient trials before unnecessary persistence, and completes with a clear result, one useful continuation when appropriate, or a truthful capability limitation.
