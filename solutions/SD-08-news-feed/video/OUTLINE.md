- [x] outline approved  - [x] design  - [x] diagrams  - [x] slides  - [x] script  - [x] video  - [x] publish

# SD-08 · News feed / home timeline — reference-solution video outline

Target level: staff (manager layer AUX) · Target length: 88 min (75–90) · Word budget: 10,700 (≈ 0.49 s a word with the
2026-11-17 pacing beats, measured on SD-94)

Generic content only: no company names or figures; all volumes are the interviewer's stated inputs or labelled assumptions. Recut of the
v3 mock round (43:48) and the 2026-11-20 classics mock round 1, both retired.

## Thesis and definition

- **Thesis** (key-line voice): *A feed is a materialised view that is cheap to read for almost everyone and impossible to precompute for a
  few: push post IDs to the followers of ordinary accounts, pull the celebrities at read time, say where the line is and why, and keep every
  correctness rule — deletes, blocks, privacy — on the read path.*
- **Definition to say aloud**: *A home feed is, for each reader, a bounded, ranked list of recent post IDs from the accounts they follow,
  assembled from a precomputed part and a part fetched at read time, then filtered and hydrated within the read budget.* Load-bearing
  clauses: **for each reader** (it is a per-user view, so it can be lost and rebuilt), **bounded** (a few hundred entries), **post IDs**
  (never bodies), **precomputed plus fetched** (the hybrid), **filtered** (correctness at read), **within the read budget** (200 ms, with a
  fallback).
- **Hook**: Push or pull is the textbook answer, and the textbook answer is "both". Interviewers still ask it, because the grade is on what
  comes after "both": the arithmetic that puts the line at ten thousand followers and not a million, what happens to the account that
  crosses it, why a deleted post stays out of millions of copies, and what the feed does when the ranker is slow or a cache shard is gone.

## 0 · What this question grades

| Axis | Weak signal | Strong signal |
|---|---|---|
| Requirements | "Show posts from friends sorted by time" | Asks the follower distribution and finds the tail; asks "twice or never: which is worse?"; puts numbers on freshness and latency |
| Correctness | Fan-out copies of posts treated as truth; deletes chased into timelines | IDs only, hydrated from the source; visibility filtered at read; idempotent inserts; a stable cursor |
| Trade-offs | Picks push or pull and defends it | The hybrid with a threshold derived from arithmetic, plus what it costs; active-only fan-out |
| Depth | Stops at "a cache" | Crossing the threshold with no backfill; rebuild under stampede with coalescing; ranking under a deadline with a fallback |
| Operations | Uptime of the feed API | Freshness as an SLI from synthetic accounts; silent quality degradation metrics; the memory bill and its lever |

## 1 · Requirements and scope

- **Clarifying questions and the interviewer's answers** (asked aloud, eight):
  1. *Users?* — 1 billion, 500 million daily active.
  2. *Read to write?* — Feed reads about 100 times post writes.
  3. *How many accounts does a user follow, and how is it distributed?* — Average about 200. "The maximum on the other side: some accounts
     have over 100 million followers." (The tail question; asking it is a signal.)
  4. *Latency?* — p99 under 200 ms for the first page.
  5. *Ranked or chronological?* — Ranked; a scoring service exists; treat the model as a black box.
  6. *How fresh?* — Seconds for close follows; a minute is tolerable generally.
  7. *How deep?* — The first 50 on open, paginated after.
  8. *Which is worse: seeing a post twice, or missing one?* — "Missing a close friend's post is worse; a duplicate on screen is a bug." (Seeds C4.)
- **Functional requirements**:
  - FR1 · **Publish** a post (text and images), visible to followers.
  - FR2 · **Read** the home feed: ranked, first 50, then paginated with a stable cursor.
  - FR3 · **Follow and unfollow** with effect on the feed.
  - FR4 · **Remove**: delete a post, block an account, change a post's audience; gone from every feed within seconds.
- **Non-functional, with numbers** (initial targets): feed p99 under 200 ms; post visible to active followers p95 under 5 s; read
  availability 99.95 %; deleted or blocked content gone within 5 s; a post is never lost (the source of truth is durable; the feed may be
  rebuilt).
- **IN / OUT**: IN: publish, feed build and serve, pagination, follow effects, deletes, blocks and audience, ranking integration under a
  budget. OUT on purpose: the ranking model itself, ads insertion, media upload and transcoding, search, notifications (SD-12), the social
  graph service internals (SD-14), comments and likes counters (one sentence: a separate counter service).
- **"The core is 4 things"**: a *source of truth* for posts, a *per-reader view* built by push and pull, a *read path* that filters, ranks
  and hydrates inside 200 ms, and a *rebuild path* for when the view is lost.

## 2 · Estimates

