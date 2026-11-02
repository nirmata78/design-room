# Question Bank — 93 system-design questions

The index. Cue sheets live in `questions/<LETTER>-<archetype>.md`, one file per archetype, each
question anchored as `### SD-nn`.

> **Interviewer: do not read a whole archetype file.** Slice it:
> ```bash
> grep -n '^### SD-08' questions/B-social-feed-content.md   # → line
> ```
> then `Read` with `offset` and `limit ≈ 90`. Reading the whole bank index is cheap; reading a whole
> archetype file is not.

**Candidates: don't read the cue sheets before a round** — they contain the answer. This index is safe.

**Reference solutions** — full stage-by-stage answer keys — exist for the rows marked
**solution**: SD-08, SD-09, SD-15, SD-25, SD-44, SD-47 ([index](solutions/README.md)). Run the round first,
read the solution after. The building blocks they rely on are in [Theory](theory/README.md).

## How the bank is organised — four ways to slice it

| Axis | Values | Use it to… |
|---|---|---|
| **Archetype** (A–K) | the technical family — what the round really tests | get coverage; one round per archetype beats ten in your comfort zone |
| **Kind** | **Build** (design X) · **Review** (inverted: critique an artifact) · **Strategy** (decide, sequence, invest) | match the round format your loop uses; senior levels see more Review and Strategy |
| **Domain** | `general` · `fintech` · `crypto` · `ai` · `social` · `commerce` · `media` · `search` · `mobility` · `saas` · `infra` · `data` | rehearse in your target industry — and, deliberately, outside your home turf |
| **Levels** | **Sr** senior · **St** staff · **Pr** principal · **EM** · **SEM** senior EM · **Dir** director | pick questions that load your target level's bar — see [`levels.md`](levels.md) |

**Tiers.** **T1** = full cue sheet: crux, clarification numbers, checklist, phase-by-phase probe
ladder, curveball, weak/strong/exceptional, traps. **T2** = compact sheet: prompt, numbers,
checklist, five probes, three bands — enough to run a complete round. **41 T1, 52 T2.**

**Asked by** — where the question shows up: **G** Google · **M** Meta · **A** Amazon · **MS** Microsoft ·
**N** Netflix · **U** Uber/Lyft/DoorDash-class · **FT** fintech (payment companies, neobanks, issuers,
lenders) · **CX** crypto exchanges & custodians · **AI** AI labs and AI-platform companies · **★** = a
flagship for that company class, the one you should assume will be asked.

**Every question can be run at every level** — the Levels column says where it is *most revealing*.
Running SD-08 at `director` is legitimate; the interviewer will steer to org and cost within fifteen
minutes (`levels.md` §3).

---

## A · Ingest, streaming & real-time analytics → [`questions/A-streaming-analytics.md`](questions/A-streaming-analytics.md)

| ID | Question | T | Kind | Domain | Levels | Asked by | Loads |
|---|---|:-:|---|---|---|---|---|
| SD-01 | Real-time audience metrics (approximate unique counts) | 1 | Build | data media | Sr St EM | G M A | streaming, approximation, lambda split |
| SD-02 | Trending now / Top-K leaderboard | 1 | Build | social media | Sr St EM | G★ M★ | read/write asymmetry, sliding windows, heavy hitters |
| SD-03 | Ad click aggregation & billing counters | 1 | Build | data | St EM | G★ M★ A | exactly-once accounting, late data, reconciliation |
| SD-04 | Metrics & monitoring pipeline | 2 | Build | infra data | Sr St EM | G M A MS | time-series storage, cardinality, downsampling |
| SD-05 | Log search & distributed tracing backend | 2 | Build | infra | St EM | G A N | inverted index at volume, sampling, retention tiers |
| SD-06 | A/B experiment platform | 2 | Build | data | St EM SEM | M★ G N | assignment consistency, metric pipelines, guardrails |
| SD-07 | Event-driven platform / durable log (Kafka-like) | 2 | Build | infra data | Sr St Pr | G A MS | partitioning, delivery semantics, consumer groups |

## B · Social, feed & content → [`questions/B-social-feed-content.md`](questions/B-social-feed-content.md)

