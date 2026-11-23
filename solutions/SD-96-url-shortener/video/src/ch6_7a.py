from dsl import *
from stack import REJ
P = "[+]"
B = lambda x: f'<span class="bad">{x}</span>'

# ───────────────────────── 6 · bridge ─────────────────────────
chapter(6, "Bridge", 4, "It works. Where does it break first?", [
 "V: It works. The question now is where it breaks first.", "[pause: 1.0]"])

S(dia("Challenge map", "Eight attack points on the same baseline", "map", chip=chips("each fix creates the next question")), [
 P, "C: The baseline with eight attack points, marked one at a time.", P,
 "C: The create service: two servers and one code, then codes that can be walked. Challenges one and two.", P,
 "C: The shared cache: one viral key. Challenge three.", P,
 "C: The edge and the browser: three-oh-one or three-oh-two. Challenge four. And every cache layer together: a takedown in five minutes, challenge five.", P,
 "C: The redirect service: counting without slowing it. Challenge six.", P,
 "C: The click log carries that fix.", P,
 "C: And the link store's region: a region lost, challenge seven. Then finally: how would we know any of it was broken? I'll take them in an order where each fix creates the next question."], cls="dia")

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
 P, "C: The create path, on the baseline.", "[+3]",
 "C: The naive answer: generate a random code, check whether it exists, insert it if not. Look at the red create service. The check is stale the moment it returns.", P,
 "C: Between the select and the insert, another server can do exactly the same thing."], cls="dia")

S(trace(K(1, "the trace"), "Two customers, one alias, three milliseconds apart", [
  ("10:00:00.001", "server A: <code>SELECT code = 'sale'</code> → none"),
  ("10:00:00.002", "server B: <code>SELECT code = 'sale'</code> → none"),
  ("10:00:00.004", "server A: <code>INSERT sale</code> → shop-a.example"),
  ("10:00:00.006", "server B: <code>INSERT sale</code> → shop-b.example: " + B("overwrites A's row")),
  ("next day", B("A's printed flyers open B's page"))],
  hedge=("Same race, random codes", "Two servers draw aZ3kQ9x. Rare at 0.34 %, but at 400 creates a second, rare happens every day.")), [
 "C: The trace. Two customers ask for the alias sale, three milliseconds apart.", P, "C: Server A selects: none.", P, "C: Server B selects: none.", P,
 "C: A inserts.", P, "C: B inserts, and without a constraint it overwrites.", P, "C: The next day, A's printed flyers open B's page.", P,
 "C: Random codes have the same race. A third of a percent sounds rare, but at four hundred creates a second, rare happens every day."])

S(dia(K(1, "the fix"), "Disjoint ranges for generated codes; the constraint for the rest", "ch1-fix",
      extra=strip(("fixb", "Mechanism", "Each server leases 1,000 IDs in one etcd transaction and hands them out locally. Every insert carries PRIMARY KEY(code): one alias race ends in one 201 and one 409."),
                  ("whyb", "Property", "S1 is decided by the one place that sees every write for a code: its shard. L1: a create waits only on its own insert.")) + rejl(*REJ(1))), [
 P, "C: The fix has two parts.", P,
 "C: Outlined green: generated codes come from disjoint ranges. Each server leases a thousand I-Ds from the allocator in one etcd transaction and hands them out from memory. Two servers can never draw the same I-D, so generated codes never even reach the constraint as a conflict.", P,
 "C: And every insert carries the primary key on the code. For a custom alias, the one shard that owns sale accepts one insert and rejects the other: one two-oh-one, one four-oh-nine.", P,
 "C: The mechanism: the store is the authority, not my application. And aliases are eight characters or longer, so an alias can never take a code the counter will produce later.", P,
 "C: The property: S-one is decided by the one place that sees every write for a code, its shard. And L-one: a create waits only on its own insert.", P,
 "C: What I rejected: Redis increment-by as the counter. After a fail-over, the new primary can hand out a range it already gave away."], cls="dia")

