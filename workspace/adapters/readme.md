# workspace adapters

Client bootstrap files live here. Generic adapter semantics remain under `system/adapters/`; Assistant and write semantics remain under `system/assistant/`.

```text
runtime_entrypoint.md                 shared canonical entrypoint
public_bootstrap.md                   safe public defaults
AGENTS.md / CLAUDE.md                 local write-capable agent adapters
chatgpt_project_instructions.md       capability-aware web adapter
claude_web_project_instructions.md    capability-aware web adapter
```

Root `AGENTS.md` and `CLAUDE.md` are thin host discovery wrappers. Adapters declare only source, entrypoint, defaults, and actual host capability; they do not copy canonical workflows.

For Doctor connectivity, each client adapter declares only:

```text
client_name
discovery_surface
entrypoint
```

Actual write capability is supplied by the active host at runtime; it is not hardcoded in adapter metadata.
