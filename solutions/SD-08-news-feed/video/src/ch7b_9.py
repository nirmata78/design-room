from dsl import *

K = lambda n, t: f"Challenge {n} of 8 · {t}"

# ───────── Challenge 5 · a lost shard ─────────
subchapter("7.5", "Challenge 5: A timeline shard is gone", ["N: Challenge five. A cache shard holding five million timelines disappears on a Sunday evening: what do those users see, and what stops the recovery from becoming the outage?"])
qs("Interviewer · challenge 5 of 8", "“A timeline cache shard is lost. One user in a hundred opens to an empty feed. What do they see, and how do you recover?”", [
 "I: A timeline cache shard is lost. One user in a hundred opens to an empty feed. What do they see, and how do you recover?", "[pause: 2.0]"])

S(dia(K(5, "a lost shard"), "An empty timeline, and a recovery that can spread", "ch5-attack", q=True, red=True,
      extra=strip(("case", "Naive answer", "“Restore it from a backup.”"),
                  ("case", "Break", "The timeline shard, then the author indexes everyone's celebrity merge depends on."))), [
 "C: The naive answer: restore the shard from a backup. A backup of a cache is hours old and slow to load, and meanwhile users open the app. Look at the red: the timeline is gone, and the obvious recovery, rebuilding by pull, lands on the author indexes, which everyone's celebrity merge also depends on."], cls="dia")

S(plain(K(5, "the trace"), "The recovery becomes the outage", '<pre class="trace"><span class="t">20:00</span>a shard with 5 M users\' timelines is lost\n<span class="t">20:00</span>20 % open within 10 min: 1,700 rebuilds/s × 200 author reads = <span class="bad">340,000 reads/s</span>\n<span class="t">20:02</span>author-index p99 goes from 5 ms to <span class="bad">400 ms</span>\n<span class="t">20:03</span>every reader\'s celebrity merge waits on the same store: <span class="bad">feed p99 breaks for everyone</span></pre>' +
  '<div class="hedge"><b class="t">Label the numbers</b>Illustrative. The shape: a derived store lost, and its rebuild aimed at a store sized for something else.</div>', q=True, red=True), [
 "C: The trace. At eight, a shard with five million users' timelines is lost. A fifth of them open within ten minutes: seventeen hundred rebuilds a second, each reading two hundred author indexes, three hundred and forty thousand reads a second. The author index p-ninety-nine goes from five milliseconds to four hundred. And every reader's celebrity merge waits on that same store. One lost shard has become everyone's outage."])

S(dia(K(5, "the fix"), "Rebuild by pull, coalesced, rate-limited, degraded beyond the limit", "ch5-fix",
      extra=strip(("fixb", "Mechanism", "A miss triggers a rebuild through the pull path, written back to the cache. One rebuild in flight per user. A global rebuild rate limit. Over it: a degraded feed now, a rebuild later."),
                  ("whyb", "Property", "L3 for the lost users, L2 for everyone else. The blast radius is set by the rate limit, not by how many users open."))), [
 "C: The fix. A timeline miss triggers a rebuild through the pull path, the same code as version one, and writes the result back. The new rebuild box. Requests are coalesced, so one user tapping three times starts one rebuild. A global rate limit caps the load on the author indexes. And anyone over the limit gets a degraded feed immediately: their celebrities plus the recent posts of their top twenty followees by interaction, marked for a full rebuild later."], cls="dia")

S(dia(K(5, "sequence"), "A token for each rebuild; a degraded feed without one", "seq-rebuild"), [
 "C: As a sequence. The reader opens the feed, the timeline is empty, the shard is lost. The feed service asks the limiter for a rebuild token, one in flight per user. With a token: read the followees' recent posts, merge, write the timeline back. Without one: a degraded feed right now, celebrities and top twenty followees."], cls="dia")

