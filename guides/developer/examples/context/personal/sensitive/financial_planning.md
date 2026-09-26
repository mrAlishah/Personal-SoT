---
ai_access: restricted
---
# financial_planning

> FAKE EXAMPLE DATA ONLY. Keep planning-level financial context, not transaction-capable credentials.

## baseline

- monthly_net_income_range_eur: 3500_to_4000 <!-- EDIT_ME -->
- maximum_monthly_housing_budget_eur: 1400 <!-- EDIT_ME -->
- recurring_family_support_eur: 250 <!-- DELETE_IF_NOT_APPLICABLE -->

## planning_targets

- emergency_fund_target_months: 6 <!-- EDIT_ME -->
- save_for_home_purchase: true <!-- EDIT_ME -->

## boundary

Use this atom for current household-level planning facts that are normally useful together.

Historical tax-year inputs, transaction history, or a separate business/freelance accounting domain should live in their own restricted atom when they have a different lifecycle or are retrieved independently.

Never store bank passwords, online-banking PINs, CVVs, full payment-card numbers, or transaction authorization codes. Prefer redacted or derived values when exact identifiers are unnecessary.
