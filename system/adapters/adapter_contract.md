# adapter_contract

## purpose

Defines how an AI client/runtime bootstraps and consumes the canonical Source of Truth without duplicating canonical knowledge or prompt templates into client-specific instruction surfaces.

## core_rule

```text
adapter
= thin bootstrap + runtime defaults + capability wiring

adapter
≠ canonical knowledge store
adapter
≠ prompt-template store
adapter
≠ duplicated runtime orchestration
```

Reusable conversational bootstrap/re-anchor behavior is canonical in `system/adapters/runtime_bootstrap.md`. Provider-neutral local/connector source binding, capability, freshness, provenance, and failure semantics are canonical in `system/adapters/source_access_contract.md`.

Connector-backed source access follows `system/connectors/source_contract.md`.
The adapter binds real host capabilities and trusted source/authorization
configuration; the connector transports bytes and creates no canonical authority.
Use `system/connectors/readme.md` for the host-side gate integration.

## canonical_adapter_fields

An adapter may configure values such as:

```text
source_root
default_scope
default_profile
default_tone
default_depth
language_defaults
start_language
controls
repository_mapping
runtime_entrypoint
client_specific_bootstrap
```

`controls` is a bounded map of registered runtime controls, not an arbitrary configuration bag. Discover registered control identities through `system/routing/switch_registry.md` and validate each configured value against the canonical target metadata defined by `system/behavior/control_contract.md`. This adapter contract does not maintain a second current-control inventory or allowed-value table.

Only configure a field when the client/runtime actually needs it. Avoid adapter-level values that merely duplicate a selected profile default, because adapter/project configuration has higher precedence and can unintentionally mask profile-specific composition.

## bootstrap_sequence

Conceptually:

```text
1. resolve one authorized canonical Source-of-Truth binding through `system/adapters/source_access_contract.md`, including actual host capability and current revision/version evidence when available
2. load minimal runtime/routing/discovery contracts needed for the task
3. parse explicit leading control block
4. if @do:sot: execute system/adapters/runtime_bootstrap.md and return its compact diagnostic
5. otherwise resolve the effective configuration from applicable adapter/project defaults, reusable same-chat configuration when still applicable, prompt/session overrides, selected profile defaults, registered-control defaults, and explicit directives
6. if an effective profile is selected, read its exact manifest and resolve/apply every referenced behavior, format, tone, depth, language module, and registered control value required by the effective configuration
7. resolve registered runtime-control contracts required by the effective configuration
8. identify at most one high-level action
9. if Prompt Library action: resolve only that prompt template + applicable parameters/defaults
10. if recap action: resolve only the requested accessible current-thread exchange window
11. resolve factual scope only for action types that permit context composition
12. validate module access before relevance
13. load minimum sufficient authoritative atoms/contracts
14. execute/render/recap/maintain according to the fully resolved effective configuration and selected action
15. preserve source/module provenance and truthful capability/coverage limitations where useful
```

Profile manifests are executable configuration, not descriptive metadata. A runtime must not claim a profile is active while silently omitting referenced behavior, presentation, or registered-control configuration. If a required selected module/control contract cannot be read or resolved, surface the limitation/configuration error instead of approximating or dropping it.

## sot_action

Adapters supporting conversational runtime bootstrapping must recognize the reserved parameterless action:

```text
@do:sot
```

Its semantics are defined only by `system/adapters/runtime_bootstrap.md`. Client/project wrappers must not maintain rewritten copies of that sequence.

Every invocation performs the same resolve + reload + re-anchor operation. It is intentionally usable both at chat start and after drift; no persistent initialized/refreshed/stale state machine is required.

## same_chat_reuse

When the host exposes the same conversation context, a successful bootstrap/re-anchor may establish an effective chat basis that subsequent ordinary requests reuse while it remains applicable.

Reuse unchanged profile/presentation/control resolution instead of re-reading the same modules on every turn merely for freshness. Resolve additional factual context selectively when the new request materially requires it.

Re-resolve when explicit directives/configuration change, relevant canonical source is known to have changed, previous resolution is unavailable/uncertain, or `@do:sot` is invoked again.

This is an optimization only: canonical current source still outranks stale conversation state.

## prompt_library

Adapters may support canonical actions:

```text
@do:prompt:<path>
@edit:prompt:<path>
@delete:prompt:<path>
@confirm:delete:prompt:<path>
@param:<name>=[value]
```

Exact prompt path resolution points to `workspace/prompts/<path>.md`.

Adapters must not maintain a copied prompt registry or paste prompt bodies into project instructions.

### read_capability

A client with authorized read access may resolve/render prompt files. `@edit` is possible when it can read the selected prompt. `@do` additionally requires whatever capabilities the rendered task itself needs.

### write_capability

Prompt deletion/repair requires real authorized repository/filesystem write capability. If unavailable, the adapter may produce the deletion plan but must state that it cannot apply it.

`@delete` never implies write authorization. `@confirm:delete` confirms user intent but still does not bypass host/tool permissions or Git governance.

### composer_boundary

The client-neutral contract does not promise pre-send insertion into a chat composer.

Universal behavior:

```text
@edit
→ render prompt preview in assistant output
→ user edits/copies
→ user sends final request
```

A client-specific UI/local helper may later insert rendered text into an editor/composer, but that is optional adapter UX, not canonical prompt semantics.

## conversation_recap

Adapters may support:

```text
@recap:<positive_integer>
```

Recap history is a host capability, not repository knowledge.

A compliant adapter/runtime should:

- use only the requested immediately preceding completed exchanges in the current thread;
- exclude the current recap request from that source window;
- treat transient progress updates as part of their logical exchange rather than separate count items;
- disclose actual coverage when fewer exchanges are accessible than requested;
- never claim review of inaccessible history;
- never reach into other chats/account history merely to satisfy the count;
- apply the source-grounded semantics in `system/routing/recap_contract.md` and `system/behavior/conversation_recap.md`.

If the client does not expose enough current-thread history, report the limitation rather than substituting memory, canonical context, web research, or guessed content.

`@recap` does not grant repository, context, or restricted-data access.

## default_scope

`default_scope` is runtime configuration, not ownership. Explicit valid `@ctx` remains higher priority for action types where context is valid.

Prompt templates do not set factual scope in V1.1. `@ctx` is invalid with `@recap` in V1.1.

## default_profile

`default_profile` is a fallback selection. Prompt-manifest profile defaults may sit above adapter fallback, while explicit invocation profiles remain highest in the prompt-template lane.

Selecting a default profile requires full profile composition exactly like explicit profile selection: read the manifest, resolve referenced modules and registered control values, and apply the resulting effective configuration. Adapters must not treat `default_profile` as a label-only hint.

Profiles do not compose into `@recap` in V1.1.

## runtime_controls

Project/adapter configuration may override any registered control through the bounded `controls:` map using exact registry identities and values accepted by each canonical target.

Control precedence is owned only by the runtime-control lane in `system/routing/precedence.md`; this adapter contract does not repeat that precedence chain.

The adapter must not duplicate control behavior text. It supplies only configured values and resolves canonical registered-control contracts.

A client may expose a same-chat/session override if the host has a real session-configuration mechanism. Do not invent persistent session state when the host cannot support it.

## presentation_defaults

Adapter direct defaults remain inside their contracted precedence lanes and do not override explicit invocation, prompt-manifest, or recap-action values where V1.1 precedence assigns higher authority.

`start_language` is an adapter/project response-opening default governed by `system/presentation/start_language.md`; it remains independent from overall response language, tone, depth, and format selection.

Host/UI Markdown used for ordinary readability is not itself activation of canonical `md`; presentation must follow `system/presentation/formats/format_contract.md`.

## source_access

Local filesystems, repository connectors, project sources, apps, and equivalent host mechanisms are transport/capability surfaces. They follow `system/adapters/source_access_contract.md` and do not create a second authority model.

A mapped source is not considered loaded until it is actually resolved and its canonical entrypoint can be read. If the source is unavailable, unauthorized, ambiguous, or only partially accessible, report that limitation rather than substituting conversation memory or another source.

Connector-backed search/list operations must not expose protected snippets before canonical access can be evaluated. Adapters should request the minimum source operations needed by canonical path/scope/module retrieval.

## sensitive_context

An adapter may participate in deterministic authorization for `ai_access: restricted` only when the host exposes a real authorization boundary.

Prompt actions/parameters and recap actions never grant restricted-data authorization.

Adapters must never embed raw secrets into prompt files or bootstrap instructions.

## external_instruction_files

Client-specific surfaces such as ChatGPT global/project instructions, `CLAUDE.md`, and `AGENTS.md` remain minimum deployment pointers/configuration surfaces.

A wrapper should contain only information the client genuinely needs before it can locate the authorized SoT/runtime entrypoint, plus unavoidable client/project defaults or capability boundaries. If a reusable rule can be expressed canonically in the SoT and resolved through the entrypoint, it should not be repeated in wrappers.

## token_efficiency

Adapter entrypoints and external wrappers should be short. Put repeated execution semantics in canonical shared contracts/runtime bootstrap, not client wrappers. Prefer same-chat reuse of unchanged effective configuration, exact profile/prompt-path lookup, bounded recap-history selection, and selective module/context loading over repeated full retrieval.

## portability

Prompt templates remain client-neutral Markdown. Recap semantics remain client-neutral but actual available history depth depends on the host/client capability.

A new AI client should normally need only minimal wiring for source location, runtime entrypoint, authorized source/file/action/history capabilities, and genuine defaults—not rewritten canonical contracts. A connector-backed client translates provider operations into the source-access contract rather than introducing client-specific authority or retrieval semantics.

## acceptance

A compliant adapter can locate the canonical runtime through a thin external surface, execute parameterless `@do:sot`, resolve effective defaults and explicit overrides including registered runtime controls, fully compose selected profiles and their referenced modules, reuse unchanged same-chat configuration when safe, selectively reload context, preserve format boundaries, resolve exact prompt actions when capabilities permit, preserve render-vs-execute-vs-delete semantics, select bounded recap history without inventing unavailable exchanges, keep context authority independent, and fail clearly when source/module/write/tool/history capabilities are unavailable.
