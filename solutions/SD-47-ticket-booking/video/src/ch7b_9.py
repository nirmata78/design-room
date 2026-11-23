from dsl import *

K = lambda n, t: f"Challenge {n} of 8 · {t}"

# ───────── Challenge 5 · a fair line, and the bots ─────────
subchapter("7.5", "Challenge 5: A fair line, and the bots", ["N: Challenge five. The line exists; now who is first in it, and what stops a bot from taking every seat?"])
qs("Interviewer · challenge 5 of 8", "“What does fair mean here, and who decided? And how do you stop a bot holding all fifty thousand seats?”", [
 "I: What does fair mean here, and who decided? And how do you stop a bot holding all fifty thousand seats?", "[pause: 2.0]"])

S(dia(K(5, "a fair line, and the bots"), "Who is first in the line?", "ch5-attack", q=True, red=True,
      extra=strip(("case", "Naive answer", "“Strict first-come-first-served from the moment sales open.”"),
                  ("case", "Break", "The order is decided in the first few hundred milliseconds, by whoever is fastest."))), [
 "C: The naive answer: strict first-come, first-served from the moment sales open. Look at the join arrow into the waiting room. The order of a million people is decided in the first few hundred milliseconds, and that rewards exactly the wrong things."], cls="dia")

S(plain(K(5, "the trace"), "Speed wins, and everyone refreshes at once", '<pre class="trace"><span class="t">09:59:59.9  </span>a million fans press refresh: <span class="bad">a self-inflicted load spike</span>\n<span class="t">10:00:00.000  </span>sales open\n<span class="t">10:00:00.005  </span><span class="bad">a data-centre bot at 5 ms latency joins first, thousands of times</span>\n<span class="t">10:00:00.250  </span>a fan on a phone network at 250 ms joins <span class="bad">behind them</span>\n<span class="t">10:00:01      </span>the first few thousand places belong to <span class="bad">machines and good networks</span></pre>' +
  '<div class="hedge"><b class="t">Label the numbers</b>Illustrative latencies. The shape is what matters: the whole ranking is set by speed in the first second.</div>', q=True, red=True), [
 "C: The trace. A million fans press refresh at a few seconds to ten, a spike we caused ourselves. At ten, sales open. At five milliseconds a bot in a data centre joins, thousands of times. A fan on a phone network, at two hundred and fifty milliseconds, joins behind them. In the first second the first few thousand places belong to machines and good networks."])

S(dia(K(5, "the fix"), "A lottery for everyone present, then first-come", "ch5-fix",
      extra=strip(("fixb", "Mechanism", "Everyone in the lobby before the start gets a random place. Latecomers go behind in arrival order. One entry per verified account. Signed tokens."),
                  ("whyb", "Property", "Fairness is the removal of the advantage speed gives. A random draw at join time costs nothing at the start."))), [
 "C: The fix. Everyone who is in the lobby before the start is treated the same: a random order. Arriving at nine-thirty or at one minute to ten makes no difference. Anyone who arrives after the start joins behind every lobby fan, in arrival order. Coming early still beats coming late, so there is a clear reason to be on time. And it is a product policy: the lobby page must say so. I would take it to the promoter, not present it as an engineering fact."], cls="dia")

S(plain(K(5, "the draw"), "A random score at join time, drawn on the server",
  '<pre class="code"><span class="cm">// on join, before the sale: one in-memory step</span>\nscore = cryptoRandom()                 <span class="cm">// server side, never sent to the client</span>\nZADD lobby:{e} NX score user            <span class="cm">// NX: keep the first score</span>\n\n<span class="cm">// at the start: no batch shuffle of a million entries</span>\nphase:{e} = QUEUE\n<span class="cm">// each fan asks once, with a random delay of 0 to 20 s:</span>\nmy number = rank(user) + 1             <span class="cm">// sorted by score</span>\n<span class="cm">// after the start: the next number goes to the back</span>\nseq = INCR next:{e}</pre>' +
  grade("Why a score at join time and not a shuffle at the start? They give the same uniform order, and the first costs nothing in the critical second.")), [
 "C: The draw in pseudocode. On join, draw a random score on the server and never send it to the client. Add the fan to the lobby set with a no-overwrite flag, so joining again keeps the first score. At the start nothing is shuffled: the order already exists. Each fan asks once for their number, after a random delay, and it is their rank plus one. Late arrivals take the next number from a counter. Independent random numbers, sorted, are the same as a shuffle, and cost nothing in the critical second."])

