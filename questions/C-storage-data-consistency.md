# Archetype C · Storage, data & consistency

**SD-15 – SD-23.** Slice with `grep -n '^### SD-15' questions/C-storage-data-consistency.md`, then
Read with `offset`. Do not read this file whole.

**What this archetype tests as a family:** whether they are **honest about consistency**. Every question
here has a point where the candidate must say out loud what happens under a partition, or what a
client can observe, and hand-waving is very visible. This is Google's favourite territory
(`CLAUDE.md` §7.3): ask *why* until you hit bedrock, and reward mechanisms over brand names —
*"a consensus-backed strongly-consistent store"* scores; *"I'd use Spanner"* alone does not.

---

### SD-15 · Globally distributed KV store / multi-region consistency   [T1 · G★ A MS]

**Read aloud:** *"Design a key-value store that serves reads and writes from five regions on three
continents."*

**Crux.** **You cannot have strongly consistent, low-latency writes in five regions.** The entire
round is whether they state that trade-off explicitly, picks a position on it deliberately, and can
describe the mechanism that implements their choice. A candidate who says "I'd use quorum replication
for strong consistency" and cannot say what the write latency becomes has not answered the question.

**If they ask:**

| Question | Answer |
|---|---|
| Regions? | 5: us-east, us-west, eu-west, ap-south, ap-northeast |
| Value size / volume? | 1 KB average, 100 TB total, 10B keys |
| Traffic? | 1M reads/sec, 100k writes/sec, globally distributed |
| Latency? | Reads p99 under 10 ms **locally**. Ask them what write latency they think they can promise — don't give them one |
| Consistency? | **"You tell me what you can offer and what it costs."** This is the question |
| Access pattern? | Mostly single-key get/put. Ask whether they want transactions before offering them |
| Durability? | Must survive the loss of an entire region |
| Data residency? | EU data must not leave the EU — raise this only if they ask, or as the curveball |

**Listen for:**
- **CAP stated correctly and specifically**: under partition, either refuse writes or accept
  divergence; there is no third option. Bonus for **PACELC** — the else-latency half is the one that
  actually governs day-to-day behaviour, and most candidates never mention it.
- **Partitioning**: consistent hashing or range partitioning, virtual nodes, and what happens to
  rebalancing when a region is added.
- **Replication mechanism**, named at the level of mechanism: leader-per-partition with a quorum
  (majority intersects, so committed data survives elections), versus leaderless with read/write
  quorums (R + W > N), versus async primary-secondary. They should be able to say which they chose *and*
  what a client can observe under each.
- Concrete write-latency arithmetic: a majority quorum across three continents means **a
  cross-continent round trip on the critical path — 150+ ms**, and they should say that number and then
  decide whether it's acceptable.
- **Local-read strategies** and their honesty: follower reads (stale — by how much?), leases, or
  read-your-writes via a session token/timestamp. "Reads are local and consistent" is a claim to
  challenge hard.
- **Conflict resolution** if they go AP: last-write-wins and its data loss, version vectors, or CRDTs
  — with the trade-off stated, not just named.
- **Failure handling**: region loss, region rejoin and re-replication, and the split-brain question.
- **← The senior insight:** offer **more than one consistency level as a product decision** and let
  the caller choose per operation — most keys do not need what the most important key needs. A
  candidate who arrives at tiered guarantees rather than one global answer is at 4.

**Probe ladder:**
- *Requirements:* "Which do you sacrifice under partition, and who is affected?" · "Does every key
  need the same guarantee?"
- *Estimation:* "What's the write latency of your scheme, concretely, for a client in Singapore?" ·
  "100 TB at replication factor N — what's the storage bill?"
- *Design:* the walk of one write, naming every network hop and which are on the critical path ·
  "Where does the ordering of two concurrent writes to one key get decided?"
- *Deep dives:* **"The link between Europe and the US drops for 30 seconds. Take me through reads and
  writes in both places, second by second."** (the crux probe — ask it every time) · "A client writes
  then immediately reads from a different region. What does it see?" · "How does a rejoining region
  catch up, and can it serve reads while catching up?" · "One key gets 100k writes/sec. What
  happens?" · "How do you add a sixth region without downtime?"
- *EM bar:* "What's the SLO you'd publish, and what's the SLI?" · "What would you buy instead of
  building, and what would make you build anyway?" · "What's the one-way-door decision here?"
  (the partitioning scheme and the consistency contract — both are near-impossible to change later)

