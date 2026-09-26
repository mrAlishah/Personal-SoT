# personal_project_examples

This directory demonstrates fake personal-owned project scopes.

## canonical_runtime_shape

When copied into a personal overlay, a personal project lives under:

```text
context/personal/projects/<project>/
```

The owner remains `personal`; the project path introduces a more-specific factual scope.

## examples

```text
career_transition/
technical_learning/
```

All data is fake and marked for editing. Nothing under `examples/` is a real registered runtime scope.

## rules

- create only modules with useful project-owned knowledge;
- keep cross-project durable facts at `context/personal/` rather than copying them into every project;
- project-specific objectives/state/constraints belong to the project;
- nested personal projects may be direct child directories without `subprojects/`;
- do not copy parent facts into nested projects to simulate inheritance;
- sensitive project facts remain subject to the sensitive-data contract.

## edit_pattern

```text
EDIT_ME
→ replace fake value

DELETE_IF_NOT_APPLICABLE
→ remove unnecessary content
```
