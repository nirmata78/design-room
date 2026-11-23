from dsl import *
import dsl

def th(): dsl.SL[-1]["cls"] = (dsl.SL[-1]["cls"] + " theory").strip()

chapter(3, "Theory", 2, "What makes this problem hard, in words that outlive any product name", [
 "C: A short theory chapter before the design, so the design can lean on it. Six parts: what a feed is and is not, the properties, the central tension, seven mechanisms, the options, and the failure catalogue."]); th()

key("Theory · 1 of 6 · what it is", "A <em>materialised view</em> per reader: a bounded, ranked list of recent <em>post IDs</em>, part precomputed, part fetched, <em>filtered</em> and hydrated within the budget.", [
 "V: A home feed is, for each reader, a bounded, ranked list of recent post I-Ds from the accounts they follow, assembled from a precomputed part and a part fetched at read time, then filtered and hydrated within the read budget.", "[pause: 1.0]",
 "C: Each clause carries weight. For each reader: it is a per-user view, so it can be lost and rebuilt. Bounded: a few hundred entries. Post I-Ds: never bodies. Precomputed plus fetched: the hybrid. Filtered: correctness happens at read. Within the budget: two hundred milliseconds, with a fallback."], cls="theory")

S(plain("Theory · 1 of 6 · what it is not", "Four things it is confused with", '<div class="cards c2">'
  '<div class="cd"><h3>Not the source of truth</h3><p>Posts are. The view may be wrong for seconds, and can be thrown away and rebuilt.</p></div>'
  '<div class="cd"><h3>Not a chat inbox</h3><p>An inbox may never lose a message. A feed may leave out an old post, and that is acceptable.</p></div>'
  '<div class="cd amb"><h3>Not search</h3><p>It answers one query shape: recent, followed, ranked. Another shape needs another path.</p></div>'
  '<div class="cd red"><h3>Not the ranking model</h3><p>Ranking is a stage with a budget, owned elsewhere.</p></div></div>'), [
 "C: Four neighbours. It is not the source of truth: posts are, and the view can be wrong for a few seconds and rebuilt. It is not a chat inbox: an inbox must never lose a message, while a feed may leave out an old post. It is not search: it answers one query shape, and challenge seven asks for a different one. And it is not the ranking model, which is a stage with a budget."], cls="theory")

S(plain("Theory · 2 of 6 · the two properties", "State safety and liveness separately",
  '<div class="prop safe"><div class="lbl">Safety · must never happen</div><p><b>S1</b> A viewer sees content they must not see (deleted, from a blocked account, outside its audience) for longer than 5 s.<br><b>S2</b> A post is lost: the source of truth is durable even if every view is lost.</p></div>'
  '<div class="prop live"><div class="lbl">Liveness · must eventually happen</div><p><b>L1</b> A post reaches its active followers\' feeds within 5 s, p95.<br><b>L2</b> Every feed open answers within 200 ms, degraded if it must.<br><b>L3</b> A lost or skipped timeline is rebuilt on its next open.</p></div>'), [
 "V: Safety: a viewer never sees content they must not see for longer than five seconds, and a post is never lost. Liveness: a post reaches active followers within five seconds, every feed open answers within two hundred milliseconds, and a lost timeline is rebuilt on its next open.", "[pause: 0.8]",
 "C: Most designs talk only about liveness, about speed. S-one is the safety property people forget: a feed made of copies will show a deleted post unless something stops it. Every fix from here names the property it serves."], cls="theory")

S(dia("Theory · 3 of 6 · the central tension", "Write amplification against read cost", "tension"), [
 "C: The central tension, as one picture. Push pays at post time, in proportion to the author's followers: the red curve rises as followers grow. Pull pays at read time, in proportion to the reader's followees: per post it is flat and small, but paid on every follower's open.",
 "C: The lines cross near the threshold. Below it push is cheaper; above it pull is. The hybrid simply follows the lower curve. Hold on to this picture: challenges one and two live on it."], cls="dia theory")

def mech(n, name, protects, how, rules, costs, say, live=True):
    S(plain(f"Theory · 4 of 6 · mechanism {n} of 7", name,
        f'<div class="prop {"live" if live else "safe"}"><div class="lbl">Property it protects</div><p>{protects}</p></div>'
        f'<div class="prop"><div class="lbl">How it works</div><p>{how}</p></div>'
        f'<div class="prop safe"><div class="lbl">Failure it rules out</div><p>{rules}</p></div>'
        f'<div class="prop" style="border-left-color:#d18f1c"><div class="lbl" style="color:#a86a12">What it costs</div><p>{costs}</p></div>'), say, cls="theory")

