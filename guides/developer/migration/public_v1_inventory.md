# Public V1 migration inventory

## Resolved source

```text
repository: mrAlishah/obsidian-ai-context-source-of-truth
default_branch: main
default_branch_sha: eed051fae42cf3cc78c5b61b2d0a46f52457b903
deployment_manifest: deployments/personal.yaml
active_ref: v1.2_ai_personal_source_of_truth
active_ref_sha: f4032444a361292a1d986fef1a445fe0a24328ee
entrypoint: workspace/adapters/runtime_entrypoint.md
generic_core_ref: v1.2_ai_context_source_of_truth
generic_core_sha: d66dec7a94c7f79b4a5340e8c0d8c76bf5c548cb
```

The deployment selection was resolved from `deployments/personal.yaml` on source `main`. The entrypoint and its referenced deployment/runtime/base instruction files were read from the active Personal ref. Migration content is sourced from the generic Core ref unless a row below explicitly says otherwise.

## Classification

Paths ending in `/` classify the whole subtree except where a later row is more specific.

| source_path | classification | destination_path | action | reason |
|---|---|---|---|---|
| `v1.2_ai_context_source_of_truth:system/` | public_core | `system/` | MIGRATE | Generic client-neutral contracts, governance, validation, and tests; no Personal overlay. |
| `v1.2_ai_context_source_of_truth:workspace/presentation/` | public_core | `workspace/presentation/` | MIGRATE | Generic registered presentation modules. |
| `v1.2_ai_context_source_of_truth:workspace/profiles/` | public_core | `workspace/profiles/` | MIGRATE | Generic fact-free composition manifests. |
| `v1.2_ai_context_source_of_truth:workspace/prompts/` | public_core | `workspace/prompts/` | MIGRATE | Generic reusable prompts that already satisfy Core ownership. |
| `v1.2_ai_context_source_of_truth:workspace/adapters/readme.md` | public_core | same | MIGRATE | Generic adapter guidance only. |
| `v1.2_ai_context_source_of_truth:workspace/context/readme.md` | public_core | same | MIGRATE | Contract navigation; contains no canonical Personal facts. |
| `v1.2_ai_context_source_of_truth:workspace/readme.md` | public_core | same | MIGRATE | Generic workspace ownership guidance. |
| `v1.2_ai_context_source_of_truth:guides/developer/` | public_core | `guides/developer/` | MIGRATE | Architecture guidance and explicitly fake examples. |
| `v1.2_ai_context_source_of_truth:guides/user/readme.md` | public_product | `guides/user/readme.md` | REPLACE | Existing guide assumes SoT knowledge; M1 needs beginner navigation. |
| `v1.2_ai_context_source_of_truth:guides/readme.md` | public_product | same | GENERALIZE | Keep audience navigation but make the beginner path primary. |
| `v1.2_ai_context_source_of_truth:readme.md` | public_product | `readme.md` | REPLACE | Existing root entrypoint is framework-first rather than product-first. |
| `v1.2_ai_personal_source_of_truth:workspace/context/personal/` | private_personal | none | DO_NOT_MIGRATE | Real identity, employment, goals, current state, projects, finance, tax, health, family, residence, and other Personal facts. |
| `v1.2_ai_personal_source_of_truth:workspace/context/personal/sensitive/` | private_personal | none | DO_NOT_MIGRATE | Restricted/sensitive facts and secret references are forbidden in the public destination. |
| `v1.2_ai_personal_source_of_truth:workspace/adapters/` except inherited Core readme | private_personal | none | DO_NOT_MIGRATE | Private deployment defaults, repository identity, client wrappers, and local paths/configuration. Public adapters will be built from placeholders later. |
| `v1.2_ai_personal_source_of_truth:guides/developer/migration/personal_history_inventory.md` | private_personal | none | DO_NOT_MIGRATE | Personal migration provenance and history are not public product content. |
| `v1.2_ai_personal_source_of_truth:system/release/personal_v1_readiness.md` | private_personal | none | DO_NOT_MIGRATE | Release evidence is specific to the private Personal overlay. |
| `v1.2_ai_personal_source_of_truth:system/tests/personal/` | needs_review | none in M1 | NEEDS_REVIEW | Tests encode Personal overlay behavior; reusable cases require independent sanitization. |
| `v1.2_ai_personal_source_of_truth:system/behavior/interpersonal_communication.md` and registry/catalog changes | needs_review | none in M1 | NEEDS_REVIEW | Potential generic Core feature, but it exists only on Personal and must follow Core-first promotion. |
| `v1.2_ai_personal_source_of_truth:workspace/prompts/coding/`, `knowledge/`, `language/`, `research/` | public_product | same candidate paths | GENERALIZE | Potential reusable product prompts; migrate only in a later reviewed slice after removing Personal assumptions and validating the prompt contract. |
| `v1.2_ai_personal_source_of_truth:workspace/prompts/job_search/` | needs_review | none in M1 | NEEDS_REVIEW | Useful product capability but likely coupled to Personal job-search context. |
| `v1.2_ai_personal_source_of_truth:workspace/profiles/gn_*` and `friendly_multilingual_chat.md` | public_product | same candidate paths | GENERALIZE | Potential beginner presets; each must be fact-free, deduplicated, and promoted through Core-first review. |
| `v1.2_ai_personal_source_of_truth:workspace/presentation/formats/communication_translation.md`, `tbl_multilingual.md` | public_product | same candidate paths | GENERALIZE | Potential multilingual product formats; require generic contract and test review first. |
| `v1.2_ai_personal_source_of_truth:workspace/context/personal/policies/development_conventions.md` | public_core | `system/governance/development_conventions.md` | GENERALIZE | The naming rules are repository governance, not a Personal fact; M1 records them without copying the Personal path. |
| new minimal Personal workspace | public_product | `workspace/context/personal/readme.md` | KEEP | Data-free instructions establish the user-owned destination without inventing facts or empty semantic modules. |

## Phase 0 gate

- No file from the Personal context subtree is eligible for M1.
- No Personal adapter or Personal history artifact is eligible for M1.
- Personal-only reusable candidates remain excluded until a separate Core-first classification loop.
- The M1 migration source is the exact generic Core SHA recorded above.

