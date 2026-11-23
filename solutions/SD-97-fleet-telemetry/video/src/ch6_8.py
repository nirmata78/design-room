from dsl import *
from stack import REJ
P = "[+]"
B = lambda x: f'<span class="bad">{x}</span>'
K = lambda n, t: f"Challenge {n} of 6 · {t}"

chapter(6, "Bridge", 5, "It works. Where does it break first?", ["V: It works. The question now is where it breaks first.", "[pause: 1.0]"])
S(dia("Challenge map", "Six challenges, five places on the same picture", "map", chip=chips("each fix creates the next question")), [
 P, "C: Version three, with the places it breaks.", P, "C: The state updater: a vehicle leaving a tunnel. Challenge one.", P,
 "C: The log and its key, under a dense downtown. Challenge two.", P, "C: The map A-P-I, with five thousand viewers. Challenge three.", P,
 "C: The uplink, when a whole city reconnects. Challenge four.", P, "C: And the lake, when an audit wants one hour exactly. Challenge five. Then: how would we know the map is stale?"], cls="dia")

chapter(7, "Challenges", 5, "Six ways to break it, and what survives", ["C: Six challenges, each the same way: the question, the naive answer, a case with numbers, where it breaks inside the container, the fix one level down, then the push on the fix itself, and what I would say in the room."])

# ── 1
subchapter("7.1", "Challenge 1: Out of the tunnel", ["N: Challenge one is the crux: old data arriving after new data."])
qs("Interviewer · challenge 1 of 6", "“A vehicle leaves a tunnel with three minutes of buffered positions. What does the map show, and what does the history get?”", [
 "I: A vehicle leaves a tunnel with three minutes of buffered positions. What does the map show, and what does the history get?", "[pause: 2.0]"])
S(dia(K(1, "a backlog"), "Which position is the vehicle’s now?", "ch1-attack", q=True, red=True,
      extra=strip(("case", "Naive answer", "“Write each position to the map as it arrives.”"),
                  ("case", "Break", "The live writer takes arrival order: the car jumps back into the tunnel and replays three minutes."))), [
 P, "C: Inside the state updater.", P, "C: The live writer is marked.", P, "C: The naive answer: write each position to the map as it arrives.", P,
 "C: Then the backlog arrives after the fresh position, and the car on the map jumps back into the tunnel and drives its last three minutes again."], cls="dia")
S(trace(K(1, "the trace"), "A car that drives backwards", [
  ("18:00:00", "v-311 exits the tunnel; sends its current position, seq 9,402"),
  ("18:00:01", "then 90 buffered positions, seq 9,312 – 9,401"),
  ("18:00:01", B("arrival order: the map moves the car 2 km back, into the tunnel")),
  ("18:00:04", B("an operator dispatches help to a car that is fine"))],
  hedge=("And the history", "It needs all 90, in their own minutes, exactly once.")), [
 "C: The trace.", P, "C: The car exits the tunnel and sends its current position, sequence nine four oh two.", P,
 "C: Then ninety buffered positions, nine three one two to nine four oh one.", P, "C: In arrival order, the map moves the car two kilometres back into the tunnel.", P,
 "C: An operator dispatches help to a car that's fine.", P, "C: And the history needs all ninety, in their own minutes, exactly once."])
S(dia(K(1, "the fix"), "The sequence decides: live takes newer, history takes all", "ch1-fix",
      extra=strip(("fixb", "Mechanism", "Keyed state holds the last seq per vehicle; a position with seq ≤ last goes to history only; the live writer overwrites only with a newer seq. The lake dedups by (vehicle, epoch, seq)."),
                  ("whyb", "Covers, and does not", "Backlogs, resends and reordering. Not a vehicle whose counter reset without a new epoch: a firmware bug, caught by the census of SD-29.")) + rejl(*REJ(1))), [
 P, "C: The fix.", P, "C: The sequence filter.", P, "C: And the live writer.", P,
 "C: One level down. Keyed state holds the last sequence number per vehicle. A position with a sequence at or below it goes to the history side output only. The live writer overwrites only with a newer sequence. And the lake deduplicates by vehicle, epoch and sequence, so a resend is one row.", P,
 "C: It covers backlogs, resends and reordering. Not a vehicle whose counter reset without a new epoch; that's a firmware bug, and question twenty-nine's census catches it.", P,
 "C: Rejected: writing every arriving position to the live store. A three-minute-old fix overwrites the position from one second ago."], cls="dia")
