# workspace

`workspace/` is the end-user managed surface of the Source of Truth.

Use it for content and configuration that a user may intentionally add, edit, rename, or maintain without redesigning the runtime engine.

```text
workspace/
├── context/       canonical user/organization/project facts
├── prompts/       reusable prompt templates
├── profiles/      reusable composition manifests
├── presentation/  concrete formats, tones, depth and language modules
└── adapters/      user/client bootstrap configuration when present
```

Rules:

- durable facts belong in `workspace/context/`;
- reusable task recipes belong in `workspace/prompts/`;
- profiles reference reusable modules instead of copying facts/instructions;
- presentation modules define user-facing output choices;
- raw secrets remain forbidden;
- runtime identifiers stay stable even if physical storage evolves.

System contracts that define how these files are interpreted live under `system/`.
