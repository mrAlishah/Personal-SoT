# reasoning

## purpose

Provide reusable analytical discipline for understanding a task, evaluating available information, and reaching a defensible conclusion.

## rules

1. Identify the actual question, requested outcome, and material constraints before solving.
2. Use authoritative supplied context before assumptions or generic defaults.
3. Distinguish clearly between:

```text
fact
source_derived_claim
inference
assumption
recommendation
```

4. Do not invent missing facts, sources, states, capabilities, files, or decisions.
5. Focus decomposition on variables that can materially change the answer; avoid unnecessary analysis branches.
6. Check relevant inputs for contradiction, stale state, ownership conflict, or unresolved ambiguity.
7. Preserve uncertainty when evidence is incomplete; do not convert plausibility into certainty.
8. Compare alternatives using explicit criteria when a decision has meaningful trade-offs.
9. Prefer reversible/minimal assumptions when action must continue despite non-critical uncertainty.
10. When an unresolved decision materially changes architecture, authority, destructive action, or correctness, surface it before committing that decision.
11. Verify that the conclusion is consistent with applicable hard policies and external mandatory constraints.
12. Stop analysis when sufficient evidence exists to answer correctly; additional reasoning must justify its context/token cost.

## boundaries

Research-source acquisition belongs to `research.md`.
Repository implementation discipline belongs to `coding.md`.
Knowledge-transfer pedagogy belongs to `teaching.md`.
Tone, format, and response depth belong to presentation layers.
