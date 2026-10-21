# Archetype E · Search, geo & ML

**SD-36 – SD-43.** Slice with `grep -n '^### SD-38' questions/E-search-geo-ml.md`, then Read with
`offset`. Do not read this file whole.

**What this archetype tests as a family:** **precomputation under a latency budget.** Every question
here is answered at read time in tens of milliseconds over a corpus far too large to scan, which means
the real design work happens offline. The recurring probe: *"what did you compute in advance, and how
stale is it?"*

---

### SD-36 · Web crawler   [T1 · G★ M]

**Read aloud:** *"Design a web crawler that fetches and keeps fresh a few billion pages."*

**Crux.** **The frontier** — the prioritised queue of what to fetch next — plus **politeness**, the
per-host rate constraint that makes the naive "parallelise everything" answer illegal. Freshness
versus coverage is the strategic trade-off underneath both.

**If they ask:**

| Question | Answer |
|---|---|
| Corpus? | 5B pages to start, growing |
| Rate? | Ask them to derive it. If pushed: recrawl the corpus monthly, so ~2,000 pages/sec sustained |
| Page size? | ~100 KB HTML average |
| Freshness? | News in minutes, most pages monthly. **They should ask this** — uniform recrawl is the weak answer |
| Politeness? | Respect `robots.txt` and no more than 1 request/sec to any host |
| JavaScript rendering? | Out of scope initially; ask what it would change if they raise it |
| Storage? | Keep raw pages; assume indexing is a separate system |
| Duplicates? | The web is ~30% duplicate content |

**Listen for:**
- **The frontier as a prioritised, persistent structure**, not a FIFO queue — priority by
  importance and expected change rate.
- **Politeness enforced by partitioning the frontier by host**, so all URLs for one host are handled
  by one worker with its own rate limiter. **← The senior insight: politeness is a per-host
  serialisation constraint, so the frontier must be sharded by host, not by URL hash.** Sharding by
  URL makes politeness require cross-worker coordination on every fetch.
- **URL-seen dedup** at billions of scale — a bloom filter or similar, with the false-positive
  consequence stated (you skip a page you've never crawled) and how to bound it.
- **Content dedup** distinct from URL dedup — near-duplicate detection by content fingerprint.
- **`robots.txt` fetching and caching**, and treating it as a hard gate.
- **Politeness and the long tail**: most hosts have few pages, a few have millions, so worker load is
  extremely skewed and needs rebalancing.
- **Adaptive recrawl**: track observed change frequency per page and schedule accordingly, rather than
  a uniform interval — the biggest single efficiency win available.
- **Crawler traps**: infinite calendars, session IDs in URLs, cycles; needs depth limits, URL
  normalisation and per-host budgets.
- **DNS as a bottleneck** and caching it — a real detail that distinguishes people who have done this.
- Distributed operation: workers, the frontier as a shared service, checkpointing so a restart doesn't
  lose progress.

**Probe ladder:**
- *Requirements:* "Does every page need the same freshness? What does that change?" · "What's out of
  scope?"
- *Estimation:* "5B pages monthly — what's your fetch rate, your bandwidth, and your storage?"
  (≈2,000/s, ≈200 MB/s, ≈500 TB raw before compression) · "How much memory does 'have I seen this
  URL' cost for 50B URLs, exactly?" (the number that forces a probabilistic structure)
- *Design:* the walk of one URL from discovery to stored page · "What's in the frontier, per entry?"
- *Deep dives:* **"Politeness says one request per second per host. You have 5,000 workers. How does
  worker 3,000 know that worker 12 just hit example.com?"** (the crux — the good answer restructures
  the sharding rather than adding coordination) · "One host has 200 million pages. What happens?" ·
  "Your bloom filter says you've seen a URL you haven't. What's the impact and is it acceptable?" ·
  "A site generates infinite unique URLs. What stops you?" · "How do you decide what to recrawl
  today?"
