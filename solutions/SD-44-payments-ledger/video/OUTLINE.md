- [x] outline approved  - [x] design  - [x] diagrams  - [x] slides  - [x] script  - [x] video  - [x] publish

# SD-44 · Payment processing and the double-entry ledger — reference-solution video outline

Target level: staff (manager layer AUX) · Target length: 85 min (75–90) · Word budget: 10,300 (≈ 0.49 s a word with the
2026-11-17 pacing beats, measured on SD-94)

Generic content only: no processor, bank or company names or figures. Amounts are in integer minor units of an unnamed currency;
fees in basis points. This is not legal, accounting or compliance advice. Recut of the 26-minute mock round and the
2026-11-20 classics mock round 2, both retired.

## Thesis and definition

- **Thesis** (key-line voice): *Exactly-once does not exist across a network boundary, so the design is at-least-once delivery, an
  effect that happens once per intent, a state for "we don't know yet", and a reconciliation that finds what the rest missed — all
  written to an append-only double-entry journal where a balance is a sum, never a field.*
- **Definition to say aloud**: *A payment system turns a customer's intent to pay into exactly one movement of money between accounts,
  records every movement as balanced, immutable journal entries, and keeps its books in agreement with the outside parties that
  actually move the money.* Load-bearing clauses: **one intent → one movement** (idempotency, not exactly-once delivery), **balanced**
  (double entry, per currency, integer minor units), **immutable** (corrections are new entries), **in agreement with outside parties**
  (reconciliation is a component, not a safety net).
- **Hook**: The happy path is three boxes and a database. The question is about the other paths: a bank call that times out and leaves
  you not knowing whether the customer paid; a client that retries the same payment three times at once; a refund ninety days later; a
  statement that says 999,998 when your books say 1,000,000. Every strong answer is a design for not knowing.

## 0 · What this question grades

| Axis | Weak signal | Strong signal |
|---|---|---|
| Requirements | "Charge the card and store it" | Asks what must never happen, in order; asks how the outside parties fail; asks about refunds, chargebacks and audit length |
| Correctness | A `balance` column updated in a transaction; "retries are safe"; floats | Double entry with derived balances; idempotency key stored with the result in the same transaction; same key + different payload rejected; integer minor units |
| Trade-offs | "Use a distributed transaction with the bank" | States why 2PC is unavailable, picks an explicit state machine with an UNKNOWN state, says what latency it costs |
| Depth | Stops at "retry with backoff" | Timeout walk: UNKNOWN → inquiry by our reference → reversal → settlement file; outbox; hot account sub-accounts; late chargebacks as adjusting entries |
| Operations | Uptime of the API | UNKNOWN count and age, approval rate per processor, Σ = 0 check that pages, unreconciled amount by age with owners, the one-way doors |

## 1 · Requirements and scope

- **Clarifying questions and the interviewer's answers** (asked aloud, seven):
  1. *Volume?* — 10,000 payments a second at peak, 50 currencies.
  2. *Latency?* — An authorisation decision back to the client within 2 seconds.
  3. *Who moves the money?* — Card networks and banks through processors. "They time out, return ambiguous results, and sometimes go down
     for hours."
  4. *What is the ledger's rule?* — "It must always balance. No exceptions."
  5. *Audit?* — Every balance explainable from immutable records for seven years.
  6. *Refunds and disputes?* — Partial refunds, full refunds and chargebacks, arriving days or months later.
  7. *What must never happen, in order?* — (the candidate proposes, the interviewer agrees) charging a customer twice or losing money; an
     unbalanced ledger; a slow payment.
- **Functional requirements**:
  - FR1 · **Pay**: authorise and capture a payment (auto or manual capture), idempotent per client key.
  - FR2 · **Adjust**: void, partial or full refund, chargeback; each referencing the original payment.
  - FR3 · **Notify**: every state change reaches the merchant (signed webhooks) and internal consumers.
  - FR4 · **Reconcile**: match our books against each processor's settlement file daily; every difference becomes an owned break.
  - FR5 · **Explain**: any account's balance at any time, from the journal.
- **Non-functional, with numbers** (initial targets): zero double charges; every journal transaction balanced at commit; decision p99
  under 2 s; API availability 99.95 % for creates (declines are successes); UNKNOWN resolved within 15 minutes for 99 %; reconciliation
  daily with breaks owned and aged; seven-year retention.
- **IN / OUT**: IN: authorise, capture, void, refund, chargeback, webhooks, ledger, reconciliation, multi-currency amounts (no conversion).
  OUT on purpose: fraud scoring (a service we call, SD-43); card data vaulting (a tokenisation service, which keeps us out of most of the
  card-data compliance scope); FX pricing (SD-80); merchant onboarding and KYC (SD-78); payouts to merchants (SD-81, but C4 and C7 need their
  balance check); loans and instalments (SD-95).
