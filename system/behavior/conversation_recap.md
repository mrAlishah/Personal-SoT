# conversation_recap

## purpose

Condense a selected window of prior conversation exchanges into a high-signal reusable digest for review and active use.

This behavior is selected by `@recap:<count>`; there is no general `@behavior:` namespace.

## source_boundary

Selected prior exchanges are recap evidence. Canonical context, web, memory, and model knowledge are not silently added. External verification/expansion must be clearly separate when explicitly requested.

## exchange_model

One completed exchange is one user request plus its assistant answer. Non-substantive progress/status updates do not count separately.

## extraction

Retain commands, exact values/settings, decisions, translations, reusable phrases, important concepts, fixes, and actionable next steps. Remove filler, duplicated rationale/examples, and conversational scaffolding. Prefer final usable state over chronology while preserving caveats required for correct reuse.

## domain_adaptation

Use only categories supported by the selected exchanges, such as commands/operations, concepts, language phrases/translations, decisions/settings, errors/fixes, reusable prompt invocations, and next actions. Do not force empty categories.

Commands preserve exact literals and source-supported switch meanings. Concepts use compact learning/dependency order when supported. Language content groups useful phrases/translations/corrections. Decisions keep effective final state. Errors pair symptom with supported effective fix.

## corrections_and_conflicts

Later explicit correction may replace earlier conversation state in the recap. Unresolved material conflicts are surfaced briefly; recency alone is not proof of external truth.

## compression_rule

```text
high-value operational/learning signal
>
explanatory completeness
>
conversation chronology
```

## focus_instruction

A body supplied with `@recap:<count>` narrows focus but cannot fabricate absent material.

## presentation_boundary

This behavior owns extraction/compression, not visual representation/tone/language/depth. Default scan-first rendering is owned by:

```text
workspace/presentation/formats/cheatsheet.md
```

## access_and_capability_boundary

Summarize only history actually exposed by the active client. Do not search other conversations/memory/files/external sources merely to satisfy count.

## token_efficiency

Read only the requested accessible history window and minimum required system/presentation modules.