- *EM bar:* "How would you know the crawler was silently missing a chunk of the web?" · "What's the
  bandwidth bill, and what's the cheapest way to halve it?" (conditional requests and content hashing
  — most recrawls should transfer nothing) · "How do you split this across three teams?"

**Curveball:** *"Half the web now needs JavaScript execution to get content."* Tests whether they can
reason about a 50–100× cost increase per page and respond with selective rendering rather than
rendering everything.

**Weak / Strong / Exceptional.** *Weak* — a URL queue, N threads fetching, a database of seen URLs,
uniform recrawl, politeness as a sleep. *Strong* — host-sharded prioritised frontier, probabilistic
URL dedup with bounded error, robots caching, trap defences, adaptive recrawl, checkpointing.
*Exceptional* — derives the rate and storage numbers and lets them drive the architecture, restructures
sharding to make politeness free, handles the host-size skew, uses conditional fetches to cut
bandwidth, and monitors coverage as a product SLI.

**Traps.** Sharding the frontier by URL hash and then needing global coordination for politeness.
Storing seen-URLs in a database and doing a lookup per discovered link (the QPS is enormous). Treating
freshness as a single global interval.

---

### SD-37 · Search indexing & serving   [T2 · G★ M A]

**Read aloud:** *"Design search over a billion documents — indexing new content and serving queries in
under 200 ms."*

**Crux.** **Sharding by document versus by term**, and the multi-tier retrieval funnel that makes
ranking affordable: you cannot score a billion documents per query, so the design is about how few you
can get away with scoring.

**Numbers if asked:** 1B documents, 100k queries/sec, p99 under 200 ms, index updated within 5 minutes
of a document changing, average query 3 terms, results need ranking not just matching, 10 KB average
document.

**Listen for:** **inverted index** with posting lists, and compression of those lists (delta/gap
encoding) as the thing that makes it fit · **document sharding (each shard holds all terms for a
subset of docs)** as the standard choice, with the reason: every shard answers every query in parallel
and results merge, whereas term sharding concentrates hot terms and makes multi-term queries a
cross-shard intersection · **scatter-gather with a stated tail-latency problem** — p99 of the slowest
of 50 shards is much worse than the p99 of one, so hedged/backup requests or a deadline with partial
results · **a retrieval funnel**: cheap candidate retrieval (thousands) → cheap ranker (hundreds) →
expensive ranker (tens), with a latency budget per stage · **index freshness** via a small mutable
recent-documents index searched alongside the large immutable one, merged periodically —
**this is the standard answer to "5-minute freshness over a billion documents"** · replication for both
QPS and availability · **caching** of common queries and their result sets · deletions as tombstones
filtered at query time.

**Probes:** *"Shard by document or by term? Defend it."* · *"You query 50 shards in parallel; one is
slow. What's your p99, and what do you do about it?"* · *"A document changes. When is it searchable,
and what did you build to make that fast?"* · *"How many documents do you actually score per query, and
how do you get from a billion to that number?"* · *(EM bar)* *"What's your relevance SLI — how do you
know a change made search worse?"*

**Weak / Strong / Exceptional.** *Weak* — a database with a text index, ranked by a single field,
reindexed nightly. *Strong* — compressed inverted index, doc-sharded scatter-gather, retrieval funnel
with a latency budget, fresh-index overlay, caching. *Exceptional* — treats tail latency of
scatter-gather as a first-class problem, sizes each funnel stage against the budget, and has a
relevance measurement story separate from the systems metrics.

---

### SD-38 · Typeahead / autocomplete   [T1 · G★ M A]

**Read aloud:** *"Design search autocomplete — suggestions appear as the user types."*

**Crux.** **The latency budget is brutal (sub-50 ms, on every keystroke) and the query volume is
multiples of actual searches**, so *nothing* can be computed at request time. The whole design is
"precompute the top suggestions per prefix and serve them from memory", and the interesting parts are
how the precomputation stays fresh and how far down the funnel the request gets to travel.

**If they ask:**

