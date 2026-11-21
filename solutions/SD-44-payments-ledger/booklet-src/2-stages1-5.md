
# Stage 1: Clarify requirements

Ask **seven questions, not fifteen**, and say why each one matters. The answers come from the simulator's
cue sheet.

| # | You ask | The interviewer answers | What it changes |
|---|---|---|---|
| 1 | What volume? | 10,000 payments a second at peak, 50 currencies | Journal write rate and partitioning; currency on every amount |
| 2 | How fast must the client get an answer? | An authorisation decision within 2 seconds | Most of it belongs to the processor; our part must be small; a plan for "no answer yet" |
| 3 | Who actually moves the money? | Card networks and banks through processors. They time out, return ambiguous results, and go down for hours | Unknown outcomes are the core problem; failover rules |
| 4 | What is the ledger's rule? | It must always balance. No exceptions | Double entry; atomic posting; a continuous check |
| 5 | How long must it be auditable? | Every balance explainable from immutable records for 7 years | No balance column as truth; append-only |
| 6 | Refunds and disputes? | Partial, full, chargebacks, days or months later | Adjustments are new transactions; closed periods |
| 7 | What must never happen, in order? | (You propose; the interviewer agrees) 1 charge twice or lose money · 2 unbalanced ledger · 3 slow payment | Settles every later trade: when in doubt, answer *pending* |

::: why
**Why ask question 7 yourself?** Because it turns a list of features into a priority order, and every hard
choice later in the round is resolved by it. "A slow payment is the least bad outcome" is what justifies the
UNKNOWN state, the `pending` answer, and never failing over an ambiguous payment.
:::

**Functional requirements** (each gets a numbered flow in Stage 4):

- **FR1 Pay**: authorise and capture (automatic or manual), idempotent per client key.
- **FR2 Adjust**: void, partial or full refund, chargeback; each referencing the original payment.
- **FR3 Notify**: every state change reaches the merchant (signed webhooks) and internal consumers.
- **FR4 Reconcile**: match our books against each processor's settlement file daily; every difference
  becomes an owned break.
- **FR5 Explain**: any account's balance at any time, from the journal.

**Non-functional requirements** (all initial targets):

- Zero double charges. Every journal transaction balanced at commit.
- Decision p99 under 2 s, or an honest `pending`.
- API availability 99.95 % for creates (a decline is a success, not an error).
- 99 % of UNKNOWN outcomes resolved within 15 minutes; all by the next settlement file.
- Reconciliation daily; every break owned within a day.
- Seven-year retention of immutable records.

**Out of scope, said aloud:** fraud scoring (a service we call; SD-43); card numbers (a tokenisation
service, which keeps most of the card-data compliance scope away from us); currency conversion (SD-80);
merchant onboarding and KYC (SD-78); payouts to merchants (SD-81, though the hot-account and correction
challenges need their balance check); loans and instalments (SD-95).

> "So the core is four things: a state machine per payment that admits *unknown*, an idempotent API, an
> immutable double-entry journal, and reconciliation against the outside world."

# Stage 2: Back-of-the-envelope

## How to do estimates in this round

Three numbers matter. Compute them aloud, and end each one with the decision it drives.

::: {.key title="Top-3 number 1: the journal write rate"}
**Arithmetic:** 10,000 payments a second × about 4 entries each (receivable, merchant payable, fee, and
sometimes a hold) = **40,000 entries a second** at peak.
**What it means:** one database primary will not take that at peak with multi-row transactions.
**How it changes the design:** partition the journal by account; a payment's entries go to the partitions of
the accounts they touch.
**Say:** "Forty thousand entries a second, so the journal is partitioned by account from the start."
:::

::: {.key title="Top-3 number 2: the hot account"}
**Arithmetic:** one merchant at 5,000 payments a second; a balance-row update holds a row lock for about
1.5 ms (illustrative, to be measured), so one row allows about 1,000 ÷ 1.5 about **670 updates a second**.
**What it means:** the queue grows by about 4,330 a second; the merchant's latency passes 2 s within a second.
**How it changes the design:** payments append entries; the balance is derived. Where a check needs a current
balance, split the account or serialise only that check.
**Say:** "Five thousand updates a second on one balance row would serialise on its lock, so I append entries
and derive the balance, which is also what auditors want."
:::

