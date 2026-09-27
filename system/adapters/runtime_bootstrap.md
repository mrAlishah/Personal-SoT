# runtime_bootstrap

## purpose

Defines the canonical reusable bootstrap/re-anchor behavior for conversational AI clients so external instruction surfaces can remain thin.

## core_rule

```text
external wrapper
→ locate authorized SoT + select this entrypoint/deployment bootstrap
→ canonical runtime resolves everything else
```

Reusable execution semantics belong here or in referenced `system/` contracts, not copied into ChatGPT Project instructions, global instructions, `AGENTS.md`, `CLAUDE.md`, or similar client surfaces.

## sot_action

The reserved runtime action is:

```text
@do:sot
```

It accepts no parameters and needs no ordinary prompt body.

Every invocation has the same semantics, whether used at chat start or later to recover from conversation drift:

```text
resolve + reload + re-anchor current chat
```

Do not introduce an initialized/refreshed/stale state machine for this action.

A re-anchor is also a freshness boundary for factual conclusions derived from the canonical SoT. Conversation-local conclusions whose freshness is not guaranteed must not survive the boundary as canonical evidence.

## execution

On `@do:sot`:

1. re-resolve one authorized canonical SoT source binding according to `system/adapters/source_access_contract.md`, including current host capability and revision/version evidence when available;
2. read the minimum current shared runtime/routing contracts required to resolve the invocation;
3. resolve effective context/default scope;
4. resolve effective profile selection;
5. read each selected profile manifest exactly;
6. resolve and apply every referenced behavior, format, tone, depth, language module, and registered profile control value, plus applicable project/adapter `start_language` and `controls` configuration;
7. resolve each effective registered control through `system/behavior/control_contract.md`, `system/routing/switch_registry.md`, and its canonical target contract, including global defaults when no higher source sets the control;
8. apply any behavior activation, suppression, or adaptive gating required by effective control values, including making `teaching` effective for `controls.learning = on`, suppressing optional profile-selected teaching for `controls.learning = off`, and adaptively gating it for `controls.learning = auto`;
9. validate access before factual context loading;
10. invalidate prior conversation-local factual conclusions that cannot be proven fresh against the current canonical source, including prior negative/not-found lookups; do not treat a pre-reanchor conclusion that a fact was absent as evidence that it is still absent;
11. load only the minimum relevant canonical context needed to establish the current chat basis;
12. make that resolved configuration/context available as the effective basis for subsequent requests in the same accessible conversation;
13. return a compact diagnostic describing what was actually resolved/loaded.

Invalidation does not require eagerly loading all factual context. After re-anchor, factual questions should resolve the needed atom from the current canonical source on demand using normal targeted retrieval.

The current registered-control set is discovered from `system/routing/switch_registry.md`. Each registered target owns its `control_id`, allowed values, global default, and behavior semantics according to `system/behavior/control_contract.md`; this bootstrap does not maintain a second control inventory or default table.

If a required source/module/control contract cannot be read, fail visibly instead of claiming successful initialization.

## chat_presentation

For ordinary conversational responses, use the host/client's normal chat surface and native formatting.

Canonical presentation formats are deltas over that baseline: each selected format adds or changes only the structure, placement, or representation it explicitly owns. They do not suppress or replace normal host formatting outside those boundaries.

Ordinary host Markdown syntax used for chat readability does not by itself activate canonical `md`; canonical `md` remains the explicit format for a deliberate Markdown-document body.

Response-opening language, when configured, follows `system/presentation/start_language.md` and remains separate from the ordinary response-language lane and from text direction.

## delivery_surface

Use the normal host/chat response surface by default.

Use a writing/document artifact only when the user explicitly requests a document, file, note, artifact, or editable deliverable.

## diagnostic

The result should expose the effective basis without dumping canonical file contents. Report applicable values such as:

```text
source
source_ref
source_revision
source_capabilities
ctx
profile
behaviors
formats
tone
depth
language
start_language
controls
loaded_context
resolved_modules
warnings
```

Rules:

- report only values/modules/files/capabilities actually resolved or loaded;
- report source revision/version only when the host actually exposes it;
- omit empty optional sections when that improves clarity;
- identify actual canonical context files/atoms loaded when available;
- never fabricate provenance merely because a profile or scope would normally imply it;
- keep the diagnostic compact and operational, not a second copy of the source.

## same_chat_reuse

After successful bootstrap/re-anchor, subsequent ordinary requests in the same accessible conversation should reuse the already resolved effective configuration when it remains applicable.

Do not reload unchanged profile/presentation/control modules on every turn merely for freshness. Selectively resolve additional factual context when the new request materially requires it.

Reuse of resolved configuration must not be confused with reuse of stale factual conclusions. After `@do:sot`, a prior factual value or prior `not found` result may be reused only when its freshness against the current canonical source is actually established. Otherwise perform a targeted current lookup when the fact is needed.

Re-resolve/reload when:

- the resolved source mapping/ref/revision changes or cannot be proven current for a freshness-sensitive fact;

- an explicit runtime directive changes the effective configuration;
- project/profile/session control configuration changes;
- the request materially requires different canonical context;
- there is evidence that relevant canonical source changed;
- previously resolved configuration/context is unavailable or uncertain;
- the user invokes `@do:sot` again.

Canonical SoT still outranks stale conversation memory. Reuse is a latency/token optimization, not permission to preserve known-stale canonical facts or stale absence conclusions.

## wrapper_boundary

A client/deployment wrapper should contain only what is required to locate this runtime/deployment and supply genuine client/project defaults or capability boundaries.

Do not copy this execution sequence into every external instruction surface.

## acceptance

A compliant runtime can bootstrap or re-anchor with one parameterless `@do:sot`, fully resolve effective profile composition, registered runtime controls, control-driven behavior activation/suppression/adaptive gating, and applicable response-start configuration, invalidate stale factual conclusions including prior negative lookups, load minimum relevant authorized context, resolve subsequently needed facts from the current canonical source through targeted retrieval, expose truthful compact diagnostics, reuse unchanged configuration within the same chat, selectively reload when needed, preserve host-native normal-chat presentation, default to the normal chat delivery surface unless the user explicitly requests a document-style artifact, apply canonical formats only within their owned boundaries, and keep client wrappers thin.
