# Beginner guide

Personal-SoT is a private source of truth that helps your AI use the right information about you and your projects.

You do not need to understand the repository structure. Start with a goal and let the Assistant route the work.

## The 30-second map

```text
First time:
install → @do:sot → @do:setup → start a real task

Something looks wrong:
@do:doctor → @do:fix

Need help deciding:
@do:help

Want to create or change something:
ask naturally or use @do:assist
```

Source names:

```text
sot
→ your private Personal-SoT

sot public
→ the public reusable product
→ mrAlishah/Personal-SoT
```

Your Personal facts belong in your private `sot`, never in `sot public`.

## Important commands

| Command | Plain-English meaning |
|---|---|
| `@do:sot` | “Use my canonical private SoT for this chat.” |
| `@do:setup` | “Help me finish, improve, or update setup.” |
| `@do:doctor` | “Check the system. Do not change anything.” |
| `@do:fix` | “Figure out what is actually wrong and repair it safely.” |
| `@do:help` | “Explain, discover, or recommend.” |
| `@do:assist` | “Help me safely create or change something.” |

Natural language is the normal interface. These commands are just precise shortcuts.

## First-time use

### 1. Install

Follow [Setup](setup.md).

The fast path is:

```text
clone sot public
→ run install.sh / install.bat
→ open the resulting private sot
```

### 2. Connect the chat

Run:

```text
@do:sot
```

This re-resolves and reloads the canonical runtime for the current chat.

### 3. Finish setup

Run:

```text
@do:setup
```

The Assistant reuses what it already knows, asks one useful question at a time, and runs the system check when the client can actually execute it.

### 4. Do useful work

You can now ask normally:

```text
Create a project for learning German.

What should I do next in my German-learning project?

Update my project. I passed A1.

Find a prompt for reviewing code.

Make my answers shorter.

I don't know what I need — recommend one useful starting point.
```

## How saved changes work

Personal-SoT does not silently save material changes.

```text
your request
→ understand/classify
→ show preview
→ you confirm
→ re-check current state
→ write
→ validate
→ report result
```

So these are different:

```text
Explain      → nothing changes
Recommend    → suggestion only
Preview      → shows the proposed saved change
Apply        → happens only after confirmation + real permission
```

## When something is wrong

Run:

```text
@do:doctor
```

Doctor is read-only.

If it finds a real problem, use:

```text
@do:fix
```

`@do:fix` first decides whether the problem is:

```text
usage confusion
→ explain the correct usage
→ no write

real defect
→ diagnose
→ preview repair
→ confirm
→ apply
→ validate
```

See [Doctor](doctor.md).

## Updating later

You can simply say:

```text
Update my Personal-SoT.
```

or run:

```text
@do:setup
```

Setup is re-runnable. It can detect incomplete setup, an installation that needs improvement, or an installation that should go through the Safe Update workflow.

See [Update](update.md).

## Common things to do

### Projects

```text
Create a project for preparing for the AWS exam.
```

Guide: [Create and use your first project](create_and_use_project.md)

### Existing prompts

```text
Find a prompt that can review a code change.
```

Guide: [Find and use prompts](find_and_use_prompts.md)

### New reusable prompt

```text
Help me make a reusable prompt for comparing two technical designs.
```

Guide: [Build a prompt](build_a_prompt.md)

### Response style

```text
Make this shorter.
Use a professional tone.
Compare these options in a table.
Teach this step by step.
```

Guide: [Customize responses](customize_responses.md)

### I do not know what to do

```text
@do:help
```

or:

```text
I don't know what I need — recommend a useful starting point.
```

## Local clients vs web clients

A local authorized client such as Codex or Claude Code may be able to:

```text
read → preview → confirm → write → validate
```

A web/read-only client may still explain and preview, but if it cannot write or run commands it must say so plainly.

## One safety rule

Do not store credentials in Personal-SoT.

Keep passwords, API keys, private keys, recovery codes, one-time codes, session cookies, and payment credentials in a proper secret store.

For more examples of how to ask for help, see [Assistant guidance](assistant_guidance.md).
