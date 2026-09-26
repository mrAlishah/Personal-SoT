# runtime_control_cases

These scenarios validate registered runtime-control syntax, metadata, and precedence.

## case_01_prompt_on

Input:

```text
@control:clarify_risk=on

Proceed with the task.
```

Expected: current-prompt `controls.clarify_risk = on`.

## case_02_prompt_off

Input:

```text
@control:clarify_risk=off

Proceed with the task.
```

Expected: current-prompt `controls.clarify_risk = off`.

## case_03_exact_control_identity

Input:

```text
@control:clarifyRisk=off
```

Expected: invalid directive; do not normalize to `clarify_risk`.

## case_04_exact_allowed_values

Inputs `@control:clarify_risk=True`, `@control:clarify_risk=false`, and `@control:clarify_risk=0`.

Expected: invalid values; only values listed in the canonical target's `control_values` metadata are accepted. For `clarify_risk`, the canonical values are `on|off|auto`.

## case_05_last_prompt_value_wins

Input:

```text
@control:clarify_risk=off
@control:clarify_risk=on
```

Expected: `on`.

## case_06_precedence

Given:

```text
global default = on
profile controls.clarify_risk = off
project controls.clarify_risk = on
prompt @control:clarify_risk=off
```

Expected: `off` for the current prompt.

## case_07_profile_fallback

Given global default `on`, selected profile `controls.clarify_risk = off`, and no higher override.

Expected: `off`.

## case_08_project_over_profile

Given selected profile `off`, project/adapter `on`, and no higher override.

Expected: `on`.

## case_09_session_over_project_when_supported

Given project `on` and an explicit supported chat/session control override `off`.

Expected: `off` while that real session override remains applicable.

## case_10_no_invented_session_persistence

Host does not provide a session-control mechanism and prompt uses `@control:clarify_risk=off`.

Expected: prompt-local only; do not persist the value into later prompts.

## case_11_initial_sot_exclusive

Input combines `@do:initialSoT` with `@control:clarify_risk=off`.

Expected: invalid control block; bootstrap resolves configured controls itself.

## case_12_recap_rejects_control

Input combines `@recap:5` with `@control:clarify_risk=off`.

Expected: invalid control block in V1.1.

## case_13_prompt_action_allows_control

Input combines `@do:prompt:<path>` with `@control:clarify_risk=off`.

Expected: valid when all other prompt-action requirements are satisfied; the explicit control applies to that invocation.

## case_14_auto_value

Input:

```text
@control:clarify_risk=auto
```

Expected: valid; the runtime applies the canonical adaptive semantics defined by `system/behavior/clarify_risk.md`.

## case_15_unknown_control

Input:

```text
@control:not_registered=on
```

Expected: invalid configuration; do not invent, fuzzy-match, or silently ignore an unknown control identity.

## case_16_control_metadata_is_canonical

A registered control target contains:

```yaml
---
control_id: clarify_risk
control_values:
  - "on"
  - "off"
  - "auto"
control_default: "auto"
---
```

Expected: validators derive the registered profile-control identity, allowed values, and default from this canonical target metadata rather than from a hard-coded control table.

## case_17_registry_control_id_mismatch

`switch_registry.md` registers identifier `clarify_risk` but the target declares:

```yaml
control_id: another_name
```

Expected: static validation fails. Registry identity and canonical control metadata must agree exactly.

## case_18_missing_control_metadata

A target listed under `switch_registry.md` section `registered_controls` has no control frontmatter or omits one of:

```text
control_id
control_values
control_default
```

Expected: static validation fails; registered controls require machine-readable canonical metadata.

## case_19_invalid_control_default

A registered control declares:

```yaml
control_values:
  - "on"
  - "off"
control_default: "auto"
```

Expected: static validation fails because `control_default` is not an allowed value.

## case_20_duplicate_control_values

A registered control declares duplicate exact values in `control_values`.

Expected: static validation fails; canonical value identities must be unique.

## case_21_profile_validation_tracks_control_metadata

A profile uses `controls.example = guarded`, and a newly registered `example` control canonically declares `guarded` in `control_values`.

Expected: profile validation can accept the value from registry + control metadata without adding `example` or `guarded` to validator source code.
