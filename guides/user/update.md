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

For a Git installation on `main` whose `origin` is a supported GitHub
private-workspace repository, the same command then offers a **separate,
explicit confirmation** to reconcile and push to `origin/main`. This step
fetches the private branch, merges without discarding Personal files,
accepts existing one-line or two-line context registry entries, validates
the entire combined result (and tests system changes), commits and pushes
only after success. Nothing is pushed to `sot public`.

The private origin must be verifiably non-public to unauthenticated GitHub
requests, and local Git credentials must already be configured. If the
private repository is public, unverified, unavailable, changed concurrently,
or the merge fails validation, the tool stops without forcing a push. A
failed merge is aborted where safe; a push rejection leaves the validated
local commit available for a later retry. The tool reports local success
and remote sync success as **different** outcomes.

Use `--local-only` to skip the private sync offer. `--preview` remains
read-only and `--confirm-digest` applies only the existing public update
transaction; scripted clients must explicitly manage private publication.

## If an update fails (Windows / macOS / Linux)

The normal command prints a safe `failure_code` on failure. To capture
stage-by-stage diagnostics in a **new** log file outside the private SoT,
use a fresh log filename each time:

Windows PowerShell:

```powershell
py -3 update.py --verbose --log-file "$env:TEMP\sot-update-diagnostic.log"
```

Linux/macOS:

```bash
python3 update.py --verbose --log-file /tmp/sot-update-diagnostic.log
```

The command still requires confirmation to apply changes; `--verbose`
and `--log-file` do **not** authorize an update. For a read-only diagnostic
preview, add `--preview`.

The report includes fixed step names and statuses, plus a bounded failure
code. It never intentionally includes Personal contents, raw Git stderr,
user-owned filenames, or secrets. Review the file before sharing it.
A stage marked `started` without `passed` identifies the operation
being attempted, not proof of its exact root cause.

The log must be outside the installation and will not overwrite an
existing file. If the filename is already used, choose a new one.

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

### One-time recovery for installations with an older updater

An older private installation may stop at a conflict **before** it can
install this guided-resolution feature. If you have a separate, clean clone
of the released public `Personal-SoT`, run its latest updater **against**
your existing private installation (do not manually copy files or overwrite
your private Git history):

```bash
cd ~/Projects/Personal-SoT
git switch main
git pull --ff-only origin main
python3 -B update.py --root ~/Projects/myPersonal-SoT
```

The `--root` argument selects the private installation to inspect/update;
the executable and update implementation come from the released public
checkout. It still asks for each genuine conflict choice, shows the final
preview, performs the normal candidate validators, and offers authorized
private-origin synchronization after a successful update. Keep your private
installation's own `main` clean before starting. Never point `--root`
at the public clone for your private update.

If both Public and Private changed the same file, the Git updater now offers
a guided choice for each conflicting item. You will see numbered entries
with a general area name, not private filenames. Choose **Public** to
accept the new released version of that entire file, or **Private** to
preserve your existing file. Review the resulting preview and confirm
before any change. If unsure about a choice, cancel; no file changes.
The updater validates the combined candidate and keeps its normal rollback
and concurrency protections. Noninteractive preview mode does not guess
conflict choices.

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
