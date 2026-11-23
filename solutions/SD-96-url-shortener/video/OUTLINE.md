- [x] outline approved  - [x] design  - [x] diagrams  - [x] slides  - [x] script  - [x] video  - [x] publish

# SD-96 · URL shortener — reference-solution video outline

Target level: staff (manager layer AUX) · Target length: 72 min (65–80) · Word budget: 8,800 (≈ 0.49 s a word with the
2026-11-17 pacing beats, measured on SD-94)

Generic content only: no company, product or vendor figures. Every number is arithmetic from the stated inputs and carries a label.
The retired 20-minute classics mock round 3 was the short version of this question; this video replaces it as
the reference.

## Thesis and definition

- **Thesis** (key-line voice): *A URL shortener is a read path with a write path attached: make codes unique without a lock per
  create and unguessable without a lookup, keep the redirect to one memory read, and let nothing else — counting, abuse, analytics —
  stand between the click and the answer.*
- **Definition to say aloud**: *A URL shortener maps a short, unique, hard-to-guess code to a long URL, answers a redirect for that
  code in milliseconds from anywhere, and can withdraw a code everywhere within a stated time.* Load-bearing clauses: **unique**
  (the store, not the app, decides), **hard to guess** (a code is not a secret, but must not be enumerable), **in milliseconds from
  anywhere** (the redirect is the product), **withdraw everywhere within a stated time** (every cached copy is a liability).
- **Hook**: Everyone has drawn this one: a hash, a table, a cache. Interviewers still ask it at every level because the grade is on the
  three places where it is not simple: two servers must never hand out the same code without coordinating on every create; one viral
  link turns a read-heavy system into a single hot key; and the things beside the redirect — click counts and phishing takedowns —
  quietly fight the cache that makes it fast.

## 0 · What this question grades

| Axis | Weak signal | Strong signal |
|---|---|---|
| Requirements | "Shorten and redirect", no numbers, no lifetime, no abuse | Read:write ratio, lifetime, custom aliases, analytics granularity and the takedown time asked before drawing |
| Correctness | Hash the URL and take six characters; check-then-insert for aliases | Code length from arithmetic; counter ranges or random-with-retry with the collision maths; the primary key as the authority |
| Trade-offs | "Use Redis and a NoSQL store" | Options matrix for code generation with costs; 301 against 302 as a product decision; lossy analytics as a stated choice |
| Depth | Stops at "add a cache" | Hot key: in-process cache plus request coalescing; keyed permutation against enumeration; takedown through every copy |
| Operations | CPU and error rate | Synthetic create-then-redirect probe, hit rate against database load as a symptom pair, takedown latency as an SLI, cost per billion redirects |

## 1 · Requirements and scope

- **Clarifying questions and the interviewer's answers** (asked aloud, six):
  1. *How many links, how many clicks?* — 100 million new links a month; 10 billion redirects a month; a viral link can take 40,000
     clicks a second.
  2. *How long does a link live?* — Forever by default; an optional expiry date set by the creator.
  3. *Custom aliases?* — Yes, for paying users, first come first served.
  4. *Analytics?* — Clicks per link by day and by country, shown to the link owner. "Not billed today. Product may bill per click later."
     (Seeds challenge 6.)
  5. *Abuse?* — Phishing and malware links exist. "Legal wants a reported link dead everywhere within five minutes." (Seeds C5.)
  6. *Who calls us?* — Browsers following links, and an API for integrators who create links in bulk.
- **Functional requirements** (each gets a numbered flow):
  - FR1 · **Create**: long URL in, short link out; optional custom alias and expiry; idempotent for a retried request.
  - FR2 · **Redirect**: a request for a code gets the long URL as a redirect, or a not-found or gone page.
  - FR3 · **Count**: clicks per link per day per country, visible to the owner within minutes.
  - FR4 · **Withdraw**: an owner deletes, or trust and safety blocks, a link; it stops redirecting everywhere within five minutes.
- **Non-functional, with numbers** (initial targets): redirect p99 under 20 ms at the server, measured at the region; redirect
  availability 99.99 %; create p99 under 200 ms, 99.9 %; codes as short as the capacity allows; takedown everywhere within 5 min;
  counts may lag by minutes and may lose a tiny fraction of clicks (stated, until billing).
- **IN / OUT**: IN: create, redirect, custom aliases, expiry, analytics by day and country, takedown, bulk API with rate limits. OUT on
  purpose: the malware classifier itself (a service we call; SD-43), user accounts and billing, QR codes (a rendering of the same short
  link), link-in-bio pages, editing a link's target (said aloud: it changes the cache story; we'd treat it like a takedown plus create).
- **"The core is 3 things"**: a *code generator* that never collides, a *redirect path* that is one memory read, and a *side path* for
  counting and withdrawal that never sits in front of the redirect.

## 2 · Estimates

