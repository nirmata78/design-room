# Question Bank — 62 system-design questions, L6 EM calibrated

The index. Cue sheets live in `questions/<LETTER>-<archetype>.md`, one file per archetype, each
question anchored as `### SD-nn`.

> **Interviewer: do not read a whole archetype file.** Slice it:
> ```bash
> grep -n '^### SD-08' questions/B-social-feed-content.md   # → line
> ```
> then `Read` with `offset` and `limit ≈ 90`. Reading the whole bank index is cheap; reading a whole
> archetype file is not.

**Tiers.** **T1** = full cue sheet: crux, clarification numbers, checklist, phase-by-phase probe
ladder, curveball, weak/strong/exceptional, traps. **T2** = compact sheet: prompt, numbers,
checklist, five probes, three bands — enough to run a complete round. **29 T1, 33 T2.**

**Frequency** is where the question actually shows up: **G** Google · **M** Meta · **A** Amazon ·
**MS** Microsoft · **N** Netflix · **U** Uber/Lyft/DoorDash-class · **★** = a flagship for that
company, the one you should assume will be asked.

---

## A · Ingest, streaming & real-time analytics → [`questions/A-streaming-analytics.md`](questions/A-streaming-analytics.md)

| ID | Question | T | Asked by | Loads |
|---|---|:-:|---|---|
| SD-01 | Real-time audience metrics (approximate unique counts) | 1 | G M A | streaming, approximation, lambda split |
| SD-02 | Trending now / Top-K leaderboard | 1 | G★ M★ | read/write asymmetry, sliding windows, heavy hitters |
| SD-03 | Ad click aggregation & billing counters | 1 | G★ M★ A | exactly-once accounting, late data, reconciliation |
| SD-04 | Metrics & monitoring pipeline | 2 | G M A MS | time-series storage, cardinality, downsampling |
| SD-05 | Log search & distributed tracing backend | 2 | G A N | inverted index at volume, sampling, retention tiers |
| SD-06 | A/B experiment platform | 2 | M★ G N | assignment consistency, metric pipelines, guardrails |
| SD-07 | Event-driven platform / durable log (Kafka-like) | 2 | G A MS | partitioning, delivery semantics, consumer groups |

## B · Social, feed & content → [`questions/B-social-feed-content.md`](questions/B-social-feed-content.md)

| ID | Question | T | Asked by | Loads |
|---|---|:-:|---|---|
| SD-08 | News feed / home timeline | 1 | M★ G | fan-out write vs read, the celebrity problem, ranking |
| SD-09 | Chat / messaging (1:1 + groups) | 1 | M★ MS★ | connection state, ordering, delivery receipts, offline |
| SD-10 | Live comments & reactions on a live stream | 2 | M★ | pub/sub fan-out, backpressure, shedding |
| SD-11 | Photo & video sharing (Instagram-like) | 2 | M★ | blob + metadata split, thumbnails, CDN |
| SD-12 | Notification & push platform | 1 | M A MS | multi-channel fan-out, dedup, preferences, rate control |
| SD-13 | Presence & online status | 2 | M MS | heartbeat scale, fan-out cost, staleness budget |
| SD-14 | Social graph store (friends, follows, FoF) | 2 | M★ G | graph sharding, adjacency caching, bidirectional writes |

## C · Storage, data & consistency → [`questions/C-storage-data-consistency.md`](questions/C-storage-data-consistency.md)

| ID | Question | T | Asked by | Loads |
|---|---|:-:|---|---|
| SD-15 | Globally distributed KV store / multi-region consistency | 1 | G★ A MS | consensus, quorums, CAP honesty, replication |
| SD-16 | Object store data plane (S3-like) | 2 | A★ G | erasure coding, durability math, large-object writes |
| SD-17 | Object storage control plane | 2 | A G | metadata at scale, quotas, lifecycle, tenancy |
| SD-18 | File sync (Drive / Dropbox) | 1 | G★ MS | chunking, dedup, conflict resolution, sync protocol |
| SD-19 | Collaborative document editing | 1 | G★ MS★ | OT vs CRDT, presence, offline merge, undo |
| SD-20 | Distributed cache | 1 | M★ G A | consistent hashing, invalidation, stampedes, hot keys |
| SD-21 | Data warehouse / batch analytics platform | 2 | A G N | columnar storage, partitioning, orchestration, cost |
| SD-22 | Change data capture & replication pipeline | 2 | A MS N | log-based CDC, schema evolution, ordering, backfill |
| SD-23 | Multi-tenant SaaS platform isolation | 2 | MS★ A G | noisy neighbours, quotas, cells, per-tenant data |

