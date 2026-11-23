
# Stage 7: Requirements that arrive mid-round

Interviewers often add a requirement two thirds of the way through. The strong answer names the seam that
absorbs it, what changes, what does not, and what it costs.

**"Product wants cash-flow underwriting: read the customer's bank account."** Bank-account data arrives
through an aggregator in seconds to minutes, after the customer consents in a separate flow. It is never
awaited at the counter. *What changes:* a new vendor adapter; a new optional input to the policy; a new
row in the missing-data table ("bank data absent: decide on the bureau alone"); the refer path can wait
for it when the policy asks. *What doesn't:* the deadline, the state machine, booking. *Cost:* a consent
flow, a vendor contract, and more data inside the vault boundary.

**"Merchants want a pre-approval: the customer checks their limit at home before visiting."** A soft
inquiry that does not affect the customer's file, a decision with an offer valid for thirty days, and at
the counter only a re-check. *What changes:* a new application type with a longer expiry; the decision
record must say it was a soft inquiry; the counter path can skip the bureau if the pre-approval is fresh
and the policy allows. *What doesn't:* booking. *Cost:* exposure from offers that live for weeks; credit
risk sets a cap on outstanding pre-approvals.

**"We're launching in a second country."** Different bureaus, different rules on reasons and retention,
possibly a different lender of record, and data that must stay in the country. *What changes:* a regional
deployment with its own vault and records; vendor adapters per country; policy and disclosures versioned
per country. *What doesn't:* the mechanisms. *Cost:* a second compliance owner and a second on-call.

**"The partner bank wants to buy each day's loans at 17:00."** A loan-sale file built from the booked
loans of the day, reconciled against the bank's purchase confirmation. *What changes:* a consumer of
LoanBooked that builds the file; a reconciliation break type. *What doesn't:* the counter. This is the
event log earning its place.

# Stage 8: Failures and reliability

| Failure | Blast radius | Detection | Response |
|---|---|---|---|
| Bureau slow | about 3 % of applications take the policy path | latency per vendor; fallback rate | none needed: the deadline decides |
| Bureau down | refer and fallback rates jump | breaker open; refer rate | policy table; per-vendor rate limits; status to merchants |
| Policy or pricing bug | every decision | approval rate per merchant per hour; reason mix | canary; kill switch to the previous version |
| Model artefact fails to load | decisions stop | readiness check; decide errors | keep the previous version loaded; roll back |
| Database primary lost | writes pause for the failover | health checks | synchronous standby; requests retry by idempotency key |
| Relay stuck | funding and servicing delayed | outbox age | restart; events are still in the table |
| Vault down | nothing new starts | vault SLI | refer; page security on-call |
| Funding transfer unknown | one merchant's money | UNKNOWN count and age | query, wait for the file, never resend |
| Notices fail | declined customers not told in time | notices due against sent | retry; the deadline for notices is days, not seconds |

**One incident, walked through.** Saturday 11:00: bureau A starts timing out. At 11:00:20 its breaker
opens on the error rate over the last twenty seconds. The orchestrator stops calling it; the policy table
sends eligible applications to bureau B at five a second, returning customers under $500 to the no-bureau
row, and the rest to refer. The refer rate climbs from 0.5 % to about 35 %; an alert fires and the on-call
engineer confirms the breaker, checks the refer queue age (under two minutes) and the cap counter for the
no-bureau row (about $40,000 of $250,000). Merchant operations posts a status banner: *some approvals are
taking a few minutes*. At 11:20 the breaker half-opens, probes succeed, it closes, and the refer queue
drains oldest first. The post-incident review reports refer completion (illustrative: 81 %), the exposure
used, and the spend at bureau B, and credit risk decides whether the caps were right.

# Stage 9: SLOs, observability, cost