- **"The core is 4 things"**: a *state machine* per payment that admits "unknown", an *idempotent API*, an *immutable double-entry journal*,
  and *reconciliation* against the outside world.

## 2 · Estimates

| Number | Arithmetic | Label | Decision it drives |
|---|---|---|---|
| Journal writes | 10,000 payments/s × ~4 entries (capture legs and fee) = **40,000 entries/s** peak | derived | Partition the journal by account; one database primary is not enough at peak |
| Average rate | peak ÷ 3 ≈ 3,300 payments/s; × 86,400 ≈ **2.9 × 10⁸ payments a day** | illustrative | Size the daily settlement files and the reconciliation job |
| Seven-year journal | 3,300/s × 3.15 × 10⁷ s × 7 × 4 entries × ~200 B ≈ **580 TB** | derived | Hot recent partitions plus cold archive; immutability makes archiving a copy, not a migration |
| Hot account | one large merchant at 5,000 payments/s; a row lock held ~1–2 ms allows **500–1,000 updates/s** on one balance row | illustrative, **to be measured** | A balance `UPDATE` cannot keep up: append entries, derive the balance; sub-accounts where a check needs it (C4) |
| Latency budget (2 s) | API + idempotency insert 10 ms + fraud call 50 ms + state commit 10 ms + **processor 300–1,500 ms** + post-commit 20 ms ≈ **1.6 s** worst p99, spare 0.4 s | initial target | Everything we own stays under ~100 ms; at 1.9 s we answer `pending` and keep waiting |
| UNKNOWN rate | 0.1 % of authorisations time out × 10,000/s = **10/s**, 36,000 an hour at peak | illustrative | The inquiry job is a real service with its own throughput and rate limits at the processor |
| Idempotency table | 2.9 × 10⁸ a day × 7-day retention × ~300 B ≈ **600 GB** | illustrative | Keys expire; a retry after the window is a new payment, said in the API contract |
| Settlement file | ~2.9 × 10⁸ lines a day; matched at 1 million lines/s ≈ **5 min** | illustrative | Reconciliation is a batch join, not a manual job; breaks are the output, not the matches |
| Cost lever | processor fees are a percentage of volume; 1 basis point of better routing on the yearly volume outweighs the whole database cluster | illustrative | The cost discussion is about routing and false declines, not servers |

## 3 · Theory

1. **Is / is not.** A payment system is the **orchestration** of an intent across outside parties; the ledger is the **book of record**.
   They are confused, and they fail differently. A ledger is not a **balance table** (a balance is a sum over entries). Idempotency is not
   **deduplication of messages** (it is one effect per intent, with the stored answer returned). **Exactly-once delivery** is not
   **exactly-once effect**: we can have the second, never the first. Reconciliation is not **a safety net for bugs**: the counterparty's truth
   diverges even when our code is correct.
2. **Safety**: S1 · one intent never moves money twice. S2 · every journal transaction balances per currency, in integer minor units. S3 ·
   history is never rewritten: a correction is a new transaction. **Liveness**: L1 · every payment leaves UNKNOWN for a terminal state
   (within minutes by inquiry, at the latest at settlement). L2 · every difference with the outside world becomes an owned break within a
   day. L3 · every state change eventually reaches the merchant.
3. **Central tension**: **speed of the answer against certainty about the truth.** The client wants an answer in two seconds; the truth
   arrives over months. Picture: the *truth timeline*: the response (seconds), the inquiry (minutes), the settlement file (next day), the
   chargeback window (months). Each mechanism lives at one point on it.
4. **Mechanisms** (7). Property → how → failure ruled out → cost.

   | Mechanism | Protects | Rules out | Costs |
   |---|---|---|---|
   | **M1 Idempotency key, stored with the request hash and the result, inserted in the same transaction** | S1 | A retry or a concurrent duplicate creating a second payment; a changed retry silently accepted | A table with retention; a "processing" state the client must handle |
   | **M2 Explicit state machine with UNKNOWN** | S1, L1 | Treating a timeout as failure (double charge on retry) or as success (lost money) | More states, more transitions to test; clients see `pending` |
   | **M3 Immutable double-entry journal, balances derived** | S2, S3, audit | Unexplainable balances; lost cents; a hot row lock on a balance | Storage grows forever; reads need projections |
   | **M4 Transactional outbox** | L3 | A state committed with no event, or an event for a state that rolled back | A relay to run; at-least-once events, so consumers de-duplicate by event ID |
   | **M5 Inquiry and reversal by our own reference** | L1, S1 | An UNKNOWN that stays unknown; a retry the processor can't recognise as the same | A job per processor, rate-limited; processors differ in what they support |
   | **M6 Reconciliation with expectations and owned breaks** | L2, S2 against the outside | Silent divergence from the counterparty's books | A pipeline, a finance-ops workflow, and people |
   | **M7 Sub-accounts or a per-account single writer for hot accounts** | Throughput where a check needs the balance | A merchant serialising on one row; overdrafting a payout | Summing N rows; routing writes; a second place to be wrong |

