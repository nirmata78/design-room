from dsl import *
from stack import REJ
P = "[+]"
B = lambda x: f'<span class="bad">{x}</span>'
K = lambda n, t: f"Challenge {n} of 6 · {t}"

# ── 4
subchapter("7.4", "Challenge 4: A shard dies", ["N: Challenge four: failure recovery for state you chose not to make durable."])
qs("Interviewer · challenge 4 of 6", "“The location shard for a big city dies with 50,000 drivers on it. What breaks, and for how long?”", [
 "I: The location shard for a big city dies with fifty thousand drivers on it. What breaks, and for how long?", "[pause: 2.0]"])
S(dia(K(4, "a lost shard"), "What was lost, and does it matter?", "ch4-attack", q=True, red=True,
      extra=strip(("case", "Naive answer", "“Replicate the index synchronously, like a database.”"),
                  ("case", "Break", "The driver table is gone: the city has no drivers until something refills it."))), [
 P, "C: Inside the location index.", P, "C: The driver table is marked.", P,
 "C: The naive answer: replicate the index synchronously, like a database.", P,
 "C: What actually breaks: the driver table is gone, and the city has no drivers until something refills it."], cls="dia")
S(trace(K(4, "the trace"), "Four seconds of an empty city, and one stale position", [
  ("18:00:00.0", "shard for city 12 dies; 50,000 drivers vanish from the index"),
  ("18:00:00.5", "the gateway routes city 12 to the standby shard, empty"),
  ("18:00:04.0", "every online driver has reported once: the index is full again"),
  ("18:00:04.2", B("a driver’s app flushes a 30 s-old buffered position after the new one"))],
  hedge=("What mattered", "Four seconds of “no drivers” in one city, and an old position that must not overwrite a new one.")), [
 "C: The trace.", P, "C: At six, the shard for city twelve dies, and fifty thousand drivers vanish from the index.", P,
 "C: Half a second later the gateway routes city twelve to a standby shard, empty.", P,
 "C: Four seconds later every online driver has reported once, and the index is full again.", P,
 "C: Then a driver's app flushes a buffered position from thirty seconds ago, after the fresh one.", P,
 "C: What mattered was four seconds of no drivers, and an old position that must not overwrite a new one."])
S(dia(K(4, "the fix"), "Refill from the next report; sequence numbers decide", "ch4-fix",
      extra=strip(("fixb", "Mechanism", "No replicas: a standby shard starts empty and fills from the next 4 s of reports. Ingest keeps only an update whose sequence is newer than the one held; requests in that city wait one tick."),
                  ("whyb", "Covers, and does not", "Shard loss and late, out-of-order updates. Not a gateway outage: drivers reconnect to other pods first.")) + rejl(*REJ(4))), [
 P, "C: The fix.", P, "C: Ingest.", P,
 "C: One level down. No replicas at all. A standby shard starts empty and fills from the next four seconds of reports, because every online driver reports every four seconds anyway. Ingest keeps an update only if its sequence number is newer than the one it holds, so a buffered old position is dropped. Requests in that city just wait a tick or two.", P,
 "C: It covers shard loss and late, out-of-order updates. Not a gateway outage: drivers reconnect to other pods first, and then refill the index the same way.", P,
 "C: Rejected: replicating the index synchronously. It doubles a million and a quarter writes a second to protect data that's stale in four seconds."], cls="dia")
S(plain(K(4, "what replication would cost"), "Protecting four seconds of data", table(["Option", "Extra writes", "Protects", "Verdict"], [
  ["Synchronous replica", "+1.25 M/s, on the hot path", "4 s of positions", "no"],
  ["Asynchronous replica", "+1.25 M/s, off the path", "4 s, mostly", "only for the biggest cities"],
  ("pick", ["<b>Refill from reports</b>", "none", "nothing; rebuilt in ~4 s", "yes, by default"])], "bt sm")), [
 "C: What replication would cost, to protect four seconds of data.", P,
 "C: A synchronous replica: another million and a quarter writes a second, on the hot path. No.", P,
 "C: An asynchronous replica: the same writes off the path, protecting most of the four seconds. Worth it only for the biggest cities, as a warm standby.", P,
 "C: Refilling from the reports: no extra writes at all, and the data is rebuilt in about four seconds. The default."])

