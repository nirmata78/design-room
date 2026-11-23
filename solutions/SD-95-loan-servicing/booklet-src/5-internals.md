
\newpage

# Part III: The internals

## Appendix A: Double-entry bookkeeping, in plain words

Every movement of money is recorded twice: where it came from and where it went. Each record is a *line* on an
*account*, and the lines of one transaction sum to zero when debits are written as positive and credits as
negative. Accounts come in kinds: assets (what we own or are owed, such as a loan's principal receivable, or cash
at the bank), liabilities (what we owe, such as merchant payable or customer payable), and income (such as the
merchant discount). The sign convention matters less than the invariant: if every transaction sums to zero, the
whole ledger sums to zero, and any account's balance is the sum of its lines.

Two consequences make the design. First, a mistake is never fixed by editing a line; it is fixed by a new
transaction that reverses it, so the history shows both the error and the correction. Second, any stored
balance can be checked against the lines at any moment, which is what the nightly invariant does. The stored
balance (the projection) exists only for speed; the lines are the truth.

In loan servicing, three accounts do most of the explaining. *Cash clearing* holds money in flight: a bank debit
moves into clearing when it is submitted and out of it when it settles, so the clearing balance is exactly what
the bank still owes us. *Customer payable* holds money we owe customers (overpayments), and must be paid out
within a deadline. *Merchant receivable* holds refunds merchants owe us.

## Appendix B: Idempotency keys at three layers

An idempotency key names one *decision*. Whoever receives the key a second time returns the first result instead
of acting again. In this design the key `coll:<loan>:<instalment>:<attempt>` is used three times:

1. **In the ledger**, as a unique column on the transaction. A duplicate posting fails at the first insert, and
   the stored result is returned.
2. **At the processor**, sent with the charge. A processor that honours keys returns the original result to a
   resend with the same key.
3. **In the schedule**, as a partial unique index on the intent table: one open intent per instalment, so two
   workers cannot create two collections for the same instalment.

The rule that holds them together: the same attempt always reuses its key; a new attempt number is created only
after a definite answer (a decline), never after a timeout. Keys are kept for at least as long as the processor
can return an answer for them, and in the ledger forever (they are part of the transaction).

## Appendix C: A database as a work queue

A table of due items with a status column, an index on `(due_date, shard, status)`, and a claim query using
`FOR UPDATE SKIP LOCKED` is a reliable queue at tens or hundreds of operations a second. `FOR UPDATE` locks the
selected rows until the transaction ends; `SKIP LOCKED` makes other workers skip those rows instead of waiting,
so many workers can drain one shard without colliding. If a worker dies before committing, its locks are
released and the rows are due again. If it dies after committing but before acting, a sweeper finds rows
claimed long ago with no follow-up and returns them. The outbox pattern completes it: the intent and an
"to send" row commit with the claim, and the dispatcher drains committed rows, so nothing is sent without a
record and nothing recorded is left unsent. The limits are known: polling adds a little latency, and very high
rates (tens of thousands a second) would justify a log-based queue. At 42 a second, none of that applies.

## Appendix D: Token buckets and the day plan

A token bucket allows a steady rate with a small burst: tokens are added at a fixed rate (say 90 a second) up to
a capacity, and each request takes one. The dispatcher keeps one bucket per rail, set below the contract to
leave room for queries and retries. When the processor signals throttling, the rate halves at once and recovers
slowly. The day plan is a schedule worked backwards from the hard deadline: the bank's cut-off minus the time to
fix and resend a rejected file gives the submission deadline; the file build and validation come before it; the
card window fits where the processor is least busy. The plan is data, re-run automatically after an outage.

## Appendix E: Bank-debit returns

A bank debit is an instruction to the customer's bank, sent in a file. It settles one to two business days later.
But it can be returned after settlement: for insufficient funds or a closed account within two banking days, and
as unauthorised (the customer says they did not agree) for up to sixty calendar days. Each return carries a
reason code and the trace number of the original entry. Under the network's rules, a debit returned for
insufficient funds may be presented again at most twice within 180 days; an unauthorised return may not be
presented again without a new authorisation. These rules are summarised from public rule documents as of
November 2026 and belong in the policy table, owned outside engineering, so a rule change is a new policy
version rather than a code change.

## Appendix F: Three-way reconciliation

Three records describe the same money: our ledger (what we expect), the processor's report (what they did), and
the bank statement (what arrived). Reconciliation stores each file raw, builds expectations from the ledger for
the period, and matches line by line: first by our reference (the key, or the trace number), then by amount
within a date window for anything left. Every unmatched line becomes a typed break: *timing* (expected to clear
on its own, and closed automatically when it does), *missing in ledger*, *missing at counterparty*, or *amount
differs*. Each break gets an owner and an age, and the ageing report is what makes a two-day month-end close
possible. Matching by totals is never acceptable: two errors of opposite sign cancel in a total, and one of them
may be a customer charged twice.

\newpage

# One-page cheat card

**Insight.** Settled is not final for a bank debit. Correctness over months, not throughput.

**Numbers.** 600,000 ÷ 14,400 s = about 42/s → the database is the queue. 120,000 card ÷ 90/s = about 22 min → budget per
rail. $90M on the 1st; 0.1 % = about $90k → correctness beats speed. 340 GB in seven years → one relational database.

**Design.** Ledger (immutable lines, projection in the same commit) · due items claimed with SKIP LOCKED, intent
and outbox in one commit · dispatcher with a token bucket per rail and a day plan from the cut-off · resolver for
UNKNOWN · file ingest for settlements and returns · policy as versioned data · three-way reconciliation.

**States.** SCHEDULED → SUBMITTED → PENDING → SETTLED → (RETURNED). SUBMITTED → UNKNOWN → query by the same key.

**Keys.** `coll:<loan>:<instalment>:<attempt>` in the ledger, at the processor, and one open intent per
instalment. Same attempt, same key.

**The eight challenges.** Timeout → UNKNOWN and the resolver. The 1st → plan back from the cut-off. Returns →
RETURNED, reversal, policy. Refund → transaction plus schedule version. Payoff → quote lists what's in flight,
PAID_PENDING. Month-end → match by reference, typed breaks. Processor down → pause, resolve, no fees, resume
slowly. Observability → funnel, file acknowledgement, invariants.

**Close.** Ledger and state machine · database as the queue, budget per rail · rare paths tested with real files ·
three-way reconciliation with owners.
