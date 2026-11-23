from dsl import *
P = "[+]"

chapter(0, "Cold open", -1, "A live map of a moving fleet, and its history", [
 "C: A live map of two million vehicles sounds like one database of positions. It's asked at autonomous-driving and delivery companies and at Google, because it's really two products off one stream, and it's built from three questions you may already know: event counting, nearby drivers, and a device fleet."])

qs("Interviewer · the prompt", "“Millions of vehicles report their position and health every few seconds. Design the system behind a live fleet map for operations, plus a history that can be audited and replayed.”", [
 "I: Millions of vehicles report their position and health every few seconds. Design the system behind a live fleet map for operations, plus a history that can be audited and replayed.", "[pause: 1.5]"])

S(dia("Why it is harder than it looks", "Two products from one stream", "tension", chip=chips("latest, overwrite", "everything, append", "never one table")), [
 "C: The hook. The live map asks where each vehicle is now: overwrite, in memory, by place, two seconds fresh, and losing a point is fine.",
 "C: The history asks where it was every two seconds for two years: append, in columns, complete, minutes late is fine. One table for both is slow for the first and wrong for the second."])

S(plain("Before the design", "What this question grades", table(["Axis", "Weak signal", "Strong signal"], [
  ["<b>Requirements</b>", "“Store positions and show a map”", "Separates the live view from the history, and asks about tunnels"],
  ["<b>Composition</b>", "Designs everything from scratch", "Names the seams: SD-03’s split, SD-39’s index, SD-29’s devices"],
  ["<b>Correctness</b>", "Latest arrival wins", "Per-vehicle order and sequence numbers; latest by seq"],
  ["<b>Depth</b>", "“Partition by region”", "Key the log by vehicle; index by cell; thin by zoom"],
  ["<b>Operations</b>", "Consumer lag", "Position age on the map, from canary vehicles"]], "bt xs sig") +
  grade("This question rewards composition: say which known part you are reusing, and where the seam is.")), [
 "N: Five axes.", P, "N: Requirements: the strong answer separates the live view from the history first, and asks about tunnels.", P,
 "N: Composition: it doesn't design everything from scratch. It names the seams: question three's split into a hot and a cold path, question thirty-nine's index, question twenty-nine's devices.", P,
 "N: Correctness: not latest arrival wins, but per-vehicle order and sequence numbers.", P,
 "N: Depth: key the log by vehicle, index by cell, thin by zoom.", P, "N: Operations: the age of a position on the map, measured from canary vehicles.", P,
 "C: And the rule for this round: say which known part I'm reusing, and where the seam is."])

key("The thesis", "One log keyed by <em>vehicle</em>, read twice: an <em>overwrite</em> view by cell for the map, and an <em>append</em> history by vehicle for replay. <em>Sequence numbers</em> decide what is newer; <em>lanes</em> decide what goes first.", [
 "V: One log keyed by vehicle, read twice: an overwrite view by cell for the map, and an append history by vehicle for replay. Sequence numbers decide what's newer; lanes decide what goes first.", "[pause: 1.0]"])

S(dia("The parts I am reusing", "Three earlier questions, and where each one sits", "seams"), [
 P, "C: Here's the shape I'm heading for, with the seams marked. It's not a new invention; it's three earlier questions put together.", P,
 "C: The vehicle uplink is question twenty-nine's device agent: identity, a buffer, backoff.", P,
 "C: The gateway is the same broker, with mutual T-L-S.", P,
 "C: The state updater is question three's live path: a stream job over one log, deduplicating by an I-D, here a sequence number.", P,
 "C: The live store is question thirty-nine's index: H-three cells, overwrite-only.", P,
 "C: And the history lake is question three's cold path, laid out for a different query."], cls="dia")

