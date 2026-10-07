# Public Personal-SoT V1 product contract

## Purpose
Define the approved product boundary and completion standard for Public Personal-SoT V1. This file owns product-level V1 decisions; runtime details remain with their referenced canonical contracts.

## Product promise
The target user is a beginner who should not need to understand Git, YAML, registries, prompt engineering, internal paths, feature categories, or SoT architecture for normal use.

The governing product principle is:

```text
simple outside + rigorous inside
```

The normal experience is natural-language-first and multilingual. The Personal SoT Assistant is the single normal beginner entry point: the user states a goal, problem, preference, or uncertainty and the Assistant auto-routes to the smallest canonical workflow. Beginners do not need to select a feature category or learn internal names/directives first.

Guided, Natural, and Expert interaction modes resolve through the same client-neutral canonical runtime; expert directives remain optional and appear through progressive disclosure.

## Beginner journey
```text
install and set up
→ select language and connect an AI client to an authorized canonical SoT source
→ run the system check
→ meet the Personal SoT Assistant
→ create a first project and complete a useful task
→ update project current state
→ discover existing capabilities
→ build or customize only when necessary
```

Guided flows use the selected language, show compact progress when useful, ask one useful adaptive question at a time, explain choices with examples and a recommendation when evidence supports one, and provide an uncertainty-safe option such as `I don't know — recommend one`. Internal schemas and paths stay behind beginner-facing concepts.

## Product behavior
The Assistant exposes six beginner categories as internal navigation and optional explanation; normal beginner requests are auto-routed and do not require category selection:

```text
Discover / Maintain / Create / Customize / Explain / Diagnose
```

A beginner may ask the Assistant to decide what to do, explain the system simply, or review accessible SoT state for a small number of useful improvement recommendations. The Assistant distinguishes:

```text
Explain → Recommend → Preview → Apply
```

so the user can tell when a change is merely being discussed versus actually applied. These are communication boundaries, not new authorities.

Expert shortcuts may expose the same canonical workflows without changing the natural-language-first product model:

```text
@do:setup   initial/resumed setup and setup improvement/update routing
@do:doctor  read-only current system diagnosis
@do:fix     guided usage-help or confirmed repair
```

These shortcuts do not duplicate workflow logic and do not create capability. `@do:fix` is supervised repair, not hidden auto-repair or autonomous self-modification.

User-facing source terminology distinguishes the user's private installation (`sot`) from the upstream reusable product (`sot public`, `mrAlishah/Personal-SoT`). The public source never silently substitutes for the user's private canonical source.

Read-only discovery, explanation, recommendation, and bounded improvement review may run without confirmation. Creation and customization follow reuse-before-create:

```text
exact existing capability
→ composition or parameterization
→ small customization
→ new canonical component only when necessary
```

When response customization can be used transiently, try the existing composition before persisting a new Profile unless the user explicitly asks to save it.

Material canonical writes follow the client-neutral safe-write contract and the risk-based change classification in `system/governance/change_classification.md`:

```text
understand and classify intent
→ resolve scope and semantic owner
→ detect duplication or conflict
→ preview the complete change
→ explicit confirmation
→ re-read/version check
→ authorized write
→ class-required validation/checks
→ truthful report
```

An ordinary private Personal-context update does not require the full Python test/validator suite solely because canonical content changed. Structural Personal-context changes use targeted validation, while reusable system/runtime/governance changes retain governed branch and full-check discipline.

No ambiguous or guessed value becomes canonical truth. Guided questions adapt to the user's answers instead of imposing a fixed universal questionnaire.

The canonical owners for these runtime semantics are:
- `system/assistant/assistant_contract.md`
- `system/assistant/guided_flow_contract.md`
- `system/assistant/safe_write_contract.md`
- `system/governance/change_classification.md`
- `system/adapters/source_access_contract.md`
- `system/diagnostics/doctor_contract.md`
- `system/prompts/prompt_contract.md`

## Client and source capability boundary
Canonical behavior remains client-neutral and adapters remain thin. Local filesystems and host-provided repository/project-source/app connectors are transport choices governed by `system/adapters/source_access_contract.md`; they do not change canonical authority, access, scope, retrieval, or safe-write semantics.

