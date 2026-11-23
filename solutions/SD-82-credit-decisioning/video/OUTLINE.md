- [x] outline  - [x] design  - [x] diagrams  - [x] slides  - [x] script  - [x] video  - [x] publish

# SD-82 · Real-time credit decisioning and origination (instant lending at the point of sale) — reference-solution video outline

Target level: staff (manager layer AUX) · Target length: 75 min (65–85) · Word budget: 9,400 (≈ 0.49 s a word with the
2026-11-17 pacing beats, measured on SD-94 and SD-96)

Generic content only: no company, lender, bureau or vendor figures. Every number is arithmetic from the stated inputs and carries a
label. Problem 1 of the retired 2026-11-20 fintech mock series is the short version of this question;
this video replaces it as the reference.

## Thesis and definition

- **Thesis** (key-line voice): *Instant credit at the counter is a regulated decision under a deadline set by slow, paid vendors,
  followed by one atomic step. Throughput is tiny. The grade is on the slow edges, on booking exactly one loan, on decisions you can
  explain years later, and on keeping identity data in a small box.*
- **Definition to say aloud**: *A credit decisioning and origination system gathers identity, fraud and credit data from paid vendors
  under one deadline, returns an explainable decision with priced offers, and books exactly one loan when the customer accepts an
  offer they were shown.* Load-bearing clauses: **paid vendors** (every call costs money and may be recorded: never race them),
  **one deadline** (the customer is standing at a counter), **explainable** (a decline must carry reasons about the applicant,
  reproducible years later), **exactly one loan** (one atomic step), **an offer they were shown** (the disclosure version is part of
  the contract).
- **Hook**: Eight applications a second at the Saturday peak. Any database takes that. Yet this question fails strong engineers,
  because the hard parts are not load: a credit bureau that answers in four seconds one time in ten while a customer waits; a phone
  that drops between "accept" and the answer; and a regulator who asks, fourteen months later, why someone was declined.

## 0 · What this question grades

| Axis | Weak signal | Strong signal |
|---|---|---|
| Requirements | "Score the customer and create a loan" | Asks who the lender of record is, the counter deadline, vendor latency and cost, the decline-reason and retention rules, before drawing |
| Correctness | A saga that "compensates" every step; check-then-insert on the loan | A state machine with one atomic step (accept → book + outbox), a unique constraint, idempotency keys |
| Trade-offs | Hedged requests to the bureau; "approve with partial data" as a code default | One deadline with a missing-data policy owned by credit risk and capped; the options matrix with a stated cost |
| Depth | "The model returns a score" | Frozen inputs and versions so any decision replays; champion and challenger under an exposure cap; a vault with tokens |
| Operations | CPU and error rate | Offers-in-3-s SLI, approval rate per merchant per hour, fallback rate against its cap, booked-not-funded, vendor spend; owners per degraded path |

## 1 · Requirements and scope

- **Clarifying questions and the interviewer's answers** (asked aloud, six):
  1. *How many applications?* — 2 million a month; the Saturday peak is about ten times the average.
  2. *How long can the customer wait?* — Offers on screen in under 3 s for 95 % of applications; 10 s is a lost sale.
  3. *Who is the lender of record?* — "We decide on the partner bank's credit policy and service the loan; the bank is the lender of
     record." (Changes: every policy version is approved, and records are the bank's too.)
  4. *Which vendors, how fast?* — Two credit bureaus (p50 0.6 s, p99 several seconds, about 1 % errors), an identity and fraud
     vendor (p99 400 ms), optional bank-account data (seconds to minutes).
  5. *What do they cost?* — About $1 a bureau pull; identity checks about 5 cents.
  6. *Which rules?* — Disclosures (APR, schedule, total cost) before signing; the principal reasons for every decline; records kept
     about seven years; fairness testing of models. (Seeds C2, C5, C6.)
- **Functional requirements** (each gets a numbered flow):
  - FR1 · **Apply**: the customer scans the merchant's code; identity goes into a vault; an application exists, idempotently.
  - FR2 · **Decide**: gather identity, fraud and credit data under one deadline; return offers, a refer, or a decline with reasons.
  - FR3 · **Accept and book**: the customer accepts one disclosed offer; exactly one loan is booked.
  - FR4 · **Fund and hand off**: the merchant is paid net of fees; the loan goes to servicing (SD-95); decline notices go out.
- **Non-functional, with numbers** (initial targets): offers p95 under 3 s from submit; apply and decide 99.9 % available in merchant
  hours; **0** loans booked twice or without acceptance of the shown disclosure version; **100 %** of decisions reproducible with
  versions and reasons for 7 years; raw identity data only inside the vault; merchant funded within one business day; every degraded
  path under an exposure cap.
- **IN / OUT**: IN: apply, identity, decide, offers, refer, accept, book, the funding instruction, the servicing handoff, decline
  notices. OUT on purpose: repayments and the ledger (SD-95), card authorisation (SD-77), merchant onboarding and underwriting, model
  training pipelines (we consume a model artefact), collections, the payment rail itself (SD-44).
