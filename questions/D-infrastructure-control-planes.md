# Archetype D · Infrastructure & control planes

**SD-24 – SD-35.** Slice with `grep -n '^### SD-25' questions/D-infrastructure-control-planes.md`,
then Read with `offset`. Do not read this file whole.

**What this archetype tests as a family:** whether they think in **control plane versus data plane**.
Every question here has a fast path that must keep working when the management path is broken, and the
single most valuable thing to probe across all twelve is *"your control plane is down — what still
works?"* This is also the archetype closest to their actual experience, so **probe harder here**: a
platform engineer should be at 4 on several of these, and a 3 is not a good result.

---

### SD-24 · Distributed lock / coordination service   [T2 · G★ A]

**Read aloud:** *"Design a distributed lock service that other teams use to make sure only one process
does a thing at a time."*

**Crux.** **A lock service cannot make a distributed system safe on its own.** The holder can be paused
by GC, lose the lease without knowing, and keep writing. Safety must be enforced **at the resource**
via a monotonic fencing token. A candidate who designs a beautiful consensus-backed lock and never
mentions the resource side has missed the point of the question.

**Numbers if asked:** 10k lock acquisitions/sec, typical hold time 100 ms to 30 s, lease TTL default
10 s, p99 acquisition under 20 ms, must survive the loss of a minority of nodes, thousands of distinct
lock names, callers are JVM services with unpredictable GC pauses.

**Listen for:** **consensus-backed replicated state** (majority quorum, so committed state survives
elections) and why a single Redis node or a database row is not equivalent · **leases with TTL, not
locks held until release** — because you cannot distinguish a dead holder from a slow one ·
**monotonically increasing fencing tokens** issued with the lease and **validated by the resource**,
which rejects any write carrying a stale token — the crux · **clock discipline**: durations from
monotonic clocks, never wall clock, and the holder must renew based on its own elapsed time with a
safety margin · **safety versus liveness** stated explicitly, with FLP honesty — under partition you
either stall or risk two holders · what a client does when it **loses its lease mid-operation** (it
must stop, not finish) · **the better question**: whether the caller needs a lock at all, since an
idempotent operation or a single-writer partition is usually cheaper and safer.

**Probes:** *"The holder is paused by a 15-second GC pause. Its lease expires, another process
acquires. Both now write. What saves you?"* (the crux — do not accept "we'd tune the TTL") · *"Why not
a row in Postgres with `SELECT FOR UPDATE`?"* · *"Your client's clock is 5 seconds fast. What
happens?"* · *"The network partitions and the lock service minority side still has clients. What do
they see?"* · *(EM bar)* *"A team asks for this. What do you ask them before saying yes?"* (the
correct EM answer is to interrogate the requirement — most lock requests are idempotency problems in
disguise)

**Weak / Strong / Exceptional.** *Weak* — a key in Redis with `SETNX` and a TTL, no fencing, no
partition analysis. *Strong* — consensus-replicated leases, fencing tokens validated at the resource,
monotonic clocks, explicit safety/liveness position. *Exceptional* — challenges whether a lock is
needed at all, states what the service cannot promise, and prices the operational burden of running a
consensus cluster against buying one.


---

### SD-25 · Rate limiter (distributed)   [T1 · G★ M★ A MS]

**Read aloud:** *"Design a rate limiter for our API — every customer has a quota and we need to enforce
it across a fleet of servers."*

**Crux.** **Accuracy costs a network round trip per request.** A globally exact limiter needs shared
state on the hot path; a cell-local approximate one is fast and slightly wrong. The whole round is
whether they identify that axis, picks a side for stated reasons, and knows what the error is.

**If they ask:**

| Question | Answer |
|---|---|
| Traffic? | 1M requests/sec across 500 API servers in 3 regions |
| Limits? | Per-customer, per-endpoint; e.g. 1,000 req/min. Some customers have 100× others |
| Accuracy? | **"How accurate can you be, and what does exact cost?"** — this is the question |
| Latency budget? | The limiter must add under 1 ms at p99 |
| Behaviour at limit? | 429 with a `Retry-After`. Ask them what else the response should carry |
| Fail open or closed? | **"Your call — defend it."** |
| Bursts? | Customers legitimately burst; a hard per-second cap would break them |

**Listen for:**
- **Algorithms compared, not listed**: fixed window (simple, allows a 2× burst at the boundary —
  they should name that flaw), sliding window log (exact, memory-expensive), sliding window counter
  (good compromise), **token bucket** (handles bursts naturally, the usual right answer), leaky
  bucket (smooths output). The *boundary burst* problem is the detail that shows they have actually
  thought about fixed windows.
