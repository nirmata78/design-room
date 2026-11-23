# SD-39 · Nearby drivers & ride matching — reference-solution video outline

Target level: staff · **Compact cut** (GUIDELINES §3.4): ≈ 60 min, ≈ 6,900 words, 6 challenges, no build-cost chapter, no drill.

## Thesis and definition

- **Thesis:** keep *where drivers are* as fast, overwrite-only, lossy memory, and *who gets which driver* as one exact
  conditional write, owned by one matcher per city.
- **Definition:** assigning scarce, moving resources to requests, exactly once, from an approximate picture of where they are.
- **Hook:** two problems that look like one: a geo problem (1.25 M writes a second, lossy is fine) and a contention problem
  (two riders, one driver, must be exact).

## Scale line (GUIDELINES §3.1)

Volume per month: **900 M trips** (30 M a day) · Total: **5 M drivers** online at peak, a location every 4 s · Peak: **one city
at midnight on New Year's Eve, × 10 requests for ten minutes**; 3,000 drivers within 2 km downtown at 6 p.m.

## 0 · What this question grades

| Axis | Weak | Strong |
|---|---|---|
| Requirements | "find the nearest driver" | asks what must never happen: one driver, two riders |
| Estimates | no write rate | 1.25 M writes a second, and what it rules out |
| Correctness | nearest wins, no claim | a conditional claim, fencing, an offer state machine |
| Depth | "use a geohash" | cells as 1-D keys, rings, hot cells, expiry |
| Operations | request success rate | probe trips; idle drivers next to "no drivers" |

## 1 · Requirements

Clarifying: never two riders per driver · offer within 5 s · nearest by distance for V1, by ETA better · cities independent ·
matching and tracking in scope; pricing, payment, routing out. FR1 Report · FR2 Match · FR3 Accept · FR4 Track. NFR: 0 double
assignments; 5 s p95; no location older than 8 s used; 99.95 % per city; a city's outage stays in the city. IN: intake, index,
matching, claims, offers, the trip until pickup, tracking. OUT: pricing, payment, routing, fraud, onboarding, pooled rides.

## 2 · Estimates

| Number | Arithmetic | Decides |
|---|---|---|
| Location writes | 5 M ÷ 4 s = 1.25 M/s; × 100 B = 125 MB/s | memory, overwrite-only |
| If durable | 1.25 M × 86,400 ≈ 1.1 × 10¹¹ rows ≈ 11 TB a day | not a database |
| Memory | 5 M × 200 B ≈ 1 GB | shards for isolation, not capacity |
| Gateway | 5 M ÷ 50,000 = 100 pods | persistent streams |
| Requests | 350 trips/s × 2 × 3 ≈ 2,100/s | a regional database takes the claims |
| NYE city | 10 % × 10 of peak ≈ 2,100/s | one matcher per city copes |
| Density | 3,000 ÷ 17 cells ≈ 180 per res-8 cell; busiest > 300 | hot cells to res 9 |
| ETA pairs | 2,100 × 20 = 42,000/s | shortlist, batch, cache |
| Budget | 2 s batch + 0.7 s index, ETA, claim + 0.5 s push ≈ 3.2 of 5 s | early ticks in quiet cities |

## 3 · Theory

Is / is not (map search, routing, telemetry) · S1 one trip per driver · S2 one trip per accept · L1 an answer in 5 s · L2 released
in seconds · tension figure · M1 cells as keys (k-ring figure) · cell systems compared (geohash, quadtree, S2, H3: pick) · M2 soft
state · M3 conditional, fenced claim · M4 leases and timeouts · M5 batched assignment · options: A database, B nearest-wins, C lock
per driver, D global optimiser, **E index + one matcher per city + conditional claims + batches** · sequence `seq-th-claim` ·
failure catalogue.

## 4 · API and entities

`POST /v1/rides` (FR2, idempotency key) · driver stream `Locations` (FR1, seq) · `Offer` / `Accept(offer_id)` (FR3) · rider car stream
(FR4). Entities: RIDER, REQUEST, TRIP, DRIVER, OFFER (weak), LOCATION. Physical: `driver_state` (version, lease), `trip`, `offer`,
`city_lease`, in-memory maps, location log.

## 5 · Design

| Version | Adds | Answers | Leaves |
|---|---|---|---|
| V1 | ride API, gateway, trip store (locations in it) | works | 1.25 M durable writes; a scan per request |
| V2 | in-memory location index | the write rate | two riders get one driver |
| V3 | matcher (leader per city), routing, location log, analytics | exact claims, ETA, history | is it right in production? |
| V4 (ch. 6) | probe riders | detection | — |

