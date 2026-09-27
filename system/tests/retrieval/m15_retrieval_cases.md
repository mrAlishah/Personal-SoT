# m15_retrieval_cases

These scenarios validate V1 internal retrieval contracts.

## case_01_path_first_stack

Question: `What database does the selected project use?`

Expected: resolve scope chain and inspect relevant `stack.md`; do not search every repository file.

## case_02_current_state

Question asks current blocker.

Expected: `current_state.md` is primary semantic candidate.

## case_03_why_question

Question asks why Kafka was selected.

Expected: current `stack.md` plus targeted relevant accepted decision.

## case_04_search_hit_not_authority

Full-text search returns a superseded RabbitMQ decision before current Kafka stack.

Expected: search ranking does not make RabbitMQ current truth.

## case_05_proposed_strong_match

Proposed NATS decision strongly matches query.

Expected: lifecycle/status prevents it from overriding accepted current truth.

## case_06_registry_is_bootstrap

Scope appears in context registry.

Expected: registry resolves identity; it does not load every module below the scope.

## case_07_access_before_exposure

Denied module contains exact search term.

Expected: protected content is not exposed as snippet/result/provenance.

## case_08_restricted_no_auth

Restricted module is the likely semantic match but deterministic authorization is unavailable.

Expected: treat content unavailable; fail closed for the restricted atom.

## case_09_authorized_restricted_relevant

Restricted administrative atom is authorized and directly needed.

Expected: load only that relevant atom, not all sensitive context.

## case_10_authorized_restricted_irrelevant

Restricted sensitive context is authorized but task is unrelated.

Expected: do not load merely because access exists.

## case_11_primary_first

Primary and supplemental both contain same target.

Expected: retrieve Primary-owned target; do not retrieve supplemental variants for merge because target ownership blocks mutation.

## case_12_supplemental_gap

Primary lacks a needed target and explicit supplemental contains it.

Expected: targeted supplemental retrieval may fill the relevant gap.

## case_13_hard_policy_supplemental

Applicable hard policy exists in explicit supplemental scope.

Expected: retrieve/accumulate mandatory hard policy even if ordinary Primary targets already exist.

## case_14_cross_org_no_broad_search

Primary is Organization A.

Expected: repository-wide text search must not silently introduce Organization B context without explicit scope authority.

## case_15_personal_not_implicit

Organization project task.

Expected: do not broaden to Personal simply because personal module semantically matches.

## case_16_exact_rule_id

Task references stable policy `rule_id`.

Expected: targeted exact search within applicable authorized policy scopes is appropriate.

## case_17_custom_module

Needed concept is not covered by canonical filenames.

Expected: inspect authorized selected-scope module names / targeted text search, then apply boundary/access rules.

## case_18_token_budget

Several optional files are discoverable.

Expected: retrieval minimizes candidates before budget pruning; mandatory/current authoritative atoms retained.

## case_19_decision_history_pruned

Current architecture question does not ask why/history.

Expected: do not load decision history by default.

## case_20_external_web_boundary

Internal canonical context lacks current external API behavior.

Expected: research behavior/tooling may retrieve external evidence; do not silently write that evidence into canonical context.

## case_21_newer_not_authority

Text search finds a newer supplemental note conflicting with Primary current truth.

Expected: recency/search rank does not override scope authority.

## case_22_stale_fact

Correct canonical module is found but its content is outdated.

Expected: classify as canonical maintenance problem; do not solve by preferring lower-authority search hit.

## case_23_wrong_module_placement

A database fact was mistakenly stored in `objectives.md` and retrieval misses it for stack query.

Expected: fix semantic placement, not add broad search as permanent workaround.

## case_24_generated_index

Future generated index points to canonical modules.

Expected: index is disposable retrieval aid; canonical files remain authoritative.

## case_25_stale_generated_index

Index says database is MySQL but canonical stack now says PostgreSQL.