**Curveball:** *"GDPR: EU user data must be stored only in the EU, but the same key space must remain
globally addressable."* Tests whether the partitioning scheme can accommodate a per-key placement
policy, and whether they see that this breaks a naive consistent-hash ring.

**Weak / Strong / Exceptional.** *Weak* — "replicate to all regions, reads are local, writes are
strongly consistent" with no acknowledgement of the contradiction. *Strong* — explicit CAP position,
quorum mechanism described correctly, write latency quantified, staleness bounded and stated,
region-failure path designed. *Exceptional* — offers tiered consistency per operation, uses PACELC to
frame the normal-operation trade-off, prices replication, names the one-way doors, and is clear about
what they would buy.

**Traps.** Conflating replication with consensus (they are different things and the confusion is
extremely common — probe it: *"is your replication protocol also deciding order?"*). Claiming
last-write-wins is safe because clocks are synchronised. Saying "strong consistency" and meaning
"read-your-writes".


---

### SD-16 · Object store data plane (S3-like)   [T2 · A★ G]

**Read aloud:** *"Design the data plane of an object store — the part that actually stores and returns
the bytes, with eleven nines of durability."*

**Crux.** **Durability is an arithmetic claim, not an adjective.** They must connect a redundancy scheme
to a failure model and produce a number — and choose between replication and erasure coding on the
basis of cost.

**Numbers if asked:** objects from 1 KB to 5 TB, 100 PB stored, 50k PUTs/sec and 500k GETs/sec,
durability 99.999999999%, availability 99.99%, single-AZ loss must be survivable, cost is a
first-class requirement.

**Listen for:** objects split into **fixed-size chunks/blocks** with a manifest, so large objects are
parallel and resumable · **multipart upload** for the 5 TB case, and the incomplete-upload garbage
problem · **erasure coding** (e.g. 6+3) versus 3× replication, with the storage-overhead arithmetic
(1.5× vs 3×) and the trade-off that erasure coding costs CPU and makes small objects inefficient —
**so small objects get replicated and large ones coded**, which is the insight to fish for · placement
across failure domains (disk → host → rack → AZ) · **background scrubbing** and repair, with
checksums stored separately from the data and repair rate as a monitored quantity · durability
computed from AFR and repair time rather than asserted · immutability of chunks, so overwrite is a new
version plus GC.

**Probes:** *"Eleven nines — show me the calculation."* · *"3× replication or erasure coding? Which,
and what does it cost per PB?"* · *"A disk silently corrupts a block. How and when do you find out?"*
· *"A 5 TB upload fails at 4.5 TB. What happens?"* · *(EM bar)* *"What's the cost per TB-month of your
design, and what's the biggest component of it?"*

**Weak / Strong / Exceptional.** *Weak* — "store 3 copies", no chunking, no scrubbing, durability
asserted. *Strong* — chunking with manifests, multipart upload, erasure coding with the overhead
arithmetic, failure-domain placement, scrub-and-repair. *Exceptional* — differentiates the scheme by
object size, derives the durability figure from AFR and repair time, and treats cost per TB as the
governing design constraint.

---

### SD-17 · Object storage control plane   [T2 · A G]

**Read aloud:** *"Design the control plane for an object store — buckets, permissions, quotas,
lifecycle policies, and the metadata index over trillions of objects."*

**Crux.** **Listing.** A flat key space with `prefix/` semantics and trillions of objects makes
`LIST` the hardest operation in the system, and it is where naive designs collapse.

**Numbers if asked:** 10M buckets, 1 trillion objects, metadata ~1 KB per object, 500k metadata
reads/sec, 50k writes/sec, list operations must paginate consistently, lifecycle rules evaluated
daily across the whole key space, strong consistency for read-after-write on a single key.

**Listen for:** metadata store sharded **by bucket, then by key range** — and the immediate
consequence that a hot bucket is a hot shard · **ordered key ranges** so prefix listing is a range
scan rather than a filter, which is the whole reason not to hash the key · pagination by continuation
token with a stated consistency guarantee (what a client sees if objects are added mid-listing) ·
read-after-write consistency for a single key versus eventual consistency for listing, stated
explicitly · **lifecycle evaluation as a scheduled scan over trillions of keys** — the cost of that
scan is the surprise, and the good answer avoids a full scan by indexing on expiry ·
**authorization evaluated per request** with policies cached, and the invalidation problem when a
policy is revoked · quotas and usage accounting that is approximate in real time and exact in billing
· control-plane/data-plane isolation, so a control-plane outage does not stop GETs.

