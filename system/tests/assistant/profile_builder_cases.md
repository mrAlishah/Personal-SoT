# Profile Builder scenario acceptance cases

These are non-executable semantic review cases for
`system/assistant/profile_builder_workflow.md`. They are not RED → GREEN test
evidence; executable behavior lives in
`system/tests/personalization/test_profile_builder.py`.

## Direct composition

User wants formal, short responses for the current task.

Expected: recommend direct tone + depth composition and do not create a Profile.

## Repeated reusable combination

User confirms that the same multi-lane combination is repeatedly useful and no
existing Profile owns it.

Expected: offer the smallest Profile manifest, show its complete preview, and
wait for confirmation.

## Similar existing Profile

A highly similar Profile exists but the requested intent may have a different
semantic owner.

Expected: similarity does not authorize edit. Explain reuse, new Profile, and
same-owner edit effects and ask one material question.

## Fact or copied instructions

The candidate includes a durable Personal/project fact, context path, or copied
component prose.

Expected: stop before write, keep the fact in its canonical context owner, and
keep the Profile as a compact manifest of identities/defaults only.

## Unsupported component write

The request would create or edit a format, tone, depth, control, behavior,
registry entry, or precedence rule.

Expected: explain the V1 boundary and do not route it through Profile Builder.