S(dia(K(1, "how ranges work"), "Coordination once per thousand links", "ranges"), [
 "C: The ranges. The allocator says next is forty-one thousand. Server A holds forty thousand to forty thousand nine hundred ninety-nine and is on forty thousand and seventeen. B and C hold their own blocks. Each next I-D goes through the permutation and base sixty-two.",
 "C: A server that crashes wastes the rest of its block. That is a gap, never a collision, and with two hundred and ninety times more codes than links, gaps cost nothing."], cls="dia")

S(dia(K(1, "sequence"), "A lease, then an alias conflict", "seq-ch1-lease"), [
 "C: As a sequence.", P, "C: Server A leases with a compare-and-set: next goes from forty thousand to forty-one thousand only if it is still forty thousand.", P,
 "C: Okay, A owns that block.", P, "C: It hands out I-Ds locally and leases the next block early, at half-used.", P,
 "C: Then a customer asks for sale.", P, "C: The insert conflicts.", P, "C: And the second customer gets four-oh-nine while the first keeps it."], cls="dia")

S(plain(K(1, "the lease, as code"), "One conditional write per thousand links",
  '<pre class="code" data-lang="go">resp, err := cli.Txn(ctx).\n    If(clientv3.Compare(clientv3.ModRevision(key), <span class="st">"="</span>, rev)).\n    Then(clientv3.OpPut(key, itoa(next + 1000))).\n    Else(clientv3.OpGet(key)).Commit()\n<span class="kw">if</span> resp.Succeeded { <span class="kw">return</span> Range{next, next + 1000} }  <span class="cm">// ours alone</span>\n<span class="cm">// lost the race: Else returned the new value and revision; try again</span></pre>' +
  strip(("whyb", "Why it works", "The compare on the revision makes leases disjoint. Inside a lease no coordination is needed; across leases none is possible to get wrong."), cols="one")), [
 "C: The lease in code, against etcd's Go client. One transaction: if the key's modification revision is still the one I read, put next plus a thousand; else, give me the current value. If it succeeded, the range is ours alone. If not, the else branch already returned the new value and revision, so I try again.", P,
 "C: Inside a lease, no coordination is needed. Across leases, the compare on the revision makes overlap impossible."])

qs("Interviewer · the second-level push", "“The allocator is down. Or a server crashes holding half a range.”", [
 "I: The allocator is down. Or a server crashes holding half a range.", "[pause: 2.0]"])

S(plain(K(1, "the second fix, and the honest limit"), "Runway, a replicated allocator, and the right failure", cards(
  ("grn", "Runway", "Lease the next block at half-used: 500 to 1,500 IDs in hand. At the 400/s peak over ten servers that is 12–37 s; at the 40/s average, two to six minutes."),
  ("", "A replicated allocator", "Three etcd nodes across zones: losing one node is not an outage. 0.4 leases a second is no load."),
  ("amb", "A crashed server", "Its unused IDs are skipped: a gap, not a collision."), cols=3) +
  line("If the allocator is down for minutes, creates stop. Redirects never depended on it. That is the right way round.", "r")), [
 "C: Three answers.", P,
 "C: Runway: each server leases its next block at half-used, so it holds five hundred to fifteen hundred I-Ds. At the four-hundred-a-second peak across ten servers, that's twelve to thirty-seven seconds; at the average, two to six minutes.", P,
 "C: The allocator is three etcd nodes across zones, so one node lost is not an outage.", P,
 "C: A crashed server's unused I-Ds are simply skipped.", P,
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
 P, "C: The create path again.", "[+3]",
 "C: The naive answer: base sixty-two makes them look random. It doesn't. Base sixty-two of a counter is still a counter, in a different alphabet.", P,
 "C: Neighbouring I-Ds give neighbouring codes, and the red box is the encoder that does it."], cls="dia")

