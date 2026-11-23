# SD-47 · Ticket / seat booking under contention — reference-solution video outline

Target level: staff (manager layer AUX) · Target length: ≈ 80 min (≤ 90) · Word budget: ≈ 9,500–10,500 (≈ 0.49 s a word with pacing beats)

Rework of the 38-minute mock-round video (v2, 2026-10-29). Same facts and numbers as `../SD-47_Ticket_Booking_Reference_Design.md`; new shape.

## From the old version

| Reused | New | Dropped |
|---|---|---|
| Every number of the old estimate table (recomputed here) · the claim SQL, expiry SQL, freeze SQL, the order-service Java · the lottery, the admission loop (AIMD), the signed tokens, the two-stage sold-out signal · the bitmap and 304 path · the multi-event cells · eight sequence diagrams and two ERDs (redrawn on the shared kit) | Theory chapter (six parts, seven mechanisms, options matrix) · the carried baseline V1 → V2 → V3 · one numbered flow per functional requirement · eight challenges in the nine-beat grammar with "if asked, I'd say" · "what this question grades" · build cost chapter · canon check | The three-voice mock format (interviewer-led rounds of ten minutes) · the five follow-up slides as a separate section (they became challenge 7) · the 22 chapter structure |

## Thesis and definition

- **Thesis** (key-line voice): *This is not a booking system, it is a rejection system: fifty thousand seats cannot be shared with a million people, so the design converts a stampede into a stream, and every seat has exactly one place where its state lives and one atomic way to change it.*
- **Definition to say aloud**: *A ticket booking system sells a fixed set of individually identified seats to many more buyers than seats, with a time-limited hold between "free" and "sold", so that no seat is ever sold twice and no seat is ever stuck in limbo.* Every clause: **fixed set** (inventory never grows by accident), **individually identified** (contention is per seat), **many more buyers** (20 to 1 turns most requests into refusals), **time-limited hold** (a third state, data not a lock), **never twice / never stuck** (safety and liveness).
- **Hook**: A seat looks like a row with a boolean. The hard parts are everything around the boolean: a million people reaching it at the same second, a human who needs three minutes to pay, and a payment provider that sometimes does not answer.

## 0 · What this question grades

| Axis | Weak signal | Strong signal |
|---|---|---|
| Requirements | Starts drawing; never asks what "fair" means | Asks about oversell, specific seats, checkout time, fairness, payment behaviour, map freshness; cuts search, pricing, resale aloud |
| Correctness | "Check availability then insert a booking" | One atomic conditional claim; a third state; expiry that does not depend on a job; the payment-unknown state |
| Trade-offs | Names a product, a distributed lock | Options with the failure that rules each out; says what the pick gives up |
| Depth | "Queue in front" and stops | Admission rate from Little's law, a controller that reacts to shop health, why polling is cacheable, why the lottery is generated at join time |
| Operations | Watches CPU | Age of the oldest expired hold, seats frozen by unknown payments, admission rate against hold latency, a pre-event load test, a plan for the day it fails |

## 1 · Requirements and scope

- **Clarifying questions (six) and answers**:
  1. Can we ever oversell? Never. → atomic claim, one source of truth per seat.
  2. Specific seats or best available? Specific seats from a map. → contention is per seat, rows not a counter.
  3. How long does checkout take? About three minutes. → a hold with a time limit, data not a lock.
  4. What does fair mean, and who decided? Ask; first-come is expected, a queue or lottery is fine if argued. → a product decision I surface.
  5. How does payment behave? External, two to ten seconds, can time out ambiguously. → "unknown" is a real state.
  6. How fresh must the seat map be? Within a couple of seconds. → a cached, versioned read path.
  Scale given with the prompt: 50,000 seats, 1,000,000 fans arriving within 60 seconds.
