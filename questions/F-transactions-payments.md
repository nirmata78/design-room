# Archetype F · Transactions, payments & commerce

**SD-44 – SD-50, plus the fintech expansion SD-77 – SD-82 and SD-93.** Slice with `grep -n '^### SD-44' questions/F-transactions-payments.md`, then Read
with `offset`. Do not read this file whole.

**What this archetype tests as a family:** **correctness under retry and partial failure.** Every
question here has a moment where a network call has an unknown outcome and money or inventory is at
stake. The recurring probe, and it applies to all seven: *"the call timed out. You don't know whether
it succeeded. What does your system do?"*

> **A note on calibration for a domain expert.** If `profile.md` says payments or commerce is the
> candidate's professional domain, **probe harder here than anywhere else in the bank, and do not be
> impressed by fluent vocabulary.** A 3 in this archetype is then a weak result; the bar is a 4 with
> mechanisms, numbers and an operational story. Also watch for the opposite failure: assuming the
> interviewer shares their domain context and under-explaining. **A domain expert who cannot make a
> non-expert follow them scores badly on Communication**, and that is a real risk in a loop where the
> interviewer will not be a payments person. If they use employer-internal vocabulary, ask them to
> define it — neutrally, once. Never let a real internal system name, figure or ticket ID into a
> session file (`CLAUDE.md` §12).

---

### SD-44 · Payment processing & double-entry ledger   [T1 · A★ G MS]

**Read aloud:** *"Design the system that takes a payment and records it — the ledger the company's money
is accounted for in."*

**Crux.** **Exactly-once does not exist across a network boundary**, so the design must be
**at-least-once delivery plus idempotent operations plus a reconciliation process that finds the
discrepancies anyway.** A candidate who claims exactly-once, or who has no reconciliation story
because they believe the system is correct by construction, has failed the core of the question.

**If they ask:**

| Question | Answer |
|---|---|
| Volume? | 10k payments/sec peak, 50 currencies |
| Latency? | Authorization decision within 2 seconds |
| External dependencies? | Card networks and banks — third parties that time out, return ambiguous results, and occasionally go down for hours |
| Consistency? | **The ledger must always balance. No exceptions.** Give this readily |
| Auditability? | Every balance must be explainable from immutable records, for 7 years |
| Refunds / partial refunds / chargebacks? | Yes, all three, arriving days or months later |
| Idempotency? | Clients retry. Ask them what they require of them |

**Listen for:**
- **Double-entry as the data model**: every movement is a pair of balanced entries; balances are
  *derived* from an immutable, append-only journal, never stored as a mutable authoritative number.
  Running balances may be cached but must be reconstructible. **This is the single most important
  listen-for on the sheet.**
- **Client-supplied idempotency keys**, stored with the *result*, so a retry returns the original
  outcome rather than re-executing — plus the retention window and what happens outside it, and the
  subtlety that the same key with a *different* payload must be rejected, not silently ignored.
- **The authorization/capture/settle lifecycle** modelled as an explicit state machine, with the
  states enumerated and the illegal transitions named.
- **The ambiguous-outcome case handled explicitly**: the request to the bank timed out. The design must
  neither assume failure (double-charging on retry) nor assume success (losing money), so it needs a
  **pending state plus a status-inquiry/reversal path** — this is the crux probe.
- **Sagas / compensating transactions** for the multi-step flow, with the honest note that compensation
  can itself fail and needs its own durability, and that a distributed two-phase commit across a bank
  is not available to you.
- **The outbox pattern** for publishing events about state changes without dual writes.
- **Reconciliation** against the external party's statement as a **designed, monitored daily process**
  with a break-investigation workflow — not a spreadsheet somebody maintains. **← The senior insight:
  reconciliation is not a safety net for a buggy system, it is a permanent, required component,
  because the counterparty's truth and yours will diverge no matter how correct your code is.**
- **Money representation**: integer minor units, never floating point; currency carried with every
  amount; exchange-rate versioning if they raise multi-currency.
- **Ordering and correctness of late events**: a chargeback arriving 90 days later must post correctly
  without mutating history — an adjusting entry, not an edit.
- **Isolation on the hot account**: a merchant's balance receiving 5,000 writes/sec, and why appending
  entries scales where updating a balance row does not.

**Probe ladder:**
- *Requirements:* "What must never happen, in priority order?" · "What are you willing to be slow
  about?"
- *Estimation:* "10k payments/sec, 7-year retention, several entries each — what's the ledger's size
  and write rate?" · "What's the hottest single account, and how many writes/sec does it take?"
- *Design:* the walk of one successful payment, naming every durable write in order · "What exactly is
  a row in your ledger, and what is immutable about it?"
- *Deep dives:* **"You call the bank. It times out. You do not know whether the customer was
  charged. Walk me through the next ten minutes and the next ten days."** (ask this every time — it
  is the whole question) · "The client retries the same payment three times with the same idempotency
  key, concurrently. What happens?" · "Same key, different amount. Then what?" · "Your service crashes
  between writing the ledger entry and publishing the event. What's the state?" · "A refund arrives
  for a payment that was already partially refunded twice. How does the ledger stay right?" · "The
  bank's statement says 999,998 and yours says 1,000,000. What now?"
- *EM bar:* "What's the SLI you'd publish, and what's the alert that fires before finance notices?" ·
  "What's your on-call runbook for 'payments are failing at 3 a.m.'?" · "How do you split this across
  three teams, given the ledger is the thing everyone touches?" · "What's the one-way door?" (the
  ledger schema and the idempotency contract — both effectively permanent)

**Curveball:** *"A bug double-posted 40,000 entries last night and some customers have already been
paid out."* Tests whether their immutable-journal model makes correction tractable (adjusting entries,
a replay from the source of truth, an audit trail of the correction) or whether they reach for
`UPDATE` — and whether they handle the customer/communication dimension, which is the EM half of the
answer.

