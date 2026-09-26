# language_contract

## purpose

Defines language composition for AI responses without duplicating behavior, format, tone, factual context, or routing precedence.

## model

Language configuration has exactly one primary language and zero or more supporting languages:

```text
primary_language
supporting_languages[]
```

The primary language owns the main response language.

Supporting languages are ordered, additive helpers used only when the active task/profile/format calls for equivalents, translations, parallel labels, or multilingual learning support. They do not automatically duplicate the whole answer.

Concrete language modules are self-addressing under `workspace/presentation/languages/<language>.md`; this contract does not maintain a second current-language inventory.

## normalization

Rules:

- one effective primary language;
- supporting languages preserve declared order;
- duplicate supporting languages are deduplicated;
- if the primary language also appears in supporting languages, remove that duplicate from supporting;
- language identifiers use exact lowercase_snake_case names;
- no fuzzy matching or silent aliasing.

## selection_and_precedence

V1 does not add an `@lang:` runtime switch.

A direct current-prompt language request may override lower language defaults for that prompt only. It does not create persistent language configuration.

Language precedence and source authority are owned by `system/routing/precedence.md`; this contract does not duplicate that precedence chain.

Persistent/default language composition must come from an explicitly contracted profile or adapter/runtime surface.

## boundaries

```text
which language is primary/supporting
→ language

how to teach
→ system/behavior/teaching.md

vocabulary record structure
→ workspace/presentation/formats/vocab.md

professional/formal/human wording
→ tone

how much detail
→ depth
```

Language modules MUST NOT own personal facts, project facts, teaching method, formatting schema, or response depth.

## supporting_language_semantics

Supporting languages are capability/configuration, not an instruction to translate every sentence.

Examples of legitimate use:

```text
primary: german
supporting: [english, persian]
+ vocab format
→ German entry with English/Persian equivalents where the task/profile requests them

primary: persian
supporting: []
→ normal Persian response
```

These examples illustrate composition semantics; they do not define or enumerate the current language-module inventory.

## retrieval_efficiency

Only the effective language configuration and needed language modules should enter runtime presentation context.

Do not repeat the same explanation in every supporting language unless explicitly required by the active task/profile/format.

## acceptance

A compliant language configuration can deterministically identify the main response language, ordered supporting languages, prompt-local overrides, and when multilingual output is actually required without duplicating current language identities or routing precedence.
