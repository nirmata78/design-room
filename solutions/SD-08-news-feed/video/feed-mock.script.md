# News feed mock round (video), v3

<!-- Video script for ~/.claude/skills/slide-video-kit/scripts/build_video.py. [slide: v-NN] = video/frames/v-NN.png;
     NN is the number printed on every slide. Speakers: I interviewer · C candidate · V candidate, key line (slower) ·
     N coach. [pause: s] = silence. Content follows ../../SD-08-news-feed.md. v3 2026-10-29, the author's review of v2:
     every term defined on first use, diagrams walked box by box, each path told as C4 → sequence → code, Chen ERD,
     wide-column and outbox/CDC explained, the ranking A-P-I shown. Target ~40 min, hard limit 45.
     v2 in .v2-staff-2026-10-29/, v1 in .v1-em-2026-10-29/. -->
<!-- voices: N=af_heart@0.92 I=bf_emma@0.95 C=am_michael@0.9 V=am_michael@0.84 -->
<!-- labels: N=COACH -->
<!-- say: CDC=C-D-C ZADD=Z-add ZSET=Z-set ZREVRANGE=Z-rev-range MGET=M-get LPUSH=L-push LTRIM=L-trim -->

## Before you start

[slide: v-01]
N: A mock system design round at the Staff bar, level six or seven, the way FAANG and other top-tier companies run it. The prompt is the news feed. You'll hear the interviewer, the candidate, and me, the coach. Then five follow-ups. On a second pass, pause after each question and answer first. Every slide is numbered, top right, for feedback.

[slide: v-02]
N: Three things carry a Staff round. Depth on the crux, here fan-out: how one post reaches millions of feeds. Trade-offs with evidence: every store and transport against the alternative that loses. And a correctness stance: where duplicates, deletes and blocks are enforced. Slides badged A-U-X are the manager layer; in a Staff round, skip them.

[pause: 0.8]

## Requirements

[slide: v-03]
I: Let's start. Design the home feed for a social network with a billion users. The ranked list of posts a user sees when they open the app.

C: A few questions first. The answers decide the architecture.

[slide: v-04]
C: How many users, and how many are active each day?

I: A billion total. About five hundred million daily.

C: And how do reads compare with writes?

I: Feed reads are about a hundred times the number of posts.

C: So I'll optimise the read path, and I'm willing to pay extra on write to make reads cheap. Now the important one. How many followers can a single account have? Not the average. The maximum.

I: About two hundred on average. The biggest accounts have over a hundred million.

C: That tail will decide the design.

N: "Not the average, the maximum" is the seniority signal. And "the tail" means the few accounts at the extreme end of a distribution. The design has to survive them. More on that in a moment.

[slide: v-05]
C: Latency?

I: P ninety-nine under two hundred milliseconds for loading the feed.

C: Ranked or chronological?

I: Ranked. A scoring service already exists. Another team owns it.

C: Then ranking is one stage in my pipeline, with a time budget, not the problem I'm solving. Freshness? How soon must a new post appear?

I: Seconds for people you're close to. About a minute in general.

C: So asynchronous delivery is fine; nothing has to happen inside the post request. And depth: the first fifty items on open, then more pages as you scroll?

I: Yes.

[slide: v-06]
C: One product question. Which is worse for the user: seeing a post twice, or missing one?

I: What would you choose?

C: Never show a duplicate, because that looks broken; tolerate a rare miss. Duplicates I remove on read. In scope: publishing, the feed, pagination, follows, deletes and blocks. Out of scope, said aloud: the ranking model, ads, media upload, search and notifications.

## Terms, defined once

[slide: v-07]
N: Before the design, five words the rest of the round uses constantly. Fan-out on write, also called push: when someone posts, copy the post's I-D into the feed of every follower, right then. Fan-in on read, also called pull: when someone opens the feed, gather recent posts from everyone they follow, right then. A timeline: a precomputed list of post I-Ds per user, newest first. Hydration: turning a list of I-Ds into full posts, text, author and media, with one multi-get from a cache. And the tail, which you just heard: the rare accounts at the extreme end.

[pause: 1.0]