- **Where the counter lives**: a shared store on the hot path (accurate, adds latency, becomes a
  dependency and a bottleneck) versus **local counters per node with a share of the quota**
  (fast, approximate, and wrong when traffic is unevenly balanced) versus **local buckets with
  periodic async reconciliation against a central authority** — the best answer at this scale.
- The arithmetic of the naive split: **1,000/min across 500 nodes is 2 per node per minute**, which is
  useless — this number should force them to a better design, and asking them to compute it is the
  highest-yield estimation probe on the sheet.
- **Atomicity** of check-and-decrement (a Lua script or an atomic counter, not read-then-write).
- **Hot keys**: one customer's counter concentrated on one shard.
- **Fail-open vs fail-closed** decided explicitly — for a rate limiter, fail-open is usually correct
  because the limiter must not become an outage, and they should say that trade-off out loud.
- **Multi-region**: whether the quota is global or per-region, and the honest answer that a global
  quota across regions cannot be exact without cross-region latency.
- Response headers telling the client its remaining quota and reset time — the difference between an
  API people can build against and one they can't.
- **← The senior insight:** the limiter is on the critical path of every request, so **its own
  availability and latency matter more than its accuracy.** A limiter that is exactly right and
  occasionally down is a worse product than one that is 2% loose and never down.

**Probe ladder:**
- *Requirements:* "Is the limit global or per region, and who cares about the difference?" · "What
  happens when the limiter itself fails?"
- *Estimation:* **"1,000 requests a minute, 500 servers. How does each server know?"** · "1M req/s
  against a shared counter store — what QPS does that store see, and can it take it?"
- *Design:* the walk of one request through the check · "What's stored per customer, and how big is
  it?"
- *Deep dives:* "Fixed window — a customer sends 1,000 at 11:59:59 and 1,000 at 12:00:00. Is that
  within the limit?" · **"Take the network round trip off the hot path. What do you lose?"** ·
  "Load balancing is uneven and one node gets 40% of a customer's traffic. What happens with local
  counters?" · "One customer is 90% of your traffic and their counter is on one shard. Now what?" ·
  "Your counter store is down. What does the API do?"
- *EM bar:* "What's the SLO of the limiter, and how do you measure whether it's wrongly rejecting?" ·
  "A big customer says they're being limited unfairly. What do you look at?" (needs per-decision
  observability, designed in advance) · "What would you ship in week one?"

**Curveball:** *"A customer needs a burst allowance of 10× for the first 30 seconds of each hour,
because that's when their batch job runs."* Tests whether the algorithm choice can express real
policy, and whether they push back on per-customer special-casing as an operational liability.

**Weak / Strong / Exceptional.** *Weak* — a counter in Redis incremented per request, fixed window,
no atomicity, no failure story. *Strong* — token bucket, atomic operations, a considered position on
local-vs-shared state, fail-open decided explicitly, hot keys and multi-region addressed.
*Exceptional* — leads with the per-node arithmetic to justify the architecture, treats limiter
availability as more important than accuracy, designs the per-decision observability for the "why was
I limited" conversation, and prices the shared-store dependency.

**Traps.** Read-then-write on the counter (race under concurrency; a real production bug).
Fail-closed by default without noticing they just made the limiter a single point of failure for the
whole API. Assuming the load balancer distributes one customer's traffic evenly.


---

### SD-26 · Feature flags & config delivery   [T2 · M★ N G]

**Read aloud:** *"Design the system that delivers feature flags and configuration to every service and
client in the company."*

**Crux.** **A flag system is a change-management tool whose failure mode is a company-wide outage.** The
design must make evaluation local and fast, make the delivery path unable to break the caller, and
make a kill switch propagate in seconds — three requirements that pull against each other.

**Numbers if asked:** 5,000 flags, 10k service instances plus 100M mobile clients, evaluation must be
in-process with zero network calls, propagation target under 10 seconds for servers and minutes for
mobile, targeting by user attributes and percentage rollouts, hundreds of flag changes per day made by
engineers and PMs.

**Listen for:** **local in-process evaluation** against a cached ruleset — never a network call per
flag check, which is the single most important structural decision · delivery by **streaming push
with polling fallback**, and a stated propagation SLO · **the client must always start**: a bundled
default ruleset and last-known-good on disk, so a config-service outage cannot prevent startup (the
availability insight) · **percentage rollouts by deterministic hash**, so a user doesn't flip between
variants on each evaluation · **kill switches** distinguished from rollout flags, with a faster path
and a stated worst-case propagation · **audit trail and approval** for who changed what — this is a
production-change system and should be treated like one · flag lifecycle and **debt**: a flag with two
years of both branches alive is a liability, so expiry and cleanup enforcement matter · a **staged
rollout of the config itself** (canary the ruleset), because a bad ruleset is deployed to everything
at once.