- **"The core is 3 things"**: an *orchestrator* that decides under one deadline with a policy for whatever is missing; a *state
  machine* whose only atomic step is accept to book; and a *record and a vault*: what we keep to explain the decision, and the small
  box where identity lives.

## 2 · Estimates

| Number | Arithmetic | Label | Decision it drives |
|---|---|---|---|
| Applications | 2 × 10⁶ ÷ (30 × 86,400 s) ≈ **0.8/s**, peak × 10 ≈ **8/s** | given → derived | One relational primary, replicated. No sharding |
| Vendor calls | 8/s × 4 calls ≈ **32/s**; in flight 32/s × 2 s ≈ **64** | derived | The load is on the vendors; concurrency limits per vendor matter more than our servers |
| Bureau bill | 2 × 10⁶ × $1 ≈ **$2M a month** | illustrative | The largest cost line by far; reuse a recent report where contract and law permit |
| Report reuse | 20 % re-apply within 30 days → 4 × 10⁵ × $1 ≈ **$400k a month** | illustrative | A report store with a retention rule is part of the design |
| Identity checks | 2 × 10⁶ × $0.05 ≈ **$100k a month** | illustrative | Second line; also paid per call |
| Decision records | 2 × 10⁶ × 50 KB ≈ **100 GB a month**; × 84 months ≈ **8.4 TB** | illustrative | Encrypted object storage with a reference in the database, not the database |
| Loans | 2 × 10⁶ × 60 % approved × 70 % accepted ≈ **840,000 a month**, × $1,200 ≈ **$1.0B a month**; ≈ 28,000 a day | illustrative | Funding is a daily batch per merchant; the money path is where compensation is real |
| Missing data | ≈ 2 % of bureau calls past a 2 s deadline + ≈ 1 % errors ≈ **3 %** → ≈ 60,000 applications a month | illustrative, to measure | The missing-data policy is a weekly-volume path, not an edge case |
| An outage | 8/s × 1,200 s (20 min) ≈ **9,600 applications**; approve all ≈ 9,600 × $1,200 ≈ **$11.5M unscored**; decline all ≈ 9,600 × 60 % × 70 % ≈ **4,000 lost loans** | derived | Neither extreme: the policy table with caps (C2) |
| Latency budget (3 s p95) | phone to API 150 + state 50 + vendor deadline 2,000 + features 100 + model 80 + policy and pricing 70 + record 50 + push 200 = **2,700 ms**, spare 300 | initial target | One deadline for all vendors; nothing optional on the counter path |

## 3 · Theory

1. **Is / is not.** Is: a decision service with an origination state machine. Is not a **scoring model** (the model is one input;
   policy decides, and pricing prices), not a **payment** (no money moves at accept; funding is later and asynchronous), not a
   **saga** (only one step must be atomic; a credit pull cannot be compensated), not an **underwriting queue** (refer is minutes, not
   days).
2. **Safety**: S1 · never book a loan twice, or without acceptance of the exact offer and disclosure version shown. S2 · never
   decline or price without reasons about the applicant that can be reproduced. S3 · raw identity data never leaves the vault
   boundary. S4 · never pay for a pull we did not need: at most one pull per bureau per application. **Liveness**: L1 · every
   application gets an answer (offer, refer, decline) within the deadline. L2 · every booked loan is eventually funded and handed to
   servicing, with one effect. L3 · every referred application is finished within ten minutes.
3. **Central tension**: **time against evidence against money.** Waiting longer for a vendor adds evidence and approvals and loses the
   sale; deciding early keeps the sale and adds risk; asking a second vendor adds evidence and cost. Picture: vendor answers arriving on
   a time axis, the deadline line at 2 s, the sale lost at 10 s, and each extra pull priced.
4. **Mechanisms** (6). Property → how → failure ruled out → cost.

   | Mechanism | Protects | Rules out | Costs |
   |---|---|---|---|
   | **M1 Scatter-gather under one deadline, a breaker per vendor** | L1, S4 | One slow vendor setting the customer's wait; waiting on a dead vendor | Decisions with data missing, which M2 must decide |
   | **M2 A missing-data policy table**, versioned, capped, owned by credit risk | S2, L1 | "Approve with partial data" as a code default; declines for "our vendor was slow" | A refer path to run; an exposure counter; an owner who signs it |
   | **M3 The application as a state machine** with optimistic versions and idempotency keys | S1, L1 | Two workers moving one application; lost progress when a phone drops | A committed write per transition |
   | **M4 One local transaction**: book + `UNIQUE(application_id)` + outbox row | S1, L2 | Two loans for one application; a loan nobody hears about | A relay to run; consumers that de-duplicate |
   | **M5 An immutable decision record**: frozen inputs, versions, ranked reasons | S2 | Unexplainable declines; a re-run that contradicts the notice sent | 8.4 TB over seven years; old model versions kept loadable |
   | **M6 An identity vault with tokens** | S3 | Identity data in rows, logs, exports and training sets | A critical small service; a hop at apply and at each vendor call; key management |

