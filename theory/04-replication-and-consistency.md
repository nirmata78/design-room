# 4 · Replication & consistency — copies, order and what a client can see

Replication keeps copies of data on several machines for **durability, availability and read
scale**. The moment there are copies, there is a question of **which copy is right, and when** — and
every answer costs latency or availability. Being precise here is the single biggest
differentiator in storage-heavy rounds.

---

## Three replication topologies

| Topology | Writes go to | Ordering decided by | Typical | Main risk |
|---|---|---|---|---|
| **Single leader** (primary/replica) | one leader per partition | the leader | PostgreSQL, MySQL, Kafka partitions, Raft groups | failover: lost writes if async; split brain if two think they lead |
| **Multi-leader** | a leader per region/datacentre | nobody globally — conflicts must be resolved | multi-region active-active databases, offline-first apps | concurrent writes to the same key conflict |
| **Leaderless** | any N replicas, with quorums | nobody — versions + read repair | Dynamo-style stores, Cassandra | stale reads, conflict resolution |

### Synchronous vs asynchronous

- **Synchronous:** the write is acknowledged only after replicas confirm. Durable on failover, but
  latency includes the slowest required replica.
- **Asynchronous:** acknowledge after the leader commits; replicas catch up. Fast, but a leader
  failure **loses the un-replicated tail** — the "replication lag" window.
- **Semi-synchronous / quorum:** wait for *some* replicas (e.g. a majority). The usual compromise.

### Quorums

With **N** replicas, writes wait for **W** acknowledgements and reads query **R** replicas. If
**R + W > N**, every read set overlaps every write set, so a read sees at least one copy of the
latest acknowledged write (subject to concurrent writes and failures — "sloppy quorums" and hinted
handoff weaken this). Typical: N=3, W=2, R=2.

{: .why }
> **Why a majority?** Any two majorities of the same group overlap. That overlap is what lets a new
> leader be guaranteed to have seen every committed write — the core of consensus.

---

## Consensus — agreeing on an order despite failures

Consensus protocols (**Raft**, **Paxos**, Zab) let a group of nodes agree on a single ordered log of
operations as long as a **majority is alive and connected**. In Raft terms:

1. Nodes elect a **leader** for a **term**; a candidate needs votes from a majority.
2. The leader appends client commands to its log and replicates them; an entry is **committed** once
   a majority has stored it.
3. Committed entries are applied in order to a state machine (e.g. a key-value map) — **state machine
   replication**.
4. A new leader must have every committed entry (the voting rule ensures it), so commits survive
   leader failure.

**What it costs:** every write needs a round trip to a majority. Inside a region that's ~1 ms; **across
continents it's 100–250 ms**. A minority partition cannot make progress — it becomes unavailable for
writes.

{: .warn }
> **Replication is not consensus.** Async primary→replica copying moves data but does not decide
> order safely under failure. Consensus decides order. Interviewers probe this confusion directly:
> *"is your replication protocol also deciding order?"*

**Where consensus is used in practice:** metadata and coordination services (etcd, ZooKeeper,
Consul), leader election, lock services, and each partition's replica group in modern databases
(Spanner, CockroachDB, TiKV — one Raft/Paxos group per range).

### Leases and fencing

A **lease** is a time-bounded right to act (e.g. "I am leader until T"). Because clocks drift and
processes pause (GC, VM migration), an old leaseholder can wake up and act after its lease expired.
**Fencing tokens** fix this: every grant carries a monotonically increasing number and the storage
rejects writes with a lower token than it has seen.

---

## Consistency models — what a client can observe

From strongest to weakest, with what each **promises a client**:

| Model | Promise | Cost |
|---|---|---|
| **Linearizable** (strong) | every operation appears to happen at one instant between its start and end; reads see the latest write | coordination on every operation; cross-region latency |
| **Sequential** | all clients see operations in the same order, consistent with each client's own order | still needs a global order |
| **Causal** | if A could have influenced B, everyone sees A before B; concurrent ops may be seen in different orders | tracking dependencies (vector clocks, session metadata) |
| **Read-your-writes** | a client sees its own writes | session stickiness or a version token |
| **Monotonic reads** | a client never sees time go backwards | stick to one replica, or track the version |
| **Eventual** | replicas converge if writes stop | nothing on the read path — but no promise about *when* |

{: .say }
> "Most keys here only need read-your-writes — the user must see their own update. I'll offer
> linearizable reads as an option for the few operations that need them, because they cost a
> leader round trip."

**Isolation (transactions) is a different axis** from replication consistency: read committed,
snapshot isolation, serializable. Snapshot isolation still permits **write skew** (two transactions
each check an invariant on data the other changes); serializable prevents it. When an invariant
spans rows (e.g. "at most one booking per seat"), use a constraint, `SELECT … FOR UPDATE`, or
serializable isolation.

---

## CAP and PACELC — stated correctly

**CAP:** when a **network partition** separates replicas, a system must choose between
**Consistency** (refuse some operations so no client sees divergent data) and **Availability**
(accept operations on both sides and reconcile later). There is no third option during the partition.

**PACELC** adds the half that governs normal days: **if Partition, choose A or C; Else, choose
Latency or Consistency.** Even with no failure, strong consistency across distance costs round trips.

| System style | Under partition | Normal operation |
|---|---|---|
| Spanner / CockroachDB (consensus per range) | **C** — minority side unavailable | **C** — pays quorum latency |
| Dynamo / Cassandra (tunable quorums) | **A** — accept writes, reconcile | **L** — local quorums are fast, reads may be stale |
| Async primary + read replicas | C for writes (primary side) | L for replica reads (stale) |

{: .key }
> **Five regions, majority quorum:** a write must reach 3 of 5 regions — the leader's region plus the
> two nearest. With the leader in Mumbai, the nearest others are Tokyo and Ireland, each roughly
> 110–130 ms away round trip, so **every write costs ~120 ms at best**, and a client in another
> continent adds its own trip to the leader on top. Say the number, then decide.

---

## Time and ordering

- **Physical clocks drift** (milliseconds with NTP, worse during incidents). Never order writes from
  different machines by wall-clock time unless you can bound the error.
- **Lamport clocks:** a counter incremented on each event and on receive (`max(local, received)+1`).
  Gives a total order consistent with causality, but can't detect concurrency.
- **Vector clocks / version vectors:** one counter per replica; can tell "A happened before B" from
  "A and B are concurrent". Used to detect conflicts.
- **Hybrid logical clocks (HLC):** physical time plus a logical counter — close to wall time, causally
  consistent. Used by CockroachDB and others.
- **TrueTime (Spanner):** clock uncertainty bounded by GPS/atomic clocks; a commit **waits out the
  uncertainty** (a few ms) so timestamps reflect real-time order — external consistency at the price
  of commit wait.

## Resolving conflicts (when you chose A)

| Strategy | How | Danger |
|---|---|---|
| **Last-write-wins (LWW)** | highest timestamp wins | silently drops concurrent writes; clock skew picks the "wrong" winner |
| **Version vectors + siblings** | keep concurrent versions, let the app/client merge | complexity pushed to the client |
| **CRDTs** | data types whose merges are commutative, associative, idempotent (counters, sets, maps, sequences) | only for operations that can be expressed that way |
| **Application merge** | domain-specific rules (e.g. union of shopping-cart adds) | must be designed per entity |

---

## Traps

{: .warn }
> **"Reads are local and strongly consistent, writes are fast, in five regions."** Physically
> impossible — say which one you give up, and where.

{: .warn }
> **"Strong consistency" meaning "read-your-writes".** Name the model you actually provide.

{: .warn }
> **LWW "because clocks are synchronised".** They aren't, to the precision concurrent writes need.