| Number | Arithmetic | Label | Decision it drives |
|---|---|---|---|
| Feed reads | 500 M × 5 opens ÷ 86,400 s ≈ **29,000/s** average; × 3 ≈ **90,000/s** peak | given → derived | Served from memory; a database per read is out |
| Pure pull cost | 90,000 opens/s × 200 followees = **18 million author-index reads/s** | derived | Rules out V1 at this scale (it is fine at 1 % of it: the MVP) |
| Posts | 500 M × 0.1 a day = 5 × 10⁷ a day ≈ **580/s** | illustrative | Writes are tiny at the source |
| Fan-out inserts | 580/s × 200 followers ≈ **120,000 inserts/s** | derived | Push multiplies writes 200×: affordable for ordinary authors |
| Active-only fan-out | if ~half of followers have not opened the app in 30 days: **≈ 60,000/s** | illustrative, **to be measured** | The cheapest big win: skip inactive followers, rebuild them by pull if they return |
| One celebrity post | 1 × 10⁸ followers = **10⁸ inserts**; at the whole fleet's 120,000/s that is ≈ 830 s, and it stalls everyone else's fan-out | derived | Kills pure push; the celebrity is pulled |
| Threshold, write side | a 10,000-follower post = 10⁴ inserts ≈ 0.08 s of fleet capacity; a 1 M-follower post ≈ 8 s, past the 5 s freshness target on its own | derived | Push up to ~10⁴–10⁵ followers, pull above |
| Threshold, read side | each followed celebrity costs one ~0.5 ms cache read per open; 20 of them ≈ 10 ms of the 200 ms budget | illustrative | The line also bounds how many pulled authors an average reader has |
| Timeline storage | 500 M active × 500 entries × 16 B (post ID + author ID + time, packed) = **4 TB**, × 3 replicas ≈ 12 TB of RAM | derived | Fits a memory tier — only because rows are IDs |
| Bodies in timelines (the mistake) | 500 M × 500 × ~1 KB ≈ **250 TB** | derived | 60× larger; never copy bodies |
| Read budget (200 ms) | timeline 5 + celebrity merge 5 + graph and blocks 5 + filter 5 + **ranking ≤ 80** + hydration 20 + network and serialisation 20 = **140 ms**, spare 60 | initial target | Ranking gets a hard deadline and a fallback |
| Rebuild after a shard loss | 100 shards → 5 M users per shard; if 20 % open in the next 10 min: 10⁶ rebuilds ÷ 600 s ≈ 1,700/s × 200 author reads ≈ **340,000 reads/s** | illustrative | Rebuild needs coalescing, a rate limit and a degraded mode (C5) |

## 3 · Theory

1. **Is / is not.** A feed is a **materialised view** per reader of the query "recent posts by accounts I follow, ranked". It is not the
   **source of truth** (posts are; the view can be wrong for seconds and rebuilt), not a **chat inbox** (an inbox may not lose a message; a
   feed may omit an old post, and says so), not **search** (it answers one query shape; C7 is a different one), and not the **ranking model**
   (ranking is a stage with a budget).
2. **Safety**: S1 · a viewer never sees content they must not see (deleted, from a blocked account, outside its audience) for longer than the
   5 s bound. S2 · a post is never lost: the source of truth is durable even if every view is lost. **Liveness**: L1 · a post reaches its active
   followers' feeds within 5 s p95. L2 · every feed open answers within 200 ms, degraded if it must. L3 · a lost or skipped timeline is rebuilt on
   its next open.
3. **Central tension**: **write amplification against read latency.** Push pays at post time, in proportion to followers; pull pays at read
   time, in proportion to followees. Picture: cost against follower count: push rises in a straight line, pull is flat per post but paid on
   every open; the lines cross near the threshold, and the hybrid follows the lower one.
4. **Mechanisms** (7). Property → how → failure ruled out → cost.

   | Mechanism | Protects | Rules out | Costs |
   |---|---|---|---|
   | **M1 Fan-out on write into bounded ID lists, idempotent by post ID** | L1, L2 | A read that touches 200 authors; duplicate entries on re-delivery | 120,000 inserts/s; a memory tier; amplification on big authors |
   | **M2 Fan-out on read from author indexes** (also the rebuild and the catch-up path) | L2 for celebrities, L3 | 10⁸ writes for one post; a lost view staying lost | A merge per read; author indexes must be fast and protected |
   | **M3 The hybrid threshold with transition rules and active-only targeting** | L1 and cost | Pure push's celebrity, pure pull's read cost, writes to users who never read | A tier per author to maintain; a number to tune |
   | **M4 IDs in the view, hydration through a post cache** | S1 (one place to delete), cost | 250 TB of copies; an edit or delete chasing millions of copies | A multi-get per page; the post cache is critical |
   | **M5 Visibility filter on the read path** | S1 | A deleted or blocked post surviving in a precomputed copy | A per-reader block and mute set read on every open |
   | **M6 Ranking under a deadline with a fallback** | L2 | A slow model making the feed fail | Lower quality while degraded, which must be measured |
   | **M7 Log-based asynchronous fan-out with priority lanes** | L1 under bursts | A burst (a global event) delaying close friends; lost fan-out work | A log and workers to run; lag as an SLI |

