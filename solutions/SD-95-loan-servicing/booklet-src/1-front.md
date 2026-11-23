---
title: "SD-95 · Instalment Loan Servicing: the Ledger and the Collections Scheduler"
subtitle: "A reference solution for a system design round at the Staff bar: an immutable double-entry ledger, a payment state machine that admits unknown and returned, a scheduler bounded by the payment rail rather than the database, and the daily three-way reconciliation that proves the books agree with the bank"
author: "design-room reference solution · practise with the simulator first"
date: "21 November 2026"
documentclass: article
fontsize: 10pt
geometry: a4paper,top=0.7in,bottom=0.75in,left=0.75in,right=0.75in
colorlinks: true
linkcolor: blue
urlcolor: blue
toc: true
toc-depth: 2
numbersections: false
---

\newpage

# How to read this document

This is the **long answer key for question `SD-95`** in
[design-room](https://github.com/nirmata78/design-room), an open-source system design interview
simulator, and the written companion to its reference-solution video. It shows how a strong Staff
candidate (L6/L7) runs the round: what to say, what to draw, and **when**. It adds the **why** behind
every line, so you can defend each choice when the interviewer asks *"why?"*, *"what is that?"* or
*"what happens when it breaks?"*.

**The document has three layers, and you will read them differently:**

1. **Part I, the system in pictures.** Read it first. It explains what happens to an instalment loan
   from the day it is booked to the day it is closed: how a schedule is made, how each payment is
   collected, why the truth about a collection keeps arriving for weeks, and where the load lands. There
   is no interview script in it.
2. **Part II, the round, stage by stage.** This is what you do in the room. Each stage has the words to
   say, what to draw, and boxes that explain every term. The eight **challenges** of the video are Stage
   6, and each goes further here than the video can.
3. **Part III, the internals.** How double entry, idempotency keys, a database used as a work queue,
   token buckets, bank-debit returns and reconciliation actually work, at the depth a round reaches when
   you name a mechanism and the interviewer asks how it works.

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
`Read CLAUDE.md. Mock me: SD-95, fintech, staff, full round.`
(3) Debrief against the Stage 12 self-check, then reread only the sections where you fell short.
**Do not memorise numbers.** Memorise *the order of the argument* and how to rebuild each number in
twenty seconds.

**About the numbers.** The scale figures in Stage 1 are the simulator's cue sheet: five million active
loans, bank debit for 80 % of collections and card for 20 %, 600,000 collections due on the 1st, a card
processor contract of 100 requests a second, a bank cut-off, seven years of audit, and a two-day
month-end close. Everything derived from them is back-of-the-envelope arithmetic, and every planning
assumption (the average instalment, the return rate, the timeout rate, record sizes) is labelled:
*given*, *illustrative*, *initial target* or *derived*. None of them is a measurement, none is any
company's figure, and this is not any company's design. The rails are described in their US form
(automated bank debits and card networks) because the cue sheet names them; amounts are in dollars and
stored as integer cents. The rule-based statements about bank-debit returns (the return windows and the
limit on re-presenting a returned debit) were checked against public rule summaries in November 2026;
check them again before relying on them. **This is not legal, accounting or compliance advice.**

**The prompt as the interviewer reads it:**
*"Loans are created elsewhere. Design the system that services them for their whole life: it schedules
repayments, collects them by bank debit or card, handles refunds, late fees and early payoff, and
reconciles with the bank."*

::: {.key title="The one-sentence insight to land by minute 10"}
**Settled is not final for a bank debit.** Throughput is never the problem here; correctness over
months is. So the design is an immutable double-entry ledger, a payment state machine that admits
*unknown* and *returned*, a scheduler bounded by the *rail* rather than the database, and a daily
*three-way reconciliation*.
:::

::: why
**Why is this the insight?** The prompt sounds like a batch job: on each due date, charge everyone who
owes money. Candidates hear "600,000 collections on the 1st" and reach for a message broker to absorb a
"thundering herd". But 600,000 over four hours is 42 a second, which one relational database handles
without noticing. What actually goes wrong in loan servicing is slower and quieter: a card charge that
times out and gets charged again, a bank debit that settles on the 2nd and is returned on the 3rd, or
returned as unauthorised forty days later, a merchant refund that changes the schedule of a live loan, a
customer paying off early while a debit is still in flight, and a month-end where the ledger says $400 more
than the bank. Every one of those is a correctness problem over time. The candidate who names that, and
designs a state or a mechanism for each point where the truth arrives, has found the question.
:::

\newpage

# Part I: The system in pictures

## Vocabulary you need first

**About the loan**

| Term | Meaning |
|---|---|
| Instalment loan | A loan repaid in a fixed number of scheduled payments. Here: 3 to 12 monthly instalments, often for a purchase at a merchant ("buy now, pay later") |
| Terms, terms version | The contract: number of instalments, rounding, interest if any, fees, the allocation order, how refunds are treated. Versioned, because old loans keep old rules |
| Schedule, schedule version | The list of instalments with due dates and amounts, derived from the terms. A refund or payoff produces a *new version*; the old one stays for the audit |
| Due item | One instalment due on one date: the row the collections scheduler works from |
| Payoff | Paying the whole remaining balance early. A *payoff quote* says how much, until when |
| Re-amortise / shorten | Two ways to apply a partial refund: smaller remaining instalments, or the same instalments and an earlier end |
| Allocation waterfall | The order in which a payment is applied: typically fees due, interest due, principal due, then future principal |

**About the rails**

| Term | Meaning |
|---|---|
| Rail | A way money moves. Here: bank debit (automated clearing, in files) and card (through a processor, one request at a time) |
| Bank debit | We instruct the customer's bank to pay us, under a *mandate* (the customer's authorisation). Sent in batch files with a daily *cut-off* |
| Settlement | The point at which the bank says the money moved. For a bank debit, one to two business days after submission |
| Return | A bank debit that comes back after settlement. *Insufficient funds* (code R01) within two banking days; *unauthorised* (R10 and similar) up to sixty calendar days |
| Re-presentment | Sending a returned debit again. For insufficient funds, the network's rules allow it at most twice within 180 days; never for unauthorised |
| Processor | The company that runs card charges for us. Card numbers are stored there as *tokens* |
| Contract limit | The processor's allowed request rate: 100 a second here |

