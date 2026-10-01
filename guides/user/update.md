# Update Personal-SoT

You do not need to understand Git, commit SHAs, merge bases, or registry
internals to update your installation safely.

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

ChatGPT, Claude Web, and similar clients can check your installation and
build a preview, but if they cannot write files or run local commands, they
will say plainly that nothing was written and that validation was not run
there. Use an authorized local agent (Claude Code, Codex) to apply a
confirmed preview and actually validate it.

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
  successful update. If it already started changing things and then hit a
  problem, it tells you whether it was able to safely restore your prior
  state.

## 8. Advanced detail is optional and still access-controlled

If you ask for Advanced/technical detail, you may see implementation detail
like commit SHAs or recovery flags — that detail was never Personal to begin
with. A path under your personal context is only ever named in that detail
when the Assistant can actually prove you are authorized to see it named;
asking for "Advanced" by itself never proves that.
