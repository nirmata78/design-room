# Theory — the building blocks under every round

Nine short chapters covering what system-design interviews actually test. They are written for the
moment an interviewer asks *"why?"* or *"what is that?"* — **mechanisms, trade-offs and the numbers
that change decisions**, not product tours. The [reference solutions](../solutions/README.md) link
into these pages instead of re-teaching.

| # | Chapter | Read it for |
|:-:|---|---|
| 1 | [The interview method](01-interview-method.md) | the twelve stages and their clock, what each proves, the four-sentence close |
| 2 | [Estimation](02-estimation.md) | the number kit, latency orders of magnitude, numbers that kill designs |
| 3 | [Storage & partitioning](03-partitioning-and-storage.md) | picking a store from the access pattern, partition keys, hot keys, indexes |
| 4 | [Replication & consistency](04-replication-and-consistency.md) | leaders, quorums, consensus, consistency models, CAP/PACELC, clocks, conflicts |
| 5 | [Caching](05-caching.md) | cache patterns, invalidation, stampedes, hot keys, hit-ratio economics |
| 6 | [Messaging & streams](06-messaging-and-streams.md) | queues vs logs, ordering, delivery semantics, the outbox, backpressure |
| 7 | [Correctness under failure](07-correctness-under-failure.md) | the unknown outcome, idempotency keys, state machines, sagas, reconciliation |
| 8 | [Reliability & operations](08-reliability-and-operations.md) | SLIs/SLOs, overload control, blast radius, observability, cost |
| 9 | [Real-time & connections](09-real-time-and-connections.md) | WebSockets vs push, the connection tier, reconnect storms, cursor sync |

## Concept → where it is decisive

| Concept | Chapter | Decisive in |
|---|---|---|
| Fan-out on write vs read | 5, 6 | [SD-08 News feed](../solutions/SD-08-news-feed.md) |
| Store-before-deliver, cursors, sequence numbers | 6, 9 | [SD-09 Chat](../solutions/SD-09-chat-messaging.md) |
| Quorums, consensus, PACELC, conflict resolution | 4 | [SD-15 Distributed KV store](../solutions/SD-15-distributed-kv-store.md) |
| Token bucket, local vs shared state, fail-open | 8 | [SD-25 Rate limiter](../solutions/SD-25-rate-limiter.md) |
| Idempotency keys, sagas, double entry, reconciliation | 7 | [SD-44 Payments & ledger](../solutions/SD-44-payments-ledger.md) |

## How to study with it

1. **Before a first round**, read chapters 1 and 2 — the method and the numbers are worth more than
   any single technology.
2. **After a round**, the report names your weakest dimension; read the chapter that covers it, not the
   model answer to the question you just did.
3. **Before a loop**, re-read the *Traps* at the end of each chapter — they are the claims that break
   under a follow-up question.
