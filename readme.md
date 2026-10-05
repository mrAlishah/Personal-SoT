# Personal-SoT

**A private source of truth for your AI.**

Personal-SoT keeps your projects, preferences, reusable prompts, profiles, and current state in one controlled place so an AI can use the right context without relying on scattered chats.

You do **not** need to learn Git, YAML, repository paths, or prompt engineering for normal use.

## Start in 30 seconds

If this is your first install:

```text
1. Clone sot public
2. Run install.sh / install.bat
3. Open your private sot in your AI client
4. Run @do:sot
5. Run @do:setup
6. Start a real task
```

The two source roles are simple:

```text
sot
→ your private Personal-SoT installation

sot public
→ the reusable public product
→ mrAlishah/Personal-SoT
```

Never store your Personal data in `sot public`.

## Important commands

| Command | Use it for |
|---|---|
| `@do:sot` | Reconnect/re-anchor the current chat to your canonical private SoT. |
| `@do:setup` | First setup, resume incomplete setup, improve configuration, or route an update. |
| `@do:doctor` | Read-only health check. Nothing is changed. |
| `@do:fix` | Diagnose a real problem and guide a safe repair. |
| `@do:help` | Explain features, discover capabilities, or recommend what to do next. |
| `@do:assist` | Safely create, change, maintain, or customize your Personal-SoT. |

You can also speak naturally. The commands are shortcuts, not a requirement.

## Quick install

### Linux / macOS

```bash
git clone https://github.com/mrAlishah/Personal-SoT.git
cd Personal-SoT
./install.sh
```

### Windows

```bat
git clone https://github.com/mrAlishah/Personal-SoT.git
cd Personal-SoT
install.bat
```

The installer can prepare:

- an empty **private GitHub repository**; or
- an empty **local folder already synced by Google Drive**.

It runs the core checks and Doctor. When it finishes successfully, open the resulting private `sot` in Codex or Claude Code and run:

```text
@do:sot
```

then:

```text
@do:setup
```

See [Setup](guides/user/setup.md) for the step-by-step version.

## How it works

```text
sot public
    │
    │ install / reusable product updates
    ▼
your private sot
    │
    │ open in an authorized AI client
    ▼
@do:sot
    │
    ▼
@do:setup
    │
    ├── projects
    ├── current state
    ├── prompts
    ├── profiles
    └── preferences
```

The design principle is:

```text
simple outside + rigorous inside
```

You tell the Assistant what you want. Internally it resolves the right context, reuses existing capabilities, previews material changes, waits for confirmation, writes only with real permission, validates, and reports what actually happened.

## Use it well

For normal use, start with the outcome instead of the feature name:

```text
Create a project for learning German.

Update my project. I finished A1 and now practise twice a week.

Find a reusable prompt for reviewing a code change.

Make my answers shorter and more structured.

I don't know what I need — recommend a useful starting point.
```

When something looks wrong:

```text
@do:doctor
```

If Doctor finds a real problem:

```text
@do:fix
```

If you are unsure what Personal-SoT can do:

```text
@do:help
```

## User guides

| Goal | Guide |
|---|---|
| First install and setup | [Setup](guides/user/setup.md) |
| Learn the normal workflow | [Beginner guide](guides/user/readme.md) |
| Check system health | [Doctor](guides/user/doctor.md) |
| Update Personal-SoT | [Update](guides/user/update.md) |
| Create and maintain a project | [First project](guides/user/create_and_use_project.md) |
| Find an existing prompt | [Prompt discovery](guides/user/find_and_use_prompts.md) |
| Build or improve a prompt | [Prompt builder](guides/user/build_a_prompt.md) |
| Change response style | [Customize responses](guides/user/customize_responses.md) |

## Developers

Start with [Developer Guide](guides/developer/readme.md).

The short version:

```text
develop
→ short-lived branch
→ tests + validators + review
→ develop
→ explicit release
→ main
```

Reusable runtime semantics belong under `system/`. Real Personal facts and private deployment state never belong in the public product repository.

## Safety and privacy

Keep these **outside** Personal-SoT:

- passwords;
- API tokens and private keys;
- recovery codes and one-time codes;
- session cookies;
- payment credentials.

A material saved change follows this rule:

```text
understand
→ preview
→ confirm
→ re-check
→ write
→ validate
→ report
```

A web/read-only client may explain and preview, but it must not claim that it wrote files or ran local validation when it could not.

## Repository map

```text
workspace/  user-owned content and configuration
system/     runtime contracts, algorithms, validation and tests
guides/     user and developer documentation
```

For the complete beginner journey, continue with [guides/user/readme.md](guides/user/readme.md).
