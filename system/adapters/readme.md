# adapters

## purpose

Index of client/runtime adapter contracts and generic templates.

## canonical_contract

```text
adapter_contract.md
```

## shared_base

```text
base_instruction.md
```

`base_instruction.md` owns the compact client-neutral operating baseline. Client wrappers should point to it instead of copying common rules.

## generic_client_guidance

```text
chatgpt.md
codex.md
claude.md
```

These files describe client-specific capability/bootstrap boundaries. They do not contain user/project facts.

Deployable Personal wrappers belong under `workspace/adapters/`. They should contain only source identity/path, defaults/overrides, and a pointer to the shared base.

## rule

Keep adapter entrypoints thin. Canonical knowledge remains in `workspace/context/`; prompt recipes in `workspace/prompts/`; operating methods/contracts in `system/`; presentation in its own modules; profiles remain manifests.