S(dia(K(5, "why it works"), "The limit decides the blast radius", "rebuild-wave"), [
 "C: Why it works, as a curve. Unlimited, rebuilds spike to seventeen hundred a second and the author indexes fall over. Limited to five hundred a second, a hundred thousand reads a second, the store stays healthy, the rebuilds take longer, and the users waiting get a degraded but instant feed. The limit, not the number of users, decides the blast radius."], cls="dia")

qs("Interviewer · the second-level push", "“It's not a shard. It's the whole timeline cluster in one region.”", [
 "I: It's not a shard. It's the whole timeline cluster in one region.", "[pause: 2.0]"])

S(plain(K(5, "the second fix, and the honest limit"), "Another region's copy, or degraded for everyone", '<div class="cards c3">'
  '<div class="cd grn"><h3>Cross-region replica</h3><p>Serve that region\'s reads from another region\'s timeline replica, seconds stale, while it warms.</p></div>'
  '<div class="cd amb"><h3>Degraded mode</h3><p>If there is no replica: the degraded feed for everyone, served instantly.</p></div>'
  '<div class="cd"><h3>Warm by activity</h3><p>Rebuild at the rate limit, most active users first.</p></div></div>' +
  line("Honest limit: a cold region takes hours to warm fully. That is a stated recovery time, and the case for replicas.", "r")), [
 "C: A whole cluster in one region. Serve that region's reads from another region's timeline replica, a few seconds stale, while the local one warms. Without a replica, the degraded feed for everyone. Then rebuild at the rate limit, most active users first.",
 "C: The honest limit: a cold region takes hours to warm fully. That is a recovery time I'd write down, and the business case for cross-region replicas of the timeline tier."])

say_slide("“A timeline is a derived view, so losing it is a latency problem, not data loss. The first open rebuilds it by pull, with coalescing per user and a rate limit, and anyone over the limit gets a degraded but instant feed. The rate limit is what stops one lost shard from overloading the author index for everyone.”", [
 "V: If asked, I'd say: a timeline is a derived view, so losing it is a latency problem, not data loss. The first open rebuilds it by pull, with coalescing per user and a rate limit, and anyone over the limit gets a degraded but instant feed. The rate limit is what stops one lost shard from overloading the author index for everyone.", "[pause: 1.0]",
 "N: The degraded feed skipped one stage on purpose. Next: what if that stage is the slow one?"])

# ───────── Challenge 6 · the ranker is slow ─────────
subchapter("7.6", "Challenge 6: The ranker takes 300 ms", ["N: Challenge six. The biggest piece of the read budget belongs to another team, and today it is slow."])
qs("Interviewer · challenge 6 of 8", "“Ranking has 80 ms of your budget. Today it takes 300. What's your plan? And the ranking team wants 120 ms for a better model.”", [
 "I: Ranking has eighty milliseconds of your budget. Today it takes three hundred. What's your plan? And the ranking team wants a hundred and twenty for a better model.", "[pause: 2.0]"])

S(dia(K(6, "a slow dependency"), "The feed waits for a component it does not own", "ch6-attack", q=True, red=True,
      extra=strip(("case", "Naive answer", "“Wait for it. Quality matters.”"),
                  ("case", "Break", "The call to ranking: the feed's latency becomes ranking's latency."))), [
 "C: The naive answer: wait for it, because quality matters. Look at the arrow into ranking, in red. If the feed waits, the feed's latency is ranking's latency, and ranking belongs to another team with another release schedule."], cls="dia")

S(plain(K(6, "the trace"), "A model push breaks the feed", '<pre class="trace"><span class="t">14:00</span>ranking ships a new model; its p99 goes from 70 ms to <span class="bad">300 ms</span>\n<span class="t">14:00</span>feed p99 goes from 160 ms to <span class="bad">420 ms</span>\n<span class="t">14:30</span>open rate down; nothing in the feed service changed\n<span class="t">ask  </span>the next model lifts engagement, at <span class="bad">120 ms p99</span></pre>', q=True, red=True), [
 "C: The trace. At two, ranking ships a new model and its p-ninety-nine goes from seventy to three hundred milliseconds. The feed's p-ninety-nine goes from a hundred and sixty to four hundred and twenty. Open rate drops, and nothing in the feed service changed. Separately, the ranking team's next model lifts engagement, but needs a hundred and twenty milliseconds."])

