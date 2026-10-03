# AI Source of Truth bootstrap

> GENERIC EXAMPLE `CLAUDE.md`. Replace placeholders before deployment.

## canonical source

- source_of_truth_root: `<SOURCE_OF_TRUTH_ROOT>` <!-- EDIT_ME -->
- default_scope: `<OPTIONAL_RUNTIME_SCOPE>` <!-- EDIT_ME_OR_DELETE -->
- default_profile: `code/review` <!-- EDIT_ME_OR_DELETE -->

## operating rules

1. The configured Source of Truth is authoritative for the canonical knowledge and reusable AI contracts it owns.
2. Resolve explicit prompt switches and scope using the canonical routing contracts.
3. Use progressive disclosure: load the minimum sufficient authoritative context, then expand only when the task needs deeper evidence.
4. Validate context access before loading. `restricted` requires deterministic authorization outside this file; `deny` never loads.
5. Use `behavior/coding.md` for reusable coding execution discipline instead of copying it here.
6. Do not duplicate project architecture, stack, personal facts, policies, or decisions in `CLAUDE.md`.
7. If canonical files are unreachable from the active environment, say so and request/resolve access rather than guessing.

## claude_specific

Keep only genuinely Claude-specific repository workflow instructions here. If the client supports imports/discovery, do not use them to load unrelated Source-of-Truth files unconditionally.
