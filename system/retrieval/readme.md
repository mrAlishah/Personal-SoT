# retrieval_contract

## purpose

Defines internal Source-of-Truth retrieval: discovering candidate canonical modules efficiently before access, authority, relevance, merge and precedence produce effective context.

## core_separation

```text
retrieval → discovers candidates
authority_resolution → decides effective context
```

A search hit/filename/recent edit/similarity score never establishes authority.

## physical_roots

Runtime factual retrieval resolves canonical modules below `workspace/context/`. Prompt/profile/presentation lookup uses their corresponding `workspace/` roots from `system/layout_contract.md`. System contracts/tests/guides are not candidate factual context merely because search can see them.

## plain_markdown_first

Prefer exact path lookup, compact registries, directory listing, filename/module selection, targeted text search and explicit references. Embeddings/vector DB/custom always-on resolver are not required.

## retrieval_order

```text
1. parse runtime control block
2. resolve logical scope and physical workspace path
3. construct authoritative scope chains
4. discover semantic module names
5. evaluate access before exposing content
6. load mandatory hard-policy atoms
7. load relevant current facts
8. targeted text search only when needed
9. decisions/history only when rationale is required
10. stop at minimum sufficient authoritative context
```

## path_first_discovery

When task maps cleanly to module responsibility, prefer deterministic scope/path/module discovery over broad repository search.

## access_before_content_exposure

A discovered denied/unauthorized restricted module must not enter context/snippets/provenance/diagnostics. If retrieval cannot safely evaluate access before exposure, treat content as unavailable.

## relevance_and_history

Relevance selects optional atoms after authority/access/mandatory requirements. Current modules normally outrank historical decisions for current-state tasks. Proposed/superseded/deprecated decisions do not become current truth through match strength.

## primary_and_supplemental

Retrieve Primary candidates first; supplementals only for relevant gaps or mandatory policies. Do not waste context retrieving supplemental variants of a target already owned by Primary.

## token_budget

```text
correctness/access/mandatory authority
>
relevance
>
retrieval convenience
>
token savings
```

## external_research_boundary

External web/docs/APIs belong to research behavior/tooling. External evidence does not silently become canonical `workspace/context/`; writing/updating canonical truth requires deliberate review.

## acceptance

A compliant client discovers a small deterministic set of Markdown atoms under `workspace/`, protects inaccessible content, and keeps retrieval ranking separate from authority.
