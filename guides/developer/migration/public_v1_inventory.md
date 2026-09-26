# Public V1 migration inventory

## Status

This sanitized historical record explains M1 classification decisions without
publishing the private source repository, refs, commit history, deployment
manifest, or Personal runtime selection. Current product governance is owned by
`system/governance/public_v1_product_contract.md`.

## Classification

Source-area labels below describe semantic origin only. They are not repository
or branch identities.

| source_area | classification | destination_path | action | reason |
|---|---|---|---|---|
| reusable system contracts | public_core | `system/` | MIGRATE | Client-neutral contracts, governance, validation, and tests were eligible after public review. |
| reusable presentation modules | public_core | `workspace/presentation/` | MIGRATE | Registered modules contained no Personal facts. |
| reusable profiles | public_core | `workspace/profiles/` | MIGRATE | Fact-free composition manifests were eligible. |
| reusable prompts | public_core | `workspace/prompts/` | MIGRATE | Independently usable prompts were eligible after prompt validation. |
| generic adapter guidance | public_core | `workspace/adapters/readme.md` | MIGRATE | Guidance was reusable; private adapter configuration was excluded. |
| generic workspace guidance | public_core | `workspace/context/readme.md`, `workspace/readme.md` | MIGRATE | Ownership guidance contained no canonical Personal facts. |
| developer guides and fake examples | public_core | `guides/developer/` | MIGRATE | Examples remained explicitly fake and non-runtime. |
| former user and root navigation | public_product | `guides/user/readme.md`, `guides/readme.md`, `readme.md` | REPLACE | M1 required beginner-first product navigation. |
| Personal context and sensitive context | private_personal | none | DO_NOT_MIGRATE | Real identity, goals, projects, finance, health, residence, and restricted facts are private. |
| Personal adapters and deployment defaults | private_personal | none | DO_NOT_MIGRATE | Private roots, defaults, client wrappers, and local configuration are not public product content. |
| Personal migration/release history | private_personal | none | DO_NOT_MIGRATE | Private provenance and deployment evidence are not public product content. |
| Personal behavior or test candidates | needs_review | none in M1 | NEEDS_REVIEW | Reusable behavior required independent generic reclassification and sanitization. |
| Personal prompt/profile/presentation candidates | public_product or needs_review | candidate public paths | GENERALIZE | Each candidate required fact removal, deduplication, ownership review, and validation before a later slice. |
| development naming rules | public_core | `system/governance/development_conventions.md` | GENERALIZE | Repository governance is not a Personal fact. |
| minimal Personal workspace | public_product | `workspace/context/readme.md` | KEEP | Context is created on demand; M1 did not add empty Personal fact modules. |

## Phase 0 gate

- No Personal context, adapter, deployment, or history file was eligible for M1.
- Reusable candidates remained excluded until a separate public-safe review.
- Every migrated file required classification, sanitization, and public validation.
