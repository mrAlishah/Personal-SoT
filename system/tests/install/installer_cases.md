# One-click installer cases

These scenarios validate `system/install/install_contract.md`.

## Case 1: fresh Linux/macOS GitHub installation

A clean `sot public/main` clone runs `./install.sh` and supplies an empty,
private GitHub repository with working read/write credentials.

Expected: public source fast-forwards only when safe, public validation passes,
preview is shown, `origin` becomes private, `upstream` remains public with
push disabled, initial push succeeds, Doctor passes, and the final handoff is
`@do:sot` then `@do:setup`.

## Case 2: Windows launcher

The same clean clone runs `install.bat`.

Expected: the batch file selects Python launcher capability and invokes the same
`system/install/installer.py` owner. No Windows-specific install semantics are
duplicated in the batch file.

## Case 3: public GitHub destination

The destination GitHub repository is public.

Expected: fail before remote conversion or push. Never treat a non-canonical
public fork as a safe private origin.

## Case 4: destination equals sot public

The user enters `mrAlishah/Personal-SoT` as destination.

Expected: fail closed before mutation.

## Case 5: non-empty first-install repository

The proposed private GitHub repository already has refs.

Expected: first install fails rather than overwriting, force-pushing, merging,
or guessing how to reconcile unrelated state.

## Case 6: failed initial private push

Remote conversion began but the initial push fails.

Expected: attempt to restore the original public `origin` topology and report
failure. Never report ready.

## Case 7: later Git update

The installer is rerun from a valid private Git topology.

Expected: re-prove `origin` is private and writable, route through
`system/update/git_update.py`, preview/confirm using its digest, run Doctor,
then push to private origin without force.

## Case 8: origin changed to another public repository

A previously installed private `origin` is replaced with a public GitHub repo.

Expected: update fails before Safe Update/private push. Private state is never
pushed merely because origin is not the canonical public repository.

## Case 9: Drive first install

A clean public clone receives a valid Google Drive folder URL and a corresponding
empty local folder already synchronized/mounted by trusted host tooling.

Expected: explain that the URL is identity, not credential capability; warn that
Drive sharing privacy is not provable from local filesystem state; stage the
canonical public distribution, validate it, run Doctor, then move the staged
copy into the local Drive path.

## Case 10: Drive URL without local path

The user provides a Drive URL but no local sync/mount location.

Expected: interactive mode asks for the local path. Non-interactive callers must
provide `--drive-path`; no OAuth flow or token storage is invented.

## Case 11: Drive/no-Git update

The installer runs from an existing no-Git Personal-SoT folder.

Expected: use `system/update/side_by_side.py`, create a new sibling candidate,
preserve the original unchanged, validate the candidate, run Doctor, and report
the new folder as the copy to open.

## Case 12: no-Git conflict or unsafe content

Side-by-side preview reports conflicts, manual review, or unsafe input.

Expected: no migration; recommend `@do:fix`.

## Case 13: Doctor blocks

Transfer/update reaches a candidate but Doctor has a blocking finding.

Expected: never print the ready handoff as successful. Report that the system
needs attention and direct the user to `@do:fix`.

## Case 14: credentials

Git credentials, OAuth tokens, refresh tokens, service-account secrets, and
provider cookies exist only in external credential/provider tooling.

Expected: installer arguments, generated repository files, diagnostics, and
canonical SoT never contain secret values.

## Acceptance

The feature is compliant when both OS launchers share one Python owner,
GitHub installs are private-only, Drive remains no-Git/local-sync based,
repeat runs reuse canonical Safe Update owners, Doctor gates readiness, and
successful completion hands the user to `@do:sot` then `@do:setup`.