S(plain(K(1, "why not timestamps"), "The vehicle’s clock is not the vehicle’s order", table(["Ordering by", "Fails when"], [
  ["Arrival time", "a backlog arrives after the present"],
  ["The vehicle’s timestamp", "the clock jumps after a GPS fix or a reboot; two fixes share a millisecond"],
  ["Server receipt time", "the same as arrival"],
  ("pick", ["<b>(epoch, seq) from flash</b>", "never: incremented once per message, survives reboots"])], "bt sm")), [
 "C: Why not just use timestamps?", P, "C: Arrival time fails as soon as a backlog arrives after the present.", P,
 "C: The vehicle's own timestamp fails when its clock jumps, after a G-P-S fix corrects it or after a reboot, and two fixes can share a millisecond.", P,
 "C: Server receipt time is arrival time again.", P,
 "C: A sequence number and an epoch, kept in flash, never fail that way: incremented once per message, surviving reboots. Time is displayed; the sequence decides."])

S(dia(K(1, "sequence"), "Latest first; backfill to history", "seq-ch1-tunnel"), [
 "C: As a sequence.", P, "C: Leaving the tunnel with ninety positions buffered.", P, "C: The latest lane goes first: nine four oh two.", P,
 "C: The car jumps forward to where it really is.", P, "C: Then the backfill.", P, "C: Older than nine four oh two: not live.", P,
 "C: All ninety into history, each in its own minute."], cls="dia")
qs("Interviewer · the second-level push", "“The updater restarts and loses its state.”", ["I: The updater restarts and loses its state.", "[pause: 1.5]"])
S(plain(K(1, "the second fix"), "State is checkpointed; the store is the backstop", cards(
  ("grn", "Restored", "The last-seq state is checkpointed with the Kafka offsets: a restart resumes exactly."),
  ("amb", "Belt and braces", "The live store also compares seq on write, so even an empty filter cannot move a car backwards."), cols=2)), [
 P, "C: The last-sequence state is checkpointed with the Kafka offsets, so a restart resumes exactly where it was.", P,
 "C: And the live store compares sequence numbers on write too. Even an empty filter can't move a car backwards: S-one is enforced in two places."])
say_slide("“Order comes from the vehicle, not from arrival. Every message carries a sequence number; the live view overwrites only with a newer one, and the history takes everything, deduplicated by vehicle and sequence. The vehicle sends its latest position before its backlog.”", [
 "V: If asked, I'd say: order comes from the vehicle, not from arrival. Every message carries a sequence number; the live view overwrites only with a newer one, and the history takes everything, deduplicated by vehicle and sequence. And the vehicle sends its latest position before its backlog.", "[pause: 1.0]",
 "N: That fix creates the next question: order per vehicle needs the log keyed by vehicle. What does that do downtown?"])

# ── 2
subchapter("7.2", "Challenge 2: Downtown at six", ["N: Challenge two: density, on the log and on the map."])
qs("Interviewer · challenge 2 of 6", "“Downtown at six there are 2,000 vehicles in one operator's view. Why not key the log by geo cell? And what does the operator actually see?”", [
 "I: Downtown at six there are two thousand vehicles in one operator's view. Why not key the log by geo cell? And what does the operator actually see?", "[pause: 2.0]"])
S(dia(K(2, "density"), "What does a city-zoom map send?", "ch2-attack", q=True, red=True,
      extra=strip(("case", "Naive answer", "“Key by cell so the map reads one partition; send every vehicle in view.”"),
                  ("case", "Break", "The aggregator sends every dot: 200,000 at city zoom; and a cell-keyed log puts downtown on one partition."))), [
 P, "C: Inside the map A-P-I.", P, "C: The aggregator is marked.", P,
 "C: The naive answer: key the log by cell, so the map reads one partition, and send every vehicle in view.", P,
 "C: Then a city-zoom map gets two hundred thousand dots a second, and a cell-keyed log puts all of downtown on one partition."], cls="dia")
S(trace(K(2, "the trace"), "One hot partition, one unreadable map", [
  ("18:00", "log keyed by cell: downtown’s cell partition takes 40 % of all traffic"),
  ("18:00", B("one consumer lags; the whole downtown map is 30 s behind")),
  ("18:00", "v-311 crosses into the next cell: its next messages land on another partition"),
  ("18:00", B("two consumers race on one vehicle; it flickers between positions"))],
  hedge=("Two errors", "A key that concentrates load, and a key that splits a vehicle’s order.")), [
 "C: The trace.", P, "C: With the log keyed by cell, downtown's partition takes forty percent of the traffic.", P,
 "C: One consumer lags, and all of downtown is thirty seconds behind.", P,
 "C: A car crosses into the next cell, and its next messages land on another partition.", P,
 "C: Two consumers race on one car, and it flickers.", P, "C: A key that concentrates load, and a key that splits a vehicle's order."])
