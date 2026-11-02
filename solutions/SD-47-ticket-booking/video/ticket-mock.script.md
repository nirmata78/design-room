# Ticket booking mock round (video), v2

<!-- Video script for ~/.claude/skills/slide-video-kit/scripts/build_video.py. [slide: v-NN] = video/frames/v-NN.png;
     NN is also the number printed on every slide. Speakers: I interviewer · C candidate · V candidate, key line
     (slower) · N coach. [pause: s] = silence. Content follows ../SD-47_Ticket_Booking_Reference_Design.md.
     v2 2026-10-29: Staff L6/L7 depth (calculations, wire formats, ERDs, alternatives); the EM layer is marked AUX.
     Target ~38 min, hard limit 45. v1 (EM framing, 28 min) is in .v1-em-2026-10-28/. -->
<!-- voices: N=af_heart@0.92 I=bf_emma@0.95 C=am_michael@0.9 V=am_michael@0.84 -->
<!-- labels: N=COACH -->
<!-- say: NOWAIT=no-wait ZADD=Z-add ZRANK=Z-rank INCR=increment HGET=H-get SETNX=set-N-X Lua=Loo-ah -->

## Before you start

[slide: v-01]
N: This is a mock system design round at the Staff engineer bar, level six or seven, the way FAANG and other top-tier companies run it. The prompt is ticket booking under contention. You'll hear the interviewer, the candidate as they should sound, and me, between the stages. Then five follow-ups. Listen once, straight through. On the second pass, pause after every question and answer it yourself first. Every slide has a number in the corner, so you can point at one when you give feedback.

[slide: v-02]
N: Know what's being weighed. At Staff, depth counts more than once: the claim, the waiting room, the seat map and the payment, each two or three levels down. Every choice is defended against its alternatives, with numbers. Slides marked A-U-X are the engineering-manager layer: phasing, teams, roadmap. Say them in a manager loop. In a Staff round, you can skip them.

## Requirements

[slide: v-03]
I: Let's start. Design ticket booking for a stadium. Fifty thousand seats, and a million people trying to buy them the moment sales open.

C: Before I draw anything, five or six questions. Each one will change a box.

[slide: v-04]
C: First. Can we ever oversell?

I: Never.

C: Then every seat has exactly one place where its state lives, and changing it is atomic. Second. Do fans pick specific seats from a map, or do we choose the best available?

I: Specific seats, from a map.

C: So two fans clicking the same seat is a real collision. Contention is per seat, not on one counter.

[slide: v-05]
C: How long does checkout take? And how does payment behave?

I: About three minutes. Payment goes to an external provider. Two to ten seconds, and sometimes it times out without an answer.

C: Two consequences. I can't hold a database transaction open for three minutes, so a reservation has to be data: a hold, with an expiry. And "didn't answer" is not "declined". The customer may have been charged. So seats must never be released while the payment outcome is unknown.

[slide: v-06]
C: Fairness. What does fair mean here, and who decided?

I: People expect first-come. A queue or a lottery is fine, if you argue it.

C: Then I'll surface it as a product decision, for the promoter. And the seat map, how fresh must it be?

I: Within a couple of seconds.

C: Then it can be a cached snapshot. Out of scope, said aloud: search, pricing, resale, the refunds screen, and the app itself.

N: Six questions, and each one visibly moved a box. That's the requirements bar at any level.

## The thesis

[slide: v-07]
C: Before boxes, the framing.

V: Turn a stampede into a metered stream.

[pause: 1.0]

C: A million people can't be allowed to fight over fifty thousand rows. So the design is mostly about where people wait, what they read while waiting, and how fast they're let through. Selling to the people who get in is a normal transactional system, once the stampede is gone.

[slide: v-08]
C: The targets. Zero oversell, as a hard invariant. The opening minute must not fall over. Holds answer in under three hundred milliseconds at p ninety-nine. The map is at most two seconds stale. And no seat is ever stuck in limbo.

## Back of the envelope

[slide: v-09]
C: I'll show the arithmetic, because the consequences are what matter. Fifty thousand seats, at two and a half per order, is twenty thousand orders. Twenty thousand out of a million is two percent.

V: This is mostly a system for saying no, quickly and fairly.

[pause: 0.8]

