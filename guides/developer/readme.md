# Developer Guide

This guide is for people changing the **public Personal-SoT product**.

If you only want to use Personal-SoT, start with the [Beginner guide](../user/readme.md).

## Developer flow in 60 seconds

Start from current `develop`:

```bash
git fetch origin
git switch develop
git pull --ff-only
git switch -c <type>_<scope>_<goal>
```

Make the smallest coherent change, then run:

```bash
python3 -B -m unittest $(find system/tests -name 'test_*.py' | sed 's#/#.#g;s#\.py$##')

python3 -B system/validation/validate_public.py
python3 -B system/validation/validate_v1.py --mode core
python3 -B system/validation/validate_prompts.py

git diff --check <base>...HEAD
```

A run that collects zero tests is **not** a pass.

The normal flow is:

```text
develop
→ short-lived <type>_<scope>_<goal> branch
→ tests + validators
→ diff / ownership / privacy review
→ review / integration into develop
→ explicit release decision
→ main
```

`main` is the stable released product. `develop` is the integration branch.

## Repository boundaries

```text
workspace/
→ user-owned canonical content and configuration

system/
→ runtime contracts, routing, algorithms, validation and tests

guides/
→ user and developer documentation
```

Reusable runtime semantics belong under `system/`.

Real Personal facts, private deployment state, credentials, user-specific absolute paths, and Personal Git history do **not** belong in the public repository.

## Canonical runtime entry

The repository runtime starts from:

```text
workspace/adapters/runtime_entrypoint.md
```

Adapters are thin. They point to canonical contracts instead of duplicating workflow logic.

Before changing behavior, find the existing semantic owner.

Examples:

```text
runtime/source access  → system/adapters/
Assistant workflows    → system/assistant/
routing/directives     → system/routing/
diagnostics            → system/diagnostics/
updates                → system/update/
validation             → system/validation/
```

Prefer:

```text
reuse existing owner
→ smallest root-cause change
```

not:

```text
new wrapper
→ duplicated semantics
```

## Public vs private source roles

User-facing terminology:

```text
sot
→ user's private installation

sot public
→ mrAlishah/Personal-SoT
```

Do not copy private Personal facts or private deployment configuration into the public product.

Repository visibility is not authorization.

## Important runtime actions

These are user-facing entry points, not separate implementations:

```text
@do:sot     → resolve/reload/re-anchor runtime
@do:setup   → setup/resume/improve/update routing
@do:doctor  → read-only diagnosis
@do:fix     → guided diagnosis and safe repair
@do:help    → read-only explain/discover/recommend
@do:assist  → guided create/change/customize
```

If you change one of these, update the canonical contract, parser/tests, and beginner docs together.

## Change discipline

Before implementation:

```text
1. inspect current owner
2. confirm current branch/ref
3. identify public/private boundary
4. choose the smallest coherent change
```

For material writes/workflows preserve:

```text
understand
→ preview
→ explicit confirmation
→ current-state re-check
→ authorized write
→ validation
→ truthful report
```

Never claim a test passed without its actual output.

## Documentation

User docs should be:

```text
natural-language-first
ELI5 where possible
short path first
advanced detail later
```

A beginner should not need Git/YAML/internal paths to use the product.

When product behavior changes, update the smallest relevant set under:

```text
readme.md
guides/user/
guides/developer/
```

Do not duplicate canonical runtime contracts in guides; summarize and link to the owner.

## Release meaning

Integration into `develop` means the change is accepted for integration.

Release to `main` is a separate explicit decision.

Neither action automatically changes any user's private installation.

## Useful references

- Public product contract: `system/governance/public_v1_product_contract.md`
- Branch flow: `system/governance/branch_flow.md`
- Development conventions: `system/governance/development_conventions.md`
- Safe-write contract: `system/assistant/safe_write_contract.md`
- Source access contract: `system/adapters/source_access_contract.md`
- Runtime syntax: `system/routing/switch_syntax.md`
