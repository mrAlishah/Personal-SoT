# depth_contract

## purpose

Defines shared semantics for response-depth modules selected through `@depth` or profile/default configuration.

Current selectable depth identities are discovered from the `depths` section of `system/routing/switch_registry.md`. Concrete depth targets own depth-specific behavior; this contract does not maintain a second current-value list.

## core_rule

Depth controls how much relevant explanation, evidence, examples, and elaboration are rendered. It does not change factual authority, policy applicability, factual scope, or unrelated behavior selection.

Depth may influence how much optional supporting context is useful, but retrieval/context optimization remains subordinate to mandatory requirements, correctness, and semantic ownership.

## precedence

Depth precedence and source authority are owned by `system/routing/precedence.md`. This presentation contract does not duplicate that precedence chain.

Within one prompt control block, source-order handling of explicit depth directives follows `system/routing/switch_syntax.md` and the precedence contract.

## boundaries

```text
detail amount → depth
simple language → format/tone as applicable
learning sequence → teaching behavior
mandatory evidence → research/policy requirements
```

A depth target may define a contracted cross-lane interaction only when that interaction is explicit and validated. Such a special case remains owned by its specific runtime/presentation contracts rather than being generalized here.

## acceptance

A compliant depth module changes detail level without changing semantic truth, factual scope, policy authority, tone, format membership, or unrelated behavior capabilities except for an explicitly contracted and validated cross-lane interaction.
