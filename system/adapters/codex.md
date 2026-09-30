# codex_adapter

## integration_surface

Use Codex project instruction files such as `AGENTS.md` / `AGENTS.override.md` as thin repository-native bootstrap surfaces where applicable.

## adapter_role

The root adapter should contain only broad repository instructions, Source-of-Truth mapping/defaults, and repository-specific validation/change rules. Do not duplicate canonical prompt bodies or context into `AGENTS.md`.

## bootstrap_execution

A source/entrypoint mapping is not sufficient by itself. When `AGENTS.md` is intended to bootstrap the SoT, it must explicitly instruct Codex to read and follow the resolved canonical entrypoint before relying on SoT behavior.

Use an imperative instruction equivalent to:

```text
Use the SoT rooted at <source_root>.
Before performing SoT-dependent work, read and follow <resolved_entrypoint>.
Resolve referenced SoT files relative to <source_root>.
```

Do not duplicate the entrypoint's runtime semantics into `AGENTS.md`. If the entrypoint cannot actually be read, report the unavailable canonical source instead of treating the mapping metadata as loaded runtime behavior.

## prompt_library

When the Source of Truth is available in the working environment:

```text
@edit:path
→ resolve workspace/prompts/path.md
→ bind available parameters
→ render preview only

@run:path
→ resolve workspace/prompts/path.md
→ validate + bind
→ execute rendered task using normal capabilities
```

`@delete` first produces a plan. Confirmation may apply it only with authorized filesystem/Git write access and matching current state.

## instruction_hierarchy

Codex instruction aggregation is an adapter concern, not factual scope or prompt inheritance.

## source_mapping

Repository-relative end-user content lives under `workspace/`; system contracts live under `system/`. If the SoT is external, verify authorized access rather than assuming a path.

## capability_boundary

Connector-backed access uses the real host executor and trusted source binding
described in `system/connectors/readme.md`. Tool responses must pass the shared
host gate before factual content is exposed to the model.

Sandbox, network, filesystem, Git, and approval capabilities are host constraints. Fail/report when required capability is unavailable.
