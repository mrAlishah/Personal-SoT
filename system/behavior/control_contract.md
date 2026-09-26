# runtime_control_contract

## purpose

Defines the reusable contract for bounded runtime controls that tune optional AI behavior without changing factual context, policy authority, or presentation ownership.

## core_rule

A registered runtime control configures one coherent optional behavioral lane at runtime.

Controls are configuration, not facts, policies, profiles, or presentation modules.

Conceptually:

```text
behavior capability
+
registered control contract
+
effective control value
→ runtime behavior
```

## registration

Every registered control MUST define:

```text
canonical identity
allowed values
global default
semantics for each value
precedence participation
boundaries that the control cannot override
acceptance behavior
```

A control MAY also define a bounded contextual default when the same control should use a different default for an explicitly identified scope, resolved behavior set, or task-intent class. Contextual defaults belong only in the control's canonical target contract; adapters, profiles, validators, and behavior modules must not independently restate those semantics.

Canonical runtime identities use:

```text
controls.<lowercase_snake_case_name>
```

Unknown control keys are configuration errors.

## machine_readable_metadata

Each registered control target MUST begin with YAML frontmatter containing these required machine-readable registration facts for validators and deterministic consumers:

```yaml
---
control_id: <lowercase_snake_case_name>
control_values:
  - "<exact_allowed_value>"
control_default: "<one_of_control_values>"
---
```

Exact string values SHOULD be quoted so tokens such as `on` and `off` cannot be coerced by YAML 1.1-style parsers.

Ownership rules:

- the control target remains the single semantic owner of its identity, allowed values, default, and behavior semantics;
- `control_id` is the bare registry identity; the runtime configuration key is derived as `controls.<control_id>`;
- `control_values` MUST be non-empty and contain unique exact values;
- `control_default` MUST be one of `control_values`;
- the `switch_registry` identifier for a registered control MUST exactly equal `control_id`;
- validators and profiles MUST consume this metadata rather than hard-code registered control names or value sets;
- prose may explain semantics but MUST NOT become a second machine-readable owner of identity/value/default data.

Additional future machine-readable fields require an explicit contract extension; consumers must not infer semantics from arbitrary undocumented frontmatter keys.

Adding or changing a registered control therefore updates its canonical control target and the compact `switch_registry` mapping when identity/target lifecycle changes; generic validators should not require source-code edits merely to learn the new control name, allowed values, or default.

## value_model

Controls SHOULD use the smallest value set that expresses genuinely distinct behavior.

For adaptive optional controls, prefer:

```text
on
off
auto
```

Semantics:

```text
on   → explicitly enable the control's optional behavior

off  → explicitly disable that optional behavior where higher authority permits

auto → let the runtime apply the control-specific adaptive decision rule
```

Do not add `auto` when it would be indistinguishable from `on` or `off`.

Boolean values are not the canonical V1.2 control value model for newly registered adaptive controls. Existing boolean controls should migrate only through an explicit compatibility decision in their own contract.

## precedence

Registered controls resolve in the runtime-control lane defined by `system/routing/precedence.md`.

General precedence:

```text
explicit current-prompt control override
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

A contextual default is a default-selection rule, not an explicit override. It MUST NOT outrank project/adapter, profile, session, or current-prompt values. Its matching conditions must be deterministic from already-resolved runtime state, such as the active factual scope, effective selected behaviors, or explicit task intent. Do not trigger it from vague keyword matching alone.

When multiple selected profiles define the same registered control, the later selected profile wins among profile defaults before higher-precedence sources are applied.

Prompt-local overrides affect only the current invocation unless a separate host/session capability explicitly provides persistence.

## profile_boundary

Profiles MAY provide registered control defaults under a bounded `controls:` map.

Profiles do not define new control semantics. A profile value is valid only when the control is registered and the value is allowed by the canonical control metadata.

## behavior_boundary

Controls may tune activation or gating of optional behavior, but they do not own the underlying reusable behavior instructions.

If a reusable capability exists as a behavior module, keep its operational method in that module and let the control only determine whether/how that capability is applied.

A behavior module does not independently assign control defaults. When a control needs behavior-sensitive defaults, the canonical control contract owns the behavior-to-default mapping.

## presentation_boundary

Controls MUST NOT own response format, tone, depth, or language.

Examples:

```text
controls.learning = on
→ may require learning-oriented behavior

ELI5
YAML opening
vocabulary table
deep response
→ remain presentation/profile configuration
```

A control may influence whether a presentation choice is useful, but it does not silently activate or mutate presentation modules unless an explicit separate contract defines that composition.

## authority_boundary

No control value may weaken or bypass:

```text
external mandatory constraints
host/tool permissions
required authorization
applicable hard policies
safety/security boundaries
explicit fail-closed contracts
```

`off` disables only the optional behavior owned by that registered control.

## invalid_values

Unknown control keys and invalid values are configuration errors and do not silently coerce, normalize, or fall back to a nearest value.

If an explicit current-prompt control override is invalid, fail that control resolution visibly rather than silently applying a lower-precedence value.

## diagnostics

Runtime/bootstrap diagnostics should report only registered controls actually resolved, using their effective canonical values. When useful for debugging, diagnostics may identify that a contextual default matched, without duplicating the control's semantic rules outside its canonical contract.

## acceptance

A compliant runtime can identify registered controls from the compact registry, read exact identity/value/default metadata from each canonical control target, validate profile/runtime values without hard-coded control tables, resolve controls through the runtime-control precedence lane including bounded canonical contextual defaults, keep behavior/presentation/policy ownership separate, and fail visibly on unknown keys, invalid metadata, or invalid values.
