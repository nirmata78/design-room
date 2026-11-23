- [x] outline  - [x] design  - [x] diagrams  - [x] slides  - [x] script  - [x] video  - [x] publish

# SD-77 · Card authorisation and issuer processing — reference-solution video outline

Target level: staff (manager layer AUX) · Target length: 80 min (70–88) · Word budget: 9,900 (≈ 0.49 s a word with the
2026-11-17 pacing beats, measured on SD-94)

Generic content only: no issuer, processor, network or company names or figures. Card networks and their message standard
(ISO 8583) are named only as public standards. Amounts in dollars are illustrative. This is not legal, compliance or scheme-rule
advice. Recut of the 2026-11-20 fintech series problem 3 ("card authorisation with real-time fraud decisions"), now retired.

## Thesis and definition

- **Thesis** (key-line voice): *Card authorisation is a promise made inside someone else's deadline: answer in milliseconds with a
  hold, not a debit; make every network message take effect once in any order; spend the deadline on the signals that matter and
  have a written answer for when one is late; and let the ledger absorb the decisions we did not make.*
- **Definition to say aloud**: *An issuer's authorisation system answers the card network's request to approve or decline a purchase
  before the network's deadline, reserves the amount as a hold against the cardholder's available balance, and later settles the
  real amount from the network's clearing file.* Load-bearing clauses: **before the network's deadline** (miss it and the network
  decides for us: stand-in), **reserves as a hold** (no money moves at the till), **available balance** (balance minus holds),
  **later settles the real amount** (clearing can differ: tips, currency, partial shipments, or never arrive).
- **Hook**: It looks like "check the balance, say yes". It is three things at once: a hard real-time decision with a deadline we do
  not set; money that is only promised at the till and moves days later, often for a different amount; and a fraud decision that
  analysts change several times a day and whose mistakes we only learn about two months later.

## 0 · What this question grades

| Axis | Weak signal | Strong signal |
|---|---|---|
| Requirements | "Approve if the balance is enough", no deadline, no message types | The deadline and who sets it, the message types (incremental, reversal, advice), clearing, fraud-label delay asked first |
| Correctness | Debit the balance at authorisation; one auth = one clearing record | Holds as ledger entries; available = balance − holds; idempotency on the network reference, in any order; per-account serialisation |
| Trade-offs | "Call the fraud service" | A latency budget per step, a fail-policy table with an exposure cap and owners; rules as versioned data |
| Depth | Stops at "add a cache" | Stand-in advices that overdraw by construction; inline burst counters; shadow mode cannot measure false positives |
| Operations | CPU and error rate | Approval rate by merchant type, stand-in count, degraded decisions against the cap, "it was me" replies, a runbook for "declines doubled" |

## 1 · Requirements and scope

- **Clarifying questions and the interviewer's answers** (asked aloud, six):
  1. *Cards and traffic?* — 8 million debit cards; 1,500 authorisations a second at the evening peak; 4,000 on the busiest shopping day.
  2. *Deadline?* — The network times out after about 2 seconds and then stands in. "Your own target is up to you." → our p99 under
     300 ms at our gateway.
  3. *Messages?* — Authorisation, incremental authorisation, reversal, advice (stand-in notification), refund; clearing by daily file.
  4. *Fraud?* — Losses about 8 basis points of volume; chargebacks and customer reports arrive 30 to 90 days later. Analysts change
     rules several times a day; no code release for a rule.
  5. *Money?* — The account balance lives in our core ledger. Clearing amounts can differ from the authorisation; some authorisations
     never clear.
  6. *Card data?* — The processor in front of us holds full card numbers in its vault; we receive a token. "Keep it that way."
- **Functional requirements** (each gets a numbered flow):
  - FR1 · **Authorise**: answer an authorisation or incremental authorisation, approve or decline, inside the deadline; an approval
    places a hold.
  - FR2 · **Reverse and advise**: reversals release holds; stand-in advices are recorded and posted, even past the balance.
  - FR3 · **Clear**: match each clearing record to its hold, post the real amount, release or adjust the hold; expire holds that never clear.
  - FR4 · **Change rules**: analysts publish fraud rules as versioned data, through backtest, shadow, slice and enforce, without a deploy.
- **Non-functional, with numbers** (initial targets): p99 under 300 ms at our gateway, measured from the request arriving to the answer
  leaving; the authorisation path available 99.99 % (each minute down is stand-in for every card); a network message never takes effect
  twice; our own approvals never take an account below zero; every decision reproducible for 7 years (inputs, rule-set version, model
  version); clearing posted by 09:00 on the day the file arrives; a rule change live within 5 minutes; degraded decisions inside an
  exposure cap per hour signed by risk and finance.
- **IN / OUT**: IN: the decision, holds, reversals and advices, rules and model scoring, online features, the fail policy, clearing match
  and posting, decision events. OUT on purpose: issuing and manufacturing cards, the network and the processor themselves, disputes and
  chargeback workflow, statements, model training, credit or overdraft products, 3-D Secure challenge flow (its result arrives as an input).
