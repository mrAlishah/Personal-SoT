---
format_id: md
placement: body
---
# md

## purpose

Render the response body as a complete, high-quality Markdown document suitable for direct use in Obsidian or another Markdown-native system.

## placement

When `yaml` is also active, YAML frontmatter appears first and the Markdown body begins immediately after the closing `---` delimiter.

Suffix formats such as `concept` and `vocab` are appended after the body.

## rules

- use valid Markdown headings, paragraphs, lists, tables, blockquotes, and fenced code blocks where useful;
- keep heading hierarchy coherent for both short and long responses;
- preserve code and command formatting exactly when relevant;
- prefer readable Markdown structure over HTML;
- do not wrap the entire document in one Markdown code fence by default, because that breaks nested code fences and direct Obsidian rendering;
- if the user explicitly asks for raw Markdown source as one copyable block, a surrounding fence may be used with safe nested-fence handling;
- `md` changes representation only; it does not change factual scope, behavior, tone, depth, or policy authority.

## long_form

Long responses remain valid Markdown documents. Do not degrade to plain-text pseudo-structure merely because the answer is long.
