from dsl import *

# ───────────────────────── 4 · API and entities ─────────────────────────
chapter(4, "API and entities", 3, "Each call tagged with the requirement it serves and what it touches", [
 "C: The A-P-I next. Each call is tagged with the requirement it serves and the entities it reads or writes."])

S(plain("API · the calls", "Five calls, each traced to a requirement", table(["Call", "Serves", "Reads / writes", "Notes"], [
  ["<code>POST /v1/posts</code> + idempotency key", "FR1", "writes Post, AuthorIndex, Outbox", "post and event in one transaction"],
  ["<code>GET /v1/feed?cursor&amp;limit=50</code>", "FR2", "reads Timeline, CelebrityRecent, Blocks, PostCache", "cursor, never an offset"],
  ["<code>POST</code> / <code>DELETE /v1/follows/{id}</code>", "FR3", "writes Follow", "no backfill on follow"],
  ["<code>DELETE /v1/posts/{id}</code> · <code>POST /v1/blocks/{id}</code>", "FR4", "writes Post.status, Blocks", "invalidation event"],
  ["internal <code>Rank(viewer, ids, deadlineMs)</code>", "FR2", "none", "IDs and a deadline in, scores out"]], "bt sm")), [
 "C: Five calls. Post, with an idempotency key so a retried upload doesn't create two posts: it writes the post, the author index and an outbox row in one transaction. Get feed, with a cursor and a limit of fifty: it reads the timeline, the celebrity lists, the block set and the post cache.",
 "C: Follow and unfollow write one edge. Delete a post and block an account write one row each and emit an invalidation event. And internally, rank: I send I-Ds and a deadline, and get scores back. Features stay on the ranking side."])

S(plain("API · publishing", "The post is written once; everything else is derived", code('POST /v1/posts HTTP/1.1\nIdempotency-Key: 7c1e9f4a-2b\nContent-Type: application/json\n\n{"text": "Launch day", "mediaIds": ["m_88"],\n "audience": "followers"}\n\nHTTP/1.1 201 Created\n{"postId": "1860371549216768000"}', "http", hl=(2, 9)) +
  strip(("whyb", "Why it matters", "The post ID is time-sortable, so timelines can order by ID alone. A retry with the same key returns the same post."), cols="one")), [
 "C: Publishing on the wire. The client sends the text, media references and audience, with an idempotency key. The answer is a post I-D. The I-D is time-sortable, so timelines can be ordered by I-D alone without another lookup. And a retry with the same key returns the same post, not a second one."])

S(plain("API · reading", "Fifty hydrated items and a cursor", code('GET /v1/feed?limit=50&cursor=eyJzIjowLjgyLCJwIjo1MX0\n\nHTTP/1.1 200 OK\n{"items": [{"postId": "1860371549216768000",\n            "author": "@ana", "text": "Launch day",\n            "media": ["https://cdn/m_88.jpg"]}],\n "nextCursor": "eyJzIjowLjc3LCJwIjo5Mn0",\n "fallback": false}', "http", hl=(1, 7, 8)) +
  strip(("whyb", "The cursor", "It encodes the score and post ID of the last item shown. The next page starts strictly after it, whatever arrived above."),
        ("fixb", "The flag", "fallback = true tells the client, and the metrics, that ranking missed its deadline."))), [
 "C: Reading. Fifty hydrated items and a cursor. The cursor encodes the score and post I-D of the last item shown, so the next page starts strictly after it whatever new posts arrived above. An offset would repeat or skip items; that is challenge four. And a fallback flag says when ranking missed its deadline, which feeds a metric."])

S(dia("Data · conceptual", "Users author posts, follow and block users; timelines are derived", "erd-chen"), [
 "C: The conceptual model. A user authors posts. Users follow users, many to many, and both directions are queried: who I follow, for reading, and who follows me, for fan-out. Users block or mute users.",
 "C: The timeline entry is a weak entity: it exists only because a user sees a post, and it is derived. Delete every timeline entry and the feed can be rebuilt from posts and follows. That sentence is the whole recovery story."], cls="dia")

S(dia("Data · physical", "Three stores of truth, three caches derived from them", "erd-physical"), [
 "C: Physically. The post table is the source of truth, keyed by the time-sortable post I-D and sharded by it. The author index has one partition per author, newest first: it serves pull, rebuild and catch-up. Follows belong to the graph service.",
 "C: Below, three in-memory structures. The timeline per viewer: a sorted set of at most five hundred I-Ds. The celebrity recent list per author: the last hundred I-Ds, replicated to many cache nodes. And the block set per viewer, small, read on every open."], cls="dia")