C: Without a queue: a million fans, each trying about twice in the first minute, is two million attempts over sixty seconds, thirty-three thousand contended writes a second on fifty thousand rows. The database doesn't slow down; it stops. And joins: a million over sixty seconds is seventeen thousand a second, but arrivals bunch at the start, so three times that, fifty thousand a second. A join must be one in-memory operation, never a database row.

[slide: v-10]
C: Now Little's law: the number inside equals the rate in times the time each one stays. We decide the shop can serve ten thousand shoppers well. Each stays about five minutes, three hundred seconds. So the admission rate is ten thousand divided by three hundred, thirty-three a second, two thousand a minute. At seventy percent conversion, twenty thousand orders need twenty-nine thousand admissions, which at two thousand a minute is about fifteen minutes to sell out. Polling: a million fans every ten seconds is a hundred thousand requests a second. Cached at about two hundred C-D-N edges for one second, the origin sees about two hundred. And with adaptive polling, the nine hundred and fifty thousand fans far back poll every thirty seconds instead of ten, which brings the edge load to about thirty-seven thousand a second.

[slide: v-11]
C: The core. Ten thousand shoppers refreshing the map every two seconds is five thousand reads a second, and fifty thousand seats at one bit each is six point two five kilobytes. Holds: thirty-three admissions a second, times one and a half attempts, is about fifty a second, and I plan for ten-times bursts, five hundred. Payments: twenty thousand orders over about nine hundred seconds is twenty-five a second, and at up to ten seconds each, two hundred and fifty in flight. Storage, a year, for the whole platform: about a hundred and twenty gigabytes of seat rows and three hundred of orders. Storage is not the problem.

[slide: v-12]
C: Read the funnel left to right. A hundred thousand polls at the C-D-N. Two hundred at the origin. Thirty-three admissions into the shop. Five thousand cached map reads. Fifty to five hundred holds. Twenty-five payments. Each layer shrinks the number below it, and each box has its calculation written on it.

I: Mm-hm. Go on.

N: Every number shown as a calculation, and every calculation tied to a box. That's the Staff estimation bar.

## The A-P-I

[slide: v-13]
C: The endpoints follow the fan. Join the queue. Ask your number once, after the draw. Poll the shared state through the C-D-N. Exchange the queue token for an admission token. Fetch the layout, which never changes, and the availability, by version. Hold seats. Place an order, and poll it. And a webhook for the payment provider. Every mutating call carries an idempotency key, and everything after admission needs the admission token.

[slide: v-14]
C: Here's the join, on the wire. The response is a signed queue token, the kind, lobby or queue, and the server's clock for the countdown. Decoded, the token carries the event, the user, and after the draw, the fan's sequence number, signed with Ed25519, with a key I-D so we can rotate keys. Because it's signed, a position can't be forged or traded, and any waiting-room node can verify it without a lookup.

[slide: v-15]
C: And this is exactly what a waiting fan gets from the C-D-N. About ninety bytes of J-S-O-N: admitted up to thirty-one thousand eight hundred, the rate per minute, two flags, and the server time. Cache-Control public, max-age one second, stale-while-revalidate two, stale-if-error thirty. There's no user in the body, so one cached object serves a million people. The client does the subtraction itself: its own seq minus the pointer. Fan three hundred and eighty thousand, at pointer thirty-one thousand eight hundred, is about three hundred and forty-nine thousand back, which at two thousand a minute is about a hundred and seventy-four minutes, long after the fifteen-minute sell-out. So we can honestly say "likely sold out" early.

I: Why one second, and not ten?

C: Origin load is edges divided by the time to live, so at one second it's already negligible. Freshness is set by the client's ten-second poll, so one second adds almost nothing. Ten seconds would make the line jump in steps of three hundred and slow the sold-out message to a million people.

[slide: v-16]
C: Admission. The client posts its queue token. If its seq is at or below the pointer, it gets a J-W-T, valid ten minutes. Too early is a four twenty-five, with how far ahead the pointer is. A second admit returns the same token, never a fresh ten minutes; once the window is used, it's a four-ten. The J-W-T says: this user may shop this event until ten fourteen, with an I-D we can revoke. It's signed with a private key that only the waiting room holds. Gateways have the public key, so a compromised gateway can't mint tokens, and the check costs microseconds with no network hop.