S(plain("The order I will follow", "Scope, numbers, theory, a simple design, then I break it",
  '<div class="ribbon" style="margin-top:6pt">' + "".join(f"<span>{x}</span>" for x in STAGES) + '</div>' +
  cards(("", "First", "Requirements, the numbers, and theory that is mostly borrowed: one log two views, sequences, cells, lanes."),
        ("grn", "Then", "The interfaces and data, three versions on one picture, every path, three containers one level down."),
        ("red", "Most of the time", "Six challenges, from a tunnel exit to a map that is stale while everything is green."), cols=3)), [
 "C: The order I'll follow.", P,
 "C: First, requirements, the numbers, and theory that's mostly borrowed: one log with two views, sequence numbers, cells and lanes.", P,
 "C: Then the interfaces and the data, three versions on one picture, every path, and three containers opened up.", P,
 "C: Then six challenges, from a tunnel exit to a map that's stale while everything is green."])

chapter(1, "Requirements and scope", 0, "The scale first, then five questions", ["C: The scale first, then five questions."])

S(plain("Requirements · the scale line", "Three numbers every estimate starts from", '<div class="tiles" style="--n:3">'
  '<div class="tile blue"><b>10¹² · 52 TB</b><span>positions a month · stored compressed</span></div>'
  '<div class="tile"><b>2 M · 2 years</b><span>vehicles · history kept</span></div>'
  '<div class="tile red"><b>1 M/s</b><span>at rush hour; 100,000 flush after an outage</span></div></div>' +
  line("Every number later starts from one of these three.", "a")), [
 "C: The scale.", P, "C: About a trillion positions a month, fifty-two terabytes once compressed.", P,
 "C: Two million vehicles, with two years of history kept for audits and replay.", P,
 "C: And the peak: a million positions a second at rush hour, and, after a city's cellular network comes back, a hundred thousand vehicles flushing three minutes of buffer at once.", P,
 "C: Every number later starts from these."])

def clar(n, q, a, ask, ans, so):
    S(f'<div class="who">Clarifying question {n} of 5</div><div class="qq">{q}</div><div class="ans">{a}</div>',
      ["C: " + ask, P, "I: " + ans, "C: " + so], cls="qs")
clar(1, "How fresh must the map be?", "Within 2 seconds of us receiving a position.",
     "How fresh must the map be?", "Within two seconds of us receiving a position.",
     "Two seconds rules out the history store for the map. It needs its own view.")
clar(2, "What happens in a tunnel?", "Vehicles lose coverage for minutes and buffer locally.",
     "What happens when a vehicle loses coverage?", "It buffers locally, for minutes in tunnels, sometimes hours, and flushes when it reconnects.",
     "So old positions arrive after new ones. Order has to come from the vehicle, not from arrival.")
clar(3, "What must history support?", "Two years; audits ask for one vehicle's exact window; ML reads whole days.",
     "What must the history support?", "Two years of it. Audits ask for one vehicle's exact window; machine learning reads whole days.",
     "Two access patterns: a narrow one for audits and a wide one for training. The layout must serve both.")
clar(4, "Is anything urgent?", "Safety events: a hard brake or a crash must reach dispatch within a second.",
     "Is anything more urgent than a position?", "Safety events: a hard brake or a crash must reach dispatch within a second.",
     "Then safety events never wait behind a backlog of positions, on the vehicle or on the server.")
clar(5, "Who watches the map?", "About 5,000 operators at once, at every zoom.",
     "Who watches the map?", "About five thousand operators at once, at every zoom level.",
     "At city zoom nobody can see two hundred thousand dots. The map must show counts far out and vehicles close in.")

S(plain("Requirements · functional", "Four things the system must do", cards(
  ("", "FR1 · Report", "Accept positions every 2 s and health every 30 s from every vehicle, including buffered backlogs."),
  ("grn", "FR2 · Watch", "Show operators a live map of any area at any zoom, within 2 s."),
  ("amb", "FR3 · Replay", "Return one vehicle’s exact positions for any window in two years."),
  ("red", "FR4 · Alert", "Deliver safety events to dispatch within 1 s."))), [
 "C: Four functional requirements.", P, "C: One, report: positions every two seconds and health every thirty, including buffered backlogs.", P,
 "C: Two, watch: a live map of any area at any zoom, within two seconds.", P,
 "C: Three, replay: one vehicle's exact positions for any window in two years.", P, "C: Four, alert: safety events to dispatch within a second."])

