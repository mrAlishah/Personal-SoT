# Personalization Explorer contract

## Purpose

Discover current Profile, format, tone, depth, registered-control, and behavior
capabilities without creating a second inventory or changing canonical state.

## Owners

```text
Profile  → workspace/profiles/
format / tone / depth / control → switch_registry + resolved target
behavior → system/behavior/module_catalog.md + resolved target
```

Control values and defaults come only from canonical control target metadata.
Profile component evidence comes only from its manifest.

## Search

Search is on demand, deterministic, read-only, bounded to twenty validated
candidates, and limited to ten returned matches. Exact lane and identity filters
apply before lexical ranking. Ranking uses only canonical identity and manifest
evidence; ties use lane then identity.

Natural-language interpretation may produce exact query/classification fields,
but it never creates a durable alias or guessed identity.

## Availability

Missing, invalid, unreadable, unresolved, or path-escaping candidates are not
returned as usable. A result may report only their count. It does not expose
candidate bodies, secrets, or denied content.

## Acceptance

A compliant Explorer reads canonical owners directly, returns repeatable
evidence-backed results, validates only bounded candidates, and writes no cache,
index, catalog, alias, or other state.
