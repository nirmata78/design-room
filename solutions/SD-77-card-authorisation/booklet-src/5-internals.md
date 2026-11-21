
\newpage

# Part III: The internals

## Appendix A: Holds and their lifetimes, in plain words

A hold is a row that says "this much of this account is promised". It has an amount, a merchant
category, an expiry and a state. Available balance is computed, never stored on its own: posted balance
minus the sum of open holds, which the account row keeps as `holds_total` so the reserve does not have to
add up every hold.

**Incremental authorisations** raise an open hold; **partial reversals** lower it; **full reversals**
release it. **Expiry** is a sweep that runs after each day's clearing file has been processed: any hold
past its lifetime is released. Lifetimes come from the merchant category, because the network's rules
and the merchant's habits differ: restaurants and fuel clear in a day or two, hotels and car hire can
take weeks. A conservative issuer sets lifetimes a little longer than the network's maximum for that
category, because releasing too early is worse (the customer spends money that is about to leave) than
releasing too late (the customer sees less available for a few days).

**Multiple clearing records for one hold.** A split shipment clears twice. The first record posts its
amount and lowers the hold by the same amount, rather than releasing it; the last record, or expiry,
releases what remains.

## Appendix B: Idempotency on a network reference

A **network reference** is the identifier the network attaches to a transaction; related messages
(incremental, reversal, advice) carry the original's reference too. The message table stores one row per
message: its reference, type, the account and the result we gave.

The rule is simple: **look up before acting, and record in the same transaction as the effect.** A
retry finds the row and returns the stored result. A reversal that finds no original writes a tombstone
row; the original, when it arrives, finds the tombstone and is answered without a hold.

**Retention.** The row must live longer than the longest window in which the network can resend or
reverse: days. After that, clearing is the backstop.

**What not to key on.** Not the arrival time, not a hash of the amount and merchant (two genuine
purchases of the same coffee five minutes apart look identical), and not our own generated ID (the
network does not know it).

## Appendix C: Conditional writes and per-account serialisation

A **conditional write** says "apply these changes only if this condition still holds", typically a
version number. It is optimistic: nobody waits; whoever commits first wins; the loser re-reads and
decides again. It works when conflicts are rare, which per-account traffic guarantees.

**Why one partition.** A transaction inside one partition is local and fast. Partitioning by account
puts the account row, its holds and its messages in the same place, so the reserve never needs a
distributed transaction. The card token is resolved to its account before the write, from the card table,
which changes rarely and is cached.

**Hot accounts.** When one account's rate grows to hundreds a second, conflicts become frequent and
retries pile up. The fix is to split the account's budget into slices (Challenge 2): each slice is its own
key, and a background refill moves budget between them. This trades a little precision (a slice can run
dry while the account has money) for throughput.

## Appendix D: Budgets, cut-offs and fail policies

A **latency budget** gives each step a slice of the target. A **cut-off** enforces the slice for the one
step that can be slow: the call is made asynchronously, and the decision proceeds when the slice is used,
whether or not the answer has arrived. A late answer is logged (it is useful for training and for
diagnosing the slowness) and otherwise ignored.

A **fail policy** is the written answer to "what do we decide when a step is late or down?" It is a
table rather than code, because the people who own the answer (risk, finance) are not the people who
write code, and because it changes with loss data. Each cell has an **exposure cap**: a running sum of
degraded approvals' amounts per hour, which, when reached, moves the cell to a stricter row.

**Hedged requests** (sending the model call twice and taking the first answer) are a tempting way to cut
the tail. They are fine for a stateless scorer with spare capacity, and they double its load exactly when
it is struggling; a cut-off with a fail policy is the safer default.

## Appendix E: Inline counters and the stream

**Inline counters** are bucketed by time: one key per card per minute. Incrementing the current bucket
and reading the nine before it gives a sliding ten-minute count accurate to a minute, in one round trip.
Keys expire after eleven minutes, so memory stays bounded: about eight million cards, of which a small
share are active in any ten minutes, a few keys each.

