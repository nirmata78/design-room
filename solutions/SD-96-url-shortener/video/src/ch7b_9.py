from dsl import *

K = lambda n, t: f"Challenge {n} of 8 · {t}"

# ───────── Challenge 5 · dead everywhere in five minutes ─────────
subchapter("7.5", "Challenge 5: Dead everywhere in five minutes", ["N: Challenge five. A phishing link is reported: how do we prove it stops working at every layer within five minutes, even when a message is lost?"])
qs("Interviewer · challenge 5 of 8", "“Legal reports a phishing link. It must stop working everywhere within five minutes. Show me.”", [
 "I: Legal reports a phishing link. It must stop working everywhere within five minutes. Show me.", "[pause: 2.0]"])

S(dia(K(5, "dead everywhere"), "Every copy of the answer is a liability", "ch5-attack", q=True, red=True,
      chip=chips("naive: “delete the row”", "none of these layers reads the row on a hit")), [
 "C: The naive answer: delete the row. Look at the red boxes. The edge, every redirect server's memory, the shared cache. None of them reads the row on a hit. Deleting the row changes the truth and nothing that answers."], cls="dia")

S(plain(K(5, "the trace"), "Twenty minutes later, a victim still lands on the page", '<pre class="trace"><span class="t">15:00:00</span>row deleted (or status = blocked)\n<span class="t">15:00:00</span>still answering: shared cache (TTL <span class="bad">1 h</span>), 40 servers\' memory (60 s), edge in 30 cities (60 s)\n<span class="t">15:00:00</span>and browsers that got a 301 last week: <span class="bad">forever</span>\n<span class="t">15:20:00</span><span class="bad">a victim still lands on the phishing page</span>, from the shared cache</pre>' +
  '<div class="hedge"><b class="t">The real question</b>Not "how do we delete", but "what is the longest any copy can live after we decide".</div>', q=True, red=True), [
 "C: The trace. At three o'clock the status is set. Still answering: the shared cache with an hour's lifetime, forty servers' memory with sixty seconds, the edge in thirty cities with sixty seconds, and browsers that got a three-oh-one last week, forever. At three-twenty a victim still lands on the page, served from the shared cache.",
 "C: So the real question is not how to delete. It is: what is the longest any copy can live after we decide?"])

S(dia(K(5, "the fix"), "Status, a direct delete, an invalidation, and a lifetime at every layer", "ch5-fix",
      chip=chips("status", "direct delete", "invalidate", "purge", "410 Gone")), [
 "C: The fix, in the green boxes. The takedown writes blocked to the store. It deletes the shared-cache key directly and retries until it's confirmed: that cache has a long lifetime, so it must never depend on a lost message. It publishes an invalidation: every redirect server drops the code, and the edge is purged. The next request reads blocked and answers four-ten with a warning page.",
 "C: The property is S-two, and it holds by arithmetic. Here is the arithmetic."], cls="dia")

S(dia(K(5, "the budget"), "The worst case is a sum, and it fits", "takedown-budget", chip=chips("if the event is lost", "initial target")), [
 "C: The worst case, if the invalidation event is lost. Status and the shared-cache delete: a couple of seconds. The in-process lifetime: sixty. The edge lifetime: sixty. The purge call: a few. About two minutes, against five. The spare covers a slow purge and a retry. Every lifetime in this system was chosen with this bar in view."], cls="dia")

S(dia(K(5, "sequence"), "Status first, then every copy", "seq-takedown"), [
 "C: As a sequence once more, with the point that matters: the shared cache is deleted directly, not by the event, and only the short-lived layers depend on the event. If it is lost, their lifetimes end the copies. Four-ten Gone tells crawlers to stop asking."], cls="dia")

