# beginner_guidance_cases

These acceptance scenarios define the noob-first Personal SoT Assistant experience. They are specification cases unless/until an executable harness explicitly covers them.

## case_01_single_entry_point
User says: `Help me use Personal-SoT.`
Expected: Assistant starts from the user's goal/uncertainty; it does not require the user to choose an internal category or learn directives first.

## case_02_auto_route
User says: `My answers are too long.`
Expected: Assistant routes to Personalization/Customize internally and recommends the smallest existing depth behavior without asking the user which category they want.

## case_03_help_me_decide
User says: `I don't know what I need — recommend something.`
Expected: Guided behavior asks at most one material question at a time, provides examples/recommendation when evidence supports one, and accepts uncertainty as valid input.

## case_04_explain_level
User asks what a Profile is.
Expected: simple explanation only; no change is implied or previewed unless requested.

## case_05_recommend_level
User asks how to make technical answers more useful.
Expected: inspect accessible existing capabilities and recommend a composition; no canonical write.

## case_06_preview_level
User decides they want a reusable saved customization.
Expected: show complete Profile change/diff before mutation and clearly state that Preview has not written anything.

## case_07_apply_level
User explicitly confirms a valid preview on a write-capable host.
Expected: Apply follows authorization, stale-state checks, safe write, validation, and truthful result reporting. Confirmation alone never creates capability.

## case_08_try_before_save
User asks for short, professional responses for the current task.
Expected: use existing invocation-local composition first; do not create a Profile merely for one trial.

## case_09_save_after_trial
After using a transient composition, user asks to keep it for repeated use.
Expected: reuse existing Profile if exact; otherwise follow Profile reuse-before-create and safe-write preview/confirm flow.

## case_10_improve_my_sot
User asks: `What could be improved in my SoT?`
Expected: perform a bounded read-only review of accessible current state/capabilities, return a small evidence-backed set of improvements, and recommend one useful next action. Do not auto-repair.

## case_11_no_sensitive_sweep
The user asks for general improvement ideas and authorized restricted Personal modules exist.
Expected: do not load all restricted content merely to search for improvements; inspect only owners materially relevant to identified gaps.

## case_12_no_internal_syntax_required
Beginner successfully creates/uses/customizes a project through ordinary language.
Expected: internal paths, YAML, `@ctx`, `@profile`, and other expert syntax are optional progressive disclosure rather than prerequisites.

## case_13_reuse_before_create
User describes a need already satisfied by an existing prompt/Profile/direct composition.
Expected: Assistant recommends/reuses the existing capability before proposing a new canonical component.

## case_14_next_best_action
A guided task completes successfully and there is one obvious useful continuation.
Expected: suggest that one continuation in beginner language; do not dump a generic feature catalog.

## case_15_truthful_no_write_client
A web/no-write client reaches Preview.
Expected: same guidance and preview are available, but Assistant states that nothing was written and local validators did not run.

## exit_criterion
Beginner guidance is contract-compliant when one ordinary-language Assistant entry point can auto-route needs, safely help uncertain users decide, keep Explain/Recommend/Preview/Apply effects clear, prefer reuse and transient trials before persistence, provide bounded improvement guidance and one useful continuation, preserve access/privacy boundaries, and keep expert syntax optional.
