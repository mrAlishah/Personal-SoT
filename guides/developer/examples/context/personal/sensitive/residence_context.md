---
ai_access: restricted
---
# residence_context

> FAKE EXAMPLE DATA ONLY. Store only administrative facts needed for residence/document planning.

## residency

- country: germany <!-- EDIT_ME -->
- status: example_skilled_worker_residence <!-- EDIT_ME -->
- valid_until: 2030-06 <!-- EDIT_ME -->
- next_action: review_renewal_requirements_6_months_before_expiry <!-- EDIT_ME -->

## supporting_document_state

- passport_expiry: 2031-04 <!-- EDIT_ME -->
- passport_number: not_stored <!-- KEEP_AS_REFERENCE_PATTERN -->
- current_process: none <!-- EDIT_ME -->

## boundary

Keep residence/status/deadline facts together when they are normally used in the same administrative workflow.

If health insurance, tax administration, or another administrative domain becomes independently useful, give it its own restricted atom instead of turning this file into a general private-administration dump.

Prefer expiry dates, status, required actions, and safe references over full document numbers or scans.