S(plain(K(5, "before the link exists"), "The cheapest takedown is the one you never need", '<div class="cards c3">'
  '<div class="cd grn"><h3>On create</h3><p>Check the URL against the classifier. Known-bad: 422, no code issued.</p></div>'
  '<div class="cd amb"><h3>After create</h3><p>When the classifier\'s list updates, rescan live links created recently and block matches through the same path.</p></div>'
  '<div class="cd"><h3>Audit</h3><p>Every takedown: who, why, when, and when each layer answered 410.</p></div></div>'), [
 "C: Two cheaper defences. On create, check the U-R-L against the classifier: if it's known-bad, no code is issued. And when the classifier's list updates, rescan recently created live links and block any matches through the same path. Every takedown is audited: who, why, when, and when each layer started answering four-ten."])

qs("Interviewer · the second-level push", "“The invalidation event is lost. Or the link was created as a 301.”", [
 "I: The invalidation event is lost. Or the link was created as a three-oh-one.", "[pause: 2.0]"])

S(plain(K(5, "the second fix, and the honest limit"), "Lifetimes are the backstop; a 301 cannot be recalled", '<div class="cards c2">'
  '<div class="cd grn"><h3>A lost event</h3><p>The lifetimes are the backstop by design: about two minutes. An hourly test takedown measures the real time at every layer (challenge eight).</p></div>'
  '<div class="cd red"><h3>A 301</h3><p>Cannot be recalled from a browser. That is why it is opt-in, and why the safety check runs before a 301 link is issued.</p></div></div>'), [
 "C: A lost event: the lifetimes are the backstop, by design, so the worst case is about two minutes. And an hourly test takedown measures the real time at every layer, which is challenge eight.",
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
 "C: The naive answer: increment a clicks column on every redirect. Look at the red store. That puts a write inside the redirect, on the row of the hottest link."], cls="dia")

S(plain(K(6, "the trace"), "Five milliseconds becomes nine hundred", '<pre class="trace"><span class="t">14:02</span>k7Pq2mZ at 40,000 clicks/s → <span class="bad">40,000 UPDATEs/s on one row</span>\n<span class="t">14:02</span>the row lock serialises them: one at a time\n<span class="t">14:03</span>each redirect waits for its write: p99 5 ms → <span class="bad">900 ms</span>\n<span class="t">14:04</span>the cache was fine. <span class="bad">the counter broke the redirect</span></pre>' +
  '<div class="hedge"><b class="t">Label the numbers</b>Illustrative. The cache had solved the read; the write put the hot key back on the critical path.</div>', q=True, red=True), [
 "C: The trace. Forty thousand updates a second on one row. The row lock serialises them. Each redirect waits for its write, and p ninety-nine goes from five milliseconds to nine hundred. The cache had solved the read. The counter put the hot key straight back on the critical path."])

S(dia(K(6, "the fix"), "Answer first, then record; count in batches", "ch6-fix",
      chip=chips("after the 302", "buffer → log → aggregate", "drops counted")), [
 "C: The fix, green along the bottom. After the three-oh-two goes out, the server appends an event to a local buffer. The buffer flushes a batch every second into a log partitioned by code. An aggregator counts per code per minute, then per day per country. If the buffer is full, events are dropped, and the drops are counted.",
 "C: L-two: nothing after the answer can delay it. L-three, with a measured loss: the drop counter is the loss, and counts say as-of."], cls="dia")

S(plain(K(6, "precision"), "Say exactly what the count promises", table(["Today (not billed)", "If clicks are billed"], [
  ["At-most-once from the server: a crash loses the unflushed second", "At-least-once: a durable buffer on disk, resent until acknowledged"],
  ["No event ID; drops counted and shown", "An event ID at the redirect; de-duplicated in the aggregator"],
  ["Bots counted as clicks", "Bots filtered before anything is billed"],
  ["Counts eventually consistent, minutes late", "Same lag; exact once settled; stated in the billing terms"]], "bt sm")), [
 "C: Precision about what the count promises. Today: at-most-once from the server, a crash loses the unflushed second, drops are counted and shown, bots are counted, and counts are minutes late.",
 "C: If clicks are billed: at-least-once with a durable buffer, an event I-D created at the redirect, de-duplication in the aggregator, so the effect is exactly once, and bots filtered before anything is billed. The redirect still never waits."])