S(plain(K(4, "ingest, as pseudocode"), "Latest wins, by sequence, not by arrival",
  pseudo("on update(d, lat, lng, seq, t):\n    cur = drivers.get(d)\n    if cur and seq <= cur.seq: return     # old, drop\n    cell = h3(lat, lng, 8)\n    if cur and cur.cell != cell:\n        cells[cur.cell].remove(d)\n    cells[cell].add(d)\n    drivers[d] = (cell, lat, lng, seq, t)", hl=(3, 7, 8))), [
 "C: As pseudocode. Line three: an update whose sequence isn't newer is dropped, which handles both the buffered flush and a reordered network path. Lines seven and eight: move the driver between cells and overwrite. There's no write-ahead log, and none is needed."])
qs("Interviewer · the second-level push", "“Four seconds of no drivers on New Year’s Eve is a lot of angry riders.”", [
 "I: Four seconds of no drivers on New Year's Eve is a lot of angry riders.", "[pause: 1.5]"])
S(plain(K(4, "the second fix, and the honest limit"), "Hide the gap; don’t pay for it everywhere", cards(
  ("grn", "Matcher waits", "A city whose shard is refilling holds requests for one extra tick instead of answering “no drivers”."),
  ("amb", "Warm standby", "Big cities keep a standby that subscribes to the gateway’s stream: it is already full when it takes over."),
  ("red", "Honest limit", "Small cities refill cold. Four seconds, once in a while, is the price of not replicating 1.25 M writes."), cols=3)), [
 P, "C: The matcher hides the gap: a city whose shard is refilling holds requests for one more tick instead of answering no drivers.", P,
 "C: For the biggest cities, a warm standby subscribes to the same updates, so it's already full when it takes over. That's replication, but only where it's worth it.", P,
 "C: The honest limit: small cities refill cold. Four seconds, now and then, is the price of not replicating everything."])
say_slide("“A location is soft state: it’s stale in four seconds, so I don’t replicate it. A lost shard refills from the next round of reports, sequence numbers stop old positions overwriting new ones, and only the biggest cities keep a warm standby.”", [
 "V: If asked, I'd say: a location is soft state. It's stale in four seconds, so I don't replicate it. A lost shard refills from the next round of reports, sequence numbers stop old positions overwriting new ones, and only the biggest cities keep a warm standby.", "[pause: 1.0]",
 "N: That fix creates the next question: the candidates are found. Is nearest the right one?"])

# ── 5
subchapter("7.5", "Challenge 5: Nearest is not closest", ["N: Challenge five: distance against time, and one rider against the whole city."])
qs("Interviewer · challenge 5 of 6", "“The nearest driver is 200 metres away, across a river. And at midnight on New Year’s Eve, nearest-first leaves half the riders with long waits. What do you change?”", [
 "I: The nearest driver is two hundred metres away, across a river. And at midnight on New Year's Eve, nearest-first leaves half the riders with long waits. What do you change?", "[pause: 2.0]"])
S(dia(K(5, "distance"), "What does “nearest” measure?", "ch5-attack", q=True, red=True,
      extra=strip(("case", "Naive answer", "“Take the closest driver, first come, first served.”"),
                  ("case", "Break", "Candidates are ranked by straight line, one request at a time."))), [
 P, "C: Inside the matcher.", P, "C: Candidates are marked.", P, "C: The naive answer: the closest driver, first come, first served.", P,
 "C: That ranks by straight line, one request at a time."], cls="dia")
S(trace(K(5, "the trace"), "Two hundred metres, twelve minutes", [
  ("23:59:58", "r77’s nearest driver: d42, 200 m away across the river"),
  ("23:59:58", B("d42’s route: 12 minutes over the next bridge")),
  ("00:00:01", "r78 asks; d42 was 3 minutes from r78 by road"),
  ("00:00:01", B("r78 gets a driver 9 minutes away instead"))],
  hedge=("Two errors", "Distance is not time, and greedy is not best for the batch.")), [
 "C: The trace.", P, "C: Rider seventy-seven's nearest driver is two hundred metres away, across the river.", P,
 "C: By road, twelve minutes.", P, "C: Three seconds later rider seventy-eight asks. Driver forty-two was three minutes from them by road.", P,
 "C: Seventy-eight gets a driver nine minutes away instead.", P, "C: Two errors: distance isn't time, and greedy isn't best for the batch."])
