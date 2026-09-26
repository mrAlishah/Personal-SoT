# Personal SoT Assistant

Client-neutral Assistant semantics live here.

```text
assistant_contract.md    intent and capability boundary
guided_flow_contract.md  beginner conversation behavior
safe_write_contract.md   canonical mutation pipeline
project_workflow.md      create, use and update a project
```

Adapters point to these contracts and declare host capabilities. They do not copy the workflows.
