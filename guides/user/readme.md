# Beginner guide

Personal-SoT helps your AI use the right information about you and your projects from one private source.

## Remember this

```text
First time:
install → @do:sot → @do:setup → real task

Problem:
@do:doctor → @do:fix

Not sure what to do:
@do:help
```

And:

```text
sot        → your private Personal-SoT
sot public → mrAlishah/Personal-SoT
```

Your Personal data belongs in `sot`, not `sot public`.

## Important commands

| Command | Meaning |
|---|---|
| `@do:sot` | Use/reload my canonical private SoT. |
| `@do:setup` | Finish, improve, or update setup. |
| `@do:doctor` | Check health; change nothing. |
| `@do:fix` | Diagnose and repair safely. |
| `@do:help` | Explain or recommend. |
| `@do:assist` | Help create or change something safely. |

You can also just ask naturally.

## First use

1. [Install Personal-SoT](install.md).
2. [Finish setup](setup.md).
3. Connect your AI client to the private `sot`. For ChatGPT Web, use [ChatGPT Web setup](chatgpt_web.md).
4. Run `@do:sot`.
5. Run `@do:setup`.
6. Start a real task.

Examples:

```text
Create a project for learning German.

Update my project. I passed A1.

Find a prompt for reviewing code.

Make my answers shorter.

I don't know what I need — recommend one.
```

## How changes are saved

Material changes are not silent:

```text
request
→ preview
→ you confirm
→ re-check
→ write
→ validate
→ report
```

So:

```text
Explain   → no change
Recommend → suggestion
Preview   → proposed saved change
Apply     → only after confirmation + permission
```

## If something breaks

Run:

```text
@do:doctor
```

Doctor is read-only. If it finds a real problem:

```text
@do:fix
```

See [Doctor](doctor.md).

## Common tasks

- Installation: [Install on Windows, macOS, or Linux](install.md)
- ChatGPT Web: [Authorize the private repo and configure Personalization](chatgpt_web.md)
- Projects: [Create and use a project](create_and_use_project.md)
- Existing prompts: [Find a prompt](find_and_use_prompts.md)
- New prompts: [Build a prompt](build_a_prompt.md)
- Response style: [Customize responses](customize_responses.md)
- Updates: [Update Personal-SoT](update.md)
- All commands and examples: [Cheat sheet](cheatsheet.md)
- More examples: [Assistant guidance](assistant_guidance.md)

## Local vs web clients

A local authorized client may be able to:

```text
read → preview → confirm → write → validate
```

A web/read-only client can still explain and preview when it can read the private source, but must say when it cannot write or run local validation. Configuring a repository locator does not grant repository access.

## Safety

Do not store passwords, API keys, private keys, recovery codes, one-time codes, session cookies, or payment credentials in Personal-SoT.
