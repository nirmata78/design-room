from dsl import *
from stack import REJ
P = "[+]"
B = lambda x: f'<span class="bad">{x}</span>'
K = lambda n, t: f"Challenge {n} of 8 · {t}"

# ───────── Challenge 5 · dead everywhere in five minutes ─────────
subchapter("7.5", "Challenge 5: Dead everywhere in five minutes", ["N: Challenge five. A phishing link is reported: how do we prove it stops working at every layer within five minutes, even when a message is lost?"])
qs("Interviewer · challenge 5 of 8", "“Legal reports a phishing link. It must stop working everywhere within five minutes. Show me.”", [
 "I: Legal reports a phishing link. It must stop working everywhere within five minutes. Show me.", "[pause: 2.0]"])

S(dia(K(5, "dead everywhere"), "Every copy of the answer is a liability", "ch5-attack", q=True, red=True,
      chip=chips("naive: “delete the row”", "none of these layers reads the row on a hit")), [
 P, "C: The naive answer: delete the row.", P,
 "C: Look at the red boxes. The edge, every redirect server's memory, the Redis cache. None of them reads the row on a hit. Deleting the row changes the truth and nothing that answers."], cls="dia")

S(trace(K(5, "the trace"), "Twenty minutes later, a victim still lands on the page", [
  ("15:00:00", "row deleted (or status = blocked)"),
  ("15:00:00", "still answering: shared cache (TTL " + B("1 h") + "), 40 servers' memory (60 s), edge in 30 cities (60 s)"),
  ("15:00:00", "and browsers that got a 301 last week: " + B("forever")),
  ("15:20:00", B("a victim still lands on the phishing page") + ", from the shared cache")],
  hedge=("The real question", "Not “how do we delete”, but “what is the longest any copy can live after we decide”.")), [
 "C: The trace.", P, "C: At three o'clock the status is set.", P,
 "C: Still answering: the shared cache with an hour's lifetime, forty servers' memory with sixty seconds, the edge in thirty cities with sixty seconds.", P,
 "C: And browsers that got a three-oh-one last week, forever.", P, "C: At three-twenty a victim still lands on the page, served from the shared cache.", P,
 "C: So the real question is not how to delete. It is: what is the longest any copy can live after we decide?"])

S(dia(K(5, "the fix"), "Status, a direct delete, an invalidation, and a lifetime at every layer", "ch5-fix",
      chip=chips("status", "direct delete", "invalidate", "purge", "410 Gone"), extra=rejl(*REJ(5))), [
 P, "C: The fix, built up on the takedown path.", P,
 "C: The takedown writes blocked to the store. It deletes the Redis key directly and retries until it's confirmed: that cache has a long lifetime, so it must never depend on a lost message. It publishes an invalidation on the Kafka topic: every redirect server drops the code, and the edge is purged by surrogate key. The next request reads blocked and answers four-ten with a warning page.",
 P, "C: Rejected: Redis Pub-Sub for the invalidation. It is at most once: a server disconnected for a second never learns.",
 "C: The property is S-two, and it holds by arithmetic. Here is the arithmetic."], cls="dia")

S(dia(K(5, "the budget"), "The worst case is a sum, and it fits", "takedown-budget", chip=chips("if the event is lost", "initial target")), [
 "C: The worst case, if the invalidation event is lost. Status and the Redis delete: a couple of seconds. The in-process lifetime: sixty. The edge lifetime: sixty. The purge call: a few. About two minutes, against five. The spare covers a slow purge and a retry. Every lifetime in this system was chosen with this bar in view."], cls="dia")

S(dia(K(5, "sequence"), "Status first, then every copy", "seq-takedown"), [
 "C: The sequence once more, with the point that matters.", "[+3]",
 "C: The status, then the shared cache deleted directly, not by the event.", "[+2]",
 "C: Only the short-lived layers depend on the event.", P,
 "C: If it is lost, their lifetimes end the copies.", P,
 "C: And four-ten Gone tells crawlers to stop asking."], cls="dia")

