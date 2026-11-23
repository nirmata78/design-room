---
title: "SD-24 · A Distributed Lock Service"
subtitle: "A reference solution for a system design round at the Staff bar: leases, consensus, fencing tokens, and the resource that has the last word"
author: "design-room reference solution · practise with the simulator first"
date: "12 November 2026"
documentclass: article
fontsize: 10pt
geometry: a4paper,top=0.7in,bottom=0.75in,left=0.75in,right=0.75in
colorlinks: true
linkcolor: gblueink
urlcolor: gblueink
toc: true
toc-depth: 2
numbersections: false
---

\newpage

# How to read this document

This is the **long answer key for question `SD-24`** in
[design-room](https://github.com/nirmata78/design-room), an open-source system design interview
simulator, and the written companion to its reference-solution video. It shows how a strong Staff
candidate (L6/L7) runs the round: what to say, what to draw, and **when**. A short stage-by-stage
version [lives in the repository](https://nirmata78.github.io/design-room/solutions/). This one adds the
**why** behind every line, so you can defend each choice when the interviewer asks *"why?"*,
*"what is that?"* or *"what happens when it breaks?"*.

**The document has three layers, and you will read them differently:**

1. **Part I, the system in pictures.** Read it first. It explains what a lock is, what a caller
   experiences, what happens to one acquisition millisecond by millisecond, and where the load lands.
   There is no interview script in it, only understanding.
2. **Part II, the round, stage by stage.** This is what you do in the room. Each stage has the words to
   say, what to draw, and boxes that explain every term. The seven **challenges** of the video are
   Stage 6, and each one goes further here than the video can.
3. **Part III, the internals.** How consensus, leases, clocks, conditional writes and linearizability
   testing actually work, at the depth a round reaches when you name a tool and the interviewer asks
   how it works.

**The coloured boxes:**

::: {.key title="Top-3 number"}
One of the back-of-the-envelope numbers worth computing out loud in the round. In a real interview you
have time for two or three calculations, not ten.
:::

::: why
Explains a term or a decision in plain words. This is for you, not for the interviewer.
:::

> Words you can say in the room, nearly verbatim.

::: warn
A trap: something weak candidates do, or a claim that breaks under a follow-up question.
:::

::: load
What this part of the system sees at peak, with numbers.
:::

**Practise in three passes.** (1) Read Part I and Part II once, end to end. (2) Close the document and
run the [simulator](https://github.com/nirmata78/design-room) cold:
`Read CLAUDE.md. Mock me: SD-24, Google, staff, full round.`
(3) Debrief against the Stage 12 self-check, then reread only the sections where you fell short.
**Do not memorise numbers.** Memorise *the order of the argument* and how to rebuild each number in
twenty seconds.

**About the numbers.** The scale figures in Stage 1 are the simulator's cue sheet. Everything derived
from them is back-of-the-envelope arithmetic, and any planning assumption (the peak factor, how many
attempts succeed, one group's write ceiling, a rebuild's quiet period) is labelled as one: *given*,
*illustrative*, *initial target* or *derived*. None of them is a measurement. They are not any
company's real figures, and this is not any company's actual design. Costs are in engineer-months, not
money, because a loaded salary depends on a market.

**The prompt as the interviewer reads it:**
*"Design a distributed lock service that other teams use to make sure only one process does a thing
at a time."*

::: {.key title="The one-sentence insight to land by minute 12"}
**A lock service says who *should* be working. Only the *resource* says who is *allowed* to write.**
The service grants a lease and a number that orders every grant. The resource remembers the highest
number it has accepted and rejects anything smaller. The lease keeps the system live. The token keeps
it safe.
:::

::: why
**Why is this the insight?** Most candidates draw a consensus group, a TTL and a key, and stop. That
design is perfectly correct at every step and still allows two writers: a holder pauses for fifteen
seconds, its lease expires, a second holder is granted, and the first one wakes up and writes. The
network was fine and the lock service did exactly what it promised. What is missing is a connection
between the lock service's idea of who holds the lock and the resource's idea of who may write. The
question tests whether you notice that gap, not whether you can draw the group.
:::

\newpage

# Part I: The system in pictures

## Vocabulary you need first

Every term below is defined here once, grouped by where it lives. Part II uses them without
re-explaining.

**Terms about the lock itself**

| Term | Meaning | Where it appears here |
|---|---|---|
| **Lock** | Permission for one party to act on a named thing, for a while | Every stage |
| **Lease** | A lock with an expiry: valid for a stated time, then the service may reassign it without asking the holder | Stage 3, challenge 1 and 3 |
| **Name** | The string a lock is on, such as `invoice:17`. Locks on different names are independent | The reason the service shards |
| **Holder** | The party that was granted the lock | Everywhere |
| **Waiter** | A party queued for a name that is held | Challenge 6 |
| **Efficiency lock** | A lock whose failure only wastes work (a job runs twice) | Stage 1, challenge 2 |
| **Correctness lock** | A lock whose failure corrupts data (two writers, a double charge) | Stage 1, challenge 2 |
| **Safety** | What must never happen: two parties both act as holder and both effects take hold | Theory, every challenge |
| **Liveness** | What must eventually happen: a free name is granted, a dead holder's name frees | Theory, every challenge |

**Terms about order and checking**

| Term | Meaning | Where it appears here |
|---|---|---|
| **Fencing token** | A number issued with each grant, larger than every earlier one for that name. The resource rejects any write with a token smaller than the highest it has accepted | Challenge 1 |
| **Log index** | The position of an entry in the replicated log. Strictly increasing, so it makes a free token | Stage 3 |
| **Epoch** | A counter, bumped on a rebuild or a slot move, that sits in the top bits of the token | Challenge 4 and 5 |
| **Conditional write** | A write that succeeds only if some stored value still matches: a version, a generation, a highest token | Challenge 1 and 2 |
| **Idempotency key** | A caller-chosen key that makes a repeated operation harmless: the second call does nothing new | Challenge 2 |

**Terms about the replicated store**

| Term | Meaning | Where it appears here |
|---|---|---|
| **Consensus** | A way for a group of machines to agree on an ordered log of entries despite failures | Stage 4, Part III |
| **Replica, leader, follower** | A copy of the state. One replica per term is the leader and takes all writes | Stage 4 |
| **Term** | A number that increases with each election. A node that sees a higher term obeys it | Challenge 4 |
| **Majority (quorum)** | More than half of the replicas: 3 of 5. An entry is committed once a majority has it | Challenge 4 |
| **Leader lease** | A short promise by the replicas not to elect another leader, so the current leader can answer reads from memory | Stage 6.4 |
| **Grace period** | After an election, the new leader treats every session as alive for one full lease | Challenge 4 |
| **Linearizable** | Behaves as if there were one copy and every operation took effect at one instant between its start and end | Stage 5 |
| **Deterministic state machine** | Applying the same entries in the same order always gives the same state, because nothing inside apply reads a clock or a random number | Stage 3 |

**Terms about clients and time**

| Term | Meaning | Where it appears here |
|---|---|---|
| **Session** | One client's connection to the service, kept alive by one heartbeat. Its locks hang off it | Stage 3, challenge 5 |
| **Heartbeat** | A small periodic message that says "this client is still alive" | Stage 4 |
| **Monotonic clock** | A clock that only measures elapsed time on one machine and never goes backwards | Challenge 3 |
| **Wall clock** | The time of day. It can jump either way, and two machines never quite agree | Challenge 3 |
| **LockLost** | The callback the client library fires when its local deadline passes, so the application stops | Stage 4 |
| **Fail closed** | If the service cannot decide, the protected operation does not proceed | Stage 1 |

## What a caller experiences

A billing worker, which this document calls the **caller**, is about to charge invoice 17. Two worker
processes could pick the same invoice up, so the caller asks the lock service first.

1. **Open a session.** The worker's lock library asks for a session with a ten-second lease. It gets a
   session id and the current epoch. A background thread now sends a heartbeat about every 3.3 seconds.
2. **Acquire.** The worker asks for the name `invoice:17`, with a request id and a maximum wait of two
   seconds. The service answers *granted*, with a **token** (say 9,001) and the lease length.
3. **Check, work, write.** The library sets a local deadline: the monotonic time at which it sent the
   request, plus seven seconds (70% of the lease). The worker loads the invoice, calls the payment
   service, and writes the result. Every write carries the token. Each resource checks it.
4. **Release.** The worker releases by token. The service frees the name and hands it to the next
   waiter, if there is one.
5. **If anything goes wrong.** If the heartbeat cannot get through and the local deadline passes, the
   library tells the worker `LockLost`. The worker stops *before its next side effect*. If it was paused
   and did not hear, the resource refuses the stale token.

That last sentence is the whole point of the design: the worker is *asked* to stop, and the resource
*makes* it stop.

## The same story as the lock's states

![The life of one lock name. A grant is a log entry. A name is held until released, expired (the lease ran out), or revoked, and the next grant always carries a higher token.](diagrams/sd24-lock-states.pdf){width=74%}

Two details matter. **HELD has no way back to HELD with the same token after EXPIRED**: a renewed lease
is the same grant, but an expired one is gone, and the next holder gets a strictly higher token. And
**REVOKED looks like EXPIRED to the next holder** and to the resource: that is why `ForceRevoke` is
safe to build. The old holder is fenced by an ordinary comparison.

## Why a lock alone cannot make a system safe

![A holder (A) pauses 15 seconds with a 10-second lease. Nothing at the resource tells A's write from B's, and both are accepted.](diagrams/video-pause-unfenced.pdf){width=94%}

![The same story when the resource checks the token. A's write carries 41, B's carried 42, and 41 is smaller. Nothing else changed.](diagrams/video-pause-fenced.pdf){width=94%}

The lock service did not misbehave in the first picture. It issued one lease at a time and expired A's on
schedule. The two parties are connected only by a lock service that neither of them can ask at the
instant of the write, because **the check ("do I still hold it?") and the action ("write") are not
atomic, and no amount of care on the client makes them atomic.** Only the resource can do both in one
step.

::: why
**Why can't a shorter lease fix it?** It makes the window smaller, not zero, and it raises the rate of
false expiry: slow holders lose their locks while alive. A longer lease does the opposite. Neither
touches the cause, which is that the check and the write are two steps. The next picture is the
trade in one line.
:::

![Lease length is one trade at every setting. No setting removes a 15-second pause. A 70-second pause beats a 60-second lease.](diagrams/video-ttl-slider.pdf){width=92%}

## One acquisition, millisecond by millisecond

The cue sheet asks for p99 under 20 ms. This table is where those milliseconds go for one successful
acquire in one region across three zones. All figures are an **initial planning budget**, not a
measurement.

| Time | What happens | Who |
|---|---|---|
| 0.0 ms | The library sends `Acquire(invoice:17, requestId, maxWait)` and notes its monotonic clock | Client |
| 0 to 2 ms | Network to the gateway, which authenticates, checks the tenant quota, and hashes the name to a slot | Gateway |
| 2 to 5 ms | The leader batches the entry with others (about 3 ms of batch wait) | Leader |
| 5 to 9 ms | The leader appends to its log and syncs its disk (about 4 ms) | Leader |
| 5 to 14 ms | In parallel, followers append and sync, and acknowledge. A majority is 3 of 5, so the leader needs two followers | Followers |
| 14 ms | The entry is committed. Apply runs: the name is free, so grant with token = log index | State machine |
| 14 to 17 ms | Reply to the gateway and the client. The library sets deadline = send time + 7 s | Gateway, client |

**17 ms used, 3 ms spare.** The follower step is the long pole because it includes both a network round
trip between zones and a disk sync. That is why a quorum across regions, where the round trip alone is
30 to 250 ms, cannot meet the target.

![The same budget as one bar that sums to the target, with the spare drawn.](diagrams/video-budget.pdf){width=95%}

## Where the load lands

![Load map at peak. The only part that must be strictly correct is the committed write path. Every figure is derived in Stage 2.](diagrams/sd24-load-map.pdf){width=88%}

::: load
**At peak (3 times the average):** about 30,000 acquisition attempts a second reach the gateways. About
40% succeed, so about 12,000 grants and as many releases a second, plus waiter enqueues and expiries:
about **30,000 committed writes a second** in total, spread over four groups, about 7,500 each against
a ceiling of about 15,000. Failed try-once attempts are answered from the leader's memory and write
nothing. Heartbeats are about 120 a second, and only an actual expiry becomes a log entry.
:::

\newpage

# Part II: The round, stage by stage

**The clock** (a 75-minute round at the simulator's `typing-adjusted` pace; spoken rounds run about 50 minutes):

| Minutes | Stage | On the whiteboard |
|---|---|---|
| 0:00 to 0:12 | **Stage 1** Clarify requirements | Requirements list and an "out of scope" box |
| 0:12 to 0:21 | **Stage 2** Back-of-the-envelope (three numbers, maybe four) | Four lines of arithmetic |
| 0:21 to 0:33 | **Stage 3** API and data model | Five calls, one state machine |
| 0:33 to 0:51 | **Stage 4** High-level design in three versions, with the walk-through | One baseline, redrawn three times |
| 0:51 to 1:13 | **Stage 6** Deep dives, with **Stage 7** requirements as they arrive | Marks on the baseline |
| Last 10 minutes | **Stages 8 and 9** Failure, SLOs, cost | Short list |
| When asked | **Stage 10** The EM layer (auxiliary at Staff) | Releases, people, months |

Stage 5 (technology) has no slot. The interviewer can ask it at any time, and you answer inline.

**At the Staff bar you pick the deep dives.** Do not wait to be asked. Say which two you would go into
and why: *the paused holder and the partition, because that is where the guarantees live.*

# Stage 1: Clarify requirements

Ask **six questions, not fifteen**. Each one changes the design, so say why you are asking. The answers
below come from the simulator's cue sheet.

| Question | Answer | What it changes |
|---|---|---|
| Who calls this, and for what? | Internal teams: leader election, per-entity exclusion before a write, run-once schedulers | One API must serve long holds, short holds and no-wait. Bounded wait and try-once are in |
| What happens if two holders act at once? | Depends on the team: corrupts records, or wastes an hour of compute | **Splits efficiency from correctness locks.** Decides whether a token is needed at all |
| Scale? | About 10,000 acquisition attempts a second, around 5,000 names, holds 100 ms to 30 s, default lease 10 s | Attempts are not grants. State is tiny. Estimates use these |
| Latency, availability, failure? | p99 under 20 ms, survive losing a minority, one region in three zones, multi-region later | Rules out a quorum across regions. Fixes the CP position |
| What are the protected resources? | Mostly SQL databases and an object store; a few partner HTTP APIs. JVM callers, pauses up to 15 s in the tail | The pause is a requirement. Partner APIs are challenge 2 |
| Several locks at once? Shared mode? Strict order? | Several: some do, tell me what you would say. Shared: no. Strict order: not required | Scope. Pushing back on atomic multi-lock is challenge 6 |

::: why
**Why ask what a double hold costs?** Because it is the only question whose answer changes the *kind*
of system. If a double hold only wastes work, a single cache node with an expiry may be enough, and
building a consensus cluster is an expensive mistake. If it corrupts data, no lock alone will do and the
resource must take part. Asking first, before drawing, is the strongest requirements signal in this
round. **Most teams that ask for a lock have an idempotency problem.**
:::

**Functional requirements** (each becomes a numbered flow in Stage 4):

- **FR1 Acquire** an exclusive lock on a name, with a bounded wait. Try-once is a wait of zero.
- **FR2 Hold and renew** the lease, and learn quickly if it is lost.
- **FR3 Release**, and have a dead holder's locks freed automatically.
- **FR4 Fence**: every grant carries a strictly increasing token the caller can hand to the resource.
- **FR5 Inspect and break glass**: operators see who holds a name and can force-revoke it, audited.

**Non-functional requirements** (initial targets): acquire p99 under 20 ms; acquire availability 99.99%
(about 4.3 minutes a month); survive the loss of 2 of 5 replicas with no manual action; default lease 10 s,
capped at 60 s; **fail closed**; tokens strictly increasing per name and **never going backwards, even
after a disaster-recovery rebuild**.

**Stated cuts:** shared and read-write modes (add behind the same API); atomic multi-name acquire (a
distributed transaction, and we push back); cross-region consensus; a general-purpose key-value store (a
written non-goal, because it is how lock services get ruined).

> "The core is four things: a lease that frees itself, a consensus-replicated record of who holds it, a
> token that orders the grants, and a check at the resource."

# Stage 2: Back-of-the-envelope

## How to do estimates in an interview

Compute a number only if it changes a decision. The shape to aim for is *"X times Y is Z, and Z means I
cannot do the obvious thing, so I do W."* Say the label once per chapter: **given** (from the cue sheet),
**illustrative** (an assumption you chose), **initial target** (a goal to be measured), **derived**
(arithmetic from those).

::: {.key title="Number 1: the ceiling nobody states"}
**Arithmetic.** One holder per name and about 5,000 names means at most **5,000 locks held at once**. A
mean hold of 0.5 s then caps grants at 5,000 ÷ 0.5 = **10,000 a second**, and only if every name is
always held. *(derived)*

**What it means.** Most of the 10,000 attempts a second cannot succeed. They fail or wait. The lock, not
the service, is the limit.

**How it changes the design.** The API needs a **bounded wait** and an explicit **try-once**. Failure is
the normal case on a busy name, so it must be cheap: a try-once that fails is answered from the leader's
memory and writes nothing.

**Say.** *"One holder per name caps the whole system at the number of names divided by the hold time. So
most attempts fail by design, and I make failure cheap."*
:::

::: {.key title="Number 2: the state is tiny, so shard for something else"}
**Arithmetic.** Say 40% of attempts succeed: 4,000 grants a second *(illustrative)*. Held at once, by
Little's law (held at once = arrival rate × time held): 4,000 × 0.5 s = **2,000 locks**. About 5,000 entries (held plus waiting) at
about 200 bytes is **about 1 MB**. *(illustrative)*

**What it means.** The whole state fits in memory and snapshots in milliseconds.

**How it changes the design.** We shard for **write throughput and blast radius**. Never for capacity.

**Say.** *"The state is a megabyte. If I shard it, it is for write throughput and for blast radius, not
because it is big."*
:::

::: {.key title="Number 3: writes, and how many groups"}
**Arithmetic.** Grant plus release is 2 × 4,000 = **8,000 committed writes a second** on average; times a
peak factor of 3 *(illustrative)* is **24,000**; add waiter enqueues and expiries and call it **30,000
all-in**. One group commits about 15,000 writes a second with batched disk syncs *(initial target, to be
measured)*. With 50% headroom: 30,000 ÷ (15,000 × 0.5) = **4 groups**, over **64 hash slots** so a slot
can move later.

**What it means.** One group nearly carries the average. We shard for the peak, and so a bad group takes
a quarter of the names, not all of them.

**Say.** *"Peak is thirty thousand writes a second against a fifteen thousand ceiling. Four groups with
headroom, sixty-four slots so I can rebalance."*
:::

## The full table, row by row

| Quantity | Arithmetic | Label | Decision it drives |
|---|---|---|---|
| Attempts, average and peak | 10,000/s; times 3 = 30,000/s | given; factor illustrative | Size for the peak |
| Concurrency ceiling | 5,000 names; grants at most 5,000 ÷ 0.5 s = 10,000/s | derived | Bounded wait; failure is the normal case |
| Grants and held at once | 40% of 10,000 = 4,000/s; 4,000 × 0.5 s = 2,000 | illustrative | State is small |
| State size | 5,000 entries × 200 B = about 1 MB | illustrative | Shard for throughput, not capacity |
| Committed writes | 2 × 4,000 = 8,000/s; times 3 = 24,000/s; plus extras, about 30,000/s | illustrative | Compare with one group |
| One group's ceiling | about 15,000 writes/s, batched sync on SSD | initial target | 30,000 ÷ 7,500 = 4 groups, 64 slots |
| Renewals | 1,600 long-held ÷ 3.3 s = about 480/s per lock; 400 sessions ÷ 3.3 s = about 120/s | illustrative | Sessions, not per-lock renewal |
| Latency budget | 2 + 3 + 4 + 5 + 1 + 2 = 17 ms, 3 spare | initial target | Quorum in one region |
| Per-name ceiling | at most 1 ÷ hold: 100 ms gives 10/s, 0.5 s gives 2/s, 30 s gives 0.03/s | derived | Hot-name policy |
| Pause against lease | A 15 s pause beats a 10 s lease; a 70 s migration beats a 60 s one | given; illustrative | Tuning cannot fix this; a token can |
| Clock margin | 200 ppm × 10 s = 2 ms. Client stops at 7 s; server at 10 s: 3 s gap | illustrative | Drift is not the risk; pauses are |
| Election budget | 99.99% of 30 days = 259 s; at 2 s an election, about 130 a group a month | initial target | Elections per day is an SLI |
| Token space | 16-bit epoch + 48-bit index; 2 to the 48 is 2.8 × 10 to the 14, over 15,000/s is about 600 years an epoch | derived | A token is one 64-bit number |

::: why
**Why only 1,600 long holds matter for renewals.** A hold of 100 ms never renews, because the lease is 10
s. Only a hold longer than a third of the lease (about 3.3 s) ever sends a renewal. Two percent of grants
are long, about 20 s each: 80 a second times 20 s is 1,600 locks, which is almost the whole held
population (the other 3,920 grants a second × 0.1 s are about 392 locks). Renewal cost is dominated by a
few long holders, such as leader elections, not by the bulk of short ones.
:::

::: warn
**Traps.** Treating 10,000 as grants rather than *attempts* (the ceiling above shows it cannot be). Sharding
"because the data is big". Quoting one group's throughput as a fact. Summing per-stage p99s as if they
added up to an end-to-end p99: they do not, because stages are correlated. Say "planning budget".
:::

# Stage 3: API and data

## The API

Design the API before the boxes. It is the contract, it forces the semantics into the open, and it shows
whether you have thought about failure. Each call carries a tag: **which requirement** it serves and
**which entity** it reads or writes.

**`OpenSession` and `Heartbeat`** (serves FR2, writes Session):

```
OpenSession { owner: "billing-worker-7", ttlMs: 10000 }
  -> { sessionId: 88123, epoch: 6, serverTimeMs: 1731400000000 }   // time is for logs only
Heartbeat { sessionId: 88123 }          // a stream, every ~3.3 s
  -> { ok: true }                       // the client trusts nothing but "ok"
```

::: why
**Why no timestamp the client uses?** Because a timestamp from another machine is a claim about a clock
you cannot trust (challenge 3). The client times its own deadline from when it *sent* the request.
:::

**`Acquire`** (serves FR1 and FR4, writes Lock and Waiter):

```
Acquire { name: "invoice:17", sessionId: 88123,
          requestId: "9f1c...",        // retries are idempotent
          maxWaitMs: 2000 }            // 0 = try once; there is no "wait forever"
  -> granted   { token: 9001, ttlMs: 10000 }
   | queued    { position: 2 }
   | timeout   { }
   | contended { retryAfterMs: 200 }
```

**`Release`** (serves FR3, writes Lock): `Release { name, token }`. Releases only if the token matches
the current holder. **It is impossible to express "release someone else's lock".** That removes a whole
failure: a holder whose lease expired, then woke up and called release, cannot free the new holder's lock.

**`Inspect` and `ForceRevoke`** (serves FR5): `Inspect` shows owner, token, expiry and waiter count and is
documented as *never used for a correctness decision*, because the answer may be stale by the time it
arrives. `ForceRevoke { name, reason, operator }` is audited, alerts, and is deliberately awkward to call.
The next grant gets a higher token, so the revoked holder is fenced like any other.

**The resource's side of the contract** (serves FR4): every write to a protected resource carries the
token, and the resource **rejects it if the token is smaller than the highest it has accepted**.

```sql
UPDATE invoice SET amount = :amount, fence = :token
 WHERE id = :id AND fence <= :token;
-- 0 rows updated: FencedOut. Log both tokens. Alert.
```

::: warn
**Precision.** *Equal* is allowed. One holder may write several times with the same token. Only *smaller* is
rejected. A version that rejects "less than or equal" breaks any critical section with more than one write.
Also pass the token as an **explicit argument**, never in a thread-local: it is lost, silently, the first
time work moves to another thread pool.
:::

::: why
**Duplicates, and the request id.** The network will duplicate an `Acquire`. If the original grant is still
live, a duplicate with the same `requestId` returns **the same grant and the same token**. If the original
has expired, the duplicate must **not** quietly mint a new grant that nobody is waiting for: that would
stall the name for a whole lease for a client that has long since given up. So the state machine keeps
`requestId` results for at least *maximum lease plus the longest plausible network delay*, and answers an
expired duplicate with `expired`. The library also sends a best-effort `Cancel(requestId)` when it times
out. Designed out, not guarded against.
:::

> "Reentrancy: yes, as a hold count in the client library keyed by session. The server keeps one grant per
> name. Doing it on the server doubles the writes for nothing. Scope it to the session, not the process, or a
> reconnecting client deadlocks against its own stale grant."

## The data model

![Conceptual model in Chen notation. A name has at most one holder at a time, which is why locks are independent per name and the service shards.](diagrams/video-erd-chen.pdf){width=96%}

![Physical model. Everything inside a group is keyed by name and lives in exactly one group, so there are no cross-group transactions. The epoch and the token floors live outside the group.](diagrams/video-erd-physical.pdf){width=96%}

**The state machine** is small enough to read whole, which is the point: everything hard is in the
replication, not the logic.

```
apply(Acquire a, index, timeFromEntry):          // same on every replica, in log order
  cur = held[a.name]
  if cur is live and cur.owner == a.owner: return cur        // same owner retrying
  if cur is live: enqueue(a); return queued
  held[a.name] = {owner: a.owner, token: index,              // token = log index: monotonic, free
                  expires: timeFromEntry + a.ttl}
  return granted(index)
```

::: warn
**Never read the clock inside `apply`.** The leader stamps the time into the entry before replicating it. If
each replica read its own clock, two replicas could disagree about whether a lease had expired, and the group
would diverge. A diverged replicated state machine is an unrecoverable incident, and this is the most
common bug in home-built ones. Naming it unprompted is a depth signal. **Expiry is a command, not a
background sweep**: the leader runs a timer and *proposes* `SessionExpired`; followers apply it like
anything else. If the leader dies first, the next leader re-derives pending expiries from state.
:::

![A token is one 64-bit number. The epoch is in the top 16 bits, the log index in the low 48.](diagrams/video-token-bits.pdf){width=86%}

**Which stores, and can you lose them?**

| Store | Holds | If lost |
|---|---|---|
| Replicated log and snapshot | grants, sessions, waiter queues | A minority loss is survived. Total loss: start empty (challenge 4) |
| Leader memory | last heartbeat per session | A new leader treats every session as alive for one lease |
| Epoch store | epoch and slot token floors | **Must not be lost**: tokens would go backwards. It is itself a small replicated store |
| The resource | highest token per row | Its own durability. The check is only as good as the store that keeps the highest token |

::: warn
**One row, one lock name.** Tokens are only comparable within one name's group. If two code paths guard the
same resource row with *different* lock names (an alias, a refactor, a second team), their tokens come from
different groups and a comparison means nothing. The rule: **a protected row is guarded by exactly one
name**, and the name is part of the resource's contract.
:::

# Stage 4: High-level design

Build it in three versions. Each is introduced by the **objection** it answers, and the system stays on
screen: later pictures are views of one baseline, and boxes never move.

## Version 1: the simplest thing that works

![V1: the library, one lock server holding a map of name to owner and expiry, and the resource drawn on top.](diagrams/video-base-v1.pdf){width=92%}

An application with a lock library, and one lock server that keeps a map from name to owner and expiry in
memory. Acquire checks the map. A lease means a dead holder's name frees itself. For an *efficiency* lock
this might be enough.

**The objection.** The server restarts and forgets who holds what. A acquires at t = 0; the server crashes
at t = 4 and restarts at t = 5 with an empty map; B acquires at t = 6 and is granted the same name while A is
still working. Two holders, caused by the lock service. And one box is a single point of failure for every
team that uses it.

## Version 2: replace the box with a consensus group

![V2: a consensus group of five replicas replaces the single server. The token is the log index of the grant.](diagrams/video-base-v2.pdf){width=92%}

Five replicas, one leader. Every grant is a **log entry**, and counts only once a **majority** (3 of 5) holds
it. If the leader dies, a follower that has all committed entries takes over, so no grant is forgotten. And the
token falls out for free: it is the log index of the grant entry.

::: why
**Why a majority, in one line.** Any two majorities of five share at least one replica. So any future leader
must have been among the replicas that held every committed entry, and therefore has it. Terms make sure two
leaders never both commit: a node that sees a higher term obeys it.
:::

**The objection.** The group is right, but callers cannot tell when they have lost the lock, every team
hand-rolls its own heartbeat and clock arithmetic, and the service is not safely reachable (no auth, no
quotas, no routing to the leader). **Half the correctness lives in the client library**, so the library is
part of the product.

## Version 3: sessions, a library, and a gateway

![V3, the baseline. The library holds a session, tracks a monotonic local deadline, and fires LockLost. A stateless gateway authenticates, applies quotas and routes to the leader.](diagrams/video-base-v3.pdf){width=96%}

The library holds **one session** with one heartbeat (the dashed purple arrow). It keeps a **local deadline**
on a monotonic clock and calls back with `LockLost` the moment it passes. A stateless **gateway** sits in
front: it authenticates, applies tenant quotas, and routes to the group's leader (cached, with
redirect-on-`NotLeader`). The token comes back in the grant and the application passes it to the resource,
which is still drawn grey and unchanged.

```
// every ~3.3 s, on a background thread
sentAt = monotonicNow()
try   { heartbeat(sessionId)
        deadline = sentAt + 0.7 * ttl }        // measured from SEND time: the conservative choice
catch (e) { if (monotonicNow() > deadline) loseAllLocks(e) }   // fail closed, loudly
```

::: warn
**What V3 still does not do.** Nothing checks the token. A paused holder that wakes up after the lease expired
still writes. Also note what a *heartbeat* proves: that the **process** is alive, not that the **work** is
making progress. If the application thread hangs while the heartbeat thread keeps running, the session stays
alive and the lock is held **forever**. So every grant also carries a **maximum hold time** (default 5 minutes,
configurable), after which `LockLost` fires unless the application explicitly **extends** the lock. A hung but
alive holder is failure F9, and the answers are a bounded hold, `ForceRevoke`, and an alert on holds beyond
their expected duration.
:::

## The numbered flows, one per functional requirement

![FR1, acquire: the library sends Acquire; the gateway authenticates, checks quota and routes; the leader commits; token and lease come back.](diagrams/video-flow-fr1.pdf){width=92%}

**FR1 Acquire.** One: the library sends `Acquire` with the name and a request id. Two: the gateway
authenticates, checks the tenant's quota, hashes the name to a slot and routes to that group's leader. Inside
the group: the leader appends, a majority acknowledges, it commits, and `apply` grants with the log index as
the token. Three: token and lease return to the gateway. Four: back to the library, which sets its deadline
from when it *sent* the request.

![FR2, hold and renew: a heartbeat per session, answered by the leader under its lease.](diagrams/video-flow-fr2.pdf){width=92%}

**FR2 Hold and renew.** One: the heartbeat (dashed, asynchronous). Two: the gateway passes it on as a
"session alive" note. The leader keeps liveness in memory under its leader lease, so **a heartbeat is not a
consensus write**. Only an actual expiry becomes a log entry.

![FR3, release and expiry: release by token, with a hand-off to the head waiter in the same step.](diagrams/video-flow-fr3.pdf){width=92%}

**FR3 Release and expiry.** Release by token takes the same four arrows. The leader commits; `apply`
compares the token, frees the name, and hands it to the head waiter *in the same step*. A dead holder takes no
arrow at all: its heartbeats stop, and after one lease the leader proposes a single `SessionExpired` that
frees everything that session held.

![FR4, fence: the write carries the token; the resource compares it with the highest it has accepted.](diagrams/video-flow-fr4.pdf){width=92%}

**FR4 Fence.** One: the application writes to the resource with the token. Two: the resource compares. Not
smaller: accept and store. Smaller: reject `FencedOut`, log both tokens, alert. **This arrow never touches the
lock service.** The service issued an order; the resource enforces it.

![FR5, inspect and revoke: audited, and the next grant carries a higher token.](diagrams/video-flow-fr5.pdf){width=92%}

**FR5 Inspect and revoke.** The operator console calls `ForceRevoke` with a reason; the gateway checks the
operator's identity; the leader commits a revoke entry and an audit entry. The old holder learns on its next
heartbeat, and even if it does not, its next write is fenced.

## The C4 views and the sequences

![C4 level 1. Note the arrow from the application straight to the protected resources: the write does not go through the lock service.](diagrams/video-c4-context.pdf){width=96%}

![C4 level 2. The library runs inside the application; the gateway is stateless; four groups of five replicas; an epoch store used only on a rebuild.](diagrams/video-c4-containers.pdf){width=96%}

![Acquire, message by message. A majority acknowledgement commits the entry, and the token is its log index.](diagrams/video-seq-acquire.pdf){width=86%}

![Losing the lease. The client stops first, by design: its deadline is 7 s from the last send, the server waits the full 10 s.](diagrams/video-seq-heartbeat-loss.pdf){width=86%}

![Release with a direct hand-off: one committed write, one waiter woken, no polling.](diagrams/video-seq-release-handoff.pdf){width=80%}

![The resource's check: accept the current holder, reject the stale one.](diagrams/video-seq-fence-write.pdf){width=70%}

**What correct caller code looks like.** Show it on the board: it shows the design from the caller's side.

```
try {
  g = session.acquire("invoice:" + id, ttl, maxWait: 2s)        // bounded
  if (g.empty) return retryLater()                              // no side effect
  inv = repo.load(id)
  session.checkStillHeld(g)                                     // narrows the window (liveness)
  payments.execute(inv, g.token)                                // the token makes it safe
  repo.markPaid(id, g.token)                                    // both resources check
  session.release(g)
} catch (LockLost e) { return abortedSafely() }                 // never "continue anyway"
```

::: warn
**`checkStillHeld` narrows the window. It does not close it.** Between the check and the write the lease can
still expire. The check is a *liveness* optimisation that stops most wasted work. The token is the *safety*
mechanism. Be clear about which mechanism provides which property: that is the whole design.
:::

## The latency budget, and the walk-through order

Walk one acquisition end to end with the numbers from Part I (17 ms of 20, 3 spare). Then say which box worries
you most: *the check at the resource*, because it is the one the lock service does not control.

\newpage

# Stage 5: Why these technology choices

Asked at any time, and you answer inline. The pattern for every tool: **why here, what to explain one level down,
and the alternative that loses with the failure that rules it out.** Mechanism first, product second.

## A consensus coordination store for the grant record

**Why here.** A lock needs a replicated record that survives the loss of a minority, an order for every change,
leases that expire, and an atomic "set if absent". A consensus-backed key-value store in the ZooKeeper, etcd or
Consul family has all four, plus a per-key revision number that is a ready-made fencing token and watches that
wake waiters in order. We run it behind **our own API and library**, so the substrate can be swapped later.

**One level down.** Writes go to the leader, are appended to a log, replicated, and committed on a majority
acknowledgement. Reads that must be fresh either go through the log or confirm leadership (a read index, or a
leader lease). A lease is an object with a TTL that keys attach to; when it expires, the attached keys vanish.
A transaction is a compare-and-set: *if this key does not exist, create it and attach the lease, else tell me who
has it*. The revision is a cluster-wide increasing number stamped on every change.

| Approach | Verdict | The failure that rules it out |
|---|---|---|
| **Consensus coordination store** | **Pick** | Load beyond one cluster's write ceiling (then shard); semantics it cannot express (priority, shared mode) |
| One cache node, set-if-absent with expiry | Efficiency locks only | Replication is asynchronous: the primary acknowledges the grant and dies before the copy arrives. The new primary grants it again |
| A quorum of independent cache nodes | Not for correctness | Safety rests on timing: a pause between acquire and use, or one node's clock jumping, lets a second client assemble a majority. And it produces **no token** |
| A relational row | Under a few thousand grants/s, or when the resource is in the same database | Throughput is bound to the primary; a hot row is a contention point; failover needs synchronous commit, or it is the cache node's problem again; a row lock tied to a connection has no lease |
| A custom consensus service | Only on evidence | Tens of engineer-months to build and a standing team to run (Stage 10) |
| No lock: conditional write or idempotency key | **Check first, every time** | The operation is not idempotent and the resource has no conditional write |

::: why
**The debate about quorum-of-caches, in two sentences.** Its authors argue the timing assumptions usually hold;
its critics argue a lock must not depend on them, and point out it produces no token to reject a stale holder.
Both positions are defensible. What is not defensible is being unaware of the exchange. Knowing it, and saying why
you choose a protocol whose safety does not rest on timing, is the depth being probed.
:::

> "Why not a row in a relational database with `SELECT FOR UPDATE`? A row lock lives as long as the connection,
> so a paused client keeps it and a dead one drops it only when the database notices: no lease. It hands out
> no number the resource can check later: no token. It is the right answer when the resource lives in the same
> database, so lock and work commit together, or under a few thousand a second."

## Conditional writes at the resource

**Why here.** The token must be checked atomically with the write, and only the resource can do both. Most
storage systems already have the primitive: a SQL `UPDATE ... WHERE fence <= :token` (or a version column), an
object store's write-if-generation-matches, a document store's update-time precondition, a transactional
store's read-modify-write inside a transaction. When the protected resource is one of these, **the fencing token
is the generation, version or ETag**, and the design is simpler.

**One level down.** The check and the write are one statement, so they are atomic under the store's own
concurrency control. The stored maximum is part of the row, so it is as durable as the data.

**Alternative.** A check in the *application* ("if my token is current, then write"): two steps, and the
pause lands between them. That is the failure.

## A validating proxy, where the resource cannot check

**Why here.** A partner HTTP API with no conditional write has nowhere to put the check. A proxy keeps the
highest token per resource in a **consistent** store and forwards only fresh calls.

**One level down.** The proxy's step is itself a conditional update (`set max = :t where max <= :t`), so two
concurrent holders cannot both pass. It fails **closed**. It is scoped per resource class so one failure does not
take everyone.

**Alternatives.** An idempotency key (cheapest, when the operation allows it). Accepting an efficiency lock
and saying so in the contract (honest). Neither is a proxy, and both are cheaper.

## Technologies, one level down

Every container with the technology it runs on, how it is built, the alternatives rejected and why, and the question an interviewer asks about it. Generated from `stack.json`.

<!-- stack:sections -->

## Consensus groups: an etcd-class store

*How it is built.* Writes go to the leader, are appended to a log, replicated and committed on a majority. A lease is an object with a time to live that keys attach to; when it expires the keys vanish. Acquire is one transaction: if the name does not exist, create it and attach the lease, else say who holds it. Every name lives in exactly one group, chosen by hash, so there are no cross-group transactions. Reads that must be fresh confirm leadership first. The revision is stamped on every change and rises across the group; the token is that revision with the epoch in its top bits. Watches wake waiters in order.

*Why etcd-class store, 4 groups × 5 replicas, one name in one group:* A lock needs a replicated record that survives losing a minority, an order for every change, leases that expire and an atomic set-if-absent. Its per-key revision is a ready-made fencing token.

*Rejected:*

- **One cache node, set if absent with expiry**: Replication is asynchronous: the primary grants the lock and dies before the copy arrives, and the new primary grants it again.
- **A quorum of independent cache nodes**: Safety rests on timing: a pause between acquire and use lets a second client assemble a majority. And it produces no token.
- **A relational row with select for update**: A row lock lives as long as the connection: no lease, no token. Right when the resource is in the same database.

*Course:* theory/04 (replication and consistency) and theory/07 (correctness under failure).

*Drill.* "The leader of a group dies mid-acquire. Can two clients both be told they hold the name?" No. A grant commits only on a majority, and the new leader has every committed entry. A client that never saw the answer retries and learns the truth. The trap is a read from a follower that has not caught up.

## Lock SDK: a library with a local deadline

*How it is built.* The library opens a session and sends a heartbeat about every third of the lease, which is 3.3 seconds for a ten-second lease. It keeps a local deadline shorter than the lease. If the heartbeat cannot get through and the local deadline passes, it raises LockLost to the application, which must stop. The library never reuses a token after expiry. A renewed lease is a new grant with a new token. The local deadline allows for the heartbeat period and the clock-rate error, not for a pause.

*Why JVM and Go libraries; a heartbeat every third of the lease:* The holder must stop on its own when it cannot prove it still holds the lock. That logic has to live in the process that does the work.

*Rejected:*

- **A thin client that only calls acquire**: The application would have to build the heartbeat and the deadline itself, and every team would get it slightly wrong.
- **A sidecar process per host**: One more process that can pause independently of the application, which is the failure we are guarding against.

*Course:* theory/07 (correctness under failure).

*Drill.* "The application's thread pauses for forty seconds with a ten-second lease. What stops the stale write?" Nothing in the library can, since the whole process is paused. That is why the token exists: the resource rejects the stale write because a newer token has been seen.

## Gateway: stateless, with the slot map

*How it is built.* The gateway authenticates the caller, applies a per-tenant quota, maps the name to its group with the slot map and forwards to the cached leader of that group. On a not-leader answer it refreshes the leader and retries once. It holds no lock state, so losing a gateway loses nothing but in-flight calls. The operator console reaches the same gateway for force revoke, with its own role.

*Why Go service on Kubernetes, gRPC, three zones:* Clients should not know which group owns a name or who leads it. A stateless layer keeps that knowledge and can be restarted at will.

*Rejected:*

- **Clients talking to the groups directly**: Every client library would carry the slot map and leader changes, and a rebalance would need a client release.
- **A shared layer-7 proxy**: Leader routing is application knowledge; a generic proxy would round-robin onto followers.

*Course:* theory/08 (reliability and operations).

## Epoch store: a small durable counter

*How it is built.* The epoch sits in the top sixteen bits of every token, and the log index in the low forty-eight. It is read at group start and bumped only on a rebuild or a slot move, a handful of times a year. The store is itself replicated, three replicas across zones, and is written with a conditional update. Token floors per slot are kept here too, so a rebuilt group seeds above every token ever issued.

*Why A three-replica strongly consistent store, outside the groups:* If every group were lost, tokens would restart from zero and go backwards. The epoch is the one number that must survive, so it lives somewhere else.

*Rejected:*

- **Keep the epoch inside the groups**: The failure it protects against is losing the groups. It must not share their fate.
- **A clock-derived epoch**: A wall-clock epoch depends on clocks agreeing across a rebuild; a bad clock gives a smaller number.

*Course:* theory/07 (correctness under failure).

*Drill.* "Every group is lost in a disaster. How do you restart without issuing a token an old holder could beat?" Bump the epoch in the epoch store, start the groups empty, seed the token floor above the old maximum, and wait one maximum lease before granting. Every new token exceeds every old one.

## The check at the resource

*How it is built.* Where the resource supports it, the token is the generation, version or entity tag, and the write is conditional on it: a SQL update where the stored token is at most mine, or a write-if-generation-matches. Where the resource is a partner API with no such primitive, a validating proxy keeps the highest token per resource in a consistent store and forwards only fresh calls. It fails closed. The proxy's own step is a conditional update, so two concurrent holders cannot both pass.

*Why A conditional write at the resource; a validating proxy where it cannot:* The lock service cannot stop a stale write; only the resource can, and only if the check and the write are one atomic step.

*Rejected:*

- **A check in the application before the write**: Two steps, and the pause lands between them. That is exactly the failure.
- **An idempotency key alone**: Cheapest, and the right answer when the operation allows it. It does not help when the second write is a different, valid operation.

*Course:* theory/07 (correctness under failure).

*Drill.* "The resource is a partner HTTP API with no conditional write. Where does the check go?" In a validating proxy that keeps the highest token seen per resource in a consistent store and rejects lower ones, failing closed. The proxy's step is itself a conditional update.

<!-- /stack:sections -->

## The stack on one page

<!-- stack:summary -->

| Container | Choice | Rejected | The deciding reason |
|---|---|---|---|
| Consensus groups | etcd-class, 4 × 5 replicas | Cache node; Redlock; SQL row | Safety without timing; a revision as token |
| Lock SDK | Library, local deadline | Thin client; sidecar | Stop on our own |
| Gateway | Go, gRPC, stateless | Direct clients; generic proxy | Routing knowledge in one place |
| Epoch store | 3-replica durable counter | In the groups; clock epoch | Survives losing every group |
| Resource check | Conditional write; proxy | App-side check | Atomic with the write |

Each fix in Stage 6 rejects one tool by name:

| Deep dive | Rejected | Because |
|---|---|---|
| 6.1 | A lease with no token | a paused holder wakes after expiry with no idea, and writes; only a token the resource checks can reject it. |
| 6.2 | Checking the token in the application | two steps, and the pause lands between them; the check must be atomic with the write. |
| 6.3 | A quorum of cache nodes for the lock | its safety rests on timing assumptions, and it issues no token. |
| 6.4 | Restoring the groups from a backup | the backup predates later grants, so tokens would go backwards; start empty with a higher epoch. |
| 6.5 | Every waiter polling the same name | a thundering herd at expiry; a watch wakes one waiter in order. |
| 6.6 | One global lock for a whole resource family | it makes one group the bottleneck for everything; split the name and keep one name in one group. |
| 6.7 | Alerting on whether the service is up | it can be up while grants miss their budget; measure acquire latency and token monotonicity. |

<!-- /stack:summary -->

# Stage 6: Deep dives

You pick two or three and say why. Each section below is **risk, mechanism, failure case, Say, weak answers**,
and ends with **what the first draft glosses over**: the race or the interaction that makes the obvious answer
subtly wrong. The video runs all seven as challenges in this order, because each fix creates the next question.

## 6.1 The paused holder (the crux)

**The risk.** A holder is stopped for longer than its lease (garbage collection, a virtual machine migration, a
starved CPU, a suspended laptop). It does not crash. It **pauses**, and wakes with no idea time passed. Another
holder has been granted the name and has written. Now both write.

**The mechanism.** Not a longer lease, and not a check before the write. A **fencing token**: each grant carries
a number larger than every earlier grant for that name; the resource keeps the highest it has accepted and
rejects any write with a smaller one. Safety is enforced **at the resource**. The lock service's job shrinks to
issuing an order, which consensus does well.

**The failure case, with numbers.** TTL 10 s. t = 0.0 A acquires `invoice-17`, token 41. t = 0.2 A reads. t = 0.3
A checks "still held: yes" and pauses. t = 10.0 the lease expires. t = 10.4 B acquires, token 42. t = 10.5 B
writes. t = 15.3 A resumes and writes with 41. Rejected: 41 is smaller than 42. Raising the lease to 60 s moves
the failure to a 70 s pause and makes every real crash stall its name for a minute.

![The attack on the baseline: the arrow to the resource, where the write lands unchecked.](diagrams/video-ch1-attack.pdf){width=88%}

![The fix: a check at the resource.](diagrams/video-ch1-fix.pdf){width=88%}

![The fix as a sequence.](diagrams/video-seq-ch1-pause.pdf){width=84%}

> "A lease cannot guarantee exclusion at the resource, because the holder cannot know it still holds the lock when
> its write lands. So the grant carries a token that only increases, and the resource rejects anything older than
> it has accepted. Safety lives at the resource. The lock service only has to give a correct order."

**What the first draft glosses over: A's stale write can arrive *before* B's first write.** The resource has only
seen 41, so it accepts A's write (41 is not smaller than 41). Then B, who read the row earlier, writes 42 on top
of it, and **A's update is lost**. Fencing rejects stale writes *after* a newer token has been seen; it does not
repair a stale read. Two ways to close it:

1. **One conditional write.** Make B's whole critical section a single statement against the version it read. The
   token is the version.
2. **Claim first.** B sends its token to the resource *before* it reads, so the stored maximum becomes 42; any
   later write by 41 is rejected. In a database, make the **first statement of the transaction** the fence bump
   (`UPDATE ... SET fence = :t WHERE id = :id AND fence <= :t`): it takes the row lock, so a stale holder's later
   bump either fails or waits, and the lost-update window closes.

![Claim first, then read: the stored maximum becomes 42 before B reads, so a stale write by 41 is rejected.](diagrams/video-seq-ch1-claim.pdf){width=70%}

**Weak answers.** "Use a longer TTL." "Check the lease before writing." "Use a lock in Redis with a random value."
"The client should know." **Strong:** names the pause unprompted, puts a token at the resource, states what the
resource must do, and volunteers the stale-first-write case.

## 6.2 The resource cannot check (the crux, part two)

**The risk.** The thing being protected is a partner's HTTP API, or a cron job. There is no conditional write, and
the pause scenario is back with nowhere to put a fence.

**The mechanism.** **Ask first, then pick the cheapest place to enforce.** In order: (1) is the operation
idempotent? Then an idempotency key (the lock name plus the job instance) makes a double hold harmless, and the
lock is an *efficiency* tool. (2) Does the resource have a conditional write? Its version is the token. (3)
Otherwise put a **validating proxy** in front. (4) If none fits, ship an efficiency lock and say so plainly in the
contract.

![The attack: a partner API with no conditional write.](diagrams/video-ch2-attack.pdf){width=86%}

![The fix: a proxy that keeps the highest token per resource.](diagrams/video-ch2-fix.pdf){width=86%}

![The proxy, accept and reject.](diagrams/video-seq-ch2-proxy.pdf){width=84%}

**Sort the callers before building (illustrative survey of 100):** 55 only avoid duplicate work (efficiency lock,
no token); 30 write to a store with a conditional write or version column (their own version is the token); 10 call
something with neither (a proxy); 5 are truly non-idempotent with no check possible (change the contract, or
accept the risk in writing with a named owner). The numbers are made up to show the shape. The method is the point.

> "Before I build a lock for a team I ask what a double hold costs and whether the operation can be made idempotent.
> If the resource supports a conditional write, the resource enforces exclusion and the lock is an optimisation. I
> only claim a correctness lock where something downstream checks the token."

**What the first draft glosses over.** The proxy is a new component that must itself be consistent, and a new
single point of failure: it fails closed, keeps its table in a consensus-backed store, and is scoped per resource
class. **Idempotency records must outlive the longest duplicate**: at least *maximum lease plus maximum pause plus
retry horizon* (illustratively 24 hours for a 60-second lease), or a late duplicate is mistaken for new work. And
**the honest limit:** a non-idempotent call to a system with no check cannot be made safe by any lock.

## 6.3 Time: clocks and leases

**The risk.** A client's clock is five seconds slow, or time is stepped back eight seconds mid-lease. The naive
design returns an expiry timestamp and the client compares it with its own clock.

![A slow client clock: for five seconds two holders both believe they hold the lock.](diagrams/video-clock-skew.pdf){width=92%}

**The mechanism.** **Durations, not timestamps.** Three kinds of time, each with one job: the **wall clock** can
jump either way (never for lease arithmetic); a **monotonic clock** never goes backwards on one machine but means
nothing across machines (use it for durations); **logical order** (log index, term) says nothing about duration
but is totally ordered (use it for the token). The client measures `deadline = send time + 0.7 × lease` on its
monotonic clock; the server counts the lease from its own commit on its own monotonic clock; **no timestamp
crosses the wire**.

![The client stops first. Seven seconds against ten: a three-second margin for round trips and scheduling.](diagrams/video-clock-fixed.pdf){width=92%}

::: why
**Why measure from the send time?** The server's lease started when it *received and committed* the request,
which is later than when the client sent it. Measuring from the send time makes the client's deadline earlier
than the server's by at least the round trip. So the client always stops first, and there is never a window in
which it believes it holds a lock the server has given away. This is what the original lock-service paper and
the consensus stores do, and it is what people mean by a *safe* lease.
:::

> "I use monotonic clocks for durations and logical order for correctness. The client gives up before the server
> does, so there is never a window where it believes it holds a lock the server has given away. And because that
> still assumes bounded drift, the token at the resource is what the safety argument rests on."

**What the first draft glosses over.** (1) The margin is **not for drift**: 200 ppm over 10 s is 2 ms. It is for
round trips and scheduling. (2) A pause **between reading the monotonic clock and writing** defeats any margin:
that is 6.1 again, and the token is the backstop. (3) Bounded drift is an *assumption*; with fencing it is no
longer load-bearing for safety, only for how often a holder is fenced. We still monitor clock health and the rate
of missed local deadlines. (4) A timestamp is not a valid token: clocks go backwards. A random identifier is not
either: no order. (5) With bounded-uncertainty clocks (a hardware-assisted time service) you can make a lease's
safety argument a proof rather than an assumption; without them, "NTP is probably fine" is a liveness assumption
masquerading as a safety one.

## 6.4 Leader loss, partition, and losing the group

**The risk.** The leader dies mid-grant, and a partition leaves two of five replicas talking to some clients.
The naive answer: promote a follower fast and let the minority side keep serving, to stay available.

![A partition: R1 (old leader) and R2 are cut off from R3, R4, R5. R1 sees 2 of 5 and cannot commit.](diagrams/video-partition.pdf){width=90%}

**The mechanism.** **Majority commit and terms.** Only the majority side commits; a stale leader steps down when
it sees a higher term and discards uncommitted entries. Heartbeats are answered by the leader under a short
**leader lease**, so they are not log entries. A new leader treats every session as alive for one full lease (the
**grace period**), or a failover would read every heartbeat gap as a death and evict every lock at once. Tokens are
log indexes, so they stay monotonic across terms.

![Both sides ask for the same name: the majority commits; the minority answers "unavailable".](diagrams/video-seq-ch4-election.pdf){width=86%}

::: why
**The honest CP position.** Safety unconditional; liveness given up on the minority side. There is no clever third
option, and interviewers listen for candidates who try to invent one. For a correctness lock, unavailability of the
lock service must become unavailability of the protected operation. If the business cannot accept that, the
requirement is really an efficiency lock: make the resource idempotent instead.
:::

**The second-level push: three of five replicas are gone, or someone restores last night's snapshot. What happens
to the tokens?** Without a majority the service **fails closed**: libraries reach their local deadlines, get
`LockLost`, and stop. The dangerous part is the **restore**. Restoring an old snapshot sends the log index
backwards, so the next grant of a name reuses a token already issued. The resource holds a much higher number, so
it rejects every new holder as stale; and in the other direction a stale holder from before the loss could slip
through. **Tokens must never go backwards, even across a disaster.**

So disaster recovery is not a restore: it is **start empty with a higher epoch**, then **wait one maximum lease**.

![Disaster recovery: bump the durable epoch, start empty, seed the token floor, wait 60 seconds, then grant.](diagrams/video-seq-ch4-recovery.pdf){width=82%}

> "Under partition I choose safety: the minority side refuses, it does not guess. After the loss of a whole group I
> start empty with a higher epoch, so every new token exceeds every old one, and I wait out the longest possible
> lease before granting. The outage is a minute. The alternative is two holders."

**What the first draft glosses over.** (1) **Leader-lease reads are clock-dependent.** A leader that answers
"held, by X" from memory relies on bounded clock drift; a leader with a slow clock could answer from stale state
after a new leader exists. This costs *liveness only* (a wrong "no"), never safety, because every **grant** goes
through consensus. It is why `Inspect` is documented as never usable for correctness. (2) **The epoch store is
itself critical.** If it is lost, a rebuild cannot know a safe epoch. It is a tiny replicated store of its own.
(3) The **quiet period** equals the longest lease we allow (60 s), so every old holder has stopped on its own
deadline before a new grant can be issued. (4) After an election, a client that could not heartbeat during a
3-second election has not lost anything: its deadline is still 7 s from the last send.

## 6.5 The top of the hour

**The risk.** Traffic triples at the top of the hour and 2,000 clients retry at once after a network blip. One
group commits about 15,000 writes a second and the peak is 30,000. The backlog grows by 15,000 a second: after 10 s
it is 150,000 deep and latency exceeds the 10 s lease. Grants that were in flight have already expired, clients
retry, load rises: a **metastable collapse**, which cannot recover even when the peak passes. **More replicas do not
help**: every write must reach a majority, so replicas add fault tolerance, not write throughput.

**The mechanism.** **Partition by name, admit at the edge, retry with jitter.** `slot = hash(name) mod 64`, slots
mapped to four groups. The gateway applies per-tenant quotas and answers `overloaded, retry-after` instead of
queueing. The library retries with jittered exponential backoff. Sessions keep renewal at about 120 a second rather
than 480. The leader batches many entries into one disk sync. This works because locks are independent per name:
**there are no cross-group transactions**, so the partition costs nothing.

![The attack: one group at three times the load.](diagrams/video-ch5-attack.pdf){width=86%}

![The fix: groups by hash of the name, and shedding at the gateway.](diagrams/video-ch5-fix.pdf){width=86%}

![Shed at the edge, retry with jitter.](diagrams/video-seq-ch5-admission.pdf){width=76%}

**The second-level push: one group goes bad, or a slot must move while its locks are held.** A bad group takes a
quarter of the names with it and **fails closed**; the other three are untouched. That is the blast radius, and it
is why we shard even though the data is tiny. Moving a slot is the dangerous operation:

![Moving a slot: freeze, drain held locks (at most one maximum lease), bump the slot's epoch, unfreeze in the new group.](diagrams/video-slots.pdf){width=90%}

Without the **epoch bump**, a name that moves to a group with a lower log index would see its tokens go backwards.
Same rule as before.

> "I size for the peak: thirty thousand writes a second against a fifteen thousand ceiling means four groups with
> headroom. Replicas do not add write throughput. I shed load at the gateway with a retry-after, make clients back
> off with jitter, and shard by name because locks are independent. A bad shard fails closed for a quarter of the
> names."

**What the first draft glosses over.** **Leader balance:** with four groups on a handful of machines, leadership
can pile up on one machine; a background balancer that transfers leadership is unglamorous and mandatory.
**Snapshot transfer** to a slow follower can saturate the network during an incident and turn one sick replica
into a dead cluster: rate-limit it.

## 6.6 One hot name, and several locks at once

**The risk.** One name gets 40 attempts a second and each hold lasts 100 ms. A name can grant at most **1 ÷ hold =
10 a second**, so it is four times over. If waiters poll every 50 ms, 30 waiters make 600 polls a second on that one
name; each release wakes them all and 29 lose (a **herd**); with an unbounded queue the depth grows by 30 a second
and after 10 s a new waiter waits about 30 s, longer than its own lease. Sharding does not help: one name lives in
one group.

![One name, 100 ms holds: capacity 10 a second against 40 arriving.](diagrams/video-hot-key.pdf){width=90%}

**The mechanism.** **A bounded wait with directed hand-off.** Waiters queue per name, with a depth cap,
**scoped to sessions** so a dead waiter is reaped. `Release` grants to the head waiter *in the same committed
step*: one write, one waiter woken. Beyond the cap or the wait budget the answer is `contended, retry-after`.
Waiting costs no writes. The herd is gone.

![The fix on the baseline: a bounded per-name waiter queue.](diagrams/video-ch6-fix.pdf){width=86%}

![Release hands over in one step.](diagrams/video-seq-ch6-queue.pdf){width=80%}

**The second-level push: a team asks to acquire three locks atomically.** Push back first: atomic multi-name
acquisition across groups is a distributed transaction. If it must be done: a **canonical order** (the library
sorts names and acquires in that order, so two callers cannot wait on each other in a cycle); **try with a
timeout and release everything** on failure; and **bounded leases**, so any deadlock that still happens heals
within one lease. Building a wait-for graph to detect cycles is rarely worth it, and saying so is a better answer
than describing the algorithm.

> "A lock serialises. If the name is hot, the lock is the wrong tool. I bound the queue, hand the lock directly to
> the next waiter so a release is one write, and return an explicit rejection beyond the limit. For several locks
> I fix the order, bound every wait, and rely on leases so a deadlock heals in one lease. I would not offer atomic
> multi-lock."

**What the first draft glosses over: the phantom grant.** Hand-off happens *inside `apply`*, which must be
deterministic. But whether the head waiter's session is still alive is *volatile* leader memory, which `apply`
must not consult. So the hand-off can grant the name to a waiter that died a moment ago, and the name is locked
for nobody for up to **one lease**. Two honest options: accept a worst-case stall of one lease and expose a
metric ("grants never used"), or have the leader check liveness first and *propose* `HandOff(name, waiter)` as an
explicit entry. We take the first for v1. **FIFO versus barging:** hand-off is first-come by construction and costs
a little tail latency; `try-once` is allowed to barge, so a free name is never idle behind a slow waiter.

## 6.7 How would you know it is broken?

**The risk.** It is three in the morning, a team says duplicates are happening, and the dashboard is green:
availability 99.99%, p99 8 ms. But one service has 12 `FencedOut` rejections a minute, its renewal failures are
rising, and the hold-time p99 on one name grew from 0.5 s to 9 s. The dashboard watches the machine. The promise is
broken somewhere it does not look.

**The mechanism.** **Measure the guarantee, not the machine.**

| SLI | Target (initial) | Why |
|---|---|---|
| Acquire availability | 99.99% | The headline contract |
| Acquire latency p50 / p99 | 3 ms / 20 ms | Locks sit in a request path |
| Session-loss rate | under 0.01% of sessions an hour | Every loss may abort work |
| **Fenced-out writes** | **alert on any** | A stale holder reached a resource: the net worked, or it is the first sign of a problem |
| Elections per group per day | under 1 | An unhealthy group, and the error budget |
| Time to leader after failure | under 2 s p99 | Bounds the unavailable window |

**Symptom pairs** (one metric says something is wrong; two say where):

| Symptom | Together with | Conclusion |
|---|---|---|
| Fenced-out writes up | renewal failures up on one client | That client is pausing. The net worked. Fix the client |
| Elections up | acquire p99 up | An unhealthy group or disk |
| Hold-time tail up | waiter depth up | Someone holds a lock across a network call, or a hot name |
| Token gaps up | attempts up | A retry storm |

Plus a **canary lock** acquired continuously (a quiet failure shows up as a missed acquire), and an **offline
checker** that replays the grant log for overlapping holds.

![The error budget turns a target into a constraint: 259 seconds a month, about 130 elections a group.](diagrams/video-error-budget.pdf){width=88%}

**The second-level push: fenced-out is zero this week. Are you safe?** No. Zero could mean nobody is sending
tokens. Track **coverage**: the share of protected writes that carry a token, and count writes that arrive
without one. And a double hold that causes no stale write is invisible to the resource: the log audit finds
overlapping holds from the server's durations. **You can observe a violation after the fact and alarm on its
precursors. You cannot observe an absence of risk.**

> "I alert on the guarantee. Any fenced-out write pages someone, because it is either the safety net working or
> the first sign of a problem. I read metrics in pairs so each page names a cause. I track how many protected
> writes carry a token at all, and I audit the grant log for overlapping holds. A green dashboard about the service
> says nothing about the promise."

## 6.8 How the whole system degrades, in priority order

When things get worse, what do you give up first? Say it before being asked.

| Order | Condition | What gives |
|---|---|---|
| 1 | One client pauses or is slow | It loses its lock and is fenced. No effect on others |
| 2 | One name is hot | `contended` and retry-after for that name only |
| 3 | A tenant exceeds its quota | `overloaded` for that tenant; others unaffected |
| 4 | A leader fails | About 2 s unavailable for one group (a quarter of names); sessions kept by the grace period |
| 5 | A minority of replicas fail or partition | The small side refuses; the majority side serves |
| 6 | Peak load beyond headroom | Gateways shed with retry-after; library backs off with jitter |
| 7 | A whole group loses its majority | A quarter of the names fail closed; protected operations on them stop |
| 8 | Total loss | Start empty, higher epoch, 60 s quiet period; protected operations pause |

At no step does the service hand out a second grant. **Availability is what degrades; safety never does.**

# Stage 7: Requirements that arrive mid-round

For each, say **what changes, what does not, and what it costs.**

**Delta 1: multi-region.** *Changes:* nothing in the design if each region is independent. *The naive answer*,
one group spanning regions, makes every acquire cost a cross-region round trip (30 to 250 ms), which is not a lock
service but an outage with good uptime numbers. *Defensible answers, in order:* (1) region-local lock services over
**region-owned resources** (requires a home region per entity, which is how large systems are actually built); (2)
a global lock used **sparingly** for rare, coarse locks (a global leader, a schema change), on a globally
consistent store; (3) hierarchical: a global lock grants a regional service the right to issue local locks for a
key range for a bounded lease: powerful and complex, a direction rather than an MVP. *Never:* asynchronous
cross-region replication of lock state. It is split brain with extra steps, and there is no reconciliation for a
payment made twice.

**Delta 2: shared (read-write) locks.** *Changes:* the state machine gains a mode and a reader count. *Does not
change:* tokens, the check at the resource, sharding. *Costs:* writer starvation policy, a richer waiter queue, and
more state per name. Add it behind the same API when someone needs it.

**Delta 3: leader election as a first-class feature.** *Changes:* a thin layer: a well-known name whose holder is the
leader, plus a watch so followers learn of changes. *Does not change:* the token, which becomes the **epoch of the
leadership**. The same fencing rule protects whatever the leader writes.

**Delta 4: priorities or weighted fairness.** *Changes:* the waiter queue becomes ordered by priority. *Costs:*
starvation of low priority, and the tail latency of everyone. Push back unless there is a real requirement.

**Delta 5: a watch API.** *Changes:* an ordered, resumable stream of changes per name from a revision. *Costs:* fan-out
to many watchers, which is a load problem of its own; cap watchers per name.

# Stage 8: Failure modes and reliability

| # | Failure | Blast radius | What happens | Detected by |
|---|---|---|---|---|
| F1 | A holder crashes | One name per lock held | Its session expires after one lease; names free | Session-loss rate |
| F2 | A holder pauses and resumes | One holder | Fenced at the resource | `FencedOut` count |
| F3 | A resource cannot check | One caller class | Efficiency lock, proxy or idempotency (challenge 2) | Token coverage |
| F4 | Clock skew or jump | One client | It gives up early (safe) or is fenced (still safe) | Missed-deadline rate |
| F5 | Leader fails | A quarter of names, about 2 s | Election; grace period | Elections per day |
| F5b | Partition | The minority side | The minority refuses | Replica reachability |
| F5c | Total loss of a group | A quarter of names | Fail closed; start empty, higher epoch | Quorum alarms |
| F6 | Duplicate or delayed message | None | Same token returned; expired duplicate refused | Duplicate rate |
| F7 | Load peak or retry storm | All tenants | Gateway sheds; library backs off | Queue depth, 429 rate |
| F8 | Hot name | One name | Bounded queue; `contended` | Waiter depth |
| F9 | Hung but alive holder | One name | Max hold time; `ForceRevoke` | Hold-time tail |
| F10 | Nobody notices | Unbounded | SLIs, canary, audit | The point of challenge 7 |

**One incident, walked through.** *A sustained network flap between zones, 02:10.* The leader of group 3 loses
contact with two followers twice in a minute; each loss triggers an election (about 2 s unavailable for a quarter
of names). Elections per group per day jumps from under 1 to 14. Acquire p99 for names in group 3 climbs. The
**page** names the pair: *elections up, acquire p99 up*, so the on-call looks at network health, not at the
service. Meanwhile libraries on affected names reach their deadlines and fire `LockLost`; applications stop;
nothing is double-granted. When the network recovers, the grace period prevents a mass eviction. The postmortem
action is **not** "make elections faster": it is to confirm election timeouts are not shorter than the network's
worst gap, and to find out why zone links flapped.

# Stage 9: SLOs, observability, cost

**SLIs, measured from outside** (never from inside the service that is being judged): acquire success rate and
latency measured by the **canary** acquiring a real lock continuously; fenced-out rate and **token coverage**
reported by the resources; elections and time-to-leader from the group; hold-time distribution and waiter depth
per name; renewal failure rate **per client** (it finds the pausing service before it causes an incident);
token-gap growth as an anomaly detector for retry storms.

**Dashboard.** One row per guarantee, not per machine: *availability, latency, safety events (fenced-out and
overlap audit), coverage, load and contention, capacity.*

**Cost.** People dominate (Stage 10). Infrastructure is small: four groups of five replicas plus gateways, which
is about a tenth of five-year ownership. Cost levers: replicas cost less than people; sharing a cluster across
tenants costs less than one cluster each, at the price of noisy neighbours (quotas); and the biggest lever is
**not building**: the cheapest correct system is the idempotency key at the resource.

# Stage 10: The EM layer (auxiliary at Staff)

::: why
**Auxiliary.** At Staff you can skip this unless asked. An engineering-manager loop treats it as a main stage. The
video marks the matching chapter AUX.
:::

**Three releases, not one project.** R0 prototype (1 to 1.5 engineer-months), R1 production in one region for one or
two teams (20 to 24 engineer-months: four engineers for five or six months), R2 platform (70 to 140). The best
question is *which of these are we being asked for, and who is the first customer?*

**R1 in detail.** Tech lead 1.0 (protocol correctness, the fencing contract, design reviews); senior backend 1.0
(service, sharding, gateway, admin tools); mid backend 1.0 (client libraries, the first two customers, migration);
SRE 1.0 (half the build is operations); manager 0.3; programme 0.2. Phases: discovery and RFC (3 weeks),
walking skeleton (4), correctness including a **linearizability harness under injected faults** (6), hardening:
sharding, quotas, revoke (6), operations: SLOs, runbooks, a game day (4), first customer in shadow and then cutover
(3).

**Ownership, illustrative.** 24 engineer-months to build, then about 1.75 people for five years (1.75 × 60 = 105):
**about 129 engineer-months, about 11 engineer-years**. Infrastructure is about a tenth. A service with no owner
becomes an incident with no owner.

| Option | To a pilot | Five-year, engineer-months (illustrative) | When it wins |
|---|---|---|---|
| **Don't**: conditional write or idempotency | about 2 weeks per resource | about 10 | The resource supports it. Check first, every time |
| **Buy**: a managed transactional store | about 4 weeks | about 60 | Moderate volume, latency tolerant |
| **Adopt**: coordination store behind our API | about 10 weeks | about 80 | High volume, correctness-critical. **R1 pick** |
| **Build**: custom consensus service | about 6 months, 4 people | about 129 | A unique semantic, or very large scale |

**Never cut:** fencing end to end, the conservative client deadline, the linearizability harness, the runbook and
a qualified on-call. **Cut first:** multi-region, shared modes, first-come fairness, extra-language libraries, the
admin console. **Top risks:** fencing not enforceable at a key resource (descope that caller to an efficiency lock,
in writing); adoption fails (a named pilot before any code: **no named customer means do not build**); scope creep
into a general key-value store, which is what happened to the best-known lock service (written non-goals, quotas in
code); a key person who knows the protocol (pair, design docs, two on-call before launch); a split-brain incident
(consensus, fencing, a harness in the pipeline, game days).

**Staffing.** Small first (design by committee is slow); grow in the middle where the work parallelises; **do not add
people in stabilisation**; share the on-call rotation with a sibling team so four people do not carry a 24/7
pager. **The question to ask before saying yes:** *"What happens if two of you hold this at once, and could the
operation be made idempotent?"*

> "At about eleven engineer-years over five years, building this needs to save more than that somewhere else, or
> protect against a comparable risk. At a company processing payments at scale that is easy to justify. Almost
> anywhere else the answer is adopt a coordination store behind our own API, and revisit in a year with data. I
> would write the buy-versus-build memo before any code, with the first customer's commitment in it."

# Stage 11: The close

Four sentences, in this order.

> "**What:** a small consensus-replicated store of named leases that issues a token with every grant, behind a
> client library that stops the application when its lease is lost. **Trade-off:** safety is unconditional and
> availability is what degrades, and a correctness lock is only as safe as the check at the resource.
> **Risk:** a resource that cannot check, so I classify every caller first and prefer idempotency to a lock.
> **Next:** a named pilot customer, then R1 on a coordination store behind our API, then the linearizability
> harness and a game day before launch."

*The lock service decides who should be working. The resource decides who is allowed to write. Everything built
here is there so those two answers can disagree safely.*

# Stage 12: Self-check after a simulator run

Score yourself honestly; the simulator's debrief uses similar dimensions.

| Signal | Weak | Strong | Exceptional (aim here) |
|---|---|---|---|
| Requirements | A key in a cache with an expiry | Asks what a double hold costs; separates efficiency from correctness | Classifies callers; states what the service cannot promise |
| Estimates | A table nobody reads again | The concurrency ceiling and the group count, each changing a decision | Notices attempts are not grants; renewals dominated by long holds |
| Correctness | "Tune the TTL" | A token at the resource; monotonic clocks; fail closed | The stale-first-write case; one row, one name; max hold time |
| Depth | "Uses Raft" | Why the token is the log index; why expiry is a command | Why a restore breaks tokens; leader-lease read caveats; the phantom grant |
| Trade-offs | Picks a product | An options matrix with the failure that rules each out | Picks, says what the pick gives up, and checks "no lock" first |
| Operations | CPU and uptime | Fenced-out writes, symptom pairs, error budget | Token coverage; the audit; a DR runbook with a quiet period |
| Leadership | Builds the biggest thing | Names a first customer, never-cut list, releases | "No named customer means do not build" |

**Common traps.** A cache key with an expiry presented as a correctness lock. "Tune the lease" as the answer to a
pause. No token, or a token nobody checks. Timestamps compared across machines. Failing open without saying so. A
beautiful consensus group and no word about the resource. Never asking whether a lock is needed. Offering atomic
multi-lock. Restoring an old snapshot. Hiding the token in a thread-local. Checking the lease and calling the
check atomic.

\newpage

# Part III: The internals, for when the interviewer digs

One appendix per tool the design names, in plain words, one level below Stage 5. Read these after the round, to
rebuild the intuition, not during it.

## Appendix A: Consensus in plain words

**What problem it solves.** Several machines must agree on one ordered list of entries, even when some of them
crash and the network drops or delays messages. The list is the **log**. If every replica applies the same log in
the same order through a deterministic state machine, they all hold the same state. A lock service is a tiny state
machine: `held` and `waiters` maps changed by `Acquire`, `Release`, `Expire`, `Revoke`.

**The pieces (Raft-style).**

- **Roles and terms.** A node is a follower, candidate or leader. Time is divided into **terms**, numbered
  upward. Each term has at most one leader. A node that sees a higher term immediately steps down and adopts it.
- **Election.** A follower that hears no leader for a randomised timeout (say 150 to 300 ms of the group's own
  clock; the exact range is a tuning choice) becomes a candidate, increments the term, and asks for votes. A node
  votes at most once per term, and only for a candidate whose log is at least as up to date as its own. A majority
  of votes wins. Randomising the timeout makes split votes rare.
- **Replication.** The leader appends a client command to its log and sends it to followers. When a **majority**
  holds the entry, the leader marks it **committed**, applies it, and answers. Followers learn the commit point and
  apply too.
- **Why committed entries survive.** A candidate needs a majority of votes; the voters refuse any candidate whose
  log is behind theirs. Any majority of the old term overlaps any majority of the new election in at least one node
  holding every committed entry, so a winner always has them.
- **Reads.** A read served from the leader's memory could be stale if a new leader exists. Options: put the read
  through the log (safe, slow); confirm leadership with a round of heartbeats first (a **read index**); or serve
  under a **leader lease**, where a majority promised not to elect another leader for a short time. The last relies
  on bounded clock drift, which is why a "held by X" answer is not usable for correctness.
- **Snapshots and recovery.** The log would grow forever, so the leader periodically saves a **snapshot** of the
  state and truncates the log before it. A new or slow replica receives the snapshot, then the tail. A restart loads
  the newest snapshot and replays the log tail: with about 1 MB of state, that is seconds.

**What consensus does not give you.** It does not make the *client* safe. A committed grant is a fact about the
record. Whether the holder still acts on it is a different matter, and that is the pause problem.

**Costs to say aloud.** Every write needs a quorum round trip and a disk sync on a majority; throughput of one
group is bounded by the leader's disk and network; no majority means no service. The usual groups are 3 or 5
nodes: 5 tolerates two failures and costs more per write than 3.

## Appendix B: Leases, clocks and why time is not a shared variable

A **lease** exists because failure detection is impossible in an asynchronous network: you cannot tell a dead
client from a slow one. So rather than detect death, the grant is made **self-terminating**.

| Kind of time | What it is | Use it for |
|---|---|---|
| **Wall clock** | Time of day. Can jump forwards or backwards: synchronisation steps, leap seconds, virtual-machine migration, an operator setting it by hand | Logs and humans. **Never** lease arithmetic |
| **Monotonic clock** | Elapsed time since an arbitrary point on one machine. Never goes backwards. Meaningless across machines | Measuring durations |
| **Logical order** | Log index, term. Says nothing about duration. Totally ordered | The fencing token and every correctness decision |

**The client-safe-lease argument.** The server grants a lease of length L starting when it commits. The client
treats its lease as ending at *L minus a margin* on its own monotonic clock, measured from when it **sent** the
request, because the server's clock started later. So in the region of ambiguity, **the client stops first**. This
holds if both clocks run at nearly the same *rate*; it does not depend on their agreeing what time it is. The
margin covers round trips and scheduling. Drift is rarely the issue: 200 parts per million over 10 s is 2 ms.

**Bounded-uncertainty clocks.** A hardware-assisted time service returns an interval `[earliest, latest]` with
bounded error. Systems built on it can *wait out* the uncertainty before acting, which turns a lease's safety
argument into a proof. Without such a service, which is almost everyone, "NTP is probably fine" is a liveness
assumption pretending to be a safety one. This is why the **token** carries the safety argument, not the clock.

## Appendix C: The features a coordination store gives you

Described generically; ZooKeeper, etcd and Consul differ in detail but share the idea.

- **Leases with keep-alive.** Create a lease with a TTL; attach keys to it; a keep-alive stream renews it; when it
  expires, the attached keys are deleted. A session in our design is a lease.
- **Transactions with a condition.** *If key K does not exist, create it and attach my lease; else return the
  current value.* This is the lock acquire. It is atomic.
- **A revision on every change.** A cluster-wide increasing number, plus per-key *create revision* and *modify
  revision*. The create revision of the lock key is a fencing token for free.
- **Watches.** Subscribe to a key or a prefix, from a revision, and receive an ordered stream of changes. Waiters
  use a watch on the predecessor in a queue so one release wakes exactly one waiter.
- **The queue recipe.** Each waiter creates an *ephemeral, sequential* node under the lock's path. The lowest
  sequence number holds the lock; everyone else watches only the node just ahead of them. This gives first-come
  fairness and avoids a herd, and it is the same idea as our directed hand-off.

**Where it stops.** Write throughput of one cluster is in the tens of thousands a second, and very large numbers of
keys, long watch fan-out, and heavy sessions strain it. That is why we shard across clusters (challenge 5) and why
semantics such as priorities and shared modes belong in our own API if they are ever needed.

## Appendix D: Conditional writes in storage systems

The fencing check is one operation in many storage systems, under different names.

| Store | The check | The token is |
|---|---|---|
| A relational database | `UPDATE ... WHERE fence <= :token` (or a version column with optimistic concurrency) | The version or fence column |
| An object store | Write only if the object's *generation* or *ETag* matches | The generation or ETag |
| A document store | Update with a precondition on the document's update time | The update time |
| A transactional key-value store | Read-modify-write inside a transaction | The commit version |
| A message broker with ordering keys | Serialise work per key instead of locking | The sequence within the key |
| A cluster scheduler's lease object | A lease with a resource version | The resource version |

**Why this matters in an interview.** Before designing a lock service, check whether the protected resource
supports a conditional write. If it does, the resource enforces exclusion by itself and the lock becomes an
*optimisation to avoid wasted work*. That collapses the availability requirement from four nines to something much
cheaper, and removes a whole system from the critical path.

## Appendix E: Idempotency keys

An **idempotency key** is a caller-chosen identifier sent with an operation. The resource records the key and the
result; a repeat with the same key returns the recorded result and does nothing new. It makes duplicate execution
harmless, so a lock shrinks to "avoid wasting compute", which is an efficiency lock, and an efficiency lock can be
one cache node.

**Costs.** The resource must keep records at least as long as the longest possible duplicate (maximum lease plus
maximum pause plus the retry horizon). It does not help operations that are inherently non-idempotent (sending a
physical parcel, calling a partner API that has no idempotency key). It moves state into the resource rather than
eliminating it. It is still, very often, the cheapest correct system.

## Appendix F: Testing a lock service: linearizability and fault injection

A lock service is a claim until it has been tested under faults. The tests that matter:

- **A linearizability checker.** Record every operation's start, end and result from many concurrent clients, then
  check that the history is consistent with *one* sequential order in which each operation took effect between its
  start and end. For a lock, the checker also asserts mutual exclusion directly: no two grants of the same name
  overlap in the server's durations.
- **Fault injection.** Kill leaders, partition replicas, pause processes (with a stop signal, which is the pause
  problem made real), skew and step clocks, drop and duplicate and delay messages, fill disks. Run the checker
  throughout.
- **Deterministic simulation.** Run the whole system in one process with a simulated network and clock, so any
  failing schedule can be replayed exactly. It is the best investment for a replicated state machine.
- **Game days.** Rehearse the disaster-recovery runbook (start empty, bump the epoch, wait out the quiet period)
  with the people who would be on call.

# One-page cheat card

**The insight:** the lock service says who *should* be working; only the resource says who is *allowed* to write.
Lease for liveness, consensus for order, a token checked at the resource for safety. Ask first whether a lock is
needed at all.

**Numbers to compute:** (1) 5,000 names, one holder each, so at most 5,000 held; at 0.5 s mean hold, at most 10,000
grants a second: *attempts are not grants*. (2) State is about 1 MB: shard for throughput and blast radius.
(3) 30,000 writes a second at peak against a 15,000 ceiling: 30,000 ÷ 7,500 = **4 groups**, 64 slots. (4) 99.99% is
259 s a month; at 2 s an election, about 130 elections a group.

**Acquire:** gateway routes by `hash(name)` to the leader; entry commits on a majority; token = log index; library
deadline = send time + 0.7 × lease on the monotonic clock.

**The check:** `UPDATE ... WHERE fence <= :token`. Equal passes; smaller is rejected. Explicit argument, never a
thread-local. One row, one lock name.

**The pause:** the lock does not make the write safe; the token does. A stale write that arrives *before* the new
holder's first write needs a **claim first** or a single conditional write.

**No check at the resource:** ask (idempotent?), then conditional write, then a validating proxy, then an honest
efficiency lock.

**Time:** durations on monotonic clocks; the client stops first; the margin is for round trips, not drift; never a
timestamp as a token.

**Partition:** majority commits, minority refuses. Safety unconditional. **Disaster:** start empty, higher epoch,
wait one maximum lease. Never restore an old snapshot.

**Peak:** replicas do not add write throughput. Shard by name, shed at the gateway, jitter. Moving a slot: freeze,
drain, bump the epoch.

**Hot name:** a lock serialises; bounded queue, directed hand-off, explicit `contended`. Several locks: push back;
canonical order and bounded leases.

**Observe:** alert on any fenced-out write; token coverage; symptom pairs; canary; audit the grant log. Zero
fenced-out is not proof of safety.

**Cost:** R0 1 to 1.5, R1 20 to 24, R2 70 to 140 engineer-months; about 11 engineer-years over five years for R1.
Don't (check first), buy, adopt (the R1 pick), or build. No named customer: do not build.

**The close:** *The lock service decides who should be working. The resource decides who is allowed to write.*
