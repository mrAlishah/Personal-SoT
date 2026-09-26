# v1_static_validation_cases

These scenarios define expected behavior for `system/validation/validate_v1.py`.

## case_01_core_isolation

Generic Core contains `workspace/context/personal/identity.md`.

Expected: fail.

## case_02_personal_mode_allows_personal_context

Personal checkout contains canonical `workspace/context/personal/` modules.

Expected: valid when the modules satisfy all other checks.

## case_03_missing_ai_access

Canonical personal/project context file has no frontmatter access state.

Expected: fail.

## case_04_invalid_ai_access

Canonical context uses `ai_access: private`.

Expected: fail; only `allow|restricted|deny` are valid.

## case_05_external_filename_exception

`AGENTS.md` and `CLAUDE.md` exist in adapter/example locations.

Expected: accepted despite uppercase external spelling.

## case_06_owned_name_convention

Repository-owned file is named `Current-State.md`.

Expected: fail lowercase_snake_case check.

## case_07_profile_reference

Profile references `teaching` behavior and the canonical file exists.

Expected: pass.

## case_08_unknown_profile_field

Profile manifest contains `context:` or another unsupported top-level field.

Expected: fail.

## case_09_missing_profile_target

Profile references `behaviors: [nonexistent]` through the supported simple manifest shape.

Expected: fail unresolved reference.

## case_10_switch_registry_target

Switch registry maps a format/tone/depth/profile to a missing Markdown target.

Expected: fail.

## case_11_context_registry_target

Personal context registry points to a missing canonical scope directory.

Expected: fail.

## case_12_example_scope_registered

Context registry points at a `guides/developer/examples/` path.

Expected: fail.

## case_13_decision_status

Decision artifact has `decision_status: active`.

Expected: fail because V1 lifecycle is `proposed|accepted|superseded|deprecated`.

## case_14_valid_decision_status

Decision uses `decision_status: accepted`.

Expected: pass that check.

## case_15_raw_password_assignment

Canonical context contains `password: real_value`.

Expected: fail secret guard.

## case_16_safe_secret_sentinel

Canonical context contains `password: not_stored` solely as a safe pattern.

Expected: secret guard does not flag it.

## case_17_secret_reference_path

`secret_references.md` contains an external password-manager path without a secret assignment.

Expected: pass secret guard.

## case_18_examples_not_access_checked_as_runtime

Fake context under `guides/developer/examples/context/` uses instructional markup.

Expected: it is not treated as canonical runtime context for `ai_access` enforcement.

## case_19_semantic_duplication

Two canonical modules duplicate the same fact but are structurally valid.

Expected: static validator may pass; semantic review must catch this. The validator is not a substitute for architectural review.

## case_20_stale_fact

Canonical module contains an old but structurally valid fact.

Expected: static validator may pass; currentness is a semantic/evidence concern.

## case_21_sensitive_monolith

One restricted file mixes several independently retrieved health domains but satisfies structural syntax.

Expected: static validator may pass; atomicity/token/privacy review must catch the semantic problem.

## case_22_exit_code

One deterministic violation exists.

Expected: validator exits non-zero and lists the failing path/rule without printing protected content.

## acceptance

Static validation is successful when deterministic repository/schema regressions are machine-detectable without adding resolver infrastructure or pretending that structural lint proves semantic correctness.