S(dia(K(5, "the fix"), "Shortlist by distance, rank by ETA, assign the batch", "ch5-fix",
      extra=strip(("fixb", "Mechanism", "20 candidates per request by distance; one ETA matrix call per tick (cached per cell pair, 30 s); a min-cost assignment over all pending requests; ETA timeout 300 ms → distance × detour factor."),
                  ("whyb", "Covers, and does not", "Rivers, one-ways, and greedy choices. Not traffic the routing service does not know.")) + rejl(*REJ(5))), [
 P, "C: The fix.", P, "C: The E-T-A ranker.", P, "C: And the assigner.", P,
 "C: One level down. Twenty candidates per request come from distance. Once per tick, one E-T-A matrix call covers every pending request against its candidates, cached per cell pair for thirty seconds. Then one minimum-cost assignment over the whole batch, so rider seventy-eight gets driver forty-two. If routing doesn't answer in three hundred milliseconds, distance times a detour factor stands in.", P,
 "C: It covers rivers, one-way streets and greedy choices. Not traffic that the routing service doesn't know about.", P,
 "C: Rejected: straight-line distance. A river, a one-way street or a highway exit turns two hundred metres into twelve minutes."], cls="dia")
S(plain(K(5, "greedy against batch"), "Two riders, two drivers: the order of arrival should not decide", table(["Plan", "r77 gets", "r78 gets", "Total wait"], [
  ["Greedy, nearest by distance", "d42: 12 min (river)", "d51: 9 min", "21 min"],
  ["Greedy, nearest by ETA", "d51: 6 min", "d42: 3 min", "9 min"],
  ("pick", ["<b>Batch, min-cost on ETA</b>", "d51: 6 min", "d42: 3 min", "<b>9 min</b>, and stable as the batch grows"])], "bt sm")), [
 "C: The same case as numbers.", P,
 "C: Greedy by distance: rider seventy-seven takes driver forty-two across the river, twelve minutes; seventy-eight gets a driver nine minutes away. Twenty-one minutes of waiting.", P,
 "C: Greedy by E-T-A happens to fix this pair: six and three. Nine minutes. But it still depends on who asked first.", P,
 "C: The batch solves all pending requests together: here also nine minutes, and as the batch grows to forty requests in a busy tick, it stays near the best total, where greedy drifts. That's what two seconds of waiting buys."])

S(plain(K(5, "one tick, as pseudocode"), "Shortlist, one matrix, one assignment, then claims",
  pseudo("reqs = pending(city)                     # every 2 s\ncands = {r: shortlist(r.pickup, 20) for r in reqs}\neta = matrix(reqs, cands, timeout=300ms,\n             fallback=haversine * 1.4)\nplan = min_cost_assignment(reqs, cands, eta)\nfor r, d in plan:\n    if not claim(d, r, epoch): retry_next_tick(r)\n    else: offer(d, r, expires=15s)", hl=(3, 5, 7))), [
 "C: One tick as pseudocode. Line three: one matrix call for the whole batch, with a timeout and a fallback. Line five: the assignment is solved over every pending request together. Line seven: each assignment still goes through the claim from challenge one, and a lost claim waits for the next tick."])
qs("Interviewer · the second-level push", "“Routing is down for ten minutes.”", ["I: Routing is down for ten minutes.", "[pause: 1.5]"])
S(plain(K(5, "the second fix"), "Degrade the ranking, never the claim", cards(
  ("amb", "Distance × detour", "Ranking falls back to straight-line distance times a per-city detour factor; matches are a little worse, never wrong."),
  ("grn", "Say so", "The dashboard marks matches made on fallback; ETAs shown to riders widen."), cols=2)), [
 P, "C: Ranking falls back to straight-line distance times a detour factor measured per city. Matches are a little worse, never wrong: the claim doesn't depend on routing.", P,
 "C: And we say so: matches made on fallback are marked, and the arrival times shown to riders widen."])
say_slide("“Distance shortlists; time decides. Twenty candidates per request by distance, one ETA matrix per tick, cached by cell pair, and a minimum-cost assignment over the whole batch. If routing is slow, distance times a detour factor stands in: worse, never wrong.”", [
 "V: If asked, I'd say: distance shortlists; time decides. Twenty candidates per request by distance, one E-T-A matrix per tick cached by cell pair, and a minimum-cost assignment over the whole batch. If routing is slow, distance times a detour factor stands in: worse, never wrong.", "[pause: 1.0]",
 "N: That fix creates the last question: how would you know matching got worse?"])

