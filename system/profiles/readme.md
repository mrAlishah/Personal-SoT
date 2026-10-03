# profiles

## purpose

Discovery guidance for V1 profile semantics.

Concrete user-editable profile manifests live under `workspace/profiles/`. Profiles compose existing behavior and presentation modules; they do not own canonical knowledge.

## identity_model

Profile identity is self-addressing and path-derived:

```text
workspace/profiles/<profile_name>.md
→ @profile:<profile_name>
```

Do not maintain a second canonical list of selectable profile identities in this README. The exact filename under `workspace/profiles/` is the runtime identity, as defined by `profile_contract.md`.

Shipped and custom Profiles share one identity grammar; no identity shape
is reserved. Ownership (shipped vs custom) is carried internally by each
file's own `owner: product | custom` frontmatter field, never by the
identity. Resolution is exact, and user create/edit flows refuse to write
over any existing file whose `owner` is `product`.

Read `profile_contract.md` for schema, composition, precedence, validation, and exact runtime-resolution rules.

Profiles are referenced through `@profile:<name>` or adapter/default profile configuration.