- **FR1 Join** the sale (lobby, then a place in line). **FR2 Browse** a seat map. **FR3 Hold** specific seats for a limited time. **FR4 Pay** and get tickets. **FR5 Release and extend**: seats come back on expiry or failure; the promoter adds inventory.
- **NFRs, with numbers (all initial targets)**: zero oversell (invariant, not a rate); hold p99 < 300 ms; seat map stale by at most about 2 s; the sale-opening minute survives 1 M arrivals; seats never stuck in limbo (oldest expired hold < 30 s); a fan learns the outcome of a payment within a bounded time.
- **IN**: lobby and queue, seat map, holds, checkout with one external provider, tickets issued, expiry, promoter release, bot controls. **OUT (on purpose)**: event search and discovery, pricing and dynamic pricing, resale marketplace, refunds UI, the mobile app, fraud scoring models (named, not drawn).
- **"The core is four things"**: an atomic claim on a three-state seat, a hold with two expiry paths, a waiting room that sheds load at the edge, and a payment path that treats "unknown" as a state.

## 2 · Estimates

| Number | Arithmetic | Label | Decision it drives |
|---|---|---|---|
| Winners | 50,000 seats ÷ 2.5 per order = 20,000 orders; 20,000 ÷ 1,000,000 = **2 %** | derived | Mostly a rejection system; tell the 98 % early and cheaply |
| Without a queue | 1 M × 2 clicks ÷ 60 s = **33,333 / s** contended writes on 50,000 rows | illustrative | The waiting room exists |
| Joins | 1 M ÷ 60 s = 16.7 k / s; ×3 at the first seconds = **50 k / s**. Lobby open 30 min: 1 M ÷ 1,800 s = **556 / s** | illustrative | A join is one in-memory operation, never a database row; a lobby flattens T0 |
| Queue polling | 1 M ÷ 10 s = **100 k / s**. One cached answer, 1 s TTL, ~200 edge locations → **~200 / s** at the origin | illustrative | The answer is the same for every fan, so a CDN can hold it |
| Admission rate | Little's law: 10,000 shoppers ÷ 5 min = **2,000 / min ≈ 33 / s** | illustrative target | R is sized by checkout capacity, not demand |
| Time to sell out | 20,000 ÷ 0.7 conversion = 28.6 k admissions ÷ 2,000 / min = **≈ 14.3 min** | derived | An honest ETA; "likely sold out" early |
| Seat map | 10,000 shoppers ÷ 2 s = **5,000 reads / s**; 50,000 bits ÷ 8 = **6.25 KB**; 5,000 × 6.25 KB ≈ 31 MB/s; with 304s (~300 B) ≈ 1.5 MB/s | derived | Bitmap by version, 304 when unchanged, off the database |
| Holds | 33 / s × 1.5 attempts = **50 / s**; bursts ×10 = **500 / s** | illustrative | One primary per event is enough |
| Payments | 20,000 ÷ 900 s = 22 ≈ 25 / s; × 10 s = **250 in flight** (Little) | illustrative | Asynchronous checkout, bounded pool |
| Storage | 500 k events × 2 k seats × 120 B = 120 GB; 300 M orders × 1 KB = 300 GB; **≈ 420 GB a year** | illustrative | Not the problem; partition by event |

Headline: after the queue, the write path is a few hundred transactions a second. The scale is at the edge.

## 3 · Theory

