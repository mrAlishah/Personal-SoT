# Obsidian AI Context Source of Truth

Canonical, client-neutral AI Source of Truth for ChatGPT, Codex, Claude, and compatible agents.

```text
repository_root == vault/99_system/ai/
```

The repository is intentionally organized into three ownership boundaries:

```text
workspace/  -> end-user managed content and configuration
system/     -> runtime contracts, algorithms, validation, governance, tests
Guides are under guides/ (user and developer documentation)
```

Canonical roots:

```text
workspace/
system/
guides/
```

Logical runtime identities do not expose physical storage paths. Existing directives remain stable:

```text
@ctx:personal
@profile:technical_learning
@fmt:yaml
@tone:human
@do:prompt:ai/recap
```

Physical resolution is owned by the system contracts:

```text
context   -> workspace/context/
prompts   -> workspace/prompts/
profiles  -> workspace/profiles/
formats   -> workspace/presentation/formats/
tones     -> workspace/presentation/tones/
depth     -> workspace/presentation/depth/
languages -> workspace/presentation/languages/
```

Start here:

```text
End user  -> guides/user/readme.md
Developer -> guides/developer/readme.md
```

Do not edit `system/` for ordinary personal/content maintenance. Reusable runtime or contract changes remain Core-first and then sync Core -> Personal.
