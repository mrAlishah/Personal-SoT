# fake_history_inventory_example

> FAKE EXAMPLE DATA ONLY. This demonstrates inventory records before canonical migration.

| source_ref | candidate | proposed_scope | proposed_home | sensitivity | temporal_role | action |
| --- | --- | --- | --- | --- | --- | --- |
| chat_2026_01_backend | User's durable primary role is backend engineering | personal | identity.md | normal | current_candidate | create |
| chat_2026_02_learning | Active goal is German B2 | personal | goals.md | normal | current_candidate | create |
| chat_2025_old_stack | User used MySQL on an old project | personal | tech_profile.md | normal | historical_only | defer |
| project_chat_42 | Payment service currently uses PostgreSQL | org/acme/projects/payment_service | stack.md | normal | current_candidate | update |
| project_chat_43 | PostgreSQL was selected for transactional consistency requirements | org/acme/projects/payment_service | decisions/use_postgresql.md | normal | historical_only | create |
| admin_chat_11 | Residence status expires in 2030-06 | personal | sensitive/administrative_context.md | sensitive | current_candidate | create |
| old_prompt_7 | Prefer mental models before precise rules | personal | working_style.md | normal | current_candidate | create |
| secret_chat_9 | API token value appeared in transcript | personal | none | forbidden_secret | historical_only | ignore |
| conflicting_chat_12 | User location conflicts with current canonical identity | personal | identity.md | normal | unknown | needs_confirmation |

## notes

- The inventory is temporary migration working material, not runtime context.
- `historical_only` does not automatically mean "ignore"; it may become a decision/evidence record or durable experience fact.
- `forbidden_secret` never migrates into Git-backed context.
- Resolve by semantic domain, not chronological chat order.
