# Archetype B · Social, feed & content

**SD-08 – SD-14.** Slice with `grep -n '^### SD-08' questions/B-social-feed-content.md`, then Read
with `offset`. Do not read this file whole.

**What this archetype tests as a family:** fan-out. Every question here is a variation on *"one write
must reach N readers — do you pay at write time or read time, and what do you do about the
outlier?"* Meta's flagship territory; expect the manner to be fast, product-driven and impatient
with option enumeration (`CLAUDE.md` §7.3).

---

### SD-08 · News feed / home timeline   [T1 · M★ G]

**Read aloud:** *"Design the home feed for a social network with a billion users — the ranked list of
posts a user sees when they open the app."*

**Crux.** **Fan-out on write versus fan-out on read**, and the recognition that neither works alone:
precomputing every follower's timeline breaks on the celebrity with 100M followers, and computing at
read time breaks the latency budget for everyone else. The strong answer is a **hybrid with a stated
threshold.** If they pick one and defends it without acknowledging the outlier, that's a 2–3 ceiling.

**If they ask:**

| Question | Answer |
|---|---|
| Users? | 1B total, 500M daily active |
| Read:write ratio? | Feed reads ~100× post writes |
| Average following count? | ~200. **Max: 100M+ (celebrities)** — offer this only if they ask about the distribution; a candidate who asks about the tail is signalling |
| Feed latency? | p99 under 200 ms |
| Ranked or chronological? | Ranked. Treat ranking quality as a black box — assume a scoring service exists |
| How fresh? | Seconds for people you follow closely; a minute is tolerable generally |
| Feed depth? | First ~50 posts on open, paginated after |
| Post types? | Text + images. Video out of scope |

**Listen for:**
- The write path and read path separated explicitly, with the ratio driving the choice.
- **Fan-out on write** (push): precompute per-user timelines into a fast store on post. Cheap reads,
  expensive writes, unbounded write amplification on celebrities.
- **Fan-out on read** (pull): fetch from each followee at read time and merge. Cheap writes,
  expensive reads, hurts everyone.
- **← The senior insight: the hybrid.** Precompute for normal accounts; for high-follower accounts,
  don't fan out — merge their posts in at read time from a separate hot cache. They should name the
  **threshold** and say how it's chosen and maintained.
- Timeline storage as a **bounded list** (a few hundred entries) of **post IDs, not post bodies** —
  hydrate from a post store/cache on read. Storing bodies per follower is a massive duplication cost
  and is the most common design error here.
- **Multi-layer caching**: timeline cache, post cache, social-graph cache. Cache hit ratio as the
  economics of the whole system.
- Ranking as a separate stage over a candidate set, with a latency budget carved out of the 200 ms.
- Inactive users: **don't fan out to accounts that haven't opened the app in 30 days** — a large,
  cheap win that strong candidates find on their own.
- Pagination that is stable while new posts arrive (cursor, not offset).

**Probe ladder:**
- *Requirements:* "What's out of scope?" · "Is a user allowed to see a post twice, or miss one
  entirely? Which is worse?" (forces an explicit correctness stance)
- *Estimation:* "500M DAU opening the app 5 times a day — what's your feed QPS?" then **"a celebrity
  with 100M followers posts. How many writes is that, and how long does it take?"** — the number
  that should kill pure fan-out-on-write in front of you.
- *Design:* the end-to-end walk of a post appearing in a follower's feed · "What exactly is stored
  in a user's timeline row?"
- *Deep dives:* **"Walk me through the celebrity post."** (the crux) · "Where's the threshold between
  push and pull, and what happens to an account that crosses it?" · "Your timeline cache loses a
  shard. What does the user see and how do you recover?" · "How does a user un-see a post from
  someone they just blocked?" (fan-out systems make deletion hard — good probe for depth) · "The
  ranker takes 80 ms and you have a 200 ms budget. What's your plan when it takes 300?"
- *EM bar:* "What's the cache-miss cost of this design, and which cache would you buy more of
  first?" · "How would you know the feed had silently degraded in quality?" · "Split this across
  three teams — where are the seams?"

