
# Stage 1: Clarify requirements

Open with questions, not boxes. Each question below has the cue sheet's answer and what it changes. Ask
them in one burst, write the answers down, and say the consequence of each one aloud: that is what turns
a list of questions into a scoping argument.

| # | Question | Answer (cue sheet) | What it changes |
|---|---|---|---|
| 1 | How big is the portfolio? | 5M active loans, 3–12 monthly instalments | ~5M collections a month; loans live up to a year, long enough for every slow failure |
| 2 | Which rails? | Bank debit 80 %, card 20 %; card numbers are tokens at the processor | Two rails with opposite behaviour; tokens mean no quick failover between processors |
| 3 | When are payments due? | They cluster: 600,000 on the 1st | One day must be planned; size it before reacting to it |
| 4 | What limits do the rails impose? | Card contract 100/s; bank debit files have a daily cut-off (take 14:00) | The binding limits are outside the system |
| 5 | Refunds? | Merchants refund fully or partly, any time | Schedules change under live loans; the terms must say how |
| 6 | Audit and close? | Every cent explained 7 years; month-end close in 2 days | Immutable lines; differences found daily, not at month-end |
| 7 | What must never happen, in order? | Your call | Propose: charge twice; an unexplained cent; a penalty for our failure; then lateness |

::: why
**Why ask "what must never happen, in order?"** Because the answer settles every later trade-off in one
sentence. When the interviewer later asks "the processor is slow, do you retry or wait?", you can point to
the order: a double charge is worse than a late collection, so you wait and ask. Candidates who never set
the order end up arguing each trade-off from scratch.
:::

**Functional requirements**, numbered, because each gets a flow in Stage 4:

- **FR1 Schedule.** A booked loan becomes a schedule of instalments from its terms version.
- **FR2 Collect.** On each due date, collect by bank debit or card; retries and late fees follow policy.
- **FR3 Adjust.** Merchant refunds, extra payments and early payoff; re-amortise or shorten per the terms;
  every payment allocated by a versioned waterfall.
- **FR4 Absorb returns.** A debit returned days or weeks later reverses a collection and puts the instalment
  back to due.
- **FR5 Reconcile.** Ledger against processor against bank, every day; month-end close in two days.

**Non-functional requirements**, all *initial targets*:

| Promise | Target |
|---|---|
| Customers charged twice for one instalment | 0 |
| Unexplained differences at month-end close | 0 |
| Debit file submitted (cut-off 14:00) | by 10:30, acknowledged by 11:00 |
| UNKNOWN card outcomes resolved | 99 % within 1 hour |
| Retention | every line kept and explainable for 7 years |
| Close | 2 days after month-end |

**In scope:** schedules and terms versions; both rails with retries and returns; refunds, late fees and
payoff; the ledger; reconciliation; customer notices as events.
**Out of scope, said aloud:** origination and underwriting (SD-82); outside collections agencies and hardship
programmes beyond a pause flag; statement design; tax reporting; payouts to merchants (SD-81); funding or
selling the loans.

> "The core is four things: a ledger that is never edited, a payment state machine with unknown and returned,
> a scheduler bounded by the rail, and reconciliation against the outside. Everything else serves those four."

::: warn
**Trap: treating the prompt's silence as "no requirement".** The prompt does not mention returns. A candidate
who does not ask how a bank debit fails will design a system in which settled means paid, and will lose the
second half of the round to Challenge 3.
:::

# Stage 2: Back-of-the-envelope

## How to do estimates in this round

Three calculations are worth doing aloud; the rest go in the table. Each ends with a decision.

::: {.key title="Top-3 number 1: the busy day is 42 a second"}
**Arithmetic:** 600,000 collections ÷ (4 h × 3,600 s) = about **42 per second**. *Derived from a given.*
**What it means:** one relational primary handles thousands of small transactions a second.
**Decision:** the database is the work queue; a message broker is not needed for load.
**Say:** "Six hundred thousand sounds like a herd, but it's forty-two a second. The database is fine. The
limits are elsewhere."
:::

::: {.key title="Top-3 number 2: the card window is 22 minutes"}
**Arithmetic:** 600,000 × 20 % = 120,000 card charges; ÷ 100/s = 1,200 s = **20 minutes** at the contract
limit; at 90 % of the contract, = about **22 minutes**. *Derived; 90 % is an initial target.*
**Decision:** a token bucket per rail set below the contract, and a day plan with a card window.
**Say:** "The processor's contract sets the pace, so I plan the window, I don't burst into it."
:::

::: {.key title="Top-3 number 3: ninety million dollars on one morning"}
**Arithmetic:** 600,000 × $150 average instalment = about **$90M**; a 0.1 % error = about **$90k**. *Illustrative
average.*
**Decision:** correctness beats speed; a day's delay is cheap, an error is not.
**Say:** "Being late costs a little. Being wrong by a tenth of a percent costs ninety thousand dollars."
:::

