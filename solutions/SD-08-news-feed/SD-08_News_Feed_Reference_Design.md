---
title: "SD-08 · The News Feed"
subtitle: "A reference solution for a system design round at the Staff bar: push for most authors, pull for a few, a line set by arithmetic, and correctness kept on the read path"
author: "design-room reference solution · practise with the simulator first"
date: "20 November 2026"
documentclass: article
fontsize: 10pt
geometry: a4paper,top=0.7in,bottom=0.75in,left=0.75in,right=0.75in
colorlinks: true
linkcolor: blue
urlcolor: blue
toc: true
toc-depth: 2
numbersections: false
---

\newpage

# How to read this document

This is the **long answer key for question `SD-08`** in
[design-room](https://github.com/nirmata78/design-room), an open-source system design interview
simulator, and the written companion to its reference-solution video. It shows how a strong Staff
candidate (L6/L7) runs the round: what to say, what to draw, and **when**. It adds the **why** behind
every line, so you can defend each choice when the interviewer asks *"why?"*, *"what is that?"* or
*"what happens when it breaks?"*.

**The document has three layers, and you will read them differently:**

1. **Part I, the system in pictures.** Read it first. It explains what a home feed is, what one post does
   from the moment it is written to the moment a follower sees it, why a few accounts decide the
   architecture, and where the load lands. There is no interview script in it, only understanding.
2. **Part II, the round, stage by stage.** This is what you do in the room. Each stage has the words to
   say, what to draw, and boxes that explain every term. The eight **challenges** of the video are
   Stage 6, and each goes further here than the video can.
3. **Part III, the internals.** How sorted sets, a partitioned log, an outbox, request coalescing and a
   cursor actually work, at the depth a round reaches when you name a mechanism and the interviewer asks
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
`Read CLAUDE.md. Mock me: SD-08, Meta, staff, full round.`
(3) Debrief against the Stage 12 self-check, then reread only the sections where you fell short.
**Do not memorise numbers.** Memorise *the order of the argument* and how to rebuild each number in
twenty seconds.

**About the numbers.** The scale figures in Stage 1 are the simulator's cue sheet. Everything derived from
them is back-of-the-envelope arithmetic, and every planning assumption (posts per user, the share of
inactive followers, bytes per timeline entry, the rebuild rate) is labelled: *given*, *illustrative*,
*initial target* or *derived*. None of them is a measurement. They are not any company's real figures,
and this is not any company's actual design. Costs are in engineer-quarters and machine sizes, not
money.

**The prompt as the interviewer reads it:**
*"Design the home feed for a social network with a billion users: the ranked list of posts a user sees
when they open the app."*

::: {.key title="The one-sentence insight to land by minute 12"}
**Neither fan-out on write nor fan-out on read works alone.** Precomputing every follower's timeline
breaks on the account with a hundred million followers; computing every feed at read time breaks the
200 ms budget for everyone else. The answer is a **hybrid with a stated threshold**: push post *IDs*
into the timelines of ordinary accounts' active followers, **pull** the celebrities' recent posts at read
time, and keep every correctness rule (deletes, blocks, audience) **on the read path**.
:::

::: why
**Why is this the insight, if every book says "hybrid"?** Because the word earns nothing. The grade is on
what comes after it: the arithmetic that puts the line near ten thousand followers rather than a million,
what happens to an account that crosses the line overnight, how a deleted post leaves millions of copies,
and what the feed does when the ranker is slow or a cache shard is gone. A candidate who says "hybrid" and
stops has repeated the textbook; a candidate who derives the line and the crossing rule has designed it.
:::

\newpage

# Part I: The system in pictures

## Vocabulary you need first

**On the write side**

| Term | What it means here |
|---|---|
| **Post** | The source of truth: one row per post, keyed by a time-sortable ID. Never copied as a body. |
| **Author index** | For each author, their post IDs newest first. The pull path, the rebuild path and catch-up read it. |
| **Outbox** | A row written in the same transaction as the post, saying "this post exists". A relay turns it into an event. No dual write. |
| **Event log** | A durable, partitioned, replayable log of post-created events, keyed by author. |
| **Fan-out** | Copying a post ID into each follower's timeline when the post is written ("fan-out on write", "push"). |
| **Tier** | Per author: *push* (fan out to active followers), *mid* (fan out to followers active today), *pull* (no fan-out). |

**On the read side**

| Term | What it means here |
|---|---|
| **Timeline** | For each reader, a bounded list (about 500) of post IDs, author IDs and times. Derived, rebuildable. |
| **Celebrity list** | For each pulled author, their last ~100 post IDs, in a replicated cache. |
| **Merge** | Reading the timeline plus the celebrity lists the reader follows, de-duplicating, filtering ("fan-out on read", "pull"). |
| **Hydration** | Fetching the post bodies for the IDs on the page from the post cache. |
| **Cursor** | An opaque token holding the score and post ID of the last item shown. The next page starts strictly after it. |
| **Fallback** | What the feed does when ranking misses its deadline: recency and close ties. |

**Properties**

| Term | What it means here |
|---|---|
| **S1** | Safety: a viewer never sees deleted, blocked or out-of-audience content for longer than 5 s. |
| **S2** | Safety: a post is never lost. The source of truth is durable even if every derived view is lost. |
| **L1** | Liveness: a post reaches its active followers' feeds within 5 s, p95. |
| **L2** | Liveness: every feed open answers within 200 ms, degraded if it must. |
| **L3** | Liveness: a lost or skipped timeline is rebuilt on its next open. |

## What a post experiences

One post by Ana, who has 2,000 followers, from the tap to the screen of a friend:

1. Ana's phone sends the post with an idempotency key. The post service writes three rows in one
   transaction: the post, the author-index entry, and the outbox row. It answers with a post ID.
2. A relay reads the outbox and publishes a *post-created* event to the log, keyed by Ana's ID.
3. A fan-out worker reads the event. Ana's tier is *push*. It pages through her followers a thousand at a
   time, keeps the ones active in the last 30 days (about 1,000 of 2,000), and adds the post ID to each
   one's timeline, trimming each to 500 entries. Then it commits the log offset.
4. Ben, a follower, opens the app. The feed service reads Ben's timeline (about 500 IDs), the recent lists of
   the six celebrities Ben follows, and Ben's block set. It merges, de-duplicates, drops blocked authors, and
   takes the top 200 by recency.
5. It asks ranking to score the 200 with an 80 ms deadline, takes the top 50, fetches their bodies from the
   post cache, drops anything deleted or not visible to Ben, and returns 50 items and a cursor.

Ana's post took a few seconds to reach Ben, and about 140 ms to show once he opened the app.

## Why a few accounts decide the design

![Followers per account, log scale, illustrative. The median account has about 200; the largest over 100 million. One post's push cost is its author's follower count.](diagrams/video-tail.pdf){width=92%}

The cost of pushing one post is its author's follower count. For the median author that is about 200
inserts, nothing. For the account at the bottom of the chart it is 110 million inserts, for one post.
Every design decision in this document follows from that chart.

![The central tension. Push pays at write time in proportion to the author's followers (red); pull pays a small read on every follower's open (blue). The hybrid follows the lower curve.](diagrams/video-tension.pdf){width=92%}

## One post, second by second

The core flow as a time table, for Ana's post (2,000 followers, tier push). Times are illustrative, at a quiet
moment; under load the fan-out lag grows and is measured per lane.

| Time | Where | What happens |
|---|---|---|
| 0 ms | phone | Ana taps *post*; the request carries an idempotency key |
| 15 ms | post service | one transaction: post row, author-index entry, outbox row; commit |
| 20 ms | phone | 201 with the post ID; Ana sees her post on her own profile, read from the posts store |
| 50 ms | relay | reads the outbox row; publishes *post-created* to the log, partition by Ana's ID |
| 80 ms | fan-out worker | consumes; tier push; asks the graph for the first page of 1,000 followers |
| 120 ms | fan-out worker | keeps the ~500 active ones; pipelines 500 inserts to the timeline shards |
| 300 ms | fan-out worker | second page; another ~500 inserts; commits the log offset |
| 2 s | Ben's phone | Ben opens the app; his timeline already holds Ana's post ID |
| 2.14 s | feed service | merge, filter, rank, hydrate; Ben sees the post |

::: why
**Why does Ana see her own post immediately, if fan-out is asynchronous?** Because her profile and her own feed
read her author index, which was written in the same transaction as the post. Read-your-own-writes is kept for
the author, which is the person who would notice; followers get eventual consistency within seconds.
:::

## Where the load lands

::: load
**At peak, illustrative, derived in Stage 2.** Feed opens about 90,000 a second, each one timeline read,
a handful of celebrity-list reads and one multi-get of 50 posts. Posts about 580 a second at the source,
becoming about 60,000 timeline inserts a second after skipping inactive followers. Timelines about 4 TB of
memory (12 TB with three replicas). Ranking about 90,000 calls a second, each with an 80 ms deadline.
:::

![The read budget as one bar: lookups and filtering 20 ms, ranking deadline 80, hydration 20, network 20; 140 used, 60 spare.](diagrams/video-budget.pdf){width=95%}

\newpage

# Part II: The round, stage by stage

**The clock** (a 75-minute round at the simulator's `typing-adjusted` pace; spoken rounds run about 50 minutes):

| Minutes | Stage | On the whiteboard |
|---|---|---|
| 0:00 to 0:12 | **Stage 1** Clarify requirements | Requirements list and an "out of scope" box |
| 0:12 to 0:21 | **Stage 2** Back-of-the-envelope (three numbers, maybe four) | Four lines of arithmetic |
| 0:21 to 0:33 | **Stage 3** API and data model | Five calls, six stores |
| 0:33 to 0:51 | **Stage 4** High-level design in three versions, with the walk-through | One baseline, three views |
| 0:51 to 1:13 | **Stage 6** Deep dives, with **Stage 7** requirements as they arrive | Marks on the baseline |
| Last 10 minutes | **Stages 8 and 9** Failure, SLOs, cost | Short list |
| When asked | **Stage 10** The EM layer (auxiliary at Staff) | Phases, teams, quarters |

**At the Staff bar you pick the deep dives.** Say which two you would go into and why: *the celebrity
post and the threshold, because that is the crux; then deletes, because correctness lives there.*

# Stage 1: Clarify requirements

Ask **eight questions, not fifteen**. Each one changes the design, so say why you are asking.

| # | You ask | The interviewer answers | What it changes |
|---|---|---|---|
| 1 | Users? | 1 billion, 500 million daily active | Sizes reads and memory; only active users need a timeline |
| 2 | Read to write? | Feed reads about 100× post writes | Optimise the read path; paying on write is acceptable |
| 3 | Followees per user, and the distribution? | Average about 200. Some accounts have over 100 million followers | The tail decides the architecture |
| 4 | Latency, ranking? | p99 under 200 ms; ranked by a scoring service, a black box | Ranking is a stage with a budget |
| 5 | Freshness? | Seconds for close follows; a minute generally | Asynchronous fan-out; priority for close ties |
| 6 | Depth? | First 50 on open, paginated | Timelines can be bounded |
| 7 | Content? | Text and images; video out of scope | The feed holds references; media is hydrated |
| 8 | Twice or never, which is worse? | Missing a close friend's post is worse; a duplicate on screen is a bug | A correctness stance: de-duplicate always; misses are the failure that matters |

::: why
**Why ask about the distribution, not just the average?** Because the average (200) supports pure push, and
the maximum (110 million) kills it. Interviewers hold the maximum back for candidates who ask. Asking it
is the single strongest requirements signal in this question.
:::

::: why
**Why ask "twice or never"?** It forces a correctness stance before the design exists. Feeds have two
failure shapes: duplicates (from at-least-once delivery and offset pagination) and gaps (from lag, from
pagination, from a lost view). Knowing which the business minds more tells you where to spend effort.
:::

**Functional requirements:** FR1 **publish** a post visible to followers · FR2 **read** the ranked feed,
first 50 then paginated with a stable cursor · FR3 **follow and unfollow** with effect on the feed · FR4
**remove**: delete, block, change audience, gone from every feed within seconds.

**Non-functional requirements** (initial targets): feed p99 under 200 ms; a post visible to active
followers within 5 s at p95; read availability 99.95 %; removed content gone within 5 s; a post never lost.

**Scope.** *In:* publish, feed, pagination, follow effects, deletes, blocks and audience, ranking as a
stage. *Out, and say so:* the ranking model, ads, media upload and transcoding, search, notifications
(SD-12), the graph service internals (SD-14), like and comment counters.

> "The core is four things: a source of truth for posts, a per-reader view built by push and pull, a read
> path inside 200 milliseconds, and a rebuild path for when the view is lost."

# Stage 2: Back-of-the-envelope

## How to do estimates in an interview

Four lines of arithmetic, each ending in a decision. State the input, do the multiplication, say what it
changes. A number that changes nothing is decoration.

::: {.key title="Top-3 number 1: feed reads"}
**Arithmetic.** 500 M daily users × 5 opens ÷ 86,400 s about 29,000 a second; × 3 for the peak about **90,000 a
second**. Pure pull would multiply that by 200 followees: **18 million author-index reads a second.**
**What it means.** Reads dominate, and merging 200 authors per open is too expensive at this scale.
**How it changes the design.** Precompute for most readers. Pull stays as the first version (right at 1 %
of this scale), the rebuild path, and the celebrity path.
**Say.** "Ninety thousand opens a second. A two-hundred-way merge on each is eighteen million reads a
second, so most of the feed has to be precomputed."
:::

::: {.key title="Top-3 number 2: the celebrity post"}
**Arithmetic.** About 580 posts a second × 200 followers about 120,000 inserts a second for the whole fleet.
One post by an account with 110 M followers ÷ 120,000 a second about **900 s, 15 minutes**.
**What it means.** One post holds the fan-out fleet for a quarter of an hour and every ordinary author
waits behind it.
**How it changes the design.** Celebrities are not fanned out; they are pulled at read time.
**Say.** "One celebrity post is a hundred million writes. That number kills pure push."
:::

::: {.key title="Top-3 number 3: memory"}
**Arithmetic.** 500 M active users × 500 entries × 16 B (post ID, author ID, time, packed) = **4 TB**, 12 TB
with three replicas. With 1 KB bodies instead: about **250 TB**.
**What it means.** IDs fit a memory tier; bodies are sixty times larger and every edit or delete would chase
millions of copies.
**How it changes the design.** Timelines hold IDs; bodies come from one post cache.
**Say.** "IDs, not bodies: four terabytes instead of two hundred and fifty, and a delete is one write."
:::

## The full table, row by row

| Number | Arithmetic | Label | Decision |
|---|---|---|---|
| Feed opens | 500 M × 5 ÷ 86,400 about 29,000/s; × 3 about 90,000/s | given → derived | Serve from memory |
| Pure pull | 90,000 × 200 = 18 M author-index reads/s | derived | Precompute for most; pull is the MVP |
| Posts | 500 M × 0.1 ÷ 86,400 about 580/s | illustrative | Writes are tiny at the source |
| Fan-out | 580 × 200 about 120,000 inserts/s | derived | Push multiplies writes 200× |
| Active only | half of followers active in 30 days → about 60,000/s | illustrative, to measure | Skip inactive followers |
| Celebrity post | 1.1 × $10^{8}$ ÷ 120,000 about 900 s | derived | Pull celebrities |
| Line, write side | $10^{4}$ followers about 0.08 s of the fleet; $10^{6}$ about 8 s | derived | Above ~$10^{5}$ one post misses 5 s alone |
| Line, read side | each pulled author about 0.5 ms; 20 about 10 ms | illustrative | Average reader pulls a handful |
| Timelines | 500 M × 500 × 16 B = 4 TB; × 3 = 12 TB | derived | IDs in memory |
| Bodies (the mistake) | 500 M × 500 × 1 KB about 250 TB | derived | Never copy bodies |
| Read budget | 20 + 80 + 20 + 20 = 140 of 200 ms | initial target | Ranking gets a deadline |
| Lost shard | 5 M users × 20 % ÷ 600 s about 1,700 rebuilds/s × 200 = 340,000 reads/s | illustrative | Coalesce, limit, degrade |

::: why
**Why 16 bytes an entry?** A 64-bit post ID, and the author ID and time packed into the member or score of
a sorted-set entry. Real overhead in an in-memory store is higher (pointers, encodings); the honest
statement is "4 TB of payload, budget for perhaps twice that in memory". The decision does not change.
:::

::: warn
**The arithmetic trap.** Candidates multiply posts by *average* followers and conclude push is fine. The
average hides the tail. Always compute the largest author's single post alongside the average.
:::

# Stage 3: API and data

## The API

| Call | Serves | Reads / writes | Notes |
|---|---|---|---|
| `POST /v1/posts` + `Idempotency-Key` | FR1 | writes Post, AuthorIndex, Outbox | one transaction |
| `GET /v1/feed?cursor&limit=50` | FR2 | reads Timeline, CelebrityRecent, Blocks, PostCache | cursor, not offset |
| `POST` / `DELETE /v1/follows/{id}` | FR3 | writes Follow | no backfill |
| `DELETE /v1/posts/{id}`, `POST /v1/blocks/{id}`, `PATCH /v1/posts/{id}` | FR4 | writes Post.status, Blocks | invalidation event |
| internal `Rank(viewer, ids, deadlineMs)` | FR2 | none | IDs in, scores out |

```http
POST /v1/posts HTTP/1.1
Idempotency-Key: 7c1e9f4a-2b
Content-Type: application/json

{"text": "Launch day", "mediaIds": ["m_88"], "audience": "followers"}

HTTP/1.1 201 Created
{"postId": "1860371549216768000"}
```

::: why
**Why a time-sortable post ID?** A 64-bit ID made of a millisecond timestamp, a machine number and a
sequence sorts by creation time. Timelines and author indexes can then order by ID alone, and a cursor can
compare IDs without fetching times. It is generated without coordination on each post-service node.
:::

::: why
**Why an idempotency key on a post?** Phones retry on bad networks. Without a key, a retry after a lost
response creates a second post. The key is stored with the post ID for a day; a retry returns the same ID.
:::

```http
GET /v1/feed?limit=50&cursor=eyJzIjowLjgyLCJwIjo1MX0 HTTP/1.1

HTTP/1.1 200 OK
{"items": [{"postId": "1860371549216768000", "author": "@ana",
            "text": "Launch day", "media": ["https://cdn/m_88.jpg"]}],
 "nextCursor": "eyJzIjowLjc3LCJwIjo5Mn0", "fallback": false}
```

::: why
**Why a cursor and not an offset?** New posts arrive at the top while a reader scrolls. An offset counts from
the top, so page two repeats what moved down and skips what moved past. A cursor holds the last item's
score and ID, and the next page is everything strictly after it, whatever arrived above.
:::

## The data model

![Conceptual model. Users author posts, follow users and block users; the timeline entry is a weak entity, derived and rebuildable.](diagrams/video-erd-chen.pdf){width=88%}

![Physical model. Three stores of truth (post, author index, follows) and three in-memory derived structures (timelines, celebrity lists, block sets).](diagrams/video-erd-physical.pdf){width=95%}

| Store | Key | Holds | Truth or derived | Lose it? |
|---|---|---|---|---|
| Posts | `post_id` | the post | **truth** | never: replicated, backed up |
| Author index | `(author_id, time desc)` | post IDs per author | **truth** (secondary index) | rebuild from posts, slowly |
| Graph | `user_id`, both directions | follows, blocks, counts | **truth** (another service) | not ours to lose |
| Timeline cache | viewer | at most 500 post IDs | derived | rebuild by pull (C5) |
| Celebrity recent | author | last 100 IDs | derived | rebuild from the author index in seconds |
| Post cache | `post_id` | hydrated post | derived | refill from posts, with coalescing |

::: why
**Why say "truth or derived" before any failure question?** It is the recovery plan in one column. Anything
derived can be thrown away and rebuilt; anything true must be durable. Interviewers who later ask "a cache
shard is gone" are checking whether you already knew.
:::

**Hot keys and their writers.** A celebrity's recent list is read by millions of readers: replicate it to many
cache nodes (or keep a copy in each feed-service process for a few seconds). A viral post's body in the post
cache is the same pattern. Timelines are written by fan-out workers and the rebuild path, read by the feed
service, and never by anything else.

# Stage 4: High-level design

Draw **one baseline** and change it three times. The boxes never move; each version adds what the objection
to the one before demands.

## Version 1: the simplest thing that works

![V1. The post service writes posts and the author index; the feed service, on every open, reads followees and blocks from the graph, merges the recent posts of 200 authors, ranks and returns.](diagrams/video-base-v1.pdf){width=95%}

Pull on every open, with a per-reader result cache for a minute. At one percent of this scale it is the
right design: no fan-out, no timelines, nothing to rebuild.

**Objection.** At 90,000 opens a second, every cache miss is a 200-way merge: 18 million author-index reads
a second at peak. And a cached result is up to a minute old, so a close friend's post waits.

## Version 2: push

![V2. Outbox, event log and fan-out workers insert post IDs into each active follower's timeline; the read is one timeline read, ranking and a multi-get from the post cache.](diagrams/video-base-v2.pdf){width=95%}

The post and an outbox row commit together; a relay publishes to a log keyed by author; fan-out workers page
through followers and insert IDs into bounded timelines; the feed reads one timeline, ranks and hydrates.

**Objection.** One celebrity post holds the fleet for 15 minutes; about half the inserts go to users who will not
open the app this month; a deleted post sits in millions of timelines.

## Version 3: the hybrid, correct on the read path

![V3. A tier per author: push below the line, one write to a celebrity list above it; readers merge the few celebrities they follow; the feed filters every page and ranks under a deadline.](diagrams/video-base-v3.pdf){width=95%}

Four changes. (1) A tier per author: above the threshold, one write to the author's recent list and no fan-out.
(2) Fan-out to active followers only. (3) A visibility filter on every page. (4) Ranking with a deadline and a
fallback. The rebuild path (Challenge 5) and probes (Challenge 8) are added in the challenges.

## The numbered flows, one per functional requirement

![FR1, an ordinary author: (1) post, (2) one transaction, (3) outbox to the log, (4) a worker consumes, (5) followers paged from the graph, (6) IDs inserted into active followers' timelines.](diagrams/video-flow-fr1.pdf){width=95%}

![FR1, a celebrity: the same event, then one write to the author's recent list. No fan-out.](diagrams/video-flow-fr1c.pdf){width=95%}

![FR2, read: (1) get feed, (2) timeline, (3) celebrity lists, (4) blocks, (5) rank with a deadline, (6) hydrate, (7) fifty items and a cursor.](diagrams/video-flow-fr2.pdf){width=95%}

![FR3, follow: one edge; nothing is backfilled.](diagrams/video-flow-fr3.pdf){width=95%}

![FR4, remove: one write to the post, an invalidation, and the filter on the next page.](diagrams/video-flow-fr4.pdf){width=95%}

**Follow, in words.** Following writes one edge. If the followee is a celebrity, the next read's merge already
includes them. If they are an ordinary author, their next post arrives by fan-out. To make a follow feel
immediate, insert the followee's last few post IDs into the follower's timeline: cheap, bounded, optional.
Unfollow adds the author to the reader's filter set; the IDs already in the timeline are filtered out and age
out.

## The C4 views and the sequences

![C4 context. Authors and readers; ranking, the social graph and the media CDN belong to other teams.](diagrams/video-c4-context.pdf){width=92%}

![C4 containers. The write path across the top, three in-memory stores in the middle, the stateless feed service below.](diagrams/video-c4-containers.pdf){width=95%}

**Why each container is separate.** The *post service* owns the only write of truth and must stay simple. The
*event log* decouples fan-out from posting and lets other consumers (search, notifications) read the same
events. *Fan-out workers* scale with followers, not with requests. The three *caches* have different keys,
lifetimes and owners. The *feed service* is stateless, so it scales with opens.

![Sequence: publish. One transaction, then asynchronous fan-out; the log offset is committed last.](diagrams/video-seq-publish.pdf){width=95%}

![Sequence: read. Timeline, celebrity lists, merge and filter, rank with a deadline, hydrate.](diagrams/video-seq-read.pdf){width=95%}

The fan-out worker, which is the mechanism, so it is worth writing:

```python
def on_post_created(evt):
    if evt.tier == "pull":                 # celebrity: one write
        celeb_recent.lpush(evt.author, evt.post_id, trim=100)
    else:
        for page in graph.followers(evt.author, page_size=1000):
            active = [f for f in page if last_seen(f) > now() - DAYS_30]
            if evt.tier == "mid":
                active = [f for f in active if last_seen(f) > now() - DAYS_1]
            timelines.add_many(active, evt.post_id, trim=500)
    log.commit(evt.offset)                  # last: re-deliver, never lose
```

Run it against a crash: the worker dies after inserting into half the followers and before committing the
offset. The event is re-delivered and the worker inserts into all followers again. Because a timeline is a
sorted set keyed by post ID, the first half's inserts are no-ops. **At-least-once delivery, idempotent
effect.** Run it against a duplicate event: the same. Run it against a huge follower list: it pages, so
memory stays bounded, but one event can take long; the mid tier and the threshold bound that.

::: warn
**What the first draft glosses over: the tier at the time of the event.** If the tier is looked up when the
worker runs, an account that crosses the line between the post and the fan-out is handled with the new tier.
That is harmless in both directions (the merge covers pull, and a late push is just a push), but say which
you chose. The design above stamps the tier on the event at post time, so the decision is reproducible.
:::

The read path:

```python
def get_feed(viewer, cursor, limit=50):
    ids = timelines.get(viewer)                           # about 500 IDs, ~5 ms
    for author in graph.followed_celebrities(viewer):     # a handful
        ids += celeb_recent.get(author)
    blocked = blocks.get(viewer)
    cand = dedupe(i for i in ids if i.author not in blocked)
    cand = top_by_time(cand, 200)
    scores = ranking.score(viewer, cand, deadline_ms=80) or fallback(cand)
    page = after(cursor, sorted(cand, key=scores.get, reverse=True), scores)[:limit]
    posts = [p for p in post_cache.multi_get(page) if visible(p, viewer)]
    return posts, make_cursor(page[-1], scores)
```

::: warn
**What the first draft glosses over: a page shorter than fifty.** The visibility filter runs *after* the page
is cut, so a page with three deleted posts returns 47 items. Either over-fetch (take 60, return 50) or accept
short pages and say so. Over-fetching is the usual answer; the cost is ten extra multi-get keys.
:::

**The latency budget.** Lookups and filtering 20 ms, ranking 80 ms as a hard deadline, hydration 20 ms,
network 20 ms: 140 of 200, with 60 spare for a slow shard or a pause.

# Stage 5: Why these choices

## Timelines in an in-memory sorted set per viewer

**Why here.** Timelines are read on every open, bounded, and rebuildable: losing one is a latency problem,
not data loss. A sorted set keyed by post ID gives idempotent inserts, ordering by time and cheap trimming.
**Internals to explain.** A skip list plus a hash map per key; insert and trim are logarithmic; a pipeline of
many `add` commands amortises round trips for fan-out.
**Alternatives.** A wide-column row per viewer (durable, but every open is a disk read: rejected for the hot
path, fine as a cold tier). A relational table (rejected: write amplification on an index for 60,000 inserts
a second). **Verdict:** memory, replicated, partitioned by viewer.

## Posts in a sharded store, an author index in a wide-column store

**Why here.** Posts are written once, read by ID, and must never be lost. The author index is a range scan
per author, newest first, which wide-column stores do natively (partition = author, clustering = time).
**Alternatives.** One relational primary (rejected at this write and read volume; fine at MVP scale).

## An outbox and a partitioned log for fan-out

**Why here.** Writing the post and calling fan-out separately is a dual write: a crash between them loses the
fan-out or fans out a post that rolled back. The outbox makes "the post exists" and "an event will be
published" one transaction. The log is replayable, absorbs bursts, and serves many consumers.
**Alternatives.** The post service calling fan-out directly (rejected: dual write, no replay); change-data
capture on the posts table (acceptable: the same guarantee, less explicit).

## The graph as a service

**Why here.** Both directions are queried constantly (followers for fan-out, followees for reads), counts
drive tiers, and blocks are a correctness input. It is another team's system with a contract (SD-14).

## Ranking as a stage with a deadline

**Why here.** Ranking is the largest piece of the budget and changes on another team's schedule. The feed
must degrade, not fail, without it.

# Stage 6: Deep dives

Eight challenges, in an order where each fix creates the next question. The crux, the celebrity and the
threshold, gets two.

## 6.1 The celebrity post (the crux, part one)

**The question.** *"Someone with a hundred million followers posts. Walk me through it."*

**Weak answer.** "The workers push it to every follower; we add workers."

**The case.** At 20:00 an account with 110 M followers posts. At the fleet's 120,000 inserts a second that is
about 15 minutes. Thirty seconds later Ana posts to 300 friends; her event waits behind the star's (or the
workers are saturated, which amounts to the same). Her friends see her post 14 minutes late, and the star
posts again at 20:31. Even at ten times the fleet, one post costs 90 seconds of all of it.

**Mechanism.** The event carries the author's tier. Above the threshold, the worker appends the post ID to
`celebrity_recent:{author}` (one write) and does not fan out. On the read path, the feed service reads the
recent lists of the celebrities the reader follows (a handful) and merges them with the timeline,
de-duplicating by post ID. The lists are hot keys, so they are replicated to many cache nodes or cached in
each feed-service process for a few seconds.

![Challenge 1 fix: one write to the celebrity list; readers merge.](diagrams/video-ch1-fix.pdf){width=95%}

![Sequence: one write on publish, a small merge on read.](diagrams/video-seq-celebrity.pdf){width=95%}

**Why it works.** Push costs a write multiplied by followers; pull costs a small read multiplied by opens.
For the tail, the read is far cheaper, and it is paid by the reader inside the budget rather than by every
other author in delay.

**The push: a burst of ordinary posts** (New Year's Eve, ten times the rate, all ordinary accounts). No single
author is the problem; the volume is. *Priority lanes:* fan out to close-tie followers first (an interaction
score), the rest after. *Spread:* the log is keyed by author, so a burst of many authors spreads across
partitions and workers. *Pull covers lag:* lag is a metric per lane, and while the general lane is behind,
the read merge pulls the recent posts of a reader's top ties. **Honest limit:** for those minutes the general
one-minute target may slip; close ties keep their seconds.

> "One celebrity post would be a hundred million writes, minutes of fan-out that block everyone else. So above
> a follower threshold I don't fan out at all: the post goes into a small recent-posts list for that author,
> and each reader merges the few celebrities they follow at read time. That costs a few milliseconds per
> open, which I've budgeted."

## 6.2 Where is the line, and who crosses it? (the crux, part two)

**The question.** *"Where exactly is the threshold, and what happens to an account that crosses it?"*

**Weak answer.** "A million followers."

**The case.** At a million, one post is a million inserts, about 8 s of the fleet: past the 5 s target on its
own. An account goes from 9,000 followers on Monday to 2 million on Tuesday with 200 posts already pushed.
A power reader follows 5,000 accounts, 300 of them celebrities: 300 lists × 0.5 ms = 150 ms.

**Mechanism: three tiers, from both sides of the arithmetic.**

| Tier | Followers | Fan-out | Why |
|---|---|---|---|
| Push | under ~10 k | every follower active in 30 days | cheap per post; fresh |
| Mid | ~10 k to 100 k | only followers active in the last day | an order of magnitude cheaper |
| Pull | over ~100 k | none: one write to the recent list | a post alone would miss the freshness target |

The write side says one post's fan-out must finish well inside 5 s on a fair share of the fleet. The read side
says the average reader pulls fewer than about twenty authors. Start at 10 k, measure, tune: a config value.

**Crossing.** A tier job reads follower counts hourly. Up at 100 k, down only below 50 k (hysteresis, so an
account near the line does not flap). Crossing up: new posts become one write each; the IDs already pushed
stay and age out; readers' merge shows new posts from the first minute. Crossing down: new posts are pushed
again; the merge still shows the recent ones until they age out of the list. **No backfill in either
direction**, because the read merge covers the gap.

![Sequence: crossing the line needs no backfill.](diagrams/video-seq-tier.pdf){width=95%}

**The push: the power reader.** Treat the tail of readers like the tail of authors. For readers who pull more
than about 50 authors, a background job merges their celebrity lists every few minutes into their timeline,
so their open is one read again; the live merge is capped at the top 50 celebrities by interaction. **Honest
limit:** for those readers, a celebrity's post may be a few minutes late.

::: warn
**What the first draft glosses over: the merge must know the tier.** The read path merges only the lists of
authors the graph marks as pulled. If the tier job and the graph's "followed celebrities" list disagree for
a mid-tier author, that author's posts reach nobody: no push and no pull. Make the tier the single input to
both decisions, and probe it (6.8 is exactly this failure).
:::

> "I set the line from both sides: one post's fan-out must finish inside the freshness target, and the average
> reader should pull only a handful of authors. That puts it around ten thousand followers, as a config value
> I'd tune with data. Crossing it needs no backfill because the read merge covers recent posts, and the rare
> reader who follows hundreds of celebrities gets their merge precomputed."

## 6.3 Delete, block, unfollow (correctness)

**The question.** *"A user deletes a post, or blocks someone. That post ID is already in millions of
timelines. How does it disappear?"*

**Weak answer.** "Fan out a delete to every timeline that has it."

**The case.** Ana posts to 3 M followers; 40 s later she deletes it. A delete fan-out starts behind the insert
fan-out and races it: wherever the insert lands after the delete, the post stays. Ben blocks Cal; 500 of
Cal's posts are already in Ben's timeline.

**Mechanism: correctness on the read path; cleanup is cosmetic.** The delete writes the post's status once and
emits an invalidation for the post cache. Every page is hydrated through the post cache, and anything
deleted or out of audience is dropped. The merge drops authors in the reader's block, mute and unfollow set
(small, cached per reader). A background job removes stale IDs from timelines later.

![Challenge 3 fix: hydrate from the post itself and filter by the reader's sets.](diagrams/video-ch3-fix.pdf){width=95%}

![Sequence: one write, filtered on every page.](diagrams/video-seq-delete.pdf){width=95%}

**Why it works.** S1 is decided at one place, the post's own row, read on every page. The bound is the cache
invalidation time.

**The push: the invalidation event is lost.** Post-cache entries live at most 5 minutes, so a lost event costs
one lifetime. To keep the 5 s bound even then, deletes and audience changes also write a small
*recently removed* set that hydration checks for an hour. **Honest limit:** a post already rendered on a phone
stays until the next refresh.

::: warn
**What the first draft glosses over: audience changes are not deletes.** A post moved from "public" to "close
friends" must disappear for some viewers and not others. The filter needs the post's audience and the viewer's
relationship, both of which hydration already has; a delete-only design misses it.
:::

> "Fanned-out IDs are copies, so I don't trust them. Every page is hydrated from the post itself and filtered by
> the reader's block and unfollow set, so a delete is one write that takes effect within seconds everywhere.
> Cleaning the IDs out of timelines is a background job, and it's cosmetic."

## 6.4 Twice, or never (correctness)

**The question.** *"You said a duplicate on screen is a bug and a missed close-friend post is worse. Where do
each come from in your design?"*

**Weak answer.** "The log delivers exactly once."

**The case.** Worker W3 inserts post p9 into 1,000 timelines and crashes before committing its offset; W7
re-reads and inserts again. A reader takes page one with `offset=0`; twelve new posts arrive; page two with
`offset=50` repeats twelve items and skips twelve.

**Mechanism.** A sorted set keyed by post ID makes a re-delivered insert a no-op. A cursor holds the last item's
score and ID; the next page is everything strictly after that pair. The merge de-duplicates across the timeline
and the celebrity lists. Gaps are bounded by fan-out lag, measured per lane.

```python
def make_cursor(last_id, scores):
    return encode({"s": scores[last_id], "p": last_id})

def after(cursor, ranked, scores):
    if cursor is None:
        return ranked
    c = decode(cursor)
    # strictly after the last item shown, whatever arrived above it
    return [i for i in ranked if (scores[i], i) < (c["s"], c["p"])]
```

![Sequence: re-delivery is a no-op; the next page starts after the last item.](diagrams/video-seq-dedupe.pdf){width=95%}

**The push: ranking reorders between pages.** Scores in a cursor mean nothing if the next request re-ranks. Keep
the first page's ranked candidate list (a few hundred IDs) for the session with a short lifetime; later pages
walk it. New posts appear on refresh, which starts a new session.

::: warn
**What the first draft glosses over: the tie.** Two items with the same score: comparing the score alone skips
one of them. The cursor compares the pair (score, post ID), which is a strict total order.
:::

> "Fan-out is at-least-once, so inserts are idempotent: the timeline is keyed by post ID. Pagination uses a cursor
> holding the last item's score and ID, never an offset, and the ranked list for a session is kept so page two
> doesn't reshuffle page one."

## 6.5 A timeline shard is gone (failure recovery)

**The question.** *"A timeline cache shard is lost. One user in a hundred opens to an empty feed. What do they
see, and how do you recover?"*

**Weak answer.** "Restore it from a backup." A backup of a cache is hours old, slow to load, and users open the
app meanwhile.

**The case.** At 20:00 a shard with 5 M users' timelines is lost. A fifth open within ten minutes: 1,700
rebuilds a second, each reading 200 author indexes, 340,000 reads a second. Author-index p99 goes from 5 to
400 ms, and every reader's celebrity merge reads the same store. One lost shard has become everyone's outage.

**Mechanism: rebuild by pull, coalesced, rate-limited, degraded beyond the limit.** A timeline miss triggers a
rebuild through the pull path (the code of V1), written back to the cache. One rebuild in flight per user
(coalescing: a user tapping three times starts one rebuild). A global rate limit on rebuilds (a token bucket in
front of the author indexes). Over the limit, a degraded feed immediately: the reader's celebrities plus the
recent posts of their top 20 followees by interaction, marked for a full rebuild later.

![Challenge 5 fix: the rebuild path with coalescing and a limit.](diagrams/video-ch5-fix.pdf){width=95%}

![Sequence: a token for each rebuild; a degraded feed without one.](diagrams/video-seq-rebuild.pdf){width=95%}

![The limit decides the blast radius: unlimited, 1,700 rebuilds a second and an author-index overload; limited to 500, a healthy store and a longer recovery.](diagrams/video-rebuild-wave.pdf){width=92%}

::: load
**With a limit of 500 rebuilds a second** (illustrative): 100,000 author-index reads a second from rebuilds,
on top of normal celebrity reads. The million users who open in the first ten minutes are rebuilt in about
33 minutes; meanwhile they see the degraded feed, which costs about 20 reads each.
:::

**The push: the whole timeline cluster in one region.** Serve that region's reads from another region's timeline
replica (seconds stale) while it warms; without a replica, the degraded feed for everyone; rebuild at the limit,
most active users first. **Honest limit:** a cold region takes hours to warm fully: a stated recovery time, and the
case for cross-region replicas.

::: warn
**What the first draft glosses over: the rebuild races the fan-out.** A rebuild reads the author indexes at
time T and writes the timeline at T + 200 ms. A post fanned out in between is inserted into the empty timeline
and then *overwritten* by the rebuild's write, if the rebuild replaces the key. Write the rebuild as a merge
(add the rebuilt IDs to the set), not a replace; the set's keying makes it safe.
:::

> "A timeline is a derived view, so losing it is a latency problem, not data loss. The first open rebuilds it by
> pull, with coalescing per user and a rate limit, and anyone over the limit gets a degraded but instant feed.
> The rate limit is what stops one lost shard from overloading the author index for everyone."

## 6.6 The ranker takes 300 ms (overload, latency budget)

**The question.** *"Ranking has 80 ms of your budget. Today it takes 300. What's your plan? And the ranking team
wants 120 ms for a better model."*

**Weak answer.** "Wait for it; quality matters."

**The case.** A model push takes ranking p99 from 70 to 300 ms; feed p99 goes from 160 to 420 ms; the open rate
drops; nothing in the feed service changed.

**Mechanism: a hard deadline and a counted fallback.** Call with `deadline_ms=80`. On a miss, order by recency
plus close ties, or reuse the session's last ranking. Late scores are dropped and counted; the response carries
`fallback=true`.

![Sequence: eighty milliseconds, then the fallback.](diagrams/video-seq-rank.pdf){width=95%}

**The 120 ms request: find the budget, don't move the user's deadline.**

| Option | What it costs |
|---|---|
| Pre-rank on app background or prefetch, so the slow model runs before the open | compute on opens that never happen |
| Rank the first 20 fast, the rest asynchronously | a two-stage ranking contract |
| Give 120 ms if lookups and hydration shrink by 40 ms | work in the feed team first |
| Say yes and move the p99 to 240 ms | every user pays, for a gain on some |

**The push: the fallback rate is 30 % for a week, and nobody noticed.** The fallback rate is ranking's SLI, with an
error budget (say under 1 % of opens), and ranking is paged on it. A model push that breaks the budget on its
canary is rolled back automatically.

> "Ranking gets a hard deadline inside the two hundred milliseconds, and if it misses, I rank by recency and close
> ties, so the feed degrades instead of failing. For a slower model, I'd find the budget by pre-ranking before the
> open, not by moving the user's deadline. And the fallback rate is a number someone owns."

## 6.7 Catch up on the last 48 hours (a requirement mid-round)

**The question.** *"Product adds 'catch up': a chronological view of everything from the last 48 hours, for any
user. What changes?"*

**Weak answer.** "Make the timelines longer and order them by time."

**The case.** Catch-up needs every post from the followees in 48 h (perhaps 2,000), in time order, including
celebrities and including users who were inactive. The timeline holds at most 500 ranked IDs, no celebrities,
and nothing for inactive users. Stretching it doubles the memory bill for everyone.

**Mechanism: go to the source of truth.** Merge the followees' author indexes for the window (the rebuild path),
in time order, paginated by (time, post ID), filtered by the same visibility rules, cached per user for ten
minutes. The ranked feed is untouched.

![Challenge 7 fix: catch-up reads the author indexes through the rebuild path.](diagrams/video-ch7-fix.pdf){width=95%}

![Sequence: cached result, or the rebuild path.](diagrams/video-seq-catchup.pdf){width=95%}

::: load
**Catch-up cost** (illustrative): if 2 % of opens use it, 1,800 a second at peak, each about 200 author-index
range reads (cached for ten minutes per user): up to 360,000 reads a second without the cache, much less with
it. Measure the hit rate before calling it cheap.
:::

**The push: it becomes the most used screen.** Then it earns its own materialised view: a per-user chronological
list maintained by the same fan-out event, IDs only, a 48-hour lifetime, celebrities merged at read as before.
Its price, said first: roughly doubles timeline memory for its users.

> "I wouldn't distort the ranked timeline for a query it wasn't designed for. Catch-up reads the source of truth,
> the followees' author indexes for the window, through the same path I use for rebuilds, and caches the result
> for minutes. If it becomes popular, it gets its own small view, and I'd say what that costs first."

## 6.8 How would you know the feed got worse? (observability)

**The question.** *"The feed is up and fast. How would you know it had silently got worse?"*

**Weak answer.** "Error rate and latency."

**The case.** A tier-job change marks 30 % of mid-tier authors as pull by mistake. No errors, latency unchanged.
Their posts reach followers only through the read merge, which lists only true celebrities: never shown.
Engagement drifts down 2 % over a week, and a product manager asks why.

**Mechanism: measure the promise.** Synthetic authors, one per tier, post every minute through the real path;
synthetic followers open the feed every 5 s and time the post's arrival. That is the **freshness SLI per tier**
(p95 under 5 s). In this case, the mid-tier probe stops arriving within minutes.

![Sequence: post, deliver, look, time it.](diagrams/video-seq-probe.pdf){width=95%}

**Symptom pairs: two metrics, one conclusion.**

| When you see | And | It means |
|---|---|---|
| fan-out lag up | post rate flat | workers slow or stuck, not more traffic |
| freshness bad for one tier | lag flat | a routing bug (this case) |
| ranking fallback up | ranking p99 normal | the deadline is misconfigured |
| author-index reads up | timeline hit rate down | a rebuild wave: a lost shard |
| engagement down | fallback, freshness, empty-feed rate normal | a ranking model change: ranking's to own |

**Quality, not uptime:** empty-feed rate, fallback rate, the share of items from close ties, engagement per
session against its seasonal baseline.

**The push: the memory bill doubled while users grew 10 %.** Cost is observable too: memory per active user,
the share of inserts to inactive users, entries per timeline. Usually a setting drifted: the bound crept up,
the active cut-off widened, the mid tier pushes to everyone. Pull the lever (500 entries to 300 saves 40 % of
memory if nobody scrolls that far) before buying a bigger cluster.

> "I measure the promise, not the servers: synthetic accounts in every tier post and read every minute, so I know
> post-to-visible time per tier. Then quality signals, empty feeds, ranking fallbacks, engagement against its
> baseline, catch the feed that works but got worse. And I read metrics in pairs to find the cause."

## 6.9 How the whole system degrades, in priority order

When things go wrong, the feed gives things up in this order, and the order is a design decision:

1. **Ranking quality** first: the deadline and the fallback (6.6).
2. **Freshness for distant ties**: priority lanes keep close ties fresh (6.1).
3. **Completeness for a lost view**: a degraded feed while rebuilding (6.5).
4. **Celebrity freshness for power readers**: precomputed every few minutes (6.2).
5. **Never S1**: a deleted or blocked post is filtered on every page, degraded or not (6.3).
6. **Never S2**: posts are durable; every view is derived.

# Stage 7: Requirements that arrive mid-round

| New requirement | What changes | What does not | What it costs |
|---|---|---|---|
| Catch up on 48 hours (6.7) | a new read path through the author indexes, cached | the ranked timeline | author-index reads; memory if materialised |
| A second region, active-active | timelines per region, fan-out per region from a replicated log | the posts store stays the truth | double the timeline tier; cross-region log replication |
| "Close friends" posts | audience on the post; the filter checks the viewer's relationship | fan-out (it pushes IDs either way) | a relationship lookup per filtered post |
| Pinned posts at the top | a per-author pinned ID merged at read | timelines | one more small read |
| Reshares | a reshare is a new post pointing at the original; hydration resolves both | the write path | de-duplication of the same original across reshares in the merge |

::: why
**Why is "a new consumer of the same event" the strong answer?** Because the event log already exists. Search
indexing, notifications and a chronological view are new readers of post-created events; the post service
does not change. Naming the extension point before the requirement arrives is the altitude interviewers note.
:::

# Stage 8: Failures and reliability

| Failure | Blast radius | Response |
|---|---|---|
| Fan-out lag (log backlog) | new posts late for some followers | priority lanes; lag per lane; pull covers close ties |
| Timeline shard lost | slow first loads for ~1 % of users | rebuild by pull, coalesced, limited, degraded (6.5) |
| Ranking slow or down | ranking quality drops | deadline and fallback (6.6) |
| Post-cache stampede after a deploy | posts store overload | warm caches, coalesce misses, shed low-ranked hydration |
| Celebrity list hot key | one cache node overloaded | replicate the list; a few seconds of in-process cache |
| Graph slow | merges and fan-out slow | cached followee and block sets; fan-out pauses, does not fail |
| Posts store primary failover | seconds of failed posts | clients retry with the same idempotency key |

**One incident, walked through.** Sunday 20:00: a timeline cache node fails and its replica is promoted, but the
replica was rebuilding and is half empty. *Minute 0:* empty-feed rate jumps for 1 % of users; author-index reads
rise; the rebuild limiter is at its cap; degraded feeds are served. *Minute 5:* the on-call reads the pair
"author-index reads up, timeline hit rate down" and confirms a rebuild wave, not traffic. *Minute 10:* no action
on the limiter (it is doing its job); replica health is checked. *Minute 40:* rebuilds complete; the degraded-feed
rate returns to zero. *After:* a review asks why a half-empty replica could be promoted, and adds a readiness check.

# Stage 9: SLOs, observability, cost

**SLIs, measured from outside:**

| SLI | Measured how | Target (initial) |
|---|---|---|
| Feed latency | real-user p99 for the first page, per region | under 200 ms |
| Feed availability | share of opens that return a feed (degraded counts) | 99.95 % |
| Freshness | synthetic post-to-visible time, per tier | p95 under 5 s |
| Removal | synthetic delete-to-gone time | under 5 s |
| Ranking fallback | share of opens with `fallback=true` | under 1 % (ranking's SLO) |

**Dashboard, top to bottom:** freshness per tier · feed p99 and availability · fallback rate · fan-out lag per
lane · timeline hit rate and rebuild rate · empty-feed and degraded-feed rates · engagement per session against
baseline · memory per active user.

**Cost, with the levers:**

| Item | Arithmetic | Lever |
|---|---|---|
| Timeline memory | 4 TB × 3 about 12 TB of RAM | skip inactive users; the bound; the threshold |
| Fan-out writes | about 120,000 → 60,000 inserts a second | active-only targeting |
| Post cache | the hot posts, a few TB | hit rate |
| Ranking calls | 90,000 a second | owned by ranking; pre-rank only where it pays |

# Stage 10: The EM layer (auxiliary at Staff)

**Phasing, by measured load.**

| Phase | Scope | People | Time |
|---|---|---|---|
| MVP · V1 | pull with a per-reader cache; posts, author index, graph integration, ranking call | 4 engineers | 1 quarter |
| Push · V2 | outbox, log, fan-out, timelines, post cache | two teams | 1 quarter |
| Hybrid · V3 | tiers, celebrity lists, filter, deadline, rebuild path, probes | 2–3 teams | 2 quarters |

**The migration from pull to push, with no downtime** (two teams, one quarter): weeks 1–4 build fan-out and
timelines beside the pull path, read by nothing; weeks 5–8 shadow (write timelines, keep serving pull, compare
the two feeds per user, alert on divergence); weeks 9–11 switch by cohort, 1 %, 10 %, 50 %, all, with rollback by
cohort; weeks 12–13 keep pull as the rebuild and catch-up path and remove the per-reader cache.

**Team seams.** *Publish and graph* (post service, posts store, author index; contract: the post-created event
schema). *Fan-out and timelines* (workers, tiers, timelines, celebrity lists, rebuild; contract: the timeline
entry format). *Feed serving* (read path, filter, cursor, ranking integration; contract: the `Rank` call with
its deadline). On-call is on freshness and feed latency; ranking's fallback rate pages ranking.

**With half the team.** Keep V1 longer, add the celebrity split before general push (it is where V1 hurts
first: popular authors' indexes are read by everyone), and skip the mid tier.

**Top risks.** The threshold set once and never measured. The rebuild path never load-tested. Ranking's budget
renegotiated every release instead of owned.

# Stage 11: The close

> "It's a hybrid: post IDs pushed into bounded timelines for ordinary accounts, celebrities pulled at read time,
> with the line set by arithmetic and tuned with data. Correctness lives on the read path, so a delete is one
> write. I traded strict freshness for seconds of eventual consistency, and every degraded mode, slow ranking or
> a lost shard, has a fallback and a metric. Next I'd measure the threshold with real follower data and load-test
> the rebuild path."

**What, trade-off, risk, next** in four sentences: what it is (hybrid fan-out with IDs and a read-path filter);
what it trades (strict freshness, simplicity); the biggest risk (an unmeasured threshold, an untested rebuild);
what is next (measurement, load tests, the active cut-off).

# Stage 12: Self-check after a simulator run

| | Weak | Strong | Exceptional |
|---|---|---|---|
| Requirements | no distribution question; no cuts | the tail asked; numbers; cuts | "twice or never" asked; correctness stance stated |
| Estimates | averages only | the celebrity number | both sides of the threshold; memory of IDs against bodies |
| Design | push or pull, defended | the hybrid with a threshold | crossing rules; mid tier; power reader |
| Correctness | deletes fanned out | filter on read | audience changes; short pages; tie-breaking cursor |
| Failure | "restore from backup" | rebuild by pull | coalescing, limit, degraded mode, the rebuild-fan-out race |
| Operations | uptime | freshness SLI | synthetic probes per tier; symptom pairs; the memory lever |

**Common traps.** Bodies in timelines. A round number for the threshold. Chasing deletes into copies. Offsets
for pagination. "Exactly-once" fan-out. Ranking with no deadline. No plan for a lost shard. Strong consistency
for a feed. Going deep on the ranking model.

# Part III: The internals

## Appendix A: Sorted sets, the timeline's data structure

An in-memory sorted set maps members to scores and keeps them ordered by score. Internally it is a skip list
(ordered, logarithmic insert and range read) plus a hash map from member to score (constant-time "is it there").
For a timeline: the member is the post ID (packed with the author ID), the score is the time (or the post ID
itself, which is time-sortable). Adding an existing member only updates its score, which is why re-delivery is a
no-op. Trimming to 500 is a "remove by rank" of everything below position 500. Fan-out pipelines many adds to
many keys in one round trip per shard.

## Appendix B: The outbox and a partitioned log

The outbox is a table in the same database as the posts. The post and its outbox row are written in one
transaction, so either both exist or neither does. A relay (or change-data capture) reads committed outbox rows
in order and publishes them to the log, then marks them sent; a crash re-publishes, so consumers must be
idempotent. The log is split into partitions by key (the author ID); order is kept within a partition, and a
consumer group assigns partitions to workers. A worker commits its position after doing the work, so a crash
means re-delivery, never loss.

## Appendix C: Request coalescing and rate limiting for rebuilds

*Coalescing* (single flight): the first request for a key starts the work; concurrent requests for the same
key wait for its result instead of starting their own. For rebuilds the key is the user. *Rate limiting*: a
token bucket refilled at R tokens a second; a rebuild takes a token or gets the degraded path. Both are cheap and
local; the global limit can be split per feed-service instance (R ÷ N each) to avoid a central counter.

## Appendix D: Cursors and stable pagination

A cursor is an opaque, signed token holding the position of the last item: here the pair (score, post ID). The
next page is the items strictly after that pair in the same order. Because the pair is unique (the ID breaks
ties), no item is skipped or repeated, whatever arrives above. Sign or encrypt the cursor so clients cannot
forge positions, and include a session ID if the ranked list is kept per session.

## Appendix E: Deadlines and fallbacks

A deadline is the time by which a caller stops waiting. The callee should receive it (so it can stop work that
will be thrown away) and the caller must have a plan for a miss. A fallback is only safe if it is counted: the
fallback rate is a metric with an owner and an error budget, otherwise a degraded mode becomes the normal mode
without anyone deciding it.

## Appendix F: Synthetic probes

A probe is a fake user doing the real thing on a schedule. For a feed: a synthetic author per tier posts; a
synthetic follower polls the feed until the post appears and records the time. Probes must use the real path
(same services, same caches), be excluded from product metrics, and be cheap enough to run every minute in
every region. They measure the promise to the user, not the health of a box.

## Appendix G: Time-sortable IDs

A 64-bit ID made of (milliseconds since an epoch: 41 bits) + (machine: 10 bits) + (sequence within the
millisecond: 12 bits) is unique without coordination and sorts by creation time. Each post-service node is
assigned a machine number at start; a node can issue 4,096 IDs a millisecond. Sorting by ID is sorting by time,
to the millisecond, which is all a feed needs. Clock skew between nodes reorders posts by a few milliseconds
across authors: harmless for a feed, and worth one sentence if asked.

## Appendix H: The threshold, worked once more

Suppose the fleet does 120,000 inserts a second and the freshness target is 5 s at p95. If no single post
should take more than 5 % of the fleet for more than 1 s, a post may fan out to at most 0.05 × 120,000 ×
1 s = 6,000 followers instantly, or about 60,000 if it may take 10 s at that share. That is the order of the
line ($10^{4}$ to $10^{5}$). On the read side, if a feed open may spend 10 ms on pulled authors at 0.5 ms each,
the average reader should pull at most about 20. If the follower data say the average reader follows 35
accounts above 10,000 followers, raise the line or precompute merges; the arithmetic tells you which knob
moves.

# One-page cheat card

**Thesis.** Push IDs for most authors, pull the few, set the line by arithmetic, keep correctness on the read path.

**Order of the round.** Clarify (users, ratio, the distribution, latency, freshness, depth, twice or never) ·
numbers (90,000 opens/s; 18 M reads/s for pure pull; 120,000 → 60,000 inserts/s; 15 min per celebrity post; 4 TB
against 250 TB) · API (post, feed with cursor, follow, delete, rank) · V1 pull, V2 push, V3 hybrid · eight
challenges · cost.

**The four numbers.** 90,000 opens a second · one celebrity post about 15 minutes of the fleet · 4 TB of IDs ·
140 of 200 ms.

**Eight fixes.** (1) pull celebrities; priority lanes. (2) three tiers; hysteresis; no backfill; power readers
precomputed. (3) filter on read; recently-removed set. (4) set keyed by post ID; (score, ID) cursor; session list.
(5) rebuild by pull, coalesced, limited, degraded; merge, don't replace. (6) a deadline, a counted fallback, an owner.
(7) catch-up from the source of truth. (8) synthetic probes per tier; symptom pairs; the memory lever.

**Properties.** S1 no removed content after 5 s · S2 no lost post · L1 5 s freshness · L2 200 ms · L3 rebuild on open.

**Say first.** "The tail decides the design." "IDs, not bodies." "Correctness lives on the read path." "A timeline is
derived: losing it is latency, not data loss."

**Close.** A hybrid with a line set by arithmetic, correctness on the read path, and a fallback and a metric for
every degraded mode.
