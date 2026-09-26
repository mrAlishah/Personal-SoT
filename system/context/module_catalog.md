# canonical_module_catalog

## purpose

Defines default semantic responsibilities for canonical V1 context modules.

This catalog defines boundaries, not mandatory file creation.

```text
semantic_need
→ create_module

no_independent_semantic_need
→ omit_module
```

Canonical facts have one authoritative home. Composition supplies parent/sibling facts when relevant; do not copy them merely to make one file self-contained.

## catalog_rules

- repository-owned filenames use lowercase_snake_case;
- path determines factual ownership scope;
- one module has one independently useful semantic responsibility;
- separate domains when they are routinely retrieved separately, have materially different lifecycles/access, or combining them creates material token/privacy waste;
- do not split into one-file-per-fact fragments;
- factual modules do not own behavior, presentation, adapter configuration, or runtime switches;
- nested scopes store only their own additions/overrides, not copied parent truth.

# personal_scope

## identity.md

Stable high-level personal identity.

Typical content:

```text
name or preferred identity
stable location/language facts when broadly relevant
profession
seniority
high-level professional specialization
```

Exclude:

```text
detailed technology lists or engineering capability → tech_profile.md
current role-search positioning → project scope
current goals → goals.md or project objectives.md
working preferences → working_style.md
short-lived state → current_state.md or owning project current_state.md
```

`identity.md` should answer "who is this person at a stable high level?", not serve as a résumé or technical profile.

## current_state.md

Current **cross-project** personal state that materially changes recommendations across multiple domains.

Use only when such state exists independently of active projects.

If every current fact is more precisely owned by projects such as job search, language learning, or a technical project, the Personal root may legitimately have no `current_state.md`.

Do not create a root dashboard that copies child-project status merely for convenience.

## goals.md

Cross-project personal outcome goals.

Typical examples:

```text
long-term career trajectory
financial independence direction
home-ownership direction
cross-domain life outcomes
```

Project-owned outcomes belong to that project's `objectives.md`.

Do not duplicate near-term project objectives at Personal root merely because they are important.

## constraints.md

Cross-project real-world limitations that constrain personal decisions or plans.

Examples:

```text
time/capacity
budget envelope when broadly applicable
legal/location constraints when cross-domain
availability/resource constraints
```

Exclude:

```text
behavioral preference → working_style.md
machine/tool fact → appropriate custom environment module
project-only constraint → project constraints.md
presentation preference → presentation/profile layer
```

## tech_profile.md

Durable technical capability and engineering experience reusable across technical tasks.

Typical content:

```text
languages/frameworks/databases/infrastructure experience
system/backend domains
engineering strengths
measured technical achievements
```

Exclude:

```text
current learning targets → learning project objectives/current_state
current workstation/tool installation → environment context
project-specific stack/version → project stack.md
employment chronology/evidence → employment-history artifact when independently useful
```

A technology may legitimately appear in employment history as historical evidence and in `tech_profile.md` as current durable capability because those artifacts answer different questions. Avoid identical duplicated prose.

## working_style.md

Stable collaboration, execution, learning, planning, and tool-choice preferences that are factual descriptions of how the user works.

Response format/tone/depth/language defaults remain in presentation/profile layers.

Project-specific operating goals remain in their project scope.

## sensitive/

Optional personal risk/access boundary for AI-relevant sensitive context.

The directory is not one semantic atom. Preserve semantic atomicity inside it.

Illustrative atoms:

```text
sensitive/health_constraints.md
sensitive/financial_planning.md
sensitive/residence_context.md
sensitive/secret_references.md
```

Real personal contexts may use narrower atoms when independent retrieval/lifecycle justifies it, for example:

```text
current household finance ≠ historical tax-year evidence
residence status ≠ health-insurance administration
musculoskeletal health ≠ cardiometabolic health
```

Sensitive modules normally use `ai_access: restricted` and follow `system/context/sensitive_data_contract.md`.