5. **Options matrix — how to run an application** (rows = approaches; columns = deciding properties; last column = fails when).

   | Approach | Meets 3 s p95 | One pull per bureau | Survives a dropped phone | Explainable | Fails when |
   |---|---|---|---|---|---|
   | A · Synchronous chain: identity, then bureau, then model, in the request | no: latencies add | yes | no | partly | The bureau's tail alone is several seconds |
   | B · Parallel calls with hedging (race two bureaus) | yes | **no** | no | partly | Every race is two paid pulls and two inquiries on the customer's file |
   | C · A saga with a compensation for every step | yes | yes | yes | partly | A pull cannot be undone; compensations that do nothing are complexity |
   | D · A durable workflow engine for the whole flow | yes | yes | yes | yes | Not a failure: another system to run; worth it when steps last days |
   | **E · Database state machine + one deadline + policy table + atomic book with outbox** | yes | yes | yes | yes | The flow grows multi-day steps (document upload, manual review) |
   | F · A manual or batch underwriting queue | no | yes | yes | yes | Ten seconds is a lost sale |

   **Pick: E**, with **D** as the honest equal (choose it when steps last hours or days). A, B, C, F greyed with their failure.
   **Gives up:** timers, retries and the relay we write ourselves, which a workflow engine would give us.
6. **Failure catalogue**: F1 a slow bureau → C1 · F2 a bureau down for everyone → C2 · F3 a dropped phone, two taps → C3 · F4 funding
   fails after booking; an unknown transfer → C4 · F5 a decision nobody can explain → C5 · F6 a new model that approves more → C6 ·
   F7 identity data spreading → C7 · F8 a silent approval drop → C8 · F9 merchant fraud (a merchant ringing up fake sales): out of
   scope, merchant risk; named on the scope slide.

## 4 · API and entities

| API | Serves | Reads / writes | Wire-format notes |
|---|---|---|---|
| `POST /v1/applications {merchant_id, amount, applicant: {vault_token}}` + `Idempotency-Key` → `202 {application_id, status}` | FR1 | writes **Application** | Identity goes to the vault first; only a token crosses |
| `GET /v1/applications/{id}` → `{status, offers[], expires_at}` (or a push to the phone) | FR2 | reads **Application**, **Offer** | Offers expire (15 min); the status says REFERRED with a promise time |
| `POST /v1/applications/{id}/accept {offer_id, disclosure_version}` + `Idempotency-Key` → `201 {loan_id}` | FR3 | writes **Loan**, **Application**, **Outbox** | A second accept returns the same loan |
| event `LoanBooked {loan_id, application_id, merchant_id, terms}` | FR4 | read by funding, servicing | At least once; consumers de-duplicate by `event_id` |
| internal `Decide(application) → {outcome, offers, reasons[], versions, missing[]}` | FR2 | writes **Decision** | The decision interface between teams |

**Conceptual**: **Applicant** (vault token) 1—N **Application** (merchant, amount, status, version); **Application** 1—N **VendorCall**
(vendor, outcome, cost, latency); **Application** 1—1 **Decision** (outcome, reasons, versions, record reference); **Decision** 1—N
**Offer** (term, APR, schedule, expiry); **Application** 1—0..1 **Loan** (offer, terms, disclosure version); **Loan** 1—N
**FundingTransfer**.
**Physical**: `application(id PK, merchant_id, applicant_tok, amount_cents, status, version)`; `vendor_call(application_id, vendor,
seq, outcome, cost_cents, ms)`; `decision(application_id PK, outcome, reasons[], model_v, policy_v, pricing_v, record_uri)` written
once; `offer(id PK, application_id, terms, expires_at)`; `loan(id PK, application_id UNIQUE, offer_id, disclosure_v, terms)`;
`outbox(event_id PK, type, payload, published_at)`; the record body in object storage under `record_uri`; the vault separate.

## 5 · High-level design

| Version | Adds | Objection it answers | Objection it leaves |
|---|---|---|---|
| V1 | One application service called by the POS; calls identity, then the bureau, then a scoring function, in the request; writes the application and the loan | (none: the simplest thing that works) | Latencies add: p99 is several seconds; a dropped phone books twice; nothing explains a decision |
| V2 | **A decision orchestrator** calling vendors in parallel under one deadline, with a breaker per vendor; **the application as a state machine** in the database; booking with a unique constraint and an **outbox** relayed to an **event log**; a versioned model, policy and pricing step | "The customer waits for the slowest vendor; a retry or a second tap repeats work" | What happens when data is missing at the deadline; identity data is in every row; no record survives a model change; nobody funds the merchant |
| V3 | **The identity vault** (tokenise at apply, detokenise only in vendor adapters); **decision records** in encrypted object storage; the **missing-data policy table** in the policy step; **funding and servicing** consuming the loan-booked event; decline notices | "It must be regulated, explainable and owned" | The details, which are the challenges |