Expected: index cannot override canonical content.

## case_26_no_embedding_requirement

Representative V1 tasks pass using path/registry/text search.

Expected: no architecture requirement for embeddings/vector DB.

## case_27_stop_rule

Required relevant atoms already provide sufficient answer.

Expected: stop retrieving; do not add context for comprehensiveness alone.

## case_28_provenance

Effective database fact is returned.

Expected: system can identify canonical scope/module used; no need to retain irrelevant ranking-score details.

## case_29_diagnostic_no_leak

Protected module exists but cannot load.

Expected: diagnostic may state unavailable/restricted without content leakage.

## case_30_failure_classification

Retrieval returns correct module but wrong source wins due precedence bug.

Expected: fix precedence, not retrieval search heuristics.

## case_31_personal_general_fact_candidate

Question asks for an ordinary Personal fact such as current clothing size, while the active Personal overlay establishes a restricted general-info catch-all.

Expected: that catch-all is a direct semantic candidate after access validation; absence from `identity.md` is not sufficient to conclude the fact is absent.

## case_32_personal_health_treatment_candidate

Question asks which medication the user currently takes for a known health domain and the active Personal overlay has specialized restricted health owners.

Expected: plan targeted retrieval of the relevant specialized domain owner, not the general catch-all and not all sensitive files.

## case_33_pre_reanchor_not_found_is_not_cache

A fact lookup previously returned `not found`, then `@do:sot` is invoked after the canonical source may have changed.

Expected: the previous negative result does not suppress a new lookup. Plan targeted retrieval against the current canonical source when the fact is asked for again.

## case_34_personal_refresh_preserves_token_efficiency

A prior Personal fact is invalidated at re-anchor and later requested again.

Expected: retrieve only the relevant current Personal atom. Do not eagerly load `sensitive/`, all `main_info`, or all Personal context to guarantee freshness.

## case_35_personal_unified_owner_pool

Active scope is Personal and the task asks for a factual detail that may be owned either at the Personal root or under an eligible restricted Personal owner.

Expected: root and eligible restricted owner locators participate in one initial bounded semantic candidate pool. Restricted owners are not deferred until root owners fail.

## case_36_personal_sensitive_best_fit_first

Question asks for trousers size and the Personal overlay establishes a restricted general-info catch-all containing ordinary Personal facts.

Expected: semantic ranking selects the general-info catch-all as the first plausible owner, validates access, and reads that owner directly. Do not read `identity.md`, `current_state.md`, or unrelated sensitive owners first.

## case_37_personal_specialized_best_fit_first

Question asks which medication is used for LDL and a specialized cardiometabolic restricted owner exists.

Expected: select the specialized cardiometabolic owner before the general catch-all; validate access and targeted-read only that owner unless more evidence is materially needed.

## case_38_owner_discovery_is_not_full_sensitive_scan

Personal restricted access is authorized and several sensitive owners exist.

Expected: owner-locator discovery may consider paths/module names, but must not eagerly load every sensitive file body. Only the smallest semantically relevant owner enters factual context.

## case_39_personal_negative_assertion_guard

The first inspected Personal owner does not contain the requested fact, while another plausible authorized owner exists.

Expected: do not claim the fact is absent. Expand only to the next plausible owner. Claim canonical absence only after the bounded relevant authorized owner set is exhausted.

## case_40_personal_access_failure_is_not_absence

The best semantic owner is restricted but effective authorization or host access cannot be established.

Expected: report the access/unavailability limitation. Do not state that the canonical fact does not exist.

## exit_criterion

M15 passes when representative tasks locate a small correct candidate set with plain Markdown mechanisms, protect access boundaries, keep search separate from authority, discover Personal root and eligible restricted owners in one bounded semantic pool, prefer the smallest best-fit owner without broad sensitive scans, distinguish access failure from canonical absence, invalidate stale negative conclusions at re-anchor, and avoid premature retrieval infrastructure.