S(dia(K(2, "the fix"), "Key by vehicle; index by cell; show by zoom", "ch2-fix",
      extra=strip(("fixb", "Mechanism", "The log stays keyed by vehicle (even load, per-vehicle order). The live store indexes res-9 cells and keeps res-6/7 counts. A viewport at city zoom gets ~100 counts; at street zoom, vehicles."),
                  ("whyb", "Covers, and does not", "Hot areas and unreadable maps. Not 2,000 vehicles at street zoom in one block: those are shown, clustered client-side.")) + rejl(*REJ(2))), [
 P, "C: The fix.", P, "C: The aggregator.", P,
 "C: One level down. The log stays keyed by vehicle, for even load and per-vehicle order. The live store indexes resolution-nine cells and keeps counts at resolutions six and seven. A viewport at city zoom gets about a hundred counts a second; zoomed in to the street, it gets vehicles.", P,
 "C: It covers hot areas and unreadable maps. Not two thousand vehicles in one block at street zoom; those are sent, and the browser clusters them.", P,
 "C: Rejected: keying the log by geo cell. A stadium's cell becomes one hot partition, and vehicles lose their order as they move."], cls="dia")
S(plain(K(2, "zoom to resolution"), "What a viewport receives, by zoom", table(["Zoom", "Resolution", "Cells in view", "Sent"], [
  ["City (10)", "6", "~30", "counts"],
  ["District (12)", "7", "~100", "counts"],
  ["Neighbourhood (14)", "9", "~200", "vehicles, clustered by the browser"],
  ["Street (16+)", "9 or 10", "~50", "vehicles"]], "bt sm")), [
 "C: Concretely, what a viewport receives by zoom.", P, "C: At city zoom, resolution six: about thirty cells, sent as counts.", P,
 "C: At district zoom, resolution seven: about a hundred cells, still counts.", P,
 "C: At neighbourhood zoom, resolution nine: about two hundred cells of vehicles, which the browser clusters.", P,
 "C: At street zoom, resolution nine or ten: about fifty cells, every vehicle. The payload stays roughly the same size at every zoom."])

qs("Interviewer · the second-level push", "“A stadium empties: 3,000 vehicles in one resolution-9 cell.”", ["I: A stadium empties: three thousand vehicles in one resolution-nine cell.", "[pause: 1.5]"])
S(plain(K(2, "the second fix"), "Finer where crowded, as in SD-39", cards(
  ("grn", "Split the cell", "Over 300 vehicles, the cell is indexed at resolution 10 as well; street zoom reads the finer cells."),
  ("amb", "The log does not care", "The log is keyed by vehicle; 3,000 vehicles are 3,000 keys spread over 512 partitions."), cols=2)), [
 P, "C: The live store splits the cell, exactly as in question thirty-nine: over three hundred vehicles, it's indexed at resolution ten as well, and street zoom reads the finer cells.", P,
 "C: And the log doesn't care: three thousand vehicles are three thousand keys spread over five hundred and twelve partitions. That's the point of keying by vehicle."])
say_slide("“Key by what must stay in order, index by what you query. The log is keyed by vehicle, so load is even and each vehicle stays in order; the live store indexes cells, splits hot ones, and keeps coarse counts so a zoomed-out map gets a hundred numbers, not two hundred thousand dots.”", [
 "V: If asked, I'd say: key by what must stay in order, and index by what you query. The log is keyed by vehicle, so load is even and each vehicle stays in order. The live store indexes cells, splits hot ones, and keeps coarse counts, so a zoomed-out map gets a hundred numbers, not two hundred thousand dots.", "[pause: 1.0]",
 "N: That fix creates the next question: five thousand people are looking at once."])

# ── 3
subchapter("7.3", "Challenge 3: Five thousand viewers", ["N: Challenge three: fan-out to the people watching."])
qs("Interviewer · challenge 3 of 6", "“Five thousand operators keep the map open all day. How does each one stay within two seconds without melting the live store?”", [
 "I: Five thousand operators keep the map open all day. How does each one stay within two seconds without melting the live store?", "[pause: 2.0]"])
