from dsl import *
P = "[+]"

# ───────────────────────── 0 · cold open ─────────────────────────
chapter(0, "Cold open", -1, "Match riders to nearby drivers", [
 "C: Nearby drivers sounds like a geometry question: put drivers on a map, find the closest one. It is asked at every ride-hailing and delivery company, and at Google, because the geometry is the easy half. The hard half is that two riders can be handed the same driver in the same second."])

qs("Interviewer · the prompt", "“Design the system that matches riders to nearby drivers. Drivers move constantly; a rider expects a match in seconds.”", [
 "I: Design the system that matches riders to nearby drivers. Drivers move constantly, and a rider expects a match in seconds.", "[pause: 1.5]"])

S(dia("Why it is harder than it looks", "Two problems that look like one", "tension", chip=chips("fast and lossy", "exact and contended", "kept apart")), [
 "C: Here is the hook. There are two problems here, and the weak answer treats them as one.",
 "C: A geo problem: a million location writes a second, and a lookup by area in milliseconds. That can be fast and even lossy. And a contention problem: two riders, one driver, the same second. That must be exact. The design keeps them in different stores with different guarantees."])

S(plain("Before the design", "What this question grades", table(["Axis", "Weak signal", "Strong signal"], [
  ["<b>Requirements</b>", "“Find the nearest driver”", "Asks what must never happen: one driver, two riders"],
  ["<b>Estimates</b>", "No write rate", "1.25 M writes a second, and what that rules out"],
  ["<b>Correctness</b>", "Nearest wins, no claim", "A conditional claim, fencing, an offer state machine"],
  ["<b>Depth</b>", "“Use a geohash”", "Cells as 1-D keys, neighbours, hot cells, expiry"],
  ["<b>Operations</b>", "Request success rate", "Probe trips; idle drivers next to “no drivers” answers"]], "bt xs sig") +
  grade("The geo index may be stale. The claim may never be wrong.")), [
 "N: Five axes.", P,
 "N: Requirements: the strong answer asks what must never happen, and the answer is one driver, two riders.", P,
 "N: Estimates: the write rate, and what it rules out.", P,
 "N: Correctness: not nearest-wins, but a conditional claim, fencing and an offer state machine.", P,
 "N: Depth: cells as one-dimensional keys, neighbours, hot cells and expiry, not just the word geohash.", P,
 "N: Operations: probe trips, and idle drivers sitting next to riders who were told there are none.", P,
 "C: And the rule for the round: the geo index may be stale; the claim may never be wrong."])

key("The thesis", "Keep <em>where drivers are</em> as fast, overwrite-only, lossy memory, and <em>who gets which driver</em> as one exact conditional write, owned by <em>one matcher per city</em>.", [
 "V: Keep where drivers are as fast, overwrite-only, lossy memory. And keep who gets which driver as one exact conditional write, owned by one matcher per city.", "[pause: 1.0]"])

S(plain("The order I will follow", "Scope, numbers, theory, a simple design, then I break it",
  '<div class="ribbon" style="margin-top:6pt">' + "".join(f"<span>{x}</span>" for x in STAGES) + '</div>' +
  cards(("", "First", "Requirements, the write rate and the density, and the theory: cells, soft state, claims, leases, batches."),
        ("grn", "Then", "The API and the data, three versions on one picture, every path as a sequence, the components one level down."),
        ("red", "Most of the time", "Six challenges that break it, each fixed one level down."), cols=3)), [
 "C: The order I'll follow.", P,
 "C: First, the requirements, the write rate and the density, and the theory: cells as keys, soft state, claims, leases and batches.", P,
 "C: Then the A-P-I and the data, three versions on one picture, every path as a sequence, and the two important containers opened up with their technologies.", P,
 "C: Then most of the time on six challenges, each fixed one level down, and each fix creating the next question."])

# ───────────────────────── 1 · requirements ─────────────────────────
chapter(1, "Requirements and scope", 0, "The scale first, then five questions", ["C: The scale first, then five questions."])