S(plain(K(5, "before the link exists"), "The cheapest takedown is the one you never need", cards(
  ("grn", "On create", "Check the URL against the classifier. Known-bad: 422, no code issued."),
  ("amb", "After create", "When the classifier's list updates, rescan live links created recently and block matches through the same path."),
  ("", "Audit", "Every takedown: who, why, when, and when each layer answered 410."), cols=3)), [
 "C: Three cheaper defences.", P, "C: On create, check the U-R-L against the classifier: if it's known-bad, no code is issued.", P,
 "C: When the classifier's list updates, rescan recently created live links and block any matches through the same path.", P,
 "C: And every takedown is audited: who, why, when, and when each layer started answering four-ten."])

qs("Interviewer · the second-level push", "“The invalidation event is lost. Or the link was created as a 301.”", [
 "I: The invalidation event is lost. Or the link was created as a three-oh-one.", "[pause: 2.0]"])

S(plain(K(5, "the second fix, and the honest limit"), "Lifetimes are the backstop; a 301 cannot be recalled", cards(
  ("grn", "A lost event", "The lifetimes are the backstop by design: about two minutes. Kafka replay narrows it further. An hourly test takedown measures the real time at every layer (challenge eight)."),
  ("red", "A 301", "Cannot be recalled from a browser. That is why it is opt-in, and why the safety check runs before a 301 link is issued."))), [
 P, "C: A lost event: the lifetimes are the backstop, by design, so the worst case is about two minutes, and Kafka's replay makes a lost event rarer still. An hourly test takedown measures the real time at every layer, which is challenge eight.", P,
 "C: A three-oh-one is the honest limit. It cannot be recalled from a browser, ever. That's why it's opt-in, and why the safety check runs before a three-oh-one link is issued."])

say_slide("“Every copy of the answer is a liability. A takedown writes the status, deletes the shared-cache key directly, sends an invalidation and purges the edge, and the lifetime at every layer is chosen so that even with a lost message the worst case is inside five minutes. A 301 can't be recalled, which is one more reason it isn't the default.”", [
 "V: If asked, I'd say: every copy of the answer is a liability. A takedown writes the status, deletes the shared-cache key directly, sends an invalidation and purges the edge. The lifetime at every layer is chosen so that even with a lost message, the worst case is inside five minutes. A three-oh-one can't be recalled, which is one more reason it isn't the default.", "[pause: 1.0]",
 "N: The redirect is fast and withdrawable. Next: how do we count it without slowing it down?"])

# ───────── Challenge 6 · counting ─────────
subchapter("7.6", "Challenge 6: Counting without slowing the redirect", ["N: Challenge six. Owners want clicks by day and country: where does the count happen, and what changes when every click is money?"])
qs("Interviewer · challenge 6 of 8", "“How do you count clicks per link per country without touching the redirect latency?”", [
 "I: How do you count clicks per link, per country, without touching the redirect latency?", "[pause: 2.0]"])

S(dia(K(6, "counting"), "A counter on the row is a lock on the hot path", "ch6-attack", q=True, red=True,
      extra=strip(("case", "Naive answer", "“UPDATE links SET clicks = clicks + 1 on every redirect.”"),
                  ("case", "Break", "The link store, on every click: one row per viral link, a write inside the redirect."))), [
 P, "C: Version two's redirect path.", "[+3]",
 "C: The naive answer: increment a clicks column on every redirect.", P,
 "C: Look at the red store. That puts a write inside the redirect, on the row of the hottest link."], cls="dia")

