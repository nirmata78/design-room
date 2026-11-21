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

# Stage 6: Deep dives

The bridge sentence, said aloud: **"It works. Where does it break first?"** Then show the challenge map
and take the challenges in an order where each fix creates the next question.

![The challenge map: eight attack points on the same baseline.](diagrams/video-map.pdf){width=100%}

| # | Challenge | Kind | Mechanism that answers it |
|---|---|---|---|
| 6.1 | The bureau is slow | latency, crux part 1 | scatter-gather under one deadline, a breaker per vendor |
| 6.2 | The bureau is down for everyone | failure and policy, crux part 1 | a signed missing-data table with caps; refer |
| 6.3 | The phone drops | correctness, crux part 2 | a conditional update, a unique loan, the outbox |
| 6.4 | Funding fails after booking | failure recovery, crux part 2 | funding as its own state machine; UNKNOWN as a state |
| 6.5 | Explain a decision fourteen months later | correctness and regulation | an immutable decision record; nightly replay |
| 6.6 | A new model approves six percent more | trade-off | backtest, shadow, a capped challenger slice |
| 6.7 | Where identity data lives | security | a vault with tokens |
| 6.8 | How would you know it is broken? | observability | SLIs on the decision; symptom pairs |

## 6.1 The bureau is slow (latency)

**The question.** *"One bureau call in ten takes four seconds today. What does the customer at the
counter see?"*

**The naive answer.** "Wait for it, and if it's slow, send the same request to the second bureau and
take whichever answers first." Hedged requests are a good answer for an internal read-only service. They
are the wrong answer here, and the interviewer asked the question to find out whether you know why.

![The vendors break: waiting misses the promise; racing pays twice.](diagrams/video-ch1-attack.pdf){width=100%}

**The case.**

| Time | Event |
|---|---|
| 10:00:00.000 | Submit from the phone |
| 10:00:00.050 | Identity, fraud and bureau A called |
| 10:00:00.350 | Fraud answers |
| 10:00:00.400 | Identity answers |
| 10:00:01.000 | Hedge: the same pull sent to bureau B |
| 10:00:01.700 | Bureau B answers; offers shown at about 2.0 s |
| 10:00:04.100 | Bureau A answers: a second paid pull, a second inquiry on the customer's file |
| without the hedge | offers at about 4.4 s, past the 3 s promise |

Each pull costs about a dollar and may appear on the customer's credit file as an inquiry. Racing two
bureaus doubles the bill for every slow call and can hurt the very customer you are serving.

**The fix: scatter-gather under one deadline, and a breaker per vendor.**

![The orchestrator owns time: one deadline, a breaker per vendor.](diagrams/video-ch1-fix.pdf){width=100%}

All required calls go out at once. The orchestrator decides at the deadline (2.0 s from the start of the
calls) with what has arrived; if everything arrives earlier, it decides earlier. Each vendor adapter has a
circuit breaker: when a vendor's error rate or tail latency crosses a threshold over a window, the breaker
opens and the adapter stops calling that vendor for everyone, so no customer waits for a vendor that is
known to be failing. The second bureau is called **only after an error or an open breaker**, never as a
race against a slow but healthy first call.

![The gather in time: the late answer is recorded and used to finish a refer.](diagrams/video-seq-ch1-gather.pdf){width=95%}

**Why it works.** L1 (an answer within the deadline) is bounded by the deadline, not by the slowest
vendor. S4 (at most one pull per bureau per application) holds because a second bureau is asked only
when the first has failed, not when it is slow.

**"What if the fix fails?"** *"The bureau's answer arrives at 4.1 seconds, after you decided. What do you
do with it? You paid for it."*

**The second fix.** Record it: the call happened and was billed, so it is a fact in `vendor_call`. If the
application was referred because the bureau was missing, the late answer finishes it: the customer gets a
text with offers. If the application was already offered or declined, the late answer does not change what
the customer saw, because the decision record says what we knew at the time; it is kept as evidence and,
where the contract allows, in the report store for a re-application. The honest limit: a deadline means
about 3 % of applications reach the missing-data path every day, which is the next question.

> "All vendors at once, one deadline, a breaker per vendor. I never race two bureaus, because each pull
> is paid and may show on the customer's file. A late answer is recorded and used to finish a refer, never
> to change what the customer saw."

::: warn
**"Set a three-second timeout on the bureau."** A timeout per call is not a deadline per decision. With
three vendors each on a three-second timeout in sequence, the wait is nine seconds; in parallel, each
still allows three seconds and leaves nothing for the model and the push. Derive one deadline from the
promise.
:::

## 6.2 The bureau is down for everyone (failure and policy)

**The question.** *"Bureau A is down for everyone for twenty minutes on a Saturday. What happens at the
counter?"*

**The naive answers.** "Approve with whatever data we have" or "decline until it's back." Both are
engineering decisions about credit risk, made in a catch block.

![The vendors and the policy break together: both extremes are expensive.](diagrams/video-ch2-attack.pdf){width=100%}

