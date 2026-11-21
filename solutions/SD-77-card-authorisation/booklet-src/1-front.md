---
title: "SD-77 · Card Authorisation and Issuer Processing"
subtitle: "A reference solution for a system design round at the Staff bar: answer inside someone else's deadline with a hold, not a debit; make every network message count once in any order; spend the budget on the signals that matter; and let the ledger absorb the decisions we did not make"
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

This is the **long answer key for question `SD-77`** in
[design-room](https://github.com/nirmata78/design-room), an open-source system design interview
simulator, and the written companion to its reference-solution video. It shows how a strong Staff
candidate (L6/L7) runs the round: what to say, what to draw, and **when**. It adds the **why** behind
every line, so you can defend each choice when the interviewer asks *"why?"*, *"what is that?"* or
*"what happens when it breaks?"*.

Card authorisation looks like the easiest question in a fintech loop: a request arrives, you check the
balance, you say yes. It is asked at senior, Staff and manager levels because the simple answer is wrong
in three separate places at once. The decision has a **deadline set by someone else**, and missing it
does not produce an error: it produces a decision made by the card network on your behalf. The money
**does not move at the till**: an approval is a promise, recorded as a hold, and the real amount arrives
days later in a file, often different, sometimes never. And the fraud decision is **changed by analysts
several times a day**, while the labels that say whether a decision was right arrive two months later.
This document is written for those three places.

**The document has three layers, and you will read them differently:**

1. **Part I, the system in pictures.** Read it first. It explains who is in the chain of a card
   payment, what one restaurant bill does to an account, where the deadline comes from, and where the
   load lands. There is no interview script in it, only understanding.
2. **Part II, the round, stage by stage.** This is what you do in the room. Each stage has the words to
   say, what to draw, and boxes that explain every term. The eight **challenges** of the video are
   Stage 6, and each goes further here than the video can.
3. **Part III, the internals.** How holds and their expiry work, how idempotency on a network reference
   survives a failover, how a conditional write serialises one account, how inline counters are built,
   how a sandboxed rule language is evaluated, and how clearing is matched, at the depth a round reaches
   when you name a mechanism and the interviewer asks how it works.

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
`Read CLAUDE.md. Mock me: SD-77, fintech, staff, full round.`
(3) Debrief against the Stage 12 self-check, then reread only the sections where you fell short.
**Do not memorise numbers.** Memorise *the order of the argument* and how to rebuild each number in
twenty seconds.

**About the numbers.** The scale figures in Stage 1 are the simulator's cue sheet. Everything derived
from them is back-of-the-envelope arithmetic, and every planning assumption (daily volume, hold
lifetimes, the average purchase, record sizes, the fraud rate) is labelled as one: *given*, *derived*,
*illustrative* or *initial target*. None of them is a measurement, they are not any issuer's, processor's
or network's real figures, and this is not any company's actual design. Card networks and their message
standard (ISO 8583) are named only as public standards. **This is not legal, compliance or scheme-rule
advice**: network rules on hold lifetimes, stand-in and clearing differ by network, region and product,
and an issuer's own agreements decide them.

**The prompt as the interviewer reads it:**
*"You're building a card issuer — a company that issues debit cards to its customers. Design the system
that receives authorisation requests from the card network and approves or declines them."*

::: {.key title="The one-sentence insight to land by minute 12"}
**Card authorisation is a promise made inside someone else's deadline.** Answer in milliseconds with a
*hold, not a debit*; make every network message *take effect once, in any order*; spend the deadline on
the signals that matter and have a *written answer for when one is late*; and let the ledger *absorb the
decisions we did not make*.
:::

::: why
**Why this sentence, and why by minute 12.** It names the four places the question is graded: the money
model (holds), correctness under a messy network (idempotency and order), the deadline (budget and fail
policy) and stand-in (decisions made for us). Everything after it defends one of those four. A candidate
who says it early is driving the round; one who discovers stand-in at minute 45 is being driven.
:::

\newpage

# Part I: The system in pictures

## Vocabulary you need first

| Term | Plain meaning | Where it lives |
|---|---|---|
| **Issuer** | The company whose card it is: holds the customer's account, decides yes or no | us |
| **Acquirer** | The merchant's bank; sends the purchase into the network | outside |
| **Card network** | Routes messages between acquirers and issuers; sets the rules and the deadline | outside |
| **Processor** | The issuer's technical front end: link to the network, card vault, stand-in | outside, bought |
| **Authorisation** | "May this card spend this amount here, now?" Approve or decline | the decision service |
| **Incremental authorisation** | "Raise the earlier amount by this much" (a tip, a longer hotel stay) | same message family |
| **Reversal** | "Cancel all or part of an earlier authorisation" | releases a hold |
| **Advice** | "We decided for you while you were late or down; here is what we decided" | stand-in's notification |
| **Stand-in** | The network or processor approving or declining on our behalf, within limits we set | outside, configured by us |
| **Hold** | Money reserved against an account by an approval; not yet moved | the authorisation store |
| **Available balance** | Posted balance minus active holds: what a new purchase may spend | computed per decision |
| **Clearing** | The network's file with the real, final amounts, days later | the clearing matcher |
| **Settlement** | Banks paying each other the net amounts; the issuer pays the network | treasury, outside the design |
| **Network reference** | The identifier the network gives a transaction; links its messages | the message table |
| **Token** | A stand-in for the card number; the real number stays in the processor's vault | the card table |
| **Rule set** | A versioned bundle of fraud rules, written by analysts as data | the rule service |
| **Chargeback** | The cardholder disputes a purchase; the money is pulled back, weeks later | outside the design; a label |

::: why
**Why this table first.** Most weak answers fail on vocabulary, not on boxes. A candidate who says
"we debit the balance" has not heard the word *hold*; one who says "the network gives us 100 ms" has
confused the network's deadline with their own target. Getting the nouns right is half of the money
model.
:::

## The path of a swipe

![The chain of a card payment, and who decides when we are late](diagrams/video-swipe-path.pdf){width=100%}

A cardholder taps at a till. The **merchant's terminal** sends the purchase to the **acquirer**, which
sends it into the **card network**. The network routes it by the card's number range to the
**issuer's processor**, which holds the card vault and the link, and the processor passes it to **us**.
We answer approve or decline, and the answer travels the same chain back. The whole round trip is a
couple of seconds at most; the network's own timeout is about two seconds, and the processor's is
shorter. Our part must be a small fraction of it.

If we do not answer in time, nothing fails visibly at the till. The network **stands in**: it approves
or declines using limits we configured in advance (for example, approve up to some amount per
transaction and per day, decline above), and later sends us an **advice** saying what it decided. The
cardholder never knows. We do, the next minute, and we must record it.

No money moved. Days later, the network sends a **clearing file** with the final amounts, and the banks
**settle** between themselves. The design is therefore two systems joined at the hold: a hard
real-time decision path, and a batch clearing path that turns promises into posted money.

## What one restaurant bill does to an account

![One restaurant bill: a hold, an incremental, then clearing](diagrams/video-holds.pdf){width=100%}

| When | Message | Effect | Posted | Available |
|---|---|---|---|---|
| Mon 20:14 | Authorise \$60 | Hold \$60 | \$500 | \$440 |
| Mon 20:16 | Incremental authorisation +\$12 (tip) | Hold becomes \$72 | \$500 | \$428 |
| Thu 06:00 | Clearing \$72, matched by network reference | Post \$72; release the hold | \$428 | \$428 |

Read the last column. Available balance is what the next decision reads, and it moved at the till,
not on Thursday. Posted balance moved on Thursday, when the money really moved. Between the two, the
customer's banking app shows a **pending** \$72. If Thursday never comes (the restaurant never submits),
the hold **expires** after a lifetime set by merchant category, about seven days for most and thirty
for hotels and car hire, and the \$72 comes back to available.

::: warn
**The weak answer debits \$60 at the till.** Then Thursday's \$72 is either a second debit (the
customer pays \$132) or a mismatch nobody owns (the restaurant is short \$12). Every follow-up the
interviewer has, tips, hotel pre-authorisations, partial shipments, refunds, currency conversion, is a
case where the authorised amount and the cleared amount differ. Debiting at authorisation fails all of
them.
:::

