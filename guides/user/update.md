# Update Personal-SoT

Start with:

```text
Update my Personal-SoT.
```

or:

```text
@do:setup
```

Setup can route an existing installation into the Safe Update workflow.

## Simplest local update

If your AI client can run commands in your private `sot`, you should normally
only need to say:

```text
Update my Personal-SoT.
```

The local agent should use the repository-owned Safe Update runner and show you
one preview to confirm. You should not have to copy SHAs, digests, branch names,
or Git commands.

If you are working directly in a terminal, run one command from your private
`sot`:

Linux/macOS:

```bash
python3 update.py
```

Windows:

```bat
py -3 update.py
```

The runner inspects the installation, shows the beginner-safe preview, asks
`Apply this update? [y/N]`, then applies and validates only after that
confirmation. If the available update changes while you are confirming, it
refreshes the preview and asks again instead of applying stale approval.

## What happens

```text
inspect installation
→ compare with sot public
→ show preview
→ you confirm
→ apply
→ validate
→ report
```

Nothing material is applied before you confirm the exact preview.

## Git installation

For a Git-backed private `sot`:

- user-owned changes are preserved when they can be classified safely;
- product updates come from `sot public`;
- unsaved local work must be saved first with a local commit;
- the updater does not silently commit, stash, reset, or clean your work.

Never push Personal commits to:

```text
mrAlishah/Personal-SoT
```

That is `sot public`, not your private storage.

## No-Git installation

For a downloaded/no-Git installation:

```text
old folder stays unchanged
→ new side-by-side folder is built
→ validate
→ use only if ready
```

## If something is blocked

A conflict or validation failure is not forced through and is not reported as success.

Use:

```text
@do:fix
```

If the installation changes after a preview, the old confirmation becomes invalid and a new preview is required.

## Web/read-only clients

A client that cannot run local commands cannot honestly inspect, apply, or validate your real update. Use an authorized local environment for the actual update.

## Remember

```text
private sot = your data and working state
sot public  = reusable product source
```