S(dia(K(6, "the fix"), "A hard deadline, and a fallback that is counted", "ch6-fix",
      extra=strip(("fixb", "Mechanism", "Call ranking with deadline 80 ms. On a miss: recency plus close ties, or the session's last ranking. Late scores are dropped and counted; the response says fallback."),
                  ("whyb", "Property", "L2: the feed's latency no longer depends on a component it does not own. Quality loss is bounded and visible."))), [
 "C: The fix, on both boxes. The feed service calls ranking with a deadline of eighty milliseconds. On a miss, it orders by recency plus close ties, or reuses this session's last ranking. Late scores are dropped and counted, and the response carries the fallback flag. The feed degrades instead of failing."], cls="dia")

S(dia(K(6, "sequence"), "Eighty milliseconds, then the fallback", "seq-rank"), [
 "C: As a sequence. Score two hundred, deadline eighty. Eighty milliseconds pass with no answer. Fallback: recency plus close ties. Hydrate the top fifty. The feed returns in a hundred and forty milliseconds, flagged fallback. When ranking's late answer arrives, it is dropped and counted."], cls="dia")

S(plain(K(6, "the 120 ms request"), "Find the budget; don't move the user's deadline", table(["Option", "What it costs"], [
  ["Pre-rank on app background or prefetch, so the slow model runs before the open", "compute on opens that never happen"],
  ["Rank the first 20 fast, the rest asynchronously", "a two-stage ranking contract"],
  ["Give 120 ms if hydration and lookups shrink by 40 ms", "work in the feed team first"],
  ["Say yes and move the p99 to 240 ms", "every user pays, for a model gain on some"]], "bt sm") +
  grade("Negotiating a budget with another team, with options and their costs, is the Staff signal here.")), [
 "C: Now the hundred and twenty milliseconds. I wouldn't move the user's deadline. Options, each with a cost. Pre-rank on app background or prefetch, so the slow model runs before the open: costs compute on opens that never happen. Rank the first twenty fast and the rest asynchronously: a two-stage contract. Or find forty milliseconds elsewhere in the budget first.",
 "N: Negotiating a shared budget with options and costs is the signal here."])

qs("Interviewer · the second-level push", "“The fallback rate is thirty percent for a week, and nobody noticed.”", [
 "I: The fallback rate is thirty percent for a week, and nobody noticed.", "[pause: 2.0]"])

S(plain(K(6, "the second fix"), "The fallback rate has an owner", '<div class="cards c2">'
  '<div class="cd grn"><h3>An SLI with an owner</h3><p>Fallback rate is ranking\'s SLI, with an error budget: say under 1 % of opens. Ranking is paged on it, not the feed team.</p></div>'
  '<div class="cd grn"><h3>Automatic rollback</h3><p>A model push that breaks the fallback budget on its canary is rolled back by the deploy system.</p></div></div>' +
  line("That is a metric about quality, not uptime. Challenge eight is about exactly that.", "a")), [
 "C: A fallback is only safe if someone notices it. The fallback rate becomes ranking's service level indicator, with an error budget, say under one percent of opens, and ranking is paged on it. And a model push that breaks that budget on its canary is rolled back automatically.",
 "C: That is a metric about quality, not uptime. Challenge eight is about exactly that."])

