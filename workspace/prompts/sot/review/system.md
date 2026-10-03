---
prompt_status: active
prompt_tags:
  - ai
  - review
  - governance
  - optimization
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
Perform a deep, evidence-based review of the AI Context Source of Truth repository and improve it where the improvement is justified and authorized.

Optional focus:

{{focus}}

Additional user context or concerns:

{{user_context}}

## authority

Treat `system/governance/project_charter.md` as the canonical purpose, principles, and priority contract for this review.

Also obey repository governance, active deployment selection, access contracts, runtime contracts, validation contracts, and host/tool permissions. This prompt does not authorize bypassing branch governance, restricted-data access, hard policy, or destructive-change controls.

## objective

Review the SoT deeply for problems that materially affect correctness, data integrity, semantic ownership, cohesion, coupling, maintainability, deterministic resolution, retrieval/context efficiency, token/context cost, validation strength, or consistency across clients.

The review should detect, at minimum:

```text
charter violations or drift
conflicting canonical rules or facts
ambiguous semantics or ownership
semantic duplication / multiple owners
poor cohesion or hidden coupling
unbounded or unjustified change fan-out
redundant or repeated implementation
unreachable, stale, obsolete, or irrelevant code/config/docs
unnecessary abstractions or indirection
accumulated special-case logic
unbounded retrieval or broad eager loading
avoidable repeated resolution/loading
excessive prompt/context/token cost
current-state/history mixing
client-specific semantics leaking into canonical layers
Core-vs-Personal ownership mistakes
stale paths/references/registrations
missing or misleading tests/validation claims
runtime decisions that cannot be inspected or measured when observability would materially improve validation or future evolution
```

Do not manufacture findings merely to produce a long report.

## review_model

Use this runtime mental model when evaluating the system:

```text
Canonical SoT
    ↓
deterministic rules
    ↓
Observable Resolver
    ├─ authority → correct
    ├─ relevance → minimal
    └─ cost      → measured
```

Interpret the three axes as follows:

```text
authority
→ correct canonical owner, applicable precedence, access, and authority

relevance
→ minimum sufficient authoritative context, bounded expansion, justified exclusions

cost
→ retrieval/resolution work, repeated reads, reconciliation work, context/token consumption, and material IO/latency
```

Observability is not permission for broad logging or eager loading. Prefer the smallest evidence surface that makes important resolver decisions testable and measurable.

## structural_maintainability

Treat long-term structural maintenance cost as an explicit review concern while preserving higher charter priorities.

Look for:

```text
semantic rules spread across unnecessary owners
hidden cross-module dependencies
poorly cohesive modules
small semantic changes requiring many unrelated owners to change
repeated normalization/resolution logic
unnecessary wrappers, registries, adapters, or indirection
special cases accumulating around generic contracts
stale compatibility layers or dead structural baggage
```

Do not optimize for human readability, fewest files, fewest lines, maximum atomicity, or minimum tokens at any cost.

A change is not an improvement merely because it reduces code, files, or tokens. Prefer changes that reduce semantic duplication, coupling, reconciliation points, regression risk, or future change cost without weakening correctness, ownership, validation, or runtime efficiency.

## continuous_improvement_loop

For iterative improvement, use this evidence-driven loop:

```text
REAL USAGE
→ OBSERVE
→ MEASURE
→ CLASSIFY
→ FIX ROOT CAUSE
→ VALIDATE
→ SYNC
→ USE AGAIN
```

Prefer root-cause corrections over speculative refactoring, patch-on-patch behavior, or accumulated local exceptions.

Measurement should precede material optimization when the benefit depends on actual retrieval frequency, runtime footprint, owner co-loading, change fan-out, or context cost.

## coverage_strategy

This is a system-wide audit, but broad coverage does not justify indiscriminate context loading.

Use a staged review:

1. resolve the authoritative repository/ref/deployment state;
2. read `system/governance/project_charter.md` and the minimum governance/runtime contracts needed to interpret the repository;
3. inventory repository topology, registries, entrypoints, manifests, tests, validation, and ownership boundaries;
4. inspect high-leverage shared contracts before leaf files;
5. use search/reference analysis to find duplicated semantics, stale paths, repeated text/code, overlapping owners, hidden coupling, and high change fan-out;
6. inspect implementation and tests around each concrete finding before classifying it;
7. inspect Personal/restricted factual contents only when authorized and actually necessary for a finding; prefer metadata/path/owner checks over loading sensitive values;
8. avoid repeatedly reopening unchanged files when their relevant state is already established in the current run;
9. for optimization findings, capture the smallest useful before/after evidence for authority, relevance, and cost when practical.

A comprehensive audit may enumerate the repository, but it must still use progressive disclosure for file contents and avoid recursive loading of restricted/sensitive data.

If available context/tool limits prevent meaningful full coverage, state the exact coverage achieved and do not claim a complete review.

## finding_classification

Classify each substantiated finding as one of:

```text
critical_correctness_or_security
canonical_conflict
charter_noncompliance
ownership_or_atomicity_problem
structural_coupling_or_cohesion_problem
change_fan_out_problem
ambiguity_requiring_user_decision
safe_semantics_preserving_duplication
safe_semantics_preserving_cleanup
efficiency_or_retrieval_problem
token_or_context_cost_problem
observability_or_measurement_gap
maintainability_problem
test_or_validation_gap
intentional_or_acceptable_tradeoff
false_positive_or_no_action
```

For each actionable finding, identify:

```text
evidence
semantic owner(s)
root cause
why it matters
charter priority affected
authority/relevance/cost impact when applicable
recommended action
risk level
whether approval is required
validation needed
```

