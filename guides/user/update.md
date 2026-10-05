# Update Personal-SoT

You do not need to understand Git, commit SHAs, merge bases, or registry
internals to update your installation safely.

## Installer shortcut

If your installation was created with the repository installer, you can rerun the launcher from the private installation:

Linux/macOS:

```bash
./install.sh
```

Windows:

```bat
install.bat
```

A private Git installation routes to the canonical Git Safe Update and pushes only to private `origin`. A no-Git/Drive installation builds a validated side-by-side sibling and keeps the original folder unchanged. The launcher still shows a preview and asks for confirmation before applying the update.

## 1. Ask naturally

```text
Update my Personal-SoT.
```

The Assistant checks your actual installation and tells you what kind of
update applies — you do not need to say whether you cloned the repository or
downloaded an archive; the Assistant can tell from your installation itself.

## 2. Clone vs. downloaded archive

- **Cloned with Git:** your installation updates in place, through a safe,
  confirmed flow — nothing is applied until you confirm an exact preview.
- **Downloaded archive (no Git):** the update is built as a new,
  side-by-side folder next to your original. Your original archive
  installation is never changed, on success or on failure.

## 3. Preview before anything happens

Before anything is written, the Assistant shows a preview: what would be
preserved, what would be updated, and whether anything needs your decision
(a conflict, or an unsafe item that needs attention). Building this preview
never changes anything.

## 4. Confirm the exact preview

Nothing is applied or migrated until you explicitly confirm that exact
preview. If your installation changes in the meantime — including if you
change which files to keep — the Assistant builds a new preview instead of
applying the old one.

## 5. If your Git clone has unsaved local changes

If you cloned with Git and have local changes the updater cannot safely
classify yet, the Assistant will tell you to save them first:

- Save your local changes with a local Git commit.
- Do **not** push those local commits to the public
  [mrAlishah/Personal-SoT](https://github.com/mrAlishah/Personal-SoT)
  repository — they are yours, not the shared product.
- The Assistant/updater never commits, stashes, resets, or cleans your
  changes for you.

## 6. Web clients and other no-write hosts

A host that can read your installation and run local commands, but cannot
write or validate, still builds the real preview and shows it to you — on
the very first check, not only once you try to confirm — but adds plainly
that nothing was written and that validation was not run there.

ChatGPT, Claude Web, and similar clients typically cannot run local commands
at all, so they cannot actually check your installation or build that
preview themselves. They can explain the workflow in plain language and hand
off to a local agent, but they must not claim to have checked or previewed
your actual installation when they have not. Use an authorized local agent
(Claude Code, Codex) to build a real preview, apply a confirmed one, and
actually validate it.

## 7. What success means

- **Clone, applied:** "Update applied and validation passed." means the
  update was written AND the real validators actually passed against it.
- **Archive, migrated:** "Updated side-by-side copy is ready. Your original
  folder was not changed." — your new, updated copy is ready to use; your
  original archive folder is untouched.
- **Already current:** "You're already current." — nothing needed to
  change.
- **Blocked:** if something failed validation, or the updater could not
  safely finish, it reports that honestly as a failure, never as a
  successful update — a clone update is only ever reported as applied when
  it actually produced a real result, not just because the validators
  happened to run. If it already started changing things and then hit a
  problem, it tells you whether it was able to safely restore your prior
  state.
- **Archive, didn't finish:** if a side-by-side update fails partway
  through, your original folder is still untouched, but the Assistant will
  never say "nothing changed" — it will say plainly that the new copy did
  not finish and is not ready to use.

## 8. Advanced detail is optional and still access-controlled

If you ask for Advanced/technical detail, you may see implementation detail
like commit SHAs or recovery flags — that detail was never Personal to begin
with. A path under your personal context is only ever named in that detail
when the Assistant can actually prove you are authorized to see it named;
asking for "Advanced" by itself never proves that.
