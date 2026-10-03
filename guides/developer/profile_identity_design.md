# profile_identity_design

## status

Historical design record. Describes the decision to move Profile identity
from a dotted `g.*` reserved namespace to a slash-native `g/*` reserved
namespace as part of the runtime user-naming refactor. The current
canonical contract is `system/profiles/profile_contract.md`.

## purpose

Public V1 had not released when this change was made, so the dotted
`g.segment.segment` Profile grammar (itself introduced by an earlier
refactor, see `runtime_naming_design.md`) could be replaced outright
rather than aliased. The product's broader naming cleanup moved every
other user-facing hierarchical identity (Prompts) to `/`-separated
`[a-z0-9]+` segments; keeping Profiles on `.`-separated segments would
have left two different hierarchy separators in the same runtime
vocabulary, which fails the "structurally consistent" requirement.

## grammar

```text
custom Profile:  <segment>[/<segment>...]
shipped Profile: g/<segment>[/<segment>...]

segment := [a-z0-9]+
```

A custom Profile identity's first segment must not be the literal `g`;
that string is reserved exactly, not fuzzy-matched.

## migration table

```text
g.architecture.review  -> g/architecture/review
g.coding                -> g/coding
g.german.learning       -> g/lang/german
g.obsidian.note         -> g/obsidian/note
g.research              -> g/research
g.technical.learning    -> g/tech/learn
```

Old dotted identities do not resolve after this change. No alias layer
was added, matching the project's pre-V1-release no-compatibility-shim
policy.

## ownership

Ownership enforcement is unchanged in mechanism, only in carrier: a
single function, `profile_identity_kind()` in
`system/routing/runtime_naming.py`, classifies an identity as `"custom"`,
`"built_in"`, or unresolved (`None`). Any identity whose first `/`-segment
equals `g` is either `"built_in"` (if it fully matches the reserved
grammar) or unresolved — it can never be classified `"custom"`, so
`system/personalization/profile_builder.py`'s existing
`if kind == "built_in": raise ValueError(...)` guard needed no logic
change, only the regex constants it depends on transitively.

No frontmatter field, no separate physical directory outside the `g/`
prefix, and no registry entry carries ownership — the identity string
itself is still the only signal, by design (this mirrors
`registry_contract.md`'s "self-addressing" principle for Profiles).

## acceptance

A compliant implementation rejects any underscore or dot inside a
Profile identity segment, resolves `g/...` identities only to shipped
files under `workspace/profiles/g/`, and never allows a guided
create/edit flow to write to a `g/...` identity.
