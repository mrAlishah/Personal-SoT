# v1_1_prompt_contract_cases

These scenarios validate V1.1 Prompt Library semantics.

## case_01_prompt_identity
`workspace/prompts/coding/review_pr.md` resolves exactly as `coding/review_pr`; no registry/fuzzy alias.

## case_02_do_executes
`@do:prompt:coding/review_pr` with all required params → render, validate, execute.

## case_03_edit_does_not_execute
`@edit:prompt:coding/review_pr` → rendered preview only; stop before task execution.

## case_04_delete_plans_only
`@delete:prompt:coding/review_pr` → analyze file/owned assets/inbound refs; show plan; no deletion.

## case_05_confirm_delete
Current deletion plan + `@confirm:delete:prompt:coding/review_pr` → revalidate state, then delete/repair only if unchanged and write-authorized.

## case_06_changed_after_delete_plan
Prompt/reference state changes after plan → confirmation invalid; require new plan.

## case_07_shared_modules_preserved
Deleted prompt references `coding`, `md`, `concept` → shared modules remain.

## case_08_action_exclusivity
One block contains `@do` and `@edit` → invalid; no line-order choice.

## case_09_bare_prompt_invalid
`@prompt:coding/review_pr` → invalid because action is ambiguous.

## case_10_single_line_param
`@param:target_language=[german]` → exact value `german`.

## case_11_param_spaces
`@param:role=[Senior Backend Engineer]` → spaces preserved.

## case_12_multiline_param

```text
@param:job_description=[[
line one
[
  "array"
]
]]
```

Expected: all content preserved until standalone `]]`; standalone `]` remains data.

## case_13_literal_closing_delimiter
A multiline value needs literal standalone `]]` and uses `\]]`.

Expected: decoded value contains literal `]]`; parameter remains open until next unescaped standalone `]]`.

## case_14_switch_text_inside_param
Multiline parameter contains `@fmt:yaml` → literal data, not executable directive.

## case_15_duplicate_param
Same param twice → last explicit value wins; duplicate diagnostic available.

## case_16_unknown_param
Undeclared explicit param → invalid diagnostic; do not silently inject/ignore.

## case_17_missing_required_do
Missing required param under `@do` → fail closed; no execution.

## case_18_missing_required_edit
Missing required param under `@edit` → preserve placeholder + list unresolved required param.

## case_19_optional_edit
Optional param absent under edit → preserve placeholder + optional/unbound diagnostic.

## case_20_optional_do
Optional param absent under do → empty substitution only when resulting template is fully resolved/renderable.

## case_21_implicit_input
Template has `{{input}}` + invocation body → body binds to input.

## case_22_explicit_input_precedence
Explicit `@param:input=[...]` + body → explicit input wins.

## case_23_unconsumed_body_do
Body exists but template has no input → fail closed; never discard/append silently.

## case_24_unconsumed_body_edit
Same under edit → preview + unconsumed-body diagnostic.

## case_25_parameter_no_switch_injection
Parameter value contains `@ctx:`/`@delete:` → substituted literal text cannot become executable control.

## case_26_status_active
Active prompt → do/edit allowed subject to validation.

## case_27_status_draft
Draft prompt → edit allowed; do blocked.

## case_28_status_deprecated
Deprecated prompt → edit/recovery with warning; do blocked.

## case_29_prompt_context_boundary
Prompt manifest defines factual context → unsupported field/configuration defect.

## case_30_prompt_profile_precedence
Prompt defaults `research`; invocation explicitly selects `coding` → explicit selection replaces prompt profile selection.

## case_31_prompt_format_composition
Prompt defaults `md + concept`; invocation `@no:fmt:concept` → md remains, concept disabled.

## case_32_prompt_tone_depth_precedence
Prompt defaults professional/deep; invocation neutral/short → neutral/short.

## case_33_owned_asset_boundary
Owned asset outside `workspace/prompts/_assets/<prompt_identity>/` → validation error.

## case_34_prompt_to_prompt_include
Runtime prompt include/inheritance → unsupported in V1.1.

## case_35_exact_delete_reference_repair
Another document references deleted prompt identity → plan identifies inbound ref before apply.

## case_36_no_write_capability
Read-only client → edit may render, delete may plan, confirmation cannot apply deletion.

## case_37_exact_path_token_efficiency
One exact prompt selected → do not load all prompts or build full prompt registry.

## case_38_dynamic_personal_library
User changes a conforming Personal prompt → Personal content maintenance; no Core architecture change.

## case_39_quality_over_convenience
Ambiguous prompt path/required param → explicit diagnostic/fail-closed rather than guess.