Clients with authorized local or connector-backed read capability may resolve the same canonical source and perform targeted authorized retrieval. A configured repository/source mapping is not proof that the source was actually resolved.

Clients with authorized write capability may apply a confirmed change only through the applicable safe-write workflow. Write capability and local-command/validator capability are independent: a connector-backed or web host with real repository write capability may complete a private change whose resolved class requires no unavailable local validator, while a class that requires validators/tests cannot be reported as validated when the host cannot actually execute them. A genuinely no-write client provides the same questions, recommendations, and preview, explicitly states that nothing was written, and must not claim that local validation ran.

V1 requires a truthful connector-backed read path where the host exposes an authorized source/connector capability. It does not require building a custom connector server. Future helpers or additional connector providers implement the same contracts without changing their semantics.

## Public and private boundary
The public repository must not contain real Personal facts, sensitive content, private project state, user-specific absolute paths, private deployment or adapter configuration, connector credentials/handles that expose private resources, raw secrets, or Personal Git history.

Authorization is resolved before loading, and diagnostics or discovery must not leak denied or unauthorized restricted content, including through connector snippets or previews.

Reusable prompts remain fact-light. Durable Personal facts belong to separately resolved canonical context rather than reusable prompt bodies.

## V1 scope
V1 includes:
- a safe public repository and clean reusable Core foundation;
- beginner setup, multilingual onboarding, AI-client connection guidance, and re-runnable `@do:setup` recovery/improvement routing;
- the Personal SoT Assistant as a noob-first one-entry-point control plane, including auto-routing, help-me-decide guidance, clear Explain/Recommend/Preview/Apply effects, and next-best-action guidance;
- basic Personal context onboarding;
- adaptive project creation, project use, and current-state maintenance;
- capability and prompt discovery;
- guided prompt building with reuse-before-create and safe writes;
- basic profile, format, tone, depth, and control guidance with transient try-before-save customization;
- connector-backed read access to the selected canonical Personal SoT when the host exposes an authorized connector/source capability, with source freshness, no-leak access, and provenance semantics;
- validation, beginner-friendly Doctor diagnostics (`@do:doctor`), a supervised guided repair path (`@do:fix`), and a safe update path;
- beginner documentation and truthful capability reporting.

## V1 non-goals
V1 does not require a GUI, Obsidian plugin, custom MCP/connector server, cloud backend, vector database, accounts, mobile app, background agent, autonomous self-modification, prompt marketplace, or hidden auto-repair.

## Definition of Done
Public Personal-SoT V1 is complete when evidence shows that:
1. a beginner can follow the target journey through the Assistant without learning repository internals, feature categories, or expert directives;
2. the Assistant auto-routes ordinary-language requests through the approved categories/modes, safely handles `I don't know — recommend one`, distinguishes Explain/Recommend/Preview/Apply effects, and offers a useful next action when clear;
3. project create/use/update and prompt discover/reuse/build flows work end to end with honest client capability boundaries;
4. every material write is previewed, confirmed, current-state checked, authorized, receives the validation/checks required by its resolved change class and active repository governance, and is truthfully reported;
5. read-only discovery, recommendation, and explanation are usable without unnecessary confirmation;
6. multilingual guidance, adaptive questions, help-me-decide recommendations, examples, try-before-save customization, and progressive disclosure are present where required;
7. public/private, source-access, canonical access, secret, and fact-ownership boundaries are preserved;
8. relevant tests, Core validation, prompt validation, and public-distribution validation pass;
9. beginner documentation covers setup, first useful work, diagnosis, discovery, customization, and safe maintenance;
10. no V1 non-goal has become a hidden dependency of the core product;
11. when an authorized connector-backed source is available, the runtime can bind one canonical source, preserve access-before-content, retrieve a minimum relevant atom, report truthful source/module provenance, and distinguish source/access failure from canonical absence.

## Change governance
Product changes that materially affect target users, beginner UX, product scope, public/private boundaries, source or client capability semantics, or the Definition of Done must be reviewed against this contract. Other files reference this owner rather than copying the product contract.
