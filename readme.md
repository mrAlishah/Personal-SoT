# Personal-SoT

**A private source of truth for your AI.**

Personal-SoT keeps your projects, preferences, prompts, profiles, and current state in one controlled place so your AI can use the right context without relying on scattered chats.

You do **not** need to learn Git, YAML, repository paths, or prompt engineering for normal use.

## Start here

First time:

```text
1. Clone sot public
2. Run install.sh / install.bat
3. Open your private sot
4. Run @do:sot
5. Run @do:setup
6. Start a real task
```

Source roles:

```text
sot        → your private Personal-SoT
sot public → mrAlishah/Personal-SoT
```

Never store Personal data in `sot public`.

## Important commands

| Command | What it does |
|---|---|
| `@do:sot` | Reconnect/re-anchor this chat to your private SoT. |
| `@do:setup` | Set up, resume, improve, or route an update. |
| `@do:doctor` | Check system health without changing anything. |
| `@do:fix` | Diagnose and safely repair a real problem. |
| `@do:help` | Explain, discover, or recommend. |
| `@do:assist` | Safely create or change something. |

Natural language also works. These commands are shortcuts.

## Quick install

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

The installer can prepare an empty private GitHub repository or an empty local folder already synced by Google Drive. It runs validation and Doctor before reporting success.

Then open the private `sot` in Codex or Claude Code and run:

```text
@do:sot
@do:setup
```

See [Setup](guides/user/setup.md).

## How it works

```text
sot public
    ↓ install / reusable updates
private sot
    ↓
AI client
    ↓
@do:sot
    ↓
@do:setup
    ↓
projects / prompts / profiles / current state
```

The product rule is:

```text
simple outside + rigorous inside
```

You state the outcome. Personal-SoT resolves the right context, reuses existing capabilities, previews material changes, waits for confirmation, validates, and reports what actually happened.

## Typical use

```text
Create a project for learning German.

Update my project. I finished A1.

Find a prompt for reviewing code.

Make my answers shorter.

I don't know what I need — recommend one.
```

If something looks wrong:

```text
@do:doctor
@do:fix
```

## Guides

| Goal | Guide |
|---|---|
| Learn the normal workflow | [Beginner guide](guides/user/readme.md) |
| Install and set up | [Setup](guides/user/setup.md) |
| Diagnose problems | [Doctor](guides/user/doctor.md) |
| Update safely | [Update](guides/user/update.md) |
| Create a project | [First project](guides/user/create_and_use_project.md) |
| Find/build prompts | [Prompt discovery](guides/user/find_and_use_prompts.md) / [Prompt builder](guides/user/build_a_prompt.md) |
| Customize responses | [Customization](guides/user/customize_responses.md) |
| Develop the public product | [Developer guide](guides/developer/readme.md) |

## For developers

```text
develop
→ short-lived branch
→ tests + validators + review
→ PR to develop
→ explicit release
→ main
```

Reusable runtime semantics belong in `system/`. Personal facts and private deployment state never belong in the public product.

## Safety

Keep passwords, tokens, private keys, recovery codes, one-time codes, session cookies, and payment credentials outside Personal-SoT.

Material saved changes follow:

```text
preview → confirm → re-check → write → validate → report
```

Repository map:

```text
workspace/  user-owned content/configuration
system/     runtime + validation + tests
guides/     user/developer documentation
```

## Quick reference

| What you want | Command / example |
|---|---|
| Reconnect this chat to your private SoT | `@do:sot` |
| Finish or improve setup | `@do:setup` |
| Check system health | `@do:doctor` |
| Diagnose and repair a problem | `@do:fix` |
| Ask the system what to use or do next | `@do:help` |
| Create/change something through guided workflows | `@do:assist` |
| Use a specific context/project | `@ctx:<path>` |
| Use a saved response profile | `@profile:<name>` |
| Run a reusable prompt | `@run:<prompt_path>` |
| Recap recent conversation exchanges | `@recap:<count>` |

You normally do not need expert syntax. Start in natural language and use these shortcuts when you want precise control.