| Question | Answer |
|---|---|
| Latency? | Under 50 ms end to end, including network. This is the hard constraint |
| Volume? | 500k keystrokes/sec — roughly 5× the search QPS |
| Suggestions? | Top 10 per prefix |
| Corpus? | 100M distinct historical queries, heavy long tail |
| Freshness? | A trending query should appear within ~10 minutes. Breaking news within 1 minute if they ask |
| Personalisation? | Not in v1. Offer it as the curveball |
| Typos? | Should tolerate one typo. Ask what it costs them |
| Languages? | Multiple, including non-space-delimited (raise only if they ask) |

**Listen for:**
- **Precomputed top-K per prefix**, stored as a map from prefix → suggestion list. The
  trie-with-cached-top-K-at-each-node formulation is the classic answer; a flat key-value map of
  prefix → list is simpler and often better, and noticing that trade-off is a good signal.
- **The estimate that justifies it**: 100M queries, average prefix count ~20 each, top 10 per prefix →
  a few billion entries if naive, which forces truncation (prefixes of length ≥2 or 3 only, since
  single-letter prefixes are useless anyway).
- **Serve from memory, sharded by prefix**, with the whole structure replicated so any node can answer.
- **Client-side behaviour as part of the design**: debouncing keystrokes, caching prefixes locally,
  and cancelling in-flight requests — this cuts the 500k/s substantially and candidates who own the
  client are thinking about the whole system.
- **Offline pipeline** aggregating query logs into the prefix map, published as an immutable versioned
  snapshot and atomically swapped — **never mutated in place**, so a bad build is a rollback.
- **A separate fast path for trending terms** layered on top of the slow snapshot, because a 6-hour
  batch cannot deliver breaking news.
- **Filtering** — offensive, personal-data-leaking, and legally-problematic suggestions are a genuine
  product requirement, and a strong candidate raises safety unprompted.
- Typo tolerance and what it costs (edit-distance expansion multiplies the prefix space; the cheaper
  answer is precomputing common misspellings from logs).

**Probe ladder:**
- *Requirements:* "What are you not doing in v1?" · "Who decides what a bad suggestion is?"
- *Estimation:* "100M queries — how many prefixes, and how much memory for the whole map?" · "500k
  keystrokes a second — how much of that can you make disappear before it reaches your servers?"
- *Design:* the walk of one keystroke, including the client · "What's the exact key and value in your
  store?"
- *Deep dives:* **"Nothing can be computed at request time. Prove your design honours that."** · "A
  query starts trending in the last 60 seconds. When does it appear, and via which path?" · "How do
  you deploy a new suggestion map to 200 nodes without a latency spike?" · "The user types 'a'. What
  do you return and why is that question a trap?" · "Add typo tolerance. What happens to your memory
  and your latency?"
- *EM bar:* "What's the SLI — latency, or suggestion quality? How do you measure the second one?" ·
  "A suggestion causes a PR incident. What's the mechanism to remove it in 5 minutes?" (needs a
  blocklist with its own fast path, designed in advance) · "What's the cost per thousand keystrokes?"

**Curveball:** *"Now personalise it — the user's own recent searches should rank higher."* Tests
whether they keep the shared precomputed layer and merges a small per-user list client-side or at the
edge (correct), or tries to precompute per user (impossible — 500M × prefixes).

**Weak / Strong / Exceptional.** *Weak* — a `LIKE 'prefix%'` query against a database, ordered by
count, at request time. *Strong* — precomputed prefix→top-K served from memory, sharded and
replicated, offline pipeline with atomic snapshot swaps, client debouncing, trending fast path.
*Exceptional* — derives the memory footprint and truncates prefixes accordingly, layers trending over
snapshots, treats safety filtering and the emergency-removal path as first-class, and merges
personalisation without touching the shared layer.

**Traps.** Querying a database per keystroke. Personalising by precomputation. Forgetting that the
client is part of the latency budget and the traffic volume.

---

### SD-39 · Nearby / ride matching (geo)   [T1 · U★ G M]

