from dsl import *

# ───────────────────────── 6 · bridge ─────────────────────────
chapter(6, "Bridge", 4, "It works. Where does it break first?", [
 "V: It works. The question now is where it breaks first.", "[pause: 1.0]"])

S(dia("Challenge map", "Eight attack points on the same baseline", "map", chip=chips("each fix creates the next question")), [
 "C: The baseline with eight attack points. The create service: two servers and one code, then codes that can be walked. The cache and the store: one viral key. The edge and the browser: three-oh-one or three-oh-two. Every cache layer: a takedown in five minutes. The click log: counting without slowing the redirect. The store's region: a region lost. And finally: how would we know any of it was broken? I'll take them in an order where each fix creates the next question."], cls="dia")

chapter(7, "Challenges", 5, "Eight ways to break it, and what survives", [
 "C: Eight challenges, each the same way: the question, the naive answer, a case with numbers, where it breaks, the fix, why it works, then the interviewer pushes on the fix itself, and what I'd say in the room."])

K = lambda n, t: f"Challenge {n} of 8 · {t}"

# ───────── Challenge 1 · two servers, one code ─────────
subchapter("7.1", "Challenge 1: Two servers, one code", ["N: Challenge one. Two create servers run at once: how do they never hand out the same code, without asking each other every time?"])
qs("Interviewer · challenge 1 of 8", "“Two create servers run at the same time. How do they never hand out the same code, without asking each other every time?”", [
 "I: Two create servers run at the same time. How do they never hand out the same code, without asking each other every time?", "[pause: 2.0]"])

S(dia(K(1, "two servers, one code"), "Who decides that a code is free?", "ch1-attack", q=True, red=True,
      extra=strip(("case", "Naive answer", "“Generate a random code, check whether it exists, and insert it if it doesn't.”"),
                  ("case", "Break", "Check-then-insert in the create service: the check is stale the moment it returns."))), [
 "C: The naive answer: generate a random code, check whether it exists, insert it if not. Look at the red create service. The check is stale the moment it returns. Between the select and the insert, another server can do exactly the same thing."], cls="dia")

S(plain(K(1, "the trace"), "Two customers, one alias, three milliseconds apart", '<pre class="trace"><span class="t">10:00:00.001</span>server A: SELECT code = \'sale\' → none\n<span class="t">10:00:00.002</span>server B: SELECT code = \'sale\' → none\n<span class="t">10:00:00.004</span>server A: INSERT sale → shop-a.example\n<span class="t">10:00:00.006</span>server B: INSERT sale → shop-b.example: <span class="bad">overwrites A\'s row</span>\n<span class="t">next day</span><span class="bad">A\'s printed flyers open B\'s page</span></pre>' +
  '<div class="hedge"><b class="t">Same race, random codes</b>Two servers draw aZ3kQ9x. Rare at 0.34 %, but at 400 creates a second, rare happens every day.</div>', q=True, red=True), [
 "C: The trace. Two customers ask for the alias sale, three milliseconds apart. Server A selects: none. Server B selects: none. A inserts. B inserts, and without a constraint it overwrites. The next day, A's printed flyers open B's page.",
 "C: Random codes have the same race. A third of a percent sounds rare, but at four hundred creates a second, rare happens every day."])

S(dia(K(1, "the fix"), "Disjoint ranges for generated codes; the constraint for the rest", "ch1-fix",
      extra=strip(("fixb", "Mechanism", "Each server leases 1,000 IDs in one conditional write and hands them out locally. Every insert carries UNIQUE(code): one alias race ends in one 201 and one 409."),
                  ("whyb", "Property", "S1 is decided by the one place that sees every write for a code: its shard. L1: a create waits only on its own insert."))), [
 "C: The fix has two parts, outlined green. Generated codes come from disjoint ranges: each server leases a thousand I-Ds from the allocator in one conditional write and hands them out from memory. Two servers can never draw the same I-D, so generated codes never even reach the constraint as a conflict.",
 "C: And every insert carries a unique constraint on the code. For a custom alias, the one shard that owns sale accepts one insert and rejects the other: one two-oh-one, one four-oh-nine. The store is the authority, not my application. One more rule: aliases are eight characters or longer, so an alias can never take a code the counter will produce later."], cls="dia")