5. **Options matrix** (rows = approaches; columns = deciding properties; last column = fails when).

   | Approach | Read cost at 90,000/s | Write cost per post | Celebrity | Fails when |
   |---|---|---|---|---|
   | A · Pull with a database join at read time | 18 M reads/s | 1 write | Fine | Any real scale: every open is a 200-way merge on the database |
   | B · Pull with a per-reader result cache (the MVP) | One cache read on a hit; a merge on a miss | 1 write | Fine | Freshness (the cache is stale) and the miss rate at peak |
   | C · Pure push of IDs | One cache read | followers inserts | **10⁸ inserts** | The first celebrity post |
   | D · Pure push of bodies | One cache read, no hydration | followers × 1 KB | 10⁸ copies | Storage (250 TB) and every edit or delete |
   | **E · Hybrid: push IDs for ordinary authors to active followers, pull celebrities, hydrate, filter on read** | One read + a small merge | ≤ 10⁴–10⁵ inserts | Pulled | The threshold is set wrong and not measured; a power reader who follows hundreds of celebrities |
   | F · Buy: a managed activity-feed service | Theirs | Theirs | Theirs | Ranking and privacy rules that must live in our code; a billion users' cost |

   **Pick: E**, built after **B** as the MVP (say when B is enough: until the merge-on-miss rate breaks the budget). A, C, D, F greyed with their
   failure. **Gives up:** strict freshness (seconds of eventual consistency) and simplicity (two paths and a tier per author) for a read that
   costs one memory lookup.
6. **Failure catalogue**: F1 the celebrity post → C1 (crux part 1) · F2 an account crossing the line; the mid tier; the power reader → C2 (crux
   part 2) · F3 delete, block, unfollow, audience change → C3 · F4 duplicates and a feed that moves while you scroll → C4 · F5 a timeline shard
   lost; rebuild stampede → C5 · F6 the ranker is slow → C6 · F7 a query the view was not built for → C7 · F8 the feed works but is worse → C8
   · F9 a global event bursting the fan-out log: covered in C1's second fix (priority lanes).

## 4 · API and entities

| API | Serves | Reads / writes | Wire-format notes |
|---|---|---|---|
| `POST /v1/posts {text, mediaIds[], audience}` + `Idempotency-Key` → `{postId}` | FR1 | writes **Post**, **AuthorIndex**, **Outbox** | The post and its event in one transaction; media uploaded separately |
| `GET /v1/feed?cursor&limit=50` → `{items[], nextCursor}` | FR2 | reads **Timeline**, **CelebrityRecent**, **Post** cache, **Block** | The cursor encodes `(score or time, postId)` of the last item; stable while posts arrive |
| `POST /v1/follows/{id}` · `DELETE /v1/follows/{id}` | FR3 | writes **Follow** | An event; no backfill on follow, the read merge covers recent posts |
| `DELETE /v1/posts/{id}` · `POST /v1/blocks/{id}` · `PATCH /v1/posts/{id} {audience}` | FR4 | writes **Post.status**, **Block** | Invalidation event for the post cache |
| internal `Rank(viewer, candidateIds[], deadlineMs)` → `{scores}` | FR2 | — | IDs and a deadline in, scores out; features stay with ranking |

**Conceptual** (Chen): **User** authors **Post**; **User** follows **User** (both directions queried); **User** blocks or mutes **User**;
**Timeline** (viewer → bounded list of post IDs) and **CelebrityRecent** (author → last ~100 post IDs) are derived.
**Physical**: `post(post_id PK time-sortable, author_id, text, media_refs, audience, status, created_at)` sharded by `post_id`;
`author_index(author_id, created_at DESC, post_id)` in a wide-column store, one partition per author; `follow(user_id, followee_id)` and
the reverse, in the graph service with follower counts; `timeline:{viewer}` an in-memory sorted set of `(post_id, author_id, time)`, at most 500,
partitioned by viewer; `celebrity_recent:{author}` replicated widely; `post_cache:{post_id}`; `blocks:{viewer}` a small set.

## 5 · High-level design

| Version | Adds | Objection it answers | Objection it leaves |
|---|---|---|---|
| V1 | Post service writes posts and author indexes; the feed service, on each open, reads the followees' recent posts, merges, ranks and caches the result per reader for a minute | (none: simplest thing that works; right at 1 % of this scale) | 18 M author-index reads a second at peak on every cache miss; a minute of staleness |
| V2 | **Push**: post and event in one transaction (outbox); a partitioned log; fan-out workers insert post IDs into each follower's bounded timeline; the feed reads one timeline, ranks, hydrates from a post cache | "The read must be one memory lookup, not a 200-way merge" | One celebrity post is 10⁸ inserts; half the inserts go to users who never read; a deleted post sits in millions of copies |
| V3 | **Hybrid and correct**: tier per author (push below the threshold, pull above from a celebrity-recent cache); fan-out to active followers only; visibility filter on read; ranking under a deadline with fallback; rebuild by pull with coalescing | "The tail of authors decides the design, and correctness cannot live in copies" | The details, which are the challenges |