S(plain("Requirements · the scale line", "Three numbers every estimate starts from", '<div class="tiles" style="--n:3">'
  '<div class="tile blue"><b>900 M</b><span>trips a month, 30 M a day</span></div>'
  '<div class="tile"><b>5 M</b><span>drivers online at peak, a location every 4 s</span></div>'
  '<div class="tile red"><b>× 10</b><span>one city at midnight on New Year’s Eve</span></div></div>' +
  line("Every number later starts from one of these three.", "a")), [
 "C: The scale.", P, "C: Nine hundred million trips a month, thirty million a day.", P,
 "C: Five million drivers online at peak, each sending a location every four seconds.", P,
 "C: And the peak: one city at midnight on New Year's Eve, ten times its usual requests for ten minutes, with three thousand drivers inside two kilometres downtown.", P,
 "C: Every number later starts from these."])

def clar(n, q, a, ask, ans, so):
    S(f'<div class="who">Clarifying question {n} of 5</div><div class="qq">{q}</div><div class="ans">{a}</div>',
      ["C: " + ask, P, "I: " + ans, "C: " + so], cls="qs")

clar(1, "What must never happen?", "A driver must never be assigned to two riders.",
     "What must never happen?", "A driver must never be assigned to two riders.",
     "That's the safety property, and it isn't a geo property. It needs a claim.")
clar(2, "How fast?", "An offer on a driver's phone within 5 seconds of the request.",
     "How fast must a match be?", "An offer on a driver's phone within five seconds of the request.",
     "Five seconds leaves room to wait a moment and match a batch, which can beat first come, first served.")
clar(3, "Nearest by distance, or by time?", "Nearest is fine for version one; by ETA is better.",
     "Nearest by distance, or by arrival time?", "Nearest is fine for version one. By E-T-A is better.",
     "Then distance shortlists and E-T-A ranks. Challenge five.")
clar(4, "Across cities?", "No. Cities are independent.",
     "Do we ever match across cities?", "No. Cities are independent.",
     "That's the biggest simplification on the board: a city is a unit of sharding, of failure and of ownership.")
clar(5, "What else is in scope?", "Matching and tracking the car. Not pricing, payment or routing.",
     "What else is in scope?", "Matching, and showing the rider the approaching car. Not pricing, payment or routing.",
     "Routing is a dependency I call for travel times, not something I build.")

S(plain("Requirements · functional", "Four things the system must do", cards(
  ("", "FR1 · Report", "Accept a location from every online driver every 4 seconds."),
  ("grn", "FR2 · Match", "Turn a request into an offer to one driver, nearby by time, within 5 seconds."),
  ("amb", "FR3 · Accept", "A driver accepts or declines; an accepted offer becomes a trip, exactly once."),
  ("red", "FR4 · Track", "The rider sees the assigned car approach, updated every few seconds."))), [
 "C: Four functional requirements.", P, "C: One, report: a location from every online driver every four seconds.", P,
 "C: Two, match: a request becomes an offer to one nearby driver within five seconds.", P,
 "C: Three, accept: an accepted offer becomes a trip, exactly once.", P,
 "C: Four, track: the rider sees the car approach."])

S(plain("Requirements · non-functional", "The numbers, and what each is for", '<p class="chips">all initial targets</p><div class="tiles" style="--n:4">'
  '<div class="tile red"><b>0</b><span>drivers on two trips</span></div>'
  '<div class="tile blue"><b>5 s</b><span>request to offer, p95</span></div>'
  '<div class="tile"><b>8 s</b><span>oldest location used</span></div>'
  '<div class="tile blue"><b>99.95 %</b><span>matching availability per city</span></div></div>' +
  line("A city’s outage must not touch another city.", "a")), [
 "C: The numbers.", P, "C: Zero drivers on two trips.", P, "C: Five seconds from request to offer.", P,
 "C: No location older than eight seconds used for a match.", P, "C: Three and a half nines per city.", P,
 "C: And a city's outage must not touch another city."])

S(plain("Requirements · scope", "In, and out on purpose", cards(
  ("grn", "In scope", "Location intake, the nearby index, matching, claims, offers, the trip until pickup, tracking the car."),
  ("red", "Out, on purpose", "Pricing and surge, payment, routing and ETA models, fraud, driver onboarding, pooled rides.")) +
  line("Pooled rides would change the claim from one-or-zero to capacity: I’d say so, and leave it.", "")), [
 P, "C: In scope: location intake, the nearby index, matching, claims and offers, the trip until pickup, and tracking the car.", P,
 "C: Out, on purpose: pricing and surge, payment, routing and its models, fraud, onboarding, and pooled rides.", P,
 "C: Pooled rides I'd mention aloud: they change a claim from one-or-zero to capacity. The same conditional write works with a seat count instead of a state, but it's a different product."])