**Curveball:** *"We're adding a 'catch up on what you missed' feature — the feed must now be able to
reconstruct a chronological view of the last 48 hours for any user."* Tests whether their precomputed
bounded timeline can answer a query it wasn't designed for, and whether they reach for the source of
truth rather than distorting the cache.

**Weak / Strong / Exceptional.** *Weak* — one query joining posts and follows at read time, ordered
by timestamp, no caching, no celebrity awareness. *Strong* — hybrid fan-out with a named threshold,
ID-only bounded timelines, layered caches, ranking as a separate stage, inactive-user optimisation.
*Exceptional* — quantifies the write amplification to justify the hybrid, prices the cache tier,
handles deletion/blocking correctly, states the freshness SLO, and sequences an MVP that starts pure
pull and adds precomputation where the numbers demand it.

**Traps.** Storing post bodies in every follower's timeline (check the storage number with them if they
do — it is usually a factor of 100 wasted). Treating the ranking model as the interesting part; it
isn't, and going deep there is a rabbit hole to redirect. Claiming strong consistency for the feed —
nobody needs it and it costs everything.


---

### SD-09 · Chat / messaging, 1:1 and groups   [T1 · M★ MS★]

**Read aloud:** *"Design a messaging system — one-to-one and group chats, for a billion users, with
delivery and read receipts and support for clients that go offline."*

**Crux.** **Where a message lives between "sent" and "delivered to every device."** The design is
really a per-recipient durable inbox plus a connection-routing problem, and candidates who start from
the socket rather than from the mailbox tie themselves in knots.

**If they ask:**

| Question | Answer |
|---|---|
| Users / concurrency? | 1B users, 100M concurrently connected |
| Message rate? | 1M messages/sec peak |
| Group size? | Up to 1,000 members |
| Delivery guarantee? | Never lose a message; never show one twice; ordering must be consistent for all participants |
| Receipts? | Sent, delivered, read — all three |
| History? | Full history, retained indefinitely, searchable by the user |
| Multi-device? | Yes — up to 5 devices per user, all must converge |
| E2E encryption? | Out of scope unless they raise it; if they do, say "assume not, but tell me what it would change" |
| Media? | Out of scope — text only |

**Listen for:**
- **Persistent connections** (WebSocket or similar) terminated on a gateway tier, with a **registry
  mapping user/device → gateway node**, and awareness that this registry is hot and changes
  constantly.
- **Store before deliver.** The message is durably written before any ack goes back to the sender.
  A design that pushes to a socket and writes later will lose messages, and they should say so.
- **Per-recipient inbox / message queue** as the model, not "look up whether they're online" — the
  offline case is then the same code path as the online case, which is the elegance to listen for.
- **Ordering:** per-conversation sequence numbers assigned server-side by a single authority for that
  conversation. Client timestamps are unusable. Ask what happens when two people send
  simultaneously.
- **Idempotency**: client-generated message ID so a retry doesn't duplicate.
- **Group fan-out** — write once and fan out to 1,000 inboxes, and the trade-off against a shared
  conversation log that each member reads with a cursor. **The cursor model is the better answer at
  scale and the one to probe toward** (but never name it for them).
- **Multi-device convergence**: a per-device delivery cursor, so each device independently catches up.
- Receipts as their own message flow, and the observation that read receipts in a 1,000-person group
  are 1,000× the traffic of the message itself — a scale trap worth finding.
- Push notification path for disconnected clients as a separate concern (see SD-12).

**Probe ladder:**
- *Requirements:* "Which matters more — never losing a message or never showing a duplicate?" ·
  "What's out of scope?"
- *Estimation:* "100M concurrent connections — how many gateway nodes, and what's the memory per
  connection?" · "1,000-member group, everyone reads: what's the receipt traffic?"
- *Design:* the walk of one message from sender to a recipient who is **offline**, then the same
  message to one who is online on two devices · "What's stored, and where, at each hop?"
- *Deep dives:* **"Two users send a message at the same instant. What order does everyone see, and
  who decided?"** · "A gateway node dies with 500k connections on it. What happens?" (thundering
  reconnect is the answer to fish for — and the mitigation) · "A user has been offline for a month
  and comes back. Walk me through the catch-up." · "Group of 1,000 — you fan out to 1,000 inboxes.
  Defend that, or don't." · "Message sent, phone dies before the ack. What does the sender see and
  what happens next?"
