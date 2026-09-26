# Set up Personal-SoT

You do not need to understand Git, YAML, prompt engineering, or the repository structure.

## 1. Get the repository

Choose the simplest option that fits you:

- **Download:** download the repository archive from [Personal-SoT on GitHub](https://github.com/mrAlishah/Personal-SoT), extract it, and keep the folder somewhere private on your computer.
- **Clone:** if you already use Git, clone the repository so later updates are easier.

The public repository contains no real Personal facts. Your local copy becomes personal only after you confirm information to save.

## 2. Open it with your AI client

For real local writes, open the repository folder in Codex or Claude Code and allow only the repository access needed for the task.

Then ask naturally in your preferred language:

```text
Help me set up Personal-SoT. Guide me one step at a time in English.
```

You can replace English with your preferred language. The Assistant should use that language immediately when your choice is clear.

## 3. Follow the guided setup

The Assistant will guide you through:

```text
[1 Repository]
→ [2 Language]
→ [3 AI client]
→ [4 Optional personal context]
→ [5 System check]
→ [6 Meet the Assistant]
→ [7 First useful task]
```

It asks one useful question at a time, reuses answers you already gave, and explains recommendations in plain language.

Personal onboarding is optional. You can skip it and create your first project. No empty personal files should be created just to finish setup.

## 4. Review any saved information

If you choose to save durable personal information, the Assistant must first show what it proposes to store, where the meaning belongs, what it excluded, and which checks it will run.

Nothing material should be written before you confirm that exact preview. Do not enter passwords, API tokens, private keys, recovery codes, one-time codes, or payment credentials.

## 5. System check

An authorized local agent runs the existing repository checks and explains the result as:

```text
ready
or
what failed → affected area → smallest next action
```

It must not call setup successful when a required check fails.

## Web clients

ChatGPT and Claude Web can follow the same language choice, guided questions, recommendations, and previews when the repository is available to them.

If the web client cannot write files or run local commands, it must say that nothing was written and the local system check was not run there. Use an authorized local agent to apply the confirmed preview and validate it.

## First useful task

After setup, ask for a concrete outcome:

```text
Help me create my first project for learning German.
```

See [Create and use your first project](create_and_use_project.md) for the complete create → use → update flow.
