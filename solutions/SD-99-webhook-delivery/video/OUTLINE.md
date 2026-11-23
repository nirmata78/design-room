# SD-99 · Outbound webhook & partner event-delivery platform — reference-solution video outline

Target level: staff, manager layer AUX (the build-cost chapter carries the SD-59 overlay: team seams, contracts, API governance)
· **Full shape** (GUIDELINES §3), 7 challenges · Word budget 10,000–11,000 · Logical slides ≈ 160.
Set in the world of SD-82 (origination) and SD-95 (servicing): a point-of-sale lender's loan and payment events to merchants and a partner bank.

## Thesis and definition

- **Thesis** (key line): *We promise at-least-once delivery and give every endpoint its own failure budget; exactly-once is the consumer's job, and the contract that makes it possible is the product.*
- **Definition:** a platform that turns committed state changes into signed HTTP calls to endpoints we do not control, retries them for days, and never lets one endpoint take capacity from another.
- **Hook:** the first version is one POST inside the booking request; it fails the first time a merchant's server takes 30 seconds.

## Scale line (GUIDELINES §3.1)

60 M events a month (origination, funding, servicing) × ≈ 3 subscriptions → **180 M deliveries a month** (≈ 70/s) · over 30 days: ≈ 216 M attempt rows, ≈ 120 GB of payloads · **peak 800 events/s → 2,400 deliveries/s**, cause: the bank's settlement file posts 480,000 payments in ≈ 10 minutes (SD-95), ×34 the average · 20,000 endpoints, ≈ 3 % (600) failing at any moment. Illustrative.

## 0 · What this question grades

| Axis | Weak | Strong |
|---|---|---|
| Requirements | "send a webhook" | who subscribes and what they do with it; ordering; retry window; latency |
| Correctness | call inside the transaction; exactly-once | outbox; at-least-once; event ID and per-loan sequence |
| Trade-offs | one shared queue; fixed retry count | isolation per endpoint; full jitter; disable policy; buy against build |
| Depth | "a queue with retries" | the claimed row, the timer column, the lease, the ramp |
| Operations | API uptime | lag we own; success to healthy endpoints; SSRF, secrets and the contract owned |

## 1 · Requirements

Six clarifying answers: subscribers (tills and accounting systems self-serve; the partner bank by contract) · order not guaranteed, fetch current state allowed · first attempt p99 < 5 s, 72 h of retries · at-least-once, say so · 2 KB, one region · producers own events, merchants must not break.
FR1 register and subscribe · FR2 emit atomically with the change · FR3 deliver, signed, retried · FR4 attempts, redeliver, replay.
NFR: zero loss after commit; p99 first attempt < 5 s; one endpoint adds < 1 s to anyone else's p99; 72 h; ingest 99.95 %; never a private address.
IN/OUT pair; "the core is three things"; C4 context closes the chapter.

## 2 · Estimates (all from the scale line)

| Number | From | Arithmetic | Decision |
|---|---|---|---|
| In flight at peak | peak | 2,400 × 0.25 s ≈ 600 | the fleet is small; time held is the risk |
| One slow endpoint | peak | 120/s × 10 s = 1,200 | a cap per endpoint; tier pools |
| Two-day outage | average | 1.4/s × 172,800 ≈ 240,000; 1,700 × normal load if dumped | rows, not memory; a ramp |
| Storage | volume | attempts ≈ 108 GB/month; payloads ≈ 120 GB/month; ≈ 10,000 writes/s at peak | daily partitions; one payload per event; 4 shards |
| Latency budget | NFR | 0.5 + 0.5 + 0.5 + 2 + 1.5 = 5 s | poll intervals are the dial |

## 3 · Theory