5. **Options matrix** (rows = approaches; columns = deciding properties; last column = fails when).

   | Approach | One effect per intent | Balanced and auditable | Handles unknown outcomes | Fails when |
   |---|---|---|---|---|
   | A · A balance column updated in a transaction, retries assumed safe | No | No (a number, no history) | No | The first timeout and retry: a double charge; the hot merchant's row lock |
   | B · A distributed transaction (two-phase commit) across our database and the processor | Would be | Would be | — | Always: the processor is not a participant in our transaction; it will not hold a prepare for us |
   | C · An orchestrated saga with compensations, no ledger invariants | Partly | No | Partly | A compensation that itself times out; nothing says what the books should be |
   | **D · State machine with UNKNOWN + idempotency + immutable journal + outbox + inquiry + reconciliation** | Yes | Yes | Yes | The processor gives no way to query by our reference (then the settlement file is the only arbiter, a day late) |
   | E · Event-sourced ledger in a log, balances in stream processors | Yes with keys | Yes | Yes | A synchronous check (refund ≤ captured, payout ≤ available) needs the current balance now; multi-account atomic postings across partitions |
   | F · Buy: the processor's own records, or a ledger service | Yes | Theirs | Theirs | More than one processor, or the company must keep its own books of record |

   **Pick: D**; **F** is the honest V0 for a small company with one processor; **E** is how projections are built inside D. **Gives up:**
   more states, a reconciliation team, and `pending` answers the client must handle, in exchange for never guessing.
6. **Failure catalogue**: F1 timeout, ambiguous result, processor down → C1 (crux part 1) · F2 concurrent retries, changed retry → C2 · F3 crash
   between commit and event → C3 · F4 the hot merchant → C4 · F5 partial refunds and late chargebacks → C5 · F6 our books and the statement
   disagree → C6 (crux part 2) · F7 a bug that posted wrong entries, money already paid out → C7 · F8 nobody notices → C8 · F9 floats and
   currencies: covered on the API slide (integer minor units, currency on every amount), not a challenge.

## 4 · API and entities

| API | Serves | Reads / writes | Wire-format notes |
|---|---|---|---|
| `POST /v1/payments` + `Idempotency-Key` `{merchantId, amount:{value, currency}, methodToken, capture}` → `201 {paymentId, status}` | FR1 | writes **Idempotency**, **Payment**, **Attempt**, **JournalTxn** | `value` in integer minor units; `status` may be `pending`; same key + different body → 422; in flight → 409 |
| `POST /v1/payments/{id}/capture` · `/void` · `/refunds {amount}` + key | FR1, FR2 | **Payment**, **JournalTxn** | refund allowed only if refunded + amount ≤ captured, checked by a conditional update |
| Webhook `POST merchant/url` `{eventId, type, paymentId, status}` signed | FR3 | reads **Outbox** | Retried with backoff; merchants de-duplicate by `eventId` |
| `GET /v1/payments/{id}` | FR1, FR3 | **Payment** | The polling backstop when a webhook is lost |
| internal `Inquire(processor, reference)` | FR1 | **Attempt** | Our reference per attempt: `paymentId + attempt number` |
| internal `ImportSettlement(file)` · `Breaks?status=open&age>1d` | FR4 | **SettlementLine**, **Expectation**, **Break** | The raw file is stored unchanged first |
| `GET /v1/accounts/{id}/balance?asOf=` | FR5 | **JournalEntry**, **BalanceProjection** | From the projection, with the entry ID it is current to |

**Conceptual**: **Payment** 1—N **Attempt** (our reference, processor result); **Payment** 1—N **JournalTxn**; **JournalTxn** 1—N
**JournalEntry** (account, debit or credit, amount, currency); **Account** (owner, type: merchant payable, processor receivable, fee revenue,
refunds…); **Idempotency** (client, key, request hash, status, response); **Outbox** (event); **Expectation** and **SettlementLine** matched
into **Break** (owner, age, resolution).
**Physical**: `journal_entry(account_id, entry_id, txn_id, direction, amount_minor BIGINT, currency CHAR(3))` partitioned by account;
`journal_txn(txn_id, payment_id, type, created_at, idempotency_key)`; a deferred check or posting function that rejects a transaction whose
debits ≠ credits per currency; `payment(payment_id, state, captured_minor, refunded_minor, version)`; `idempotency(client_id, key) UNIQUE`;
`outbox(id, payload, created_at)`; `balance_projection(account_id, balance, as_of_entry)`. **Worked example on screen**: 1,050 captured, 30
fee: processor receivable debit 1,050; merchant payable credit 1,020; fee revenue credit 30.

