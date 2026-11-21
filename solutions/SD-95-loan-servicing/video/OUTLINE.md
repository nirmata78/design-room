- [x] outline  - [x] design  - [x] diagrams  - [x] slides  - [x] script  - [x] video  - [x] publish

# SD-95 · Instalment loan servicing: ledger and collections scheduler — reference-solution video outline

Target level: staff (manager layer AUX) · Target length: 80 min (70–90) · Word budget: 9,800 (≈ 0.49 s a word with the
2026-11-17 pacing beats, measured on SD-44 and SD-96)

Generic content only: no lender, processor or bank names or figures. US-style rails are used because the cue sheet names them
(bank debit = ACH, card); amounts in dollars, stored as integer cents. Rule-based claims (ACH return windows, re-presentment
limits) were checked in November 2026 (`../VERIFY-claims-2026-11-20.md`). Not legal, accounting or compliance advice.
Recut of problem 2 of the 2026-11-20 fintech mock series (retired).

## Thesis and definition

- **Thesis** (key-line voice): *In loan servicing, throughput is never the problem; correctness over months is. Money moves in
  days and can come back weeks later, so the design is an immutable double-entry ledger, a payment state machine that admits
  "unknown" and "returned", a scheduler bounded by the rail rather than the database, and a daily three-way reconciliation.*
- **Definition to say aloud**: *A loan servicing system turns each loan's terms into a schedule of amounts due, collects each one
  once through rails that answer in days and can reverse weeks later, records every movement as balanced, immutable ledger lines,
  and proves every day that its books agree with the processor's and the bank's.* Load-bearing clauses: **terms → schedule**
  (policy is versioned data), **once** (idempotency at three layers, not exactly-once delivery), **answer in days, reverse weeks later**
  (PENDING, UNKNOWN and RETURNED are states; SETTLED is not final), **balanced, immutable** (double entry, reversals), **proves every
  day** (three-way reconciliation is a component).
- **Hook**: 600,000 collections on the 1st sounds like a thundering herd. It is 42 a second, which any database absorbs. The hard
  parts are elsewhere: a card charge that times out, a debit that "settled" and comes back 40 days later, a refund that changes the
  schedule under a live loan, and a month-end where the ledger says $400 more than the bank.

## 0 · What this question grades

| Axis | Weak signal | Strong signal |
|---|---|---|
| Requirements | "Charge everyone on the due date" | Asks the rails, their limits and cut-offs, refunds, returns, audit length; names what must never happen |
| Correctness | A balance column; retry on any error; SETTLED = done | Double entry with reversals; keys at three layers; UNKNOWN and RETURNED as states |
| Trade-offs | "Kafka for the thundering herd" | Says 42/s is nothing for a database; the binding limits are the processor contract and the bank cut-off; a broker is optional |
| Depth | Stops at "retry with backoff" | Claim with SKIP LOCKED + intent + outbox in one commit; token bucket per rail; re-presentment limits; allocation waterfall |
| Operations | API uptime | UNKNOWN age, debit file acknowledged by the cut-off, return rate by reason, breaks by age and amount, Σ = 0 nightly |

## 1 · Requirements and scope

- **Clarifying questions and answers** (asked aloud, seven): portfolio (5M active loans, 3–12 monthly instalments) · rails (bank
  debit 80 %, card 20 %, card numbers tokenised at the processor) · peak (due dates cluster: 600,000 collections on the 1st) · limits
  (card processor contract 100/s; bank debit files have daily cut-offs, we take 14:00) · refunds (merchants refund fully or partly at
  any time) · audit (every cent explained for 7 years; month-end close in 2 days) · what must never happen, in order (candidate
  proposes: charge twice; an unexplained cent; a customer penalised for our fault; then lateness).
- **FR1 Schedule**: a booked loan becomes a schedule of instalments from its terms version. **FR2 Collect**: on each due date, collect
  by bank debit or card; retries and late fees per policy. **FR3 Adjust**: merchant refunds, extra payments, early payoff — re-amortise
  or shorten per the terms; allocation waterfall. **FR4 Absorb returns**: bank debit returns (NSF within 2 banking days, unauthorised up
  to 60 days) and card disputes reverse a collection. **FR5 Reconcile**: ledger vs processor vs bank daily; month-end close in 2 days.
