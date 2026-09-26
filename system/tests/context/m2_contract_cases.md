# m2_atomic_module_contract_cases

These scenarios validate the M2 context contracts.

## case_01_semantic_atom_not_monolith

Given one project file contains architecture, current sprint state, terminology, and personal learning preferences.

Expected: split by semantic responsibility; unrelated domains must not remain bundled merely to reduce file count.

## case_02_semantic_atom_not_one_fact_per_file

Given `database`, `runtime`, and `messaging` are normally useful together as project technology facts.

Expected: keep them in `stack.md`; do not create one file per fact without an independent retrieval reason.

## case_03_path_derived_metadata_not_duplicated

Given:

```text
workspace/context/organizations/acme/projects/payment_service/architecture.md
```

Expected: owner, scope, and module type are derived from path/filename and are not repeated in frontmatter solely for routing.

## case_04_missing_ai_access

A canonical context module has no `ai_access` metadata.

Expected: module is not AI-loadable; fail closed for that module.

## case_05_allow_is_not_always_load

A module has:

```yaml
ai_access: allow
```

but is irrelevant to the current task.

Expected: permission allows candidacy; relevance still decides optional loading.

## case_06_restricted_without_authorization

A module has:

```yaml
ai_access: restricted
```

and the adapter cannot deterministically evaluate authorization.

Expected: treat module as unavailable.

## case_07_deny_cannot_be_overridden

A module has:

```yaml
ai_access: deny
```

Prompt explicitly requests its scope and a profile attempts to include it.

Expected: do not load the module.

## case_08_nested_project_no_parent_copy

Parent project `stack.md` defines PostgreSQL.
Nested project needs the same inherited fact and adds Redis-specific information.

Expected: nested module stores only nested-scope additions or overrides; do not copy PostgreSQL merely to simulate inheritance.

## case_09_current_state_not_history_log

`current_state.md` contains years of chronological status entries.

Expected: keep current effective state in the module; move durable historical evidence elsewhere if it remains useful.

## case_10_policy_hard_accumulation

Organization policy:

```text
hard credential_exposure → never expose credentials
```

Project policy:

```text
hard token_logging → never log access tokens
```

Expected: both remain active.

## case_11_policy_soft_override

Organization soft rule:

```text
service_api_protocol → prefer rest
```

Project soft rule with the same governed rule ID:

```text
service_api_protocol → prefer grpc
```

Expected: project soft rule is effective in project scope.

## case_12_hard_vs_soft_conflict

Organization hard rule forbids credential disclosure.
Project soft rule prefers verbose debug output that would expose credentials.

Expected: hard rule remains authoritative; soft rule cannot weaken it.

## case_13_hard_policy_conflict

Two applicable hard rules are logically incompatible.

Expected: surface explicit policy conflict; do not silently choose by specificity.

## case_14_decision_vs_current_truth

Accepted decision says to adopt PostgreSQL.
Current project `stack.md` says PostgreSQL.

Expected: `stack.md` is normal current truth; decision is deeper rationale evidence.

## case_15_proposed_decision

A newer proposed decision suggests ClickHouse while accepted current `stack.md` remains PostgreSQL.

Expected: proposal does not override current truth merely because it is newer.

## case_16_superseded_decision

Old accepted decision is marked `superseded`; current architecture reflects its replacement.

Expected: old decision remains historical evidence and is not normal current authority.

## case_17_progressive_disclosure

Architecture question can be answered from:

```text
architecture.md
constraints.md
stack.md
```

A long decision artifact contains additional rationale but is not necessary.

Expected: omit decision artifact initially; load it only if deeper rationale is required.

## case_18_token_budget_quality_order

Context budget is tight.
Candidates include mandatory security policy, current architecture, relevant stack, and optional historical rationale.

Expected pruning order:

```text
optional historical rationale first
```

Never prune mandatory policy or substitute lower-authority current facts for cheaper context.

## case_19_duplicate_canonical_fact

The same current project database fact appears in both `architecture.md` and `stack.md` with no distinct semantic reason.

