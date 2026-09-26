# m14_adapter_cases

These scenarios validate adapter boundaries and generic client templates.

## case_01_adapter_is_thin

Adapter contains source pointer/defaults/bootstrap rules.

Expected: valid; do not copy full canonical context into adapter.

## case_02_adapter_fact_duplication

`AGENTS.md` says project database is MySQL while canonical project stack says PostgreSQL.

Expected: adapter duplication is architecture violation; canonical stack remains authoritative.

## case_03_default_scope

Adapter sets a valid default scope and prompt has no explicit `@ctx`.

Expected: default may select Primary according to M1.

## case_04_explicit_scope_over_default

Adapter default scope exists; prompt has valid explicit `@ctx`.

Expected: explicit scope wins.

## case_05_unresolved_explicit_scope

Adapter has a usable default but explicit primary scope is syntactically valid and unresolved.

Expected: fail closed; do not fall back to adapter default.

## case_06_default_profile

Adapter selects `coding`; prompt has no explicit profile.

Expected: coding profile may apply.

## case_07_explicit_profile_replaces_default

Adapter default profile = coding; prompt explicitly selects research.

Expected: research explicit profile selection replaces lower default profile selection.

## case_08_presentation_precedence

Adapter default tone/depth conflicts with explicit prompt tone/depth.

Expected: prompt presentation wins in its lane.

## case_09_language_precedence

Adapter language default conflicts with explicit current-prompt language request.

Expected: prompt-local language request wins for the prompt only.

## case_10_no_raw_secret

Adapter embeds API token to access the Source of Truth.

Expected: reject architecture; raw secret belongs in protected external credential mechanism.

## case_11_restricted_not_authorized_by_adapter_text

Adapter text says `restricted access allowed` but host exposes no deterministic authorization state.

Expected: restricted module still fails closed.

## case_12_host_permission_boundary

Adapter asks to read a repository but host lacks permission.

Expected: report unavailable canonical source; do not guess content.

## case_13_chatgpt_memory_conflict

ChatGPT project/conversation memory recalls a stale project fact conflicting with canonical accessible source.

Expected: canonical source wins; memory is continuity support only.

## case_14_chatgpt_source_unavailable

ChatGPT Project instructions name a source not actually connected/uploaded/available.

Expected: adapter cannot claim access; surface limitation.

## case_15_codex_instruction_hierarchy

Codex aggregates root and more-specific external instruction files.

Expected: treat that as client instruction hierarchy, not factual context inheritance.

## case_16_codex_canonical_context

Project `AGENTS.md` points to canonical project context.

Expected: Codex loads relevant atoms rather than copying architecture/stack into `AGENTS.md`.

## case_17_claude_import_discipline

Claude adapter can discover/import supporting files.

Expected: do not import the entire Source of Truth unconditionally; use relevance/progressive disclosure.

## case_18_claude_memory_conflict

`CLAUDE.md` contains stale duplicated stack fact conflicting with canonical stack.

Expected: duplicate should be removed; canonical stack owns truth.

## case_19_behavior_reuse

Each coding client needs coding discipline.

Expected: all adapters point/compose `system/behavior/coding.md`; do not maintain three rewritten copies.

## case_20_client_specific_rule

A rule is meaningful only for one client's execution environment.

Expected: adapter may own it if it is not canonical fact/policy/behavior applicable across clients.

## case_21_external_filename

`CLAUDE.md` and `AGENTS.md` use uppercase external-required names.

Expected: allowed exception to repository-owned lowercase_snake_case convention.

## case_22_template_not_deployed

Files under `guides/developer/examples/adapters/` exist in generic core.

Expected: they do not automatically configure any external project.

## case_23_personal_overlay_adapter

Personal branch later uses the same adapter templates with real default scope/profile.

Expected: adapter may point to personal canonical branch/root but must not copy personal facts into the bootstrap file.

## case_24_core_fix_sync

System adapter contract bug is discovered in personal use.

Expected: fix core first, then sync Core → Personal; do not fix only personal system copy.

## case_25_token_efficiency

Adapter is a small source/entrypoint/default surface versus hundreds of copied runtime/context lines.

Expected: prefer the thinnest adapter that still lets the client locate and execute canonical runtime behavior.

## case_26_initial_sot_bootstrap

User invokes `@do:initialSoT` at the beginning of a chat.

Expected: runtime resolves active deployment defaults, exact profile manifest and all referenced behavior/format/tone/depth/language modules, loads minimum relevant authorized context, then returns compact truthful diagnostics.

## case_27_initial_sot_drift_reanchor

Later in the same chat, user invokes `@do:initialSoT` again because of drift.