**Read aloud:** *"Design the system that matches riders to nearby drivers — drivers moving constantly,
riders requesting a ride and expecting a match in seconds."*

**Crux.** **Two problems, and candidates conflate them.** (1) A very high-write geospatial index over
moving objects. (2) **Matching under contention** — the same driver being offered to several riders at
once, which is a distributed-consistency problem, not a geo problem. The second is the harder one and
the one most candidates never reach on their own.

**If they ask:**

| Question | Answer |
|---|---|
| Scale? | 5M active drivers, 1M concurrent ride requests at peak, one large city is 50k drivers |
| Location updates? | Every 4 seconds per active driver → ~1.2M writes/sec |
| Match latency? | Under 5 seconds from request to a driver being offered |
| Search radius? | Start at 2 km, expand if nothing found |
| Match criteria? | Nearest is fine for v1; ETA-based is better. Ask which they want and why |
| Consistency? | **A driver must never be assigned to two riders.** Give this only if they ask; if they don't ask, it becomes the curveball |
| Geography? | Cities are independent — no cross-city matching |

**Listen for:**
- **A geospatial index**: geohash, S2 cells, or a quadtree, and *why* — the key property is turning a
  2-D proximity query into a **1-D range scan over cell IDs**, which any ordinary store can serve.
- **Cell size trade-off**: large cells mean scanning many irrelevant drivers, small cells mean querying
  many neighbouring cells. Naming the trade-off matters more than the choice.
- **Boundary handling** — the nearest driver may be in an adjacent cell, so a query must cover
  neighbours; this is the classic bug.
- **Location writes kept out of durable storage**: current location is ephemeral, in-memory,
  overwrite-only, and losing it is recoverable within one update interval. **← The senior insight: a
  driver's current location has a 4-second lifespan, so it must not be written like durable data**;
  candidates who put 1.2M writes/sec into a replicated database and then try to scale it have taken
  the wrong turn, and the estimate is what should reveal it.
- **Sharding by city/region**, which makes the whole problem embarrassingly parallel and bounds every
  query — a genuinely important simplification.
- **Matching as a two-phase operation**: find candidates from the index, then **atomically claim** a
  driver (a lock, a conditional update, or a per-driver single-writer) before offering the ride.
- **The offer state machine**: offered → accepted/declined/timed-out, with a timeout releasing the
  driver, and idempotency on accept.
- **Batch matching versus greedy**: waiting a few seconds and solving a small assignment problem beats
  first-come-first-served on global efficiency — a strong optimisation to raise.
- Surge/supply imbalance as a product lever, and the empty-result path (expand radius, then give up
  gracefully).

**Probe ladder:**
- *Requirements:* "What must never happen?" (fishing for double-assignment) · "What's out of scope?"
- *Estimation:* **"1.2 million location writes a second. Where do they go?"** (the decisive probe —
  if they say "a database", ask what that costs and let them find it) · "How many drivers in a 2 km cell
  in Manhattan at 6 p.m.?"
- *Design:* the walk of one ride request from tap to driver notification · "What's the key in your geo
  index?"
- *Deep dives:* **"Two riders request at the same instant and your index returns the same driver to
  both. Walk me through it."** (the crux) · "The nearest driver is 50 metres away but across a cell
  boundary. Does your query find them?" · "Your location store loses a node with 50,000 drivers on
  it. What breaks and for how long?" · "Nearest by straight line is 200 m away but across a river.
  What now?" (ETA vs distance — a routing dependency they should acknowledge rather than solve) ·
  "A driver's app crashes after accepting. What happens to the rider?"
- *EM bar:* "What's the SLI for matching, and what's the business metric it maps to?" · "What's the
  cost of 1.2M writes/sec, and what's the cheapest correct design?" · "Which part would you build
  first, and what would you fake?"

**Curveball:** If they already handled double-assignment, use: *"Drivers can now be offered a queued
next-ride while still finishing the current one."* Tests whether their claim mechanism generalises from
binary availability to capacity.