say_slide("“Ranking gets a hard deadline inside the two hundred milliseconds, and if it misses, I rank by recency and close ties, so the feed degrades instead of failing. For a slower model, I'd find the budget by pre-ranking before the open, not by moving the user's deadline. And the fallback rate is a number someone owns.”", [
 "V: If asked, I'd say: ranking gets a hard deadline inside the two hundred milliseconds. If it misses, I rank by recency and close ties, so the feed degrades instead of failing. For a slower model, I'd find the budget by pre-ranking before the open, not by moving the user's deadline. And the fallback rate is a number someone owns.", "[pause: 1.0]",
 "N: So far the feed answered its one query. Next: product asks a different one."])

# ───────── Challenge 7 · catch up on 48 hours ─────────
subchapter("7.7", "Challenge 7: Catch up on the last 48 hours", ["N: Challenge seven, a new requirement mid-round. Product wants a chronological view of everything from the last two days: does the design absorb it?"])
qs("Interviewer · challenge 7 of 8", "“Product adds ‘catch up’: a chronological view of everything from the last 48 hours, for any user. What changes?”", [
 "I: Product adds catch up: a chronological view of everything from the last forty-eight hours, for any user. What changes?", "[pause: 2.0]"])

S(dia(K(7, "a new query"), "The view does not hold the answer", "ch7-attack", q=True, red=True,
      extra=strip(("case", "Naive answer", "“Make the timelines longer and order them by time.”"),
                  ("case", "Break", "The timeline: bounded, ranked, missing celebrities and inactive users."))), [
 "C: The naive answer: make the timelines longer and keep them in time order. Look at the timeline in red. It is bounded at five hundred, it is ranked, it never held the celebrities, and inactive users were skipped by fan-out. It doesn't hold the answer, and stretching it doubles the memory bill for everyone."], cls="dia")

S(plain(K(7, "the case"), "Why the view can't answer it", table(["Needed for catch-up", "What the timeline has"], [
  ["every post from followees in 48 h: maybe 2,000", "at most 500 IDs"],
  ["time order", "ranked order"],
  ["celebrities' posts", "none: they are pulled"],
  ["a returning user's posts", "nothing: inactive users were skipped"]], "bt sm")), [
 "C: The case, as a table. Catch-up needs every post from my followees in forty-eight hours, perhaps two thousand. The timeline holds at most five hundred. It needs time order; the timeline is ranked. It needs celebrities; they were never in it. And a returning user has no timeline at all."])

S(dia(K(7, "the fix"), "Go to the source of truth, not into the cache", "ch7-fix",
      extra=strip(("fixb", "Mechanism", "Catch-up merges the followees' author indexes for the window, the same pull path as the rebuild, in time order, filtered by the same visibility rules, cached per user for minutes."),
                  ("whyb", "Why it works", "The ranked view keeps its bounds and its cost. The new query costs what it costs, once per use, where its data lives."))), [
 "C: The fix: go to the source of truth. Catch-up merges the followees' author indexes for the window, the green arrow from the feed service to the posts store. It is the same pull path as the rebuild. In time order, paginated by time and post I-D, filtered by the same visibility rules, and cached per user for ten minutes. The ranked feed is untouched."], cls="dia")

S(dia(K(7, "sequence"), "Cached result, or the rebuild path", "seq-catchup"), [
 "C: As a sequence. Get catch-up for forty-eight hours. Is there a cached result for this user? A miss. For each followee, posts since forty-eight hours ago, the rebuild path. Merge by time, filter, page by time and I-D. Store for ten minutes. Return the first fifty and a cursor."], cls="dia")

qs("Interviewer · the second-level push", "“It becomes the most used screen.”", [
 "I: It becomes the most used screen.", "[pause: 2.0]"])