**Weak / Strong / Exceptional.** *Weak* — a `balance` column updated in a transaction, retries assumed
safe, no idempotency keys, "we'd use a distributed transaction", no reconciliation. *Strong* —
double-entry immutable journal, idempotency keys with stored results, explicit lifecycle state machine,
pending/inquiry handling for ambiguous outcomes, sagas with compensation, outbox, daily reconciliation.
*Exceptional* — states the exactly-once impossibility precisely and designs around it, treats
reconciliation as a permanent component with a break workflow, handles the same-key-different-payload
and late-chargeback cases, sizes the hot account, and names the one-way doors.

**Traps.** "I'd use a distributed transaction across our database and the bank" — impossible; probe it.
Storing the balance as the source of truth. Assuming an HTTP timeout means the operation did not
happen. Using floats for money. Believing idempotency keys alone remove the need for reconciliation.


---

### SD-45 · Payment gateway integration, multi-PSP   [T2 · A MS]

**Read aloud:** *"Design the integration layer that lets our product take payments through several
different payment providers."*

**Crux.** **Every provider is a differently-shaped unreliable third party**, and the abstraction must
be thin enough to be honest. A canonical model that hides provider differences will leak, and the good
answer plans for that rather than pretending otherwise.

**Numbers if asked:** 5 providers, 3k transactions/sec, each provider has its own API shape, error
taxonomy, rate limits and 99.9% availability; provider outages last minutes to hours; webhooks arrive
out of order, duplicated, and sometimes not at all; some providers are region-specific.

**Listen for:** an **anti-corruption layer** — a canonical internal payment model with a per-provider
adapter translating both ways, including an **error taxonomy mapping** (retryable, terminal, ambiguous)
which is the part that actually matters and the part usually done badly · **routing** between providers
by cost, geography, card type and health, with **failover on provider outage** and the crucial caveat
that **you must not fail over an ambiguous transaction** — only a definitely-failed one · **webhooks
treated as untrusted, unordered and duplicated**: signature verification, idempotent handling, and
tolerance for out-of-order arrival by using state transitions rather than assuming sequence ·
**reconciliation against each provider's settlement file**, because webhooks are not a source of truth ·
**a state machine per transaction** that can be advanced by either an API response or a webhook, with
polling as the backstop when a webhook never arrives — **the polling backstop is the detail that
separates people who have run this from people who have designed it** · circuit breakers and per-provider
rate-limit budgets · a sandbox/test strategy, since you cannot integration-test against real money.

**Probes:** *"Provider A is down. You retry through B. Then A's webhook arrives saying the original
succeeded. What happens?"* · *"A webhook for 'captured' arrives before the one for 'authorized'. Does
your system cope?"* · *"A webhook never arrives at all. When and how do you find out?"* · *"Provider C
returns an error code your adapter has never seen. What does the system do — retry or fail?"* ·
*(EM bar)* *"You're adding a sixth provider. How long does that take, and what determines the
answer?"*

**Weak / Strong / Exceptional.** *Weak* — per-provider code branches in application logic, webhooks
trusted and processed in arrival order, retries on any error. *Strong* — adapter layer with canonical
model and error mapping, health-based routing with careful failover, idempotent order-independent
webhook handling, polling backstop, per-provider reconciliation. *Exceptional* — refuses to fail over
ambiguous transactions and says why, treats settlement files as the only truth, designs unknown-error
handling to be conservative, and quantifies the marginal cost of a new provider as a platform metric.


---

### SD-46 · Digital wallet & balance transfers   [T2 · A G]

**Read aloud:** *"Design a wallet — users hold a balance, send money to each other, and must never be
able to spend money they don't have."*

**Crux.** **A balance is a contended, serialised resource.** Two concurrent withdrawals must not both
succeed against the same funds, and the naive read-check-write is a real overdraft bug. The design is
about where serialisation happens and how it stays fast.

**Numbers if asked:** 100M wallets, 20k transfers/sec, hot merchant wallets take 5k writes/sec, balance
must be strictly non-negative, transfers between users must be atomic, holds/authorizations expire
after 7 days, full audit history required.

**Listen for:** **the overdraft race identified explicitly** and solved by an atomic conditional
operation, row-level locking, or a **single-writer-per-account partition** — with the throughput
consequence discussed · **append-only entries with a derived balance** (as in SD-44), and the tension
that a strict non-negative check needs the current balance, so either a maintained running balance
updated in the same transaction as the entry, or a per-account serialisation point · **transfers as
two-sided atomic operations**, and how that works when the two accounts are on different shards
(same-shard fast path, or a saga with a reserved/pending state and compensation) · **holds/reservations**
as a distinct concept from settled debits, with expiry and the reconciliation of expired holds ·
**hot-account handling**: sharding a merchant balance into sub-accounts that are summed, which is the
standard technique and a strong signal if they reach it · **idempotency** on transfer requests · the
audit trail and the ability to answer "why is my balance this number" · fraud/limits hooks as a
separate concern that must not be bypassable.

**Probes:** *"Two withdrawals for the full balance arrive at the same millisecond on different servers.
Walk me through why one fails."* · *"Sender and receiver are on different database shards. Is the
transfer atomic? Prove it."* · *"A merchant wallet takes 5,000 writes a second on one row. What
happens?"* · *"A hold expires but the capture arrives one second later. What's correct?"* · *(EM bar)*
*"A customer says their balance is wrong. What do you look at, and did you build it in advance?"*

**Weak / Strong / Exceptional.** *Weak* — `SELECT balance` then `UPDATE`, transfers as two independent
updates, no holds, no audit trail. *Strong* — atomic conditional debits, append-only journal with
derived balance, cross-shard transfers via saga with pending state, holds with expiry, idempotency.
*Exceptional* — splits hot accounts into summed sub-accounts, states the serialisation point and its
throughput ceiling, handles hold/capture races, and makes "explain this balance" a first-class product
feature.

---

### SD-47 · Ticket / seat booking under contention   [T1 · A★ G MS]

**Read aloud:** *"Design ticket booking for a stadium — fifty thousand seats, and a million people
trying to buy them the moment sales open."*

**Crux.** **20:1 demand-to-supply contention on a fixed, uniquely-identified inventory**, where
overselling is unacceptable and holding a seat during a 3-minute checkout is required. The **hold with
expiry** is the mechanism; the *fairness* and *load-shedding* questions are what separate an EM answer
from an engineer's answer.

