# Check Personal-SoT with Doctor

Doctor gives you a read-only health report. It checks the setup but never changes your information or configuration.

## Ask naturally

Open the repository in your local AI agent and say:

```text
Run Personal-SoT Doctor and explain the result in English.
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

Doctor does not silently repair anything. If a fix requires a canonical change, ask:

```text
Show me a repair proposal for this Doctor finding. Do not change anything yet.
```

The Assistant must show the exact proposal and wait for confirmation. An authorized local agent may then apply the confirmed repair and rerun validation.

## Web clients

A web client can explain Doctor and guide a diagnosis. If it cannot run local commands, it must say that Doctor was not run there.

If it cannot write the repository, it may prepare a repair proposal but must not claim that the repair was applied or validated.

## Privacy

Doctor does not display secret values or canonical content. It does not quote `restricted` or `deny` content. Keep passwords, API tokens, private keys, recovery codes, one-time codes, and payment credentials outside Personal-SoT.
