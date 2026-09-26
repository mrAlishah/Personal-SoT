---
prompt_status: active
prompt_tags:
  - coding
  - pull_request
  - review
prompt_profiles:
  - coding
prompt_formats:
  - md
  - concept
prompt_tone: professional
prompt_depth: medium
required_params:
  - pull_request
optional_params:
  - focus
owned_assets: []
---
Review the following pull request for correctness, maintainability, regression risk, security-relevant issues, and test coverage.

Pull request:

{{pull_request}}

Optional review focus:

{{focus}}

Prioritize concrete defects and high-value improvements. Distinguish blocking issues from non-blocking suggestions.