| ID | Question | T | Kind | Domain | Levels | Asked by | Loads |
|---|---|:-:|---|---|---|---|---|
| SD-08 | News feed / home timeline · [**solution**](solutions/SD-08-news-feed.md) | 1 | Build | social | Sr St EM | M★ G | fan-out write vs read, the celebrity problem, ranking |
| SD-09 | Chat / messaging (1:1 + groups) · [**solution**](solutions/SD-09-chat-messaging.md) | 1 | Build | social | Sr St EM | M★ MS★ | connection state, ordering, delivery receipts, offline |
| SD-10 | Live comments & reactions on a live stream | 2 | Build | social media | Sr St | M★ | pub/sub fan-out, backpressure, shedding |
| SD-11 | Photo & video sharing (Instagram-like) | 2 | Build | social media | Sr EM | M★ | blob + metadata split, thumbnails, CDN |
| SD-12 | Notification & push platform | 1 | Build | social | Sr St EM | M A MS | multi-channel fan-out, dedup, preferences, rate control |
| SD-13 | Presence & online status | 2 | Build | social | Sr | M MS | heartbeat scale, fan-out cost, staleness budget |
| SD-14 | Social graph store (friends, follows, FoF) | 2 | Build | social | St Pr | M★ G | graph sharding, adjacency caching, bidirectional writes |

## C · Storage, data & consistency → [`questions/C-storage-data-consistency.md`](questions/C-storage-data-consistency.md)

| ID | Question | T | Kind | Domain | Levels | Asked by | Loads |
|---|---|:-:|---|---|---|---|---|
| SD-15 | Globally distributed KV store / multi-region consistency · [**solution**](solutions/SD-15-distributed-kv-store.md) | 1 | Build | infra | St Pr | G★ A MS | consensus, quorums, CAP honesty, replication |
| SD-16 | Object store data plane (S3-like) | 2 | Build | infra | St Pr | A★ G | erasure coding, durability math, large-object writes |
| SD-17 | Object storage control plane | 2 | Build | infra saas | St EM | A G | metadata at scale, quotas, lifecycle, tenancy |
| SD-18 | File sync (Drive / Dropbox) | 1 | Build | saas | Sr St EM | G★ MS | chunking, dedup, conflict resolution, sync protocol |
| SD-19 | Collaborative document editing | 1 | Build | saas | St Pr | G★ MS★ | OT vs CRDT, presence, offline merge, undo |
| SD-20 | Distributed cache | 1 | Build | infra | Sr St EM | M★ G A | consistent hashing, invalidation, stampedes, hot keys |
| SD-21 | Data warehouse / batch analytics platform | 2 | Build | data | St EM SEM | A G N | columnar storage, partitioning, orchestration, cost |
| SD-22 | Change data capture & replication pipeline | 2 | Build | data | St EM | A MS N | log-based CDC, schema evolution, ordering, backfill |
| SD-23 | Multi-tenant SaaS platform isolation | 2 | Build | saas | St EM SEM | MS★ A G | noisy neighbours, quotas, cells, per-tenant data |

## D · Infrastructure & control planes → [`questions/D-infrastructure-control-planes.md`](questions/D-infrastructure-control-planes.md)

| ID | Question | T | Kind | Domain | Levels | Asked by | Loads |
|---|---|:-:|---|---|---|---|---|
| SD-24 | Distributed lock / coordination service | 2 | Build | infra | St Pr | G★ A | consensus, fencing, lease expiry, safety vs liveness |
| SD-25 | Rate limiter (distributed) · [**solution**](solutions/SD-25-rate-limiter.md) | 1 | Build | infra | Sr St EM | G★ M★ A MS | algorithms, distributed counters, cell-local vs global |
| SD-26 | Feature flags & config delivery | 2 | Build | infra | Sr St EM | M★ N G | push vs poll, staleness, kill switches, targeting |
| SD-27 | Authorization / permission graph (Zanzibar-like) | 2 | Build | infra saas | St Pr | G★ MS | graph evaluation, caching consistency, tuple storage |
| SD-28 | Workflow orchestrator / distributed job scheduler | 1 | Build | infra | St EM | A★ G MS | durable state machines, retries, exactly-once effects |
| SD-29 | Device-fleet control plane (IoT) | 2 | Build | infra | St EM | G A MS | device identity, reconciliation loops, cohort rollout |
| SD-30 | API gateway / edge platform | 1 | Build | infra | St EM SEM | A★ MS G | authn/z at edge, routing, quotas, deploys, blast radius |
| SD-31 | Service discovery & load balancing | 2 | Build | infra | Sr St | G A N | health checking, propagation delay, LB algorithms |
| SD-32 | CI/CD & build platform (developer productivity) | 1 | Build | infra | St EM SEM | G★ M MS | build graph, caching, queueing, tenancy, DORA metrics |
| SD-33 | Cluster scheduler / capacity manager (Borg-like) | 2 | Build | infra | St Pr | G★ MS | bin packing, priority/preemption, quota, bad-node ejection |
| SD-34 | Secrets management & key rotation | 2 | Build | infra | St EM | MS A G | root of trust, rotation without downtime, blast radius |
| SD-35 | Progressive deployment & automatic rollback | 2 | Build | infra | St EM SEM | G N A | canary gates, halt conditions, blast radius, rollback safety |

