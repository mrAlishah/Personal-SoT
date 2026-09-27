# precedence_cases

These cases validate `routing/precedence.md` as the canonical owner of source authority and target ownership.

## case_01_context_selection

```text
explicit @ctx
> default_scope
> personal fallback
```

Expected: highest applicable source selects primary scope.

## case_02_primary_over_supplemental_fact

Primary project defines `go_version = 1_24`.
Supplemental personal context prefers `latest`.

Expected project fact: `1_24`.

## case_03_specificity

```text
organization: transport = rest
project: transport = grpc
```

Expected: `grpc`.

## case_04_hard_policy_accumulation

Owner hard policy A and project hard policy B.

Expected: A + B; neither is overridden.

## case_05_soft_policy_specificity

Owner soft policy prefers REST; project soft policy prefers gRPC for the same preference domain.

Expected project soft policy.

## case_06_multiple_profiles

Input:

```text
@profile:g.technical.learning
@profile:g.research
```

Expected:

```text
additive profile components → compose
tone/depth profile defaults → `g.research` wins if conflicting
```

## case_07_explicit_profile_over_default_profile

Given `default_profile = g.coding` and explicit `@profile:g.research`.

Expected selected profile: `g.research`; do not compose `g.coding`.

## case_08_prompt_depth_over_profile_and_adapter

Given:

```text
profile depth = deep
adapter default_depth = medium
prompt @depth:short
```

Expected: `short`.

## case_09_prompt_format_removal

Profile formats: `yaml + eli5`.
Prompt:

```text
@no:fmt:yaml
@fmt:comparison_table
```

Expected: `eli5 + comparison_table`.

## case_10_adapter_fact_duplication

Adapter says project database is MySQL; canonical project context says PostgreSQL.

Expected: treat adapter fact duplication as architecture violation, not a valid higher-precedence fact.

## case_11_recency_does_not_override_authority

Newer supplemental fact conflicts with older authoritative primary fact.

Expected: primary authority remains unless temporal module contract explicitly changes it.

## case_12_token_budget_does_not_change_truth

Cheaper supplemental fact conflicts with costlier authoritative primary fact.

Expected: token optimization cannot select the lower-authority fact merely because it is cheaper.

## case_13_primary_target_blocks_supplemental_additive_merge

Primary defines `required_tests = [unit, integration]`. Supplemental defines `[exploratory]` for the same target.

Expected: primary owns the target; supplemental is excluded from authority for that target. Merge mechanics must therefore preserve `[unit, integration]`.

## case_14_supplemental_fills_primary_gap

Primary has no `preferred_region`; Supplemental 1 defines `europe`.

Expected: Supplemental 1 may own/supply the target if relevant/access-valid.

## case_15_supplemental_order_owns_new_target

Primary lacks target T. Supplemental 1 defines T; Supplemental 2 also defines T.

Expected: Supplemental 1 owns T because it is the first authoritative supplemental source; Supplemental 2 is excluded for T.

## case_16_hard_policy_exception_to_target_ownership

Primary and supplemental each contain different applicable hard policies.

Expected: both are authoritative/applicable because hard policies accumulate.

## case_17_prompt_language_over_profile_language

Profile language is German with English/Persian support. Current prompt explicitly requests Persian.

Expected: Persian is primary for that prompt only; profile is not mutated.

## case_18_adapter_language_over_profile_without_prompt_override

Adapter language default is English; selected profile language default is German; no prompt-local language request exists.

Expected: English adapter language default wins within the language lane.

## case_19_language_does_not_change_fact_authority

Prompt requests German while primary project database is PostgreSQL.

Expected: response language changes; database authority does not.

## boundary_with_merge_strategy

`system/routing/merge_strategy.md` may demonstrate that merge mechanics respect an already-resolved authority result, but it must not own or independently redefine the primary/supplemental winner rules validated here.
