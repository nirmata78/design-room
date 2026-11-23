
# Stage 6: Deep dives

The interviewer picks two to four of these. Each follows the same shape as the video: the question, the
answer most people give, a case with numbers that breaks it, where it breaks, the fix, why it works, the
push on the fix, and the answer to give in the room. Each goes one level further here.

![Eight attack points on the same baseline](diagrams/video-map.pdf){width=100%}

| # | Challenge | Kind | Mechanism |
|---|---|---|---|
| 1 | The tip | correctness (crux) | holds with expiry; clearing as truth |
| 2 | Two swipes, one balance | correctness under concurrency | per-account atomic reserve |
| 3 | The same message twice, and in the wrong order | correctness | idempotency on the network reference |
| 4 | The model is slow tonight | overload (crux) | budget and fail-policy table with a cap |
| 5 | A burst, seconds apart | decision quality | two-speed features |
| 6 | A new attack at 2 a.m. | operations | rules as versioned data, staged |
| 7 | We were down for twenty minutes | failure recovery (crux) | the ledger absorbs stand-in; idempotent files |
| 8 | Declines doubled in ten minutes | observability | decision SLIs, symptom pairs, a runbook |

## 6.1 The tip (correctness)

> **Interviewer:** "A sixty-dollar restaurant authorisation clears three days later at seventy-two, with
> the tip. Walk me through the money."

**The naive answer.** "Approve and debit sixty. Clearing is a formality."

**The case.**

| Time | Event | Debit model |
|---|---|---|
| Mon 20:14 | authorise \$60 | debit \$60; balance \$500 → \$440 |
| Mon 20:16 | the waiter adds a \$12 tip | nothing, or a second debit of \$12 |
| Thu 06:00 | clearing \$72 | a second debit of \$72 (\$368), or ignored (restaurant \$12 short) |

The same shape appears everywhere amounts differ: a hotel pre-authorises \$300 and checks out at \$180; a
fuel pump authorises \$1 and clears at \$64; an online order ships in two parts and clears twice; a
purchase in another currency clears at a different rate.

![Where it breaks: the decision service writing money](diagrams/video-ch1-attack.pdf){width=100%}

**The fix: a hold, not a debit.** An approval inserts a hold of \$60 in the authorisation store. The
incremental authorisation raises the same hold to \$72. Available is posted minus active holds:
500 − 72 = \$428. On Thursday the clearing record matches the hold by network reference; in one write
the authorisation store lowers posted by \$72 and releases the hold, so available stays \$428 and posted
becomes \$428; the ledger posts \$72. Each hold gets a lifetime by merchant category: about seven days
for most, about thirty for hotels and car hire, where the final amount can come weeks later.

![The fix on the baseline](diagrams/video-ch1-fix.pdf){width=100%}

**Why it works.** Safety S1 is checked against available, which includes every promise already made.
Liveness L2 holds because every hold ends: by clearing, by reversal or by expiry.

> **Interviewer:** "The clearing record has no matching authorisation. Or it arrives after the hold
> expired."

**The second fix.** Match by reference first. If there is no reference, or it matches nothing, fall
back to a fuzzy match: same card, same merchant, amount within a tolerance (±20 % covers tips and most
currency swings), within a date window (seven days). If nothing matches, **the clearing record still
posts**: the network has already paid the merchant from our settlement account, so the file is the
financial truth, and the record goes to a review queue. A clearing that arrives after its hold expired
posts too, and may take the account below zero: that is the modelled over-limit state of Challenge 7.

::: warn
**"One authorisation equals one clearing record"** is the trap. Split shipments clear several times
against one authorisation; some authorisations never clear; some clearing has no authorisation at all
(offline transactions on a plane, below-floor-limit purchases). A matcher that assumes one-to-one either
double-releases or leaves holds open forever.
:::

::: why
**Why expiry waits for the day's file.** A hold that expires at 05:00 when the day's clearing file arrives
at 06:00 would release \$72 of available for an hour; the clearing then posts against nothing and takes
the account below what the customer saw. Gating expiry on the arrival of the day's file closes that hour.
:::

**If asked, I'd say:** *"Approval is a hold, not a debit. Available is posted minus active holds, and
clearing moves the real amount from hold to posted, matched by the network's reference. Holds that never
clear expire, and late clearing still posts."*

## 6.2 Two swipes, one balance (correctness under concurrency)

> **Interviewer:** "Two authorisations for one account arrive two milliseconds apart. The balance covers
> one of them. What happens?"

