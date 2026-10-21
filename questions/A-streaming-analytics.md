# Archetype A · Ingest, streaming & real-time analytics

**SD-01 – SD-07.** Interviewer: slice with `grep -n '^### SD-0n' questions/A-streaming-analytics.md`
then Read with `offset`. Do not read this file whole.

**What this archetype tests as a family:** whether they put a durable buffer between producers and
consumers, whether they know the difference between event time and processing time, and whether they
can tell the difference between *approximate and cheap* and *exact and expensive* — and choose
deliberately. The recurring senior insight across all seven: **the real-time path and the
exact/historical path are two different pipelines off the same stream, and conflating them is the
weak answer.**

---

### SD-01 · Real-time audience metrics (approximate unique counts)   [T1 · G M A]

**Read aloud:** *"Design a system that ingests viewing events from tens of millions of
internet-connected TVs and shows internal dashboards how many unique households are watching each
programme — updated to within about a minute."*

**Crux.** Exact distinct-counting at this cardinality is unaffordable, so the design must
deliberately trade accuracy for cost on the real-time path *while still preserving raw events for
exact historical analysis later.* Everything else is scaffolding.

**If they ask:**

| Question | Answer |
|---|---|
| How many devices? | ~50 million, each emitting an event every few seconds while powered on |
| Peak event rate? | Let them derive it. If pushed: assume 3M events/sec peak |
| Event size? | ~500 bytes |
| Does "unique" have to be exact? | No — within 1–2% is fine for dashboards |
| Dashboard refresh? | Once a minute is fine |
| Retention? | Raw events kept for years; exact historical analysis must be possible later |
| Regions? | One region to start |
| Who reads it? | Internal analysts, tens of concurrent dashboards — not consumer scale |

**Listen for:**
- Thin, **stateless ingest tier** behind a load balancer — collectors do validation and nothing else.
- A **durable, partitioned event log** between ingest and processing, so producer spikes and consumer
  slowness don't lose data. Ask *why* if they add it; ask *what absorbs a spike* if they don't.
- A **stream processor** computing rolling per-programme counts over time windows.
- An **approximate distinct-count structure** — they may say HyperLogLog, or "a probabilistic
  cardinality sketch". **The insight is that exact distinct-counting is too expensive**; the name is
  worth nothing without that reasoning. Sketches being *mergeable* across partitions is the detail
  that separates recall from understanding.
- Handling of **late and out-of-order events** — windowing with a watermark and a stated lateness
  cutoff, plus what happens to events arriving after it.
- A small, fast **serving store** the dashboards read; not a live query over the event store.
- **Separately: raw events landed in cheap columnar storage** for later exact/batch queries.
- **← The senior insight:** real-time-approximate and batch-exact are **two paths off one stream**,
  with the log as the shared source of truth. A candidate who builds one path and bolts the other on
  as an afterthought is at 2–3; one who names the split unprompted is at 4.
- Replay + idempotency: a consumer crashing for ten minutes must neither lose nor double-count.

**Probe ladder:**
- *Requirements:* "What did you decide is out of scope?" · "Is 1–2% error acceptable for every
  consumer of this, or just the dashboards?"
- *Estimation:* "3M/s at 500 bytes — what's that per day, and what does that number rule out?"
  (~1.5 GB/s, ~43 TB/day raw; it rules out a single ingest node and any synchronous DB write.)
- *Design:* the end-to-end walk of one event · "Why a log rather than writing straight to the
  database?"
- *Deep dives:* **"Events arrive late or out of order — how do you count them correctly?"** (the
  crux-adjacent probe; look for windowing and watermarks, not just "I'd sort them") · "Why
  approximate? What would exact cost?" · "A consumer crashes for ten minutes — do you lose data or
  double-count?" · "Programme X is a national final and is 1000× hotter than the rest — what
  happens to that partition?"
- *EM bar:* **"How would you know in production that the counts are wrong?"** (this is the best
  question in the sheet — a wrong number that looks plausible is the real operational risk here) ·
  "What's the SLA on that one-minute freshness, and what does the pipeline cost a month?"

**Curveball:** *"Legal now needs to delete all events for a given household on request, including
from the historical store."* Watch whether they touch only the storage layer or realises the sketches
are unattributable and the raw store needs a deletion path with a re-derivation story.

