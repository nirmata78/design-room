# Reference solutions — how a strong candidate runs the round

Stage-by-stage answer keys for the problems you are most likely to face. Each one is written the way
a strong candidate would run a 45–60-minute round: **what to ask, which numbers to compute and what
they decide, the API and data model, the design and its walk-through, the deep dives, the mid-round
curveball, failure modes, SLOs and cost, what changes by level, and the four-sentence close.**

{: .spoiler }
> **Run the round first.** A solution read before a mock turns the mock into a recital and the score
> into fiction. The loop that works: run the question cold in the simulator → get the report → read the
> solution at the stages the report flagged → re-run weeks later.

## The five most-asked

| ID | Problem | The insight in one line | Asked most at | Theory it leans on |
|---|---|---|---|---|
| [SD-25](SD-25-rate-limiter.md) | Distributed rate limiter | the limiter's availability and latency matter more than its accuracy — decide locally, reconcile async | Google, Meta, Amazon, Microsoft | [8](../theory/08-reliability-and-operations.md), [7](../theory/07-correctness-under-failure.md) |
| [SD-08](SD-08-news-feed.md) | News feed / home timeline | hybrid fan-out with a threshold: push for normal accounts, pull for celebrities | Meta, Google | [5](../theory/05-caching.md), [6](../theory/06-messaging-and-streams.md) |
| [SD-09](SD-09-chat-messaging.md) | Chat / messaging | mailbox first, socket second: durable sequenced log + per-device cursors | Meta, Microsoft | [9](../theory/09-real-time-and-connections.md), [6](../theory/06-messaging-and-streams.md) |
| [SD-15](SD-15-distributed-kv-store.md) | Globally distributed KV store | consistency is a per-operation product choice; say what each level costs | Google, Amazon, Microsoft | [4](../theory/04-replication-and-consistency.md), [3](../theory/03-partitioning-and-storage.md) |
| [SD-44](SD-44-payments-ledger.md) | Payments & double-entry ledger | exactly-once doesn't exist across the bank boundary — idempotency, pending states, reconciliation | Amazon, fintech, Google | [7](../theory/07-correctness-under-failure.md) |

**Why these five.** Between them they are the flagship question at every major company class in the
[bank](../Question-Bank.md), and they cover the five recurring hard problems of system design:
**fan-out** (SD-08), **real-time delivery and ordering** (SD-09), **distributed consistency** (SD-15),
**correctness under failure** (SD-44) and **hot-path protection** (SD-25). Master these and most other
questions are recombinations.

**Mock-round videos:** [VIDEOS.md](VIDEOS.md) lists each problem published so far.

## How every solution is laid out

| Stage | Clock (60 min) | Section |
|:-:|---|---|
| 1 | 0:00–0:06 | Clarify — *I ask / they answer / why it matters*, scope, non-functional numbers |
| 2 | 0:06–0:11 | Estimation — three numbers, each with its consequence |
| 3 | 0:11–0:17 | API and data model |
| 4 | 0:17–0:27 | High-level design (diagram) and the end-to-end walk-through |
| 5 | anywhere | Technology choices — mechanism and trade-off |
| 6 | 0:27–0:45 | Deep dives — the crux first |
| 7 | as given | The mid-round requirement, as a delta |
| 8 | 0:45–0:50 | Failure modes |
| 9 | 0:50–0:54 | SLOs, observability, cost |
| 10 | when asked | The level layer — Staff vs EM vs Director |
| 11 | 0:55–0:57 | The close — four sentences |
| 12 | after | Self-check |

The boxes: **Say it in the room** — words you can use nearly verbatim · **Why?** — the reasoning
behind a term or decision · **The number that matters** · **Trap** — what breaks under a follow-up ·
**Level lens** — how the bar shifts by level. Method in full: [The interview method](../theory/01-interview-method.md).

## Videos

**Reference-solution videos** exist for SD-03 in the **current format** (2026-11-28: 40–60 min, six chapters, the design as a
C4 container view that evolves through interviewer challenges) and, in the older ten-chapter format (60–100 min), for SD-29,
SD-39, SD-97, SD-98, SD-08, SD-24, SD-44, SD-47, SD-77, SD-82, SD-94, SD-95, SD-96, SD-99 and SD-59; see [VIDEOS.md](VIDEOS.md).
Each is rebuilt with `/reference-solution SD-NN`.

**Mock-round videos.** A narrated mock round per solution at the **L6 Engineering Manager** bar (1080p, interviewer, candidate, key lines
spoken slower, coach, burned-in captions, chapters): the design, then four manager follow-ups. Each lives in
`SD-NN-<name>/video/` with its slides, C4 and sequence diagrams and script, and rebuilds with `video/build-video.sh`.
The MP4s and frames are gitignored. Built with the `system-design-video` skill.

| ID | Video folder | The four follow-ups |
|---|---|---|
| SD-09 | `SD-09-chat-messaging/video/` | encryption announced on stage · a deploy restarts a zone · a burning on-call · storage cost −40% |
| SD-15 | `SD-15-distributed-kv-store/video/` | build or buy · a region goes dark · "strong everywhere" · the transfer bill |
| SD-25 | `SD-25-rate-limiter/video/` | a customer wants no limits · a zero-limit policy push · billing from the limiter · the decision-log bill |