S(dia("Architecture · C4 level 1 · context", "The system in its context", "c4-context",
      cap="Figure 1.1 — C4 system context: riders, drivers, routing, and the trip lifecycle around matching"), [
 "C: The context.", P, "C: Riders request rides and watch the car arrive.", P, "C: The matching system, one box.", P,
 "C: Drivers report locations and accept offers on a stream.", P, "C: Routing gives travel times.", P,
 "C: And the trip lifecycle, with pricing and payment, hears when a trip starts. Out of scope."], cls="dia")

key("The core", "The core is three things: a <em>lossy, fast location index</em>, an <em>exact claim</em>, and an <em>offer that expires</em>.", [
 "V: The core is three things. A lossy, fast location index. An exact claim. And an offer that expires.", "[pause: 0.8]"])

# ───────────────────────── 2 · estimates ─────────────────────────
chapter(2, "Estimates", 1, "Each number from the scale line, with what it decides", [
 "C: Numbers next, from the scale line, each ending in a decision. Illustrative."])

S(plain("Estimates · locations", "1.25 million writes a second, each stale in four", table(["Number", "From", "Arithmetic", "Decides"], [
  ["Writes", "5 M drivers", "5 M ÷ 4 s = <b>1.25 M/s</b>; × 100 B = 125 MB/s", "Memory, overwrite-only"],
  ["If durable", "the rate", "1.25 M × 86,400 ≈ 1.1 × 10¹¹ rows ≈ <b>11 TB a day</b>", "Not a database"],
  ["Memory", "5 M drivers", "5 M × 200 B ≈ <b>1 GB</b>", "Shards for isolation, not capacity"],
  ["Gateway", "5 M drivers", "5 M streams ÷ 50,000 per pod = <b>100 pods</b>", "Persistent streams"]])), [
 "C: Locations.", P,
 "C: Five million drivers every four seconds is one point two five million writes a second, a hundred and twenty-five megabytes a second.", P,
 "C: Written durably, that's a hundred and ten billion rows, eleven terabytes, a day, of data that's stale in four seconds. Not a database.", P,
 "C: In memory, all five million drivers are about a gigabyte. One machine could hold them. So I shard by city for isolation, not for capacity.", P,
 "C: And five million streams at fifty thousand per pod is a hundred gateway pods."])

S(plain("Estimates · density", "Downtown at six: how many drivers per cell?", table(["Number", "From", "Arithmetic", "Decides"], [
  ["Downtown", "the peak", "3,000 drivers in a 2 km radius ≈ 12.6 km²", "Hundreds per cell"],
  ["Per res-8 cell", "0.74 km²", "3,000 ÷ 17 cells ≈ <b>180</b>; the busiest > 300", "Split hot cells to res 9 (0.1 km²)"],
  ["Suburb", "a quiet hour", "≈ 0.5 drivers per cell", "Expand the ring until 20 candidates"],
  ["Ranking all", "downtown", "3,000 ETA pairs per request", "Shortlist 20 by distance first"]])), [
 "C: Density, because averages hide it.", P,
 "C: Downtown at six, three thousand drivers within two kilometres, about twelve and a half square kilometres.", P,
 "C: A resolution-eight cell is point seven four square kilometres, so about a hundred and eighty drivers a cell on average, and the busiest over three hundred. Those get split to resolution nine, a tenth of a square kilometre.", P,
 "C: In a suburb at a quiet hour, half a driver per cell. One ring isn't enough; the query expands until it has twenty.", P,
 "C: And ranking every downtown driver by E-T-A would be three thousand routing pairs per request. So distance shortlists twenty first."])

