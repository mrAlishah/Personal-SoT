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

Read `profile_contract.md` for schema, composition, precedence, validation, and exact runtime-resolution rules.

Profiles are referenced through `@profile:<name>` or adapter/default profile configuration.
