- [x] outline approved  - [x] design  - [x] diagrams  - [x] slides  - [x] script  - [x] video  - [x] publish

# SD-24 · Distributed lock / coordination service — reference-solution video outline

Target level: staff (manager layer AUX) · Target length: 86.5 min (≤ 90) · Word budget: 11,505 (≈ minutes × 133)

Generic content only: no employer, cloud vendor or currency in anything that ships. Costs are in engineer-months with an illustrative loading.

## Thesis and definition

- **Thesis** (one sentence, key-line voice): *A lock service can say who should be working; only the resource can say who is
  allowed to write. So: a lease for liveness, consensus for the order, a fencing token checked at the resource for safety, and
  first the question of whether this caller needs a lock at all.*
- **Definition to say aloud**: *A distributed lock service is a small, consensus-replicated store of named leases. It gives one
  holder at a time permission to act on a name, for a bounded time, together with a number that orders every grant on that name.*
  Load-bearing clauses: **consensus-replicated** (a failover must not forget a grant), **named** (locks are independent per name,
  which is what lets it shard), **bounded time** (we cannot tell a dead holder from a slow one), **a number that orders** (the
  fencing token; the part the resource needs).
- **Hook** (why it is harder than it looks): The lock service can be perfectly correct at every step and mutual exclusion is still
  violated. A holder pauses for fifteen seconds, its lease expires, a second holder is granted, the first one wakes up and writes.
  No component misbehaved; the lock service's idea of "who holds it" and the resource's idea of "who may write" are two different
  things and nothing connects them. The question tests whether you notice the gap, not whether you can draw a consensus group.

## 0 · What this question grades

| Axis | Weak signal | Strong signal |
|---|---|---|
| Requirements | Starts with a key in a cache and an expiry; never asks what a double hold costs | Asks what breaks if two parties hold it and separates **efficiency** locks from **correctness** locks before drawing a box |
| Correctness | "Tune the TTL"; checks the lease and then writes; trusts wall-clock timestamps | Names the pause scenario unprompted, puts a monotonic token **at the resource**, measures durations on monotonic clocks, states fail-closed |
| Trade-offs | Picks a product and defends it | Options matrix with the failure that rules each row out; picks, and says what the pick gives up; asks first whether a lock is needed |
| Depth | Stops at "uses Raft" | Two levels down: why the token is the log index, why expiry is a replicated command, what a new leader assumes about live sessions, why restore-from-backup breaks tokens |
| Operations | Monitors CPU and uptime | Symptom pairs, a fenced-out-write alert, error-budget arithmetic for elections, a disaster-recovery plan that keeps tokens monotonic, and a build/adopt/don't decision with people and months |

## 1 · Requirements and scope

- **Clarifying questions and the interviewer's answers** (asked aloud, six):
  1. *Who calls this, and for what?* — Internal teams. Roughly: background workers electing a leader, per-entity mutual exclusion
     before a write, and some "run this job once" schedulers.
  2. *What happens if two holders act at once?* — "Depends on the team. For some it corrupts records; for some it wastes an hour of
     compute. I'd like you to tell me how you'd find out." (This seeds the efficiency / correctness split and challenge 2.)
  3. *Scale?* — About 10,000 acquisition attempts a second, around 5,000 lock names, holds from 100 ms to 30 s, default lease 10 s.
  4. *Latency, availability, failure?* — p99 acquisition under 20 ms; survive the loss of a minority of nodes; one region, three
     zones; multi-region is a later question.
  5. *What are the protected resources?* — Mostly SQL databases and an object store; a few call partner HTTP APIs. Callers are JVM
     services; "assume stop-the-world pauses up to fifteen seconds in the tail. That is a fact, not a tuning problem."
  6. *Do callers ever need several locks at once, or shared/read locks, or strict FIFO?* — Several at once: "some do, tell me what
     you'd say." Shared mode: no. FIFO: not required.
- **Functional requirements** (each one gets a numbered flow later):
  - FR1 · **Acquire** an exclusive lock on a name, with a bounded wait (try-once is wait = 0).
  - FR2 · **Hold and renew**: keep the lease alive while working; learn promptly when it is lost.
  - FR3 · **Release**, and have a dead holder's locks freed automatically.
  - FR4 · **Fence**: every grant carries a strictly increasing token the caller can hand to the resource.
  - FR5 · **Inspect and break glass**: operators can see who holds a name and force-revoke it, audited.
- **Non-functional requirements, with numbers** (all initial targets, not measurements):
  - Acquisition p99 < 20 ms; acquire availability 99.99 % (≈ 4.3 min a month).
  - Survive loss of any minority of replicas (2 of 5) with no manual action.
  - Default lease 10 s, cap 60 s; a dead holder's name is free again within one lease.
  - **Fail closed**: if the service cannot decide, the protected operation does not proceed.
  - Tokens strictly increase per name and never go backwards, including after a disaster-recovery rebuild.
- **IN scope / OUT of scope**:
  - IN: exclusive named leases, sessions, tokens, bounded wait queue, operator tools, one region, quotas per tenant.
  - OUT, on purpose: shared/read-write modes (add later behind the same API); atomic multi-name acquisition (needs a cross-group
    transaction, and we push back on it, see challenge 6); cross-region consensus (one slide: region-local services over
    region-owned resources); a general-purpose key-value store (a written non-goal).
- **"The core is 4 things"**: a *lease* that frees itself, a *consensus-replicated* record of who holds it, a *token* that orders
  grants, and a *check at the resource*.

## 2 · Estimates

Every number is arithmetic from the stated inputs, and carries a label.