1. Is / is not (broker, push notifications, webhooks received, exactly-once). 2. S1 no loss / no event for a rollback; S2 no private address; S3 no unsigned or replayable call · L1 delivered or visibly dead in 72 h; L2 healthy endpoints served while others fail; L3 recovery without relapse. 3. Tension: retry hard against stay fair; resolved by a budget per endpoint. 4. M1 outbox · M2 log · M3 queue per endpoint with a cap · M4 full jitter, breaker, ramp · M5 consumer contract · M6 egress proxy; the mechanisms-at-work table; badges on the container view (`th-where`); one protocol sequence (`seq-th-claim`). 5. Options: inline · shared queue · partition/retry topic per endpoint · **log + delivery rows by endpoint (pick; gives up write amplification)** · managed push pub/sub · buy (honest equal). 6. Failure catalogue → the seven challenges.

## 4 · API and entities

Register (FR1) · the delivery on the wire with `Webhook-Id`, `Webhook-Timestamp`, `Webhook-Signature`, per-loan `sequence` (FR3) · logs, redeliver, replay with `since`, `rate`, `mode` (FR4). Chen: merchant, endpoint, subscription, event, delivery, attempt. Physical: `delivery(endpoint_id SK, event_id UQ*, state, attempt_no, next_attempt_at IX partial, lease_until)`; attempts by day.

## 5 · High-level design

| Version | Adds | Objection it answers | Objection it leaves |
|---|---|---|---|
| V1 | POST inside the request | — | 30 s till; crash loses; rollback lies |
| V2 | outbox, relay, log, dispatcher | lost or false events | one slow till holds the pool; retries in memory; no record |
| V3 | fan-out, delivery store (rows by endpoint, claim under cap, lease), attempt log, API | head-of-line; retries in memory; visibility | recovery, trust, contract |
| V4 (C3) | endpoint health: breaker, ramp, disable | recovery herd | — |
| V5 (C5) | egress proxy; signing | SSRF, forgery | — |
| V6 (C6) | contract renderer + schema registry | producers breaking merchants | — |

Canonical plan: baseline `basesvg` (U-shaped spine), drawn once at V1→V3 and then as deltas (`base-v4/5/6` with `new=`); container view (`c4svg`, `since=`) at V3, then with technologies (V4–V6 marked NEW); component views of the dispatcher and fan-out carry challenges 2, 3, 5 and 4, 6. Numbered flows FR2 and FR3; sequences FR1–FR4.

## 5.1 · Components and technologies

<!-- stack:outline -->

| Container | Choice | How it is built | Rejected | Theory part |
|---|---|---|---|---|
| Outbox relay | An outbox table in each producer's PostgreSQL, drained by a Go poller in ID order | The producer inserts the outbox row in the same transaction as the change | A dual write: commit, then publish to Kafka; Change data capture with Debezium | 08 10 |
| Event log | Kafka, domain topics keyed by loan ID, seven days of retention | One topic per domain, keyed by loan ID, so one loan's events stay in commit order | Amazon SQS as the backbone; RabbitMQ | 10 |
| Fan-out | A Go consumer group with an in-memory subscription cache, writing delivery rows in batches | Each consumer matches events to subscriptions from an in-memory cache and inserts one delivery row per match, in batches, unique on event and endpoint | One Kafka topic per endpoint; Filtering inside every dispatcher | 10 |
| Delivery store | PostgreSQL sharded by endpoint ID; claim with SKIP LOCKED and a lease; next_attempt_at is the timer | A row per delivery, on the shard that owns its endpoint, with its state, next attempt time and lease | Kafka retry topics; An SQS queue per endpoint | 08 06 |
| Dispatcher | Go workers: a concurrency cap per endpoint, pools per merchant tier, a breaker per endpoint | Workers claim only for endpoints under their in-flight cap, ten by default, in pools split by merchant tier | One shared worker pool with retries; A thread pool per endpoint | 13 12 |
| Egress proxy | Smokescreen, an open-source egress proxy, in front of every dispatcher | The proxy resolves the name itself, refuses private, loopback, link-local and metadata addresses, and connects to the address it checked | Checking the URL at registration only; A firewall allow-list of merchant addresses | 16 |
| Attempt log | PostgreSQL partitioned by day, then object storage; read by the merchant dashboard | One row per attempt: status, latency, the first bytes of the answer, the error class | Elasticsearch; ClickHouse | 14 07 |
| Contract renderer | A schema registry of public event versions, rendered at fan-out for each endpoint's pinned version | Each endpoint is pinned to a dated public version; fan-out renders the internal event into it from a registry of every supported version | Sending the internal event as it is; One public payload forever | 11 16 |