1. **Is / is not.** Definition above. Not a lock (a lock is held by a process, a hold is data with an expiry). Not a shopping cart (a cart promises nothing). Not an auction (price does not move). Not a queue in the data-structure sense (the line is a product experience with a position and an estimated wait).
2. **Safety** (must never happen): **S1** one seat belongs to two orders. **S2** money is taken for seats we do not deliver, or seats delivered with no money. **Liveness** (must eventually happen): **L1** every seat is eventually sold or free again (no limbo). **L2** every fan eventually learns where they stand (position, sold out, order result). **L3** the sale-opening minute does not take the system down (admitted work finishes).
3. **Central tension**: demand is unbounded, supply and checkout capacity are not. *Fairness against load*: the fairest line (strict first-come) rewards bots and low latency and invites refresh storms; the cheapest line (random admission) needs a product decision. Picture: a funnel, 1 M → 10 k inside → 50 holds a second → 20 k orders.
4. **Mechanisms** (property → how → failure ruled out → cost):

   | # | Mechanism | Protects | Rules out | Costs |
   |---|---|---|---|---|
   | 1 | Conditional claim in one statement | S1 | read-then-write race | contended rows; losers get a 409 |
   | 2 | Hold as a row with an expiry (a third state) | L1, no lock across a human | a transaction open for minutes | a sweeper, a clock to trust |
   | 3 | Two expiry paths: lazy in the predicate, sweeper for the map | L1 | seats stuck forever; correctness depending on a job | staleness when the sweeper is down |
   | 4 | Admission control at the edge, adjusted by shop health | L3 | a stampede on 50,000 rows | most fans wait; a rate to tune |
   | 5 | Freeze, authorize then capture, "unknown" as a state, idempotency keys | S2 | double charge, sold twice after a late approval | seats frozen up to 10 min, a reconciler |
   | 6 | Split reads: immutable layout, versioned bitmap, cached queue state | L2, L3 | live map from the database | a click on a stale seat fails (graceful 409) |
   | 7 | Random admission among early arrivals; signed, short-lived tokens | fairness | bots winning at T0, forged positions | a product rule to explain |

5. **Options matrix** (seat reservation): rows (a) read then write · (b) database lock held through checkout · (c) a distributed lock per seat · (d) SERIALIZABLE transactions · (e) optimistic version column on each seat · (f) **one conditional update, hold as data (pick)**. Columns: atomic? · survives crashed server? · holds a connection through checkout? · fails when. (a) two readers see free; (b) connections held for minutes, falls over; (c) a lease expires mid-transaction and a second system to run; (d) correct but aborts most contended transactions; (e) works for one seat, multi-seat all-or-nothing still ends in a conditional update. **Pick (f). Gives up**: the hold can expire on a slow fan, hot seats are contended rows on one primary, and a sweeper must exist.
6. **Failure catalogue** (becomes the challenges): two fans on one seat · holds that outlive their owner · hold expires while payment is in flight · a stampede at T0 · bots and an unfair line · a stale map for ten thousand shoppers · requirements that arrive mid-sale · a failure nobody sees.

## 4 · API and entities

| API | Serves | Reads / writes | Wire-format notes |
|---|---|---|---|
| `POST /events/{id}/queue` | FR1 | writes Queue entry (Redis) | returns a signed queue token and server time |
| `GET /events/{id}/queue/state` (CDN, 1 s) | FR1 | reads Queue pointer | `{admittedUpTo, ratePerMin, soldOut}`; no user identity, same bytes for everyone |
| `POST /events/{id}/admit` | FR1 | writes Admission | exchanges a queue token for a 10-minute signed token |
| `GET /layout` · `GET /availability?v=` | FR2 | reads Layout · Availability bitmap | layout immutable; bitmap 6.25 KB, 304 when unchanged |
| `POST /events/{id}/holds` | FR3 | writes Seat · Hold | 201 `{holdId, expiresAt}` or 409 with a fresh bitmap; idempotency key |
| `POST /orders` · `GET /orders/{id}` | FR4 | writes Order · PaymentAttempt · Ticket | 202 accepted, then poll; idempotency key |
| `POST /psp/webhooks` | FR4 | writes Order | HMAC-signed; deduplicated by event id |
| Promoter `POST /events/{id}/inventory` | FR5 | writes Seat | adds rows as available in one transaction |