## D · Infrastructure & control planes → [`questions/D-infrastructure-control-planes.md`](questions/D-infrastructure-control-planes.md)

| ID | Question | T | Asked by | Loads |
|---|---|:-:|---|---|
| SD-24 | Distributed lock / coordination service | 2 | G★ A | consensus, fencing, lease expiry, safety vs liveness |
| SD-25 | Rate limiter (distributed) | 1 | G★ M★ A MS | algorithms, distributed counters, cell-local vs global |
| SD-26 | Feature flags & config delivery | 2 | M★ N G | push vs poll, staleness, kill switches, targeting |
| SD-27 | Authorization / permission graph (Zanzibar-like) | 2 | G★ MS | graph evaluation, caching consistency, tuple storage |
| SD-28 | Workflow orchestrator / distributed job scheduler | 1 | A★ G MS | durable state machines, retries, exactly-once effects |
| SD-29 | Device-fleet control plane (IoT) | 2 | G A MS | device identity, reconciliation loops, cohort rollout |
| SD-30 | API gateway / edge platform | 1 | A★ MS G | authn/z at edge, routing, quotas, deploys, blast radius |
| SD-31 | Service discovery & load balancing | 2 | G A N | health checking, propagation delay, LB algorithms |
| SD-32 | CI/CD & build platform (developer productivity) | 1 | G★ M MS | build graph, caching, queueing, tenancy, DORA metrics |
| SD-33 | Cluster scheduler / capacity manager (Borg-like) | 2 | G★ MS | bin packing, priority/preemption, quota, bad-node ejection |
| SD-34 | Secrets management & key rotation | 2 | MS A G | root of trust, rotation without downtime, blast radius |
| SD-35 | Progressive deployment & automatic rollback | 2 | G N A | canary gates, halt conditions, blast radius, rollback safety |

## E · Search, geo & ML → [`questions/E-search-geo-ml.md`](questions/E-search-geo-ml.md)

| ID | Question | T | Asked by | Loads |
|---|---|:-:|---|---|
| SD-36 | Web crawler | 1 | G★ M | frontier, politeness, dedup, freshness, traps |
| SD-37 | Search indexing & serving | 2 | G★ M A | inverted index, sharding by doc vs term, ranking tiers |
| SD-38 | Typeahead / autocomplete | 1 | G★ M A | tries, precomputation, latency budget, personalisation |
| SD-39 | Nearby / ride matching (geo) | 1 | U★ G M | geo indexing, matching under contention, state machines |
| SD-40 | Maps routing & ETA | 2 | G★ U | graph preprocessing, contraction, live traffic ingestion |
| SD-41 | Recommendation serving & feature store | 1 | M★ N★ A | candidate generation → ranking, feature freshness, skew |
| SD-42 | LLM inference serving / RAG platform | 1 | G M MS A | GPU batching, KV cache, vector retrieval, cost per token |
| SD-43 | Abuse / fraud detection in real time | 2 | M A★ | rules + model serving, latency budget, feedback loops |

## F · Transactions, payments & commerce → [`questions/F-transactions-payments.md`](questions/F-transactions-payments.md)

| ID | Question | T | Asked by | Loads |
|---|---|:-:|---|---|
| SD-44 | Payment processing & double-entry ledger | 1 | A★ G MS | idempotency, exactly-once effects, sagas, reconciliation |
| SD-45 | Payment gateway integration (multi-PSP) | 2 | A MS | adapter design, retries against third parties, webhooks |
| SD-46 | Digital wallet & balance transfers | 2 | A G | atomic balance moves, hot accounts, holds, audit |
| SD-47 | Ticket / seat booking under contention | 1 | A★ G MS | holds vs locks, oversell, fairness, expiry |
| SD-48 | Inventory & order management at scale | 1 | A★ | reservation vs availability, distributed inventory, sagas |
| SD-49 | Delivery dispatch & order lifecycle | 2 | U★ A | long-lived state machines, assignment, real-time tracking |
| SD-50 | Subscription billing & usage metering | 2 | A MS G | metering accuracy, proration, idempotent invoicing |

## G · Media & delivery → [`questions/G-media-delivery.md`](questions/G-media-delivery.md)

