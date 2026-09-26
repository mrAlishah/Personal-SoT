# runtime_switch_syntax

## purpose

Defines the canonical prompt-level control grammar. Runtime directives select context/configuration, invoke reusable prompt templates, bootstrap/re-anchor the current chat, or perform contracted conversation operations without exposing physical repository layout.

Related contracts:

```text
system/layout_contract.md
system/adapters/runtime_bootstrap.md
system/routing/scope_resolution.md
system/routing/merge_strategy.md
system/routing/precedence.md
system/routing/recap_contract.md
system/presentation/start_language.md
system/behavior/control_contract.md
system/routing/switch_registry.md
system/prompts/prompt_contract.md
system/prompts/parameter_contract.md
system/prompts/action_contract.md
```

## control_block

Executable directives are allowed only in a leading control block that starts at the first non-empty prompt line. Ordinary directives occupy one line. A blank line after all closed directives separates the control block from ordinary body text.

Multiline `@param` is the exception: after `@param:<name>=[[`, every following line is literal parameter content until a line whose trimmed content is exactly `]]`. Switch-like text inside that value is data, not executable directives. A standalone `]` is ordinary data; a literal standalone `]]` content line is escaped as `\]]`.

Switch-like text after the body starts, or inside bullets/quotes/code fences, is ordinary text. Directives are prompt-local by default except the contracted same-chat basis established by `@do:initialSoT`.

## canonical_namespaces

```text
@ctx:<path>
@profile:<name>
@fmt:<registered_format>
@tone:<registered_tone>
@depth:<registered_depth>
@start:<language|auto>
@control:<registered_control>=<allowed_value>
@no:fmt:<registered_format>

@do:initialSoT
@do:prompt:<path>
@edit:prompt:<path>
@delete:prompt:<path>
@confirm:delete:prompt:<path>
@param:<name>=[value]
@param:<name>=[[...multiline...]]

@recap:<positive_integer>
```

`@do:initialSoT` is a reserved literal runtime spelling. Its exact case is canonical and it is not a repository-owned identifier subject to lowercase_snake_case naming.

Bare `@prompt:<path>` is unsupported because action intent must be explicit.

## lexical_rules

Repository-owned identifiers use lowercase snake_case; hierarchical context/prompt identities use `/`. Values are exact and case-sensitive. Adapters must not silently fix case, spelling or nearest matches.

`@fmt`, `@tone`, and `@depth` accept exact identifiers registered in the corresponding `system/routing/switch_registry.md` sections. This syntax contract does not maintain duplicate current-identity lists.

`@start` accepts `auto` or a valid configured/supported language code such as `fa`, `en`, or `de`. Unknown/unsupported values fail closed rather than being guessed.

`@control` accepts only a registered control identity from `system/routing/switch_registry.md` and a value allowed by that control's canonical machine-readable metadata. Unknown controls or invalid values fail closed and are not coerced. This syntax contract does not maintain a second current-control value inventory.

`@recap` count is a positive base-10 integer defined by `system/routing/recap_contract.md`.

## physical_resolution_boundary

Public runtime syntax is decoupled from storage paths:

```text
@ctx      → system/routing/context_registry.md → canonical context scope
@profile  → workspace/profiles/<name>.md
@fmt      → system/routing/switch_registry.md → canonical format target
@tone     → system/routing/switch_registry.md → canonical tone target
@depth    → system/routing/switch_registry.md → canonical depth target
@start    → system/presentation/start_language.md
@control  → system/routing/switch_registry.md → canonical registered-control target
prompt path → workspace/prompts/<path>.md
```

Users never include those physical prefixes in directive values.

## context_switch

```text
@ctx:personal
@ctx:personal/projects/<project_path>
@ctx:org/<organization>
@ctx:org/<organization>/projects/<project_path>
```

First valid explicit context is primary; later ones are supplemental. Duplicate contexts are idempotent. Explicit context suppresses automatic `default_scope` composition.

## profile_switch

`@profile:<name>` selects composition manifests from `workspace/profiles/`. Multiple explicit profiles compose in source order; explicit selection replaces lower-priority profile selection for the invocation.

## format_switch

Format is multi-value/additive. Explicit operations execute in source order after lower-priority defaults:

```text
@fmt:yaml
@fmt:eli5
@no:fmt:yaml
→ disabled

@no:fmt:yaml
@fmt:yaml
→ enabled
```

## tone_switch

Tone is single-value; the last explicit prompt tone wins.

## depth_switch

Depth is single-value; the last explicit prompt depth wins and does not change factual scope, policy authority, or execution-flow controls.