| Number | Arithmetic | Label | Decision it drives |
|---|---|---|---|
| Create rate | 10⁸ ÷ (30 × 86,400 s) ≈ **40/s**, peak ×10 = **400/s** | given → derived | Writes are tiny; one primary could take them. The hard part is uniqueness, not throughput |
| Redirect rate | 10¹⁰ ÷ 2.6 × 10⁶ s ≈ **4,000/s** average; viral peak **40,000/s** on one code | given → derived | Read:write 100:1; optimise the read path, and the peak is one key, not many |
| Links in ten years | 10⁸ × 12 × 10 = **1.2 × 10¹⁰** | derived | Sizes the code space |
| Code length | 62⁶ ≈ 5.7 × 10¹⁰ (only 4.7× headroom, and random codes collide far earlier); 62⁷ ≈ **3.5 × 10¹²** (≈ 290×) | derived | **Seven characters.** Six is possible only with a counter and no headroom for bulk users |
| Random-code collisions | birthday bound: with n = 1.2 × 10¹⁰ codes in a 3.5 × 10¹² space, a new random code collides with probability n ÷ N ≈ **0.34 %** at the end of year ten | derived | Random-with-retry works with a unique constraint; the retry rate is measurable and small |
| Storage | 1.2 × 10¹⁰ × ~500 B (code, URL averaging ~200 B, owner, dates, status, index overhead) ≈ **6 TB**, × 3 replicas = 18 TB | illustrative | Fits a sharded key-value or relational store easily; not the hard part |
| Cache working set | Say 2 % of links get 90 % of clicks: 2 × 10⁸ hot links × 500 B ≈ **100 GB** | illustrative, **to be measured** | A shared cache tier of a few nodes holds it; the database sees misses only |
| Database read load | 4,000/s × 1 % miss ≈ **40/s** average; a cold cache after a restart: up to 4,000/s | derived | The database is never on the hot path — except when the cache is cold (challenge 3) |
| One hot key | 40,000/s on one shared-cache shard, plus the other traffic on that shard | derived | One shard can take it, but the network hop and the shard's tail become every viral click's tail: in-process cache in front |
| Counter ranges | 400 creates/s ÷ ranges of 1,000 = **0.4 range allocations/s** | derived | The allocator is touched once per thousand links; it can be a small strongly consistent store |
| Analytics volume | 4,000 clicks/s × ~200 B event ≈ **0.8 MB/s**, ≈ 70 GB/day raw | illustrative | A log and a batch aggregator, not a counter on the link row |
| Takedown budget | 5 min = DB write + invalidation event (seconds) + in-process TTL 60 s + CDN cache 60 s + purge call | initial target | Every cache layer's lifetime has to fit inside five minutes, summed along the worst path |
| Latency budget (20 ms server) | parse 0.5 + in-process hit 0.05 or shared cache 1 + miss to DB 5 + write response 0.5 + emit click 0.1 ≈ **7 ms** worst case, spare 13 | initial target | Room for one miss; none for a synchronous analytics write |

## 3 · Theory

1. **Is / is not.** Is: a globally replicated, read-mostly key-to-value map with a write path that must assign unique keys. Is not a
   **hash function** (a hash of the URL is one way to make a key; it is not the system), not a **cache** (the map is the source of truth;
   the cache is a copy that can be wrong for a bounded time), not a **secret** (a short code can be guessed; links that must be private
   need authentication or a long random token), not a **CDN** (the CDN is a layer that can answer for us, and that we must be able to
   take back).
2. **Safety**: S1 · two different long URLs are never given the same code. S2 · a withdrawn code is never answered by any layer after
   the takedown bound. **Liveness**: L1 · a create always gets a code without waiting for another create. L2 · a redirect for a live code
   answers within the latency target, even under a viral peak or with the database down. L3 · every click is eventually counted,
   with a stated, measured loss.
3. **Central tension**: **speed of the answer against control over the answer.** Every layer that answers a redirect closer to the
   user (in-process, edge, the browser) makes it faster and cheaper and makes counting and takedown slower or impossible. Picture: the
   five layers from browser to database, latency falling to the left, control falling to the left; 301 lives at the far end.
4. **Mechanisms** (6). Property → how → failure ruled out → cost.

   | Mechanism | Protects | Rules out | Costs |
   |---|---|---|---|
   | **M1 Counter ranges plus base-62** (each create server leases 1,000 IDs from an allocator) | S1, L1 | Two servers handing out one code; a lock or round trip per create | Gaps when a server dies with an unused range (harmless at 290× headroom); codes are sequential unless M2 |
   | **M2 Keyed permutation** (a small Feistel network over the code space, with cycle walking) | Non-enumerability | Scrapers walking codes in order; codes that leak creation volume | A secret key to keep and rotate; not cryptographic secrecy for private links |
   | **M3 Unique constraint as the final authority** | S1 for custom aliases and random codes | Check-then-insert races | A conflict answer (409) the API must surface; a retry loop for random codes |
   | **M4 Cache-aside with in-process hot cache and request coalescing** | L2 | A cache miss storm on one key; every viral click paying a network hop | Bounded staleness per layer (which M6 must budget); memory on every redirect server |
   | **M5 Asynchronous click log** (local buffer → partitioned log → aggregator) | L2 and L3 | A counter update on the hot path; a hot row per viral link | Counts minutes late; a small stated loss on a crash (or a durable buffer if clicks are billed) |
   | **M6 Status plus invalidation plus bounded TTLs everywhere** | S2 | A blocked phishing link still answered by a cache or an edge | Short TTLs cost hit rate; a purge path to the CDN; 302 instead of 301 |