**Weak / Strong / Exceptional.** *Weak* — driver locations in a relational table, a query computing
distance across all rows, nearest driver returned with no claim step. *Strong* — cell-based index with
neighbour queries, ephemeral in-memory location store, region sharding, atomic claim plus an offer
state machine with timeouts. *Exceptional* — uses the write-rate estimate to justify the ephemeral
store, treats matching as a contention problem distinctly from the geo problem, raises batch matching
as an efficiency lever, and separates ETA from distance honestly.

**Traps.** Durably storing every location update. Ignoring the claim step entirely (the most common
failure — the design "works" until two riders collide). Building cross-city generality nobody needs.

---

### SD-40 · Maps routing & ETA   [T2 · G★ U]

**Read aloud:** *"Design driving directions with accurate ETAs over a continental road network, with
live traffic."*

**Crux.** **Dijkstra over a continental graph per request is far too slow**, so routing is a
**preprocessing** problem — and live traffic invalidates the preprocessing, which is the real tension.

**Numbers if asked:** 100M road segments continent-wide, 50k route requests/sec, p99 under 100 ms,
traffic updated every 2 minutes from probe data, ETAs must be within 10% for 90% of trips, routes must
respect turn restrictions and vehicle type.

**Listen for:** **hierarchical routing** as the core idea — long routes travel via a small
higher-level graph (motorways) and only the endpoints use detailed local graphs, cutting the search
space by orders of magnitude · **precomputation** (contraction hierarchies, transit-node routing, or
precomputed region-to-region costs) with the honest statement that preprocessing takes hours and must
be rebuilt, which is exactly why live traffic is hard · **live traffic as edge-weight overlays**
applied at query time on top of static preprocessed structures, rather than reprocessing the graph ·
**graph partitioning by geography** with boundary/cut nodes, and caching routes between boundary pairs
· **ETA as a prediction problem** distinct from routing: historical speed profiles by time-of-day and
day-of-week, plus live conditions, plus segment-level models · probe-data ingestion and privacy
(aggregate, never per-user traces) · caching of popular route prefixes and the observation that route
requests are extremely skewed.

**Probes:** *"Straight Dijkstra over 100M edges — how long, and why is that unacceptable?"* · *"Your
preprocessing takes 6 hours. Traffic changes every 2 minutes. Reconcile that."* · *"A motorway closes
suddenly. When do routes stop using it?"* · *"How do you know your ETAs are wrong?"* (compare
predicted against actual on completed trips — the feedback loop is the answer) · *(EM bar)* *"What's
the cost of the preprocessing pipeline, and how would you measure whether it's worth it?"*

**Weak / Strong / Exceptional.** *Weak* — Dijkstra or A* over the full graph per request, static
weights, ETA as distance ÷ speed limit. *Strong* — hierarchical/preprocessed routing, traffic as a
query-time overlay, geographic partitioning, ETA from historical profiles plus live data, caching.
*Exceptional* — states the preprocessing-versus-freshness tension explicitly and resolves it with
overlays, treats ETA accuracy as a measured feedback loop, and handles sudden closures as a distinct
invalidation path.

---

### SD-41 · Recommendation serving & feature store   [T1 · M★ N★ A]

**Read aloud:** *"Design the serving system behind recommendations — 'what should we show this user
next' — for a hundred million daily users."*

**Crux.** **You cannot score a million candidates per request in 100 ms**, so the design is the
**funnel** — cheap retrieval, then progressively more expensive ranking over fewer items — plus
**feature freshness and train/serve consistency**, which is where these systems actually fail in
production.

**If they ask:**

| Question | Answer |
|---|---|
| Scale? | 100M DAU, 50k recommendation requests/sec |
| Catalogue? | 10M items, ~50k new per day |
| Latency? | Under 100 ms for the whole recommendation call |
| Freshness of behaviour? | A user's action should influence recommendations within a minute |
| Models? | Assume the model artifacts exist; **you are designing the serving system, not the model** — say this if they start designing a model |
| Cold start? | Yes, both new users and new items |
| Business rules? | Yes — diversity, promoted content, and hard exclusions |

