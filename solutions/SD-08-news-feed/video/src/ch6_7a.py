from dsl import *

# ───────────────────────── 6 · bridge ─────────────────────────
chapter(6, "Bridge", 4, "It works. Where does it break first?", [
 "V: It works. The question now is where it breaks first.", "[pause: 1.0]"])

S(dia("Challenge map", "Eight attack points on the same baseline", "map", chip=chips("each fix creates the next question")), [
 "C: The baseline with the attack points marked in red. The fan-out workers, for the celebrity and for bursts. The celebrity lists and the timelines, for the threshold, for duplicates and for a lost shard. The feed service, for deletes and pagination. And ranking, for its deadline. Then a new kind of query, and the question of how we'd know. Eight challenges, in an order where each fix creates the next question."], cls="dia")

chapter(7, "Challenges", 5, "Eight ways to break it, and what survives", [
 "C: Each challenge runs the same way: the question, the naive answer, a case with numbers, where it breaks, the fix, why it works, then the interviewer pushes on the fix itself, and I say what I'd say in the room."])

K = lambda n, t: f"Challenge {n} of 8 · {t}"

# ───────── Challenge 1 · the celebrity post ─────────
subchapter("7.1", "Challenge 1: The celebrity post", ["N: Challenge one, the crux. Someone with a hundred million followers posts: what happens, write by write?"])
qs("Interviewer · challenge 1 of 8", "“Someone with a hundred million followers posts. Walk me through it.”", [
 "I: Someone with a hundred million followers posts. Walk me through it.", "[pause: 2.0]"])

S(dia(K(1, "the celebrity post"), "What does one post cost?", "ch1-attack", q=True, red=True,
      extra=strip(("case", "Naive answer", "“The fan-out workers push it to every follower. We add more workers.”"),
                  ("case", "Break", "The fan-out fleet and the log partition: one author's post blocks everyone else's."))), [
 "C: The naive answer: the workers push it to every follower, and if that is slow we add workers. Look at the red: the fan-out workers and the arrows into the timelines. One post becomes a hundred million inserts, and the log partition holding it is blocked until they finish."], cls="dia")

S(plain(K(1, "the trace"), "Fifteen minutes for one post", '<pre class="trace"><span class="t">20:00:00</span>@star (110 M followers) posts\n<span class="t">20:00:00</span>110 M inserts at the fleet\'s 120,000 a second = <span class="bad">about 15 minutes</span>\n<span class="t">20:00:30</span>@ana posts to her 300 friends; her event waits behind @star\'s\n<span class="t">20:14:10</span><span class="bad">@ana\'s close friends see her post 14 minutes late</span>\n<span class="t">20:31:00</span>@star posts again: the next quarter of an hour is gone</pre>' +
  '<div class="hedge"><b class="t">Label the numbers</b>Illustrative. Even at ten times the fleet capacity, one post costs ninety seconds of all of it.</div>', q=True, red=True), [
 "C: The trace. At eight o'clock a star with a hundred and ten million followers posts. At the whole fleet's hundred and twenty thousand inserts a second, that takes about fifteen minutes. Thirty seconds later, Ana posts to her three hundred friends, and her event waits behind the star's. Her friends see it fourteen minutes late. And the star posts again at half past.",
 "C: Illustrative numbers, but the shape holds at any fleet size. Even ten times the capacity spends ninety seconds of all of it on one post."])

S(dia(K(1, "the fix"), "Don't fan out celebrities: pull them at read time", "ch1-fix",
      extra=strip(("fixb", "Mechanism", "Above the line: one entry in the author's recent list; readers merge it."),
                  ("whyb", "Property", "L1: no author holds the log. L2: readers pay a few budgeted reads."))), [
 "C: The fix. The event carries the author's tier. Above the threshold the worker writes one entry to that author's recent list, the dashed arrow, and is done. On the read path, the feed service merges the recent lists of the celebrities this reader follows. One write instead of a hundred and ten million."], cls="dia")

