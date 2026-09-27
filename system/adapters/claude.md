# claude_adapter

## integration_surface

Use Claude Code project memory/instruction files such as `CLAUDE.md` as a thin bootstrap surface where appropriate.

## adapter_role

A project `CLAUDE.md` should primarily contain Source-of-Truth mapping/defaults and genuinely Claude-specific workflow instructions. Do not copy canonical prompt bodies or personal/project truth into it.

## bootstrap_execution

A source/entrypoint mapping is not sufficient by itself. When `CLAUDE.md` is intended to bootstrap the SoT, it must explicitly instruct Claude to read and follow the resolved canonical entrypoint before relying on SoT behavior.

The thin wrapper may use a Claude-supported file import when that import deterministically loads the intended entrypoint, or an imperative instruction equivalent to:

```text
Use the SoT rooted at <source_root>.
Before performing SoT-dependent work, read and follow <resolved_entrypoint>.
Resolve referenced SoT files relative to <source_root>.
```

Do not duplicate the entrypoint's runtime semantics into `CLAUDE.md`. If the entrypoint cannot actually be read, report the unavailable canonical source instead of treating the mapping metadata as loaded runtime behavior.

## prompt_library

When canonical prompt files are reachable:

```text
@edit:prompt:path
→ resolve workspace/prompts/path.md
→ substitute supplied params
→ render preview only

@do:prompt:path
→ resolve workspace/prompts/path.md
→ validate + bind
→ execute with available tools/capabilities
```

`@delete` is analysis-only until explicit confirmation and still requires real write permission/revalidation.

Do not turn imports/project memory into unconditional loading of `workspace/prompts/`; resolve one exact prompt first and search only for discovery.

## composer_boundary

Canonical `@edit` does not promise pre-send composer insertion.

## memory_boundary

Claude-specific memory/instruction files are adapter configuration, not canonical prompt/context stores.

## capability_boundary

Use `system/connectors/source_contract.md` and its host integration guide for
connector-backed sources. Claude Code may use a permitted host executor;
Claude Web must report limited capability if no pre-exposure gate is available.

Filesystem, network, tool, model, and permission capabilities are external runtime constraints. Surface unavailable canonical content/write capability rather than simulating success.
