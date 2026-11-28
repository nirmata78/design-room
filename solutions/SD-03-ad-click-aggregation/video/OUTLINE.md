# SD-03 · Event counting & billing rollups — reference-solution outline (six-chapter, C4-first format)

Target level: staff · Format: GUIDELINES 2026-11-28 (issue #5 pilot) · Target 45–60 min · Word budget 6,000–7,500 · 6 challenges.
The slides and narration are `src/*.py`; the C4 views are `../workspace.dsl` + `../views.json`; the technologies `../stack.json`.

## Thesis and hook

- **Thesis** (key line): *Count once, from one log, with one piece of code run twice: fast and provisional for the dashboard,
  exact and pinned for the bill. Never increment a number you can recompute: replace it.*
- **Hook**: one hour of one campaign has three numbers — live at +10 s, final at +48 h, corrected at +9 days (figure `tension`).

## Scale line

Volume per month: **25 T impressions, 250 B clicks** (1 % CTR) · Retention: raw events **6 months** (≈ 150 T), aggregates 7 years ·
Peak: **30 M events/s** in the evening (3 × the 10 M/s average), and **one ad at 2 M impressions/s** in a sports break.

## 1 · Prompt, clarifying Q&A and C4 context

- **Graded**: requirements (which numbers are money) · correctness (IDs at the source, event time, replace) · trade-offs (one code
  run twice) · depth (watermarks, keyed state, two-stage sums, pinned re-runs) · operations (conservation, live vs final, canaries).
- **Clarifying** (5): freshness (10 s live, hourly bill final in 2 days) · exactness (bill exact, dashboard converges) · duplicates
  and lateness (SDK retries, offline phones, skewed clocks) · fraud (separate, can invalidate after invoices) · retention (6 months
  raw, 90-day disputes, 7 years aggregates, re-runs give the same numbers).
- **FR1** record · **FR2** live within 10 s · **FR3** exact hourly bill, versioned · **FR4** corrections as versions and adjustments.
- **NFRs**: 30 M/s ingest, ack p99 50 ms · live p99 10 s · bill final at H + 48 h, re-run bit for bit · 99.99 % ingest · zone loss.
- **Properties**: `S1-count-once` · `S2-right-hour-right-version` · `S3-reproducible` · `L1-final-in-48h` · `L2-fresh-in-10s`.
- **Out of scope**: fraud detection, ad serving, budget pacing (a consumer of live counts), invoicing, attribution.
- **C4 context**: ad clients → system (HTTPS) · advertiser → system (HTTPS) · fraud system → system (event) · invoicing ← final hours (batch).
- **The core**: an idempotent durable intake; one aggregation run twice; versioned final hours with a correction path.

## 2 · Back-of-the-envelope

| Number | From | Arithmetic | Constraint it forces |
|---|---|---|---|
| Events | volume | 2.5 × 10¹³ ÷ 2.6 × 10⁶ s ≈ 10 M/s; × 3 = 30 M/s | no write per event: a partitioned log |
| Clicks | volume | ≈ 100 k/s, 300 k/s peak | same pipeline; billable click keyed by impression |
| Bandwidth | peak | 30 M × 200 B = 6 GB/s, 18 GB/s replicated | ~1,024 partitions, ~80 brokers |
| Log, 3 days | average | ≈ 390 TB compressed and replicated | older replays read the lake |
| Lake | volume, retention | 0.6 PB/month, 3.8 PB | object storage by event hour |
| Dedup state | peak | 1.8 × 10¹⁰ IDs × 40 B ≈ 0.7 TB | keyed state over 512 tasks, not Redis |
| Hot ad | peak | 2 M/s on one key vs ~300 k/s per task | combine before the shuffle |
| Duplicates | clicks | 0.3 % retried ≈ $375 M/month | dedup is the crux |
| Freshness budget | NFR | 1 + 0.5 + 2 + 1 + 1 = 5.5 s of 10 | early firings every 2 s |

## 3 · API and data model

`POST /v1/events` (FR1; `event_id` UUIDv7 minted at the source, `impression_id`, `client_ts`; 202 after the log ack) ·
`GET …/live` (FR2, `provisional`) · `GET /v1/billing/hours` (FR3, `version`, `manifest_id`) · `POST /v1/invalidations` (FR4).
Tables: events (Iceberg, by event hour) · billing_hour (campaign, ad, hour, version) · manifest · live_minute (ClickHouse, by
version) · invalidation · adjustment. Lifecycle of a billing hour: open → final v1 → dirty → final v + 1 (`state-hour`).

## 4 · The design, driven by challenges

**V1** (`v1`): ad clients → collector → event log → event lake → billing job → billing tables → reporting API → advertiser. Exact,
hourly. Flow `flow-v1`. Tech cards: event log (Kafka), event lake (Iceberg).

| # | Challenge | Break | Mechanism | Fix (view) | Rejected | Version | Push → second fix |
|:-:|---|---|---|---|---|---|---|
| 1 | Advertisers need 10 s | `v1-break` (billing job hourly) | M1 one aggregation, run twice; options A–E | `v2` + `flow-live`; tech: Flink | — | **V2** | "make the stream the bill?" → state TTL, cutoff, reproducibility |
| 2 | The same click, three times | `dd-break` | M2 idempotency by event ID; `seq-retry` | `dd-fix`; tech: collector | Kafka EOS | zoom | replay four hours → `replay-fix` (replace by key and version) |
| 3 | Yesterday's events at 6 a.m. | `late-break` | M3 event time, watermarks; `seq-watermark` | `late-fix`, pseudocode, `close-fix` | processing-time windows | zoom | quiet partition, bad SDK clock → idle timeout, clamp alert |
| 4 | One ad at 2 M/s | `hot-break` | M4 two-stage aggregation; `combiner` | `hot-fix`; tech: ClickHouse | Redis INCRBY | zoom | 500 hot ads → bounded by active keys |
| 5 | Fraud after the invoice | `v3`, `fraud-break` | versions + adjustments | `fraud-fix`, pseudocode, `state-hour` | update in place | **V3** | 7-month-old invalidation → a contract, refused and logged |
| 6 | "Your numbers are 3 % high" | trace | conservation, live vs final, canaries | `recon-fix`, cards, symptom pairs | lag/CPU dashboards | zoom | the reconciler wrong → canaries check the checker |

## 5 · When you don't need all this

One ClickHouse cluster (`alt`, ALTERNATE): insert dedup token, materialised minutes, nightly billing query. Gives up: no
independent log, ingest contention, corrections as mutations, eventual dedup. **Crossover**: ~20 nodes take 1–2 M rows/s; we
average 10 M/s; below ~200,000 events/s ship the one-cluster version.

## 6 · Recap

`recap` badges: stream `M1 M2 M4 M5` · live `M3 · replace` · batch `M1 M2 M3` · bill `versions` · api `provisional | final`.
Stack table from `stack.json`; six mistakes; five follow-ups (reach via HyperLogLog, second region, a country dimension, 30-day
retention, 1-second pacing numbers).

## C4 plan

| View key | From | Overlays | Used on |
|---|---|---|---|
| c4-context | exported | steps | ch1 |
| containers | exported (master, grid 3 × 5) | — | Markdown only |
| v1 · flow-v1 · v1-break | containers | hide stream, live, fraud · flow · breaks batch | ch4 |
| v2 · flow-live | containers | hide fraud · new stream, live · flow | ch4.1 |
| v3 | containers | new fraud | ch4.5 |
| comp-stream | exported (grid 3 × 4, 5 grouped steps) | — | ch4.2, shown whole before the first zoom |
| comp-billing | exported (grid 4 × 5, 4 grouped steps) | — | ch4.3, shown whole before the first zoom |
| dd-break · dd-fix · replay-fix · late-break · late-fix · hot-break · hot-fix | comp-stream | keep (rest dimmed) + breaks / fix, via zoom() | ch4.2–4.4 |
| close-fix · fraud-break · fraud-fix · recon-fix | comp-billing | keep (rest dimmed) + breaks / fix, via zoom() | ch4.3, 4.5, 4.6 |
| recap | containers | badges | ch6 |
| alt | exported | alternate live | ch5 |

## Canon check

| Canonical point | Covered at, or dismissed because |
|---|---|
| Durable log before aggregation | V1, ch 4 |
| Idempotency key / dedup window | challenge 2 |
| Event time, watermarks, late data | challenge 3 |
| Lambda against Kappa | challenge 1 options matrix |
| Exactly-once is not end-to-end | challenge 2 and its push |
| Hot keys / sharded counters | challenge 4 |
| HyperLogLog for uniques | recap follow-up; reach on the dashboard only |
| Reconciliation between paths | challenge 6 |
| Retroactive invalidation | challenge 5 |
| Reproducible history | challenge 1 push, challenge 5 pseudocode |
| Click fraud detection itself | dismissed aloud: out of scope, a separate system |
| Ad serving, auctions, budget pacing | dismissed aloud; pacing named as a consumer of live counts |

## Budget (measured by gen.py, 2026-11-28, after the C4 restyle)

| Chapter | Words |
|---|---|
| 1 · Prompt + context | 1,009 |
| 2 · Estimates | 450 |
| 3 · API + data | 416 |
| 4 · Design + challenges | 4,196 |
| 5 · Alternate | 181 |
| 6 · Recap | 465 |
| **Total** | **6,717** (≈ 56 min), **114** logical slides |

Chapter 4 grew by two component-view slides and one card slide per zoom (the picture full frame, then its explanation at reading
size); no narration was cut for time.