Trip state machine table. Flows: `flow-location`, `flow-match`. Sequences: `seq-location`, `seq-request`, `seq-offer`, `seq-track`.

## 5.1 · Components and technologies

Component views: matcher, location index.

<!-- stack:outline -->

| Container | Choice | How it is built | Rejected | Theory part |
|---|---|---|---|---|
| Location index | Go service, H3 resolution 8, in memory | Per city: driver → (cell, position, seq) and cell → drivers | Redis GEO; PostGIS | 6 §6.5, 17 §17.3 |
| Trip store | PostgreSQL per region, synchronous standby | `UPDATE driver_state … WHERE state='available' AND version=$v AND epoch current` | Redis for claims; Cassandra LWT | 8 §8.2, 2 §2.11 |
| Driver gateway | Go on Kubernetes, gRPC bidirectional streams | About 50,000 streams per pod, 100 pods | HTTP polling; An MQTT broker | 11 §11.6–11.7 |
| Matcher | Go service, leader per city via etcd lease | Every 2 s: shortlist 20 per request, one ETA matrix, a min-cost assignment, claims carrying the epoch. | Racing stateless matchers; ZooKeeper | 4 §4.3, 2 §2.11 |

Fix-slide rejections: 1: Redis SETNX as the claim; 2: A long fixed offer timeout; 3: Geohash prefixes alone; 4: Replicating the index synchronously; 5: Straight-line distance; 6: Request success rate.

<!-- /stack:outline -->

## 5.2 · Alternate path

PostgreSQL + PostGIS, updates every 15 s, claims with `SELECT … FOR UPDATE SKIP LOCKED`. Gives up: durable writes for soft data, no
batching, one database. Line: 20,000 drivers ÷ 15 s ≈ 1,300 updates/s; below ≈ 20,000 drivers, ship it.

## 7 · Challenges

### Challenge 1 · Two riders, one driver (crux)
Read-then-write race; fix: one leader per city (etcd lease, epoch) and one conditional `UPDATE` (available, version, epoch), SQL shown.
Push: PostgreSQL fail-over → synchronous standby; claims pause, never duplicate. Rejected: Redis `SETNX`.

### Challenge 2 · The driver who vanishes (crux, second half)
Offer timeout 15 s; 30 s heartbeat lease on accepted trips; idempotent accept by offer ID; lease-length trade table. Push: the phone
returns after 40 s → the store's version wins; the app is told. Rejected: a long fixed offer timeout.

### Challenge 3 · Boundaries and hot cells
Expanding k-rings to 20 candidates; res 9 for cells over 300 drivers; pseudocode. Push: stadium exit → a pickup-zone queue; supply
is pricing's lever. Rejected: geohash prefixes alone.

### Challenge 4 · A shard dies
No replicas; refill from the next 4 s of reports; sequence numbers drop old positions; replication cost table; pseudocode. Push:
NYE → hold one more tick; warm standby for the biggest cities. Rejected: synchronous replication of the index.

### Challenge 5 · Nearest is not closest
Shortlist 20 by distance, one ETA matrix per tick (cached per cell pair, 300 ms timeout, detour fallback), min-cost batch
assignment; greedy against batch table; pseudocode. Push: routing down → fallback, marked. Rejected: straight-line distance.

### Challenge 6 · "No drivers" next to idle drivers (observability)
**V4** probe riders; idle-next-to-"no" count; stale share per pod; time to offer; symptom pairs; SLIs (double assignments 0,
nightly audit). Rejected: request success rate.

## 8 · Recap

V4 with badges; one sentence per path; mistakes; thesis.

## Canon check

| Point | Covered at |
|---|---|
| Geo index (geohash, S2, H3, quadtree) and why | theory M1, cell systems table |
| Boundary handling (neighbour cells) | M1 figure, challenge 3 |
| Ephemeral location state; the write-rate estimate | estimates, M2, challenge 4 |
| Sharding by city | V2/V3, NFR |
| Atomic claim before offering | M3, challenge 1 |
| Offer state machine with timeouts and idempotent accept | M4, state machine, challenge 2 |
| Batch against greedy matching | M5, challenge 5 |
| ETA against distance | challenge 5 |
| Surge and supply | dismissed aloud: pricing's lever (challenge 3 push) |
| Cross-city matching | dismissed: cities are independent |

## Budget (measured)

0: 324 · 1: 426 · 2: 366 · 3: 909 · 4: 359 · 5 (+5.1, 5.2): 1,333 · 6: 82 · 7: 2,813 · 8: 243 · **total 6,855 words (≈ 60 min)**.
