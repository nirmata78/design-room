# 3 · Storage & partitioning — choosing a store and splitting the data

Choose the store **from the access pattern**, then choose the key **from the partitioning you need**.
Candidates who name a database before stating how data is read and written are guessing.

---

## Start from the access pattern

Ask four questions of every entity:

1. **How is it read?** By primary key? By range (time, score)? By arbitrary filters? Joined with what?
2. **How is it written?** Insert-only (events, messages, ledger entries)? Updated in place? How often
   per key?
3. **What must be atomic?** One row? Several rows of one entity? Several entities?
4. **How big, how hot, how long?** Volume, the hottest key's rate, retention.

| Access pattern | Fits | Gives up |
|---|---|---|
| Transactions across several rows/entities, ad-hoc queries, strong integrity | **Relational** (PostgreSQL/MySQL; distributed SQL like Spanner/CockroachDB at global scale) | horizontal write scale without sharding effort (or latency, for distributed SQL) |
| Huge write volume, read by partition key + time/score range | **Wide-column / LSM** (Cassandra, ScyllaDB, Bigtable, HBase) | cross-partition transactions, secondary-index flexibility |
| Key lookups at high rate, simple values | **Key-value** (DynamoDB, Redis-as-store, RocksDB-backed services) | rich queries |
| Documents with nested fields, per-document atomicity | **Document** (MongoDB, Firestore) | cross-document invariants |
| Text relevance, faceted filters | **Search index** (Elasticsearch/OpenSearch) | being the source of truth |
| Analytics over billions of rows | **Columnar warehouse** (BigQuery, Snowflake, ClickHouse) | low-latency point updates |
| Large blobs | **Object storage** (S3, GCS) + metadata elsewhere | in-place edits, low-latency small reads |
| Ordered, replayable stream of events | **Log** (Kafka, Kinesis, Pulsar) — see [Messaging](06-messaging-and-streams.md) | random access by key |

{: .say }
> "Messages are insert-only and always read per conversation in sequence order, so I want a store
> partitioned by conversation with rows clustered by sequence number — a wide-column store fits, and
> I don't need cross-conversation transactions."

### How storage engines behave (one level down)

- **B-tree** (most relational engines): pages updated in place; fast point reads and range scans;
  random writes cost page writes plus a write-ahead log. Good when reads dominate.
- **LSM tree** (Cassandra, RocksDB, Bigtable): writes go to an in-memory table plus a log, flushed as
  immutable sorted files and merged by **compaction**. Very high write throughput; reads may consult
  several files (bloom filters help); compaction costs I/O in the background. Good when writes dominate.
- **Write-ahead log (WAL)**: every durable engine appends the change to a sequential log before
  acknowledging — this is what makes a commit survive a crash, and it is also what replication ships.

---

## Partitioning (sharding)

One machine runs out of disk, memory, write throughput or connection capacity. Partitioning splits
the data so each node owns a subset.

### Strategies

| Strategy | How | Good at | Bad at |
|---|---|---|---|
| **Hash** | `partition = hash(key) mod N` (or on a ring) | even spread, no hot ranges | range scans across keys |
| **Range** | contiguous key ranges per partition | range scans, ordered iteration | hot ranges (e.g. "now" for time keys); needs splitting |
| **Consistent hashing** | keys and nodes on a ring; a key belongs to the next node clockwise | adding/removing a node moves only ~1/N of keys | uneven load without virtual nodes |
| **Directory / lookup** | a service maps key → partition | arbitrary placement (e.g. data residency) | the directory is a dependency to scale and cache |

**Virtual nodes:** each physical node owns many small ranges on the ring, so load evens out and a
failed node's load spreads over many peers rather than one neighbour.

{: .why }
> **Why not `hash(key) mod N`?** Changing N remaps almost every key — a full reshuffle. Consistent
> hashing (or a fixed large number of logical partitions mapped to nodes) means growth moves only the
> data that has to move.

**A common production shape:** a fixed, large number of logical partitions (e.g. 4,096), each
assigned to a node by a small metadata service. Rebalancing moves whole partitions; the key→partition
function never changes.

### Choosing the partition key

The partition key should (1) spread load evenly, (2) keep data that is read together on one
partition, and (3) keep the things that must be atomic together.

| System | Partition key | Why |
|---|---|---|
| Chat messages | `conversation_id` | a conversation is read in order and sequenced by one authority |
| Timelines | `user_id` | one user's feed is read together |
| Ledger entries | `account_id` (+ time bucket for huge accounts) | balance derivation per account |
| Rate-limit counters | `(customer_id, endpoint)` | one decision reads one key |

### Hot keys and skew

Real workloads are skewed: one celebrity, one merchant, one viral post. Options, in order of
preference:

1. **Cache the hot read** (replicas of the value in many cache nodes, or client-side caching).
2. **Split the hot write**: shard the key into `key#0…key#k` sub-keys and aggregate on read
   (counters, append-only entries).
3. **Treat the outlier differently in the design** — the feed's celebrity path is this.
4. **Isolate it** onto dedicated capacity so it can't hurt its neighbours.

{: .warn }
> **Time as a leading key** (`2026-10-21T…`) sends every current write to one range partition — the
> classic hot-range bug. Prefix with something high-cardinality, or hash.

### Secondary indexes on partitioned data

- **Local index** (per partition): cheap writes; a query by the indexed field must ask *every*
  partition (scatter-gather), and tail latency grows with partition count.
- **Global index** (partitioned by the indexed field): one-partition reads; every write may update
  another partition, usually asynchronously, so the index is **eventually consistent**.

### Rebalancing and resharding

Move data while serving traffic: copy the partition (snapshot + change stream), let the copy catch
up, briefly fence writes, flip ownership in the metadata, release. **Rebalancing is a common cause of
outages** — throttle it and never rebalance automatically in response to a transient failure.

---

## Traps

{: .warn }
> **"NoSQL because it scales."** Relational databases shard too; the real question is which
> guarantees and query shapes you need. Many systems are best served by a relational database
> partitioned by tenant or user.

{: .warn }
> **Choosing the key last.** The key decides partitioning, ordering, atomicity and which queries are
> cheap. It is the first decision, not the last.
