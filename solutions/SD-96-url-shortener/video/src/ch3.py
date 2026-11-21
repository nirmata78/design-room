from dsl import *
import dsl

def th(): dsl.SL[-1]["cls"] = (dsl.SL[-1]["cls"] + " theory").strip()

chapter(3, "Theory", 2, "What makes this problem hard, in words that outlive any product name", [
 "C: A short theory chapter before the design, so the design can lean on it. What a shortener is and is not, the properties, the central tension, six mechanisms, an options matrix, and the failure catalogue."]); th()

key("Theory · 1 of 6 · what it is", "A map from a <em>short, unique, hard-to-guess</em> code to a long URL, answered in <em>milliseconds from anywhere</em>, that can be <em>withdrawn everywhere</em> within a stated time.", [
 "V: A U-R-L shortener maps a short, unique, hard-to-guess code to a long U-R-L, answers a redirect for that code in milliseconds from anywhere, and can withdraw a code everywhere within a stated time.", "[pause: 1.0]",
 "C: Every clause is load-bearing. Unique: and the store, not the application, decides. Hard to guess: a code is not a secret, but it must not be walkable. In milliseconds from anywhere: the redirect is the product. Withdrawn everywhere within a stated time: every cached copy is a liability."], cls="theory")

S(plain("Theory · 1 of 6 · what it is not", "Four things it is confused with", '<div class="cards c2">'
  '<div class="cd"><h3>Not a hash function</h3><p>Hashing the URL is one way to make a key. It is not the system, and it is not unique once truncated.</p></div>'
  '<div class="cd amb"><h3>Not a cache</h3><p>The map is the source of truth. A cache is a copy that may be wrong for a bounded time.</p></div>'
  '<div class="cd red"><h3>Not a secret</h3><p>Seven characters can be sampled. A link that must stay private needs authentication.</p></div>'
  '<div class="cd"><h3>Not a CDN</h3><p>The edge is a layer that answers for us, and that we must be able to take back.</p></div></div>'), [
 "C: Four neighbours it is confused with. It is not a hash function: hashing the U-R-L is one way to get a key, and once you truncate it, it is not unique. It is not a cache: the map is the truth, and a cache is a copy allowed to be wrong for a bounded time.",
 "C: It is not a secret: seven characters can be sampled, so private content needs authentication, not a short code. And it is not a C-D-N: the edge is a layer that answers for us, and one we must be able to take back."], cls="theory")

S(plain("Theory · 2 of 6 · the two properties", "State safety and liveness separately",
  '<div class="prop safe"><div class="lbl">Safety · must never happen</div><p><b>S1</b> Two different long URLs are given the same code.<br><b>S2</b> A withdrawn code is answered by any layer after the takedown bound.</p></div>'
  '<div class="prop live"><div class="lbl">Liveness · must eventually happen</div><p><b>L1</b> A create gets a code without waiting for another create.<br><b>L2</b> A redirect for a live code answers within the target, even at a viral peak or with the store down.<br><b>L3</b> Every click is eventually counted, with a stated, measured loss.</p></div>'), [
 "V: Safety: two different long U-R-Ls never get the same code, and a withdrawn code is never answered by any layer after the takedown bound. Liveness: a create never waits for another create, a live code always redirects within the target, and every click is eventually counted, with a stated loss.", "[pause: 0.8]",
 "C: S-one is the collision. S-two is the phishing link that will not die. L-two is the viral peak. Every fix from here names which one it serves."], cls="theory")

S(dia("Theory · 3 of 6 · the central tension", "Speed of the answer against control over it", "tension"), [
 "C: The central tension. On the left, the browser: with a permanent redirect it answers in zero milliseconds, forever, and we never see that click again. Then the edge: fast and cheap, counted from logs, purgeable. Then our servers and caches: a millisecond, every click seen, recallable. Then the store: the truth, for misses only.",
 "C: Every layer closer to the user makes the redirect faster and cheaper, and counting and takedown harder or impossible. Three-oh-one against three-oh-two is the choice of where on this line the answer lives. That is a product decision, and challenge four."], cls="dia theory")

def mech(n, name, protects, how, rules, costs, say, live=True):
    S(plain(f"Theory · 4 of 6 · mechanism {n} of 6", name,
        f'<div class="prop {"live" if live else "safe"}"><div class="lbl">Property it protects</div><p>{protects}</p></div>'
        f'<div class="prop"><div class="lbl">How it works</div><p>{how}</p></div>'
        f'<div class="prop safe"><div class="lbl">Failure it rules out</div><p>{rules}</p></div>'
        f'<div class="prop" style="border-left-color:#d18f1c"><div class="lbl" style="color:#a86a12">What it costs</div><p>{costs}</p></div>'), say, cls="theory")

