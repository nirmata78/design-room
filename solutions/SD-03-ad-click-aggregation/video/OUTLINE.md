# SD-03 · Event counting & billing rollups — reference-solution video outline

Target level: staff (manager layer dropped: compact cut) · **Compact cut** (GUIDELINES §3.4): target 65–75 min · Word budget
≈ 7,600 · 6 challenges · no build-cost chapter, no drill interlude.

## Thesis and definition

- **Thesis** (key line): *Count once, from one log, with one piece of code run twice: fast and provisional for the dashboard,
  exact and pinned for the bill. Never increment a number that can be recomputed; replace it.*
- **Definition**: an event-counting system accepts impression and click events at the rate they happen, shows advertisers live
  counts within seconds, and produces exact, reproducible hourly totals that invoices are built on, including corrections that
  arrive after the invoice.
- **Hook**: "count clicks" sounds like `n = n + 1`. At 30 million events a second, with retries, phones that were offline for a
  day and a fraud team that changes its mind a week later, the hard part is not counting fast: it is counting *once*, in the
  *right hour*, and being able to show *which events* make up an invoice line.

## Scale line (GUIDELINES §3.1)

Volume per month: **25 trillion impressions and 250 billion clicks** (1 % click-through) · Retention: raw events **6 months**
(≈ 150 trillion), aggregates 7 years · Peak: **30 million events a second** in the evening (3 × the 10 M/s average), and **one
prime-time ad at 2 million impressions a second** during a sports break.

Every estimate starts from one of these three: the monthly volumes, the 6-month retention, the evening peak or the hot ad.

## 0 · What this question grades

| Axis | Weak signal | Strong signal |
|---|---|---|
| Requirements | "Count clicks", no split between live and billed | Asks which numbers are money, how late events arrive, who can invalidate them |
| Correctness | `UPDATE … n = n + 1`; "exactly-once" by name | Event IDs minted at the source; dedup; event time; replace, never increment |
| Trade-offs | Lambda or Kappa recited | One aggregation code run twice; says what each run gives up |
| Depth | Stops at "Kafka and Flink" | Watermarks, keyed state with a TTL, two-stage aggregation, snapshot-pinned re-runs |
| Operations | CPU and consumer lag | Conservation checks, live-versus-final reconciliation, canary events, an audit trail per invoice line |

## 1 · Requirements and scope

Clarifying questions (6), interviewer answers:
1. Volume → the scale line.
2. Freshness → dashboards within 10 s; sub-second only for one headline number, not slice-and-dice. Billing: hourly totals,
   final within two days.
3. Exactness → the bill is exact and auditable; the dashboard may be slightly off but converges to the bill.
4. Duplicates and late data → SDKs retry; offline phones flush hours or days late; client clocks are skewed.
5. Fraud → a separate system; it can invalidate events after invoices are sent; we apply the corrections.
6. Retention and audits → raw 6 months (dispute window 90 days), aggregates 7 years; re-running a day must give the same numbers.

FRs: **FR1 Record** (accept events, acknowledge once durable, idempotent on retry) · **FR2 Live** (per ad and campaign:
impressions, clicks, spend, approximate unique reach, within 10 s) · **FR3 Bill** (exact hourly totals per campaign and ad,
final at the cutoff, versioned, exported) · **FR4 Correct** (late events and invalidations reach closed hours as new versions
and adjustment lines; a sent invoice is never edited).

NFRs (initial targets): ingest 30 M events/s peak, ack p99 50 ms; live freshness p99 10 s, dashboard query p99 1 s; bill final
at H + 48 h, reproducible bit for bit; an acknowledged event survives a zone loss; ingest availability 99.99 %, dashboards 99.9 %.

IN: ingest, dedup, live counts, unique reach (approximate), hourly billing totals, versions, corrections, audit trail,
reconciliation. OUT, on purpose: fraud detection itself, ad serving and auctions, budget pacing (a consumer of the live counts),
invoicing and payments, conversion attribution, advertiser accounts.

Core (key line): *three things — an idempotent, durable intake; one aggregation run twice; versioned final hours with a correction path.*

C4 context: ad clients (SDKs, browsers, ad servers) → system; advertiser ↔ system; fraud system → system; system → invoicing.

## 2 · Estimates

