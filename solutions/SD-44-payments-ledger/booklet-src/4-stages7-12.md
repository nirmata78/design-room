
# Stage 7: Requirements that arrive mid-round

Each worked as a delta: what changes, what does not, what it costs.

**"Merchants want to capture up to seven days after authorisation."** Changes: `AUTHORIZED` becomes a long-lived state; a
job voids authorisations nearing the network's expiry; the merchant gets a webhook first. Does not change: the journal (an
authorisation can be posted as a memo hold or not at all; captures post as before). Cost: one scheduled job and a state
timeout, plus a support question when a capture arrives after expiry (a new authorisation, which may be declined).

**"Add a second processor for resilience."** Changes: a routing step (by cost, card type, region, health); a second adapter
with its own error taxonomy and inquiry; reconciliation per processor. Does not change: the state machine, the journal, the
idempotency contract. The rule that makes it safe: route **new** attempts only; an UNKNOWN stays with its processor. Cost: a
second integration (months, not weeks, because of certification and testing) and a second settlement file.

**"Marketplace: split each payment between the platform and a seller."** Changes: a capture posts more legs (seller payable,
platform commission); payouts per seller. Does not change: the posting function, which already takes N legs and checks the
sum. Cost: more accounts (one payable per seller), so the hot-account question returns for large sellers.

**"Multi-currency settlement."** Changes: the processor settles in a different currency from the charge; a conversion
transaction with its rate; an FX gain or loss account. Does not change: every amount carries its currency, so no existing
row is ambiguous. Cost: rate versioning, and reconciliation that matches converted amounts within a tolerance with a stated
rounding rule.

# Stage 8: Failures and reliability

| Failure | Blast radius | Response |
|---|---|---|
| Processor slow | payments for that processor become UNKNOWN | deadline, `pending`, inquiry; breaker if sustained |
| Processor down | all new payments for it | breaker; route new payments elsewhere; never UNKNOWNs |
| Database primary failover | seconds of write unavailability for one partition | clients retry with the same key: safe |
| Relay stuck | webhooks late; consumers stale | outbox age alert; merchants can `GET` |
| Inquiry endpoint down | UNKNOWNs age | wait; settlement file resolves them next day |
| A bad release posts wrong entries | money for many merchants | kill switch, payout hold, reversing entries (6.7) |
| Settlement file late or malformed | no reconciliation that day | stored raw; parse errors are breaks; next file catches up |
| Webhook endpoint of a merchant down | that merchant only | retries for days; then reconcile by `GET` |

**One incident, walked through: "payments failing at 3 a.m."**

1. The page is *UNKNOWN count rising for processor A, latency at the 1.9 s deadline* (the symptom pair says: processor slow).
2. Check the processor's status page and the breaker. If errors exceed the threshold, the breaker opens; new payments route to
   processor B where contracts allow.
3. Do **not** retry UNKNOWNs elsewhere. Confirm the inquiry job is running and rate-limited to A's published limit.
4. Tell merchant support: payments may show `pending` for minutes; they are not failed; do not retry as new payments.
5. When A recovers, watch UNKNOWN age fall. Anything still unknown at the next settlement file becomes a break.
6. Postmortem: was the deadline right? Did any merchant integration treat `pending` as failure?

# Stage 9: SLOs, observability, cost

**SLOs** (initial targets, to be agreed with the business):

| SLO | Target | Measured from |
|---|---|---|
| Payment API success, excluding legitimate declines | 99.95 % | API logs, outside the service |
| Decision latency | p99 under 2 s (including `pending` answers) | API logs |
| UNKNOWN resolution | 99 % within 15 minutes | payment table |
| Ledger balanced | 100 %; any violation is a page | continuous query |
| Breaks owned | 100 % within 1 day | break table |
| Webhook delivery | 99.9 % within 1 minute of commit | outbox and sender logs |

**The dashboard** has five rows: money in (approval rate per processor and segment), unknowns (count and oldest age), the
ledger (balance check, projection lag), events (outbox age, webhook success), and the outside truth (breaks by age and type).