## The full table, row by row

| Number | Arithmetic | Label | Decision it drives |
|---|---|---|---|
| Busy-day rate | 600,000 ÷ 14,400 s = about 42/s | derived | DB as the queue |
| Card charges | 600,000 × 20 % = 120,000 | derived | — |
| Card window | 120,000 ÷ 90/s = about 1,333 s = about 22 min | derived | token bucket, day plan |
| Bank debits | 600,000 × 80 % = 480,000 | derived | one file |
| File size | 480,000 × 94 B = about 45 MB | illustrative record size | build early, validate, wait for the acknowledgement |
| Money on the 1st | 600,000 × $150 = about $90M | illustrative | correctness over speed |
| Returns | 480,000 × 3 % = about 14,400 on days 2–3 | illustrative rate | a return pipeline with an owner |
| Card timeouts | 120,000 × 0.2 % = about 240 | illustrative rate | a resolver service |
| Ledger lines a month | 5M × 4 = 2 × 10^7 | illustrative lines per loan | — |
| Seven years | 2 × 10^7 × 84 × 200 B = about 336 GB = about 340 GB | derived | one relational DB, partitioned by month, no sharding |
| Daily accrual lines (rejected) | 5M × 30 × 2 = 3 × 10^8 a month | derived | accrue by calculation; post at events and month-end |

::: why
**Why "four lines per loan per month"?** Two for the collection itself (cash clearing against the loan's
principal). The move from clearing to cash at settlement happens on system accounts, posted once per
settlement batch rather than once per loan, so it adds little. Two more for the interest accrued at
month-end, on loans that carry interest. Refunds, fees and returns add lines, but rarely. The point of the
estimate is the order of magnitude: hundreds of
gigabytes over seven years, not petabytes, which is why a single relational database with real constraints
is the right home for the ledger.
:::

::: warn
**Trap: posting interest every day.** It feels accurate, and it multiplies the ledger by fifteen. Accrual is a
calculation from the balance, the rate and the days elapsed; it is *posted* when something happens (a
payment, a payoff, a refund) and at month-end. The posted amount is exactly what the calculation gives, so
nothing is lost.
:::

# Stage 3: API and data

## The API

Every call carries a tag: the requirement it serves and the entity it reads or writes.

**`LoanBooked` (event from origination) · FR1 · writes Loan, ScheduleVersion, Instalment, LedgerTxn.**

```text
LoanBooked {
  loanId: "ln-5531", principalCents: 120000,
  termsVersion: "bnpl-8m-v3", firstDue: "2026-12-01",
  rail: "bank_debit", mandateId: "md-204" }
```

Idempotent by `loanId`: a duplicate delivery creates nothing. Due dates are moved to business days, because
a bank debit cannot take effect on a weekend or bank holiday.

**`POST /loans/{id}/payments` · FR2, FR3 · writes Intent, LedgerTxn.** A customer payment (an instalment paid
early, or an extra payment), with an `Idempotency-Key` header.

**`POST /loans/{id}/refunds` · FR3 · writes LedgerTxn, ScheduleVersion.** From the merchant. The merchant's own
`merchantRefundId` is the idempotency key, so a merchant retry cannot refund twice.

**`GET /loans/{id}/payoff-quote` · FR3 · reads Balance and in-flight Intents.**

```text
-> { quoteId: "q-31", amountCents: 75000,
     inFlight: [ { kind: "bank_debit", amountCents: 15000 } ],
     validUntil: "2026-12-05" }
```

Paying it uses `quoteId` as the idempotency key. The `inFlight` list is the subject of Challenge 5.

**Rail calls · FR2, FR4, FR5.** Card: `Charge(token, amount, key)` and `Query(key)`, where the key is
`coll:<loan>:<instalment>:<attempt>`. Bank: `SubmitDebitFile(batch)` returning an acknowledgement,
`ImportReturns(file)`, `ImportSettlement(file)`, `ImportStatement(file)`. Every file is stored unchanged
before anything parses it.

**Operations · FR5.** `GET /breaks?age>1d`, and `PUT /rails/{rail}/pause` (the rail switch).

::: why
**Why is the attempt number in the key?** Because a key identifies a *decision to collect*, not an
instalment. Resending the same attempt after a timeout must reuse the key, so the processor returns the
first result instead of charging again. But after a *definite decline*, trying again is a new decision, and
needs a new key, or the processor would return the old decline forever. The rule is: same attempt, same
key; new attempt only after a definite answer.
:::

## The data model

![Conceptual model in Chen notation. A loan has schedule versions; a version contains instalments; an instalment is collected by intents, at most one open at a time; a loan posts ledger transactions, each containing lines; an intent posts the transactions for its result.](diagrams/video-erd-chen.pdf){width=96%}

