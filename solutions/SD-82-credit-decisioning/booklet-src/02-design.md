
# Stage 3: API and data

## The API

An application is a **resource**, not a call. The decision takes seconds and the phone may drop, so
creating an application answers at once with an identifier, and the phone polls or receives a push.

```http
POST /v1/applications
Idempotency-Key: 6f1e2c90-...            # the POS and the phone retry; we answer once
{ "merchant_id": "m_42", "amount_cents": 120000,
  "applicant": { "vault_token": "tok_8f2c" } }
-> 202 { "application_id": "ap_91", "status": "STARTED" }

GET /v1/applications/ap_91              # poll, or receive a push on the phone
-> 200 { "status": "OFFERED",
         "offers": [ { "offer_id": "of_3", "months": 6, "apr_bps": 1490,
                       "total_cents": 125600, "disclosure_version": "v7" } ],
         "expires_at": "2026-11-21T14:46:00Z" }

POST /v1/applications/ap_91/accept
Idempotency-Key: 0b7d11a4-...
{ "offer_id": "of_3", "disclosure_version": "v7" }
-> 201 { "loan_id": "ln_5531" }          # a second accept returns the same loan
```

| Field | Why it is there |
|---|---|
| `Idempotency-Key` on create | A point of sale retries on a timeout; the second request must return `ap_91`, not create `ap_92` and pull the bureau again |
| `vault_token` instead of identity | The application service never sees the raw number; the phone posts identity to the vault first |
| `202` with a status | The decision is not finished when the request returns; a slow phone network must not hold an open request for three seconds |
| `expires_at` on offers | Prices and credit files go stale; an offer accepted an hour later is a different risk |
| `disclosure_version` on accept | The customer accepts the cost statement they saw; the loan must record which one |
| `Idempotency-Key` on accept | A double tap or a retried request returns the existing loan |

The status can also be `REFERRED`, with a promise: `{"status": "REFERRED", "finish_by": "...",
"message": "We'll text you in about two minutes"}`, and `DECLINED`, with a pointer to the notice the
customer will receive. The merchant's point of sale sees the same states, with less detail: *pending*,
*approved*, *not approved*.

**The event** that leaves the system after booking:

```json
{ "event_id": "ev_77", "type": "LoanBooked", "loan_id": "ln_5531",
  "application_id": "ap_91", "merchant_id": "m_42",
  "principal_cents": 120000, "merchant_fee_cents": 3600,
  "terms": { "months": 6, "apr_bps": 1490 }, "booked_at": "2026-11-21T14:31:08Z" }
```

It is delivered at least once; every consumer de-duplicates by `event_id`.

**The internal decision interface** is the contract between the applications team and the decisioning
platform:

```json
Decide(application_id, applicant_token, merchant, amount) ->
  { "outcome": "APPROVE | REFER | DECLINE",
    "offers": [...], "reasons": ["high utilisation", "short history"],
    "versions": { "model": "v9", "policy": "v31", "pricing": "v12" },
    "missing": ["bureau_a"], "path": "second_bureau", "record_uri": "rec://..." }
```

::: why
**Why `missing` and `path` are in the answer.** The applications team must be able to show "pending"
for a referred application, and operations must be able to count how often each degraded path is taken.
If the decision interface hides which data was missing, nobody can prove the policy's caps hold.
:::

## The data model

![The conceptual model: one application, many vendor calls, one decision, many offers, at most one loan.](diagrams/video-erd-chen.pdf){width=92%}

Read the conceptual model aloud in one breath: *an applicant, known by a token, submits applications;
each application makes paid vendor calls; each is decided once; a decision holds offers; an application
books at most one loan; a loan is paid out by funding transfers.*

![The physical tables. The record body lives in object storage under `record_uri`.](diagrams/video-erd-physical.pdf){width=100%}

```sql
CREATE TABLE application (
  id            text PRIMARY KEY,
  merchant_id   text NOT NULL,
  applicant_tok text NOT NULL,            -- a vault token, never identity
  amount_cents  int  NOT NULL,
  status        text NOT NULL,            -- STARTED ... FUNDED
  version       int  NOT NULL             -- optimistic lock
);
CREATE TABLE decision (                   -- written once, never updated
  application_id text PRIMARY KEY REFERENCES application(id),
  outcome text, reasons text[], model_v text, policy_v text, pricing_v text,
  record_uri text NOT NULL
);
CREATE TABLE loan (
  id text PRIMARY KEY, application_id text UNIQUE NOT NULL,   -- one loan per application
  offer_id text NOT NULL, disclosure_v text NOT NULL, terms jsonb NOT NULL
);
CREATE TABLE outbox (event_id text PRIMARY KEY, type text, payload jsonb, published_at timestamptz);
CREATE TABLE vendor_call (application_id text, vendor text, seq int, outcome text,
  cost_cents int, ms int, PRIMARY KEY (application_id, vendor, seq));
```

