# automation

## purpose

Defines the V1 boundary for safe automation around the AI Source of Truth.

Automation is optional infrastructure around canonical Markdown. It is not a replacement for canonical modules, routing contracts, or human-owned Git history.

## contracts

```text
automation_contract.md
generated_artifact_contract.md
```

## core_model

```text
canonical markdown
→ source of truth

automation
→ discovery / validation / classification / proposal / reproducible generation

generated artifacts
→ disposable derivatives
```

## allowed_direction

Automation may read authorized canonical content and produce diagnostics, indexes, migration inventories, traces, or proposed edits.

When automation writes canonical content, the write must preserve the same ownership, access, semantic-boundary, and Git-review contracts as a manual edit.

## non_goal

V1 does not require a daemon, MCP server, vector database, custom resolver service, or background synchronization process.