[slide: v-08]
N: Push against pull, as a picture. On the left, fan-out on write: the author posts once, and the I-D is written into follower A's, B's and C's timelines. Work at post time, growing with followers; reading is one lookup. On the right, fan-in on read: authors X, Y and Z each keep their own list, the author index, and the reader's open merges all three. Writing is one append; work at read time, growing with followees.

[pause: 1.0]

N: Push makes reads cheap and writes expensive; pull, the opposite. The design is about where to pay.

[slide: v-09]
N: And this is what "the tail decides the design" means. Followers per account, on a log scale, so each grid line is a hundred times the last. The median account has a couple of hundred followers. The top one percent, around ten thousand. The top hundredth of a percent, around a million. And the largest, over a hundred million. Illustrative, but the shape is real. Under push, one post costs one write per follower, so one post from the bottom bar costs a hundred million writes. A design that works for the median and fails for them, fails.

[pause: 1.0]

## The thesis

[slide: v-10]
C: So, my framing.

V: Push for most accounts. Pull for celebrities.

[pause: 1.0]

C: Pushing every post into every follower's timeline breaks on the account with a hundred million followers. Pulling every feed at read time breaks the two-hundred-millisecond budget for everyone else, because the average user follows a couple of hundred accounts. So it's a hybrid, with a threshold between the two that I'll derive from numbers, not pick.

[slide: v-11]
C: Targets. Feed load under two hundred milliseconds at p ninety-nine. A new post visible within five seconds at p ninety-five. Reads available ninety-nine point nine five percent. And deleted or blocked content gone within seconds: a trust and safety requirement.

## Back of the envelope

[slide: v-12]
C: The arithmetic, each number with its consequence. Five hundred million daily users, five opens each, over eighty-six thousand four hundred seconds, is about twenty-nine thousand feed loads a second; seventy-five thousand at a three-times peak. That can't touch a database per request, so the feed comes from caches.

C: Posts: five hundred million users, a tenth of a post a day, is about six hundred a second. Small. But each fans out to two hundred followers: a hundred and twenty thousand timeline inserts a second.

C: About half of followers haven't opened the app in thirty days. Skipping them gives sixty thousand. That's the biggest cost lever in the system.

[slide: v-13]
C: The tail. One celebrity post, a hundred million followers. Even at a million inserts a second, that's a hundred seconds of fan-out for one post.

C: Storage. Five hundred million timelines, five hundred entries, sixteen bytes each, is about four terabytes; twelve with three replicas. That fits in memory. Full bodies at a kilobyte would be two hundred and fifty terabytes, sixty times more, and every edit would touch millions of copies. So, I-Ds, not bodies.

C: Hydration: seventy-five thousand opens, fifty posts, a kilobyte each, is about three point seven five gigabytes a second from the post cache.

C: And the latency budget: five milliseconds for the timeline, five for celebrity lists, at most eighty for ranking, twenty for hydration. About a hundred and ten at the median.

[slide: v-14]
V: One celebrity post, a hundred million writes.

[pause: 0.8]

C: So pure fan-out on write is dead for the tail. It's fine for everyone else.

[slide: v-15]
C: The same arithmetic as a funnel, formula on each box. Seventy-five thousand reads. Six hundred posts. Times two hundred: a hundred and twenty thousand inserts. Halved by skipping the idle. Then, per open, five to twenty celebrity lists and fifty hydrations. The red boxes are the expensive part, and they're on the asynchronous write path. Every read is cache only.

I: Mm-hm.

N: Every number as a calculation, each tied to a decision. That's the Staff estimation bar.

## The A-P-I

[slide: v-16]
C: The A-P-I is four calls. Create a post, with an idempotency key. Get the feed, with a cursor and a limit. Follow and unfollow. And delete a post.

[slide: v-17]
C: Publishing, on the wire. The request: text, media I-Ds uploaded separately, visibility, and an idempotency key in a header. If the phone retries, the server sees the same key and returns the same post instead of a second one. The response: two-oh-one, the post I-D, a Snowflake I'll explain with the data model, and the time.

C: On the right, what the system emits, in the same transaction: a post-created event with the post I-D, the author I-D and the author's tier, normal, mid or celebrity, which the fan-out worker branches on. It goes into Kafka keyed by author, so one author's posts stay in order. How it gets there, the outbox and C-D-C, comes on the write path.

