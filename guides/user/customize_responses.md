# Customize responses

Tell the Personal SoT Assistant what you want in ordinary language. You do not
need to know Profile names, commands, files, or YAML.

For example:

```text
Make the answer shorter.
Use a more formal tone.
Compare these options in a table.
Teach this one step at a time.
Use a deep, professional research style.
```

The Assistant follows this flow:

```text
understand your goal
→ find existing capabilities
→ recommend a composition
→ reuse an existing Profile when useful
→ try it for the current task
→ offer a new Profile only for a repeated combination
```

It asks one useful question at a time when your request is unclear. You can say
“I don't know — recommend one” to get an example and a recommendation.

## What can be combined

- Format changes structure, such as a comparison table.
- Tone changes voice, such as formal or neutral.
- Depth changes how brief or detailed the answer is.
- Controls and behaviors guide an existing interaction, such as step-by-step learning.
- A Profile saves a reusable combination of those existing capabilities.

The Assistant does not create new formats, tones, depth levels, controls, or
behaviors in Public V1. It recommends and combines only capabilities that the
repository can verify.

## Saving a reusable combination

For a one-time request, direct composition is usually enough. If you repeatedly
use the same combination and no existing Profile fits, the Assistant can offer
the smallest Profile manifest.

Before a local write it shows the complete proposed change and waits for your
confirmation. It then rechecks for concurrent changes, writes only the Profile,
and runs Core, prompt, and public-distribution validation. If validation fails,
it clearly says that the file changed and provides a new repair proposal; it
does not silently repair anything.

ChatGPT and Claude Web provide the same guidance and preview. When they do not
have repository write access, they must say that nothing was written and no
validation was run.

## Keep facts separate

Profiles contain only references to existing presentation and behavior
capabilities. Do not put personal facts, project facts, context paths, copied
instructions, or secrets in a Profile. Store facts in their proper context
owner instead.

## Advanced

After the beginner recommendation, an expert may use directives such as
`@profile`, `@fmt`, `@tone`, `@depth`, and registered `@control` forms. These
are optional shortcuts, not required setup knowledge.
