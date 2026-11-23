# SD-39 Nearby drivers and ride matching: reference solution (Staff L6/L7, compact cut)

<!-- Video script for slide-video-kit/scripts/build_video.py. [slide: v-NNN] = frames/v-NNN.png; [reveal: v-NNN] = the next
     reveal step of the same slide. Generated from src/*.py: edit the sources, not this file. -->
<!-- voices: N=af_heart@0.92 I=bf_emma@0.95 C=am_michael@0.9 V=am_michael@0.84 -->
<!-- names: C=Candidate V=Candidate N=Coach I=Interviewer -->
<!-- say: API=A-P-I SDK=S-D-K TB=terabytes PB=petabytes GB=gigabytes HTTP=H-T-T-P HTTPS=H-T-T-P-S ID=I-D IDs=I-Ds ETA=E-T-A H3=H-three PostGIS=Post-G-I-S SQL=S-Q-L etcd=et-see-dee gRPC=G-R-P-C NYE=New-Year's-Eve CPU=C-P-U CPUs=C-P-Us GPU=G-P-U GPUs=G-P-Us Kafka=Kahf-kah ClickHouse=Click-House GCS=G-C-S MCAP=M-cap SHA-256=shaw-two-fifty-six DAG=dag Kueue=queue Bigtable=Big-table CI=C-I EM=E-M -->


## 0 Cold open

[slide: v-001]
[pause: 1.2]
C: Nearby drivers sounds like a geometry question: put drivers on a map, find the closest one. It is asked at every ride-hailing and delivery company, and at Google, because the geometry is the easy half. The hard half is that two riders can be handed the same driver in the same second.
[pause: 1.8]

[slide: v-002]
[pause: 0.6]
I: Design the system that matches riders to nearby drivers. Drivers move constantly, and a rider expects a match in seconds.
[pause: 1.5]

[slide: v-003]
[pause: 1.3]
C: Here is the hook. There are two problems here, and the weak answer treats them as one.
C: A geo problem: a million location writes a second, and a lookup by area in milliseconds. That can be fast and even lossy. And a contention problem: two riders, one driver, the same second. That must be exact. The design keeps them in different stores with different guarantees.
[pause: 1.1]

[slide: v-004]
[pause: 1.0]
N: Five axes.
[reveal: v-005]
[pause: 0.45]
N: Requirements: the strong answer asks what must never happen, and the answer is one driver, two riders.
[reveal: v-006]
[pause: 0.45]
N: Estimates: the write rate, and what it rules out.
[reveal: v-007]
[pause: 0.45]
N: Correctness: not nearest-wins, but a conditional claim, fencing and an offer state machine.
[reveal: v-008]
[pause: 0.45]
N: Depth: cells as one-dimensional keys, neighbours, hot cells and expiry, not just the word geohash.
[reveal: v-009]
[pause: 0.45]
N: Operations: probe trips, and idle drivers sitting next to riders who were told there are none.
[reveal: v-010]
[pause: 0.45]
C: And the rule for the round: the geo index may be stale; the claim may never be wrong.
[pause: 1.0]

[slide: v-011]
[pause: 0.7]
V: Keep where drivers are as fast, overwrite-only, lossy memory. And keep who gets which driver as one exact conditional write, owned by one matcher per city.
[pause: 1.6]

[slide: v-012]
[pause: 0.6]
C: The order I'll follow.
[reveal: v-013]
[pause: 0.45]
C: First, the requirements, the write rate and the density, and the theory: cells as keys, soft state, claims, leases and batches.
[reveal: v-014]
[pause: 0.45]
C: Then the A-P-I and the data, three versions on one picture, every path as a sequence, and the two important containers opened up with their technologies.
[reveal: v-015]
[pause: 0.45]
C: Then most of the time on six challenges, each fixed one level down, and each fix creating the next question.
[pause: 0.8]

[pause: 1.4]

## 1 Requirements and scope

[slide: v-016]
[pause: 1.2]
C: The scale first, then five questions.
[pause: 1.8]

[slide: v-017]
[pause: 0.6]
C: The scale.
[reveal: v-018]
[pause: 0.45]
C: Nine hundred million trips a month, thirty million a day.
[reveal: v-019]
[pause: 0.45]
C: Five million drivers online at peak, each sending a location every four seconds.
[reveal: v-020]
[pause: 0.45]
C: And the peak: one city at midnight on New Year's Eve, ten times its usual requests for ten minutes, with three thousand drivers inside two kilometres downtown.
[reveal: v-021]
[pause: 0.45]
C: Every number later starts from these.
[pause: 0.8]

[slide: v-022]
[pause: 0.6]
C: What must never happen?
[reveal: v-023]
[pause: 0.45]
I: A driver must never be assigned to two riders.
C: That's the safety property, and it isn't a geo property. It needs a claim.
[pause: 0.6]

[slide: v-024]
[pause: 0.6]
C: How fast must a match be?
[reveal: v-025]
[pause: 0.45]
I: An offer on a driver's phone within five seconds of the request.
C: Five seconds leaves room to wait a moment and match a batch, which can beat first come, first served.
[pause: 0.6]

[slide: v-026]
[pause: 0.6]
C: Nearest by distance, or by arrival time?
[reveal: v-027]
[pause: 0.45]
I: Nearest is fine for version one. By E-T-A is better.
C: Then distance shortlists and E-T-A ranks. Challenge five.
[pause: 0.6]

[slide: v-028]
[pause: 0.6]
C: Do we ever match across cities?
[reveal: v-029]
[pause: 0.45]
I: No. Cities are independent.
C: That's the biggest simplification on the board: a city is a unit of sharding, of failure and of ownership.
[pause: 0.6]

[slide: v-030]
[pause: 0.6]
C: What else is in scope?
[reveal: v-031]
[pause: 0.45]
I: Matching, and showing the rider the approaching car. Not pricing, payment or routing.
C: Routing is a dependency I call for travel times, not something I build.
[pause: 0.6]

[slide: v-032]
[pause: 0.6]
C: Four functional requirements.
[reveal: v-033]
[pause: 0.45]
C: One, report: a location from every online driver every four seconds.
[reveal: v-034]
[pause: 0.45]
C: Two, match: a request becomes an offer to one nearby driver within five seconds.
[reveal: v-035]
[pause: 0.45]
C: Three, accept: an accepted offer becomes a trip, exactly once.
[reveal: v-036]
[pause: 0.45]
C: Four, track: the rider sees the car approach.
[pause: 0.8]

[slide: v-037]
[pause: 0.6]
C: The numbers.
[reveal: v-038]
[pause: 0.45]
C: Zero drivers on two trips.
[reveal: v-039]
[pause: 0.45]
C: Five seconds from request to offer.
[reveal: v-040]
[pause: 0.45]
C: No location older than eight seconds used for a match.
[reveal: v-041]
[pause: 0.45]
C: Three and a half nines per city.
[reveal: v-042]
[pause: 0.45]
C: And a city's outage must not touch another city.
[pause: 0.8]

[slide: v-043]
[pause: 0.6]
C: In scope: location intake, the nearby index, matching, claims and offers, the trip until pickup, and tracking the car.
[reveal: v-044]
[pause: 0.45]
C: Out, on purpose: pricing and surge, payment, routing and its models, fraud, onboarding, and pooled rides.
[reveal: v-045]
[pause: 0.45]
C: Pooled rides I'd mention aloud: they change a claim from one-or-zero to capacity. The same conditional write works with a seat count instead of a state, but it's a different product.
[pause: 0.8]

[slide: v-046]
[pause: 1.3]
C: The context.
[reveal: v-047]
[pause: 0.45]
C: Riders request rides and watch the car arrive.
[reveal: v-048]
[pause: 0.45]
C: The matching system, one box.
[reveal: v-049]
[pause: 0.45]
C: Drivers report locations and accept offers on a stream.
[reveal: v-050]
[pause: 0.45]
C: Routing gives travel times.
[reveal: v-051]
[pause: 0.45]
C: And the trip lifecycle, with pricing and payment, hears when a trip starts. Out of scope.
[pause: 1.1]

[slide: v-052]
[pause: 0.7]
V: The core is three things. A lossy, fast location index. An exact claim. And an offer that expires.
[pause: 1.6]

[pause: 1.4]

## 2 Estimates

[slide: v-053]
[pause: 1.2]
C: Numbers next, from the scale line, each ending in a decision. Illustrative.
[pause: 1.8]

[slide: v-054]
[pause: 1.0]
C: Locations.
[reveal: v-055]
[pause: 0.45]
C: Five million drivers every four seconds is one point two five million writes a second, a hundred and twenty-five megabytes a second.
[reveal: v-056]
[pause: 0.45]
C: Written durably, that's a hundred and ten billion rows, eleven terabytes, a day, of data that's stale in four seconds. Not a database.
[reveal: v-057]
[pause: 0.45]
C: In memory, all five million drivers are about a gigabyte. One machine could hold them. So I shard by city for isolation, not for capacity.
[reveal: v-058]
[pause: 0.45]
C: And five million streams at fifty thousand per pod is a hundred gateway pods.
[pause: 1.0]

[slide: v-059]
[pause: 1.0]
C: Density, because averages hide it.
[reveal: v-060]
[pause: 0.45]
C: Downtown at six, three thousand drivers within two kilometres, about twelve and a half square kilometres.
[reveal: v-061]
[pause: 0.45]
C: A resolution-eight cell is point seven four square kilometres, so about a hundred and eighty drivers a cell on average, and the busiest over three hundred. Those get split to resolution nine, a tenth of a square kilometre.
[reveal: v-062]
[pause: 0.45]
C: In a suburb at a quiet hour, half a driver per cell. One ring isn't enough; the query expands until it has twenty.
[reveal: v-063]
[pause: 0.45]
C: And ranking every downtown driver by E-T-A would be three thousand routing pairs per request. So distance shortlists twenty first.
[pause: 1.0]

[slide: v-064]
[pause: 1.0]
C: Matching.
[reveal: v-065]
[pause: 0.45]
C: Nine hundred million trips a month is about three hundred and fifty a second. Double it for cancellations and retries, triple it for the peak hour: about two thousand one hundred requests a second. A regional database takes that many conditional writes.
[reveal: v-066]
[pause: 0.45]
C: The biggest city on New Year's Eve: ten percent of the peak, times ten, for ten minutes. The same order, in one city: one matcher still copes.
[reveal: v-067]
[pause: 0.45]
C: A two-kilometre search is two rings of H3 resolution-eight cells: nineteen cells, about fourteen square kilometres. Nineteen lookups.
[reveal: v-068]
[pause: 0.45]
C: And twenty candidates each for E-T-A is forty-two thousand pairs a second: shortlist, batch, and cache by cell pair.
[pause: 1.0]

[slide: v-069]
[pause: 1.3]
C: The budget. Up to two seconds waiting for the batch tick. About seven tenths of a second for the index, the E-T-A matrix and the claim. Half a second to push the offer down the driver's stream. About three seconds of five.
C: The spare is for a slow E-T-A call, which gets a timeout and a fallback, not more waiting.
[pause: 1.1]

[pause: 1.4]

## 3 Theory

[slide: v-070]
[pause: 1.2]
C: The theory: what makes this hard, in terms that outlive product names. Five mechanisms, the options, what will go wrong.
[pause: 1.8]

[slide: v-071]
[pause: 0.6]
C: What it is, and what it is not.
[reveal: v-072]
[pause: 0.45]
V: Assigning scarce, moving resources to requests, exactly once, from an approximate picture of where they are.
[reveal: v-073]
[pause: 0.45]
C: Not a map search: restaurants near me never run out; a driver can be given away only once.
[reveal: v-074]
[pause: 0.45]
C: Not routing: routing says how long; matching says who.
[reveal: v-075]
[pause: 0.45]
C: And not fleet telemetry, which keeps history. Matching needs the latest four seconds. That's question ninety-seven.
[pause: 0.8]

[slide: v-076]
[pause: 0.6]
C: Safety first.
[reveal: v-077]
[pause: 0.45]
V: S-one: a driver is never assigned to two trips at once.
[reveal: v-078]
[pause: 0.45]
V: S-two: an accepted offer becomes exactly one trip. A retry changes nothing.
[reveal: v-079]
[pause: 0.45]
C: Liveness. L-one: every request gets an offer or a clear no within five seconds.
[reveal: v-080]
[pause: 0.45]
C: L-two: a driver who doesn't respond, or vanishes, is released within seconds. Otherwise drivers leak out of the pool.
[pause: 0.8]

[slide: v-081]
[pause: 0.6]
C: Mechanism one: cells as keys.
[reveal: v-082]
[pause: 0.45]
C: It protects L-one.
[reveal: v-083]
[pause: 0.45]
C: Every point maps to a hexagonal cell with a sixty-four-bit I-D. A radius query becomes the pickup's cell plus its rings of neighbours: a handful of map lookups.
[reveal: v-084]
[pause: 0.45]
C: It rules out computing distance to every driver, and, because the ring includes neighbours, missing a driver just across a boundary.
[reveal: v-085]
[pause: 0.45]
C: It costs a cell size to choose, and some extra cells read at the edges.
[pause: 0.8]

[slide: v-086]
[pause: 1.3]
C: Drawn: the pickup's cell in the middle, six neighbours in the first ring, twelve in the second. Nineteen cells, about fourteen square kilometres.
C: The green driver is fifty metres away but in the next cell. A query of the pickup's cell alone would miss them; the ring doesn't. And each cell is a sixty-four-bit integer, so the whole query is nineteen hash-map lookups.
[pause: 1.1]

[slide: v-087]
[pause: 0.6]
C: Mechanism two: soft state.
[reveal: v-088]
[pause: 0.45]
C: It protects freshness, and so L-one.
[reveal: v-089]
[pause: 0.45]
C: Keep only the latest location. Drop an update whose sequence number is older than the one held. Forget a driver who has been silent for twelve seconds.
[reveal: v-090]
[pause: 0.45]
C: It rules out writing a million durable rows a second, and an old, buffered position overwriting a new one.
[reveal: v-091]
[pause: 0.45]
C: It costs this: a lost shard is empty until drivers report again. About four seconds.
[pause: 0.8]

[slide: v-092]
[pause: 0.6]
C: Mechanism three, the crux: a conditional claim, fenced.
[reveal: v-093]
[pause: 0.45]
C: It protects S-one.
[reveal: v-094]
[pause: 0.45]
C: A driver is claimed by one write that succeeds only if the driver is still available, at the version the matcher read, and the matcher's epoch is the city's current one.
[reveal: v-095]
[pause: 0.45]
C: It rules out two riders getting one driver, and a matcher that lost its leadership still claiming.
[reveal: v-096]
[pause: 0.45]
C: It costs a retry for whoever loses, and a small, strongly consistent store.
[pause: 0.8]

[slide: v-097]
[pause: 0.6]
C: Mechanism four: leases and timeouts.
[reveal: v-098]
[pause: 0.45]
C: They protect L-two and S-two.
[reveal: v-099]
[pause: 0.45]
C: An offer expires in fifteen seconds. A driver on a trip holds a thirty-second lease, renewed by heartbeats. An accept carries the offer I-D, so a retried accept is the same accept.
[reveal: v-100]
[pause: 0.45]
C: It rules out drivers stuck as offered forever, and a double accept creating two trips.
[reveal: v-101]
[pause: 0.45]
C: It costs choosing timeouts, and the occasional false release of a slow driver.
[pause: 0.8]

[slide: v-102]
[pause: 0.6]
C: Mechanism five: batched assignment.
[reveal: v-103]
[pause: 0.45]
C: It protects L-one, and efficiency.
[reveal: v-104]
[pause: 0.45]
C: Every two seconds, take all pending requests in a city and solve a small minimum-cost assignment over their candidates' E-T-As.
[reveal: v-105]
[pause: 0.45]
C: It rules out greedy first-come choices that grab the driver a later rider needed more.
[reveal: v-106]
[pause: 0.45]
C: It costs up to two seconds of waiting, and a solver.
[pause: 0.8]

[slide: v-107]
[pause: 1.0]
C: Before the options for matching, the options for cutting the map. Four common ones.
[reveal: v-108]
[pause: 0.45]
C: Geohash: rectangles named by a prefix. Simple, but two neighbours across a prefix edge share no prefix, and the cells distort away from the equator.
[reveal: v-109]
[pause: 0.45]
C: A quadtree: squares that split when they fill. It adapts to density, but a moving point keeps rebalancing it, and it's hard to shard.
[reveal: v-110]
[pause: 0.45]
C: S-two: quads on a cube in Hilbert order, so nearby cells have nearby I-Ds. Strong, but cell areas vary by about two times.
[reveal: v-111]
[pause: 0.45]
C: H-three, which I pick: hexagons, where all six neighbours are the same distance away, so a ring really is a ring. The cost: hexagons don't nest perfectly, so a child cell can straddle its parent's edge. For finding nearby drivers, that doesn't matter.
[pause: 1.0]

[slide: v-112]
[pause: 1.0]
C: Five ways.
[reveal: v-113]
[pause: 0.45]
C: A, drivers in a database: a million writes a second and a scan per request.
[reveal: v-114]
[pause: 0.45]
C: B, a geo index with nearest-wins and no claim: fast, and wrong the first time two riders share a driver.
[reveal: v-115]
[pause: 0.45]
C: C, a lock per driver: correct, but a lock service sits on the hot path, and its expiry is ambiguous.
[reveal: v-116]
[pause: 0.45]
C: D, one global optimiser: cities are independent, so it buys nothing.
[reveal: v-117]
[pause: 0.45]
C: E, which I pick: a geo index, one matcher per city, conditional claims, and batches.
[reveal: v-118]
[pause: 0.45]
V: Lossy where it's cheap, exact where it matters, and one writer per city.
[pause: 1.0]

[slide: v-119]
[pause: 1.3]
C: Mechanism three at protocol level. A matcher with epoch seven, and an old leader that hasn't noticed it lost, epoch six.
[reveal: v-120]
[pause: 0.45]
C: The new leader claims driver forty-two: if available, at version eighteen, with epoch at least seven.
[reveal: v-121]
[pause: 0.45]
C: The old leader sends the same claim, with epoch six.
[reveal: v-122]
[pause: 0.45]
C: The first one wins: version nineteen, offered to rider seventy-seven.
[reveal: v-123]
[pause: 0.45]
C: The second finds version nineteen and a city epoch of seven. Zero rows.
[reveal: v-124]
[pause: 0.45]
C: The deposed leader learns it lost from the database, not from a clock.
[pause: 1.1]

[slide: v-125]
[pause: 1.0]
C: The failure catalogue.
[reveal: v-126]
[pause: 0.45]
C: One: two riders, one driver, the same second.
[reveal: v-127]
[pause: 0.45]
C: Two: a driver accepts, then vanishes.
[reveal: v-128]
[pause: 0.45]
C: Three: a driver across a cell boundary, and three thousand drivers in one cell.
[reveal: v-129]
[pause: 0.45]
C: Four: a location shard dies.
[reveal: v-130]
[pause: 0.45]
C: Five: the nearest driver is across a river.
[reveal: v-131]
[pause: 0.45]
C: Six: riders hear no drivers while drivers sit idle.
[pause: 1.0]

[pause: 1.4]

## 4 API and entities

[slide: v-132]
[pause: 1.2]
C: The A-P-I, then the data. Every endpoint is tagged with its requirement.
[pause: 1.8]

[slide: v-133]
[pause: 1.0]
C: Requesting a ride, for F-R-two. An idempotency key, because a rider who taps twice in a tunnel must not get two cars. Pickup, drop-off and product.
C: The answer is immediate and says matching. The driver arrives later, pushed to the rider's app, because matching takes seconds and nobody should hold a request open for it.
[pause: 1.0]

[slide: v-134]
[pause: 1.0]
C: Three more.
[reveal: v-135]
[pause: 0.45]
C: The driver's stream, for F-R-one: position, heading and a sequence number every four seconds. The sequence number lets the server drop an old position that arrives late.
[reveal: v-136]
[pause: 0.45]
C: Offers and accepts, on the same stream, for F-R-three. An offer expires; an accept names the offer, so a retried accept is the same accept.
[reveal: v-137]
[pause: 0.45]
C: And the rider's car position, for F-R-four.
[pause: 1.0]

[slide: v-138]
[pause: 1.0]
C: The offer on the wire, down the driver's stream, for F-R-three. It names itself, offer nine-oh-one, says where and how far, and says when it expires: fifteen seconds after it was made.
C: The accept carries the offer I-D and the driver-state version the claim produced. A retried accept with the same offer I-D returns the same trip, and an accept for an offer that has expired, or for an older version, is refused. Both halves of S-two are in those two fields.
[pause: 1.0]

[slide: v-139]
[pause: 1.3]
C: The conceptual model.
[reveal: v-140]
[pause: 0.45]
C: A rider.
[reveal: v-141]
[pause: 0.45]
C: A rider makes requests.
[reveal: v-142]
[pause: 0.45]
C: A request becomes at most one trip.
[reveal: v-143]
[pause: 0.45]
C: A driver drives many trips over time, one at a time.
[reveal: v-144]
[pause: 0.45]
C: An offer exists only for a request: a weak entity, identified by the request and an offer I-D, with an expiry. A driver receives many offers.
[reveal: v-145]
[pause: 0.45]
C: And a driver's location: the last place they were seen, a cell and a sequence number. Only the latest.
[pause: 1.1]

[slide: v-146]
[pause: 1.3]
C: The physical tables.
[reveal: v-147]
[pause: 0.45]
C: Driver state: available, offered or on a trip, with a version and a lease. Claims are one conditional update here.
[reveal: v-148]
[pause: 0.45]
C: Trips, in the regional PostgreSQL.
[reveal: v-149]
[pause: 0.45]
C: Offers, one row each, with an expiry and an outcome.
[reveal: v-150]
[pause: 0.45]
C: The city lease, mirroring etcd's epoch, so claims can be fenced.
[reveal: v-151]
[pause: 0.45]
C: In memory, per city shard: driver to cell, and cell to drivers. Never written to disk.
[reveal: v-152]
[pause: 0.45]
C: And the location log, batched, for history only. Matching never reads it.
[pause: 1.1]

[pause: 1.4]

## 5 High-level design

[slide: v-153]
[pause: 1.2]
C: The design in three versions, on one picture that only changes by deltas.
[pause: 1.8]

[slide: v-154]
[pause: 1.3]
C: Version one, the simplest thing that works.
[reveal: v-155]
[pause: 0.45]
C: A rider requests.
[reveal: v-156]
[pause: 0.45]
C: The ride A-P-I writes a trip.
[reveal: v-157]
[pause: 0.45]
C: Into a trip store, which also holds every driver's location. It asks it for the nearest available driver.
[reveal: v-158]
[pause: 0.45]
C: A driver reports a location.
[reveal: v-159]
[pause: 0.45]
C: The driver gateway updates the driver's row. The objection: one point two five million durable updates a second, and a distance scan per request.
[pause: 1.1]

[slide: v-160]
[pause: 1.3]
C: Version two answers that.
[reveal: v-161]
[pause: 0.45]
C: Version one, carried; the location update no longer goes to the trip store.
[reveal: v-162]
[pause: 0.45]
C: New, a location index: in memory, cells to drivers, overwrite-only, sharded by city. The A-P-I asks it for nearby drivers. The objection: two riders asking at once get the same nearest driver.
[pause: 1.1]

[slide: v-163]
[pause: 1.3]
C: Version three answers that.
[reveal: v-164]
[pause: 0.45]
C: Version two, carried.
[reveal: v-165]
[pause: 0.45]
C: New, a matcher: one leader per city. It batches requests, takes candidates from the index, and claims drivers with a conditional write.
[reveal: v-166]
[pause: 0.45]
C: New, routing for E-T-A: candidates are ranked by time, not distance.
[reveal: v-167]
[pause: 0.45]
C: New, a location log: the gateway appends history in batches, for analytics.
[reveal: v-168]
[pause: 0.45]
C: Which feeds E-T-A training, outside the system. This is the baseline.
[pause: 1.1]

[slide: v-169]
[pause: 1.0]
C: The containers.
[reveal: v-170]
[pause: 0.45]
C: The ride A-P-I: requests, idempotency, and what the rider sees.
[reveal: v-171]
[pause: 0.45]
C: The driver gateway: five million streams, locations in and offers out.
[reveal: v-172]
[pause: 0.45]
C: The location index: the latest position, per city, in memory. A million and a quarter updates a second in about a gigabyte.
[reveal: v-173]
[pause: 0.45]
C: The matcher: the only writer of assignments in its city, ticking every two seconds.
[reveal: v-174]
[pause: 0.45]
C: The trip store: trips, offers, driver state and claims.
[reveal: v-175]
[pause: 0.45]
C: And the location log: history only. Matching never reads it.
[pause: 1.0]

[slide: v-176]
[pause: 1.0]
C: Before the flows, the trip's state machine, because every failure later is a missing exit from one of these states.
[reveal: v-177]
[pause: 0.45]
C: Matching: entered on a request, left by a claim or a clear no, within five seconds.
[reveal: v-178]
[pause: 0.45]
C: Offered: entered by the claim, left by accept, decline or a fifteen-second expiry. The expiry is what returns the driver to the pool.
[reveal: v-179]
[pause: 0.45]
C: Accepted: left by arriving, or by a lapsed thirty-second lease if the driver vanishes.
[reveal: v-180]
[pause: 0.45]
C: Arriving: the same lease, renewed by heartbeats, and the rider may cancel.
[reveal: v-181]
[pause: 0.45]
C: On trip: from pickup to drop-off, handed over to the trip lifecycle. Every state has an owner, and every state has a timer or an event that ends it.
[pause: 1.0]

[slide: v-182]
[pause: 1.3]
C: A location, numbered.
[reveal: v-183]
[pause: 0.45]
C: One: the driver's app sends it on its stream.
[reveal: v-184]
[pause: 0.45]
C: Two: the gateway forwards it to the city's index shard: latest wins.
[reveal: v-185]
[pause: 0.45]
C: Three: and appends it to the log in a batch.
[reveal: v-186]
[pause: 0.45]
C: Four: history flows to analytics.
[pause: 1.1]

[slide: v-187]
[pause: 1.3]
C: A request, numbered.
[reveal: v-188]
[pause: 0.45]
C: One: the rider asks.
[reveal: v-189]
[pause: 0.45]
C: Two: the request joins the city matcher's queue.
[reveal: v-190]
[pause: 0.45]
C: Three: candidates from two rings of cells.
[reveal: v-191]
[pause: 0.45]
C: Four: an E-T-A matrix for the shortlist.
[reveal: v-192]
[pause: 0.45]
C: Five: one conditional claim per assignment.
[reveal: v-193]
[pause: 0.45]
C: Six: the offer, pushed down the driver's stream.
[pause: 1.1]

[slide: v-194]
[pause: 1.3]
C: Report, as a sequence.
[reveal: v-195]
[pause: 0.45]
C: Driver forty-two sends sequence four thousand eight hundred and twelve.
[reveal: v-196]
[pause: 0.45]
C: The gateway updates the shard.
[reveal: v-197]
[pause: 0.45]
C: It's newer than what the shard holds, so it overwrites.
[reveal: v-198]
[pause: 0.45]
C: A batch of two thousand updates goes to the log every second.
[reveal: v-199]
[pause: 0.45]
C: And if driver forty-two goes silent for twelve seconds, they expire from the index: no longer offered rides.
[pause: 1.1]

[slide: v-200]
[pause: 1.3]
C: Match, as a sequence.
[reveal: v-201]
[pause: 0.45]
C: The rider posts a request with an idempotency key.
[reveal: v-202]
[pause: 0.45]
C: It joins the matcher's pending set.
[reveal: v-203]
[pause: 0.45]
C: On the tick, forty requests are pending in this city.
[reveal: v-204]
[pause: 0.45]
C: Two rings of cells around each pickup.
[reveal: v-205]
[pause: 0.45]
C: Twenty candidates each, by distance.
[reveal: v-206]
[pause: 0.45]
C: One E-T-A matrix, forty by twenty.
[reveal: v-207]
[pause: 0.45]
C: A minimum-cost assignment: rider seventy-seven to driver forty-two.
[pause: 1.1]

[slide: v-208]
[pause: 1.3]
C: Accept, as a sequence.
[reveal: v-209]
[pause: 0.45]
C: The matcher claims driver forty-two: if available, at version eighteen, with epoch seven.
[reveal: v-210]
[pause: 0.45]
C: One row: claimed.
[reveal: v-211]
[pause: 0.45]
C: The offer, valid for fifteen seconds.
[reveal: v-212]
[pause: 0.45]
C: Pushed to the driver.
[reveal: v-213]
[pause: 0.45]
C: The driver accepts, naming the offer: a retry would be the same accept.
[reveal: v-214]
[pause: 0.45]
C: The rider sees driver forty-two, four minutes away.
[pause: 1.1]

[slide: v-215]
[pause: 1.3]
C: Track, as a sequence.
[reveal: v-216]
[pause: 0.45]
C: The driver's location, every four seconds.
[reveal: v-217]
[pause: 0.45]
C: Driver forty-two is on trip fifty-five twelve, so the gateway forwards it to that trip's rider.
[reveal: v-218]
[pause: 0.45]
C: Smoothed.
[reveal: v-219]
[pause: 0.45]
C: And the rider's map animates between points. No polling, no database read.
[pause: 1.1]

[pause: 1.4]

## 5.1 Components and technologies

[slide: v-220]
[pause: 1.2]
C: One level down: what each box runs on, the two containers the challenges open, and what I rejected.
[pause: 1.8]

[slide: v-221]
[pause: 1.3]
C: The same container view, with technologies.
[reveal: v-222]
[pause: 0.45]
C: The ride A-P-I: Go on Kubernetes.
[reveal: v-223]
[pause: 0.45]
C: The gateway: Go, gRPC streams, fifty thousand per pod.
[reveal: v-224]
[pause: 0.45]
C: The location index: Go, in memory, H3, sharded by city.
[reveal: v-225]
[pause: 0.45]
C: The matcher: Go, one leader per city through an etcd lease.
[reveal: v-226]
[pause: 0.45]
C: The trip store: regional PostgreSQL with conditional claims.
[reveal: v-227]
[pause: 0.45]
C: And the location log: Kafka.
[pause: 1.1]

[slide: v-228]
[pause: 1.3]
C: Inside the matcher.
[reveal: v-229]
[pause: 0.45]
C: Requests arrive from the ride A-P-I.
[reveal: v-230]
[pause: 0.45]
C: The batcher collects them for a two-second tick.
[reveal: v-231]
[pause: 0.45]
C: Candidates: two rings of cells from the location index, top twenty by distance.
[reveal: v-232]
[pause: 0.45]
C: The E-T-A ranker: one matrix call to routing, cached per cell pair.
[reveal: v-233]
[pause: 0.45]
C: The assigner solves min-cost over the whole batch.
[reveal: v-234]
[pause: 0.45]
C: The claimer writes conditionally, carrying the epoch from the city lease in etcd.
[reveal: v-235]
[pause: 0.45]
C: Into the trip store.
[reveal: v-236]
[pause: 0.45]
C: And the offer manager runs the state machine and its timers, pushing offers through the gateway. Challenges one, two and five live here.
[pause: 1.1]

[slide: v-237]
[pause: 1.3]
C: Inside the location index.
[reveal: v-238]
[pause: 0.45]
C: Updates arrive from the gateway.
[reveal: v-239]
[pause: 0.45]
C: Ingest drops anything older than the sequence it holds.
[reveal: v-240]
[pause: 0.45]
C: The cell mapper turns latitude and longitude into an H3 resolution-eight cell.
[reveal: v-241]
[pause: 0.45]
C: The driver table: driver to cell and sequence.
[reveal: v-242]
[pause: 0.45]
C: Expiry removes drivers silent for twelve seconds.
[reveal: v-243]
[pause: 0.45]
C: The cell table: cell to drivers.
[reveal: v-244]
[pause: 0.45]
C: A hot cell, over three hundred drivers, is indexed again at resolution nine.
[reveal: v-245]
[pause: 0.45]
C: The query reads rings, nearest first.
[reveal: v-246]
[pause: 0.45]
C: For the matcher. Challenges three and four live here.
[pause: 1.1]

[slide: v-247]
[pause: 1.0]
C: Per city: driver to (cell, position, seq) and cell to drivers. Older sequence numbers are dropped; silent drivers expire after 12 s.
[reveal: v-248]
[pause: 0.45]
C: Why: A location lives four seconds.
[reveal: v-249]
[pause: 0.45]
C: Rejected: Redis GEO. Members never expire, and every update is a hop to a shared cluster.
[reveal: v-250]
[pause: 0.45]
C: PostGIS. A durable write per update.
[pause: 1.0]

[slide: v-251]
[pause: 1.0]
C: UPDATE driver_state … WHERE state='available' AND version=$v AND epoch current. One row back: claimed.
[reveal: v-252]
[pause: 0.45]
C: Why: Claims are thousands a second and must be linearizable.
[reveal: v-253]
[pause: 0.45]
C: Rejected: Redis for claims. Asynchronous replication can lose a claim in a fail-over.
[reveal: v-254]
[pause: 0.45]
C: Cassandra LWT. A Paxos round per claim, and a second store to run.
[pause: 1.0]

[slide: v-255]
[pause: 1.0]
C: About 50,000 streams per pod, 100 pods. A driver to pod table lets the matcher push to the right one.
[reveal: v-256]
[pause: 0.45]
C: Why: An open stream delivers an offer in under a second and carries locations too.
[reveal: v-257]
[pause: 0.45]
C: Rejected: HTTP polling. Offers wait for the next poll.
[reveal: v-258]
[pause: 0.45]
C: An MQTT broker. An honest equal.
[pause: 1.0]

[slide: v-259]
[pause: 1.0]
C: Every 2 s: shortlist 20 per request, one ETA matrix, a min-cost assignment, claims carrying the epoch.
[reveal: v-260]
[pause: 0.45]
C: Why: One writer per city means no racing matchers.
[reveal: v-261]
[pause: 0.45]
C: Rejected: Racing stateless matchers. Constant claim conflicts and retries.
[reveal: v-262]
[pause: 0.45]
C: ZooKeeper. An honest equal.
[pause: 1.0]

[slide: v-263]
[pause: 1.0]
C: The stack on one slide, as I would leave it on the whiteboard.
[reveal: v-264]
[pause: 0.45]
C: Location index: in-memory H3, per city. Not Redis GEO, PostGIS. Overwrite-only; expiry; 1 GB fits.
[reveal: v-265]
[pause: 0.45]
C: Trip store: PostgreSQL, regional. Not Redis, Cassandra LWT. A claim is one conditional update.
[reveal: v-266]
[pause: 0.45]
C: Driver gateway: gRPC streams. Not polling, MQTT. Offers pushed on an open stream.
[reveal: v-267]
[pause: 0.45]
C: Matcher: leader per city, etcd. Not racing matchers, ZooKeeper. One writer; epoch fences.
[reveal: v-268]
[pause: 0.45]
N: Naming a product is not the signal. Naming the property that rules out its rival is. Interviewers go one level down on whichever box you name, so name only what you can defend.
[pause: 1.0]

[pause: 1.4]

## 5.2 When you don't need all this

[slide: v-269]
[pause: 1.2]
C: Before I break it: for one city, a much smaller design is right.
[pause: 1.8]

[slide: v-270]
[pause: 1.3]
C: The alternate path, on version three.
[reveal: v-271]
[pause: 0.45]
C: The matcher goes away.
[reveal: v-272]
[pause: 0.45]
C: And the in-memory index.
[reveal: v-273]
[pause: 0.45]
C: Instead, drivers update a PostGIS row every fifteen seconds. A request runs a radius query with a spatial index, and claims a driver with select for update skip locked, so two requests never take the same row.
[reveal: v-274]
[pause: 0.45]
C: What it gives up: durable writes for data that's stale in seconds, no batching, and one database for every city.
[pause: 1.1]

[slide: v-275]
[pause: 0.7]
C: Where's the line? Twenty thousand drivers every fifteen seconds is thirteen hundred updates a second. One database does that easily. Five million every four seconds is a million and a quarter.
V: Below about twenty thousand drivers, a city or two, I'd ship PostGIS and skip locked, and say when I'd switch.
[pause: 1.6]

[pause: 1.4]

## 6 Bridge

[slide: v-276]
[pause: 1.2]
V: It works. The question now is where it breaks first.
[pause: 1.8]

[slide: v-277]
[pause: 1.3]
C: Version three, with the places it breaks.
[reveal: v-278]
[pause: 0.45]
C: The matcher: two riders and one driver, a driver who vanishes after accepting, and the nearest driver across a river. Challenges one, two and five.
[reveal: v-279]
[pause: 0.45]
C: The location index: a driver across a cell boundary, and a shard that dies. Challenges three and four.
[reveal: v-280]
[pause: 0.45]
C: The gateway, where offers and locations both travel, and where challenge six starts: how would we know any of it is wrong?
[pause: 1.1]

[pause: 1.4]

## 7 Challenges

[slide: v-281]
[pause: 1.2]
C: Six challenges, each the same way: question, naive answer, case, break, fix one level down, the push on the fix, and what I'd say.
[pause: 1.8]

[pause: 1.4]

## 7.1 Challenge 1: Two riders, one driver

[slide: v-282]
[pause: 1.2]
N: Challenge one is the crux, and most candidates never reach it on their own.
[pause: 1.8]

[slide: v-283]
[pause: 0.6]
I: Two riders request at the same instant, and the index returns the same nearest driver to both. Walk me through it.
[pause: 2.0]

[slide: v-284]
[pause: 1.3]
C: Inside the matcher.
[reveal: v-285]
[pause: 0.45]
C: The claimer is marked.
[reveal: v-286]
[pause: 0.45]
C: The naive answer: mark the driver busy after sending the offer.
[reveal: v-287]
[pause: 0.45]
C: Then both requests read available before either writes busy. Read, then write, is a race.
[pause: 1.1]

[slide: v-288]
[pause: 1.0]
C: The trace.
[reveal: v-289]
[pause: 0.45]
C: Request seventy-seven's nearest available driver is forty-two.
[reveal: v-290]
[pause: 0.45]
C: Twenty milliseconds later, another matcher instance, request seventy-eight: also forty-two.
[reveal: v-291]
[pause: 0.45]
C: Two offers go to one driver.
[reveal: v-292]
[pause: 0.45]
C: The driver accepts both.
[reveal: v-293]
[pause: 0.45]
C: One rider waits for a car that will never come.
[reveal: v-294]
[pause: 0.45]
C: At two thousand requests a second, the same instant happens every second.
[pause: 1.0]

[slide: v-295]
[pause: 1.3]
C: The fix.
[reveal: v-296]
[pause: 0.45]
C: The claimer.
[reveal: v-297]
[pause: 0.45]
C: And the trip store, which decides.
[reveal: v-298]
[pause: 0.45]
C: One level down. There is one matcher leader per city, holding an etcd lease whose epoch it carries. Each claim is one conditional update: set the driver to offered, if the driver is available, at the version the matcher read, and the matcher's epoch is the city's current one. One row back means claimed. None means someone else won.
[reveal: v-299]
[pause: 0.45]
C: It covers two requests, two matchers and a deposed leader. The loser simply gets its next candidate on the next tick.
[reveal: v-300]
[pause: 0.45]
C: Rejected: Redis set-if-not-exists as the claim. After a fail-over the asynchronous replica may not have it, and the driver is handed out twice.
[pause: 1.1]

[slide: v-301]
[pause: 1.0]
C: The claim in S-Q-L, because here the idiom is the lesson. Lines five and six: the driver must still be available, at the version I read. Line seven: my epoch must be the city's current one. If any of it is false, no row comes back, and I know I lost. No lock was held, and no clock was trusted.
[pause: 1.0]

[slide: v-302]
[pause: 0.6]
I: The PostgreSQL primary fails over in the middle of New Year's Eve.
[pause: 1.5]

[slide: v-303]
[pause: 0.6]
C: The standby is synchronous, in another zone, so every committed claim survives the fail-over.
[reveal: v-304]
[pause: 0.45]
C: For the ten to thirty seconds it takes, claims fail and requests wait in the batch.
[reveal: v-305]
[pause: 0.45]
C: The honest limit: matching in that region stops for seconds. Wrong matches never happen. That's the right way round.
[pause: 0.8]

[slide: v-306]
[pause: 0.7]
V: If asked, I'd say: the index can be stale; the claim can't be wrong. One matcher leads each city under an etcd lease, and a driver is claimed by one conditional update: available, at the version read, with the current epoch. Whoever gets no row back lost, and retries on the next tick.
[pause: 1.0]
N: That fix creates the next question: the driver is claimed. What if they never answer?
[pause: 1.6]

[pause: 1.4]

## 7.2 Challenge 2: The driver who vanishes

[slide: v-307]
[pause: 1.2]
N: Challenge two: the other half of the crux. A claim that is never released is a driver lost from the pool.
[pause: 1.8]

[slide: v-308]
[pause: 0.6]
I: A driver accepts, and their app crashes. What happens to the rider, and to the driver?
[pause: 2.0]

[slide: v-309]
[pause: 1.3]
C: The end of the matcher.
[reveal: v-310]
[pause: 0.45]
C: The offer manager is marked.
[reveal: v-311]
[pause: 0.45]
C: The naive answer: the rider can cancel.
[reveal: v-312]
[pause: 0.45]
C: Then nothing notices the driver is gone. The trip waits forever, and the driver, if the app comes back, is still on a trip that isn't happening.
[pause: 1.1]

[slide: v-313]
[pause: 1.0]
C: The trace.
[reveal: v-314]
[pause: 0.45]
C: Driver forty-two accepts, and trip fifty-five twelve starts.
[reveal: v-315]
[pause: 0.45]
C: Five seconds later the phone crashes in a tunnel.
[reveal: v-316]
[pause: 0.45]
C: The rider watches a car that doesn't move.
[reveal: v-317]
[pause: 0.45]
C: Seven minutes later the rider cancels, and the driver reconnects still marked on a trip.
[reveal: v-318]
[pause: 0.45]
C: Two leaks: a rider waiting for nothing, and a driver lost to matching.
[pause: 1.0]

[slide: v-319]
[pause: 1.3]
C: The fix.
[reveal: v-320]
[pause: 0.45]
C: The offer manager.
[reveal: v-321]
[pause: 0.45]
C: One level down. An offer expires after fifteen seconds if not accepted. An accepted trip holds a thirty-second lease on the driver, renewed by the heartbeats the stream already carries. If the lease lapses, the driver becomes unavailable and the trip goes back to matching, at the front of the queue. And an accept carries the offer I-D, so a retried accept returns the same trip.
[reveal: v-322]
[pause: 0.45]
C: It covers crashes, tunnels, ignored offers and retried accepts. Not a driver who's connected but not moving. That's a product rule on top.
[reveal: v-323]
[pause: 0.45]
C: Rejected: a long fixed offer timeout. It either leaves riders waiting or takes trips from slow but willing drivers. Only a heartbeat lease tells the two apart.
[pause: 1.1]

[slide: v-324]
[pause: 1.3]
C: As a sequence.
[reveal: v-325]
[pause: 0.45]
C: Driver forty-two accepts.
[reveal: v-326]
[pause: 0.45]
C: The app crashes. No more heartbeats.
[reveal: v-327]
[pause: 0.45]
C: The lease on driver forty-two for this trip is thirty seconds, renewed by heartbeats.
[reveal: v-328]
[pause: 0.45]
C: It lapses: the driver becomes unavailable, and the trip returns to matching.
[reveal: v-329]
[pause: 0.45]
C: The rider sees: finding you a new driver, no charge. Thirty seconds lost, not seven minutes.
[pause: 1.1]

[slide: v-330]
[pause: 1.0]
C: Why thirty seconds? Two kinds of error, against each other.
[reveal: v-331]
[pause: 0.45]
C: Ten seconds: a vanished driver costs ten seconds, but most tunnels and lifts are longer, so willing drivers get released all the time.
[reveal: v-332]
[pause: 0.45]
C: Thirty seconds: thirty seconds of waiting, and only long tunnels release a driver, who reconnects and is told.
[reveal: v-333]
[pause: 0.45]
C: Two minutes: almost no false releases, and riders wait two minutes for ghosts.
[reveal: v-334]
[pause: 0.45]
C: Thirty is an initial target. The distribution of gaps between heartbeats tells you where the knee really is, per city.
[pause: 1.0]

[slide: v-335]
[pause: 0.6]
I: The driver's phone comes back after forty seconds and says: I'm on my way.
[pause: 1.5]

[slide: v-336]
[pause: 0.6]
C: The reconnecting app sends its trip and version. The store says the trip was reassigned, at a newer version, and the store wins.
[reveal: v-337]
[pause: 0.45]
C: The app is told, not argued with: trip reassigned, and the driver is back to available. One owner, one version, no split brain.
[pause: 0.8]

[slide: v-338]
[pause: 0.7]
V: If asked, I'd say: every claim is a lease. An offer expires in fifteen seconds; an accepted trip holds a thirty-second lease renewed by heartbeats; and accepts carry the offer I-D. A vanished driver is released in half a minute, and a late phone is told the trip moved on.
[pause: 1.0]
N: That fix creates the next question: the claims are right. Are the candidates?
[pause: 1.6]

[pause: 1.4]

## 7.3 Challenge 3: Boundaries and hot cells

[slide: v-339]
[pause: 1.2]
N: Challenge three: the geo index itself, at its edges and at its densest.
[pause: 1.8]

[slide: v-340]
[pause: 0.6]
I: The nearest driver is fifty metres away, across a cell boundary. And downtown at six, one cell holds three thousand drivers. Does your query cope?
[pause: 2.0]

[slide: v-341]
[pause: 1.3]
C: Inside the location index.
[reveal: v-342]
[pause: 0.45]
C: The query is marked.
[reveal: v-343]
[pause: 0.45]
C: The naive answer: look up the pickup's cell.
[reveal: v-344]
[pause: 0.45]
C: Then a driver fifty metres away in the next cell is invisible, and a downtown cell returns three thousand drivers to rank.
[pause: 1.1]

[slide: v-345]
[pause: 1.0]
C: The trace.
[reveal: v-346]
[pause: 0.45]
C: Seven thirty, a suburb: the pickup is near a cell edge, the cell is empty, and the rider hears no drivers.
[reveal: v-347]
[pause: 0.45]
C: A driver fifty metres away, in the next cell, is idle.
[reveal: v-348]
[pause: 0.45]
C: Six p.m. downtown: the pickup's cell holds three thousand drivers.
[reveal: v-349]
[pause: 0.45]
C: Ranking them all by E-T-A is three thousand routing pairs for one request.
[reveal: v-350]
[pause: 0.45]
C: One cell size fits neither place.
[pause: 1.0]

[slide: v-351]
[pause: 1.3]
C: The fix.
[reveal: v-352]
[pause: 0.45]
C: The query.
[reveal: v-353]
[pause: 0.45]
C: And the cell table.
[reveal: v-354]
[pause: 0.45]
C: One level down. The query reads the pickup's cell and its first ring; if that gives fewer than twenty candidates, the second ring, then the third. Candidates are sorted by straight-line distance and cut at twenty. A cell holding more than three hundred drivers is also indexed at the next finer resolution, and a pickup there reads finer rings: a few hundred drivers, not thousands.
[reveal: v-355]
[pause: 0.45]
C: It covers boundaries and density. Not distance by road. That's challenge five.
[reveal: v-356]
[pause: 0.45]
C: Rejected: geohash prefixes alone. Neighbours across a prefix boundary share no prefix, and the cells distort with latitude.
[pause: 1.1]

[slide: v-357]
[pause: 1.0]
C: As pseudocode. Line one: a crowded pickup uses the finer resolution. Line three: expand ring by ring, each ring only the new cells. Line seven: sort by straight-line distance and keep twenty. Every step is a map lookup; nothing scans a city.
[pause: 1.0]

[slide: v-358]
[pause: 0.6]
I: The stadium lets out: twenty thousand riders in one cell, four hundred drivers.
[pause: 1.5]

[slide: v-359]
[pause: 0.6]
C: Requests in one hot cell join a pickup-zone queue and are served in order.
[reveal: v-360]
[pause: 0.45]
C: Surge pricing and a drivers-needed signal bring supply. That's pricing's lever, not mine.
[reveal: v-361]
[pause: 0.45]
C: The honest limit: no index finds twenty thousand drivers who aren't there. Tell the rider the wait.
[pause: 0.8]

[slide: v-362]
[pause: 0.7]
V: If asked, I'd say: a cell index turns a radius into lookups, but a query must read rings of neighbours, expanding until it has enough candidates, and crowded cells are indexed at a finer resolution. Straight-line distance is only the shortlist. Arrival time decides.
[pause: 1.0]
N: That fix creates the next question: this index lives only in memory. What happens when a shard dies?
[pause: 1.6]

[pause: 1.4]

## 7.4 Challenge 4: A shard dies

[slide: v-363]
[pause: 1.2]
N: Challenge four: failure recovery for state you chose not to make durable.
[pause: 1.8]

[slide: v-364]
[pause: 0.6]
I: The location shard for a big city dies with fifty thousand drivers on it. What breaks, and for how long?
[pause: 2.0]

[slide: v-365]
[pause: 1.3]
C: Inside the location index.
[reveal: v-366]
[pause: 0.45]
C: The driver table is marked.
[reveal: v-367]
[pause: 0.45]
C: The naive answer: replicate the index synchronously, like a database.
[reveal: v-368]
[pause: 0.45]
C: What actually breaks: the driver table is gone, and the city has no drivers until something refills it.
[pause: 1.1]

[slide: v-369]
[pause: 1.0]
C: The trace.
[reveal: v-370]
[pause: 0.45]
C: At six, the shard for city twelve dies, and fifty thousand drivers vanish from the index.
[reveal: v-371]
[pause: 0.45]
C: Half a second later the gateway routes city twelve to a standby shard, empty.
[reveal: v-372]
[pause: 0.45]
C: Four seconds later every online driver has reported once, and the index is full again.
[reveal: v-373]
[pause: 0.45]
C: Then a driver's app flushes a buffered position from thirty seconds ago, after the fresh one.
[reveal: v-374]
[pause: 0.45]
C: What mattered was four seconds of no drivers, and an old position that must not overwrite a new one.
[pause: 1.0]

[slide: v-375]
[pause: 1.3]
C: The fix.
[reveal: v-376]
[pause: 0.45]
C: Ingest.
[reveal: v-377]
[pause: 0.45]
C: One level down. No replicas at all. A standby shard starts empty and fills from the next four seconds of reports, because every online driver reports every four seconds anyway. Ingest keeps an update only if its sequence number is newer than the one it holds, so a buffered old position is dropped. Requests in that city just wait a tick or two.
[reveal: v-378]
[pause: 0.45]
C: It covers shard loss and late, out-of-order updates. Not a gateway outage: drivers reconnect to other pods first, and then refill the index the same way.
[reveal: v-379]
[pause: 0.45]
C: Rejected: replicating the index synchronously. It doubles a million and a quarter writes a second to protect data that's stale in four seconds.
[pause: 1.1]

[slide: v-380]
[pause: 1.0]
C: What replication would cost, to protect four seconds of data.
[reveal: v-381]
[pause: 0.45]
C: A synchronous replica: another million and a quarter writes a second, on the hot path. No.
[reveal: v-382]
[pause: 0.45]
C: An asynchronous replica: the same writes off the path, protecting most of the four seconds. Worth it only for the biggest cities, as a warm standby.
[reveal: v-383]
[pause: 0.45]
C: Refilling from the reports: no extra writes at all, and the data is rebuilt in about four seconds. The default.
[pause: 1.0]

[slide: v-384]
[pause: 1.0]
C: As pseudocode. Line three: an update whose sequence isn't newer is dropped, which handles both the buffered flush and a reordered network path. Lines seven and eight: move the driver between cells and overwrite. There's no write-ahead log, and none is needed.
[pause: 1.0]

[slide: v-385]
[pause: 0.6]
I: Four seconds of no drivers on New Year's Eve is a lot of angry riders.
[pause: 1.5]

[slide: v-386]
[pause: 0.6]
C: The matcher hides the gap: a city whose shard is refilling holds requests for one more tick instead of answering no drivers.
[reveal: v-387]
[pause: 0.45]
C: For the biggest cities, a warm standby subscribes to the same updates, so it's already full when it takes over. That's replication, but only where it's worth it.
[reveal: v-388]
[pause: 0.45]
C: The honest limit: small cities refill cold. Four seconds, now and then, is the price of not replicating everything.
[pause: 0.8]

[slide: v-389]
[pause: 0.7]
V: If asked, I'd say: a location is soft state. It's stale in four seconds, so I don't replicate it. A lost shard refills from the next round of reports, sequence numbers stop old positions overwriting new ones, and only the biggest cities keep a warm standby.
[pause: 1.0]
N: That fix creates the next question: the candidates are found. Is nearest the right one?
[pause: 1.6]

[pause: 1.4]

## 7.5 Challenge 5: Nearest is not closest

[slide: v-390]
[pause: 1.2]
N: Challenge five: distance against time, and one rider against the whole city.
[pause: 1.8]

[slide: v-391]
[pause: 0.6]
I: The nearest driver is two hundred metres away, across a river. And at midnight on New Year's Eve, nearest-first leaves half the riders with long waits. What do you change?
[pause: 2.0]

[slide: v-392]
[pause: 1.3]
C: Inside the matcher.
[reveal: v-393]
[pause: 0.45]
C: Candidates are marked.
[reveal: v-394]
[pause: 0.45]
C: The naive answer: the closest driver, first come, first served.
[reveal: v-395]
[pause: 0.45]
C: That ranks by straight line, one request at a time.
[pause: 1.1]

[slide: v-396]
[pause: 1.0]
C: The trace.
[reveal: v-397]
[pause: 0.45]
C: Rider seventy-seven's nearest driver is two hundred metres away, across the river.
[reveal: v-398]
[pause: 0.45]
C: By road, twelve minutes.
[reveal: v-399]
[pause: 0.45]
C: Three seconds later rider seventy-eight asks. Driver forty-two was three minutes from them by road.
[reveal: v-400]
[pause: 0.45]
C: Seventy-eight gets a driver nine minutes away instead.
[reveal: v-401]
[pause: 0.45]
C: Two errors: distance isn't time, and greedy isn't best for the batch.
[pause: 1.0]

[slide: v-402]
[pause: 1.3]
C: The fix.
[reveal: v-403]
[pause: 0.45]
C: The E-T-A ranker.
[reveal: v-404]
[pause: 0.45]
C: And the assigner.
[reveal: v-405]
[pause: 0.45]
C: One level down. Twenty candidates per request come from distance. Once per tick, one E-T-A matrix call covers every pending request against its candidates, cached per cell pair for thirty seconds. Then one minimum-cost assignment over the whole batch, so rider seventy-eight gets driver forty-two. If routing doesn't answer in three hundred milliseconds, distance times a detour factor stands in.
[reveal: v-406]
[pause: 0.45]
C: It covers rivers, one-way streets and greedy choices. Not traffic that the routing service doesn't know about.
[reveal: v-407]
[pause: 0.45]
C: Rejected: straight-line distance. A river, a one-way street or a highway exit turns two hundred metres into twelve minutes.
[pause: 1.1]

[slide: v-408]
[pause: 1.0]
C: The same case as numbers.
[reveal: v-409]
[pause: 0.45]
C: Greedy by distance: rider seventy-seven takes driver forty-two across the river, twelve minutes; seventy-eight gets a driver nine minutes away. Twenty-one minutes of waiting.
[reveal: v-410]
[pause: 0.45]
C: Greedy by E-T-A happens to fix this pair: six and three. Nine minutes. But it still depends on who asked first.
[reveal: v-411]
[pause: 0.45]
C: The batch solves all pending requests together: here also nine minutes, and as the batch grows to forty requests in a busy tick, it stays near the best total, where greedy drifts. That's what two seconds of waiting buys.
[pause: 1.0]

[slide: v-412]
[pause: 1.0]
C: One tick as pseudocode. Line three: one matrix call for the whole batch, with a timeout and a fallback. Line five: the assignment is solved over every pending request together. Line seven: each assignment still goes through the claim from challenge one, and a lost claim waits for the next tick.
[pause: 1.0]

[slide: v-413]
[pause: 0.6]
I: Routing is down for ten minutes.
[pause: 1.5]

[slide: v-414]
[pause: 0.6]
C: Ranking falls back to straight-line distance times a detour factor measured per city. Matches are a little worse, never wrong: the claim doesn't depend on routing.
[reveal: v-415]
[pause: 0.45]
C: And we say so: matches made on fallback are marked, and the arrival times shown to riders widen.
[pause: 0.8]

[slide: v-416]
[pause: 0.7]
V: If asked, I'd say: distance shortlists; time decides. Twenty candidates per request by distance, one E-T-A matrix per tick cached by cell pair, and a minimum-cost assignment over the whole batch. If routing is slow, distance times a detour factor stands in: worse, never wrong.
[pause: 1.0]
N: That fix creates the last question: how would you know matching got worse?
[pause: 1.6]

[pause: 1.4]

## 7.6 Challenge 6: “No drivers” next to idle drivers

[slide: v-417]
[pause: 1.2]
N: Challenge six is observability, measured where riders feel it.
[pause: 1.8]

[slide: v-418]
[pause: 0.6]
I: Riders in one city are told no drivers available, while drivers there sit idle. How would you have known before Twitter did?
[pause: 2.0]

[slide: v-419]
[pause: 1.3]
C: The ride A-P-I, the matcher, the index, the trip store.
[reveal: v-420]
[pause: 0.45]
C: The matcher is marked.
[reveal: v-421]
[pause: 0.45]
C: The naive answer: request success rate and latency are green.
[reveal: v-422]
[pause: 0.45]
C: They are. The matcher answers quickly and correctly, from a shard that stopped receiving one gateway's updates.
[pause: 1.1]

[slide: v-423]
[pause: 1.0]
C: The trace.
[reveal: v-424]
[pause: 0.45]
C: A gateway deploy breaks forwarding for a tenth of the drivers in city three.
[reveal: v-425]
[pause: 0.45]
C: They expire from the index while still online and idle.
[reveal: v-426]
[pause: 0.45]
C: For fifty minutes, nearby riders hear no drivers, and the success rate is a hundred percent.
[reveal: v-427]
[pause: 0.45]
C: The first complaint arrives on social media.
[reveal: v-428]
[pause: 0.45]
C: No drivers is a successful response.
[pause: 1.0]

[slide: v-429]
[pause: 1.3]
C: The fix changes the design: version four. Version three, carried.
[reveal: v-430]
[pause: 0.45]
C: New: probe riders. In every city, every minute, a fake driver reports a position and a fake rider requests a trip next to it, end to end.
[pause: 1.1]

[slide: v-431]
[pause: 0.6]
C: One level down, four signals.
[reveal: v-432]
[pause: 0.45]
C: Probe trips: a fake driver and rider per city per minute, matched, offered, accepted and released. A failure pages.
[reveal: v-433]
[pause: 0.45]
C: Idle next to no: count no-driver answers where the gateway knows of online, available drivers within two kilometres. That one would have fired at seventeen forty-five.
[reveal: v-434]
[pause: 0.45]
C: The stale share: drivers the gateway sees online but the index doesn't have, per pod. It names the broken pod.
[reveal: v-435]
[pause: 0.45]
C: And time to offer, per city, against five seconds.
[reveal: v-436]
[pause: 0.45]
C: Rejected: the request success rate. It stays green while riders are told no drivers next to idle ones.
[pause: 0.8]

[slide: v-437]
[pause: 1.0]
C: And read them in pairs.
[reveal: v-438]
[pause: 0.45]
C: No drivers up, with idle drivers nearby: an index gap. Our case.
[reveal: v-439]
[pause: 0.45]
C: No drivers up, with no idle drivers: real demand. Surge's problem, not mine.
[reveal: v-440]
[pause: 0.45]
C: Offers expiring, all from one app version: a client bug.
[reveal: v-441]
[pause: 0.45]
C: Claims failing, with a new leader epoch: a leadership change in progress.
[reveal: v-442]
[pause: 0.45]
C: And time to offer up, with slow E-T-A calls: routing, and we're on the fallback.
[pause: 1.0]

[slide: v-443]
[pause: 1.0]
C: And the matching service levels, so health is numbers.
[reveal: v-444]
[pause: 0.45]
C: Probe trips completed: a hundred percent per city. One failure pages.
[reveal: v-445]
[pause: 0.45]
C: Time to offer: ninety-fifth percentile within five seconds, per city.
[reveal: v-446]
[pause: 0.45]
C: No-driver answers with idle drivers nearby: at most a tenth of a percent.
[reveal: v-447]
[pause: 0.45]
C: Online drivers missing from the index: at most half a percent, per gateway pod.
[reveal: v-448]
[pause: 0.45]
C: And double assignments: zero, checked by a nightly audit of driver state, because S-one deserves its own alarm.
[pause: 1.0]

[slide: v-449]
[pause: 0.7]
V: If asked, I'd say: I'd measure what riders feel. Probe trips in every city every minute, no-driver answers next to idle drivers, online drivers missing from the index, and time to offer per city. No drivers is a successful response, so success rates can't see this.
[pause: 1.6]

[pause: 1.4]

## 8 Recap

[slide: v-450]
[pause: 1.2]
C: The recap: one picture, the mechanisms, and the mistakes that cost most.
[pause: 1.8]

[slide: v-451]
[pause: 1.3]
C: Version four, the final design.
[reveal: v-452]
[pause: 0.45]
C: The location index: cells as keys, and soft state.
[reveal: v-453]
[pause: 0.45]
C: The matcher: conditional, fenced claims, and batched assignment.
[reveal: v-454]
[pause: 0.45]
C: The trip store, where the claim is one conditional update.
[reveal: v-455]
[pause: 0.45]
C: The gateway, carrying the heartbeats that renew the leases.
[reveal: v-456]
[pause: 0.45]
C: And the probes, measuring what riders feel.
[pause: 1.1]

[slide: v-457]
[pause: 0.6]
C: One sentence per path.
[reveal: v-458]
[pause: 0.45]
C: Report: a location rides an open stream into a city's in-memory cells. Latest wins, and silence expires.
[reveal: v-459]
[pause: 0.45]
C: Match: every two seconds the city's one matcher shortlists by distance, ranks by E-T-A, and assigns the whole batch.
[reveal: v-460]
[pause: 0.45]
C: Accept: a conditional, fenced write claims the driver, the offer expires if ignored, and the accept is idempotent.
[reveal: v-461]
[pause: 0.45]
C: Track: the assigned driver's stream is forwarded to the rider. Nothing on that path reads a database.
[pause: 0.8]

[slide: v-462]
[pause: 1.0]
N: The mistakes that cost most.
[reveal: v-463]
[pause: 0.45]
N: Every location written to a database. Instead, memory, overwrite-only.
[reveal: v-464]
[pause: 0.45]
N: Nearest wins with no claim. Instead, one conditional, fenced write.
[reveal: v-465]
[pause: 0.45]
N: An offer that never expires. Instead, timeouts and heartbeat leases.
[reveal: v-466]
[pause: 0.45]
N: One cell with no neighbours. Instead, expanding rings and finer cells where it's crowded.
[reveal: v-467]
[pause: 0.45]
N: Straight-line nearest, first come first served. Instead, E-T-A on a shortlist, and a batch.
[reveal: v-468]
[pause: 0.45]
N: And watching success rates. Instead, probe trips and idle drivers next to no-driver answers.
[pause: 1.0]

[slide: v-469]
[pause: 0.7]
V: Keep where drivers are fast and forgettable. Keep who gets which driver exact and fenced. And make every claim a lease that expires.
[pause: 1.0]
C: Thanks for watching. The written design is linked below.
[pause: 1.6]
