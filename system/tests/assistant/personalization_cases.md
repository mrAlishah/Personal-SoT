# Personalization scenario acceptance cases

These are non-executable semantic review cases for
`system/assistant/personalization_workflow.md`. They are not RED → GREEN test
evidence; executable composition behavior lives in
`system/tests/personalization/test_advisor.py`.

## Shorter answer

User asks in the selected language for shorter answers.

Expected: classify as depth, discover `short`, explain the result in beginner
language, and show `@depth:short` only in Advanced.

## More formal

User asks for a more formal register.

Expected: classify as tone and recommend current canonical `formal`; do not
change depth, format, or facts.

## Comparison table

User asks to compare alternatives in a table.

Expected: classify as format and recommend `comparison_table`; do not create a
Profile solely for this invocation.

## Step-by-step learning

User wants a guided learning flow one step at a time.

Expected: recommend an evidence-backed composition such as the existing
`technical_learning` Profile with registered `learning=on` and
`step_execution=on`, while preserving behavior/control ownership.

## Deep professional research

User requests deep professional research.

Expected: reuse the existing `research` Profile before proposing anything new.

## Unknown friendly label

The Assistant's interpretation points to an identity that discovery cannot
resolve.

Expected: explain that no current canonical match was found and ask one useful
question or recommend a real alternative; do not persist an alias or invent a
capability.
