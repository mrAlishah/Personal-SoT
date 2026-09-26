# automation_contract

## purpose

Defines what automation may and may not do around the canonical AI Source of Truth.

## core_rule

```text
automation may assist canonical maintenance
automation may not become canonical authority by accident
```

Canonical Markdown remains authoritative unless an approved workflow intentionally writes a canonical change.

## safe_automation_classes

Automation may perform tasks such as:

```text
validate naming and path grammar
validate registries against existing targets
check missing or invalid ai_access metadata
check broken references
classify migration candidates
compare canonical modules for duplicate candidate facts
produce retrieval traces
produce generated indexes
produce change proposals
run contract scenario checks
```

These operations do not gain semantic authority merely because they are automated.

## canonical_writes

An automated canonical write is permitted only when all of the following remain satisfied:

1. target ownership is deterministic;
2. semantic home is deterministic;
3. effective access rules are preserved;
4. hard policies are not weakened;
5. target-ownership and precedence rules are preserved;
6. sensitive-data rules are preserved;
7. the change is reviewable in Git;
8. uncertainty that could materially alter canonical truth is not guessed.

If any required classification is unresolved:

```text
propose_or_defer
```

Do not silently write a guessed canonical result.

## historical_migration

Automation processing chat history or legacy notes follows `migration/` contracts.

It may extract candidate claims and classify them, but unresolved conflicts require confirmation before canonical mutation.

Raw secrets discovered in source history must not be copied into Git-backed context.

## access_boundary

Automation receives no implicit access advantage over an interactive AI client.

Before reading canonical content:

```text
host_permission
+
canonical_ai_access
+
required_restriction_authorization
→ effective_read_access
```

Automation must not use generated caches to bypass a later access denial.

## generated_indexes

Generated registries, indexes, search caches, summaries, or reports are derivatives.

If a generated artifact conflicts with canonical content, canonical content wins and the derivative should be regenerated or discarded.

## failure_behavior

Prefer explicit failure or partial safe output over silent repair when:

- a scope cannot be resolved;
- a registry entry is stale;
- a canonical fact conflict is unresolved;
- restricted authorization cannot be evaluated;
- a generated artifact is stale and cannot be regenerated reliably.

## idempotence

Where practical, validation and generation should be idempotent:

```text
same canonical inputs
+
same declared configuration
→ same semantic result
```

Do not encode hidden mutable state into generated truth.

## observability

Material canonical-changing automation should leave an inspectable Git diff and coherent commit message.

Diagnostics may record paths, rule identifiers, and failure classes, but must not leak denied or secret content.

## scheduling

Scheduling is an execution concern, not part of canonical meaning.

A scheduled job must obey the same contracts as an on-demand run. Frequency does not grant additional authority or access.

## non_goals

V1 does not require:

```text
continuous background synchronization
automatic self-modifying prompts
unreviewed autonomous canonical rewrites
vector database synchronization
custom always-on resolver service
```

Introduce these only after a concrete need is demonstrated and their authority/access model is explicit.

## acceptance

Automation is compliant when it reduces repetitive maintenance without creating hidden authority, duplicated truth, uncontrolled sensitive-data exposure, or unreproducible state.