S(dia(K(1, "sequence"), "One write on publish, a small merge on read", "seq-celebrity"), [
 "C: As a sequence. The star's event arrives with tier pull. The worker appends the post I-D to the star's list: one write. The partition is free again in milliseconds. Later, a reader opens the feed. The feed service reads the lists of the six celebrities this reader follows, merges them with the timeline, and de-duplicates by post I-D. One ranked feed."], cls="dia")

S(plain(K(1, "why it works"), "The cost moved to where it is small", table(["", "Push the celebrity", "Pull the celebrity"], [
  ["Per post", "110 M inserts, ~15 min of the fleet", "1 write"],
  ["Per open", "nothing extra", "1 cache read per followed celebrity, ~0.5 ms"],
  ["Who pays", "every other author, in delay", "the reader, inside the budget"]], "bt sm") +
  strip(("whyb", "Why", "Pull costs a small read multiplied by opens; push costs a write multiplied by followers. For the tail, the read is far cheaper. The hot lists are replicated to many cache nodes."), cols="one")), [
 "C: Why it works, in one table. Pushing the celebrity costs a hundred and ten million inserts per post, paid by every other author in delay. Pulling costs one write per post, and one small cache read per followed celebrity per open, paid by the reader inside the budget. Those celebrity lists are hot keys, so they are replicated to many cache nodes."])

qs("Interviewer · the second-level push", "“New Year's Eve: ten times the normal posting rate, all ordinary accounts, for ten minutes.”", [
 "I: New Year's Eve. Ten times the normal posting rate, all ordinary accounts, for ten minutes.", "[pause: 2.0]"])

S(plain(K(1, "the second fix, and the honest limit"), "Priority lanes, and a pull that covers lag", '<div class="cards c3">'
  '<div class="cd grn"><h3>Priority lanes</h3><p>Fan out to close-tie followers first (an interaction score), the rest after. Close friends keep their seconds.</p></div>'
  '<div class="cd"><h3>Spread the burst</h3><p>The log is keyed by author, so a burst of many authors spreads across partitions and workers.</p></div>'
  '<div class="cd amb"><h3>Pull covers lag</h3><p>Lag is a metric per lane. While the general lane is behind, the read merge can pull recent posts of a reader\'s top ties.</p></div></div>' +
  line("Honest limit: for ten minutes, the “a minute generally” target may slip. Close ties keep their seconds.", "r")), [
 "C: A burst of ordinary posts is a different problem: no single author is the issue, the volume is. Three things. Priority lanes: fan out to close-tie followers first, the rest after. Partitioning by author, so the burst spreads across the fleet. And lag measured per lane, so that while the general lane is behind, the read merge can pull recent posts from a reader's top ties.",
 "C: The honest limit: for those ten minutes, the general one-minute target may slip. Close friends keep their seconds."])

say_slide("“One celebrity post would be a hundred million writes, minutes of fan-out that block everyone else. So above a follower threshold I don't fan out at all: the post goes into a small recent-posts list for that author, and each reader merges the few celebrities they follow at read time. That costs a few milliseconds per open, which I've budgeted.”", [
 "V: If asked, I'd say: one celebrity post would be a hundred million writes, minutes of fan-out that block everyone else. So above a follower threshold I don't fan out at all. The post goes into a small recent-posts list for that author, and each reader merges the few celebrities they follow at read time. That costs a few milliseconds per open, which I've budgeted.", "[pause: 1.0]",
 "N: That fix creates the next question: where exactly is the threshold?"])

# ───────── Challenge 2 · the threshold ─────────
subchapter("7.2", "Challenge 2: Where is the line, and who crosses it?", ["N: Challenge two, the second half of the crux. Where exactly is the line, and what happens to an account that crosses it overnight?"])
qs("Interviewer · challenge 2 of 8", "“Where exactly is the threshold, and what happens to an account that crosses it?”", [
 "I: Where exactly is the threshold, and what happens to an account that crosses it?", "[pause: 2.0]"])

