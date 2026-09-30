# Runtime naming normalization

## status

Historical design record. Superseded as current command-grammar authority
by the runtime command-grammar refactor (`@run`/`@edit`/`@delete`, plus
`@do:help`/`@do:assist`). This document describes only the earlier Runtime
Naming Normalization milestone (bootstrap-literal and profile-identity
normalization) and must not be read as the current runtime authority. For
current grammar and its executable ownership, see
`system/routing/switch_syntax.md` and `system/routing/runtime_naming.py`.

## purpose

Normalize the public bootstrap action and shipped profile identities before
connector-backed source access expands the number of runtime surfaces.

Natural language remains the beginner interface. The directives in this
document are the optional exact expert interface.

## command grammar

```text
actions        @do:<action>
selectors      @ctx:<identity>
               @profile:<identity>
               @fmt:<identity>
               @tone:<identity>
               @depth:<identity>
controls       @control:<identity>=<value>
prompt actions @do:prompt:<identity>
               @edit:prompt:<identity>
parameters     @param:<identity>=[value]
```

Command keywords are lowercase. Identities are exact and case-sensitive.
No fuzzy matching or general alias mechanism participates in resolution.
Slash remains the separator for already-contracted hierarchical resource
identities.

## bootstrap action

The canonical parameterless bootstrap action is:

```text
@do:sot
```

Every valid invocation performs the existing operation:

```text
resolve -> reload -> re-anchor current chat
```

It is exclusive: it cannot be combined with another action, selector,
presentation directive, control, parameter, recap, or ordinary body.

`@do:initialSoT` is the only temporary legacy literal. It performs the same
operation and returns a deprecation diagnostic recommending `@do:sot`.
Canonical documentation, examples, and Assistant guidance display only
`@do:sot`. The spellings `@sot`, `@init`, `@load`, and `@bootstrap` are not
recognized aliases.

The legacy literal may be removed only after the private v1.2 deployment and
all maintained canonical references have migrated.

## profile identities

Custom profile identities retain the existing form:

```text
<lowercase_snake_case>
```

Product-owned shipped profiles use a hierarchical namespace:

```text
g.<segment>[.<segment>...]
```

Each built-in segment is non-empty and contains lowercase ASCII letters or
digits. Underscores do not cross a built-in semantic boundary.

Examples:

```text
g.architecture.review  valid
g.problem.solving      valid
g.technical.learning   valid
g.architecture_review  invalid built-in identity
g.problem_solving      invalid built-in identity
G.Architecture.Review  invalid
g..review              invalid
```

Resolution remains exact and path-derived:

```text
@profile:g.architecture.review
-> workspace/profiles/g.architecture.review.md
```

There is no profile alias registry. Old shipped files are renamed, not copied,
and old identities cease to be canonical.

## shipped migration

```text
coding              -> g.coding
research            -> g.research
technical_learning  -> g.technical.learning
german_learning     -> g.german.learning
obsidian_note       -> g.obsidian.note
architecture_review -> g.architecture.review
```

The `g.*` namespace is reserved for product-owned profiles. Personalization
may discover, select, and compose them, but user-facing Profile Builder flows
must not create or edit them. Customization produces a separate custom profile.

Private v1.2 `gn_*` profiles are evidence only and are not copied or
reclassified by this change.

## ownership

`system/routing/runtime_naming.py` is the small executable owner of bootstrap
literal classification and profile identity grammar. Runtime orchestration
remains owned by `system/adapters/runtime_bootstrap.md`; profile composition
remains owned by `system/profiles/profile_contract.md`.

The repository-wide lowercase-snake-case rule remains unchanged. Only profile
filenames validated through the profile-specific grammar may contain dots.

## acceptance

- `@do:sot` is accepted only as an exclusive parameterless invocation.
- the legacy literal is accepted with a deprecation signal;
- case variants, parameters, companion directives, bodies, and unknown aliases
  are rejected or remain unresolved as appropriate;
- custom and built-in profile identities are deterministically distinguished;
- built-in profile resolution is exact and path-derived;
- no alias registry, duplicate shipped profile, or private `gn_*` profile is
  introduced.
