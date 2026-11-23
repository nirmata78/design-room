# SD-08 News feed / home timeline: reference solution (Staff L6/L7)

<!-- Video script for slide-video-kit/scripts/build_video.py. [slide: v-NNN] = frames/v-NNN.png; [reveal: v-NNN] = the next
     reveal step of the same slide. Generated from src/*.py: edit the sources, not this file. -->
<!-- voices: N=af_heart@0.92 I=bf_emma@0.95 C=am_michael@0.9 V=am_michael@0.84 -->
<!-- names: C=Candidate V=Candidate N=Coach I=Interviewer -->
<!-- say: SLO=S-L-O SLOs=S-L-Os SLI=S-L-I SLIs=S-L-Is TTL=T-T-L API=A-P-I APIs=A-P-Is RAM=ram TB=terabytes MB=megabytes GB=gigabytes KB=kilobytes HTTP=H-T-T-P SQL=S-Q-L CDN=C-D-N CDC=C-D-C DAU=D-A-U ID=I-D IDs=I-Ds EM=E-M AUX=aux SRE=S-R-E RFC=R-F-C Redis=Reddis MVP=M-V-P QPS=Q-P-S CPU=C-P-U p99=P-ninety-nine p95=P-ninety-five p50=P-fifty Kafka=Kaf-ka Cassandra=Cass-andra -->


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
N: Five axes.
[reveal: v-005]
[pause: 0.45]
N: The weak signal is a clean push design or a clean pull design, defended well.
[reveal: v-006]
[pause: 0.45]
N: The strong signal is the arithmetic that puts a line between them,
[reveal: v-007]
[pause: 0.45]
N: and what happens on the read path to keep the feed correct.
[reveal: v-008]
[pause: 0.45]
C: I'll keep one question in view the whole way: where does correctness live?
[reveal: v-009]
[pause: 0.45]
C: Because a feed is full of copies, and copies go stale.
[pause: 1.0]

[slide: v-010]
[pause: 0.7]
V: A feed is a materialised view that is cheap to read for almost everyone and impossible to precompute for a few. So: push post IDs to the followers of ordinary accounts, pull the celebrities at read time, say where the line is and why, and keep every correctness rule on the read path.
[pause: 1.0]
C: Concretely: a durable source of truth for posts, a small precomputed list of post IDs per reader, a merge of a few celebrity lists when the feed opens, and a read path that filters, ranks under a deadline and hydrates, all inside two hundred milliseconds.
[pause: 1.6]

[slide: v-011]
[pause: 0.6]
C: The order.
C: Requirements and scope, then numbers, then a short theory chapter.
[reveal: v-012]
[pause: 0.45]
C: Then the A-P-I and data, and a design in three versions, each answering the objection to the one before.
[reveal: v-013]
[pause: 0.45]
C: Then most of the time: eight challenges that break the design, where each fix creates the next question.
C: A build cost, because someone has to staff this.
C: And a recap.
[pause: 0.8]

[pause: 1.4]

## 1 Requirements and scope

[slide: v-014]
[pause: 1.2]
C: Eight questions before I draw anything. Each answer is used later.
[pause: 1.8]

[slide: v-015]
[pause: 0.6]
C: How many users, and how many are active?
I: A billion users.
I: Five hundred million daily active.
C: Daily active is the number that matters.
C: It sizes the reads and the memory, because only active users need a precomputed feed.
[pause: 0.6]

[slide: v-016]
[pause: 0.6]
C: What is the ratio of reads to writes?
I: Feed reads are about a hundred times post writes.
C: So I optimise the read path and accept paying on the write path.
C: That is the argument for precomputing at all.
[pause: 0.6]

[slide: v-017]
[pause: 0.6]
C: How many accounts does a user follow, and what does the distribution look like?
I: About two hundred on average.
I: And on the other side, some accounts have over a hundred million followers.
C: That is the tail from the cold open.
C: Asking about the distribution, not just the average, is the question that changes the design.
[pause: 0.6]

[slide: v-018]
[pause: 0.6]
C: What latency, and is the feed ranked?
I: P-ninety-nine under two hundred milliseconds for the first page.
I: Ranked.
I: A scoring service exists.
I: Treat the model as a black box.
C: Good.
C: Ranking becomes a stage with a budget inside the two hundred, not the problem I'm solving.
[pause: 0.6]

[slide: v-019]
[pause: 0.6]
C: How fresh must the feed be?
I: Seconds for people you follow closely.
I: A minute is tolerable in general.
C: That rules out strict consistency and allows asynchronous fan-out.
C: It also says close ties deserve priority.
[pause: 0.6]

[slide: v-020]
[pause: 0.6]
C: How deep do readers go?
I: The first fifty on open, paginated after that.
C: So a precomputed list can be bounded.
C: A few hundred entries cover almost every session.
[pause: 0.6]

[slide: v-021]
[pause: 0.6]
C: What content types?
I: Text and images.
I: Video is out of scope.
C: Bodies and media are hydrated separately from the feed.
C: The feed itself only needs to hold references.
[pause: 0.6]

[slide: v-022]
[pause: 0.6]
C: Which is worse: seeing a post twice, or missing one?
I: Missing a close friend's post is worse.
I: A duplicate on screen is a bug.
C: That gives me a correctness stance.
C: De-duplicate always, and treat a missed close-tie post as the failure that matters.
C: Challenge four comes from this answer.
[pause: 0.6]

[slide: v-023]
[pause: 0.6]
C: Functionally, four things.
C: One, publish a post with text and images, visible to followers.
[reveal: v-024]
[pause: 0.45]
C: Two, read the ranked home feed: the first fifty, then pages with a stable cursor.
[reveal: v-025]
[pause: 0.45]
C: Three, follow and unfollow, with an effect on the feed.
[reveal: v-026]
[pause: 0.45]
C: Four, remove: delete a post, block an account, or change who can see a post, and have it gone from every feed within seconds.
C: Each of these gets a numbered flow later.
[pause: 0.8]

[slide: v-027]
[pause: 0.6]
C: Non-functional, with numbers.
C: These are initial targets, not measurements.
C: P-ninety-nine under two hundred milliseconds for the first page.
[reveal: v-028]
[pause: 0.45]
C: A new post visible to active followers within five seconds at p-ninety-five.
[reveal: v-029]
[pause: 0.45]
C: Read availability of ninety-nine point nine five percent.
[reveal: v-030]
[pause: 0.45]
C: Deleted or blocked content gone within five seconds.
[reveal: v-031]
[pause: 0.45]
C: And one more: a post is never lost.
C: The posts store is the source of truth.
C: Every feed is derived, and can be rebuilt from it.
[pause: 0.8]

[slide: v-032]
[pause: 0.6]
C: In scope: publish, the feed itself, pagination, follow effects, deletes, blocks and audience changes, and ranking as a stage with a budget.
C: Out, on purpose.
C: The ranking model itself.
C: Ads.
[reveal: v-033]
[pause: 0.45]
C: Media upload and transcoding.
C: Search.
C: Notifications, which is its own question.
C: The social graph's internals, which I'll treat as a service.
[reveal: v-034]
[pause: 0.45]
C: And like and comment counters, which belong to a separate counter service.
N: An explicit out list scores.
N: Going deep on the ranking model is the classic rabbit hole here.
[pause: 0.8]

[slide: v-035]
[pause: 0.7]
C: So the core is four things. A source of truth for posts. A per-reader view, built by push for most authors and pull for a few. A read path that filters, ranks and hydrates inside two hundred milliseconds. And a rebuild path for when the view is lost, because it will be.
[pause: 1.6]

[pause: 1.4]

## 2 Estimates

[slide: v-036]
[pause: 1.2]
C: Numbers next. Each one comes with its arithmetic and the decision it changes. All of them are illustrative, built from the interviewer's inputs, not measurements.
[pause: 1.8]

[slide: v-037]
[pause: 0.6]
C: Reads.
C: Five hundred million daily users, five opens a day each, over eighty-six thousand four hundred seconds: about twenty-nine thousand feed opens a second on average.
C: With a peak factor of three, about ninety thousand a second.
C: The decision: the feed is served from memory.
C: A database query per open is out from the start.
[pause: 0.8]

[slide: v-038]
[pause: 0.6]
C: Now the cost of computing every feed when it is opened.
C: Ninety thousand opens a second, each merging the recent posts of two hundred followed accounts: eighteen million reads a second on the author indexes.
[reveal: v-039]
[pause: 0.45]
C: That rules out pure pull at this scale.
C: But at one percent of this scale it is fine, and I'll say so: it is the honest first version.
[pause: 0.8]

[slide: v-040]
[pause: 0.6]
C: Writes.
C: If a tenth of daily users post once a day, that is about five hundred eighty posts a second.
C: Tiny at the source.
C: If each post is copied into two hundred followers' lists, that is about a hundred and twenty thousand inserts a second.
C: Push multiplies writes by two hundred.
C: For ordinary authors that is affordable: an in-memory cluster takes it.
[pause: 0.8]

[slide: v-041]
[pause: 0.6]
C: The cheapest big win.
C: Suppose about half of a typical account's followers haven't opened the app in thirty days.
C: Then half the inserts go to lists nobody reads.
C: Skip them: about sixty thousand a second instead of a hundred and twenty.
C: The fraction is an assumption to measure.
C: The decision holds either way: fan out only to active followers, and rebuild a returning user's feed by pull on their first open.
[pause: 0.8]

[slide: v-042]
[pause: 0.6]
C: Now the number that matters.
C: One celebrity with a hundred and ten million followers posts.
C: At the whole fleet's hundred and twenty thousand inserts a second, that one post takes about nine hundred seconds, fifteen minutes.
[reveal: v-043]
[pause: 0.45]
C: And every ordinary author posting in that window waits behind it.
V: One celebrity post would be a hundred million writes.
V: That number kills pure push.
[pause: 0.8]

[slide: v-044]
[pause: 1.0]
C: Where does the line go?
C: From both sides.
C: Write side: a ten-thousand-follower post is about eight hundredths of a second of the fleet.
[reveal: v-045]
[pause: 0.45]
C: A million-follower post is about eight seconds, past the five-second freshness target on its own.
C: Read side: each pulled author costs about half a millisecond per open.
[reveal: v-046]
[pause: 0.45]
C: Twenty of them, ten milliseconds of the budget.
C: So the line sits around ten to a hundred thousand followers, as a config value I tune with data.
[reveal: v-047]
[pause: 0.45]
C: Challenge two returns to this.
[pause: 1.0]

[slide: v-048]
[pause: 1.3]
C: Memory. Five hundred million active users, five hundred entries each, sixteen bytes an entry for a post I-D, author I-D and time packed together: four terabytes, twelve with three replicas. That fits a memory tier.
C: If each entry held the post body, about a kilobyte, it would be two hundred and fifty terabytes, sixty times larger. And every edit or delete would chase millions of copies. So the precomputed list holds I-Ds, and bodies are hydrated from one post cache.
[pause: 1.1]

[slide: v-049]
[pause: 1.3]
C: The read budget, as one bar. Lookups and filtering, about twenty milliseconds: the timeline, the celebrity lists, the block set. Ranking gets a hard deadline of eighty. Hydrating fifty posts, about twenty. Network and serialisation, twenty. A hundred and forty used, sixty spare.
C: The decision: ranking gets a deadline and a fallback, because it is the largest piece and it belongs to another team.
[pause: 1.1]

[slide: v-050]
[pause: 0.6]
C: One more, because it shapes a failure path.
C: Lose one cache shard out of a hundred: five million users.
C: If a fifth of them open the app in the next ten minutes, that is about seventeen hundred rebuilds a second, each reading two hundred author indexes: three hundred and forty thousand reads a second on a store sized for something much smaller.
C: So the rebuild path needs coalescing, a rate limit and a degraded mode.
C: That is challenge five.
[pause: 0.8]

[slide: v-051]
[pause: 1.0]
N: Every number on this slide ends in a decision.
[reveal: v-052]
[pause: 0.45]
N: That is what the estimation phase is graded on.
[reveal: v-053]
[pause: 0.45]
C: Serve from memory.
[reveal: v-054]
[pause: 0.45]
C: Precompute for most, with pull as the first version and the rebuild path.
[reveal: v-055]
[pause: 0.45]
C: Push only to active followers.
[reveal: v-056]
[pause: 0.45]
C: Pull the celebrities, with a measured line.
[reveal: v-057]
[pause: 0.45]
C: I-Ds, not bodies.
[reveal: v-058]
[pause: 0.45]
C: And a deadline for ranking.
[pause: 1.0]

[pause: 1.4]

## 3 Theory

[slide: v-059]
[pause: 1.2]
C: A short theory chapter before the design, so the design can lean on it. Six parts: what a feed is and is not, the properties, the central tension, seven mechanisms, the options, and the failure catalogue.
[pause: 1.8]

[slide: v-060]
[pause: 0.7]
V: A home feed is, for each reader, a bounded, ranked list of recent post I-Ds from the accounts they follow, assembled from a precomputed part and a part fetched at read time, then filtered and hydrated within the read budget.
[pause: 1.0]
C: Each clause carries weight. For each reader: it is a per-user view, so it can be lost and rebuilt. Bounded: a few hundred entries. Post I-Ds: never bodies. Precomputed plus fetched: the hybrid. Filtered: correctness happens at read. Within the budget: two hundred milliseconds, with a fallback.
[pause: 1.6]

[slide: v-061]
[pause: 0.6]
C: Four neighbours.
C: It is not the source of truth: posts are, and the view can be wrong for a few seconds and rebuilt.
[reveal: v-062]
[pause: 0.45]
C: It is not a chat inbox: an inbox must never lose a message, while a feed may leave out an old post.
[reveal: v-063]
[pause: 0.45]
C: It is not search: it answers one query shape, and challenge seven asks for a different one.
[reveal: v-064]
[pause: 0.45]
C: And it is not the ranking model, which is a stage with a budget.
[pause: 0.8]

[slide: v-065]
[pause: 0.6]
V: Safety: a viewer never sees content they must not see for longer than five seconds, and a post is never lost.
[reveal: v-066]
[pause: 0.45]
V: Liveness: a post reaches active followers within five seconds, every feed open answers within two hundred milliseconds, and a lost timeline is rebuilt on its next open.
[pause: 0.8]
C: Most designs talk only about liveness, about speed.
C: S-one is the safety property people forget: a feed made of copies will show a deleted post unless something stops it.
C: Every fix from here names the property it serves.
[pause: 0.8]

[slide: v-067]
[pause: 1.3]
C: The central tension, as one picture. Push pays at post time, in proportion to the author's followers: the red curve rises as followers grow. Pull pays at read time, in proportion to the reader's followees: per post it is flat and small, but paid on every follower's open.
C: The lines cross near the threshold. Below it push is cheaper; above it pull is. The hybrid simply follows the lower curve. Hold on to this picture: challenges one and two live on it.
[pause: 1.1]

[slide: v-068]
[pause: 0.6]
C: Mechanism one, fan-out on write.
C: It protects freshness and a cheap read.
[reveal: v-069]
[pause: 0.45]
C: On each post, insert the post I-D, author and time into each active follower's sorted list, trimmed to five hundred, keyed by post I-D so a repeat is a no-op.
[reveal: v-070]
[pause: 0.45]
C: It rules out a read that touches two hundred authors, and duplicates on re-delivery.
[reveal: v-071]
[pause: 0.45]
C: It costs a hundred and twenty thousand inserts a second, a memory tier, and amplification on big authors.
[pause: 0.8]

[slide: v-072]
[pause: 0.6]
C: Mechanism two, fan-out on read.
C: It protects the read for celebrities, and recovery.
[reveal: v-073]
[pause: 0.45]
C: At read time, read each pulled author's recent post I-Ds from a per-author index and merge them.
C: The same path rebuilds a lost timeline.
[reveal: v-074]
[pause: 0.45]
C: It rules out a hundred million writes for one post, and a lost view staying lost.
[reveal: v-075]
[pause: 0.45]
C: It costs a merge per read, and author indexes that must be protected from a stampede.
[pause: 0.8]

[slide: v-076]
[pause: 0.6]
C: Mechanism three, the threshold.
[reveal: v-077]
[pause: 0.45]
C: Each author has a tier: push below the line, pull above, and push to recently active followers in between.
C: The line has hysteresis, so an account near it does not flap, and crossing it needs no backfill.
[reveal: v-078]
[pause: 0.45]
C: It rules out the celebrity problem, pure pull's read cost, and writes to users who never read.
[reveal: v-079]
[pause: 0.45]
C: It costs a tier per author, and a number I must defend.
[pause: 0.8]

[slide: v-080]
[pause: 0.6]
C: Mechanism four, I-Ds in the view and hydration through a post cache.
C: It protects deletes, because there is one place to change, and memory.
[reveal: v-081]
[pause: 0.45]
C: The view holds I-Ds; the read path fetches the top fifty bodies from a post cache.
[reveal: v-082]
[pause: 0.45]
C: It rules out two hundred and fifty terabytes of copies and edits chasing millions of entries.
[reveal: v-083]
[pause: 0.45]
C: It costs a multi-get per page, and a post cache that becomes critical.
[pause: 0.8]

[slide: v-084]
[pause: 0.6]
C: Mechanism five, the visibility filter.
C: It protects S-one.
[reveal: v-085]
[pause: 0.45]
C: Every page drops posts that are deleted or out of audience when it hydrates them, and drops authors in the reader's block, mute and unfollow set when it merges.
[reveal: v-086]
[pause: 0.45]
C: It rules out a deleted or blocked post surviving in a copy.
[reveal: v-087]
[pause: 0.45]
C: It costs a small set read on every open.
[pause: 0.8]

[slide: v-088]
[pause: 0.6]
C: Mechanism six, ranking under a deadline.
C: It protects the two hundred milliseconds.
[reveal: v-089]
[pause: 0.45]
C: Call ranking with a hard deadline; on a miss, order by recency and close ties, and count it.
[reveal: v-090]
[pause: 0.45]
C: It rules out a slow model making the whole feed slow.
[reveal: v-091]
[pause: 0.45]
C: It costs lower quality while degraded, which must be measured and owned by someone.
[pause: 0.8]

[slide: v-092]
[pause: 0.6]
C: Mechanism seven, a log with priority lanes.
[reveal: v-093]
[pause: 0.45]
C: The post and its event commit in one transaction, an outbox.
C: A log keyed by author feeds the workers.
C: Close ties are fanned out first, and the log offset is committed last, so a crash re-delivers rather than loses.
[reveal: v-094]
[pause: 0.45]
C: It rules out a burst delaying close friends, and lost work.
[reveal: v-095]
[pause: 0.45]
C: It costs a log to run, and makes lag a metric to watch.
[pause: 0.8]

[slide: v-096]
[pause: 1.0]
C: Six approaches, each with the failure that rules it out.
C: A, pull with a database join: fails at any real scale.
[reveal: v-097]
[pause: 0.45]
C: B, pull with a per-reader result cache: fine until freshness and the miss rate at peak bite.
[reveal: v-098]
[pause: 0.45]
C: It is my first version.
C: C, pure push of I-Ds: fails on the first celebrity post.
[reveal: v-099]
[pause: 0.45]
C: D, pure push of bodies: two hundred and fifty terabytes, and every edit chases copies.
[reveal: v-100]
[pause: 0.45]
C: E is the hybrid: push I-Ds to active followers of ordinary authors, pull celebrities, hydrate, and filter on read.
C: It fails if the threshold is set once and never measured, and on a reader who follows hundreds of celebrities, which is challenge two.
[reveal: v-101]
[pause: 0.45]
C: F, buy a managed feed service: it fails on our own ranking and privacy rules, and on cost at a billion users.
V: I pick E, built after B as the first version.
[pause: 1.0]

[slide: v-102]
[pause: 0.6]
C: What the pick gives up, plainly.
C: Strict freshness: a post appears within seconds, not instantly.
C: And simplicity: two paths, a tier per author, and a number I must defend.
C: What it buys: a feed open that costs one memory read and a small merge, writes bounded per post, deletes that are one write, and a view that can be thrown away and rebuilt.
[reveal: v-103]
[pause: 0.45]
C: And B is not wrong.
[reveal: v-104]
[pause: 0.45]
C: It is right until the merge on a cache miss breaks the budget at peak.
C: I'd measure that before building E.
[pause: 0.8]

[slide: v-105]
[pause: 1.0]
C: The failure catalogue, which becomes the challenge list.
C: The celebrity post, and bursts.
[reveal: v-106]
[pause: 0.45]
C: An account crossing the line, and the reader who follows hundreds of celebrities.
[reveal: v-107]
[pause: 0.45]
C: Deletes and blocks.
[reveal: v-108]
[pause: 0.45]
C: Duplicates, and a feed that moves while you scroll.
[reveal: v-109]
[pause: 0.45]
C: A lost shard and the rebuild stampede.
[reveal: v-110]
[pause: 0.45]
C: A slow ranker.
[reveal: v-111]
[pause: 0.45]
C: A query the view was not built for.
[reveal: v-112]
[pause: 0.45]
C: And the feed that works but got worse.
C: Eight challenges, in that order.
[pause: 1.0]

[slide: v-113]
[pause: 1.0]
N: Good theory has a consequence for the design.
[reveal: v-114]
[pause: 0.45]
N: Every mechanism here names the property it serves and where it returns.
[reveal: v-115]
[pause: 0.45]
C: That is the vocabulary.
[reveal: v-116]
[pause: 0.45]
C: On to the A-P-I and the data.
[pause: 1.0]

[pause: 1.4]

## 4 API and entities

[slide: v-117]
[pause: 1.2]
C: The A-P-I next. Each call is tagged with the requirement it serves and the entities it reads or writes.
[pause: 1.8]

[slide: v-118]
[pause: 1.0]
C: Five calls.
C: Post, with an idempotency key so a retried upload doesn't create two posts: it writes the post, the author index and an outbox row in one transaction.
[reveal: v-119]
[pause: 0.45]
C: Get feed, with a cursor and a limit of fifty: it reads the timeline, the celebrity lists, the block set and the post cache.
[reveal: v-120]
[pause: 0.45]
C: Follow and unfollow write one edge.
[reveal: v-121]
[pause: 0.45]
C: Delete a post and block an account write one row each and emit an invalidation event.
[reveal: v-122]
[pause: 0.45]
C: And internally, rank: I send I-Ds and a deadline, and get scores back.
C: Features stay on the ranking side.
[pause: 1.0]

[slide: v-123]
[pause: 1.0]
C: Publishing on the wire.
C: The client sends the text, media references and audience, with an idempotency key.
C: The answer is a post I-D.
C: The I-D is time-sortable, so timelines can be ordered by I-D alone without another lookup.
C: And a retry with the same key returns the same post, not a second one.
[pause: 1.0]

[slide: v-124]
[pause: 1.0]
C: Reading.
C: Fifty hydrated items and a cursor.
C: The cursor encodes the score and post I-D of the last item shown, so the next page starts strictly after it whatever new posts arrived above.
[reveal: v-125]
[pause: 0.45]
C: An offset would repeat or skip items; that is challenge four.
C: And a fallback flag says when ranking missed its deadline, which feeds a metric.
[pause: 1.0]

[slide: v-126]
[pause: 1.3]
C: The conceptual model.
[reveal: v-127]
[pause: 0.45]
C: A user authors posts.
[reveal: v-128]
[pause: 0.45]
C: Users follow users,
[reveal: v-129]
[pause: 0.45]
C: many to many, and both directions are queried: who I follow, for reading, and who follows me, for fan-out.
[reveal: v-130]
[pause: 0.45]
C: Users block or mute users.
[reveal: v-131]
[pause: 0.45]
C: The timeline entry is a weak entity: it exists only because a user sees a post, and it is derived.
[reveal: v-132]
[pause: 0.45]
C: Delete every timeline entry and the feed can be rebuilt from posts and follows.
[reveal: v-133]
[pause: 0.45]
C: That sentence is the whole recovery story.
[pause: 1.1]

[slide: v-134]
[pause: 1.3]
C: Physically.
[reveal: v-135]
[pause: 0.45]
C: The post table is the source of truth, keyed by the time-sortable post I-D and sharded by it.
[reveal: v-136]
[pause: 0.45]
C: The author index has one partition per author, newest first: it serves pull, rebuild and catch-up.
[reveal: v-137]
[pause: 0.45]
C: Follows belong to the graph service.
[reveal: v-138]
[pause: 0.45]
C: Below, three in-memory structures.
[reveal: v-139]
[pause: 0.45]
C: The timeline per viewer: a sorted set of at most five hundred I-Ds.
[reveal: v-140]
[pause: 0.45]
C: The celebrity recent list per author: the last hundred I-Ds, replicated to many cache nodes.
C: And the block set per viewer, small, read on every open.
[pause: 1.1]

[slide: v-141]
[pause: 1.0]
C: In one table.
[reveal: v-142]
[pause: 0.45]
C: Three stores of truth: posts, the author index, and the graph.
[reveal: v-143]
[pause: 0.45]
C: Three derived stores: timelines, celebrity lists, and the post cache.
[reveal: v-144]
[pause: 0.45]
C: Anything derived can be lost and rebuilt.
[reveal: v-145]
[pause: 0.45]
C: Anything true must be durable and replicated.
[reveal: v-146]
[pause: 0.45]
N: Naming truth and derived before the interviewer asks about failures is the recovery plan,
[reveal: v-147]
[pause: 0.45]
N: said early.
[pause: 1.0]

[pause: 1.4]

## 5 High-level design

[slide: v-148]
[pause: 1.2]
C: The design, in three versions. Each version answers the objection to the one before. The boxes never move: every later picture is a view of the same baseline.
[pause: 1.8]

[slide: v-149]
[pause: 1.3]
C: Version one.
[reveal: v-150]
[pause: 0.45]
C: On the top row, the write path: the author posts, the post service writes the post and its author index in one transaction.
[reveal: v-151]
[pause: 0.45]
C: On the bottom,
[reveal: v-152]
[pause: 0.45]
C: the read path:
[reveal: v-153]
[pause: 0.45]
C: the reader opens the app, the feed service asks the graph for the followees and the block set, reads the recent posts of two hundred authors from the author indexes, merges, sends the candidates to ranking, and returns fifty.
[reveal: v-154]
[pause: 0.45]
C: That is the honest first version.
[reveal: v-155]
[pause: 0.45]
C: At one percent of this scale, with a short per-reader result cache, it works.
[pause: 1.1]

[slide: v-156]
[pause: 0.6]
C: The objection to version one.
C: Every cache miss is a two-hundred-way merge, and at peak that is eighteen million author-index reads a second.
[reveal: v-157]
[pause: 0.45]
C: And a cached result is up to a minute old, so a close friend's post waits.
[reveal: v-158]
[pause: 0.45]
C: The read must become one memory lookup.
C: That means doing the work when a post is written.
[pause: 0.8]

[slide: v-159]
[pause: 1.3]
C: Version two, push.
[reveal: v-160]
[pause: 0.45]
C: New boxes are outlined in blue.
[reveal: v-161]
[pause: 0.45]
C: The post service still writes one transaction, now with an outbox row.
[reveal: v-162]
[pause: 0.45]
C: A relay carries it to the event log, keyed by author.
C: Fan-out workers read the event, page through the author's followers from the graph, skip the inactive ones, and insert the post I-D into each follower's timeline.
[reveal: v-163]
[pause: 0.45]
C: The read path becomes: read my timeline, about five hundred I-Ds, rank, and hydrate the top fifty from the post cache.
C: One memory read and a multi-get.
[pause: 1.1]

[slide: v-164]
[pause: 1.0]
C: The technology, each against its rivals.
C: Timelines in memory, as a sorted set per viewer, rather than a table: they are read-dominated, bounded and rebuildable, so memory is the right price.
[reveal: v-165]
[pause: 0.45]
C: Posts in a sharded store with time-sortable keys, and a per-author index.
[reveal: v-166]
[pause: 0.45]
C: The transport is an outbox and a partitioned log rather than a direct call, so there is no dual write, the work is replayable, and other consumers like search can read the same events.
[reveal: v-167]
[pause: 0.45]
C: And the graph is a service, because both directions are queried constantly.
[pause: 1.0]

[slide: v-168]
[pause: 1.0]
C: The worker in code, because here the code is the mechanism. One branch per tier. A pulled author gets one write to their recent list. Otherwise, page through followers a thousand at a time, keep only the active ones, and for the mid tier only those active in the last day. Add the post I-D to each timeline, trimmed to five hundred. And commit the log offset last, so a crash re-delivers the event instead of losing it. Re-delivery is safe because the timeline is keyed by post I-D.
[pause: 1.0]

[slide: v-169]
[pause: 0.6]
C: The objection to version two has three parts.
C: One celebrity post holds the whole fan-out fleet for fifteen minutes.
[reveal: v-170]
[pause: 0.45]
C: About half the inserts go to users who won't open the app this month.
[reveal: v-171]
[pause: 0.45]
C: And a deleted post now sits in millions of timelines.
[reveal: v-172]
[pause: 0.45]
C: The tail of authors decides the design, and correctness cannot live in copies.
[pause: 0.8]

[slide: v-173]
[pause: 1.3]
C: Version three.
C: The new box is the celebrity posts cache.
C: Above the threshold, the fan-out worker does not fan out at all: it writes one entry to the author's recent list, the dashed purple arrow.
C: On the read path, the feed service merges my timeline with the lists of the few celebrities I follow.
[reveal: v-174]
[pause: 0.45]
C: Three more changes that do not add boxes.
C: Fan-out goes only to active followers.
C: The feed service filters every page against the post's status and my block set.
C: And ranking is called with a deadline, with a fallback.
[pause: 1.1]

[slide: v-175]
[pause: 1.3]
C: The publish flow for an ordinary author with two thousand followers, by the numbers.
[reveal: v-176]
[pause: 0.45]
C: One, the author posts.
[reveal: v-177]
[pause: 0.45]
C: Two, one transaction writes the post, the author index and the outbox row.
[reveal: v-178]
[pause: 0.45]
C: Three, the relay publishes the event.
[reveal: v-179]
[pause: 0.45]
C: Four, a worker consumes it: tier push.
[reveal: v-180]
[pause: 0.45]
C: Five, it pages through the followers from the graph.
[reveal: v-181]
[pause: 0.45]
C: Six, it inserts the I-D into each active follower's timeline and trims to five hundred.
C: The offset is committed after that.
[pause: 1.1]

[slide: v-182]
[pause: 1.3]
C: The same flow for a celebrity.
[reveal: v-183]
[pause: 0.45]
C: Steps one to four are identical.
[reveal: v-184]
[pause: 0.45]
C: Step five is different:
[reveal: v-185]
[pause: 0.45]
C: one append to the author's recent list.
[reveal: v-186]
[pause: 0.45]
C: No fan-out.
[reveal: v-187]
[pause: 0.45]
C: The log partition is free again in milliseconds.
[pause: 1.1]

[slide: v-188]
[pause: 1.3]
C: As a sequence.
[reveal: v-189]
[pause: 0.45]
C: The post service writes post,
[reveal: v-190]
[pause: 0.45]
C: author index and outbox row together, and answers two-oh-one.
[reveal: v-191]
[pause: 0.45]
C: Only then does the relay publish the event,
[reveal: v-192]
[pause: 0.45]
C: keyed by author.
[reveal: v-193]
[pause: 0.45]
C: The worker pages through followers,
[reveal: v-194]
[pause: 0.45]
C: skips the inactive, inserts and trims, and commits its offset last.
[reveal: v-195]
[pause: 0.45]
C: Nothing the client waits for depends on fan-out.
[pause: 1.1]

[slide: v-196]
[pause: 1.3]
C: The read flow.
[reveal: v-197]
[pause: 0.45]
C: One, get feed.
[reveal: v-198]
[pause: 0.45]
C: Two, read my timeline, about five hundred I-Ds.
[reveal: v-199]
[pause: 0.45]
C: Three, merge the recent lists of the celebrities I follow.
[reveal: v-200]
[pause: 0.45]
C: Four, the graph gives me my block and mute set, and the merge drops those authors.
[reveal: v-201]
[pause: 0.45]
C: Five, the top two hundred by recency go to ranking with an eighty millisecond deadline.
[reveal: v-202]
[pause: 0.45]
C: Six, the top fifty are hydrated by multi-get from the post cache, which drops anything deleted.
[reveal: v-203]
[pause: 0.45]
C: Seven, fifty items and a cursor go back.
[pause: 1.1]

[slide: v-204]
[pause: 1.0]
C: The read path in code. Read the timeline. Add the recent lists of followed celebrities, a handful. Drop blocked authors, de-duplicate, keep the top two hundred by time. Score them with an eighty millisecond deadline, or fall back. Take the page after the cursor. Hydrate, and drop anything not visible to this viewer: deleted, or out of its audience. Return the page and the next cursor.
[pause: 1.0]

[slide: v-205]
[pause: 1.3]
C: The same read as a sequence, with times.
[reveal: v-206]
[pause: 0.45]
C: Timeline, five milliseconds.
[reveal: v-207]
[pause: 0.45]
C: Celebrity lists, five.
[reveal: v-208]
[pause: 0.45]
C: Merge, de-duplicate and filter.
[reveal: v-209]
[pause: 0.45]
C: Score two hundred with an eighty millisecond deadline.
[reveal: v-210]
[pause: 0.45]
C: Multi-get fifty, about twenty.
[reveal: v-211]
[pause: 0.45]
C: Drop anything deleted.
[reveal: v-212]
[pause: 0.45]
C: Fifty items and a cursor.
[pause: 1.1]

[slide: v-213]
[pause: 1.3]
C: Follow.
C: One, the request.
[reveal: v-214]
[pause: 0.45]
C: Two, one edge is written in the graph.
C: Three: nothing is backfilled.
[reveal: v-215]
[pause: 0.45]
C: If the new followee is a celebrity, the next read's merge already includes them.
C: If they are ordinary, their next post arrives by fan-out.
[reveal: v-216]
[pause: 0.45]
C: Optionally I'd insert their last few posts so the follow feels immediate.
C: Unfollow adds the author to my filter set.
[pause: 1.1]

[slide: v-217]
[pause: 1.3]
C: Remove.
[reveal: v-218]
[pause: 0.45]
C: One and two, the delete writes the post's status, once.
[reveal: v-219]
[pause: 0.45]
C: Three, an invalidation event drops the post from the cache.
[reveal: v-220]
[pause: 0.45]
C: Four and five,
[reveal: v-221]
[pause: 0.45]
C: the next read hydrates the page, sees the status, and drops the I-D.
[reveal: v-222]
[pause: 0.45]
C: The I-Ds still sitting in timelines are harmless, and a background job removes them later.
[pause: 1.1]

[slide: v-223]
[pause: 1.3]
C: Now the same system in C4 terms, for the detail.
[reveal: v-224]
[pause: 0.45]
C: The context: authors post, about six hundred a second.
[reveal: v-225]
[pause: 0.45]
C: Readers open the feed, about ninety thousand a second at peak.
[reveal: v-226]
[pause: 0.45]
C: The feed system depends on two systems owned by other teams,
[reveal: v-227]
[pause: 0.45]
C: ranking with an eighty millisecond budget and the social graph,
[reveal: v-228]
[pause: 0.45]
C: and media is served from a C-D-N, out of scope.
[pause: 1.1]

[slide: v-229]
[pause: 1.3]
C: The containers.
[reveal: v-230]
[pause: 0.45]
C: Across the top,
[reveal: v-231]
[pause: 0.45]
C: the write path: post service, posts database, event log, fan-out workers.
[reveal: v-232]
[pause: 0.45]
C: In the middle,
[reveal: v-233]
[pause: 0.45]
C: three in-memory stores: the post cache, the celebrity lists, and the timelines.
[reveal: v-234]
[pause: 0.45]
C: At the bottom,
[reveal: v-235]
[pause: 0.45]
C: the feed service,
[reveal: v-236]
[pause: 0.45]
C: stateless,
[reveal: v-237]
[pause: 0.45]
C: which merges, filters, ranks under a deadline, hydrates, and writes the cursor.
[reveal: v-238]
[pause: 0.45]
C: The graph and ranking sit outside, as dependencies with contracts.
[pause: 1.1]

[slide: v-239]
[pause: 1.3]
C: Back to the budget, now with every box named. Lookups and filtering, twenty milliseconds. Ranking, eighty, as a hard deadline. Hydration, twenty. Network, twenty. A hundred and forty used, sixty spare. The spare is not slack: it is what a slow cache shard or a garbage-collection pause eats.
[pause: 1.1]

[slide: v-240]
[pause: 1.0]
C: Version three works end to end.
C: What it still owes are the details, and each one is a challenge.
C: What exactly happens on a celebrity post.
[reveal: v-241]
[pause: 0.45]
C: Where the line is.
[reveal: v-242]
[pause: 0.45]
C: How a deleted post disappears.
[reveal: v-243]
[pause: 0.45]
C: Duplicates and pagination.
[reveal: v-244]
[pause: 0.45]
C: A lost shard.
[reveal: v-245]
[pause: 0.45]
C: A slow ranker.
[reveal: v-246]
[pause: 0.45]
C: A new kind of query.
[reveal: v-247]
[pause: 0.45]
C: And how we would know any of it went wrong.
[pause: 1.0]

[pause: 1.4]

## 5.1 Components and technologies

[slide: v-248]
[pause: 1.2]
C: Now one level down. Every container, with the technology I would run it on, and for each choice, the alternatives I rejected and why.
[pause: 1.8]

[slide: v-249]
[pause: 1.3]
C: The container view again, with one change: the type line now names the technology. I will walk it once, then defend each choice on its own slide.
[reveal: v-250]
[pause: 0.45]
C: Post service is Go, stateless.
[reveal: v-251]
[pause: 0.45]
C: Feed service is Go, gRPC, stateless.
[reveal: v-252]
[pause: 0.45]
C: Posts DB is PostgreSQL + Cassandra.
[reveal: v-253]
[pause: 0.45]
C: Post cache is Memcached.
[reveal: v-254]
[pause: 0.45]
C: Event log is Kafka.
[reveal: v-255]
[pause: 0.45]
C: Celebrity posts is Redis, replicated.
[reveal: v-256]
[pause: 0.45]
C: Fan-out workers is Kafka consumers, Go.
[reveal: v-257]
[pause: 0.45]
C: Timeline cache is Redis Cluster.
[reveal: v-258]
[pause: 0.45]
C: Social graph is Another team's service.
[reveal: v-259]
[pause: 0.45]
C: Ranking is Another team's gRPC.
[pause: 1.1]

[slide: v-260]
[pause: 1.0]
C: Each shard is a PostgreSQL primary with a synchronous standby in another zone; the post row and an outbox row go in one transaction. The author index is a Cassandra table keyed by author, newest first.
[reveal: v-261]
[pause: 0.45]
C: Why PostgreSQL 16, sharded by post ID; Cassandra for the author index: Written once, read by ID, never lost: one transaction for post plus outbox. The author index is a newest-first range per author, which Cassandra does natively.
[reveal: v-262]
[pause: 0.45]
C: Rejected: One PostgreSQL primary. Fine at MVP scale. At 600 posts a second plus the reads of 90,000 feed opens, it is one failure domain and one vacuum problem.
[reveal: v-263]
[pause: 0.45]
C: DynamoDB for everything. Good at both access paths, but the post-and-outbox transaction becomes a transactional write across items and tables, and we lose the plain SQL for moderation queries.
[reveal: v-264]
[pause: 0.45]
C: Cassandra for posts too. Leaderless writes suit the index. For the post of record, no multi-row transaction with the outbox means the dual-write bug returns.
[pause: 1.0]

[slide: v-265]
[pause: 1.0]
C: A relay reads the outbox through change data capture and publishes PostCreated, keyed by author. Three brokers across zones, replication factor three, producers wait for all in-sync replicas. Fan-out workers form one consumer group; a second group, for search or notifications, reads the same events without touching the first.
[reveal: v-266]
[pause: 0.45]
C: Why Kafka, 64 partitions keyed by author, replication factor three: A replayable log that absorbs bursts and serves many consumers. Keying by author keeps one author's posts in order, and a rebuild is a replay.
[reveal: v-267]
[pause: 0.45]
C: Rejected: RabbitMQ. A queue: once acknowledged, a message is gone. A rebuilt consumer cannot replay, and a second consumer needs its own queue.
[reveal: v-268]
[pause: 0.45]
C: The post service calling fan-out directly. The dual write: a crash between the two loses the fan-out or fans out a post that rolled back. No replay either.
[reveal: v-269]
[pause: 0.45]
C: Pub-Sub or Kinesis. Honest equals if we are on that cloud. Buy, not build, and the same design.
[pause: 1.0]

[slide: v-270]
[pause: 1.0]
C: Each viewer has a sorted set of their 500 newest post IDs, scored by time. The fan-out worker pipelines inserts and trims to 500; one replica per shard. A viewer away for a week has no timeline until they return.
[reveal: v-271]
[pause: 0.45]
C: Why Redis Cluster, a sorted set per viewer, partitioned by viewer: A feed open is one range read. A sorted set gives idempotent inserts, ordering by time and cheap trimming, and losing one is a latency problem, not data loss.
[reveal: v-272]
[pause: 0.45]
C: Rejected: A relational table per viewer. 60,000 inserts a second into an indexed table is write amplification we do not need for something we can rebuild.
[reveal: v-273]
[pause: 0.45]
C: A Cassandra row per viewer. Durable, but every feed open becomes a disk read. Fine as a cold tier, wrong for the hot path.
[reveal: v-274]
[pause: 0.45]
C: Memcached. No sorted structure: every insert becomes a read-modify-write of a whole list, which races under concurrent fan-out.
[pause: 1.0]

[slide: v-275]
[pause: 1.0]
C: A feed open ends in one multi-get of fifty post IDs. A miss reads the posts store and fills the cache with a lifetime of a day and jitter. An edit or a delete does not rewrite the cache; a delete is filtered on read.
[reveal: v-276]
[pause: 0.45]
C: Why Memcached, a separate pool from the timelines: Posts change rarely and are read by ID in batches of 50, so a plain key-value cache with multi-get is enough. A separate pool means a post-cache problem cannot evict timelines.
[reveal: v-277]
[pause: 0.45]
C: Rejected: Hydrating from the posts store directly. Fifty point reads per feed open at 90,000 opens a second is 4.5 million reads a second on the primary store.
[reveal: v-278]
[pause: 0.45]
C: The same Redis cluster as the timelines. One eviction policy and one failure domain for two different jobs. A post-cache stampede would take timelines with it.
[pause: 1.0]

[slide: v-279]
[pause: 1.0]
C: Workers read PostCreated and check the author's tier. Ordinary: page through followers and insert the post ID into each active follower's timeline. Celebrity: one entry in the celebrity list. The autoscaler follows consumer lag.
[reveal: v-280]
[pause: 0.45]
C: Why Go workers on Kubernetes, scaled on lag: Fan-out is the 120,000 inserts a second. Idempotent inserts make a retry harmless, and scaling on consumer lag keeps a burst from becoming a delay.
[reveal: v-281]
[pause: 0.45]
C: Rejected: Push to every follower, always. A 100-million-follower post is 100 million inserts: minutes of backlog behind it for everyone else.
[reveal: v-282]
[pause: 0.45]
C: Pull for everyone. Every feed open reads 200 followees' recent posts: 90,000 opens a second times 200 merges.
[reveal: v-283]
[pause: 0.45]
C: Spark or Flink for the fan-out. A stream engine adds state and a cluster for a loop that reads an event and writes pipelines.
[pause: 1.0]

[slide: v-284]
[pause: 1.0]
C: The service reads the timeline, reads the celebrity lists of the authors the viewer follows, merges, filters blocked and deleted posts, asks ranking, and hydrates fifty posts. Each downstream call gets what is left of a 200 millisecond budget. If ranking misses its deadline the page is served in time order.
[reveal: v-285]
[pause: 0.45]
C: Why Go services on Kubernetes, gRPC inside, a deadline propagated: The feed open has a 200 millisecond p99 across five dependencies. A deadline passed down every call and a fallback at each hop is how it stays inside the budget.
[reveal: v-286]
[pause: 0.45]
C: Rejected: A monolith with the post service. A slow ranker or a flood of posts would take the read path down with it. Different scaling, different failure domains.
[reveal: v-287]
[pause: 0.45]
C: Computing the ranked feed in the background. Fresh for nobody: the ranker's score depends on the second the viewer opens the app.
[pause: 1.0]

[slide: v-288]
[pause: 1.0]
C: The graph answers followers for fan-out and followees for reads, with blocks. We cache its answers briefly and treat a block as a correctness input, checked on read. Ranking receives about 200 candidates and returns scores inside 80 milliseconds. Each has a circuit breaker and a defined fallback: cached followees for the graph, time order for ranking.
[reveal: v-289]
[pause: 0.45]
C: Why gRPC contracts with a deadline, a cache and a fallback each: Both are another team's system on another schedule. A contract and a fallback keep their bad day from becoming ours.
[reveal: v-290]
[pause: 0.45]
C: Rejected: Rebuilding the graph inside the feed. A second copy of the follow data that would drift from the first. Own the contract, not the data.
[reveal: v-291]
[pause: 0.45]
C: No fallback for ranking. The feed's availability would be the ranker's availability.
[pause: 1.0]

[slide: v-292]
[pause: 1.0]
C: The stack on one slide, as I would leave it on the whiteboard.
C: Posts DB: PostgreSQL; Cassandra index.
C: Not One primary; DynamoDB.
C: Post plus outbox in one transaction.
[reveal: v-293]
[pause: 0.45]
C: Event log: Kafka, keyed by author.
C: Not RabbitMQ; direct call.
C: Replayable; ordered per author.
[reveal: v-294]
[pause: 0.45]
C: Timelines: Redis sorted sets.
C: Not SQL table; Cassandra row.
C: Idempotent insert; one read.
[reveal: v-295]
[pause: 0.45]
C: Post cache: Memcached, own pool.
C: Not Direct reads; shared Redis.
C: Multi-get; isolated.
[reveal: v-296]
[pause: 0.45]
C: Fan-out: Go consumers, tiered.
C: Not Push all; pull all.
C: Celebrities pulled.
[reveal: v-297]
[pause: 0.45]
C: Feed service: Go, gRPC, deadlines.
C: Not Monolith.
C: Degrade, do not fail.
[reveal: v-298]
[pause: 0.45]
C: Graph, ranking: gRPC with fallback.
C: Not No fallback.
C: Their outage is not ours.
[reveal: v-299]
[pause: 0.45]
N: Naming a product is not the signal.
N: Naming the property that rules out its rival is.
N: Interviewers go one level down on whichever box you name, so name only what you can defend.
[pause: 1.0]

[slide: v-300]
[pause: 0.6]
N: Before the challenges, swap seats. You are the interviewer now. Of everything on the last slide, which box would you push on, and what is the one question you would ask? Pause the video and pick one.
[pause: 3.0]

[slide: v-301]
[pause: 1.0]
N: Here is where interviewers usually go.
I: A post is created and the post service crashes right after the commit.
I: Does the post reach its followers?
[pause: 1.2]
N: Yes.
N: The outbox row committed with the post, so the relay publishes it when the service or the relay restarts.
[reveal: v-302]
[pause: 0.45]
N: The trap is a second call to fan-out after the commit, which is a dual write.
I: Fan-out was down for two hours.
I: How does it catch up, and does a reader see posts out of order?
[pause: 1.2]
N: The consumer group resumes from its committed offset and works through the backlog at its own pace.
N: Inserts are idempotent and ordered by post ID in the sorted set, so a late insert lands in the right place.
[reveal: v-303]
[pause: 0.45]
N: Readers see fresh posts late, not out of order.
I: A Redis shard holding two million timelines is lost.
I: What does a reader see, and how do they come back?
[pause: 1.2]
N: A replica is promoted, and timelines written in the last seconds may be missing.
N: Readers whose timeline is gone are rebuilt by pull from followees, rate limited, so the posts store is not flattened.
[reveal: v-304]
[pause: 0.45]
I: One post goes viral and every reader's feed contains it.
I: What happens to the one cache key holding it?
[pause: 1.2]
N: It becomes a hot key: one node answers every hydrate for that post.
N: A small in-process cache on the feed service for the hottest few thousand posts, with a short lifetime, takes the load before it reaches the node.
[reveal: v-305]
[pause: 0.45]
I: Ranking now takes 300 milliseconds.
I: What does the viewer get?
[pause: 1.2]
N: The feed service's deadline fires at 80 milliseconds for ranking, and it serves the merged timeline in time order.
[reveal: v-306]
[pause: 0.45]
N: The page is slightly worse and on time.
N: If you picked a box that is not on this list, good.
N: Write its probe down and answer it before you watch on.
[pause: 1.2]

[pause: 1.4]

## 6 Bridge

[slide: v-307]
[pause: 1.2]
V: It works. The question now is where it breaks first.
[pause: 1.8]

[slide: v-308]
[pause: 1.3]
C: The baseline with the attack points marked in red.
C: The fan-out workers, for the celebrity and for bursts.
C: The celebrity lists and the timelines, for the threshold, for duplicates and for a lost shard.
[reveal: v-309]
[pause: 0.45]
C: The feed service, for deletes and pagination.
C: And ranking, for its deadline.
C: Then a new kind of query, and the question of how we'd know.
C: Eight challenges, in an order where each fix creates the next question.
[pause: 1.1]

[pause: 1.4]

## 7 Challenges

[slide: v-310]
[pause: 1.2]
C: Each challenge runs the same way: the question, the naive answer, a case with numbers, where it breaks, the fix, why it works, then the interviewer pushes on the fix itself, and I say what I'd say in the room.
[pause: 1.8]

[pause: 1.4]

## 7.1 Challenge 1: The celebrity post

[slide: v-311]
[pause: 1.2]
N: Challenge one, the crux. Someone with a hundred million followers posts: what happens, write by write?
[pause: 1.8]

[slide: v-312]
[pause: 0.6]
I: Someone with a hundred million followers posts. Walk me through it.
[pause: 2.0]

[slide: v-313]
[pause: 1.3]
C: The naive answer:
[reveal: v-314]
[pause: 0.45]
C: the workers push it to every follower, and if that is slow we add workers.
[reveal: v-315]
[pause: 0.45]
C: Look at the red: the fan-out workers and the arrows into the timelines.
[reveal: v-316]
[pause: 0.45]
C: One post becomes a hundred million inserts, and the log partition holding it is blocked until they finish.
[pause: 1.1]

[slide: v-317]
[pause: 1.0]
C: The trace.
C: At eight o'clock a star with a hundred and ten million followers posts.
[reveal: v-318]
[pause: 0.45]
C: At the whole fleet's hundred and twenty thousand inserts a second, that takes about fifteen minutes.
[reveal: v-319]
[pause: 0.45]
C: Thirty seconds later, Ana posts to her three hundred friends, and her event waits behind the star's.
[reveal: v-320]
[pause: 0.45]
C: Her friends see it fourteen minutes late.
[reveal: v-321]
[pause: 0.45]
C: And the star posts again at half past.
[reveal: v-322]
[pause: 0.45]
C: Illustrative numbers, but the shape holds at any fleet size.
C: Even ten times the capacity spends ninety seconds of all of it on one post.
[pause: 1.0]

[slide: v-323]
[pause: 1.3]
C: The fix.
[reveal: v-324]
[pause: 0.45]
C: The event carries the author's tier.
[reveal: v-325]
[pause: 0.45]
C: Above the threshold the worker writes one entry to that author's recent list, the dashed arrow, and is done.
[reveal: v-326]
[pause: 0.45]
C: On the read path, the feed service merges the recent lists of the celebrities this reader follows.
C: One write instead of a hundred and ten million.
[reveal: v-327]
[pause: 0.45]
C: Rejected: Push to every follower for every author.
C: A 100-million-follower post is 100 million inserts, and everyone else waits behind them.
[pause: 1.1]

[slide: v-328]
[pause: 1.3]
C: As a sequence.
[reveal: v-329]
[pause: 0.45]
C: The star's event arrives with tier pull.
[reveal: v-330]
[pause: 0.45]
C: The worker appends the post I-D to the star's list: one write.
[reveal: v-331]
[pause: 0.45]
C: The partition is free again in milliseconds.
[reveal: v-332]
[pause: 0.45]
C: Later, a reader opens the feed.
[reveal: v-333]
[pause: 0.45]
C: The feed service reads the lists of the six celebrities this reader follows,
[reveal: v-334]
[pause: 0.45]
C: merges them with the timeline, and de-duplicates by post I-D.
[reveal: v-335]
[pause: 0.45]
C: One ranked feed.
[pause: 1.1]

[slide: v-336]
[pause: 1.0]
C: Why it works, in one table.
[reveal: v-337]
[pause: 0.45]
C: Pushing the celebrity costs a hundred and ten million inserts per post, paid by every other author in delay.
[reveal: v-338]
[pause: 0.45]
C: Pulling costs one write per post, and one small cache read per followed celebrity per open, paid by the reader inside the budget.
[reveal: v-339]
[pause: 0.45]
C: Those celebrity lists are hot keys, so they are replicated to many cache nodes.
[pause: 1.0]

[slide: v-340]
[pause: 0.6]
I: New Year's Eve. Ten times the normal posting rate, all ordinary accounts, for ten minutes.
[pause: 2.0]

[slide: v-341]
[pause: 0.6]
C: A burst of ordinary posts is a different problem: no single author is the issue, the volume is.
C: Three things.
C: Priority lanes: fan out to close-tie followers first, the rest after.
[reveal: v-342]
[pause: 0.45]
C: Partitioning by author, so the burst spreads across the fleet.
[reveal: v-343]
[pause: 0.45]
C: And lag measured per lane, so that while the general lane is behind, the read merge can pull recent posts from a reader's top ties.
[reveal: v-344]
[pause: 0.45]
C: The honest limit: for those ten minutes, the general one-minute target may slip.
C: Close friends keep their seconds.
[pause: 0.8]

[slide: v-345]
[pause: 0.7]
V: If asked, I'd say: one celebrity post would be a hundred million writes, minutes of fan-out that block everyone else. So above a follower threshold I don't fan out at all. The post goes into a small recent-posts list for that author, and each reader merges the few celebrities they follow at read time. That costs a few milliseconds per open, which I've budgeted.
[pause: 1.0]
N: That fix creates the next question: where exactly is the threshold?
[pause: 1.6]

[pause: 1.4]

## 7.2 Challenge 2: Where is the line, and who crosses it?

[slide: v-346]
[pause: 1.2]
N: Challenge two, the second half of the crux. Where exactly is the line, and what happens to an account that crosses it overnight?
[pause: 1.8]

[slide: v-347]
[pause: 0.6]
I: Where exactly is the threshold, and what happens to an account that crosses it?
[pause: 2.0]

[slide: v-348]
[pause: 1.3]
C: The naive answer is a round number: a million followers.
[reveal: v-349]
[pause: 0.45]
C: Look at the fan-out box and both of its outputs in red.
[reveal: v-350]
[pause: 0.45]
C: The routing decision rests on a number with no arithmetic behind it,
[reveal: v-351]
[pause: 0.45]
C: and no rule for what happens when an account crosses it.
[pause: 1.1]

[slide: v-352]
[pause: 1.0]
C: Three ways a fixed number fails.
[reveal: v-353]
[pause: 0.45]
C: At a million followers, one post is a million inserts, about eight seconds of the whole fleet, past the five-second target by itself.
[reveal: v-354]
[pause: 0.45]
C: Then an account goes viral: nine thousand followers on Monday, two million on Tuesday, with two hundred posts already pushed.
[reveal: v-355]
[pause: 0.45]
C: Which tier now, and what about the copies?
[reveal: v-356]
[pause: 0.45]
C: And a power reader follows five thousand accounts, three hundred of them celebrities: three hundred lists at half a millisecond each is a hundred and fifty milliseconds.
[pause: 1.0]

[slide: v-357]
[pause: 1.0]
C: The fix: derive the line from both sides, and use three tiers.
C: Push for authors under about ten thousand followers, to every follower active in thirty days.
[reveal: v-358]
[pause: 0.45]
C: A mid tier up to about a hundred thousand, pushed only to followers active in the last day, which cuts the cost by an order of magnitude.
[reveal: v-359]
[pause: 0.45]
C: And pull above that.
C: The write side says one post's fan-out must finish well inside five seconds on a fair share of the fleet.
[reveal: v-360]
[pause: 0.45]
C: The read side says the average reader should pull fewer than about twenty authors.
C: Start at ten thousand, measure, tune.
C: It is a config value, not a constant.
[reveal: v-361]
[pause: 0.45]
C: Rejected: One fixed follower-count threshold.
C: Accounts near the line flip between push and pull and get delivered twice or not at all.
[pause: 1.0]

[slide: v-362]
[pause: 1.3]
C: Crossing, as a sequence.
[reveal: v-363]
[pause: 0.45]
C: A tier job reads follower counts hourly.
[reveal: v-364]
[pause: 0.45]
C: Up at a hundred thousand, down only below fifty thousand, so an account near the line does not flap.
[reveal: v-365]
[pause: 0.45]
C: The new star is marked pull.
[reveal: v-366]
[pause: 0.45]
C: Its new posts become one write each.
[reveal: v-367]
[pause: 0.45]
C: Yesterday's pushed I-Ds stay in timelines and age out: no backfill, no removal.
[reveal: v-368]
[pause: 0.45]
C: And readers' merge shows the new posts from the first minute.
C: Crossing down works the same way in reverse.
[pause: 1.1]

[slide: v-369]
[pause: 1.3]
C: Why it works, on the baseline.
[reveal: v-370]
[pause: 0.45]
C: L-one and L-two both hold at the line, because the line was placed where both costs are acceptable.
[reveal: v-371]
[pause: 0.45]
C: And no transition needs a backfill, because the read path's merge covers the gap: whichever tier an author is in today, their recent posts are reachable.
[pause: 1.1]

[slide: v-372]
[pause: 0.6]
I: The power reader. Three hundred celebrities on every open.
[pause: 2.0]

[slide: v-373]
[pause: 0.6]
C: The power reader is the tail of readers, and gets the same treatment as the tail of authors.
C: For readers who pull more than about fifty authors, a background job merges their celebrity lists every few minutes into their timeline, so their open is one read again.
[reveal: v-374]
[pause: 0.45]
C: At read time, the live merge is capped at the top fifty celebrities by interaction.
[reveal: v-375]
[pause: 0.45]
C: The honest limit: for those readers, a celebrity's post may be a few minutes late.
C: I'd say that to product.
[pause: 0.8]

[slide: v-376]
[pause: 0.7]
V: If asked, I'd say: I set the line from both sides. One post's fan-out must finish inside the freshness target, and the average reader should pull only a handful of authors. That puts it around ten thousand followers, as a config value I'd tune with data. Crossing it needs no backfill, because the read merge covers recent posts. And the rare reader who follows hundreds of celebrities gets their merge precomputed.
[pause: 1.0]
N: The pull path now carries correctness weight. Next question: what about posts that must disappear?
[pause: 1.6]

[pause: 1.4]

## 7.3 Challenge 3: Delete, block, unfollow

[slide: v-377]
[pause: 1.2]
N: Challenge three. A post is deleted, or an author is blocked, while its I-D sits in millions of timelines: how does it disappear?
[pause: 1.8]

[slide: v-378]
[pause: 0.6]
I: A user deletes a post, or blocks someone. That post I-D is already in millions of timelines. How does it disappear?
[pause: 2.0]

[slide: v-379]
[pause: 1.3]
C: The naive answer: fan out a delete, removing the I-D from every timeline that has it.
[reveal: v-380]
[pause: 0.45]
C: Look at the timeline cache in red.
[reveal: v-381]
[pause: 0.45]
C: The I-D was copied millions of times,
[reveal: v-382]
[pause: 0.45]
C: and the delete has to chase every copy, at the same cost as the post, racing it.
[pause: 1.1]

[slide: v-383]
[pause: 1.0]
C: The trace.
C: Ana posts to three million followers and fan-out starts.
[reveal: v-384]
[pause: 0.45]
C: Forty seconds later she deletes it, a wrong photo, and a delete fan-out starts behind it.
[reveal: v-385]
[pause: 0.45]
C: Wherever the insert lands after the delete, the post stays.
[reveal: v-386]
[pause: 0.45]
C: Separately, Ben blocks Cal, and five hundred of Cal's posts are already in Ben's timeline.
[reveal: v-387]
[pause: 0.45]
C: Both violate S-one.
[pause: 1.0]

[slide: v-388]
[pause: 1.3]
C: The fix.
[reveal: v-389]
[pause: 0.45]
C: Correctness lives on the read path.
[reveal: v-390]
[pause: 0.45]
C: The delete writes the post's status once, and an invalidation event drops it from the post cache, the dashed arrow.
C: Every page is hydrated through that cache, and anything deleted or out of audience is dropped.
[reveal: v-391]
[pause: 0.45]
C: The merge drops authors in my block, mute and unfollow set, which the graph keeps small and cached.
C: A background job removes stale I-Ds from timelines later, and that cleanup is cosmetic.
[reveal: v-392]
[pause: 0.45]
C: Rejected: Deleting from every follower's timeline.
C: The delete fans out as wide as the post did; filtering on read makes cleanup cosmetic.
[pause: 1.1]

[slide: v-393]
[pause: 1.3]
C: As a sequence.
[reveal: v-394]
[pause: 0.45]
C: The author deletes: one write, status deleted.
[reveal: v-395]
[pause: 0.45]
C: The post cache is invalidated.
[reveal: v-396]
[pause: 0.45]
C: A reader opens the feed: the merge drops authors they block or unfollowed.
[reveal: v-397]
[pause: 0.45]
C: Hydration misses the cache, finds the row says deleted, and drops it.
[reveal: v-398]
[pause: 0.45]
C: Later, a cleanup job removes stale I-Ds.
[reveal: v-399]
[pause: 0.45]
C: The user never depended on it.
[pause: 1.1]

[slide: v-400]
[pause: 0.6]
I: The post-cache invalidation event is lost.
[pause: 2.0]

[slide: v-401]
[pause: 0.6]
C: Two backstops.
C: Post-cache entries have a lifetime of at most five minutes, so a lost event costs one lifetime, not forever.
[reveal: v-402]
[pause: 0.45]
C: And deletes and audience changes also write a small recently-removed set, which hydration checks for an hour.
C: That keeps the five-second bound even when the event is lost.
[reveal: v-403]
[pause: 0.45]
C: The honest limit: a post already rendered on someone's phone stays there until they refresh.
C: The next fetch removes it.
[pause: 0.8]

[slide: v-404]
[pause: 0.7]
V: If asked, I'd say: fanned-out I-Ds are copies, so I don't trust them. Every page is hydrated from the post itself and filtered by the reader's block and unfollow set, so a delete is one write that takes effect within seconds everywhere. Cleaning the I-Ds out of timelines is a background job, and it's cosmetic.
[pause: 1.0]
N: If correctness lives on the read path, the read path must also handle duplicates. Next.
[pause: 1.6]

[pause: 1.4]

## 7.4 Challenge 4: Twice, or never

[slide: v-405]
[pause: 1.2]
N: Challenge four. The interviewer said a duplicate is a bug and a missed close-friend post is worse: where does each come from?
[pause: 1.8]

[slide: v-406]
[pause: 0.6]
I: You said a duplicate on screen is a bug, and a missed close-friend post is worse. Where does each come from in your design?
[pause: 2.0]

[slide: v-407]
[pause: 1.3]
C: The naive answer: the log delivers exactly once.
[reveal: v-408]
[pause: 0.45]
C: It doesn't; it delivers at least once.
[reveal: v-409]
[pause: 0.45]
C: Two places break,
[reveal: v-410]
[pause: 0.45]
C: in red: the insert into the timeline, on re-delivery, and the page boundary on the way back to the reader.
[pause: 1.1]

[slide: v-411]
[pause: 1.0]
C: The trace.
C: Worker three inserts post nine into a thousand timelines and crashes before committing its offset.
[reveal: v-412]
[pause: 0.45]
C: Worker seven re-reads the event and inserts it again.
[reveal: v-413]
[pause: 0.45]
C: In a plain list, post nine is there twice.
[reveal: v-414]
[pause: 0.45]
C: Separately: a reader takes page one with offset zero, twelve new posts arrive at the top, and page two with offset fifty returns items the reader already saw.
[reveal: v-415]
[pause: 0.45]
C: Twelve repeated, and twelve others never shown.
[pause: 1.0]

[slide: v-416]
[pause: 1.0]
C: The fix is two small things.
C: The timeline is a sorted set keyed by post I-D, so a re-delivered insert changes nothing: at-least-once delivery, with an idempotent effect.
C: And pagination uses a cursor holding the last item's score and I-D.
C: The next page is everything strictly after that pair, whatever arrived at the top.
[reveal: v-417]
[pause: 0.45]
C: The read merge also de-duplicates across the timeline and the celebrity lists.
C: Duplicates become impossible by data structure.
C: Misses are bounded by fan-out lag, which I measure, and for close ties the pull covers a lagging lane.
C: Rejected: Exactly-once delivery from the broker alone.
C: The broker cannot see the timeline write; an idempotent insert gives the same result without it.
[pause: 1.0]

[slide: v-418]
[pause: 1.3]
C: As a sequence.
[reveal: v-419]
[pause: 0.45]
C: Worker three inserts and crashes.
[reveal: v-420]
[pause: 0.45]
C: Worker seven inserts the same post again:
[reveal: v-421]
[pause: 0.45]
C: the set is keyed by post I-D, no change.
[reveal: v-422]
[pause: 0.45]
C: The reader asks for the next page with a cursor holding score point eight two and post fifty-one,
[reveal: v-423]
[pause: 0.45]
C: and gets the next fifty strictly after it.
[pause: 1.1]

[slide: v-424]
[pause: 0.6]
I: Ranking reorders things between page one and page two.
[pause: 2.0]

[slide: v-425]
[pause: 0.6]
C: If ranking reorders between pages, scores in the cursor stop meaning anything.
C: So the first page's ranked candidate list, a few hundred I-Ds, is kept for the session with a short lifetime, and later pages walk that list instead of re-ranking.
[reveal: v-426]
[pause: 0.45]
C: New posts appear on refresh, which starts a new session.
[reveal: v-427]
[pause: 0.45]
C: That is the expected behaviour, and I'd say so.
[pause: 0.8]

[slide: v-428]
[pause: 0.7]
V: If asked, I'd say: fan-out is at-least-once, so inserts are idempotent: the timeline is keyed by post I-D. Pagination uses a cursor holding the last item's score and I-D, never an offset. And the ranked list for a session is kept, so page two doesn't reshuffle page one.
[pause: 1.0]
N: All of this assumes the timeline exists. Next: what if it doesn't?
[pause: 1.6]

[pause: 1.4]

## 7.5 Challenge 5: A timeline shard is gone

[slide: v-429]
[pause: 1.2]
N: Challenge five. A cache shard holding five million timelines disappears on a Sunday evening: what do those users see, and what stops the recovery from becoming the outage?
[pause: 1.8]

[slide: v-430]
[pause: 0.6]
I: A timeline cache shard is lost. One user in a hundred opens to an empty feed. What do they see, and how do you recover?
[pause: 2.0]

[slide: v-431]
[pause: 1.3]
C: The naive answer: restore the shard from a backup.
[reveal: v-432]
[pause: 0.45]
C: A backup of a cache is hours old and slow to load, and meanwhile users open the app.
[reveal: v-433]
[pause: 0.45]
C: Look at the red:
[reveal: v-434]
[pause: 0.45]
C: the timeline is gone, and the obvious recovery, rebuilding by pull, lands on the author indexes, which everyone's celebrity merge also depends on.
[pause: 1.1]

[slide: v-435]
[pause: 1.0]
C: The trace.
C: At eight, a shard with five million users' timelines is lost.
[reveal: v-436]
[pause: 0.45]
C: A fifth of them open within ten minutes: seventeen hundred rebuilds a second, each reading two hundred author indexes, three hundred and forty thousand reads a second.
[reveal: v-437]
[pause: 0.45]
C: The author index p-ninety-nine goes from five milliseconds to four hundred.
[reveal: v-438]
[pause: 0.45]
C: And every reader's celebrity merge waits on that same store.
[reveal: v-439]
[pause: 0.45]
C: One lost shard has become everyone's outage.
[pause: 1.0]

[slide: v-440]
[pause: 1.3]
C: The fix.
[reveal: v-441]
[pause: 0.45]
C: A timeline miss triggers a rebuild through the pull path, the same code as version one, and writes the result back.
C: The new rebuild box.
[reveal: v-442]
[pause: 0.45]
C: Requests are coalesced, so one user tapping three times starts one rebuild.
C: A global rate limit caps the load on the author indexes.
[reveal: v-443]
[pause: 0.45]
C: And anyone over the limit gets a degraded feed immediately: their celebrities plus the recent posts of their top twenty followees by interaction, marked for a full rebuild later.
[reveal: v-444]
[pause: 0.45]
C: Rejected: Replicating every timeline synchronously.
C: It doubles the write cost of 60,000 inserts a second for data we can rebuild.
[pause: 1.1]

[slide: v-445]
[pause: 1.3]
C: As a sequence.
[reveal: v-446]
[pause: 0.45]
C: The reader opens the feed,
[reveal: v-447]
[pause: 0.45]
C: the timeline is empty, the shard is lost.
[reveal: v-448]
[pause: 0.45]
C: The feed service asks the limiter for a rebuild token,
[reveal: v-449]
[pause: 0.45]
C: one in flight per user.
[reveal: v-450]
[pause: 0.45]
C: With a token: read the followees' recent posts, merge, write the timeline back.
[reveal: v-451]
[pause: 0.45]
C: Without one: a degraded feed right now, celebrities and top twenty followees.
[pause: 1.1]

[slide: v-452]
[pause: 1.3]
C: Why it works, as a curve. Unlimited, rebuilds spike to seventeen hundred a second and the author indexes fall over. Limited to five hundred a second, a hundred thousand reads a second, the store stays healthy, the rebuilds take longer, and the users waiting get a degraded but instant feed. The limit, not the number of users, decides the blast radius.
[pause: 1.1]

[slide: v-453]
[pause: 0.6]
I: It's not a shard. It's the whole timeline cluster in one region.
[pause: 2.0]

[slide: v-454]
[pause: 0.6]
C: A whole cluster in one region.
C: Serve that region's reads from another region's timeline replica, a few seconds stale, while the local one warms.
[reveal: v-455]
[pause: 0.45]
C: Without a replica, the degraded feed for everyone.
[reveal: v-456]
[pause: 0.45]
C: Then rebuild at the rate limit, most active users first.
[reveal: v-457]
[pause: 0.45]
C: The honest limit: a cold region takes hours to warm fully.
C: That is a recovery time I'd write down, and the business case for cross-region replicas of the timeline tier.
[pause: 0.8]

[slide: v-458]
[pause: 0.7]
V: If asked, I'd say: a timeline is a derived view, so losing it is a latency problem, not data loss. The first open rebuilds it by pull, with coalescing per user and a rate limit, and anyone over the limit gets a degraded but instant feed. The rate limit is what stops one lost shard from overloading the author index for everyone.
[pause: 1.0]
N: The degraded feed skipped one stage on purpose. Next: what if that stage is the slow one?
[pause: 1.6]

[pause: 1.4]

## 7.6 Challenge 6: The ranker takes 300 ms

[slide: v-459]
[pause: 1.2]
N: Challenge six. The biggest piece of the read budget belongs to another team, and today it is slow.
[pause: 1.8]

[slide: v-460]
[pause: 0.6]
I: Ranking has eighty milliseconds of your budget. Today it takes three hundred. What's your plan? And the ranking team wants a hundred and twenty for a better model.
[pause: 2.0]

[slide: v-461]
[pause: 1.3]
C: The naive answer: wait for it, because quality matters.
[reveal: v-462]
[pause: 0.45]
C: Look at the arrow into ranking, in red.
[reveal: v-463]
[pause: 0.45]
C: If the feed waits,
[reveal: v-464]
[pause: 0.45]
C: the feed's latency is ranking's latency, and ranking belongs to another team with another release schedule.
[pause: 1.1]

[slide: v-465]
[pause: 1.0]
C: The trace.
C: At two, ranking ships a new model and its p-ninety-nine goes from seventy to three hundred milliseconds.
[reveal: v-466]
[pause: 0.45]
C: The feed's p-ninety-nine goes from a hundred and sixty to four hundred and twenty.
[reveal: v-467]
[pause: 0.45]
C: Open rate drops, and nothing in the feed service changed.
[reveal: v-468]
[pause: 0.45]
C: Separately, the ranking team's next model lifts engagement, but needs a hundred and twenty milliseconds.
[pause: 1.0]

[slide: v-469]
[pause: 1.3]
C: The fix, on both boxes.
[reveal: v-470]
[pause: 0.45]
C: The feed service calls ranking with a deadline of eighty milliseconds.
[reveal: v-471]
[pause: 0.45]
C: On a miss, it orders by recency plus close ties, or reuses this session's last ranking.
C: Late scores are dropped and counted, and the response carries the fallback flag.
[reveal: v-472]
[pause: 0.45]
C: The feed degrades instead of failing.
[reveal: v-473]
[pause: 0.45]
C: Rejected: Waiting for ranking however long it takes.
C: The feed's p99 would become the ranker's p99; a deadline and a fallback cap it.
[pause: 1.1]

[slide: v-474]
[pause: 1.3]
C: As a sequence.
C: Score two hundred, deadline eighty.
[reveal: v-475]
[pause: 0.45]
C: Eighty milliseconds pass with no answer.
[reveal: v-476]
[pause: 0.45]
C: Fallback: recency plus close ties.
[reveal: v-477]
[pause: 0.45]
C: Hydrate the top fifty.
[reveal: v-478]
[pause: 0.45]
C: The feed returns in a hundred and forty milliseconds, flagged fallback.
[reveal: v-479]
[pause: 0.45]
C: When ranking's late answer arrives, it is dropped and counted.
[pause: 1.1]

[slide: v-480]
[pause: 1.0]
C: Now the hundred and twenty milliseconds.
C: I wouldn't move the user's deadline.
[reveal: v-481]
[pause: 0.45]
C: Options, each with a cost.
C: Pre-rank on app background or prefetch, so the slow model runs before the open: costs compute on opens that never happen.
[reveal: v-482]
[pause: 0.45]
C: Rank the first twenty fast and the rest asynchronously: a two-stage contract.
[reveal: v-483]
[pause: 0.45]
C: Or find forty milliseconds elsewhere in the budget first.
[reveal: v-484]
[pause: 0.45]
N: Negotiating a shared budget with options and costs is the signal here.
[pause: 1.0]

[slide: v-485]
[pause: 0.6]
I: The fallback rate is thirty percent for a week, and nobody noticed.
[pause: 2.0]

[slide: v-486]
[pause: 0.6]
C: A fallback is only safe if someone notices it.
C: The fallback rate becomes ranking's service level indicator, with an error budget, say under one percent of opens, and ranking is paged on it.
[reveal: v-487]
[pause: 0.45]
C: And a model push that breaks that budget on its canary is rolled back automatically.
[reveal: v-488]
[pause: 0.45]
C: That is a metric about quality, not uptime.
C: Challenge eight is about exactly that.
[pause: 0.8]

[slide: v-489]
[pause: 0.7]
V: If asked, I'd say: ranking gets a hard deadline inside the two hundred milliseconds. If it misses, I rank by recency and close ties, so the feed degrades instead of failing. For a slower model, I'd find the budget by pre-ranking before the open, not by moving the user's deadline. And the fallback rate is a number someone owns.
[pause: 1.0]
N: So far the feed answered its one query. Next: product asks a different one.
[pause: 1.6]

[pause: 1.4]

## 7.7 Challenge 7: Catch up on the last 48 hours

[slide: v-490]
[pause: 1.2]
N: Challenge seven, a new requirement mid-round. Product wants a chronological view of everything from the last two days: does the design absorb it?
[pause: 1.8]

[slide: v-491]
[pause: 0.6]
I: Product adds catch up: a chronological view of everything from the last forty-eight hours, for any user. What changes?
[pause: 2.0]

[slide: v-492]
[pause: 1.3]
C: The naive answer: make the timelines longer and keep them in time order.
[reveal: v-493]
[pause: 0.45]
C: Look at the timeline in red.
[reveal: v-494]
[pause: 0.45]
C: It is bounded at five hundred, it is ranked, it never held the celebrities, and inactive users were skipped by fan-out.
[reveal: v-495]
[pause: 0.45]
C: It doesn't hold the answer, and stretching it doubles the memory bill for everyone.
[pause: 1.1]

[slide: v-496]
[pause: 1.0]
C: The case, as a table.
C: Catch-up needs every post from my followees in forty-eight hours, perhaps two thousand.
[reveal: v-497]
[pause: 0.45]
C: The timeline holds at most five hundred.
C: It needs time order; the timeline is ranked.
[reveal: v-498]
[pause: 0.45]
C: It needs celebrities; they were never in it.
[reveal: v-499]
[pause: 0.45]
C: And a returning user has no timeline at all.
[pause: 1.0]

[slide: v-500]
[pause: 1.3]
C: The fix: go to the source of truth.
[reveal: v-501]
[pause: 0.45]
C: Catch-up merges the followees' author indexes for the window, the green arrow from the feed service to the posts store.
[reveal: v-502]
[pause: 0.45]
C: It is the same pull path as the rebuild.
C: In time order, paginated by time and post I-D, filtered by the same visibility rules, and cached per user for ten minutes.
[reveal: v-503]
[pause: 0.45]
C: The ranked feed is untouched.
[reveal: v-504]
[pause: 0.45]
C: Rejected: A larger timeline: 2,000 IDs per user.
C: It multiplies memory by four for the rare returning user, who is better served by a pull.
[pause: 1.1]

[slide: v-505]
[pause: 1.3]
C: As a sequence.
[reveal: v-506]
[pause: 0.45]
C: Get catch-up for forty-eight hours.
[reveal: v-507]
[pause: 0.45]
C: Is there a cached result for this user?
[reveal: v-508]
[pause: 0.45]
C: A miss.
[reveal: v-509]
[pause: 0.45]
C: For each followee, posts since forty-eight hours ago, the rebuild path.
[reveal: v-510]
[pause: 0.45]
C: Merge by time, filter, page by time and I-D.
[reveal: v-511]
[pause: 0.45]
C: Store for ten minutes.
C: Return the first fifty and a cursor.
[pause: 1.1]

[slide: v-512]
[pause: 0.6]
I: It becomes the most used screen.
[pause: 2.0]

[slide: v-513]
[pause: 0.6]
C: If catch-up becomes the most used screen, it earns its own materialised view: a per-user chronological list maintained by the same fan-out event, I-Ds only, with a forty-eight hour lifetime, and celebrities merged at read as before.
[reveal: v-514]
[pause: 0.45]
C: Its price, said first: it roughly doubles timeline memory for the users who use it.
C: I'd measure the load on the author indexes before paying it.
[reveal: v-515]
[pause: 0.45]
C: Either way, the design absorbed the requirement with a new reader of the same data, not a rebuild.
[pause: 0.8]

[slide: v-516]
[pause: 0.7]
V: If asked, I'd say: I wouldn't distort the ranked timeline for a query it wasn't designed for. Catch-up reads the source of truth, the followees' author indexes for the window, through the same path I use for rebuilds, and caches the result for minutes. If it becomes popular, it gets its own small view, and I'd say what that costs first.
[pause: 1.0]
N: Last challenge, and always the last one: how would you know any of this broke?
[pause: 1.6]

[pause: 1.4]

## 7.8 Challenge 8: How would you know the feed got worse?

[slide: v-517]
[pause: 1.2]
N: Challenge eight. The feed is up and fast. How would you know it had silently got worse?
[pause: 1.8]

[slide: v-518]
[pause: 0.6]
I: The feed is up and fast. How would you know it had silently got worse?
[pause: 2.0]

[slide: v-519]
[pause: 1.3]
C: The naive answer: error rate and latency.
[reveal: v-520]
[pause: 0.45]
C: Both measure boxes.
[reveal: v-521]
[pause: 0.45]
C: The promise to the user is different: your friends' posts show up within seconds, and the feed is good.
[reveal: v-522]
[pause: 0.45]
C: A routing bug in the fan-out box, in red, can break that promise with every box green.
[pause: 1.1]

[slide: v-523]
[pause: 1.0]
C: The trace.
C: A change to the tier job marks thirty percent of mid-tier authors as pull, by mistake.
[reveal: v-524]
[pause: 0.45]
C: No errors.
[reveal: v-525]
[pause: 0.45]
C: Latency unchanged.
[reveal: v-526]
[pause: 0.45]
C: Their posts now reach followers only through the read merge, and the merge lists only true celebrities, so they are never shown.
[reveal: v-527]
[pause: 0.45]
C: Engagement drifts down two percent over a week, and a product manager is the one who notices.
[pause: 1.0]

[slide: v-528]
[pause: 1.3]
C: The fix.
[reveal: v-529]
[pause: 0.45]
C: Measure the promise.
[reveal: v-530]
[pause: 0.45]
C: Synthetic authors, one in every tier, post every minute through the real path.
C: Synthetic followers open the feed and time the post's arrival.
[reveal: v-531]
[pause: 0.45]
C: That is the freshness indicator, per tier, with a target of five seconds at p-ninety-five.
C: In this case, the mid-tier probe stops arriving within minutes of the change.
[reveal: v-532]
[pause: 0.45]
C: Rejected: Dashboards of CPU and error rate.
C: Every box can be green while a post takes ten minutes to appear; probe post to visible.
[pause: 1.1]

[slide: v-533]
[pause: 1.3]
C: As a sequence.
[reveal: v-534]
[pause: 0.45]
C: The synthetic author posts, one per tier.
[reveal: v-535]
[pause: 0.45]
C: Fan-out delivers it by the real path.
[reveal: v-536]
[pause: 0.45]
C: The synthetic follower opens the feed every five seconds until the post appears, and reports post-to-visible time per tier.
[reveal: v-537]
[pause: 0.45]
C: Mid tier not visible after five minutes: page, with the tier named.
[pause: 1.1]

[slide: v-538]
[pause: 1.0]
C: Then read metrics in pairs.
C: Fan-out lag up with the post rate flat: workers are slow, not traffic.
[reveal: v-539]
[pause: 0.45]
C: Freshness bad for one tier with lag flat: a routing bug, this case.
[reveal: v-540]
[pause: 0.45]
C: Fallback up with ranking's latency normal: a misconfigured deadline.
[reveal: v-541]
[pause: 0.45]
C: Author-index reads up with the timeline hit rate down: a rebuild wave.
[reveal: v-542]
[pause: 0.45]
C: Engagement down with everything else normal: a model change, and ranking's to own.
[reveal: v-543]
[pause: 0.45]
C: And quality metrics, not uptime: empty-feed rate, fallback rate, the share of items from close ties, and engagement per session against its seasonal baseline.
[pause: 1.0]

[slide: v-544]
[pause: 0.6]
I: Finance says the timeline tier's memory bill doubled while users grew ten percent.
[pause: 2.0]

[slide: v-545]
[pause: 1.0]
C: Cost is observable too.
[reveal: v-546]
[pause: 0.45]
C: Memory per active user, the share of inserts going to inactive users, and entries per timeline.
[reveal: v-547]
[pause: 0.45]
C: Usually something drifted: the bound crept up, the active cut-off was widened, or the mid tier is pushing to everyone.
[reveal: v-548]
[pause: 0.45]
C: Find what grew, then pull the lever.
C: Five hundred entries to three hundred saves forty percent of memory if nobody scrolls that far.
C: Don't buy a bigger cluster first.
[pause: 1.0]

[slide: v-549]
[pause: 0.7]
V: If asked, I'd say: I measure the promise, not the servers. Synthetic accounts in every tier post and read every minute, so I know post-to-visible time per tier. Then quality signals, empty feeds, ranking fallbacks, engagement against its baseline, catch the feed that works but got worse. And I read metrics in pairs to find the cause.
[pause: 1.6]

[pause: 1.4]

## 8 Build cost

[slide: v-550]
[pause: 1.2]
C: The build cost. This is the manager layer, marked auxiliary: a Staff candidate can skip it, an engineering manager should not.
[pause: 1.8]

[slide: v-551]
[pause: 1.0]
C: Sequenced by measured load.
C: The first version is pull with a per-reader cache: about four engineers, one quarter.
[reveal: v-552]
[pause: 0.45]
C: It is right until the merge on a miss breaks the budget.
C: Then push: two teams, a quarter.
[reveal: v-553]
[pause: 0.45]
C: Then the hybrid, the filter, the deadline, the rebuild path and the probes: two or three teams, two quarters.
[reveal: v-554]
[pause: 0.45]
C: Illustrative numbers; the order is the point.
[pause: 1.0]

[slide: v-555]
[pause: 1.0]
C: The migration from pull to push, with no downtime.
C: Weeks one to four, build fan-out and timelines beside the pull path, read by nothing.
[reveal: v-556]
[pause: 0.45]
C: Weeks five to eight, shadow: write timelines, keep serving pull, and compare the two feeds per user.
[reveal: v-557]
[pause: 0.45]
C: Weeks nine to eleven, switch by cohort, one percent, ten, fifty, all, with rollback by cohort.
[reveal: v-558]
[pause: 0.45]
C: Then pull stays, as the rebuild and catch-up path.
[pause: 1.0]

[slide: v-559]
[pause: 0.6]
C: Three teams along the data.
C: Publish and graph, owning the post-created event.
[reveal: v-560]
[pause: 0.45]
C: Fan-out and timelines, owning the timeline entry format.
[reveal: v-561]
[pause: 0.45]
C: Feed serving, owning the rank call with its deadline.
[reveal: v-562]
[pause: 0.45]
C: On-call is on freshness and feed latency, and ranking's fallback rate pages the ranking team.
[pause: 0.8]

[slide: v-563]
[pause: 1.0]
C: Money.
[reveal: v-564]
[pause: 0.45]
C: Two lines dominate: timeline memory, about twelve terabytes of RAM with replicas, and fan-out writes.
[reveal: v-565]
[pause: 0.45]
C: The biggest lever on both is skipping inactive users, roughly half.
[reveal: v-566]
[pause: 0.45]
C: Then the threshold and the timeline bound.
[reveal: v-567]
[pause: 0.45]
C: The top risks: a threshold set once and never measured, a rebuild path never load-tested, and ranking's budget renegotiated every release instead of owned.
[pause: 1.0]

[pause: 1.4]

## 9 Recap

[slide: v-568]
[pause: 1.2]
C: The recap. One picture, a sentence per path, the common mistakes, and the thesis.
[pause: 1.8]

[slide: v-569]
[pause: 1.3]
C: The final design on the baseline.
[reveal: v-570]
[pause: 0.45]
C: The write path along the top:
[reveal: v-571]
[pause: 0.45]
C: post service,
[reveal: v-572]
[pause: 0.45]
C: one transaction, the event log, fan-out by tier.
[reveal: v-573]
[pause: 0.45]
C: In the middle,
[reveal: v-574]
[pause: 0.45]
C: the graph, the celebrity lists and the timelines.
[reveal: v-575]
[pause: 0.45]
C: Along the bottom,
[reveal: v-576]
[pause: 0.45]
C: the feed service,
[reveal: v-577]
[pause: 0.45]
C: ranking with a deadline and the post cache.
[reveal: v-578]
[pause: 0.45]
C: And the parts that only show up when something goes wrong:
[reveal: v-579]
[pause: 0.45]
C: invalidation,
[reveal: v-580]
[pause: 0.45]
C: the rebuild path,
[reveal: v-581]
[pause: 0.45]
C: catch-up,
[reveal: v-582]
[pause: 0.45]
C: and the synthetic users that tell us the promise holds.
[pause: 1.1]

[slide: v-583]
[pause: 1.0]
C: Four paths, one sentence each.
C: Publish: one transaction and an event, then push I-Ds to active followers, or one write for a celebrity.
[reveal: v-584]
[pause: 0.45]
C: Read: one timeline and a few celebrity lists, filtered, ranked under a deadline, fifty hydrated, and a cursor.
[reveal: v-585]
[pause: 0.45]
C: Remove: one write to the post, enforced on every page.
[reveal: v-586]
[pause: 0.45]
C: Rebuild: pull, coalesced and rate-limited, degraded beyond the limit.
[pause: 1.0]

[slide: v-587]
[pause: 0.6]
C: The common mistakes.
C: Picking push or pull and defending it.
C: Bodies in timelines.
C: No number on the threshold.
[reveal: v-588]
[pause: 0.45]
C: Strong consistency for a feed.
C: Chasing deletes into copies, offsets for pagination, and exactly-once fan-out.
[reveal: v-589]
[pause: 0.45]
C: Ranking with no deadline, no plan for a lost shard, and watching uptime instead of freshness.
[reveal: v-590]
[pause: 0.45]
C: And going deep on the ranking model, or never asking about the follower distribution.
[pause: 0.8]

[slide: v-591]
[pause: 1.0]
C: The eight challenges in a phrase each.
C: Pull the celebrity.
[reveal: v-592]
[pause: 0.45]
C: Set the line from both sides.
[reveal: v-593]
[pause: 0.45]
C: Filter on read.
[reveal: v-594]
[pause: 0.45]
C: Idempotent inserts and a cursor.
[reveal: v-595]
[pause: 0.45]
C: Rebuild by pull, limited and degraded.
[reveal: v-596]
[pause: 0.45]
C: A deadline with an owner.
[reveal: v-597]
[pause: 0.45]
C: The source of truth for a new query.
[reveal: v-598]
[pause: 0.45]
C: And probes that measure the promise.
[pause: 1.0]

[slide: v-599]
[pause: 0.7]
V: It's a hybrid: post I-Ds pushed into bounded timelines for ordinary accounts, celebrities pulled at read time, with the line set by arithmetic and tuned with data. Correctness lives on the read path, so a delete is one write. I traded strict freshness for seconds of eventual consistency, and every degraded mode, slow ranking or a lost shard, has a fallback and a metric.
[pause: 2.0]