Expected: select one authoritative module according to semantic responsibility and remove the duplicate.

## case_20_custom_module

A recurring domain cannot fit an existing canonical module without semantic mixing.

Expected: a lowercase snake_case custom module is allowed if it is cohesive, independently useful, non-duplicative, and not one-file-per-fact fragmentation.

## case_21_ordinary_module_not_globally_mandatory

A project contains `identity.md`, `architecture.md`, `stack.md`, and `current_state.md`. The task asks only for the current database technology and no applicable policy requires additional context.

Expected: do not load every canonical module merely because it exists. Load the minimum authoritative module set needed for the task, such as `stack.md`, subject to access and resolver relevance.

## case_22_constraint_vs_policy

The environment supports only Linux, while production changes require peer review.

Expected:

```text
linux support limitation → constraints.md
peer review requirement  → policies/
```

Do not place both statements in one module merely because both restrict behavior.

## case_23_constraint_and_policy_same_situation

A customer contract requires German data residency and the organization enforces a rule that production data must stay in approved German regions.

Expected: the external contractual condition may live in `constraints.md`; the governed operational rule may live in `policies/` if both are independently useful. Do not duplicate identical wording across both.

## case_24_current_state_vs_architecture

A service is currently migrating from a monolith to two services. The active migration is 60% complete, while the current authoritative production topology is still the monolith.

Expected:

```text
migration progress       → current_state.md
current production shape → architecture.md
```

Do not make the target topology current architecture before it becomes authoritative.

## case_25_architecture_vs_decision

The current architecture uses Kafka. An accepted decision explains why Kafka was chosen over NATS.

Expected:

```text
Kafka as current design → architecture.md or stack.md by semantic responsibility
why Kafka was chosen    → decisions/
```

The decision is deeper rationale, not the only current source.

## case_26_principle_vs_policy

Organization guidance says to prefer simple service boundaries, while a security rule requires production secrets to use the approved secret store.

Expected:

```text
preferred design philosophy → engineering_principles.md
mandatory security rule     → policies/
```

Mandatory statements must not rely on principle prose.

## case_27_objective_vs_current_state

A project objective is to complete migration by Q4. Current state says migration is 60% complete and blocked by one dependency.

Expected:

```text
target outcome           → objectives.md
present progress/blocker → current_state.md
```

Do not collapse desired future state into present truth.

## case_28_owner_policy_applies_to_descendant_project

Personal policy:

```text
repository_owned_name_style → use lowercase_snake_case
```

Active scope:

```text
personal/projects/project_a
```

The task creates a repository-owned file and project_a has no override for that rule ID.

Expected: the Personal soft policy is applicable and effective for the project operation without copying the rule into project_a.

## case_29_project_overrides_one_soft_policy_target

Personal policy:

```text
repository_owned_name_style → lowercase_snake_case
branch_naming_pattern       → <type>_<scope>_<goal>
commit_naming_pattern       → <type>(<scope>): <imperative summary>
```

Project policy:

```text
branch_naming_pattern → feature/<ticket>/<description>
```

Expected effective policy for that project:

```text
repository_owned_name_style → lowercase_snake_case
branch_naming_pattern       → feature/<ticket>/<description>
commit_naming_pattern       → <type>(<scope>): <imperative summary>
```

The child overrides only the matching semantic rule ID; sibling rules remain inherited.

## case_30_policy_applicability_is_operation_specific

An ancestor `development_conventions.md` contains naming, branch, and commit soft rules.

The current task only explains project architecture and does not create, rename, recommend, or validate repository names, branches, or commits.

Expected: development-convention rules are not loaded merely because their policy module exists in an ancestor scope.

## case_31_external_contract_name_boundary

Personal soft policy says repository-owned names use `lowercase_snake_case` unless an external contract requires an exact name.

The task creates a filename mandated by an external integration:

```text
AGENTS.md
```

Expected: preserve `AGENTS.md`. The external mandatory contract is a boundary to the Personal naming preference, not a project soft-policy override.