S(trace(K(6, "the trace"), "Five milliseconds becomes nine hundred", [
  ("14:02", "<code>k7Pq2mZ</code> at 40,000 clicks/s → " + B("40,000 UPDATEs/s on one row")),
  ("14:02", "the row lock serialises them: one at a time"),
  ("14:03", "each redirect waits for its write: p99 5 ms → " + B("900 ms")),
  ("14:04", "the cache was fine. " + B("the counter broke the redirect"))],
  hedge=("Label the numbers", "Illustrative. The cache had solved the read; the write put the hot key back on the critical path.")), [
 "C: The trace.", P, "C: Forty thousand updates a second on one row.", P, "C: The row lock serialises them.", P,
 "C: Each redirect waits for its write, and p ninety-nine goes from five milliseconds to nine hundred.", P,
 "C: The cache had solved the read.", P, "C: The counter put the hot key straight back on the critical path."])

S(dia(K(6, "the fix"), "Answer first, then record; count in batches", "ch6-fix",
      chip=chips("after the 302", "buffer → Kafka → Flink → ClickHouse", "drops counted"), extra=rejl(*REJ(6))), [
 P, "C: The fix, green along the bottom.", P,
 "C: After the three-oh-two goes out, the server appends to a local buffer that pre-aggregates. The buffer flushes a batch every second into Kafka, partitioned by code. Flink counts per code per minute, then per day per country, into ClickHouse. If the buffer is full, events are dropped, and the drops are counted.",
 "C: L-two: nothing after the answer can delay it. L-three, with a measured loss: the drop counter is the loss, and counts say as-of.", P,
 "C: Rejected: Cassandra counters. They remove the row lock, but a retried increment counts twice."], cls="dia")

S(plain(K(6, "precision"), "Say exactly what the count promises", table(["Today (not billed)", "If clicks are billed"], [
  ["At-most-once from the server: a crash loses the unflushed second", "At-least-once: a durable buffer on disk, resent until acknowledged (acks=all)"],
  ["No event ID; drops counted and shown", "An event ID at the redirect; de-duplicated in Flink's keyed state"],
  ["Bots counted as clicks", "Bots filtered before anything is billed"],
  ["Counts eventually consistent, minutes late", "Same lag; exact once settled; stated in the billing terms"]])), [
 "C: Precision about what the count promises, today against billed.", P,
 "C: Today: at-most-once from the server, a crash loses the unflushed second. Billed: at-least-once, with a durable buffer on disk, resent until every replica acknowledges.", P,
 "C: Today drops are counted and shown. Billed: an event I-D is created at the redirect and de-duplicated in Flink's keyed state, so the effect is exactly once.", P,
 "C: Bots: counted today, filtered before anything is billed.", P,
 "C: And the lag stays minutes either way. The redirect still never waits."])

qs("Interviewer · the second-level push", "“Product now bills per click. A lost click is lost money, and a double-counted one is a refund.”", [
 "I: Product now bills per click. A lost click is lost money, and a double-counted one is a refund.", "[pause: 2.0]"])

S(dia(K(6, "the second fix"), "Event IDs, a durable buffer, de-duplication", "seq-ch6-billed"), [
 "C: The second fix, as a sequence.", P, "C: The three-oh-two is already sent.", P,
 "C: The server appends the event, with an I-D, to a buffer on local disk.", P, "C: It flushes a batch every second.", P,
 "C: It trims the buffer only on acknowledgement.", P, "C: Delivery to Flink is at least once.", P,
 "C: And Flink de-duplicates by event I-D, filters bots, and counts.",
 "C: The honest limit: a server's disk lost with an unflushed buffer loses up to a second of that server's clicks. That bound goes into the billing terms."], cls="dia")

say_slide("“The click is recorded after the answer, never before it. Events go to a local buffer and a log, and an aggregator counts per minute. Today that's lossy by choice and we measure the loss. If clicks are billed, I add event IDs, a durable buffer and de-duplication, and the redirect still doesn't wait.”", [
 "V: If asked, I'd say: the click is recorded after the answer, never before it. Events go to a local buffer and a log, and an aggregator counts per minute. Today that's lossy by choice and we measure the loss. If clicks are billed, I add event I-Ds, a durable buffer and de-duplication, and the redirect still doesn't wait.", "[pause: 1.0]",
 "N: Every path now depends on the store being somewhere. What if that somewhere is gone?"])

