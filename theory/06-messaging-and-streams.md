# 6 · Messaging & streams — decoupling work in time

Asynchronous messaging lets a producer hand work to consumers **without waiting for them**. It
absorbs bursts, isolates failures and lets many systems react to one event. It also introduces the
hardest questions in distributed systems: **ordering, duplicates and loss.**

---

## Queue or log?

| | **Message queue** (SQS, RabbitMQ) | **Log / stream** (Kafka, Kinesis, Pulsar) |
|---|---|---|
| Model | messages are taken and deleted on ack | an append-only, ordered, retained sequence; consumers track offsets |
| Consumers | competing consumers share the work | each **consumer group** reads the whole log independently |
| Replay | no (once acked, gone) | yes — rewind the offset |
| Ordering | weak (FIFO variants exist, with limits) | **per partition** |
| Good for | task distribution, jobs, per-message retries | event streams many systems consume; rebuilding state; CDC |

{: .say }
> "I want several independent consumers — the inbox writer, the push notifier and search indexing —
> to read the same events at their own pace, and to replay after a bug. That's a log, partitioned by
> conversation ID so each conversation stays ordered."

## Partitions and ordering

A log is split into **partitions**; each is totally ordered and consumed by at most one consumer in
a group at a time. Ordering is guaranteed **only within a partition**, so the partition key must be
the unit you need ordered (user, account, conversation). Global order means one partition — which
means one consumer's throughput.

- **Too few partitions** caps parallelism. **Too many** costs broker memory and rebalance time.
- **Skewed keys** make one partition hot; split the key or route the outlier separately.
- **Rebalances** (consumers joining/leaving) pause consumption briefly — design consumers to tolerate it.

## Delivery semantics

| Semantics | Mechanism | Risk |
|---|---|---|
| **At-most-once** | ack/commit before processing | crash loses messages |
| **At-least-once** | process, then ack/commit | crash causes **redelivery → duplicates** |
| **"Exactly-once"** | at-least-once delivery **+ idempotent or transactional processing** | true only within a closed system (e.g. Kafka transactions read-process-write) |

{: .key }
> **Exactly-once delivery across a network to an external system does not exist.** What you can
> build is **exactly-once *effect***: at-least-once delivery plus an idempotent consumer
> ([Correctness under failure](07-correctness-under-failure.md)). Saying this precisely is a strong
> signal in any payments, messaging or billing round.

**Idempotent consumers:** record processed message IDs (or a per-key high-water mark of sequence
numbers) in the same transaction as the side effect; skip anything already seen.

## The dual-write problem and the outbox pattern

A service that writes its database **and** publishes an event has two writes that can't share a
transaction. Crash between them and the two disagree forever.

**Transactional outbox:** write the business change and an `outbox` row **in the same database
transaction**. A relay (polling the table, or reading the DB's change stream via CDC) publishes outbox
rows to the log and marks them sent. Publishing is at-least-once, so consumers must be idempotent.

```mermaid
sequenceDiagram
  participant S as Service
  participant DB as Database
  participant R as Outbox relay
  participant L as Log
  S->>DB: BEGIN; UPDATE order; INSERT outbox(event); COMMIT
  R->>DB: read unsent outbox rows (or CDC)
  R->>L: publish event (at-least-once)
  R->>DB: mark sent
```

**Change data capture (CDC):** stream the database's write-ahead log as events (Debezium-style).
Turns any database into an event source without application dual writes.

## Backpressure, retries and dead letters

- **Consumer lag** (how far behind the head a group is) is the primary health metric of a streaming
  system. Alert on lag *growth*, not just level.
- **Retries:** transient failures retry with backoff; **poison messages** (always fail) go to a
  **dead-letter queue** after N attempts so they don't block the partition — with an owner and a
  replay tool.
- **Backpressure:** when consumers can't keep up, the log absorbs it (retention is the buffer); for
  synchronous edges, shed or queue at the boundary rather than letting latency grow unbounded.
- **Priority isolation:** separate topics (or queues) per priority class, with dedicated consumers, so
  a bulk backlog never delays urgent work.

## Push vs pull delivery to consumers

- **Pull** (Kafka consumers poll): the consumer controls its pace — natural backpressure.
- **Push** (webhooks, push queues): lower latency, but the producer must handle slow or failed
  consumers with retries, backoff and circuit breakers.

---

## Traps

{: .warn }
> **"Kafka guarantees ordering."** Per partition only. Name the partition key and what is ordered.

{: .warn }
> **Write DB, then publish** with no outbox. Ask yourself: what if the process dies between the two?

{: .warn }
> **One giant topic** for all priorities — a marketing backlog then delays password resets.