## E · Search, geo & ML → [`questions/E-search-geo-ml.md`](questions/E-search-geo-ml.md)

See also archetype **I** for AI & LLM systems — SD-42 is the serving prerequisite for SD-63/SD-64.

| ID | Question | T | Kind | Domain | Levels | Asked by | Loads |
|---|---|:-:|---|---|---|---|---|
| SD-36 | Web crawler | 1 | Build | search | Sr St | G★ M | frontier, politeness, dedup, freshness, traps |
| SD-37 | Search indexing & serving | 2 | Build | search | St Pr | G★ M A | inverted index, sharding by doc vs term, ranking tiers |
| SD-38 | Typeahead / autocomplete | 1 | Build | search | Sr St | G★ M A | tries, precomputation, latency budget, personalisation |
| SD-39 | Nearby / ride matching (geo) | 1 | Build | mobility | Sr St EM | U★ G M | geo indexing, matching under contention, state machines |
| SD-40 | Maps routing & ETA | 2 | Build | mobility | St Pr | G★ U | graph preprocessing, contraction, live traffic ingestion |
| SD-41 | Recommendation serving & feature store | 1 | Build | ai commerce | St EM | M★ N★ A | candidate generation → ranking, feature freshness, skew |
| SD-42 | LLM inference serving / RAG platform | 1 | Build | ai | St Pr EM | G M MS A | GPU batching, KV cache, vector retrieval, cost per token |
| SD-43 | Abuse / fraud detection in real time | 2 | Build | fintech ai | St EM | M A★ | rules + model serving, latency budget, feedback loops |

## F · Transactions, payments & commerce → [`questions/F-transactions-payments.md`](questions/F-transactions-payments.md)

**SD-77–82 are the fintech expansion** — card issuing, KYC/AML, reconciliation, FX, payouts, credit. Pair with archetype **J** for digital-asset roles.

| ID | Question | T | Kind | Domain | Levels | Asked by | Loads |
|---|---|:-:|---|---|---|---|---|
| SD-44 | Payment processing & double-entry ledger · [**solution**](solutions/SD-44-payments-ledger.md) | 1 | Build | fintech | Sr St EM | A★ G MS | idempotency, exactly-once effects, sagas, reconciliation |
| SD-45 | Payment gateway integration (multi-PSP) | 2 | Build | fintech commerce | Sr St EM | A MS | adapter design, retries against third parties, webhooks |
| SD-46 | Digital wallet & balance transfers | 2 | Build | fintech | Sr St | A G | atomic balance moves, hot accounts, holds, audit |
| SD-47 | Ticket / seat booking under contention · [**solution**](solutions/SD-47-ticket-booking/SD-47_Ticket_Booking_Reference_Design.md) | 1 | Build | commerce | Sr St EM | A★ G MS | holds vs locks, oversell, fairness, expiry |
| SD-48 | Inventory & order management at scale | 1 | Build | commerce | St EM | A★ | reservation vs availability, distributed inventory, sagas |
| SD-49 | Delivery dispatch & order lifecycle | 2 | Build | mobility commerce | St EM | U★ A | long-lived state machines, assignment, real-time tracking |
| SD-50 | Subscription billing & usage metering | 2 | Build | saas fintech | St EM | A MS G | metering accuracy, proration, idempotent invoicing |
| SD-77 | Card authorisation & issuer processing | 1 | Build | fintech | Sr St EM | FT★ A MS | holds, stand-in, auth ↔ clearing matching |
| SD-93 | Personal investment tracker with price alerts | 1 | Build | fintech data | Sr St EM | FT G | two data speeds, inverted alert matching, unreliable third parties, restated history |
| SD-78 | KYC / AML onboarding & sanctions screening | 2 | Build | fintech | Sr EM | FT★ MS | durable workflow, fuzzy screening, continuous re-screening |
| SD-79 | Reconciliation & settlement engine | 1 | Build | fintech | St EM SEM | FT★ A MS | multi-pass matching, expectations, exception workflow |
| SD-80 | Cross-border payments & FX | 2 | Build | fintech | St EM | FT★ A | locked quotes, exposure, prefunding, multi-currency ledger |
| SD-81 | Payouts & disbursements to bank rails | 2 | Build | fintech commerce | Sr St EM | FT★ A U | exactly-once outbound, ambiguous rail status, returns |
| SD-82 | Real-time credit decisioning (BNPL) | 2 | Build | fintech ai | St EM | FT★ A | explainable decisions under budget, loan servicing |