## The same story as states

A hold is a small state machine, and every message moves it:

| From | Message | To | Notes |
|---|---|---|---|
| — | authorisation approved | **open** | amount A, expiry by merchant category |
| — | advice (stand-in approved) | **open** | even if it overdraws the account |
| open | incremental authorisation | open | amount A + delta |
| open | partial reversal | open | amount reduced |
| open | full reversal | **released** | available restored |
| open | clearing record matched | **cleared** | posted in the ledger; hold released |
| open | expiry passed *and* the day's clearing file has arrived | **expired** | available restored |
| released or expired | late clearing record | — | posts anyway; may overdraw: a modelled state |

The last row is where weak designs break: the network has already paid the merchant, so a clearing
record is a fact, not a request. We post it even if the hold is long gone.

## The central contrast: two clocks

| | The decision clock | The money clock |
|---|---|---|
| Speed | milliseconds, inside a ~2 s network deadline | days, by daily file |
| Who sets it | the network | the network's clearing cycle |
| What it writes | a hold, a decision record | a posting in the core ledger |
| What happens if late | the network decides for us (stand-in) | posting slips; holds wait; the customer sees pending longer |
| Truth | our decision, with its inputs | the clearing file |
| Failure mode | missing the deadline | a mismatch nobody owns |

Most of the design is keeping these two clocks apart: nothing on the money clock may sit on the
decision clock's path, and nothing the decision clock decided may be lost by the money clock.