**The naive answer.** "Read the available balance, check it, insert the hold."

**The case.**

| Time | Request A: fuel \$80 | Request B: online \$60 |
|---|---|---|
| 12:00:00.000 | reads available \$100 | |
| 12:00:00.002 | | reads available \$100 |
| 12:00:00.004 | 80 <= 100: inserts hold \$80 | |
| 12:00:00.006 | | 60 <= 100: inserts hold \$60 |
| result | **available −\$40, both approved by us** | |

Joint accounts, a cardholder with a phone wallet and a physical card, and an online subscription that
renews while the customer pays at a till all produce this race. It is rare per account and common across
eight million.

![Where it breaks: read, then write](diagrams/video-ch2-attack.pdf){width=100%}

**The fix: one conditional write per account.** The reserve is a single operation in the partition that
owns the account: *if* holds total plus the amount is within posted, *and* the account's version is the
one I read, *then* insert the hold, record the message, add to holds total and bump the version.
Otherwise nothing is written, and the decision service re-reads and decides again.

```python
def reserve(store, acct_id, ref, amount, expires_at):
    while True:
        a = store.get("account", acct_id)                  # posted, holds_total, version
        if a.holds_total + amount > a.posted:
            return "decline: insufficient funds"
        ok = store.transact(acct_id, [                     # one partition, one transaction
            cond("account", acct_id, version=a.version),
            put("hold", (acct_id, new_id()), ref=ref, amount=amount, expires_at=expires_at),
            put("message", ref, type="auth", result="approve"),
            upd("account", acct_id, holds_total=a.holds_total + amount, version=a.version + 1)])
        if ok:
            return "approve"                               # else: someone else won; read again
```

![The reserve race, resolved](diagrams/video-seq-ch2-reserve.pdf){width=100%}

**Why it works.** S1 is decided by the one partition that owns the account, so there is exactly one
place where "is there enough?" can be answered. The conflict is cheap because per-account traffic is a
few requests a minute: a retry costs one more round trip, rarely.

> **Interviewer:** "A business account has 2,000 fleet cards on one balance, and on the busiest day they
> all buy fuel at 7 a.m."

**The second fix.** First the arithmetic: 2,000 cards × one authorisation in ten minutes is 3.3 a
second on one key. One partition handles that easily, with a conflict now and then. If it grows to
hundreds a second (a very large fleet, a marketplace with virtual cards), carve **sub-limits per card**
from the account: the account reserves budget to each card in blocks, refilled asynchronously, and most
authorisations touch only the card's slice. This is the escrow pattern, the same idea as counter ranges
in other designs.

![Sub-limits for a shared business account](diagrams/video-escrow.pdf){width=100%}

**The honest limit.** A card's slice can run dry while the account still has money. Refill early (at
half-used), size slices by each card's recent spend, and when a slice is empty, fall back to the
account-level reserve rather than declining.

::: why
**Why not a distributed lock.** A lock taken before the read and released after the write gives the
same safety, at the cost of a lock service on the hot path, a lease to expire when a decision service
dies holding it, and a second round trip. The conditional write is the lock and the write in one
operation, in the store that already owns the data.
:::

**If asked, I'd say:** *"Check-and-reserve is one conditional write in the partition that owns the
account, so two swipes can't both spend the same money. Per-account traffic is tiny, so that costs
nothing; a shared business account gets sub-limits per card."*

## 6.3 The same message twice, and in the wrong order (idempotency)

> **Interviewer:** "The network retries an authorisation we already approved. And a reversal arrives
> before the authorisation it reverses. What happens?"

**The naive answer.** "Process messages as they arrive; a retry is a new request."

**The case.**

| Time | Event | Naive result |
|---|---|---|
| 18:30:00.000 | authorise R-7731 \$45; approved; hold placed | |
| 18:30:00.090 | our answer is lost on the link | |
| 18:30:01.900 | the network retries R-7731 | a second hold: available down \$90 |
| 19:02:10.120 | reversal of R-8840 arrives (the merchant cancelled at once) | "nothing to reverse": dropped |
| 19:02:10.180 | authorise R-8840 \$45 arrives | approved: a hold for a cancelled purchase, for seven days |

Networks retry, processors resend after a failover, and the paths an authorisation and its reversal take
are not guaranteed to deliver in order. These are normal conditions, not edge cases.

![Where it breaks: every arrival treated as new](diagrams/video-ch3-attack.pdf){width=100%}

