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

## Booklet-length solutions

Longer, illustrated answer keys, built to PDF. Same stage layout, more depth per stage, plus an
internals appendix for the "how does that tool actually work?" probe.

| ID | Problem | Source | What's in it |
|---|---|---|---|
| [SD-47](SD-47-ticket-booking/SD-47_Ticket_Booking_Reference_Design.md) | Ticket booking under contention | `SD-47-ticket-booking/` | 60-minute script (pace `hour`), 21 PlantUML diagrams, seven deep dives (the same-millisecond click, the lottery waiting room, hold expiry, the expired-hold-paid case, the seat map at 10k shoppers, concurrent on-sales, degradation), three worked requirement drips, PostgreSQL / Redis / Kafka / CDN / card-payment internals, a one-page cheat card |

Build the PDF (needs `pandoc`, `xelatex`, `plantuml`, `rsvg-convert`; the PDF is gitignored):

```bash
solutions/SD-47-ticket-booking/build-sd-booklet.sh SD-47_Ticket_Booking_Reference_Design             # diagrams + PDF
solutions/SD-47-ticket-booking/build-sd-booklet.sh SD-47_Ticket_Booking_Reference_Design --no-diagrams
```

For a guide in the *style* of the URL-shortener and notification-platform reference interviews (cover
band, coloured callouts, hand-drawn SVG diagrams), use the HTML kit in [`../pdf-kit/`](../pdf-kit/README.md).

**In a practice session** (`CLAUDE.md` §16) the coach reads these one stage at a time and scaffolds
from them. In a certifying session they stay closed until the debrief.

## Coming next

The next solutions in the queue, by how often they're asked: SD-12 notification platform · SD-20
distributed cache · SD-18 file sync · SD-39 ride matching ·
SD-42 LLM inference serving · SD-55 design review (inverted) · SD-58 SLO design. Contributions
welcome — follow this layout ([CONTRIBUTING](../CONTRIBUTING.md)).
