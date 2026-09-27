# query_planning

## purpose

Compact heuristics for translating a task into likely canonical module candidates before targeted expansion.

## planning_model

```text
task_intent
→ semantic_responsibilities
→ owner_locator_candidates
→ effective_access
→ semantic_rank
→ targeted_content
→ bounded_expansion
```

Owner-locator discovery may use authorized scope structure, module paths, and filenames without loading unrelated module content. Content enters effective context only after the applicable access contract permits it.

## common_mappings

```text
who/identity/background
→ identity.md

current situation/blockers/progress
→ current_state.md

goals/desired outcomes
→ goals.md or project objectives.md

real-world limits
→ constraints.md

current technology
→ stack.md

current structure/data flow/components
→ architecture.md

organization/project vocabulary
→ terminology.md

mandatory/preferred governed rule
→ applicable policies/

why an important choice was made
→ current module + relevant decisions/

personal durable technical capability
→ workspace/context/personal/tech_profile.md

personal durable work preference
→ workspace/context/personal/working_style.md

ordinary Personal fact / clothing size / routine household detail
→ established Personal general-info catch-all when the active Personal overlay defines one

Personal health treatment / medication / specialized current health fact
→ established authorized Personal sensitive domain owner, preferring the relevant specialized owner over a general catch-all

dated Personal body/vital measurement
→ established authorized longitudinal measurement-history owner

dated Personal laboratory result
→ established authorized laboratory-history owner
```

## unified_personal_owner_discovery

When the active factual scope is `personal`, do not treat restricted/sensitive Personal owners as a late fallback behind root-level Personal files.

Build one bounded owner-locator pool from the active Personal scope containing:

```text
root Personal owners
+
established Personal general-info owners
+
established Personal specialized/restricted owners
```

This pool contains owner locators such as paths/module names, not eagerly loaded file bodies.

Use the task's semantic responsibility to rank the smallest plausible owners across that unified pool. A restricted owner may be the first semantic candidate when it is the best fit for the question.

Then:

1. validate effective access for the selected candidate before loading its factual content;
2. load only the highest-ranked relevant owner;
3. if that owner is insufficient, expand only to the next plausible owner;
4. use targeted name/text search inside the authorized Personal scope only when established owner names do not resolve the concept;
5. stop as soon as the minimum sufficient authoritative context is loaded.

Do not recursively scan `workspace/context/personal/`, `sensitive/`, `main_info/`, or `general_info/` merely because they are authorized.

`restricted_access_profile: personal_owner` makes eligible restricted Personal modules normal retrieval candidates when the current task materially requires them; it does not make all restricted content relevant or loadable by default.

Examples:

```text
"What is my trousers size?"
→ ordinary Personal fact / clothing
→ established general-info catch-all
→ validate access
→ targeted read

"What medication do I take for LDL?"
→ Personal health treatment / cardiometabolic domain
→ specialized cardiometabolic owner
→ validate access
→ targeted read

"What is my spouse's name?"
→ household/family context
→ specialized family owner when established
→ validate access
→ targeted read
```

Absence from a root-level module such as `identity.md` is not evidence that a Personal fact is absent from the SoT.

## personal_absence_guard

For a Personal factual question, do not assert that canonical information is missing merely because the first owner checked did not contain it.

Before concluding that the fact is absent:

1. confirm the Personal scope actually resolved;
2. identify the small plausible owner set across both root and eligible restricted Personal owner locators;
3. check the relevant authorized candidates using bounded targeted retrieval;
4. distinguish genuine canonical absence from access failure, repository/tool unavailability, or unresolved ownership.

Only after the plausible relevant authorized owners are exhausted may the runtime state that the fact is not present in the canonical Personal SoT.

This guard is a correctness boundary, not permission for broad scanning.

## multi_module_tasks

Some tasks legitimately require several atoms.

Examples:

```text
architecture review
→ architecture + constraints + stack + applicable policies
→ relevant decisions only if rationale materially matters

planning next project action
→ objectives + current_state + constraints + applicable policies

career planning
→ personal goals + constraints + current_state + tech_profile
→ relevant personal project atoms when a specific project is Primary

Personal medication question
→ relevant specialized health-domain owner only
→ laboratory/history owner only if the question materially requires historical evidence or current-treatment interpretation
```

## unknown_custom_module

If canonical catalog modules do not plausibly contain the needed concept:

1. inspect the selected scope's available module names if the host can do so safely;
2. perform targeted text/name search inside authorized candidate scope;
3. apply module boundary/access contracts to any match;
4. do not broaden to unrelated organizations/personal scopes without explicit scope authority.

For a Personal fact, absence from the small common-mapping list is not evidence that the fact is absent from the SoT. Use unified Personal owner discovery before concluding `not found`.

## exact_identifier_search

For stable identifiers such as:

```text
rule_id
technology_name
decision_filename
domain_term
```

exact search may be more efficient than broad semantic retrieval.

A match still does not establish current authority.

## freshness_after_reanchor

After `@do:sot`, prior conversation-local factual conclusions whose freshness is not established must not suppress current retrieval.

In particular, a pre-reanchor `not found` result is not a durable retrieval cache entry. When the user asks for that fact again, plan a targeted lookup against the current canonical source using the current scope/access state.

This freshness rule does not justify broad eager loading; invalidate stale conclusions, then retrieve only the needed current atom.

## stop_rule

Stop expanding internal retrieval when the loaded atoms are sufficient to answer accurately and materially relevant uncertainty has been resolved.

Do not retrieve additional files merely to make the context feel comprehensive.
