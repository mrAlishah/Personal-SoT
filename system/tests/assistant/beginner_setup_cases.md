# Beginner setup cases

## Case 1: local beginner

The repository is open in an authorized local agent and the user asks in Persian for help getting started.

Expected: reply in Persian, show compact setup progress, verify the runtime entrypoint, infer the local client capability, and ask only the next material question.

## Case 2: language is already clear

The user explicitly asks to continue in German.

Expected: use German without asking for language again and do not create canonical context merely to remember the conversation language.

## Case 3: optional personal onboarding

The user wants to start a project and provides no reusable personal facts.

Expected: explain that personal onboarding can be skipped, create no empty personal modules, and route to project creation.

## Case 4: useful durable fact

The user voluntarily supplies a stable fact that materially improves several future tasks.

Expected: classify it against the module catalog, preview the minimum owner and `personal` scope registration, and wait for confirmation before a capable-host write.

## Case 5: web client

A web client can read the repository but has no filesystem write or command execution.

Expected: run the same questions and recommendations, produce any requested preview, state that nothing was written, and state that the local system check was not run there.

## Case 6: repository unavailable

The client cannot read the runtime entrypoint.

Expected: report that the repository is not connected, give the smallest client-appropriate connection guidance, and do not claim setup success.

## Case 7: local validation failure

One system-check command fails.

Expected: explain the affected area and smallest next action in beginner language; do not report ready or successful setup.

## Case 8: first useful task

Setup is connected and validation passed.

Expected: introduce the Assistant categories in the selected language, recommend one based on the user's goal, and offer one concrete natural-language request before optional expert syntax.

## Case 9: first-time private installation

The user invokes `@do:setup` from `sot public` and no private `sot` exists.

Expected: explain in ELI5-style language that `sot public` is the reusable source and the new private installation is the future `sot`; guide clone/archive plus private destination/remote as capability allows; never store Personal data in the public source.

## Case 10: rerun after partial setup

A private `sot` exists, but its client wiring or system check is incomplete.

Expected: preserve valid existing state and resume from the smallest missing/broken setup step rather than restarting or overwriting the installation.

## Case 11: rerun on stale healthy installation

A private `sot` is healthy but an update from `sot public` is applicable.

Expected: route to `system/assistant/update_workflow.md`; do not perform an ad-hoc merge/copy inside setup.

## Case 12: rerun on healthy current installation

The private `sot` is healthy and current.

Expected: report ready, avoid unnecessary writes, and offer one useful next task.

## Case 13: real setup defect

Doctor reports a current blocking setup/runtime defect.

Expected: setup explains the finding and routes repair to `system/assistant/fix_workflow.md`; setup itself does not silently repair.
