# v1_1_prompt_routing_cases

## case_01_action_names

Only these prompt actions are canonical:

```text
@do:prompt
@edit:prompt
@delete:prompt
@confirm:delete:prompt
```

Bare `@prompt` is invalid.

## case_02_exact_path

`@do:prompt:coding/review_pr` resolves exactly to `workspace/prompts/coding/review_pr.md`.

No prompt registry or alias lookup.

## case_03_path_case_sensitive

`@do:prompt:Coding/review_pr` is invalid/unresolved rather than normalized.

## case_04_one_action

Two prompt actions in one control block are invalid.

## case_05_param_with_do

`@param` is valid with `@do` and `@edit` when declared by selected prompt.

## case_06_param_with_delete

`@param` with `@delete`/`@confirm:delete` is invalid in V1.1.

## case_07_multiline_param_control_block

An open multiline param keeps the parser in literal parameter mode until standalone closing `]]`.

Blank lines inside do not end the control block.

## case_08_directive_inside_multiline_param

`@ctx:personal` inside a multiline param value remains literal data.

## case_09_invocation_body

Text after the closed control block is ordinary body and may bind only to `{{input}}`.

## case_10_prompt_profiles

Explicit `@profile` on invocation outranks/replaces prompt-manifest profile defaults.

## case_11_prompt_formats

Prompt formats form a base set; explicit `@fmt/@no:fmt` operations apply afterward.

## case_12_prompt_tone_depth

Explicit tone/depth outrank prompt manifest tone/depth.

## case_13_prompt_context_not_default

Prompt manifest cannot select factual context; explicit/default scope remains routing-owned.

## case_14_prompt_registry_absent

`system/routing/switch_registry.md` intentionally contains no prompt-path entries.

## case_15_discovery_not_identity

Tag/search discovery may suggest `coding/review_pr`; after selection exact path identity governs.

## case_16_unresolved_prompt

Valid-shaped but missing prompt path fails closed; do not choose nearest template.

## case_17_delete_confirmation_path_match

Confirmation path must exactly match current deletion plan path.

## case_18_parameter_substitution_no_reparse

Runtime directives appearing after parameter substitution are never reparsed as executable control directives.
