from dsl import *

# ───────────────────────── 0 · cold open ─────────────────────────
chapter(0, "Cold open", -1, "Design the home feed for a social network", [
 "C: The news feed is the question everyone has seen. Push or pull, and the textbook says: both. Interviewers keep asking it anyway, because the grade is not on the word hybrid. It is on what comes after it: where the line sits and why, what happens to the account that crosses it, how a deleted post leaves millions of copies, and what the feed does when the ranker is slow or a cache shard is gone."])

qs("Interviewer · the prompt", "“Design the home feed for a social network with a billion users: the ranked list of posts a user sees when they open the app.”", [
 "I: Design the home feed for a social network with a billion users. The ranked list of posts a user sees when they open the app.", "[pause: 1.5]"])

S(dia("Why it is harder than it looks", "A few accounts carry most of the write cost", "tail",
      chip=chips("median ~200 followers", "the largest: 110 million", "one post, one insert per follower")), [
 "C: Here is the hook. Followers per account, on a log scale. The median account has about two hundred followers. The top one percent has around ten thousand. And the largest have over a hundred million.",
 "C: If I precompute feeds by copying each post into every follower's list, the cost of one post is its author's follower count. For the median author that is nothing. For the account on the bottom row it is a hundred million writes, for one post. The tail decides the architecture, not the average."], cls="dia")

S(plain("Before the design", "What this question grades", table(["Axis", "Weak signal", "Strong signal"], [
  ["<b>Requirements</b>", "“Posts from friends, sorted by time”", "Asks the follower distribution and finds the tail; asks “twice or never: which is worse?”; numbers on freshness and latency"],
  ["<b>Correctness</b>", "Copies of posts treated as the truth", "IDs only, hydrated from the source; filters on read; idempotent inserts; a stable cursor"],
  ["<b>Trade-offs</b>", "Picks push or pull and defends it", "The hybrid with a threshold derived from arithmetic, and what it costs"],
  ["<b>Depth</b>", "Stops at “add a cache”", "Crossing the threshold with no backfill; rebuild under a stampede; ranking under a deadline"],
  ["<b>Operations</b>", "Uptime of the feed API", "Freshness as an SLI from synthetic accounts; quality metrics; the memory bill and its lever"]], "bt sm sig") +
  grade("The word “hybrid” earns nothing on its own. The line, the arithmetic behind it and the crossing rules do.")), [
 "N: Five axes. The weak signal is a clean push design or a clean pull design, defended well. The strong signal is the arithmetic that puts a line between them, and what happens on the read path to keep the feed correct.",
 "C: I'll keep one question in view the whole way: where does correctness live? Because a feed is full of copies, and copies go stale."])

key("The thesis", "Push IDs for ordinary accounts, <em>pull</em> the celebrities, say <em>where the line is</em> and why, and keep every correctness rule <em>on the read path</em>.", [
 "V: A feed is a materialised view that is cheap to read for almost everyone and impossible to precompute for a few. So: push post IDs to the followers of ordinary accounts, pull the celebrities at read time, say where the line is and why, and keep every correctness rule on the read path.", "[pause: 1.0]",
 "C: Concretely: a durable source of truth for posts, a small precomputed list of post IDs per reader, a merge of a few celebrity lists when the feed opens, and a read path that filters, ranks under a deadline and hydrates, all inside two hundred milliseconds."])

S(plain("The order I will follow", "Scope, numbers, theory, a simple design, then I break it",
  '<div class="ribbon" style="margin-top:14pt">' + "".join(f"<span>{x}</span>" for x in STAGES) + '</div>' +
  '<div class="cards c3" style="margin-top:18pt"><div class="cd"><h3>First</h3><p>Requirements and scope. Numbers. A short theory chapter.</p></div>'
  '<div class="cd grn"><h3>Then</h3><p>API and data. A design in three versions, each answering the objection to the one before.</p></div>'
  '<div class="cd red"><h3>Most of the time</h3><p>Eight challenges that break it. A build cost. A recap.</p></div></div>'), [
 "C: The order. Requirements and scope, then numbers, then a short theory chapter. Then the A-P-I and data, and a design in three versions, each answering the objection to the one before.",
 "C: Then most of the time: eight challenges that break the design, where each fix creates the next question. A build cost, because someone has to staff this. And a recap."])