[slide: v-18]
C: Reading. The request: a limit of fifty and an opaque cursor. The response: fifty hydrated items, each with post I-D, author, text, media U-R-Ls on the C-D-N, rank score and time. Then a next cursor, and a ranking field: model, or the recency fallback.

C: The cursor, decoded on the right, is signed base64 J-S-O-N: the last item's score, its post I-D to break ties, the ranking version, and the candidate snapshot.

[slide: v-19]
I: Why not a plain offset? Page two is items fifty to a hundred.

C: Because the feed moves while you scroll. If five new posts arrive at the top while you read page one, offset fifty now points five items earlier, and you see five repeats. Or, after a delete, you skip one. The cursor says exactly where you stopped: after this score and this post. That stays stable while the feed changes.

[slide: v-20]
C: One more A-P-I I depend on: ranking, another team's. My request, on the left: the viewer, the surface, and up to two hundred candidates, each just I-Ds, a timestamp and its source, timeline or celebrity list. Plus an eighty-millisecond deadline header.

C: The response: a score per post, the model version, and a partial flag. And the grey comment: ranking reads its own features by I-D. I never ship bodies, which keeps the call small and the teams decoupled.

I: And if it's slow?

C: Then I stop waiting at eighty milliseconds, sort the candidates by time, and say "recency" in the response. A worse feed, not a broken one.

## Data model

[slide: v-21]
C: The data model, conceptual, in Chen notation: rectangles are entities, diamonds relationships, ovals attributes, numbers cardinality. A user authors posts: one to many. The double line means total participation: every post has an author.

C: Users relate to users twice. Follows, at the bottom: many-to-many, with two roles, follower and followee, and one attribute on the relationship itself, since when. Blocks, at the top: also many-to-many, blocker and blocked.

C: Attributes. The user I-D, underlined, is the key; follower count is dashed because it's derived from follows. On post, the post I-D is the key, and media I-Ds is a double oval: multivalued.

C: Bottom right is the key modelling choice. Timeline entry is a weak entity, the double rectangle. It has no identity of its own: it exists only in one user's feed, through the identifying relationship, the double diamond, and references one post. Its partial key, dashed, is the post I-D. Drawing it weak says timelines are derived: lose one, rebuild it from follows and posts.

[pause: 1.0]

[slide: v-22]
C: The same model as physical tables. Posts, in red, sharded by post I-D. Its key is a Snowflake: forty-one bits of millisecond timestamp, ten bits of machine I-D, twelve bits of sequence. So I-Ds are unique without coordination, and they sort by time, which means a timeline can order by I-D with no lookup.

C: Next to it, author posts: the author index. Partition key author I-D, clustering key created at, descending, then the post I-D. That's the table pull and rebuild both read. Accounts holds the follower count and the tier that drives fan-out, plus last seen. And the follow relationship is stored twice, as followers and as followees, because the two directions are read by different paths. Fan-out pages through an author's followers. The read path needs a user's followees. A single table can only be partitioned one way, so I store both and keep them in step from one follow event.

[slide: v-23]
I: You keep saying wide-column. What do you mean by it, and why do you need it here?

C: A wide-column store, like Cassandra or Bigtable, organises a table by two keys. The partition key decides which node a row lives on: hash the author I-D, and every row for that author lands on the same node. The clustering key decides the order of rows inside that partition: here, created at, newest first.

C: On the slide, three nodes. Node A holds author four-eight-two-one-three's partition, in red. Inside, rows are already sorted, newest first.

C: So "this author's posts from the last forty-eight hours" is one node, one partition, one sequential read, in time order: exactly what pull and rebuild need. A relational index on author and time does the same; wide-column makes that layout the table itself, spreads partitions by hash, and is built for append-heavy writes.

[pause: 1.0]

[slide: v-24]
C: Now the cache tier in Redis: six keys, and the arrows show how a member of one key names another. Top left, in red, the timeline: one sorted set per active user. Each member is a post I-D packed with its author I-D, sixteen bytes, and the score is the timestamp. Trimmed to five hundred by rank. The arrow to the right says each member points at one post, in the post cache: a hash per post with author, text, media and a deleted flag.