**Probes:** *"The config service is down and a service instance restarts. Does it start?"* · *"A bad
flag change takes the site down. How fast can you revert, and what's the worst case?"* · *"A user
sees the new UI, refreshes, sees the old one. Why, and how do you prevent it?"* · *"5,000 flags and
nobody deletes them. What do you do about that as a manager?"* · *(EM bar)* *"This is the highest-blast
-radius system you own. What's the change-control process and what's the alert?"*

**Weak / Strong / Exceptional.** *Weak* — a network call per flag evaluation, no fallback, no audit,
rollout by random number. *Strong* — local evaluation with pushed rulesets, last-known-good on disk,
deterministic hashing, kill switches, audit trail. *Exceptional* — canaries the ruleset itself,
states propagation SLOs per client class, enforces flag lifecycle, and treats the whole thing as
production change control with the corresponding process.


---

### SD-27 · Authorization / permission graph (Zanzibar-like)   [T2 · G★ MS]

**Read aloud:** *"Design the service that answers 'can this user do this thing to this object' for
every product in the company."*

**Crux.** **Correctness and latency are in direct conflict.** The check is on the critical path of
every request, so it must be cached; but a stale permission cache means a user can read a document
after their access was revoked — a security bug, not a performance bug. The resolution is a
consistency token, and finding that need is the round.

**Numbers if asked:** 10M checks/sec, p99 under 10 ms, billions of relationship tuples, groups nested
up to 10 deep, permission changes must be effective "immediately" for the acting user and within
seconds globally, and the answer must be auditable.

**Listen for:** **relationship tuples** (`object#relation@subject`) as the data model rather than
per-product ACL tables · **evaluation as a bounded graph traversal** over nested groups, with depth
limits and cycle detection · caching of both tuples and computed decisions, with the invalidation
problem named honestly · **← the key mechanism: a consistency token / zookie** returned with reads
and passed to checks, so the caller can demand "at least as fresh as the change I just made" —
snapshot reads at a version rather than a global cache flush · **newly-enemy problem**: reordering of
a revoke and a content change can leak data, which is the subtle failure and a strong signal if they
raise it · **check-vs-list asymmetry**: "can A read X" is cheap; "list everything A can read" is
expensive and needs a different index · fail-closed on the authz path (opposite of the rate limiter,
and they should notice the difference) · audit logging of decisions for compliance.

**Probes:** *"Access is revoked. How long until every service refuses them, and is any window
acceptable?"* · *"You cache decisions for 60 seconds for latency. Argue against yourself."* · *"Group
nested 10 deep with 100k members — what's your evaluation cost?"* · *"Now list every document this
user can see. Same design?"* · *(EM bar)* *"Fail open or fail closed, and what does fail-closed mean
for your availability SLO when this is on every request?"*

**Weak / Strong / Exceptional.** *Weak* — per-service permission tables, cached with a TTL, revocation
"eventually". *Strong* — tuple model, bounded traversal, caching with an explicit staleness stance,
fail-closed, audit logging. *Exceptional* — arrives at consistency tokens for read-your-writes on
permissions, distinguishes check from list, raises the ordering/leak subtlety, and reasons about the
availability cost of being on every request path.


---

### SD-28 · Workflow orchestrator / distributed job scheduler   [T1 · A★ G MS]

**Read aloud:** *"Design a service that runs multi-step workflows reliably — steps that call other
services, can fail, need retrying, and must not be executed twice when they shouldn't be."*

**Crux.** **Durable execution state plus at-least-once step invocation means every step must be
idempotent** — and the orchestrator cannot promise exactly-once side effects, only exactly-once
*recorded* progress. Whether they state that honestly is the round.

**If they ask:**

| Question | Answer |
|---|---|
| Scale? | 100k workflow starts/sec, 1M concurrently in flight |
| Duration? | Seconds to 90 days |
| Steps? | 5–50 per workflow, calling internal and external services |
| Guarantee? | Every workflow must eventually complete or land in a terminal failed state. **Never silently stuck** |
| Side effects? | Steps charge cards and send emails. Ask them what that implies |
| Scheduling? | Both event-triggered and cron-style |
| Visibility? | Users must be able to see where a workflow is and why it's stuck |
| Versioning? | Workflow definitions change while instances are running — **this is the hard part** |

**Listen for:**
- **The workflow's state persisted after every transition** — an event/history log per instance, so a
  worker crash resumes rather than restarts. Holding state in a worker's memory is the weak design.