S(plain(K(5, "the bots"), "Make bots expensive, in layers", table(["Control", "What it stops"], [
  ["<b>A challenge at the lobby</b>", "scripts that cannot pass it, at the edge, before they reach a queue"],
  ["<b>One entry per verified account</b>, bound to a device", "an account farm is the real attack; verification makes accounts expensive"],
  ["<b>Limits per account and per payment card</b>", "one buyer with many accounts is caught at the card"],
  ["<b>Signed, short-lived tokens, bound to the user</b>", "a place cannot be forged, traded or shared at scale"],
  ["<b>Pre-registered, screened fans</b> for flagship events", "only people checked offline may join"],
  ["<b>After the sale</b>: cancel flagged orders, release to the waitlist", "what slipped through, caught late"]], "bt sm")), [
 "C: Bots, in layers, because no layer is enough. A challenge at the lobby entry, at the edge. One entry per verified account, bound to a device: an account farm is the real attack, so verification makes accounts expensive. Limits per account and per payment card, because the card catches one buyer with many accounts. Signed short-lived tokens bound to the user, so a place cannot be forged or sold at scale. Pre-registered, screened fans for flagship events. And after the sale, cancelling flagged orders and releasing those seats to the waitlist."])

qs("Interviewer · the second-level push", "“A farm of verified accounts gets through. Now what?”", [
 "I: A farm of verified accounts gets through. Now what?", "[pause: 2.0]"])

S(plain(K(5, "the second fix, and the honest limit"), "Make the second layer cost more than the first", '<div class="cards c2">'
  '<div class="cd grn"><h3>Cheap controls that scale</h3><p>Limits per card and per device, fraud scoring after the fact, and orders cancelled and re-released to real fans on the waitlist.</p></div>'
  '<div class="cd amb"><h3>The honest limit</h3><p>No scheme is bot-proof. The aim is to make a bot expensive enough that it is not worth it, and to say so to the promoter.</p></div></div>' +
  line("Fairness, and how far to go on bots, is a product and risk decision. I bring the options and the costs.", "a")), [
 "C: Cheap controls that scale: limits per card and per device, fraud scoring after the fact, and orders cancelled and re-released to real fans on the waitlist. The honest limit: no scheme is bot-proof. The aim is to make a bot expensive enough that it is not worth it, and to say so to the promoter. How far to go is a product and risk decision. I bring the options and the costs."])

say_slide("“Fairness is a product decision, so I would take it to the promoter: a lottery for everyone in the lobby at the start, then first-come. Each place is a signed number, so it cannot be forged or traded. And I would make bots expensive, with one entry per verified account and limits per card.”", [
 "V: If asked, I'd say: fairness is a product decision, so I would take it to the promoter: a lottery for everyone in the lobby at the start, then first-come. Each place is a signed number, so it cannot be forged or traded. And I would make bots expensive, with one entry per verified account and limits per card.", "[pause: 1.0]",
 "N: That fix creates the next question: what do the admitted fans see, and how stale can it be?"])

# ───────── Challenge 6 · the seat map ─────────
subchapter("7.6", "Challenge 6: The seat map for ten thousand shoppers", ["N: Challenge six. Ten thousand admitted fans all want to see the seats: where does that read go?"])
qs("Interviewer · challenge 6 of 8", "“Is a user allowed to see a seat as available and then fail to get it?”", [
 "I: Is a user allowed to see a seat as available and then fail to get it?", "[pause: 2.0]"])

S(dia(K(6, "the seat map"), "Where does a read of fifty thousand seats go?", "ch6-attack", q=True, red=True,
      extra=strip(("case", "Naive answer", "“Each shopper reads the seat table every two seconds.”"),
                  ("case", "Break", "The reads lock against the claims and starve them of connections."))), [
 "C: The naive answer: each shopper reads the seat table every couple of seconds. Look at the path into the seat database again. Five thousand reads a second now compete with the claims for the same rows and the same connections. The part of the system that must be fastest slows down because of the part that is only a picture."], cls="dia")

S(plain(K(6, "the trace"), "Reads starve the writes", '<pre class="trace"><span class="t">10:05:00  </span>10,000 shoppers ÷ 2 s = <span class="bad">5,000 reads / s</span> of 50,000 rows\n<span class="t">10:05:01  </span>the reads share the connection pool with the claims\n<span class="t">10:05:03  </span><span class="bad">hold p99 climbs from 40 ms to 600 ms</span>\n<span class="t">10:05:04  </span>the controller cuts the rate: <span class="bad">the line slows because of a picture</span></pre>' +
  '<div class="hedge"><b class="t">Label the numbers</b>Illustrative latencies; the 5,000 reads a second is derived from ten thousand shoppers and a two-second refresh.</div>', q=True, red=True), [
 "C: The trace. Ten thousand shoppers every two seconds is five thousand reads a second against fifty thousand rows. They share the connection pool with the claims. Hold latency at the ninety-ninth percentile climbs from forty milliseconds to six hundred. The controller sees it and cuts the rate, so the line slows because of a picture. The latencies are illustrative."])

