# response_start_language

## purpose

Controls only the language of the response opening without changing the language of the whole response, factual scope, behavior, tone, depth, or format selection.

## configuration

A project/adapter instruction may provide:

```text
start_language: <language>
```

Use a BCP-47-style language code when practical, for example `fa`, `en`, or `de`.

`auto` disables a forced opening language and returns control to the ordinary language lane.

## prompt_switch

A prompt may override the configured default with:

```text
@start:<language>
@start:auto
```

The switch is prompt-local.

## precedence

```text
explicit @start:<language|auto>
>
project_or_adapter start_language
>
none
```

`@start:auto` explicitly clears the lower project/adapter start-language default for the current prompt.

## rendering

`start_language` controls the first human-readable response-owned element.

If no active prefix/starter format owns the beginning of the response, begin the conversational body with at least one natural sentence in `start_language`.

If an active prefix/starter format owns the beginning, preserve that format's required structural prefix and render its first human-readable owned element in `start_language` when that format can represent localized human-readable content.

Example with YAML and `start_language: fa`:

```yaml
---
عنوان: "معماری Source of Truth"
Name: Source of Truth Architecture
...
---
```

The opening `---` remains structurally first; the first human-readable YAML field is Persian.

A starter/prefix that cannot safely or validly represent localized human-readable content keeps its canonical structure; the first eligible human-readable element after it uses `start_language`.

## boundaries

`start_language` is not text direction and does not imply RTL/LTR rendering.

```text
start_language != response_language
start_language != text_direction
start_language != format
```

After the opening requirement is satisfied, ordinary effective language rules continue to control the rest of the response.

It must not make invalid YAML/JSON/XML/Markdown or violate a higher-priority host/safety requirement merely to force a localized starter.

## acceptance

A compliant renderer can force or clear an opening language independently of the overall response language, preserve structural prefix formats, localize the first eligible human-readable starter element, and then return to the ordinary effective language configuration.