## Where the deadline goes

![Decision quality against time: the deadline is someone else's](diagrams/video-tension.pdf){width=100%}

Each signal costs time. Card status and the balance are a few milliseconds. In-process rules are ten.
A fraud model is tens of milliseconds and occasionally far more. Rich aggregates computed on request
would be hundreds. Past our own target, the extra quality is small; past the network's deadline, the
network decides with far less information than we have. The design spends the deadline deliberately and
writes down, in advance, what happens when a step is late.

## Where the load lands

::: load
**Authorisation path at the busiest peak (illustrative):** 4,000 requests a second; 1,200 in flight at
the 300 ms target, about 400 at a typical 100 ms; about 12,000 state reads a second (account and holds,
card, counters), each budgeted at a few milliseconds. **Per account:** a few authorisations a minute.
**Auth store:** about 36 million open holds, about 7 GB. **Event log:** about 20 million decisions a day,
40 GB of decision records. **Clearing:** one file of about 10 million records, 5 GB, once a day.
**Advices after an outage:** a burst of hundreds of thousands within minutes.
:::

The shape matters more than the size. The fleet is small; the tail latency of the slowest dependency is
the whole problem on the decision path; the per-account rate is tiny, so serialising per account is
free; and the batch side is large but has hours, not milliseconds.

## The whole design on one page

![The final design on the carried baseline](diagrams/video-base-final.pdf){width=100%}

Across the middle, the authorisation path: the **card network** (through the processor) calls our
**auth gateway**, which maps the network's message format to ours; the **decision service** reads and
increments **burst counters** in the **feature store**, asks the **model scorer** for a risk score
under a 60 ms cut-off while **rules** run in its own process, and reserves the hold in the
**authorisation store** in one atomic write. The answer goes back the same way. Above, the **rule
service** pushes versioned rule sets that **analysts** write, and a **stream aggregator** feeds pattern
features. Below, every decision goes through an outbox to the **event log**, which feeds **alerts,
cases and the decision archive**. On the right, the **clearing matcher** turns the network's daily file
into postings in the **core ledger** and releases holds in the authorisation store, and posted-balance
changes flow back from the ledger to the authorisation store.