[slide: v-17]
C: The availability map, byte by byte. Seat I-Ds are dense, zero to forty-nine thousand nine hundred and ninety-nine, so seat i is bit i. One means free; zero means held, pending or sold. Fifty thousand bits is six thousand two hundred and fifty bytes. The version is the Kafka offset of the last applied seat event. A client that already has the current version gets three-oh-four with no body: five thousand requests a second at about two hundred bytes is one megabyte a second, instead of thirty-one. The layout, positions and prices, is separate and immutable, on the C-D-N for a year.

[slide: v-18]
C: Holds. The request is just the seat I-Ds, with the admission token and an idempotency key. Two-oh-one means you got all of them, with the hold I-D and the expiry. Four-oh-nine means at least one was taken, and the body is the same bitmap structure, fresh, so the next click lands on a free seat without a second round trip. Four twenty-nine for the per-account limit. A retried click with the same key gets the same answer, never a second hold.

[slide: v-19]
C: Orders are asynchronous. The client sends the hold and a payment token from the provider's card form; we never see a card number. We answer two-oh-two, pending, immediately, and the client polls. Holding the request open for ten seconds would pin two hundred and fifty connections at the peak; this pins none.

## Data model

[slide: v-20]
C: The inventory database, as an E-R-D. Event, one row per show. Event seat, one row per seat per event, fifty thousand for this show, partitioned by hash of event I-D. The primary key is event and seat. State is one of four, with a check constraint. The hold is a hold I-D and an expiry on the seat row: data, not a lock. A partial index on held rows only, so the sweeper's query touches thousands of rows, not fifty thousand. The hold table carries the user and the idempotency key, unique together. And the outbox row is written in the same commit. The seat row is the truth; the hold row is bookkeeping.

[slide: v-21]
C: Orders live in a separate database, owned by the order service, because the inventory database is the hottest resource in the system. Orders: unique on hold I-D, so one order per hold, ever. Money as numeric, never a float. Payment attempts carry the key the provider deduplicates on. And tickets have a unique constraint on event and seat. That's the second, independent guard against oversell: even if our code had a bug, the database refuses the second ticket.

[slide: v-22]
C: The waiting room is seven Redis keys per event. The phase. The lobby, a sorted set of users with a secret random score, about a hundred megabytes for a million fans. The last issued seq. The admission pointer. The rate and the sold-out flag. Per-user admission markers. And the versioned map. Every key has the event in braces, a Redis Cluster hash tag, so all of one event's keys sit on one node and one Lua script can change them atomically. Different events spread across nodes.

## Technology, against the alternatives

[slide: v-23]
I: Why PostgreSQL for the seats? Redis would be faster.

C: Faster isn't the bottleneck after the queue; correctness is. The hold is a multi-row, all-or-nothing change guarded by a condition, which is exactly a relational transaction with row locks. With a synchronous replica, an acknowledged hold survives failover. Redis replicates asynchronously: a hold is acknowledged, the primary dies, the replica is promoted without it, the seat is free again, and two people pay. That's oversell. DynamoDB or Cassandra: multi-item conditional writes are limited or expensive, and lightweight transactions are slow exactly under contention. Spanner or Cockroach would work, but global serialisability is something we don't need: one event lives in one region, and five hundred writes a second fit one primary.

[slide: v-24]
C: For the queue, the opposite trade. Fifty thousand trivial operations a second at T0, no joins, and losing a second is survivable. Redis runs commands one at a time, so increment and Lua scripts are atomic without locks. PostgreSQL would be fifty thousand inserts a second for data that doesn't need durability. Kafka sounds like a queue, but we ask "what's my position?" and "advance by thirty-three", not "consume the next message". And in-process memory has no shared pointer. What Redis can lose, about a second with fsync every second, is fine: each fan's seq lives in their signed token.

[slide: v-25]
C: For fan-out, Kafka, fed by a transactional outbox. The seat change and its event commit together, Debezium reads them from the write-ahead log, and per-event order comes from keying by event I-D. A dual write from the application loses the event on a crash between the commit and the publish, and the map shows a sold seat as free. Polling the seat table puts five thousand reads a second back on the hot database. And a plain queue like S-Q-S has no replay, so we couldn't rebuild a snapshot.

