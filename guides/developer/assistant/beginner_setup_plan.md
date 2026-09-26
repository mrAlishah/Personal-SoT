# Beginner setup implementation plan

## Goal

Complete the repository-local beginner journey without adding a mutation CLI or duplicating Assistant semantics in client adapters.

```text
get repository
→ choose conversation language
→ choose local or web client
→ optional minimal personal onboarding
→ run system check when capable
→ meet Personal SoT Assistant
→ start the first useful task
```

## Boundaries

- Local agents may perform confirmed canonical writes through the existing safe-write contract.
- Web clients provide the same guided setup and preview, but do not claim local checks or writes they cannot perform.
- Conversation language is runtime state. Durable response preferences belong in a profile; durable personal facts belong in canonical context.
- Personal onboarding is optional and creates only semantically necessary modules.
- The system check reuses existing validators. No installer, mutation helper, connector, dependency, or new configuration format is added.

## Tasks

- [x] Define one client-neutral setup workflow and scenario cases.
- [ ] Add a thin setup prompt and runtime entrypoint reference.
- [ ] Add beginner installation/setup guidance with local and web capability boundaries.
- [ ] Validate prompts, Core invariants, public distribution, and the complete branch diff.
