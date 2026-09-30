# precedence_rules

## purpose

Defines authority when multiple valid, accessible, applicable sources compete for the same semantic target.

There is no universal precedence chain. Precedence is semantic-lane-specific.

This contract is the canonical owner of source authority and target ownership. `system/routing/scope_resolution.md` determines which scopes/roles exist; `system/routing/merge_strategy.md` applies value-composition mechanics only after this contract has resolved authority.

## external_boundary

Mandatory host, platform, legal, security, tool-permission, history-availability, and access constraints are outside the internal Source of Truth precedence model and cannot be overridden by it.

## applicability_before_precedence

```text
validate_access
→ validate_applicability
→ resolve_authority
```

Invalid, inaccessible, or irrelevant sources do not participate in precedence.

## context_selection_lane

```text
explicit_prompt_context
>
project_or_adapter_default_scope
>
personal_fallback
```

A valid-but-unresolved explicit primary context fails closed.

Prompt templates do not own factual context and therefore do not add another context-selection source.

`@recap` does not participate in factual context selection in V1.1; `@ctx` is invalid with recap so the recap remains grounded in the selected history window.

## context_specificity_lane

Within one primary scope chain, for overridable conflicts:

```text
nearest_specific_scope
>
parent_project_scope
>
owner_scope
```

Hard policies are excluded from winner-takes-all specificity.

## primary_vs_supplemental_lane

Primary and supplemental contexts use target ownership, not peer-style additive composition.

```text
if primary effective context defines target T:
    primary owns T
    supplemental ordinary values/operators cannot modify T
else:
    first authoritative supplemental defining T owns it
    later supplementals cannot mutate it
```

This applies to scalar/list/set/map/soft-policy targets. Hard policies are the exception and all applicable valid hard policies accumulate.

This section owns the cross-context authority rule. Merge mechanics must consume this resolved target ownership and must not restate or independently reinterpret primary/supplemental authority.

## merge_lane

After target authority is established, `system/routing/merge_strategy.md` owns type-aware value composition inside the authoritative scope chain or otherwise-authorized target.

At the authority level, this contract determines which source/value is eligible to participate; it does not redefine scalar/list/set/map operator mechanics.

## policy_lane

Hard policies accumulate and cannot be weakened. Soft policies obey scope/target ownership. Incompatible hard policies produce an explicit conflict.

## runtime_control_lane

Registered runtime controls are runtime configuration, not factual context or policy authority.

For each registered control `controls.<name>`:

```text
explicit current-prompt @control:<name>=<value>
>
explicit chat_or_session control override when supported
>
project_or_adapter controls.<name>
>
selected profile controls.<name>
>
control-specific contextual default when its canonical condition matches
>
global control default
```

Each registered control defines its own allowed values, global default, optional contextual-default conditions, and mode semantics in its canonical control contract. Contextual defaults are default-selection rules only: they are evaluated from already-resolved scope/effective behavior/task intent and never outrank explicit, project/adapter, or profile control values.

The current registered-control set and each target's allowed values/defaults are resolved from `system/routing/switch_registry.md` plus canonical control metadata. This precedence contract does not maintain a second control inventory or value table.

When multiple selected profiles define the same registered control, the later selected profile wins among profile defaults before higher-precedence sources are applied.

A prompt-local `@control:<name>=<value>` changes only the current invocation. A host/session may expose a persistent chat/session override, but clients must not invent persistence when the host has no such capability.

### derived_summary_learning_override

An explicit `@depth:summary` creates a prompt-local derived operation equivalent to:

```text
controls.learning = off
```

This derived operation participates only in the current control block and is ordered with explicit `@control:learning=<value>` operations by source order.

Examples:

```text
@depth:summary
@control:learning=on
→ learning = on

@control:learning=on
@depth:summary
→ learning = off
```

The derived override exists only to prevent learning scaffolding from expanding an explicitly requested operational summary. It does not change factual scope, policy authority, mandatory safety/security behavior, or unrelated controls.

Unknown control names and invalid values are configuration errors and do not silently fall back to a guessed control or mode.

No runtime-control value can weaken external mandatory constraints, required host/tool permission or authorization, applicable hard policies, safety/security boundaries, or explicit fail-closed contracts.

## high_level_action_lane

At most one high-level action is valid per control block.

System actions:

```text
@do:sot
@do:help
@do:assist
```

Prompt actions:

```text
@run
@edit
@delete
```

Conversation action:

```text
@recap:<count>
```

No default high-level action exists. Combining a system action, a prompt action, and/or recap in the same control block is invalid.

No high-level action overrides host/tool/write permissions, history availability, context authority, `ai_access`, hard policies, or Git governance.

## prompt_template_lane

A selected prompt may provide prompt-local profile/presentation defaults but not factual scope.

Profile selection precedence for a prompt invocation:

```text
explicit @profile list
>
prompt_manifest prompt_profiles
>
explicit chat_or_session profile override
>
project_or_adapter default_profile
>
no profile
```

If explicit `@profile` directives exist, prompt-manifest profile selection is not silently composed with them.

Prompt-manifest presentation defaults:

```text
explicit invocation presentation directive
>
prompt manifest direct default
>
explicit chat_or_session override when supported
>
project_or_adapter direct default
>
selected profile default
>
global presentation default
```

For formats, lower-priority prompt/profile/adapter defaults form a base set and explicit `@fmt/@no:fmt` operations apply afterward in source order.

For tone/depth, explicit invocation values outrank prompt manifest values; prompt manifest values outrank selected-profile defaults.

Prompt templates do not define language in V1.1. Existing language precedence remains unchanged. Prompt templates also do not define registered runtime controls in V1.1; use explicit invocation switches or lower configuration sources.