S(plain("Estimates · matching", "Matching is small; it is contention, not throughput", table(["Number", "From", "Arithmetic", "Decides"], [
  ["Requests", "900 M trips", "9 × 10⁸ ÷ 2.6 × 10⁶ s ≈ 350 trips/s; × 2 requests; × 3 peak ≈ <b>2,100/s</b>", "A regional database takes the claims"],
  ["One city, NYE", "the peak", "10 % of peak × 10 ≈ <b>2,100/s</b> for ten minutes", "One matcher per city still copes"],
  ["Search area", "2 km", "k = 2 ring of H3 res 8: 19 cells ≈ 14 km²", "19 lookups, not a scan"],
  ["ETA pairs", "requests", "2,100/s × 20 candidates = <b>42,000/s</b>", "Shortlist, batch, cache by cell pair"]])), [
 "C: Matching.", P,
 "C: Nine hundred million trips a month is about three hundred and fifty a second. Double it for cancellations and retries, triple it for the peak hour: about two thousand one hundred requests a second. A regional database takes that many conditional writes.", P,
 "C: The biggest city on New Year's Eve: ten percent of the peak, times ten, for ten minutes. The same order, in one city: one matcher still copes.", P,
 "C: A two-kilometre search is two rings of H3 resolution-eight cells: nineteen cells, about fourteen square kilometres. Nineteen lookups.", P,
 "C: And twenty candidates each for E-T-A is forty-two thousand pairs a second: shortlist, batch, and cache by cell pair."])

S(dia("Estimates · the latency budget", "Five seconds, from a request to an offer", "budget", chip=chips("initial target", "p95")), [
 "C: The budget. Up to two seconds waiting for the batch tick. About seven tenths of a second for the index, the E-T-A matrix and the claim. Half a second to push the offer down the driver's stream. About three seconds of five.",
 "C: The spare is for a slow E-T-A call, which gets a timeout and a fallback, not more waiting."], cls="dia")

# ───────────────────────── 3 · theory ─────────────────────────
chapter(3, "Theory", 2, "Proximity, soft state and claims", [
 "C: The theory: what makes this hard, in terms that outlive product names. Five mechanisms, the options, what will go wrong."])

S(plain("Theory · what it is", "A fast proximity index next to an exact assignment", cards(
  ("", "It is", "Assigning scarce, moving resources to requests, exactly once, from an approximate picture of where they are."),
  ("amb", "Not a map search", "“Restaurants near me” never runs out; a driver can be given away only once."),
  ("amb", "Not routing", "Routing says how long; matching says who. Matching calls routing."),
  ("amb", "Not fleet telemetry", "Telemetry keeps history; matching needs only the latest four seconds."), cols=2)), [
 "C: What it is, and what it is not.", P,
 "V: Assigning scarce, moving resources to requests, exactly once, from an approximate picture of where they are.", P,
 "C: Not a map search: restaurants near me never run out; a driver can be given away only once.", P,
 "C: Not routing: routing says how long; matching says who.", P,
 "C: And not fleet telemetry, which keeps history. Matching needs the latest four seconds. That's question ninety-seven."])

S(plain("Theory · properties", "Safety and liveness, stated separately", cards(
  ("red", "S1 · one trip per driver", "A driver is never assigned to two trips at once."),
  ("red", "S2 · one trip per accept", "An accepted offer becomes exactly one trip; a retry changes nothing."),
  ("grn", "L1 · an answer", "Every request gets an offer, or “no drivers”, within 5 seconds."),
  ("grn", "L2 · released", "A driver who does not respond, or vanishes, is released within seconds."), cols=2)), [
 "C: Safety first.", P, "V: S-one: a driver is never assigned to two trips at once.", P,
 "V: S-two: an accepted offer becomes exactly one trip. A retry changes nothing.", P,
 "C: Liveness. L-one: every request gets an offer or a clear no within five seconds.", P,
 "C: L-two: a driver who doesn't respond, or vanishes, is released within seconds. Otherwise drivers leak out of the pool."])

def mech(n, name, prot, how, rules, cost, say):
    S(plain(f"Theory · mechanism M{n}", name, cards(("", "Protects", prot), ("grn", "How it works", how), ("red", "Rules out", rules), ("amb", "Costs", cost), cols=2)), say)