mech(1, "Counter ranges plus base-62", "S1 and L1.", "Each create server leases a block of 1,000 IDs from an allocator in one conditional write, then hands them out locally and encodes each in base-62.",
     "Two servers handing out the same code; a lock or a round trip on every create.", "Gaps when a server dies holding a range: harmless at 290× headroom. Codes are sequential, unless mechanism 2.", [
 "C: Mechanism one, counter ranges. It protects S-one and L-one. Each create server leases a block of a thousand I-Ds from an allocator in one conditional write, then hands them out from memory and encodes each in base sixty-two. It rules out two servers handing out the same code, and it rules out a round trip on every create. It costs gaps when a server dies holding a range, which is harmless with two hundred and ninety times headroom. And on its own it makes codes sequential."], live=False)
mech(2, "A keyed permutation", "Non-enumerability.", "A small Feistel network over the code space with a secret round key, plus cycle walking to stay below 62⁷. A bijection: distinct in, distinct out.",
     "Scrapers walking codes in order; codes that reveal how many links we create.", "A key to keep and rotate. It is not secrecy: private links still need authentication.", [
 "C: Mechanism two, a keyed permutation. It protects against enumeration. A small Feistel network over the code space with a secret key, plus cycle walking to stay below sixty-two to the seventh. It is a bijection: different inputs always give different outputs, so uniqueness is untouched. It rules out scrapers walking codes in order, and codes that leak our volume. It costs a key to keep and rotate, and it is not secrecy."], live=False)
mech(3, "The unique constraint as the final authority", "S1 for aliases and random codes.", "Insert with a unique key on the code. The one shard that owns the code accepts one insert and rejects the other.",
     "Check-then-insert races between two creators.", "A conflict answer the API must surface (409); a retry loop if codes are random.", [
 "C: Mechanism three, the unique constraint as the final authority. It protects S-one where codes can collide: custom aliases, or random codes. Insert with a unique key; the one shard that owns that code accepts one insert and rejects the other. It rules out the check-then-insert race. It costs a conflict answer, four-oh-nine, and a retry loop for random codes."], live=False)
mech(4, "Cache-aside with an in-process hot cache and single flight", "L2.", "Shared cache in front of the store; a small in-process cache on every redirect server; concurrent misses for one code wait on one lookup.",
     "A miss storm on one key; every viral click paying a network hop.", "Bounded staleness per layer, which the takedown budget must absorb. Memory on every server.", [
 "C: Mechanism four, layered caching with single flight. It protects L-two, the redirect under load. A shared cache in front of the store, a small in-process cache on every redirect server, and concurrent misses for one code waiting on a single lookup. It rules out a miss storm on one key, and every viral click paying a network hop. It costs bounded staleness at each layer, which the takedown budget has to absorb."])
mech(5, "An asynchronous click log", "L2 and L3.", "The redirect answers first, then appends a click event to a local buffer; batches go to a log partitioned by code; an aggregator counts per minute.",
     "A counter update on the hot path; a hot row per viral link.", "Counts are minutes late; a small, stated loss on a crash, or a durable buffer if clicks are billed.", [
 "C: Mechanism five, the asynchronous click log. It protects L-two and L-three. The redirect answers first, then appends a click event to a local buffer, which flushes batches to a log partitioned by code, and an aggregator counts per minute. It rules out a counter update on the hot path and a hot row per viral link. It costs minutes of lag and a small stated loss, or a durable buffer if clicks are ever billed."])
mech(6, "Status, invalidation and bounded lifetimes everywhere", "S2.", "A status in the store; an invalidation event to every cache; a purge at the edge; and a maximum lifetime at every layer, chosen so their sum fits the bound.",
     "A blocked phishing link still answered by a cache or an edge.", "Short lifetimes cost hit rate. A purge path to the CDN. 302 instead of 301.", [
 "C: Mechanism six, status, invalidation and bounded lifetimes. It protects S-two. A status in the store, an invalidation event to every cache, a purge at the edge, and a maximum lifetime at every layer, chosen so that even when a message is lost, the sum fits the bound. It rules out a blocked phishing link still being answered somewhere. It costs hit rate, a purge path, and the three-oh-two."], live=False)