**Cost items and levers.** Infrastructure: a relational cluster growing toward 580 TB over seven years (cold storage for old
partitions), a log, a handful of services. People: two engineering teams and a finance-operations function. Processor fees
dominate everything: a percentage of every payment's value. The engineering levers on cost are therefore **routing** (send
each payment to the cheapest processor that will approve it) and **false declines** (every wrongly declined payment is lost
revenue). One basis point of the yearly volume outweighs the database cluster.

# Stage 10: The EM layer (auxiliary at Staff)

**Phasing.**

| Release | Scope | People × time (illustrative) |
|---|---|---|
| V1, bought | a processor's hosted payment page and token vault; our orders, their records | 3 engineers × 1 quarter |
| V2, built | idempotency, the state machine, the journal | 5–6 engineers × 2 quarters |
| V3, run | outbox, inquiry, reconciliation, a second processor | two teams × 2–3 quarters, plus finance operations |

V1 keeps card data entirely out of our scope. That is worth more than any of our code.

**The one-way doors.** The ledger schema (seven years of records and every auditor depend on it) and the idempotency contract
(every merchant integration has encoded it). These get the most review; everything else can change in a quarter.

**Team seams.**

| Team | Owns | Contract |
|---|---|---|
| Payments API and state machine | keys, states, the deadline | the public API and webhook schema |
| Ledger | accounts, postings, projections | a posting interface; reviews every new transaction type |
| Processor integrations | adapters, references, error taxonomy | one internal interface per processor |
| Reconciliation and finance tooling | expectations, breaks, the console | break types and ageing targets |

**With half the team:** keep V1 longer; build the journal and idempotency first (they are the one-way doors); buy reconciliation
tooling before building it; defer the second processor.

**On-call.** The ledger balance check and UNKNOWN age page the payments on-call; breaks by age page finance operations in
business hours; the runbook starts from the symptom pairs in 6.8. Inject processor timeouts in staging every day, because the
UNKNOWN path runs rarely in production and breaks quietly.

# Stage 11: The close

> "**What:** a state machine per payment that admits unknown, an idempotent API with keys inserted first, an immutable
> double-entry journal where balances are derived, and reconciliation against each processor's settlement file.
> **Trade-off:** I accept pending answers and a reconciliation team in exchange for never guessing.
> **Risk:** the unknown path runs rarely, so it must be tested daily.
> **Next:** harden the inquiry protocol per processor, and make breaks an owned, aged workflow."

# Stage 12: Self-check after a simulator run

| | Weak | Strong | Exceptional |
|---|---|---|---|
| Requirements | "charge the card and store it" | asks what must never happen, in order | names the outside parties' failure modes before drawing |
| Exactly-once | claims it | "at-least-once plus idempotency" | states precisely: exactly-once *effect* per intent, never delivery, and designs each point on the truth timeline |
| Data model | balance column | double entry, derived balances, integer minor units | the deferred balance check, conditional updates on legal edges only, checks against rows not projections |
| Timeout | "retry" | UNKNOWN plus inquiry | keeps the call alive past the client deadline; same reference for unknown, new reference only after a definite no |
| Retries | "check the key" | key inserted in the same transaction | request hash, 409 versus 422, retention in the contract, the crash case as an UNKNOWN |
| Events | publish after commit | outbox | per-payment ordering and consumers that ignore backward transitions |
| Outside truth | none | daily reconciliation | line by line, break types, owners, ageing, three-way with the bank |
| Operations | uptime | approval rate, UNKNOWN age | the zero-sum page, symptom pairs, a synthetic payment per processor |

**Common traps.** "A distributed transaction with the bank." A balance column as the source of truth. A timeout treated as
failure. Floats for money. Keys checked rather than inserted. A changed retry silently accepted. Events published outside the
transaction. History edited. No reconciliation, or reconciliation by totals. Failing over an UNKNOWN to a second processor.