Baseline spine, left to right: **Phone / POS → API edge → Application service → Decision orchestrator → Credit vendors**, with
**Identity vault** above the API edge, and **Funding · servicing ← Event log ← Application DB**, **Model · policy · pricing**,
**Decision records** along the bottom. Tags: `ch6` challenger model above the orchestrator; `ch7` analytics above the application
service.

Flows (numbered arrows):
- **FR1 Apply:** 1 the phone posts the application with an idempotency key · 2 the API edge tokenises identity in the vault · 3 the
  application service creates the row, STARTED · 4 commit · 5–6 202 with the application ID back to the phone.
- **FR2 Decide:** 1 the application service asks the orchestrator · 2 adapters detokenise in the vault · 3 all vendors called at once,
  one deadline · 4 answers, or a recorded miss · 5 features, model, policy, pricing · 6 the decision record is written · 7 the
  decision returns; the row is OFFERED, REFERRED or DECLINED · 8 offers reach the phone.
- **FR3 Accept and book:** 1 the phone posts accept with the offer and disclosure version · 2 to the application service · 3 one
  transaction: status BOOKED at a version, the loan with a unique application ID, the outbox row · 4 201 with the loan ID.
- **FR4 Fund and hand off:** 1 the relay reads the outbox into the event log · 2 funding and servicing consume LoanBooked · 3 funding
  pays the merchant in the daily batch; servicing opens the schedule (SD-95); declines get their notice.

C4 and sequence views that follow: context; containers; sequences for apply-and-decide and accept-and-book.

## 6 · Bridge and challenge map

*It works. Where does it break first?* The baseline with eight attack points. Latency and policy: C1, C2. Correctness: C3, C4, C5.
Trade-off: C6. Security: C7. Observability: C8. The crux (a decision under slow paid vendors; one atomic step) gets C1 + C2 and C3 + C4.

## 7 · Challenges

### Challenge 1 · The bureau is slow  *(latency; crux part 1)*

- Q: "One bureau call in ten takes four seconds today. What does the customer at the counter see?"
- Naive answer: "Wait for it, and if it's slow, send the same request to the second bureau and take whichever answers first."
- Case: 10:00:00.000 submit; .050 identity, fraud and bureau A called; .400 identity back; .350 fraud back; bureau A silent at 2.0 s;
  a hedge to bureau B at 1.0 s answers at 1.7 s; bureau A answers at 4.1 s. Two pulls paid ($2), two inquiries on the customer's
  file, and with no hedge the offers appear at 4.4 s, past the 3 s promise.
- Break: the orchestrator's call to the vendors, dashed red.
- Fix: **scatter-gather under one deadline** (all calls at once, decide at 2.0 s with what has arrived) and **a breaker per vendor**
  (stop calling a vendor that is failing for everyone). The second bureau only after an error or an open breaker, never as a race.
  Sequence: scatter, gather, deadline. Code: the gather with a deadline.
- Why it works: L1 is bounded by the deadline, not by the slowest vendor; S4 holds because a second pull happens only when the first
  has failed, not when it is slow.
- "What if the fix fails?": "The bureau's answer arrives at 4.1 s, after you decided. What do you do with it? And it was paid for."
- Second fix: record it (it is a fact and a cost); use it to finish a referred application; never change an offer already shown; keep
  the report for reuse within the window the contract allows. Honest limit: a deadline means some customers get the missing-data path
  every day: about 3 %, which is the next question.
- If asked, I'd say: "All vendors at once, one deadline, a breaker per vendor. I never race two bureaus, because each pull is paid
  and may show on the customer's file. A late answer is recorded and used to finish a refer, never to change what the customer saw."

### Challenge 2 · The bureau is down for everyone  *(failure recovery and policy; crux part 1)*

- Q: "Bureau A is down for everyone for twenty minutes on a Saturday. What happens at the counter?"
- Naive answer: "Approve with whatever data we have" or "decline until it's back."
- Case: Saturday 11:00 to 11:20, 8 applications a second: 9,600 applications. Approve all: about $11.5M offered with no credit file.
  Decline all: about 4,000 lost loans, and 9,600 decline notices whose reason would be "our vendor was down", which is not a reason
  about the applicant.
- Break: the vendors (bureau A dead) and the policy step, dashed red.
- Fix: **the missing-data policy table**, owned by credit risk and versioned like any policy: (1) the second bureau, after the breaker
  opens; (2) decide without a bureau only for returning customers in good standing, at most $500, under a daily exposure cap of
  $250,000; (3) **refer**: "we'll finish in two minutes by text", the merchant sees pending; (4) decline only with a reason about the
  applicant. Engineering makes each row a setting with a counter and a dashboard.
- Why it works: S2 (no decline for our own outage) and L1 (everyone gets an answer), with exposure bounded by arithmetic: the cap is
  the worst case.
