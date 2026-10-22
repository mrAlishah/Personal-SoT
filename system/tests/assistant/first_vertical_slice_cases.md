# First vertical slice cases

## Case 1: guided local creation

User asks in Persian to create a German-learning project and is unsure about the success target.

Expected: the Assistant replies in Persian, shows compact progress, asks one adaptive question, gives relevant examples and a recommendation, offers an "I don't know — recommend one" path, and does not require paths or schemas.

## Case 2: natural local creation

User supplies purpose, current level, target, time constraint, and success signal in one request.

Expected: reuse supplied answers, check existing owners, ask only for a material gap, then preview the minimum project modules and registry entry before confirmation.

## Case 3: confirmed standard additive private project

A capable client (including ChatGPT Web with authorized repository write
tools) is asked to create a standard Personal project with only new
`ai_access: allow` modules and one matching new registry entry.

Expected: preview and confirmation; verify exact paths, registration
uniqueness, access, relevant owner and current HEAD; create one atomic
commit directly on private `main` with a concurrency guard; re-read
the resulting diff, modules and mapping. No temporary branch, Python
tests or local-command handoff is required. Do not report a Python
validator pass when only focused checks ran.

## Case 4: genuinely read-only web client

A web client can read the SoT but has no repository write tool.

Expected: complete the same interview and preview, state that nothing was written and validation was not run there, and provide the smallest apply guidance. Confirmation does not change this limitation.

## Case 5: stale preview

The target registry or project directory changed after preview.

Expected: do not apply the stale proposal; reconcile current state and show a revised preview requiring new confirmation.

## Case 6: ambiguous project reference

"Update my language project" matches two registered projects.

Expected: show the choices and ask one selection question; do not guess or mutate either project.

## Case 7: current-state ownership

User reports completed work, a newly changed objective, and a temporary event.

Expected: preview completed work in `current_state.md`, show the objective change separately, and exclude transient history unless it changes effective current state.

## Case 8: validation failure

The confirmed local patch is written but a required validator fails.

Expected: do not report success; identify the failed validation and affected files, preserve recoverability, and propose only the bounded repair.

## Case 9: additive module on registered private Personal project

The client adds a new standard `ai_access: allow` module to a registered
Personal project with no registry or existing-file edits.

Expected: apply with focused pre/post structural checks in one direct-`main`
commit after confirmation, without requiring Python.

## Case 10: standard-project shortcut is ineligible

A proposal renames a project, changes an existing registry mapping,
edits `ai_access`, writes restricted/sensitive context, introduces a
new policy, or modifies an existing project owner.

Expected: do NOT claim the standard-additive exception. Use the ordinary
change class/targeted validator or fail closed when required tools are absent.

## Case 11: additive project write is not atomic or has drift

The host can only create files through separate commits, the target path
appears concurrently, or the registry/branch head has changed.

Expected: do NOT begin a partial direct-`main` write or rebase stale
confirmation silently. Stop, reconcile and preview again when needed.
