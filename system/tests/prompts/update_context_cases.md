# update_context_cases

These scenarios validate `workspace/prompts/sot/context/update.md` as the unified factual-context maintenance workflow.

## case_01_personal_scope_updates_personal_owner

Active scope is `personal` and candidate evidence contains a durable non-project personal fact.

Expected: classify the fact and update the smallest established Personal semantic owner; do not require a project scope.

## case_02_personal_scope_sensitive_owner

Active scope is `personal` and candidate evidence is a sensitive family/health/finance fact with an established authorized sensitive owner.

Expected: preserve sensitive placement and access metadata; update the appropriate existing sensitive owner rather than an unrestricted Personal file.

## case_03_personal_scope_does_not_guess_project

Active scope is `personal` and candidate evidence concerns a project-specific implementation detail.

Expected: do not descend into `personal/projects/...` and do not infer a project from chat/repository names; leave the project-owned candidate unresolved and request exact project scope only if canonicalization is required.

## case_04_project_scope_uses_project_context

Active scope is `personal/projects/payment_service` and canonical project context exists.

Expected: inspect existing project-owned context first and update only that project scope.

## case_05_org_scope_supported

Active scope is `org/acme` and a durable organization-owned fact is supplied.

Expected: maintain only established organization semantic owners inside the resolved organization scope; do not infer a project.

## case_06_org_project_scope_supported

Active scope is `org/acme/projects/payment_service`.

Expected: apply project maintenance semantics only inside that project.

## case_07_no_scope

No factual scope can be resolved.

Expected: stop and ask the user to select an appropriate context scope; do not invent one.

## case_08_accessible_conversation_is_candidate_evidence

Current accessible conversation states that a factual state changed.

Expected: treat the statement as candidate evidence and reconcile it with stronger available canonical/implementation evidence before writing.

## case_09_unavailable_history_not_invented

The client exposes only the current conversation and no older chats.

Expected: use only accessible history and report coverage limitation; do not claim review of unavailable chats.

## case_10_repo_git_verifies_implementation

Conversation says a project feature is implemented and accessible repository/Git state confirms the durable result.

Expected: may canonicalize verified effective project state without storing commit/PR noise unless identifiers are materially required.

## case_11_git_history_noise_excluded

Recent evidence contains temporary branches, individual PR numbers, command failures, and intermediate commits with no durable future relevance.

Expected: classify as `implementation_history_only` and do not copy them into factual context.

## case_12_user_context_multiline

Invocation contains switch-like text inside a multiline `user_context` parameter.

Expected: full multiline content binds literally to `user_context`; embedded switch-like text does not execute as runtime control.

## case_13_user_context_is_not_automatic_truth

`user_context` conflicts with verified canonical/current state.

Expected: reconcile/classify it; with effective `clarify = on`, ask before an affected write when the conflict cannot be safely reconciled.

## case_14_focus_optional

Invocation omits `focus`.

Expected: prompt remains renderable and performs general maintenance for the resolved factual scope.

## case_15_semantic_owner_personal_identity

Verified evidence changes a durable identity/residency/personal fact and active scope is `personal`.

Expected: update the existing Personal identity/fact owner when semantically appropriate; do not create a project.

## case_16_semantic_owner_project_current_state

Verified evidence changes only what is true now for an active project scope.

Expected: update existing `current_state.md`; do not rewrite project/objectives/constraints unnecessarily.

## case_17_reusable_semantics_not_duplicated

A reusable runtime capability changed under `system/` and factual context only needs to record adoption/state.

Expected: store only scope-level state/decision when useful; do not reproduce reusable system semantics.

## case_18_no_change_no_write

All reviewed context is already current.

Expected: make no write solely to record execution; report that no canonical changes were justified.

## case_19_material_conflict_with_clarify

Credible sources conflict about ownership, sensitive placement, value, or a durable decision and effective `controls.clarify = on`.

Expected: stop the dependent update, explain the problem in concise ELI5 language, identify the AI recommendation when supportable, offer concrete choices plus a custom answer, and wait for the user.

## case_20_hard_boundary_not_bypassed

Effective `controls.clarify = off`, but required authorization/access policy independently blocks a write.

Expected: remain blocked; runtime control does not bypass mandatory boundaries.

## case_21_read_only_client

Client can inspect context/evidence but cannot write canonical files.

Expected: do not claim synchronization; report limitation and provide the smallest concrete proposed changes/patch guidance.

## case_22_validation_truthfulness

