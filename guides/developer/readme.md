# Developer Guide

This guide is for changing the **public Personal-SoT product**.

If you only want to use the system, start with the [Beginner guide](../user/readme.md).

## 60-second workflow

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

A zero-test run is not a pass.

Canonical flow:

```text
develop
→ short-lived branch
→ tests + validators
→ diff / ownership / privacy review
→ PR to develop
→ explicit release
→ main
```

`develop` is integration. `main` is the stable release.

## Repository map

```text
workspace/  user-owned canonical content/configuration
system/     runtime contracts, routing, validation and tests
guides/     user/developer documentation
```

Reusable runtime semantics belong in `system/`.

Real Personal facts, credentials, private deployment state, user-specific paths, and Personal Git history do not belong in the public repository.

## Find the semantic owner first

Runtime starts from:

```text
workspace/adapters/runtime_entrypoint.md
```

Common owners:

```text
source/runtime access → system/adapters/
Assistant workflows   → system/assistant/
directives/routing    → system/routing/
diagnostics           → system/diagnostics/
updates               → system/update/
validation            → system/validation/
```

Prefer:

```text
existing owner → smallest root-cause change
```

not duplicated wrapper logic.

### Keep the runtime entrypoint stable

`workspace/adapters/runtime_entrypoint.md` is the public deployment boundary.
Do not use it as a feature registry. Private deployments intentionally diverge
there, so changing the public file can manufacture a both-changed Safe Update
conflict for otherwise unrelated product work.

Add reusable behavior to the appropriate `system/` owner and its already
referenced contracts instead. `validate_public.py` intentionally rejects
public runtime-entrypoint drift.

Safe Update UX acceptance for the normal Git path is:

```text
one command/request
→ one preview
→ one confirmation
→ apply + validators + report
```

The E2E suite must preserve that path while stale previews and genuine
conflicts continue to fail closed.

## Source roles

```text
sot        → user's private installation
sot public → mrAlishah/Personal-SoT
```

Repository visibility is not authorization. Never move Personal/private state into `sot public`.

## Runtime actions

```text
@do:sot     re-anchor runtime
@do:setup   setup/resume/improve/update routing
@do:doctor  read-only diagnosis
@do:fix     guided safe repair
@do:help    explain/discover/recommend
@do:assist  create/change/customize
```

If behavior changes, update its canonical contract, relevant parser/tests, and the smallest affected guide.

## Change discipline

Before implementation:

```text
inspect current owner
→ verify branch/ref
→ check public/private boundary
→ make smallest coherent change
```

For material writes preserve:

```text
preview → confirm → re-check → write → validate → truthful report
```

Never claim a test passed without actual output.

## Documentation rule

User docs should be:

```text
natural-language-first
ELI5
short path first
advanced detail later
```

Do not copy full runtime contracts into guides. Summarize and link to the canonical owner.

## References

- `system/governance/public_v1_product_contract.md`
- `system/governance/branch_flow.md`
- `system/governance/development_conventions.md`
- `system/assistant/safe_write_contract.md`
- `system/adapters/source_access_contract.md`
- `system/routing/switch_syntax.md`