- **NFRs** (initial targets): 0 customers charged twice for one instalment · 0 unexplained differences at close · the day's debit file
  submitted by 10:30, cut-off 14:00 · UNKNOWN resolved within 1 hour for 99 % · every line kept and explainable 7 years · close in 2 days.
- **IN**: schedules, two rails, retries and returns, refunds, late fees, payoff, the ledger, reconciliation, customer notices (events).
  **OUT** (said aloud): origination and underwriting (SD-82), collections agencies and hardship beyond a pause flag, statement design,
  tax reporting, payouts to merchants (SD-81), funding/securitisation of loans.
- **The core is four things**: a ledger that is never edited, a payment state machine with UNKNOWN and RETURNED, a scheduler bounded by
  the rail, and reconciliation against the outside.

## 2 · Estimates

| Number | Arithmetic | Label | Decision it drives |
|---|---|---|---|
| Busy day rate | 600,000 ÷ (4 h × 3,600 s) ≈ 42/s | derived from given | The database is the queue; a broker is not needed for load |
| Card share | 600,000 × 20 % = 120,000 | derived | — |
| Card minimum time | 120,000 ÷ 100/s = 1,200 s = 20 min; at 90/s ≈ 22 min | derived | A token bucket per rail at 90 % of contract; the card window is a plan, not a burst |
| Debit file | 480,000 entries × 94 B ≈ 45 MB | illustrative (fixed-width record) | A batch built hours before the cut-off, validated, acknowledged |
| Money on the 1st | 600,000 × $150 ≈ $90M | illustrative average instalment | A 0.1 % error is $90k: correctness beats speed |
| Returns | 480,000 × 3 % NSF ≈ 14,400 on days 2–3 | illustrative rate | Returns are a workload with its own pipeline, not an exception |
| Unknowns | 120,000 × 0.2 % timeouts ≈ 240 on the 1st | illustrative | A resolver service, small but each item is a possible double charge |
| Ledger size | 5M loans × 4 lines/month = 2 × 10⁷; × 84 months × 200 B ≈ 340 GB | derived + illustrative | One relational database, partitioned by month; no sharding; archive read-only |
| Interest accrual | daily lines would be 5M × 30 × 2 = 3 × 10⁸ a month | derived | Accrue by calculation; post at events and at month-end, not daily lines |

## 3 · Theory

1. **Is / is not**: definition above. Not a payment gateway (SD-44: one payment in seconds; here many payments over months against
   a schedule). Not a cron job. A ledger is not a balance table. SETTLED is not final.
2. **Safety**: S1 one instalment is never collected twice · S2 every ledger transaction sums to zero in integer cents, and lines are
   never edited · S3 no customer is penalised beyond policy or for our fault (fees, re-presentments ≤ 2, late marks). **Liveness**:
   L1 every due instalment is attempted on its due date before the rail's cut-off · L2 every payment leaves UNKNOWN and PENDING for
   SETTLED or RETURNED within a bound · L3 every difference between ledger, processor and bank becomes an owned break within a day,
   closed or explained before month-end close.
3. **Central tension**: when money is final. Timeline picture `truth`: seconds (card answer, or nothing) · 1–2 days (debit settles) ·
   2 banking days (NSF return) · 60 days (unauthorised return) · months (refunds, card disputes) · 7 years (audit). Booking cash early
   (finance) against waiting (risk): book at settlement, age the exposure.
4. **Mechanisms**:

   | Mechanism | Protects | Rules out | Costs |
   |---|---|---|---|
   | M1 Immutable double-entry ledger, balance projection in the same commit with a version | S2, audit | unexplained balances, lost cents, interleaved postings | storage that only grows; reversals for every fix |
   | M2 Payment state machine with UNKNOWN and RETURNED | S1, L2 | a timeout treated as failure; a return with nowhere to go | more states and tests; "pending" in statements |
   | M3 Idempotency at three layers: ledger key (loan, instalment, attempt), the same key at the processor, one open intent per instalment | S1 | duplicate posting, duplicate charge, two workers' intents | key discipline; the attempt-number rule |
   | M4 Database as the queue: claim with SKIP LOCKED; intent + outbox in one commit; sweeper | L1 | lost or doubly-claimed due items; a commit with no send | polling; a sweeper to run |
   | M5 A rail budget: token bucket per rail, pause switch, a day plan back-scheduled from the cut-off | L1, S3 | self-inflicted throttling and declines; a missed cut-off | planning; live limits from the adapter |
   | M6 Policy as versioned data: allocation waterfall, retry schedule, fees, refund treatment | S3, audit | undocumented behaviour; a rule change nobody can explain | a rules component; owners in risk and legal |
   | M7 Three-way reconciliation: expectations, match by reference, owned and aged breaks | L3 | silent divergence; plugs at close | a pipeline, a console, people |

