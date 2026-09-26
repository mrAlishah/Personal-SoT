# v1_readiness

## status

V1 remains the hardened semantic baseline. V1.1 may change physical layout and add compatible extensions without weakening V1 invariants.

## governing_priorities

```text
1. quality_and_correctness
2. token_efficiency
3. atomic_and_composable_context
```

## persistent_invariants

- generic Core contains no real Personal/organization canonical facts;
- fake examples are non-runtime and unregistered;
- raw secrets remain excluded;
- `ai_access` is checked before exposure/relevance;
- unauthorized restricted context fails closed;
- hard policies accumulate;
- Primary target ownership prevents supplemental mutation;
- each canonical fact has one authoritative semantic home;
- profiles remain compact/fact-free;
- adapters remain thin;
- retrieval does not create authority;
- Core → Personal remains one-way;
- presentation composition remains deterministic;
- static validation is structural and does not replace semantic review;
- `main` remains untouched unless separately authorized.

## current_physical_mapping

The V1 semantic model now resolves canonical factual content under:

```text
workspace/context/
```

System contracts live under:

```text
system/
```

This physical refactor does not change runtime scope identities.

## validation

```bash
python3 system/validation/validate_v1.py --mode core
python3 system/validation/validate_v1.py --mode personal
```

V1.1 prompt validation:

```bash
python3 system/validation/validate_prompts.py
```

## validation_assets

```text
system/validation/readme.md
system/validation/validate_v1.py
system/tests/validation/v1_static_validation_cases.md
system/tests/integration/v1_core_acceptance.md
```
