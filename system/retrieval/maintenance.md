# retrieval_maintenance

## purpose

Defines how to detect retrieval problems and decide whether the architecture needs stronger discovery mechanisms.

## evidence_first_rule

Do not add retrieval infrastructure because the repository is growing or because embeddings/vector search are available.

Add complexity only after representative tasks show a recurring measurable gap.

## failure_classes

```text
scope_resolution_failure
→ routing/registry problem

wrong_semantic_home
→ module/boundary problem

inaccessible_content
→ access/authorization problem

relevant_module_not_found
→ retrieval/discovery problem

wrong_source_wins
→ authority/precedence problem

excessive_context
→ relevance/progressive-disclosure problem

stale_canonical_fact
→ maintenance/migration problem, not retrieval ranking
```

Classify the failure before changing retrieval.

## retrieval_evaluation_set

Maintain representative scenarios rather than synthetic score targets alone.

Useful task classes:

```text
simple_current_fact
multi_module_planning
nested_project_scope
policy_sensitive_task
why_decision_question
custom_term_lookup
supplemental_gap_fill
restricted_sensitive_fact
```

For each scenario evaluate:

- correct scope resolved;
- required module found;
- inaccessible modules protected;
- authoritative source selected;
- unnecessary modules avoided;
- answer can explain provenance.

## escalation_ladder

Prefer the least complex fix that closes the measured gap:

```text
1. improve module boundary/name
2. improve registry/index
3. improve exact/path/text-search heuristic
4. add a small deterministic generated index if justified
5. only then evaluate semantic/embedding retrieval
```

Do not jump directly to a vector database.

## generated_indexes

A future generated index may be acceptable if it is disposable and derived from canonical sources.

It must never become a competing source of truth.

Conceptually:

```text
canonical_markdown
→ generated_index
→ retrieval aid only
```

If regenerated, no canonical fact should be lost.

## stale_index

A stale generated index may cause missed discovery but must not be allowed to override canonical file content or access metadata.

## acceptance

Retrieval maintenance is working when failures are diagnosed in the correct architectural layer and complexity is introduced only to solve demonstrated retrieval problems.
