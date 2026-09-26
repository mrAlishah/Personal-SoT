# behavior_contracts

## purpose

This directory defines reusable behavior modules: instructions for how an AI performs work.

Behavior modules are not factual context, scoped policies, presentation styles, profiles, or adapter configuration.

Read only the behavior contract or selected module needed for the current composition task.

## contract_index

```text
behavior_contract.md
→ generic behavior-module semantics, composition, conflicts, and token-efficiency rules

module_catalog.md
→ sole canonical catalog of behavior module identities and semantic responsibilities

boundary_contract.md
→ deterministic boundaries between behavior, context, policy, presentation, profile, and adapter configuration
```

Do not maintain a second canonical behavior-module list in this README. Module discovery and responsibility ownership belong to `module_catalog.md`; individual module files own their operating semantics.

## selection_model

V1 does not introduce a general `@behavior:` runtime switch.

Behavior modules are reusable components selected by a profile or another explicitly contracted composition surface. Ordinary prompt wording does not silently create persistent behavior configuration.

V1.1 `@recap:<count>` is one such explicit surface and selects `conversation_recap.md` for that request only.

## runtime_loading_guidance

Behavior modules are composable and should be loaded only when selected for the active profile/configuration/action.

Do not load all behavior modules by default merely because they exist.

## quality_and_token_rule

```text
correctness_and_quality
>
token_efficiency
```

Keep behavior instructions compact and orthogonal so clients can compose only the required operating guidance without duplicating facts, policies, or presentation instructions.
