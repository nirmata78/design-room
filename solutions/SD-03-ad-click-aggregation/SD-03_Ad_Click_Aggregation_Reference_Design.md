---
title: "SD-03 · Event Counting and Billing Rollups"
subtitle: "A reference solution for a system design round at the Staff bar: ad impressions and clicks counted once, in the hour they happened, with live numbers in seconds and exact, reproducible hourly totals that invoices are built on"
author: "design-room reference solution · practise with the simulator first"
date: "22 November 2026"
documentclass: article
fontsize: 10pt
geometry: a4paper,top=0.7in,bottom=0.75in,left=0.75in,right=0.75in
colorlinks: true
linkcolor: gblueink
urlcolor: gblueink
toc: true
toc-depth: 2
numbersections: false
---

\newpage

# How to read this document

This is the **long answer key for question `SD-03`** in
[design-room](https://github.com/nirmata78/design-room), an open-source system design interview
simulator, and the written companion to its reference-solution video (the **compact cut**: about 70
minutes, six challenges). It shows how a strong Staff candidate (L6/L7) runs the round and adds the
**why** behind every line.

**One question, many names.** The bank keeps this as the single question for *counting events that are
money*: ad impressions and clicks, video views paid per play, API calls billed per request, metered cloud
usage. Google often phrases it as *"billions of events a minute, sub-second dashboards and exact
billing-grade hourly rollups"*; others say *"usage metering"* or *"ad click aggregation"*. The nouns
change; the crux does not. SD-01 is its approximate-only sibling (no money), SD-02 the top-K one.

**The document has three layers:**

1. **Part I, the system in pictures.** What the system is, what one impression experiences, what one hour's
   number goes through, and where the load lands.
2. **Part II, the round, stage by stage.** What you do in the room. The six **challenges** of the video
   are Stage 6, with more detail than the video has time for.
3. **Part III, the internals.** Event IDs and dedup, watermarks, two-stage aggregation and HyperLogLog,
   Iceberg snapshots and manifests, and ClickHouse's replacing tables, one level below Stage 5.

**The coloured boxes:**

::: {.key title="Top-3 number"}
One of the back-of-the-envelope numbers worth computing out loud in the round.
:::

::: why
Explains a term or a decision in plain words. This is for you, not for the interviewer.
:::

> Words you can say in the room, nearly verbatim.

::: warn
A trap: something weak candidates do, or a claim that breaks under a follow-up question.
:::

::: load
What this part of the system sees at peak, with numbers.
:::

**Practise in three passes.** (1) Read Part I and Part II once. (2) Close the document and run the
[simulator](https://github.com/nirmata78/design-room) cold:
`Read CLAUDE.md. Mock me: SD-03, Google, staff, full round.`
(3) Debrief against the Stage 12 self-check, then reread only the sections where you fell short.
**Do not memorise numbers.** Memorise the order of the argument and how to rebuild each number.

**About the numbers.** The scale figures in Stage 1 are the simulator's cue sheet. Everything derived from
them is arithmetic, and every planning assumption (event size, compression, retry rate, price per click)
is labelled *given*, *derived*, *illustrative* or *initial target*. None is a measurement, none is any
company's real figure, and this is not any company's actual design.

**The prompt as the interviewer reads it:**
*"Design the system that counts ad impressions and clicks. Advertisers watch their numbers live on a
dashboard, and they are billed on the hourly totals."*

::: {.key title="The one-sentence insight to land by minute 12"}
**Count once, from one log, with one piece of code run twice:** fast and provisional for the dashboard,
exact and pinned for the bill. **Never increment a number you can recompute: replace it,** and keep every
version you billed.
:::

::: why
**Why this sentence.** It names all four places the question is graded: *once* (dedup on an ID minted at
the source), *one log* (a replayable source of truth), *run twice* (the live and the billed numbers come
from the same code, so their difference has a name), and *replace, never increment* (a replay or a
correction cannot double anything). Everything after it defends one of those four.
:::

\newpage

# Part I: The system in pictures

## Vocabulary you need first

| Term | Plain meaning | Where it lives |
|---|---|---|
| **Impression / click** | An ad was shown / an ad was clicked | events from SDKs and ad servers |
| **Event ID** | A unique ID minted when the event happens, carried by every retry | the event itself |
| **Impression ID** | The ID of the impression a click came from; one billable click per impression | click events |
| **Event time** | When the event happened (by the client's clock, checked) | the event; windows |
| **Processing time** | When our system sees it | never used for billing |
| **Watermark** | The job's claim that no older event is still coming | the live aggregator |
| **Window** | A bucket of event time, here one minute per ad | the live aggregator |
| **Allowed lateness** | How long after the watermark a window still accepts events | one hour, live |
| **Cutoff** | When a billing hour is closed and computed | 48 hours after the hour |
| **Version** | A billing hour is never edited; a correction adds version n + 1 | billing tables |
| **Manifest** | What one billing run read: snapshot, rate card, invalidations, code | beside every hour |
| **Adjustment** | The difference between a new version and what was invoiced | sent to invoicing |
| **Snapshot** | An immutable, numbered state of a lake table | Iceberg |
| **HyperLogLog** | A small, mergeable sketch that estimates distinct counts | reach on dashboards |

## What one impression experiences

1. **Minted.** An ad is shown in an app. The SDK creates an impression event with a UUIDv7 event ID and
   the client's timestamp, and buffers it.
2. **Sent.** Within a second, the SDK sends a batch of up to 500 events to the nearest collector.
3. **Appended.** The collector validates the batch, stamps the server time, clamps a client time that is
   too far off, and appends the events to Kafka, keyed by event ID, waiting for all in-sync replicas. Only
   then does it answer `202`.
4. **Counted live.** The live aggregator (Flink) drops any event ID it has seen in ten minutes, adds the
   event to its subtask's partial sum for this ad and minute, and every second sends the partial on. The
   ad's minute window emits an early result every two seconds into ClickHouse, with a version.
5. **Seen.** The advertiser's dashboard shows it within about five seconds, labelled *provisional*.
6. **Landed.** Every five minutes the event is written to the lake, in the partition of the hour it
   happened.
7. **Billed.** Forty-eight hours after that hour, the billing job reads the hour at a pinned snapshot,
   removes every duplicate, drops invalidated events, prices and sums, and writes the hour as version 1.
   The dashboard switches from provisional to final.
8. **Corrected, maybe.** If fraud later invalidates it, the hour is re-run as version 2 and the
   difference goes on the next invoice as an adjustment line.

::: say
The bill is the product. The dashboard is a preview of it, and every number on it says whether it is
provisional or final.
:::

## One hour's number, three times

![One hour, three numbers: live at +10 s, final at +48 h, corrected at +9 days. Each later number is slower, more exact, and the one that counts.](diagrams/video-tension.pdf){width=95%}

## The whole design on one page

![Version 4, with the mechanisms on it. Intake across the middle, the live path on top, the billing path along the bottom, the reconciler top left.](diagrams/video-recap.pdf){width=100%}

## Where the load lands

::: load
**Collectors:** 10 M events a second on average, 30 M at the evening peak (6 GB/s). **Kafka:** 18 GB/s of
replicated writes at peak over 1,024 partitions; about 390 TB on disk for three days. **Live aggregator:**
30 M events a second through dedup (0.7 TB of keyed state), 512 partial sums per active ad per second
after the combiner. **ClickHouse:** about 100,000 rows a second of minute rows; about 2,000 dashboard
queries a second at peak (illustrative). **Lake:** 0.6 PB a month. **Billing job:** 24 hour-runs a day plus
re-runs of dirty hours. **Hot ad:** 2 M impressions a second on one key during a sports break.
:::

\newpage

# Part II: The round, stage by stage

| Stage | Minutes (of 60) | What you produce |
|---|---|---|
| 1 Clarify | 0–6 | The scale line; five questions; four FRs; numbers; IN and OUT |
| 2 Estimates | 6–11 | Events a second, bytes, dedup state, the hot ad, money in duplicates |
| 3 API and data | 11–16 | One write, three reads or corrections; six entities; the billing key |
| 4 High-level design | 16–28 | V1, V2, V3; two numbered flows; four sequences |
| 5 Technology | inside 4 | One sentence per choice, against the alternative |
| 6 Deep dives | 28–52 | Two to four of the six challenges |
| 8–9 Failures, SLOs, cost | 52–57 | Two minutes each |
| 11 Close | 57–60 | Four sentences |

# Stage 1: Clarify requirements

**The scale line first** (given): 25 trillion impressions and 250 billion clicks a month (1 %
click-through); raw events kept six months, about 150 trillion; peak 30 million events a second in the
evening, three times the 10 million average; one prime-time ad at 2 million impressions a second.

| Question | Answer (cue sheet) | What it changes |
|---|---|---|
| How fresh must the dashboard be? | Within ~10 s; the bill hourly, final within two days | Two clocks: a live run and a billing run |
| Which numbers must be exact? | The bill, exact and auditable; the dashboard converges to it | One exact run for money, one fast run for people |
| Duplicates? Late data? | SDKs retry; phones buffer for hours or days; clocks skew | Event IDs; event time; a clamp on client time |
| Fraud? | A separate system; can invalidate after invoicing | Versions of an hour; adjustment lines |
| Retention and audits? | Raw 6 months (dispute window 90 days); aggregates 7 years; re-runs reproduce | A billing run must be a pure function of pinned inputs |

::: why
**Why ask "which numbers are money" first.** It splits the problem in two before any box is drawn. A
candidate who designs one number for everything either makes the dashboard slow (exact) or the bill wrong
(approximate). Asking it out loud is the strongest requirements signal on this question.
:::

**Functional requirements.** FR1 *Record*: accept impression and click events, acknowledge once durable,
a retry changes nothing. FR2 *Live*: per ad and campaign, impressions, clicks, spend and approximate unique
reach within 10 s. FR3 *Bill*: exact hourly totals per campaign and ad, final at a cutoff, versioned,
exported. FR4 *Correct*: late events and invalidations reach closed hours as new versions and adjustment
lines; a sent invoice is never edited.

**Non-functional requirements** (initial targets): ingest 30 M events/s at peak, ack p99 50 ms; live
freshness p99 10 s; dashboard query p99 1 s; bill final at H + 48 h and reproducible bit for bit; an
acknowledged event survives a zone loss; ingest 99.99 %, dashboards 99.9 %.

**In scope:** ingest, dedup, live counts, approximate reach, hourly billing totals, versions, corrections,
an audit trail, reconciliation. **Out, on purpose:** fraud detection itself, ad serving and auctions,
budget pacing (a consumer of the live counts, and the reason they must be fast), invoicing and payment,
conversion attribution, advertiser accounts.

> The core is three things: an idempotent, durable intake; one aggregation, run twice; and versioned
> final hours with a correction path.

![C4 level 1: the system, the clients that send events, the advertiser who reads them, and the two systems around the bill.](diagrams/video-c4-context.pdf){width=90%}

# Stage 2: Back-of-the-envelope

::: {.key title="Top-3 number 1: events a second, and what they rule out"}
2.5 × 10^13^ impressions ÷ 2.6 × 10^6^ s ≈ **10 M/s**; × 3 in the evening = **30 M/s**, 1.8 billion a minute.
At 200 B an event that is **6 GB/s**, 18 GB/s with three replicas. *What it means:* no database takes a
write per event; a partitioned log does. *Say:* "Thirty million a second rules out a write per event
anywhere but an append-only log."
:::

::: {.key title="Top-3 number 2: dedup state"}
Ten minutes at the peak: 30 M/s × 600 s = 1.8 × 10^10^ IDs × ~40 B ≈ **0.7 TB**. *What it means:* dedup
must be partitioned keyed state (about 1.4 GB on each of 512 subtasks), not one Redis set of eighteen
billion keys. *Say:* "Dedup is state, so it lives where the events are partitioned."
:::

::: {.key title="Top-3 number 3: the money in duplicates"}
If 0.3 % of click batches are retried: 0.003 × 2.5 × 10^11^ = 7.5 × 10^8^ duplicate clicks a month; at $0.50 a
click, **about $375 M a month** billed twice (illustrative). *What it means:* dedup is the crux, not an
optimisation. *Say:* "Retries alone would overbill by hundreds of millions a month."
:::

| Number | From | Arithmetic | Label | Decides |
|---|---|---|---|---|
| Clicks | monthly volume | 2.5 × 10^11^ ÷ 2.6 × 10^6^ ≈ 100 k/s; peak 300 k/s | derived | same pipeline; billable click keyed by impression ID |
| Partitions | bandwidth | 6 GB/s ÷ ~6 MB/s per partition ≈ 1,000 | illustrative | 1,024 partitions; ~80 brokers |
| Broker disk | average | 2 GB/s × 259,200 s ≈ 520 TB; ÷ 4 × 3 ≈ 390 TB | illustrative | brokers keep 3 days; the lake beyond |
| Lake | volume, retention | 2.5 × 10^13^ × 25 B ≈ 0.6 PB a month; × 6 ≈ 3.8 PB | illustrative | object storage by event hour |
| Hot ad | given | 2 M/s on one key vs ~300 k/s for one subtask | illustrative | combine before the shuffle |
| Billing rows | ads × hours | ~5 M active ads × 24 ≈ 1.2 × 10^8^ rows a day; 7 years ≈ 15 TB | illustrative | a columnar table, not PostgreSQL |
| Freshness | NFR | 1 + 0.5 + 2 + 1 + 1 ≈ 5.5 s of 10 | target | early firings every 2 s |

![The freshness budget, worst case: SDK batching, collector and log, early firing, insert, query.](diagrams/video-budget.pdf){width=95%}

# Stage 3: API and data

## The API

```json
POST /v1/events
{"events": [{
  "event_id": "0190f3c2-7d1e-7a4b-9c2e-...",
  "type": "click",
  "impression_id": "0190f3c1-0b9a-7f10-...",
  "ad_id": 77,
  "client_ts": "2026-11-22T14:05:07.312Z"
}, ...]}

202 Accepted  {"accepted": 500}
```

::: why
**Why the ID is minted by the client.** A retry is the same request sent again. If the collector minted
the ID, a retry would get a new one and dedup would see two events. UUIDv7 puts a millisecond timestamp in
its first 48 bits, so IDs sort by time, which helps the lake's file layout and makes a skewed clock
visible. **Why the click names its impression.** A user who double-clicks makes two click events; the
billing rule is one billable click per impression, so the dedup key for billing clicks is the impression
ID.
:::

| Endpoint | Serves | Touches | Response carries |
|---|---|---|---|
| `GET /v1/campaigns/{id}/live?step=1m` | FR2 | live minutes | `asOf`, `provisional: true` |
| `GET /v1/billing/hours?advertiser=&month=` | FR3 | HOUR TOTAL | `version`, `manifest_id`, `final: true` |
| `POST /v1/invalidations` (fraud system) | FR4 | INVALIDATION | event IDs with their hours, reason, rule version |

## The data model

![Conceptual model: an hour total is a weak entity whose key includes the hour and a version.](diagrams/video-erd-chen.pdf){width=95%}

![Physical model: where each entity lives, and its key.](diagrams/video-erd-physical.pdf){width=95%}

| Store | Holds | Writer | Lose it? |
|---|---|---|---|
| Kafka `events.raw` | 3 days of events, keyed by event ID | collectors | a replay source; the lake has a copy after 5 min |
| Iceberg `events` | 6 months, by event hour | lake sink | **no**: the bill's source of truth |
| Iceberg `billing_hour` + `manifest` | every version of every hour, 7 years | billing job | **no**: the record of what was billed |
| ClickHouse `live_minute`, `final_hour` | live minutes; a copy of final hours | live aggregator; billing job | yes: rebuildable from the log and the billing tables |
| `invalidation` (Kafka topic + table) | append-only | fraud system | no: the input to corrections |

# Stage 4: High-level design

## Version 1: the simplest thing that is exact

![V1: a log, a lake, an hourly job. Exact and replayable; the dashboard is a day behind.](diagrams/video-base-v1.pdf){width=100%}

Collectors append to a log; the log lands in a lake by event hour; a billing job counts each closed hour
and writes billing tables; a reporting API serves them. **Objection:** the dashboard is an hour or a day
behind, and budget pacing cannot run on that.

## Version 2: freshness

![V2: a live aggregator on the same log, and a live store that also receives the final hours.](diagrams/video-base-v2.pdf){width=100%}

A live aggregator runs **the same aggregation code** as a stream job and writes minute rows to a live
store; the billing job loads its final hours into the same store, so the API reads one store and labels
each number provisional or final. **Objection:** a bill has to be final, yet late events and fraud
corrections keep arriving after the hour.

## Version 3: corrections

![V3: invalidations in, final hours out, versions in between.](diagrams/video-base-v3.pdf){width=100%}

The fraud system appends invalidations; the billing job re-runs the affected hours as new versions; final
hours and adjustments go to invoicing. This is the baseline the challenges attack. Version 4 (Stage 6.6)
adds a reconciler.

## The numbered flows and the sequences

![FR1 and FR2: an impression from the phone to the dashboard.](diagrams/video-flow-live.pdf){width=100%}

![FR3 and FR4: an hour from the log to the invoice.](diagrams/video-flow-bill.pdf){width=100%}

![FR1, record: durable before the yes.](diagrams/video-seq-ingest.pdf){width=85%}

![FR2, live: from the log to a provisional number.](diagrams/video-seq-live.pdf){width=85%}

![FR3, bill: closing an hour, pinned.](diagrams/video-seq-bill.pdf){width=85%}

![FR4, correct: a correction without editing an invoice.](diagrams/video-seq-correct.pdf){width=85%}

# Stage 5: Components and technologies

Two containers carry almost every challenge, so open them up first.

![The live aggregator, in the order an event meets it.](diagrams/video-c4-comp-stream.pdf){width=100%}

![The billing job: the same counting, plus what makes it final.](diagrams/video-c4-comp-billing.pdf){width=100%}

![The container view with technologies.](diagrams/video-c4-containers-tech.pdf){width=100%}

<!-- stack:sections -->

## Collector: a stateless Go service with a disk spool

*How it is built.* Batches of up to 500 events, produced to Kafka with `acks=all` and the idempotent producer; `202` only after the ack. If Kafka is unreachable: a bounded disk spool for ten minutes, then `503`. The collector never generates an event ID and never deduplicates: the ID is minted by the SDK or the ad server when the event happens, and dedup is downstream. It adds `server_ts` and the collector ID. Client time is kept as `client_ts`; the event time is the client time when it lies within 72 hours before and 5 minutes after the server time, and the server time otherwise, with a `clamped` flag. Producer settings: `linger.ms=20`, `batch.size` 256 KB, zstd compression, `enable.idempotence=true`. The spool is an append-only file per pod, replayed in order on reconnect; a pod that dies with a non-empty spool is drained by its replacement from the same persistent volume.

*Why Go on Kubernetes, behind an L4 load balancer:* It does three things and nothing else: validate, stamp the server time, append. Stateless, so it scales on CPU; the ack means durable.

*Rejected:*

- **Warehouse streaming inserts**: Ties ingest to the store's quotas, and leaves no replayable log.
- **Access logs shipped by an agent**: The client hears yes before the event is durable.

*Course:* building-blocks course, part 11 §11.10 (idempotent writes) and part 12 §12.5 (load shedding).

*Drill.* "Kafka is down for four minutes. What do the SDKs and the collectors do?" The collector spools to local disk and keeps answering 202 for up to ten minutes; past that it answers 503 and the SDK keeps its own buffer and retries with the same event IDs. Nothing acknowledged is lost; duplicates from the retries are removed downstream.

## Event log: Kafka, keyed by event ID

*How it is built.* Topic `events.raw`: partition = hash(event ID) mod 1,024, RF 3 over three zones, `min.insync.replicas=2`. Brokers keep three days. Brokers keep three days (about 390 TB compressed, with replicas); replays older than that read the lake. Keying by ad would put a 2-million-a-second ad on one partition; keying by event ID spreads it and keeps a retry on the same partition as its original, which the stream's dedup uses. Six gigabytes a second at peak, three replicas, is 18 GB/s of broker writes: about 80 brokers at 250 MB/s each (illustrative). Consumer groups: the live aggregator, the lake sink. Tiered storage is possible but not relied on. RabbitMQ was also rejected: a queue, not a log, so a consumed message is gone and there is nothing to replay.

*Why Kafka, 1,024 partitions, RF 3 over 3 zones:* A replayable log is the one copy everything is derived from; keyed by event ID, load is even and a retry lands beside its original.

*Rejected:*

- **Google Pub/Sub**: An honest equal on Google Cloud; rejected for per-key placement and portability.
- **Amazon Kinesis**: 1 MB/s a shard: about 6,000 shards to manage at 6 GB/s.

*Course:* building-blocks course, part 10 §10.2–10.5 (inside a partitioned log, delivery semantics).

## Live aggregator: Flink, streaming

*How it is built.* Dedup keyed by event ID (TTL 10 min), a per-subtask combiner flushed every second, then ad × minute windows: early results every 2 s, final on the watermark. Checkpoints every 30 s. The watermark is the minimum over partitions of (largest event time seen minus 2 minutes); an idle partition is excluded after 30 seconds so it cannot hold the watermark back. Allowed lateness is one hour: a late event updates its minute again; anything later goes to a side output that only counts late events (the lake has them anyway). Unique reach is a HyperLogLog sketch per campaign and minute, merged across minutes on read. The sink writes rows with a version (window end, emit sequence) so a re-emitted minute replaces the old row. Dataflow (Apache Beam) is an honest equal on Google Cloud: the same model as a service; rejected only to keep one engine for both runs on any cloud.

*Why Apache Flink, 512 subtasks, RocksDB state:* Keyed state with a TTL, event-time windows, and checkpoints that hold state and offsets together. The same job runs in batch mode for the bill.

*Rejected:*

- **Kafka Streams**: Re-keying to the ad writes a repartition topic: another 6 GB/s through the brokers.
- **Spark Structured Streaming**: A near-equal; micro-batches eat into the 10 s budget.

*Course:* building-blocks course, part 10 §10.11–10.13 (event time, stateful processing, Lambda and Kappa).

*Drill.* "Your watermark stops moving. What happened, and what do the dashboards show?" Usually one idle or stuck partition: the watermark is a minimum. Idle partitions are excluded after 30 seconds; a stuck one shows as lag on that partition. Early firings keep the dashboard moving, marked provisional, while on-time results wait.

## Live store: ClickHouse, replacing by version

*How it is built.* `live_minute ORDER BY (campaign_id, ad_id, minute, shard)` with a `version` column, inserted in batches. Reads take the latest version per key and sum the shards. Sharded across nodes by campaign so one advertiser's dashboard hits one shard. A hot ad writes up to 16 rows a minute (one per combiner shard); the read sums them. Merges collapse replaced rows in the background; until then `argMax` by version (or `FINAL` on small ranges) gives the right answer. Closed hours are also loaded from the billing tables into `final_hour`, so one query serves both. Bigtable was also rejected: fast row reads, but no aggregation queries, so every dashboard becomes a scan in the API.

*Why ClickHouse, ReplacingMergeTree, 2 replicas a shard:* Columnar scans answer a dashboard in milliseconds; a row keyed by what it counts, with a version, makes a re-emitted minute a replacement.

*Rejected:*

- **Apache Druid / Pinot**: Honest equals; more moving parts for no property we need.
- **Redis counters**: An increment is not replay-safe, and history does not fit in memory.

*Course:* building-blocks course, part 14 §14.9 (columnar storage) and part 8 §8.10 (split counters).

## Event lake and billing tables: Iceberg on object storage

*How it is built.* `events` partitioned by event hour, 0.6 PB a month. `billing_hour` keyed by (campaign, ad, hour, version); each run commits version n + 1 with its manifest. The lake sink (a Flink job) commits files every five minutes; late events for an old hour are new files in that hour's partition, stamped with the ingest time, so "hour H as of the cutoff" is a snapshot, not a guess. Raw events are kept six months (the dispute window is 90 days) and then expired by snapshot expiry; billing tables are kept seven years (about 15 TB). The billing job is the live aggregator's code run in Flink's batch mode over one hour: the same dedup, combine and window operators, with all data present. BigQuery as the system of record was also considered: a good choice on Google Cloud, rejected here for the per-query cost of re-running months and to keep the truth in open files.

*Why Apache Iceberg on GCS, Parquet + zstd:* Each commit is a snapshot with an ID, so a run pins what it read, and replacing an hour is atomic.

*Rejected:*

- **Plain Parquet folders**: No atomic overwrite and no snapshot: a reader can see half an hour.
- **Delta Lake**: An honest equal; Iceberg chosen for engine-neutral tables.

*Course:* building-blocks course, part 7 §7.7 (multi-version storage) and part 10 §10.13 (batch and stream).

*Drill.* "Finance wants last March re-run and bit-identical. What makes that possible?" The March manifests: each names the Iceberg snapshot of the events, the rate-card version, the invalidation-list snapshot and the job's image digest. Re-running that image over those snapshots gives the same rows, because the job uses no wall clock, sums integers, and sorts before it reduces.

<!-- /stack:sections -->

## The stack on one page

<!-- stack:summary -->

| Container | Choice | Rejected | The deciding reason |
|---|---|---|---|
| Collector | Go, stateless, disk spool | warehouse streaming inserts | the ack means the log has it |
| Event log | Kafka, keyed by event ID | Pub/Sub (equal), Kinesis | replayable; even load; retries co-located |
| Live aggregator | Flink, event time | Kafka Streams, Spark | state TTL, watermarks, one engine for both runs |
| Live store | ClickHouse | Druid/Pinot (equal), Redis | replace by version; columnar slice-and-dice |
| Lake + billing | Iceberg on GCS | Hive folders, Delta (equal) | snapshots to pin; atomic overwrite |

Each fix in Stage 6 rejects one tool by name:

| Deep dive | Rejected | Because |
|---|---|---|
| 6.1 | Kafka exactly-once (idempotent producer and transactions) | it removes a producer's own retry inside one session; an SDK retry over HTTP is a new request, and only dedup on the event ID removes it. |
| 6.2 | Processing-time windows | they bill a phone's Tuesday-evening impressions in Wednesday's 6 a.m. hour. |
| 6.3 | Redis `INCRBY` on one counter key | one key is one shard's thread, about 100,000 operations a second against 2 million, and a replay increments again. |
| 6.4 | Flink's two-phase-commit sink alone | it makes one run's output atomic; a second run from four hours earlier still adds on top unless the write replaces by key. |
| 6.5 | Updating billed rows in place | the invoice then matches no stored version, and the audit trail ends at the edit. |
| 6.6 | Lag and CPU dashboards | they stay green while the pipeline counts wrong; only conservation checks and canaries see a wrong number. |

<!-- /stack:summary -->

## When you don't need all this (the alternate path)

![ALTERNATE: one ClickHouse cluster replaces the lake, the billing job and the billing tables.](diagrams/video-alt.pdf){width=100%}

Below about **200,000 events a second**, one ClickHouse cluster can be the buffer, the truth and the
dashboard. Collectors insert batches with an `insert_deduplication_token`; a materialised view keeps
minute rollups; billing is a nightly `INSERT … SELECT` from a `ReplacingMergeTree` of events, deduplicated
by event ID with `FINAL`. **What it gives up:** there is no independent replayable log (the table is the
only copy); a heavy query slows ingest; a correction is a mutation; and dedup happens on background
merges, so it is eventual unless every query pays for `FINAL`. **The line:** a cluster of about twenty
nodes ingests on the order of 1–2 M rows a second; the scale line's average is 10 M/s, an order of
magnitude past it.

> Below about two hundred thousand events a second, with room to spare, I'd ship the one-box version, and
> say out loud when I'd switch.

# Stage 6: Deep dives

The video's six challenges, in the order each fix creates the next question. The interviewer will pick
two to four.

## 6.1 The same click, three times (correctness, the crux)

**The case.** Batch B17 with click `e7f3…` is appended at offset 81,220; the `202` is lost on a cell
network; the SDK retries at +2 s and +4 s: offsets 81,977 and 82,610. Three copies, and nothing did
anything wrong.

**The mechanism.** The event ID is minted at the source, so every copy carries it. The log is keyed by
event ID, so all copies land on the same partition and reach the same dedup subtask. The live
deduplicator keeps keyed state (`ValueState<Boolean>` keyed by event ID, a TTL of ten minutes, in
RocksDB) and drops any record whose ID is present. State and Kafka offsets are checkpointed together, so
a restart restores the state that matches the offsets it resumes from. The billing run deduplicates over
the whole hour: a group by event ID, keeping the first row (for clicks, by impression ID).

::: why
**Why two windows.** Ten minutes of state per ID is affordable (0.7 TB); an hour of state on the live
path is not (4 TB, and the state would be checkpointed every 30 s). The billing run sees the whole hour as
files, so its dedup is exact at no state cost. A retry later than ten minutes over-counts the *live*
number until the hour closes; the *bill* is unaffected, and the reconciler counts late duplicates so the
window is measured, not guessed.
:::

::: warn
**"Kafka is exactly-once."** Kafka's idempotent producer and transactions remove a producer's own
retries inside one producer session, and make read-process-write atomic inside Kafka. An SDK retry over
HTTPS is a new request from a different process; only dedup on the event ID removes it. Exactly-once
end-to-end is at-least-once delivery plus idempotent, deterministic processing.
:::

**What it does not cover.** A client that mints a new ID per click, or a bot: that is fraud, and the fraud
system's invalidations (6.5) handle it.

> Every event carries an ID minted where it happened. The live path drops repeats in keyed state for ten
> minutes; the billing run drops them over the whole hour. Exactly-once isn't a broker setting.

## 6.2 Yesterday's events at 6 a.m. (correctness)

**The case.** A phone offline on a flight buffers 300 impressions between 21:10 and 23:40 on Tuesday; the
campaign's flight ends at midnight; the batch arrives at 06:00 on Wednesday. Counted by arrival, those
impressions are billed after the campaign ended. Another phone reports `client_ts = 2031-01-01`.

**The mechanism.** Event time is the client's time if it lies within [server time − 72 h, server time +
5 min]; otherwise the server time, with a `clamped` flag. The live watermark is the minimum over active
partitions of (latest event time − 2 minutes); a partition silent for 30 s is excluded so one idle
partition cannot freeze every dashboard. Minute windows emit early every 2 s, finally when the watermark
passes their end, and again (with a higher version) for a late event within one hour of allowed lateness.
Later events are only counted as late on the live path; the lake has them. The **bill** waits: files land
in the partition of their event hour, and at H + 48 h the hour closer pins an Iceberg snapshot of that
partition and the billing run reads exactly that.

![Mechanism M2 at protocol level: a watermark, an early result, an on-time result, a late update by version.](diagrams/video-seq-th-watermark.pdf){width=85%}

::: why
**Why 48 hours.** It is an initial target, to be measured: if 99.99 % of events arrive within 36 hours,
the remaining 0.01 % become version 2 of their hour at the cost of one adjustment line. Shorter means more
versions; longer means a later bill. **Why 72 hours and 5 minutes.** Long enough for a weekend offline,
short enough that a broken clock cannot open hours that never close; five minutes forward tolerates NTP
drift.
:::

::: warn
**Trusting the client clock.** It is skewed and attacker-controlled. Clamp it, flag what you clamped,
and alert when the clamped share jumps (usually one SDK release).
:::

## 6.3 One ad at 2 million a second (overload)

**The case.** A sports break puts ad 77 on every screen: from 3,000 to 2,000,000 impressions a second.
Keyed by ad, one window subtask receives all of it; it saturates at a few hundred thousand updates a
second, its input buffers fill, and Flink's backpressure slows every source. Lag grows on all 1,024
partitions; every advertiser's dashboard goes stale.

**The mechanism.** Two-stage aggregation. Each of the 512 subtasks keeps a small map of partial sums per
(ad, minute) and flushes it every second; the keyed merge receives 512 updates a second for ad 77 instead
of 2 M. On the store side the counter is sharded: up to 16 rows per (ad, minute), keyed by `shard =
subtask mod 16`, summed on read.

![The combiner: 512 partial sums a second instead of 2 million updates on one thread.](diagrams/video-combiner.pdf){width=95%}

::: why
**Why the log is not the hot spot.** The log is keyed by event ID, so its partitions are even whatever the
ads do. The hot spot was one thread, created by the first `keyBy(ad)`. Combining before that shuffle is
the same idea as a sharded counter, applied in time.
:::

**Five hundred hot ads.** Each subtask's map holds one entry per active ad and minute; the merge stage
sees 500 × 512 ≈ 256,000 updates a second, spread over its subtasks by key. It scales with active keys,
not with events. The cost: one second more delay, inside the budget.

## 6.4 Replay four hours (failure recovery, the crux)

**The case.** A bug in the reach computation is found at 14:02; the fixed build is deployed at 14:10 and
the offsets rewound to 10:00. With a sink that adds (`n = n + partial`), minutes 10:00–14:00 are doubled;
budget pacing stops forty campaigns. A billing job written the same way would double the invoice.

**The mechanism.** Every output is a replacement keyed by what it counts. `live_minute` rows are keyed
(campaign, ad, minute, shard) with a `version`; ClickHouse's `ReplacingMergeTree(version)` keeps the
highest version per key and readers take `argMax(…, version)`. A billing hour is committed as a whole
partition of `billing_hour`, as the next version, and the billing run is a pure function of its manifest.

![The replay with replacing writes: the store keeps the higher version; the bill re-run changes nothing.](diagrams/video-seq-ch4-replay.pdf){width=85%}

**Bit-identical, two years later.** The manifest pins the Iceberg snapshot of the events, the rate-card
version, the invalidation snapshot and the job's image digest. The job reads no wall clock, uses integer
micro-dollars (floating-point sums depend on order), and sorts before every reduction. The honest limit:
raw events are kept six months, so after that an hour is reproducible from its stored version, not from
events.

::: warn
**"Our sink is two-phase commit."** Flink's two-phase-commit sinks make one run's output atomic with its
checkpoints. A second run from four hours earlier is a different run; it still adds on top unless the
write replaces by key.
:::

## 6.5 Fraud after the invoice (correctness)

**The case.** October is invoiced on 1 November: advertiser A, 155 M clicks, $77.5 M. On 9 November the
fraud system flags botnet 17: 3.1 M of A's October clicks (2 %, $1.55 M). Updating the billed rows in
place leaves an invoice that matches nothing stored.

**The mechanism.** Invalidations are appended (event ID, the event's hour, reason, rule version). The hour
closer marks the affected hours dirty and re-runs each with a new manifest; the writer commits version
n + 1 and version n stays; the adjuster computes version n + 1 minus what was invoiced and sends an
adjustment line.

```
on invalidations(b): mark_dirty(hours(b))
rerun(h):
    m = manifest(h, events_snap, rates_v, invalid_snap)
    v = latest_version(h) + 1
    rows = price(dedup(read(h, m)) - invalid(m))
    commit(h, v, rows, m)          # version v - 1 stays
    for r in rows:
        d = r.cost - invoiced(r.key)
        if d != 0: adjustment(r.key, v, d)
```

::: why
**One path for every correction.** Fraud, events past the cutoff and a rate-card fix all become "re-run
the hour with a newer manifest". There is no second code path that could compute a correction
differently from a bill.
:::

**Seven months later.** Past the six-month raw retention the events are gone; the dispute window is 90
days, so such invalidations are refused by contract, and the refusal is logged.

## 6.6 "Your numbers are 3 % high" (observability)

**The case.** A config push sets the dedup TTL to 10 seconds instead of 10 minutes. Lag, CPU and errors
stay green; live clicks run 3 % above their usual ratio to impressions; Monday's final hours are right
(the billing run dedups the whole hour); on Thursday an advertiser calls.

![V4: a reconciler that checks the numbers themselves.](diagrams/video-base-v4.pdf){width=100%}

**The mechanism (version 4).** A reconciler with three checks: **conservation per hop** each minute
(accepted = appended = landed − duplicates); **live against final** for every closed hour per campaign,
alerting above 0.5 % (this would have fired on Wednesday); **canary events** with known IDs every minute
from every region, each expected exactly once in the live store and in the final hour. And for the
advertiser: invoice line → hour version → manifest → the event IDs, exportable for their line.

| Symptom | Paired with | Means |
|---|---|---|
| Live clicks up 3 % | final for the same hour flat | duplicates on the live path |
| Live and final both up | impressions up too | real traffic |
| Accepted above landed | log lag flat | the lake sink is losing files |
| A canary seen twice | — | a duplicate path, wherever it is |
| Clamped share above 0.1 % | one SDK version | a client clock bug |

**Checking the checker.** The canary count is known, so the reconciler must count exactly that many or
page about itself; and no comparison for 15 minutes pages too.

## 6.7 How the whole system degrades, in priority order

1. **Ingest never refuses while it can spool:** a Kafka outage is absorbed by collector disk spools for
   ten minutes, then by SDK buffers (with `503`). No acknowledged event is lost.
2. **The bill is protected before the dashboard:** if the live aggregator falls behind, dashboards go
   stale and say so; the billing run reads the lake and is unaffected.
3. **The dashboard degrades to coarser data:** under query overload, the API serves hour rollups and
   cached results before it refuses.
4. **Corrections can wait:** dirty-hour re-runs are queued behind on-time closes.

# Stage 8: Failures and reliability

| Failure | Blast radius | What happens | Recovery |
|---|---|---|---|
| A zone is lost | one third of brokers and collectors | `min.insync.replicas=2` holds; producers continue | replicas re-sync |
| Kafka unreachable | all ingest | collectors spool 10 min, then `503`; SDKs buffer | drain spools in order |
| Live job crash | dashboards | restore from checkpoint (≤ 30 s of rework) | automatic |
| Live job bug | dashboards, pacing | rewind offsets; replacing writes | redeploy and replay |
| Lake sink stalls | the bill's input | conservation check pages; brokers keep 3 days | restart the sink, re-land |
| Billing run fails | one hour late | the closer retries; the hour stays provisional | rerun with the same manifest |
| ClickHouse shard lost | some dashboards | replica serves | rebuild from log and billing tables |

**One incident, walked through.** The 10-second dedup TTL of 6.6: detected by live-against-final at
Wednesday 09:15, page; on-call reads the symptom pair (live up, final flat), checks the deployment log,
reverts the config; replays the affected live hours (replacing writes); notifies affected advertisers
that Monday's provisional numbers were high and the billed numbers were not.

# Stage 9: SLOs, observability, cost

| SLI | Measured from | Target |
|---|---|---|
| Ingest success | collector `2xx` share, from synthetic SDKs in every region | 99.99 % |
| Live freshness | canary event time to its appearance in the API | p99 10 s |
| Bill on time | hours final by H + 50 h | 99.9 % |
| Correctness | canaries seen exactly once in live and final | 100 %; any miss pages |
| Live vs final | per closed hour per campaign | within 0.5 % |

**Cost, roughly (illustrative).** The largest items are the brokers (about 80, with 390 TB of disk), the
live aggregator (hundreds of cores for 30 M events a second), and lake storage (3.8 PB, about $75k a month
at $20 per TB-month). Levers: shorter broker retention (the lake is the long replay source), sampling
impressions *never* (they are billed), compressing harder in the lake, and fewer re-runs by a measured
cutoff.

# Stage 10: The EM layer (dropped in the compact cut)

The compact video drops the build-cost chapter. In a manager round: V1 (log, lake, billing job) is one team
for a quarter and already bills correctly; V2 (live path) is the second quarter; corrections and the
reconciler follow. Buy the log and the stream engine as managed services if the company has them; build
the dedup, versioning and reconciliation, because they are the product.

# Stage 11: The close

> **What:** one log, one aggregation run twice: live in seconds, final at forty-eight hours. **Trade-off:**
> compute twice and a bill that waits, for numbers that are exact and reproducible. **Risk:** a wrong
> number that every system calls healthy; hence conservation checks, live-against-final and canaries.
> **Next:** measure the lateness curve and move the cutoff.

# Stage 12: Self-check

| Area | Weak | Strong | Exceptional |
|---|---|---|---|
| Requirements | one number for everything | splits money from preview | prices sub-second before accepting it |
| Correctness | `n = n + 1`; "exactly-once" | event IDs, event time, replace | the billable-click key; the clamp; versions |
| Trade-offs | Lambda or Kappa recited | two runs with reasons | one code run twice, and what each gives up |
| Depth | names Kafka and Flink | watermarks, keyed state | two-stage sums, manifests, `argMax` by version |
| Operations | lag and CPU | reconciliation | conservation per hop, canaries, an audit trail per line |

**Common traps:** deduplicating in memory only; trusting client time; one run for both numbers; editing
billed rows; HyperLogLog on the bill; incrementing a counter that a replay will increment again.

\newpage

# Part III: The internals

## Appendix A: Event IDs and dedup, in plain words

An event ID is a promise from the source: *this is the same event*. UUIDv7 is 128 bits: 48 bits of Unix
milliseconds, then random bits, so two devices never collide in practice and IDs sort by time. Dedup is a
set membership test with a lifetime. On the live path the set is Flink keyed state: because the stream is
keyed by event ID, each subtask holds only the IDs of its own key range, in RocksDB on local disk, expired
by TTL during compaction. On the billing path the "set" is a sort or hash aggregation over one hour of
files, exact and stateless between runs.

## Appendix B: Watermarks and windows

A watermark W(t) is a timestamp carried through the job saying "no event with event time below t will
arrive". Sources generate it per partition (here: latest event time minus 2 minutes); an operator's
watermark is the minimum over its inputs. Windows fire when the watermark passes their end; *early
triggers* fire on processing time before that; *allowed lateness* keeps a fired window's state so a late
event can update it. Every emission of the same window must carry a higher version so the store can
replace rather than add. Idle sources must be marked idle, or the minimum stops.

## Appendix C: Two-stage aggregation and HyperLogLog

Two-stage aggregation is a combiner: a map-side partial aggregate before the shuffle. It is exact for
associative, commutative functions (sum, count, max, HLL merge) and wrong for others (median). It trades
one second of latency for a hot key's load divided by the number of subtasks.

HyperLogLog hashes each item to 64 bits, uses the first 12 bits to pick one of 4,096 registers and keeps
in each register the longest run of leading zeros seen. The harmonic mean of 2^register^ estimates the
distinct count with a standard error of 1.04/√4096 ≈ 1.6 %, in about 3 KB. Two sketches merge by
register-wise maximum, so minute sketches roll up into hours and campaigns. It cannot delete an item, so it
never appears on a bill.

## Appendix D: Iceberg snapshots and manifests

An Iceberg table is metadata over immutable Parquet files: each commit writes new files and a new
snapshot that lists them, atomically, by swapping one pointer in the catalog. A reader that pins a
snapshot ID sees exactly that set of files forever (until the snapshot is expired). The billing manifest
stores that ID, so "what did the run for hour H read" is one number, not a directory listing. Replacing an
hour's partition is one commit: readers see the old version or the new one, never half.

## Appendix E: ClickHouse's ReplacingMergeTree

A MergeTree table stores sorted parts and merges them in the background. `ReplacingMergeTree(version)`
keeps, for rows with the same sorting key, only the one with the highest version, *when parts are merged*.
Until then duplicates exist, so queries either use `FINAL` (exact, slower) or `argMax(value, version)`
grouped by the key (exact, fast for dashboard ranges). Inserting a re-emitted minute is therefore a
replacement, which is what makes the live path replay-safe.

## Appendix F: Testing it

Property tests on the aggregation code: a shuffled, duplicated, delayed copy of a stream must give the same
final hour as the clean stream. A replay test in staging: rewind four hours and compare `live_minute` before
and after (equal). A determinism test: run the billing job twice on one manifest and compare the committed
files byte for byte. A chaos test: kill a broker zone and a Flink TaskManager during the evening-peak load
test; canaries must still be seen exactly once.

\newpage

# One-page cheat card

- **Scale line:** 25 T impressions + 250 B clicks a month; 6 months raw; 30 M/s evening peak; one ad at 2 M/s.
- **Numbers:** 10 M/s average, 6 GB/s peak, 1,024 partitions, 390 TB broker disk, 0.6 PB a month in the
  lake, 0.7 TB dedup state, $375 M a month in duplicates if retries are not removed.
- **Thesis:** count once, from one log, with one code run twice; replace, never increment; keep every version billed.
- **Mechanisms:** M1 event ID (minted at source; 10 min live, whole hour billed) · M2 event time (clamp,
  watermark − 2 min, 1 h lateness, 48 h cutoff) · M3 replace by key and version; pinned manifest · M4
  combine then merge; shard rows summed on read · M5 HyperLogLog for reach, never billed.
- **Stack:** Go collectors with a disk spool · Kafka keyed by event ID · Flink streaming and batch · ClickHouse
  ReplacingMergeTree · Iceberg on object storage for events and billing versions.
- **Challenges:** retries · late and skewed events · a hot ad · replay · fraud after the invoice · a wrong
  number nobody notices.
- **Alternate:** one ClickHouse cluster below ~200,000 events a second.
- **Say at the end:** what (one log, two runs), trade-off (compute twice, a bill that waits), risk (a wrong
  healthy-looking number), next (measure the lateness curve).