## G · Media & delivery → [`questions/G-media-delivery.md`](questions/G-media-delivery.md)

| ID | Question | T | Kind | Domain | Levels | Asked by | Loads |
|---|---|:-:|---|---|---|---|---|
| SD-51 | Video upload, transcode & streaming (YouTube) | 1 | Build | media | St EM | G★ N★ M | pipeline fan-out, ABR, CDN, cost per hour watched |
| SD-52 | Live streaming at low latency | 2 | Build | media | St Pr | M★ N | ingest fan-out, latency-vs-resilience, catch-up |
| SD-53 | CDN / edge cache design | 2 | Build | media infra | St Pr | G N A | hierarchy, origin shielding, invalidation, hit ratio economics |
| SD-54 | Partner data-feed / large-file delivery | 1 | Build | data media | St EM | G A N | generation vs delivery split, versioning, deadlines, authz |

## H · EM & senior-manager rounds → [`questions/H-em-specific-rounds.md`](questions/H-em-specific-rounds.md)

**The archetype manager candidates skip, and the one an EM loop is most likely to contain in some form.** These are not "design X" questions — they test the work an engineering manager actually does. Several invert the round: **you** present something and they respond. **SD-89–92 are the senior-EM / director expansion** — strategy conversations where org shape and investment are the design.

| ID | Question | T | Kind | Domain | Levels | Asked by | Loads |
|---|---|:-:|---|---|---|---|---|
| SD-55 | Design review — critique and improve a given design | 1 | Review | general | St EM SEM | G★ A MS | judgment, prioritising findings, influence, tone |
| SD-56 | Migration — monolith → services, or datacentre → cloud | 1 | Strategy | general | St EM SEM | A★ MS★ G | sequencing, dual-write/backfill, rollback, org staging |
| SD-57 | Capacity, cost & FinOps review | 1 | Review | general | EM SEM Dir | A★ N G | unit economics, cost drivers, the levers, forecasting |
| SD-58 | Reliability & SLO design for an existing system | 1 | Review | general | St EM SEM | G★ A N | SLI selection, error budgets, alerting, on-call load |
| SD-59 | Multi-team decomposition & API contracts | 1 | Strategy | general | Pr EM SEM | G★ MS A | Conway's law, seams, contract versioning, dependency risk |
| SD-60 | Platform consolidation / tech-debt strategy | 2 | Strategy | general | Pr SEM Dir | MS A G | portfolio judgment, deprecation, migration incentives |
| SD-61 | Incident → design fix | 2 | Review | general | St EM | A★ G N | RCA discipline, systemic vs local fixes, prevention |
| SD-62 | Build vs buy | 2 | Strategy | general | EM SEM Dir | MS A G | TCO, differentiation, exit cost, team capability |
| SD-89 | Org & architecture for a new product line | 1 | Strategy | saas | SEM Dir | G MS A | Conway's law by design, reuse vs build, sequenced hiring |
| SD-90 | Reliability program after a major outage | 2 | Strategy | general | SEM Dir | A★ G N | the failure class, SLOs/error budgets, no blanket freeze |
| SD-91 | Annual planning — roadmap, headcount, platform | 2 | Strategy | general | EM SEM Dir | G MS A | capacity model, explicit trade-offs, platform business case |
| SD-92 | Cloud, vendor & multi-region strategy | 2 | Strategy | infra | Pr SEM Dir | A MS G N | conflicting asks quantified, tiered redundancy, leverage |