- "What if the fix fails?": "Bureau B's contract allows five calls a second. You're sending eight."
- Second fix: a token bucket per vendor at the contract rate; overflow goes to refer; referred applications complete when a breaker
  half-opens, oldest first, inside the ten-minute promise; the cap is split per merchant so one busy merchant cannot drain it.
  Honest limit: referred customers walk away; measure refer completion and the sale lost per minute of outage.
- If asked, I'd say: "Every timeout is a credit decision with an owner. Credit risk signs a table: second bureau, small known
  customers under a daily cap, refer, or decline with a real reason. Engineering makes it a setting with a counter, a cap and a
  dashboard."

### Challenge 3 · The phone drops  *(correctness; crux part 2)*

- Q: "The customer taps accept, the phone loses signal, and they tap again on the merchant's tablet. How many loans?"
- Naive answer: "Check whether a loan exists, and create one if it doesn't." Or: "a saga, with a compensation for each step."
- Case: 14:31:07.200 phone posts accept (key k1); 07.900 the response is lost; 08.050 tablet posts accept (key k2, another device);
  08.060 worker 1 and 08.070 worker 2 both read OFFERED at version 7; both see no loan; both insert: two loans, two funding transfers
  of $1,200, and the customer is billed twice.
- Break: the application service and the database, dashed red.
- Fix: **one local transaction**: `UPDATE application SET status = BOOKED, version = 8 WHERE id = ap_91 AND status = OFFERED AND
  version = 7`; zero rows means someone else booked: return the existing loan. The loan has `UNIQUE(application_id)`. The outbox row
  commits with the loan. Idempotency keys make a retry on the same device return the stored answer. Code: the SQL transaction.
- Why it works: S1 is enforced by the database: the conditional update lets exactly one writer through, and the constraint is a
  second wall. The outbox makes "the loan exists" and "the world will hear about it" one fact.
- "What if the fix fails?": "The commit succeeded but the relay crashed before publishing. Or it published twice."
- Second fix: the relay is at least once by design (it marks rows published after the log acknowledges); every consumer de-duplicates
  by `event_id`, and funding uses the loan ID as its idempotency key at the bank. Honest limit: at-least-once plus idempotent
  consumers, not exactly once.
- If asked, I'd say: "Only one step is atomic: accept to book. A conditional update at a version, a unique constraint on the
  application, and the outbox row in the same commit. A second tap finds the loan and shows it. The event is at least once, and
  every consumer de-duplicates."

### Challenge 4 · Funding fails after booking  *(failure recovery; crux part 2)*

- Q: "The loan is booked. The transfer to the merchant is rejected, or the bank times out. What do you undo?"
- Naive answer: "Roll back the saga: cancel the loan, reverse the credit check, delete the application."
- Case: 14:31 loan ln_5531 booked; 18:00 the daily funding batch sends $1,164 (the $1,200 less a 3 % merchant fee) to the merchant;
  18:02 the bank returns "account closed"; a second merchant's transfer at 18:03 times out with no answer. Re-sending both would
  pay the second merchant twice if the first attempt had worked.
- Break: funding, dashed red.
- Fix: **funding as its own state machine** after booking, the only step with a real compensation: PENDING → SENT → SETTLED, or
  RETURNED → merchant ops fixes the account → resend with a new attempt; a timeout is **UNKNOWN**: query the bank by our idempotency
  key, never resend blindly. The loan is cancelled only if the goods were not delivered, and that is a business decision with the
  merchant. Daily reconciliation against the bank's file. Table: step · can it be undone · so.
- Why it works: L2 with one effect: the loan ID is the idempotency key end to end; UNKNOWN keeps "maybe paid" from becoming "paid
  twice".
- "What if the fix fails?": "The bank's status API says 'not found' for the timed-out transfer, and the file tomorrow shows it paid."
- Second fix: "not found" in the first minutes is not "not sent": wait for the reconciliation window before any resend; a break
  between our ledger and the bank file opens a case with an owner and an age. Honest limit: some outcomes are only known the next
  day; the merchant sees "in progress", not a guess.
- If asked, I'd say: "The credit pull and the booking aren't compensated: they happened. The one step with a real undo is funding,
  so it's its own state machine after booking, with UNKNOWN as a state: query, never resend. Reconciliation against the bank file
  closes the gap."

### Challenge 5 · Explain a decision fourteen months later  *(correctness and regulation)*

- Q: "A regulator asks why a customer was declined fourteen months ago. Reproduce it."
- Naive answer: "Re-run the model on the customer's data."
- Case: January 2026, application ap_204 declined by model v9 and policy v31: reasons "high utilisation, short history". March 2027:
  re-running today's model v14 on today's bureau file approves. The notice we sent says one thing and the replay says another.
- Break: the model, policy and pricing step, dashed red: it only knows today.
- Fix: **an immutable decision record**: frozen inputs (the bureau report stored encrypted, by reference; identity and fraud results;
  internal history as of then; the feature vector; which calls were missing), every version (model, policy, pricing, disclosure),
  the outputs (offers, outcome, ranked reasons, the degraded path taken). Old model artefacts stay loadable; a replay job runs
  sampled records every night and alarms on any difference.
