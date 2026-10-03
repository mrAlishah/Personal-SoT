# Branch flow

## Purpose

Define how changes reach `develop` and then `main` in the public
`Personal-SoT` product repository. This repository does not inherit the
long-lived Core/Personal branch topology or deployment branches of the private
source repository.

## Canonical branches

`main` is the accepted, stable public product state. `develop` is the
integration branch that accumulates reviewed, accepted work before it reaches
`main`.

Both are long-lived. `develop` is intentionally exempt from the
`<type>_<scope>_<goal>` short-lived branch pattern.

Do not commit feature, fix, documentation, test, refactor, or maintenance
changes directly to `main`, and do not base new work on `main`. `develop` also
receives work through pull requests rather than direct commits.

## Change flow

Create one short-lived branch from current `develop` using the naming contract
in `system/governance/development_conventions.md`:

```text
develop
→ <type>_<scope>_<goal>
→ required checks
→ diff, semantic-duplication, and public-data review
→ pull request targeting develop
→ develop
```

Keep each branch and commit coherent. Independent changes use independent work
branches rather than being accumulated into one branch.

## Required checks

Run the full test suite and the canonical validators before opening a pull
request. `system/tests/` is deliberately not an importable package, so
`unittest discover` collects nothing; enumerate the test modules explicitly:

```text
python3 -B -m unittest $(find system/tests -name 'test_*.py' | sed 's#/#.#g;s#\.py$##')
```

```text
python3 -B system/validation/validate_public.py
python3 -B system/validation/validate_v1.py --mode core
python3 -B system/validation/validate_prompts.py
```

A run that collects zero tests is a failed check, not a pass.

## Source repository boundary

Material may be migrated from an upstream source only after classification,
sanitization, and public validation. Do not copy Personal branches, deployment
configuration, Personal facts, private project state, secrets, user-specific
paths, or Git history into this repository.

The upstream source branch model is migration evidence, not governance for this
public product. Reusable semantics belong to the public product only after an
explicit public-safe change is accepted through the flow above.

## Integration and release meaning

A merge to `develop` means the change passed review and is accepted into
integration. It is not a public release.

`develop` reaches `main` only as an explicit manual release decision. A merge to
`main` means the change is accepted into the stable public product state.

Neither merge activates or mutates any user's Personal workspace, external
deployment, AI client configuration, or installed copy.

## Security boundary

A Git branch is a review and versioning boundary, not a security boundary. Raw
secrets and private Personal content remain forbidden on every branch.

## Acceptance

The branch model is compliant when work starts from current `develop`, uses a
convention-compliant short-lived branch, passes the required checks and review,
reaches `develop` through a pull request, and reaches `main` only by explicit
release decision, without importing private source repository branch
semantics.