S(plain("Theory · 5 of 6 · the options for codes", "Six ways to make a code", table(["Approach", "Unique without per-create coordination", "Length", "Guessable?", "Fails when"], [
  ("rej", ["A · Hash the URL, keep 7 characters", "no: truncation collides", "7", "deterministic", "same URL, two owners; a probe loop anyway"]),
  ("", ["B · Random 7 characters, insert with retry", "yes, via the constraint", "7", "no", "rarely: 0.34 % retries by year ten"]),
  ("rej", ["C · One global counter, base-62", "no: a round trip each", "6–7", "<b>yes</b>", "the counter is a bottleneck and a single point"]),
  ("pick", ["D · Ranges + keyed permutation + constraint", "yes, one lease per 1,000", "7", "no", "the allocator is down longer than a range lasts"]),
  ("rej", ["E · Time-based IDs (time + machine + sequence)", "yes", "10–11", "partly", "too long for a short link"]),
  ("rej", ["F · A pre-generated pool handed out from a queue", "yes", "7", "no", "a second system to fill, monitor and not lose"])], "bt sm mx")), [
 "C: Six ways to make a code. A, hash the U-R-L and keep seven characters: truncation collides, and the same U-R-L shortened by two owners wants two links, so you need a probe loop anyway. C, one global counter: a round trip per create, a single point of failure, and the codes are a counter anyone can read.",
 "C: E, time-based I-Ds: unique without coordination, but ten or eleven characters, which is not short. F, a pre-generated pool: works, but it's a second system to fill and monitor.",
 "C: That leaves B, random codes with a retry on conflict, and D, ranges plus a keyed permutation plus the constraint.",
 "V: I pick D, and I say plainly that B is an honest equal.", "[pause: 0.8]"], cls="theory")

S(plain("Theory · 5 of 6 · the pick, and what it gives up", "D, with B as the simpler equal", '<div class="cards c2">'
  '<div class="cd grn"><h3>Why D</h3><p>No retry loop, ever; six-character codes possible for a premium tier; creation stays fast when the store is slow; coordination once per thousand links.</p></div>'
  '<div class="cd red"><h3>What it gives up</h3><p>An allocator service to run, and a permutation key to manage. B needs neither: the constraint does all the work.</p></div></div>' +
  line("Choose B if creates stay under a few thousand a second and seven characters are always fine.", "a")), [
 "C: Why D. Generated codes never meet the constraint as a conflict, so there is no retry loop; the store's slowness never multiplies; and coordination happens once per thousand links. What it gives up: an allocator to run and a key to manage. B needs neither.",
 "C: So I'd say this in the room: if creates stay under a few thousand a second and seven characters are always fine, B is simpler and I'd pick it. At this scale, either is defensible. The reasoning is what is graded."], cls="theory")

S(plain("Theory · 6 of 6 · the failure catalogue", "What will go wrong", table(["#", "Failure", "Becomes"], [
  ["F1", "Two servers, one code; a custom-alias race", "<b>Challenge 1</b>"],
  ["F2", "Codes walked in order", "<b>Challenge 2</b>"],
  ["F3", "One viral code; a cold cache after a restart", "<b>Challenge 3</b>"],
  ["F4", "A layer answering that we cannot see or recall: 301, the edge", "<b>Challenge 4</b>"],
  ["F5", "A phishing link still live after five minutes", "<b>Challenge 5</b>"],
  ["F6", "Counting on the hot path; billed clicks", "<b>Challenge 6</b>"],
  ["F7", "A region, or the store's primary, lost", "<b>Challenge 7</b>"],
  ["F8", "Nobody notices a broken redirect", "<b>Challenge 8</b>"],
  ["F9", "A creator floods the bulk API", "rate limit per key, on the API slide"]], "bt sm")), [
 "C: The failure catalogue, which becomes the challenge list. Two servers handing out one code. Codes walked in order. One viral code, and a cold cache. A layer we cannot see or recall. A phishing link still live. Counting on the hot path. A region lost. And nobody noticing.",
 "C: The ninth, a creator flooding the bulk A-P-I, is a rate limit per key. I'll put it on the A-P-I slide rather than spend a challenge on it."], cls="theory")

S(plain("Theory · what each mechanism serves", "Every mechanism names its property", table(["Mechanism", "Serves", "Where it returns"], [
  ["M1 Counter ranges", "S1, L1", "challenges 1 and 7"],
  ["M2 Keyed permutation", "non-enumerability", "challenge 2"],
  ["M3 Constraint as authority", "<b>S1</b>", "challenge 1"],
  ["M4 Layered cache, single flight", "<b>L2</b>", "challenges 3 and 4"],
  ["M5 Asynchronous click log", "L2, L3", "challenge 6"],
  ["M6 Status, invalidation, lifetimes", "<b>S2</b>", "challenges 4 and 5"]], "bt sm") +
  grade("A mechanism with no stated property is decoration. Say which one each fix serves.")), [
 "N: Good theory has a consequence for the design. Every mechanism here names the property it serves and where it comes back.",
 "C: That is the vocabulary. On to the A-P-I."], cls="theory")
