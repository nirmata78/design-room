from dsl import *
from stack import REJ
P = "[+]"
B = lambda x: f'<span class="bad">{x}</span>'
K = lambda n, t: f"Challenge {n} of 6 · {t}"

# ── 4
subchapter("7.4", "Challenge 4: A city comes back", ["N: Challenge four: backpressure, decided on the vehicle."])
qs("Interviewer · challenge 4 of 6", "“A city's cellular network was down for three minutes. 100,000 vehicles reconnect at once with full buffers. What happens to the map, and to a crash that happens right now?”", [
 "I: A city's cellular network was down for three minutes. A hundred thousand vehicles reconnect at once with full buffers. What happens to the map, and to a crash that happens right now?", "[pause: 2.0]"])
S(dia(K(4, "a flush"), "In what order does a vehicle catch up?", "ch4-attack", q=True, red=True,
      extra=strip(("case", "Naive answer", "“Send the buffer in order, as fast as possible.”"),
                  ("case", "Break", "The scheduler sends oldest first: the map stays three minutes behind, and a new crash waits behind history."))), [
 P, "C: Inside the uplink.", P, "C: The scheduler is marked.", P, "C: The naive answer: send the buffer in order, as fast as possible.", P,
 "C: Then every vehicle sends its oldest positions first. The map stays three minutes behind for the whole flush, and a crash that happens now waits behind ninety old positions."], cls="dia")
S(trace(K(4, "the trace"), "Nine million old messages in front of one new crash", [
  ("17:03:00", "the network returns; 100,000 vehicles flush 90 positions each"),
  ("17:03:01", "9 M messages, oldest first, as fast as possible"),
  ("17:03:20", B("the city’s map still shows 17:00")),
  ("17:03:25", B("v-907 crashes; its event is behind 60 queued positions: dispatch hears at 17:03:55"))],
  hedge=("Two errors", "The present waits behind the past, and the urgent waits behind the routine.")), [
 "C: The trace.", P, "C: The network returns, and a hundred thousand vehicles flush ninety positions each.", P,
 "C: Nine million messages, oldest first, as fast as each vehicle can.", P, "C: Twenty seconds later the city's map still shows three minutes ago.", P,
 "C: A vehicle crashes; its event waits behind sixty queued positions, and dispatch hears thirty seconds late.", P,
 "C: The present waits behind the past, and the urgent waits behind the routine."])
S(dia(K(4, "the fix"), "Three lanes: safety, latest, then capped backfill", "ch4-fix",
      extra=strip(("fixb", "Mechanism", "On reconnect: safety events first (own topic), then the newest position, then the backlog oldest-first at ≤ 50 messages/s per vehicle; the cap halves if the broker answers retry-after."),
                  ("whyb", "Covers, and does not", "Outages, tunnels, and the city-wide flush. Not a buffer that overflowed: past 6 h, the oldest positions are dropped and counted.")) + rejl(*REJ(4))), [
 P, "C: The fix.", P, "C: The scheduler.", P,
 "C: One level down. On reconnect, the scheduler sends safety events first, on their own topic. Then the newest position, on the latest lane, so the map is current within seconds. Then the backlog, oldest first, at no more than fifty messages a second per vehicle, and the cap halves if the broker answers retry-after. That's question twenty-nine's backoff, applied to data.", P,
 "C: It covers outages, tunnels and a city-wide flush. Not a buffer that overflowed: past six hours the oldest positions are dropped, and the drop is counted and reported.", P,
 "C: Rejected: flushing the buffer oldest first. The map stays three minutes behind for the whole flush, and safety events queue behind history."], cls="dia")
S(plain(K(4, "the flush, in numbers"), "Nine million messages, arranged", table(["Lane", "Messages", "Reaches the server"], [
  ["Safety", "a handful", "within a second of reconnecting"],
  ["Latest", "100,000 (one per vehicle)", "within a few seconds: the map is current"],
  ["Backfill", "9 M, capped at 50/s per vehicle", "over about two minutes, to history only"]], "bt sm")), [
 "C: The flush, in numbers.", P, "C: Safety: a handful, within a second of reconnecting.", P,
 "C: Latest: one per vehicle, a hundred thousand, within a few seconds. The city's map is current almost at once.", P,
 "C: Backfill: nine million, capped at fifty a second per vehicle, over about two minutes, into history only. The live path never sees it."])