S(plain(K(7, "the second fix"), "Then it earns its own view, with a price said first", '<div class="cards c2">'
  '<div class="cd grn"><h3>A second view</h3><p>A per-user chronological list maintained by the same fan-out: IDs only, a 48 h lifetime. Celebrities merged at read as before.</p></div>'
  '<div class="cd amb"><h3>Its price</h3><p>About doubles timeline memory for the users who use it. Measure the read load on the author indexes first.</p></div></div>' +
  line("The design absorbed the requirement with a new consumer of the same event, not a rebuild.", "g")), [
 "C: If catch-up becomes the most used screen, it earns its own materialised view: a per-user chronological list maintained by the same fan-out event, I-Ds only, with a forty-eight hour lifetime, and celebrities merged at read as before. Its price, said first: it roughly doubles timeline memory for the users who use it. I'd measure the load on the author indexes before paying it.",
 "C: Either way, the design absorbed the requirement with a new reader of the same data, not a rebuild."])

say_slide("“I wouldn't distort the ranked timeline for a query it wasn't designed for. Catch-up reads the source of truth, the followees' author indexes for the window, through the same path I use for rebuilds, and caches the result for minutes. If it becomes popular, it gets its own small view, and I'd say what that costs first.”", [
 "V: If asked, I'd say: I wouldn't distort the ranked timeline for a query it wasn't designed for. Catch-up reads the source of truth, the followees' author indexes for the window, through the same path I use for rebuilds, and caches the result for minutes. If it becomes popular, it gets its own small view, and I'd say what that costs first.", "[pause: 1.0]",
 "N: Last challenge, and always the last one: how would you know any of this broke?"])

# ───────── Challenge 8 · observability ─────────
subchapter("7.8", "Challenge 8: How would you know the feed got worse?", ["N: Challenge eight. The feed is up and fast. How would you know it had silently got worse?"])
qs("Interviewer · challenge 8 of 8", "“The feed is up and fast. How would you know it had silently got worse?”", [
 "I: The feed is up and fast. How would you know it had silently got worse?", "[pause: 2.0]"])

S(dia(K(8, "green dashboards"), "Green boxes, a worse product", "ch8-attack", q=True, red=True,
      extra=strip(("case", "Naive answer", "“Error rate and latency.”"),
                  ("case", "Break", "The monitoring: it watches boxes, not the promise to the user."))), [
 "C: The naive answer: error rate and latency. Both measure boxes. The promise to the user is different: your friends' posts show up within seconds, and the feed is good. A routing bug in the fan-out box, in red, can break that promise with every box green."], cls="dia")

S(plain(K(8, "the trace"), "A routing bug nobody sees", '<pre class="trace"><span class="t">Mon 10:00</span>a tier-job change marks <span class="bad">30 % of mid-tier authors as pull</span> by mistake\n<span class="t">Mon 10:00</span>no errors; latency unchanged\n<span class="t">Mon 10:00</span>their posts reach followers only through the merge, which lists only true celebrities: <span class="bad">never shown</span>\n<span class="t">Mon–Sun  </span>engagement per session drifts down 2 %\n<span class="t">Mon +7   </span>a product manager asks why</pre>', q=True, red=True), [
 "C: The trace. A change to the tier job marks thirty percent of mid-tier authors as pull, by mistake. No errors. Latency unchanged. Their posts now reach followers only through the read merge, and the merge lists only true celebrities, so they are never shown. Engagement drifts down two percent over a week, and a product manager is the one who notices."])

S(dia(K(8, "the fix"), "Measure the promise: post-to-visible time, per tier", "ch8-fix",
      extra=strip(("fixb", "Mechanism", "Synthetic authors in every tier post every minute; synthetic followers open the feed and time the post's arrival. That is the freshness SLI, per tier: p95 under 5 s."),
                  ("whyb", "Why it works", "The probe walks the real path end to end, so a routing mistake shows in one tier within minutes."))), [
 "C: The fix. Measure the promise. Synthetic authors, one in every tier, post every minute through the real path. Synthetic followers open the feed and time the post's arrival. That is the freshness indicator, per tier, with a target of five seconds at p-ninety-five. In this case, the mid-tier probe stops arriving within minutes of the change."], cls="dia")

