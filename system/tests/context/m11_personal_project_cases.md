# m11_personal_project_cases

These scenarios validate generic personal-project examples.

## case_01_personal_owner

`context/personal/projects/career_transition/` is selected.

Expected: owner remains Personal; project is a more-specific personal scope.

## case_02_project_identity

Project purpose belongs in `project.md`.

## case_03_objective_boundary

Desired interview outcome belongs in project `objectives.md`, not personal `goals.md` when it is project-specific.

## case_04_current_state_boundary

Current application count belongs in career project `current_state.md`, not stable personal identity.

## case_05_project_constraint

Maximum weekly application time specific to job search belongs in project `constraints.md`.

## case_06_cross_project_constraint

A constraint applying to all personal projects belongs at personal root, not copied into every project.

## case_07_no_skill_duplication

Durable Go skill exists in `context/personal/tech_profile.md`.

Expected: do not copy the same skill into career-transition project merely for convenience.

## case_08_learning_project_vs_tech_profile

Active study topic belongs in technical-learning `current_state.md`; acquired durable skill later moves/updates personal `tech_profile.md` as current truth.

## case_09_nested_project

`career_transition/interview_prep/` is valid without a synthetic `subprojects/` directory.

## case_10_nested_no_parent_copy

Interview-prep child does not repeat parent region/compensation/objectives.

Expected: parent scope chain supplies applicable inherited context.

## case_11_nested_specificity

Nested interview project defines a more-specific overridable fact.

Expected: nearest authoritative scope wins inside the personal project chain.

## case_12_example_not_registry

Fake career project appears under `examples/`.

Expected: no production `context_registry` entry.

## case_13_project_access

Copied project module lacks `ai_access`.

Expected: fail closed for that module.

## case_14_sensitive_project_fact

Job-search project contains a sensitive administrative fact.

Expected: classify to appropriate sensitive module/boundary rather than leaving it in ordinary project prose merely because the project needs it.

## case_15_sparse_project

Project has no architecture or stack semantics.

Expected: do not create empty `architecture.md` or `stack.md`.

## case_16_project_decision

A durable decision about target-role strategy needs rationale.

Expected: project `decisions/` may be used when rationale is independently useful.

## case_17_project_profile_separation

Career project prefers architecture-review profile for a task.

Expected: profile selection is runtime/adapter configuration, not copied factual project knowledge.

## case_18_personal_supplemental

Organization project is Primary and personal career project is explicit Supplemental.

Expected: target ownership rules prevent personal project targets from mutating primary-owned organization project targets.

## case_19_project_migration

Historical job-search chats are migrated.

Expected: use M10 inventory/classification and write only current durable project facts.

## case_20_fake_data_markers

Example project values remain clearly marked `EDIT_ME`.

Expected: generic core contains no real person's project data.

## exit_criterion

M11 passes when personal projects can be modeled as sparse hierarchical scopes without duplicating personal-root facts, parent project facts, profiles, or real user data in generic core.