| Store | Holds | Lose it? |
|---|---|---|
| Application database | applications, decisions, offers, loans, outbox, vendor calls | No: replicated synchronously within the region; point-in-time recovery |
| Decision records (object storage) | the full record body, encrypted | No: versioned objects, retention lock for the retention period |
| Vault | identity values, encrypted per field | No: it is the only copy; replicated across zones, backed up with its keys separately |
| Event log | LoanBooked and decision events | Can be rebuilt from the outbox table, which is kept for a week after publishing |
| Report store | recent bureau reports for reuse | Yes: a miss costs a dollar, not correctness |

::: why
**Why the decision is written once.** If a decision row can be updated, "what we decided" and "what we
decide now" become the same column, and an audit cannot tell them apart. A referred application that is
later finished gets a second decision with its own record, and the application moves on; nothing is
overwritten.
:::

# Stage 4: High-level design

Build the design in three versions, each answering the objection to the one before. Say the objection
aloud before drawing the next version: it shows the interviewer that each box exists for a reason.

## Version 1: the simplest thing that works

![V1: one application service calls the vendors one after another and writes the loan.](diagrams/video-base-v1.pdf){width=100%}

The point of sale calls an application service, which calls the identity vendor, then the bureau, runs a
scoring function and writes the application and, on acceptance, the loan. It would work in a demo.

> "Version one, so we have something to break: one service, the calls in order, one table. Three
> objections. The latencies add up, so the bureau's slow tail alone breaks the three seconds. A dropped
> phone retried on another device can book twice. And nothing records why we decided."

## Version 2: one deadline, one state machine, one atomic step

![V2: an orchestrator calls vendors in parallel under one deadline; the application is a state machine; booking writes an outbox row.](diagrams/video-base-v2.pdf){width=100%}

Three changes, each answering one objection. A **decision orchestrator** sends all vendor calls at once
and decides at a deadline, with a circuit breaker per vendor. The **application becomes a state machine**
in the database, one committed row per transition, with an optimistic version, so a retry or a second
worker cannot move it twice. **Booking** is one transaction that inserts the loan under a unique
constraint on the application and writes an **outbox** row that a relay publishes to an **event log**.
The scoring function becomes a **versioned policy engine**: model, policy rules, pricing.

> "Version two answers latency and correctness. What it leaves: what we do when the bureau is missing at
> the deadline, identity data in every row and log, no record that survives a model change, and nobody
> paying the merchant."

## Version 3: regulated, explainable, owned

![V3: the vault, decision records, the policy table inside the policy engine, funding and servicing consuming LoanBooked.](diagrams/video-base-v3.pdf){width=100%}

The **identity vault** tokenises at apply and detokenises only inside the vendor adapters, which need
the real values for the call. **Decision records** go to encrypted object storage, written once. The
**missing-data policy table** lives inside the policy engine, versioned with the policy. **Funding** and
**servicing** consume LoanBooked. Decline notices are generated from the decision's reasons.

> "Version three makes it regulated and owned: identity in a small box, every decision replayable, every
> degraded path a signed policy, and money moving after booking, not during it."

## The numbered flows, one per functional requirement

**FR1 · Apply.**

![FR1: apply. The identity is tokenised before anything else sees it.](diagrams/video-flow-fr1.pdf){width=100%}

1. The phone posts the application with an idempotency key.
2. The API edge tokenises identity in the vault (or the phone posts identity to the vault directly and
   sends the token; both keep the application service clean).
3. The application service creates the row, status STARTED.
4. The row commits.
5. The service answers.
6. The phone has `202 ap_91`.

**FR2 · Decide.**

![FR2: decide. Everything at once, one deadline, a record written once.](diagrams/video-flow-fr2.pdf){width=100%}

1. The application service asks the orchestrator to decide, with a deadline.
2. The vendor adapters detokenise the identity in the vault for the calls that need it.
3. Identity, fraud and bureau A are called at once.
4. Answers arrive, or the deadline passes and the missing call is recorded.
5. Features, model, policy and pricing run, including the missing-data table if needed.
6. The decision record is written once.
7. The decision returns; the application row becomes OFFERED, REFERRED or DECLINED.
8. Offers reach the phone.

**FR3 · Accept and book.**

![FR3: accept and book. One transaction.](diagrams/video-flow-fr3.pdf){width=100%}

1. The phone posts accept with the offer and the disclosure version, and an idempotency key.
2. The API edge passes it to the application service.
3. One transaction: the status moves to BOOKED at a version, the loan is inserted with a unique
   application ID, and the outbox row is inserted.
4. The service answers.
5. The phone shows `201 ln_5531`.

**FR4 · Fund and hand off.**

![FR4: fund and hand off. After the customer has left the counter.](diagrams/video-flow-fr4.pdf){width=100%}

