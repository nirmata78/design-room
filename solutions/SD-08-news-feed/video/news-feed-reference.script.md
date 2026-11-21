# SD-08 News feed / home timeline: reference solution (Staff L6/L7)

<!-- Video script for slide-video-kit/scripts/build_video.py. [slide: v-NNN] = frames/v-NNN.png, the number printed on every slide.
     Speakers: C candidate · I interviewer · V key line (slower) · N coach. Generated from src/*.py: edit the sources, not this file. -->
<!-- voices: N=af_heart@0.92 I=bf_emma@0.95 C=am_michael@0.9 V=am_michael@0.84 -->
<!-- labels: N=COACH -->
<!-- say: SLO=S-L-O SLOs=S-L-Os SLI=S-L-I SLIs=S-L-Is TTL=T-T-L API=A-P-I APIs=A-P-Is RAM=ram TB=terabytes MB=megabytes GB=gigabytes KB=kilobytes HTTP=H-T-T-P SQL=S-Q-L CDN=C-D-N CDC=C-D-C DAU=D-A-U ID=I-D IDs=I-Ds EM=E-M AUX=aux SRE=S-R-E RFC=R-F-C Redis=Reddis MVP=M-V-P QPS=Q-P-S CPU=C-P-U p99=P-ninety-nine p95=P-ninety-five p50=P-fifty -->


## 0 Cold open

[slide: v-001]
[pause: 1.2]
C: The news feed is the question everyone has seen. Push or pull, and the textbook says: both. Interviewers keep asking it anyway, because the grade is not on the word hybrid. It is on what comes after it: where the line sits and why, what happens to the account that crosses it, how a deleted post leaves millions of copies, and what the feed does when the ranker is slow or a cache shard is gone.
[pause: 1.8]

[slide: v-002]
[pause: 0.6]
I: Design the home feed for a social network with a billion users. The ranked list of posts a user sees when they open the app.
[pause: 1.5]

[slide: v-003]
[pause: 1.3]
C: Here is the hook. Followers per account, on a log scale. The median account has about two hundred followers. The top one percent has around ten thousand. And the largest have over a hundred million.
C: If I precompute feeds by copying each post into every follower's list, the cost of one post is its author's follower count. For the median author that is nothing. For the account on the bottom row it is a hundred million writes, for one post. The tail decides the architecture, not the average.
[pause: 1.1]

[slide: v-004]
[pause: 1.0]
N: Five axes. The weak signal is a clean push design or a clean pull design, defended well. The strong signal is the arithmetic that puts a line between them, and what happens on the read path to keep the feed correct.
C: I'll keep one question in view the whole way: where does correctness live? Because a feed is full of copies, and copies go stale.
[pause: 1.0]

[slide: v-005]
[pause: 0.7]
V: A feed is a materialised view that is cheap to read for almost everyone and impossible to precompute for a few. So: push post IDs to the followers of ordinary accounts, pull the celebrities at read time, say where the line is and why, and keep every correctness rule on the read path.
[pause: 1.0]
C: Concretely: a durable source of truth for posts, a small precomputed list of post IDs per reader, a merge of a few celebrity lists when the feed opens, and a read path that filters, ranks under a deadline and hydrates, all inside two hundred milliseconds.
[pause: 1.6]

[slide: v-006]
[pause: 0.6]
C: The order. Requirements and scope, then numbers, then a short theory chapter. Then the A-P-I and data, and a design in three versions, each answering the objection to the one before.
C: Then most of the time: eight challenges that break the design, where each fix creates the next question. A build cost, because someone has to staff this. And a recap.
[pause: 0.8]

[pause: 1.4]

## 1 Requirements and scope

[slide: v-007]
[pause: 1.2]
C: Eight questions before I draw anything. Each answer is used later.
[pause: 1.8]

[slide: v-008]
[pause: 0.6]
C: How many users, and how many are active?
I: A billion users. Five hundred million daily active.
C: Daily active is the number that matters. It sizes the reads and the memory, because only active users need a precomputed feed.
[pause: 0.6]

[slide: v-009]
[pause: 0.6]
C: What is the ratio of reads to writes?
I: Feed reads are about a hundred times post writes.
C: So I optimise the read path and accept paying on the write path. That is the argument for precomputing at all.
[pause: 0.6]

[slide: v-010]
[pause: 0.6]
C: How many accounts does a user follow, and what does the distribution look like?
I: About two hundred on average. And on the other side, some accounts have over a hundred million followers.
C: That is the tail from the cold open. Asking about the distribution, not just the average, is the question that changes the design.
[pause: 0.6]

[slide: v-011]
[pause: 0.6]
C: What latency, and is the feed ranked?
I: P-ninety-nine under two hundred milliseconds for the first page. Ranked. A scoring service exists. Treat the model as a black box.
C: Good. Ranking becomes a stage with a budget inside the two hundred, not the problem I'm solving.
[pause: 0.6]

[slide: v-012]
[pause: 0.6]
C: How fresh must the feed be?
I: Seconds for people you follow closely. A minute is tolerable in general.
C: That rules out strict consistency and allows asynchronous fan-out. It also says close ties deserve priority.
[pause: 0.6]

[slide: v-013]
[pause: 0.6]
C: How deep do readers go?
I: The first fifty on open, paginated after that.
C: So a precomputed list can be bounded. A few hundred entries cover almost every session.
[pause: 0.6]

[slide: v-014]
[pause: 0.6]
C: What content types?
I: Text and images. Video is out of scope.
C: Bodies and media are hydrated separately from the feed. The feed itself only needs to hold references.
[pause: 0.6]

[slide: v-015]
[pause: 0.6]
C: Which is worse: seeing a post twice, or missing one?
I: Missing a close friend's post is worse. A duplicate on screen is a bug.
C: That gives me a correctness stance. De-duplicate always, and treat a missed close-tie post as the failure that matters. Challenge four comes from this answer.
[pause: 0.6]

[slide: v-016]
[pause: 0.6]
C: Functionally, four things. One, publish a post with text and images, visible to followers. Two, read the ranked home feed: the first fifty, then pages with a stable cursor.
C: Three, follow and unfollow, with an effect on the feed. Four, remove: delete a post, block an account, or change who can see a post, and have it gone from every feed within seconds. Each of these gets a numbered flow later.
[pause: 0.8]

[slide: v-017]
[pause: 0.6]
C: Non-functional, with numbers. These are initial targets, not measurements. P-ninety-nine under two hundred milliseconds for the first page. A new post visible to active followers within five seconds at p-ninety-five. Read availability of ninety-nine point nine five percent. Deleted or blocked content gone within five seconds.
C: And one more: a post is never lost. The posts store is the source of truth. Every feed is derived, and can be rebuilt from it.
[pause: 0.8]

[slide: v-018]
[pause: 0.6]
C: In scope: publish, the feed itself, pagination, follow effects, deletes, blocks and audience changes, and ranking as a stage with a budget.
C: Out, on purpose. The ranking model itself. Ads. Media upload and transcoding. Search. Notifications, which is its own question. The social graph's internals, which I'll treat as a service. And like and comment counters, which belong to a separate counter service.
N: An explicit out list scores. Going deep on the ranking model is the classic rabbit hole here.
[pause: 0.8]

[slide: v-019]
[pause: 0.7]
C: So the core is four things. A source of truth for posts. A per-reader view, built by push for most authors and pull for a few. A read path that filters, ranks and hydrates inside two hundred milliseconds. And a rebuild path for when the view is lost, because it will be.
[pause: 1.6]

[pause: 1.4]

## 2 Estimates

[slide: v-020]
[pause: 1.2]
C: Numbers next. Each one comes with its arithmetic and the decision it changes. All of them are illustrative, built from the interviewer's inputs, not measurements.
[pause: 1.8]

[slide: v-021]
[pause: 0.6]
C: Reads. Five hundred million daily users, five opens a day each, over eighty-six thousand four hundred seconds: about twenty-nine thousand feed opens a second on average. With a peak factor of three, about ninety thousand a second.
C: The decision: the feed is served from memory. A database query per open is out from the start.
[pause: 0.8]

[slide: v-022]
[pause: 0.6]
C: Now the cost of computing every feed when it is opened. Ninety thousand opens a second, each merging the recent posts of two hundred followed accounts: eighteen million reads a second on the author indexes.
C: That rules out pure pull at this scale. But at one percent of this scale it is fine, and I'll say so: it is the honest first version.
[pause: 0.8]

[slide: v-023]
[pause: 0.6]
C: Writes. If a tenth of daily users post once a day, that is about five hundred eighty posts a second. Tiny at the source. If each post is copied into two hundred followers' lists, that is about a hundred and twenty thousand inserts a second.
C: Push multiplies writes by two hundred. For ordinary authors that is affordable: an in-memory cluster takes it.
[pause: 0.8]

[slide: v-024]
[pause: 0.6]
C: The cheapest big win. Suppose about half of a typical account's followers haven't opened the app in thirty days. Then half the inserts go to lists nobody reads. Skip them: about sixty thousand a second instead of a hundred and twenty.
C: The fraction is an assumption to measure. The decision holds either way: fan out only to active followers, and rebuild a returning user's feed by pull on their first open.
[pause: 0.8]

[slide: v-025]
[pause: 0.6]
C: Now the number that matters. One celebrity with a hundred and ten million followers posts. At the whole fleet's hundred and twenty thousand inserts a second, that one post takes about nine hundred seconds, fifteen minutes. And every ordinary author posting in that window waits behind it.
V: One celebrity post would be a hundred million writes. That number kills pure push.
[pause: 0.8]

[slide: v-026]
[pause: 1.0]
C: Where does the line go? From both sides. Write side: a ten-thousand-follower post is about eight hundredths of a second of the fleet. A million-follower post is about eight seconds, past the five-second freshness target on its own.
C: Read side: each pulled author costs about half a millisecond per open. Twenty of them, ten milliseconds of the budget. So the line sits around ten to a hundred thousand followers, as a config value I tune with data. Challenge two returns to this.
[pause: 1.0]

[slide: v-027]
[pause: 1.3]
C: Memory. Five hundred million active users, five hundred entries each, sixteen bytes an entry for a post I-D, author I-D and time packed together: four terabytes, twelve with three replicas. That fits a memory tier.
C: If each entry held the post body, about a kilobyte, it would be two hundred and fifty terabytes, sixty times larger. And every edit or delete would chase millions of copies. So the precomputed list holds I-Ds, and bodies are hydrated from one post cache.
[pause: 1.1]

[slide: v-028]
[pause: 1.3]
C: The read budget, as one bar. Lookups and filtering, about twenty milliseconds: the timeline, the celebrity lists, the block set. Ranking gets a hard deadline of eighty. Hydrating fifty posts, about twenty. Network and serialisation, twenty. A hundred and forty used, sixty spare.
C: The decision: ranking gets a deadline and a fallback, because it is the largest piece and it belongs to another team.
[pause: 1.1]

[slide: v-029]
[pause: 0.6]
C: One more, because it shapes a failure path. Lose one cache shard out of a hundred: five million users. If a fifth of them open the app in the next ten minutes, that is about seventeen hundred rebuilds a second, each reading two hundred author indexes: three hundred and forty thousand reads a second on a store sized for something much smaller.
C: So the rebuild path needs coalescing, a rate limit and a degraded mode. That is challenge five.
[pause: 0.8]

[slide: v-030]
[pause: 1.0]
N: Every number on this slide ends in a decision. That is what the estimation phase is graded on.
C: Serve from memory. Precompute for most, with pull as the first version and the rebuild path. Push only to active followers. Pull the celebrities, with a measured line. I-Ds, not bodies. And a deadline for ranking.
[pause: 1.0]

[pause: 1.4]

## 3 Theory

[slide: v-031]
[pause: 1.2]
C: A short theory chapter before the design, so the design can lean on it. Six parts: what a feed is and is not, the properties, the central tension, seven mechanisms, the options, and the failure catalogue.
[pause: 1.8]

[slide: v-032]
[pause: 0.7]
V: A home feed is, for each reader, a bounded, ranked list of recent post I-Ds from the accounts they follow, assembled from a precomputed part and a part fetched at read time, then filtered and hydrated within the read budget.
[pause: 1.0]
C: Each clause carries weight. For each reader: it is a per-user view, so it can be lost and rebuilt. Bounded: a few hundred entries. Post I-Ds: never bodies. Precomputed plus fetched: the hybrid. Filtered: correctness happens at read. Within the budget: two hundred milliseconds, with a fallback.
[pause: 1.6]

[slide: v-033]
[pause: 0.6]
C: Four neighbours. It is not the source of truth: posts are, and the view can be wrong for a few seconds and rebuilt. It is not a chat inbox: an inbox must never lose a message, while a feed may leave out an old post. It is not search: it answers one query shape, and challenge seven asks for a different one. And it is not the ranking model, which is a stage with a budget.
[pause: 0.8]

[slide: v-034]
[pause: 0.6]
V: Safety: a viewer never sees content they must not see for longer than five seconds, and a post is never lost. Liveness: a post reaches active followers within five seconds, every feed open answers within two hundred milliseconds, and a lost timeline is rebuilt on its next open.
[pause: 0.8]
C: Most designs talk only about liveness, about speed. S-one is the safety property people forget: a feed made of copies will show a deleted post unless something stops it. Every fix from here names the property it serves.
[pause: 0.8]

[slide: v-035]
[pause: 1.3]
C: The central tension, as one picture. Push pays at post time, in proportion to the author's followers: the red curve rises as followers grow. Pull pays at read time, in proportion to the reader's followees: per post it is flat and small, but paid on every follower's open.
C: The lines cross near the threshold. Below it push is cheaper; above it pull is. The hybrid simply follows the lower curve. Hold on to this picture: challenges one and two live on it.
[pause: 1.1]

[slide: v-036]
[pause: 0.6]
C: Mechanism one, fan-out on write. It protects freshness and a cheap read. On each post, insert the post I-D, author and time into each active follower's sorted list, trimmed to five hundred, keyed by post I-D so a repeat is a no-op. It rules out a read that touches two hundred authors, and duplicates on re-delivery. It costs a hundred and twenty thousand inserts a second, a memory tier, and amplification on big authors.
[pause: 0.8]

[slide: v-037]
[pause: 0.6]
C: Mechanism two, fan-out on read. It protects the read for celebrities, and recovery. At read time, read each pulled author's recent post I-Ds from a per-author index and merge them. The same path rebuilds a lost timeline. It rules out a hundred million writes for one post, and a lost view staying lost. It costs a merge per read, and author indexes that must be protected from a stampede.
[pause: 0.8]

[slide: v-038]
[pause: 0.6]
C: Mechanism three, the threshold. Each author has a tier: push below the line, pull above, and push to recently active followers in between. The line has hysteresis, so an account near it does not flap, and crossing it needs no backfill. It rules out the celebrity problem, pure pull's read cost, and writes to users who never read. It costs a tier per author, and a number I must defend.
[pause: 0.8]

[slide: v-039]
[pause: 0.6]
C: Mechanism four, I-Ds in the view and hydration through a post cache. It protects deletes, because there is one place to change, and memory. The view holds I-Ds; the read path fetches the top fifty bodies from a post cache. It rules out two hundred and fifty terabytes of copies and edits chasing millions of entries. It costs a multi-get per page, and a post cache that becomes critical.
[pause: 0.8]

[slide: v-040]
[pause: 0.6]
C: Mechanism five, the visibility filter. It protects S-one. Every page drops posts that are deleted or out of audience when it hydrates them, and drops authors in the reader's block, mute and unfollow set when it merges. It rules out a deleted or blocked post surviving in a copy. It costs a small set read on every open.
[pause: 0.8]

[slide: v-041]
[pause: 0.6]
C: Mechanism six, ranking under a deadline. It protects the two hundred milliseconds. Call ranking with a hard deadline; on a miss, order by recency and close ties, and count it. It rules out a slow model making the whole feed slow. It costs lower quality while degraded, which must be measured and owned by someone.
[pause: 0.8]

[slide: v-042]
[pause: 0.6]
C: Mechanism seven, a log with priority lanes. The post and its event commit in one transaction, an outbox. A log keyed by author feeds the workers. Close ties are fanned out first, and the log offset is committed last, so a crash re-delivers rather than loses. It rules out a burst delaying close friends, and lost work. It costs a log to run, and makes lag a metric to watch.
[pause: 0.8]

[slide: v-043]
[pause: 1.0]
C: Six approaches, each with the failure that rules it out. A, pull with a database join: fails at any real scale. B, pull with a per-reader result cache: fine until freshness and the miss rate at peak bite. It is my first version. C, pure push of I-Ds: fails on the first celebrity post. D, pure push of bodies: two hundred and fifty terabytes, and every edit chases copies.
C: E is the hybrid: push I-Ds to active followers of ordinary authors, pull celebrities, hydrate, and filter on read. It fails if the threshold is set once and never measured, and on a reader who follows hundreds of celebrities, which is challenge two. F, buy a managed feed service: it fails on our own ranking and privacy rules, and on cost at a billion users.
V: I pick E, built after B as the first version.
[pause: 1.0]

[slide: v-044]
[pause: 0.6]
C: What the pick gives up, plainly. Strict freshness: a post appears within seconds, not instantly. And simplicity: two paths, a tier per author, and a number I must defend. What it buys: a feed open that costs one memory read and a small merge, writes bounded per post, deletes that are one write, and a view that can be thrown away and rebuilt.
C: And B is not wrong. It is right until the merge on a cache miss breaks the budget at peak. I'd measure that before building E.
[pause: 0.8]

[slide: v-045]
[pause: 1.0]
C: The failure catalogue, which becomes the challenge list. The celebrity post, and bursts. An account crossing the line, and the reader who follows hundreds of celebrities. Deletes and blocks. Duplicates, and a feed that moves while you scroll. A lost shard and the rebuild stampede. A slow ranker. A query the view was not built for. And the feed that works but got worse. Eight challenges, in that order.
[pause: 1.0]

[slide: v-046]
[pause: 1.0]
N: Good theory has a consequence for the design. Every mechanism here names the property it serves and where it returns.
C: That is the vocabulary. On to the A-P-I and the data.
[pause: 1.0]

[pause: 1.4]

## 4 API and entities

[slide: v-047]
[pause: 1.2]
C: The A-P-I next. Each call is tagged with the requirement it serves and the entities it reads or writes.
[pause: 1.8]

[slide: v-048]
[pause: 1.0]
C: Five calls. Post, with an idempotency key so a retried upload doesn't create two posts: it writes the post, the author index and an outbox row in one transaction. Get feed, with a cursor and a limit of fifty: it reads the timeline, the celebrity lists, the block set and the post cache.
C: Follow and unfollow write one edge. Delete a post and block an account write one row each and emit an invalidation event. And internally, rank: I send I-Ds and a deadline, and get scores back. Features stay on the ranking side.
[pause: 1.0]

[slide: v-049]
[pause: 1.0]
C: Publishing on the wire. The client sends the text, media references and audience, with an idempotency key. The answer is a post I-D. The I-D is time-sortable, so timelines can be ordered by I-D alone without another lookup. And a retry with the same key returns the same post, not a second one.
[pause: 1.0]

[slide: v-050]
[pause: 1.0]
C: Reading. Fifty hydrated items and a cursor. The cursor encodes the score and post I-D of the last item shown, so the next page starts strictly after it whatever new posts arrived above. An offset would repeat or skip items; that is challenge four. And a fallback flag says when ranking missed its deadline, which feeds a metric.
[pause: 1.0]

[slide: v-051]
[pause: 1.3]
C: The conceptual model. A user authors posts. Users follow users, many to many, and both directions are queried: who I follow, for reading, and who follows me, for fan-out. Users block or mute users.
C: The timeline entry is a weak entity: it exists only because a user sees a post, and it is derived. Delete every timeline entry and the feed can be rebuilt from posts and follows. That sentence is the whole recovery story.
[pause: 1.1]

[slide: v-052]
[pause: 1.3]
C: Physically. The post table is the source of truth, keyed by the time-sortable post I-D and sharded by it. The author index has one partition per author, newest first: it serves pull, rebuild and catch-up. Follows belong to the graph service.
C: Below, three in-memory structures. The timeline per viewer: a sorted set of at most five hundred I-Ds. The celebrity recent list per author: the last hundred I-Ds, replicated to many cache nodes. And the block set per viewer, small, read on every open.
[pause: 1.1]

[slide: v-053]
[pause: 1.0]
C: In one table. Three stores of truth: posts, the author index, and the graph. Three derived stores: timelines, celebrity lists, and the post cache. Anything derived can be lost and rebuilt. Anything true must be durable and replicated.
N: Naming truth and derived before the interviewer asks about failures is the recovery plan, said early.
[pause: 1.0]

[pause: 1.4]

## 5 High-level design

[slide: v-054]
[pause: 1.2]
C: The design, in three versions. Each version answers the objection to the one before. The boxes never move: every later picture is a view of the same baseline.
[pause: 1.8]

[slide: v-055]
[pause: 1.3]
C: Version one. On the top row, the write path: the author posts, the post service writes the post and its author index in one transaction. On the bottom, the read path: the reader opens the app, the feed service asks the graph for the followees and the block set, reads the recent posts of two hundred authors from the author indexes, merges, sends the candidates to ranking, and returns fifty.
C: That is the honest first version. At one percent of this scale, with a short per-reader result cache, it works.
[pause: 1.1]

[slide: v-056]
[pause: 0.6]
C: The objection to version one. Every cache miss is a two-hundred-way merge, and at peak that is eighteen million author-index reads a second. And a cached result is up to a minute old, so a close friend's post waits.
C: The read must become one memory lookup. That means doing the work when a post is written.
[pause: 0.8]

[slide: v-057]
[pause: 1.3]
C: Version two, push. New boxes are outlined in blue. The post service still writes one transaction, now with an outbox row. A relay carries it to the event log, keyed by author. Fan-out workers read the event, page through the author's followers from the graph, skip the inactive ones, and insert the post I-D into each follower's timeline.
C: The read path becomes: read my timeline, about five hundred I-Ds, rank, and hydrate the top fifty from the post cache. One memory read and a multi-get.
[pause: 1.1]

[slide: v-058]
[pause: 1.0]
C: The technology, each against its rivals. Timelines in memory, as a sorted set per viewer, rather than a table: they are read-dominated, bounded and rebuildable, so memory is the right price. Posts in a sharded store with time-sortable keys, and a per-author index. The transport is an outbox and a partitioned log rather than a direct call, so there is no dual write, the work is replayable, and other consumers like search can read the same events. And the graph is a service, because both directions are queried constantly.
[pause: 1.0]

[slide: v-059]
[pause: 1.0]
C: The worker in code, because here the code is the mechanism. One branch per tier. A pulled author gets one write to their recent list. Otherwise, page through followers a thousand at a time, keep only the active ones, and for the mid tier only those active in the last day. Add the post I-D to each timeline, trimmed to five hundred. And commit the log offset last, so a crash re-delivers the event instead of losing it. Re-delivery is safe because the timeline is keyed by post I-D.
[pause: 1.0]

[slide: v-060]
[pause: 0.6]
C: The objection to version two has three parts. One celebrity post holds the whole fan-out fleet for fifteen minutes. About half the inserts go to users who won't open the app this month. And a deleted post now sits in millions of timelines.
C: The tail of authors decides the design, and correctness cannot live in copies.
[pause: 0.8]

[slide: v-061]
[pause: 1.3]
C: Version three. The new box is the celebrity posts cache. Above the threshold, the fan-out worker does not fan out at all: it writes one entry to the author's recent list, the dashed purple arrow. On the read path, the feed service merges my timeline with the lists of the few celebrities I follow.
C: Three more changes that do not add boxes. Fan-out goes only to active followers. The feed service filters every page against the post's status and my block set. And ranking is called with a deadline, with a fallback.
[pause: 1.1]

[slide: v-062]
[pause: 1.3]
C: The publish flow for an ordinary author with two thousand followers, by the numbers. One, the author posts. Two, one transaction writes the post, the author index and the outbox row. Three, the relay publishes the event. Four, a worker consumes it: tier push.
C: Five, it pages through the followers from the graph. Six, it inserts the I-D into each active follower's timeline and trims to five hundred. The offset is committed after that.
[pause: 1.1]

[slide: v-063]
[pause: 1.3]
C: The same flow for a celebrity. Steps one to four are identical. Step five is different: one append to the author's recent list. No fan-out. The log partition is free again in milliseconds.
[pause: 1.1]

[slide: v-064]
[pause: 1.3]
C: As a sequence. The post service writes post, author index and outbox row together, and answers two-oh-one. Only then does the relay publish the event, keyed by author. The worker pages through followers, skips the inactive, inserts and trims, and commits its offset last. Nothing the client waits for depends on fan-out.
[pause: 1.1]

[slide: v-065]
[pause: 1.3]
C: The read flow. One, get feed. Two, read my timeline, about five hundred I-Ds. Three, merge the recent lists of the celebrities I follow. Four, the graph gives me my block and mute set, and the merge drops those authors.
C: Five, the top two hundred by recency go to ranking with an eighty millisecond deadline. Six, the top fifty are hydrated by multi-get from the post cache, which drops anything deleted. Seven, fifty items and a cursor go back.
[pause: 1.1]

[slide: v-066]
[pause: 1.0]
C: The read path in code. Read the timeline. Add the recent lists of followed celebrities, a handful. Drop blocked authors, de-duplicate, keep the top two hundred by time. Score them with an eighty millisecond deadline, or fall back. Take the page after the cursor. Hydrate, and drop anything not visible to this viewer: deleted, or out of its audience. Return the page and the next cursor.
[pause: 1.0]

[slide: v-067]
[pause: 1.3]
C: The same read as a sequence, with times. Timeline, five milliseconds. Celebrity lists, five. Merge, de-duplicate and filter. Score two hundred with an eighty millisecond deadline. Multi-get fifty, about twenty. Drop anything deleted. Fifty items and a cursor.
[pause: 1.1]

[slide: v-068]
[pause: 1.3]
C: Follow. One, the request. Two, one edge is written in the graph. Three: nothing is backfilled. If the new followee is a celebrity, the next read's merge already includes them. If they are ordinary, their next post arrives by fan-out. Optionally I'd insert their last few posts so the follow feels immediate. Unfollow adds the author to my filter set.
[pause: 1.1]

[slide: v-069]
[pause: 1.3]
C: Remove. One and two, the delete writes the post's status, once. Three, an invalidation event drops the post from the cache. Four and five, the next read hydrates the page, sees the status, and drops the I-D. The I-Ds still sitting in timelines are harmless, and a background job removes them later.
[pause: 1.1]

[slide: v-070]
[pause: 1.3]
C: Now the same system in C4 terms, for the detail. The context: authors post, about six hundred a second. Readers open the feed, about ninety thousand a second at peak. The feed system depends on two systems owned by other teams, ranking with an eighty millisecond budget and the social graph, and media is served from a C-D-N, out of scope.
[pause: 1.1]

[slide: v-071]
[pause: 1.3]
C: The containers. Across the top, the write path: post service, posts database, event log, fan-out workers. In the middle, three in-memory stores: the post cache, the celebrity lists, and the timelines. At the bottom, the feed service, stateless, which merges, filters, ranks under a deadline, hydrates, and writes the cursor. The graph and ranking sit outside, as dependencies with contracts.
[pause: 1.1]

[slide: v-072]
[pause: 1.3]
C: Back to the budget, now with every box named. Lookups and filtering, twenty milliseconds. Ranking, eighty, as a hard deadline. Hydration, twenty. Network, twenty. A hundred and forty used, sixty spare. The spare is not slack: it is what a slow cache shard or a garbage-collection pause eats.
[pause: 1.1]

[slide: v-073]
[pause: 1.0]
C: Version three works end to end. What it still owes are the details, and each one is a challenge. What exactly happens on a celebrity post. Where the line is. How a deleted post disappears. Duplicates and pagination. A lost shard. A slow ranker. A new kind of query. And how we would know any of it went wrong.
[pause: 1.0]

[pause: 1.4]

## 6 Bridge

[slide: v-074]
[pause: 1.2]
V: It works. The question now is where it breaks first.
[pause: 1.8]

[slide: v-075]
[pause: 1.3]
C: The baseline with the attack points marked in red. The fan-out workers, for the celebrity and for bursts. The celebrity lists and the timelines, for the threshold, for duplicates and for a lost shard. The feed service, for deletes and pagination. And ranking, for its deadline. Then a new kind of query, and the question of how we'd know. Eight challenges, in an order where each fix creates the next question.
[pause: 1.1]

[pause: 1.4]

## 7 Challenges

[slide: v-076]
[pause: 1.2]
C: Each challenge runs the same way: the question, the naive answer, a case with numbers, where it breaks, the fix, why it works, then the interviewer pushes on the fix itself, and I say what I'd say in the room.
[pause: 1.8]

[pause: 1.4]

## 7.1 Challenge 1: The celebrity post

[slide: v-077]
[pause: 1.2]
N: Challenge one, the crux. Someone with a hundred million followers posts: what happens, write by write?
[pause: 1.8]

[slide: v-078]
[pause: 0.6]
I: Someone with a hundred million followers posts. Walk me through it.
[pause: 2.0]

[slide: v-079]
[pause: 1.3]
C: The naive answer: the workers push it to every follower, and if that is slow we add workers. Look at the red: the fan-out workers and the arrows into the timelines. One post becomes a hundred million inserts, and the log partition holding it is blocked until they finish.
[pause: 1.1]

[slide: v-080]
[pause: 1.0]
C: The trace. At eight o'clock a star with a hundred and ten million followers posts. At the whole fleet's hundred and twenty thousand inserts a second, that takes about fifteen minutes. Thirty seconds later, Ana posts to her three hundred friends, and her event waits behind the star's. Her friends see it fourteen minutes late. And the star posts again at half past.
C: Illustrative numbers, but the shape holds at any fleet size. Even ten times the capacity spends ninety seconds of all of it on one post.
[pause: 1.0]

[slide: v-081]
[pause: 1.3]
C: The fix. The event carries the author's tier. Above the threshold the worker writes one entry to that author's recent list, the dashed arrow, and is done. On the read path, the feed service merges the recent lists of the celebrities this reader follows. One write instead of a hundred and ten million.
[pause: 1.1]

[slide: v-082]
[pause: 1.3]
C: As a sequence. The star's event arrives with tier pull. The worker appends the post I-D to the star's list: one write. The partition is free again in milliseconds. Later, a reader opens the feed. The feed service reads the lists of the six celebrities this reader follows, merges them with the timeline, and de-duplicates by post I-D. One ranked feed.
[pause: 1.1]

[slide: v-083]
[pause: 1.0]
C: Why it works, in one table. Pushing the celebrity costs a hundred and ten million inserts per post, paid by every other author in delay. Pulling costs one write per post, and one small cache read per followed celebrity per open, paid by the reader inside the budget. Those celebrity lists are hot keys, so they are replicated to many cache nodes.
[pause: 1.0]

[slide: v-084]
[pause: 0.6]
I: New Year's Eve. Ten times the normal posting rate, all ordinary accounts, for ten minutes.
[pause: 2.0]

[slide: v-085]
[pause: 0.6]
C: A burst of ordinary posts is a different problem: no single author is the issue, the volume is. Three things. Priority lanes: fan out to close-tie followers first, the rest after. Partitioning by author, so the burst spreads across the fleet. And lag measured per lane, so that while the general lane is behind, the read merge can pull recent posts from a reader's top ties.
C: The honest limit: for those ten minutes, the general one-minute target may slip. Close friends keep their seconds.
[pause: 0.8]

[slide: v-086]
[pause: 0.7]
V: If asked, I'd say: one celebrity post would be a hundred million writes, minutes of fan-out that block everyone else. So above a follower threshold I don't fan out at all. The post goes into a small recent-posts list for that author, and each reader merges the few celebrities they follow at read time. That costs a few milliseconds per open, which I've budgeted.
[pause: 1.0]
N: That fix creates the next question: where exactly is the threshold?
[pause: 1.6]

[pause: 1.4]

## 7.2 Challenge 2: Where is the line, and who crosses it?

[slide: v-087]
[pause: 1.2]
N: Challenge two, the second half of the crux. Where exactly is the line, and what happens to an account that crosses it overnight?
[pause: 1.8]

[slide: v-088]
[pause: 0.6]
I: Where exactly is the threshold, and what happens to an account that crosses it?
[pause: 2.0]

[slide: v-089]
[pause: 1.3]
C: The naive answer is a round number: a million followers. Look at the fan-out box and both of its outputs in red. The routing decision rests on a number with no arithmetic behind it, and no rule for what happens when an account crosses it.
[pause: 1.1]

[slide: v-090]
[pause: 1.0]
C: Three ways a fixed number fails. At a million followers, one post is a million inserts, about eight seconds of the whole fleet, past the five-second target by itself. Then an account goes viral: nine thousand followers on Monday, two million on Tuesday, with two hundred posts already pushed. Which tier now, and what about the copies? And a power reader follows five thousand accounts, three hundred of them celebrities: three hundred lists at half a millisecond each is a hundred and fifty milliseconds.
[pause: 1.0]

[slide: v-091]
[pause: 1.0]
C: The fix: derive the line from both sides, and use three tiers. Push for authors under about ten thousand followers, to every follower active in thirty days. A mid tier up to about a hundred thousand, pushed only to followers active in the last day, which cuts the cost by an order of magnitude. And pull above that.
C: The write side says one post's fan-out must finish well inside five seconds on a fair share of the fleet. The read side says the average reader should pull fewer than about twenty authors. Start at ten thousand, measure, tune. It is a config value, not a constant.
[pause: 1.0]

[slide: v-092]
[pause: 1.3]
C: Crossing, as a sequence. A tier job reads follower counts hourly. Up at a hundred thousand, down only below fifty thousand, so an account near the line does not flap. The new star is marked pull. Its new posts become one write each. Yesterday's pushed I-Ds stay in timelines and age out: no backfill, no removal. And readers' merge shows the new posts from the first minute. Crossing down works the same way in reverse.
[pause: 1.1]

[slide: v-093]
[pause: 1.3]
C: Why it works, on the baseline. L-one and L-two both hold at the line, because the line was placed where both costs are acceptable. And no transition needs a backfill, because the read path's merge covers the gap: whichever tier an author is in today, their recent posts are reachable.
[pause: 1.1]

[slide: v-094]
[pause: 0.6]
I: The power reader. Three hundred celebrities on every open.
[pause: 2.0]

[slide: v-095]
[pause: 0.6]
C: The power reader is the tail of readers, and gets the same treatment as the tail of authors. For readers who pull more than about fifty authors, a background job merges their celebrity lists every few minutes into their timeline, so their open is one read again. At read time, the live merge is capped at the top fifty celebrities by interaction.
C: The honest limit: for those readers, a celebrity's post may be a few minutes late. I'd say that to product.
[pause: 0.8]

[slide: v-096]
[pause: 0.7]
V: If asked, I'd say: I set the line from both sides. One post's fan-out must finish inside the freshness target, and the average reader should pull only a handful of authors. That puts it around ten thousand followers, as a config value I'd tune with data. Crossing it needs no backfill, because the read merge covers recent posts. And the rare reader who follows hundreds of celebrities gets their merge precomputed.
[pause: 1.0]
N: The pull path now carries correctness weight. Next question: what about posts that must disappear?
[pause: 1.6]

[pause: 1.4]

## 7.3 Challenge 3: Delete, block, unfollow

[slide: v-097]
[pause: 1.2]
N: Challenge three. A post is deleted, or an author is blocked, while its I-D sits in millions of timelines: how does it disappear?
[pause: 1.8]

[slide: v-098]
[pause: 0.6]
I: A user deletes a post, or blocks someone. That post I-D is already in millions of timelines. How does it disappear?
[pause: 2.0]

[slide: v-099]
[pause: 1.3]
C: The naive answer: fan out a delete, removing the I-D from every timeline that has it. Look at the timeline cache in red. The I-D was copied millions of times, and the delete has to chase every copy, at the same cost as the post, racing it.
[pause: 1.1]

[slide: v-100]
[pause: 1.0]
C: The trace. Ana posts to three million followers and fan-out starts. Forty seconds later she deletes it, a wrong photo, and a delete fan-out starts behind it. Wherever the insert lands after the delete, the post stays. Separately, Ben blocks Cal, and five hundred of Cal's posts are already in Ben's timeline. Both violate S-one.
[pause: 1.0]

[slide: v-101]
[pause: 1.3]
C: The fix. Correctness lives on the read path. The delete writes the post's status once, and an invalidation event drops it from the post cache, the dashed arrow. Every page is hydrated through that cache, and anything deleted or out of audience is dropped. The merge drops authors in my block, mute and unfollow set, which the graph keeps small and cached. A background job removes stale I-Ds from timelines later, and that cleanup is cosmetic.
[pause: 1.1]

[slide: v-102]
[pause: 1.3]
C: As a sequence. The author deletes: one write, status deleted. The post cache is invalidated. A reader opens the feed: the merge drops authors they block or unfollowed. Hydration misses the cache, finds the row says deleted, and drops it. Later, a cleanup job removes stale I-Ds. The user never depended on it.
[pause: 1.1]

[slide: v-103]
[pause: 0.6]
I: The post-cache invalidation event is lost.
[pause: 2.0]

[slide: v-104]
[pause: 0.6]
C: Two backstops. Post-cache entries have a lifetime of at most five minutes, so a lost event costs one lifetime, not forever. And deletes and audience changes also write a small recently-removed set, which hydration checks for an hour. That keeps the five-second bound even when the event is lost.
C: The honest limit: a post already rendered on someone's phone stays there until they refresh. The next fetch removes it.
[pause: 0.8]

[slide: v-105]
[pause: 0.7]
V: If asked, I'd say: fanned-out I-Ds are copies, so I don't trust them. Every page is hydrated from the post itself and filtered by the reader's block and unfollow set, so a delete is one write that takes effect within seconds everywhere. Cleaning the I-Ds out of timelines is a background job, and it's cosmetic.
[pause: 1.0]
N: If correctness lives on the read path, the read path must also handle duplicates. Next.
[pause: 1.6]

[pause: 1.4]

## 7.4 Challenge 4: Twice, or never

[slide: v-106]
[pause: 1.2]
N: Challenge four. The interviewer said a duplicate is a bug and a missed close-friend post is worse: where does each come from?
[pause: 1.8]

[slide: v-107]
[pause: 0.6]
I: You said a duplicate on screen is a bug, and a missed close-friend post is worse. Where does each come from in your design?
[pause: 2.0]

[slide: v-108]
[pause: 1.3]
C: The naive answer: the log delivers exactly once. It doesn't; it delivers at least once. Two places break, in red: the insert into the timeline, on re-delivery, and the page boundary on the way back to the reader.
[pause: 1.1]

[slide: v-109]
[pause: 1.0]
C: The trace. Worker three inserts post nine into a thousand timelines and crashes before committing its offset. Worker seven re-reads the event and inserts it again. In a plain list, post nine is there twice. Separately: a reader takes page one with offset zero, twelve new posts arrive at the top, and page two with offset fifty returns items the reader already saw. Twelve repeated, and twelve others never shown.
[pause: 1.0]

[slide: v-110]
[pause: 1.0]
C: The fix is two small things. The timeline is a sorted set keyed by post I-D, so a re-delivered insert changes nothing: at-least-once delivery, with an idempotent effect. And pagination uses a cursor holding the last item's score and I-D. The next page is everything strictly after that pair, whatever arrived at the top. The read merge also de-duplicates across the timeline and the celebrity lists.
C: Duplicates become impossible by data structure. Misses are bounded by fan-out lag, which I measure, and for close ties the pull covers a lagging lane.
[pause: 1.0]

[slide: v-111]
[pause: 1.3]
C: As a sequence. Worker three inserts and crashes. Worker seven inserts the same post again: the set is keyed by post I-D, no change. The reader asks for the next page with a cursor holding score point eight two and post fifty-one, and gets the next fifty strictly after it.
[pause: 1.1]

[slide: v-112]
[pause: 0.6]
I: Ranking reorders things between page one and page two.
[pause: 2.0]

[slide: v-113]
[pause: 0.6]
C: If ranking reorders between pages, scores in the cursor stop meaning anything. So the first page's ranked candidate list, a few hundred I-Ds, is kept for the session with a short lifetime, and later pages walk that list instead of re-ranking. New posts appear on refresh, which starts a new session. That is the expected behaviour, and I'd say so.
[pause: 0.8]

[slide: v-114]
[pause: 0.7]
V: If asked, I'd say: fan-out is at-least-once, so inserts are idempotent: the timeline is keyed by post I-D. Pagination uses a cursor holding the last item's score and I-D, never an offset. And the ranked list for a session is kept, so page two doesn't reshuffle page one.
[pause: 1.0]
N: All of this assumes the timeline exists. Next: what if it doesn't?
[pause: 1.6]

[pause: 1.4]

## 7.5 Challenge 5: A timeline shard is gone

[slide: v-115]
[pause: 1.2]
N: Challenge five. A cache shard holding five million timelines disappears on a Sunday evening: what do those users see, and what stops the recovery from becoming the outage?
[pause: 1.8]

[slide: v-116]
[pause: 0.6]
I: A timeline cache shard is lost. One user in a hundred opens to an empty feed. What do they see, and how do you recover?
[pause: 2.0]

[slide: v-117]
[pause: 1.3]
C: The naive answer: restore the shard from a backup. A backup of a cache is hours old and slow to load, and meanwhile users open the app. Look at the red: the timeline is gone, and the obvious recovery, rebuilding by pull, lands on the author indexes, which everyone's celebrity merge also depends on.
[pause: 1.1]

[slide: v-118]
[pause: 1.0]
C: The trace. At eight, a shard with five million users' timelines is lost. A fifth of them open within ten minutes: seventeen hundred rebuilds a second, each reading two hundred author indexes, three hundred and forty thousand reads a second. The author index p-ninety-nine goes from five milliseconds to four hundred. And every reader's celebrity merge waits on that same store. One lost shard has become everyone's outage.
[pause: 1.0]

[slide: v-119]
[pause: 1.3]
C: The fix. A timeline miss triggers a rebuild through the pull path, the same code as version one, and writes the result back. The new rebuild box. Requests are coalesced, so one user tapping three times starts one rebuild. A global rate limit caps the load on the author indexes. And anyone over the limit gets a degraded feed immediately: their celebrities plus the recent posts of their top twenty followees by interaction, marked for a full rebuild later.
[pause: 1.1]

[slide: v-120]
[pause: 1.3]
C: As a sequence. The reader opens the feed, the timeline is empty, the shard is lost. The feed service asks the limiter for a rebuild token, one in flight per user. With a token: read the followees' recent posts, merge, write the timeline back. Without one: a degraded feed right now, celebrities and top twenty followees.
[pause: 1.1]

[slide: v-121]
[pause: 1.3]
C: Why it works, as a curve. Unlimited, rebuilds spike to seventeen hundred a second and the author indexes fall over. Limited to five hundred a second, a hundred thousand reads a second, the store stays healthy, the rebuilds take longer, and the users waiting get a degraded but instant feed. The limit, not the number of users, decides the blast radius.
[pause: 1.1]

[slide: v-122]
[pause: 0.6]
I: It's not a shard. It's the whole timeline cluster in one region.
[pause: 2.0]

[slide: v-123]
[pause: 0.6]
C: A whole cluster in one region. Serve that region's reads from another region's timeline replica, a few seconds stale, while the local one warms. Without a replica, the degraded feed for everyone. Then rebuild at the rate limit, most active users first.
C: The honest limit: a cold region takes hours to warm fully. That is a recovery time I'd write down, and the business case for cross-region replicas of the timeline tier.
[pause: 0.8]

[slide: v-124]
[pause: 0.7]
V: If asked, I'd say: a timeline is a derived view, so losing it is a latency problem, not data loss. The first open rebuilds it by pull, with coalescing per user and a rate limit, and anyone over the limit gets a degraded but instant feed. The rate limit is what stops one lost shard from overloading the author index for everyone.
[pause: 1.0]
N: The degraded feed skipped one stage on purpose. Next: what if that stage is the slow one?
[pause: 1.6]

[pause: 1.4]

## 7.6 Challenge 6: The ranker takes 300 ms

[slide: v-125]
[pause: 1.2]
N: Challenge six. The biggest piece of the read budget belongs to another team, and today it is slow.
[pause: 1.8]

[slide: v-126]
[pause: 0.6]
I: Ranking has eighty milliseconds of your budget. Today it takes three hundred. What's your plan? And the ranking team wants a hundred and twenty for a better model.
[pause: 2.0]

[slide: v-127]
[pause: 1.3]
C: The naive answer: wait for it, because quality matters. Look at the arrow into ranking, in red. If the feed waits, the feed's latency is ranking's latency, and ranking belongs to another team with another release schedule.
[pause: 1.1]

[slide: v-128]
[pause: 1.0]
C: The trace. At two, ranking ships a new model and its p-ninety-nine goes from seventy to three hundred milliseconds. The feed's p-ninety-nine goes from a hundred and sixty to four hundred and twenty. Open rate drops, and nothing in the feed service changed. Separately, the ranking team's next model lifts engagement, but needs a hundred and twenty milliseconds.
[pause: 1.0]

[slide: v-129]
[pause: 1.3]
C: The fix, on both boxes. The feed service calls ranking with a deadline of eighty milliseconds. On a miss, it orders by recency plus close ties, or reuses this session's last ranking. Late scores are dropped and counted, and the response carries the fallback flag. The feed degrades instead of failing.
[pause: 1.1]

[slide: v-130]
[pause: 1.3]
C: As a sequence. Score two hundred, deadline eighty. Eighty milliseconds pass with no answer. Fallback: recency plus close ties. Hydrate the top fifty. The feed returns in a hundred and forty milliseconds, flagged fallback. When ranking's late answer arrives, it is dropped and counted.
[pause: 1.1]

[slide: v-131]
[pause: 1.0]
C: Now the hundred and twenty milliseconds. I wouldn't move the user's deadline. Options, each with a cost. Pre-rank on app background or prefetch, so the slow model runs before the open: costs compute on opens that never happen. Rank the first twenty fast and the rest asynchronously: a two-stage contract. Or find forty milliseconds elsewhere in the budget first.
N: Negotiating a shared budget with options and costs is the signal here.
[pause: 1.0]

[slide: v-132]
[pause: 0.6]
I: The fallback rate is thirty percent for a week, and nobody noticed.
[pause: 2.0]

[slide: v-133]
[pause: 0.6]
C: A fallback is only safe if someone notices it. The fallback rate becomes ranking's service level indicator, with an error budget, say under one percent of opens, and ranking is paged on it. And a model push that breaks that budget on its canary is rolled back automatically.
C: That is a metric about quality, not uptime. Challenge eight is about exactly that.
[pause: 0.8]

[slide: v-134]
[pause: 0.7]
V: If asked, I'd say: ranking gets a hard deadline inside the two hundred milliseconds. If it misses, I rank by recency and close ties, so the feed degrades instead of failing. For a slower model, I'd find the budget by pre-ranking before the open, not by moving the user's deadline. And the fallback rate is a number someone owns.
[pause: 1.0]
N: So far the feed answered its one query. Next: product asks a different one.
[pause: 1.6]

[pause: 1.4]

## 7.7 Challenge 7: Catch up on the last 48 hours

[slide: v-135]
[pause: 1.2]
N: Challenge seven, a new requirement mid-round. Product wants a chronological view of everything from the last two days: does the design absorb it?
[pause: 1.8]

[slide: v-136]
[pause: 0.6]
I: Product adds catch up: a chronological view of everything from the last forty-eight hours, for any user. What changes?
[pause: 2.0]

[slide: v-137]
[pause: 1.3]
C: The naive answer: make the timelines longer and keep them in time order. Look at the timeline in red. It is bounded at five hundred, it is ranked, it never held the celebrities, and inactive users were skipped by fan-out. It doesn't hold the answer, and stretching it doubles the memory bill for everyone.
[pause: 1.1]

[slide: v-138]
[pause: 1.0]
C: The case, as a table. Catch-up needs every post from my followees in forty-eight hours, perhaps two thousand. The timeline holds at most five hundred. It needs time order; the timeline is ranked. It needs celebrities; they were never in it. And a returning user has no timeline at all.
[pause: 1.0]

[slide: v-139]
[pause: 1.3]
C: The fix: go to the source of truth. Catch-up merges the followees' author indexes for the window, the green arrow from the feed service to the posts store. It is the same pull path as the rebuild. In time order, paginated by time and post I-D, filtered by the same visibility rules, and cached per user for ten minutes. The ranked feed is untouched.
[pause: 1.1]

[slide: v-140]
[pause: 1.3]
C: As a sequence. Get catch-up for forty-eight hours. Is there a cached result for this user? A miss. For each followee, posts since forty-eight hours ago, the rebuild path. Merge by time, filter, page by time and I-D. Store for ten minutes. Return the first fifty and a cursor.
[pause: 1.1]

[slide: v-141]
[pause: 0.6]
I: It becomes the most used screen.
[pause: 2.0]

[slide: v-142]
[pause: 0.6]
C: If catch-up becomes the most used screen, it earns its own materialised view: a per-user chronological list maintained by the same fan-out event, I-Ds only, with a forty-eight hour lifetime, and celebrities merged at read as before. Its price, said first: it roughly doubles timeline memory for the users who use it. I'd measure the load on the author indexes before paying it.
C: Either way, the design absorbed the requirement with a new reader of the same data, not a rebuild.
[pause: 0.8]

[slide: v-143]
[pause: 0.7]
V: If asked, I'd say: I wouldn't distort the ranked timeline for a query it wasn't designed for. Catch-up reads the source of truth, the followees' author indexes for the window, through the same path I use for rebuilds, and caches the result for minutes. If it becomes popular, it gets its own small view, and I'd say what that costs first.
[pause: 1.0]
N: Last challenge, and always the last one: how would you know any of this broke?
[pause: 1.6]

[pause: 1.4]

## 7.8 Challenge 8: How would you know the feed got worse?

[slide: v-144]
[pause: 1.2]
N: Challenge eight. The feed is up and fast. How would you know it had silently got worse?
[pause: 1.8]

[slide: v-145]
[pause: 0.6]
I: The feed is up and fast. How would you know it had silently got worse?
[pause: 2.0]

[slide: v-146]
[pause: 1.3]
C: The naive answer: error rate and latency. Both measure boxes. The promise to the user is different: your friends' posts show up within seconds, and the feed is good. A routing bug in the fan-out box, in red, can break that promise with every box green.
[pause: 1.1]

[slide: v-147]
[pause: 1.0]
C: The trace. A change to the tier job marks thirty percent of mid-tier authors as pull, by mistake. No errors. Latency unchanged. Their posts now reach followers only through the read merge, and the merge lists only true celebrities, so they are never shown. Engagement drifts down two percent over a week, and a product manager is the one who notices.
[pause: 1.0]

[slide: v-148]
[pause: 1.3]
C: The fix. Measure the promise. Synthetic authors, one in every tier, post every minute through the real path. Synthetic followers open the feed and time the post's arrival. That is the freshness indicator, per tier, with a target of five seconds at p-ninety-five. In this case, the mid-tier probe stops arriving within minutes of the change.
[pause: 1.1]

[slide: v-149]
[pause: 1.3]
C: As a sequence. The synthetic author posts, one per tier. Fan-out delivers it by the real path. The synthetic follower opens the feed every five seconds until the post appears, and reports post-to-visible time per tier. Mid tier not visible after five minutes: page, with the tier named.
[pause: 1.1]

[slide: v-150]
[pause: 1.0]
C: Then read metrics in pairs. Fan-out lag up with the post rate flat: workers are slow, not traffic. Freshness bad for one tier with lag flat: a routing bug, this case. Fallback up with ranking's latency normal: a misconfigured deadline. Author-index reads up with the timeline hit rate down: a rebuild wave. Engagement down with everything else normal: a model change, and ranking's to own.
C: And quality metrics, not uptime: empty-feed rate, fallback rate, the share of items from close ties, and engagement per session against its seasonal baseline.
[pause: 1.0]

[slide: v-151]
[pause: 0.6]
I: Finance says the timeline tier's memory bill doubled while users grew ten percent.
[pause: 2.0]

[slide: v-152]
[pause: 1.0]
C: Cost is observable too. Memory per active user, the share of inserts going to inactive users, and entries per timeline. Usually something drifted: the bound crept up, the active cut-off was widened, or the mid tier is pushing to everyone. Find what grew, then pull the lever. Five hundred entries to three hundred saves forty percent of memory if nobody scrolls that far. Don't buy a bigger cluster first.
[pause: 1.0]

[slide: v-153]
[pause: 0.7]
V: If asked, I'd say: I measure the promise, not the servers. Synthetic accounts in every tier post and read every minute, so I know post-to-visible time per tier. Then quality signals, empty feeds, ranking fallbacks, engagement against its baseline, catch the feed that works but got worse. And I read metrics in pairs to find the cause.
[pause: 1.6]

[pause: 1.4]

## 8 Build cost

[slide: v-154]
[pause: 1.2]
C: The build cost. This is the manager layer, marked auxiliary: a Staff candidate can skip it, an engineering manager should not.
[pause: 1.8]

[slide: v-155]
[pause: 1.0]
C: Sequenced by measured load. The first version is pull with a per-reader cache: about four engineers, one quarter. It is right until the merge on a miss breaks the budget. Then push: two teams, a quarter. Then the hybrid, the filter, the deadline, the rebuild path and the probes: two or three teams, two quarters. Illustrative numbers; the order is the point.
[pause: 1.0]

[slide: v-156]
[pause: 1.0]
C: The migration from pull to push, with no downtime. Weeks one to four, build fan-out and timelines beside the pull path, read by nothing. Weeks five to eight, shadow: write timelines, keep serving pull, and compare the two feeds per user. Weeks nine to eleven, switch by cohort, one percent, ten, fifty, all, with rollback by cohort. Then pull stays, as the rebuild and catch-up path.
[pause: 1.0]

[slide: v-157]
[pause: 0.6]
C: Three teams along the data. Publish and graph, owning the post-created event. Fan-out and timelines, owning the timeline entry format. Feed serving, owning the rank call with its deadline. On-call is on freshness and feed latency, and ranking's fallback rate pages the ranking team.
[pause: 0.8]

[slide: v-158]
[pause: 1.0]
C: Money. Two lines dominate: timeline memory, about twelve terabytes of RAM with replicas, and fan-out writes. The biggest lever on both is skipping inactive users, roughly half. Then the threshold and the timeline bound.
C: The top risks: a threshold set once and never measured, a rebuild path never load-tested, and ranking's budget renegotiated every release instead of owned.
[pause: 1.0]

[pause: 1.4]

## 9 Recap

[slide: v-159]
[pause: 1.2]
C: The recap. One picture, a sentence per path, the common mistakes, and the thesis.
[pause: 1.8]

[slide: v-160]
[pause: 1.3]
C: The final design on the baseline. The write path along the top: post service, one transaction, the event log, fan-out by tier. In the middle, the graph, the celebrity lists and the timelines. Along the bottom, the feed service, ranking with a deadline and the post cache. And the parts that only show up when something goes wrong: invalidation, the rebuild path, catch-up, and the synthetic users that tell us the promise holds.
[pause: 1.1]

[slide: v-161]
[pause: 1.0]
C: Four paths, one sentence each. Publish: one transaction and an event, then push I-Ds to active followers, or one write for a celebrity. Read: one timeline and a few celebrity lists, filtered, ranked under a deadline, fifty hydrated, and a cursor. Remove: one write to the post, enforced on every page. Rebuild: pull, coalesced and rate-limited, degraded beyond the limit.
[pause: 1.0]

[slide: v-162]
[pause: 0.6]
C: The common mistakes. Picking push or pull and defending it. Bodies in timelines. No number on the threshold. Strong consistency for a feed. Chasing deletes into copies, offsets for pagination, and exactly-once fan-out. Ranking with no deadline, no plan for a lost shard, and watching uptime instead of freshness. And going deep on the ranking model, or never asking about the follower distribution.
[pause: 0.8]

[slide: v-163]
[pause: 1.0]
C: The eight challenges in a phrase each. Pull the celebrity. Set the line from both sides. Filter on read. Idempotent inserts and a cursor. Rebuild by pull, limited and degraded. A deadline with an owner. The source of truth for a new query. And probes that measure the promise.
[pause: 1.0]

[slide: v-164]
[pause: 0.7]
V: It's a hybrid: post I-Ds pushed into bounded timelines for ordinary accounts, celebrities pulled at read time, with the line set by arithmetic and tuned with data. Correctness lives on the read path, so a delete is one write. I traded strict freshness for seconds of eventual consistency, and every degraded mode, slow ranking or a lost shard, has a fallback and a metric.
[pause: 2.0]