- **"The core is 3 things"**: a *decision path* that always answers inside the deadline, a *hold ledger* where each network message takes
  effect once, and a *clearing path* that turns promises into posted money and absorbs what we did not decide.

## 2 · Estimates

| Number | Arithmetic | Label | Decision it drives |
|---|---|---|---|
| Peak rate | **1,500/s** evening; **4,000/s** busiest day | given | Size for 4,000 with headroom; per-account rate is tiny |
| Daily messages | assume 20 M a day (≈ 230/s average; peak ÷ average ≈ 6.5) ≈ 2.5 a card a day | illustrative | Daily volume sizes the logs and the clearing file, not the servers |
| Concurrency | 4,000/s × 0.3 s = **1,200** in flight at the target; × 0.1 s typical = 400 | derived | Small; the problem is the tail, not the fleet |
| State reads | 4,000/s × 3 reads (account + holds, card, counters) = **12,000 reads/s**, each budgeted at a few ms | derived | State next to the decision, in memory; never the core ledger on the hot path |
| Active holds | 12 M approvals a day × ~3 days open ≈ **36 M holds** × 200 B ≈ **7 GB** | illustrative | The whole hold book fits in memory on a partitioned store |
| Per account | a busy card: a few authorisations a minute | derived | Serialising per account costs nothing; the exception is a shared business account (C2) |
| Cost of a slow model | 4,000/s × 60 s × 2 % = **4,800 decisions/min** without the model; × $60 × 0.08 % ≈ **$230/min** at the base fraud rate | illustrative | Falling back to rules is a money question with a cap, not an engineering default |
| Outage | 20 min at 02:00 at 300/s = **360,000** stand-in decisions | illustrative | Advices arrive in a burst the next minutes; the ledger must post them all, idempotently |
| Clearing file | ~10 M records a day × ~500 B ≈ **5 GB** | illustrative | A batch job of minutes; the hard part is matching, not volume |
| Decision log | 20 M × ~2 KB (inputs, features, versions) ≈ **40 GB/day** ≈ 15 TB a year | illustrative | Object storage, compressed, partitioned by day; 7-year retention |
| Latency budget (300 ms p99) | parse + idempotency 5 · state read 5 · counters 3 · rules 10 · model ≤ 60 (cut-off) · reserve hold 10 · respond 5 ≈ **98 ms**, spare ≈ 200 | initial target | The model is the only step allowed to be slow, and it has a cut-off |

## 3 · Theory

1. **Is / is not.** Is: an online decision over a ledger of reservations, inside a deadline set by the network. Is not a **payment** (no
   money moves at authorisation; clearing and settlement move it), not a **debit** (a hold can be reversed, increased, cleared for a
   different amount, or expire), not **the fraud model** (the model is one input under a budget), not **the core ledger** (holds live next
   to the decision; posted money lives in the ledger; the two are reconciled).
2. **Safety**: S1 · our own approvals never take an account's available balance below zero. S2 · a network message never takes effect
   twice: one hold per authorisation, one posting per clearing record. S3 · every decision can be reproduced: its inputs, features and
   versions are recorded. **Liveness**: L1 · every authorisation gets an answer inside the deadline: ours, degraded if need be, never
   silence. L2 · every hold ends: cleared, reversed or expired. L3 · a rule change takes effect within minutes.
3. **Central tension**: **decision quality against the deadline.** Every extra signal (model, aggregates, external checks) buys
   accuracy and costs milliseconds; past the deadline the network decides for us with much less information. Picture: decision quality
   rising with time, the 300 ms target, the network's 2 s deadline, and stand-in beyond it.
4. **Mechanisms** (7). Property → how → failure ruled out → cost.

   | Mechanism | Protects | Rules out | Costs |
   |---|---|---|---|
   | **M1 Holds as ledger entries, with expiry** (available = balance − active holds) | S1, L2 | Debiting at the till; tip and currency differences; money stuck forever | A hold lifecycle; an expiry job; "pending" the customer must understand |
   | **M2 Idempotency on the network reference, order-independent** (a message table keyed by reference; early reversals kept) | S2 | A retried request placing two holds; a reversal before its authorisation lost | A message store kept past the network's retry window; tombstones |
   | **M3 Per-account atomic reserve** (one conditional write: check available, insert hold, record the message, in the partition that owns the account) | S1, S2 | Two concurrent swipes both seeing the same balance | An account-partitioned store; a shared business account becomes a hot key |
   | **M4 A latency budget with a fail-policy table** (rules in process, model with a cut-off, a table for when something is late) | L1 | A slow dependency making us miss the deadline | Degraded decisions with real exposure; a policy owned by risk and finance |
   | **M5 Two-speed features** (burst counters read-and-incremented inline; richer aggregates from the stream; features logged with the decision) | decision quality, S3 | A stream that lags behind a burst; training on values the model never saw | A counter store on the hot path; a second pipeline |
   | **M6 Rules as versioned data** (sandboxed expressions; backtest → shadow → slice → enforce; kill switch; the version recorded) | L3, S3 | A deploy to block an attack; one bad rule declining everyone | Tooling; labels 30–90 days late, so shadow cannot measure false positives |
   | **M7 The clearing file as financial truth** (match by reference, fall back to fuzzy; post the real amount; over-limit as a modelled state) | L2, books correct | Holds that never end; refusing to post advices or over-clearing | An unmatched queue both ways; overdraft handling and collections |

