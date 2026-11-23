---
title: "SD-47 · Ticket Booking Under Contention"
subtitle: "A reference solution at the Staff bar: a rejection system, an atomic claim, a hold that expires, and a payment that may never answer"
author: "design-room reference solution · practise with the simulator first"
date: "21 November 2026 · reference-solution edition"
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

This is the reference solution for **SD-47, ticket and seat booking under contention**, written for the
**Staff bar (L6/L7)**. It follows the order of the video that accompanies it, and the video follows the order an
interviewer expects: **scope, numbers, a simple design, then break it, fix it, and recap.** Everything the video says
is here, with the reasoning, the code and the traps written out.

**Four layers, read in this order:**

1. **Part I, the system in pictures.** What a fan sees, what happens second by second when a million people arrive,
   where the load lands. Start here if the vocabulary is new.
2. **Part II, the reference solution** (this is the video, in print): thesis, requirements, estimates, a theory
   chapter, API and data, the design in three versions, then **eight challenges** that break it, a build cost and a recap.
3. **Part III, the internals** for when an interviewer digs: PostgreSQL, Redis, Kafka, a CDN, card payments, signed tokens.
4. **The one-page cheat card** at the end.

**How to use it.** Run the round cold first (`mock me SD-47`). Then read Part II with your own notes beside it. Mark
every place where you named a number, a mechanism or a trade-off less precisely than this document does.

> Numbers in this document are **illustrative or initial targets**, never measurements. Each one is labelled the first
> time it appears. A number you cannot tie to a decision is decoration; every one here is tied to one.

\newpage

# Part I — The system in pictures

## Vocabulary you need first

Every term used later in the document, grouped by where it lives. When a word in Part II makes you
ask "what is that?", the answer is here.

**The business**

| Term | Meaning |
|-------|-----------------------------------------------------|
| **On-sale** | The moment tickets for an event go on sale. Called **T0** in this document. A big on-sale is the only time the system is under stress. On a normal day it is a quiet e-commerce site |
| **Event** | One show on one date in one venue. Everything in this design is partitioned by `event_id` |
| **Seat inventory** | The list of every sellable seat for an event, each with a state: available, held, payment pending, sold |
| **Hold** | A temporary reservation. The seat is yours for 5 minutes while you pay; nobody else can take it. If you don't pay, it goes back |
| **Promoter** | The company that owns the show and decides the rules (fairness policy, ticket limits, extra seat releases) |
| **Oversell** | Selling the same seat twice. The one thing that must never happen |
| **Sell-through** | How fast the inventory sells out. Faster is better for the promoter, but not at the cost of oversell |
| **Conversion** | The share of admitted shoppers who complete an order. We assume ~70% |

**The waiting room**

| Term | Meaning |
|--------|----------------------------------------------------|
| **Waiting room** | A virtual queue in front of the shop. Fans wait there and are let into the shop in a controlled stream |
| **Lobby** | The waiting room *before* T0. Everyone who arrives early is in the lobby with no position yet |
| **Lottery (the T0 draw)** | At T0 everyone in the lobby gets a **random** place in the line. People who arrive after T0 join at the back in arrival order. Explained in challenges 4 and 5 |
| **Queue token** | A signed ticket the waiting room gives a fan on joining. It says: "this user, this event, this place in line". The signature means it can't be forged |
| **seq** | A fan's number in the line: 1, 2, 3 … 1,000,000 |
| **admittedUpTo** | One number per event: "everyone with seq at or below this may now enter the shop". It only grows |
| **Admission** | Letting one fan out of the waiting room into the shop. The fan proves they were admitted with an **admission token** |
| **Admission token** | A signed, short-lived (10 minutes) pass, a JWT. Every shop API call must carry it. The gateway checks the signature and the expiry locally, without a database call |
| **Admission rate R** | How many fans per minute are admitted. It's a dial: set by how many shoppers the shop can handle, not by how many people are waiting |
| **Admission controller** | The small process that turns the dial: every second it looks at the health of the shop and moves `admittedUpTo` forward by R |
| **soldOut flag** | A boolean in the same cached JSON as `admittedUpTo`. When set, waiting fans are told to stop waiting |

**The web and the edge**

