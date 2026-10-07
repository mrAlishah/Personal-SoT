# Set up Personal-SoT

Setup has one goal:

```text
sot public
→ create/connect your private sot
→ check it
→ start using it
```

You do not need to understand Git, YAML, schemas, or internal paths.

If Personal-SoT is not installed yet, start with the [Install guide](install.md) for prerequisites and OS-specific commands.

## Quick path

### 1. Clone and run the installer

Linux/macOS:

```bash
git clone https://github.com/mrAlishah/Personal-SoT.git
cd Personal-SoT
./install.sh
```

Windows:

```bat
git clone https://github.com/mrAlishah/Personal-SoT.git
cd Personal-SoT
install.bat
```

Choose one destination:

- **GitHub Private** — an empty private GitHub repository.
- **Google Drive** — an empty local folder already synchronized by Google Drive Desktop or equivalent.

A Google Drive sharing URL alone is not a writable local folder.

The installer runs the core checks and Doctor before it reports success.

## 2. Open your private sot

Open the resulting private repository/folder in an authorized AI client such as Codex or Claude Code.

Remember:

```text
sot
→ your private installation

sot public
→ mrAlishah/Personal-SoT
```

Do not put Personal facts or private configuration in `sot public`.

## 3. Connect the chat

Run:

```text
@do:sot
```

This tells the current chat to resolve and reload your canonical Personal-SoT runtime.

## 4. Finish setup

Run:

```text
@do:setup
```

Setup is guided and re-runnable. It may:

```text
new install       → finish initial configuration
partial setup     → continue from the missing step
healthy but stale → route to Safe Update
needs improvement → recommend a small improvement
healthy/current   → report ready
```

It should reuse information already available instead of asking you the same question again.

## 5. Check health

You can run:

```text
@do:doctor
```

Doctor changes nothing.

If it finds a real problem:

```text
@do:fix
```

See [Doctor](doctor.md).

## 6. Start a real task

Examples:

```text
Create a project for learning German.

Help me plan my first week.

Find a reusable prompt for reviewing code.

I don't know what to do first — recommend one.
```

## Manual setup

If you do not use the installer, keep these roles separate:

```text
private sot
→ your user-owned installation

sot public
→ reusable product/update source
```

For a Git installation, the common layout is:

```text
origin   → your private repository
upstream → mrAlishah/Personal-SoT
```

Do not invent repository URLs or permissions. The client must verify what actually exists.

## If your client cannot write

A web/read-only client can still guide setup and show previews. It must not claim that files were written or that local validation ran when it could not perform those actions.

Use an authorized local agent to apply and validate material changes.

## Safety

Never enter passwords, API tokens, private keys, recovery codes, one-time codes, session cookies, or payment credentials into Personal-SoT.

Next: [Beginner guide](readme.md).