# ───────────────────────── 1 · requirements ─────────────────────────
chapter(1, "Requirements and scope", 0, "Ask first. Cut on purpose. Put numbers on it.", [
 "C: Eight questions before I draw anything. Each answer is used later."])

def clar(n, q, a, say):
    S(f'<div class="who">Clarifying question {n} of 8</div><div class="qq">{q}</div><div class="ans">{a}</div>', say, cls="qs")

clar(1, "How many users, and how many open the app?", "1 billion users, 500 million daily active.", [
 "C: How many users, and how many are active?",
 "I: A billion users. Five hundred million daily active.",
 "C: Daily active is the number that matters. It sizes the reads and the memory, because only active users need a precomputed feed."])
clar(2, "Read to write?", "Feed reads are about 100 times post writes.", [
 "C: What is the ratio of reads to writes?",
 "I: Feed reads are about a hundred times post writes.",
 "C: So I optimise the read path and accept paying on the write path. That is the argument for precomputing at all."])
clar(3, "How many accounts does a user follow, and how is it distributed?", "Average about 200. On the other side: some accounts have over 100 million followers.", [
 "C: How many accounts does a user follow, and what does the distribution look like?",
 "I: About two hundred on average. And on the other side, some accounts have over a hundred million followers.",
 "C: That is the tail from the cold open. Asking about the distribution, not just the average, is the question that changes the design."])
clar(4, "Latency, and ranked or chronological?", "p99 under 200 ms for the first page. Ranked; a scoring service exists, treat it as a black box.", [
 "C: What latency, and is the feed ranked?",
 "I: P-ninety-nine under two hundred milliseconds for the first page. Ranked. A scoring service exists. Treat the model as a black box.",
 "C: Good. Ranking becomes a stage with a budget inside the two hundred, not the problem I'm solving."])
clar(5, "How fresh?", "Seconds for close follows; a minute is tolerable generally.", [
 "C: How fresh must the feed be?",
 "I: Seconds for people you follow closely. A minute is tolerable in general.",
 "C: That rules out strict consistency and allows asynchronous fan-out. It also says close ties deserve priority."])
clar(6, "How deep?", "The first 50 posts on open, paginated after.", [
 "C: How deep do readers go?",
 "I: The first fifty on open, paginated after that.",
 "C: So a precomputed list can be bounded. A few hundred entries cover almost every session."])
clar(7, "Content?", "Text and images. Video is out of scope.", [
 "C: What content types?",
 "I: Text and images. Video is out of scope.",
 "C: Bodies and media are hydrated separately from the feed. The feed itself only needs to hold references."])
clar(8, "Which is worse: seeing a post twice, or missing one?", "Missing a close friend's post is worse. A duplicate on screen is a bug.", [
 "C: Which is worse: seeing a post twice, or missing one?",
 "I: Missing a close friend's post is worse. A duplicate on screen is a bug.",
 "C: That gives me a correctness stance. De-duplicate always, and treat a missed close-tie post as the failure that matters. Challenge four comes from this answer."])