# ── 6
subchapter("7.6", "Challenge 6: “No drivers” next to idle drivers", ["N: Challenge six is observability, measured where riders feel it."])
qs("Interviewer · challenge 6 of 6", "“Riders in one city are told ‘no drivers available’ while drivers there sit idle. How would you have known before Twitter did?”", [
 "I: Riders in one city are told no drivers available, while drivers there sit idle. How would you have known before Twitter did?", "[pause: 2.0]"])
S(dia(K(6, "a silent failure"), "Where does a healthy system return a wrong answer?", "ch6-attack", q=True, red=True,
      extra=strip(("case", "Naive answer", "“Request success rate and latency are green.”"),
                  ("case", "Break", "The matcher answers fast and correctly from a shard that stopped receiving one gateway’s updates."))), [
 P, "C: The ride A-P-I, the matcher, the index, the trip store.", P, "C: The matcher is marked.", P,
 "C: The naive answer: request success rate and latency are green.", P,
 "C: They are. The matcher answers quickly and correctly, from a shard that stopped receiving one gateway's updates."], cls="dia")
S(trace(K(6, "the trace"), "Green dashboards, empty cars", [
  ("17:40", "a gateway deploy breaks forwarding for 10 % of drivers in city 3"),
  ("17:44", "those drivers expire from the index; they are still online, idle"),
  ("17:44 – 18:30", B("riders nearby: “no drivers available”; success rate 100 %")),
  ("18:30", B("the first complaint arrives on social media"))],
  hedge=("What the dashboards saw", "Every request answered quickly. “No drivers” is a successful response.")), [
 "C: The trace.", P, "C: A gateway deploy breaks forwarding for a tenth of the drivers in city three.", P,
 "C: They expire from the index while still online and idle.", P,
 "C: For fifty minutes, nearby riders hear no drivers, and the success rate is a hundred percent.", P,
 "C: The first complaint arrives on social media.", P, "C: No drivers is a successful response."])
S(dia(K(6, "the fix"), "Version four: probes that take trips", "base-v4", vtag="V4"), [
 P, "C: The fix changes the design: version four. Version three, carried.", P,
 "C: New: probe riders. In every city, every minute, a fake driver reports a position and a fake rider requests a trip next to it, end to end."], cls="dia")
S(plain(K(6, "the fix, one level down"), "Measure what riders feel", cards(
  ("grn", "Probe trips", "A fake driver and rider per city per minute: matched, offered, accepted, released."),
  ("grn", "Idle next to “no”", "“No drivers” answers where the gateway says online, available drivers are within 2 km."),
  ("grn", "Stale share", "Online drivers missing from the index, per gateway pod."),
  ("grn", "Time to offer", "p95 per city, against 5 s."), cols=2) + rejl(*REJ(6))), [
 "C: One level down, four signals.", P, "C: Probe trips: a fake driver and rider per city per minute, matched, offered, accepted and released. A failure pages.", P,
 "C: Idle next to no: count no-driver answers where the gateway knows of online, available drivers within two kilometres. That one would have fired at seventeen forty-five.", P,
 "C: The stale share: drivers the gateway sees online but the index doesn't have, per pod. It names the broken pod.", P,
 "C: And time to offer, per city, against five seconds.", P,
 "C: Rejected: the request success rate. It stays green while riders are told no drivers next to idle ones."])
S(plain(K(6, "reading the signals"), "Symptoms in pairs", table(["Symptom", "Paired with", "Means"], [
  ["“No drivers” up", "idle drivers nearby", "an index gap: check the stale share"],
  ["“No drivers” up", "no idle drivers", "real demand: surge’s problem"],
  ["Offers expiring", "one app version", "a client bug, not matching"],
  ["Claims failing", "a new leader epoch", "a leadership change in progress"],
  ["Time to offer up", "ETA calls slow", "routing, on fallback"]], "bt sm")), [
 "C: And read them in pairs.", P, "C: No drivers up, with idle drivers nearby: an index gap. Our case.", P,
 "C: No drivers up, with no idle drivers: real demand. Surge's problem, not mine.", P,
 "C: Offers expiring, all from one app version: a client bug.", P,
 "C: Claims failing, with a new leader epoch: a leadership change in progress.", P,
 "C: And time to offer up, with slow E-T-A calls: routing, and we're on the fallback."])