S(dia(K(6, "the fix"), "An immutable layout, and a bitmap built from the event log", "ch6-fix",
      extra=strip(("fixb", "Mechanism", "Layout on the CDN, never changes. Availability is a bitmap built from the event log, at most one version a second, served by version with a 304."),
                  ("whyb", "Property", "L2 and L3: the claim is the authority, the map is a hint. A stale click fails fast with a fresh map."))), [
 "C: The fix. Split the map in two. The layout, the seat positions and prices, never changes during a sale, so it comes from the edge and is cached for a year. The availability is the live part: one bit per seat. The database writes a change and an outbox row in one transaction. The event log carries it. The snapshot builder, the new box at the top, keeps the bitmap in memory, and at most once a second publishes a new version to the seat-map cache. The edge serves it by version."], cls="dia")

S(dia(K(6, "the bitmap"), "One bit per seat: six and a quarter kilobytes", "bitmap"), [
 "C: The bitmap, bit by bit. Seat eight hundred twelve is bit eight hundred twelve, because the identifiers are dense. A one is available, a zero is taken. Fifty thousand bits is six and a quarter kilobytes. The version is the log offset, because it only ever grows, survives a restart of the builder, and two builders reading the same partition agree on it. A counter in memory would reset, and clients would see versions go backwards."], cls="dia")

S(dia(K(6, "sequence"), "From a committed hold to a fan's map", "seq-seatmap"), [
 "C: As a sequence. A hold commits with its outbox row. A log-based relay reads the database's write-ahead log and publishes the row to the event log: if the relay is down, rows wait in the log and nothing is lost. The snapshot builder applies the change and marks the event dirty. Once a second it writes a new versioned bitmap and flips the pointer last. A fan's poll carries the version it has: a not-modified if nothing changed, the new body otherwise."], cls="dia")

qs("Interviewer · the second-level push", "“The stream stalls for a minute. What does the fan see?”", [
 "I: The stream stalls for a minute. What does the fan see?", "[pause: 2.0]"])

S(plain(K(6, "the second fix, and the honest limit"), "Staleness grows. Correctness does not.", '<div class="cards c2">'
  '<div class="cd grn"><h3>A stale click fails fast</h3><p>The claim is authoritative. A click on a seat taken 800 ms ago fails in milliseconds with a 409 and the current bitmap. That is a graceful failure, not a bug.</p></div>'
  '<div class="cd amb"><h3>The builder can rebuild</h3><p>Cold start: one scan of the table, then resume from the committed log offset. A lagging builder is a metric, and an alert.</p></div></div>' +
  line("Optional later: push seat deltas to the ten thousand admitted fans over a persistent connection. Polling a 6 KB bitmap is good enough for the first release.", "a")), [
 "C: Staleness grows; correctness does not. The claim is authoritative, so a click on a seat taken eight hundred milliseconds ago fails in milliseconds with a four-oh-nine and the current bitmap. That is a graceful failure, not a bug. The builder can always rebuild: one scan of the table, then resume from the committed offset, and a lagging builder is an alert. A later upgrade is to push changes to the admitted fans, but polling a six-kilobyte bitmap is good enough for the first release."])

say_slide("“The map may be a second or two stale because the write path decides. The layout is immutable on the edge, and the availability is a six-kilobyte bitmap, rebuilt once a second from the event stream and served by version. A stale click fails fast with a fresh map.”", [
 "V: If asked, I'd say: the map may be a second or two stale because the write path decides. The layout is immutable on the edge, and the availability is a six-kilobyte bitmap, rebuilt once a second from the event stream and served by version. A stale click fails fast with a fresh map.", "[pause: 1.0]",
 "N: That fix creates the next question: what if the requirements change in the middle of the sale?"])

# ───────── Challenge 7 · requirements that arrive mid-sale ─────────
subchapter("7.7", "Challenge 7: Requirements that arrive mid-sale", ["N: Challenge seven. The promoter changes the plan while the sale is running: does the design bend, or break?"])
qs("Interviewer · challenge 7 of 8", "“The promoter wants to release five thousand more seats, mid-sale.”", [
 "I: The promoter wants to release five thousand more seats, mid-sale.", "[pause: 2.0]"])

S(dia(K(7, "mid-sale changes"), "What changes, what does not, what it costs?", "ch7-attack", q=True, red=True,
      extra=strip(("case", "Naive answer", "“Redesign it, or stop the sale and restart.”"),
                  ("case", "Break", "A cached layout and map, and a sold-out flag already shown to 970,000 people."))), [
 "C: The naive answer: redesign it, or stop the sale and restart. Look at what is outlined. The cached layout and map, and the waiting room's sold-out flag. Forty-five thousand seats are sold, and nearly a million people have already been told it is over. The question is whether the design bends or breaks, and I will say aloud what changes, what does not, and what it costs."], cls="dia")