S(dia(K(8, "sequence"), "Post, deliver, look, time it", "seq-probe"), [
 "C: As a sequence. The synthetic author posts, one per tier. Fan-out delivers it by the real path. The synthetic follower opens the feed every five seconds until the post appears, and reports post-to-visible time per tier. Mid tier not visible after five minutes: page, with the tier named."], cls="dia")

S(plain(K(8, "symptom pairs"), "Two metrics, one conclusion", table(["When you see", "And", "It means"], [
  ["fan-out lag up", "post rate flat", "workers slow or stuck, not more traffic"],
  ["freshness bad for one tier", "lag flat", "a routing bug: this case"],
  ["ranking fallback up", "ranking p99 normal", "the deadline is misconfigured"],
  ["author-index reads up", "timeline hit rate down", "a rebuild wave: a lost shard"],
  ["engagement down", "fallback, freshness, empty-feed rate all normal", "a ranking model change; ranking's to own"]], "bt sm") +
  strip(("whyb", "Quality, not uptime", "Empty-feed rate, fallback rate, share of items from close ties, engagement per session against its seasonal baseline."), cols="one")), [
 "C: Then read metrics in pairs. Fan-out lag up with the post rate flat: workers are slow, not traffic. Freshness bad for one tier with lag flat: a routing bug, this case. Fallback up with ranking's latency normal: a misconfigured deadline. Author-index reads up with the timeline hit rate down: a rebuild wave. Engagement down with everything else normal: a model change, and ranking's to own.",
 "C: And quality metrics, not uptime: empty-feed rate, fallback rate, the share of items from close ties, and engagement per session against its seasonal baseline."])

qs("Interviewer · the second-level push", "“Finance says the timeline tier's memory bill doubled while users grew ten percent.”", [
 "I: Finance says the timeline tier's memory bill doubled while users grew ten percent.", "[pause: 2.0]"])

S(plain(K(8, "the second fix"), "Cost is observable too", table(["Measure", "What usually drifted", "Lever"], [
  ["memory per active user", "the timeline bound crept up", "500 → 300 entries saves 40 %"],
  ["share of inserts to inactive users", "the active cut-off was widened", "back to 30 days: about half the writes"],
  ["entries per timeline", "the mid tier pushes to everyone", "restore active-in-a-day for the mid tier"]], "bt sm") +
  line("Find what grew, then pull the lever. Don't buy a bigger cluster first.", "a")), [
 "C: Cost is observable too. Memory per active user, the share of inserts going to inactive users, and entries per timeline. Usually something drifted: the bound crept up, the active cut-off was widened, or the mid tier is pushing to everyone. Find what grew, then pull the lever. Five hundred entries to three hundred saves forty percent of memory if nobody scrolls that far. Don't buy a bigger cluster first."])

say_slide("“I measure the promise, not the servers: synthetic accounts in every tier post and read every minute, so I know post-to-visible time per tier. Then quality signals, empty feeds, ranking fallbacks, engagement against its baseline, catch the feed that works but got worse. And I read metrics in pairs to find the cause.”", [
 "V: If asked, I'd say: I measure the promise, not the servers. Synthetic accounts in every tier post and read every minute, so I know post-to-visible time per tier. Then quality signals, empty feeds, ranking fallbacks, engagement against its baseline, catch the feed that works but got worse. And I read metrics in pairs to find the cause.", "[pause: 1.0]"])

# ───────────────────────── 8 · build cost (AUX) ─────────────────────────
chapter(8, "Build cost", 6, "Who builds it, in what order, and what it costs. The manager layer.", [
 "C: The build cost. This is the manager layer, marked auxiliary: a Staff candidate can skip it, an engineering manager should not."], aux=True)