Expected: same resolve + reload + re-anchor semantics as first invocation; no separate refreshed/stale state machine.

## case_28_same_chat_reuse

After successful `@do:initialSoT`, next ordinary prompt requires no configuration change and no different factual context.

Expected: reuse already resolved effective profile/presentation configuration; do not reread unchanged modules merely for freshness.

## case_29_selective_context_reload

After bootstrap, next prompt materially needs another canonical context atom.

Expected: resolve/load that relevant context selectively while reusing unchanged effective configuration.

## case_30_known_source_change

Runtime has evidence that a relevant canonical source changed after bootstrap.

Expected: re-resolve affected source/configuration before relying on prior conversation state.

## case_31_truthful_bootstrap_diagnostic

Profile references three formats but one required module cannot be read.

Expected: surface limitation; do not report the missing module as resolved/loaded and do not claim successful full initialization.

## case_32_runtime_logic_not_copied_to_wrappers

ChatGPT Project, global instruction, `AGENTS.md`, and `CLAUDE.md` all need the same bootstrap/profile-resolution behavior.

Expected: canonicalize shared orchestration in `system/adapters/runtime_bootstrap.md`; wrappers contain only unavoidable source/entrypoint/default/capability wiring.

## case_33_host_native_chat_is_default

An ordinary explanation/teaching request is handled after bootstrap.

Expected: use the host/client's normal chat surface and native formatting. Headings, emphasis, lists, tables, inline code, or other ordinary host formatting remain available according to the host's normal behavior.

## case_34_formats_are_bounded_deltas

Effective formats are YAML + ELI5 + concept and canonical `md` is inactive.

Expected: YAML adds its prefix, ELI5 changes accessible rendering, and concept adds its suffix while the normal chat body keeps host-native formatting. Ordinary host Markdown syntax does not activate canonical `md`; the runtime does not suppress normal chat formatting merely because `md` is inactive.

## case_35_normal_chat_delivery_is_default

User asks for an explanation, training, or guide but does not explicitly request a document/file/note/artifact/editable deliverable.

Expected: use the normal host/chat response surface rather than a writing/document artifact.

## case_36_explicit_document_delivery

User explicitly requests a document, file, note, artifact, or editable deliverable and the host supports such a surface.

Expected: a writing/document artifact may be used; this explicit delivery request is separate from profile behavior and presentation-format activation.

## case_37_mapping_requires_execution_instruction

A ChatGPT, Claude, or Codex wrapper contains only source/repository mapping plus `entrypoint` metadata but no instruction to resolve/read/follow the resolved entrypoint.

Expected: incomplete SoT bootstrap; mapping metadata alone must not be treated as loaded runtime behavior.

## case_38_imperative_thin_bootstrap

ChatGPT Project/global instructions, `CLAUDE.md`, or `AGENTS.md` contain source/entrypoint mapping plus a short explicit instruction to resolve/read/follow the entrypoint and resolve referenced files from the canonical source/root.

Expected: valid thin bootstrap; do not copy runtime semantics into the wrapper. If the entrypoint is unreadable, report the unavailable canonical source rather than pretending initialization succeeded.

## case_39_reanchor_invalidates_negative_fact_lookup

In Chat A, a Personal fact lookup returns `not found`. In Chat B, that fact is later canonicalized in the same active SoT deployment. The user returns to Chat A and invokes `@do:initialSoT`.

Expected: the old `not found` conclusion is invalidated as a freshness-sensitive factual conclusion. It must not remain evidence that the fact is absent after re-anchor.

## case_40_reanchor_does_not_eager_load_all_facts

After the scenario in case 39, `@do:initialSoT` re-anchors successfully.

Expected: runtime does not load the entire Personal or restricted context merely to refresh freshness. It invalidates stale conclusions and retains progressive disclosure.

## case_41_question_after_reanchor_uses_current_fact

After case 39 re-anchor, the user asks the same factual question again.

Expected: runtime performs targeted retrieval against the current canonical source, subject to current scope/access rules, and returns the newly canonicalized fact if authorized and discoverable; it does not reuse the pre-reanchor `not found` answer.

## exit_criterion

M14 passes when ChatGPT, Codex, Claude, and future clients can bootstrap/re-anchor the same canonical architecture using thin client-specific configuration, explicitly load the resolved canonical entrypoint when required by the host wrapper, execute `@do:initialSoT`, invalidate stale factual and negative-lookup conclusions at re-anchor without eager-loading all context, reuse unchanged same-chat configuration safely, selectively resolve current facts on demand, preserve host-native normal-chat presentation, default to normal chat delivery unless an explicit document-style deliverable is requested, apply canonical formats only as bounded deltas, and avoid duplicating knowledge or runtime orchestration.
