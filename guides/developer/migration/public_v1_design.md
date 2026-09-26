# Public Personal-SoT V1 design

## Outcome

Build a public, beginner-first Personal-SoT whose normal interface is natural language while the existing canonical contracts remain authoritative underneath.

The first delivery is a safe foundation, not the full product:

```text
generic Core
→ public distribution gate
→ minimal empty Personal workspace
→ beginner navigation
```

No real Personal facts, private project state, user-specific paths, credentials, private adapters, or Personal Git history may enter the repository.

## Architecture

Keep the canonical three-root layout:

```text
workspace/  user-managed canonical content and configuration
system/     runtime contracts, validation, governance and tests
guides/     user and developer documentation
```

`readme.md` is the only root navigation file. Generic reusable material comes from `v1.2_ai_context_source_of_truth`. Personal-only material is excluded until it is independently classified, generalized, and validated.

The eventual beginner interface is the Personal SoT Assistant with six categories: Discover, Maintain, Create, Customize, Explain, and Diagnose. Material canonical writes follow:

```text
understand → resolve scope → classify → reconcile → propose → preview
→ confirm → write → validate → report
```

Read-only operations may run directly. Ambiguous truth is clarified or deferred, never guessed.

## M1 scope

M1 delivers:

- the reusable Core baseline;
- an explicit migration inventory;
- a dependency-free public-distribution validator;
- a minimal, data-free Personal workspace entrypoint;
- beginner-oriented repository navigation;
- a repeatable validation command.

M1 deliberately excludes setup automation, Assistant workflows, Project Builder, prompt building, GUI, plugins, servers, accounts, cloud services, and background self-modification.

## First vertical slice after M1

```text
beginner setup
→ meet Personal SoT Assistant
→ create one project adaptively
→ ask using that project
→ preview and confirm a current-state update
```

The guided interaction uses the selected language, shows progress, asks one useful question at a time, offers examples and a recommendation, includes an "I don't know — recommend one" path when useful, and teaches expert directives only after the beginner workflow.

## Validation

M1 is acceptable only when:

1. the generic Core validators pass;
2. the public validator rejects known Personal identifiers, private source/deployment references, user-specific home paths, and likely raw secrets;
3. the public validator accepts placeholders and the clean repository;
4. the Git diff contains no unclassified Personal source file.