S(dia(K(1, "how ranges work"), "Coordination once per thousand links", "ranges"), [
 "C: The ranges. The allocator says next is forty-one thousand. Server A holds forty thousand to forty thousand nine hundred ninety-nine and is on forty thousand and seventeen. B and C hold their own blocks. Each next I-D goes through the permutation and base sixty-two.",
 "C: A server that crashes wastes the rest of its block. That is a gap, never a collision, and with two hundred and ninety times more codes than links, gaps cost nothing."], cls="dia")

S(dia(K(1, "sequence"), "A lease, then an alias conflict", "seq-ch1-lease"), [
 "C: As a sequence. Server A leases with a compare-and-set: next goes from forty thousand to forty-one thousand only if it is still forty thousand. Okay, A owns that block. It hands out I-Ds locally and leases the next block early, at half-used. Then a customer asks for sale: the insert conflicts, and the second customer gets four-oh-nine while the first keeps it."], cls="dia")

S(plain(K(1, "the lease, as code"), "One conditional write per thousand links",
  '<pre class="code" data-lang="python"><span class="kw">def</span> lease(store, size=1000):\n    <span class="kw">while</span> True:\n        cur = store.get(<span class="st">"next_id"</span>)\n        <span class="kw">if</span> store.compare_and_set(<span class="st">"next_id"</span>, cur, cur + size):\n            <span class="kw">return</span> range(cur, cur + size)   <span class="cm"># ours alone</span>\n        <span class="cm"># lost the race to another server: read again</span></pre>' +
  strip(("whyb", "Why it works", "Compare-and-set makes leases disjoint. Inside a lease no coordination is needed; across leases none is possible to get wrong."), cols="one")), [
 "C: The lease in code. Read next, then compare-and-set it to next plus a thousand. If another server won the race, read again. When it succeeds, the range is ours alone. Inside a lease, no coordination is needed. Across leases, the compare-and-set makes overlap impossible."])

qs("Interviewer · the second-level push", "“The allocator is down. Or a server crashes holding half a range.”", [
 "I: The allocator is down. Or a server crashes holding half a range.", "[pause: 2.0]"])

S(plain(K(1, "the second fix, and the honest limit"), "Runway, a replicated allocator, and the right failure", '<div class="cards c3">'
  '<div class="cd grn"><h3>Runway</h3><p>Lease the next block at half-used: 500 to 1,500 IDs in hand. At the 400/s peak over ten servers that is 12–37 s; at the 40/s average, two to six minutes.</p></div>'
  '<div class="cd"><h3>A replicated allocator</h3><p>A small consensus-backed store: losing one node is not an outage. 0.4 leases a second is no load.</p></div>'
  '<div class="cd amb"><h3>A crashed server</h3><p>Its unused IDs are skipped: a gap, not a collision.</p></div></div>' +
  line("If the allocator is down for minutes, creates stop. Redirects never depended on it. That is the right way round.", "r")), [
 "C: Three answers. Runway: each server leases its next block at half-used, so it holds five hundred to fifteen hundred I-Ds. At the four-hundred-a-second peak across ten servers, that's twelve to thirty-seven seconds; at the average, two to six minutes. The allocator is a small replicated store with a consensus protocol, so one node lost is not an outage. A crashed server's unused I-Ds are simply skipped.",
 "C: The honest limit. If the allocator is down for minutes, creates stop. Redirects never depended on it. That is the right way round: the product keeps working."])

say_slide("“Each create server leases a block of a thousand IDs, so coordination happens once per thousand links, not once per link. The unique constraint on the code is the final authority, so an alias race ends in one success and one conflict. If the allocator goes down, servers have their leased runway, and redirects never depended on it.”", [
 "V: If asked, I'd say: each create server leases a block of a thousand I-Ds, so coordination happens once per thousand links, not once per link. The unique constraint on the code is the final authority, so an alias race ends in one success and one conflict. If the allocator goes down, servers have their leased runway, and redirects never depended on it.", "[pause: 1.0]",
 "N: That fix creates the next question: codes from a counter are in order."])

# ───────── Challenge 2 · codes in order ─────────
subchapter("7.2", "Challenge 2: Codes in order", ["N: Challenge two. The codes come from a counter: what can a stranger learn from that, and how do we stop it without losing uniqueness?"])
qs("Interviewer · challenge 2 of 8", "“Your codes come from a counter. What can someone learn from that?”", [
 "I: Your codes come from a counter. What can someone learn from that?", "[pause: 2.0]"])