**Weak / Strong / Exceptional.** *Weak* — events written straight to one database, `COUNT DISTINCT`
run live, no buffer, late data ignored. *Strong* — durable log, stream processor, approximate
counting, separate batch path, replay and idempotency handled. *Exceptional* — quantifies the load
to justify each choice, reasons about lake-vs-serving-store cost, names how drift would be detected
and what the on-call story is, and scopes an MVP first.

**Traps.** Making the collector do the aggregation (loses the replay property). Treating "unique
households" as "unique devices" without asking (a household has several TVs — a strong candidate
asks). Choosing exact counting because "1–2% sounds sloppy" without pricing it.

**Deep reference:** [`guides/interviewer-guide.md`](../guides/interviewer-guide.md) §6
Problem A.

---

### SD-02 · Trending now / Top-K leaderboard   [T1 · G★ M★]

**Read aloud:** *"Design a system that shows the current top 10 trending shows across the country in
near real time, based on a high-volume stream of 'someone started watching X' events."*

**Crux.** Reads vastly outnumber writes, so the leaderboard must be **precomputed on the write path
and served from cache** — and the memory cost of tracking every title forces a deliberate choice
between exact counting for a bounded key space and approximate counting for an unbounded one.

**If they ask:**

| Question | Answer |
|---|---|
| Event volume? | Millions of view-start events per minute |
| Definition of trending? | Simple count over a sliding window — say the last 10 minutes |
| How many titles? | Start with ~100k. **If they ask whether it could be unbounded, say yes: user-generated content, tens of millions of keys** — that question is itself a strong signal |
| Refresh rate? | Every few seconds |
| Exact ranking required? | No, approximate is acceptable |
| Read volume? | Very high — shown to many users and dashboards |
| Global or per-region? | National top 10; per-region is a stretch goal |

**Listen for:**
- Ingest into a **durable stream**, partitioned by title (or by hash of title).
- **Sliding-window counting** with a concrete mechanism for how old events *age out* — bucketed
  sub-windows that are summed and expired is the common correct answer; "I'd subtract old events"
  usually means they haven't thought about the state.
- Recognition that **per-partition partial counts must be aggregated** into one global ranking, and
  that this aggregation is where the ordering guarantee lives.
- A **heap / top-K structure** at the aggregation point, not a full sort of all titles.
- At high cardinality, an **approximate frequency structure** (count-min sketch, or "track only heavy
  hitters") to bound memory — with the trade-off named: it over-counts, never under-counts.
- **Precompute + cache the leaderboard**; reads hit a single cached blob, not the counters.
- A stated **staleness budget** — how old the served leaderboard can be, and why that's acceptable.
- **← The senior insight:** the read path and write path have wildly different volumes, so you
  precompute on write and serve a cached result on read. If they say this in their own words, note the
  quote.

**Probe ladder:**
- *Requirements:* "What does 'trending' actually mean here — you picked a definition; defend it."
  (Raw count favours already-popular titles; a rate-of-change definition is more interesting and
  much harder. Either is fine *if justified.*)
- *Estimation:* "How much memory does your counter state need? Show me." Then: "now the key space is
  50 million — same answer?"
- *Design:* the end-to-end walk · "Reads are 10,000× writes here — where does that show up in your
  picture?"
- *Deep dives:* **"How do counts expire as the window slides?"** · "Two aggregator nodes each have
  partial counts — how do you get one global top 10, and is it correct?" · "Memory blows up if you
  track every title — what do you do?" · "How fresh is the leaderboard really, and is that okay?"
- *EM bar:* "How would you test that the ranking is correct?" · **"How would you detect that it has
  silently gone stale?"** (a frozen leaderboard looks exactly like a quiet news day — this is the
  operational crux and most candidates miss it) · "What would you cut to ship this in three weeks?"

**Curveball:** *"Now we want top 10 per region, for 200 regions, plus the national one."* Watch for
the realisation that per-region state multiplies memory and that the national list can be derived by
merging regional ones — and whether they check that merging top-K lists is *not* generally exact.

**Weak / Strong / Exceptional.** *Weak* — recomputes a global sort over all events on every page
view. *Strong* — durable stream, windowed counting with explicit expiry, precomputed leaderboard
served from cache, sensible aggregation of partial counts. *Exceptional* — reasons explicitly about
read/write asymmetry and memory, chooses approximate vs exact deliberately with a justification tied
to cardinality, and addresses staleness detection and the freshness SLO.

