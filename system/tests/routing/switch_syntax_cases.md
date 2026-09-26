# switch_syntax_cases

These cases validate `routing/switch_syntax.md`. They are test artifacts, not runtime instructions.

## case_01_leading_control_block

Input:

```text
@depth:deep
@tone:professional

Explain CQRS.
```

Expected:

```text
depth = deep
tone = professional
```

## case_02_switch_like_text_in_body

Input:

```text
Explain what @depth:deep means.
```

Expected: no runtime switch activation.

## case_03_last_single_value_wins

Input:

```text
@depth:short
@depth:deep

Explain CQRS.
```

Expected: `depth = deep`.

## case_04_format_source_order

Input:

```text
@fmt:yaml
@fmt:eli5
@no:fmt:yaml

Explain CQRS.
```

Expected format set: `eli5`.

## case_05_multiple_contexts

Input:

```text
@ctx:org/acme/projects/payment_service
@ctx:personal

Review the design.
```

Expected:

```text
primary = org/acme/projects/payment_service
supplemental = personal
```

## case_06_explicit_profiles_replace_default_profile

Given:

```text
default_profile = coding
```

Input:

```text
@profile:research
@profile:technical_learning

Explain event sourcing.
```

Expected selected profiles:

```text
research
technical_learning
```

`coding` is not silently composed.

## case_07_default_profile_fallback

Given:

```text
default_profile = coding
```

Input has no explicit `@profile`.

Expected selected profile: `coding`.

## case_08_invalid_switch

Input:

```text
@Depth:deep
@depth:medium

Explain CQRS.
```

Expected:

```text
@Depth:deep → rejected with diagnostic
@depth:medium → applied
```

## case_09_unsupported_no_target

Input:

```text
@no:policy:security

Explain the system.
```

Expected: invalid directive; hard policies are not removed.

## case_10_initial_sot_reserved_action

Input:

```text
@do:initialSoT
```

Expected: exact reserved runtime action; execute canonical runtime bootstrap/re-anchor semantics.

## case_11_initial_sot_has_no_parameters

Input:

```text
@do:initialSoT
@param:x=[1]
```

Expected: invalid control block; `@do:initialSoT` accepts no parameters.

## case_12_initial_sot_is_exclusive

Input:

```text
@do:initialSoT
@profile:research
```

Expected: invalid control block; bootstrap action resolves effective deployment defaults itself and does not compose companion runtime switches.

## case_13_initial_sot_case_is_exact

Input:

```text
@do:initialsot
```

Expected: invalid/unresolved action; do not case-correct to `@do:initialSoT`.

## case_14_start_language_prompt_override

Given project/adapter default:

```text
start_language: en
```

Input:

```text
@start:fa

Explain context drift.
```

Expected: effective response start language is `fa` for this prompt; the rest of the response still follows the ordinary language lane.

## case_15_start_language_auto_clears_default

Given project/adapter default:

```text
start_language: fa
```

Input:

```text
@start:auto

Explain context drift.
```

Expected: the forced Persian opening is disabled for this prompt; ordinary language behavior decides the opening.

## case_16_start_language_last_explicit_wins

Input:

```text
@start:de
@start:fa

Explain context drift.
```

Expected: effective response start language is `fa`.

## case_17_start_language_invalid_value

Input:

```text
@start:not-a-language

Explain context drift.
```

Expected: invalid/unresolved start-language directive; do not guess or map it to another language.

## case_18_initial_sot_rejects_start_companion

Input:

```text
@do:initialSoT
@start:fa
```

Expected: invalid control block; `@do:initialSoT` remains exclusive and resolves deployment defaults itself.
