---
control_id: learning
control_values:
  - "on"
  - "off"
  - "auto"
control_default: "auto"
---
# learning

## purpose

Control whether the runtime should intentionally optimize ordinary work for user learning and knowledge transfer.

## control

The YAML frontmatter is the canonical machine-readable owner of this control's identity, allowed values, and global default. The runtime configuration key is derived as `controls.<control_id>`.

The general runtime-control contract is canonical in `system/behavior/control_contract.md`.
The reusable pedagogy method remains canonical in `system/behavior/teaching.md`.

## semantics

### on

Intentionally apply learning-oriented behavior when the response contains non-trivial concepts, decisions, mechanisms, trade-offs, or procedures that the user can reasonably learn from.

When `learning = on`, the runtime MUST make the `teaching` behavior capability effective for the invocation even when the selected profile did not explicitly list `teaching`.

Do not inflate trivial operational answers merely to demonstrate teaching behavior. Keep explanation proportional to the task and selected presentation depth.

### off

Suppress optional learning-oriented teaching behavior for the invocation, including `teaching` selected by a profile solely as part of its learning-first defaults.

A profile may still list `teaching` so that it is self-contained when learning is enabled; `learning = off` is the runtime gate that makes such optional profile teaching ineffective for the invocation.

Still explain information required for correctness, safety, informed consent, or completion of the user's request. `off` is not permission to become cryptic or omit required rationale.

If the user explicitly asks to learn, understand, explain, teach, compare concepts, or otherwise requests pedagogy in the ordinary prompt body, that explicit task intent outranks the optional learning gate and may require teaching even when the effective control value is `off`.

### auto

Apply learning-oriented behavior when teaching materially improves the user's ability to understand, reuse, maintain, evaluate, or safely execute the result.

When `auto` decides teaching is useful, make the `teaching` capability effective for the invocation even if it was not selected explicitly. When `auto` decides teaching is not useful, do not retain profile-selected `teaching` merely because a learning-first profile listed it as a default capability.

Prefer teaching for:

```text
new or subtle concepts
important terminology or distinctions
architecture/design trade-offs
non-obvious code or system behavior
high-leverage mental models
procedures where understanding reduces future error
```

Prefer ordinary concise execution for trivial lookups, confirmations, or low-learning-value operational requests unless the user asks for explanation.

## presentation_boundary

This control does not own YAML openings, ELI5/ELI10 style, vocabulary tables, summaries, tone, language, or response depth.

Those remain presentation/profile configuration. A presentation module may remain selected while learning is off; the runtime should apply it only within its own contract and without reintroducing suppressed teaching scaffolding.

## behavior_boundary

`learning` is a runtime gate over optional learning-oriented application of `teaching`. The pedagogy itself remains in `teaching.md` and should not be duplicated here.

The gate does not suppress explanations independently required by other behavior modules, explicit user task intent, mandatory constraints, or safety/correctness requirements.

## acceptance

A compliant runtime resolves this control using its canonical metadata and semantics, makes `teaching` effective when `on` requires it, suppresses optional profile-selected teaching when `off` requires it, adaptively gates teaching under `auto`, respects explicit user learning requests, and does not silently own presentation configuration.
