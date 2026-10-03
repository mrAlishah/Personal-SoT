---
format_id: mental
placement: body
---
# mental

## purpose

Render one compact conceptual model that helps the user see how the important parts of a non-trivial concept, mechanism, architecture, workflow, or decision relate.

## activation

This format is rendered only when explicitly selected by profile, prompt, adapter/project default, or `@fmt:mental`.

When active, render it only if the current answer has a meaningful structure, mechanism, flow, hierarchy, lifecycle, dependency, or comparison that benefits from visualization. For trivial answers or isolated facts, omit the block rather than inventing a diagram.

## placement

Place it near the first substantive explanation of the concept it models, normally after the concise direct answer and before detailed analysis.

## output_shape

Prefer a compact text/ASCII model that works reliably in ordinary Markdown clients.

Example:

```text
Context
   ↓
Profile
   ↓
Controls
   ↓
Effective behavior
   ↓
Presentation
```

A small table or short analogy is acceptable when it communicates the structure more clearly than arrows.

## rules

- model the smallest useful set of relationships;
- prefer structure over decoration;
- use canonical terminology already present in the answer;
- localize explanatory labels when useful, but preserve important exact technical names;
- show direction, containment, lifecycle, dependency, or contrast only when supported by the answer;
- do not introduce new factual claims merely to complete a diagram;
- avoid large diagrams, pseudo-UML, or visual complexity unless the task genuinely requires it;
- do not repeat the entire answer in diagram form;
- if no useful mental model exists, omit the block even though the format is active.

## boundaries

`mental` owns only the compact conceptual visualization. It does not activate teaching behavior, increase depth, perform research, or replace `concept`, `compare`, or the main explanation.

## acceptance

A compliant response with `mental` active includes a compact model when it materially improves understanding, omits it when it would be artificial, and keeps the visualization faithful to the explanation already supported by the task/context.