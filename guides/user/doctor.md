# Check Personal-SoT with Doctor

Doctor gives you a read-only health report. It checks the setup but never changes your information or configuration.

## Ask naturally

Open your private `sot` in your local AI agent and say:

```text
Run Personal-SoT Doctor and explain the result in English.
```

Or use the exact expert action:

```text
@do:doctor
```

You can use any preferred language. You do not need to know repository paths, YAML, registries, or Git.

## Understand the report

Doctor starts with a short status list:

```text
✓ Setup is ready
✓ Runtime entrypoint resolves correctly
✓ Personal workspace is valid
✓ Prompts are valid
✓ Codex configuration detected
```

Warnings describe a usable limitation:

```text
⚠ ChatGPT is preview-only
```

Errors mean an area needs attention:

```text
✗ Personal workspace has validation problems
```

Every warning or error explains:

- what is wrong;
- why it matters;
- whether it blocks safe use;
- exactly what to do next.

Technical paths and validator details stay in an optional `Advanced` section.

## Repairs are separate

Doctor does not silently repair anything. If a finding needs action, use:

```text
@do:fix
```

You can also include a problem description after a blank line.

`@do:fix` first checks whether the issue is usage confusion or a real current defect. Guidance-only problems are explained without a write. Real repairs must show the exact proposal, wait for explicit confirmation, re-check current state, apply only with real permission, and rerun the relevant validation/Doctor when possible.

By default, repair targets your private `sot`. Fixing `sot public` is a separate explicit public-development task and follows the public repository branch/review rules.

## Web clients

A web client can explain Doctor and guide a diagnosis. If it cannot run local commands, it must say that Doctor was not run there.

If it cannot write the repository, it may prepare a repair proposal but must not claim that the repair was applied or validated.

## Privacy

Doctor does not display secret values or canonical content. It does not quote `restricted` or `deny` content. Keep passwords, API tokens, private keys, recovery codes, one-time codes, and payment credentials outside Personal-SoT.
