# Update Personal-SoT

You do not need to understand merge bases, commit SHAs, or registry internals.

Start with:

```text
Update my Personal-SoT.
```

You may also run:

```text
@do:setup
```

Setup is re-runnable and can route an existing installation into the Safe Update workflow.

## The update flow

```text
1. inspect current installation
2. compare with sot public
3. show a preview
4. you confirm
5. apply safely
6. validate
7. report the real result
```

Nothing material is applied before you confirm the exact preview.

## Git installation

For a Git-backed private `sot`, the updater preserves user-owned changes and applies reusable product updates only when it can classify them safely.

If you have unsaved local changes, save them first with a **local commit**.

Do not push Personal commits to:

```text
mrAlishah/Personal-SoT
```

That repository is `sot public`, not your private storage.

The updater does not silently commit, stash, reset, or clean your work.

## Downloaded / no-Git installation

For an installation without Git, Safe Update creates a new side-by-side folder.

```text
old folder
→ remains untouched

new folder
→ updated candidate
→ validate
→ use only if ready
```

A failed update must never be reported as successful.

## Preview means preview

Before writing anything, the Assistant shows what will happen.

Typical result:

```text
preserve these private/user-owned items
update these reusable product files
these conflicts need a decision
validation that will run
```

If the installation changes after the preview, the old confirmation is no longer valid. A new preview is required.

## What success means

```text
Applied + validation passed
→ update is ready

Already current
→ nothing changed

Blocked / conflict
→ nothing unsafe is forced through

Validation failed
→ do not call the system ready
```

If an update is blocked, use:

```text
@do:fix
```

## Web/read-only clients

A client that cannot run local commands cannot honestly inspect or update your real installation.

It may explain the process, but a real preview/apply/validation must happen in an authorized local environment.

## Simple rule

```text
private sot = your data and working state
sot public  = reusable product source
```

Never push Personal data to `sot public`.