| Number | From (scale line) | Arithmetic | Label | Decision it drives |
|---|---|---|---|---|
| Events/s | monthly volume | 2.5 × 10¹³ ÷ 2.6 × 10⁶ s ≈ 10 M/s; peak × 3 = 30 M/s = 1.8 B a minute | derived | a partitioned log; stateless collectors; no write per event to a database |
| Clicks/s | monthly volume | 2.5 × 10¹¹ ÷ 2.6 × 10⁶ ≈ 100 k/s, peak 300 k/s | derived | clicks ride the same pipeline; the billable-click key is the impression ID |
| Ingest bandwidth | peak | 30 M × 200 B = 6 GB/s; × 3 replicas = 18 GB/s of broker writes | illustrative | 1,024 partitions; about 80 brokers |
| Broker disk, 3 days | average | 2 GB/s × 259,200 s ≈ 520 TB; ÷ 4 compression ≈ 130 TB; × 3 ≈ 390 TB | illustrative | brokers keep 3 days; older replays read the lake |
| Lake | monthly volume, retention | 2.5 × 10¹³ × 25 B ≈ 0.6 PB a month; × 6 ≈ 3.8 PB | illustrative | object storage, partitioned by event hour |
| Dedup state | peak | 30 M/s × 600 s = 1.8 × 10¹⁰ IDs × 40 B ≈ 0.7 TB | illustrative | keyed state over 512 subtasks (~1.4 GB each), not one Redis set |
| Hot ad | hot ad | 2 M/s on one key against ~300 k updates/s for one subtask | illustrative | combine before the shuffle: 512 partial sums a second |
| Money in duplicates | monthly clicks | 0.3 % retried × 2.5 × 10¹¹ = 7.5 × 10⁸ clicks × $0.50 ≈ $375 M a month | illustrative | dedup is the crux, not an optimisation |
| Freshness budget | NFR | SDK 1 s + collector and log 0.3 s + early firing 2 s + insert 1 s + query 1 s ≈ 5.3 s of 10 | target | early firings every 2 s; batches of a second |

## 3 · Theory (compact: 6 parts, 5 mechanisms, one sequence)

1. Is: counting events that are money, so each must be counted once, in its hour, reproducibly. Is not: metrics monitoring
   (approximate is fine; SD-04), analytics uniques (SD-01), a ledger of transfers (SD-44: balances, not counts).
2. Safety: S1 an accepted event is never lost and never billed twice; S2 an event is billed in the hour it happened, and not at
   all once invalidated, without editing a sent invoice; S3 every billed number can be reproduced and traced to its events.
   Liveness: L1 every accepted event reaches a final hour (or an adjustment) within 48 h plus the run; L2 live counts within 10 s.
3. Tension: freshness against exactness; one hour's number, three times (figure `tension`).
4. Mechanisms (property → how → rules out → costs):

   | Mechanism | Protects | Rules out | Costs |
   |---|---|---|---|
   | M1 Idempotency by event ID | S1 | a retry counted twice | an ID minted upstream; state per ID for the window |
   | M2 Event time with watermarks | S2, L2 | late events in the wrong hour | waiting; open-window state; a cutoff |
   | M3 Deterministic re-run over an immutable log; replace, never increment | S1, S3 | double counting on replay; irreproducible invoices | raw retention; computing twice |
   | M4 Two-stage aggregation (sharded counters) | L2 under skew | one hot key stalling the job | one more stage; a sum on read |
   | M5 Mergeable sketches (HyperLogLog) | L2 for reach | exact distinct counts at this scale | ~1.6 % error; never on the bill |

5. Options matrix: A counter per event in a database · B batch only · C stream only (Kappa, the stream result is the bill) ·
   D Lambda, two codebases · **E one aggregation code run twice (Kappa in code, Lambda in time)**. Pick E; gives up: compute twice,
   the bill lags 48 h.
   Mechanisms at work: a table (mechanism · container · clause); badges M1–M6 on the canonical view return in the recap.
   One sequence at protocol level: `seq-th-watermark` (watermark, early firing, on-time firing, a late update by version).
6. Failure catalogue → challenges: retries (1), late and skewed events (2), a hot ad (3), crash and replay (4), corrections after
   invoicing (5), a wrong number nobody notices (6).

## 4 · API and entities

| API | Serves | Reads / writes | Wire-format notes |
|---|---|---|---|
| `POST /v1/events` | FR1 | writes EVENT | batch ≤ 500; `event_id` UUIDv7 minted at creation; `202` only after the log ack |
| `GET /v1/campaigns/{id}/live?step=1m` | FR2 | reads live minutes | `asOf`, `provisional: true` |
| `GET /v1/billing/hours?advertiser=&month=` | FR3 | reads HOUR TOTAL | `version`, `manifest_id`, `final: true` |
| `POST /v1/invalidations` (fraud) | FR4 | writes INVALIDATION | event IDs with their hours, a reason, the rule version |

