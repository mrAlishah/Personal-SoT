# m8_end_to_end_resolution_cases

These scenarios validate the M1–M7 contracts together using only `tests/fixtures/m8/` synthetic data.

The fixture registry is test-only and MUST NOT populate production `routing/context_registry.md`.

## baseline_nested_scope

Selected primary:

```text
org/acme/projects/payment_service/reconciliation
```

Expected scope chain:

```text
org/acme
org/acme/projects/payment_service
org/acme/projects/payment_service/reconciliation
```

## case_01_nearest_scalar_wins

Expected effective values:

```text
database = postgresql
runtime = go_1_24
messaging = kafka
```

Organization MySQL is shadowed by project PostgreSQL. Organization Go 1.23 is shadowed by project Go 1.24.

## case_02_list_merge

Expected primary-chain `required_tests`:

```text
unit
integration
contract
```

Preserve first effective order and deduplicate inside the primary scope chain.

## case_03_map_deep_merge

Expected settings:

```yaml
observability: advanced
retries: 5
tracing: enabled
```

Map deep merge occurs inside the primary authoritative scope chain.

## case_04_hard_policy_accumulation

Expected active hard policies:

```text
credential_exposure
token_logging
```

Neither may be weakened by nested scope, supplemental context, profile, presentation, or token budget.

## case_05_soft_policy_specificity

Organization soft `service_api_protocol = REST`; project soft value = gRPC.

Expected: project gRPC preference.

## case_06_denied_module_excluded

`reconciliation/internal_notes.md` has `ai_access: deny`.

Expected: it never enters candidate/effective context and its content is not leaked through provenance.

## case_07_decision_progressive_disclosure

Question: `What messaging system is currently used?`

Expected: current `stack.md` is sufficient; `decisions/use_kafka.md` is optional deep evidence and should not load.

## case_08_decision_loaded_for_why

Question: `Why is Kafka used for reconciliation?`

Expected: load current stack plus relevant accepted decision rationale.

## case_09_primary_vs_personal_supplemental_scalar

Prompt contexts:

```text
@ctx:org/acme/projects/payment_service/reconciliation
@ctx:personal
```

Personal fixture says `database = sqlite`.

Expected: primary project-owned `database = postgresql` remains effective.

## case_10_supplemental_does_not_change_primary_requirement

Personal fixture contains:

```text
required_tests = exploratory
```

Primary chain already owns `required_tests`.

Expected:

```text
required_tests = [unit, integration, contract]
```

`exploratory` does not extend the primary-owned list.

## case_11_cross_org_isolation

Primary ACME context without explicit Beta selection.

Expected: Beta MongoDB/Node.js values are unavailable to effective context.

## case_12_explicit_cross_org_supplemental

Primary ACME + explicit supplemental Beta.

Expected: Beta may fill only relevant semantic targets absent from Primary. It cannot replace or extend ACME-owned database/runtime/list/map/soft-policy targets. Applicable hard policies remain cumulative.

## case_13_unresolved_explicit_primary_fails_closed

Explicit syntactically valid scope is not in the test registry.

Expected: unresolved primary; no fallback to configured default or personal.

## case_14_invalid_context_directive_can_fallback

Malformed `@ctx` never becomes a valid explicit request.

Expected: if no other valid explicit context exists, default_scope/personal fallback may proceed with a warning.

## case_15_failed_supplemental_does_not_break_primary

Primary resolves; one supplemental is unresolved; later Personal resolves.

Expected: primary remains, failed supplemental excluded with warning, Personal retained.

## case_16_g_architecture_review_profile

Prompt:

```text
@profile:architecture/review
```

Expected profile configuration:

```text
behaviors = reasoning + research + communication
formats = compare
tone = professional
depth = deep
```

No factual context is selected by the profile.

## case_17_prompt_depth_over_profile

`architecture/review` + `@depth:short`.

Expected: short depth; profile remains otherwise active.

## case_18_multiple_profiles

Explicit profiles in order:

```text
tech/learn
research/deep
```

Expected:

```text
behaviors = reasoning + teaching + communication + research
formats = eli5
tone = professional
depth = deep
```

## case_19_explicit_profiles_replace_default_profile

Adapter default profile = code/review; prompt explicitly selects research/deep.

Expected: research/deep only as selected profile set; code/review is not hidden-composed.

## case_20_german_learning_language

`lang/german` with no prompt language override.

Expected:

```text
primary_language = german
supporting_languages = [english, persian]
formats = [eli5, vocab]
tone = human
depth = medium
```

## case_21_prompt_language_override

`lang/german`, prompt explicitly requests Persian for this answer.

Expected: Persian primary for this prompt; no persistent change to profile.

## case_22_format_disable_after_profile

`lang/german` provides `eli5 + vocab`; prompt includes `@no:fmt:vocab`.

Expected effective formats: `eli5` only.

## case_23_format_reenable_order

Prompt operations:

```text
@no:fmt:vocab
@fmt:vocab
```

Expected: vocab enabled.

## case_24_unknown_profile

Unknown explicit profile with no valid explicit profiles.

Expected: invalid directive warning; lower profile selection may continue because no valid explicit profile became active.

## case_25_profile_does_not_override_policy

Codinresearch/deep/profile guidance conflicts with hard policy.

Expected: hard policy wins; profile remains active only for compatible behavior/presentation.

## case_26_token_budget_prunes_optional_first

Tight context budget on a simple stack question.

Expected ordering:

```text
keep access-valid mandatory policies
keep authoritative required stack facts
prune unrelated optional current_state/decision evidence first
```

## case_27_depth_does_not_expand_scope

`@depth:deep` on ACME primary.

Expected: deeper rendering/evidence where relevant; no implicit Personal or Beta scope.

## case_28_registry_bootstrap

Resolver uses compact test registry to resolve scope identities, then loads selected modules.

Expected: no need to scan every fixture file before scope resolution.

## case_29_provenance_scalar

For effective `database = postgresql`, provenance should explain:

```text
source_scope = org/acme/projects/payment_service
shadowed_value = mysql
shadowed_source = org/acme
resolution = nearest_authoritative_scope
```

## case_30_provenance_denied

Denied `internal_notes.md` must not expose its contents as a shadowed value or diagnostic detail.

## case_31_current_truth_vs_decision

Accepted Kafka decision explains rationale but current stack remains the authoritative `messaging = kafka` truth.

## case_32_no_full_language_duplication

German primary with English/Persian supporting on a normal non-vocab answer.

Expected: no automatic full three-language duplication.

## case_33_effective_context_minimum

For `What database does reconciliation use?`, minimum sufficient authoritative context should primarily require applicable mandatory policy metadata plus the relevant stack chain; unrelated current state, decision rationale, Beta, and Personal are not loaded unless explicitly/relevantly needed.

## case_34_complete_trace

Given:

```text
@ctx:org/acme/projects/payment_service/reconciliation
@ctx:personal
@profile:architecture/review
@depth:short

Compare the current messaging choice with its relevant constraints.
```

Expected high-level effective configuration:

```text
primary_scope = reconciliation
supplemental = personal
behaviors = reasoning + research + communication
formats = compare
tone = professional
depth = short
hard_policies = credential_exposure + token_logging
messaging = kafka
required_tests = unit + integration + contract
```

Personal cannot replace or extend primary-owned targets. Denied notes are excluded. Decision evidence is loaded only if the comparison requires the rationale.

## case_35_supplemental_fills_missing_target_when_relevant

Primary ACME chain has no `preferred_region`. Personal supplemental defines:

```text
preferred_region = europe
```

Task explicitly asks for the relevant supplemental region preference.

Expected: `preferred_region = europe` may enter effective context because Primary does not own that target and Personal is the first authoritative supplemental that supplies it.

## case_36_irrelevant_gap_fill_is_not_loaded

Same contexts as case 35, but task is only `What database is used?`.

Expected: Personal `preferred_region` remains unloaded/unused because target ownership permission does not bypass relevance selection.

## case_37_later_supplemental_cannot_modify_first_supplemental_target

Primary lacks target T. Supplemental 1 introduces T; Supplemental 2 also defines T.

Expected: Supplemental 1 owns T; Supplemental 2 cannot replace or add to it.

## case_38_language_precedence_is_presentation_only

Current prompt explicitly requests German while primary database is PostgreSQL.

Expected: response language changes to German; database remains PostgreSQL with unchanged provenance.

## case_39_hard_policy_cross_context_exception

Primary context has hard policy A and an explicit accessible supplemental has applicable hard policy B.

Expected: A + B. Ordinary target ownership does not suppress applicable hard policies.

## exit_criterion

M8 passes when each scenario can be resolved deterministically from M1–M7 contracts with an explainable provenance path and without loading unrelated synthetic context.