S(plain(K(7, "the trace"), "Five thousand rows, under a live sale", '<pre class="trace"><span class="t">10:41  </span>45,000 seats are sold. The sold-out flag has reached <span class="bad">970,000 waiting fans</span>\n<span class="t">10:42  </span>the promoter asks for 5,000 more rows, now, while holds continue\n<span class="t">10:42  </span>the layout browsers cached lists 50,000 seats: <span class="bad">the new ones do not exist for them</span>\n<span class="t">10:43  </span>the bitmap is 50,000 bits: <span class="bad">seats 50,000 to 54,999 have no bit</span>\n<span class="t">10:43  </span>the controller is paused on sold out: <span class="bad">nobody new is admitted</span></pre>' +
  '<div class="hedge"><b class="t">Label the numbers</b>Illustrative times; 45,000 sold and 5,000 released are the exercise numbers.</div>', q=True, red=True), [
 "C: The trace. Forty-five thousand seats are sold, and the sold-out flag has reached nearly a million waiting fans. The promoter asks for five thousand more rows now, while holds continue. The layout that browsers cached lists fifty thousand seats, so the new ones do not exist for them. The bitmap is fifty thousand bits: the new seats have no bit. And the controller is paused on sold out, so nobody new is admitted."])

S(plain(K(7, "the delta, in a table"), "Each new requirement, and the seam that absorbs it", table(["New requirement", "What changes", "What does not change"], [
  ["<b>Release 5,000 more seats</b>", "Insert the rows as available in one transaction. New layout version, so a new edge key. Clear the sold-out flag; the controller resumes", "The claim path. New rows are claimable like any other"],
  ["<b>A waitlist when sold out</b>", "A new consumer of the seat-released events offers a freed seat to the next fan as a <b>targeted hold</b>. One nullable column", "The line, and the claim"],
  ["<b>Best available</b>", "A server-side allocator picks adjacent seats and hands different fans different seats: less contention", "The same conditional claim, from a different source of seat ids"],
  ["<b>A tour: twenty shows, ten times the traffic</b>", "One line per show, a cross-show lobby, a dedicated cell for mega events, a payment budget split across events", "The per-event design already shards by event"]], "bt sm")), [
 "C: Four new requirements, and the seam that absorbs each. Release five thousand seats: insert the rows as available in one transaction, publish a new layout version so the edge has a new key, clear the sold-out flag, and the controller resumes. The claim path does not change.",
 "C: A waitlist: a new consumer of the seat-released events offers a freed seat to the next fan as a targeted hold, with one nullable column. Best available: a server-side allocator hands different fans different seats, so contention drops; same claim, a different source of seat identifiers. And a tour: next."])

S(dia(K(7, "the fix"), "The waitlist is a new consumer, not a redesign", "ch7-fix",
      extra=strip(("fixb", "Mechanism", "New rows are inserted in one transaction with a new layout version. A released seat is announced on the event log; the waitlist consumes it and creates a targeted hold."),
                  ("whyb", "Property", "The extension seams were real: new demand lands as consumers and read models, not as a rewrite."))), [
 "C: On the baseline. The new box, top right, is the waitlist. It subscribes to the same event log the snapshot builder already reads. When a seat is released it creates a targeted hold for the next waiting fan, an ordinary held row with a ten-minute expiry, and sends a notification with a link that carries an admission token for that fan only. Inventory gets one nullable column. Nothing else moves."], cls="dia")

S(dia(K(7, "the tour"), "Everything is keyed by event, so events are independent", "fu-multi-event"), [
 "C: A twenty-date tour on sale at once. Everything is keyed by event: the Redis keys, the database partitions, the log key, the admission token, the edge cache key. So events are independent by construction, and running many at once is an isolation problem, not a coordination one. Small events pack into a shared cell. A mega on-sale gets its own cell and Redis node, moved the day before, because on-sales are scheduled."], cls="dia")

S(plain(K(7, "shared resources"), "The three things events share, and how I divide them", '<div class="cards c3">'
  '<div class="cd amb"><h3>The payment provider</h3><p>A contract of, say, 300 authorizations a second. Twenty dates at 25 a second each would want 500. <b>Stagger the on-sales</b>, split the budget per event, or add a second provider.</p></div>'
  '<div class="cd amb"><h3>The admission budget</h3><p>The sum of every event\'s rate must fit the shared gateway and order fleets. A small coordinator gives each event a ceiling, weighted by expected demand.</p></div>'
  '<div class="cd red"><h3>The fan</h3><p>A fan can join all twenty queues to improve their odds. <b>One active queue per account per tour</b>, with preferred dates, or a cap on tickets per account. A product question.</p></div></div>' +
  line("Numbers illustrative. Most days thousands of events trickle, and a queue would only annoy people: it switches on past a threshold.", "a")), [
 "C: Three shared resources. The payment provider: say the contract allows three hundred authorizations a second, and twenty dates at twenty-five a second each would want five hundred. I would stagger the on-sales, which is a product conversation to start weeks ahead, or split the budget per event, or add a second provider. The admission budget: a small coordinator gives each event a ceiling, weighted by expected demand.",
 "C: And the fan: they can join all twenty queues to improve their odds. One active queue per account per tour, with a list of preferred dates, is fairer and cheaper, or a cap on tickets per account per tour. A product question. And on quiet days a queue would only annoy people, so it switches on past a threshold."])

