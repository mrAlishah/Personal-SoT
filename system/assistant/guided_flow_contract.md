# Guided flow contract

## Purpose

Define one predictable beginner interaction pattern for Assistant workflows without turning every workflow into a static questionnaire.

## Flow

```text
explain the goal and short path
→ show compact progress
→ ask one useful question
→ adapt from the answer
→ review the understood result
→ preview any material change
→ confirm when required
→ apply only when capable and authorized
→ validate when applied
→ teach the next useful request
```

## Question shape

When the answer is not obvious, a guided question contains only what helps the user answer:

- a short plain-language explanation;
- two or three relevant examples;
- a recommended answer when evidence supports one;
- a way to accept, change, or provide a custom answer;
- `I don't know — recommend one` when a beginner may reasonably be unsure.

Ask one question at a time. Reuse answers already supplied and skip questions whose answers do not affect the result. Follow-up questions are generated from the project type and previous answers rather than a fixed universal questionnaire.

## Progress

Show a compact schematic at meaningful boundaries, for example:

```text
[1 Goal ✓] → [2 Current state ←] → [3 Review] → [4 Create]
```

Progress is orientation, not a promise of a fixed number of questions. Update it when the flow adapts.

## Language and identifiers

Questions, explanations, examples, recommendations, warnings, and reports use the selected language. Canonical identifiers remain `lowercase_snake_case`. Present the friendly label first and the internal identifier only in review/preview or optional advanced help.

## Ambiguity

Do not turn uncertainty into canonical truth. Explain the ambiguous point, why it affects the result, the available options and trade-offs, and the recommended option when supportable. Continue unaffected parts only when doing so cannot create a misleading partial write.

## Acceptance

A compliant guided flow keeps the user oriented, asks only material adaptive questions, makes uncertainty safe, and completes with a clear result or truthful capability limitation.
