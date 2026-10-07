# Branch flow

## Purpose

Define how changes reach `develop` and `main` in the public `Personal-SoT` product repository.

Change classification and validation level are owned by `system/governance/change_policy.md`.

## Canonical branches

`main` is the stable public product state. `develop` is the normal integration branch.

## Help-documentation fast path

A pure `help_docs` change does not require a short-lived branch, pull request, or Python test suite.

Default flow:

```text
current develop
→ edit help-only docs directly
→ diff/link/path/public-data hygiene
→ commit to develop
```

If the user explicitly requests a stable documentation correction on `main`, a help-only docs change may be committed directly to current `main` after the same hygiene review.

This exception applies only to explanatory user/developer help. It does not apply to runtime contracts, governance, adapters, machine-consumed instructions/configuration, schemas, prompts, installers, validators, tests, or any documentation edit that changes product semantics.

When Git command capability exists, run:

```text
git diff --check
```

No Python tests/validators are required solely for a help-only documentation change.

## Engineered product flow

A `system_change` uses a short-lived branch from current `develop`:

```text
develop
→ <type>_<scope>_<goal>
→ full relevant checks
→ diff + semantic-duplication + public-data review
→ pull request targeting develop
→ develop
```

Keep independent system changes independently reviewable.

## Full checks

For a system/product change, run:

```text
python3 -B -m unittest $(find system/tests -name 'test_*.py' | sed 's#/#.#g;s#\.py$##')
python3 -B system/validation/validate_public.py
python3 -B system/validation/validate_v1.py --mode core
python3 -B system/validation/validate_prompts.py
```

Also run `git diff --check <base>...HEAD`.

A run that collects zero tests is not a pass.

## Source repository boundary

Material may be migrated from an upstream/private source only after classification, sanitization, and public review. Do not copy Personal facts, private project state, private deployment configuration, secrets, user-specific paths, or private Git history into this repository.

## Integration and release meaning

A system/product merge to `develop` means accepted integration, not stable release.

`develop` reaches `main` only through an explicit release decision for product semantics. A direct help-only docs correction on `main` is a documentation exception; it does not authorize direct runtime/product changes.

Neither path mutates any user's private Personal-SoT automatically.

## Security boundary

A branch is a review/versioning control, not a security boundary. Secrets and private Personal content remain forbidden on every public branch.

## Acceptance

The flow is compliant when help-only docs use the light path, system/product changes use the engineered branch/full-check path, and classification is based on semantics rather than file extension.