S(plain("Data · six stores, one job each", "Which store owns what", table(["Store", "Key", "Holds", "Truth or derived?"], [
  ["Posts", "post_id", "the post", "<b>truth</b>"],
  ["Author index", "(author_id, time desc)", "post IDs by author", "<b>truth</b> (secondary index)"],
  ["Graph", "user_id, both directions", "follows, blocks, counts", "<b>truth</b> (another service)"],
  ["Timeline cache", "viewer", "≤ 500 post IDs", "derived, rebuildable"],
  ["Celebrity recent", "author", "last 100 post IDs", "derived, rebuildable"],
  ["Post cache", "post_id", "hydrated post", "derived, invalidated"]], "bt sm") +
  grade("Saying which stores are truth and which are derived, before any failure question, is a strong signal: it is the recovery plan.")), [
 "C: In one table. Three stores of truth: posts, the author index, and the graph. Three derived stores: timelines, celebrity lists, and the post cache. Anything derived can be lost and rebuilt. Anything true must be durable and replicated.",
 "N: Naming truth and derived before the interviewer asks about failures is the recovery plan, said early."])

# ───────────────────────── 5 · high-level design ─────────────────────────
chapter(5, "High-level design", 4, "Three versions, each answering the objection to the one before", [
 "C: The design, in three versions. Each version answers the objection to the one before. The boxes never move: every later picture is a view of the same baseline."])

S(dia("High-level design · version 1 of 3", "The simplest thing that works", "base-v1", vtag="V1",
      chip=chips("pull on every open", "right at 1 % of this scale")), [
 "C: Version one. On the top row, the write path: the author posts, the post service writes the post and its author index in one transaction. On the bottom, the read path: the reader opens the app, the feed service asks the graph for the followees and the block set, reads the recent posts of two hundred authors from the author indexes, merges, sends the candidates to ranking, and returns fifty.",
 "C: That is the honest first version. At one percent of this scale, with a short per-reader result cache, it works."], cls="dia")

S(plain("V1 · the objection", "Eighteen million reads a second, and a minute of staleness", '<div class="cards c2">'
  '<div class="cd red"><h3>Read cost</h3><p>90,000 opens/s × 200 authors = 18 M author-index reads/s whenever the result cache misses.</p></div>'
  '<div class="cd amb"><h3>Freshness</h3><p>A cached result is up to a minute old. A close friend\'s post waits for the cache to expire.</p></div></div>' +
  line("The read must be one memory lookup, not a 200-way merge.", "r")), [
 "C: The objection to version one. Every cache miss is a two-hundred-way merge, and at peak that is eighteen million author-index reads a second. And a cached result is up to a minute old, so a close friend's post waits.",
 "C: The read must become one memory lookup. That means doing the work when a post is written."])

S(dia("High-level design · version 2 of 3", "Push: precompute every reader's timeline", "base-v2", vtag="V2",
      chip=chips("outbox → log → fan-out", "IDs, not bodies", "post cache")), [
 "C: Version two, push. New boxes are outlined in blue. The post service still writes one transaction, now with an outbox row. A relay carries it to the event log, keyed by author. Fan-out workers read the event, page through the author's followers from the graph, skip the inactive ones, and insert the post I-D into each follower's timeline.",
 "C: The read path becomes: read my timeline, about five hundred I-Ds, rank, and hydrate the top fifty from the post cache. One memory read and a multi-get."], cls="dia")

S(plain("V2 · the technology, against the alternatives", "Each box, chosen against its rivals", table(["Box", "Choice", "Rejected", "Because"], [
  ["Timelines", "in-memory sorted set per viewer", "a database table; a wide-column row", "read-dominated, bounded, rebuildable: memory is the right price"],
  ["Posts + author index", "sharded store, time-sortable keys; wide-column author index", "one relational primary", "write volume and a per-author range scan"],
  ["Transport", "outbox → partitioned log → workers", "the post service calling fan-out directly", "no dual write; replayable; many consumers"],
  ["Graph", "a service with cached adjacency", "joins in the posts store", "both directions queried constantly; another team's contract"]], "bt xs")), [
 "C: The technology, each against its rivals. Timelines in memory, as a sorted set per viewer, rather than a table: they are read-dominated, bounded and rebuildable, so memory is the right price. Posts in a sharded store with time-sortable keys, and a per-author index. The transport is an outbox and a partitioned log rather than a direct call, so there is no dual write, the work is replayable, and other consumers like search can read the same events. And the graph is a service, because both directions are queried constantly."])

