---
prompt_status: active
prompt_tags:
  - assistant
  - beginner
  - diagnostics
  - doctor
prompt_profiles: []
prompt_formats: []
prompt_tone: professional
prompt_depth: medium
required_params: []
optional_params:
  - concern
owned_assets: []
---
Execute `system/diagnostics/doctor_contract.md` through the Personal SoT Assistant.

User concern:

{{concern}}

Use the user's selected language. Resolve actual host capability, run Doctor only when available, keep technical detail optional, and never apply a repair during diagnosis.