S(dia(K(2, "the line"), "A number nobody can justify", "ch2-attack", q=True, red=True,
      extra=strip(("case", "Naive answer", "“A million followers.”"),
                  ("case", "Break", "The tier decision: a fixed number with no arithmetic, and no rule for crossing it."))), [
 "C: The naive answer is a round number: a million followers. Look at the fan-out box and both of its outputs in red. The routing decision rests on a number with no arithmetic behind it, and no rule for what happens when an account crosses it."], cls="dia")

S(plain(K(2, "the trace"), "Three ways a fixed number fails", '<pre class="trace"><span class="t">at 1 M  </span>one post = 10⁶ inserts ≈ <span class="bad">8 s of the whole fleet</span>: past the 5 s target on its own\n<span class="t">Mon     </span>@newstar has 9,000 followers: tier push\n<span class="t">Tue     </span>@newstar has 2 M: 200 posts already pushed; <span class="bad">which tier now, and what about those?</span>\n<span class="t">reader  </span>follows 5,000 accounts, 300 celebrities: <span class="bad">300 lists × 0.5 ms = 150 ms</span></pre>' +
  '<div class="hedge"><b class="t">Label the numbers</b>Illustrative. A line too high breaks writes; too low breaks the reader who follows many pulled authors.</div>', q=True, red=True), [
 "C: Three ways a fixed number fails. At a million followers, one post is a million inserts, about eight seconds of the whole fleet, past the five-second target by itself. Then an account goes viral: nine thousand followers on Monday, two million on Tuesday, with two hundred posts already pushed. Which tier now, and what about the copies? And a power reader follows five thousand accounts, three hundred of them celebrities: three hundred lists at half a millisecond each is a hundred and fifty milliseconds."])

S(plain(K(2, "the fix"), "Three tiers, from both sides of the arithmetic", table(["Tier", "Followers", "Fan-out", "Why"], [
  ["Push", "under ~10 k", "every follower active in 30 days", "cheap per post; fresh"],
  ["Mid", "~10 k – 100 k", "only followers active in the last day", "cuts the cost by an order of magnitude"],
  ["Pull", "over ~100 k", "none: one write to the recent list", "a post alone would miss the freshness target"]], "bt sm") +
  strip(("fixb", "Mechanism", "Write side: one post's fan-out must finish well inside 5 s on a fair share of the fleet. Read side: the average reader pulls fewer than ~20 authors. Start at 10 k, measure, tune. A config value."), cols="one")), [
 "C: The fix: derive the line from both sides, and use three tiers. Push for authors under about ten thousand followers, to every follower active in thirty days. A mid tier up to about a hundred thousand, pushed only to followers active in the last day, which cuts the cost by an order of magnitude. And pull above that.",
 "C: The write side says one post's fan-out must finish well inside five seconds on a fair share of the fleet. The read side says the average reader should pull fewer than about twenty authors. Start at ten thousand, measure, tune. It is a config value, not a constant."])

S(dia(K(2, "sequence"), "Crossing the line needs no backfill", "seq-tier"), [
 "C: Crossing, as a sequence. A tier job reads follower counts hourly. Up at a hundred thousand, down only below fifty thousand, so an account near the line does not flap. The new star is marked pull. Its new posts become one write each. Yesterday's pushed I-Ds stay in timelines and age out: no backfill, no removal. And readers' merge shows the new posts from the first minute. Crossing down works the same way in reverse."], cls="dia")

S(dia(K(2, "why it works"), "The read merge covers every transition", "ch2-fix",
      extra=strip(("whyb", "Property", "L1 and L2 both hold at the line because it sits where each side's cost is acceptable. The transition needs no backfill because the merge reads the recent list either way."), cols="one")), [
 "C: Why it works, on the baseline. L-one and L-two both hold at the line, because the line was placed where both costs are acceptable. And no transition needs a backfill, because the read path's merge covers the gap: whichever tier an author is in today, their recent posts are reachable."], cls="dia")

qs("Interviewer · the second-level push", "“The power reader: three hundred celebrities on every open.”", [
 "I: The power reader. Three hundred celebrities on every open.", "[pause: 2.0]"])