## recap_lane

`@recap:<count>` selects conversation-history input, not factual SoT scope.

History selection:

```text
requested immediately preceding completed exchanges
>
older conversation history
```

Only the requested window participates. Older exchanges are excluded merely because they are available.

When fewer than the requested exchanges are accessible, available history is used with explicit coverage disclosure; unavailable history is never reconstructed from memory or external sources.

Within the selected window:

```text
later explicit correction/supersession
→ may replace earlier conversation state in the recap

unresolved material conflict
→ surface conflict
→ no guessed winner
```

This is recap-state compression, not a claim that recency establishes external factual truth.

## recap_presentation_lane

Recap action defaults are explicit action-local defaults:

```text
behavior: conversation_recap
format: cheatsheet
depth: short
```

For recap presentation:

```text
explicit current-prompt presentation directive
>
recap action default
>
explicit chat_or_session override when compatible
>
project_or_adapter direct default
>
global presentation default
```

`@profile` and `@control` are invalid with recap in V1.1, so profile/control defaults do not participate in the recap action lane.

Format remains additive: recap establishes `cheatsheet` as a base format and explicit `@fmt/@no:fmt` operations apply afterward in source order.

Tone has no recap-specific default. Language follows the ordinary conversation/current-prompt language lane.

## profile_selection_lane

Outside recap, profile selection remains:

```text
explicit @profile list
>
explicit chat_or_session profile override
>
project_or_adapter default_profile
>
no profile
```

Prompt-template invocation may insert prompt-manifest profile defaults as defined above. Profiles cannot override canonical facts or hard policies.

## presentation_lane

Presentation configuration includes format, tone, depth, and language.

For ordinary non-action requests:

```text
explicit_prompt_switch
>
explicit_chat_or_session_override
>
project_or_adapter_direct_default
>
selected_profile_default
>
global_presentation_default
```

Prompt-template and recap actions insert their contracted action-local defaults according to their specific lanes above.

### format

Format is multi-value. Lower-priority sources establish a base set; explicit prompt operations apply afterward in source order.

### tone_and_depth

Tone/depth are single-value. Last explicit invocation value wins within the control block.

### language

```text
explicit_current_prompt_language_request
>
explicit_chat_or_session_language_override_if_supported
>
project_or_adapter_language_default
>
selected_profile_language_default
>
client_conversation_language_fallback
```

V1.1 prompt manifests and recap action defaults do not add a language field.

## parameter_lane

Parameter binding is not factual precedence.

For reserved Prompt Library `input`:

```text
explicit @param:input
>
invocation body
>
unbound
```

Other prompt parameters bind only from explicit `@param` in V1.1.

Parameter values cannot create executable switches after substitution.

`@param` is invalid with recap; recap body is a focus/filter instruction instead.

## delete_lane

Deletion is two-phase and safety-dominant:

```text
@delete:path
→ analyze + plan only
→ STOP for ordinary explicit confirmation bound to the exact displayed plan
```

There is no separate `@confirm:delete` directive; confirmation follows
`system/assistant/safe_write_contract.md`'s ordinary confirmation model.
Before applying, current file/reference state is re-checked against the
confirmed plan; a changed prompt or changed inbound-reference set
invalidates it and requires a new plan.

Shared modules are never cascade-deleted merely because a prompt referenced them.

## adapter_configuration_lane

Adapters may configure runtime defaults and capability wiring only inside their contracted lanes, including registered values under `controls:`. They cannot duplicate canonical prompt contents, facts, policies, or unavailable conversation history to gain precedence.

## canonical_fact_vs_runtime_configuration

Canonical facts, prompt templates, conversation-history evidence, and runtime configuration are different semantic domains.

A historical chat statement does not become canonical SoT fact merely because it appears in a recap.

## temporal_state_lane

Recency alone does not establish factual authority:

```text
scope_authority
>
raw_recency
```

The recap correction rule only represents explicit correction state inside the chosen conversation evidence.

## token_budget_lane

```text
access_and_mandatory_requirements
>
scope/source correctness
>
relevance
>
token_budget
```

Prompt-library optimization loads only the selected prompt and required modules.

Recap optimization reads only the requested accessible exchange window and required recap/format contracts. Compression must not remove operational values or caveats required for correct reuse.

## invalid_and_unresolved_configuration

Invalid/unresolved configuration does not participate in precedence. Remaining configuration may continue only when safe.

Unresolved explicit primary context and unresolved prompt action path fail closed. Unknown registered-control keys or invalid control values are configuration errors. Invalid recap count/action combinations also fail closed rather than silently selecting a different history scope.

## conflict_resolution_order

Prompt-template execution follows `system/prompts/action_contract.md`.

Recap execution conceptually performs:

```text
1. enforce external/history-availability boundaries
2. parse exactly one @recap action + allowed presentation directives
3. validate positive count
4. select accessible immediately preceding exchange window
5. parse optional recap focus body
6. activate conversation_recap + recap presentation defaults
7. apply explicit presentation overrides
8. extract/deduplicate/classify only supported history content
9. preserve later explicit corrections and surface unresolved conflicts
10. render source-grounded quick reference + coverage diagnostic when needed
```

## acceptance

A compliant resolver can explain which semantic lane applies, resolve source authority/target ownership before merge mechanics, resolve registered runtime controls independently from factual/policy authority including canonical contextual defaults, apply the prompt-local source-ordered `@depth:summary → controls.learning=off` derived override, identify which conversation window was selected, explain how action defaults/overrides resolved, why unavailable history was not invented, and why unsafe or ambiguous action combinations failed closed.
