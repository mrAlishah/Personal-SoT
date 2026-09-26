# scope_resolution_cases

These cases validate `routing/scope_resolution.md`.

## case_01_explicit_scope_over_default

Given:

```text
default_scope = personal/projects/job_search
```

Input:

```text
@ctx:org/acme/projects/payment_service
```

Expected primary: `org/acme/projects/payment_service`.

`default_scope` is not added.

## case_02_default_scope

No explicit `@ctx`.

Given:

```text
default_scope = org/acme/projects/payment_service
```

Expected primary: `org/acme/projects/payment_service`.

## case_03_personal_fallback

No explicit `@ctx` and no usable `default_scope`.

Expected primary: `personal`.

## case_04_nested_chain

Input:

```text
@ctx:org/acme/projects/payment_service/reconciliation/batch_processor
```

Expected chain:

```text
org/acme
→ org/acme/projects/payment_service
→ org/acme/projects/payment_service/reconciliation
→ org/acme/projects/payment_service/reconciliation/batch_processor
```

## case_05_valid_but_missing_primary

Input:

```text
@ctx:org/acme/projects/nonexistent_service
```

Expected: primary resolution fails closed. Do not substitute `default_scope` or `personal`.

## case_06_invalid_primary_syntax

Input contains only syntactically invalid `@ctx` directives.

Expected: invalid directives are rejected; normal `default_scope` / personal fallback selection may continue.

## case_07_failed_supplemental

Input:

```text
@ctx:org/acme/projects/payment_service
@ctx:org/unknown_company
@ctx:personal
```

If `unknown_company` is unresolved, expected:

```text
primary = org/acme/projects/payment_service
supplemental = personal
warning = unknown_company unresolved
```

## case_08_cross_owner_isolation

Input:

```text
@ctx:org/acme/projects/payment_service
```

Expected: no implicit `personal` and no implicit second organization.

## case_09_relevance_not_recursive_loading

For an architecture task under payment_service, ancestor scopes are candidates.

Expected: load only mandatory and relevant semantic atoms; unrelated ancestor files are not automatically loaded.

## case_10_token_budget_quality_guard

Given optional context exceeds budget.

Expected pruning order:

```text
preserve access rules
preserve mandatory policies
preserve authoritative facts
preserve relevant higher-value atoms
prune optional lower-value atoms
```
