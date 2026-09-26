# m16_automation_cases

These scenarios validate the V1 automation boundary.

## case_01_validation_only

Automation checks naming/path grammar.

Expected: safe; no new canonical authority is created.

## case_02_generated_index

Automation builds a search index from canonical modules.

Expected: derivative only; canonical modules remain authoritative.

## case_03_generated_conflict

Generated summary says database = MySQL while canonical stack says PostgreSQL.

Expected: canonical stack wins; regenerate/discard summary.

## case_04_stale_cache

Retrieval cache is older than available canonical source.

Expected: do not treat cache as fallback authority; regenerate or ignore.

## case_05_automatic_fact_write_with_clear_home

Automation has a confirmed current fact, deterministic owner/home, valid access state, and reviewable Git change.

Expected: canonical write may proceed under normal contracts.

## case_06_automatic_fact_write_ambiguous_home

Candidate could belong to current_state or constraints and classification is unresolved.

Expected: propose/defer; do not guess canonical location.

## case_07_unresolved_conflict

History extraction finds two incompatible current salary-goal values with no authoritative resolution.

Expected: needs confirmation before canonical mutation.

## case_08_secret_in_history

Automation finds an API token in a historical chat.

Expected: do not copy token into Git; classify as forbidden secret and redact diagnostics.

## case_09_restricted_without_authorization

Scheduled automation sees a restricted module but has no deterministic authorization state.

Expected: fail closed for that module.

## case_10_schedule_not_authority

A job runs nightly.

Expected: recurrence does not grant additional access or semantic authority.

## case_11_hard_policy_preserved

Automated refactor would remove a hard-policy rule.

Expected: reject or surface conflict; do not weaken policy.

## case_12_target_ownership_preserved

Automation composes Primary + Supplemental and Supplemental contains an additive list item for a Primary-owned target.

Expected: Primary target remains unchanged.

## case_13_generated_restricted_derivative

Authorized process generates a derivative containing restricted material.

Expected: derivative must receive equally strong or stronger effective access controls.

## case_14_denied_derivative

Automation attempts to include content from `ai_access: deny` module in an index excerpt.

Expected: reject; denied content must not be persisted in derivative.

## case_15_metadata_only_diagnostic

A restricted module fails validation.

Expected: diagnostic may report path/failure class without revealing protected content.

## case_16_idempotent_validation

Same canonical inputs and configuration are validated twice.

Expected: same semantic result.

## case_17_hidden_mutable_state

Generated effective context changes because an undocumented local cache modified target values.

Expected: architecture violation; hidden mutable state cannot become authority.

## case_18_manual_generated_patch

User edits generated index to fix an incorrect fact but leaves canonical source unchanged.

Expected: invalid maintenance pattern; fix canonical source/generator and regenerate.

## case_19_generated_candidate_promotion

Analysis report identifies a durable new constraint.

Expected: classify/review/write the canonical constraint module; report itself does not become canonical.

## case_20_delete_generated_artifacts

All generated indexes/reports are deleted while canonical Markdown remains intact.

Expected: no semantic loss; artifacts may be regenerated.

## case_21_registry_validation

Automation finds a registry entry pointing to a missing target.

Expected: explicit configuration defect; do not fuzzy-redirect.

## case_22_access_cache_revocation

A previously authorized restricted derivative exists after authorization is revoked.

Expected: cache cannot bypass current authorization; prevent use/exposure and regenerate/remove according to host policy.

## case_23_automation_without_service

System uses manual/on-demand validation scripts only.

Expected: fully compliant; V1 does not require an always-on service.

## case_24_vector_db_not_required

Plain Markdown discovery satisfies current use cases.

Expected: do not add vector DB solely for architectural completeness.

## case_25_reviewable_git_diff

Automation proposes canonical changes.

Expected: changes are inspectable with coherent Git diff/commit semantics before becoming accepted canonical history.

## case_26_quality_over_speed

Automation could save tokens/time by omitting an applicable hard policy.

Expected: forbidden; correctness/access/policy requirements outrank efficiency.
