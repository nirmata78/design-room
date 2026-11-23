from dsl import *
from stack import REJ
P = "[+]"
B = lambda x: f'<span class="bad">{x}</span>'
K = lambda n, t: f"Challenge {n} of 6 · {t}"

chapter(6, "Bridge", 5, "It works. Where does it break first?", ["V: It works. The question now is where it breaks first.", "[pause: 1.0]"])

S(dia("Challenge map", "Six challenges, three places on the same picture", "map", chip=chips("each fix creates the next question")), [
 P, "C: Version three, with the places it breaks.", P,
 "C: The matcher: two riders and one driver, a driver who vanishes after accepting, and the nearest driver across a river. Challenges one, two and five.", P,
 "C: The location index: a driver across a cell boundary, and a shard that dies. Challenges three and four.", P,
 "C: The gateway, where offers and locations both travel, and where challenge six starts: how would we know any of it is wrong?"], cls="dia")

chapter(7, "Challenges", 5, "Six ways to break it, and what survives", [
 "C: Six challenges, each the same way: question, naive answer, case, break, fix one level down, the push on the fix, and what I'd say."])

# ── 1
subchapter("7.1", "Challenge 1: Two riders, one driver", ["N: Challenge one is the crux, and most candidates never reach it on their own."])
qs("Interviewer · challenge 1 of 6", "“Two riders request at the same instant, and the index returns the same nearest driver to both. Walk me through it.”", [
 "I: Two riders request at the same instant, and the index returns the same nearest driver to both. Walk me through it.", "[pause: 2.0]"])
S(dia(K(1, "one driver"), "Who decides the driver is taken?", "ch1-attack", q=True, red=True,
      extra=strip(("case", "Naive answer", "“Mark the driver busy after we send the offer.”"),
                  ("case", "Break", "The claimer reads “available”, then writes: both requests read before either writes."))), [
 P, "C: Inside the matcher.", P, "C: The claimer is marked.", P, "C: The naive answer: mark the driver busy after sending the offer.", P,
 "C: Then both requests read available before either writes busy. Read, then write, is a race."], cls="dia")
S(trace(K(1, "the trace"), "Two offers, one car", [
  ("18:00:00.100", "request r77: nearest available is d42"),
  ("18:00:00.120", "request r78 (another matcher instance): nearest available is d42"),
  ("18:00:00.300", "offer to d42 for r77; offer to d42 for r78"),
  ("18:00:04", B("d42 accepts both; two riders wait for one car")),
  ("18:00:09", B("one rider cancels angry; the other gets a car that was already full"))],
  hedge=("At scale", "At 2,100 requests a second in one city on New Year’s Eve, “the same instant” happens every second.")), [
 "C: The trace.", P, "C: Request seventy-seven's nearest available driver is forty-two.", P,
 "C: Twenty milliseconds later, another matcher instance, request seventy-eight: also forty-two.", P,
 "C: Two offers go to one driver.", P, "C: The driver accepts both.", P, "C: One rider waits for a car that will never come.", P,
 "C: At two thousand requests a second, the same instant happens every second."])
S(dia(K(1, "the fix"), "One conditional write decides; one writer per city", "ch1-fix",
      extra=strip(("fixb", "Mechanism", "One matcher leader per city (etcd lease, epoch). Each claim is one conditional UPDATE: available, at the version read, with a current epoch. One row back: claimed."),
                  ("whyb", "Covers, and does not", "Two requests, two matchers, a deposed leader. Not a slow decision: the loser retries on the next tick.")) + rejl(*REJ(1))), [
 P, "C: The fix.", P, "C: The claimer.", P, "C: And the trip store, which decides.", P,
 "C: One level down. There is one matcher leader per city, holding an etcd lease whose epoch it carries. Each claim is one conditional update: set the driver to offered, if the driver is available, at the version the matcher read, and the matcher's epoch is the city's current one. One row back means claimed. None means someone else won.", P,
 "C: It covers two requests, two matchers and a deposed leader. The loser simply gets its next candidate on the next tick.", P,
 "C: Rejected: Redis set-if-not-exists as the claim. After a fail-over the asynchronous replica may not have it, and the driver is handed out twice."], cls="dia")
S(plain(K(1, "the claim, in SQL"), "The whole safety property is one WHERE clause",
  code("UPDATE driver_state\n   SET state = 'offered', trip_id = $2,\n       version = version + 1\n WHERE driver_id = $1\n   AND state = 'available'\n   AND version = $3\n   AND $4 >= (SELECT epoch FROM city_lease\n              WHERE city = driver_state.city)\nRETURNING version;", "sql", hl=(5, 6, 7))), [
 "C: The claim in S-Q-L, because here the idiom is the lesson. Lines five and six: the driver must still be available, at the version I read. Line seven: my epoch must be the city's current one. If any of it is false, no row comes back, and I know I lost. No lock was held, and no clock was trusted."])