- Why it works: S2: same inputs and same versions give the same answer, and the replay proves it continuously instead of on the day
  a regulator asks.
- "What if the fix fails?": "The customer asks us to delete their data. The record holds their bureau report."
- Second fix: the retention duty for credit records wins for its period, and compliance owns that call; within it, the record holds
  tokens and an encrypted report under a per-record key; at the end of retention the key is destroyed (crypto-shredding), so every
  copy, backups included, becomes unreadable. Honest limit: a deletion request inside the retention period is answered by restricting
  use, not by deleting.
- If asked, I'd say: "I never re-run today's model to explain yesterday. Every decision freezes its inputs, the versions of model,
  policy and pricing, and the ranked reasons. A nightly replay proves records still reproduce, and retention ends by destroying
  the record's key."

### Challenge 6 · A new model approves six percent more  *(trade-off and rollout)*

- Q: "Data science has a new model. It approves six percent more people at the same predicted loss. Roll it out."
- Naive answer: "Shadow mode for a week, it looks good, switch it on." Or "a fifty-fifty A/B test."
- Case: 6 % of 2 million is 120,000 more approvals a month; at 70 % take-up, 84,000 loans, about $100M a month of new exposure.
  The first payments fall due in two to four weeks; losses show at 90 to 120 days. A week of shadow shows the approval rate, and
  nothing about whether the new approvals repay.
- Break: the model, policy and pricing step, dashed red.
- Fix: **champion and challenger**: (1) a backtest on history; (2) shadow, scoring every application with both, acting on the
  champion, comparing approval rates and reasons by segment and by protected group; (3) a **challenger slice** of 5 % of traffic
  under its own exposure cap (5 % of the extra ≈ 4,200 loans, about $5M a month), signed by credit risk and the partner bank;
  (4) early signals at 30 to 45 days (first payment missed); (5) widen only through a policy version change, with a kill switch.
- Why it works: S2 is kept (each decision records which model decided), and the exposure of learning is bounded by the slice cap,
  not by hope.
- "What if the fix fails?": "Shadow looked great. Why isn't that enough?"
- Second fix: shadow cannot see outcomes for people the champion declined: they never got a loan, so there is no label. Only a
  capped slice where the challenger decides produces labels. Fairness checks run on the slice and on shadow. Honest limit: a slice
  is real money at risk; the cap is the price of learning, and credit risk owns it.
- If asked, I'd say: "Shadow tells you who the new model would approve, not whether they repay. So: backtest, shadow, then a
  capped slice where the challenger decides, early signals at thirty days, fairness by group, and every step a policy change with
  a kill switch."

### Challenge 7 · Where identity data lives  *(security)*

- Q: "The analytics team wants application data to train the next model. What do they get?"
- Naive answer: "A copy of the database; we encrypt it at rest." Or "we drop the name column."
- Case: the application table holds a social security number, date of birth and address; a debug log line at the bureau adapter
  prints the full request; the support tool shows the full number; the training extract keeps date of birth and postcode, which
  re-identify most people together. One leaked extract leaks two million identities a month.
- Break: the application service, its database and the export to analytics, dashed red.
- Fix: **an identity vault**: identity is tokenised at apply; only the vault and the vendor adapters, which need the real values for
  the call, sit inside the boundary; every detokenise is logged with a purpose; rows, logs, records, support tools and training see
  tokens or masked values; training gets derived features, not identity. Know the rulebook: card numbers fall under the card
  industry's security standard; a social security number falls under privacy and lending law.
- Why it works: S3 by construction: a leak outside the boundary leaks tokens.
- "What if the fix fails?": "The vault is down."
- Second fix: the vault is a tier-0 dependency: small, replicated across zones, with its own 99.95 % objective and no logic in it;
  if it is down, apply cannot start and decide cannot call vendors, so applications refer and the merchant sees pending; nothing raw
  is ever cached outside it to "help". Honest limit: the vault being small is what makes it reliable; resist every feature request.
- If asked, I'd say: "They get tokens and derived features, never identity. Only the vault and the vendor adapters see real values,
  every access is logged, and a leak anywhere else leaks tokens. And I'd name the right rulebook: identity data is privacy and
  lending law, not the card standard."

### Challenge 8 · How would you know it is broken?  *(observability)*

- Q: "Your dashboards are green. How would you know decisions are going wrong?"
- Naive answer: "Error rate, latency and CPU."
- Case: Friday 18:00 a pricing-table change maps one bureau field wrongly. No errors; latency is fine; the approval rate across all
  merchants drops from 62 % to 41 %. At about 2 applications a second that is 7,200 an hour, about 1,500 wrongly declined each hour,
  each with a notice. Found at 09:00 on Saturday, when merchants start calling: fifteen hours, about 22,000 customers (if the evening rate held; illustrative).
