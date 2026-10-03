# Personalization workflow

## Purpose

Help a beginner customize response behavior and presentation from ordinary
language without requiring Profile names, directives, registries, or paths.

## Flow

```text
understand the desired experience
→ classify each requested semantic lane
→ discover current canonical capabilities
→ recommend the smallest existing composition
→ try/use it invocation-locally when persistence is not required
→ show a simple usage example
→ offer Profile saving only for a valuable repeated combination or explicit save request
```

Follow `guided_flow_contract.md`: use the selected language, show compact
progress, ask one material adaptive question at a time, provide examples and a
recommendation, and offer “I don't know — recommend one” when useful.

## Classification

```text
shorter / more detailed response → depth
formal / human / neutral register → tone
table / document / learning appendix → format
optional learning, clarification, step flow → registered control
research, teaching, coding method → behavior selected through a Profile
reusable combination defaults → Profile
```

This is invocation-local interpretation, not an alias table. Convert intent to
exact query fields, then accept only identities and values returned from
canonical discovery. Never guess a nearest identity.

## Reuse order

```text
exact existing Profile
→ direct existing format/tone/depth/control composition
→ existing Profile plus existing overrides
→ Profile customization for the clear same semantic owner
→ new Profile only for a repeated reusable combination
```

Examples:

- “Make answers shorter” recommends the current `short` depth.
- “Answer more formally” recommends the current `formal` tone.
- “Use a comparison table” recommends the current `compare` format.
- “Teach step by step” may compose `g.technical.learning` with canonical
  `learning=on` and `step_execution=on` controls.
- “Deep professional research” reuses `g.research` when its current manifest
  supplies that composition.

Direct `formal + short` composition does not justify a new Profile by itself.

## Try before save

A beginner customization normally starts as an invocation-local composition of existing capabilities. Do not create a Profile merely to let the user experience a tone/depth/format/control combination once.

After the user has tried the composition, offer persistence only when one of these is true:

- the user explicitly asks to save it;
- the same combination is clearly intended as a repeated default;
- a reusable Profile materially reduces repeated configuration.

If persistence is not justified, keep the customization transient and explain that no canonical configuration was changed. A saved Profile still follows reuse-before-create, preview, explicit confirmation, stale-state checks, authorization, write, and validation.

## Ownership and write boundary

Format, tone, depth, control, and behavior are discover/compose-only here. Do
not create or edit their targets, registry mappings, metadata, contracts, or
precedence. Only `workspace/profiles/<name>.md` may enter the flow defined by
`system/assistant/profile_builder_workflow.md` and the canonical safe-write
contract.

Profiles contain component identities and defaults only. Durable Personal or
project facts, context paths, copied module instructions, policies, adapter
wiring, and secrets stay out.

## Beginner and Advanced output

Lead with the outcome and a natural-language example. After that, Advanced may
show exact optional syntax such as:

```text
@profile:g.research
@fmt:compare
@tone:formal
@depth:short
@control:learning=on
```

## Client capability

Discovery and composition are read-only. Web/no-write clients may complete
them. If Profile saving is proposed, they show the same complete preview but
state that nothing was written and validation was not run there.