- **Separation of the orchestrator (decides what's next) from workers (execute a step)**, so a slow
  step doesn't block the scheduler.
- **A durable timer / timeout mechanism** that scales to 1M pending timers and 90-day sleeps — this is
  a genuinely hard subproblem and a good deep dive: a table scan for "due" rows won't do at this rate.
- **At-least-once step execution ⇒ idempotency required of every step**, with an idempotency key
  passed to the callee. **← This is the senior insight and it must be said out loud:** the
  orchestrator cannot make a non-idempotent side effect safe.
- **Retries with backoff, jitter and a retry budget**, plus a distinction between retryable and
  terminal errors, and a dead-letter/manual-intervention path.
- **Compensation / saga** semantics for rolling back a partially completed workflow, and the honest
  note that compensation is itself a workflow that can fail.
- **Versioning**: instances pinned to the definition version they started with, because migrating a
  running 90-day workflow to new logic is usually unsafe.
- **Visibility**: query by state, and "why is this stuck" answerable without a database spelunk.
- Fairness/isolation so one tenant's 10M workflows don't starve everyone else.

**Probe ladder:**
- *Requirements:* "What does 'never stuck' actually require you to build?" · "What's out of scope?"
- *Estimation:* "1M in-flight workflows with a pending timer each — how do you find the ones due in
  the next second, 100k times a second?" (the timer-index probe; a naive `WHERE due_at < now()` scan
  is the trap)
- *Design:* the walk of one 5-step workflow, including where state is written · "What's the exact
  boundary between orchestrator and worker?"
- *Deep dives:* **"A worker charges a card, then dies before recording success. What happens on
  retry?"** (the crux) · "A step is stuck retrying against a dead downstream for 6 hours. What does
  the system do, and who finds out?" · "You deploy a new version of a workflow definition. 400,000
  instances are mid-flight. What happens to them?" · "Step 4 of 6 fails permanently and steps 1–3 had
  side effects. Now what?" · "How do you scale the timer store?"
- *EM bar:* "What's the SLI for 'workflows complete'?" · "This becomes critical infrastructure for 40
  teams. What's the contract and what's the on-call load?" · "Buy or build? What tips it?"

**Curveball:** *"A workflow needs a human approval step that may take three weeks, and the approver
may leave the company."* Tests whether long waits are just another durable timer (good) or something
special (bad), and whether they handle external state changing during the wait.

**Weak / Strong / Exceptional.** *Weak* — a job table polled by workers, state in memory, retries by
re-running from the start, no versioning. *Strong* — event-sourced instance state, orchestrator/worker
split, scalable durable timers, idempotency keys, backoff and DLQ, version pinning. *Exceptional* —
states plainly that exactly-once side effects are impossible and pushes idempotency into the step
contract, designs the timer index with the arithmetic, handles in-flight versioning, and has a
build-vs-buy position with the operational cost quantified.

**Traps.** Believing a transaction around "call the service and record the result" is possible.
Retrying a whole workflow instead of the failed step. Ignoring that a 90-day workflow will outlive
several deployments of its own code.


---

### SD-29 · Device-fleet control plane (IoT)   [T2 · G A MS]

**Read aloud:** *"Design the control plane for a million devices in the field — you need to know their
state, push configuration and software to them, and do it without bricking the fleet."*

**Crux.** **The device is a principal you cannot trust and cannot physically reach.** Push is an
optimisation; the design is a **reconciliation loop** over desired-versus-reported state, and a
rollout without an automatic halt condition is a fleet-wide outage with a schedule.

**Numbers if asked:** 1M devices, intermittently connected (some offline for weeks), constrained CPU
and flaky networks, config changes daily and firmware monthly, telemetry every 5 minutes, a bricked
device costs a physical visit, devices live 7+ years and old versions never fully disappear.

**Listen for:** **per-device identity** with keys provisioned at manufacture, attestation, and
rotation/revocation · **desired state vs reported state**, with the device pulling and reconciling —
so an offline device converges when it returns, with no special-case code · **cohorts and staged
rollout** with canary gates, an explicit **halt condition and automatic rollback**, and the point that
a percentage is not a cohort · **A/B partitions and a watchdog** so a bad firmware image rolls back
without a human · **offline store-and-forward telemetry** with dedup on the server, since the device
buffers and replays · **telemetry cardinality**: never label a metric with a device ID; aggregate by
cohort · connection storms after a regional outage · the long tail of ancient versions, which means the
server must support every protocol version it ever shipped · a **kill switch** that works on a device
already running bad software.

**Probes:** *"You push a config that crashes the device on boot. It's now offline. What saves you?"* ·
*"200,000 devices come back online at once after a regional ISP outage. What happens to your control
plane?"* · *"A device has been offline for 6 weeks and 4 config changes. What does it do on
reconnect?"* · *"How do you know a rollout is going badly, and what stops it — a person or the
system?"* · *(EM bar)* *"What's your SLO, and what's the blast-radius budget for a firmware release?"*