- Break: the policy step (the change) and the monitoring view, dashed red.
- Fix: **SLIs on the promise and on the decision**: offers within 3 s p95; approval rate per merchant per hour against its own
  baseline; fallback rate per path against its cap; booked-not-funded after one hour; vendor errors, latency and spend per hour; the
  mix of decline reasons. **Symptom pairs**: approval down + vendor errors flat = our change; refer up + breaker open = an outage being
  handled; latency up + breaker closed = a vendor slow but under the threshold; booked up + funded flat = funding stuck. Policy and
  pricing changes ship as canaries on a small slice with the approval-rate alarm.
- Why it works: the SLIs measure what the customer and the lender experience; the pairs turn two metrics into one cause.
- "What if the fix fails?": "Approval drops at one merchant only."
- Second fix: per-merchant baselines by hour of week; one merchant is usually an integration bug (amounts in cents sent as dollars)
  or a fraud ring; route to merchant ops or fraud, not to credit. Honest limit: small merchants have noisy baselines; alarm on
  totals over a window.
- If asked, I'd say: "I watch the decision, not the servers: offers in three seconds, approval rate per merchant per hour against
  its baseline, fallback rate against the cap, and loans booked but not funded. Two metrics together tell me whether it's us, a
  vendor or one merchant."

## 8 · Build cost (AUX)

- **V1** (one service, sequential calls, one table): 3 engineers, 2 months, to learn. **V2** (orchestrator, state machine, outbox,
  versioned model step): a team of 6 for 2 quarters. **V3** (vault, records, policy table, funding, notices, champion and challenger):
  two teams for 2 more quarters, plus security and compliance time.
- **Buy against build**: bureaus, identity and bank-data vendors are bought; the vault is bought (a tokenisation service) or built small;
  a workflow engine is bought only if steps grow to days; the decision orchestrator, policy engine and records are ours, because the
  regulator asks us, not a vendor.
- **Team seams** (six owners): applications and origination (state machine, booking); decisioning platform (orchestrator, policy engine,
  model serving); vendor integrations (adapters, contracts, spend); security (vault); credit risk and data science (models, every
  degraded path, caps); compliance (disclosures, notices, retention). Contracts: the decision interface, the decision record, the
  LoanBooked event.
- **Cost, illustrative**: the bureau bill ($2M a month) dwarfs compute; report reuse and the second-bureau rule are the cost levers;
  storage of 8.4 TB is small.
- **Top risks**: a degraded path without an owner or a cap; a model change without a replayable record; identity data leaking into
  logs; funding retries without an UNKNOWN state.

## 9 · Recap

Final diagram: the V3 baseline. One sentence per path: *Apply:* tokenise, create, answer at once. *Decide:* all vendors at once, one
deadline, policy for what's missing, a record. *Book:* one transaction, one loan, one event. *Fund:* its own state machine, UNKNOWN
as a state, reconciled.
**Common mistakes:** treating it as a throughput problem; sequential vendor calls; hedging paid pulls; "approve with partial data" as
a default; a saga that compensates a credit pull; check-then-insert on the loan; re-running today's model to explain yesterday;
"encrypt the database" as the identity answer; card rules quoted for a social security number; no owner for any degraded path.
**Closing line (key-line voice):** "The core is small and boring on purpose: one database, one atomic step. The design lives at
the slow edges and in what we keep: one deadline with a signed policy for what's missing, a record that replays, and identity in a
vault."

## Canon check

| Canonical point | Source | Covered at, or dismissed because |
|---|---|---|
| Scatter-gather with timeouts and circuit breakers | cue sheet; common prep material | M1; C1 |
| No hedged requests to paid vendors | cue sheet | Options matrix row B; C1 |
| Missing-data table with refer, owned by credit risk | cue sheet | M2; C2 |
| Application state machine, idempotency keys, unique loan, outbox | cue sheet; common prep | M3, M4; C3 |
| A credit pull is not compensated; only funding is | cue sheet | Theory 1; options row C; C4 |
| Reproducible decision record with versions and reasons; adverse action | cue sheet; lending rules | M5; C5 |
| Champion and challenger with exposure caps; early signals; fairness | cue sheet | C6 |
| PII vault and tokenisation; card standard is not the SSN rulebook | cue sheet | M6; C7 |
| Bureau cost as the largest line; report reuse | cue sheet | Ch. 2; build cost |
| Lender of record (partner bank) | cue sheet | Ch. 1 Q3 |
| Durable workflow engines | widely used since about 2022 | Options row D, the honest equal |
| Cash-flow underwriting with bank-account data | recent practice | Optional input, never awaited at the counter (FR2, C1) |
| Merchant fraud, merchant underwriting | adjacent | Dismissed aloud on the scope slide: merchant risk, another system |
| What changed recently | — | Workflow engines common; bank data through aggregators more available; regulators asking for explainable models and documented fairness testing |

## From the old version (Problem 1 of the retired fintech mock series, 2026-11-20)