Raw secrets never belong in Git-backed context.

# organization_scope

## identity.md

Stable organization identity and high-level organizational facts.

## business_context.md

Business domain, products, customers, operating model, and business concepts needed across organization work.

Exclude project-specific implementation detail.

## constraints.md

Organization-wide factual constraints applying across projects.

## engineering_principles.md

Organization-wide preferred engineering/design guidance.

Mandatory rules belong in policies rather than being hidden in principle prose.

## terminology.md

Organization-specific vocabulary, abbreviations, domain terms, and canonical meanings useful across projects.

## policies/

Normative organization rules grouped by semantic domain, e.g. security/compliance/coding.

Hard/soft semantics follow routing/policy contracts.

# project_scope

Personal and organization projects use the same module responsibilities.

## project.md

Stable project identity, purpose, scope boundary, and domain description.

Exclude information owned more precisely by objectives, architecture, stack, current_state, constraints, policies, or decisions.

## objectives.md

Current project outcomes, priorities, and target results.

Objectives answer "where is this project trying to go?"

## current_state.md

Current effective project/delivery state.

Typical content:

```text
current phase
active implementation/delivery status
blockers
migration progress
active risks
current focus
```

Do not copy parent identity, capability, language level, or other owner-root facts. Compose them from the scope chain when relevant.

Do not turn `current_state.md` into an append-only history log.

## architecture.md

Current authoritative system structure, boundaries, components, responsibilities, and data/control flows.

Historical rationale belongs to decision artifacts when independently useful.

## stack.md

Current project technology/platform facts.

Typical content:

```text
languages/runtimes/frameworks
databases/caches/messaging
infrastructure/build/deployment technologies
```

Personal skills and organization-wide principles are not project stack facts.

## constraints.md

Project-specific factual limitations and non-negotiable operating conditions.

A constraint describes the box the project operates inside. A policy describes governed behavior inside the box.

## terminology.md

Project-specific vocabulary/meanings not already owned upstream.

Do not copy parent terminology.

## policies/

Project-specific normative rules.

Project hard policies may add stricter requirements but cannot weaken applicable upstream hard policies.

## decisions/

Durable decision rationale/history whose context, alternatives, consequences, or lifecycle remain independently useful.

Decision artifacts do not replace current truth in `architecture.md`, `stack.md`, `constraints.md`, or `current_state.md`.

# nested_projects

Nested projects reuse project module responsibilities and store only nested-owned additions/overrides.

```text
workspace/context/organizations/acme/projects/payment_service/
├── architecture.md
├── stack.md
└── reconciliation/
    ├── architecture.md
    ├── constraints.md
    └── current_state.md
```

The child does not copy parent content to simulate inheritance. Scope composition supplies upstream context.

# custom_modules

A scope MAY introduce a custom module when existing canonical modules would force semantic mixing.

A custom module must:

- use lowercase_snake_case;
- have one clear responsibility;
- be independently useful;
- not duplicate an existing canonical home;
- not create one-file-per-fact fragmentation.

Examples may include an environment or employment-history atom when those concerns are repeatedly useful independently and do not fit the default catalog cleanly.

If the same custom pattern becomes common across many scopes, consider promoting it into the canonical catalog in a later architecture revision.

# selection_guidance

Typical relevance patterns:

```text
architecture review
→ architecture + constraints + stack + applicable policies

project status planning
→ objectives + current_state + constraints

technical capability question
→ personal tech_profile

current project learning focus
→ project current_state + objectives; parent tech_profile only when needed

deep design rationale
→ current architecture/stack + relevant decision

narrow sensitive task
→ only relevant authorized sensitive atom(s)
```

These are relevance hints, not unconditional dependency graphs.

# acceptance

The catalog works when contributors can place a new fact without duplicate authority, omit unnecessary modules, distinguish root vs project ownership, and retrieve a small semantically coherent atom set without losing correctness.