S(plain("Build cost · sequence by measured load", "MVP first, then push, then the hybrid", table(["Phase", "Scope", "People", "Time"], [
  ["MVP · V1", "pull with a per-reader cache; posts, author index, graph integration, ranking call", "4 engineers", "1 quarter"],
  ["Push · V2", "outbox, log, fan-out workers, timelines, post cache", "two teams", "1 quarter"],
  ["Hybrid · V3", "tiers, celebrity lists, filter on read, deadline, rebuild path, probes", "2–3 teams", "2 quarters"]], "bt sm") +
  '<div class="hedge"><b class="t">Label the numbers</b>Illustrative staffing. The order is the point: each phase starts when the measured load of the one before demands it.</div>'), [
 "C: Sequenced by measured load. The first version is pull with a per-reader cache: about four engineers, one quarter. It is right until the merge on a miss breaks the budget. Then push: two teams, a quarter. Then the hybrid, the filter, the deadline, the rebuild path and the probes: two or three teams, two quarters. Illustrative numbers; the order is the point."], cls="aux")

S(plain("Build cost · the migration", "Pull to push, two teams, one quarter, no downtime", table(["Weeks", "Step"], [
  ["1–4", "build fan-out and timelines beside the pull path; nothing reads them"],
  ["5–8", "shadow: write timelines, keep serving pull, compare both feeds per user"],
  ["9–11", "switch by cohort: 1 %, 10 %, 50 %, all; roll back by cohort"],
  ["12–13", "pull stays as the rebuild and catch-up path; remove the per-reader cache"]], "bt sm")), [
 "C: The migration from pull to push, with no downtime. Weeks one to four, build fan-out and timelines beside the pull path, read by nothing. Weeks five to eight, shadow: write timelines, keep serving pull, and compare the two feeds per user. Weeks nine to eleven, switch by cohort, one percent, ten, fifty, all, with rollback by cohort. Then pull stays, as the rebuild and catch-up path."], cls="aux")

S(plain("Build cost · team seams", "Three teams along the data", '<div class="cards c3">'
  '<div class="cd"><h3>Publish and graph</h3><p>Post service, posts store, author index, the event. Contract: the post-created event schema.</p></div>'
  '<div class="cd grn"><h3>Fan-out and timelines</h3><p>Workers, tiers, timelines, celebrity lists, rebuild. Contract: the timeline entry format.</p></div>'
  '<div class="cd amb"><h3>Feed serving</h3><p>Read path, filter, cursor, ranking integration. Contract: the Rank call with its deadline.</p></div></div>' +
  line("On-call is on freshness and feed latency; ranking's fallback rate pages ranking.", "a")), [
 "C: Three teams along the data. Publish and graph, owning the post-created event. Fan-out and timelines, owning the timeline entry format. Feed serving, owning the rank call with its deadline. On-call is on freshness and feed latency, and ranking's fallback rate pages the ranking team."], cls="aux")

S(plain("Build cost · money", "Two lines dominate; one lever halves the first", table(["Item", "Arithmetic", "Lever"], [
  ["Timeline memory", "4 TB × 3 replicas ≈ 12 TB of RAM", "skip inactive users; the bound; the threshold"],
  ["Fan-out writes", "~120,000 → ~60,000 inserts/s", "active-only targeting"],
  ["Post cache", "hot posts, a few TB", "hit rate"],
  ["Everything else", "small next to these", "—"]], "bt sm") +
  '<div class="hedge"><b class="t">Top risks</b>The threshold set once and never measured. Rebuild never load-tested. Ranking\'s budget renegotiated every release instead of owned.</div>'), [
 "C: Money. Two lines dominate: timeline memory, about twelve terabytes of RAM with replicas, and fan-out writes. The biggest lever on both is skipping inactive users, roughly half. Then the threshold and the timeline bound.",
 "C: The top risks: a threshold set once and never measured, a rebuild path never load-tested, and ranking's budget renegotiated every release instead of owned."], cls="aux")

# ───────────────────────── 9 · recap ─────────────────────────
chapter(9, "Recap", 7, "One picture, one sentence per path, the mistakes, the thesis", [
 "C: The recap. One picture, a sentence per path, the common mistakes, and the thesis."])

