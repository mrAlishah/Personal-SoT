# Beginner guide

## What Personal-SoT is

Personal-SoT is a controlled memory and instruction system for AI. It is designed to help an AI use the right information about you and your projects without relying on scattered chats or repeated prompts.

The intended beginner experience is conversational:

```text
You: I want to create a project for learning German.

Assistant:
1. explains the short flow;
2. asks one useful question at a time;
3. gives examples and a recommendation;
4. shows exactly what it proposes to save;
5. waits for confirmation;
6. writes and validates the smallest necessary project;
7. teaches you what to ask next.
```

## What works now

The reusable SoT engine, safety validators, guided setup, Personal SoT Assistant contracts, and first Project Builder flow are present. The repository starts without real Personal facts and creates only the modules your confirmed setup or project actually needs.

Start with [Set up Personal-SoT](setup.md).

If setup or configuration seems wrong, run the [beginner-friendly Doctor](doctor.md).

Open the repository in Codex or Claude Code and ask naturally:

```text
Help me create my first Personal-SoT project.
Please guide me in English.
```

The local agent can preview, confirm, write, and validate when its actual permissions allow it. ChatGPT and Claude Web can run the same questions and preview, but must tell you when they cannot write the repository.

Then see [Create and use your first project](create_and_use_project.md) for the complete project flow.

To reuse an existing capability before creating one, see
[Find and use an existing prompt](find_and_use_prompts.md).

## Safety rule

Do not put secrets here. Keep passwords, API tokens, private keys, recovery codes, session cookies, one-time codes, and payment credentials in a password manager or another proper secret store.

## Product journey

```text
[1 Install]
     ↓
[2 Choose language]
     ↓
[3 Choose AI client]
     ↓
[4 Personal onboarding]
     ↓
[5 System check]
     ↓
[6 Meet Personal SoT Assistant]
     ↓
[7 First useful task]
```

The Assistant will offer six simple categories:

- Discover — find the right existing capability.
- Maintain — update your information or project state safely.
- Create — build a project, goal, or reusable prompt.
- Customize — adjust response style and behavior.
- Explain — learn what a feature means and when to use it.
- Diagnose — check the system and get beginner-friendly repair guidance.

Advanced directives such as `@ctx`, `@profile`, `@fmt`, `@tone`, `@depth`, and `@do:prompt` remain available, but they are optional. The Assistant should first complete or recommend the natural-language workflow, then show precise syntax only when useful.
