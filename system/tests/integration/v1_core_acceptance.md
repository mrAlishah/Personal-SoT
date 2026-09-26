# v1_core_acceptance

These scenarios validate cross-layer V1 Core invariants after M1–M16 consolidation and the V1 hardening review.

## case_01_repository_mapping

Repository root maps directly to `vault/99_system/ai/`.

Expected: repository does not recreate `99_system/ai/` inside itself.

## case_02_generic_core

Search generic Core canonical context.

Expected: no real user/company-specific canonical data; only contracts and fake examples.

## case_03_example_isolation

A fake personal/organization example exists.

Expected: example is not a registered runtime scope and is not canonical truth.

## case_04_prompt_scope_precedence

Valid explicit `@ctx` conflicts with adapter default scope.

Expected: explicit scope wins; valid unresolved explicit primary fails closed.

## case_05_primary_target_ownership

Primary owns target T and Supplemental contributes another value to T.

Expected: Supplemental cannot mutate Primary-owned target.

## case_06_hard_policy_exception

Primary and applicable Supplemental each contain compatible hard policies.

Expected: hard policies accumulate despite ordinary target ownership.

## case_07_access_before_relevance

A semantically relevant module is `ai_access: deny`.

Expected: it never enters effective context.

## case_08_restricted_without_authorization

Restricted sensitive module is requested but host cannot deterministically prove authorization.

Expected: fail closed.

## case_09_prompt_not_restricted_authorization

Prompt explicitly asks to use restricted context but external authorization is unavailable.

Expected: prompt text does not grant access.

## case_10_raw_secret_exclusion

Candidate content contains API token/private key/recovery code.

Expected: never write raw secret to Git-backed canonical context or generated derivative.

## case_11_semantic_atomicity

A proposed module mixes goals, architecture, health, and project state solely to reduce file count.

Expected: split by independently useful semantic responsibility.

## case_12_no_over_fragmentation

Proposal creates one file per individual fact.

Expected: reject; atomicity is semantic, not line-level.

## case_13_current_vs_decision

Accepted decision says Kafka was chosen; current `stack.md` says Kafka.

Expected: stack answers current truth; decision loads for rationale/history only when needed.

## case_14_proposed_decision

Newer proposed NATS decision exists while current stack remains Kafka.

Expected: proposal does not override current truth.

## case_15_behavior_presentation_boundary

`eli5` format is selected without teaching behavior.

Expected: accessible rendering does not implicitly activate pedagogical sequencing.

## case_16_language_model

German learning profile selects German primary with English/Persian supporting.

Expected: supporting languages assist where relevant; no automatic full-response triplication.

## case_17_profile_manifest

Profile contains duplicated factual project architecture.

Expected: invalid; profile is a composition manifest only.

## case_18_registry_index

Registry points to canonical target.

Expected: registry stores identity/discovery only, not copied target facts/access rules.

## case_19_history_migration

Old chat contains durable fact plus contradictory newer candidate.

Expected: history is evidence; classify/deduplicate and require confirmation when current truth remains unresolved.

## case_20_adapter_thinness

`AGENTS.md`, `CLAUDE.md`, or ChatGPT Project Instructions copy large canonical context blocks.

Expected: architecture violation; keep bootstrap/default pointers only.

## case_21_host_capability

Adapter names canonical source but active client cannot access it.

Expected: report limitation; do not reconstruct canonical truth from memory.

## case_22_retrieval_not_authority

Full-text result conflicts with more-authoritative canonical module.

Expected: canonical authority wins regardless of search relevance score.

## case_23_progressive_retrieval

Known scope/module directly answers task.

Expected: do not scan whole vault or load decision/history unnecessarily.

## case_24_generated_artifact

Generated index conflicts with canonical source.

Expected: canonical source wins; regenerate/discard derivative.

## case_25_automation_ambiguous_write

Automation cannot deterministically classify semantic home.

Expected: propose/defer rather than silently mutating canonical truth.

## case_26_branch_direction

Personal branch contains real user context and a reusable system fix is discovered.

Expected: fix the system-owned contract through the public branch flow; never copy Personal context into public system contracts.

## case_27_private_branch_security

Sensitive personal context is stored on a private Git branch.

Expected: branch is logical/versioning isolation, not a security boundary; raw secrets remain forbidden.

## case_28_token_budget

Optional historical context exceeds budget while hard policy/current authoritative facts fit.

Expected: prune optional history first; never prune mandatory hard policy or authoritative required fact for efficiency.

## case_29_unknown_switch

Prompt contains unknown/case-mismatched/fuzzy switch value.

Expected: no normalization/guessing.

## case_30_portability

New AI client is introduced.

Expected: add thin adapter/capability wiring without rewriting canonical context/behavior/presentation layers.

## case_31_plain_markdown_viability

No MCP, embedding store, vector DB, or custom resolver service is available.

Expected: V1 remains understandable and usable with plain Markdown + deterministic contracts.

## case_32_identity_tech_boundary

Personal identity contains detailed technology/capability facts already owned by tech profile.

Expected: high-level identity remains in `identity.md`; detailed technical capability belongs to `tech_profile.md`.

## case_33_root_project_boundary

Root current-state/goals files copy child project state/objectives to provide a dashboard.

Expected: reject duplication; root stores only independently useful cross-project facts and may omit a module entirely when no such atom exists.

## case_34_parent_composition

Project current state needs parent capability/identity context.

Expected: compose relevant parent atom; do not copy parent facts into project state.

## case_35_sensitive_retrieval_split

One restricted file contains several independently queried sensitive domains.

Expected: split when independent retrieval/lifecycle materially reduces token/privacy exposure.

## case_36_sensitive_no_overfragmentation

Proposal creates one restricted file per symptom, tax field, or deadline.

Expected: reject; keep facts that are normally useful together in one semantic atom.

## case_37_sensitive_current_vs_history

Current household finance and tax-year-2025 evidence are stored together.

Expected: separate when lifecycle/currentness would otherwise create stale-state ambiguity or unnecessary retrieval.

## case_38_static_validator_scope

Structural validator reports all checks passed.

Expected: this supports naming/reference/schema confidence but does not prove factual currentness, semantic atomicity, or absence of duplication; semantic review remains required.

## case_39_static_validator_failure

Validator reports invalid `ai_access`, missing registry/profile target, invalid decision status, naming violation, or a guarded raw-secret assignment.

Expected: treat as structural release blocker until reviewed/fixed.

## case_40_quality_order

A more token-efficient composition would omit required authority/policy/current context.

Expected: choose the higher-quality/correct composition. Token efficiency remains subordinate to correctness.

## acceptance_result

V1 Core is accepted architecturally when these invariants are mutually satisfiable without contradictory contracts or duplicate canonical authority.

Full release freeze additionally requires local execution of `system/validation/validate_v1.py` on the target Core/Personal checkout because the GitHub connector itself does not execute the repository locally.