![Physical model. Ledger lines are partitioned by month and only inserted. Ledger transactions carry a unique idempotency key and the policy version used. The balance row has a version and is updated in the same commit. Due items are indexed by date, shard and status: the work queue. Payment intents have a partial unique index: one open intent per instalment.](diagrams/video-erd-physical.pdf){width=96%}

| Table | Changes? | Lose it? |
|---|---|---|
| `ledger_line` | insert only | never: it is the book of record |
| `ledger_txn` | insert only | never |
| `account_balance` | updated in the same commit, at a version | rebuildable from lines |
| `due_item` | status changes (DUE, CLAIMED, DONE) | rebuildable from schedule versions |
| `payment_intent` | state machine transitions | never: it is the evidence of what was attempted |
| `outbox` | inserted with the state, deleted after publish | republished at least once |
| raw files | stored once | never: the replay source for ingest |

**The posting transaction:**

```sql
BEGIN;
INSERT INTO ledger_txn (id, idem_key, kind, policy_ver)
  VALUES ('tx-9', 'coll:ln-5531:2:1', 'COLLECTION', 'v3');   -- unique key
INSERT INTO ledger_line (txn_id, account, amount_cents) VALUES
  ('tx-9', 'cash_clearing',            15000),
  ('tx-9', 'loan:ln-5531:principal',  -15000);
UPDATE account_balance
   SET balance_cents = balance_cents - 15000, version = version + 1
 WHERE account = 'loan:ln-5531:principal' AND version = 41;
COMMIT;   -- a deferred check rejects it unless the lines sum to zero
```

> "Lines are facts and never change. The balance is a projection, updated in the same commit, and provable
> from the lines."

### One race the first draft glosses over: the version check

If the `UPDATE ... AND version = 41` touches zero rows, another posting to the same loan committed first.
The transaction must roll back and be retried from a fresh read, *with the same idempotency key*. If the
first attempt actually committed (the client lost the commit acknowledgement), the retry fails at the unique
key and returns the stored result. Run the listing in your head against both cases: a concurrent posting,
and a duplicate. It handles both, because the key insert comes first.

### One more: the deferred zero-sum check

A check that lines sum to zero cannot run on each row insert, because the first line of a transaction never
sums to zero on its own. It runs at commit (a deferred constraint trigger, or a check in the single posting
function that every writer must use). Prefer both: the posting function refuses to build an unbalanced
transaction, and the database refuses to commit one.

**Three rules about money and dates.** Never a float: integer cents, and the rounding of instalments is a rule
(the remainder on the last one). Business days: a due date on a weekend or bank holiday takes effect the next
business day, and late fees count from there. Two dates on every line: the effective date and the booking
date, so a return that arrives today never edits last month.

# Stage 4: High-level design

Build the design in three versions, each introduced by the objection to the one before. The boxes never move:
every later picture is a view of the same baseline.

## Version 1: the simplest thing that works

![V1. Origination books loans through the servicing API. At midnight a job in the schedule service charges everyone due today at the rails and updates a balance column in the loans database.](diagrams/video-base-v1.pdf){width=92%}

The objection, as a trace: at 00:00:00 the job sends 2,000 card charges a second against a contract of 100; at
00:00:03 the processor throttles 95 % and the job retries at once; at 08:00:10 one charge times out and is
retried as new, and the customer is charged twice; on Dec 3 a debit returns, and the balance column was
already reduced, so there is nowhere to post it; at year end an auditor asks why a balance is 75,000 and there
is no history.

## Version 2: one collection per instalment, at the rail's pace, with books

![V2. The servicing database holds the ledger with projections, due items, payment intents and an outbox. The schedule service claims due items and writes intents and outbox rows in one commit. A dispatcher drains the outbox under a budget per rail, sends each charge with its key, and posts the result.](diagrams/video-base-v2.pdf){width=92%}

What V2 adds, and the objection each addition answers:

- **The ledger, with projections**, answers "no history".
- **Due items claimed with `SKIP LOCKED`, and intent plus outbox in one commit**, answers lost and doubled work.
- **A dispatcher with a token bucket per rail** answers the midnight burst.
- **Keys on every send, UNKNOWN on timeout** answers the double charge.

The objection to V2: inside the database it is correct, but four holes remain. Settlements and returns arrive as
files days later and nothing reads them. Nothing ends an unknown: 240 on the 1st, pending forever. Refunds and
payoffs change schedules, while allocation and fees are buried in code. And nobody checks our books against the
bank's.

## Version 3: close every loop

![V3. File ingest posts settlements and reversals from the bank's and processor's files; a resolver queries every UNKNOWN by the same key; a policy service holds terms, allocation, retry and fee rules as versioned data; reconciliation matches all three views and hands breaks to finance operations; an outbox relay feeds customer notices.](diagrams/video-base-v3.pdf){width=92%}

