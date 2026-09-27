# hierarchical_scope_resolution

## purpose

Defines how an active context scope is selected, mapped to canonical ownership, and expanded into candidate scope chains.

Scope resolution does not merge facts and does not recursively load every file in the hierarchy.

## ownership_roots

V1 factual context has exactly two logical ownership roots, physically stored under the end-user workspace:

```text
workspace/context/personal/
workspace/context/organizations/<organization>/
```

Projects always belong to one of these roots.

## canonical_scope_forms

```text
personal
personal/projects/<project_path>
org/<organization>
org/<organization>/projects/<project_path>
```

Runtime `personal` maps below `workspace/context/personal/`.
Runtime `org/<organization>` maps to `workspace/context/organizations/<organization>/`.

Nested project depth is expressed directly with additional path segments.

## primary_selection

```text
explicit_prompt_context
>
project_or_adapter_default_scope
>
personal_fallback
```

Algorithm:

```text
parse valid executable @ctx directives

if explicit primary @ctx exists:
    resolve it
else if usable default_scope exists:
    resolve default_scope
else:
    resolve personal
```

`default_scope` uses the same canonical grammar as `@ctx`.

## explicit_failure_semantics

```text
invalid @ctx syntax
→ directive never becomes a valid explicit request
→ normal default/fallback selection may continue

valid explicit primary @ctx but missing/inaccessible/unresolved
→ explicit intent exists
→ fail closed for primary scope
→ do not substitute default_scope or personal
```

If a supplemental context is missing or inaccessible, keep the valid primary and other valid supplementals, omit the failed supplemental, emit a concise warning, and never insert a fallback replacement.

## multiple_contexts

```text
first resolved explicit @ctx = primary
later resolved @ctx values   = supplemental
```

Each supplemental context resolves into its own independent chain.

## scope_chain_construction

Personal example:

```text
personal/projects/job_search/cv
→ personal
→ personal/projects/job_search
→ personal/projects/job_search/cv
```

Organization example:

```text
org/acme/projects/payment_service/reconciliation
→ org/acme
→ org/acme/projects/payment_service
→ org/acme/projects/payment_service/reconciliation
```

Within one chain, deeper scopes are more specific.

## ownership_isolation

Traversal must never cross ownership boundaries implicitly. Organization resolution does not automatically include personal or another organization; personal resolution does not automatically include organization context.

## scope_vs_module_loading

```text
hierarchy_finds_candidate_scopes
semantic_atomicity_defines_module_boundaries
relevance_selects_optional_modules
```

Ancestor presence does not imply loading all ancestor files.

## quality_first_loading

```text
1. validate_access
2. include mandatory hard policies and required context
3. preserve primary ownership and fact authority
4. select relevant semantic atoms
5. prune only optional context to satisfy context budget
```

Token optimization must not change authority.

## progressive_disclosure

Prefer minimum sufficient authoritative context first. Expand only when required.

## no_global_fact_root

There is no implicit factual `global` root above personal and organizations.

## provenance

A resolver preserves enough metadata to explain selection source, role, owner, selected scope, chain and warnings. The current source binding/provenance envelope is owned by `system/adapters/source_access_contract.md`; scope resolution adds logical scope/module provenance within that binding. Physical repository paths may be included for provenance but do not replace logical scope identity.

## resolution_pipeline

```text
1. parse executable switches
2. validate canonical @ctx syntax
3. choose explicit primary, default_scope, or personal fallback
4. map logical scope through workspace/context/ and registry
5. verify existence/registration and access
6. construct primary scope chain
7. resolve supplemental contexts independently
8. expose candidate scopes to relevance-aware module selection
```

## acceptance

A compliant resolver preserves logical scope identity while resolving physical modules under `workspace/context/`.