**If they ask:**

| Question | Answer |
|---|---|
| Scale? | 50k seats; 1M users arriving within 60 seconds of sale opening |
| Overselling? | **Never acceptable.** Give this readily |
| Checkout time? | Users need ~3 minutes to enter payment details |
| Seat selection? | Users pick specific seats from a map — so seats are individually identified |
| Fairness? | **Ask them what fair means here.** If pushed: first-come-first-served is expected, but a queue or lottery is acceptable if they argue for it |
| Payment? | External provider, 2–10 seconds, can time out ambiguously |
| Seat map freshness? | Should reflect reality within a couple of seconds |

**Listen for:**
- **A hold/reservation with a TTL**, atomically claimed, expiring automatically — the seat is neither
  free nor sold during checkout, which is a **third state** most weak designs lack.
- **Atomic claim** via a conditional update on the seat row (state `available → held` with the holder's
  ID), and recognition that this must be a single atomic operation, not read-then-write.
- **A virtual waiting room / queue in front of the inventory system**, admitting users at a rate the
  inventory can serve. **← The senior insight: 1M users cannot be allowed to contend on 50k rows;
  the design's job is to convert a stampede into a stream**, and the queue is a product feature (a
  position and an estimated wait), not just a throttle.
- **Hold expiry handled correctly** — a background sweeper *plus* lazy expiry evaluated on read,
  because a sweeper alone leaves seats invisible for its interval and a lazy check alone never frees
  seats nobody looks at.
- **The payment-timeout case**: hold expired, payment succeeded. The design must decide — extend the
  hold pending payment resolution, or refund and apologise — and say which, and why.
- **Seat map read path separated from the write path**: a cached, slightly stale map served to a
  million browsers, with the honest admission that a user may click an already-taken seat, and that
  this is acceptable if the failure is fast and graceful.
- **Fairness** discussed explicitly, including bot mitigation, and that strict FIFO is expensive while
  a randomised queue admission is often fairer in practice.
- **Idempotency** so a double-clicked buy doesn't buy two.
- Adjacent-seat allocation as a harder variant if they want to volunteer it.

**Probe ladder:**
- *Requirements:* "What does fair mean, and who decided?" · "Is a user allowed to see a seat as
  available and then fail to get it?"
- *Estimation:* "1M users in 60 seconds — what's the QPS on your seat map, and on your inventory
  writes?" · "How many of those million can possibly succeed?" (50k — a number worth saying out loud,
  because it reframes the design as *mostly* a rejection system)
- *Design:* the walk from "sale opens" to "ticket issued" · "What are the exact states of a seat?"
- *Deep dives:* **"Two users click the same seat in the same millisecond. Walk me through it,
  mechanically."** · **"The hold expires while the payment provider is still thinking, then the
  payment succeeds. What do you do?"** (the best probe here — there is no clean answer, and watching
  them choose and justify is the signal) · "A million users hit your inventory database at once. What
  breaks?" · "Your hold-expiry sweeper is down for 10 minutes. What do users see?" · "How do you stop
  a bot holding all 50,000 seats?"
- *EM bar:* "What's the SLO for the sale opening, and what's your plan for the day it fails?" ·
  "What's the load test you'd run before the biggest event of the year?" · "Half the time and half the
  team — what ships?"

**Curveball:** *"The promoter wants to release 5,000 more seats mid-sale."* Tests whether inventory
addition is safe under live contention, and whether cached seat maps and the waiting room cope.

**Drips** (format `drip`, §7.5 — read the prompt above as increment #1): **#2** *"Add a waitlist for when it sells out."* · **#3** *"A celebrity tour: ten times the traffic, and bots."* Listen for the delta stated out loud and the seam that absorbs it.

**Weak / Strong / Exceptional.** *Weak* — check availability then insert a booking, no hold state, no
queue, seat map queried live by a million clients. *Strong* — three-state seats with atomic
conditional claim, TTL holds with sweeper *and* lazy expiry, waiting room admitting at a serviceable
rate, cached seat map with graceful failure, idempotent purchase. *Exceptional* — reframes the problem
as load-shedding at 20:1 contention, makes the queue a product experience, takes an explicit position
on the expired-hold-successful-payment case, plans bot mitigation, and specifies the pre-event load
test.

**Traps.** Locking seats in the database for the duration of checkout (holds connections for minutes,
falls over). Relying only on a periodic sweeper for expiry. Assuming the payment provider is fast and
deterministic. Serving a live seat map to a million clients.

---

### SD-48 · Inventory & order management at scale   [T1 · A★]

**Read aloud:** *"Design inventory and order management for a large e-commerce site — customers must not
be able to buy something that isn't there, and we must not refuse a sale we could have made."*

**Crux.** **Available-to-promise is a computed, distributed quantity, not a number in a row.** Physical
stock sits in many warehouses; some is reserved, some is in transit, some is damaged. The design is
about where the authoritative reservation happens and how much oversell risk the business will accept
to keep the site fast — which is a **business** decision they should surface rather than resolve
silently.

**If they ask:**

| Question | Answer |
|---|---|
| Scale? | 100M SKUs, 50 warehouses, 10k orders/sec at peak, 100× that in product-page views |
| Oversell? | **"Some is tolerable if it's rare and you can recover. You tell me how much and why."** — this is the question |
| Multi-warehouse? | Yes, and shipping cost/speed depends on which one fulfils |
| Order lifecycle? | Placed → payment → allocated → picked → shipped → delivered, with cancellations and returns at most stages |
| Flash sales? | Yes — a single SKU can take 50k orders/minute |
| Physical reality? | Counts drift: damage, theft, mis-picks. **Give this if they ask — it is a strong question to ask** |

**Listen for:**
- **Separation of the read path (is it available?) from the write path (reserve it)**: product pages
  read a cached, slightly stale availability signal; only checkout attempts a real reservation. The
  100:1 ratio makes this mandatory.
- **Reservation as an atomic decrement of available-to-promise**, with a conditional update and a
  compensating release on cancellation or payment failure.
- **Available-to-promise as a derived quantity**: on-hand minus reserved minus safety buffer, per
  location — and the **safety buffer as the explicit oversell-risk dial**, which is the most useful
  single concept in this design.
- **Deliberate oversell tolerance stated as a business trade-off** — a stricter system refuses valid
  sales and costs revenue; the correct answer names both costs and asks who decides. **← The senior
  insight: this is a business calibration, not a technical absolute, and the EM's job is to surface
  the dial rather than pick silently.**
- **Hot SKU handling** in a flash sale: partition the SKU's inventory into buckets across shards so
  writes distribute, with a rebalance or fall-through when a bucket empties.
- **Order state machine, durable and event-sourced**, so every transition is auditable and resumable,
  with sagas across payment, allocation and fulfilment plus compensation for each.
- **Allocation as a separate decision from reservation** — which warehouse fulfils can be decided
  after the order, optimising cost and speed, and that decoupling is a real design insight.
- **Reconciliation with physical reality**: cycle counts adjusting on-hand, and the fact that the
  system must handle "we sold it but it isn't on the shelf" as a normal path, not an exception.
- **Idempotency** on order submission, and exactly-once *effects* handled by keys rather than claimed.
- Cancellation and return flows putting stock back, with the timing subtleties.

**Probe ladder:**
- *Requirements:* "How much overselling is acceptable, and who gets to decide?" · "What's out of
  scope?"
- *Estimation:* "1M product views/sec against 10k orders/sec — what does that say about where the
  authoritative check lives?" · "One SKU, 50k orders a minute. What's the write rate on that row?"
- *Design:* the walk of one order from add-to-cart to shipped, naming each durable transition ·
  "What's the exact quantity a customer sees on the product page, and how stale is it?"
- *Deep dives:* **"Flash sale: 50,000 orders a minute for one SKU with 1,000 units. Walk me
  through it."** · "Payment fails 30 seconds after you reserved. What releases the stock, and what if
  that release fails?" · "The warehouse picks the item and it's damaged. The customer has paid. What
  does your system do?" · "Two warehouses could fulfil, one is cheaper and slower. Where is that
  decided and when?" · "Your inventory service is down. Do you keep selling?" (a genuine business
  judgment call — fishing for a deliberate degraded mode)
