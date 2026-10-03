# m8_effective_context_trace

Worked synthetic trace for M1–M7 integration.

## prompt

```text
@ctx:org/acme/projects/payment_service/reconciliation
@ctx:personal
@profile:g.architecture.review
@depth:short

Compare the current messaging choice with its relevant constraints.
```

## 1_parse_switches

```text
primary_context = org/acme/projects/payment_service/reconciliation
supplemental_contexts = [personal]
profiles = [g.architecture.review]
explicit_depth = short
```

## 2_resolve_scopes

Primary chain:

```text
org/acme
org/acme/projects/payment_service
org/acme/projects/payment_service/reconciliation
```

Supplemental chain:

```text
personal
```

## 3_validate_access

Allowed relevant modules may continue.

```text
reconciliation/internal_notes.md
→ ai_access: deny
→ excluded before relevance/merge/precedence
```

## 4_select_relevant_atoms

Relevant current facts/policies:

```text
acme/stack.md
payment_service/stack.md
reconciliation/stack.md
acme/policies/engineering.md
payment_service/policies/engineering.md
```

Optional evidence:

```text
reconciliation/decisions/use_kafka.md
```

Load the decision only if rationale is required for the comparison.

Irrelevant to this task unless explicitly needed:

```text
reconciliation/current_state.md
personal preferred_region
beta/*
```

## 5_merge_primary_chain

Effective stack:

```yaml
database: postgresql
runtime: go_1_24
messaging: kafka
required_tests:
  - unit
  - integration
  - contract
settings:
  observability: advanced
  retries: 5
  tracing: enabled
```

Resolution highlights:

```text
mysql → shadowed by project postgresql
go_1_23 → shadowed by project go_1_24
required_tests → additive list merge inside the primary scope chain
settings → recursive map merge inside the primary scope chain
```

## 6_apply_policies

Hard policies accumulate:

```text
credential_exposure
token_logging
```

Soft policy:

```text
service_api_protocol = gRPC
```

Project soft policy overrides organization REST preference.

## 7_compose_supplemental

Target ownership is resolved before type-aware merge across context roles.

Personal fixture contains:

```yaml
database: sqlite
preferred_region: europe
required_tests:
  - exploratory
```

Primary already owns:

```text
database
required_tests
```

Therefore:

```text
personal database = sqlite
→ excluded from the primary-owned database target

personal required_tests = exploratory
→ does not extend the primary-owned required_tests list
```

`preferred_region` is not owned by Primary, so Personal could supply it if the task made that target relevant. This prompt does not require it, so relevance filtering leaves it unloaded/unused.

Hard policies remain the exception: an applicable accessible supplemental hard policy would still accumulate.

## 8_resolve_profile

`g.architecture.review` resolves to:

```text
behaviors = reasoning + research + communication
formats = compare
tone = professional
depth_default = deep
```

## 9_apply_prompt_presentation

Explicit prompt depth:

```text
short > profile deep default
```

Effective presentation:

```text
formats = compare
tone = professional
depth = short
```

No explicit current-prompt language request exists, so language follows lower contracted defaults/fallbacks without changing factual authority.

## 10_effective_configuration

```text
primary_scope = org/acme/projects/payment_service/reconciliation
supplemental_scopes = [personal]
behaviors = [reasoning, research, communication]
formats = [compare]
tone = professional
depth = short
messaging = kafka
database = postgresql
runtime = go_1_24
required_tests = [unit, integration, contract]
hard_policies = [credential_exposure, token_logging]
soft_service_api_protocol = grpc
```

Not effective for this task:

```text
personal database = sqlite
personal required_tests = exploratory
personal preferred_region = europe  # valid gap-fill candidate but irrelevant here
```

## 11_token_discipline

Do not load merely because available:

```text
denied internal notes
Beta organization context
unrelated current state
irrelevant Personal gap-fill targets
full decision history
all behavior modules
all presentation modules
all language modules
```

The effective context is the minimum sufficient authoritative composition for the task.

## acceptance

The trace is valid only if every effective value can be explained by source, access, scope role, target ownership, specificity, merge rule, profile/default rule, language/presentation precedence, relevance, and prompt override without hidden fallback or duplicated authority.