`@depth:summary` is the explicit operationally compressed mode defined by `workspace/presentation/depth/summary.md`.

For the current prompt, an explicit `@depth:summary` also derives `controls.learning = off` in the runtime-control lane so learning scaffolding does not expand the summary. Directive order remains authoritative for this derived interaction: a later explicit `@control:learning=on` in the same control block re-enables learning intentionally. A `@control:learning=on` that appears before a later `@depth:summary` is superseded by the derived `learning=off`.

This derived interaction changes only optional learning behavior; it does not bypass mandatory constraints or alter factual authority.

## start_language_switch

`@start:<language>` controls only the first human-readable response-owned element according to `system/presentation/start_language.md`.

```text
@start:fa
```

forces a Persian opening for the current prompt while leaving the ordinary response-language lane unchanged after that opening requirement is satisfied.

```text
@start:auto
```

clears any lower project/adapter `start_language` default for the current prompt.

The last valid explicit `@start` in the control block wins.

## registered_control_switch

Generic form:

```text
@control:<registered_control>=<allowed_value>
```

The directive sets the named registered control for the current prompt only. The last valid explicit directive or contracted derived override for the same control in the control block wins in source order.

Control semantics remain canonical in the registered target contract; the runtime syntax does not redefine them.

No control value can disable external mandatory constraints, host/tool permissions, required authorization, applicable hard policies, safety/security boundaries, or explicit fail-closed contracts.

## high_level_action_exclusivity

At most one high-level action may appear in one control block: one bootstrap action, one prompt action, or one recap action. Combining high-level actions is invalid.

## initial_sot_action

```text
@do:initialSoT
```

Invokes `system/adapters/runtime_bootstrap.md` semantics. It accepts no `@param`, needs no body, and every invocation performs the same resolve + reload + re-anchor operation for the current accessible chat. It may be used at chat start or later after drift.

Do not combine `@do:initialSoT` with `@ctx`, `@profile`, presentation switches (including `@start`), `@control`, prompt actions, `@param`, or `@recap`; effective defaults/configuration are resolved from the active deployment/bootstrap according to the runtime contract.

## prompt_action

Prompt identity resolves exactly to:

```text
workspace/prompts/<prompt_path>.md
```

No prompt registry or fuzzy lookup participates. `@do` and `@edit` may coexist with context/profile/presentation directives, registered `@control` directives, and parameter bindings. `@delete`/`@confirm:delete` are maintenance actions and do not accept parameters in V1.1.

## recap_action

`@recap:<count>` selects immediately preceding completed exchanges according to `system/routing/recap_contract.md`. Only presentation companion directives are valid with recap; `@ctx`, `@profile`, `@control`, `@param`, and prompt actions are invalid.

Ordinary body text after the recap control block is an optional focus/filter instruction.

## parameter_directive

Single-line:

```text
@param:target_language=[german]
```

Multiline:

```text
@param:job_description=[[
line one

@fmt:yaml
[
  "array item"
]
]]
```

Parameter semantics are defined in `system/prompts/parameter_contract.md`.

## invocation_body

For Prompt Library actions, body text may bind to reserved `{{input}}` only when the selected prompt consumes it. For recap, body text is only a focus/filter instruction. Body text must not be silently discarded.

## precedence

Explicit invocation directives outrank prompt/profile/action defaults according to `system/routing/precedence.md`. `@start` uses its dedicated precedence in `system/presentation/start_language.md`. Registered `@control` directives and the contracted `@depth:summary` derived learning override use the runtime-control lane in `system/routing/precedence.md`.

## invalid_and_unresolved_directives

Invalid/unresolved directives do not take effect. Never guess prompt paths, context paths, profile names, registered presentation identities, parameter names, start-language values, control identities/values, or recap counts. Unresolved explicit primary context or prompt action path fails closed; invalid explicit registered-control overrides and invalid recap counts fail closed.

## adapter_defaults

Repeated defaults belong in adapter/project configuration. `start_language: <language|auto>` may be supplied there as a response-opening default. Registered runtime controls may be supplied under a bounded `controls:` map using exact registered identities and target-accepted values.

Adapters may wire prompt discovery and history availability but must not duplicate prompt bodies or unavailable conversation history. Reusable bootstrap/re-anchor execution belongs in `system/adapters/runtime_bootstrap.md`, not copied into client wrappers.

## acceptance

A compliant parser identifies directives deterministically while resolving user-facing registered format/tone/depth/control identities through `system/routing/switch_registry.md`, applies the contracted prompt-local `summary → learning=off` derived override in source order, validates each control against the registry and its canonical target metadata, and does not normalize or guess identifiers or values.