| Term | Meaning |
|---------|---------------------------------------------------|
| **CDN** (content delivery network) | A network of cache servers in hundreds of cities (Cloudflare, Akamai, CloudFront, Fastly). A fan's request goes to the nearest one. If it has a fresh copy, our servers never see the request |
| **PoP** / edge location | One CDN site. Big CDNs have 200–300 |
| **Origin** | Our own servers, behind the CDN |
| **TTL** (time to live) | How long a cached copy may be served before the CDN must fetch a new one. `Cache-Control: max-age=1` means one second |
| **Request collapsing** | When many requests for the same expired object arrive at one PoP at once, the CDN sends **one** request to the origin and answers all of them from the result |
| **WAF / bot challenge** | Web application firewall. Blocks known bad traffic and makes a browser solve an invisible or visible challenge before entering the lobby |
| **API gateway** | The front door of our backend (Envoy, Kong, AWS API Gateway): TLS, authentication, rate limits, routing to the right service |
| **Polling** | The client asking "anything new?" every few seconds, as opposed to the server **pushing** updates over a long-lived connection (WebSocket, SSE) |
| **SSE** (server-sent events) | A one-way push channel over plain HTTP. Cheaper than WebSockets for "server tells client" updates |
| **HTTP 201 / 202 / 304 / 409** | 201 Created (hold made) · 202 Accepted (we've started, check back later) · 304 Not Modified (your cached copy is still current, no body) · 409 Conflict (a seat you wanted is gone) |
| **Idempotency key** | A unique id the client sends with a write. If the same request arrives twice (a retry after a timeout), the server sees the same key and returns the first result instead of acting twice |
| **JWT** (JSON Web Token) | A small JSON document plus a signature. Anyone with the key can verify it was issued by us and hasn't been changed |
| **HMAC** | A keyed hash. HMAC-SHA256 of a message with a secret key is a signature only the key holder can produce |

**The data layer**

| Term | Meaning |
|--------|----------------------------------------------------|
| **PostgreSQL** | The relational database holding seats, holds and orders. Chosen for transactions and row locks |
| **Transaction** | A group of changes that commit together or not at all |
| **Row lock** | When a transaction updates or `SELECT … FOR UPDATE`s a row, other writers to that row must wait (or fail, with `NOWAIT`) until it commits |
| **Conditional update** | `UPDATE … WHERE state = 'AVAILABLE'`: the change only happens if the condition still holds. Its result (how many rows changed) tells you whether you won |
| **`NOWAIT` / `SKIP LOCKED`** | Two options on `FOR UPDATE`: fail immediately if a row is locked, or silently skip locked rows |
| **Read Committed** | PostgreSQL's default isolation level. Each statement sees data committed before it started. Appendix A explains why it is enough here |
| **Synchronous replica** | A second database copy that must confirm every commit before the commit is acknowledged. If the primary dies, nothing acknowledged is lost |
| **Shard / partition** | Splitting data across databases (shards) or across physical pieces of a table (partitions) by a key, here `event_id` |
| **Redis** | An in-memory key-value store. Very fast (100k+ operations per second per node), single-threaded per node, optionally persisted to disk |
| **Lua script (Redis)** | A small program Redis runs atomically: no other command runs in the middle of it |
| **Bitmap** | One bit per seat: 1 = available, 0 = not. 50,000 seats = 50,000 bits = 6.25 KB |

**Messaging**

| Term | Meaning |
|-------|-----------------------------------------------------|
| **Kafka** | A durable, ordered, replayable log of events. Producers append, consumers read at their own pace |
| **Topic / partition** | A topic is a named log, split into partitions. Order is guaranteed only *within* a partition, so we key every message by `event_id` |
| **Outbox pattern** | Instead of "write the database, then publish to Kafka" (which loses messages if you crash between the two), you write the message into an `outbox` table **in the same transaction** as the data. A relay process copies outbox rows to Kafka |
| **CDC / Debezium** | Change data capture: reading the database's write-ahead log to stream changes out. Debezium is the common open-source relay |
| **At-least-once** | A message may be delivered more than once, never zero times. Consumers must therefore be idempotent |

**Payments**

| Term | Meaning |
|--------|----------------------------------------------------|
| **PSP** (payment service provider) | The company that talks to the card networks for us: Stripe, Adyen, Worldpay, Braintree. We send it a card token and an amount; it answers approved or declined |
| **Authorization** | The card issuer **reserves** the money on the card but doesn't move it yet. Valid for days |
| **Capture** | Actually taking the reserved money. Done after we've confirmed the seats |
| **Void** | Cancelling an authorization before capture. The reservation disappears; the customer was never charged |
| **Refund** | Returning money after capture. Slower, visible on the statement, and costs a fee. We design to need it rarely |
| **Webhook** | The PSP calling *our* URL to tell us an outcome, signed so we can verify it came from them |
| **Unknown outcome** | We sent an authorization and got no answer (timeout, connection reset). The payment may or may not have happened |
| **Reconciliation** | A job that compares our records with the PSP's and fixes disagreements |

**Reliability**

| Term | Meaning |
|-----------|-------------------------------------------------|
| **p99** | The 99th percentile latency: 99% of requests are faster than this |
| **SLO** (service level objective) | A target we commit to, like "hold API p99 < 300 ms" |
| **Invariant** | Something that must always be true, like "no seat has two tickets". We monitor it directly |
| **Backpressure** | Slowing the input when the system is overloaded, instead of accepting work and failing it |
| **Little's law** | *Items in a system = arrival rate × time each spends in it.* Used in Chapter 2 to size R |
| **Game day** | A planned rehearsal where you deliberately break things in staging to test the runbook |

\newpage

## What a fan experiences

Before any architecture, here is the product from the fan's side. Every box in the architecture
exists to make one of these steps work under load.

![User journey, part 1: from opening the page to being admitted. The fan spends most of the on-sale here, and the waiting room serves this whole phase without touching the database.](diagrams/sd47-journey-1-queue.pdf){width=62%}

**Step by step, with what the screen shows:**

1. **09:30, half an hour before the sale.** Maria opens the event page. A bot check runs (often
   invisibly). She lands on the **lobby** page: *"Sale starts at 10:00. Stay on this page. Everyone
   here at 10:00 gets a random place in line."* No seat map, no position. The page is static and comes
   from the CDN.
2. **10:00:00, T0.** The lobby closes. Every lobby fan's place in line is now fixed by the draw. Maria's
   browser asks once, *"what's my number?"*, and gets **412,377**. Fans who arrive at 10:00:05 get
   numbers after the last lobby fan, in arrival order.
3. **10:00 to 10:20.** Every ~10 seconds the browser fetches one small JSON file that's **the same for
   every fan**: `{"admittedUpTo": 31800, "ratePerMin": 2000, "soldOut": false}`. It computes *"you are
   380,577th in line, about 3 hours"* locally. That number is honest, and it tells Maria early that her
   chances are slim.
4. **10:16.** The admission controller predicts that the remaining seats will be bought by people
   already admitted. It sets `soldOut: true`. Within one polling interval, Maria's page says *"This
   event is sold out. Join the waitlist?"* She has waited 16 minutes, not 3 hours.

For the ~29,000 fans with low numbers, the story continues:

![User journey, part 2: from admission to tickets. Only ~10,000 fans are in this phase at any moment, which is why the database survives.](diagrams/sd47-journey-2-buy.pdf){width=85%}

5. **Admitted.** The browser swaps the queue token for an **admission token** valid for 10 minutes.
   It downloads the venue layout (immutable, from the CDN) and the **availability bitmap**, which shows
   which seats are free.
6. **Picks two seats and clicks "Hold".** In about 50 ms the server answers *held for 5 minutes* (201),
   or *one of those seats was just taken* (409) together with a fresh map, so the next click is on a
   free seat.
7. **Pays.** The order goes in, the seats are frozen as `PAYMENT_PENDING`, and the card is authorized.
   The page shows *"Processing payment…"* and polls the order status.
8. **Tickets.** Approved: seats become `SOLD`, the money is captured, tickets arrive in the app and by
   email. Declined: seats go back to the pool, and the fan can try another card while the admission
   token lasts.

## The funnel: who gets what

![Where a million fans end up. The design is mostly about the red box.](diagrams/sd47-funnel.pdf){width=72%}

::: why
**Why only ~29,000 admitted, if 1,000,000 are waiting?** Admitting more than can possibly buy is
pointless and harmful: they would all load the seat map and fight over a few remaining seats. We
admit roughly *(orders needed) ÷ (conversion)* = 20,000 ÷ 0.7 ~ 29,000, then stop and announce
sold out. **Why are 9,000 admitted fans without an order not a problem?** Their holds expire or are
released, those seats go back into the pool, and fans admitted later buy them. Admission continues
until the seats are actually gone.
:::

## Where the load lands

The single most useful picture for the round. **Three paths with three different load shapes**:
the waiting path is huge and served from cache, the read path is large and may be a second stale,
and the write path is small and must be correct.

![Load map at the on-sale peak. Each arrow carries its request rate. The only component that must be strictly correct, PostgreSQL, sees the smallest number.](diagrams/sd47-load-map.pdf){width=68%}

::: load
**Read the numbers top to bottom: 100,000 → 200 → 33 → 5,000 → 500 → 25.** Each layer exists to
shrink the number below it. The CDN removes 99.8% of polling traffic. The waiting room turns a
million people into 33 per second. The snapshot cache keeps seat-map reads off the database. The
database only sees the people actually clicking "hold".
:::

\newpage
\newpage
# Part II — The reference solution

## The thesis, and what this question grades

::: {.key title="The thesis"}
**This is not a booking system. It is a rejection system.** Fifty thousand seats cannot be shared with a million
people, so the design **converts a stampede into a stream**. Every seat has exactly one place where its state
lives and exactly one atomic way to change it.
:::

**The definition to say aloud.** A ticket booking system sells a *fixed set of individually identified seats* to
*many more buyers than seats*, with a *time-limited hold* between "free" and "sold", so that **no seat is ever sold
twice and no seat is ever stuck in limbo.** Each clause carries weight: *fixed set* (inventory never grows by
accident), *individually identified* (contention is per seat), *many more buyers* (twenty to one turns most requests
into refusals), *time-limited hold* (a third state, data and not a lock), *never twice, never stuck* (safety and
liveness).

**The hook.** A seat looks like a row with a boolean. The hard parts are everything around the boolean: a million
people reaching it in the same second, a human who needs three minutes to pay, and a payment provider that
sometimes does not answer.

| Axis | Weak signal | Strong signal |
|---|---|---|
| **Requirements** | Starts drawing. Never asks what "fair" means | Asks about oversell, specific seats, checkout time, fairness, payment behaviour, map freshness. Cuts search, pricing and resale aloud |
| **Correctness** | "Check availability, then insert a booking" | One atomic conditional claim. A third state. Expiry that does not depend on a job. An *unknown* payment state |
| **Trade-offs** | Names a product, or "a distributed lock" | Options, each with the failure that rules it out; says what the pick gives up |
| **Depth** | "A queue in front", and stops | Admission rate from Little's law; a controller driven by shop health; why the poll is cacheable; why the lottery is drawn at join time |
| **Operations** | Watches CPU | Age of the oldest expired hold; seats frozen by unknown payments; admission against hold latency; a pre-event load test; a plan for the day it fails |

::: warn
**Two ways to be wrong run through this question:** a seat sold twice, and a seat nobody can ever buy. Most weak
designs defend the first and forget the second. Keep both in view in every answer.
:::

\newpage

# Chapter 1 · Requirements and scope

Ask **five or six questions, not fifteen**. Each one changes the design, so say why you're asking.
The interviewer's answers below come from the simulator's cue sheet.

| I ask | Interviewer answers | Why it matters to the design |
|--------------|--------------|-------------------------------|
| Can we ever oversell? | Never | Forces an atomic claim and one source of truth per seat |
| Do users pick specific seats, or "best available"? | Specific seats, from a map | Each seat is a separate row; contention is per seat, not on one counter |
| How long does checkout take? | About 3 minutes | We need a **hold** with a time limit: a third state between free and sold |
| What does "fair" mean, and who decided? | First-come is expected; a queue or lottery is fine if argued | Decides the waiting-room design. It's a product decision, so I surface it rather than assume |
| How does payment behave? | External provider, 2–10 s, can time out ambiguously | A payment's outcome can be *unknown*; seats must not be released while it's unknown |
| How fresh must the seat map be? | Within a couple of seconds | Allows a cached, versioned read path |

::: why
**Why each question, in more depth.**

**Oversell.** If the answer were *"a little is fine, we'll refund"*, you could use an eventually
consistent counter and skip row locks. *"Never"* means every seat has exactly one place where its
state lives, and changing it is atomic.

**Pick a seat vs best available.** With *pick a seat*, two fans clicking the same seat is a real
collision you must resolve. With *best available*, the **server** chooses the seats, so it can avoid
collisions entirely by handing different fans different seats. That's why "best available" appears
later as a requirement that *reduces* contention.

**Checkout time.** If paying took 200 ms you could do *"lock the seat, charge, commit"* in one
transaction. It takes minutes, because a human types a card number. You cannot keep a database
transaction open for minutes: it would hold a connection and a row lock the whole time. So the
reservation must be **data** (a row with `state = HELD` and an expiry time), not a lock.

**Fairness.** Strict first-come-first-served (FIFO) at T0 rewards whoever has the lowest network
latency and whoever runs bots. A lottery among early arrivals is fairer. Either way, someone outside
engineering (the promoter, product) owns the decision. An EM candidate says so.

**Payment.** The PSP is slow and sometimes doesn't answer. "Didn't answer" is not "declined": the
customer may have been charged. The whole PAYMENT_PENDING state in challenge 3 comes from this one
question.

**Map freshness.** If the map had to be exact, every fan would need a live connection to the
database. "A couple of seconds stale" lets us build a snapshot once a second and serve it from cache
to everyone.
:::

**Functional (in scope):** join the sale, see a seat map, hold seats, pay, get tickets; release seats
on expiry or failure; the promoter adds inventory.

**Non-functional:** zero oversell (a hard invariant); the sale-opening minute must not fall over;
hold p99 < 300 ms; seat map stale by at most ~2 s; fair and bot-resistant; seats never stuck in limbo.

**Explicitly out of scope** (say it, write it in a box): event search and discovery, pricing and
dynamic pricing, the resale marketplace, the refunds UI, the mobile app itself.

> "Happy to pull any of these in if you want, but I'll spend the time on the contention path."

::: warn
**Don't ask about things you won't use.** "What's the tech stack?", "how many engineers?" and "which
cloud?" sound thorough and change nothing. Each question should visibly change a box on the
whiteboard.
:::


\newpage
# Chapter 2 · Estimates

## The full table, row by row

| Quantity | Arithmetic | Result | Consequence |
|---------|---------------|-----------|-------------------------|
| **1 · Winners vs losers** | 50k seats ÷ 2.5 per order | **~20k orders, 2% succeed** | A rejection system: tell the 98% early and cheaply |
| **2 · Without a queue** | 1M × 2 attempts ÷ 60 s | **~33k contended writes/s** | The reason the waiting room exists |
| **3 · Queue polling** | 1M ÷ 10 s | **~100k req/s** | Same answer for everyone, cached at the CDN for 1 s |
| Arrival (join) rate | 1M ÷ 60 s, ×3 in the first seconds | ~17k/s average, **~50k/s peak** | Joining must be one in-memory operation, never a DB row. The lobby spreads it over 30 min |
| Admission rate R | 10k shoppers ÷ 5 min each | **~2k/min = ~33/s** | R is set by shop capacity, not by demand |
| Time to sell out | 20k orders ÷ 70% = ~29k admissions ÷ 2k/min | **~15 min** | Fans past ~30,000 in line can be told "likely sold out" early |
| Seat-map reads | 10k shoppers × 1 per 2 s | ~5k req/s; 50k bits = 6.25 KB | ~30 MB/s; served from Redis, with 304s |
| Hold writes | 33/s × ~1.5 attempts, bursts ×10 | **50–500 writes/s** | One PostgreSQL primary per event is plenty |
| Payments | 20k orders ÷ 15 min; up to 10 s each | **~25/s, ~250 in flight** | Async checkout (202 + poll); bounded pool to the PSP |
| Storage (platform/year) | 500k events × 2k seats × ~120 B; 300M orders × 1 KB | ~120 GB + ~300 GB | Storage is not the problem; partition by `event_id` |

::: why
**Arrival rate: what is a "join"?** A **join** is one fan entering the waiting room: the
`POST /events/{id}/queue` call that returns a queue token. **Arrival rate** is how many joins per
second we receive. The worst case is everyone arriving in the first minute: 1M ÷ 60 s ~ 17,000/s on
average, and arrivals bunch at the start (people refreshing at exactly 10:00:00), so the first seconds
are ~3× the average, ~50,000/s. **Consequence:** a join must be a single in-memory operation (a Redis
`ZADD` or `INCR`, ~10 microseconds), never an `INSERT` into PostgreSQL. And it's a reason for the
**lobby**: if the waiting room opens 30 minutes early, the same million joins arrive over 1,800
seconds, ~600/s, and T0 itself carries no join spike at all.
:::

::: why
**Admission rate R: where do "10,000 shoppers" and "5 minutes" come from?** This is **Little's
law**: *items in a system = arrival rate × time each item spends there.* The shop (seat map + holds +
checkout) is the system. We decide how many concurrent shoppers it can serve well. 10,000 is a
comfortable number for one event's inventory database and the snapshot cache. A shopper spends about
5 minutes inside (pick seats, type card details, wait for payment). So the arrival rate that keeps
10,000 inside is 10,000 ÷ 5 min = **2,000 per minute**. In the room: *"R is a dial sized by checkout
capacity, not by demand. Demand is a million; capacity is ten thousand at a time."*
:::

::: why
**Time to sell out, and why it matters.** At 70% conversion we need ~29,000 admissions to produce
20,000 orders. At 2,000/min that's ~15 minutes. **The design consequence is the honest ETA:** a fan
at position 400,000 would be admitted after 200 minutes, long after the seats are gone. We can tell
them so as soon as the arithmetic is clear, instead of letting them wait.
:::

::: why
**Hold writes: why "×1.5" and "bursts ×10"?** Each admitted fan tries about 1.5 holds on average
(some get a 409 and retry). 33 fans/s × 1.5 ~ 50 holds/s. Admissions aren't perfectly smooth, and
in the first seconds of a new batch everyone clicks at once, so plan for 10× bursts: 500/s. A single
PostgreSQL primary does thousands of short transactions a second, so even the burst fits with room
to spare.
:::

::: why
**Payments: why "~250 in flight"?** By Little's law again: 25 payments/s × up to 10 s each = 250
open requests to the PSP at the worst moment. **Consequence:** the order service needs a connection
pool to the PSP of a few hundred, and checkout must be **asynchronous**: answer the fan with 202
immediately and let them poll, rather than holding their HTTP request open for 10 seconds.
:::

::: why
**Storage: why compute it at all?** To say out loud that it doesn't matter. ~420 GB a year is one
ordinary database server. Saying *"storage is not the problem"* earns credit, because it shows you
know what *is* the problem and won't spend design time on the wrong one.
:::

> "The headline is that this is not a big-data problem. After the queue, the write path is a few
> hundred transactions a second. All the scale is in the waiting room and the read path, so that's
> where I'll spend the design budget."

::: warn
**The classic estimation mistake** is computing ten numbers and drawing no conclusion from any of
them. The interviewer is scoring the *consequence* column. A number without a consequence is time
lost.
:::

\newpage

# Chapter 3 · Theory

*What makes this problem hard, in terms that outlive any product name.* It comes after the estimates and before any
design, so the design can lean on it. Six parts.

## 3.1 What it is, and what it is not

**A ticket booking system** is a *fixed set of individually identified seats*, sold to *many more buyers than seats*,
with a *time-limited hold* between free and sold. It is confused with four neighbours:

| Not this | Why not |
|---|---|
| **A lock** | A lock belongs to a process and vanishes when it crashes or is held too long. A hold is *data with an expiry*: it survives a crashed server and needs no open transaction |
| **A shopping cart** | A cart promises nothing. A hold promises that nobody else can take this seat until a time you can read |
| **An auction** | Price does not move with demand. The contest is over *who gets there first*, not who pays most |
| **A queue (the data structure)** | The line here is a *product experience*: a position, an estimated wait, an honest "likely sold out". It is also a load-shedding device |

## 3.2 Properties, stated separately

| | Property | Said precisely |
|---|---|---|
| **Safety** (must never happen) | **S1** | One seat belongs to two orders |
| | **S2** | Money is taken for seats we do not deliver, or seats are delivered with no money |
| **Liveness** (must eventually happen) | **L1** | Every seat is eventually sold or free again: nothing is stuck in limbo |
| | **L2** | Every fan eventually learns where they stand: a position, "sold out", an order result |
| | **L3** | The sale-opening minute does not take the system down; admitted work finishes |

Every mechanism below says which of these it serves, and every challenge says which one it is protecting.

## 3.3 The central tension

**Demand is unbounded; supply and checkout capacity are not.** The fairest line (strict first-come) rewards bots and
low latency and invites refresh storms. The cheapest line (random admission among early arrivals) needs a product
decision. The picture is a funnel: **1,000,000 fans at the door, about 10,000 inside the shop, about 50 holds a second,
20,000 orders.** Everything left of the shop is cheap and edge-served; everything right of it is expensive and
protected.

::: why
**Why "fairness against load" and not "consistency against availability"?** The inventory is a single-writer
relational row set: there is no replica disagreement to resolve. The trade the problem forces is *who gets the scarce
resource, and how cheaply do we tell everyone else no*. A designer who frames it as CAP has chosen the wrong axis.
:::

## 3.4 The seven mechanisms

Each in a fixed form: **property it protects, how it works, the failure it rules out, what it costs.** Mechanism first,
product name second.

| # | Mechanism | Protects | How | Rules out | Costs |
|---|---|---|---|---|---|
| 1 | **Conditional claim** | S1 | One statement whose `WHERE` clause is the availability check, rows locked in a stable order | A read-then-write race | Contended rows; the loser gets a 409 |
| 2 | **Hold as data with an expiry** | L1, no lock across a human | A seat row `HELD` with a `hold_id` and an expiry time; no transaction stays open | A transaction open for minutes; a lost lock | A clock to trust; a sweeper |
| 3 | **Two expiry paths** | L1 | Lazy: the claim treats an expired hold as free. Sweeper: releases and announces, so the map catches up | Seats stuck forever; correctness that depends on a job | Staleness while the sweeper is down |
| 4 | **Admission control at the edge** | L3 | A line, a pointer, and a rate chosen from shop health (increase slowly, cut fast) | A stampede on 50,000 rows | Most fans wait; a rate to tune |
| 5 | **Freeze, authorize then capture, "unknown" as a state, idempotency keys** | S2 | Move `HELD` to `PAYMENT_PENDING` before the provider call; reserve money first, take it last; ask again with the same key | Double charge; a seat sold twice after a late approval | Seats frozen up to ten minutes; a reconciler |
| 6 | **Split reads** | L2, L3 | Immutable layout on the CDN; a versioned availability bitmap; one cached queue-state answer for everyone | A live map from the database | A click on a stale seat fails (gracefully) |
| 7 | **Random admission and signed tokens** | fairness | Draw a random score at join time for everyone present at T0; signed, short-lived tokens bound to the account | Bots winning at T0; forged positions | A product rule to explain |

::: why
**Why is the hold "data" and not "a lock"?** A lock is something a process *holds*. If the process dies, the lock
goes with it, or lingers, depending on the lock service. A hold is a row: it is there after a crash, it expires on its
own, and anyone can read when. It also means the hold can be reasoned about in a *transaction log*, not in the
memory of a service.
:::

## 3.5 The options matrix, for the central decision

*How do we stop two fans taking one seat, across a three-minute checkout?* Six serious approaches:

| | Approach | Atomic? | Survives a crashed server? | Holds a connection through checkout? | Fails when |
|---|---|---|---|---|---|
| a | Read the seat, then write it | no | yes | no | Two readers both see free |
| b | A database row lock held through checkout | yes | **no** | **yes (minutes)** | The pool empties; the database falls over |
| c | A distributed lock per seat (a cache key with a lease) | mostly | partly | no | The lease expires mid-transaction; a second system to run and to fail |
| d | `SERIALIZABLE` transactions | yes | yes | no | Under contention most transactions abort and retry |
| e | An optimistic version column on each seat | per seat | yes | no | A multi-seat all-or-nothing claim still ends in one conditional update |
| **f** | **One conditional update; the hold is data with an expiry (pick)** | **yes** | **yes** | **no** | A slow fan loses the hold; hot seats are contended rows on one primary |

**The pick is (f).** What it **gives up:** the hold can expire on a slow fan; the hottest seats are contended rows on
a single primary (which is why the waiting room exists); and there must be a sweeper. Options (b) and (c) are the ones
a candidate reaches for first, and the ones to rule out aloud.

## 3.6 The failure catalogue

The things that will go wrong. It becomes the challenge list, in an order where each fix creates the next question:

1. Two fans on one seat → **the claim** (S1)
2. Holds that outlive their owner → **two expiry paths** (L1)
3. The hold expires while the payment is in flight → **freeze, authorize, unknown** (S2)
4. A stampede at the door → **the waiting room** (L3)
5. Bots, and an unfair line → **a lottery and signed tokens** (fairness)
6. A stale map for ten thousand shoppers → **split reads** (L2)
7. Requirements that arrive mid-sale → **the seams** (extension)
8. A failure nobody can see → **measure the promise** (all)

\newpage

# Chapter 4 · API and entities

## The API

All mutating calls take an `Idempotency-Key` header. Everything past the queue requires the
admission token.

```text
POST   /events/{id}/queue                      -> {queueToken(seq, signed), serverTime}
GET    /events/{id}/queue/me                   -> {seq}            (lobby fans, once, after T0)
GET    /events/{id}/queue/state  (CDN, 1s TTL) -> {admittedUpTo, ratePerMin, soldOut}
POST   /events/{id}/admit   {queueToken}       -> {admissionToken (JWT, 10 min)}
GET    /events/{id}/layout   (CDN, immutable)  -> venue SVG + seat ids, versioned URL
GET    /events/{id}/availability?v=812         -> bitmap (304 if unchanged)
POST   /events/{id}/holds   {seatIds[]}        -> 201 {holdId, expiresAt} | 409 {fresh bitmap}
DELETE /holds/{holdId}
POST   /orders  {holdId, paymentToken}         -> 202 {orderId, status: PENDING}
GET    /orders/{orderId}                       -> PENDING | CONFIRMED | FAILED
POST   /psp/webhooks                           -> payment outcome (signed by the PSP)
```

::: why
**Why is each endpoint there?**

- **`POST /queue`** creates the fan's place in the waiting room. It returns a **signed token** rather
  than storing a session, so any waiting-room server can verify it later without a lookup. It also
  returns the server's clock, so the countdown is the same for everyone.
- **`GET /queue/me`** exists only for lobby fans: their number isn't known until the T0 draw, so they
  ask once after T0.
- **`GET /queue/state`** is the poll. It carries **no user identity**, which is exactly why the CDN
  can cache it: every fan gets the same bytes.
- **`POST /admit`** exchanges a queue token for an admission token once the fan's `seq` is at or below
  `admittedUpTo`. The server checks the condition. The client can't admit itself early by lying,
  because `seq` is inside the signed token.
- **`GET /layout`** is the venue drawing. It never changes during a sale, so it's served from the CDN
  under a versioned URL and cached "forever".
- **`GET /availability?v=`** is the live part of the map. The client sends the version it already has;
  if nothing changed, the answer is **304 with no body**.
- **`POST /holds`** is the only contended write. **201** means you got all the seats; **409** means at
  least one was taken, and the body carries a fresh bitmap so the fan can choose again at once.
- **`POST /orders`** returns **202 Accepted**, not 200, because payment takes seconds. The fan polls
  `GET /orders/{id}`.
- **`POST /psp/webhooks`** is how the PSP tells us an outcome we may have missed.
:::

::: why
**What is an idempotency key, concretely?** The browser generates a random id (a UUID) once per
user action, say `k-77` for "pay for hold 5521", and sends it with every retry of that action. The
server stores `(user_id, idem_key) → result` with a unique constraint. If the network drops the
first response and the browser retries, the second request finds `k-77` already stored and gets the
**same** order back, instead of creating a second order and charging twice. Every mutating endpoint
here needs one, because under load timeouts and retries are normal.
:::

**The two tokens side by side** (they're easy to confuse, and the interviewer will check):

| | Queue token | Admission token |
|-------|-------------------------|----------------------------|
| Issued by | `POST /queue` | `POST /admit` |
| Says | "user U is in line for event E, kind LOBBY or seq N" | "user U may shop for event E until 10:14" |
| Lifetime | The whole sale | 10 minutes |
| Checked by | Waiting room only | API gateway, on every shop call |
| Why it exists | So the position can't be forged or traded | So the shop is unreachable without passing through the queue |

An admission token is a JWT. Decoded, it looks like this:

```json
{
  "iss": "waiting-room",
  "sub": "user-48213",
  "evt": "evt-7731",
  "scope": "shop",
  "iat": 1792130400,
  "exp": 1792131000,
  "jti": "adm-5f1c2b"
}
```

::: why
**Why a signed token instead of a session in a database?** During the peak, every shop request
must prove "this fan was admitted". A database lookup per request would put the waiting room's
state on the hot path of every hold and map read. A JWT is checked by the gateway with one signature
verification, in microseconds and without any network call. We sign with an asymmetric key (Ed25519
or RS256): the waiting room holds the private key, gateways only need the public key, so a
compromised gateway can't mint tokens. `jti` (a token id) lets us revoke a specific token (a detected
bot, for example) through a small deny-list.
:::

## The data model

One store per responsibility. Every inventory table is **partitioned by `event_id`**.

```sql
-- The source of truth for seats. One row per seat per event: 50,000 rows for this event.
CREATE TABLE event_seat (
  event_id        bigint      NOT NULL,
  seat_id         int         NOT NULL,           -- dense 0..N-1, so it doubles as a bitmap index
  section         text        NOT NULL,
  state           text        NOT NULL DEFAULT 'AVAILABLE'
                  CHECK (state IN ('AVAILABLE','HELD','PAYMENT_PENDING','SOLD')),
  hold_id         uuid,
  hold_expires_at timestamptz,
  order_id        uuid,
  version         int         NOT NULL DEFAULT 0,
  PRIMARY KEY (event_id, seat_id)
) PARTITION BY HASH (event_id);

CREATE INDEX event_seat_expiry ON event_seat (event_id, hold_expires_at)
  WHERE state = 'HELD';                            -- the sweeper's index: only held rows

CREATE TABLE hold (
  hold_id    uuid PRIMARY KEY,
  event_id   bigint      NOT NULL,
  user_id    bigint      NOT NULL,
  seat_ids   int[]       NOT NULL,
  status     text        NOT NULL,               -- ACTIVE, FROZEN, CONVERTED, RELEASED
  expires_at timestamptz NOT NULL,
  idem_key   text        NOT NULL,
  UNIQUE (user_id, idem_key)
);

CREATE TABLE outbox (
  id         bigserial PRIMARY KEY,
  event_id   bigint NOT NULL,
  event_type text   NOT NULL,                    -- SeatsHeld, SeatsReleased, SeatsSold
  payload    jsonb  NOT NULL,
  created_at timestamptz NOT NULL DEFAULT now()
);
```

```sql
-- Order DB: a separate database, owned by the order service.
CREATE TABLE orders (
  order_id   uuid PRIMARY KEY,
  user_id    bigint        NOT NULL,
  event_id   bigint        NOT NULL,
  hold_id    uuid          NOT NULL UNIQUE,      -- one order per hold, ever
  amount     numeric(12,2) NOT NULL,             -- money is never a float
  currency   char(3)       NOT NULL,
  status     text          NOT NULL,             -- PENDING, AUTHORIZING, UNKNOWN, CONFIRMED, ...
  psp_ref    text,
  idem_key   text          NOT NULL,
  UNIQUE (user_id, idem_key)
);

CREATE TABLE payment_attempt (
  order_id        uuid NOT NULL REFERENCES orders,
  attempt         int  NOT NULL,
  psp_idem_key    text NOT NULL UNIQUE,          -- what we send to the PSP as its idempotency key
  status          text NOT NULL,                 -- SENT, AUTHORIZED, DECLINED, UNKNOWN, VOIDED
  last_checked_at timestamptz,
  PRIMARY KEY (order_id, attempt)
);

CREATE TABLE ticket (
  ticket_id uuid PRIMARY KEY,
  event_id  bigint NOT NULL,
  seat_id   int    NOT NULL,
  order_id  uuid   NOT NULL REFERENCES orders,
  barcode   bytea  NOT NULL,                     -- secret; rotating barcodes come later
  UNIQUE (event_id, seat_id)                     -- the last line of defence against oversell
);
```

::: why
**Why is each table shaped like this?**

- **`event_seat` holds the state, not a separate "locks" table.** The hold is data with an expiry, so
  it survives a crashed server and needs no open transaction. `version` increases on every change, so
  the snapshot builder and any optimistic-concurrency client can tell whether a row moved.
- **Dense `seat_id` (0 to 49,999)** means "seat 812" is bit 812 in the availability bitmap. No lookup
  table is needed to build the map.
- **The partial index `WHERE state = 'HELD'`** contains only the few thousand held rows, not all
  50,000, so the expiry sweeper's query stays fast.
- **`hold` is separate from `event_seat`** because a hold covers several seats, belongs to a user and
  carries the idempotency key. The seat rows point back to it with `hold_id`.
- **`orders` is in a different database.** The inventory database is the hottest, most contended
  resource during a sale, so we keep everything else off it. Orders, payments and tickets have
  different access patterns and can be scaled and backed up independently.
- **`numeric(12,2)` for money.** Floating-point numbers can't represent 0.10 exactly; money is always a
  decimal type or an integer number of cents.
- **`UNIQUE (event_id, seat_id)` on `ticket`.** Even if a bug somewhere let two orders believe they own
  seat 812, the second ticket insert fails. The database enforces the invariant independently of our
  code. That's "belt and braces".
- **`outbox`** exists so that "seats changed" and "tell the rest of the system" happen in **one
  transaction**. challenge 6 explains why.
:::

**Waiting-room state lives in Redis**, not PostgreSQL:

| Redis key | Type | Holds |
|------------------|----------|--------------------------------|
| `phase:{e}` | string | `LOBBY` or `QUEUE` |
| `lobby:{e}` | sorted set | user → secret random score (the draw) |
| `next:{e}` | integer | last issued seq (late arrivals `INCR` it) |
| `admittedUpTo:{e}` | integer | the admission pointer |
| `rate:{e}`, `soldOut:{e}` | string | published with the pointer |
| `admitted:{e}:{user}` | string, TTL 600 s | "already admitted", stops double admission |

::: why
**Why `{e}` in braces?** In Redis Cluster, a key's **hash slot** decides which node stores it.
If part of a key is in `{…}`, only that part is hashed. So every key of event `e` lands on the **same
node**, and one Lua script can touch all of them atomically. Different events land on different
nodes, which is how many simultaneous on-sales spread out (challenge 7).
:::

\newpage
# Chapter 5 · High-level design

Three versions on **one carried baseline**. Each is introduced by the objection it answers. The boxes never move: every
later picture is a view of the same drawing. *Colour means role:* client blue, edge darker blue, service purple, data
store green, queue orange, cache yellow, external grey. Red is only failure; a green outline is only a fix.

## V1 · The simplest thing that works

One API and one database. A seat table with a status column. The API reads the seat; if it is available it writes the
fan's name. For a small venue with a quiet sale this is enough, and saying so is part of the answer.

![V1: one API, one table, read then write.](diagrams/video-base-v1.pdf){width=80%}

**The objection.** Two fans can both read "available" and both write. There is no state for "someone is paying", so
a lock would have to be held for the whole checkout. And a million requests land straight on the table.

## V2 · A third state, a conditional claim, and a separate order path

![V2: the claim, the hold, and checkout behind it. New boxes outlined blue.](diagrams/video-base-v2.pdf){width=90%}

The seat gets a third state and an expiry; the claim becomes **one conditional update**. Checkout moves to its own
**order service**, which freezes the seats, calls the **payment provider** and only then sells. The two paths are
separated because the provider is slow and sometimes silent, and the inventory database must never wait for it.

**The objection.** The claim is correct, but a million fans still reach fifty thousand rows, and the seat map is still
read from the same database that the claims lock.

## V3 · An edge, a waiting room, a seat-map pipeline

![V3: the shape that survives the sale. New boxes outlined blue.](diagrams/video-base-v3.pdf){width=100%}

Three additions, each with a job:

- **CDN and gateway** absorb the million. Nothing behind them is sized for it. The gateway checks an **admission
  token** on every shop call: no token, no shop.
- **Waiting room**: a lobby, a signed place in line, a pointer, and a cached, user-independent answer to "how far has
  the line moved?". An **admission controller** moves the pointer at a rate it reads from shop health.
- **Seat-map pipeline**: the database writes a change and an **outbox** row in one transaction; a log carries it to a
  **snapshot builder**, which publishes at most one versioned bitmap a second to a cache.

**What V3 leaves open.** The details: the payment race, bots, what the map shows after a mid-sale release, and what we
cannot see. Those are the eight challenges.

## One numbered flow per functional requirement

Each is a view of the same baseline. The numbers are the order of the arrows.

**FR1 · Join and admission.** (1) A fan requests the sale page from the CDN. (2) The gateway sends "join" to the
waiting room, which draws a random score and returns a signed queue token. (3) The fan polls one cached answer and
computes their own position; when the pointer reaches them, `admit` exchanges the queue token for a ten-minute admission
token.

![FR1](diagrams/video-flow-fr1.pdf){width=85%}

**FR2 · Browse.** (1) Request. (2) The layout comes from the CDN, immutable; the availability comes from the seat-map
cache by version, with a 304 when nothing changed. (3) Response.

![FR2](diagrams/video-flow-fr2.pdf){width=85%}

**FR3 · Hold.** (1) Request with the admission token and an idempotency key. (2) The gateway checks the token. (3) The
API sends one conditional claim, all or nothing. (4) The database answers won or lost. (5) The API answers `201` with an
expiry, or `409` with a fresh bitmap. (6) The response.

![FR3](diagrams/video-flow-fr3.pdf){width=85%}

**FR4 · Pay and ticket.** (1) `POST /orders` reaches the order service. (2) It **freezes** the seats before calling the
provider. (3) It authorizes. (4) The provider answers approved, declined, or nothing. (5) A silent answer becomes
*unknown*, and the reconciler asks again. The seats are sold only on an approved authorization.

![FR4](diagrams/video-flow-fr4.pdf){width=90%}

**FR5 · Expiry and release.** (1) The sweeper releases expired holds in small batches. (2) The same transaction writes
an outbox row. (3) The released seat is announced and can go to a fan on the waitlist.

![FR5](diagrams/video-flow-fr5.pdf){width=90%}

## The C4 views, and the sequences, follow in the pages below

The context, container and component views, and the walk-through of one fan from the lobby to a ticket, are the
unchanged detail that sits under the baseline. The baseline is the map; these are the territory.

## The container view, and the walk-through of one fan

Draw the context first (30 seconds), then the containers, then **walk one request end to end.**

::: why
**What are C4 levels?** C4 is a convention for architecture diagrams at four zoom levels.
**Level 1, Context:** our system as one box, plus the people and outside systems it talks to.
**Level 2, Containers:** the deployable pieces inside (services, databases, queues).
**Level 3, Components:** the parts inside one container. **Level 4** is code, rarely drawn. In an
interview you draw L1 in seconds, spend your time on L2, and zoom to L3 only in a deep dive.
:::

![C4 Level 1: system context. Two external dependencies decide the shape of the design: the PSP (slow, sometimes silent) and the edge (where bots are stopped and polling is absorbed).](diagrams/sd47-c4-context.pdf){width=100%}

![C4 Level 2: containers. Three separate paths: the queue path (Redis, cached at the CDN), the read path (snapshots built from the event stream) and the write path (PostgreSQL, one shard per hot event).](diagrams/sd47-c4-container.pdf){height=62%}

**Every container, and why it's separate:**

| Container | Job | Why it is its own box |
|---------|----------------------|-----------------------------|
| CDN / WAF | Static app, venue layout, the cached queue state, the bot challenge | Absorbs the million. Nothing behind it is sized for a million |
| API gateway | TLS, authentication, rate limits, **admission-token check**, routing by `event_id` | One place enforces "no token, no shop" |
| Waiting room | Join, the draw, `queue/me`, `queue/state`, `admit` | Scales with *waiting* fans, which is a different curve from shopping fans |
| Queue store (Redis) | Lobby set, sequence counter, `admittedUpTo` | Losing a second of queue state is survivable; losing a seat isn't. Different durability, different store |
| Admission controller | Turns the R dial every second | One decision per event, separate from request handling |
| Seat-map service + snapshot cache | Serves the availability bitmap by version | Read path; may be 1–2 s stale; must never touch the DB |
| Inventory & holds | The atomic claim, hold lifecycle, the outbox | The correctness core. Small, boring, heavily tested |
| Inventory DB (PostgreSQL) | `event_seat`, `hold`, `outbox` | The one source of truth for seats |
| Order service + Order DB | Checkout saga, payments, tickets | Talks to the slow PSP; must not hold inventory connections while it waits |
| Kafka | `SeatsHeld/Released/Sold`, `OrderConfirmed` | Decouples everything downstream from the write path |
| Hold expirer | Releases expired holds and announces them | Background cleanup, never on the critical path |
| Notification service | Tickets, waitlist offers | Third-party email and push are slow; keep them async |

# Chapter 5 (continued) · Why these technology choices

Requirement-drip interview guides say it outright: *if you name a tool, be ready to defend it in depth.* For each
tool: why it fits here, the internals you must be able to explain, and the alternative you rejected.
Part III goes one level deeper on each.

## PostgreSQL for seats

**Why here.** The hold is a multi-row, all-or-nothing change (two or four seats together), guarded by
a condition (all must be free). That is exactly what a relational transaction with row locks does.
Constraints (`UNIQUE` on tickets, `CHECK` on state) enforce the invariant inside the database. The
write rate after the queue is tiny.

**Internals to explain.**

- An `UPDATE` (or `SELECT … FOR UPDATE`) takes a **row-level lock** that lasts until commit. A second
  writer to the same row waits, or fails at once with `NOWAIT`.
- Under **Read Committed**, a writer that waited re-checks its `WHERE` clause against the **new**
  version of the row once the lock is released. If the seat is now `HELD`, the condition is false and
  zero rows are updated. That's why the conditional update is safe without `SERIALIZABLE`.
- **Synchronous replication** to a standby in another zone: a commit is acknowledged only after the
  standby has the WAL record, so failover loses nothing acknowledged.

**Rejected: Redis as the seat store.** It's faster, but replication is asynchronous. A primary can
acknowledge a hold and crash before the replica has it; the replica is promoted and the seat is free
again. Someone else holds it, and both pay: an oversell. Speed isn't our bottleneck; correctness is.

## Redis for the waiting room

**Why here.** The queue needs 50,000+ trivial operations a second at T0 (`ZADD`, `ZRANK`, `INCR`,
`GET`) with no joins and no durability beyond seconds. Redis does 100k+ simple operations a second
per node.

**Internals to explain.**

- **Single-threaded command execution**: commands run one at a time per node, so `INCR` is atomic
  without locks, and a **Lua script** runs as one atomic unit.
- **Persistence:** AOF (append-only file) with `fsync` every second can lose about one second of writes
  on a crash. Replication is asynchronous, so failover can lose the last moments too.
- **Why that loss is acceptable here:** the queue token is signed and carries the fan's `seq`, so the
  truth about a fan's position lives in their token, not only in Redis. If `next:{e}` rolled back by a
  second, we'd re-seed it from the highest seq seen in tokens since.

**Rejected: Kafka as the queue.** Kafka is a durable ordered log, which sounds like a queue, but the
access pattern is wrong. We need *"what is my position?"* and *"advance the pointer by 33"*, not
*"consume the next message"*. One consumer reading a million join messages at R per second would
add latency and moving parts for nothing.

## Kafka with the outbox pattern

**Why here.** Several things react to seat changes: the seat-map builder, notifications, analytics,
the waitlist. Publishing from the inventory transaction directly would couple the write path to all
of them. A durable log lets each consumer read at its own pace and lets us **replay** to rebuild a
snapshot from scratch.

**Internals to explain.**

- **Partition by `event_id`**: all messages for one event go to one partition, so they're consumed
  in order. Different events spread across partitions.
- **Consumer groups**: each consuming service has its own group and its own offset; adding a consumer
  doesn't affect the others.
- **At-least-once delivery**: after a crash a consumer can re-read messages, so consumers must be
  idempotent. The seat-map builder is naturally idempotent: setting bit 812 to 0 twice is harmless.

**Rejected: dual write** (commit to PostgreSQL, then publish to Kafka from application code). A crash
between the two loses the event forever, and the map shows a sold seat as free until the next full
rebuild.

## A CDN for the queue state and the layout

**Why here.** It turns 100,000 req/s into about 200 req/s at our origin. It also sits close to the
fan, so polling is fast everywhere.

**Internals to explain.**

- **Cache key and TTL**: `queue/state` for event E is one cache entry per edge with `max-age=1`.
- **Request collapsing**: when the entry expires and 500 requests arrive at that edge in the same
  millisecond, the edge sends one request to us, not 500.
- **Origin shield**: an optional middle tier, so 200 edges ask one shield, and only the shield asks
  us. That brings origin traffic to roughly 1 req/s per event.
- **Versioned URLs** for the layout (`/layout?v=3`), cached for a year: a new seat release bumps the
  version, so no cache purge is needed.

**Rejected: WebSockets to a million clients.** It works (some ticket sites do it), but it means a fleet
of stateful servers holding a million open connections to push a number that changes once a second.
Polling a cached file is simpler, cheaper and degrades better: if the push fleet dies, fans see
nothing; if the CDN briefly can't refresh, fans see a number one second older.

## Technologies, one level down

Every container with the technology it runs on, how it is built, the alternatives rejected and why, and the question an interviewer asks about it. Generated from `stack.json`.

<!-- stack:sections -->

## Inventory DB: PostgreSQL, one conditional statement

*How it is built.* Each seat of each event is a row with a state. A claim is one update statement that names the state it expects: set held where the seat is free. A second fan's identical statement matches no row and learns the seat is taken. The hold row and the outbox row commit in the same transaction. Read committed is enough because the check and the change are the same statement. The database is partitioned by event, so a hot on-sale loads one partition.

*Why PostgreSQL 16, primary and synchronous standby, read committed:* Selling a seat once is a conditional update on a row, in a transaction with the hold and the outbox. Row locks and constraints are the tools that make it true.

*Rejected:*

- **Read the seat, then update it**: Two fans both read free and both write. The conditional update closes the gap in one statement.
- **Redis for the hold**: A key can expire or vanish while the database still says held. The hold belongs in the same transaction as the seat.
- **A distributed lock per seat**: One more system, and a lock without a token has the stale-holder failure.

*Course:* theory/03 (partitioning and storage) and theory/07 (correctness under failure).

*Drill.* "Ten thousand fans click the same seat in the same second. What does the database do?" Ten thousand identical conditional updates queue on one row; the first matches, the other 9,999 match nothing and return taken. The trap is a read-then-write in the application.

## Waiting room: Redis with Lua

*How it is built.* A fan joins the lobby and receives a position. An admission pointer advances at the rate the controller sets. A Lua script moves a batch from the lobby into the admitted set and mints their tokens in one atomic step, so no fan is admitted twice. Polling for position is served from a cached snapshot, not from Redis. Persistence to disk is on, and the line can be rebuilt from the join log if the node is lost.

*Why Redis, a sorted set for the lobby, a pointer, Lua scripts for the atomic steps:* A million fans arriving at once cannot all reach the shop. The line is a data structure that must be fast and atomic.

*Rejected:*

- **The relational database as the queue**: A million inserts in a minute onto the inventory primary: the line would take the booking path down with it.
- **Kafka as the queue**: Good for ordering, awkward for a position the fan can poll and a pointer that advances.
- **A third-party waiting room product**: A real option; we show the design, and buy if the team cannot run it.

*Course:* theory/05 (caching) and theory/09 (real-time and connections).

*Drill.* "The Redis node holding the line fails. What happens to the million fans waiting?" A replica is promoted and the line is rebuilt from the replicated state and the join log; positions may shift slightly but nobody is admitted twice, because admission is a single script. The trap is losing the line.

## Admission: a dial and a signed token

*How it is built.* The admission controller watches the shop's load and turns the rate dial down or up. A fan reaching the pointer gets a short-lived signed token, a JWT valid for ten minutes. Every shop call carries it. The gateway verifies the signature and expiry locally, so the check costs no database call. A bot farm can hold many tokens; per-fan limits sit behind the gateway.

*Why A Go control loop, a signed token, a gateway that verifies without a database call:* The shop can serve only so many shoppers. The dial sets how many enter per second, and a signed pass proves they were let in.

*Rejected:*

- **Rate limiting at the gateway only**: It rejects fans instead of queueing them: a fair line becomes a race of retries.
- **A session lookup per request**: The session store becomes the bottleneck of the shop.

*Course:* theory/08 (reliability and operations).

## Seat events: Kafka with the outbox

*How it is built.* Each claim, release and sale writes an outbox row in the same transaction as the seat change. A relay publishes the rows to Kafka in commit order, partitioned by event, at least once. The seat-map builder, notifications and a future waitlist are separate consumer groups, each deduplicating. A waitlist, for example, is just a new consumer of this log.

*Why Outbox in the inventory transaction, Kafka partitioned by event:* The seat map, notifications and any later consumer need to know what changed. The event must exist if and only if the claim committed.

*Rejected:*

- **Publishing after the commit**: A crash between the two loses a seat change for ever.
- **Consumers reading the database**: Every consumer adds load to the inventory primary during the sale.

*Course:* theory/06 (messaging and streams).

*Drill.* "Product wants a waitlist added mid-sale. What changes in the booking path?" Nothing. The waitlist is a new consumer group reading the seat events, and it acts on a released seat. The trap is rewriting booking.

## CDN: the queue state and the layout

*How it is built.* The CDN caches the immutable venue layout for a long time and the queue state for a second. When many requests for an expired object reach one point of presence, request collapsing sends one request to the origin. The WAF rejects obvious bot traffic and scripted floods before they reach the waiting room. Per-fan data, like a position, is not cached at the edge; it goes through a short cached snapshot at the origin.

*Why A CDN with a WAF, one-second lifetimes, request collapsing:* Ten thousand shoppers asking for the same seat map should cost one origin request, not ten thousand.

*Rejected:*

- **Serving everything from the origin**: The origin would carry the whole stampede.
- **A long edge lifetime for seat state**: Fans would see seats as free that are gone, and click into failures.

*Course:* theory/05 (caching).

## Seat map: layout and a versioned bitmap

*How it is built.* The venue layout is immutable and cached for ever. A builder consumes the seat events and writes a compact bitmap of seat states, about six kilobytes per event, to the snapshot cache under a version number. The seat-map service serves the layout plus the latest bitmap, and the client shows a fresh-as-of time. A stale map can show a taken seat as free; the claim is what decides, so staleness costs a retry, not an oversell.

*Why A Go service, an immutable layout object, a bitmap snapshot per event version in Redis:* Ten thousand shoppers want to see which seats are free. That must not touch the inventory primary.

*Rejected:*

- **Querying the seat table per shopper**: Ten thousand readers on the primary during the sale.
- **Pushing every seat change to every browser**: A fan-out of every claim to ten thousand screens.

*Course:* theory/05 (caching).

*Drill.* "The map says a seat is free and the fan clicks it, but it is gone. Is that an oversell?" No. The claim, one conditional update, decides, and answers taken; the map is a hint. The client refetches. The trap is treating the map as the truth.

## Order service and the hold expirer

*How it is built.* The order service runs a saga: freeze the hold so it cannot expire mid-payment, call the payment provider with an idempotency key, then confirm the sale or release. The hold expirer sweeps holds past their time and releases them; the claim itself also expires an old hold when it finds one. A reconciler asks the provider about payments that went silent. Two paths each cover the other's gap: the sweeper catches what no claim touches, and the claim catches what the sweeper has not reached.

*Why Go order service, an idempotent payment call, a hold expirer, a reconciler:* A hold must end, whether the fan pays, abandons or the payment goes quiet. Both outcomes must be safe.

*Rejected:*

- **A TTL on a Redis key as the hold**: The key and the database can disagree. The hold belongs with the seat.
- **Releasing the hold the moment it expires**: If the payment succeeded in that instant, we have taken money for a seat we resold.

*Course:* theory/07 (correctness under failure).

*Drill.* "The hold expires, then the payment succeeds. Who gets the seat?" The fan who paid, because the hold was frozen before the call. A reconciler resolves a silent payment by asking the provider, and only then releases. The trap is releasing at expiry.

<!-- /stack:sections -->

## The stack on one page

<!-- stack:summary -->

| Container | Choice | Rejected | The deciding reason |
|---|---|---|---|
| Inventory DB | PostgreSQL, conditional update | Read then write; Redis hold | Check and change are one statement |
| Waiting room | Redis, sorted set, Lua | Database; Kafka | Fast and atomic admission |
| Admission | Rate dial; signed token | Gateway limit only; sessions | Check without a database |
| Seat events | Outbox into Kafka | Publish after; poll the DB | A waitlist is a new consumer |
| CDN and WAF | One-second lifetime, collapsing | Origin only; long lifetime | Shared answers cost one request |
| Seat map | Layout plus bitmap by version | Query per shopper; push all | Reads never touch the primary |
| Orders and holds | Saga; sweeper; reconciler | Redis TTL; release at expiry | Freeze before the call |

Each fix in Stage 6 rejects one tool by name:

| Deep dive | Rejected | Because |
|---|---|---|
| 6.1 | Read the seat, then update it | two fans both see free; one statement is the check and the change. |
| 6.2 | Holding seats in Redis with a TTL | the key and the database can disagree; two paths cover each other's gap. |
| 6.3 | Releasing the hold at the moment it expires | the payment may have succeeded in that instant; freeze before the call and reconcile silence. |
| 6.4 | Autoscaling the shop to a million at the door | scale lags the spike; a line in front and a dial behind it. |
| 6.5 | First-come at the gate | bots with faster connections win; a lottery for everyone present, then first-come. |
| 6.6 | Querying the seat table per shopper | ten thousand readers on the primary; an immutable layout and a versioned bitmap. |
| 6.7 | Rewriting booking to add a waitlist | a waitlist is a new consumer of the seat events, not a redesign. |
| 6.8 | Alerting on server health | the servers can be fine while seats sell twice; measure the promise, not the machine. |

<!-- /stack:summary -->

# Chapter 6 · Bridge

> **It works. Where does it break first?**

Version 3 has one order, an atomic claim, a hold with an expiry, a line in front of the shop, a pipeline for the map and
a payment path that expects silence. It has *not* been tested against: two fans on one seat; a fan who leaves; a
payment that arrives late; a million at the door; bots; ten thousand shoppers reading the map; a promoter who changes
the plan; or a failure nobody can see. These are the eight attack points on the baseline, taken in an order where
**each fix creates the next question.**

![The challenge map: eight attack points on the same baseline.](diagrams/video-map.pdf){width=100%}

\newpage

# Chapter 7 · Challenges

Each challenge runs the same way: **the question, the naive answer, a case with numbers, where it breaks, the fix, why it
works** (naming the property it protects), **the second-level push** ("what if the fix fails?"), a **second fix or an
honest limit**, and **what to say in the room**. The deep dive that follows each frame is the full mechanism, with the
SQL and the code.

## Challenge 1 · Two fans, one seat

**Two fans click the same seat in the same millisecond.** *The correctness crux, part one.* Protects **S1**.

| | |
|---|---|
| **The question** | "Two users click the same seat in the same millisecond. Walk me through it, mechanically." |
| **The naive answer** | Read the seat. If it is available, write the hold. |
| **The case** | Seat 102. Fan A and Fan B both read `AVAILABLE` at 10:00:01.120. Both write. Both pay. Two tickets for seat 102. |
| **Where it breaks** | The claim path in inventory: the check and the change are two steps with a gap between them. |
| **The fix** | One conditional `UPDATE` whose `WHERE` clause is the check. Rows locked in ascending order, `NOWAIT`, all or nothing. The loser gets a `409` with a fresh bitmap. |
| **Why it works** | **S1** by atomicity: whoever commits first wins; the other's condition is false and it changes zero rows. |
| **If the fix fails** | A bug elsewhere issues a second ticket, or the primary fails over mid-claim. |
| **Second fix** | `UNIQUE (event_id, seat_id)` on the ticket rejects the second insert, independently of our code. On failover, a synchronous replica: an unacknowledged claim never became a hold. |

![Attack and fix on the baseline.](diagrams/video-ch1-fix.pdf){width=85%}

::: {.key title="If asked, I would say"}
One conditional update is the check and the change, all or nothing, with rows locked in a stable order. The loser
fails in milliseconds and gets a fresh map. And the ticket table has a unique constraint on event and seat as an
independent guard.
:::

### Deep dive · the claim, in SQL and code

**The risk.** Two requests read "seat 102 is free", both write "seat 102 is mine", both pay: an
oversell. This is a classic **read-then-write race**: the check and the change are separate steps,
and another writer slips in between them.

**The mechanism.** Make the check and the change **one atomic step** inside the database: a
conditional `UPDATE` whose `WHERE` clause is the check. Whoever's update commits first wins; the
other's condition is false and it changes zero rows.

![Two fans, one seat. Fan A locks first and wins. Fan B fails immediately because of NOWAIT; without NOWAIT it would wait a few milliseconds and then match zero rows.](diagrams/sd47-seq-hold-race.pdf){width=78%}

```sql
BEGIN;
-- Step 1: lock the requested rows in a stable order (ascending seat_id).
-- NOWAIT: if any row is locked by another buyer, fail now instead of queueing behind them.
SELECT seat_id FROM event_seat
 WHERE event_id = :e AND seat_id = ANY(:seats)
 ORDER BY seat_id
 FOR UPDATE NOWAIT;

-- Step 2: the conditional claim. The WHERE clause IS the availability check.
UPDATE event_seat
   SET state = 'HELD', hold_id = :h,
       hold_expires_at = now() + interval '5 minutes',
       version = version + 1
 WHERE event_id = :e AND seat_id = ANY(:seats)
   AND (state = 'AVAILABLE'
        OR (state = 'HELD' AND hold_expires_at < now()))   -- lazy expiry, see challenge 2
RETURNING seat_id;
-- If fewer rows came back than were requested: ROLLBACK, answer 409 (all-or-nothing).

INSERT INTO hold (hold_id, event_id, user_id, seat_ids, status, expires_at, idem_key)
VALUES (:h, :e, :u, :seats, 'ACTIVE', now() + interval '5 minutes', :k);
INSERT INTO outbox (event_id, event_type, payload)
VALUES (:e, 'SeatsHeld', jsonb_build_object('holdId', :h, 'seats', :seats));
COMMIT;
```

The service code around it, in Java with Spring's `JdbcTemplate`:

```java
public HoldResult hold(long eventId, long userId, List<Integer> requested, String idemKey) {
    // A retry of the same click returns the first answer instead of holding twice.
    var previous = holds.findByUserAndKey(userId, idemKey);
    if (previous.isPresent()) return HoldResult.created(previous.get());

    limits.check(eventId, userId, requested.size());   // e.g. max 4 seats per account per event
    var seats = requested.stream().distinct().sorted().toList();
    var holdId = UUID.randomUUID();
    try {
        return tx.execute(status -> {
            lockRowsNowait(eventId, seats);               // step 1 above
            int claimed = claimIfFree(eventId, seats, holdId);   // step 2 above
            if (claimed != seats.size()) {                // someone holds at least one seat
                status.setRollbackOnly();
                return HoldResult.conflict(snapshots.current(eventId));
            }
            holds.insert(holdId, eventId, userId, seats, idemKey);
            outbox.append(eventId, "SeatsHeld", Map.of("holdId", holdId, "seats", seats));
            return HoldResult.created(holdId, Instant.now().plus(Duration.ofMinutes(5)));
        });
    } catch (CannotAcquireLockException e) {              // SQLSTATE 55P03 from NOWAIT
        return HoldResult.conflict(snapshots.current(eventId));
    } catch (DuplicateKeyException e) {                   // a parallel retry with this key won
        return HoldResult.created(holds.findByUserAndKey(userId, idemKey).orElseThrow());
    }
}
```

::: why
**Why lock in sorted order?** Imagine Fan A asks for seats [102, 101] and Fan B for [101, 102],
and each locks in the order given. A locks 102, B locks 101, then A waits for 101 and B waits for
102. Neither can proceed: a **deadlock**. PostgreSQL detects it after `deadlock_timeout` (1 s by
default) and kills one transaction. That's a 1-second stall on the hottest rows at the worst
moment. If everyone locks in ascending `seat_id` order, a cycle is impossible: whoever gets 101 first
also gets 102.

**Why `NOWAIT`?** Without it, B waits for A's lock. A's transaction lasts a few milliseconds, so B
waits a few milliseconds, then its `UPDATE` re-checks the condition, finds the seat `HELD`, and
updates zero rows: a 409 anyway. `NOWAIT` returns the same 409 sooner and, more importantly,
**doesn't hold a database connection while waiting**. On the front-row section, where hundreds of
fans click the same seats, waiting creates lock queues and connection exhaustion; failing fast
doesn't. **The trade-off:** if A's transaction then rolls back (rare), B was refused a seat that turned
out to be free. B has a fresh map and clicks again. Acceptable.

**Why all-or-nothing?** A fan who wants two seats together doesn't want one. Holding a partial set
would leave orphan single seats held for five minutes. So if any seat fails, the transaction rolls
back and nothing is held.

**Why is the 409 body a fresh bitmap?** The fan lost because their map was stale. Sending the
current map in the same response saves a round trip and makes the next click land on a free seat.
Under load that matters: 409s are frequent in hot sections, and each extra `GET` multiplies traffic.

**Why `UNIQUE (event_id, seat_id)` on `ticket` as well?** The state machine and the conditional update
should make double-selling impossible. The constraint is the independent check: if a bug in our code
ever tries to issue a second ticket for seat 102, the database rejects the insert. Two independent
guards are much less likely to fail together.
:::

::: why
**What happens to the old hold when lazy expiry steals its seat?** Fan A's hold expired at 10:07:00
and Fan C claimed seat 101 at 10:07:02. A's `hold` row still says `ACTIVE`, but the seat row now
carries C's `hold_id`. When A comes back and submits an order, the freeze step (challenge 3) checks
`WHERE hold_id = A's hold AND state = 'HELD'` and finds zero rows, so A is told *"your hold
expired"*. **The seat row is the truth; the hold row is bookkeeping.**
:::

![C4 Level 3: inside the inventory service. The claim engine and the outbox writer share one database transaction.](diagrams/sd47-c4-component.pdf){width=100%}

> "The claim is one conditional UPDATE, all-or-nothing, with rows locked in sorted order and NOWAIT,
> so a loser fails in milliseconds and gets a fresh map with the 409. Expired holds are claimable
> inside the same predicate, so correctness never depends on a cleanup job. And the ticket table has
> a unique constraint on event and seat as a last line of defence."

::: warn
**Weak answers to avoid.** "Use a distributed lock" (Redis `SETNX` per seat): a second system whose
failure modes you now own, and a lock lease that can expire mid-transaction. "Use SERIALIZABLE": it
works, but under contention it aborts many transactions with serialization failures, and you've
added retries for no benefit. "Use optimistic locking with a version column": it works for one
seat, but a multi-seat all-or-nothing claim with versions needs a version per seat and still ends in
a conditional update, so just write the conditional update.
:::

\newpage



\newpage
## Challenge 2 · The hold that outlives its owner

**The hold that outlives its owner.** Protects **L1**.

| | |
|---|---|
| **The question** | "A fan holds two seats and closes the laptop. Your sweeper is down for ten minutes. What do users see?" |
| **The naive answer** | A cleanup job every minute releases expired holds. |
| **The case** | 10:00:00 hold on 101 and 102, five minutes. 10:05:00 it expires. The job runs at 10:05:50: the map shows the seats taken for fifty seconds. If the job is down, the seats stay taken for everyone. |
| **Where it breaks** | Inventory, expiry: correctness depends on a job. |
| **The fix** | **Lazy expiry** inside the claim predicate (an expired hold is claimable at once) plus a **sweeper** every five seconds with `SKIP LOCKED`, batches of 500, announcing releases through the outbox. |
| **Why it works** | **L1**: correctness never depends on the job. The job only makes the map catch up. |
| **If the fix fails** | The sweeper releases a seat a buyer is paying for. |
| **Second fix** | The predicate says `state = 'HELD'`: a seat in `PAYMENT_PENDING` is never touched. A sweeper that is down costs *staleness, not oversell*; alert on the age of the oldest expired hold above 30 seconds. |

![The sweeper and the lazy path.](diagrams/video-ch2-fix.pdf){width=85%}

::: {.key title="If asked, I would say"}
Two expiry paths, each covering the other's gap. The claim treats an expired hold as free, so correctness does not
depend on a job. A sweeper releases in small batches and announces the release so the map catches up. If it dies we
get staleness, not oversell, and an alert on the oldest expired hold.
:::

### Deep dive · the expiry mechanism

**The risk.** A fan holds two seats and closes the laptop. If nothing releases the hold, those seats
are lost for the rest of the sale. If something releases them **too early**, we sell them while the
first fan is paying.

**The mechanism: two expiry paths, each covering the other's gap.**

![Lazy expiry and the sweeper. Fan C claims an expired seat directly; the sweeper releases seats nobody tried and announces them so the map shows them free.](diagrams/sd47-seq-expiry.pdf){width=88%}

1. **Lazy expiry** is the `OR (state = 'HELD' AND hold_expires_at < now())` in the claim predicate
   (challenge 1). An expired hold is claimable the instant it expires, whether or not any job has run.
   **Correctness never depends on the sweeper.**
2. **The sweeper** runs every 5 seconds, releases expired holds and **publishes `SeatsReleased`**, so
   the seat map shows those seats as free. Without it, expired seats would be claimable but invisible
   on everyone's map.

```sql
-- sweeper, every 5 s per hot event; several instances may run safely in parallel
WITH expired AS (
  SELECT event_id, seat_id
    FROM event_seat
   WHERE event_id = :e AND state = 'HELD' AND hold_expires_at < now()
   ORDER BY hold_expires_at
   LIMIT 500
   FOR UPDATE SKIP LOCKED              -- skip rows a buyer is claiming right now
)
UPDATE event_seat s
   SET state = 'AVAILABLE', hold_id = NULL, hold_expires_at = NULL, version = s.version + 1
  FROM expired x
 WHERE s.event_id = x.event_id AND s.seat_id = x.seat_id
RETURNING s.seat_id;
-- same transaction: INSERT INTO outbox ('SeatsReleased', {seats}), then COMMIT
```

::: why
**Why `SKIP LOCKED` here and `NOWAIT` in the claim?** They answer different questions. A buyer
needs *specific* seats, so if one is locked the answer is "no", and `NOWAIT` says so at once. The
sweeper needs *any* expired seats; if a buyer is claiming one right now, the sweeper doesn't care
about that one. It skips it and takes the next. That also means several sweeper instances never
block each other or a buyer.

**Why `LIMIT 500`?** Small batches keep each transaction short, so locks are held for milliseconds.
At 5-second intervals, 500 per batch releases 100 seats a second, far more than expire.

**Why does `PAYMENT_PENDING` never expire this way?** The predicate says `state = 'HELD'`. A seat
whose payment is in flight is frozen by design (challenge 3). Only the order service, once the payment
outcome is definite, can release it.
:::

::: {.load title="Under load: what if the sweeper is down for 10 minutes?"}
No incorrectness, only staleness. Expired seats are still claimable through the lazy predicate, but
the map shows them as taken, so fans don't click them and the sell-through slows. An alert fires on
**age of the oldest expired hold**: anything above 30 seconds means the sweeper isn't keeping up.
:::

![Seat state machine. PAYMENT_PENDING is the state weak designs miss; the sweeper never touches it.](diagrams/sd47-seat-states.pdf){width=55%}

> "Two expiry paths. The claim predicate treats an expired hold as free, so correctness doesn't
> depend on a job. A sweeper with SKIP LOCKED releases expired holds in small batches and publishes
> the release, so the map catches up. If the sweeper dies we get staleness, not oversell, and an
> alert on the oldest expired hold."

\newpage


\newpage
## Challenge 3 · The hold expires, then the payment succeeds

**The hold expires, then the payment succeeds.** *The correctness crux, part two, and the best probe in the round.* Protects **S2**.

| | |
|---|---|
| **The question** | "The hold expires while the payment provider is still thinking, then the payment succeeds. What do you do?" |
| **The naive answer** | The hold expired, so release the seat. If the payment arrives later, refund. |
| **The case** | 4:50 the fan submits. 5:00 the hold expires. 5:01 Fan C claims seat 101. 5:05 the provider answers *approved* for Fan A. Two people paid for one seat. |
| **Where it breaks** | Order service to inventory: nothing stops the seat being released while a payment is in flight. |
| **The fix (four parts)** | **Freeze** the seats (`HELD` to `PAYMENT_PENDING`, ten more minutes) *before* calling the provider. **Authorize, then capture.** A timeout is **unknown, not failed**: query by idempotency key, accept the webhook, first definite answer wins. **The residual case** refunds and apologises. |
| **Why it works** | **S2**: money is reserved before seats are sold, and every step is cheap to undo until the last. |
| **If the fix fails** | The provider stays silent for an hour. |
| **Second fix** | A reconciler with backoff and a freeze deadline; cancel with the provider, then release. The trade-off is explicit and goes to the product owner: *slower sell-through at the very end of the sale.* |

![Freeze, authorize, and a reconciler.](diagrams/video-ch3-fix.pdf){width=95%}

::: {.key title="If asked, I would say"}
I would rather hold a seat ten extra minutes than sell it twice or charge someone for nothing. Seats are frozen before I
call the provider, sold only on an approved authorization, and an unknown outcome stays frozen until a status check
or the webhook gives a definite answer. The cost is slower sell-through at the end, and I would show that trade-off to
the product owner.
:::

### Deep dive · the freeze, the authorization and the reconciler

**The risk.** A fan's hold lasts 5 minutes. They submit payment at 4:50. The PSP takes 15 seconds.
Meanwhile the hold expires, someone else claims the seat, and then the first payment comes back
**approved**. Now two people have paid for one seat, or one person has paid for nothing.

There's no perfectly clean answer. **Take a position and defend it.** Mine has four parts.

**1. Prevent it: freeze the seats before calling the PSP.** On `POST /orders`, atomically move the
seats from `HELD` to `PAYMENT_PENDING` with a longer deadline (+10 minutes). The expiry paths only
touch `HELD`, so a frozen seat can't be taken.

```sql
-- freeze: only succeeds if the hold is still the owner of every seat and not yet expired
UPDATE event_seat
   SET state = 'PAYMENT_PENDING', hold_expires_at = now() + interval '10 minutes',
       order_id = :o, version = version + 1
 WHERE event_id = :e AND hold_id = :h
   AND state = 'HELD' AND hold_expires_at > now()
RETURNING seat_id;
-- rows returned < seats in the hold -> ROLLBACK, tell the fan "your hold expired"
```

**2. Authorize, then capture.** Ask the PSP to **authorize** (reserve the money). Mark the seats
`SOLD` only after the authorization is approved. Then **capture** (take the money). If anything goes
wrong between authorize and capture, **void** the authorization: the reservation disappears and the
customer was never charged, so no refund flow is needed.

**3. Unknown is not failure.** On a PSP timeout, **query the payment status** by our idempotency key
with backoff, and accept the webhook too. Seats stay `PAYMENT_PENDING` until the outcome is
**definite**. A reconciliation job sweeps payments that stay unknown too long.

**4. The residual case.** If the PSP reports success *after* we gave up and released the seats, we
refund automatically, apologise, and give the fan priority on the waitlist. It's rare, it's
measured, and it has an owner.

![Order state machine. UNKNOWN is a real state with its own exits, not an error. VOIDED -> REFUNDED is the residual case.](diagrams/sd47-order-states.pdf){width=55%}

![Checkout when the PSP goes silent: the authorization times out, the order becomes UNKNOWN, status polling and the webhook race, and the first definite answer wins.](diagrams/sd47-seq-checkout.pdf){width=78%}

The order service, step by step:

```java
// POST /orders  ->  202 Accepted; the fan polls GET /orders/{id}
public OrderView placeOrder(long userId, UUID holdId, String paymentToken, String idemKey) {
    Order order = orders.insertOrGet(userId, idemKey, holdId);   // UNIQUE(user_id, idem_key)
    if (order.status() != Status.PENDING) return view(order);    // a retry: just report state
    if (!inventory.freeze(holdId, order.id(), Duration.ofMinutes(10))) {
        orders.markFailed(order.id(), "hold expired");
        return view(order);
    }
    orders.markAuthorizing(order.id());
    pspExecutor.submit(() -> authorize(order, paymentToken));   // bounded pool: ~300 threads
    return view(order);
}

void authorize(Order order, String paymentToken) {
    String pspKey = "order-" + order.id() + "-1";   // the PSP dedupes retries on this key
    try {
        AuthResult r = psp.authorize(order.amount(), order.currency(), paymentToken, pspKey,
                                     Duration.ofSeconds(10));
        switch (r.status()) {
            case APPROVED -> confirm(order, r.authorizationId());
            case DECLINED -> fail(order, r.declineReason());
        }
    } catch (PspTimeoutException | PspUnavailableException e) {
        orders.markUnknown(order.id());              // NOT failed: the money may have moved
        reconciler.scheduleCheck(order.id(), Duration.ofSeconds(2));
    }
}

void confirm(Order order, String authId) {
    // Three callers (the authorize call, the reconciler, the webhook) may race here.
    // The conditional status change makes confirm idempotent: only the first one proceeds.
    if (!orders.transition(order.id(), Set.of(AUTHORIZING, UNKNOWN), CONFIRMING)) return;
    inventory.sell(order.holdId(), order.id());      // idempotent RPC: PAYMENT_PENDING -> SOLD
    orderTx.execute(s -> {                           // one local transaction in the Order DB
        orders.markConfirmed(order.id(), authId);
        tickets.issue(order);                        // UNIQUE(event_id, seat_id) guards oversell
        outbox.append("OrderConfirmed", order.id()); // capture worker + notifications consume it
        return null;
    });
}
```

```java
// Reconciler: every 2 s, for orders whose outcome is still unknown
@Scheduled(fixedDelay = 2000)
void reconcile() {
    for (Order o : orders.findUnknownDue(clock.instant(), 200)) {
        PspStatus st = psp.lookup("order-" + o.id() + "-1");
        switch (st.kind()) {
            case AUTHORIZED -> confirm(o, st.authorizationId());
            case DECLINED   -> fail(o, "declined");
            case NOT_FOUND  -> {                     // the request may never have reached the PSP
                if (o.age().compareTo(Duration.ofMinutes(2)) > 0) fail(o, "never reached PSP");
                else orders.backoff(o.id());
            }
            case PROCESSING -> {
                if (o.freezeDeadline().isBefore(clock.instant())) {
                    psp.cancel("order-" + o.id() + "-1");   // void if it ever authorizes
                    fail(o, "payment timed out");           // releases the seats
                } else {
                    orders.backoff(o.id());                 // 2 s, 4 s, 8 s ... capped at 60 s
                }
            }
        }
    }
}
```

```java
// POST /psp/webhooks : the PSP tells us an outcome
@PostMapping("/psp/webhooks")
ResponseEntity<Void> webhook(@RequestBody String body,
                             @RequestHeader("Psp-Signature") String signature) {
    if (!hmac.verify(body, signature, webhookSecret)) return ResponseEntity.status(401).build();
    PspEvent ev = PspEvent.parse(body);
    if (!processedEvents.insertIfAbsent(ev.id())) return ResponseEntity.ok().build(); // seen it
    Order o = orders.byPspKey(ev.idempotencyKey());
    switch (ev.type()) {
        case AUTHORIZED -> confirm(o, ev.authorizationId());
        case DECLINED   -> fail(o, ev.reason());
        default         -> { }                        // captures, refunds: recorded elsewhere
    }
    return ResponseEntity.ok().build();               // 2xx so the PSP stops retrying
}
```

::: why
**Why authorize then capture, instead of one "charge" call?** A charge moves money at once. If we
then can't give the seats (they were lost, or a bug), we must **refund**: slow, visible on the
statement, costly, and a support ticket. An authorization only *reserves* the money. Until we
capture, backing out is a **void**, which the customer never sees as a charge. So the ordering is:
reserve money → secure seats → take money. Each step can be undone cheaply until the last.

**Why is a timeout "unknown" and not "failed"?** A timeout means we didn't hear the answer, not that
there wasn't one. The PSP may have authorized the card a millisecond before the connection dropped.
If we treated that as a decline and released the seats, someone else could buy them, and the first
fan would be charged for nothing. **So we keep the seats frozen and ask again.** The PSP's
idempotency key makes asking safe: a retried `authorize` with the same key returns the original
result instead of reserving the money twice.

**Why both a status query and a webhook?** Either can fail: the webhook may be delayed or lost, and
the status endpoint may be slow during the same outage. Whichever gives a definite answer first
wins. `confirm` is idempotent (the conditional status transition), so it doesn't matter if both
arrive.

**Why verify the webhook signature?** Anyone can POST to a public URL. Without the HMAC check, an
attacker could send *"order-91 authorized"* and get free tickets.

**Why is capture asynchronous?** Capture almost never fails once authorized, and when it does it can
be retried for days. Keeping it off the fan's critical path makes confirmation faster.
:::

> "I'd rather hold a seat ten extra minutes than sell it twice or charge someone for nothing. The
> seats are frozen before I call the PSP, they're sold only on an approved authorization, and an
> unknown outcome stays frozen until a status check or the webhook gives a definite answer. The cost
> is slightly slower sell-through at the very end of the sale. I'd show that to the product owner as
> the explicit trade-off."

::: warn
**The traps in this probe.** Treating a timeout as a decline (charges people for nothing). Retrying
`authorize` without an idempotency key (double reservation). Holding the inventory database
transaction open while calling the PSP (minutes of row locks and a pinned connection per order: at
250 in flight that's the whole pool). Letting the hold sweeper release `PAYMENT_PENDING` seats (the
exact race this deep dive is about).
:::

\newpage



\newpage
## Challenge 4 · A million at the door

**A million at the door, and the line in front of it.** *Challenges 4 and 5 share one section below: the stampede (this one) and the fair line (next).* Protects **L3**.

| | |
|---|---|
| **The question** | "A million users hit your inventory database at once. What breaks?" |
| **The naive answer** | Autoscale the database and the API fleet. |
| **The case** | 33,333 writes a second on 50,000 rows. Each waits on a row lock while holding a connection; a pool of a few hundred empties in milliseconds; timeouts; retries; a retry storm. |
| **Where it breaks** | The whole front: gateway to inventory. |
| **The fix** | A waiting room: a lobby, a position, admission at a rate $R$ chosen from shop capacity (Little's law: 10,000 shoppers over 5 minutes is 2,000 a minute). The poll answer is the *same for everyone*, so the CDN holds it. An **admission controller** adjusts $R$ by shop health (increase slowly, cut fast), with a slow start. A pointer advanced by one Lua script. An admission token checked at the gateway. |
| **Why it works** | **L3**: the core only sees what it chose to admit. Demand is absorbed at the edge. |
| **If the fix fails** | The controller dies, or the CDN cannot reach the origin. |
| **Second fix** | One leader per event by lease; the pointer simply pauses. `stale-if-error` at the CDN. Jitter on every synchronised action. Double the fans changes the lobby size, not the database load. |

![The line in front of the shop.](diagrams/video-ch4-fix.pdf){width=85%}

::: {.key title="If asked, I would say"}
I convert a stampede into a stream. A million people wait at the edge for almost nothing each; a controller admits them at
a rate the shop can serve, and cuts that rate when hold latency or the payment error rate rises. The database only ever
sees what I chose to admit.
:::


\newpage
## Challenge 5 · A fair line, and the bots

**A fair line, and the bots.** *Part two of the waiting-room section.* Protects **fairness**.

| | |
|---|---|
| **The question** | "What does fair mean, and how do you stop a bot holding all 50,000 seats?" |
| **The naive answer** | Strict first-come-first-served from T0. |
| **The case** | The order is decided in the first few hundred milliseconds. Data-centre bots at five milliseconds take the first thousands of places, and everybody refreshes at 09:59:59. |
| **Where it breaks** | The waiting-room join. |
| **The fix** | A **lottery** among everyone present before T0 (a random score drawn server-side at join time, `ZADD NX`), late arrivals first-come behind. Signed queue tokens bound to the account. One entry per verified account. Purchase limits per account and per card. A challenge at the lobby. Pre-registered fans for flagship events. **It is a product decision, taken to the promoter.** |
| **Why it works** | Fairness is the removal of an advantage that speed gives. A random draw at join time costs nothing at T0. |
| **If the fix fails** | An account farm passes verification. |
| **Second fix** | Limits per payment card and per device; cancel flagged orders after the sale and release them to the waitlist. The honest limit: no scheme is bot-proof, the aim is to make bots expensive. |

![A fair line.](diagrams/video-ch5-fix.pdf){width=85%}

::: {.key title="If asked, I would say"}
Fairness is a product decision, so I would take it to the promoter: a lottery for everyone in the lobby at T0, then
first-come. Each place is a signed number, so it cannot be forged or traded. And I would make bots expensive with one
entry per verified account and limits per card.
:::

### Deep dive · the waiting room (challenges 4 and 5): the lottery, polling, admission, bots

This is the deep dive that decides the round, because it's where the million fans are.

#### The fairness question, and why a lottery

**The risk.** If the line is strictly first-come-first-served at T0, the order is decided in the first
few hundred milliseconds after 10:00:00. Who wins that race? Whoever has the lowest network latency
to our servers, the fastest device, and above all **bots** that fire at exactly T0 from data centres.
It also encourages a million people to hammer *refresh* at 09:59:59, which is a self-inflicted
load spike.

**The mechanism: a lottery among early arrivals.** Everyone who is in the lobby **before T0** is
treated the same: at T0 they're put in a **random order**. Arriving at 09:30 or 09:59 makes no
difference. Anyone arriving **after** T0 joins the back of the line in arrival order (FIFO), behind
every lobby fan.

::: why
**Why is that fair, and is it fair to people who came early?** The lottery removes the only
advantage that FIFO-at-T0 gives: speed in the first second, which mostly rewards bots and good
networks. Coming 30 minutes early earns nothing over coming one minute early, by design. That's
deliberate: otherwise fans would camp for hours and the lobby would open ever earlier. Coming
*before* T0 still beats coming after, so there's a clear reason to be on time. This is a **product
policy**; the lobby page must state the rule ("everyone here at 10:00 gets a random place"). Ticketmaster
and other large ticketing sites use this pattern. In the room, name it as a product decision you would
take to the promoter, not as an engineering fact.

**Why a random score at join time rather than a shuffle at T0?** They're equivalent: giving every
entrant an independent uniform random number and sorting by it produces a uniformly random order of
everyone present at T0. Doing it at join time means T0 itself costs nothing: no batch job has to
shuffle a million entries in the critical second. The score is generated **server-side** with a
cryptographic random generator and never sent to the client, so nobody can see or influence their
draw before T0.

**What stops someone re-joining until they get a good number?** `ZADD NX`: re-joining with the same
account keeps the first score. And one queue entry per verified account (see bots below).
:::

#### The code: join, the T0 flip, and "what's my number?"

The join is one Lua script, so the phase check and the write are atomic. A join racing the T0 flip
lands cleanly on one side of it.

```lua
-- join.lua  KEYS: phase:{e}, lobby:{e}, next:{e}, seqOf:{e}
--           ARGV: userId, randomScore (from SecureRandom in the service, never shown to clients)
local phase = redis.call('GET', KEYS[1])
if phase == 'LOBBY' then
  redis.call('ZADD', KEYS[2], 'NX', ARGV[2], ARGV[1])   -- NX: re-joining keeps the first draw
  return {'LOBBY', 0}
end
if redis.call('ZSCORE', KEYS[2], ARGV[1]) then           -- a lobby fan re-opening the page
  return {'LOBBY', 0}                                    -- (they ask /queue/me for their seq)
end
local existing = redis.call('HGET', KEYS[4], ARGV[1])
if existing then return {'QUEUE', tonumber(existing)} end  -- idempotent re-join after T0
local seq = redis.call('INCR', KEYS[3])                   -- late arrivals: plain FIFO
redis.call('HSET', KEYS[4], ARGV[1], seq)
return {'QUEUE', seq}
```

```lua
-- open_queue.lua, run once at T0 by the scheduler. Safe to run twice.
-- KEYS: phase:{e}, lobby:{e}, next:{e}
if redis.call('GET', KEYS[1]) == 'QUEUE' then return redis.call('GET', KEYS[3]) end
redis.call('SET', KEYS[1], 'QUEUE')
local n = redis.call('ZCARD', KEYS[2])   -- lobby size: lobby fans hold numbers 1..n
redis.call('SET', KEYS[3], n)            -- the first late arrival gets n + 1
return n
```

```java
// GET /events/{e}/queue/me  - lobby fans call this once after T0 (with 0-20 s client jitter)
public SignedSeq myNumber(QueueToken token) {
    verifier.verify(token);                               // our signature, this event
    if (token.kind() == Kind.QUEUE) return SignedSeq.of(token.seq());
    Long rank = redis.zrank("lobby:{" + token.eventId() + "}", token.userId());   // O(log n)
    if (rank == null) throw new NotInLobby();
    return signer.sign(token.eventId(), token.userId(), rank + 1);   // seq is 1-based
}
```

::: load
**At T0, ~1M `queue/me` calls arrive within 20 seconds**, ~50,000/s, each one `ZRANK` on one sorted
set. `ZRANK` is O(log n), about 20 steps for a million entries, and Redis runs ~100,000 such commands
a second per node. It fits on the event's node, just. **If it didn't**, precompute: a background job
walks the sorted set once (`ZRANGE` in chunks of 10,000) and writes each fan's `seq` into the
`seqOf:{e}` hash, so `queue/me` becomes an `HGET`. The client-side 0–20 s jitter is what turns a
one-millisecond spike into a 20-second plateau. **The sorted set itself** is about 100 bytes per
entry, so ~100 MB for a million fans: fine on one node.
:::

#### Polling the shared state through the CDN

The waiting client needs one piece of information: *has my number come up?* The poll answers it
with a response that is **identical for every fan**:

```http
GET /events/evt-7731/queue/state HTTP/1.1

HTTP/1.1 200 OK
Content-Type: application/json
Cache-Control: public, max-age=1, stale-while-revalidate=2, stale-if-error=30

{"admittedUpTo": 31800, "ratePerMin": 2000, "soldOut": false, "serverTime": 1792131002}
```

::: why
**Why the response has no user in it.** A CDN can only cache a response that is the same for
everyone who asks. *"You are 380,577th"* is different for every fan, so it can't be cached: a
million fans would mean a million origin requests. *"The line has reached number 31,800"* is the same
for everyone. The client already knows its own `seq` (it's in the signed token) and does the
subtraction itself. **Moving one subtraction to the client turns an uncacheable request into a
cacheable one.** That's the core trick of the whole waiting room.

**What the headers mean.** `public, max-age=1`: any cache, including the CDN, may serve this copy
for one second. `stale-while-revalidate=2`: for two more seconds the CDN may keep serving the old
copy *while* it fetches a new one in the background, so no fan waits on the refresh.
`stale-if-error=30`: if our origin is failing, keep serving the last good copy for 30 seconds. A
fan sees the line pause instead of an error page.
:::

::: {.why title="Why does the CDN cache it for exactly one second?"}
The TTL trades **origin load** against **freshness**:

- **Origin load** is roughly *number of CDN edges ÷ TTL*. With ~200 edges and a 1-second TTL, the
  origin sees ~200 requests a second (or ~1 a second with an origin shield). With no caching it
  would see all 100,000.
- **Freshness** is set mostly by the **client's polling interval** (~10 s), not by the TTL. A 1-second
  TTL adds at most one second to a ten-second wait, which nobody notices. The pointer moves about 33
  places a second, so a 1-second-old value is at most ~33 places behind.

**Why not longer, say 10 seconds?** The origin load is already negligible at 1 s, so there's nothing
left to save. A 10-second TTL would double the worst-case delay before a fan notices their turn,
make the line visibly jump in steps of ~330, and slow the **sold-out** message, which should reach
970,000 people as fast as possible.

**Why not shorter, or zero?** Zero means no caching and 100,000 req/s at the origin. Sub-second
TTLs aren't reliably supported by all CDNs and buy no freshness the 10-second polling interval
would let anyone see.

**So 1 second is the point where origin load is already tiny and freshness is already as good as
the polling interval allows.** In the room: *"one second, because the origin cost is already
negligible and fans poll every ten seconds anyway."*
:::

The client loop, with **adaptive polling**: fans far back in the line poll less often.

```javascript
async function waitForTurn(eventId, queueToken, mySeq) {
  for (;;) {
    const s = await (await fetch(`/events/${eventId}/queue/state`)).json();  // CDN-served
    if (s.soldOut) return showSoldOut(eventId);
    const ahead = mySeq - s.admittedUpTo;
    if (ahead <= 0) return admit(eventId, queueToken);       // POST /admit
    showPosition(ahead, Math.ceil(ahead / s.ratePerMin));     // "about N minutes"
    await sleep(pollDelayMs(ahead));
  }
}

// Far from the front: poll rarely. Near the front: poll often. Always add jitter (+-20%)
// so a million clients that started together don't stay synchronised.
function pollDelayMs(ahead) {
  const base = ahead > 50_000 ? 30_000 : ahead > 5_000 ? 10_000 : 3_000;
  return base * (0.8 + Math.random() * 0.4);
}
```

::: load
**Adaptive polling cuts the 100,000 req/s further.** About 950,000 of the million fans are more than
50,000 places back, so they poll every 30 s instead of 10. Total: ~32,000 + ~5,000 + small change
~ **37,000 req/s** at the CDN. It's a cheap win and a good sentence in the room, but the design
doesn't depend on it: the CDN handles 100,000 req/s anyway.
:::

#### The admission controller: turning the dial

![The admission control loop, once a second per event. It's the same idea as TCP congestion control: increase gently while healthy, cut sharply on trouble (AIMD).](diagrams/sd47-admission-loop.pdf){width=55%}

```java
@Scheduled(fixedRate = 1000)                  // one active instance per event (leader-elected)
void tick() {
    for (long e : onSales.active()) {
        Signals s = metrics.read(e);          // shoppers, hold p99, DB CPU, PSP errors, 409 ratio
        double r = rates.get(e);              // fans per minute
        if (s.holdP99Millis() > 300 || s.dbCpu() > 0.70 || s.pspErrorRate() > 0.05) {
            r = Math.max(MIN_RATE, r * 0.7);  // multiplicative decrease: back off fast
        } else if (s.activeShoppers() < TARGET_SHOPPERS) {   // 10,000
            r = Math.min(MAX_RATE, r + RAMP_STEP);           // additive increase: ramp slowly
        }
        rates.put(e, r);
        long n = carry.take(e, r / 60.0);     // whole fans this second; fractions carried over
        redis.eval(ADVANCE_LUA, keysFor(e), n, (long) r, soldOutDecision(e, s));
    }
}
```

```lua
-- advance.lua  KEYS: admittedUpTo:{e}, next:{e}, rate:{e}, soldOut:{e}
-- Never admit past the last issued number: there's nobody there yet.
local cur  = tonumber(redis.call('GET', KEYS[1]) or '0')
local last = tonumber(redis.call('GET', KEYS[2]) or '0')
local new  = math.min(cur + tonumber(ARGV[1]), last)
redis.call('SET', KEYS[1], new)
redis.call('SET', KEYS[3], ARGV[2])
redis.call('SET', KEYS[4], ARGV[3])
return new
```

::: why
**Why a feedback loop instead of a fixed R?** Our capacity estimate (10,000 shoppers) is a guess
until the sale is running. Real capacity depends on how fast fans pick seats, how slow the PSP is
today, and how hot one section is. The controller measures and adjusts. **Why "slow start"?** At T0
every cache is cold and every connection pool is empty. Starting at a quarter of the target rate and
ramping is cheaper than discovering the limit by falling over. **Why cut by 30% but grow by a small
step?** Overload makes things worse quickly (retries, queues); under-admission only wastes a little
time. So react fast to bad signals and slowly to good ones. **Why one active instance per event?**
Two controllers both advancing the pointer would admit double. A simple lease (a Redis key with a
TTL, renewed every second) makes one instance the leader; if it dies, another takes over within a
few seconds and the pointer just pauses meanwhile.
:::

#### Admission: exchanging the queue token

```java
// POST /events/{e}/admit
public AdmissionToken admit(QueueToken qt) {
    verifier.verify(qt);
    long seq = resolveSeq(qt);                           // token seq, or lobby rank + 1
    long pointer = redis.getLong("admittedUpTo:{" + qt.eventId() + "}");
    if (seq > pointer) throw new NotYourTurnYet(seq - pointer);  // client clock or cache skew
    // First admission wins; asking again returns the same token, never a fresh 10 minutes.
    String key = "admitted:{" + qt.eventId() + "}:" + qt.userId();
    AdmissionToken fresh = signer.admission(qt.eventId(), qt.userId(), Duration.ofMinutes(10));
    String stored = redis.setIfAbsentOrGet(key, fresh.serialized(), Duration.ofHours(6));
    AdmissionToken token = AdmissionToken.parse(stored);
    if (token.expired()) throw new ShoppingWindowEnded();   // TIMED_OUT in the fan state machine
    return token;
}
```

::: why
**What is admission, in one line?** Moving one fan from "waiting" to "allowed to shop", proven by a
token. **Why can't a fan skip the queue by calling `/holds` directly?** The gateway rejects any shop
call without a valid admission token for that event, and only `/admit` issues one, only when
`seq <= admittedUpTo`, and `seq` is inside a token we signed. **Why does a second `/admit` return the
same token?** Otherwise a fan could refresh their 10-minute window indefinitely and occupy a shopping
slot forever. When the window ends, it ends. The fan can rejoin the back of the line if the sale is
still on.
:::

#### The sold-out signal

Two stages, because "sold out" is a prediction until it isn't:

1. **`admissionPaused` ("likely sold out").** When *available seats ÷ 2.5* drops below the number of
   admitted fans still shopping, we stop admitting. Everyone already inside can probably absorb
   what's left. Waiting fans see *"Tickets are likely sold out. Stay if you like: seats may come back."*
2. **`soldOut` (final).** When no seat is `AVAILABLE` or `HELD`, only `PAYMENT_PENDING` or `SOLD`,
   for a few minutes. If holds expire and seats come back, the controller resumes admission from
   where the pointer stopped.

::: why
**Why two stages?** Declaring sold out too early leaves seats unsold if admitted fans don't buy.
Declaring it too late wastes the time of 970,000 people. The first stage stops the waste; the second
is the truth. Both flags travel in the same cached JSON, so they reach everyone within one poll.
:::

#### Bots

- **Challenge at lobby entry** (CAPTCHA or an invisible browser challenge from the WAF).
- **One queue entry per verified account**, with a phone number or a payment card on file, bound to a
  device fingerprint. Account farms are the real attack, so verification makes accounts expensive.
- **Purchase limits per account and per payment card**: the card limit catches one buyer with many
  accounts.
- **Tokens are signed and short-lived**, and the admission token is bound to the user id, so a token
  can't be sold or shared at scale.
- **Verified-fan pre-registration** for flagship events: fans register days ahead and are screened
  offline. Only registered fans may join.
- **After the sale**: cancel orders flagged by fraud scoring and release the seats to the waitlist.

> "Fairness is a product decision, so I'd take it to the promoter: a lottery for everyone in the
> lobby at T0, then first-come-first-served. Each fan's position is computed client-side from a
> signed sequence number and one cached pointer, so a waiting fan costs us almost nothing. An
> admission controller moves the pointer at a rate it adjusts from shop health, and a sold-out flag
> in the same cached response tells the 98% within seconds."

\newpage



\newpage
## Challenge 6 · The seat map for ten thousand shoppers

**The seat map for ten thousand shoppers.** Protects **L2** and **L3**.

| | |
|---|---|
| **The question** | "Is a user allowed to see a seat as available and then fail to get it?" |
| **The naive answer** | Each shopper reads the seat table every two seconds. |
| **The case** | 10,000 shoppers every 2 seconds is 5,000 reads a second against the same rows the claims lock; the claim p99 climbs. |
| **Where it breaks** | Inventory serving both reads and writes. |
| **The fix** | The **layout** is immutable and lives on the CDN. The **availability** is a bitmap (50,000 bits, 6.25 KB) built from the event log and published at most once a second to a cache; clients send the version they have and get **304** when nothing changed; admitted fans only. |
| **Why it works** | **L2/L3**: the claim is authoritative and the map is a hint. A stale click fails in milliseconds with a fresh map. |
| **If the fix fails** | The stream stalls. |
| **Second fix** | Staleness grows, never incorrectness. A click gets a `409` with the current bitmap. The map is rebuilt from a scan. The log offset as the version never goes backwards. |

![The seat-map pipeline.](diagrams/video-ch6-fix.pdf){width=85%}

::: {.key title="If asked, I would say"}
The map can be a second or two stale because the write path decides. The layout is immutable on the CDN and the
availability is a 6-kilobyte bitmap, rebuilt once a second from the event stream and served by version. A stale click
fails fast with a fresh map.
:::

### Deep dive · the seat map pipeline

**The risk.** 10,000 shoppers refreshing a 50,000-seat map every 2 seconds is 5,000 reads a second.
Served from the inventory database, that would compete with the holds for the same rows and
connections, which is exactly the "mixed paths" failure from Chapter 5.

**The mechanism: split the map into an immutable part and a live part.**

- The **layout** (seat positions, sections, prices) never changes during a sale. It's an SVG plus a
  seat list, served from the CDN under a versioned URL and cached for a year.
- The **availability** is one bit per seat: 50,000 bits = 6.25 KB. A **snapshot builder** keeps it in
  memory from the Kafka stream, and **at most once a second** publishes a new version to Redis.
  Clients send the version they have and get **304 Not Modified** when nothing changed.

![From a committed hold to a fan's map: outbox row, log-based relay, Kafka, the snapshot builder, a versioned bitmap in Redis, and the 304 path.](diagrams/sd47-seq-seatmap.pdf){width=96%}

```java
// The snapshot builder: a Kafka consumer group, partitioned by event_id
final class SnapshotBuilder {
    private final Map<Long, BitSet> free = new ConcurrentHashMap<>();
    private final Map<Long, Long> lastOffset = new ConcurrentHashMap<>();
    private final Set<Long> dirty = ConcurrentHashMap.newKeySet();

    @KafkaListener(topics = "seat-events")
    void on(ConsumerRecord<Long, SeatEvent> rec) {
        long e = rec.key();
        BitSet bits = free.computeIfAbsent(e, this::loadFromDatabase);  // cold start: one scan
        boolean available = rec.value().type() == SeatEventType.RELEASED;
        synchronized (bits) {
            rec.value().seatIds().forEach(seat -> bits.set(seat, available));
        }
        lastOffset.put(e, rec.offset());     // the Kafka offset doubles as the map version
        dirty.add(e);
    }

    @Scheduled(fixedRate = 1000)             // at most one new version per event per second
    void publish() {
        for (long e : List.copyOf(dirty)) {
            dirty.remove(e);
            byte[] bytes;
            BitSet bits = free.get(e);
            synchronized (bits) { bytes = bits.toByteArray(); }
            long v = lastOffset.get(e);
            redis.set("map:{" + e + "}:" + v, bytes, Duration.ofMinutes(2));
            redis.set("map:{" + e + "}:v", Long.toString(v));    // flip the pointer last
        }
    }
}
```

```java
// GET /events/{e}/availability?v=812
@GetMapping("/events/{e}/availability")
ResponseEntity<byte[]> availability(@PathVariable long e,
                                    @RequestParam(defaultValue = "-1") long v) {
    long current = Long.parseLong(redis.get("map:{" + e + "}:v"));
    if (v == current) return ResponseEntity.status(HttpStatus.NOT_MODIFIED).build();
    return ResponseEntity.ok()
            .header("X-Map-Version", Long.toString(current))
            .cacheControl(CacheControl.noStore())          // admitted users only; not CDN-cached
            .body(redis.getBytes("map:{" + e + "}:" + current));
}
```

::: why
**Why is a stale map acceptable?** Because **the write path is authoritative**. The map is a hint
for the fan's eye; the claim in PostgreSQL decides. If a fan clicks a seat that was taken 800 ms
ago, the hold fails in milliseconds with a 409 and a fresh map. That's a graceful failure, not a bug.
The requirement said "within a couple of seconds", and we deliver ~1–2 s.

**Why rebuild at most once a second?** During the peak there are ~50 seat changes a second. Publishing
a new version for each would mean 50 versions a second and almost no 304s. Batching per second gives
one version a second, so a client polling every 2 seconds gets a 200 at most every other time.

**Why the Kafka offset as the version?** It only ever grows, it survives a builder restart (the
builder resumes from its committed offset), and two builder instances reading the same partition
agree on it. A counter in memory would reset on restart, and clients would see version numbers go
backwards.

**Why the outbox and a log-based relay?** The seat change and the event announcing it commit in the
same transaction, so they can't disagree. Debezium reads the PostgreSQL write-ahead log and publishes
each outbox row to Kafka. If the relay is down, rows wait in the log and nothing is lost. Part III
explains it further.

**Why 304 and not just a cheap 200?** A 304 has no body: a few hundred bytes instead of 6 KB. At
5,000 req/s that's the difference between ~30 MB/s and ~1 MB/s, and the fan's browser does no
re-render.

**What about pushing changes?** For admitted fans only (10,000 connections, not a million), the
seat-map service can push deltas over **SSE**: *"seats 101, 102 taken"*. It's a nice upgrade for
phase 2, but polling a 6 KB bitmap is good enough and has fewer moving parts.
:::

> "The layout is immutable and on the CDN. Availability is a 6 KB bitmap rebuilt at most once a
> second from the event stream and served from Redis by version, with 304s when nothing changed. It
> can be a second or two stale because the claim is authoritative: a stale click fails fast with a
> fresh map."

\newpage



\newpage
## Challenge 7 · Requirements that arrive mid-sale

**Requirements that arrive mid-sale.** *The extension seams.*

| | |
|---|---|
| **The question** | "The promoter wants to release 5,000 more seats mid-sale." Then: "Add a waitlist." Then: "A 20-date tour with ten times the traffic." |
| **The naive answer** | Redesign, or restart the sale. |
| **The case** | 45,000 are sold. 5,000 rows must appear under live contention; the layout and the map are cached; a sold-out flag has already reached 970,000 people. |
| **Where it breaks** | The layout cache, the sold-out flag, per-event limits. |
| **The fix** | Insert the rows as `AVAILABLE` in one transaction, publish a new layout version (a new CDN key), clear the flag, let the controller resume. The waitlist is a **new consumer** of seat-released events, giving a *targeted hold*. "Best available" is an allocator that hands different fans different seats. The tour: everything is keyed by event; mega events get their own cell; the payment budget is split; **one active queue per account per tour**. |
| **Why it works** | The seams were there. The claim path does not change; new demand lands as consumers and read models. |
| **If the fix fails** | Two mega events share a Redis node or a payment budget. |
| **Second fix** | Pin hot slots and move to a dedicated cell the day before (on-sales are scheduled); stagger on-sales; split the budget. |

![The waitlist is a new consumer.](diagrams/video-ch7-fix.pdf){width=85%}

::: {.key title="If asked, I would say"}
Say what changes, what does not, and what it costs. Releasing seats is an insert and a new layout version; the claim
does not move. The waitlist is a new consumer on the stream. A tour is an isolation problem, not a coordination one,
because everything is keyed by event.
:::

### Deep dive · several events on sale at once

**The question you'll get:** *"A 20-date stadium tour goes on sale on Friday at 10:00 for all
dates at once, and three other big shows open the same morning. What changes?"*

**The key idea:** everything in this design is **keyed by `event_id`**: the Redis keys, the database
partitions, the Kafka partition key, the admission token's `evt` claim, the CDN cache key. So events
are **independent by construction**. Running many at once isn't a coordination problem; it's an
**isolation** problem: one huge on-sale mustn't hurt the others, and the few resources they *do*
share must be divided fairly.

![Many events at once. Stateless fleets and the CDN are shared. Each event's queue state is one Redis slot. Inventory is placed per event: thousands of small events packed into a shared cell, a mega on-sale in its own cell.](diagrams/sd47-multi-event.pdf){width=86%}

**Layer by layer:**

| Layer | What's per event | What's shared, and how it's protected |
|------|------------------|------------------------------------|
| CDN | Cache key includes the event id: one `queue/state` per event | The CDN itself. It's built for this; nothing to do |
| Gateway, waiting-room pods | Nothing; they're stateless | Autoscaled **ahead of** scheduled on-sales from the on-sale calendar, not reactively |
| Redis (queue state) | All of an event's keys share one hash slot via `{event_id}` | Two mega events could hash to the same node: **pin** hot events' slots to separate nodes before the sale (Redis Cluster can migrate slots) |
| Admission controller | One control loop and one R per event | A **global budget** caps the sum of all Rs (see below) |
| Inventory + PostgreSQL | An **event directory** maps `event_id` → cell and shard | Small events packed many per shard; a mega event is moved to a **dedicated cell** days before. Its data is 50,000 rows, so the move is trivial |
| Kafka | Partition key `event_id` keeps each event in order | Partitions spread across brokers; 500 messages/s per event is nothing |
| PSP | Checkout pool per event | **Contracted throughput is global**: divide it across events |

**The routing lookup**, cached in every pod for 30 seconds:

```java
record Placement(String cell, String dbShard, boolean queueEnabled,
                 int maxRatePerMin, int pspShareAuthPerSec) {}

Placement placementFor(long eventId) {
    return placementCache.get(eventId, directory::load);   // tiny table, rarely changes
}
```

::: why
**What is a "cell"?** A complete, independent copy of the shop's stateful stack: inventory and order
pods, their databases, their connection pools. A failure or overload in one cell can't spread to
another, like the watertight compartments (bulkheads) in a ship. Most events share one cell because
they're small. A known mega on-sale gets its own, so if it melts down, the other 2,000 events on sale
that day don't notice.

**Why place events in advance and not react?** On-sales are **scheduled** weeks ahead, and the
promoter announces them. That's a gift: we know the demand curve's timing exactly. Pre-scaling
fleets, pinning Redis slots and moving the event's inventory to its own cell the day before is
cheaper and safer than any autoscaler reacting to a spike at T0.
:::

**The shared resources, and how they're divided:**

- **The PSP.** Suppose our contract allows 300 authorizations a second. Twenty tour dates at ~25/s each
  would want 500/s. Options, in order of preference: (1) **stagger the on-sales**, e.g. dates 1–10
  at 10:00, 11–20 at 11:00 (a product conversation, which the EM should start weeks before);
  (2) **split the budget**: each event's controller gets a share (`pspShareAuthPerSec`) and admits only
  as fast as its share allows; (3) add a **second PSP** for failover and headroom.
- **The global admission budget.** The sum of all events' R must fit the shared gateway and order
  fleets. A small coordinator gives each active event a ceiling, weighted by expected demand.
- **The fan.** The hardest one, and a product question. In a 20-date tour, a fan can join all 20
  queues to maximise their odds: 20 million queue entries, and unfair to fans who join one. Two
  policies: (a) **one active queue per account per tour**: the fan picks their preferred dates in a
  **cross-show lobby** and the draw considers them for those dates in order; (b) allow many queues
  but **cap tickets per account per tour**, enforced at the hold. (a) is fairer and cheaper; (b) is
  simpler to ship.

**And the quiet days.** Most of the time thousands of events are on sale with a trickle of traffic,
and a queue would only annoy people. The event directory's `queueEnabled` flag is **off** by
default: the gateway issues an admission token on page load and the fan goes straight to the map.
The waiting room switches **on** automatically when an event's arrival rate crosses a threshold
(say, 5× what its cell can serve), and always for events flagged as high-demand.

> "Everything is keyed by event, so events are independent; the problem is isolation, not
> coordination. Small events share a cell, a mega on-sale gets its own cell and its own Redis slot,
> placed the day before, because on-sales are scheduled. The shared things are the PSP throughput,
> which I'd budget per event and ideally avoid by staggering on-sales, and the fan, where 'one queue
> per tour' is a policy decision for the promoter."

\newpage


### The requirements as they arrive, worked

The requirement-drip format adds requirements as you go. The scoring is about **re-stating the delta**: what
changes, what doesn't, what it costs. Don't silently redraw.

| New requirement | Change | What stays untouched |
|-----------|---------------------------------|---------------|
| *"Promoter releases 5,000 more seats mid-sale"* (the cue-sheet curveball) | Insert rows as `AVAILABLE` in one transaction; bump the layout version (new CDN key); clear `soldOut`; let the controller resume | The claim path: new rows are claimable like any other |
| *"Add a waitlist when sold out"* | New consumer of `SeatsReleased`: offer the seats to the next waitlisted fan with a **targeted hold** and a notification | Inventory gets one nullable column; the queue is unchanged |
| *"Best available, not pick-a-seat"* | A server-side **allocator** chooses contiguous seats by section score; contention drops sharply because the server avoids collisions | Same claim SQL, a different source of seat ids |
| *"A celebrity tour: 20 shows, 10× traffic, bots"* | challenge 7: one queue per show, a cross-show lobby, dedicated cells, a PSP budget | The per-event architecture already shards cleanly |
| *"Multi-region"* | Edge, queue state and reads are global; **each event's inventory is homed in one region** (single writer) with a synchronous replica in a second zone | No multi-master writes on seats, ever |
| *"Dynamic pricing"* | Price lives on the seat or section, read at hold time and **locked into the hold** | The claim; the price the fan saw is the price they pay |

### Worked delta 1: the waitlist

![The waitlist as a new consumer: a released seat becomes a targeted hold for the next waitlisted fan, who gets a deep link with a one-off admission token.](diagrams/sd47-seq-waitlist.pdf){width=86%}

```sql
ALTER TABLE event_seat ADD COLUMN hold_for_user bigint;   -- null for ordinary holds
-- A targeted hold is an ordinary HELD row created by the waitlist service, with a 10-minute
-- expiry; the freeze step additionally checks hold_for_user = the ordering user.
```

> "The waitlist is a new consumer of SeatsReleased. It creates a targeted hold for the next fan who
> wants that many seats, and the notification carries a deep link with an admission token for that
> fan only. Inventory gets one nullable column; the queue and the claim path don't change."

::: why
**Why is this a good answer to score?** It shows the extension point from Chapter 5 was real: the
event stream was there "so the waitlist could subscribe later", and now it does. **The interviewer
is checking whether new requirements land as new consumers and read models, or as a redesign.**
:::

### Worked delta 3: the promoter releases 5,000 more seats

```sql
BEGIN;
INSERT INTO event_seat (event_id, seat_id, section, state)
SELECT :e, gs, :section, 'AVAILABLE' FROM generate_series(50000, 54999) AS gs;
INSERT INTO outbox (event_id, event_type, payload)
VALUES (:e, 'InventoryAdded', jsonb_build_object('from', 50000, 'to', 54999, 'layoutVersion', 4));
COMMIT;
```

Then: the snapshot builder grows the bitmap; clients see `layoutVersion` 4 in the next map response
and fetch `/layout?v=4` from the CDN (a new URL, so no purge); the controller clears `soldOut` and
`admissionPaused` and resumes moving the pointer.

\newpage


\newpage
## Challenge 8 · How would you know it is broken?

**How would you know it is broken?** *The observability challenge, and the one that is always last.*

| | |
|---|---|
| **The question** | "What is the SLO for the sale opening, and what is your plan for the day it fails?" |
| **The naive answer** | CPU, error rate and a dashboard. |
| **The case** | The dashboard is green while unknown payments pile up and two thousand seats sit frozen; the line has stopped moving. |
| **Where it breaks** | The whole baseline, silently. |
| **The fix** | SLIs tied to promises: hold p99 and the 409 ratio; admission rate against shop health; the **age of the oldest expired hold**; **seats frozen by unknown payments and their age**; queue-state staleness; map version lag; **tickets issued against seats sold (they must be equal)**. A **synthetic fan** every ten seconds through lobby, hold and release. A pre-event load test at 2× and a game day. A kill switch that stops admission, and a status page. |
| **Symptom pair** | Hold p99 *flat* and admitted fans *falling* points at the payment path, not inventory. |
| **Why it works** | Measure the promise, not the machine. |
| **If the fix fails** | The metrics say all is fine and fans are angry. |
| **Second fix** | The synthetic fan, and a support-contact signal as a metric of last resort. |

![Measure the promise.](diagrams/video-ch8-fix.pdf){width=85%}

::: {.key title="If asked, I would say"}
The SLI is a fan completing a purchase, probed continuously. I watch seats frozen by unknown payments and the age of the
oldest expired hold, because those are where this system fails silently. And there is a plan for degradation: shrink the
rate, pause admission, and say so.
:::

### Deep dive · the whole system under load: how it degrades

A good design doesn't only work at the planned load. It **fails gently** above it. The interviewer
may ask *"what if twice as many people show up?"* or *"what breaks first?"*

**What each layer does when overloaded** (each one sheds or slows before the next is hurt):

| Layer overloaded | What it does | What the fan sees |
|--------|---------------------------------|-------------------|
| CDN can't reach origin | `stale-if-error`: keeps serving the last queue state for 30 s | The line pauses |
| Waiting-room service at T0 | `queue/me` answers `503` with `Retry-After: 5`; clients retry with jitter | "Finding your place…" a few seconds longer |
| Gateway | Sheds requests **without** an admission token first; admitted traffic has priority | Waiting fans' polls slow; shoppers unaffected |
| Inventory DB | Controller sees hold p99 rise and **cuts R by 30%** every second until it recovers | The line moves slower; shoppers' clicks stay fast |
| PSP slow or failing | Circuit breaker opens; seats stay frozen; controller cuts R so new shoppers don't pile up holds | "Processing payment…" longer; fewer new admissions |
| Kafka lag | Map staleness grows; tickets emails are delayed | A 409 now and then; tickets arrive a minute late |

::: load
**Double the fans (2M instead of 1M).** The database doesn't notice: R is set by shop health, not by
demand. What doubles is the lobby (~200 MB of Redis), the T0 `queue/me` burst (~100,000/s: precompute
the ranks, challenges 4 and 5) and CDN polling (CDN capacity, not ours). Sell-out time doesn't change; the
sold-out message goes to 1.97M people instead of 970,000. **This is the strongest argument for the
design: demand is absorbed at the edge, and the core only ever sees what it chose to admit.**
:::

**Thundering herds, and the small things that prevent them:**

- **Jitter on every synchronised action.** `queue/me` after T0 (0–20 s), every poll (±20%), every
  client retry (exponential backoff with full jitter, below).
- **Admission in steady increments**, 33 a second, never 2,000 at once at the top of each minute.
- **Admission tokens expire at staggered times**, because fans were admitted at different seconds.
- **409 carries the fresh map**, so a lost click doesn't trigger an extra `GET`.
- **Static everything at the edge**: the app, the layout, the lobby page.

```javascript
// Client-side retry: exponential backoff with "full jitter" (a random wait up to the cap).
// Without jitter, every client that failed together retries together.
async function withRetry(fn, attempts = 5) {
  for (let i = 0; ; i++) {
    try {
      return await fn();
    } catch (e) {
      if (i + 1 >= attempts || !e.retryable) throw e;
      const cap = Math.min(8000, 250 * 2 ** i);   // 250 ms, 500 ms, 1 s, 2 s, 4 s ... 8 s
      await sleep(Math.random() * cap);
    }
  }
}
```

::: why
**What is a thundering herd?** Many clients doing the same thing at the same instant because
something synchronised them: a clock (T0), a shared failure (everyone's request failed at once, so
everyone retries at once) or a shared cache expiry. Each wave is far above the average load. **Jitter**
(a random delay) spreads the wave into a plateau with the same total but a much lower peak.
:::

\newpage

### Failure modes and reliability

| Failure | Blast radius | Mitigation |
|--------|-----------|-----------------------------------------|
| Inventory DB primary fails mid-sale | Holds and orders for **that event's cell** | Synchronous replica in another zone, automatic failover (~30 s). The **controller pauses R** on health signals, so the queue absorbs the outage instead of fans hammering errors |
| Redis queue node fails | Waiting positions for events on that node | AOF + replica; admitted fans unaffected (the JWT is stateless). Worst case, re-seed `next:{e}` from the highest seq seen in tokens |
| PSP outage or slowness | Checkout | Circuit breaker; `PAYMENT_PENDING` keeps seats safe; lower R so new shoppers don't pile up holds; status reconciliation after recovery; a second PSP as failover for big sales |
| Kafka lag | Map staleness, delayed ticket emails | Not a correctness issue; alert on lag; the outbox means nothing is lost |
| Hot section (the front rows) | Lock contention on a few rows | `NOWAIT` fails fast; the best-available allocator spreads requests |
| Bot surge | The queue is polluted | Challenge at the lobby, per-account and per-card limits, post-sale cancellation of flagged orders |
| Admission controller dies | The pointer stops moving | Leader lease expires in seconds, another instance takes over; the line pauses briefly, nothing breaks |
| Clock skew between servers | Holds expiring early or late | Every expiry is computed with the **database's** `now()`, never an application server's clock |

::: why
**Why "the queue absorbs the outage" is the key sentence.** In a design without a waiting room, a
30-second database failover during the peak means a million clients retrying against errors, and the
recovered database is flattened again the moment it comes back. With a waiting room, the controller
stops admitting; the waiting fans see the line pause; the 10,000 shoppers inside see a few errors
and retry with backoff; the database comes back to the load we choose to give it.

**Why the database's clock?** If three inventory pods compute `now() + 5 minutes` on their own
clocks and one is 20 seconds fast, its holds expire 20 seconds early, and a seat can be claimed while
its owner thinks they still have time. One clock, the database's, avoids the whole class of bugs.
:::

### SLOs, observability, operations

- **The invariant monitor (page immediately):** per event, no seat with two tickets, and the number of
  tickets equals the number of `SOLD` seats. **Oversell has an SLO of zero.**

```sql
-- runs every minute per active event; any row returned pages the on-call engineer
SELECT 'ticket count mismatch' AS problem, :e AS event_id
 WHERE (SELECT count(*) FROM ticket WHERE event_id = :e)          -- Order DB
    <> (SELECT count(*) FROM event_seat WHERE event_id = :e AND state = 'SOLD');  -- Inventory DB
-- (two databases: in practice two queries and a comparison in the monitor job)
```

- **SLOs:** queue join availability 99.95% during on-sales; hold API p99 < 300 ms; approved
  authorization to tickets issued p99 < 30 s; **no seat in `PAYMENT_PENDING` older than 15 minutes**;
  oversell = 0.
- **The on-sale dashboard:** admitted vs waiting, R, hold success vs 409 ratio, conversion, PSP
  latency and unknown-outcome count, Kafka lag, age of the oldest expired hold.
- **Before the biggest sale of the year:** a load test replaying **1M synthetic fans** with realistic
  think-times against a staging copy of the event; and a **game day**: kill the inventory primary,
  stop the sweeper, slow the PSP to 30 s, kill the admission controller's leader. The on-sale
  **runbook** names who may change R and who may pause the sale.

::: why
**Why an SLO on `PAYMENT_PENDING` age?** It's the one place seats can get stuck: a payment whose
outcome we never learned. Watching its age turns a silent leak into an alert. **Why "zero" for
oversell rather than 99.99%?** Because it's an invariant, not a latency. Any violation is an incident
with a refund, an angry fan at a gate, and possibly a news story.
:::


\newpage
# Chapter 8 · Build cost (AUX: the engineering-manager layer)

*This layer is optional in a Staff round and expected in a manager round. All figures are illustrative; replace them with
the team's own.*

| Version | Scope | People and time |
|---|---|---|
| **V1** | A sale with no waiting room: one primary per event, the conditional claim and holds, orders, one provider | **3 engineers, 2 months** |
| **V2** | The sweeper, the freeze and the reconciler, the outbox and the snapshot builder | **+2 engineers, 2 months** |
| **V3** | The waiting room, the admission controller, bot controls, the load test and game days | **+2 engineers, 3 months** |

**Buy against build.** The payment provider and the bot challenge are bought. The waiting room can be bought for the
first season and built when per-event cost or control justifies it. Inventory and orders are ours: they hold the
invariant.

**Top risks.** A payment-provider outage during a flagship sale (answer: a second provider). The first big on-sale
with no load test. A fairness rule decided late by the business.

## Phasing, team split and the asks

- **Phasing.** *MVP (6–8 weeks):* holds, checkout, the claim path, a simple FIFO queue, a polled seat
  map. *Then:* the lobby and lottery, bot defence, adaptive polling, SSE deltas, the waitlist, the
  best-available allocator, cells for mega events.
- **Team split along the three paths:** **Edge and Waiting Room** (queue, admission, bot defence),
  **Inventory and Orders** (the correctness core, owns the invariant), **Payments** (PSP adapters,
  reconciliation), plus a small **Fan Experience** team for the map and apps. The contracts between
  them are the event stream and the admission token, so they can work in parallel.
- **Cost driver:** CDN egress and the peak-only fleet. Scale ahead of known on-sales from the
  calendar, not reactively.
- **Half the time and half the team?** Ship the hold with a TTL, the atomic claim, authorize-then-
  capture and a basic FIFO queue. **Never cut the invariant monitor.**
- **Cross-team asks:** the promoter decides the fairness policy and the on-sale schedule; finance
  owns PSP contracts and throughput; support needs the residual-refund playbook.

::: why
**Why split teams along the paths?** Each path has different skills, scaling and on-call profile:
the edge team thinks in CDN rules and bot signals, the inventory team in transactions and
invariants, the payments team in PSP contracts and reconciliation. Clear contracts between them (an
event schema, a token format) let them ship independently. An EM answer names the seams and who owns
the invariant.
:::

# Chapter 9 · Recap

![The final baseline.](diagrams/video-base-final.pdf){width=100%}

| Path | In one sentence |
|---|---|
| **Join** | A lobby and a signed place in line; a cached answer identical for everyone |
| **Browse** | An immutable layout on the CDN and a versioned bitmap, one version a second |
| **Hold** | One conditional update, all or nothing; a `409` with a fresh map |
| **Pay** | Freeze, authorize, sell on approval; silence is *unknown*, not failure |
| **Expire** | The claim treats an expired hold as free; a sweeper makes the map catch up |
| **Release** | New rows and a new layout version; the waitlist is a consumer |

**Common mistakes in this round:** a database lock held through checkout · a sweeper as the only expiry · a timeout
treated as a decline · a live map read from the database · strict first-come at T0 · numbers with no decision attached ·
no number for what "fair" costs · no plan for the day it fails.

> *Fifty thousand seats, a million fans: the design is the distance between what arrives and what is admitted.*

## The four-sentence close

> "**What I built:** a waiting room that meters a million people into a few hundred transactions a
> second, a cached seat map, and a relational claim path with time-limited holds. **Key trade-off:** I
> chose correctness and graceful rejection over raw throughput, so seats are frozen during payment and
> the map can be a second stale. **Biggest risk:** the unknown payment outcome, watched by the
> PAYMENT_PENDING-age SLO and the oversell invariant. **Next:** bot defence and the best-available
> allocator, which reduce both fraud and contention."

::: why
**Why four sentences in this shape?** What / trade-off / risk / next is how senior people summarise
decisions. It shows you know what you built, what you gave up for it, what could still hurt, and
where you'd invest. Interviewers often write the debrief from your close.
:::

# Canon check

The points the standard treatments of this question make, each either covered or dismissed aloud.

| Canonical point | Where covered, or why dismissed |
|---|---|
| Three-state seat, atomic conditional claim | Chapter 3 mechanism 1; V2; challenge 1 |
| A hold with a TTL, not a lock through checkout | Mechanism 2; challenges 1 and 2 |
| A virtual waiting room admitting at a serviceable rate; the queue as a product | Chapter 2; challenge 4 |
| Sweeper plus lazy expiry | Challenge 2 |
| Hold expired, payment succeeded: take a position | Challenge 3 |
| Seat-map read path split; a stale click is acceptable and graceful | Challenge 6 |
| Fairness and bots; a lottery over strict first-come | Challenge 5 |
| Idempotent purchase | Chapter 4; challenge 3 |
| Adjacent seats ("best available") | Challenge 7 (an allocator) |
| A pre-event load test; an SLO for the opening | Challenge 8; Chapter 8 |
| A distributed lock per seat | **Dismissed** in the options matrix: a second system, and a lease can expire mid-transaction |
| Optimistic locking with a version column | In the options matrix; ends in a conditional update anyway |
| "Exactly-once" payment | Corrected in challenge 3: at-least-once with idempotent effects |
| Multi-region | Challenge 7: each event homed in one region, a single writer; no multi-master seats |

*What changed since older write-ups:* strict first-come at T0 is now widely seen as bot-friendly; verified-fan
registration and per-event lotteries are standard for flagship events.

\newpage

# Self-check after a simulator run

Score yourself honestly; the simulator's debrief uses similar dimensions.

| Signal | Weak | Strong | Exceptional (aim here) |
|-----|--------|----------|-------------------------------------|
| Framing | Starts drawing at minute 2 | Asks about oversell, hold, payment | Says **"98% will be rejected"** by minute 12 and designs for it |
| Estimation | Lists numbers | Numbers lead to decisions | Two or three numbers, each with a consequence; shows *why the queue exists* with the 33k-txn/s figure |
| Seat states | Available / sold | Adds HELD with TTL | Adds **PAYMENT_PENDING**; lazy + sweeper expiry |
| Contention | "Use a lock" | Conditional update, all-or-nothing | Sorted locks, `NOWAIT`, 409 with a fresh map, ticket `UNIQUE` |
| Queue | Rate limiter | Waiting room with admission | **CDN-cached pointer**, lottery at T0, adaptive polling, sold-out signal, a feedback-controlled R |
| Payments | Synchronous, assumes success | Idempotency key | **Authorize → sell → capture**, unknown is not failure, status + webhook + reconciliation |
| Many events | Not considered | "Shard by event" | Isolation by cell, PSP budget, one-queue-per-tour policy |
| Tool depth | Names tools | Justifies tools | Explains Postgres re-check semantics, Redis failover loss, CDN request collapsing |
| New requirements | Redraws | Adapts | **States the delta** and what stays untouched |
| EM layer | None | SLOs | Invariant monitor, game day, team split along paths, phasing |

**Common traps:** holding database row locks for the whole checkout; sweeper-only expiry; serving a
live seat map to everyone; Redis as the seat source of truth; treating a PSP timeout as a decline;
a per-user poll response that can't be cached; forgetting to tell the losers.

\newpage
# Part III — The internals, for when the interviewer digs

Requirement-drip rounds promise an in-depth tool probe. These appendices go one level below the technology choices,
in plain words. Read them once; reread the one for whichever tool you named in your last mock.

## Appendix A — PostgreSQL: row locks, Read Committed, replication

**MVCC in one paragraph.** PostgreSQL never overwrites a row in place. An `UPDATE` writes a **new
version** of the row and marks the old one as dead from that transaction on. Readers see the version
that was committed when their statement started, so **readers never block writers and writers never
block readers**. That's why 5,000 map reads a second *could* run alongside the holds, and why we
keep them off the database anyway: they still cost CPU and connections.

**Row locks.** A writer (`UPDATE`, `DELETE`, `SELECT … FOR UPDATE`) locks each row it touches until
its transaction ends. A second writer to the same row waits, fails at once with `NOWAIT`, or skips
the row with `SKIP LOCKED`.

**Read Committed and the re-check, as a timeline.** Seat 102 is `AVAILABLE`. Two transactions,
without `NOWAIT`:

| Time | Transaction A | Transaction B |
|-----|-------------------|------------------------------------|
| t1 | `UPDATE … SET state='HELD' WHERE seat=102 AND state='AVAILABLE'`: matches, locks the row | |
| t2 | | Same `UPDATE`: finds row 102, sees it locked by A, **waits** |
| t3 | `COMMIT`: row 102 is now `HELD` (new version) | |
| t4 | | Wakes up. PostgreSQL **re-reads the newest version** of row 102 and **re-evaluates the `WHERE`**: `state='AVAILABLE'` is now false. **0 rows updated** |
| t5 | | Sees 0 < 1 requested, `ROLLBACK`, answers 409 |

This re-check (internally "EvalPlanQual") is why the conditional update is safe at PostgreSQL's
default isolation level. You don't need `SERIALIZABLE`.

::: why
**Why not `SERIALIZABLE` anyway, to be safe?** It makes PostgreSQL detect *any* pattern of
reads and writes that couldn't happen in some serial order, and abort one transaction with a
serialization failure. Under heavy contention that means many aborts and retries for no extra
safety here: the conditional update already makes our one critical operation atomic. Use the
simplest isolation level that's correct, and say why it's correct.
:::

**Why a long transaction is deadly: the connection-pool arithmetic.** Each transaction holds one
database connection from `BEGIN` to `COMMIT`. A pool has, say, 200 connections. If a hold
transaction lasts 5 ms, 200 connections serve 200 ÷ 0.005 = **40,000 transactions a second**. If you
kept the transaction open while calling the PSP (10 s), the same pool would serve **20 a second**.
That's why the hold is *data with an expiry*, not an open transaction, and why payment happens
outside any inventory transaction.

**Synchronous replication.** The primary streams its write-ahead log (WAL) to a standby. With
`synchronous_commit = on` and a named synchronous standby, a `COMMIT` returns only after the standby
has written the WAL record. If the primary dies, the standby has every acknowledged commit and is
promoted (Patroni or a managed service does this in ~30 s). The cost is one network round trip per
commit, ~1 ms within a region, which our 500 writes/s barely notices.

**Partitioning vs sharding.** `PARTITION BY HASH (event_id)` splits one table into pieces *inside
one database*: smaller indexes, faster vacuum, easy archiving of past events. **Sharding** puts
different events in *different databases*. We use both: partitions for housekeeping, and the event
directory for placing events on shards and cells.

## Appendix B — Redis: why it's fast, what it can lose

**Single-threaded execution.** One Redis node executes commands one at a time on one thread. Every
command is atomic, with no locks, because nothing runs concurrently. It's fast because everything is
in memory and most commands are O(1) or O(log n): ~100,000+ simple operations a second per node.

**Lua scripts.** `EVAL` runs a script as one unit: no other command runs in between. That's how the
join script checks the phase and writes in one atomic step. Keep scripts short: while one runs, the
node serves nobody else.

**Data structures used here.** Strings (`INCR` counters, the pointer), **sorted sets** (the lobby:
members with a score, kept ordered; `ZADD`, `ZRANK` in O(log n)), hashes (`seqOf`).

**Redis Cluster and hash tags.** The key space is split into 16,384 **hash slots**, spread over the
nodes. A key's slot is `CRC16(key) mod 16384`. If the key contains `{…}`, only the part in braces is
hashed, so `lobby:{evt-7731}` and `next:{evt-7731}` land in the same slot and one script can touch
both. Multi-key scripts across slots aren't allowed, which is exactly why every event's keys share a
tag. Slots can be moved between nodes while running, which is how we give a mega event its own node.

**Persistence and what can be lost.** **RDB** snapshots the whole data set periodically; **AOF**
appends every write to a log. With `appendfsync everysec`, a crash loses up to ~1 second of writes.
**Replication is asynchronous**: a primary acknowledges a write before replicas have it, so a failover
can lose the last few hundred milliseconds. (`WAIT` can make a client wait for replicas, but it
doesn't make Redis a consensus system.)

::: why
**Why that's acceptable for the queue and not for seats.** If the queue loses one second, a few
hundred late arrivals might get a sequence number again, and the signed tokens still tell us who had
which number. Nobody pays twice, and nothing is sold twice. If a seat store lost one second, an
acknowledged hold could vanish and the seat be sold twice. Same tool, different consequence,
different decision.
:::

## Appendix C — Kafka and the outbox pattern

**The log.** A Kafka topic is an append-only log split into **partitions**. Each message gets an
**offset**, its position in the partition. Messages stay for a retention period (days), whether or
not anyone has read them. **Order is guaranteed only within a partition**, which is why we use
`event_id` as the message key: all of an event's messages go to one partition, in order.

**Consumers and groups.** Each consuming service is a **consumer group**. Kafka assigns each partition
to one member of the group, and the group stores its own **committed offset** per partition. The
snapshot builder and the notification service read the same topic independently, at their own pace.
A crashed consumer restarts from its last committed offset, so it may **re-read** a few messages:
that's **at-least-once** delivery, and consumers must be idempotent.

**Replication.** Each partition has a leader and followers on other brokers. With `acks=all` and
`min.insync.replicas=2`, a write is acknowledged only once two replicas have it, so losing one broker
loses nothing.

**Why the outbox: the dual-write failure, step by step.**

| Step | Dual write (wrong) | Outbox (right) |
|----|---------------------------|------------------------------|
| 1 | `COMMIT` the hold in PostgreSQL | `INSERT` the hold **and** an outbox row, then `COMMIT` (one transaction) |
| 2 | Service **crashes** before publishing | Service may crash: irrelevant |
| 3 | The `SeatsHeld` event is **lost forever**; the map shows the seat free until a full rebuild | The relay reads the outbox row from the WAL and publishes it, now or after a restart |

**The relay.** **Debezium** reads PostgreSQL's write-ahead log through logical replication and turns
each committed outbox insert into a Kafka message. It never sees uncommitted rows, and it remembers
its position in the log, so a restart resumes exactly where it stopped. A simpler alternative is a
**polling publisher** (`SELECT … FROM outbox WHERE published = false … FOR UPDATE SKIP LOCKED`, publish,
mark published): fine at our 500 rows/s, with a little more database load.

## Appendix F — Signed tokens (JWT) in plain words

A JWT is three base64 parts: `header.payload.signature`. The header names the algorithm, the
payload carries the claims (`sub`, `evt`, `exp`…), and the signature is computed over the first two
parts with a key. **Verification** recomputes or checks the signature and the expiry; if anyone
changed one byte of the payload, it fails. With an **asymmetric** algorithm (EdDSA, RS256), the
waiting room signs with a **private** key and gateways verify with the **public** key, so a gateway
can check tokens but never create them. A JWT can't be revoked by itself, which is why admission
tokens are short-lived (10 minutes) and carry a `jti` for an emergency deny-list.

\newpage

# One-page cheat card

**The insight:** a million fans, 50,000 seats, 2% succeed. Turn the stampede into a metered stream
and say "no" fast and fairly.

**Two numbers to compute:** (1) 50k ÷ 2.5 = 20k orders → **2%** win → a rejection system.
(2) 1M × 2 ÷ 60 s = **33k contended writes/s** without a queue → a waiting room → ~50 holds/s after
it. If there's time: (3) 1M ÷ 10 s = **100k polls/s** → identical answer, CDN-cached for 1 s.

**Three paths:** queue (huge, stateless, edge) · reads (large, may be stale, cached) · writes (small,
must be correct, PostgreSQL).

**Waiting room:** lobby + random draw at T0, FIFO after. Signed `seq` in the token. One cached JSON
`{admittedUpTo, rate, soldOut}`, position computed by the client. Controller moves the pointer at R
(AIMD on shop health). Admission JWT, 10 min, checked at the gateway.

**Claim:** sorted `FOR UPDATE NOWAIT`, conditional `UPDATE … WHERE state='AVAILABLE' OR expired`,
all-or-nothing, outbox row in the same transaction, 409 with a fresh bitmap. `UNIQUE(event, seat)` on
tickets.

**States:** AVAILABLE → HELD (5 min) → PAYMENT_PENDING (+10 min, never swept) → SOLD.

**Payment:** freeze → authorize → sell → capture. Timeout = UNKNOWN, not declined. Status query +
webhook + reconciliation. Void before capture; refund only in the residual case.

**Map:** immutable layout on the CDN; 6 KB bitmap, versioned by Kafka offset, at most 1 rebuild/s, 304s.

**Many events:** everything keyed by `event_id`; isolation by cell; Redis slot per event; PSP budget;
one queue per tour.

**EM layer:** invariant monitor (oversell = 0), PAYMENT_PENDING-age SLO, game day, teams along the
three paths, MVP = hold + claim + auth/capture + FIFO queue.

**Close:** what I built · key trade-off · biggest risk · next.

