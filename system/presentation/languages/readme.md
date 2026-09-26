# languages

## purpose

Index of language composition contracts and self-addressing canonical language modules.

Concrete language modules live under:

```text
workspace/presentation/languages/<language>.md
```

The exact filename is the language identity for profile/adapter composition. This README does not maintain a second current-language inventory.

Language configuration uses one primary language and zero or more supporting languages. No `@lang:` switch exists in V1; language is selected by profile/adapter configuration or an explicit current-prompt language request.

Read `language_contract.md` for composition semantics and `system/routing/precedence.md` for language precedence.
