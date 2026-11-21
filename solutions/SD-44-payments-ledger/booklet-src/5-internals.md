
\newpage

# Part III: The internals

## Appendix A: Double-entry bookkeeping, in plain words

Every movement of money takes it *from* somewhere and puts it *somewhere*. Double entry writes both sides. Each account has a
normal side: assets (what we are owed, cash) increase with a debit; liabilities (what we owe merchants) and revenue increase
with a credit. A journal transaction is valid only if its debits equal its credits, per currency. That single rule makes three
things true at once: no money is created or destroyed by our code; every balance can be recomputed from the entries; and an
error shows up as an imbalance somewhere, rather than as a silently wrong number.

**Why a balance column fails.** A balance updated in place is a number with no history. When it is wrong, nothing tells you
why. When two transactions update it at once, one waits for the other's lock. A derived balance has neither problem: it is
the sum of entries that never change, and a projection can be rebuilt from them at any time.

**Integer minor units.** 10.50 is stored as 1050 with a currency whose minor-unit exponent is 2. Some currencies have 0 or 3
minor digits, so the exponent comes from the currency, never from the code. Rounding happens once, at a stated point (for
example, when a percentage fee is computed), with a stated rule, and the rounding difference is posted to an account rather
than lost.

**Closed periods.** Accounting closes a month and reports it. An adjustment that belongs to a closed month is posted in the
current month with a reference to the original. The closed month still adds up, and the correction is visible as a correction.

## Appendix B: Idempotency keys

An idempotency key names an *intent*, chosen by the client, so that every retry of that intent is recognisable. The server's
duties:

1. **Insert, do not check.** The key is inserted with a unique constraint in the same transaction as the effect. The database
   resolves concurrent retries; the application never does.
2. **Store the result.** The final response is stored on the key's row, so a retry returns it without re-executing anything.
3. **Bind the key to the request.** A hash of the canonical request is stored; a different request under the same key is
   rejected (422), because it is a client bug that would otherwise be hidden or double-charged.
4. **Report in-flight state.** A retry that arrives while the first is still running gets 409, not a second execution.
5. **Publish the retention.** Keys expire after a stated window; a retry after it is a new intent. This is part of the API
   contract, and a one-way door.

**Downstream idempotency** is the same idea one hop further: our call to the processor carries our own reference, so the
processor can de-duplicate our retries and answer inquiries about them. The reference is per *attempt*: the same while the
outcome is unknown, new only after a definite failure.

## Appendix C: The transactional outbox

The problem: a database commit and a message publish are two writes to two systems, and no shared transaction covers both. The
outbox puts the message *in the database*, in the same transaction as the change. A relay then moves committed outbox rows to
the message system:

- **Polling relay:** `SELECT ... FROM outbox WHERE id > :last ORDER BY id LIMIT 500`, publish, record `:last`, delete or mark
  sent. Simple; adds a little latency; watch for gaps when transactions commit out of id order (read only rows older than a
  small safety margin, or use a commit-ordered sequence).
- **Change-data-capture relay:** read the database's own commit log and publish outbox inserts in commit order. Lower latency;
  more moving parts.

Either way delivery is **at least once**: a relay that crashes after publishing and before recording progress publishes again.
Consumers de-duplicate by event ID, and merchants are told so in the webhook documentation.

## Appendix D: Processor inquiry and reversal

A processor typically offers some of: an idempotency key or merchant reference on requests; a status lookup by that reference;
a reversal (void) of an authorisation by reference; and a daily settlement file. The adapter for each processor records which
it supports and what its *safe window* is: how long after a request a "not found" can be trusted to mean it never arrived. The
inquiry job:

1. selects UNKNOWN payments in age order;
2. asks the processor about each attempt's reference, within the processor's rate limit;
3. applies the answer through the same state machine (conditional update from UNKNOWN);
4. reverses approvals that are no longer wanted;
5. leaves anything still unknown for the settlement file, and reports it by age.

When a processor supports none of this, the settlement file is the only arbiter, and UNKNOWNs last a day. That is a selection
criterion for processors.

## Appendix E: Reconciliation

**Inputs:** the processor's settlement file (stored raw, unchanged, with a checksum); the ledger's **expectations** for the
same period (every capture, refund and fee we believe the processor will settle, by reference); and, for the third leg, the
bank statement of cash received.

**Matching:** by reference first; then by amount and fee; with a tolerance only where a documented rounding rule allows one.
Output three sets: matched (post settlement entries, move payments to `SETTLED`), timing (expected tomorrow; auto-close when it
matches), and breaks.

**Breaks:** each has a type (missing on their side, missing on ours, amount, fee, duplicate), an owner, an age and a resolution
(an adjusting transaction with a reason, a claim against the processor, or a write-off with approval). Breaks by age is a
dashboard with a target. A sudden spike is classified by type and processor before anyone works individual lines.

## Appendix F: Sub-accounts for hot accounts

Split account A into A~1~ ... A~16~. Each posting picks one (round-robin, or by a hash of the payment ID). Balance(A) = Σ
balance(A~i~). Writes no longer contend on one row. A check that needs the current balance either sums the sub-accounts inside
one transaction (16 reads) or goes through one writer per merchant that serialises the rare operation. The number of
sub-accounts is the peak rate divided by one row's capacity, with headroom: 5,000 ÷ 670 about 7.5, so 16.

\newpage

# One-page cheat card

**Insight.** Exactly-once does not exist across the boundary: at-least-once delivery, one effect per intent, a state for not
knowing, reconciliation, on an immutable double-entry journal.

**Numbers.** 10,000 payments/s -> 40,000 entries/s. 2.9 × 10^8^ payments/day. 580 TB over 7 years. Hot merchant 5,000/s against
about 670/s per row lock. Budget: ours about 90 ms, processor at most 1.5 s, 410 ms spare. 10 UNKNOWNs/s at peak.

**API.** Idempotency key inserted first (409 in progress, 422 reused). Integer minor units plus currency. `pending` is an answer.
Signed webhooks with event IDs, plus `GET` as backstop.

**States.** CREATED -> AUTH_PENDING -> AUTHORIZED / DECLINED / **UNKNOWN** -> CAPTURED -> SETTLED; refunds and chargebacks as new
transactions. Legal edges only, by conditional update.

**Pay path.** Commit the attempt before the call -> call by reference with a 1.9 s deadline -> one transaction: state, entries,
outbox, key done.

**Eight challenges.** Timeout (UNKNOWN + inquiry) · three retries (insert first) · crash before event (outbox) · hot merchant
(append, sub-accounts) · refunds and chargebacks (new transactions, conditional limit) · 999,998 (line-by-line reconciliation) ·
double-posted entries (stop, reverse, recover) · observability (approval rate, UNKNOWN age, zero-sum page, symptom pairs).

**Traps.** Distributed transaction with the bank. Balance column. Timeout = failed. Floats. Check-then-insert. Publish after commit.
Editing history. Reconciling totals. Failing over an UNKNOWN.

**One-way doors.** The ledger schema and the idempotency contract.

*The technical content of this document is the model's reasoning; it has not been reviewed by a person. Numbers are illustrative
and are not any company's figures.*
