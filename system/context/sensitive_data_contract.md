# sensitive_data_contract

## purpose

Defines how AI-relevant sensitive personal context and secret references may be represented without turning the Git-backed Source of Truth into a secret store.

## core_rule

```text
sensitive_context → may be stored when useful and deliberately authorized
raw_secret        → must not be stored in Git-backed context
```

A private repository/branch or `ai_access: restricted` is not a secret manager.

## sensitive_vs_secret

Sensitive context may include medical constraints, high-level financial obligations, residence status, private family constraints, or confidential planning context.

The repository MUST NOT store passwords, API tokens, private keys, recovery codes, session cookies, one-time authentication codes, full payment-card credentials, bank-login credentials, or secret security answers.

## location_and_atomicity

Sensitive personal context lives under:

```text
workspace/context/personal/sensitive/
```

The directory is a risk/access boundary, not a semantic atom. Split only when separate retrieval, lifecycle, or materially lower privacy/token exposure justifies it. Do not create one file per fact and do not let broad health/finance/admin files become dumping grounds.

A Personal overlay MAY establish a two-tier organization beneath this boundary:

```text
sensitive/main_info/
→ important, specialized, domain-owned restricted context

sensitive/general_info/
→ low-stakes restricted Personal/household facts that are potentially reusable but do not justify a dedicated semantic owner
```

This is a Personal overlay convention, not a universal requirement for organization or project context.

When this convention exists:

- prefer an established specialized `main_info` owner only when the candidate satisfies the stricter main-info criteria below;
- otherwise use the established `general_info` catch-all for concrete low-stakes facts rather than inventing one file per minor category;
- the catch-all intentionally uses a lower importance threshold than specialized owners;
- low importance does not mean low integrity: do not store facts known to be false, superseded current-state claims, unsupported inference, or raw secrets;
- ambiguity/conflict that could change the stored meaning follows effective `controls.clarify_risk` before the affected write.

## main_info_strictness

`main_info` is the high-integrity Personal sensitive layer. A candidate should be written there only when all applicable conditions are satisfied:

- the fact is materially useful to future reasoning, decisions, health/admin/financial handling, or another established specialized domain;
- the fact is durable/current enough to justify canonical storage, or belongs to an explicitly longitudinal/history owner;
- the specialized owner clearly matches the semantic domain;
- the source/evidence is sufficiently clear for the consequence of being wrong;
- units, dates, identity/relationship, current-vs-historical status, and other meaning-changing qualifiers are known when they matter;
- the candidate has been reconciled against relevant canonical state and does not create an unresolved duplicate or contradiction;
- any material ambiguity/conflict is resolved before the write.

For higher-impact facts, prefer stronger provenance when available. Document-confirmed, clinician/lab-confirmed, official-document-confirmed, implementation-verified, or otherwise independently verifiable evidence is stronger than an AI inference. User-reported facts remain valid evidence when the domain naturally depends on user report, but the owner should preserve provenance/confidence when that distinction matters.

Do not promote a low-stakes fact into `main_info` merely because a specialized filename seems approximately related. If the fact is useful but does not meet the stricter threshold, keep it in the established `general_info` catch-all when appropriate or leave it unresolved when its meaning cannot be safely represented.

## general_info_integrity

`general_info` is permissive about importance, not permissive about contradiction.

Before writing a new or changed current fact to the catch-all:

1. inspect the relevant existing `general_info` entries and any obvious specialized owner that could already own the same fact;
2. determine whether the candidate is new, equivalent, a clearer restatement, a newer current value, historical evidence, or a genuine conflict;
3. avoid duplicate aliases that express the same fact in incompatible wording or units;
4. never silently assume equivalence between labels/systems when that mapping is not established;
5. when a clearly newer current value supersedes an older one, update/mark the old current value rather than retaining two contradictory current facts;
6. when both values may legitimately coexist because they refer to different dates, systems, contexts, people, or scopes, preserve those qualifiers explicitly;
7. if the conflict cannot be reconciled deterministically, follow `controls.clarify_risk` before the affected write.

The goal is broad retention of useful low-stakes facts while maintaining a single coherent canonical interpretation of current Personal context.

## access_default

Sensitive AI-relevant modules should normally use `ai_access: restricted`. Natural-language prompt text is not authorization. Restricted authorization must come from the effective trusted adapter/resolver configuration, such as a canonical authorization profile defined by `system/context/access_contract.md`. If authorization cannot be evaluated deterministically, fail closed. `deny` remains appropriate for content that should never enter AI context.

