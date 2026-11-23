# Kafka in system design: reviewed agenda

The starting point was a 40-minute draft with three modules. This file records what was kept, what was corrected, and the agenda that was built.

## What the review changed

| Draft said | Problem | Course says |
|---|---|---|
| One topic per business event type | Kafka orders events only inside a partition, so `order-created`, `order-paid` and `order-shipped` lose their relative order. The draft's own summary table (`order-events`) contradicts this rule. | One topic per **ordering domain**, split only for retention, access, volume or reader selectivity (2.1, 2.2) |
| `v1.order-events` as a naming example | A leading version defeats prefix-based access rules and ownership | `orders.order-events.v1` (2.2) |
| Local development with ZooKeeper or KRaft | ZooKeeper was removed in Kafka 4.0 | KRaft only (3.4) |
| 3 brokers and RF 3 give high availability | Says nothing about `min.insync.replicas`, whose default is 1. Three brokers have no spare, and the count ignores load. | RF 3, minimum 2 in sync, broker count computed from disk, writes and network, plus a spare (3.2, 3.3) |
| How many brokers, but not how many partitions | Partition count is the harder decision: it caps parallelism, moves keys when raised, and can never be lowered | Its own section with a formula (3.1) |
| `null` key or round-robin | Current producers use sticky partitioning for null keys | Described as it works today (2.3) |
| Kafka as the source of truth, with CQRS | Kafka has no conditional write, so it cannot enforce an invariant | Database decides by default; three explicit options for where truth lives (5.2, 5.5) |
| Event sourcing as a Kafka pattern | No lookup by entity and no expected-version check | Limits stated, with alternatives (5.5) |
| Log compaction keeps the latest state | Compaction runs behind, the active segment is never compacted, and tombstones expire | Guarantees stated precisely (5.3) |
| Simple job queues are not for Kafka | Share groups became production ready in Kafka 4.2 | Decision table includes them (1.6, 6.2) |

## What the draft did not cover, now added

- How a write becomes durable: replication, in-sync replicas, the high watermark (1.4)
- Consumer groups, lag and rebalances (1.5)
- Delivery guarantees, the real scope of exactly once, idempotent receivers (4.1 to 4.3)
- The dual-write bug and the outbox pattern (4.4)
- Poison records, retry topics and dead-letter topics (4.5)
- Schema evolution (6.1)
- Rebuild time, consumer catch-up time and tiered storage (3.5)
- Zones and controllers (3.4)
- Where Kafka belongs in classic design rounds (6.5)
- One running example, sized end to end, ending in a finished design (1.1, 6.6)

## Length

The draft asked for 40 minutes. The finished course runs 42:44, in six modules with 33 chapters, at the pacing approved for the other courses.

## Agenda as built

| Module | Title | Sections |
|---|---|---|
| 1 | The log, and where it fits | Six questions · what Kafka is · events or calls · durable writes · consumer groups and lag · when Kafka belongs |
| 2 | Topics and keys | The rule that sounds right · split or merge, naming · what the key does · choosing the key · two quiet ways to lose order |
| 3 | Partitions and brokers | Partitions · durability · brokers · zones, controllers, local setups · recovery and catch-up |
| 4 | What can be lost or duplicated | Delivery guarantees · exactly once · idempotent receiver · dual write and outbox · poison records |
| 5 | Can Kafka be the database? | The short answer · the missing check · compaction · read models · event sourcing and where truth lives |
| 6 | Kafka in a real design | Schemas · share groups · what changed by 2026 · anti-patterns · classic rounds · finished design · drills |
