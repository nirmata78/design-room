
\newpage

# Part II: The round, stage by stage

| Stage | Minutes (of 60) | What you produce |
|---|---|---|
| 1 Clarify | 0–5 | Six questions; four functional requirements; numbers; IN and OUT |
| 2 Estimates | 5–10 | Concurrency, the hold book in memory, the cost of a slow model, the latency budget |
| 3 API and data | 10–16 | The four message families and the clearing file; the auth store's tables; the keys |
| 4 High-level design | 16–28 | V1, V2, V3; four numbered flows |
| 5 Technology | inside 4 | One sentence per choice, against the alternative |
| 6 Deep dives | 28–50 | Two to four of the eight challenges, chosen by the interviewer |
| 7 Mid-round requirement | inside 6 | A late, duplicated clearing file; a second region; credit cards |
| 8–10 Failure, SLOs, cost, EM layer | 50–56 | Two minutes each, prioritised |
| 11 Close | 56–58 | Four sentences |

# Stage 1: Clarify requirements

Ask six questions before drawing. Each answer below is the simulator's, and each changes the design.

| Question | Answer | What it changes |
|---|---|---|
| Cards and traffic? | 8 million debit cards; 1,500 authorisations a second at the evening peak; 4,000 on the busiest shopping day | Size for 4,000; the fleet is small; the tail is the problem |
| The deadline? | The network times out after about 2 seconds and stands in; our own target is up to us | We pick p99 under 300 ms at our gateway, and design for when we miss it |
| Which messages? | Authorisation, incremental authorisation, reversal, advice, refund; clearing by daily file | A message state machine, not a single request type |
| Fraud? | Losses about 8 basis points of volume; chargebacks and customer reports 30 to 90 days later; analysts change rules several times a day without a release | A fraud score under a budget; rules as data; labels are late |
| Money? | The balance lives in our core ledger; clearing can differ from the authorisation; some never clear | Holds, not debits; clearing is the financial truth |
| Card data? | The processor holds full card numbers in its vault; we receive a token | Card-data scope stays at the processor; we never see a full number |

::: why
**Why ask about the deadline before anything else.** It is the one number set by someone else, and it
has a consequence nobody else's number has: missing it does not fail, it hands the decision to the
network. Asking it first also lets you correct the most common prep error out loud: the network's
timeout is seconds, and *your* target is a choice you make inside it.
:::

::: why
**Why ask about fraud labels.** "30 to 90 days" is the sentence that later makes shadow mode unable to
measure false positives (Challenge 6). A candidate who asks it in minute three and uses it in minute
forty is showing exactly the habit the round grades: a number that changes a decision.
:::

**Functional requirements.**

- **FR1 · Authorise.** Answer an authorisation or incremental authorisation, approve or decline, inside
  the deadline. An approval places a hold.
- **FR2 · Reverse and advise.** Reversals release holds. Stand-in advices are recorded and held, even
  past the balance.
- **FR3 · Clear.** Match each clearing record to its hold, post the real amount, release or adjust the
  hold; expire holds that never clear.
- **FR4 · Change rules.** Analysts publish fraud rules as versioned data, through backtest, shadow, a
  slice and enforcement, without a deploy.

**Non-functional requirements** (initial targets, not measurements):

| Requirement | Number | Why this number |
|---|---|---|
| Latency | p99 under 300 ms at our gateway, request in to answer out | leaves most of the ~2 s for the network and processor hops |
| Availability of the authorisation path | 99.99 % | each minute down is stand-in for every card |
| Effects | a network message never takes effect twice | retries and duplicates are normal |
| Our approvals | never take an account's available balance below zero | the advice path may; ours may not |
| Reproducibility | every decision reproducible for 7 years | disputes, regulators, model debugging |
| Clearing | posted by 09:00 on the day the file arrives | the customer's statement and the bank's books |
| Rule change | live within 5 minutes | an attack at 02:00 is minutes, not a release cycle |
| Degraded decisions | inside an hourly exposure cap signed by risk and finance | falling back is a money decision |