## I · AI & LLM systems → [`questions/I-ai-llm-systems.md`](questions/I-ai-llm-systems.md)

**New.** Designing around a component that is expensive, non-deterministic and occasionally wrong. Related: SD-41, SD-42, SD-43 in E.

| ID | Question | T | Kind | Domain | Levels | Asked by | Loads |
|---|---|:-:|---|---|---|---|---|
| SD-63 | LLM gateway & multi-model router | 1 | Build | ai | St EM SEM | G MS A AI | quotas & chargeback, routing/fallback, PII egress control |
| SD-64 | AI agent platform — tool-using agents | 1 | Build | ai | St Pr EM | AI★ G MS | delegated least privilege, durable execution, injection containment |
| SD-65 | LLM evaluation & observability platform | 2 | Build | ai | St EM | AI★ G M | no ground truth, calibrated judges, change gating |
| SD-66 | Distributed training & GPU cluster scheduler | 1 | Build | ai infra | St Pr | AI★ G M MS | gang scheduling, failure math, checkpoints, goodput |
| SD-67 | Vector search at billion scale | 2 | Build | ai search | Sr St | G M A AI | ANN recall vs memory, filtering, freshness |
| SD-68 | Content moderation — ML plus human review | 2 | Build | social ai | St EM SEM | M★ G MS | triage by severity × confidence, reviewer capacity, retro policy |
| SD-69 | ML platform — notebook to production | 2 | Build | ai data | St EM SEM | M G A N | train/serve skew, point-in-time features, lineage |
| SD-70 | AI code-completion backend | 2 | Build | ai | Sr St | AI G MS | latency budget, cancellation, context assembly |

## J · Crypto & digital assets → [`questions/J-crypto-digital-assets.md`](questions/J-crypto-digital-assets.md)

**New.** Custody of irreversible value against an adversary, with an external ledger that can reorganise. Asked at exchanges and at fintechs adding digital-asset products.

| ID | Question | T | Kind | Domain | Levels | Asked by | Loads |
|---|---|:-:|---|---|---|---|---|
| SD-71 | Exchange matching engine & order book | 1 | Build | crypto fintech | St Pr | CX★ FT | sequencer + log as truth, single-threaded books, replay |
| SD-72 | Custodial wallet — hot/warm/cold keys | 1 | Build | crypto | St EM | CX★ FT | risk-tiered custody, policy at the signer, insider threat |
| SD-73 | Deposit detection & crediting across chains | 2 | Build | crypto | Sr St | CX | reorgs, confirmation state machine, idempotent credits |
| SD-74 | Blockchain indexer & on-chain data API | 2 | Build | crypto data | Sr St | CX | reorg-aware CDC, backfill, hot addresses |
| SD-75 | Margin & liquidation engine | 2 | Build | crypto fintech | St | CX FT | incremental risk, liquidation-price index, volatility peaks |
| SD-76 | Fiat on-ramp & proof of reserves | 2 | Build | crypto fintech | St EM | CX FT | reversibility asymmetry, Merkle liabilities, attestation |

## K · Staff+ technical-leadership rounds → [`questions/K-staff-technical-leadership.md`](questions/K-staff-technical-leadership.md)

**New. The IC-track counterpart to H.** Strategy, API review, deprecation, rewrite-vs-refactor, a performance investigation, and arbitration — judgment exercised without a reporting line. Two are inverted (SD-84, SD-87).

| ID | Question | T | Kind | Domain | Levels | Asked by | Loads |
|---|---|:-:|---|---|---|---|---|
| SD-83 | Technical strategy — a 3-year platform direction | 1 | Strategy | general | St Pr SEM Dir | G★ MS A | diagnosis, few bets, what to stop, adoption without authority |
| SD-84 | API design review | 1 | Review | general fintech | St Pr EM | G★ MS A | one-way doors, idempotency, money types, contracts |
| SD-85 | Deprecating a widely used internal system | 2 | Strategy | general | St Pr SEM | G MS A | migration without mandate, zero-cost path, long tail |
| SD-86 | Rewrite vs refactor | 2 | Strategy | general | St Pr EM | G MS A N | hidden requirements, strangler, evidence for the call |
| SD-87 | Performance investigation — the p99 regression | 1 | Review | general | Sr St Pr | G★ M A | hypotheses from evidence, tail latency, mitigate vs fix |
| SD-88 | Arbitrating two teams' competing designs | 2 | Strategy | general | St Pr SEM | G★ MS A | agreed criteria, finding the crux, decidable disagreement |

