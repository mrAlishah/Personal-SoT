---
control_id: clarify_risk
control_values:
  - "on"
  - "off"
  - "auto"
control_default: "auto"
---
# clarify_risk

## purpose

Control when unresolved ambiguity, conflict, or risk should stop dependent execution for explicit user clarification.

## control

The YAML frontmatter is the canonical machine-readable owner of this control's identity, allowed values, and global default. The runtime configuration key is derived as `controls.<control_id>`.

The general runtime-control contract is canonical in `system/behavior/control_contract.md`.

## contextual_default

Use contextual default `on` when no higher-precedence control value is supplied and either of these conditions is true:

```text
active factual scope == personal/projects/ai_source_of_truth
```

or the effective task uses any of these resolved behavior/task-intent classes:

```text
coding
review
planning
architecture
problem_solving
research
reasoning
```

This includes questions, requests, reviews, plans, investigations, problem-solving work, architecture discussions, and repository/system changes whose effective task intent clearly activates one of those behavior classes, even when the user did not name the behavior token literally.

Do not trigger this contextual default from incidental keyword occurrence alone. The behavior/task-intent classification must be genuinely applicable to the requested work.

For all other contexts, fall through to the global default defined by `control_default`.

Normal control precedence remains authoritative. In particular, an explicit current-prompt/session/project/profile value may override this contextual default according to `system/behavior/control_contract.md`.

## clarification_procedure

Whenever clarification is required:

1. stop the dependent execution path before writing or making the affected durable decision;
2. explain the ambiguity, conflict, or risk in ELI5-style plain language before technical detail;
3. state briefly why the unresolved point matters;
4. give the AI's recommended option when one is supportable, and identify it clearly as the recommendation;
5. present a small set of concrete choices, including an option for the user to provide a different/custom answer;
6. ask the minimum question needed to resolve the point;
7. do not continue the blocked part of the task until the user resolves it.

The ELI5 explanation is required as part of clarification behavior and does not require a separate presentation-format selection. It should remain concise and should not replace necessary technical detail when that detail affects the decision.

After resolution, continue the original task from that decision boundary. No separate pause/resume state machine is required.

## semantics

### on

`on` is the conservative mode used explicitly or by the contextual default above.

Ask before dependent execution whenever a genuine unresolved ambiguity, conflict, or risk could change factual meaning, canonical ownership, stored value, scope, authority, privacy/security exposure, durable state, architecture, destructive action, or create meaningful rework.

For context maintenance specifically, conflicting values, unclear units/labels, uncertain identity/relationship, unclear date/source, or ambiguity about which fact the user intends to persist are clarification candidates when the difference would affect the canonical record.

Do not ask about trivial wording, cosmetic preferences, or uncertainty that cannot materially change the stored/resulting meaning. When clarification is required, use the canonical clarification procedure above.

### auto

`auto` is the general adaptive default outside the conservative contexts above.

Stop only when the unresolved ambiguity/conflict/risk can materially change correctness, authority, destructive or irreversible action, security/privacy exposure, durable architecture, canonical state, or the resulting implementation path.

For minor, safely reversible, non-blocking uncertainty, continue using the best-supported minimal safe assumption when ordinary reasoning/communication contracts allow it.

When `auto` decides clarification is required, use the canonical clarification procedure above.

### off

When effective `clarify_risk = off`, do not stop solely because of ordinary ambiguity or risk covered by this optional control. Continue using the best-supported safe assumption when existing contracts allow it.

`off` never bypasses:

```text
external mandatory constraints
host/tool permissions
required authorization
applicable hard policies
safety/security boundaries
explicit fail-closed contracts
```

If any of those independently require stopping or obtaining user input, they remain authoritative.

## boundaries

General analytical ambiguity detection remains in `reasoning.md`.
General collaboration and clarification behavior remains in `communication.md`.
Repository execution discipline remains in `coding.md`.
The clarification procedure may use ELI5-style language, but `clarify_risk` does not otherwise own response presentation, tone, depth, or language.

The behavior names in `contextual_default` are selectors for this control's default only; their operating semantics remain owned by their respective behavior modules.

## migration

The prior boolean model maps conceptually as:

```text
true  → on
false → off
```

Runtimes should not silently coerce legacy boolean prompt/config values after the migration boundary; validators and runtime syntax should require canonical values.

## acceptance

A compliant runtime resolves this control using its canonical metadata and semantics, applies the contextual `on` default for the `ai_source_of_truth` Personal project and the listed high-deliberation behavior/task-intent classes, respects higher-precedence explicit/project/profile values, asks about genuine meaning-changing ambiguity/conflict/risk while ignoring trivial uncertainty, uses ELI5 + recommendation + concrete choices whenever clarification is required, preserves higher mandatory boundaries, and resumes the original task after the user resolves the decision boundary.
