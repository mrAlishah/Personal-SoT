# project_charter_cases

These scenarios validate `system/governance/project_charter.md` as the canonical project-purpose, priority, and structural-maintainability contract.

## case_01_priority_order_preserves_mandatory_boundaries

A lower-cost or simpler design would weaken required authorization, safety, or correctness.

Expected: reject the optimization; mandatory boundaries and correctness outrank ownership/cohesion, retrieval/context efficiency, and convenience.

## case_02_single_owner_over_duplicate_state

A new feature can either duplicate the same durable rule/fact/current inventory in several modules or introduce/reference one clear semantic owner.

Expected: prefer one semantic owner with composition/reference unless independent ownership/lifecycle genuinely requires separate atoms.

## case_03_minimum_necessary_semantic_boundaries

Several tightly related facts/rules share retrieval, lifecycle, privacy, and ownership.

Expected: keep them cohesive; do not split merely to maximize atomicity or file count. Conversely, split when the boundary materially reduces coupling or has independent lifecycle/retrieval/privacy value.

## case_04_progressive_disclosure_over_eager_loading

Two correct retrieval designs exist: one loads an entire scope and another resolves a small relevant atom through registry/path-first lookup.

Expected: prefer targeted progressive disclosure.

## case_05_context_cost_is_efficiency_evidence_not_independent_authority

Two solutions preserve mandatory boundaries, correctness, ownership, cohesion, and validation equally, but one duplicates large prose/state and consumes substantially more context.

Expected: prefer the lower measured retrieval/context-cost design as an efficiency improvement. Do not sacrifice higher priorities merely to minimize tokens.

## case_06_current_state_not_full_history

A current-state owner can either contain a compact effective summary or duplicate an entire historical evidence stream.

Expected: keep the compact current state and retain history only in its history-oriented owner.

## case_07_client_specific_constraint_stays_in_adapter

A Claude- or ChatGPT-specific limitation can be handled in an adapter without changing canonical cross-client semantics.

Expected: keep the workaround in the adapter/deployment boundary.

## case_08_smallest_coherent_root_cause_patch

A requested change can be implemented with a focused root-cause patch or a broad unrelated refactor/rewrite.

Expected: choose the smallest coherent root-cause patch unless the broader change materially improves a higher-priority charter concern and is justified.

## case_09_material_system_change_reads_charter

A task changes SoT routing, context ownership, access, adapters, profiles, prompts, retrieval, governance, or structural boundaries.

Expected: evaluate the material design choice against `system/governance/project_charter.md` before accepting the implementation.

## case_10_validation_truthfulness

A change is merged but no executable validator was run.

Expected: report merge/inspection accurately and do not call the result validator-passed.

## case_11_change_fan_out_must_be_inherent_or_reduced

Adding one registry-covered identity requires edits to several generic consumers only because each repeats the current inventory.

Expected: classify this as unnecessary change fan-out and move current inventory ownership back to the registry/canonical target. Keep multi-file changes only when each file owns genuinely distinct semantics.

## case_12_indirection_requires_boundary_value

Two layers can be collapsed, but they have separate lifecycle/ownership/capability responsibilities and merging them would increase coupling.

Expected: retain the boundary. File-count reduction is not evidence of improved maintainability.

A forwarding layer with no independent lifecycle, semantic responsibility, capability boundary, or measurable coupling benefit should instead be considered unnecessary indirection.

## case_13_maintainability_definition_of_done

A stabilization release claims structural completion.

Expected: evidence supports clear semantic ownership, no known material semantic duplication/hidden coupling/unnecessary indirection/stale logic, bounded or justified change fan-out, acceptable cohesion, controlled special cases, validated critical boundaries, and bounded future change cost.