5. **Options matrix — where the decision and the money live** (rows = approaches; columns = deciding properties; last column = fails when).

   | Approach | Inside the deadline? | Correct when clearing differs? | Safe under concurrent swipes? | Rules without a deploy? | Fails when |
   |---|---|---|---|---|---|
   | A · Debit the core ledger at authorisation | depends on the ledger's tail | **no** | yes (row lock) | no | tips, reversals, partial shipments; the ledger's batch window |
   | B · Synchronous chain: gateway → ledger → fraud service → rules service | **no**: tails add up | yes, if holds | yes | yes | any one slow call means stand-in |
   | C · Holds in the core ledger, inline scoring with a budget | mostly | yes | yes | yes | the ledger's nightly posting and maintenance sit on the authorisation path |
   | **D · A dedicated authorisation store (balances, holds, messages) next to a stateless decision service; rules in process; model under a cut-off; fail table; events to the ledger** | **yes** | **yes** | **yes** (per-account reserve) | **yes** | the auth store and the ledger drift apart without reconciliation |
   | E · Let the processor decide with uploaded rules (outsourced authorisation) | yes | the processor's | the processor's | limited | our fraud needs outgrow its rule language; no own model |

   **Pick: D.** E is the honest build-cost answer for a first launch (V0 in chapter 8). A, B, C greyed with their failure. **Gives up:** a
   second copy of balances, which must be reconciled with the core ledger every day (C7).
6. **Failure catalogue**: F1 a tip or a currency difference at clearing → C1 · F2 two swipes on one balance → C2 · F3 a retried request; a
   reversal before its authorisation → C3 · F4 the model slow tonight → C4 · F5 a burst of fraud seconds apart → C5 · F6 a new attack at
   02:00, and a bad rule → C6 · F7 we are down; the network stands in; the clearing file is late and duplicated → C7 · F8 declines doubled
   and nobody knows why → C8 · F9 a shared business account with 2,000 cards: inside C2 · F10 card data in scope: dismissed, tokens only.

## 4 · API and entities

| API / message | Serves | Reads / writes | Wire-format notes |
|---|---|---|---|
| `Authorise {networkRef, token, amount, currency, mcc, merchant, entryMode, 3ds, ts}` → `{approve | decline, reasonCode, authCode}` | FR1 | reads Card, Account, Counters; writes Hold, Message, Decision | ISO 8583 authorisation request over the processor's link; our gateway maps it to this |
| `IncrementalAuth {networkRef, originalRef, deltaAmount}` | FR1 | writes Hold (increase) | the same hold, larger |
| `Reversal {networkRef, originalRef, amount}` → ack | FR2 | writes Hold (release), Message | may arrive before the original |
| `Advice {networkRef, decidedBy: stand-in, decision, amount}` → ack | FR2 | writes Hold or Posting, Message | "we decided for you": always acknowledged, always recorded |
| `ClearingFile(fileId, records[])` (batch) | FR3 | reads Hold; writes Posting, Hold, ClearingRecord | each record has its own ID; files may repeat |
| `POST /rulesets {rules[], parent}` · `POST /rulesets/{v}/promote {mode, slice}` | FR4 | writes RuleSet | internal; four-eyes review; kill switch |

**Conceptual**: **Account** 1—N **Card**; Account 1—N **Hold**; a **Message** (authorisation, incremental, reversal, advice) 1—1 or
N—1 a Hold; **Decision** (weak, of a Message) with **RuleSet version** and model version; **ClearingRecord** N—1 Hold (usually 1—1;
split shipments N—1; zero for a hold that never clears); **Posting** in the core ledger.
**Physical**: auth store partitioned by `account_id`: `account(account_id PK, posted_balance, holds_total, version, state)`,
`hold(account_id, hold_id PK, network_ref UNIQUE, amount, mcc, expires_at, state)`, `message(network_ref PK, type, result, at)`;
`card(token PK, account_id, status, limits)`; counters in an in-memory store keyed by `card:minute`; decision log in object storage by day;
`clearing_record(record_id PK, file_id, network_ref, amount, hold_id)`; `ruleset(version PK, parent, rules, mode, slice, owner)`.

## 5 · High-level design

