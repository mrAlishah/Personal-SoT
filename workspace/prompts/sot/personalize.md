---
prompt_status: active
prompt_tags:
  - assistant
  - beginner
  - personalization
prompt_profiles: []
prompt_formats: []
prompt_tone: professional
prompt_depth: medium
required_params: []
optional_params:
  - request
owned_assets: []
---
Execute `system/assistant/personalization_workflow.md` through the Personal SoT
Assistant.

User request:

{{request}}

Use the selected language, classify semantic lanes without inventing aliases,
and recommend existing composition before offering Profile creation. Keep
Advanced directives optional and route any Profile write through the canonical
safe-write flow.
