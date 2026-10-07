# Project workflow

## Purpose

Define the client-neutral create, use, and current-state maintenance flow for Personal projects.

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

The same proposal adds the exact scope mapping to `system/routing/context_registry.md`. Check for duplicate scope, target, identifier, or overlapping ownership first.

Preview the understood project, proposed identifier, semantic modules, access state, registry mapping, complete new content, excluded items, and validation command. Then request explicit confirmation through `system/assistant/safe_write_contract.md`.

### Write and validate

Project creation changes owner/registry structure, so classify it as a structural context change through `system/governance/change_classification.md`.

On an authorized write-capable host, revalidate and apply project files plus registry mapping as one coherent patch. In a private Personal-SoT workspace, run the targeted Personal structural validator:

```text
python3 -B system/validation/validate_v1.py --mode personal
```

Do not run `validate_public.py` merely because a private project was created; public-distribution certification is a different concern. Run another validator only when the confirmed proposal also changes the domain it owns. Never claim project creation if the patch or required validation failed.

On a host that can write but cannot run the required targeted validator, leave the change in the reviewable state required by active repository governance and report validation as unavailable; do not claim accepted success. On a no-write host, return the same proposal, say nothing was written and validation was not run, and provide apply guidance without changing semantics.

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
3. Ask what changed when the evidence is not already clear.
4. Classify each candidate as current state, objective, constraint, decision, temporary history, or unresolved.
5. Keep `current_state.md` as current effective state, not an append-only activity log.
6. Reconcile duplicates and conflicts with existing owners.
7. Preview the exact diff and exclusions.
8. Classify the proposal through `system/governance/change_classification.md`. An ordinary edit to existing owners is a context update; creating/removing owners, changing registry/routing, or changing `ai_access` is a structural context change.
9. Confirm, revalidate, and write through the safe-write contract. For an ordinary private context update, no Python validator is required solely for the content edit. For a structural context change, run only the targeted structural validator(s).
10. Report the update and one useful next request.

Do not silently change objectives, constraints, decisions, or access state while updating current state. If such a change is justified, show it as a separate owner in the same proposal or defer it for clarification.

## Acceptance

A compliant vertical slice can create the minimum valid project and registry entry, resolve and use it by natural language, update current effective state without ownership drift, classify creation as structural and ordinary state maintenance as a context update, apply only the checks required by that class, and preserve identical preview semantics on clients that cannot write.
