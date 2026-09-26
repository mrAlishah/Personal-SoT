# context_merge_strategy

## purpose

Defines how already-authorized values compose into an effective context.

Scope discovery is defined in `system/routing/scope_resolution.md`. Source authority and target ownership are canonically resolved by `system/routing/precedence.md` before merge mechanics run.

This contract does not decide which source wins. It consumes the resolved authority result and defines only value-composition behavior.

## authority_boundary

Type-aware merge applies only to sources/targets already authorized by `system/routing/precedence.md`.

Merge mechanics MUST NOT create, widen, reinterpret, or override source authority or target ownership. If precedence excludes a source from target T, no scalar/list/set/map behavior or explicit operator may make that source affect T.

Applicable hard-policy authority is also resolved by precedence; this contract only defines how those already-applicable policies accumulate and how invalid weakening operations are handled.

## semantic_categories

Within an authoritative scope chain or otherwise-authorized target, V1 merge semantics are type-aware:

| category | default behavior |
| --- | --- |
| scalar | replace with the effective more-specific authorized value |
| list | merge, deduplicate, preserve first effective order |
| set | union |
| map | recursive deep merge |
| hard_policy | accumulate; non-overridable |
| soft_policy | replace with the effective more-specific authorized value |

A later module contract may make category metadata machine-readable.

## scalar

For authorized values in the same effective target, the more-specific effective scalar replaces the less-specific scalar. If the child omits the value, the inherited value remains effective.

A source excluded by precedence does not participate in scalar replacement.

## list_and_set

For authorized values, lists merge and deduplicate and sets union. Primitive identity uses exact equality unless a later module contract defines stable structured identity.

Additive data types do not bypass the authority result already resolved by precedence.

## map

For authorized values, maps deep-merge recursively. Conflicting nested keys use the semantic rule of the nested value.

A semantic type mismatch for the same canonical target is invalid unless a later schema explicitly permits conversion.

A source excluded by precedence cannot add map keys merely because map semantics are additive/deep-merging.

## hard_policy

Applicable hard policies that precedence admits to the effective target accumulate.

Once applicable, a hard policy may not be removed, replaced, weakened, or negated by merge mechanics.

Logically incompatible applicable hard policies produce a policy conflict; do not silently choose one.

## soft_policy

For an authorized overridable soft-policy target, the effective more-specific value replaces the less-specific value according to the authority result supplied by precedence.

This contract does not independently determine whether a primary or supplemental context owns that target.

## explicit_operators

V1 supports exactly:

```text
add
remove
replace
```

No implicit `reset`, `clear`, or `inherit_none` semantics exist in V1.

Every explicit operator is authority-gated: syntax never grants authority that precedence did not already establish.

### add

Extends an additive target only when the source is authorized for that target.

Typical targets:

```text
list
set
map
hard_policy
soft_policy_collection
```

`add` may extend applicable hard policies because hard policies accumulate.

An `add` from a source excluded by precedence is rejected. Additive syntax does not grant cross-context authority.

### remove

Removes an exact named item or key from an overridable target only when the source is authorized for that target.

Rules:

- exact identity only; no fuzzy matching;
- missing target is a no-op with diagnostic;
- hard policies cannot be removed;
- an unauthorized source cannot remove values from the target.

### replace

Replaces the complete named overridable target with a new value only when the source is authorized for that target.

Rules:

- replacing a map replaces that target rather than deep-merging it;
- use narrow targets when only one nested key should change;
- hard-policy collections cannot be replaced in a weakening way;
- an unauthorized source cannot replace the target;
- one target may not have competing `replace` operations in the same authoritative scope.

## operator_order

For the same target inside one authoritative scope:

```text
1. inherit less-specific effective value
2. apply ordinary local declaration by semantic type
3. apply add
4. apply remove
5. apply replace, if present
```

Authority/target ownership is resolved before this operator sequence.

Mixing redundant destructive operations for the same target should be treated as invalid or diagnostic-worthy by a future validator rather than relying on hidden ordering.

## absence_null_and_empty

Absence means inherit; it is not deletion.

V1 does not treat `null` as a universal delete operator.

An empty collection does not mean "remove all inherited values". Use explicit `replace` when replacement with an empty overridable collection is intentional.

Replacing a hard-policy collection with empty is invalid.

## provenance

Effective values should retain conceptual provenance sufficient to explain:

```text
source_scope
context_role
semantic_category
target_owner
merge_operator
shadowed_source
excluded_source
removed_source
rejected_operation
```

`target_owner` and authority/exclusion decisions originate from `system/routing/precedence.md`; merge provenance records their effect but does not redefine them.

The exact machine-readable schema is deferred.

## failure_rules

- operations from sources excluded by precedence do not modify the target;
- hard-policy removal/replacement attempts are rejected;
- type conflicts are surfaced rather than guessed;
- unknown operator names are invalid;
- removal never uses fuzzy matching;
- rejected operations should be visible in diagnostics/provenance.

## acceptance

A compliant merge engine can deterministically compose authorized scalar, list, set, map, hard-policy, and soft-policy inputs; apply permitted `add`, `remove`, and `replace`; preserve applicable mandatory hard policies; respect source authority/target ownership resolved by `system/routing/precedence.md`; and explain excluded or rejected operations without independently redefining authority.
