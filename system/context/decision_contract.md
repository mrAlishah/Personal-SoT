# decision_artifact_contract

## purpose

Defines durable decision artifacts used as deeper evidence behind current canonical state.

Decision artifacts preserve why an important choice was made without forcing historical rationale into normal runtime context.

## location

Decisions live under the scope that owns them:

```text
workspace/context/personal/projects/<project>/decisions/
workspace/context/organizations/<organization>/decisions/
workspace/context/organizations/<organization>/projects/<project>/decisions/
```

Use organization-level decisions only for decisions genuinely governed at organization scope.

## role

A decision artifact is historical/rationale evidence.

It is not normally the primary source for current effective state.

Current effective truth belongs in the appropriate canonical module, for example:

```text
architecture.md
stack.md
constraints.md
current_state.md
```

A resolver may load a related decision when deeper rationale, trade-offs, or historical reasoning is required.

## filename

Decision filenames use descriptive lowercase snake_case.

Example:

```text
use_event_driven_reconciliation.md
migrate_primary_database.md
```

V1 does not require duplicate decision IDs when canonical path already provides stable identity.

## metadata

Decision status materially affects interpretation and cannot be derived from path, so it is explicit.

Minimum form:

```yaml
---
ai_access: allow
decision_status: accepted
---
```

Canonical V1 statuses:

```text
proposed
accepted
superseded
deprecated
```

Unknown or malformed status should be treated as unresolved lifecycle state rather than guessed.

## canonical_sections

A decision artifact should remain compact and use only sections that add durable value.

Recommended structure:

```markdown
# decision_title

## decision

The chosen direction.

## context

The problem or constraint that made the decision necessary.

## consequences

Material trade-offs, constraints, or follow-up effects.
```

Optional when materially useful:

```text
## alternatives
## evidence
## supersession
```

Do not add empty sections for template symmetry.

## current_truth_rule

When an accepted decision changes current project truth, update the relevant current canonical module as well.

Example:

```text
decision:
use postgresql

current canonical state:
stack.md → database = postgresql
```

This is not prohibited duplication because the two artifacts have different semantic responsibilities:

```text
stack.md
→ what is true now

decision artifact
→ why the choice was made
```

The decision artifact must not be used as the only source of current state when a dedicated current module owns that fact.

## supersession

When a decision is replaced:

- mark the old artifact `decision_status: superseded`;
- create or identify the newer authoritative decision when rationale is still useful;
- update current canonical modules to reflect the new effective truth;
- do not delete useful historical rationale solely because it is no longer current.

A superseded decision is deep evidence, not current authority.

## proposed_decisions

`proposed` decisions are candidates, not current canonical truth.

They MUST NOT override accepted current architecture, stack, constraints, or policies merely because they are newer.

## deprecated_decisions

`deprecated` indicates the decision should no longer guide new work but may remain useful for historical understanding.

Deprecated decisions are normally excluded from ordinary runtime context unless the task explicitly requires historical analysis.

## access

Decision artifacts follow `system/context/access_contract.md`.

An inaccessible decision does not authorize exposing its rationale through summaries or provenance.

## progressive_disclosure

Decision artifacts are normally lower-priority context than current authoritative modules.

Typical loading:

```text
architecture question
→ architecture.md + constraints.md + stack.md

architecture question requiring rationale
→ above + relevant accepted decision artifact

historical analysis
→ relevant accepted/superseded/deprecated decisions as needed
```

Context budget should prune unnecessary historical evidence before pruning current authoritative facts or mandatory policies.

## acceptance

A compliant decision artifact makes it clear:

- which scope owns the decision;
- whether it is proposed, accepted, superseded, or deprecated;
- what was decided;
- why it was decided when rationale matters;
- where current effective truth should be read;
- whether the artifact should normally be loaded for the current task.
