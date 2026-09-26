# semantic_module_boundary_contract

## purpose

Defines deterministic placement rules for canonical facts that could appear to belong to more than one context module.

Use this contract when classifying or migrating knowledge. It is not normal task context.

## core_rule

Place a fact according to its **semantic responsibility**, not according to which filename could plausibly contain the words.

Ask in this order:

```text
1. is this describing what exists or is true now?
2. is this describing an external limitation or operating condition?
3. is this prescribing what must, must not, should, or should not happen?
4. is this explaining the current structural design of a system?
5. is this preserving why a durable choice was made?
```

A canonical fact should normally have one authoritative home.

## constraints_vs_policies

### constraints

A constraint is a factual boundary imposed by reality, environment, dependency, budget, law, capability, compatibility, time, location, or another condition the scope must operate within.

Mental model:

```text
constraint
= the box we must operate inside
```

Examples:

```text
production supports only linux
release must occur before a fixed external deadline
budget is capped at an approved amount
legacy consumer requires protocol compatibility
```

### policies

A policy is a governed normative rule describing what actors or systems must, must not, should, or should not do.

Mental model:

```text
policy
= the rule for how we operate inside the box
```

Examples:

```text
production changes require review
credentials must never be logged
prefer grpc for internal service communication
```

### overlap_rule

If the same situation has both a factual condition and a normative rule, store each semantic statement only if both are independently useful.

Example:

```text
constraint:
customer contract requires data residency in germany

policy:
production data must not be stored outside approved german regions
```

Do not duplicate identical wording in both modules merely because both concepts apply.

## current_state_vs_architecture

### current_state

`current_state.md` owns changeable operational or delivery state describing what is happening now.

Typical content:

```text
current phase
active migration status
current blockers
material active risks
temporary implementation state
work currently in progress
```

Mental model:

```text
current_state
= where we are right now
```

### architecture

`architecture.md` owns current authoritative structural design.

Typical content:

```text
system boundaries
components
responsibilities
data flow
control flow
integration boundaries
architecture patterns
current structural relationships
```

Mental model:

```text
architecture
= how the system is built now
```

### transition_rule

During a migration, temporary progress belongs in `current_state.md`; the currently authoritative structure belongs in `architecture.md`.

If both old and target architectures matter during transition, state clearly which is current and which is target. Do not make a proposed target silently become current architecture.

## architecture_vs_decisions

### architecture

Answers:

```text
what is the current effective design?
```

### decisions

A decision artifact answers:

```text
why was an important choice made?
what alternatives or consequences mattered?
what is the lifecycle status of that choice?
```

Mental model:

```text
architecture
= current map

decision
= durable rationale behind a route choice
```

When an accepted decision changes current design, update the appropriate current module as well. The decision remains deeper evidence, not the sole current source.

## current_state_vs_decisions

Current state is not an append-only decision log.

```text
current_state
→ current effective situation

decision artifact
→ durable rationale for a consequential choice
```

A temporary status update normally does not deserve a decision artifact. A durable decision normally should not be buried in chronological status prose.

## principles_vs_policies

`engineering_principles.md` contains preferred organization-wide engineering guidance and durable design philosophy.

If a statement is mandatory or enforceable, place it in a policy module instead of relying on principle prose.

```text
principle
→ preferred guidance

hard policy
→ mandatory, non-overridable rule

soft policy
→ governed but overridable preference/default
```

Do not duplicate the same rule in both principle and policy form.

## objectives_vs_current_state

`objectives.md` describes desired outcomes and active targets.

`current_state.md` describes present reality.

```text
objective
= where we intend to go

current_state
= where we are now
```

Progress toward an objective may appear in current state, but the objective itself remains in `objectives.md`.

## placement_algorithm

For an ambiguous statement:

```text
1. identify whether it is fact, condition, rule, structure, goal, or rationale
2. identify the owning scope from path
3. select the narrowest canonical module whose semantic responsibility matches
4. check whether the same fact already has an authoritative home
5. avoid copying parent or sibling facts
6. use a custom module only if existing boundaries would force semantic mixing
7. surface genuine ambiguity instead of silently duplicating
```

## token_efficiency

Boundary clarity reduces token cost because the resolver can load the specific semantic atom needed for the task.

Do not solve ambiguity by loading or duplicating several overlapping modules by default.

## acceptance

A contributor can classify an ambiguous statement between constraints, policies, current state, architecture, objectives, principles, and decisions without creating duplicate canonical truth.