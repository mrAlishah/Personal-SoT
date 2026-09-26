# behavior_module_contract

## purpose

Defines the V1 contract for reusable behavior modules.

A behavior module contains one coherent class of operational guidance for how an AI should perform work. It does not own facts about the user, an organization, or a project.

## core_rule

A behavior module should be the smallest coherent operating capability that remains useful independently during profile composition.

Canonical examples:

```text
reasoning
research
teaching
coding
communication
```

Behavior atomicity is semantic, not line-based. Avoid both one giant `behavior.md` and one instruction per file.

## global_reuse

V1 behavior modules are globally reusable system-layer components under `behavior/`.

They are not hierarchically owned by personal, organization, or project scopes.

Scope-specific facts remain in `context/`. Scope-specific mandatory or overridable governance remains in `context/.../policies/`.

## no_fact_ownership

Behavior modules MUST NOT own or duplicate canonical facts such as:

```text
project stack
organization architecture
user goals
current project state
business constraints
```

Behavior may describe how to use such facts after they are supplied by context resolution.

## no_policy_override

Behavior modules MUST NOT weaken, remove, bypass, or reinterpret applicable hard policies.

Conceptually:

```text
external mandatory boundary
+
applicable hard policy
>
behavior instruction
```

If behavior guidance conflicts with a hard policy, the hard policy remains effective and the behavior conflict should be surfaced or ignored for the conflicting operation.

## separation_from_presentation

Behavior defines how work is performed. Presentation defines how the answer looks, sounds, and which language configuration is used.

Behavior MUST NOT own response-format, tone, depth, or language defaults.

Examples:

```text
cross-check material claims
→ research behavior

use a comparison table
→ format

professional tone
→ tone

short answer
→ depth

primary German with English/Persian support
→ language
```

## selection

M3 defines behavior modules and their composition semantics, not a new runtime switch namespace.

Behavior selection may be provided by selected profiles or another explicitly contracted adapter/runtime surface.

V1 MUST NOT infer persistent behavior configuration merely from arbitrary prompt words.

## composition

Selected behavior modules compose additively.

Rules:

- duplicate module selection is idempotent;
- module order may preserve deterministic assembly/provenance but does not grant authority to override another module;
- modules should be designed to be orthogonal;
- a genuine contradictory instruction between active behavior modules is a configuration conflict, not a last-wins case;
- behavior conflicts must not be resolved by context scope specificity because behavior modules are not factual scope descendants.

## conflict_handling

When two active behavior modules appear to conflict:

```text
1. check whether the statements actually belong to different semantic layers
2. move misplaced facts/policies/presentation instructions to their proper layer
3. if a real behavior conflict remains, surface it or resolve it in a later explicit profile/behavior contract
4. do not silently use source order as hidden override authority
```

This keeps profile composition predictable.

## instruction_design

Behavior instructions SHOULD be:

- reusable across AI clients;
- task-oriented;
- concise and independently understandable;
- explicit about important failure/verification behavior;
- compatible with unknown future context values;
- free of client-specific UI or tool syntax unless the module explicitly targets that capability.

Avoid:

- duplicated architecture explanations;
- personal preferences that belong in context/profile composition;
- output formatting/language choices that belong to presentation;
- hard security/compliance rules that belong in policies;
- long examples needed only for validation.

## token_efficiency

Only selected behavior modules should enter runtime context.

Behavior modules SHOULD prefer compact rules over repeated rationale. Examples and edge-case validation belong under `tests/behavior/`.

Do not add metadata such as `priority`, `token_weight`, or `relevance_score` without an demonstrated correctness need.

## access_boundary

`ai_access` in `context/access_contract.md` governs factual context modules, not these reusable system-layer behavior modules.

Behavior availability is bounded by repository, host, tool, and external mandatory access controls. Do not repeat `ai_access: allow` in every behavior file solely for symmetry.

If behavior-specific access control becomes necessary later, add it through an explicit architecture revision rather than reusing context access semantics implicitly.

## provenance

The canonical behavior module path is the V1 provenance identifier.

A composed profile should be able to state which behavior modules are active without copying their full instructions into the profile.

## acceptance

A compliant behavior module makes it possible to determine:

- which operating capability it owns;
- whether an instruction is behavior rather than fact, policy, or presentation;
- whether it can compose safely with other behavior modules;
- whether a conflict must be surfaced;
- whether loading it is necessary for the selected profile/configuration.