**Traps.** Merging per-partition top-10 lists and calling it a global top 10 (wrong — a title ranked
11th everywhere can beat one ranked 1st in a single partition; they must aggregate counts, not lists).
Using a cache TTL as the freshness mechanism without noticing that a stalled writer leaves a stale
value that never refreshes visibly.

**Deep reference:** [`guides/interviewer-guide.md`](../guides/interviewer-guide.md) §6
Problem C.

---

### SD-03 · Ad click aggregation & billing counters   [T1 · G★ M★ A]

**Read aloud:** *"Design the system that counts ad impressions and clicks and produces the numbers
advertisers are billed on."*

**Crux.** These counts are **money**, so the usual "approximate is fine for analytics" answer is
wrong here — and yet the volume forbids a synchronous transactional write per click. The design must
reconcile a fast approximate path with an eventually-exact, auditable one, and must be correct under
retries.

**If they ask:**

| Question | Answer |
|---|---|
| Volume? | 1M clicks/sec peak, 10× that in impressions |
| Freshness for advertiser dashboards? | A minute or two is fine |
| Freshness for billing? | Daily is fine, but it must be **exact and auditable** |
| Duplicates? | The client retries on network failure; the same click can arrive several times |
| Late data? | Mobile clients buffer offline; events can arrive hours late, occasionally days |
| Retention? | Raw events 6 months, aggregates 7 years |
| Fraud? | Out of scope — assume a separate system flags invalid clicks and can **retroactively
invalidate** them |

**Listen for:**
- Client-supplied **idempotency key / event ID**, and dedup somewhere durable — with a stated window
  for how long dedup state is kept and what happens outside it.
- Durable log first, aggregation second. Never "increment a counter in the DB per click".
- **Event-time vs processing-time** distinction made explicitly, and the aggregation keyed on event
  time — otherwise a late batch lands in the wrong day and the invoice is wrong.
- **Two paths with different guarantees**: fast approximate for dashboards, batch recompute for
  billing, with the batch result being authoritative and **reconciliation between them monitored.**
- Idempotent, **replayable** aggregation — recomputing a day must produce the same answer (so
  aggregation output is keyed and overwritten, not incremented in place).
- An **immutable audit trail**: for any invoice line, the ability to point at the events behind it.
- Handling of the **retroactive invalidation** case — the fraud system removing clicks after billing
  ran, which forces either a correction/adjustment model or delayed finalisation.
- **← The senior insight:** "exactly once" end-to-end doesn't exist; what exists is **at-least-once
  delivery plus idempotent, replayable aggregation**, which is *effectively* once. A candidate who
  says "I'd use exactly-once semantics" and cannot unpack it is name-dropping.

**Probe ladder:**
- *Requirements:* "Which of these numbers has to be exact and which doesn't? Why is that distinction
  worth building two paths for?"
- *Estimation:* "1M/s — what does a day of raw events cost you to store, and what does that say about
  retention tiers?"
- *Design:* the end-to-end walk · "What's the primary key of your aggregate table, and why?"
- *Deep dives:* **"The same click arrives three times, two seconds apart, from a retrying client.
  Walk me through it."** · "A batch of yesterday's events shows up at 6 a.m. today — which day gets
  billed, and how?" · "Your stream job crashes and you replay four hours. Is the advertiser
  double-billed?" · "Fraud invalidates 2% of last month's clicks after invoices went out — what
  happens?"
- *EM bar:* **"An advertiser calls and says our number is 3% higher than theirs. What do you do, and
  what did you build in advance to make that answerable?"** (the single best probe on this sheet —
  it tests auditability, reconciliation and operational thinking at once) · "What's the alert that
  fires when the two paths diverge?" · "Who is on call for this and what wakes them?"

**Curveball:** *"Finance wants the ability to re-run any historical day and get bit-identical
numbers, two years later."* Tests whether their aggregation is a pure function of immutable input, or
whether it depends on mutable config (rate cards, fraud lists) that also needs versioning.

**Weak / Strong / Exceptional.** *Weak* — `UPDATE counters SET n = n + 1` per click; no dedup; no
event-time handling; one path for everything. *Strong* — dedup by event ID, durable log, event-time
windowed aggregation, separate authoritative batch path, replay-safe. *Exceptional* — treats
reconciliation as a monitored product feature, versions the inputs so history is reproducible,
designs the adjustment path for retroactive invalidation, and can say what the whole thing costs per
million clicks.

