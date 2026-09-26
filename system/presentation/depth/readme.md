# depth

## purpose

Index of response-depth contracts and canonical selectable depth targets.

Current selectable depth identities and their target mappings are discovered from the `depths` section of `system/routing/switch_registry.md`. This README does not maintain a second current-depth list.

Read `system/presentation/depth/depth_contract.md` for shared depth semantics. Concrete selectable depth modules live under `workspace/presentation/depth/` and own their depth-specific behavior.

Depth is single-value. Only the effective depth module should enter runtime presentation context.

Depth controls rendered detail, not factual scope, authority, policy, or unrelated behavior selection.
