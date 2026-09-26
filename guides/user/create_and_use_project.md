# Create and use your first project

## What you need

Open the Personal-SoT repository in Codex or Claude Code. The local agent needs permission to read and write this repository and run its validators.

You do not need to know the folder structure, YAML, schemas, or runtime directives.

## 1. Ask for a project

Say what you want in your preferred language:

```text
I want a project for learning German. Guide me step by step in English.
```

Or provide more context immediately:

```text
Create a German-learning project for me.
I am at A1, want to handle daily conversations, and can study four hours per week.
```

The Assistant will reuse what you already said and ask only questions that materially affect the project. When useful, it gives examples, recommends an answer, and lets you say:

```text
I don't know — recommend one.
```

## 2. Review before anything changes

The Assistant summarizes what it understood and previews the complete proposed change, including the friendly project name, internal identifier, information it will store, anything it excluded, and the validation it will run.

Nothing should be written before you explicitly confirm that preview. If you change the proposal, the Assistant shows a new preview before asking again.

## 3. Confirm and validate

After confirmation, a capable local agent rechecks the current repository, writes the smallest necessary project, registers it for use, and runs the repository validators.

The result must distinguish:

```text
written files
validation that actually ran and passed or failed
deferred or ambiguous information
```

If validation fails, the Assistant reports the failure instead of claiming that the project is ready.

## 4. Use the project

Ask naturally:

```text
Using my German-learning project, what should I study next?
```

Other useful examples:

```text
Summarize the current state of my German-learning project.
Create a two-week plan from my current state.
What is blocking my progress?
```

If you want precise expert control, the Assistant may also show an optional form such as:

```text
@ctx:personal/projects/german_learning
```

You do not need this syntax for normal use.

## 5. Update current state

Tell the Assistant what changed:

```text
Update my German-learning project. I completed A1 and now practise conversation twice a week.
```

The Assistant reads the current project, separates effective current state from goals, constraints, decisions, and temporary history, then previews the exact update. It writes only after confirmation and runs validation again.

## Web clients

ChatGPT and Claude Web follow the same guided questions, recommendations, classification, and preview when they can read the repository. If they do not have repository write capability, they must state:

```text
nothing was written
validation was not run here
```

You can take that preview to an authorized local agent for application. A future helper or connector may automate this handoff without changing the Assistant workflow.
