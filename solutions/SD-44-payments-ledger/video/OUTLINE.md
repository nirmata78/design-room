# SD-44 · Payment processing and the double-entry ledger — reference-solution video outline

Target level: staff (manager layer dropped in the compact cut) · **Compact cut** (GUIDELINES §3.4) · Target length: 75–80 min · Word budget: ≈ 9,700 spoken · 138 logical slides · 546 reveal frames.
Rebuilt 2026-11-22 from the 2026-11-20 / 11-22 retrofit (snapshot in `.v2-retrofit-2026-11-22/`, removed after QA). Author feedback of 2026-11-22 folded in: the partition key and a million one-time accounts, the state machine and both data models built up step by step, why Go and how it compares, gateway or direct processor, Debezium against its alternatives.

## Thesis and definition

- **Thesis:** at-least-once delivery, one effect per intent, a state for not knowing yet, and a reconciliation that finds what the rest missed, on an append-only double-entry journal.
- **Definition to say aloud:** a payment system turns an intent to pay into exactly one movement of money, records every movement as balanced, immutable entries, and keeps its books in agreement with the outside parties that move the money.
- **Hook:** the truth about a payment arrives over months; the answer is due in two seconds.

## Scale line (GUIDELINES §3.1)

9 billion payments a month (290 M a day, 3,300/s average) · peak 10,000/s on a sale-day evening, one merchant at 5,000/s · seven years of entries, about 2.9 × 10¹². Every estimate names which of these it starts from.

## 0 · What this question grades

| Axis | Weak signal | Strong signal |
|---|---|---|
| Requirements | "Charge the card and store it" | what must never happen, in order; how the outside parties fail |
| Correctness | balance column, floats, "retries are safe" | double entry, derived balances, key inserted first |
| Trade-offs | "a distributed transaction with the bank" | why it is unavailable; a state for unknown and its cost |
| Depth | "retry with backoff" | timeout walk, outbox, the partition key, the hot account |
| Operations | API uptime | unknown count and age, a zero-sum ledger, owned breaks |

## 1 · Requirements and scope