qs("Interviewer · the second-level push", "“Product now bills per click. A lost click is lost money, and a double-counted one is a refund.”", [
 "I: Product now bills per click. A lost click is lost money, and a double-counted one is a refund.", "[pause: 2.0]"])

S(dia(K(6, "the second fix"), "Event IDs, a durable buffer, de-duplication", "seq-ch6-billed"), [
 "C: The second fix, as a sequence. The three-oh-two is already sent. The server appends the event, with an I-D, to a buffer on local disk. It flushes a batch every second and trims the buffer only on acknowledgement. Delivery to the aggregator is at least once, and the aggregator de-duplicates by event I-D, filters bots, and counts.",
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
                  ("case", "Break", "The store's primary and the allocator's leader were in the lost region."))), [
 "C: The naive answer: fail over the database. That's part of it, but look at what is red: the store's primary and the allocator's leader both lived in the lost region. Fail-over takes time, and during it, creates fail and every miss goes somewhere."], cls="dia")

S(plain(K(7, "the trace"), "Which requests fail, and which merely slow", '<pre class="trace"><span class="t">03:10</span>the primary region is lost\n<span class="t">03:10</span>redirects in Europe and Asia: 98 % from caches, <span class="bad">2 % miss to a store that is now read-only</span>\n<span class="t">03:10</span>creates: <span class="bad">fail</span>: the primary and the allocator\'s leader are gone\n<span class="t">03:11</span>bulk integrators retry, with their idempotency keys</pre>', q=True, red=True), [
 "C: The trace. At ten past three the primary region is lost. Redirects elsewhere: ninety-eight percent from caches, two percent miss to a store that is now read-only, which is fine for reads, if the reads are local. Creates fail, because the primary and the allocator's leader are gone. Bulk integrators retry with their idempotency keys."])

S(dia(K(7, "the fix"), "Redirects are regional; creates are regional too", "regions",
      extra=strip(("fixb", "Mechanism", "Each region has a replica of the link store and its own caches: a redirect never crosses regions. Each region leases from its own slice of the ID space, so it can create alone."),
                  ("whyb", "Property", "L2 depends only on regional state. S1 holds because the slices are disjoint."))), [
 "C: The fix. Redirects are regional: each region has a replica of the link store and its own caches, so a redirect never crosses a region. Creates are regional too: each region leases ranges from its own slice of the I-D space, Europe the first third, the Americas the second, Asia the last. A region can create without the others, and the store replicates asynchronously.",
 "C: L-two depends only on regional state. S-one holds because the slices are disjoint: no two regions can ever produce the same I-D."], cls="dia")

S(dia(K(7, "on the baseline"), "The replica beside the store", "ch7-fix"), [
 "C: On the baseline: the replica beside the link store, receiving asynchronous replication, and the shared cache reading from the local copy. Fail-over of a shard's primary is now only for writes to links created in the lost region, and those are rare: links are written once."], cls="dia")

qs("Interviewer · the second-level push", "“A link created in Asia is clicked in Europe two hundred milliseconds later, before replication.”", [
 "I: A link created in Asia is clicked in Europe two hundred milliseconds later, before replication.", "[pause: 2.0]"])

S(dia(K(7, "the second fix"), "One cross-region lookup, not an error", "seq-ch7-region"), [
 "C: The second fix, as a sequence. A code created in Asia two hundred milliseconds ago is clicked in Europe. Local miss. The code's slice of the I-D space says which region created it: Asia. One cross-region lookup, cache the answer here, and three-oh-two. One round trip slower, no error.",
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
 "C: The naive answer: error rate and C-P-U. Those watch boxes. The red one here is the shared cache, and nothing about it will show as an error."], cls="dia")

S(plain(K(8, "the trace"), "Nothing failed, and the morning peak paged", '<pre class="trace"><span class="t">01:55</span>a config change sets the shared cache\'s lifetime to 0\n<span class="t">02:00</span>errors 0; p50 unchanged; p99 6 ms → 18 ms\n<span class="t">02:00</span>store reads <span class="bad">40/s → 4,000/s</span>: nobody is watching\n<span class="t">09:00</span>the peak arrives: <span class="bad">the store saturates; the first page</span></pre>', q=True, red=True), [
 "C: The trace. Just before two in the morning, a config change sets the shared cache's lifetime to zero. No errors. Median unchanged. p ninety-nine creeps from six milliseconds to eighteen, still under target. Store reads go from forty a second to four thousand. Nobody is watching, and at nine, when the peak arrives, the store saturates and the first page fires. Seven hours late."])