mech(1, "Fan-out on write into bounded ID lists", "L1 and L2: fresh, and one read per open.", "On each post, insert (post ID, author, time) into each active follower's sorted list, trimmed to 500. Keyed by post ID, so a repeat is a no-op.",
     "A feed open that touches 200 authors; duplicate entries when an event is delivered twice.", "120,000 inserts a second, a memory tier, and amplification on big authors.", [
 "C: Mechanism one, fan-out on write. It protects freshness and a cheap read. On each post, insert the post I-D, author and time into each active follower's sorted list, trimmed to five hundred, keyed by post I-D so a repeat is a no-op. It rules out a read that touches two hundred authors, and duplicates on re-delivery. It costs a hundred and twenty thousand inserts a second, a memory tier, and amplification on big authors."])
mech(2, "Fan-out on read from author indexes", "L2 for celebrities, and L3: rebuild.", "At read time, read each pulled author's recent post IDs from a per-author index, and merge. The same path rebuilds a lost timeline and answers catch-up.",
     "A hundred million writes for one post; a lost view staying lost.", "A merge per read. The author indexes must be fast, and protected from a stampede.", [
 "C: Mechanism two, fan-out on read. It protects the read for celebrities, and recovery. At read time, read each pulled author's recent post I-Ds from a per-author index and merge them. The same path rebuilds a lost timeline. It rules out a hundred million writes for one post, and a lost view staying lost. It costs a merge per read, and author indexes that must be protected from a stampede."])
mech(3, "A threshold, with transition rules and active-only targeting", "L1, and cost.", "Each author has a tier: push below the line, pull above it, push to recently active followers in the middle. The line has hysteresis, and crossing it needs no backfill.",
     "Pure push's celebrity, pure pull's read cost, and writes to users who never read.", "A tier per author to maintain, and a number to tune and defend.", [
 "C: Mechanism three, the threshold. Each author has a tier: push below the line, pull above, and push to recently active followers in between. The line has hysteresis, so an account near it does not flap, and crossing it needs no backfill. It rules out the celebrity problem, pure pull's read cost, and writes to users who never read. It costs a tier per author, and a number I must defend."])
mech(4, "IDs in the view, hydration through a post cache", "S1 (one place to delete), and memory.", "The view holds IDs only. The read path multi-gets the top 50 bodies from a post cache backed by the posts store.",
     "250 TB of copies; an edit or delete chasing millions of entries.", "A multi-get per page, and a post cache that becomes critical.", [
 "C: Mechanism four, I-Ds in the view and hydration through a post cache. It protects deletes, because there is one place to change, and memory. The view holds I-Ds; the read path fetches the top fifty bodies from a post cache. It rules out two hundred and fifty terabytes of copies and edits chasing millions of entries. It costs a multi-get per page, and a post cache that becomes critical."], live=False)
mech(5, "A visibility filter on the read path", "S1.", "Every page drops posts that are deleted or out of audience at hydration, and authors in the reader's block, mute and unfollow set at merge.",
     "A deleted or blocked post surviving in a precomputed copy.", "A small per-reader set read on every open.", [
 "C: Mechanism five, the visibility filter. It protects S-one. Every page drops posts that are deleted or out of audience when it hydrates them, and drops authors in the reader's block, mute and unfollow set when it merges. It rules out a deleted or blocked post surviving in a copy. It costs a small set read on every open."], live=False)
mech(6, "Ranking under a deadline, with a fallback", "L2.", "Call ranking with a hard deadline. On a miss, order by recency and close ties, or reuse the session's last ranking, and count it.",
     "A slow model making the whole feed slow or failing.", "Lower quality while degraded, which must be measured and owned.", [
 "C: Mechanism six, ranking under a deadline. It protects the two hundred milliseconds. Call ranking with a hard deadline; on a miss, order by recency and close ties, and count it. It rules out a slow model making the whole feed slow. It costs lower quality while degraded, which must be measured and owned by someone."])
mech(7, "Log-based fan-out with priority lanes", "L1 under bursts.", "The post and its event commit together (an outbox); a log keyed by author feeds the workers; close ties are fanned out first; the offset is committed last.",
     "A burst delaying close friends; fan-out work lost in a crash.", "A log and workers to run; lag becomes an SLI.", [
 "C: Mechanism seven, a log with priority lanes. The post and its event commit in one transaction, an outbox. A log keyed by author feeds the workers. Close ties are fanned out first, and the log offset is committed last, so a crash re-delivers rather than loses. It rules out a burst delaying close friends, and lost work. It costs a log to run, and makes lag a metric to watch."])