**Weak / Strong / Exceptional.** *Weak* — server pushes commands, assumes devices are online,
percentage-based rollout with manual monitoring. *Strong* — reconciliation loop, per-device identity,
cohorted rollout with automatic halt, A/B firmware with watchdog, buffered telemetry with dedup.
*Exceptional* — designs for the un-reachable device first, quantifies the blast-radius budget, handles
the reconnect storm, plans for a 7-year version tail, and prices a field visit into the reliability
argument.


---

### SD-30 · API gateway / edge platform   [T1 · A★ MS G]

**Read aloud:** *"Design the API gateway that fronts every external request into the company — hundreds
of backend services behind one edge."*

**Crux.** **It is a single point of failure by construction, and every feature added to it increases
the blast radius of a change.** The design is as much about what *doesn't* belong in the gateway and
how config changes are rolled out safely, as about request handling.

**If they ask:**

| Question | Answer |
|---|---|
| Traffic? | 500k req/s peak, 3 regions, 300 backend services, 5,000 routes |
| Latency overhead? | Under 5 ms p99 added by the gateway |
| Availability? | 99.99% — it is the front door |
| Responsibilities? | TLS, authn, coarse authz, routing, rate limiting, request/response logging. **Ask them what they'd refuse to put here** |
| Config changes? | Teams change their own routes; ~100 changes/day |
| Payload sizes? | Up to 100 MB uploads |
| Protocols? | HTTP/JSON externally; HTTP and gRPC internally |

**Listen for:**
- **Stateless gateway nodes** behind L4 load balancing, with anycast/DNS for regional routing, so
  capacity is horizontal and node loss is trivial.
- **Config/routing as data, pushed to nodes and evaluated locally** — never a lookup per request — plus
  **staged rollout and validation of the config**, since a bad route table is an instant global
  outage. **← This is the crux and the best deep dive on the sheet.**
- **Token validation done locally** (verify a signed token, cache the keys) rather than calling an
  auth service per request; and what happens on key rotation.
- **Per-route timeouts, retries with budgets, circuit breakers and bulkheads**, so one slow backend
  can't consume all gateway connections — **connection/thread exhaustion from a single slow backend is
  the classic gateway outage** and a strong candidate names it.
- **Streaming large payloads** rather than buffering 100 MB in the gateway.
- **Backpressure and load shedding by priority** when saturated, plus admission control.
- What the gateway must *not* do: business logic, response aggregation for one team's convenience,
  per-team custom plugins — because each becomes a shared-fate liability. Saying no is part of the
  answer.
- **Blue/green or canary deployment of the gateway itself**, and how you canary something every
  request passes through.
- Observability per route and per tenant, so "the API is slow" is attributable in one query.

**Probe ladder:**
- *Requirements:* "What are you refusing to put in the gateway, and why?" · "What's your availability
  target, and what does that allow you per year?"
- *Estimation:* "500k req/s, 5 ms budget — how many nodes and what's the per-request CPU you can
  afford?" · "How many open connections at peak?"
- *Design:* the walk of one request through every stage in order · "Where does the route table live at
  request time?"
- *Deep dives:* **"A team pushes a bad route change. Walk me through the next 60 seconds."** · "One
  backend starts taking 30 seconds per request. What happens to unrelated traffic?" · "How do you
  deploy a new gateway version safely when 100% of traffic goes through it?" · "A 100 MB upload to a
  backend that rejects it — where do those bytes go?" · "Auth key rotation: walk me through it without
  an outage."
- *EM bar:* "What's the SLI and where do you measure it — at the edge or at the client?" · "300 teams
  depend on you. How do you let them self-serve route changes without letting them break each other?"
  · "What's the one-way-door decision here?"

**Curveball:** *"Compliance requires that all EU traffic terminates in the EU and never transits the
US, including failover."* Tests whether regional isolation was designed in or bolted on, and whether
they notice this removes their cross-region failover story.

**Weak / Strong / Exceptional.** *Weak* — a reverse proxy with a config file, auth by calling the auth
service per request, no circuit breaking, config deployed by restart. *Strong* — stateless nodes,
locally-evaluated pushed config with validation, local token verification, per-route resilience
controls, streaming, shedding. *Exceptional* — treats config change as the primary risk and canaries
it, names what belongs elsewhere and defends the boundary, designs self-service with guardrails, and
quantifies the blast radius of each option.

**Traps.** Making the gateway call an auth service per request (adds latency and a hard dependency).
Buffering large bodies. Letting each team add a plugin, then being surprised by shared-fate incidents.

---

### SD-31 · Service discovery & load balancing   [T2 · G A N]

**Read aloud:** *"Design how services find each other and spread load, across 10,000 instances of 500
services."*

**Crux.** **Propagation delay.** Between an instance dying and every client knowing, requests fail —
and the design is about shrinking and surviving that window, not eliminating it.