| Version | Adds | Objection it answers | Objection it leaves |
|---|---|---|---|
| V1 | Gateway and one decision service reading the core ledger: authorise = read balance and insert a hold row in one transaction; rules in code; a nightly clearing job posts and releases | (none: the simplest thing that works) | The ledger's tail and nightly batch on the authorisation path; a rule needs a deploy; no fraud score; no answer for a retried or out-of-order message |
| V2 | **Split the decision from the ledger**: an authorisation store (balances, holds, messages, partitioned by account) with an atomic reserve; a stateless decision service with rules in process from a rule service; a model scorer under a cut-off; every decision through an outbox to an event log that posts to the ledger; a clearing matcher that releases holds and posts | "The authorisation path must not depend on the ledger's tail, and rules must change without a deploy" | Features from where? What when something is late? Stand-in advices? Two balances to keep in agreement |
| V3 | **Protect the deadline and close the loops**: an in-memory feature store with inline counters fed also by a stream aggregator; the fail-policy table with exposure counters; advice handling; rule lifecycle tooling (backtest on the decision archive, shadow); alerts, cases and the decision archive off the event log; daily auth-store ↔ ledger reconciliation | "Every step has a budget and a written fallback, and nothing we did not decide is lost" | The details, which are the challenges |

Baseline spine, left to right: **Card network / processor → Auth gateway → Decision service → Authorisation store → Core ledger**, with
**Analysts → Rule service → Model scorer → Feature store → Stream aggregator** above, and **Event log → Alerts, cases, archive → Clearing
matcher** along the bottom; probes as a ch8 tag.

Flows (numbered arrows):
- **FR1 Authorise:** 1 the network sends the request · 2 the gateway maps it and passes it on · 3 the decision service reads and increments the
  burst counters · 4 the model scores under a 60 ms cut-off while rules run in process · 5 approve: one atomic reserve in the account's
  partition (check available, insert hold, record the message) · 6 the decision goes to the outbox and the event log · 7–8 the answer goes back.
- **FR2 Reverse and advise:** 1 reversal or advice from the network · 2 gateway · 3 apply by network reference: release the hold, or record
  the stand-in decision as a hold even over the balance · 4 event to the log · 5 the ledger posts what must be posted · 6 acknowledge.
- **FR3 Clear:** 1 the matcher loads the day's file, skipping records already seen · 2 match each record to its hold by reference, falling back
  to card + merchant + amount window + date · 3 in the auth store, one write moves the amount from hold to posted (available does not
  move) · 4 post to the ledger keyed by record ID · 5 the ledger's other posted changes flow back, clearing ones skipped by record ID ·
  unmatched both ways go to a queue; holds past expiry are released, after the day's file has arrived.
- **FR4 Change rules:** 1 an analyst writes rule v15 · 2 the rule service backtests it on the decision archive · 3 shadow: pushed to every
  decision service, logged, not enforced · 4 the decisions carry the rule-set version to the log · 5 alarms on the decline rate · 6 slice, then
  enforce; rollback = re-point to v14.

C4 and sequence views that follow: context; containers; sequences for authorise, reversal-before-authorisation, clearing; rule rollout.

## 6 · Bridge and challenge map

