# v1_1_readiness

## status

```text
scope: generic_core_extension
feature: prompt_library + presentation_correctness + conversation_recap + repository_layout
implementation: accepted
manual_contract_review: complete
repository_layout_refactor: complete
layout_roots: workspace + system + guides
core_validation: passed
personal_validation: passed
release_state: frozen
frozen_on: 2026-08-27
```

## validation_evidence

```text
validated_core_implementation_sha: cfa3e84da2643480e0f7cc3bc8a2130698095610
validated_personal_implementation_sha: 3c11686ff7b42b1c06471e93b5e8954c65a0eee4

core:
  V1 static validation PASSED (mode=core)
  V1.1 prompt validation PASSED

personal:
  V1 static validation PASSED (mode=personal)
  V1.1 prompt validation PASSED
```

The validation evidence refers to the implementation heads above. Release-attestation commits that only update files under `system/release/` do not change runtime semantics and are recorded separately from the validated implementation SHAs.

V1.1 preserves priority:

```text
1. quality_and_correctness
2. token_efficiency
3. atomic_and_composable_context
```

## repository_layout

```text
workspace/ → end-user managed canonical content/configuration
system/    → runtime contracts, algorithms, validation, governance, tests
guides/    → end-user/developer documentation
```

Logical runtime syntax is unchanged. Physical mapping is authoritative in `system/layout_contract.md`.

Key mappings:

```text
@ctx        → workspace/context/
@profile    → workspace/profiles/
@fmt        → workspace/presentation/formats/
@tone       → workspace/presentation/tones/
@depth      → workspace/presentation/depth/
prompt path → workspace/prompts/
```

Profiles resolve directly by exact canonical filename under `workspace/profiles/`; they are not duplicated in the flat switch registry.

## carried_v1_1_features

```text
Prompt Library + exact path identity
@do/@edit/two-phase @delete
@param single/multiline values
reusable ai/recap and ai/context_snapshot prompts
bounded current-thread @recap action
cheatsheet/yaml/md/vocab/concept presentation semantics
human/professional plain keyboard punctuation
public-safe generic prompt promotion governance
exact filename-based profile resolution
```

## layout_invariants

1. only `workspace/`, `system/`, `guides/` are primary implementation/documentation roots;
2. root `readme.md` is navigation only;
3. ordinary end-user maintenance stays in `workspace/`;
4. runtime/schema/algorithm/validation/governance changes stay in `system/`;
5. user and developer documentation stay in separate guide subtrees;
6. fake examples are developer documentation and never runtime context;
7. logical directive identities do not expose physical prefixes;
8. the public foundation contains no real Personal/organization factual context;
9. raw secrets remain forbidden;
10. Personal facts and user-specific content never flow into public system contracts.

## freeze_rule

V1.1 is frozen against the validated implementation SHAs recorded above. Future runtime or architecture changes require a concrete defect or explicit new requirement and start a new reviewed change; release metadata may be updated without redefining the validated implementation.

## declarative_coverage

```text
system/tests/validation/v1_1_repository_layout_cases.md
system/tests/presentation/v1_tone_punctuation_cases.md
system/tests/presentation/v1_1_cheatsheet_cases.md
system/tests/integration/v1_1_conversation_recap_cases.md
system/tests/profile/m7_contract_cases.md
```

## non_goals

No new runtime namespace, MCP, vector DB, prompt scripting language, cross-chat recap, automatic composer insertion, or secret interpolation is introduced by V1.1.
