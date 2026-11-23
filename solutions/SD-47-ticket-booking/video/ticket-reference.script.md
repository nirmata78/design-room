# SD-47 Ticket booking under contention: reference solution (Staff L6/L7)

<!-- Video script for slide-video-kit/scripts/build_video.py. [slide: v-NNN] = frames/v-NNN.png; [reveal: v-NNN] = the next
     reveal step of the same slide. Generated from src/*.py: edit the sources, not this file. -->
<!-- voices: N=af_heart@0.92 I=bf_emma@0.95 C=am_michael@0.9 V=am_michael@0.84 -->
<!-- names: C=Candidate V=Candidate N=Coach I=Interviewer -->
<!-- say: TTL=T-T-L CDN=C-D-N API=A-P-I APIs=A-P-Is SQL=S-Q-L JWT=J-W-T FIFO=fifo WAF=waff SLO=S-L-O SLOs=S-L-Os SLI=S-L-I SLIs=S-L-Is HTTP=H-T-T-P HTTPS=H-T-T-P-S UUID=U-U-I-D ID=I-D IDs=I-Ds EM=E-M AUX=aux SRE=S-R-E PSP=payment_provider DB=database KB=kilobytes MB=megabytes GB=gigabytes TB=terabytes TLS=T-L-S HMAC=H-mac RPC=R-P-C SSE=S-S-E AIMD=A-I-M-D NOWAIT=no_wait CAPTCHA=capcha Redis=Reddis Kafka=Kafka Lua=loo-ah T0=T_zero SLA=S-L-A RAM=ram ETA=E-T-A p99=P-ninety-nine QPS=Q-P-S WebSocket=web_socket Postgres=Postgres PostgreSQL=Postgres_S-Q-L idempotency=idem-potency idempotent=idem-potent -->


## 0 Cold open

[slide: v-001]
[pause: 1.2]
C: A seat looks like a row with a boolean. Available, or taken. Anyone can write that in an afternoon. This question is not testing the boolean. It is testing what happens around it: a million people reaching it in the same second, a human who needs three minutes to pay, and a payment provider that sometimes does not answer.
[pause: 1.8]

[slide: v-002]
[pause: 0.6]
I: Design ticket booking for a stadium. Fifty thousand seats, and a million people trying to buy them the moment sales open.
[pause: 1.5]

[slide: v-003]
[pause: 1.3]
C: Here is the hook.
[reveal: v-004]
[pause: 0.45]
C: Fifty thousand seats at about two and a half a purchase is twenty thousand orders.
[reveal: v-005]
[pause: 0.45]
C: Twenty thousand winners out of a million fans: two percent.
[reveal: v-006]
[pause: 0.45]
C: Ninety-eight percent of the people who show up leave without a ticket, whatever we build.
[reveal: v-007]
[pause: 0.45]
C: The picture shows the load at each layer, which I derive in the estimates: it shrinks from a hundred thousand polls a second at the door to a few hundred writes at the database.
[reveal: v-008]
[pause: 0.45]
C: So this is mostly a system for saying no, quickly and fairly.
[reveal: v-009]
[pause: 0.45]
C: The cheap, honest no is a first-class feature.
C: A design that only works well for the two percent has failed the other ninety-eight.
[pause: 1.1]

[slide: v-010]
[pause: 1.0]
N: Five axes.
[reveal: v-011]
[pause: 0.45]
N: The weak signal is always the same shape:
[reveal: v-012]
[pause: 0.45]
N: a clean claim on a seat, and nothing about the million, the payment, or the day it fails.
[reveal: v-013]
[pause: 0.45]
C: I'll keep two failures in mind the whole way.
[reveal: v-014]
[pause: 0.45]
C: A seat sold twice, and a seat stuck so nobody can buy it.
[reveal: v-015]
[pause: 0.45]
C: Most designs defend the first and forget the second.
[pause: 1.0]

[slide: v-016]
[pause: 0.7]
V: This is not a booking system. It is a rejection system. Fifty thousand seats cannot be shared with a million people, so the design converts a stampede into a stream. Every seat has exactly one place where its state lives, and exactly one atomic way to change it.
[pause: 1.0]
C: Concretely: a waiting room at the edge that admits people at a rate the shop can serve. A seat with three states, not two. A claim that is one statement, not two. And a payment path that treats silence as a state of its own.
[pause: 1.6]

[slide: v-017]
[pause: 0.6]
C: The order I'll follow.
C: Requirements and scope, then numbers, then a short theory chapter the design can lean on.
[reveal: v-018]
[pause: 0.45]
C: Then the A-P-I and data, and a high-level design in three versions, each answering the objection to the one before.
[reveal: v-019]
[pause: 0.45]
C: Then the part I care about most: eight challenges that break the design, where each fix creates the next question.
C: A build cost, because someone has to own this.
C: And a recap.
[pause: 0.8]

[pause: 1.4]

## 1 Requirements and scope

[slide: v-020]
[pause: 1.2]
C: Before I draw anything I want to ask six questions. Each answer will change the design.
[pause: 1.8]

[slide: v-021]
[pause: 0.6]
C: Can we ever oversell?
I: Never.
I: Two people must not hold tickets for the same seat.
C: Then every seat has exactly one place where its state lives, and changing it has to be atomic.
C: If the answer had been a little is fine, I could use an eventually consistent counter and skip all of that.
[pause: 0.6]

[slide: v-022]
[pause: 0.6]
C: Do fans pick specific seats, or ask for best available?
I: Specific seats, from a map.
C: That makes each seat a row of its own, and contention per seat, not on one counter.
C: With best available the server chooses, and could avoid collisions entirely.
C: Here two fans can aim at the same seat, so I must resolve it.
[pause: 0.6]

[slide: v-023]
[pause: 0.6]
C: How long does checkout take?
I: Users need about three minutes to enter payment details.
C: A human typing a card number.
C: I cannot keep a database transaction open for minutes: it would pin a connection and a row lock the whole time.
C: So the reservation has to be data, a row with an expiry, and not a lock.
[pause: 0.6]

[slide: v-024]
[pause: 0.6]
C: What does fair mean here, and who decided?
I: You tell me.
I: First-come is expected, but a queue or a lottery is acceptable if you argue for it.
C: Then it is a product decision, and I will surface it to the promoter and not quietly assume one.
C: I'll bring it back in challenge five.
[pause: 0.6]

[slide: v-025]
[pause: 0.6]
C: How does the payment provider behave?
I: An external provider.
I: Two to ten seconds, and it can time out ambiguously.
C: Ambiguously means a timeout is not a decline.
C: The customer may have been charged.
C: So the outcome of a payment can be unknown, and seats must not be released while it is.
C: That one answer produces a whole state in challenge three.
[pause: 0.6]

[slide: v-026]
[pause: 0.6]
C: How fresh must the seat map be?
I: Within a couple of seconds.
C: Good.
C: If it had to be exact, every fan would need a live read of the database.
C: A couple of seconds stale means I can build a snapshot once a second and serve it from cache to everyone.
[pause: 0.6]

[slide: v-027]
[pause: 0.6]
C: Functionally, five things.
C: One, join the sale: a lobby before it opens and a place in line after.
[reveal: v-028]
[pause: 0.45]
C: Two, browse a seat map that is fresh to within a couple of seconds.
[reveal: v-029]
[pause: 0.45]
C: Three, hold specific seats for a limited time, atomically, never twice.
[reveal: v-030]
[pause: 0.45]
C: Four, pay once and get tickets once, whatever the provider does.
[reveal: v-031]
[pause: 0.45]
C: Five, release: seats come back on expiry or failure, and the promoter can add inventory.
C: Each of these gets a numbered flow later.
[pause: 0.8]

[slide: v-032]
[pause: 0.6]
C: The numbers.
C: They are initial targets, and I'll say so once for this chapter: none is a measurement.
C: Zero oversell.
C: That is an invariant, not a rate.
[reveal: v-033]
[pause: 0.45]
C: A hold answers in under three hundred milliseconds at the ninety-ninth percentile.
[reveal: v-034]
[pause: 0.45]
C: The seat map is stale by about two seconds at most.
[reveal: v-035]
[pause: 0.45]
C: And no expired hold goes unreleased for more than thirty seconds, so no seat sits in limbo.
C: Plus one that is not a number: the sale-opening minute must not fall over.
[pause: 0.8]

[slide: v-036]
[pause: 0.6]
C: In scope: a lobby and a line in front of the sale, the seat map, holds on specific seats, checkout with one external payment provider, expiry and release, the promoter adding seats, and bot controls from the first version.
C: Out of scope, on purpose. Event search and discovery. Pricing and dynamic pricing. The resale marketplace. The refunds interface. And the mobile app itself. Happy to pull any of these in, but I will spend the time on the contention path.
[pause: 0.8]

[slide: v-037]
[pause: 0.7]
V: The core is four things. An atomic claim on a three-state seat. A hold with two expiry paths. A waiting room that sheds load at the edge. And a payment path that treats unknown as a state.
[pause: 0.8]
N: Notice what the candidate did in six minutes. They asked what fair means and who owns it, they cut five things out loud, and every answer changed a box on the board. That is the framing signal.
[pause: 1.6]

[pause: 1.4]

## 2 Estimates

[slide: v-038]
[pause: 1.2]
C: Now the numbers. Every one is arithmetic from the inputs and carries a label: given, illustrative, derived or an initial target. Each has to change a decision, or I drop it.
[pause: 1.8]

[slide: v-039]
[pause: 1.0]
C: First number.
C: Fifty thousand seats divided by two and a half per order is twenty thousand orders.
C: Twenty thousand out of a million is two percent.
[reveal: v-040]
[pause: 0.45]
C: This is the number that reframes the design as a rejection system.
C: Decision: the no path gets as much design as the yes path.
[reveal: v-041]
[pause: 0.45]
C: Losers must not reach the database to learn they lost.
C: They wait in a line that costs almost nothing per person, and we tell them early.
[pause: 1.0]

[slide: v-042]
[pause: 1.0]
C: Second number.
[reveal: v-043]
[pause: 0.45]
C: Suppose everyone could reach the inventory database directly.
C: A million fans, two clicks each in the first minute, is two million attempts over sixty seconds: about thirty-three thousand writes a second, all aimed at the same fifty thousand rows, and really at the best few thousand seats.
[reveal: v-044]
[pause: 0.45]
C: That is not big, it is fatal.
[reveal: v-045]
[pause: 0.45]
C: Each write waits for a row lock while holding a connection, and there are only a few hundred connections.
C: The pool empties in milliseconds.
C: Decision: a waiting room that admits fans at a rate I choose.
C: At about thirty-three a second, the database sees roughly fifty holds a second, six hundred times less.
[pause: 1.0]

[slide: v-046]
[pause: 1.0]
C: Arrivals.
[reveal: v-047]
[pause: 0.45]
C: A million joins in the first minute is seventeen thousand a second on average, and about three times that in the first seconds: fifty thousand a second.
[reveal: v-048]
[pause: 0.45]
C: So a join is one in-memory operation, never a database insert.
C: And it argues for a lobby.
[reveal: v-049]
[pause: 0.45]
C: If the waiting room opens thirty minutes early, the same million joins arrive over eighteen hundred seconds: about five hundred and fifty a second.
C: The sale opening itself then carries no join spike at all.
[pause: 1.0]

[slide: v-050]
[pause: 1.0]
C: Polling.
C: A million waiting fans each asking where am I every ten seconds is a hundred thousand requests a second for as long as the line exists.
[reveal: v-051]
[pause: 0.45]
C: Too much for my origin, so the answer must be identical for every fan and cacheable at the edge.
[reveal: v-052]
[pause: 0.45]
C: The trick: not where am I, which differs per fan, but how far has the line moved, one number per event.
C: Each fan computes their own position locally from a number inside their signed token.
C: With a one-second lifetime and about two hundred edge locations, the origin sees two hundred requests a second instead of a hundred thousand.
[pause: 1.0]

[slide: v-053]
[pause: 1.0]
C: Admission rate.
C: Little's law: items in a system equal the arrival rate times the time each spends in it.
[reveal: v-054]
[pause: 0.45]
C: The shop is the system.
C: I decide ten thousand shoppers is comfortable.
[reveal: v-055]
[pause: 0.45]
C: A shopper spends about five minutes inside.
C: So the arrival rate that keeps ten thousand inside is ten thousand over five minutes: two thousand a minute, about thirty-three a second.
[reveal: v-056]
[pause: 0.45]
C: At seventy percent conversion, twenty thousand orders need about twenty-eight thousand six hundred admissions, which at two thousand a minute is about fourteen minutes.
[reveal: v-057]
[pause: 0.45]
C: So a fan at position four hundred thousand can be told honestly that they are unlikely to get in.
C: Decision: R is a dial sized by the shop, and the line shows an honest estimate.
[pause: 1.0]

[slide: v-058]
[pause: 1.0]
C: The seat map.
C: Ten thousand shoppers refreshing every two seconds is five thousand reads a second.
[reveal: v-059]
[pause: 0.45]
C: One bit per seat: fifty thousand bits is six and a quarter kilobytes.
[reveal: v-060]
[pause: 0.45]
C: At five thousand a second that is thirty-one megabytes a second as full bodies, but if clients send the version they have and get a not-modified answer when nothing changed, about one and a half.
[reveal: v-061]
[pause: 0.45]
C: Decision: the map is a bitmap served by version from a cache, and it never competes with the claims for the same rows.
[pause: 1.0]

[slide: v-062]
[pause: 1.0]
C: Writes after the line.
C: Each admitted fan tries about one and a half holds: fifty a second, with bursts ten times that, five hundred.
[reveal: v-063]
[pause: 0.45]
C: One PostgreSQL primary does thousands of short transactions a second, so even the burst fits with room.
C: Payments: twenty thousand orders over fifteen minutes is about twenty-five a second, each taking up to ten seconds, so about two hundred and fifty requests in flight.
[reveal: v-064]
[pause: 0.45]
C: That means checkout must be asynchronous, with a bounded pool to the provider.
C: And storage: about four hundred and twenty gigabytes a year.
[reveal: v-065]
[pause: 0.45]
C: I say it aloud to show I know it is not the problem.
[pause: 1.0]

[slide: v-066]
[pause: 1.3]
C: The hold request has a budget. Twenty milliseconds at the gateway, ten for the token and limits, forty for the lock and the claim, ten for the outbox write, twenty to return: a hundred used, two hundred spare, against three hundred. The spare is what the controller spends when a burst arrives. If hold latency eats it, that is the signal to cut the admission rate. Decision: latency is the dial's feedback.
[pause: 1.1]

[slide: v-067]
[pause: 0.6]
C: The headline.
C: This is not a big-data problem.
[reveal: v-068]
[pause: 0.45]
C: After the queue, the write path is a few hundred transactions a second.
[reveal: v-069]
[pause: 0.45]
C: All the scale is in the waiting room and the read path, so that is where I spend the design budget.
N: Each number above ended in a decision.
[reveal: v-070]
[pause: 0.45]
N: That is what the interviewer is writing down.
C: That is the numbers.
C: Next, theory.
[pause: 0.8]

[pause: 1.4]

## 3 Theory

[slide: v-071]
[pause: 1.2]
C: A short theory chapter before any design, so the design can lean on it. Six parts: what a booking system is and is not, the properties, the central tension, seven mechanisms, an options matrix, and the failure catalogue. Every slide here has a theory badge.
[pause: 1.8]

[slide: v-072]
[pause: 0.7]
V: A ticket booking system sells a fixed set of individually identified seats to many more buyers than seats, with a time-limited hold between free and sold, so that no seat is ever sold twice and no seat is ever stuck in limbo.
[pause: 1.0]
C: Each clause carries weight. A fixed set: inventory does not grow by accident. Individually identified: contention is per seat. Many more buyers: twenty to one turns most requests into refusals. A time-limited hold: a third state, data and not a lock. And never twice, never stuck: safety and liveness.
[pause: 1.6]

[slide: v-073]
[pause: 0.6]
C: Four neighbours.
C: It is not a lock: a lock belongs to a process and goes with it, but a hold is data with an expiry, so it survives a crashed server.
[reveal: v-074]
[pause: 0.45]
C: It is not a shopping cart: a cart promises nothing.
[reveal: v-075]
[pause: 0.45]
C: It is not an auction: price does not move, the contest is who gets there first.
[reveal: v-076]
[pause: 0.45]
C: And it is not a queue as a data structure: the line is a product experience with a position and an honest estimate, and it is also how we shed load.
[pause: 0.8]

[slide: v-077]
[pause: 0.6]
V: Safety: one seat never belongs to two orders, and money is never taken for seats we do not deliver.
[reveal: v-078]
[pause: 0.45]
V: Liveness: every seat is eventually sold or free again, every fan eventually learns where they stand, and the sale-opening minute does not take the system down.
[pause: 0.8]
C: Two safety properties, because there are two ways to be wrong.
[reveal: v-079]
[pause: 0.45]
C: S-one is the seat sold twice.
C: S-two is the payment and the seat disagreeing.
C: And three liveness properties, of which L-one is the one weak designs forget: a seat stuck in limbo is lost revenue.
C: Every fix from here says which property it serves.
[pause: 0.8]

[slide: v-080]
[pause: 1.3]
C: Here is the central tension. Demand is unbounded, supply and checkout capacity are not. The picture is a funnel. A million fans at the door, about ten thousand in the shop, about fifty holds a second, twenty thousand orders. Everything left of the shop is cheap and served at the edge. Everything right of it is expensive and protected.
C: And the trade the problem forces is fairness against load. The fairest line, strict first-come, rewards bots and low latency and invites refresh storms. The cheapest line, random admission, needs a product decision. Not consistency against availability: the inventory is a single-writer set of rows, so there is no replica disagreement to resolve. Hold that picture. Challenges four and five live on it.
[pause: 1.1]

[slide: v-081]
[pause: 0.6]
C: Mechanism one, the conditional claim.
C: It protects S-one.
[reveal: v-082]
[pause: 0.45]
C: One statement whose condition is the availability check, with rows locked in a stable order, and all or nothing across the seats.
[reveal: v-083]
[pause: 0.45]
C: It rules out the read-then-write race.
[reveal: v-084]
[pause: 0.45]
C: It costs contended rows on a single primary, and the loser gets a quick no.
[pause: 0.8]

[slide: v-085]
[pause: 0.6]
C: Mechanism two, the hold as data.
C: It protects liveness without holding a lock across a human.
[reveal: v-086]
[pause: 0.45]
C: The seat row says held, with a hold identifier and an expiry time, and nothing stays open.
[reveal: v-087]
[pause: 0.45]
C: It rules out a transaction open for minutes.
[reveal: v-088]
[pause: 0.45]
C: It costs a clock to trust, and a way to free seats nobody comes back to.
[pause: 0.8]

[slide: v-089]
[pause: 0.6]
C: Mechanism three, two expiry paths.
C: It protects liveness.
[reveal: v-090]
[pause: 0.45]
C: The claim itself treats an expired hold as free, so correctness never depends on a job.
C: A sweeper releases in small batches and announces it, so the map catches up.
[reveal: v-091]
[pause: 0.45]
C: It rules out seats stuck forever.
[reveal: v-092]
[pause: 0.45]
C: It costs staleness on the map while the sweeper is down.
[pause: 0.8]

[slide: v-093]
[pause: 0.6]
C: Mechanism four, admission control.
C: It protects the sale-opening minute.
[reveal: v-094]
[pause: 0.45]
C: A line, a pointer, and a rate chosen from the shop's health: increase slowly, cut fast.
[reveal: v-095]
[pause: 0.45]
C: It rules out a stampede on fifty thousand rows.
[reveal: v-096]
[pause: 0.45]
C: It costs the fans' time, a rate to tune, and an honest estimate to show.
[pause: 0.8]

[slide: v-097]
[pause: 0.6]
C: Mechanism five, freeze, authorize then capture, and unknown as a state.
C: It protects S-two.
[reveal: v-098]
[pause: 0.45]
C: Move the seats to payment-pending before the provider call.
C: Reserve the money first and take it last.
C: A silent provider means unknown, so ask again with the same idempotency key.
[reveal: v-099]
[pause: 0.45]
C: It rules out a double charge and a seat sold twice after a late approval.
[reveal: v-100]
[pause: 0.45]
C: It costs seats frozen for up to ten minutes, and a reconciler to run.
[pause: 0.8]

[slide: v-101]
[pause: 0.6]
C: Mechanism six, split reads.
C: It protects the fan's view and the database.
[reveal: v-102]
[pause: 0.45]
C: The layout is immutable on the edge.
C: Availability is a versioned bitmap built from the event stream.
C: The queue state is one cached answer for everyone.
[reveal: v-103]
[pause: 0.45]
C: It rules out a live map read from the claims database.
[reveal: v-104]
[pause: 0.45]
C: It costs a click on a stale seat, which fails gracefully with a fresh map.
[pause: 0.8]

[slide: v-105]
[pause: 0.6]
C: Mechanism seven, random admission and signed tokens.
C: It protects fairness.
[reveal: v-106]
[pause: 0.45]
C: Draw a random score at join time for everyone present at the start; late arrivals go first-come behind them.
C: Tokens are signed, short-lived and bound to the account.
[reveal: v-107]
[pause: 0.45]
C: It rules out bots winning the first millisecond, and forged positions.
[reveal: v-108]
[pause: 0.45]
C: It costs a product rule that has to be stated on the page.
[pause: 0.8]

[slide: v-109]
[pause: 1.0]
C: The options for the central decision: how do I stop two fans taking one seat across a three-minute checkout.
C: Three look cheap.
C: A: read the seat then write it.
C: Not atomic, so two readers both see free.
[reveal: v-110]
[pause: 0.45]
C: B: a row lock held through checkout.
C: Atomic, but a crashed server loses it, and it holds a connection for minutes: the pool empties and the database falls over.
[reveal: v-111]
[pause: 0.45]
C: C: a distributed lock per seat with a lease.
[reveal: v-112]
[pause: 0.45]
C: It sounds right.
C: But it is a second system whose failures I now own, and a lease can expire in the middle of the transaction, leaving two fans who both believe they hold the seat.
[pause: 1.0]

[slide: v-113]
[pause: 1.0]
C: Three that work.
C: D: serializable transactions.
C: Correct, but under contention most of them abort and retry.
[reveal: v-114]
[pause: 0.45]
C: E: an optimistic version column on each seat.
C: Fine for one seat, but a multi-seat all-or-nothing claim still ends in one conditional update, so I just write that.
[reveal: v-115]
[pause: 0.45]
C: F: one conditional update, with the hold as data and an expiry.
C: That is the pick.
C: What it gives up.
[reveal: v-116]
[pause: 0.45]
C: The hold can expire on a slow fan.
C: The hottest seats are contended rows on one primary, which is exactly why the waiting room exists.
C: And there must be a sweeper.
C: I take those costs knowingly.
[pause: 1.0]

[slide: v-117]
[pause: 1.0]
C: The failure catalogue, and it becomes the challenge list.
C: One: two fans on one seat.
[reveal: v-118]
[pause: 0.45]
C: Two: holds that outlive their owner.
[reveal: v-119]
[pause: 0.45]
C: Three: a hold expires while a payment is in flight.
[reveal: v-120]
[pause: 0.45]
C: Four: a stampede at the door.
[reveal: v-121]
[pause: 0.45]
C: Five: bots and an unfair line.
[reveal: v-122]
[pause: 0.45]
C: Six: a stale seat map.
[reveal: v-123]
[pause: 0.45]
C: Seven: requirements that arrive in the middle of the sale.
[reveal: v-124]
[pause: 0.45]
C: Eight: a failure nobody can see.
N: The order matters.
N: Each fix creates the next question, and the last one is always: how would you know?
[pause: 1.0]

[pause: 1.4]

## 4 API and entities

[slide: v-125]
[pause: 1.2]
C: The A-P-I before the boxes. It is the contract, and it shows whether I have thought about failure. Every call carries a tag: which requirement it serves, and which entity it reads or writes. Every call that changes something takes an idempotency key.
[pause: 1.8]

[slide: v-126]
[pause: 1.0]
C: The line. Join is one call that returns a signed queue token and the server's clock, so the countdown is the same for everyone. The token says: this user is in line for this event, either in the lobby or at number N. A join is one in-memory step, never a database row.
C: The poll returns three fields: how far the line has moved, the current admission rate, and whether it is sold out. There is no user identity in it. Every fan gets the same bytes, which is exactly why a C-D-N can hold it. The fan computes their own position from the number in their token.
[pause: 1.0]

[slide: v-127]
[pause: 1.0]
C: Admission. When the pointer has reached the fan's number, they exchange the queue token for an admission token, a signed pass valid ten minutes for this event. The server checks the condition, and the number is inside a token we signed, so a client cannot admit itself early.
C: Asking again returns the same token, never a fresh ten minutes. Otherwise a fan could refresh their window forever and occupy a shopping slot. The gateway checks the signature on every shop call: one check, no lookup, no network. And the token has an identifier, so a detected bot can be revoked.
[pause: 1.0]

[slide: v-128]
[pause: 1.0]
C: The map. The layout is the venue drawing and the seat identifiers. It never changes during a sale, so it comes from the C-D-N under a versioned address and is cached for a year. The availability is the live part: one bit per seat, six and a quarter kilobytes. The client sends the version it has. If nothing changed, the answer is a not-modified with no body.
C: Only admitted fans read it. And one point worth saying aloud: the map is a hint for the fan's eye. The claim is the authority.
[pause: 1.0]

[slide: v-129]
[pause: 1.0]
C: Holds and orders. A hold takes a list of seats and answers two-oh-one with an identifier and an expiry, or four-oh-nine with a fresh bitmap. All the seats or none. The four-oh-nine carries the current map so the fan's next click lands on a free seat without an extra request.
C: An order answers two-oh-two accepted, not two-hundred, because payment takes seconds. The fan polls for the result. And a webhook endpoint, signed by the provider and deduplicated by event identifier, is how we hear an outcome we might have missed. The idempotency key on both calls is what makes a double click harmless.
[pause: 1.0]

[slide: v-130]
[pause: 1.3]
C: The conceptual model. An event has seats. A seat is held by at most one hold at a time, and a hold may cover several seats. A hold becomes an order, one to one. An order has payment attempts, a weak entity: it only exists in the context of an order. An order issues tickets, and each ticket is for exactly one seat. Fans join an event through the line.
C: One fact matters most. A seat has at most one live hold, and the seat row is the truth. The hold row is bookkeeping. That is what makes the claim in challenge one safe.
[pause: 1.1]

[slide: v-131]
[pause: 1.3]
C: Physically, the inventory database, the hot one. The seat table is keyed by event and seat, partitioned by event. The seat identifier is dense, zero to forty-nine thousand nine hundred ninety-nine, so seat eight hundred twelve is bit eight hundred twelve in the availability map. The state is one of four values. A partial index covers only held rows, so the sweeper's query reads a few thousand rows, not fifty thousand.
C: The hold table carries the user, the seats, the expiry and the idempotency key, unique per user. And the outbox: a change to a seat and the event announcing it commit in one transaction, so they cannot disagree.
[pause: 1.1]

[slide: v-132]
[pause: 1.3]
C: The order database is separate, owned by the order service, because the inventory database is the hottest resource in the sale and I keep everything else off it. Orders carry the hold they came from, unique, so there is one order per hold, ever. Money is a decimal type. Each payment attempt carries the key we send to the provider.
C: And tickets, with a unique constraint on event and seat. The state machine and the conditional claim should make a double sale impossible. This constraint is the independent check. Two guards are far less likely to fail together.
[pause: 1.1]

[slide: v-133]
[pause: 1.3]
C: The line's state lives in Redis, not the database. Losing a second of queue state is survivable. Losing a seat is not. The curly braces around the event identifier in every key make Redis hash only that part, so every key of one event lands on the same node, and one script can touch all of them atomically. Different events land on different nodes, which is how many simultaneous sales spread out.
[pause: 1.1]

[slide: v-134]
[pause: 1.3]
C: The seat's state machine.
C: Available, claimed to held with a five-minute expiry.
[reveal: v-135]
[pause: 0.45]
C: Held, when an order is placed, to payment-pending, which is frozen.
C: Payment-pending to sold on an authorization.
[reveal: v-136]
[pause: 0.45]
C: And back to available on a decline, or a definite failure.
C: Payment-pending is the state weak designs miss.
[reveal: v-137]
[pause: 0.45]
C: The expiry paths only touch held.
C: A seat whose payment is in flight is frozen by design, and only the order service can release it, once the outcome is definite.
[pause: 1.1]

[pause: 1.4]

## 5 High-level design

[slide: v-138]
[pause: 1.2]
C: Three versions. Each is introduced by the objection it answers. The system stays on screen from here, and later pictures are views of it. Boxes never move.
[pause: 1.8]

[slide: v-139]
[pause: 1.3]
C: Version one.
C: Fans call a booking API.
[reveal: v-140]
[pause: 0.45]
C: The API reads the seat row.
C: If it is available, it writes the fan's name.
[reveal: v-141]
[pause: 0.45]
C: One API, one table.
C: For a small venue with a quiet sale this is enough, and saying so is part of the answer.
C: No objection yet: it is the simplest thing that works.
[pause: 1.1]

[slide: v-142]
[pause: 1.0]
C: The objection.
[reveal: v-143]
[pause: 0.45]
C: Two fans read the seat at the same moment and both see free.
[reveal: v-144]
[pause: 0.45]
C: Both write.
[reveal: v-145]
[pause: 0.45]
C: Either one overwrites the other, or both pay.
[reveal: v-146]
[pause: 0.45]
C: And there is no state for a fan who is still typing a card, so the only way to protect their seat is a lock held for three minutes.
[reveal: v-147]
[pause: 0.45]
C: A million requests land on that table, and the map reads from the same rows.
[pause: 1.0]

[slide: v-148]
[pause: 1.3]
C: Version two answers that.
C: The seat gets a third state and an expiry, and the claim becomes one conditional update, the green arrow.
[reveal: v-149]
[pause: 0.45]
C: Checkout moves to its own order service, the new box below.
C: It freezes the seats, calls the payment provider, and only then sells.
C: The two paths are separate because the provider is slow and sometimes silent, and the inventory database must never wait for it.
[reveal: v-150]
[pause: 0.45]
C: The dashed line from the provider carries either an answer or silence.
C: Version two is correct.
C: It is not yet survivable.
[pause: 1.1]

[slide: v-151]
[pause: 0.6]
C: The objection to version two.
C: The claim is right, and checkout is right.
C: But every fan can call the claim, so the hottest seats take every click.
[reveal: v-152]
[pause: 0.45]
C: And the seat map is still read from the table that the claims lock.
[reveal: v-153]
[pause: 0.45]
C: What is missing is a way to keep a million people away from fifty thousand rows.
[pause: 0.8]

[slide: v-154]
[pause: 1.3]
C: Version three.
[reveal: v-155]
[pause: 0.45]
C: The gateway and C-D-N absorb the million, and check an admission token on every shop call.
[reveal: v-156]
[pause: 0.45]
C: The waiting room holds the lobby, the pointer and the tokens.
[reveal: v-157]
[pause: 0.45]
C: And a pipeline for the map: the database writes a change and an outbox row in one transaction, the event log carries it, a snapshot builder publishes at most one bitmap a second to the seat-map cache, and the edge serves it by version.
[reveal: v-158]
[pause: 0.45]
C: This is the baseline.
[reveal: v-159]
[pause: 0.45]
C: It stays on screen, and every later picture is a view of it.
[pause: 1.1]

[slide: v-160]
[pause: 0.6]
C: What version three leaves open.
C: It has an atomic claim, a hold with an expiry, a line, a map off the database and a payment path that expects silence.
[reveal: v-161]
[pause: 0.45]
C: It has not been tested against two fans on one seat, a fan who leaves, a late payment, a million at the door, bots, a stale map, a promoter who changes the plan, or a failure nobody sees.
[reveal: v-162]
[pause: 0.45]
C: Those are the eight challenges, after the flows.
[pause: 0.8]

[slide: v-163]
[pause: 1.3]
C: Requirement one, join.
[reveal: v-164]
[pause: 0.45]
C: Step one: a fan requests the sale page and the join from the C-D-N.
[reveal: v-165]
[pause: 0.45]
C: Step two: the gateway sends the join to the waiting room, which draws a random score, one in-memory step, and returns a signed queue token.
[reveal: v-166]
[pause: 0.45]
C: Step three:
[reveal: v-167]
[pause: 0.45]
C: after the sale opens, the fan polls the one cached answer, computes their position, and when the pointer reaches them, the admit call exchanges the queue token for a ten-minute admission token.
[pause: 1.1]

[slide: v-168]
[pause: 1.3]
C: Requirement two, browse.
[reveal: v-169]
[pause: 0.45]
C: Step one: the request reaches the edge.
[reveal: v-170]
[pause: 0.45]
C: Step two: the layout comes from the C-D-N, immutable, and the availability comes from the seat-map cache by version, with a not-modified when nothing changed.
[reveal: v-171]
[pause: 0.45]
C: Step three: the response goes back.
[reveal: v-172]
[pause: 0.45]
C: The claims database is not touched.
[pause: 1.1]

[slide: v-173]
[pause: 1.3]
C: Requirement three, hold.
[reveal: v-174]
[pause: 0.45]
C: One: the request arrives with an admission token and an idempotency key.
[reveal: v-175]
[pause: 0.45]
C: Two: the gateway checks the token.
[reveal: v-176]
[pause: 0.45]
C: Three: the booking API sends one conditional claim, all the seats or none.
[reveal: v-177]
[pause: 0.45]
C: Four: the database answers won or lost.
[reveal: v-178]
[pause: 0.45]
C: Five: the API answers two-oh-one with an expiry, or four-oh-nine with a fresh bitmap.
[reveal: v-179]
[pause: 0.45]
C: Six: the response.
[reveal: v-180]
[pause: 0.45]
C: The outbox row is written in the same transaction as the claim.
[pause: 1.1]

[slide: v-181]
[pause: 1.3]
C: Requirement four, pay.
[reveal: v-182]
[pause: 0.45]
C: One: the order reaches the order service.
[reveal: v-183]
[pause: 0.45]
C: Two: it freezes the seats in the inventory database before it calls the provider.
[reveal: v-184]
[pause: 0.45]
C: Three: it asks the provider to authorize.
[reveal: v-185]
[pause: 0.45]
C: Four: the provider answers approved, or declined, or nothing.
[reveal: v-186]
[pause: 0.45]
C: Five: silence becomes unknown, not failed, and the reconciler asks again.
[reveal: v-187]
[pause: 0.45]
C: The seats are sold only on an approved authorization, and the money is captured last.
[pause: 1.1]

[slide: v-188]
[pause: 1.3]
C: Requirement five, release.
[reveal: v-189]
[pause: 0.45]
C: One: the sweeper finds expired holds in small batches and returns the seats to available.
[reveal: v-190]
[pause: 0.45]
C: Two: the same transaction writes an outbox row, and the event log carries it.
[reveal: v-191]
[pause: 0.45]
C: Three: the released seat is announced, so the map shows it free, and a fan on the waitlist can be offered it.
[reveal: v-192]
[pause: 0.45]
C: Nothing in this path is on a fan's critical path.
[pause: 1.1]

[slide: v-193]
[pause: 1.3]
C: The C4 context.
[reveal: v-194]
[pause: 0.45]
C: A million fans arrive through the C-D-N and the web application firewall, which absorb the crowd.
[reveal: v-195]
[pause: 0.45]
C: The promoter and operations set the sale, the fairness policy and the seats.
[reveal: v-196]
[pause: 0.45]
C: The payment provider is slow and sometimes silent.
[reveal: v-197]
[pause: 0.45]
C: Email and push carry the tickets.
[reveal: v-198]
[pause: 0.45]
C: Two outside dependencies decide the shape of the design: the payment provider, and the edge, where bots are stopped.
[pause: 1.1]

[slide: v-199]
[pause: 1.3]
C: The containers on the waiting side.
[reveal: v-200]
[pause: 0.45]
C: The waiting room does the join,
[reveal: v-201]
[pause: 0.45]
C: the position and the admit,
[reveal: v-202]
[pause: 0.45]
C: backed by a Redis queue store.
[reveal: v-203]
[pause: 0.45]
C: The admission controller turns the rate dial every second from shop health.
[reveal: v-204]
[pause: 0.45]
C: The seat-map service serves the bitmap,
[reveal: v-205]
[pause: 0.45]
C: built by a snapshot cache from the seat events in Kafka.
[reveal: v-206]
[pause: 0.45]
C: The gateway checks the admission token.
[reveal: v-207]
[pause: 0.45]
C: Three separate paths:
[reveal: v-208]
[pause: 0.45]
C: the queue, the read, and the write.
[pause: 1.1]

[slide: v-209]
[pause: 1.3]
C: The containers on the write side.
[reveal: v-210]
[pause: 0.45]
C: The inventory service holds the atomic claim,
[reveal: v-211]
[pause: 0.45]
C: over its PostgreSQL database with the outbox.
[reveal: v-212]
[pause: 0.45]
C: The order service,
[reveal: v-213]
[pause: 0.45]
C: with its own database,
[reveal: v-214]
[pause: 0.45]
C: talks to the slow provider and must never hold inventory connections
[reveal: v-215]
[pause: 0.45]
C: it waits.
[reveal: v-216]
[pause: 0.45]
C: A hold expirer releases expired holds.
[reveal: v-217]
[pause: 0.45]
C: Kafka carries the events.
[reveal: v-218]
[pause: 0.45]
C: The ticket constraint is the last line of defence against oversell.
[pause: 1.1]

[slide: v-219]
[pause: 1.3]
C: Level three, inside the inventory service.
[reveal: v-220]
[pause: 0.45]
C: The hold interface takes the request with its idempotency key and limits.
[reveal: v-221]
[pause: 0.45]
C: The claim engine runs the conditional update.
[reveal: v-222]
[pause: 0.45]
C: The outbox writer shares its transaction.
[reveal: v-223]
[pause: 0.45]
C: The freeze-and-sell component serves the order service.
[reveal: v-224]
[pause: 0.45]
C: And the sweeper,
[reveal: v-225]
[pause: 0.45]
C: with its skip-locked batches.
[reveal: v-226]
[pause: 0.45]
C: Lazy expiry lives in the claim predicate;
[reveal: v-227]
[pause: 0.45]
C: the sweeper only makes the map catch up.
[pause: 1.1]

[slide: v-228]
[pause: 1.3]
C: Join as a sequence.
[reveal: v-229]
[pause: 0.45]
C: A fan enters the lobby before the sale opens.
[reveal: v-230]
[pause: 0.45]
C: The waiting room draws a random score on the server,
[reveal: v-231]
[pause: 0.45]
C: writes it to the lobby set with a no-overwrite flag,
[reveal: v-232]
[pause: 0.45]
C: and returns a signed token.
[reveal: v-233]
[pause: 0.45]
C: At the start moment, the phase flips.
[reveal: v-234]
[pause: 0.45]
C: Fans in the lobby ask once for their number,
[reveal: v-235]
[pause: 0.45]
C: with a jitter,
[reveal: v-236]
[pause: 0.45]
C: and the answer is their rank by score.
[reveal: v-237]
[pause: 0.45]
C: Late arrivals take the next number behind them.
[pause: 1.1]

[slide: v-238]
[pause: 1.3]
C: Checkout, the happy path.
[reveal: v-239]
[pause: 0.45]
C: The fan submits the order with a payment token and an idempotency key.
[reveal: v-240]
[pause: 0.45]
C: The order service inserts the order,
[reveal: v-241]
[pause: 0.45]
C: freezes the seats in the inventory database,
[reveal: v-242]
[pause: 0.45]
C: and answers accepted at once.
[reveal: v-243]
[pause: 0.45]
C: In the background it asks the provider to authorize with a ten-second timeout.
[reveal: v-244]
[pause: 0.45]
C: On approval it sells the seats,
[reveal: v-245]
[pause: 0.45]
C: writes the tickets and an outbox row in one local transaction,
[reveal: v-246]
[pause: 0.45]
C: and capture happens later, off the fan's path.
[pause: 1.1]

[pause: 1.4]

## 5.1 Components and technologies

[slide: v-247]
[pause: 1.2]
C: Now one level down. Every container, with the technology I would run it on, and for each choice, the alternatives I rejected and why.
[pause: 1.8]

[slide: v-248]
[pause: 1.3]
C: The container view again, with one change: the type line now names the technology. I will walk it once, then defend each choice on its own slide.
[reveal: v-249]
[pause: 0.45]
C: The path between them..
[reveal: v-250]
[pause: 0.45]
C: The path between them..
[reveal: v-251]
[pause: 0.45]
C: Waiting room is Go, stateless.
[reveal: v-252]
[pause: 0.45]
C: API gateway is Envoy, JWT check.
[reveal: v-253]
[pause: 0.45]
C: Queue store is Redis, Lua scripts.
[reveal: v-254]
[pause: 0.45]
C: Seat-map service is Go, version keyed.
[reveal: v-255]
[pause: 0.45]
C: Admission controller is Go control loop.
[reveal: v-256]
[pause: 0.45]
C: Snapshot cache is Redis.
[reveal: v-257]
[pause: 0.45]
C: Seat events is Kafka.
[reveal: v-258]
[pause: 0.45]
C: The path between them..
[pause: 1.1]

[slide: v-259]
[pause: 1.3]
C: The container view again, with one change: the type line now names the technology. I will walk it once, then defend each choice on its own slide.
[reveal: v-260]
[pause: 0.45]
C: API gateway is Envoy, JWT check.
[reveal: v-261]
[pause: 0.45]
C: The path between them..
[reveal: v-262]
[pause: 0.45]
C: Inventory and holds is Go, one statement.
[reveal: v-263]
[pause: 0.45]
C: Order service is Go, checkout saga.
[reveal: v-264]
[pause: 0.45]
C: Inventory DB is PostgreSQL 16.
[reveal: v-265]
[pause: 0.45]
C: Order DB is PostgreSQL.
[reveal: v-266]
[pause: 0.45]
C: Seat events is Kafka.
[reveal: v-267]
[pause: 0.45]
C: Hold expirer is Go sweeper.
[reveal: v-268]
[pause: 0.45]
C: Notifications is Kafka consumer.
[reveal: v-269]
[pause: 0.45]
C: The path between them..
[pause: 1.1]

[slide: v-270]
[pause: 1.0]
C: Each seat of each event is a row with a state. A claim is one update statement that names the state it expects: set held where the seat is free. A second fan's identical statement matches no row and learns the seat is taken. The hold row and the outbox row commit in the same transaction. Read committed is enough because the check and the change are the same statement.
[reveal: v-271]
[pause: 0.45]
C: Why PostgreSQL 16, primary and synchronous standby, read committed: Selling a seat once is a conditional update on a row, in a transaction with the hold and the outbox. Row locks and constraints are the tools that make it true.
[reveal: v-272]
[pause: 0.45]
C: Rejected: Read the seat, then update it. Two fans both read free and both write. The conditional update closes the gap in one statement.
[reveal: v-273]
[pause: 0.45]
C: Redis for the hold. A key can expire or vanish while the database still says held. The hold belongs in the same transaction as the seat.
[reveal: v-274]
[pause: 0.45]
C: A distributed lock per seat. One more system, and a lock without a token has the stale-holder failure.
[pause: 1.0]

[slide: v-275]
[pause: 1.0]
C: A fan joins the lobby and receives a position. An admission pointer advances at the rate the controller sets. A Lua script moves a batch from the lobby into the admitted set and mints their tokens in one atomic step, so no fan is admitted twice. Polling for position is served from a cached snapshot, not from Redis.
[reveal: v-276]
[pause: 0.45]
C: Why Redis, a sorted set for the lobby, a pointer, Lua scripts for the atomic steps: A million fans arriving at once cannot all reach the shop. The line is a data structure that must be fast and atomic.
[reveal: v-277]
[pause: 0.45]
C: Rejected: The relational database as the queue. A million inserts in a minute onto the inventory primary: the line would take the booking path down with it.
[reveal: v-278]
[pause: 0.45]
C: Kafka as the queue. Good for ordering, awkward for a position the fan can poll and a pointer that advances.
[reveal: v-279]
[pause: 0.45]
C: A third-party waiting room product. A real option; we show the design, and buy if the team cannot run it.
[pause: 1.0]

[slide: v-280]
[pause: 1.0]
C: The admission controller watches the shop's load and turns the rate dial down or up. A fan reaching the pointer gets a short-lived signed token, a JWT valid for ten minutes. Every shop call carries it. The gateway verifies the signature and expiry locally, so the check costs no database call.
[reveal: v-281]
[pause: 0.45]
C: Why A Go control loop, a signed token, a gateway that verifies without a database call: The shop can serve only so many shoppers. The dial sets how many enter per second, and a signed pass proves they were let in.
[reveal: v-282]
[pause: 0.45]
C: Rejected: Rate limiting at the gateway only. It rejects fans instead of queueing them: a fair line becomes a race of retries.
[reveal: v-283]
[pause: 0.45]
C: A session lookup per request. The session store becomes the bottleneck of the shop.
[pause: 1.0]

[slide: v-284]
[pause: 1.0]
C: Each claim, release and sale writes an outbox row in the same transaction as the seat change. A relay publishes the rows to Kafka in commit order, partitioned by event, at least once. The seat-map builder, notifications and a future waitlist are separate consumer groups, each deduplicating.
[reveal: v-285]
[pause: 0.45]
C: Why Outbox in the inventory transaction, Kafka partitioned by event: The seat map, notifications and any later consumer need to know what changed. The event must exist if and only if the claim committed.
[reveal: v-286]
[pause: 0.45]
C: Rejected: Publishing after the commit. A crash between the two loses a seat change for ever.
[reveal: v-287]
[pause: 0.45]
C: Consumers reading the database. Every consumer adds load to the inventory primary during the sale.
[pause: 1.0]

[slide: v-288]
[pause: 1.0]
C: The CDN caches the immutable venue layout for a long time and the queue state for a second. When many requests for an expired object reach one point of presence, request collapsing sends one request to the origin. The WAF rejects obvious bot traffic and scripted floods before they reach the waiting room.
[reveal: v-289]
[pause: 0.45]
C: Why A CDN with a WAF, one-second lifetimes, request collapsing: Ten thousand shoppers asking for the same seat map should cost one origin request, not ten thousand.
[reveal: v-290]
[pause: 0.45]
C: Rejected: Serving everything from the origin. The origin would carry the whole stampede.
[reveal: v-291]
[pause: 0.45]
C: A long edge lifetime for seat state. Fans would see seats as free that are gone, and click into failures.
[pause: 1.0]

[slide: v-292]
[pause: 1.0]
C: The venue layout is immutable and cached for ever. A builder consumes the seat events and writes a compact bitmap of seat states, about six kilobytes per event, to the snapshot cache under a version number. The seat-map service serves the layout plus the latest bitmap, and the client shows a fresh-as-of time.
[reveal: v-293]
[pause: 0.45]
C: Why A Go service, an immutable layout object, a bitmap snapshot per event version in Redis: Ten thousand shoppers want to see which seats are free. That must not touch the inventory primary.
[reveal: v-294]
[pause: 0.45]
C: Rejected: Querying the seat table per shopper. Ten thousand readers on the primary during the sale.
[reveal: v-295]
[pause: 0.45]
C: Pushing every seat change to every browser. A fan-out of every claim to ten thousand screens.
[pause: 1.0]

[slide: v-296]
[pause: 1.0]
C: The order service runs a saga: freeze the hold so it cannot expire mid-payment, call the payment provider with an idempotency key, then confirm the sale or release. The hold expirer sweeps holds past their time and releases them; the claim itself also expires an old hold when it finds one. A reconciler asks the provider about payments that went silent.
[reveal: v-297]
[pause: 0.45]
C: Why Go order service, an idempotent payment call, a hold expirer, a reconciler: A hold must end, whether the fan pays, abandons or the payment goes quiet. Both outcomes must be safe.
[reveal: v-298]
[pause: 0.45]
C: Rejected: A TTL on a Redis key as the hold. The key and the database can disagree. The hold belongs with the seat.
[reveal: v-299]
[pause: 0.45]
C: Releasing the hold the moment it expires. If the payment succeeded in that instant, we have taken money for a seat we resold.
[pause: 1.0]

[slide: v-300]
[pause: 1.0]
C: The stack on one slide, as I would leave it on the whiteboard.
C: Inventory DB: PostgreSQL, conditional update.
C: Not Read then write; Redis hold.
C: Check and change are one statement.
[reveal: v-301]
[pause: 0.45]
C: Waiting room: Redis, sorted set, Lua.
C: Not Database; Kafka.
C: Fast and atomic admission.
[reveal: v-302]
[pause: 0.45]
C: Admission: Rate dial; signed token.
C: Not Gateway limit only; sessions.
C: Check without a database.
[reveal: v-303]
[pause: 0.45]
C: Seat events: Outbox into Kafka.
C: Not Publish after; poll the DB.
C: A waitlist is a new consumer.
[reveal: v-304]
[pause: 0.45]
C: CDN and WAF: One-second lifetime, collapsing.
C: Not Origin only; long lifetime.
C: Shared answers cost one request.
[reveal: v-305]
[pause: 0.45]
C: Seat map: Layout plus bitmap by version.
C: Not Query per shopper; push all.
C: Reads never touch the primary.
[reveal: v-306]
[pause: 0.45]
C: Orders and holds: Saga; sweeper; reconciler.
C: Not Redis TTL; release at expiry.
C: Freeze before the call.
[reveal: v-307]
[pause: 0.45]
N: Naming a product is not the signal.
N: Naming the property that rules out its rival is.
N: Interviewers go one level down on whichever box you name, so name only what you can defend.
[pause: 1.0]

[slide: v-308]
[pause: 0.6]
N: Before the challenges, swap seats. You are the interviewer now. Of everything on the last slide, which box would you push on, and what is the one question you would ask? Pause the video and pick one.
[pause: 3.0]

[slide: v-309]
[pause: 1.0]
N: Here is where interviewers usually go.
I: Ten thousand fans click the same seat in the same second.
I: What does the database do?
[pause: 1.2]
N: Ten thousand identical conditional updates queue on one row; the first matches, the other 9,999 match nothing and return taken.
[reveal: v-310]
[pause: 0.45]
N: The trap is a read-then-write in the application.
I: The Redis node holding the line fails.
I: What happens to the million fans waiting?
[pause: 1.2]
N: A replica is promoted and the line is rebuilt from the replicated state and the join log; positions may shift slightly but nobody is admitted twice, because admission is a single script.
[reveal: v-311]
[pause: 0.45]
N: The trap is losing the line.
I: Product wants a waitlist added mid-sale.
I: What changes in the booking path?
[pause: 1.2]
N: Nothing.
N: The waitlist is a new consumer group reading the seat events, and it acts on a released seat.
[reveal: v-312]
[pause: 0.45]
N: The trap is rewriting booking.
I: The map says a seat is free and the fan clicks it, but it is gone.
I: Is that an oversell?
[pause: 1.2]
N: No.
N: The claim, one conditional update, decides, and answers taken; the map is a hint.
[reveal: v-313]
[pause: 0.45]
N: The client refetches.
N: The trap is treating the map as the truth.
I: The hold expires, then the payment succeeds.
I: Who gets the seat?
[pause: 1.2]
N: The fan who paid, because the hold was frozen before the call.
[reveal: v-314]
[pause: 0.45]
N: A reconciler resolves a silent payment by asking the provider, and only then releases.
N: The trap is releasing at expiry.
N: If you picked a box that is not on this list, good.
N: Write its probe down and answer it before you watch on.
[pause: 1.2]

[pause: 1.4]

## 6 Bridge

[slide: v-315]
[pause: 1.2]
V: It works. The question now is where it breaks first.
[pause: 1.8]

[slide: v-316]
[pause: 1.3]
C: Here is the baseline with the attack points.
C: Two fans on one seat, at the database.
C: A hold that outlives its owner, at the sweeper.
C: A payment that arrives late, at the order service.
C: A million at the door, at the waiting room.
[reveal: v-317]
[pause: 0.45]
C: Bots, in the same line.
C: A stale map, at the seat-map cache.
C: A promoter who changes the plan, at the layout and the flag.
C: And finally: how would we know any of it was broken?
C: I'll take them in an order where each fix creates the next question.
[pause: 1.1]

[pause: 1.4]

## 7 Challenges

[slide: v-318]
[pause: 1.2]
C: Eight challenges. Each runs the same way: the question, the naive answer, a case with numbers, where it breaks, the fix, why it works, then the interviewer pushes on the fix itself, and I answer what I'd say in the room.
[pause: 1.8]

[pause: 1.4]

## 7.1 Challenge 1: Two fans, one seat

[slide: v-319]
[pause: 1.2]
N: Challenge one. Two fans click the same seat in the same millisecond: what happens, mechanically?
[pause: 1.8]

[slide: v-320]
[pause: 0.6]
I: Two users click the same seat in the same millisecond. Walk me through it, mechanically.
[pause: 2.0]

[slide: v-321]
[pause: 1.3]
C: Look at the arrow from the booking API to the seat database.
[reveal: v-322]
[pause: 0.45]
C: The check and the change are two separate steps,
[reveal: v-323]
[pause: 0.45]
C: and another writer can slip in between them.
[pause: 1.1]

[slide: v-324]
[pause: 1.0]
C: The trace.
[reveal: v-325]
[pause: 0.45]
C: At ten o'clock and one point one two zero seconds, Fan A reads seat one hundred two: available.
[reveal: v-326]
[pause: 0.45]
C: A millisecond later Fan B reads it: available.
[reveal: v-327]
[pause: 0.45]
C: A writes, then B writes, and both are told they hold the seat.
[reveal: v-328]
[pause: 0.45]
C: Three minutes later both pay.
C: Two tickets for one seat.
[reveal: v-329]
[pause: 0.45]
C: That breaks safety property one.
C: the gap is milliseconds wide, and under this load it is hit constantly.
[pause: 1.0]

[slide: v-330]
[pause: 1.3]
C: The fix.
[reveal: v-331]
[pause: 0.45]
C: The arrow from the API to the database is now one conditional update.
[reveal: v-332]
[pause: 0.45]
C: The condition is the availability check, so there is no gap.
[reveal: v-333]
[pause: 0.45]
C: The rows are locked in ascending order, so two fans asking for the same pair can never deadlock, and the lock fails at once instead of queueing.
[reveal: v-334]
[pause: 0.45]
C: Then the update changes the seats only if they are still available.
[reveal: v-335]
[pause: 0.45]
C: Rejected: Read the seat, then update it.
C: Two fans both see free; one statement is the check and the change.
[pause: 1.1]

[slide: v-336]
[pause: 1.0]
C: In pseudocode.
C: Begin.
C: Lock the requested rows in sorted order, failing at once if another buyer holds one.
C: Then update those seats to held, with a five-minute expiry, only where the seat is available, or its old hold has expired.
C: The condition is the check.
C: If fewer rows came back than were asked for, roll back and answer four-oh-nine with a fresh bitmap.
C: Otherwise insert the hold and the outbox row and commit.
C: All or nothing: a partial hold would leave an orphan seat held for five minutes.
[pause: 1.0]

[slide: v-337]
[pause: 1.3]
C: As a sequence.
[reveal: v-338]
[pause: 0.45]
C: Fan A asks for seats one-oh-one and one-oh-two.
[reveal: v-339]
[pause: 0.45]
C: The inventory service locks the rows in order.
[reveal: v-340]
[pause: 0.45]
C: Fan B asks for one-oh-two and one-oh-three.
[reveal: v-341]
[pause: 0.45]
C: It tries to lock one-oh-two,
[reveal: v-342]
[pause: 0.45]
C: which is taken:
[reveal: v-343]
[pause: 0.45]
C: the database answers immediately that the row is locked, and Fan B gets a four-oh-nine with a fresh bitmap.
[reveal: v-344]
[pause: 0.45]
C: Fan A's update claims two rows,
[reveal: v-345]
[pause: 0.45]
C: the hold and outbox row are inserted, commit, and A gets a two-oh-one with an expiry.
[pause: 1.1]

[slide: v-346]
[pause: 0.6]
I: What if your code has a bug and issues a second ticket anyway? Or the primary fails over in the middle of a claim?
[pause: 2.0]

[slide: v-347]
[pause: 0.6]
C: A second guard the code cannot skip.
C: The ticket table has a unique constraint on event and seat, so if a bug ever tries to issue a second ticket for seat one hundred two, the database rejects the insert.
[reveal: v-348]
[pause: 0.45]
C: Two independent guards are far less likely to fail together.
C: And failover in the middle of a claim: the claim is one transaction, and with a synchronous replica an acknowledged hold is never lost.
[reveal: v-349]
[pause: 0.45]
C: An unacknowledged one never became a hold.
C: The cost is a few seconds of refused holds, not a wrong sale.
[pause: 0.8]

[slide: v-350]
[pause: 0.7]
V: If asked, I'd say: one conditional update is the check and the change, all or nothing, with rows locked in a stable order. The loser fails in milliseconds and gets a fresh map. And the ticket table has a unique constraint on event and seat as a second, independent guard.
[pause: 1.0]
N: That fix creates the next question: the hold needs an end.
[pause: 1.6]

[pause: 1.4]

## 7.2 Challenge 2: The hold that outlives its owner

[slide: v-351]
[pause: 1.2]
N: Challenge two. A fan holds two seats and closes the laptop: who frees them, and what if the thing that frees them is down?
[pause: 1.8]

[slide: v-352]
[pause: 0.6]
I: A fan holds two seats and closes the laptop. Your cleanup job is down for ten minutes. What do users see?
[pause: 2.0]

[slide: v-353]
[pause: 1.3]
C: The naive answer: a cleanup job every minute releases expired holds.
[reveal: v-354]
[pause: 0.45]
C: Look at the seat database under attack.
[reveal: v-355]
[pause: 0.45]
C: A hold has no owner left, and the seat is neither free nor sold.
[reveal: v-356]
[pause: 0.45]
C: If the only thing that frees it is a job,
[reveal: v-357]
[pause: 0.45]
C: then every failure of the job is a failure of the sale.
[pause: 1.1]

[slide: v-358]
[pause: 1.0]
C: The trace.
C: Fan A holds seats one-oh-one and one-oh-two at ten.
[reveal: v-359]
[pause: 0.45]
C: At five past, the hold expires and Fan A is gone.
[reveal: v-360]
[pause: 0.45]
C: A second later Fan C clicks seat one-oh-one and is refused, because the row still says held.
[reveal: v-361]
[pause: 0.45]
C: The job runs at ten-oh-five-fifty: fifty seconds of two good seats refused.
[reveal: v-362]
[pause: 0.45]
C: And if the job is down for ten minutes, every expired seat stays taken and sales stall.
[reveal: v-363]
[pause: 0.45]
C: This is liveness property one: a seat stuck in limbo.
[pause: 1.0]

[slide: v-364]
[pause: 1.3]
C: The fix, with two paths.
[reveal: v-365]
[pause: 0.45]
C: Lazy expiry: the claim from challenge one already says a seat is claimable if it is available, or if it is held and its expiry is in the past.
[reveal: v-366]
[pause: 0.45]
C: So an expired hold is claimable the instant it expires, whether or not any job has run.
C: Correctness never depends on the sweeper.
[reveal: v-367]
[pause: 0.45]
C: And the sweeper, the new box under the database.
C: Every five seconds it releases expired holds and announces each release through the outbox.
[reveal: v-368]
[pause: 0.45]
C: Without it expired seats would be claimable but invisible on everyone's map.
[reveal: v-369]
[pause: 0.45]
C: Rejected: Holding seats in Redis with a TTL.
C: The key and the database can disagree; two paths cover each other's gap.
[pause: 1.1]

[slide: v-370]
[pause: 1.0]
C: The sweeper in pseudocode. Select the held rows whose expiry has passed, oldest first, at most five hundred, and skip any row that is locked. Then set them available and return them. In the same transaction, write the released event to the outbox. Skip-locked, not no-wait: the sweeper needs any expired seats, so if a buyer is claiming one it moves on, and several sweepers never block each other.
[pause: 1.0]

[slide: v-371]
[pause: 1.3]
C: As a sequence.
[reveal: v-372]
[pause: 0.45]
C: Fan C claims seat one-oh-one,
[reveal: v-373]
[pause: 0.45]
C: whose hold expired two seconds ago: the lazy predicate lets it through at once.
[reveal: v-374]
[pause: 0.45]
C: Later, the sweeper finds seat one-oh-two, which nobody tried.
[reveal: v-375]
[pause: 0.45]
C: It releases it and writes the event,
[reveal: v-376]
[pause: 0.45]
C: the snapshot builder hears it,
[reveal: v-377]
[pause: 0.45]
C: and the map shows seat one-oh-two free on the next version.
[pause: 1.1]

[slide: v-378]
[pause: 0.6]
I: Your sweeper releases a seat while its owner is entering a card number. Or it is simply down.
[pause: 2.0]

[slide: v-379]
[pause: 0.6]
C: Two answers.
C: First, the sweeper only touches held seats.
C: A seat whose payment is in flight is in payment-pending, a different state, so it is simply not eligible.
C: Only the order service, on a definite outcome, can release it.
[reveal: v-380]
[pause: 0.45]
C: Second, a dead sweeper costs staleness, not oversell.
C: Expired seats are still claimable through the lazy path, but the map shows them as taken, so fans do not click them and sell-through slows.
[reveal: v-381]
[pause: 0.45]
C: I alert on the age of the oldest expired hold: anything above thirty seconds means the sweeper is not keeping up.
[pause: 0.8]

[slide: v-382]
[pause: 0.7]
V: If asked, I'd say: two expiry paths, each covering the other's gap. The claim treats an expired hold as free, so correctness does not depend on a job. A sweeper releases in small batches and announces it, so the map catches up. If it dies, we get staleness, not oversell, and an alert on the oldest expired hold.
[pause: 1.0]
N: That fix creates the next question: what if the seat expires while the fan is paying?
[pause: 1.6]

[pause: 1.4]

## 7.3 Challenge 3: The hold expires, then the payment succeeds

[slide: v-383]
[pause: 1.2]
N: Challenge three. The best probe in the round: the hold expires while the payment provider is thinking, then the payment succeeds.
[pause: 1.8]

[slide: v-384]
[pause: 0.6]
I: The hold expires while the payment provider is still thinking, then the payment succeeds. What do you do?
[pause: 2.0]

[slide: v-385]
[pause: 1.3]
C: The naive answer: the hold expired, so release the seat, and if the payment arrives later, refund.
[reveal: v-386]
[pause: 0.45]
C: Look at the order service and the arrow into the database.
[reveal: v-387]
[pause: 0.45]
C: Nothing stops the seat from being claimed by someone else
[reveal: v-388]
[pause: 0.45]
C: the first fan's payment is still in flight.
[reveal: v-389]
[pause: 0.45]
C: There is no perfectly clean answer here, so I take a position and defend it.
[pause: 1.1]

[slide: v-390]
[pause: 1.0]
C: The trace.
C: At four-fifty Fan A submits and the provider is slow.
[reveal: v-391]
[pause: 0.45]
C: At five the hold expires.
[reveal: v-392]
[pause: 0.45]
C: At five-oh-one Fan C claims the seat.
[reveal: v-393]
[pause: 0.45]
C: At five-oh-five the provider answers: approved, for A.
[reveal: v-394]
[pause: 0.45]
C: Now two people paid for one seat, or one person paid for nothing.
[reveal: v-395]
[pause: 0.45]
C: That breaks safety property two.
[pause: 1.0]

[slide: v-396]
[pause: 0.6]
C: My position has four parts.
C: One: prevent it.
C: Before I call the provider, I freeze the seats: held becomes payment-pending, with ten more minutes.
[reveal: v-397]
[pause: 0.45]
C: The expiry paths only touch held.
C: Two: authorize, then capture.
C: Authorize only reserves the money; I sell on approval and capture last, and backing out is a void the customer never sees.
[reveal: v-398]
[pause: 0.45]
C: Three: unknown is not failure.
C: A timeout means we did not hear the answer, not that there was none.
C: I ask again with our idempotency key, and accept the webhook.
[reveal: v-399]
[pause: 0.45]
C: Four: the residual.
C: If the provider reports success after we gave up, we refund, apologise and give priority on the waitlist.
[pause: 0.8]

[slide: v-400]
[pause: 1.3]
C: On the baseline.
[reveal: v-401]
[pause: 0.45]
C: The new box is the reconciler, next to the order service.
[reveal: v-402]
[pause: 0.45]
C: The freeze is the arrow from the order service to the database.
[reveal: v-403]
[pause: 0.45]
C: The order service authorizes with the provider, and the provider's answer, or silence, comes back on the dashed line.
[reveal: v-404]
[pause: 0.45]
C: A silent order becomes unknown, and the reconciler asks the provider about it, by key, with backoff.
[reveal: v-405]
[pause: 0.45]
C: Rejected: Releasing the hold at the moment it expires.
C: The payment may have succeeded in that instant; freeze before the call and reconcile silence.
[pause: 1.1]

[slide: v-406]
[pause: 1.0]
C: In pseudocode. The freeze is one conditional update: move to payment-pending only the seats still held by this hold, and only if the hold has not expired. If fewer rows come back than the hold covers, the fan is told the hold expired, before any money moves.
C: And the confirm step. Three callers may race to it: the original call, the reconciler and the webhook. A conditional status change makes it idempotent: only the first caller proceeds, and the rest return. Then sell the seats, and in one transaction confirm the order, issue the tickets and write the outbox row.
[pause: 1.0]

[slide: v-407]
[pause: 1.0]
C: The reconciler asks the provider about unknown orders, by our key.
C: Authorized: confirm.
[reveal: v-408]
[pause: 0.45]
C: Declined: fail and release.
[reveal: v-409]
[pause: 0.45]
C: Not found: the request may never have arrived, so wait, and fail after two minutes.
[reveal: v-410]
[pause: 0.45]
C: Still processing: back off up to sixty seconds, and past the freeze deadline cancel at the provider, then release.
C: Unknown stays frozen, but not forever.
[pause: 1.0]

[slide: v-411]
[pause: 1.3]
C: As a sequence.
[reveal: v-412]
[pause: 0.45]
C: The order service authorizes with a ten-second timeout and gets nothing back.
[reveal: v-413]
[pause: 0.45]
C: It marks the order unknown, not failed, and schedules a check.
[reveal: v-414]
[pause: 0.45]
C: Two things now race:
[reveal: v-415]
[pause: 0.45]
C: the reconciler's status query,
[reveal: v-416]
[pause: 0.45]
C: and the provider's webhook, verified by signature and deduplicated by event identifier.
[reveal: v-417]
[pause: 0.45]
C: Whichever brings a definite answer first calls confirm,
[reveal: v-418]
[pause: 0.45]
C: and because confirm is idempotent it does not matter if both arrive.
[pause: 1.1]

[slide: v-419]
[pause: 0.6]
I: The provider stays silent for an hour. Your seats are frozen for an hour.
[pause: 2.0]

[slide: v-420]
[pause: 0.6]
C: A deadline.
C: The freeze lasts ten minutes, and past it the reconciler cancels with the provider, so a late authorization is voided and the customer is never charged, and then it releases the seats.
[reveal: v-421]
[pause: 0.45]
C: The cost is explicit: slightly slower sell-through at the very end of the sale.
C: I would show that to the product owner as the trade-off.
C: The traps.
[reveal: v-422]
[pause: 0.45]
C: A timeout treated as a decline charges people for nothing.
C: A retry without an idempotency key reserves the money twice.
C: A transaction held open across the provider call is, at two hundred and fifty in flight, the whole connection pool.
C: And a sweeper that releases frozen seats is the race we started with.
[pause: 0.8]

[slide: v-423]
[pause: 0.7]
V: If asked, I'd say: I would rather hold a seat ten extra minutes than sell it twice or charge someone for nothing. Seats are frozen before I call the provider, sold only on an approved authorization, and an unknown outcome stays frozen until a status check or the webhook gives a definite answer. The cost is slower sell-through at the end, and I would show that trade-off to the product owner.
[pause: 1.0]
N: That fix creates the next question: the whole system works, so how do we protect it from a million people?
[pause: 1.6]

[pause: 1.4]

## 7.4 Challenge 4: A million at the door

[slide: v-424]
[pause: 1.2]
N: Challenge four. The correctness is right; now a million people arrive in the same minute.
[pause: 1.8]

[slide: v-425]
[pause: 0.6]
I: A million users hit your inventory database at once. What breaks?
[pause: 2.0]

[slide: v-426]
[pause: 1.3]
C: The naive answer: autoscale the database and the A-P-I fleet.
[reveal: v-427]
[pause: 0.45]
C: Look at the red path from the fans to the seat database.
[reveal: v-428]
[pause: 0.45]
C: The load is concentrated on fifty thousand rows,
[reveal: v-429]
[pause: 0.45]
C: and really on the best few thousand.
[reveal: v-430]
[pause: 0.45]
C: More machines do not make a row lock shorter.
[pause: 1.1]

[slide: v-431]
[pause: 1.0]
C: The trace.
C: A million fans, two clicks each in sixty seconds, is thirty-three thousand contended writes a second.
[reveal: v-432]
[pause: 0.45]
C: Each waits for a row lock while holding a connection.
[reveal: v-433]
[pause: 0.45]
C: The pool of a few hundred empties in a fraction of a second, new requests time out, and clients retry, so the retries are the next wave.
[reveal: v-434]
[pause: 0.45]
C: A retry storm.
[reveal: v-435]
[pause: 0.45]
C: The database does not slow down gracefully.
C: It stops.
[reveal: v-436]
[pause: 0.45]
C: These figures are illustrative: the point is that the same rows are the problem.
[pause: 1.0]

[slide: v-437]
[pause: 1.3]
C: The fix, on the baseline.
[reveal: v-438]
[pause: 0.45]
C: The new boxes are the waiting room and the admission controller.
[reveal: v-439]
[pause: 0.45]
C: A fan joins and waits at the edge.
[reveal: v-440]
[pause: 0.45]
C: The controller sets a rate, the dotted green arrow to the waiting room, and the waiting room moves a pointer at that rate.
C: The gateway lets in only fans carrying an admission token.
[reveal: v-441]
[pause: 0.45]
C: By Little's law, ten thousand shoppers over five minutes is two thousand admissions a minute: that is R.
[reveal: v-442]
[pause: 0.45]
C: Rejected: Autoscaling the shop to a million at the door.
C: Scale lags the spike; a line in front and a dial behind it.
[pause: 1.1]

[slide: v-443]
[pause: 1.3]
C: The controller is a feedback loop, once a second per event.
C: It reads hold latency, database load and the provider's error rate.
[reveal: v-444]
[pause: 0.45]
C: If any is bad it cuts the rate by thirty percent.
[reveal: v-445]
[pause: 0.45]
C: If all is well and fewer than ten thousand shoppers are inside, it adds a small step: the same idea as congestion control, increase gently, cut sharply.
[reveal: v-446]
[pause: 0.45]
C: Why not a fixed rate?
[reveal: v-447]
[pause: 0.45]
C: Ten thousand is a guess until the sale is running, and real capacity depends on how slow the provider is today.
[reveal: v-448]
[pause: 0.45]
C: It starts at a quarter of the target, because at the first second every cache is cold.
[pause: 1.1]

[slide: v-449]
[pause: 1.3]
C: And the poll.
[reveal: v-450]
[pause: 0.45]
C: Every waiting fan asks how far the line has moved,
[reveal: v-451]
[pause: 0.45]
C: and the answer is the same bytes for everyone:
[reveal: v-452]
[pause: 0.45]
C: the pointer,
[reveal: v-453]
[pause: 0.45]
C: the rate, and the sold-out flag.
[reveal: v-454]
[pause: 0.45]
C: The edge holds it for one second.
[reveal: v-455]
[pause: 0.45]
C: So the origin sees about two hundred requests instead of a hundred thousand.
[reveal: v-456]
[pause: 0.45]
C: The fan works out their own position from the number in their signed token.
[pause: 1.1]

[slide: v-457]
[pause: 1.0]
C: The pointer in pseudocode. Once a second, per event, one controller chosen by a lease, so there is no double admission. Compute how many whole fans are due, carrying fractions over. Then one atomic script: set the pointer to the smaller of the pointer plus that count and the last issued number, so we never admit past the last person in line. Admit allows a fan in only when their number is at or below the pointer, and the first admission wins.
[pause: 1.0]

[slide: v-458]
[pause: 1.3]
C: As a sequence.
[reveal: v-459]
[pause: 0.45]
C: The fan polls the edge,
[reveal: v-460]
[pause: 0.45]
C: which fetches from the origin at most once a second.
[reveal: v-461]
[pause: 0.45]
C: The browser compares the pointer to the number in its token.
[reveal: v-462]
[pause: 0.45]
C: When it is reached, it calls admit.
[reveal: v-463]
[pause: 0.45]
C: The waiting room checks the signature and the pointer, and returns the token.
[reveal: v-464]
[pause: 0.45]
C: From here every shop call carries the token and the gateway verifies it,
[reveal: v-465]
[pause: 0.45]
C: with no lookup.
[pause: 1.1]

[slide: v-466]
[pause: 0.6]
I: What if the controller dies mid-sale? Or the edge cannot reach your origin? Or twice the people show up?
[pause: 2.0]

[slide: v-467]
[pause: 0.6]
C: Three answers.
C: A dead controller: one leader per event by a short lease; if it dies another takes over in seconds, and the pointer simply pauses.
[reveal: v-468]
[pause: 0.45]
C: An unreachable origin: the edge keeps serving the last answer for thirty seconds, so the line stalls and nobody is hurt.
[reveal: v-469]
[pause: 0.45]
C: Twice the people: the database does not notice, because the rate is set by shop health, not by demand.
C: What doubles is the lobby, about two hundred megabytes of Redis.
[reveal: v-470]
[pause: 0.45]
C: And a random delay on every synchronised action, so herds spread out.
C: Demand is absorbed at the edge, and the core only ever sees what it chose to admit.
[pause: 0.8]

[slide: v-471]
[pause: 0.7]
V: If asked, I'd say: I convert a stampede into a stream. A million people wait at the edge for almost nothing each, and a controller admits them at a rate the shop can serve, cutting it when hold latency or the payment error rate rises. The database only ever sees what I chose to admit.
[pause: 1.0]
N: That fix creates the next question: in what order do we admit them, and who gets in first?
[pause: 1.6]

[pause: 1.4]

## 7.5 Challenge 5: A fair line, and the bots

[slide: v-472]
[pause: 1.2]
N: Challenge five. The line exists; now who is first in it, and what stops a bot from taking every seat?
[pause: 1.8]

[slide: v-473]
[pause: 0.6]
I: What does fair mean here, and who decided? And how do you stop a bot holding all fifty thousand seats?
[pause: 2.0]

[slide: v-474]
[pause: 1.3]
C: The naive answer:
[reveal: v-475]
[pause: 0.45]
C: strict first-come, first-served from the moment sales open.
[reveal: v-476]
[pause: 0.45]
C: Look at the join arrow into the waiting room.
[reveal: v-477]
[pause: 0.45]
C: The order of a million people is decided in the first few hundred milliseconds,
[reveal: v-478]
[pause: 0.45]
C: and that rewards exactly the wrong things.
[pause: 1.1]

[slide: v-479]
[pause: 1.0]
C: The trace.
[reveal: v-480]
[pause: 0.45]
C: A million fans press refresh at a few seconds to ten, a spike we caused ourselves.
[reveal: v-481]
[pause: 0.45]
C: At ten, sales open.
[reveal: v-482]
[pause: 0.45]
C: At five milliseconds a bot in a data centre joins, thousands of times.
[reveal: v-483]
[pause: 0.45]
C: A fan on a phone network, at two hundred and fifty milliseconds, joins behind them.
[reveal: v-484]
[pause: 0.45]
C: In the first second the first few thousand places belong to machines and good networks.
[pause: 1.0]

[slide: v-485]
[pause: 1.3]
C: The fix.
[reveal: v-486]
[pause: 0.45]
C: Everyone who is in the lobby before the start is treated the same: a random order.
[reveal: v-487]
[pause: 0.45]
C: Arriving at nine-thirty or at one minute to ten makes no difference.
[reveal: v-488]
[pause: 0.45]
C: Anyone who arrives after the start joins behind every lobby fan, in arrival order.
C: Coming early still beats coming late, so there is a clear reason to be on time.
[reveal: v-489]
[pause: 0.45]
C: And it is a product policy: the lobby page must say so.
C: I would take it to the promoter, not present it as an engineering fact.
[reveal: v-490]
[pause: 0.45]
C: Rejected: First-come at the gate.
C: Bots with faster connections win; a lottery for everyone present, then first-come.
[pause: 1.1]

[slide: v-491]
[pause: 1.0]
C: The draw in pseudocode.
C: On join, draw a random score on the server and never send it to the client.
C: Add the fan to the lobby set with a no-overwrite flag, so joining again keeps the first score.
C: At the start nothing is shuffled: the order already exists.
C: Each fan asks once for their number, after a random delay, and it is their rank plus one.
C: Late arrivals take the next number from a counter.
C: Independent random numbers, sorted, are the same as a shuffle, and cost nothing in the critical second.
[pause: 1.0]

[slide: v-492]
[pause: 1.0]
C: Bots, in layers, because no layer is enough.
C: A challenge at the lobby entry, at the edge.
[reveal: v-493]
[pause: 0.45]
C: One entry per verified account, bound to a device: an account farm is the real attack, so verification makes accounts expensive.
[reveal: v-494]
[pause: 0.45]
C: Limits per account and per payment card, because the card catches one buyer with many accounts.
[reveal: v-495]
[pause: 0.45]
C: Signed short-lived tokens bound to the user, so a place cannot be forged or sold at scale.
[reveal: v-496]
[pause: 0.45]
C: Pre-registered, screened fans for flagship events.
[reveal: v-497]
[pause: 0.45]
C: And after the sale, cancelling flagged orders and releasing those seats to the waitlist.
[pause: 1.0]

[slide: v-498]
[pause: 0.6]
I: A farm of verified accounts gets through. Now what?
[pause: 2.0]

[slide: v-499]
[pause: 0.6]
C: Cheap controls that scale: limits per card and per device, fraud scoring after the fact, and orders cancelled and re-released to real fans on the waitlist.
[reveal: v-500]
[pause: 0.45]
C: The honest limit: no scheme is bot-proof.
C: The aim is to make a bot expensive enough that it is not worth it, and to say so to the promoter.
[reveal: v-501]
[pause: 0.45]
C: How far to go is a product and risk decision.
C: I bring the options and the costs.
[pause: 0.8]

[slide: v-502]
[pause: 0.7]
V: If asked, I'd say: fairness is a product decision, so I would take it to the promoter: a lottery for everyone in the lobby at the start, then first-come. Each place is a signed number, so it cannot be forged or traded. And I would make bots expensive, with one entry per verified account and limits per card.
[pause: 1.0]
N: That fix creates the next question: what do the admitted fans see, and how stale can it be?
[pause: 1.6]

[pause: 1.4]

## 7.6 Challenge 6: The seat map for ten thousand shoppers

[slide: v-503]
[pause: 1.2]
N: Challenge six. Ten thousand admitted fans all want to see the seats: where does that read go?
[pause: 1.8]

[slide: v-504]
[pause: 0.6]
I: Is a user allowed to see a seat as available and then fail to get it?
[pause: 2.0]

[slide: v-505]
[pause: 1.3]
C: The naive answer:
[reveal: v-506]
[pause: 0.45]
C: each shopper reads the seat table every couple of seconds.
[reveal: v-507]
[pause: 0.45]
C: Look at the path into the seat database again.
[reveal: v-508]
[pause: 0.45]
C: Five thousand reads a second now compete with the claims for the same rows and the same connections.
[reveal: v-509]
[pause: 0.45]
C: The part of the system that must be fastest slows down because of the part that is only a picture.
[pause: 1.1]

[slide: v-510]
[pause: 1.0]
C: The trace.
C: Ten thousand shoppers every two seconds is five thousand reads a second against fifty thousand rows.
[reveal: v-511]
[pause: 0.45]
C: They share the connection pool with the claims.
[reveal: v-512]
[pause: 0.45]
C: Hold latency at the ninety-ninth percentile climbs from forty milliseconds to six hundred.
[reveal: v-513]
[pause: 0.45]
C: The controller sees it and cuts the rate, so the line slows because of a picture.
[reveal: v-514]
[pause: 0.45]
C: The latencies are illustrative.
[pause: 1.0]

[slide: v-515]
[pause: 1.3]
C: The fix.
[reveal: v-516]
[pause: 0.45]
C: Split the map in two.
C: The layout, the seat positions and prices, never changes during a sale, so it comes from the edge and is cached for a year.
[reveal: v-517]
[pause: 0.45]
C: The availability is the live part: one bit per seat.
C: The database writes a change and an outbox row in one transaction.
[reveal: v-518]
[pause: 0.45]
C: The event log carries it.
C: The snapshot builder, the new box at the top, keeps the bitmap in memory, and at most once a second publishes a new version to the seat-map cache.
[reveal: v-519]
[pause: 0.45]
C: The edge serves it by version.
[reveal: v-520]
[pause: 0.45]
C: Rejected: Querying the seat table per shopper.
C: Ten thousand readers on the primary; an immutable layout and a versioned bitmap.
[pause: 1.1]

[slide: v-521]
[pause: 1.3]
C: The bitmap, bit by bit. Seat eight hundred twelve is bit eight hundred twelve, because the identifiers are dense. A one is available, a zero is taken. Fifty thousand bits is six and a quarter kilobytes. The version is the log offset, because it only ever grows, survives a restart of the builder, and two builders reading the same partition agree on it. A counter in memory would reset, and clients would see versions go backwards.
[pause: 1.1]

[slide: v-522]
[pause: 1.3]
C: As a sequence.
[reveal: v-523]
[pause: 0.45]
C: A hold commits with its outbox row.
[reveal: v-524]
[pause: 0.45]
C: A log-based relay reads the database's write-ahead log and publishes the row to the event log:
[reveal: v-525]
[pause: 0.45]
C: if the relay is down, rows wait in the log and nothing is lost.
[reveal: v-526]
[pause: 0.45]
C: The snapshot builder applies the change and marks the event dirty.
[reveal: v-527]
[pause: 0.45]
C: Once a second it writes a new versioned bitmap and flips the pointer last.
[reveal: v-528]
[pause: 0.45]
C: A fan's poll carries the version it has: a not-modified if nothing changed, the new body otherwise.
[pause: 1.1]

[slide: v-529]
[pause: 0.6]
I: The stream stalls for a minute. What does the fan see?
[pause: 2.0]

[slide: v-530]
[pause: 0.6]
C: Staleness grows; correctness does not.
C: The claim is authoritative, so a click on a seat taken eight hundred milliseconds ago fails in milliseconds with a four-oh-nine and the current bitmap.
[reveal: v-531]
[pause: 0.45]
C: That is a graceful failure, not a bug.
C: The builder can always rebuild: one scan of the table, then resume from the committed offset, and a lagging builder is an alert.
[reveal: v-532]
[pause: 0.45]
C: A later upgrade is to push changes to the admitted fans, but polling a six-kilobyte bitmap is good enough for the first release.
[pause: 0.8]

[slide: v-533]
[pause: 0.7]
V: If asked, I'd say: the map may be a second or two stale because the write path decides. The layout is immutable on the edge, and the availability is a six-kilobyte bitmap, rebuilt once a second from the event stream and served by version. A stale click fails fast with a fresh map.
[pause: 1.0]
N: That fix creates the next question: what if the requirements change in the middle of the sale?
[pause: 1.6]

[pause: 1.4]

## 7.7 Challenge 7: Requirements that arrive mid-sale

[slide: v-534]
[pause: 1.2]
N: Challenge seven. The promoter changes the plan while the sale is running: does the design bend, or break?
[pause: 1.8]

[slide: v-535]
[pause: 0.6]
I: The promoter wants to release five thousand more seats, mid-sale.
[pause: 2.0]

[slide: v-536]
[pause: 1.3]
C: The naive answer: redesign it, or stop the sale and restart.
[reveal: v-537]
[pause: 0.45]
C: Look at what is outlined.
[reveal: v-538]
[pause: 0.45]
C: The cached layout and map, and the waiting room's sold-out flag.
[reveal: v-539]
[pause: 0.45]
C: Forty-five thousand seats are sold, and nearly a million people have already been told it is over.
[reveal: v-540]
[pause: 0.45]
C: The question is whether the design bends or breaks, and I will say aloud what changes, what does not, and what it costs.
[pause: 1.1]

[slide: v-541]
[pause: 1.0]
C: The trace.
[reveal: v-542]
[pause: 0.45]
C: Forty-five thousand seats are sold, and the sold-out flag has reached nearly a million waiting fans.
[reveal: v-543]
[pause: 0.45]
C: The promoter asks for five thousand more rows now, while holds continue.
[reveal: v-544]
[pause: 0.45]
C: The layout that browsers cached lists fifty thousand seats, so the new ones do not exist for them.
[reveal: v-545]
[pause: 0.45]
C: The bitmap is fifty thousand bits: the new seats have no bit.
[reveal: v-546]
[pause: 0.45]
C: And the controller is paused on sold out, so nobody new is admitted.
[pause: 1.0]

[slide: v-547]
[pause: 1.0]
C: Four new requirements, and the seam that absorbs each.
C: Release five thousand seats: insert the rows as available in one transaction, publish a new layout version so the edge has a new key, clear the sold-out flag, and the controller resumes.
[reveal: v-548]
[pause: 0.45]
C: The claim path does not change.
C: A waitlist: a new consumer of the seat-released events offers a freed seat to the next fan as a targeted hold, with one nullable column.
[reveal: v-549]
[pause: 0.45]
C: Best available: a server-side allocator hands different fans different seats, so contention drops; same claim, a different source of seat identifiers.
[reveal: v-550]
[pause: 0.45]
C: And a tour: next.
[pause: 1.0]

[slide: v-551]
[pause: 1.3]
C: On the baseline.
[reveal: v-552]
[pause: 0.45]
C: The new box, top right, is the waitlist.
[reveal: v-553]
[pause: 0.45]
C: It subscribes to the same event log the snapshot builder already reads.
[reveal: v-554]
[pause: 0.45]
C: When a seat is released it creates a targeted hold for the next waiting fan, an ordinary held row with a ten-minute expiry, and sends a notification with a link that carries an admission token for that fan only.
[reveal: v-555]
[pause: 0.45]
C: Inventory gets one nullable column.
C: Nothing else moves.
[reveal: v-556]
[pause: 0.45]
C: Rejected: Rewriting booking to add a waitlist.
C: A waitlist is a new consumer of the seat events, not a redesign.
[pause: 1.1]

[slide: v-557]
[pause: 1.3]
C: A twenty-date tour on sale at once.
[reveal: v-558]
[pause: 0.45]
C: Everything is keyed by event: the Redis keys, the database partitions, the log key, the admission token, the edge cache key.
[reveal: v-559]
[pause: 0.45]
C: So events are independent by construction, and running many at once is an isolation problem, not a coordination one.
[reveal: v-560]
[pause: 0.45]
C: Small events pack into a shared cell.
[reveal: v-561]
[pause: 0.45]
C: A mega on-sale gets its own cell and Redis node, moved the day before, because on-sales are scheduled.
[pause: 1.1]

[slide: v-562]
[pause: 0.6]
C: Three shared resources.
C: The payment provider: say the contract allows three hundred authorizations a second, and twenty dates at twenty-five a second each would want five hundred.
C: I would stagger the on-sales, which is a product conversation to start weeks ahead, or split the budget per event, or add a second provider.
[reveal: v-563]
[pause: 0.45]
C: The admission budget: a small coordinator gives each event a ceiling, weighted by expected demand.
[reveal: v-564]
[pause: 0.45]
C: And the fan: they can join all twenty queues to improve their odds.
C: One active queue per account per tour, with a list of preferred dates, is fairer and cheaper, or a cap on tickets per account per tour.
[reveal: v-565]
[pause: 0.45]
C: A product question.
C: And on quiet days a queue would only annoy people, so it switches on past a threshold.
[pause: 0.8]

[slide: v-566]
[pause: 0.6]
I: Two mega events land on the same Redis node and share one provider budget. Then?
[pause: 2.0]

[slide: v-567]
[pause: 0.6]
C: Place them apart the day before.
C: Pin the hot events' slots to separate nodes, move a mega event to a dedicated cell, and scale the fleets from the on-sale calendar rather than reactively.
C: On-sales are scheduled weeks ahead: that is a gift, and I should use it.
[reveal: v-568]
[pause: 0.45]
C: The limit: a provider budget is a contract, so past it only staggering or a second provider helps.
C: And if multi-region comes up: each event is homed in one region with a single writer, with a synchronous replica in a second zone.
C: Never multi-master writes on seats.
[pause: 0.8]

[slide: v-569]
[pause: 0.7]
V: If asked, I'd say: say what changes, what does not, and what it costs. Releasing seats is an insert and a new layout version; the claim does not move. The waitlist is a new consumer of the stream. And a tour is an isolation problem, not a coordination one, because everything is keyed by event.
[pause: 1.0]
N: One question left, and it is the one that decides whether anyone sleeps: how would you know?
[pause: 1.6]

[pause: 1.4]

## 7.8 Challenge 8: How would you know it is broken?

[slide: v-570]
[pause: 1.2]
N: Challenge eight, always the last. The system is built; how would we know it is failing, before the fans tell us?
[pause: 1.8]

[slide: v-571]
[pause: 0.6]
I: What is the S-L-O for the sale opening, and what is your plan for the day it fails?
[pause: 2.0]

[slide: v-572]
[pause: 1.3]
C: The naive answer: C-P-U, error rate and a dashboard.
[reveal: v-573]
[pause: 0.45]
C: Look at the booking A-P-I, and notice what is not outlined: everything looks healthy.
[reveal: v-574]
[pause: 0.45]
C: The failures in this system are silent.
[reveal: v-575]
[pause: 0.45]
C: Nothing crashes.
[reveal: v-576]
[pause: 0.45]
C: A provider outage leaves seats frozen on unknown payments, the controller cuts the rate, and the line simply stops moving, while every machine reports green.
[pause: 1.1]

[slide: v-577]
[pause: 1.0]
C: The trace.
C: At twelve past, the provider slows from three seconds to fourteen.
[reveal: v-578]
[pause: 0.45]
C: By thirteen, nineteen hundred orders are unknown, and their thirty-eight hundred seats are frozen.
[reveal: v-579]
[pause: 0.45]
C: Hold latency is fine, so the controller does not cut the rate, but shoppers are not leaving.
[reveal: v-580]
[pause: 0.45]
C: By sixteen the shop is full of people who cannot pay, and admissions fall to zero.
[reveal: v-581]
[pause: 0.45]
C: At eighteen all the dashboards are green, and social media is not.
[reveal: v-582]
[pause: 0.45]
C: The numbers are illustrative: the point is that no single machine metric moved.
[pause: 1.0]

[slide: v-583]
[pause: 1.3]
C: The fix.
[reveal: v-584]
[pause: 0.45]
C: The new box is a probe: a synthetic fan, every ten seconds, through the whole path: the lobby, a hold on a reserved test seat, a release.
[reveal: v-585]
[pause: 0.45]
C: If a fan cannot complete a purchase, I want to know before a real one tells me.
[reveal: v-586]
[pause: 0.45]
C: And the indicators are tied to promises, not machines.
[reveal: v-587]
[pause: 0.45]
C: Rejected: Alerting on server health.
[reveal: v-588]
[pause: 0.45]
C: The servers can be fine while seats sell twice; measure the promise, not the machine.
[pause: 1.1]

[slide: v-589]
[pause: 1.0]
C: The indicators.
C: Hold latency and the conflict ratio.
[reveal: v-590]
[pause: 0.45]
C: The admission rate against shop health: if the rate falls while hold latency is flat, something other than the database is wrong.
[reveal: v-591]
[pause: 0.45]
C: The age of the oldest expired hold, above thirty seconds.
[reveal: v-592]
[pause: 0.45]
C: Seats frozen by unknown payments, and their age.
[reveal: v-593]
[pause: 0.45]
C: Queue state and map version lag.
[reveal: v-594]
[pause: 0.45]
C: And the one that must never differ: tickets issued against seats sold.
C: Any difference, page immediately, because that is the oversell invariant, and it is cheap to count.
[pause: 1.0]

[slide: v-595]
[pause: 1.0]
C: Two metrics, one conclusion.
C: Hold latency flat and admitted fans falling: that is the payment path, not inventory.
[reveal: v-596]
[pause: 0.45]
C: Hold latency and conflicts both rising: a hot section.
[reveal: v-597]
[pause: 0.45]
C: Map version lag rising with hold latency flat: the pipeline, which is staleness and not incorrectness.
[reveal: v-598]
[pause: 0.45]
C: The oldest expired hold rising while the sweeper is up: batch size or lock contention in the sweeper.
C: A pair tells you where to look first.
[pause: 1.0]

[slide: v-599]
[pause: 0.6]
C: Before the day.
C: A load test at twice the plan, a million simulated fans and then two million, against a production-sized cell, with the real provider replaced by one that is slow on purpose.
[reveal: v-600]
[pause: 0.45]
C: A game day: kill the sweeper, the controller and the provider in turn, and check that each alert fires and each runbook works.
[reveal: v-601]
[pause: 0.45]
C: And a plan to degrade: shrink the rate, pause admission, say so on the page, and a kill switch that stops the line while the invariants hold.
[reveal: v-602]
[pause: 0.45]
C: The service level objective for the opening, as an initial target: a fan who is admitted can complete a purchase within the checkout window, ninety-nine percent of the time.
[pause: 0.8]

[slide: v-603]
[pause: 0.6]
I: The metrics say all is fine and the fans are furious.
[pause: 2.0]

[slide: v-604]
[pause: 0.6]
C: Trust the synthetic fan and the support queue over the dashboard.
C: If the probe fails, the dashboard is wrong, whatever it says, and the probe goes on the pager, not on a wall.
[reveal: v-605]
[pause: 0.45]
C: Support contacts per minute, and what they say, is a metric of last resort: slow and noisy, but it never lies about a real fan.
[reveal: v-606]
[pause: 0.45]
C: The honest limit: every indicator is a guess about what matters, so I review them after every sale, against what actually hurt.
[pause: 0.8]

[slide: v-607]
[pause: 0.7]
V: If asked, I'd say: the S-L-I is a fan completing a purchase, probed continuously. I watch seats frozen by unknown payments and the age of the oldest expired hold, because that is where this system fails silently. And there is a plan to degrade: shrink the rate, pause admission, and say so.
[pause: 1.0]
N: That is the last challenge. Next: what would this cost to build, and who would build it?
[pause: 1.6]

[pause: 1.4]

## 8 Build cost

[slide: v-608]
[pause: 1.2]
N: This chapter is marked auxiliary. It is the engineering-manager layer, optional in a Staff round.
C: A ticket booking system is not one project. It is three, and the third is the one people forget to staff.
[pause: 1.8]

[slide: v-609]
[pause: 1.0]
C: Three releases, called V-one, V-two and V-three, as in the design.
C: V-one: a sale for a moderate crowd.
[reveal: v-610]
[pause: 0.45]
C: One primary per event, the conditional claim, holds, orders and one provider.
C: Three engineers for two months, about six engineer-months.
C: V-two: a sale that survives a provider that goes quiet: the sweeper, the freeze and the reconciler, the outbox and the snapshot builder.
[reveal: v-611]
[pause: 0.45]
C: Two more engineers for two months, about ten more.
C: V-three: a sale that survives a million at the door: the waiting room, the controller, bot controls, the load test and game days.
[reveal: v-612]
[pause: 0.45]
C: Two more engineers for three months, about twenty more.
C: All of these are illustrative; use your own.
[pause: 1.0]

[slide: v-613]
[pause: 1.0]
C: Buy against build.
C: Inventory and orders I build, because they hold the invariant: never twice, never stuck.
[reveal: v-614]
[pause: 0.45]
C: The payment provider I buy: it is regulated and not a differentiator.
[reveal: v-615]
[pause: 0.45]
C: The bot challenge I buy: it is an arms race with a vendor's data behind it.
[reveal: v-616]
[pause: 0.45]
C: The waiting room I could buy for the first season, to reach a first sale sooner, and build when control or the per-event cost justifies it.
[reveal: v-617]
[pause: 0.45]
C: The map pipeline, the sweeper and the reconciler are small and tied to the claim's meaning, so I build them.
[pause: 1.0]

[slide: v-618]
[pause: 0.6]
C: Top risks.
C: A provider outage on a flagship sale: a second provider behind the same interface, and a budget agreed in advance.
[reveal: v-619]
[pause: 0.45]
C: The first big on-sale with no load test: test at twice the plan, with a slow provider.
[reveal: v-620]
[pause: 0.45]
C: And a fairness rule decided late: the promoter and product decide it weeks ahead, and the page states it.
[reveal: v-621]
[pause: 0.45]
V: The question I ask before saying yes: what does a wrong sale cost, who decides what is fair, and how big is the first on-sale?
[pause: 1.0]

[pause: 1.4]

## 9 Recap

[slide: v-622]
[pause: 1.2]
C: Four minutes to close. One picture, one sentence per path, the mistakes to avoid, and the thesis.
[pause: 1.8]

[slide: v-623]
[pause: 1.3]
C: The final picture.
[reveal: v-624]
[pause: 0.45]
C: Fans reach a C-D-N and gateway that check an admission token.
[reveal: v-625]
[pause: 0.45]
C: The waiting room holds the lobby and the pointer,
[reveal: v-626]
[pause: 0.45]
C: and the controller sets its rate from shop health.
[reveal: v-627]
[pause: 0.45]
C: The booking API makes one conditional claim on the seat database,
[reveal: v-628]
[pause: 0.45]
C: which writes an outbox row to the event log.
[reveal: v-629]
[pause: 0.45]
C: The sweeper frees expired holds.
[reveal: v-630]
[pause: 0.45]
C: The snapshot builder turns the log into a versioned bitmap for the seat map.
[reveal: v-631]
[pause: 0.45]
C: The order service freezes seats,
[reveal: v-632]
[pause: 0.45]
C: calls the provider,
[reveal: v-633]
[pause: 0.45]
C: and a reconciler resolves silence.
[reveal: v-634]
[pause: 0.45]
C: A probe plays a fan,
[reveal: v-635]
[pause: 0.45]
C: continuously.
[pause: 1.1]

[slide: v-636]
[pause: 1.0]
C: Six paths, one sentence each.
C: Join: a lobby and a signed place in line, one cached answer identical for everyone.
[reveal: v-637]
[pause: 0.45]
C: Browse: an immutable layout and a versioned bitmap.
[reveal: v-638]
[pause: 0.45]
C: Hold: one conditional update, all or nothing, with a four-oh-nine and a fresh map.
[reveal: v-639]
[pause: 0.45]
C: Pay: freeze, authorize, sell on approval, and silence is unknown, not failure.
[reveal: v-640]
[pause: 0.45]
C: Expire: the claim treats an expired hold as free, and a sweeper makes the map catch up.
[reveal: v-641]
[pause: 0.45]
C: Release: new rows and a new layout version, and a waitlist is a consumer.
[pause: 1.0]

[slide: v-642]
[pause: 1.0]
C: Eight fixes, each naming the property it protects.
C: One: a conditional update and a unique ticket constraint, for safety one.
[reveal: v-643]
[pause: 0.45]
C: Two: lazy expiry and the sweeper, for liveness.
[reveal: v-644]
[pause: 0.45]
C: Three: freeze, authorize then capture, unknown and the reconciler, for safety two.
[reveal: v-645]
[pause: 0.45]
C: Four: the waiting room, the controller and the token, for the opening minute.
[reveal: v-646]
[pause: 0.45]
C: Five: the lottery, signed tokens and verified accounts, for fairness.
[reveal: v-647]
[pause: 0.45]
C: Six: an immutable layout and a versioned bitmap.
[reveal: v-648]
[pause: 0.45]
C: Seven: new rows, consumers and cells, so new demand does not mean a rewrite.
[reveal: v-649]
[pause: 0.45]
C: Eight: indicators, a synthetic fan and a load test, so the silent failures are not silent.
[pause: 1.0]

[slide: v-650]
[pause: 0.6]
C: Ten mistakes in this round.
C: In the design: check availability then insert.
C: A database lock held through checkout.
C: Expiry that only a sweeper provides.
C: A live seat map read from the claims database.
C: Strict first-come at the start.
[reveal: v-651]
[pause: 0.45]
C: In judgment: a timeout treated as a decline.
C: No idempotency key on a payment or a purchase.
C: Never asking what fair means, or who decides.
C: Numbers with no decision attached.
C: And no plan for the day it fails.
[pause: 0.8]

[slide: v-652]
[pause: 0.7]
V: Fifty thousand seats, a million fans. The design is the distance between what arrives and what is admitted. A rejection system, with an atomic claim, a hold that expires, a payment that may never answer, and a way to know when any of it is broken.
[pause: 1.2]
N: Four sentences the interviewer can write down: what I built, what I traded away, what could still hurt, and what I would do next. That close is often the whole debrief.
[pause: 1.6]
