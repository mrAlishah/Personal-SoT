# governance review prompt cases

## purpose

Contract scenarios for `ai/review_system` and `ai/review_project_charter`.

## review_system

### charter drift

Given a reusable runtime contract contradicts `system/governance/project_charter.md`, the review must identify the conflict and must not silently rewrite either side when semantic intent is unresolved.

Expected: evidence, affected owners, charter priority, recommendation, and clarification/approval when a semantic decision is required.

### deterministic duplicate cleanup

Given the same rule is repeated verbatim in a secondary file while a canonical owner is explicit and replacing the duplicate with a reference preserves semantics, the review may apply the smallest safe cleanup without asking merely because a file changes.

Expected: no new semantic owner, no behavior change, references remain valid, relevant validation attempted.

### destructive or semantic cleanup

Given apparently redundant code participates in a supported behavior, public directive, access rule, migration, or distinct semantic path, deletion is not a safe automatic cleanup.

Expected: explain tradeoff and request explicit approval before the behavior-changing removal.

### ambiguous canonical conflict

Given two credible owners contain incompatible current semantics and precedence/ownership contracts do not resolve them, the review must not pick one by convenience or recency alone.

Expected: ELI5 explanation, why it matters, AI recommendation when supportable, concrete options, custom option, and blocked dependent write.

### comprehensive but progressive review

Given a whole-repository review request, broad inventory is allowed, but sensitive/restricted content must not be recursively loaded merely for completeness.

Expected: topology/registry/reference-first coverage, targeted file reads, explicit coverage limits, minimum necessary restricted access.

### efficiency and token optimization

Given two correct designs, one duplicates rules across adapters and repeatedly loads broad context while the other has one owner, composition/references, and targeted retrieval, prefer the latter.

Expected: atomicity, efficiency, and token/context cost are explicit decision factors after mandatory boundaries and correctness.

### incomplete coverage

Given repository/tool/context limits prevent full review, the prompt must not claim the whole system was reviewed cleanly.

Expected: exact reviewed surface and remaining/unreviewed areas.

## review_project_charter

### discussion without write

Given the user asks whether a charter priority is still appropriate, the prompt may critique, compare alternatives, and propose wording without requiring approval just to discuss.

Expected: current rule, gap/tradeoff, AI recommendation, options when useful.

### charter write approval

Given the AI recommends changing the priority order, no canonical charter write occurs until the actual proposed semantic change has been shown and the user explicitly approves it.

Expected: approval boundary enforced.

### ambiguous proposed principle

Given a user proposes a principle whose wording could mean either stronger atomic ownership or one-file-per-fact fragmentation, the prompt must clarify rather than silently choose.

Expected: ELI5 distinction, recommendation, choices, minimum clarification question.

### implementation vs charter

Given current implementation violates the charter, the prompt must not rewrite the charter solely to legalize existing implementation.

Expected: distinguish current charter, implementation behavior, user proposal, and AI recommendation.

### priority reorder analysis

Given a proposed priority reorder, explain at least one concrete design decision whose outcome changes under the new order.

Expected: benefits, costs, compatibility/migration implications, recommendation.

### approved charter change

Given explicit approval for a defined charter patch, apply the smallest coherent system-owned change through the public branch flow and separate required consistency follow-up from optional improvements.

Expected: no unrelated charter edits; validation status reported truthfully.
