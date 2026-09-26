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

Only `workspace/profiles/<name>.md` may be created or edited. This workflow
never writes format, tone, depth, control, behavior, registry, or precedence
owners.

## Client capability

No-write clients provide the same questions and complete preview, then state
that nothing was written and validation was not run. Confirmation does not add
write capability.
