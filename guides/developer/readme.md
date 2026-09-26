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

Reusable system change:

```text
Core feature/fix/refactor
-> review + validation
-> v1_ai_context_source_of_truth
-> develop
-> sync Core -> Personal
```

Personal facts and Personal-only prompt content never flow into Core.

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
