# history_inventory_contract

## purpose

Defines the minimum inventory record used before migrating historical material into canonical context.

## inventory_unit

The unit is one **candidate claim or instruction**, not one whole conversation.

A long source may produce zero, one, or many candidate records.

## minimum_fields

Use a compact record with these fields:

```text
source_ref
candidate
proposed_scope
proposed_home
sensitivity
temporal_role
action
```

### source_ref

Enough provenance to find the historical source again without copying its full content.

### candidate

Concise extracted fact/rule/preference/decision candidate.

### proposed_scope

The likely owner, for example:

```text
personal
personal/projects/job_search
org/acme
org/acme/projects/payment_service
```

### proposed_home

The narrowest semantic module or policy/decision location matching current contracts.

### sensitivity

Use one of:

```text
normal
sensitive
secret_reference
forbidden_secret
```

`forbidden_secret` must never migrate into Git-backed context.

### temporal_role

Use one of:

```text
current_candidate
historical_only
unknown
```

### action

Use one of:

```text
create
update
ignore
defer
needs_confirmation
```

## authority_rule

Historical chat is evidence, not automatic current authority.

If a candidate conflicts with existing canonical current truth, do not overwrite the canonical fact solely because the historical source is newer or more detailed.

If current truth cannot be determined deterministically:

```text
needs_confirmation
```

## deduplication

Before `create` or `update`:

1. check the proposed canonical home;
2. check parent/nested ownership boundaries;
3. check whether equivalent truth already exists under a different module;
4. consolidate rather than create synchronized copies.

## instruction_classification

Historical prompts/instructions may classify as:

```text
behavior
presentation
profile
policy
adapter_configuration
personal_working_style_fact
```

Do not migrate an old prompt directly until its semantic responsibility is identified.

## sensitive_history

Sensitive candidates require the M9 sensitive-data contract.

Raw secrets are classified `forbidden_secret` and ignored for Git migration even if they appeared historically.

## provenance_after_migration

Canonical files do not need to embed full migration history.

Retain source provenance only when it materially improves verification, decision rationale, or future maintenance. Avoid turning every fact into a verbose audit record.

## acceptance

An inventory record is sufficient when another reviewer can understand what was extracted, where it probably belongs, whether it is sensitive/current, and what action remains without rereading the full source first.
