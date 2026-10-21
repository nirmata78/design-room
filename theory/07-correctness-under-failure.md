# 7 · Correctness under failure — retries, idempotency, sagas, reconciliation

Networks lose, delay, duplicate and reorder messages; processes crash between any two lines of code.
A correct distributed system is one that **produces the right outcome anyway**. The toolkit is small
and recurs in every money, booking, messaging and workflow question.

---

## The unknown outcome

The single most important failure case:

> You sent a request. It **timed out**. You do not know whether it happened.

There are three possibilities — it never arrived, it ran and the response was lost, or it is still
running — and **you cannot tell them apart** from the caller. Every correct design answers: *how do
we retry safely, and how do we find out what happened?*

{: .key }
> **A timeout is not a failure.** Treating it as one (and retrying blindly) double-charges; treating
> it as success loses money. The answer is an **idempotent retry** where possible, and otherwise a
> **pending state plus a status inquiry**, with reconciliation as the backstop.

## Retries done right

- **Timeouts on every remote call**, derived from the caller's own budget (a 200 ms endpoint cannot
  wait 30 s on a dependency).
- **Exponential backoff with jitter** — `sleep = random(0, base × 2^attempt)` — so retries from many
  clients don't synchronise into waves.
- **Retry budgets** (e.g. retries ≤ 10% of requests) so retries can't multiply load during an outage —
  the retry storm.
- **Retry only idempotent or idempotency-keyed operations.**
- **Circuit breakers** stop calling a failing dependency for a while and fail fast instead
  ([Reliability](08-reliability-and-operations.md)).

## Idempotency

An operation is **idempotent** if doing it twice has the same effect as once. Reads, `PUT` of a full
value and `DELETE` are naturally idempotent; "charge $10", "append a message" and "decrement stock"
are not — so we make them idempotent with a key.

### Idempotency keys

1. The **client generates a unique key** per logical operation (UUID) and sends it with every retry.
2. The server, **in the same transaction as the effect**, records `(key → request fingerprint, result)`.
3. A repeat with the same key returns the **stored result** without re-executing.
4. A repeat with the same key but a **different payload** is rejected (409/422) — never silently
   treated as the original.
5. Keys are retained for a defined window (e.g. 24 h–30 days); say what happens after it.

**Concurrent duplicates:** two retries arrive at the same time. A unique constraint on the key (or a
"processing" row inserted first) makes the second one wait or return "in progress" — not execute.

```sql
-- inside the transaction that performs the effect
INSERT INTO idempotency (key, request_hash, status) VALUES ($1, $2, 'processing');
-- unique violation → look up the existing row:
--   same hash + 'done'  → return stored result
--   same hash + 'processing' → 409 "in progress, retry later"
--   different hash → 422 "key reused with different request"
```

### Dedup by natural identity

When the producer can't supply a key, use a natural one: `(chain, tx_hash, output_index)` for a
deposit, `(network_ref)` for a card message, `(conversation_id, client_msg_id)` for a chat message.

## State machines

Model every long-lived entity (payment, order, booking, withdrawal) as an **explicit state machine**:
enumerated states, allowed transitions, and **conditional updates** that enforce them:

```sql
UPDATE payment SET state = 'CAPTURED', version = version + 1
WHERE id = $1 AND state = 'AUTHORIZED' AND version = $2;   -- 0 rows → someone else moved it
```

Illegal transitions fail loudly; concurrent updates resolve by optimistic concurrency (version check).
Persist every transition as an event for audit and replay.

## Multi-step operations: sagas, not two-phase commit

**Two-phase commit (2PC)** makes several participants commit atomically through a coordinator. It
**blocks** if the coordinator fails at the wrong moment, needs every participant to support it, and is
**unavailable across company boundaries** — your bank does not join your transaction.

A **saga** is a sequence of local transactions, each with a **compensating action** that semantically
undoes it:

| Step | Action | Compensation |
|---|---|---|
| 1 | reserve inventory | release inventory |
| 2 | authorise payment | void authorisation |
| 3 | create shipment | cancel shipment |

- **Orchestrated** (a coordinator drives the steps — clearer for complex flows, easy to observe) or
  **choreographed** (services react to each other's events — looser coupling, harder to follow).
- **Compensation can fail too**, so it must be durable and retried; some steps are irreversible
  (money sent, email delivered) and must come **last** — the *pivot* step.
- Sagas give **no isolation**: intermediate states are visible. Design for it (e.g. "pending" states,
  holds rather than debits).

{: .say }
> "I can't get a transaction across our database and the bank, so the payment is a saga: authorise,
> record, capture — each step durable and idempotent, each with a compensation, and anything we
> can't tell about gets parked in a pending state for the inquiry job."

## Concurrency control for contended resources

| Technique | How | When |
|---|---|---|
| **Pessimistic lock** | `SELECT … FOR UPDATE` / `SKIP LOCKED` | short critical sections, high contention on few rows |
| **Optimistic concurrency** | version column; retry on conflict | conflicts are rare |
| **Conditional write / compare-and-set** | `UPDATE … WHERE state = 'AVAILABLE'` | a single-row state transition (seat holds, idempotent status moves) |
| **Unique constraint** | the database rejects the duplicate | "at most one X per Y" invariants |
| **Single-writer partitioning** | route all writes for a key to one owner | sequencing (chat order, matching engines) |
| **Distributed lock with fencing** | lease + monotonic token checked by storage | coordinating across systems — use sparingly |

## Reconciliation — the permanent safety net

Even a perfect system disagrees with external parties: they have bugs, delays, fees, and their own
retries. **Reconciliation** compares your records with theirs (or derived state with its source of
truth) on a schedule, and turns every difference into an **owned, aged, explained exception**.

{: .key }
> Reconciliation is **not** a sign the system is buggy. It is a required component whenever a second
> party keeps its own record of the same events — banks, card networks, payment processors, partner
> feeds, even your own cache vs database.

---

## Traps

{: .warn }
> **"We'll use a distributed transaction across our DB and the payment provider."** Not available.
> Sagas, idempotency and reconciliation are the answer.

{: .warn }
> **Retrying everything three times** with no idempotency, jitter or budget — turns a blip into an
> outage and a double charge.

{: .warn }
> **Check-then-act** (`read balance; if enough, write new balance`) without a lock or conditional
> write — the classic race.