The collect path, in code:

```python
def collect(batch):
    with db.transaction():
        rows = db.claim_due(today, shard, limit=500)          # SKIP LOCKED
        for r in rows:
            i = intents.open(r.instalment, attempt=r.attempt) # one open per instalment
            outbox.add("send", i.id, key=i.key)               # same commit

def dispatch(i):                                              # under the rail bucket
    try:
        r = rail.charge(i.token, i.amount, key=i.key)
    except Timeout:
        return db.set(i, "UNKNOWN")                           # the resolver takes over
    ledger.post(i, r, key=i.key)                              # lines + balance + state, one commit
```

Run it against a crash at every line. Before the first commit: nothing happened, the rows are due again.
After the commit, before the send: the outbox row is still there, and the dispatcher sends it later. After the
send, before the post: the intent is not settled, the resolver queries by key and posts once. After the post:
the outbox row is deleted on the next pass; if it is sent again, the processor returns the first result for the
same key. No branch guesses.

## The numbered flows, one per functional requirement

![FR1, schedule. 1 loan booked · 2 to the schedule service · 3 terms from policy · 4 schedule version, due items and booking lines in one transaction.](diagrams/video-flow-fr1.pdf){width=90%}

![FR2, collect. 1 claim, intent and outbox in one commit · 2 the dispatcher drains the outbox under the rail budget · 3 charge or debit file, with the key · 4 the result · 5 post the result: lines, balance, state.](diagrams/video-flow-fr2.pdf){width=90%}

![FR3, adjust. 1 refund or payoff arrives · 2 to the schedule service · 3 policy: re-amortise or shorten, and the waterfall · 4 ledger lines and the new schedule version · 5 and 6 the answer.](diagrams/video-flow-fr3.pdf){width=90%}

![FR4, returns. 1 the return file arrives and is stored raw · 2 ingest posts the reversal dated today and puts the instalment back to due · 3 the outbox relay emits the event · 4 the customer is told what happens next.](diagrams/video-flow-fr4.pdf){width=90%}

![FR5, reconcile. 1 the processor's report and bank statement arrive · 2 ingest passes the lines · 3 reconciliation reads the ledger's expectations and matches line by line · 4 every difference becomes an owned break.](diagrams/video-flow-fr5.pdf){width=90%}

## The C4 views and the sequence

![C4 level 1. The customer repays and asks for payoffs; merchants refund; origination books loans; we charge and query at the card processor, send debit files to the bank and receive returns and statements; finance operations own breaks and the close.](diagrams/video-c4-context.pdf){width=92%}

![C4 level 2. The servicing API owns keys, refunds and quotes; schedule and collect owns due items and the state machine; the servicing database holds ledger, intents and outbox; the dispatcher owns rail budgets; policy, file ingest, the resolver and reconciliation close the loops.](diagrams/video-c4-containers.pdf){width=96%}

![One card instalment as a sequence: claim, intent and outbox in one commit; drain under 90 a second; charge with the key; approved; one transaction for state, lines and balance.](diagrams/video-seq-collect.pdf){width=92%}

# Stage 5: Why these choices

## A relational database for the ledger and the queue

The ledger needs real transactions (lines and balance together), constraints (a unique key, a zero-sum check)
and seven years of history at about 340 GB. That is the profile of a relational database partitioned by month,
with old partitions archived read-only. The work queue needs 42 operations a second and exactly-one claiming;
`SELECT ... FOR UPDATE SKIP LOCKED` gives both without another system to run. Putting both in one database means
the claim, the intent and the outbox row commit together, which a separate broker cannot give without its own
outbox. **Alternatives:** a distributed SQL database (unjustified at this size; the cost is latency and
operations for scale we don't need); a document store (no multi-row transactions where we need them).

## One writer to the ledger

Every posting goes through one posting function owned by the ledger team. Other services ask for postings; they
never insert lines. This is how the invariants (zero-sum, keys, versions, the policy version on every
transaction) stay true when six teams touch money.

## A message broker: optional, and why

Not needed for load. Worth adding later if other consumers (notifications, analytics, a data warehouse) need
the events: the outbox relay publishes to it, and nothing on the money path depends on it. Say this
distinction aloud; it is the trade-off the interviewer is listening for.

## Files stored raw before parsing

Every file from the bank and the processor is stored unchanged with a checksum before anything reads it. A
parsing bug then costs a replay, not a lost return. It also gives the auditor the original evidence.

## Policy as data, owned by risk and legal

Allocation order, retry schedules, fee amounts and caps, refund treatment: each is a rule with a version, an
effective date and an owner. Engineering owns the mechanism that applies a rule and records which version it
used. A rule change is a new version, approved by its owner, shadow-tested on yesterday's postings, and never a
code deploy.