| Number | Arithmetic | Label | Decision it drives |
|---|---|---|---|
| Attempts, average and peak | 10,000/s given; peak factor 3 (top-of-hour storms) → 30,000/s | given; peak factor illustrative | Size for the peak, not the average |
| Concurrency ceiling | One holder per name, ~5,000 names → ≤ 5,000 held at once. Mean hold 0.5 s → grants ≤ 5,000 / 0.5 = 10,000/s *only if every name is always held* | derived | Many attempts must fail or wait: the lock, not the service, is the limit. Drives the bounded-wait API and challenge 6 |
| Grants, and held at once | Assume 40 % of attempts succeed → 4,000 grants/s. Held at once (Little's law, L = λ·W): 4,000 × 0.5 s = 2,000 locks | illustrative | State is tiny, see next row |
| State size | ~5,000 entries (held + waiters) × ~200 B ≈ 1 MB | illustrative | Whole state in memory, snapshot in milliseconds: shard for **throughput and blast radius**, never for capacity |
| Committed writes | Grant + release = 2 × 4,000 = 8,000/s average; ×3 peak = 24,000/s; plus waiter enqueues and expiries ≈ 30,000/s all-in | illustrative | Compare with one group's ceiling, next row |
| One group's ceiling | ~15,000 committed writes/s with batched fsync on SSD | initial target, **to be measured** | Peak 30,000 / (15,000 × 0.5 headroom) = **4 groups**, 64 hash slots to allow later moves |
| Renewal traffic | Only holds longer than TTL/3 = 3.3 s ever renew. Say 2 % of grants are long (mean 20 s): 4,000 × 2 % = 80/s × 20 s = 1,600 long-held locks. Per-lock renewal: 1,600 / 3.3 s ≈ 480/s. Per-session (400 client processes): 400 / 3.3 s ≈ 120/s | illustrative | Sessions: one heartbeat per client, not per lock; a dead client is one expiry, not fifty |
| Latency budget (p99 20 ms) | 2 ms network in + 3 ms batch wait + 4 ms leader fsync + 5 ms follower round trip and fsync + 1 ms apply and reply + 2 ms network out = 17 ms, **3 ms spare** | initial target | Quorum in one region, three zones. A cross-region quorum (30–250 ms) cannot meet it |
| Per-key ceiling | Max grants per name = 1 / hold: 100 ms → 10/s; 0.5 s → 2/s; 30 s → 0.03/s. A name at 40 attempts/s with 100 ms holds is 4× over | derived | Hot-key policy: bounded queue, explicit rejection, and go back to the requirement |
| Pause against lease | TTL 10 s against a 15 s pause: the pause wins. Raise TTL to 60 s: a 70 s migration still wins, and every crash now stalls its name for 60 s | given pause; illustrative | **Tuning the TTL cannot fix this.** Fencing can |
| Clock margin | Worst drift 200 ppm × 10 s = 2 ms. Client gives up at 0.7 × TTL = 7 s after sending; server waits the full 10 s: 3 s of gap | illustrative | Drift is not the risk; pauses and round trips are. The margin is cheap, the token is the backstop |
| Election budget | 99.99 % of a 30-day month = 259 s ≈ 4.3 min. One election ≈ 2 s per group → ~130 elections a group a month burns it | initial target | Elections per group per day is an SLI, challenge 7 |
| Token space | 16-bit epoch + 48-bit log index. 2⁴⁸ ≈ 2.8 × 10¹⁴ entries ÷ 15,000/s ≈ 1.9 × 10¹⁰ s ≈ 600 years per epoch | derived | Room for 65,536 rebuilds; challenge 4 |

## 3 · Theory

1. **Is / is not.**
   - Is: replicated leases on names, giving one holder at a time, for bounded time, plus an ordering number.
   - Is not a **mutex**: a mutex lives in shared memory and can stop the holder; a distributed lock cannot reach into a paused
     process. Is not a **queue**: no payload, no work ordering; if the caller wants "one at a time per entity, in order", a
     partitioned single-writer is the right tool. Is not a **transaction**: it protects nothing by itself; the resource must
     participate. Leader election is a *use* of it, not another thing.
   - The classification that runs through the video: **efficiency lock** (avoid duplicate work; a double hold costs money) versus
     **correctness lock** (a double hold corrupts data).
2. **Safety (must never happen):** two parties both act as the holder on the same name and both effects take hold at the resource.
   **Liveness (must eventually happen):** a free name is granted; a name whose holder died becomes free within one lease; a waiter
   is served or told no within its wait budget. Each later fix is tagged with the property it serves.
   - FLP honesty, one slide: in an asynchronous network with a failure, you cannot have both unconditionally. We keep safety
     unconditional and give up liveness on the minority side of a partition.
3. **Central tension:** you cannot tell a dead holder from a slow one. So **recovery speed against false expiry**, per workflow.
   Picture: one timeline with a lease bar, a pause bar, a second holder bar, and a TTL slider under it: short TTL means fast
   recovery and more false expiries, long TTL means slow recovery and fewer, and **no TTL removes the pause**. The same picture
   later hosts challenge 1.
4. **Mechanisms** (7). Form per slide: property → how → failure ruled out → cost.

   | Mechanism | Protects | Rules out | Costs |
   |---|---|---|---|
   | **M1 Lease with a TTL** | Liveness | A lock held forever by a dead holder; manual cleanup | A slow holder can be expired while alive; a crash stalls its name up to one TTL |
   | **M2 Consensus-replicated record** (majority commit, terms) | Safety of the grant record | Split brain; a failover that forgets a grant | A quorum round trip on every write; no majority means no service; a cluster to run |
   | **M3 Fencing token** (strictly increasing per name, checked at the resource) | Safety at the resource | A paused holder's stale write landing after a newer holder's | The resource must check; one number per protected row; orders writes, does not make multi-step reads consistent |
   | **M4 Monotonic-clock leases, conservative client deadline** | Safety of the lease arithmetic | Wall-clock jumps and skew making the client believe it holds a lease it lost | The client gives up early (30 % of the lease wasted); still assumes bounded drift |
   | **M5 Sessions** (one heartbeat covers many locks) | Liveness and throughput | Per-lock renewal storms; N separate expiries for one dead client | Coarser failure unit: one missed heartbeat drops every lock of that client |
   | **M6 Deterministic replicated state machine** (time carried in the log entry; expiry is a command) | Safety of the replicas | Replicas that disagree about who holds a lock; a follower expiring a lease on its own clock | Expiry waits for the leader's timer; a new leader must re-derive pending expiries |
   | **M7 Bounded wait with directed hand-off** | Liveness under contention | Thundering herd on release; an unbounded queue; polling that burns consensus | Queue state in the replicated machine; FIFO adds tail latency |

5. **Options matrix** (rows = approaches; columns = deciding properties; last column = fails when).

   | Approach | Safe without fencing? | Token | Throughput | Ops burden | Fails when |
   |---|---|---|---|---|---|
   | A · Single cache node, set-if-absent with expiry | No | Bolt-on counter, not atomic with the grant | Very high | Very low | The primary fails before replicating the grant: the new primary has no record and grants it again |
   | B · Quorum of independent cache nodes | Disputed | None | High | Medium | A pause between acquiring and using; one node's clock jumps and its key expires early; no token to reject a stale holder |
   | C · Relational row, conditional update or row lock | Yes, with synchronous commit | Version column | Low to medium | Very low | Above a few thousand grants/s, on a hot row, or with asynchronous failover; a row lock tied to a connection has no lease at all |
   | **D · Consensus coordination store** (ZooKeeper / etcd / Consul class): lease + compare-and-set + revision | Yes | Store revision (log index) | 10–30 k writes/s a cluster | Medium | Load beyond one cluster (then shard); needs semantics it cannot express (priorities, shared modes); cross-region latency |
   | E · Custom consensus lock service | Yes | Log index | High, sharded | Very high | You cannot staff it: tens of engineer-months to build, a standing team to run |
   | F · No lock: conditional write or idempotency key at the resource | Yes, at the resource | The resource's own version | Not applicable | Lowest | The operation is not idempotent and the resource has no conditional write (a partner API) |

   **Pick: D**, behind our own API and client library, **after asking whether F applies**; E stays a swap, not a start. Rows A, B, C, E
   and F stay on screen, greyed, with their failures.
   **Gives up:** one cluster's write ceiling (so we shard), generic fairness/priority/shared modes, cross-region reach, and the
   operating burden of a consensus cluster. The pick of D over F buys one place to enforce rules, and costs a service to run.
6. **Failure catalogue** (becomes the challenge list):
   - F1 holder crashes → lease (M1), no challenge needed, covered in flows
   - F2 holder pauses and resumes → **C1**
   - F3 resource cannot check tokens; or no lock needed → **C2**
   - F4 clock skew, jumps, drift → **C3**
   - F5 leader fails, partition, whole group lost → **C4**
   - F6 duplicate acquire, stale release, delayed message → designed out in the API (release takes the token; acquire carries a request id and returns the same token; old terms rejected): shown on the API slides, not a challenge
   - F7 load peak, renewal storm, retry storm → **C5**
   - F8 hot key, herd, deadlock across several locks → **C6**
   - F9 holder hung but alive → bounded lease, force revoke (FR5), flows
   - F10 nobody notices → **C7**

## 4 · API and entities

| API | Serves | Reads / writes | Wire-format notes |
|---|---|---|---|
| `OpenSession(ttl)` → `{sessionId, epoch}` | FR2 | writes **Session** | Client chooses ttl ≤ 60 s; server returns the grant time on its own clock *for logging only* |
| `Heartbeat(sessionId)` (stream) | FR2 | touches **Session** liveness (volatile under leader lease) | Response carries nothing the client must trust except "ok"; the client measures its own deadline from send time |
| `Acquire(name, sessionId, requestId, maxWait)` → `granted{token, ttlMs}` / `queued{pos}` / `timeout` / `contended` | FR1, FR4 | writes **Lock** and **Waiter** | `requestId` makes retries idempotent: a duplicate returns the **same** token. `maxWait = 0` is try-once. No indefinite wait exists |
| `Release(name, token)` | FR3 | writes **Lock** | By token, not by name: releasing someone else's lock is not expressible. Compare-and-delete |
| `Inspect(name)` | FR5 | reads **Lock**, **Waiter** | Never used for correctness decisions; documented as such |
| `ForceRevoke(name, reason, operator)` | FR5 | writes **Lock**, **AuditEvent** | Audited and alerting; the next grant gets a higher token, so the revoked holder is fenced like any other |
| *Resource contract:* `Write(..., fencingToken)` | FR4 | resource's own row | Reject if the token is **less than** the highest accepted for that row; equal is allowed (same holder, several writes). Token travels as an explicit argument, never a thread-local |

**Conceptual model** (Chen view): **Tenant** 1—N **LockName**; **Session** 1—N **Lock** (a grant of one name to one session);
**LockName** 1—N **Waiter**; every grant carries one **Token**; **AuditEvent** records revocations and DR rebuilds; a
**Resource** row stores the highest token it has accepted.

**Physical** (inside the replicated state machine, in memory with log and snapshot on disk):

- `held[name] → {owner, sessionId, token, expiresAt}`; key = `hash(namespace + name)` → slot (0–63) → group.
- `waiters[name] → FIFO of {owner, sessionId, requestId, enqueuedAt}`, depth-capped.
- `sessions[sessionId] → {owner, ttl, names}`; last-heartbeat time is volatile, not in the log.
- Durable outside the group: **epoch** counter (16 bits) and per-slot **floor** token for moves. Token = `epoch << 48 | logIndex`.
- At the resource: `fence BIGINT` on each protected row (or the object's generation, or the proxy's table).

## 5 · High-level design

| Version | Adds | Objection it answers | Objection it leaves |
|---|---|---|---|
| V1 | SDK + one lock server holding a map of `name → owner, expiry` in memory; leases with a TTL; acquire, renew, release | (none: simplest thing that works) | One box: if it restarts, it forgets who holds what and re-grants; it is also a single point of failure |
| V2 | Replace the server with a **consensus group** of 5 (leader, followers, majority commit, terms); token = log index of the grant; expiry as a replicated command | "A restart or failover forgets a grant and hands it out twice" | Every client hand-rolls renewal; callers do not know they lost the lock; the service is not reachable safely (auth, quotas, routing to the leader) |
| V3 | **Client SDK with sessions**, heartbeat, a monotonic local deadline and a `LockLost` callback; a **stateless gateway** (auth, quota, route to the leader); the token returned in the handle and passed to the resource (resource drawn grey, unchanged) | "Clients cannot tell they lost the lock, and renewal is chatty" | **Nothing checks the token.** A paused holder still writes. This is challenge 1 |

Baseline spine, left to right: **Client app + SDK → Gateway → Consensus group (leader + 4 followers) →** and, along the bottom,
**Client app → Resource (grey)** carrying the token. Boxes that appear only in a challenge carry a tag: `ch1` fence check at the
resource; `ch2` validating proxy; `ch4` epoch store; `ch5` shard groups, admission control; `ch6` waiter queue; `ch7` metrics
and canary. Colours by role as in GUIDELINES §7.

Flows, one per functional requirement (numbered arrows, narration uses the numbers):

- **FR1 Acquire:** 1 SDK `Acquire(name, requestId, maxWait)` · 2 gateway authenticates, applies the tenant quota, hashes the name
  to a slot · 3 leader appends `Acquire` · 4 replicate to followers · 5 majority acknowledges, entry commits · 6 apply: free →
  grant, token = log index; held → enqueue or `contended` · 7 response `{token, ttl}` · 8 SDK sets deadline = *send time* + 0.7·TTL
  on its monotonic clock.
- **FR2 Hold and renew:** 1 heartbeat per session every TTL/3 · 2 leader (under its own leader lease) records liveness in memory ·
  3 ack · 4 SDK extends its local deadline from the *send* time · 5 on two missed beats and a passed deadline → `LockLost` and the
  application stops.
- **FR3 Release and expiry:** 1 `Release(name, token)` · 2 commit · 3 apply compares the token, frees, **hands off to the head
  waiter in the same step** · 4 for a dead client: no heartbeat for one TTL → 5 leader proposes `SessionExpired` · 6 all that
  session's names freed in one command.
- **FR4 Fence:** 1 app writes to the resource with the token · 2 resource compares with its stored maximum · 3a accept and store
  if not less · 3b reject `FencedOut` if less · 4 the rejection is logged with both tokens and alerts.
- **FR5 Inspect and revoke:** 1 operator calls `ForceRevoke(name, reason)` · 2 gateway checks operator identity · 3 commit
  `Revoke` + audit entry · 4 holder is told on next heartbeat; its next write is fenced because the next grant has a higher token.

C4 and sequence views that follow: context; container (SDK, gateway, group, resource, operator console); sequences for acquire,
heartbeat-and-loss, release-with-hand-off, and the resource check. Challenge sequences are added in each challenge.

## 6 · Bridge and challenge map

*It works. Where does it break first?* The carried baseline with seven attack points marked: pause (C1), resource without a check
(C2), clocks (C3), leader and partition (C4), peak load (C5), hot key and several locks (C6), the 3 a.m. blind spot (C7). Spoken
line: "every fix creates the next question."

## 7 · Challenges

Seven, ordered so that each fix creates the next question. Correctness: C1, C2, C3. Failure recovery: C4. Overload: C5, C6.
Observability: C7. The crux (a lock service cannot make a system safe on its own) gets two: C1 and C2.

### Challenge 1 · The paused holder  *(crux, part 1; correctness)*

- Q (interviewer): "A holder is stopped by a fifteen-second garbage-collection pause. Its lease expires, another process acquires,
  and then the first one wakes up. Both now write. What saves you?"
- Naive answer: "Make the lease longer, and check that the lease is still valid just before every write."
- Case (IDs, times, numbers): TTL 10 s. t = 0.0 A acquires `invoice-17`, token 41 · t = 0.2 A reads the invoice · t = 0.3 A checks
  "still held: yes", then pauses · **t = 10.0 lease expires** · t = 10.4 B acquires, token 42 · t = 10.5 B writes · **t = 15.3 A
  resumes and writes**. A 60 s TTL only moves the failure to a 70 s pause, and every real crash now stalls its name for a minute.
- Break (which box): the arrow from the client to the resource, dashed red: the lock service did everything right and the
  resource accepted both writes.
- Fix (mechanism) · sequence? code?: **Fencing token checked at the resource.** The resource keeps the highest token it has
  accepted for the row and rejects any write with a smaller one: `UPDATE invoice SET …, fence = :t WHERE id = :id AND fence <= :t`.
  Sequence: A (41) pauses; B (42) writes, fence = 42; A wakes, writes 41, rejected `FencedOut`. Code: that one statement, and the
  object-store equivalent (generation match).
- Why it works (property): **Safety, enforced where the effect happens.** The lock service's job shrinks to issuing an order, which
  consensus does well; the check-and-write is atomic at the resource, which the client could never make it. Precision statement:
  equal tokens are allowed (one holder, several writes); only smaller is rejected.
- "What if the fix fails?": "A's stale write arrives **before** B's first write. The resource has only seen 41, so it accepts A.
  Then B, who read the old row, writes 42 on top. Is that fenced?"
- Second fix or honest limit: No, and that is the honest limit: fencing rejects stale writes *after* a newer token has been seen.
  Two ways to close it: make B's critical section one conditional write against the version it read (the token is the version), or
  have B **claim** its token at the resource before it reads, so any later write by 41 is rejected. Cost: one extra round trip, or a
  critical section that fits in one conditional write.
- If asked, I'd say: "A lease cannot guarantee exclusion at the resource, because the holder cannot know it still holds the lock
  when its write lands. So the grant carries a monotonically increasing token, and the resource rejects anything older than what
  it has already accepted. Safety lives at the resource. The lock service only has to give a correct order."

### Challenge 2 · The resource cannot check  *(crux, part 2; correctness and design)*

- Q (interviewer): "The thing you are protecting is a partner's HTTP API, or a cron job. There is no conditional write. Now what?"
- Naive answer: "Use a long lease, trust the client library, and call it correct."
- Case (IDs, times, numbers): 100 callers surveyed (illustrative): 55 only avoid duplicate work, 30 write to a store with a
  conditional write or version column, 10 call something that has neither, 5 are truly non-idempotent. A payment call with no
  idempotency key, paused after the lock check, is charged twice.
- Break (which box): the grey resource box, outlined red: the fence has nowhere to live.
- Fix (mechanism) · sequence? code?: **Ask first; then pick the cheapest place to enforce.** In order: (1) is the operation
  idempotent? Then an idempotency key `lockName + jobInstance` makes a double hold harmless and the lock is only an *efficiency* tool;
  (2) does the resource have a conditional write? Use its version as the token; (3) otherwise a **validating proxy** in front of the
  resource that stores the highest token per resource in a consistent store and forwards only fresh ones; (4) if none fits, ship it
  as an efficiency lock **and say so in the contract**. Sequence for the proxy path.
- Why it works (property): **Matching the guarantee to the cost of a double hold.** Each option moves safety to the place that can
  atomically check and act. Most lock requests are idempotency problems in disguise.
- "What if the fix fails?": "The proxy is now a single point of failure and a new thing that must itself be consistent. And your
  idempotency records: how long do you keep them?"
- Second fix or honest limit: The proxy fails closed, keeps its table in a consensus-backed store, and is scoped per resource class.
  Idempotency records live at least as long as *max lease + max pause + retry horizon* (illustrative: 24 h for a 60 s lease).
  Honest limit: a non-idempotent call to a system with no check cannot be made safe by any lock; the answer is to change the
  contract or accept the risk with a named owner.
- If asked, I'd say: "Before I build a lock for a team I ask what a double hold costs and whether the operation can be made
  idempotent. If the resource supports a conditional write, the resource enforces exclusion and the lock is an optimisation. I only
  claim a correctness lock where something downstream checks the token."

### Challenge 3 · Time  *(correctness)*

- Q (interviewer): "A client's clock is five seconds slow. Or time is stepped back eight seconds in the middle of a lease. What
  happens to the lease?"
- Naive answer: "The server returns an expiry timestamp and the client compares it with its own clock."
- Case (IDs, times, numbers): Server grants at server time 10:00:00, expiry 10:00:10. Client clock is 5 s **slow**: it believes it
  has until its own 10:00:10, which is server time 10:00:15. **From 10:00:10 to 10:00:15 two holders both believe they hold.** A fast
  clock is merely wasteful. An 8 s step back does the same to a perfectly good client. (A timestamp as the fencing token fails
  the same way: clocks go backwards.)
- Break (which box): the SDK's deadline logic, outlined dashed red.
- Fix (mechanism) · sequence? code?: **Durations, not timestamps.** The client measures `deadline = sendTime + 0.7·TTL` on its
  **monotonic** clock, taken when the request was *sent*. The server counts the lease from its own commit on its own monotonic clock.
  No timestamp is compared across machines. Inside the replicated machine the leader decides the apply time and **writes it into
  the log entry**; replicas never read their own clock. Code: the heartbeat method, eight lines.
- Why it works (property): **Safety of the lease arithmetic.** It depends only on how fast two clocks *tick*, not on what they read.
  The client stops first: 7 s against the server's 10 s. Worst drift 200 ppm is 2 ms over a lease; the 3 s margin is for round trips
  and scheduling.
- "What if the fix fails?": "What if the process is paused between reading the monotonic clock and doing the write? Or drift is
  far above your assumption, as on a throttled virtual machine?"
- Second fix or honest limit: The margin cannot help with a pause between check and write; that is challenge 1 again, and the token
  is the backstop. The bounded-drift assumption is an assumption: it is not load-bearing for safety once fencing is in, so we
  **monitor** clock health and the rate of local-deadline misses, and keep the margin configurable per tenant.
- If asked, I'd say: "I use monotonic clocks for durations and logical order for correctness. The client gives up before the
  server does, so there is never a window where it believes it holds a lock the server has given away. And because that still
  assumes bounded drift, the token at the resource is what the safety argument rests on."

### Challenge 4 · Leader loss, partition, and losing the group  *(failure recovery)*

- Q (interviewer): "The leader dies mid-grant, and a partition leaves two of the five replicas talking to some clients. What do
  those clients see?"
- Naive answer: "Promote a follower quickly, and let the minority side keep serving so we stay available."
- Case (IDs, times, numbers): Replicas R1–R5; R1 leads in term 7. A partition isolates {R1, R2} from {R3, R4, R5}. R3 wins term 8 at
  t = 1.5 s and commits a grant of `x`, token 9,001. Clients still on R1's side ask for `x`: if R1 answered, `x` would have two
  holders. R1 holds no majority, cannot commit, and its leader lease lapses after 1 s of silence.
- Break (which box): the consensus group box, split by a red cut.
- Fix (mechanism) · sequence? code?: **Majority commit and terms, plus a leader lease and a grace period.** Only the majority side
  commits; the stale leader steps down on contact with a higher term and discards uncommitted entries. A new leader treats every
  session as alive for one full session timeout (10 s) so a failover does not mass-evict every lock. Tokens are log indexes, which
  stay monotonic across terms. Sequence: partition, election, heal.
- Why it works (property): **Safety unconditional, liveness sacrificed on the minority side.** This is the honest CP position: the
  minority gets "unavailable", never a second grant. The grace period protects liveness after a failover.
- "What if the fix fails?": "Three of five replicas are gone, or someone restores last night's snapshot. What happens to the tokens?"
- Second fix or honest limit: No majority means **fail closed**: clients reach their local deadline, get `LockLost`, and stop.
  Restoring an old snapshot would **reissue tokens already given out**. So disaster recovery is *start empty*: bump the durable
  **epoch** (token = `epoch << 48 | index`, 16 + 48 bits), then wait one maximum lease (60 s) before granting so every old holder has
  stopped on its own deadline. The cost is a minute of outage, which is cheap against a double grant.
- If asked, I'd say: "Under partition I choose safety: the minority side refuses, it does not guess. After a loss of the whole
  group I start empty with a higher epoch, so every new token exceeds every old one, and I wait out the longest possible lease
  before granting. The outage is a minute, and the alternative is two holders."

### Challenge 5 · The top of the hour  *(overload)*

- Q (interviewer): "At the top of the hour traffic triples and two thousand clients retry at once after a network blip. What
  happens, and what do you do?"
- Naive answer: "Add replicas, or shorten the lease so dead holders clear faster."
- Case (IDs, times, numbers): Peak ≈ 30,000 committed writes/s against one group's ~15,000/s target. The queue grows by
  15,000/s, so after 10 s it is 150,000 writes deep and latency exceeds the 10 s TTL: grants that were in flight are already
  expired, clients retry, load rises. A metastable collapse. More replicas add fault tolerance, **not** write throughput, since every
  write must reach a majority.
- Break (which box): the single consensus group, saturated, dashed red.
- Fix (mechanism) · sequence? code?: **Partition by name, admit at the edge, retry with jitter.** `slot = hash(name) mod 64`, slots
  mapped to **4 groups**: 30,000 / (15,000 × 0.5) = 4. Gateway admission control with a per-tenant quota returns `overloaded,
  retry-after` instead of queueing; the SDK retries with jittered exponential backoff; sessions keep renewal at ~120/s instead of
  ~480/s; the leader batches entries into one fsync.
- Why it works (property): **Liveness inside capacity.** Locks are independent per name, so there are no cross-group transactions:
  that independence is what makes the partition free. Shedding at the edge keeps the committed work below the ceiling.
- "What if the fix fails?": "One group goes bad, or you need to move a slot while its locks are held."
- Second fix or honest limit: A bad group takes 25 % of the names with it and fails closed; the rest are untouched (blast radius).
  Moving a slot freezes it, drains held locks (up to one maximum lease), bumps the slot's **epoch** so the new group's token floor
  is above the old group's, and unfreezes. Without that floor a key that moves to a group with a lower log index would see its
  tokens go backwards.
- If asked, I'd say: "I size for the peak, not the average: 30 thousand writes a second against a 15 thousand ceiling means four
  groups with headroom. Replicas do not add write throughput. I shed load at the gateway with a retry-after, make clients back off
  with jitter, and shard by name because locks are independent. A bad shard fails closed for a quarter of the names."

### Challenge 6 · One hot name, and several locks at once  *(overload and contention)*

- Q (interviewer): "One name gets forty attempts a second, and each hold lasts a hundred milliseconds. What happens?"
- Naive answer: "Everyone polls until they get it, or we keep a queue that grows."
- Case (IDs, times, numbers): Capacity of one name = 1 / 0.1 s = 10 grants/s; 40 attempts/s is 4× over. With polling every 50 ms,
  30 waiters make 600 polls/s on that one name; each release wakes all of them and 29 lose (a herd). With an unbounded queue, depth
  grows 30/s: after 10 s a waiter is 300 deep and waits 30 s, longer than its own lease.
- Break (which box): the leader of the one group that owns that slot, dashed red.
- Fix (mechanism) · sequence? code?: **Bounded wait with directed hand-off.** Waiters are queued per name (session-scoped, depth
  capped, reaped when their session dies). `Release` grants to the head waiter **in the same apply step**: one write, one waiter
  woken. Beyond the cap or the wait budget the answer is `contended` with a retry-after. Sequence for the hand-off.
- Why it works (property): **Liveness and fairness without burning consensus.** Waiting costs no writes; the herd is gone; every
  wait is bounded.
- "What if the fix fails?": "A team now asks to acquire three locks atomically."
- Second fix or honest limit: Atomic multi-name acquisition across groups is a distributed transaction, so push back on the
  requirement. If it must be done: a canonical lock order (sorted by name, enforced in the SDK), try with a timeout and release
  everything on failure, and bounded leases so any deadlock clears itself within one TTL. And for the hot name itself: a lock caps a
  name at 1/hold per second; forty a second means the caller wants a queue or a single writer per partition, not a lock.
- If asked, I'd say: "A lock serialises. If the name is hot, the lock is the wrong tool. I bound the queue, hand the lock
  directly to the next waiter so a release is one write, and return an explicit rejection beyond the limit. For several locks I
  fix the order, bound every wait, and rely on leases so a deadlock heals in one TTL. I would not offer atomic multi-lock."

### Challenge 7 · How would you know it is broken?  *(observability)*

- Q (interviewer): "It is three in the morning, a team says duplicates are happening, and your dashboard is green. How would you
  have known?"
- Naive answer: "Watch CPU, memory and uptime of the service."
- Case (IDs, times, numbers): Availability 99.99 %, p99 8 ms: green. But one service has 12 `FencedOut` rejections a minute, its
  renewal failures are rising, and the hold-time p99 on one name grew from 0.5 s to 9 s.
- Break (which box): the whole baseline dimmed, with the metrics pipeline (tag `ch7`) as the only box outlined.
- Fix (mechanism) · sequence? code?: **Measure the guarantee, not the machine.** SLIs and targets (initial): acquire availability
  99.99 %; p99 < 20 ms; session-loss < 0.01 % of sessions an hour; **fenced-out writes: alert on any**; elections per group per day
  < 1; time to leader < 2 s p99. Plus a canary lock acquired continuously, and an offline checker that replays the log for
  overlapping holds. **Symptom pairs**:
  - fenced-out writes up **and** one client's renewal failures up → that client is pausing; the safety net worked, fix the client
  - elections up **and** acquire p99 up → an unhealthy group or disk
  - hold-time tail up **and** waiter depth up → someone holds a lock across a network call, or a hot name
  - token-gap growth up **and** attempts up → a retry storm
  Error budget: 99.99 % of a 30-day month = 259 s; at 2 s an election, about 130 elections a group a month spend all of it.
- Why it works (property): **It turns the safety argument into something you can watch.** Each pair names a cause, so the page goes
  to the right owner.
- "What if the fix fails?": "Fenced-out is zero this week. Does that mean you are safe?"
- Second fix or honest limit: No. Zero could mean nobody is sending tokens. Track **coverage**: the share of protected writes that
  carry a token, and a counter of writes that arrive without one. Also, a double hold that causes no stale write is invisible to the
  resource; the log audit finds overlapping holds using the server's durations. Honest limit: you can observe a violation after
  the fact, and you can alarm on its precursors; you cannot observe an absence of risk.
- If asked, I'd say: "I alert on the guarantee. Any fenced-out write pages someone, because it is either the safety net working or
  the first sign of a problem. I read metrics in pairs so each page names a cause, I track how many protected writes carry a token
  at all, and I audit the grant log for overlapping holds. Green dashboards about the service say nothing about the promise."

## 8 · Build cost (AUX)

**Marked AUX: the manager layer.** Three releases (called R0, R1, R2 so they are not confused with design versions V1–V3):

| Release | R0 · Prototype | R1 · Production, one region | R2 · Platform |
|---|---|---|---|
| Goal | Prove the model | One or two teams' correctness locks | Company-wide, multi-tenant |
| Substrate | Coordination store, or a relational row | Coordination store, sharded | Custom consensus service, or a managed global store |
| Fencing | Demonstrated | Enforced end to end for one resource type | Every resource type; proxy for legacy |
| Availability, on-call | None | 99.9 %, business hours | 99.99 %, 24/7 with an error budget |
| Effort (engineer-months) | 1–1.5 | 20–24 (4 engineers, 5–6 months) | 70–140 (6–8 engineers, 12–18 months) |

- **People and months, R1:** tech lead 1.0, senior backend 1.0, mid backend (SDK, migration) 1.0, SRE 1.0 (half the build is
  operations), manager 0.3, product/programme 0.2. Phases: discovery and RFC (3 weeks), walking skeleton (4), correctness incl. a
  linearizability harness under injected faults (6), hardening: sharding, quotas, revoke (6), operations: SLOs, runbooks, game day
  (4), first customer in shadow then cutover (3).
- **Total cost of ownership, illustrative:** 24 engineer-months to build, then ~1.75 people for five years (1.75 × 60 = 105) ≈
  **129 engineer-months ≈ 11 engineer-years**; infrastructure is about a tenth of it. People dominate.
- **Buy against build against don't:**

  | Option | Effort to a pilot | Five-year cost, engineer-months (illustrative) | When it wins |
  |---|---|---|---|
  | Don't: resource-side conditional write or idempotency | ~2 engineer-weeks per resource | ~10 | The resource supports it. **Check first, every time** |
  | Buy: a managed transactional store as the substrate | ~4 weeks | ~60 | Moderate volume, latency tolerant, a managed store already in use |
  | Adopt: a coordination store behind our own API and SDK | ~10 weeks | ~80 | High volume, correctness-critical, Kubernetes already run. **Our pick for R1** |
  | Build: a custom consensus service | ~6 months, 4 people | ~129 | A semantic nothing else gives, or very large scale |

- **Never cut:** fencing end to end, the conservative client deadline, the linearizability test harness, the runbook and a
  qualified on-call. **Cut first:** multi-region, shared modes, FIFO fairness, extra-language SDKs, the admin UI.
- **Top risks:** (1) fencing cannot be enforced at a key resource, so descope that caller to efficiency-grade in writing; (2)
  adoption fails and teams keep their own cache locks: a named pilot customer before any code, and **no named customer means do not
  build**; (3) scope creep into a general-purpose store, which is what happened to the best-known lock service: written non-goals,
  quotas enforced in code; (4) a key person who knows the replication protocol: pair, write design docs, two people qualified
  on-call before launch; (5) a split-brain incident: consensus store, fencing, a linearizability harness in CI, game days.
- **Staffing:** small first (design by committee is slow), grow in the middle where the work parallelises, **do not add people in
  stabilisation**, and share the on-call rotation with a sibling team so four people do not carry a 24/7 pager.
- **The question to ask the requesting team before saying yes:** "What happens if two of you hold this at once, and could the
  operation be made idempotent?"

## 9 · Recap

- **Final diagram:** the full carried baseline, all tags visible and green: SDK with sessions and local deadline, gateway, four
  consensus groups with leaders, resource with the check, epoch store, metrics and canary.
- **One sentence per path:** *Acquire:* one committed write, a token out. *Renew:* one heartbeat per client, measured from send
  time. *Release and expiry:* compare by token, hand off to the head waiter, a dead session is one command. *Fence:* the resource
  rejects anything older than it has seen. *Revoke:* audited, and the next token is higher.
- **If asked: multi-region.** Region-local services over region-owned resources; a global lock only for rare, coarse locks; never
  asynchronous replication of lock state, which is split brain with extra steps.
- **Common mistakes in this round:** a cache key with an expiry presented as a correctness lock; "tune the TTL" as the answer to a
  pause; no token, or a token nobody checks; comparing timestamps across machines; failing open silently; a beautiful consensus
  group and no word about the resource; never asking whether a lock is needed; offering atomic multi-lock; restoring an old
  snapshot; hiding the token in a thread-local; checking the lease and calling the check atomic.
- **Closing line (key-line voice):** "The lock service decides who should be working. The resource decides who is allowed to write.
  Everything I built is there so that those two answers can disagree safely."

## Canon check

For the video README, not for the screen. The source map is kept outside the tracked files.

| Canonical point | Covered at (chapter / slide) or dismissed because |
| --- | --- |
| A lock alone cannot make a system safe; a paused holder writes after expiry | Ch. 0 hook; ch. 3 mechanism M3; **C1** |
| Fencing tokens: monotonic, validated by the resource, equal vs smaller | **C1** (precision statement); API slide "Resource contract" |
| Leases with a TTL, not locks held until release | Ch. 3 M1, M5; FR2 flow |
| Consensus-backed replicated state; single cache node and a database row are not equivalent | Ch. 3 options matrix rows A, C, D; V2 |
| Quorum-of-caches debate: probabilistic safety, no token | Ch. 3 matrix row B; spoken in the matrix slide; **older source: "what changed since"**: conditional writes in object stores now make resource-side checks natural |
| Clock discipline: monotonic durations, conservative client deadline | Ch. 3 M4; **C3** |
| Safety against liveness, FLP-honest, fail closed | Ch. 3 part 2 and 3; **C4** |
| What the minority side of a partition sees | **C4** |
| Client that loses its lease mid-operation must stop | V3 SDK; FR2 flow step 5; **C1** |
| Do you even need a lock (idempotency, single-writer) | Ch. 0, **C2**, ch. 8 closing question |
| `SELECT FOR UPDATE` on a database row | Ch. 3 matrix row C: no lease, no token, tied to a connection; fine when the resource is in the same database |
| Reentrancy | Dismissed aloud on the API slide: a hold count in the SDK keyed by session, not server state; doubling writes for no gain |
| FIFO fairness, herd, deadlock, lock ordering | **C6** |
| Sharding by name, hot keys | **C5**, **C6** |
| Session heartbeats, grace period on failover | Ch. 3 M5; **C4** |
| Token continuity after restore or rebuild (epoch) | **C4** second fix |
| Observability, SLOs, error budget | **C7** |
| Multi-region | Out of scope in ch. 1; one slide in ch. 9; reason: cross-region quorum breaks the 20 ms target |
| Shared / read-write locks, watch API | Dismissed in ch. 1 (OUT): add behind the same API; no requirement |
| Build against adopt against don't, people and months | Ch. 8 |

## Budget

Planned: 86.5 minutes, 11,505 words, 182 slides. **Actual (script, after the build): 11,073 words, 166 slides**, 78 minutes of video.

| Chapter | Words (actual) | Slides (actual) |
|---|---|---|
| 0 Cold open | 342 | 6 |
| 1 Requirements and scope | 808 | 13 |
| 2 Estimates | 819 | 11 |
| 3 Theory | 1,570 | 20 |
| 4 API and entities | 978 | 12 |
| 5 High-level design | 1,502 | 22 |
| 6 Bridge | 80 | 2 |
| 7 Challenges | 42 | 1 |
| 7.1 Challenge 1: The paused holder | 705 | 11 |
| 7.2 Challenge 2: The resource cannot check | 561 | 9 |
| 7.3 Challenge 3: Clocks and leases | 547 | 9 |
| 7.4 Challenge 4: Leader loss, partition, group loss | 689 | 11 |
| 7.5 Challenge 5: The top of the hour | 509 | 8 |
| 7.6 Challenge 6: A hot name, several locks | 531 | 9 |
| 7.7 Challenge 7: How would you know? | 537 | 9 |
| 8 Build cost | 544 | 7 |
| 9 Recap | 309 | 6 |
| **Total** | **11,073** | **166** |
