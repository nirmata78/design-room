from dsl import *
from stack import TECH, STACK, SUMMARY, SUMMARY_SAY, say_text
import re
P = "[+]"

chapter(4, "API and entities", 3, "What crosses the wire, and what is stored", ["C: The interfaces, then the data."])

S(plain("API · a position on the wire (FR1)", "Small, numbered, and honest about its own time",
  chips("serves FR1", "writes POSITION", "MQTT, QoS 1") +
  code('PUBLISH v/v-311/pos\n{"seq": 9402, "epoch": 2,\n "t": "2026-11-22T18:00:04.120Z",\n "lat": 40.7484, "lng": -73.9857,\n "speed": 11.2, "heading": 184,\n "lane": "latest"}', "json", hl=(2, 3, 7))), [
 "C: A position on the wire, for F-R-one. About three hundred bytes with headers.",
 "C: Three fields matter. The sequence number and epoch: the vehicle's own order, surviving reboots. The time the vehicle took the fix, which the history keeps and the map displays as age, but which never decides what's newer. And the lane: latest, backfill or safety, which tells the server how the message was scheduled."])

S(plain("API · a health summary (FR1)", "Every 30 seconds: counters, not a stream of readings",
  code('PUBLISH v/v-311/health\n{"seq": 9405, "epoch": 2, "window_s": 30,\n "battery_v": 12.6, "cpu_temp_c": 61,\n "gps_fix": "3d", "rssi_dbm": -97,\n "faults": ["camera_2_dropped_frames"]}', "json", hl=(2, 5))), [
 "C: A health summary, every thirty seconds. Notice it's a summary over a window, not a stream of raw readings: battery, temperature, G-P-S fix, signal strength, and any faults. Raw sensor logs are question ninety-eight's input and travel another way.",
 "C: It shares the position's sequence counter, so the same ordering and deduplication rules apply to everything a vehicle sends."])

S(plain("API · the rest", "Three more, each tagged", table(["Interface", "Serves", "Touches", "Carries"], [
  ["<code>WS /v1/map</code> {viewport, zoom}", "FR2", "live cells", "a snapshot, then deltas or counts every second"],
  ["<code>GET /v1/vehicles/{id}/track?from&amp;to</code>", "FR3", "POSITION history", "every fix, by seq, at a pinned snapshot"],
  ["<code>v/{id}/safety</code> (MQTT) → dispatch", "FR4", "SAFETY EVENT", "kind, position, seq; its own topic"]], "bt xs mx")), [
 "C: Three more.", P, "C: The map socket, for F-R-two: a viewport and a zoom in; a snapshot, then deltas or counts each second, out.", P,
 "C: A vehicle's track, for F-R-three: every fix in a window, ordered by sequence, read at a pinned snapshot so the answer doesn't change under the auditor.", P,
 "C: And safety events, for F-R-four, on their own topic, straight to dispatch."])

S(dia("Data · conceptual model", "Vehicles, positions in cells, and what watches them", "erd-chen"), [
 "C: The conceptual model.", P, "C: A vehicle.", P,
 "C: It reports positions: a weak entity identified by the vehicle and a sequence number, with a time and a place.", P,
 "C: Each position is in one cell.", P, "C: A vehicle raises safety events, also numbered.", P,
 "C: Positions belong to trips.", P, "C: And a viewport covers many cells, which is how the map knows what to send."], cls="dia")

S(dia("Data · physical model", "History by vehicle; the present in memory", "erd-physical"), [
 "C: The physical side.", P, "C: Positions in Iceberg: partitioned by day and vehicle bucket, sorted by vehicle and sequence. Fifty-two terabytes a month.", P,
 "C: Safety events in their own table.", P, "C: The live view in memory: vehicle to cell, cell to vehicles, and counts at coarser resolutions.", P,
 "C: The updater's keyed state: the last sequence per vehicle, checkpointed.", P,
 "C: Subscriptions in memory, per map pod.", P, "C: And the vehicle registry, shared with question twenty-nine."], cls="dia")

chapter(5, "High-level design", 4, "Three versions on one picture, then every path", ["C: The design in three versions, on one picture."])

S(dia("Design · version 1", "The simplest thing that is complete: a log and a lake", "base-v1", vtag="V1"), [
 "C: Version one, the simplest thing that's complete.", P, "C: The vehicle uplink sends positions.", P, "C: To a telemetry gateway.", P,
 "C: Appended to a log keyed by vehicle.", P, "C: Landed in a history lake every five minutes.", P,
 "C: A map A-P-I queries the lake.", P, "C: For the operator. The objection: the map is minutes behind, and every viewport is a scan."], cls="dia")

S(dia("Design · version 2", "The live view: a state updater and a live store", "base-v2", vtag="V2"), [
 "C: Version two.", P, "C: Version one, carried.", P, "C: New, a state updater: a stream job keyed by vehicle that keeps only newer sequence numbers.", P,
 "C: New, a live store by cell, in memory; the map reads it. That's question three's split: the same log, a hot path and a cold one. The objection: a safety event waits behind everything, and nobody can replay an hour precisely."], cls="dia")