C: Second row. Celebs followed: the five to twenty celebrities a user follows; each member names a celebrity list, which holds that author's last hundred post I-Ds, each pointing at a post. Below, the hide set, blocked or unfollowed authors, filtering both. And last seen, which fan-out reads to skip the idle.

C: So the read path literally follows the arrows: timeline to posts, celebs followed to celebrity lists to posts, with hide subtracted.

[pause: 1.0]

[slide: v-25]
C: And where each key comes from, because none of them is written by hand. Four writers. The fan-out worker, in red, consumes post-created events. For normal and mid authors it adds to followers' timelines and trims; for celebrities it pushes onto the author's list and trims to a hundred.

C: The post-cache filler sits inside the feed service. On a miss it reads the post from the database and sets the hash. When a post is deleted or edited, C-D-C from the posts database deletes the cached copy.

C: The graph-change consumer reads follow and block events: a followed celebrity goes into celebs followed; a block or unfollow into the hide set. And the session tracker sets last seen on every open.

C: Everything here is derived, so losing it costs latency, not data.

[slide: v-26]
C: So, six stores, one job each. Read the last column. Posts are the truth, replicated, never lost. The author index rebuilds from posts. The graph is another team's. Timelines rebuild by pull, celebrity lists from the author index, the post cache refills on a miss. One store is the truth; five can be thrown away and rebuilt. That's what keeps the failure stories short.

N: Conceptual model, physical tables, the storage idea, the cache keys and their writers, then the summary. That's two levels down on data.

[pause: 0.8]

## Technology, against the alternatives

[slide: v-27]
I: Why Redis sorted sets for timelines? Why not keep them in the database?

C: Redis sorted sets: bounded, read in one call, idempotent inserts; losing one costs a rebuild, not data. A Cassandra row per user: rejected, disk reads and compaction on a seventy-five-thousand-a-second path, and trimming creates tombstones, deletion markers that slow reads. A Memcached blob: rejected, a read-modify-write of five hundred entries per insert, with races. Pure pull: fine for phase one, but two hundred merges per open break the budget at scale.

[slide: v-28]
C: For posts, wide-column, for the reasons I just drew. Sharded MySQL or PostgreSQL is viable; resharding is the cost. DynamoDB is viable; hot authors need a split partition key. One relational database is rejected, not for six hundred posts a second, but for fifty petabytes of history and four gigabytes a second of hydration.

[slide: v-29]
C: For transport, Kafka keyed by author: absorbs bursts, replays for rebuilds, and search and notifications consume the same events. Fan-out inside the post call: rejected, seconds for a large account, and one slow shard fails the post. A plain queue: no replay. A dual write, save then publish: a crash in between loses the event.

N: Each choice against the alternative that loses, with the failure that rules it out.

## The write path

[slide: v-30]
C: Now the architecture, one level at a time. C4 level one, the system context. Our system is the red box in the middle: the news feed system. It publishes posts, keeps bounded timelines and serves a ranked feed in two hundred milliseconds.

C: Two kinds of people use it. Authors, top left: six hundred posts a second. Readers, bottom left: seventy-five thousand opens a second at peak.

C: And three external systems, in grey, that we depend on but don't own. The ranking service: we send it about two hundred candidates and give it eighty milliseconds. The social graph: who follows whom. And the media C-D-N, which the reader's app fetches images from directly, by U-R-L; media upload is out of scope.

C: The boundary matters: ranking and the graph are other teams' risks, which I manage with deadlines and caching.

[pause: 1.0]

[slide: v-31]
C: Level two, the containers on the write path. The author's post goes to the post service. The post service writes the post and an outbox row in one transaction into the posts database, which holds both the posts and the author index. From the database, the outbox and C-D-C carry the event into the post-created log, partitioned by author. Fan-out workers consume it. For normal authors, they page through the author's followers from the social graph and insert I-Ds into those followers' timelines, trimmed to five hundred. For celebrities, the event goes to the celebrity recent-posts list instead: one write.

C: And the note on the left is the principle: store I-Ds, never bodies. Four terabytes, not two hundred and fifty.

I: What does "outbox slash C-D-C" mean on that arrow? Do you use both, or either?

