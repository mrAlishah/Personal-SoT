# Prompt Explorer contract

## Purpose

Define client-neutral, read-only discovery of reusable prompts for a beginner
without creating a second prompt inventory.

## Authority

`workspace/prompts/` paths and prompt frontmatter are the only discovery source
of truth. Explorer builds an ephemeral result from current files for each
request. It creates no registry, catalog, index, cache, alias, or status copy.

Prompt identity and validity remain owned by `prompt_contract.md` and
`system/validation/validate_prompts.py`.

## Discovery

Discovery reads canonical path identity and frontmatter first. It excludes
`_assets/`, examples, readme files, malformed metadata, and files that do not
resolve safely inside the canonical prompt root.

Exact filters use AND semantics. Every requested list value must exist in its
canonical list; scalar values require exact equality. Identity is exact and a
path prefix matches only that identity or descendants beneath `<prefix>/`.

Free-text evidence is deterministic. Query tokens are case-folded, split on
non-alphanumeric boundaries and underscores, and deduplicated. Candidate score
is compared lexicographically:

```text
exact identity
path-token matches
tag matches
parameter matches
profile/format/tone/depth matches
partial path/tag matches
```

Scores sort descending; canonical identity ascending is the final tie-break.
Filesystem order never affects the result. Search evidence cannot create or
normalize a canonical identity, tag, parameter, or capability.

## Bounded validation and body loading

Explorer ranks from metadata, then calls the canonical per-file prompt validator
in rank order. It validates at most twenty candidates and returns at most five by
default or a requested limit from one through ten.

Prompt bodies are not loaded for unmatched candidates. A body may load only for
bounded canonical validation or after selection for rendering, execution, edit,
or real capability analysis. If the validation ceiling prevents filling the
requested limit, Explorer reports incomplete bounded coverage.

`owned_assets` remains validator-owned technical metadata and never filters or
ranks discovery.

## Status and availability

```text
active      default discovery; recommendable when otherwise valid
draft       explicit draft/edit/build lookup only; not executable
deprecated  explicit lookup only; warning required; not executable
```

Invalid or unresolved prompts are unavailable and never recommended as
executable. Structural validity does not grant context access, restricted-data
authorization, host permission, or task capability.

## Beginner result

Default presentation explains the use case, evidence for the match, required
input, capability limitation, and simple natural-language usage. Canonical path,
metadata evidence, and `@run:<identity>` belong in optional Advanced
output.

Unavailable diagnostics never expose unselected bodies, secret values,
restricted/denied context, or inaccessible client state.

## Acceptance

A compliant Explorer is read-only, on-demand, bounded, metadata-first,
validator-backed, deterministic, client-neutral, capability-honest, and unable
to invent prompt authority or persist discovery state.
