# context_registry

## purpose

Compact registry of canonical selectable factual scopes.

## physical_root

Canonical factual scope directories resolve below:

```text
workspace/context/
```

Runtime `@ctx` values do not include the `workspace/context/` prefix.

## entry_shape

An entry is **two consecutive lines** inside the registered-scopes code
fence: the runtime scope alone, followed by the arrow and canonical target
on the next line. The following indented example is explanatory, not an
active registry entry:

    personal/projects/example
    → workspace/context/personal/projects/example/

Do **not** put the scope and arrow on a single line. The registry stores identity/location only. It does not duplicate facts, policies, module access state, or module inventory.

## registered_scopes

Generic Core intentionally registers no real factual scopes.

Personal/organization overlays add entries only for scopes that physically exist under `workspace/context/`.

## rules

- runtime scope uses canonical lowercase_snake_case grammar;
- canonical directory is repository-relative and begins with `workspace/context/`;
- one runtime scope maps to exactly one canonical directory;
- a registry entry does not imply module-level AI access;
- developer examples under `guides/developer/examples/` must never be registered as runtime scopes;
- do not create placeholder scope entries for contexts that do not yet exist.
