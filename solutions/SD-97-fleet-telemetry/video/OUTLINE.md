# SD-97 · Device telemetry & live location map (fleet tracking) — reference-solution video outline

Target level: staff · **Compact cut** (GUIDELINES §3.4): ≈ 60 min, ≈ 6,750 words, 6 challenges, no build-cost chapter, no drill.
A **combination question**: SD-03 (one log, a hot and a cold path), SD-39 (H3 index, soft state), SD-29 (identity, store-and-forward,
backoff), with SD-98's pinned history. The video says which part is reused, where.

## Thesis and definition

- **Thesis:** one log keyed by vehicle, read twice: an overwrite view by cell for the map, and an append history by vehicle for
  replay. Sequence numbers decide what is newer; lanes decide what goes first.
- **Definition:** keeping, from one per-vehicle stream, a latest-state view by place and a complete history by vehicle.
- **Hook:** two products from one stream; one table for both is slow for the map and wrong for the history.

## Scale line (GUIDELINES §3.1)

Volume per month: **~10¹² positions, 52 TB compressed** · Total: **2 M vehicles, 2 years of history (≈ 1.25 PB)** · Peak: **1 M
positions/s at rush hour**; a city's network recovers and **100,000 vehicles flush 3 minutes of buffer**.

## 0 · What this question grades

| Axis | Weak | Strong |
|---|---|---|
| Requirements | "store positions, show a map" | separates live from history; asks about tunnels |
| Composition | everything from scratch | names the seams: SD-03, SD-39, SD-29 |
| Correctness | latest arrival wins | per-vehicle order; latest by seq |
| Depth | "partition by region" | key by vehicle; index by cell; thin by zoom |
| Operations | consumer lag | position age on the map, from canaries |

## 1 · Requirements

Clarifying: map within 2 s of receipt · tunnels buffer for minutes to hours · history 2 years, audits per vehicle, ML per day ·
safety events to dispatch in 1 s · 5,000 viewers at every zoom. FR1 Report · FR2 Watch · FR3 Replay · FR4 Alert. NFR: 2 s p99 to
the map; 1 s safety; 100 % of received positions in history; 10 s per vehicle-hour replay; the map may drop a point, the history may
not. IN: uplink, ingest, map, history, replay, alerts. OUT: raw sensor logs (SD-98), routing, dispatching, the control plane (SD-29).

## 2 · Estimates

| Number | Arithmetic | Decides |
|---|---|---|
| Ingest | 1 M/s × 300 B = 300 MB/s; × 3 = 900 MB/s | 512 partitions by vehicle |
| A month | 4 × 10⁵/s × 2.6 × 10⁶ s ≈ 10¹² | history in columns |
| Stored | 10¹² × ~50 B ≈ 52 TB a month; × 24 ≈ 1.25 PB | object storage |
| Live state | 2 M × 200 B ≈ 400 MB | memory per city |
| Map | ~100 res-7 counts per viewer per second at city zoom; ~400 deltas at street zoom | counts and deltas |
| Flush | 100,000 × 90 = 9 M messages; ≈ 150 k/s over a minute | lanes, capped backfill |
| Vehicle buffer | 1,800/h; 6 h ≈ 10,800 × 300 B ≈ 3.2 MB | a ring in flash, paged writes |
| Budget | 0.3 + 0.3 + 1.0 ≈ 1.6 of 2 s | a 1 s push tick |

## 3 · Theory

Is / is not (ride matching, metrics, the control plane) · S1 never backwards · S2 nothing lost · L1 fresh · L2 urgent first ·
M1 one log, two views (SD-03; `seq-th-split`) · M2 per-vehicle order and sequence (SD-29, SD-39) · M3 cells at several resolutions
(SD-39) · M4 lanes and backpressure (SD-29) · M5 subscriptions by cell · seams table · options: A one table, B log + lake only, C live
only, D log keyed by cell, **E log by vehicle → live by cell + history by vehicle; lanes; subscriptions** · failure catalogue.

## 4 · API and entities

Position message (seq, epoch, t, lane) · health summary · `WS /v1/map` · `GET /v1/vehicles/{id}/track` · safety topic. Entities:
VEHICLE, POSITION (weak, by seq), CELL, SAFETY EVENT, TRIP, VIEWPORT. Physical: positions (Iceberg, day × bucket, sorted), safety
events, live maps in memory, updater keyed state, subscriptions, the vehicle registry (SD-29).

## 5 · Design

