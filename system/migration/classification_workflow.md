# classification_workflow

## purpose

Deterministic decision path for each candidate extracted from historical material.

## classification_algorithm

```text
1. is it durable/useful enough to keep?
   no  → ignore
   yes → continue

2. is it a raw secret?
   yes → forbidden_secret → do not migrate to Git
   no  → continue

3. who owns it?
   personal / organization / project / nested project / system layer

4. what semantic kind is it?
   fact / constraint / goal / current_state / architecture / stack /
   terminology / policy / decision / behavior / presentation / profile /
   adapter_configuration

5. what is the narrowest canonical home?

6. is it current truth, historical evidence, or unknown?

7. does equivalent canonical truth already exist?
   yes → ignore or update, never duplicate

8. does it conflict with current canonical truth?
   yes and deterministic authority exists → preserve authoritative truth
   yes and unresolved → needs_confirmation

9. what access state is appropriate?
   allow / restricted / deny

10. write only the minimum authoritative representation and validate
```

## current_vs_history

Examples:

```text
"I currently use PostgreSQL"
→ current stack candidate

"We chose PostgreSQL because..."
→ possible decision rationale

"I used MySQL three years ago"
→ historical-only unless durable experience belongs in tech_profile
```

Do not confuse a historical event with current state.

## change_detection

When several historical sources discuss the same topic:

- do not preserve every version;
- identify the current effective value when evidence is sufficient;
- retain historical rationale only if independently useful;
- mark unresolved contradictions for confirmation.

## quality_gate

Before committing migrated context, verify:

```text
one_authoritative_home
correct_scope
correct_semantic_module
explicit_ai_access
no_raw_secret
no_unresolved_conflict_hidden
no_transcript_dump
no_unnecessary_metadata
```

## batching

Migrate by coherent domain batches rather than by chronological chat order.

Useful batches:

```text
personal_identity_and_state
career_and_learning
personal_projects
organization_context
project_context
policies_and_decisions
```

This reduces cross-file duplication and makes review easier.