S(plain(K(4, "the scheduler, as pseudocode"), "Urgent, then present, then past",
  pseudo("on connected:\n    send_all(safety_queue)          # own topic\n    send(latest_position, lane = latest)\n    rate = 50 / s\n    for m in buffer.oldest_first():\n        send(m, lane = backfill); throttle(rate)\n        if broker.retry_after: rate = max(5, rate / 2)\n        if safety_queue: send_all(safety_queue)", hl=(2, 3, 6, 8))), [
 "C: The scheduler in pseudocode. Line two: safety first. Line three: the newest position, so the map catches up at once. Line six: the backlog at a capped rate. Line eight: a new safety event during the backfill jumps the queue again."])
qs("Interviewer · the second-level push", "“And on the server side?”", ["I: And on the server side?", "[pause: 1.5]"])
S(plain(K(4, "the second fix"), "Lanes all the way through", cards(
  ("grn", "Separate topics", "Safety and positions are different topics with different consumers: one can lag while the other cannot."),
  ("amb", "Backfill does not touch the map", "Backfilled positions fail the sequence filter and go to history only: no live-store load."), cols=2)), [
 P, "C: The lanes continue on the server. Safety and positions are different topics with different consumers, so one can lag while the other can't.", P,
 "C: And backfilled positions fail the sequence filter, so they go to history only. Nine million old messages cost the live store nothing."])
say_slide("“The vehicle decides what goes first. Safety events, then the newest position, then the backlog oldest-first at a capped rate that backs off when the broker asks. Backfill fails the sequence filter and goes only to history, so a city coming back online never delays the map or a crash.”", [
 "V: If asked, I'd say: the vehicle decides what goes first. Safety events, then the newest position, then the backlog, oldest first, at a capped rate that backs off when the broker asks. Backfill fails the sequence filter and goes only to history, so a city coming back online never delays the map or a crash.", "[pause: 1.0]",
 "N: That fix creates the next question: all of that backfill lands in history. Can you find it again?"])

# ── 5
subchapter("7.5", "Challenge 5: One vehicle, one hour", ["N: Challenge five: history laid out for the question it will be asked."])
qs("Interviewer · challenge 5 of 6", "“An incident review needs vehicle 311's exact positions from 14:00 to 15:00 on 3 November, including what it buffered in a tunnel. How fast, and how sure?”", [
 "I: An incident review needs vehicle three-eleven's exact positions from two to three p.m. on the third of November, including what it buffered in a tunnel. How fast, and how sure?", "[pause: 2.0]"])
S(dia(K(5, "a replay"), "Where is one vehicle’s hour?", "ch5-attack", q=True, red=True,
      extra=strip(("case", "Naive answer", "“History is files by arrival hour; query them.”"),
                  ("case", "Break", "The lake is laid out by arrival: one vehicle’s hour is in every file of two days, mixed with 2 M others."))), [
 P, "C: The lake and the replay A-P-I.", P, "C: The lake is marked.", P, "C: The naive answer: history is files by arrival hour; query them.", P,
 "C: Then one vehicle's hour, including buffered fixes that arrived later, is spread over every file of two days, mixed with two million other vehicles."], cls="dia")
S(trace(K(5, "the trace"), "A ten-second question that takes an hour", [
  ("14:00 – 15:00", "v-311 drives; 20 min in a tunnel; 600 positions buffered"),
  ("15:12", "the buffer lands, in the 15:00 arrival files"),
  ("review", "query 14:00 – 15:00 arrival files: 1,200 positions, a 20-min gap"),
  ("review", B("full scan of two days to find the rest: 52 TB / 30 days ≈ 3.5 TB read"))],
  hedge=("Two needs", "Find one vehicle cheaply, and include what arrived late.")), [
 "C: The trace.", P, "C: Vehicle three-eleven drives, twenty minutes of it in a tunnel: six hundred positions buffered.", P,
 "C: The buffer lands at twelve past three, in the three o'clock arrival files.", P,
 "C: The reviewer queries two to three: twelve hundred positions, and a twenty-minute gap.", P,
 "C: Finding the rest means scanning two days, about three and a half terabytes.", P, "C: Two needs: find one vehicle cheaply, and include what arrived late."])
