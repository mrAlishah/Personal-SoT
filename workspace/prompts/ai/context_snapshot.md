---
prompt_status: active
prompt_tags:
  - ai
  - conversation
  - context_snapshot
  - handoff
  - continuity
prompt_profiles: []
prompt_formats:
  - md
prompt_tone: professional
prompt_depth: medium
required_params: []
optional_params:
  - focus
owned_assets: []
---
Create a self-contained context snapshot of the current conversation that can be pasted as the first message in a new chat so work can continue without rereading the original thread.

Optional emphasis:

{{focus}}

Use only conversation context that is actually available to the active client. Do not silently enrich the snapshot with web research, other chats, hidden memory, or unrelated canonical facts.

The snapshot must preserve continuity, not reproduce the whole transcript. Compress aggressively while retaining every detail that materially affects correct continuation.

Prefer the latest effective state. When later messages corrected, replaced, or invalidated earlier information, keep the corrected/current version. Mention superseded state only when it is necessary to understand a migration, conflict, or warning.

Include the following sections only when supported by the conversation:

1. Current goal / task
   - what the user is trying to achieve now;
   - the immediate scope and success criteria.

2. Active user instructions and working conventions
   - response style, tone, language, formatting, control syntax, naming rules, workflow preferences, and explicit constraints that remain active;
   - preserve exact custom directives or invocation syntax when they matter.

3. Current architecture / mental model
   - important definitions, boundaries, ownership rules, precedence, invariants, or agreed terminology required to continue correctly.

4. Latest effective decisions
   - decisions already made;
   - rejected alternatives only when they explain a current constraint;
   - distinguish decided, proposed, and unresolved items.

5. Current implementation / operational state
   - what has been completed;
   - what is partially complete;
   - what has not been done;
   - exact branch/ref/state relationships where relevant.

6. Important exact literals
   - commands, flags, file paths, filenames, repository names, branch names, commit SHAs, URLs when necessary, configuration keys, versions, identifiers, parameter syntax, exact values, and other literals whose spelling/case must be preserved.

7. Errors, fixes, and corrections
   - meaningful failures encountered;
   - confirmed fixes;
   - known temporary workarounds or hygiene issues that affect future work.

8. Open items / risks
   - unresolved questions, validation still required, known limitations, assumptions, or decisions intentionally deferred.

9. Continue from here
   - the smallest concrete next step a new chat should take;
   - include commands or files to inspect first when applicable.

Formatting requirements:

- Output one paste-ready Markdown document beginning with `# Context Snapshot`.
- Make it self-contained: do not rely on phrases such as "as discussed above" or "see previous messages".
- Use compact headings, bullets, tables, or code blocks only when they improve scanability.
- Preserve the original conversation's active formatting conventions and custom syntax when those conventions are part of the working contract.
- Preserve exact spelling/case of code, paths, commands, branch names, SHAs, identifiers, switches, and parameter syntax.
- Clearly separate facts/current state from proposals and unresolved items.
- Do not include conversational filler, repeated explanations, obsolete intermediate drafts, or examples that do not help continuation.

Safety and privacy:

- Never copy raw secrets, passwords, API tokens, private keys, session cookies, recovery codes, one-time authentication codes, or credentials into the snapshot.
- If such material is relevant to continuity, replace the value with a clear placeholder such as `[SECRET OMITTED]` and preserve only the non-secret reference/context needed.
- Include sensitive personal information only when it is materially required to continue the active task; keep it minimal and clearly scoped.

If conversation history appears incomplete or truncated, state that limitation in the snapshot rather than pretending coverage is complete.

The final output should be suitable for direct paste into a new AI chat as continuation context.