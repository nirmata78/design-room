---
title: "SD-82 · Instant Credit at the Point of Sale"
subtitle: "A reference solution for a system design round at the Staff bar: a regulated decision under a deadline set by slow, paid vendors, one atomic step from acceptance to a booked loan, decisions you can replay years later, and identity data kept in a small box"
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

This is the **long answer key for question `SD-82`** in
[design-room](https://github.com/nirmata78/design-room), an open-source system design interview
simulator, and the written companion to its reference-solution video. It shows how a strong Staff
candidate (L6/L7) runs the round: what to say, what to draw, and **when**. It adds the **why** behind
every line, so you can defend each choice when the interviewer asks *"why?"*, *"what is that?"* or
*"what happens when it breaks?"*.

Instant credit at the point of sale is the question a lending company asks when it wants to know whether
you understand its business, not only its servers. The load is tiny: a few applications a second. That is
exactly why it trips strong engineers. They arrive ready to shard and cache, and the interviewer wants to
hear about a credit bureau that is slow one time in ten, a phone that drops between "accept" and the
answer, a decline that must be explained to a regulator fourteen months later, and a social security
number that must never reach a log file. This document is written for those parts.

**The document has three layers, and you will read them differently:**

1. **Part I, the system in pictures.** Read it first. It explains what the system is, what one
   application experiences from the scan of a code to the merchant being paid, and where the load and
   the money land. There is no interview script in it, only understanding.
2. **Part II, the round, stage by stage.** This is what you do in the room. Each stage has the words to
   say, what to draw, and boxes that explain every term. The eight **challenges** of the video are
   Stage 6, and each one goes further here than the video can.
3. **Part III, the internals.** How scatter-gather with a deadline, circuit breakers, optimistic versions,
   the outbox, decision records, champion and challenger rollouts and tokenisation vaults actually work, at
   the depth a round reaches when you name a mechanism and the interviewer asks how it works.

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
`Read CLAUDE.md. Mock me: SD-82, fintech, staff, full round.`
(3) Debrief against the Stage 12 self-check, then reread only the sections where you fell short.
**Do not memorise numbers.** Memorise *the order of the argument* and how to rebuild each number in
twenty seconds.

**About the numbers.** The scale figures in Stage 1 are the simulator's cue sheet. Everything derived from
them is back-of-the-envelope arithmetic, and every planning assumption (approval rate, take-up, record
size, the share of late bureau answers, exposure caps) is labelled as one: *given*, *derived*,
*illustrative* or *initial target*. None of them is a measurement. They are not any lender's real figures,
and this is not any company's actual design. Statements about lending rules are general descriptions for
interview practice, not legal or compliance advice.

**The prompt as the interviewer reads it:**
*"A customer at a merchant's counter scans a QR code to pay a $1,200 bill in instalments. Design the
system that decides within a few seconds whether to lend, shows the offers, and creates the loan when the
customer accepts."*

::: {.key title="The one-sentence insight to land by minute 12"}
**Instant credit at the counter is a regulated decision under a deadline set by slow, paid vendors,
followed by one atomic step.** Throughput is tiny. The grade is on the slow edges, on booking exactly one
loan, on decisions you can explain years later, and on keeping identity data in a small box.
:::

::: why
**Why this sentence, and why by minute 12.** It tells the interviewer that you have found where the
question is graded. Candidates who miss it spend twenty minutes on sharding a database that sees eight
writes a second, and then run out of time before the parts that decide the level: what happens when a
vendor is missing, which step must be atomic, what a decision record holds, and who owns each degraded
path. Saying the sentence early also gives you permission to keep the core boring, which is the right
call here.
:::

\newpage

# Part I: The system in pictures

## Vocabulary you need first

| Term | Plain meaning | Where it lives |
|---|---|---|
| **Application** | One request for credit for one purchase, with a status | the application database |
| **Credit bureau** | A paid vendor that returns a person's credit file | outside; called through an adapter |
| **Pull** | One paid request for a credit file; it may be recorded on the person's file as an inquiry | the vendor call log |
| **Identity and fraud check** | A paid check that the person exists and is who they say | outside; called in parallel |
| **Scatter-gather** | Send all vendor calls at once, collect what arrives by a deadline | the decision orchestrator |
| **Circuit breaker** | Stop calling a vendor that is failing for everyone; probe it again later | each vendor adapter |
| **Missing-data policy** | The signed table that says what to do when a vendor did not answer | the policy engine, versioned |
| **Refer** | "We'll finish in a few minutes": the decision is delayed, not made badly | a state of the application |
| **Offer** | A priced proposal: term, rate (APR), schedule, total cost, expiry | written with the decision |
| **Disclosure** | The legally required statement of the offer's cost, shown before acceptance | its version is stored with the loan |
| **Adverse action reasons** | The principal reasons a person was declined, which they must be told | the decision record and the notice |
| **Lender of record** | The legal lender; often a partner bank, while we decide and service | contracts, policy approval |
| **Booking** | Creating the loan from an accepted offer: the one atomic step | one database transaction |
| **Outbox** | A row written in the same transaction as the loan, later published as an event | the application database, then the log |
| **Decision record** | Everything that produced a decision: inputs, versions, outputs | encrypted object storage |
| **Vault** | The only place raw identity data (SSN, date of birth) exists; everyone else sees tokens | a small, separate service |
| **Champion and challenger** | The model in use, and a new one tested against it | the policy engine |
| **Funding** | Paying the merchant for the purchase, net of a fee | the funding service, after booking |

## What one application experiences

Follow one purchase, start to finish, with no jargon.

1. **The scan.** A customer at a car-repair shop owes $1,200. They scan the merchant's code. Their phone
   opens a short form: name, date of birth, the last digits of an identity number, income.
2. **The vault.** The identity fields go straight into the vault, which returns a token. From here on,
   our systems carry `tok_8f2c`, not the number.
3. **The application.** The merchant's point of sale and the phone now share one application,
   `ap_91`, in status **STARTED**. If the phone retries, the idempotency key returns the same application.
4. **Everything at once.** The orchestrator calls the identity and fraud vendor and credit bureau A at
   the same moment, and sets a deadline two seconds from now. Identity answers in 0.40 s, fraud in
   0.35 s, the bureau in 0.62 s.
5. **The decision.** Features are computed from what arrived. The model scores; the policy rules decide
   (approve, refer, decline); pricing builds three offers. The decision record is written once.
6. **The offers.** About a second and a half after the customer pressed submit (in a usual case), three offers appear on the phone:
   pay in four, six months, twelve months, each with its total cost and rate. The application is
   **OFFERED**, and the offers expire in fifteen minutes.
7. **Acceptance.** The customer picks six months and taps accept. One database transaction moves the
   application to **BOOKED**, inserts the loan, and inserts an outbox row. The phone shows the loan.
8. **After the counter.** The relay publishes *LoanBooked*. That evening, funding pays the merchant
   $1,164 (the $1,200 less a 3 % merchant fee) in its daily batch. Servicing opens the repayment schedule.

::: say
The customer waits about two seconds. Everything after the tap on accept happens without them: one
transaction while they watch, then events.
:::

## The same story as a state machine

![The application as a state machine. Each arrow is one committed row. The only atomic step is OFFERED → BOOKED.](diagrams/video-states.pdf){width=95%}

Read the picture left to right. **STARTED** means the application exists and nothing has been asked.
**CHECKING** means vendor calls are out. From there, three exits: **OFFERED** (approved, priced),
**REFERRED** (data was missing at the deadline, and the policy said "finish within minutes"), or
**DECLINED** (with reasons about the applicant). A referred application comes back to OFFERED or DECLINED
when the missing answer arrives. An offer either becomes **BOOKED** when accepted or **EXPIRED** after
fifteen minutes. A booked loan becomes **FUNDED** when the merchant is paid.

Two facts hide in this picture and are worth saying in the round. First, the vendor calls are not undone
if the application later fails: a credit pull happened, it was paid for, and it is recorded. Second,
funding is after booking and is not part of the customer's wait: it is the one step with a real
compensating action, because a transfer can be reversed.

## The central contrast

![Time against evidence against money: what waiting buys, and what it costs.](diagrams/video-tension.pdf){width=95%}

In most systems the hard trade is between consistency and availability. Here it is between **time,
evidence and money**. Waiting longer for a vendor adds evidence and approvals, and loses the sale at
the counter. Deciding early keeps the sale and adds risk. Asking a second bureau adds evidence and costs
another dollar and another inquiry on the customer's file. Every design choice in this document is a
point on that triangle, and the ones that matter are owned by someone in credit risk, not chosen by an
engineer in a timeout setting.

## A time table of the core flow

| t (ms) | What happens | Where |
|---|---|---|
| 0 | Submit from the phone; idempotency key checked | API edge |
| 150 | Identity tokenised; application row STARTED committed | vault, application DB |
| 200 | Three vendor calls sent at once; deadline set at 2,200 | orchestrator |
| 550 | Fraud answers | vendor adapter |
| 600 | Identity answers | vendor adapter |
| 820 | Bureau A answers (a usual case) | vendor adapter |
| 820 | All required answers in: no need to wait for the deadline | orchestrator |
| 1,070 | Features, model, policy, pricing done | policy engine |
| 1,120 | Decision record written; row OFFERED | object storage, application DB |
| 1,320 | Offers on the phone | push |

The deadline is a ceiling, not a wait: when every required answer has arrived, the orchestrator moves on.

## The whole design on one page

![The final design. The counter path across the middle; the vault above; what happens after booking, and what we keep, along the bottom.](diagrams/video-base-final.pdf){width=100%}

## Where the load and the money land

::: load
**Applications:** 0.8 a second on average, about 8 a second at the Saturday peak. **Database writes:**
about six committed transitions an application, so about 50 a second at peak. **Vendor calls:** about
32 a second at peak, about 64 in flight with a two-second deadline. **Decision records:** about 100 GB a
month. **Loans:** about 28,000 a day. **Funding:** one batch a day per merchant. **Money:** about $2M a
month to bureaus if every application pulls, about $1B a month of loans originated (illustrative).
:::

The load map says something most candidates miss: our own servers are idle. The pressure is on the
vendors (their latency, their error rate, their contract rate limits and their invoices) and on the
correctness of one transaction. The design spends its complexity there.

\newpage

# Part II: The round, stage by stage

| Stage | Minutes (of 75) | What the interviewer is listening for |
|---|---|---|
| 1 Clarify | 0–8 | The lender of record, the deadline, the vendors and what they cost, the rules on reasons and records |
| 2 Estimates | 8–14 | That the load is tiny, and that the bureau bill is the largest line |
| 3 API and data | 14–20 | An application as a resource; idempotency keys; a unique loan; a decision written once |
| 4 High-level design | 20–32 | V1 → V2 → V3, each answering an objection; one walk-through per requirement |
| 5 Technology | inside 4 and 6 | Mechanisms before brands |
| 6 Deep dives | 32–62 | The eight challenges; two on each half of the crux |
| 7 Mid-round requirement | inside 6 | The bureau outage; a new model; a second region |
| 8–9 Failures, SLOs, cost | 62–70 | What pages, and what it costs |
| 10 EM layer | if asked | Owners for every degraded path; the team seams |
| 11 Close | 70–75 | Four sentences |

# Stage 1: Clarify requirements

Ask six questions before drawing anything. Each answer moves the design, and the interviewer is watching
whether you ask the ones that only someone who knows lending would ask.

| Question | The cue sheet's answer | What it changes |
|---|---|---|
| How many applications? | 2 million a month; Saturday peak about 10× the average | The load is tiny: one relational primary |
| How long can the customer wait? | Offers on screen in under 3 s for 95 %; 10 s is a lost sale | One deadline for all vendor calls; nothing optional on the counter path |
| Who is the lender of record? | We decide on the partner bank's credit policy and service the loan; the bank is the lender of record | Every policy version is approved by the bank; records are the bank's too; funding flows through the bank |
| Which vendors, how fast? | Two bureaus (p50 0.6 s, p99 several seconds, about 1 % errors); identity and fraud (p99 400 ms); optional bank-account data (seconds to minutes) | The bureau's tail sets the deadline; bank data is never awaited at the counter |
| What do they cost? | About $1 a bureau pull; identity checks about 5 cents | Never race two bureaus; the bureau bill is the largest cost |
| Which rules? | Disclosures before signing; the principal reasons for every decline; records kept about seven years; fairness testing | Decisions must be reproducible; a vendor outage is not a decline reason; the disclosure version is part of the loan |

::: why
**Why ask who the lender of record is.** Many point-of-sale lenders decide and service loans while a
partner bank is the legal lender. That changes who approves a credit policy (the bank must), whose records
the decision records are, and how the merchant is paid. A candidate who asks it shows they know the
business model, and the interviewer will often answer with a smile. A candidate who never asks it designs
as if we were a bank, which is usually wrong and always a missed signal.
:::

::: why
**Why ask about the rules.** Three rules shape the architecture directly. A declined applicant must be
told the principal reasons, so a decision must carry reasons about the applicant, and "the bureau timed
out" is not one: that is why a *refer* path exists. Disclosures must be shown before the customer signs,
so the version shown is part of the contract and must be stored with the loan. Records are kept for years,
so a decision must be reproducible long after the model that made it has been replaced.
:::

**Functional requirements**, each of which gets a numbered flow in Stage 4:

- **FR1 · Apply.** The customer scans the merchant's code; identity goes into a vault; an application
  exists, and a retry returns the same one.
- **FR2 · Decide.** Gather identity, fraud and credit data under one deadline; return offers, a refer, or
  a decline with reasons.
- **FR3 · Accept and book.** The customer accepts one disclosed offer; exactly one loan is booked.
- **FR4 · Fund and hand off.** The merchant is paid net of fees; the loan goes to servicing; decline
  notices go out.

**Non-functional requirements**, all initial targets:

| Requirement | Target | Why this number |
|---|---|---|
| Offers on screen | p95 under 3 s from submit | The cue sheet; 10 s is a lost sale |
| Availability of apply and decide | 99.9 % in merchant hours | A merchant with a queue at the counter |
| Duplicate or unaccepted loans | zero | Money and law |
| Reproducible decisions | 100 %, for 7 years | Adverse action and audit |
| Raw identity outside the vault | never | Privacy law and breach blast radius |
| Merchant funded | within one business day | The merchant contract |
| Degraded paths | every one under an exposure cap | Credit risk's appetite |

**Scope, said aloud.** In: apply, identity, decide, offers, refer, accept, book, the funding
instruction, the servicing handoff, decline notices. Out, on purpose: repayments and the ledger (SD-95),
card authorisation (SD-77), merchant onboarding and underwriting, merchant fraud, model training pipelines
(we consume a model artefact), collections, and the payment rail itself (SD-44).

> "I'll leave repayments and the ledger out; that's a servicing system with its own hard problems. Same for
> how models are trained: I'll treat a model as a versioned artefact we load. And merchant fraud is a
> merchant-risk system; I'll name where it would plug in."

::: {.key title="The core is three things"}
An **orchestrator** that decides under one deadline with a policy for whatever is missing; a **state
machine** whose only atomic step is accept to book; and a **record and a vault**: what we keep to explain
the decision, and the small box where identity lives.
:::

# Stage 2: Back-of-the-envelope

## How to do estimates in this round

The numbers in this question are small, and that is the point. Do three calculations out loud, each with
the decision it drives, and move on. A candidate who spends ten minutes on storage per year is showing that
they did not notice the load is not the problem.

::: {.key title="Top-3 number 1: the load"}
**Arithmetic.** 2 × 10^6^ applications ÷ (30 × 86,400 s) $\approx$ 0.8 a second; at a 10× Saturday peak, about
8 a second. Each application fans out to about four vendor calls: about 32 calls a second.
**What it means.** Any relational database takes 8 applications and about 50 committed transitions a
second without noticing.
**How it changes the design.** One replicated relational primary. No sharding, no exotic store. The
engineering effort goes to the slow edges and to one transaction.
**Say:** "Eight a second at peak. One relational database holds every application; the hard part is
the vendors."
:::

::: {.key title="Top-3 number 2: the bureau bill"}
**Arithmetic.** 2 × 10^6^ pulls × about $1 $\approx$ $2M a month, if every application pulls. If 20 % of applicants
re-apply within thirty days and a recent report may be reused, 4 × 10^5^ × $1 $\approx$ $400k a month saved.
**What it means.** The vendor invoice is far larger than the compute bill.
**How it changes the design.** Never race two bureaus; store reports for reuse inside the window the
bureau contract and the law allow; count spend per vendor per hour like latency.
**Say:** "The biggest line on the bill isn't servers, it's bureau pulls: about two million a month. So no
hedged requests, and a report store with a reuse rule."
:::

::: {.key title="Top-3 number 3: the missing-data path"}
**Arithmetic.** If about 2 % of bureau calls miss a two-second deadline and about 1 % fail, about 3 % of
applications reach the deadline without a bureau answer: about 60,000 a month, about 14 a minute at the
Saturday peak.
**What it means.** "The bureau didn't answer" is not an edge case; it happens every minute of every busy
day.
**How it changes the design.** The missing-data policy is a first-class, versioned, owned part of the
decision, with counters and caps, not a catch block.
**Say:** "About three percent of applications hit the deadline without a bureau. That's a weekly volume of
sixty thousand, so what we do then is a policy, not an exception handler."
:::

## The full table

| Number | Arithmetic | Label | Decision it drives |
|---|---|---|---|
| Applications | 2 × 10^6^ ÷ 2.6 × 10^6^ s $\approx$ **0.8/s**; peak × 10 $\approx$ **8/s** | given → derived | One relational primary |
| Database transitions | 8/s × about 6 $\approx$ **50 writes/s** | derived | Every transition can be a committed row |
| Vendor calls | 8/s × 4 $\approx$ **32/s**; in flight 32 × 2 s $\approx$ **64** | derived | Per-vendor concurrency and rate limits matter more than our capacity |
| Bureau bill | 2 × 10^6^ × $1 $\approx$ **$2M/month** | illustrative | The largest cost line |
| Report reuse | 4 × 10^5^ × $1 $\approx$ **$400k/month** saved | illustrative | A report store with a retention rule |
| Identity checks | 2 × 10^6^ × $0.05 $\approx$ **$100k/month** | illustrative | Also paid per call; not raced either |
| Decision records | 2 × 10^6^ × 50 KB $\approx$ **100 GB/month**; × 84 $\approx$ **8.4 TB** | illustrative | Object storage, encrypted, referenced from the database |
| Loans | 2 × 10^6^ × 60 % × 70 % $\approx$ **840,000/month**; × $1,200 $\approx$ **$1.0B/month**; $\approx$ **28,000/day** | illustrative | Funding is a daily batch per merchant |
| Missing data at the deadline | $\approx$ 3 % $\approx$ **60,000/month** | illustrative, to measure | The policy table is a busy path |
| A 20-minute bureau outage at peak | 8 × 1,200 $\approx$ **9,600** applications; approve all $\approx$ **$11.5M** unscored; decline all $\approx$ 9,600 × 60 % × 70 % $\approx$ **4,000** lost loans | derived | Neither extreme: a capped policy (6.2) |
| Latency budget | 150 + 50 + 2,000 + 100 + 80 + 70 + 50 + 200 = **2,700 ms**, spare 300 | initial target | One deadline; nothing optional on the path |

![The latency budget from submit to offers on screen, with the vendor deadline as the largest slice.](diagrams/video-budget.pdf){width=95%}

::: why
**Why the deadline is two seconds and not three.** The customer's promise is three seconds at the 95th
percentile from submit to offers on screen. The phone-to-API hop, the state write, the model, policy,
pricing, the record and the push to the phone take about 700 ms together. What is left for the vendors is
about two seconds, with 300 ms of spare for a slow network. The deadline is derived from the promise, not
picked from experience.
:::

::: warn
**The thundering-herd reflex.** A candidate hears "Saturday peak" and reaches for queues, autoscaling and
sharding. Eight a second is not a herd. Say the number, say what it means, and spend the time on the
vendors.
:::
