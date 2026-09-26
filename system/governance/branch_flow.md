# Branch flow

## Purpose

Define how changes reach `main` in the public `Personal-SoT` product repository.
This repository does not inherit the long-lived Core/Personal branch topology or
deployment branches of the private source repository.

## Canonical branch

`main` is the accepted public product state and the base for new work. Do not
commit feature, fix, documentation, test, refactor, or maintenance changes
directly to `main`.

## Change flow

Create one short-lived branch from current `main` using the naming contract in
`system/governance/development_conventions.md`:

```text
main
→ <type>_<scope>_<goal>
→ relevant tests and validators
→ diff, semantic-duplication, and public-data review
→ pull request
→ main
```

Keep each branch and commit coherent. Independent changes use independent
branches rather than being accumulated into a release or integration branch.

## Source repository boundary

Material may be migrated from an upstream source only after classification,
sanitization, and public validation. Do not copy Personal branches, deployment
configuration, Personal facts, private project state, secrets, user-specific
paths, or Git history into this repository.

The upstream source branch model is migration evidence, not governance for this
public product. Reusable semantics belong to the public product only after an
explicit public-safe change is accepted through the flow above.

## Merge and release meaning

A merge to `main` means the change is accepted into the public repository. It
does not activate or mutate any user's Personal workspace, external deployment,
AI client configuration, or installed copy.

## Security boundary

A Git branch is a review and versioning boundary, not a security boundary. Raw
secrets and private Personal content remain forbidden on every branch.

## Acceptance

The branch model is compliant when work starts from current `main`, uses a
convention-compliant short-lived branch, passes the relevant checks and review,
and reaches `main` through a pull request without importing private source
repository branch semantics.
