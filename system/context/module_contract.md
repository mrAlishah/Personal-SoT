# atomic_module_contract

## purpose

Defines the contract for context modules used by the AI Source of Truth.

A context module is an independently addressable semantic atom containing one coherent category of canonical knowledge for one owning scope. Canonical factual modules live under `workspace/context/`.

## core_rule

A module should be the smallest semantically coherent unit independently useful during context composition. Atomicity is semantic, not line-based.

Avoid monolithic unrelated context and one-file-per-small-fact fragmentation.

## ownership

Every canonical module belongs to exactly one resolved factual scope derived from physical path.

Examples:

```text
workspace/context/personal/goals.md
→ owner: personal

workspace/context/personal/projects/job_search/current_state.md
→ owner: personal/projects/job_search

workspace/context/organizations/acme/projects/payment_service/architecture.md
→ owner: org/acme/projects/payment_service
```

Projects never become independent top-level owners.

## authority_and_responsibility

A module is authoritative only for its assigned semantic domain and scope. Cross-module conflicts indicate stale knowledge, incorrect placement, or undefined boundaries and should be surfaced rather than silently resolved by filename.

## split_rule

Split a module when it contains unrelated domains, one part is frequently needed without the rest, lifecycle/access differs, or combined loading creates material repeated token/privacy waste. Do not split when fragments lose independent meaning or overhead exceeds value.

## no_duplication

Canonical facts have one authoritative location. Composition/reference supplies facts to other tasks; retrieval convenience is not a reason to copy them.

## path_derived_metadata

Do not repeat scope, owner, module_type, or canonical_path metadata when deterministically derived from `workspace/context/...` and filename.

## required_access_metadata

A canonical module is AI-loadable only when access state permits it according to `system/context/access_contract.md`. Access metadata cannot safely be inferred from path.

## mandatory_semantics

Ordinary factual modules are not globally mandatory by filename/location. Applicable hard policies are mandatory; ordinary facts are selected by task relevance and resolver semantics.

## content_design

Prefer stable facts, explicit constraints, current authoritative state, domain terminology, compact structured lists, and deeper evidence only when needed.

Avoid copied repository architecture, prompt/presentation instructions, duplicated parent/sibling facts, long chronological history in current-state modules, and schema examples inside canonical context.

Developer examples belong under `guides/developer/examples/`; contract/integration cases belong under `system/tests/`.

## current_vs_historical

Current-state modules contain current effective state. Historical rationale belongs in decision/history artifacts when still useful. Recency alone does not establish authority.

## composition

```text
resolve_scope
→ discover_candidate_modules
→ validate_access
→ include_mandatory_modules
→ select_relevant_optional_modules
→ apply_context_budget_to_optional_modules
→ merge_and_resolve_precedence
```

## progressive_disclosure

Prefer the minimum sufficient authoritative set and load deeper evidence only when needed.

## module_size

There is no fixed line/token limit. Size is judged by cohesion and retrieval usefulness.

## separation_from_other_layers

Context defines what is true for a scope. Behavior, response formats, tone, depth, adapter configuration and runtime grammar belong to their own `system/` or `workspace/` areas.

## provenance

The repository-relative module path under `workspace/context/` is the primary physical provenance identifier; the corresponding logical scope remains the runtime identity.

## acceptance

A compliant module has clear semantic responsibility, one owner, explicit access state, no duplicate canonical truth, and boundaries that reduce unnecessary loading without reducing correctness.
