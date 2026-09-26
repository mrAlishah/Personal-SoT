# SoT project charter

## purpose

Define the durable purpose, design principles, and decision priorities for evolving the AI Context Source of Truth itself.

This charter is the canonical governance basis for architecture changes, refactors, new runtime capabilities, context-model changes, adapters, prompts, profiles, retrieval, and maintenance automation.

The public V1 product audience, experience, scope, and completion standard are
owned by `system/governance/public_v1_product_contract.md`.

## project_definition

The SoT is a canonical, client-neutral, Git-backed context and runtime-governance system for AI clients such as ChatGPT, Claude, Codex, and compatible agents.

Its goal is to replace fragmented prompt repetition, stale client memory, duplicated context, and ad-hoc AI assumptions with a maintainable authoritative system that provides:

- canonical factual context;
- explicit semantic ownership;
- reusable behavior and presentation contracts;
- deterministic routing, access, and precedence;
- progressive disclosure of only relevant context;
- consistent behavior across supported clients;
- reviewable, versioned, testable evolution.

The SoT should make an AI more context-aware and reliable without requiring the entire knowledge base to be loaded into every interaction.

## priority_order

When design goals compete, use this order:

```text
mandatory policy / authorization / safety
>
correctness and data integrity
>
semantic ownership / cohesion / non-duplication
>
retrieval and context efficiency
>
convenience and implementation simplicity
```

Higher priorities must not be sacrificed merely to optimize a lower priority.

Context/token consumption is a measured subdimension of retrieval/context efficiency, not an independent priority that can override ownership, cohesion, correctness, or mandatory boundaries.

Within solutions that preserve higher priorities, prefer the design with clearer semantic ownership, higher cohesion, lower coupling, bounded change fan-out, minimum necessary indirection, narrower retrieval, and lower measured context cost.

## principles

### canonical_truth

Canonical SoT content outranks client memory, inference, stale copies, and duplicated summaries for domains the SoT owns.

Do not create competing authoritative copies of the same durable state.

### semantic_ownership_and_cohesion

Each durable fact, rule, preference, behavior, schema fact, or runtime semantic has one primary semantic owner. Other modules should reference, compose, or mechanically consume that owner rather than restating current state or creating a parallel interpretation.

A module boundary is justified when it reduces coupling, has an independent lifecycle/ownership/retrieval/privacy value, or materially narrows change/retrieval blast radius.

Do not split merely to maximize atomicity. Do not merge unrelated semantics merely to reduce file count. Prefer the minimum necessary semantic boundaries that preserve coherent ownership.

### structural_maintainability

Treat long-term structural maintenance cost as a first-class quality attribute after mandatory boundaries, correctness, and semantic ownership are protected.

Prefer:

```text
high cohesion
low coupling
bounded and explainable change fan-out
minimum necessary indirection
few reconciliation points
explicit contracts at critical boundaries
controlled special-case accumulation
no known dead/stale ownership paths
```

A small semantic change should not require edits to unrelated owners merely because current identities, values, precedence, or schema facts were duplicated across generic consumers.

Do not optimize for human readability, fewest files, fewest lines, maximum abstraction, or maximum atomicity. Those properties are incidental unless they reduce actual maintenance cost without weakening higher priorities.

### separation_of_concerns

Keep factual context, behavior, presentation, routing, access, deployment, and implementation history conceptually separate.

Profiles compose existing semantics; they should not duplicate implementation semantics.

Adapters translate host/client constraints; they should not become independent sources of canonical knowledge.

### retrieval_and_context_efficiency

Prefer path/registry-first resolution, progressive disclosure, targeted reads, bounded reconciliation, reuse of stable resolved configuration, and the smallest sufficient authoritative context.

Avoid recursive scans, broad eager loading, unnecessary repeated resolution, duplicated context, and maintenance work that does not improve future reasoning.

Measure context/token consumption, repeated reads, resolution steps, reconciliation work, and material IO/latency when an optimization decision depends on actual cost. Do not optimize token count in isolation.

Prefer references/composition over repeated prose, compact canonical state over transcript-like history, current summaries over duplicated full evidence, and targeted retrieval over loading entire scopes.

Do not retain information merely because it is available; retain it when it has a defined owner and plausible future contextual value under the applicable maintenance policy.

### conflict_resistance

Before canonical writes, reconcile against the relevant current owner and obvious overlapping owners.