qs("Interviewer · the second-level push", "“The PostgreSQL primary fails over in the middle of New Year’s Eve.”", [
 "I: The PostgreSQL primary fails over in the middle of New Year's Eve.", "[pause: 1.5]"])
S(plain(K(1, "the second fix, and the honest limit"), "Synchronous standby; claims pause, never duplicate", cards(
  ("grn", "No lost claim", "A synchronous standby in another zone has every committed claim; the fail-over cannot forget one."),
  ("amb", "Claims pause", "For the 10–30 s of fail-over, claims fail; requests wait in the batch and retry."),
  ("red", "Honest limit", "Matching in that region stops for seconds. Wrong matches never happen. That is the right way round."), cols=3)), [
 P, "C: The standby is synchronous, in another zone, so every committed claim survives the fail-over.", P,
 "C: For the ten to thirty seconds it takes, claims fail and requests wait in the batch.", P,
 "C: The honest limit: matching in that region stops for seconds. Wrong matches never happen. That's the right way round."])
say_slide("“The index can be stale; the claim can't be wrong. One matcher leads each city under an etcd lease, and a driver is claimed by one conditional update: available, at the version read, with the current epoch. Whoever gets no row back lost, and retries on the next tick.”", [
 "V: If asked, I'd say: the index can be stale; the claim can't be wrong. One matcher leads each city under an etcd lease, and a driver is claimed by one conditional update: available, at the version read, with the current epoch. Whoever gets no row back lost, and retries on the next tick.", "[pause: 1.0]",
 "N: That fix creates the next question: the driver is claimed. What if they never answer?"])

# ── 2
subchapter("7.2", "Challenge 2: The driver who vanishes", ["N: Challenge two: the other half of the crux. A claim that is never released is a driver lost from the pool."])
qs("Interviewer · challenge 2 of 6", "“A driver accepts, and their app crashes. What happens to the rider, and to the driver?”", [
 "I: A driver accepts, and their app crashes. What happens to the rider, and to the driver?", "[pause: 2.0]"])
S(dia(K(2, "a silent driver"), "Who notices the driver is gone?", "ch2-attack", q=True, red=True,
      extra=strip(("case", "Naive answer", "“The rider can cancel.”"),
                  ("case", "Break", "The offer manager has no timer after an accept: the trip waits forever."))), [
 P, "C: The end of the matcher.", P, "C: The offer manager is marked.", P, "C: The naive answer: the rider can cancel.", P,
 "C: Then nothing notices the driver is gone. The trip waits forever, and the driver, if the app comes back, is still on a trip that isn't happening."], cls="dia")
S(trace(K(2, "the trace"), "A trip nobody is driving", [
  ("18:02:00", "d42 accepts offer o-901; trip t-5512 starts"),
  ("18:02:05", "d42's phone crashes in a tunnel"),
  ("18:02:05 – 18:09", B("the rider watches a car that does not move")),
  ("18:09", B("the rider cancels; d42 reconnects still marked on a trip"))],
  hedge=("Two leaks", "A rider waiting seven minutes for nothing, and a driver lost to matching until someone fixes the row.")), [
 "C: The trace.", P, "C: Driver forty-two accepts, and trip fifty-five twelve starts.", P,
 "C: Five seconds later the phone crashes in a tunnel.", P, "C: The rider watches a car that doesn't move.", P,
 "C: Seven minutes later the rider cancels, and the driver reconnects still marked on a trip.", P,
 "C: Two leaks: a rider waiting for nothing, and a driver lost to matching."])
S(dia(K(2, "the fix"), "Every claim is a lease, renewed by heartbeats", "ch2-fix",
      extra=strip(("fixb", "Mechanism", "An offer expires after 15 s; an accepted trip holds a 30 s lease on the driver, renewed by the stream’s heartbeats. Accepts carry the offer ID; a second accept returns the same trip."),
                  ("whyb", "Covers, and does not", "Crashes, tunnels, ignored offers, retried accepts. Not a driver who is connected but not moving: that is a product rule.")) + rejl(*REJ(2))), [
 P, "C: The fix.", P, "C: The offer manager.", P,
 "C: One level down. An offer expires after fifteen seconds if not accepted. An accepted trip holds a thirty-second lease on the driver, renewed by the heartbeats the stream already carries. If the lease lapses, the driver becomes unavailable and the trip goes back to matching, at the front of the queue. And an accept carries the offer I-D, so a retried accept returns the same trip.", P,
 "C: It covers crashes, tunnels, ignored offers and retried accepts. Not a driver who's connected but not moving. That's a product rule on top.", P,
 "C: Rejected: a long fixed offer timeout. It either leaves riders waiting or takes trips from slow but willing drivers. Only a heartbeat lease tells the two apart."], cls="dia")