S(dia(K(2, "codes in order"), "Base-62 of a counter is a counter", "ch2-attack", q=True, red=True,
      extra=strip(("case", "Naive answer", "“Base-62 makes them look random.”"),
                  ("case", "Break", "The encoder after the range: neighbouring IDs give neighbouring codes."))), [
 "C: The naive answer: base sixty-two makes them look random. It doesn't. Base sixty-two of a counter is still a counter, in a different alphabet. Neighbouring I-Ds give neighbouring codes, and the red box is the encoder that does it."], cls="dia")

S(plain(K(2, "the trace"), "Our volume, and someone's private document, for free", '<pre class="trace"><span class="t">Mon 09:00</span>a user creates a link: 0000g8Q\n<span class="t">Mon 09:10</span>the same user: 0000gBA → <span class="bad">2,000 links in 10 minutes: our creation rate</span>\n<span class="t">Mon 09:11</span>a scraper requests 0000g8R, 0000g8S, 0000g8T …\n<span class="t">Mon 09:12</span><span class="bad">reads every link created that morning</span>, including an unlisted document share</pre>' +
  '<div class="hedge"><b class="t">What leaks</b>Business volume to a competitor, and links their owners believed nobody would find.</div>', q=True, red=True), [
 "C: The trace. At nine a user gets zero-zero-zero-zero-g-eight-Q. At ten past, another: zero-zero-zero-zero-g-B-A. Subtract: two thousand links in ten minutes. That's our creation rate, for free.",
 "C: Then a scraper asks for the next code, and the next, and reads every link created that morning, including someone's unlisted document share. Volume leaks to a competitor, and links leak that their owners thought nobody would find."])

S(dia(K(2, "the fix"), "A keyed permutation between the counter and the code", "ch2-fix",
      extra=strip(("fixb", "Mechanism", "ID → a four-round Feistel network over 42 bits with a secret key, cycle-walked below 62⁷ → base-62. Plus a rate limit on 404s per client."),
                  ("whyb", "Property", "Uniqueness comes from the counter, unpredictability from the key. The two are separated, so neither weakens the other."))), [
 "C: The fix lives in the same create box. Between the counter and the encoder, a keyed permutation: a four-round Feistel network over forty-two bits with a secret key, cycle-walked to stay below sixty-two to the seventh. Then base sixty-two. And a rate limit on four-oh-fours per client, so random guessing is slow."], cls="dia")

S(dia(K(2, "what the permutation does"), "Unique in, unique out, neighbours unrelated", "feistel"), [
 "C: Three neighbouring I-Ds: forty thousand and seventeen, eighteen, nineteen. Out come a-Z-three-k-Q-nine-x, P-q-zero-seven-m-W-d, and three-f-L-x-nine-T-b. Unrelated. And because a Feistel network is a bijection, two different I-Ds can never give the same code. Uniqueness is untouched."], cls="dia")

S(plain(K(2, "the permutation, as code"), "Four rounds, then walk back into range",
  '<pre class="code" data-lang="python">N = 62 ** 7                       <span class="cm"># 3.5 × 10¹² codes</span>\n<span class="kw">def</span> permute(i, key):\n    <span class="kw">while</span> True:\n        l, r = i &gt;&gt; 21, i &amp; (2**21 - 1)  <span class="cm"># 42 bits, two halves</span>\n        <span class="kw">for</span> k <span class="kw">in</span> range(4):\n            l, r = r, l ^ (prf(key, k, r) &amp; (2**21 - 1))\n        i = (l &lt;&lt; 21) | r\n        <span class="kw">if</span> i &lt; N: <span class="kw">return</span> base62(i, width=7)  <span class="cm"># cycle walk</span></pre>' +
  strip(("whyb", "Why it works", "Each round is invertible, so the whole is a bijection on 42 bits. Walking until the value falls below 62⁷ keeps it a bijection on the code space."), cols="one")), [
 "C: In code. Split forty-two bits into two halves. Four rounds: swap the halves and mix one with a keyed pseudo-random function of the other. Each round is invertible, so the whole thing is a bijection. If the result lands above sixty-two to the seventh, run it again: that's cycle walking, and it keeps the bijection on exactly the code space."])

qs("Interviewer · the second-level push", "“The key leaks. Or a customer says short links to private files must not be guessable at all.”", [
 "I: The key leaks. Or a customer says short links to private files must not be guessable at all.", "[pause: 2.0]"])

