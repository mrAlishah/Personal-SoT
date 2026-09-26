---
prompt_status: active
prompt_tags:
  - job_search
  - job_analysis
prompt_profiles:
  - research
prompt_formats:
  - md
  - concept
prompt_tone: professional
prompt_depth: deep
required_params:
  - role
  - job_description
optional_params:
  - company
owned_assets: []
---
Analyze the following job opportunity against the relevant canonical professional context available to the active runtime.

Role:

{{role}}

Company:

{{company}}

Job description:

{{job_description}}

Evaluate overall fit, technical fit, missing skills, seniority fit, language requirements, location/remote compatibility, compensation signals when supported, application priority, CV adjustments, and interview-preparation priorities.

End with one of:

```text
apply
apply_with_adjustments
skip
```

Do not invent personal facts that are unavailable from the active canonical context.