**The case.** From 11:00 to 11:20 on Saturday, at about 8 applications a second: 8 × 1,200 s $\approx$ 9,600
applications. Approve all of them without a credit file and we offer about 9,600 × $1,200 $\approx$ $11.5M of
credit nobody scored. Decline all of them and we lose about 9,600 × 60 % × 70 % $\approx$ 4,000 loans, and we owe
9,600 decline notices whose only true reason is "our vendor was down", which is not a reason about the
applicant.

**The fix: a missing-data policy table, signed by credit risk.**

![The policy engine holds a signed table for missing data.](diagrams/video-ch2-fix.pdf){width=100%}

![Four answers, in order, each with its own cap.](diagrams/video-policy.pdf){width=100%}

1. **The second bureau**, after the breaker on the first has opened. Not a race: the first is known to be
   failing.
2. **Decide without a bureau** only for returning customers in good standing (for example, three or more
   on-time payments on a previous loan), for at most $500, under a daily exposure cap of $250,000
   (illustrative): at most 500 such loans a day.
3. **Refer.** "We'll finish in about two minutes by text." The merchant's screen says *pending*, not
   *declined*. The application waits in a refer queue and is finished when a bureau answers.
4. **Decline**, only with a reason about the applicant, which needs data we have.

Each row is a versioned setting in the policy, with a counter per row and a dashboard, signed by credit
risk and approved by the partner bank as part of the credit policy. Engineering builds the mechanism;
credit risk owns the numbers.

![A referred application finished by text when a bureau answers.](diagrams/video-seq-ch2-refer.pdf){width=95%}

**Why it works.** S2 holds: nobody is declined for our outage. L1 holds: everybody gets an answer (an
offer, a refer, a reasoned decline) within the deadline. And the exposure is bounded by arithmetic: the
daily cap is the worst case, whatever happens to the vendor.

**"What if the fix fails?"** *"Bureau B's contract allows five calls a second. You're sending eight."*

**The second fix.** A token bucket per vendor at the contract rate: five tokens a second for bureau B.
Calls beyond it are not sent; those applications go to refer. The refer queue is drained oldest first when
tokens free up or when bureau A's breaker half-opens and a probe succeeds, inside the ten-minute promise.
The exposure cap for row 2 is split per merchant, so one busy merchant cannot spend the whole day's cap in
an hour. In twenty minutes at three a second over the limit, about 3,600 applications are referred. The
honest limit: some referred customers walk away; measure the refer completion rate and the lost sales per
minute of outage, and give those numbers to credit risk when they set the caps.

> "Every timeout is a credit decision with an owner. Credit risk signs a table: second bureau, small known
> customers under a daily cap, refer, or decline with a real reason. Engineering makes it a setting with a
> counter, a cap and a dashboard."

::: why
**Why "refer" is the senior insight.** A declined applicant must be told the principal reasons for the
decline. If the only reason is that a vendor did not answer, the decline is both wrong for the customer and
hard to defend. *Refer* turns a bad decision into a delayed one. It costs a queue and a text message.
:::

## 6.3 The phone drops (correctness)

**The question.** *"The customer taps accept, the phone loses signal, and they tap again on the
merchant's tablet. How many loans?"*

**The naive answers.** "Check whether a loan exists, and create one if it doesn't." Or: "an orchestrated
saga with a compensating action for each step."

![The application service and the database break: two workers, one application.](diagrams/video-ch3-attack.pdf){width=100%}

**The case.**

| Time | Event |
|---|---|
| 14:31:07.200 | Phone posts accept, idempotency key k1 |
| 14:31:07.900 | The response is lost in the shop's dead zone |
| 14:31:08.050 | Tablet posts accept, key k2 (another device, another key) |
| 14:31:08.060 | Worker 1 reads ap_91: OFFERED, version 7; no loan |
| 14:31:08.070 | Worker 2 reads ap_91: OFFERED, version 7; no loan |
| 14:31:08.090 | Both insert a loan: **two loans**, two funding transfers of $1,200 tonight, the customer billed twice |

Idempotency keys alone do not save this case: the two requests came from two devices with two keys.
Check-then-insert does not save it either: both checks ran before either insert.

**The fix: one local transaction.**

![The database decides: a conditional update, a unique loan, the outbox row in the same commit.](diagrams/video-ch3-fix.pdf){width=100%}

```sql
BEGIN;
UPDATE application SET status = 'BOOKED', version = 8
 WHERE id = 'ap_91' AND status = 'OFFERED' AND version = 7;
-- 0 rows: someone else booked (or the offer expired): ROLLBACK and return the existing loan
INSERT INTO loan (id, application_id, offer_id, disclosure_v, terms)
VALUES ('ln_5531', 'ap_91', 'of_3', 'v7', '{"months": 6, "apr_bps": 1490}');
INSERT INTO outbox (event_id, type, payload)
VALUES ('ev_77', 'LoanBooked', '{"loan_id": "ln_5531", "application_id": "ap_91"}');
COMMIT;
```

The conditional update lets exactly one writer through: the second worker's update matches zero rows,
because the first changed the status and the version. The unique constraint on `loan.application_id` is
a second wall, in case a code path forgets the update. The outbox row commits with the loan, so "the loan
exists" and "the world will hear about it" are one fact. The second device's request reads the
application, finds it BOOKED, and returns `ln_5531`.