**Probes:** *"`LIST` on a bucket with 10 billion objects under one prefix. What happens?"* · *"Why not
hash the object key for even distribution?"* (the answer is that it destroys prefix listing — a good
test of whether they understand the trade they'd be making) · *"A permission is revoked. How long until
it's enforced everywhere, and is that acceptable?"* · *"Lifecycle: delete everything older than 30
days, across a trillion objects. What does that job look like?"* · *(EM bar)* *"Control plane is down.
What still works, and is that the right blast radius?"*

**Weak / Strong / Exceptional.** *Weak* — metadata in one relational database, LIST as a `LIKE`
query, lifecycle as a full scan. *Strong* — range-sharded ordered metadata, continuation tokens with
a stated guarantee, per-request authz with caching, control/data-plane isolation. *Exceptional* —
treats listing as the defining constraint, avoids the full scan with an expiry index, is precise about
which operations are strongly consistent and which aren't, and designs the hot-bucket mitigation.


---

### SD-18 · File sync (Drive / Dropbox)   [T1 · G★ MS]

**Read aloud:** *"Design a file-sync service — a folder on my laptop stays in sync with the cloud and
with my other devices, and with people I share it with."*

**Crux.** **Sync is a distributed-state-convergence problem disguised as a storage problem.** Two
devices edit the same file offline; the design must have an answer that is not "last write wins" — or
must justify last-write-wins explicitly as a product decision, which is legitimate but must be said
out loud.

**If they ask:**

| Question | Answer |
|---|---|
| Users / files? | 500M users, average 50 GB and 100k files each |
| File sizes? | Mostly under 1 MB, occasionally multi-GB |
| Devices per user? | Up to 10, frequently offline |
| Conflicts? | **Common — this is the interesting part.** Real-world answer: keep both versions. Let them get there |
| Sync latency? | Seconds when online |
| Bandwidth? | Users complain about it; minimising transfer matters |
| Versioning? | 30 days of history |
| Sharing? | Yes, folder-level, with multiple editors |

**Listen for:**
- **Content-defined chunking** and per-chunk hashing → transfer only changed chunks, and
  **deduplication** across users of identical chunks (the bandwidth and storage win, and the privacy
  caveat if they mention cross-user dedup, which is a strong detail).
- **Metadata vs block storage split**: a file is a manifest of chunk hashes; the manifest is small and
  the sync protocol operates on manifests.
- **A per-user monotonic version/journal** so a device can say "I'm at revision N, what changed?" —
  this is the sync protocol's core and the alternative to expensive full-tree diffs.
- **Notification channel** (long poll or push) to tell devices to sync, with polling as the fallback
  and the thundering-herd risk on reconnect.
- **Conflict detection via version vectors or parent-revision tracking**, and a resolution policy:
  keep both as `file (device's conflicted copy)`. **← The senior insight: the correct answer to
  conflicting file edits is usually "don't merge, don't lose — surface both", because automatic
  merging of arbitrary binary content is impossible.**
- Delete/rename handled correctly (a rename must not be a delete-plus-upload; a delete must be
  tombstoned so it propagates).
- Sharing changing the model: the shared folder needs its own journal, and permission changes must
  propagate to already-synced devices.
- Large-file and low-bandwidth handling: resumable transfer, chunk-level retry.

**Probe ladder:**
- *Requirements:* "What's out of scope?" · "What's the correct behaviour when two people edit
  simultaneously? Don't tell me what's easy — tell me what's right."
- *Estimation:* "500M users × 50 GB — what's the raw storage, and what does dedup plausibly save
  you?" · "A user edits one byte in a 1 GB file. How many bytes cross the network in your design?"
  (the question that justifies chunking)
- *Design:* the walk of one file edit from laptop A to laptop B, both online · "What exactly does the
  client send to ask 'what's changed?'"
- *Deep dives:* **"Both devices are offline, both edit the same file, both come back. Walk me
  through it."** (the crux) · "The user renames a folder with 50,000 files in it. What does your
  client send?" (a classic naive-design killer) · "A device has been off for six months. Sync it." ·
  "How do you know the client's local state isn't corrupt?" · "Shared folder, someone's access is
  revoked while they're offline with local copies. What can you actually do?"