*It works. Where does it break first?* The baseline with eight attack points. Correctness: C1, C2, C3. Overload: C4, C5. Operations and
trade-off: C6. Failure recovery: C7. Observability: C8. The crux (the money is a hold; the deadline is someone else's) gets C1 + C2 and C4 + C7.

## 7 · Challenges

### Challenge 1 · The tip  *(correctness; crux part 1)*

- Q: "A sixty-dollar restaurant authorisation clears three days later at seventy-two, with the tip. Walk me through the money."
- Naive answer: "Approve and debit sixty; the clearing is a formality."
- Case: Mon 20:14 auth $60, debit; balance $500 → $440. 20:16 the tip adjusts. Thu 06:00 clearing $72: a second debit, $368 — or the job
  ignores it and the restaurant is short $12. A hotel pre-authorises $300 and checks out at $180; a second fuel-pump pre-auth of $1 clears at $64.
- Break: the decision service writing to the ledger, dashed red.
- Fix: **a hold, not a debit** (M1). Approval inserts a hold of $60; incremental auth raises it to $72; available = posted − holds = 500 − 72 =
  $428. Thursday's clearing record matches the hold by network reference, posts $72, releases the hold: available stays $428, posted becomes
  $428. Hold lifetimes by merchant category (7 days general, 30 for hotels and car hire). Figure: the hold timeline.
- Why it works: S1 is checked against available balance; L2 because every hold ends by clearing, reversal or expiry.
- "What if the fix fails?": "The clearing record has no matching authorisation. Or it arrives after the hold expired."
- Second fix: match by reference first, then fuzzy (card + merchant + amount within a tolerance + date window); unmatched clearing still posts
  (the network has already paid the merchant: the file is the financial truth) and goes to a review queue; unmatched holds expire. A clearing
  after expiry posts and may overdraw: a modelled state (C7).
- If asked, I'd say: "Approval is a hold, not a debit. Available balance is posted balance minus active holds, and clearing posts the real
  amount and releases the hold, matched by the network's reference. Holds that never clear expire, and late clearing still posts."

### Challenge 2 · Two swipes, one balance  *(correctness under concurrency)*

- Q: "Two authorisations for one account arrive two milliseconds apart. The balance covers one of them. What happens?"
- Naive answer: "Read the available balance, check it, insert the hold."
- Case: available $100. 12:00:00.000 fuel $80 reads 100; .002 online $60 reads 100; .004 hold 80; .006 hold 60: available −$40, both approved by us.
- Break: the read-then-write between the decision service and the store, dashed red.
- Fix: **a per-account atomic reserve** (M3): one conditional write in the account's partition: `holds_total + amount ≤ posted` and `version`
  unchanged, insert the hold and the message record, bump the version; a conflict re-reads and decides again. Sequence and code (eight lines).
- Why it works: S1 is decided by the one partition that owns the account; per-account traffic is a few a minute, so the conflict is rare and cheap.
- "What if the fix fails?": "A business account has 2,000 fleet cards on one balance, and on the busiest day they all buy fuel at 7 a.m."
- Second fix: 2,000 cards × 1 auth per 10 min at 07:00 ≈ 3.3/s on one key: still fine for one partition. If it grows to hundreds a second,
  give each card a **sub-limit carved from the account** (escrow: the account reserves budget to cards in blocks, refilled asynchronously), so
  most auths touch only the card's slice. Honest limit: a slice can run dry while the account has money; refill early and decline rarely.
- If asked, I'd say: "Check-and-reserve is one conditional write in the partition that owns the account, so two swipes can't both spend the
  same money. Per-account traffic is tiny, so that costs nothing; a shared business account gets sub-limits carved per card."

### Challenge 3 · The same message twice, and in the wrong order  *(correctness: idempotency)*

- Q: "The network retries an authorisation we already approved. And a reversal arrives before the authorisation it reverses. What happens?"
- Naive answer: "Process messages as they arrive; a retry is a new request."
- Case: 18:30:00.000 auth R-7731 $45 approved, hold placed; the answer is lost on the link; 18:30:01.900 the network retries R-7731: a second
  hold, available down $90. Separately: 19:02:10.120 reversal of R-8840 arrives (the merchant cancelled); 19:02:10.180 R-8840 itself arrives
  and is approved: a hold for a purchase that was cancelled, for seven days.
- Break: the gateway and store, treating each arrival as new, dashed red.
- Fix: **idempotency on the network reference, in the same atomic write as the hold** (M2 + M3): the message table is keyed by reference; a
  retry returns the stored answer; a reversal with no original is stored as a tombstone, so when the original arrives it is answered as the
  network expects (approved and reversed, no hold). Sequence: reversal before authorisation.
- Why it works: S2: the effect is keyed by what the network calls the message, not by when it arrives; recording the message in the same
  write as the hold means no crash can separate them.
- "What if the fix fails?": "The partition fails over mid-write. Or the message table is purged and a retry arrives a day later."
- Second fix: the write is one transaction in one partition, replicated synchronously within the zone, so a failover either has both or
  neither; keep message records for longer than the network's retry and reversal windows (days, not minutes) and compress them; past
  that window, the clearing match (C1) is the backstop.
- If asked, I'd say: "Every message is keyed by the network's reference, and the record of it is written in the same atomic step as the
  hold. A retry gets the stored answer, and a reversal that arrives first waits as a tombstone for its original."

### Challenge 4 · The model is slow tonight  *(overload; crux part 2)*

- Q: "Your fraud model is at 1.8 seconds p99 tonight. What does the authorisation path do?"
- Naive answer: "Wait for it; fraud matters more than latency." Or: "Fail open."
- Case: 20:00 a model release doubles feature fetches; p99 1.8 s. Waiting: 20:01 our p99 passes 2 s on 30 % of traffic; the network stands in
  for 450 a second with limits we set months ago; fraud gets through stand-in. Failing open: 1,500 × 60 = 90,000 unscored decisions a minute, and a fraud ring that notices.
- Break: the model scorer, dashed red.
- Fix: **a budget per step and a fail-policy table** (M4): rules in process (10 ms) always run; the model gets a 60 ms cut-off and the decision
  proceeds without it; the table says what "without it" means, by amount × merchant risk × which component is late; every cell has an
  exposure cap per hour, counted live. Budget bar; the table.
- Why it works: L1: the answer leaves inside 300 ms whatever the model does; the quality loss is bounded, priced and owned.
- "What if the fix fails?": "It lasts all evening and the cap runs out. And who decided those numbers?"
- Second fix: when a cell's cap is used, that cell tightens (step-up, lower limits, then decline); risk sets the limits, finance signs the
  cap, engineering makes each cell a setting and pages before the cap; roll the model back by version. The conversation happens before the incident.
- If asked, I'd say: "The model gets a fixed slice of the budget and the decision never waits past it. When it's late, a table owned by risk
  and finance decides by amount and merchant risk, under an hourly exposure cap. We answer in time and we know what that costs."

### Challenge 5 · A burst, seconds apart  *(overload of the feature path; decision quality)*

- Q: "Your rule is more than three swipes in ten minutes on one card. Where does that number come from, in time?"
- Naive answer: "From the stream processor, into a key-value store."
- Case: 03:12:01, 03:12:04, 03:12:06, 03:12:09 four card-not-present auths of $240 on token T-55; the stream's counters lag 5–8 s behind,
  so each decision reads 0, 1, 1, 2: all four approved; $960 gone before the counter reads 4.
- Break: the stream aggregator feeding the feature store, dashed red: features seconds late.
- Fix: **two-speed features** (M5): burst counters updated inline: per-card one-minute buckets, increment this one and read the nine before in
  one pipelined round trip (~1 ms); pattern features (distinct merchants per day, merchant decline rate per hour) from the stream, seconds
  late is fine. Every feature value logged with the decision. Code: the counter.
- Why it works: an exact count at decision time for the features whose value is in being now; S3: training sees what the model saw.
- "What if the fix fails?": "The counter store is slow or down."
- Second fix: it is a row in the fail table (counters missing → rules with conservative card-not-present limits); counters are an
  in-memory store partitioned by card with a replica; losing it loses ten minutes of buckets, rebuilt from the event log for the next decision.
- If asked, I'd say: "Burst features are counted inline, read and incremented in one round trip, because a stream lags behind a burst.
  Pattern features come from the stream. And every value is logged with the decision, so training sees what the model saw."

### Challenge 6 · A new attack at 2 a.m.  *(operations: change safely)*

- Q: "A new attack appears at two in the morning. How fast can an analyst block it, and what stops them from blocking everyone?"
- Naive answer: "Add an if-statement and hotfix the decision service." Or: "Shadow-test it to measure the false positives."
- Case: 02:05 a pattern of $1 test charges then $400 at electronics merchants. A hotfix takes 50 min through review and deploy. Or an analyst
  pushes `amount > 300 && mcc == electronics → decline` live at 02:20: it declines 9 % of all electronics purchases, mostly good customers.
- Break: the rule path into the decision service, dashed red.
- Fix: **rules as versioned data** (M6): a sandboxed expression language with a time limit; backtest on 90 days of the decision archive with
  known labels; shadow on live traffic (would-decline rate, overlap with existing rules); a 5 % slice with a decline-rate alarm; enforce; a kill
  switch and an expiry; every decision records the rule-set version; rollback = re-point to the previous version, in seconds. Figure and YAML.
- Why it works: L3: minutes, not a deploy; S3: the version is on every decision; the staged rollout bounds the blast radius.
- "What if the fix fails?": "Shadow says the rule would decline 4,000 transactions a day. How many were fraud?"
- Second fix / limit: shadow cannot say: chargebacks arrive in 30–90 days. Use backtests on labelled history, fast proxies ("it was me" replies
  to a decline text; step-up pass rates), a small slice with an alarm, and a rule expiry so emergency rules do not live forever.
- If asked, I'd say: "Rules are versioned data, not code: backtest, shadow, a small slice with a decline-rate alarm, then enforce, with a kill
  switch and the version on every decision. Shadow can't measure false positives, because labels arrive months later."

### Challenge 7 · We were down for twenty minutes  *(failure recovery; crux part 2)*

- Q: "You were down for twenty minutes at two in the morning. The network approved 360,000 transactions in stand-in. Walk me through the next morning."
- Naive answer: "The network declined them while we were down." Or: "Replay them through our system and decline the ones we wouldn't approve."
- Case: 02:00–02:20 stand-in approves within our pre-set limits (say up to $150 per transaction, $400 a day per card). 02:21 360,000 advices
  arrive. Account A-19 had $35 available and two stand-in approvals of $60 and $80: available −$105. A "balance never below zero" check
  rejects the advices; the holds are missing; clearing on Thursday posts anyway; the books disagree.
- Break: the store's invariant check on the advice path, dashed red.
- Fix: **the ledger absorbs decisions we did not make** (M7 + M2): advices are always acknowledged and recorded idempotently by reference, as
  holds even past the balance; over-limit is a modelled account state (new authorisations decline until it is cleared, the customer is
  told, collections if it persists). Then replay the 360,000 through our rules offline to tune the stand-in limits with risk.
- Why it works: S1 is about *our* approvals; the network's decisions are facts to record (S2), never to refuse.
- "What if the fix fails?": "And the next day's clearing file arrives six hours late, with 3 % of its records duplicated."
- Second fix: ingest files idempotently (file checksum, record ID unique; 300,000 duplicates become no-ops); hold expiry waits for the day's
  file, so late clearing does not find its holds already released; the 09:00 posting target slips with a status note, not silently.
  Reconcile auth store against ledger daily (holds total + posted = ledger balance per account).
- If asked, I'd say: "Stand-in decisions are facts, not requests: we record every advice once, even when it overdraws the account, and
  model over-limit as a state. Clearing files are ingested idempotently, and hold expiry waits for the day's file."

### Challenge 8 · Declines doubled in ten minutes  *(observability)*

- Q: "The decline rate doubled in ten minutes. Your dashboards are green. How do you know what is wrong, and what is on the runbook?"
- Naive answer: "CPU, error rate and latency."
- Case: 19:40 rule-set v212 enforced (a typo widens a merchant list). 19:41 approval rate for grocery falls from 96 % to 71 %; no errors, p99 92 ms;
  19:55 the first complaints on social media; the first page at 20:10 from support volume.
- Break: the monitoring view, dashed red: it watches boxes, not decisions.
- Fix: **SLIs on decisions, not machines**: approval rate by merchant type and region every minute against the same hour last week; stand-in
  count; degraded decisions against the cap; "it was me" replies after declines; unmatched holds and clearings per day. **Symptom pairs**:
  declines up + one rule-set version change = a rule; declines up in one merchant + flat elsewhere = a merchant's terminal; stand-in up + p99
  flat = the link to the processor; model cut-offs up + p99 flat = the model. **Runbook**: changes first (rule set, release), re-point to the
  previous version, compare by merchant and region, then model and features.
- Why it works: the SLI is what the cardholder experiences; the pair turns two metrics into one cause; the most common cause is the cheapest to undo.
- "What if the fix fails?": "It's real fraud this time: an attack, and the rule is right."
- Second fix: the "it was me" rate and step-up pass rate separate good customers from fraud within minutes; if they stay low, keep the rule
  and tell support. Probes: synthetic test cards in every region authorise and reverse every minute end to end.
- If asked, I'd say: "I watch decisions, not boxes: approval rate by merchant type against last week, stand-in count, degraded decisions
  against the cap. The runbook starts with what changed, because a rule or a release is the usual cause and the fastest to undo."

## 8 · Build cost (AUX)

- **V0 (buy)**: outsourced authorisation at the processor with uploaded rules and stand-in limits: 3 engineers, 8 weeks; fine for a launch.
  **V1** (own decision service on the core ledger): 4 engineers, 3 months. **V2** (auth store, rules as data, model under cut-off, clearing
  matcher): a team of 6–8 for 2 quarters. **V3** (features, fail table, advices, lifecycle tooling, reconciliation): two teams, a further 2 quarters.
- **Buy against build**: the processor and its card vault are bought; the network's own risk score is an input; the model platform may be bought;
  the decision path, holds and clearing match are built, because they are the product.
- **Team seams**: authorisation platform (gateway, decision service, auth store, latency) · risk platform (rules engine, features, shadow
  tooling) · data science (models) · fraud operations (rule content, customer contact) · ledger and clearing (holds, posting, reconciliation).
  Contracts: the decision event schema; the rule-set format; the fail-policy table.
- **Cost, illustrative**: the fleet is small; the largest lines are the processor's per-transaction fees and fraud losses (8 bps of volume),
  then the decision archive (15 TB a year) and the model serving. A basis point of fraud is worth more than all the servers.
- **Top risks**: a fail policy nobody signed; the auth store and the ledger drifting; rules without expiry; card data creeping into scope.

## 9 · Recap

Final diagram: the V3 baseline. One sentence per path: *Authorise:* counters, rules and model in parallel under a budget, one atomic reserve, an
answer in time. *Reverse and advise:* by reference, in any order, and record what the network decided. *Clear:* the file is the truth: match,
post, release, expire. *Change rules:* data, versioned, staged, recorded on every decision.
**Common mistakes:** debiting at authorisation; one auth = one clearing; read-then-write on the balance; ignoring retries and out-of-order
reversals; "the network gives 100 ms"; waiting for the model; fail open as a slogan; velocity only from a stream; shadow mode to measure false
positives; refusing advices; no owner for the fail policy.
**Closing line (key-line voice):** "Answer in time with a hold, not a debit. Make every message count once, whatever the order. Spend the
budget on what matters and write down what happens when something is late. And record what the network decided for us, even when it hurts."

## Canon check

| Canonical point | Source | Covered at, or dismissed because |
|---|---|---|
| Authorisation vs clearing and settlement; holds | cue sheet; standard issuer documentation | M1; C1; FR3 |
| Available balance = balance − holds | cue sheet | Theory M1; C1 trace |
| Network deadline and stand-in (STIP), advices | cue sheet; issuer documentation | Ch. 1 Q2; tension; C7 |
| Idempotency on network identifiers; out-of-order reversals | cue sheet | M2; C3 |
| Per-cardholder serialisation | cue sheet | M3; C2 |
| Fraud scoring inside a budget; fail open or closed per risk class | cue sheet; old fintech problem 3 | M4; C4 |
| Velocity features: inline bursts, stream aggregates | cue sheet; old problem 3 | M5; C5 |
| Rules as versioned data; backtest → shadow → slice → enforce | cue sheet; old problem 3 | M6; C6 |
| Shadow mode cannot measure false positives | cue sheet; old problem 3 | C6 second push |
| Clearing matching with fuzzy fallback; unmatched both ways | cue sheet | C1 second fix; FR3 |
| Curveball: clearing file late and duplicated | cue sheet | C7 second push |
| Hold never cleared after 30 days | cue sheet probe | C1 (expiry by merchant category) |
| Runbook "declines doubled in ten minutes"; who owns the fail policy | cue sheet EM bar | C8; C4 second fix; ch. 8 |
| Card data (PCI) scope | general canon | Ch. 1 Q6: tokens only, dismissed aloud as a cut |
| 3-D Secure | cue sheet input list | Dismissed: its result arrives as an input field; the challenge flow is out of scope |
| What changed recently | — | Network risk scores routinely arrive with the request as one more feature; tokenised cards (wallets, network tokens) are the norm; sandboxed rule languages such as CEL are common |

## From the old version (retired fintech series, problem 3)

| Reused | New | Dropped |
|---|---|---|
| The five graded axes and the three "usual prep answer" corrections (100 ms, stream velocity, fail open); the concurrency and timeout-cost arithmetic; the fail-policy table and its owners; the counter code; the rule YAML and lifecycle; the runbook and signals; the two drills (stand-in morning, reversal before auth) as challenges 7 and 3; ideas of figures f3-path, f3-holds, f3-features, f3-rules, f3-budget (redrawn on the carried baseline) | Debit issuer per the cue sheet (available = posted − holds) instead of credit limit; theory chapter (six parts, seven mechanisms); options matrix with a pick; V1 → V2 → V3; four numbered flows; C2 per-account reserve, C3 idempotency and order, C7 with the late duplicated clearing file, C8 symptom pairs as full challenges; clearing match; build cost; canon check; target p99 300 ms per the cue sheet (old: 150 ms) | Coach-led framing (now candidate-led); "where this shows up" table (one line in the recap); f3-teams figure (ownership now in build cost); the credit-card framing |

## Budget

| Chapter | Minutes | Words | Slides |
|---|---|---|---|
| 0 Cold open | 2.7 | 330 | 5 |
| 1 Requirements and scope | 5.7 | 700 | 11 |
| 2 Estimates | 5.5 | 680 | 9 |
| 3 Theory | 10 | 1,230 | 16 |
| 4 API and entities | 4.9 | 600 | 7 |
| 5 High-level design | 9.6 | 1,180 | 17 |
| 6 Bridge | 0.9 | 110 | 2 |
| 7 Challenges (8 × ~4.5) | 36 | 4,400 | 80 |
| 8 Build cost (AUX) | 3.1 | 380 | 5 |
| 9 Recap | 3.1 | 380 | 6 |
| **Total** | **81** | **9,990** | **158** |

## 5.1 Components and technologies (retrofit, 2026-11-22)

<!-- stack:outline -->

| Container | Choice | How it is built | Rejected | Theory part |
|---|---|---|---|---|
| Auth store | PostgreSQL 16, partitioned by account, hot set in memory, synchronous standby | Accounts are partitioned by account ID, so the balance, the holds and the network message a decision touches live together | Holds in the core ledger; A cache in front of the ledger; An event log as the source of truth | 03, 07 |
| Rules in process | A sandboxed expression language in the decision service, a rule set per version | The rule service holds versions of the rule set | Rules as code; A remote rules engine | 08 |
| Model scorer | A separate gRPC service, a 60 millisecond cut-off, a fail table | The decision service sends the request asynchronously and waits at most sixty milliseconds | Embedding a large model in the decision service; Waiting for the model | 08 |
| Feature store | Redis Cluster, one key per card per minute, one pipelined round trip | One key per card per minute | Counters from a stream processor; A SQL count over recent transactions | 05 |
| Event log | Outbox row in the same transaction, Kafka partitioned by account | The decision is written to an outbox row in the same transaction as the hold | Publishing after the commit; Synchronous calls to each consumer | 06 |
| Auth gateway | Go service, mutual TLS to the processor, message mapping, deduplication | The gateway terminates mutual TLS from the processor, maps each message to our request and keys it by the network's reference | The processor's format through our services; Treating each message as new | 07 |
| Clearing matcher | Spark batch over clearing files, matching by network reference | The matcher reads the clearing file and matches each line to its hold by the network's reference | Debiting at authorisation; Matching on amount and time | 08 |

Fix-slide rejections: 1: Debiting the balance at authorisation; 2: Reading the balance, then writing it; 3: Treating every network message as new; 4: Waiting for the model; 5: Burst counters from a stream processor; 6: Rules as code, deployed; 7: Dropping advices received while we were down; 8: Dashboards of CPU and memory.

<!-- /stack:outline -->