::: {.key title="Top-3 number 3: the latency budget"}
**Arithmetic:** idempotency insert 10 ms + fraud call 50 ms + two commits 20 ms + post-commit 10 ms about **90 ms
ours**; the processor up to **1,500 ms** at p99; **410 ms** spare of 2,000.
**What it means:** we cannot make the payment fast; we can only avoid making it slower, and decide what to do
when the processor uses all of it.
**How it changes the design:** a 1.9 s deadline, then UNKNOWN and `pending`.
**Say:** "Most of the two seconds belong to the processor. Ours stays under a hundred milliseconds, and at one
point nine seconds I answer pending."
:::

## The full table, row by row

| Quantity | Arithmetic | Label | Decision |
|---|---|---|---|
| Journal writes | 10,000 × 4 = **40,000 entries/s** | derived | partition by account |
| Average rate | peak ÷ 3 about **3,300/s** | illustrative | sizes daily volumes |
| Payments a day | 3,300 × 86,400 about **2.9 × 10^8^** | derived | settlement files are hundreds of millions of lines |
| Seven-year journal | 3,300 × 3.15 × 10^7^ × 7 × 4 × 200 B about **580 TB** | illustrative | hot partitions plus cold archive |
| Hot account | 5,000/s against about 670/s per row lock | illustrative | append, derive; sub-accounts |
| UNKNOWN rate | 0.1 % × 10,000 = **10/s**, 36,000 an hour | illustrative | the inquiry job is a real service |
| Idempotency table | 2.9 × 10^8^ × 7 days × 300 B about **600 GB** | illustrative | keys expire; contract says so |
| Reconciliation | 2.9 × 10^8^ lines ÷ 10^6^ lines/s about **5 min** | illustrative | a batch join; the output is breaks |
| Cost | processor fees are a percentage of value | fact | routing and false declines, not servers |

::: why
**Why "peak ÷ 3" for the average?** It is a common planning ratio for consumer payment traffic with a daily
peak. It is an assumption, so say so; the conclusions (hundreds of millions of lines a day, hundreds of
terabytes over seven years) survive a factor of two either way.
:::

::: warn
**The arithmetic trap.** Seven years of entries is 3,300 × 3.15 × 10^7^ × 7 × 4 about 2.9 × 10^12^ entries. At
200 bytes each that is about 580 TB. Candidates often multiply by the years twice, or forget the entries per
payment; an interviewer will redo the sum.
:::

# Stage 3: API and data

## The API

**Pay** (serves FR1; writes Idempotency, Payment, Attempt, JournalTxn):

```text
POST /v1/payments
Idempotency-Key: k-91
{ "merchantId": "m-42",
  "amount": { "value": 1050, "currency": "EUR" },   -- integer minor units, never a float
  "methodToken": "tok_7c1...",                      -- the card lives in a tokenisation service
  "capture": "auto" }

201 { "paymentId": "p-7731", "status": "captured" }
202 { "paymentId": "p-7731", "status": "pending" }   -- honest: we do not know yet
409 in progress (same key, first request still running)
422 key reused with a different body
```

::: why
**Why `202 pending` is part of the contract.** A merchant integration that cannot handle *pending* will
treat a slow answer as a failure and retry as a new payment. Making *pending* a first-class answer, with a
webhook and a `GET` to resolve it, is what lets the server be honest.
:::

**Adjust** (serves FR1 and FR2), each with its own key:

```text
POST /v1/payments/p-7731/capture  { "amount": 1050 }
POST /v1/payments/p-7731/void
POST /v1/payments/p-7731/refunds  { "amount": 2500 }

-- the refund limit, enforced in one statement
UPDATE payment SET refunded = refunded + :amt
 WHERE id = :p AND refunded + :amt <= captured;   -- 0 rows -> 422 exceeds captured
```

**Notify** (serves FR3): a signed webhook per state change, retried with backoff for days, carrying an
`eventId` that merchants de-duplicate on; plus `GET /v1/payments/{id}`, which always answers from the
database and is the backstop when webhooks are lost.

**Internal calls:** `Inquire(processor, "p-7731/1") -> approved | declined | not_found`;
`ImportSettlement(file)`, which stores the raw file unchanged before any processing; `GET /breaks?status=open`;
`GET /v1/accounts/{id}/balance -> { balance, currency, asOfEntry }`.