S(dia(K(2, "sequence"), "A lapsed lease, and a new driver", "seq-ch2-vanish"), [
 "C: As a sequence.", P, "C: Driver forty-two accepts.", P, "C: The app crashes. No more heartbeats.", P,
 "C: The lease on driver forty-two for this trip is thirty seconds, renewed by heartbeats.", P,
 "C: It lapses: the driver becomes unavailable, and the trip returns to matching.", P,
 "C: The rider sees: finding you a new driver, no charge. Thirty seconds lost, not seven minutes."], cls="dia")
S(plain(K(2, "choosing the lease"), "Thirty seconds, from two kinds of error", table(["Lease", "A vanished driver costs the rider", "A tunnel releases a willing driver"], [
  ["10 s", "10 s", "often: most tunnels and lifts are longer"],
  ["30 s", "30 s", "rarely: a long tunnel; the app reconnects and is told"],
  ["120 s", "2 minutes", "almost never, but riders wait for ghosts"]], "bt sm") +
  line("An initial target, to be measured: the gap distribution of heartbeats tells you where the knee is.", "a")), [
 "C: Why thirty seconds? Two kinds of error, against each other.", P,
 "C: Ten seconds: a vanished driver costs ten seconds, but most tunnels and lifts are longer, so willing drivers get released all the time.", P,
 "C: Thirty seconds: thirty seconds of waiting, and only long tunnels release a driver, who reconnects and is told.", P,
 "C: Two minutes: almost no false releases, and riders wait two minutes for ghosts.", P,
 "C: Thirty is an initial target. The distribution of gaps between heartbeats tells you where the knee really is, per city."])

qs("Interviewer · the second-level push", "“The driver’s phone comes back after 40 seconds and says: I’m on my way.”", [
 "I: The driver's phone comes back after forty seconds and says: I'm on my way.", "[pause: 1.5]"])
S(plain(K(2, "the second fix"), "The trip has moved on; the phone is told", cards(
  ("grn", "Version wins", "The reconnecting app sends its trip and version; the store says the trip was reassigned at version 23."),
  ("amb", "Told, not argued", "The app shows “trip reassigned” and returns the driver to available, at a new version."), cols=2)), [
 P, "C: The reconnecting app sends its trip and version. The store says the trip was reassigned, at a newer version, and the store wins.", P,
 "C: The app is told, not argued with: trip reassigned, and the driver is back to available. One owner, one version, no split brain."])
say_slide("“Every claim is a lease. An offer expires in fifteen seconds; an accepted trip holds a thirty-second lease renewed by heartbeats; accepts carry the offer ID. A vanished driver is released in half a minute, and a late phone is told the trip moved on.”", [
 "V: If asked, I'd say: every claim is a lease. An offer expires in fifteen seconds; an accepted trip holds a thirty-second lease renewed by heartbeats; and accepts carry the offer I-D. A vanished driver is released in half a minute, and a late phone is told the trip moved on.", "[pause: 1.0]",
 "N: That fix creates the next question: the claims are right. Are the candidates?"])

# ── 3
subchapter("7.3", "Challenge 3: Boundaries and hot cells", ["N: Challenge three: the geo index itself, at its edges and at its densest."])
qs("Interviewer · challenge 3 of 6", "“The nearest driver is 50 metres away, across a cell boundary. And downtown at six, one cell holds 3,000 drivers. Does your query cope?”", [
 "I: The nearest driver is fifty metres away, across a cell boundary. And downtown at six, one cell holds three thousand drivers. Does your query cope?", "[pause: 2.0]"])
S(dia(K(3, "edges and density"), "Which cells does a query read?", "ch3-attack", q=True, red=True,
      extra=strip(("case", "Naive answer", "“Look up the pickup’s cell; it’s small, so it’s near.”"),
                  ("case", "Break", "The query reads one cell: it misses the neighbour, and in a dense cell it reads 3,000 drivers."))), [
 P, "C: Inside the location index.", P, "C: The query is marked.", P, "C: The naive answer: look up the pickup's cell.", P,
 "C: Then a driver fifty metres away in the next cell is invisible, and a downtown cell returns three thousand drivers to rank."], cls="dia")