mech(1, "Cells as keys: a 2-D query as lookups", "L1.", "Map every point to a hexagonal H3 cell ID; a radius query is the cell and its rings of neighbours.",
     "Computing distance to every driver; missing a driver across a boundary.", "A cell size to choose; extra cells read at the edges.", [
 "C: Mechanism one: cells as keys.", P, "C: It protects L-one.", P,
 "C: Every point maps to a hexagonal cell with a sixty-four-bit I-D. A radius query becomes the pickup's cell plus its rings of neighbours: a handful of map lookups.", P,
 "C: It rules out computing distance to every driver, and, because the ring includes neighbours, missing a driver just across a boundary.", P,
 "C: It costs a cell size to choose, and some extra cells read at the edges."])

S(dia("Theory · mechanism M1, drawn", "The pickup's cell and two rings: 19 lookups", "kring"), [
 "C: Drawn: the pickup's cell in the middle, six neighbours in the first ring, twelve in the second. Nineteen cells, about fourteen square kilometres.",
 "C: The green driver is fifty metres away but in the next cell. A query of the pickup's cell alone would miss them; the ring doesn't. And each cell is a sixty-four-bit integer, so the whole query is nineteen hash-map lookups."], cls="dia")

mech(2, "Soft state: overwrite, sequence, expire", "L1, freshness.", "Keep only the latest location; drop an update with an older sequence number; expire a driver silent for 12 s.",
     "Writing 1.25 M durable rows a second; an old buffered fix overwriting a new one.", "A lost shard is empty until drivers report again: about 4 s.", [
 "C: Mechanism two: soft state.", P, "C: It protects freshness, and so L-one.", P,
 "C: Keep only the latest location. Drop an update whose sequence number is older than the one held. Forget a driver who has been silent for twelve seconds.", P,
 "C: It rules out writing a million durable rows a second, and an old, buffered position overwriting a new one.", P,
 "C: It costs this: a lost shard is empty until drivers report again. About four seconds."])

mech(3, "A conditional claim, fenced", "S1.", "Claim a driver with one write that succeeds only if the driver is still available at the version read, and the writer's epoch is current.",
     "Two riders given one driver; a deposed matcher still claiming.", "A retry for the loser; a small, consistent store.", [
 "C: Mechanism three, the crux: a conditional claim, fenced.", P, "C: It protects S-one.", P,
 "C: A driver is claimed by one write that succeeds only if the driver is still available, at the version the matcher read, and the matcher's epoch is the city's current one.", P,
 "C: It rules out two riders getting one driver, and a matcher that lost its leadership still claiming.", P,
 "C: It costs a retry for whoever loses, and a small, strongly consistent store."])

mech(4, "Leases and timeouts", "L2, S2.", "An offer expires in 15 s; an assigned driver holds a 30 s lease renewed by heartbeats; accepts carry the offer ID.",
     "Drivers stuck as “offered” forever; a double accept creating two trips.", "Choosing the timeouts; the occasional false release.", [
 "C: Mechanism four: leases and timeouts.", P, "C: They protect L-two and S-two.", P,
 "C: An offer expires in fifteen seconds. A driver on a trip holds a thirty-second lease, renewed by heartbeats. An accept carries the offer I-D, so a retried accept is the same accept.", P,
 "C: It rules out drivers stuck as offered forever, and a double accept creating two trips.", P,
 "C: It costs choosing timeouts, and the occasional false release of a slow driver."])

mech(5, "Batched assignment", "L1, efficiency.", "Every 2 s, take all pending requests in a city and solve a small min-cost assignment on ETA.",
     "Greedy first-come choices that leave later riders a long way away.", "Up to 2 s of waiting; a solver.", [
 "C: Mechanism five: batched assignment.", P, "C: It protects L-one, and efficiency.", P,
 "C: Every two seconds, take all pending requests in a city and solve a small minimum-cost assignment over their candidates' E-T-As.", P,
 "C: It rules out greedy first-come choices that grab the driver a later rider needed more.", P,
 "C: It costs up to two seconds of waiting, and a solver."])