S(plain(K(2, "the second fix, and the honest limit"), "Treat the tail of readers like the tail of authors", '<div class="cards c2">'
  '<div class="cd grn"><h3>Precompute their merge</h3><p>For readers above ~50 pulled authors, a background job merges their celebrity lists every few minutes into their timeline. Their open is one read again.</p></div>'
  '<div class="cd"><h3>Cap the live merge</h3><p>At read time, merge only the top 50 celebrities by interaction. The rest arrive with the next background merge.</p></div></div>' +
  line("Honest limit: for those readers, celebrity posts may be a few minutes late. Say it.", "r")), [
 "C: The power reader is the tail of readers, and gets the same treatment as the tail of authors. For readers who pull more than about fifty authors, a background job merges their celebrity lists every few minutes into their timeline, so their open is one read again. At read time, the live merge is capped at the top fifty celebrities by interaction.",
 "C: The honest limit: for those readers, a celebrity's post may be a few minutes late. I'd say that to product."])

say_slide("“I set the line from both sides: one post's fan-out must finish inside the freshness target, and the average reader should pull only a handful of authors. That puts it around ten thousand followers, as a config value I'd tune with data. Crossing it needs no backfill because the read merge covers recent posts, and the rare reader who follows hundreds of celebrities gets their merge precomputed.”", [
 "V: If asked, I'd say: I set the line from both sides. One post's fan-out must finish inside the freshness target, and the average reader should pull only a handful of authors. That puts it around ten thousand followers, as a config value I'd tune with data. Crossing it needs no backfill, because the read merge covers recent posts. And the rare reader who follows hundreds of celebrities gets their merge precomputed.", "[pause: 1.0]",
 "N: The pull path now carries correctness weight. Next question: what about posts that must disappear?"])

# ───────── Challenge 3 · delete, block, unfollow ─────────
subchapter("7.3", "Challenge 3: Delete, block, unfollow", ["N: Challenge three. A post is deleted, or an author is blocked, while its I-D sits in millions of timelines: how does it disappear?"])
qs("Interviewer · challenge 3 of 8", "“A user deletes a post, or blocks someone. That post ID is already in millions of timelines. How does it disappear?”", [
 "I: A user deletes a post, or blocks someone. That post I-D is already in millions of timelines. How does it disappear?", "[pause: 2.0]"])

S(dia(K(3, "copies"), "Correctness stored in copies", "ch3-attack", q=True, red=True,
      extra=strip(("case", "Naive answer", "“Fan out a delete to every timeline that has the ID.”"),
                  ("case", "Break", "The timelines: millions of copies, and a delete that races the insert."))), [
 "C: The naive answer: fan out a delete, removing the I-D from every timeline that has it. Look at the timeline cache in red. The I-D was copied millions of times, and the delete has to chase every copy, at the same cost as the post, racing it."], cls="dia")

S(plain(K(3, "the trace"), "The delete loses the race", '<pre class="trace"><span class="t">21:00:00</span>@ana posts to 3 M followers; fan-out starts\n<span class="t">21:00:40</span>she deletes it (wrong photo); a delete fan-out starts\n<span class="t">21:00:41</span>followers whose insert lands after the delete <span class="bad">keep the post</span>\n<span class="t">21:05:00</span>@ben blocks @cal; <span class="bad">500 of @cal\'s posts stay in @ben\'s timeline</span></pre>' +
  '<div class="hedge"><b class="t">Property at risk</b>S1: a viewer must not see deleted or blocked content for longer than 5 s.</div>', q=True, red=True), [
 "C: The trace. Ana posts to three million followers and fan-out starts. Forty seconds later she deletes it, a wrong photo, and a delete fan-out starts behind it. Wherever the insert lands after the delete, the post stays. Separately, Ben blocks Cal, and five hundred of Cal's posts are already in Ben's timeline. Both violate S-one."])