Fix-slide rejections: 1: A dual write: commit, then publish; 2: A Kafka partition, or retry topics, per endpoint; 3: A fixed retry count every ten seconds; 4: An exactly-once, ordered delivery promise; 5: Checking the URL string at registration; 6: Sending the producers' internal events as they are; 7: Alerting on merchants' error rates.

<!-- /stack:outline -->

Drill interlude: outbox relay, fan-out, delivery store, dispatcher, egress proxy.

## 5.2 · The alternate path

Buy the delivery engine (a managed webhook service) and keep the outbox, log, fan-out and contract. Gives up: data leaves (the partner bank's vendor review), caps and tiers are the vendor's, cost per message. Crossover: 180 M × $0.10/1,000 ≈ $18k a month against ≈ $80k for a team of three; build past ≈ 800 M a month or when data must stay.

## 7 · Challenges

| # | Challenge | Fix one level down | Version | Rejected |
|---|---|---|---|---|
| 1 | Why not publish after the commit? | outbox row in the commit; relay publishes, waits for acks, then marks; consumers de-duplicate | — (V2 drilled) | dual write |
| 2 | One slow endpoint (crux 1) | claim where in_flight < cap, counter in the same commits; tier pools; breaker; caps from Little's law; batching for the bank | — | partition / retry topic per endpoint |
| 3 | Down two days, then back (crux 2) | full jitter capped at 1 h for 72 h; breaker pauses; probe; ramp ×2 per clean minute; disable and email; latest-per-loan replay | V4 | fixed retry count |
| 4 | Twice, and out of order | event ID kept 7 days; per-loan sequence from the loan's version in the outbox; thin events; ordered mode costs throughput | — | exactly-once, ordered promise |
| 5 | Hostile URLs, forged calls | egress proxy resolves and connects to the checked IP; HMAC over id.t.body, 5 min; rotation with overlap; GET before releasing goods | V5 | URL check at registration |
| 6 | A producer changes the payload (SD-59 overlay) | pinned dated versions; renderer; golden examples fail the producer's build; 12 months; the integrations team owns the seam | V6 | internal event as the contract |
| 7 | "You never sent it" | attempts in the merchant's dashboard; health emails; SLIs we own; symptom pairs; debuggable signatures | — | alerting on merchants' errors |

## 8 · Build cost (AUX)

Releases V2–V6 with people and quarters; contracts between teams (producers, integrations, platform); buy against build; on-call; top risks.

## 9 · Recap

The final view as a numbered flow; seven paths in one sentence each; common mistakes; the thesis.

## Canon check

| Canonical point | Covered at |
|---|---|
| Asynchronous delivery through a queue | V2–V3 |
| Retries with exponential backoff and jitter | M4; challenge 3 |
| Idempotency and event IDs | M5; challenge 4 |
| Signatures, secrets and rotation | M5; challenge 5 |
| Dead letters and disabling endpoints | challenge 3 |
| Isolation per subscriber | M3; challenge 2 |
| Replay and redelivery API | FR4; challenge 3 |
| Ordering | challenge 4 |
| SSRF | M6; challenge 5 |
| Customer-facing delivery logs | FR4; challenge 7 |
| Payload versioning | challenge 6; build cost |
| Multi-region | dismissed aloud (one region first); booklet Stage 7 |
| Buy a managed service | 5.2; build cost |

## From the old version (the 2026-11 compact outline)

| Reused | New | Dropped |
|---|---|---|
| thesis, definition, mechanisms M1–M6, options matrix, challenges 1–5 and 7 in substance | re-anchored on lending (SD-82/SD-95 events, partner bank, a forged approval releasing goods); scale line from the settlement-file peak; challenge 6 (contract and team seams, the SD-59 overlay); V4–V6; buy as the alternate path; build cost restored; component views | compact cut; the generic 900 M-events scale line; the "outbox is the delivery table" alternate path |

## Budget (measured after the build)

Recorded in `README.md`.
