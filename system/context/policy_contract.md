# policy_module_contract

## purpose

Defines the V1 representation of scoped hard and soft policies so M1 merge and precedence rules can be applied deterministically.

Policies describe what must, must not, should, or should not happen. They are distinct from factual context.

## location

Policies live under the scope that governs them:

```text
workspace/context/personal/policies/
workspace/context/personal/projects/<project>/policies/
workspace/context/organizations/<organization>/policies/
workspace/context/organizations/<organization>/projects/<project>/policies/
```

Nested projects may also own `policies/` directories at their own scope.

Create only policy domains that actually contain rules.

Typical domain files may include:

```text
security.md
compliance.md
coding.md
privacy.md
development_conventions.md
```

## scope_and_applicability

A policy module governs its owning scope and descendant scopes within the same resolved ownership chain unless a narrower policy rule overrides an applicable soft rule.

Examples:

```text
personal/policies/development_conventions.md
→ applies to personal and personal project descendants when the task performs the governed development operation

personal/projects/project_a/policies/development_conventions.md
→ applies to project_a and its descendants

organizations/acme/policies/development_conventions.md
→ applies to acme and acme project descendants
```

Policy applicability is semantic, not merely path-presence based. A policy rule participates only when the current task or operation falls inside the rule's governed domain.

Examples:

```text
branch_naming_pattern
→ applicable when creating, renaming, recommending, or validating a Git branch

commit_naming_pattern
→ applicable when creating, recommending, or validating a commit message

repository_owned_name_style
→ applicable when naming repository-owned files, directories, identifiers, or internal paths
```

Applicable hard policies are mandatory. Applicable soft policies are active defaults subject to scope precedence. An unrelated policy module is not loaded merely because it exists in an ancestor scope.

A client or adapter must not require the user to repeat an applicable ancestor policy inside each project instruction. Scope composition supplies the governing policy.

## access

Policy modules follow `system/context/access_contract.md` and require explicit `ai_access` metadata before AI loading.

A mandatory policy that is not accessible cannot be silently treated as absent when the task requires that governing scope; the resolver should surface an access/configuration problem rather than assume permission to proceed.

## representation

A policy file groups rules by rule type:

```markdown
---
ai_access: allow
---

# security

## hard

- `credential_exposure`: Never expose credentials.
- `token_logging`: Never log access tokens.

## soft

- `security_review_style`: Prefer review before production rollout.
```

Only sections that contain rules are required.

A structured policy domain should normally use separate stable rule IDs for independently overridable targets rather than one broad rule that forces all settings to override together.

Example:

```markdown
# development_conventions

## soft

- `repository_owned_name_style`: Use lowercase_snake_case for repository-owned names unless an external contract requires an exact name.
- `branch_naming_pattern`: Use `<type>_<scope>_<goal>`.
- `commit_naming_pattern`: Use `<type>(<scope>): <imperative summary>`.
```

A child project may override only `branch_naming_pattern` while continuing to use the inherited naming and commit conventions.

## rule_identity

Every policy rule has a stable lowercase snake_case `rule_id`.

Conceptual identity is the governed semantic rule domain identified by `rule_id` within the corresponding policy domain across a resolved scope chain.

The physical module path provides provenance and ownership; downstream policy modules intentionally reuse the same semantic `rule_id` when overriding the same soft rule domain.

Within one policy file, `rule_id` MUST be unique.

A rule ID should describe the governed rule domain rather than restate the full sentence.

Good:

```text
credential_exposure
service_api_protocol
production_change_review
repository_owned_name_style
branch_naming_pattern
commit_naming_pattern
```

Avoid IDs tied to temporary wording such as:

```text
do_not_do_this_new_rule
rule_2
important_policy
```

## hard_rules

Rules under `## hard` are cumulative and non-overridable.

A downstream scope may:

- add a new hard rule;
- add a stricter compatible requirement;
- restate an exact equivalent only when unavoidable, though duplication should normally be removed.

A downstream scope may not:

- remove an applicable upstream hard rule;
- replace it with a weaker rule;
- negate it;
- use a soft rule to bypass it.

If applicable hard rules are logically incompatible, surface a policy conflict rather than choosing one by specificity.

## soft_rules

Rules under `## soft` are overridable preferences or defaults.

For the same governed rule domain, more-specific authoritative primary scope wins according to `system/routing/precedence.md`.

Use the same semantic `rule_id` across scopes when a downstream soft policy intentionally refines or overrides the same rule domain.

Example:

```text
organization soft rule:
service_api_protocol → prefer rest

project soft rule:
service_api_protocol → prefer grpc
```

The project rule is effective for that project scope.

A scope may override one soft rule in a policy domain without restating sibling rules. Omitted sibling rules continue to resolve from applicable ancestor scopes.

Example:

```text
personal:
repository_owned_name_style → lowercase_snake_case
branch_naming_pattern       → <type>_<scope>_<goal>
commit_naming_pattern       → <type>(<scope>): <imperative summary>

project:
branch_naming_pattern       → feature/<ticket>/<description>

project effective policy:
repository_owned_name_style → lowercase_snake_case
branch_naming_pattern       → feature/<ticket>/<description>
commit_naming_pattern       → <type>(<scope>): <imperative summary>
```

## external_contracts

A policy may explicitly defer to an external mandatory naming or integration contract.

Example:

```text
repository_owned_name_style
→ use lowercase_snake_case for names owned by the project
→ preserve exact external contract names such as AGENTS.md, CLAUDE.md, Dockerfile, or other tool-required names
```

External mandatory contracts are boundaries, not downstream soft-policy overrides.

## duplicate_and_conflict_handling

Exact duplicate rules with the same effective meaning should be deduplicated in composed context.

For the same `rule_id`:

```text
hard + hard differing meaning
→ retain applicable hard requirements if compatible
→ otherwise explicit conflict

soft + soft
→ resolve by scope authority and specificity

hard + soft conflict
→ hard wins; soft cannot weaken hard
```

Rule IDs help identify the conflict domain but do not authorize weakening a hard rule.

## rule_text

Rule text should be concise, normative, and independently understandable.

Prefer explicit terms such as:

```text
must
must_not
should
should_not
prefer
require
```

Avoid embedding long rationale in the rule itself.

If rationale is important, keep it below the rule or in a referenced decision/evidence artifact so normal runtime loading can remain compact.

## operators

M1 merge operators apply only where permitted:

```text
add
→ may add hard or soft rules

remove
→ may target removable soft rules
→ never removes hard rules

replace
→ may replace an overridable soft-policy target
→ never weakens or replaces applicable hard rules
```

A future machine-readable operator schema may target policy rule IDs directly. V1 requires stable IDs now so that later tooling does not depend on fuzzy text matching.

## provenance

At minimum, policy provenance is identified by:

```text
policy_module_path
rule_id
rule_type: hard | soft
governing_scope
```

The rule type is derived from its section rather than repeated per rule.

## token_efficiency

Policy files should contain compact active rules.

Long examples, validation scenarios, implementation tutorials, and repeated M1 explanations belong outside runtime policy modules.

Rationale should be loaded progressively only when required.

## acceptance

A compliant policy module allows a resolver to determine without guessing:

- which scope governs the rule;
- which descendant scopes may receive it;
- whether the current task makes the rule applicable;
- whether the rule is hard or soft;
- the stable identity of the rule;
- whether a downstream rule may override it;
- whether sibling soft rules remain inherited when one rule is overridden;
- whether a conflict must be surfaced;
- whether the rule is accessible to AI.
