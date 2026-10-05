# Personal-SoT

**A private source of truth for your AI.**

Personal-SoT keeps your projects, preferences, prompts, profiles, and current state in one controlled place so your AI can use the right context without relying on scattered chats.

You do **not** need to learn Git, YAML, repository paths, or prompt engineering for normal use.

## Start here

First time:

```text
1. Clone sot public
2. Run install.sh / install.bat
3. Open your private sot
4. Run @do:sot
5. Run @do:setup
6. Start a real task
```

Source roles:

```text
sot        → your private Personal-SoT
sot public → mrAlishah/Personal-SoT
```

Never store Personal data in `sot public`.

## Important commands

| Command | What it does |
|---|---|
| `@do:sot` | Reconnect/re-anchor this chat to your private SoT. |
| `@do:setup` | Set up, resume, improve, or route an update. |
| `@do:doctor` | Check system health without changing anything. |
| `@do:fix` | Diagnose and safely repair a real problem. |
| `@do:help` | Explain, discover, or recommend. |
| `@do:assist` | Safely create or change something. |

Natural language also works. These commands are shortcuts.

## Quick install

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

The installer can prepare an empty private GitHub repository or an empty local folder already synced by Google Drive. It runs validation and Doctor before reporting success.

Then open the private `sot` in Codex or Claude Code and run:

```text
@do:sot
@do:setup
```

See [Setup](guides/user/setup.md).

## How it works

```text
sot public
    ↓ install / reusable updates
private sot
    ↓
AI client
    ↓
@do:sot
    ↓
@do:setup
    ↓
projects / prompts / profiles / current state
```

The product rule is:

```text
simple outside + rigorous inside
```

You state the outcome. Personal-SoT resolves the right context, reuses existing capabilities, previews material changes, waits for confirmation, validates, and reports what actually happened.

## Typical use

```text
Create a project for learning German.

Update my project. I finished A1.

Find a prompt for reviewing code.

Make my answers shorter.

I don't know what I need — recommend one.
```

If something looks wrong:

```text
@do:doctor
@do:fix
```

## Guides

| Goal | Guide |
|---|---|
| Learn the normal workflow | [Beginner guide](guides/user/readme.md) |
| Install and set up | [Setup](guides/user/setup.md) |
| Diagnose problems | [Doctor](guides/user/doctor.md) |
| Update safely | [Update](guides/user/update.md) |
| Create a project | [First project](guides/user/create_and_use_project.md) |
| Find/build prompts | [Prompt discovery](guides/user/find_and_use_prompts.md) / [Prompt builder](guides/user/build_a_prompt.md) |
| Customize responses | [Customization](guides/user/customize_responses.md) |
| Develop the public product | [Developer guide](guides/developer/readme.md) |

## For developers

```text
develop
→ short-lived branch
→ tests + validators + review
→ PR to develop
→ explicit release
→ main
```

Reusable runtime semantics belong in `system/`. Personal facts and private deployment state never belong in the public product.

## Safety

Keep passwords, tokens, private keys, recovery codes, one-time codes, session cookies, and payment credentials outside Personal-SoT.

Material saved changes follow:

```text
preview → confirm → re-check → write → validate → report
```

Repository map:

```text
workspace/  user-owned content/configuration
system/     runtime + validation + tests
guides/     user/developer documentation
```
