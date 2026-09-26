# Development conventions

## Repository-owned names

Prefer `lowercase_snake_case` for repository-owned files, directories, identifiers, and internal paths.

## Branches

Use:

```text
<type>_<scope>_<goal>
```

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

Keep branches and commits small and coherent. Run the relevant validators before claiming a change passed validation.