[slide: v-26]
C: For telling a million people, polling a cached file at the C-D-N. WebSockets would mean a stateful fleet holding a million sockets to push one number a second, and if that fleet dies, fans see nothing. If the C-D-N can't refresh, fans see a number one second older. Server-sent events are a fine upgrade later, for the ten thousand admitted shoppers' map deltas.

[slide: v-27]
V: One store for everything would be too weak for the seats, or too expensive for the queue.

[pause: 0.8]

N: Four stores, each against its rejected alternative, with the failure that rules the alternative out. That's what "justify your stack" means at Staff.

## High-level design

[slide: v-28]
C: The system context. A million fans arrive at the edge, the C-D-N and the web firewall. Promoters set the sale. Two outside dependencies shape everything: the edge, which absorbs the million, and the payment provider, which is slow, and sometimes silent.

[slide: v-29]
C: The first container view: the waiting path and the read path. Fans join the waiting room, which writes to Redis. The admission controller moves the pointer every second. The queue state is served through the C-D-N. The gateway checks admission tokens, and the seat-map service reads a snapshot in Redis. It never touches the database.

[slide: v-30]
C: The write path. The inventory service makes the atomic claim in PostgreSQL and writes the outbox in the same transaction. Debezium publishes to Kafka. The order service runs checkout against the payment provider, with its own database. A sweeper cleans up expired holds, off the critical path.

I: Why so many boxes for fifty thousand seats?

C: Because there are three different load shapes.

[slide: v-31]
V: The queue path is huge. The read path can be stale. The write path must be correct.

[pause: 1.0]

C: Mixing any two is how ticket sites fall over. The classic failure is a seat-map read that queries the inventory database. Five thousand reads a second compete with the holds, the holds slow down, people retry, and the database melts under traffic that was never meant to reach it.

## Deep dive one: the seat

[slide: v-32]
I: Two fans click the same seat, in the same millisecond. What happens?

C: The risk is a read-then-write race. Both read "free", both write "mine", both pay.

[slide: v-33]
C: Follow it. Fan A asks for one-oh-one and one-oh-two. The inventory service locks those rows in seat order, with no-wait. Fan B asks for one-oh-two and one-oh-three. Its lock on one-oh-two fails immediately, so B gets a four-oh-nine with a fresh map. A's update succeeds on both rows, the hold and the outbox row are written, and A has two seats for five minutes.

[slide: v-34]
C: Here's the transaction. Lock the requested rows in ascending order, with no-wait. Then one conditional update whose WHERE clause is the availability check: the seat is available, or it's held and the hold has expired. That second branch is lazy expiry. If fewer rows come back than were asked for, roll back and answer four-oh-nine. All or nothing. Then the hold row and the outbox row, in the same commit.

[slide: v-35]
I: Why not a distributed lock? Or serialisable isolation?

C: A Redis lock per seat is a second system with its own failure modes, and its lease can expire in the middle of my transaction. Serialisable is correct, but under contention it aborts many transactions, and I add retries for nothing. Optimistic versions per seat still end in a conditional update for multi-seat claims, so I write that directly. Without no-wait, losers queue while holding connections, and on the front row the pool empties. And locking in request order deadlocks: one-oh-two then one-oh-one against one-oh-one then one-oh-two, and PostgreSQL only breaks it after a second. Read Committed is enough here, because a writer that waited re-checks its WHERE clause against the new version of the row.

[slide: v-36]
C: Inside the inventory service: the hold A-P-I handles idempotency and per-account limits. The claim engine and the outbox writer share one transaction. A freeze-and-sell component serves checkout. The sweeper runs on its own.

N: Risk, mechanism, failure case, and five rejected alternatives each with a reason. That's three levels down.

## Deep dive two: the waiting room

[slide: v-37]
I: A million people arrive at ten o'clock. Where do they wait, and how do they get in?

[slide: v-38]
C: They wait in a lobby that opens before the sale. Joining puts the fan in a sorted set with a secret random score, and returns a signed token and the server's clock. At ten, the lobby closes. The sorted order is the lottery. Each fan asks "what's my number?" once, after a random delay of up to twenty seconds, so they don't all ask in the same millisecond. Anyone arriving later just gets the next number.