S(plain("Requirements · functional", "Four things the system must do", '<div class="cards c2">'
  '<div class="cd"><h3>FR1 · Publish</h3><p>A post with text and images, visible to the author\'s followers.</p></div>'
  '<div class="cd"><h3>FR2 · Read</h3><p>The ranked home feed: the first 50, then paginated with a stable cursor.</p></div>'
  '<div class="cd amb"><h3>FR3 · Follow</h3><p>Follow and unfollow, with effect on the feed.</p></div>'
  '<div class="cd red"><h3>FR4 · Remove</h3><p>Delete a post, block an account, change a post\'s audience: gone from every feed within seconds.</p></div></div>'), [
 "C: Functionally, four things. One, publish a post with text and images, visible to followers. Two, read the ranked home feed: the first fifty, then pages with a stable cursor.",
 "C: Three, follow and unfollow, with an effect on the feed. Four, remove: delete a post, block an account, or change who can see a post, and have it gone from every feed within seconds. Each of these gets a numbered flow later."])

S(plain("Requirements · non-functional", "The numbers, and what each is for", '<p class="chips">all initial targets, not measurements</p><div class="tiles" style="--n:4">'
  '<div class="tile"><b>200 ms</b><span>feed p99, first page</span></div>'
  '<div class="tile blue"><b>5 s</b><span>post visible to active followers, p95</span></div>'
  '<div class="tile"><b>99.95 %</b><span>read availability</span></div>'
  '<div class="tile red"><b>5 s</b><span>deleted or blocked content gone</span></div></div>' +
  line("And a post is never lost: the source of truth is durable; every feed may be rebuilt from it.", "g")), [
 "C: Non-functional, with numbers. These are initial targets, not measurements. P-ninety-nine under two hundred milliseconds for the first page. A new post visible to active followers within five seconds at p-ninety-five. Read availability of ninety-nine point nine five percent. Deleted or blocked content gone within five seconds.",
 "C: And one more: a post is never lost. The posts store is the source of truth. Every feed is derived, and can be rebuilt from it."])

S(plain("Scope", "In, and out on purpose", '<div class="cards c2">'
  '<div class="cd grn"><h3>In</h3><p>Publish. Build and serve the feed. Pagination. Follow effects. Deletes, blocks and audience. Ranking integration under a budget.</p></div>'
  '<div class="cd red"><h3>Out, on purpose</h3><p>The ranking model. Ads. Media upload and transcoding. Search. Notifications (SD-12). The graph service internals (SD-14). Like and comment counters.</p></div></div>' +
  grade("An explicit out list is a strong signal. Going deep on the ranking model is a rabbit hole the interviewer will redirect.")), [
 "C: In scope: publish, the feed itself, pagination, follow effects, deletes, blocks and audience changes, and ranking as a stage with a budget.",
 "C: Out, on purpose. The ranking model itself. Ads. Media upload and transcoding. Search. Notifications, which is its own question. The social graph's internals, which I'll treat as a service. And like and comment counters, which belong to a separate counter service.",
 "N: An explicit out list scores. Going deep on the ranking model is the classic rabbit hole here."])

key("The core", "Four things: a <em>source of truth</em> for posts, a <em>per-reader view</em> built by push and pull, a <em>read path</em> inside 200 ms, and a <em>rebuild path</em>.", [
 "C: So the core is four things. A source of truth for posts. A per-reader view, built by push for most authors and pull for a few. A read path that filters, ranks and hydrates inside two hundred milliseconds. And a rebuild path for when the view is lost, because it will be."])

# ───────────────────────── 2 · estimates ─────────────────────────
chapter(2, "Estimates", 1, "Every number with its arithmetic, a label, and the decision it drives", [
 "C: Numbers next. Each one comes with its arithmetic and the decision it changes. All of them are illustrative, built from the interviewer's inputs, not measurements."])

S(plain("Estimates · reads", "Ninety thousand feed opens a second at peak", '<p class="chips">given → derived</p>' +
  tex(r"\frac{500\,\text{M} \times 5\ \text{opens}}{86{,}400\ \text{s}} \approx 29{,}000/\text{s} \quad\times 3\ \text{peak} \approx 90{,}000/\text{s}") + '' +
  strip(("whyb", "Decision", "Served from memory. A database query per feed open is out from the start."), cols="one")), [
 "C: Reads. Five hundred million daily users, five opens a day each, over eighty-six thousand four hundred seconds: about twenty-nine thousand feed opens a second on average. With a peak factor of three, about ninety thousand a second.",
 "C: The decision: the feed is served from memory. A database query per open is out from the start."])

