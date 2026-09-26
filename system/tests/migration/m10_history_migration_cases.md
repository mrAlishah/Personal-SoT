# m10_history_migration_cases

These scenarios validate inventory and migration behavior.

## case_01_transcript_is_not_canonical_context

A long chat contains several useful facts.

Expected: extract candidate claims; do not copy the transcript wholesale into canonical context.

## case_02_one_source_many_candidates

One chat contains identity, goal, and project-stack information.

Expected: separate candidates by owner and semantic home.

## case_03_source_with_no_durable_value

Small-talk history contains no durable useful context.

Expected: zero migration candidates.

## case_04_history_is_evidence

Historical chat conflicts with current canonical identity.

Expected: historical chat does not automatically overwrite current truth.

## case_05_unresolved_conflict

Two plausible historical sources conflict and current truth is not deterministically known.

Expected: `needs_confirmation`.

## case_06_current_state_not_history_log

Several chats describe previous blockers.

Expected: only currently active blocker belongs in `current_state.md`; old blockers are not copied forward by default.

## case_07_old_technology_as_experience

User used MySQL years ago but no longer uses it in current project.

Expected: may become durable personal technical experience, not current project stack.

## case_08_decision_rationale

Historical source explains why PostgreSQL was chosen and rationale remains useful.

Expected: decision candidate separate from current stack truth.

## case_09_raw_secret

History contains an API token.

Expected: classify `forbidden_secret`; do not migrate token value.

## case_10_sensitive_candidate

History contains AI-relevant residency expiry.

Expected: classify sensitive and route through restricted sensitive-data contract.

## case_11_duplicate_fact

Same durable fact appears in twenty chats.

Expected: one canonical fact, not twenty copies.

## case_12_parent_child_ownership

Organization and project chats mention the same project-specific stack fact.

Expected: narrowest authoritative project home; do not duplicate at organization level.

## case_13_old_prompt_classification

Legacy prompt says `always answer professionally`.

Expected: classify presentation/profile concern before migration; do not dump into personal facts.

## case_14_working_style_fact

Repeated history shows durable preference for small reviewable changes.

Expected: candidate for personal `working_style.md` when confirmed/current.

## case_15_policy_instruction

Historical organization instruction says production changes require security review.

Expected: classify as scoped policy, not behavior.

## case_16_adapter_configuration

Legacy `CLAUDE.md` contains default scope.

Expected: adapter configuration, not canonical factual context.

## case_17_ignore_obsolete_goal

History contains completed goal no longer active.

Expected: do not place it in current `goals.md`; preserve only if historical value is independently useful.

## case_18_inventory_minimality

Inventory record copies an entire conversation into `candidate`.

Expected: invalid style; candidate should be concise extracted meaning with source reference.

## case_19_migrate_by_domain

History spans years of chronological chats.

Expected: process coherent semantic/domain batches rather than copying in chronological order.

## case_20_access_required

Migrated canonical module has no `ai_access` metadata.

Expected: not AI-loadable; migration quality gate fails.

## case_21_no_fake_scope_registration

Fake migration example refers to `org/acme`.

Expected: no production context registry entry is created from the example.

## case_22_provenance_when_useful

Decision rationale needs traceability to a historical source.

Expected: retain concise useful provenance, not full transcript duplication.

## case_23_recency_not_authority

Newer historical chat conflicts with more authoritative confirmed canonical current truth.

Expected: current authority wins; recency alone is insufficient.

## case_24_personal_history_runs_outside_generic_core

Real user history inventory is performed.

Expected: working inventory and migrated real data live in personal/private workflow, not generic core.

## case_25_quality_gate

Candidate is correctly scoped but creates duplicate truth and contains unnecessary raw sensitive detail.

Expected: reject migration until deduplicated/minimized.

## exit_criterion

M10 passes when historical material can be converted into a compact reviewed candidate inventory and then into canonical context without transcript dumping, secret leakage, ownership drift, or silent conflict resolution.