## The data model

![Conceptual model in Chen notation. A payment has attempts and posts journal transactions; a transaction contains at least two entries, each on one account; a balance is derived; a break may explain one transaction.](diagrams/video-erd-chen.pdf){width=96%}

![Physical model. Journal entries are partitioned by account and only inserted. The payment row is the only mutable row, changed by conditional updates. Idempotency keys keep a request hash and the stored response. The outbox commits with the state.](diagrams/video-erd-physical.pdf){width=96%}

| Table | Key | Mutability | Lose it? |
|---|---|---|---|
| `journal_entry` | `(account_id, entry_id)` | insert only | never: the book of record |
| `journal_txn` | `txn_id` | insert only | never |
| `payment` | `payment_id` | conditional updates on legal edges | never |
| `attempt` | `(payment_id, n)` | result filled once | never: the reference lives here |
| `idempotency` | `(client_id, key)` | processing -> done | after 7 days, by contract |
| `outbox` | `id` | deleted after publish | never before publish |
| `balance_projection` | `account_id` | overwritten | yes: rebuildable from entries |

**The invariant**, enforced twice: the posting function refuses to build an unbalanced transaction, and a
deferred check at commit verifies that, per transaction and per currency, Σ debits = Σ credits.

### One race the first draft glosses over: the refund check and the projection

A refund limit checked against the *balance projection* is wrong, because the projection is seconds behind.
The limit must be checked against the payment row itself, with a conditional update, because the payment row
is updated in the same transaction as the posting. Rule of thumb: **checks read the row that the posting
transaction writes; dashboards read projections.**

### One more: an attempt per call, not per payment

A retry to the processor after a definite failure is a *new attempt*, with a new reference (`p-7731/2`).
Reusing the old reference for a genuinely new attempt makes the processor deduplicate a legitimate charge; a
new reference for a retry of an *unknown* attempt makes two charges possible. The rule: **same reference while
the outcome is unknown; a new reference only after a definite "no".**

# Stage 4: High-level design

Three versions on one baseline. Each is introduced by the objection to the one before. The boxes never move.

## Version 1: the simplest thing that works

![V1. The merchant calls the API; the payment service charges the card synchronously; one transaction updates the payment's status and the merchant's balance column.](diagrams/video-base-v1.pdf){width=92%}

**The objection:** a timeout leaves no answer, and the naive code marks it failed; the processor approves half a
second later; the checkout retries as a new payment, which is approved: two holds on one card. And next month an
auditor asks why a balance is what it is, and the answer is a number updated in place.

## Version 2: one effect per intent, and books that prove themselves

![V2. The key is inserted first; the attempt is committed before the call; an adapter calls with our reference; the database holds a journal of immutable, balanced entries.](diagrams/video-base-v2.pdf){width=92%}

The heart of V2 is one transaction:

```sql
BEGIN;
  UPDATE payment SET state = 'CAPTURED', captured = 1050
   WHERE id = 'p-7731' AND state = 'AUTH_PENDING';          -- legal edge only
  INSERT INTO journal_txn (txn_id, payment_id, type) VALUES (..., 'capture');
  INSERT INTO journal_entry (account, dir, amount_minor, currency) VALUES
    (recv, 'D', 1050, 'EUR'), (mpay, 'C', 1020, 'EUR'), (fees, 'C', 30, 'EUR');
  INSERT INTO outbox (payload) VALUES ('payment.captured p-7731');
  UPDATE idempotency SET status = 'done', response = ... WHERE key = 'k-91';
COMMIT;  -- a deferred check rejects it unless debits = credits per currency
```

**The objection:** inside the database it is correct. Outside, three holes: merchants hear about changes by a
second write after commit; nothing ends an UNKNOWN; and our books can differ from the processor's with no one
noticing.

## Version 3: close every loop