---

## Browse by level

The questions that are **most revealing** at each level — the ones where the level's bar is the
thing being tested. Full ladder in [`levels.md`](levels.md).

| Level | Most revealing (★ = start here) | Also strong |
|---|---|---|
| **Sr** | SD-25★ SD-20★ SD-38 SD-02 SD-47 SD-87 | SD-09 SD-44 SD-67 SD-73 SD-77 |
| **St** | SD-15★ SD-19★ SD-28 SD-66 SD-71 SD-84 SD-87 | SD-24 SD-27 SD-33 SD-42 SD-64 SD-79 SD-86 |
| **Pr** | SD-83★ SD-88★ SD-27 SD-33 SD-59 SD-60 | SD-14 SD-15 SD-66 SD-71 SD-85 SD-92 |
| **EM** | SD-55★ SD-58★ SD-08 SD-44 SD-57 SD-59 | SD-12 SD-28 SD-32 SD-63 SD-77 SD-79 SD-91 |
| **SEM** | SD-56★ SD-59★ SD-60 SD-90 SD-92 | SD-23 SD-32 SD-63 SD-68 SD-79 SD-85 SD-88 |
| **Dir** | SD-89★ SD-91★ SD-90 SD-92 SD-62 SD-60 | SD-57 SD-83 |

Questions tagged per level: **Sr** 30 · **St** 81 · **Pr** 25 · **EM** 59 · **SEM** 24 · **Dir** 8.

## Browse by domain

Run at least one round **in your target domain** before a domain-specific loop, and at least one
**outside** it — fluent vocabulary in your own domain hides weak reasoning (`profile.md` raises the
bar on your home domain).

| Domain | Questions | Core test in this domain |
|---|---|---|
| `general` | SD-55 SD-56 SD-57 SD-58 SD-59 SD-60 SD-61 SD-62 SD-83 SD-84 SD-85 SD-86 SD-87 SD-88 SD-90 SD-91 | judgment, sequencing, review — domain-neutral rounds |
| `fintech` | SD-43 SD-44 SD-45 SD-46 SD-50 SD-71 SD-75 SD-76 SD-77 SD-78 SD-79 SD-80 SD-81 SD-82 SD-84 SD-93 | correctness under retry; you are not the only ledger |
| `crypto` | SD-71 SD-72 SD-73 SD-74 SD-75 SD-76 | irreversible value, key custody, reorgs |
| `ai` | SD-41 SD-42 SD-43 SD-63 SD-64 SD-65 SD-66 SD-67 SD-68 SD-69 SD-70 SD-82 | expensive, non-deterministic components; evaluation without ground truth |
| `social` | SD-02 SD-08 SD-09 SD-10 SD-11 SD-12 SD-13 SD-14 SD-68 | fan-out, the celebrity problem, abuse at scale |
| `commerce` | SD-41 SD-45 SD-47 SD-48 SD-49 SD-81 | contention for scarce inventory, sagas |
| `media` | SD-01 SD-02 SD-10 SD-11 SD-51 SD-52 SD-53 SD-54 | moving bytes cheaply — egress dominates |
| `search` | SD-36 SD-37 SD-38 SD-67 | precomputation under a latency budget |
| `mobility` | SD-39 SD-40 SD-49 | geo indexing, matching under contention |
| `saas` | SD-17 SD-18 SD-19 SD-23 SD-27 SD-50 SD-89 | tenancy, isolation, collaboration |
| `infra` | SD-04 SD-05 SD-07 SD-15 SD-16 SD-17 SD-20 SD-24 SD-25 SD-26 SD-27 SD-28 SD-29 SD-30 SD-31 SD-32 SD-33 SD-34 SD-35 SD-53 SD-66 SD-92 | control plane vs data plane, blast radius |
| `data` | SD-01 SD-03 SD-04 SD-06 SD-07 SD-21 SD-22 SD-54 SD-69 SD-74 SD-93 | event time, exactly-once accounting, lineage |