S(trace(K(2, "the trace"), "Our volume, and someone's private document, for free", [
  ("Mon 09:00", "a user creates a link: <code>0000g8Q</code>"),
  ("Mon 09:10", "the same user: <code>0000gBA</code> → " + B("2,000 links in 10 minutes: our creation rate")),
  ("Mon 09:11", "a scraper requests <code>0000g8R</code>, <code>0000g8S</code>, <code>0000g8T</code> …"),
  ("Mon 09:12", B("reads every link created that morning") + ", including an unlisted document share")],
  hedge=("What leaks", "Business volume to a competitor, and links their owners believed nobody would find.")), [
 "C: The trace.", P, "C: At nine a user gets zero-zero-zero-zero-g-eight-Q.", P,
 "C: At ten past, another: zero-zero-zero-zero-g-B-A. Subtract: two thousand links in ten minutes. That's our creation rate, for free.", P,
 "C: Then a scraper asks for the next code, and the next.", P,
 "C: And reads every link created that morning, including someone's unlisted document share.", P,
 "C: Volume leaks to a competitor, and links leak that their owners thought nobody would find."])

S(dia(K(2, "the fix"), "A keyed permutation between the counter and the code", "ch2-fix",
      extra=strip(("fixb", "Mechanism", "ID → a four-round Feistel network over 42 bits with a secret key, cycle-walked below 62⁷ → base-62. Plus a rate limit on 404s per client."),
                  ("whyb", "Property", "Uniqueness comes from the counter, unpredictability from the key. The two are separated, so neither weakens the other.")) + rejl(*REJ(2))), [
 P, "C: The fix lives in the same create box.", "[+2]",
 "C: Between the counter and the encoder, a keyed permutation.", P,
 "C: A four-round Feistel network over forty-two bits with a secret key, cycle-walked to stay below sixty-two to the seventh. Then base sixty-two. And a rate limit on four-oh-fours per client, so random guessing is slow.", P,
 "C: Uniqueness comes from the counter, unpredictability from the key. They are separate, so neither weakens the other.", P,
 "C: Rejected: a hash of the long U-R-L. Cut to seven characters it collides, and one U-R-L would get the same code for every owner."], cls="dia")

S(dia(K(2, "what the permutation does"), "Unique in, unique out, neighbours unrelated", "feistel"), [
 "C: Three neighbouring I-Ds: forty thousand and seventeen, eighteen, nineteen. Out come a-Z-three-k-Q-nine-x, P-q-zero-seven-m-W-d, and three-f-L-x-nine-T-b. Unrelated. And because a Feistel network is a bijection, two different I-Ds can never give the same code. Uniqueness is untouched.",
 "C: One more property I'll use in challenge seven: the permutation is invertible. A server holding the key can turn a code back into its I-D, and so into the region that created it."], cls="dia")

S(plain(K(2, "the permutation, as code"), "Four rounds, then walk back into range",
  '<pre class="code" data-lang="python">N = 62 ** 7                       <span class="cm"># 3.5 × 10¹² codes</span>\n<span class="kw">def</span> permute(i, key):\n    <span class="kw">while</span> True:\n        l, r = i &gt;&gt; 21, i &amp; (2**21 - 1)  <span class="cm"># 42 bits, two halves</span>\n        <span class="kw">for</span> k <span class="kw">in</span> range(4):\n            l, r = r, l ^ (prf(key, k, r) &amp; (2**21 - 1))\n        i = (l &lt;&lt; 21) | r\n        <span class="kw">if</span> i &lt; N: <span class="kw">return</span> base62(i, width=7)  <span class="cm"># cycle walk</span></pre>' +
  strip(("whyb", "Why it works", "Each round is invertible, so the whole is a bijection on 42 bits. Walking until the value falls below 62⁷ keeps it a bijection on the code space."), cols="one")), [
 "C: In code. Split forty-two bits into two halves. Four rounds: swap the halves and mix one with a keyed pseudo-random function of the other. The function is a keyed hash, H-MAC with SHA-two-fifty-six truncated, keyed from the key-management service.", P,
 "C: Each round is invertible, so the whole thing is a bijection. If the result lands above sixty-two to the seventh, run it again: that's cycle walking, and it keeps the bijection on exactly the code space."])

