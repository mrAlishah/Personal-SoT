# coding

## purpose

Provide reusable software-engineering execution discipline for understanding, modifying, and validating code or repositories.

## rules

1. Inspect the relevant repository state, surrounding code, interfaces, and local conventions before editing.
2. When modifying this SoT repository itself, resolve `system/governance/project_charter.md` and ensure material design choices preserve its purpose, priorities, atomicity, efficiency, and context/token-economy principles.
3. Prefer the smallest coherent change that satisfies the requested outcome.
4. Preserve existing behavior, public interfaces, data contracts, and compatibility unless a change is intentional and justified.
5. Verify assumptions against actual code, configuration, schemas, tests, or documentation rather than inventing repository state.
6. Follow existing naming, architecture, error-handling, testing, and dependency conventions unless the task explicitly changes them.
7. Consider failure modes, edge cases, security, concurrency, data integrity, migration, and backward compatibility when relevant to the change.
8. Do not broaden scope with unrelated refactors unless they are necessary for correctness or materially improve a higher-priority project-charter concern.
9. Prefer explicit, reviewable changes over hidden side effects or duplicated logic/state.
10. For otherwise-correct alternatives, prefer clearer semantic ownership, fewer reconciliation points, narrower retrieval, less duplicated context, and lower runtime/token cost.
11. Validate the result with the strongest practical checks available, such as:

```text
targeted tests
static analysis
build/type checks
linting
focused runtime verification
```

12. If validation cannot be completed, state what was not verified and why.
13. Report the files/areas changed and give reproducible local verification or sync commands when user action is required.
14. Distinguish implemented work from suggested follow-up work.

## destructive_changes

For destructive, irreversible, schema-changing, security-sensitive, or architecture-defining changes, ensure the required context/policy/decision authority is resolved before execution.

## boundaries

Project stack and architecture are context, not behavior.
General evidence research belongs to `research.md`.
General analytical decision-making belongs to `reasoning.md`.
Response format and tone belong to presentation layers.
Project-wide SoT purpose/priorities belong to `system/governance/project_charter.md`.