## Browse by kind

- **Review** (6) — **Inverted** — the interviewer presents an artifact with planted defects and you review it. Rules: top of `H-em-specific-rounds.md`. SD-55 · SD-57 · SD-58 · SD-61 · SD-84 · SD-87
- **Strategy** (12) — Decide, sequence, invest — the "design" is a plan, a recommendation or an org shape. SD-56 · SD-59 · SD-60 · SD-62 · SD-83 · SD-85 · SD-86 · SD-88 · SD-89 · SD-90 · SD-91 · SD-92
- **Build** (75) — Classic "design X". Every other question.

---

## Selection guidance

**If a real loop is close, run the company flagships first:**

| Company class | Run these |
|---|---|
| **Google L6 EM / Staff** | SD-15, SD-36, SD-02, SD-25, SD-19, SD-32, and **two from H or K** (SD-58, SD-59 for EM · SD-84, SD-87 for Staff) |
| **Meta E6 EM / Staff** | SD-08, SD-09, SD-20, SD-41, SD-10, SD-06, SD-68 |
| **Amazon L6/L7** | SD-48, SD-44, SD-47, SD-28, SD-30, SD-56, SD-57, SD-61, SD-90 |
| **Microsoft Principal / M2** | SD-23, SD-19, SD-09, SD-34, SD-56, SD-59, SD-63 |
| **Netflix** | SD-51, SD-52, SD-41, SD-35, SD-57 |
| **Fintech** (payments, neobank, issuing, lending) | SD-44, SD-77, SD-79, SD-81, SD-45, SD-80, SD-78, plus SD-84 |
| **Crypto exchange / custodian** | SD-71, SD-72, SD-73, SD-44, SD-75, SD-76 |
| **AI lab / AI platform** | SD-42, SD-63, SD-64, SD-66, SD-65, SD-67 |
| **Director / Head of Engineering loops** | SD-89, SD-91, SD-90, SD-92, SD-62, SD-60 |
| **Data-heavy product company, hour-long requirement-drip round** (`data-co`, format `drip`, pace `hour`) | SD-47, SD-18, SD-39, SD-12, SD-93 — each carries two scripted drips |

**If there is no loop yet, go for coverage:** one round in each archetype (A–K) beats ten rounds in the
two that feel comfortable. `Progress-Log.md` tracks this.

**The questions that most reliably expose a gap at each bar** — where strong ICs stall and managers
should not, or the reverse:

- **EM bar:** SD-58 (SLOs and on-call), SD-57 (cost), SD-59 (splitting work across teams), SD-56
  (sequencing a migration).
- **Staff bar:** SD-87 (diagnosis from evidence), SD-84 (one-way-door review), SD-15 (consistency
  honesty), SD-88 (making a disagreement decidable).
- **Director bar:** SD-89 (Conway's law by design), SD-91 (capacity is the constraint), SD-92 (exposing
  conflicting asks).

**Don't practise what is already strong.** After each round the debrief names one weak dimension;
the next question should load that dimension hard:

| Weak dimension | Questions that load it hardest |
|---|---|
| Requirements & scoping | SD-55, SD-12, SD-21, SD-83 — all deliberately over-broad |
| Estimation | SD-03, SD-05, SD-51, SD-57, SD-66 — the numbers dominate the design |
| Technical depth | SD-15, SD-19, SD-24, SD-16, SD-71, SD-87 — nowhere to hide |
| Trade-off reasoning | SD-08, SD-18, SD-20, SD-62, SD-67, SD-86 — each has two defensible answers |
| Operations / cost | SD-58, SD-57, SD-35, SD-30, SD-63, SD-92 |
| Ambiguity & pushback | any T1 at `brutal` difficulty; SD-55, SD-56, SD-88 especially |
| Leadership signal | SD-59, SD-56, SD-60, SD-32, SD-85, SD-89 |

---

## Adding a question

1. Build the sheet with `Cue-Sheet-Template.md`.
2. Append it to the right archetype file as `### SD-nn · Title   [T1 · G★ M]`. **IDs are global and
   monotonic** — take the next free number (currently **SD-94**) even if it lands in an older
   archetype; the archetype file's header lists its ranges.
3. Add a row here with Kind, Domain and Levels.
4. Open a pull request — see `CONTRIBUTING.md`.