S(dia(K(5, "the fix"), "Partition by day and vehicle bucket; sort by vehicle and seq", "ch5-fix",
      extra=strip(("fixb", "Mechanism", "Iceberg partitions (event day, hash(vehicle) mod 256), files sorted by (vehicle, seq); late positions are new files in their event day. A replay prunes to one bucket and range-reads, at a pinned snapshot."),
                  ("whyb", "Covers, and does not", "Late arrivals and one-vehicle audits in seconds. Not a whole-day ML read: that scans all 256 buckets, which is what it wants.")) + rejl(*REJ(5))), [
 P, "C: The fix.", P, "C: The lake.", P, "C: And replay.", P,
 "C: One level down. Iceberg partitions by the event's day and by the vehicle's hash modulo two hundred and fifty-six, and files are sorted by vehicle and sequence. A late position is a new file in its event day, not in its arrival hour. A replay prunes to one day and one bucket, about two hundred and seventy gigabytes a month divided by thirty, and range-reads one vehicle, at a pinned snapshot so the answer can't change.", P,
 "C: It covers late arrivals and one-vehicle audits in seconds. Not a whole-day training read; that scans all buckets, which is what it wants anyway.", P,
 "C: Rejected: partitioning history by arrival time. A vehicle's hour is spread over every file that arrived late, and one replay scans everyone."], cls="dia")
S(plain(K(5, "two kinds of reader"), "The audit and the model read the same lake differently", table(["", "An audit", "ML training"], [
  ["Asks for", "one vehicle, one hour", "every vehicle, a day or a week"],
  ["Reads", "one bucket, a range", "all 256 buckets, every column it needs"],
  ["Cares about", "exactness, late fixes, a pinned snapshot", "throughput and cost"],
  ["Layout serves it by", "bucket + sort order", "columnar files, day partitions"]], "bt sm")), [
 "C: The same lake has two kinds of reader.", P, "C: An audit asks for one vehicle and one hour; training asks for every vehicle over a day or a week.", P,
 "C: The audit reads one bucket and a range; training reads all two hundred and fifty-six buckets and only the columns it needs.", P,
 "C: The audit cares about exactness, late fixes and a pinned snapshot; training cares about throughput and cost.", P,
 "C: The bucket and sort order serve the audit; the columnar files and day partitions serve training. One layout, chosen so neither has to scan for the other."])

S(plain(K(5, "what the layout buys"), "Bytes read for one vehicle’s hour", table(["Layout", "Read", "Time"], [
  ["By arrival hour, scan", "two days of everything ≈ 3.5 TB", "an hour of cluster time"],
  ["By event day only", "one day ≈ 1.7 TB", "minutes"],
  ("pick", ["<b>Day × 256 buckets, sorted</b>", "one bucket ≈ 7 GB, then a range ≈ 50 MB", "<b>≈ 10 s</b>"])], "bt sm")), [
 "C: What the layout buys, in bytes.", P, "C: By arrival hour, scanning: two days of everything, three and a half terabytes, an hour of cluster time.", P,
 "C: By event day only: one day, one point seven terabytes. Minutes.", P,
 "C: By day and one of two hundred and fifty-six buckets, sorted: one bucket of about seven gigabytes, and because it's sorted by vehicle, a range of about fifty megabytes inside it. About ten seconds."])