[slide: v-39]
C: The join is one Lua script, so the phase check and the write are atomic, and a join racing the T0 flip lands cleanly on one side. In the lobby, a Z-add with N-X, so re-joining keeps the first draw. After T0, an existing seq is returned, so re-joining is idempotent. Otherwise, increment the counter for a plain first-come number. At T0, a million number lookups spread over twenty seconds is fifty thousand Z-ranks a second, each about twenty steps for a million entries. That fits one node. If it didn't, I'd precompute every seq into a hash once, and the lookup becomes an H-get.

[slide: v-40]
C: Then they wait. The browser polls the shared state, computes its own position, and when its number comes up, exchanges the queue token for an admission token, once.

[slide: v-41]
I: Who decides how fast the pointer moves?

C: The admission controller, every second, per event. It reads shop health: active shoppers, hold latency, database C-P-U, payment errors. If hold p ninety-nine is above three hundred milliseconds, C-P-U above seventy percent, or payment errors above five percent, it multiplies the rate by zero point seven. Otherwise, below ten thousand shoppers, it adds a small step. Additive increase, multiplicative decrease, like T-C-P. It starts slowly at ten, because every cache is cold. Then a Lua script advances the pointer by the rate over sixty, never past the last issued number. One leader per event, through a lease renewed every second, because two controllers would admit double.

[slide: v-42]
C: And telling the ninety-eight percent, in two stages. "Likely sold out" when the seats left, divided by two and a half, are fewer than the fans still shopping: stop admitting, and say so. Then "sold out" when nothing is available or held for a few minutes. If seats come back, resume from the pointer. Both flags travel in the same cached J-S-O-N, so nine hundred and seventy thousand people know within one poll.

[slide: v-43]
V: A waiting fan costs us almost nothing.

[pause: 1.0]

C: A signed number in their token, and one cached pointer for everyone. The core only ever sees what it chose to admit.

N: The weak answer here is "a rate limiter". The Staff answer is a cached pointer, a Lua join, a lottery, and a feedback-controlled rate, each with its numbers.

## Deep dive three: the seat map

[slide: v-44]
I: Ten thousand shoppers refresh a fifty-thousand-seat map every two seconds. Where does that read come from?

C: Not from the inventory database.

[slide: v-45]
C: A hold commits the seat change and an outbox row together. Debezium tails the write-ahead log and publishes to Kafka, keyed by event. A snapshot builder consumes in order and flips bits in memory. At most once a second it writes a new version of the bitmap to Redis, keyed by its Kafka offset, and then flips the pointer to that version. The A-P-I compares the client's version with the pointer and answers two hundred with the bitmap, or three-oh-four.

[slide: v-46]
C: The decisions inside. Publish at most once a second: there are about fifty seat changes a second, and one version a second keeps most two-second polls at three-oh-four. The Kafka offset as the version, because it only grows, survives a restart, and two builders agree on it. Write the bytes first and flip the pointer last, so no reader sees a version that isn't there. Not on the C-D-N, because it's admitted users only, and five thousand a second is easy for Redis. And a second or two of staleness is fine, because the claim is authoritative: a stale click fails fast with a fresh map.

## Deep dive four: holds

[slide: v-47]
I: A fan holds two seats, and closes the laptop.

C: Release too late, and the seats are lost. Too early, and we sell them twice. So two expiry paths, each covering the other's gap.

[slide: v-48]
C: The first is lazy expiry, inside the claim: an expired hold counts as free. So correctness never depends on any job. The second is the sweeper, which makes released seats visible on the map.

[slide: v-49]
C: The sweeper selects expired held rows for this event, oldest first, five hundred at a time, with skip-locked, and sets them available in the same statement, plus a seats-released outbox row. Skip-locked, because the sweeper wants any expired seats and should step over one a buyer is claiming right now. The buyer uses no-wait, because they want these specific seats. Every five seconds, five hundred a batch, that's up to a hundred releases a second, with short locks, and several sweepers can run in parallel. It never touches payment pending.

[slide: v-50]
C: The seat's state machine: available, held, payment pending, sold. Payment pending is the state weak designs miss. If the sweeper dies, we get staleness, not oversell, and an alert on the age of the oldest expired hold.

## Deep dive five: the payment

[slide: v-51]
I: Here's the hard one. The hold expires at four fifty. The payment provider takes fifteen seconds. Then it says approved.