**The fix: idempotency on the network reference, written with the hold.** The message table is keyed by
the network's reference. Before acting, the decision service looks the reference up: if it is there, it
returns the stored answer. A reversal whose original has not arrived is stored as a **tombstone**; when
the original arrives, it is answered as the network expects (the network already knows it was reversed)
and no hold is placed. The message record is written **in the same transaction as the hold** (the
reserve of Challenge 2), so no crash can leave a hold without its message record or the reverse.

![Reversal before authorisation](diagrams/video-seq-reversal.pdf){width=100%}

**Why it works.** S2: the effect is keyed by what the network calls the message, not by when it arrives.
Retries return the same answer; order stops mattering.

::: why
**Why the same transaction, and why it must be the same partition.** If the message record lived in a
separate idempotency store, a crash after the hold and before the record would let the retry place a
second hold; a crash after the record and before the hold would return "approved" for a purchase with no
hold. Putting the message in the account's partition lets one local transaction cover both. The
reference arrives with the account already resolved from the token, so the partition is known before the
write.
:::

> **Interviewer:** "The partition fails over mid-write. Or the message table is purged and a retry
> arrives a day later."

**The second fix.** The transaction commits on a quorum of replicas in the zone before the answer
leaves, so a failover finds both writes or neither. Message records are kept for longer than the
network's retry and reversal windows, which are days, not minutes; they are small (about 100 bytes) and
compress well: 20 million a day × 100 B × 30 days about 60 GB. Past that window, clearing (Challenge 1) is
the backstop: a hold that should not exist expires, and a clearing that should exist posts.

**If asked, I'd say:** *"Every message is keyed by the network's reference, and the record of it is
written in the same atomic step as the hold. A retry gets the stored answer, and a reversal that arrives
first waits as a tombstone for its original."*

## 6.4 The model is slow tonight (overload; the crux)

> **Interviewer:** "Your fraud model is at 1.8 seconds p99 tonight. What does the authorisation path do?"

**The naive answers.** "Wait for it: fraud matters more than latency." Or: "Fail open."

**The case.** At 20:00 a model release doubles its feature fetches and its p99 goes to 1.8 seconds. If
we wait: by 20:01 about 30 % of our answers pass two seconds, and the network stands in for about 450 a
second (30 % of 1,500) with limits we set months ago and no fraud score at all. If we fail open: every
decision is unscored, 1,500 × 60 = 90,000 a minute, and a fraud ring that probes with small purchases
notices within minutes.

![Where it breaks: the model scorer](diagrams/video-ch4-attack.pdf){width=100%}

**The fix: a budget per step and a fail-policy table.** Rules always run, in process, in about 10 ms.
The model gets a 60 ms cut-off; at 60 ms the decision proceeds without it. What "without it" means is a
table, agreed in advance:

| Situation | Low amount, low-risk merchant | High amount or risky merchant type |
|---|---|---|
| Model late | rules-only decision | rules only, stricter limits |
| Counters missing | rules with conservative card-not-present limits | decline card-not-present; step up |
| Rules engine fails | approve within stand-in-like limits | decline, or step up the customer |
| Authorisation store unavailable | (the network stands in) | (the network stands in) |
| We miss the deadline | network stand-in | network stand-in |

Every cell has an **exposure cap per hour**: the most we accept losing while degraded. The decision
service counts degraded approvals and their amounts against the cap, live.

![The cut-off, then the table](diagrams/video-seq-ch4-cutoff.pdf){width=100%}

**Why it works.** L1: the answer leaves inside 300 ms whatever the model does, because nothing waits past
its slice. The quality loss is bounded by the cap, priced by the estimate in Stage 2, and owned.

> **Interviewer:** "It lasts all evening and the cap runs out. And who decided those numbers?"

**The second fix.** When a cell's cap is used up, that cell tightens: first a step-up (ask the
cardholder to confirm in the app), then lower limits, then decline. The model is rolled back by
re-pointing its version, which is the first runbook step. The ownership: **risk** sets the limits in each
cell from loss data and reviews them monthly; **finance** signs the cap; **engineering** makes each cell
a setting, counts every degraded decision and pages at 50 % of the cap. The point at the manager bar is
that this conversation happens before the incident, not during it.

::: warn
**"Fail open under \$100"** is the usual prep line. It is a start, not an answer: fraud is not uniform
across merchants or entry modes, a fraud ring adapts to a known threshold within hours, and nobody has
said how much fail-open costs or who signed it. The table with caps and owners is the answer.
:::