S(dia(K(8, "the fix"), "Probe the path, in every region", "ch8-fix",
      extra=strip(("fixb", "Mechanism", "Synthetic probes in every region create a link and follow it through the edge every minute. Hourly, a test takedown is timed until every layer answers 410."),
                  ("whyb", "Property", "The SLI measures what the user gets, end to end, per region: latency, success, create-to-first-redirect, takedown time."))), [
 "C: The fix. Synthetic probes in every region create a link and follow it through the edge, every minute: redirect latency, success, and the time from create to first redirect. And every hour, a test link is blocked and timed until every layer answers four-ten. That's our takedown time, measured, not hoped for."], cls="dia")

S(plain(K(8, "symptom pairs"), "Two metrics, one cause", table(["When you see", "Together with", "It means"], [
  ["Cache hit rate down", "store reads up, traffic flat", "<b>a cold or misconfigured cache</b>, not more users (this trace)"],
  ["404 rate up", "creates flat", "<b>scanning</b>: someone is walking codes"],
  ["p99 up", "hit rate flat", "<b>something synchronous</b> crept onto the redirect path"],
  ["Click drops up", "buffer full on many servers", "<b>the log or the aggregator is slow</b>, not the redirect"],
  ["Takedown time up", "invalidation lag up", "<b>the channel is behind</b>: the lifetimes are carrying us"]], "bt sm")), [
 "C: Symptom pairs: two metrics, one cause. Hit rate down with store reads up and traffic flat: a cold or misconfigured cache, not more users. That's this trace, caught at two, not nine.",
 "C: Four-oh-fours up while creates are flat: someone is scanning codes. p ninety-nine up while hit rate is flat: something synchronous crept onto the redirect path. Click drops up with buffers full: the log is slow, not the redirect. Takedown time up with invalidation lag: the channel is behind, and the lifetimes are carrying us."])

S(dia(K(8, "sequence"), "The probe, minute by minute", "seq-ch8-probe"), [
 "C: The probe as a sequence. Create a test link. Follow it through the edge: three-oh-two in six milliseconds, create to first redirect in under half a second. Hourly, block a test link and poll every layer until four-ten. Today, seventy-four seconds, against five minutes."], cls="dia")

qs("Interviewer · the second-level push", "“The probes pass, but one country's DNS sends users to the wrong region.”", [
 "I: The probes pass, but one country's D-N-S sends users to the wrong region.", "[pause: 2.0]"])

S(plain(K(8, "the second fix"), "Real users, compared with the probes", '<div class="cards c2">'
  '<div class="cd grn"><h3>Real-user monitoring</h3><p>From edge logs, per country: latency and the region that answered. Probes say the path works; real users say they reach it.</p></div>'
  '<div class="cd amb"><h3>Alert on divergence</h3><p>Probes healthy and one country slow is the signal: routing, not our servers.</p></div></div>'), [
 "C: The probes prove the path works. They don't prove users reach the right path. So add real-user monitoring from edge logs, per country: latency and which region answered. When probes are healthy and one country is slow, that divergence is the alert, and it says routing, not our servers."])

say_slide("“I measure the path, not the boxes: probes that create a link and follow it in every region, and a test takedown every hour, timed until every layer answers 410. Then pairs of metrics give me causes: hit rate down with store reads up means a cold cache, not more traffic.”", [
 "V: If asked, I'd say: I measure the path, not the boxes. Probes create a link and follow it in every region, and a test takedown every hour is timed until every layer answers four-ten. Then pairs of metrics give me causes: hit rate down with store reads up means a cold cache, not more traffic.", "[pause: 1.0]"])