qs("Interviewer · the second-level push", "“Two mega events land on the same Redis node and share one provider budget. Then?”", [
 "I: Two mega events land on the same Redis node and share one provider budget. Then?", "[pause: 2.0]"])

S(plain(K(7, "the second fix, and the honest limit"), "Place them apart the day before; the on-sale calendar is a gift", '<div class="cards c2">'
  '<div class="cd grn"><h3>Pin and separate</h3><p>Pin the hot events\' slots to separate nodes and move a mega event to a dedicated cell before the sale. Fleets are scaled ahead from the calendar, not reactively.</p></div>'
  '<div class="cd amb"><h3>The limit</h3><p>A provider budget is a contract; past it, only staggering or a second provider helps. Multi-region: each event is homed in one region with a single writer, never multi-master seats.</p></div></div>'), [
 "C: Place them apart the day before. Pin the hot events' slots to separate nodes, move a mega event to a dedicated cell, and scale the fleets from the on-sale calendar rather than reactively. On-sales are scheduled weeks ahead: that is a gift, and I should use it. The limit: a provider budget is a contract, so past it only staggering or a second provider helps. And if multi-region comes up: each event is homed in one region with a single writer, with a synchronous replica in a second zone. Never multi-master writes on seats."])

say_slide("“Say what changes, what does not, and what it costs. Releasing seats is an insert and a new layout version; the claim does not move. The waitlist is a new consumer of the stream. And a tour is an isolation problem, not a coordination one, because everything is keyed by event.”", [
 "V: If asked, I'd say: say what changes, what does not, and what it costs. Releasing seats is an insert and a new layout version; the claim does not move. The waitlist is a new consumer of the stream. And a tour is an isolation problem, not a coordination one, because everything is keyed by event.", "[pause: 1.0]",
 "N: One question left, and it is the one that decides whether anyone sleeps: how would you know?"])

# ───────── Challenge 8 · observability ─────────
subchapter("7.8", "Challenge 8: How would you know it is broken?", ["N: Challenge eight, always the last. The system is built; how would we know it is failing, before the fans tell us?"])
qs("Interviewer · challenge 8 of 8", "“What is the S-L-O for the sale opening, and what is your plan for the day it fails?”", [
 "I: What is the S-L-O for the sale opening, and what is your plan for the day it fails?", "[pause: 2.0]"])

S(dia(K(8, "how would you know?"), "The dashboard is green and the line has stopped", "ch8-attack", q=True, red=True,
      extra=strip(("case", "Naive answer", "“CPU, error rate and a dashboard.”"),
                  ("case", "Break", "The failures here are silent: nothing crashes, the line just stops moving."))), [
 "C: The naive answer: C-P-U, error rate and a dashboard. Look at the booking A-P-I, and notice what is not outlined: everything looks healthy. The failures in this system are silent. Nothing crashes. A provider outage leaves seats frozen on unknown payments, the controller cuts the rate, and the line simply stops moving, while every machine reports green."], cls="dia")

S(plain(K(8, "the trace"), "A quiet failure, seen too late", '<pre class="trace"><span class="t">10:12  </span>the provider slows: authorizations go from 3 s to 14 s\n<span class="t">10:13  </span><span class="bad">1,900 orders are UNKNOWN; their 3,800 seats are frozen</span>\n<span class="t">10:14  </span>the controller sees hold latency fine, but shoppers are not leaving: <span class="bad">it holds R</span>\n<span class="t">10:16  </span><span class="bad">the shop is full of people who cannot pay; admissions fall to zero</span>\n<span class="t">10:18  </span>all dashboards green. <span class="bad">Social media is not</span></pre>' +
  '<div class="hedge"><b class="t">Label the numbers</b>Illustrative. The point is that no single machine metric moved.</div>', q=True, red=True), [
 "C: The trace. At twelve past, the provider slows from three seconds to fourteen. By thirteen, nineteen hundred orders are unknown, and their thirty-eight hundred seats are frozen. Hold latency is fine, so the controller does not cut the rate, but shoppers are not leaving. By sixteen the shop is full of people who cannot pay, and admissions fall to zero. At eighteen all the dashboards are green, and social media is not. The numbers are illustrative: the point is that no single machine metric moved."])

S(dia(K(8, "the fix"), "Measure the promise, not the machine", "ch8-fix",
      extra=strip(("fixb", "Mechanism", "Indicators tied to promises, a synthetic fan through the whole path every ten seconds, and a plan for degradation."),
                  ("whyb", "Property", "Everything the system promises, watched where it fails silently."))), [
 "C: The fix. The new box is a probe: a synthetic fan, every ten seconds, through the whole path: the lobby, a hold on a reserved test seat, a release. If a fan cannot complete a purchase, I want to know before a real one tells me. And the indicators are tied to promises, not machines."], cls="dia")