| ID | Question | T | Asked by | Loads |
|---|---|:-:|---|---|
| SD-51 | Video upload, transcode & streaming (YouTube) | 1 | G★ N★ M | pipeline fan-out, ABR, CDN, cost per hour watched |
| SD-52 | Live streaming at low latency | 2 | M★ N | ingest fan-out, latency-vs-resilience, catch-up |
| SD-53 | CDN / edge cache design | 2 | G N A | hierarchy, origin shielding, invalidation, hit ratio economics |
| SD-54 | Partner data-feed / large-file delivery | 1 | G A N | generation vs delivery split, versioning, deadlines, authz |

## H · EM-specific rounds → [`questions/H-em-specific-rounds.md`](questions/H-em-specific-rounds.md)

**The archetype candidates skip, and the one an L6 EM loop is most likely to contain in some
form.** These are not "design X" questions — they test the work an engineering manager actually
does. Several invert the round: **you** present something and they respond.

| ID | Question | T | Asked by | Loads |
|---|---|:-:|---|---|
| SD-55 | Design review — critique and improve a given design | 1 | G★ A MS | judgment, prioritising findings, influence, tone |
| SD-56 | Migration — monolith → services, or datacentre → cloud | 1 | A★ MS★ G | sequencing, dual-write/backfill, rollback, org staging |
| SD-57 | Capacity, cost & FinOps review | 1 | A★ N G | unit economics, cost drivers, the levers, forecasting |
| SD-58 | Reliability & SLO design for an existing system | 1 | G★ A N | SLI selection, error budgets, alerting, on-call load |
| SD-59 | Multi-team decomposition & API contracts | 1 | G★ MS A | Conway's law, seams, contract versioning, dependency risk |
| SD-60 | Platform consolidation / tech-debt strategy | 2 | MS A G | portfolio judgment, deprecation, migration incentives |
| SD-61 | Incident → design fix | 2 | A★ G N | RCA discipline, systemic vs local fixes, prevention |
| SD-62 | Build vs buy | 2 | MS A G | TCO, differentiation, exit cost, team capability |

---

## Selection guidance

**If a real loop is close, run the company flagships first:**

| Company | Run these |
|---|---|
| **Google L6 EM** | SD-15, SD-36, SD-02, SD-25, SD-19, SD-32, and **two from H** (SD-58, SD-59) |
| **Meta E6 EM** | SD-08, SD-09, SD-20, SD-41, SD-10, SD-06 |
| **Amazon L6/L7** | SD-48, SD-44, SD-47, SD-28, SD-30, SD-56, SD-57, SD-61 |
| **Microsoft Principal/M2** | SD-23, SD-19, SD-09, SD-34, SD-56, SD-59 |
| **Netflix** | SD-51, SD-52, SD-41, SD-35, SD-57 |

**If there is no loop yet, go for coverage:** one round in each of A–H beats eight rounds in the two
archetypes that feel comfortable. `Progress-Log.md` tracks this.

**The four questions that most reliably expose a gap at the EM bar** — because they are the ones
where strong ICs stall and managers should not: **SD-58** (SLOs and on-call), **SD-57** (cost),
**SD-59** (splitting work across teams), **SD-56** (sequencing a migration).

**Don't practise what is already strong.** After each round the debrief names one weak dimension;
the next question should load that dimension hard:

| Weak dimension | Questions that load it hardest |
|---|---|
| Requirements & scoping | SD-55, SD-12, SD-21 — all deliberately over-broad |
| Estimation | SD-03, SD-05, SD-51, SD-57 — the numbers dominate the design |
| Technical depth | SD-15, SD-19, SD-24, SD-16 — nowhere to hide |
| Trade-off reasoning | SD-08, SD-18, SD-20, SD-62 — each has two genuinely defensible answers |
| Operations / cost | SD-58, SD-57, SD-35, SD-30 |
| Ambiguity & pushback | any T1 at `brutal` difficulty; SD-55 and SD-56 especially |
| Leadership signal | SD-59, SD-56, SD-60, SD-32 |

---

## Adding a question

1. Build the sheet with `Cue-Sheet-Template.md`.
2. Append it to the right archetype file as `### SD-nn · Title` — **keep IDs monotonic within the
   archetype's range** so the ranges stay greppable.
3. Add a row here.
4. Open a pull request — see `CONTRIBUTING.md`.
