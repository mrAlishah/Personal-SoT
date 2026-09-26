# merge_strategy_cases

These cases validate `routing/merge_strategy.md` as the owner of value-composition mechanics after authority has already been resolved by `routing/precedence.md`.

## case_01_scalar_override

Given both values are already authorized within one authoritative scope chain:

```text
owner: database = postgresql
project: database = clickhouse
```

Expected: `database = clickhouse`.

## case_02_list_merge

Within one authorized scope chain:

```yaml
owner:
  tests: [unit, integration]
project:
  tests: [integration, contract]
```

Expected:

```yaml
tests: [unit, integration, contract]
```

## case_03_map_deep_merge

Within one authorized scope chain:

```yaml
owner:
  testing:
    unit: required
    integration: required
project:
  testing:
    performance: required
```

Expected all three keys.

## case_04_add

Parent:

```yaml
required_tests: [unit, integration]
```

Authorized child in the same scope chain:

```yaml
add:
  required_tests: [contract]
```

Expected: `[unit, integration, contract]`.

## case_05_remove

Parent:

```yaml
required_tests: [unit, integration]
```

Authorized child in the same scope chain:

```yaml
remove:
  required_tests: [integration]
```

Expected: `[unit]`.

## case_06_replace

Parent:

```yaml
required_tests: [unit, integration]
```

Authorized child in the same scope chain:

```yaml
replace:
  required_tests: [contract]
```

Expected: `[contract]`.

## case_07_remove_missing_exact_target

Remove `integration_test` when only `integration` exists.

Expected: no removal; diagnostic emitted; no fuzzy match.

## case_08_hard_policy_non_removal

An applicable hard policy is `never_expose_credentials`.

An otherwise-authorized operation attempts `remove`.

Expected: policy remains active; operation rejected.

## case_09_unauthorized_operator_cannot_bypass_precedence

Precedence has already excluded a supplemental source from target `required_tests`.

That source attempts:

```yaml
remove:
  required_tests: [integration]
```

Expected: merge rejects the operation and preserves the authoritative target. The merge contract does not independently decide why the source was excluded.

## case_10_empty_collection

Parent has inherited list. Authorized child declares `required_tests: []` without `replace`.

Expected: empty declaration is not universal inherited-value deletion.

## case_11_type_conflict

Parent canonical target is a map; authorized child declares same target as incompatible scalar without schema permission.

Expected: configuration conflict; do not guess conversion.

## case_12_unauthorized_additive_value_is_excluded

Precedence has already determined that a supplemental source does not own target `required_tests`.

The excluded source presents `[exploratory]` while the authoritative target is `[unit, integration, contract]`.

Expected: merge mechanics do not append `exploratory`; final value remains `[unit, integration, contract]`.

## case_13_authorized_set_union

Within an authorized scope chain:

```text
parent regions = {eu_central}
child regions  = {us_east}
```

Expected: `{eu_central, us_east}`.

## case_14_authorized_map_deep_merge

Within an authorized scope chain:

```yaml
parent:
  settings:
    retries: 5
child:
  settings:
    debug: true
```

Expected:

```yaml
settings:
  retries: 5
  debug: true
```

## case_15_applicable_hard_policy_accumulation

Precedence has already determined hard policies A and B are both applicable.

Expected: merge accumulates A + B; neither is removed or replaced.

## exit_criterion

Merge-strategy tests pass when authorized values compose deterministically by scalar/list/set/map/operator mechanics, hard-policy weakening is prevented, invalid types/operators are surfaced, and no merge behavior can create or override source authority resolved by `routing/precedence.md`.