- *EM bar:* "What's the metric that tells you the oversell buffer is set wrong in either direction?" ·
  "What do you tell the VP who asks why we refused 4,000 orders for items we had?" · "Split this
  across teams — where's the seam between orders, inventory and fulfilment?"

**Curveball:** *"Third-party sellers now hold their own stock and report counts to us hourly."* Tests
whether their availability model can absorb a source of truth they do not control and cannot trust, and
whether they raise a per-seller buffer.

**Weak / Strong / Exceptional.** *Weak* — a `quantity` column decremented at checkout, product pages
reading it live, one warehouse assumed, no compensation paths. *Strong* — cached availability read path
with authoritative reservation at checkout, ATP computed per location with a safety buffer, hot-SKU
partitioning, event-sourced order state machine with sagas, physical reconciliation.
*Exceptional* — frames the oversell buffer as a business dial with the cost of both errors quantified,
decouples allocation from reservation, handles the untrustworthy-physical-count path as normal, defines
degraded-mode selling, and names the team seams.

**Traps.** Treating oversell as absolutely forbidden without pricing the refused sales (the classic
over-correct answer). Serving live inventory reads to the product page. Ignoring that physical counts
are wrong regardless of software correctness.

---

### SD-49 · Delivery dispatch & order lifecycle   [T2 · U★ A]

**Read aloud:** *"Design food-delivery order dispatch — from order placed, through a courier being
assigned, to delivered, with live tracking."*

**Crux.** **A long-lived, multi-party state machine with real-world actors who fail unpredictably.** The
restaurant is slow, the courier cancels, the customer isn't home. The design's quality is measured by
how many of those it handles as designed paths rather than exceptions.

**Numbers if asked:** 1M orders/day with a sharp 2-hour dinner peak, 100k active couriers, assignment
within 60 seconds of the order being accepted, location updates every 5 seconds during delivery,
tracking must be visible to customer and restaurant, cancellations possible at most stages.