# ───────── Challenge 7 · a region goes dark ─────────
subchapter("7.7", "Challenge 7: A region goes dark", ["N: Challenge seven. The region holding the store's primary disappears: what keeps working, and what may stop?"])
qs("Interviewer · challenge 7 of 8", "“The region holding your link store's primary goes down. What still works?”", [
 "I: The region holding your link store's primary goes down. What still works?", "[pause: 2.0]"])

S(dia(K(7, "a region goes dark"), "Creates fail; misses hit a read-only store", "ch7-attack", q=True, red=True,
      extra=strip(("case", "Naive answer", "“We fail over the database.”"),
                  ("case", "Break", "The PostgreSQL primaries and the etcd quorum were in the lost region."))), [
 P, "C: The store, the allocator and the paths that use them.", "[+3]",
 "C: The naive answer: fail over the database. That's part of it.", P,
 "C: But look at what is red: the PostgreSQL primaries and the etcd quorum both lived in the lost region. Fail-over takes time, and during it, creates fail and every miss goes somewhere."], cls="dia")

S(trace(K(7, "the trace"), "Which requests fail, and which merely slow", [
  ("03:10", "the primary region is lost"),
  ("03:10", "redirects in Europe and Asia: 98 % from caches, " + B("2 % miss to a store that is now read-only")),
  ("03:10", "creates: " + B("fail") + ": the primaries and the allocator's quorum are gone"),
  ("03:11", "bulk integrators retry, with their idempotency keys")]), [
 "C: The trace.", P, "C: At ten past three the primary region is lost.", P,
 "C: Redirects elsewhere: ninety-eight percent from caches, two percent miss to a store that is now read-only, which is fine for reads, if the reads are local.", P,
 "C: Creates fail, because the primaries and the allocator's quorum are gone.", P, "C: Bulk integrators retry with their idempotency keys."])

S(dia(K(7, "the fix"), "Redirects are regional; creates are regional too", "regions",
      extra=strip(("fixb", "Mechanism", "Each region has PostgreSQL replicas of every slice, its own Redis and its own etcd: a redirect never crosses regions. Each region is the primary for its own slice of the ID space, so it can create alone."),
                  ("whyb", "Property", "L2 depends only on regional state. S1 holds because the slices are disjoint.")) + rejl(*REJ(7))), [
 "C: The fix. Redirects are regional: each region has PostgreSQL replicas of every slice, its own Redis Cluster, its own etcd. A redirect never crosses a region.", P,
 "C: Creates are regional too: each region is the primary for its own slice of the I-D space, Europe the first third, the Americas the second, Asia the last. A region can create without the others, and the slices replicate asynchronously.", P,
 "C: L-two depends only on regional state. S-one holds because the slices are disjoint: no two regions can ever produce the same I-D.", P,
 "C: Rejected: one global consensus database, Spanner or Cockroach. Every create would pay a cross-region quorum. Right for money, wrong for four hundred link creates a second."], cls="dia")

S(dia(K(7, "on the baseline"), "The replica beside the store", "ch7-fix"), [
 P, "C: On the baseline.", "[+2]",
 "C: The replica beside the link store, receiving asynchronous replication, and the shared cache reading from the local copy. Fail-over of a shard's primary is now only for writes to links created in the lost region, and those are rare: links are written once."], cls="dia")

qs("Interviewer · the second-level push", "“A link created in Asia is clicked in Europe two hundred milliseconds later, before replication.”", [
 "I: A link created in Asia is clicked in Europe two hundred milliseconds later, before replication.", "[pause: 2.0]"])

S(dia(K(7, "the second fix"), "One cross-region lookup, not an error", "seq-ch7-region"), [
 "C: The second fix, as a sequence.", P, "C: A code created in Asia two hundred milliseconds ago.", P, "C: It is clicked in Europe.", P,
 "C: Local miss. The server inverts the permutation, gets the I-D back, and its slice says which region created it: Asia.", P,
 "C: One cross-region lookup.", P, "C: Cache the answer here.", P, "C: And three-oh-two. One round trip slower, no error.",
 "C: The honest limit: a region lost with unreplicated creates loses those links' last seconds. A creator who retries with the same idempotency key gets the same code back once the region returns."], cls="dia")

