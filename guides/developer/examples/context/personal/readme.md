# personal_context_example

This directory is a **fake, reusable example** for building one person's canonical AI context.

Nothing here is real user data and nothing under `examples/` is runtime canonical context.

## how_to_use

1. Copy only the modules that are actually useful into `context/personal/` in your personal overlay.
2. Replace every fake example value marked with `EDIT_ME`.
3. Delete sections that are not applicable; do not keep empty files for symmetry.
4. Choose `ai_access` deliberately for every copied module.
5. Keep one canonical home for each fact; do not copy the same fact into several modules.
6. Do not register this example directory as a real context scope.

## edit_markers

```text
EDIT_ME
→ replace the fake example with your own value

OPTIONAL
→ keep only if the information is useful to recurring AI tasks

DELETE_IF_NOT_APPLICABLE
→ remove rather than preserving meaningless placeholders
```

## starter_modules

```text
identity.md
current_state.md
goals.md
constraints.md
tech_profile.md
working_style.md
```

These are examples, not a mandatory checklist.

## sensitive_section

Sensitive AI-relevant information is shown separately under:

```text
sensitive/
```

The sensitive example uses fake data and `ai_access: restricted` to demonstrate the intended boundary.

Raw secrets such as passwords, API tokens, private keys, recovery codes, or banking login credentials must not be copied into the Git-backed Source of Truth.

See:

```text
context/sensitive_data_contract.md
```

## personal_overlay

The generic core should remain free of person-specific data.

A personalized branch or repository may later copy these examples and replace them with real user-owned context.

System changes flow from core to personal overlay. Personal data must never merge back into generic core.