S(dia(K(3, "the fix"), "Correctness on the read path; cleanup is cosmetic", "ch3-fix",
      extra=strip(("fixb", "Mechanism", "Hydrate via the post cache, dropping deleted or hidden posts."),
                  ("whyb", "Property", "S1 is decided at the post's own row, on every page; the bound is seconds."))), [
 "C: The fix. Correctness lives on the read path. The delete writes the post's status once, and an invalidation event drops it from the post cache, the dashed arrow. Every page is hydrated through that cache, and anything deleted or out of audience is dropped. The merge drops authors in my block, mute and unfollow set, which the graph keeps small and cached. A background job removes stale I-Ds from timelines later, and that cleanup is cosmetic."], cls="dia")

S(dia(K(3, "sequence"), "One write, filtered on every page", "seq-delete"), [
 "C: As a sequence. The author deletes: one write, status deleted. The post cache is invalidated. A reader opens the feed: the merge drops authors they block or unfollowed. Hydration misses the cache, finds the row says deleted, and drops it. Later, a cleanup job removes stale I-Ds. The user never depended on it."], cls="dia")

qs("Interviewer · the second-level push", "“The post-cache invalidation event is lost.”", [
 "I: The post-cache invalidation event is lost.", "[pause: 2.0]"])

S(plain(K(3, "the second fix, and the honest limit"), "A lifetime as the backstop, and a short list checked first", '<div class="cards c2">'
  '<div class="cd grn"><h3>A bounded lifetime</h3><p>Post-cache entries live at most 5 minutes. A lost event costs at most one lifetime, not forever.</p></div>'
  '<div class="cd grn"><h3>Recently removed</h3><p>Deletes and audience changes also write a small recently-removed set, checked at hydration for one hour. That keeps the 5 s bound with the event lost.</p></div></div>' +
  line("Honest limit: a post already rendered on a phone stays until the next refresh.", "r")), [
 "C: Two backstops. Post-cache entries have a lifetime of at most five minutes, so a lost event costs one lifetime, not forever. And deletes and audience changes also write a small recently-removed set, which hydration checks for an hour. That keeps the five-second bound even when the event is lost.",
 "C: The honest limit: a post already rendered on someone's phone stays there until they refresh. The next fetch removes it."])

say_slide("“Fanned-out IDs are copies, so I don't trust them. Every page is hydrated from the post itself and filtered by the reader's block and unfollow set, so a delete is one write that takes effect within seconds everywhere. Cleaning the IDs out of timelines is a background job, and it's cosmetic.”", [
 "V: If asked, I'd say: fanned-out I-Ds are copies, so I don't trust them. Every page is hydrated from the post itself and filtered by the reader's block and unfollow set, so a delete is one write that takes effect within seconds everywhere. Cleaning the I-Ds out of timelines is a background job, and it's cosmetic.", "[pause: 1.0]",
 "N: If correctness lives on the read path, the read path must also handle duplicates. Next."])

# ───────── Challenge 4 · twice, or never ─────────
subchapter("7.4", "Challenge 4: Twice, or never", ["N: Challenge four. The interviewer said a duplicate is a bug and a missed close-friend post is worse: where does each come from?"])
qs("Interviewer · challenge 4 of 8", "“You said a duplicate on screen is a bug and a missed close-friend post is worse. Where do each come from in your design?”", [
 "I: You said a duplicate on screen is a bug, and a missed close-friend post is worse. Where does each come from in your design?", "[pause: 2.0]"])

S(dia(K(4, "duplicates and gaps"), "Where twice and never come from", "ch4-attack", q=True, red=True,
      extra=strip(("case", "Naive answer", "“The log delivers exactly once.”"),
                  ("case", "Break", "The insert into the timeline, and the page boundary on the way back to the reader."))), [
 "C: The naive answer: the log delivers exactly once. It doesn't; it delivers at least once. Two places break, in red: the insert into the timeline, on re-delivery, and the page boundary on the way back to the reader."], cls="dia")