S(dia(K(3, "fan-out"), "Pull every second, or be told?", "ch3-attack", q=True, red=True,
      extra=strip(("case", "Naive answer", "“Each browser polls its bounding box every second.”"),
                  ("case", "Break", "The pusher has nothing to push: 5,000 polls a second scan the hottest cells."))), [
 P, "C: Inside the map A-P-I.", P, "C: The pusher is marked.", P, "C: The naive answer: each browser polls its bounding box every second.", P,
 "C: Then there's nothing to push: five thousand polls a second scan the hottest cells, mostly to find nothing changed."], cls="dia")
S(trace(K(3, "the trace"), "Five thousand scans a second, mostly of nothing", [
  ("09:00", "5,000 operators open the map; 3,000 of them on the same three cities"),
  ("09:00", "each polls a bounding box every second: 5,000 scans/s"),
  ("09:00", B("the same downtown cells scanned 2,000 times a second")),
  ("09:05", B("live store CPU at 90 %; updates to it slow; the map falls behind"))],
  hedge=("The waste", "At night most cells don’t change in a second; the polls still run.")), [
 "C: The trace.", P, "C: Five thousand operators open the map, three thousand on the same three cities.", P,
 "C: Each polls a bounding box every second.", P, "C: The same downtown cells are scanned two thousand times a second.", P,
 "C: The live store's C-P-U climbs, its own updates slow, and the map falls behind.", P,
 "C: And at night most cells don't change in a second; the polls still run."])
S(dia(K(3, "the fix"), "Viewports subscribe to cells; the server pushes changes", "ch3-fix",
      extra=strip(("fixb", "Mechanism", "A viewport becomes a set of cells at its zoom’s resolution; the map pod subscribes to their change feed; each second it pushes only the changes. A pan subscribes new cells and sends their snapshot."),
                  ("whyb", "Covers, and does not", "Any number of viewers per cell: one feed, many sockets. Not a single viewer panning wildly: that costs snapshots.")) + rejl(*REJ(3))), [
 P, "C: The fix.", P, "C: Subscriptions.", P, "C: And the pusher.", P,
 "C: One level down. A viewport becomes a set of cells at its zoom's resolution. The map pod subscribes to those cells' change feed from the live store, once per pod, however many viewers share a cell. Each second it pushes each viewer only what changed in their cells. A pan subscribes the new cells and sends their snapshot first.", P,
 "C: It covers any number of viewers per cell: one feed, many sockets. Not a single viewer panning wildly, which costs a snapshot each time.", P,
 "C: Rejected: clients polling a bounding box. Five thousand viewers scan the hottest cells every second."], cls="dia")
S(plain(K(3, "polling against pushing"), "The same 5,000 viewers, two ways", table(["", "Polling a bounding box", "Cell subscriptions"], [
  ["Reads per second", "5,000 scans of the live store", "one change feed per (pod, cell)"],
  ["Downtown, 3,000 viewers", "3,000 scans of the same cells", "one feed, 3,000 sockets"],
  ["A quiet night", "5,000 scans finding nothing", "almost nothing sent"]], "bt sm")), [
 "C: The same five thousand viewers, two ways.", P, "C: Polling: five thousand scans of the live store a second. Subscriptions: one change feed per pod and cell.", P,
 "C: Downtown, with three thousand viewers: three thousand scans of the same cells, against one feed fanned out to three thousand sockets.", P,
 "C: And on a quiet night: five thousand scans finding nothing, against almost nothing sent."])

qs("Interviewer · the second-level push", "“A map pod dies with 800 viewers.”", ["I: A map pod dies with eight hundred viewers.", "[pause: 1.5]"])
S(plain(K(3, "the second fix"), "Viewers reconnect; a snapshot, then deltas", cards(
  ("grn", "Stateless enough", "Subscriptions are rebuilt from the viewport the browser resends; any pod can take it."),
  ("amb", "Jittered reconnect", "800 browsers reconnect over 5 s, not in one burst."), cols=2)), [
 P, "C: The browser resends its viewport to any pod, which rebuilds the subscriptions and sends a snapshot.", P,
 "C: Eight hundred browsers reconnect with jitter over five seconds, not in one burst. The same lesson as the reconnect storm in question twenty-nine."])
say_slide("“A viewport is a set of cells at its zoom. Map pods subscribe once per cell to the live store's change feed and push each viewer only what changed, every second. No browser polls, and a busy cell costs one feed however many people watch it.”", [
 "V: If asked, I'd say: a viewport is a set of cells at its zoom. Map pods subscribe once per cell to the live store's change feed and push each viewer only what changed, every second. No browser polls, and a busy cell costs one feed however many people watch it.", "[pause: 1.0]",
 "N: That fix creates the next question: the map is fresh as long as vehicles can send. What if a whole city couldn't?"])