Entities (conceptual, Chen): Event has Seats; Seat is held by a Hold; a Hold becomes an Order; an Order has PaymentAttempts and issues Tickets; Fan joins a Queue. Physical: `event_seat` (event, seat, state, hold_id, expiry, order_id, version), `hold`, `outbox`, `orders`, `payment_attempt`, `ticket` with `UNIQUE (event_id, seat_id)`; Redis keys `phase`, `lobby`, `next`, `admittedUpTo`, `admitted:{user}` under one hash tag per event.

## 5 · High-level design

| Version | Adds | Objection it answers | Objection it leaves |
|---|---|---|---|
| V1 | One API and one database: a seat table with a status, check then update, direct to the database | (none: simplest thing that works) | Two fans on one seat; a hold cannot be expressed; a million requests land on the table |
| V2 | The third state and conditional claim with a hold expiry; a separate order service, payment provider, tickets; an outbox | "Two fans can both win; a lock held through checkout falls over" | A million fans on the same rows; a live map from the database |
| V3 | A waiting room in front (Redis, CDN-cached state, admission controller); a seat-map pipeline (Kafka, snapshot builder, Redis bitmap); a sweeper; a reconciler; signed tokens | "A million fans reach 50,000 rows; the map reads compete with the claims" | The details: payment races, bots, mid-sale changes, what we cannot see |

Baseline spine, left to right: Fans → CDN and gateway → Waiting room → Inventory (PostgreSQL) → Order service → Payment provider; Redis, Kafka and the snapshot builder above; sweeper and reconciler below.
Flows (numbered): FR1 join and admission · FR2 the seat map · FR3 hold · FR4 pay and ticket · FR5 expiry and release.
Then C4 context and containers, the inventory component view, and sequences for hold, checkout, seat map, admission.

## 6 · Bridge

"It works. Where does it break first?" Map: eight attack points on the baseline.

## 7 · Challenges (eight; the last is observability)

### Challenge 1 · Two fans, one seat
- Q: Two users click the same seat in the same millisecond. Walk me through it, mechanically.
- Naive answer: read the seat, if available write the hold.
- Case: seat 102, Fan A and Fan B both read AVAILABLE at 10:00:01.120; both write; both pay; two tickets for seat 102.
- Break: Inventory, the claim path.
- Fix: one conditional UPDATE (the WHERE is the check), rows locked in ascending order, NOWAIT, all or nothing; 409 with a fresh bitmap. Sequence + SQL.
- Why: S1 by atomicity; the loser's condition is false and it changes zero rows. Unique constraint on ticket as belt and braces.
- What if the fix fails: a bug elsewhere issues a second ticket, or the primary fails over mid-claim.
- Second fix: `UNIQUE (event_id, seat_id)` on ticket rejects the second insert; on failover, a synchronous replica, the claim is a transaction so an unacknowledged claim is not a hold.
- If asked: one conditional update, all or nothing, loser fails fast with a fresh map; unique constraint as the independent guard.

### Challenge 2 · The hold that outlives its owner
- Q: A fan holds two seats and closes the laptop. Your sweeper is down for ten minutes. What do users see?
- Naive: a cleanup job every minute releases expired holds.
- Case: 10:00:00 hold on 101, 102 (5 min); 10:05:00 expiry; the job runs 10:05:50; the map shows taken for 50 s; if the job is down, seats stay taken to everyone.
- Break: Inventory, expiry.
- Fix: lazy expiry inside the claim predicate (an expired hold is claimable at once) plus a sweeper every 5 s with SKIP LOCKED, batches of 500, announcing releases through the outbox.
- Why: L1; correctness never depends on the job, the job only makes the map catch up.
- What if: the sweeper releases a seat a buyer is paying for?
- Second fix: the predicate says state = HELD; a seat in PAYMENT_PENDING is never touched. Sweeper down: staleness, not oversell; alert on age of the oldest expired hold > 30 s.
- If asked: two expiry paths, each covering the other's gap.