S(plain(K(2, "the second fix, and the honest limit"), "Rotate the key; and a short code is not a secret", '<div class="cards c2">'
  '<div class="cd grn"><h3>A leaked key</h3><p>New codes use a new key with a version marker, or a fresh slice of the ID space. Old codes stay valid: they are stored, never recomputed.</p></div>'
  '<div class="cd red"><h3>Private content</h3><p>42 bits can be sampled by an attacker with many addresses. Private files need authentication, or a long random token, not a short link. Say so to product.</p></div></div>'), [
 "C: A leaked key: new codes use a new key, with a version marker or a fresh slice of the I-D space. Old codes stay valid, because codes are stored, never recomputed. Nothing breaks.",
 "C: Private content is the honest limit. Forty-two bits can be sampled by an attacker with enough addresses. Links to private files need authentication or a long random token, not a short link. That's a conversation with product, not a cleverer encoder."])

say_slide("“A counter gives uniqueness, but base-62 of a counter is still a counter: it leaks our volume and lets anyone walk the links. I pass the ID through a keyed permutation, which keeps it unique and makes neighbours unrelated. And I'm clear that a short code is not a secret: private links need authentication.”", [
 "V: If asked, I'd say: a counter gives uniqueness, but base sixty-two of a counter is still a counter. It leaks our volume and lets anyone walk the links. I pass the I-D through a keyed permutation, which keeps it unique and makes neighbours unrelated. And I'm clear that a short code is not a secret: private links need authentication.", "[pause: 1.0]",
 "N: Codes are settled. The next question is the read side: one code, forty thousand times a second."])

# ───────── Challenge 3 · one viral link ─────────
subchapter("7.3", "Challenge 3: One link at 40,000 clicks a second", ["N: Challenge three. One link goes viral: what happens to the one cache shard that holds it, and to the store when that shard restarts?"])
qs("Interviewer · challenge 3 of 8", "“A link goes viral: forty thousand clicks a second, all on one code. What happens?”", [
 "I: A link goes viral. Forty thousand clicks a second, all on one code. What happens?", "[pause: 2.0]"])

S(dia(K(3, "one viral link"), "One key, one shard, one row", "ch3-attack", q=True, red=True,
      extra=strip(("case", "Naive answer", "“It's cached, so it's fine.”"),
                  ("case", "Break", "The shared-cache shard that owns the key, then the store when that shard restarts."))), [
 "C: The naive answer: it's cached, so it's fine. Look at the red boxes. A cache is sharded by key, so all forty thousand requests land on one shard. And if that shard restarts, they all land on one row of the store."], cls="dia")

S(plain(K(3, "the trace"), "A hot key, then a cold one", '<pre class="trace"><span class="t">14:02</span>code k7Pq2mZ goes from 3 clicks/s to <span class="bad">40,000/s</span>\n<span class="t">14:02</span>its cache shard: p99 0.8 ms → <span class="bad">9 ms</span>; every other code on that shard slows too\n<span class="t">14:05</span>a deploy restarts the shard: 200 ms of misses\n<span class="t">14:05</span><span class="bad">8,000 identical SELECTs on one row</span> in those 200 ms</pre>' +
  '<div class="hedge"><b class="t">Label the numbers</b>Illustrative. The shape is the point: one key concentrates load that a fleet would spread.</div>', q=True, red=True), [
 "C: The trace. At two minutes past two, code k-seven-P-q-two-m-Z goes from three clicks a second to forty thousand. Its cache shard's p ninety-nine goes from under a millisecond to nine, and every other code on that shard slows with it. At five past, a deploy restarts the shard. Two hundred milliseconds of misses: eight thousand identical selects on one row.",
 "C: Illustrative numbers. The shape is the point: one key concentrates load that a fleet would otherwise spread."])

S(dia(K(3, "the fix"), "Answer from memory on every server; one miss per server", "ch3-fix",
      extra=strip(("fixb", "Mechanism", "An in-process cache on every redirect server (a few hundred thousand entries, 30–60 s). Single flight: concurrent misses for one code wait on one lookup. Negative caching for unknown codes."),
                  ("whyb", "Property", "L2: the hot key's load is spread across all servers' memory. The store sees at most one query per server per code, not one per click."))), [
 "C: The fix is in the redirect service, outlined green. An in-process cache on every redirect server: a few hundred thousand entries, thirty to sixty seconds. With forty servers, the viral code is a thousand requests a second from each one's own memory. Trivial.",
 "C: And single flight: when many requests miss the same code at once, the first one looks it up and the others wait on its answer. Plus negative caching for unknown codes, so a scanner's four-oh-fours don't reach the store. The store now sees at most one query per server per code."], cls="dia")

