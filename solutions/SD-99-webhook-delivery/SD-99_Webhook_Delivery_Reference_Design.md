---
title: "SD-99 · Outbound Webhooks and Partner Event Delivery"
subtitle: "A reference solution for a system design round at the Staff bar, with the manager layer: an outbox so no event exists without its commit, a queue per endpoint kept as rows and claimed under a cap, retries spread with full jitter and earned back with a ramp, a signed and versioned consumer contract, and the team seams that keep that contract stable"
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

This is the **long answer key for question `SD-99`** in
[design-room](https://github.com/nirmata78/design-room), an open-source system design interview
simulator, and the written companion to its reference-solution video. It shows how a strong Staff
candidate (L6/L7) runs the round, and, marked auxiliary, the manager layer an engineering-manager round
adds: team seams, contracts between teams, buy against build.

The question is set in the world of the two questions before it. A point-of-sale lender originates loans
(SD-82) and services them (SD-95); merchants and a partner bank subscribe to what happens to those loans.
The design is general: replace "loan" with "order" or "subscription" and every mechanism holds.

**Three layers.** **Part I** explains the system in pictures, with no interview script. **Part II** is the
round, stage by stage: what to say, what to draw, and why; the seven **challenges** of the video are Stage
6 and go further here. **Part III** is the internals: the outbox, leases and skip-locked claims, backoff
arithmetic, signatures, egress control and schema evolution, at the depth an interviewer reaches when they
ask how a named mechanism works.

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

**About the numbers.** The scale line in Stage 1 is illustrative: 60 million events a month, 180 million
deliveries, a peak of 2,400 deliveries a second caused by a bank settlement file, 20,000 endpoints. Every
other number is arithmetic from it, labelled *illustrative*, *initial target* or *derived*. None is a
measurement or any company's figure, and this is not any company's design. Prices of managed services are
illustrative orders of magnitude, not quotes.

**Practise in three passes.** (1) Read Part I and Part II once. (2) Close the document and run the
simulator cold: `Read CLAUDE.md. Mock me: SD-99, fintech, em, full round.` (3) Debrief against the Stage 12
self-check, then reread only the sections where you fell short.

\newpage

# Part I: The system in pictures

## Vocabulary you need first

| Term | Meaning here |
|---|---|
| Event | A fact that happened to a loan, committed by its owner: *approved*, *booked*, *funded*, *refunded*, *paid*, *returned*, *paid off* |
| Endpoint | A URL a merchant or partner registered to receive events, pinned to a public API version |
| Subscription | An endpoint's interest in one event type |
| Delivery | One event to one endpoint: the unit of state, with its own attempts, timer and outcome |
| Attempt | One HTTP call for a delivery, with its status, latency and the first bytes of the answer |
| Outbox | A table in the producer's database where the event is written in the same transaction as the change |
| Fan-out | The step that turns one event into one delivery per matching endpoint |
| Cap | The maximum number of calls in flight to one endpoint |
| Lease | A time-limited claim on a delivery row; when it expires, another worker may take the row |
| Breaker | A per-endpoint switch that stops calls after repeated failures and lets probes through |
| At-least-once | Every event is delivered one or more times; the receiver makes the effect happen once |
| Egress proxy | The only way out of our network for delivery calls; it checks the address it connects to |
| Public version | A dated shape of the payload that an endpoint pinned; separate from the producer's internal event |

## What one event experiences

At 14:31 on a Saturday the servicing system records a $300 refund on loan `ln_5531`. In the same database
transaction it writes an outbox row: event `ev_8841`, type `loan.refunded`, sequence 7 for that loan. Within
half a second the relay publishes the row to the event log, keyed by the loan, and marks it sent. Fan-out
reads it, finds three subscriptions (the merchant's till, the merchant's accounting system and the partner
bank) and writes three delivery rows, each rendered to the version its endpoint pinned.

A dispatcher worker claims the till's row: the till has 2 of its 10 allowed calls in flight. It signs the
body with the till's secret, sends it through the egress proxy, and gets a 200 in 180 ms; the row is
delivered and an attempt is logged. The accounting system is down for the weekend. Its row is retried at a
random time below a ceiling that doubles each attempt; after five failures its breaker opens, and the row
waits without spending any worker. On Sunday evening a probe succeeds, the endpoint ramps back from one call
a second, and the refund arrives, in sequence order, with everything else it missed. The partner bank, in
its own pool, never noticed either of them.

![The baseline at the end of the round (V6), along the path of one event: commit with the outbox row, relay to the log, fan-out renders and writes rows, the dispatcher claims under a cap and sends through the egress proxy.](diagrams/video-base-final.pdf){width=100%}

## The central contrast

| | A message broker | This platform |
|---|---|---|
| Who sets the pace | The consumer pulls when ready | We push; the receiver gives no back-pressure |
| Who the consumer is | Our own service, trusted | A stranger's server: slow, down, wrong or hostile |
| Failure unit | The consumer group | Each endpoint, separately |
| How long a backlog lives | Minutes to hours | Up to 72 hours, durably |
| What the payload is | An internal message | A public contract, versioned and signed |

## Where the load lands

The average is small: 70 deliveries a second. The **peak** comes from a batch: the bank's settlement file
on the morning after a collection day posts 480,000 payments in about ten minutes (SD-95), which is 800
events a second and 2,400 deliveries a second. Even that is about 600 calls in flight. The load that
matters is not volume but **time held**: one endpoint answering in ten seconds holds forty times the
sockets of a healthy one. The design is shaped by the slow minority, not the busy average.

\newpage

# Part II: The round, stage by stage

| Stage | Clock (75 min, typing-adjusted) | What you produce |
|---|---|---|
| 1 Clarify | 0–12 | The scale line, six questions, four functional requirements, numbers on the non-functional ones |
| 2 Estimates | 12–21 | Little's law, the slow endpoint, the outage backlog |
| 3 API and data | 21–30 | Registration, the delivery on the wire, logs and replay; the delivery row |
| 4 High-level design | 30–45 | V1 → V3, the claim, the flows |
| 5 Why these choices | (inside 4) | The technologies; the alternate path (buy) |
| 6 Deep dives | 45–67 | Two or three of the seven challenges |
| 7–11 Wrap | 67–75 | Failures, SLOs, cost, the EM layer, the close |

# Stage 1: Clarify requirements

**The scale line, said once.** 60 M events a month from origination, funding and servicing; about three
matching subscriptions each, so 180 M deliveries a month, about 70 a second. Over 30 days of retention,
about 216 M attempt rows and 120 GB of payloads. The peak: 480,000 payments posted in ten minutes, 800
events and 2,400 deliveries a second, 34 times the average. 20,000 endpoints, about 3 % failing at any
moment. All illustrative.

| Question | The answer | What it changes |
|---|---|---|
| Who subscribes, and what do they do with an event? | Merchant tills and accounting systems, self-service; the partner bank, by contract | A forged approval releases goods: signatures matter. Self-service URLs are untrusted input: egress control |
| Must one loan's events arrive in order? | Not guaranteed; merchants can fetch current state | A sequence per loan, not a promise of order |
| How fast, and how long? | First attempt p99 under 5 s for a healthy endpoint; retry 72 h | A durable backlog of days |
| Exactly once? | At least once; say so | The event ID is part of the product |
| Payload, regions? | About 2 KB; one region first | Storage is small; a second region is an extension |
| Who owns the event schema? | The producing teams; merchants must not break | The public contract is separate from the internal event |

::: why
**Why ask what the merchant does with the event.** It turns "send a webhook" into a threat model. If a
till releases goods on `loan.approved`, a forged approval is fraud, and a duplicate refund is money. The
answer justifies signatures, sequence numbers and the advice to confirm high-value approvals by API.
:::

**Functional requirements.** **FR1** register an endpoint and subscribe it to event types (verified URL,
secret shown once, pinned version). **FR2** emit an event atomically with the state change. **FR3** deliver
to every matching endpoint, signed, with retries for 72 hours, then dead and visible. **FR4** see every
attempt, and redeliver one delivery or replay everything since a time at a chosen rate.

**Non-functional requirements (initial targets).**

| Requirement | Target | Why this number |
|---|---|---|
| Event loss after commit | zero | A lost approval stops a sale |
| First attempt, healthy endpoint | p99 under 5 s | A till is waiting |
| Effect of one endpoint's failure | under 1 s on anyone else's p99 | Isolation, written as a number |
| Retry window | 72 h, then dead and visible | A weekend outage at a merchant |
| Ingest availability | 99.95 % | Producers must never block on us |
| Calls to private addresses | never | Server-side request forgery |

**Scope.** In: outbox and relay, fan-out, delivery and retries, signing, egress control, the attempt log,
replay, the public contract and its versions. Out, named: partner SDK internals, a schema design tool,
webhooks we receive (SD-45), push to customers' phones (SD-12), a second region.

::: {.key title="The core is three things"}
A **durable event** before any delivery; **isolation** per endpoint; and the **consumer contract**: ID,
sequence, signature, version.
:::

![C4 level 1: origination and servicing produce events; the platform sends signed POSTs to merchant tills and accounting systems and loan-level events to the partner bank; developers register and replay; a key service holds the secrets.](diagrams/video-c4-context.pdf){width=96%}

# Stage 2: Back-of-the-envelope

::: {.key title="Top-3 number 1: Little's law at the peak"}
**Arithmetic.** 2,400 deliveries a second × 0.25 s mean answer time $\approx$ **600 calls in flight**.
**What it means.** The fleet is small. Capacity is not the risk.
**Say:** "Six hundred calls in flight at the peak. Volume isn't the problem; time held is."
:::

::: {.key title="Top-3 number 2: one slow endpoint"}
**Arithmetic.** A till vendor with 5 % of deliveries: 2,400 × 5 % = 120 a second; at our 10 s timeout,
120 × 10 = **1,200 calls in flight**, twice the whole fleet.
**How it changes the design.** A cap on in-flight calls per endpoint and pools per tier are mandatory.
**Say:** "One slow vendor would need twelve hundred sockets. So every endpoint gets a cap."
:::

::: {.key title="Top-3 number 3: a two-day outage"}
**Arithmetic.** An accounting system with 2 % of the 70-a-second average: 1.4 a second × 172,800 s
$\approx$ **240,000 deliveries**, about 480 MB. Sent at the peak rate on recovery: about 1,700 times its
normal load.
**How it changes the design.** The backlog lives in durable rows; recovery is ramped, not dumped.
:::

| Number | Arithmetic | Label | Decision |
|---|---|---|---|
| Average | 180 M ÷ 2.6 M s $\approx$ 70/s | derived | One small fleet |
| Peak | 480,000 ÷ 600 s × 3 = 2,400/s | derived | Peak sizes the fleet and the shards |
| Attempt log | 180 M × 1.2 × 500 B $\approx$ 108 GB/month | illustrative | Daily partitions, dropped at 30 days |
| Payloads | 60 M × 2 KB $\approx$ 120 GB/month | illustrative | One copy per event, not per delivery |
| Delivery writes at peak | 2,400 × ≈ 4 $\approx$ 10,000/s | derived | Four PostgreSQL shards by endpoint |
| Latency budget | relay 0.5 + log and fan-out 0.5 + claim 0.5 + send 2 + spare 1.5 = 5 s | initial target | Poll intervals are the dial |

::: warn
**"Thousands of events a second: we need a big queue."** Volume is the wrong axis. Six hundred calls in
flight is nothing; one endpoint at ten seconds is everything. Say the number, then say what it does not
change.
:::

# Stage 3: API and data

**Register (FR1).** `POST /v1/webhook-endpoints {url, events[], api_version}` → `201 {id, secret}`, the
secret shown once. A verification ping with a challenge must be echoed before the endpoint is active.

**The delivery on the wire (FR3).** Headers `Webhook-Id`, `Webhook-Timestamp`, `Webhook-Signature: v1=…`;
body `{id, type, loan_id, sequence, api_version, data}`. Answers: any 2xx is done; 410 unsubscribes;
everything else, including a timeout, is retried. 429 and 503 honour `Retry-After`.

**Logs and replay (FR4).** `GET /v1/deliveries?endpoint=&status=` with every attempt;
`POST /v1/deliveries/{id}/redeliver`; `POST /v1/webhook-endpoints/{id}/replay {since, rate, mode}` where
`mode` is *full* or *latest per loan*.

![Conceptual model: a merchant owns endpoints; an endpoint listens to subscriptions; an event fans out to deliveries; a delivery goes to one endpoint and is tried by attempts.](diagrams/video-erd-chen.pdf){width=100%}

![Physical model: the delivery row is sharded by endpoint, unique on endpoint and event, with its state, attempt number, next attempt time and lease; attempts are partitioned by day.](diagrams/video-erd-physical.pdf){width=100%}

::: why
**Why the delivery, not the event, is the unit of state.** One event has three recipients with three
different fates: delivered, retrying, dead. A per-event status cannot say that. A per-delivery row can, and
it is also the queue (claimed), the timer (`next_attempt_at`) and the lock (`lease_until`).
:::

# Stage 4: High-level design

## Version 1: the simplest thing that works

The producer POSTs to every subscribed URL inside the booking request. **The objection:** a till that takes
30 s holds the booking request for 30 s; a crash after commit loses the event; a call made before a
rollback tells a merchant about a loan that does not exist.

![V1: the producer calls the merchant inside the request.](diagrams/video-base-v1.pdf){width=80%}

## Version 2: no event without its commit

An outbox row in the producer's transaction; a relay to the event log, keyed by loan; dispatcher workers
consume the log and POST with in-process retries. **The objection:** one slow till holds the shared pool
(1,200 sockets of 600); retries live in memory and vanish on restart; healthy merchants queue behind the
slow one in the same partition; nothing records what was sent.

![V2: outbox, relay, log, dispatcher.](diagrams/video-base-v2.pdf){width=90%}

## Version 3: a queue per endpoint, as rows

Fan-out consumes the log, matches subscriptions and writes one delivery row per endpoint into the delivery
store, sharded by endpoint. The dispatcher claims due rows only for endpoints under their cap, with a lease;
every attempt is written to the attempt log; the webhooks API reads the log and replays by writing rows.

![V3: fan-out, delivery store, attempt log and API.](diagrams/video-base-v3.pdf){width=100%}

```sql
WITH due AS (
  SELECT d.id FROM delivery d JOIN endpoint e ON e.id = d.endpoint_id
   WHERE d.state = 'PENDING' AND d.next_attempt_at <= now()
     AND e.in_flight < e.cap
   LIMIT 200 FOR UPDATE OF d SKIP LOCKED)
UPDATE delivery SET state = 'IN_FLIGHT', lease_until = now() + interval '30 s'
  FROM due WHERE delivery.id = due.id
RETURNING delivery.id;
```

::: why
**Why a lease and not a lock.** A row lock lasts as long as a transaction, and holding a transaction
open across a ten-second HTTP call would pin a database connection per call. The claim commits at once; the
lease is a timestamp in the row. If the worker dies, the lease expires and another worker claims the row.
The second send is safe because the event ID travels with it.
:::

## The numbered flows and sequences

![FR2, emit: the commit with the outbox row, the relay, fan-out, one row per endpoint.](diagrams/video-flow-fr2.pdf){width=96%}

![FR3, deliver: the row, the claim under the cap, the signed POST through the proxy, the attempt.](diagrams/video-flow-fr3.pdf){width=96%}

![FR1, register: the verification ping goes through the egress proxy; the secret is shown once.](diagrams/video-seq-fr1.pdf){width=90%}

![FR2, emit: publish, wait for the acknowledgement, then mark sent.](diagrams/video-seq-fr2.pdf){width=90%}

![FR3, deliver: insert unique on endpoint and event, claim, send, record.](diagrams/video-seq-fr3.pdf){width=92%}

![FR4, replay: dead rows back to pending, oldest first, at the merchant's rate.](diagrams/video-seq-fr4.pdf){width=90%}

![C4 level 2 at V3: relay, log, fan-out, delivery store, dispatcher, attempt log, API.](diagrams/video-c4-containers.pdf){width=100%}

# Stage 5: Why these choices

## A log the company already runs, and rows for delivery

The event log is the company's backbone: funding, servicing and analytics read the same events. Webhooks
are one more consumer group. But a log is ordered by **key**, and delivery must be isolated by
**endpoint**; a log partition cannot hold back one endpoint's events without holding back every event behind
them. So the log is where events live, and rows are where deliveries live. Fan-out is the hinge.

## Technologies, one level down

Every container with the technology it runs on, how it is built, the alternatives rejected and why.
Generated from `stack.json`.

## The dispatcher and fan-out, one level down

![C4 level 3, the dispatcher: claimer, tier pools, endpoint limiter, breaker, signer with the key service, HTTP client, result writer reporting to endpoint health.](diagrams/video-c4-comp-dsp.pdf){width=100%}

![C4 level 3, fan-out: log consumer, subscription cache, matcher, renderer with the schema registry, payload writer, sequence check, delivery writer.](diagrams/video-c4-comp-fan.pdf){width=100%}

<!-- stack:sections -->

## Outbox relay: no event without a commit

*How it is built.* The producer inserts the outbox row in the same transaction as the change. The relay publishes unsent rows in ID order, keyed by loan, and marks them sent only after the log acknowledges. A crash after commit leaves the row, so it is published later; a crash after publishing and before marking publishes it twice, so every consumer de-duplicates by event ID. The relay holds a lease per producer database so only one instance drains it; it alerts on the age of the oldest unsent row, and sent rows are deleted after a day.

*Why An outbox table in each producer's PostgreSQL, drained by a Go poller in ID order:* Only one transaction can make “the loan was booked” and “the world will hear about it” a single fact.

*Rejected:*

- **A dual write: commit, then publish to Kafka**: A crash between the two loses the event, or publishes one for a change that rolled back.
- **Change data capture with Debezium**: An honest equal: no polling and no extra table, but one more system to run.

*Course:* theory/08 (transactions) and theory/10 (logs and streams).

*Drill.* "The relay crashed after Kafka acknowledged but before it marked the row sent. What happens?" The row is published again on restart: at-least-once. Every consumer, including fan-out, de-duplicates by event ID, so the merchant still gets one delivery. The trap is trying to make the relay exactly-once.

## Event log: the company's backbone, not ours

*How it is built.* One topic per domain, keyed by loan ID, so one loan's events stay in commit order. Seven days of retention; webhooks are one more consumer group, and its lag is our first indicator. Replication factor three, minimum in-sync replicas two, producers with acks=all. Partition count is set by the producers' peak, not by the number of endpoints.

*Why Kafka, domain topics keyed by loan ID, seven days of retention:* Funding, servicing and analytics already read these events. Webhooks are one more consumer group, with their own offsets.

*Rejected:*

- **Amazon SQS as the backbone**: No replay after a message is consumed, and no per-key ordering shared by many consumer groups.
- **RabbitMQ**: Replay and a backlog of days are not what it is built for; each consumer needs its own queue copy.

*Course:* theory/10 (logs, queues, streams).

## Fan-out: from one event to many deliveries

*How it is built.* Each consumer matches events to subscriptions from an in-memory cache and inserts one delivery row per match, in batches, unique on event and endpoint. The log offset is committed only after the batch is written. A crash repeats a batch and the unique key absorbs it. The cache is refreshed by subscription change events. The payload is stored once per event, not once per delivery; a per-merchant fair-share limit stops one producer burst from filling every shard at once.

*Why A Go consumer group with an in-memory subscription cache, writing delivery rows in batches:* The event log is ordered by loan; delivery must be isolated by endpoint. Fan-out is where one becomes the other.

*Rejected:*

- **One Kafka topic per endpoint**: Twenty thousand topics, created and deleted by self-service registration.
- **Filtering inside every dispatcher**: Every worker reads every event; isolation by endpoint is lost before it starts.

*Course:* theory/10 (logs, queues, streams).

*Drill.* "A merchant adds a subscription while an event for them is in flight. Do they get it?" The cache is refreshed from subscription change events, so there is a short window. The contract says subscriptions take effect within a minute, and the merchant can replay anything since a timestamp. The trap is promising the instant.

## Delivery store: one row per delivery, the timer is a column

*How it is built.* A row per delivery, on the shard that owns its endpoint, with its state, next attempt time and lease. Workers claim due rows with skip locked; an expired lease makes a row claimable again. A partial index on next_attempt_at where the state is pending keeps the claim query cheap; delivered rows are summarised in the attempt log and deleted within a day. Four shards carry the 2,400 a second peak with headroom.

*Why PostgreSQL sharded by endpoint ID; claim with SKIP LOCKED and a lease; next_attempt_at is the timer:* Each endpoint needs its own queue, its own delay and its own state for days. Rows in a table give all three without twenty thousand queues.

*Rejected:*

- **Kafka retry topics**: Fixed delays, and head-of-line blocking within each partition: one slow endpoint delays everything behind it.
- **An SQS queue per endpoint**: Twenty thousand queues to manage, and a fifteen-minute ceiling on message delay.

*Course:* theory/08 (transactions) and theory/06 (partitioning).

*Drill.* "Two dispatchers claim at the same moment. Can both send the same delivery?" No: skip locked gives the row to one of them, and the lease marks it. If that worker dies, the lease expires and another sends it again: at-least-once, which the event ID makes safe. The trap is a distributed lock.

## Dispatcher: isolation is the product

*How it is built.* Workers claim only for endpoints under their in-flight cap, ten by default, in pools split by merchant tier. Every call has a 2 s connect and a 10 s total timeout, is signed, and leaves through the egress proxy. Five consecutive failures open the endpoint's breaker. HTTP keep-alive per endpoint; a 2xx is success, a 410 disables the subscription, 429 and 503 honour Retry-After, everything else is retried. Responses are read to 4 KB at most.

*Why Go workers: a concurrency cap per endpoint, pools per merchant tier, a breaker per endpoint:* One slow endpoint must never spend the capacity another endpoint needs. The cap is the whole design.

*Rejected:*

- **One shared worker pool with retries**: A slow endpoint holds every worker: at ten seconds a call, 120 calls a second need 1,200 sockets.
- **A thread pool per endpoint**: Twenty thousand pools, almost all idle; a cap on in-flight calls gives the same isolation for free.

*Course:* theory/13 (reliability patterns) and theory/12 (overload control).

*Drill.* "The partner bank's endpoint slows to nine seconds at the peak. What happens to a small merchant's delivery?" Nothing: the bank's endpoint is capped and sits in its own tier pool, so it queues in its own rows while the small merchant's pool is untouched. The trap is a bigger shared pool.

## Egress proxy: the only door out

*How it is built.* The proxy resolves the name itself, refuses private, loopback, link-local and metadata addresses, and connects to the address it checked. Dispatchers have no other route out. It runs in its own subnet with network policy denying everything but outbound 443, in every zone, and logs every denial with the endpoint ID for the security team.

*Why Smokescreen, an open-source egress proxy, in front of every dispatcher:* A customer-supplied URL is untrusted input that our servers will call. The check must happen on the address actually connected to.

*Rejected:*

- **Checking the URL at registration only**: DNS rebinding: the name resolves to a public address at registration and to a private one at send time.
- **A firewall allow-list of merchant addresses**: Twenty thousand self-served endpoints on cloud hosts whose addresses change.

*Course:* theory/16 (security, operating systems).

*Drill.* "A merchant registers a name that resolves to 10.0.0.5 only after you validated it. What stops the call?" The proxy resolves at send time and refuses private ranges, and it connects to the address it checked, so rebinding has no gap to use. The trap is a stricter regex.

## Attempt log: the answer to “you never sent it”

*How it is built.* One row per attempt: status, latency, the first bytes of the answer, the error class. Daily partitions, copied to object storage and dropped after thirty days. About 108 GB a month at 500 bytes a row. Response bodies are truncated to 512 bytes and scrubbed of anything that looks like a credential; the signature header and key ID are kept for debugging.

*Why PostgreSQL partitioned by day, then object storage; read by the merchant dashboard:* Support, the merchant and on-call ask the same question: what did we send, when, and what did they answer?

*Rejected:*

- **Elasticsearch**: Full-text search is not the question asked; an append-only daily table is cheaper to run.
- **ClickHouse**: An honest equal at ten times the volume, for analytics across all endpoints; one more system at ours.

*Course:* theory/14 (observability) and theory/07 (storage).

## Contract renderer: the public contract is not the internal event

*How it is built.* Each endpoint is pinned to a dated public version; fan-out renders the internal event into it from a registry of every supported version. A producer's build fails if a supported version stops rendering. Additive fields need no new version; a rename or a removal does. Usage of each version is measured per endpoint, so deprecation is a list of merchants to contact, not a guess.

*Why A schema registry of public event versions, rendered at fan-out for each endpoint's pinned version:* Producers must be free to change their internal events; merchants must not have to change their integrations when they do.

*Rejected:*

- **Sending the internal event as it is**: Every internal refactor becomes a breaking change for twenty thousand integrations.
- **One public payload forever**: It freezes the product; fields that should be renamed or split never can be.

*Course:* theory/11 (API contracts) and theory/16 (evolving systems).

<!-- /stack:sections -->

## The stack on one page

<!-- stack:summary -->

| Container | Choice | Rejected | The deciding reason |
|---|---|---|---|
| Outbox relay | Outbox + Go poller | Dual write; Debezium | One commit, one fact |
| Event log | Kafka, by loan | SQS; RabbitMQ | Replay, many readers |
| Fan-out | Go consumer group | Topic per endpoint | Loan order to endpoint rows |
| Delivery store | PostgreSQL by endpoint | Retry topics; SQS | A queue per endpoint, as rows |
| Dispatcher | Go, caps, tier pools | Shared pool; pool each | Each spends its own budget |
| Egress proxy | Smokescreen | URL check; allow-list | Check the IP you connect to |
| Attempt log | PostgreSQL by day | Elasticsearch; ClickHouse | Drop a day, not rows |
| Contract renderer | Registry, pinned versions | Internal as is; freeze | The contract is the product |

Each fix in Stage 6 rejects one tool by name:

| Deep dive | Rejected | Because |
|---|---|---|
| 6.1 | A dual write: commit, then publish | a crash between the two loses the event, or sends one for a change that rolled back. |
| 6.2 | A Kafka partition, or retry topics, per endpoint | head-of-line blocking: one slow endpoint stalls everything queued behind it. |
| 6.3 | A fixed retry count every ten seconds | synchronised retries knock a recovering endpoint over again, and a two-day outage outlasts any fixed count. |
| 6.4 | An exactly-once, ordered delivery promise | impossible into a system we do not control; the consumer de-duplicates by event ID and orders by sequence. |
| 6.5 | Checking the URL string at registration | DNS rebinding resolves a public name to a private address at send time; only the egress proxy sees the real address. |
| 6.6 | Sending the producers' internal events as they are | every internal refactor becomes a breaking change for twenty thousand merchant integrations. |
| 6.7 | Alerting on merchants' error rates | their outages would page us all night; alert on our lag and on success to healthy endpoints. |

<!-- /stack:summary -->

## When you don't need all this (the alternate path)

![The alternate path changes one box: the dispatcher becomes a managed webhook service; the outbox, the log, fan-out and the contract stay ours.](diagrams/video-alt.pdf){width=90%}

**The simpler design.** Buy the delivery engine: a managed webhook service stores, signs, retries and
shows merchants their logs. Keep what is ours: the outbox, the log, fan-out and the public contract.

**What it gives up.** Loan-level data leaves for a vendor that the partner bank's vendor-risk review must
approve. The isolation caps and tiers are the vendor's. The cost grows with every message.

**The crossover.** At an illustrative $0.10 per thousand messages, 180 M deliveries a month cost about
$18,000 a month. A team of three with on-call and infrastructure costs about $80,000 a month. On cost
alone, building wins only past about 800 M deliveries a month.

> "At a hundred and eighty million a month I'd seriously consider buying the delivery engine and keeping
> the outbox, the log and the contract. I build when the bank won't let the data leave, or past eight
> hundred million."

::: warn
**Treating "buy" as a non-answer.** In an engineering-manager round, *not* raising build against buy is
the miss. Raise it, put a number on it, then say which constraint decides it here.
:::

# Stage 6: Deep dives

The seven challenges of the video, in the order where each fix creates the next question. Versions follow
the challenges: V4 (endpoint health), V5 (egress proxy), V6 (contract renderer).

![The challenge map: seven attack points on the same baseline.](diagrams/video-map.pdf){width=100%}

## 6.1 Why not publish after the commit? (correctness)

**The question.** *"Why an outbox table? Commit, then publish to Kafka."*

**The case.** `ln_7781` commits as booked; a deploy kills the process 4 ms later, before the publish. The
customer sees *approved*, the till waits for `loan.booked`, and the merchant voids the sale: a loan with no
purchase. Publish first instead, and a failed commit tells a till to release goods for a loan that never
existed. At 800 events a second every deploy hits the window.

**The fix.** The outbox row `(event_id, loan_id, seq, type, body)` is inserted in the loan's transaction.
The relay, every 200 ms and holding a lease per database, reads up to 500 unsent rows in ID order, sends
each keyed by loan, waits for every acknowledgement, and only then marks them sent.

**Why it works.** S1: the event exists exactly when the commit does. A crash between acknowledgement and
mark publishes twice, never zero times, and consumers de-duplicate by event ID.

**The push.** *"480,000 events in ten minutes: is the relay the bottleneck?"* Not if it batches: several
thousand a second for one relay against a peak of 800. Alert on the age of the oldest unsent row over
30 s; delete sent rows after a day so the outbox never slows the producer. Past several thousand a second,
split the lease by ID range.

**Rejected.** A distributed transaction across the database and the log: neither supports it well, and it
couples their availability.

## 6.2 One slow endpoint (overload, the crux, part one)

**The question.** *"At nine on the 2nd, one till vendor's server takes ten seconds. What happens to the
partner bank?"* **The naive answer.** "Autoscale the pool."

**The case.** 2,400 deliveries a second; the vendor's 120 a second at 10 s each holds 1,200 calls; the pool
has 600; the bank's p99 goes from 0.3 s to minutes; doubling the pool gives the vendor 1,200 of 1,200.

![The dispatcher's limiter and client under a slow endpoint.](diagrams/video-ch2-attack.pdf){width=80%}

**The fix.** Claim only where `in_flight < cap`; `in_flight` rises in the claim's commit and falls in the
result's, so it cannot drift from the rows. Tier pools (bank, large merchants, long tail) never share
workers. A breaker opens after five consecutive failures.

![Tier pools, the endpoint limiter and the breaker.](diagrams/video-ch2-fix.pdf){width=80%}

| Endpoint | Rate at peak | × answer time | Needed | Cap |
|---|---|---|---|---|
| Till vendor, healthy | 120/s | 0.25 s | 30 | 40, large-merchant pool |
| Till vendor, slow | 120/s | 10 s | 1,200 | 40: the rest wait in rows |
| Partner bank | 800/s | 0.2 s | 160 | 200 by contract, own pool |
| Long-tail merchant | ≤ 1/s | 0.3 s | < 1 | 10 (default) |

**Why it works.** L2: a slow endpoint queues in its own rows. **What it does not cover:** a flood of events
from one merchant's activity, which fills rows, not sockets: that is a fair-share limit at fan-out.

**The push.** *"The bank says the cap throttles them."* Caps are a contract, raised when their endpoint
proves it can take more; better, offer batches of up to 100 events per POST, turning 800 calls a second
into 8, with a per-event result list in the answer.

**Rejected.** A Kafka partition or retry topic per endpoint: head-of-line blocking inside each partition.

## 6.3 Down for two days, then back (recovery, the crux, part two)

**The question.** *"A merchant's accounting system is down from Friday evening to Sunday evening."*
**The naive answer.** "Retry every 10 s, five times, then a dead-letter queue; send the backlog when it's
back."

**The case.** Five retries kill the first deliveries within a minute. 240,000 wait by Sunday. Sent at
once on recovery, 1,700 times the normal load knocks it over again, and on Monday the merchant has a
quarter of a million dead letters and no replay.

**The fix (V4, endpoint health).** The next attempt is
$t + U(0, \min(3600, 10 \cdot 2^n))$ seconds, full jitter, for 72 hours, then dead. After five failures
the breaker pauses the endpoint: its rows are not claimed at all, and one oldest delivery is probed each
minute. On success the endpoint opens at one call a second and doubles each clean minute up to its cap;
over 5 % errors halves it. After an hour open, the technical contact is emailed; after 72 hours the
endpoint is disabled. A 410 unsubscribes at once.

![Version 4 on the baseline: endpoint health reads outcomes and pauses, probes and ramps.](diagrams/video-base-v4.pdf){width=80%}

![The ramp: probe, half-open at one a second, double each clean minute, halve on errors.](diagrams/video-seq-ch3-ramp.pdf){width=88%}

**Why it works.** L3: recovery is earned. Full jitter spreads 240,000 retries so they never arrive in step.
**What it does not cover:** an endpoint that is up but answers 400 to everything; those deliveries die after
the window, and the dashboard says why.

**The push.** *"They replay 240,000 events; the till only wants current status."* Offer a *latest per loan*
replay: about 60,000 calls instead of 240,000. Anything that books money (an accounting system) takes the
full history, oldest first per loan.

## 6.4 Twice, and out of order (correctness)

**The case.** Refund, sequence 7, is applied by the till but its answer is lost; paid off, sequence 8, is
delivered; our retry of 7 arrives and the till applies the refund twice and shows *refunded*.

**The fix (no version change: the contract).** At-least-once, said out loud. `Webhook-Id` for
de-duplication, kept by the receiver for 7 days, longer than our 72-hour window. A per-loan sequence: the
loan's version, incremented in the same transaction as the change and copied into the outbox row, so it is
monotonic and gap-free per loan; the receiver applies an event only if its sequence is higher than the last
it saw. Thin events and `GET /loans/{id}` for current state.

![The fan-out sequence check and delivery writer carry the producer's sequence.](diagrams/video-ch4-fix.pdf){width=80%}

**The push.** *"Why not strict order per endpoint?"* An ordered mode is one call in flight: at 0.25 s,
4 a second for that endpoint, and one failing event blocks everything behind it. Offer it; default to
parallel delivery plus sequence numbers.

## 6.5 Hostile URLs and forged calls (security)

**The case.** A name passes the registration check and resolves at send time to the cloud metadata
address; our dispatcher fetches credentials and shows their first bytes in the attacker's delivery log.
Separately, a fraudster replays a copied header with a fake `loan.approved` and a till releases a
television.

**The fix (V5, egress proxy and signing).** All calls leave through an egress proxy that resolves the name
itself, refuses private, loopback, link-local and metadata ranges, and connects to the address it checked;
network policy leaves no other route. Each call is signed: `v1 = HMAC-SHA256(secret, id + "." + t + "." +
body)`; the receiver recomputes, compares in constant time, and rejects $|now - t| > 300$ s. Answers are
truncated and scrubbed before they reach a log.

![Version 5: the egress proxy on the only path between the dispatcher and the merchant.](diagrams/video-base-v5.pdf){width=80%}

![What the till checks, in order.](diagrams/video-seq-ch5-verify.pdf){width=88%}

**Defence in depth.** Merchants confirm high-value approvals with `GET /loans/{id}` before releasing goods;
the partner bank uses mutual TLS.

**The push.** *"A secret leaked."* Rotate by API with 24 hours of overlap (both secrets sign), then revoke.
Offer asymmetric signatures (Ed25519): a published public key leaves nothing to leak on the merchant's
side, at the cost of harder verification on old stacks.

## 6.6 A producer changes the payload (contract and teams)

**The case.** Servicing renames `amount` to `amount_cents` and splits `status`; by Wednesday 3,000 tills
show $0 refunds, 1,200 accounting imports fail, the partner bank's file breaks, and two teams are both
right.

**The fix (V6, contract renderer and schema registry).** Each endpoint pins a dated version. Fan-out's
renderer maps the internal event to that version. The registry holds golden examples of every supported
version, and a producer's build fails if any stops rendering: a consumer-driven contract test in the
producer's own pipeline. Additive fields go into the current version; a rename or split is a new version;
versions are supported for 12 months; usage is measured per endpoint.

![Version 6: the contract renderer beside fan-out.](diagrams/video-base-v6.pdf){width=80%}

| Team | Owns | Contract with the others |
|---|---|---|
| Producers (origination, servicing) | internal events and their meaning | golden examples must still render; additive by default |
| Merchant integrations | public versions, renderer, docs, SDKs, deprecation | 12 months per version; usage per endpoint |
| Webhook platform | relay, fan-out, delivery, egress, health, attempt log | p99 first attempt, isolation, 72 h; never edits a payload |

**The push.** *"A security fix needs a breaking change in 30 days."* Usage telemetry turns deprecation into
a list; in the old version redact the unsafe field to null instead of removing it; give every endpoint a
"send test event" per version and a migration guide with a diff.

## 6.7 "You never sent it" (observability)

**The case.** A merchant rotated their own credentials on Friday; every delivery since answers 401. On
Monday, 8,000 deliveries are dead or retrying, platform success reads 97 % as on every day (600 endpoints
always fail), and support has no per-delivery view.

**The fix.** For the merchant: every attempt in the dashboard, and an email from endpoint health after an
hour failing. For us, only what we own:

| SLI | Objective (initial target) |
|---|---|
| First attempt, healthy endpoint, per tier | p99 under 5 s |
| Success to healthy endpoints (≥ 99 % over 24 h) | 99.9 % |
| Oldest pending delivery, per tier | under 2 min outside open breakers |
| Relay lag (oldest unsent outbox row) | under 30 s |
| Fan-out consumer lag | under 30 s |

| Metric A | Metric B | Conclusion |
|---|---|---|
| first-attempt p99 up in every tier | fan-out lag up | us: fan-out or the renderer |
| first-attempt p99 up in every tier | relay lag up | us: a producer's relay |
| failures up at one endpoint | everyone else flat | them: tell them, page nobody |
| success to healthy endpoints down | egress denials up | us: the proxy or DNS |
| oldest pending up in one tier | that pool saturated | a cap or a pool size |

**The push.** *"Your signatures don't verify."* Keep the timestamp, key ID and signature header of every
attempt; a "send test event" button and a page that recomputes a signature from a pasted body; the usual
causes are re-serialised JSON, a clock more than five minutes off, and the old secret after a rotation.

# Stage 7: Requirements that arrive mid-round

**"A second region."** Producers in each region write outboxes; the log replicates; each region runs its
own fan-out and delivery store for the endpoints it owns (by merchant home region), so an endpoint's rows
live in one place. *What doesn't change:* the contract. *Cost:* duplicates across a failover, absorbed by
event IDs.

**"Partners want filters: only refunds over $500."** A filter expression per subscription, evaluated in
fan-out before a row is written. *Cost:* a small expression language to secure and version.

**"The bank wants a daily file instead."** A new consumer of the log that writes a file per day, signed and
reconciled; not a webhook at all. *What doesn't change:* everything else; this is the log earning its place.

**"A new event type: loan.dispute_opened (SD-95)."** The producer adds it to the outbox; integrations adds
it to the next public version; merchants subscribe. Nothing in delivery changes.

# Stage 8: Failures and reliability

| Failure | Blast radius | Detection | Response |
|---|---|---|---|
| Relay stuck | one producer's events delayed | relay lag | restart; rows are still there |
| Log unavailable | all new events delayed | relay errors, lag | producers keep committing; outboxes grow |
| Fan-out bug | wrong or missing rows | fan-out lag, rows per event | rewind the consumer group; unique key absorbs repeats |
| Delivery shard lost | a quarter of endpoints paused | health checks | failover to the synchronous standby; leases expire and rows are re-claimed |
| Slow endpoint | that endpoint | its pending age | cap and breaker; nothing to do |
| Proxy down in one zone | that zone's dispatchers | egress errors | proxies in every zone; dispatchers fail over |
| Key service down | no new signatures | signing errors | cached secrets for 5 min; then deliveries wait, never unsigned |

# Stage 9: SLOs, observability, cost

The SLIs are in 6.7. **Cost, illustrative:** a few hundred dollars a month of compute for dispatchers and
fan-out; four small PostgreSQL shards with standbys; about 230 GB a month of attempt log and payloads before
archiving; the log is shared. The largest line is **people**: a platform team of about five, and two
engineers in merchant integrations. That is why build against buy is a real question (Stage 5).

# Stage 10: The EM layer (auxiliary at Staff)

**Phasing.** V2 (outbox library and relay, with the producers): 2 engineers, 1 quarter. V3 (fan-out,
delivery store, capped dispatcher, attempt log, API): a team of 5, 2 quarters, with a load test of one slow
endpoint before anything ships. V4 (endpoint health): 1 quarter. V5 (egress, signing, rotation): 1 engineer
with security. V6 (versions and SDKs): a merchant-integrations team of 2, ongoing. Riskiest first: the
isolation in V3.

**Team seams, and Conway's law on purpose.** The design has three seams, and each becomes a team boundary
with one contract:

| Contract | Owner → consumers | Rule |
|---|---|---|
| Outbox row and internal event | producers → platform | additive; event ID and loan sequence always present |
| Public versions | integrations → merchants | dated; 12 months; usage measured per endpoint |
| Delivery objectives | platform → integrations, merchants | p99 first attempt, isolation, 72 h |
| Golden examples | integrations → producers' builds | a producer's build fails if a supported version stops rendering |

The common mistake in an organisation is to let the platform team own the public payload ("it's in our
system") or to let each producer own its public events ("it's our data"). The first makes the platform a
bottleneck for every product change; the second makes every refactor a merchant outage. The integrations
team owns the seam because it owns the merchants' experience: documentation, SDKs, deprecation, support.

**API governance.** A change to a public version goes through a short review with the integrations team; a
producer's internal change needs no review if the golden examples still render. Version usage is a
dashboard; a version with zero endpoints for 90 days is retired.

**On-call.** The platform pages on its own lag and on success to healthy endpoints; merchants' failures go
to them by email and never to our pager. A runbook per symptom pair (6.7).

**With half the team.** Keep the outbox, the rows with caps, backoff with jitter, signatures and the egress
proxy. Defer the ramp (use a fixed slow rate after a breaker closes), batching, ordered mode and asymmetric
signatures. Never defer the cap or the proxy.

**Top risks.** A producer that bypasses the outbox. A cap tuned too high. The proxy as a single point of
failure. A public version nobody owns.

# Stage 11: The close

> "What I built: an outbox so no event exists without its commit, and a delivery row per endpoint that is
> the queue, the timer and the lock, claimed under a cap. The trade-off I chose: at-least-once with IDs and
> sequences, rather than a promise of order I can't keep. The risk I'd watch: one endpoint spending
> another's capacity, and a public contract nobody owns. Next: batching for the bank, and buy against build
> at the next contract renewal."

# Stage 12: Self-check after a simulator run

- Did you give the scale line once and derive every number from it?
- Did you say *at-least-once* in the first ten minutes, and name the event ID as part of the product?
- Did you compute the slow endpoint (rate × timeout) and turn it into a cap?
- Did you put the timer in a durable place and say what happens on a worker crash (lease)?
- Did you spread retries with jitter and ramp recovery, rather than dumping a backlog?
- Did you sign over the timestamp and body, and handle SSRF at send time, not registration?
- Did you separate the internal event from the public contract, and name who owns it?
- Did you raise build against buy with a number?
- Did you name SLIs you own, and keep merchants' outages off your pager?

\newpage

# Part III: The internals

## Appendix A: The outbox and the relay

The outbox turns a dual write (database and log) into a single write (database) plus an idempotent copy.
The relay's only correctness rule is ordering of its own two steps: publish, wait for acknowledgements, then
mark. Change data capture (reading the database's write-ahead log, as Debezium does) is an honest
alternative with no polling and no extra table, at the price of one more system and the table layout leaking
into the event. Either way the consumers must de-duplicate, because both publish at least once.

## Appendix B: Skip-locked claims and leases

`FOR UPDATE SKIP LOCKED` lets many workers select disjoint rows without waiting on each other: a row locked
by one claim is skipped by the others. The claim commits immediately, so no lock is held during the HTTP
call; the lease timestamp is what reserves the row. A sweeper is unnecessary: the claim query treats an
expired lease as pending. The in-flight counter per endpoint changes in the same commits as the claim and
the result, so it is exact without a separate coordination service.

## Appendix C: Backoff with full jitter

With exponential backoff alone, deliveries that failed together retry together, and a recovering endpoint
sees synchronised waves. *Full jitter* draws the whole delay at random: $U(0, \min(cap, base \cdot 2^n))$.
The expected total work is lower than with "equal" or "decorrelated" jitter in most simulations, and the
arrival rate at the endpoint becomes smooth. With base 10 s and a 1-hour cap, attempts reach the cap at about
the ninth try; over 72 hours a delivery is tried roughly 80 times, most of them while the breaker would
already have paused the endpoint, which is why the breaker, not the retry count, does most of the protecting.

## Appendix D: Signatures that receivers can verify

HMAC-SHA256 over `id.timestamp.body` binds the signature to this event, this moment and these bytes. The
timestamp bounds replay to the tolerance window; the stored event ID closes the window. Receivers must
verify against the raw body, before any JSON parsing re-serialises it, and compare in constant time. During
rotation two signatures are sent (`v1` and `v1-old`), and either verifies. Asymmetric signing (Ed25519)
removes the shared secret; the cost is library support on older stacks.

## Appendix E: Egress control and SSRF

Validation at registration fails against DNS rebinding: a name can resolve to a public address when checked
and to a private one when used. The check must therefore be made on the address actually connected to, at
connection time, by a component the dispatcher cannot bypass. An egress proxy such as Smokescreen does this:
it resolves, applies deny rules (RFC 1918, loopback, link-local, the metadata address, IPv6 equivalents) and
connects to the checked address. Redirects are not followed, or are re-checked hop by hop.

## Appendix F: Schema evolution for public events

Rules that keep a public version stable: add optional fields freely; never rename, retype or remove a field
inside a version; never change the meaning of a value; make enums open ("unknown values must be ignored").
Dated versions (`2026-06-01`) let an endpoint move when it chooses. Golden examples per version, rendered in
the producer's build, catch a breaking internal change before it ships.

## Appendix G: Testing it

A load test with one endpoint answering in 10 s at the peak rate, asserting that every other endpoint's
p99 stays within its objective. A chaos test that kills dispatchers mid-call and checks that every delivery
is completed once the lease expires. A recovery test: 240,000 pending deliveries, breaker closing, the ramp
measured against the endpoint's error rate. A contract test per public version, in every producer's build.

\newpage

# One-page cheat card

**Insight.** Isolation is the product; exactly-once is the consumer's job; the contract is the product too.

**Numbers.** 2,400/s × 0.25 s ≈ 600 in flight. 120/s × 10 s = 1,200 → a cap per endpoint. 1.4/s × 2 days ≈
240,000 → rows and a ramp. 180 M × 1.2 × 500 B ≈ 108 GB/month of attempts. $18k vs $80k a month → buy is
real below ≈ 800 M deliveries.

**Design.** Outbox + relay → log by loan → fan-out (match, render, one row per endpoint) → delivery store
(row = queue + timer + lock) → dispatcher (cap, tier pools, breaker, signer) → egress proxy → endpoint;
attempt log, API with replay, endpoint health.

**Contract.** `Webhook-Id`, `Webhook-Timestamp`, `Webhook-Signature`; per-loan `sequence`; pinned dated
version; 2xx done, 410 stop, anything else retried.

**The seven challenges.** Dual write → outbox. Slow endpoint → cap, tier pools, breaker. Two-day outage →
full jitter, breaker, ramp, replay (V4). Duplicates and order → ID and sequence. SSRF and forgery → egress
proxy, HMAC with timestamp (V5). Payload change → renderer, versions, golden examples, an owning team (V6).
"You never sent it" → attempts for the merchant, SLIs we own.

**Close.** At-least-once with a budget per endpoint; the contract and its owner; buy against build with a number.
