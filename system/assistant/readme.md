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

`workspace/prompts/sot/assistant.md` is the natural-language entry point.
`guidance.py` implements read-only guidance over existing Prompt Explorer and
Personalization Advisor evidence. It does not parse a new directive language,
own a capability registry, or perform writes. Actual Preview/Apply remain with
the selected canonical workflow and its existing Builder.
