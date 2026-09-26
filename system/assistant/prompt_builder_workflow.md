# Prompt Builder workflow

## Purpose

Help a beginner reuse, customize, edit, or create a reusable prompt while
preserving canonical identity, semantic ownership, fact separation, and the
Assistant safe-write boundary.

## Flow

```text
understand the desired outcome
→ discover current canonical prompts
→ classify required input, presentation, controls, and factual context
→ choose the first sufficient reuse rung
→ ask only for material gaps
→ show usage or a complete safe-write preview
```

Use `system/assistant/guided_flow_contract.md`: explain the short path, show
compact progress, ask one adaptive question at a time, provide relevant examples
and an evidence-supported recommendation, and offer "I don't know — recommend
one" when useful.

## Reuse-before-create

Use `system/prompts/explorer_contract.md` and current Explorer results. Pass
evidence to `system/prompts/builder.py` in this order:

```text
exact existing prompt
→ usable existing prompt with parameters
→ supported composition/customization
→ edit the same semantic prompt
→ create only when every earlier rung is insufficient
```

Stop at the first rung that satisfies the user's outcome. Do not invent an
identity or capability to force reuse.

## Composition boundary

Composition may use declared parameters and existing profiles, formats, tone,
depth, and registered runtime controls. Runtime controls apply at invocation and
must not be added to prompt frontmatter unless Prompt Contract is separately
changed.

Prompt-to-prompt runtime include, inheritance, or dependency composition remains
unsupported.

## Edit boundary

High similarity never authorizes overwrite. Edit only when the requested change
belongs to the same canonical prompt identity and semantic owner. When edit
versus new remains materially ambiguous, explain both effects and ask the user to
choose before producing a write proposal.

## Fact and context boundary

```text
reusable varying input → declared parameter
durable factual truth  → independently selected canonical context
presentation behavior → existing profile/format/tone/depth/control
```

Do not put durable Personal, organization, or project facts into reusable prompt
frontmatter or body. If a candidate fact cannot be classified safely, stop before
preview and ask the minimum useful question.

## Write boundary

Explorer and reuse/composition are read-only. A justified create or edit follows
`system/assistant/safe_write_contract.md`:

```text
classify and reconcile identity/ownership
→ detect duplication/conflict
→ build the minimum prompt change
→ preview complete content and diff
→ explicit confirmation
→ re-read/version check
→ authorized write
→ strongest relevant validation
→ truthful report
```

Deletion is outside this workflow.

## Client capability

Local agents may apply a confirmed proposal only with actual repository write
and command capability. Web/read-only clients use the same discovery,
classification, questions, and preview, then explicitly state that nothing was
written and validation was not run there.

Adapters declare capability only and never copy this decision order.

## Acceptance

A compliant Builder guides a beginner without requiring paths or schemas,
reuses before creation, edits only a clear semantic owner, keeps facts separate,
preserves prompt composition boundaries, and sends every material write through
one client-neutral safe-write flow.
