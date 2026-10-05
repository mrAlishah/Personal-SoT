# Check Personal-SoT with Doctor

Doctor answers one question:

```text
Is my Personal-SoT healthy enough to use?
```

It is **read-only**. Doctor never repairs or changes your files.

## Run Doctor

Open your private `sot` in a local authorized AI client and run:

```text
@do:doctor
```

You can also ask naturally:

```text
Run Personal-SoT Doctor and explain the result simply.
```

## Read the result

A healthy result looks like:

```text
✓ Setup is ready
✓ Runtime entrypoint resolves correctly
✓ Personal workspace is valid
✓ Prompts are valid
```

A warning means the system can still be usable but has a limitation:

```text
⚠ write capability is unavailable
```

An error means something needs attention:

```text
✗ Runtime connection is broken
```

Doctor explains:

```text
what is wrong
→ why it matters
→ whether it blocks use
→ what to do next
```

## If Doctor finds a problem

Run:

```text
@do:fix
```

`@do:fix` does not blindly edit files.

```text
usage confusion
→ explain
→ no write

real defect
→ diagnose current state
→ show repair preview
→ wait for confirmation
→ apply with real permission
→ validate
```

By default, repair targets your private `sot`.

A change to `sot public` is a separate public-development task and must be requested explicitly.

## If you only need help

Use:

```text
@do:help
```

This is useful when the system may be fine and you only need to understand how a feature works.

## Web clients

A web client can explain a Doctor result. If it cannot run local commands, it must say that Doctor was not actually run there.

If it cannot write, it may prepare a repair preview but must not claim that the repair was applied.

## Privacy

Doctor should report status and diagnostics, not dump your Personal content or secret values.

Keep credentials outside Personal-SoT.