- *EM bar:* "What's your delivery-latency SLO and what's the SLI that measures it end to end?" ·
  "What does 100M idle connections cost you a month?" · "You need to change the message schema.
  How, without breaking a billion clients that update slowly?"

**Curveball:** *"Product wants message editing and deletion for everyone, retroactively."* Tests
whether fanned-out copies were treated as denormalised caches over a source of truth (easy) or as the
source of truth itself (very hard), and whether they can say what it costs.

**Weak / Strong / Exceptional.** *Weak* — deliver over the socket if online, else write to a "pending"
table; client timestamps for ordering; no multi-device story. *Strong* — durable-write-then-deliver,
per-recipient inboxes, server-assigned per-conversation sequence, per-device cursors, idempotent send,
reconnect handled. *Exceptional* — chooses the shared-log-plus-cursor model for large groups with the
storage number to justify it, quantifies the receipt-traffic trap, has a schema-evolution plan for
slow-updating clients, and states the connection-tier cost.

**Traps.** Presence and messaging conflated (they have completely different consistency needs — see
SD-13). Assuming a client that has an ack has displayed the message. Building group chat as N 1:1
chats and not noticing the write amplification until asked.


---

### SD-10 · Live comments & reactions on a live stream   [T2 · M★]

**Read aloud:** *"A live video has two million concurrent viewers commenting and reacting. Design the
system that shows them each other's comments in near real time."*

**Crux.** The fan-out is **2M readers on one logical channel**, which no single node can serve — so
the design is a **fan-out tree/hierarchy**, and the honest observation that at this scale **not every
viewer needs to see every comment.** Sampling is a feature, not a compromise.

**Numbers if asked:** 2M concurrent viewers on the hottest stream, 50k comments/sec at peak, 500k
reactions/sec, comments should appear within ~2 seconds, dropping some comments for some viewers is
acceptable, reactions can be aggregated into counts rather than shown individually.

**Listen for:** persistent connections aggregated behind a **hierarchy of fan-out nodes** (edge →
regional → source) rather than every subscriber on one publisher · **shedding and sampling** as
explicit design: show each viewer a sample of the comment firehose, prioritising the author's own
comment (must always appear — the perceived-correctness trick) and high-signal comments ·
**reactions aggregated into counts** near the edge, not delivered individually · backpressure when a
downstream node can't keep up, with an explicit drop policy · the write path decoupled from the
fan-out path so comment persistence isn't blocked by delivery · connection storms at stream start
and end.

**Probes:** *"Two million subscribers to one channel — what's your fan-out topology?"* · *"50k
comments a second and a viewer can read maybe 3. What do you do?"* (fishing for deliberate sampling)
· *"A viewer must always see their own comment appear. How, if you're sampling?"* · *"An edge node is
saturated. What gets dropped and who decides?"* · *(EM bar)* *"How would you know viewers were
silently missing comments, and what's the SLO?"*

**Weak / Strong / Exceptional.** *Weak* — one pub/sub topic per stream, all 2M subscribers on it,
every comment to everyone. *Strong* — hierarchical fan-out, aggregation of reactions, explicit
sampling and shedding policy, own-comment guarantee. *Exceptional* — reframes "deliver everything"
as the wrong goal early, prices the connection tier, designs the drop policy as a product decision
with the PM, and handles the start-of-stream connection storm.

---

### SD-11 · Photo & video sharing (Instagram-like)   [T2 · M★]

**Read aloud:** *"Design a photo-sharing service — upload, storage, and serving to a global
audience."*

**Crux.** The **blob/metadata split**, and never letting a large binary pass through the application
tier. Trivial to state, and candidates still route 5 MB uploads through their API servers.

**Numbers if asked:** 500M DAU, 100M photos uploaded/day, average 3 MB original, each needs 4
derived sizes, reads 1,000× writes, global audience, photo must be viewable within seconds of
upload, retention forever.

**Listen for:** **direct-to-object-storage upload** via pre-signed URL; the API tier issues
credentials and records metadata, and never proxies bytes · metadata in a sharded relational or
wide-column store, blobs in object storage · **asynchronous derivative generation** (thumbnails,
sizes) off a queue, with the "what does the user see before it's ready" question answered · CDN in
front, with cache keys per size and a stated hit-ratio target · the storage number computed
(100M × 3 MB × ~1.7 for derivatives ≈ 500 TB/day — **this figure should visibly change their mind
about something**) · lifecycle tiering of cold originals · idempotent upload so a client retry
doesn't create duplicates.