S(plain("V2 · the fan-out worker", "One branch per tier; commit the offset last", pseudo(
 'on PostCreated(evt):\n    if evt.tier == pull:              # celebrity\n        celeb_recent[author].push(post, keep 100)\n    else:\n        for each page of followers(author), 1,000:\n            keep followers seen in 30 days\n            if evt.tier == mid: keep seen in 1 day\n            timelines.add(page, post, keep 500)\n    commit(evt.offset)    # last: replay, never lose', hl=(2, 9))), [
 "C: The worker in code, because here the code is the mechanism. One branch per tier. A pulled author gets one write to their recent list. Otherwise, page through followers a thousand at a time, keep only the active ones, and for the mid tier only those active in the last day. Add the post I-D to each timeline, trimmed to five hundred. And commit the log offset last, so a crash re-delivers the event instead of losing it. Re-delivery is safe because the timeline is keyed by post I-D."])

S(plain("V2 · the objection", "One celebrity, half the writes wasted, and copies of deleted posts", '<div class="cards c3">'
  '<div class="cd red"><h3>The celebrity</h3><p>One post with 110 M followers holds the fleet for 15 minutes.</p></div>'
  '<div class="cd amb"><h3>Inactive followers</h3><p>About half the inserts go to users who will not open the app this month.</p></div>'
  '<div class="cd red"><h3>Copies</h3><p>A deleted post sits in millions of timelines.</p></div></div>' +
  line("The tail of authors decides the design, and correctness cannot live in copies.", "r")), [
 "C: The objection to version two has three parts. One celebrity post holds the whole fan-out fleet for fifteen minutes. About half the inserts go to users who won't open the app this month. And a deleted post now sits in millions of timelines.",
 "C: The tail of authors decides the design, and correctness cannot live in copies."])

S(dia("High-level design · version 3 of 3", "The hybrid, correct on the read path", "base-v3", vtag="V3",
      chip=chips("tier per author", "active-only fan-out", "filter on read", "ranking deadline")), [
 "C: Version three. The new box is the celebrity posts cache. Above the threshold, the fan-out worker does not fan out at all: it writes one entry to the author's recent list, the dashed purple arrow. On the read path, the feed service merges my timeline with the lists of the few celebrities I follow.",
 "C: Three more changes that do not add boxes. Fan-out goes only to active followers. The feed service filters every page against the post's status and my block set. And ranking is called with a deadline, with a fallback."], cls="dia")

S(dia("Flow · FR1 publish, an ordinary author", "Numbered: one transaction, one event, IDs into timelines", "flow-fr1"), [
 "C: The publish flow for an ordinary author with two thousand followers, by the numbers. One, the author posts. Two, one transaction writes the post, the author index and the outbox row. Three, the relay publishes the event. Four, a worker consumes it: tier push.",
 "C: Five, it pages through the followers from the graph. Six, it inserts the I-D into each active follower's timeline and trims to five hundred. The offset is committed after that."], cls="dia")

S(dia("Flow · FR1 publish, a celebrity", "The same event, one write, no fan-out", "flow-fr1c"), [
 "C: The same flow for a celebrity. Steps one to four are identical. Step five is different: one append to the author's recent list. No fan-out. The log partition is free again in milliseconds."], cls="dia")

S(dia("Sequence · publish", "One transaction, then asynchronous fan-out", "seq-publish"), [
 "C: As a sequence. The post service writes post, author index and outbox row together, and answers two-oh-one. Only then does the relay publish the event, keyed by author. The worker pages through followers, skips the inactive, inserts and trims, and commits its offset last. Nothing the client waits for depends on fan-out."], cls="dia")

S(dia("Flow · FR2 read", "Timeline, celebrities, blocks, rank, hydrate", "flow-fr2"), [
 "C: The read flow. One, get feed. Two, read my timeline, about five hundred I-Ds. Three, merge the recent lists of the celebrities I follow. Four, the graph gives me my block and mute set, and the merge drops those authors.",
 "C: Five, the top two hundred by recency go to ranking with an eighty millisecond deadline. Six, the top fifty are hydrated by multi-get from the post cache, which drops anything deleted. Seven, fifty items and a cursor go back."], cls="dia")