![V3. An outbox relay feeds the event log and the webhook sender; an inquiry job resolves UNKNOWN payments by reference; reconciliation compares the processor's settlement file with expectations from the ledger and hands breaks to finance operations.](diagrams/video-base-v3.pdf){width=92%}

```python
def pay(req, key):
    row = idem.insert_or_get(req.client, key, hash(req))     # unique; same txn as below
    if row.existing: return row.response or conflict("in progress")
    p = db.commit(new_payment(req, state="AUTH_PENDING", attempt=1))   # evidence first
    try:
        r = adapter.authorise(p, ref=f"{p.id}/1", deadline=1.9)
    except Timeout:
        db.commit(p.to("UNKNOWN"))                           # the inquiry job takes over
        return pending(p)
    return db.commit(p.apply(r), entries(r), outbox(r), idem_done(key))
```

Run it against a crash at every line. Before the first commit: nothing happened; the client retries and the key
insert wins again. After the first commit, before the call: an `AUTH_PENDING` payment with no processor call; the
sweeper sends it to inquiry, which finds *not found* and declines it safely. During the call: an UNKNOWN in all but
name; the sweeper catches it. After the final commit: done, and the response is stored.

## The numbered flows, one per functional requirement

![FR1, pay. 1 pay · 2 create · 3 one transaction: key and AUTH_PENDING with attempt · 4 authorise · 5 by reference · 6 approved · 7 status · 8 the answer.](diagrams/video-flow-fr1.pdf){width=90%}

![FR2, a refund. The conditional update, the processor refund with a reference made of the payment and the refund key, and a new journal transaction dated now.](diagrams/video-flow-fr2.pdf){width=90%}

![FR3, notify. The outbox row commits with the state; the relay publishes; the webhook sender signs and retries; the merchant de-duplicates by event ID.](diagrams/video-flow-fr3.pdf){width=90%}

![FR4, reconcile. The raw file is stored; expectations come from the ledger; matches settle payments; every unmatched line becomes a break owned by finance operations.](diagrams/video-flow-fr4.pdf){width=90%}

![FR5, explain. A balance comes from the projection with the entry it is current to; audit sums the entries for the period.](diagrams/video-flow-fr5.pdf){width=90%}

## The C4 views and the sequences

![C4 level 1. A customer pays at a merchant; the merchant's system calls us; we call the processor and receive its settlement files; finance operations owns breaks. Two neighbours keep their own books of the same money.](diagrams/video-c4-context.pdf){width=92%}

![C4 level 2. The API owns keys and the deadline; the payment service the state machine and postings; one relational database per partition holds payments, journal and outbox; the adapter owns references and error codes; relay, webhook sender, inquiry job and reconciliation complete the loops.](diagrams/video-c4-containers.pdf){width=96%}

![One payment as a sequence.](diagrams/video-seq-pay.pdf){width=92%}

::: why
**Why one relational database per partition, not a log as the source of truth?** The posting must be atomic
across several rows (state, entries, outbox, key) and must be able to read a current value for a check (refunded
so far). A relational store with transactions and constraints does both. A log is excellent for what happens
*after* the commit (projections, consumers), which is exactly where the outbox puts it.
:::

# Stage 5: Why these choices

## A relational store for payments and the journal

**Why here:** multi-row atomic postings, constraints (unique keys, deferred balance check), conditional updates for
state edges and refund limits. **Internals to explain:** row locks and why a hot row serialises; a deferred
constraint checked at commit; partitioning by account and what a transaction that touches two partitions costs
(say: keep a posting's accounts co-located where possible, for example by merchant, and use the database's
distributed transactions only for the rare cross-partition posting). **Alternatives:** a distributed SQL store
(the same model with built-in partitioning: a fine choice at this scale); a key-value store (no multi-row
transactions: rejected for postings); an event log as the source of truth (rejected for synchronous checks).

## A transactional outbox for events

**Why here:** the event must exist if and only if the state committed. **Internals:** the relay reads committed rows in
order (by polling with an index on id, or by change data capture from the database's log); at-least-once delivery;
consumers de-duplicate by event ID. **Alternatives:** publishing after commit (a crash loses the event); publishing
before commit (a failed commit leaves a false event); a distributed transaction between the database and the broker
(rarely available, slow, and still not across the merchant).

## An adapter per processor

**Why here:** every processor has its own API shape, error codes, idempotency support and inquiry semantics. The adapter
maps errors into three classes, **retryable**, **terminal** and **ambiguous**, and the class decides the state:
retryable before the call is known to have arrived; terminal is a decline; ambiguous is UNKNOWN. Getting this mapping
wrong is how real systems double-charge.

## A batch pipeline for reconciliation

**Why here:** the outside truth arrives as files. A batch join of hundreds of millions of lines is minutes of work;
the hard part is the break workflow, not the matching.
