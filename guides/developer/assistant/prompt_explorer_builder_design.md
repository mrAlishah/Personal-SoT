# Prompt Explorer and Builder design

## Outcome

Give a beginner a natural-language way to find, use, customize, edit, or create a reusable prompt while preserving canonical prompt ownership and safe-write behavior.

```text
describe use case
→ discover existing prompt
→ prefer reuse or composition
→ preview usage or minimal change
→ confirm only when a canonical write is necessary
→ validate and report
```

Explorer and Builder have separate ownership:

```text
Explorer = discovery and recommendation, read-only
Builder  = guided create/edit, safe-write required
```

## Canonical ownership

`workspace/prompts/` paths and each prompt's frontmatter remain the only prompt identity and discovery source of truth.

The design adds no prompt registry, generated catalog, persistent index, cache, canonical inventory, alias table, or secondary status owner. Search results are ephemeral and are rebuilt from current canonical files for every request.

The existing contracts remain authoritative:

```text
system/governance/public_v1_product_contract.md
system/assistant/assistant_contract.md
system/prompts/prompt_contract.md
system/prompts/parameter_contract.md
system/prompts/action_contract.md
system/profiles/profile_contract.md
system/assistant/safe_write_contract.md
```

Prompt-to-prompt runtime inheritance, inclusion, and dependency composition remain forbidden.

## Components

### Prompt Explorer contract

A client-neutral contract owns discovery behavior, beginner presentation, status handling, capability honesty, and recommendation rules. Adapters only supply real repository/tool capability and do not copy search semantics.

### On-demand scanner

A dependency-free read-only scanner under `system/prompts/` walks current canonical prompt paths on demand. It reads path identity and frontmatter only during discovery.

The scanner creates no state and performs no writes. It excludes `_assets/`, examples, and non-canonical prompt files.

### Validator interface

`system/validation/validate_prompts.py` remains the sole owner of prompt validity rules. It exposes the smallest reliable per-file interface needed to validate a selected candidate.

The refactor may expose frontmatter reading and per-file validation, but it must not move validation semantics into Explorer. The existing full-repository `run(root) -> list[str]` behavior remains available and validator-owned.

### Prompt Builder workflow

A separate client-neutral Builder workflow owns guided reuse, composition, create/edit classification, preview, stale-state checks, and safe-write routing. It does not own discovery rules or prompt-schema validation.

Thin `sot` prompts invoke Explorer and Builder contracts without copying their algorithms.

## Lazy loading boundary

Discovery reads only the path and frontmatter block, stopping at the closing frontmatter delimiter. Prompt bodies are not loaded merely to enumerate or rank the library.

A body may be loaded only when:

- an exact prompt was selected;
- a ranked candidate is being validated for recommendation;
- rendering, execution, edit preview, or dependency/capability analysis genuinely requires it.

After metadata ranking, candidates are validated in rank order only until the requested result limit is filled or a bounded validation ceiling is reached. Invalid candidates are skipped without broad body loading. An unmatched prompt body is never read.

V1 returns five recommendations by default, accepts a requested limit from one through ten, and validates at most twenty ranked candidates per search. If that ceiling prevents filling the result limit, report incomplete bounded coverage rather than widening silently.

## Explorer query model

Explorer accepts a user intent plus optional exact filters. The Assistant may translate natural language into query tokens and filters, but all reported matches and recommendations must cite actual canonical evidence returned by Explorer.

Exact filters use AND semantics and exact canonical values:

```text
identity or path prefix
prompt_status
prompt_tags
required_params
optional_params
prompt_profiles
prompt_formats
prompt_tone
prompt_depth
```

Every supplied filter must match. For list-valued filters, every requested value
must be present in the corresponding canonical list; extra canonical values do
not invalidate the match. Scalar filters require exact equality. An explicit
identity requires exact equality, while a path-prefix filter matches only a
canonical identity beneath that exact prefix.

