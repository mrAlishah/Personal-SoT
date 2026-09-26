# Public V1 M1 migration record

## Status

This is the historical design record for the initial public foundation. Current
product decisions are owned by
`system/governance/public_v1_product_contract.md`; this record must not override
that contract.

## Delivered boundary

M1 established a clean public foundation:

```text
public-safe reusable contracts
→ public distribution gate
→ minimal empty Personal workspace
→ beginner navigation
```

No real Personal facts, private project state, user-specific paths, credentials,
private adapters, deployment configuration, or Personal Git history were
eligible for migration.

## Layout

M1 preserved the three-root layout:

```text
workspace/  user-managed canonical content and configuration
system/     runtime contracts, validation, governance, and tests
guides/     user and developer documentation
```

Generic reusable material was classified and sanitized before migration.
Personal-only material remained excluded unless independently generalized and
validated.

## M1 scope

The delivered foundation included reusable contracts, a public-safe migration
inventory, a dependency-free public validator, an empty Personal workspace
entrypoint, beginner repository navigation, and repeatable validation commands.
Later setup, Assistant, project, Doctor, and prompt workflows were separate
product slices governed by the current product contract.

## Validation gate

M1 required the Core validators to pass, the public validator to reject private
identifiers, user-specific home paths, and likely raw secrets, and the diff to
contain no unclassified Personal source file.
