# SD-96 URL shortener: reference solution (Staff L6/L7)

<!-- Video script for slide-video-kit/scripts/build_video.py. [slide: v-NNN] = frames/v-NNN.png, the number printed on every slide.
     Speakers: C candidate · I interviewer · V key line (slower) · N coach. Generated from src/*.py: edit the sources, not this file. -->
<!-- voices: N=af_heart@0.92 I=bf_emma@0.95 C=am_michael@0.9 V=am_michael@0.84 -->
<!-- labels: N=COACH -->
<!-- say: URL=U-R-L URLs=U-R-Ls CDN=C-D-N CDNs=C-D-Ns TTL=T-T-L TTLs=T-T-Ls SLO=S-L-O SLOs=S-L-Os SLI=S-L-I SLIs=S-L-Is API=A-P-I APIs=A-P-Is RAM=ram TB=terabytes MB=megabytes GB=gigabytes KB=kilobytes HTTP=H-T-T-P HTTPS=H-T-T-P-S SQL=S-Q-L DNS=D-N-S ID=I-D IDs=I-Ds EM=E-M AUX=aux SRE=S-R-E RFC=R-F-C QR=Q-R UUID=U-U-I-D Redis=Reddis p99=P-ninety-nine p50=P-fifty base62=base-sixty-two 301=three-oh-one 302=three-oh-two 404=four-oh-four 410=four-ten 409=four-oh-nine 201=two-oh-one 422=four-twenty-two LRU=L-R-U -->


## 0 Cold open

[slide: v-001]
[pause: 1.2]
C: A U-R-L shortener is the question everyone has drawn. A hash, a table, a cache. Interviewers still ask it at every level, because the grade is not on the table. It is on three places where the simple answer quietly fails.
[pause: 1.8]

[slide: v-002]
[pause: 0.6]
I: Design a U-R-L shortener. A long U-R-L goes in, a short link comes out, and anyone who opens the short link is redirected.
[pause: 1.5]

[slide: v-003]
[pause: 1.3]
C: Here is the hook. First, two servers must never hand out the same code, and they must not ask each other on every create. Second, one link can go viral: forty thousand clicks a second on one key, and a read-heavy system becomes a single hot spot.
C: Third, the things beside the redirect. Click counts and phishing takedowns both fight the caching that makes the redirect fast. This picture is the whole tension: every layer that answers closer to the user is faster and cheaper, and harder to count or to take back.
[pause: 1.1]

[slide: v-004]
[pause: 1.0]
N: Five axes. The weak answer draws a fine diagram and never says a number. The strong answer says why seven characters, who decides a collision, and what a viral link does to one cache shard.
C: And one rule I'll keep for the whole round: the redirect is the product. Everything else stands beside it, never in front of it.
[pause: 1.0]

[slide: v-005]
[pause: 0.7]
V: A U-R-L shortener is a read path with a write path attached. Make codes unique without a lock per create, and unguessable without a lookup. Keep the redirect to one memory read. And let nothing, not counting, not abuse, not analytics, stand between the click and the answer.
[pause: 1.6]

[slide: v-006]
[pause: 0.6]
C: The order. Requirements, numbers, and a short theory chapter. Then the A-P-I and the data, and a design in three versions, each answering the objection to the one before.
C: Then most of the time goes to eight challenges that break it, where each fix creates the next question. A build cost, and a recap.
[pause: 0.8]

[pause: 1.4]

## 1 Requirements and scope

[slide: v-007]
[pause: 1.2]
C: Six questions before I draw anything. Each answer moves the design.
[pause: 1.8]

[slide: v-008]
[pause: 0.6]
C: How many links, and how many clicks?
I: A hundred million new links a month. Ten billion redirects a month. And a viral link can take forty thousand clicks a second.
C: A hundred to one, reads to writes. And the peak is not many keys, it is one key. That last number will get its own challenge.
[pause: 0.6]

[slide: v-009]
[pause: 0.6]
C: How long does a link live?
I: Forever by default. The creator can set an optional expiry date.
C: Forever means the code space has to last for years, so I'll size it over ten. And printed links never go away, which makes the code format a one-way door.
[pause: 0.6]

[slide: v-010]
[pause: 0.6]
C: Can users choose their own alias?
I: Yes, paying users can. First come, first served.
C: First come, first served is a uniqueness race between two customers. Somebody has to decide who was first, and it should not be my application code.
[pause: 0.6]

[slide: v-011]
[pause: 0.6]
C: What do owners see about their clicks?
I: Clicks per link, by day and by country, in a dashboard. Not billed today. Product may want to bill per click later.
C: Not billed means I may lose a tiny fraction and say so. Billed later means that decision is not permanent. Challenge six.
[pause: 0.6]

[slide: v-012]
[pause: 0.6]
C: What about abuse?
I: Phishing and malware links exist. Legal wants a reported link dead everywhere within five minutes.
C: Everywhere is the hard word. Every cache that holds the answer is a copy I have to reach. Challenge five.
[pause: 0.6]

[slide: v-013]
[pause: 0.6]
C: Who calls the service?
I: Browsers following links. And integrators who create links in bulk through an A-P-I.
C: Bulk creators retry, so create must be idempotent, and they need a rate limit per key. Two lines on the A-P-I slide.
[pause: 0.6]

[slide: v-014]
[pause: 0.6]
C: Four functional requirements. One, create: a long U-R-L in, a short link out, with an optional alias and expiry, and a retried request gets the same answer. Two, redirect: a code gets the long U-R-L, or a not-found or gone page.
C: Three, count: clicks per link per day per country, within minutes. Four, withdraw: the owner deletes, or trust and safety blocks, and it stops working everywhere within five minutes. Each of these gets a numbered flow later.
[pause: 0.8]

[slide: v-015]
[pause: 0.6]
C: The numbers, and they are initial targets, not measurements. A redirect under twenty milliseconds at the ninety-ninth percentile, measured at the server. Four nines of redirect availability. Create under two hundred milliseconds, three nines, because creating is less urgent than following.
C: A takedown effective everywhere within five minutes. And counts may lag by minutes and may lose a tiny, measured fraction, until clicks are billed.
[pause: 0.8]

[slide: v-016]
[pause: 0.6]
C: In scope: create, redirect, aliases, expiry, counts, takedowns, and a bulk A-P-I with a rate limit per key.
C: Out, on purpose. The malware classifier itself: I call it, I don't build it. Accounts and billing. Q-R codes, which are just a picture of the same link. Link-in-bio pages. And editing a link's target, which I'd say aloud: for every cache, an edit is a takedown plus a create, so it rides on challenge five.
[pause: 0.8]

[slide: v-017]
[pause: 0.7]
V: The core is three things. A code generator that never collides. A redirect path that is one memory read. And a side path for counting and withdrawal that never sits in front of the redirect.
[pause: 0.8]
N: Notice the candidate named the core before drawing. That is the scoping signal: what the system is, in a sentence, and what it is not.
[pause: 1.6]

[pause: 1.4]

## 2 Estimates

[slide: v-018]
[pause: 1.2]
C: Numbers next, each as arithmetic, each with the decision it drives. I'll label them: given, derived or illustrative.
[pause: 1.8]

[slide: v-019]
[pause: 1.0]
C: Traffic. A hundred million creates a month, divided by about two point six million seconds, is about forty a second, and say ten times that at peak: four hundred. That is nothing. One database could take it. So the hard part of create is uniqueness, not throughput.
C: Ten billion redirects a month is about four thousand a second. Reads to writes, a hundred to one. And the peak the interviewer gave me is forty thousand a second on one code. The peak is one key, which is a very different problem from a big fleet.
[pause: 1.0]

[slide: v-020]
[pause: 1.3]
C: How long must a code be? A hundred million a month, times twelve, times ten years, is one point two times ten to the ten links. The alphabet is sixty-two symbols: lower case, upper case and digits.
C: Six characters give sixty-two to the sixth, about five point seven times ten to the ten. Only four point seven times the links I need, and random codes would collide long before that. Seven characters give three point five times ten to the twelve, about two hundred and ninety times. Seven it is.
C: And with random codes, at the end of year ten, a new code hits an existing one with probability links over space: about a third of a percent. Small enough that a retry on conflict is fine.
[pause: 1.1]

[slide: v-021]
[pause: 1.0]
C: Storage. One point two times ten to the ten links at about five hundred bytes each, with the U-R-L, the owner, dates and index overhead, is six terabytes, eighteen with three replicas. Not the hard part.
C: The hot set. If two percent of links take ninety percent of clicks, that's two hundred million links, about a hundred gigabytes. A few cache nodes. This number is illustrative, and the first thing I'd measure.
C: So the store sees misses only: four thousand a second times a one percent miss rate is forty a second. Except when the cache is cold, after a restart, when it can see all four thousand. Keep that for challenge three.
[pause: 1.0]

[slide: v-022]
[pause: 1.0]
C: Three small numbers that shape the design. If each create server leases a thousand I-Ds at a time, four hundred creates a second is less than one lease every two seconds. So the allocator can be a small, strongly consistent store.
C: Click events: four thousand a second, two hundred bytes each, under a megabyte a second, seventy gigabytes a day. A log and an aggregator, not a counter on the link row.
C: And one viral key at forty thousand a second lands on one cache shard. The shard can take it, but its queue and its tail become every viral click's tail.
[pause: 1.0]

[slide: v-023]
[pause: 1.3]
C: The latency budget at the server. A cache lookup, about a millisecond. On a miss, the link store, about five. Parsing, writing the response and emitting the click event, about one more. Seven milliseconds in the worst case with a miss, against twenty.
C: That spare is room for one miss. It is not room for a synchronous write of a click counter, or a call to a classifier on the redirect path. The budget says what may never be added.
[pause: 1.1]

[slide: v-024]
[pause: 0.6]
C: The takedown budget. Five minutes is not a hope, it is a sum. The status write and the shared cache delete are done directly by the takedown, in seconds. Each redirect server's in-process cache is dropped by an event, and if that event is lost, a sixty-second lifetime ends it. The edge is purged by its A-P-I, and if that fails, a sixty-second cache time ends it.
C: The rule: every layer's lifetime fits inside five minutes, summed along the worst path. I'll come back to it with numbers in challenge five.
[pause: 0.8]

[pause: 1.4]

## 3 Theory

[slide: v-025]
[pause: 1.2]
C: A short theory chapter before the design, so the design can lean on it. What a shortener is and is not, the properties, the central tension, six mechanisms, an options matrix, and the failure catalogue.
[pause: 1.8]

[slide: v-026]
[pause: 0.7]
V: A U-R-L shortener maps a short, unique, hard-to-guess code to a long U-R-L, answers a redirect for that code in milliseconds from anywhere, and can withdraw a code everywhere within a stated time.
[pause: 1.0]
C: Every clause is load-bearing. Unique: and the store, not the application, decides. Hard to guess: a code is not a secret, but it must not be walkable. In milliseconds from anywhere: the redirect is the product. Withdrawn everywhere within a stated time: every cached copy is a liability.
[pause: 1.6]

[slide: v-027]
[pause: 0.6]
C: Four neighbours it is confused with. It is not a hash function: hashing the U-R-L is one way to get a key, and once you truncate it, it is not unique. It is not a cache: the map is the truth, and a cache is a copy allowed to be wrong for a bounded time.
C: It is not a secret: seven characters can be sampled, so private content needs authentication, not a short code. And it is not a C-D-N: the edge is a layer that answers for us, and one we must be able to take back.
[pause: 0.8]

[slide: v-028]
[pause: 0.6]
V: Safety: two different long U-R-Ls never get the same code, and a withdrawn code is never answered by any layer after the takedown bound. Liveness: a create never waits for another create, a live code always redirects within the target, and every click is eventually counted, with a stated loss.
[pause: 0.8]
C: S-one is the collision. S-two is the phishing link that will not die. L-two is the viral peak. Every fix from here names which one it serves.
[pause: 0.8]

[slide: v-029]
[pause: 1.3]
C: The central tension. On the left, the browser: with a permanent redirect it answers in zero milliseconds, forever, and we never see that click again. Then the edge: fast and cheap, counted from logs, purgeable. Then our servers and caches: a millisecond, every click seen, recallable. Then the store: the truth, for misses only.
C: Every layer closer to the user makes the redirect faster and cheaper, and counting and takedown harder or impossible. Three-oh-one against three-oh-two is the choice of where on this line the answer lives. That is a product decision, and challenge four.
[pause: 1.1]

[slide: v-030]
[pause: 0.6]
C: Mechanism one, counter ranges. It protects S-one and L-one. Each create server leases a block of a thousand I-Ds from an allocator in one conditional write, then hands them out from memory and encodes each in base sixty-two. It rules out two servers handing out the same code, and it rules out a round trip on every create. It costs gaps when a server dies holding a range, which is harmless with two hundred and ninety times headroom. And on its own it makes codes sequential.
[pause: 0.8]

[slide: v-031]
[pause: 0.6]
C: Mechanism two, a keyed permutation. It protects against enumeration. A small Feistel network over the code space with a secret key, plus cycle walking to stay below sixty-two to the seventh. It is a bijection: different inputs always give different outputs, so uniqueness is untouched. It rules out scrapers walking codes in order, and codes that leak our volume. It costs a key to keep and rotate, and it is not secrecy.
[pause: 0.8]

[slide: v-032]
[pause: 0.6]
C: Mechanism three, the unique constraint as the final authority. It protects S-one where codes can collide: custom aliases, or random codes. Insert with a unique key; the one shard that owns that code accepts one insert and rejects the other. It rules out the check-then-insert race. It costs a conflict answer, four-oh-nine, and a retry loop for random codes.
[pause: 0.8]

[slide: v-033]
[pause: 0.6]
C: Mechanism four, layered caching with single flight. It protects L-two, the redirect under load. A shared cache in front of the store, a small in-process cache on every redirect server, and concurrent misses for one code waiting on a single lookup. It rules out a miss storm on one key, and every viral click paying a network hop. It costs bounded staleness at each layer, which the takedown budget has to absorb.
[pause: 0.8]

[slide: v-034]
[pause: 0.6]
C: Mechanism five, the asynchronous click log. It protects L-two and L-three. The redirect answers first, then appends a click event to a local buffer, which flushes batches to a log partitioned by code, and an aggregator counts per minute. It rules out a counter update on the hot path and a hot row per viral link. It costs minutes of lag and a small stated loss, or a durable buffer if clicks are ever billed.
[pause: 0.8]

[slide: v-035]
[pause: 0.6]
C: Mechanism six, status, invalidation and bounded lifetimes. It protects S-two. A status in the store, an invalidation event to every cache, a purge at the edge, and a maximum lifetime at every layer, chosen so that even when a message is lost, the sum fits the bound. It rules out a blocked phishing link still being answered somewhere. It costs hit rate, a purge path, and the three-oh-two.
[pause: 0.8]

[slide: v-036]
[pause: 1.0]
C: Six ways to make a code. A, hash the U-R-L and keep seven characters: truncation collides, and the same U-R-L shortened by two owners wants two links, so you need a probe loop anyway. C, one global counter: a round trip per create, a single point of failure, and the codes are a counter anyone can read.
C: E, time-based I-Ds: unique without coordination, but ten or eleven characters, which is not short. F, a pre-generated pool: works, but it's a second system to fill and monitor.
C: That leaves B, random codes with a retry on conflict, and D, ranges plus a keyed permutation plus the constraint.
V: I pick D, and I say plainly that B is an honest equal.
[pause: 1.0]

[slide: v-037]
[pause: 0.6]
C: Why D. Generated codes never meet the constraint as a conflict, so there is no retry loop; the store's slowness never multiplies; and coordination happens once per thousand links. What it gives up: an allocator to run and a key to manage. B needs neither.
C: So I'd say this in the room: if creates stay under a few thousand a second and seven characters are always fine, B is simpler and I'd pick it. At this scale, either is defensible. The reasoning is what is graded.
[pause: 0.8]

[slide: v-038]
[pause: 1.0]
C: The failure catalogue, which becomes the challenge list. Two servers handing out one code. Codes walked in order. One viral code, and a cold cache. A layer we cannot see or recall. A phishing link still live. Counting on the hot path. A region lost. And nobody noticing.
C: The ninth, a creator flooding the bulk A-P-I, is a rate limit per key. I'll put it on the A-P-I slide rather than spend a challenge on it.
[pause: 1.0]

[slide: v-039]
[pause: 1.0]
N: Good theory has a consequence for the design. Every mechanism here names the property it serves and where it comes back.
C: That is the vocabulary. On to the A-P-I.
[pause: 1.0]

[pause: 1.4]

## 4 API and entities

[slide: v-040]
[pause: 1.2]
C: Four public calls, one internal. Each tagged with the requirement it serves and the data it reads or writes.
[pause: 1.8]

[slide: v-041]
[pause: 1.0]
C: Create is a post with the long U-R-L, an optional alias and expiry, and an idempotency key, so a bulk integrator's retry gets the same code back. It answers two-oh-one, or four-oh-nine if the alias is taken, or four-twenty-two if the U-R-L is known-bad. Aliases must be eight characters or more, so they never collide with a generated seven-character code. Each key has a rate limit: that's failure nine.
C: The redirect is a get on the code: three-oh-two, four-oh-four, or four-ten Gone for a withdrawn code, so search crawlers stop asking. Stats return counts by day and country with an as-of time, so the owner knows how fresh they are. Delete and takedown write the status and emit an invalidation. And internally, lease range hands a create server a thousand I-Ds.
[pause: 1.0]

[slide: v-042]
[pause: 1.0]
C: The redirect on the wire. A get on the code. The answer is a three-oh-two Found with a Location header. The cache headers are the design decision: private, max age zero for the browser, so it asks us again every time, which means we count the click and can withdraw the link. And sixty seconds for the edge, so a viral link is cheap.
C: Both lifetimes are in the takedown budget. That is why the headers are on a slide.
[pause: 1.0]

[slide: v-043]
[pause: 1.3]
C: The conceptual model. An owner creates links. A link has one code and one long U-R-L, a status and an optional expiry. Clicks are weak entities: they only exist as clicks of a link, and they roll up into daily counts. A takedown withdraws a link. And range leases record which server holds which block of I-Ds.
C: One sentence on the bottom matters most: a code has exactly one live long U-R-L, but the same U-R-L may have many codes. So a hash of the U-R-L is not a key.
[pause: 1.1]

[slide: v-044]
[pause: 1.0]
C: The physical model. The link table's primary key is the code, and it is sharded by code, because the code is the only key the redirect ever uses. The owner's dashboard gets its own table, keyed by owner and time, never on the hot path. Range leases live in a small consensus store. Daily counts are written by the aggregator.
C: And in each redirect server's memory: a map from code to U-R-L and status, a lifetime of thirty to sixty seconds, and an in-flight map for single flight. A hash of the U-R-L is not a key, and a click never updates the link row.
[pause: 1.0]

[slide: v-045]
[pause: 0.6]
C: Two rules I'd defend in a review. The code is the only hot key: shard by code, every redirect is one key lookup, and owner queries go to a second table written on create. And no counter on the link row: a click never writes to it, because a viral link would make that row the hottest lock in the system.
[pause: 0.8]

[pause: 1.4]

## 5 High-level design

[slide: v-046]
[pause: 1.2]
C: The design in three versions. Each is drawn on the same baseline, and each answers the objection to the one before.
[pause: 1.8]

[slide: v-047]
[pause: 1.3]
C: Version one. One service, one relational table from code to U-R-L. Create picks a random seven-character code and inserts it, retrying on a conflict. Redirect reads the table and answers three-oh-two.
C: It works, and at a thousand clicks a second it would be fine. Here is the objection: four thousand reads a second on one table, with a forty-thousand peak on one row. Analytics would be an update per click. And nothing scales out, because creating and redirecting are one process with one failure mode.
[pause: 1.1]

[slide: v-048]
[pause: 1.3]
C: Version two answers that objection. The two paths have different loads and different tolerances, so they become two services. The redirect service is stateless, many copies, with a shared cache in front of a sharded link store: cache-aside, so a miss reads the store and fills the cache.
C: The create service leases I-D ranges from the allocator and inserts with a unique constraint. The new boxes are outlined in blue.
C: The objection it leaves: one viral code is one hot cache key. Clicks still have nowhere to go. And a takedown sits behind every cache.
[pause: 1.1]

[slide: v-049]
[pause: 1.3]
C: Version three protects the redirect. An edge in front caches three-oh-twos for sixty seconds. Each redirect server has an in-process cache with single flight. Clicks go after the answer into a click log, an aggregator and a stats store along the bottom.
C: The takedown service writes the status and publishes on an invalidation channel that reaches the edge, every redirect server, and the shared cache. And create calls a safety check on the U-R-L before issuing a code.
C: The objection it leaves is the details. Those are the challenges.
[pause: 1.1]

[slide: v-050]
[pause: 1.0]
C: The three versions in one table. Version one: one service, one table. Version two: split the paths, cache the read, lease ranges. Version three: protect the redirect and make every copy withdrawable. Each answers the objection to the one before.
[pause: 1.0]

[slide: v-051]
[pause: 1.3]
C: Flow one, create, with numbered arrows. One: the client posts the long U-R-L with an idempotency key. Two: the create service asks the safety check whether the U-R-L is known-bad. Three: it takes the next I-D from its leased range, leasing a new one at half-used.
C: Four: it permutes the I-D, encodes it in base sixty-two, and inserts it with the unique constraint on the code. For a custom alias, the alias is the code, and the constraint decides who gets it. Then two-oh-one with the short U-R-L.
[pause: 1.1]

[slide: v-052]
[pause: 1.3]
C: The same flow as a sequence. Post with an idempotency key. Known-bad? No. Next I-D from the range, keyed permutation, base sixty-two: a-Z-three-k-Q-nine-x. Insert with the unique constraint. Okay. Two-oh-one with the short link. One write on the store, no lock across servers.
[pause: 1.1]

[slide: v-053]
[pause: 1.3]
C: Flow two, the redirect. One: the browser asks the edge for the code. Two: on an edge miss, the request reaches a redirect server, which checks its in-process cache. Three: on a miss, the shared cache. Four: on a miss there too, the link store.
C: Five and six: the store fills the shared cache and the U-R-L comes back. The server checks the status and the expiry. Seven and eight: the three-oh-two goes back through the edge, which may keep it for sixty seconds. For a hot code, steps three to six never happen: the answer is in memory.
[pause: 1.1]

[slide: v-054]
[pause: 1.3]
C: As a sequence. Get the code. In-process miss. Shared cache, about a millisecond: miss. Select from the link store: live. Fill both caches. Three-oh-two with the Location. And only then, the click event to the log, fire and forget. Nothing after the answer can delay the answer.
[pause: 1.1]

[slide: v-055]
[pause: 1.3]
C: Flow three, counting. One and two: the click arrives through the edge as before. Three: after answering, the redirect server appends a click event to a local buffer, which flushes a batch every second or every thousand events into the click log, partitioned by code.
C: Four: the aggregator reads batches and counts per code per minute, then per day per country. Five: the counts land in the stats store, and the owner's dashboard reads them with an as-of time. If the buffer is full, events are dropped and the drops are counted.
[pause: 1.1]

[slide: v-056]
[pause: 1.3]
C: Flow four, withdrawal. One: the takedown service writes status blocked in the link store. Two: it publishes on the invalidation channel. Three: the shared cache deletes the key; the takedown also deletes it directly and retries until confirmed. Four: every redirect server drops the code from its in-process cache.
C: Five: the edge is purged. The next request for that code reads blocked from the store and answers four-ten Gone, with a warning page. And every step is audited.
[pause: 1.1]

[slide: v-057]
[pause: 1.3]
C: As a sequence. Trust and safety posts the takedown with a reason. The status is set and audited. The shared cache key is deleted, retried until confirmed. The invalidation goes out to every server and the edge. If that event is lost, the in-process and edge lifetimes are sixty seconds each, so the worst case is about two minutes. The next request reads blocked: four-ten.
[pause: 1.1]

[slide: v-058]
[pause: 1.3]
C: The C-four context view. Visitors follow short links. Link owners create links and read stats. Trust and safety blocks bad links. And the system calls one external dependency on create: a U-R-L classifier that says whether a U-R-L is known-bad. Nothing external sits on the redirect path.
[pause: 1.1]

[slide: v-059]
[pause: 1.3]
C: The container view. The edge, which we buy. The redirect service, stateless, with its in-process cache. The shared cache. The link store, a sharded key-value store with a unique code. The create service and the range allocator, a small consensus store. The click pipeline: a log and an aggregator. And the takedown service.
C: The redirect path is four boxes in a row, left to right. Everything else is above it or below it. That layout is the thesis, drawn.
[pause: 1.1]

[slide: v-060]
[pause: 1.0]
C: Technology, mechanism first. The link store is a sharded key-value or relational store keyed by code, not one primary: writes would fit, but reads and storage outgrow it, and it would be one failure domain. The shared cache is cache-aside, so it survives the store being slow.
C: The allocator is a small consensus-backed store, not a counter row in the link store, which would couple create to the busiest store. Clicks go to a buffer, a log and an aggregator, not a counter per link. And the edge is bought, with a purge A-P-I. Points of presence are not our business.
[pause: 1.0]

[pause: 1.4]

## 6 Bridge

[slide: v-061]
[pause: 1.2]
V: It works. The question now is where it breaks first.
[pause: 1.8]

[slide: v-062]
[pause: 1.3]
C: The baseline with eight attack points. The create service: two servers and one code, then codes that can be walked. The cache and the store: one viral key. The edge and the browser: three-oh-one or three-oh-two. Every cache layer: a takedown in five minutes. The click log: counting without slowing the redirect. The store's region: a region lost. And finally: how would we know any of it was broken? I'll take them in an order where each fix creates the next question.
[pause: 1.1]

[pause: 1.4]

## 7 Challenges

[slide: v-063]
[pause: 1.2]
C: Eight challenges, each the same way: the question, the naive answer, a case with numbers, where it breaks, the fix, why it works, then the interviewer pushes on the fix itself, and what I'd say in the room.
[pause: 1.8]

[pause: 1.4]

## 7.1 Challenge 1: Two servers, one code

[slide: v-064]
[pause: 1.2]
N: Challenge one. Two create servers run at once: how do they never hand out the same code, without asking each other every time?
[pause: 1.8]

[slide: v-065]
[pause: 0.6]
I: Two create servers run at the same time. How do they never hand out the same code, without asking each other every time?
[pause: 2.0]

[slide: v-066]
[pause: 1.3]
C: The naive answer: generate a random code, check whether it exists, insert it if not. Look at the red create service. The check is stale the moment it returns. Between the select and the insert, another server can do exactly the same thing.
[pause: 1.1]

[slide: v-067]
[pause: 1.0]
C: The trace. Two customers ask for the alias sale, three milliseconds apart. Server A selects: none. Server B selects: none. A inserts. B inserts, and without a constraint it overwrites. The next day, A's printed flyers open B's page.
C: Random codes have the same race. A third of a percent sounds rare, but at four hundred creates a second, rare happens every day.
[pause: 1.0]

[slide: v-068]
[pause: 1.3]
C: The fix has two parts, outlined green. Generated codes come from disjoint ranges: each server leases a thousand I-Ds from the allocator in one conditional write and hands them out from memory. Two servers can never draw the same I-D, so generated codes never even reach the constraint as a conflict.
C: And every insert carries a unique constraint on the code. For a custom alias, the one shard that owns sale accepts one insert and rejects the other: one two-oh-one, one four-oh-nine. The store is the authority, not my application. One more rule: aliases are eight characters or longer, so an alias can never take a code the counter will produce later.
[pause: 1.1]

[slide: v-069]
[pause: 1.3]
C: The ranges. The allocator says next is forty-one thousand. Server A holds forty thousand to forty thousand nine hundred ninety-nine and is on forty thousand and seventeen. B and C hold their own blocks. Each next I-D goes through the permutation and base sixty-two.
C: A server that crashes wastes the rest of its block. That is a gap, never a collision, and with two hundred and ninety times more codes than links, gaps cost nothing.
[pause: 1.1]

[slide: v-070]
[pause: 1.3]
C: As a sequence. Server A leases with a compare-and-set: next goes from forty thousand to forty-one thousand only if it is still forty thousand. Okay, A owns that block. It hands out I-Ds locally and leases the next block early, at half-used. Then a customer asks for sale: the insert conflicts, and the second customer gets four-oh-nine while the first keeps it.
[pause: 1.1]

[slide: v-071]
[pause: 1.0]
C: The lease in code. Read next, then compare-and-set it to next plus a thousand. If another server won the race, read again. When it succeeds, the range is ours alone. Inside a lease, no coordination is needed. Across leases, the compare-and-set makes overlap impossible.
[pause: 1.0]

[slide: v-072]
[pause: 0.6]
I: The allocator is down. Or a server crashes holding half a range.
[pause: 2.0]

[slide: v-073]
[pause: 0.6]
C: Three answers. Runway: each server leases its next block at half-used, so it holds five hundred to fifteen hundred I-Ds. At the four-hundred-a-second peak across ten servers, that's twelve to thirty-seven seconds; at the average, two to six minutes. The allocator is a small replicated store with a consensus protocol, so one node lost is not an outage. A crashed server's unused I-Ds are simply skipped.
C: The honest limit. If the allocator is down for minutes, creates stop. Redirects never depended on it. That is the right way round: the product keeps working.
[pause: 0.8]

[slide: v-074]
[pause: 0.7]
V: If asked, I'd say: each create server leases a block of a thousand I-Ds, so coordination happens once per thousand links, not once per link. The unique constraint on the code is the final authority, so an alias race ends in one success and one conflict. If the allocator goes down, servers have their leased runway, and redirects never depended on it.
[pause: 1.0]
N: That fix creates the next question: codes from a counter are in order.
[pause: 1.6]

[pause: 1.4]

## 7.2 Challenge 2: Codes in order

[slide: v-075]
[pause: 1.2]
N: Challenge two. The codes come from a counter: what can a stranger learn from that, and how do we stop it without losing uniqueness?
[pause: 1.8]

[slide: v-076]
[pause: 0.6]
I: Your codes come from a counter. What can someone learn from that?
[pause: 2.0]

[slide: v-077]
[pause: 1.3]
C: The naive answer: base sixty-two makes them look random. It doesn't. Base sixty-two of a counter is still a counter, in a different alphabet. Neighbouring I-Ds give neighbouring codes, and the red box is the encoder that does it.
[pause: 1.1]

[slide: v-078]
[pause: 1.0]
C: The trace. At nine a user gets zero-zero-zero-zero-g-eight-Q. At ten past, another: zero-zero-zero-zero-g-B-A. Subtract: two thousand links in ten minutes. That's our creation rate, for free.
C: Then a scraper asks for the next code, and the next, and reads every link created that morning, including someone's unlisted document share. Volume leaks to a competitor, and links leak that their owners thought nobody would find.
[pause: 1.0]

[slide: v-079]
[pause: 1.3]
C: The fix lives in the same create box. Between the counter and the encoder, a keyed permutation: a four-round Feistel network over forty-two bits with a secret key, cycle-walked to stay below sixty-two to the seventh. Then base sixty-two. And a rate limit on four-oh-fours per client, so random guessing is slow.
[pause: 1.1]

[slide: v-080]
[pause: 1.3]
C: Three neighbouring I-Ds: forty thousand and seventeen, eighteen, nineteen. Out come a-Z-three-k-Q-nine-x, P-q-zero-seven-m-W-d, and three-f-L-x-nine-T-b. Unrelated. And because a Feistel network is a bijection, two different I-Ds can never give the same code. Uniqueness is untouched.
[pause: 1.1]

[slide: v-081]
[pause: 1.0]
C: In code. Split forty-two bits into two halves. Four rounds: swap the halves and mix one with a keyed pseudo-random function of the other. Each round is invertible, so the whole thing is a bijection. If the result lands above sixty-two to the seventh, run it again: that's cycle walking, and it keeps the bijection on exactly the code space.
[pause: 1.0]

[slide: v-082]
[pause: 0.6]
I: The key leaks. Or a customer says short links to private files must not be guessable at all.
[pause: 2.0]

[slide: v-083]
[pause: 0.6]
C: A leaked key: new codes use a new key, with a version marker or a fresh slice of the I-D space. Old codes stay valid, because codes are stored, never recomputed. Nothing breaks.
C: Private content is the honest limit. Forty-two bits can be sampled by an attacker with enough addresses. Links to private files need authentication or a long random token, not a short link. That's a conversation with product, not a cleverer encoder.
[pause: 0.8]

[slide: v-084]
[pause: 0.7]
V: If asked, I'd say: a counter gives uniqueness, but base sixty-two of a counter is still a counter. It leaks our volume and lets anyone walk the links. I pass the I-D through a keyed permutation, which keeps it unique and makes neighbours unrelated. And I'm clear that a short code is not a secret: private links need authentication.
[pause: 1.0]
N: Codes are settled. The next question is the read side: one code, forty thousand times a second.
[pause: 1.6]

[pause: 1.4]

## 7.3 Challenge 3: One link at 40,000 clicks a second

[slide: v-085]
[pause: 1.2]
N: Challenge three. One link goes viral: what happens to the one cache shard that holds it, and to the store when that shard restarts?
[pause: 1.8]

[slide: v-086]
[pause: 0.6]
I: A link goes viral. Forty thousand clicks a second, all on one code. What happens?
[pause: 2.0]

[slide: v-087]
[pause: 1.3]
C: The naive answer: it's cached, so it's fine. Look at the red boxes. A cache is sharded by key, so all forty thousand requests land on one shard. And if that shard restarts, they all land on one row of the store.
[pause: 1.1]

[slide: v-088]
[pause: 1.0]
C: The trace. At two minutes past two, code k-seven-P-q-two-m-Z goes from three clicks a second to forty thousand. Its cache shard's p ninety-nine goes from under a millisecond to nine, and every other code on that shard slows with it. At five past, a deploy restarts the shard. Two hundred milliseconds of misses: eight thousand identical selects on one row.
C: Illustrative numbers. The shape is the point: one key concentrates load that a fleet would otherwise spread.
[pause: 1.0]

[slide: v-089]
[pause: 1.3]
C: The fix is in the redirect service, outlined green. An in-process cache on every redirect server: a few hundred thousand entries, thirty to sixty seconds. With forty servers, the viral code is a thousand requests a second from each one's own memory. Trivial.
C: And single flight: when many requests miss the same code at once, the first one looks it up and the others wait on its answer. Plus negative caching for unknown codes, so a scanner's four-oh-fours don't reach the store. The store now sees at most one query per server per code.
[pause: 1.1]

[slide: v-090]
[pause: 1.3]
C: As a sequence. A thousand requests for the same code arrive in twenty milliseconds. In-process miss: the first leads, nine hundred ninety-nine wait. One get on the shared cache: miss, it's restarting. One select on the store. One answer, a thousand three-oh-twos, and the code stays in process memory for thirty seconds.
[pause: 1.1]

[slide: v-091]
[pause: 1.0]
C: Single flight in code. Check local memory. On a miss, register a future for the code. If you're the first, you do the lookup, shared cache then store, fill local memory for thirty seconds, and release the waiters. Everyone else just waits on the future. The load on the store is servers times hot codes, however many clicks arrive.
[pause: 1.0]

[slide: v-092]
[pause: 0.6]
I: Now the in-process lifetime means a takedown takes up to a minute longer. And a whole region's servers restart together.
[pause: 2.0]

[slide: v-093]
[pause: 0.6]
C: The lifetime is a line in the takedown budget, and the invalidation channel drops entries early anyway. That's challenge five. Restarts roll, never a whole region at once, and a starting server warms its cache from the last hour's top codes before it takes traffic.
C: The honest limit: for a link that is viral across the world, the real answer is the edge, close to every user. Which raises the next question.
[pause: 0.8]

[slide: v-094]
[pause: 0.7]
V: If asked, I'd say: a viral link is a hot key, not a load problem. I answer it from memory on every redirect server and coalesce misses, so each server sends one query, whatever the click rate. The cost is a short staleness window, which I count in the takedown budget.
[pause: 1.0]
N: That fix creates the next question: should the answer live even closer to the user?
[pause: 1.6]

[pause: 1.4]

## 7.4 Challenge 4: 301 or 302?

[slide: v-095]
[pause: 1.2]
N: Challenge four. Permanent or temporary redirect: what does each one cost the product, not just the servers?
[pause: 1.8]

[slide: v-096]
[pause: 0.6]
I: Should the redirect be a three-oh-one or a three-oh-two?
[pause: 2.0]

[slide: v-097]
[pause: 1.3]
C: The naive answer: three-oh-one, it's permanent and it saves servers. It does save servers. Look at the red browser. A three-oh-one tells it to remember the answer, and it does, indefinitely. It never asks us again.
[pause: 1.1]

[slide: v-098]
[pause: 1.0]
C: The trace. Monday a user clicks; we answer three-oh-one; the browser caches it. Tuesday the same user clicks again: the browser answers, we never see it, it's not counted. At three, the link is blocked for phishing. At three-twenty, that user's browser still goes straight to the phishing page.
C: Two losses: the owner loses the count, and we lose the ability to protect the user.
[pause: 1.0]

[slide: v-099]
[pause: 1.3]
C: The fix: three-oh-two by default, with browser caching off, and the edge allowed to keep it for sixty seconds, purgeable. Three-oh-one only as an owner's opt-in, for links that are permanent and that they accept will not be counted.
C: The property: counting and takedowns stay at layers we can reach. And the edge gives us most of the saving a three-oh-one would, at a bounded cost in freshness.
[pause: 1.1]

[slide: v-100]
[pause: 1.0]
C: The layers. The browser with a three-oh-one: zero milliseconds, never sees the click again, cannot be taken back. The edge with a three-oh-two cached for sixty seconds: a few milliseconds near the user, clicks from edge logs, minutes late, purgeable. Our servers and caches: a millisecond, every click, recallable. The store: the truth, for misses only.
[pause: 1.0]

[slide: v-101]
[pause: 0.6]
I: Finance says the edge bill for ten billion requests is too high. Or the counts from edge logs arrive twenty minutes late.
[pause: 2.0]

[slide: v-102]
[pause: 0.6]
C: The edge bill: compare the per-request cost with the servers and cross-region traffic it saves, and turn edge caching on per link, by click rate. Only hot links need it, and they are two percent of links.
C: Late counts are the stated lag, shown as as-of. When clicks are billed, the count must come from our servers, or a signed function running at the edge, not from logs. That is challenge six.
[pause: 0.8]

[slide: v-103]
[pause: 0.7]
V: If asked, I'd say: three-oh-one against three-oh-two is a product decision, not an optimisation. A three-oh-one is answered by the browser forever, so we lose the click and the ability to take a link down. I default to three-oh-two, let the edge cache it for a minute, and offer three-oh-one only to owners who want a permanent, uncounted link.
[pause: 1.0]
N: That fix creates the next question: we now hold copies at four layers. Can we withdraw all of them in five minutes?
[pause: 1.6]

[pause: 1.4]

## 7.5 Challenge 5: Dead everywhere in five minutes

[slide: v-104]
[pause: 1.2]
N: Challenge five. A phishing link is reported: how do we prove it stops working at every layer within five minutes, even when a message is lost?
[pause: 1.8]

[slide: v-105]
[pause: 0.6]
I: Legal reports a phishing link. It must stop working everywhere within five minutes. Show me.
[pause: 2.0]

[slide: v-106]
[pause: 1.3]
C: The naive answer: delete the row. Look at the red boxes. The edge, every redirect server's memory, the shared cache. None of them reads the row on a hit. Deleting the row changes the truth and nothing that answers.
[pause: 1.1]

[slide: v-107]
[pause: 1.0]
C: The trace. At three o'clock the status is set. Still answering: the shared cache with an hour's lifetime, forty servers' memory with sixty seconds, the edge in thirty cities with sixty seconds, and browsers that got a three-oh-one last week, forever. At three-twenty a victim still lands on the page, served from the shared cache.
C: So the real question is not how to delete. It is: what is the longest any copy can live after we decide?
[pause: 1.0]

[slide: v-108]
[pause: 1.3]
C: The fix, in the green boxes. The takedown writes blocked to the store. It deletes the shared-cache key directly and retries until it's confirmed: that cache has a long lifetime, so it must never depend on a lost message. It publishes an invalidation: every redirect server drops the code, and the edge is purged. The next request reads blocked and answers four-ten with a warning page.
C: The property is S-two, and it holds by arithmetic. Here is the arithmetic.
[pause: 1.1]

[slide: v-109]
[pause: 1.3]
C: The worst case, if the invalidation event is lost. Status and the shared-cache delete: a couple of seconds. The in-process lifetime: sixty. The edge lifetime: sixty. The purge call: a few. About two minutes, against five. The spare covers a slow purge and a retry. Every lifetime in this system was chosen with this bar in view.
[pause: 1.1]

[slide: v-110]
[pause: 1.3]
C: As a sequence once more, with the point that matters: the shared cache is deleted directly, not by the event, and only the short-lived layers depend on the event. If it is lost, their lifetimes end the copies. Four-ten Gone tells crawlers to stop asking.
[pause: 1.1]

[slide: v-111]
[pause: 0.6]
C: Two cheaper defences. On create, check the U-R-L against the classifier: if it's known-bad, no code is issued. And when the classifier's list updates, rescan recently created live links and block any matches through the same path. Every takedown is audited: who, why, when, and when each layer started answering four-ten.
[pause: 0.8]

[slide: v-112]
[pause: 0.6]
I: The invalidation event is lost. Or the link was created as a three-oh-one.
[pause: 2.0]

[slide: v-113]
[pause: 0.6]
C: A lost event: the lifetimes are the backstop, by design, so the worst case is about two minutes. And an hourly test takedown measures the real time at every layer, which is challenge eight.
C: A three-oh-one is the honest limit. It cannot be recalled from a browser, ever. That's why it's opt-in, and why the safety check runs before a three-oh-one link is issued.
[pause: 0.8]

[slide: v-114]
[pause: 0.7]
V: If asked, I'd say: every copy of the answer is a liability. A takedown writes the status, deletes the shared-cache key directly, sends an invalidation and purges the edge. The lifetime at every layer is chosen so that even with a lost message, the worst case is inside five minutes. A three-oh-one can't be recalled, which is one more reason it isn't the default.
[pause: 1.0]
N: The redirect is fast and withdrawable. Next: how do we count it without slowing it down?
[pause: 1.6]

[pause: 1.4]

## 7.6 Challenge 6: Counting without slowing the redirect

[slide: v-115]
[pause: 1.2]
N: Challenge six. Owners want clicks by day and country: where does the count happen, and what changes when every click is money?
[pause: 1.8]

[slide: v-116]
[pause: 0.6]
I: How do you count clicks per link, per country, without touching the redirect latency?
[pause: 2.0]

[slide: v-117]
[pause: 1.3]
C: The naive answer: increment a clicks column on every redirect. Look at the red store. That puts a write inside the redirect, on the row of the hottest link.
[pause: 1.1]

[slide: v-118]
[pause: 1.0]
C: The trace. Forty thousand updates a second on one row. The row lock serialises them. Each redirect waits for its write, and p ninety-nine goes from five milliseconds to nine hundred. The cache had solved the read. The counter put the hot key straight back on the critical path.
[pause: 1.0]

[slide: v-119]
[pause: 1.3]
C: The fix, green along the bottom. After the three-oh-two goes out, the server appends an event to a local buffer. The buffer flushes a batch every second into a log partitioned by code. An aggregator counts per code per minute, then per day per country. If the buffer is full, events are dropped, and the drops are counted.
C: L-two: nothing after the answer can delay it. L-three, with a measured loss: the drop counter is the loss, and counts say as-of.
[pause: 1.1]

[slide: v-120]
[pause: 1.0]
C: Precision about what the count promises. Today: at-most-once from the server, a crash loses the unflushed second, drops are counted and shown, bots are counted, and counts are minutes late.
C: If clicks are billed: at-least-once with a durable buffer, an event I-D created at the redirect, de-duplication in the aggregator, so the effect is exactly once, and bots filtered before anything is billed. The redirect still never waits.
[pause: 1.0]

[slide: v-121]
[pause: 0.6]
I: Product now bills per click. A lost click is lost money, and a double-counted one is a refund.
[pause: 2.0]

[slide: v-122]
[pause: 1.3]
C: The second fix, as a sequence. The three-oh-two is already sent. The server appends the event, with an I-D, to a buffer on local disk. It flushes a batch every second and trims the buffer only on acknowledgement. Delivery to the aggregator is at least once, and the aggregator de-duplicates by event I-D, filters bots, and counts.
C: The honest limit: a server's disk lost with an unflushed buffer loses up to a second of that server's clicks. That bound goes into the billing terms.
[pause: 1.1]

[slide: v-123]
[pause: 0.7]
V: If asked, I'd say: the click is recorded after the answer, never before it. Events go to a local buffer and a log, and an aggregator counts per minute. Today that's lossy by choice and we measure the loss. If clicks are billed, I add event I-Ds, a durable buffer and de-duplication, and the redirect still doesn't wait.
[pause: 1.0]
N: Every path now depends on the store being somewhere. What if that somewhere is gone?
[pause: 1.6]

[pause: 1.4]

## 7.7 Challenge 7: A region goes dark

[slide: v-124]
[pause: 1.2]
N: Challenge seven. The region holding the store's primary disappears: what keeps working, and what may stop?
[pause: 1.8]

[slide: v-125]
[pause: 0.6]
I: The region holding your link store's primary goes down. What still works?
[pause: 2.0]

[slide: v-126]
[pause: 1.3]
C: The naive answer: fail over the database. That's part of it, but look at what is red: the store's primary and the allocator's leader both lived in the lost region. Fail-over takes time, and during it, creates fail and every miss goes somewhere.
[pause: 1.1]

[slide: v-127]
[pause: 1.0]
C: The trace. At ten past three the primary region is lost. Redirects elsewhere: ninety-eight percent from caches, two percent miss to a store that is now read-only, which is fine for reads, if the reads are local. Creates fail, because the primary and the allocator's leader are gone. Bulk integrators retry with their idempotency keys.
[pause: 1.0]

[slide: v-128]
[pause: 1.3]
C: The fix. Redirects are regional: each region has a replica of the link store and its own caches, so a redirect never crosses a region. Creates are regional too: each region leases ranges from its own slice of the I-D space, Europe the first third, the Americas the second, Asia the last. A region can create without the others, and the store replicates asynchronously.
C: L-two depends only on regional state. S-one holds because the slices are disjoint: no two regions can ever produce the same I-D.
[pause: 1.1]

[slide: v-129]
[pause: 1.3]
C: On the baseline: the replica beside the link store, receiving asynchronous replication, and the shared cache reading from the local copy. Fail-over of a shard's primary is now only for writes to links created in the lost region, and those are rare: links are written once.
[pause: 1.1]

[slide: v-130]
[pause: 0.6]
I: A link created in Asia is clicked in Europe two hundred milliseconds later, before replication.
[pause: 2.0]

[slide: v-131]
[pause: 1.3]
C: The second fix, as a sequence. A code created in Asia two hundred milliseconds ago is clicked in Europe. Local miss. The code's slice of the I-D space says which region created it: Asia. One cross-region lookup, cache the answer here, and three-oh-two. One round trip slower, no error.
C: The honest limit: a region lost with unreplicated creates loses those links' last seconds. A creator who retries with the same idempotency key gets the same code back once the region returns.
[pause: 1.1]

[slide: v-132]
[pause: 0.7]
V: If asked, I'd say: redirects never leave their region. Replicas and caches answer them even with the primary gone. Creates are regional, because each region owns a slice of the I-D space. The one gap is a brand-new link clicked elsewhere before it replicates, and that costs one cross-region lookup, not an error.
[pause: 1.0]
N: Last challenge. All of this can fail silently. How would we know?
[pause: 1.6]

[pause: 1.4]

## 7.8 Challenge 8: How would you know it is broken?

[slide: v-133]
[pause: 1.2]
N: Challenge eight. The dashboards are green: how do we know the redirect a user gets is actually working, in every region?
[pause: 1.8]

[slide: v-134]
[pause: 0.6]
I: Your dashboards are green. How do you know redirects are actually working?
[pause: 2.0]

[slide: v-135]
[pause: 1.3]
C: The naive answer: error rate and C-P-U. Those watch boxes. The red one here is the shared cache, and nothing about it will show as an error.
[pause: 1.1]

[slide: v-136]
[pause: 1.0]
C: The trace. Just before two in the morning, a config change sets the shared cache's lifetime to zero. No errors. Median unchanged. p ninety-nine creeps from six milliseconds to eighteen, still under target. Store reads go from forty a second to four thousand. Nobody is watching, and at nine, when the peak arrives, the store saturates and the first page fires. Seven hours late.
[pause: 1.0]

[slide: v-137]
[pause: 1.3]
C: The fix. Synthetic probes in every region create a link and follow it through the edge, every minute: redirect latency, success, and the time from create to first redirect. And every hour, a test link is blocked and timed until every layer answers four-ten. That's our takedown time, measured, not hoped for.
[pause: 1.1]

[slide: v-138]
[pause: 1.0]
C: Symptom pairs: two metrics, one cause. Hit rate down with store reads up and traffic flat: a cold or misconfigured cache, not more users. That's this trace, caught at two, not nine.
C: Four-oh-fours up while creates are flat: someone is scanning codes. p ninety-nine up while hit rate is flat: something synchronous crept onto the redirect path. Click drops up with buffers full: the log is slow, not the redirect. Takedown time up with invalidation lag: the channel is behind, and the lifetimes are carrying us.
[pause: 1.0]

[slide: v-139]
[pause: 1.3]
C: The probe as a sequence. Create a test link. Follow it through the edge: three-oh-two in six milliseconds, create to first redirect in under half a second. Hourly, block a test link and poll every layer until four-ten. Today, seventy-four seconds, against five minutes.
[pause: 1.1]

[slide: v-140]
[pause: 0.6]
I: The probes pass, but one country's D-N-S sends users to the wrong region.
[pause: 2.0]

[slide: v-141]
[pause: 0.6]
C: The probes prove the path works. They don't prove users reach the right path. So add real-user monitoring from edge logs, per country: latency and which region answered. When probes are healthy and one country is slow, that divergence is the alert, and it says routing, not our servers.
[pause: 0.8]

[slide: v-142]
[pause: 0.7]
V: If asked, I'd say: I measure the path, not the boxes. Probes create a link and follow it in every region, and a test takedown every hour is timed until every layer answers four-ten. Then pairs of metrics give me causes: hit rate down with store reads up means a cold cache, not more traffic.
[pause: 1.6]

[pause: 1.4]

## 8 Build cost

[slide: v-143]
[pause: 1.2]
C: Build cost. This is the manager layer, marked aux: skip it in a pure Staff round, use it in a manager round.
[pause: 1.8]

[slide: v-144]
[pause: 1.0]
C: Three releases. Version one, one service and one table with random codes and a cache: two engineers, six weeks. Version two, split paths, ranges, the permutation and a sharded store: two more engineers, two months. Version three, the in-process cache, the click pipeline, the takedown channel, the edge and regions: a team of five or six for two quarters, with a twenty-four-seven rotation.
[pause: 1.0]

[slide: v-145]
[pause: 0.6]
C: If asked to split it across two teams for a quarter: links and redirect, owning create, codes, store, caches and the edge, and the redirect objective. And clicks and trust, owning the event pipeline, stats, the takedown service and the classifier. The contract between them is two things: the click event schema, and the invalidation channel.
[pause: 0.8]

[slide: v-146]
[pause: 1.0]
C: Buy, build, or don't. The store, the cache and the log are bought, managed. The edge is bought. The classifier is bought or an internal service. What we build is small: code generation, the redirect and the takedown path. And if shortening is not the business, the right answer may be: don't build it, use an off-the-shelf shortener. Say it.
[pause: 1.0]

[slide: v-147]
[pause: 0.6]
C: Cost, illustrative. A handful of redirect servers, a hundred gigabytes of cache memory, eighteen terabytes of storage. The edge is billed per request, and at ten billion a month it's the largest line, which is why its default lifetime is a business decision.
C: Top risks. The code format is a one-way door: codes are printed on paper and live forever. Takedown time untested until a real incident. And analytics quietly becoming billing without the exactness work.
[pause: 0.8]

[pause: 1.4]

## 9 Recap

[slide: v-148]
[pause: 1.2]
C: To close: one picture, one sentence per path, the mistakes to avoid, and the thesis.
[pause: 1.8]

[slide: v-149]
[pause: 1.3]
C: The final picture. Create on top: a safety check, leased ranges, a permutation, an insert under the constraint. The redirect across the middle: edge, redirect service with its in-process cache, shared cache, link store, and a replica per region. Along the bottom: the click log, the aggregator and the stats, and the takedown with its invalidation channel. And probes in every region, following the path a user takes.
[pause: 1.1]

[slide: v-150]
[pause: 1.0]
C: Four paths, one sentence each. Create: check the U-R-L, lease, permute, insert under the constraint. Redirect: memory, then the shared cache, then the store; answer; then count. Count: buffer, log, aggregate, and say how fresh. Withdraw: status, a direct delete, invalidate, purge, and lifetimes that sum to under five minutes.
[pause: 1.0]

[slide: v-151]
[pause: 1.0]
C: Eight fixes, each with its property. Ranges and the constraint, for uniqueness. A keyed permutation, against enumeration. In-process caching with single flight, for the viral link. Three-oh-two by default, for counting and takedowns. Status, a direct delete and bounded lifetimes, for the five minutes. Counting after the answer. Regional replicas and I-D slices. And probes that measure the path.
[pause: 1.0]

[slide: v-152]
[pause: 0.6]
C: Nine mistakes. In the design: hash and truncate with no collision story. Six characters without the arithmetic. Check, then insert. A counter update on every click. Codes that are a counter in disguise.
C: In judgment: add a cache, with no plan for one hot key. Three-oh-one by default. Forgetting that every cached copy must be withdrawable. And no number on the takedown time.
[pause: 0.8]

[slide: v-153]
[pause: 0.7]
V: The redirect is the product, so it's one memory read, and nothing waits on anything else. Codes are unique because each server owns a block and the database has the last word, and unguessable because a key shuffles them. Everything else, counting, takedowns, the edge, lives beside the redirect, with a number on how late it may be.
[pause: 1.2]
C: Thank you. I'll stop there.
[pause: 1.6]
