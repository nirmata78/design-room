
# Stage 6: Deep dives

The interviewer picks two or three of these; the video walks all eight. They are ordered so that each fix
creates the next question, and each follows the same grammar: the question, the naive answer, a case with
numbers, where it breaks, the fix, why it works, the push on the fix, and the answer to give in the room.

![The challenge map: the carried baseline with every attack point outlined.](diagrams/video-map.pdf){width=92%}

## 6.1 The processor timed out (the crux, part one)

**The question.** *"The processor times out on a card charge. Your worker retries. Was the customer charged
twice?"*

**The naive answer.** "Mark it failed and retry." The retry goes out as a new attempt with a new key.

**The case.**

| Time | Event |
|----|------------------|
| 08:00:00.000 | `ln-5531` instalment 2, $150, key `coll:ln-5531:2:1` sent |
| 08:00:03.200 | the processor approves it |
| 08:00:10.000 | the worker times out; the naive design marks it FAILED |
| 08:00:12.000 | retry as attempt 2, key `coll:ln-5531:2:2`: approved |
| 08:00:12.000 | the customer has paid $300 for one $150 instalment |

**Where it breaks.** Between the dispatcher and the rails. A timeout is not an answer: the request may have
arrived and been approved. A new key gives the processor no way to know the second request is the same
decision.

**The fix.** At the timeout the intent goes to **UNKNOWN**, a state with exits. A **resolver** queries the
processor *by the same key* after 30 seconds, 2 minutes and 10 minutes. Resending the same attempt reuses
its key. Only a *definite decline* allows attempt 2.

```python
def resolve(i):                                    # runs at +30 s, +2 min, +10 min
    r = rail.query(key=i.key)
    if r == "approved":  return ledger.post(i, r, key=i.key)    # idempotent
    if r == "declined":  return db.set(i, "DECLINED")           # attempt 2 now allowed
    if r == "not_found" and i.age > rail.safe_window:
        return rail.charge(i.token, i.amount, key=i.key)        # the SAME key
    schedule_again(i)                                           # still unknown
```

![The fix on the baseline: the resolver queries the rail and hands the result to the dispatcher, which posts it once.](diagrams/video-ch1-fix.pdf){width=90%}

![The next ten minutes as a sequence.](diagrams/video-seq-unknown.pdf){width=90%}

**Why it works.** S1 (no instalment collected twice) holds at two layers: the processor de-duplicates by key,
and the ledger's unique key means the result can only be posted once even if the resolver and a late answer
race. L2 (every unknown ends) holds because the resolver runs on a schedule with a bounded number of tries,
and after that the settlement file decides.

**The push.** *"The query says 'not found'. You resend. Tomorrow's settlement file shows the first charge went
through after all."*

**The second fix, and the honest limit.** With the same key, a processor that honours keys returns the first
result, so usually there is no harm. "Not found" should only count as final after the processor's documented
window, which is why the resolver waits for `safe_window` before resending. If a duplicate still happens,
reconciliation finds two settled charges for one instalment the next morning; the duplicate is refunded
automatically the same day and counted as an incident. The limit: a processor that neither honours keys nor
answers queries can only be checked by its file, a day late. That belongs in the processor selection criteria.

> "A timeout is not a failure. The intent goes to unknown, the resolver queries by the same key, and a resend
> reuses that key. The settlement file is the final arbiter."

::: warn
**Weak answers.** "Retry with exponential backoff" (with which key?). "Make the charge idempotent" (how, and
at which layer?). "Use a distributed transaction with the processor" (the processor is not a participant in
your transaction).
:::

::: why
**A race worth naming.** The processor's late answer and the resolver's query can both arrive at the
dispatcher within milliseconds. Both try to post. The ledger's unique key on `coll:ln-5531:2:1` lets exactly
one commit; the other gets a unique violation and reads the stored result. That is why the key is on the
ledger transaction and not only at the processor.
:::

## 6.2 The morning of the 1st (overload)

**The question.** *"Six hundred thousand payments are due on the first. Walk me through that morning."*

**The naive answers.** "A cron job at midnight." Or: "It's a thundering herd, so put a message broker in front."

**The case.**

| Time | Event |
|----|------------------|
| 00:00:00 | workers send 2,000 card charges a second; the contract is 100 |
| 00:00:03 | the processor throttles: 95 % rejected; workers retry at once |
| 00:20:00 | 18,000 card charges marked failed; late fees due tomorrow |
| 13:55:00 | the debit file is built; validation fails on one bad record |
| 14:00:00 | cut-off missed: 480,000 collections slip a day |

