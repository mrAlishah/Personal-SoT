# runtime_control_profile_cases

These scenarios validate the bounded `controls` map in profile manifests.

## case_01_registered_control

Profile:

```yaml
---
controls:
  clarify_risk: false
---
```

Expected: valid profile control default.

## case_02_unknown_control

Profile:

```yaml
---
controls:
  unknown_control: true
---
```

Expected: configuration error; `controls` is not an arbitrary key/value bag.

## case_03_invalid_value

Profile:

```yaml
---
controls:
  clarify_risk: off
---
```

Expected: configuration error; only exact `true` or `false` are valid.

## case_04_omitted_control

Profile has no `controls` field.

Expected: valid; lower-priority project/global control defaults remain available.

## case_05_multiple_profiles

Profile A sets `clarify_risk: true`; later selected Profile B sets `clarify_risk: false`.

Expected among profile defaults: `false`.

## case_06_profile_control_has_no_policy_authority

Profile sets `clarify_risk: false` while a hard policy independently requires user confirmation.

Expected: hard policy remains authoritative; profile control cannot weaken it.