S(plain(K(5, "a replay, as pseudocode"), "Prune, range-read, deduplicate, order",
  pseudo("snap = lake.snapshot_now()            # pin it\nday = date(t_from)\nb = hash(vehicle) % 256\nrows = read(snap, day=day, bucket=b,\n            vehicle=vehicle, t in [t_from, t_to])\nrows = dedup_by(rows, (epoch, seq))\nreturn sort_by(rows, (epoch, seq))", hl=(1, 3, 6))), [
 "C: As pseudocode. Line one: pin a snapshot, so the auditor and a second reviewer see the same rows. Line three: one bucket out of two hundred and fifty-six. Line six: deduplicate by epoch and sequence. About ten seconds, and the same answer every time."])
qs("Interviewer · the second-level push", "“A buffered position arrives after the audit ran.”", ["I: A buffered position arrives after the audit ran.", "[pause: 1.5]"])
S(plain(K(5, "the second fix, and the honest limit"), "The snapshot says what was known when", cards(
  ("grn", "A newer snapshot", "Re-running at a newer snapshot includes it; the report records which snapshot it used."),
  ("red", "Honest limit", "A vehicle offline longer than its 6 h buffer has gaps forever; the gap is reported, not interpolated."), cols=2)), [
 P, "C: Re-running at a newer snapshot includes it, and the report records which snapshot each answer used. What we knew, and when, is part of the audit.", P,
 "C: The honest limit: a vehicle offline longer than its six-hour buffer has gaps forever. The gap is reported, never interpolated into something that looks like data."])
say_slide("“History is laid out for its question: partitioned by event day and a vehicle bucket, sorted by vehicle and sequence, with late positions filed under the day they happened. One vehicle's hour is one bucket and a range read at a pinned snapshot: about ten seconds, and the same answer every time.”", [
 "V: If asked, I'd say: history is laid out for its question. It's partitioned by event day and a vehicle bucket, sorted by vehicle and sequence, and late positions are filed under the day they happened. One vehicle's hour is one bucket and a range read at a pinned snapshot: about ten seconds, and the same answer every time.", "[pause: 1.0]",
 "N: That fix creates the last question: how would you know the map itself is stale?"])

# ── 6
subchapter("7.6", "Challenge 6: Forty seconds stale", ["N: Challenge six is observability, measured on the map."])
qs("Interviewer · challenge 6 of 6", "“An operator notices a vehicle on the map is 40 seconds behind its driver's phone. Every dashboard is green. How would you have known first?”", [
 "I: An operator notices a vehicle on the map is forty seconds behind its driver's phone. Every dashboard is green. How would you have known first?", "[pause: 2.0]"])
S(dia(K(6, "staleness"), "Where can a position wait without anyone counting?", "ch6-attack", q=True, red=True,
      extra=strip(("case", "Naive answer", "“Consumer lag is zero.”"),
                  ("case", "Break", "The map API pushes from a pod whose change-feed subscription silently stopped."))), [
 P, "C: The log, the updater, the live store and the map.", P, "C: The map A-P-I is marked.", P, "C: The naive answer: consumer lag is zero.", P,
 "C: It is. The live store is current. One map pod's change-feed subscription silently stopped, and its viewers see a frozen city."], cls="dia")
S(trace(K(6, "the trace"), "Lag zero, map frozen", [
  ("10:00", "a map pod’s change-feed connection drops; the reconnect bug leaves it unsubscribed"),
  ("10:00 →", "its 800 viewers keep their sockets; pushes contain nothing new"),
  ("10:40", B("Kafka lag 0; live store current; pod CPU low: all green")),
  ("10:41", B("an operator compares the map with a driver’s phone"))],
  hedge=("What the dashboards saw", "Every stage healthy, measured from the inside. Nobody measured the map.")), [
 "C: The trace.", P, "C: A map pod's change-feed connection drops, and a reconnect bug leaves it unsubscribed.", P,
 "C: Its eight hundred viewers keep their sockets; the pushes contain nothing new.", P,
 "C: Forty minutes later, Kafka lag is zero, the live store is current, the pod's C-P-U is low. All green.", P,
 "C: An operator compares the map with a driver's phone.", P, "C: Every stage was healthy, measured from the inside. Nobody measured the map."])