**Numbers if asked:** 500 services, 10k instances, instances come and go every few seconds (autoscaling
and deploys), clients make 1M internal RPCs/sec, unhealthy instances must be out of rotation within a
few seconds, registry must not be a hard dependency of the request path.

**Listen for:** a **registry as the source of truth** with instances registering and heartbeating, but
**clients caching the endpoint list locally** so a registry outage doesn't stop traffic — the key
availability decision · **client-side load balancing** (no extra hop, needs a fat client library) vs a
**sidecar/proxy** (language-agnostic, one more hop) vs a **central LB** (simple, a bottleneck and a
SPOF) — with the trade-off named · **health checking**: active probes vs passive/outlier detection
from real request results, and why passive catches things probes miss · **ejection and re-admission**
with hysteresis, so a flapping instance doesn't oscillate · load-balancing algorithm chosen for the
workload — **round robin vs least-request vs power-of-two-choices**, the last being the good answer
for heterogeneous latency · **graceful shutdown**: deregister, drain, then exit, and the observation
that most "deploy caused errors" incidents are a missing drain phase · zone-aware routing to keep
traffic local and its interaction with failover.

**Probes:** *"An instance is killed abruptly. How long do clients keep sending to it and what do they
see?"* · *"The registry is down. Does traffic flow?"* · *"One instance is up but returning errors for
one endpoint. Do your health checks catch it?"* · *"Why not just put a load balancer in front of every
service?"* · *(EM bar)* *"A deploy causes a 30-second error spike every time. What's missing and how
would you prove it?"*

**Weak / Strong / Exceptional.** *Weak* — DNS with a TTL, round robin, registry queried per request.
*Strong* — registry plus locally-cached endpoints, passive and active health checks, ejection with
hysteresis, graceful drain, a considered LB algorithm. *Exceptional* — quantifies the propagation
window and designs around it, makes the registry non-critical, chooses power-of-two-choices with a
reason, and connects deploy error spikes to the drain phase.

---

### SD-32 · CI/CD & build platform (developer productivity)   [T1 · G★ M MS]

**Read aloud:** *"Design the build and deployment platform for two thousand engineers in a large
monorepo."*

**Crux.** **Build the dependency graph, not a pipeline.** Everything good in this design — caching,
test selection, incremental builds — follows from having a precise graph of what depends on what.
Everything bad follows from treating CI as a queue of shell scripts. **This is the question closest to
their own platform-and-productivity experience, so probe it hardest and expect a 4.**

**If they ask:**

| Question | Answer |
|---|---|
| Scale? | 2,000 engineers, one monorepo, 50M lines, 3,000 commits/day, 20k CI runs/day |
| Current pain? | A full build is 90 minutes; engineers wait. **That's the brief** |
| Test suite? | 500k tests, 6 hours if run serially |
| Deploy targets? | 800 services, 200 deploys/day |
| Merge model? | Trunk-based; main must always be releasable |
| Budget? | Compute cost is already a visible line item — ask them what they'd spend and where |
| Metrics? | Ask *them* what they'd measure. Do not offer DORA |

**Listen for:**
- **A content-addressed dependency graph** of targets, with **remote build caching keyed on the hash
  of inputs** — if nothing an artifact depends on changed, don't rebuild it. This is the whole game.
- **Test selection from the graph**: run only the tests affected by the change, with the honest caveat
  that graph precision determines correctness and a too-clever cut misses real breakages.
- **Remote execution / distributed build** to parallelise across a fleet, and the cache-hit-rate metric
  as the primary health indicator of the platform.
- **Merge queue / commit queue**: test the merged result, not the branch, in batches, with bisection on
  failure — otherwise trunk breaks constantly at 3,000 commits/day, and they should connect the volume
  to the need.
- **Flaky-test handling as a systemic problem**: quarantine automatically, attribute to owners, and
  measure flake rate — because flakes destroy trust in the platform faster than slowness does.
- **Deployment**: artifact promotion through environments, progressive rollout, automatic rollback on
  SLO regression, and the same artifact deployed everywhere (build once).
- **Multi-tenancy and queueing fairness**, so one team's 10,000-job burst doesn't starve everyone; plus
  priority for the merge queue over speculative runs.
- **Metrics that matter**: p50/p95 time-to-signal, cache hit rate, flake rate, queue wait, and DORA
  (lead time, deploy frequency, change failure rate, MTTR) — **and cost per build**.
- **← The senior insight, and the one to listen hardest for:** this platform's product is
  **engineer-minutes**, so the design should be justified in those terms — *"cutting p95 signal time
  from 40 to 10 minutes gives 2,000 engineers back roughly N hours a day, which is worth M in
  compute"*. That sentence is the difference between an infrastructure answer and an EM answer.

**Probe ladder:**
- *Requirements:* "What's the actual goal — faster builds, or something else?" (the goal is
  time-to-signal and trunk health; a candidate who reframes it that way is signalling) · "What's out
  of scope?"