S(plain(K(8, "the indicators"), "What I watch, and the promise each protects", table(["Indicator", "Promise it watches", "Alert when"], [
  ["<b>Hold p99</b> and the 409 ratio", "claims are fast; contention is expected", "p99 above 300 ms, or 409s far above the plan"],
  ["<b>Admission rate</b> against shop health", "the line keeps moving", "rate falls while hold latency is flat"],
  ["<b>Age of the oldest expired hold</b>", "L1: no seat stuck", "above 30 s"],
  ["<b>Seats frozen by unknown payments</b>, and their age", "S2, L1: money and seats agree", "count or age beyond a deadline"],
  ["<b>Queue state and map version lag</b>", "L2: fans see the truth", "stale beyond a few seconds"],
  ["<b>Tickets issued against seats sold</b>", "<b>S1</b>: never twice", "any difference at all: page immediately"]], "bt sm")), [
 "C: The indicators. Hold latency and the conflict ratio. The admission rate against shop health: if the rate falls while hold latency is flat, something other than the database is wrong. The age of the oldest expired hold, above thirty seconds. Seats frozen by unknown payments, and their age. Queue state and map version lag. And the one that must never differ: tickets issued against seats sold. Any difference, page immediately, because that is the oversell invariant, and it is cheap to count."])

S(plain(K(8, "symptom pair"), "Two metrics, one conclusion", table(["Symptom A", "Symptom B", "Conclusion"], [
  ["Hold p99 flat", "Admitted fans falling", "<b>The payment path</b>, not inventory: frozen seats and a full shop"],
  ["Hold p99 rising", "409 ratio rising", "<b>A hot section</b>: contention on a few rows; check the allocation"],
  ["Map version lag rising", "Hold p99 flat", "<b>The pipeline</b>, not the claim: staleness, not incorrectness"],
  ["Oldest expired hold rising", "Sweeper up", "<b>Batch size or lock contention</b> in the sweeper"]], "bt sm")), [
 "C: Two metrics, one conclusion. Hold latency flat and admitted fans falling: that is the payment path, not inventory. Hold latency and conflicts both rising: a hot section. Map version lag rising with hold latency flat: the pipeline, which is staleness and not incorrectness. The oldest expired hold rising while the sweeper is up: batch size or lock contention in the sweeper. A pair tells you where to look first."])

S(plain(K(8, "before the day"), "A load test, a game day, and a plan to degrade", '<div class="cards c3">'
  '<div class="cd"><h3>A load test at 2×</h3><p>A million simulated fans, then two million, against a production-sized cell, with the real provider replaced by one that is slow on purpose.</p></div>'
  '<div class="cd amb"><h3>A game day</h3><p>Kill the sweeper, the controller and the provider in turn. Check each alert fires and each runbook works.</p></div>'
  '<div class="cd grn"><h3>A plan to degrade</h3><p>Shrink the rate, pause admission, say so on the page, and a kill switch that stops the line while the invariants hold.</p></div></div>' +
  line("The SLO for the opening: a fan who is admitted can complete a purchase within the checkout window, 99 % of the time. Initial target.", "a")), [
 "C: Before the day. A load test at twice the plan, a million simulated fans and then two million, against a production-sized cell, with the real provider replaced by one that is slow on purpose. A game day: kill the sweeper, the controller and the provider in turn, and check that each alert fires and each runbook works. And a plan to degrade: shrink the rate, pause admission, say so on the page, and a kill switch that stops the line while the invariants hold.",
 "C: The service level objective for the opening, as an initial target: a fan who is admitted can complete a purchase within the checkout window, ninety-nine percent of the time."])

qs("Interviewer · the second-level push", "“The metrics say all is fine and the fans are furious.”", [
 "I: The metrics say all is fine and the fans are furious.", "[pause: 2.0]"])

S(plain(K(8, "the second fix, and the honest limit"), "Trust the synthetic fan and the support queue over the dashboard", '<div class="cards c2">'
  '<div class="cd grn"><h3>The probe is the truth</h3><p>If the synthetic fan fails, the dashboard is wrong, whatever it says. The probe goes on the pager, not on a wall.</p></div>'
  '<div class="cd amb"><h3>Support as a signal</h3><p>Contacts per minute, and what they say, is a metric of last resort. It is slow and noisy, and it is the one that never lies about a real fan.</p></div></div>' +
  line("The honest limit: every indicator is a guess about what matters. Review them after every sale, against what actually hurt.", "a")), [
 "C: Trust the synthetic fan and the support queue over the dashboard. If the probe fails, the dashboard is wrong, whatever it says, and the probe goes on the pager, not on a wall. Support contacts per minute, and what they say, is a metric of last resort: slow and noisy, but it never lies about a real fan. The honest limit: every indicator is a guess about what matters, so I review them after every sale, against what actually hurt."])