5. **Options matrix** (deciding columns: one collection per instalment · explains every cent · respects the rail · fails when):
   A cron at midnight + balance column + retry on error (rejected) · B a broker fan-out of 600k messages to workers, no state machine
   (rejected) · C an event-sourced loan aggregate in a log (rejected as the core; how projections could be built) · **D relational
   ledger + state machine + DB-as-queue + rail budget + policy as data + three-way reconciliation (pick)** · E buy a servicing platform
   (honest V0 for a small book; fails at product-specific refunds and when we must own the books). **D gives up**: more states, a
   reconciliation team, "pending" for days on statements, and every product change becomes a policy version with an owner.
6. **Failure catalogue → challenges**: timeout (C1, crux) · the morning of the 1st (C2) · a settled debit returns (C3, crux) · refund
   mid-loan (C4) · payoff with a debit in flight (C5) · month-end mismatch (C6) · processor down on the 1st (C7) · nobody notices (C8).

## 4 · API and entities

| API | Serves | Reads / writes | Wire-format notes |
|---|---|---|---|
| event `LoanBooked` | FR1 | writes Loan, ScheduleVersion, Instalment, LedgerTxn | loanId, principal cents, termsVersion, first due date, rail + mandate ID; idempotent by loanId |
| `POST /loans/{id}/payments` | FR2, FR3 | Intent, Attempt, LedgerTxn | Idempotency-Key; amount cents; "extra" or "instalment" |
| `POST /loans/{id}/refunds` | FR3 | LedgerTxn, ScheduleVersion | from the merchant; merchantRefundId as key; partial allowed |
| `GET /loans/{id}/payoff-quote` | FR3 | reads Balance, pending Intents | quoteId, amount, validUntil, lists in-flight items |
| `Charge(key)` / `Query(key)` | FR2 | Attempt | the attempt key passed to the processor |
| `SubmitDebitFile` / `ImportReturns` / `ImportSettlement` | FR2, FR4, FR5 | Attempt, ReturnRecord, SettlementLine | raw files stored unchanged first |
| `GET /breaks?age>1d` · `PUT /rails/{rail}/pause` | FR5, ops | Break, RailConfig | console |

Entities: Loan · ScheduleVersion (from a TermsVersion) · Instalment · PaymentIntent (one open per instalment) · Attempt (per send,
carries the key) · LedgerTxn · LedgerLine · Account (per loan: principal, interest, fees; system: cash clearing, cash, merchant
receivable, customer payable) · BalanceProjection · Outbox · ReturnRecord · Break. Physical: `due_item(due_date, shard, status)`
index; `payment_intent` partial unique index on `instalment_id WHERE state IN open states`; `ledger_txn.idem_key` unique;
`ledger_line` partitioned by month, insert only; `account_balance(account, balance_cents, version)`.

## 5 · High-level design

| Version | Adds | Objection it answers | Objection it leaves |
|---|---|---|---|
| V1 | a cron at 00:00 loops over due loans, calls the processor, updates a balance column | (simplest thing that works) | midnight spike throttled; timeout + retry = double charge; a return has nowhere to go; no history |
| V2 | ledger (lines + projection), state machine, scheduler claiming from the DB, dispatcher with a token bucket per rail, card + bank-file adapters | double charge, load against the rail, history | returns and settlements arrive later; refunds and payoff change schedules; unknowns pile up; nobody checks the bank |
| V3 | file ingest (returns, settlement, statements), resolver for UNKNOWN, policy (terms, waterfall, retries, fees), three-way reconciliation + finance ops, outbox → notices | every loop closed | the challenges |

