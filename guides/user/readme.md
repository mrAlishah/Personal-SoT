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

## What works in the foundation milestone

The reusable SoT engine and safety validators are present. The repository contains no real Personal facts and does not create empty Personal modules just to fill a template.

The guided setup and Personal SoT Assistant are not implemented yet. You do not need to hand-edit internal files to simulate them; the next vertical slice will add the supported beginner path.

## Safety rule

Do not put secrets here. Keep passwords, API tokens, private keys, recovery codes, session cookies, one-time codes, and payment credentials in a password manager or another proper secret store.

## How the finished beginner flow will work

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
