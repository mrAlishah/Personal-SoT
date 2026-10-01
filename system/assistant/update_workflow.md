# update_workflow

## Purpose

Routes a natural-language update request ("update my Personal-SoT") through
the existing Safe Update owners and renders a truthful, beginner-safe result.
This workflow is thin routing/presentation — it is never a second update
engine. See `system/update/update_contract.md` for the actual classification,
apply/recovery, and migration semantics it routes to, and
`system/assistant/update_reporting.py` for the executable presentation glue.

## Flow

```text
[1 Check current installation]
→ [2 Show update/preservation/conflict summary]
→ [3 Preview]
→ [4 Confirm]
→ [5 Apply or provide handoff]
→ [6 Validate/report]
```

This is the same `Explain → Recommend → Preview → Apply` pattern as every
other guided flow (`system/assistant/guided_flow_contract.md`).

## Install-type routing

Step 1 determines whether the installation is a real Git clone/worktree or a
downloaded/no-Git archive using actual host/repository evidence (the smallest
existing Git probe through the controlled Git boundary — `.git` may be a file,
as in a linked worktree, not only a directory). It never infers this from how
the user describes their install ("I cloned it" / "I downloaded a ZIP").

- Git clone/worktree → routes to `system.update.git_update`.
- No-Git archive → routes to `system.update.side_by_side`.
- Neither provable → the route fails closed and the workflow explains what
  capability is missing, rather than guessing.

## One material question at a time

The workflow asks the user only what the host cannot already determine
(e.g. a destination folder for a no-Git archive update). It never asks the
user to identify their install type.

## Capability is host-truth, not prompt text

Read/preview, canonical write/apply, and local command/validator execution
are three independent, trusted host inputs this workflow is given, never
parsed from the user's message. A client that cannot prove write and local
command capability can preview but can never cause `apply`/`migrate` to run,
regardless of what the user says or "confirms".

## Preview is non-mutating; apply requires exact confirmation

Every call recomputes a fresh preview and digest from current state. Apply
or migrate proceeds only when the caller passes back that exact digest as
confirmation. A stale digest, or a plan that changed in the meantime
(conflict, new unsafe path, a different exclusion choice), never applies —
the workflow reports that a new preview is required. Re-verification of
staleness is itself owned by Loop 1–4 (`classify`/`preview` re-run fresh, and
`apply`/`migrate` independently re-verify before mutating); this workflow
does not duplicate that logic, only gates on its result.

## No-write handoff

A host without canonical write/local-command capability may explain, check,
and build a preview, but must state plainly that nothing was written and
that validation was not run here (see
`system/assistant/safe_write_contract.md`). An explicit user confirmation
never upgrades that capability.

## Beginner privacy

Default output names only safe area/count concepts (`workspace: 3 item(s)
preserved`), never a Personal path, filename, or content fragment — see
`system/assistant/update_reporting.py`'s beginner report builders, which
consume Loop 1–4's own already-reviewed Plan/Preview/Result objects rather
than re-deriving disclosure decisions.

## Advanced authorization

A `workspace/context/*.md` path may be named in Advanced detail only when
`system.context.access.permitted(...)` returns `True` for it, called
directly with honestly-sourced inputs (a bounded host-side header read, the
canonical registry scope, and trusted host/deployment capability — never
derived from user/chat/prompt text). `advanced=True` alone authorizes
nothing; it is a presentation toggle, exactly as in `doctor.py`. Product/
implementation detail (commit SHAs, baseline provenance, recovery flags) may
appear in Advanced output freely, since it was never Personal in the first
place.

## Dirty Git clone guidance

When the Git route reports unresolved local changes, the beginner message
explains that those changes must first be saved in local Git history, that
they must never be pushed to the public `mrAlishah/Personal-SoT` repository,
and that the updater itself never commits, stashes, resets, or cleans them.

## Acceptance

- Routes to the correct canonical owner from real host evidence only.
- Never reclassifies, applies, migrates, recovers, or validates itself.
- Never exposes a Personal path/filename/content in beginner output.
- Names a Personal path in Advanced output only via a real `permitted()` call.
- A no-write client's confirmation never causes a write.
- A stale confirmation never applies a recomputed plan silently.
