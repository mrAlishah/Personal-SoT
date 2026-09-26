# context workspace

Canonical factual content lives here.

For a new public installation, do not create empty Personal files up front. Guided onboarding should create only the smallest semantically necessary modules after the user previews and confirms the proposed facts.

Personal overlay:

```text
workspace/context/personal/
```

Organization overlay:

```text
workspace/context/organizations/<organization>/
```

The schema, access rules, atomicity rules and sensitive-data contracts are defined under `system/context/`.

Never store raw credentials or secrets here.
