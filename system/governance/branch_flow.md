# branch_flow

## purpose

Defines the branch relationship between generic Core, integration, versioned release staging, and the personalized Source-of-Truth overlay under the three-root repository layout.

## long_lived_branches

```text
v1_ai_context_source_of_truth → generic client-neutral Core canonical
v1_ai_personal_source_of_truth → long-lived personalized overlay when used
develop                       → integration branch for accepted Core changes
```

Personal may contain real end-user content under `workspace/`: context, Personal-only prompts and adapter configuration.

## revision_branches

A stabilization/revision cycle may use versioned staging branches such as:

```text
v<release>_ai_context_source_of_truth
v<release>_ai_personal_source_of_truth
```

A Core revision branch stages reusable changes before promotion to Core canonical. A Personal revision branch stages the corresponding release overlay after accepted Core changes have flowed through `develop`.

Revision branches are release staging surfaces, not new semantic owners. They must not create a parallel implementation of reusable Core semantics.

## one_way_invariant

```text
CORE → PERSONAL allowed
PERSONAL → CORE forbidden
```

Personal facts, sensitive context, project state and Personal-specific prompt contents never merge into generic Core.

A prompt first authored on Personal may be promoted only through explicit generic reclassification/review and a separate Core-owned change with no Personal facts/assumptions.

## reusable_system_change_flow

Outside a versioned revision cycle:

```text
v1_ai_context_source_of_truth
→ fix/feat/refactor Core branch
→ review + python3 system/validation/...
→ v1_ai_context_source_of_truth
→ develop
→ sync accepted Core into the intended Personal branch
```

Inside a versioned revision cycle:

```text
v<release>_ai_context_source_of_truth
→ validate/review
→ v1_ai_context_source_of_truth
→ develop
→ v<release>_ai_personal_source_of_truth
→ Personal validation
```

Do not independently reimplement the same system change on Personal.

## reusable_prompt_promotion_flow

```text
Personal prompt candidate
→ generic applicability review
→ reject/remove Personal facts and assumptions
→ add under workspace/prompts/ through a Core-owned change
→ validate/review Core
→ Core + develop
→ sync Core → intended Personal staging/canonical branch
```

Core becomes authoritative owner after promotion; never merge Personal branch into Core to perform promotion.

## personal_content_change_flow

Conforming Personal facts/prompts/profiles/presentation/config changes are made on Personal-only branches under `workspace/` and validated without changing system contracts.

Prompt schema/routing/action semantics remain system-owned under `system/` and require Core-first change.

## merge_rule

When Core advances, merge/sync Core into Personal while preserving Personal-only `workspace/` content. Never resolve conflict by moving Personal facts/templates into Core.

## deployment_activation

Branch promotion and deployment activation are separate states.

A versioned Personal staging branch may exist and validate while production continues using an older `active_ref`. Production changes only when the authoritative deployment manifest is deliberately updated after the required Core/Personal validation and release gate.

Do not change a deployment manifest merely because a staging branch was created, merged, or synchronized.

## security_boundary

A Git branch is a versioning/logical boundary, not a security boundary. Raw secrets remain forbidden throughout `workspace/`.

## deletion_governance

`@delete:prompt` produces a plan first. Confirmation does not bypass active branch ownership or Git change discipline.

Shared modules are never cascade-deleted merely because a prompt referenced them.

## release_flow

Accepted reusable changes flow Core revision/change → Core canonical → `develop` → intended Personal staging/canonical branch. `main` remains untouched unless a deployment/release action is separately authorized.

A release is not considered active merely because its implementation branches are merged. Deployment manifest selection and final validation remain explicit release gates.

## acceptance

Reusable system semantics evolve in Core; end-user Personal content evolves independently in `workspace/`; Core → Personal lineage remains one-way; versioned revision branches stage rather than duplicate semantics; and deployment activation remains separate from branch promotion.