C: There's no perfectly clean answer, so I'll take a position.

[slide: v-52]
C: First, prevent it. When the order is placed, I freeze the seats before calling the provider. Then I authorise the card, which only reserves the money. On approval, the seats become sold and tickets are issued. Only then do I capture.

[slide: v-53]
C: The freeze is one conditional update: held becomes payment pending, with a ten-minute deadline, only where the hold is still mine and not expired. Fewer rows, and the fan is told their hold expired, before any money moves. Then the order of money. Authorise, keyed by order I-D, so a retry is never a second charge; backing out is a void, which the customer never sees. Sell, with the unique ticket constraint. Capture last; backing out after that is a refund.

[slide: v-54]
C: Second. Unknown is not failure. If the provider times out, the order becomes unknown, because the money may have moved. Seats stay frozen. A reconciler asks the provider for the status by our key, and the webhook may arrive too. The first definite answer wins, and confirming is idempotent. Past the deadline, we cancel the authorisation and release the seats. If the provider still reports success after that, we refund automatically and give that fan priority on the waitlist. It's rare, measured, and has an owner.

[slide: v-55]
V: I'd rather hold a seat ten extra minutes than sell it twice.

[pause: 1.0]

C: The cost is slightly slower sell-through at the very end. That's a trade-off I'd show the product owner, explicitly.

N: This is the probe that separates levels. The traps: treating a timeout as a decline, or holding a transaction open across the provider call.

## Under load and failures

[slide: v-56]
I: What if twice as many people show up?

C: Nothing in the core changes, because the rate is set by shop health, not demand. Every layer sheds before the next one hurts. If the C-D-N can't reach us, it serves the last state, and the line pauses. The gateway sheds traffic without a token first. If the database struggles, the controller cuts the rate. If the provider fails, the breaker opens and seats stay frozen. And there's jitter on everything synchronised.

[slide: v-57]
I: The promoter wants to release five thousand more seats, mid-sale.

C: Insert them as available rows in one transaction, bump the layout version, clear the sold-out flag, and the controller resumes. The claim path doesn't change. A waitlist is a new consumer of released seats. Best available is a server-side allocator that actually reduces contention. And multi-region means each event's inventory is homed in one region.

[slide: v-58]
C: Failures. The inventory primary fails: the synchronous replica takes over in about thirty seconds, and the controller pauses admissions, so the queue absorbs it. A Redis node fails: admitted fans are unaffected, their tokens are stateless. The controller dies: its lease expires, another takes over, the line pauses. And every expiry uses the database's clock, never an application server's.

[slide: v-59]
C: Oversell has an S-L-O of zero: tickets issued must equal seats sold, checked every minute. Hold p ninety-nine under three hundred milliseconds. Approved to tickets within thirty seconds. And no seat in payment pending for more than fifteen minutes. Before the biggest sale, a million-fan load test and a game day.

## The EM layer, auxiliary

[slide: v-60]
N: The next two slides are the engineering-manager layer. In a Staff round, you'd say one sentence at most, or skip them.

C: The correctness core first. The M-V-P is six to eight weeks: holds, checkout, the claim path, a simple first-come queue, and a polled map. Then the lobby and lottery, bot defence, the waitlist, best available. With half the time, I'd cut features, never the invariant monitor.

[slide: v-61]
C: Teams along the three paths: edge and waiting room; inventory and orders, which owns the invariant; and payments. The contracts between them are the event stream and the admission token, so they ship in parallel.

## The close

[slide: v-62]
C: To close.

V: I chose correctness and graceful rejection over raw throughput.

[pause: 0.8]

C: A waiting room that meters a million people into a few hundred transactions a second, a six-kilobyte versioned bitmap for the map, and a relational claim path with time-limited holds. The biggest risk is the unknown payment outcome, watched by the payment-pending age and the oversell invariant. Next: bot defence, and best available.

I: Thanks. A few follow-ups.

## Follow-up 1: twenty dates at once

[slide: v-63]
I: A twenty-date stadium tour goes on sale at ten, for every date at once, and three other big shows open the same morning. What changes?

