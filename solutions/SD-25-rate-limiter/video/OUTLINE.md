# SD-25 · Rate limiter (distributed) — reference-solution outline (six-chapter, C4-first format)

Target level: staff (manager layer as one recap follow-up) · Target length: 45–55 min · Word budget: 5,800–6,800 · 6 challenges.
Re-cut on 2026-11-28 from the older solution (`git show HEAD:solutions/SD-25-rate-limiter.md`) and the L6 EM mock video.
The slides and narration are `src/*.py`; the C4 views are `../workspace.dsl` + `../views.json`; the technologies `../stack.json`.

## Thesis and hook

- **Thesis** (key line): *A rate limiter sits on every request, so its latency and availability matter more than its
  accuracy. Decide in memory from a token bucket, lease the global budget to where the traffic actually lands, and know
  exactly how wrong you can be.*
- **Hook** (figure `tension`): one customer, 1,000 a minute, 500 servers, three answers — a central counter (exact, +1.2 ms
  at p99, Redis down means the API is down) · a static split (2 per server per minute: throttled at 0.6 % of its quota) ·
  leases that follow demand (≤ 5 % over, microseconds, survives its own dependencies).

## Scale line (GUIDELINES §3.1)

Volume per month: **1 M requests/s on average, 2.6 T a month**, over **500 API servers in 3 regions** · Keys and retention:
**2 M limit keys** (100,000 customers × 20 endpoints); **30 days** of decisions kept · Peak and its cause: **3 M requests/s at
the top of every hour**, when customers' batch jobs start; inside it, **one customer at 100,000/s** (10 % of the average).

## 1 · Prompt, clarifying Q&A and C4 context

- **Graded** (weak · strong): requirements (a protection limit, not a meter) · correctness (algorithm compared; atomic) ·
  trade-offs (exact against a round trip per request; the error stated) · depth (leases sized by demand, the bound N × c,
  regional budgets) · operations (fail mode per limit, false-limit rate, "why was I limited?").
- **Clarifying** (5): what a limit is (per customer and endpoint, 1,000/min typical, some 100×) · how exact ("how accurate can
  you be, and what does exact cost?") · latency (under 1 ms p99 added) · at the limit and on failure (429 + Retry-After;
  fail mode "your call — defend it") · bursts and regions (legitimate bursts; most limits per region, some contracts global).
- **FR1** decide per request · **FR2** tell the client (limit, remaining, reset; 429 + Retry-After + decision ID) ·
  **FR3** configure (tiers, bursts, schedules, scope, mode; staged; effective in seconds) · **FR4** explain any 429.
- **NFRs** (initial targets): ≤ 1 ms p99 added at 3 M/s · API availability unaffected by the limiter (99.99 %) · local-mode
  keys within 5 % of the limit over a minute, exact-mode keys never over · policy change everywhere in ≤ 10 s ·
  false-limit rate < 0.1 %.
- **Properties**: `S1-bounded-overshoot` · `S2-never-the-outage` · `S3-no-false-limits` · `L1-change-in-10s` ·
  `L2-decide-in-1ms`.
- **IN**: per-customer/endpoint quotas, fleet and region enforcement, the client contract, policy management with staged
  rollout, decision observability. **OUT**: DDoS at the network edge (a different layer), billing and metering (a separate
  exact pipeline — said aloud), abuse detection, load shedding by criticality, authentication.
