# V1.1 Repository Layout Cases

## purpose

Declarative acceptance cases for the three-root ownership refactor.

### Case 1 - exactly three primary roots

Given a compliant repository, implementation content is organized under:

```text
workspace/
system/
guides/
```

Root `readme.md` may exist as navigation. Legacy top-level areas such as `context/`, `prompts/`, `routing/`, `validation/`, `tests/`, `formats/`, or `profiles/` fail structural validation.

### Case 2 - logical context identity stays stable

```text
@ctx:personal/projects/job_search
```

resolves physically below:

```text
workspace/context/personal/projects/job_search/
```

The user never writes `@ctx:workspace/context/...`.

### Case 3 - prompt identity stays stable

```text
@do:prompt:chat/recap
```

resolves:

```text
workspace/prompts/chat/recap.md
```

### Case 4 - presentation mapping

```text
@profile:tech/learn → workspace/profiles/tech/learn.md
@fmt:yaml                  → workspace/presentation/formats/yaml.md
@tone:human                → workspace/presentation/tones/human.md
@depth:short               → workspace/presentation/depth/short.md
```

### Case 5 - system content is not factual context

Files under `system/` may define contracts/behavior/routing but cannot become factual scope candidates merely because they are searchable.

### Case 6 - guides are non-runtime

`guides/user/` is operational documentation and `guides/developer/examples/` contains fake examples. Neither is registered as canonical factual context.

### Case 7 - end-user maintenance boundary

Adding/updating a conforming Personal fact, prompt, profile or concrete presentation module is a `workspace/` change and does not require editing `system/`.

### Case 8 - system change boundary

Changing prompt schema, access semantics, routing grammar, precedence, validator logic, behavior algorithms, or generic adapter semantics belongs under `system/` and follows `system/governance/branch_flow.md`.

### Case 9 - public foundation isolation

The public foundation may contain reusable prompts/profiles/presentation modules in `workspace/`, but must not contain real `workspace/context/personal/*.md` or organization facts.

### Case 10 - installed Personal workspace

After installation, a user may add real `workspace/context/personal/`, Personal-only `workspace/prompts/`, and `workspace/adapters/` without changing public system contracts.