Baseline spine, left to right: **Author client → Post service → Posts DB + author index → Outbox / log → Fan-out workers → Timeline cache**
on the upper (write) lane; **Reader client → Feed service → (Timeline cache, Celebrity-recent cache, Graph and blocks) → Ranking → Post cache**
on the lower (read) lane; the **Graph service** in the middle, read by both. Tags: `ch1` celebrity-recent cache and the tier router; `ch2` tier
service; `ch3` filter and invalidation; `ch4` idempotent insert and the cursor; `ch5` rebuild path and coalescer; `ch6` ranking deadline; `ch7`
catch-up query; `ch8` synthetic accounts and quality metrics.

Flows (numbered arrows):
- **FR1 Publish (ordinary author, 2,000 followers):** 1 `POST /posts` · 2 one transaction: post row, author-index row, outbox row · 3 relay
  to the log, partitioned by author · 4 worker reads the event: tier = push · 5 pages through followers (1,000 a page), skips the inactive ·
  6 inserts `(postId, authorId, time)` into each timeline, trims to 500 · 7 commits the log offset last.
- **FR1 Publish (celebrity):** 1–4 as above, tier = pull · 5 append the post ID to `celebrity_recent:{author}` · done: one write.
- **FR2 Read:** 1 `GET /feed` · 2 read the timeline (≈ 500 IDs) · 3 read the reader's followed celebrities and their recent IDs · 4 merge, de-
  duplicate, drop blocked, muted, deleted · 5 top ~200 by recency to ranking with an 80 ms deadline · 6 hydrate the top 50 by multi-get from
  the post cache · 7 return with a cursor.
- **FR3 Follow:** 1 write the edge · 2 event · 3 nothing is backfilled; the next read's merge (for a celebrity) or the next post (for an ordinary
  author) covers it; optionally insert the followee's last few posts into the timeline. Unfollow: added to the reader's filter set.
- **FR4 Remove:** 1 delete or audience change on the post row · 2 invalidation event · 3 post cache entry dropped · 4 the next read's hydration
  sees the status and drops the ID · 5 a background job lazily removes the ID from timelines (cosmetic).

C4 and sequence views that follow: context; containers for the write and the read path (reuse `c4-containers-write`, `c4-containers-read`);
sequences: publish (`seq-publish`), outbox (`seq-outbox`), read (`seq-read`), celebrity (`seq-celebrity`), delete (`seq-delete`), rebuild
(`seq-rebuild`); the component view inside the feed service (`c4-component-feed`).

## 6 · Bridge and challenge map

*It works. Where does it break first?* Eight attack points. Correctness: C3, C4. Overload: C1, C6. The crux: C1 and C2. Failure recovery: C5.
New requirement: C7. Observability: C8.

## 7 · Challenges

### Challenge 1 · The celebrity post  *(crux part 1; overload)*

- Q: "Someone with a hundred million followers posts. Walk me through it."
- Naive answer: "The fan-out workers push it to every follower; we add more workers."
- Case: 20:00:00 author `@star` (1.1 × 10⁸ followers) posts. At 120,000 inserts a second for the whole fleet, the fan-out takes about 15
  minutes and holds the log partition; every ordinary author posting at 20:00 waits behind it; a close friend's post appears at 20:14. And
  `@star` posts six times that evening.
- Break: the fan-out workers and the log, dashed red.
- Fix: **don't fan out celebrities.** The event carries the author's tier; above the threshold the worker writes one entry to
  `celebrity_recent:{author}`; the read path merges the reader's followed celebrities (a handful of small cached lists). Sequence
  `seq-celebrity`; code: the tier router, twelve lines.
- Why it works: L1 for everyone else (the log is no longer blocked by one author); L2 for the reader (a few extra cache reads, budgeted).
- "What if the fix fails?": "New Year's Eve: ten times the normal posting rate, all ordinary accounts, for ten minutes."
- Second fix: **priority lanes**: fan-out to close-tie followers (an interaction score) first, the rest after; partition the log by author so a
  burst spreads; lag is a metric per lane, and the read path's pull covers a lagging close friend for minutes. Honest limit: during the
  burst the "a minute generally" target may slip; close friends keep their seconds.
- If asked, I'd say: "One celebrity post would be a hundred million writes, minutes of fan-out that block everyone else. So above a follower
  threshold I don't fan out at all: the post goes into a small recent-posts cache for that author, and each reader merges the few celebrities
  they follow at read time. That costs a few milliseconds per open, which I've budgeted."

### Challenge 2 · Where is the line, and who crosses it?  *(crux part 2)*

- Q: "Where exactly is the threshold, and what happens to an account that crosses it?"
- Naive answer: "A million followers."
- Case: at a million, one post is 10⁶ inserts ≈ 8 s of the whole fleet: past the 5 s target by itself. Meanwhile `@newstar` goes from 9,000 to 2
  million followers in a day; two hundred of its posts were pushed into timelines yesterday, none will be today. And a power reader follows
  5,000 accounts, 300 of them celebrities: 300 pulled lists on every open is 150 ms.
