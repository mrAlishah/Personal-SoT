# generated_artifact_contract

## purpose

Defines the authority and lifecycle of machine-generated derivatives.

## core_rule

```text
generated_artifact
≠ canonical truth
```

A generated artifact is disposable unless a separate approved process promotes specific content into a canonical module.

## examples

Generated derivatives may include:

```text
search indexes
retrieval caches
registry validation reports
migration inventories
context traces
duplicate-candidate reports
summary dashboards
compiled adapter payloads
```

## authority

When a generated artifact conflicts with its canonical source:

```text
canonical source wins
```

Do not manually patch generated output as a substitute for fixing canonical input or the generator.

## reproducibility

A generated artifact should identify enough input/configuration context to be reproducible when practical, without copying sensitive content unnecessarily.

Prefer regenerating artifacts over maintaining hand-edited synchronized copies.

## storage

Generated artifacts should live outside canonical factual scope unless a directory is explicitly designated for generated derivatives.

They must not be registered as factual contexts merely because retrieval tooling can read them.

## sensitive_content

Do not persist denied content in generated artifacts.

Restricted content may appear in a generated derivative only when the generating workflow is deterministically authorized and the derivative receives an equally strong or stronger access boundary.

Raw secrets remain forbidden.

When safe, prefer metadata-only diagnostics over copying sensitive source text.

## staleness

Stale generated artifacts are not fallback authority.

If freshness cannot be established and the canonical source is available, regenerate or ignore the derivative.

## promotion

If generated analysis reveals a durable canonical fact:

```text
generated candidate
→ classify owner + semantic home + access + currentness
→ review
→ write canonical module
```

Do not treat the generated report itself as the canonical home.

## cleanup

Generated artifacts may be deleted and recreated without semantic loss, provided canonical sources and required generator configuration remain intact.

## acceptance

Generated artifacts improve efficiency while remaining clearly subordinate, reproducible, access-safe, and disposable relative to canonical Markdown.