| Version | Adds | Answers | Leaves |
|---|---|---|---|
| V1 | uplink, gateway, log, lake, map API | complete history | map minutes behind |
| V2 | state updater, live store | the live map | safety waits; replay imprecise |
| V3 | safety lane, dispatch, replay API, analysts | urgency, exact replay | is the map actually fresh? |
| V4 (ch. 6) | freshness probe | freshness measured on the map | — |

Where a position can wait (bounds per queue). Flows: `flow-live`, `flow-history`. Sequences: `seq-report`, `seq-watch`, `seq-replay`,
`seq-safety`.

## 5.1 · Components and technologies

Component views: vehicle uplink, state updater, map API.

<!-- stack:outline -->

| Container | Choice | How it is built | Rejected | Theory part |
|---|---|---|---|---|
| Telemetry log | Kafka, 512 partitions, keyed by vehicle ID | Topic `positions`, partition = hash(vehicle); a separate `safety` topic | Keying by geo cell; Google Pub/Sub | 10 §10.2, 10.6 |
| Live store | Go service, in memory, H3 res 9, per city | vehicle → (cell, position, seq) and cell → vehicles, with per-cell change counters | Redis GEO; The history lake | 6 §6.5 |
| Map API | Go, WebSockets, a 1 s push tick | A viewport maps to cells at its zoom's resolution; each second the server pushes changes, or counts when zoomed out. | Polling a bounding box; Every vehicle in view | 11 §11.6, 10 §10.10 |
| History lake | Iceberg on GCS, Parquet, day × 256 vehicle buckets | Partitioned by (event day, hash(vehicle) mod 256), sorted by vehicle and seq; late positions go to their event day. | Arrival-hour partitions; A time-series database | 7 §7.10, 14 §14.9 |

Fix-slide rejections: 1: Writing every arriving position to the live store; 2: Keying the log by geo cell; 3: Clients polling a bounding box; 4: Flushing the buffer oldest first; 5: Partitioning history by arrival time; 6: Consumer-lag dashboards.

<!-- /stack:outline -->

## 5.2 · Alternate path

One PostgreSQL: a latest table upserted by seq and a history table by day; PostGIS bounding-box map. Line: 5,000 vehicles every 2 s
= 2,500 writes/s, twice; below ≈ 5,000 vehicles, ship it.

## 7 · Challenges

1. **Out of the tunnel (crux):** seq filter in keyed state, live overwrites only with newer seq, history dedups by (vehicle, epoch,
   seq); why not timestamps; `seq-ch1-tunnel`; push: updater restart → checkpointed state; the store also compares. Rejected: writing
   every arrival to live.
2. **Downtown at six:** key by vehicle, index by cell, counts by zoom; zoom → resolution table; push: a stadium → hot-cell split as in
   SD-39. Rejected: keying the log by cell.
3. **Five thousand viewers:** cell subscriptions, change feed per pod and cell, snapshot on pan; polling vs pushing; push: a pod dies
   → jittered reconnect. Rejected: bounding-box polling.
4. **A city comes back:** lanes (safety, latest, capped backfill); the flush in numbers; pseudocode; push: server-side lanes; backfill
   is history-only. Rejected: oldest-first flush.
5. **One vehicle, one hour:** day × 256 buckets sorted by (vehicle, seq), late files in their event day, pinned snapshot; two kinds of
   reader; bytes read; pseudocode; push: late after the audit → a newer snapshot; gaps are reported. Rejected: arrival-hour partitions.
6. **Forty seconds stale (observability):** **V4** freshness probe: canary vehicles through every map pod, age on screen, per-pod
   freshness, safety canaries; the canary in detail; symptom pairs; SLIs. Rejected: consumer-lag dashboards.

## 8 · Recap

V4 with badges; one sentence per path; mistakes; thesis, with the three reused questions.

## Canon check

| Point | Covered at |
|---|---|
| Hot vs cold path split | M1, V2 (SD-03) |
| Geo indexing (H3 / S2 / quadtrees), dense cells | M3, challenge 2 (SD-39) |
| Edge buffering, reconnect flush, in-order dedup | M2, M4, challenges 1 and 4 (SD-29) |
| Backpressure | challenge 4, "where a position can wait" |
| Map tiles / viewport queries, thinning at low zoom | M5, challenges 2 and 3 |
| Replay and audit | challenge 5 |
| ML training reads | challenge 5, two kinds of reader |
| Raw sensor logs | dismissed: SD-98 |

## Budget (measured)

0: 415 · 1: 439 · 2: 306 · 3: 705 · 4: 313 · 5 (+5.1, 5.2): 1,205 · 6: 77 · 7: 3,039 · 8: 248 · **total 6,747 words (≈ 60 min)**.