S(plain("Theory · 5 of 6 · the options matrix", "Six approaches, one pick", table(["Approach", "Read at 90,000/s", "Write per post", "Celebrity", "Fails when"], [
  ("rej", ["A · Pull with a database join at read time", "18 M reads/s", "1", "fine", "any real scale"]),
  ("rej", ["B · Pull with a per-reader result cache", "1 read, a merge on a miss", "1", "fine", "freshness, and the miss rate at peak"]),
  ("rej", ["C · Pure push of IDs", "1 read", "followers", "10⁸ inserts", "the first celebrity post"]),
  ("rej", ["D · Pure push of bodies", "1 read, no hydration", "followers × 1 KB", "10⁸ copies", "250 TB; every edit and delete"]),
  ("pick", ["E · Hybrid: push IDs to the active, pull celebrities, filter on read", "1 read + a small merge", "≤ 10⁴–10⁵", "pulled", "a line never measured; a power reader"]),
  ("rej", ["F · Buy a managed feed service", "theirs", "theirs", "theirs", "our ranking and privacy rules; cost at 10⁹ users"])], "bt xs mx")), [
 "C: Six approaches, each with the failure that rules it out. A, pull with a database join: fails at any real scale. B, pull with a per-reader result cache: fine until freshness and the miss rate at peak bite. It is my first version. C, pure push of I-Ds: fails on the first celebrity post. D, pure push of bodies: two hundred and fifty terabytes, and every edit chases copies.",
 "C: E is the hybrid: push I-Ds to active followers of ordinary authors, pull celebrities, hydrate, and filter on read. It fails if the threshold is set once and never measured, and on a reader who follows hundreds of celebrities, which is challenge two. F, buy a managed feed service: it fails on our own ranking and privacy rules, and on cost at a billion users.",
 "V: I pick E, built after B as the first version.", "[pause: 0.8]"], cls="theory")

S(plain("Theory · 5 of 6 · the pick, and what it gives up", "E, after B, with the line measured", '<div class="cards c2">'
  '<div class="cd grn"><h3>What the pick buys</h3><p>A feed open that costs one memory read and a small merge. Writes bounded per post. Deletes that are one write. A view that can be rebuilt.</p></div>'
  '<div class="cd red"><h3>What it gives up</h3><p>Strict freshness: seconds of eventual consistency. Simplicity: two paths, a tier per author, and a number to defend.</p></div></div>' +
  line("When is B enough? Until the merge on a cache miss breaks the 200 ms budget at peak. Measure it, then move.", "a")), [
 "C: What the pick gives up, plainly. Strict freshness: a post appears within seconds, not instantly. And simplicity: two paths, a tier per author, and a number I must defend. What it buys: a feed open that costs one memory read and a small merge, writes bounded per post, deletes that are one write, and a view that can be thrown away and rebuilt.",
 "C: And B is not wrong. It is right until the merge on a cache miss breaks the budget at peak. I'd measure that before building E."], cls="theory")

S(plain("Theory · 6 of 6 · the failure catalogue", "What will go wrong", table(["#", "Failure", "Becomes"], [
  ["F1", "The celebrity post; a burst of ordinary posts", "<b>Challenge 1</b>"],
  ["F2", "An account crossing the line; the mid tier; the power reader", "<b>Challenge 2</b>"],
  ["F3", "Delete, block, unfollow, audience change", "<b>Challenge 3</b>"],
  ["F4", "Duplicates; a feed that moves while you scroll", "<b>Challenge 4</b>"],
  ["F5", "A timeline shard lost; the rebuild stampede", "<b>Challenge 5</b>"],
  ["F6", "The ranker is slow", "<b>Challenge 6</b>"],
  ["F7", "A query the view was not built for", "<b>Challenge 7</b>"],
  ["F8", "The feed works, but got worse", "<b>Challenge 8</b>"]], "bt sm")), [
 "C: The failure catalogue, which becomes the challenge list. The celebrity post, and bursts. An account crossing the line, and the reader who follows hundreds of celebrities. Deletes and blocks. Duplicates, and a feed that moves while you scroll. A lost shard and the rebuild stampede. A slow ranker. A query the view was not built for. And the feed that works but got worse. Eight challenges, in that order."], cls="theory")

S(plain("Theory · what each mechanism serves", "Safety or liveness, never unnamed", table(["Mechanism", "Serves", "Where it returns"], [
  ["M1 Fan-out on write, bounded IDs", "L1, L2", "challenges 1 and 4"],
  ["M2 Fan-out on read", "L2, L3", "challenges 1, 5 and 7"],
  ["M3 Threshold and tiers", "L1, cost", "challenge 2"],
  ["M4 IDs and hydration", "<b>S1</b>, memory", "challenge 3"],
  ["M5 Visibility filter", "<b>S1</b>", "challenge 3"],
  ["M6 Ranking deadline", "L2", "challenge 6"],
  ["M7 Log with priority lanes", "L1", "challenges 1 and 8"]], "bt sm") +
  grade("Every mechanism names the property it protects. A mechanism with no stated property is decoration.")), [
 "N: Good theory has a consequence for the design. Every mechanism here names the property it serves and where it returns.",
 "C: That is the vocabulary. On to the A-P-I and the data."], cls="theory")
