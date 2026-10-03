# retrieval

## purpose

Index of V1 internal retrieval guidance.

## files

```text
retrieval_contract.md
→ normative retrieval boundaries and order

query_planning.md
→ compact task-to-module planning heuristics

maintenance.md
→ how to detect and correct retrieval drift without adding premature infrastructure
```

## runtime_guidance

Normal clients need the retrieval contract only when they are implementing or debugging Source-of-Truth discovery.

For ordinary tasks, adapter/routing/module contracts should be sufficient to perform the compact path-first flow without loading all retrieval documentation.

## non_goal

This directory does not provide a custom resolver, embeddings pipeline, or vector index in V1.