**Listen for:** an **explicit durable state machine** per order with every state enumerated and each
transition triggered by an event, including all the failure transitions (restaurant rejects, courier
cancels, courier unreachable, customer absent) · **assignment as a matching problem with a claim step**
(shares SD-39's contention structure — a courier must not be assigned twice) plus a **timeout and
reassignment** loop, and the batching insight that waiting 30 seconds to assign in batches beats greedy
nearest · **prep-time prediction** driving *when* to dispatch, because assigning too early wastes
courier time and too late makes food cold — a nice example of a prediction inside a systems design ·
**live tracking** reusing the ephemeral-location pattern (never durably storing every ping) with a
push channel to the customer · **multi-party notification** on every transition, and the observation
that notification volume is several times order volume · **compensation and money**: refunds, courier
pay for cancelled trips, and who bears the cost — the business logic that makes this hard ·
**peak load** being 10× the daily average and lasting two hours, which drives capacity and degraded
modes.

**Probes:** *"The courier accepts, then goes offline for 20 minutes. What happens to the order?"* ·
*"Two dispatchers assign the same courier to two orders. How is that prevented?"* · *"The restaurant
takes 40 minutes instead of 15. What does your system do differently?"* · *"Dinner peak is 10× —
what's your degraded mode?"* · *(EM bar)* *"What's the SLI customers actually feel, and how does it
differ from the one your services report?"*

**Weak / Strong / Exceptional.** *Weak* — status column updated by each service, nearest-courier
assignment with no claim or timeout, all locations persisted. *Strong* — durable event-driven state
machine with failure transitions, atomic courier claim with reassignment timeouts, ephemeral location
tracking, multi-party notifications. *Exceptional* — batches assignment for efficiency, uses prep-time
prediction to time dispatch, designs the peak degraded mode explicitly, and handles the money
consequences of each failure path.

---

### SD-50 · Subscription billing & usage metering   [T2 · A MS G]

**Read aloud:** *"Design usage-based billing for a cloud product — meter what customers use and invoice
them accurately."*

**Crux.** **The meter must be accurate enough to defend in a dispute and cheap enough to run**, and
invoicing must be **idempotent across retries** because sending a duplicate invoice or double-charging
is a customer-trust event, not a bug.

**Numbers if asked:** 100k customers, 50 metered dimensions, 500k usage events/sec, monthly invoicing
with mid-cycle plan changes, usage events can arrive hours late from some regions, invoices must be
reproducible and auditable for 7 years, customers dispute bills and expect a line-item breakdown.

**Listen for:** **raw usage events retained immutably** as the source of truth, with aggregates derived
and recomputable — so a rating bug is a re-run, not a data-loss event · **event-time aggregation with a
late-arrival policy**: a cutoff after which late usage moves to the next period, stated explicitly
because otherwise closed invoices change · **idempotent metering** (dedup by event ID) since agents
retry · **rating separated from metering** — quantity measurement is one concern, price application
another, and **rate cards must be versioned** so a historical invoice can be reproduced exactly (the
detail that makes 7-year auditability real) · **proration** on mid-cycle plan changes, which is where
most of the actual bugs live · **invoice generation as an idempotent, resumable workflow** with a single
finalisation transition; once finalised, corrections are credit notes, never edits · **customer-visible
usage during the period**, which needs a fast approximate path alongside the exact batch one — and the
requirement that the approximate number never *exceeds* the final bill, because under-promising is
tolerable and over-promising is not · **spend caps and alerts** as a product feature that needs
near-real-time metering to be useful · reconciliation between metered usage and the resource system's
own view.

**Probes:** *"Usage events for last month arrive after you've invoiced. What happens?"* · *"You need
to reproduce a bill from 18 months ago, exactly. What did you have to store?"* · *"The invoice job
crashes halfway through 100,000 customers. What does it do on restart?"* · *"A customer upgrades on
day 12 of the month. Walk me through the arithmetic and where it's implemented."* · *(EM bar)* *"A
customer disputes a $40,000 bill. What can you show them, and how long does it take?"*

**Weak / Strong / Exceptional.** *Weak* — counters incremented per usage event, prices read from
current config at invoice time, invoicing as a script, corrections by editing rows. *Strong* —
immutable events with derived aggregates, event-time windows with a late cutoff, dedup, versioned rate
cards, resumable idempotent invoicing, credit notes for corrections. *Exceptional* — makes every
invoice reproducible from immutable inputs including rate-card versions, guarantees the in-period
estimate never exceeds the final bill, supports spend caps off the real-time path, and designs the
dispute-resolution view as a product surface.

---

## Fintech expansion — SD-77 – SD-82

*Added for fintech-targeted loops (payment companies, neobanks, lenders, card issuers). Same family
test as SD-44–50 — correctness under retry and partial failure — with the regulatory and
counterparty constraints that make fintech different from generic commerce: **you are not the only
ledger**, and an external party's file is often the final word.*

---

### SD-77 · Card authorisation & issuer processing   [T1 · FT★ A MS]

**Read aloud:** *"You're building a card issuer — a company that issues debit cards to its customers.
Design the system that receives authorisation requests from the card network and approves or declines
them."*

**Crux.** **A hard real-time decision with a contractual deadline, followed by a long, messy
reconciliation.** The network gives the issuer a couple of seconds to answer; miss it and the network
decides for you (stand-in). Approval places a **hold**, not a debit — the real money moves days later
in **clearing files** whose amounts can differ from the authorisation (tips, currency conversion,
partial shipments). The design is the **authorisation path** plus the **auth ↔ clearing matching**.

**If they ask:**

| Question | Answer |
|---|---|
| Scale? | 8M cards, 1,500 authorisations/sec peak, 4,000 on Black Friday |
| Deadline? | The network times out after ~2 seconds; target internal p99 under 300 ms |
| Decision inputs? | Balance, card status, limits, fraud score, merchant category rules, 3-D Secure results |
| Message types? | Authorisation, incremental auth, reversal, advice (stand-in notifications), refunds |
| Settlement? | Daily clearing files from the network; amounts may differ from auth; some auths never clear |
| Availability? | Each declined good transaction is a customer at a till; downtime triggers network stand-in |

**Listen for:**
- **Available balance = ledger balance − active holds**, with holds as first-class ledger entries
  that expire (e.g. 7–30 days) if never cleared.
- **Idempotency on network identifiers** — the network retries, and reversals can arrive before the
  original (out-of-order).
- **A tight critical path**: in-memory/low-latency balance and limit check, fraud scoring within a
  budget with a **fail-open/fail-closed policy per risk class**, everything else async.
- **Stand-in** handling: when the issuer is down the network approves under configured limits and later
  sends advices — **← the senior insight: the issuer's ledger must absorb decisions it did not make,
  so "balance can never go negative" is false by construction; the design needs overdraft handling.**
- **Clearing/matching**: match clearing records to authorisations (by network reference, with fuzzy
  fallback), release or adjust holds, post final debits, handle unmatched both ways.
- **Hot account contention** is mostly absent here (per-card), but **per-cardholder serialisation** of
  concurrent auths on one balance is required.
- **Audit and dispute support**: every decision and its inputs recorded.

**Probe ladder:**
- *Requirements:* "What's the deadline and what happens if you miss it?" · "What's out of scope?"
  (card manufacturing, the network itself)
- *Estimation:* "1,500 auths/sec at a 300 ms budget — how much concurrency, and what's your per-call
  budget for fraud scoring?"
- *Design:* walk a $60 restaurant auth that clears three days later at $72 with tip.
- *Deep dives:* **"Your fraud service is at 1.8 s p99 tonight. What does the authorisation path do?"** ·
  "A reversal arrives before the authorisation it reverses. What happens?" · "You were down for 20
  minutes; the network approved 9,000 transactions in stand-in. Walk me through the next morning." ·
  "A hold was never cleared after 30 days. What does the customer see?"
- *EM/Staff bar:* "What's on the on-call runbook for 'auth decline rate doubled in 10 minutes'?" ·
  "Who decides the fail-open policy for fraud — engineering, risk or finance?"

**Curveball:** *"The card network sends the clearing file six hours late and with 3% of records
duplicated."* Tests idempotent ingestion of external files and resilience of the posting schedule.

**Weak / Strong / Exceptional.** *Weak* — synchronous debit of the balance on auth, no holds, no
stand-in thinking. *Strong* — holds model, available-balance arithmetic, idempotent out-of-order
message handling, budgeted fraud with explicit fail policy, clearing matching with adjustments.
*Exceptional* — designs the ledger to absorb stand-in and over-clearing (negative balances as a modelled
state), treats the clearing file as the financial source of truth, and quantifies the cost of each
fail-open decision.

**Traps.** Debiting at authorisation. Assuming one auth = one clearing record. Ignoring stand-in.

---

### SD-78 · KYC / AML onboarding & sanctions screening   [T2 · FT★ MS]

**Read aloud:** *"Design customer onboarding for a regulated financial app: identity verification,
anti-money-laundering checks, sanctions screening — and keep screening customers after they join."*

**Crux.** **A long-running, partially manual, audited workflow with external vendors**, where the
regulator cares less about the average case than about proving every decision. Screening is not a
one-off: **sanctions lists change daily and every existing customer must be re-screened.**

**Numbers if asked:** 20k sign-ups/day, three identity-verification vendors with different coverage by
country, ~8% of applicants need manual review, sanctions lists updated several times a day, 5M
existing customers, fuzzy name matching produces many false positives, and regulators require
retaining evidence for 5+ years.

**Listen for:** **workflow engine / state machine** per application (submitted → document check →
liveness → screening → risk score → approved / manual review / rejected), durable and resumable across
vendor calls taking seconds to days · **vendor abstraction with routing by country and fallback** ·
**risk-based approach**: tiered checks and limits by risk score · **sanctions screening as fuzzy
matching** with tunable thresholds, transliteration, and a **case-management queue** for analysts ·
**continuous screening**: a list update triggers re-screening of all customers incrementally (match the
delta against the customer base, not the base against the full list) · **immutable audit evidence** of
each decision with the inputs and list versions used · **PII protection** — encryption, access logging,
data minimisation, retention schedules.

**Probes:** *"The sanctions list adds 300 names at 4 p.m. How long until every affected customer is
frozen?"* · *"A vendor is down for one country. What do applicants see?"* · *"An analyst cleared a
false positive last month; the same customer matches again today. What happens?"* · *"A regulator asks
why customer X was approved in 2023. Show me."* · *(EM bar)* *"Manual review backlog is 4 days and
growth wants instant onboarding. How do you negotiate that?"*

**Weak / Strong / Exceptional.** *Weak* — synchronous vendor calls in the sign-up request, one-time
screening. *Strong* — durable workflow, vendor routing, risk tiers, fuzzy screening with case
management, continuous delta re-screening, immutable evidence. *Exceptional* — treats audit evidence as
a product, remembers analyst dispositions to suppress repeat false positives safely, and quantifies the
re-screening time against regulatory expectations.

---

### SD-79 · Reconciliation & settlement engine   [T1 · FT★ A MS]

**Read aloud:** *"We process payments through several banks and payment processors. Every day they send
us files saying what they think happened. Design the system that reconciles their view with ours and
settles the money."*

**Crux.** **Matching imperfect records from systems you don't control, at volume, and turning every
difference into an owned, explained exception.** The internal ledger is your truth for intent; the
bank's statement is the truth for money. Reconciliation is where those meet, and its outputs —
**breaks** — are the most important operational signal in a payments company.

**If they ask:**

| Question | Answer |
|---|---|
| Volume? | 15M transactions/day across 6 processors and 4 banks |
| Formats? | CSV, fixed-width, ISO 20022 XML, and one processor's API; formats change without notice |
| Timing? | Files arrive T+0 to T+3, sometimes late, sometimes resent with corrections |
| Matching? | No common key across all sources; processor references, amounts, dates, sometimes only descriptions |
| Differences? | Fees netted from settlements, FX conversions, chargebacks, partial refunds, rounding |
| Users? | Finance ops team of 25 resolves exceptions; auditors review monthly |

**Listen for:**
- **Ingestion as immutable raw files** with checksums and versioning; parsing into a canonical schema
  per source, with schema-change detection that **fails loudly**.
- **Multi-pass matching**: exact on strong keys first, then rule-based (amount + date window +
  reference fragments), then many-to-one / one-to-many (a settlement batch vs many transactions),
  with confidence scores.
- **Expected vs actual**: the ledger generates *expectations* (we expect processor X to pay us Y on
  day Z, net of fees) — **← the senior insight: reconciliation works when the ledger predicts external
  records, so a break is "expectation unmet", not "two lists that don't line up".**
- **Exceptions as a workflow**: categorised (timing, fee, missing, duplicate, amount mismatch), aged,
  owned, with SLAs and write-off approvals; auto-resolution of timing breaks when the late record
  arrives.
- **Idempotent re-runs** when a corrected file supersedes an earlier one.
- **Settlement**: computing net positions per counterparty and generating payment instructions, under
  maker-checker approval.
- **Reporting**: unreconciled balance by age as the key metric; audit trail of every match and manual
  action.

**Probe ladder:**
- *Requirements:* "What's the output — a report, a ledger adjustment, or a workflow?" · "Who are the
  users?"
- *Estimation:* "15M records/day against 15M ledger entries — what's the matching cost if you're naive,
  and how do you avoid it?" (partition by date, account and processor — never a cross product)
- *Design:* walk one processor's settlement file from arrival to matched/unmatched.
- *Deep dives:* **"Processor B resends yesterday's file with 4% of rows changed. What happens to
  matches already made?"** · "A $1.2M settlement is $3,400 short. How does your system explain it?"
  (fees, FX, chargebacks — expected vs actual) · "A file format changes silently and parsing 'succeeds'
  with amounts in the wrong column. Who notices?" · "Breaks older than 30 days are growing 10% a
  month. What do you do?"
- *EM/Staff bar:* "The finance-ops team is 25 people resolving breaks by hand. What's your plan for
  that number?" · "Auditors want proof nobody can change a match without approval. Show me."

**Curveball:** *"One bank moves to a real-time payment rail; you now get individual credit
notifications in seconds instead of a daily file."* Tests whether the design is file-batch-shaped or
event-shaped underneath.

**Weak / Strong / Exceptional.** *Weak* — nightly SQL join on amount and date, mismatches emailed as a
spreadsheet. *Strong* — immutable raw ingestion, canonical schema, multi-pass matching including
many-to-one, exception workflow with ageing and ownership, idempotent re-runs, maker-checker
settlement. *Exceptional* — ledger-generated expectations including fees and FX, break taxonomy driving
root-cause fixes upstream, and an ops-headcount reduction plan tied to auto-match rate.

**Traps.** Matching only on exact keys. Mutable raw data. Treating the exception queue as a report
rather than a workflow.

---

### SD-80 · Cross-border payments & FX   [T2 · FT★ A]

**Read aloud:** *"Design the system that lets customers send money abroad: they pay in one currency and
the recipient gets another, in seconds where possible."*

**Crux.** **Quoting a rate is making a promise against a moving market**, and the money crosses
several systems with different speeds and finality. The design is **quote → lock → fund → convert →
pay out** with the company's **FX exposure** managed explicitly, and with **prefunded accounts** in
destination countries as the trick that makes it fast.

**Numbers if asked:** 40 corridors, 300k transfers/day, quotes valid 30 seconds to 24 hours, market
rates move constantly, local payout rails differ by country (instant to T+2), prefunded balances in 25
countries, and compliance screening on both ends.

**Listen for:** **quote service** with a rate source, a margin, an expiry, and a locked rate stored with
the transfer · **exposure management**: aggregating net positions per currency and hedging/rebalancing
treasury, rather than converting each transfer on the market · **prefunding** local accounts to pay
out instantly and settle the cross-border leg in bulk later — and the liquidity forecasting it
requires · **multi-currency double-entry ledger** with explicit FX conversion entries and realised
gain/loss · **payout rail adapters** with per-rail status semantics · **transfer state machine** with
idempotency and refunds in the original currency · **compliance**: screening, travel-rule data, limits
per corridor.

**Probes:** *"A customer locks a quote for 24 hours and the currency drops 4%. Who loses money?"* ·
*"Your prefunded balance in Mexico runs out at 2 p.m. What happens?"* · *"How do you record a GBP→MXN
transfer in your ledger?"* · *"The payout rail returns 'pending' for three days."* · *(EM bar)* *"Who
owns FX risk — engineering, treasury or product — and how does the system make that ownership
visible?"*

**Weak / Strong / Exceptional.** *Weak* — call an FX API per transfer, one-currency ledger. *Strong* —
locked quotes, multi-currency ledger with FX entries, prefunding with forecasting, rail adapters,
transfer saga. *Exceptional* — treats net exposure as the system's real output for treasury, prices quote
duration as risk, and designs liquidity alerts as operational SLIs.

---

### SD-81 · Payouts & disbursements to bank rails   [T2 · FT★ A U]

**Read aloud:** *"A marketplace pays millions of sellers and drivers every week. Design the payout
system."*

**Crux.** **Money leaving is the dangerous direction**: a duplicate payout is usually unrecoverable, and
bank rails have **asynchronous, delayed and sometimes contradictory** status reporting. The design
centres on **exactly-once intent with idempotent rail submission**, **returns** that arrive days later,
and **funding** — making sure the money is there before you promise it.

**Numbers if asked:** 4M payees, weekly cycle plus on-demand instant payouts, 6 rails (batch ACH-style
files, real-time rails, cards, wallets), returns arrive up to 5 business days later (closed account,
wrong details), some payees blocked by compliance, and a funding account that must be topped up before
batch submission.

**Listen for:** **payout as a state machine** (calculated → approved → submitted → sent → settled /
returned / failed) with an idempotency key per payout that survives retries and re-runs ·
**balance reservation** before submission so the same earnings cannot be paid twice · **rail
adapters** — batch-file rails with file-level and record-level acknowledgements, real-time rails with
synchronous-but-unreliable responses · **returns handling** — reverse the ledger entry, notify, retry
with corrected details · **funding check and cut-off times** per rail · **compliance holds** and limits
· **reconciliation** against bank statements (see SD-79).

**Probes:** *"You submitted a batch file and got no acknowledgement. Do you resubmit?"* · *"Instant
payout request times out at the rail. What do you tell the driver?"* · *"2% of last week's payouts come
back as returns on Thursday. Walk me through it."* · *"How do you guarantee earnings can't be paid out
twice when the weekly run and an instant payout race?"* · *(EM bar)* *"A bug double-paid 800 sellers.
What happens next — technically and with the business?"*

**Weak / Strong / Exceptional.** *Weak* — loop over payees and call a bank API. *Strong* — idempotent
payout state machine, reservation, rail-specific adapters with ack semantics, returns flow, funding
check, reconciliation. *Exceptional* — designs ambiguous rail outcomes explicitly ("unknown" as a state
with a resolution procedure), and puts kill switches and per-run limits on the outbound path.

---

### SD-82 · Real-time credit decisioning (BNPL / instant lending)   [T2 · FT★ A]

**Read aloud:** *"At checkout, customers can split a purchase into instalments. Design the system that
decides, in under a second, whether to lend them the money — and then services the loan."*

**Crux.** **A regulated, explainable decision under a latency budget**, followed by a long-lived
financial object. The decision combines bureau data, internal history and models; regulators require
that every decline can be explained and that the same inputs give the same answer. After approval, the
**loan servicing** (schedules, collections, late fees, early repayment) is a ledger and state-machine
problem that lasts months.

**Numbers if asked:** 500 decisions/sec at peak, under 800 ms p99 including a credit-bureau call that
is sometimes slow, 10M active loans, models retrained monthly, regulators require adverse-action
reasons and audit of model versions, merchants are paid upfront.

**Listen for:** **decision pipeline**: hard rules → feature assembly (internal + bureau, cached where
permitted) → model score → policy (limits, pricing) — with a **timeout strategy for the bureau** that
is a credit-policy decision · **reproducibility**: decisions stored with all inputs, model version and
policy version · **reason codes** generated from the policy and model for adverse-action notices ·
**champion/challenger** for models and policies with controlled exposure · **loan as a state machine**
and **amortisation schedule** in a ledger, with payment retries and collections workflows · **exposure
limits** per customer and portfolio · **fairness monitoring** across protected groups.

**Probes:** *"The bureau takes 3 seconds today. Approve, decline, or something else?"* · *"A regulator
asks why a customer was declined 14 months ago. Reproduce it."* · *"A new model approves 6% more people.
How do you roll it out safely?"* · *"A customer repays early mid-cycle. What changes in the ledger?"* ·
*(EM bar)* *"Who signs off a model change — data science, risk, or engineering?"*

**Weak / Strong / Exceptional.** *Weak* — synchronous model call, no versioning, servicing as a cron
job. *Strong* — budgeted pipeline with bureau fallback policy, versioned reproducible decisions, reason
codes, champion/challenger, ledger-backed servicing. *Exceptional* — treats every timeout as a risk
decision with an owner, monitors fairness and drift as SLIs, and separates model, policy and pricing
versions so each can change independently with audit.

---

### SD-93 · Personal investment tracker with price alerts   [T1 · FT G]

**Read aloud:** *"Design a personal investment tracker. Users link their brokerage and bank accounts,
see their total portfolio value and performance, and set price alerts on stocks they care about."*

**Crux.** **Two data shapes at very different speeds.** Holdings change slowly and come from
**unreliable external institutions**; prices change constantly and come from **one market-data feed
shared by everyone**. Portfolio value is holdings × prices, so the design has to decide **what to
precompute and what to compute at read time**. Alerts **invert the query**: index alerts by *ticker
and threshold*, not by user. The data-company signal is how the design handles **corrections and
history**.

**If they ask:**

| Question | Answer |
|---|---|
| Scale? | 10M users, 3M daily active; average 3 linked accounts and 30 holdings per user |
| Instruments? | ~10k distinct tickers held; US equities and ETFs to start |
| Price feed? | Licensed vendor feed. During market hours, an update per ticker roughly every second. Treat it as a stream |
| Account data? | Through an aggregator or broker APIs: pull-based, rate-limited, sometimes down for hours, sometimes returns corrected history |
| Freshness? | Portfolio value within ~a minute of the market during trading hours. Holdings within a day is acceptable |
| Alerts? | Up to 20 per user, e.g. "AAPL above 250". Deliver within ~30 seconds. Don't spam |
| Performance? | Day change on the home screen at launch. Historical charts are a later requirement |
| Accuracy? | Money is shown exactly (no floating-point drift). A displayed value must say how stale it is |

**Listen for:**
- **Separate ingestion pipelines for holdings and prices**, each with its own store and SLO.
- **Holdings ingestion as idempotent batch pulls**, keyed by `(institution, account, external_txn_id)`;
  a **raw landing zone kept for reprocessing**, and a normalised model of transactions from which
  positions are derived.
- **Third-party failure handled as a product state**: retries with backoff, per-institution circuit
  breakers, and *"last synced 3h ago"* shown to the user rather than a wrong number.
- **Price fan-out per ticker, not per user**: one latest-price cache; the home screen computes value at
  read time from 30 holdings × cached prices, which is cheap. **Don't push 10M portfolio recomputations
  on every tick.**
- **Alert matching as a range query.** Per ticker, keep "above" and "below" thresholds sorted (a sorted
  set or an in-memory structure partitioned by ticker); on each move from p0 to p1, fire exactly the
  thresholds crossed in (p0, p1]. Partitioned by ticker so it scales out.
- **Alert hygiene**: fire once per crossing, with hysteresis or re-arm rules, dedup on retry, and
  delivery through a notification service (SD-12) that respects user preferences.
- **Decimal money types** and a currency on every amount.
- **A daily snapshot job** of position values, which becomes the history store when charts arrive.

**Probe ladder:**
- *Requirements:* "Which number has to be right, and which only has to be recent?" · "What do you show
  when a bank connection has been failing for two days?"
- *Estimation:* "How many price updates per second at peak, and how many alert evaluations does that
  trigger?" (10k tickers at ~1/s ≈ 10k updates/s; the second number depends entirely on whether
  matching is indexed — that is the point of the probe) · "How much do daily snapshots add per year?"