say_slide("“Redirects never leave their region: replicas and caches answer them even with the primary gone. Creates are regional because each region owns a slice of the ID space. The one gap is a brand-new link clicked elsewhere before it replicates, and that costs one cross-region lookup, not an error.”", [
 "V: If asked, I'd say: redirects never leave their region. Replicas and caches answer them even with the primary gone. Creates are regional, because each region owns a slice of the I-D space. The one gap is a brand-new link clicked elsewhere before it replicates, and that costs one cross-region lookup, not an error.", "[pause: 1.0]",
 "N: Last challenge. All of this can fail silently. How would we know?"])

# ───────── Challenge 8 · observability ─────────
subchapter("7.8", "Challenge 8: How would you know it is broken?", ["N: Challenge eight. The dashboards are green: how do we know the redirect a user gets is actually working, in every region?"])
qs("Interviewer · challenge 8 of 8", "“Your dashboards are green. How do you know redirects are actually working?”", [
 "I: Your dashboards are green. How do you know redirects are actually working?", "[pause: 2.0]"])

S(dia(K(8, "how would you know"), "Green boxes, a slower product", "ch8-attack", q=True, red=True,
      extra=strip(("case", "Naive answer", "“Error rate and CPU.”"),
                  ("case", "Break", "The monitoring view watches boxes. Nothing measures the path a user takes."))), [
 P, "C: The redirect path.", "[+3]",
 "C: The naive answer: error rate and C-P-U. Those watch boxes.", P,
 "C: The red one here is the shared cache, and nothing about it will show as an error."], cls="dia")

S(trace(K(8, "the trace"), "Nothing failed, and the morning peak paged", [
  ("01:55", "a config change sets the shared cache's lifetime to 0"),
  ("02:00", "errors 0; p50 unchanged; p99 6 ms → 18 ms"),
  ("02:00", "store reads " + B("40/s → 4,000/s") + ": nobody is watching"),
  ("09:00", "the peak arrives: " + B("the store saturates; the first page"))]), [
 "C: The trace.", P, "C: Just before two in the morning, a config change sets the shared cache's lifetime to zero.", P,
 "C: No errors. Median unchanged. p ninety-nine creeps from six milliseconds to eighteen, still under target.", P,
 "C: Store reads go from forty a second to four thousand. Nobody is watching.", P,
 "C: At nine, when the peak arrives, the store saturates and the first page fires. Seven hours late."])

S(dia(K(8, "the fix"), "Probe the path, in every region", "ch8-fix",
      extra=strip(("fixb", "Mechanism", "Synthetic probes in every region create a link and follow it through the edge every minute. Hourly, a test takedown is timed until every layer answers 410. Prometheus records; alerts page on the SLI, not on boxes."),
                  ("whyb", "Property", "The SLI measures what the user gets, end to end, per region: latency, success, create-to-first-redirect, takedown time.")) + rejl(*REJ(8))), [
 P, "C: The fix.", "[+3]",
 "C: Synthetic probes in every region create a link and follow it through the edge, every minute: redirect latency, success, and the time from create to first redirect. And every hour, a test link is blocked and timed until every layer answers four-ten. Prometheus records it, and alerts page on these, not on boxes.", P,
 "C: That's our service level indicator: what the user gets, end to end, per region. Takedown time measured, not hoped for.", P,
 "C: Rejected: an outside uptime checker alone. One vantage point that sees only the edge: never create-to-redirect, never a takedown."], cls="dia")