| SLI | How it is measured, from outside | Objective (initial target) |
|---|---|---|
| Offers on screen | submit to offers at the phone SDK, p95 | under 3 s, 99 % of hours |
| Decision availability | answers (offer, refer, decline) over submits | 99.9 % in merchant hours |
| Refer completion | referred applications finished within 10 minutes | 95 % |
| Booking correctness | duplicate loans found by the nightly check | zero |
| Funding | loans funded within one business day | 99.5 % |
| Replay | sampled records that reproduce | 100 % |
| Vault | tokenise and detokenise success | 99.95 % |

**A synthetic application**, every minute, in each region: a test merchant, a test identity the bureaus
provide for testing, through apply, decide and a cancelled accept. It measures the promise end to end.

**The dashboard**, top to bottom: offers latency; approval rate per merchant (a heat map against
baselines); fallback rate per policy row with its cap; refer queue age; vendor latency, errors and spend;
booked-not-funded; replay mismatches; vault health.

**Cost, illustrative.** Bureau pulls about $2M a month; identity checks about $100k; compute and storage
a small fraction of either. The levers: report reuse inside the contract's window (about $400k a month);
the second-bureau rule (no races); asking the bureau only when the policy needs it (a returning customer
with a recent report may not); and negotiating the contract with spend data per merchant segment.

# Stage 10: The EM layer (auxiliary at Staff)

**Phasing.** V1 (one service, sequential calls, one table): three engineers, two months, to learn the
vendors. V2 (orchestrator, state machine, outbox, versioned policy engine): a team of six for two
quarters. V3 (vault, records, policy table, funding, notices, champion and challenger): two teams for two
more quarters, plus security and compliance time. The riskiest work first: the vendor adapters and the
policy table, because they decide whether the counter promise can be kept.

**Team seams.**

![Six owners, three contracts.](diagrams/video-teams.pdf){width=95%}

Applications and origination own the state machine and booking. The decisioning platform owns the
orchestrator, the policy engine and model serving. Vendor integrations own the adapters, the contracts and
the spend. Security owns the vault. Credit risk and data science own the models and every degraded path
and its cap. Compliance owns disclosures, notices and retention. The contracts between them are the
decision interface, the decision record and the LoanBooked event.

**With half the team.** Keep the deadline, the policy table, the atomic booking and the records. Buy the
vault. Defer champion and challenger (run one model; change it rarely, with a backtest and shadow) and
cash-flow underwriting.

**On-call.** Engineering pages on the SLIs; credit risk is paged by the fallback-rate and cap alarms,
because they own the decision behind them. A runbook per vendor: how to read its status, who to call at
the vendor, which policy rows change when it is down.

**Buy against build.** Bureaus, identity and bank-data vendors are bought. A tokenisation vault is a
reasonable buy. A workflow engine is a buy if steps grow to days. The orchestrator, the policy engine and
the records are ours: a regulator asks us, not a vendor, why someone was declined.

# Stage 11: The close

> "What I built: an application that's a small state machine in one database, with one atomic step,
> accept to book, and an outbox. The trade-off I chose: one deadline with a signed policy for whatever is
> missing, rather than waiting or racing paid vendors. The risk I'd watch: a degraded path or a model
> change without an owner and a cap. Next: the challenger pipeline and cash-flow data, behind the same
> policy table."

# Stage 12: Self-check after a simulator run

| Area | Weak | Strong | Exceptional |
|---|---|---|---|
| Framing | Treats it as a throughput problem | Says the load is tiny and the vendors are the problem | Asks who the lender of record is and what that changes |
| Latency | Sequential calls; hedged bureau requests | One deadline, parallel calls, breakers | Derives the deadline from the promise; per-vendor rate limits |
| Missing data | "Approve with partial data" in code | A policy table with refer | Every row owned, capped, counted; "a timeout is not a reason" |
| Correctness | Check-then-insert; a saga for everything | Conditional update, unique loan, outbox | Says which steps are facts, which expire, which can be undone |
| Money | Funding inside the request | Funding after booking, retried | UNKNOWN as a state; reconciliation with breaks and owners |
| Explainability | "The model returns a score" | Versions and reasons stored | Frozen inputs, nightly replay, crypto-shredding at retention end |
| Models | Shadow, then switch | Champion and challenger with a slice | Says why shadow cannot measure loss; fairness by group |
| Identity | "Encrypt the database" | A vault with tokens | The right rulebook; the vault kept small and tier-0 |
| Operations | CPU and errors | Offers latency, approval rate | Symptom pairs; canaries for policy changes; credit risk on the pager |