say_slide("“The S-L-I is a fan completing a purchase, probed continuously. I watch seats frozen by unknown payments and the age of the oldest expired hold, because that is where this system fails silently. And there is a plan to degrade: shrink the rate, pause admission, and say so.”", [
 "V: If asked, I'd say: the S-L-I is a fan completing a purchase, probed continuously. I watch seats frozen by unknown payments and the age of the oldest expired hold, because that is where this system fails silently. And there is a plan to degrade: shrink the rate, pause admission, and say so.", "[pause: 1.0]",
 "N: That is the last challenge. Next: what would this cost to build, and who would build it?"])

# ───────────────────────── 8 · build cost (AUX) ─────────────────────────
chapter(8, "Build cost", 6, "The manager layer: people, months, buy against build", [
 "N: This chapter is marked auxiliary. It is the engineering-manager layer, optional in a Staff round.",
 "C: A ticket booking system is not one project. It is three, and the third is the one people forget to staff."], aux=True)

S(plain("Build cost · three versions", "V1, V2, V3: three releases, not one", table(["", "V1 · A sale", "V2 · A safe sale", "V3 · A big sale"], [
  ["Goal", "Sell seats correctly to a moderate crowd", "Survive a payment provider that goes quiet", "Survive a million at the door"],
  ["Scope", "One primary per event, the conditional claim, holds, orders, one provider", "The sweeper, the freeze and the reconciler, the outbox, the snapshot builder", "Waiting room, admission controller, bot controls, load test, game days"],
  ["People · time", "3 engineers · 2 months", "+2 engineers · 2 months", "+2 engineers · 3 months"],
  ["Engineer-months", "≈ 6", "≈ 10 more", "≈ 20 more"]], "bt sm") + chips("all figures illustrative", "replace with your team's own")), [
 "C: Three releases, called V-one, V-two and V-three, as in the design. V-one: a sale for a moderate crowd. One primary per event, the conditional claim, holds, orders and one provider. Three engineers for two months, about six engineer-months.",
 "C: V-two: a sale that survives a provider that goes quiet: the sweeper, the freeze and the reconciler, the outbox and the snapshot builder. Two more engineers for two months, about ten more. V-three: a sale that survives a million at the door: the waiting room, the controller, bot controls, the load test and game days. Two more engineers for three months, about twenty more. All of these are illustrative; use your own."], cls="aux")

S(plain("Build cost · buy against build", "Own the invariant. Buy the rest, at first", table(["Component", "Decision", "Why"], [
  ["Inventory and orders", "<b>build</b>", "they hold the invariant: never twice, never stuck"],
  ["Payment provider", "<b>buy</b>", "regulated, and not a differentiator"],
  ["Bot and abuse challenge", "<b>buy</b>", "an arms race with a vendor's data behind it"],
  ["Waiting room", "<b>buy for season one</b>, build when control or per-event cost justifies", "faster to a first sale; a clear exit"],
  ["Seat-map pipeline, sweeper, reconciler", "<b>build</b>", "small, and tied to the claim's semantics"]], "bt sm")), [
 "C: Buy against build. Inventory and orders I build, because they hold the invariant: never twice, never stuck. The payment provider I buy: it is regulated and not a differentiator. The bot challenge I buy: it is an arms race with a vendor's data behind it. The waiting room I could buy for the first season, to reach a first sale sooner, and build when control or the per-event cost justifies it. The map pipeline, the sweeper and the reconciler are small and tied to the claim's meaning, so I build them."], cls="aux")

S(plain("Build cost · the top risks", "Three things that sink a first season", '<div class="cards c3">'
  '<div class="cd red"><h3>A provider outage on a flagship sale</h3><p>A second provider behind the same interface, and a budget agreed in advance.</p></div>'
  '<div class="cd red"><h3>The first big on-sale with no load test</h3><p>Test at twice the plan, with a slow provider, before the calendar says so.</p></div>'
  '<div class="cd amb"><h3>A fairness rule decided late</h3><p>The promoter and product decide it weeks ahead, and the page states it.</p></div></div>' +
  line("Half the time and half the team: ship the claim with expiry, authorize-then-capture and a simple line. Never cut the invariant check.", "a")), [
 "C: Top risks. A provider outage on a flagship sale: a second provider behind the same interface, and a budget agreed in advance. The first big on-sale with no load test: test at twice the plan, with a slow provider. And a fairness rule decided late: the promoter and product decide it weeks ahead, and the page states it.",
 "V: The question I ask before saying yes: what does a wrong sale cost, who decides what is fair, and how big is the first on-sale?", "[pause: 1.0]"], cls="aux")

# ───────────────────────── 9 · recap ─────────────────────────
chapter(9, "Recap", 7, "One picture, six paths, the mistakes, the thesis", [
 "C: Four minutes to close. One picture, one sentence per path, the mistakes to avoid, and the thesis."])

