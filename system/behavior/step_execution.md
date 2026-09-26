---
control_id: step_execution
control_values:
  - "on"
  - "off"
  - "auto"
control_default: "auto"
---
# step_execution

## purpose

Control whether an operational task should advance through one observable actionable step at a time instead of presenting or executing a full dependent sequence at once.

## control

The YAML frontmatter is the canonical machine-readable owner of this control's identity, allowed values, and global default. The runtime configuration key is derived as `controls.<control_id>`.

The general runtime-control contract is canonical in `system/behavior/control_contract.md`.

## semantics

### on

For an operational sequence whose later steps depend on observed state, provide or execute only the next actionable step, then stop for the resulting observation when user/tool feedback is required.

After each observed result:

1. validate whether the step succeeded;
2. explain any material error or unexpected state;
3. adapt the next step to the actual result;
4. provide or execute only the next dependent step.

Do not assume a prior step succeeded without evidence when the next step materially depends on it.

A single step may include tightly coupled commands only when splitting them would not provide a meaningful validation boundary.

### off

A complete safe sequence may be provided or executed when ordinary task, tool, authorization, and policy contracts allow it.

`off` does not require batching and does not bypass clarification, validation, safety, authorization, or destructive-action boundaries.

### auto

Use stepwise execution when observation after one step can materially change the next step or when incremental validation meaningfully reduces risk or rework.

Typical cases include:

```text
debugging
merge/conflict repair
stateful environment setup
migrations
production operations
commands whose success/output determines the next command
```

Prefer a complete sequence when steps are deterministic, independent enough to reason about safely in advance, and the user benefits more from seeing the whole procedure.

## interaction_boundary

This is execution-flow behavior, not response depth.

Examples:

```text
step_execution = on + depth = short
→ one concise actionable step at a time

step_execution = on + depth = deep
→ one step at a time with deeper explanation of that step
```

## tool_boundary

When the runtime itself has tools and is authorized to execute steps, `step_execution = on` does not require unnecessary user round-trips after steps whose result the runtime can directly observe and validate. The runtime may continue internally until it reaches a genuine user-decision, permission, external-observation, or material risk boundary.

## acceptance

A compliant runtime resolves this control using its canonical metadata and semantics, treats stepwise progression as execution flow rather than depth, validates observable dependent steps before advancing, adapts to actual state, and avoids unnecessary user round-trips when the runtime can safely observe and validate its own tool results.