Explorer does not invent or normalize a missing canonical identity, tag, parameter, profile, format, tone, depth, or capability. A search term is evidence for discovery only; it never becomes a canonical alias.

`owned_assets` remains validator-owned technical metadata. It is never a ranking/filter field and is not exposed during discovery.

## Deterministic ranking

Candidate enumeration is sorted by canonical identity before scoring. Free-text query tokens are case-folded, split on non-ASCII-alphanumeric boundaries, and further split on underscores. Empty tokens and duplicates are removed. Metadata identities remain exact and case-sensitive for resolution.

Each candidate receives this lexicographically compared match vector:

```text
(
  exact_full_identity_match,
  exact_path_token_match_count,
  exact_tag_match_count,
  exact_parameter_match_count,
  exact_profile_format_tone_depth_match_count,
  partial_path_or_tag_match_count
)
```

Sort order is:

1. match vector descending;
2. canonical prompt identity ascending as the final tie-break.

`exact_full_identity_match` is true only when the caller supplied an explicit identity equal to the canonical identity. A partial path/tag match means a query token of at least three characters is a substring of a path token or tag. Duplicate query tokens count once. A candidate with no match and no satisfied explicit filter is excluded. Filesystem iteration order never affects results.

Exact path resolution remains authoritative after selection. Ranking never changes identity or creates aliases.

## Status and usability

Status handling remains aligned with Prompt Contract and Action Contract:

```text
active      default discovery; may be recommended for execution
draft       visible only for explicit draft/edit/build requests; never executable
deprecated  visible only when explicitly requested; warning required; never recommended for execution
```

A candidate must pass the canonical per-file validator before being presented as executable or recommended. Invalid prompts and prompts with unresolved profiles, formats, tones, depths, parameters, owned assets, or other validator-owned dependencies are unavailable.

Unavailable items may be counted or identified minimally without displaying prompt bodies, secret values, restricted context, or sensitive canonical content.

Structural prompt validity does not grant task capability, context access, restricted-data authorization, or host permission. After selecting a candidate, resolve the minimum body and referenced runtime configuration needed to determine whether the active client can render or execute it. Report unavailable capability instead of simulating success.

## Beginner result

Default results are organized around the user's use case, not repository paths:

```text
recommended use
why it matches
information the user must provide
status or capability limitation
simple natural-language usage
```

The exact canonical identity, path, matching metadata, and expert invocation such as `@do:prompt:<identity>` appear only in an optional `Advanced` section.

No result claims that a prompt exists, is valid, or is executable without corresponding current canonical evidence.

## Builder decision order

Builder must follow this order and stop at the first rung that satisfies the user's outcome:

```text
1. exact existing prompt
2. usable existing prompt with parameters
3. composition/customization
4. edit the same semantic prompt when identity and ownership are clear
5. create a new prompt only when necessary
```

Composition/customization may use only contracted parameters, profiles, formats, tone, depth, and registered controls. It does not introduce prompt-to-prompt runtime inheritance or inclusion.

Registered controls may be applied as invocation/runtime composition only. They
must not be written into prompt frontmatter unless Prompt Contract adds a
canonical control field through a separate approved contract change.

High similarity alone never authorizes editing an existing prompt. Edit is appropriate only when the requested change modifies the same semantic prompt and its canonical identity/ownership is clear. When edit-versus-new is materially ambiguous, show both effects and ask the user to choose before building a write proposal.

## Fact and context boundary

Reusable prompts remain fact-light. Durable Personal, organization, or project facts are never copied into the prompt body or manifest.

```text
reusable varying input → prompt parameter
durable factual truth  → independently selected canonical context
presentation behavior → profile/format/tone/depth/control reference
```

Prompt selection never grants factual scope or restricted-context access.

## Safe-write flow

Explorer never writes. Builder uses the existing safe-write model for every material create or edit:

```text
classify
→ reconcile existing identity and ownership
→ detect duplication and conflict
→ build the minimum change
→ preview the complete diff
→ explicit confirmation
→ re-read and verify version/current state
→ authorized write
→ validate
→ report
```