S(dia(K(6, "the fix"), "Version four: a freshness probe", "base-v4", vtag="V4"), [
 P, "C: The fix changes the design: version four. Version three, carried.", P,
 "C: New: a freshness probe. Canary vehicles, simulated in every city, publish through the gateway, and the probe reads them back through the map, like a viewer."], cls="dia")
S(plain(K(6, "the fix, one level down"), "Measure age where the operator sees it", cards(
  ("grn", "Canary vehicles", "A simulated vehicle per city moves every 2 s; a probe viewer on every map pod must see it within 2 s."),
  ("grn", "Age on screen", "Each push carries the position’s receipt time; the browser reports the age it displays."),
  ("grn", "Per-pod freshness", "The share of viewers per pod receiving changes; zero for a busy city pages."),
  ("grn", "Safety latency", "Canary safety events, end to end to a test dispatch endpoint."), cols=2) + rejl(*REJ(6))), [
 "C: One level down, four signals.", P,
 "C: Canary vehicles: a simulated vehicle in every city moves every two seconds, and a probe viewer subscribed on every map pod must see it within two seconds. That one would have paged at ten o'clock and two seconds.", P,
 "C: Age on screen: every push carries the position's receipt time, and the browser reports the age it actually displays.", P,
 "C: Per-pod freshness: the share of a pod's viewers receiving changes. Zero for a busy city pages.", P,
 "C: And canary safety events, end to end, to a test dispatch endpoint.", P,
 "C: Rejected: consumer-lag dashboards. Lag can be zero while a vehicle on the map is forty seconds stale."])
S(plain(K(6, "the canary, in detail"), "A fake vehicle that behaves like a real one", table(["Step", "What it checks"], [
  ["Publishes a position every 2 s with its own seq, through the real gateway", "identity, sessions, the log"],
  ["Moves along a fixed route in every city", "cell changes, the updater, the live store"],
  ["A probe viewer per map pod subscribes to its cell", "subscriptions and pushes, per pod"],
  ["Raises a safety event every 10 minutes", "the safety lane to a test endpoint"],
  ["Its history is replayed every hour", "the lake and the replay API"]], "bt xs mx")), [
 "C: The canary, in detail, because its value is that it behaves like a real vehicle.", P,
 "C: It publishes a position every two seconds with its own sequence, through the real gateway: identity, sessions and the log.", P,
 "C: It drives a fixed route in every city, so it changes cells: the updater and the live store.", P,
 "C: A probe viewer on every map pod subscribes to its cell: subscriptions and pushes, pod by pod.", P,
 "C: Every ten minutes it raises a safety event to a test endpoint.", P,
 "C: And every hour its history is replayed: the lake and the replay A-P-I. One fake vehicle exercises every path in this video."])

S(plain(K(6, "reading the signals"), "Symptoms in pairs", table(["Symptom", "Paired with", "Means"], [
  ["Canary stale on one pod", "others fresh", "that pod’s subscription"],
  ["Canary stale everywhere", "Kafka lag rising", "the updater or the log"],
  ["Age on screen high", "canaries fresh", "real vehicles in a coverage hole"],
  ["Backfill share rising", "one carrier", "a carrier outage, recovering"],
  ["Safety canary late", "position lag normal", "the safety lane itself"]], "bt sm")), [
 "C: And read them in pairs.", P, "C: A canary stale on one pod while others are fresh: that pod's subscription. Our case.", P,
 "C: Canaries stale everywhere with Kafka lag rising: the updater or the log.", P,
 "C: Age on screen high while canaries are fresh: real vehicles in a coverage hole, not us.", P,
 "C: The share of backfill rising on one carrier: that carrier is recovering from an outage.", P,
 "C: And a late safety canary with normal position lag: the safety lane itself."])