qs("Interviewer · the second-level push", "“The key leaks. Or a customer says short links to private files must not be guessable at all.”", [
 "I: The key leaks. Or a customer says short links to private files must not be guessable at all.", "[pause: 2.0]"])

S(plain(K(2, "the second fix, and the honest limit"), "Rotate the key; and a short code is not a secret", cards(
  ("grn", "A leaked key", "New codes use a new key with a version marker, or a fresh slice of the ID space. Old codes stay valid: they are stored, never recomputed."),
  ("red", "Private content", "42 bits can be sampled by an attacker with many addresses. Private files need authentication, or a long random token, not a short link. Say so to product."))), [
 P, "C: A leaked key: new codes use a new key, with a version marker or a fresh slice of the I-D space. Old codes stay valid, because codes are stored, never recomputed. Nothing breaks.", P,
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
                  ("case", "Break", "The Redis shard that owns the key, then the store when that shard restarts."))), [
 P, "C: The redirect path.", "[+3]",
 "C: The naive answer: it's cached, so it's fine. Look at the red boxes. Redis Cluster puts a key in one hash slot, on one shard, so all forty thousand requests land on one shard.", P,
 "C: And if that shard restarts without a warm replica, they all land on one row of the store."], cls="dia")

S(trace(K(3, "the trace"), "A hot key, then a cold one", [
  ("14:02", "code <code>k7Pq2mZ</code> goes from 3 clicks/s to " + B("40,000/s")),
  ("14:02", "its Redis shard: p99 0.8 ms → " + B("9 ms") + "; every other code on that shard slows too"),
  ("14:05", "a deploy restarts the shard: 200 ms of misses"),
  ("14:05", B("8,000 identical SELECTs on one row") + " in those 200 ms")],
  hedge=("Label the numbers", "Illustrative. The shape is the point: one key concentrates load that a fleet would spread.")), [
 "C: The trace.", P, "C: At two minutes past two, code k-seven-P-q-two-m-Z goes from three clicks a second to forty thousand.", P,
 "C: Its Redis shard's p ninety-nine goes from under a millisecond to nine, and every other code on that shard slows with it.", P,
 "C: At five past, a deploy restarts the shard. Two hundred milliseconds of misses.", P,
 "C: Eight thousand identical selects on one row.", P,
 "C: Illustrative numbers. The shape is the point: one key concentrates load that a fleet would otherwise spread."])

S(dia(K(3, "the fix"), "Answer from memory on every server; one miss per server", "ch3-fix",
      extra=strip(("fixb", "Mechanism", "ristretto on every redirect server (300k entries, 60 s). singleflight: concurrent misses for one code wait on one lookup. Negative caching for unknown codes."),
                  ("whyb", "Property", "L2: the hot key's load is spread across all servers' memory. The store sees at most one query per server per code, not one per click.")) + rejl(*REJ(3))), [
 P, "C: The fix is in the redirect service.", "[+2]",
 "C: An in-process cache on every redirect server: ristretto, three hundred thousand entries, sixty seconds. With forty servers, the viral code is a thousand requests a second from each one's own memory. Trivial.", P,
 "C: And single flight: when many requests miss the same code at once, the first one looks it up and the others wait on its answer. Plus negative caching for unknown codes, so a scanner's four-oh-fours don't reach the store.", P,
 "C: The store now sees at most one query per server per code, not one per click.", P,
 "C: Rejected: Redis replica reads alone. They spread the hot key over two nodes, not forty, and every click is still a network hop."], cls="dia")

S(dia(K(3, "sequence"), "A thousand requests, one lookup", "seq-ch3-flight"), [
 "C: As a sequence.", P, "C: A thousand requests for the same code arrive in twenty milliseconds.", P,
 "C: In-process miss: the first leads, nine hundred ninety-nine wait.", P, "C: One get on Redis.", P, "C: Miss: the shard is restarting.", P,
 "C: One select on the store.", P, "C: The U-R-L.", P,
 "C: One answer, a thousand three-oh-twos, and the code stays in process memory."], cls="dia")

