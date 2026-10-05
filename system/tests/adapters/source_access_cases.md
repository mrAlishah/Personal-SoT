# source_access_cases

These acceptance scenarios define the contract-level behavior required for local and connector-backed canonical Personal-SoT source access. They are specification cases unless/until an executable harness explicitly covers them.

## case_01_mapping_is_not_resolution
Trusted adapter configuration names a repository/ref/entrypoint, but the active host cannot read it.
Expected: source is reported unavailable; mapping metadata is not treated as loaded canonical runtime.

## case_02_connector_is_transport_not_authority
A connector search result and current canonical module disagree.
Expected: once the configured canonical source is resolved and authorized, the canonical module owns the fact; connector ranking does not create authority.

## case_03_one_canonical_binding
Two accessible repository copies appear to match the configured SoT but trusted configuration does not identify which is canonical.
Expected: source remains unresolved; do not merge or choose one by recency/search rank.

## case_04_read_does_not_imply_write
Connector can read canonical files but exposes no authorized mutation operation.
Expected: read/recommend/preview may proceed; no write success or validation execution is claimed.

## case_05_revision_is_truthful
Host exposes repository/ref but no resolved revision token.
Expected: provenance may report source/ref but must not fabricate a commit/version.

## case_06_access_before_connector_snippet
Restricted/denied module contains an exact query match and connector search would return body snippets before canonical access evaluation.
Expected: do not use the leaking operation for that candidate; protected content is absent from snippets/provenance/diagnostics.

## case_07_authorized_targeted_read
Personal restricted authorization is valid and one specialized atom is materially needed.
Expected: read only the smallest relevant atom through the connector; do not dump the Personal source.

## case_08_access_failure_not_absence
Likely owner is restricted but host authorization cannot be established.
Expected: report source/access limitation; do not claim the fact does not exist.

## case_09_reanchor_reresolves_source
A prior fact/not-found conclusion exists, the canonical source changes, and the user invokes `@do:sot`.
Expected: re-resolve the current source binding, invalidate unverified factual conclusions, and retrieve the needed owner again only when requested.

## case_10_revision_change
Host exposes a revision token and it changes after bootstrap.
Expected: treat affected prior factual assumptions as requiring current resolution; do not preserve stale fact conclusions solely because scope/profile configuration is unchanged.

## case_11_no_revision_available
Host exposes no revision token and freshness materially matters for a later fact lookup.
Expected: targeted reread of the current canonical owner; do not claim the source is unchanged.

## case_12_memory_conflict
Conversation memory recalls an older value while the current authorized connector-backed canonical module contains a newer value.
Expected: current canonical source wins.

## case_13_external_result_is_not_canonical
Connector/search tool returns material outside the resolved SoT source.
Expected: treat it as external evidence/research; it does not silently enter canonical Personal context.

## case_14_provider_neutral_provenance
A factual answer uses an authorized canonical module.
Expected: preserve source identity, selected ref/selector, optional actual revision, logical scope, and canonical module/path when available and safe; provider-specific IDs are transport detail.

## case_15_partial_coverage
Connector can inspect only part of the requested authorized source.
Expected: report partial coverage and avoid universal claims based on inaccessible owners.

## case_16_private_sot_term_does_not_fall_back_to_public
Trusted configuration names a private `sot` source, but that source is unavailable while `mrAlishah/Personal-SoT` is reachable.
Expected: report private source unavailable/unresolved; do not silently bind `sot` to `sot public`.

## case_17_public_sot_term_is_explicit_upstream
The user explicitly asks about `sot public`.
Expected: resolve the upstream reusable public product role (`mrAlishah/Personal-SoT`) subject to actual source capability/governance; do not substitute the user's private `sot`.

## case_18_first_setup_keeps_source_roles_separate
No private `sot` exists yet and setup is running from `sot public`.
Expected: the public source is only the reusable bootstrap/update source; the intended private destination is the future `sot`, and Personal data is never written to the public source merely to complete setup.

## case_19_legacy_source_is_not_implicit_sot
A reachable legacy repository contains a valid older runtime while the trusted current mapping selects a different private installation.
Expected: legacy availability does not make it `sot`; current trusted private source binding wins, or resolution fails closed if ambiguous.

## exit_criterion
Source access is contract-compliant when local and connector transports resolve one intended canonical source, preserve host plus canonical access before content exposure, perform minimum targeted retrieval without parallel authority, re-anchor freshness truthfully, retain provider-neutral provenance, and distinguish unavailable/unauthorized/partial access from canonical absence.