- **C4 context**: API clients → system (HTTPS) · system → backend services (gRPC, admitted only) · account team → system
  (HTTPS) · usage metering → system (Kafka topic, async: reads request logs, never the limiter's counts).
- **The core is three things**: a decision in memory from a token bucket; leases of the global budget that follow demand;
  a failure mode chosen per limit.

## 2 · Back-of-the-envelope

| Number | From | Arithmetic | Label | Constraint it forces |
|---|---|---|---|---|
| Requests | average | 1 M/s × 2.6 × 10⁶ s = 2.6 T/month; × 3 = 3 M/s | given | the decision is per request: in memory |
| Per server | peak, fleet | 3 M/s ÷ 500 = 6,000/s; × 2 µs = 1.2 % of a core | illustrative | in-process is cheap; a sharded map |
| Central store | peak | 3 M scripts/s ÷ ~100 k per shard = 30 primaries | illustrative | feasible, but a dependency on every request |
| Static split | limit, fleet | 1,000/min ÷ 500 = 2 per server per minute; 3 servers → 6/min = 0.6 % | arithmetic | rules out a static split; shares follow demand |
| Latency | NFR | in-zone round trip ~0.3 ms median, ~1.2 ms p99; cross-region 70–150 ms | illustrative | no call per request; no exact global |
| State | keys | 2 M × 64 B = 128 MB; ~20 k active per server × 64 B ≈ 1.3 MB | illustrative | memory is not the problem |
| Hot customer | peak | 100 k/s on one key vs ~100 k ops/s per shard; leases: 500 × 10 = 5,000 updates/s | illustrative | aggregate locally |
| Sync | fleet | 167 servers × 10/s ≈ 1,700 batches/s a region; ≤ 600 keys each → ≤ 1 M key-updates/s; 8 shards ≈ 125 k each | illustrative | batched, sharded by key, off the hot path |
| Decisions | average | 1 % 429s + 1 % of allows = 20 k/s × 150 B = 3 MB/s; × 2.6 M s ÷ 5 ≈ 1.6 TB / 30 days | illustrative | a columnar store |

Budget bar (`budget`): the exact path — policy lookup 0.02 + Redis round trip at p99 1.2 + script 0.05 = 1.27 ms against
1 ms: over. The local path is ~0.03 ms.

## 3 · API contracts and the data model

| Endpoint / event | Serves | Key · status codes | What the response says |
|---|---|---|---|
| `allow(customer, endpoint, cost)` in process | FR1 | — | allowed, remaining, reset, retry-after, policy version, decision ID |
| any response; `429 Too Many Requests` | FR2 | `RateLimit-*` headers, `Retry-After`, `decision_id` | the client can plan; support can trace |
| `PUT /v1/policies/{customer}/{endpoint}` | FR3 | `If-Match` version; `202` with the new version in `shadow` | staged, versioned |
| `Sync` RPC (server → quota service) | FR1 at scale | per key: admitted, asked, policy version | per key: lease, valid until, global remaining |
| `GET /v1/decisions/{id}` | FR4 | — | policy version, server, mode, lease, global count |

Tables (`erd-physical`): tier · policy (customer, endpoint, version) · local bucket (in memory) · global bucket (quota
service memory) · exact bucket (Redis hash, TTL) · decision (ClickHouse, by day). Lifecycle (`state-policy`): draft →
shadow → canary → enforced → superseded; canary or enforced → rolled back.

## 4 · The design, driven by challenges

**V1** (`v1`): API clients → API server (limiter library) → limit store (Redis, one script per request) · API server →
backend services · policy service + policy store, watched by the API servers; account team → policy service. Exact.
Flow `flow-v1`. Tech cards: limiter library (in process), limit store (Redis).

| # | Challenge | Break | Mechanism | Fix (view) | Rejected | Version | Push → second fix |
|:-:|---|---|---|---|---|---|---|
| 1 | 1,000 at 11:59:59, 1,000 at 12:00:00 | trace + `boundary` figure | M1 token bucket, lazy refill; options matrix (5 algorithms) | `v1-fix` (store), pseudocode | sliding-window log | zoom | two servers, the last token → one script per key, the store's clock; rejected GET-compare-SET |
| 2 | Take the round trip off the hot path (crux) | `v1-break` (store) | M2 leased tokens sized by demand; options A–E; `seq-share` | `v2`, `comp-api` whole, `share-fix`; tech: quota service | static split | **V2** | 40 % on four servers, one customer at 100 k/s → shares follow demand, hot key free, cold start N × c |
| 3 | The quota service is down | `down-break` | M3 static stability, bounded fallback; `seq-down` | `down-fix`, pseudocode | fail closed everywhere | zoom | policy service down + 50 restarts → `lkg-fix`: last-known-good on disk, start conservative |
| 4 | One quota, three regions | `v2-break` (quota) | M4 regional budgets rebalanced every 2 s; `seq-regions` | `v3` | one global counter | **V3** | the Atlantic partitions → each keeps its last budget; stricter, not looser; exact global = 70–150 ms |
| 5 | 10× burst for 30 s every hour (curveball) | `pol-break` | M5 scheduled, versioned, staged policy; `state-policy` | `pol-fix`, pseudocode; tech: policy service | hand-edited exceptions | zoom | 200 more, and a typo sets every limit to zero → validate, shadow, canary, rollback |
| 6 | "You limited us while we were under" | trace | false-limit SLI, decision record, explain | `v4`, `obs-fix`, cards, symptom pairs; tech: decision store | sampling the 429s | **V4** | the decision log drops records → counters reconcile the log; a canary customer |

## 5 · When you don't need all this

One Redis primary with a replica, one token-bucket script per request, policies in a config file (`alt`, ALTERNATE on the
store). Gives up: a round trip on every request, Redis on the critical path (must fail open), a hot key on one thread, no
global scope. **Crossover**: one shard runs ~100 k scripted ops/s; below ~50,000 requests/s at peak, in one region, with a
latency budget of a couple of milliseconds, ship it. We peak at 3 M/s with 1 ms: sixty times past it.

## 6 · Recap

`recap` badges: api `lease · floor` · store `exact keys` · quota `leases by demand` · peer `budgets, 2 s` · pol `staged
versions` · dstore `false-limit SLI`. Stack table from `stack.json`; six mistakes; six follow-ups (billing from the limiter ·
cost-weighted endpoints · concurrency limits · protecting the backend · build or buy · week one).

## C4 plan (`workspace.dsl` + `views.json`)

| View key | From | Overlays | Used on |
|---|---|---|---|
| c4-context | exported (cross grid) | steps | ch1 |
| containers | exported (master, grid 3 × 4) | — | Markdown only |
| v1 · flow-v1 · v1-fix · v1-break | containers | hide quota, peer, dlog, dstore · flow · fix / breaks store | ch4, 4.1, 4.2 |
| v2 · v2-break | containers | hide peer, dlog, dstore · new quota · breaks quota | 4.2, 4.4 |
| v3 · pol-break · pol-fix | containers | hide dlog, dstore · new peer · breaks / fix pol, pdb | 4.4, 4.5 |
| v4 | containers | new dlog, dstore | 4.6 |
| comp-api | exported (grid 4 × 5, 5 grouped steps) | — | 4.2, shown whole before the first zoom |
| share-fix · down-break · down-fix · lkg-fix · obs-fix | comp-api | keep (rest dimmed) + breaks / fix, via zoom() | 4.2, 4.3, 4.6 |
| recap | containers | badges | ch6 |
| alt | exported | alternate store | ch5 |

## Canon check

| Canonical point | Covered at, or dismissed because |
|---|---|
| Algorithms compared; the fixed-window boundary burst | challenge 1 trace, figure and options matrix |
| Sliding-window log memory cost | challenge 1 options and Rejected line |
| Token bucket for rate + burst | challenge 1 mechanism and pseudocode |
| Atomic check-and-decrement (Lua), no read-then-write | challenge 1 push |
| Where the counter lives: shared, local, local + async | challenge 2 options matrix |
| 1,000 ÷ 500 = 2 per server | chapter 2 and challenge 2 Rejected line |
| Hot keys on one shard | chapter 2, challenge 2 push |
| Fail open vs closed, decided explicitly | challenge 3 |
| Multi-region: global exact is a cross-region round trip | challenge 4 |
| Response headers, Retry-After | chapter 3 wire format |
| Limiter availability over accuracy | thesis, hook, challenge 3 |
| Per-decision observability, "why was I limited?" | challenge 6 |
| Price the shared-store dependency | chapter 2 (30 primaries), chapter 5 |
| Curveball: scheduled burst; special cases as a liability | challenge 5 |
| Week-one plan (EM) | recap follow-up |
| DDoS protection at the edge | dismissed aloud: a different layer, before the API servers |
| Billing-accurate counts | dismissed aloud in scope; recap follow-up |
| Concurrency limits, load shedding | recap follow-ups (part 12.4, 12.5) |

## Budget

| Chapter | Minutes | Words | Logical slides |
|---|---|---|---|
| 1 · Prompt + context | 6–7 | ~900 | 15 |
| 2 · Estimates | 3–4 | ~450 | 5 |
| 3 · API + data | 4 | ~450 | 6 |
| 4 · Design + challenges | 30–34 | ~4,000 | ~75 |
| 5 · Alternate | 1–2 | ~180 | 3 |
| 6 · Recap | 4 | ~450 | 6 |
