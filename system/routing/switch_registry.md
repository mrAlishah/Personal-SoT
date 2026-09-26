# switch_registry

## purpose

Compact registry of canonical runtime-selectable identifiers whose identities require explicit name-to-module mapping.

The registry validates names and points to canonical modules. It does not copy module contents.

Physical paths follow `system/layout_contract.md`; runtime switch names remain unchanged.

Profiles are intentionally not enumerated here. Their runtime identity is the exact filename under `workspace/profiles/` as defined by `system/profiles/profile_contract.md`.

## formats

```text
yaml                 → workspace/presentation/formats/yaml.md
md                   → workspace/presentation/formats/md.md
eli5                 → workspace/presentation/formats/eli5.md
vocab                → workspace/presentation/formats/vocab.md
concept              → workspace/presentation/formats/concept.md
mental_picture       → workspace/presentation/formats/mental_picture.md
learning_summary     → workspace/presentation/formats/learning_summary.md
comparison_table     → workspace/presentation/formats/comparison_table.md
cheatsheet           → workspace/presentation/formats/cheatsheet.md
language_correction  → workspace/presentation/formats/language_correction.md
```

## tones

```text
human         → workspace/presentation/tones/human.md
formal        → workspace/presentation/tones/formal.md
professional  → workspace/presentation/tones/professional.md
neutral       → workspace/presentation/tones/neutral.md
```

## depths

```text
summary → workspace/presentation/depth/summary.md
short   → workspace/presentation/depth/short.md
medium  → workspace/presentation/depth/medium.md
deep    → workspace/presentation/depth/deep.md
```

`summary` is an explicit operationally compressed depth. Its prompt-local interaction with `controls.learning` is defined by `workspace/presentation/depth/summary.md` and `system/routing/precedence.md`.

## registered_controls

Registered runtime-control identities are canonical configuration keys and resolve to their canonical contracts.

```text
clarify_risk    → system/behavior/clarify_risk.md
learning        → system/behavior/learning.md
step_execution  → system/behavior/step_execution.md
```

The shared control model is defined by:

```text
system/behavior/control_contract.md
```

Public prompt syntax uses the generic registered-control directive:

```text
@control:<registered_control>=<allowed_value>
```

Examples:

```text
@control:clarify_risk=auto
@control:learning=off
@control:step_execution=on
```

Control identities are repository-owned lowercase_snake_case identifiers. Values are exact and validated by the target control contract.

## dynamic_path_actions

Prompt templates are not listed here. Prompt identity remains relative to the prompt workspace:

```text
@do:prompt:<path>
@edit:prompt:<path>
@delete:prompt:<path>
@confirm:delete:prompt:<path>

→ workspace/prompts/<path>.md
```

`@param` names are validated against the selected prompt manifest, not this registry.

Creating a flat prompt registry would duplicate dynamic prompt paths and is intentionally forbidden.

## grammar_actions

```text
@recap:<positive_integer>
→ system/routing/recap_contract.md
→ system/behavior/conversation_recap.md
→ default format cheatsheet
```

The numeric recap value is grammar-validated, not enumerated in this registry.

## non_registry_modules

Profiles resolve dynamically by exact filename:

```text
@profile:<name>
→ workspace/profiles/<name>.md
```

Behavior modules have no general `@behavior:` namespace. Language modules have no `@lang:` namespace. Context paths resolve through scope grammar plus `system/routing/context_registry.md`.

## rules

- identifiers are exact and case-sensitive;
- repository-owned identifiers use lowercase_snake_case;
- no aliases, fuzzy matching, camelCase, or kebab-case normalization is performed;
- each registry entry points to one canonical target;
- removing/renaming a registry-covered selectable target requires coherent registry update;
- registry presence does not override precedence or target-layer contracts;
- profile and prompt identities remain outside this flat registry by design.