- Break: the tier decision, dashed red: a fixed number nobody can justify.
- Fix: **derive the line from both sides of the arithmetic and make it config.** Write side: a post's fan-out must finish well inside 5 s on
  a fair share of capacity (≈ 10⁴–10⁵ followers). Read side: the average reader should pull fewer than ~20 authors. Start at 10,000, measure,
  tune. **Crossing up:** mark the author pull; existing timeline entries stay and age out; the merge covers new posts: no backfill. **Crossing
  down:** resume push for new posts; the merge still covers the recent ones. **The mid tier** (10⁴–10⁵): push to followers active in the last day
  only. Table: three tiers of author.
- Why it works: L1 and L2 both hold at the line because it was chosen where each side's cost is acceptable; the transition never needs a backfill
  because the read merge covers the gap.
- "What if the fix fails?": "The power reader: three hundred celebrities on every open."
- Second fix: treat the tail of readers like the tail of authors: precompute that reader's celebrity merge every few minutes into their
  timeline (a per-reader pull job), so their open is one read; cap the merge at the top 50 celebrities by interaction. Honest limit: their
  celebrity posts may be a few minutes late.
- If asked, I'd say: "I set the line from both sides: one post's fan-out must finish inside the freshness target, and the average reader should
  pull only a handful of authors. That puts it around ten thousand followers; it's a config value I'd tune with real data. Crossing it needs no
  backfill because the read merge covers recent posts, and the rare reader who follows hundreds of celebrities gets their merge precomputed."

### Challenge 3 · Delete, block, unfollow  *(correctness)*

- Q: "A user deletes a post, or blocks someone. That post ID is already in millions of timelines. How does it disappear?"
- Naive answer: "Fan out a delete to every timeline that has it."
- Case: 21:00:00 `@ana` posts to 3 M followers; at 21:00:40 she deletes it (wrong photo). The delete fan-out takes as long as the post fan-out
  and races it: followers whose insert lands after the delete keep the post. At 21:05 `@ben` blocks `@cal`; `@cal`'s 500 posts in `@ben`'s timeline
  stay.
- Break: the timeline cache, dashed red: correctness stored in copies.
- Fix: **correctness on the read path; cleanup is cosmetic.** Timelines hold only IDs; hydration reads the post through the post cache, which is
  invalidated by the delete event, and drops anything deleted or out of audience; the merge drops authors in the reader's block, mute and
  unfollow set (small, cached per reader). A background job removes IDs lazily. Sequence `seq-delete`.
- Why it works: S1 is decided at one place, the post's own row, read on every page; the bound is the cache invalidation time, seconds.
- "What if the fix fails?": "The post-cache invalidation event is lost."
- Second fix: the post cache entry has a TTL (say 5 min) as a backstop, and deletes and audience changes write a small `recently_removed` set
  checked at hydration for its first hour. Honest limit: a client that already rendered the post shows it until refresh; the next fetch
  removes it.
- If asked, I'd say: "Fanned-out IDs are copies, so I don't trust them. Every page is hydrated from the post itself and filtered by the reader's
  block and unfollow set, so a delete is one write that takes effect within seconds everywhere. Cleaning the IDs out of timelines is a
  background job, and it's cosmetic."

### Challenge 4 · Twice, or never  *(correctness)*

- Q: "You said a duplicate on screen is a bug and a missed close-friend post is worse. Where do each come from in your design?"
- Naive answer: "The log delivers exactly once."
- Case: worker W3 inserts post `p9` into 1,000 timelines, crashes before committing its offset; W7 re-reads the event and inserts `p9` again. A
  reader scrolling with `?offset=50` gets items 50–99 while 12 new posts arrive at the top: items 50–61 repeat and 12 others are never shown.
- Break: the fan-out insert and the pagination, dashed red.
- Fix: **idempotent inserts and a cursor.** The timeline is a sorted set keyed by post ID, so a re-delivered insert is a no-op (at-least-once
  delivery, idempotent effect). The cursor encodes `(score, postId)` of the last item, so the next page starts after it whatever arrives above.
  The read merge de-duplicates by post ID across timeline and celebrity lists. Missing: the pull covers posts whose fan-out is lagging for close
  ties. Code: the cursor encode and decode.
- Why it works: duplicates are impossible by data structure; misses are bounded by fan-out lag, which is measured.
- "What if the fix fails?": "Ranking reorders between page one and page two."
- Second fix: the first page's ranked candidate list is kept for the session (a few hundred IDs, short TTL); later pages page through that
  snapshot, not a re-rank. Honest limit: a new post appears only on refresh, which is the expected behaviour.
- If asked, I'd say: "Fan-out is at-least-once, so inserts are idempotent: the timeline is keyed by post ID. Pagination uses a cursor holding the
  last item's score and ID, never an offset, and the ranked list for a session is kept so page two doesn't reshuffle page one."