- *Design:* "Walk me from 'AAPL ticks to 251' to a phone buzzing." · "Walk me from 'user opens the app'
  to the total value on screen."
- *Deep dives:* **"A broker sends corrected transactions for last month. What changes, and what does
  the user see?"** (the best probe: restating history, recomputing derived positions and snapshots,
  *as-of* versus *as-known* time) · "A ticker splits 4:1 overnight." · "Your price feed stalls for 90
  seconds during market open." · "A hot ticker has 2M alerts on it."
- *EM bar:* "What are the SLOs for value freshness and alert latency, and which one do you page on?" ·
  "Who owns the institution connectors, and how do you stop that team drowning in breakage?" · "What
  ships in the first six weeks?"

**Curveball:** *"A broker restates last month's transactions."* Tests whether derived positions and
snapshots can be recomputed from a retained raw zone, and whether the design distinguishes what the
value *was* from what we *believed* it was.

**Drips** (format `drip`, §7.5 — read the prompt above as increment #1): **#2** *"Show 5-year
performance charts, including time-weighted return."* · **#3** *"Add multi-currency: a user in Warsaw
holding US stocks."* Listen for the delta stated out loud and the seam that absorbs it.

**Weak / Strong / Exceptional.** *Weak* — one store, polls prices per user, recomputes every portfolio
on every tick, matches alerts by scanning all users, uses floats, treats aggregator data as
authoritative and final. *Strong* — the two pipelines, read-time valuation from a price cache, indexed
alert matching partitioned by ticker, idempotent ingestion with a raw zone, staleness shown to the
user. *Exceptional* — also brings in **bitemporal history** (what the value was vs what we believed it
was) for corrections, models corporate actions as events, separates connector reliability into its
own team and SLO, and states which numbers are approximations.

**Traps.** Confusing *portfolio value* (needs prices) with *holdings* (needs only the broker).
Over-engineering streaming for holdings that change daily. Forgetting that markets close: off-hours
load is nearly zero and batch work belongs there.
