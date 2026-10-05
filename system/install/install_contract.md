# One-click install contract

## Purpose

Define the cross-platform mechanical path from a clean clone of `sot public`
to a validated private `sot`, and the repeatable update path thereafter.

The installer reduces terminal work. It does not bypass source binding,
Safe Update, Doctor, safe-write semantics, provider authentication, or public/private boundaries.

## Entry points

Linux/macOS:

```text
./install.sh
```

Windows:

```text
install.bat
```

Both are thin launchers for:

```text
system/install/installer.py
```

The Python installer is the single semantic owner. Shell/batch files must not
reimplement provider, update, validation, or safety logic.

## Supported starting states

```text
clean sot public Git clone
→ first private installation

private Git installation with origin=private
→ Git Safe Update
→ local upstream may be canonical public or absent after a re-clone

no-Git Personal-SoT installation
→ side-by-side Safe Update
```

Unknown, dirty, ambiguous, or incompatible states fail closed.

## GitHub private installation

Initial GitHub installation requires:

- a clean `sot public` clone on `main` whose HEAD exactly equals current canonical `sot public/main`;
- an exact GitHub repository URL;
- proof the destination exists and is not public;
- proof current Git credentials can read and dry-run push;
- no active Git URL rewrite rules that could redirect the chosen destination;
- an empty destination repository.

The installer then creates this topology:

```text
origin   → user's private GitHub repository
upstream → mrAlishah/Personal-SoT
```

`upstream` keeps the canonical public fetch URL, but its push URL is set to
the same private destination as `origin`; `remote.pushDefault` is also set to
`origin`. Therefore ordinary/default pushes and even an accidental
`git push upstream` remain private, while fetch authority stays canonical
`sot public`.

If remote conversion or the initial private push fails, the installer attempts
to restore the original public-origin topology and must not report success.

## Git update

An existing private Git installation routes update planning/apply through the canonical updater. A private repository cloned onto another machine may have only `origin=private`; that is valid because remotes such as `upstream` are local Git configuration and Safe Update resolves its public authority independently:

```text
system/update/git_update.py
```

The installer does not perform ad-hoc pull/merge/reset/stash logic.

It:

1. builds the canonical Safe Update plan;
2. shows a bounded preview;
3. obtains one explicit installer confirmation;
4. applies using the preview digest;
5. runs Doctor;
6. pushes the resulting commit to private `origin` without force.

A failed private push is reported as a partial state: local update may have
succeeded, but remote synchronization did not. It is never reported as fully complete.

## Google Drive installation

A Google Drive URL identifies the intended Drive folder but does not itself
provide filesystem or OAuth capability.

V1 writes only to an existing local filesystem location that the user has
already synchronized or mounted through Google Drive Desktop, rclone mount, or
equivalent trusted host tooling.

The installer:

- validates the Google Drive folder URL shape;
- asks for (or accepts via `--drive-path`) the corresponding local synced/mounted path;
- never stores OAuth/access/refresh tokens;
- never treats Drive as a Git remote;
- creates a no-Git Personal-SoT distribution from canonical `sot public/main`;
- stages and validates before moving the initial copy into place.

The Drive URL is not written into canonical Personal-SoT content.

## No-Git / Drive update

A no-Git installation routes through:

```text
system/update/side_by_side.py
```

The update is created in a new sibling directory. The original folder is not
modified. The installer shows the new path after validation and the user opens
that new copy for subsequent work.

This deliberately preserves the existing Safe Update invariant rather than
inventing in-place Drive mutation.

## Runtime handoff boundary

The installer owns mechanical storage/topology/readiness only. It does not
invent Personal facts, a default factual scope, restricted-context authorization,
or a user Profile merely because the destination is private.

The repository adapters already define the opened repository root as the
canonical SoT root. After installation:

```text
open/connect private repository root
→ @do:sot
→ source/runtime re-anchor to that private root
→ @do:setup
→ guided onboarding/configuration
```

The initial `public_bootstrap.md` remains intentionally onboarding-safe until
the user's confirmed setup creates/configures durable Personal state. Private
repository visibility by itself is not authorization to load restricted facts.

## Validation

Initial public source:

```text
validate_public.py
```

Installed/updated target:

```text
system/diagnostics/doctor.py
```

The installer never reports ready when a blocking Doctor finding is present.

## Completion

A successful install/update ends with:

```text
@do:sot
@do:setup
```

These are instructions for the AI client; the shell installer does not pretend
to execute conversational runtime actions itself.

## Security

The installer:

- never accepts embedded provider credentials as canonical configuration;
- never stores GitHub/Google OAuth tokens in the repository;
- never pushes private data to `sot public`;
- never force-pushes the private destination;
- never treats user confirmation as provider permission;
- never reports a validator/Doctor pass that did not execute successfully.

## Acceptance

The installer is compliant when Linux/macOS and Windows launch the same Python
owner, initial GitHub conversion is private-only and recoverable, Drive uses a
real local sync/mount rather than fake Git semantics, repeat runs route to the
existing Safe Update owners, Doctor gates readiness, and the final user handoff
is `@do:sot` then `@do:setup`.
