# v1_catalog_boundary_cases

These scenarios validate canonical context-module ownership boundaries after the V1 hardening review.

## case_01_identity_vs_tech_profile

A personal `identity.md` contains a full list of frameworks, databases, messaging systems, and measured performance achievements while `tech_profile.md` also owns durable technical capability.

Expected: keep only high-level professional identity in `identity.md`; detailed capability/evidence belongs to `tech_profile.md`.

## case_02_identity_not_resume

Employment chronology and role-specific implementation evidence are proposed for `identity.md`.

Expected: use an employment-history artifact when independently useful; identity remains stable/high-level.

## case_03_root_current_state_cross_project_only

Personal root `current_state.md` repeats job-search status, German-learning state, and technical-learning focus already owned by active projects.

Expected: remove the duplicate root dashboard. Root `current_state.md` may be absent when no independently useful cross-project state exists.

## case_04_root_current_state_valid

A temporary cross-domain personal constraint/state affects job search, learning, finance planning, and scheduling and is not owned more precisely elsewhere.

Expected: a concise root `current_state.md` may be valid.

## case_05_root_goals_vs_project_objectives

Root `goals.md` repeats the exact next-role target from `projects/job_search/objectives.md`.

Expected: near-term job-search outcome stays in the project; root goals keep cross-project/long-term outcomes only.

## case_06_long_term_goal_at_root

A three-year career/financial-independence trajectory spans multiple projects.

Expected: valid root goal when not duplicated verbatim in child objectives.

## case_07_constraints_vs_working_style

`constraints.md` says "prefer coherent commits" or "avoid repeated prompting".

Expected: those are working/execution preferences; move to `working_style.md`.

## case_08_constraints_vs_environment

`constraints.md` stores Intel macOS, Homebrew, VS Code, and local tool facts.

Expected: use an independently useful environment atom; do not mix machine state into general constraints.

## case_09_project_constraint

German-language requirements constrain only the current job search.

Expected: store in job-search `constraints.md`, not Personal root merely because the person also studies German.

## case_10_tech_profile_vs_learning_state

`tech_profile.md` stores current goals such as "learn deeper Go concurrency this month".

Expected: learning target/current focus belongs to technical-learning objectives/current_state; tech profile stores durable capability.

## case_11_tech_profile_vs_environment

`tech_profile.md` lists the current workstation, editor installation, and dock/display configuration.

Expected: environment atom owns those facts when independently useful.

## case_12_project_current_state_parent_composition

Technical-learning `current_state.md` copies the entire parent technical stack to explain the learner's foundation.

Expected: keep only project-local current focus; compose parent `tech_profile.md` when relevant.

## case_13_job_search_state_parent_evidence

Job-search state copies measured backend performance achievements already canonical in the parent tech/employment atoms.

Expected: retrieve parent evidence when needed for CV/interview work; do not copy it into project state.

## case_14_language_state_vs_objectives

Language current state contains both current A2/B1 level and target B1/Executive-English outcomes already in objectives.

Expected: current level/tool use stays in current_state; target outcomes stay in objectives.

## case_15_language_state_vs_presentation

Language current state instructs the AI to use the `g.german.learning` profile or German+English+Persian rendering.

Expected: factual context does not own presentation/profile configuration.

## case_16_sensitive_broad_bucket

A broad restricted health file accumulates shoulder history, lipid monitoring, eye symptoms, hair treatment, and skin-care history that are routinely queried separately.

Expected: split into coherent restricted atoms when independent retrieval materially reduces unrelated token/privacy exposure.

## case_17_sensitive_lifecycle_split

Current household financial planning and tax-year-2025 filing evidence are in one restricted atom.

Expected: separate them because currentness/lifecycle and retrieval purpose differ materially.

## case_18_sensitive_administration_split

Residence-status workflows and health-insurance service/app issues are stored in one generic administrative dump but are independently queried.

Expected: use separate restricted atoms.

## case_19_sensitive_no_overfragmentation

Proposal creates one restricted file for each individual lab value, symptom, bill, or deadline.

Expected: reject; facts normally useful together remain one semantic atom.

## case_20_custom_environment_module

Machine/tool configuration is repeatedly useful independently and does not fit identity, tech capability, or project stack cleanly.

Expected: a custom environment module is valid when it is cohesive and non-duplicative.

## case_21_custom_employment_history

Résumé-level employment history is repeatedly useful independently of current technical capability.

Expected: a cohesive employment-history artifact is valid; do not copy proprietary internal ticket details into it.

## case_22_missing_module_is_valid

A scope has no independently useful canonical knowledge for `current_state.md`.

Expected: omit the module; the catalog is sparse, not a checklist.

## case_23_parent_child_no_copy

Nested project wants access to organization terminology or parent architecture.

Expected: scope composition supplies upstream context; child stores only nested-owned additions/overrides.

## case_24_atomicity_over_filename

A broad canonical or custom filename has gradually accumulated unrelated content.

Expected: semantic responsibility governs placement; rename/split when cohesion is lost rather than preserving a monolith because the filename already exists.

## acceptance

The catalog passes when contributors can identify one authoritative semantic home, distinguish root from project ownership, use parent composition instead of copies, and improve retrieval/token/privacy efficiency without one-file-per-fact fragmentation.
