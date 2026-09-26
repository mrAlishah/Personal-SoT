---
ai_access: allow
decision_status: superseded
---
# use_rabbitmq_for_async_payment_work

> FICTIONAL DECISION EXAMPLE ONLY.

## decision

Use RabbitMQ for asynchronous payment work. <!-- HISTORICAL FAKE EXAMPLE -->

## context

The original system needed a simple broker for background processing before event replay and multi-consumer stream requirements became material.

## consequences

- simple queue-oriented operations;
- limited fit for later replay/stream requirements.

## supersession

Superseded by:

```text
adopt_kafka_for_payment_events.md
```

The current stack must not be inferred from this superseded artifact.