S(plain("Theory · cell systems", "Four ways to cut the map, and what each costs", table(["System", "Cell shape", "Neighbours", "Watch out for"], [
  ["Geohash", "rectangles, 32-way prefix", "8, by adjacency rules", "neighbours across a prefix edge share no prefix; distorts with latitude"],
  ["Quadtree", "squares, split when full", "by walking the tree", "a moving point re-balances the tree; hard to shard"],
  ["S2", "quads on a cube, Hilbert order", "by cell ID arithmetic", "cell area varies ~2×; neighbours not equidistant"],
  ("pick", ["<b>H3</b>", "hexagons, 16 resolutions", "6, all equidistant", "not perfectly nested: a child can straddle a parent edge"])], "bt xs mx")), [
 "C: Before the options for matching, the options for cutting the map. Four common ones.", P,
 "C: Geohash: rectangles named by a prefix. Simple, but two neighbours across a prefix edge share no prefix, and the cells distort away from the equator.", P,
 "C: A quadtree: squares that split when they fill. It adapts to density, but a moving point keeps rebalancing it, and it's hard to shard.", P,
 "C: S-two: quads on a cube in Hilbert order, so nearby cells have nearby I-Ds. Strong, but cell areas vary by about two times.", P,
 "C: H-three, which I pick: hexagons, where all six neighbours are the same distance away, so a ring really is a ring. The cost: hexagons don't nest perfectly, so a child cell can straddle its parent's edge. For finding nearby drivers, that doesn't matter."])

S(plain("Theory · the options", "Five ways to build it, one picked", table(["Approach", "Never double-assigns", "Fast at scale", "Fails when"], [
  ["A · drivers in a database, distance per request", "with locks", "no", "1.25 M writes a second; a full scan per request"],
  ["B · a geo index, nearest wins, no claim", "no", "yes", "two riders in one second share a driver"],
  ["C · a geo index and a lock per driver", "yes", "partly", "a lock service on the hot path; lock expiry is ambiguous"],
  ["D · global optimal matching", "yes", "no", "cities are independent: one solver for all is pointless"],
  ("pick", ["<b>E · a geo index, one matcher per city, conditional claims, batches</b>", "yes", "yes", "up to 2 s of waiting; one leader per city"])], "bt xs mx") +
  line("Lossy where it is cheap, exact where it matters, and one writer per city.", "a")), [
 "C: Five ways.", P, "C: A, drivers in a database: a million writes a second and a scan per request.", P,
 "C: B, a geo index with nearest-wins and no claim: fast, and wrong the first time two riders share a driver.", P,
 "C: C, a lock per driver: correct, but a lock service sits on the hot path, and its expiry is ambiguous.", P,
 "C: D, one global optimiser: cities are independent, so it buys nothing.", P,
 "C: E, which I pick: a geo index, one matcher per city, conditional claims, and batches.", P,
 "V: Lossy where it's cheap, exact where it matters, and one writer per city.", "[pause: 0.8]"])

S(dia("Theory · mechanism M3 at work", "Two matchers, one driver, one winner", "seq-th-claim"), [
 "C: Mechanism three at protocol level. A matcher with epoch seven, and an old leader that hasn't noticed it lost, epoch six.", P,
 "C: The new leader claims driver forty-two: if available, at version eighteen, with epoch at least seven.", P,
 "C: The old leader sends the same claim, with epoch six.", P, "C: The first one wins: version nineteen, offered to rider seventy-seven.", P,
 "C: The second finds version nineteen and a city epoch of seven. Zero rows.", P,
 "C: The deposed leader learns it lost from the database, not from a clock."], cls="dia")

S(plain("Theory · the failure catalogue", "What will go wrong, in the order I'll take it", table(["#", "Failure", "At risk"], [
  ["1", "Two riders, one driver, the same second", "S1"],
  ["2", "A driver accepts, then vanishes", "S2, L2"],
  ["3", "A driver across a cell boundary; 3,000 drivers in one cell", "L1"],
  ["4", "A location shard dies with 50,000 drivers", "L1"],
  ["5", "The nearest driver is across a river", "efficiency"],
  ["6", "Riders told “no drivers” while drivers sit idle", "all"]], "bt sm")), [
 "C: The failure catalogue.", P, "C: One: two riders, one driver, the same second.", P, "C: Two: a driver accepts, then vanishes.", P,
 "C: Three: a driver across a cell boundary, and three thousand drivers in one cell.", P, "C: Four: a location shard dies.", P,
 "C: Five: the nearest driver is across a river.", P, "C: Six: riders hear no drivers while drivers sit idle."])