Baseline spine, left to right: Customer & merchant · Servicing API · Schedule & collections · Dispatcher · Rails. Row 2: Policy ·
Servicing DB · File ingest · Resolver. Row 3: Notices · Reconciliation · Finance ops. Origination above-left. Tag-only: Payoff quote
(C5), Day plan (C2), Probes (C8), Rail switch (C7).
Flows: FR1 LoanBooked → API → schedule from policy → instalments + booking txn. FR2 claim → intent + outbox → dispatcher → rail →
result → post. FR3 refund/payoff → API → policy waterfall → new schedule version + txn. FR4 return file → ingest → reversal → notice.
FR5 settlement + statement → ingest → reconciliation vs expectations → breaks → finance ops.
C4 context and containers; sequences: collect (card), resolve UNKNOWN, claim, return, refund, payoff, reconcile, probe.

## 7 · Challenges

### Challenge 1 · The processor timed out
- Q: "The processor times out on a card charge. Your worker retries. Was the customer charged twice?"
- Naive: mark it failed and retry (new attempt, new key).
- Case: ln-5531 instalment 2, $150, key coll:ln-5531:2:1 sent 08:00:00; approved 08:00:03.2; worker timeout 08:00:10; retry as attempt 2 approved 08:00:12 → $300.
- Break: Dispatcher ↔ Rails. Fix: UNKNOWN; resolver queries by the same key at 30 s, 2 min, 10 min; same attempt = same key; new attempt only after a definite decline · sequence `seq-unknown` · code: the resolve loop.
- Why: S1 (one key per decision), L2 (bounded exit).
- Push: "Query says not found, and the charge appears in tomorrow's settlement file." · Second: not-found is final only after the processor's documented window; resend with the same key; the settlement file is the arbiter; a found duplicate is auto-refunded and counted.
- If asked: a timeout is not a failure; one key per decision, query never resend, the file is the arbiter.