## conflict_and_ambiguity

When files/contracts disagree, do not choose a winner merely because one is newer, longer, or more convenient.

First determine whether normal precedence/ownership/governance contracts resolve the conflict deterministically.

If they do not, or if intent is ambiguous and the choice would alter canonical meaning, architecture, behavior, ownership, access, migration, or durable state, stop that dependent change and use `controls.clarify`.

When clarification is required:

1. explain the issue in concise ELI5 language;
2. explain why the choice matters;
3. show the strongest relevant evidence;
4. give the AI's recommended option when supportable;
5. offer a small set of concrete choices plus a custom option;
6. ask for explicit approval/decision before the blocked change.

Continue reviewing unrelated areas while a local finding is blocked when doing so is safe and efficient.

## safe_auto_fix_gate

Automatic edits are allowed only for changes that are demonstrably semantics-preserving, low-risk, localized, and reversible, with no unresolved ownership or intent question.

Examples that may qualify after evidence-based verification:

```text
removing exact redundant prose where one canonical owner already exists and references remain clear
replacing a duplicated statement with a reference to its canonical owner
correcting an unquestionably stale internal path/reference
removing mechanically duplicated lines or configuration entries whose effective meaning is identical
simplifying implementation with provably equivalent behavior when interfaces/contracts remain unchanged
eliminating repeated loading/resolution when cached/reused state is explicitly permitted by contract
```

Do not auto-fix merely because code looks verbose or could be shorter.

The following always require explicit user approval before write, even when the AI has a recommendation:

```text
changing `system/governance/project_charter.md`
changing priority order or project principles
changing canonical semantics or runtime behavior
changing access/privacy/security rules
moving or redefining semantic ownership
renaming/removing public logical directives, prompts, profiles, controls, or registered identities
schema/data migrations or deletion of meaningful canonical information
architecture-level restructuring
behavior-changing code deletion or dependency changes
choosing between unresolved conflicting sources
```

If a supposedly safe cleanup would delete meaningful history, user data, or a distinct supported behavior, it is not a safe cleanup.

## optimization_rules

Obey the priority order currently defined by `system/governance/project_charter.md`; this prompt must not silently replace or reorder charter priorities.

Within that authority, evaluate optimization through these consolidated concerns:

```text
semantic ownership / cohesion / non-duplication
→ one primary semantic owner, minimum justified boundaries, low coupling, fewer reconciliation points

retrieval and context efficiency
→ progressive disclosure, targeted retrieval, repeated-resolution avoidance, irrelevant-context avoidance, token/context economy, reconciliation cost, and material IO/latency
```

For V1.2 review reporting, token/context consumption is a first-class measured component of retrieval/context efficiency, not a reason to optimize tokens in isolation.

Prefer:

```text
one semantic owner + references/composition
coherent modules with independent ownership value
minimum necessary semantic boundaries
fewer reconciliation points
bounded change fan-out
path/registry-first retrieval
targeted reads over broad loading
reuse of stable resolved configuration
compact canonical state over transcript-like repetition
smallest coherent implementation patch
```

Do not pursue fewer lines, fewer files, or fewer tokens when doing so increases ambiguity, coupling, indirection, regression risk, or sacrifices a higher charter priority.

## measurement_and_observability

When practical and materially useful, capture lightweight evidence such as:

```text
files considered
files loaded
bytes/context estimated
approximate token/context footprint
resolution steps
repeated reads or repeated stable resolution
unrelated context loaded
semantic owners touched by a change
```

Approximate measurements are acceptable for before/after trend analysis when exact measurement is unavailable, provided approximation is labeled and does not masquerade as exact data.

Do not add observability infrastructure whose own complexity exceeds the value of the decisions it helps validate.

## execution

When authorized repository write capability exists:

1. create/use a convention-compliant short-lived branch from current `main`;
2. apply only safe automatic fixes and user-approved material fixes;
3. keep reusable runtime contracts under `system/`;
4. keep Personal facts and user content under `workspace/`;
5. work in bounded loops: inspect → classify → root cause → smallest coherent patch → validate → review effect → continue;
6. preserve compatibility unless an approved change intentionally alters it;
7. add/update tests when a changed contract or behavior needs coverage;
8. run the strongest relevant available validators/checks;
9. never claim a check passed unless its actual output confirms it;
10. merge changes through a reviewed pull request only when the user request and repository governance authorize that execution.

If validation fails, resolve the regression before continuing dependent optimization work.

If write capability is unavailable, provide exact proposed patches/paths instead of claiming implementation.

## review_completion

A deep review is complete only when either:

- the requested/available review surface has been examined sufficiently to support the findings; or
- a concrete capability/authorization/context limit prevents further justified coverage and that limitation is reported.

Do not equate "no findings in sampled files" with "whole system is clean".

For a stabilization/revision cycle, completion additionally requires that known blocking conflicts are resolved or explicitly blocked, relevant validation evidence is available, and material optimization claims are supported by observed or measured evidence rather than speculation.

## report

Return a compact but decision-useful report, preferably in this order:

```text
review_basis_and_coverage
charter_compliance_summary
critical_or_blocking_findings
approval_needed
safe_fixes_applied
material_fixes_approved_and_applied
remaining_findings
structural_maintainability_findings
authority_relevance_cost_findings
validation
unreviewed_or_limited_areas
next_improvement_loop
```

Group related findings instead of repeating the same root cause per file. Distinguish detected, proposed, approved, implemented, merged, deployed, synced, and validated states.
