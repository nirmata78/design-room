---
title: "SD-44 · Payment Processing and the Double-Entry Ledger"
subtitle: "A reference solution for a system design round at the Staff bar: one effect per intent, a state for not knowing yet, an immutable journal, and the reconciliation that keeps your books in agreement with the parties that actually move the money"
author: "design-room reference solution · practise with the simulator first"
date: "20 November 2026"
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