**Where it breaks.** Not in the database. At the processor's contract, and at the bank's clock.

**The fix: plan the day backwards from the cut-off.** The debit file is built at 09:00, validated, submitted
by 10:30, and acknowledged by 11:00, three hours before the cut-off, so a rejected file can be corrected and
resent. The card window opens at 06:00 at 90 a second (about 22 minutes for 120,000). Soft declines (a
"try again later" from the issuer) are retried around 07:00. Workers claim due rows with `SKIP LOCKED`, and the
intent and outbox row commit with the claim.

```sql
WITH due AS (
  SELECT id FROM due_item
   WHERE due_date = current_date AND status = 'DUE' AND shard = $1
   ORDER BY id LIMIT 500
   FOR UPDATE SKIP LOCKED)
UPDATE due_item d SET status = 'CLAIMED', claimed_by = $2, claimed_at = now()
  FROM due WHERE d.id = due.id
RETURNING d.id, d.loan_id, d.amount_cents, d.rail;
-- same transaction: one intent + one outbox row per claimed row
```

![Two workers, one shard: the second skips the locked rows; a worker that dies before commit releases its locks; a sweeper returns stale claims.](diagrams/video-seq-claim.pdf){width=90%}

**Why it works.** L1 (every instalment attempted before the cut-off) is designed in, with three hours of
margin. S3 (no penalty for our failure) holds because the declines that a burst would cause were our fault.
`SKIP LOCKED` gives exactly-one claiming without a distributed lock; the sweeper handles a worker that dies
after its commit and before its send.

**The push.** *"At ten past six, the processor lowers your limit to fifty a second."*

**The second fix.** The bucket's rate is live: a throttle response halves it at once. By 06:10, 54,000 are done
(600 s × 90/s); the other 66,000 at 50 a second take 1,320 s, 22 minutes: done by 06:32. The better fix is
upstream: spread due dates when loans are created (let the customer pick a day, default to the booking day).
The peak shrinks at the source.

> "Forty-two a second is nothing for a database. The limits are the processor's contract and the bank's
> cut-off, so I plan backwards from the cut-off, with a budget per rail."

::: load
**Under load, the 1st:** 42 operations a second on the database (claims, intents, postings); 90 a second to the
card processor for 22 minutes; one 45 MB file to the bank; 240 timeouts for the resolver; about 14,400 returns
arriving on days 2 and 3. Every one of these numbers is illustrative.
:::

## 6.3 It settled, then it came back (the crux, part two)

**The question.** *"A bank debit settled on the second. On the third it comes back for insufficient funds.
Another one comes back forty days later as unauthorised."*

**The naive answer.** "Settled means paid: close the instalment. Retry anything that fails."

**The case.**

| Time | Event |
|----|------------------|
| Dec 1 | `ln-7702` instalment 3, $150, in the debit file |
| Dec 2 | settled; the naive design closes the instalment |
| Dec 3 | return R01 (insufficient funds): no state for it; the balance was already reduced |
| Dec 2 | `ln-4410` instalment 2, $150, settled |
| Jan 11 | return R10 (unauthorised), day 40; the naive design retries it: a rule breach and a complaint |

**Where it breaks.** In file ingest and the ledger. A return has nowhere to land, and an automatic retry of an
unauthorised debit breaks the network's rules.

**The fix.** SETTLED → **RETURNED**, a normal state. File ingest matches each return to its attempt by the
trace number, posts a **reversing transaction dated the day the return arrives** (never editing the original),
and moves the instalment from PAID back to DUE with the reason. Then **policy** decides:

| Code | Means | Window | Policy |
|---|---|---|---|
| R01 | insufficient funds | 2 banking days | re-present at most twice within 180 days; after the customer's payday |
| R02, R03 | account closed, not found | 2 banking days | stop; ask for a new payment method |
| R10 and similar | unauthorised | up to 60 days | never retry; a new authorisation; dispute review |
| late fee | after the grace period | — | capped by law where the customer lives; never for our failures |

![One return, end to end: the raw file, the match to the attempt, the reversal dated the day it arrived, the policy decision, the customer notice.](diagrams/video-seq-return.pdf){width=90%}

**Why it works.** S2 (no line edited) holds because a return is a new transaction. S3 (no penalty beyond the
rules) holds because the network's rules live in one table, owned by risk and legal, and applied by one piece
of code. L2 holds because RETURNED has defined exits.