**If asked, I'd say:** *"The model gets a fixed slice of the budget and the decision never waits past
it. When it's late, a table owned by risk and finance decides by amount and merchant risk, under an
hourly exposure cap. We answer in time and we know what that costs."*

## 6.5 A burst, seconds apart (features)

> **Interviewer:** "Your rule is more than three swipes in ten minutes on one card. Where does that number
> come from, in time?"

**The naive answer.** "From the stream processor, into a key-value store."

**The case.**

| Time | Event | Counter from the stream (5–8 s behind) |
|---|---|---|
| 03:12:01 | card-not-present \$240 on token T-55 | reads 0: approve |
| 03:12:04 | \$240 | reads 1: approve |
| 03:12:06 | \$240 | reads 1: approve |
| 03:12:09 | \$240 | reads 2: approve |
| 03:12:15 | | the counter finally reads 4: \$960 already gone |

A burst of fraud on one stolen card is seconds apart, because it is a script. A stream processor's
counters are seconds behind, because that is what streams are.

![Where it breaks: features from the stream](diagrams/video-ch5-attack.pdf){width=100%}

**The fix: two-speed features.** Burst counters are **updated inline**: per card, one-minute buckets;
increment the current bucket and read the previous nine in one pipelined round trip, about a
millisecond. Pattern features that can be seconds late come from the stream: distinct merchants for this
card today, a merchant's decline rate in the last hour, a device seen on other cards in thirty days.

![Inline counters and stream aggregates](diagrams/video-features.pdf){width=100%}

```python
def swipes_last_10_min(store, card_token: str, now_s: int) -> int:
    """Count this swipe and return the swipes in the last 10 minutes, including it."""
    minute = now_s // 60
    key = f"v:{card_token}:{minute}"
    pipe = store.pipeline(transaction=True)
    pipe.incr(key)                              # this swipe
    pipe.expire(key, 11 * 60)                   # buckets clean themselves up
    for m in range(minute - 9, minute):
        pipe.get(f"v:{card_token}:{m}")         # the nine minutes before
    res = pipe.execute()
    return res[0] + sum(int(x or 0) for x in res[2:])
```

**Why it works.** The features whose value is in being *now* are exact at decision time. And every
feature value is **logged with the decision**, so the model is trained on exactly what it saw (safety S3),
not on values recomputed later from a different pipeline, which is how training and serving drift apart.

::: why
**Why a declined swipe still counts.** The counter is incremented before the decision, so declined
attempts count too. A fraud script that keeps trying after a decline is the strongest burst signal
there is.
:::

> **Interviewer:** "The counter store is slow or down."

**The second fix.** It is a row in the fail table: counters missing, so rules apply conservative
card-not-present limits. The counter store is partitioned by card with a replica; losing a partition
loses at most ten minutes of buckets, which are rebuilt from the event log for the cards that transact
next.

**If asked, I'd say:** *"Burst features are counted inline, read and incremented in one round trip,
because a stream lags behind a burst. Pattern features come from the stream. And every value is logged
with the decision, so training sees what the model saw."*

## 6.6 A new attack at 2 a.m. (operations: change safely)

> **Interviewer:** "A new attack appears at two in the morning. How fast can an analyst block it, and what
> stops them from blocking everyone?"

**The naive answers.** "Add an `if` and hotfix the decision service." Or: "Shadow-test it to measure the
false positives."

**The case.** At 02:05 fraud operations see a pattern: a \$1 test charge, then \$400 at electronics
merchants, on cards from one breach. A hotfix takes fifty minutes through review, build and deploy. The
alternative, an analyst pushing `amount > 300 && mcc == electronics → decline` live at 02:20, declines
9 % of all electronics purchases, almost all of them good customers.

![Where it breaks: the rule path](diagrams/video-ch6-attack.pdf){width=100%}

**The fix: rules as versioned data, staged.** A rule is an expression in a small sandboxed language (no
loops, no I/O, a time limit), with an owner and an expiry. It goes through four stages:

![A rule's lifecycle](diagrams/video-rule-life.pdf){width=100%}

1. **Backtest** on ninety days of the decision archive with known labels: how much of the ring's fraud
   it catches, how many good purchases it declines.
2. **Shadow** on live traffic: it runs and logs what it would have done, without enforcing; it shows the
   would-decline rate and the overlap with existing rules.
3. **Slice**: enforce on 5 % of traffic, with an alarm on the decline rate by merchant type.
4. **Enforce** everywhere, with a kill switch and the expiry.

```yaml
id: test-then-electronics
version: 15
condition: >
  txn.entry_mode == "card_not_present"
  && txn.mcc in ["5732", "5734"]
  && txn.amount > 300
  && features.small_charges_24h >= 1
action: decline
mode: shadow            # shadow | slice | enforce
slice: 0.05
expires: 2026-12-05
owner: fraud-ops/night
```

Every decision records the rule-set version it ran. Rollback is re-pointing every decision service to
the previous version: seconds, no deploy.

![The rollout as a sequence](diagrams/video-seq-ch6-rollout.pdf){width=100%}

**Why it works.** L3: minutes from idea to enforcement, not a release cycle. S3: the version is on every
decision, so any decision can be explained and any version undone. The staged rollout bounds the blast
radius of a mistake to a slice and an alarm.

> **Interviewer:** "Shadow says the rule would decline 4,000 transactions a day. How many were fraud?"

**The second fix, and the honest limit.** Shadow cannot say. It shows *how many* it would decline today,
not *which* were fraud: the labels, chargebacks and customer reports, arrive in 30 to 90 days. So the
evidence comes from elsewhere: the **backtest** on labelled history; **fast proxies**, such as the share
of customers who reply "it was me" to a decline text, or who pass a step-up; the **slice** with its
decline-rate alarm; and the **expiry**, so an emergency rule is reviewed with real labels rather than
living forever.

::: warn
**"Shadow mode measures false positives"** is in many prep sheets, and it is wrong for fraud. A false
positive is a decline of a good customer; you only learn a declined purchase was good when the customer
complains or confirms, and you never learn it for most of them. Say what you would measure instead.
:::

**If asked, I'd say:** *"Rules are versioned data, not code: backtest, shadow, a small slice with a
decline-rate alarm, then enforce, with a kill switch and the version on every decision. Shadow can't
measure false positives, because labels arrive months later."*

## 6.7 We were down for twenty minutes (failure recovery; the crux)

> **Interviewer:** "You were down for twenty minutes at two in the morning. The network approved 360,000
> transactions in stand-in. Walk me through the next morning."

**The naive answers.** "The network declined them while we were down." Or: "Replay them through our system
and decline the ones we wouldn't have approved."

**The case.** From 02:00 to 02:20 the network stands in with our pre-set limits, say up to \$150 a
transaction and \$400 a day a card: 20 × 60 × 300 = 360,000 approvals. At 02:21 we are back and the
advices arrive. Account A-19 had \$35 available; stand-in approved \$60 and \$80 on it, so available is now
−\$105. A check that refuses any write taking available below zero rejects those advices. The holds are
missing; Thursday's clearing posts anyway; the books disagree with the network's.

![Where it breaks: the invariant on the advice path](diagrams/video-ch7-attack.pdf){width=100%}

**The fix: the ledger absorbs decisions we did not make.** Advices are always acknowledged and recorded,
idempotently by network reference, as holds, even when they take the account past zero. Over-limit is a
**modelled account state**: new authorisations decline until the balance is back above zero, the
customer is told, and collections take over if it persists. Then, the next morning, the 360,000 are
replayed through our rules offline, not to reverse them, but to see which we would have declined and to
tune the stand-in limits with risk.

![Advices after an outage](diagrams/video-seq-ch7-advices.pdf){width=100%}

**Why it works.** S1 is about *our* approvals. The network's decisions are facts to record (S2), never
requests to refuse. A design whose invariant is "never below zero" is false by construction the first
time stand-in runs.

> **Interviewer:** "And the next day's clearing file arrives six hours late, with 3 % of its records
> duplicated."

**The second fix.** Ingest files idempotently: a checksum per file, so a resent file is recognised, and
a unique record ID per clearing record, so the 300,000 duplicates (3 % of 10 million) are no-ops. Hold
expiry waits for the day's file, so a late file does not find its holds already released. The 09:00
posting target slips, with a status note to finance and support, not silently. And every day, after
clearing, the authorisation store is **reconciled** with the ledger: for every account, posted balance
in the authorisation store must equal the ledger's; any difference is a break with an owner.

![Recording stand-in on the baseline](diagrams/video-ch7-fix.pdf){width=100%}

::: why
**Why stand-in limits are a risk decision too.** Higher limits mean fewer declined good customers during
an outage and more fraud let through; lower limits the reverse. The replay the morning after is the only
data that says whether last night's limits were right, which is why it happens every time.
:::

**If asked, I'd say:** *"Stand-in decisions are facts, not requests: we record every advice once, even
when it overdraws the account, and model over-limit as a state. Clearing files are ingested
idempotently, and hold expiry waits for the day's file."*

## 6.8 Declines doubled in ten minutes (observability)

> **Interviewer:** "The decline rate doubled in ten minutes. Your dashboards are green. How do you know
> what is wrong, and what is on the runbook?"

**The naive answer.** "CPU, error rate and latency."

**The case.**

| Time | Event |
|---|---|
| 19:40 | rule set v212 enforced: a typo widens a merchant-category list to include groceries |
| 19:41 | grocery approval rate 96 % → 71 %; no errors; p99 92 ms |
| 19:55 | the first complaints on social media |
| 20:10 | the first page, from support call volume |

Nothing failed. Every box was healthy. The product, deciding yes or no well, was broken for half an
hour.

![Where it breaks: monitoring that watches boxes](diagrams/video-ch8-attack.pdf){width=100%}

**The fix: SLIs on decisions, not machines.**

| SLI | Why it pages |
|---|---|
| Approval rate by merchant type and region, per minute, against the same hour last week | a sudden drop is almost always a rule or a release |
| Stand-in count | each one is a decision we did not make |
| Degraded decisions against the cap | prove the cap risk agreed to holds |
| "It was me" replies after declines | the fastest false-positive signal |
| p99 at the gateway, and model cut-offs | the deadline |
| Unmatched holds and clearings, per day | money and customers' available stuck |
| Synthetic test cards, every minute, every region | the end-to-end path works |

**Symptom pairs: two metrics, one cause.**

| When you see | Together with | It means |
|---|---|---|
| Declines up | a rule-set version change in the same minute | **a rule** (this case) |
| Declines up in one merchant | flat everywhere else | **that merchant's terminal or acquirer** |
| Stand-in count up | p99 at the gateway flat | **the link to the processor**, not us |
| Model cut-offs up | p99 flat | **the model**: the cut-off is doing its job |
| "It was me" up | declines up | **false positives**: roll back |
| Declines up | "it was me" flat, step-up pass low | **a real attack**: keep the rule, warn support |

**The runbook for "declines doubled in ten minutes".**

| Step | Why |
|---|---|
| 1 Check rule-set and release changes in the last hour | the most common cause, and the fastest to undo |
| 2 Re-point to the previous rule-set version | rollback in seconds, no deploy |
| 3 Compare by merchant type and region | a real attack, or one merchant's broken terminal? |
| 4 Then the model and its features | a stale feature looks like risk |
| 5 Tell support and the status page | complaints arrive before alerts otherwise |

![Probes and decision SLIs on the baseline](diagrams/video-ch8-fix.pdf){width=100%}

**Why it works.** The SLI measures what the cardholder experiences. A pair turns two metrics into one
cause. And the runbook starts with the most common cause, which is also the cheapest to undo.

> **Interviewer:** "It's real fraud this time: an attack, and the rule is right."

**The second fix.** The "it was me" rate and the step-up pass rate separate good customers from fraud
within minutes: if few declined customers say it was them and few pass a step-up, the rule is right.
Keep it, tell support what customers will hear, and let the expiry bring it back for review.

**If asked, I'd say:** *"I watch decisions, not boxes: approval rate by merchant type against last week,
stand-in count, degraded decisions against the cap. The runbook starts with what changed, because a rule
or a release is the usual cause and the fastest to undo."*

## 6.9 How the whole system degrades, in priority order

| What fails | What still works | What the customer sees |
|---|---|---|
| Model scorer | rules, counters, holds | slightly more fraud, inside the cap; maybe a step-up |
| Feature store | rules with conservative limits; holds | more step-ups for card-not-present |
| Rule service | the last pushed rule set keeps running | nothing; analysts cannot change rules |
| Event log | decisions continue; outbox rows accumulate | alerts delayed; nothing lost |
| Clearing matcher | authorisations continue; holds stay open | pending lasts longer |
| Core ledger | authorisations continue against the auth store | statements delayed |
| One auth-store partition | the other partitions | for that partition's accounts: stand-in |
| Gateway or decision service fleet | — | stand-in for everyone, within our limits |

The order is deliberate: everything above the last two lines degrades *inside* our answer; only the
authorisation store and the decision fleet hand the decision to the network.
