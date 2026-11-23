---
title: "SD-97 · Device Telemetry and a Live Location Map"
subtitle: "A reference solution for a system design round at the Staff bar: one log keyed by vehicle, read twice, into a live view by cell for the map and a complete history by vehicle for replay, built from three questions you already know"
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

The **long answer key for question `SD-97`** in [design-room](https://github.com/nirmata78/design-room), the companion to its
compact-cut video (about an hour, six challenges). It is asked as *fleet telemetry and a live operations map* (autonomous-vehicle and
delivery fleets), *live tracking of couriers or trucks*, and *device telemetry with a map*.

**A combination question.** It is built from three questions with their own reference solutions, and the strongest answer says so:

| Question | Reused here |
|---|---|
| [SD-03 Event counting](../SD-03-ad-click-aggregation/SD-03_Ad_Click_Aggregation_Reference_Design.md) | one log, a hot and a cold path; dedup by an ID |
| [SD-39 Ride matching](../SD-39-ride-matching/SD-39_Ride_Matching_Reference_Design.md) | the in-memory H3 index; soft state; hot cells |
| [SD-29 Device fleet](../SD-29-device-fleet/SD-29_Device_Fleet_Reference_Design.md) | identity, the gateway, store-and-forward, backoff |

::: {.key title="Top-3 number"}
A number worth computing out loud.
:::

::: why
A term or decision, in plain words.
:::

> Words to say in the room.

**Practise:** read Parts I–II, run `Read CLAUDE.md. Mock me: SD-97, Google, staff, full round.` cold, reread where you fell short.
**Numbers** are the cue sheet's plus labelled arithmetic; none is a measurement or any company's figure.

**The prompt:** *"Millions of vehicles report their position and health every few seconds. Design the system behind a live fleet
map for operations, plus a history that can be audited and replayed."*

::: {.key title="The one-sentence insight to land by minute 12"}
**One log keyed by vehicle, read twice: an overwrite view by cell for the map, and an append history by vehicle for replay.
Sequence numbers decide what is newer; lanes decide what goes first.**
:::

\newpage

# Part I: The system in pictures

![Two products from one stream.](diagrams/video-tension.pdf){width=95%}

![The seams: which earlier question each part comes from.](diagrams/video-seams.pdf){width=100%}

## Vocabulary

| Term | Plain meaning |
|---|---|
| **(epoch, seq)** | The vehicle's own message counter, kept in flash; the epoch changes only if flash is wiped |
| **Latest lane / backfill lane / safety lane** | The vehicle's three send queues, in priority order |
| **Live store** | The latest position per vehicle, by H3 cell, in memory |
| **Change feed** | A per-cell stream of "these vehicles moved", consumed by map pods |
| **Event day, vehicle bucket** | The history's partitions: the day the fix was taken, and hash(vehicle) mod 256 |
| **Canary vehicle** | A simulated vehicle that exercises every path |

## What one position experiences

1. The vehicle takes a GPS fix, numbers it, writes it to its flash ring buffer, and sends it on the latest lane.
2. The gateway checks the vehicle's certificate and appends the message to Kafka, keyed by vehicle.
3. The state updater (Flink, keyed by vehicle) compares its sequence with the last one: newer, so it moves the vehicle in the live
   store; older positions go to history only.
4. Map pods subscribed to the vehicle's old and new cells push the change to their viewers within a second.
5. Every five minutes, the lake sink writes it to Iceberg, in its event day and vehicle bucket, sorted.
6. Two years later, an auditor reads that vehicle's hour from one bucket at a pinned snapshot in about ten seconds.

![Version 4, with the mechanisms on it.](diagrams/video-recap.pdf){width=100%}

::: load
**Ingest:** 1 M positions/s at rush hour, 300 MB/s (900 MB/s replicated), 512 partitions. **Live store:** 400 MB. **Map:** 5,000
viewers, ~100 counts each per second zoomed out, ~400 deltas zoomed in. **Lake:** 52 TB a month, 1.25 PB for two years.
**Flush:** 9 M messages after a city-wide outage, ≈ 150 k/s for a minute, history only.
:::

# Part II: The round, stage by stage

# Stage 1: Clarify

| Question | Answer | What it changes |
|---|---|---|
| How fresh? | 2 s from receipt | a separate live view |
| Tunnels? | Buffers for minutes to hours | order from the vehicle |
| History? | 2 years; audits per vehicle; ML per day | a layout for both readers |
| Anything urgent? | Safety events in 1 s | a lane that never waits |
| Who watches? | 5,000 operators, every zoom | counts far, vehicles near |

FR1 Report · FR2 Watch · FR3 Replay · FR4 Alert. The map may drop a point; the history may not.

![C4 level 1.](diagrams/video-c4-context.pdf){width=90%}

# Stage 2: Back-of-the-envelope

::: {.key title="Top-3 number 1: ingest"}
1 M/s × 300 B = **300 MB/s**, 900 MB/s replicated. *Say:* "That rules out a database row per position; it's a log."
:::

::: {.key title="Top-3 number 2: the live state is small"}
2 M × 200 B = **400 MB**. *Say:* "The map's data fits in memory; the history is what's big."
:::

::: {.key title="Top-3 number 3: the history"}
≈ 10^12^ positions a month × ~50 B ≈ **52 TB a month**, 1.25 PB for two years. *Say:* "Columns on object storage, laid out for the
questions it will be asked."
:::

![The freshness budget.](diagrams/video-budget.pdf){width=95%}

# Stage 3: API and data

```json
PUBLISH v/v-311/pos
{"seq": 9402, "epoch": 2,
 "t": "2026-11-22T18:00:04.120Z",
 "lat": 40.7484, "lng": -73.9857,
 "speed": 11.2, "heading": 184,
 "lane": "latest"}
```

`WS /v1/map` (viewport, zoom → snapshot, then deltas or counts) · `GET /v1/vehicles/{id}/track?from&to` (every fix by seq, at a pinned
snapshot) · a separate safety topic to dispatch.

![Conceptual model.](diagrams/video-erd-chen.pdf){width=95%}

![Physical model.](diagrams/video-erd-physical.pdf){width=95%}

# Stage 4: High-level design

![V1: a log and a lake.](diagrams/video-base-v1.pdf){width=100%}

![V2: the live view (SD-03's hot path).](diagrams/video-base-v2.pdf){width=100%}

![V3: a safety lane and a replay API.](diagrams/video-base-v3.pdf){width=100%}

| Where a position waits | Bound | When it fills |
|---|---|---|
| The vehicle's buffer | 6 h ring | drop oldest, count it |
| The gateway session | inflight window | the vehicle backs off |
| The log | 3 days | lag pages |
| The updater | checkpointed state | resume from offsets |
| The map push | 1 s tick | drop deltas, resend snapshot |

![The live path, numbered.](diagrams/video-flow-live.pdf){width=100%}

![The history path, numbered.](diagrams/video-flow-history.pdf){width=100%}

# Stage 5: Components and technologies

![The vehicle uplink.](diagrams/video-c4-comp-uplink.pdf){width=100%}

![The state updater.](diagrams/video-c4-comp-updater.pdf){width=100%}

![The map API.](diagrams/video-c4-comp-map.pdf){width=100%}

<!-- stack:sections -->

## Telemetry log: Kafka, keyed by vehicle ID

*How it is built.* Topic `positions`, partition = hash(vehicle); a separate `safety` topic. Three days on the brokers. 300 MB/s at peak, 900 MB/s with replication. Keying by geo cell was rejected: a vehicle crossing a cell boundary would change partitions, losing per-vehicle order, and a stadium's cell would be one hot partition.

*Why Kafka, 512 partitions, keyed by vehicle ID:* Even load, and each vehicle's messages in order on one partition.

*Rejected:*

- **Keying by geo cell**: Hot partitions; a moving vehicle loses its order.
- **Google Pub/Sub**: An honest equal with ordering keys.

*Course:* building-blocks course, part 10 §10.2 and §10.6 (partitioned logs, ordering).

## Live store: the SD-39 index, holding vehicles instead of drivers

*How it is built.* vehicle → (cell, position, seq) and cell → vehicles, with per-cell change counters. Older seq is dropped. The same design as SD-39's location index, at resolution 9 because the map zooms further in. Hot cells (> 300 vehicles) are split further; each cell also keeps a count at resolutions 6 and 7 for zoomed-out maps.

*Why Go service, in memory, H3 res 9, per city:* Only the latest matters, and 2 M vehicles fit in 400 MB.

*Rejected:*

- **Redis GEO**: No per-cell change feed, no expiry per member.
- **The history lake**: Minutes behind, built for scans.

*Course:* building-blocks course, part 6 §6.5 (hot keys) and SD-39 (location index).

## Map API: viewports subscribe to cells

*How it is built.* A viewport maps to cells at its zoom's resolution; each second the server pushes changes, or counts when zoomed out. About 5,000 concurrent viewers. At city zoom a viewport is ~100 resolution-7 cells sent as counts; at street zoom ~50 resolution-9 cells sent as vehicles. A viewer pans: subscribe the new cells, send their snapshot, then deltas.

*Why Go, WebSockets, a 1 s push tick:* Deltas for subscribed cells cost far less than every client polling.

*Rejected:*

- **Polling a bounding box**: 5,000 scans of the hottest cells a second.
- **Every vehicle in view**: 200,000 points at city zoom.

*Course:* building-blocks course, part 11 §11.6 (push) and part 10 §10.10 (fan-out).

## History lake: Iceberg, partitioned by day and vehicle bucket

*How it is built.* Partitioned by (event day, hash(vehicle) mod 256), sorted by vehicle and seq; late positions go to their event day. About 52 TB a month at ~50 bytes a position, 1.25 PB for two years. ML training reads whole days in bulk; audits read one bucket and filter. Snapshots pin what a replay read.

*Why Iceberg on GCS, Parquet, day × 256 vehicle buckets:* One vehicle's hour becomes one bucket and a range read.

*Rejected:*

- **Arrival-hour partitions**: One replay scans everyone; late fixes land in the wrong hour.
- **A time-series database**: Not for 10¹² positions with per-vehicle replay.

*Course:* building-blocks course, part 7 §7.10 (blob layout) and part 14 §14.9 (columnar storage).

<!-- /stack:sections -->

## The stack on one page

<!-- stack:summary -->

| Container | Choice | Rejected | The deciding reason |
|---|---|---|---|
| Telemetry log | Kafka by vehicle ID | keyed by cell, Pub/Sub | per-vehicle order; even load |
| Live store | in-memory H3, per city | Redis GEO, the lake | latest only; per-cell change feed |
| Map API | WebSockets, cell subscriptions | polling, all points | deltas per cell; counts when zoomed out |
| History lake | Iceberg, day × bucket | ingest-hour partitions, TSDB | one vehicle's hour is a range read |

Each fix in Stage 6 rejects one tool by name:

| Deep dive | Rejected | Because |
|---|---|---|
| 6.1 | Writing every arriving position to the live store | a three-minute-old buffered fix overwrites the position from one second ago. |
| 6.2 | Keying the log by geo cell | a stadium's cell becomes one hot partition and vehicles lose their order as they move. |
| 6.3 | Clients polling a bounding box | 5,000 viewers scan the hottest cells every second. |
| 6.4 | Flushing the buffer oldest first | the map stays three minutes behind for the whole flush, and safety events queue behind history. |
| 6.5 | Partitioning history by arrival time | a vehicle's hour is spread over every file that arrived late, and one replay scans everyone. |
| 6.6 | Consumer-lag dashboards | lag can be zero while a vehicle on the map is 40 seconds stale. |

<!-- /stack:summary -->

## When you don't need all this

Below about 5,000 vehicles (2,500 writes a second, twice): one PostgreSQL with a latest table upserted by sequence and a history
table partitioned by day, and a PostGIS map. Keep the sequence numbers and the lanes on the vehicle regardless.

# Stage 6: Deep dives

## 6.1 Out of the tunnel (the crux)

![Latest first; backfill to history.](diagrams/video-seq-ch1-tunnel.pdf){width=85%}

Keyed state holds the last sequence per vehicle; anything at or below it goes to history only; the live store also compares on
write. Timestamps cannot order: arrival time reverses backlogs, the vehicle's clock jumps, and two fixes can share a millisecond.

## 6.2 Downtown at six

The log is keyed by vehicle (even load, per-vehicle order). The live store indexes resolution-9 cells, keeps counts at 6 and 7, and
splits hot cells to resolution 10. Keying by cell would make downtown one hot partition and split each moving vehicle's order across
partitions.

| Zoom | Resolution | Sent |
|---|---|---|
| City | 6 | ~30 counts |
| District | 7 | ~100 counts |
| Neighbourhood | 9 | vehicles, clustered |
| Street | 9–10 | vehicles |

## 6.3 Five thousand viewers

A viewport becomes cells; each map pod subscribes once per cell to the live store's change feed and pushes each viewer only what
changed, every second; a pan subscribes new cells and sends a snapshot. Downtown with 3,000 viewers costs one feed and 3,000
sockets, not 3,000 scans a second.

## 6.4 A city comes back

```
on connected:
    send_all(safety_queue)          # own topic
    send(latest_position, lane = latest)
    rate = 50 / s
    for m in buffer.oldest_first():
        send(m, lane = backfill); throttle(rate)
        if broker.retry_after: rate = max(5, rate / 2)
        if safety_queue: send_all(safety_queue)
```

Safety in a second, the map current in seconds, nine million backfill messages to history over about two minutes; backfill fails
the sequence filter, so the live path never sees it.

## 6.5 One vehicle, one hour

```
snap = lake.snapshot_now()            # pin it
day = date(t_from)
b = hash(vehicle) % 256
rows = read(snap, day=day, bucket=b,
            vehicle=vehicle, t in [t_from, t_to])
rows = dedup_by(rows, (epoch, seq))
return sort_by(rows, (epoch, seq))
```

| Layout | Read | Time |
|---|---|---|
| By arrival hour | ≈ 3.5 TB | an hour |
| By event day | ≈ 1.7 TB | minutes |
| **Day × 256 buckets, sorted** | ≈ 7 GB, then ≈ 50 MB | **≈ 10 s** |

## 6.6 Forty seconds stale (observability)

![V4: a freshness probe.](diagrams/video-base-v4.pdf){width=100%}

A canary vehicle per city publishes through the real gateway, drives a route across cells, is watched by a probe viewer on every map
pod, raises a safety event every ten minutes, and has its history replayed hourly. With age-on-screen reported by browsers and
per-pod freshness, a pod whose subscription silently stopped pages within seconds, while Kafka lag stays at zero.

| SLI | Target |
|---|---|
| Canary visible on every pod | p99 ≤ 2 s |
| Safety canary to dispatch | p99 ≤ 1 s |
| Received positions in history | 100 % (daily count reconciliation) |
| One-vehicle replay | p95 ≤ 10 s |

# Stage 11: The close

> **What:** one log by vehicle, a live view by cell, a history by vehicle, lanes on the vehicle. **Trade-off:** two consumers and a
> vehicle agent to build, for a fresh map and an exact history. **Risk:** a map that is stale while every stage is healthy; hence
> canaries. **Next:** reuse: three of these boxes already exist in SD-03, SD-39 and SD-29.

# Stage 12: Self-check

| Area | Weak | Strong | Exceptional |
|---|---|---|---|
| Split | one table | live and history | one log, two views, said as SD-03's split |
| Order | arrival | timestamps | (epoch, seq) from flash, filtered in two places |
| Keys | by region | by cell | log by vehicle, index by cell, hot-cell split |
| Map | all dots, polling | thinning | zoom → resolution; cell subscriptions |
| Recovery | flush in order | rate limits | three lanes; backfill to history only |
| Operations | lag | latency | canaries through every map pod |

\newpage

# One-page cheat card

- **Scale:** 10^12^ positions a month (52 TB); 2 M vehicles; 1 M/s at rush hour; 100,000 vehicles flushing after an outage.
- **Thesis:** one log by vehicle, read twice; sequences decide newer; lanes decide first.
- **Reused:** SD-03 (split), SD-39 (H3 index), SD-29 (devices, backoff), SD-98 (pinned history).
- **Mechanisms:** M1 one log two views · M2 (epoch, seq) · M3 cells at three resolutions · M4 lanes · M5 cell subscriptions.
- **Stack:** EMQX gateway · Kafka by vehicle · Flink updater · in-memory H3 live store · Go WebSocket map · Iceberg lake · Trino replay.
- **Challenges:** out of the tunnel · downtown at six · 5,000 viewers · a city comes back · one vehicle, one hour · forty seconds stale.
