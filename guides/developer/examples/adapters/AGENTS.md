# AI Source of Truth bootstrap

> GENERIC EXAMPLE `AGENTS.md`. Replace placeholders before deployment. Do not copy fake example data into a real project.

## canonical source

- source_of_truth_root: `<SOURCE_OF_TRUTH_ROOT>` <!-- EDIT_ME -->
- default_scope: `<OPTIONAL_RUNTIME_SCOPE>` <!-- EDIT_ME_OR_DELETE -->
- default_profile: `coding` <!-- EDIT_ME_OR_DELETE -->

## operating rules

1. Treat the configured Source of Truth as canonical for facts, policies, decisions, behaviors, profiles, and presentation modules it owns.
2. Parse explicit leading runtime switches according to the canonical routing contracts.
3. Load only the routing contracts and semantic atoms needed for the task; do not load the full Source of Truth by default.
4. Validate `ai_access` before relevance. Do not expose denied content. Restricted content requires deterministic external authorization.
5. For coding tasks, compose relevant project context/policies with `behavior/coding.md`; do not duplicate those rules here.
6. If required canonical content is unavailable from the current environment, state the limitation instead of reconstructing facts from memory.
7. Do not write canonical project facts into this file. Update the canonical Source-of-Truth module instead.

## repository work

Follow the repository's own build/test/Git conventions. Add only conventions here that are genuinely specific and not already represented in canonical policy/context or normal project documentation.