**Stream aggregates** cover what does not fit the inline shape: distinct counts (merchants, devices),
long windows (thirty days), cross-card features (a device seen on many cards). A stream processor reads
the event log, maintains these in its own state, and writes them to the feature store, where the decision
reads them in the same call as the counters. They are seconds late by design.

**Logging what the model saw.** Every feature value used in a decision is written to the decision record.
Training reads those values, not values recomputed later, so a bug or a lag in the feature pipeline shows
up in training exactly as it did in serving.

## Appendix F: Rule languages and the rule lifecycle

A **sandboxed expression language** (the Common Expression Language is one widely used example) lets
analysts write conditions over the request and the features without being able to loop, call the
network or read files. Each evaluation has a time limit. Rules are compiled once per rule-set version and
swapped atomically in every decision service when a new version is pushed.

**Why staged.** A rule's two errors are asymmetric in time: missed fraud is visible within days (customer
reports), declined good customers almost never (most just use another card). The lifecycle (backtest,
shadow, slice, enforce) and the **expiry** exist because the second error is invisible.

## Appendix G: Clearing and matching

The network's clearing file lists every transaction the acquirers submitted, with the final amount, the
network reference where there is one, and a record ID. The matcher:

1. Loads the file; skips it if its checksum has been seen; skips any record ID already applied.
2. Matches each record to a hold: by reference; if none, by card, merchant, amount within a tolerance and
   a date window.
3. For a match: one write in the authorisation store moves the amount from hold to posted; then the
   ledger posting, keyed by record ID.
4. For no match: posts anyway, flags for review.
5. After the file: the expiry sweep for holds past their lifetime.
6. After posting: the daily reconciliation of the authorisation store against the ledger.

## Appendix H: Testing it

- **Property tests on the hold state machine:** any order of authorisation, incremental, reversal,
  advice and clearing for one reference ends in the same state, and holds total equals the sum of open
  holds.
- **A concurrency test** firing hundreds of reserves at one account: never below zero from our approvals.
- **A replay test**: a day of recorded messages, replayed twice with duplicates and reordering, produces
  the same balances.
- **Fault injection**: the model at 2 s, the feature store down, an auth-store failover mid-reserve,
  the clearing file resent; each must produce the table's behaviour and no double effect.
- **Synthetic test cards** in production, every minute, every region.

\newpage

# One-page cheat card

**Prompt:** a debit-card issuer; approve or decline the network's authorisation requests.

**Insight:** a promise inside someone else's deadline: a hold, not a debit; every message once, any
order; a budget with a written fallback; the ledger absorbs what we did not decide.

**Numbers:** 4,000/s peak → 1,200 in flight at 300 ms; 12,000 state reads/s; 36 M holds about 7 GB in memory;
slow model about \$230/min at the base rate; budget 98 ms of 300; outage 360,000 advices.

**Design:** network → gateway → decision service (rules in process, model under 60 ms cut-off, inline
counters) → authorisation store (one conditional write per account: hold + message) → outbox → event log
→ alerts, archive, aggregator. Clearing matcher: file → hold to posted in one write → ledger.

**Challenges:** 1 tip: holds, expiry, clearing as truth · 2 two swipes: per-account conditional write;
sub-limits for fleets · 3 duplicates and order: network reference, tombstones · 4 slow model: cut-off,
fail table, caps, owners · 5 burst: inline counters, features logged · 6 2 a.m. attack: rules as data,
staged; shadow cannot measure false positives · 7 stand-in: record advices even when they overdraw;
idempotent files; expiry waits · 8 declines doubled: decision SLIs, symptom pairs, runbook starts with
changes.

**Close:** "Answer in time with a hold, not a debit. Make every message count once, whatever the order.
Spend the budget on what matters and write down what happens when something is late. And record what the
network decided for us, even when it hurts."