### Challenge 3 · The hold expires, then the payment succeeds (crux)
- Q: The hold expires while the payment provider is still thinking, then the payment succeeds. What do you do?
- Naive: the hold expired, so release the seat; if the payment arrives later, refund.
- Case: 4:50 submit; 5:00 hold expires; 5:01 Fan C claims seat 101; 5:05 provider answers approved for Fan A. Two paid, one seat.
- Break: Order service to Inventory, the freeze.
- Fix, four parts: freeze (HELD → PAYMENT_PENDING, +10 min) before calling the provider; authorize first, capture after; timeout is UNKNOWN not failed, query by idempotency key plus webhook, first definite answer wins; the residual case refunds and apologises. Sequence + states + code.
- Why: S2; money is reserved before seats are sold, each step cheap to undo until the last.
- What if: the provider stays silent for an hour?
- Second fix: the reconciler with backoff, a freeze deadline, a cancel with the provider, then release; an explicit position with the product owner: slower sell-through at the end.
- If asked: "I would rather hold a seat ten extra minutes than sell it twice or charge for nothing."

### Challenge 4 · A million at the door
- Q: A million users hit your inventory database at once. What breaks?
- Naive: autoscale the database and the API fleet.
- Case: 33,333 writes/s on 50,000 rows; each waits on a row lock holding a connection; pool of a few hundred empties in milliseconds; timeouts, retries, retry storm.
- Break: gateway to inventory (the whole front).
- Fix: waiting room: lobby, a position, admission at a rate R chosen from shop capacity (Little's law: 2,000/min); polling answer identical for everyone and cached at the CDN; an admission controller adjusting R by health (AIMD) with slow start; a pointer advanced by one Lua script; admission token checked at the gateway.
- Why: L3; the core only sees what it chose to admit; demand is absorbed at the edge.
- What if: the controller dies, or the CDN cannot reach the origin?
- Second fix: one leader per event by lease; the pointer just pauses; `stale-if-error`; jitter on every synchronised action; double the fans changes the lobby size, not the database load.
- If asked: convert a stampede into a stream.

### Challenge 5 · A fair line, and the bots
- Q: What does fair mean, and how do you stop a bot holding all 50,000 seats?
- Naive: strict first-come-first-served from T0.
- Case: the order is decided in the first few hundred milliseconds; data-centre bots with 5 ms latency take the first thousands of places; everyone refreshes at 09:59:59.
- Break: waiting room join.
- Fix: a lottery among everyone present before T0 (random score drawn server-side at join, `ZADD NX`), late arrivals FIFO behind; signed queue tokens bound to account; one entry per verified account; purchase limits per account and card; challenge at lobby entry; pre-registered verified fans for flagship events. It is a product decision taken to the promoter.
- Why: fairness is the removal of an advantage speed gives; a random draw at join time costs nothing at T0.
- What if: an account farm passes verification?
- Second fix: limit per payment card and per device; cancel flagged orders after the sale and release to the waitlist; honest limit: no scheme is bot-proof, the aim is to make them expensive.
- If asked: a lottery for the lobby, first-come after, a product rule the page states.

### Challenge 6 · The seat map for ten thousand shoppers
- Q: Is a user allowed to see a seat as available and then fail to get it?
- Naive: each shopper reads the seat table every two seconds.
- Case: 10,000 ÷ 2 s = 5,000 reads a second against the same rows the claims lock; the claim p99 climbs.
- Break: Inventory used by both reads and writes.
- Fix: immutable layout on the CDN; availability as a bitmap built from the event stream (outbox → log-based relay → Kafka → snapshot builder → Redis), at most one version a second, served by version with 304; admitted fans only.
- Why: L2/L3; the claim is authoritative, the map is a hint; a stale click fails in milliseconds with a fresh map.
- What if: the stream stalls?
- Second fix: staleness grows, not incorrectness; a fan clicks and gets a 409 with the current bitmap; rebuild from a scan; the Kafka offset as the map version never goes backwards.
- If asked: the map may be a second or two stale because the write path decides.

### Challenge 7 · Requirements that arrive mid-sale
- Q: The promoter wants to release 5,000 more seats mid-sale. And then: add a waitlist, and a 20-date tour with ten times the traffic.
- Naive: redesign or restart the sale.
- Case: 45,000 sold, 5,000 rows to add under live contention; cached map and layout; a sold-out flag already shown to 970,000 people.
- Break: layout cache, soldOut flag, per-event limits.
- Fix: insert rows as AVAILABLE in one transaction, new layout version (new CDN key), clear soldOut, let the controller resume; the waitlist is a new consumer of seat-released events with a targeted hold; best available is an allocator that hands different fans different seats; the tour: everything keyed by event, cells for mega events, a PSP budget, one queue per account per tour.
- Why: the seams were there: the claim path is unchanged; new demand lands as consumers and read models.
- What if: two mega events share a Redis node or a PSP budget?
- Second fix: pin slots, dedicated cell the day before (on-sales are scheduled); stagger on-sales; split the PSP budget.
- If asked: say what changes, what does not, and what it costs.

### Challenge 8 · How would you know it is broken?
- Q: What is the SLO for the sale opening, and what is your plan for the day it fails?
- Naive: CPU, error rate and a dashboard.
- Case: a green dashboard while payment unknowns pile up and 2,000 seats sit frozen; the line stops moving.
- Break: whole baseline.
- Fix: SLIs tied to promises: hold p99 and 409 ratio, admission rate against shop health, age of the oldest expired hold, seats frozen by unknown payments and their age, queue state staleness, map version lag, tickets issued against seats sold (must be equal); a synthetic fan every ten seconds through lobby, hold and release; a pre-event load test at 2× and a game day; a kill switch that stops admission and a status page.
- Symptom pair: hold p99 flat and admitted fans falling → the payment path, not inventory.
- Why: measure the promise, not the machine.
- What if: the metric says all is fine and fans are angry? → the synthetic fan and a support-ticket signal.
- If asked: the SLI is a fan completing a purchase, probed continuously, with a plan for degradation: shrink R, pause admission, say so.

## 8 · Build cost (AUX)

V1 scope: waiting-room-less sale, one primary per event, conditional claim and holds, orders, one provider; **3 engineers, 2 months**. V2 adds the sweeper, the freeze and reconciler, the outbox and snapshot builder: **+2 engineers, 2 months**. V3 adds the waiting room, admission controller, bot controls, load test and game days: **+2 engineers, 3 months**. Buy against build: the payment provider and the bot/WAF challenge are bought; the waiting room can be bought for the first season (then build when per-event cost or control justifies); inventory and orders are ours. Top risks: payment provider outage on a flagship sale (second provider), the first big on-sale with no load test, a product rule on fairness decided late. All figures illustrative, to be replaced by the team's own.

## 9 · Recap

Final baseline; one bar per path (join, browse, hold, pay, expire, release) with one sentence; common mistakes in this round: lock through checkout; sweeper-only expiry; timeout treated as decline; live map from the database; strict FIFO at T0; no number on any estimate. Closing line: *fifty thousand seats, a million fans: the design is the distance between what arrives and what is admitted.*

## Canon check

| Canonical point | Source | Covered at (chapter) or dismissed because |
|---|---|---|
| Three-state seat, atomic conditional claim | cue sheet, booklet | Ch 3 mechanism 1, Ch 5 V2, Challenge 1 |
| Hold with TTL, not a lock through checkout | cue sheet | Ch 3 mechanism 2, Challenge 1–2 |
| Virtual waiting room admitting at a serviceable rate; the queue as a product | cue sheet, widely watched walkthroughs | Ch 2 estimates, Challenge 4 |
| Sweeper plus lazy expiry | cue sheet | Challenge 2 |
| Hold expired, payment succeeded: take a position | cue sheet | Challenge 3 |
| Seat map read path split; stale click acceptable and graceful | cue sheet | Challenge 6 |
| Fairness and bots; lottery over strict FIFO | cue sheet | Challenge 5 |
| Idempotent purchase | cue sheet | Ch 4 API, Challenge 3 |
| Adjacent seats (best available) | cue sheet, optional | Challenge 7 (allocator slide) |
| Pre-event load test and an SLO for the opening | cue sheet EM bar | Challenge 8, Ch 8 |
| Distributed lock per seat (Redis SETNX) | common walkthroughs | Dismissed aloud in the options matrix: a second system, lease can expire mid-transaction |
| Optimistic locking with a version column | common walkthroughs | In the options matrix; ends in a conditional update anyway |
| Exactly-once payment | common mistake | Corrected in Challenge 3: at-least-once with idempotent effects |
| Multi-region | common follow-up | Challenge 7: events homed in one region, single writer; no multi-master seats |

What changed since older write-ups: strict FIFO at T0 is now widely regarded as bot-friendly; verified-fan registration and per-event lotteries are standard for flagship events.

## Budget

| Chapter | Minutes | Words | Slides |
|---|---|---|---|
| 0 Cold open | 3 | 480 | 7 |
| 1 Requirements | 7 | 1,000 | 14 |
| 2 Estimates | 6 | 900 | 12 |
| 3 Theory | 9 | 1,250 | 17 |
| 4 API and entities | 6 | 800 | 12 |
| 5 High-level design | 11 | 1,300 | 22 |
| 6 Bridge | 1 | 120 | 2 |
| 7 Challenges (8) | 38 | 4,500 | 70 |
| 8 Build cost (AUX) | 3 | 350 | 5 |
| 9 Recap | 4 | 450 | 6 |
| **Total** | **≈ 88** | **≈ 11,000** | **≈ 167** |

If the generated total runs over 90 minutes, trim challenge 7 and the flows first.

## 5.1 Components and technologies (retrofit, 2026-11-22)

<!-- stack:outline -->

| Container | Choice | How it is built | Rejected | Theory part |
|---|---|---|---|---|
| Inventory DB | PostgreSQL 16, primary and synchronous standby, read committed | Each seat of each event is a row with a state | Read the seat, then update it; Redis for the hold; A distributed lock per seat | 03, 07 |
| Waiting room | Redis, a sorted set for the lobby, a pointer, Lua scripts for the atomic steps | A fan joins the lobby and receives a position | The relational database as the queue; Kafka as the queue; A third-party waiting room product | 05, 09 |
| Admission | A Go control loop, a signed token, a gateway that verifies without a database call | The admission controller watches the shop's load and turns the rate dial down or up | Rate limiting at the gateway only; A session lookup per request | 08 |
| Seat events | Outbox in the inventory transaction, Kafka partitioned by event | Each claim, release and sale writes an outbox row in the same transaction as the seat change | Publishing after the commit; Consumers reading the database | 06 |
| CDN | A CDN with a WAF, one-second lifetimes, request collapsing | The CDN caches the immutable venue layout for a long time and the queue state for a second | Serving everything from the origin; A long edge lifetime for seat state | 05 |
| Seat map | A Go service, an immutable layout object, a bitmap snapshot per event version in Redis | The venue layout is immutable and cached for ever | Querying the seat table per shopper; Pushing every seat change to every browser | 05 |
| Order service and the hold expirer | Go order service, an idempotent payment call, a hold expirer, a reconciler | The order service runs a saga: freeze the hold so it cannot expire mid-payment, call the payment provider with an idempotency key, then confirm the sale or release | A TTL on a Redis key as the hold; Releasing the hold the moment it expires | 07 |

Fix-slide rejections: 1: Read the seat, then update it; 2: Holding seats in Redis with a TTL; 3: Releasing the hold at the moment it expires; 4: Autoscaling the shop to a million at the door; 5: First-come at the gate; 6: Querying the seat table per shopper; 7: Rewriting booking to add a waitlist; 8: Alerting on server health.

<!-- /stack:outline -->