S(plain(K(8, "symptom pairs"), "Two metrics, one cause", table(["When you see", "Together with", "It means"], [
  ["Cache hit rate down", "store reads up, traffic flat", "<b>a cold or misconfigured cache</b>, not more users (this trace)"],
  ["404 rate up", "creates flat", "<b>scanning</b>: someone is walking codes"],
  ["p99 up", "hit rate flat", "<b>something synchronous</b> crept onto the redirect path"],
  ["Click drops up", "buffer full on many servers", "<b>Kafka or Flink is slow</b>, not the redirect"],
  ["Takedown time up", "invalidation consumer lag up", "<b>the channel is behind</b>: the lifetimes are carrying us"]], "bt sm")), [
 "C: Symptom pairs: two metrics, one cause.", P,
 "C: Hit rate down with store reads up and traffic flat: a cold or misconfigured cache, not more users. That's this trace, caught at two, not nine.", P,
 "C: Four-oh-fours up while creates are flat: someone is scanning codes.", P,
 "C: p ninety-nine up while hit rate is flat: something synchronous crept onto the redirect path.", P,
 "C: Click drops up with buffers full: Kafka or Flink is slow, not the redirect.", P,
 "C: Takedown time up with consumer lag on the invalidation topic: the channel is behind, and the lifetimes are carrying us."])

S(dia(K(8, "sequence"), "The probe, minute by minute", "seq-ch8-probe"), [
 "C: The probe as a sequence.", P, "C: Create a test link.", P, "C: Two-oh-one.", P, "C: Follow it through the edge.", P,
 "C: Three-oh-two in six milliseconds, create to first redirect in under half a second.", P,
 "C: Hourly, block a test link.", P, "C: And poll every layer until four-ten. Today, seventy-four seconds, against five minutes."], cls="dia")

qs("Interviewer · the second-level push", "“The probes pass, but one country's DNS sends users to the wrong region.”", [
 "I: The probes pass, but one country's D-N-S sends users to the wrong region.", "[pause: 2.0]"])

S(plain(K(8, "the second fix"), "Real users, compared with the probes", cards(
  ("grn", "Real-user monitoring", "From edge logs, per country: latency and the region that answered. Probes say the path works; real users say they reach it."),
  ("amb", "Alert on divergence", "Probes healthy and one country slow is the signal: routing, not our servers."))), [
 "C: The probes prove the path works. They don't prove users reach the right path.", P,
 "C: So add real-user monitoring from edge logs, per country: latency and which region answered.", P,
 "C: When probes are healthy and one country is slow, that divergence is the alert, and it says routing, not our servers."])

say_slide("“I measure the path, not the boxes: probes that create a link and follow it in every region, and a test takedown every hour, timed until every layer answers 410. Then pairs of metrics give me causes: hit rate down with store reads up means a cold cache, not more traffic.”", [
 "V: If asked, I'd say: I measure the path, not the boxes. Probes create a link and follow it in every region, and a test takedown every hour is timed until every layer answers four-ten. Then pairs of metrics give me causes: hit rate down with store reads up means a cold cache, not more traffic.", "[pause: 1.0]"])

# ───────────────────────── 8 · build cost ─────────────────────────
chapter(8, "Build cost", 6, "Who, how long, buy or build: the manager layer", [
 "C: Build cost. This is the manager layer, marked aux: skip it in a pure Staff round, use it in a manager round."], aux=True)

S(plain("Build cost · three releases", "Not one project", table(["", "V1", "V2", "V3"], [
  ["Scope", "One service, one table, random codes, a cache", "Split paths, etcd ranges, permutation, sharded PostgreSQL", "ristretto + singleflight, Kafka → Flink → ClickHouse, takedown channel, CDN, regions"],
  ["People", "2", "+2", "a team of 5–6"],
  ["Time", "6 weeks", "2 months", "2 quarters"],
  ["On-call", "business hours", "shared rotation", "24/7, error budgets"]])), [
 "C: Three releases.", P,
 "C: Scope. Version one, one service and one table with random codes and a cache. Version two, split paths, etcd ranges, the permutation and sharded PostgreSQL. Version three, the in-process cache, the click pipeline, the takedown channel, the C-D-N and regions.", P,
 "C: People: two engineers, then two more, then a team of five or six.", P, "C: Time: six weeks, two months, two quarters.", P,
 "C: And on-call grows with it: business hours, a shared rotation, then twenty-four-seven with error budgets."], cls="aux")

