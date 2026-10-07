# Development conventions

## Repository-owned names

Prefer `lowercase_snake_case` for repository-owned files, directories, identifiers, and internal paths.

## Change routing

Resolve branch and validation requirements through:

```text
system/governance/change_policy.md
```

Do not create a branch or run a full test suite merely by habit when the policy class does not require it.

## Branches

When a branch is required, use:

```text
<type>_<scope>_<goal>
```

Direct-branch flows explicitly allowed by the change policy do not create a bookkeeping branch.

## Commits

Use:

```text
<type>(<scope>): <imperative summary>
```

Canonical types:

```text
feat
fix
refactor
test
docs
chore
```

Keep commits small and coherent. Run only the validation level required by the resolved change class before claiming validation success.