S(plain(K(6, "the SLIs"), "What matching promises, measured", table(["SLI", "Target", "Measured by"], [
  ["Probe trips completed", "100 % per city", "the probes, every minute"],
  ["Time to offer", "p95 ≤ 5 s", "request to offer, per city"],
  ["“No drivers” with idle drivers nearby", "≤ 0.1 %", "the gateway’s view against the answers"],
  ["Online drivers missing from the index", "≤ 0.5 %", "gateway against index, per pod"],
  ["Double assignments", "0", "a nightly audit of driver_state"]], "bt sm")), [
 "C: And the matching service levels, so health is numbers.", P, "C: Probe trips completed: a hundred percent per city. One failure pages.", P,
 "C: Time to offer: ninety-fifth percentile within five seconds, per city.", P,
 "C: No-driver answers with idle drivers nearby: at most a tenth of a percent.", P,
 "C: Online drivers missing from the index: at most half a percent, per gateway pod.", P,
 "C: And double assignments: zero, checked by a nightly audit of driver state, because S-one deserves its own alarm."])

say_slide("“I’d measure what riders feel: probe trips in every city every minute, ‘no drivers’ answers next to idle drivers, online drivers missing from the index, and time to offer per city. ‘No drivers’ is a successful response, so success rates can’t see this.”", [
 "V: If asked, I'd say: I'd measure what riders feel. Probe trips in every city every minute, no-driver answers next to idle drivers, online drivers missing from the index, and time to offer per city. No drivers is a successful response, so success rates can't see this.", "[pause: 1.0]"])

# ── recap
chapter(8, "Recap", 6, "The final design, and what to say", ["C: The recap: one picture, the mechanisms, and the mistakes that cost most."])
S(dia("Recap · version four", "Where each mechanism ended up", "recap"), [
 P, "C: Version four, the final design.", P, "C: The location index: cells as keys, and soft state.", P,
 "C: The matcher: conditional, fenced claims, and batched assignment.", P, "C: The trip store, where the claim is one conditional update.", P,
 "C: The gateway, carrying the heartbeats that renew the leases.", P, "C: And the probes, measuring what riders feel."], cls="dia")
S(plain("Recap · one sentence per path", "Four paths, four sentences", cards(
  ("", "Report", "A location rides an open stream into a city’s in-memory cells; latest wins; silence expires."),
  ("grn", "Match", "Every two seconds the city’s one matcher shortlists by distance, ranks by ETA and assigns the batch."),
  ("amb", "Accept", "A conditional, fenced write claims the driver; the offer expires; the accept is idempotent."),
  ("red", "Track", "The assigned driver’s stream is forwarded to the rider; nothing reads a database."), cols=2)), [
 "C: One sentence per path.", P,
 "C: Report: a location rides an open stream into a city's in-memory cells. Latest wins, and silence expires.", P,
 "C: Match: every two seconds the city's one matcher shortlists by distance, ranks by E-T-A, and assigns the whole batch.", P,
 "C: Accept: a conditional, fenced write claims the driver, the offer expires if ignored, and the accept is idempotent.", P,
 "C: Track: the assigned driver's stream is forwarded to the rider. Nothing on that path reads a database."])

S(plain("Recap · the mistakes", "What costs most in this round", table(["Mistake", "Instead"], [
  ["Every location written to a database", "memory, overwrite-only, sequence numbers, expiry"],
  ["Nearest wins, no claim", "one conditional, fenced write per assignment"],
  ["An offer that never expires", "offer timeouts; heartbeat leases on trips"],
  ["One cell, no neighbours", "k-rings that expand; finer cells where crowded"],
  ["Straight-line nearest, first come first served", "ETA on a shortlist; batched assignment"],
  ["Watching success rates", "probe trips; idle drivers next to “no drivers”"]], "bt sm")), [
 "N: The mistakes that cost most.", P, "N: Every location written to a database. Instead, memory, overwrite-only.", P,
 "N: Nearest wins with no claim. Instead, one conditional, fenced write.", P,
 "N: An offer that never expires. Instead, timeouts and heartbeat leases.", P,
 "N: One cell with no neighbours. Instead, expanding rings and finer cells where it's crowded.", P,
 "N: Straight-line nearest, first come first served. Instead, E-T-A on a shortlist, and a batch.", P,
 "N: And watching success rates. Instead, probe trips and idle drivers next to no-driver answers."])
key("The close", "Keep <em>where drivers are</em> fast and forgettable, keep <em>who gets which driver</em> exact and fenced, and make every claim a <em>lease</em> that expires.", [
 "V: Keep where drivers are fast and forgettable. Keep who gets which driver exact and fenced. And make every claim a lease that expires.", "[pause: 1.0]",
 "C: Thanks for watching. The written design is linked below."])