## Why use Personal-SoT?

| Goal | Without a Personal SoT | With Personal-SoT | Value |
|---|---|---|---|
| Continue a long-running project | Re-explain goals, constraints, decisions, and current state in new chats. | Keep the project state in one canonical private context and update it as things change. | Less repetition and fewer context mistakes. |
| Learn something over weeks or months | Each chat may treat you like a new learner. | Keep goals, level, constraints, and current progress in a project. | Advice can start from your actual current state. |
| Reuse a good AI workflow | Copy/paste the same long prompt repeatedly. | Save or reuse a validated prompt and call it when needed. | More consistent results with less prompt maintenance. |
| Keep response style consistent | Repeatedly ask for the same tone, depth, and format. | Reuse a Profile or explicit presentation controls. | Consistent output without repeating preferences. |
| Maintain trustworthy context | Old chat history and current facts can get mixed together. | Separate durable context, project current state, prompts, and presentation settings by owner. | Clearer source of truth and less stale-context drift. |
| Diagnose a broken setup | Guess whether the problem is configuration, usage, or runtime. | Run `@do:doctor`, then `@do:fix` only when repair is actually needed. | Safer troubleshooting without blind edits. |

## Examples: Noob vs Expert

The **Noob** version is usually enough. The **Expert** version gives you more precise control.

Placeholders such as `<project_context_path>`, `<prompt_path>`, and `<profile_name>` mean: use the real identity that Personal-SoT discovers or creates for you. Do not guess paths or names.

### 1. Programming project that continues across chats

**Noob**

```text
Create a project for refactoring my backend authentication service.

The goals are:
- reduce duplicated auth logic;
- add better tests;
- migrate gradually without breaking existing clients.

Guide me step by step.
```

Later:

```text
Update my authentication-refactor project.

I finished extracting token validation and added integration tests.
The next problem is migrating the old login endpoint.
```

Then:

```text
Using the current state of my authentication-refactor project,
what should I do next and what are the biggest risks?
```

**Expert**

```text
@do:assist

Create a project for refactoring my backend authentication service.
Track goals, constraints, decisions, current state, and next actions.
```

After the project exists, you can target its real context directly:

```text
@ctx:<project_context_path>

Review the current state and recommend the next implementation step.
```

**Value:** you stop re-explaining architecture decisions, constraints, progress, and next steps in every new chat.

### 2. Code review with project context

**Noob**

```text
Review this code change using the architecture and constraints of my backend project.
Focus on correctness, regressions, security boundaries, and missing tests.

<paste diff or describe the change>
```

Without Personal-SoT, you may also need to repeat:

```text
Here is our architecture...
Here are our constraints...
Here are previous decisions...
Here is what this migration is trying to achieve...
```

With Personal-SoT, those durable project facts can already live in the project context.

**Expert**

First discover a reusable review prompt:

```text
@do:help

Find the best existing prompt for reviewing a code change.
```

If the Assistant returns a usable prompt identity:

```text
@ctx:<project_context_path>
@run:<prompt_path>

<paste diff or describe the change>
```

**Value:** review can use both a reusable review method and the actual project context instead of treating every diff as isolated code.

### 3. Save useful personal information

Use Personal-SoT for durable, non-secret information that genuinely helps future work.

**Noob**

```text
Save this if it belongs in my Personal context:

My long-term professional focus is backend and platform engineering.
I learn technical topics best from a short example first, then the deeper explanation.

Show me what you would save before changing anything.
```

Personal-SoT should classify the information, show a preview, and wait for confirmation.

**Expert**

```text
@do:assist

Add these durable non-sensitive facts/preferences to the correct Personal owner:

- professional focus: backend and platform engineering;
- learning preference: example first, deeper explanation second.

Show the exact preview before saving.
```

**Value:** useful durable context can be reused without copying it into every project or prompt.

Do **not** store passwords, tokens, private keys, recovery codes, session cookies, or other credentials.

### 4. Define long-term life goals

**Noob**