### Challenge 5 · A timeline shard is gone  *(failure recovery)*

- Q: "A timeline cache shard is lost. One user in a hundred opens to an empty feed. What do they see, and how do you recover?"
- Naive answer: "Restore it from a backup."
- Case: Sunday 20:00, a shard with 5 M users' timelines is lost. 20 % open within ten minutes: about 1,700 rebuilds a second, each 200 author
  index reads: 340,000 reads a second on author indexes sized for celebrity pulls. Author index p99 goes from 5 ms to 400 ms; now everyone's
  celebrity merge is slow: the outage spreads.
- Break: the timeline shard, then the author index, dashed red.
- Fix: **rebuild by pull, protected.** A miss on a timeline triggers a rebuild by the pull path (the same code as V1), written back to the cache;
  **request coalescing** per user; a **rebuild rate limit** with a queue; beyond it, a **degraded feed** (celebrities and the 50 most recent posts
  from the top 20 followees by interaction) served immediately and marked for rebuild. Sequence `seq-rebuild`.
- Why it works: L3 for the lost users, L2 for everyone else (the blast radius is capped by the rate limit, not by how many users open).
- "What if the fix fails?": "It's not a shard; it's the whole timeline cluster in one region."
- Second fix: serve that region's reads from another region's timeline replica (stale by seconds), or degraded mode for all; rebuild in the
  background at the rate limit, prioritising users by activity. Honest limit: a cold region takes hours to fully warm; that is a stated
  recovery time, and a reason for cross-region replicas of the timeline tier.
- If asked, I'd say: "A timeline is a derived view, so losing it is a latency problem, not data loss. The first open rebuilds it by pull, with
  coalescing per user and a rate limit, and anyone over the limit gets a degraded but instant feed. The rate limit is what stops one lost shard
  from overloading the author index for everyone."

### Challenge 6 · The ranker takes 300 ms  *(overload; latency budget)*

- Q: "Ranking has 80 ms of your budget. Today it takes 300. What's your plan? And the ranking team wants 120 ms for a better model."
- Naive answer: "Wait for it; quality matters."
- Case: p99 of `Rank` jumps from 70 ms to 300 ms after a model push; feed p99 goes to 420 ms; open rate drops. The ranking team's new model lifts
  engagement by an amount they measured, at 120 ms p99.
- Break: the arrow from the feed service to ranking, dashed red.
- Fix: **a hard deadline with a fallback.** Call with `deadlineMs = 80`; on timeout rank by recency plus a cheap heuristic (close ties first), or
  reuse the session's last ranking; measure the fallback rate. For the 120 ms request: pre-rank on app background or prefetch, so the
  expensive model runs before the open; or rank the first 20 fast and the rest asynchronously; or give the budget if hydration shrinks by 40 ms
  (show the budget bar).
- Why it works: L2: the feed's latency no longer depends on a component it does not own; quality loss is bounded and visible.
- "What if the fix fails?": "The fallback rate is 30 % for a week and nobody noticed."
- Second fix: the fallback rate is an SLI with an owner (the ranking team), an error budget, and an automatic rollback of the model push. That
  hands over to C8.
- If asked, I'd say: "Ranking gets a hard deadline inside the two hundred milliseconds, and if it misses, I rank by recency and close ties, so
  the feed degrades instead of failing. For a slower model, I'd find the budget by pre-ranking before the open, not by moving the user's
  deadline. And the fallback rate is a number someone owns."

### Challenge 7 · Catch up on the last 48 hours  *(new requirement)*

- Q: "Product adds 'catch up': a chronological view of everything from the last 48 hours, for any user. What changes?"
- Naive answer: "Make the timelines longer and store them by time."
- Case: the bounded timeline holds 500 ranked IDs; a user following 200 active accounts may have 2,000 posts in 48 h; celebrities were never in
  the timeline; and inactive users were skipped by fan-out.
- Break: the timeline cache, dashed red: asked a query it was not built for.
- Fix: **go to the source of truth, not into the cache.** The catch-up view merges the followees' author indexes for the window (the same pull path
  as the rebuild), chronological, paginated by `(time, postId)`, filtered by the same visibility rules; cache the result per user for minutes.
  The ranked feed is untouched. Diagram `midround-48h`.
- Why it works: the view keeps its bounds and its cost; the new query costs what it costs, once per use, where its data lives.
- "What if the fix fails?": "It becomes the most used screen."
- Second fix: then it earns its own materialisation: a per-user chronological list maintained by the same fan-out (a second sorted set, IDs only,
  48 h TTL), with the cost stated: roughly doubles timeline memory for users who use it. Measure before building.
- If asked, I'd say: "I wouldn't distort the ranked timeline for a query it wasn't designed for. Catch-up reads the source of truth — the
  followees' author indexes for the window — through the same path I use for rebuilds, and caches the result for minutes. If it becomes popular,
  it gets its own small view, and I'd say what that costs first."

### Challenge 8 · How would you know the feed got worse?  *(observability)*

