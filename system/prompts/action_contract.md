# action_contract

## purpose

Defines action semantics for rendering, executing, and deleting canonical prompt templates stored under `workspace/prompts/`.

## do

```text
@do:prompt:<path>
```

Pipeline:

```text
resolve workspace/prompts/<path>.md
→ validate prompt status
→ parse invocation parameters
→ bind parameters
→ validate required variables/body consumption
→ resolve explicit switches + prompt defaults
→ resolve factual context independently
→ apply normal access/policy/authority rules
→ execute rendered request
```

`@do` never exposes an intermediate preview unless diagnostics are required. Failure is fail-closed for unresolved path, non-active status, missing required params/variables, unconsumed body, invalid referenced modules, or unavailable required capability.

## edit

```text
@edit:prompt:<path>
```

```text
resolve workspace/prompts/<path>.md
→ parse/bind available parameters
→ render complete preview
→ report unresolved required/optional parameters
→ STOP
```

`@edit` never executes the rendered task.

## delete

```text
@delete:prompt:<path>
```

Phase one is analysis only:

```text
resolve exact workspace prompt file
→ fetch current identity/version
→ identify explicitly owned assets
→ search exact inbound references
→ classify shared vs repairable references
→ produce deletion plan
→ STOP
```

The plan lists the prompt file, owned assets, references to repair/remove, shared dependencies preserved, and blocking ambiguities.

## delete_confirmation

```text
@confirm:delete:prompt:<path>
```

Before applying deletion, re-check file version and inbound-reference state. If changed, abort and require a new plan.

After valid confirmation:

```text
delete workspace prompt file
→ delete only explicitly owned assets under workspace/prompts/_assets/<identity>/
→ repair exact inbound references
→ preserve shared dependencies
→ run structural validation when available
→ commit one coherent maintenance change
```

## shared_dependency_rule

A prompt may reference shared profiles, formats, tones, depth, context scopes, behavior modules, and system contracts. References never imply ownership and deletion must not cascade-delete shared modules.

## prompt_to_prompt_boundary

Runtime prompt inheritance/include/dependency composition is unsupported. Documentation mentions are inbound references, not ownership edges.

## action_exclusivity

One invocation may contain at most one prompt action. Multiple actions are invalid.

## action_boundary

Prompt actions cannot override context authority, `ai_access`, hard policies, host/tool permissions, or Git governance.

An AI client that cannot access/modify `workspace/prompts/` must report that limitation rather than pretend success.