S(dia("Design · version 3", "Urgent and exact: a safety lane and a replay API", "base-v3", vtag="V3"), [
 "C: Version three.", P, "C: Version two, carried.", P, "C: New, a safety lane: its own topic, never behind positions.", P,
 "C: Straight to dispatch.", P, "C: New, a replay A-P-I over the lake, built for one vehicle's window.", P,
 "C: For analysts and training. This is the baseline."], cls="dia")

S(plain("Design · the containers", "Each container, what it owns, and its number", table(["Container", "Owns", "Its number"], [
  ["Vehicle uplink", "The buffer, the lanes, the backoff", "2 M vehicles; 6 h of buffer"],
  ["Telemetry gateway", "Identity, sessions, topics", "1 M messages/s"],
  ["Telemetry log", "Order per vehicle", "512 partitions, 3 days"],
  ["State updater", "Newest per vehicle", "1 M/s in, last seq per vehicle"],
  ["Live store + map API", "Now, by cell; viewers’ subscriptions", "400 MB; 5,000 viewers"],
  ["History lake + replay", "Everything, by vehicle", "52 TB a month; 10 s per vehicle-hour"]], "bt xs mx")), [
 "C: The containers.", P, "C: The uplink: the buffer, the lanes and the backoff.", P, "C: The gateway: identity, sessions and topics, a million messages a second.", P,
 "C: The log: order per vehicle.", P, "C: The state updater: the newest per vehicle.", P,
 "C: The live store and map A-P-I: now, by cell, and five thousand viewers' subscriptions.", P,
 "C: The lake and replay: everything, by vehicle."])

S(plain("Design · where a position can wait", "Every queue on the path, and what bounds it", table(["Where", "Bound", "When it fills"], [
  ["The vehicle’s buffer", "6 h, ring", "coverage gaps: drop oldest, count it"],
  ["The gateway session", "MQTT inflight window", "a slow broker: the vehicle backs off"],
  ["The log", "3 days", "a stalled consumer: lag pages"],
  ["The updater", "keyed state + checkpoint", "a restart: resumes from offsets"],
  ["The map push", "one tick (1 s)", "a slow socket: drop deltas, resend snapshot"]], "bt xs mx")), [
 "C: Before the flows, every place a position can wait, because each is a freshness risk.", P,
 "C: The vehicle's buffer, six hours: when it fills, drop the oldest and count it.", P,
 "C: The gateway session's in-flight window: a slow broker makes the vehicle back off.", P,
 "C: The log, three days: a stalled consumer shows as lag, and pages.", P,
 "C: The updater's keyed state: a restart resumes from its checkpoint.", P,
 "C: And the map push, one tick: a slow browser gets its deltas dropped and a fresh snapshot instead. Nothing waits without a bound."])

S(dia("Flow · FR1 and FR2", "A position, from the vehicle to the map", "flow-live"), [
 P, "C: The live path, numbered.", P, "C: One: the uplink publishes.", P, "C: Two: appended, keyed by vehicle.", P,
 "C: Three: the updater consumes in order.", P, "C: Four: it overwrites the live store if newer.", P,
 "C: Five: the operator's viewport.", P, "C: Six: the map reads cells and pushes changes."], cls="dia")

S(dia("Flow · FR1 and FR3", "A position, from the vehicle to an audit", "flow-history"), [
 P, "C: The history path, numbered.", P, "C: One and two: the same publish and append.", P, "C: The same, the log.", P,
 "C: Three: landed in the lake every five minutes.", P, "C: Four: an analyst asks for a window.", P, "C: Five: the replay A-P-I reads one bucket."], cls="dia")

S(dia("Sequence · FR1 report", "Newer by sequence, not by arrival", "seq-report"), [
 "C: Report, as a sequence.", P, "C: Vehicle three-eleven, sequence nine thousand four hundred and two.", P, "C: Appended, keyed by the vehicle.", P,
 "C: Delivered in order for that vehicle.", P, "C: Newer than nine four oh one.", P, "C: The live store moves the vehicle to its new cell."], cls="dia")

S(dia("Sequence · FR2 watch", "A snapshot, then what changed", "seq-watch"), [
 "C: Watch, as a sequence.", P, "C: An operator opens downtown at zoom fifteen.", P, "C: Zoom fifteen means resolution nine: forty-eight cells.", P,
 "C: A snapshot of those cells.", P, "C: Nineteen hundred and thirty vehicles.", P, "C: Then changes in those cells.", P,
 "C: Every second, the four hundred that moved."], cls="dia")

S(dia("Sequence · FR3 replay", "One bucket, one vehicle, one hour", "seq-replay"), [
 "C: Replay, as a sequence.", P, "C: Vehicle three-eleven, two to three p.m., the third of November.", P,
 "C: The day and the bucket: hash of the vehicle, mod two-fifty-six.", P, "C: One bucket at a snapshot, a range of sequence numbers.", P,
 "C: Eighteen hundred positions, sorted.", P, "C: The hour, including every fix that arrived late."], cls="dia")