S(plain("Estimates · the cost of pure pull", "Eighteen million reads a second", '<p class="chips">derived</p>' +
  tex(r"90{,}000\ \text{opens/s} \times 200\ \text{followees} = 18\ \text{million author-index reads/s}") + '' +
  strip(("case", "Consequence", "Computing every feed at read time, by merging 200 authors' recent posts, is too expensive at this scale."),
        ("fixb", "But", "At one percent of this scale it is fine. It is the honest first version."))), [
 "C: Now the cost of computing every feed when it is opened. Ninety thousand opens a second, each merging the recent posts of two hundred followed accounts: eighteen million reads a second on the author indexes.",
 "C: That rules out pure pull at this scale. But at one percent of this scale it is fine, and I'll say so: it is the honest first version."])

S(plain("Estimates · writes and fan-out", "Six hundred posts a second become a hundred and twenty thousand inserts", '<p class="chips">illustrative → derived</p>' +
  tex(r"\frac{500\,\text{M} \times 0.1}{86{,}400} \approx 580\ \text{posts/s} \qquad 580 \times 200 \approx 120{,}000\ \text{inserts/s}") + '' +
  strip(("whyb", "Decision", "Pushing post IDs into followers' lists multiplies writes by 200. Affordable for ordinary authors: a cluster handles it."), cols="one")), [
 "C: Writes. If a tenth of daily users post once a day, that is about five hundred eighty posts a second. Tiny at the source. If each post is copied into two hundred followers' lists, that is about a hundred and twenty thousand inserts a second.",
 "C: Push multiplies writes by two hundred. For ordinary authors that is affordable: an in-memory cluster takes it."])

S(plain("Estimates · the cheapest win", "Skip followers who never read", '<p class="chips">illustrative · to be measured</p>' +
  tex(r"120{,}000 \times \tfrac{1}{2}\ \text{(followers active in 30 days)} \approx 60{,}000\ \text{inserts/s}") + '' +
  strip(("whyb", "Decision", "Fan out only to followers active in the last 30 days. A returning user's feed is rebuilt by pull on their first open."), cols="one")), [
 "C: The cheapest big win. Suppose about half of a typical account's followers haven't opened the app in thirty days. Then half the inserts go to lists nobody reads. Skip them: about sixty thousand a second instead of a hundred and twenty.",
 "C: The fraction is an assumption to measure. The decision holds either way: fan out only to active followers, and rebuild a returning user's feed by pull on their first open."])

S(plain("Estimates · the number that matters", "One celebrity post", '<p class="chips">derived</p>' +
  tex(r"1.1 \times 10^{8}\ \text{followers} \div 120{,}000\ \text{inserts/s} \approx 900\ \text{s} \approx 15\ \text{min}") + '' +
  strip(("case", "Consequence", "One post holds the whole fan-out fleet for a quarter of an hour, and everyone else's posts wait behind it."),
        ("fixb", "Decision", "Pure push dies here. Celebrities are pulled at read time."))), [
 "C: Now the number that matters. One celebrity with a hundred and ten million followers posts. At the whole fleet's hundred and twenty thousand inserts a second, that one post takes about nine hundred seconds, fifteen minutes. And every ordinary author posting in that window waits behind it.",
 "V: One celebrity post would be a hundred million writes. That number kills pure push.", "[pause: 0.8]"])

