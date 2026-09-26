---
ai_access: restricted
---
# secret_references

> FAKE EXAMPLE DATA ONLY. This file contains **references**, never secret values.

## password_manager_references

- github_work_account: password_manager/example/github_work <!-- EDIT_ME -->
- primary_email_account: password_manager/example/email_primary <!-- EDIT_ME -->

## encrypted_document_references

- passport_scan: encrypted_archive/example/identity/passport <!-- EDIT_ME -->
- tax_documents: encrypted_archive/example/finance/tax_2025 <!-- EDIT_ME -->

## key_references

- personal_ssh_key: secure_key_store/example/personal_ed25519 <!-- EDIT_ME -->

## explicit_non_values

```text
password = NOT_STORED
api_token = NOT_STORED
private_key = NOT_STORED
recovery_code = NOT_STORED
```

## use_rule

The AI may use a safe reference only when the task actually needs to identify where protected material lives and restricted authorization is satisfied. The protected value itself remains outside the Git-backed Source of Truth.