S(plain("Build cost · two teams, one quarter", "Split along the contract", cards(
  ("", "Links and redirect", "Create, codes, store, caches, edge. Owns the redirect SLO and the takedown time."),
  ("grn", "Clicks and trust", "Event pipeline, stats, the takedown service and its channel, the classifier integration.")) +
  line("The contract between them: the click event schema, and the invalidation topic.", "a")), [
 "C: If asked to split it across two teams for a quarter.", P,
 "C: Links and redirect, owning create, codes, store, caches and the edge, and the redirect objective.", P,
 "C: And clicks and trust, owning the event pipeline, stats, the takedown service and the classifier.", P,
 "C: The contract between them is two things: the click event schema, and the invalidation topic."], cls="aux")

S(plain("Build cost · buy, build, or don't", "Most of this is bought", table(["Part", "Decision", "Why"], [
  ["PostgreSQL, Redis, Kafka, ClickHouse", "buy managed", "commodity; the design is in how we use them"],
  ["Edge", "buy", "points of presence and a purge API"],
  ["URL classifier", "buy, or an internal service", "a specialist problem"],
  ["Code generation, redirect, takedown path", "build", "small, and it is the product"],
  ["The whole thing", "<b>don't</b>, if shortening is not our business", "an off-the-shelf shortener is a fine answer"]], "bt sm mx")), [
 "C: Buy, build, or don't.", P, "C: PostgreSQL, Redis, Kafka and ClickHouse are bought, managed.", P, "C: The edge is bought.", P,
 "C: The classifier is bought or an internal service.", P, "C: What we build is small: code generation, the redirect and the takedown path.", P,
 "C: And if shortening is not the business, the right answer may be: don't build it, use an off-the-shelf shortener. Say it."], cls="aux")

S(plain("Build cost · cost and risks", "The edge bill is the biggest line", cards(
  ("amb", "Cost, illustrative", "A handful of redirect pods at 4,000/s. 100 GB of Redis. 18 TB of PostgreSQL. The edge is billed per request: at 10 billion a month, the largest line, which is why its default lifetime is a business decision."),
  ("red", "Top risks", "The code format is a one-way door: codes are printed on paper. Takedown time untested until a real incident. Analytics becoming billing without the exactness work."))), [
 P, "C: Cost, illustrative. A handful of redirect pods, a hundred gigabytes of Redis, eighteen terabytes of PostgreSQL. The edge is billed per request, and at ten billion a month it's the largest line, which is why its default lifetime is a business decision.", P,
 "C: Top risks. The code format is a one-way door: codes are printed on paper and live forever. Takedown time untested until a real incident. And analytics quietly becoming billing without the exactness work."], cls="aux")

# ───────────────────────── 9 · recap ─────────────────────────
chapter(9, "Recap", 7, "One picture, four paths, the mistakes, the thesis", [
 "C: To close: one picture, one sentence per path, the mistakes to avoid, and the thesis."])

S(dia("Recap", "The whole design on one baseline", "base-final", chip=chips("ranges", "permutation", "in-process cache", "302 + edge", "click log", "takedown channel", "probes")), [
 "C: The final picture, drawn once more in the order a request meets it.", "[+5]",
 "C: The redirect across the middle: browser, edge, redirect service with its in-process cache, Redis, PostgreSQL.", P,
 "C: And a replica per region.", "[+3]",
 "C: Create on top: a safety check, the create service with its permutation, and etcd's leased ranges, inserting under the constraint.", "[+3]",
 "C: Along the bottom: the click log, the aggregator and the stats.", "[+2]",
 "C: The takedown with its invalidation channel.", P,
 "C: And probes in every region, following the path a user takes."], cls="dia")

