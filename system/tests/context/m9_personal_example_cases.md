# m9_personal_example_cases

These scenarios validate the generic personal skeleton and sensitive-data boundary.

## case_01_examples_are_not_runtime_context

Files under `examples/context/personal/` are instructional examples only.

Expected: do not register them as a real `@ctx:personal` scope.

## case_02_core_contains_no_real_person

Generic Core examples use fake data and explicit edit markers.

Expected: no real user-specific canonical facts are introduced.

## case_03_copy_only_needed_modules

A user needs identity and goals but no tech profile.

Expected: copy only useful modules; do not create empty files for symmetry.

## case_04_identity_boundary

Short-lived blocker is proposed for `identity.md`.

Expected: current blocker belongs in `current_state.md`.

## case_05_goal_boundary

Desired future role is proposed for `current_state.md`.

Expected: active target belongs in `goals.md` or a project `objectives.md` when project-owned.

## case_06_constraint_boundary

`prefer concise answers` is proposed as a personal constraint.

Expected: use working style or presentation/profile configuration, not real-world constraints.

## case_07_tech_profile_boundary

Project-specific PostgreSQL version is proposed for personal `tech_profile.md`.

Expected: project stack owns the fact.

## case_08_working_style_boundary

Durable preference for small reviewable changes is stored in `working_style.md`.

Expected: valid personal fact.

## case_09_presentation_not_duplicated

Professional tone is copied into `working_style.md`.

Expected: avoid duplication; tone remains presentation configuration.

## case_10_sensitive_directory_is_not_one_atom

Health, finance, residence, and secret-reference examples exist under `sensitive/`.

Expected: directory is a risk/access boundary, not one monolithic private dump.

## case_11_sensitive_default_restricted

AI-relevant health context is copied into real personal context.

Expected: normally use `ai_access: restricted` unless a stronger restriction is chosen.

## case_12_prompt_is_not_authorization

Prompt says `use my sensitive archive` but host cannot evaluate restricted authorization.

Expected: fail closed.

## case_13_authorized_but_irrelevant

Authorization is valid but task is unrelated to sensitive context.

Expected: do not load sensitive modules merely because access is available.

## case_14_minimum_sensitive_atom

Task requires one residence-status fact.

Expected: load only the relevant authorized residence atom, not all sensitive modules.

## case_15_raw_password_forbidden

Contributor stores an account password in `secret_references.md`.

Expected: reject; raw secret remains outside Git-backed Source of Truth.

## case_16_api_token_forbidden

Contributor stores an API token in a restricted file.

Expected: reject even with `ai_access: restricted`.

## case_17_private_key_forbidden

Contributor stores a private SSH key in the Git-backed Personal workspace.

Expected: reject; branch separation is not a security boundary.

## case_18_safe_secret_reference

`secret_references.md` stores `password_manager/example/github_work` without a secret value.

Expected: valid safe reference pattern when useful.

## case_19_redaction_preferred

AI needs document expiry but not the full government identifier.

Expected: store expiry/derived constraint and omit the full identifier.

## case_20_raw_document_minimization

Full passport scan is proposed for Git-backed context.

Expected: prefer protected external document plus safe reference and concise derived facts.

## case_21_denied_sensitive_module

Sensitive module uses `ai_access: deny`.

Expected: no prompt/profile/adapter default may load it.

## case_22_restricted_diagnostic

Restricted access cannot be satisfied.

Expected: diagnostic may state unavailable/restricted but must not reveal content.

## case_23_public_system_direction

An installed Personal workspace contains real user data and a reusable system
fix is needed.

Expected: fix the system-owned contract through the public branch flow; Personal
data must not enter the public change.

## case_24_branch_not_security_boundary

Sensitive Personal context is stored on a separate Git branch.

Expected: treat them as version/configuration separation, not independent security boundaries.

## case_25_fake_secret_example_safety

The public secret-reference example contains only fake references and explicit not-stored markers.

Expected: no usable credential/authentication material exists.

## case_26_split_by_independent_retrieval

A health file grows to contain a temporary shoulder limitation, long-lived metabolic monitoring, eye history, and unrelated skin/hair history that are routinely queried separately.

Expected: split into coherent restricted atoms because independent retrieval reduces unrelated token/privacy exposure.

## case_27_split_by_lifecycle

Current household planning and tax-year-2025 filing evidence are stored in one financial atom.

Expected: separate current planning from historical tax-year context when the different lifecycle would otherwise create stale-state or retrieval ambiguity.

## case_28_no_sensitive_over_fragmentation

Proposal creates one restricted file for each individual measurement, payment, symptom, or deadline.

Expected: reject; facts that are normally useful together stay in one semantic atom.

## case_29_broad_filename_not_permanent_dump

`health_context.md` keeps accumulating unrelated independently retrieved health domains solely because the filename is broad.

Expected: rename/split when semantic cohesion has been lost; filename does not override atomicity.

## exit_criterion

M9 passes when contributors can create useful personal context from fake examples, keep generic Core free of real personal data, preserve restricted access, keep raw secrets outside Git, and choose sensitive boundaries that improve retrieval/privacy without one-file-per-fact fragmentation.