**Listen for:**
- **The funnel with a latency budget per stage**: candidate generation (millions → ~1,000, must be
  cheap — ANN over embeddings, plus precomputed lists and heuristic sources), light ranking (1,000 →
  ~100), heavy ranking (~100 → ordered), then business-rule reranking. Stage sizes and budgets stated.
- **Multiple candidate sources merged**, not one — recent-popular, embedding-similar, followed-authors,
  and a fresh-content source to solve item cold start.
- **A feature store with an online and offline half**, and the crucial property: **the same feature
  definitions and values feed training and serving.** **← The senior insight: train/serve skew is the
  dominant failure mode of production ML, and it is a systems problem, not a modelling one.** Listen
  for point-in-time correctness in training data — using a feature value the model would not have had
  at prediction time silently inflates offline metrics.
- **Real-time features** (what the user did in the last minute) served from a low-latency store fed by
  a stream, versus batch features precomputed nightly — with the freshness/cost trade-off named.
- **Embedding index (ANN)** with the accuracy/latency trade-off and the operational problem of
  rebuilding and hot-swapping the index as items are added.
- **Model deployment**: versioned artifacts, shadow/canary evaluation, and A/B as the only real
  arbiter of quality (links to SD-06).
- **Fallbacks at every stage**: if heavy ranking times out, serve the light-ranked list; if the model
  server is down, serve a popularity baseline. A recommendation system must degrade, never fail.
- **Feedback loop and its pathologies** — logging impressions and outcomes for training, and the
  popularity-bias/echo-chamber effect of training on your own output.
- **Exclusions must be applied last and reliably** (already-seen, blocked, legally restricted), because
  a ranking mistake is a bad experience and an exclusion mistake is an incident.

**Probe ladder:**
- *Requirements:* "What's the actual objective, and who decides it?" · "What must never be
  recommended?"
- *Estimation:* "10M items, 100 ms budget. How many can you score with a heavy model, and what's your
  per-request compute?" · "50k req/s of model inference — what does that hardware cost?"
- *Design:* the walk of one request through every stage with a millisecond budget attached · "Where do
  features come from at serving time?"
- *Deep dives:* **"Your offline metrics improved 5% and the A/B test was flat. Give me three
  systems-level explanations."** (train/serve skew, point-in-time leakage, a feature unavailable at
  serving — this is the best probe on the sheet and it separates people who have shipped ML from
  people who have read about it) · "A user watches something now. How does that reach the next
  request within a minute?" · "The heavy ranker is at 200 ms. What do you serve?" · "A brand-new item
  has no interactions. How does it ever get shown?" · "Your ANN index needs rebuilding with 50k new
  items. How, without a latency spike?"
- *EM bar:* "What's the cost per thousand recommendations, and where would you cut?" · "How do you know
  quality regressed, given nobody complains — they just engage less?" · "Split this across three teams
  — where are the seams?" (retrieval / ranking / feature platform is the natural cut, and the contract
  between them is the interesting part)

**Curveball:** *"The model must now run on-device for privacy reasons."* Tests whether they understand
which parts of the funnel can move (light ranking, exclusions) and which cannot (retrieval over 10M
items), and whether they can reason about the feature-availability change.

**Weak / Strong / Exceptional.** *Weak* — score all items with one model at request time; features
fetched ad hoc from production databases; no fallback. *Strong* — staged funnel with budgets, multiple
candidate sources, feature store with online/offline parity, ANN retrieval, model versioning,
degradation paths. *Exceptional* — names train/serve skew and point-in-time correctness unprompted,
prices inference hardware, designs exclusions as a reliability-critical last stage, and treats the
feedback loop's biases as a design problem.

**Traps.** Designing the model instead of the system (redirect: *"assume the model exists"*). Fetching
features from production service databases at serving time (couples ML latency to unrelated services).
Believing offline metrics are sufficient evidence.

