# formats

## purpose

Index the V1/V1.1 response-format contract and canonical discovery path without duplicating the current selectable format set or placement table.

## contract_index

```text
format_contract.md
→ generic format semantics, metadata schema, placement bands, composition, and boundaries
```

## runtime_discovery

Selectable format identities are discovered only from the `formats` section of:

```text
system/routing/switch_registry.md
```

Each registry target under:

```text
workspace/presentation/formats/
```

owns its exact `format_id`, `placement`, and representation semantics through canonical target metadata and module content.

This README does not maintain a second canonical-format list or placement summary. Adding or changing a format must not require updating this index merely to keep discovery facts synchronized.

Formats are selected additively and loaded only when active.

Runtime syntax and precedence remain defined by `system/routing/switch_syntax.md`, `system/routing/recap_contract.md`, and `system/routing/precedence.md`.