S(trace(K(3, "the trace"), "Too few, then too many", [
  ("07:30", "suburb: pickup near a cell edge; the cell is empty → “no drivers”"),
  ("07:30", B("a driver 50 m away in the next cell, idle")),
  ("18:00", "downtown: the pickup’s cell holds 3,000 drivers"),
  ("18:00", B("ranking 3,000 by ETA: 3,000 routing pairs per request"))],
  hedge=("One size fits neither", "Cells that are right for the suburb are wrong for downtown, and the other way round.")), [
 "C: The trace.", P, "C: Seven thirty, a suburb: the pickup is near a cell edge, the cell is empty, and the rider hears no drivers.", P,
 "C: A driver fifty metres away, in the next cell, is idle.", P, "C: Six p.m. downtown: the pickup's cell holds three thousand drivers.", P,
 "C: Ranking them all by E-T-A is three thousand routing pairs for one request.", P,
 "C: One cell size fits neither place."])
S(dia(K(3, "the fix"), "Rings of neighbours; hot cells indexed finer", "ch3-fix",
      extra=strip(("fixb", "Mechanism", "Read the k-ring (k = 1, then 2, then 3) until 20 candidates; sort by haversine distance. A cell over 300 drivers is also indexed at resolution 9, and dense pickups read the finer ring."),
                  ("whyb", "Covers, and does not", "Boundaries and density. Not distance by road: that is challenge five.")) + rejl(*REJ(3))), [
 P, "C: The fix.", P, "C: The query.", P, "C: And the cell table.", P,
 "C: One level down. The query reads the pickup's cell and its first ring; if that gives fewer than twenty candidates, the second ring, then the third. Candidates are sorted by straight-line distance and cut at twenty. A cell holding more than three hundred drivers is also indexed at the next finer resolution, and a pickup there reads finer rings: a few hundred drivers, not thousands.", P,
 "C: It covers boundaries and density. Not distance by road. That's challenge five.", P,
 "C: Rejected: geohash prefixes alone. Neighbours across a prefix boundary share no prefix, and the cells distort with latitude."], cls="dia")
S(plain(K(3, "the query, as pseudocode"), "Expand until enough, finer where crowded",
  pseudo("cell = h3(pickup, res = 9 if hot(pickup) else 8)\ncands = []\nfor k in 1, 2, 3:\n    for c in ring(cell, k) - seen:\n        cands += drivers_in(c)        # map lookups\n    if len(cands) >= 20: break\nreturn sort_by_haversine(cands, pickup)[:20]", hl=(1, 3, 7))), [
 "C: As pseudocode. Line one: a crowded pickup uses the finer resolution. Line three: expand ring by ring, each ring only the new cells. Line seven: sort by straight-line distance and keep twenty. Every step is a map lookup; nothing scans a city."])
qs("Interviewer · the second-level push", "“Stadium lets out: 20,000 riders in one cell, 400 drivers.”", [
 "I: The stadium lets out: twenty thousand riders in one cell, four hundred drivers.", "[pause: 1.5]"])
S(plain(K(3, "the second fix, and the honest limit"), "Not a geo problem any more: a queue", cards(
  ("grn", "Queue the pickup point", "Requests in one hot cell join a pickup-zone queue, served in order."),
  ("amb", "Bring supply", "Surge and a “drivers needed” signal move drivers in; that is pricing’s lever."),
  ("red", "Honest limit", "No index finds 20,000 drivers that are not there. Say the wait, honestly."), cols=3)), [
 P, "C: Requests in one hot cell join a pickup-zone queue and are served in order.", P,
 "C: Surge pricing and a drivers-needed signal bring supply. That's pricing's lever, not mine.", P,
 "C: The honest limit: no index finds twenty thousand drivers who aren't there. Tell the rider the wait."])
say_slide("“A cell index turns a radius into lookups, but a query must read rings of neighbours, expanding until it has enough candidates, and crowded cells are indexed at a finer resolution. Straight-line distance is only the shortlist; arrival time decides.”", [
 "V: If asked, I'd say: a cell index turns a radius into lookups, but a query must read rings of neighbours, expanding until it has enough candidates, and crowded cells are indexed at a finer resolution. Straight-line distance is only the shortlist. Arrival time decides.", "[pause: 1.0]",
 "N: That fix creates the next question: this index lives only in memory. What happens when a shard dies?"])
