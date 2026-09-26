# Personal SoT Assistant first vertical slice

## Outcome

A beginner can ask a capable local agent to create one Personal project, review the proposal, confirm it, use the resulting project as context, and later update its current state. The user never needs to know file paths or schemas.

The same guided conversation works in ChatGPT and Claude Web, but a host without repository write capability stops after preview and gives truthful validation guidance. It never claims a mutation occurred.

## Ownership

Client-neutral semantics live under `system/assistant/`:

```text
assistant_contract.md    intent categories and capability negotiation
guided_flow_contract.md  beginner interaction behavior
safe_write_contract.md   proposal, confirmation, write and validation rules
project_workflow.md      create/use/update project semantics
```

Reusable entry prompts live under `workspace/prompts/sot/`. Adapters contain only source discovery, host capability, and the canonical entrypoint. They do not copy workflow steps.

Root `AGENTS.md` and `CLAUDE.md` are thin host-required instruction surfaces, not new content roots. Their only job is to point local agents to `workspace/adapters/runtime_entrypoint.md` and declare that local repository writes remain subject to host authorization.

## Capability model

```text
read only      → discover, explain, ask questions, recommend
preview only   → complete proposal and validation guidance, no mutation claim
read + write   → preview, confirm, revalidate, write, run validators, report
```

The capability is supplied by the host. A prompt, user confirmation, profile, or adapter default never grants filesystem permission.

Codex and Claude Code are the first executable write adapters. ChatGPT and Claude Web use the same canonical flows with preview-only behavior when write tools are unavailable. A future CLI/helper may implement the same safe-write boundary without changing the Core contracts.

## Create project flow

```text
understand intent
→ explain the short flow in the selected language
→ ask one adaptive question at a time
→ classify the minimum semantic owners
→ check existing projects and conflicts
→ propose identifier, scope, files, registry entry and exact content
→ preview everything that would change
→ ask for explicit confirmation
→ re-check current state and host permission
→ write atomically enough to avoid an unregistered partial project
→ run validation
→ report files, scope and useful beginner requests
```

`project.md` and `current_state.md` are created when their semantics are known. `objectives.md`, `constraints.md`, and other modules are created only when the answers establish independently useful content. Empty template modules are forbidden.

The new scope is registered in `system/routing/context_registry.md` as part of the same proposal. This is Personal overlay configuration, not a change to registry grammar.

## Use and update flow

After creation, the Assistant teaches a natural-language request first:

```text
Using my German-learning project, what should I do next?
```

It may then show the optional expert form:

```text
@ctx:personal/projects/german_learning
```

For an update, the Assistant resolves the project, reads the minimum current owners, asks what changed, separates current state from objectives/constraints/decisions, previews the diff, confirms, writes, validates, and reports. `current_state.md` remains current effective state rather than a changelog.

## Validation

The slice is accepted when:

- prompt validation accepts the three Assistant prompts;
- scenario cases cover Guided, Natural, and preview-only hosts;
- a runnable integration check creates a fake project, registers it, validates it, updates `current_state.md`, and validates again;
- Core, prompt, public-distribution, and Assistant tests pass;
- adapters contain no duplicated safe-write or project-workflow semantics.

## Excluded

- standalone CLI/helper or connector;
- GUI, MCP server, cloud backend, accounts, or background mutation;
- prompt/profile builders and broad Personal onboarding beyond what the first project needs;
- silent mutation or simulated write success on web clients.