S(plain("V3 · the read path, in code", "Gather, filter, rank inside a deadline, hydrate", pseudo(
 'get_feed(viewer, cursor):\n    ids  = timelines[viewer]          # ~500 IDs, 5 ms\n    ids += recent posts of followed celebrities\n    drop authors viewer blocked or muted; dedupe\n    cand = top 200 by time\n    scores = rank(viewer, cand, deadline 80 ms)\n             or fallback(cand)          # counted\n    page = 50 strictly after cursor, by score\n    posts = post_cache.multi_get(page), visible only\n    return posts, cursor(last of page)', hl=(6, 7, 8))), [
 "C: The read path in code. Read the timeline. Add the recent lists of followed celebrities, a handful. Drop blocked authors, de-duplicate, keep the top two hundred by time. Score them with an eighty millisecond deadline, or fall back. Take the page after the cursor. Hydrate, and drop anything not visible to this viewer: deleted, or out of its audience. Return the page and the next cursor."])

S(dia("Sequence · read", "Merge, rank inside a deadline, hydrate", "seq-read"), [
 "C: The same read as a sequence, with times. Timeline, five milliseconds. Celebrity lists, five. Merge, de-duplicate and filter. Score two hundred with an eighty millisecond deadline. Multi-get fifty, about twenty. Drop anything deleted. Fifty items and a cursor."], cls="dia")

S(dia("Flow · FR3 follow", "One edge, and no backfill", "flow-fr3"), [
 "C: Follow. One, the request. Two, one edge is written in the graph. Three: nothing is backfilled. If the new followee is a celebrity, the next read's merge already includes them. If they are ordinary, their next post arrives by fan-out. Optionally I'd insert their last few posts so the follow feels immediate. Unfollow adds the author to my filter set."], cls="dia")

S(dia("Flow · FR4 remove", "A delete is one write, enforced on every page", "flow-fr4"), [
 "C: Remove. One and two, the delete writes the post's status, once. Three, an invalidation event drops the post from the cache. Four and five, the next read hydrates the page, sees the status, and drops the I-D. The I-Ds still sitting in timelines are harmless, and a background job removes them later."], cls="dia")

S(dia("Architecture · C4 context", "Authors write, readers open; ranking and the graph belong to others", "c4-context"), [
 "C: Now the same system in C4 terms, for the detail. The context: authors post, about six hundred a second. Readers open the feed, about ninety thousand a second at peak. The feed system depends on two systems owned by other teams, ranking with an eighty millisecond budget and the social graph, and media is served from a C-D-N, out of scope."], cls="dia")

S(dia("Architecture · C4 containers", "The write path across the top, the read path below", "c4-containers"), [
 "C: The containers. Across the top, the write path: post service, posts database, event log, fan-out workers. In the middle, three in-memory stores: the post cache, the celebrity lists, and the timelines. At the bottom, the feed service, stateless, which merges, filters, ranks under a deadline, hydrates, and writes the cursor. The graph and ranking sit outside, as dependencies with contracts."], cls="dia")

S(dia("Design · the latency budget", "Where the 200 ms go", "budget"), [
 "C: Back to the budget, now with every box named. Lookups and filtering, twenty milliseconds. Ranking, eighty, as a hard deadline. Hydration, twenty. Network, twenty. A hundred and forty used, sixty spare. The spare is not slack: it is what a slow cache shard or a garbage-collection pause eats."], cls="dia")

S(plain("Design · what V3 still owes", "It works. The details are the challenges", table(["Open question", "Challenge"], [
  ["What exactly happens on a celebrity post?", "1"],
  ["Where is the line, and who crosses it?", "2"],
  ["How does a deleted or blocked post disappear?", "3"],
  ["Twice or never: duplicates and pagination", "4"],
  ["A timeline shard is lost", "5"],
  ["Ranking misses its deadline", "6"],
  ["A query the view was not built for", "7"],
  ["How would we know it got worse?", "8"]], "bt sm")), [
 "C: Version three works end to end. What it still owes are the details, and each one is a challenge. What exactly happens on a celebrity post. Where the line is. How a deleted post disappears. Duplicates and pagination. A lost shard. A slow ranker. A new kind of query. And how we would know any of it went wrong."])