### Challenge 2 · The morning of the 1st
- Q: "600,000 payments are due on the 1st. Walk me through that morning."
- Naive: a cron at midnight; or "Kafka for the thundering herd".
- Case: 00:00 workers send 2,000/s; 00:00:03 throttled, 95 % rejected; retries triple the load; 18,000 card charges marked failed; the debit file built at 13:55 fails validation; cut-off 14:00 missed; 480,000 slip a day.
- Break: Dispatcher and Schedule. Fix: day plan back-scheduled from the cut-off: debit file built 09:00, submitted 10:30; card window 06:00 at 90/s ≈ 22 min; claim with SKIP LOCKED, intent + outbox in one commit · code: the claim SQL · sequence `seq-claim`.
- Why: L1 and S3 (our throttling must not become a customer's decline).
- Push: "At 06:10 the processor lowers you to 50/s." · Second: the bucket rate is live, halves on throttle signals; by 06:10, 54,000 are done; the other 66,000 at 50/s take 22 min, done by 06:32; spread due dates at origination removes the peak at the source.
- If asked: 42/s is nothing; the limit is the rail; back-schedule from the cut-off and rate-limit per rail.

### Challenge 3 · It settled, then it came back
- Q: "A bank debit settled on the 2nd. On the 3rd it comes back for insufficient funds. Another one comes back 40 days later as unauthorised."
- Naive: settled means paid; close the instalment; retry anything that fails.
- Case: ln-7702 #3 $150 submitted Dec 1, settled Dec 2, R01 Dec 3; ln-4410 #2 $150 settled Dec 2, R10 Jan 11 (day 40); naive retries R10 → rule breach; balance column already reduced.
- Break: File ingest → DB. Fix: RETURNED from SETTLED; a reversing transaction dated the return day; instalment PAID → DUE with a reason; policy: NSF re-presented ≤ 2 (after payday rule), unauthorised never retried, needs a new authorisation · sequence `seq-return`.
- Why: S2 (no edit), S3 (rules), L2.
- Push: "Finance wants the cash on settlement day; risk wants to wait 60 days." · Second: post cash at settlement into an account that is returnable, report exposure by age (settled within 60 days), price the risk; merchant funding never waits on it.
- If asked: settled is not final for a bank debit; returns are reversals and a state, and retry rules are policy.

### Challenge 4 · A refund in the middle of the loan
- Q: "After two instalments, the merchant refunds $300 of the $1,200. What changes?"
- Naive: subtract $300 from the balance.
- Case: 8 × $150; paid 2 → $900 outstanding; refund $300; schedule untouched → 6 × $150 = $900 collected on $600 owed → $300 over.
- Break: Schedule + DB. Fix: refund = ledger txn (merchant receivable 300 / loan principal 300); a new schedule version per the terms: re-amortise (6 × $100) or shorten (4 × $150); allocation waterfall versioned · sequence `seq-refund`.
- Why: S2, S3, audit (the version says why).
- Push: "The merchant refunds the full $1,200 after the customer paid $900." · Second: principal → 0, $900 to customer payable, refunded to the original method within the policy days; merchant discount returned per the contract.
- If asked: a refund is a transaction and a new schedule version; which way it lands is a decision in the terms.

### Challenge 5 · Paying off with a debit in flight
- Q: "The customer pays off early on the 3rd, while instalment 3's debit from the 1st is still pending."
- Naive: quote the balance.
- Case: $900 outstanding incl. the pending $150. Quote $900 → paid by card, debit settles → $150 over-collected. Quote $750 → loan closed; Dec 4 the $150 returns NSF → a closed loan owes $150.
- Break: API quote + DB. Fix: the quote lists in-flight items: $750 now, conditional; loan → PAID_PENDING until the pending item clears its NSF window; if it returns, $150 reopens as a single due item (not a late mark); quote has an ID, validity and idempotency · sequence `seq-payoff`.
- Why: S1, S3, L2.
- Push: "A merchant refund arrives the day after payoff." · Second: overpayment to customer payable; automatic refund; never silently held.
- If asked: a payoff quote is a statement about the future; list what's in flight and close only when it clears.

### Challenge 6 · $400 more than the bank
- Q: "Month-end: the ledger says we collected $400 more than the bank received. Find it."
- Naive: compare totals and post a $400 plug.
- Case: ledger $90,000,400 vs bank $90,000,000. Inside: two NSF returns $300 on the bank statement Nov 30, return file not ingested (timing) · a $100 chargeback netted by the processor, none in the ledger (real) · +$150 a card payment we hold as settled that the processor never settled (real) · −$150 a charge the processor settled that we hold as declined (real: a double charge). 300 + 100 + 150 − 150 = 400.
- Break: Reconciliation. Fix: expectations from the ledger; match by reference, then amount + date window; three-way (ledger, processor report, bank statement); breaks typed, owned, aged; timing auto-closes · sequence `seq-recon`.
- Why: L3; totals hide offsetting breaks.
- Push: "The processor's month-end file is two days late." · Second: close with documented open items, aged; honest limit.
- If asked: never reconcile by totals; match each line by reference three ways, own every break.

### Challenge 7 · The card processor is down on the 1st
- Q: "06:11 on the 1st, the card processor goes down with 60,000 charges left. What do you do?"
- Naive: keep retrying; or mark everyone failed and charge late fees tomorrow.
- Case: 06:00–06:11 at 90/s ≈ 59,400 done; 180 in flight at 06:11 → UNKNOWN; blind retries add 9,000 more timeouts by 06:20; tomorrow 60,000 late fees at $10 = $600,000 charged for our outage.
- Break: Dispatcher ↔ Rails. Fix: breaker opens, card rail paused; unknowns resolved first; policy "our outage is not your late fee" (the late clock runs from our attempt window); resume at 50/s, ramp · tokens are processor-specific: no failover of cards; ACH fallback only where a mandate exists.
- Why: S1, S3, L1 (eventually).
- Push: "It lasts until 15:00, past the debit cut-off." · Second: collect tomorrow; grace extended automatically; customer notice; the day plan re-runs.
- If asked: pause, resolve unknowns first, never charge for our outage, resume under a lower limit.

### Challenge 8 · How would you know before month-end?
- Q: "How would you know any of this is going wrong before finance finds it at close?"
- Naive: API error rate and latency.
- Case: Dec 1 debit file accepted with 12,000 entries rejected for an account-format change; APIs green; nobody looks at the acknowledgement; Dec 2 customers get late notices; found at close.
- Break: Dispatcher → Rails → ingest. Fix: SLIs on money: funnel due → claimed → sent → acknowledged → settled by rail; file acknowledged by 11:00; UNKNOWN count and age; returns by reason code vs baseline; breaks by age and amount; Σ = 0 and projection = Σ lines nightly · symptom pairs · sequence `seq-probe`.
- Push: "A rule change misallocates $4 on 30,000 loans; everything sums to zero." · Second: shadow-run a new policy version on yesterday's postings and diff; per-loan invariant schedule = outstanding principal.
- If asked: watch the money funnel and the files, not the servers; read metrics in pairs.

## 8 · Build cost (AUX)

V1 ledger + scheduler + card rail, 4 engineers × 2 quarters · V2 bank-file rail, returns, policy as data, 6 × 2 quarters · V3
three-way reconciliation, finance console, runbooks, due-date spreading, 2 teams × 2 quarters + finance ops. Buy against build: a
servicing platform for V0 on a small book. One-way doors: chart of accounts and ledger schema; terms versioning (contracts cite it);
the key format shared with the processor. Six team seams (ledger is the one writer). Risks: the return path rarely tested; month-end
found by hand; one processor holds the card tokens.

## 9 · Recap

`base-final` · one sentence per path (schedule, collect, adjust, return, reconcile) · common mistakes · four sentences · thesis.

## Canon check

| Canonical point | Source | Covered at, or dismissed because |
|---|---|---|
| Double-entry ledger, immutable lines | cue sheet; standard payment/ledger treatments | M1; ch. 4 worked entries; C3, C4 |
| "Never store a balance" | common prep | Corrected: a projection in the same commit, provable, checked nightly (M1) |
| Idempotency keys | all | M3; C1 |
| Payment state machine; UNKNOWN; RETURNED | cue sheet (crux) | M2; C1; C3 |
| Scheduler / cron at scale; "thundering herd" | common prep; cue sheet trap | Estimates; M4, M5; C2 |
| Broker (Kafka) for the work queue | common prep | Options row B; outbox kept for correctness, broker optional |
| Dunning / failed-payment retries, late fees | billing treatments | M6; C3; C7 |
| Refunds, proration, re-amortisation | cue sheet | C4; allocation waterfall |
| Early payoff, interest accrual | cue sheet | C5; estimates (accrue by calculation) |
| Bank-debit return codes and windows | cue sheet; rule summaries | C3 (NSF 2 banking days, unauthorised 60 days, re-present ≤ 2) |
| Business days and holidays for due dates | billing treatments | Ch. 4 (effective date = next business day) |
| Three-way reconciliation | cue sheet | M7; C6 |
| Event sourcing | some treatments | Options row C |
| Instant rails (since 2023) | then-and-now | Theory 3 note: removes some pending states, not returns or reconciliation |

## From the old version (fintech mock series, problem 2, 2026-11-20)

| Reused | New | Dropped |
|---|---|---|
| Clarifying answers, the two estimates, double-entry table and invariant, posting SQL, claim SQL, the three idempotency layers, the four deep dives (now C1, C2, C4, C6), the drill on returns (now C3), the runbook (now C7), signals (now C8), ownership | Theory chapter with safety/liveness; options matrix; V1→V2→V3 on a carried baseline; five numbered flows; C5 payoff with a debit in flight; push and second fix per challenge; symptom pairs; build cost; canon check; all figures redrawn | Coach-led narration frame; `f2-*` figures (redrawn on the baseline); "where this shows up" table (one line in the recap); then-and-now panel (one line in theory) |

## Budget

| Chapter | Minutes | Words | Slides |
|---|---|---|---|
| 0 Cold open | 3 | 380 | 5 |
| 1 Requirements and scope | 7 | 800 | 12 |
| 2 Estimates | 6 | 700 | 10 |
| 3 Theory | 11 | 1,350 | 18 |
| 4 API and entities | 6 | 750 | 11 |
| 5 High-level design | 11 | 1,300 | 20 |
| 6 Bridge | 1 | 100 | 2 |
| 7 Challenges (8 × ~4.3) | 34 | 4,150 | 75 |
| 8 Build cost (AUX) | 3 | 400 | 5 |
| 9 Recap | 3 | 380 | 6 |
| **Total** | **85** | **10,310** | **164** |

Key-line voice budget: under 5 % of words (≤ 470): definition, thesis twice, eight "if asked" lines of about 35 words.

**Actual (after the build, 2026-11-21): 75:13, 9,238 words (C 88.4 %, I 4.3 %, V 4.3 %, N 3.0 %), 162 slides.** Under the 85-minute plan: chapters 1, 2, 4, 5 and 8 ran shorter than budgeted. Within the 60–90 minute target; the key-line voice is under 5 %.