S(dia("Sequence · FR4 alert", "A safety event never waits", "seq-safety"), [
 "C: Alert, as a sequence.", P, "C: The vehicle detects a hard brake and skips its queue.", P, "C: A safety message.", P,
 "C: On the safety topic.", P, "C: Dispatch is paged within a second, whatever else is flushing."], cls="dia")

subchapter("5.1", "Components and technologies", ["C: One level down: what each box runs on, three containers opened up, and what I rejected."])

S(dia("Architecture · C4 containers · technologies", "The same containers, now with what they run on", "c4-containers-tech"), [
 P, "C: The same view, with technologies.", P, "C: The uplink: C-plus-plus on the vehicle.", P, "C: The gateway: E-M-Q-X, MQTT five, mutual T-L-S.", P,
 "C: The log: Kafka, keyed by vehicle.", P, "C: The updater: Flink, keyed by vehicle.", P, "C: The live store: the in-memory H-three index from question thirty-nine.", P,
 "C: The map A-P-I: Go with WebSockets.", P, "C: The lake: Iceberg on Google Cloud Storage.", P, "C: And replay: Trino over Iceberg."], cls="dia")

S(dia("Architecture · C4 components · vehicle uplink", "Inside the uplink, from the sensors to the network", "c4-comp-uplink"), [
 "C: Inside the uplink.", P, "C: GPS and sensors.", P, "C: The sampler: every two seconds moving, thirty parked.", P,
 "C: A safety detector that skips the queue.", P, "C: A ring buffer in flash: six hours, a sequence per message.", P,
 "C: The scheduler with three lanes: safety, latest, backfill.", P, "C: A rate cap on backfill.", P,
 "C: The MQTT client with jittered backoff.", P, "C: To the gateway. Challenge four lives here."], cls="dia")

S(dia("Architecture · C4 components · state updater", "Inside the updater, from the log to the live store", "c4-comp-updater"), [
 "C: Inside the state updater.", P, "C: The log.", P, "C: The source, per partition, in order.", P,
 "C: The sequence filter: the last sequence per vehicle, in keyed state.", P, "C: Older positions go to a side output: history only.", P,
 "C: The cell mapper: has the vehicle changed cell?", P, "C: The live writer, only if newer.", P, "C: Into the live store. Challenge one lives here."], cls="dia")

S(dia("Architecture · C4 components · map API", "Inside the map, from a viewport to a push", "c4-comp-map"), [
 "C: Inside the map A-P-I.", P, "C: The operator's browser.", P, "C: The viewport tracker turns zoom into a resolution, and the view into cells.", P,
 "C: Subscriptions to only those cells.", P, "C: A snapshot loader, on every pan.", P, "C: The aggregator: counts when zoomed out.", P,
 "C: The delta pusher, every second.", P, "C: Fed by the live store's change feed. Challenges two and three live here."], cls="dia")

def tsay(_id):
    s = STACK[_id]; first = lambda t: re.split(r"(?<=[.:;])\s", say_text(t))[0].rstrip(".:;") + "."
    out = [P, "C: " + say_text(s["how"]), P, "C: Why: " + first(s["why"])]
    for i, (n, w) in enumerate(s["rejected"]):
        out += [P, f"C: {'Rejected: ' if i == 0 else ''}{say_text(n)}. " + first(w)]
    return out
for _id in ("log", "live", "map", "lake"):
    S(tech(**TECH(_id)), tsay(_id))

_ss = SUMMARY_SAY()
S(plain("Technology · the stack on one slide", "The stack, against its rivals",
        table(["Container", "Choice", "Rejected", "The deciding reason"], SUMMARY(), "bt xs mx") +
        grade("Naming a product is not the signal. Naming the property that rules out its rival is.")), _ss[:-1] + [P, _ss[-1]])

subchapter("5.2", "When you don't need all this", ["C: Before I break it: a small fleet needs one database."], sub="ALTERNATE")

S(dia("Alternate path · ALTERNATE", "One PostgreSQL: a latest table and a history table", "alt",
      extra=strip(("fixb", "How it works", "Each position upserts latest(vehicle) if seq is newer and appends to a history table partitioned by day; the map queries latest by bounding box with PostGIS."),
                  ("case", "What it gives up", "One database for both jobs; no lanes; polling maps; history in one box."))), [
 P, "C: The alternate path, on version two.", P, "C: The log goes.", P, "C: The state updater.", P, "C: And the live store.", P,
 "C: Instead, each position upserts a latest row if its sequence is newer, and appends to a history table partitioned by day. The map queries the latest table by bounding box with PostGIS.", P,
 "C: What it gives up: one database for both jobs, no lanes, polling maps, and the history in one box."], cls="dia")

key("ALTERNATE · the line", "5,000 vehicles every 2 s is <em>2,500 writes a second</em>, twice: one database copes. 2 M is <em>1 M a second</em>. Below about <em>5,000 vehicles</em>, I'd ship PostgreSQL.", [
 "C: The line. Five thousand vehicles every two seconds is twenty-five hundred writes a second, twice. One database copes. Two million is a million a second.",
 "V: Below about five thousand vehicles, I'd ship PostgreSQL, keep the sequence numbers and the lanes on the vehicle, and say when I'd switch.", "[pause: 0.8]"])