# ───────────────────────── 8 · build cost ─────────────────────────
chapter(8, "Build cost", 6, "Who, how long, buy or build: the manager layer", [
 "C: Build cost. This is the manager layer, marked aux: skip it in a pure Staff round, use it in a manager round."], aux=True)

S(plain("Build cost · three releases", "Not one project", table(["", "V1", "V2", "V3"], [
  ["Scope", "One service, one table, random codes, a cache", "Split paths, ranges, permutation, sharded store", "In-process cache, click pipeline, takedown channel, edge, regions"],
  ["People", "2", "+2", "a team of 5–6"],
  ["Time", "6 weeks", "2 months", "2 quarters"],
  ["On-call", "business hours", "shared rotation", "24/7, error budgets"]], "bt sm")), [
 "C: Three releases. Version one, one service and one table with random codes and a cache: two engineers, six weeks. Version two, split paths, ranges, the permutation and a sharded store: two more engineers, two months. Version three, the in-process cache, the click pipeline, the takedown channel, the edge and regions: a team of five or six for two quarters, with a twenty-four-seven rotation."], cls="aux")

S(plain("Build cost · two teams, one quarter", "Split along the contract", '<div class="cards c2">'
  '<div class="cd"><h3>Links and redirect</h3><p>Create, codes, store, caches, edge. Owns the redirect SLO and the takedown time.</p></div>'
  '<div class="cd grn"><h3>Clicks and trust</h3><p>Event pipeline, stats, the takedown service and its channel, the classifier integration.</p></div></div>' +
  line("The contract between them: the click event schema, and the invalidation channel.", "a")), [
 "C: If asked to split it across two teams for a quarter: links and redirect, owning create, codes, store, caches and the edge, and the redirect objective. And clicks and trust, owning the event pipeline, stats, the takedown service and the classifier. The contract between them is two things: the click event schema, and the invalidation channel."], cls="aux")

S(plain("Build cost · buy, build, or don't", "Most of this is bought", table(["Part", "Decision", "Why"], [
  ["Link store, cache, log", "buy managed", "commodity; the design is in how we use them"],
  ["Edge", "buy", "points of presence and a purge API"],
  ["URL classifier", "buy, or an internal service", "a specialist problem"],
  ["Code generation, redirect, takedown path", "build", "small, and it is the product"],
  ["The whole thing", "<b>don't</b>, if shortening is not our business", "an off-the-shelf shortener is a fine answer"]], "bt sm mx")), [
 "C: Buy, build, or don't. The store, the cache and the log are bought, managed. The edge is bought. The classifier is bought or an internal service. What we build is small: code generation, the redirect and the takedown path. And if shortening is not the business, the right answer may be: don't build it, use an off-the-shelf shortener. Say it."], cls="aux")

S(plain("Build cost · cost and risks", "The edge bill is the biggest line", '<div class="cards c2">'
  '<div class="cd amb"><h3>Cost, illustrative</h3><p>A handful of redirect servers at 4,000/s. 100 GB of cache RAM. 18 TB of storage. The edge is billed per request: at 10 billion a month, the largest line, which is why its default lifetime is a business decision.</p></div>'
  '<div class="cd red"><h3>Top risks</h3><p>The code format is a one-way door: codes are printed on paper. Takedown time untested until a real incident. Analytics becoming billing without the exactness work.</p></div></div>'), [
 "C: Cost, illustrative. A handful of redirect servers, a hundred gigabytes of cache memory, eighteen terabytes of storage. The edge is billed per request, and at ten billion a month it's the largest line, which is why its default lifetime is a business decision.",
 "C: Top risks. The code format is a one-way door: codes are printed on paper and live forever. Takedown time untested until a real incident. And analytics quietly becoming billing without the exactness work."], cls="aux")

# ───────────────────────── 9 · recap ─────────────────────────
chapter(9, "Recap", 7, "One picture, four paths, the mistakes, the thesis", [
 "C: To close: one picture, one sentence per path, the mistakes to avoid, and the thesis."])

