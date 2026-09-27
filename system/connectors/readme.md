# Read-only source access

`source_contract.md` owns the transport boundary. `source.py` composes existing
access, scope and runtime naming owners. `github.py` supplies one real host-side
transport using GitHub's immutable Git objects through an installed `gh`.

## Host integration

Run inside a trusted host executor with `PYTHONPATH` set to the product root:

```python
from system.connectors.github import GitHubSource
from system.connectors.source import SourceSession

# Values come from trusted installation configuration, not prompt fields.
session = SourceSession(GitHubSource("<owner>/<personal_repository>"))
resolution = session.reanchor()
# First complete runtime_bootstrap's effective configuration and mandatory
# policy resolution. Only then query the semantically selected owner.
result = session.lookup("personal", "goals.md")
```

The host must pass `host_read=False` whenever host or stronger policy denies
the operation. Set `personal_owner=True` only from trusted deployment binding
that proves a private single-user owner-controlled Personal instance. It is
not an end-user query option. The transport independently checks repository
privacy, which is necessary but not sufficient for that authorization.

`reanchor()` is the source stage of `@do:sot`, not a claim that profiles,
controls or the full chat runtime were activated. The client continues the
existing `system/adapters/runtime_bootstrap.md` sequence. Re-anchor clears the
old source first; failure leaves no usable old source. Lookups are pinned to
the resolved revision. When freshness is uncertain or change is known, resolve
again before answering. No positive or negative content cache is maintained.

Only `Result.content` after success may enter factual AI context. Show the
result's source/revision/atom provenance in Advanced or citations. Do not print
raw transport responses, internal exceptions, or the host authorization
configuration. Failed results contain no atom content or provenance.

Lookup is an exact-owner primitive. The Assistant uses canonical query planning
to choose the smallest owner and expands only if needed; a failed single-owner
lookup does not prove the fact is absent everywhere. This primitive does not
replace scope-chain policy composition or the Personal absence guard.

## Capabilities and limitations

The reference transport probes repository metadata and the requested/default
ref, reads exact Git objects and verifies blob integrity. It has no write,
search, discovery dump, validator execution, persistent cache or file inventory.
The product's public repository is upstream; users explicitly bind their
canonical Personal instance. It does not depend on the development source repo.

Private instance credentials remain in `gh`'s external host credential store.
Missing executable, authentication, permission, ref, entrypoint, malformed
metadata or unavailable required operations produce a truthful limitation.

Web clients may use the same flow only if their host can run the gate before
tool results enter the model. A tool returning raw bodies or search snippets
directly is not sufficient. Report “This connection cannot safely check access
before displaying context. Use an authorized host with source access enabled.”
They may explain setup/preview guidance, but must not claim reads, writes or
local validation that were not performed.

`write_applied`, `validation_ran`, and `validation_passed` are always false for
this read-only API. A successful factual lookup means only that one current
authorized atom was obtained. Validator runs are separate real host operations.
