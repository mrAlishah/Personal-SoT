# Personal-SoT

Personal-SoT gives your AI one controlled place to understand your goals, projects, preferences, and current situation.

The product goal is simple:

```text
install → choose your language → connect your AI
→ meet the Personal SoT Assistant → complete a useful task
```

You should not need to understand Git, YAML, prompt engineering, repository paths, or SoT architecture for normal use.

## Current milestone

This repository currently contains the safe public foundation and the first runnable Personal SoT Assistant flow:

- generic, client-neutral SoT contracts;
- no real Personal data or private configuration;
- local structural, prompt, and public-distribution validation;
- a minimal workspace that creates Personal modules only when needed;
- client-neutral guided setup from repository connection to first useful task;
- a read-only beginner Doctor for setup, workspace, reference and client diagnostics;
- client-neutral guided project creation and current-state maintenance;
- on-demand prompt discovery and reuse-first guided prompt creation;
- natural-language personalization with Profile-only safe creation and editing;
- authorized local writes in Codex and Claude Code;
- truthful preview-only behavior when a web client cannot write the repository.

The guided onboarding and first create → use → update project workflow are available through a local agent opened at the repository root. A cross-platform one-click installer is included for users who start from a Git clone: `install.sh` on Linux/macOS and `install.bat` on Windows.

## Quick install

Clone the stable public product, then run the launcher for your OS:

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

The installer can convert the clone to a private GitHub-backed `sot`, or create a validated no-Git copy in a local Google Drive synced/mounted folder. Successful completion tells you to open the private installation and run `@do:sot`, then `@do:setup`.

## Start here

- New user: [Setup guide](guides/user/setup.md)
- Product tour: [Beginner guide](guides/user/readme.md)
- Diagnose a problem: [Personal-SoT Doctor](guides/user/doctor.md)
- Create and use a project: [First project guide](guides/user/create_and_use_project.md)
- Find an existing prompt: [Prompt Explorer guide](guides/user/find_and_use_prompts.md)
- Build or improve a prompt: [Prompt Builder guide](guides/user/build_a_prompt.md)
- Customize responses: [Personalization guide](guides/user/customize_responses.md)
- Developer or contributor: [Developer guide](guides/developer/readme.md)
- Migration decisions: [Public V1 inventory](guides/developer/migration/public_v1_inventory.md)

## Safety

Never store passwords, API tokens, private keys, recovery codes, session cookies, one-time codes, or other credentials in Personal-SoT.

Before any public release, run:

```bash
python3 system/validation/validate_v1.py
python3 system/validation/validate_prompts.py
python3 system/validation/validate_public.py
```

Personal-SoT keeps the canonical three-root model:

```text
workspace/  your content and configuration
system/     shared contracts and validation
guides/     beginner and developer documentation
```