- *EM bar:* "What's the bandwidth cost of the naive design vs yours, per user per month?" · "How
  would you detect that a subset of clients had silently stopped syncing?" · "Which part would you
  ship first, and what would you deliberately not support in v1?"

**Curveband:** *"The client must now work with a folder larger than the local disk — selective
sync."* Tests whether metadata and content were properly separated, and whether they handle a
placeholder file being opened.

**Weak / Strong / Exceptional.** *Weak* — upload the whole file on any change, server timestamp wins,
no offline story, rename is delete+create. *Strong* — chunked transfer with hashing, manifest-based
files, a per-user change journal, push notification, conflict detection with both-copies resolution.
*Exceptional* — quantifies the bandwidth saving to justify chunking, handles rename and delete
correctly, has a client-corruption recovery path, treats sharing as a distinct journal, and sequences
an MVP.

**Traps.** Trusting client clocks to order edits. Treating the client as reliable (it crashes
mid-write, its disk lies, its clock is wrong, and the user edits files while it's not running).
Designing only the happy online path and being surprised by the offline question — offline *is* the
question.

---

### SD-19 · Collaborative document editing   [T1 · G★ MS★]

**Read aloud:** *"Design real-time collaborative document editing — several people typing in the same
document at the same time, seeing each other's cursors."*

**Crux.** **Concurrent edits to a shared ordered sequence must converge to the same result on every
client, and the two mechanisms for that — OT and CRDT — have genuinely different trade-offs.** This
question has a real technical floor: a candidate who cannot say *how* convergence is achieved cannot
score above 2 on depth, no matter how good the rest of the architecture is.

**If they ask:**

| Question | Answer |
|---|---|
| Concurrent editors per doc? | Typically 2–10, occasionally 100+ |
| Total scale? | 100M documents, 1M concurrently open |
| Latency? | Local edits must appear instantly; remote edits within ~100 ms |
| Offline editing? | Yes, must work and merge on reconnect |
| Document size? | Up to a few MB of text |
| Rich text? | Yes — formatting, not just plain characters |
| History? | Full revision history, with named versions and undo |
| Cursors/presence? | Yes, show collaborators' cursors |

**Listen for:**
- **Local-first application of edits** (optimistic), then reconciliation — never a server round trip
  before the character appears. This is a hard requirement and they should recognise it as one.
- **The convergence mechanism, named and explained**:
  - **OT (operational transformation)** — operations are transformed against concurrent ones;
    requires a **central server to establish a total order**; conceptually simpler state, notoriously
    hard to get right, especially with rich text.
  - **CRDT** — operations commute by construction using unique, immutable position identifiers;
    works peer-to-peer and offline naturally; costs **metadata that grows with edit history**
    (tombstones), needing GC.
  - **← The senior insight:** with a central server available and offline support required, either
    works; the choice is between *server complexity* (OT) and *client memory and metadata growth*
    (CRDT). Naming that axis is the 4.
- **A per-document authority/session server** holding the current state, with documents sharded across
  a fleet and a routing layer — plus what happens when that node dies mid-session.
- **Persistence as an operation log plus periodic snapshots**, which gives revision history and undo
  for free. Storing only the current document text is the weak answer.
- **Cursors and presence as ephemeral, separately-transported data** — never in the durable op log.
- Undo being **per-user and non-trivial** under concurrency (undoing your own edit when others have
  edited on top of it) — a genuinely hard corner worth probing.
- Access control checked at the session level, and revocation mid-session.

**Probe ladder:**
- *Requirements:* "Does the character have to appear before the server confirms? What does that force?"
  · "What's out of scope?"
- *Estimation:* "1M concurrent documents — how many session servers, and what's the memory per open
  document?" · "What's your ops-per-second per document, and does the op log's growth matter?"
- *Design:* the walk of one keystroke, from keypress to appearing on a collaborator's screen · "Where
  is the authoritative document state at this instant?"
- *Deep dives:* **"Two users type at the same position at the same moment. Both clients applied their
  own edit locally. Walk me through how they converge, mechanically."** (the crux — climb the ladder
  here until you find the edge) · "OT or CRDT — pick one and tell me what you gave up." · "The session
  server for a document crashes with 30 seconds of unpersisted operations. What's lost?" · "A user
  edits offline for a week, then reconnects." · "How does undo work when someone else has edited on
  top of yours?"