---

### SD-42 · LLM inference serving / RAG platform   [T1 · G M MS A]

**Read aloud:** *"Design the platform that serves a large language model to internal product teams —
including retrieval over our own documents."*

**Crux.** **GPU economics.** Inference is memory-bandwidth-bound and GPUs are the dominant cost, so
throughput comes from **batching** — which trades latency for utilisation. Every serious decision in
this design follows from that tension, and cost per request is a first-class requirement rather than
an afterthought.

**If they ask:**

| Question | Answer |
|---|---|
| Traffic? | 2,000 requests/sec at peak, very bursty; 20 internal teams |
| Prompt / output size? | ~2,000 input tokens, ~500 output tokens typical |
| Latency? | Time-to-first-token under 500 ms; streaming after that |
| Model? | A hosted open-weights model on your own GPUs. Ask what would make them use an API instead |
| Corpus for retrieval? | 50M documents, updated continuously; permissions vary per user |
| Availability? | 99.9% |
| Cost? | **Explicitly a first-class requirement.** They should ask; if they don't, raise it in the wrap |

**Listen for:**
- **Continuous/dynamic batching** rather than static batching — requests join an in-flight batch as
  others finish, which is the single biggest throughput lever, and the latency cost stated.
- **The KV cache** as the memory constraint that determines how many concurrent sequences fit on a
  GPU, and therefore the real capacity limit. **← The senior insight: capacity here is bounded by
  GPU memory for KV cache, not by FLOPs**, and someone who reaches that has understood the workload.
- **Prefill versus decode** having completely different performance profiles (compute-bound versus
  memory-bandwidth-bound), and the scheduling consequence.
- **Streaming responses** as a product and systems requirement — time-to-first-token and
  inter-token latency as the two SLIs, not one end-to-end number.
- **Admission control and queueing** with per-team quotas, since a burst cannot be absorbed by
  autoscaling (GPU cold starts are minutes, not seconds) — **so the design must shed or queue, and
  say which.**
- **Retrieval**: chunking strategy, embedding pipeline, a vector index with the ANN accuracy/latency
  trade-off, hybrid keyword+vector retrieval, and reranking.
- **Permission-aware retrieval** — filtering candidates by what *this* user may see, and the trap of
  filtering after retrieval (you get fewer results than requested, or leak counts). A strong candidate
  raises that a RAG system trivially becomes a data-exfiltration path.
- **Caching**: exact-prompt cache, prefix/prompt caching for shared system prompts (a large real
  saving), and semantic caching with its correctness risk.
- **Cost per request computed** and attributed per team; smaller models or quantisation for cheap
  requests; routing by request class.
- **Evaluation and safety** as platform functions: regression evaluation on model or prompt change,
  output filtering, and abuse/prompt-injection handling, plus logging that doesn't retain sensitive
  prompts indefinitely.
- **Model version rollout** with shadow evaluation, since "the model got worse" is not detectable by
  standard monitoring.

**Probe ladder:**
- *Requirements:* "What's the cost ceiling per request, and who pays?" · "What's out of scope?"
- *Estimation:* "2,000 req/s at 500 output tokens — what's your tokens/sec, and how many GPUs is
  that?" · "What does one request cost you, roughly?" · "How many concurrent sequences fit in 80 GB?"
- *Design:* the walk of one request from API call to first streamed token · "Where's the queue, and
  what's its policy?"
- *Deep dives:* **"Traffic triples in 30 seconds. Autoscaling GPUs takes four minutes. What
  happens?"** (queue, shed by priority, degrade to a smaller model — anything but "scale up") ·
  "Batching improves throughput 5× and hurts p99. How do you choose the batch policy?" · "A user
  retrieves a document they shouldn't see. Where did your design fail?" · "The model is swapped for a
  new version and quality drops subtly. How do you find out?" · "50M documents, continuously updated
  — how does the index stay current?"
