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
downloaded/no-Git archive using actual host/repository evidence. It never
infers this from how the user describes their install ("I cloned it" / "I
downloaded a ZIP"). One installation-evidence rule covers BOTH routes:
the selected root must carry Personal-SoT's own stable repository-owned
markers (each a genuine regular file at its exact path, never a symlink
standing in for one) before either route is even considered — an arbitrary
directory, or an arbitrary unrelated Git repository that happens to exist at
its own top level, is never treated as this installation merely for
existing or merely for being *some* Git repo. Install type must ALSO be
PROVEN at the exact selected root, not merely somewhere above or below it: a
Git route additionally requires the selected path itself to be the
repository's working-tree top level (so an arbitrary subdirectory nested
inside an unrelated parent repository is never misidentified as the
installation, and a linked worktree — whose `.git` is a file, not a
directory — is still correctly recognized as its own root).

- Git clone/worktree → routes to `system.update.git_update`.
- No-Git archive → routes to `system.update.side_by_side`.
- Neither provable → the route fails closed and the workflow explains what
  capability is missing, rather than guessing.

Every check this step performs is itself a local command/Git execution, so it
never runs at all without local-command capability (below) — a route is never
produced on the strength of filesystem shape alone when the commands needed
to actually confirm it could not run.

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

Local-command capability specifically gates ALL of install-type detection,
classification, and preview — every one of them shells out to Git or a
validator. A client that cannot run local commands at all gets an honest
no-write report immediately, before any of those are even attempted; this
workflow never claims to have checked or previewed an installation using
commands that could not actually execute, and not every web/read-only host
can necessarily run this local Python workflow at all.

## Preview is non-mutating; apply requires exact confirmation

Every call recomputes a fresh preview and digest from current state. Apply
or migrate proceeds only when the caller passes back that exact digest as
confirmation. A stale digest, or a plan that changed in the meantime
(conflict, new unsafe path, a different exclusion choice), never applies —
the workflow reports that a new preview is required. Re-verification of
staleness is itself owned by Loop 1–4 (`classify`/`preview` re-run fresh, and
`apply`/`migrate` independently re-verify before mutating); this workflow
does not duplicate that logic, only gates on its result.

## Success means the result actually succeeded

A Git update is reported applied/ready only when the canonical apply result
itself proves it: a resulting commit, no failure literal, and real validator
success — never inferred from validator flags alone, since a controlled
failure can legitimately have every validator flag set true (object-transfer
failure, or a fully rolled-back post-mutation failure) without the update
having succeeded at all. A rolled-back or recovered update is reported as not
applied, with the prior verified state restored — never as success.

A no-Git (side-by-side) update that fails after copying has already begun is
never reported as "nothing changed": Loop 4 does not promise to delete a
partially built destination on failure, only that the ORIGINAL installation
is never touched. Such a failure always says the original folder was not
changed and that the new copy specifically did not finish and is not ready.

## No-write handoff

Two distinct no-write cases, both always stating plainly that nothing was
written and that validation was not run here (see
`system/assistant/safe_write_contract.md`), but worded differently because
only one of them actually has a preview to show:

- Can read and run local commands, but cannot write: the real preview IS
  built and shown — on the very first call, not only once the user tries to
  confirm — with that notice attached alongside it.
- Cannot run local commands at all (so install-type detection,
  classification, and preview itself cannot run): no preview is claimed to
  exist, since none could actually be built.

An explicit user confirmation never upgrades either case's capability.

## Beginner privacy

Default output names only safe area/count concepts (`workspace: 3 item(s)
preserved`), never a Personal path, filename, or content fragment — see
`system/assistant/update_reporting.py`'s beginner report builders, which
consume Loop 1–4's own already-reviewed Plan/Preview/Result objects rather
than re-deriving disclosure decisions.

## Advanced authorization

A `workspace/context/*.md` path may be named in Advanced detail only when
`system.context.access.permitted(...)` returns `True` for it, called
directly with honestly-sourced inputs (a frontmatter-only host-side header
read, the canonical registry scope, and trusted host/deployment capability —
never derived from user/chat/prompt text). The registry scope always comes
from the CANONICAL `system/routing/context_registry.md` read directly from
the selected installation, never from caller-supplied registry text — a
caller passing its own registry string could otherwise fabricate scope
ownership for a path the installation's own registry never actually
registers. `advanced=True` alone authorizes nothing; it is a presentation
toggle, exactly as in `doctor.py`. Product/implementation detail (commit
SHAs, baseline provenance, recovery flags) may appear in Advanced output
freely, since it was never Personal in the first place.

The one production Advanced view (`advanced_report`) stores and renders only
already-authorized Personal paths and safe product/result facts — never a
raw frontmatter header, a module body, or an unauthorized Personal path, and
nothing resembling a raw header ever survives as hidden state on the result
object the workflow returns. The header read itself is bounded to the
frontmatter block alone (stops at the matching closing `---`, never returns
body bytes even if they would fit within the read limit). This read, the
canonical registry read, and installation-marker proof all share one
root-anchored primitive that is component-safe throughout — every
intermediate directory, not only the final component, must be a real
directory with no symlink anywhere along the path (and the selected root
itself must not be a symlink either), so a symlinked `workspace`, `system`,
or scope directory can redirect none of them outside the selected root.

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