For an edit, preview binds confirmation to the exact canonical identity, current file version, full proposed diff, and referenced components. For a create, preview binds confirmation to the exact new identity, absent-target check, complete file content, and any justified owned assets.

Immediately before writing:

- re-read the existing file and compare it with the previewed version for edits;
- verify the proposed target is still absent for creates;
- re-run duplication/conflict checks against current canonical prompts;
- stop and issue a new preview if relevant state changed.

After an authorized write, run `system/validation/validate_prompts.py` plus other affected repository validators. Never report creation/edit success when the write or required validation failed.

## Client capability

Local agents with authorized repository write capability may apply a confirmed Builder proposal and run validation.

Web or read-only clients run the same discovery, questions, classification, composition, and preview. When write or command capability is unavailable, they state that nothing was written and validation was not run there.

Client adapters expose capability only. They do not duplicate Explorer ranking, Builder decision order, prompt validity, or safe-write semantics.

## Errors and privacy

- Missing exact identity: report no exact match and continue bounded discovery when requested.
- No usable candidate: explain why at category level and offer Builder; do not fabricate a prompt.
- Invalid/unresolved candidate: exclude from execution recommendations and provide only safe availability diagnostics.
- Ambiguous edit ownership: stop the write path and ask the user to choose edit or new identity.
- Stale preview: discard authorization and generate a new proposal.
- Validation failure after write: report failure and affected files; do not claim success.
- Secret or durable-fact candidate: exclude it from reusable prompt content and recommend parameters, context, or a proper secret store.

Default output never exposes prompt bodies from unselected candidates, secret values, restricted/denied context, or inaccessible client state.

## Performance boundary

V1 performs bounded on-demand metadata scans and limited candidate validation. It adds no optimization state.

Record only measurements needed to evaluate an actual problem, such as prompt count, metadata scan duration, candidate count, and bodies loaded for final validation. These observations are non-canonical diagnostics.

An index, cache, catalog, or vector/semantic search requires measured evidence and a separate architecture decision. It is not part of this design.

## Tests

### Explorer executable tests

- exact identity and exact filter behavior;
- deterministic match-vector ordering and canonical-identity tie-break;
- independence from filesystem iteration order;
- unmatched bodies are not loaded;
- only bounded top candidates load bodies for canonical validation;
- active/draft/deprecated behavior;
- invalid and unresolved-reference candidates are not executable/recommended;
- results contain only real canonical identities and metadata;
- read-only execution leaves repository bytes unchanged.

### Builder workflow cases

- exact prompt reuse stops creation;
- existing prompt plus parameters is preferred;
- profile/format/tone/depth/control composition is preferred to creation;
- prompt-to-prompt inheritance remains rejected;
- high similarity without shared identity does not authorize overwrite;
- ambiguous edit-versus-new requires user choice;
- create/edit preview contains the complete diff;
- stale edit version and newly occupied create target require a new preview;
- durable facts are moved to parameters or independently resolved context;
- web/read-only clients remain preview-only;
- successful local write runs canonical prompt validation.

### Review gates

After GREEN, review the complete branch for:

```text
semantic duplication
secondary inventories or stale state
prompt-to-prompt coupling
unbounded body loading
access or content leakage
client-specific semantics in core contracts
```

## Non-goals

- committed prompt catalog or index;
- cache, database, vector store, embeddings, or fuzzy identity resolution;
- prompt-to-prompt inheritance/include;
- prompt deletion changes;
- web mutation helper, connector, or server;
- automatic background prompt creation or modification;
- storing durable Personal facts in reusable prompts.

## Acceptance

The slice is complete when a beginner can describe a use case, receive a deterministic evidence-backed recommendation from current canonical metadata, use or customize an existing valid prompt before creation, safely preview and confirm a justified create/edit, validate an actual local write, and receive the same truthful preview on clients without write capability—without any secondary prompt inventory or leaked canonical content.