**Out of scope, said aloud:** issuing and manufacturing cards; the network and the processor themselves;
the disputes and chargeback workflow (we only consume its labels); statements; how models are trained;
credit and overdraft products; the 3-D Secure challenge flow, whose result arrives as an input field.

> The core is three things: a decision path that always answers inside the deadline, a hold ledger where
> each network message takes effect once, and a clearing path that turns promises into posted money and
> absorbs what we did not decide.

# Stage 2: Back-of-the-envelope

## How to do estimates in an interview

Three numbers deserve to be said out loud; the rest go in a table you mention. For each, say the
arithmetic, the label, and the decision it changes.

::: {.key title="Top-3 number: what is in flight, and where state must live"}
4,000 requests a second × 0.3 s at the target = **1,200 in flight** at worst; about 400 at a typical
100 ms. Each reads three things: the account and its holds, the card, the counters. 4,000 × 3 = **12,000
state reads a second**, each budgeted at a few milliseconds. **Meaning:** concurrency is small, but every
read is on the critical path. **Design change:** the state a decision needs lives next to the decision,
in a store built for single-digit-millisecond reads, never the core ledger.
**Say:** "Twelve thousand reads a second, each in a few milliseconds: that's a dedicated authorisation
store, not the ledger."
:::

::: {.key title="Top-3 number: the hold book fits in memory"}
Assume 12 million approvals a day, each open about three days until clearing: **36 million open holds**.
At about 200 bytes each that is **7 GB**. **Meaning:** the whole hold book, with balances, fits in the
memory of a small partitioned cluster. **Design change:** an in-memory-backed store, partitioned by
account, with a durable log; reads never touch disk on the hot path.
**Say:** "Thirty-six million holds is seven gigabytes. The whole book fits in memory, partitioned by account."
:::

::: {.key title="Top-3 number: what a slow model costs"}
If 2 % of decisions at the 4,000-a-second peak miss the model's slot: 4,000 × 60 × 2 % = **4,800
decisions a minute** decided without it. At an average \$60 and the base fraud rate of 8 basis points:
4,800 × \$60 × 0.08 % about **\$230 a minute** of expected loss. **Meaning:** small, at the base rate; but
fraud concentrates exactly where the model is blind, so the real number is several times higher.
**Design change:** falling back to rules is a priced decision with an hourly cap and an owner, not an
engineering default.
**Say:** "About two hundred and thirty dollars a minute at the base rate, more in practice. That's a
finance conversation, so it's a table with a cap."
:::

## The full table

| Number | Arithmetic | Label | Decision it drives |
|---|---|---|---|
| Peak rate | 1,500/s evening; 4,000/s busiest day | given | Size for 4,000 with headroom |
| Daily messages | assume 20 M a day about 230/s average; 4,000 ÷ 230 about 17 at the busiest peak, 1,500 ÷ 230 about 6.5 on a normal evening; 20 M ÷ 8 M about 2.5 a card a day | illustrative | Daily volume sizes logs and the clearing file, not servers |
| Concurrency | 4,000 × 0.3 s = 1,200; × 0.1 s = 400 | derived | Small fleet; the tail is the problem |
| State reads | 4,000 × 3 = 12,000/s | derived | A dedicated authorisation store next to the decision |
| Open holds | 12 M a day × 3 days = 36 M × 200 B about 7 GB | illustrative | In memory, partitioned by account |
| Per account | a busy card: a few a minute | derived | Serialising per account is free (C2) |
| Fleet card account | 2,000 cards × 1 per 10 min = 3.3/s on one key | illustrative | Still fine; sub-limits only at hundreds a second |
| Slow model | 4,800/min × \$60 × 0.08 % about \$230/min | illustrative | Fail policy with a cap |
| Outage | 20 min × 60 × 300/s = 360,000 stand-in decisions | illustrative | Advices arrive in a burst; post them all, once |
| Clearing file | 10 M records × 500 B about 5 GB a day | illustrative | Minutes of batch; matching is the hard part |
| Duplicates in a bad file | 3 % × 10 M = 300,000 | illustrative | Record-level idempotency (C7) |
| Decision log | 20 M × 2 KB about 40 GB a day; × 365 about 15 TB a year | illustrative | Object storage by day; seven-year retention |
| Latency budget | 5 + 5 + 3 + 10 + 60 + 10 + 5 = 98 ms; spare 202 ms of 300 | initial target | The model is the only slow step, and it has a cut-off |

