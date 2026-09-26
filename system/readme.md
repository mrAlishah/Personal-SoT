# system

`system/` contains the runtime model and developer-owned implementation contracts.

Ordinary end users should not need to edit this area when updating facts, prompts, profiles, or presentation preferences.

Major areas include:

```text
context/       factual schema/access/policy contracts
prompts/       prompt schema/action/parameter contracts
profiles/      profile schema contracts
presentation/  presentation contracts
behavior/      reusable AI operating behavior
routing/       grammar, registries, scope and precedence
adapters/      generic client wiring contracts
retrieval/     candidate discovery/query planning
automation/    safe generated/maintenance operations
validation/    executable structural checks
migration/     history migration contracts
governance/    project charter and Core/Personal development rules
release/       readiness/freeze records
tests/         contract and integration coverage
```

Canonical project purpose, design principles, and decision priorities live in:

```text
system/governance/project_charter.md
```

Material changes to the SoT itself should be evaluated against that charter before implementation.

Developer documentation starts at `guides/developer/readme.md`.
