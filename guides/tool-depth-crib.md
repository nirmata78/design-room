# Tool-depth crib

*What "in depth" means for the four tools a design round reaches for by default. Some loops — the
hour-long requirement-drip rounds especially (`CLAUDE.md` §7.5) — promise it outright: **"if you're
going to use a specific tool, be prepared to talk in depth about that tool, how it works, and why it's
best for this scenario."** If you can't say most of a section, don't name the tool; describe the
mechanism instead ("a replicated, partitioned log").*

*Interviewer: this is your reference for `data-co` probing. Never quote it during a round. Coach (practice):
point the candidate here after the round, not during it.*

## PostgreSQL: the system of record

- **MVCC**: readers don't block writers. Updates create new row versions, and **VACUUM** reclaims dead
  ones (bloat is the operational cost).
- **WAL** for durability, which also drives **streaming replication**. Async replicas can lag and can
  lose the last commits on failover; synchronous replication trades latency for zero loss.
- **Isolation**: default *Read Committed*; *Repeatable Read* (snapshot); *Serializable* via SSI, which
  aborts transactions and requires retries.
- **Contention tools**: conditional `UPDATE … WHERE state='available'` (atomic claim), `SELECT … FOR
  UPDATE`, **`FOR UPDATE SKIP LOCKED`** for work queues, advisory locks.
- **Scaling**: read replicas → declarative partitioning → sharding by tenant/user (Citus or done in the
  application). Connections are expensive, so put **PgBouncer** in front.
- **Why here**: transactions, constraints and joins on the core entities. A single primary goes a long
  way before sharding.

## Kafka: the durable event log between the seams

- **Topic → partitions**. A partition is the unit of **ordering** and **parallelism**. Order holds only
  within a partition, so **the key choice is the design** (and hot keys become hot partitions).
- **Consumer groups**: one consumer per partition per group. Offsets are committed per group. Adding
  consumers past the partition count does nothing. Rebalances pause consumption.
- **Durability**: replication factor 3, `acks=all`, `min.insync.replicas=2`. The ISR set decides which
  replicas can be elected leader.
- **Delivery**: at-least-once by default, so **consumers must be idempotent**. The idempotent producer
  removes duplicates from producer retries. **Transactions/EOS cover Kafka→Kafka only**, not your
  database side effects.
- **Retention** (time/size) vs **log compaction** (keep the latest per key), which makes replay and
  rebuilding read models possible.
- **Why here**: decoupling, replay and adding new consumers without touching the producer. That is the
  "flexible to new requirements" argument in one component.

## Redis: cache, counters and fast structures, not the source of truth

- **Single-threaded command execution**, so each command is atomic. Use **Lua** or `MULTI` for
  multi-step atomicity.
- **Structures worth naming**: sorted sets (leaderboards, alert thresholds, time-ordered queues),
  hashes, streams, HyperLogLog, geo (`GEOSEARCH`).
- **TTL** for holds and sessions, with eviction policies (`allkeys-lru` etc.).
- **Persistence**: RDB snapshots and/or AOF. Replication is **async**, so a failover can lose
  acknowledged writes.
- **Redis Cluster**: 16,384 hash slots. Multi-key operations need hash tags.
- **Distributed locks**: know the Redlock critique. Correctness needs **fencing tokens** (`theory/07-correctness-under-failure.md`).
- **Why here**: read amplification and sub-millisecond reads on hot data, with a stated plan for when
  it is cold or lost.

## Object store + CDN: bytes

- Blobs (files, images, video segments) go to the object store; **metadata goes to the database**.
- **Pre-signed URLs** let clients upload and download directly. Multipart upload for large files.
- Content-addressed chunks (a hash as the key) give **dedup** for free (SD-18).
- A CDN in front for reads. **Egress usually dominates the bill**, so say so in the cost section.

## The four-sentence summary to end every design round

1. What I built: the core path, in one sentence.
2. The key trade-off I made, and what I gave up.
3. The biggest risk and how I'd watch it (the SLO and the alert).
4. What I'd do next with more time or a second team.