**Common traps.** Treating it as a throughput problem. Sequential vendor calls. Hedging paid pulls.
"Approve with partial data" as a code default. A saga that compensates a credit pull. Check-then-insert on
the loan. Re-running today's model to explain yesterday. "Encrypt the database" as the identity answer.
Quoting the card standard for a social security number. No owner for any degraded path.

\newpage

# Part III: The internals

## Appendix A: Scatter-gather with one deadline

A deadline is a point in time, not a duration per call. The orchestrator computes it once (the start of
the vendor calls plus two seconds) and every wait uses the time left until it. Calls that finish early
free the decision early. Calls that are late are not cancelled: their answers are recorded when they
arrive. Three details matter in practice. **Required against optional**: the policy says which inputs are
required for which application (a returning customer may not need a fresh bureau report); optional inputs
are never awaited. **Fan-out limits**: each vendor has a concurrency limit in the adapter, so a burst of
applications cannot open hundreds of connections to a vendor that throttles. **Clock**: the deadline is
measured on the orchestrator's monotonic clock, never on wall time, so a clock adjustment cannot extend or
shorten it.

## Appendix B: Circuit breakers and token buckets

A breaker has three states. **Closed**: calls flow; the adapter counts errors and slow calls over a
rolling window (for example twenty seconds). When the error rate or the share of calls slower than a
threshold crosses a limit, it **opens**: calls are refused immediately and the policy treats the vendor as
missing. After a cool-down it goes **half-open**: a few probe calls go through; if they succeed, it closes;
if not, it opens again. Two mistakes to avoid: a window so short that one slow second opens it, and a
breaker per server rather than per vendor, which lets each server rediscover the outage separately. A
**token bucket** at the vendor's contract rate is separate from the breaker: a healthy vendor can still be
over its contract. Tokens refill at the contract rate; a call without a token is not sent, and the
application follows the policy (usually refer).

## Appendix C: Optimistic versions and the conditional update

An optimistic lock does not lock anything while the request is thinking. The worker reads the row and
its version, does its work, then writes with `WHERE version = <what I read>`. If another worker wrote in
between, the version changed and the update matches zero rows: the worker knows it lost and re-reads.
This suits applications well: conflicts are rare (two devices, a retry), and holding a database lock
across a vendor call would be a disaster. The unique constraint on `loan.application_id` backs it up: it is
checked by the database at insert, so even a code path that forgets the version check cannot create a
second loan.

## Appendix D: The outbox and the relay

The outbox is a table written in the same transaction as the business change. A relay (a small process)
reads unpublished rows in order, publishes each to the log, and marks it published. If the relay dies after
publishing and before marking, the row is published again: consumers must be idempotent. Alternatives to
polling are tailing the database's change log, which avoids the polling load and keeps order per key. Keep
published rows for a week, so the log can be rebuilt from them if needed, then delete them in batches.

## Appendix E: Decision records and replay

A record is written once to object storage with a retention lock: it cannot be changed or deleted before
the retention date, even by an administrator. It is encrypted with a data key unique to the record, and
that key is encrypted by a key in a key-management service. The database holds the record's URI and the
hot fields (outcome, reasons, versions). Replay needs three things kept for as long as the records: the
model artefacts (in a registry, by version), the policy and pricing tables (as versioned data, not code
paths), and the feature code (versioned with the model). A nightly replay of a sample catches the day
someone "cleans up" an old version. At the end of retention, destroying the data key makes the record and
every backup copy unreadable.

