# Beginner personalization design

## Status

Approved for Public Personal-SoT V1.

## Goal

Let a beginner describe how responses should behave or look in natural
language, discover the current canonical capabilities, compose the smallest
effective configuration, and save a reusable Profile only when that repeated
combination deserves a stable manifest.

```text
natural-language intent
→ classify semantic lanes
→ discover canonical capabilities on demand
→ reuse or compose existing capabilities
→ preview effective configuration
→ create or edit one Profile only when justified
```

Expert directives are optional Advanced output after the beginner-facing
recommendation.

## Scope

| Lane | Discover | Recommend/compose | Create/edit |
| --- | --- | --- | --- |
| Profile | yes | yes | yes |
| Format | yes | yes | no |
| Tone | yes | yes | no |
| Depth | yes | yes | no |
| Registered control | yes | yes | no |
| Behavior | yes | yes through Profile composition | no |

Profile creation and editing target only:

```text
workspace/profiles/<profile_name>.md
```

Deletion and canonical changes to format, tone, depth, control, behavior,
registry, precedence, or their contracts are outside this feature.

## Canonical owners

Discovery reads current owners directly and creates no registry, cache, index,
alias map, or committed inventory:

- Profiles: exact filenames and manifests under `workspace/profiles/`.
- Formats, tones, depths, and registered controls: their sections in
  `system/routing/switch_registry.md` plus resolved canonical targets.
- Control identities, values, and defaults: registered target frontmatter owned
  by `system/behavior/control_contract.md`.
- Behaviors: `system/behavior/module_catalog.md` and the referenced canonical
  behavior targets.

The Explorer may read bounded canonical purpose/metadata evidence for matching.
It never promotes inferred text into a canonical identity. The Assistant may
translate multilingual user intent into exact query/classification fields, but
that translation is invocation-local and never becomes an alias.

## Semantic ownership

```text
response structure or representation → format
interpersonal register              → tone
amount of detail                    → depth
optional runtime behavior tuning    → registered control
method used to perform work          → behavior
reusable composition defaults        → Profile
durable Personal/project truth       → context, never Profile
```

The Advisor must not solve one lane by writing another. A request for a shorter
answer recommends a depth; a formal register recommends a tone; a comparison
table recommends a format. Step-by-step learning may compose an existing
learning Profile with canonical `learning` and `step_execution` control values.

## Discovery and ranking

Discovery is deterministic and on demand. Exact lane, identity, component, and
allowed-value filters are applied before bounded lexical ranking. Ranking uses
only evidence present in canonical identities, Profile manifests, registry
mappings, target metadata, and bounded purpose text. Equal scores are ordered by
lane and exact canonical identity, never filesystem iteration order.

Unavailable, invalid, unresolved, or unreadable capabilities are not
recommended as usable. The result may report a non-sensitive unavailable count
without exposing target contents or secret values.

Canonical bodies are read only when a candidate needs purpose evidence or final
validation. No discovered state is persisted.

## Reuse-before-create

The Advisor uses this order:

```text
exact existing Profile
→ direct existing lane composition
→ existing Profile plus explicit existing overrides
→ small Profile customization for a clear same owner
→ new Profile only for a valuable reusable repeated combination
```

An invocation such as `formal + short` is already satisfied by direct tone and
depth composition and must not create a Profile. `research + deep +
professional` reuses the existing `g/research` Profile when its manifest matches.

High similarity does not authorize an edit. Editing requires an exact Profile
identity, clear same-semantic-owner intent, and the normal safe-write pipeline.

## Profile representation and validation

A Profile remains a compact YAML-frontmatter composition manifest. It stores
only canonical component identities and control values; it never copies module
instructions, canonical facts, context paths, policies, adapter wiring,
credentials, or client-specific behavior.

`system/validation/validate_v1.py` remains the owner of Profile schema,
reference, registry, and control-value validation. It exposes the smallest
stable per-source interface needed for preflight and state binding. Builder code
must not duplicate those rules or parse validator stdout.

The existing batch validator behavior remains compatible. Profile scenario
Markdown remains acceptance specification; executable RED → GREEN claims apply
only to Python tests that were observed failing and passing.

## Safe write

Read-only discovery and composition run directly. Profile create/edit follows
`system/assistant/safe_write_contract.md`:

```text
classify and reconcile Profile identity/owner
→ detect existing equivalent composition or conflict
→ build the minimum manifest
→ preview complete content and diff
→ explicit confirmation
→ re-read Profile and referenced validation state
→ authorized atomic write
→ validate_v1 core + validate_prompts + validate_public
→ truthful report
```

The Profile Builder is intentionally narrow. `system/prompts/builder.py` is not
turned into a generic component builder. A shared primitive is extracted only
if its behavior is genuinely component-neutral and reduces duplicated security
logic without importing Prompt semantics into Profiles.

The result distinguishes whether a write happened, whether validation ran,
whether it passed, validation errors, and overall success. A post-write
validation failure preserves recovery evidence and is never reported as
success. Semantic repair requires a new proposal.

## Client capability

Local agents may apply a confirmed Profile change only with real write and
command capability. Web or no-write clients use the same discovery,
recommendation, questions, and complete preview, then state explicitly:

```text
nothing was written
validation was not run here
```

Adapters declare capability only and never restate discovery, composition,
Profile, or safe-write semantics.

## Beginner interaction

The workflow uses the selected language, shows compact progress, and asks one
adaptive material question at a time. It explains the recommendation with an
example and offers `I don't know — recommend one` when appropriate.

Required examples include:

- “Make answers shorter” → depth recommendation.
- “Answer more formally” → tone recommendation.
- “Show it as a comparison table” → format recommendation.
- “Teach me step by step” → existing Profile/control/behavior composition.
- “Deep professional research” → reuse the existing Profile before creation.

Only after this result may Advanced show exact `@profile`, `@fmt`, `@tone`,
`@depth`, and `@control` syntax.

## Acceptance

The feature is complete when executable evidence shows deterministic canonical
discovery, correct multi-lane composition, reuse-before-create, Profile-only
mutation, fact-free manifests, same-owner edit protection, preview-bound and
stale-safe local writes, honest web previews, strongest relevant validation,
and no secondary inventory or client-specific canonical logic.