::: why
**Why the peak-to-average ratio matters here.** A payments system is sized for its worst evening, not
its average second, and card traffic is spiky: lunchtime, evening, the busiest shopping day of the year.
The ratio also tells you the fleet will idle most of the day, which is why the cost lines that matter
(Stage 9) are fees and fraud, not servers.
:::

![The latency budget at the cut-off](diagrams/video-budget.pdf){width=100%}

**The budget, step by step.** Parse the network message and check its reference: 5 ms. Read the account,
holds and card: 5 ms. Read and increment the burst counters: 3 ms. Rules, in process: 10 ms, in
parallel with the model. The model: up to 60 ms, then the decision proceeds without it. Reserve the hold:
10 ms. Respond: 5 ms. **98 ms at the cut-off; about 200 ms spare.** The spare is not waste: it is the room
for a garbage-collection pause, a partition failover and a slow network hop, all at once, before the
network's own clock is in danger.

# Stage 3: API and data

## The messages

The network speaks ISO 8583, a message standard with numbered fields; the processor delivers it to us
over a dedicated link. Our gateway maps it to our own messages, so nothing behind the gateway knows the
wire format.

| Message | Serves | Reads / writes | Notes |
|---|---|---|---|
| `Authorise {networkRef, token, amount, currency, mcc, merchant, entryMode, threeDS, ts}` → `{approve \| decline, reasonCode, authCode}` | FR1 | reads Card, Account, Counters; writes Hold, Message, Decision | The answer must leave inside the budget |
| `IncrementalAuth {networkRef, originalRef, deltaAmount}` | FR1 | writes Hold | The same hold, larger |
| `Reversal {networkRef, originalRef, amount}` → ack | FR2 | writes Hold, Message | May arrive before its original |
| `Advice {networkRef, decidedBy, decision, amount}` → ack | FR2 | writes Hold, Message | Always acknowledged, always recorded |
| `ClearingFile {fileId, records[]}` | FR3 | reads Hold; writes Posting, Hold, ClearingRecord | Each record has its own ID; files repeat |
| `POST /rulesets {rules[], parent}` · `POST /rulesets/{v}/promote {mode, slice}` | FR4 | writes RuleSet | Internal; reviewed by a second analyst |

::: why
**Why `mcc` and `entryMode` are on the request.** The merchant category code says what kind of
merchant it is (restaurant, fuel, hotel, electronics); it sets the hold's lifetime and is the strongest
single fraud feature. The entry mode says whether the card was present (chip, contactless) or not
(online, phone). Card-not-present fraud is most of fraud, so almost every rule branches on it.
:::

::: why
**Why an advice is acknowledged even when we disagree.** It is not a question. It is the network telling
us what it already did, under limits we set. Refusing it does not undo the purchase; it only makes our
books disagree with the network's, which clearing will expose on Thursday.
:::

**The reason codes matter.** A decline carries a reason (insufficient funds, suspected fraud, card
blocked, do not honour). The terminal and the cardholder's app show something different for each, and
"suspected fraud" triggers a text asking the customer whether it was them, which is the fastest
false-positive signal there is (Challenge 6).

## The data model