5. **Options matrix — code generation** (rows = approaches; columns = deciding properties; last column = fails when).

   | Approach | Unique without coordination per create | Length | Guessable? | Fails when |
   |---|---|---|---|---|
   | A · Hash of the URL, first 7 characters | No: truncation collides; needs check-and-retry | 7 | Hard to guess, but deterministic | Two users shorten the same URL and want separate stats or expiry; collisions need a probe loop anyway |
   | B · Random 7 characters, insert with retry | Yes, via the constraint (M3) | 7 | No | The space fills (0.34 % retry at year ten is fine); a slow store makes every retry visible |
   | C · One global counter, base-62 | Needs a round trip per create | 6–7 | **Yes, sequential** | The counter is a single point of failure and a bottleneck; codes leak volume |
   | **D · Counter ranges (M1) + keyed permutation (M2) + constraint (M3)** | Yes, one lease per 1,000 | 7 | No | The allocator is down longer than a range lasts (tens of seconds at peak, minutes on average) |
   | E · Time-based IDs (timestamp + machine + sequence) | Yes | 10–11 base-62 | Partly (time-ordered) | Codes too long for a "short" link |
   | F · Pre-generated pool of codes handed out from a queue | Yes | 7 | No | A second system to fill and monitor; a lost batch is wasted codes |

   **Pick: D**, with **B** as an honest equal (simpler, and the constraint does the work; say when you'd choose it: fewer than a few
   thousand creates a second and no need for short six-character codes). A, C, E, F greyed with their failure. **Gives up:** an allocator
   service to run and a key to manage, against B's simplicity.
6. **Failure catalogue**: F1 two servers, one code; a custom alias race → C1 · F2 codes walked in order → C2 · F3 one viral code; a cold
   cache after a restart → C3 · F4 a layer answering that we cannot see or recall (301, CDN) → C4 · F5 phishing still live after five
   minutes → C5 · F6 counting on the hot path; billed clicks → C6 · F7 a region or the database lost → C7 · F8 nobody notices a broken
   redirect → C8 · F9 a creator floods the bulk API: rate limit per key (SD-25), covered on the API slide, not a challenge.

## 4 · API and entities

| API | Serves | Reads / writes | Wire-format notes |
|---|---|---|---|
| `POST /v1/links {url, alias?, expiresAt?}` + `Idempotency-Key` → `201 {code, shortUrl}` | FR1 | writes **Link** | 409 on an alias that exists; 422 on a blocked URL; the key makes a retried bulk call harmless |
| `GET /{code}` → `302 Location: …` · `404` · `410 Gone` | FR2 | reads **Link** (cache first) | `Cache-Control: private, max-age=0` by default; 410 for a withdrawn code so crawlers stop |
| `GET /v1/links/{code}/stats?from&to&by=day,country` | FR3 | reads **DailyCount** | Says how fresh the numbers are (`asOf`) |
| `DELETE /v1/links/{code}` (owner) · `POST /v1/takedowns {code, reason}` (trust and safety) | FR4 | writes **Link.status**, **Takedown** | Both publish an invalidation event; audit row |
| internal `LeaseRange()` → `{start, end}` | FR1 | writes **RangeLease** | 1,000 IDs per lease |

**Conceptual**: **Link** (code, long URL, owner, created, expires, status) N—1 **Owner**; **Link** 1—N **ClickEvent** (code, time, country,
referrer class); **DailyCount** (code, day, country, n) derived from ClickEvent; **Takedown** (code, reason, actor, time); **RangeLease**
(server, start, end, time).
**Physical**: `link(code PK, url, owner_id, created_at, expires_at, status)` sharded by `code` (the only key the hot path uses); a secondary
`link_by_owner(owner_id, created_at, code)` for the dashboard; `range_lease` in a small strongly consistent store; click events in a log
partitioned by code; `daily_count(code, day, country)` in an analytics store. A deterministic hash of the URL is **not** a key: the same
URL may have many links.

## 5 · High-level design

| Version | Adds | Objection it answers | Objection it leaves |
|---|---|---|---|
| V1 | One service, one relational table `code → url`; random 7-character code inserted with retry on conflict; redirect reads the table | (none: simplest thing that works) | 4,000 reads a second on one table with a 40,000 peak on one row; analytics would be an `UPDATE` per click; nothing scales out |
| V2 | **Split the paths**: stateless redirect servers with a shared cache (cache-aside) in front of a sharded link store; a separate create service with counter ranges and the keyed permutation | "The redirect path and the create path have different loads and different failure tolerances; and the store is hit on every click" | One viral code is one hot cache key; clicks still have nowhere to go; a takedown sits behind every cache |
| V3 | **Protect the redirect**: in-process hot cache with coalescing; click events to a local buffer and a log, aggregated off-path; status, invalidation events and bounded TTLs; a CDN edge in front with short cache times and purge; safety-check on create | "Nothing beside the redirect may slow it, and every copy must be withdrawable" | The details, which are the challenges |