S(plain(K(3, "single flight, as code"), "The first caller looks up; the rest wait",
  '<pre class="code" data-lang="go"><span class="kw">var</span> group singleflight.Group\n<span class="kw">func</span> resolve(code <span class="kw">string</span>) (Link, <span class="kw">error</span>) {\n    <span class="kw">if</span> l, ok := local.Get(code); ok { <span class="kw">return</span> l, <span class="kw">nil</span> }\n    v, err, _ := group.Do(code, <span class="kw">func</span>() (any, <span class="kw">error</span>) {\n        l, err := sharedCache.Get(code)        <span class="cm">// Redis, 2 ms timeout</span>\n        <span class="kw">if</span> err != <span class="kw">nil</span> { l, err = store.Get(code) } <span class="cm">// PostgreSQL by PK</span>\n        <span class="kw">if</span> err == <span class="kw">nil</span> { local.SetWithTTL(code, l, 1, 60*time.Second) }\n        <span class="kw">return</span> l, err\n    })\n    <span class="kw">return</span> v.(Link), err\n}</pre>' +
  strip(("whyb", "Why it works", "However many clicks arrive, each server sends at most one lookup per code per lifetime: load on the store is servers × hot codes, not clicks."), cols="one")), [
 "C: Single flight in Go. Check local memory. On a miss, group dot do with the code as the key: the first caller runs the function, shared cache then store, and fills local memory for sixty seconds. Every concurrent caller with the same code waits and receives the same result.", P,
 "C: The load on the store is servers times hot codes, however many clicks arrive."])

qs("Interviewer · the second-level push", "“Now the in-process lifetime means a takedown takes up to a minute longer. And a whole region's servers restart together.”", [
 "I: Now the in-process lifetime means a takedown takes up to a minute longer. And a whole region's servers restart together.", "[pause: 2.0]"])

S(plain(K(3, "the second fix, and the honest limit"), "Budget the lifetime; warm before serving", cards(
  ("amb", "Takedown", "The 60 s lifetime is a line in the takedown budget, and the invalidation topic drops entries early. Challenge five."),
  ("grn", "Restarts", "Roll them, one zone at a time. A starting pod warms its cache from the last hour's top codes before it passes readiness."),
  ("", "The real answer for a global viral link", "The edge, a minute from every user. Challenge four."), cols=3)), [
 P, "C: The lifetime is a line in the takedown budget, and the invalidation topic drops entries early anyway. That's challenge five.", P,
 "C: Restarts roll, one zone at a time, never a whole region at once, and a starting pod warms its cache from the last hour's top codes before it passes its readiness check.", P,
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
 P, "C: The browser, the edge and the redirect service.", "[+3]",
 "C: The naive answer: three-oh-one, it's permanent and it saves servers. It does save servers.", P,
 "C: Look at the red browser. A three-oh-one tells it to remember the answer, and it does, indefinitely. It never asks us again."], cls="dia")

S(trace(K(4, "the trace"), "Yesterday's click was the last one we saw", [
  ("Mon 10:00", "a user clicks <code>k7Pq2mZ</code>; we answer <b>301</b>; the browser caches it"),
  ("Tue 09:00", "the same user clicks again: " + B("answered by the browser; not counted")),
  ("Tue 15:00", "trust and safety blocks <code>k7Pq2mZ</code>: it now leads to a phishing page"),
  ("Tue 15:20", B("that user's browser still goes straight to the phishing page"))],
  hedge=("Two losses", "The owner loses the count. We lose the ability to protect the user.")), [
 "C: The trace.", P, "C: Monday a user clicks; we answer three-oh-one; the browser caches it.", P,
 "C: Tuesday the same user clicks again: the browser answers, we never see it, it's not counted.", P,
 "C: At three, the link is blocked for phishing.", P, "C: At three-twenty, that user's browser still goes straight to the phishing page.", P,
 "C: Two losses: the owner loses the count, and we lose the ability to protect the user."])

