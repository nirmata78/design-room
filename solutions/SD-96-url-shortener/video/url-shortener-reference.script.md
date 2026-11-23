# SD-96 URL shortener: reference solution (Staff L6/L7)

<!-- Video script for slide-video-kit/scripts/build_video.py. [slide: v-NNN] = frames/v-NNN.png; [reveal: v-NNN] = the next
     reveal step of the same slide. Generated from src/*.py: edit the sources, not this file. -->
<!-- voices: N=af_heart@0.92 I=bf_emma@0.95 C=am_michael@0.9 V=am_michael@0.84 -->
<!-- names: C=Candidate V=Candidate N=Coach I=Interviewer -->
<!-- say: URL=U-R-L URLs=U-R-Ls CDN=C-D-N CDNs=C-D-Ns TTL=T-T-L TTLs=T-T-Ls SLO=S-L-O SLOs=S-L-Os SLI=S-L-I SLIs=S-L-Is API=A-P-I APIs=A-P-Is RAM=ram TB=terabytes MB=megabytes GB=gigabytes KB=kilobytes HTTP=H-T-T-P HTTPS=H-T-T-P-S SQL=S-Q-L DNS=D-N-S ID=I-D IDs=I-Ds EM=E-M AUX=aux SRE=S-R-E RFC=R-F-C QR=Q-R UUID=U-U-I-D Redis=Reddis p99=P-ninety-nine p50=P-fifty base62=base-sixty-two 301=three-oh-one 302=three-oh-two 404=four-oh-four 410=four-ten 409=four-oh-nine 201=two-oh-one 422=four-twenty-two LRU=L-R-U etcd=et-see-dee PostgreSQL=postgres-Q-L ClickHouse=click-house ristretto=ris-tretto Feistel=Fy-stel Kubernetes=koo-ber-net-eez -->


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
N: Five axes. I'll fill them in one at a time.
[reveal: v-005]
[pause: 0.45]
N: Requirements. The weak answer is shorten and redirect, with no numbers. The strong one asks the read to write ratio, the lifetime, aliases, analytics and the takedown time first.
[reveal: v-006]
[pause: 0.45]
N: Correctness. Hashing and truncating, or checking and then inserting, is weak. The strong answer derives the code length and lets a key constraint decide a collision.
[reveal: v-007]
[pause: 0.45]
N: Trade-offs. Use a cache and a NoSQL store is a slogan. The strong answer names a technology, names what it rejected, and says why.
[reveal: v-008]
[pause: 0.45]
N: Depth: what one viral key does to one cache shard. And operations: probes and pairs of metrics, not C-P-U.
[reveal: v-009]
[pause: 0.45]
C: And one rule I'll keep for the whole round: the redirect is the product. Everything else stands beside it, never in front of it.
[pause: 1.0]

[slide: v-010]
[pause: 0.7]
V: A U-R-L shortener is a read path with a write path attached. Make codes unique without a lock per create, and unguessable without a lookup. Keep the redirect to one memory read. And let nothing, not counting, not abuse, not analytics, stand between the click and the answer.
[pause: 1.6]

[slide: v-011]
[pause: 0.6]
C: The order.
[reveal: v-012]
[pause: 0.45]
C: First, requirements and scope, with the system in its context. Numbers. And a theory chapter where each mechanism is shown at work.
[reveal: v-013]
[pause: 0.45]
C: Then the A-P-I and the data, a design in three versions, the container view, every flow as a sequence, and every component one level deep, with the technology I would use and the ones I would not.
[reveal: v-014]
[pause: 0.45]
C: Then most of the time goes to eight challenges that break it, where each fix creates the next question. A build cost, and a recap.
[pause: 0.8]

[pause: 1.4]

## 1 Requirements and scope

[slide: v-015]
[pause: 1.2]
C: Six questions before I draw anything. Each answer moves the design.
[pause: 1.8]

[slide: v-016]
[pause: 0.6]
C: How many links, and how many clicks?
[reveal: v-017]
[pause: 0.45]
I: A hundred million new links a month. Ten billion redirects a month. And a viral link can take forty thousand clicks a second.
C: A hundred to one, reads to writes. And the peak is not many keys, it is one key. That last number will get its own challenge.
[pause: 0.6]

[slide: v-018]
[pause: 0.6]
C: How long does a link live?
[reveal: v-019]
[pause: 0.45]
I: Forever by default. The creator can set an optional expiry date.
C: Forever means the code space has to last for years, so I'll size it over ten. And printed links never go away, which makes the code format a one-way door.
[pause: 0.6]

[slide: v-020]
[pause: 0.6]
C: Can users choose their own alias?
[reveal: v-021]
[pause: 0.45]
I: Yes, paying users can. First come, first served.
C: First come, first served is a uniqueness race between two customers. Somebody has to decide who was first, and it should not be my application code.
[pause: 0.6]

[slide: v-022]
[pause: 0.6]
C: What do owners see about their clicks?
[reveal: v-023]
[pause: 0.45]
I: Clicks per link, by day and by country, in a dashboard. Not billed today. Product may want to bill per click later.
C: Not billed means I may lose a tiny fraction and say so. Billed later means that decision is not permanent. Challenge six.
[pause: 0.6]

[slide: v-024]
[pause: 0.6]
C: What about abuse?
[reveal: v-025]
[pause: 0.45]
I: Phishing and malware links exist. Legal wants a reported link dead everywhere within five minutes.
C: Everywhere is the hard word. Every cache that holds the answer is a copy I have to reach. Challenge five.
[pause: 0.6]

[slide: v-026]
[pause: 0.6]
C: Who calls the service?
[reveal: v-027]
[pause: 0.45]
I: Browsers following links. And integrators who create links in bulk through an A-P-I.
C: Bulk creators retry, so create must be idempotent, and they need a rate limit per key. Two lines on the A-P-I slide.
[pause: 0.6]

[slide: v-028]
[pause: 0.6]
C: Four functional requirements.
[reveal: v-029]
[pause: 0.45]
C: One, create: a long U-R-L in, a short link out, with an optional alias and expiry, and a retried request gets the same answer.
[reveal: v-030]
[pause: 0.45]
C: Two, redirect: a code gets the long U-R-L, or a not-found or gone page.
[reveal: v-031]
[pause: 0.45]
C: Three, count: clicks per link per day per country, within minutes.
[reveal: v-032]
[pause: 0.45]
C: Four, withdraw: the owner deletes, or trust and safety blocks, and it stops working everywhere within five minutes. Each of these gets a numbered flow and a sequence later.
[pause: 0.8]

[slide: v-033]
[pause: 0.6]
C: The numbers, and they are initial targets, not measurements.
[reveal: v-034]
[pause: 0.45]
C: A redirect under twenty milliseconds at the ninety-ninth percentile, measured at the server.
[reveal: v-035]
[pause: 0.45]
C: Four nines of redirect availability.
[reveal: v-036]
[pause: 0.45]
C: Create under two hundred milliseconds, three nines, because creating is less urgent than following.
[reveal: v-037]
[pause: 0.45]
C: A takedown effective everywhere within five minutes.
[reveal: v-038]
[pause: 0.45]
C: And counts may lag by minutes and may lose a tiny, measured fraction, until clicks are billed.
[pause: 0.8]

[slide: v-039]
[pause: 0.6]
C: In scope: create, redirect, aliases, expiry, counts, takedowns, and a bulk A-P-I with a rate limit per key.
[reveal: v-040]
[pause: 0.45]
C: Out, on purpose. The malware classifier itself: I call it, I don't build it. Accounts and billing. Q-R codes, which are just a picture of the same link. Link-in-bio pages.
[reveal: v-041]
[pause: 0.45]
C: And editing a link's target, which I'd say aloud: for every cache, an edit is a takedown plus a create, so it rides on challenge five.
[pause: 0.8]

[slide: v-042]
[pause: 1.3]
C: Before any boxes inside it, the system in its context. This is C-four level one: people and other systems, nothing internal.
[reveal: v-043]
[pause: 0.45]
C: First, visitors. They follow a short link from anywhere, an email, a printed flyer, a chat, and they get a three-oh-two. This is ninety-nine percent of the traffic.
[reveal: v-044]
[pause: 0.45]
C: In the middle, the shortener, one box for now: codes, redirects, counts and takedowns.
[reveal: v-045]
[pause: 0.45]
C: Link owners create links through the A-P-I, alone or in bulk, and read their click statistics.
[reveal: v-046]
[pause: 0.45]
C: Trust and safety block phishing and malware links, through a console or an A-P-I. Their five-minute bar is a requirement on everything inside the box.
[reveal: v-047]
[pause: 0.45]
C: And one external system: a U-R-L classifier we call on create, to ask whether a U-R-L is known-bad. Notice what is not on this picture: nothing external sits on the redirect path. That is a decision, and I'll defend it.
[pause: 1.1]

[slide: v-048]
[pause: 0.7]
V: The core is three things. A code generator that never collides. A redirect path that is one memory read. And a side path for counting and withdrawal that never sits in front of the redirect.
[pause: 0.8]
N: Notice the candidate named the core and drew the context before any internals. That is the scoping signal.
[pause: 1.6]

[pause: 1.4]

## 2 Estimates

[slide: v-049]
[pause: 1.2]
C: Numbers next, each as arithmetic, each with the decision it drives. I'll label them: given, derived or illustrative.
[pause: 1.8]

[slide: v-050]
[pause: 1.0]
C: Traffic, three rows.
[reveal: v-051]
[pause: 0.45]
C: A hundred million creates a month, divided by about two point six million seconds, is about forty a second, and say ten times that at peak: four hundred. That is nothing. One database could take it. So the hard part of create is uniqueness, not throughput.
[reveal: v-052]
[pause: 0.45]
C: Ten billion redirects a month is about four thousand a second. Reads to writes, a hundred to one.
[reveal: v-053]
[pause: 0.45]
C: And the peak the interviewer gave me is forty thousand a second on one code. The peak is one key, which is a very different problem from a big fleet.
[pause: 1.0]

[slide: v-054]
[pause: 1.3]
C: How long must a code be? A hundred million a month, times twelve, times ten years, is one point two times ten to the ten links. The alphabet is sixty-two symbols: lower case, upper case and digits.
C: Six characters give sixty-two to the sixth, about five point seven times ten to the ten. Only four point seven times the links I need, and random codes would collide long before that. Seven characters give three point five times ten to the twelve, about two hundred and ninety times. Seven it is.
C: And with random codes, at the end of year ten, a new code hits an existing one with probability links over space: about a third of a percent. Small enough that a retry on conflict is fine.
[pause: 1.1]

[slide: v-055]
[pause: 1.0]
C: Storage and memory.
[reveal: v-056]
[pause: 0.45]
C: One point two times ten to the ten links at about five hundred bytes each, with the U-R-L, the owner, dates and index overhead, is six terabytes, eighteen with three replicas. Not the hard part.
[reveal: v-057]
[pause: 0.45]
C: The hot set. If two percent of links take ninety percent of clicks, that's two hundred million links, about a hundred gigabytes. A few cache nodes. This number is illustrative, and the first thing I'd measure.
[reveal: v-058]
[pause: 0.45]
C: So the store sees misses only: four thousand a second times a one percent miss rate is forty a second. Except when the cache is cold, after a restart, when it can see all four thousand. Keep that for challenge three.
[pause: 1.0]

[slide: v-059]
[pause: 1.0]
C: Three small numbers that shape the design.
[reveal: v-060]
[pause: 0.45]
C: If each create server leases a thousand I-Ds at a time, four hundred creates a second is less than one lease every two seconds. So the allocator can be a small, strongly consistent store.
[reveal: v-061]
[pause: 0.45]
C: Click events: four thousand a second, two hundred bytes each, under a megabyte a second, seventy gigabytes a day. A log and an aggregator, not a counter on the link row.
[reveal: v-062]
[pause: 0.45]
C: And one viral key at forty thousand a second lands on one cache shard. The shard can take it, but its queue and its tail become every viral click's tail.
[pause: 1.0]

[slide: v-063]
[pause: 1.3]
C: The latency budget at the server. A cache lookup, about a millisecond. On a miss, the link store, about five. Parsing, writing the response and emitting the click event, about one more. Seven milliseconds in the worst case with a miss, against twenty.
C: That spare is room for one miss. It is not room for a synchronous write of a click counter, or a call to a classifier on the redirect path. The budget says what may never be added.
[pause: 1.1]

[slide: v-064]
[pause: 0.6]
C: The takedown budget. Five minutes is not a hope, it is a sum.
[reveal: v-065]
[pause: 0.45]
C: The status write and the shared cache delete are done directly by the takedown, in seconds.
[reveal: v-066]
[pause: 0.45]
C: Each redirect server's in-process cache is dropped by an event, and if that event is lost, a sixty-second lifetime ends it.
[reveal: v-067]
[pause: 0.45]
C: The edge is purged by its A-P-I, and if that fails, a sixty-second cache time ends it.
[reveal: v-068]
[pause: 0.45]
C: The rule: every layer's lifetime fits inside five minutes, summed along the worst path. I'll come back to it with numbers in challenge five.
[pause: 0.8]

[pause: 1.4]

## 3 Theory

[slide: v-069]
[pause: 1.2]
C: A theory chapter before the design, so the design can lean on it. What a shortener is and is not, the properties, the central tension, six mechanisms, then three pictures of those mechanisms at work, an options matrix, and the failure catalogue.
[pause: 1.8]

[slide: v-070]
[pause: 0.7]
V: A U-R-L shortener maps a short, unique, hard-to-guess code to a long U-R-L, answers a redirect for that code in milliseconds from anywhere, and can withdraw a code everywhere within a stated time.
[pause: 1.0]
C: Every clause is load-bearing. Unique: and the store, not the application, decides. Hard to guess: a code is not a secret, but it must not be walkable. In milliseconds from anywhere: the redirect is the product. Withdrawn everywhere within a stated time: every cached copy is a liability.
[pause: 1.6]

[slide: v-071]
[pause: 0.6]
C: Four neighbours it is confused with.
[reveal: v-072]
[pause: 0.45]
C: It is not a hash function: hashing the U-R-L is one way to get a key, and once you truncate it, it is not unique.
[reveal: v-073]
[pause: 0.45]
C: It is not a cache: the map is the truth, and a cache is a copy allowed to be wrong for a bounded time.
[reveal: v-074]
[pause: 0.45]
C: It is not a secret: seven characters can be sampled, so private content needs authentication, not a short code.
[reveal: v-075]
[pause: 0.45]
C: And it is not a C-D-N: the edge is a layer that answers for us, and one we must be able to take back.
[pause: 0.8]

[slide: v-076]
[pause: 0.6]
V: Safety: two different long U-R-Ls never get the same code, and a withdrawn code is never answered by any layer after the takedown bound.
[pause: 0.6]
[reveal: v-077]
[pause: 0.45]
V: Liveness: a create never waits for another create, a live code always redirects within the target, and every click is eventually counted, with a stated loss.
[pause: 0.8]
C: S-one is the collision. S-two is the phishing link that will not die. L-two is the viral peak. Every fix from here names which one it serves.
[pause: 0.8]

[slide: v-078]
[pause: 1.3]
C: The central tension. On the left, the browser: with a permanent redirect it answers in zero milliseconds, forever, and we never see that click again. Then the edge: fast and cheap, counted from logs, purgeable. Then our servers and caches: a millisecond, every click seen, recallable. Then the store: the truth, for misses only.
C: Every layer closer to the user makes the redirect faster and cheaper, and counting and takedown harder or impossible. Three-oh-one against three-oh-two is the choice of where on this line the answer lives. That is a product decision, and challenge four.
[pause: 1.1]

[slide: v-079]
[pause: 0.6]
C: Mechanism one, counter ranges. It protects S-one and L-one.
[reveal: v-080]
[pause: 0.45]
C: Each create server leases a block of a thousand I-Ds from an allocator in one conditional write, then hands them out from memory and encodes each in base sixty-two.
[reveal: v-081]
[pause: 0.45]
C: It rules out two servers handing out the same code, and a round trip on every create.
[reveal: v-082]
[pause: 0.45]
C: It costs gaps when a server dies holding a range, which is harmless with two hundred and ninety times headroom. And on its own it makes codes sequential.
[pause: 0.8]

[slide: v-083]
[pause: 0.6]
C: Mechanism two, a keyed permutation. It protects against enumeration.
[reveal: v-084]
[pause: 0.45]
C: A small Feistel network over the code space with a secret key, plus cycle walking to stay below sixty-two to the seventh. It is a bijection: different inputs always give different outputs, so uniqueness is untouched.
[reveal: v-085]
[pause: 0.45]
C: It rules out scrapers walking codes in order, and codes that leak our volume.
[reveal: v-086]
[pause: 0.45]
C: It costs a key to keep and rotate, and it is not secrecy.
[pause: 0.8]

[slide: v-087]
[pause: 0.6]
C: Mechanism three, the unique constraint as the final authority. It protects S-one where codes can collide: custom aliases, or random codes.
[reveal: v-088]
[pause: 0.45]
C: Insert with a unique key; the one shard that owns that code accepts one insert and rejects the other.
[reveal: v-089]
[pause: 0.45]
C: It rules out the check-then-insert race.
[reveal: v-090]
[pause: 0.45]
C: It costs a conflict answer, four-oh-nine, and a retry loop for random codes.
[pause: 0.8]

[slide: v-091]
[pause: 0.6]
C: Mechanism four, layered caching with single flight. It protects L-two, the redirect under load.
[reveal: v-092]
[pause: 0.45]
C: A shared cache in front of the store, a small in-process cache on every redirect server, and concurrent misses for one code waiting on a single lookup.
[reveal: v-093]
[pause: 0.45]
C: It rules out a miss storm on one key, and every viral click paying a network hop.
[reveal: v-094]
[pause: 0.45]
C: It costs bounded staleness at each layer, which the takedown budget has to absorb, and memory on every server.
[pause: 0.8]

[slide: v-095]
[pause: 0.6]
C: Mechanism five, the asynchronous click log. It protects L-two and L-three.
[reveal: v-096]
[pause: 0.45]
C: The redirect answers first, then appends a click event to a local buffer, which flushes batches to a log partitioned by code, and an aggregator counts per minute.
[reveal: v-097]
[pause: 0.45]
C: It rules out a counter update on the hot path and a hot row per viral link.
[reveal: v-098]
[pause: 0.45]
C: It costs minutes of lag and a small stated loss, or a durable buffer if clicks are ever billed.
[pause: 0.8]

[slide: v-099]
[pause: 0.6]
C: Mechanism six, status, invalidation and bounded lifetimes. It protects S-two.
[reveal: v-100]
[pause: 0.45]
C: A status in the store, an invalidation event to every cache, a purge at the edge, and a maximum lifetime at every layer, chosen so that even when a message is lost, the sum fits the bound.
[reveal: v-101]
[pause: 0.45]
C: It rules out a blocked phishing link still being answered somewhere.
[reveal: v-102]
[pause: 0.45]
C: It costs hit rate, a purge path, and the three-oh-two.
[pause: 0.8]

[slide: v-103]
[pause: 1.3]
C: Before any design decision, where these six mechanisms will live. This is the container view I'll build in chapter five, labelled by mechanism instead of by technology.
[reveal: v-104]
[pause: 0.45]
C: Visitors come in through the edge, which carries mechanism six as a bounded lifetime: sixty seconds, purgeable. The classifier stays outside.
[reveal: v-105]
[pause: 0.45]
C: The create service carries mechanisms one and two: it hands out I-Ds from leased ranges and permutes them.
[reveal: v-106]
[pause: 0.45]
C: The range allocator is the consensus part of mechanism one: one conditional write per thousand I-Ds.
[reveal: v-107]
[pause: 0.45]
C: The link store carries mechanism three. Its unique key on the code is the final authority.
[reveal: v-108]
[pause: 0.45]
C: The redirect service carries mechanism four, the layered cache, and the start of mechanism five: the click is recorded after the answer.
[reveal: v-109]
[pause: 0.45]
C: The shared cache is mechanism four, and mechanism six touches it too: a takedown deletes its key directly.
[reveal: v-110]
[pause: 0.45]
C: The click pipeline is mechanism five.
[reveal: v-111]
[pause: 0.45]
C: And the takedown service is mechanism six: status, events, purge. Two of the six mechanisms sit on the redirect path; four sit beside it. That ratio is the thesis.
[pause: 1.1]

[slide: v-112]
[pause: 1.3]
C: Mechanism one at work, at the level of the consensus protocol. The allocator is a three-node store that replicates a log with Raft. One node leads.
[reveal: v-113]
[pause: 0.45]
C: Server A sends one transaction: if the key next was last modified at revision seventeen, set it to forty-one thousand. A compare-and-set, keyed on the revision.
[reveal: v-114]
[pause: 0.45]
[reveal: v-115]
[pause: 0.45]
C: The leader appends the change as entry eighteen and sends it to both followers.
[reveal: v-116]
[pause: 0.45]
C: Follower one acknowledges.
[reveal: v-117]
[pause: 0.45]
C: Two of three now hold the entry: that is a majority, so it is committed. It will survive the loss of any one node, including the leader.
[reveal: v-118]
[pause: 0.45]
C: Only now does A hear: you own forty thousand to forty thousand nine hundred and ninety-nine.
[reveal: v-119]
[pause: 0.45]
C: Server B raced A with the same transaction, conditioned on revision seventeen.
[reveal: v-120]
[pause: 0.45]
C: It fails, because the revision is now eighteen. No lock was held; the condition did the work.
[reveal: v-121]
[pause: 0.45]
C: B reads again and its next transaction wins the following thousand. The guarantee needs only that the log is linearizable. It needs no clock and no timeout, unlike a lease that expires.
[pause: 1.1]

[slide: v-122]
[pause: 1.3]
C: Mechanisms four and six together, on one redirect server.
[reveal: v-123]
[pause: 0.45]
C: Three requests for the same code arrive at once.
[reveal: v-124]
[pause: 0.45]
C: The in-process cache misses. Single flight: the first request becomes the leader, the other two wait on its result instead of each doing the lookup.
[reveal: v-125]
[pause: 0.45]
C: The leader asks the shared cache.
[reveal: v-126]
[pause: 0.45]
C: Miss.
[reveal: v-127]
[pause: 0.45]
C: It reads the link store by primary key.
[reveal: v-128]
[pause: 0.45]
C: The U-R-L, and the status: live.
[reveal: v-129]
[pause: 0.45]
C: It fills the shared cache with an hour's lifetime and ten percent random jitter, so keys loaded together do not expire together.
[reveal: v-130]
[pause: 0.45]
C: All three requests get their three-oh-two from one lookup.
[reveal: v-131]
[pause: 0.45]
C: Later, a takedown sends an invalidation for this code, asynchronously.
[reveal: v-132]
[pause: 0.45]
C: The server drops it at once. If that message is lost, the sixty-second in-process lifetime ends the copy anyway. Mechanism six never trusts a message alone: every copy also has a maximum age.
[pause: 1.1]

[slide: v-133]
[pause: 1.0]
C: Six ways to make a code.
[reveal: v-134]
[pause: 0.45]
C: A, hash the U-R-L and keep seven characters: truncation collides, and the same U-R-L shortened by two owners wants two links, so you need a probe loop anyway.
[reveal: v-135]
[pause: 0.45]
C: B, random codes with a retry on conflict. Simple, and honest.
[reveal: v-136]
[pause: 0.45]
C: C, one global counter: a round trip per create, a single point of failure, and the codes are a counter anyone can read.
[reveal: v-137]
[pause: 0.45]
C: D, ranges plus a keyed permutation plus the constraint.
[reveal: v-138]
[pause: 0.45]
C: E, time-based I-Ds: unique without coordination, but ten or eleven characters, which is not short.
[reveal: v-139]
[pause: 0.45]
C: F, a pre-generated pool: works, but it's a second system to fill and monitor.
V: I pick D, and I say plainly that B is an honest equal.
[pause: 1.0]

[slide: v-140]
[pause: 0.6]
C: Why D. Generated codes never meet the constraint as a conflict, so there is no retry loop; the store's slowness never multiplies; and coordination happens once per thousand links.
[reveal: v-141]
[pause: 0.45]
C: What it gives up: an allocator to run and a key to manage. B needs neither.
[reveal: v-142]
[pause: 0.45]
C: So I'd say this in the room: if creates stay under a few thousand a second and seven characters are always fine, B is simpler and I'd pick it. At this scale, either is defensible. The reasoning is what is graded.
[pause: 0.8]

[slide: v-143]
[pause: 1.0]
C: The failure catalogue, which becomes the challenge list.
[reveal: v-144]
[pause: 0.45]
C: Two servers handing out one code.
[reveal: v-145]
[pause: 0.45]
C: Codes walked in order.
[reveal: v-146]
[pause: 0.45]
C: One viral code, and a cold cache.
[reveal: v-147]
[pause: 0.45]
C: A layer we cannot see or recall.
[reveal: v-148]
[pause: 0.45]
C: A phishing link still live.
[reveal: v-149]
[pause: 0.45]
C: Counting on the hot path.
[reveal: v-150]
[pause: 0.45]
C: A region lost.
[reveal: v-151]
[pause: 0.45]
C: And nobody noticing.
[reveal: v-152]
[pause: 0.45]
C: The ninth, a creator flooding the bulk A-P-I, is a rate limit per key. I'll put it on the A-P-I slide rather than spend a challenge on it.
[pause: 1.0]

[slide: v-153]
[pause: 1.0]
C: The vocabulary in one table.
[reveal: v-154]
[pause: 0.45]
C: Ranges: S-one and L-one, back in challenges one and seven.
[reveal: v-155]
[pause: 0.45]
C: The permutation: enumeration, challenge two.
[reveal: v-156]
[pause: 0.45]
C: The constraint: S-one, challenge one.
[reveal: v-157]
[pause: 0.45]
C: The layered cache: L-two, challenges three and four.
[reveal: v-158]
[pause: 0.45]
C: The click log: L-two and L-three, challenge six.
[reveal: v-159]
[pause: 0.45]
C: And status, invalidation and lifetimes: S-two, challenges four and five.
[reveal: v-160]
[pause: 0.45]
N: Good theory has a consequence for the design. Every mechanism here names the property it serves and where it comes back.
[pause: 1.0]

[pause: 1.4]

## 4 API and entities

[slide: v-161]
[pause: 1.2]
C: Four public calls, one internal. Each tagged with the requirement it serves and the data it reads or writes.
[pause: 1.8]

[slide: v-162]
[pause: 1.0]
C: The calls, one row at a time.
[reveal: v-163]
[pause: 0.45]
C: Create is a post with the long U-R-L, an optional alias and expiry, and an idempotency key, so a bulk integrator's retry gets the same code back. It answers two-oh-one, or four-oh-nine if the alias is taken, or four-twenty-two if the U-R-L is known-bad. Aliases must be eight characters or more, so they never collide with a generated seven-character code. Each key has a rate limit: that's failure nine.
[reveal: v-164]
[pause: 0.45]
C: The redirect is a get on the code: three-oh-two, four-oh-four, or four-ten Gone for a withdrawn code, so search crawlers stop asking.
[reveal: v-165]
[pause: 0.45]
C: Stats return counts by day and country with an as-of time, so the owner knows how fresh they are.
[reveal: v-166]
[pause: 0.45]
C: Delete and takedown write the status and emit an invalidation, with an audit row.
[reveal: v-167]
[pause: 0.45]
C: And internally, lease range hands a create server a thousand I-Ds.
[pause: 1.0]

[slide: v-168]
[pause: 1.0]
C: The redirect on the wire. A get on the code. The answer is a three-oh-two Found with a Location header. The cache headers are the design decision: private, max age zero for the browser, so it asks us again every time, which means we count the click and can withdraw the link. And sixty seconds for the edge, so a viral link is cheap.
[reveal: v-169]
[pause: 0.45]
C: The surrogate key tags every edge copy of this code, so one purge call finds them all. Both lifetimes are in the takedown budget. That is why the headers are on a slide.
[pause: 1.0]

[slide: v-170]
[pause: 1.3]
C: The conceptual model. An owner creates links. A link has one code and one long U-R-L, a status and an optional expiry. Clicks are weak entities: they only exist as clicks of a link, and they roll up into daily counts. A takedown withdraws a link. And range leases record which server holds which block of I-Ds.
C: One sentence on the bottom matters most: a code has exactly one live long U-R-L, but the same U-R-L may have many codes. So a hash of the U-R-L is not a key.
[pause: 1.1]

[slide: v-171]
[pause: 1.0]
C: The physical model.
[reveal: v-172]
[pause: 0.45]
C: The link table's primary key is the code, and it is sharded by code, because the code is the only key the redirect ever uses.
[reveal: v-173]
[pause: 0.45]
C: The owner's dashboard gets its own table, keyed by owner and time, never on the hot path.
[reveal: v-174]
[pause: 0.45]
C: The allocator holds one key per region: the next I-D, with its revision.
[reveal: v-175]
[pause: 0.45]
C: Daily counts are written by the aggregator.
[reveal: v-176]
[pause: 0.45]
C: And in each redirect server's memory: a map from code to U-R-L and status, a lifetime of thirty to sixty seconds, and an in-flight map for single flight.
[reveal: v-177]
[pause: 0.45]
C: A hash of the U-R-L is not a key, and a click never updates the link row.
[pause: 1.0]

[slide: v-178]
[pause: 0.6]
C: Two rules I'd defend in a review.
[reveal: v-179]
[pause: 0.45]
C: The code is the only hot key: shard by code, every redirect is one key lookup, and owner queries go to a second table written on create.
[reveal: v-180]
[pause: 0.45]
C: And no counter on the link row: a click never writes to it, because a viral link would make that row the hottest lock in the system.
[pause: 0.8]

[pause: 1.4]

## 5 High-level design

[slide: v-181]
[pause: 1.2]
C: The design in three versions, drawn on one baseline, each answering the objection to the one before. Then the container view, and every flow as a numbered picture and a sequence.
[pause: 1.8]

[slide: v-182]
[pause: 1.3]
C: Version one, drawn from the left, the way a request travels.
[reveal: v-183]
[pause: 0.45]
C: A browser, or an A-P-I client.
[reveal: v-184]
[pause: 0.45]
C: One service that does everything: it creates, and it redirects.
[reveal: v-185]
[pause: 0.45]
C: And one relational table from code to U-R-L. Create picks a random seven-character code and inserts it, retrying on a conflict. Redirect reads the table and answers three-oh-two.
C: It works, and at a thousand clicks a second it would be fine. Here is the objection: four thousand reads a second on one table, with a forty-thousand peak on one row. Analytics would be an update per click. And nothing scales out, because creating and redirecting are one process with one failure mode.
[pause: 1.1]

[slide: v-186]
[pause: 1.3]
C: Version two answers that objection. The two paths have different loads and different tolerances, so they become two services. What stays from version one is now the redirect service, stateless, many copies, in front of a link store that is now sharded by code.
[reveal: v-187]
[pause: 0.45]
C: New, in blue: a shared cache between them. Cache-aside: a miss reads the store and fills the cache.
[reveal: v-188]
[pause: 0.45]
C: New on top: the create service, a separate deployment with its own scaling and its own failure mode. It inserts with a unique constraint.
[reveal: v-189]
[pause: 0.45]
C: And the allocator it leases I-D ranges from.
C: The objection it leaves: one viral code is one hot cache key. Clicks still have nowhere to go. And a takedown sits behind every cache.
[pause: 1.1]

[slide: v-190]
[pause: 1.3]
C: Version three. Version two is carried as it is; I add seven boxes, in the order a request meets them.
[reveal: v-191]
[pause: 0.45]
C: First, an edge in front of the redirect, which may keep a three-oh-two for sixty seconds. Each redirect server also gets an in-process cache with single flight, inside its box.
[reveal: v-192]
[pause: 0.45]
C: On the create path, a safety check on the U-R-L before any code is issued.
[reveal: v-193]
[pause: 0.45]
C: Below the redirect, the click path. After the answer, the redirect server sends a click event into a click log.
[reveal: v-194]
[pause: 0.45]
C: An aggregator reads it in batches and counts per minute.
[reveal: v-195]
[pause: 0.45]
C: And writes counts into a stats store, by day and country.
[reveal: v-196]
[pause: 0.45]
C: Bottom left, the takedown service, which writes status blocked straight to the link store.
[reveal: v-197]
[pause: 0.45]
C: And publishes on an invalidation channel that reaches the edge, every redirect server and the shared cache.
C: The objection it leaves is the details. Those are the challenges.
[pause: 1.1]

[slide: v-198]
[pause: 1.3]
C: Now the same design in C-four, level two: containers. A container here means a separately deployed and separately scaled thing, a service or a data store. This is the picture the rest of the video hangs on, so I'll take it slowly, in the order a click travels.
[reveal: v-199]
[pause: 0.45]
C: The visitor, outside the boundary, opens a short link over H-T-T-P-S. The request does not come to us first.
[reveal: v-200]
[pause: 0.45]
C: It reaches the edge, a content delivery network that we buy. The edge may answer a hot code itself for up to sixty seconds. On a miss, it forwards the request. The edge is ours to configure and to purge, but not ours to run.
[reveal: v-201]
[pause: 0.45]
C: Next, the redirect service: stateless, many copies in every region, each with a small in-process cache and single flight. It owns the twenty-millisecond objective. Everything it needs to answer is in memory, one network hop away at most.
[reveal: v-202]
[pause: 0.45]
C: Behind it, the shared cache: an in-memory, sharded cache, read cache-aside. It holds the hot set, about a hundred gigabytes, so that a cold redirect server does not mean a cold store.
[reveal: v-203]
[pause: 0.45]
C: Then the link store: the truth. A sharded store keyed by code, with a unique constraint on the code. On the redirect path it sees only misses, about forty reads a second.
[reveal: v-204]
[pause: 0.45]
C: Above, the create service. It is not on the redirect path at all. It leases I-D ranges, permutes I-Ds into codes, and inserts under the constraint, writing straight to the link store.
[reveal: v-205]
[pause: 0.45]
C: The range allocator: a small consensus-backed store. Point four leases a second. It is the only place where create servers coordinate, and they do it once per thousand links.
[reveal: v-206]
[pause: 0.45]
C: To the right, outside the boundary, the U-R-L classifier we call on create. Bought, or another team's service.
[reveal: v-207]
[pause: 0.45]
C: Below the redirect service, the click pipeline: a log and an aggregator. Note the arrow: click events go asynchronously, after the answer.
[reveal: v-208]
[pause: 0.45]
C: And the takedown service, which writes status to the store and drives the invalidation of every copy.
C: Read it as a layout: the redirect path is four boxes in a row, left to right. Create is above it, counting and takedown are below it. Nothing crosses the row. That layout is the thesis, drawn.
[pause: 1.1]

[slide: v-209]
[pause: 1.0]
C: The three versions in one table.
[reveal: v-210]
[pause: 0.45]
C: Version one: one service, one table.
[reveal: v-211]
[pause: 0.45]
C: Version two: split the paths, cache the read, lease ranges.
[reveal: v-212]
[pause: 0.45]
C: Version three: protect the redirect and make every copy withdrawable. Each answers the objection to the one before.
[pause: 1.0]

[slide: v-213]
[pause: 1.3]
C: Flow one, create, on the baseline, with numbered arrows.
[reveal: v-214]
[pause: 0.45]
C: One: the client posts the long U-R-L with an idempotency key.
[reveal: v-215]
[pause: 0.45]
C: Two: the create service asks the safety check whether the U-R-L is known-bad.
[reveal: v-216]
[pause: 0.45]
C: Three: it takes the next I-D from its leased range, leasing a new one at half-used.
[reveal: v-217]
[pause: 0.45]
C: Four: it permutes the I-D, encodes it in base sixty-two, and inserts it with the unique constraint on the code. For a custom alias, the alias is the code, and the constraint decides who gets it. Then two-oh-one with the short U-R-L.
[pause: 1.1]

[slide: v-218]
[pause: 1.3]
C: The same flow as a sequence, message by message.
[reveal: v-219]
[pause: 0.45]
C: Post with an idempotency key.
[reveal: v-220]
[pause: 0.45]
C: Is this U-R-L known-bad?
[reveal: v-221]
[pause: 0.45]
C: No.
[reveal: v-222]
[pause: 0.45]
C: Locally, no network: next I-D from the range, keyed permutation, base sixty-two: a-Z-three-k-Q-nine-x.
[reveal: v-223]
[pause: 0.45]
C: Insert with the unique constraint.
[reveal: v-224]
[pause: 0.45]
C: Okay.
[reveal: v-225]
[pause: 0.45]
C: Two-oh-one with the short link. One write on the store, no lock across servers.
[pause: 1.1]

[slide: v-226]
[pause: 1.3]
C: Flow two, the redirect, the product.
[reveal: v-227]
[pause: 0.45]
C: One: the browser asks the edge for the code.
[reveal: v-228]
[pause: 0.45]
C: Two: on an edge miss, the request reaches a redirect server, which checks its in-process cache.
[reveal: v-229]
[pause: 0.45]
C: Three: on a miss, the shared cache.
[reveal: v-230]
[pause: 0.45]
C: Four: on a miss there too, the link store.
[reveal: v-231]
[pause: 0.45]
C: Five: the store's answer fills the shared cache.
[reveal: v-232]
[pause: 0.45]
C: Six: the U-R-L comes back to the redirect server, which checks the status and the expiry.
[reveal: v-233]
[pause: 0.45]
C: Seven: the three-oh-two goes back to the edge.
[reveal: v-234]
[pause: 0.45]
C: Eight: the edge returns it, and may keep it for sixty seconds. For a hot code, steps three to six never happen: the answer is in memory.
[pause: 1.1]

[slide: v-235]
[pause: 1.3]
C: As a sequence.
[reveal: v-236]
[pause: 0.45]
C: Get the code.
[reveal: v-237]
[pause: 0.45]
C: In-process miss.
[reveal: v-238]
[pause: 0.45]
C: Shared cache, about a millisecond.
[reveal: v-239]
[pause: 0.45]
C: Miss.
[reveal: v-240]
[pause: 0.45]
C: Select from the link store by primary key.
[reveal: v-241]
[pause: 0.45]
C: Live. Fill both caches.
[reveal: v-242]
[pause: 0.45]
C: Three-oh-two with the Location.
[reveal: v-243]
[pause: 0.45]
C: And only then, the click event to the log, fire and forget. Nothing after the answer can delay the answer.
[pause: 1.1]

[slide: v-244]
[pause: 1.3]
C: Flow three, counting.
[reveal: v-245]
[pause: 0.45]
C: One: the click arrives at the edge.
[reveal: v-246]
[pause: 0.45]
C: Two: the edge forwards it, as before.
[reveal: v-247]
[pause: 0.45]
C: Three: after answering, the redirect server appends a click event to a local buffer, which flushes a batch every second into the click log, partitioned by code.
[reveal: v-248]
[pause: 0.45]
C: Four: the aggregator reads batches and counts per code per minute, then per day per country.
[reveal: v-249]
[pause: 0.45]
C: Five: the counts land in the stats store. If the buffer is full, events are dropped and the drops are counted.
[pause: 1.1]

[slide: v-250]
[pause: 1.3]
C: Counting as a sequence, end to end.
[reveal: v-251]
[pause: 0.45]
C: The three-oh-two is already sent.
[reveal: v-252]
[pause: 0.45]
C: The server appends the code, the country and the minute to a local buffer.
[reveal: v-253]
[pause: 0.45]
C: The buffer pre-aggregates: per code and country, each second. A viral link becomes forty small counters a second, one per server, not forty thousand events.
[reveal: v-254]
[pause: 0.45]
C: Once a second, a batch goes to the click log, keyed by code.
[reveal: v-255]
[pause: 0.45]
C: The stream job consumes it.
[reveal: v-256]
[pause: 0.45]
C: It counts in one-minute windows of event time, and accepts data up to thirty seconds late.
[reveal: v-257]
[pause: 0.45]
C: It inserts counts by code, minute and country into the stats store.
[reveal: v-258]
[pause: 0.45]
C: The owner's dashboard asks for this code's counts by day.
[reveal: v-259]
[pause: 0.45]
C: And gets them with an as-of time: fourteen-oh-five. Fresh within minutes, and it says so.
[pause: 1.1]

[slide: v-260]
[pause: 1.3]
C: Flow four, withdrawal.
[reveal: v-261]
[pause: 0.45]
C: One: the takedown service writes status blocked in the link store.
[reveal: v-262]
[pause: 0.45]
C: Two: it publishes on the invalidation channel.
[reveal: v-263]
[pause: 0.45]
C: Three: the shared cache deletes the key; the takedown also deletes it directly and retries until confirmed.
[reveal: v-264]
[pause: 0.45]
C: Four: every redirect server drops the code from its in-process cache.
[reveal: v-265]
[pause: 0.45]
C: Five: the edge is purged. The next request reads blocked from the store and answers four-ten Gone, with a warning page.
[pause: 1.1]

[slide: v-266]
[pause: 1.3]
C: As a sequence.
[reveal: v-267]
[pause: 0.45]
C: Trust and safety posts the takedown with a reason.
[reveal: v-268]
[pause: 0.45]
C: The status is set and audited.
[reveal: v-269]
[pause: 0.45]
C: The shared cache key is deleted directly, retried until confirmed.
[reveal: v-270]
[pause: 0.45]
C: The invalidation is published.
[reveal: v-271]
[pause: 0.45]
C: It reaches every server and the edge.
[reveal: v-272]
[pause: 0.45]
C: If that event is lost, the in-process and edge lifetimes are sixty seconds each, so the worst case is about two minutes.
[reveal: v-273]
[pause: 0.45]
C: The next request reads blocked: four-ten.
[pause: 1.1]

[pause: 1.4]

## 5.1 Components and technologies

[slide: v-274]
[pause: 1.2]
C: Now one level down. Every container, with the technology I would run it on, the components inside the two services, and for each choice, the alternatives I rejected and why.
[pause: 1.8]

[slide: v-275]
[pause: 1.3]
C: The container view again, with one change: the type line now names the technology. I'll walk it once quickly, then defend each choice on its own slide.
[reveal: v-276]
[pause: 0.45]
C: The visitor.
[reveal: v-277]
[pause: 0.45]
C: The edge is a bought C-D-N with purge by surrogate key.
[reveal: v-278]
[pause: 0.45]
C: The redirect service is Go on Kubernetes, with an in-process cache and single flight.
[reveal: v-279]
[pause: 0.45]
C: The shared cache is Redis Cluster, with a replica per shard.
[reveal: v-280]
[pause: 0.45]
C: The link store is PostgreSQL, sharded by code, with a primary per shard in the region that creates its links.
[reveal: v-281]
[pause: 0.45]
C: The create service is Go as well.
[reveal: v-282]
[pause: 0.45]
C: The range allocator is etcd: three nodes, Raft, one compare-and-set transaction per lease.
[reveal: v-283]
[pause: 0.45]
C: The classifier is a bought web-risk A-P-I.
[reveal: v-284]
[pause: 0.45]
C: The click pipeline is Kafka into a Flink job into ClickHouse.
[reveal: v-285]
[pause: 0.45]
C: And the takedown service is a small Go service that publishes to a Kafka topic. Six technologies in total, and three of them we would buy managed.
[pause: 1.1]

[slide: v-286]
[pause: 1.3]
C: C-four level three, components, for the container that matters most. Inside the redirect service, in the order a request meets them.
[reveal: v-287]
[pause: 0.45]
C: The edge forwards a miss.
[reveal: v-288]
[pause: 0.45]
C: The H-T-T-P handler parses the code, rejects anything that is not seven to thirty characters of the alphabet before it touches a cache, and writes the three-oh-two, four-oh-four or four-ten with the cache headers.
[reveal: v-289]
[pause: 0.45]
C: The resolver owns single flight: one in-flight lookup per code per process, everyone else waits on it. In Go that is the singleflight package.
[reveal: v-290]
[pause: 0.45]
C: It asks the in-process cache first. That's ristretto: a bounded cache with TinyLFU admission, so a scan of random codes cannot evict the hot set. Three hundred thousand codes, sixty seconds, about a hundred megabytes.
[reveal: v-291]
[pause: 0.45]
C: On a miss, the cache client: a cluster-aware Redis client that keeps the slot map and has a two-millisecond timeout.
[reveal: v-292]
[pause: 0.45]
C: It talks to Redis Cluster.
[reveal: v-293]
[pause: 0.45]
C: On a second miss, the store client: a connection pool that maps the code to its shard, with a twenty-millisecond timeout.
[reveal: v-294]
[pause: 0.45]
C: And PostgreSQL, read by primary key.
[reveal: v-295]
[pause: 0.45]
C: After the answer, the handler hands the click to the click emitter: an in-memory ring buffer that pre-aggregates and flushes every second.
[reveal: v-296]
[pause: 0.45]
C: Into the Kafka click topic, asynchronously.
[reveal: v-297]
[pause: 0.45]
C: And on the left: an invalidation listener reads the invalidation topic with its own consumer group, and drops codes from the in-process cache. On restart it rewinds five minutes, so it cannot miss a recent takedown.
[pause: 1.1]

[slide: v-298]
[pause: 1.3]
C: And the create service, components.
[reveal: v-299]
[pause: 0.45]
C: An integrator posts a batch of links.
[reveal: v-300]
[pause: 0.45]
C: The A-P-I handler looks up the idempotency key first: a repeat returns the stored response. It answers two-oh-one, four-oh-nine or four-twenty-two.
[reveal: v-301]
[pause: 0.45]
C: The rate limiter takes a token from a bucket per A-P-I key, kept in Redis.
[reveal: v-302]
[pause: 0.45]
C: The safety client asks the web-risk A-P-I, with a hundred-and-fifty-millisecond timeout and a circuit breaker. If the classifier is down: anonymous creates are refused with a retry, trusted keys are accepted and rescanned later.
[reveal: v-303]
[pause: 0.45]
C: The encoder runs the Feistel permutation and base sixty-two. Its round key comes from a key-management service at start-up.
[reveal: v-304]
[pause: 0.45]
C: It takes the next I-D from the range holder, an etcd client that leases a thousand I-Ds and leases the next block at half-used.
[reveal: v-305]
[pause: 0.45]
C: And the store writer inserts on conflict do nothing. No row back means the code was taken: four-oh-nine for an alias. The idempotency row is written in the same transaction, so a crash can never leave a link without its idempotency record.
[pause: 1.1]

[slide: v-306]
[pause: 1.0]
C: The link store. I'd run PostgreSQL, sharded by code: sixteen shards per region to start. Each region is the primary for the links it creates, its slice of the I-D space, and holds asynchronous replicas of the other regions. Each primary has a synchronous standby in another zone. The insert is on conflict do nothing: no row back means the code was taken. A custom alias has no I-D, so its home region is fixed by a hash of the alias, and both creates of the same alias land on one primary.
[reveal: v-307]
[pause: 0.45]
C: Why: the primary key is the unique constraint I need. Six terabytes is boring for it, and we know exactly how it fails.
[reveal: v-308]
[pause: 0.45]
C: Rejected: Cassandra or Scylla. Good at reads, but uniqueness needs a lightweight transaction, a Paxos round per insert, and its multi-region serial modes are easy to get wrong. Its strength, leaderless writes everywhere, buys nothing at four hundred writes a second.
[reveal: v-309]
[pause: 0.45]
C: DynamoDB: a conditional put is exactly the constraint, in one region. But global tables resolve concurrent writes by last writer wins, so an alias created in two regions at once could succeed twice.
[reveal: v-310]
[pause: 0.45]
C: And one big PostgreSQL: the writes fit, but eighteen terabytes on one primary is one failure domain, and vacuum on a twelve-billion-row table is its own project.
[pause: 1.0]

[slide: v-311]
[pause: 1.0]
C: The range allocator: etcd, three nodes per region, one in each zone. A lease is one transaction: if the next key's revision is still what I read, put next plus a thousand. It commits when a majority of the Raft group has it. There is no expiring lock, so no clock assumption and no fencing token. A crashed server just leaves a gap.
[reveal: v-312]
[pause: 0.45]
C: Why etcd: a linearizable compare-and-set by revision, it survives losing one node, and the load is point four leases a second. And it's often already running under Kubernetes.
[reveal: v-313]
[pause: 0.45]
C: Rejected: ZooKeeper. The same guarantee, a conditional write on a version, replicated by its own atomic broadcast protocol. An honest equal. I'd reject it only because it is a Java ensemble we would run for this alone.
[reveal: v-314]
[pause: 0.45]
C: Redis increment-by: fast, but replication is asynchronous. After a fail-over the new primary may not have seen the last increment, and it hands out the same range twice. That breaks S-one silently, which is the worst way to break it.
[reveal: v-315]
[pause: 0.45]
C: A Cassandra counter cannot compare-and-set and is not idempotent; a lightweight transaction would work but ties create to the busiest data store.
[reveal: v-316]
[pause: 0.45]
C: And a PostgreSQL sequence that increments by a thousand is durable and simple, a defensible choice. I'd reject it because create would then depend on one shard's fail-over.
[pause: 1.0]

[slide: v-317]
[pause: 1.0]
C: The shared cache: Redis Cluster, six primaries and six replicas per region, bought managed. Sixteen thousand three hundred and eighty-four hash slots over six shards, about seventeen gigabytes of the hot set each. A miss sets the key with an hour's lifetime and jitter; a takedown deletes the key directly. Least-frequently-used eviction.
[reveal: v-318]
[pause: 0.45]
C: Why: a replica per shard, so losing a shard is a promotion, not a cold slice of the key space.
[reveal: v-319]
[pause: 0.45]
C: Rejected: Memcached, an honest equal, simpler and multi-threaded. But a node's loss is a cold slice with no replica, which is exactly the stampede of challenge three.
[reveal: v-320]
[pause: 0.45]
C: Hazelcast: an in-memory data grid with a near cache. Its near cache duplicates the in-process cache we already have, its clients are Java-first, and its split-brain merge policies solve a problem a cache-aside copy does not have.
[reveal: v-321]
[pause: 0.45]
C: And no shared cache at all, just store replicas: it works at four thousand a second, until a region's redirect servers restart together and every miss lands on the store.
[pause: 1.0]

[slide: v-322]
[pause: 1.0]
C: Inside each redirect server: ristretto and singleflight in Go, or Caffeine in Java, which does both. Three hundred thousand entries, about a hundred megabytes per server, sixty seconds, and ten seconds for a not-found.
[reveal: v-323]
[pause: 0.45]
C: Why: TinyLFU admission. A new key gets in only if it is more frequent than the one it would evict, so a storm of random codes cannot push out the hot set. And singleflight turns concurrent misses into one lookup.
[reveal: v-324]
[pause: 0.45]
C: Rejected: a plain least-recently-used map, which admits everything, so a scan evicts exactly the hot set.
[reveal: v-325]
[pause: 0.45]
C: A sidecar cache per host: one more hop and one more process, for a job a library does.
[reveal: v-326]
[pause: 0.45]
C: And no local cache: every viral click becomes a network call to one Redis shard. That's challenge three.
[pause: 1.0]

[slide: v-327]
[pause: 1.0]
C: The click log: Kafka, three brokers per region, replication factor three. Topic clicks, thirty-two partitions keyed by code, a week's retention. Today the producer waits for one acknowledgement and pre-aggregates per code and country each second; when clicks are billed it waits for all replicas, is idempotent, and every click carries an I-D.
[reveal: v-328]
[pause: 0.45]
C: Why: a replayable log. A bug in counting is fixed by replaying a week, which is the feature that matters here. And pre-aggregation means a viral code is forty small messages a second, not a hot partition.
[reveal: v-329]
[pause: 0.45]
C: Rejected: RabbitMQ. It's a queue: once acknowledged, a message is gone, so there is nothing to replay.
[reveal: v-330]
[pause: 0.45]
C: Kinesis or Pub-Sub: honest equals if we are on that cloud. Buy, not build.
[reveal: v-331]
[pause: 0.45]
C: And writing straight into the stats store: no buffer against a spike, and the redirect's health would depend on the analytics database.
[pause: 1.0]

[slide: v-332]
[pause: 1.0]
C: Counting: a Flink job into ClickHouse. The job is keyed by code, counts in one-minute windows of event time, and allows thirty seconds of lateness. When billed, it removes duplicates by event I-D, kept for a day. ClickHouse stores counts ordered by code, day and country, and sums rows with the same key in the background.
[reveal: v-333]
[pause: 0.45]
C: Why: event-time windows with a stated lateness, exactly-once state through checkpoints, and a column store that answers by code and day in milliseconds.
[reveal: v-334]
[pause: 0.45]
C: Rejected: Spark Structured Streaming is an honest equal; its micro-batches add seconds, which is fine.
[reveal: v-335]
[pause: 0.45]
C: A nightly batch job: the requirement says minutes.
[reveal: v-336]
[pause: 0.45]
C: Cassandra counters: a retried increment counts twice. Wrong for anything that may be billed.
[reveal: v-337]
[pause: 0.45]
C: And a PostgreSQL table is fine on day one, but counts by code, day and country grow into billions of rows, which a column store compresses far better.
[pause: 1.0]

[slide: v-338]
[pause: 1.0]
C: Invalidation: a Kafka topic for the servers and a surrogate-key purge for the edge. Each redirect server reads the topic with its own consumer group, and rewinds five minutes when it starts. The takedown service calls the C-D-N's purge A-P-I with the surrogate key, and retries; the sixty-second edge lifetime is the backstop.
[reveal: v-339]
[pause: 0.45]
C: Why: we already run Kafka, and a reconnecting server replays what it missed instead of silently missing it.
[reveal: v-340]
[pause: 0.45]
C: Rejected: Redis Pub-Sub. It is at most once: a server disconnected for one second misses the message and never knows. It would only be acceptable because the lifetime backstops it, and Kafka's replay costs nothing extra.
[reveal: v-341]
[pause: 0.45]
C: Polling the store: forty servers asking every second adds load, and a slow store makes takedowns slower exactly when it hurts.
[reveal: v-342]
[pause: 0.45]
C: And purge by U-R-L works, but every variant must be listed. One surrogate key names them all.
[pause: 1.0]

[slide: v-343]
[pause: 1.0]
C: Services and the edge: Go on Kubernetes across three zones per region, behind a bought C-D-N. Redirect pods scale on requests per second, and a pod warms its cache from the last hour's top codes before it reports ready. Rollouts go one zone at a time. The C-D-N caches only links over a click-rate threshold, chosen by a response header.
[reveal: v-344]
[pause: 0.45]
C: Why: small binaries and short, predictable pauses for a twenty-millisecond p ninety-nine. And points of presence are not our business.
[reveal: v-345]
[pause: 0.45]
C: Rejected: Java with Caffeine is an honest equal. If the team is a J-V-M team, pick it and tune the collector.
[reveal: v-346]
[pause: 0.45]
C: Serverless functions for the redirect: cold starts break the target, and per-invocation pricing at ten billion a month is the most expensive way to run a loop.
[reveal: v-347]
[pause: 0.45]
C: And building our own edge: hundreds of points of presence, for a product whose core is a map lookup.
[pause: 1.0]

[slide: v-348]
[pause: 1.0]
C: The stack on one slide, as I'd leave it on the whiteboard.
[reveal: v-349]
[pause: 0.45]
C: Link store: PostgreSQL, because the primary key is the authority.
[reveal: v-350]
[pause: 0.45]
C: Allocator: etcd, because asynchronous replication could reissue a range.
[reveal: v-351]
[pause: 0.45]
C: Shared cache: Redis Cluster, a replica per shard.
[reveal: v-352]
[pause: 0.45]
C: Local cache: TinyLFU admission.
[reveal: v-353]
[pause: 0.45]
C: Click log: Kafka, for replay.
[reveal: v-354]
[pause: 0.45]
C: Counting: Flink into ClickHouse.
[reveal: v-355]
[pause: 0.45]
C: Invalidation: a replayable topic and a surrogate-key purge.
[reveal: v-356]
[pause: 0.45]
N: Naming a product is not the signal. Naming the property that rules out its rival is. Interviewers go one level down on whichever box you name, so name only what you can defend.
[pause: 1.0]

[slide: v-357]
[pause: 0.6]
N: Before the challenges, swap seats. You are the interviewer now. Of everything on the last slide, which box would you push on, and what is the one question you would ask? Pause the video and pick one.
[pause: 3.0]

[slide: v-358]
[pause: 1.0]
N: Here is where interviewers usually go.
[reveal: v-359]
[pause: 0.45]
I: Link store. Two regions accept the same alias in the same second. Which write wins?
[pause: 1.2]
N: Neither region decides alone. The alias has a home region, fixed by its hash, so both creates reach one primary and the key rejects the second. The trap is saying last writer wins.
[reveal: v-360]
[pause: 0.45]
I: Allocator. The etcd leader dies mid-lease. Can two servers hold the same thousand I-Ds?
[pause: 1.2]
N: No. A lease commits only on a majority, the new leader has every committed entry, and an unfinished one is retried against the new revision. The worst case is a gap.
[reveal: v-361]
[pause: 0.45]
I: Shared cache. A Redis primary fails over. What does a redirect see in the next two seconds?
[pause: 1.2]
N: Timeouts at two milliseconds, then the store, already shielded by the in-process cache and single flight. The client refreshes its slot map, and a takedown's delete is retried until it is confirmed.
[reveal: v-362]
[pause: 0.45]
I: Click log. Counting had a bug for three days. How do you fix the numbers?
[pause: 1.2]
N: Reset the counting job's consumer group three days back, recount into a new table, and switch the reads. That is why it is a log and why it keeps a week.
[reveal: v-363]
[pause: 0.45]
I: Invalidation. One redirect server was cut off for ten minutes during a takedown. Is it still serving the link?
[pause: 1.2]
N: For at most sixty seconds after the event it missed. Ten minutes is past the five-minute rewind, so here the lifetime, not the topic, is what keeps the promise.
[reveal: v-364]
[pause: 0.45]
N: If you picked a box that is not on this list, good. Write its probe down and answer it before you watch on.
[pause: 1.2]

[pause: 1.4]

## 6 Bridge

[slide: v-365]
[pause: 1.2]
V: It works. The question now is where it breaks first.
[pause: 1.8]

[slide: v-366]
[pause: 1.3]
C: The baseline with eight attack points, marked one at a time.
[reveal: v-367]
[pause: 0.45]
C: The create service: two servers and one code, then codes that can be walked. Challenges one and two.
[reveal: v-368]
[pause: 0.45]
C: The shared cache: one viral key. Challenge three.
[reveal: v-369]
[pause: 0.45]
C: The edge and the browser: three-oh-one or three-oh-two. Challenge four. And every cache layer together: a takedown in five minutes, challenge five.
[reveal: v-370]
[pause: 0.45]
C: The redirect service: counting without slowing it. Challenge six.
[reveal: v-371]
[pause: 0.45]
C: The click log carries that fix.
[reveal: v-372]
[pause: 0.45]
C: And the link store's region: a region lost, challenge seven. Then finally: how would we know any of it was broken? I'll take them in an order where each fix creates the next question.
[pause: 1.1]

[pause: 1.4]

## 7 Challenges

[slide: v-373]
[pause: 1.2]
C: Eight challenges, each the same way: the question, the naive answer, a case with numbers, where it breaks, the fix, why it works, then the interviewer pushes on the fix itself, and what I'd say in the room.
[pause: 1.8]

[pause: 1.4]

## 7.1 Challenge 1: Two servers, one code

[slide: v-374]
[pause: 1.2]
N: Challenge one. Two create servers run at once: how do they never hand out the same code, without asking each other every time?
[pause: 1.8]

[slide: v-375]
[pause: 0.6]
I: Two create servers run at the same time. How do they never hand out the same code, without asking each other every time?
[pause: 2.0]

[slide: v-376]
[pause: 1.3]
C: The create path, on the baseline.
[reveal: v-377]
[pause: 0.45]
C: The naive answer: generate a random code, check whether it exists, insert it if not. Look at the red create service. The check is stale the moment it returns.
[reveal: v-378]
[pause: 0.45]
C: Between the select and the insert, another server can do exactly the same thing.
[pause: 1.1]

[slide: v-379]
[pause: 1.0]
C: The trace. Two customers ask for the alias sale, three milliseconds apart.
[reveal: v-380]
[pause: 0.45]
C: Server A selects: none.
[reveal: v-381]
[pause: 0.45]
C: Server B selects: none.
[reveal: v-382]
[pause: 0.45]
C: A inserts.
[reveal: v-383]
[pause: 0.45]
C: B inserts, and without a constraint it overwrites.
[reveal: v-384]
[pause: 0.45]
C: The next day, A's printed flyers open B's page.
[reveal: v-385]
[pause: 0.45]
C: Random codes have the same race. A third of a percent sounds rare, but at four hundred creates a second, rare happens every day.
[pause: 1.0]

[slide: v-386]
[pause: 1.3]
C: The fix has two parts.
[reveal: v-387]
[pause: 0.45]
C: Outlined green: generated codes come from disjoint ranges. Each server leases a thousand I-Ds from the allocator in one etcd transaction and hands them out from memory. Two servers can never draw the same I-D, so generated codes never even reach the constraint as a conflict.
[reveal: v-388]
[pause: 0.45]
C: And every insert carries the primary key on the code. For a custom alias, the one shard that owns sale accepts one insert and rejects the other: one two-oh-one, one four-oh-nine.
[reveal: v-389]
[pause: 0.45]
C: The mechanism: the store is the authority, not my application. And aliases are eight characters or longer, so an alias can never take a code the counter will produce later.
[reveal: v-390]
[pause: 0.45]
C: The property: S-one is decided by the one place that sees every write for a code, its shard. And L-one: a create waits only on its own insert.
[reveal: v-391]
[pause: 0.45]
C: What I rejected: Redis increment-by as the counter. After a fail-over, the new primary can hand out a range it already gave away.
[pause: 1.1]

[slide: v-392]
[pause: 1.3]
C: The ranges. The allocator says next is forty-one thousand. Server A holds forty thousand to forty thousand nine hundred ninety-nine and is on forty thousand and seventeen. B and C hold their own blocks. Each next I-D goes through the permutation and base sixty-two.
C: A server that crashes wastes the rest of its block. That is a gap, never a collision, and with two hundred and ninety times more codes than links, gaps cost nothing.
[pause: 1.1]

[slide: v-393]
[pause: 1.3]
C: As a sequence.
[reveal: v-394]
[pause: 0.45]
C: Server A leases with a compare-and-set: next goes from forty thousand to forty-one thousand only if it is still forty thousand.
[reveal: v-395]
[pause: 0.45]
C: Okay, A owns that block.
[reveal: v-396]
[pause: 0.45]
C: It hands out I-Ds locally and leases the next block early, at half-used.
[reveal: v-397]
[pause: 0.45]
C: Then a customer asks for sale.
[reveal: v-398]
[pause: 0.45]
C: The insert conflicts.
[reveal: v-399]
[pause: 0.45]
C: And the second customer gets four-oh-nine while the first keeps it.
[pause: 1.1]

[slide: v-400]
[pause: 1.0]
C: The lease in code, against etcd's Go client. One transaction: if the key's modification revision is still the one I read, put next plus a thousand; else, give me the current value. If it succeeded, the range is ours alone. If not, the else branch already returned the new value and revision, so I try again.
[reveal: v-401]
[pause: 0.45]
C: Inside a lease, no coordination is needed. Across leases, the compare on the revision makes overlap impossible.
[pause: 1.0]

[slide: v-402]
[pause: 0.6]
I: The allocator is down. Or a server crashes holding half a range.
[pause: 2.0]

[slide: v-403]
[pause: 0.6]
C: Three answers.
[reveal: v-404]
[pause: 0.45]
C: Runway: each server leases its next block at half-used, so it holds five hundred to fifteen hundred I-Ds. At the four-hundred-a-second peak across ten servers, that's twelve to thirty-seven seconds; at the average, two to six minutes.
[reveal: v-405]
[pause: 0.45]
C: The allocator is three etcd nodes across zones, so one node lost is not an outage.
[reveal: v-406]
[pause: 0.45]
C: A crashed server's unused I-Ds are simply skipped.
[reveal: v-407]
[pause: 0.45]
C: The honest limit. If the allocator is down for minutes, creates stop. Redirects never depended on it. That is the right way round: the product keeps working.
[pause: 0.8]

[slide: v-408]
[pause: 0.7]
V: If asked, I'd say: each create server leases a block of a thousand I-Ds, so coordination happens once per thousand links, not once per link. The unique constraint on the code is the final authority, so an alias race ends in one success and one conflict. If the allocator goes down, servers have their leased runway, and redirects never depended on it.
[pause: 1.0]
N: That fix creates the next question: codes from a counter are in order.
[pause: 1.6]

[pause: 1.4]

## 7.2 Challenge 2: Codes in order

[slide: v-409]
[pause: 1.2]
N: Challenge two. The codes come from a counter: what can a stranger learn from that, and how do we stop it without losing uniqueness?
[pause: 1.8]

[slide: v-410]
[pause: 0.6]
I: Your codes come from a counter. What can someone learn from that?
[pause: 2.0]

[slide: v-411]
[pause: 1.3]
C: The create path again.
[reveal: v-412]
[pause: 0.45]
C: The naive answer: base sixty-two makes them look random. It doesn't. Base sixty-two of a counter is still a counter, in a different alphabet.
[reveal: v-413]
[pause: 0.45]
C: Neighbouring I-Ds give neighbouring codes, and the red box is the encoder that does it.
[pause: 1.1]

[slide: v-414]
[pause: 1.0]
C: The trace.
[reveal: v-415]
[pause: 0.45]
C: At nine a user gets zero-zero-zero-zero-g-eight-Q.
[reveal: v-416]
[pause: 0.45]
C: At ten past, another: zero-zero-zero-zero-g-B-A. Subtract: two thousand links in ten minutes. That's our creation rate, for free.
[reveal: v-417]
[pause: 0.45]
C: Then a scraper asks for the next code, and the next.
[reveal: v-418]
[pause: 0.45]
C: And reads every link created that morning, including someone's unlisted document share.
[reveal: v-419]
[pause: 0.45]
C: Volume leaks to a competitor, and links leak that their owners thought nobody would find.
[pause: 1.0]

[slide: v-420]
[pause: 1.3]
C: The fix lives in the same create box.
[reveal: v-421]
[pause: 0.45]
C: Between the counter and the encoder, a keyed permutation.
[reveal: v-422]
[pause: 0.45]
C: A four-round Feistel network over forty-two bits with a secret key, cycle-walked to stay below sixty-two to the seventh. Then base sixty-two. And a rate limit on four-oh-fours per client, so random guessing is slow.
[reveal: v-423]
[pause: 0.45]
C: Uniqueness comes from the counter, unpredictability from the key. They are separate, so neither weakens the other.
[reveal: v-424]
[pause: 0.45]
C: Rejected: a hash of the long U-R-L. Cut to seven characters it collides, and one U-R-L would get the same code for every owner.
[pause: 1.1]

[slide: v-425]
[pause: 1.3]
C: Three neighbouring I-Ds: forty thousand and seventeen, eighteen, nineteen. Out come a-Z-three-k-Q-nine-x, P-q-zero-seven-m-W-d, and three-f-L-x-nine-T-b. Unrelated. And because a Feistel network is a bijection, two different I-Ds can never give the same code. Uniqueness is untouched.
C: One more property I'll use in challenge seven: the permutation is invertible. A server holding the key can turn a code back into its I-D, and so into the region that created it.
[pause: 1.1]

[slide: v-426]
[pause: 1.0]
C: In code. Split forty-two bits into two halves. Four rounds: swap the halves and mix one with a keyed pseudo-random function of the other. The function is a keyed hash, H-MAC with SHA-two-fifty-six truncated, keyed from the key-management service.
[reveal: v-427]
[pause: 0.45]
C: Each round is invertible, so the whole thing is a bijection. If the result lands above sixty-two to the seventh, run it again: that's cycle walking, and it keeps the bijection on exactly the code space.
[pause: 1.0]

[slide: v-428]
[pause: 0.6]
I: The key leaks. Or a customer says short links to private files must not be guessable at all.
[pause: 2.0]

[slide: v-429]
[pause: 0.6]
C: A leaked key: new codes use a new key, with a version marker or a fresh slice of the I-D space. Old codes stay valid, because codes are stored, never recomputed. Nothing breaks.
[reveal: v-430]
[pause: 0.45]
C: Private content is the honest limit. Forty-two bits can be sampled by an attacker with enough addresses. Links to private files need authentication or a long random token, not a short link. That's a conversation with product, not a cleverer encoder.
[pause: 0.8]

[slide: v-431]
[pause: 0.7]
V: If asked, I'd say: a counter gives uniqueness, but base sixty-two of a counter is still a counter. It leaks our volume and lets anyone walk the links. I pass the I-D through a keyed permutation, which keeps it unique and makes neighbours unrelated. And I'm clear that a short code is not a secret: private links need authentication.
[pause: 1.0]
N: Codes are settled. The next question is the read side: one code, forty thousand times a second.
[pause: 1.6]

[pause: 1.4]

## 7.3 Challenge 3: One link at 40,000 clicks a second

[slide: v-432]
[pause: 1.2]
N: Challenge three. One link goes viral: what happens to the one cache shard that holds it, and to the store when that shard restarts?
[pause: 1.8]

[slide: v-433]
[pause: 0.6]
I: A link goes viral. Forty thousand clicks a second, all on one code. What happens?
[pause: 2.0]

[slide: v-434]
[pause: 1.3]
C: The redirect path.
[reveal: v-435]
[pause: 0.45]
C: The naive answer: it's cached, so it's fine. Look at the red boxes. Redis Cluster puts a key in one hash slot, on one shard, so all forty thousand requests land on one shard.
[reveal: v-436]
[pause: 0.45]
C: And if that shard restarts without a warm replica, they all land on one row of the store.
[pause: 1.1]

[slide: v-437]
[pause: 1.0]
C: The trace.
[reveal: v-438]
[pause: 0.45]
C: At two minutes past two, code k-seven-P-q-two-m-Z goes from three clicks a second to forty thousand.
[reveal: v-439]
[pause: 0.45]
C: Its Redis shard's p ninety-nine goes from under a millisecond to nine, and every other code on that shard slows with it.
[reveal: v-440]
[pause: 0.45]
C: At five past, a deploy restarts the shard. Two hundred milliseconds of misses.
[reveal: v-441]
[pause: 0.45]
C: Eight thousand identical selects on one row.
[reveal: v-442]
[pause: 0.45]
C: Illustrative numbers. The shape is the point: one key concentrates load that a fleet would otherwise spread.
[pause: 1.0]

[slide: v-443]
[pause: 1.3]
C: The fix is in the redirect service.
[reveal: v-444]
[pause: 0.45]
C: An in-process cache on every redirect server: ristretto, three hundred thousand entries, sixty seconds. With forty servers, the viral code is a thousand requests a second from each one's own memory. Trivial.
[reveal: v-445]
[pause: 0.45]
C: And single flight: when many requests miss the same code at once, the first one looks it up and the others wait on its answer. Plus negative caching for unknown codes, so a scanner's four-oh-fours don't reach the store.
[reveal: v-446]
[pause: 0.45]
C: The store now sees at most one query per server per code, not one per click.
[reveal: v-447]
[pause: 0.45]
C: Rejected: Redis replica reads alone. They spread the hot key over two nodes, not forty, and every click is still a network hop.
[pause: 1.1]

[slide: v-448]
[pause: 1.3]
C: As a sequence.
[reveal: v-449]
[pause: 0.45]
C: A thousand requests for the same code arrive in twenty milliseconds.
[reveal: v-450]
[pause: 0.45]
C: In-process miss: the first leads, nine hundred ninety-nine wait.
[reveal: v-451]
[pause: 0.45]
C: One get on Redis.
[reveal: v-452]
[pause: 0.45]
C: Miss: the shard is restarting.
[reveal: v-453]
[pause: 0.45]
C: One select on the store.
[reveal: v-454]
[pause: 0.45]
C: The U-R-L.
[reveal: v-455]
[pause: 0.45]
C: One answer, a thousand three-oh-twos, and the code stays in process memory.
[pause: 1.1]

[slide: v-456]
[pause: 1.0]
C: Single flight in Go. Check local memory. On a miss, group dot do with the code as the key: the first caller runs the function, shared cache then store, and fills local memory for sixty seconds. Every concurrent caller with the same code waits and receives the same result.
[reveal: v-457]
[pause: 0.45]
C: The load on the store is servers times hot codes, however many clicks arrive.
[pause: 1.0]

[slide: v-458]
[pause: 0.6]
I: Now the in-process lifetime means a takedown takes up to a minute longer. And a whole region's servers restart together.
[pause: 2.0]

[slide: v-459]
[pause: 0.6]
C: The lifetime is a line in the takedown budget, and the invalidation topic drops entries early anyway. That's challenge five.
[reveal: v-460]
[pause: 0.45]
C: Restarts roll, one zone at a time, never a whole region at once, and a starting pod warms its cache from the last hour's top codes before it passes its readiness check.
[reveal: v-461]
[pause: 0.45]
C: The honest limit: for a link that is viral across the world, the real answer is the edge, close to every user. Which raises the next question.
[pause: 0.8]

[slide: v-462]
[pause: 0.7]
V: If asked, I'd say: a viral link is a hot key, not a load problem. I answer it from memory on every redirect server and coalesce misses, so each server sends one query, whatever the click rate. The cost is a short staleness window, which I count in the takedown budget.
[pause: 1.0]
N: That fix creates the next question: should the answer live even closer to the user?
[pause: 1.6]

[pause: 1.4]

## 7.4 Challenge 4: 301 or 302?

[slide: v-463]
[pause: 1.2]
N: Challenge four. Permanent or temporary redirect: what does each one cost the product, not just the servers?
[pause: 1.8]

[slide: v-464]
[pause: 0.6]
I: Should the redirect be a three-oh-one or a three-oh-two?
[pause: 2.0]

[slide: v-465]
[pause: 1.3]
C: The browser, the edge and the redirect service.
[reveal: v-466]
[pause: 0.45]
C: The naive answer: three-oh-one, it's permanent and it saves servers. It does save servers.
[reveal: v-467]
[pause: 0.45]
C: Look at the red browser. A three-oh-one tells it to remember the answer, and it does, indefinitely. It never asks us again.
[pause: 1.1]

[slide: v-468]
[pause: 1.0]
C: The trace.
[reveal: v-469]
[pause: 0.45]
C: Monday a user clicks; we answer three-oh-one; the browser caches it.
[reveal: v-470]
[pause: 0.45]
C: Tuesday the same user clicks again: the browser answers, we never see it, it's not counted.
[reveal: v-471]
[pause: 0.45]
C: At three, the link is blocked for phishing.
[reveal: v-472]
[pause: 0.45]
C: At three-twenty, that user's browser still goes straight to the phishing page.
[reveal: v-473]
[pause: 0.45]
C: Two losses: the owner loses the count, and we lose the ability to protect the user.
[pause: 1.0]

[slide: v-474]
[pause: 1.3]
C: The fix.
[reveal: v-475]
[pause: 0.45]
C: Three-oh-two by default, with browser caching off, and the edge allowed to keep it for sixty seconds, tagged with a surrogate key, purgeable.
[reveal: v-476]
[pause: 0.45]
C: Three-oh-one only as an owner's opt-in, for links that are permanent and that they accept will not be counted.
[reveal: v-477]
[pause: 0.45]
C: The property: counting and takedowns stay at layers we can reach. And the edge gives us most of the saving a three-oh-one would, at a bounded cost in freshness.
[reveal: v-478]
[pause: 0.45]
C: Rejected: a C-D-N without a purge A-P-I. Then the sixty-second edge copy could not be taken back early.
[pause: 1.1]

[slide: v-479]
[pause: 1.0]
C: The layers.
[reveal: v-480]
[pause: 0.45]
C: The browser with a three-oh-one: zero milliseconds, never sees the click again, cannot be taken back.
[reveal: v-481]
[pause: 0.45]
C: The edge with a three-oh-two cached for sixty seconds: a few milliseconds near the user, clicks from edge logs, minutes late, purgeable.
[reveal: v-482]
[pause: 0.45]
C: Our servers and caches: a millisecond, every click, recallable.
[reveal: v-483]
[pause: 0.45]
C: The store: the truth, for misses only.
[pause: 1.0]

[slide: v-484]
[pause: 0.6]
I: Finance says the edge bill for ten billion requests is too high. Or the counts from edge logs arrive twenty minutes late.
[pause: 2.0]

[slide: v-485]
[pause: 0.6]
C: The edge bill: compare the per-request cost with the servers and cross-region traffic it saves, and turn edge caching on per link, by click rate. Only hot links need it, and they are two percent of links.
[reveal: v-486]
[pause: 0.45]
C: Late counts are the stated lag, shown as as-of. When clicks are billed, the count must come from our servers, or a signed function running at the edge, not from logs. That is challenge six.
[pause: 0.8]

[slide: v-487]
[pause: 0.7]
V: If asked, I'd say: three-oh-one against three-oh-two is a product decision, not an optimisation. A three-oh-one is answered by the browser forever, so we lose the click and the ability to take a link down. I default to three-oh-two, let the edge cache it for a minute, and offer three-oh-one only to owners who want a permanent, uncounted link.
[pause: 1.0]
N: That fix creates the next question: we now hold copies at four layers. Can we withdraw all of them in five minutes?
[pause: 1.6]

[pause: 1.4]

## 7.5 Challenge 5: Dead everywhere in five minutes

[slide: v-488]
[pause: 1.2]
N: Challenge five. A phishing link is reported: how do we prove it stops working at every layer within five minutes, even when a message is lost?
[pause: 1.8]

[slide: v-489]
[pause: 0.6]
I: Legal reports a phishing link. It must stop working everywhere within five minutes. Show me.
[pause: 2.0]

[slide: v-490]
[pause: 1.3]
C: The naive answer: delete the row.
[reveal: v-491]
[pause: 0.45]
C: Look at the red boxes. The edge, every redirect server's memory, the Redis cache. None of them reads the row on a hit. Deleting the row changes the truth and nothing that answers.
[pause: 1.1]

[slide: v-492]
[pause: 1.0]
C: The trace.
[reveal: v-493]
[pause: 0.45]
C: At three o'clock the status is set.
[reveal: v-494]
[pause: 0.45]
C: Still answering: the shared cache with an hour's lifetime, forty servers' memory with sixty seconds, the edge in thirty cities with sixty seconds.
[reveal: v-495]
[pause: 0.45]
C: And browsers that got a three-oh-one last week, forever.
[reveal: v-496]
[pause: 0.45]
C: At three-twenty a victim still lands on the page, served from the shared cache.
[reveal: v-497]
[pause: 0.45]
C: So the real question is not how to delete. It is: what is the longest any copy can live after we decide?
[pause: 1.0]

[slide: v-498]
[pause: 1.3]
C: The fix, built up on the takedown path.
[reveal: v-499]
[pause: 0.45]
C: The takedown writes blocked to the store. It deletes the Redis key directly and retries until it's confirmed: that cache has a long lifetime, so it must never depend on a lost message. It publishes an invalidation on the Kafka topic: every redirect server drops the code, and the edge is purged by surrogate key. The next request reads blocked and answers four-ten with a warning page.
[reveal: v-500]
[pause: 0.45]
C: Rejected: Redis Pub-Sub for the invalidation. It is at most once: a server disconnected for a second never learns.
C: The property is S-two, and it holds by arithmetic. Here is the arithmetic.
[pause: 1.1]

[slide: v-501]
[pause: 1.3]
C: The worst case, if the invalidation event is lost. Status and the Redis delete: a couple of seconds. The in-process lifetime: sixty. The edge lifetime: sixty. The purge call: a few. About two minutes, against five. The spare covers a slow purge and a retry. Every lifetime in this system was chosen with this bar in view.
[pause: 1.1]

[slide: v-502]
[pause: 1.3]
C: The sequence once more, with the point that matters.
[reveal: v-503]
[pause: 0.45]
C: The status, then the shared cache deleted directly, not by the event.
[reveal: v-504]
[pause: 0.45]
C: Only the short-lived layers depend on the event.
[reveal: v-505]
[pause: 0.45]
C: If it is lost, their lifetimes end the copies.
[reveal: v-506]
[pause: 0.45]
C: And four-ten Gone tells crawlers to stop asking.
[pause: 1.1]

[slide: v-507]
[pause: 0.6]
C: Three cheaper defences.
[reveal: v-508]
[pause: 0.45]
C: On create, check the U-R-L against the classifier: if it's known-bad, no code is issued.
[reveal: v-509]
[pause: 0.45]
C: When the classifier's list updates, rescan recently created live links and block any matches through the same path.
[reveal: v-510]
[pause: 0.45]
C: And every takedown is audited: who, why, when, and when each layer started answering four-ten.
[pause: 0.8]

[slide: v-511]
[pause: 0.6]
I: The invalidation event is lost. Or the link was created as a three-oh-one.
[pause: 2.0]

[slide: v-512]
[pause: 0.6]
C: A lost event: the lifetimes are the backstop, by design, so the worst case is about two minutes, and Kafka's replay makes a lost event rarer still. An hourly test takedown measures the real time at every layer, which is challenge eight.
[reveal: v-513]
[pause: 0.45]
C: A three-oh-one is the honest limit. It cannot be recalled from a browser, ever. That's why it's opt-in, and why the safety check runs before a three-oh-one link is issued.
[pause: 0.8]

[slide: v-514]
[pause: 0.7]
V: If asked, I'd say: every copy of the answer is a liability. A takedown writes the status, deletes the shared-cache key directly, sends an invalidation and purges the edge. The lifetime at every layer is chosen so that even with a lost message, the worst case is inside five minutes. A three-oh-one can't be recalled, which is one more reason it isn't the default.
[pause: 1.0]
N: The redirect is fast and withdrawable. Next: how do we count it without slowing it down?
[pause: 1.6]

[pause: 1.4]

## 7.6 Challenge 6: Counting without slowing the redirect

[slide: v-515]
[pause: 1.2]
N: Challenge six. Owners want clicks by day and country: where does the count happen, and what changes when every click is money?
[pause: 1.8]

[slide: v-516]
[pause: 0.6]
I: How do you count clicks per link, per country, without touching the redirect latency?
[pause: 2.0]

[slide: v-517]
[pause: 1.3]
C: Version two's redirect path.
[reveal: v-518]
[pause: 0.45]
C: The naive answer: increment a clicks column on every redirect.
[reveal: v-519]
[pause: 0.45]
C: Look at the red store. That puts a write inside the redirect, on the row of the hottest link.
[pause: 1.1]

[slide: v-520]
[pause: 1.0]
C: The trace.
[reveal: v-521]
[pause: 0.45]
C: Forty thousand updates a second on one row.
[reveal: v-522]
[pause: 0.45]
C: The row lock serialises them.
[reveal: v-523]
[pause: 0.45]
C: Each redirect waits for its write, and p ninety-nine goes from five milliseconds to nine hundred.
[reveal: v-524]
[pause: 0.45]
C: The cache had solved the read.
[reveal: v-525]
[pause: 0.45]
C: The counter put the hot key straight back on the critical path.
[pause: 1.0]

[slide: v-526]
[pause: 1.3]
C: The fix, green along the bottom.
[reveal: v-527]
[pause: 0.45]
C: After the three-oh-two goes out, the server appends to a local buffer that pre-aggregates. The buffer flushes a batch every second into Kafka, partitioned by code. Flink counts per code per minute, then per day per country, into ClickHouse. If the buffer is full, events are dropped, and the drops are counted.
C: L-two: nothing after the answer can delay it. L-three, with a measured loss: the drop counter is the loss, and counts say as-of.
[reveal: v-528]
[pause: 0.45]
C: Rejected: Cassandra counters. They remove the row lock, but a retried increment counts twice.
[pause: 1.1]

[slide: v-529]
[pause: 1.0]
C: Precision about what the count promises, today against billed.
[reveal: v-530]
[pause: 0.45]
C: Today: at-most-once from the server, a crash loses the unflushed second. Billed: at-least-once, with a durable buffer on disk, resent until every replica acknowledges.
[reveal: v-531]
[pause: 0.45]
C: Today drops are counted and shown. Billed: an event I-D is created at the redirect and de-duplicated in Flink's keyed state, so the effect is exactly once.
[reveal: v-532]
[pause: 0.45]
C: Bots: counted today, filtered before anything is billed.
[reveal: v-533]
[pause: 0.45]
C: And the lag stays minutes either way. The redirect still never waits.
[pause: 1.0]

[slide: v-534]
[pause: 0.6]
I: Product now bills per click. A lost click is lost money, and a double-counted one is a refund.
[pause: 2.0]

[slide: v-535]
[pause: 1.3]
C: The second fix, as a sequence.
[reveal: v-536]
[pause: 0.45]
C: The three-oh-two is already sent.
[reveal: v-537]
[pause: 0.45]
C: The server appends the event, with an I-D, to a buffer on local disk.
[reveal: v-538]
[pause: 0.45]
C: It flushes a batch every second.
[reveal: v-539]
[pause: 0.45]
C: It trims the buffer only on acknowledgement.
[reveal: v-540]
[pause: 0.45]
C: Delivery to Flink is at least once.
[reveal: v-541]
[pause: 0.45]
C: And Flink de-duplicates by event I-D, filters bots, and counts.
C: The honest limit: a server's disk lost with an unflushed buffer loses up to a second of that server's clicks. That bound goes into the billing terms.
[pause: 1.1]

[slide: v-542]
[pause: 0.7]
V: If asked, I'd say: the click is recorded after the answer, never before it. Events go to a local buffer and a log, and an aggregator counts per minute. Today that's lossy by choice and we measure the loss. If clicks are billed, I add event I-Ds, a durable buffer and de-duplication, and the redirect still doesn't wait.
[pause: 1.0]
N: Every path now depends on the store being somewhere. What if that somewhere is gone?
[pause: 1.6]

[pause: 1.4]

## 7.7 Challenge 7: A region goes dark

[slide: v-543]
[pause: 1.2]
N: Challenge seven. The region holding the store's primary disappears: what keeps working, and what may stop?
[pause: 1.8]

[slide: v-544]
[pause: 0.6]
I: The region holding your link store's primary goes down. What still works?
[pause: 2.0]

[slide: v-545]
[pause: 1.3]
C: The store, the allocator and the paths that use them.
[reveal: v-546]
[pause: 0.45]
C: The naive answer: fail over the database. That's part of it.
[reveal: v-547]
[pause: 0.45]
C: But look at what is red: the PostgreSQL primaries and the etcd quorum both lived in the lost region. Fail-over takes time, and during it, creates fail and every miss goes somewhere.
[pause: 1.1]

[slide: v-548]
[pause: 1.0]
C: The trace.
[reveal: v-549]
[pause: 0.45]
C: At ten past three the primary region is lost.
[reveal: v-550]
[pause: 0.45]
C: Redirects elsewhere: ninety-eight percent from caches, two percent miss to a store that is now read-only, which is fine for reads, if the reads are local.
[reveal: v-551]
[pause: 0.45]
C: Creates fail, because the primaries and the allocator's quorum are gone.
[reveal: v-552]
[pause: 0.45]
C: Bulk integrators retry with their idempotency keys.
[pause: 1.0]

[slide: v-553]
[pause: 1.3]
C: The fix. Redirects are regional: each region has PostgreSQL replicas of every slice, its own Redis Cluster, its own etcd. A redirect never crosses a region.
[reveal: v-554]
[pause: 0.45]
C: Creates are regional too: each region is the primary for its own slice of the I-D space, Europe the first third, the Americas the second, Asia the last. A region can create without the others, and the slices replicate asynchronously.
[reveal: v-555]
[pause: 0.45]
C: L-two depends only on regional state. S-one holds because the slices are disjoint: no two regions can ever produce the same I-D.
[reveal: v-556]
[pause: 0.45]
C: Rejected: one global consensus database, Spanner or Cockroach. Every create would pay a cross-region quorum. Right for money, wrong for four hundred link creates a second.
[pause: 1.1]

[slide: v-557]
[pause: 1.3]
C: On the baseline.
[reveal: v-558]
[pause: 0.45]
C: The replica beside the link store, receiving asynchronous replication, and the shared cache reading from the local copy. Fail-over of a shard's primary is now only for writes to links created in the lost region, and those are rare: links are written once.
[pause: 1.1]

[slide: v-559]
[pause: 0.6]
I: A link created in Asia is clicked in Europe two hundred milliseconds later, before replication.
[pause: 2.0]

[slide: v-560]
[pause: 1.3]
C: The second fix, as a sequence.
[reveal: v-561]
[pause: 0.45]
C: A code created in Asia two hundred milliseconds ago.
[reveal: v-562]
[pause: 0.45]
C: It is clicked in Europe.
[reveal: v-563]
[pause: 0.45]
C: Local miss. The server inverts the permutation, gets the I-D back, and its slice says which region created it: Asia.
[reveal: v-564]
[pause: 0.45]
C: One cross-region lookup.
[reveal: v-565]
[pause: 0.45]
C: Cache the answer here.
[reveal: v-566]
[pause: 0.45]
C: And three-oh-two. One round trip slower, no error.
C: The honest limit: a region lost with unreplicated creates loses those links' last seconds. A creator who retries with the same idempotency key gets the same code back once the region returns.
[pause: 1.1]

[slide: v-567]
[pause: 0.7]
V: If asked, I'd say: redirects never leave their region. Replicas and caches answer them even with the primary gone. Creates are regional, because each region owns a slice of the I-D space. The one gap is a brand-new link clicked elsewhere before it replicates, and that costs one cross-region lookup, not an error.
[pause: 1.0]
N: Last challenge. All of this can fail silently. How would we know?
[pause: 1.6]

[pause: 1.4]

## 7.8 Challenge 8: How would you know it is broken?

[slide: v-568]
[pause: 1.2]
N: Challenge eight. The dashboards are green: how do we know the redirect a user gets is actually working, in every region?
[pause: 1.8]

[slide: v-569]
[pause: 0.6]
I: Your dashboards are green. How do you know redirects are actually working?
[pause: 2.0]

[slide: v-570]
[pause: 1.3]
C: The redirect path.
[reveal: v-571]
[pause: 0.45]
C: The naive answer: error rate and C-P-U. Those watch boxes.
[reveal: v-572]
[pause: 0.45]
C: The red one here is the shared cache, and nothing about it will show as an error.
[pause: 1.1]

[slide: v-573]
[pause: 1.0]
C: The trace.
[reveal: v-574]
[pause: 0.45]
C: Just before two in the morning, a config change sets the shared cache's lifetime to zero.
[reveal: v-575]
[pause: 0.45]
C: No errors. Median unchanged. p ninety-nine creeps from six milliseconds to eighteen, still under target.
[reveal: v-576]
[pause: 0.45]
C: Store reads go from forty a second to four thousand. Nobody is watching.
[reveal: v-577]
[pause: 0.45]
C: At nine, when the peak arrives, the store saturates and the first page fires. Seven hours late.
[pause: 1.0]

[slide: v-578]
[pause: 1.3]
C: The fix.
[reveal: v-579]
[pause: 0.45]
C: Synthetic probes in every region create a link and follow it through the edge, every minute: redirect latency, success, and the time from create to first redirect. And every hour, a test link is blocked and timed until every layer answers four-ten. Prometheus records it, and alerts page on these, not on boxes.
[reveal: v-580]
[pause: 0.45]
C: That's our service level indicator: what the user gets, end to end, per region. Takedown time measured, not hoped for.
[reveal: v-581]
[pause: 0.45]
C: Rejected: an outside uptime checker alone. One vantage point that sees only the edge: never create-to-redirect, never a takedown.
[pause: 1.1]

[slide: v-582]
[pause: 1.0]
C: Symptom pairs: two metrics, one cause.
[reveal: v-583]
[pause: 0.45]
C: Hit rate down with store reads up and traffic flat: a cold or misconfigured cache, not more users. That's this trace, caught at two, not nine.
[reveal: v-584]
[pause: 0.45]
C: Four-oh-fours up while creates are flat: someone is scanning codes.
[reveal: v-585]
[pause: 0.45]
C: p ninety-nine up while hit rate is flat: something synchronous crept onto the redirect path.
[reveal: v-586]
[pause: 0.45]
C: Click drops up with buffers full: Kafka or Flink is slow, not the redirect.
[reveal: v-587]
[pause: 0.45]
C: Takedown time up with consumer lag on the invalidation topic: the channel is behind, and the lifetimes are carrying us.
[pause: 1.0]

[slide: v-588]
[pause: 1.3]
C: The probe as a sequence.
[reveal: v-589]
[pause: 0.45]
C: Create a test link.
[reveal: v-590]
[pause: 0.45]
C: Two-oh-one.
[reveal: v-591]
[pause: 0.45]
C: Follow it through the edge.
[reveal: v-592]
[pause: 0.45]
C: Three-oh-two in six milliseconds, create to first redirect in under half a second.
[reveal: v-593]
[pause: 0.45]
C: Hourly, block a test link.
[reveal: v-594]
[pause: 0.45]
C: And poll every layer until four-ten. Today, seventy-four seconds, against five minutes.
[pause: 1.1]

[slide: v-595]
[pause: 0.6]
I: The probes pass, but one country's D-N-S sends users to the wrong region.
[pause: 2.0]

[slide: v-596]
[pause: 0.6]
C: The probes prove the path works. They don't prove users reach the right path.
[reveal: v-597]
[pause: 0.45]
C: So add real-user monitoring from edge logs, per country: latency and which region answered.
[reveal: v-598]
[pause: 0.45]
C: When probes are healthy and one country is slow, that divergence is the alert, and it says routing, not our servers.
[pause: 0.8]

[slide: v-599]
[pause: 0.7]
V: If asked, I'd say: I measure the path, not the boxes. Probes create a link and follow it in every region, and a test takedown every hour is timed until every layer answers four-ten. Then pairs of metrics give me causes: hit rate down with store reads up means a cold cache, not more traffic.
[pause: 1.6]

[pause: 1.4]

## 8 Build cost

[slide: v-600]
[pause: 1.2]
C: Build cost. This is the manager layer, marked aux: skip it in a pure Staff round, use it in a manager round.
[pause: 1.8]

[slide: v-601]
[pause: 1.0]
C: Three releases.
[reveal: v-602]
[pause: 0.45]
C: Scope. Version one, one service and one table with random codes and a cache. Version two, split paths, etcd ranges, the permutation and sharded PostgreSQL. Version three, the in-process cache, the click pipeline, the takedown channel, the C-D-N and regions.
[reveal: v-603]
[pause: 0.45]
C: People: two engineers, then two more, then a team of five or six.
[reveal: v-604]
[pause: 0.45]
C: Time: six weeks, two months, two quarters.
[reveal: v-605]
[pause: 0.45]
C: And on-call grows with it: business hours, a shared rotation, then twenty-four-seven with error budgets.
[pause: 1.0]

[slide: v-606]
[pause: 0.6]
C: If asked to split it across two teams for a quarter.
[reveal: v-607]
[pause: 0.45]
C: Links and redirect, owning create, codes, store, caches and the edge, and the redirect objective.
[reveal: v-608]
[pause: 0.45]
C: And clicks and trust, owning the event pipeline, stats, the takedown service and the classifier.
[reveal: v-609]
[pause: 0.45]
C: The contract between them is two things: the click event schema, and the invalidation topic.
[pause: 0.8]

[slide: v-610]
[pause: 1.0]
C: Buy, build, or don't.
[reveal: v-611]
[pause: 0.45]
C: PostgreSQL, Redis, Kafka and ClickHouse are bought, managed.
[reveal: v-612]
[pause: 0.45]
C: The edge is bought.
[reveal: v-613]
[pause: 0.45]
C: The classifier is bought or an internal service.
[reveal: v-614]
[pause: 0.45]
C: What we build is small: code generation, the redirect and the takedown path.
[reveal: v-615]
[pause: 0.45]
C: And if shortening is not the business, the right answer may be: don't build it, use an off-the-shelf shortener. Say it.
[pause: 1.0]

[slide: v-616]
[pause: 0.6]
C: Cost, illustrative. A handful of redirect pods, a hundred gigabytes of Redis, eighteen terabytes of PostgreSQL. The edge is billed per request, and at ten billion a month it's the largest line, which is why its default lifetime is a business decision.
[reveal: v-617]
[pause: 0.45]
C: Top risks. The code format is a one-way door: codes are printed on paper and live forever. Takedown time untested until a real incident. And analytics quietly becoming billing without the exactness work.
[pause: 0.8]

[pause: 1.4]

## 9 Recap

[slide: v-618]
[pause: 1.2]
C: To close: one picture, one sentence per path, the mistakes to avoid, and the thesis.
[pause: 1.8]

[slide: v-619]
[pause: 1.3]
C: The final picture, drawn once more in the order a request meets it.
[reveal: v-620]
[pause: 0.45]
C: The redirect across the middle: browser, edge, redirect service with its in-process cache, Redis, PostgreSQL.
[reveal: v-621]
[pause: 0.45]
C: And a replica per region.
[reveal: v-622]
[pause: 0.45]
C: Create on top: a safety check, the create service with its permutation, and etcd's leased ranges, inserting under the constraint.
[reveal: v-623]
[pause: 0.45]
C: Along the bottom: the click log, the aggregator and the stats.
[reveal: v-624]
[pause: 0.45]
C: The takedown with its invalidation channel.
[reveal: v-625]
[pause: 0.45]
C: And probes in every region, following the path a user takes.
[pause: 1.1]

[slide: v-626]
[pause: 1.0]
C: Four paths, one sentence each.
[reveal: v-627]
[pause: 0.45]
C: Create: check the U-R-L, lease, permute, insert under the constraint.
[reveal: v-628]
[pause: 0.45]
C: Redirect: memory, then Redis, then PostgreSQL; answer; then count.
[reveal: v-629]
[pause: 0.45]
C: Count: buffer, Kafka, Flink, ClickHouse, and say how fresh.
[reveal: v-630]
[pause: 0.45]
C: Withdraw: status, a direct delete, invalidate, purge, and lifetimes that sum to under five minutes.
[pause: 1.0]

[slide: v-631]
[pause: 1.0]
C: Eight fixes, each with its property.
[reveal: v-632]
[pause: 0.45]
C: Ranges and the constraint, for uniqueness.
[reveal: v-633]
[pause: 0.45]
C: A keyed permutation, against enumeration.
[reveal: v-634]
[pause: 0.45]
C: In-process caching with single flight, for the viral link.
[reveal: v-635]
[pause: 0.45]
C: Three-oh-two by default, for counting and takedowns.
[reveal: v-636]
[pause: 0.45]
C: Status, a direct delete and bounded lifetimes, for the five minutes.
[reveal: v-637]
[pause: 0.45]
C: Counting after the answer.
[reveal: v-638]
[pause: 0.45]
C: Regional replicas and I-D slices.
[reveal: v-639]
[pause: 0.45]
C: And probes that measure the path.
[pause: 1.0]

[slide: v-640]
[pause: 0.6]
C: Ten mistakes.
[reveal: v-641]
[pause: 0.45]
C: In the design: hash and truncate with no collision story. Six characters without the arithmetic. Check, then insert. A counter update on every click. Codes that are a counter in disguise.
[reveal: v-642]
[pause: 0.45]
C: In judgment: add a cache, with no plan for one hot key. Three-oh-one by default. Forgetting that every cached copy must be withdrawable. No number on the takedown time. And naming a product you cannot defend one level down.
[pause: 0.8]

[slide: v-643]
[pause: 0.7]
V: The redirect is the product, so it's one memory read, and nothing waits on anything else. Codes are unique because each server owns a block and the database has the last word, and unguessable because a key shuffles them. Everything else, counting, takedowns, the edge, lives beside the redirect, with a number on how late it may be.
[pause: 1.2]
C: Thank you. I'll stop there.
[pause: 1.6]
