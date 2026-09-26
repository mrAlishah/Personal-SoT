---
prompt_status: active
prompt_tags:
  - ai
  - governance
  - architecture
  - charter
  - source_of_truth
prompt_profiles: []
prompt_formats: []
prompt_tone: professional
prompt_depth: deep
required_params: []
optional_params:
  - focus
  - user_context
owned_assets: []
---
Review, discuss, and when explicitly approved improve `system/governance/project_charter.md`, the canonical purpose/principles/priority contract for the AI Context Source of Truth.

Optional focus:

{{focus}}

User proposals, concerns, or candidate principles:

{{user_context}}

## objective

Use this prompt as the dedicated design-review surface for questions such as:

```text
Is the project definition still correct?
Are the priorities ordered correctly?
Is a principle missing, redundant, ambiguous, or too broad?
Does an existing rule create harmful tradeoffs?
Should ownership/cohesion, retrieval/context efficiency, privacy, correctness, maintainability, convenience, or another concern be weighted differently?
Does current system evolution reveal a gap in the charter?
Should a principle be clarified, split, merged, renamed, strengthened, or removed?
```

The goal is not to defend the current charter by default. Treat it as canonical current governance that may itself be improved through explicit governance change.

## evidence_basis

Start from the actual current `system/governance/project_charter.md` and inspect only the repository evidence needed to evaluate the discussion.

When relevant, compare the charter against:

```text
actual runtime/base instructions
routing/access/context contracts
retrieval behavior
prompt/profile/adapter architecture
validation/tests
governance branch flow
recent durable implementation patterns
known recurring conflicts or inefficiencies
```

Distinguish clearly between:

```text
what the charter currently says
what the implementation currently does
what the user proposes
what the AI recommends
```

Do not rewrite the charter merely to make existing implementation look compliant. Implementation may be wrong; the charter may be incomplete; or both may need change.

## charter_change_classes

Classify proposed changes as one or more of:

```text
clarification_without_semantic_change
remove_duplication_or_ambiguity
new_principle
principle_scope_change
priority_order_change
conflict_resolution_between_principles
non_goal_change
decision_test_change
governance_process_change
terminology_or_structure_cleanup
no_change_recommended
```

For each material proposal, explain:

```text
current rule
problem/gap
evidence or motivating example
proposed wording/semantic change
benefits
costs/tradeoffs
impact on higher/lower priorities
expected implementation consequences
migration/compatibility concerns
AI recommendation
```

## priority_reasoning

Always read and use the current `priority_order` from `system/governance/project_charter.md` as the baseline. This prompt must not maintain a second hard-coded copy of the current priority sequence.

When evaluating that order, pay particular attention to interactions among mandatory boundaries, correctness/data integrity, semantic ownership/cohesion/non-duplication, structural maintainability, retrieval/context efficiency including measured token/context cost, and implementation convenience.

Do not optimize ownership into fragmentation, efficiency into hidden coupling, maintainability into abstraction for its own sake, or token cost into loss of correctness/ownership/validation.

If proposing a priority reorder, state concrete examples where the new order would choose a different design than the current order.

## ambiguity_and_conflict

If the user's proposed principle/priority is ambiguous, conflicts with another charter principle, or has multiple plausible interpretations with different architectural consequences, do not silently choose one.

Use `controls.clarify_risk`:

1. explain the ambiguity/conflict in concise ELI5 language;
2. explain why it matters;
3. give the AI's recommended interpretation when supportable;
4. provide concrete options plus a custom option;
5. ask the minimum question needed to resolve it.

## approval_boundary

Discussion, critique, comparison, and proposed wording do not require approval.

Any canonical write to `system/governance/project_charter.md` requires explicit user approval after the intended semantic direction is sufficiently established to avoid an unresolved governance choice.

Approval may come from a direct charter decision or from an explicitly authorized stabilization/revision plan whose agreed target priority/principle model already determines the change. Do not treat a generic request to "improve things" as approval for an unspecified governance change.

After approval, apply the smallest coherent charter patch. Do not bundle unrelated charter changes simply because the file is already being edited.

If an approved charter change implies changes elsewhere in the SoT, separate them into:

```text
required_follow_up_for_consistency
recommended_follow_up
optional_future_improvement
```

Do not automatically perform material follow-up implementation unless the user also authorized it or it is a strictly mechanical consistency update with no semantic choice.

## governance_and_execution

Changes to the charter are reusable architecture/governance changes and must follow Core-first governance.

When write capability is available and approval has been received:

1. modify the Core charter on an appropriate feature/revision branch;
2. update tests/references only where needed to keep the approved governance semantics coherent;
3. validate with the strongest relevant available checks;
4. promote Core -> develop -> intended Personal staging/canonical branch only when authorized by the task/governance;
5. never claim deployment/sync or validator success without evidence.

If write capability is unavailable, provide the exact proposed patch and affected paths.

## discussion_mode

When the user is exploring rather than asking for an immediate change, prioritize clear design discussion over implementation.

Use examples and tradeoffs. Challenge proposals when they conflict with the project's stated purpose or create hidden cost, but do not treat the existing charter as immutable.

Prefer one strong recommendation over many weak alternatives when evidence supports it.

## report

When no write is requested/approved, return a concise design-review result such as:

```text
charter_area_reviewed
current_rule
identified_gap_or_conflict
AI_recommendation
options_or_open_question
proposed_wording_if_useful
```

After an approved write, report:

```text
approved_change
updated_files
semantic_effect
required_follow_up
validation
branch_or_promotion_state
```

Distinguish discussion, proposal, approval, implementation, merge, deployment, sync, and validation.