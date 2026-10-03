# runtime_control_profile_cases

These non-executable acceptance scenarios validate the bounded `controls` map
in Profile manifests. They are not RED → GREEN test evidence.

## case_01_registered_control

Profile:

```yaml
---
controls:
  clarify: off
---
```

Expected: valid profile control default.

## case_02_unknown_control

Profile:

```yaml
---
controls:
  unknown_control: on
---
```

Expected: configuration error; `controls` is not an arbitrary key/value bag.

## case_03_invalid_value

Profile:

```yaml
---
controls:
  clarify: false
---
```

Expected: configuration error; only exact canonical `on`, `off`, or `auto`
values are valid for this control.

## case_04_omitted_control

Profile has no `controls` field.

Expected: valid; lower-priority project/global control defaults remain available.

## case_05_multiple_profiles

Profile A sets `clarify: on`; later selected Profile B sets
`clarify: off`.

Expected among profile defaults: `off`.

## case_06_profile_control_has_no_policy_authority

Profile sets `clarify: off` while a hard policy independently requires
user confirmation.

Expected: hard policy remains authoritative; profile control cannot weaken it.