Baseline spine, left to right: **Browser / API client → Edge (CDN) → Redirect service (in-process cache) → Shared cache → Link store**, with
**Create service → Range allocator** above, and **Click buffer → Click log → Aggregator → Stats store** along the bottom; **Safety check** and
**Takedown service** on the right, feeding an **invalidation channel** to every cache layer. Tags: `ch1` range allocator and constraint;
`ch2` permutation; `ch3` in-process cache, coalescing; `ch4` edge; `ch5` invalidation channel; `ch6` click path; `ch7` regional replicas;
`ch8` probes.

Flows (numbered arrows):
- **FR1 Create:** 1 client `POST /links` with idempotency key · 2 safety check on the URL · 3 next ID from the server's leased range (lease a
  new range at half-used) · 4 permute and base-62 encode · 5 insert with the unique constraint on `code` (alias: the alias is the code) ·
  6 201 with the short URL; a 409 for a taken alias.
- **FR2 Redirect:** 1 `GET /aZ3kQ9x` reaches the edge; miss · 2 redirect server: in-process cache · 3 miss: shared cache · 4 miss: link store,
  then fill both caches · 5 check status and expiry · 6 302 with the long URL · 7 click event into the local buffer, after the response.
- **FR3 Count:** 1 buffer flushes a batch every second or 1,000 events · 2 log partitioned by code · 3 raw events to object storage · 4
  aggregator per code per minute, then per day per country · 5 stats store · 6 owner's dashboard reads with `asOf`.
- **FR4 Withdraw:** 1 takedown or delete · 2 status `blocked` in the link store · 3 invalidation event on the channel · 4 shared cache deletes;
  every redirect server drops its in-process entry · 5 CDN purge call · 6 next request reads `blocked`, answers 410 · 7 audit.

