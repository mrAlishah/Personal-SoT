# runtime_control_validation_cases

These scenarios validate static checking of profile runtime controls.

## case_01_valid_registered_control

Profile frontmatter contains:

```yaml
controls:
  clarify: true
```

Expected: static profile validation accepts the control.

## case_02_valid_false_value

Profile frontmatter contains:

```yaml
controls:
  clarify: false
```

Expected: static profile validation accepts the control.

## case_03_unknown_control_rejected

Profile frontmatter contains:

```yaml
controls:
  arbitrary_toggle: true
```

Expected: static validation reports unsupported profile control `arbitrary_toggle`.

## case_04_invalid_control_value_rejected

Profile frontmatter contains:

```yaml
controls:
  clarify: off
```

Expected: static validation rejects the value and requires exact `true` or `false`.

## case_05_controls_top_level_is_supported

Profile contains a valid `controls:` map.

Expected: `controls` is not reported as an unsupported top-level profile field.