**Traps.** Deduping in memory in the stream processor only (loses dedup state on restart, exactly
when replay makes duplicates likely). Assuming the click timestamp from the client is trustworthy —
it is attacker-controlled and clock-skewed; a strong candidate uses both client and server time.


---

### SD-04 · Metrics & monitoring pipeline   [T2 · G M A MS]

**Read aloud:** *"Design the metrics system for a company running ten thousand services — ingest,
storage, querying, dashboards and alerting."*

**Crux.** **Cardinality**, not volume. A single badly-labelled metric can multiply series count by
millions, and the design must make that structurally impossible or at least survivable.

**Numbers if asked:** 10k services, ~1M active time series per service tier, 10-second scrape
interval, 100M data points/minute ingest, queries mostly over the last hour but retention 13 months,
p99 dashboard query under 2 s, alerting evaluation every 30 s.

**Listen for:** pull (scrape) vs push and the trade-off named · a time-series store with **delta and
timestamp compression**, not rows in a relational DB · **downsampling / rollup tiers** by age with
retention per tier · **cardinality limits enforced at ingest** with per-tenant quotas and a way to
find the offender · aggregation at the edge for high-frequency series · separate alerting evaluation
path so a dashboard query storm can't stop pages firing · **alert on symptoms, page on burn rate,
not on every threshold** · the meta-problem: monitoring the monitoring, without a circular dependency.

**Probes:** *"A team ships a metric labelled with user ID. What happens, and how does your design
survive it?"* · *"Why not store this in a relational database — be specific about what breaks?"* ·
*"How do you serve a 13-month query in under two seconds?"* · *"Your alerting pipeline is down. How
does anyone find out?"* · *(EM bar)* *"What does this cost per service per month, and what's the
conversation you have with the team whose metrics cost the most?"*

**Weak / Strong / Exceptional.** *Weak* — one big database, all metrics kept at full resolution
forever, alerts as DB queries. *Strong* — compressed TSDB, rollup tiers, cardinality quotas,
separate alert path. *Exceptional* — treats cardinality as the primary design constraint, prices
retention tiers, and has an answer for monitoring the monitor.


---

### SD-05 · Log search & distributed tracing backend   [T2 · G A N]

**Read aloud:** *"Design a system where engineers can search across all logs from all services, and
follow a single request's path across fifty services."*

**Crux.** Full-text indexing every log line is unaffordable at this volume, and tracing every request
is unnecessary — so the design lives or dies on **sampling and retention policy**, and on sampling
that still captures the traces you actually need (the slow ones and the failures).

**Numbers if asked:** 5 TB of logs/day, 100k spans/sec, 50 services in a typical request path,
engineers search the last 24 h in 95% of cases, retention 30 days for logs and 7 days for traces,
search p95 under 5 s, ingest must never block the application.

**Listen for:** ingest decoupled from the application (local agent + buffer; never a synchronous
network write in the request path) · **trace context propagation** as the hard cross-cutting problem,
including through queues and third parties · **tail-based sampling** — decide *after* seeing the
whole trace so errors and slow traces are kept, and its cost (buffering all spans until the trace
completes) · **head-based sampling** as the cheap alternative and what it loses · time-partitioned
indexes with hot/warm/cold tiers · indexing only structured fields, storing the raw body in object
storage · linking logs↔traces by trace ID so one query hops to the other.

**Probes:** *"Which traces do you keep, and how do you know a trace is interesting before it's
finished?"* · *"A service in the middle doesn't propagate the trace header. What do you see?"* ·
*"Your log volume triples during an incident — exactly when you need it most. What happens?"* ·
*"Why not index everything?"* · *(EM bar)* *"What's the cost per engineer per month, and would you
buy this instead of building it?"*

**Weak / Strong / Exceptional.** *Weak* — everything into one full-text index, no sampling, ingest
in the request path. *Strong* — buffered agents, structured-field indexing, tiered retention,
deliberate sampling strategy with the trade-off named. *Exceptional* — tail sampling with a costed
buffer, incident-time volume surge handled by shedding low-value data first, and a clear build-vs-buy
position.


---

### SD-06 · A/B experiment platform   [T2 · M★ G N]