S(plain(K(6, "the SLIs"), "What the map promises, measured", table(["SLI", "Target"], [
  ["Canary visible on every pod", "p99 ≤ 2 s"],
  ["Safety canary to dispatch", "p99 ≤ 1 s"],
  ["Received positions in history", "100 % (daily reconciliation of counts)"],
  ["One-vehicle replay", "p95 ≤ 10 s"],
  ["Positions dropped on vehicles (buffer full)", "counted, reported per fleet"]], "bt sm")), [
 "C: And the service levels.", P, "C: The canary visible on every pod within two seconds.", P, "C: The safety canary at dispatch within a second.", P,
 "C: Every received position in history, checked by a daily reconciliation of counts, question three's conservation check.", P,
 "C: One vehicle's hour replayed within ten seconds.", P, "C: And positions dropped on vehicles because a buffer filled: counted and reported, never hidden."])
say_slide("“I'd measure freshness where the operator sees it: a canary vehicle in every city, read back through every map pod within two seconds; the age each browser actually displays; and canary safety events end to end. Lag measures the pipeline. Canaries measure the map.”", [
 "V: If asked, I'd say: I'd measure freshness where the operator sees it. A canary vehicle in every city, read back through every map pod within two seconds; the age each browser actually displays; and canary safety events end to end. Lag measures the pipeline. Canaries measure the map.", "[pause: 1.0]"])

chapter(8, "Recap", 6, "The final design, and what to say", ["C: The recap."])
S(dia("Recap · version four", "Where each mechanism ended up", "recap"), [
 P, "C: Version four.", P, "C: The uplink: lanes and a capped backfill.", P, "C: The log: keyed by vehicle, so order holds.", P,
 "C: The updater: one log, two views, and sequence numbers.", P, "C: The live store: cells at several resolutions.", P,
 "C: The map: cells, and subscriptions.", P, "C: The lake: everything, by vehicle.", P, "C: And the probe: canaries, read back like a viewer."], cls="dia")
S(plain("Recap · one sentence per path", "Four paths, four sentences", cards(
  ("", "Report", "Positions carry a sequence; the log is keyed by vehicle; safety has its own lane."),
  ("grn", "Watch", "The live view overwrites only with newer positions; viewports subscribe to cells, counts when far."),
  ("amb", "Replay", "History is by event day and vehicle bucket, sorted by seq, read at a snapshot."),
  ("red", "Alert", "Safety events skip every queue, on the vehicle and on the server."), cols=2)), [
 "C: One sentence per path.", P, "C: Report: positions carry a sequence, the log is keyed by vehicle, and safety has its own lane.", P,
 "C: Watch: the live view overwrites only with newer positions, and viewports subscribe to cells, counts when far.", P,
 "C: Replay: history by event day and vehicle bucket, sorted by sequence, read at a snapshot.", P,
 "C: Alert: safety events skip every queue, on the vehicle and on the server."])
S(plain("Recap · the mistakes", "What costs most in this round", table(["Mistake", "Instead"], [
  ["One table for the map and the history", "one log, two views"],
  ["Latest arrival wins", "latest sequence wins"],
  ["Keying the log by geo cell", "key by vehicle; index by cell"],
  ["Every dot at every zoom; polling", "counts when far; cell subscriptions"],
  ["Flushing buffers oldest first", "safety, latest, then capped backfill"],
  ["Watching consumer lag", "canary vehicles read through the map"]], "bt sm")), [
 "N: The mistakes that cost most.", P, "N: One table for the map and the history. Instead, one log, two views.", P,
 "N: Latest arrival wins. Instead, latest sequence wins.", P, "N: Keying the log by geo cell. Instead, key by vehicle and index by cell.", P,
 "N: Every dot at every zoom, polled. Instead, counts when far and subscriptions to cells.", P,
 "N: Flushing buffers oldest first. Instead, safety, latest, then capped backfill.", P, "N: Watching consumer lag. Instead, canaries read through the map."])
key("The close", "One log keyed by <em>vehicle</em>, read twice: <em>latest by cell</em> for the map, <em>everything by vehicle</em> for history. The vehicle orders its own data and decides what goes first. Most of it you have <em>already built</em> in three other questions.", [
 "V: One log keyed by vehicle, read twice: latest by cell for the map, everything by vehicle for history. The vehicle orders its own data and decides what goes first. And most of it, you've already built, in three other questions.", "[pause: 1.0]",
 "C: Thanks for watching. The written design, and the three questions it builds on, are linked below."])