![Conceptual model: accounts, cards, holds, messages, decisions, clearing](diagrams/video-erd-chen.pdf){width=95%}

An **account** has many **cards** (a joint account, a replacement card, a fleet of business cards). An
account has many **holds**. A hold is created by a **message** and changed by later messages with the
same reference family: the authorisation, its incrementals, its reversals. Each message is recorded as
a **decision**, a weak entity that only exists as the record of its message, carrying the features, the
rule-set version and the model version. A hold is **settled** by clearing records: usually one, several
for a split shipment, none for a hold that expires.

![Physical tables in the authorisation store](diagrams/video-erd-physical.pdf){width=100%}

| Table | Key | Columns | Note |
|---|---|---|---|
| `account` | `account_id`, the partition key | posted_balance, holds_total, version, state | `state` includes over-limit |
| `hold` | `(account_id, hold_id)`; `network_ref` unique | amount, mcc, expires_at, state | same partition as its account |
| `message` | `network_ref` | account_id, type, result, at | idempotency; kept past the retry window |
| `card` | `token` | account_id, status, limits | tokens only |
| `clearing_record` | `record_id` | file_id, network_ref, amount, hold_id | the financial truth |
| `ruleset` | `version` | parent, rules, mode, slice, owner | read by every decision service |
| counters | `card:minute` in an in-memory store | count | expire after 11 minutes |

**The hot keys and their writers.** The account row is written by the decision service (holds), the
clearing matcher (releases) and the ledger's posted-balance events. All three write through the same
conditional-write path with the version column, so none of them can overwrite another's change. The
counter keys are written only by the decision service. The rule-set table is written by the rule
service and read, through a push, by every decision service.

**Stores and "can we lose it?"**

| Store | Lose it? | Because |
|---|---|---|
| Auth store (balances, holds, messages) | **No** | holds are money; messages are idempotency |
| Feature store (counters) | Yes, ten minutes of it | rebuilt from the event log; a row of the fail table covers the gap |
| Event log | No, until consumed and archived | it carries the outbox to the ledger, alerts and archive |
| Decision archive | No | seven-year reproducibility |
| Rule sets | No | every decision names one |
| Core ledger | No | it is the bank's books |

# Stage 4: High-level design

Draw one baseline and evolve it. Boxes never move; each version adds boxes and reroutes arrows.

## Version 1: the simplest thing that works

![V1: one decision service on the core ledger](diagrams/video-base-v1.pdf){width=100%}

A gateway and one decision service. To authorise, it reads the balance from the core ledger and inserts
a hold row there, in one transaction. Rules are `if` statements in its code. A nightly clearing job reads
the network's file, posts the amounts and releases the holds.

> V1 works, and for a small issuer at a hundred authorisations a second it might be enough. The objection:
> the core ledger's tail latency and its nightly batch window now sit on the authorisation path; every rule
> change is a deploy; there is no fraud score; and nothing answers a retried or out-of-order message.

## Version 2: split the decision from the ledger

![V2: a dedicated authorisation store, rules as data, a model under a cut-off](diagrams/video-base-v2.pdf){width=100%}

The decision service becomes stateless, and the state it needs moves to an **authorisation store**:
balances, holds and the message table, partitioned by account, with one atomic reserve. **Rules** move
into the decision service's process, pushed as versioned data from a **rule service** that analysts
use. A **model scorer** answers under a 60 ms cut-off. Every decision is written to an **outbox** in the
same transaction as the hold and published to an **event log**. A **clearing matcher** loads the
network's daily file, posts to the core ledger and releases holds in the authorisation store; the
ledger's posted-balance changes (salary in, a direct debit out) flow back to the authorisation store as
events.

> The objection V2 answers: the authorisation path must not depend on the ledger's tail, and a rule must
> change without a deploy. The objection it leaves: where do features come from, what happens when
> something is late, what about stand-in advices, and how do two copies of the balance stay in agreement?

## Version 3: protect the deadline and close the loops