S(plain("Recap · one sentence per path", "Four paths", table(["Path", "In one sentence"], [
  ["<b>Create</b>", "Check the URL, lease, permute, insert under the constraint"],
  ["<b>Redirect</b>", "Memory, then Redis, then PostgreSQL; answer; then count"],
  ["<b>Count</b>", "Buffer, Kafka, Flink, ClickHouse, and say how fresh"],
  ["<b>Withdraw</b>", "Status, a direct delete, invalidate, purge, and lifetimes that sum to under five minutes"]], "bt")), [
 "C: Four paths, one sentence each.", P, "C: Create: check the U-R-L, lease, permute, insert under the constraint.", P,
 "C: Redirect: memory, then Redis, then PostgreSQL; answer; then count.", P, "C: Count: buffer, Kafka, Flink, ClickHouse, and say how fresh.", P,
 "C: Withdraw: status, a direct delete, invalidate, purge, and lifetimes that sum to under five minutes."])

S(plain("Recap · eight fixes", "Each names the property it protects", table(["Challenge", "Fix", "Property"], [
  ["1 Two servers, one code", "etcd ranges; the primary key decides", "S1, L1"],
  ["2 Codes in order", "keyed permutation; 404 rate limit", "non-enumerable"],
  ["3 One viral link", "in-process cache; single flight", "L2"],
  ["4 301 or 302", "302 default; edge 60 s; 301 opt-in", "S2, counting"],
  ["5 Takedown in 5 min", "status, direct delete, invalidation, lifetimes", "<b>S2</b>"],
  ["6 Counting", "after the answer; buffer, log, aggregate", "L2, L3"],
  ["7 A region lost", "regional replicas; ID slices", "L2, S1"],
  ["8 How would you know", "probes, test takedowns, symptom pairs", "all"]])), [
 "C: Eight fixes, each with its property.", P, "C: Ranges and the constraint, for uniqueness.", P, "C: A keyed permutation, against enumeration.", P,
 "C: In-process caching with single flight, for the viral link.", P, "C: Three-oh-two by default, for counting and takedowns.", P,
 "C: Status, a direct delete and bounded lifetimes, for the five minutes.", P, "C: Counting after the answer.", P,
 "C: Regional replicas and I-D slices.", P, "C: And probes that measure the path."])

S(plain("Recap · common mistakes in this round", "Ten ways this round goes wrong", '<div class="cards c2"><div class="cd red"><h3>Design</h3><ul><li>Hash and truncate, with no collision story</li><li>Six characters without the arithmetic</li><li>Check, then insert</li><li>A counter update on every click</li><li>Codes that are a counter in disguise</li></ul></div>'
  '<div class="cd amb"><h3>Judgment</h3><ul><li>“Add a cache” with no plan for one hot key</li><li>301 by default</li><li>Forgetting every cached copy must be withdrawable</li><li>No number on the takedown time</li><li>Naming a product you cannot defend one level down</li></ul></div></div>'), [
 "C: Ten mistakes.", P, "C: In the design: hash and truncate with no collision story. Six characters without the arithmetic. Check, then insert. A counter update on every click. Codes that are a counter in disguise.", P,
 "C: In judgment: add a cache, with no plan for one hot key. Three-oh-one by default. Forgetting that every cached copy must be withdrawable. No number on the takedown time. And naming a product you cannot defend one level down."])

key("The close", "The redirect is <em>one memory read</em>. Codes are unique by <em>blocks and a constraint</em>, unguessable by a <em>key</em>. Everything else lives <em>beside</em> the redirect, with a number on how late it may be.", [
 "V: The redirect is the product, so it's one memory read, and nothing waits on anything else. Codes are unique because each server owns a block and the database has the last word, and unguessable because a key shuffles them. Everything else, counting, takedowns, the edge, lives beside the redirect, with a number on how late it may be.", "[pause: 1.2]",
 "C: Thank you. I'll stop there."])