S(plain("Requirements · non-functional", "The numbers, and what each is for", '<p class="chips">all initial targets</p><div class="tiles" style="--n:4">'
  '<div class="tile blue"><b>2 s</b><span>receipt to map, p99</span></div>'
  '<div class="tile red"><b>1 s</b><span>safety event to dispatch</span></div>'
  '<div class="tile"><b>100 %</b><span>of received positions in history</span></div>'
  '<div class="tile blue"><b>10 s</b><span>one vehicle-hour replay</span></div></div>' +
  line("The map may drop a point; the history may not.", "a")), [
 "C: The numbers.", P, "C: Two seconds from receipt to the map.", P, "C: One second for a safety event.", P,
 "C: Every received position in the history.", P, "C: Ten seconds to replay one vehicle's hour.", P,
 "C: The map may drop a point. The history may not."])

S(plain("Requirements · scope", "In, and out on purpose", cards(
  ("grn", "In scope", "The uplink on the vehicle, ingest, the live map, history, replay, safety alerts."),
  ("red", "Out, on purpose", "Raw camera and lidar logs (SD-98’s input), routing, dispatching jobs, the fleet’s control plane (SD-29).")) +
  line("The control plane and this data plane share the gateway and the identity, not the stores.", "")), [
 P, "C: In scope: the uplink on the vehicle, ingest, the live map, history, replay and safety alerts.", P,
 "C: Out, on purpose: raw camera and lidar logs, which are question ninety-eight's input; routing; dispatching jobs; and the control plane, question twenty-nine.", P,
 "C: The control plane and this data plane share the gateway and the identity, not the stores."])

S(dia("Architecture · C4 level 1 · context", "The system in its context", "c4-context"), [
 "C: The context.", P, "C: Vehicles send positions and health.", P, "C: The system, one box.", P,
 "C: Operators watch the live map.", P, "C: Dispatch receives safety events.", P, "C: Analysts and machine learning replay and export history."], cls="dia")

key("The core", "The core is three things: a <em>log keyed by vehicle</em>, an <em>overwrite view by cell</em>, and an <em>append history by vehicle</em>.", [
 "V: The core is three things. A log keyed by vehicle. An overwrite view by cell. And an append history by vehicle.", "[pause: 0.8]"])

chapter(2, "Estimates", 1, "Each number from the scale line, with what it decides", ["C: Numbers, from the scale line. Illustrative."])

S(plain("Estimates · ingest and storage", "Three hundred megabytes a second in; fifty terabytes a month kept", table(["Number", "From", "Arithmetic", "Decides"], [
  ["Ingest", "rush hour", "1 M/s × 300 B = <b>300 MB/s</b>; × 3 replicas = 900 MB/s", "512 partitions, keyed by vehicle"],
  ["A month", "average 400 k/s", "4 × 10⁵ × 2.6 × 10⁶ s ≈ <b>10¹² positions</b>", "History in columns"],
  ["Stored", "10¹² × ~50 B", "≈ <b>52 TB a month</b>; × 24 ≈ 1.25 PB", "Object storage, Parquet"],
  ["Live state", "2 M vehicles", "2 M × 200 B ≈ <b>400 MB</b>", "Memory, per city"]])), [
 "C: Ingest and storage.", P, "C: A million positions a second at three hundred bytes is three hundred megabytes a second, nine hundred with replication. Five hundred and twelve partitions, keyed by vehicle.", P,
 "C: At an average of four hundred thousand a second, a month is about a trillion positions.", P,
 "C: At about fifty bytes each in compressed columns, fifty-two terabytes a month, one and a quarter petabytes for two years. Object storage.", P,
 "C: And the live state: two million vehicles at two hundred bytes is four hundred megabytes. Memory."])

