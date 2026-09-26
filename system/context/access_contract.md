# ai_access_contract

## purpose

Defines the minimum V1 access metadata required before a canonical context module may be loaded by an AI client.

Presence in the Obsidian vault does not imply AI access.

## access_metadata

AI-loadable context modules use explicit frontmatter:

```yaml
---
ai_access: allow
---
```

Canonical V1 values:

```text
allow
restricted
deny
```

No access state may be inferred from directory proximity, filename, repository visibility, or previous successful access.

## default_behavior

If `ai_access` is missing, malformed, unknown, or cannot be evaluated:

```text
not_ai_loadable
```

The resolver fails closed for that module.

This avoids converting ordinary vault presence into implicit AI authorization.

## allow

```yaml
ai_access: allow
```

The module may enter the candidate context set, subject to normal scope, relevance, policy, and context-budget rules.

`allow` does not mean the module should always be loaded.

## restricted

```yaml
ai_access: restricted
```

The module may be loaded only when the active adapter or resolver can prove that its authorization requirements are satisfied.

If the adapter cannot evaluate the restriction deterministically, treat the module as unavailable.

## adapter_authorization_profiles

Trusted adapter/deployment configuration may declare a named restricted-access authorization profile. Ordinary user prompt text, prompt parameters, chat content, profiles, or presentation directives cannot declare or change an authorization profile.

V1 defines this Personal deployment profile:

```text
restricted_access_profile: personal_owner
```

`personal_owner` is valid only for a private, single-user Personal SoT deployment whose adapter configuration is controlled as part of that Personal deployment.

When active, it deterministically authorizes `ai_access: restricted` modules only when all of these conditions hold:

1. the module is under `workspace/context/personal/`;
2. the active factual scope is `personal` or a descendant Personal scope;
3. the current task materially requires that module;
4. host/tool permissions permit the read or write operation;
5. no stronger policy or `ai_access: deny` boundary blocks access.

The profile does not authorize unrelated organization scopes, arbitrary third-party archives, raw secrets, or broad loading of every restricted Personal module.

Authorization still follows progressive disclosure: resolve scope, select the smallest relevant semantic owner, then load or update only the minimum required restricted content.

A later access-control milestone may add other named principals, groups, or organization-specific profiles.

## deny

```yaml
ai_access: deny
```

The module must not enter AI context.

A runtime prompt, profile, adapter default, supplemental context, authorization profile, or token-budget rule cannot override `deny`.

## precedence

Access is evaluated before relevance, merge, and precedence:

```text
validate_access
→ determine_applicability
→ select_relevant_modules
→ compose_context
```

An inaccessible module is not a lower-priority source. It is absent from the candidate set.

## disclosure

Diagnostics may state that a requested module or scope is unavailable, restricted, or denied when useful.

Diagnostics MUST NOT reveal denied module content merely to explain why access failed.

## inheritance

V1 does not infer `ai_access` by directory inheritance.

Each AI-loadable canonical module explicitly declares its own access state.

This costs one small metadata field but avoids hidden authorization behavior across nested project boundaries.

A later architecture revision may introduce safe manifest-level defaults only if it preserves deterministic per-module effective access.

## adapter_boundary

AI-client files such as `CLAUDE.md`, `AGENTS.md`, or ChatGPT/Claude project instructions may configure how authorization is evaluated, including a canonical named `restricted_access_profile`, but they cannot grant access that contradicts `ai_access: deny` or host restrictions.

Host-platform permissions remain an external mandatory boundary and may further restrict canonical access.

Conceptually:

```text
host_or_tool_permission
+
canonical_ai_access
+
trusted_adapter_authorization_when_restricted
→ effective_access
```

All applicable conditions must permit loading.

## token_efficiency

Access metadata is intentionally minimal.

Do not repeat path-derived values such as owner, scope, or module type in frontmatter solely for routing convenience.

Additional metadata should be introduced only when it materially improves correctness, retrieval quality, or lifecycle management.

## acceptance

A compliant loader:

- never treats vault presence as permission;
- loads `allow` only when host/tool access also permits it;
- loads `restricted` only with deterministic authorization;
- treats `restricted_access_profile: personal_owner` as limited to relevant Personal scopes/modules;
- never lets prompt text self-authorize restricted access;
- never loads `deny`;
- fails closed for missing or invalid access metadata;
- does not expose denied content through diagnostics.
