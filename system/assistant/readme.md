# Personal SoT Assistant

Client-neutral Assistant semantics live here.

```text
assistant_contract.md    intent and capability boundary
guided_flow_contract.md  beginner conversation behavior
safe_write_contract.md   canonical mutation pipeline
setup_workflow.md         repository-to-first-task onboarding
project_workflow.md      create, use and update a project
prompt_explorer_workflow.md  discover and recommend existing prompts
prompt_builder_workflow.md   reuse, customize, edit or create a prompt
personalization_workflow.md  discover and compose response customization
```

Adapters point to these contracts and declare host capabilities. They do not copy the workflows.