S(plain("Estimates · the map and the flush", "Five thousand viewers, and a city coming back online", table(["Number", "From", "Arithmetic", "Decides"], [
  ["City zoom", "5,000 viewers", "~100 res-7 cells as counts per viewer per second", "Counts, not dots"],
  ["Street zoom", "downtown", "~2,000 vehicles in view; ~400 move each second", "Deltas per cell"],
  ["The flush", "100,000 vehicles", "× 90 buffered = <b>9 M messages</b>; spread over ~1 min ≈ 150 k/s", "Latest first; backfill capped"],
  ["Safety", "fleet-wide", "~10 events a second", "Its own lane and topic"]])), [
 "C: The map and the flush.", P, "C: At city zoom, a viewer sees about a hundred resolution-seven cells as counts each second. Counts, not dots.", P,
 "C: At street zoom downtown, about two thousand vehicles, four hundred of them moving each second: send the deltas.", P,
 "C: The flush: a hundred thousand vehicles times ninety buffered positions is nine million messages; spread over a minute, a hundred and fifty thousand a second on top of a million. Latest first, backfill capped.", P,
 "C: And safety: about ten events a second fleet-wide, in their own lane."])

S(plain("Estimates · the vehicle’s buffer", "Six hours on the vehicle, and what it costs", table(["Number", "From", "Arithmetic", "Decides"], [
  ["Positions an hour", "2 s cadence", "1,800 an hour; 6 h = 10,800", "A ring buffer in flash"],
  ["Bytes", "~300 B each", "10,800 × 300 B ≈ <b>3.2 MB</b>", "Cheap: keep six hours"],
  ["Flash wear", "1 write per fix", "batched per 30 s: 120 writes an hour", "Write in pages, not per fix"]])), [
 "C: The buffer on the vehicle, because half the design depends on it.", P,
 "C: Every two seconds is eighteen hundred positions an hour; six hours is about eleven thousand.", P,
 "C: At three hundred bytes each, about three megabytes. Cheap enough to keep six hours.", P,
 "C: But flash wears out, so positions are written in pages every thirty seconds, a hundred and twenty writes an hour, not one per fix."])

S(dia("Estimates · the freshness budget", "Two seconds, from receipt to the map", "budget", chip=chips("initial target", "p99")), [
 "C: The freshness budget, from the moment we receive a position. A third of a second through the gateway and the log. A third through the state updater. Up to a second waiting for the map's push tick. About one point six of two seconds.",
 "C: Sampling on the vehicle adds up to two seconds before that, which the operator sees as the dot's own age."], cls="dia")

chapter(3, "Theory", 2, "Two views of one stream", ["C: The theory: five mechanisms, most of them borrowed, then the options."])

S(plain("Theory · what it is", "Two views of one ordered stream", cards(
  ("", "It is", "Keeping, from one per-vehicle stream, a latest-state view by place and a complete history by vehicle."),
  ("amb", "Not ride matching", "SD-39 claims drivers; here nothing is claimed, only shown."),
  ("amb", "Not metrics", "Positions are events with identity, not counters by label."),
  ("amb", "Not the control plane", "SD-29 changes devices; this only listens to them."), cols=2)), [
 "C: What it is.", P, "V: Keeping, from one per-vehicle stream, a latest-state view by place and a complete history by vehicle.", P,
 "C: Not ride matching: nothing is claimed here, only shown.", P, "C: Not metrics: positions are events with identity, not counters.", P,
 "C: And not the control plane: that changes devices; this only listens."])

S(plain("Theory · properties", "Safety and liveness, stated separately", cards(
  ("red", "S1 · never backwards", "The map never moves a vehicle to an older position than it has shown."),
  ("red", "S2 · nothing lost", "Every received position is in history, exactly once."),
  ("grn", "L1 · fresh", "A received position is on the map within 2 s."),
  ("grn", "L2 · urgent first", "A safety event reaches dispatch within 1 s, even during a flush."), cols=2)), [
 "C: Safety.", P, "V: S-one: the map never moves a vehicle backwards to an older position than it has shown.", P,
 "V: S-two: every received position is in history, exactly once.", P, "C: Liveness. L-one: on the map within two seconds.", P,
 "C: L-two: a safety event reaches dispatch within a second, even during a flush."])