[slide: v-32]
C: Both; they do different jobs. The transactional outbox decides what to publish: the event is a row in an outbox table, written in the same transaction as the post. Both exist, or neither.

C: C-D-C, change data capture, decides how it leaves: a connector reads the database's commit log and publishes each new outbox row to Kafka. No polling, no second write.

C: Could I use only one? At smaller scale, yes. An outbox with a relay polling the table works; it adds load and latency. Or C-D-C straight off the posts table; that works too, but every consumer then depends on the table's internal schema. The outbox gives them a deliberate contract.

[slide: v-33]
C: As a sequence. One: the post service begins a transaction and inserts the post row. Two: in the same transaction it inserts the outbox row, the post-created event, and commits. Three: the database confirms. Both rows or neither. Four, asynchronously: the commit log streams that outbox insert to the C-D-C connector. Five: the connector publishes post-created to the log, keyed by author I-D. Six: the fan-out consumer group reads it. Seven: search and notifications read the same event in their own groups, at their own pace.

C: The green note is the guarantee. If the transaction rolls back, there's no event. If the connector crashes, it resumes from its saved position in the commit log. So delivery is at least once. Which means my consumers must be idempotent, and they are.

[pause: 1.0]

[slide: v-34]
C: Now the whole publish for an author with two thousand followers. One: post, with an idempotency key. Two: post and outbox row, one transaction. Three: two-oh-one with the post I-D at once; the author is done, the rest is asynchronous. Four: C-D-C puts post-created on the log. Five: a worker consumes it. Then the loop: six, the next page of followers; seven, skip the inactive; eight, insert into each timeline and trim to five hundred. Two pages, milliseconds, well inside five seconds.

I: Where does the worker learn that this author is a celebrity? Does it look it up?

[slide: v-35]
C: No lookup. It's in the event. The post service stamps the author's tier into post-created at publish time, from the accounts table, which it reads through a cache. The worker just branches.

C: On the slide: the log feeds the fan-out worker in red. Three branches. Normal, under about ten thousand followers: push to every follower active in the last thirty days. Mid, ten thousand to a hundred thousand: push only to followers active today. Both of those write into followers' timelines with Z-add. And celebrity, over a hundred thousand: one L-push onto the author's own list, no fan-out at all.

C: The tier itself is recomputed by a daily job from the follower count. With a gap between the up and down thresholds, so an account hovering at the line doesn't flip back and forth every day.

[slide: v-36]
C: The worker in code, part one, the router. If the author is a celebrity: L-push the post I-D onto their list and L-trim it to a hundred. One write. Otherwise, push to followers, on the next slide.

C: And the last line matters: commit the Kafka offset only after every write has succeeded. If the worker crashes halfway, the event is delivered again, which is at-least-once.

[pause: 0.8]

[slide: v-37]
C: Part two, pushing to followers. Active means seen today for a mid-tier author, otherwise in the last thirty days. Page through followers a thousand at a time, keeping the active ones.

C: Then one Redis pipeline per page, which sends all the writes in a single round trip. For each active follower: Z-add the post into their timeline, with the timestamp as the score. And trim the timeline by rank, keeping the newest five hundred.

C: Why is at-least-once safe? Z-add of a member already in the set adds nothing, so a re-delivered event changes nothing. Idempotent by construction.

N: The write path in order: containers, the pattern, the sequence, the routing, the code. Now the read path the same way.

[pause: 0.8]

## The read path

[slide: v-38]
C: Level two, the read path. The reader calls get feed on the feed service, in red. The feed service makes one read to the timeline cache: about five hundred I-Ds. Then five to twenty reads to the celebrity recent-posts cache, one per celebrity the reader follows. Which celebrities is the celebs-followed set, kept in sync from the social graph. It merges and filters, then sends the top two hundred candidates to ranking, on the right, with an eighty-millisecond deadline. Then it hydrates the top fifty from the post cache, which falls back to the posts database on a miss.

C: The green note is the rule for the slowest dependency: if ranking is slow, fall back to recency inside the deadline.

[pause: 1.0]

