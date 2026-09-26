---
ai_access: restricted
---
# health_constraints

> FAKE EXAMPLE DATA ONLY. Keep only health facts that materially affect planning or recommendations.

## current_constraints

- seasonal_pollen_allergy: mild <!-- EDIT_ME -->
- exercise_limitation: avoid_high_impact_running_for_4_weeks <!-- EDIT_ME -->

## care_preferences

- preferred_appointment_time: early_morning <!-- EDIT_ME -->

## boundary

Use this atom for concise health constraints that are commonly useful together.

If a real personal context grows into independently retrieved health domains with different lifecycles—for example long-lived cardiometabolic monitoring versus a temporary musculoskeletal limitation—split those domains into separate restricted atoms rather than growing this file indefinitely.

Do not store full medical records, unnecessary identifiers, or raw diagnostic documents when a concise derived constraint is sufficient.
