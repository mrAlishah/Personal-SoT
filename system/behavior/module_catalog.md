# behavior_module_catalog

## purpose

Defines the canonical V1 behavior modules and their semantic responsibilities.

The catalog defines reusable capability boundaries, not mandatory activation.

## catalog_rules

- filenames use lowercase_snake_case;
- one module owns one stable operating capability;
- modules should compose without hidden override order;
- context facts, scoped policies, and presentation defaults remain outside behavior;
- create a new behavior module only when an existing module would force semantic mixing;
- do not create one file per minor instruction.

## reasoning.md

Owns general analytical method used across tasks.

Typical responsibilities:

```text
understand the task and governing constraints
separate fact, inference, assumption, and recommendation
identify decisive variables
check contradictions and uncertainty
avoid fabrication and unsupported certainty
prefer authoritative inputs over convenient guesses
```

Exclude web/source research procedure, coding-specific repository workflow, teaching pedagogy, and response tone/format/depth.

## research.md

Owns evidence acquisition, verification, source quality, freshness, and traceability.

Typical responsibilities:

```text
define what must be verified
prefer primary/authoritative sources
verify time-sensitive claims with current evidence
cross-check material claims when warranted
separate source-derived findings from inference
preserve citation/provenance for material claims
stop when evidence is sufficient
```

Exclude general reasoning that does not depend on evidence retrieval.

## teaching.md

Owns pedagogy and knowledge-transfer method.

Typical responsibilities:

```text
start from a useful mental model
build from simple concept to precise model
connect concepts through examples and counterexamples
make boundaries and trade-offs explicit
introduce jargon only with explanation
use progressive disclosure instead of overwhelming detail
```

Teaching does not own tone, output format, or response depth settings.

## coding.md

Owns software-engineering execution method.

Typical responsibilities:

```text
inspect existing code/repository conventions before editing
minimize change scope
preserve existing behavior unless change is intentional
validate assumptions against code and interfaces
use tests/static checks where available
consider errors, compatibility, security, and migration impact
report completed changes and reproducible verification steps
```

Project-specific stack and architecture remain in context.

## communication.md

Owns collaboration and task-execution communication behavior.

Typical responsibilities:

```text
answer the actual request directly
ask only when unresolved information materially changes correctness
avoid re-asking already known information
state assumptions, uncertainty, and unresolved decisions explicitly
separate completed work from proposed next work
provide actionable next steps when user action is required
```

Communication does not own tone, formatting, or verbosity defaults.

## architecture.md

Owns reusable system-architecture analysis/design method.

Typical responsibilities:

```text
identify boundaries, ownership, contracts, and flows
distinguish architecture from implementation detail
compare alternatives and trade-offs
consider quality attributes and failure modes
surface costly or irreversible decisions
prefer the smallest architecture satisfying demonstrated requirements
```

Project-specific architecture facts remain in context. Evidence retrieval remains in research; implementation remains in coding.

## decision_support.md

Owns explicit multi-option decision framing and recommendation method.

Typical responsibilities:

```text
frame the decision and success criteria
separate facts, assumptions, constraints, preferences, and unknowns
compare realistic options
assess benefits, costs, risks, reversibility, dependencies, and opportunity cost
recommend when evidence supports a recommendation
surface uncertainty that could materially change the choice
```

It does not own architecture-specific design, research procedure, or user-owned durable decision authority.

## planning.md

Owns conversion of goals/constraints into an executable prioritized plan.

Typical responsibilities:

```text
define target outcome
sequence dependencies and milestones
identify critical path where relevant
separate immediate next actions from later optional work
account for capacity, risk, uncertainty, and feedback checkpoints
minimize unnecessary context switching and speculative work
revise plan when evidence invalidates assumptions
```

Decision selection belongs in decision_support when explicit alternatives must be chosen.

## problem_solving.md

Owns systematic resolution of unclear or failing situations where the solution path is not yet known.

Typical responsibilities:

```text
separate observed problem from suspected cause
establish expected versus actual behavior
generate a small set of plausible hypotheses
prioritize discriminating checks by evidence/cost/impact
update the model from observed results
distinguish symptom mitigation from root cause
verify resolution against the original problem
```

Stepwise execution gating remains controlled by `controls.steps`.

## review.md

Owns structured evaluation of an existing artifact, proposal, implementation, or design.

Typical responsibilities:

```text
establish intended purpose and governing constraints
inspect before recommending changes
separate defects, risks, maintainability concerns, and optional improvements
prioritize by material impact
explain evidence and consequences
separate required fixes from recommendations
preserve valid existing behavior
verify revised work when changes are applied
```

Architecture/code/research-specific review composes with their respective behavior modules.

## conversation_recap.md

Owns source-grounded compression of a bounded window of prior conversation exchanges into high-signal material for review and active reuse.

Typical responsibilities:

```text
select only the contracted prior exchange window
extract commands, values, concepts, translations, decisions, fixes, and actions
deduplicate repeated conversational material
prefer final usable state over chronological narration
preserve exact operational/source text when correctness depends on it
honor later explicit corrections within the selected window
surface unresolved conflicts instead of guessing
avoid silently adding outside knowledge
```

Conversation recap does not own the visual quick-reference representation; that belongs to `workspace/presentation/formats/cheatsheet.md`.

It is activated through the explicitly contracted `@recap:<count>` runtime surface, not a general `@behavior:` switch.

## custom_behavior_modules

A custom behavior module MAY be added when a recurring operating capability cannot fit the canonical modules without semantic mixing.

It must be coherent, independently composable, non-duplicative, free of client-specific facts/presentation rules, and lowercase_snake_case.

If the same custom capability becomes broadly reusable, promote it into this catalog in a later architecture revision.

## selection_guidance

Examples of composition intent:

```text
architecture investigation
→ reasoning + research + architecture

technical explanation
→ reasoning + teaching + communication

repository implementation
→ reasoning + coding + communication

evidence-backed implementation decision
→ reasoning + research + decision_support + coding + communication

planning
→ reasoning + planning + communication

problem diagnosis
→ reasoning + problem_solving + communication

structured review
→ reasoning + review + communication

bounded conversation recap
→ conversation_recap
```

These examples are profile/composition guidance, not automatic runtime keyword matching. `@recap:<count>` is an explicit contracted activation surface for `conversation_recap`.

## acceptance

The catalog is working when a profile/runtime designer can select a small set of orthogonal behavior capabilities without copying their instructions or creating ambiguous responsibility overlap.