- *EM bar:* "What's the SLO for a document being available and not losing edits, and what's the SLI?"
  · "This is a famously hard system to get right. How would you de-risk it with a team of six —
  what's the first prototype?" · "What would you buy?"

**Curveball:** *"A document is opened by 200 people in a company all-hands."* Tests whether the
session model scales to a fan-out it wasn't designed for — read-only viewers should be served
differently from editors.

**Weak / Strong / Exceptional.** *Weak* — lock the document, or send the whole document on each
change, or "the server merges the changes" with no mechanism. *Strong* — local-first edits, a named
and correctly-explained convergence mechanism, per-document session servers, op log plus snapshots,
ephemeral presence. *Exceptional* — states the OT-vs-CRDT axis and picks for stated reasons, handles
session-server failure with a bounded loss window, has an honest answer on undo, and sequences a
de-risking prototype before committing the team.

**Traps.** Saying "CRDT" or "OT" as a brand with no mechanism — probe once and it collapses; score
depth accordingly. Putting cursor updates through the durable log (correct-looking, catastrophic for
volume). Assuming last-write-wins is acceptable for text — it silently destroys work, and they should
say so.

---

### SD-20 · Distributed cache   [T1 · M★ G A]

**Read aloud:** *"Design a distributed cache used by hundreds of services — the thing they put in
front of their databases."*

**Crux.** **Invalidation, and what a client can observe.** Adding a cache is trivial; keeping it
correct is not, and the question is really about whether they understand staleness as a contract rather
than an accident.

**If they ask:**

| Question | Answer |
|---|---|
| Scale? | 10M ops/sec, 100 TB of cached data, 500 nodes |
| Latency? | p99 under 1 ms |
| Hit ratio? | Currently 95%; the design should protect it |
| Consistency? | **"You tell me what you can offer."** This is the question |
| Eviction? | LRU is fine unless they argue otherwise |
| Durability? | None needed — it's a cache. But probe what happens on cold start |
| Multi-region? | Start single-region; use as a curveball |

**Listen for:**
- **Consistent hashing with virtual nodes**, and *why*: adding or removing a node moves only 1/N of
  keys instead of remapping everything. Ask what happens to the hit ratio during a rebalance.
- **Cache-aside vs read-through vs write-through vs write-behind**, with the trade-offs named — not
  just listed. Which one they pick should follow from the consistency answer.
- **Invalidation strategy**: TTL as the safety net, explicit invalidation on write for correctness,
  and the honest admission that **invalidation across a cluster is not atomic** — so there is always
  a window, and the design should state its size.
- **The thundering herd / stampede** on a popular key expiring, and a real mitigation
  (single-flight/request coalescing, probabilistic early refresh, or a lock per key) — this is the
  probe most candidates fail.
- **Hot keys** exceeding a single node's capacity: client-side local cache with a short TTL, or key
  replication across several nodes. Consistent hashing does not solve this and they should know that.
- **Cold start / cache flush** being an availability event for the database behind it — *"what happens
  to your database when the cache restarts?"* is the best failure probe here.
- **Negative caching** for lookups that miss, or the miss path becomes a DoS vector.
- Client-side vs server-side routing and where the topology lives.
- **← The senior insight:** the cache's failure mode is not "slow", it is **"the database gets the
  full 10M ops/sec"** — the cache must be sized and operated as a load-bearing dependency, not an
  optimisation.

**Probe ladder:**
- *Requirements:* "What staleness are you offering the callers, as a contract?" · "Is this cache
  allowed to be a hard dependency?"
- *Estimation:* "95% hit ratio at 10M ops/sec — what does the database see? Now at 90%." (a 5-point
  drop doubles the database load — a beautifully counter-intuitive number to make them compute)
- *Design:* the walk of a read miss and a write · "Who decides which node a key lives on?"
- *Deep dives:* **"The hottest key in the system expires and 50,000 requests miss simultaneously.
  What happens?"** · "You lose one node out of 500. What do you lose, and what does the database
  see?" · "You restart the whole cluster. Walk me through the next 60 seconds." · "One key gets 1M
  ops/sec on its own. Now what?" · "A write updates the database and the invalidation fails. What
  does the next reader see, and for how long?"
- *EM bar:* "What's the SLO of a cache, and what do you alert on — hit ratio, latency, or something
  else?" · "This is a shared service for 200 teams. What stops one team's traffic hurting another?" ·
  "What does 100 TB of memory cost, and would you rather have 50 TB and a lower hit ratio?"

