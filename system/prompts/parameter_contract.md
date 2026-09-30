# parameter_contract

## purpose

Defines deterministic parameter binding for `@run` and `@edit`.

## syntax

Single-line parameter:

```text
@param:target_language=[german]
@param:role=[Senior Backend Engineer]
```

Multiline parameter uses doubled brackets so ordinary array/code lines containing `]` remain safe:

```text
@param:job_description=[[
We are looking for a Senior Go Engineer.

Requirements:
- Go
- PostgreSQL

Example JSON:
[
  "go",
  "kafka"
]
]]
```

For multiline values, content ends at a line whose trimmed content is exactly:

```text
]]
```

A `]` character or standalone `]` line inside content does not close the parameter.

If the literal content itself needs a standalone `]]` line, write `\]]`; the renderer removes the leading escape backslash during parameter decoding.

## parameter_names

Parameter names use:

```text
[a-z0-9]+(?:_[a-z0-9]+)*
```

They are case-sensitive and must match template variables exactly.

## binding

Explicit `@param` values bind by exact name to `{{name}}` variables.

Invocation body after the leading control block is reserved for `{{input}}` when the selected template contains that variable.

Example:

```text
@run:language/translate_professional
@param:target_language=[german]

من هنوز آن را شروع نکرده‌ام.
```

Binds:

```text
target_language = german
input = من هنوز آن را شروع نکرده‌ام.
```

## precedence

```text
explicit @param:input=[...]
>
implicit invocation body for {{input}}
>
unbound input
```

All other parameters bind only from explicit `@param` in V1.1. Prompt-file parameter defaults are intentionally not supported yet.

## duplicate_parameter

If the same parameter appears more than once, the last explicit occurrence wins and a concise duplicate diagnostic should be available.

## unknown_parameter

An explicit parameter not declared by the selected prompt and not reserved `input` is invalid. Do not silently inject or ignore it without diagnostics.

## required_parameters

For `@do`:

```text
missing required parameter
or unresolved required variable
→ fail closed
→ do not execute
```

For `@edit`:

```text
missing required parameter
→ preserve {{name}}
→ render preview
→ list unresolved required parameters
```

## optional_parameters

For `@edit`, unbound optional parameters remain visible as placeholders and are reported as optional/unbound.

For `@do`, an unbound optional parameter may resolve to an empty string only when no unresolved variable remains and the resulting template remains renderable. Prompt authors must make optional placement omission-safe.

## body_without_input

If invocation body exists but selected template does not consume `{{input}}`:

```text
@do   → fail closed; never discard/append silently
@edit → render preview + report unconsumed body
```

## escaping_and_injection

Parameter substitution is literal.

A parameter value cannot create executable runtime directives after substitution, even if it contains lines such as:

```text
@ctx:personal
@delete:example
```

Multiline decoder only removes the one escape used for a literal standalone closing delimiter:

```text
\]] → ]]
```

## safety

Parameter substitution grants no context authority, tool permission, restricted-data authorization, or destructive capability.

## non_goals

V1.1 does not add conditions, loops, functions, expressions, computed variables, remote parameter lookup, or automatic secret interpolation.
