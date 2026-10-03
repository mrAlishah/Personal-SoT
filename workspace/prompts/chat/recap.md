---
prompt_status: active
prompt_tags:
  - ai
  - conversation
  - recap
  - summary
  - quick_reference
prompt_profiles: []
prompt_formats:
  - cheatsheet
prompt_tone: professional
prompt_depth: short
required_params:
  - count
optional_params:
  - focus
owned_assets: []
---
Create a compact, active-use recap of the last {{count}} completed user/assistant exchanges immediately preceding this invocation in the current conversation.

Optional focus:

{{focus}}

Treat one exchange as one user prompt plus its assistant answer. Exclude this recap invocation itself.

`count` must be a positive base-10 integer. If `{{count}}` is zero, negative, fractional, non-numeric, or otherwise invalid, fail closed with a concise parameter error instead of guessing a history window.

Use only the selected current-thread conversation history that is actually available to the active client. Do not silently add facts from other chats, canonical context, web research, memory, or general knowledge merely to improve the recap.

If fewer than {{count}} complete exchanges are available, state the actual coverage concisely before the recap.

Compression rules:

1. Keep the latest effective correction when a later exchange supersedes an earlier one.
2. If a contradiction remains unresolved, show it briefly instead of inventing a winner.
3. Deduplicate repeated explanations and examples.
4. Preserve exact commands, flags, paths, filenames, identifiers, values, versions, and important caveats needed for active use.
5. For Bash/Git/CLI material, show the exact command, one-line purpose, and concise argument/switch meaning when useful.
6. For technical learning, group the important concepts in a compact learning order and show key relationships or distinctions.
7. For language learning/translation, group useful sentences, translations, phrases, and high-value vocabulary cleanly.
8. For decisions/configuration, keep only the effective final decision or setting unless the superseded state is needed to avoid confusion.
9. For errors/fixes, pair the symptom with the confirmed/effective fix where the source supports it.
10. For mixed content, organize by meaningful categories and omit empty categories.
11. Prefer scan-first density over narrative explanation. Do not recreate the original long answers.
12. Preserve uncertainty and source limitations when they materially affect correctness.

The result should function as a practical quick-reference sheet for remembering and reusing the selected exchanges.