def mech(n, name, prot, how, rules, cost, say):
    S(plain(f"Theory · mechanism M{n}", name, cards(("", "Protects", prot), ("grn", "How it works", how), ("red", "Rules out", rules), ("amb", "Costs", cost), cols=2)), say)

mech(1, "One log, two views (from SD-03)", "L1, S2.", "Every position is appended to one log; one consumer overwrites a latest view, another appends history.",
     "One store that is slow for the map and lossy for history.", "Two consumers; history minutes behind the map.", [
 "C: Mechanism one, borrowed from question three: one log, two views.", P, "C: It protects freshness and completeness at once.", P,
 "C: Every position is appended once. One consumer overwrites a latest view; another appends history.", P,
 "C: It rules out one store that's slow for the map and lossy for history.", P, "C: It costs two consumers, and a history a few minutes behind the map."])

S(dia("Theory · mechanism M1 at work", "The same positions, two fates", "seq-th-split"), [
 "C: Mechanism one at protocol level.", P, "C: The lake receives every position, appended in five-minute files.", P,
 "C: The state updater receives the same positions.", P, "C: It keeps only the newest per vehicle.", P,
 "C: And overwrites the live store: latest wins.", P, "C: In the lake nothing is ever overwritten."], cls="dia")

mech(2, "Per-vehicle order and sequence numbers (from SD-29, SD-39)", "S1, S2.", "The vehicle numbers every message; the log is keyed by vehicle, so its messages stay in order; views compare sequence numbers, never arrival.",
     "A buffered old fix overwriting a new one; duplicates after a resend.", "A counter in the vehicle’s flash.", [
 "C: Mechanism two, borrowed from twenty-nine and thirty-nine: per-vehicle order and sequence numbers.", P, "C: It protects S-one and S-two.", P,
 "C: The vehicle numbers every message from a counter in flash. The log is keyed by vehicle, so one vehicle's messages stay in order on one partition. Views compare sequence numbers, never arrival times.", P,
 "C: It rules out a buffered old position overwriting a new one, and duplicates after a resend.", P, "C: It costs a counter that survives reboots."])

mech(3, "Cells at several resolutions (from SD-39)", "L1 for the map.", "Index vehicles by H3 resolution 9; keep counts at resolutions 6 and 7; a viewport picks the resolution from its zoom.",
     "Sending 200,000 dots to a city-zoom map; a hot cell holding thousands.", "A count to maintain per coarse cell.", [
 "C: Mechanism three, from thirty-nine: cells, at several resolutions.", P, "C: It protects map freshness.", P,
 "C: Vehicles are indexed by resolution-nine cells, with counts kept at resolutions six and seven. A viewport picks the resolution from its zoom.", P,
 "C: It rules out sending two hundred thousand dots to a city-zoom map.", P, "C: It costs a count per coarse cell, updated with every move."])

mech(4, "Lanes and backpressure (from SD-29)", "L2, L1.", "The vehicle sends safety events first, then its latest position, then backfill oldest-first at a capped rate.",
     "A three-minute backlog delaying the present; safety events queued behind history.", "Backfill reaches history a little later.", [
 "C: Mechanism four, from twenty-nine: lanes and backpressure.", P, "C: It protects L-two and L-one.", P,
 "C: On reconnect, the vehicle sends safety events first, then its latest position, then the backfill, oldest first, at a capped rate.", P,
 "C: It rules out a three-minute backlog delaying the present, and safety events queued behind history.", P, "C: It costs a little delay for the backfill."])

mech(5, "Subscriptions by cell", "L1 at 5,000 viewers.", "A viewport subscribes to the cells it covers; each tick the server pushes only what changed in them.",
     "5,000 clients polling the hottest cells every second.", "Subscription state per viewer; a snapshot on every pan.", [
 "C: Mechanism five: subscriptions by cell.", P, "C: It protects freshness for five thousand viewers.", P,
 "C: A viewport subscribes to the cells it covers, and each tick the server pushes only what changed in them.", P,
 "C: It rules out five thousand clients polling the hottest cells every second.", P, "C: It costs subscription state per viewer, and a snapshot on every pan."])

