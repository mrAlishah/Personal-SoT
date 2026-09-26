# sensitive_personal_context_example

This directory demonstrates a **fake** sensitive-context boundary for Obsidian/AI use.

It is intentionally separate from ordinary personal context because authorization and privacy risk are different. The directory itself is not one semantic atom; semantic atomicity still applies inside it.

## default_access

Copied real modules should normally begin with:

```yaml
---
ai_access: restricted
---
```

`restricted` does not mean "safe to load whenever requested". The active adapter/resolver must deterministically prove authorization. Otherwise access fails closed.

## example_modules

```text
health_constraints.md
financial_planning.md
residence_context.md
secret_references.md
```

These are examples, not required filenames.

Choose boundaries by independent usefulness, lifecycle, and retrieval/privacy cost:

```text
independently useful together
→ keep one atom

frequently needed separately
or materially different lifecycle/access exposure
→ split into separate atoms
```

Examples:

```text
current household financial planning
≠ historical tax-year filing data

residence/status workflow
≠ unrelated health-insurance administration

short-lived musculoskeletal constraint
may differ from long-lived cardiometabolic monitoring
```

Do not create one file per individual fact.

## never_store_in_git

Do not place raw secrets here:

```text
passwords
api_tokens
private_keys
recovery_codes
session_cookies
bank_login_credentials
full_payment_card_credentials
```

For such material, keep the protected value in an external encrypted store and record only a minimal safe reference when useful.

## ai_use_pattern

```text
authorization
→ scope/applicability
→ relevance
→ minimum required sensitive atom
```

Do not load the entire sensitive subtree merely because one restricted fact is relevant.

See `context/sensitive_data_contract.md`.