## Booklet-length solutions

Longer, illustrated answer keys, built to PDF. Same stage layout, more depth per stage, plus an
internals appendix for the "how does that tool actually work?" probe.

| ID | Problem | Source | What's in it |
|---|---|---|---|
| [SD-47](SD-47-ticket-booking/SD-47_Ticket_Booking_Reference_Design.md) | Ticket booking under contention, Staff bar | `SD-47-ticket-booking/` | The written companion to the reference-solution video ([notes](SD-47-ticket-booking/video/README.md)): thesis and what is graded, a theory chapter (seven mechanisms, an options matrix), the design in three versions, eight challenges (the same-millisecond click, the hold that outlives its owner, the expired hold that is paid, a million at the door, a fair line and bots, the seat map, mid-sale changes, observability), the build cost, a canon check, and PostgreSQL / Redis / Kafka / signed-token appendices |
| [SD-09](SD-09-chat-messaging/SD-09_Chat_Messaging_Reference_Design.md) | Chat and messaging, Staff bar | `SD-09-chat-messaging/` | The written companion to the video: 34 figures shared with it where possible, ten deep dives (ordering and leader failover, the lost ACK, groups, receipts, reconnect storms, a month offline, the sync races, storage and buckets, degradation, regions), four worked deltas, WebSocket / Raft / wide-column / log and CDC / Redis / push-service / E2E internals, a one-page cheat card |
| [SD-24](SD-24-distributed-lock/SD-24_Distributed_Lock_Reference_Design.md) | Distributed lock service, Staff bar | `SD-24-distributed-lock/` | The written companion to the reference-solution video: 43 figures shared with it where possible, seven deep dives (the paused holder and the fencing token, a resource that cannot check, clocks and leases, partition and disaster recovery, the top of the hour, a hot name, observability), each with what the first draft glosses over, five worked deltas, consensus / leases and clocks / coordination-store / conditional-write / idempotency / linearizability-testing internals, build cost in engineer-months, a one-page cheat card |
| [SD-03](SD-03-ad-click-aggregation/SD-03_Ad_Click_Aggregation_Reference_Design.md) | Event counting & billing rollups (ad clicks, usage metering), Staff bar | `SD-03-ad-click-aggregation/` | **The pilot of the 2026-11-28 format** (six chapters, C4-first, challenge-driven; generated from the video sources): event IDs and dedup, event time and a 48-hour cutoff, one aggregation run twice (Flink streaming and batch), replace-not-increment (ClickHouse, Iceberg), versioned corrections, reconciliation; six challenges |
| [SD-29](SD-29-device-fleet/SD-29_Device_Fleet_Reference_Design.md) | Device-fleet control plane (IoT), Staff bar | `SD-29-device-fleet/` | Compact-cut companion: desired vs reported state, cohort waves with automatic halt, A/B slots and a watchdog, jittered reconnects, fleet census |
| [SD-08](SD-08-news-feed/SD-08_News_Feed_Reference_Design.md) | News feed / home timeline, Staff bar | `SD-08-news-feed/` | The written companion to the reference-solution video: figures shared with it, eight deep dives (celebrity, threshold, deletes, duplicates, lost shard, slow ranker, catch-up, observability), the EM layer, internals appendices |
| [SD-94](SD-94-denylist-system/SD-94_Denylist_System_Reference_Design.md) | Blocking / denylist system, Staff bar | `SD-94-denylist-system/` | The written companion to the reference-solution video: figures shared with it, seven deep dives (a node that was offline, order and overlap, the bad push, stale or no control plane, a list that does not fit, a slow external source, observability), each with what the first draft glosses over (version order against commit order, a state digest, drain flapping, the gate's blind spot, filter rebuilds), five worked deltas, versioned-distribution / prefix-trie / Bloom-filter / staged-rollout internals, build cost in engineer-months, a one-page cheat card |
| [SD-44](SD-44-payments-ledger/SD-44_Payments_Ledger_Reference_Design.md) | Payments & double-entry ledger, Staff bar | `SD-44-payments-ledger/` | The written companion to the reference-solution video (compact cut, six challenges in the video, eight deep dives here; adds the partition key, runtime, gateway or processor and a ledger ladder): figures shared with it, the internals of idempotency, the outbox, inquiry and reconciliation |
| [SD-96](SD-96-url-shortener/SD-96_URL_Shortener_Reference_Design.md) | URL shortener, Staff bar | `SD-96-url-shortener/` | The written companion to the reference-solution video: components and technologies (PostgreSQL, etcd, Redis Cluster, ristretto, Kafka, Flink, ClickHouse, each against named alternatives), eight deep dives (two servers and one code, codes in order, a viral link, 301 or 302, a takedown in five minutes, counting off the redirect, a region lost, observability), each with what the first draft glosses over (aliases stealing future codes, the idempotency table, lost lease responses, the cache-fill race against a takedown, negative caching against replication lag), counter-range / Feistel / single-flight / lifetime-budget internals, a one-page cheat card |
| [SD-39](SD-39-ride-matching/SD-39_Ride_Matching_Reference_Design.md) | Nearby drivers & ride matching, Staff bar | `SD-39-ride-matching/` | Compact-cut companion: an in-memory H3 index, fenced conditional claims, offer leases, ETA ranking, batch assignment, probe trips |
| [SD-97](SD-97-fleet-telemetry/SD-97_Fleet_Telemetry_Reference_Design.md) | Device telemetry & live location map, Staff bar | `SD-97-fleet-telemetry/` | Compact-cut companion, a combination of SD-03, SD-39 and SD-29: one log by vehicle, two views, lanes, cell subscriptions, a history laid out for replay |
| [SD-98](SD-98-replay-platform/SD-98_Replay_Platform_Reference_Design.md) | Reproducible replay & regression-gate platform, Staff bar | `SD-98-replay-platform/` | The written companion to the compact-cut video: pinned manifests, a deterministic harness, Merkle stage keys and a content-addressed cache, Kueue quotas, open against closed loop, paired-interval gates, a gate auditor; six deep dives |
| [SD-82](SD-82-credit-decisioning/SD-82_Credit_Decisioning_Reference_Design.md) | Instant credit at the point of sale, Staff bar | `SD-82-credit-decisioning/` | The written companion to the reference-solution video: components and technologies (PostgreSQL, etcd, Redis Cluster, ristretto, Kafka, Flink, ClickHouse, each against named alternatives), eight deep dives (a slow bureau, a bureau down for everyone, a dropped phone, funding after booking, explaining a decline later, a new model, the identity vault, observability), the missing-data policy table, the decision record and replay, champion and challenger, a one-page cheat card |
| [SD-95](SD-95-loan-servicing/SD-95_Loan_Servicing_Reference_Design.md) | Instalment loan servicing, Staff bar | `SD-95-loan-servicing/` | The written companion to the reference-solution video: double entry with a balance projection, UNKNOWN and RETURNED payment states, the rail budget on the 1st, refunds mid-loan, three-way reconciliation, build cost, a one-page cheat card |
| [SD-99](SD-99-webhook-delivery/SD-99_Webhook_Delivery_Reference_Design.md) | Outbound webhooks and partner event delivery, Staff bar with the EM layer | `SD-99-webhook-delivery/` | The written companion to the reference-solution video: an outbox, a queue per endpoint as rows claimed under a cap, full jitter with a breaker and a ramp, signing and egress control, versioned public events and the team seams that own them, buy against build, a one-page cheat card |
| [SD-59](SD-59-team-decomposition/SD-59_Team_Decomposition_Reference_Design.md) | Multi-team decomposition and API contracts, Principal / senior EM bar | `SD-59-team-decomposition/` | The written companion to the reference-solution video (compact cut, 2026-11-25 format): domain seams against layers, versioned contracts with consumer-driven tests, one owner per shared thing, an end-to-end skeleton by week four, split-health indicators. GitHub Markdown only; its SVGs were drawn by the retired PlantUML pipeline (re-cut pending). |
| [SD-77](SD-77-card-authorisation/SD-77_Card_Authorisation_Reference_Design.md) | Card authorisation & issuer processing, Staff bar | `SD-77-card-authorisation/` | The written companion to the reference-solution video: holds not debits, idempotency on the network reference, a per-account reserve, the model cut-off and fail-policy table, inline counters, rules as versioned data, stand-in advices, decision SLIs |

Rebuild a solution in the current format (issue #5: six chapters, C4 from one Structurizr workspace, the Markdown design
generated from the video sources; no PDF):

```bash
python3 .claude/skills/reference-solution/scripts/ref_solution.py all SD-03 --no-video   # diagrams → deck (layout gate) → Markdown
python3 .claude/skills/reference-solution/scripts/ref_solution.py video SD-03            # the narrated MP4 + .srt/.vtt (local only)
```

Solutions not yet re-cut keep their committed Markdown and SVGs; their old build scripts (PlantUML, booklet PDFs) were removed on
2026-11-28 and they are rebuilt only by re-cutting them in the new format (`/reference-solution SD-NN`).

For a guide in the *style* of the URL-shortener and notification-platform reference interviews (cover
band, coloured callouts, hand-drawn SVG diagrams), use the HTML kit in [`../pdf-kit/`](../pdf-kit/README.md).

**In a practice session** (`CLAUDE.md` §16) the coach reads these one stage at a time and scaffolds
from them. In a certifying session they stay closed until the debrief.

## Coming next

The next solutions in the queue, by how often they're asked: SD-12 notification platform · SD-20
distributed cache · SD-18 file sync · SD-39 ride matching ·
SD-42 LLM inference serving · SD-55 design review (inverted) · SD-58 SLO design. Contributions
welcome — follow this layout ([CONTRIBUTING](../CONTRIBUTING.md)).