**About the books**

| Term | Meaning |
|---|---|
| Double entry | Every movement of money is a transaction of two or more lines whose amounts sum to zero |
| Line | One amount on one account in one transaction. Never edited |
| Account | Where lines accumulate: per loan (principal, interest, fees) and system-wide (cash clearing, cash at bank, merchant payable, customer payable) |
| Balance projection | A stored balance, updated in the same transaction as the lines, at a version; always provable from the lines |
| Reversal | A new transaction that undoes an earlier one. The only way to correct a mistake |
| Reconciliation | Matching our books against the processor's report and the bank's statement, line by line |
| Break | A difference found by reconciliation: typed, owned, aged |

## What a loan experiences

Follow one loan, `ln-5531`, through its life. It is a $1,200 purchase repaid in eight monthly instalments of
$150, collected by bank debit.

1. **Day 0, booked.** Origination emits *loan booked*. Servicing creates schedule version 1 (eight
   instalments of $150, due dates on business days), and posts the booking: the loan's principal receivable
   is debited $1,200; the merchant payable is credited $1,164; merchant discount income is credited $36.
2. **The merchant is funded** (by a payouts system outside our scope), which settles the merchant payable.
3. **Each due date.** The scheduler claims the due item, opens a *payment intent* with a key, and writes an
   outbox row, all in one commit. The dispatcher adds the debit to the day's bank file, which is submitted by
   10:30 and acknowledged by 11:00. The ledger moves $150 into *cash clearing*: the collection is PENDING.
4. **A day or two later, settled.** The bank's settlement report confirms it. Clearing moves to cash at bank.
   The instalment is PAID.
5. **Month 2, returned.** One debit settles and comes back the next day for insufficient funds. The
   collection moves from SETTLED to RETURNED; a reversing transaction is posted *dated the day the return
   arrives*; the instalment goes back to DUE with the reason; policy schedules a re-presentment after the
   customer's payday.
6. **Month 3, refunded.** The merchant refunds $300 of the purchase. The ledger records that the merchant
   owes us $300 and the loan's principal is $300 lower. Schedule version 2 replaces the remaining instalments,
   re-amortised or shortened as the terms say.
7. **Month 5, paid off.** The customer asks for a payoff quote. The quote lists the debit still in flight. The
   loan goes to PAID_PENDING and closes when nothing can come back.