C4 and sequence views that follow: context; container; sequences for create and redirect (reused from the mock round's `u-create`,
`u-redirect`, redrawn on the kit's sequence generator); takedown sequence.

## 6 · Bridge and challenge map

*It works. Where does it break first?* The baseline with eight attack points. Correctness: C1, C2, C5. Overload: C3, C6. Trade-off: C4.
Failure recovery: C7. Observability: C8. The crux (unique and unguessable codes; the redirect under a viral peak) gets C1 + C2 and C3 + C4.

## 7 · Challenges

### Challenge 1 · Two servers, one code  *(correctness; crux part 1)*

- Q: "Two create servers run at the same time. How do they never hand out the same code, without asking each other every time?"
- Naive answer: "Generate a random code, check whether it exists, and insert it if it doesn't."
- Case: Servers A and B each draw `aZ3kQ9x` (or two customers ask for alias `sale` within 3 ms). Both `SELECT` and see nothing at 10:00:00.001;
  both `INSERT` at .004 and .006; with no constraint, the second overwrites the first and the first customer's printed flyer now opens
  someone else's page.
- Break: the create service's check-then-insert, dashed red.
- Fix: **counter ranges + the unique constraint as the authority.** Each server leases `[40,000; 40,999]` from the allocator in one
  conditional write; it hands out IDs locally; the insert carries `UNIQUE(code)`, so an alias race produces one 201 and one 409, never two
  owners. Aliases are 8+ characters, a namespace generated 7-character codes never enter (added while writing the booklet). Sequence: lease, local next, insert, conflict path. Code: the lease as a compare-and-set, eight lines.
- Why it works: S1 is enforced by the one place that sees every write (the shard owning the code); ranges are disjoint by construction,
  so generated codes never even reach the constraint as a conflict. L1: a create waits only on its own insert.
- "What if the fix fails?": "The allocator is down. Or a server crashes holding half a range."
- Second fix: a server leases the next range at half-used, so it holds 500–1,500 IDs of runway: at the 400/s peak across ten servers that is 12–37 s, at the
  40/s average two to six minutes; the allocator is a small replicated store with a consensus protocol, so one
  node lost is not an outage. A crashed server's unused IDs are skipped: a gap, not a collision. Honest limit: an allocator down for
  minutes stops creates; redirects are untouched, which is the right way round.
- If asked, I'd say: "Each create server leases a block of a thousand IDs, so coordination happens once per thousand links, not once per
  link. The unique constraint on the code is the final authority, so a custom-alias race ends in one success and one conflict. If the
  allocator goes down, the servers have their leased runway, and redirects never depended on it."

### Challenge 2 · Codes in order  *(correctness and security; crux part 1)*

- Q: "Your codes come from a counter. What can someone learn from that?"
- Naive answer: "Base-62 makes them look random."
- Case: Monday 09:00 a user gets `0000g8Q`, at 09:10 `0000gBA`: the difference is 2,000 links in ten minutes, our creation rate, for free. A
  scraper requests `0000g8R`, `0000g8S`… and reads every link created that morning, including someone's unlisted document share.
- Break: the encoder after the range, dashed red: base-62 of a counter is a counter.
- Fix: **a keyed permutation**: a four-round Feistel network over the 42-bit space with a secret round key, plus cycle walking to stay
  below 62⁷. It is a bijection, so distinct IDs still give distinct codes (S1 untouched) and neighbouring IDs give unrelated codes.
  Rate-limit 404s per client so random guessing is slow. Code: the Feistel round, ten lines.
- Why it works: uniqueness comes from the counter, unpredictability from the key; the two properties are separated, so neither weakens the other.
- "What if the fix fails?": "The key leaks. Or a customer says short links to private files must not be guessable at all."
- Second fix / limit: rotate the key with a version character (or a new range space) for new codes; old codes stay valid because they are
  stored, not recomputed. Honest limit: seven characters are 42 bits; a determined attacker with many addresses can still sample. Private
  content needs authentication or a long random token, not a short link: say so to product.
- If asked, I'd say: "A counter gives uniqueness, but base-62 of a counter is still a counter: it leaks volume and lets anyone walk the
  links. I pass the ID through a keyed permutation, which keeps it unique and makes neighbours unrelated. And I'm clear that a short code
  is not a secret: private links need authentication."

### Challenge 3 · One link at 40,000 clicks a second  *(overload; crux part 2)*

- Q: "A link goes viral: forty thousand clicks a second, all on one code. What happens?"
- Naive answer: "It's cached, so it's fine."
- Case: 14:02 the code `k7Pq2mZ` goes from 3 clicks/s to 40,000/s. All of it hashes to one shared-cache shard; that shard's p99 goes from
  0.8 ms to 9 ms as its network queue fills, and every other code on the shard slows too. At 14:05 a deploy restarts the shard: for 200 ms
  every request misses, and 8,000 identical queries reach one database row.
- Break: the shared cache shard, then the link store, dashed red.
- Fix: **an in-process cache on every redirect server** (a few hundred thousand entries, 30–60 s TTL) so the viral code is answered from
  memory on each of, say, 40 servers (1,000/s each, trivial); **request coalescing (single flight)** so a miss on one server sends one
  query, not 1,000. Negative caching for unknown codes (a scanner's 404s). Sequence: many requests, one in flight, all answered.
- Why it works: L2: the hot key's load is spread across all servers' memory instead of concentrated on one shard; coalescing caps the
  database load at servers × keys, not clicks.
- "What if the fix fails?": "Now the in-process TTL means a takedown takes up to a minute longer. And a whole region's servers restart together."
- Second fix: the TTL becomes part of the takedown budget (C5) and the invalidation channel drops entries early; restarts roll, and a
  starting server warms its cache from the top codes of the last hour before taking traffic. Honest limit: the edge (C4) is the real
  answer for a global viral link.
- If asked, I'd say: "A viral link is a hot key, not a load problem. I answer it from memory on every redirect server and coalesce misses so
  one server sends one query whatever the click rate. The cost is a short staleness window, which I count in the takedown budget."

### Challenge 4 · 301 or 302?  *(trade-off)*

- Q: "Should the redirect be a 301 or a 302?"
- Naive answer: "301, it's permanent and it saves servers."
- Case: with 301 the browser caches the redirect indefinitely: a user who clicked `k7Pq2mZ` yesterday never asks us again, so today's
  click is not counted and, if the link is blocked for phishing at 15:00, that user's browser still goes straight to the phishing page.
- Break: the arrow from browser to edge, dashed red: an answer we cannot see or recall.
- Fix: **302 by default, with a short shared-cache lifetime at the edge** (`s-maxage=60`, `private` for browsers), CDN purge on takedown; 301
  only as an owner's opt-in for permanent, uncounted links. The layers table: browser (free, invisible, unrecallable), edge (cheap, counted
  from logs, purgeable), our servers (exact, recallable).
- Why it works: control (counting, S2) stays at layers we can reach; the edge gives most of 301's saving at a bounded cost to freshness.
- "What if the fix fails?": "Finance says the edge bill for 10 billion requests is too high. Or clicks counted from edge logs arrive twenty minutes late."
- Second fix: edge cost is per request either way; compare it with the servers it saves (the layered-cost slide, arithmetic labelled
  illustrative). Edge-log counts are the stated lag; when clicks are billed, the count comes from our servers or a signed edge function.
- If asked, I'd say: "301 against 302 is a product decision, not an optimisation. A 301 is answered by the browser forever, so we lose the
  click and the ability to take a link down. I default to 302, let the edge cache it for a minute, and offer 301 only to owners who want a
  permanent, uncounted link."

### Challenge 5 · Dead everywhere in five minutes  *(correctness and operations)*

- Q: "Legal reports a phishing link. It must stop working everywhere within five minutes. Show me."
- Naive answer: "Delete the row."
- Case: 15:00:00 row status set to blocked. Copies still answering: the shared cache (TTL 1 h), 40 redirect servers' in-process caches
  (60 s), the edge in 30 locations (60 s), and browsers that got a 301 last week (forever). At 15:20 a victim still lands on the page.
- Break: every cache layer on the baseline, dashed red.
- Fix: **status in the store, an invalidation event, and a bounded TTL at every layer.** The takedown writes `blocked`, publishes on the
  invalidation channel (the shared cache deletes the key; every redirect server drops it), calls the CDN purge, and the redirect answers
  410 with a warning page. The budget: event seconds + in-process 60 s + edge 60 s + purge ≈ 2 min worst case if the event is lost, under
  the 5 min target. 302s mean browsers re-ask. Also: the safety check on create and a rescan of live links when the classifier updates.
- Why it works: S2 holds by arithmetic: the worst case is the sum of TTLs along the path, and each TTL is chosen to fit.
- "What if the fix fails?": "The invalidation event is lost. Or the link was created as a 301."
- Second fix: the TTLs are the backstop by design; a sweeper compares blocked codes against the in-process caches' metrics. A 301 cannot be
  recalled: say so; that is why it is opt-in and the safety check runs before a 301 link is issued.
- If asked, I'd say: "Every copy of the answer is a liability. A takedown writes the status, sends an invalidation, purges the edge, and the
  TTL at every layer is chosen so that even with a lost message the worst case is inside five minutes. A 301 can't be recalled, which is
  one more reason it isn't the default."

### Challenge 6 · Counting without slowing the redirect  *(overload; correctness when billed)*

- Q: "How do you count clicks per link per country without touching the redirect latency?"
- Naive answer: "`UPDATE links SET clicks = clicks + 1` on every redirect."
- Case: the viral code at 40,000/s means 40,000 updates a second on one row: the row lock serialises them, the redirect waits on the
  write, and p99 goes from 5 ms to 900 ms.
- Break: an arrow from the redirect service to the link store on every click, dashed red.
- Fix: **click events to a local buffer, flushed in batches to a log partitioned by code, aggregated per minute.** The redirect emits after
  answering; if the buffer is full it drops and counts the drops. Counts are eventually consistent and say `asOf`.
- Why it works: L2: nothing after the answer can delay it; L3 with a measured loss (the dropped counter is the loss).
- "What if the fix fails?": "Product now bills per click. A lost click is lost money, and a double-counted one is a refund."
- Second fix: billed clicks get an event ID at the redirect, a durable local buffer (disk), at-least-once delivery and de-duplication by
  event ID in the aggregator; bot filtering before billing. The redirect still never waits for the log. Honest limit: a server's disk lost
  with an unflushed buffer: bounded by the flush interval, stated in the billing terms.
- If asked, I'd say: "The click is recorded after the answer, never before it. Events go to a local buffer and a log, and an aggregator
  counts per minute. Today that's lossy by choice and we measure the loss; if clicks are billed, I add event IDs, a durable buffer and
  de-duplication, and the redirect still doesn't wait."

### Challenge 7 · A region goes dark  *(failure recovery)*

- Q: "The region holding your link store's primary goes down. What still works?"
- Naive answer: "We fail over the database."
- Case: 03:10 the primary region is lost. Redirects in Europe and Asia still have their caches; 2 % of requests miss and go to a store
  that is now read-only; creates fail; the allocator's leader was in that region too.
- Break: the link store primary and the allocator, dashed red.
- Fix: **redirects are read-only and regional**: each region has a replica of the link store and its own caches, so a redirect never
  crosses regions. **Creates are regional too**: each region leases ranges from its own slice of the ID space (the top bits), so a region
  can create without the others; the store replicates asynchronously. Failover of the primary for the shard is for writes only.
- Why it works: L2 depends only on regional state; S1 holds because the regions' ID spaces are disjoint.
- "What if the fix fails?": "A link created in Asia is clicked in Europe 200 ms later, before replication."
- Second fix: on a miss the redirect asks the creating region (its prefix says which) once, then caches; the new link's first click pays
  one cross-region round trip. Honest limit: a region lost with unreplicated creates loses those links' last seconds; the creator retried
  with the same idempotency key gets the same code back once the region returns.
- If asked, I'd say: "Redirects never leave their region: replicas and caches answer them even with the primary gone. Creates are regional
  because each region owns a slice of the ID space. The one gap is a brand-new link clicked elsewhere before it replicates, and that costs
  one cross-region lookup, not an error."

### Challenge 8 · How would you know it is broken?  *(observability)*

- Q: "Your dashboards are green. How do you know redirects are actually working?"
- Naive answer: "Error rate and CPU."
- Case: a config change sets the shared cache's TTL to 0. No errors; p50 is fine; p99 rises from 6 ms to 18 ms; the database's read load
  goes from 40/s to 4,000/s at 02:00, when nobody is watching, and the first page is at 09:00 when the peak arrives.
- Break: the monitoring view of the baseline, dashed red: we watch boxes, not the user's path.
- Fix: **SLIs on the user's path**: redirect latency and success from synthetic probes in every region (create a link, then follow it,
  every minute: create-to-first-redirect time), takedown latency (a test link blocked hourly, measured until 410 at every layer). **Symptom
  pairs**: cache hit rate down + store reads up = cold cache, not traffic; 404 rate up + creates flat = scanning; p99 up + hit rate flat
  = something synchronous crept onto the path; click events dropped up + buffer full = log or aggregator slow.