## Appendix F: Champion, challenger and what shadow cannot see

The champion is the model in production. A challenger is scored beside it. In shadow, the challenger's
score is recorded and never acted on, which answers *who would it approve, and with what reasons* by
segment and group. It cannot answer *do they repay*, because applicants the champion declined never
received a loan. Only a slice where the challenger decides produces those outcomes. The slice is sized by
an exposure cap that credit risk sets, and judged on early signals (first payment missed at 30 to 45 days,
early delinquency) long before charge-offs arrive at 90 to 120 days. Fairness testing compares approval
rates and outcomes across protected groups on both shadow and slice; the method and the thresholds belong
to compliance and credit risk.

## Appendix G: Tokenisation vaults

A token is a random reference to a stored value. The vault stores the value encrypted per field, with keys
held in a hardware-backed key service, and returns the token. Detokenise is allowed only to named callers,
for named purposes, and every call is logged. Format-preserving tokens (a token that looks like a nine-digit
number) help legacy systems but make it easier to confuse a token with a real value in a log; random tokens
with a prefix (`tok_`) are easier to scan for. The vault is deliberately boring: no search, no analytics,
no business logic.

## Appendix H: Where this shape shows up again

| Problem | The same core |
|---|---|
| An insurance quote at checkout | Slow, paid data vendors under a deadline; a price you must explain |
| Account opening with identity checks | Parallel checks; refer instead of decline; a vault |
| Marketplace seller onboarding | A durable state machine; an identity vault; a manual review path |
| Mortgage pre-approval | Reproducible decisions under versioned policy; reasons for a decline |
| Rental or tenant screening | Paid reports; a decision with reasons; retention rules |

## Appendix I: Testing it

Contract tests per vendor adapter against the vendor's sandbox, including its slow and error modes. A
fault-injection suite in the orchestrator: a vendor slow, failing, over its rate limit, answering after the
deadline. A concurrency test for booking: two accepts for the same application from two clients, a
thousand times, expecting exactly one loan. A replay test in CI: every policy or model change replays a
fixed set of historical records and must reproduce them, or ship as a new version. A game day each
quarter: a bureau "outage" in a test region, with credit risk in the room.

\newpage

# One-page cheat card

**Insight.** A regulated decision under a deadline set by slow, paid vendors, then one atomic step. The
load is tiny.

**Numbers.** 0.8/s average, 8/s peak · 32 vendor calls/s · $2M a month in bureau pulls · 3 % reach the
deadline without a bureau · 9,600 applications in a 20-minute outage · 100 GB of records a month, 8.4 TB
over 7 years · 2.7 s of the 3 s budget used.

**Design.** Phone → API edge (vault tokens, idempotency) → application service (state machine) →
orchestrator (one deadline, breakers, rate limits) → vendors; policy engine (model, policy, pricing,
missing-data table); one transaction for loan + outbox; event log → funding and servicing; decision
records in object storage.

**Challenges and the one-line answer.**

1. Slow bureau: everything at once, one deadline, breakers; never race paid pulls.
2. Bureau down: a signed table: second bureau, small known under a cap, refer, decline with a real reason.
3. Phone drops: conditional update at a version, unique loan, outbox in one commit.
4. Funding fails: its own state machine; UNKNOWN means query, never resend; reconcile.
5. Explain later: frozen inputs, versions, ranked reasons; nightly replay; crypto-shred at the end.
6. New model: backtest, shadow, a capped slice; shadow cannot see loss.
7. Identity: a vault; tokens everywhere else; the right rulebook.
8. Know it's broken: offers in 3 s, approval per merchant per hour, fallback against cap, booked not
   funded; read metrics in pairs.

**Close.** "One database, one atomic step. The design lives at the slow edges and in what we keep."