- Q: "The feed is up and fast. How would you know it had silently got worse?"
- Naive answer: "Error rate and latency."
- Case: a change to the tier service marks 30 % of mid-tier authors as pull by mistake. No errors; latency unchanged; their posts reach followers
  only if the followers' merge includes them — which it doesn't, because the merge lists only true celebrities. Freshness for those authors is
  now infinite; engagement per session drifts down 2 % over a week.
- Break: the monitoring view, dashed red: green boxes, a worse product.
- Fix: **measure freshness and quality, not just uptime.** Synthetic accounts in every tier post every minute and synthetic followers read: post-to-
  visible time per tier (the freshness SLI, p95 under 5 s). Quality: empty-feed rate, ranking fallback rate, the share of feed items from close
  ties, engagement per session against its seasonal baseline. **Symptom pairs**: fan-out lag up + post rate flat = workers slow; freshness bad for
  one tier + lag flat = routing bug (this case); fallback rate up + ranking p99 normal = deadline misconfigured; author-index reads up + timeline hit
  rate down = a rebuild wave.
- Why it works: the synthetic path measures the user's promise end to end, per tier, so a routing mistake shows within minutes.
- "What if the fix fails?": "Finance says the timeline tier's memory bill doubled while users grew ten percent."
- Second fix: cost is observable too: memory per active user, entries per timeline, the share of inserts to inactive users; usually the inactive
  cut-off or the timeline bound drifted. Fix the lever, not the cluster size.
- If asked, I'd say: "I measure the promise, not the servers: synthetic accounts in every tier post and read every minute, so I know post-to-visible
  time per tier. Then quality signals — empty feeds, ranking fallbacks, engagement against its baseline — catch the feed that works but got worse.
  And I read metrics in pairs to find the cause."

## 8 · Build cost (AUX)

- **MVP**: pure pull with a per-reader cache (V1): 4 engineers, 1 quarter, right until the merge-on-miss rate breaks the budget.
- **Migration to push** (two teams, one quarter, no downtime): build fan-out and timelines beside the pull path; **shadow** (write timelines, keep
  serving pull, compare the two feeds per user); switch by cohort; keep pull as the rebuild path. **V3** hybrid and the rest: 2–3 teams, 2 quarters.
- **Team seams**: *publish and graph* · *fan-out and timelines* · *feed serving and ranking integration*; contracts: the post-created event
  schema, the timeline entry format, the `Rank` call with its deadline.
- **Cost, illustrative**: the timeline tier (≈ 12 TB of RAM with replicas) and fan-out writes dominate; **biggest lever: skip inactive users**
  (roughly halves inserts); second: the threshold; third: the timeline bound (500 → 300 saves 40 % of memory if nobody scrolls that far).
- **Top risks**: the threshold set once and never measured; rebuild never load-tested; ranking's budget negotiated per release instead of owned.

## 9 · Recap

Final diagram: the V3 baseline. One sentence per path: *Publish:* one transaction, an event, push IDs to active followers or one write for a
celebrity. *Read:* one timeline, a few celebrity lists, filter, rank under a deadline, hydrate. *Remove:* one write to the post, filtered on read.
*Rebuild:* pull, coalesced, rate-limited, degraded if needed.
**Common mistakes**: picking push or pull and defending it; bodies in timelines; no number on the threshold; chasing deletes into copies; an
offset for pagination; ranking with no deadline; "exactly once" fan-out; no plan for a lost shard; strong consistency for a feed; going deep on
the ranking model.
**Closing line (key-line voice):** "It's a hybrid: post IDs pushed into bounded timelines for ordinary accounts, celebrities pulled at read time,
with the line set by arithmetic and tuned with data. Correctness lives on the read path, so a delete is one write. I traded strict freshness
for seconds of eventual consistency, and every degraded mode — slow ranking, lost shard — has a fallback and a metric."

## Canon check

| Canonical point | Source | Covered at, or dismissed because |
|---|---|---|
| Feed publishing and feed retrieval as two flows | book ch. 11; cue sheet | FR1, FR2 flows; V2 |
| Fan-out on write against fan-out on read, pros and cons | book; all | Theory 3 and 5; C1 |
| Hybrid: push for most, pull for celebrities | book; cue sheet | Pick E; C1, C2 |
| Inactive users: don't fan out to them | book (as a pull advantage); cue sheet | Ch. 2; M3; ch. 8 lever |
| Graph store for follow relations; filter by mute settings | book | Ch. 4; FR4; C3 |
| News feed cache stores IDs, not objects | book; cue sheet | M4; ch. 2 (4 TB against 250 TB) |
| Five cache tiers (feed, content with hot set, graph, action, counters) | book | Ch. 4 physical; counters dismissed aloud as a separate service |
| Message queue between post and fan-out | book | M7; V2 (outbox + log) |
| Ranking as a separate stage with a budget | cue sheet | M6; C6 |
| Cursor pagination | cue sheet | C4 |
| Celebrity threshold and its transition | cue sheet (crux) | C2 |
| Deletes and blocks | cue sheet | C3 |
| Cache loss and rebuild | cue sheet | C5 |
| 48-hour catch-up curveball | cue sheet | C7 |
| Rate limiting, authentication, CDN for media | book (wrap-up) | Dismissed aloud in ch. 1 OUT: standard edge concerns, not this question's grade |
| What changed since the book | — | Ranked feeds with a candidate-generation stage are now the default; "chronological only" is a user setting, which C7 covers |

