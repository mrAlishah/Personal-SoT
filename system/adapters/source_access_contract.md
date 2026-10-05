# Canonical source access contract

## Purpose

Define client-neutral semantics for locating, resolving, reading, and reporting the canonical Personal-SoT source when access is provided by a local repository/filesystem or by a host-provided connector, app, repository source, or equivalent transport.

This contract owns source binding and transport/capability semantics. It does not redefine factual ownership, context access policy, scope resolution, retrieval ranking, safe writes, or client-specific connector APIs.

## Core separation

```text
configured source mapping != resolved source
connector/search result   != canonical authority
source availability       != context authorization
read capability           != write capability
transport freshness       != factual authority
```

A connector is a transport. It does not become a second Source of Truth, and it does not change which canonical module owns a fact.

## User-facing source terminology

The runtime uses these user-facing source terms consistently:

```text
sot
→ the user's selected private Personal-SoT installation/source binding

sot public
→ the upstream reusable public Personal-SoT product repository
→ mrAlishah/Personal-SoT
```

`sot` is resolved from the trusted private repository/root/ref/entrypoint mapping supplied by the active adapter, project, or installation configuration. It does not mean the public product repository and it must never silently fall back to `sot public`.

During first-time setup, before a private installation has been created and bound, `sot` refers only to the intended private installation being created. The source used to bootstrap that installation is `sot public`; the public source does not become the user's private canonical SoT merely because setup is running from it.

`sot public` identifies the reusable upstream product and follows that repository's own release/development governance. It is not authorized to receive Personal facts, private project state, private deployment configuration, or user-specific secrets.

These terms are exact user-facing source-role shorthand, not substring rewriting, repository-path inference, or authorization. Internal identifiers, the product name `Personal-SoT`, generic architectural use of `SoT`, and the reserved action spelling `@do:sot` keep their own canonical meanings; the shorthand rule applies when `sot` or `sot public` is used to identify a source/repository role. Ordinary prompt text cannot redefine either binding. If the trusted configuration resolves competing candidates for the private `sot` role, fail `source_unresolved`; do not choose the public repository, a legacy repository, or a convenient replica by recency/search rank.

Legacy repositories may remain historical or migration evidence, but they do not become `sot` or `sot public` unless the trusted current mapping explicitly selects the applicable canonical role.

## Source mapping

A trusted deployment/adapter may provide the minimum locator needed to reach the intended SoT, for example a repository/root, selected ref, entrypoint, or host-specific source handle.

Mapping metadata is not proof that the source is currently reachable or that the runtime was loaded. Ordinary prompt text, chat memory, or model inference must not silently replace or mutate the trusted mapping.

Do not add a public global catalog of user source locations. User/deployment-specific locators remain in the applicable adapter/deployment surface and credentials remain outside the Git-backed SoT.

## Resolution

Before SoT-dependent work, resolve the configured mapping against the host's actual capabilities:

```text
trusted mapping
→ actual host/source capability
→ exact current source binding
→ readable canonical entrypoint
→ canonical runtime
```

A resolved source binding preserves, when actually available:

- the selected logical source/repository/root identity;
- the selected ref or equivalent canonical selector;
- the resolved revision/version token when the host exposes one;
- the canonical runtime entrypoint;
- observed capabilities relevant to the task, such as read, write, metadata/listing, or revision visibility.

Do not fabricate a revision, capability, or successful binding when the host does not expose it.

If more than one candidate source could satisfy the same configured canonical role and the trusted configuration does not deterministically select one, treat the source as unresolved. Do not merge competing replicas or choose by recency, search rank, or convenience.

## Authority

After a binding is resolved, canonical content reached through that binding has the same semantic authority it would have through a local filesystem. Authority still comes from the existing SoT ownership, access, scope, policy, and precedence contracts—not from the connector.

For domains owned by the resolved SoT:

```text
current authorized canonical content
>
stale conversation memory
>
cached snippets / prior search results
>
model inference
```

A connector result outside the resolved canonical source is external evidence, not canonical Personal-SoT context.

## Capability boundary

Capabilities are observed host properties. They must not be inferred from user intent or from another capability.