**Probes:** *"Trace the bytes. Which of your components does the 3 MB actually pass through?"* ·
*"How much are you storing per day, and what's that per year in money?"* · *"The user uploads and
immediately opens the photo. Is the thumbnail ready? What do they see if not?"* · *"Your transcode
queue is 4 hours behind. What's the user impact and what do you do?"* · *(EM bar)* *"Where's your
biggest cost line, and what's the first lever you'd pull?"*

**Weak / Strong / Exceptional.** *Weak* — upload POSTed to an API server which writes to a database
blob column, resizing synchronously. *Strong* — pre-signed direct upload, metadata/blob split, async
derivatives, CDN, lifecycle tiers. *Exceptional* — the storage cost figure drives concrete decisions
(fewer derivative sizes, on-the-fly resizing at the edge, aggressive cold tiering), and they can
justify serving derivatives on demand versus precomputing them.

---

### SD-12 · Notification & push platform   [T1 · M A MS]

**Read aloud:** *"Design the platform that sends notifications to users across push, email and SMS —
used by every product team in the company."*

**Crux.** It is a **platform** problem, not a delivery problem. The interesting design is the
governance layer: **dedup, preferences, rate limiting per user, and the ability to stop a bad
campaign that is already in flight.** A candidate who designs only the delivery pipeline has missed
the question.

**Numbers if asked:** 500M users, 1B notifications/day with a 10× peak (a marketing campaign),
channels are mobile push, email, SMS and in-app, third-party providers for each with their own rate
limits and failure modes, transactional notifications must be delivered in seconds, marketing can be
minutes, a user must never receive the same notification twice.