Entities: ADVERTISER 1:N CAMPAIGN 1:N AD 1:N EVENT; EVENT N:1 HOUR TOTAL (weak: hour, version); CAMPAIGN billed as HOUR TOTAL;
INVALIDATION voids EVENT. Physical: `events` (Iceberg, by event hour), `billing_hour` (PK campaign, ad, hour, version),
`manifest`, `live_minute` (ClickHouse ReplacingMergeTree), `invalidation` (append-only), `adjustment`.

## 5 · High-level design

| Version | Adds | Objection it answers | Objection it leaves |
|---|---|---|---|
| V1 | collector, event log, event lake, billing job, billing tables, reporting API | (simplest correct thing: exact, from a log) | the dashboard is a day behind |
| V2 | live aggregator, live store (final hours loaded into it; the API reads one store) | freshness | the bill must be final while late events and invalidations keep arriving |
| V3 | fraud system → invalidations; invoicing; versioned hours | corrections without editing invoices | a wrong number that nobody notices |
| V4 (challenge 6) | reconciler | detection | — |

Spine: clients → collector → log → (top) live aggregator → live store ← API ← advertiser; (bottom) lake → billing job →
billing tables → invoicing. Canonical diagram plan:

| Slide | Canonical diagram | Delta |
|---|---|---|
| v1 | containers | `upto=1` (the one full drawing) |
| v2, v3 | containers | `new=2`, `new=3` |
| container walk | containers | the V3 slide's narration walks it; no second drawing |
| flow-live, flow-bill | containers | `flow=` |
| 5.1 technologies | containers | `focus=` on the seven in-scope boxes, type lines from `stack.json` |
| alternate path | containers | `attack=` on lake, billing job, billing tables (what goes away) |
| bridge map | containers | `attack=` one box per challenge |
| challenges 1–4 | component: live aggregator | `keep=` + `attack=` / `fix=` |
| challenges 2, 4, 5 | component: billing job | `keep=` + `fix=` |
| challenge 6 | containers | `attack=` api, then V4 `new=4` |
| recap | containers | V4 with `badges=` |

Sequences, one per FR: `seq-ingest`, `seq-live`, `seq-bill`, `seq-correct`. Numbered flows for the two core paths only (compact cut).

## 5.1 · Components and technologies

Component views: live aggregator (source, time assigner, deduplicator, combiner, window counter, late output, reach sketch, sink;
checkpoints) and billing job (hour closer, reader, exact dedup, invalid filter, price + sum, writer, adjuster).

<!-- stack:outline -->

| Container | Choice | How it is built | Rejected | Theory part |
|---|---|---|---|---|
| Collector | Go on Kubernetes, behind an L4 load balancer | Batches of up to 500 events, produced to Kafka with `acks=all` and the idempotent producer; `202` only after the ack | Warehouse streaming inserts; Access logs shipped by an agent | 11 §11.10, 12 §12.5 |
| Event log | Kafka, 1,024 partitions, RF 3 over 3 zones | Topic `events.raw`: partition = hash(event ID) mod 1,024, RF 3 over three zones, `min.insync.replicas=2` | Google Pub/Sub; Amazon Kinesis | 10 §10.2–10.5 |
| Live aggregator | Apache Flink, 512 subtasks, RocksDB state | Dedup keyed by event ID (TTL 10 min), a per-subtask combiner flushed every second, then ad × minute windows: early results every 2 s, final on the watermark | Kafka Streams; Spark Structured Streaming | 10 §10.11–10.13 |
| Live store | ClickHouse, ReplacingMergeTree, 2 replicas a shard | `live_minute ORDER BY (campaign_id, ad_id, minute, shard)` with a `version` column, inserted in batches | Apache Druid / Pinot; Redis counters | 14 §14.9, 8 §8.10 |
| Event lake and billing tables | Apache Iceberg on GCS, Parquet + zstd | `events` partitioned by event hour, 0.6 PB a month | Plain Parquet folders; Delta Lake | 7 §7.7, 10 §10.13 |

Fix-slide rejections: 1: Kafka exactly-once (idempotent producer and transactions); 2: Processing-time windows; 3: Redis INCRBY on one counter key; 4: Flink's two-phase-commit sink alone; 5: Updating billed rows in place; 6: Lag and CPU dashboards.

<!-- /stack:outline -->

No drill interlude (compact cut); the booklet keeps the probes.

## 5.2 · When you don't need all this (alternate path)

