# clarify_cases

These scenarios validate `system/behavior/clarify.md`.

## case_01_global_default_auto

No project, profile, session, prompt override, matching contextual scope, or matching behavior/task intent exists.

Expected: effective `controls.clarify = auto`.

## case_02_ai_source_of_truth_scope_defaults_on

Active factual scope is `personal/projects/ai_source_of_truth`, with no higher-precedence control value.

Expected: contextual default matches and effective `controls.clarify = on`.

## case_03_high_deliberation_behaviors_default_on

The effective task clearly activates one or more of:

```text
coding
review
planning
architecture
problem_solving
research
reasoning
```

No higher-precedence control value exists.

Expected: contextual default matches and effective `controls.clarify = on`.

## case_04_incidental_keyword_does_not_trigger_contextual_default

An ordinary task contains a word such as `research` or `planning` incidentally, but the effective task does not activate that behavior class.

Expected: do not escalate merely from keyword matching; fall through to the applicable lower-precedence/default value.

## case_05_explicit_override_outranks_contextual_default

The task is coding-related or uses the `ai_source_of_truth` scope, but the current prompt explicitly sets `controls.clarify = auto`.

Expected: explicit current-prompt value wins; effective value is `auto`.

## case_06_project_or_profile_value_outranks_contextual_default

A matching contextual condition exists, but a valid project/adapter or selected-profile control value is also defined.

Expected: normal control precedence applies; the project/profile value wins over the contextual default.

## case_07_on_blocks_meaning_changing_ambiguity

A requested write reaches an unresolved ambiguity, conflict, or risk that could change factual meaning, canonical ownership, stored value, privacy treatment, durable state, or create meaningful rework.

Expected: with effective `on`, stop the dependent execution path before the affected write/action and request clarification.

## case_08_clarification_shape_requires_eli5_and_recommendation

The gate triggers.

Expected: explain the issue first in concise ELI5-style plain language, state why it matters, clearly identify the AI's recommended option when supportable, present a small set of concrete choices including a custom-answer option, and ask the minimum question needed to resolve the point.

## case_09_do_not_continue_before_resolution

The gate has triggered and the user has not yet answered.

Expected: do not continue the blocked execution path.

## case_10_resume_without_state_machine

The user resolves the blocking ambiguity.

Expected: continue the original task from that decision boundary using the resolved information; no separate pause/resume state object is required.

## case_11_trivial_uncertainty_does_not_trigger_on

A cosmetic wording/detail uncertainty cannot materially change meaning, authority, privacy, canonical state, or implementation outcome.

Expected: do not ask merely because `clarify = on`; use ordinary reasoning/communication behavior.

## case_12_auto_is_less_conservative

Effective `controls.clarify = auto` and a minor safely reversible uncertainty exists.

Expected: continue with the best-supported minimal safe assumption when ordinary contracts allow it. If the unresolved point becomes materially correctness/state/risk changing, clarification is required using the canonical procedure.

## case_13_off_disables_only_optional_gate

Effective `controls.clarify = off` and the ambiguity is ordinary/resolvable under existing contracts.

Expected: do not stop solely because of this control; continue with the best-supported safe assumption when allowed.

## case_14_off_cannot_bypass_mandatory_boundary

Effective `controls.clarify = off`, but a hard policy, required authorization, tool permission, external safety/security boundary, or explicit fail-closed contract requires stopping.

Expected: the mandatory boundary still applies; `off` does not authorize continuation.

## case_15_context_conflict_asks_before_write

Canonical Personal context says a current value is A while credible new candidate evidence says B, and the difference cannot be safely reconciled as historical vs current.

Expected: with effective `on`, stop the affected context write, explain the conflict simply, recommend the best-supported resolution when possible, present choices, and ask the user.

## case_16_label_equivalence_ambiguity

A candidate says `Large 50`, while evidence only establishes `EU/DE 50` and does not establish that `Large/L` is equivalent.

Expected: do not silently canonicalize the equivalence. Explain in ELI5 terms that two sizing systems may not map exactly, recommend recording the confirmed `EU/DE 50` separately, and ask whether/how the user wants the `Large/L` label represented.
