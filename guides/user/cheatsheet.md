# Personal-SoT Cheat Sheet

Quick user guide for beginners and advanced users.

## Start

~~~text
First time: install → @do:sot → @do:setup
Problem: @do:doctor → @do:fix
Help: @do:help
Create/change: natural language or @do:assist
~~~

~~~text
sot        → your private Personal-SoT
sot public → mrAlishah/Personal-SoT
~~~

Natural language is the default interface. Expert directives are optional.

## All commands

| Type | Syntax | Use |
|---|---|---|
| System | **@do:sot** | Re-anchor chat to private SoT |
| System | **@do:setup** | Setup/resume/improve/update routing |
| System | **@do:doctor** | Read-only health check |
| System | **@do:fix** | Diagnose and safely repair |
| System | **@do:help** | Explain/discover/recommend |
| System | **@do:assist** | Guided create/change/customize |
| Context | **@ctx:<path>** | Select factual scope |
| Profile | **@profile:<name>** | Apply reusable composition |
| Format | **@fmt:<name>** | Add presentation format |
| Format | **@no:fmt:<name>** | Disable format |
| Tone | **@tone:<name>** | Select tone |
| Depth | **@depth:<name>** | Select depth |
| Start | **@start:<language>** | Opening language only |
| Control | **@control:<name>=<value>** | Tune optional behavior |
| Prompt | **@run:<path>** | Run reusable Prompt |
| Prompt | **@edit:<path>** | Preview Prompt only |
| Prompt | **@delete:<path>** | Build deletion plan only |
| Param | **@param:<name>=[value]** | Bind Prompt parameter |
| Param | **@param:<name>=[[...]]** | Bind multiline parameter |
| Recap | **@recap:<count>** | Recap recent exchanges |

Deprecated compatibility: **@do:initialSoT** → **@do:sot**.

## Context

~~~text
@ctx:personal
@ctx:personal/projects/<project_path>
@ctx:org/<organization>
@ctx:org/<organization>/projects/<project_path>
~~~

Use only real context identities from your private SoT.

## Shipped Profiles

~~~text
architecture/review
code/review
lang/german
obsidian/note
research/deep
tech/learn
~~~

## Presentation / representation

Formats:

~~~text
yaml md eli5 vocab concept mental learn compare cheatsheet correct
~~~

Tones:

~~~text
human formal professional neutral
~~~

Depth:

~~~text
summary short medium deep
~~~

Opening language:

~~~text
@start:fa
@start:en
@start:de
@start:auto
~~~

Presentation changes how an answer is rendered, not factual authority.

## Runtime controls

~~~text
@control:clarify=on|off|auto
@control:learning=on|off|auto
@control:steps=on|off|auto
~~~

- **clarify**: stop for clarification when ambiguity materially matters.
- **learning**: intentionally optimize for learning.
- **steps**: advance operational work one observable step at a time.

## Prompt actions

~~~text
@run:<prompt_path>
@edit:<prompt_path>
@delete:<prompt_path>
~~~

**@run** executes. **@edit** previews and stops. **@delete** creates a deletion plan and stops.

## Shipped Prompt Library

| Prompt | Purpose | Parameters |
|---|---|---|
| **chat/recap** | Conversation recap | required: count; optional: focus |
| **chat/snapshot** | New-chat handoff | optional: focus |
| **sot/assistant** | General SoT Assistant | optional: request |
| **sot/context/update** | Update active context | optional: focus, user_context |
| **sot/doctor** | Doctor workflow | optional: concern |
| **sot/personalize** | Personalization | optional: request |
| **sot/project/create** | Create project | optional: project_intent |
| **sot/project/update** | Update project | optional: project_reference, update_evidence |
| **sot/prompt/create** | Create Prompt | optional: use_case |
| **sot/prompt/list** | Find Prompts | optional: use_case |
| **sot/review/charter** | Review governance charter | optional: focus, user_context |
| **sot/review/system** | Deep system review | optional: focus, user_context |
| **sot/setup** | Setup workflow | optional: setup_goal |

## Parameters

~~~text
@param:name=[value]

@param:name=[[
multiline value
]]
~~~

Names are exact and case-sensitive.

## Recap

~~~text
@recap:5

Focus on decisions and confirmed fixes.
~~~

Recap may combine only with presentation directives such as **@fmt**, **@no:fmt**, **@tone**, and **@depth**.

## Rules

- Directives must be at the start of the prompt, followed by a blank line and body text.
- Identities are exact and case-sensitive; do not guess Prompt/Profile/context names.
- One high-level action per invocation: one **@do:***, or one **@run/@edit/@delete**, or one **@recap**.
- Prompt actions may combine with context, Profiles, presentation, controls, and valid parameters.
- Presentation changes rendering, not factual authority.
- Material changes follow preview → confirm → re-check → write → validate → report.

# Case studies

## 1. Code review

Noob:

~~~text
Review this change using my backend project's architecture and constraints.
Focus on correctness, regressions, security, and missing tests.
~~~

Expert:

~~~text
@ctx:personal/projects/<backend_project>
@profile:code/review
@depth:deep
@control:clarify=on

Review this change.
~~~

## 2. Project create/update

Create:

~~~text
@run:sot/project/create
@param:project_intent=[Refactor authentication while preserving compatibility]
~~~

Update:

~~~text
@run:sot/project/update
@param:project_reference=[<real_project_identity>]
@param:update_evidence=[[
Current work is complete.
The next migration step is identified.
]]
~~~

## 3. Personal facts and life goals

Noob:

~~~text
Save this if it belongs in my Personal context:
My professional focus is backend/platform engineering.
Show the preview first.
~~~

Goals:

~~~text
Help me define my 12-month goals:
German B2, two open-source projects, better public speaking.
Then show what should be saved.
~~~

Update:

~~~text
@ctx:personal
@run:sot/context/update
@param:focus=[goals and current state]
@param:user_context=[[
German A2 is complete.
One project is published.
German study capacity is four hours per week.
]]
~~~

## 4. Ask SoT for guidance

~~~text
@ctx:<real_goals_or_project_context>
@fmt:compare
@depth:deep

What are the three highest-leverage actions for this month?
Explain trade-offs and what to deprioritize.
~~~

## 5. Learning

German:

~~~text
@ctx:personal/projects/<german_project>
@profile:lang/german
@control:learning=on

Create my next two-week study plan.
~~~

Technical:

~~~text
@profile:tech/learn
@control:learning=on
@depth:deep

Teach me MVCC with a concrete example first.
~~~

## 6. Prompt discovery + chat handoff

Find a Prompt:

~~~text
@run:sot/prompt/list
@param:use_case=[Compare technical designs by trade-offs and risk]
~~~

Recap:

~~~text
@recap:6

Focus on decisions, commands, errors, and fixes.
~~~

New-chat snapshot:

~~~text
@run:chat/snapshot
@param:focus=[current state, decisions, unresolved work, next step]
~~~

## Common mistakes

Wrong:

~~~text
Please use @depth:deep and explain this.
~~~

Right:

~~~text
@depth:deep

Explain this.
~~~

Wrong: two high-level actions:

~~~text
@do:help
@run:chat/snapshot
~~~

When in doubt, use **@do:help** or explain what you want in normal language.