[slide: v-39]
C: As a sequence, with timings. One: get feed. Two: my timeline, five milliseconds. Three: followed celebrities' lists, pipelined, five more. Four, highlighted: merge, dedup, filter hidden authors, keep two hundred by recency. Five: ranking, eighty-millisecond deadline; the alt box is the recency fallback. Six: multi-get the top fifty, twenty milliseconds. Seven: fifty items and a cursor, about a hundred and ten milliseconds.

[slide: v-40]
C: The read path in code, also in two parts. Part one, gathering candidates. Read the timeline: Z-rev-range, the newest five hundred. If the timeline is missing, because a cache node was lost, rebuild it by pull. That's deep dive three.

C: Then the celebrities: read the celebs-followed set, and fetch each of their lists, the newest hundred I-Ds, all in one pipelined round trip.

C: Then blocks and unfollows, enforced here: drop candidates whose author is in the hide set. Dedup, because after a tier change a post can arrive both ways. Return the newest two hundred past the cursor.

[slide: v-41]
C: Part two, ranking and hydration. Gather the candidates. Then try ranking with an eighty-millisecond deadline. If it times out, sort by time instead. Degrade, never fail.

C: Then hydration, the step that turns I-Ds into posts. Take the top fifty, and multi-get their post hashes in one call. Drop anything missing or marked deleted. That one line is where deletes are enforced, and I'll come back to it. Return the posts, and a cursor built from the last item.

[slide: v-42]
C: So a hundred and ten milliseconds at the median, and under two hundred at p ninety-nine, because the one slow stage has a hard deadline and a fallback.

I: And if ranking is down altogether?

C: The feed gets worse, not broken. Which is dangerous in its own way, because it never shows up as an error rate. So I'd alert on the fallback rate: that's a quality outage hiding behind a green dashboard.

## Deep dive one: the celebrity

[slide: v-43]
I: Someone with a hundred million followers posts. Walk me through it, end to end.

[pause: 1.5]

[slide: v-44]
C: Three tiers of author, and the post takes a different path in each. On the left, under about ten thousand followers: plain push, to every follower who's been active in thirty days. Cheap per post, and these are almost all accounts.

C: In the middle, ten to a hundred thousand: push only to followers active today. Most aren't, so this cuts the cost sharply; latecomers pick the post up from the author index.

C: On the right, over a hundred thousand: pull. No fan-out. The author's recent posts are cached in one list, and every reader merges it at read time.

C: And the note: the threshold is a config value, set where one post's fan-out cost exceeds the extra read cost across that author's followers. I'd start at ten thousand and measure.

[pause: 1.0]

[slide: v-45]
C: The celebrity's post as a sequence. One: the celebrity posts, through the post service as usual, and it lands on the log. Two, highlighted: the worker appends the post I-D to that author's list. One write, not a hundred million. The red note is why: a hundred million inserts would take about a hundred seconds even at a million a second.

C: Then a reader opens the feed. Three: their timeline. Four: their celebrities' lists. Five, highlighted: merge and dedup by post I-D. Six: one ranked feed; push and pull are invisible to the reader.

I: But that list is now read by tens of millions of readers.

C: Yes. It's the hottest key in the system. So it's replicated across many cache nodes, and readers spread over the replicas. It's small, a hundred I-Ds, so replicating it is cheap.

[slide: v-46]
I: Why there, though? Why ten thousand and not a thousand, or a million?

C: Because the costs grow differently. Push grows with followers: at a million inserts a second, two thousand followers is two milliseconds; a hundred thousand, a hundred; ten million, ten seconds, swamping the workers; a hundred million, a hundred seconds.

C: Pull cost is flat: one list read per open, about a third of a millisecond, whatever the size, but paid on every open by every follower. So push wins for small accounts, pull wins outright for huge ones, and the crossover depends on how often the author posts and the followers open the app. So I measure both.

[slide: v-47]
C: When an account crosses the line, there's no migration. If it grows past the threshold, the tier job marks it celebrity. New posts stop fanning out and go to its list. The entries already in followers' timelines simply age out as newer posts push them down. If it falls back below, fan-out resumes, and the read-time merge covers the gap. No backfill in either direction, because the list and the timeline are merged and deduplicated on every read.

[slide: v-48]
V: The threshold is where one post's fan-out cost exceeds the extra read cost across its followers.