S(plain("Estimates · where the line goes", "Both sides of the threshold", table(["Side", "Arithmetic", "What it says"], [
  ["Write", "10,000 followers ≈ 0.08 s of the fleet; 1 M followers ≈ 8 s", "above ~10⁵, one post alone misses the 5 s freshness target"],
  ["Read", "each pulled author ≈ 0.5 ms; 20 of them ≈ 10 ms", "the average reader must pull only a handful of authors"],
  ["Result", "push below ~10⁴–10⁵ followers, pull above", "a config value, tuned with data"]], "bt sm") +
  '<div class="hedge"><b class="t">Label the numbers</b>Illustrative. The shape matters: both sides of the line have a cost, and the line sits where both are acceptable.</div>'), [
 "C: Where does the line go? From both sides. Write side: a ten-thousand-follower post is about eight hundredths of a second of the fleet. A million-follower post is about eight seconds, past the five-second freshness target on its own.",
 "C: Read side: each pulled author costs about half a millisecond per open. Twenty of them, ten milliseconds of the budget. So the line sits around ten to a hundred thousand followers, as a config value I tune with data. Challenge two returns to this."])

S(dia("Estimates · memory", "Store IDs, not bodies", "memory", chip=chips("500 M × 500 × 16 B = 4 TB", "× 3 replicas = 12 TB", "bodies: ~250 TB")), [
 "C: Memory. Five hundred million active users, five hundred entries each, sixteen bytes an entry for a post I-D, author I-D and time packed together: four terabytes, twelve with three replicas. That fits a memory tier.",
 "C: If each entry held the post body, about a kilobyte, it would be two hundred and fifty terabytes, sixty times larger. And every edit or delete would chase millions of copies. So the precomputed list holds I-Ds, and bodies are hydrated from one post cache."], cls="dia")

S(dia("Estimates · the read budget", "Two hundred milliseconds, spent on purpose", "budget"), [
 "C: The read budget, as one bar. Lookups and filtering, about twenty milliseconds: the timeline, the celebrity lists, the block set. Ranking gets a hard deadline of eighty. Hydrating fifty posts, about twenty. Network and serialisation, twenty. A hundred and forty used, sixty spare.",
 "C: The decision: ranking gets a deadline and a fallback, because it is the largest piece and it belongs to another team."], cls="dia")

S(plain("Estimates · a lost shard", "Rebuilds after losing one cache shard", '<p class="chips">illustrative</p>' +
  tex(r"\frac{5\,\text{M users} \times 20\%}{600\ \text{s}} \approx 1{,}700\ \text{rebuilds/s} \times 200 \approx 340{,}000\ \text{reads/s}") + '' +
  strip(("whyb", "Decision", "A rebuild path needs coalescing, a rate limit and a degraded mode. Challenge five."), cols="one")), [
 "C: One more, because it shapes a failure path. Lose one cache shard out of a hundred: five million users. If a fifth of them open the app in the next ten minutes, that is about seventeen hundred rebuilds a second, each reading two hundred author indexes: three hundred and forty thousand reads a second on a store sized for something much smaller.",
 "C: So the rebuild path needs coalescing, a rate limit and a degraded mode. That is challenge five."])

S(plain("Estimates · summary", "Each number, and the decision it drove", table(["Number", "Decision"], [
  ["90,000 opens/s", "serve from memory"],
  ["18 M reads/s for pure pull", "precompute for most readers; pull is the MVP and the rebuild path"],
  ["120,000 → 60,000 inserts/s", "push IDs to active followers only"],
  ["One post, 110 M followers ≈ 15 min", "pull celebrities"],
  ["Line at ~10⁴–10⁵ followers", "a config value, measured"],
  ["4 TB of IDs against 250 TB of bodies", "IDs in the view; hydrate from one cache"],
  ["80 of 200 ms for ranking", "a deadline and a fallback"]], "bt sm") +
  grade("A number that never changes a decision is decoration. Each row here ends in a design choice.")), [
 "N: Every number on this slide ends in a decision. That is what the estimation phase is graded on.",
 "C: Serve from memory. Precompute for most, with pull as the first version and the rebuild path. Push only to active followers. Pull the celebrities, with a measured line. I-Ds, not bodies. And a deadline for ranking."])