- *Estimation:* "20k runs a day, 90 minutes each. What's your compute bill, and what does an 80% cache
  hit rate save?" · "2,000 engineers waiting 40 minutes for signal — put that in hours per day."
- *Design:* the walk of one commit from push to deployed · "What exactly is the cache key?"
- *Deep dives:* **"How do you know which tests to run, and what happens when you're wrong?"** ·
  "3,000 commits a day on one trunk — how does main stay green?" · "A cached artifact is wrong because
  a dependency wasn't declared. How do you even find that?" (hermeticity — the deep answer) · "The
  flake rate is 2% and engineers retry everything on red. What do you do?" · "One team submits 10,000
  jobs. What happens to everyone else?"
- *EM bar:* **"What do you measure to prove this platform is working, and what would you report to
  your VP?"** · "Half the budget and half the team — what ships?" · "Buy or build? What would make you
  buy?" · "Nobody adopts your new build system. What now?" (adoption is the real failure mode of
  platform work — a strong EM goes here unprompted)

**Curveball:** *"Security now requires every artifact to be attested and every dependency scanned
before deploy, and that must not add more than two minutes."* Tests whether the graph and cache can
absorb a new mandatory stage, and whether they protect the developer experience while complying.

**Weak / Strong / Exceptional.** *Weak* — a pipeline per service, full build and full test suite on
every commit, more parallelism as the answer to slowness. *Strong* — dependency graph, remote cache
and execution, affected-test selection, merge queue, flake quarantine, progressive deploy with
rollback. *Exceptional* — frames the whole design as buying back engineer-minutes with a number
attached, treats hermeticity as the precondition for caching correctness, designs queue fairness, has
an adoption strategy, and names what they'd buy.

**Traps.** Adding parallelism without caching (spends money, barely moves p95). Test selection without
hermeticity (fast, occasionally lets a breakage through, destroys trust permanently). Ignoring flakes
as "the teams' problem" — an EM answer owns the flake rate as a platform metric.

---

### SD-33 · Cluster scheduler / capacity manager (Borg-like)   [T2 · G★ MS]

**Read aloud:** *"Design the system that decides which machine each workload runs on, across a hundred
thousand machines."*

**Crux.** **Utilisation versus isolation.** Packing tightly saves enormous money and makes noisy
neighbours and cascading evictions inevitable; the design is where they set that dial and how they
protect the important workloads when they're wrong.

**Numbers if asked:** 100k machines, 1M running tasks, 10k scheduling decisions/sec, workloads mix
latency-sensitive serving with batch, target utilisation above 60% (industry naive average is nearer
20%), machine failures are constant, a scheduling decision should take under 100 ms.

**Listen for:** **resource requests vs actual usage** and the overcommit decision that follows —
overcommitting memory is qualitatively more dangerous than CPU, and they should distinguish them ·
**priority classes with preemption**, so batch is evicted to protect serving, plus preemption cascades
as a failure mode · **bin packing** as the placement problem, with constraints (affinity,
anti-affinity, spread across failure domains, special hardware) and the note that optimal packing is
NP-hard so heuristics plus a scheduling *queue* are the real answer · **quota separate from
allocation** — a team's quota is an accounting promise, not a reservation, and conflating them is a
common design error · **sharded or optimistic-concurrency scheduling** to reach 10k decisions/sec, since
a single serialised scheduler cannot · **bad-machine detection and automatic draining**, because at
100k machines a small percentage of bad hosts silently eats a large amount of reliability ·
**disruption budgets** so maintenance doesn't take down all replicas of a service · what happens when
the scheduler is down: **running tasks keep running** (control/data-plane separation).

**Probes:** *"You overcommit memory by 20% and a batch job spikes. What dies, and who chose?"* · *"Two
schedulers pick the same machine at the same moment. What happens?"* · *"A team has quota for 1,000
cores but the cluster is full. What do they see?"* · *"Scheduler is down for an hour. What's the
impact?"* · *(EM bar)* *"Utilisation is 25% and finance wants it at 60%. What do you do first, and what
breaks?"*

**Weak / Strong / Exceptional.** *Weak* — first-fit placement, no priorities, no preemption, quota as
a hard reservation. *Strong* — priority classes with preemption, constraint-aware packing, sharded
scheduling, quota distinct from allocation, bad-machine draining. *Exceptional* — sets the
overcommit dial explicitly with the money attached, distinguishes memory from CPU risk, designs
against preemption cascades, and keeps the data plane alive without the control plane.

---

### SD-34 · Secrets management & key rotation   [T2 · MS A G]

**Read aloud:** *"Design how secrets and encryption keys are stored, distributed and rotated across the
company."*

