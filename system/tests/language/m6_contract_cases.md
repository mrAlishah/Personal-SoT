# m6_language_contract_cases

These scenarios validate V1 primary/supporting language semantics.

## case_01_single_primary

`primary_language = german` with no supporting languages.

Expected: main response is German.

## case_02_primary_with_supporting

`primary_language = german`, `supporting_languages = [english, persian]`.

Expected: German is the main response language; English/Persian appear only where the task/profile/format requests equivalents or multilingual support.

## case_03_supporting_not_full_translation

Supporting languages are configured but the task asks for a normal explanation only.

Expected: do not duplicate the full answer in every supporting language.

## case_04_supporting_order

`supporting_languages = [english, persian]`.

Expected: preserve that order where both are rendered.

## case_05_supporting_dedup

`supporting_languages = [english, english, persian]`.

Expected: `[english, persian]`.

## case_06_primary_removed_from_supporting

`primary_language = german`, supporting includes German.

Expected: remove German from supporting.

## case_07_prompt_local_override

Profile defaults to German, current prompt explicitly asks for Persian.

Expected: Persian for that prompt only; profile default remains unchanged.

## case_08_no_lang_switch

Prompt contains `@lang:german`.

Expected: uncontracted/invalid namespace in V1/M6.

## case_09_no_persistent_inference

Ordinary prompt says `answer this one in English`.

Expected: current-prompt language request; do not create persistent language state.

## case_10_language_not_teaching

German is primary.

Expected: German rendering alone does not activate teaching behavior.

## case_11_language_not_vocab

German + English + Persian are configured.

Expected: multilingual configuration alone does not force vocabulary-table output.

## case_12_vocab_with_supporting

Primary German + supporting English/Persian + `vocab` format.

Expected: German vocabulary entries may include English/Persian equivalents where the task/profile requires them.

## case_13_language_not_tone

Primary German with formal tone.

Expected: German controls language; formal controls register.

## case_14_language_not_depth

Primary Persian with short depth.

Expected: Persian controls language; short controls amount of detail.

## case_15_language_not_fact

Statement: `project language runtime is Go`.

Expected: project technical fact in context, not language presentation configuration.

## case_16_exact_identifiers

External technical identifiers appear in German/Persian output.

Expected: preserve exact identifiers where translation would reduce precision.

## case_17_no_fuzzy_language

`German`, `de`, or `de-DE` is supplied where canonical profile/language-module semantics require the exact self-addressing identity `german`.

Expected: do not silently normalize unless an adapter contract explicitly maps external locale identifiers before canonical resolution.

## case_18_profile_language_default

A profile defines primary German and English/Persian supporting languages.

Expected: profile provides language defaults without copying language module instructions.

## case_19_explicit_prompt_over_profile

Profile default is German; prompt explicitly requests English.

Expected: English wins for current prompt.

## case_20_adapter_over_profile

Adapter default language is Persian; profile default is German and no prompt language request exists.

Expected: adapter default wins according to the language lane in `system/routing/precedence.md`.

## case_21_supporting_languages_token_efficiency

Three languages are configured but only one supporting equivalent is needed.

Expected: do not render unnecessary multilingual duplication.

## case_22_language_modules_are_reusable

German module is used by different profiles/tasks.

Expected: one canonical `workspace/presentation/languages/german.md`; no duplicated German rules inside profiles.

## case_23_behavior_boundary

Instruction says `teach with mental models in German`.

Expected: teaching method from behavior + German from language; do not merge both responsibilities into one module.

## case_24_quality_over_translation_convenience

A literal translation would distort a technical term.

Expected: preserve the precise canonical/technical term rather than forcing a misleading translation.