S(dia("Recap", "The whole design on one baseline", "base-final", chip=chips("waiting room", "atomic claim", "hold + sweeper", "freeze + reconciler", "seat map", "probe")), [
 "C: The final picture. Fans reach a C-D-N and gateway that check an admission token. The waiting room holds the lobby and the pointer, and the controller sets its rate from shop health. The booking API makes one conditional claim on the seat database, which writes an outbox row to the event log. The sweeper frees expired holds. The snapshot builder turns the log into a versioned bitmap for the seat map. The order service freezes seats, calls the provider, and a reconciler resolves silence. A probe plays a fan, continuously."], cls="dia")

S(plain("Recap · one sentence per path", "Six paths", table(["Path", "In one sentence"], [
  ["<b>Join</b>", "A lobby and a signed place in line; one cached answer identical for everyone"],
  ["<b>Browse</b>", "An immutable layout and a versioned bitmap, one version a second, a 304 when nothing changed"],
  ["<b>Hold</b>", "One conditional update, all or nothing; a 409 with a fresh map"],
  ["<b>Pay</b>", "Freeze, authorize, sell on approval; silence is unknown, not failure"],
  ["<b>Expire</b>", "The claim treats an expired hold as free; a sweeper makes the map catch up"],
  ["<b>Release</b>", "New rows and a new layout version; a waitlist is a consumer"]], "bt")), [
 "C: Six paths, one sentence each. Join: a lobby and a signed place in line, one cached answer identical for everyone. Browse: an immutable layout and a versioned bitmap. Hold: one conditional update, all or nothing, with a four-oh-nine and a fresh map. Pay: freeze, authorize, sell on approval, and silence is unknown, not failure. Expire: the claim treats an expired hold as free, and a sweeper makes the map catch up. Release: new rows and a new layout version, and a waitlist is a consumer."])

S(plain("Recap · eight fixes", "Each one names the property it protects", table(["Challenge", "Fix", "Property"], [
  ["1 Two fans, one seat", "one conditional update; unique ticket constraint", "<b>S1</b>"],
  ["2 A hold outlives its owner", "lazy expiry + sweeper", "L1"],
  ["3 Expiry meets payment", "freeze, authorize then capture, unknown, reconciler", "<b>S2</b>"],
  ["4 A million at the door", "waiting room, controller, token at the gateway", "L3"],
  ["5 Fairness and bots", "lottery, signed tokens, verified accounts, limits", "fairness"],
  ["6 The seat map", "immutable layout, versioned bitmap, 304", "L2, L3"],
  ["7 Mid-sale changes", "new rows and layout version, consumers, cells", "extension"],
  ["8 Silent failure", "indicators, synthetic fan, load test, kill switch", "all"]], "bt sm")), [
 "C: Eight fixes, each naming the property it protects. One: a conditional update and a unique ticket constraint, for safety one. Two: lazy expiry and the sweeper, for liveness. Three: freeze, authorize then capture, unknown and the reconciler, for safety two. Four: the waiting room, the controller and the token, for the opening minute. Five: the lottery, signed tokens and verified accounts, for fairness. Six: an immutable layout and a versioned bitmap. Seven: new rows, consumers and cells, so new demand does not mean a rewrite. Eight: indicators, a synthetic fan and a load test, so the silent failures are not silent."])

S(plain("Recap · common mistakes in this round", "Ten ways this round goes wrong", '<div class="cards c2"><div class="cd red"><h3>Design</h3><ul style="font-size:17pt"><li>Check availability, then insert a booking</li><li>A database lock held through checkout</li><li>Expiry that only a sweeper provides</li><li>A live seat map read from the claims database</li><li>Strict first-come at the start</li></ul></div>'
  '<div class="cd amb"><h3>Judgment</h3><ul style="font-size:17pt"><li>A timeout treated as a decline</li><li>No idempotency key on a payment or a purchase</li><li>Never asking what fair means, or who decides</li><li>Numbers with no decision attached</li><li>No plan for the day it fails</li></ul></div></div>'), [
 "C: Ten mistakes in this round. In the design: check availability then insert. A database lock held through checkout. Expiry that only a sweeper provides. A live seat map read from the claims database. Strict first-come at the start.",
 "C: In judgment: a timeout treated as a decline. No idempotency key on a payment or a purchase. Never asking what fair means, or who decides. Numbers with no decision attached. And no plan for the day it fails."])

key("The thesis", "Fifty thousand seats, a million fans: the design is the distance between what <em>arrives</em> and what is <em>admitted</em>.", [
 "V: Fifty thousand seats, a million fans. The design is the distance between what arrives and what is admitted. A rejection system, with an atomic claim, a hold that expires, a payment that may never answer, and a way to know when any of it is broken.", "[pause: 1.2]",
 "N: Four sentences the interviewer can write down: what I built, what I traded away, what could still hurt, and what I would do next. That close is often the whole debrief."])