**The push.** *"Finance wants to recognise the cash on settlement day. Risk wants to wait sixty days. Who
wins?"*

**The second fix.** Both, with the exposure on a report. Cash is posted at settlement, because that is when the
bank says it is cash; a return is a later reversal, in the month it arrives. A daily report shows everything
settled within the last sixty days, by age, against the observed return rate. Risk prices that exposure; no
process waits on it.

> "Settled is not final for a bank debit. A return is a state and a reversal dated when it arrives, and
> whether we retry is policy: never for unauthorised."

::: warn
**Trap: retrying an unauthorised return.** It looks like ordinary dunning (retrying a failed payment). It is
not: the customer has said they did not authorise the debit. Retrying it breaks the network's rules and turns
a dispute into a complaint, or worse.
:::

::: why
**What is a trace number?** Each entry in a debit file carries an identifier assigned when the file is built,
and the bank returns it with any return. Storing it on the attempt is what lets ingest match a return to
exactly one attempt, rather than guessing by amount and date.
:::

## 6.4 A refund in the middle of the loan (correctness, changing terms)

**The question.** *"After two instalments, the merchant refunds three hundred dollars of the twelve hundred.
What changes?"*

**The naive answer.** "Subtract three hundred from the balance."

**The case.**

| Time | Event |
|----|------------------|
| Oct 1 | `ln-9100` booked: $1,200 in 8 × $150 |
| Nov 1 | instalment 2 paid; $900 outstanding |
| Nov 14 | the merchant refunds $300; the balance column says $600 |
| Dec–May | the schedule is untouched: 6 × $150 = $900 collected |
| May 1 | the customer has overpaid $300, and noticed before we did |

**Where it breaks.** In the schedule. The balance changed; the plan to collect it did not.

**The fix.** A refund is **a ledger transaction and a new schedule version**. The transaction: the merchant
receivable is debited $300 (the merchant owes it back), and the loan's principal is credited $300, keyed by
the merchant's refund ID. The schedule: the terms say how the refund lands. **Re-amortise**: six remaining
payments of $100. **Shorten**: payments stay at $150 and the loan ends after four more. Which one is a product
and legal decision, written into the terms before any code.

Every payment is also **allocated** by a versioned waterfall:

| Order | Bucket | Why |
|---|---|---|
| 1 | fees due | usually first, but rules differ by state |
| 2 | interest due | accrued daily, by calculation |
| 3 | principal due | this instalment's share |
| 4 | future principal | extra or early: shortens the loan |