## third_party_personal_context

A fact is not categorically prohibited merely because it concerns another person.

When a third-party fact is useful to represent the user's own household, family, caregiving, administrative, financial, or health context, it may be stored in the appropriate restricted Personal semantic owner when deliberately supplied/approved by the user and effective access authorization permits the operation.

Apply minimization:

- store only facts useful to the user's Personal/household context;
- prefer relationship/context facts over broad unrelated biographical detail;
- do not create dossiers, surveillance histories, or general archives about another person;
- separate materially different third-party sensitive domains when retrieval/privacy boundaries justify it;
- do not infer consent, diagnoses, secrets, identifiers, or facts not actually supplied by authorized evidence.

An established `general_info` catch-all may contain ordinary low-stakes spouse/household facts when they are relevant to the user's own context and no specialized owner is justified. Sensitive medical, financial, insurance, legal, identity-document, or similarly high-impact third-party details should remain in an appropriate specialized owner or external source rather than being flattened into the catch-all.

## longitudinal_health_context

Health context may require both a current summary and dated historical evidence for trend analysis. Keep those roles distinct.

Typical pattern:

```text
current/baseline health owner
→ compact effective state used for current reasoning

dated measurement history
→ repeatable body/vital measurements with date and units

dated laboratory history
→ laboratory values with date, units, and source/reference context when available
```

For longitudinal records:

- preserve measurement date; use collection date for laboratory results when known;
- preserve units exactly; do not silently normalize or convert units in canonical evidence;
- preserve reference ranges only when they come from the source/lab and remain associated with that result;
- record fasting/non-fasting or other collection context only when known and materially relevant;
- distinguish user-reported values from document/lab-confirmed values when that affects confidence;
- do not overwrite older measurements merely because a newer result exists;
- keep current summaries compact and derive trends from dated history rather than copying the full history into every health owner;
- do not store a model-generated diagnosis as canonical fact; clinician-confirmed diagnoses or durable user-reported conditions belong in their proper health owner with provenance/context when useful;
- raw reports/scans should remain external when possible; store the minimum structured values and a safe document reference when useful.

Trend calculations and interpretations are normally derived at analysis time. Canonicalize a derived trend only when it is itself a durable reviewed fact or decision-relevant state, not merely because an AI calculated it once.

## host_and_repository_boundary

Effective access requires both host/tool permission and canonical `ai_access`. A Git branch is not a security boundary.

## secret_references

A safe `secret_references.md` may contain minimal locator labels to an external encrypted store but never secret values.

## data_minimization

Prefer high-level facts, redacted identifiers, derived constraints and external-document references over raw scans, full account/government identifiers, full medical records or transaction history.

For a Personal `general_info` catch-all, minimization primarily means concise factual storage rather than refusing harmless low-stakes details solely for lack of strategic importance.

For longitudinal health evidence, structured dated measurements are appropriate when trend analysis benefits from retaining them; this does not justify copying entire medical records into Git.

## relevance_and_progressive_disclosure

Authorization does not imply loading. Validate authorization/scope/applicability, then load only the minimum relevant sensitive atoms. A catch-all may contain many low-stakes facts but should be retrieved only when relevant to the active task.

## currentness

Separate current sensitive state from historical evidence when mixing them would be misleading or wasteful. For catch-all current facts, replace or mark a superseded value when the user clearly supplies a newer current value; preserve history only when the fact is explicitly useful as history.

## diagnostics

Diagnostics may say relevant sensitive context exists but is restricted/unavailable; they must not reveal its content.

## examples

Fake developer examples live under:

```text
guides/developer/examples/context/personal/sensitive/
```

They are non-runtime and never registered as real scopes.

## personal_overlay_rule

An installed Personal workspace may contain deliberately reviewed real sensitive context and may adopt the `main_info/general_info` convention above. System changes follow the public repository branch flow. Personal/sensitive data never flows into public system contracts.

## acceptance

A compliant system keeps raw secrets out of Git, fails closed on unresolved restricted authorization, permits minimized useful third-party Personal context when properly authorized, supports an optional Personal specialized-plus-catch-all sensitive layout, applies a stricter evidence/durability/conflict-free threshold to `main_info`, keeps `general_info` permissive about importance but coherent and conflict-aware, separates longitudinal health evidence from compact current state, and loads only the minimum relevant authorized sensitive atom.
