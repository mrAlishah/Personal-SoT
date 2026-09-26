# organization_context_examples

This directory demonstrates fake organization-owned context.

## runtime_shape

```text
context/organizations/<organization>/
context/organizations/<organization>/projects/<project_path>/
```

The examples use a fictional organization and must never be registered as production scopes.

## rules

- organization scope stores organization-wide truth only;
- project scope stores project-owned additions/overrides;
- organization A never implicitly composes organization B;
- personal context never implicitly loads into organization scope;
- project modules do not copy organization truth to become self-contained;
- applicable hard policies accumulate;
- cross-context supplemental composition follows target ownership.

All values are fake and marked `EDIT_ME` where intended for reuse.