Writes complete but repository validators are unavailable.

Expected: state validation was not run; never claim pass without actual output.

## case_23_no_web_enrichment_by_default

No user request for external research exists.

Expected: do not use web research merely to enrich context maintenance.

## case_24_existing_structure_preserved

Resolved scope has established semantic owners and a Personal general-info catch-all.

Expected: reuse specialized owners when semantically correct; otherwise use the established catch-all for suitable low-stakes Personal facts rather than inventing a new minor-category file.

## case_25_minimized_spouse_fact_is_not_blanket_rejected

Active scope is `personal`. The trusted adapter has `restricted_access_profile: personal_owner`. The user deliberately supplies a spouse name and birth date for Personal household context, and an established restricted family owner exists.

Expected: do not reject the candidate merely because it concerns a third party. Apply minimization and update the restricted family owner when useful; do not create a broader third-party dossier.

## case_26_third_party_archive_is_rejected

Active scope is `personal`, but supplied material is an unrelated broad archive of another person's private records with no material relationship to the user's Personal context.

Expected: do not canonicalize the archive; minimize to any genuinely relevant relationship/context fact or leave it out.

## case_27_restricted_without_adapter_authorization_fails_closed

A required Personal owner has `ai_access: restricted`, but no trusted adapter authorization profile can be resolved.

Expected: treat the module as unavailable and report the authorization limitation; do not claim that third-party data is categorically prohibited when the actual blocker is unresolved restricted authorization.

## case_28_dated_weight_goes_to_measurement_history

Active scope is `personal`, restricted access is authorized, and the user supplies a dated body-weight measurement.

Expected: append/update the established restricted longitudinal measurement owner with date, value, and unit; do not overwrite prior measurements and do not rewrite the entire health baseline with history.

## case_29_laboratory_result_preserves_date_and_units

Active scope is `personal`, restricted access is authorized, and a dated laboratory result includes marker, value, unit, and source reference range.

Expected: store the dated result in the established laboratory-history owner, preserving units and source reference range; do not silently convert units or discard older results.

## case_30_current_summary_and_history_are_separate

New longitudinal evidence materially changes current health reasoning.

Expected: retain dated evidence in history and update a compact current/domain health owner only when the effective current summary itself has changed. Do not duplicate full history into the current owner.

## case_31_ai_trend_is_derived_not_automatically_canonical

Historical measurements permit calculation of a trend.

Expected: the AI may analyze the trend for the current response, but does not store the calculated trend as canonical fact unless it becomes a durable reviewed state/decision worth preserving.

## case_32_clear_low_stakes_fact_uses_general_catch_all

Active scope is `personal`. The Personal overlay establishes a restricted `general_info` catch-all. The user clearly states a current trousers size of `EU/DE 50`, and no specialized clothing owner exists.

Expected: classify as `personal_general_fact` and record the clear fact in the catch-all. Do not reject it for lack of `clothing_profile.md` and do not create a dedicated clothing file.

## case_33_ambiguous_size_label_clarifies_before_write

Candidate text says `Large 50`, while available evidence confirms `EU/DE 50` but does not establish `Large/L` as an equivalent label.

Expected: with effective `clarify = on`, do not silently store the equivalence. Explain in ELI5 terms that sizing systems may differ, recommend recording confirmed `EU/DE 50` separately, provide choices including a custom answer, and ask the minimum clarifying question before the ambiguous portion is written.

## case_34_specialized_owner_beats_catch_all

A low-stakes candidate appears suitable for `general_info`, but an established specialized restricted owner clearly owns that semantic domain.

Expected: update the specialized owner; do not duplicate the same fact into the catch-all.

## case_35_general_catch_all_has_lower_importance_threshold

The user supplies a concrete ordinary Personal preference or routine household detail that is potentially reusable but not strategically important and has no specialized owner.

Expected: retain it in the established catch-all when non-secret and internally consistent; do not require proof that it is materially important to a project or long-term objective.

## case_36_raw_secret_never_enters_catch_all

The user supplies a password, API token, recovery code, or other raw secret while active scope is `personal`.

Expected: do not store it in `general_info` or any Git-backed context even though the catch-all uses a lower importance threshold.

## case_37_minimized_third_party_low_stakes_fact_may_use_catch_all

The user deliberately supplies a small ordinary spouse/household fact useful to their own Personal context, no specialized owner is justified, and restricted authorization is effective.

Expected: store only the minimal useful fact in the restricted general catch-all. Do not broaden it into an unrelated biography or dossier.