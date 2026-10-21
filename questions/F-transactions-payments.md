# Archetype F · Transactions, payments & commerce

**SD-44 – SD-50.** Slice with `grep -n '^### SD-44' questions/F-transactions-payments.md`, then Read
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
