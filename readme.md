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
sot        -> your private Personal-SoT
sot public -> mrAlishah/Personal-SoT
```

Never store Personal data in `sot public`.

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

Then open the private `sot` in a supported local AI client and run:

```text
@do:sot
@do:setup
```

See the [Install guide](guides/user/install.md) for prerequisites and OS-specific steps, then [Setup](guides/user/setup.md).

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

## Update later

Normally, tell a capable local AI client:

```text
Update my Personal-SoT.
```

Or run from the private `sot` terminal:

```bash
python3 update.py
```

Safe Update shows one preview, asks for confirmation, then applies and validates.

## How it works

```text
sot public
    |
    v
private sot
    |
    v
AI client
    |
    v
@do:sot -> @do:setup
    |
    v
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

I don't know what I need - recommend one.
```

If something looks wrong:

```text
@do:doctor
@do:fix
```

## Guides

| Goal | Guide |
|---|---|
| Reach your goals with Personal-SoT | [Goals guide](guides/user/goals.md) |
| Learn the normal workflow | [Beginner guide](guides/user/readme.md) |
| All commands, Profiles, prompts, controls, and examples | [Cheat sheet](guides/user/cheatsheet.md) |
| Install on Windows, macOS, or Linux | [Install](guides/user/install.md) |
| Finish setup | [Setup](guides/user/setup.md) |
| Diagnose problems | [Doctor](guides/user/doctor.md) |
| Update safely | [Update](guides/user/update.md) |
| Create a project | [First project](guides/user/create_and_use_project.md) |
| Find/build prompts | [Prompt discovery](guides/user/find_and_use_prompts.md) / [Prompt builder](guides/user/build_a_prompt.md) |
| Customize responses | [Customization](guides/user/customize_responses.md) |
| Develop the public product | [Developer guide](guides/developer/readme.md) |

## Why use Personal-SoT?

Personal-SoT gives your AI a reliable picture of where you are, what you want, and what constraints matter, so it can help you decide what to do next.

| What you need | Without Personal-SoT | With Personal-SoT |
|---|---|---|
| Choose the next step | Generic advice | Advice based on your current state |
| Continue in a new chat | Explain everything again | Recover the relevant project context |
| Make a decision | General comparison | Compare options against your goals and constraints |
| Plan your work | A mostly static plan | A plan that adapts to real progress |
| Avoid contradictions | Different chats may make different assumptions | Decisions and constraints have a clear source |
| Learn over time | Generic teaching | Learning based on your project and current level |
| Maintain projects | Information is scattered across chats | Current state and objectives stay organized |

For a deeper explanation and practical goal loop, see the [Goals guide](guides/user/goals.md). For usage examples and expert syntax, see the [Beginner guide](guides/user/readme.md) and [Cheat sheet](guides/user/cheatsheet.md).

## Safety

Keep passwords, tokens, private keys, recovery codes, one-time codes, session cookies, and payment credentials outside Personal-SoT.

Material saved changes follow:

```text
preview -> confirm -> re-check -> write -> validate -> report
```

Repository map:

```text
workspace/  user-owned content/configuration
system/     runtime + validation + tests
guides/     user/developer documentation
```

## For developers

```text
develop
-> short-lived branch
-> tests + validators + review
-> PR to develop
-> explicit release
-> main
```

Reusable runtime semantics belong in `system/`. Personal facts and private deployment state never belong in the public product.
