# m12_organization_project_cases

These scenarios validate fake organization/project examples.

## case_01_org_root

Organization-wide identity/business context belongs at `context/organizations/<org>/`.

## case_02_project_under_owner

`projects/payment_platform/` remains owned by the organization.

## case_03_no_personal_implicit_load

Organization project is selected.

Expected: personal context is not loaded unless explicitly supplemental.

## case_04_cross_org_isolation

Organization A is selected.

Expected: Organization B does not implicitly compose.

## case_05_business_vs_architecture

Merchant/business concepts belong in business context; service topology belongs in project architecture.

## case_06_org_constraint_not_project_copy

EU data-region constraint is organization-wide.

Expected: project consumes it through scope chain; do not copy into project constraints.

## case_07_org_principle_vs_policy

`design for observability` is preferred guidance.

Expected: engineering principle unless made a mandatory governed rule.

## case_08_hard_policy_accumulates

Organization `credential_exposure` + project `payment_idempotency`.

Expected: both active.

## case_09_soft_policy_specificity

Organization prefers REST; project prefers gRPC for same `service_api_protocol` rule id.

Expected: project soft preference within project scope.

## case_10_current_state_vs_architecture

Migration is 60% complete.

Expected: current_state, not architecture.

## case_11_target_architecture_not_current

Settlement extraction is planned/in progress.

Expected: current architecture does not silently claim extracted service is already production truth.

## case_12_stack_boundary

Go/PostgreSQL/Kafka belong in stack, not architecture rationale.

## case_13_project_constraint

Payment p95 latency limit belongs in project constraints.

## case_14_nested_project

`payment_platform/settlement/` is a valid direct nested project path.

## case_15_nested_no_parent_copy

Settlement architecture contains only settlement-owned structure.

Expected: parent API/cache/org policies are not copied.

## case_16_example_not_registry

Fictional Northstar Labs examples exist.

Expected: production context registry remains unchanged.

## case_17_ai_access_explicit

Copied canonical org/project module requires explicit `ai_access`.

## case_18_supplemental_personal_gap_fill

Personal is explicit supplemental and has a target missing from organization project.

Expected: may fill relevant missing target, but cannot mutate project-owned target.

## case_19_org_a_vs_org_b_supplemental

Organization B is explicit supplemental.

Expected: target ownership prevents it from changing Organization A primary-owned targets.

## case_20_policy_cannot_be_pruned

Tight token budget.

Expected: applicable hard policies remain mandatory.

## case_21_project_decision_rationale

Why a project technology was selected becomes a decision artifact when independently useful; current stack remains current truth.

## case_22_fake_data_only

Generic core uses fictional organization/project data and `EDIT_ME` markers.

Expected: no real employer/client context in core.

## exit_criterion

M12 passes when an organization and nested project can be modeled with clean ownership, policy accumulation, specificity, isolation, and no copied parent/personal truth or real organization data in generic core.
