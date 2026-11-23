---
title: "SD-44 · Payment Processing and the Double-Entry Ledger"
subtitle: "A reference solution for a system design round at the Staff bar: one effect per intent, a state for not knowing yet, an immutable journal, and the reconciliation that keeps your books in agreement with the parties that actually move the money"
author: "design-room reference solution · practise with the simulator first"
date: "20 November 2026"
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

This is the **long answer key for question `SD-44`** in
[design-room](https://github.com/nirmata78/design-room), an open-source system design interview
simulator, and the written companion to its reference-solution video. It shows how a strong Staff
candidate (L6/L7) runs the round: what to say, what to draw, and **when**. It adds the **why** behind
every line, so you can defend each choice when the interviewer asks *"why?"*, *"what is that?"* or
*"what happens when it breaks?"*.

**The document has three layers, and you will read them differently:**

1. **Part I, the system in pictures.** Read it first. It explains what a payment is from the moment a
   customer taps a card to the moment the money shows up in the processor's settlement file, why the truth
   about a payment arrives over months, and where the load lands. There is no interview script in it.
2. **Part II, the round, stage by stage.** This is what you do in the room. Each stage has the words to say,
   what to draw, and boxes that explain every term. The eight **challenges** of the video are Stage 6, and
   each goes further here than the video can.
3. **Part III, the internals.** How idempotency keys, double-entry posting, the transactional outbox,
   processor inquiry and reconciliation actually work, at the depth a round reaches when you name a
   mechanism and the interviewer asks how it works.

**The coloured boxes:**

::: {.key title="Top-3 number"}
One of the back-of-the-envelope numbers worth computing out loud in the round. In a real interview you
have time for two or three calculations, not ten.
:::

::: why
Explains a term or a decision in plain words. This is for you, not for the interviewer.
:::

> Words you can say in the room, nearly verbatim.

::: warn
A trap: something weak candidates do, or a claim that breaks under a follow-up question.
:::

::: load
What this part of the system sees at peak, with numbers.
:::

**Practise in three passes.** (1) Read Part I and Part II once, end to end. (2) Close the document and
run the [simulator](https://github.com/nirmata78/design-room) cold:
`Read CLAUDE.md. Mock me: SD-44, Amazon, staff, full round.`
(3) Debrief against the Stage 12 self-check, then reread only the sections where you fell short.
**Do not memorise numbers.** Memorise *the order of the argument* and how to rebuild each number in
twenty seconds.

**About the numbers.** The scale figures in Stage 1 are the simulator's cue sheet. Everything derived
from them is back-of-the-envelope arithmetic, and every planning assumption (entries per payment, the
timeout rate, the lock hold time, record sizes) is labelled: *given*, *illustrative*, *initial target* or
*derived*. None of them is a measurement. They are not any company's real figures, and this is not any
company's actual design. Amounts are integer minor units of an unnamed currency; costs are in people and
quarters. **This is not legal, accounting or compliance advice.**

**The prompt as the interviewer reads it:**
*"Design the system that takes a payment and records it: the ledger the company's money is accounted for in."*

::: {.key title="The one-sentence insight to land by minute 10"}
**Exactly-once does not exist across a network boundary.** So the design is at-least-once delivery, an
effect that happens *once per intent*, a state for *"we don't know yet"*, and a *reconciliation* that finds
what the rest missed, all written to an append-only double-entry journal where a balance is a sum, never a
field.
:::

::: why
**Why is this the insight?** The happy path is three boxes and a database. Every interviewer knows that,
so the question is really about the other paths: a bank call that times out and leaves you not knowing
whether the customer paid; a client that retries the same payment three times at once; a refund ninety days
later; a statement that says 999,998 when your books say 1,000,000. A candidate who claims exactly-once, or
who has no reconciliation story because the system is "correct by construction", has missed the core of
the question. A candidate who names what cannot be guaranteed, then designs a mechanism for each point
where the truth arrives, has found it.
:::

\newpage

# Part I: The system in pictures

## Vocabulary you need first

**Where the money moves**

| Term | Plain meaning |
|---|---|
| Merchant | The business taking the payment. Calls our API, receives our webhooks. |
| Processor | The third party that talks to card networks and banks on our behalf. Times out, returns ambiguous answers, goes down. |
| Authorise | Ask the card's bank to reserve the amount. A *hold*, not yet a transfer. |
| Capture | Turn an authorisation into a charge. Often automatic, sometimes days later (hotels, shipping). |
| Void | Cancel an authorisation before capture. |
| Settlement | The processor actually moves the money, in batches, and sends a file listing what it moved. Usually the next day. |
| Refund | Return captured money, wholly or in part. |
| Chargeback | The cardholder disputes the charge with their bank; the money is pulled back, often months later. |

**Where the books live**

| Term | Plain meaning |
|---|---|
| Account | A bucket in the ledger: merchant payable, processor receivable, fee revenue, disputes. |
| Journal transaction | One movement of money: a set of entries whose debits equal its credits. |
| Entry | One line: an account, debit or credit, an amount in integer minor units, a currency. |
| Balance | The sum of an account's entries. Derived, never stored as the truth. |
| Projection | A precomputed balance kept up to date from the entries, a few seconds behind. Rebuildable. |
| Break | A difference between our books and the processor's settlement file, with a type, an owner and an age. |

**Where retries are tamed**

| Term | Plain meaning |
|---|---|
| Idempotency key | A client-chosen string that names one intent. The same key always gets the same result. |
| Our reference | An ID we generate for each attempt at the processor (`payment/attempt`). Lets us ask about it and reverse it. |
| UNKNOWN | A payment state meaning "we sent it and do not know the outcome". A real state, with exits. |
| Outbox | A table of events written in the same transaction as the change they describe. |
| Inquiry | Asking the processor for the status of one of our references. |

## What a payment experiences

Follow one payment, `p-7731`, for 1,050 minor units, from tap to settlement.

1. **10:00:00.000.** The merchant's checkout calls `POST /v1/payments` with idempotency key `k-91`. We insert
   the key as *processing* and create the payment as `AUTH_PENDING` with attempt `p-7731/1`, and commit.
   Nothing has left the building, but there is now evidence that something might.
2. **10:00:00.010.** The adapter sends the authorisation to the processor, carrying reference `p-7731/1`.
3. **10:00:00.350.** The processor approves. In one transaction we move the payment to `CAPTURED` (auto
   capture), post three journal entries, write an outbox row and mark the key *done* with the response.
4. **10:00:00.360.** The merchant gets `201 captured`. A relay reads the outbox row and publishes
   `payment.captured`; the webhook sender posts it, signed, to the merchant.
5. **Next morning.** The processor's settlement file lists `p-7731/1` with a fee. Reconciliation matches it
   against our expectation; the payment moves to `SETTLED`, and settlement entries move the amount from
   *processor receivable* to *bank cash*.
6. **Day 40.** The customer asks for 300 back. A refund is a new transaction referencing `p-7731`.
7. **Day 92.** A dispute arrives for the remainder. A chargeback is another new transaction, dated day 92.
   The month of the original payment, long closed and reported, is never touched.

## The same story as a payment's states

![The payment state machine. UNKNOWN is a real state with exactly two exits: the inquiry says approved, or the processor reports the reference as not found after its safe window. Any transition not drawn is rejected by the code.](diagrams/video-states.pdf){width=96%}

Read the diagram as a contract: the only legal moves are the arrows. `CAPTURED -> AUTHORIZED`, or a capture
on a `DECLINED` payment, cannot happen, because the update that would perform it carries the expected old
state in its `WHERE` clause and finds no row.

## Why the truth arrives over months

![The truth timeline. The client wants an answer in two seconds; the processor's answer comes in about a second or not at all; an inquiry can settle an unknown in minutes; the settlement file arrives next day; a dispute can arrive months later.](diagrams/video-truth.pdf){width=94%}

Every mechanism in this design lives at one point on that line:

| When | What we know | Mechanism |
|---|---|---|
| 2 seconds | approved, declined, or nothing | idempotency key, the UNKNOWN state, the answer *pending* |
| minutes | the processor's answer to our question | the inquiry job, by our reference |
| next day | the processor's books | reconciliation against the settlement file |
| months | a dispute | a new, adjusting transaction, dated now |

No mechanism replaces another. A design with idempotency and no reconciliation has a hole at "next day"; a
design with reconciliation and no UNKNOWN state double-charges at "two seconds".

## One capture as entries

![A capture of 1,050 with a fee of 30. Processor receivable is debited 1,050; merchant payable is credited 1,020; fee revenue is credited 30. Debits equal credits.](diagrams/video-entries.pdf){width=90%}

## Where the load lands

::: load
**At peak (derived in Stage 2):** 10,000 payments a second into the API; about 40,000 journal entries a
second across the ledger partitions; 10 UNKNOWN outcomes a second for the inquiry job; one merchant at
5,000 payments a second against a single account; about 2.9 × 10^8^ settlement lines a day for
reconciliation; the processor taking up to 1.5 seconds of the 2-second budget at its 99th percentile.
:::

![The latency budget: our own work about 90 ms, the processor up to 1,500 ms at p99, 410 ms spare out of 2,000.](diagrams/video-budget.pdf){width=92%}

\newpage

# Part II: The round, stage by stage

**The clock** (a 75-minute round at the simulator's `typing-adjusted` pace; spoken rounds run about 50 minutes):

| Minutes | Stage | On the whiteboard |
|---|---|---|
| 0:00 to 0:12 | **Stage 1** Clarify requirements | Requirements, "never happen" list, out-of-scope box |
| 0:12 to 0:21 | **Stage 2** Back-of-the-envelope (three numbers) | Write rate, hot account, latency budget |
| 0:21 to 0:33 | **Stage 3** API and data model | The pay call, the state machine, the journal tables |
| 0:33 to 0:51 | **Stage 4** High-level design in three versions, with the walk-through | One baseline, redrawn three times |
| 0:51 to 1:13 | **Stage 6** Deep dives, with **Stage 7** requirements as they arrive | Marks on the baseline |
| Last 10 minutes | **Stages 8 and 9** Failure, SLOs, cost | Short list |
| When asked | **Stage 10** The EM layer (auxiliary at Staff) | Releases, teams, one-way doors |

**At the Staff bar you pick the deep dives.** Say which two you would go into and why: *the timeout,
because it is the whole question, and reconciliation, because that is where our books meet the outside.*

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

::: {.key title="The scale line: three numbers every estimate starts from"}
**9 billion payments a month** (290 million a day, 3,300 a second on average) · **peak 10,000 a second** on a sale-day
evening, one merchant at 5,000 a second · **seven years** of balanced entries, about 2.9 × 10¹². Every estimate below says which
of these it starts from. All three are illustrative.
:::

## How to do estimates in this round

Three numbers matter. Compute them aloud, and end each one with the decision it drives.

::: {.key title="Top-3 number 1: the journal write rate"}
**Arithmetic:** 10,000 payments a second × about 4 entries each (receivable, merchant payable, fee, and
sometimes a hold) = **40,000 entries a second** at peak.
**What it means:** one database primary will not take that at peak with multi-row transactions.
**How it changes the design:** partition the journal, and key it by the **owner (the merchant), not the account**: a
capture touches three accounts, so keyed by account every payment would span partitions (see *The partition key*, Stage 5).
**Say:** "Forty thousand entries a second, so the journal is partitioned from the start, and by merchant, so a posting never leaves its partition."
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
| Journal writes | 10,000 × 4 = **40,000 entries/s** | derived | partition by merchant (owner), not by account |
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

![Physical model. Journal entries are hashed by merchant into 64 partitions and only inserted. The payment row is the only mutable row, changed by conditional updates. Idempotency keys keep a request hash and the stored response. The outbox commits with the state.](diagrams/video-erd-physical.pdf){width=96%}

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

![FR1, pay. 1 pay · 2 create · 3 one transaction: key and AUTH_PENDING with attempt · 4 authorise · 5 by reference · 6 approved · 7 status · 8 the answer.](diagrams/video-flow-pay.pdf){width=90%}

![FR2, a refund. The conditional update, the processor refund with a reference made of the payment and the refund key, and a new journal transaction dated now.](diagrams/video-seq-refund.pdf){width=90%}

![FR3, notify. The outbox row commits with the state; the relay publishes; the webhook sender signs and retries; the merchant de-duplicates by event ID.](diagrams/video-seq-outbox.pdf){width=90%}

![FR4, reconcile. The raw file is stored; expectations come from the ledger; matches settle payments; every unmatched line becomes a break owned by finance operations.](diagrams/video-flow-recon.pdf){width=90%}

![FR5, explain. A balance comes from the projection with the entry it is current to; audit sums the entries for the period.](diagrams/video-seq-explain.pdf){width=90%}

## The C4 views and the sequences

![C4 level 1. A customer pays at a merchant; the merchant's system calls us; we call the processor and receive its settlement files; finance operations owns breaks. Two neighbours keep their own books of the same money.](diagrams/video-c4-context.pdf){width=92%}

![C4 level 2. The API owns keys and the deadline; the payment service the state machine and postings; one relational database per partition holds payments, journal and outbox; the adapter owns references and error codes; relay, webhook sender, inquiry job and reconciliation complete the loops.](diagrams/video-base-v3.pdf){width=96%}

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
constraint checked at commit; partitioning by merchant, why not by account, and what a transaction that touches two partitions costs
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

## Technologies, one level down

Every container with the technology it runs on, how it is built, the alternatives rejected and why, and the question an interviewer asks about it. Generated from `stack.json`.

<!-- stack:sections -->

## Ledger database: PostgreSQL, partitioned by merchant

*How it is built.* The key is the owner, the merchant, not the account: a capture touches three accounts and would span partitions. Shared accounts, like fee revenue, exist once per partition and are summed for the company view. A deferred constraint checks that debits equal credits at commit. Unique keys on the idempotency key and on the processor reference. 64 logical partitions are mapped to physical primaries, so a rebalance moves a partition, not rows. Accounts are rows: a million one-time accounts are about 100 MB and change nothing in the layout. TigerBeetle is a purpose-built ledger database (Zig, 128-byte accounts and transfers, thousands of transfers per batch on a single leader, strict serialisability): the fastest at plain debits and credits and a natural upgrade for the ledger core past one primary, but it holds only accounts and transfers, so the state machine, keys and outbox still need a database.

*Why PostgreSQL 16, 64 partitions by merchant, a synchronous standby each:* State, journal and outbox commit together or not at all; a posting never leaves its partition.

*Rejected:*

- **Partitioning by account**: Every capture becomes a cross-partition transaction.
- **TigerBeetle, a ledger database**: Fastest at debits and credits, but state, keys and outbox need a database anyway. The upgrade past one primary.
- **A key-value store, or a log as the truth**: No multi-row transaction, no synchronous refund limit.

*Course:* theory/03 (partitioning).

**Partition key, compared**

| Key | Co-locates | A capture (3 accounts) | A balance read | A hot merchant |
|---|---|---|---|---|
| Account | one account's entries | cross-partition, every time | one partition | one hot row |
| Payment | one payment's entries | one partition | scatter over all | spread, but its balance is a sum of all |
| **Merchant** | everything of one owner | **one partition** | **one partition** | one partition: sub-accounts (challenge 4) |
| Time | the same period | one partition, all writers | scatter | every writer on the newest partition |

## Runtime: Go for the services, and the honest rivals

*How it is built.* The processor takes a second, the commit a few milliseconds, our own code microseconds. So raw speed is not the lever. What matters is a low and flat tail under bursts, memory per replica, a deadline that cancels the whole call chain, and engineers who can run it at three in the morning. Illustrative orders of magnitude from public benchmarks that disagree with each other, so measure on your own load. Service overhead per request: Go 0.1 to 0.5 ms; Java 21+ with virtual threads (Spring Boot or Quarkus) 0.2 to 1 ms warm; Spring WebFlux about the same throughput as virtual threads with much harder code and stack traces, and a JDBC driver blocks anyway; Python async 1 to 3 ms and about a fifth of the per-core throughput under the interpreter lock; Rust 0.05 to 0.3 ms. Memory per instance: Go 30 to 80 MB, JVM 200 to 500 MB, Quarkus native 50 to 100 MB, Python 60 to 150 MB, Rust 10 to 40 MB. Reported comparisons of Go against Java virtual threads range from parity to Go ahead by tens of percent on throughput and several times less memory. Rust pays where microseconds matter, such as a matching engine that never waits on a database, not in a payments service whose time is a bank call and a commit; the cost is hiring and build speed. For a Java team, Java 21+ with virtual threads is an equal choice, and Java 25 removed the main pinning limit.

*Why Go services, one static binary each, context deadlines through every call:* Our share of the two seconds is under a hundred milliseconds and the commit dominates it. Any serious runtime meets that; Go is chosen for small memory, a flat tail and one way to carry a deadline.

*Rejected:*

- **Java 21+ with virtual threads (Spring Boot, Quarkus)**: An equal choice. Within a small factor of Go on throughput, more memory per instance. The right pick for a Java team.
- **Spring WebFlux**: Reactive code to get what virtual threads now give with plain blocking code.
- **Python**: One core per process under the GIL, several times less throughput per core, a fatter tail.
- **Rust**: Fastest and leanest, and not where our time goes. The cost is hiring and build speed.

*Course:* theory/02 (concurrency).

## Outbox relay and log: Debezium into Kafka

*How it is built.* The outbox row commits with the payment. Debezium, in Kafka Connect, reads the write-ahead log through a replication slot and publishes rows to Kafka in commit order, at least once. The risk: a stalled reader makes the database keep log. Alternatives, in the order I would reach for them. A polling relay, SELECT with SKIP LOCKED then mark published: simplest, no Kafka Connect, adds 100 to 500 ms and a query a second; right below about 1,000 events a second. Debezium Server or the embedded engine: the same capture without Kafka Connect, sinking to a cloud queue. Our own consumer of logical decoding with pgoutput: no framework, but we own slot handling, restarts and schema changes. Managed capture such as AWS DMS or Datastream: fine for analytics, weaker ordering guarantees. A database-native queue such as pgmq or River: no Kafka at all, one system fewer. LISTEN and NOTIFY: lossy, never the only path. Publishing after or before the commit: not atomic.

*Why Outbox table, Debezium (change data capture), Kafka:* Reading the write-ahead log costs the database nothing extra and keeps commit order.

*Rejected:*

- **A polling relay**: Right below about 1,000 events a second; here a hot query and 100 ms or more added. It is the alternate path.
- **Own consumer of logical decoding**: We would own slots, restarts and schema changes.
- **Managed capture (DMS, Datastream)**: Built for analytics copies; weaker ordering and replay.

*Course:* theory/06 (messaging).

## Processor adapter: direct processors, with a gateway as another adapter

*How it is built.* The port has authorise, capture, void, refund, inquire and read settlement. Each adapter maps the processor's codes into three classes; only the ambiguous one becomes UNKNOWN. Gateway or direct. A gateway gives one API, tokenisation that keeps card data out of our scope, many payment methods, fraud tools and dispute handling, in days. It costs a blended price, about 2.9 percent plus 30 cents at list for cards, and one more hop. Direct processor or acquirer integration prices interchange plus a margin, about 1.8 to 2.4 percent, but needs card-data compliance at the highest level, underwriting, network certification and months of work. Rough break-even, illustrative: a premium of 0.7 percent against a team and audits of about $80,000 a month is about $10 million of card volume a month. Either way the ledger stays ours: a gateway's balance is not our books, and a timeout to a gateway is still an unknown, found again by the idempotency key it supports.

*Why A Go adapter per processor behind one port: a reference on every call:* The processor is where unknowns are born. Our own reference per attempt lets us ask about it, and reverse it.

*Rejected:*

- **A shared generic client**: The ambiguous class gets lost in the lowest common denominator.
- **A gateway only, at this volume**: About 0.7 % of volume above interchange: tens of millions a year. Right below $10 million a month.
- **Retrying every timeout**: If the first call landed, the retry charges twice.

*Course:* theory/07 (failure).

## Reconciliation: expectations, matched by reference

*How it is built.* The ledger produces, per processor and day, what it expects to be settled, by reference and net of fees. The raw file is stored unchanged, then joined by reference. Matches become settled; everything else becomes a break with a type, an owner and an age. About 290 million lines a day at a million lines a second is five minutes of batch. Break types: missing at the processor, missing here, amount differs, duplicate.

*Why A Spark batch over the processor files, expectations in PostgreSQL, a break workflow with owners:* A report of totals cannot say which line is wrong. A match by reference can.

*Rejected:*

- **Matching on amount and time alone**: Two same-amount payments in a minute are indistinguishable; match by reference.
- **Comparing daily totals**: A matching total can hide two offsetting errors; a differing one does not say which line.

*Course:* theory/08 (batch).

<!-- /stack:sections -->

## The stack on one page

<!-- stack:summary -->

| Container | Choice | Rejected | The deciding reason |
|---|---|---|---|
| Ledger database | PostgreSQL, by merchant | Partition by account; TigerBeetle | A posting stays in one partition |
| Services | Go | Java virtual threads; Rust | Memory, tail and deadlines, not speed |
| Outbox and log | Debezium into Kafka | Polling relay; publish after commit | Commit order, no extra load |
| Processor adapter | Go per processor; gateway too | One generic client; gateway only | Own reference; price at our volume |
| Reconciliation | Spark batch, breaks queue | Match by amount and time; totals | Reference match, owned breaks |

Each fix in Stage 6 rejects one tool by name:

| Deep dive | Rejected | Because |
|---|---|---|
| 6.1 | Treating a timeout as a decline | the bank may have charged; a retry double-charges. |
| 6.2 | Check, then insert, for the idempotency key | two concurrent requests both pass the check; a unique constraint decides. |
| 6.3 | Publishing to the broker after the commit | a crash between the two loses the event for good. |
| 6.4 | One balance row updated on every payment | it serialises the hot merchant on one lock; post journal lines and derive balances. |
| 6.5 | Matching on amount and time alone | two same-amount payments in a minute are indistinguishable; match by reference. |
| 6.6 | Alerting on the error rate | finance finds the break before the dashboard does; measure unmatched count and age. |

<!-- /stack:summary -->

## The partition key: the owner, not the account

The question an interviewer asks about the database is *why this partition key?* A capture posts to three accounts (the
processor receivable, the merchant payable, the fee), and one transaction has to commit all of them.

| Key | Co-locates | A capture (3 accounts) | A balance read | A hot merchant |
|---|---|---|---|---|
| Account | one account's entries | cross-partition, every time | one partition | one hot row |
| Payment | one payment's entries | one partition | scatter over all partitions | spread, but the balance is a sum of all |
| **Merchant** | everything one owner has | **one partition** | **one partition** | one partition: sub-accounts (6.4) |
| Time | the same period | one partition, all writers | scatter | every writer on the newest partition |

By merchant keeps every posting and every balance read inside one partition, at the cost that a hot merchant is a hot
partition, which 6.4 handles. **Shared accounts** (fee revenue, the processor receivable) would be hot and cross-partition, so
each partition has its own, and the company-wide figure is the sum of the mirrors. 64 logical partitions map to about ten
primaries, so a rebalance moves a partition, not rows.

![The same container view, with the type lines naming the technologies.](diagrams/video-c4-containers-tech.pdf){width=100%}

![Inside the payment service: where challenges 1 and 2 happen.](diagrams/video-c4-comp-service.pdf){width=100%}

![Inside one partition of the ledger database: where challenges 3 and 4 happen.](diagrams/video-c4-comp-db.pdf){width=100%}

![Inside reconciliation: where challenge 5 happens.](diagrams/video-c4-comp-rec.pdf){width=100%}

## Gateway or processor: why most companies use a gateway

A **gateway** (Stripe, Adyen, Braintree) is a payment service provider with one API in front of acquirers and networks. A
**processor or acquirer** (Worldpay, Fiserv, a bank) is the party that actually moves card money; integrating with it directly
means a network of contracts and certifications.

| | A gateway | Direct to a processor or acquirer |
|---|---|---|
| Time to first payment | days: one API | months: underwriting, network certification |
| Card-data scope | tokens and hosted fields keep it out of yours (the lightest self-assessment) | the highest compliance level, audited yearly |
| Price (illustrative, list) | about 2.9 % + 30 ¢ blended for cards | interchange plus a margin, about 1.8 to 2.4 % at scale, negotiated |
| You also get | payment methods, 3-D Secure, fraud tools, disputes, payouts, reporting | only what you build |
| Control | their routing; their outage is yours | your routing across several processors |
| Still yours either way | the ledger, idempotency keys, the UNKNOWN state, reconciliation | the same |

**Simpler** (days against months), **cheaper at small volume** (no team, no audits), and **dearer at large volume**, where the
blended premium over interchange is the whole margin. Break-even, illustrative: a 0.7 % premium against a payments team and
audits of about $80,000 a month is about **$10 million of card volume a month**. Large companies run both: a gateway for the
long tail of payment methods, direct processors for the bulk of cards.

**What stays yours with a gateway.** A gateway's balance is not your books: you still keep your own journal, so that you
can explain every figure, reconcile against the gateway's balance transactions and payout reports, and move to a second
provider. A network timeout to a gateway is still an *unknown*: you resolve it by retrieving the payment by the idempotency
key you sent (Stripe accepts one), which is the same inquiry mechanism with a different endpoint. Webhooks from a gateway are
at-least-once and may arrive out of order: de-duplicate by event ID and re-read the object before acting. That is why the
design puts a **processor port** between the payment service and any provider: a gateway is one more adapter.

## Runtime: why Go, and how it compares

Our own code costs microseconds inside a call to a processor that takes a second, and the commit takes a few milliseconds, so
the language is **not** the bottleneck. What matters: a flat tail under bursts, memory per replica (replicas cost money), a
deadline that cancels the whole call chain, and engineers who can run it at 3 a.m.

| Runtime | Overhead per request | Memory per instance | Verdict here |
|---|---|---|---|
| **Go** | 0.1 to 0.5 ms | 30 to 80 MB | the pick: small, flat tail, deadlines in every call |
| Java 21+ with virtual threads (Spring Boot, Quarkus) | 0.2 to 1 ms warm | 200 to 500 MB; Quarkus native 50 to 100 MB | an equal choice for a Java team; plain blocking code scales |
| Spring WebFlux (reactive) | like virtual threads | like virtual threads | not chosen: reactive code for what virtual threads now give, and a JDBC driver blocks anyway |
| Python, async | 1 to 3 ms | 60 to 150 MB | one core per process under the interpreter lock; several times less throughput per core |
| Rust | 0.05 to 0.3 ms | 10 to 40 MB | fastest and leanest; pays in a matching engine, not here; costs hiring and build speed |

*Illustrative orders of magnitude.* Public benchmarks disagree: comparisons of Go against Java virtual threads range from
parity to Go ahead by tens of percent on I/O-bound throughput and several times less memory; virtual threads against WebFlux
trade wins depending on the workload; Java 25 removed the main virtual-thread pinning limit. **Measure on your own load.**
For a latency-critical in-memory component (a crypto exchange's matching engine, which never waits on a database) Rust or C++
is the right tool; a payments service waits on a bank and a commit, so Go, or Java with virtual threads, is enough.

## Building a payment ledger for your own business: the ladder

For a small business, the fastest correct path is a ladder, and you climb only when the number says so:

1. **A gateway (Stripe) and one PostgreSQL primary with your own journal.** Keys first, UNKNOWN, a polled outbox,
   reconciliation against the gateway's balance transactions. Correct from day one, days of work. This is the 5.2 alternate.
2. **A tuned PostgreSQL:** partition by merchant, a synchronous standby, batch inserts. Takes you to thousands of payments a second.
3. **Change capture instead of polling** (Debezium) when events need a replayable log or consumers multiply.
4. **A purpose-built ledger core** (TigerBeetle) for debits and credits when one primary's commit rate or a hot account is the
   limit, with PostgreSQL still holding payment state and the outbox.
5. **Direct processors** when the gateway premium exceeds the cost of a team (about $10 million a month, illustrative).

"The fastest in the world" is a property of one component at one scale, not of the whole system. The slowest part of a
payment is the processor, so the design that wins is the one that is **correct under retry**, then simple to operate.

## 5.2 When you don't need all this (alternate path)

![ALTERNATE: a gateway, one primary, a polled outbox.](diagrams/video-alt.pdf){width=100%}

One adapter (the gateway); one PostgreSQL primary with a synchronous standby; the outbox polled every 200 ms; no Kafka, no
Debezium, no partitions. **It gives up** one writer (about 1,200 commits a second), a replayable log, the gateway's fee premium
and its outages, and, with an asynchronous standby, the lag on failover. **Crossover**, from the scale line: below about
300 payments a second and $10 million a month, ship this and say when you would switch. We are at 10,000 a second and
9 billion a month, so the full design.

# Stage 6: Deep dives

The video runs **six** challenges (the compact cut); this stage keeps **all eight deep dives**, each in the same shape: the risk,
the naive answer and why it fails, the mechanism, the failure case that tests it, what to say, and the weak answers to avoid.
They are ordered so that each fix creates the next question.

| Video challenge | Booklet section | Note |
|---|---|---|
| 1 The bank timed out | 6.1 | the crux, part one |
| 2 Three retries at once | 6.2 | |
| 3 A crash between the ledger and the event | 6.3 | the video adds the replication slot as the new risk |
| 4 The hot merchant, and a million one-time accounts | 6.4 | the video adds the million-accounts push (below) |
| (folded into the refund sequence and challenge 5) | 6.5 Refunds and a chargeback | booklet only |
| 5 999,998 against 1,000,000 | 6.6, with 6.7 as its second push | 6.7 the bad release |
| 6 How would you know before finance does? | 6.8 | |

![The challenge map: the carried baseline with every attack point outlined.](diagrams/video-map.pdf){width=92%}

## 6.1 The bank timed out (the crux, part one)

**The question:** *"You call the processor. It times out. You don't know whether the customer was charged. Walk me
through the next ten minutes, and the next ten days."*

**The naive answers** are "mark it failed and let the client retry" and "retry it ourselves until it works". Both
guess. The first double-charges when the processor in fact approved; the second double-charges when the first
request arrived and only the answer was lost, unless the processor de-duplicates by a reference we control.

| Time | What happens (naive design) |
|---|---|
| 10:00:00.000 | attempt `p-7731/1` sent, 1,050 |
| 10:00:01.900 | client deadline: no answer; marked **failed** |
| 10:00:02.400 | the processor approves `p-7731/1` |
| 10:00:05.000 | checkout retries as `p-7744`: approved |
| 10:00:05.000 | **two holds of 1,050 on one card** |

**The mechanism: UNKNOWN is a state, and an inquiry ends it.**

1. The attempt, with our reference, was **committed before the call**. A crash or a timeout leaves evidence.
2. At the 1.9 s deadline the payment moves to `UNKNOWN`; the client gets `pending`. A retry with the same
   idempotency key gets the same `pending`: it is the same intent.
3. The adapter's call is allowed to continue to the processor's own timeout (often several seconds); a late
   answer still lands, through the same state machine.
4. The **inquiry job** asks the processor for the status of `p-7731/1` after 5 s, 30 s and 2 min, then with backoff.
   *Approved* -> `AUTHORIZED` (or `CAPTURED`), entries, outbox. *Declined* -> `DECLINED`. *Not found after the
   processor's documented safe window* -> `DECLINED`, and only now is a new attempt with a new reference safe.
5. An approval we no longer want (the customer abandoned checkout, the merchant cancelled) is **reversed by the same
   reference**.
6. **Ten days later**, the settlement file is the final arbiter: an approval the inquiry never confirmed appears there,
   becomes a break, and is fixed by an adjusting transaction and a message to the merchant.

![The attack and the fix on the baseline. The inquiry job resolves UNKNOWN payments by our reference.](diagrams/video-ch1-fix.pdf){width=90%}

![The next ten minutes as a sequence.](diagrams/video-seq-timeout.pdf){width=92%}

**Why it works.** S1 holds because no path creates a second movement for one intent: every retry carries the same
key, and every processor call for one unknown attempt carries the same reference. L1 holds because every UNKNOWN has a
bounded exit: the inquiry within minutes, or the settlement file by the next day.

**The second-level push:** *"The inquiry endpoint is down too. Actually, the whole processor is down for an hour."*
A circuit breaker per processor stops new attempts to it. **New** payments may be routed to a second processor if the
contracts allow; an **UNKNOWN** payment must never be sent elsewhere, because that would make two charges possible.
Unknowns wait, age, and show on a dashboard; merchants see `pending`. The honest limit: a processor that supports
neither inquiry nor idempotent references can only be resolved by the settlement file, a day late. That is a reason to
choose processors, and to say so to whoever negotiates contracts.

> "A timeout is an unknown, not a failure. I commit the attempt before calling out, move the payment to unknown,
> answer pending, and an inquiry job asks the processor by our own reference until it knows. Retries carry the same
> reference, so they can't become a second charge, and the settlement file is the final arbiter."

::: warn
**Weak answers.** "We use exactly-once delivery." "We'd use a distributed transaction with the bank." "Retry three
times with backoff." "If it times out we roll back." None of them says what the state is between the timeout and the
truth.
:::

::: why
**What the first draft glosses over: the deadline and the processor's timeout are different numbers.** We answer the
client at 1.9 s, but the processor may answer at 4 s. If the adapter abandons the call at 1.9 s, a late approval is lost
and only inquiry can find it. Keep the call alive to the processor's own timeout, and let a late answer advance the state
machine like any other event, with the conditional update guarding against a race with the inquiry job.
:::

## 6.2 Three retries at once (correctness)

**The question:** *"The client sends the same payment three times, concurrently, with the same idempotency key. Then
once more, same key, different amount."*

**The naive answer** is "check whether the key exists before processing". On three servers, three checks see nothing and
three authorisations go out. A check followed by an act is a race, however fast the check.

**The mechanism: insert first, let the constraint decide.** Insert the key, unique per client, with a hash of the
canonical request, *in the same transaction* that creates the payment. One insert wins. The others fail the constraint
and read the row: `processing` -> 409, retry later; `done` -> the stored response; a different hash -> 422, nothing
executed.

```python
def insert_or_get(client, key, req_hash, create):
    with db.transaction():
        try:
            db.insert("idempotency", client, key, req_hash, status="processing")
            return New(create())                 # the payment, same transaction
        except UniqueViolation:
            row = db.get("idempotency", client, key)
    if row.req_hash != req_hash: return Error(422, "key reused")
    if row.status == "processing": return Error(409, "in progress")
    return Stored(row.response)
```

![One wins; the others read.](diagrams/video-seq-idem.pdf){width=90%}

**Why it works.** S1 is decided by the database's unique constraint: the one place every request must pass. The
result is returned, not re-executed. A changed request under an old key is a client bug, so it is reported, not hidden.

**The second-level push:** *"The server that won crashes after the processor approved, but before it wrote done."*
The rows say exactly how far it got: the key is `processing` with the payment ID; the payment is `AUTH_PENDING` with the
attempt's reference. That is an unknown outcome, and 6.1 already handles it. A sweeper sends any `processing` row older
than a minute to recovery.

**Retention.** Keys live seven days (illustrative). The API contract says a retry after that is a new payment. Shorter
retention saves storage and breaks clients with long retry queues; say who decides.

> "The idempotency key is inserted first, with a unique constraint, in the same transaction that creates the payment.
> One request wins; the others get 'in progress' or the stored answer. A different body under the same key is a client
> bug, so I reject it instead of hiding it. And a crash in the middle is just an unknown outcome, which I already handle."

::: why
**Hashing the request.** Hash a canonical form (sorted fields, normalised amounts), not the raw bytes, or a client that
reorders JSON fields gets a 422 for an identical request. Exclude fields that legitimately vary between retries, such as
a client timestamp, or document that they must not vary.
:::

## 6.3 A crash between the ledger and the event (failure recovery)

**The question:** *"Your service commits the payment, then crashes before telling the merchant. What state are you in?"*

**The naive answer** is "publish right after commit; crashes are rare". At 10,000 payments a second, rare is several a
day. Commit-then-publish loses events (a customer charged, nothing shipped); publish-then-commit invents them (goods
shipped for an unpaid order).

**The mechanism: the transactional outbox.** The event is a row in the same transaction as the state and the entries. A
relay reads committed rows in order and publishes them, at least once; consumers and merchants de-duplicate by event ID.

![Nothing is lost at the crash.](diagrams/video-seq-outbox.pdf){width=92%}

**The second-level push:** *"The relay is twenty minutes behind. Or a merchant's endpoint is down for a day."* Outbox age
is a metric with an alert. The relay publishes keyed by merchant, so one slow partition does not hold the others. Webhooks
retry with backoff for days, then the merchant is told to reconcile with `GET`; the merchant dashboard reads our database,
not the stream.

> "I never write to two systems and hope. The event is a row in the same transaction as the state change, and a relay
> publishes it at least once. Consumers de-duplicate by event ID, and the merchant can always ask us for the state directly."

::: why
**Ordering.** Events for one payment must arrive in order (`authorized` before `captured`), or a consumer must tolerate
disorder by applying only legal state transitions. The relay preserves order per partition; across partitions there is no
order, so consumers should key their state by payment and ignore an event that would move it backwards.
:::

## 6.4 The hot merchant (overload)

**The question:** *"One merchant receives five thousand payments a second. Where does that land?"*

**The naive answer** updates the merchant's balance inside each payment's transaction. Every transaction takes the same row
lock: about 670 a second at 1.5 ms each, against 5,000 arriving. The queue grows by 4,330 a second; within a second the
merchant's payments pass 2 s and start timing out, becoming UNKNOWNs: this challenge feeds 6.1.

![One balance row against one merchant's payment rate. Illustrative lock time; the ratio is the point.](diagrams/video-hot.pdf){width=90%}

**The mechanism: append; derive; serialise only what must be serial.** Payments insert only their own entries: no shared
row. A projection updates balances a few seconds behind, which is fine for dashboards. Where a check needs a current
balance (a payout must not exceed available funds): split the merchant's payable account into 16 sub-accounts that take
writes in turn (16 × 670 about 10,700 a second of capacity, twice this merchant's peak), or send the rare checked operation
through **one writer per merchant**.

**The second-level push:** *"A refund needs refunded at most captured, per payment. A payout needs paid out at most
available, now."* Per payment: a conditional update on the payment row; one payment is never hot. Per merchant: the single
payout writer sums the sub-accounts and posts the payout. Payouts are rare next to payments, so serialising them costs
nothing. The honest limit: the projection lag must be measured and stated to the payouts team.

**The second-level push in the video: "a million one-time virtual cards a day, none ever hot. Do you partition by account now?"**
No. An account is a **row**, not a partition: a million accounts at about 100 bytes is 100 MB, created by an upsert on first
posting. They hash with their merchant, so they spread evenly, and a posting between a card and its funding account stays in
one partition. Partitioning by account would solve a problem we do not have (cold accounts) and bring back the one we avoided
(every posting spanning partitions). Three further points:

1. **Does the card need a ledger account at all?** A card is an *instrument*. Its spending limit is a hold in authorisation
   (SD-77). The ledger needs accounts for *who owes whom*: the program's or the customer's, with the card ID as a tag on the
   entries. One-time accounts that never carry a balance are rows nobody reads.
2. **The cross-partition case is real, and rare:** a funding account shared by many merchants. Post it in two steps, a
   pending debit on one side and a confirmation on the other, or give each merchant a mirror account and settle the mirrors in
   a batch.
3. **Housekeeping:** close and archive accounts with zero balance and no activity; keep the account table small enough to cache.

**Past one primary: a purpose-built ledger database.** TigerBeetle (written in Zig) is built for exactly debits and credits:
128-byte accounts and transfers, thousands of transfers in one batched request on a single leader, strict serialisability,
and a flag that makes an account refuse to go below zero. A hot account is not a lock there, because the engine applies a
batch in order on one core. It is the natural upgrade for the *ledger core* of a very large or very hot system, and it is
only the core: payment state, idempotency keys, the outbox and the break workflow still need a general database. Published
throughput figures are vendor-reported and workload-dependent, so measure your own; and weigh a younger system's operational
maturity against the speed.

> "Five thousand updates a second to one balance row would serialise on its lock. So payments only append entries and the
> balance is derived. Where a check needs the balance now, like a payout, I split the account into sub-accounts or serialise
> just that rare operation through one writer."

## 6.5 Refunds, and a chargeback months later (correctness, late events)

**The question:** *"A payment was partially refunded twice. Two more refunds arrive at once. Then, three months later, a
chargeback."*

| Time | What happens (naive design) |
|---|---|
| day 1 | `p-5520` captured 10,000 |
| days 3 and 9 | refunds of 3,000 and 4,000: refunded = 7,000 |
| day 12, +0 ms | refund 2,500 reads 7,000; 9,500 is within 10,000: ok |
| day 12, +2 ms | refund 2,500 reads 7,000; 9,500 is within 10,000: ok |
| day 12 | **12,000 refunded on a 10,000 payment** |
| day 92 | chargeback for the rest; **month 1 is closed and reported** |

**The mechanism.** Each adjustment is a new journal transaction referencing the payment. The limit is one conditional
update on the payment row, so exactly one of two racing refunds changes a row. A chargeback posts entries **dated now**, to
a disputes account, referencing the payment; the closed month is never touched.

![One refund wins; the month stays closed.](diagrams/video-seq-refund.pdf){width=90%}

**The second-level push:** *"The merchant wins the dispute. Or the refund is in another currency."* A won dispute is one
more transaction from the disputes account back to the merchant. Amounts stay in the original currency; a conversion is its
own transaction with the rate it used. Who bears a dispute loss is a contract, owned by finance, not by code.

> "Nothing is edited. A refund, a chargeback or a reversal is a new balanced transaction that references the payment and is
> dated when it happened, so closed months still add up. The refund limit is one conditional update on the payment row, so
> two concurrent refunds can't both pass."

::: why
**Ordering the refund and the processor call.** Reserve the refund amount with the conditional update *before* calling the
processor, in the same transaction as a refund row in state `pending`. If the processor declines, release the reservation
with a compensating update. Calling first and reserving after allows two refunds to reach the processor before either is
counted.
:::

## 6.6 999,998 against 1,000,000 (the crux, part two)

**The question:** *"The processor's statement says 999,998. Your books say 1,000,000. What now?"*

**The naive answer** is "we'd look into it; our system is correct by construction". Correct inside our database is not the
same as agreeing with the party that moved the money.

| Line | Ours | Theirs | Kind |
|---|---|---|---|
| Capture booked at 23:58, settles tomorrow | 1,050 | — | timing: closes by itself |
| An UNKNOWN we resolved as declined | — | 1,050 | **real: the customer paid** |
| A fee 2 higher than the contract | 30 | 32 | real: the processor's error |
| **Net** | | **−2** | |

The totals differ by 2, but there are three breaks, and the one that matters most, a real charge we believe was declined,
is invisible in the total. That is why reconciliation is never done on totals.

**The mechanism: expectations, matched line by line, every break owned.** Store the raw file unchanged. The ledger generates
expectations: what each processor should settle, by reference, net of fees. Match line by line on reference, amount and fee.
Matched lines move payments to `SETTLED` with settlement entries. Every unmatched line is a break with a type (missing on
their side, missing on ours, amount, timing), an owner and an age. Timing breaks close themselves when the next file matches;
real breaks get an adjusting transaction with a reason.

![From the file to an owned break.](diagrams/video-seq-recon.pdf){width=92%}

**The second-level push:** *"Forty thousand breaks this morning, not forty."* That is an incident, not a backlog. Classify by
type and processor first: one cause usually explains thousands of lines. Hold payouts if the break amount crosses a threshold.
Fix the cause, then the lines. Breaks by age is a dashboard with a target, and finance operations is a team with tooling.

> "Reconciliation isn't a safety net for a buggy system; it's a permanent component, because the processor's truth and ours
> diverge even when our code is right. I match line by line against expectations from the ledger, every difference becomes a
> break with an owner and an age, and a spike in breaks is treated as an incident."

::: why
**Three-way, not two-way.** A complete reconciliation compares three sources: our ledger, the processor's settlement file,
and the bank statement showing the cash that actually arrived. The processor can agree with us and still pay out short. The
video draws the two-way match; say the third leg exists.
:::

## 6.7 A bug double-posted forty thousand entries (failure recovery; the EM half)

**The question:** *"A bug double-posted forty thousand entries last night, and some merchants have already been paid out."*

| Time | What happened |
|---|---|
| 22:10 | release 2026.11.19 starts posting the fee leg twice |
| 23:40 | 40,000 captures affected; 1,200 merchants' payables too high by the fee |
| 00:00 | nightly payouts: 180 of them paid the excess |
| 07:30 | reconciliation's fee breaks jump; incident opened |

**The naive answer** is "a script to delete the duplicates". A `DELETE` destroys the evidence, breaks S3, and does nothing
about money already paid out.

**The mechanism: stop, identify, reverse, recover, learn.**

1. **Stop:** switch the release off; **hold payouts** for the affected merchants (money not yet sent can still be protected).
2. **Identify:** the journal is immutable, so the duplicates are exactly the payments with two fee transactions.
3. **Reverse:** one reversing transaction per duplicate, tagged with the incident ID. The audit trail shows the error and the
   correction.
4. **Recover:** for the 180 already paid, a receivable from the merchant, recovered from future settlements, with a message to
   each. A business decision with communication, not a database operation.
5. **Learn:** why did idempotency not catch it?

![The correction, step by step.](diagrams/video-seq-correct.pdf){width=90%}

**Why idempotency did not catch it:** it guards *requests*, not code paths. There was one request with one key; the bug posted
twice inside it, with a new transaction ID each time. The invariant that stops the class is a unique constraint on
`(payment_id, type)` for single-occurrence types such as the fee, plus an hourly reconciliation check that would have flagged it
at 23:00.

> "Stop the bleeding first: kill the release and hold payouts. Because the journal is immutable I can find the duplicates
> exactly and post reversing entries tagged with the incident, so the audit trail shows both. Money already paid out is a
> receivable and a conversation with those merchants. Then a constraint and an hourly check, so this class can't repeat silently."

## 6.8 How would you know before finance does? (observability)

**The question:** *"What do you watch, and what alert fires before finance notices?"*

**The naive answer** is "API error rate and latency". A decline is a successful API call. At 02:00 one processor declines six
more points of cards from one country; errors are zero, latency normal, every dashboard green; at 09:00 merchants report sales
are down.

**The mechanism: watch the money and the truth.**

| SLI | How it is measured | Alert |
|---|---|---|
| Approval rate per processor, country, card type | against its own baseline (same hour last week) | a drop of several points |
| UNKNOWN count and age | from the payment table | oldest above 15 min |
| Outbox age | oldest unpublished row | above 1 min |
| Ledger balance | Σ debits − Σ credits per currency, continuously | any non-zero value pages immediately |
| Unreconciled amount by age | from the break table | above a threshold at 1 day |
| End-to-end success | a synthetic payment per processor every minute, test card | any failure twice |

**Symptom pairs**: two metrics, one conclusion.

| Metric A | Metric B | Conclusion |
|---|---|---|
| approvals down | latency normal | a processor or issuer change, not us |
| UNKNOWN up | latency at the timeout | the processor is slow |
| outbox age up | commits normal | the relay is stuck |
| breaks up today | UNKNOWN up yesterday | the inquiry is not resolving |
| debits − credits non-zero | anything | stop and page: a posting bug |

![The probe, end to end.](diagrams/video-seq-probe.pdf){width=88%}

**The second-level push:** *"The approval rate drops slowly: half a point a week."* Compare weekly, per segment, against a
seasonal baseline; give approval rate an owner in payments operations who reviews it with the processor every week.

> "I watch the money, not the servers: approval rate per processor and segment against its baseline, the count and age of
> unknown outcomes, outbox age, unreconciled amount by age, and a continuous check that the ledger sums to zero, which pages
> immediately. Then I read metrics in pairs to tell 'the processor changed' from 'we broke'."

## 6.9 How the whole system degrades, in priority order

When something gives, it should give in this order, matching the "never happen" list from Stage 1:

1. **Correctness is never traded.** No path posts an unbalanced transaction or moves money twice.
2. **Answers become `pending`** before they become wrong: a slow processor turns answers into UNKNOWN, not into guesses.
3. **New payments fail over** to a second processor; unknown ones never do.
4. **Notifications lag** (outbox age grows) before payments stop.
5. **Projections lag** (dashboards a few minutes old) before postings slow.
6. **Payouts are held** before money leaves on a wrong balance.

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

\newpage

# Part III: The internals

## Appendix A: Double-entry bookkeeping, in plain words

Every movement of money takes it *from* somewhere and puts it *somewhere*. Double entry writes both sides. Each account has a
normal side: assets (what we are owed, cash) increase with a debit; liabilities (what we owe merchants) and revenue increase
with a credit. A journal transaction is valid only if its debits equal its credits, per currency. That single rule makes three
things true at once: no money is created or destroyed by our code; every balance can be recomputed from the entries; and an
error shows up as an imbalance somewhere, rather than as a silently wrong number.

**Why a balance column fails.** A balance updated in place is a number with no history. When it is wrong, nothing tells you
why. When two transactions update it at once, one waits for the other's lock. A derived balance has neither problem: it is
the sum of entries that never change, and a projection can be rebuilt from them at any time.

**Integer minor units.** 10.50 is stored as 1050 with a currency whose minor-unit exponent is 2. Some currencies have 0 or 3
minor digits, so the exponent comes from the currency, never from the code. Rounding happens once, at a stated point (for
example, when a percentage fee is computed), with a stated rule, and the rounding difference is posted to an account rather
than lost.

**Closed periods.** Accounting closes a month and reports it. An adjustment that belongs to a closed month is posted in the
current month with a reference to the original. The closed month still adds up, and the correction is visible as a correction.

## Appendix B: Idempotency keys

An idempotency key names an *intent*, chosen by the client, so that every retry of that intent is recognisable. The server's
duties:

1. **Insert, do not check.** The key is inserted with a unique constraint in the same transaction as the effect. The database
   resolves concurrent retries; the application never does.
2. **Store the result.** The final response is stored on the key's row, so a retry returns it without re-executing anything.
3. **Bind the key to the request.** A hash of the canonical request is stored; a different request under the same key is
   rejected (422), because it is a client bug that would otherwise be hidden or double-charged.
4. **Report in-flight state.** A retry that arrives while the first is still running gets 409, not a second execution.
5. **Publish the retention.** Keys expire after a stated window; a retry after it is a new intent. This is part of the API
   contract, and a one-way door.

**Downstream idempotency** is the same idea one hop further: our call to the processor carries our own reference, so the
processor can de-duplicate our retries and answer inquiries about them. The reference is per *attempt*: the same while the
outcome is unknown, new only after a definite failure.

## Appendix C: The transactional outbox

The problem: a database commit and a message publish are two writes to two systems, and no shared transaction covers both. The
outbox puts the message *in the database*, in the same transaction as the change. A relay then moves committed outbox rows to
the message system:

- **Polling relay:** `SELECT ... FROM outbox WHERE id > :last ORDER BY id LIMIT 500`, publish, record `:last`, delete or mark
  sent. Simple; adds a little latency; watch for gaps when transactions commit out of id order (read only rows older than a
  small safety margin, or use a commit-ordered sequence).
- **Change-data-capture relay:** read the database's own commit log and publish outbox inserts in commit order. Lower latency;
  more moving parts.

Either way delivery is **at least once**: a relay that crashes after publishing and before recording progress publishes again.
Consumers de-duplicate by event ID, and merchants are told so in the webhook documentation.

## Appendix D: Processor inquiry and reversal

A processor typically offers some of: an idempotency key or merchant reference on requests; a status lookup by that reference;
a reversal (void) of an authorisation by reference; and a daily settlement file. The adapter for each processor records which
it supports and what its *safe window* is: how long after a request a "not found" can be trusted to mean it never arrived. The
inquiry job:

1. selects UNKNOWN payments in age order;
2. asks the processor about each attempt's reference, within the processor's rate limit;
3. applies the answer through the same state machine (conditional update from UNKNOWN);
4. reverses approvals that are no longer wanted;
5. leaves anything still unknown for the settlement file, and reports it by age.

When a processor supports none of this, the settlement file is the only arbiter, and UNKNOWNs last a day. That is a selection
criterion for processors.

## Appendix E: Reconciliation

**Inputs:** the processor's settlement file (stored raw, unchanged, with a checksum); the ledger's **expectations** for the
same period (every capture, refund and fee we believe the processor will settle, by reference); and, for the third leg, the
bank statement of cash received.

**Matching:** by reference first; then by amount and fee; with a tolerance only where a documented rounding rule allows one.
Output three sets: matched (post settlement entries, move payments to `SETTLED`), timing (expected tomorrow; auto-close when it
matches), and breaks.

**Breaks:** each has a type (missing on their side, missing on ours, amount, fee, duplicate), an owner, an age and a resolution
(an adjusting transaction with a reason, a claim against the processor, or a write-off with approval). Breaks by age is a
dashboard with a target. A sudden spike is classified by type and processor before anyone works individual lines.

## Appendix F: Sub-accounts for hot accounts

Split account A into A~1~ ... A~16~. Each posting picks one (round-robin, or by a hash of the payment ID). Balance(A) = Σ
balance(A~i~). Writes no longer contend on one row. A check that needs the current balance either sums the sub-accounts inside
one transaction (16 reads) or goes through one writer per merchant that serialises the rare operation. The number of
sub-accounts is the peak rate divided by one row's capacity, with headroom: 5,000 ÷ 670 about 7.5, so 16.

\newpage

# One-page cheat card

**Insight.** Exactly-once does not exist across the boundary: at-least-once delivery, one effect per intent, a state for not
knowing, reconciliation, on an immutable double-entry journal.

**Numbers.** 10,000 payments/s -> 40,000 entries/s. 2.9 × 10^8^ payments/day. 580 TB over 7 years. Hot merchant 5,000/s against
about 670/s per row lock. Budget: ours about 90 ms, processor at most 1.5 s, 410 ms spare. 10 UNKNOWNs/s at peak.

**API.** Idempotency key inserted first (409 in progress, 422 reused). Integer minor units plus currency. `pending` is an answer.
Signed webhooks with event IDs, plus `GET` as backstop.

**States.** CREATED -> AUTH_PENDING -> AUTHORIZED / DECLINED / **UNKNOWN** -> CAPTURED -> SETTLED; refunds and chargebacks as new
transactions. Legal edges only, by conditional update.

**Pay path.** Commit the attempt before the call -> call by reference with a 1.9 s deadline -> one transaction: state, entries,
outbox, key done.

**Eight challenges.** Timeout (UNKNOWN + inquiry) · three retries (insert first) · crash before event (outbox) · hot merchant
(append, sub-accounts) · refunds and chargebacks (new transactions, conditional limit) · 999,998 (line-by-line reconciliation) ·
double-posted entries (stop, reverse, recover) · observability (approval rate, UNKNOWN age, zero-sum page, symptom pairs).

**Traps.** Distributed transaction with the bank. Balance column. Timeout = failed. Floats. Check-then-insert. Publish after commit.
Editing history. Reconciling totals. Failing over an UNKNOWN.

**One-way doors.** The ledger schema and the idempotency contract.

*The technical content of this document is the model's reasoning; it has not been reviewed by a person. Numbers are illustrative
and are not any company's figures.*
