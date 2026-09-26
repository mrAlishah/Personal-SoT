# Developer Guide

## Repository boundaries

```text
workspace/  end-user managed canonical content/configuration
system/     engine contracts, algorithms, validation and tests
guides/     audience-specific documentation
```

Logical identifiers are decoupled from physical paths. Runtime mapping is:

```text
@ctx        -> workspace/context/
@profile    -> workspace/profiles/
@fmt        -> workspace/presentation/formats/
@tone       -> workspace/presentation/tones/
@depth      -> workspace/presentation/depth/
language    -> workspace/presentation/languages/
prompt path -> workspace/prompts/
```

The contracts that interpret those files live under `system/`.

## Development flow

Start from current `main` and follow
`system/governance/branch_flow.md`:

```text
main
-> short-lived <type>_<scope>_<goal> branch
-> relevant tests, validators, and review
-> pull request
-> main
```

Reusable runtime semantics belong under `system/`. Personal facts and
Personal-only content remain under `workspace/` and never become system
contracts.

## Validation

```bash
python3 system/validation/validate_v1.py --mode core
python3 system/validation/validate_prompts.py
```

Personal:

```bash
python3 system/validation/validate_v1.py --mode personal
python3 system/validation/validate_prompts.py
```

Fake examples used by developers live under `guides/developer/examples/` and never become runtime canonical context.