```text
Help me define my main goals for the next 12 months.

Current ideas:
- reach German B2;
- publish two useful open-source projects;
- improve my public speaking.

Help me make the goals clear and realistic, then show what should be saved.
```

**Expert**

```text
@do:assist

Help me create or update the correct Personal goals context for these 12-month goals:
- German B2;
- two useful open-source projects;
- better public speaking.

Separate goals, constraints, current state, and next actions.
Preview before saving.
```

**Value:** your goals become explicit context that can guide later planning instead of disappearing inside an old chat.

### 5. Update goal context as life changes

**Noob**

```text
Update my goals.

Changes:
- I completed German A2;
- one open-source project is now published;
- I can spend about four hours per week on German for the next two months.

Keep the old goals that are still valid and update only the current state and constraints that changed.
```

**Expert**

```text
@do:assist

Update my existing goals context with the following current-state changes:
- German A2 completed;
- first open-source project published;
- German study capacity is now about four hours per week for two months.

Preserve still-valid goals and decisions. Preview the exact update first.
```

**Value:** the AI can reason from your **current** situation instead of stale assumptions.

### 6. Ask for guidance based on your goals

**Noob**

```text
Look at my current goals, constraints, and active projects.

What are the three highest-leverage things I should focus on this month?
Explain what you deprioritized and why.
```

**Expert**

After the real context identity is known:

```text
@ctx:<goals_or_project_context_path>
@depth:deep

Based on the current goals, constraints, and progress in this context,
recommend the three highest-leverage actions for this month.
Explain the trade-offs.
```

**Value:** advice can be grounded in explicit goals and constraints rather than generic productivity advice.

### 7. Learning that remembers your real progress

**Noob**

```text
Create a project for learning German.

I am currently A1.
My target is B2.
I can study five hours per week.
I care most about speaking and listening.
```

Weeks later:

```text
Update my German project.

I finished A1 and now practise conversation twice a week.
Vocabulary is improving, but listening is still weak.
```

Then:

```text
Based on my current German project, create the best two-week study plan.
```

**Expert**

```text
@ctx:<german_project_context_path>

Use the current project state to build my next two-week study plan.
```

**Value:** the plan starts from your actual level, progress, constraints, and weak areas.

### 8. Reuse a proven workflow instead of rewriting prompts

**Noob**

```text
Find a reusable prompt for comparing two technical designs.
I want the answer to focus on trade-offs, risks, and operational complexity.
```

Later, simply ask the Assistant to use the discovered prompt.

**Expert**

```text
@do:help

Find the best existing prompt for comparing technical designs.
```

Then, using the real returned identity:

```text
@run:<prompt_path>

Compare design A and design B.
Focus on trade-offs, failure modes, and operational complexity.
```

**Value:** good workflows become reusable capabilities instead of copy/pasted prompt text.

### 9. Keep your preferred response style

**Noob**

```text
For technical decisions, give me:
- a short recommendation first;
- then the main trade-offs;
- then deeper detail only if useful.

If this is something I use repeatedly, help me save the smallest reusable configuration.
```

**Expert**

After a suitable Profile exists:

```text
@profile:<profile_name>

Compare these two deployment strategies.
```

**Value:** repeated response preferences become reusable configuration instead of repeated instructions.

### 10. Use recent conversation plus canonical context

Sometimes the latest few chat exchanges matter, but they should not replace durable SoT context.

**Expert**

```text
@recap:5

Summarize what changed in the last five completed exchanges and identify anything that should update my project current state.
```

Then use `@do:assist` if a durable update is actually needed.

**Value:** short-term conversation history and long-term canonical context stay separate instead of being mixed together.

### The core idea

Without Personal-SoT:

```text
new chat
→ repeat background
→ repeat goals
→ repeat constraints
→ repeat preferences
→ hope old assumptions are still correct
```

With Personal-SoT:

```text
private canonical context
→ update it when reality changes
→ reuse it when relevant
→ preview + confirm saved changes
→ keep prompts, facts, projects, and presentation concerns separated
```

The value is not that the AI "remembers everything." The value is that **you control a private, explicit, updateable source of truth that the AI can resolve and use when relevant.**