- Why it works: the SLI measures what the user gets, the pairs turn two metrics into one cause.
- "What if the fix fails?": "The probes pass, but one country's DNS sends users to the wrong region."
- Second fix: real-user monitoring from the edge logs per country, compared with the probes; an alert when they diverge.
- If asked, I'd say: "I measure the path, not the boxes: probes that create a link and follow it in every region, and a test takedown every
  hour timed until every layer answers 410. Then pairs of metrics give me causes: hit rate down with database reads up means a cold cache,
  not more traffic."

## 8 · Build cost (AUX)

- **V1** (one service, one table, random codes, a cache): 2 engineers, 6 weeks. **V2** (split paths, ranges, permutation, sharded store):
  +2 engineers, 2 months. **V3** (in-process cache, click pipeline, takedown channel, edge, regions): a team of 5–6 for 2 quarters;
  analytics and trust-and-safety integration are a second team's seam.
- **Buy against build**: a managed key-value store and a CDN are bought; the classifier is bought or an internal service; an off-the-shelf
  shortener product is a fine answer if the business is not the shortener itself (say it).
- **Team seams** (two teams, one quarter): *links and redirect* (create, codes, store, caches, edge) and *clicks and trust* (event pipeline,
  stats, takedown channel). Contract between them: the click event schema and the invalidation channel.