Simpler design: **one ClickHouse cluster** as buffer, truth and dashboard. Collectors insert batches with an
`insert_deduplication_token`; a materialised view keeps minute rollups; billing is a nightly `INSERT … SELECT` over the
`ReplacingMergeTree` table of events (deduplicated by event ID with `FINAL`). Gives up: an independent replayable log (the table is
the only copy), isolation (a heavy query slows ingest), corrections become mutations, and dedup is eventual (merges).
Crossover: one cluster of about twenty nodes takes on the order of 1–2 M rows a second; the scale line's average is 10 M/s, so
we are past it by an order of magnitude. Below about **200,000 events a second**, with room to spare, I'd ship the one-box version.

## 7 · Challenges

### Challenge 1 · The same click, three times (correctness, crux)
- Q: A retrying client sends the same click three times, two seconds apart. Walk me through it.
- Naive: "Kafka has exactly-once." · Case: batch B17, 202 lost on a cell network, offsets 81,220 and 81,977; 0.3 % retries ≈ $375 M a month.
- Break: the deduplicator does not exist (live aggregator component view, `attack=dedup`).
- Fix: dedup by the event ID minted at creation: Flink keyed state, TTL 10 min, in RocksDB, checkpointed with the offsets; the
  billing job keeps the first row per ID in the hour; the billable click is keyed by impression ID. One level down: covers retries
  of the same event; does not cover a client minting new IDs (that's fraud's job) — sequence `seq-ch1-retry`. Version: no change.
- Rejected: Kafka exactly-once (transactions) — producer-session retries only. · Why: S1 by construction, cost 0.7 TB of state.
- If the fix fails: the job restarts → state restored with the offsets; a retry after 10 min → only the live view double counts,
  and the bill does not, because its dedup covers the whole hour.
- If asked: "Every event carries an ID minted where it happened; I drop repeats in keyed state for ten minutes on the live path and
  over the whole hour on the billing run. Exactly-once is not a broker setting; it is at-least-once plus that dedup."

### Challenge 2 · Yesterday's events at 6 a.m. (correctness)
- Q: A phone was offline overnight; 300 impressions from Tuesday 21:00–23:40 land Wednesday 06:00. Which hour is billed?
- Naive: count when it arrives. Case: Tuesday's hour short by 300, Wednesday's 06:00 over; the campaign ended Tuesday → billed
  outside its flight dates; a skewed clock says 2031.
- Break: the time assigner uses arrival time (`attack=time`).
- Fix: event time from the client, clamped to [server − 72 h, server + 5 min]; watermark = min over partitions(latest − 2 min);
  allowed lateness 1 h for the live view; the bill closes hour H at H + 48 h from a snapshot of every file in that hour's
  partition (billing component view `ch2-close`). Pseudocode with key lines. Later than the cutoff → a new version (challenge 5).
  Version: no change.
- Rejected: processing-time windows. · Why: S2.
- If the fix fails: a partition goes idle → idle timeout 30 s; the clamp is attacked → flagged events, counted as server time, a rule for fraud.
- If asked: "The event's own time decides its hour, clamped against server time. The live view waits two minutes and accepts an hour of
  lateness; the bill closes at forty-eight hours from a snapshot, and anything later becomes a new version, not an edit."

### Challenge 3 · One ad at 2 million a second (overload)
- Q: A sports break puts one ad on every screen: 2 million impressions a second. What happens to your job?
- Naive: key by ad, add machines. Case: one subtask at 100 %, backpressure, lag on all partitions: every dashboard stale.
- Break: the window counter keyed by ad (`attack=win`).
- Fix: combine in each of 512 subtasks for 1 s, then merge by (ad, minute) → 512 updates a second; the live store keeps up to 16
  shard rows per ad-minute, summed on read (a sharded counter). Figure `combiner`, pseudocode. Version: no change.
- Rejected: Redis `INCRBY` on one key. · Why: L2 under skew; the log is keyed by event ID so no partition is hot.
- If the fix fails: 500 ads hot at once → the combiner's map is bounded per second (one entry per active ad); honest limit: the
  merge stage scales with active keys, not events.
- If asked: "A hot key is a hot thread. I sum where the events already are, once a second, and merge 512 partials; on the read side
  the counter is sharded and summed."

### Challenge 4 · Crash and replay four hours (failure recovery, crux)
- Q: Your stream job had a bug; you redeploy and replay from 10:00. Is anyone double-billed?
- Naive: "Flink is exactly-once." Case: sink did `+=`; minutes 10:00–14:00 doubled on the dashboard; a billing job that adds to the
  previous run doubles the bill.
- Break: the store sink increments (`attack=sink`).
- Fix: every output is a replacement by key: ClickHouse rows by (ad, minute, shard) with a higher version; billing hours replaced
  as a partition commit; the billing run is a pure function of its manifest (snapshot, rate card, invalidation list, image digest).
  Sequence `seq-ch4-replay`; billing component view `ch4-rerun`. Version: no change.
