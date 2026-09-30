# prompts

## purpose

System-owned contracts for the reusable Prompt Library.

Concrete reusable prompt templates live under `workspace/prompts/` and may be used across ChatGPT, Codex, Claude, and future AI clients.

The user-managed library is intentionally dynamic: prompt files may be added, edited, renamed, reorganized, deprecated, or deleted without changing factual context ownership or the system contracts here.

## boundary

```text
workspace/context/               = what the AI knows
system/behavior/                  = reusable operating capability
workspace/profiles/               = reusable behavior/presentation composition defaults
workspace/presentation/formats/   = response representation
workspace/prompts/                 = reusable user-request templates
system/prompts/                    = prompt schema/action/parameter/discovery contracts
```

Prompt templates must not become a second factual Source of Truth or duplicate format/profile instructions.

## identity

Prompt identity is its repository-relative path under `workspace/prompts/`, without `.md`.

```text
workspace/prompts/coding/review_pr.md
→ coding/review_pr
```

No flat prompt registry is required. Exact path resolution is authoritative.

## lifecycle

Canonical status values:

```text
active
draft
deprecated
```

- `active`: may be rendered with `@edit` and executed with `@run`;
- `draft`: may be rendered with `@edit`; `@run` fails closed;
- `deprecated`: retained for migration/recovery; `@edit` may render with warning, `@run` fails closed.

## runtime actions

```text
@run:<path>      → render + validate + execute
@edit:<path>     → render + validate + show only
@delete:<path>   → analyze deletion + show plan + require ordinary confirmation
```

Parameters use:

```text
@param:<name>=[value]
```

See `prompt_contract.md`, `parameter_contract.md`, `action_contract.md`, and
`explorer_contract.md`.

## token_efficiency

Prompt discovery uses the bounded, metadata-first behavior in
`explorer_contract.md`. Prefer exact-path lookup; use targeted search/tags only
when the user is discovering a prompt by topic.

Only the selected prompt template plus required referenced runtime modules enter prompt construction.