**Read aloud:** *"Design the platform teams use to run A/B experiments — assignment, exposure
logging, and the metrics that say whether the experiment won."*

**Crux.** **Assignment must be deterministic, sticky and instant**, computed client- or server-side
without a network call, while the *analysis* side must be trustworthy enough that people accept
losing. Two very different systems sharing one config.

**Numbers if asked:** 2B users, 1,000 concurrent experiments, assignment must add <1 ms and must not
require a network call, exposure events ~50k/sec, metrics refresh daily with a real-time
guardrail check every 15 minutes.

**Listen for:** **hash(user_id + experiment_salt) → bucket** — deterministic, no state, no lookup —
and why a random assignment stored in a database is the wrong answer · config distributed by push or
poll with a bounded staleness and a **kill switch** whose propagation time is stated · **exposure
logging** (log that the user *saw* the treatment, not that they were bucketed — the distinction is
the single most common real-world bug in these systems) · mutual exclusion / layering so overlapping
experiments don't confound each other · sample ratio mismatch detection as a correctness alarm ·
guardrail metrics that auto-halt a harmful experiment · the statistics honestly bounded: fixed
horizons or sequential testing, not peeking daily and stopping on a win.

**Probes:** *"Why hash rather than assign-and-store?"* · *"Two experiments both change the checkout
button. What breaks, and how does your design prevent it?"* · *"An experiment is losing money badly.
How fast can you stop it, and what's the mechanism?"* · *"Your buckets should be 50/50 and they're
52/48. What does that mean and what do you do?"* · *(EM bar)* *"A PM wants to ship on day two
because it's winning. What does the platform do to make that conversation easy?"*

**Weak / Strong / Exceptional.** *Weak* — assignment stored per user in a database, no exposure
logging, no interaction handling. *Strong* — deterministic hashing, layered experiments, exposure
logs, guardrails, kill switch. *Exceptional* — SRM detection, sequential testing to make early
stopping legitimate, and treats the statistical guardrails as a platform responsibility rather than
the analyst's problem.


---

### SD-07 · Event-driven platform / durable log (Kafka-like)   [T2 · G A MS]

**Read aloud:** *"Design a durable, partitioned event log as a platform service — the thing other
teams publish to and consume from."*

**Crux.** The **ordering and delivery guarantees you offer**, stated precisely, and what they cost
you in the replication and commit path. Everything else in the design follows from that contract.

**Numbers if asked:** 10 GB/s aggregate write, 5× that read (multiple consumer groups), 7-day
retention default with per-topic override, publish p99 under 10 ms, no data loss on single-node
failure, thousands of topics and tens of thousands of partitions.

**Listen for:** **partition as the unit of ordering and parallelism** — ordering within a partition
only, and the consequence that a global ordering requirement means one partition means no scaling ·
append-only segment files, sequential I/O and page cache as the reason this is fast · replication
with a leader per partition, an in-sync-replica set, and a **stated acknowledgement policy**
(ack=leader vs ack=quorum) with its durability-vs-latency trade-off · consumer groups, offsets and
rebalancing, with the rebalance storm as a known failure mode · **delivery semantics stated
honestly** — at-least-once by default, at-most-once, and "exactly once" as
idempotent-producer-plus-transactional-commit within the system only, never end-to-end into an
external side effect · consumer lag as the primary SLI · retention by time/size, compaction as a
distinct mode and what it is for · the **outbox pattern** for the write-to-DB-and-publish problem if
they raise dual writes.

**Probes:** *"A consumer needs strict global ordering across all events. What do you tell them?"* ·
*"The leader for a partition dies mid-write with acks outstanding. Walk me through it."* · *"A
consumer group is 6 hours behind. What's happening to the cluster and what do you do?"* · *"A team
says they need exactly-once into their database. Is that possible? Be precise."* · *(EM bar)*
*"You're running this for 200 teams. What's the quota model, and what stops one team taking the
cluster down?"*

**Weak / Strong / Exceptional.** *Weak* — "I'd use Kafka" with no mechanism, or a queue with no
ordering story. *Strong* — partitions, replication with an explicit ack policy, consumer groups,
honest delivery semantics, lag monitoring. *Exceptional* — treats the guarantee contract as the
product, prices the replication factor, designs the multi-tenant quota model, and names build-vs-buy
explicitly.