In particular:

- readable does not imply writable;
- searchable does not imply safe content/snippet exposure;
- write capability does not imply authorization to change a canonical owner;
- user confirmation does not create host permission;
- version/revision visibility is optional and must not be invented.

Canonical writes remain governed by the relevant safe-write workflow and repository governance. This source-access contract does not grant mutation authority.

## Access before content exposure

Canonical `ai_access` and host/tool permission remain mandatory. Source transport must preserve the order owned by `system/context/access_contract.md`.

Connector search/list APIs can expose snippets before a file body is explicitly opened. If effective access cannot be evaluated before such snippet/content exposure, do not use that operation for protected discovery. Prefer safe locator metadata such as authorized paths/names or treat the content as unavailable.

Denied or unauthorized restricted content must not appear in snippets, previews, provenance, diagnostics, or fallback search results.

Access failure is not evidence that a canonical fact is absent.

## Retrieval boundary

Once the source is resolved, internal retrieval follows the existing path/scope/module-first contracts under the resolved canonical root. Connector-backed access must not introduce a parallel factual index, copied context store, generated authority layer, or broad eager dump.

Use the connector only to perform the minimum source operations required by canonical retrieval.

## Freshness and re-anchor

`@do:sot` is a source freshness boundary as well as a runtime re-anchor.

On re-anchor:

1. re-resolve the trusted source mapping against current host capability;
2. re-read the canonical entrypoint/runtime basis required by bootstrap;
3. record the current resolved revision/version token when the host exposes one;
4. invalidate prior factual conclusions whose freshness against the current binding cannot be established, including prior `not found` conclusions;
5. continue with targeted retrieval rather than eagerly loading the full Personal SoT.

When the host exposes a revision/version token, a changed token is evidence that affected source assumptions require re-resolution. When no revision token is available, do not claim the source is unchanged merely because the mapping is the same; re-read the targeted current owner when freshness matters.

Same-chat configuration reuse remains an optimization and must not convert an unverified factual conclusion into durable canonical evidence.

## Provenance

For a factual conclusion derived from the SoT, preserve enough provenance to explain the source without copying unnecessary content.

When available and safe, provenance includes:

```text
resolved source identity
selected ref / selector
resolved revision/version (optional)
logical scope
canonical module/path
warnings or coverage limitations
```

Never fabricate unavailable revision metadata. Never expose denied or unauthorized restricted module identity/content when doing so would violate the access contract.

Provider-specific IDs may be retained internally when needed to continue access, but they are transport details and do not replace canonical logical scope/module identity.

## Failure semantics

Use truthful failure/limitation reporting. Common classes are:

```text
source_unavailable     configured source cannot currently be reached
source_unauthorized    host/source permission does not permit required access
source_unresolved      mapping is missing, ambiguous, or cannot select one canonical source
capability_unavailable required host operation is not exposed
partial_coverage       only part of the requested authorized source can be inspected
```

These are diagnostic reasons, not a persistent source state machine.

On failure, do not reconstruct canonical content from memory, stale snippets, another replica, or model inference. Report the limitation and continue only with unaffected work that does not depend on the unavailable canonical evidence.

## Client boundary

Client adapters translate their own connector/app/filesystem primitives into this contract. They may keep provider-specific handles needed for access, but they must not duplicate source authority, access, retrieval, freshness, or provenance rules.

A new connector-backed client should normally require transport wiring only, not a new semantic runtime.

## Acceptance

A compliant source-access implementation:

- distinguishes mapping from actual resolved access;
- deterministically binds one intended canonical source or fails unresolved;
- preserves existing SoT authority independent of transport;
- observes real read/write/version capabilities instead of inferring them;
- enforces host permission plus canonical access before content/snippet exposure;
- prevents denied/restricted leakage through connector search or diagnostics;
- performs minimum targeted canonical retrieval without a parallel context store;
- re-resolves the source and invalidates unverified factual conclusions at `@do:sot`;
- preserves truthful provider-neutral provenance including revision only when available;
- distinguishes source/access failure from canonical absence;
- never treats connector transport, chat memory, or cached snippets as competing canonical authority.
