# Set up Personal-SoT

For this guide:

```text
sot
→ your private Personal-SoT installation/repository

sot public
→ the upstream public product
→ mrAlishah/Personal-SoT
```

The setup flow is safe to run again later. `@do:setup` does not blindly reinstall: it checks what already exists, resumes incomplete setup, recommends small setup improvements, or routes an existing installation through the safe update workflow when appropriate.

You do not need to understand Git, YAML, prompt engineering, or the repository structure.

## 1. Get the repository

### Fast path after clone

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

The installer asks for one destination:

- **GitHub Private:** provide an empty private GitHub repository URL. The installer verifies access/privacy, renames the public remote to `upstream`, adds the private repository as `origin`, pushes the initial copy, and runs the checks.
- **Google Drive:** provide an empty **local folder already synchronized by Google Drive Desktop or equivalent**. A Google Drive sharing URL alone is not enough for a local script to write files safely.

After the checks pass, open the resulting private `sot` in your AI client and run:

```text
@do:sot
```

then:

```text
@do:setup
```

### Manual path

Choose the simplest option that fits you:

- **Download:** download `sot public`, extract it, and create/use a private folder for your future `sot`.
- **Clone:** if you already use Git, clone `sot public` so later updates are easier, then keep Personal work in a private installation/repository you control.

The public repository contains no real Personal facts. Your private copy becomes `sot` only when it is the selected user-owned installation. Do not push Personal facts or private configuration to `sot public`.

For a Git-backed installation, a common safe remote layout is:

```text
origin   → your private repository
upstream → mrAlishah/Personal-SoT
```

The Assistant should verify real remotes/capabilities rather than inventing account names or URLs.

## 2. Open it with your AI client

For real local writes, open the repository folder in Codex or Claude Code and allow only the repository access needed for the task.

Then ask naturally in your preferred language:

```text
Help me set up Personal-SoT. Guide me one step at a time in English.
```

Or use the exact expert shortcut:

```text
@do:setup
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

An authorized local agent runs Personal-SoT Doctor, which reuses the existing repository checks and explains the result as:

```text
ready
or
what failed → affected area → smallest next action
```

It must not call setup successful when a required check fails.

You can request the same check directly with:

```text
@do:doctor
```

If Doctor finds a real problem, use `@do:fix` for guided diagnosis/repair. Doctor itself remains read-only.

See [Check Personal-SoT with Doctor](doctor.md) for status meanings and safe repair guidance.

## Web clients

ChatGPT and Claude Web can follow the same language choice, guided questions, recommendations, and previews when the repository is available to them.

If the web client cannot write files or run local commands, it must say that nothing was written and the local system check was not run there. Use an authorized local agent to apply the confirmed preview and validate it.

## Run setup again later

You may run:

```text
@do:setup
```

at any later time. The Assistant should inspect current evidence and choose the smallest applicable path:

```text
incomplete setup → resume
healthy but stale → safe update workflow
healthy but improvable → recommend/preview improvement
healthy and current → report ready
```

It must preserve valid Personal state and must not restart or overwrite setup merely because the command was invoked again.

## First useful task

After setup, ask for a concrete outcome:

```text
Help me create my first project for learning German.
```

See [Create and use your first project](create_and_use_project.md) for the complete create → use → update flow.
