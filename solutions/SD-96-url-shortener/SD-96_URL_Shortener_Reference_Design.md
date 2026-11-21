---
title: "SD-96 · A URL Shortener"
subtitle: "A reference solution for a system design round at the Staff bar: codes that never collide and cannot be walked, a redirect that is one memory read, and a side path for counting and takedowns that never stands in front of it"
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

This is the **long answer key for question `SD-96`** in
[design-room](https://github.com/nirmata78/design-room), an open-source system design interview
simulator, and the written companion to its reference-solution video. It shows how a strong Staff
candidate (L6/L7) runs the round: what to say, what to draw, and **when**. It adds the **why** behind
every line, so you can defend each choice when the interviewer asks *"why?"*, *"what is that?"* or
*"what happens when it breaks?"*.

The URL shortener is the most widely practised system design question there is. That is exactly why it
is still asked at every level: everyone arrives with the same diagram, and the interviewer learns most
from what a candidate does *after* the diagram. This document is written for that part.

**The document has three layers, and you will read them differently:**

1. **Part I, the system in pictures.** Read it first. It explains what the system is, what one click
   experiences, what one takedown has to reach, and where the load lands. There is no interview script in
   it, only understanding.
2. **Part II, the round, stage by stage.** This is what you do in the room. Each stage has the words to
   say, what to draw, and boxes that explain every term. The eight **challenges** of the video are
   Stage 6, and each one goes further here than the video can.
3. **Part III, the internals.** How counter ranges, keyed permutations, single flight, cache lifetimes and
   click pipelines actually work, at the depth a round reaches when you name a mechanism and the
   interviewer asks how it works.

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
`Read CLAUDE.md. Mock me: SD-96, Google, staff, full round.`
(3) Debrief against the Stage 12 self-check, then reread only the sections where you fell short.
**Do not memorise numbers.** Memorise *the order of the argument* and how to rebuild each number in
twenty seconds.

**About the numbers.** The scale figures in Stage 1 are the simulator's cue sheet. Everything derived
from them is back-of-the-envelope arithmetic, and every planning assumption (record size, the share of
hot links, cache lifetimes, the miss rate) is labelled as one: *given*, *derived*, *illustrative* or
*initial target*. None of them is a measurement. They are not any company's real figures, and this is not
any company's actual design.

**The prompt as the interviewer reads it:**
*"Design a URL shortener: a long URL goes in, a short link comes out, and anyone who opens the short link
is redirected."*

::: {.key title="The one-sentence insight to land by minute 12"}
**A URL shortener is a read path with a write path attached.** Codes must be *unique without a lock per
create* and *unguessable without a lookup*; the redirect must be *one memory read*; and nothing else
(counting, abuse, analytics) may stand between the click and the answer.
:::

::: why
**Why this sentence, and why by minute 12.** It tells the interviewer that you have found the three
places the question is graded: code generation, the hot read path, and the side paths that fight the
cache. Everything after it is a defence of one of those three. A candidate who says it early is driving
the round; one who says it at minute 40 is being driven.
:::

\newpage

# Part I: The system in pictures

## Vocabulary you need first

| Term | Plain meaning | Where it lives |
|---|---|---|
| **Code** | The seven characters after the domain, such as `aZ3kQ9x` | the link store's primary key |
| **Alias** | A code the customer chose, such as `spring-sale` | the same table, a different length |
| **Base-62** | Writing a number with 62 symbols: `a-z`, `A-Z`, `0-9` | the encoder in the create service |
| **Range lease** | A block of 1,000 IDs one create server owns for a while | the allocator, then the server's memory |
| **Keyed permutation** | A secret, reversible shuffle of the ID space | the create service, between ID and encoder |
| **Unique constraint** | The store refuses a second row with the same code | the link store |
| **Cache-aside** | Read the cache; on a miss read the store and fill the cache | the redirect service |
| **Single flight** | Many concurrent misses for one key share one lookup | the redirect service |
| **301 / 302** | Permanent and temporary redirects; the browser caches a 301 | the HTTP response |
| **Edge** | A content delivery network close to the user that can answer for us | in front of everything |
| **Lifetime (TTL)** | How long a cached copy may be served without asking | every cache layer |
| **Takedown** | Withdrawing a link everywhere, for abuse or by its owner | the takedown service |
| **Click event** | One record of one redirect, written after the answer | a local buffer, then a log |

## What one click experiences

Walk through the life of one redirect, in order, with no jargon.

1. **The browser asks.** A user taps `https://sho.rt/aZ3kQ9x`. DNS sends them to the nearest edge location.
2. **The edge.** If the edge answered this code in the last 60 seconds, it answers again: a `302` with
   the long URL. Done, in a few milliseconds, and the click appears later in the edge's logs.
3. **A redirect server.** Otherwise the request reaches one of many identical, stateless redirect
   servers in the user's region. It looks in its own memory first.
4. **The shared cache.** On a local miss, it asks the shared cache: about a millisecond.
5. **The link store.** On a miss there too (about 1 % of requests), it reads the link store, then fills
   both caches.
6. **The answer.** It checks the link's status and expiry and answers `302 Location: ...`, or `404` for
   an unknown code, or `410 Gone` for a withdrawn one.
7. **After the answer.** Only now does it append a click event to a local buffer. Nothing in this step
   can delay the answer.

::: say
The redirect is the product. It is answered from memory in almost every case, and everything we want to
know about it, we learn after it has been answered.
:::

## One takedown, everywhere it has to reach

The same link, seen from the other side. A phishing report arrives at 15:00. Copies of the answer exist
in five places: the link store, the shared cache, the in-process memory of every redirect server in every
region, the edge in dozens of cities, and the browsers of everyone who received a permanent `301`. A
takedown is only as fast as the slowest copy. This is why every cache lifetime in this design is chosen
with the five-minute takedown target in view, and why `301` is not the default.

![Speed against control: every layer closer to the user answers faster and is harder to count or to take back.](diagrams/video-tension.pdf){width=95%}

## The whole design on one page

![The final design. Create on top, the redirect across the middle, side paths along the bottom, probes on the left, a replica per region on the right.](diagrams/video-base-final.pdf){width=100%}

## Where the load lands

::: load
**Redirects:** 4,000 a second on average, 40,000 a second on one code at a viral peak. **Shared cache:**
about 4,000 lookups a second in steady state, much less for hot codes once in-process caches are warm.
**Link store:** about 40 reads a second (1 % misses), up to 4,000 a second if a cache tier is cold.
**Creates:** 40 a second, 400 at peak. **Allocator:** 0.4 leases a second. **Click log:** 0.8 MB a
second. **Takedowns:** a handful an hour, each reaching every cache layer.
:::

\newpage

# Part II: The round, stage by stage

| Stage | Minutes (of 60) | What you produce |
|---|---|---|
| 1 Clarify | 0–5 | Six questions; four functional requirements; numbers; IN and OUT |
| 2 Estimates | 5–10 | Code length, the hot set, the store's real load, the latency budget |
| 3 API and data | 10–16 | Four calls and one internal; the redirect headers; the link table |
| 4 High-level design | 16–28 | V1, V2, V3; four numbered flows |
| 5 Technology | inside 4 | One sentence per choice, against the alternative |
| 6 Deep dives | 28–50 | Two to four of the eight challenges, chosen by the interviewer |
| 7 Mid-round requirement | inside 6 | Billed clicks, or editable targets |
| 8–10 Failure, SLOs, cost, EM layer | 50–56 | Two minutes each, prioritised |
| 11 Close | 56–58 | Four sentences |

# Stage 1: Clarify requirements

Ask six questions before drawing. Each answer below is the simulator's, and each changes the design.

| Question | Answer | What it changes |
|---|---|---|
| How many links, how many clicks? | 100 M new links a month; 10 B redirects a month; a viral link can take 40,000 clicks a second | Read to write is 100 : 1; the peak is one key |
| How long does a link live? | Forever by default; optional expiry | The code space must last a decade; codes are a one-way door |
| Custom aliases? | Yes, for paying users, first come first served | A uniqueness race between customers; the store must decide |
| Analytics? | Clicks per link by day and by country; not billed today, maybe later | Lossy counting is allowed, and that decision is not permanent |
| Abuse? | Phishing exists; a reported link must be dead everywhere within five minutes | Every cache layer is in scope; 301 becomes a question |
| Who calls us? | Browsers, and integrators creating links in bulk | Idempotent create; a rate limit per key |

::: why
**Why ask about abuse at all.** Because "dead everywhere within five minutes" is the requirement that
fights the caches. A candidate who never asks designs a fast system that cannot take back a phishing
link, and the interviewer will ask in the last ten minutes, when there is no time to redesign.
:::

**Functional requirements.** FR1 *create* (long URL in, short link out; alias and expiry optional; a retry
gets the same answer) · FR2 *redirect* (a code gets a `302`, `404` or `410`) · FR3 *count* (clicks per link
per day per country, within minutes) · FR4 *withdraw* (owner delete or trust-and-safety block, effective
everywhere within five minutes).

**Non-functional requirements** (initial targets, not measurements): redirect p99 under 20 ms at the
server; redirect availability 99.99 %; create p99 under 200 ms and 99.9 %; takedown within 5 minutes at
every layer; counts may lag by minutes and lose a tiny, measured fraction until clicks are billed.

**Out of scope, said aloud:** the malware classifier itself (we call it); accounts and billing; QR codes
(a picture of the same link); link-in-bio pages; editing a link's target. An edit is, for every cache, a
takedown plus a create, so it rides on the takedown path (Stage 7).

> The core is three things: a code generator that never collides, a redirect path that is one memory
> read, and a side path for counting and withdrawal that never sits in front of it.

# Stage 2: Back-of-the-envelope

## How to do estimates in an interview

Say the input, do the arithmetic aloud, round hard, and end every number with the decision it drives.
An estimate that changes nothing is decoration. In this question three numbers change the design.

::: {.key title="Number 1 · How long is a code"}
Links in ten years: 10^8^ a month × 12 × 10 = **1.2 × 10^10^**. Base-62 with six characters gives 62^6^ $\approx$
5.7 × 10^10^, only 4.7 times the need. Seven characters give 62^7^ $\approx$ **3.5 × 10^12^**, about 290 times.
*Decision:* seven characters; and random codes would collide with probability 1.2 × 10^10^ ÷ 3.5 × 10^12^
$\approx$ 0.34 % per create by the end of year ten, which a retry absorbs.

> Seven characters: three and a half trillion codes for twelve billion links, so random codes would retry
> a third of a percent of the time by year ten, and counter codes never collide at all.
:::

::: {.key title="Number 2 · What the store really sees"}
Redirects: 10^10^ ÷ 2.6 × 10^6^ s $\approx$ **4,000 a second**. If the cache misses 1 %, the store sees **40 a
second**. If the cache tier is cold, it sees all 4,000. *Decision:* the store is not on the hot path in
steady state, so its sizing is about storage and cold starts, and protecting it from a cold cache is a
design problem (Challenge 3).
:::

::: {.key title="Number 3 · The latency budget"}
At the server, with a miss: cache 1 ms + store 5 ms + parse, respond and emit 1.1 ms $\approx$ **7 ms** against
20 ms. *Decision:* there is room for one miss and nothing synchronous after it: no counter write, no
classifier call, no cross-region read in the normal path.

![The redirect's latency budget at the server (initial target).](diagrams/video-budget.pdf){width=85%}
:::

## The full table

| Number | Arithmetic | Label | Decision |
|---|---|---|---|
| Creates | 10^8^ ÷ (30 × 86,400 s) $\approx$ 40/s; peak ×10 = 400/s | derived | Throughput is easy; uniqueness is the problem |
| Redirects | 10^10^ ÷ 2.6 × 10^6^ s $\approx$ 4,000/s | derived | Optimise the read |
| Viral peak | 40,000/s on one code | given | A hot key, not a big fleet |
| Links in ten years | 1.2 × 10^10^ | derived | Sizes the code space |
| Storage | 1.2 × 10^10^ × ~500 B $\approx$ 6 TB; ×3 = 18 TB | illustrative | Sharded store, not the hard part |
| Hot set | 2 % of links take 90 % of clicks: 2 × 10^8^ × 500 B $\approx$ 100 GB | illustrative, to measure | A few cache nodes |
| Store reads | 4,000/s × 1 % $\approx$ 40/s; cold: 4,000/s | derived | Protect the store from cold caches |
| Range leases | 400/s ÷ 1,000 = 0.4/s | derived | A small consensus store is enough |
| Click events | 4,000/s × 200 B $\approx$ 0.8 MB/s $\approx$ 70 GB a day | illustrative | A log and an aggregator |
| Takedown | status + delete (s) + in-process 60 s + edge 60 s + purge | initial target | About 2 min worst case against 5 |

::: why
**The record size.** About 500 bytes is the URL (median around 100 bytes, long tails much longer, so
an average near 200), the code, the owner, two timestamps, a status, and index and storage overhead. It
is illustrative; what matters is that six terabytes is small for a sharded store, so storage does not
shape the design. If an interviewer pushes on it, say what you would measure.
:::

::: warn
**A classic arithmetic slip.** Multiplying a ten-year record count by ten years again. Write the unit at
every step (links per month, months per year, years) and the error is visible.
:::

# Stage 3: API and data

## The API

| Call | Serves | Touches | Notes |
|---|---|---|---|
| `POST /v1/links {url, alias?, expiresAt?}` + `Idempotency-Key` -> `201 {code, shortUrl}` | FR1 | writes link | `409` alias taken; aliases are 8 to 30 characters; `422` known-bad URL; a rate limit per API key |
| `GET /{code}` -> `302` / `404` / `410` | FR2 | reads link, caches first | `410 Gone` for a withdrawn code |
| `GET /v1/links/{code}/stats` | FR3 | reads daily_count | `from`, `to`, `by=day,country`; returns `asOf` |
| `DELETE /v1/links/{code}`, `POST /v1/takedowns {code, reason}` | FR4 | writes status, takedown | Invalidation event, audit |
| internal `LeaseRange()` -> `{start, end}` | FR1 | writes range_lease | 1,000 IDs |

**The redirect on the wire.**

```
GET /aZ3kQ9x HTTP/1.1
Host: sho.rt

HTTP/1.1 302 Found
Location: https://example.com/spring-sale?utm=news
Cache-Control: private, max-age=0
CDN-Cache-Control: max-age=60
```

::: why
**Why these headers.** `private, max-age=0` tells the browser not to reuse the answer: it asks us every
time, so we count the click and can withdraw the link. `CDN-Cache-Control: max-age=60` lets the edge keep
it for a minute, which makes a viral link cheap. Both lifetimes are entries in the takedown budget, so
they are design decisions, not defaults.
:::

::: why
**What the first draft glosses over: an alias can steal a future code.** If a customer may choose any
seven-character alias, they can choose `aZ3kQ9x` today, and in a year the counter will permute to exactly
that code. The generated insert would then conflict, and "generated codes never conflict" would be false.
Give aliases their own namespace: **eight characters or more** (or a character the encoder never emits).
Then generated codes and aliases can never meet, and the constraint only ever arbitrates between two
customers.
:::

::: why
**What the first draft glosses over: an idempotent create needs the key stored with the result.** Ranges
make a retry dangerous in a new way: a bulk client times out after we inserted `aZ3kQ9x` and retries; the
server takes the *next* ID and creates a second link for the same request. Store `(api_key,
idempotency_key) -> code` in the same transaction as the link row (a small table with a retention of a day
or so). A retry finds the row and returns the same code. A retry with the same key and a *different* URL
is a client bug: answer `422`, never silently return the old code.
:::

## The data model

![Conceptual model: owners create links; clicks are weak entities of a link and roll up into daily counts.](diagrams/video-erd-chen.pdf){width=88%}

| Table | Key | Columns | Note |
|---|---|---|---|
| `link` | `code` PK, sharded by code | long_url, owner_id, created_at, expires_at, status | 12 B rows in ten years; the only hot key |
| `link_by_owner` | `(owner_id, created_at)` | code | The dashboard; written on create; never on the hot path |
| `idempotency` | `(api_key, idempotency_key)` | code, request_hash, created_at | One day retention |
| `range_lease` | `server_id` | start, end, leased_at | Consensus store; 0.4 leases a second |
| `daily_count` | `(code, day, country)` | n | Written by the aggregator |
| redirect server memory | code | url, status; 30 to 60 s lifetime; in-flight map | Single flight |

::: warn
**A hash of the URL is not a key.** The same URL shortened by two customers is two links with two owners,
two expiries and two sets of statistics. A design keyed by `hash(url)` either merges them (wrong) or adds
a disambiguator (and is now a random-code design with extra steps).
:::

::: warn
**No counter on the link row.** A click never writes to `link`. At 40,000 clicks a second on one viral
code, a `clicks = clicks + 1` column makes that row the hottest lock in the system, and puts a write
inside every redirect.
:::

# Stage 4: High-level design

Build it in three versions, each answering the objection to the one before. Draw on one baseline so the
interviewer sees the same boxes grow.

## Version 1: the simplest thing that works

One service, one relational table `code -> url`. Create draws a random seven-character code and inserts
it, retrying on a conflict. Redirect reads the table and answers `302`.

![V1: one service, one table.](diagrams/video-base-v1.pdf){width=95%}

**The objection.** 4,000 reads a second on one table and a 40,000 peak on one row; analytics would be an
update per click; creating and redirecting share one process and one failure mode.

## Version 2: split the paths, cache the read

The two paths have different loads (100 : 1) and different tolerances (a redirect must not fail; a create
can wait a few seconds), so they become two services. Redirect servers are stateless, many copies, with a
shared cache in front of a sharded link store, cache-aside. The create service leases ID ranges from an
allocator and inserts under a unique constraint.

![V2: split paths; a shared cache; counter ranges.](diagrams/video-base-v2.pdf){width=95%}

**The objection.** One viral code is one hot cache key. Clicks have nowhere to go. A takedown sits behind
every cache.

## Version 3: protect the redirect, make every copy withdrawable

An edge in front caches `302`s for 60 seconds. Each redirect server keeps an in-process cache with single
flight. Clicks go *after* the answer into a click log, an aggregator and a stats store. A takedown service
writes the status and publishes on an invalidation channel that reaches the edge, every redirect server and
the shared cache. Create calls a safety check on the URL first.

![V3: protect the redirect; make every copy withdrawable.](diagrams/video-base-v3.pdf){width=100%}

## The numbered flows, one per functional requirement

![FR1 create: (1) post with an idempotency key, (2) safety check, (3) next ID from the leased range, (4) insert under the unique constraint.](diagrams/video-flow-fr1.pdf){width=95%}

![Create as a sequence.](diagrams/video-seq-create.pdf){width=88%}

![FR2 redirect: (1) edge, (2) redirect server and its memory, (3) shared cache, (4) store on a miss, (5–6) fill and return, (7–8) the 302 back through the edge.](diagrams/video-flow-fr2.pdf){width=95%}

![The redirect as a sequence: the click is recorded after the answer.](diagrams/video-seq-redirect.pdf){width=92%}

![FR3 count: after the answer, a local buffer, a log by code, an aggregator, a stats store.](diagrams/video-flow-fr3.pdf){width=95%}

![FR4 withdraw: status, publish, the shared cache deleted, every server drops it, the edge purged.](diagrams/video-flow-fr4.pdf){width=95%}

**Code for the redirect path**, the part interviewers ask to see:

```python
def redirect(code):
    hit = local.get(code)                       # in-process, 30-60 s
    if hit is None:
        hit = single_flight(code, lambda: shared_cache.get(code) or store_fill(code))
        local.put(code, hit, ttl=30)
    if hit is NOT_FOUND:            return 404
    if hit.status != "live" or hit.expired(now()):  return 410
    respond_302(hit.url)                         # the answer goes out first
    clicks.append(code, now(), country(), event_id())   # then, never before
```

![The C4 context view.](diagrams/video-c4-context.pdf){width=85%}

![The C4 container view: the redirect path is four boxes in a row; everything else is above or below it.](diagrams/video-c4-containers.pdf){width=95%}

# Stage 5: Why these choices

## A sharded key-value or relational store, keyed by code

*Why here:* every redirect is a single-key lookup by code, and every create is a single-row insert with a
uniqueness check. Both are what any sharded store does best. *Internals to explain:* sharding by code
spreads writes evenly because codes are permuted; the unique constraint is local to the shard that owns the
code, so it needs no cross-shard coordination. *Alternative:* one relational primary. Writes would fit
(400 a second) but reads, storage growth and a single failure domain argue against it at ten years.

## An in-memory shared cache, cache-aside

*Why here:* the hot set (about 100 GB, illustrative) fits in memory. Cache-aside rather than
read-through-in-the-store because the cache must keep answering when the store is slow. *Internals:* a
lifetime per entry, eviction by least-recent use, sharding by key, which is exactly why a single viral key
lands on one shard. *Alternative:* no shared cache, only in-process caches: works, but a restart of the
fleet sends every miss to the store.

## A small consensus-backed store for the allocator

*Why here:* 0.4 leases a second needs no throughput, only correctness: two servers must never receive the
same range. A compare-and-set on one key in a replicated, consensus-backed store gives that and survives
the loss of one replica. *Alternative:* a counter row in the link store, which couples creates to the
busiest store and has no natural lease semantics.

## A local buffer, a partitioned log, an aggregator

*Why here:* the click path must never delay the redirect and must absorb 40,000 events a second for one
code. A log partitioned by code spreads codes across partitions and keeps one code's events in order.
*Alternative:* a counter per link (the hot row) or a synchronous write to an analytics store (latency on the
critical path).

## A bought edge with a purge API

*Why here:* points of presence in dozens of cities are not our business. What we need from it: honouring
`CDN-Cache-Control`, a purge API that completes in seconds, and logs. *Alternative:* building our own edge:
no.

# Stage 6: Deep dives

The interviewer picks; you should be able to run any of the eight. Each is written in the same shape:
the question, the risk, the naive answer, a failure case with numbers, the mechanism, why it works, the
second-level push, what the first draft glosses over, weak answers, and the words to say.

![The challenge map: eight attack points on the same baseline.](diagrams/video-map.pdf){width=95%}

## 6.1 Two servers, one code (correctness)

**The question.** "Two create servers run at the same time. How do they never hand out the same code,
without asking each other every time?"

**The risk.** Two long URLs get one code: a printed flyer opens someone else's page (S1).

**The naive answer.** "Generate a random code, check whether it exists, and insert it if it doesn't."

**The failure case.**

```
10:00:00.001  server A: SELECT code = 'sale' -> none
10:00:00.002  server B: SELECT code = 'sale' -> none
10:00:00.004  server A: INSERT sale -> shop-a.example
10:00:00.006  server B: INSERT sale -> shop-b.example   (overwrites A without a constraint)
next day      A's printed flyers open B's page
```

**The mechanism.** Generated codes come from **disjoint leased ranges**: each server leases 1,000 IDs from
the allocator in one compare-and-set and hands them out from memory. Every insert carries
`UNIQUE(code)`, so the store, not the application, arbitrates aliases: one `201`, one `409`. Aliases live
in their own namespace (eight characters or more).

![The fix on the baseline: disjoint ranges and the constraint as the authority.](diagrams/video-ch1-fix.pdf){width=95%}

![Ranges: coordination once per thousand links.](diagrams/video-ranges.pdf){width=90%}

```python
def lease(store, size=1000):
    while True:
        cur = store.get("next_id")
        if store.compare_and_set("next_id", cur, cur + size):
            return range(cur, cur + size)      # ours alone
        # another server won the race: read again
```

**Why it works.** Compare-and-set makes leases disjoint; inside a lease no coordination is needed. The
shard that owns a code sees every insert for it, so the constraint is a complete authority.

**The second-level push.** "The allocator is down. Or a server crashes holding half a range." *Runway:*
lease the next block at half-used, so each server holds 500 to 1,500 IDs: at the 400 a second peak across
ten servers that is 12 to 37 seconds, at the 40 a second average two to six minutes. *A crashed server's*
unused IDs are skipped: a gap, never a collision. *Honest limit:* an allocator down for longer stops
creates; redirects never depended on it.

::: why
**What the first draft glosses over: a lease that was granted but never received.** The compare-and-set
succeeds, the response is lost, the server retries and gets the *next* range. The first range is never
used: a gap of 1,000 IDs. Harmless at 290 times headroom, and the reason not to make ranges huge: a
range of ten million would waste meaningful space on every lost response and crash.
:::

::: warn
**Weak answers.** "Use a distributed lock" (coordination per create). "Use a UUID" (36 characters is not
a short link). "Check, then insert, in a transaction" (still a race without a unique constraint, unless the
transaction is serialisable, which is the constraint with extra cost).
:::

::: say
"Each create server leases a block of a thousand IDs, so coordination happens once per thousand links, not
once per link. The unique constraint on the code is the final authority, so an alias race ends in one
success and one conflict. If the allocator goes down, servers have their leased runway, and redirects never
depended on it."
:::

## 6.2 Codes in order (correctness and security)

**The question.** "Your codes come from a counter. What can someone learn from that?"

**The risk.** Codes reveal creation volume, and anyone can walk them to read links their owners thought
were unfindable.

**The naive answer.** "Base-62 makes them look random."

**The failure case.** At 09:00 a user gets `0000g8Q`; at 09:10 `0000gBA`. The difference is 2,000 IDs: our
creation rate in ten minutes. A scraper then requests the next codes in order and reads every link created
that morning.

**The mechanism.** A **keyed permutation** between the counter and the encoder: a four-round Feistel
network over 42 bits with a secret key, plus *cycle walking* (re-apply until the result is below 62^7^).
It is a bijection, so distinct IDs give distinct codes; neighbouring IDs give unrelated codes. Add a rate
limit on `404`s per client so guessing is slow.

![A keyed permutation: unique in, unique out, neighbours unrelated.](diagrams/video-feistel.pdf){width=90%}

```python
N = 62 ** 7
def permute(i, key):
    while True:
        l, r = i >> 21, i & (2**21 - 1)        # 42 bits, two halves
        for k in range(4):
            l, r = r, l ^ (prf(key, k, r) & (2**21 - 1))
        i = (l << 21) | r
        if i < N:
            return base62(i, width=7)           # cycle walk
```

**Why it works.** Uniqueness comes from the counter; unpredictability from the key. Each Feistel round is
invertible whatever the round function, so the whole is a bijection on 42 bits, and cycle walking keeps it
a bijection on the 62^7^ code space (Appendix B).

**The second-level push.** "The key leaks. Or a customer says private links must not be guessable at
all." *A leaked key:* new codes use a new key and a fresh slice of the ID space; old codes stay valid
because they are stored, never recomputed. *Private content:* seven characters are 42 bits; an attacker
with many addresses can still sample. Links to private files need authentication or a long random token.

::: why
**What the first draft glosses over: cycle walking cannot loop forever.** The values at or above 62^7^
are about 20 % of the 42-bit space (2^42^ $\approx$ 4.4 × 10^12^ against 3.5 × 10^12^), so each walk step lands
in range with probability about 0.8; the expected number of steps is about 1.25, and the walk always
terminates because a permutation's cycle through an out-of-range value must return to an in-range one.
:::

::: say
"A counter gives uniqueness, but base-62 of a counter is still a counter: it leaks our volume and lets
anyone walk the links. I pass the ID through a keyed permutation, which keeps it unique and makes
neighbours unrelated. And I'm clear that a short code is not a secret: private links need authentication."
:::

## 6.3 One link at 40,000 clicks a second (overload)

**The question.** "A link goes viral: forty thousand clicks a second, all on one code. What happens?"

**The risk.** One key concentrates load that a fleet would otherwise spread: one cache shard's queue, and
on a restart, one row of the store (L2).

**The naive answer.** "It's cached, so it's fine."

**The failure case.**

```
14:02  code k7Pq2mZ goes from 3 clicks/s to 40,000/s
14:02  its cache shard: p99 0.8 ms -> 9 ms; every other code on that shard slows too
14:05  a deploy restarts the shard: 200 ms of misses
14:05  8,000 identical SELECTs on one row in those 200 ms
```

**The mechanism.** An **in-process cache on every redirect server** (a few hundred thousand entries, 30 to
60 seconds): with 40 servers the viral code is 1,000 requests a second from each server's own memory.
**Single flight:** concurrent misses for one code wait on one lookup. **Negative caching** for unknown
codes, so scanners' `404`s don't reach the store.

![A thousand requests, one lookup.](diagrams/video-seq-ch3-flight.pdf){width=88%}

```python
inflight = {}                                   # code -> future
def resolve(code):
    hit = local.get(code)
    if hit:
        return hit
    leader = code not in inflight
    fut = inflight.setdefault(code, Future())
    if leader:
        fut.set(shared_cache.get(code) or store.get(code))
        local.put(code, fut.value, ttl=30)
        inflight.pop(code)
    return fut.wait()
```

**Why it works.** The store's load is bounded by servers × hot codes per lifetime, not by clicks.

**The second-level push.** "The in-process lifetime makes a takedown slower. And a whole region's servers
restart together." The lifetime is a line in the takedown budget (6.5), and invalidation drops entries
early. Restarts roll; a starting server warms its cache from the last hour's top codes before taking
traffic.

::: why
**What the first draft glosses over: single flight is per process, not per fleet.** With 40 servers, a cold
viral code costs up to 40 store reads per lifetime, not one: still nothing. After a whole-fleet restart, the
bound is servers × *distinct codes requested in the next lifetime*, which is the few thousand codes being
clicked right now, not the 2 × 10^8^ codes in the hot set. Do this arithmetic aloud if pushed; it is why a
rolling restart with warm-up is enough and a fleet-wide cache preload is not needed.
:::

::: say
"A viral link is a hot key, not a load problem. I answer it from memory on every redirect server and
coalesce misses, so each server sends one query, whatever the click rate. The cost is a short staleness
window, which I count in the takedown budget."
:::

## 6.4 301 or 302? (trade-off)

**The question.** "Should the redirect be a 301 or a 302?"

**The risk.** An answer we cannot see or take back.

**The naive answer.** "301, it's permanent and it saves servers."

**The failure case.** Monday a user clicks; we answer `301`; the browser caches it. Tuesday the same user
clicks again: the browser answers, the click is not counted. At 15:00 the link is blocked for phishing; at
15:20 that user's browser still goes straight to the phishing page.

**The mechanism.** **302 by default**, browser caching off, the edge allowed 60 seconds, purgeable. **301
only as an owner's opt-in** for permanent, uncounted links, after the safety check.

| Layer | Answers in | Sees the click? | Can we take it back? |
|---|---|---|---|
| Browser, 301 | 0 ms | never again | no |
| Edge, 302 cached 60 s | ~5 ms near the user | from edge logs, minutes late | yes: purge, or 60 s |
| Redirect service + caches | ~1 ms at the server | every click, exact | yes: invalidation, or 60 s |
| Link store | ~5 ms, misses only | — | it is the truth |

**Why it works.** Control (counting and S2) stays at layers we can reach; the edge gives most of 301's
saving at a bounded cost in freshness.

**The second-level push.** "The edge bill is too high, or edge-log counts arrive late." Compare the
per-request edge cost with what it saves, and enable edge caching per link by click rate: only hot links
need it. Edge-log counts carry their lag (`asOf`); billed clicks must come from our servers or a signed
edge function.

::: why
**What the first draft glosses over: search engines and `302`.** Some site owners prefer `301` so search
engines attribute the target's ranking correctly. Modern crawlers generally follow temporary redirects
too, but if the business sells to marketers, ask: this is a product conversation, and the opt-in `301`
exists for it.
:::

::: say
"301 against 302 is a product decision, not an optimisation. A 301 is answered by the browser forever, so
we lose the click and the ability to take a link down. I default to 302, let the edge cache it for a
minute, and offer 301 only to owners who want a permanent, uncounted link."
:::

## 6.5 Dead everywhere in five minutes (correctness and operations)

**The question.** "Legal reports a phishing link. It must stop working everywhere within five minutes.
Show me."

**The risk.** S2: a withdrawn code answered by any layer after the bound.

**The naive answer.** "Delete the row."

**The failure case.**

```
15:00:00  status = blocked in the store
15:00:00  still answering: shared cache (lifetime 1 h), 40 servers' memory (60 s), edge (60 s)
15:00:00  and browsers that got a 301 last week: forever
15:20:00  a victim still lands on the phishing page, from the shared cache
```

**The mechanism.** Write `blocked`. Delete the shared-cache key **directly, retried until confirmed** (it
has the longest lifetime, so it must not depend on a lost message). Publish on the invalidation channel:
every redirect server drops the code, the edge is purged. The next request reads `blocked` and answers
`410` with a warning page. The safety check on create and a rescan when the classifier's list updates
prevent most takedowns from being needed.

![The worst case if the invalidation event is lost: about two minutes against five.](diagrams/video-takedown-budget.pdf){width=85%}

![The takedown as a sequence.](diagrams/video-seq-takedown.pdf){width=90%}

**Why it works.** S2 holds by arithmetic: the worst case is the sum of lifetimes along the path, and each
was chosen to fit.

**The second-level push.** "The event is lost, or the link was a 301." The lifetimes are the backstop by
design; an hourly synthetic takedown measures the real time (6.8). A `301` cannot be recalled: that is why
it is opt-in and checked before issue.

::: why
**What the first draft glosses over: a cache fill racing the takedown.** A redirect server misses at
15:00:00.000, reads the store (still `live`), and is slow; the takedown writes `blocked` and deletes the
cache at 15:00:00.010; the slow server then fills the shared cache with `live` at 15:00:00.050, for an
hour. Two defences: fill with a short lifetime, and use a version (or the status write's timestamp) so a
fill older than the last takedown is refused (a conditional "set if not newer" in the cache). Or delete the
key a second time a few seconds after the first. Mention one; it shows you ran the race.
:::

::: say
"Every copy of the answer is a liability. A takedown writes the status, deletes the shared-cache key
directly, sends an invalidation and purges the edge, and the lifetime at every layer is chosen so that even
with a lost message the worst case is inside five minutes. A 301 can't be recalled, which is one more
reason it isn't the default."
:::

## 6.6 Counting without slowing the redirect (overload; correctness when billed)

**The question.** "How do you count clicks per link per country without touching the redirect latency?"

**The naive answer.** "`UPDATE links SET clicks = clicks + 1` on every redirect."

**The failure case.** 40,000 updates a second on one row; the row lock serialises them; each redirect waits
for its write; p99 goes from 5 ms to 900 ms. The cache had solved the read; the counter put the hot key back
on the critical path.

**The mechanism.** After the `302`, append an event to a local buffer; flush a batch every second or
1,000 events to a log partitioned by code; an aggregator counts per code per minute, then per day per
country. Buffer full: drop, and count the drops.

![The click path on the baseline.](diagrams/video-ch6-fix.pdf){width=95%}

| Today (not billed) | If clicks are billed |
|---|---|
| At-most-once from the server: a crash loses the unflushed second | At-least-once: a durable buffer on disk, resent until acknowledged |
| No event ID; drops counted and shown | An event ID at the redirect; de-duplicated in the aggregator |
| Bots counted | Bots filtered before billing |
| Minutes late | Same lag; exact once settled; stated in the billing terms |

![Billed clicks: event IDs, a durable buffer, de-duplication.](diagrams/video-seq-ch6-billed.pdf){width=88%}

::: why
**Precision about "exactly once".** Delivery is at least once; the *effect* is once per event ID because
the aggregator de-duplicates. Say it that way. The de-duplication window must cover the longest resend
delay (a server down for an hour resends an hour-old buffer), so keep seen event IDs per code for at least
that long, or partition by code and keep a per-partition set with a time bound.
:::

::: say
"The click is recorded after the answer, never before it. Events go to a local buffer and a log, and an
aggregator counts per minute. Today that's lossy by choice and we measure the loss. If clicks are billed, I
add event IDs, a durable buffer and de-duplication, and the redirect still doesn't wait."
:::

## 6.7 A region goes dark (failure recovery)

**The question.** "The region holding your link store's primary goes down. What still works?"

**The naive answer.** "We fail over the database."

**The failure case.** At 03:10 the primary region is lost. Redirects elsewhere: 98 % from caches, 2 % miss
to a store now read-only. Creates fail: the primary and the allocator's leader are gone.

**The mechanism.** **Redirects are regional:** each region has a replica of the link store and its own
caches; a redirect never crosses regions. **Creates are regional:** each region leases from its own slice
of the ID space, so it can create alone; the store replicates asynchronously.

![Each region answers its own redirects and creates in its own slice of the ID space.](diagrams/video-regions.pdf){width=92%}

**The second-level push.** "A link created in Asia is clicked in Europe 200 ms later." The code's ID slice
says which region created it (decode the permutation, read the top bits); on a local miss, one
cross-region lookup, then cache it. One round trip slower, no error.

![One cross-region lookup, not an error.](diagrams/video-seq-ch7-region.pdf){width=85%}

::: why
**What the first draft glosses over: negative caching meets replication lag.** Challenge 3 caches `404`s
to protect the store from scanners. A brand-new code clicked in another region before replication would
be cached as *not found* for the negative lifetime. Either skip the negative cache for codes whose ID
slice belongs to another region (check that region once), or keep the negative lifetime very short
(seconds). The two fixes interact; saying so is the Staff signal.
:::

::: say
"Redirects never leave their region: replicas and caches answer them even with the primary gone. Creates
are regional because each region owns a slice of the ID space. The one gap is a brand-new link clicked
elsewhere before it replicates, and that costs one cross-region lookup, not an error."
:::

## 6.8 How would you know it is broken? (observability)

**The question.** "Your dashboards are green. How do you know redirects are actually working?"

**The failure case.** At 01:55 a config change sets the shared cache's lifetime to zero. No errors; p50
unchanged; p99 6 ms -> 18 ms, still under target; store reads 40/s -> 4,000/s. At 09:00 the peak arrives,
the store saturates, and the first page fires: seven hours late.

**The mechanism.** **Probes on the path:** in every region, every minute, create a link and follow it through
the edge: redirect latency, success, create-to-first-redirect time. **A synthetic takedown** every hour:
block a test link and poll every layer until `410`. **Symptom pairs:**

| When you see | Together with | It means |
|---|---|---|
| Cache hit rate down | store reads up, traffic flat | a cold or misconfigured cache, not more users |
| 404 rate up | creates flat | scanning: someone is walking codes |
| p99 up | hit rate flat | something synchronous crept onto the redirect path |
| Click drops up | buffers full on many servers | the log or aggregator is slow, not the redirect |
| Takedown time up | invalidation lag up | the channel is behind; the lifetimes are carrying us |

**The second-level push.** "The probes pass, but one country's DNS sends users to the wrong region."
Real-user monitoring from edge logs per country (latency and answering region), compared with the probes;
alert on divergence.

::: say
"I measure the path, not the boxes: probes that create a link and follow it in every region, and a test
takedown every hour, timed until every layer answers 410. Then pairs of metrics give me causes: hit rate
down with store reads up means a cold cache, not more traffic."
:::

## 6.9 How the whole system degrades, in priority order

1. **Redirects for known links** survive the loss of the store (caches), the allocator (irrelevant), the
   click pipeline (drops counted) and the classifier (irrelevant). They need only memory and, for misses,
   a regional replica.
2. **Takedowns** survive a lost event (lifetimes) and a slow purge (lifetime at the edge).
3. **Counts** survive by lagging; they lose at most a flush interval per crashed server.
4. **Creates** stop when the region's allocator and the store's primary are both unavailable beyond the
   runway. This is the right order: the product keeps working.

# Stage 7: Requirements that arrive mid-round

**"Clicks will be billed."** The click path becomes at-least-once with event IDs, a durable buffer and
de-duplication (6.6); bot filtering moves before billing; the stats API gains a "settled" state. The
redirect path does not change. *Cost:* disk on every redirect server and a de-duplication store.

**"Owners can edit a link's target."** For every cache, an edit is a takedown of the old answer plus a
create of the new one: status and URL updated in the store, the shared cache deleted directly,
invalidation sent, edge purged. Links that were issued as `301` cannot be edited for users who already
followed them: say so, and disallow edits on `301` links. *Cost:* edits become as heavy as takedowns,
so rate-limit them per owner.

**"QR codes for every link."** A rendering of the short URL, generated on demand and cached; it adds no
state. Say it in one sentence and move on.

# Stage 8: Failures and reliability

| Failure | Blast radius | Response |
|---|---|---|
| One redirect server dies | its share of traffic for seconds | stateless; the balancer removes it |
| Shared cache shard restarts | misses for its keys; store spike | single flight; in-process caches carry hot keys |
| Link store shard primary lost | writes for its codes; reads continue from replicas | fail-over; creates retry with the idempotency key |
| Allocator unavailable | creates after runway expires | runway, a replicated allocator; redirects unaffected |
| Click log slow | counts lag; drops after the buffer fills | drops counted; redirects unaffected |
| Invalidation channel down | takedowns rely on lifetimes | about 2 minutes worst case; alert on channel lag |
| Edge outage | traffic shifts to our servers | capacity for the edge's share for an hour; purge irrelevant |
| A region lost | that region's users routed elsewhere | regional replicas; ID slices |

**One incident, walked through.** The 01:55 configuration change in 6.8: detected at 02:01 by the pair
"hit rate down, store reads up, traffic flat"; the on-call engineer rolls back the cache config at 02:10;
store reads return to 40 a second. Postmortem action: the cache lifetime becomes a validated configuration
with a lower bound.

# Stage 9: SLOs, observability, cost

**SLIs, measured from outside:** redirect success and latency from probes in every region and from real
users at the edge; create-to-first-redirect time; takedown time from the hourly synthetic takedown; count
freshness (`asOf` lag). **SLOs (initial targets):** redirect 99.99 % under 20 ms at the server; takedown
under 5 minutes for 99 % of takedowns; counts under 10 minutes behind for 99 % of minutes.

**The dashboard:** one row per region: redirect rate, success, p99; hit rates of each cache layer; store
reads; 404 rate; click drops; invalidation lag; last synthetic takedown time.

**Cost (illustrative):** a handful of redirect servers at 4,000 a second; about 100 GB of cache memory;
18 TB of storage; a small log. **The edge is billed per request** and at 10 billion a month is the largest
line, which is why edge caching is enabled per link by click rate and its default lifetime is a business
decision. *Levers:* edge caching only for hot links; a longer in-process lifetime (traded against the
takedown budget); cold storage for links not clicked in a year.

# Stage 10: The EM layer (auxiliary at Staff)

**Phasing.** V1 with two engineers in six weeks; V2 with two more in two months; V3 with a team of five or
six over two quarters, with 24/7 on-call.

**Two teams, one quarter.** *Links and redirect:* create, codes, store, caches, edge; owns the redirect SLO
and the takedown time. *Clicks and trust:* event pipeline, stats, the takedown service and its channel, the
classifier. The contract between them: the click event schema and the invalidation channel.

**Buy, build, or don't.** Buy the store, the cache, the log and the edge. Build code generation, the
redirect and the takedown path. And if shortening is not the business, the honest answer is an
off-the-shelf shortener.

**Top risks.** The code format is a one-way door (codes are printed on paper). Takedown time untested until
a real incident: the hourly synthetic takedown exists for this. Analytics drifting into billing without
the exactness work.

# Stage 11: The close

> **What:** a create path with leased ID ranges, a keyed permutation and a unique constraint; a redirect
> path that answers from memory, behind a short-lived edge; and side paths for counting and takedowns.
> **Trade-off:** I chose a 302 and short lifetimes over the cheapest possible redirect, so we can count and
> withdraw. **Risk:** the takedown time is only as good as its least-tested layer, so I measure it every
> hour. **Next:** per-link edge caching by click rate, and the exactness work if clicks are billed.

# Stage 12: Self-check after a simulator run

| | Weak | Strong | Exceptional |
|---|---|---|---|
| Codes | Hash and truncate; six characters | Ranges or random with retry; seven from arithmetic; the constraint decides | Keyed permutation; aliases in their own namespace; the idempotency table |
| Redirect | "Add a cache" | Cache-aside, hot set sized | In-process cache and single flight; negative caching and its interaction with replication |
| 301/302 | 301 for speed | 302 with a reason | Layer-by-layer cost and control; opt-in 301 |
| Side paths | Counter per click | Async log | Lossy by choice, measured; the billed variant |
| Takedown | "Delete the row" | Invalidate the caches | Budget as a sum of lifetimes; the fill race |
| Operations | CPU and errors | Latency and hit rate | Probes, synthetic takedowns, symptom pairs |

**Common traps:** check-then-insert; a counter in disguise; `301` by default; a write per click; no number
on the takedown time; confusing a short code with a secret.

\newpage

# Part III: The internals

## Appendix A: Counter ranges, in plain words

A counter that every create must touch is a bottleneck and a single point of failure. A range lease moves
the coordination off the critical path: a server asks the allocator for the next block of IDs once, using
a compare-and-set (write `next = cur + 1000` only if `next` is still `cur`), and then hands out IDs from
memory. Two leases can never overlap because only one compare-and-set from `cur` can succeed. The cost is
gaps: unused IDs when a server dies, and whole ranges when a granted lease's response is lost. Choose the
range size so that coordination is rare (seconds to minutes between leases) and gaps are cheap (a tiny
fraction of headroom). The allocator itself should be replicated with a consensus protocol, because its
correctness matters and its throughput does not.

## Appendix B: Feistel networks and cycle walking

A Feistel network splits a number into two halves `(L, R)` and runs rounds of `(L, R) -> (R, L xor F(k, R))`
where `F` is any keyed function. Each round is invertible (given the output you recover the input by
running the round backwards), so the whole network is a permutation of the input space, whatever `F` is.
Four rounds with a strong `F` (for example, a keyed hash truncated to 21 bits) make outputs look unrelated
to inputs. The network works on 42 bits (2^42^ values), but the code space is 62^7^ values, smaller. Cycle
walking fixes the mismatch: apply the permutation; if the result is outside the code space, apply it again
to that result, until it lands inside. Because a permutation's cycles return to their start, the walk
always ends, and the map restricted to the code space is still a permutation. This is the same idea as
format-preserving encryption, at a smaller scale and with a weaker goal: unpredictability, not secrecy.

## Appendix C: Single flight and negative caching

Single flight keeps a map from key to an in-progress lookup. The first caller for a key starts the lookup;
later callers for the same key wait for its result instead of starting their own. It turns a burst of N
concurrent misses into one backend call per server. Two details matter: remove the entry when the lookup
finishes, including on error (or one failure blocks the key); and give waiters a timeout. Negative caching
stores "not found" for a short time so repeated requests for unknown codes (scanners) do not reach the
store; keep its lifetime short, because a not-yet-replicated new code would otherwise be hidden (6.7).

## Appendix D: Cache lifetimes as a budget

Every cached copy of an answer can be wrong for at most its lifetime after the truth changes, unless it is
actively invalidated. Active invalidation is fast but can be lost; lifetimes are slow but certain. So
design both: invalidate for speed, and choose lifetimes so that their sum along the worst path meets the
correctness target even if every invalidation is lost. In this design: shared cache (deleted directly and
retried), in-process (60 s), edge (60 s), purge (seconds): about two minutes against five. Write the sum
down; it is the proof.

## Appendix E: Click pipelines, from lossy to billed

The lossy pipeline: a bounded in-memory buffer per server, flushed every second to a partitioned log,
dropped when full, with the drops counted. The billed pipeline adds an event ID minted at the redirect, a
buffer on local disk, resend until acknowledged, de-duplication by event ID in the aggregator over a window
at least as long as the longest resend delay, and bot filtering before billing. The redirect never waits for
either. Counts are eventually consistent and say how fresh they are.

## Appendix F: Testing it

Unit: the permutation is a bijection on a small space (exhaustively, with a 20-bit version); cycle walking
terminates. Integration: two create servers and one alias, concurrently, a thousand times: exactly one
`201`. Load: one code at 40,000 a second with a shard restart mid-test; store reads stay bounded by servers
× codes. Chaos: drop all invalidation events and run a takedown: measured time under five minutes. Probes
in production run the same create-then-follow path every minute.

\newpage

# One-page cheat card

**Thesis.** A read path with a write path attached: unique codes without a lock, unguessable without a
lookup, a redirect that is one memory read, nothing in front of it.

**Order of the round.** Clarify (volume, lifetime, aliases, analytics, abuse, callers) · numbers (7
characters, 4,000/s, 40/s at the store, 7 of 20 ms) · API (create with idempotency, redirect headers,
stats, takedown) · V1, V2, V3 · eight challenges · cost.

**The numbers.** 62^7^ $\approx$ 3.5 × 10^12^ against 1.2 × 10^10^ links (290×) · 4,000 redirects/s, 40,000 on one code
· 40 store reads/s · 0.4 leases/s · about 2 minutes worst-case takedown against 5.

**Eight fixes.** (1) leased ranges, unique constraint, aliases of 8+ characters. (2) keyed permutation.
(3) in-process cache, single flight. (4) 302 default, edge 60 s, 301 opt-in. (5) status, direct delete,
invalidate, purge, lifetimes that sum. (6) click after the answer; buffer, log, aggregate. (7) regional
replicas, ID slices. (8) probes, synthetic takedowns, symptom pairs.

**Properties.** S1 no two URLs share a code · S2 no withdrawn code answered after the bound · L1 a create
never waits for another · L2 a redirect always answers in time · L3 every click eventually counted, with a
stated loss.

**Say first.** "The redirect is the product." "A short code is not a secret." "A 301 cannot be recalled."
"The worst case is a sum of lifetimes."

**Close.** The redirect is one memory read. Codes are unique by blocks and a constraint, unguessable by a
key. Everything else lives beside the redirect, with a number on how late it may be.