S(plain(K(4, "the trace"), "A re-delivered event, and an offset that moves", '<pre class="trace"><span class="t">W3      </span>inserts p9 into 1,000 timelines, <span class="bad">crashes before committing the offset</span>\n<span class="t">W7      </span>re-reads the event: inserts p9 again. In a plain list, <span class="bad">p9 twice</span>\n<span class="t">page 1  </span>reader gets items 0–49 with ?offset=0\n<span class="t">+12     </span>twelve new posts arrive at the top\n<span class="t">page 2  </span>?offset=50 returns old items 38–87: <span class="bad">12 repeated, 12 never shown</span></pre>', q=True, red=True), [
 "C: The trace. Worker three inserts post nine into a thousand timelines and crashes before committing its offset. Worker seven re-reads the event and inserts it again. In a plain list, post nine is there twice. Separately: a reader takes page one with offset zero, twelve new posts arrive at the top, and page two with offset fifty returns items the reader already saw. Twelve repeated, and twelve others never shown."])

S(plain(K(4, "the fix"), "A set keyed by post ID, and a cursor", pseudo(
 'cursor(last) = encode(score[last], last.id)\n\nafter(cursor, ranked):\n    if no cursor: return ranked\n    (s, p) = decode(cursor)\n    # strictly after the last item shown\n    return [i in ranked where (score[i], i.id) < (s, p)]', hl=(1, 7)) +
  strip(("whyb", "Property", "A set keyed by post ID absorbs a re-delivery; gaps are bounded by measured fan-out lag."), cols="one")), [
 "C: The fix is two small things. The timeline is a sorted set keyed by post I-D, so a re-delivered insert changes nothing: at-least-once delivery, with an idempotent effect. And pagination uses a cursor holding the last item's score and I-D. The next page is everything strictly after that pair, whatever arrived at the top. The read merge also de-duplicates across the timeline and the celebrity lists.",
 "C: Duplicates become impossible by data structure. Misses are bounded by fan-out lag, which I measure, and for close ties the pull covers a lagging lane."])

S(dia(K(4, "sequence"), "Re-delivery is a no-op; the next page starts after the last item", "seq-dedupe"), [
 "C: As a sequence. Worker three inserts and crashes. Worker seven inserts the same post again: the set is keyed by post I-D, no change. The reader asks for the next page with a cursor holding score point eight two and post fifty-one, and gets the next fifty strictly after it."], cls="dia")

qs("Interviewer · the second-level push", "“Ranking reorders between page one and page two.”", [
 "I: Ranking reorders things between page one and page two.", "[pause: 2.0]"])

S(plain(K(4, "the second fix, and the honest limit"), "Keep the session's ranked list", '<div class="cards c2">'
  '<div class="cd grn"><h3>A session snapshot</h3><p>The first page\'s ranked candidates (a few hundred IDs) are kept for the session with a short lifetime. Later pages walk that list; they do not re-rank.</p></div>'
  '<div class="cd"><h3>New posts</h3><p>Appear on pull-to-refresh, which starts a new session and a new ranking.</p></div></div>' +
  line("Honest limit: a post that arrives mid-scroll waits for a refresh. That is the expected behaviour, not a bug.", "a")), [
 "C: If ranking reorders between pages, scores in the cursor stop meaning anything. So the first page's ranked candidate list, a few hundred I-Ds, is kept for the session with a short lifetime, and later pages walk that list instead of re-ranking. New posts appear on refresh, which starts a new session. That is the expected behaviour, and I'd say so."])

say_slide("“Fan-out is at-least-once, so inserts are idempotent: the timeline is keyed by post ID. Pagination uses a cursor holding the last item's score and ID, never an offset, and the ranked list for a session is kept so page two doesn't reshuffle page one.”", [
 "V: If asked, I'd say: fan-out is at-least-once, so inserts are idempotent: the timeline is keyed by post I-D. Pagination uses a cursor holding the last item's score and I-D, never an offset. And the ranked list for a session is kept, so page two doesn't reshuffle page one.", "[pause: 1.0]",
 "N: All of this assumes the timeline exists. Next: what if it doesn't?"])
