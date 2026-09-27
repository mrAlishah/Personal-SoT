# Profile Builder workflow

## Purpose

Save or edit a reusable Personalization composition only when existing direct
composition or an existing Profile is insufficient for the user's repeated
need.

## Reuse-before-create

```text
exact existing Profile
→ direct existing capability composition
→ existing Profile plus existing overrides
→ edit the same semantic Profile owner
→ create a new Profile only for a valuable repeated combination
```

Similarity never authorizes overwrite. An edit requires the exact Profile
identity and clear intent to modify that same semantic owner.

Shipped `g.*` Profiles are product-owned. The Assistant may discover, select,
and compose them, but user-guided create/edit targets a separate custom
`lowercase_snake_case` Profile.

## Representation

A Profile is a frontmatter-only composition manifest. It references existing
behavior, format, tone, depth, language, and registered-control identities. It
does not copy component instructions or contain prose body content, facts,
context paths, policies, adapters, client wiring, or secrets.

## Preview boundary

Before any write, classify the candidate as fact-safe, reconcile current
Profiles and direct composition, validate through the Profile validator owner,
and show the complete manifest and diff. Route confirmation and apply through
`safe_write_contract.md`.

After confirmation, re-read the target and validation dependencies. If either
changed, stop and produce a new preview. A successful local write runs the
repository-owned Profile/Core, prompt, and public-distribution validators. The
result reports separately whether the write occurred, whether validation ran,
and whether validation passed. A failed post-write validation never hides that
the file changed; repair requires a new proposal.

Local Builder applies for the same Profile are serialized with a short-lived
per-Profile lock. Creates use an atomic no-clobber operation, and all writes are
anchored to the verified Profile directory. Direct filesystem edits do not
participate in that lock; make them before preview or wait for the Builder to
finish so its stale-state reread can detect them.

Only custom `workspace/profiles/<lowercase_snake_case>.md` files may be created
or edited. This workflow
never writes format, tone, depth, control, behavior, registry, or precedence
owners.

## Client capability

No-write clients provide the same questions and complete preview, then state
that nothing was written and validation was not run. Confirmation does not add
write capability.
