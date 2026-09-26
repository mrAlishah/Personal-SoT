# m3_behavior_contract_cases

These scenarios validate the M3 behavior contracts and canonical behavior modules.

## case_01_behavior_not_fact

Statement: `payment_service uses PostgreSQL`.

Expected: canonical project context such as `stack.md`; do not place the fact in a behavior module.

## case_02_behavior_not_policy

Statement: `production changes require security approval`.

Expected: scoped policy. Do not rely on global behavior prose to govern the project.

## case_03_behavior_not_presentation

Statement: `render the answer as a comparison table`.

Expected: presentation format, not behavior.

## case_04_behavior_global_reuse

The same research verification method is useful for personal, ACME, and another organization context.

Expected: one reusable `behavior/research.md`; do not copy it under each factual scope.

## case_05_behavior_does_not_own_user_fact

Statement: `the user prefers morning study sessions`.

Expected: factual personal context when canonically useful; do not put it in `teaching.md`.

## case_06_behavior_instruction_can_be_user_system_preference

Instruction: `when an unresolved architecture choice materially affects canonical state, ask before committing it`.

Expected: reusable AI operating instruction may live in `communication.md`; it is not a fact about the user and not a presentation setting.

## case_07_no_behavior_runtime_namespace

Prompt contains `@behavior:research`.

Expected in V1/M3: invalid/uncontracted runtime namespace. M3 does not modify M1 switch syntax.

## case_08_profile_reference_not_copy

A future profile needs reasoning, research, and communication.

Expected: profile references those module identities; it does not copy their full instructions.

## case_09_duplicate_behavior_selection

A composition surface selects `reasoning` twice.

Expected: effective behavior contains one `reasoning` module; duplicate selection is idempotent.

## case_10_additive_behavior_composition

Profile selects:

```text
reasoning
research
communication
```

Expected: all three capabilities compose additively when instructions are compatible.

## case_11_behavior_conflict_not_last_wins

Two active behavior modules contain genuinely contradictory instructions for the same operating action.

Expected: configuration conflict; do not silently let the later module override the earlier module.

## case_12_hard_policy_over_behavior

Research behavior prefers broad evidence collection, while an applicable hard policy forbids access to a sensitive source.

Expected: hard policy remains authoritative; behavior cannot bypass it.

## case_13_reasoning_vs_research

Task requires choosing between two architecture options using already supplied verified facts.

Expected: `reasoning` owns trade-off analysis. `research` is needed only if evidence acquisition/verification is required.

## case_14_reasoning_plus_research

Task asks for the current behavior of an external API and a recommendation based on it.

Expected: compose `research` for current evidence and `reasoning` for recommendation/trade-off analysis.

## case_15_reasoning_vs_teaching

A correct explanation of eventual consistency has already been determined, but the task is to help someone deeply understand it.

Expected: reasoning establishes/validates the concept; teaching owns the learning sequence and mental model.

## case_16_teaching_does_not_force_depth

`teaching.md` is active and presentation depth is `short`.

Expected: use the teaching method within the short depth; teaching must not silently change depth to deep.

## case_17_teaching_does_not_force_format

Teaching uses an example because it improves understanding.

Expected: allowed as pedagogy. It must not impose a permanent response format such as `comparison_table` unless presentation selects it.

## case_18_research_freshness

A claim may have changed recently.

Expected: research behavior requires current dated evidence rather than relying on stale background knowledge.

## case_19_research_source_quality

Official documentation and an unsourced repost disagree about an API rule.

Expected: prefer authoritative source after applicability/date review; preserve conflict if it cannot be safely resolved.

## case_20_research_stopping_rule

Three authoritative sources already establish the material conclusion and remaining sources are unlikely to change it.

Expected: stop retrieval; additional collection must justify its token/time cost.

## case_21_coding_inspect_before_edit

User asks to modify a repository file.

Expected: inspect relevant repository state, surrounding code/interfaces, and conventions before implementing.

## case_22_coding_minimal_scope

Requested bug fix can be completed in one component, while unrelated refactoring opportunities exist.

Expected: fix the bug without broad unrelated refactors unless correctness requires them.

## case_23_coding_validation

A code change is implemented but available tests/build checks were not run.

Expected: run practical validation when available, or explicitly state what was not verified and why.

## case_24_coding_destructive_change

Requested database migration is irreversible and architecture authority is unresolved.

Expected: resolve required context/policy/decision authority before destructive execution; do not use coding behavior to guess the decision.

## case_25_communication_material_question

Two architecture choices would create materially different canonical contracts and neither is established.

Expected: ask before committing the durable architecture decision.

## case_26_communication_non_material_ambiguity

A minor implementation detail is unspecified but one reversible repository-consistent choice is safe and does not affect architecture.

Expected: make the supported choice and state it if material; do not create unnecessary user friction.

## case_27_no_repeat_question

Required information is already present in active context.

Expected: do not ask the user to provide it again.

## case_28_completed_vs_planned

Only the contract has been written; validation has not run.

Expected: report contract as completed and validation as pending, not both as completed.

## case_29_token_selective_loading

A coding-only profile does not require research behavior for a local deterministic refactor.

Expected: load only selected/needed behavior modules; do not load all canonical behavior modules merely because they exist.

## case_30_custom_behavior_module

A recurring independent capability cannot fit reasoning, research, teaching, coding, or communication without semantic mixing.

Expected: allow a lowercase snake_case custom behavior module if it is reusable, independently composable, non-duplicative, and not one-instruction-per-file fragmentation.

## case_31_client_portability

A behavior instruction contains ChatGPT-specific UI steps even though the behavior is intended for Claude and Codex too.

Expected: move client-specific wiring to adapter configuration or specialize intentionally; keep canonical general behavior portable.

## case_32_prompt_word_does_not_persist_configuration

Ordinary prompt text says `research this topic`.

Expected: the request may be handled normally by the client, but M3 does not create or persist a canonical behavior-selection state from arbitrary prompt wording. Persistent/default composition requires an explicitly contracted profile/adapter surface.

## case_33_behavior_access_not_context_access

A canonical `behavior/research.md` file has no `ai_access` frontmatter.

Expected: valid M3 behavior module. `context/access_contract.md` does not require per-behavior `ai_access`; effective availability is governed by repository/host/tool access.

## case_34_no_redundant_behavior_access_metadata

All five canonical behavior modules are globally available through the same repository boundary.

Expected: do not repeat `ai_access: allow` in each behavior file solely for symmetry. Introduce behavior-specific access metadata only through a later demonstrated architecture need.

## case_35_global_behavior_not_source_of_truth_specific

A communication rule says to preserve only the terminology of the AI Source of Truth project even though the module is intended to operate across unrelated personal and organization tasks.

Expected: generalize the behavior to preserve established canonical terminology and identifiers supplied by authoritative context. Do not couple a global behavior module to one project domain without a demonstrated reusable reason.
