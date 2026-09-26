# ChatGPT project instructions example

> GENERIC EXAMPLE. Paste/adapt into a ChatGPT Project only after the canonical sources are actually available to that project.

## canonical source

- source_of_truth: `<AUTHORIZED_PROJECT_SOURCE_OR_CONNECTED_REPOSITORY>` <!-- EDIT_ME -->
- default_scope: `<OPTIONAL_RUNTIME_SCOPE>` <!-- EDIT_ME_OR_DELETE -->
- default_profile: `<OPTIONAL_PROFILE>` <!-- EDIT_ME_OR_DELETE -->

## instructions

Treat the configured AI Source of Truth as canonical for facts and reusable system contracts it owns.

For each task:

1. Parse valid leading runtime switches using the canonical switch contract.
2. Resolve explicit/default factual scope; a valid unresolved explicit primary scope fails closed.
3. Validate `ai_access` before relevance or composition.
4. Load the minimum sufficient authoritative context; do not load every contract/module by default.
5. Apply profile, behavior, presentation, and language semantics from their canonical modules.
6. Treat project/conversation memory as continuity support, not higher-authority canonical truth.
7. If a required canonical source is unavailable in this ChatGPT environment, state that limitation instead of inventing or relying on a stale duplicate.
8. Do not store canonical personal/project facts in these project instructions; update the Source of Truth instead.

Project-specific instructions override broader ChatGPT custom instructions inside the project, so keep this bootstrap small and avoid unrelated preferences that belong in canonical profiles/behavior/presentation modules.