## 5 · High-level design

| Version | Adds | Objection it answers | Objection it leaves |
|---|---|---|---|
| V1 | One service and one database: `payments` row with a status and a merchant `balance` column; a synchronous call to one processor; update both in one transaction | (none: simplest thing that works) | A timeout leaves no answer; a client retry charges twice; the balance cannot be explained; the hot merchant serialises on its row |
| V2 | **Make the effect once and the books provable**: idempotency key in the same transaction; the state machine with UNKNOWN, committed *before* calling out; our reference per attempt; the immutable double-entry journal, balances as a projection | "A retry must not be a second charge, a timeout must not be a guess, and every balance must be a sum of facts" | Merchants and other systems learn about changes by dual writes; UNKNOWNs pile up; our books can still disagree with the processor's |
| V3 | **Close the loops**: outbox + relay + event log + signed webhooks; the inquiry and recovery job; daily reconciliation with expectations, breaks and a finance-ops console; processor adapters with an error taxonomy; sub-accounts for hot accounts | "Every change must reach the merchant, every unknown must end, and the outside world's books must agree with ours" | The details, which are the challenges |

Baseline spine, left to right: **Merchant / client → Payments API (idempotency) → Payment service (state machine) → Processor adapter →
Processor / network** (grey, external); below the service **Payments DB + Ledger** (payment, attempt, journal, outbox, in one database
per partition); along the bottom **Outbox relay → Event log → Webhook sender / consumers**; on the right **Inquiry job** and **Reconciliation**
reading **Settlement files**; **Finance-ops console** for breaks. Tags: `ch1` inquiry job; `ch2` idempotency table; `ch3` outbox relay;
`ch4` sub-accounts; `ch5` refund check; `ch6` reconciliation; `ch7` correction tool and payout hold; `ch8` probes and the Σ check.

Flows (numbered arrows):
- **FR1 Pay:** 1 `POST /payments` with key · 2 insert idempotency row `processing` (unique) · 3 payment `CREATED → AUTH_PENDING`, attempt row with
  our reference, **commit** · 4 adapter calls the processor with the reference · 5 approved: one transaction: `AUTHORIZED` (or `CAPTURED`),
  journal entries, outbox row, idempotency `done` with the response · 6 201 to the client · 7 relay publishes; webhook.
- **FR2 Adjust (refund):** 1 `POST /refunds` with key · 2 conditional update `refunded + amount ≤ captured` · 3 processor refund with reference ·
  4 new journal transaction referencing the payment, dated now · 5 outbox.
- **FR3 Notify:** 1 outbox row committed with the state · 2 relay reads in order · 3 event log · 4 webhook sender signs and posts; retries with
  backoff · 5 merchant de-duplicates by event ID; `GET` as backstop.
- **FR4 Reconcile:** 1 settlement file lands, stored raw · 2 ledger produces expectations for the day · 3 match by reference and amount · 4
  matched: `SETTLED` with settlement entries (receivable → bank cash, fees) · 5 unmatched: a break with an owner and an age.
- **FR5 Explain:** 1 balance request · 2 projection with `as_of_entry` · 3 for audit, the sum over entries for the period, joined to the
  transactions and their payments.

C4 and sequence views that follow: context; container (reuse `c4-containers` redrawn on the baseline palette); sequences: pay (`seq-pay`),
timeout (`seq-timeout`), idempotency (`seq-idem`), outbox (`seq-outbox`), reconciliation (`seq-recon`); the state diagram (`states`).

## 6 · Bridge and challenge map