Do not create duplicate aliases, contradictory current values, inferred equivalences, or silent ownership drift. Resolve or explicitly clarify meaning-changing conflicts.

### current_state_vs_history

Keep effective current state separate from historical evidence when mixing them harms correctness, retrieval, or context efficiency.

Preserve history only in owners whose purpose is longitudinal evidence, auditability, or durable decision history.

### progressive_disclosure_and_privacy

Authorization does not imply loading. Resolve access and applicability first, then load only the minimum relevant authorized atoms.

Sensitive/restricted context must preserve fail-closed access behavior and data minimization. Raw secrets do not belong in the Git-backed SoT.

### client_neutrality

Canonical semantics should remain independent of ChatGPT, Claude, Codex, or any single host wherever practical.

Host-specific constraints belong in adapters/deployment surfaces. A client limitation should not silently redefine canonical semantics for every client.

### smallest_safe_change

For maintenance and implementation, prefer the smallest coherent patch that satisfies the requested outcome while preserving existing contracts and compatibility.

Avoid opportunistic refactors or new abstractions unless they materially improve correctness, semantic ownership, cohesion, coupling, retrieval/context efficiency, structural maintainability, or another higher-priority concern.

A rewrite from scratch is not a default optimization strategy. Prefer root-cause corrections that preserve valid existing behavior and reduce future structural cost.

### evidence_over_assumption

Inspect actual canonical files, code, tests, configuration, manifests, and relevant repository state before changing architecture or claiming effective behavior.

If authoritative evidence is unavailable, report the limitation rather than inventing state.

### truthful_validation

Never claim validation passed unless the relevant validator/check actually ran and passed.

Distinguish inspected, implemented, merged, deployed, synced, and validated states.

### core_first_reuse

Reusable runtime/contracts belong in Core first and flow through the governed branch path into Personal deployments. Personal facts and deliberately Personal-specific overlays remain Personal-owned.

## decision_test

Before accepting a material SoT change, ask:

1. What semantic owner should contain this change?
2. Does it duplicate an existing canonical fact/rule/contract/current inventory?
3. Does the proposed boundary reduce coupling or have independent lifecycle/retrieval/privacy value?
4. What is the change fan-out, and is each touched owner inherently required?
5. Does the design introduce unnecessary indirection, wrappers, reconciliation, or special cases?
6. Does it reduce or increase required retrieval/context and measured token/IO cost?
7. Can progressive disclosure avoid loading unrelated material?
8. Does it preserve correctness, access, privacy, and conflict resistance?
9. Is current state being confused with history or implementation noise?
10. Is this reusable Core behavior or a Personal/client-specific overlay?
11. Is there a smaller coherent root-cause change that achieves the same result?
12. What validation actually proves the result and critical boundaries?

If two designs are otherwise correct, prefer the one with fewer semantic owners to reconcile, higher cohesion, lower coupling, bounded change fan-out, less duplicated prose/state, narrower retrieval, lower measured context cost, and less unnecessary indirection.

## non_goals

The SoT is not intended to be:

- a transcript/archive of every conversation;
- a generic document dump;
- a raw secret store;
- a replacement for source repositories, issue trackers, medical records, or other authoritative external systems;
- a mechanism for loading all known context into every prompt;
- a client-specific prompt collection with duplicated semantics;
- an architecture optimized primarily for human readability;
- a design optimized for fewest files or fewest lines;
- a maximum-atomicity or maximum-abstraction exercise;
- a minimum-token system at the expense of correctness, ownership, cohesion, or validation;
- a rewrite-from-scratch project when bounded root-cause evolution is sufficient.

## maintainability_definition_of_done

For a stabilization/revision release, structural maintainability is acceptable when evidence supports:

```text
semantic_ownership_clear: yes
unnecessary_indirection: no known material instance
semantic_duplication: no known material instance
hidden_coupling: no known material instance
change_fan_out: bounded or justified
module_cohesion: acceptable
special_case_accumulation: controlled
dead_or_stale_logic: no known material instance
critical_boundaries_validated: yes
future_change_cost: bounded
```

This is an evidence standard, not a claim that future defects are impossible.

## change_governance

Material modifications to the SoT architecture or reusable system contracts should be evaluated against this charter before implementation.

If a requested change materially conflicts with the charter, make the conflict explicit and use the applicable clarification/decision authority rather than silently weakening the charter.

Changes to this charter itself are architecture/governance changes and should follow Core-first branch governance and normal validation discipline.
