# One-click installer cases

These scenarios validate `system/install/install_contract.md`.

## Case 1: fresh Linux/macOS GitHub installation

A clean, exact-current `sot public/main` clone runs `./install.sh` and supplies an empty,
private GitHub repository with working read/write credentials.

Expected: the installer proves the clone exactly matches current canonical `sot public/main`,
public validation passes, preview is shown, `origin` becomes private, `upstream` keeps
public fetch authority but routes push to the same private destination,
`remote.pushDefault` is `origin`, initial push succeeds, Doctor passes, and the final
handoff is `@do:sot` then `@do:setup`.

## Case 2: Windows launcher

The same clean clone runs `install.bat`.

Expected: the batch file selects a supported Python 3.10+ launcher and invokes the same
`system/install/installer.py` owner. No Windows-specific install semantics are
duplicated in the batch file, and the Python process exit status is preserved.

## Case 3: stale or locally diverged public clone

The clone is not exactly the currently resolved canonical `sot public/main`
commit, or hardened Safe Update preflight finds dirty/unsafe state.

Expected: fail before provider mutation. The installer does not auto-merge,
reset, stash, or execute a second update engine during first installation.

## Case 4: Git URL rewrite configured

Git configuration contains `url.*.insteadOf` or `url.*.pushInsteadOf`.

Expected: fail before private provider access so the selected GitHub
destination cannot be silently redirected.

## Case 5: public GitHub destination

The destination GitHub repository is public.

Expected: fail before remote conversion or push. Never treat a non-canonical
public fork as a safe private origin.

## Case 6: destination equals sot public

The user enters `mrAlishah/Personal-SoT` as destination.

Expected: fail closed before mutation.

## Case 7: non-empty first-install repository

The proposed private GitHub repository already has refs.

Expected: first install fails rather than overwriting, force-pushing, merging,
or guessing how to reconcile unrelated state.

## Case 8: failed initial private push

Remote conversion began but the initial push fails.

Expected: attempt to restore the original public `origin` topology and report
failure. Never report ready.

## Case 9: later Git update

The installer is rerun from a valid private Git topology.

Expected: re-prove `origin` is private and writable, route through
`system/update/git_update.py`, preview/confirm using its digest, run Doctor,
re-prove the private origin immediately before synchronization, then push to
that private destination without force.

## Case 10: re-cloned private repository has no upstream

The user clones their private `sot` on another machine, so only
`origin=private` exists and the local `upstream` remote is absent.

Expected: recognize it as an installed private Git `sot`, re-prove origin
privacy/write access, and use the canonical Safe Update target directly.
Do not misclassify it as a fresh public clone.

## Case 11: origin changed to another public repository

A previously installed private `origin` is replaced with a public GitHub repo.

Expected: update fails before Safe Update/private push. Private state is never
pushed merely because origin is not the canonical public repository.

## Case 12: Drive first install

A clean public clone receives a valid Google Drive folder URL and a corresponding
empty local folder already synchronized/mounted by trusted host tooling.

Expected: explain that the URL is identity, not credential capability; warn that
Drive sharing privacy is not provable from local filesystem state; stage the
canonical public distribution, validate it, run Doctor, then move the staged
copy into the local Drive path.

## Case 13: Drive URL without local path

The user provides a Drive URL but no local sync/mount location.

Expected: interactive mode asks for the local path. Non-interactive callers must
provide `--drive-path`; no OAuth flow or token storage is invented.

## Case 14: Drive/no-Git update

The installer runs from an existing no-Git Personal-SoT folder.

Expected: use `system/update/side_by_side.py`, create a new sibling candidate,
preserve the original unchanged, validate the candidate, run Doctor, and report
the new folder as the copy to open.

## Case 15: no-Git conflict or unsafe content

Side-by-side preview reports conflicts, manual review, or unsafe input.

Expected: no migration; recommend `@do:fix`.

## Case 16: Doctor blocks

Transfer/update reaches a candidate but Doctor has a blocking finding.

Expected: never print the ready handoff as successful. Report that the system
needs attention and direct the user to `@do:fix`.

## Case 17: credentials

Git credentials, OAuth tokens, refresh tokens, service-account secrets, and
provider cookies exist only in external credential/provider tooling.

Expected: installer arguments, generated repository files, diagnostics, and
canonical SoT never contain secret values.

## Acceptance

The feature is compliant when both OS launchers share one Python owner,
GitHub installs are private-only, Drive remains no-Git/local-sync based,
repeat runs reuse canonical Safe Update owners, Doctor gates readiness, and
successful completion hands the user to `@do:sot` then `@do:setup`.