[pause: 0.8]

C: Start at ten thousand, measure both sides, make it a config value.

N: The threshold derived from a table, not asserted, and the crossing handled with no backfill. That's two levels down on the crux.

[slide: v-49]
C: A timeline entry is sixteen to twenty-four bytes, capped at five hundred, because almost nobody scrolls further; deeper pages come from author indexes. Bodies live once, so an edit or delete is one write.

## Deep dive two: deletes and blocks

[slide: v-50]
I: A user deletes a post. Or blocks someone. That post I-D is already in millions of timelines. Now what?

[pause: 1.5]

[slide: v-51]
C: I don't chase the copies. As a sequence. One: the delete is one write to the source of truth, the posts database. Two, asynchronously: C-D-C sees that change and invalidates the post in the post cache. That's the second use of C-D-C, on the posts table this time.

C: A reader opens the feed. Three: hidden authors are dropped using the hide set. Four: hydrate the top fifty. Five, highlighted: the deleted post comes back missing, so it's dropped. Six, later: a cleanup job removes stale I-Ds, but that's cosmetic.

I: What about the cursor? If I delete the post a cursor points at?

C: The cursor holds a score and an I-D, not a position, so the next page starts after that point whether the post still exists or not.

[slide: v-52]
V: Correctness lives on the read path. Cleanup is cosmetic.

[pause: 0.8]

N: That one sentence answers a whole class of follow-ups: edits, deletes, blocks, takedowns. Say it, then show the line in the code where it's enforced.

## Deep dive three: losing a shard

[slide: v-53]
I: A cache node holding timelines dies. What happens?

C: As a sequence. One: a reader opens the feed. Two: the feed service asks for their timeline. Three: empty, the shard is gone. Nothing is lost, because timelines are derived. But if every affected reader rebuilds at once, the author index gets a stampede, and that can take down the source of truth.

C: So four, highlighted: ask the rebuild limiter for a token. It coalesces, so five refreshes trigger one rebuild, and caps the total rate. Token granted: merge the followees' author indexes and write the timeline back. Capacity exhausted: don't fail; serve a degraded feed from the celebrity lists, and rebuild on a later open.

C: It's the same pull path as phase one and catch-up: exercised all the time, so it works when needed.

[pause: 1.0]

[slide: v-54]
C: C4 level three, inside the feed service. The assembler gathers about two hundred I-Ds; if the timeline is missing, the rebuilder pulls, coalesced. The filter removes deletes, blocks and unfollows. The ranking client, in red, owns the deadline and fallback. The hydrator multi-gets the top fifty. The cursor codec signs and checks cursors.

## A requirement added mid-round

[slide: v-55]
I: New requirement. Product wants a "catch up on the last forty-eight hours" view, in chronological order.

[pause: 1.5]

[slide: v-56]
C: The ranked, bounded timeline can't answer that: it's capped at five hundred and ordered by rank. So I won't distort it. A new catch-up endpoint in the feed service merges the followees' author indexes for the last forty-eight hours. Thanks to the wide-column layout, each followee is one partition read in time order. The result is cached per user for a few minutes. The timeline cache on the right is untouched.

C: It's the rebuild's pull path, a heavier read, which is the right trade for an occasional feature. I'd say the cost aloud.

## Failures and operations

[slide: v-57]
C: Failures. Fan-out lag: priority lanes for close friends, and a lag alert. A lost shard: rebuild through the limiter. Ranking down: recency fallback. A post-cache stampede after a deploy: warm first, shed low-ranked hydration. A viral celebrity: replicate the hot list wider.

[slide: v-58]
C: The S-L-O I care most about is freshness: post to visible, p ninety-five, measured by synthetic accounts that post and read all day. And silent quality: fallback rate, empty-feed rate, engagement per session.

[slide: v-59]
C: Cost: four terabytes times three replicas is twelve terabytes of memory; a hundred and twenty thousand inserts a second is ten billion a day. Skipping the idle halves the writes; the threshold is the second lever.

## The EM layer, auxiliary

[slide: v-60]
N: The next two slides are the manager layer. In a Staff round, give them a sentence at most.

C: Phase one, pure pull with caching. Phase two, push for active users, when latency says so. Phase three, the celebrity split, when an account crosses the line. Each triggered by a measured number.