**Curveball:** *"We need the cache in three regions now, and writes happen in all three."* Tests
whether they see that cross-region invalidation makes staleness unbounded in practice and that
region-local caches with region-local invalidation is usually the right answer.

**Weak / Strong / Exceptional.** *Weak* — "put Redis in front of the database", TTL-only, no herd
handling, no hot-key story, cache failure not considered. *Strong* — consistent hashing with virtual
nodes, an explicit consistency contract, invalidation plus TTL with the window acknowledged, stampede
mitigation, cold-start impact understood. *Exceptional* — computes the database load at several hit
ratios and uses it to argue the cache is a load-bearing dependency, handles hot keys separately from
distribution, designs multi-tenant isolation, and prices memory against hit ratio.

**Traps.** Claiming write-through gives strong consistency (it doesn't — there is a window between
the two writes, and a failure in between leaves them divergent). Believing consistent hashing solves
hot keys. Treating cache loss as a latency event rather than an availability event.


---

### SD-21 · Data warehouse / batch analytics platform   [T2 · A G N]

**Read aloud:** *"Design the analytics platform for the company — how data from a hundred services
gets to a place where analysts can query it, reliably, by 8 a.m."*

**Crux.** **The 8 a.m. deadline**, which turns this from a data-modelling question into a
dependency-scheduling and data-quality question. And **cost**, which in real warehouses dominates
every other consideration.

**Numbers if asked:** 100 source systems, 50 TB/day ingested, 5 PB total, 500 analysts, 10k queries/day
ranging from seconds to an hour, daily batch by 8 a.m. with some hourly tables, 13-month retention,
schema changes in source systems happen weekly and without warning.

**Listen for:** ingestion via CDC or extract, landing in **immutable, partitioned raw storage**
(bronze) before any transformation · a layered model — raw → cleaned → modelled/marts — with each
layer reproducible from the one before, so a bug is a re-run and not a data-loss event · **columnar
format with partitioning and clustering** chosen for the actual query patterns, and the compression
factor (~6×) in the sizing · an **orchestrator with an explicit dependency DAG**, retries, and
**backfill as a first-class operation** (not a manual heroic act) · **data-quality gates that block
publication** rather than alerting after the fact — the strong stance here is that a wrong number
served on time is worse than a right number served late, and they should be able to argue it either way
· **schema evolution** handled by contract with the source teams, and what happens when a source
silently changes a column type · **separating storage from compute** so the analyst-query load and the
batch load don't fight · **cost controls**: query cost attribution per team, partition pruning
enforced, and the observation that a single unpartitioned scan can cost more than a day of the
pipeline.

**Probes:** *"The 3 a.m. job fails. Walk me through the next five hours — who knows, what happens,
and does anyone get a wrong number?"* · *"A source team renames a column without telling you. What
breaks and when do you find out?"* · *"An analyst writes a query that scans 5 PB. What happens?"* ·
*"You need to re-run last month because of a bug. What does that cost and how long does it take?"* ·
*(EM bar)* *"What's the monthly bill, what's the biggest line item, and what's the first thing you'd
do to halve it?"*

**Weak / Strong / Exceptional.** *Weak* — nightly ETL scripts writing straight into final tables,
transformations that overwrite their inputs, quality checked by complaint. *Strong* — layered
immutable pipeline, orchestrated DAG with retries and backfill, columnar partitioned storage, blocking
quality gates, schema contracts. *Exceptional* — designs the missed-deadline runbook explicitly, makes
every layer reproducible, attributes cost per team as a governance mechanism, and takes a defensible
position on late-but-right versus on-time-but-wrong.

---

### SD-22 · Change data capture & replication pipeline   [T2 · A MS N]

**Read aloud:** *"Design a system that streams every change in our production databases to other
systems — search indexes, caches, the warehouse, other services."*

**Crux.** **Dual writes are the bug this system exists to eliminate**, and the candidate should say so:
you cannot atomically write to a database and publish an event, so the change stream must be derived
*from the database's own log*. If they propose application-level publishing, probe until they find the
failure.

**Numbers if asked:** 200 source databases, 500k changes/sec aggregate, 20 downstream consumers,
end-to-end lag target under 5 seconds, ordering must be preserved per row, downstream systems
occasionally need a full re-sync, schemas change weekly.

