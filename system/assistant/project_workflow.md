# Project workflow

## Purpose

Define the client-neutral create, use, and current-state maintenance flow for Personal projects.

Git/validation routing follows `system/governance/change_policy.md`.

## Create

### Discover

Understand the intended project and search existing registered scopes and project directories for an exact or overlapping owner. Prefer reuse or update over a duplicate project.

### Interview

Use `system/assistant/guided_flow_contract.md`. Ask only questions whose answers affect a canonical owner. Typical concerns are:

```text
purpose and scope boundary
desired outcome
known current state
material constraints
success signal
```

These are concerns, not a fixed questionnaire. Infer clear supplied answers, adapt to the project type, and ask one material question at a time.

### Classify

Propose a friendly label and a `lowercase_snake_case` project identifier. The logical scope is:

```text
personal/projects/<project_id>
```

The physical owner is:

```text
workspace/context/personal/projects/<project_id>/
```

Create only justified modules from `system/context/module_catalog.md`:

- `project.md` for stable identity, purpose, and scope;
- `current_state.md` for known effective state;
- `objectives.md` only for independently useful outcomes;
- `constraints.md` only for material project-specific limitations;
- other established project modules only when the answers actually require them.

Every created context module requires explicit `ai_access`. Do not create empty placeholders.

### Register and preview

The same proposal adds the exact Personal/project scope mapping to `system/routing/context_registry.md`. Check for duplicate scope, target, identifier, or overlapping ownership first.

Creating project modules plus their private scope registration is `private_context_structure`, not a reusable registry-system change.

Preview the understood project, proposed identifier, semantic modules, access state, registry mapping, complete new content, and excluded items. Then request explicit confirmation through `system/assistant/safe_write_contract.md`.

### Write and persist

On a host with real write capability, re-check current owners/ref and apply the confirmed project files plus registry mapping directly to the current private `main`; a short-lived branch is not required for this private context structure.

Full unit tests and `validate_public.py` are not required for project creation.

When local-command capability exists, run the targeted structural validator:

```text
python3 -B system/validation/validate_v1.py --mode personal
```

When a web/remote client can write but cannot run local Python, it may still apply the confirmed structural change and must report that targeted validation was unavailable.

Persist with commit + push when the host exposes those capabilities. A remote provider commit directly to private `main` is already persisted remotely.

On a no-write host, return the same proposal and say nothing was written.

## Use

Resolve natural references such as "my German-learning project" against registered project identities and friendly project content. If one exact project resolves, use its logical scope and load only relevant accessible owners. If several projects plausibly match, ask the user to choose; do not guess.

Teach natural usage first, for example:

```text
Using my German-learning project, what should I work on next?
```

Then optionally show:

```text
@ctx:personal/projects/german_learning
```

An explicit valid scope remains authoritative.

## Update current state

1. Resolve exactly one registered project.
2. Read the minimum current project owners.
3. Ask what changed only when the evidence is not already clear.
4. Classify each candidate as current state, objective, constraint, decision, temporary history, or unresolved.
5. Keep `current_state.md` as current effective state, not an append-only activity log.
6. Reconcile duplicates and conflicts with existing owners.
7. Classify the Git/validation flow:
   - existing-module content only → `private_context_content`;
   - new/deleted/moved module, registry change, or `ai_access`/frontmatter identity change → `private_context_structure`;
   - any runtime/product semantic change → `system_change`.
8. Preview the exact diff and exclusions.
9. After explicit confirmation, re-read the affected owners/current ref.
10. For `private_context_content`, write directly to private `main`, commit/push when capable, and do not run Python tests or validators.
11. For `private_context_structure`, write directly to private `main`, commit/push when capable, and run only the targeted Personal validator when local-command capability exists.
12. Report the update and one useful next request.

Do not silently change objectives, constraints, decisions, access state, registration, or ownership while updating current state. If such a change is justified, show it explicitly in the same proposal or defer it.

## Web clients

A web client with verified repository write capability may perform the same confirmed direct-private-main update. Do not require a local branch merely because the client is web-based.

If the web client has read-only access, return the preview; confirmation does not create write permission.

## Acceptance

A compliant project flow keeps ordinary project updates simple:

```text
request
→ preview
→ confirm
→ private main update
→ commit/push
→ report
```

It escalates only structural context to targeted validation and only real system/product changes to the engineered branch/full-validation flow.