S(plain("Theory · the seams", "What each earlier question contributes, and what changes here", table(["Question", "Reused part", "What changes here"], [
  ["SD-03 event counting", "one log, a hot and a cold path; dedup by an ID", "the hot path overwrites instead of counting"],
  ["SD-39 ride matching", "the in-memory H3 index; soft state", "resolution 9, counts at 6 and 7, subscribers"],
  ["SD-29 device fleet", "identity, the gateway, store-and-forward, backoff", "lanes for data: safety, latest, backfill"],
  ["SD-98 replay", "a history pinned by snapshot", "laid out for one vehicle, not for scenarios"]], "bt xs mx")), [
 "C: Before the options, the seams, explicitly.", P,
 "C: From question three: one log with a hot path and a cold path, and dedup by an I-D. Here the hot path overwrites instead of counting.", P,
 "C: From question thirty-nine: the in-memory H-three index and soft state. Here at resolution nine, with counts at six and seven, and subscribers.", P,
 "C: From question twenty-nine: identity, the gateway, store-and-forward and backoff. Here the backoff becomes lanes for data.", P,
 "C: And from question ninety-eight: a history pinned by snapshot, laid out here for one vehicle instead of for scenarios. Saying this out loud in the room is the composition signal."])

S(plain("Theory · the options", "Five ways to build it, one picked", table(["Approach", "Fresh map", "Complete history", "Fails when"], [
  ["A · one database table of positions", "no", "slowly", "1 M writes a second; a bounding-box scan per viewer"],
  ["B · log + lake only", "no", "yes", "the map is minutes behind"],
  ["C · a live store only", "yes", "no", "no audit, no replay"],
  ["D · a log keyed by geo cell", "yes", "yes", "hot partitions; vehicles lose order as they move"],
  ("pick", ["<b>E · log by vehicle → live view by cell + history by vehicle; lanes; subscriptions</b>", "yes", "yes", "two consumers; a vehicle agent to build"])], "bt xs mx") +
  line("Key by what must stay in order; index by what you query.", "a")), [
 "C: Five ways.", P, "C: A, one database table: a million writes a second and a bounding-box scan per viewer.", P,
 "C: B, a log and a lake only: the map is minutes behind.", P, "C: C, a live store only: no audit, no replay.", P,
 "C: D, a log keyed by geo cell: hot partitions downtown, and a vehicle crossing a cell boundary changes partitions and loses its order.", P,
 "C: E, which I pick: a log by vehicle, read into a live view by cell and a history by vehicle, with lanes and subscriptions.", P,
 "V: Key by what must stay in order. Index by what you query.", "[pause: 0.8]"])

S(plain("Theory · the failure catalogue", "What will go wrong, in the order I'll take it", table(["#", "Failure", "At risk"], [
  ["1", "A vehicle leaves a tunnel with three minutes of buffer", "S1, S2"],
  ["2", "Downtown at six: 2,000 vehicles in one view", "L1"],
  ["3", "5,000 operators watching at once", "L1"],
  ["4", "A city’s network recovers: 100,000 vehicles flush", "L1, L2"],
  ["5", "An audit wants one vehicle’s hour, exactly", "S2"],
  ["6", "The map is 40 seconds stale and nothing says so", "all"]], "bt sm")), [
 "C: The failure catalogue.", P, "C: One: a vehicle leaves a tunnel with three minutes of buffer.", P, "C: Two: downtown at six, two thousand vehicles in one view.", P,
 "C: Three: five thousand operators watching at once.", P, "C: Four: a city's network recovers, and a hundred thousand vehicles flush.", P,
 "C: Five: an audit wants one vehicle's hour, exactly.", P, "C: Six: the map is forty seconds stale, and nothing says so."])