**Listen for:** **log-based CDC** (reading the database's replication log) versus query-based polling,
with the trade-off named: polling misses deletes and intermediate states and adds load; log-based is
correct but couples you to the engine · **the outbox pattern** as the alternative when log access
isn't available, and why it is still better than dual writes · **ordering guaranteed per key** by
partitioning on the primary key, with global ordering explicitly not offered · **at-least-once
delivery plus idempotent consumers**, which means every consumer must be able to apply the same change
twice — a requirement they should push onto consumers explicitly rather than pretending to solve
centrally · **snapshot + stream** for initial load and re-sync, and the hard part: the handover point
between the snapshot and the log position, done wrong in most first designs · **schema evolution**
with a registry and compatibility rules · **lag as the primary SLI**, per consumer, with the source
log retention as the hard deadline for recovery · what happens when a consumer is down longer than
the log retention (the answer is re-snapshot, and it should be a designed operation).

**Probes:** *"Why not just publish an event from the application when it writes?"* (drive to the dual
write failure) · *"A consumer needs a full copy plus the ongoing stream. How do you stitch the
snapshot to the log without gaps or duplicates?"* · *"A source table gets a new non-nullable column.
What happens downstream?"* · *"A consumer is down for three days and your log retains one. Now what?"*
· *(EM bar)* *"Twenty teams depend on this. What's the contract you publish, and what's your on-call
surface when a source database fails over?"*

**Weak / Strong / Exceptional.** *Weak* — application publishes events alongside its writes; no
snapshot story; ordering assumed global. *Strong* — log-based CDC, per-key ordering, at-least-once
with idempotent consumers, snapshot-to-stream handover, schema registry, lag monitoring.
*Exceptional* — articulates dual-write impossibility crisply, designs the re-snapshot operation as
routine, publishes an explicit consumer contract, and handles source failover and log-position
continuity.


---

### SD-23 · Multi-tenant SaaS platform isolation   [T2 · MS★ A G]

**Read aloud:** *"Design a multi-tenant platform where ten thousand customers share infrastructure —
and no customer can hurt another."*

**Crux.** **The noisy neighbour**, and the fact that fairness must be enforced at *every* shared
resource — not just the API tier. A per-endpoint rate limit does nothing about the tenant whose query
saturates a shared database.

**Numbers if asked:** 10k tenants ranging from 5 users to 500k, the largest tenant is 30% of total
load, tenants require logical data isolation with some demanding physical, per-tenant availability
99.9%, some tenants require EU-only data, a tenant onboards in under an hour, and a few tenants need
to stay on an older version for months.

**Listen for:** the isolation spectrum named and chosen deliberately — shared schema with a tenant
column, schema-per-tenant, database-per-tenant, **cell/pod-per-tenant-group** — with the
cost-versus-isolation trade-off and the operational cost of 10k databases · **tenant ID propagated
through every layer** and enforced at the data-access layer rather than trusted from the request (the
one bug in this design class that becomes a breach) · **quotas and rate limits per tenant at every
shared resource**: API, queue consumers, database connections, background jobs, storage · **cells** as
the blast-radius mechanism — a failure affects one cell of tenants, not all — plus the tenant-to-cell
placement and migration problem · **the largest tenant** getting its own cell, because a 30% tenant
in a shared cell is a permanent risk · **per-tenant observability**, so "is it us or them" is
answerable in seconds · **deployment**: rolling by cell, and the tenant pinned to an old version
forcing versioned APIs and a supported-window policy · noisy-neighbour detection *before* the
complaint.

**Probes:** *"One tenant runs a report that saturates a shared database. Walk me through what every
other tenant experiences and what your design does about it."* · *"Where exactly is the tenant filter
applied, and what happens if a developer forgets it?"* · *"Your biggest tenant is 30% of load. Where
do they live?"* · *"Tenant X needs to stay on v4 for six months. What does that do to your release
process?"* · *(EM bar)* *"A tenant opens a ticket saying the platform is slow. What do you look at,
and did you build it in advance?"*

**Weak / Strong / Exceptional.** *Weak* — one shared database with a `tenant_id` column, filtering in
application code, one rate limit at the API. *Strong* — deliberate isolation level with cost
justification, tenant enforced at the data layer, quotas at every shared resource, cells for blast
radius, per-tenant metrics. *Exceptional* — treats cell placement and tenant migration as designed
operations, isolates the whale tenant, has a supported-version policy with a stated cost, and detects
noisy neighbours before the ticket arrives.
