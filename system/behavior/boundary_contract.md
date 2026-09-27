# behavior_boundary_contract

## purpose

Defines deterministic boundaries between behavior instructions and neighboring system layers.

Use this contract when deciding where an instruction belongs. It is not ordinary task context.

## core_rule

Classify by semantic responsibility:

```text
context
→ what is true

policy
→ what must/must not/should/should not happen for a governed scope

behavior
→ how the AI performs work

presentation
→ how the answer is rendered, sounds, and which language configuration is active

profile
→ which reusable modules/defaults are composed

adapter
→ client/runtime integration configuration
```

A canonical instruction should normally have one authoritative home.

## behavior_vs_context

Behavior consumes facts; it does not own them.

```text
project uses postgresql
→ workspace/context/...

compare alternatives against known project constraints
→ system/behavior/reasoning.md
```

Do not copy project/user facts into behavior modules to make them self-contained.

## behavior_vs_policy

Behavior is reusable operating method. Policy is governed normative authority.

Examples:

```text
cross-check material claims when warranted
→ research behavior

production changes require security review
→ scoped policy
```

A behavior instruction may use normative wording for operational clarity, but it does not gain authority to weaken or replace scoped hard policy.

When the same idea exists because a specific organization/project mandates it, the governing requirement belongs in policy; do not duplicate identical wording into behavior solely for emphasis.

## behavior_vs_presentation

Behavior answers "how should the AI work?" Presentation answers "how should the result be rendered, sound, and which language configuration should be used?"

```text
explain causal relationships accurately
→ behavior

use a comparison table
→ format

professional tone
→ tone

short response
→ depth

primary German with English/Persian support
→ language
```

Teaching behavior may use examples or mental models when useful, but it must not force permanent format, language, tone, or verbosity settings.

## behavior_vs_profile

Behavior modules contain reusable instructions. Profiles contain composition references/defaults.

A profile SHOULD reference behavior modules rather than copying their content.

Conceptually:

```text
profile: g.technical.learning
behaviors:
  - reasoning
  - teaching
  - communication
```

The exact profile file schema is defined by a later milestone.

## behavior_vs_adapter

Client-specific wiring belongs in adapters, not reusable behavior.

```text
use careful source verification
→ system/behavior/research.md

ChatGPT project default_profile = g.research
→ adapter/project configuration
```

Behavior modules should remain portable across ChatGPT, Claude, Codex, and future clients.

## reasoning_vs_research

`system/behavior/reasoning.md` owns analysis of supplied/available information.

`system/behavior/research.md` owns acquisition, verification, freshness, source quality, and evidence traceability.

```text
identify the decisive trade-off
→ reasoning

verify the current API behavior from official documentation
→ research
```

A task may compose both.

## reasoning_vs_teaching

`system/behavior/reasoning.md` determines and validates the conceptual answer.

`system/behavior/teaching.md` determines how to build understanding of that answer.

```text
determine why eventual consistency is acceptable
→ reasoning

teach eventual consistency from a mental model to precise trade-offs
→ teaching
```

## coding_vs_reasoning

`system/behavior/reasoning.md` owns general analysis; `system/behavior/coding.md` owns repository/change execution discipline.

```text
choose between two architectures
→ reasoning

inspect repository conventions, implement the selected change, and validate it
→ coding
```

They commonly compose and should not duplicate each other's generic rules.

## communication_vs_presentation

`system/behavior/communication.md` owns interaction discipline: clarify material ambiguity, distinguish completed/planned work, and provide next actions.

Presentation modules own tone, format, language configuration, and detail level.

```text
state an unresolved architectural decision before committing
→ communication behavior

formal wording
→ tone
```

## placement_algorithm

For a new instruction:

```text
1. ask whether it describes fact, governance, operating method, output style/language, composition, or client wiring
2. place it in the matching semantic layer
3. check for an existing authoritative instruction
4. avoid duplication across modules/layers
5. create a custom behavior module only for a recurring independent operating capability
6. surface genuine conflicts instead of relying on hidden source order
```

## token_efficiency

Clear boundaries allow profiles to load only the behavior capabilities they need.

Do not solve uncertain placement by duplicating the instruction across several behavior modules or system layers.

## acceptance

A contributor can classify an instruction between context, policy, behavior, presentation, profile, and adapter configuration without creating duplicate or contradictory authority.