1. The booking transaction has written the outbox row.
2. The relay publishes LoanBooked to the event log.
3. Funding and servicing consume it: funding adds the loan to tonight's batch for the merchant; servicing
   opens the schedule (SD-95). Decline notices are generated from DECLINED decisions on their own path.

## The C4 views

![Context: the customer and the merchant on the left; vendors, the partner bank and servicing on the right.](diagrams/video-c4-context.pdf){width=92%}

![Containers. Every container exists for one reason.](diagrams/video-c4-containers.pdf){width=100%}

| Container | Why it is separate |
|---|---|
| API edge | Merchant authentication, idempotency-key storage, rate limits per merchant; the only public surface |
| Application service | Owns the state machine and the one atomic step; no vendor code in it |
| Decision orchestrator | Owns time: the deadline, the breakers, the per-vendor rate limits; one team can change vendors without touching booking |
| Policy engine | Owns the versioned model, rules and pricing; must be replayable, so it is a pure function of inputs and versions |
| Identity vault | The regulated part, kept small, audited separately |
| Application database | One relational primary; correctness lives in its constraints |
| Event log | Decouples the counter from funding, servicing, notices and analytics |
| Funding | The only component that moves money; its own state machine and reconciliation |
| Decision records | Object storage with a retention lock; cheap, durable, written once |

## The two core sequences

![Apply and decide: submit, then everything at once, then one record.](diagrams/video-seq-decide.pdf){width=95%}

![Accept and book: one transaction, then at-least-once publishing.](diagrams/video-seq-book.pdf){width=95%}

The gather step, in code:

```python
async def decide(app, deadline_s=2.0):
    calls = {v: asyncio.create_task(adapter[v].call(app)) for v in required(app)}
    done, pending = await asyncio.wait(calls.values(), timeout=deadline_s)
    for t in pending:
        t.add_done_callback(record_late_answer)   # paid for: keep it, never discard
    got = {v: t.result() for v, t in calls.items() if t in done and not t.exception()}
    missing = [v for v in calls if v not in got]
    return policy.decide(features(app, got), missing=missing)   # the table decides, not this code
```

::: warn
**Do not cancel the late calls.** A cancelled bureau call has usually been answered and billed already on
the vendor's side. Let it complete, record it, and use it to finish a referred application. Cancelling
throws away a dollar and the evidence.
:::

# Stage 5: Why these choices

## One relational database for applications, decisions and loans

**Why here.** The load is about 50 committed transitions a second at peak; the correctness lives in
constraints (`UNIQUE(application_id)`) and conditional updates, which a relational database does in one
transaction with the outbox row. **Internals to explain.** Row-level locks under a conditional `UPDATE`;
unique indexes checked at insert; synchronous replication to a standby in another zone; point-in-time
recovery. **Alternatives.** A distributed SQL database: correct, unneeded at this scale, and more to run.
A key-value store: no multi-row transaction for loan plus outbox, so the outbox would have to be emulated.
**Verdict:** one relational primary, replicated; revisit at a hundred times the volume.

## A decision orchestrator with deadlines and breakers

**Why here.** The customer's wait is set by the slowest vendor unless something owns time. The
orchestrator owns one deadline per application and a breaker and a rate limit per vendor. **Internals.**
Scatter-gather with a timeout; breakers that open on an error rate or a latency percentile over a window,
half-open with a trickle of probes; token buckets at the contract rate. **Alternatives.** A durable workflow
engine (good when steps last hours or days; fine here too, as the honest equal); a service mesh's timeouts
(they cut calls but do not decide what happens next).

## An outbox and an event log

**Why here.** "The loan exists" and "funding will hear about it" must be one fact. Writing the event in
the same transaction as the loan and publishing it afterwards gives that without a distributed
transaction. **Internals.** A relay polls unpublished rows (or tails the database's change log), publishes,
and marks rows published; it is at least once; consumers de-duplicate by `event_id`. **Alternatives.**
Publishing directly after the commit (loses the event if the process dies between the two); two-phase
commit to the broker (slow, rarely supported, unnecessary).

## Object storage for decision records

**Why here.** About 8.4 TB over seven years, written once, read rarely, kept under a retention rule.
**Internals.** Versioned objects; a retention lock so records cannot be deleted early; encryption with a
key per record so that destroying the key at the end of retention makes every copy unreadable.
**Alternatives.** The database (expensive, and backups multiply copies of identity-adjacent data); a data
warehouse (fine for analytics, wrong as the system of record).

## A tokenisation vault

**Why here.** The regulated data should exist in one small place. **Internals.** Format-preserving or
random tokens; field-level encryption with keys in a hardware-backed key service; an access log with the
purpose of every detokenise; detokenise allowed only to named callers (the vendor adapters).
**Alternatives.** Encrypting the database at rest (protects stolen disks, not a leaked query, log or
export); a bought tokenisation service (a fine choice; the boundary matters more than who built it).