- **Cost, illustrative**: redirect servers at 4,000/s are a handful of instances; the cache tier 100 GB of RAM; storage 18 TB; the edge
  bill per request is the largest line at 10 billion requests a month, which is why the default edge lifetime is a business decision.
- **Top risks**: the ID scheme is a one-way door (codes are printed on paper); takedown latency untested until a real incident; analytics
  turning into billing without the exactness work.

## 9 · Recap

Final diagram: the V3 baseline. One sentence per path: *Create:* lease, permute, insert under the constraint. *Redirect:* memory, then the
shared cache, then the store, answer, then count. *Count:* buffer, log, aggregate, say how fresh. *Withdraw:* status, invalidate, purge,
and TTLs that sum to under five minutes.
**Common mistakes:** hashing the URL and truncating with no collision story; six characters without the arithmetic; check-then-insert;
"add a cache" with no hot-key plan; 301 by default; a counter `UPDATE` per click; forgetting that every cached copy must be withdrawable;
codes that are a counter in disguise; no number on the takedown time.
**Closing line (key-line voice):** "The redirect is the product, so it's one memory read and nothing waits on anything else. Codes are unique
because each server owns a block and the database has the last word, and unguessable because a key shuffles them. Everything else —
counting, takedowns, the edge — lives beside the redirect, with a number on how late it may be."

## Canon check

| Canonical point | Source | Covered at, or dismissed because |
|---|---|---|
| Read:write ratio and capacity over the service's life | book ch. 8; walkthrough 02 | Ch. 1 Q1–2; ch. 2 |
| Code length from capacity over a 62-character alphabet | book; 02 | Ch. 2 (six against seven, with the headroom) |
| Hash-and-truncate against counter + base-62, with the trade | book; 02 | Ch. 3 options matrix rows A, C, D; C1 |
| 301 against 302 tied to analytics and load | book; 02 | C4 |
| Cache in front of the store on the redirect | book; 02 | V2; C3 |
| Unique IDs in a distributed deployment | book (points to its ID-generator chapter) | M1; C1; C7 (regional slices) |
| Unique constraint as the final authority; custom-alias race | 02 | M3; C1 |
| Analytics off the critical path | 02 deep dive | M5; C6 |
| Bloom filter to test whether a code exists | book (as an option) | Dismissed aloud in C1: the constraint already answers it on insert; a filter adds a second truth to keep in sync |
| Rate limiting the create API | book wrap-up | API slide (per-key limit, SD-25) |
| Database scaling, replication, multi-region | book wrap-up (one line) | C7 |
| Hot key / viral link | not in either source in depth | C3 (ours) |
| Takedown through every cache layer | not in either source | C5 (ours) |
| Enumeration of sequential codes | 02 mentions; book does not | C2 (ours, with the permutation) |
| What changed since the book | — | Edge platforms now run code at the edge and expose purge APIs in seconds; browser caching rules for 301 unchanged |

## From the old version (retired classics mock round 3)

| Reused | New | Dropped |
|---|---|---|
| The clarifying answers and all estimates; the options for code generation; 301/302 layers table; analytics pipeline; the six SVGs `u-*` as starting points for the baseline views | Theory chapter (six parts); options matrix with a pick; V1→V2→V3 on a carried baseline; four numbered flows; C2 permutation, C5 takedown budget, C7 regions, C8 symptom pairs as full challenges; build cost; canon check | Interviewer–candidate dialogue as the frame (now candidate-led); the coach's "six checks" (become the recap's common mistakes) |

## Budget

| Chapter | Minutes | Words | Slides |
|---|---|---|---|
| 0 Cold open | 2.5 | 300 | 5 |
| 1 Requirements and scope | 5 | 620 | 10 |
| 2 Estimates | 5 | 620 | 10 |
| 3 Theory | 9 | 1,100 | 15 |
| 4 API and entities | 4.5 | 550 | 8 |
| 5 High-level design | 9 | 1,100 | 17 |
| 6 Bridge | 1 | 100 | 2 |
| 7 Challenges (8 × ~4.4) | 35 | 4,000 | 64 |
| 8 Build cost (AUX) | 3 | 360 | 5 |
| 9 Recap | 3 | 350 | 6 |
| **Total** | **77** | **9,100** | **142** |

## Revision 2026-11-21 (revised standard: progressive disclosure, components and technologies)

**Moved earlier and expanded.** C4 context now closes chapter 1 (after scope). The C4 container view follows V3 directly and is
walked container by container (≈ 45 words each, 10 reveal steps). Every functional requirement has a flow **and** a sequence
(new: `seq-count` for FR3; `seq-takedown` now shown in chapter 5).

