# Create and use your first project

## What you need

Use Personal-SoT from an AI client that can read your private repository. To let the Assistant save changes for you, the current client also needs real write access to that private repository.

You do not need to know the folder structure, YAML, schemas, branches, or test commands.

## 1. Ask for a project

Say what you want naturally:

```text
I want a project for learning German. Guide me step by step in English.
```

Or provide more context immediately:

```text
Create a German-learning project for me.
I am at A1, want to handle daily conversations, and can study four hours per week.
```

The Assistant reuses what you already said and asks only questions that materially affect the project.

## 2. Review before anything changes

The Assistant shows a concise preview of what it understood and the exact Personal/project information it proposes to save.

Nothing is written before you explicitly confirm the preview.

If the proposal changes, you get a new preview before confirming again.

## 3. Confirm

For a new project, the Assistant creates the minimum project structure and registration after confirmation.

This is a private-context structural change:

```text
preview
→ confirm
→ update private main
→ commit/push
→ targeted Personal validation when available
→ report
```

A short-lived branch and full Python test suite are not required.

If the current web client can write the private repository but cannot run local Python, it may still save the confirmed project and must say that targeted validation was unavailable.

## 4. Use the project

Ask naturally:

```text
Using my German-learning project, what should I study next?
```

Other examples:

```text
Summarize the current state of my German-learning project.
Create a two-week plan from my current state.
What is blocking my progress?
```

Expert scope syntax remains optional:

```text
@ctx:personal/projects/german_learning
```

## 5. Update current state

Just tell the Assistant what changed:

```text
Update my German-learning project. I completed A1 and now practise conversation twice a week.
```

For a normal content-only update to existing project files, the flow is deliberately simple:

```text
read current project
→ preview exact change
→ confirm
→ update private main
→ commit/push
→ report
```

No branch and no Python tests/validators are required for that routine content update.

If the change also creates/deletes/moves modules, changes registration, or changes `ai_access`, the Assistant treats it as a structural context change and uses only targeted Personal validation when command capability exists.

## Web clients

ChatGPT or Claude Web can use the same direct-private-main flow when the connected repository tool actually exposes write capability.

If the web client is read-only, it still shows the same preview but must state that nothing was written. User confirmation does not create write permission.