- Rejected: Flink's two-phase-commit sink alone. · Why: S1 and S3.
- If the fix fails: Finance asks for March re-run, bit-identical, two years later → the manifest; no wall clock, integer micros,
  sort before reduce.
- If asked: "I never increment a number I can recompute. Live minutes and billing hours are written as replacements keyed by what
  they count, and a billing run is a pure function of a pinned manifest, so a replay is a no-op on the bill."

### Challenge 5 · Fraud after the invoice (correctness)
- Q: Nine days after invoices went out, fraud invalidates 2 % of October's clicks for one advertiser. What happens?
- Naive: delete the rows, re-send the invoice. Case: 3.1 M clicks, $1.55 M; the invoice no longer matches anything stored.
- Break: the writer edits billed rows (billing component view, `attack=write`).
- Fix: invalidations are an append-only topic; the closer marks the affected hours dirty; each is re-run as version n + 1 (the
  old version stays); the adjuster sends version n + 1 minus the invoiced version as an adjustment line. V3 already holds the boxes;
  the fix is the version rule. Pseudocode. Version: no change.
- Rejected: updating billed rows in place. · Why: S2 and S3.
- If the fix fails: an invalidation for an event older than raw retention → refused by contract (90-day dispute window, 6 months of raw).
- If asked: "Nothing billed is ever edited. A correction re-runs the hour as a new version, and the difference to what was invoiced
  becomes an adjustment line, so every invoice still matches a stored version."

### Challenge 6 · "Our numbers are 3 % higher than theirs" (observability)
- Q: An advertiser says our clicks are 3 % higher than their logs. And how would you have known first?
- Naive: CPU, lag and error dashboards. Case: all green while a dedup TTL set to 10 s lets retries through: live +3 %, bill fine.
- Break: the container view, `attack=api`.
- Fix: V4 adds the reconciler: conservation per hop (accepted = appended = landed − duplicates), live against final per hour
  (alert above 0.5 %), canary events with known IDs every minute (expected exactly once in both), and the audit trail per invoice
  line (line → hour version → manifest → event IDs, exportable). Symptom-pair table.
- Rejected: lag and CPU dashboards. · Why: S3, made operational.
- If the fix fails: the reconciler itself is wrong → it is checked by the canaries; an alert with nothing to compare means the check is down.
- If asked: "I'd answer the advertiser with the event IDs behind their line. And I'd have seen it first: conservation checks at every
  hop, live against final every hour, and canary events whose count I know."

## 9 · Recap (chapter 8 in the compact cut)

V4 with badges; one sentence per path (record, live, bill, correct); common mistakes (increment per event; "exactly-once" by name;
processing time; one path for both; editing billed rows; no way to show the events behind a line); thesis.

## Canon check

| Canonical point | Source | Covered at, or dismissed because |
|---|---|---|
| Durable log before aggregation | common treatments | V1, ch 5 |
| Idempotency key / dedup window | common | challenge 1 |
| Event time, watermarks, late data | common | theory M2, challenge 2 |
| Lambda against Kappa | common | theory options matrix |
| Exactly-once is not end-to-end | common | challenge 1, challenge 4 |
| Hot keys / sharded counters | common (Google phrasing) | theory M4, challenge 3 |
| HyperLogLog for uniques | common | theory M5; reach on the dashboard only |
| Reconciliation between paths | common | challenge 6 |
| Retroactive invalidation | cue sheet | challenge 5 |
| Reproducible history | cue sheet curveball | challenge 4 second push |
| Click fraud detection itself | common | dismissed aloud: out of scope, a separate system |
| Ad serving, auctions, budget pacing | common | dismissed aloud: out of scope; pacing named as a consumer of live counts |
| Build cost and team | template | dismissed: compact cut, no AUX chapter |

## Budget

| Chapter | Minutes | Words | Slides |
|---|---|---|---|
| 0 Cold open | 3 | 350 | 5 |
| 1 Requirements | 7 | 800 | 12 |
| 2 Estimates | 5 | 550 | 5 |
| 3 Theory | 8 | 1,050 | 12 |
| 4 API and data | 4 | 450 | 5 |
| 5 Design | 8 | 950 | 10 |
| 5.1 Technologies | 6 | 650 | 9 |
| 5.2 Alternate | 2 | 250 | 2 |
| 6 Bridge | 1 | 130 | 2 |
| 7 Challenges (6) | 26 | 2,500 | 48 |
| 8 Recap | 3 | 300 | 4 |
| **Total** | **≈ 73** | **≈ 7,980** | **≈ 114** |
