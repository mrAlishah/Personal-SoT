# First vertical slice cases

## Case 1: guided local creation

User asks in Persian to create a German-learning project and is unsure about the success target.

Expected: the Assistant replies in Persian, shows compact progress, asks one adaptive question, gives relevant examples and a recommendation, offers an "I don't know — recommend one" path, and does not require paths or schemas.

## Case 2: natural local creation

User supplies purpose, current level, target, time constraint, and success signal in one request.

Expected: reuse supplied answers, check existing owners, ask only for a material gap, then preview the minimum project modules and registry entry before confirmation.

## Case 3: confirmed capable write

The local agent has authorized repository write capability and the user confirms an unchanged proposal.

Expected: re-read affected state, apply project files and registry entry coherently, run Personal and public validators, and report only their actual results.

## Case 4: web preview only

ChatGPT or Claude Web can read the SoT but has no repository write tool.

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