*It works. Where does it break first?* Eight attack points. Correctness: C2, C5. Failure recovery: C1, C3, C7. Overload: C4. Outside truth:
C6. Observability: C8. The crux (not knowing, and the outside world's books) gets C1 and C6.

## 7 · Challenges

### Challenge 1 · The bank timed out  *(crux part 1; failure recovery)*

- Q: "You call the processor. It times out. You don't know whether the customer was charged. Walk me through the next ten minutes and the
  next ten days."
- Naive answer: "Mark it failed and let the client retry." (Or: "Retry it ourselves until it works.")
- Case: payment `p-7731`, 1,050, attempt `p-7731/1` sent at 10:00:00.000; no answer by the 1.9 s client deadline; the processor actually
  approved at 10:00:02.4. We said "failed"; the merchant's checkout retried as a new payment `p-7744` at 10:00:05; approved. The customer
  sees two holds of 1,050.
- Break: the arrow from the adapter to the processor, dashed red: a timeout is reported as an answer.
- Fix: **UNKNOWN is a state.** The attempt was committed before the call, so a crash or timeout leaves evidence. At the deadline: state
  `UNKNOWN`, client gets `pending` (and the merchant's retry with the same idempotency key gets the same `pending`, not a new payment). The
  inquiry job asks the processor **by our reference** after 5 s, 30 s, 2 min: approved → `AUTHORIZED` and continue; "not found" after the
  processor's safe window → `DECLINED`, safe to retry with a new attempt; an approval we no longer want → a reversal by reference.
  Ten days later: the settlement file is the final word (C6). Sequence: `seq-timeout`. The state diagram with the UNKNOWN edges.
- Why it works: S1: no path creates a second movement for one intent, because every retry carries the same key or the same reference. L1:
  every UNKNOWN has a bounded way out.
- "What if the fix fails?": "The processor's inquiry endpoint is down too. Actually the whole processor is down for an hour."
- Second fix: a circuit breaker per processor; **fail over to a second processor only for payments that definitely failed or were never
  sent** — never for an UNKNOWN, which would make two possible charges. UNKNOWNs wait and age, with a metric; the merchant sees `pending`.
  Honest limit: a processor that supports neither inquiry nor idempotent references can only be resolved by the settlement file, a day
  late; that is a reason to choose processors.
- If asked, I'd say: "A timeout is an unknown, not a failure. I commit the attempt before calling out, move the payment to UNKNOWN, answer
  pending, and an inquiry job asks the processor by our own reference until it knows. Retries carry the same reference, so they can't
  become a second charge, and the settlement file is the final arbiter."

### Challenge 2 · Three retries at once  *(correctness)*

- Q: "The client sends the same payment three times, concurrently, with the same idempotency key. Then once more with the same key and a
  different amount. What happens?"
- Naive answer: "We check whether the key exists before processing."
- Case: requests R1, R2, R3 with key `k-91` arrive at 10:00:00.001, .002, .003 on three API servers. Each `SELECT`s, finds nothing, and calls
  the processor: three authorisations. At 10:05 R4 with key `k-91` and amount 2,050 instead of 1,050: returning the stored answer hides the
  client's bug; executing it charges again.
- Break: the API's check-then-act, dashed red.
- Fix: **insert the idempotency row first, unique on `(client, key)`, in the same transaction that creates the payment.** One insert wins;
  the others fail the constraint and read the row: `processing` → 409 "in progress, retry"; `done` → the stored response. Store a hash of
  the request: a different body → 422. Sequence `seq-idem`; code: the insert-or-read, twelve lines.
- Why it works: S1 is decided by the database's constraint, the one place every request passes; the stored result makes a retry
  return, not re-execute.
- "What if the fix fails?": "The server that won crashes after the processor approved but before writing `done`."
- Second fix: the row says `processing` with the payment ID; the payment row says `AUTH_PENDING` with the attempt reference: that is exactly
  an UNKNOWN, handled by C1's inquiry. A `processing` row older than a minute is swept into recovery. Retention: keys live seven days; the
  contract says a retry after that is a new payment.
- If asked, I'd say: "The idempotency key is inserted first, with a unique constraint, in the same transaction that creates the payment.
  One request wins; the others get 'in progress' or the stored answer. A different body under the same key is a client bug, so I reject it
  instead of hiding it. And a crash in the middle is just an unknown outcome, which I already handle."

### Challenge 3 · Crash between the ledger and the event  *(failure recovery)*

- Q: "Your service commits the payment and then crashes before telling the merchant. What state are you in?"
- Naive answer: "We publish the event right after commit; crashes are rare."
- Case: 11:20:00.010 commit `CAPTURED` for `p-8102`; 11:20:00.012 the process is killed by a deploy; no event. The merchant's order system
  never ships; the customer is charged and gets nothing. The reverse order (publish, then commit, then the commit fails) ships goods for an
  unpaid order.
- Break: the arrow from the service to the event log, dashed red: two writes, two systems, no shared transaction.
- Fix: **transactional outbox.** The outbox row is part of the same transaction as the state and the journal entries; a relay reads committed
  rows in order and publishes; at-least-once, so consumers and merchants de-duplicate by event ID. Sequence `seq-outbox`.
- Why it works: L3: the event exists if and only if the state committed; delivery is retried until acknowledged.
- "What if the fix fails?": "The relay is behind by twenty minutes. Or a merchant's endpoint is down for a day."
- Second fix: outbox age is a metric with an alert; the relay is partitioned by account so a slow partition doesn't block the rest.
  Webhooks retry with backoff for days, then the merchant is told to reconcile with `GET`; their dashboard shows the state from our database,
  not from the event stream.
- If asked, I'd say: "I never write to two systems and hope. The event is a row in the same transaction as the state change, and a relay
  publishes it at least once. Consumers de-duplicate by event ID, and the merchant can always ask us for the state directly."

### Challenge 4 · The hot merchant  *(overload)*

- Q: "One merchant receives five thousand payments a second. Where does that land?"
- Naive answer: "Update the merchant's balance in each payment's transaction."
- Case: 5,000 transactions a second each taking a row lock on `balance(merchant-42)`, held ~1.5 ms: the row serialises at ~670 a second; the
  queue grows by 4,330 a second; p99 for that merchant passes 2 s in under a second and its payments start timing out — and become UNKNOWNs.
- Break: the balance row in the ledger, dashed red.
- Fix: **append entries; the balance is a projection.** Each payment writes only its own entries (no shared row); a projection updates
  balances asynchronously, seconds behind, which is fine for dashboards. Where a check needs a current balance (a payout must not exceed
  available funds): **split the account into 16 sub-accounts** that receive writes round-robin and sum them, or send payout checks
  through **one writer per merchant**; payouts are rare next to incoming payments. Diagram `hot-account`.
- Why it works: throughput comes from removing the shared row from the hot path; correctness of the rare check comes from serialising
  only the rare operation.
- "What if the fix fails?": "A refund needs 'refunded ≤ captured' per payment, and a payout needs 'paid out ≤ available' right now."
- Second fix: per-payment checks are a conditional update on the payment row (no hot spot: one payment is not hot). Payout ≤ available reads
  the sum of sub-accounts under the merchant's single payout writer, then posts the payout transaction. Honest limit: the projection lag must
  be measured and stated to the payouts team.
- If asked, I'd say: "Five thousand updates a second to one balance row would serialise on its lock. So payments only append entries and
  the balance is derived. Where a check needs the balance now, like a payout, I split the account into sub-accounts or serialise just that
  rare operation through one writer."

### Challenge 5 · Refunds and a chargeback ninety days later  *(correctness, late events)*

- Q: "A payment was partially refunded twice. A third refund arrives. Then, three months later, a chargeback. How does the ledger stay right?"
- Naive answer: "Update the payment's amount and the merchant's balance."
- Case: `p-5520` captured 10,000; refunds of 3,000 and 4,000 done, so 7,000 refunded. Two refund requests of 2,500 arrive 2 ms apart; each
  reads 7,000, each checks 7,000 + 2,500 ≤ 10,000 and passes: 12,000 refunded on a 10,000 payment. On day 92 a chargeback for the remaining
  amount arrives; the month it belongs to was closed and reported.
- Break: the refund path's read-then-write, and the edit of a closed period, dashed red.
- Fix: **each adjustment is a new journal transaction referencing the original; the limit is one conditional update**: `UPDATE payment SET
  refunded = refunded + :a WHERE id = :p AND refunded + :a <= captured`: one succeeds, one is rejected. The chargeback posts entries **dated
  now**, referencing the payment, to a disputes account; the closed period is never rewritten. The state machine: `CAPTURED →
  PARTIALLY_REFUNDED → REFUNDED`, `SETTLED → CHARGEBACK`. Code: the conditional update.
- Why it works: S2 and S3: history is append-only, so the closed month still adds up and the correction is visible as a correction.
- "What if the fix fails?": "The merchant wins the dispute: the chargeback is reversed. Or the refund is in a different currency."
- Second fix: a reversal is one more transaction (dispute won: disputes account back to the merchant); currency: amounts stay in the original
  currency, and any conversion is its own transaction with the rate it used, versioned. Honest limit: the rules for who bears the loss are
  contracts, not code: finance owns them.
- If asked, I'd say: "Nothing is edited. A refund, a chargeback or a reversal is a new balanced transaction that references the payment and
  is dated when it happened, so closed months still add up. The refund limit is one conditional update on the payment row, so two
  concurrent refunds can't both pass."

### Challenge 6 · 999,998 against 1,000,000  *(crux part 2; the outside truth)*

- Q: "The processor's settlement statement says 999,998. Your books say 1,000,000. What now?"
- Naive answer: "We'd look into it; our system is correct by construction."
- Case: yesterday's file has 2.9 × 10⁸ lines. Three differences: a capture of 1,050 we booked late in the day that settles tomorrow
  (theirs −1,050, timing); an UNKNOWN we resolved as declined that the processor actually settled (theirs +1,050, a real break: the
  customer paid); a fee 2 higher than the contract on one line (theirs −2). The totals differ by 2, but there are three breaks, and the
  one that matters most is invisible in the total.
- Break: the reconciliation box, missing from the V2 baseline, drawn dashed red.
- Fix: **reconciliation as a permanent, designed component.** Store the raw file unchanged. The ledger generates **expectations** (what should
  settle, by reference, net of fees). Match line by line, not totals. Each unmatched line is a **break** with a type (missing on their side,
  missing on ours, amount, timing), an owner, and an age; timing breaks auto-close when the next file matches; real breaks get an adjusting
  transaction with a reason. Sequence `seq-recon`.
- Why it works: L2: every difference becomes a named, owned item; S2 holds against the outside world, not only inside our database.
- "What if the fix fails?": "There are forty thousand breaks this morning, not forty."
- Second fix: a spike is an incident, not a backlog: classify by type and processor first (one cause usually explains thousands), stop
  payouts if the break amount crosses a threshold, and fix the cause before the lines. Breaks by age is a dashboard with an SLO; finance ops
  is a team with tooling, said out loud.
- If asked, I'd say: "Reconciliation isn't a safety net for a buggy system; it's a permanent component, because the processor's truth and ours
  diverge even when our code is right. I match line by line against expectations from the ledger, every difference becomes a break with an
  owner and an age, and a spike in breaks is treated as an incident."

### Challenge 7 · A bug double-posted 40,000 entries  *(failure recovery; the EM half)*

- Q: "A bug double-posted forty thousand entries last night, and some merchants have already been paid out. What do you do?"
- Naive answer: "Write a script to delete the duplicates."
- Case: release 2026.11.19 posted the fee leg twice for 40,000 captures between 22:10 and 23:40; 1,200 merchants' payable balances are too high
  by the fee; 180 of them were paid out at midnight.
- Break: the ledger, dashed red; and a `DELETE` arrow, crossed out.
- Fix: **stop, identify, reverse, recover, learn.** Kill-switch the release and **hold payouts** for affected merchants. Identify the duplicates
  exactly from the immutable journal (same payment, same type, two transactions). Post **one reversing transaction per duplicate**, tagged
  with an incident ID: the audit trail shows the error and the correction. For the 180 already paid: a receivable from the merchant, recovered
  from future settlements, with a message — a business decision with communication, not a database operation.
- Why it works: S3 makes the correction tractable and provable: nothing was overwritten, so the duplicates can be found and reversed exactly.
- "What if the fix fails?": "Idempotency should have stopped this. Why didn't it?"
- Second fix: the bug was inside one request (a second posting with a new transaction ID); add an invariant: one fee transaction per capture,
  enforced by a unique constraint on `(payment_id, type)` for single-occurrence types, and a reconciliation check within the hour that would
  have flagged it. Postmortem on the class.
- If asked, I'd say: "Stop the bleeding first: kill the release and hold payouts. Because the journal is immutable I can find the duplicates
  exactly and post reversing entries tagged with the incident, so the audit trail shows both. Money already paid out is a receivable and a
  conversation with those merchants. Then a constraint and an hourly check so this class can't repeat silently."

### Challenge 8 · How would you know before finance does?  *(observability)*

- Q: "What do you watch, and what alert fires before finance notices something is wrong?"
- Naive answer: "API error rate and latency."
- Case: at 02:00 one processor starts declining 6 % more card payments from one country after a change on its side. API errors: zero (declines
  are successes). Latency: normal. Merchants notice at 09:00 when their sales are down.
- Break: the monitoring view of the baseline, dashed red: no metric on the money.
- Fix: **SLIs on the money and the truth.** Payment success excluding legitimate declines; **approval rate per processor, per country, per
  card type, against its own baseline**; UNKNOWN count and **age**; outbox age; **Σ debits − Σ credits = 0** checked continuously (any non-zero
  pages immediately); unreconciled amount by age. **Symptom pairs**: approvals down + latency normal = a processor or issuer change, not us;
  UNKNOWN up + latency at the timeout = processor slow; outbox age up + commits normal = relay stuck; breaks up + UNKNOWN up yesterday =
  inquiry not resolving.
- Why it works: the alerts measure what finance and merchants measure, a day earlier.
- "What if the fix fails?": "The approval rate drops slowly, half a percent a week."
- Second fix: weekly comparison against a seasonal baseline per segment, and a synthetic payment per processor every minute with a test card.
  The on-call runbook for "payments failing at 3 a.m." starts from these pairs.
- If asked, I'd say: "I watch the money, not the servers: approval rate per processor and segment against its baseline, the count and age of
  unknown outcomes, outbox age, unreconciled amount by age, and a continuous check that the ledger sums to zero, which pages immediately.
  Then I read metrics in pairs to tell 'the processor changed' from 'we broke'."

## 8 · Build cost (AUX)

- **V1**: buy a processor with its hosted payment page and token vault (keeps card data out of our scope); 3 engineers, 1 quarter.
- **V2**: idempotency, state machine, journal: 5–6 engineers, 2 quarters. **V3**: outbox, inquiry, reconciliation, second processor: two teams,
  2–3 quarters, plus a finance-ops function.
- **One-way doors**: the ledger schema and the idempotency contract; both get the most review, because merchants and auditors depend on them for years.
- **Team seams**: *payments API and state machine* · *ledger* (owned centrally, a contract for everyone) · *processor integrations* ·
  *reconciliation and finance tooling*. The ledger team reviews every new transaction type.
- **Cost, illustrative**: infrastructure is small next to processor fees; the engineering levers on cost are routing (basis points) and
  false declines.
- **Top risks**: an untested UNKNOWN path; reconciliation built last; a second processor added without its own inquiry semantics.

## 9 · Recap

Final diagram: the V3 baseline. One sentence per path: *Pay:* key first, attempt committed, call by reference, one transaction for state,
entries and event. *Adjust:* a new transaction, a conditional limit. *Notify:* outbox, at least once, de-duplicated. *Reconcile:* expectations,
line by line, breaks owned. *Explain:* a sum over immutable entries.
**Common mistakes**: "a distributed transaction with the bank"; a balance column as the truth; a timeout treated as a failure; floats; idempotency
keys checked, not inserted; same key with a new amount silently accepted; publishing events outside the transaction; editing history; no
reconciliation, or reconciliation by totals; no owner for breaks.
**Closing line (key-line voice):** "I can't get exactly-once across the boundary, so I get one effect per intent: a key inserted first, a
reference on every call, a state for not knowing, and an inquiry that ends it. Every movement is a balanced, immutable entry, so any balance is
a sum I can explain. And because the outside world's books will disagree with mine anyway, reconciliation is part of the design, with owners."

## Canon check

| Canonical point | Source | Covered at, or dismissed because |
|---|---|---|
| Pay-in flow through a payment service and an external processor | standard treatments; cue sheet | Ch. 5 V1–V3; FR1 flow |
| Hosted payment page / tokenisation to keep card data out of scope | standard treatments | Ch. 1 OUT; ch. 8 V1 |
| Double-entry ledger | all | M3; ch. 4 worked example; C5 |
| Idempotency keys; exactly-once as at-least-once + idempotent effect | all | M1; precision statement in theory 1; C2 |
| Retry with backoff; dead-letter for failures | standard treatments | C1 (retries carry the reference); C3 (webhooks with backoff); dead-letter = break or aged UNKNOWN |
| Reconciliation with settlement files | all | M6; C6 |
| Handling a PSP timeout / unknown outcome | cue sheet (crux) | C1 |
| Sagas and compensations | cue sheet | Options matrix row C; C1 reversal; dismissed as the core model because compensation can itself be unknown |
| Outbox | cue sheet | M4; C3 |
| Hot account | cue sheet | C4 |
| Wallet / stored balance product | some treatments | Dismissed aloud: a different product (stored value) with its own regulation; the same journal underneath |
| Payouts to merchants | some treatments | OUT (SD-81); payout checks in C4 and C7 |
| Fraud | all | OUT (SD-43), one call in the latency budget |
| Multi-currency | cue sheet | Ch. 4 (currency on every amount); C5 second fix |
| What changed since older treatments | — | Network tokens and processor idempotency keys are now common, which makes M5 easier; the UNKNOWN state is still needed |

## From the old version (26-minute mock round)

| Reused | New | Dropped |
|---|---|---|
| Clarifying answers, estimates, the six deep dives (now C1–C6), the curveball (C7), the SVGs `states`, `seq-pay`, `seq-timeout`, `seq-idem`, `seq-outbox`, `seq-recon`, `hot-account`, `c4-*` | Theory chapter; options matrix with the 2PC row; V1→V2→V3 on a carried baseline; five numbered flows; C8 observability with symptom pairs; the truth timeline; build cost; canon check | Interviewer–candidate–coach dialogue frame; follow-up figures `fu-fees`, `fu-offline` (offline payments are out of scope), `fu-processor` (folded into C1) |

## Budget

| Chapter | Minutes | Words | Slides |
|---|---|---|---|
| 0 Cold open | 3 | 360 | 5 |
| 1 Requirements and scope | 6 | 730 | 11 |
| 2 Estimates | 5 | 610 | 10 |
| 3 Theory | 11 | 1,330 | 18 |
| 4 API and entities | 6 | 730 | 10 |
| 5 High-level design | 11 | 1,330 | 20 |
| 6 Bridge | 1 | 100 | 2 |
| 7 Challenges (8 × ~4.6) | 37 | 4,500 | 72 |
| 8 Build cost (AUX) | 3 | 360 | 5 |
| 9 Recap | 3 | 360 | 6 |
| **Total** | **86** | **10,410** | **159** |

**Actual (after the build, 2026-11-20): 73:56, 8,977 words, 160 slides.** Shorter than planned (86 min): the challenges ran about 450 words each against 560 planned. Within the 60–90 minute target.