## From the old version (v3 mock, 43:48; classics round 1, 50:16)

| Reused | New | Dropped |
|---|---|---|
| Clarifying answers; estimates; the five deep dives (C1, C2 part, C3, C5, C6) and the 48-hour curveball (C7); follow-ups power reader (C2 second fix), incident (C5), ranking budget (C6), migration and memory bill (ch. 8, C8); the SVGs `push-pull`, `tail`, `fanout-tiers`, `fanout-routing`, `seq-*`, `c4-*`, `erd-*`, `redis-keys`, `midround-48h`, `load-funnel` | Theory chapter (six parts); options matrix; V1→V2→V3 on a carried baseline; five numbered flows; C4 twice-or-never; C8 observability with symptom pairs; build cost with the migration; canon check | The interviewer–candidate–coach frame; the technology-choice tables (become one slide per choice inside V2 and V3); the debrief table (becomes "what this question grades" and the recap's mistakes) |

## Budget

| Chapter | Minutes | Words | Slides |
|---|---|---|---|
| 0 Cold open | 3 | 360 | 5 |
| 1 Requirements and scope | 6 | 730 | 12 |
| 2 Estimates | 6 | 730 | 12 |
| 3 Theory | 11 | 1,330 | 18 |
| 4 API and entities | 6 | 730 | 11 |
| 5 High-level design | 12 | 1,450 | 22 |
| 6 Bridge | 1 | 100 | 2 |
| 7 Challenges (8 × ~4.6) | 37 | 4,500 | 72 |
| 8 Build cost (AUX) | 3.5 | 420 | 6 |
| 9 Recap | 3 | 360 | 6 |
| **Total** | **88.5** | **10,710** | **166** |

**Actual (script, 2026-11-20 build): 9,087 words, 164 slides.** Voice mix: candidate 83.8 %, interviewer 4.0 %, key line 7.9 %,
coach 4.3 %. Words per chapter: cold open 413 · requirements 601 · estimates 696 · theory 1,165 · API 437 · design 1,267 ·
bridge 81 · challenges 3,853 (C1 514, C2 574, C3 420, C4 424, C5 534, C6 454, C7 422, C8 471, intro 40) · build cost 251 ·
recap 323. Under the 10,700-word plan by about 15 %, mostly in the API chapter and the challenges; every beat is present.

## 5.1 Components and technologies (retrofit, 2026-11-22)

<!-- stack:outline -->

| Container | Choice | How it is built | Rejected | Theory part |
|---|---|---|---|---|
| Posts DB | PostgreSQL 16, sharded by post ID; Cassandra for the author index | Each shard is a PostgreSQL primary with a synchronous standby in another zone; the post row and an outbox row go in one transaction | One PostgreSQL primary; DynamoDB for everything; Cassandra for posts too | 03, 04 |
| Event log | Kafka, 64 partitions keyed by author, replication factor three | A relay reads the outbox through change data capture and publishes PostCreated, keyed by author | RabbitMQ; The post service calling fan-out directly; Pub-Sub or Kinesis | 06 |
| Timeline cache | Redis Cluster, a sorted set per viewer, partitioned by viewer | Each viewer has a sorted set of their 500 newest post IDs, scored by time | A relational table per viewer; A Cassandra row per viewer; Memcached | 05, 03 |
| Post cache | Memcached, a separate pool from the timelines | A feed open ends in one multi-get of fifty post IDs | Hydrating from the posts store directly; The same Redis cluster as the timelines | 05 |
| Fan-out workers | Go workers on Kubernetes, scaled on lag | Workers read PostCreated and check the author's tier | Push to every follower, always; Pull for everyone; Spark or Flink for the fan-out | 06, 07 |
| Feed service | Go services on Kubernetes, gRPC inside, a deadline propagated | The service reads the timeline, reads the celebrity lists of the authors the viewer follows, merges, filters blocked and deleted posts, asks ranking, and hydrates fifty posts | A monolith with the post service; Computing the ranked feed in the background | 08 |
| The graph and ranking | gRPC contracts with a deadline, a cache and a fallback each | The graph answers followers for fan-out and followees for reads, with blocks | Rebuilding the graph inside the feed; No fallback for ranking | 08 |

Fix-slide rejections: 1: Push to every follower for every author; 2: One fixed follower-count threshold; 3: Deleting from every follower's timeline; 4: Exactly-once delivery from the broker alone; 5: Replicating every timeline synchronously; 6: Waiting for ranking however long it takes; 7: A larger timeline: 2,000 IDs per user; 8: Dashboards of CPU and error rate.

<!-- /stack:outline -->
