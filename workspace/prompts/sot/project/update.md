---
prompt_status: active
prompt_tags:
  - assistant
  - beginner
  - project
  - maintenance
prompt_profiles: []
prompt_formats: []
prompt_tone: professional
prompt_depth: medium
required_params: []
optional_params:
  - project_reference
  - update_evidence
owned_assets: []
---
Execute the update-current-state flow in `system/assistant/project_workflow.md` through the canonical Assistant, guided-flow, and safe-write contracts.

Project reference:

{{project_reference}}

Candidate update evidence:

{{update_evidence}}

Resolve exactly one registered project, classify the evidence before preview, and never treat missing host write capability as a successful update.