**Why it works.** S1 is enforced by the database, the one place that sees both writers. No distributed
coordination, no lock held across a network call.

**Why not a saga.** The table below is worth drawing in the round.

| Step | Can it be undone? | So |
|---|---|---|
| Identity check, credit pull | No: it happened, it was paid, it may be on the customer's file | Record it; never "compensate" |
| Offer | Expires by itself | A lifetime, no action |
| Accept → book | Must be atomic | One local transaction with the outbox |
| Fund the merchant | Yes, by a reversal or a return | Asynchronous, retried, reconciled (6.4) |

A saga is a fine tool when several steps each change state that can be undone. Here only one step after
booking can be undone, and everything before booking is either a fact or expires.

**"What if the fix fails?"** *"The commit succeeded, but the relay crashed before publishing. Or it
published twice."*

**The second fix.** The relay is at least once by design: it reads unpublished outbox rows, publishes,
and only then marks them published. A crash between the two publishes the event again on restart. So
every consumer de-duplicates by `event_id`, and funding uses the loan ID as its idempotency key at the bank,
so even a duplicate that slips through cannot pay twice. The honest limit: this is at least once plus
idempotent consumers, not "exactly once".

> "Only one step is atomic: accept to book. A conditional update at a version, a unique constraint on the
> application, and the outbox row in the same commit. A second tap finds the loan and shows it. The event
> is at least once, and every consumer de-duplicates."

## 6.4 Funding fails after booking (failure recovery)

**The question.** *"The loan is booked. The transfer to the merchant is rejected, or the bank times out.
What do you undo?"*

**The naive answer.** "Roll back the saga: cancel the loan, reverse the credit check, delete the
application."

![Funding breaks after the customer has left.](diagrams/video-ch4-attack.pdf){width=100%}

**The case.** At 14:31 loan `ln_5531` is booked. At 18:00 the daily funding batch sends $1,164 (the
$1,200 less a 3 % merchant fee) to the merchant. At 18:02 the bank returns *account closed*. At 18:03 a
second merchant's transfer, for another loan, times out with no answer at all. Re-sending both "to be
safe" would pay the second merchant twice if its first attempt actually went through.

**The fix: funding as its own state machine, with UNKNOWN as a state.**

![Funding owns its states; reconciliation closes the gaps.](diagrams/video-ch4-fix.pdf){width=100%}

| State | Meaning | Next |
|---|---|---|
| PENDING | In tonight's batch | SENT |
| SENT | The bank acknowledged the instruction | SETTLED, RETURNED |
| UNKNOWN | We asked and got no answer | query the bank by our key; never resend |
| RETURNED | The bank rejected or returned it | merchant operations fixes the account; a new attempt |
| SETTLED | Money arrived | done; reconciled |

Every transfer carries our idempotency key (the loan ID and the attempt number), so the bank can tell us
whether it already has the instruction. A timeout becomes **UNKNOWN**, and the only allowed action on
UNKNOWN is to ask, not to send. A *returned* transfer goes to merchant operations, who fix the account,
and a new attempt is sent with a new attempt number. The loan itself is cancelled only if the goods were
not delivered, and that is a business decision with the merchant, not a rollback.

