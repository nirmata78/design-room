
# Stage 6: Deep dives

The video's eight challenges, each in the same shape: the risk, the naive answer and why it fails, the mechanism,
the failure case that tests it, what to say, and the weak answers to avoid. They are ordered so that each fix
creates the next question. Correctness: 2 and 5. Failure recovery: 1, 3 and 7. Overload: 4. The outside truth: 6.
Observability: 8. The crux, not knowing and the outside world's books, gets two: 1 and 6.

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
is a metric with an alert. The relay is partitioned by account so one slow partition does not hold the others. Webhooks
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
