# static_validation

## purpose

Dependency-free local static checks for Source-of-Truth invariants.

Run from repository root.

## core_personal_validator

```bash
python3 system/validation/validate_v1.py --mode core
python3 system/validation/validate_v1.py --mode personal
```

It checks the three-root layout, naming, Core isolation, `ai_access`, profile references, registries, decision status, and a simple canonical-context secret guard.

## prompt_validator

```bash
python3 system/validation/validate_prompts.py
```

It validates real `workspace/prompts/` templates and fake `guides/developer/examples/prompts/` templates for manifest fields, lifecycle, path/parameter identifiers, variable declarations, referenced profiles/presentation modules, owned assets and simple raw-secret assignments.

Prompt execution semantics remain contract/integration-test concerns; the validator does not execute prompts.

## non_goals

These validators are not a runtime resolver, prompt engine, semantic search engine, complete secret scanner, full YAML parser, or proof of semantic factual quality/currentness.

## privacy

Hosted CI remains optional. Personal validation stays local-first until an explicit CI/privacy decision is made.

## exit_behavior

```text
0 → implemented structural checks passed
1 → one or more structural violations were found
```