[slide: v-64]
C: Less than you'd think, because everything is keyed by event I-D: the Redis hash slot, the database partition, the Kafka key, the J-W-T's event claim, the C-D-N cache key. So events are independent by construction. It's an isolation problem, not a coordination problem. Hash tags put each event's keys on its own Redis node. The genuinely shared resources are the payment provider's capacity and edge bandwidth, so those get explicit budgets: a global admission budget split across events, weighted by their size. And the biggest on-sale gets a dedicated PostgreSQL host for its partition.

V: Keyed by event, everywhere. Budget only what's truly shared.

[pause: 0.8]

N: The design's partitioning choice paid off in a follow-up. Name the shared resources precisely; that's the Staff move.

## Follow-up 2: the failover

[slide: v-65]
I: Ten minutes into the biggest on-sale of the year, the inventory primary fails over. Walk me through it.

[slide: v-66]
C: In the first seconds, hold latency and errors spike, and on-call is paged. But the design does the first thing for us: the controller sees the signals and cuts admissions to the floor. The line pauses; fans see "the line has paused", not an error. After about thirty seconds, the synchronous replica is promoted, and nothing acknowledged is lost. The controller ramps up from a slow start, and shoppers retry with jitter. The same day, I check the invariant monitor and the payment-pending ages. The week after, a blameless review, and before the next sale, a game day.

V: The queue absorbs the outage. The database comes back to the load we choose to give it.

[pause: 0.8]

## Follow-up 3: fairness

[slide: v-67]
I: The promoter says the lottery looks rigged. They want strict first-come, first-served, at ten o'clock.

[slide: v-68]
C: It's their decision, and my job is to make it an informed one. Strict first-come at ten rewards whoever has the lowest latency and the best bots, at the millisecond. It looks fair, and it isn't. A lottery among everyone in the lobby gives each fan present the same chance. Verified pre-registration is the strongest against bots. I'd bring data from the last sale, the bot share and the latency spread, and address the real worry, which is trust: publish the rules before the sale, and show positions early.

V: I won't decide fairness alone, and I won't let it be decided without the data.

[pause: 0.8]

## Follow-up 4: the CDN bill

[slide: v-69]
I: Finance says the C-D-N bill for last month's on-sale was three times the forecast.

[slide: v-70]
C: Cost is polling rate, times response size, times audience. One of those moved. I'd slice by path: queue state, layout or availability. Then by client version: did a release start polling every second? Then by bot score. To contain it: block flagged bots at the firewall, raise the poll interval from the server, because it travels in the state file, and roll back the client. To fix it: adaptive polling, a cost forecast per on-sale reviewed before the sale, and an alert on edge requests per waiting fan.

N: The diagnosis order is the answer, and the fix touches neither fairness nor correctness.

## Follow-up 5: twelve weeks, auxiliary

[slide: v-71]
N: This last one is for engineering-manager loops. In a Staff round, it's unlikely.

I: Three teams. Twelve weeks until the biggest tour of the year. What ships, and what doesn't?

[slide: v-72]
C: Correctness first, scale second. Weeks one to four: the claim, holds and lazy expiry; the payment adapter with idempotency; a simple first-come queue with admission tokens. Weeks five to eight: freeze and authorise-then-capture, the unknown-outcome reconciler, the lobby, the cached queue state. Weeks nine to twelve: the invariant monitor, bot defence, a load test and a game day. What doesn't ship: the waitlist and best available.

V: I'd cut features before I'd cut the game day.

[pause: 0.8]

## Debrief

[slide: v-73]
N: Here's where the round lands at Staff. A senior candidate asks about oversell and holds; Staff says "ninety-eight percent will be rejected" and designs for it, with the arithmetic. Senior uses a conditional update; Staff adds sorted locks, no-wait, the fresh map, and why not serialisable. Senior draws a waiting room; Staff gives the cached pointer, the Lua join, the lottery and the controller. Senior lists tables; Staff shows the E-R-D, the wire formats and the six-kilobyte bitmap. And on payments, Staff says freeze, authorise, sell, capture, and unknown is not failure.

[slide: v-74]
N: Six checks, before the real round. "Mostly a system for saying no", with the arithmetic. Every number as a calculation, with its consequence. The wire formats: what the C-D-N, the bitmap and the four-oh-nine actually contain. Every store against its rejected alternatives. Payment pending, and unknown is not failure. And the manager layer only when the loop asks for it. Good luck.