- Six clarifying questions: latency; who moves the money (**gateway or direct is the candidate's call**); the ledger rule; auditability; refunds and disputes; priorities.
- FR1 pay · FR2 adjust · FR3 notify · FR4 reconcile · FR5 explain. NFR: 0 double charges, < 2 s or pending, 99 % of unknowns in 15 min, breaks owned in a day.
- IN: authorise, capture, void, refund, chargeback, webhooks, ledger, reconciliation, 50 currencies. OUT: fraud scoring, card data, FX, onboarding/KYC, payouts.
- C4 context closes the chapter. The core is four things.

## 2 · Estimates

| Number | From | Arithmetic | Label | Decides |
|---|---|---|---|---|
| Entries | peak | 10,000 × 4 = 40,000/s | derived | one primary will not take it |
| Primaries | peak | 10,000 ÷ ~1,200 commits/s ≈ 9 | illustrative | 64 logical partitions on ~10 primaries; **key by merchant** |
| Per day | monthly | 3,300 × 86,400 ≈ 2.9 × 10⁸ | derived | settlement files of hundreds of millions of lines |
| Seven years | retention | 2.9 × 10¹² entries × 200 B ≈ 580 TB | illustrative | hot partitions, cold archive |
| Keys | daily | 2.9 × 10⁸ × 7 × 300 B ≈ 600 GB | illustrative | keys expire after 7 days |
| Hot merchant | peak | 5,000/s against ≈ 670/s per row lock | illustrative | append-only entries |
| Latency | target | 90 ms ours + 1.5 s processor, 2 s | target | our code is microseconds in a second-long call |
| Unknowns | peak | 0.1 % × 10,000 = 10/s | illustrative | the inquiry job is a service |
| Settlement | daily | 2.9 × 10⁸ lines at 1 M/s ≈ 5 min | illustrative | batch join |

## 3 · Theory

Six parts as in GUIDELINES §4. Five mechanisms: M1 idempotency key first · M2 state machine with UNKNOWN and inquiry · M3 immutable double-entry journal, partitioned by the owner · M4 transactional outbox read from the log · M5 reconciliation with owned breaks. Mechanisms at work as a table; one protocol-level sequence (one capture as one transaction). Options matrix A–F, pick D, with its cost. Failure catalogue → six challenges.

## 4 · API and entities

Pay (wire format), the state machine **built up state by state (12 steps)**, the rest of the surface as one tagged table, Chen model and physical model **built up entity by entity**, a worked entry example, three rules about money.

## 5 · High-level design

| Version | Adds | Objection it answers | Objection it leaves |
|---|---|---|---|
| V1 | merchant, API, service, database, processor, synchronous | none | timeout, retry, two charges; no history |
| V2 | processor adapter; key first; attempt before the call; journal | the above | merchants not told; unknowns pile up; books may differ |
| V3 | outbox relay + log, webhooks, inquiry job, reconciliation, finance ops | the above | the eight → six challenges |
| V4 (challenge 4) | balance projector | the hot merchant | |

Container walk (7 rows with numbers), **the partition-key slide (account, payment, merchant, time)**, flow and sequence per FR: pay (flow + sequence), refund, explain here; notify in challenge 3's sequence; reconcile in challenge 5's.

Canonical diagrams: context (chapter 1); containers (V1–V3, then deltas `new=`, `flow=`, `badges=`, `attack=`, `fix=`, `focus=`, technologies via `OVERRIDE`); three component views (payment service, ledger database, reconciliation).

## 5.1 · Components and technologies

Container view with technologies; component views of the three containers the challenges open; technology slides from `stack.json` (ledger database, outbox relay); **language and runtime comparison** (Go, Java virtual threads, Spring WebFlux, Python, Rust); **gateway or direct processor** table with break-even arithmetic; processor adapter; the stack on one slide. No drill interlude (compact cut).

<!-- stack:outline -->

| Container | Choice | How it is built | Rejected | Theory part |
|---|---|---|---|---|
| Ledger database | PostgreSQL 16, 64 partitions by merchant, a synchronous standby each | The key is the owner, the merchant, not the account: a capture touches three accounts and would span partitions | Partitioning by account; TigerBeetle, a ledger database; A key-value store, or a log as the truth | 03 |
| Runtime | Go services, one static binary each, context deadlines through every call | The processor takes a second, the commit a few milliseconds, our own code microseconds | Java 21+ with virtual threads (Spring Boot, Quarkus); Spring WebFlux; Python; Rust | 02 |
| Outbox relay and log | Outbox table, Debezium (change data capture), Kafka | The outbox row commits with the payment | A polling relay; Own consumer of logical decoding; Managed capture (DMS, Datastream) | 06 |
| Processor adapter | A Go adapter per processor behind one port: a reference on every call | The port has authorise, capture, void, refund, inquire and read settlement | A shared generic client; A gateway only, at this volume; Retrying every timeout | 07 |
| Reconciliation | A Spark batch over the processor files, expectations in PostgreSQL, a break workflow with owners | The ledger produces, per processor and day, what it expects to be settled, by reference and net of fees | Matching on amount and time alone; Comparing daily totals | 08 |

Fix-slide rejections: 1: Treating a timeout as a decline; 2: Check, then insert, for the idempotency key; 3: Publishing to the broker after the commit; 4: One balance row updated on every payment; 5: Matching on amount and time alone; 6: Alerting on the error rate.

<!-- /stack:outline -->

## 5.2 · When you don't need all this (ALTERNATE)

A gateway, one PostgreSQL primary with a synchronous standby, a polled outbox; no Kafka, no Debezium, no partitions. Gives up: one writer (~1,200 commits/s), no replayable log, the gateway's fee and outages, failover loses the standby's lag if asynchronous. Crossover from the scale line: below about 300 payments a second and $10 million a month; we are at 10,000/s and 9 B a month.

## 6–7 · Challenges (6)

| # | Challenge | Fix, one level down | Version |
|---|---|---|---|
| 1 | The bank timed out | attempt row before the call; UNKNOWN by conditional update; inquiry by reference; breaker, never fail over an unknown | none |
| 2 | Three retries at once | unique insert of the key with a request hash in the payment's transaction; 409 / stored / 422; a stuck row is an unknown | none |
| 3 | A crash between the ledger and the event | outbox row in the transaction; Debezium reads the WAL via a slot, commit order, at least once; the slot as the new risk | none |
| 4 | The hot merchant, and a million one-time accounts | insert-only entries; projector; payout writer; **an account is a row, not a partition**; TigerBeetle as the upgrade | V4 |
| 5 | 999,998 against 1,000,000 | expectations by reference, line-by-line match, owned breaks; a spike is an incident: kill switch, reversing entries | none |
| 6 | How would you know before finance does? | approval rate by segment, UNKNOWN age, slot lag, unmatched by age, zero-sum, a probe; symptom pairs | none |

Refunds and chargebacks and the bad release (old challenges 5 and 7) are folded into the FR2 sequence and challenge 5; the booklet keeps them as full deep dives.

## 8 · Recap

Version four with M-badges; five paths in one sentence each; common mistakes; the four sentences; the thesis.

## Canon check

| Point | Covered at |
|---|---|
| Idempotency keys, request hash, 409/422 | theory M1; challenge 2 |
| Double entry, integer minor units, derived balances | theory M3; chapter 4 |
| State machine with UNKNOWN, inquiry, reversal by reference | chapter 4 states; challenge 1 |
| Outbox, at-least-once, consumer dedup | challenge 3 |
| Reconciliation against settlement files | challenge 5 |
| Hot accounts, partition key | chapter 5 partition slide; challenge 4 |
| Refunds and chargebacks as new transactions | FR2 sequence; challenge 5 second push; booklet |
| PCI scope, tokenisation | scope; gateway slide |
| Gateway versus processor | 5.1 slide; 5.2 |
| Multi-currency, FX | dismissed aloud (out of scope) |
| Fraud scoring, payouts | dismissed aloud (out of scope) |

## From the old version

| Reused | New | Dropped |
|---|---|---|
| clarifying answers, estimates, theory mechanisms, challenge narration (1–4, 6, 8), sequences, ERD content | scale line, 5.2, partition-key slide, runtime and gateway comparisons, Debezium alternatives, component views, V4, one-strip fix slides | build-cost chapter (AUX), drill interlude, challenges 5 and 7 as separate challenges, challenge 6's old wording |

## Revision log

2026-11-22 · compact cut · stack.json is the only place a technology is written · first unit revealed with the opening line on 15 slides (gen.py) · the layout gate passes with 0 failures.
