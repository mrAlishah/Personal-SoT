# Public Personal-SoT V1 product contract

## Purpose

Define the approved product boundary and completion standard for Public
Personal-SoT V1. This file owns product-level V1 decisions; runtime details
remain with their referenced canonical contracts.

## Product promise

The target user is a beginner who should not need to understand Git, YAML,
registries, prompt engineering, internal paths, or SoT architecture for normal
use.

The governing product principle is:

```text
simple outside + rigorous inside
```

The normal experience is natural-language-first and multilingual. The Personal
SoT Assistant is the primary beginner interface. Guided, Natural, and Expert
interaction modes resolve through the same client-neutral canonical runtime;
expert directives remain optional and appear through progressive disclosure.

## Beginner journey

```text
install and set up
→ select language and connect an AI client
→ run the system check
→ meet the Personal SoT Assistant
→ create a first project and complete a useful task
→ update project current state
→ discover existing capabilities
→ build or customize only when necessary
```

Guided flows use the selected language, show compact progress, ask one useful
adaptive question at a time, explain choices with examples and a recommendation
when evidence supports one, and provide an uncertainty-safe option. Internal
schemas and paths stay behind beginner-facing concepts.

## Product behavior

The Assistant exposes six beginner categories:

```text
Discover / Maintain / Create / Customize / Explain / Diagnose
```

Read-only discovery and explanation may run without confirmation. Creation and
customization follow reuse-before-create:

```text
exact existing capability
→ composition or parameterization
→ small customization
→ new canonical component only when necessary
```

Material canonical writes follow the client-neutral safe-write contract:

```text
understand and classify intent
→ resolve scope and semantic owner
→ detect duplication or conflict
→ preview the complete change
→ explicit confirmation
→ re-read/version check
→ authorized write
→ validation
→ truthful report
```

No ambiguous or guessed value becomes canonical truth. Guided questions adapt to
the user's answers instead of imposing a fixed universal questionnaire.

The canonical owners for these runtime semantics are:

- `system/assistant/assistant_contract.md`
- `system/assistant/guided_flow_contract.md`
- `system/assistant/safe_write_contract.md`
- `system/diagnostics/doctor_contract.md`
- `system/prompts/prompt_contract.md`

## Client capability boundary

Canonical behavior remains client-neutral and adapters remain thin. Clients with
authorized local write capability may apply a confirmed change and run the real
validators. Web or other no-write clients provide the same questions,
recommendations, and preview, but explicitly state that nothing was written and
must not claim that local validation ran.

Future helpers or connectors may implement the same contracts without changing
their semantics.

## Public and private boundary

The public repository must not contain real Personal facts, sensitive content,
private project state, user-specific absolute paths, private deployment or
adapter configuration, credentials, raw secrets, or Personal Git history.
Authorization is resolved before loading, and diagnostics or discovery must not
leak denied content or secret values.

Reusable prompts remain fact-light. Durable Personal facts belong to separately
resolved canonical context rather than reusable prompt bodies.

## V1 scope

V1 includes:

- a safe public repository and clean reusable Core foundation;
- beginner setup, multilingual onboarding, and AI-client connection guidance;
- the Personal SoT Assistant and basic Personal context onboarding;
- adaptive project creation, project use, and current-state maintenance;
- capability and prompt discovery;
- guided prompt building with reuse-before-create and safe writes;
- basic profile, format, tone, depth, and control guidance;
- validation, beginner-friendly Doctor diagnostics, and a safe update path;
- beginner documentation and truthful capability reporting.

## V1 non-goals

V1 does not require a GUI, Obsidian plugin, MCP server, cloud backend, vector
database, accounts, mobile app, background agent, autonomous self-modification,
prompt marketplace, or hidden auto-repair.

## Definition of Done

Public Personal-SoT V1 is complete when evidence shows that:

1. a beginner can follow the target journey without learning repository internals;
2. the Assistant provides the approved categories and interaction modes through one canonical runtime;
3. project create/use/update and prompt discover/reuse/build flows work end to end with honest client capability boundaries;
4. every material write is previewed, confirmed, current-state checked, authorized, validated, and truthfully reported;
5. read-only discovery is usable without unnecessary confirmation;
6. multilingual guidance, adaptive questions, recommendations, examples, and progressive disclosure are present where required;
7. public/private, access, secret, and fact-ownership boundaries are preserved;
8. relevant tests, Core validation, prompt validation, and public-distribution validation pass;
9. beginner documentation covers setup, first useful work, diagnosis, discovery, and safe maintenance;
10. no V1 non-goal has become a hidden dependency of the core product.

## Change governance

Product changes that materially affect target users, beginner UX, product scope,
public/private boundaries, client capability semantics, or the Definition of Done
must be reviewed against this contract. Other files reference this owner rather
than copying the product contract.
