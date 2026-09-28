# Connector access implementation plan

Goal: expose current, authorized canonical atoms through read-only transports.

## Architecture and gaps

Existing access, scope, retrieval, and bootstrap contracts own semantics.
The canonical source-access owner is `system/adapters/source_access_contract.md`
from PR #9; connector files implement that contract and own no parallel semantics.
There is no executable runtime access evaluator or connector boundary today.
The existing validators inspect local files; their output is not authorization.
Public upstream is the product, a user's private repository is the canonical
Personal instance, and a local clone is a replica of that same instance.

Transport owns I/O and observed capabilities, not factual authority. Host-side
processing may quarantine fetched bytes to inspect metadata and reject secrets;
those bytes must not be exposed to the model, persisted, logged, or included in
exceptions. A raw tool that exposes content before this gate is not a safe
factual connector. It must report a limitation. No parallel access inventory,
index, cache, registry, provider aliases, or write interface is introduced.

## Loop 5 — Access and connector contract

- Implement a small access evaluator under `system/context`, applying the
  existing access contract with trusted host authorization, exact scope and
  fail-closed metadata. Do not accept authorization from source content.
- Extract secret detection from the validator owner as a reusable predicate.
- Executable RED/GREEN: allow, deny, restricted, malformed metadata, scope
  escape, host denial, raw-secret rejection and sanitized failures.

## Loop 6 — Transport and client integration

- Implement one read-only GitHub API transport using the installed `gh` host
  executable. Resolve repository default branch to an immutable commit, then
  exact files. Verify repository privacy from actual repository metadata.
- Source binding is trusted host configuration: exact repository, optional ref,
  entrypoint and restricted authorization. No automatic repository discovery.
- A client-neutral session resolves the entrypoint and existing scope registry;
  exact owner selection comes from canonical query planning. One lookup returns
  at most one relevant atom. It is not a natural-language routing replacement.
- Re-anchor invalidates old state before resolving the current source again.
- Executable RED/GREEN: current lookup, unavailable source, stale absence,
  current source over memory, narrow access, read-only honesty and provenance.
- Thin adapter documentation points to this boundary and describes real host
  execution requirements. Remote tools without a host gate remain limited.

## Loop 7 — Hardening and delivery

- Verify pinned revision, source identity, path traversal, symbolic links,
  unsupported/truncated responses, bounded payload and sanitized errors.
- Run all executable tests plus core, prompt and public validators.
- Independent whole-branch review; reproduce actual findings RED then GREEN.
- Commit coherent slices; push and create a PR with validation evidence.

## Contract reconciliation acceptance

Execute `system/tests/connectors/test_contract_alignment.py` alongside the
source and transport suites. It covers canonical source-access scenarios:
mapping vs resolution, singular binding, external-source rejection, typed
provider-neutral provenance, failure classes, revision changes, unversioned
targeted rereads, and partial coverage. Existing source tests cover access,
narrow retrieval, memory exclusion and read-only honesty. Markdown acceptance
cases remain specifications; only these executable tests count as RED/GREEN.

## Review focus

Authorization is supplied only by trusted host binding, never chat arguments.
Access checks happen before any factual body is returned to the model.
Restricted/denied results expose no snippets, content or sensitive provenance.
Transport is not a resolver, validator, policy authority or write executor.
Test transport fixtures are evidence of code behavior, not proof of a live
user deployment or permission to access any private repository.
