# prompt_contract

## purpose

Defines the canonical representation and boundaries of reusable prompt templates.

## core_rule

A prompt is a reusable request template. It may reference runtime profiles/formats/tone/depth by identity, but it must not duplicate canonical facts or instructions owned by those modules.

## file_identity

Canonical prompt files live under:

```text
workspace/prompts/<topic>/<nested_path>/<prompt_name>.md
```

Runtime identity is the exact relative path below `workspace/prompts/` without `.md`.

```text
workspace/prompts/code/review.md
→ code/review
```

Identifiers use lowercase `[a-z0-9]+` path segments joined by `/`, no underscores. Identity is case-sensitive; no aliases or fuzzy matching are implicit.

## representation

A prompt file is Markdown with YAML frontmatter followed by the template body.

Allowed manifest fields:

```text
prompt_status
prompt_tags[]
prompt_profiles[]
prompt_formats[]
prompt_tone
prompt_depth
required_params[]
optional_params[]
owned_assets[]
```

Unknown fields are configuration defects.

## status

```text
active
draft
deprecated
```

`@run` requires active. `@edit` accepts active/draft and may render deprecated only with a warning.

## runtime_defaults

Prompt manifests may reference reusable composition but never copy its instructions.

```text
explicit invocation switches
>
prompt manifest defaults
>
adapter/project defaults
>
selected profile defaults
```

Explicit `@profile` replaces prompt manifest profile selection. Prompt formats establish a base set before explicit `@fmt/@no:fmt`; explicit tone/depth outrank prompt tone/depth. Prompt manifests never define factual `@ctx` scope.

## context_boundary

A prompt must not embed durable user, organization, or project facts for convenience. Select factual context independently with `@ctx`.

Prompt files do not grant restricted-context authorization.

## template_variables

Variables use exact identifiers:

```text
{{parameter_name}}
```

Every non-reserved variable is declared exactly once in required or optional params. `input` is the reserved implicit body parameter defined by `system/prompts/parameter_contract.md`.

## optional_parameters

If an optional parameter is absent, `@edit` preserves the placeholder and reports it as unbound. `@run` may substitute an empty string only when the resulting template remains valid. V1.1 has no conditions, loops, functions, or expression language.

## owned_assets

Owned assets are allowed only under:

```text
workspace/prompts/_assets/<prompt_identity>/...
```

Shared profiles, formats, context modules, behavior modules, other prompts, system contracts, and arbitrary repository files are never owned assets.

Prompt-to-prompt runtime inclusion/inheritance is not supported.

## dynamic_library

`workspace/prompts/` is intentionally user-maintainable. Adding/editing/removing conforming prompt files does not require an architecture version change. Schema/action changes remain system-owned.

## acceptance

A compliant prompt is path-addressable, fact-light, parameter-valid, composition-friendly, client-neutral, and independently editable without duplicating canonical context/presentation behavior.