![The refund as a sequence: the terms version decides, the transaction is keyed by the merchant's refund ID, and schedule version 2 replaces version 1 from instalment 3. An instalment already in flight stays in flight; allocation applies when it settles.](diagrams/video-seq-refund.pdf){width=90%}

**Why it works.** S2 and the audit: every change is a transaction plus a version that says why. S3: the
customer pays what they owe, no more.

**The push.** *"The customer has paid nine hundred. Now the merchant refunds the full twelve hundred."*

**The second fix.** The principal goes to zero, and the $900 the customer paid becomes **customer payable**:
money we owe. It is refunded to the original payment method within the days policy sets, and never held
silently as credit. On the merchant side, they owe $1,200 back; whether the $36 discount fee is returned is
the merchant contract, also versioned.

> "A refund is a ledger transaction and a new schedule version. Re-amortise or shorten is a decision in the
> terms, and any overpayment goes back to the customer."

::: why
**A race the first draft glosses over.** If instalment 3 is in the debit file when the refund arrives, the new
schedule version must not cancel or resize it: the debit is already with the bank. It stays as it is; when it
settles, the waterfall applies it to the new schedule, and any excess becomes a reduction of future principal
(or customer payable, if nothing is left). Regenerating the schedule "from the next unclaimed instalment" is the
rule that keeps the two from colliding.
:::

## 6.5 Paying off with a debit in flight (correctness, timing)

**The question.** *"On the third, the customer pays off the loan early. Instalment three's debit from the first
is still pending. What do you quote?"*

**The naive answer.** "Quote the balance." But the balance either counts the pending debit as paid, or it does
not, and both are wrong some of the time.

**The case.**

| Time | Event |
|----|------------------|
| Dec 1 | `ln-5531` instalment 3, $150, in the debit file; $900 outstanding before it |
| Dec 3 | quote A: $900 (ignores the pending debit); paid by card |
| Dec 3 | the debit settles: $150 over-collected |
| Dec 3 | quote B: $750 (counts it as paid); loan CLOSED, lien released |
| Dec 4 | the $150 returns R01: a closed loan that owes $150 |

**The fix.** A payoff quote is a statement about the future, so it **lists what is in flight**. Quote `q-31`:
$750 now, conditional on the $150 debit clearing, valid to Dec 5. Paying it moves the loan to
**PAID_PENDING**, not CLOSED. If the debit clears its insufficient-funds window, the loan closes. If it returns,
$150 reopens as a single due item, with no late mark.

| In flight at payoff | Quote | Loan state | Closes when |
|---|---|---|---|
| nothing | full balance | CLOSED | at payment |
| a card charge | balance − charge | PAID_PENDING | the charge settles (minutes) |
| a bank debit | balance − debit, conditional | PAID_PENDING | the debit is past its insufficient-funds window |
| a debit not yet sent | full balance; cancel it | CLOSED | at payment |

![The payoff as a sequence: the quote lists the debit in flight; paying it with the quote ID as the key moves the loan to PAID_PENDING; a return reopens one due item; no return by the deadline closes the loan.](diagrams/video-seq-payoff.pdf){width=90%}

**Why it works.** S1: nothing is collected twice. S3: no penalty for a timing gap the customer did not create.
L2: PAID_PENDING has a defined exit on a known date. The only uncertainty left is the 60-day unauthorised
window, which is handled as a dispute rather than by holding every paid-off loan open for two months.

**The push.** *"The day after the payoff, a merchant refund arrives on the same loan."*

**The second fix.** The refund takes the principal below zero; the excess moves to customer payable and is paid
back automatically to the original method. Every customer payable older than the policy's limit pages its
owner. Money we owe is never left as a quiet credit.

> "A payoff quote lists what's in flight. The loan goes to paid-pending and closes only when nothing can still
> come back, and any overpayment is refunded automatically."

## 6.6 Four hundred dollars more than the bank (reconciliation)

**The question.** *"Month-end. The ledger says we collected four hundred dollars more than the bank received.
Find it."*

**The naive answer.** "Compare the totals, and post a $400 adjustment to close."

**The case.**

| Item | Amount | What it is |
|---|----|----------------|
| ledger | $90,000,400 | cash collected in November |
| bank | $90,000,000 | deposits net of returns |
| +300 | timing | two R01 returns on the bank statement for Nov 30; the return file arrives Dec 1 |
| +100 | real | a card dispute the processor netted from its payout; none in the ledger |
| +150 | real | a card payment we hold as settled; the processor never settled it |
| −150 | real | a charge the processor settled that we hold as declined: a double charge |

300 + 100 + 150 − 150 = 400. The last two cancel in the total, and one of them is a customer charged twice.

**The fix.** Match every line, three ways, by reference. The ledger produces **expectations**. The processor's
report and the bank statement are matched to them by our reference first, then by amount within a three-day
window. Every difference becomes a **typed break** (timing, missing in our ledger, missing at the processor,
wrong amount) with an owner and an age.

| Break | Type | Owner | Action |
|---|---|---|---|
| +$300, two returns | timing | auto | closes when the Dec 1 return file posts |
| +$100, card dispute | missing in ledger | disputes team | post the dispute; contest or accept |
| +$150, never settled | missing at processor | payments team | query; reverse our posting |
| −$150, settled, held declined | double charge | payments team | post it; refund the customer today |

![Reconciliation as a sequence: expectations, the processor's report and the bank statement matched by reference, four typed breaks to finance operations, the timing break closing itself.](diagrams/video-seq-recon.pdf){width=90%}

**Why it works.** L3 (every difference owned within a day) is a process with a clock. Totals cannot hide
offsetting breaks, because nothing is matched by total.

**The push.** *"It's month-end, and the processor's report is two days late. Close is in two days."*

**The second fix, and the honest limit.** Close on what is known. The bank statement still reconciles against
the ledger two ways; card items wait as open timing breaks, listed with amounts and ages, and signed off by
finance. A late file delays certainty, not the close. A file late three months running is a vendor problem for
the contract owner.

> "I never reconcile by totals. I match the ledger, the processor and the bank line by line, by reference, and
> every difference is a typed break with an owner and an age."

::: warn
**Trap: the plug.** Posting a $400 adjustment to make totals agree is the most common silent failure in this
round. It closes the month and hides a double charge.
:::

## 6.7 The card processor is down on the 1st (failure and operations)

**The question.** *"Eleven minutes past six on the first, the card processor goes down with sixty thousand
charges left. What do you do?"*

**The naive answer.** "Keep retrying until it comes back. Whatever failed is late tomorrow."

**The case.**

| Time | Event |
|----|------------------|
| 06:00–06:11 | 59,400 charged at 90 a second (660 s × 90) |
| 06:11 | the processor goes down; 180 in flight: UNKNOWN |
| 06:11–06:20 | blind retries: 9,000 more timeouts, all UNKNOWN |
| 09:00 | the processor is back; workers send everything at once; throttled again |
| Dec 2 | 60,000 late fees at $10 = $600,000 charged to customers for our outage |

**The fix, as a runbook.**

| Step | Who | Why |
|---|---|---|
| Pause the card rail | on-call, one switch | stop creating unknowns |
| Resolve every UNKNOWN | resolver, then payments | know before resending anything |
| Suppress late marks and fees | policy, agreed in advance | our outage is not the customer's fault |
| Resume at 50 a second, ramp to 90 | on-call | avoid a second throttle |
| Tell customers | notices | say what happens next, before they ask |

Note what is missing: failover. The card tokens live at this processor, so card customers cannot move to
another one this morning. Bank debit is a fallback only for customers with a debit mandate.

**Why it works.** S1: no unknown is resent blindly. S3: no fee for our failure, because the late clock runs from
our attempt window, not the due date. L1: collection resumes the same day.

**The push.** *"It stays down until three in the afternoon, past the bank's cut-off for any fallback."*

**The second fix.** Collect tomorrow. The day plan re-runs; the 60,000 join tomorrow's card window; the grace
period extends automatically for everyone affected. Longer term: network tokens that work across processors,
and a second processor in the contract. That is a quarter of work, to be priced against what a day like this
costs.

> "Pause the rail, resolve every unknown before sending anything, never charge a late fee for our outage, and
> resume under a lower limit."

## 6.8 How would you know before month-end? (observability)

**The question.** *"How would you know any of this is going wrong, before finance finds it at month-end
close?"*

**The naive answer.** "API error rate and latency."

**The case.**

| Time | Event |
|----|------------------|
| Dec 1 10:30 | debit file submitted, 480,000 entries; API errors 0 % |
| Dec 1 11:00 | acknowledgement: 12,000 rejected after an account-format change; nobody reads it |
| Dec 2 | 12,000 customers get late notices for payments we never sent |
| Dec 30 | found by finance at close |

**The fix: watch the money funnel and the files.** Per rail and day: due, claimed, sent, acknowledged, settled,
returned. A page if the file is not acknowledged by 11:00, or if acknowledged over sent falls below its
baseline. UNKNOWN count and age. Returns by reason code against their baseline. Breaks by age and amount.
Every night: every transaction sums to zero, and every balance equals the sum of its lines.

![The funnel catches it at eleven: acknowledged over sent is 97.5 % against a 99.9 % baseline, with three hours left before the cut-off to correct and resend.](diagrams/video-seq-probe.pdf){width=90%}

| Metric A | Metric B | Conclusion |
|---|---|---|
| sent normal | acknowledged down | the bank rejected entries: read the file |
| UNKNOWN up | latency at the timeout | the processor is slow |
| unauthorised returns up | concentrated on one merchant | an authorisation-capture bug there |
| breaks up today | returns ingest lagging | ingest is stuck, not the money |
| a transaction that does not sum to 0 | anything | stop posting and page |

**The push.** *"A policy change misallocates four dollars on thirty thousand loans. Every transaction still sums
to zero."*

**The second fix.** Balanced but wrong needs two more checks. Shadow every new policy version over yesterday's
postings and diff the allocations before it goes live; because policy is data, that is a query, not a project.
And a per-loan invariant, nightly: the remaining schedule sums to the outstanding principal. A misallocation
that still balances fails right there.

> "I watch the money, not the servers. A funnel from due to settled per rail, the file acknowledged by eleven,
> unknowns and breaks by age, and nightly invariants on the ledger and every loan."

## 6.9 How the whole system degrades, in priority order

When something fails, protect the properties in the order agreed in Stage 1:

1. **Never charge twice.** Under any doubt, stop sending and ask (UNKNOWN, the resolver, the rail switch).
2. **Never lose or invent a cent.** Postings stop before they go unbalanced; files are stored raw and replayed.
3. **Never penalise a customer for our failure.** Fees and late marks are suppressed by policy during incidents.
4. **Collect on time.** Only after the first three: a collection can always move to tomorrow.

The ledger database is the one component whose loss stops everything; it runs with synchronous replication to a
standby in another zone, and a lost primary costs minutes of collection time, never data.