![V3: features, consumers, and the loops closed](diagrams/video-base-v3.pdf){width=100%}

A **feature store** holds burst counters that the decision service reads and increments inline, and
pattern features that a **stream aggregator** computes from the event log. The decision service carries
the **fail-policy table** and exposure counters. Advices take the same path as authorisations and are
always recorded. The rule service gains **backtest** (on the decision archive) and **shadow** modes.
**Alerts, cases and the archive** consume the event log. And a daily job **reconciles** the
authorisation store against the ledger.

| Version | Adds | Answers | Leaves |
|---|---|---|---|
| V1 | Gateway, one service, holds in the ledger, rules in code, a nightly clearing job | — | the ledger on the hot path; deploys for rules; no score; no idempotency |
| V2 | Auth store, atomic reserve, rules as data, model under a cut-off, outbox and event log, clearing matcher | the ledger off the hot path; rules without deploy | features; lateness; advices; two balances |
| V3 | Feature store and aggregator, fail table, advices, lifecycle tooling, consumers, reconciliation | every step budgeted with a written fallback; nothing we did not decide is lost | the details: Challenges 1 to 8 |

## The numbered flows, one per functional requirement

![FR1, authorise: eight numbered steps](diagrams/video-flow-fr1.pdf){width=100%}

**FR1 · Authorise.** (1) The network sends the request through the processor. (2) The gateway maps it
and passes it to a decision service. (3) The decision service increments this card's current-minute
counter and reads the previous nine minutes in one round trip. (4) It sends the request to the model
scorer with a 60 ms cut-off, while the rules run in its own process. (5) If the decision is approve, it
reserves the hold in the account's partition: check available, insert the hold, record the message, in
one conditional write. (6) The decision, with its inputs, features and versions, goes to the outbox in
the same write and to the event log. (7, 8) The answer goes back through the gateway to the network.

![The authorise sequence](diagrams/video-seq-authorise.pdf){width=100%}

![FR2, reverse and advise](diagrams/video-flow-fr2.pdf){width=100%}

**FR2 · Reverse and advise.** (1) A reversal or an advice arrives from the network. (2) The gateway passes
it on. (3) The decision service applies it by network reference in the authorisation store: a reversal
releases all or part of a hold (or is stored as a tombstone if its original has not arrived); an advice
is recorded as a hold even if it takes the account past zero. (4) The event goes to the log. (5) The
acknowledgement goes back.

![FR3, clear](diagrams/video-flow-fr3.pdf){width=100%}

**FR3 · Clear.** Before step 1 the matcher loads the day's file and skips record IDs it has already seen.
(1) In the authorisation store, in one write, it moves the amount from the hold to the posted balance:
posted goes down by \$72 and the \$72 hold is released, so available does not move at all. (2) It posts the
same amount to the core ledger, keyed by the clearing record's ID. (3) The ledger's other posted-balance
changes (a salary in, a direct debit out) flow back to the authorisation store; the clearing postings it
already applied are recognised by record ID and skipped. Records with no reference fall back to a fuzzy
match; unmatched records still post and go to a review queue; holds past their lifetime are released once
the day's file has arrived.

::: warn
**The ordering trap.** If the matcher released the hold first and waited for the ledger's posted event to
lower the balance, available would jump up by \$72 for a moment, and a purchase in that moment could
spend money that is already gone. Moving the amount from hold to posted in one write in the
authorisation store keeps available unchanged at every instant.
:::

![The clearing sequence](diagrams/video-seq-clearing.pdf){width=100%}

![FR4, change rules](diagrams/video-flow-fr4.pdf){width=100%}

**FR4 · Change rules.** (1) An analyst writes rule version 15 in the rule service, which backtests it on
the decision archive. (2) The rule service pushes a new rule-set version to every decision service, in
shadow. (3) Every decision records the rule-set version and what shadow rules would have done, to the
outbox. (4) The event log feeds the alarms on decline rate by merchant type. Then a slice, then
enforcement; rollback is re-pointing to the previous version.