S(dia("Recap · the final design", "Everything on one baseline", "base-final"), [
 "C: The final design on the baseline. The write path along the top: post service, one transaction, the event log, fan-out by tier. In the middle, the graph, the celebrity lists and the timelines. Along the bottom, the feed service, ranking with a deadline and the post cache. And the parts that only show up when something goes wrong: invalidation, the rebuild path, catch-up, and the synthetic users that tell us the promise holds."], cls="dia")

S(plain("Recap · one sentence per path", "Four paths", table(["Path", "In one sentence"], [
  ["Publish", "One transaction and an event; push IDs to active followers, or one write for a celebrity."],
  ["Read", "One timeline and a few celebrity lists; filter; rank under a deadline; hydrate fifty; a cursor."],
  ["Remove", "One write to the post; enforced on every page; cleanup later."],
  ["Rebuild", "Pull, coalesced, rate-limited; degraded if over the limit."]], "bt sm")), [
 "C: Four paths, one sentence each. Publish: one transaction and an event, then push I-Ds to active followers, or one write for a celebrity. Read: one timeline and a few celebrity lists, filtered, ranked under a deadline, fifty hydrated, and a cursor. Remove: one write to the post, enforced on every page. Rebuild: pull, coalesced and rate-limited, degraded beyond the limit."])

S(plain("Recap · common mistakes in this round", "What costs points", '<div class="cards c2">'
  '<div class="cd red"><h3>Design</h3><p>Picking push or pull and defending it. Bodies in timelines. No number on the threshold. Strong consistency for a feed.</p></div>'
  '<div class="cd red"><h3>Correctness</h3><p>Chasing deletes into copies. An offset for pagination. “Exactly once” fan-out.</p></div>'
  '<div class="cd amb"><h3>Operations</h3><p>Ranking with no deadline. No plan for a lost shard. Watching uptime, not freshness.</p></div>'
  '<div class="cd amb"><h3>Focus</h3><p>Going deep on the ranking model. Never asking about the follower distribution.</p></div></div>'), [
 "C: The common mistakes. Picking push or pull and defending it. Bodies in timelines. No number on the threshold. Strong consistency for a feed. Chasing deletes into copies, offsets for pagination, and exactly-once fan-out. Ranking with no deadline, no plan for a lost shard, and watching uptime instead of freshness. And going deep on the ranking model, or never asking about the follower distribution."])

S(plain("Recap · the challenges", "Eight questions, eight answers", table(["Challenge", "The answer in a phrase"], [
  ["1 The celebrity post", "pull it; one write"],
  ["2 The line", "both sides of the arithmetic; no backfill"],
  ["3 Delete and block", "filter on read; cleanup is cosmetic"],
  ["4 Twice or never", "idempotent inserts; a cursor; a session list"],
  ["5 A lost shard", "rebuild by pull; coalesce; limit; degrade"],
  ["6 A slow ranker", "a deadline, a fallback, an owner"],
  ["7 Catch-up", "the source of truth, not the cache"],
  ["8 Got worse?", "synthetic probes per tier; symptom pairs"]], "bt sm")), [
 "C: The eight challenges in a phrase each. Pull the celebrity. Set the line from both sides. Filter on read. Idempotent inserts and a cursor. Rebuild by pull, limited and degraded. A deadline with an owner. The source of truth for a new query. And probes that measure the promise."])

key("The close", "Push IDs for most, <em>pull</em> the few, a line set by <em>arithmetic</em>. Correctness on the <em>read path</em>. Every degraded mode has a <em>fallback and a metric</em>.", [
 "V: It's a hybrid: post I-Ds pushed into bounded timelines for ordinary accounts, celebrities pulled at read time, with the line set by arithmetic and tuned with data. Correctness lives on the read path, so a delete is one write. I traded strict freshness for seconds of eventual consistency, and every degraded mode, slow ranking or a lost shard, has a fallback and a metric.", "[pause: 2.0]"])
