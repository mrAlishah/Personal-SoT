# migration_workflow

## purpose

Design-time workflow for converting existing AI/chat/project history into clean canonical Source-of-Truth modules.

Migration is not transcript storage. Extract durable, useful, currently valid knowledge and place it in one authoritative semantic home under `workspace/context/`.

## workflow

```text
inventory_sources
→ extract_candidate_claims
→ classify_owner_and_semantic_home
→ classify_sensitivity
→ determine_current_vs_historical_role
→ deduplicate_against_canonical_truth
→ surface_conflicts_or_uncertainty
→ write_minimum_canonical_fact
→ validate_access_and_registry
→ verify_with_tests
```

## design_time_only

`system/migration/` contains maintenance contracts/workflows and is not normal task context.

Fake migration examples live under `guides/developer/examples/migration/`.

## source_types

Sources may include chat/project history, existing notes, legacy prompts/instructions, manual notes, or repository docs. Source existence does not establish authority.

## core_rule

```text
history → evidence/candidate source
workspace/context/ → current authoritative home after review
```

Do not copy whole conversations into canonical context merely because they contain useful facts.

## installed_workspace_use

The public repository contains migration workflow and fake examples only. A
real Personal migration inventory belongs only in the user's installed
workspace and must not flow into the public repository.