**Crux.** **Rotation without downtime**, which requires that every consumer accept two valid keys at
once — and the recognition that a secrets service on the critical path of every service start is a
company-wide single point of failure.

**Numbers if asked:** 10k service instances, 50k distinct secrets, 500 encryption keys, rotation
required every 90 days for secrets and annually for keys (or immediately on suspected compromise),
audit of every access, secrets must never be in source control or environment variables of a shared
host, and services must start even during a secrets-service outage.

**Listen for:** a **root of trust** and the recursive problem it solves (how does a service authenticate
to the secrets service without a secret — workload identity from the platform, not a bootstrap
password) · **envelope encryption**: data keys wrapped by key-encryption keys held in an HSM/KMS, so
rotating the outer key doesn't require re-encrypting the data · **dual-key validity windows** for
rotation: publish new, accept both, migrate consumers, retire old — with the sequencing spelled out
and the observation that **rotation is a multi-week process, not an event** · short-lived,
automatically-renewed credentials as strictly better than long-lived secrets, with rotation becoming a
non-event · **caching with a TTL on the consumer** so a secrets-service outage doesn't stop the fleet,
balanced against revocation latency (the direct tension) · **audit logging** of every read, and
detection of anomalous access · **blast radius**: per-service, per-environment scoping so one leak
isn't total · the **compromise runbook**, which is the real test — what happens in the hour after a
leak is discovered.

**Probes:** *"How does a brand-new service instance authenticate to get its first secret?"* · *"Rotate
a database password used by 40 services, with no downtime. Walk me through it, in order."* · *"The
secrets service is down and 500 pods restart. What happens?"* · *"A secret leaks to a public repo at
2 a.m. What's the runbook?"* · *(EM bar)* *"How do you get 200 teams to stop putting secrets in config
files — what does the platform have to do to make the right way the easy way?"*

**Weak / Strong / Exceptional.** *Weak* — an encrypted store services read at startup, rotation as a
coordinated deploy, no audit. *Strong* — workload identity, envelope encryption, dual-validity
rotation, consumer caching with a stated revocation window, audit logs, scoped blast radius.
*Exceptional* — moves to short-lived credentials so rotation stops being a project, designs the
compromise runbook, keeps the fleet bootable during an outage, and treats developer ergonomics as the
adoption mechanism.

---

### SD-35 · Progressive deployment & automatic rollback   [T2 · G N A]

**Read aloud:** *"Design the system that rolls out a new version of a service safely and rolls it back
automatically when it's bad."*

**Crux.** **The halt condition.** A rollout without an automatic, quantitative halt condition is a
scheduled outage — and defining that condition requires statistically comparing canary against
baseline, not eyeballing a dashboard.

**Numbers if asked:** 800 services, 200 deploys/day, a service runs 50–5,000 instances across 3
regions, a bad deploy must be detected and reverted within 5 minutes, some changes are not revertible
(schema migrations), and canary traffic must be a representative sample.

**Listen for:** **stages with gates**: one instance → 1% → 10% → one region → everywhere, with a bake
time per stage and a stated rationale for the bake duration · **automatic analysis comparing canary to
a baseline** on error rate, latency, and business metrics — and the statistical honesty that at 1%
traffic a rare error may be undetectable, so the stage sizing has to be justified by the error rate
you need to catch · **automatic rollback on gate failure**, with a hard cap on rollout duration ·
**blast radius per stage** stated as a number of affected users, not a percentage of instances ·
**the not-revertible cases** — schema changes, data migrations, cache format changes — handled by
**decoupling deploy from release** (flags) and by expand/contract migrations · **rollback safety**:
whether the previous version can still read what the new one wrote, which is the failure candidates
miss most often · session draining and in-flight request handling at each step · **cross-service
dependencies**: rolling back service A while B has already adapted to A's new behaviour · a manual
override and an emergency full-speed path, because sometimes the fix must ship now.

**Probes:** *"What exactly stops the rollout — a person or a number? Give me the number."* · *"At 1%
canary, how long until you'd notice an error affecting 1 in 10,000 requests?"* · *"The new version
wrote data the old version can't parse. You roll back. What happens?"* · *"A schema migration is part
of the change. How do you roll that back?"* · *(EM bar)* *"What's the change failure rate you'd accept,
and how does this system move it?"*

**Weak / Strong / Exceptional.** *Weak* — rolling restart with a health check, monitored by a human
watching a dashboard. *Strong* — staged rollout with automated statistical gates, automatic rollback,
bake times, drain handling, deploy/release decoupled by flags. *Exceptional* — justifies stage sizes
against detectable error rates, treats backward-compatible data as a rollout precondition, handles
non-revertible changes with expand/contract, reasons about cross-service rollback ordering, and ties
it to change-failure-rate as the metric.