S(dia(K(3, "sequence"), "A thousand requests, one lookup", "seq-ch3-flight"), [
 "C: As a sequence. A thousand requests for the same code arrive in twenty milliseconds. In-process miss: the first leads, nine hundred ninety-nine wait. One get on the shared cache: miss, it's restarting. One select on the store. One answer, a thousand three-oh-twos, and the code stays in process memory for thirty seconds."], cls="dia")

S(plain(K(3, "single flight, as code"), "The first caller looks up; the rest wait",
  '<pre class="code" data-lang="python">inflight = {}                       <span class="cm"># code → future</span>\n<span class="kw">def</span> resolve(code):\n    hit = local.get(code)\n    <span class="kw">if</span> hit: <span class="kw">return</span> hit\n    leader = code <span class="kw">not in</span> inflight\n    fut = inflight.setdefault(code, Future())\n    <span class="kw">if</span> leader:\n        fut.set(shared_cache.get(code) <span class="kw">or</span> store.get(code))\n        local.put(code, fut.value, ttl=30); inflight.pop(code)\n    <span class="kw">return</span> fut.wait()</pre>' +
  strip(("whyb", "Why it works", "However many clicks arrive, each server sends at most one lookup per code per lifetime: load on the store is servers × hot codes, not clicks."), cols="one")), [
 "C: Single flight in code. Check local memory. On a miss, register a future for the code. If you're the first, you do the lookup, shared cache then store, fill local memory for thirty seconds, and release the waiters. Everyone else just waits on the future. The load on the store is servers times hot codes, however many clicks arrive."])

qs("Interviewer · the second-level push", "“Now the in-process lifetime means a takedown takes up to a minute longer. And a whole region's servers restart together.”", [
 "I: Now the in-process lifetime means a takedown takes up to a minute longer. And a whole region's servers restart together.", "[pause: 2.0]"])

S(plain(K(3, "the second fix, and the honest limit"), "Budget the lifetime; warm before serving", '<div class="cards c3">'
  '<div class="cd amb"><h3>Takedown</h3><p>The 60 s lifetime is a line in the takedown budget, and the invalidation channel drops entries early. Challenge five.</p></div>'
  '<div class="cd grn"><h3>Restarts</h3><p>Roll them. A starting server warms its cache from the last hour\'s top codes before it takes traffic.</p></div>'
  '<div class="cd"><h3>The real answer for a global viral link</h3><p>The edge, a minute from every user. Challenge four.</p></div></div>'), [
 "C: The lifetime is a line in the takedown budget, and the invalidation channel drops entries early anyway. That's challenge five. Restarts roll, never a whole region at once, and a starting server warms its cache from the last hour's top codes before it takes traffic.",
 "C: The honest limit: for a link that is viral across the world, the real answer is the edge, close to every user. Which raises the next question."])

say_slide("“A viral link is a hot key, not a load problem. I answer it from memory on every redirect server and coalesce misses, so each server sends one query, whatever the click rate. The cost is a short staleness window, which I count in the takedown budget.”", [
 "V: If asked, I'd say: a viral link is a hot key, not a load problem. I answer it from memory on every redirect server and coalesce misses, so each server sends one query, whatever the click rate. The cost is a short staleness window, which I count in the takedown budget.", "[pause: 1.0]",
 "N: That fix creates the next question: should the answer live even closer to the user?"])

# ───────── Challenge 4 · 301 or 302 ─────────
subchapter("7.4", "Challenge 4: 301 or 302?", ["N: Challenge four. Permanent or temporary redirect: what does each one cost the product, not just the servers?"])
qs("Interviewer · challenge 4 of 8", "“Should the redirect be a 301 or a 302?”", [
 "I: Should the redirect be a three-oh-one or a three-oh-two?", "[pause: 2.0]"])

S(dia(K(4, "301 or 302"), "An answer we cannot see, and cannot take back", "ch4-attack", q=True, red=True,
      extra=strip(("case", "Naive answer", "“301. It's permanent, and it saves servers.”"),
                  ("case", "Break", "The browser: with a 301 it answers by itself, forever, and never asks us again."))), [
 "C: The naive answer: three-oh-one, it's permanent and it saves servers. It does save servers. Look at the red browser. A three-oh-one tells it to remember the answer, and it does, indefinitely. It never asks us again."], cls="dia")

