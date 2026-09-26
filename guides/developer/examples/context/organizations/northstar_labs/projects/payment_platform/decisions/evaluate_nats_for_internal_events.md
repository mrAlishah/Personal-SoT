---
ai_access: allow
decision_status: proposed
---
# evaluate_nats_for_internal_events

> FICTIONAL DECISION EXAMPLE ONLY.

## decision

Evaluate NATS as a possible future internal messaging option for narrowly scoped low-latency service communication. <!-- EDIT_ME -->

## context

A future subsystem may value lower operational overhead and low-latency messaging for ephemeral internal events.

## consequences

No current production change is authorized by this proposal.

## alternatives

- continue using Kafka
- use direct gRPC calls where asynchronous messaging is unnecessary

## current_truth

This proposal does not override the accepted Kafka decision or `../stack.md` merely because it is newer.
