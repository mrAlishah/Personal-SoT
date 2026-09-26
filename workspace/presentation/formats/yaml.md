---
format_id: yaml
placement: prefix
---
# yaml

## purpose

Emit an Obsidian-ready YAML frontmatter block at the very beginning of the response.

The V1 switch name remains `@fmt:yaml`, but its canonical semantics are **frontmatter prefix**, not "convert the whole response to YAML".

## placement

When active, the first response content MUST be the opening frontmatter delimiter:

```text
---
```

No heading, greeting, note, or prose appears before it unless a higher-priority safety/host requirement makes that impossible.

## canonical_shape

Use this property set and ordering by default:

```yaml
---
Name: Playwright MCP
Type: Tool Analysis
Subject: AI Browser Automation / MCP / Playwright
Status: Reviewed
Tags:
  - playwright
  - mcp
  - browser-automation
  - ai-agent
  - e2e-testing
  - codex
  - claude-code
Aliases:
  - Microsoft Playwright MCP
  - "@playwright/mcp"
Date Time: 2026-08-25, 07:35 PM
---
```

## field_semantics

### Name

Concise note title representing the current response.

### Type

Concise document/note class such as:

```text
Tool Analysis
Technical Note
Concept Note
Comparison
Research Note
Language Learning
Translation
Troubleshooting
```

Use the most appropriate class for the task rather than inventing overly specific taxonomies.

### Subject

Compact subject hierarchy or topic summary. Slash-separated topic paths are allowed when useful.

### Status

Default:

```text
Reviewed
```

This is a note-lifecycle label. It MUST NOT be interpreted as a claim that all facts were independently externally verified.

An explicit user-requested status may override this default.

### Tags

Use a concise list of high-signal Obsidian tags:

- normally about 3–8 tags;
- lowercase kebab-case when the tag is system-generated;
- no leading `#`;
- prefer concepts/entities actually central to the answer;
- avoid filler synonyms.

### Aliases

Use known useful alternate names, abbreviations, package names, or common labels.

Do not invent aliases merely to populate the field.

If none are useful, emit valid empty YAML:

```yaml
Aliases: []
```

Quote aliases when YAML-special characters make quoting safer.

### Date Time

Use the best reliable current timestamp available from the host/runtime, preferably in the user's local timezone and in this display shape:

```text
YYYY-MM-DD, hh:mm AM/PM
```

Do not fabricate unavailable time precision. If only a reliable date is available, use the date rather than inventing a clock time.

## rules

- emit valid YAML frontmatter, not a fenced YAML code block;
- use the canonical property names/casing above for Obsidian consistency;
- frontmatter describes the response as a note and does not duplicate the answer body;
- keep values concise;
- preserve exact external names in `Name`, `Subject`, or `Aliases` where appropriate;
- metadata must not change factual authority, access, policy applicability, behavior, or response depth.

## composition

`yaml` composes with body and suffix formats:

```text
yaml + md
→ frontmatter + Markdown document

yaml + vocab
→ frontmatter + answer + vocabulary appendix

yaml + concept
→ frontmatter + answer + concept appendix
```

It MUST NOT convert `vocab`, `concept`, `comparison_table`, or other formats into YAML records.
