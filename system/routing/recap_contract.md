# conversation_recap_routing

## purpose

Defines the runtime action that summarizes a bounded window of the current conversation into a compact reusable recap.

## syntax

```text
@recap:<count>
```

`count` is a positive base-10 integer. Zero, negatives, decimals, ranges, aliases, and fuzzy forms are invalid.

## selection_window

`@recap:n` selects the `n` immediately preceding completed user/assistant exchanges in the current thread. The current recap request is excluded. Progress/status updates for one request are not separate exchanges.

## history_boundary

Recap does not automatically retrieve other chats, account-wide history, memory stores, files, web sources, or canonical context.

If fewer than requested exchanges are available, summarize the accessible subset and disclose actual coverage; never imply missing history was reviewed.

## default_composition

```text
system/behavior/conversation_recap.md
format: cheatsheet → workspace/presentation/formats/cheatsheet.md
depth: short      → workspace/presentation/depth/short.md
```

Recap does not implicitly select factual context, profile, tone, or language override.

## presentation_overrides

Explicit current-prompt presentation directives outrank recap defaults. `@fmt:yaml`, `@fmt:vocab`, and `@fmt:concept` may compose normally.

## focus_body

Text after the control block is an optional focus/filter instruction and is not part of the history window.

## action_exclusivity

`@recap` is mutually exclusive with prompt actions. `@param`, `@ctx`, and `@profile` are invalid with recap. Allowed companions are presentation-only:

```text
@fmt:<name>
@no:fmt:<name>
@tone:<name>
@depth:<short|medium|deep>
```

## execution_flow

```text
parse + validate count
→ determine accessible prior exchange window
→ parse optional focus
→ load system/behavior/conversation_recap.md
→ apply workspace presentation defaults/overrides
→ extract/deduplicate/classify source-grounded signal
→ render compact recap
→ disclose incomplete coverage/conflicts when material
```

## correctness_boundary

A recap summarizes selected exchanges; it does not silently verify/correct them with external knowledge. Later explicit corrections may supersede earlier statements inside the selected window.

## token_efficiency

Select only the requested accessible window. For counts beyond reliable host history capacity, report available coverage instead of pretending completeness.