**Theory, mechanisms at work (new, 3 slides).** `th-map`: the container view labelled M1–M6. `seq-th-lease`: two create servers
race through an etcd Txn on `ModRevision`; the Raft log commits on a majority; no clock, no lock. `seq-th-cache`: three
concurrent misses → one lookup (singleflight) → Redis `SET EX 3600 ± 10 %`; an invalidation, or the 60 s lifetime, ends the copy.

### 5.1 · Components and technologies

C4 component views: `c4-comp-redirect` (HTTP handler, resolver/singleflight, ristretto, Redis cluster client 2 ms, pgx pool
20 ms, click emitter, invalidation listener rewinding 5 min) and `c4-comp-create` (API handler with idempotency key, rate
limiter on Redis token buckets, safety client 150 ms + breaker, Feistel encoder keyed from KMS, etcd range holder, store writer
`ON CONFLICT DO NOTHING` + idempotency row in one transaction).

<!-- stack:outline -->

| Container | Choice | How it is built | Rejected | Theory part |
|---|---|---|---|---|
| Link store | PostgreSQL 16, 16 shards per region | `link(code char(7) PRIMARY KEY, …)` | Cassandra / ScyllaDB; DynamoDB; One big PostgreSQL | 5, 6 |
| Range allocator | etcd, 3 nodes per region across zones | Key `/alloc/{region}/next` | ZooKeeper; Redis INCRBY; Cassandra counter or LWT; A PostgreSQL sequence (INCREMENT 1000) | 2 §2.11, 3 |
| Shared cache | Redis Cluster, 6 primaries + 6 replicas per region | 16,384 hash slots over 6 shards, about 17 GB of the hot set each | Memcached; Hazelcast; No shared cache, store replicas only | 9 |
| In-process cache and single flight | ristretto (Go) + golang.org/x/sync/singleflight | 300,000 entries × ~300 B, about 100 MB per server; lifetime 60 s, 10 s for a not-found | A plain LRU map; A sidecar cache per host; No local cache | 9 §9.7, 6 §6.5 |
| Click log | Kafka, 3 brokers per region, replication factor 3 | Topic `clicks`, 32 partitions, keyed by code, 7 days' retention | RabbitMQ; Kinesis or Pub/Sub; Write straight into the stats store | 8 |
| Aggregator and stats store | Flink job → ClickHouse (SummingMergeTree) | Keyed by code; 1-minute tumbling windows; 30 s allowed lateness | Spark Structured Streaming; A nightly batch job; Cassandra counters; A PostgreSQL table | 8 |
| Invalidation and the edge | Kafka topic link-invalidations + CDN purge by surrogate key | Each redirect server reads with its own consumer group, from the latest offset, rewinding 5 minutes on start | Redis Pub/Sub; Polling the store for changes; Purge by URL only | 9 |
| Services | Go on Kubernetes, 3 zones per region; a bought CDN | Redirect pods scale on requests per second; a pod warms its in-process cache from the last hour's top codes before it passes readiness | Java (Caffeine); Serverless functions for the redirect; Build our own edge | 1, 9 |

Fix-slide rejections: 1: Redis INCRBY as the counter; 2: A hash of the long URL; 3: Redis replica reads alone; 4: A CDN without a purge API; 5: Redis Pub/Sub for the invalidation; 6: Cassandra counters; 7: One global consensus database (Spanner, CockroachDB); 8: An outside uptime checker alone.

<!-- /stack:outline -->

### Second pass, 2026-11-21 (single source, drill, rejections, captions)

- **`stack.json` is the one place a technology is written.** The 5.1 technology slides, the stack slide, the drill table, the
  fix-slide rejections and the container view with technologies read it; `stack.py sync` writes the booklet's Stage 5
  sections and stack table and the table above.
- **Drill interlude** after the stack slide (~2.3 min): the coach hands the viewer the interviewer's seat, then five boxes
  (link store, allocator, shared cache, click log, invalidation), each read as interviewer probe and coach answer.
- **Every fix slide names a rejected tool** (`rejl`), with one candidate sentence: Redis `INCRBY`, a URL hash, Redis replica
  reads, a CDN without purge, Redis Pub/Sub, Cassandra counters, a global consensus database, an outside uptime checker.
- **New design fact**: a custom alias has a home region fixed by a hash of the alias; alias creates are forwarded there.
- **Captions**: SRT speaker prefix inside the 42-character budget; VTT voice spans.

### Budget, measured

| Chapter | Minutes | Words |
|---|---|---|
| 0 Cold open | 3.3 | 423 |
| 1 Requirements | 5.8 | 699 |
| 2 Estimates | 4.8 | 630 |
| 3 Theory | 13.7 | 1,664 |
| 4 API and entities | 4.0 | 519 |
| 5 Design + 5.1 | 28.1 | 3,417 |
| 6 Bridge | 1.0 | 118 |
| 7 Challenges | 35.5 | 4,137 |
| 8 Build cost | 2.6 | 288 |
| 9 Recap | 3.2 | 338 |
| **Total** | **101.9** | **12,222** (169 slides, 627 frames) |