[slide: v-61]
C: Three teams along the data: publish and graph; fan-out and timelines, owning freshness on-call; feed serving, owning the budget. Contracts: the post-created event and the timeline schema.

## The close

[slide: v-62]
C: To close.

V: I traded strict freshness for seconds of eventual consistency.

[pause: 0.8]

C: A hybrid feed: post I-Ds pushed into bounded timelines for most accounts, celebrities pulled and merged at read time, deletes and blocks enforced on the read path, ranking inside a deadline with a fallback. Next, I'd tune the threshold with real data, and stop fanning out to inactive users.

I: Thanks. A few follow-ups.

## Follow-up 1: the ranking budget

[slide: v-63]
I: The ranking team has a new model that lifts engagement. It needs three hundred milliseconds. They want it in the feed next sprint.

[pause: 1.5]

[slide: v-64]
C: Yes, as asked, breaks p ninety-nine for everyone. Pre-rank on app background, off the critical path. Or two stages: a cheap model narrows to fifty, the heavy one ranks only those. Then a one percent holdout, engagement against latency, and the product owner decides with data.

V: The budget is a product decision with a number on it. My job is to price it, and offer a way to have both.

[pause: 0.8]

## Follow-up 2: the incident

[slide: v-65]
I: Sunday, eight in the evening. A timeline cache cluster is lost. One user in five opens an empty feed.

[pause: 1.5]

[slide: v-66]
C: Detect: the empty-feed rate pages on-call. Contain: degraded feed on, rebuild rate capped, because a fifth of users rebuilding at once melts the author index. Recover: replace capacity, rebuild gradually, coalesced. Learn: a blameless review, the limiter's tuning, a warm standby, a game day. No data is lost; the risk is the rebuild.

## Follow-up 3: the migration

[slide: v-67]
I: Today the feed is pure pull, and it's getting slow. Two teams, one quarter, no downtime. Get us to the hybrid.

[pause: 1.5]

[slide: v-68]
C: Weeks one to three, fan-out in shadow; timelines fill, nobody reads them. Four to six, read both, serve pull, diff the top fifty. Seven to nine, ramp from one percent to everyone. Ten to thirteen, the celebrity split; the pull path stays as the rebuild path. Every step behind a flag.

V: Shadow, compare, ramp. Never switch on faith.

[pause: 0.8]

## Follow-up 4: the memory bill

[slide: v-69]
I: Finance says the timeline tier's memory bill doubled this year. Users grew twenty percent.

[pause: 1.5]

[slide: v-70]
C: Then something else grew. The bill is users times entries times bytes per entry. Timelines kept for inactive users? A raised cap? A body creeping into the row? Levers: stop fanning out to the idle and evict their timelines; shorten the list if scroll depth allows; audit the row. And report cost per daily active user.

## Follow-up 5: the power reader

[slide: v-71]
I: Some users follow five thousand accounts, three hundred of them celebrities. Their feed is slow.

[pause: 1.5]

[slide: v-72]
C: The hybrid's own weak spot: three hundred list reads per open blows p ninety-nine. Cap the merge to the thirty celebrities they engage with most. Or, for heavy readers only, a background job folds celebrity posts into their timeline, so for them celebrities become push. And measure who's affected, maybe a tenth of a percent, with their own S-L-O.

V: Treat the tail of readers like the tail of authors.

[pause: 0.8]

N: The candidate found the design's own failure mode and fixed it with the same idea that built it. That's what separates level seven.

## Debrief

[slide: v-73]
N: Where it lands. Senior asks the read-write ratio; Staff asks for the maximum and says a hundred million writes. Senior picks push or pull; Staff gives three tiers, the lag table, the crossing, the power reader. Senior says "a timeline cache"; Staff draws timelines as a weak entity, sized, with the key layout. Plus wire formats, a signed cursor, and filtering on read.

[slide: v-74]
N: Six checks before the real round. Ask for the maximum follower count. Every number as a calculation. Wire formats for the post, the feed page and the cursor. Every store and transport against its alternatives. Deletes on the read path, ranking inside a deadline. And the manager layer only when the loop asks for it. Good luck.
