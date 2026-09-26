---
ai_access: allow
decision_status: accepted
---
# adopt_kafka_for_payment_events

> FICTIONAL DECISION EXAMPLE ONLY.

## decision

Use Kafka as the current messaging platform for payment-domain asynchronous events. <!-- EDIT_ME -->

## context

The payment platform needs durable ordered event streams, consumer replay, and operational visibility across payment and settlement workflows. <!-- EDIT_ME -->

## consequences

- operate Kafka as a production dependency;
- design idempotent consumers;
- define event-schema compatibility rules;
- accept higher operational complexity than a simple queue.

## alternatives

- RabbitMQ
- managed cloud queue

## current_truth

Current messaging truth remains in `../stack.md`:

```text
messaging: kafka
```

This decision explains why; it is not the sole source of current stack state.