| Reused | New | Dropped |
|---|---|---|
| The clarifying answers and the three estimates (load, bureau bill, records); the API and the three tables; the four deep dives (slow bureau, dropped phone, explain later, vault) and the drills; the "what is graded" axes; the three traps; figures f1-budget, f1-scatter, f1-fallback, f1-states, f1-record, f1-vault, f1-teams as content for the redrawn baseline views | Theory chapter (six parts, four safety and three liveness properties); options matrix with a pick; V1 → V2 → V3 on a carried baseline; four numbered flows; C2 outage with arithmetic and per-vendor rate limits; C4 funding with UNKNOWN; C6 champion and challenger as a full challenge (shadow cannot see labels); C8 symptom pairs; build cost; canon check | Coach-led narration (now candidate-led); the "where this shows up" table (moved to the booklet); the then-and-now panel (into the canon check) |

## Budget

| Chapter | Minutes | Words | Slides |
|---|---|---|---|
| 0 Cold open | 2.5 | 300 | 5 |
| 1 Requirements and scope | 5.5 | 680 | 11 |
| 2 Estimates | 5 | 620 | 8 |
| 3 Theory | 10 | 1,200 | 15 |
| 4 API and entities | 4.5 | 550 | 7 |
| 5 High-level design | 9 | 1,100 | 15 |
| 6 Bridge | 1 | 100 | 2 |
| 7 Challenges (8 × ~4.5) | 36 | 4,200 | 72 |
| 8 Build cost (AUX) | 3 | 360 | 5 |
| 9 Recap | 3 | 330 | 5 |
| **Total** | **80** | **9,440** | **145** |

## 5.1 Components and technologies (retrofit, 2026-11-22)

<!-- stack:outline -->

| Container | Choice | How it is built | Rejected | Theory part |
|---|---|---|---|---|
| Application DB | PostgreSQL 16, one primary, a synchronous standby, point-in-time recovery | A unique constraint on the application ID means a second booking cannot exist | A distributed SQL database; A key-value store | 04, 07 |
| Decision orchestrator | A Go service: scatter-gather, per-vendor breakers and token buckets | The orchestrator runs the free in-house checks first (about 50 ms), then starts one deadline and calls one bureau, identity and fraud in parallel; bank data is never awaited | A durable workflow engine; A service mesh's timeouts | 08 |
| Policy engine | A rules and model service, every decision stamped with the versions | The engine holds versioned policy, model and pricing | Rules and model baked into the service; Switching the model for everyone | 08 |
| Event log | Outbox row, Kafka, consumers deduplicating by event ID | The outbox row is written in the booking transaction | Publishing directly after the commit; Two-phase commit with the broker | 06 |
| Decision records | Object storage with a retention lock, a key per record | Each decision's inputs, versions and outcome are written as one versioned object under a retention lock, so it cannot be deleted early | The application database; A data warehouse | 08 |
| Identity vault | A tokenisation vault, keys in a hardware-backed key service, an access log | The vault replaces identity values with random tokens and stores the mapping with field-level encryption, with keys in a hardware-backed key service | Raw identity in every service; Encrypting columns in each database | 08 |
| API edge | An API gateway, merchant keys, an idempotency key on every create | The edge authenticates the merchant, rate limits per merchant and requires an idempotency key on every create | No idempotency, retry on the client; Long polling on the connection | 07 |

Fix-slide rejections: 1: Waiting for the slowest vendor; 2: A hard dependency on one bureau; 3: Check, then book, in the service; 4: Booking and funding in one transaction; 5: Rebuilding a decision from today's data; 6: Switching to the new model for everyone; 7: Raw identity in every service; 8: Dashboards of server health.

<!-- /stack:outline -->

## Revision 2026-11-22 (review for a lending / BNPL EM loop)

| Change | Where |
|---|---|
| Cost tiers in the gather: tier-0 in-house checks (≈ 50 ms, ≈ 6 % stopped, ≈ $126k a month) before one parallel gather; full waterfall rejected at the counter (identity p99 pushes past 3 s), kept for pre-approval; soft inquiry recorded | Challenge 1, new slide; booklet 6.1; estimates table |
| The rulebook by name: ECOA / Regulation B, FCRA, fair lending, model risk management, each mapped to fields of the decision record; every rule evaluated stored; features with source and as-of time | Challenge 5, new slide; booklet 6.5 |
| 5.2 alternate path: one bureau and refer; crossover ≈ 330,000 applications a month | new sub-chapter 5.2; booklet Stage 5 |
| C4 component view of the decision orchestrator | 5.1; booklet Stage 5 |
| Contracts between teams (owner → consumers → change rule), Conway's law stated; LoanBooked consumed by SD-95 and SD-99 | Build cost; booklet Stage 10 |
| Consistency fixes: orchestrator no longer "awaits bank data" (stack.json); late calls are recorded, not cancelled (stack.json detail); the gather code is labelled pseudocode (the service is Go) | stack.json, Challenge 1 |
| Layout gate: 57 failures → 0 (C4 views redrawn wide at size 25, overlay notes dropped where the strip said the same, code ≤ 56 columns, ERD sizes) | diagrams.py, chapter files |