- *EM bar:* "What's the monthly bill, and what are the three levers?" (prefix caching, smaller model
  routing, quantisation/batch tuning) · "Twenty teams, one GPU pool. What's the quota and
  prioritisation model?" · "When would you stop running this and buy an API instead?" — a genuinely
  good EM question and the honest answer is usually *"below a utilisation threshold, buying wins."*

**Curveball:** *"Legal requires that no prompt or response leaves our infrastructure and that we can
prove which documents informed any given answer."* Tests provenance/citation design and audit
logging, and whether they had already ruled out third-party APIs.

**Weak / Strong / Exceptional.** *Weak* — a model server behind a load balancer, autoscale on CPU,
retrieval as a vector-DB lookup with no permission model, no cost analysis. *Strong* — continuous
batching, KV-cache-aware capacity planning, streaming with two latency SLIs, admission control with
quotas, hybrid retrieval with reranking, permission-aware filtering, prompt caching, cost per request.
*Exceptional* — treats GPU memory as the binding constraint and designs capacity from it, has a
concrete answer to burst traffic that isn't autoscaling, designs permission filtering into retrieval
rather than after it, builds evaluation into model rollout, and has a defensible build-versus-buy
threshold.

**Traps.** Assuming GPU autoscaling responds like stateless web autoscaling. Post-filtering retrieval
results by permission. Quoting a single end-to-end latency number for a streaming system. Ignoring
cost, which for this system is the primary constraint.

---

### SD-43 · Abuse / fraud detection in real time   [T2 · M A★]

**Read aloud:** *"Design a system that blocks fraudulent or abusive actions in real time — before the
action completes."*

**Crux.** It is **inline on the critical path with a hard latency budget**, and the adversary adapts.
That combination means the design needs a fast deterministic layer, a slower model layer, an
asynchronous layer that can act after the fact, and a feedback loop that closes in hours, not
quarters.

**Numbers if asked:** 50k decisions/sec, budget under 50 ms inline, false positives are extremely
expensive (blocking a real customer), false negatives cost money directly, attack patterns change
within hours, labels arrive days later via chargebacks or reports, and decisions must be explainable
for appeals and regulators.

**Listen for:** **layered defence**: cheap deterministic rules and velocity checks inline (milliseconds),
a model scoring inline within budget, and asynchronous deeper analysis that can reverse or freeze
afterwards · **the async tier as the pressure valve** — accepting that not everything can be decided in
50 ms is the mature position · **features requiring aggregation over recent history** (counts per
account/device/IP over sliding windows) served from a low-latency store, which is the real engineering
work · **fail-open versus fail-closed decided per action class** — fail-open on a login check, likely
fail-closed on a large payout, and the reasoning behind the split · **explainability and an appeals
path** as product requirements, plus an audit record of why each decision was made ·
**adversarial adaptation**: rules deployable in minutes without a code release, shadow mode for new
rules, and measuring the false-positive rate before enforcing · **delayed labels** making online
metrics hard, so proxy metrics and shadow evaluation matter · precision/recall framed as a business
trade-off with the PM rather than a technical setting.

**Probes:** *"Your scorer is at 200 ms and the budget is 50. What do you do?"* · *"A new attack pattern
appears at 2 a.m. What's the fastest path to blocking it, and what's the risk of that path?"* · *"You
block 5,000 legitimate customers in an hour. What happens, and what did you build to notice?"* · *"The
label arrives 30 days later. How do you know today's model is working?"* · *(EM bar)* *"Who owns the
false-positive rate — you, or the fraud team? How is that decided?"*

**Weak / Strong / Exceptional.** *Weak* — one model called synchronously, rules in application code
requiring a deploy, no appeals path, no false-positive monitoring. *Strong* — layered inline/async
design, velocity features from a fast store, hot-deployable rules with shadow mode, explicit fail
policy per action class, explainability. *Exceptional* — treats the async tier as a deliberate
architectural concession, closes the feedback loop against delayed labels, monitors false positives as
a first-class SLI, and frames the precision/recall dial as a business decision with named owners.
