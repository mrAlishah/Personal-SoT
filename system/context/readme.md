# context_contracts

## purpose

This directory defines system-owned semantic contracts for factual context atoms.

Canonical factual content itself lives under:

```text
workspace/context/
```

Read only the contract relevant to the current operation.

## contract_index

```text
module_contract.md          semantic atomicity/ownership/composition
module_catalog.md           module names and semantic responsibilities
boundary_contract.md        classification boundaries
access_contract.md          ai_access and fail-closed loading
sensitive_data_contract.md  sensitive-vs-secret boundary
policy_contract.md          hard/soft policy representation
decision_contract.md        durable rationale/lifecycle
```

These are architecture contracts, not ordinary task context. `system/routing/` remains authoritative for scope resolution, merge and precedence.

Correctness and quality outrank token efficiency.
