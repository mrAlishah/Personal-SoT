# m13_decision_example_cases

These scenarios validate decision/ADR examples against `context/decision_contract.md`.

## case_01_accepted_decision_is_rationale

Accepted Kafka decision exists and project stack says `messaging: kafka`.

Expected: stack is current truth; decision explains why.

## case_02_accepted_change_updates_current_truth

An accepted decision changes database from MySQL to PostgreSQL.

Expected: update the decision artifact and current `stack.md`; do not leave current truth only in the decision.

## case_03_superseded_not_current

RabbitMQ decision is marked `superseded`.

Expected: it never overrides current Kafka stack.

## case_04_supersession_reference

Superseded RabbitMQ decision identifies the newer Kafka decision.

Expected: valid concise historical chain; no need to copy the full newer decision.

## case_05_proposed_not_authority

NATS proposal is newer than accepted Kafka decision.

Expected: Kafka remains current truth.

## case_06_deprecated_not_guidance

Custom tracing-agent decision is deprecated while stack uses OpenTelemetry.

Expected: deprecated artifact is historical evidence only.

## case_07_current_question_skips_decision

Question: `What messaging system does payment_platform use?`

Expected: `stack.md` is sufficient; decision artifacts are not loaded by default.

## case_08_why_question_loads_decision

Question: `Why does payment_platform use Kafka?`

Expected: load current stack plus relevant accepted Kafka decision.

## case_09_historical_question

Question asks what messaging preceded Kafka.

Expected: relevant superseded RabbitMQ decision may be loaded.

## case_10_token_budget

Context budget is tight for a current architecture question.

Expected: prune unnecessary decision history before current stack/architecture or mandatory policies.

## case_11_access_applies

Decision has missing or denied `ai_access`.

Expected: it does not become loadable merely because current stack references the same topic.

## case_12_sensitive_decision

A personal decision contains AI-relevant sensitive rationale.

Expected: use appropriate restricted access/sensitive boundary rather than ordinary allow by convenience.

## case_13_path_is_identity

Decision file path is stable and descriptive.

Expected: no duplicate `decision_id` metadata required in V1.

## case_14_status_required

Decision artifact lacks `decision_status`.

Expected: lifecycle unresolved; do not guess accepted/proposed state.

## case_15_unknown_status

`decision_status: active` appears.

Expected: unresolved lifecycle state; do not normalize to accepted.

## case_16_scope_ownership

Payment-platform decision is stored under the payment-platform project.

Expected: do not move it to organization scope merely because several teams know about it.

## case_17_personal_project_decision

Career-transition strategy rationale belongs under personal project `decisions/`.

Expected: current active targets remain in project `objectives.md`.

## case_18_decision_not_history_log

Every small implementation choice is proposed as an ADR.

Expected: create decision artifacts only when rationale/consequences remain independently useful.

## case_19_no_empty_sections

Decision has no useful alternatives/evidence.

Expected: omit those sections rather than preserving template symmetry.

## case_20_policy_not_decision

`Production changes require peer review` is proposed as a decision.

Expected: scoped policy owns the mandatory rule.

## case_21_architecture_not_decision

Current component topology is stored only in a decision artifact.

Expected: current `architecture.md` must own the structural truth.

## case_22_migration_rationale

Historical chat explains a durable architecture choice.

Expected: M10 may migrate it to a decision artifact when independently useful, while updating current truth separately if needed.

## case_23_fake_examples_not_runtime_scopes

Decision examples live under `examples/`.

Expected: no production registry entries are created from them.

## case_24_proposal_conflicts_with_policy

Proposed decision would weaken an applicable hard policy.

Expected: proposal cannot override the hard policy.

## case_25_superseded_retention

Old decision remains valuable for historical incident/design analysis.

Expected: keep it as superseded evidence rather than deleting merely because current truth changed.

## exit_criterion

M13 passes when decision artifacts reliably preserve durable rationale/lifecycle without becoming a parallel source of current architecture, stack, state, goals, or policy authority.
