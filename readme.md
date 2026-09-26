# Personal-SoT

Personal-SoT gives your AI one controlled place to understand your goals, projects, preferences, and current situation.

The product goal is simple:

```text
install → choose your language → connect your AI
→ meet the Personal SoT Assistant → complete a useful task
```

You should not need to understand Git, YAML, prompt engineering, repository paths, or SoT architecture for normal use.

## Current milestone

This repository currently contains the safe public foundation:

- generic, client-neutral SoT contracts;
- no real Personal data or private configuration;
- local structural, prompt, and public-distribution validation;
- a minimal workspace that creates Personal modules only when needed.

Guided setup, the Personal SoT Assistant, and the first Project Builder flow are the next vertical slice. Until that slice lands, this is a foundation release rather than a finished beginner installation.

## Start here

- New user: [Beginner guide](guides/user/readme.md)
- Developer or contributor: [Developer guide](guides/developer/readme.md)
- Migration decisions: [Public V1 inventory](guides/developer/migration/public_v1_inventory.md)

## Safety

Never store passwords, API tokens, private keys, recovery codes, session cookies, one-time codes, or other credentials in Personal-SoT.

Before any public release, run:

```bash
python3 system/validation/validate_v1.py --mode core
python3 system/validation/validate_prompts.py
python3 system/validation/validate_public.py
```

Personal-SoT keeps the canonical three-root model:

```text
workspace/  your content and configuration
system/     shared contracts and validation
guides/     beginner and developer documentation
```