## The C4 views

![C4 context](diagrams/video-c4-context.pdf){width=95%}

**Context.** The cardholder pays a merchant, whose acquirer sends the purchase through the card network
and the processor to us. We send the cardholder alerts. Fraud operations write rules and work cases. We
send postings to the core banking ledger. Nothing else is on the authorisation path.

![C4 containers](diagrams/video-c4-containers.pdf){width=100%}

**Containers.** The gateway, the decision service, the authorisation store and the feature store, the
model scorer and the rule service, the event log with its consumers, and the clearing matcher. The
authorisation path is three boxes in a row; everything else is above it (what it reads) or below it (what
happens after the answer). That layout is the thesis, drawn.

# Stage 5: Why these choices

## A dedicated authorisation store, partitioned by account

**Why here.** The decision reads the account, its holds and its messages, and must reserve atomically,
in a few milliseconds, 12,000 times a second, without inheriting the core ledger's batch windows. **What
to explain.** Partition by `account_id`, so every write a decision makes lands in one partition and one
transaction; keep the working set in memory with a replicated, durable log; a version column on the
account for conditional writes. **Alternatives.** Holds in the core ledger (correct, but its tail and
maintenance sit on the authorisation path); a cache in front of the ledger (a cache cannot reserve: two
readers of the same cached balance both approve). **Verdict:** a dedicated store, reconciled daily with
the ledger, which keeps the truth for posted money.

## Rules in process, pushed as versioned data

**Why here.** Rules are cheap to evaluate and must change without a deploy. Calling a remote rules
service would add a network hop and a failure mode to every decision. **What to explain.** A sandboxed
expression language with a time and memory limit per evaluation; the rule set compiled once per version
and swapped atomically; the version on every decision. **Alternatives.** Rules as code (a deploy per
change); a remote rules engine (a hop and a dependency). **Verdict:** in process, as data.

## A model scorer with a hard cut-off

**Why here.** The model is the only step that can be slow, and its slowness must never become ours.
**What to explain.** The decision service sends the request asynchronously and waits at most 60 ms; a
late score is logged and ignored; the fail-policy table decides without it. **Alternatives.** Embed the
model in the decision service (no hop, but model releases become decision-service releases, and a heavy
model competes for the same CPU); wait for it (stand-in). **Verdict:** a separate scorer behind a cut-off,
or embedded when the model is small, with the same cut-off around it.

## An in-memory feature store for counters

**Why here.** Burst counters must be exact at decision time and cost about a millisecond. **What to
explain.** One key per card per minute; increment the current bucket and read the previous nine in one
pipelined round trip; keys expire on their own. **Alternatives.** Counters from a stream processor (seconds
late: Challenge 5); a SQL count over recent transactions (milliseconds turn into tens). **Verdict:** inline
counters, plus pattern features from the stream.

## An outbox and a partitioned event log

**Why here.** Every decision must reach the archive, alerts, case management and the aggregator, and none
of them may slow the answer. **What to explain.** The decision is written to an outbox row in the same
transaction as the hold; a relay publishes it to the log; consumers are idempotent by network reference.
**Alternatives.** Publish directly from the decision service (a crash between the hold and the publish
loses the event, or publishes an event for a hold that rolled back). **Verdict:** outbox, then log.

## A batch clearing matcher

**Why here.** Clearing arrives as a file once a day; it is large but has hours. **What to explain.**
Record-level idempotency; matching by reference first, then fuzzy; one write in the authorisation store
that moves the amount from hold to posted, so available never jumps; then the ledger posting, keyed by
record ID, so a crash between the two is repaired by simply running the record again. **Alternatives.** Streaming clearing per record
(fine where the network offers it; the matching logic is the same). **Verdict:** batch, with the same
idempotent per-record step a stream would use.