S(dia("Recap", "The whole design on one baseline", "base-final", chip=chips("ranges", "permutation", "in-process cache", "302 + edge", "click log", "takedown channel", "probes")), [
 "C: The final picture. Create on top: a safety check, leased ranges, a permutation, an insert under the constraint. The redirect across the middle: edge, redirect service with its in-process cache, shared cache, link store, and a replica per region. Along the bottom: the click log, the aggregator and the stats, and the takedown with its invalidation channel. And probes in every region, following the path a user takes."], cls="dia")

S(plain("Recap · one sentence per path", "Four paths", table(["Path", "In one sentence"], [
  ["<b>Create</b>", "Check the URL, lease, permute, insert under the constraint"],
  ["<b>Redirect</b>", "Memory, then the shared cache, then the store; answer; then count"],
  ["<b>Count</b>", "Buffer, log, aggregate, and say how fresh"],
  ["<b>Withdraw</b>", "Status, a direct delete, invalidate, purge, and lifetimes that sum to under five minutes"]], "bt")), [
 "C: Four paths, one sentence each. Create: check the U-R-L, lease, permute, insert under the constraint. Redirect: memory, then the shared cache, then the store; answer; then count. Count: buffer, log, aggregate, and say how fresh. Withdraw: status, a direct delete, invalidate, purge, and lifetimes that sum to under five minutes."])

S(plain("Recap · eight fixes", "Each names the property it protects", table(["Challenge", "Fix", "Property"], [
  ["1 Two servers, one code", "leased ranges; the constraint decides", "S1, L1"],
  ["2 Codes in order", "keyed permutation; 404 rate limit", "non-enumerable"],
  ["3 One viral link", "in-process cache; single flight", "L2"],
  ["4 301 or 302", "302 default; edge 60 s; 301 opt-in", "S2, counting"],
  ["5 Takedown in 5 min", "status, direct delete, invalidation, lifetimes", "<b>S2</b>"],
  ["6 Counting", "after the answer; buffer, log, aggregate", "L2, L3"],
  ["7 A region lost", "regional replicas; ID slices", "L2, S1"],
  ["8 How would you know", "probes, test takedowns, symptom pairs", "all"]], "bt sm")), [
 "C: Eight fixes, each with its property. Ranges and the constraint, for uniqueness. A keyed permutation, against enumeration. In-process caching with single flight, for the viral link. Three-oh-two by default, for counting and takedowns. Status, a direct delete and bounded lifetimes, for the five minutes. Counting after the answer. Regional replicas and I-D slices. And probes that measure the path."])

S(plain("Recap · common mistakes in this round", "Nine ways this round goes wrong", '<div class="cards c2"><div class="cd red"><h3>Design</h3><ul style="font-size:17pt"><li>Hash and truncate, with no collision story</li><li>Six characters without the arithmetic</li><li>Check, then insert</li><li>A counter update on every click</li><li>Codes that are a counter in disguise</li></ul></div>'
  '<div class="cd amb"><h3>Judgment</h3><ul style="font-size:17pt"><li>“Add a cache” with no plan for one hot key</li><li>301 by default</li><li>Forgetting every cached copy must be withdrawable</li><li>No number on the takedown time</li></ul></div></div>'), [
 "C: Nine mistakes. In the design: hash and truncate with no collision story. Six characters without the arithmetic. Check, then insert. A counter update on every click. Codes that are a counter in disguise.",
 "C: In judgment: add a cache, with no plan for one hot key. Three-oh-one by default. Forgetting that every cached copy must be withdrawable. And no number on the takedown time."])

key("The close", "The redirect is <em>one memory read</em>. Codes are unique by <em>blocks and a constraint</em>, unguessable by a <em>key</em>. Everything else lives <em>beside</em> the redirect, with a number on how late it may be.", [
 "V: The redirect is the product, so it's one memory read, and nothing waits on anything else. Codes are unique because each server owns a block and the database has the last word, and unguessable because a key shuffles them. Everything else, counting, takedowns, the edge, lives beside the redirect, with a number on how late it may be.", "[pause: 1.2]",
 "C: Thank you. I'll stop there."])