S(dia(K(4, "the fix"), "302 by default; a short, purgeable edge cache", "ch4-fix",
      extra=strip(("fixb", "Mechanism", "302 with browser caching off; the edge may keep it 60 s, tagged with a surrogate key, and can be purged. 301 only as an owner's opt-in for permanent, uncounted links."),
                  ("whyb", "Property", "Control (counting, and S2) stays at layers we can reach. The edge gives most of 301's saving at a bounded cost in freshness.")) + rejl(*REJ(4))), [
 P, "C: The fix.", "[+2]",
 "C: Three-oh-two by default, with browser caching off, and the edge allowed to keep it for sixty seconds, tagged with a surrogate key, purgeable.", P,
 "C: Three-oh-one only as an owner's opt-in, for links that are permanent and that they accept will not be counted.", P,
 "C: The property: counting and takedowns stay at layers we can reach. And the edge gives us most of the saving a three-oh-one would, at a bounded cost in freshness.", P,
 "C: Rejected: a C-D-N without a purge A-P-I. Then the sixty-second edge copy could not be taken back early."], cls="dia")

S(plain(K(4, "the layers"), "Where a redirect is answered, and what each layer costs", table(["Layer", "Answers in", "Sees the click?", "Can we take it back?"], [
  ["Browser, 301", "0 ms", "never again", "<b>no</b>"],
  ["Edge, 302 cached 60 s", "~5 ms near the user", "from edge logs, minutes late", "yes: purge, or 60 s"],
  ["Redirect service + caches", "~1 ms at the server", "every click, exact", "yes: invalidation, or 60 s"],
  ["Link store", "~5 ms, misses only", "—", "it is the truth"]])), [
 "C: The layers.", P, "C: The browser with a three-oh-one: zero milliseconds, never sees the click again, cannot be taken back.", P,
 "C: The edge with a three-oh-two cached for sixty seconds: a few milliseconds near the user, clicks from edge logs, minutes late, purgeable.", P,
 "C: Our servers and caches: a millisecond, every click, recallable.", P, "C: The store: the truth, for misses only."])

qs("Interviewer · the second-level push", "“Finance says the edge bill for ten billion requests is too high. Or edge-log counts arrive twenty minutes late.”", [
 "I: Finance says the edge bill for ten billion requests is too high. Or the counts from edge logs arrive twenty minutes late.", "[pause: 2.0]"])

S(plain(K(4, "the second fix, and the honest limit"), "Price both sides; say where exact counts come from", cards(
  ("amb", "The edge bill", "Compare the per-request edge cost with the servers and cross-region traffic it saves. Turn edge caching on per link, by click rate: only hot links need it."),
  ("", "Late counts", "Edge-log counts carry their lag, shown as <code>asOf</code>. When clicks are billed, the count comes from our servers or a signed edge function, not from logs."))), [
 P, "C: The edge bill: compare the per-request cost with the servers and cross-region traffic it saves, and turn edge caching on per link, by click rate. Only hot links need it, and they are two percent of links.", P,
 "C: Late counts are the stated lag, shown as as-of. When clicks are billed, the count must come from our servers, or a signed function running at the edge, not from logs. That is challenge six."])

say_slide("“301 against 302 is a product decision, not an optimisation. A 301 is answered by the browser forever, so we lose the click and the ability to take a link down. I default to 302, let the edge cache it for a minute, and offer 301 only to owners who want a permanent, uncounted link.”", [
 "V: If asked, I'd say: three-oh-one against three-oh-two is a product decision, not an optimisation. A three-oh-one is answered by the browser forever, so we lose the click and the ability to take a link down. I default to three-oh-two, let the edge cache it for a minute, and offer three-oh-one only to owners who want a permanent, uncounted link.", "[pause: 1.0]",
 "N: That fix creates the next question: we now hold copies at four layers. Can we withdraw all of them in five minutes?"])