8. **Every night,** reconciliation matches each line of the ledger against the processor's report and the
   bank's statement, and gives every difference to an owner.

## The same story as a collection's states

![The collection state machine. A timeout leads to UNKNOWN, which is resolved by querying with the same key, never by resending with a new one. SETTLED is not final for a bank debit: a return can arrive up to sixty days later and is posted as a reversal. An insufficient-funds return may be retried at most twice more; an unauthorised one never.](diagrams/video-states.pdf){width=96%}

Read it left to right. SCHEDULED, SUBMITTED, PENDING, SETTLED is the happy path. Two red states are the
point of the question. **UNKNOWN** is where a card charge goes when the processor does not answer: we do
not know whether money moved, so we neither call it failed nor call it paid; we ask. **RETURNED** is where
a settled bank debit goes when the bank sends it back. It has exits: a re-presentment, allowed by policy for
insufficient funds; or a stop, for an unauthorised return, which needs the customer's new authorisation.

## Why the truth keeps arriving

![When is a collection final? Seconds for a card answer (or nothing); one to two days for a debit to settle; two banking days for an insufficient-funds return; sixty days for an unauthorised return; months for refunds and card disputes; seven years of audit.](diagrams/video-truth.pdf){width=94%}

A payment gateway (SD-44) deals with truth that arrives over a payment's life. Servicing deals with the same
problem multiplied by a schedule: every instalment of every loan goes through this timeline, and the
schedule itself changes when refunds and payoffs arrive. That is why the design has a mechanism at each
point: the resolver for seconds, settlement posting for days, return handling for weeks, schedule versions
for months, and reconciliation every day.

## One loan as entries

![A $1,200 loan booked: principal receivable debited 1,200, merchant payable credited 1,164, discount income credited 36. One $150 instalment: cash clearing debited 150 and principal credited 150 while pending; then cash at bank debited 150 and clearing credited 150 at settlement.](diagrams/video-entries.pdf){width=92%}

::: why
**Why a clearing account?** A pending bank debit has not moved money yet, but the loan's balance should
show that a payment is on its way, or the customer would be chased for it. So the collection is posted
twice: first into *cash clearing* (an account that says "money expected"), then from clearing into cash when
the bank settles. A balance on the clearing account at any moment is exactly the money in flight; a
clearing balance that never empties is a bug or a lost file, and reconciliation sees it.
:::

## Where the load lands

::: load
**The 1st of the month (illustrative, from the cue sheet):** 600,000 collections. 480,000 bank debits go in
one file (about 45 MB). 120,000 card charges go one by one under a contract of 100 a second: at 90 a second,
about 22 minutes. Spread over four hours, the whole day is about **42 operations a second** on the database.
Two days later: about 14,400 insufficient-funds returns (an illustrative 3 %). On the 1st itself, about 240
card timeouts (an illustrative 0.2 %), each one a possible double charge.
:::

![The 1st, planned backwards from the bank's 14:00 cut-off: the card window from 06:00 at 90 a second, soft-decline retries around 07:00, the debit file built from 09:00 and submitted by 10:30, the bank's acknowledgement by 11:00, three hours of margin before the cut-off.](diagrams/video-dayplan.pdf){width=94%}

The load map has one surprise for most candidates: the database is the least loaded component. The binding
constraints are outside the system: a processor contract measured in requests a second, and a bank clock
that closes the door at 14:00. The design follows the constraints, not the volume.

\newpage

# Part II: The round, stage by stage

| Stage | Clock (75 min, typing-adjusted) | What you produce |
|---|---|---|
| 1 Clarify | 0–12 | Seven questions, five functional requirements, numbers on the non-functional ones, stated cuts |
| 2 Estimates | 12–21 | Three calculations that change the design |
| 3 API and data | 21–30 | The event, the calls, the states, the tables, the posting transaction |
| 4 High-level design | 30–45 | V1 → V2 → V3, the collect path walked end to end |
| 5 Why these choices | (inside 4) | The database as the queue; one writer to the ledger; files stored raw |
| 6 Deep dives | 45–67 | Two or three of the eight challenges, as the interviewer picks them |
| 7–11 Wrap | 67–75 | Failures, SLOs, cost, the EM layer, the four-sentence close |