**Listen for:** a **request/intent layer** separated from the **delivery layer**, with the intent
durably queued · **per-user rate limiting and quiet hours** enforced centrally so no team can spam
(the platform's real value) · **preference and consent checks** as a blocking gate before send, plus
the legal dimension for email/SMS · **deduplication** by (user, notification key) with a stated
window · **channel fallback** logic (push fails → email) and the trap that fallback can duplicate ·
per-provider adapters with **provider rate limits, retries with jitter and a circuit breaker** ·
**templating and localisation** as a first-class concern · priority classes so a marketing burst
cannot delay a password reset — **this is the probe that separates strong from average** ·
**a kill switch** to halt an in-flight campaign, and the honest statement that already-delivered
notifications cannot be recalled.

**Probes:** *"A marketing campaign to 400M users is queued. A password reset comes in. What happens?"*
· *"The campaign has a typo and 80M have already gone out. What can you actually do?"* · *"Push fails
and you fall back to email. The push actually arrived. Now what?"* · *"A team's retry loop sends the
same notification 5 times. Whose job is it to stop that, and how?"* · *(EM bar)* *"Twenty teams
depend on this. What's the quota model and what's your on-call surface?"*

**Drips** (format `drip`, §7.5 — read the prompt above as increment #1): **#2** *"Users set quiet hours and per-channel preferences."* · **#3** *"Marketing sends a blast to 50M users — transactional messages must not be starved."* Listen for the delta stated out loud and the seam that absorbs it.

**Weak / Strong / Exceptional.** *Weak* — an API that calls the push provider synchronously; no
dedup, no preferences, no priorities. *Strong* — intent/delivery split, durable queues, priority
classes, dedup, preference gate, provider adapters with circuit breakers. *Exceptional* — treats
governance as the product, designs the kill switch and states its limits honestly, prices SMS as the
dominant cost line, and defines the platform's contract with its twenty tenant teams.

---

### SD-13 · Presence & online status   [T2 · M MS]

**Read aloud:** *"Design 'who's online' for a billion-user product."*

**Crux.** Presence is **high-write, low-value, and O(N²) if you're naive** — every user's status
change potentially notifies everyone who can see them. The senior move is to attack it from the
**read side and the staleness budget**, not the write side.

**Numbers if asked:** 1B users, 100M concurrently online, average 200 contacts, heartbeat every 30 s,
"online within 30 seconds of truth" is acceptable, a user viewing a contact list sees ~50 at a time.

**Listen for:** heartbeat-with-TTL as the state model (presence expires; absence of a heartbeat is
the offline signal) rather than explicit online/offline events, which are lost on crashes · **pull on
read, not push on change** — compute presence when someone actually looks, for the ~50 contacts
visible, instead of fanning out 100M status changes to 200 contacts each (the estimate that proves
this is the whole question) · subscribe-to-visible only for open conversations · a stated
**staleness budget** and the observation that nobody notices 30 seconds · in-memory store with TTL,
and the accepted consequence that a restart loses presence and it self-heals within one heartbeat ·
the last-seen-timestamp variant as a much cheaper product answer.

**Probes:** *"100M users going online and offline, 200 contacts each — what's the fan-out per
second?"* (should be a visibly alarming number) *"Now what?"* · *"How do you know someone's offline
if their phone just died?"* · *"Your presence store restarts. What do users see?"* · *"Is 30 seconds
stale acceptable? Who decides?"* · *(EM bar)* *"This is the highest-write, lowest-value data in the
product. How do you make that argument to the PM who wants it instant?"*

**Weak / Strong / Exceptional.** *Weak* — a database row per user updated on every change, pushed to
all contacts. *Strong* — heartbeat + TTL in memory, computed on read for visible contacts, explicit
staleness budget. *Exceptional* — leads with the fan-out estimate and uses it to reframe the
requirement, offers last-seen as a cheaper product alternative, and is comfortable saying presence is
a best-effort signal.

---

### SD-14 · Social graph store (friends, follows, friends-of-friends)   [T2 · M★ G]

**Read aloud:** *"Design the storage and serving layer for a social graph — a billion nodes, a
hundred billion edges — supporting 'who do I follow', 'who follows me', and 'do we have friends in
common'."*

**Crux.** **How you shard a graph.** Any sharding scheme makes some traversal cross shards, and the
design is a choice about *which* queries you make cheap and which you make expensive — plus the
recognition that friends-of-friends is a fundamentally different (and much more expensive) query
than the adjacency lookups.

**Numbers if asked:** 1B users, 100B edges, average degree 200 with a max in the tens of millions,
adjacency reads 100k/sec, edge writes 10k/sec, p99 under 50 ms for adjacency, mutual-friends can take
200 ms and be approximate.

**Listen for:** edges stored **twice, in both directions** (following and followers as separate
indexes) with the write cost and consistency window acknowledged — this denormalisation is the
correct answer and the "consistency between the two" question is the good follow-up · sharding **by
node ID** so a user's whole adjacency list is on one shard, and the explicit consequence that any
two-hop query is cross-shard · adjacency lists cached aggressively; the graph is read-dominated and
cache hit ratio is the design's economics · **mutual friends via set intersection of two adjacency
lists**, smaller list first, and for high-degree nodes either a bounded/approximate answer or a
precomputed sketch · **the supernode problem** — an account with 50M followers whose adjacency list
does not fit the assumptions; needs splitting across shards or a separate representation ·
bidirectional (friend) vs unidirectional (follow) modelled distinctly, including pending requests ·
why a general-purpose graph database is usually the wrong answer at this scale (traversal depth is
1–2, and specialised indexes beat a general engine).

**Probes:** *"Which query did your sharding choice make expensive, and was that the right trade?"* ·
*"Do we have friends in common — walk me through the actual computation and its cost for two users
with 200 friends each. Now for one with 50 million."* · *"You write both edge directions and the
second write fails. What's the state and who notices?"* · *"Why not a graph database?"* · *(EM bar)*
*"Every product team wants a new query type. How do you keep this from becoming everyone's
database?"*

**Weak / Strong / Exceptional.** *Weak* — a single `friendships` table with an index, joined at query
time. *Strong* — bidirectional denormalised adjacency, node-ID sharding with the cross-shard cost
named, heavy caching, intersection for mutuals, supernode handling. *Exceptional* — states which
queries the shard key sacrifices and why that's acceptable, handles the failed second write with a
repair mechanism, bounds the mutual-friends cost explicitly, and treats the query surface as a
platform contract to be governed.
