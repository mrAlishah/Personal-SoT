---
ai_access: allow
decision_status: accepted
---
# use_kafka_for_reconciliation

## decision

Use Kafka for reconciliation event transport.

## context

The subsystem requires durable ordered event processing and replay.

## consequences

Kafka becomes relevant deep evidence when the task asks why messaging is Kafka; it is not required for a simple current-stack lookup.