![The unknown transfer, resolved by the next day's file rather than by a resend.](diagrams/video-seq-ch4-fund.pdf){width=95%}

**Why it works.** L2 (every booked loan eventually funded, with one effect): the loan ID is the
idempotency key end to end, and UNKNOWN keeps "maybe paid" from becoming "paid twice".

**"What if the fix fails?"** *"The bank's status API says 'not found' for the timed-out transfer, and the
file tomorrow shows it paid."*

**The second fix.** "Not found" in the first minutes after a timeout does not mean "not sent": many
bank interfaces index instructions asynchronously. So no resend happens before the reconciliation window
closes. Daily reconciliation compares three things: our funding records, the bank's settlement file, and
the loans booked. Every difference is a *break* with an owner and an age; breaks older than two days page
someone. The honest limit: some outcomes are only known the next day, so the merchant's portal says *in
progress*, not a guess.

> "The credit pull and the booking aren't compensated: they happened. The one step with a real undo is
> funding, so it's its own state machine after booking, with UNKNOWN as a state: query, never resend.
> Reconciliation against the bank file closes the gap."

## 6.5 Explain a decision fourteen months later (correctness and regulation)

**The question.** *"A regulator asks why a customer was declined fourteen months ago. Reproduce it."*

**The naive answer.** "Re-run the model on the customer's data."

![The policy engine only knows today.](diagrams/video-ch5-attack.pdf){width=100%}

**The case.** In January 2026, application `ap_204` was declined by model v9 under policy v31, with
reasons *high utilisation* and *short history*, and the customer was sent a notice saying so. In March
2027 someone re-runs today's model v14 on today's bureau file, and it approves. Now we hold a notice that
says one thing and a replay that says another, and neither tells the regulator what actually happened.

**The fix: an immutable decision record.**

![The record is written once by the orchestrator.](diagrams/video-ch5-fix.pdf){width=100%}

![What a decision record holds.](diagrams/video-record.pdf){width=100%}

Every decision writes, once, a record of three parts. **Inputs, frozen**: the bureau report stored
encrypted and referenced, the identity and fraud results, our internal history *as of that moment*, the
feature vector actually used, and which calls were missing. **Versions**: model, policy (including the
missing-data table), pricing, disclosure, and the orchestrator build. **Outputs**: the outcome, the offers,
the ranked reasons, the degraded path taken, the timings and the deadline. Old model artefacts stay
loadable in a registry. A replay job runs every night on a sample of records: it loads the versions,
re-scores the frozen features and alarms on any difference.

![The replay: load the record, load the old versions, re-score, compare.](diagrams/video-seq-ch5-replay.pdf){width=95%}

**Why it works.** S2: the same inputs and the same versions give the same answer. And the nightly replay
proves it continuously, instead of on the day the regulator asks.

**"What if the fix fails?"** *"The customer asks us to delete their data. The record holds their bureau
report."*

**The second fix.** Retention duties for credit records generally take precedence for their period, and
that call belongs to compliance, not engineering. Within the period, the record holds tokens rather than
identity and an encrypted report under a key per record; access is restricted to the purposes the rules
allow. At the end of the retention period the record's key is destroyed (crypto-shredding), which makes
every copy unreadable, backups included, without hunting for them. The honest limit: a deletion request
inside the retention period is answered by restricting use, and the customer is told so.

> "I never re-run today's model to explain yesterday. Every decision freezes its inputs, the versions of
> model, policy and pricing, and the ranked reasons. A nightly replay proves records still reproduce, and
> retention ends by destroying the record's key."

::: why
**Why "reasons" are ranked and stored, not computed later.** Reason codes come from the model and the
policy together: the features that pushed the score down most, mapped to plain language, plus any policy
rule that fired. Computing them later from a different model version gives different reasons. Store what
you told the customer.
:::

## 6.6 A new model approves six percent more (trade-off)

**The question.** *"Data science has a new model. It approves six percent more people at the same
predicted loss. Roll it out."*

**The naive answers.** "Shadow mode for a week; it looks good; switch it on." Or "a fifty-fifty A/B test."

![The policy engine is where the risk of a new model lands.](diagrams/video-ch6-attack.pdf){width=100%}

**The case.** Six percent of two million is 120,000 more approvals a month; at 70 % take-up, about 84,000
more loans, about $100M a month of new exposure. The first payments of those loans fall due in two to four
weeks; losses only show at 90 to 120 days. A week of shadow mode shows the approval rate. It shows nothing
about whether the newly approved people repay. A fifty-fifty test puts $50M a month at risk to learn it.

**The fix: champion and challenger, in steps that each see what the one before cannot.**

![A challenger beside the champion, deciding only a capped slice.](diagrams/video-ch6-fix.pdf){width=100%}

![From backtest to a policy change.](diagrams/video-rollout.pdf){width=100%}

1. **Backtest** on labelled history: approval and loss on past loans the old model approved.
2. **Shadow**: both models score every application; only the champion acts. Compare approval rates and
   reason codes by segment and by protected group.
3. **Challenger slice**: the challenger decides 5 % of traffic under its own exposure cap. The extra
   approvals in the slice are about 5 % of 120,000 = 6,000 a month, about 4,200 loans, about $5M a month,
   signed by credit risk and the partner bank.
4. **Early signals** at 30 to 45 days: the first payment missed, compared between champion and challenger
   approvals of similar people.
5. **Widen** only through a policy version change, with a kill switch per version.

**Why it works.** S2 is kept: each record says which model decided. And the exposure of learning is
bounded by the slice cap, not by optimism.

**"What if the fix fails?"** *"Shadow looked great. Why isn't that enough?"*

**The second fix.** Shadow cannot see outcomes for the people only the challenger would approve: the
champion declined them, so they never got a loan and have no repayment label. Only a slice where the
challenger actually decides produces labels for them. Fairness checks run on shadow (who would be
approved) and on the slice (who repays). The honest limit: a slice is real money at risk; the cap is the
price of learning, and credit risk owns that price.

> "Shadow tells you who the new model would approve, not whether they repay. So: backtest, shadow, then a
> capped slice where the challenger decides, early signals at thirty days, fairness by group, and every
> step a policy change with a kill switch."

## 6.7 Where identity data lives (security)

**The question.** *"The analytics team wants application data to train the next model. What do they
get?"*

**The naive answers.** "A copy of the database; we encrypt it at rest." Or "we drop the name column."

![Identity spread through rows, logs and exports.](diagrams/video-ch7-attack.pdf){width=100%}

**The case.** In V2 the application table holds a social security number, a date of birth and an address.
A debug log line in the bureau adapter prints the full request. The support tool shows the full number to
every agent. The training extract drops names but keeps date of birth and postcode, which together
re-identify most people. One leaked extract leaks two million identities a month. Encryption at rest
protects a stolen disk; it does nothing for a query, a log line or an export.

**The fix: an identity vault with tokens.**

![Only the vault and the vendor adapters see real values.](diagrams/video-ch7-fix.pdf){width=100%}

![The boundary, drawn small on purpose.](diagrams/video-vault.pdf){width=95%}

Identity is tokenised at apply. Only two things sit inside the boundary: the vault itself and the vendor
adapters, which must send the real values to the bureau and the identity vendor. Every detokenise is
logged with its caller and purpose. Rows, logs, decision records, support tools and the event log carry
tokens or masked values. Training gets derived features (utilisation, history length, income band), not
identity. Adapter logs are scrubbed at the source.

Know the rulebook, because the interviewer may test it: **card numbers** fall under the card industry's
security standard; a **social security number** falls under privacy and lending law. Quoting the card
standard for identity data is a common slip.

**Why it works.** S3 by construction: a leak anywhere outside the boundary leaks tokens.

**"What if the fix fails?"** *"The vault is down."*

**The second fix.** The vault is a tier-0 dependency, so it is kept small, with no business logic,
replicated across zones, with its own 99.95 % objective and its own on-call. If it is down, apply cannot
tokenise and the adapters cannot detokenise; applications are referred and the merchant sees *pending*.
Nothing raw is ever cached outside the vault "to help". The honest limit: the vault being small is what
makes it reliable; resist every feature request that would grow it.

> "They get tokens and derived features, never identity. Only the vault and the vendor adapters see real
> values, every access is logged, and a leak anywhere else leaks tokens. And I'd name the right rulebook:
> identity data is privacy and lending law, not the card standard."

## 6.8 How would you know it is broken? (observability)

**The question.** *"Your dashboards are green. How would you know decisions are going wrong?"*

**The naive answer.** "Error rate, latency and CPU."

![The change that broke decisions raised no error.](diagrams/video-ch8-attack.pdf){width=100%}

**The case.** At 18:00 on Friday a pricing-table change maps one bureau field wrongly. No errors; latency
is fine; CPU is flat. The approval rate across all merchants drops from 62 % to 41 %. At about two
applications a second in the evening that is 7,200 an hour and about 1,500 wrongly declined each hour,
each with a notice. It is found at 09:00 on Saturday when merchants start calling: fifteen hours, about
22,000 customers if the evening rate held (illustrative).

**The fix: SLIs on the promise and on the decision, read in pairs.**

![What to watch: the decision, the fallbacks, the money.](diagrams/video-ch8-fix.pdf){width=100%}

| SLI | Why it pages |
|---|---|
| Offers on screen within 3 s, p95 | The promise at the counter |
| Approval rate per merchant per hour, against its own baseline | A sudden drop is almost never the customers |
| Fallback rate per policy row, against its cap | Credit risk said "capped": prove it |
| Loans booked and not funded after one hour (batch-aware) | Money owed to a merchant |
| Vendor errors, latency and spend per hour | The largest cost line and the deadline's enemy |
| The mix of decline reasons | A new dominant reason is a change, not a population |

| When you see | Together with | It means |
|---|---|---|
| Approval down | Vendor errors flat, a deploy at the same time | Our change |
| Refer rate up | A breaker open | An outage being handled as designed |
| Offer latency up | Breakers closed | A vendor slow but under the breaker's threshold |
| Booked up | Funded flat | Funding stuck |
| One decline reason jumps | Feature distribution shifted for one bureau | A vendor changed a field |

Policy and pricing changes ship as canaries: a small slice first, with the approval-rate alarm armed.

**"What if the fix fails?"** *"Approval drops at one merchant only."*

**The second fix.** Per-merchant baselines by hour of the week. A drop at one merchant is usually an
integration bug (amounts sent in dollars instead of cents) or a fraud ring testing stolen identities, and
it goes to merchant operations or fraud, not credit. The honest limit: small merchants have noisy
baselines; alarm on totals over a window, not on one hour.

> "I watch the decision, not the servers: offers in three seconds, approval rate per merchant per hour
> against its baseline, fallback rate against the cap, and loans booked but not funded. Two metrics
> together tell me whether it's us, a vendor or one merchant."

## 6.9 How the whole system degrades, in priority order

| What fails | What still works | What the customer sees |
|---|---|---|
| One bureau slow | Everything; the deadline decides | Offers, rarely a refer |
| One bureau down | Second bureau, small known customers, refer | Offers or *we'll text you* |
| Both bureaus down | Small known customers under the cap, refer | Mostly *we'll text you* |
| Identity vendor down | Returning customers already verified; refer | *We'll text you* |
| Policy engine down | Nothing decides; apply still records | *Pending*; refer queue fills |
| Vault down | Nothing new starts; booked loans continue | *Pending* |
| Database primary lost | Failover to the standby in seconds; in-flight requests retry by key | A short pause |
| Event log down | Booking continues; the outbox holds events | Nothing; funding later |
| Funding down | Loans booked; merchants paid in the next batch | Nothing at the counter |

# Stage 7: Requirements that arrive mid-round

Interviewers often add a requirement two thirds of the way through. The strong answer names the seam that
absorbs it, what changes, what does not, and what it costs.

**"Product wants cash-flow underwriting: read the customer's bank account."** Bank-account data arrives
through an aggregator in seconds to minutes, after the customer consents in a separate flow. It is never
awaited at the counter. *What changes:* a new vendor adapter; a new optional input to the policy; a new
row in the missing-data table ("bank data absent: decide on the bureau alone"); the refer path can wait
for it when the policy asks. *What doesn't:* the deadline, the state machine, booking. *Cost:* a consent
flow, a vendor contract, and more data inside the vault boundary.

**"Merchants want a pre-approval: the customer checks their limit at home before visiting."** A soft
inquiry that does not affect the customer's file, a decision with an offer valid for thirty days, and at
the counter only a re-check. *What changes:* a new application type with a longer expiry; the decision
record must say it was a soft inquiry; the counter path can skip the bureau if the pre-approval is fresh
and the policy allows. *What doesn't:* booking. *Cost:* exposure from offers that live for weeks; credit
risk sets a cap on outstanding pre-approvals.

**"We're launching in a second country."** Different bureaus, different rules on reasons and retention,
possibly a different lender of record, and data that must stay in the country. *What changes:* a regional
deployment with its own vault and records; vendor adapters per country; policy and disclosures versioned
per country. *What doesn't:* the mechanisms. *Cost:* a second compliance owner and a second on-call.

**"The partner bank wants to buy each day's loans at 17:00."** A loan-sale file built from the booked
loans of the day, reconciled against the bank's purchase confirmation. *What changes:* a consumer of
LoanBooked that builds the file; a reconciliation break type. *What doesn't:* the counter. This is the
event log earning its place.

# Stage 8: Failures and reliability

| Failure | Blast radius | Detection | Response |
|---|---|---|---|
| Bureau slow | about 3 % of applications take the policy path | latency per vendor; fallback rate | none needed: the deadline decides |
| Bureau down | refer and fallback rates jump | breaker open; refer rate | policy table; per-vendor rate limits; status to merchants |
| Policy or pricing bug | every decision | approval rate per merchant per hour; reason mix | canary; kill switch to the previous version |
| Model artefact fails to load | decisions stop | readiness check; decide errors | keep the previous version loaded; roll back |
| Database primary lost | writes pause for the failover | health checks | synchronous standby; requests retry by idempotency key |
| Relay stuck | funding and servicing delayed | outbox age | restart; events are still in the table |
| Vault down | nothing new starts | vault SLI | refer; page security on-call |
| Funding transfer unknown | one merchant's money | UNKNOWN count and age | query, wait for the file, never resend |
| Notices fail | declined customers not told in time | notices due against sent | retry; the deadline for notices is days, not seconds |

**One incident, walked through.** Saturday 11:00: bureau A starts timing out. At 11:00:20 its breaker
opens on the error rate over the last twenty seconds. The orchestrator stops calling it; the policy table
sends eligible applications to bureau B at five a second, returning customers under $500 to the no-bureau
row, and the rest to refer. The refer rate climbs from 0.5 % to about 35 %; an alert fires and the on-call
engineer confirms the breaker, checks the refer queue age (under two minutes) and the cap counter for the
no-bureau row (about $40,000 of $250,000). Merchant operations posts a status banner: *some approvals are
taking a few minutes*. At 11:20 the breaker half-opens, probes succeed, it closes, and the refer queue
drains oldest first. The post-incident review reports refer completion (illustrative: 81 %), the exposure
used, and the spend at bureau B, and credit risk decides whether the caps were right.

# Stage 9: SLOs, observability, cost

| SLI | How it is measured, from outside | Objective (initial target) |
|---|---|---|
| Offers on screen | submit to offers at the phone SDK, p95 | under 3 s, 99 % of hours |
| Decision availability | answers (offer, refer, decline) over submits | 99.9 % in merchant hours |
| Refer completion | referred applications finished within 10 minutes | 95 % |
| Booking correctness | duplicate loans found by the nightly check | zero |
| Funding | loans funded within one business day | 99.5 % |
| Replay | sampled records that reproduce | 100 % |
| Vault | tokenise and detokenise success | 99.95 % |

**A synthetic application**, every minute, in each region: a test merchant, a test identity the bureaus
provide for testing, through apply, decide and a cancelled accept. It measures the promise end to end.

**The dashboard**, top to bottom: offers latency; approval rate per merchant (a heat map against
baselines); fallback rate per policy row with its cap; refer queue age; vendor latency, errors and spend;
booked-not-funded; replay mismatches; vault health.

**Cost, illustrative.** Bureau pulls about $2M a month; identity checks about $100k; compute and storage
a small fraction of either. The levers: report reuse inside the contract's window (about $400k a month);
the second-bureau rule (no races); asking the bureau only when the policy needs it (a returning customer
with a recent report may not); and negotiating the contract with spend data per merchant segment.

# Stage 10: The EM layer (auxiliary at Staff)

**Phasing.** V1 (one service, sequential calls, one table): three engineers, two months, to learn the
vendors. V2 (orchestrator, state machine, outbox, versioned policy engine): a team of six for two
quarters. V3 (vault, records, policy table, funding, notices, champion and challenger): two teams for two
more quarters, plus security and compliance time. The riskiest work first: the vendor adapters and the
policy table, because they decide whether the counter promise can be kept.

**Team seams.**

![Six owners, three contracts.](diagrams/video-teams.pdf){width=95%}

Applications and origination own the state machine and booking. The decisioning platform owns the
orchestrator, the policy engine and model serving. Vendor integrations own the adapters, the contracts and
the spend. Security owns the vault. Credit risk and data science own the models and every degraded path
and its cap. Compliance owns disclosures, notices and retention. The contracts between them are the
decision interface, the decision record and the LoanBooked event.

**With half the team.** Keep the deadline, the policy table, the atomic booking and the records. Buy the
vault. Defer champion and challenger (run one model; change it rarely, with a backtest and shadow) and
cash-flow underwriting.

**On-call.** Engineering pages on the SLIs; credit risk is paged by the fallback-rate and cap alarms,
because they own the decision behind them. A runbook per vendor: how to read its status, who to call at
the vendor, which policy rows change when it is down.

**Buy against build.** Bureaus, identity and bank-data vendors are bought. A tokenisation vault is a
reasonable buy. A workflow engine is a buy if steps grow to days. The orchestrator, the policy engine and
the records are ours: a regulator asks us, not a vendor, why someone was declined.

# Stage 11: The close

> "What I built: an application that's a small state machine in one database, with one atomic step,
> accept to book, and an outbox. The trade-off I chose: one deadline with a signed policy for whatever is
> missing, rather than waiting or racing paid vendors. The risk I'd watch: a degraded path or a model
> change without an owner and a cap. Next: the challenger pipeline and cash-flow data, behind the same
> policy table."

# Stage 12: Self-check after a simulator run

| Area | Weak | Strong | Exceptional |
|---|---|---|---|
| Framing | Treats it as a throughput problem | Says the load is tiny and the vendors are the problem | Asks who the lender of record is and what that changes |
| Latency | Sequential calls; hedged bureau requests | One deadline, parallel calls, breakers | Derives the deadline from the promise; per-vendor rate limits |
| Missing data | "Approve with partial data" in code | A policy table with refer | Every row owned, capped, counted; "a timeout is not a reason" |
| Correctness | Check-then-insert; a saga for everything | Conditional update, unique loan, outbox | Says which steps are facts, which expire, which can be undone |
| Money | Funding inside the request | Funding after booking, retried | UNKNOWN as a state; reconciliation with breaks and owners |
| Explainability | "The model returns a score" | Versions and reasons stored | Frozen inputs, nightly replay, crypto-shredding at retention end |
| Models | Shadow, then switch | Champion and challenger with a slice | Says why shadow cannot measure loss; fairness by group |
| Identity | "Encrypt the database" | A vault with tokens | The right rulebook; the vault kept small and tier-0 |
| Operations | CPU and errors | Offers latency, approval rate | Symptom pairs; canaries for policy changes; credit risk on the pager |

**Common traps.** Treating it as a throughput problem. Sequential vendor calls. Hedging paid pulls.
"Approve with partial data" as a code default. A saga that compensates a credit pull. Check-then-insert on
the loan. Re-running today's model to explain yesterday. "Encrypt the database" as the identity answer.
Quoting the card standard for a social security number. No owner for any degraded path.

\newpage

# Part III: The internals

## Appendix A: Scatter-gather with one deadline

A deadline is a point in time, not a duration per call. The orchestrator computes it once (the start of
the vendor calls plus two seconds) and every wait uses the time left until it. Calls that finish early
free the decision early. Calls that are late are not cancelled: their answers are recorded when they
arrive. Three details matter in practice. **Required against optional**: the policy says which inputs are
required for which application (a returning customer may not need a fresh bureau report); optional inputs
are never awaited. **Fan-out limits**: each vendor has a concurrency limit in the adapter, so a burst of
applications cannot open hundreds of connections to a vendor that throttles. **Clock**: the deadline is
measured on the orchestrator's monotonic clock, never on wall time, so a clock adjustment cannot extend or
shorten it.

## Appendix B: Circuit breakers and token buckets

A breaker has three states. **Closed**: calls flow; the adapter counts errors and slow calls over a
rolling window (for example twenty seconds). When the error rate or the share of calls slower than a
threshold crosses a limit, it **opens**: calls are refused immediately and the policy treats the vendor as
missing. After a cool-down it goes **half-open**: a few probe calls go through; if they succeed, it closes;
if not, it opens again. Two mistakes to avoid: a window so short that one slow second opens it, and a
breaker per server rather than per vendor, which lets each server rediscover the outage separately. A
**token bucket** at the vendor's contract rate is separate from the breaker: a healthy vendor can still be
over its contract. Tokens refill at the contract rate; a call without a token is not sent, and the
application follows the policy (usually refer).

## Appendix C: Optimistic versions and the conditional update

An optimistic lock does not lock anything while the request is thinking. The worker reads the row and
its version, does its work, then writes with `WHERE version = <what I read>`. If another worker wrote in
between, the version changed and the update matches zero rows: the worker knows it lost and re-reads.
This suits applications well: conflicts are rare (two devices, a retry), and holding a database lock
across a vendor call would be a disaster. The unique constraint on `loan.application_id` backs it up: it is
checked by the database at insert, so even a code path that forgets the version check cannot create a
second loan.

## Appendix D: The outbox and the relay

The outbox is a table written in the same transaction as the business change. A relay (a small process)
reads unpublished rows in order, publishes each to the log, and marks it published. If the relay dies after
publishing and before marking, the row is published again: consumers must be idempotent. Alternatives to
polling are tailing the database's change log, which avoids the polling load and keeps order per key. Keep
published rows for a week, so the log can be rebuilt from them if needed, then delete them in batches.

## Appendix E: Decision records and replay

A record is written once to object storage with a retention lock: it cannot be changed or deleted before
the retention date, even by an administrator. It is encrypted with a data key unique to the record, and
that key is encrypted by a key in a key-management service. The database holds the record's URI and the
hot fields (outcome, reasons, versions). Replay needs three things kept for as long as the records: the
model artefacts (in a registry, by version), the policy and pricing tables (as versioned data, not code
paths), and the feature code (versioned with the model). A nightly replay of a sample catches the day
someone "cleans up" an old version. At the end of retention, destroying the data key makes the record and
every backup copy unreadable.

## Appendix F: Champion, challenger and what shadow cannot see

The champion is the model in production. A challenger is scored beside it. In shadow, the challenger's
score is recorded and never acted on, which answers *who would it approve, and with what reasons* by
segment and group. It cannot answer *do they repay*, because applicants the champion declined never
received a loan. Only a slice where the challenger decides produces those outcomes. The slice is sized by
an exposure cap that credit risk sets, and judged on early signals (first payment missed at 30 to 45 days,
early delinquency) long before charge-offs arrive at 90 to 120 days. Fairness testing compares approval
rates and outcomes across protected groups on both shadow and slice; the method and the thresholds belong
to compliance and credit risk.

## Appendix G: Tokenisation vaults

A token is a random reference to a stored value. The vault stores the value encrypted per field, with keys
held in a hardware-backed key service, and returns the token. Detokenise is allowed only to named callers,
for named purposes, and every call is logged. Format-preserving tokens (a token that looks like a nine-digit
number) help legacy systems but make it easier to confuse a token with a real value in a log; random tokens
with a prefix (`tok_`) are easier to scan for. The vault is deliberately boring: no search, no analytics,
no business logic.

## Appendix H: Where this shape shows up again

| Problem | The same core |
|---|---|
| An insurance quote at checkout | Slow, paid data vendors under a deadline; a price you must explain |
| Account opening with identity checks | Parallel checks; refer instead of decline; a vault |
| Marketplace seller onboarding | A durable state machine; an identity vault; a manual review path |
| Mortgage pre-approval | Reproducible decisions under versioned policy; reasons for a decline |
| Rental or tenant screening | Paid reports; a decision with reasons; retention rules |

## Appendix I: Testing it

Contract tests per vendor adapter against the vendor's sandbox, including its slow and error modes. A
fault-injection suite in the orchestrator: a vendor slow, failing, over its rate limit, answering after the
deadline. A concurrency test for booking: two accepts for the same application from two clients, a
thousand times, expecting exactly one loan. A replay test in CI: every policy or model change replays a
fixed set of historical records and must reproduce them, or ship as a new version. A game day each
quarter: a bureau "outage" in a test region, with credit risk in the room.

\newpage

# One-page cheat card

**Insight.** A regulated decision under a deadline set by slow, paid vendors, then one atomic step. The
load is tiny.

**Numbers.** 0.8/s average, 8/s peak · 32 vendor calls/s · $2M a month in bureau pulls · 3 % reach the
deadline without a bureau · 9,600 applications in a 20-minute outage · 100 GB of records a month, 8.4 TB
over 7 years · 2.7 s of the 3 s budget used.

**Design.** Phone → API edge (vault tokens, idempotency) → application service (state machine) →
orchestrator (one deadline, breakers, rate limits) → vendors; policy engine (model, policy, pricing,
missing-data table); one transaction for loan + outbox; event log → funding and servicing; decision
records in object storage.

**Challenges and the one-line answer.**

1. Slow bureau: everything at once, one deadline, breakers; never race paid pulls.
2. Bureau down: a signed table: second bureau, small known under a cap, refer, decline with a real reason.
3. Phone drops: conditional update at a version, unique loan, outbox in one commit.
4. Funding fails: its own state machine; UNKNOWN means query, never resend; reconcile.
5. Explain later: frozen inputs, versions, ranked reasons; nightly replay; crypto-shred at the end.
6. New model: backtest, shadow, a capped slice; shadow cannot see loss.
7. Identity: a vault; tokens everywhere else; the right rulebook.
8. Know it's broken: offers in 3 s, approval per merchant per hour, fallback against cap, booked not
   funded; read metrics in pairs.

**Close.** "One database, one atomic step. The design lives at the slow edges and in what we keep."