S(plain(K(4, "the trace"), "Yesterday's click was the last one we saw", '<pre class="trace"><span class="t">Mon 10:00</span>a user clicks k7Pq2mZ; we answer <b>301</b>; the browser caches it\n<span class="t">Tue 09:00</span>the same user clicks again: <span class="bad">answered by the browser; not counted</span>\n<span class="t">Tue 15:00</span>trust and safety blocks k7Pq2mZ: it now leads to a phishing page\n<span class="t">Tue 15:20</span><span class="bad">that user\'s browser still goes straight to the phishing page</span></pre>' +
  '<div class="hedge"><b class="t">Two losses</b>The owner loses the count. We lose the ability to protect the user.</div>', q=True, red=True), [
 "C: The trace. Monday a user clicks; we answer three-oh-one; the browser caches it. Tuesday the same user clicks again: the browser answers, we never see it, it's not counted. At three, the link is blocked for phishing. At three-twenty, that user's browser still goes straight to the phishing page.",
 "C: Two losses: the owner loses the count, and we lose the ability to protect the user."])

S(dia(K(4, "the fix"), "302 by default; a short, purgeable edge cache", "ch4-fix",
      extra=strip(("fixb", "Mechanism", "302 with browser caching off; the edge may keep it 60 s and can be purged. 301 only as an owner's opt-in for permanent, uncounted links."),
                  ("whyb", "Property", "Control (counting, and S2) stays at layers we can reach. The edge gives most of 301's saving at a bounded cost in freshness."))), [
 "C: The fix: three-oh-two by default, with browser caching off, and the edge allowed to keep it for sixty seconds, purgeable. Three-oh-one only as an owner's opt-in, for links that are permanent and that they accept will not be counted.",
 "C: The property: counting and takedowns stay at layers we can reach. And the edge gives us most of the saving a three-oh-one would, at a bounded cost in freshness."], cls="dia")

S(plain(K(4, "the layers"), "Where a redirect is answered, and what each layer costs", table(["Layer", "Answers in", "Sees the click?", "Can we take it back?"], [
  ["Browser, 301", "0 ms", "never again", "<b>no</b>"],
  ["Edge, 302 cached 60 s", "~5 ms near the user", "from edge logs, minutes late", "yes: purge, or 60 s"],
  ["Redirect service + caches", "~1 ms at the server", "every click, exact", "yes: invalidation, or 60 s"],
  ["Link store", "~5 ms, misses only", "—", "it is the truth"]], "bt sm")), [
 "C: The layers. The browser with a three-oh-one: zero milliseconds, never sees the click again, cannot be taken back. The edge with a three-oh-two cached for sixty seconds: a few milliseconds near the user, clicks from edge logs, minutes late, purgeable. Our servers and caches: a millisecond, every click, recallable. The store: the truth, for misses only."])

qs("Interviewer · the second-level push", "“Finance says the edge bill for ten billion requests is too high. Or edge-log counts arrive twenty minutes late.”", [
 "I: Finance says the edge bill for ten billion requests is too high. Or the counts from edge logs arrive twenty minutes late.", "[pause: 2.0]"])

S(plain(K(4, "the second fix, and the honest limit"), "Price both sides; say where exact counts come from", '<div class="cards c2">'
  '<div class="cd amb"><h3>The edge bill</h3><p>Compare the per-request edge cost with the servers and cross-region traffic it saves. Turn edge caching on per link, by click rate: only hot links need it.</p></div>'
  '<div class="cd"><h3>Late counts</h3><p>Edge-log counts carry their lag, shown as <code>asOf</code>. When clicks are billed, the count comes from our servers or a signed edge function, not from logs.</p></div></div>'), [
 "C: The edge bill: compare the per-request cost with the servers and cross-region traffic it saves, and turn edge caching on per link, by click rate. Only hot links need it, and they are two percent of links.",
 "C: Late counts are the stated lag, shown as as-of. When clicks are billed, the count must come from our servers, or a signed function running at the edge, not from logs. That is challenge six."])

say_slide("“301 against 302 is a product decision, not an optimisation. A 301 is answered by the browser forever, so we lose the click and the ability to take a link down. I default to 302, let the edge cache it for a minute, and offer 301 only to owners who want a permanent, uncounted link.”", [
 "V: If asked, I'd say: three-oh-one against three-oh-two is a product decision, not an optimisation. A three-oh-one is answered by the browser forever, so we lose the click and the ability to take a link down. I default to three-oh-two, let the edge cache it for a minute, and offer three-oh-one only to owners who want a permanent, uncounted link.", "[pause: 1.0]",
 "N: That fix creates the next question: we now hold copies at four layers. Can we withdraw all of them in five minutes?"])
