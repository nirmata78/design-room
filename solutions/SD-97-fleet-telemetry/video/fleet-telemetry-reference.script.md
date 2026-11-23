# SD-97 Device telemetry and live location map: reference solution (Staff L6/L7, compact cut)

<!-- Video script for slide-video-kit/scripts/build_video.py. [slide: v-NNN] = frames/v-NNN.png; [reveal: v-NNN] = the next
     reveal step of the same slide. Generated from src/*.py: edit the sources, not this file. -->
<!-- voices: N=af_heart@0.92 I=bf_emma@0.95 C=am_michael@0.9 V=am_michael@0.84 -->
<!-- names: C=Candidate V=Candidate N=Coach I=Interviewer -->
<!-- say: API=A-P-I SDK=S-D-K TB=terabytes PB=petabytes GB=gigabytes HTTP=H-T-T-P HTTPS=H-T-T-P-S ID=I-D IDs=I-Ds H3=H-three ML=M-L Trino=Treeno PostGIS=Post-G-I-S GPS=G-P-S MQTT=M-Q-T-T mTLS=M-T-L-S TLS=T-L-S CDN=C-D-N EMQX=E-M-Q-X HSM=H-S-M PKI=P-K-I QoS=Q-O-S IoT=I-o-T TSDB=T-S-D-B URL=U-R-L CPU=C-P-U CPUs=C-P-Us GPU=G-P-U GPUs=G-P-Us Kafka=Kahf-kah ClickHouse=Click-House GCS=G-C-S MCAP=M-cap SHA-256=shaw-two-fifty-six DAG=dag Kueue=queue Bigtable=Big-table CI=C-I EM=E-M -->


## 0 Cold open

[slide: v-001]
[pause: 1.2]
C: A live map of two million vehicles sounds like one database of positions. It's asked at autonomous-driving and delivery companies and at Google, because it's really two products off one stream, and it's built from three questions you may already know: event counting, nearby drivers, and a device fleet.
[pause: 1.8]

[slide: v-002]
[pause: 0.6]
I: Millions of vehicles report their position and health every few seconds. Design the system behind a live fleet map for operations, plus a history that can be audited and replayed.
[pause: 1.5]

[slide: v-003]
[pause: 1.3]
C: The hook. The live map asks where each vehicle is now: overwrite, in memory, by place, two seconds fresh, and losing a point is fine.
C: The history asks where it was every two seconds for two years: append, in columns, complete, minutes late is fine. One table for both is slow for the first and wrong for the second.
[pause: 1.1]

[slide: v-004]
[pause: 1.0]
N: Five axes.
[reveal: v-005]
[pause: 0.45]
N: Requirements: the strong answer separates the live view from the history first, and asks about tunnels.
[reveal: v-006]
[pause: 0.45]
N: Composition: it doesn't design everything from scratch. It names the seams: question three's split into a hot and a cold path, question thirty-nine's index, question twenty-nine's devices.
[reveal: v-007]
[pause: 0.45]
N: Correctness: not latest arrival wins, but per-vehicle order and sequence numbers.
[reveal: v-008]
[pause: 0.45]
N: Depth: key the log by vehicle, index by cell, thin by zoom.
[reveal: v-009]
[pause: 0.45]
N: Operations: the age of a position on the map, measured from canary vehicles.
[reveal: v-010]
[pause: 0.45]
C: And the rule for this round: say which known part I'm reusing, and where the seam is.
[pause: 1.0]

[slide: v-011]
[pause: 0.7]
V: One log keyed by vehicle, read twice: an overwrite view by cell for the map, and an append history by vehicle for replay. Sequence numbers decide what's newer; lanes decide what goes first.
[pause: 1.6]

[slide: v-012]
[pause: 1.3]
C: Here's the shape I'm heading for, with the seams marked. It's not a new invention; it's three earlier questions put together.
[reveal: v-013]
[pause: 0.45]
C: The vehicle uplink is question twenty-nine's device agent: identity, a buffer, backoff.
[reveal: v-014]
[pause: 0.45]
C: The gateway is the same broker, with mutual T-L-S.
[reveal: v-015]
[pause: 0.45]
C: The state updater is question three's live path: a stream job over one log, deduplicating by an I-D, here a sequence number.
[reveal: v-016]
[pause: 0.45]
C: The live store is question thirty-nine's index: H-three cells, overwrite-only.
[reveal: v-017]
[pause: 0.45]
C: And the history lake is question three's cold path, laid out for a different query.
[pause: 1.1]

[slide: v-018]
[pause: 0.6]
C: The order I'll follow.
[reveal: v-019]
[pause: 0.45]
C: First, requirements, the numbers, and theory that's mostly borrowed: one log with two views, sequence numbers, cells and lanes.
[reveal: v-020]
[pause: 0.45]
C: Then the interfaces and the data, three versions on one picture, every path, and three containers opened up.
[reveal: v-021]
[pause: 0.45]
C: Then six challenges, from a tunnel exit to a map that's stale while everything is green.
[pause: 0.8]

[pause: 1.4]

## 1 Requirements and scope

[slide: v-022]
[pause: 1.2]
C: The scale first, then five questions.
[pause: 1.8]

[slide: v-023]
[pause: 0.6]
C: The scale.
[reveal: v-024]
[pause: 0.45]
C: About a trillion positions a month, fifty-two terabytes once compressed.
[reveal: v-025]
[pause: 0.45]
C: Two million vehicles, with two years of history kept for audits and replay.
[reveal: v-026]
[pause: 0.45]
C: And the peak: a million positions a second at rush hour, and, after a city's cellular network comes back, a hundred thousand vehicles flushing three minutes of buffer at once.
[reveal: v-027]
[pause: 0.45]
C: Every number later starts from these.
[pause: 0.8]

[slide: v-028]
[pause: 0.6]
C: How fresh must the map be?
[reveal: v-029]
[pause: 0.45]
I: Within two seconds of us receiving a position.
C: Two seconds rules out the history store for the map. It needs its own view.
[pause: 0.6]

[slide: v-030]
[pause: 0.6]
C: What happens when a vehicle loses coverage?
[reveal: v-031]
[pause: 0.45]
I: It buffers locally, for minutes in tunnels, sometimes hours, and flushes when it reconnects.
C: So old positions arrive after new ones. Order has to come from the vehicle, not from arrival.
[pause: 0.6]

[slide: v-032]
[pause: 0.6]
C: What must the history support?
[reveal: v-033]
[pause: 0.45]
I: Two years of it. Audits ask for one vehicle's exact window; machine learning reads whole days.
C: Two access patterns: a narrow one for audits and a wide one for training. The layout must serve both.
[pause: 0.6]

[slide: v-034]
[pause: 0.6]
C: Is anything more urgent than a position?
[reveal: v-035]
[pause: 0.45]
I: Safety events: a hard brake or a crash must reach dispatch within a second.
C: Then safety events never wait behind a backlog of positions, on the vehicle or on the server.
[pause: 0.6]

[slide: v-036]
[pause: 0.6]
C: Who watches the map?
[reveal: v-037]
[pause: 0.45]
I: About five thousand operators at once, at every zoom level.
C: At city zoom nobody can see two hundred thousand dots. The map must show counts far out and vehicles close in.
[pause: 0.6]

[slide: v-038]
[pause: 0.6]
C: Four functional requirements.
[reveal: v-039]
[pause: 0.45]
C: One, report: positions every two seconds and health every thirty, including buffered backlogs.
[reveal: v-040]
[pause: 0.45]
C: Two, watch: a live map of any area at any zoom, within two seconds.
[reveal: v-041]
[pause: 0.45]
C: Three, replay: one vehicle's exact positions for any window in two years.
[reveal: v-042]
[pause: 0.45]
C: Four, alert: safety events to dispatch within a second.
[pause: 0.8]

[slide: v-043]
[pause: 0.6]
C: The numbers.
[reveal: v-044]
[pause: 0.45]
C: Two seconds from receipt to the map.
[reveal: v-045]
[pause: 0.45]
C: One second for a safety event.
[reveal: v-046]
[pause: 0.45]
C: Every received position in the history.
[reveal: v-047]
[pause: 0.45]
C: Ten seconds to replay one vehicle's hour.
[reveal: v-048]
[pause: 0.45]
C: The map may drop a point. The history may not.
[pause: 0.8]

[slide: v-049]
[pause: 0.6]
C: In scope: the uplink on the vehicle, ingest, the live map, history, replay and safety alerts.
[reveal: v-050]
[pause: 0.45]
C: Out, on purpose: raw camera and lidar logs, which are question ninety-eight's input; routing; dispatching jobs; and the control plane, question twenty-nine.
[reveal: v-051]
[pause: 0.45]
C: The control plane and this data plane share the gateway and the identity, not the stores.
[pause: 0.8]

[slide: v-052]
[pause: 1.3]
C: The context.
[reveal: v-053]
[pause: 0.45]
C: Vehicles send positions and health.
[reveal: v-054]
[pause: 0.45]
C: The system, one box.
[reveal: v-055]
[pause: 0.45]
C: Operators watch the live map.
[reveal: v-056]
[pause: 0.45]
C: Dispatch receives safety events.
[reveal: v-057]
[pause: 0.45]
C: Analysts and machine learning replay and export history.
[pause: 1.1]

[slide: v-058]
[pause: 0.7]
V: The core is three things. A log keyed by vehicle. An overwrite view by cell. And an append history by vehicle.
[pause: 1.6]

[pause: 1.4]

## 2 Estimates

[slide: v-059]
[pause: 1.2]
C: Numbers, from the scale line. Illustrative.
[pause: 1.8]

[slide: v-060]
[pause: 1.0]
C: Ingest and storage.
[reveal: v-061]
[pause: 0.45]
C: A million positions a second at three hundred bytes is three hundred megabytes a second, nine hundred with replication. Five hundred and twelve partitions, keyed by vehicle.
[reveal: v-062]
[pause: 0.45]
C: At an average of four hundred thousand a second, a month is about a trillion positions.
[reveal: v-063]
[pause: 0.45]
C: At about fifty bytes each in compressed columns, fifty-two terabytes a month, one and a quarter petabytes for two years. Object storage.
[reveal: v-064]
[pause: 0.45]
C: And the live state: two million vehicles at two hundred bytes is four hundred megabytes. Memory.
[pause: 1.0]

[slide: v-065]
[pause: 1.0]
C: The map and the flush.
[reveal: v-066]
[pause: 0.45]
C: At city zoom, a viewer sees about a hundred resolution-seven cells as counts each second. Counts, not dots.
[reveal: v-067]
[pause: 0.45]
C: At street zoom downtown, about two thousand vehicles, four hundred of them moving each second: send the deltas.
[reveal: v-068]
[pause: 0.45]
C: The flush: a hundred thousand vehicles times ninety buffered positions is nine million messages; spread over a minute, a hundred and fifty thousand a second on top of a million. Latest first, backfill capped.
[reveal: v-069]
[pause: 0.45]
C: And safety: about ten events a second fleet-wide, in their own lane.
[pause: 1.0]

[slide: v-070]
[pause: 1.0]
C: The buffer on the vehicle, because half the design depends on it.
[reveal: v-071]
[pause: 0.45]
C: Every two seconds is eighteen hundred positions an hour; six hours is about eleven thousand.
[reveal: v-072]
[pause: 0.45]
C: At three hundred bytes each, about three megabytes. Cheap enough to keep six hours.
[reveal: v-073]
[pause: 0.45]
C: But flash wears out, so positions are written in pages every thirty seconds, a hundred and twenty writes an hour, not one per fix.
[pause: 1.0]

[slide: v-074]
[pause: 1.3]
C: The freshness budget, from the moment we receive a position. A third of a second through the gateway and the log. A third through the state updater. Up to a second waiting for the map's push tick. About one point six of two seconds.
C: Sampling on the vehicle adds up to two seconds before that, which the operator sees as the dot's own age.
[pause: 1.1]

[pause: 1.4]

## 3 Theory

[slide: v-075]
[pause: 1.2]
C: The theory: five mechanisms, most of them borrowed, then the options.
[pause: 1.8]

[slide: v-076]
[pause: 0.6]
C: What it is.
[reveal: v-077]
[pause: 0.45]
V: Keeping, from one per-vehicle stream, a latest-state view by place and a complete history by vehicle.
[reveal: v-078]
[pause: 0.45]
C: Not ride matching: nothing is claimed here, only shown.
[reveal: v-079]
[pause: 0.45]
C: Not metrics: positions are events with identity, not counters.
[reveal: v-080]
[pause: 0.45]
C: And not the control plane: that changes devices; this only listens.
[pause: 0.8]

[slide: v-081]
[pause: 0.6]
C: Safety.
[reveal: v-082]
[pause: 0.45]
V: S-one: the map never moves a vehicle backwards to an older position than it has shown.
[reveal: v-083]
[pause: 0.45]
V: S-two: every received position is in history, exactly once.
[reveal: v-084]
[pause: 0.45]
C: Liveness. L-one: on the map within two seconds.
[reveal: v-085]
[pause: 0.45]
C: L-two: a safety event reaches dispatch within a second, even during a flush.
[pause: 0.8]

[slide: v-086]
[pause: 0.6]
C: Mechanism one, borrowed from question three: one log, two views.
[reveal: v-087]
[pause: 0.45]
C: It protects freshness and completeness at once.
[reveal: v-088]
[pause: 0.45]
C: Every position is appended once. One consumer overwrites a latest view; another appends history.
[reveal: v-089]
[pause: 0.45]
C: It rules out one store that's slow for the map and lossy for history.
[reveal: v-090]
[pause: 0.45]
C: It costs two consumers, and a history a few minutes behind the map.
[pause: 0.8]

[slide: v-091]
[pause: 1.3]
C: Mechanism one at protocol level.
[reveal: v-092]
[pause: 0.45]
C: The lake receives every position, appended in five-minute files.
[reveal: v-093]
[pause: 0.45]
C: The state updater receives the same positions.
[reveal: v-094]
[pause: 0.45]
C: It keeps only the newest per vehicle.
[reveal: v-095]
[pause: 0.45]
C: And overwrites the live store: latest wins.
[reveal: v-096]
[pause: 0.45]
C: In the lake nothing is ever overwritten.
[pause: 1.1]

[slide: v-097]
[pause: 0.6]
C: Mechanism two, borrowed from twenty-nine and thirty-nine: per-vehicle order and sequence numbers.
[reveal: v-098]
[pause: 0.45]
C: It protects S-one and S-two.
[reveal: v-099]
[pause: 0.45]
C: The vehicle numbers every message from a counter in flash. The log is keyed by vehicle, so one vehicle's messages stay in order on one partition. Views compare sequence numbers, never arrival times.
[reveal: v-100]
[pause: 0.45]
C: It rules out a buffered old position overwriting a new one, and duplicates after a resend.
[reveal: v-101]
[pause: 0.45]
C: It costs a counter that survives reboots.
[pause: 0.8]

[slide: v-102]
[pause: 0.6]
C: Mechanism three, from thirty-nine: cells, at several resolutions.
[reveal: v-103]
[pause: 0.45]
C: It protects map freshness.
[reveal: v-104]
[pause: 0.45]
C: Vehicles are indexed by resolution-nine cells, with counts kept at resolutions six and seven. A viewport picks the resolution from its zoom.
[reveal: v-105]
[pause: 0.45]
C: It rules out sending two hundred thousand dots to a city-zoom map.
[reveal: v-106]
[pause: 0.45]
C: It costs a count per coarse cell, updated with every move.
[pause: 0.8]

[slide: v-107]
[pause: 0.6]
C: Mechanism four, from twenty-nine: lanes and backpressure.
[reveal: v-108]
[pause: 0.45]
C: It protects L-two and L-one.
[reveal: v-109]
[pause: 0.45]
C: On reconnect, the vehicle sends safety events first, then its latest position, then the backfill, oldest first, at a capped rate.
[reveal: v-110]
[pause: 0.45]
C: It rules out a three-minute backlog delaying the present, and safety events queued behind history.
[reveal: v-111]
[pause: 0.45]
C: It costs a little delay for the backfill.
[pause: 0.8]

[slide: v-112]
[pause: 0.6]
C: Mechanism five: subscriptions by cell.
[reveal: v-113]
[pause: 0.45]
C: It protects freshness for five thousand viewers.
[reveal: v-114]
[pause: 0.45]
C: A viewport subscribes to the cells it covers, and each tick the server pushes only what changed in them.
[reveal: v-115]
[pause: 0.45]
C: It rules out five thousand clients polling the hottest cells every second.
[reveal: v-116]
[pause: 0.45]
C: It costs subscription state per viewer, and a snapshot on every pan.
[pause: 0.8]

[slide: v-117]
[pause: 1.0]
C: Before the options, the seams, explicitly.
[reveal: v-118]
[pause: 0.45]
C: From question three: one log with a hot path and a cold path, and dedup by an I-D. Here the hot path overwrites instead of counting.
[reveal: v-119]
[pause: 0.45]
C: From question thirty-nine: the in-memory H-three index and soft state. Here at resolution nine, with counts at six and seven, and subscribers.
[reveal: v-120]
[pause: 0.45]
C: From question twenty-nine: identity, the gateway, store-and-forward and backoff. Here the backoff becomes lanes for data.
[reveal: v-121]
[pause: 0.45]
C: And from question ninety-eight: a history pinned by snapshot, laid out here for one vehicle instead of for scenarios. Saying this out loud in the room is the composition signal.
[pause: 1.0]

[slide: v-122]
[pause: 1.0]
C: Five ways.
[reveal: v-123]
[pause: 0.45]
C: A, one database table: a million writes a second and a bounding-box scan per viewer.
[reveal: v-124]
[pause: 0.45]
C: B, a log and a lake only: the map is minutes behind.
[reveal: v-125]
[pause: 0.45]
C: C, a live store only: no audit, no replay.
[reveal: v-126]
[pause: 0.45]
C: D, a log keyed by geo cell: hot partitions downtown, and a vehicle crossing a cell boundary changes partitions and loses its order.
[reveal: v-127]
[pause: 0.45]
C: E, which I pick: a log by vehicle, read into a live view by cell and a history by vehicle, with lanes and subscriptions.
[reveal: v-128]
[pause: 0.45]
V: Key by what must stay in order. Index by what you query.
[pause: 1.0]

[slide: v-129]
[pause: 1.0]
C: The failure catalogue.
[reveal: v-130]
[pause: 0.45]
C: One: a vehicle leaves a tunnel with three minutes of buffer.
[reveal: v-131]
[pause: 0.45]
C: Two: downtown at six, two thousand vehicles in one view.
[reveal: v-132]
[pause: 0.45]
C: Three: five thousand operators watching at once.
[reveal: v-133]
[pause: 0.45]
C: Four: a city's network recovers, and a hundred thousand vehicles flush.
[reveal: v-134]
[pause: 0.45]
C: Five: an audit wants one vehicle's hour, exactly.
[reveal: v-135]
[pause: 0.45]
C: Six: the map is forty seconds stale, and nothing says so.
[pause: 1.0]

[pause: 1.4]

## 4 API and entities

[slide: v-136]
[pause: 1.2]
C: The interfaces, then the data.
[pause: 1.8]

[slide: v-137]
[pause: 1.0]
C: A position on the wire, for F-R-one. About three hundred bytes with headers.
C: Three fields matter. The sequence number and epoch: the vehicle's own order, surviving reboots. The time the vehicle took the fix, which the history keeps and the map displays as age, but which never decides what's newer. And the lane: latest, backfill or safety, which tells the server how the message was scheduled.
[pause: 1.0]

[slide: v-138]
[pause: 1.0]
C: A health summary, every thirty seconds. Notice it's a summary over a window, not a stream of raw readings: battery, temperature, G-P-S fix, signal strength, and any faults. Raw sensor logs are question ninety-eight's input and travel another way.
C: It shares the position's sequence counter, so the same ordering and deduplication rules apply to everything a vehicle sends.
[pause: 1.0]

[slide: v-139]
[pause: 1.0]
C: Three more.
[reveal: v-140]
[pause: 0.45]
C: The map socket, for F-R-two: a viewport and a zoom in; a snapshot, then deltas or counts each second, out.
[reveal: v-141]
[pause: 0.45]
C: A vehicle's track, for F-R-three: every fix in a window, ordered by sequence, read at a pinned snapshot so the answer doesn't change under the auditor.
[reveal: v-142]
[pause: 0.45]
C: And safety events, for F-R-four, on their own topic, straight to dispatch.
[pause: 1.0]

[slide: v-143]
[pause: 1.3]
C: The conceptual model.
[reveal: v-144]
[pause: 0.45]
C: A vehicle.
[reveal: v-145]
[pause: 0.45]
C: It reports positions: a weak entity identified by the vehicle and a sequence number, with a time and a place.
[reveal: v-146]
[pause: 0.45]
C: Each position is in one cell.
[reveal: v-147]
[pause: 0.45]
C: A vehicle raises safety events, also numbered.
[reveal: v-148]
[pause: 0.45]
C: Positions belong to trips.
[reveal: v-149]
[pause: 0.45]
C: And a viewport covers many cells, which is how the map knows what to send.
[pause: 1.1]

[slide: v-150]
[pause: 1.3]
C: The physical side.
[reveal: v-151]
[pause: 0.45]
C: Positions in Iceberg: partitioned by day and vehicle bucket, sorted by vehicle and sequence. Fifty-two terabytes a month.
[reveal: v-152]
[pause: 0.45]
C: Safety events in their own table.
[reveal: v-153]
[pause: 0.45]
C: The live view in memory: vehicle to cell, cell to vehicles, and counts at coarser resolutions.
[reveal: v-154]
[pause: 0.45]
C: The updater's keyed state: the last sequence per vehicle, checkpointed.
[reveal: v-155]
[pause: 0.45]
C: Subscriptions in memory, per map pod.
[reveal: v-156]
[pause: 0.45]
C: And the vehicle registry, shared with question twenty-nine.
[pause: 1.1]

[pause: 1.4]

## 5 High-level design

[slide: v-157]
[pause: 1.2]
C: The design in three versions, on one picture.
[pause: 1.8]

[slide: v-158]
[pause: 1.3]
C: Version one, the simplest thing that's complete.
[reveal: v-159]
[pause: 0.45]
C: The vehicle uplink sends positions.
[reveal: v-160]
[pause: 0.45]
C: To a telemetry gateway.
[reveal: v-161]
[pause: 0.45]
C: Appended to a log keyed by vehicle.
[reveal: v-162]
[pause: 0.45]
C: Landed in a history lake every five minutes.
[reveal: v-163]
[pause: 0.45]
C: A map A-P-I queries the lake.
[reveal: v-164]
[pause: 0.45]
C: For the operator. The objection: the map is minutes behind, and every viewport is a scan.
[pause: 1.1]

[slide: v-165]
[pause: 1.3]
C: Version two.
[reveal: v-166]
[pause: 0.45]
C: Version one, carried.
[reveal: v-167]
[pause: 0.45]
C: New, a state updater: a stream job keyed by vehicle that keeps only newer sequence numbers.
[reveal: v-168]
[pause: 0.45]
C: New, a live store by cell, in memory; the map reads it. That's question three's split: the same log, a hot path and a cold one. The objection: a safety event waits behind everything, and nobody can replay an hour precisely.
[pause: 1.1]

[slide: v-169]
[pause: 1.3]
C: Version three.
[reveal: v-170]
[pause: 0.45]
C: Version two, carried.
[reveal: v-171]
[pause: 0.45]
C: New, a safety lane: its own topic, never behind positions.
[reveal: v-172]
[pause: 0.45]
C: Straight to dispatch.
[reveal: v-173]
[pause: 0.45]
C: New, a replay A-P-I over the lake, built for one vehicle's window.
[reveal: v-174]
[pause: 0.45]
C: For analysts and training. This is the baseline.
[pause: 1.1]

[slide: v-175]
[pause: 1.0]
C: The containers.
[reveal: v-176]
[pause: 0.45]
C: The uplink: the buffer, the lanes and the backoff.
[reveal: v-177]
[pause: 0.45]
C: The gateway: identity, sessions and topics, a million messages a second.
[reveal: v-178]
[pause: 0.45]
C: The log: order per vehicle.
[reveal: v-179]
[pause: 0.45]
C: The state updater: the newest per vehicle.
[reveal: v-180]
[pause: 0.45]
C: The live store and map A-P-I: now, by cell, and five thousand viewers' subscriptions.
[reveal: v-181]
[pause: 0.45]
C: The lake and replay: everything, by vehicle.
[pause: 1.0]

[slide: v-182]
[pause: 1.0]
C: Before the flows, every place a position can wait, because each is a freshness risk.
[reveal: v-183]
[pause: 0.45]
C: The vehicle's buffer, six hours: when it fills, drop the oldest and count it.
[reveal: v-184]
[pause: 0.45]
C: The gateway session's in-flight window: a slow broker makes the vehicle back off.
[reveal: v-185]
[pause: 0.45]
C: The log, three days: a stalled consumer shows as lag, and pages.
[reveal: v-186]
[pause: 0.45]
C: The updater's keyed state: a restart resumes from its checkpoint.
[reveal: v-187]
[pause: 0.45]
C: And the map push, one tick: a slow browser gets its deltas dropped and a fresh snapshot instead. Nothing waits without a bound.
[pause: 1.0]

[slide: v-188]
[pause: 1.3]
C: The live path, numbered.
[reveal: v-189]
[pause: 0.45]
C: One: the uplink publishes.
[reveal: v-190]
[pause: 0.45]
C: Two: appended, keyed by vehicle.
[reveal: v-191]
[pause: 0.45]
C: Three: the updater consumes in order.
[reveal: v-192]
[pause: 0.45]
C: Four: it overwrites the live store if newer.
[reveal: v-193]
[pause: 0.45]
C: Five: the operator's viewport.
[reveal: v-194]
[pause: 0.45]
C: Six: the map reads cells and pushes changes.
[pause: 1.1]

[slide: v-195]
[pause: 1.3]
C: The history path, numbered.
[reveal: v-196]
[pause: 0.45]
C: One and two: the same publish and append.
[reveal: v-197]
[pause: 0.45]
C: The same, the log.
[reveal: v-198]
[pause: 0.45]
C: Three: landed in the lake every five minutes.
[reveal: v-199]
[pause: 0.45]
C: Four: an analyst asks for a window.
[reveal: v-200]
[pause: 0.45]
C: Five: the replay A-P-I reads one bucket.
[pause: 1.1]

[slide: v-201]
[pause: 1.3]
C: Report, as a sequence.
[reveal: v-202]
[pause: 0.45]
C: Vehicle three-eleven, sequence nine thousand four hundred and two.
[reveal: v-203]
[pause: 0.45]
C: Appended, keyed by the vehicle.
[reveal: v-204]
[pause: 0.45]
C: Delivered in order for that vehicle.
[reveal: v-205]
[pause: 0.45]
C: Newer than nine four oh one.
[reveal: v-206]
[pause: 0.45]
C: The live store moves the vehicle to its new cell.
[pause: 1.1]

[slide: v-207]
[pause: 1.3]
C: Watch, as a sequence.
[reveal: v-208]
[pause: 0.45]
C: An operator opens downtown at zoom fifteen.
[reveal: v-209]
[pause: 0.45]
C: Zoom fifteen means resolution nine: forty-eight cells.
[reveal: v-210]
[pause: 0.45]
C: A snapshot of those cells.
[reveal: v-211]
[pause: 0.45]
C: Nineteen hundred and thirty vehicles.
[reveal: v-212]
[pause: 0.45]
C: Then changes in those cells.
[reveal: v-213]
[pause: 0.45]
C: Every second, the four hundred that moved.
[pause: 1.1]

[slide: v-214]
[pause: 1.3]
C: Replay, as a sequence.
[reveal: v-215]
[pause: 0.45]
C: Vehicle three-eleven, two to three p.m., the third of November.
[reveal: v-216]
[pause: 0.45]
C: The day and the bucket: hash of the vehicle, mod two-fifty-six.
[reveal: v-217]
[pause: 0.45]
C: One bucket at a snapshot, a range of sequence numbers.
[reveal: v-218]
[pause: 0.45]
C: Eighteen hundred positions, sorted.
[reveal: v-219]
[pause: 0.45]
C: The hour, including every fix that arrived late.
[pause: 1.1]

[slide: v-220]
[pause: 1.3]
C: Alert, as a sequence.
[reveal: v-221]
[pause: 0.45]
C: The vehicle detects a hard brake and skips its queue.
[reveal: v-222]
[pause: 0.45]
C: A safety message.
[reveal: v-223]
[pause: 0.45]
C: On the safety topic.
[reveal: v-224]
[pause: 0.45]
C: Dispatch is paged within a second, whatever else is flushing.
[pause: 1.1]

[pause: 1.4]

## 5.1 Components and technologies

[slide: v-225]
[pause: 1.2]
C: One level down: what each box runs on, three containers opened up, and what I rejected.
[pause: 1.8]

[slide: v-226]
[pause: 1.3]
C: The same view, with technologies.
[reveal: v-227]
[pause: 0.45]
C: The uplink: C-plus-plus on the vehicle.
[reveal: v-228]
[pause: 0.45]
C: The gateway: E-M-Q-X, MQTT five, mutual T-L-S.
[reveal: v-229]
[pause: 0.45]
C: The log: Kafka, keyed by vehicle.
[reveal: v-230]
[pause: 0.45]
C: The updater: Flink, keyed by vehicle.
[reveal: v-231]
[pause: 0.45]
C: The live store: the in-memory H-three index from question thirty-nine.
[reveal: v-232]
[pause: 0.45]
C: The map A-P-I: Go with WebSockets.
[reveal: v-233]
[pause: 0.45]
C: The lake: Iceberg on Google Cloud Storage.
[reveal: v-234]
[pause: 0.45]
C: And replay: Trino over Iceberg.
[pause: 1.1]

[slide: v-235]
[pause: 1.3]
C: Inside the uplink.
[reveal: v-236]
[pause: 0.45]
C: GPS and sensors.
[reveal: v-237]
[pause: 0.45]
C: The sampler: every two seconds moving, thirty parked.
[reveal: v-238]
[pause: 0.45]
C: A safety detector that skips the queue.
[reveal: v-239]
[pause: 0.45]
C: A ring buffer in flash: six hours, a sequence per message.
[reveal: v-240]
[pause: 0.45]
C: The scheduler with three lanes: safety, latest, backfill.
[reveal: v-241]
[pause: 0.45]
C: A rate cap on backfill.
[reveal: v-242]
[pause: 0.45]
C: The MQTT client with jittered backoff.
[reveal: v-243]
[pause: 0.45]
C: To the gateway. Challenge four lives here.
[pause: 1.1]

[slide: v-244]
[pause: 1.3]
C: Inside the state updater.
[reveal: v-245]
[pause: 0.45]
C: The log.
[reveal: v-246]
[pause: 0.45]
C: The source, per partition, in order.
[reveal: v-247]
[pause: 0.45]
C: The sequence filter: the last sequence per vehicle, in keyed state.
[reveal: v-248]
[pause: 0.45]
C: Older positions go to a side output: history only.
[reveal: v-249]
[pause: 0.45]
C: The cell mapper: has the vehicle changed cell?
[reveal: v-250]
[pause: 0.45]
C: The live writer, only if newer.
[reveal: v-251]
[pause: 0.45]
C: Into the live store. Challenge one lives here.
[pause: 1.1]

[slide: v-252]
[pause: 1.3]
C: Inside the map A-P-I.
[reveal: v-253]
[pause: 0.45]
C: The operator's browser.
[reveal: v-254]
[pause: 0.45]
C: The viewport tracker turns zoom into a resolution, and the view into cells.
[reveal: v-255]
[pause: 0.45]
C: Subscriptions to only those cells.
[reveal: v-256]
[pause: 0.45]
C: A snapshot loader, on every pan.
[reveal: v-257]
[pause: 0.45]
C: The aggregator: counts when zoomed out.
[reveal: v-258]
[pause: 0.45]
C: The delta pusher, every second.
[reveal: v-259]
[pause: 0.45]
C: Fed by the live store's change feed. Challenges two and three live here.
[pause: 1.1]

[slide: v-260]
[pause: 1.0]
C: Topic positions, partition = hash(vehicle); a separate safety topic. Three days on the brokers.
[reveal: v-261]
[pause: 0.45]
C: Why: Even load, and each vehicle's messages in order on one partition.
[reveal: v-262]
[pause: 0.45]
C: Rejected: Keying by geo cell. Hot partitions.
[reveal: v-263]
[pause: 0.45]
C: Google Pub/Sub. An honest equal with ordering keys.
[pause: 1.0]

[slide: v-264]
[pause: 1.0]
C: vehicle to (cell, position, seq) and cell to vehicles, with per-cell change counters. Older seq is dropped.
[reveal: v-265]
[pause: 0.45]
C: Why: Only the latest matters, and 2 M vehicles fit in 400 MB.
[reveal: v-266]
[pause: 0.45]
C: Rejected: Redis GEO. No per-cell change feed, no expiry per member.
[reveal: v-267]
[pause: 0.45]
C: The history lake. Minutes behind, built for scans.
[pause: 1.0]

[slide: v-268]
[pause: 1.0]
C: A viewport maps to cells at its zoom's resolution; each second the server pushes changes, or counts when zoomed out.
[reveal: v-269]
[pause: 0.45]
C: Why: Deltas for subscribed cells cost far less than every client polling.
[reveal: v-270]
[pause: 0.45]
C: Rejected: Polling a bounding box. 5,000 scans of the hottest cells a second.
[reveal: v-271]
[pause: 0.45]
C: Every vehicle in view. 200,000 points at city zoom.
[pause: 1.0]

[slide: v-272]
[pause: 1.0]
C: Partitioned by (event day, hash(vehicle) mod 256), sorted by vehicle and seq; late positions go to their event day.
[reveal: v-273]
[pause: 0.45]
C: Why: One vehicle's hour becomes one bucket and a range read.
[reveal: v-274]
[pause: 0.45]
C: Rejected: Arrival-hour partitions. One replay scans everyone.
[reveal: v-275]
[pause: 0.45]
C: A time-series database. Not for 10¹² positions with per-vehicle replay.
[pause: 1.0]

[slide: v-276]
[pause: 1.0]
C: The stack on one slide, as I would leave it on the whiteboard.
[reveal: v-277]
[pause: 0.45]
C: Telemetry log: Kafka by vehicle ID. Not keyed by cell, Pub/Sub. Per-vehicle order; even load.
[reveal: v-278]
[pause: 0.45]
C: Live store: in-memory H3, per city. Not Redis GEO, the lake. Latest only; per-cell change feed.
[reveal: v-279]
[pause: 0.45]
C: Map API: WebSockets, cell subscriptions. Not polling, all points. Deltas per cell; counts when zoomed out.
[reveal: v-280]
[pause: 0.45]
C: History lake: Iceberg, day times bucket. Not ingest-hour partitions, TSDB. One vehicle's hour is a range read.
[reveal: v-281]
[pause: 0.45]
N: Naming a product is not the signal. Naming the property that rules out its rival is. Interviewers go one level down on whichever box you name, so name only what you can defend.
[pause: 1.0]

[pause: 1.4]

## 5.2 When you don't need all this

[slide: v-282]
[pause: 1.2]
C: Before I break it: a small fleet needs one database.
[pause: 1.8]

[slide: v-283]
[pause: 1.3]
C: The alternate path, on version two.
[reveal: v-284]
[pause: 0.45]
C: The log goes.
[reveal: v-285]
[pause: 0.45]
C: The state updater.
[reveal: v-286]
[pause: 0.45]
C: And the live store.
[reveal: v-287]
[pause: 0.45]
C: Instead, each position upserts a latest row if its sequence is newer, and appends to a history table partitioned by day. The map queries the latest table by bounding box with PostGIS.
[reveal: v-288]
[pause: 0.45]
C: What it gives up: one database for both jobs, no lanes, polling maps, and the history in one box.
[pause: 1.1]

[slide: v-289]
[pause: 0.7]
C: The line. Five thousand vehicles every two seconds is twenty-five hundred writes a second, twice. One database copes. Two million is a million a second.
V: Below about five thousand vehicles, I'd ship PostgreSQL, keep the sequence numbers and the lanes on the vehicle, and say when I'd switch.
[pause: 1.6]

[pause: 1.4]

## 6 Bridge

[slide: v-290]
[pause: 1.2]
V: It works. The question now is where it breaks first.
[pause: 1.8]

[slide: v-291]
[pause: 1.3]
C: Version three, with the places it breaks.
[reveal: v-292]
[pause: 0.45]
C: The state updater: a vehicle leaving a tunnel. Challenge one.
[reveal: v-293]
[pause: 0.45]
C: The log and its key, under a dense downtown. Challenge two.
[reveal: v-294]
[pause: 0.45]
C: The map A-P-I, with five thousand viewers. Challenge three.
[reveal: v-295]
[pause: 0.45]
C: The uplink, when a whole city reconnects. Challenge four.
[reveal: v-296]
[pause: 0.45]
C: And the lake, when an audit wants one hour exactly. Challenge five. Then: how would we know the map is stale?
[pause: 1.1]

[pause: 1.4]

## 7 Challenges

[slide: v-297]
[pause: 1.2]
C: Six challenges, each the same way: the question, the naive answer, a case with numbers, where it breaks inside the container, the fix one level down, then the push on the fix itself, and what I would say in the room.
[pause: 1.8]

[pause: 1.4]

## 7.1 Challenge 1: Out of the tunnel

[slide: v-298]
[pause: 1.2]
N: Challenge one is the crux: old data arriving after new data.
[pause: 1.8]

[slide: v-299]
[pause: 0.6]
I: A vehicle leaves a tunnel with three minutes of buffered positions. What does the map show, and what does the history get?
[pause: 2.0]

[slide: v-300]
[pause: 1.3]
C: Inside the state updater.
[reveal: v-301]
[pause: 0.45]
C: The live writer is marked.
[reveal: v-302]
[pause: 0.45]
C: The naive answer: write each position to the map as it arrives.
[reveal: v-303]
[pause: 0.45]
C: Then the backlog arrives after the fresh position, and the car on the map jumps back into the tunnel and drives its last three minutes again.
[pause: 1.1]

[slide: v-304]
[pause: 1.0]
C: The trace.
[reveal: v-305]
[pause: 0.45]
C: The car exits the tunnel and sends its current position, sequence nine four oh two.
[reveal: v-306]
[pause: 0.45]
C: Then ninety buffered positions, nine three one two to nine four oh one.
[reveal: v-307]
[pause: 0.45]
C: In arrival order, the map moves the car two kilometres back into the tunnel.
[reveal: v-308]
[pause: 0.45]
C: An operator dispatches help to a car that's fine.
[reveal: v-309]
[pause: 0.45]
C: And the history needs all ninety, in their own minutes, exactly once.
[pause: 1.0]

[slide: v-310]
[pause: 1.3]
C: The fix.
[reveal: v-311]
[pause: 0.45]
C: The sequence filter.
[reveal: v-312]
[pause: 0.45]
C: And the live writer.
[reveal: v-313]
[pause: 0.45]
C: One level down. Keyed state holds the last sequence number per vehicle. A position with a sequence at or below it goes to the history side output only. The live writer overwrites only with a newer sequence. And the lake deduplicates by vehicle, epoch and sequence, so a resend is one row.
[reveal: v-314]
[pause: 0.45]
C: It covers backlogs, resends and reordering. Not a vehicle whose counter reset without a new epoch; that's a firmware bug, and question twenty-nine's census catches it.
[reveal: v-315]
[pause: 0.45]
C: Rejected: writing every arriving position to the live store. A three-minute-old fix overwrites the position from one second ago.
[pause: 1.1]

[slide: v-316]
[pause: 1.0]
C: Why not just use timestamps?
[reveal: v-317]
[pause: 0.45]
C: Arrival time fails as soon as a backlog arrives after the present.
[reveal: v-318]
[pause: 0.45]
C: The vehicle's own timestamp fails when its clock jumps, after a G-P-S fix corrects it or after a reboot, and two fixes can share a millisecond.
[reveal: v-319]
[pause: 0.45]
C: Server receipt time is arrival time again.
[reveal: v-320]
[pause: 0.45]
C: A sequence number and an epoch, kept in flash, never fail that way: incremented once per message, surviving reboots. Time is displayed; the sequence decides.
[pause: 1.0]

[slide: v-321]
[pause: 1.3]
C: As a sequence.
[reveal: v-322]
[pause: 0.45]
C: Leaving the tunnel with ninety positions buffered.
[reveal: v-323]
[pause: 0.45]
C: The latest lane goes first: nine four oh two.
[reveal: v-324]
[pause: 0.45]
C: The car jumps forward to where it really is.
[reveal: v-325]
[pause: 0.45]
C: Then the backfill.
[reveal: v-326]
[pause: 0.45]
C: Older than nine four oh two: not live.
[reveal: v-327]
[pause: 0.45]
C: All ninety into history, each in its own minute.
[pause: 1.1]

[slide: v-328]
[pause: 0.6]
I: The updater restarts and loses its state.
[pause: 1.5]

[slide: v-329]
[pause: 0.6]
C: The last-sequence state is checkpointed with the Kafka offsets, so a restart resumes exactly where it was.
[reveal: v-330]
[pause: 0.45]
C: And the live store compares sequence numbers on write too. Even an empty filter can't move a car backwards: S-one is enforced in two places.
[pause: 0.8]

[slide: v-331]
[pause: 0.7]
V: If asked, I'd say: order comes from the vehicle, not from arrival. Every message carries a sequence number; the live view overwrites only with a newer one, and the history takes everything, deduplicated by vehicle and sequence. And the vehicle sends its latest position before its backlog.
[pause: 1.0]
N: That fix creates the next question: order per vehicle needs the log keyed by vehicle. What does that do downtown?
[pause: 1.6]

[pause: 1.4]

## 7.2 Challenge 2: Downtown at six

[slide: v-332]
[pause: 1.2]
N: Challenge two: density, on the log and on the map.
[pause: 1.8]

[slide: v-333]
[pause: 0.6]
I: Downtown at six there are two thousand vehicles in one operator's view. Why not key the log by geo cell? And what does the operator actually see?
[pause: 2.0]

[slide: v-334]
[pause: 1.3]
C: Inside the map A-P-I.
[reveal: v-335]
[pause: 0.45]
C: The aggregator is marked.
[reveal: v-336]
[pause: 0.45]
C: The naive answer: key the log by cell, so the map reads one partition, and send every vehicle in view.
[reveal: v-337]
[pause: 0.45]
C: Then a city-zoom map gets two hundred thousand dots a second, and a cell-keyed log puts all of downtown on one partition.
[pause: 1.1]

[slide: v-338]
[pause: 1.0]
C: The trace.
[reveal: v-339]
[pause: 0.45]
C: With the log keyed by cell, downtown's partition takes forty percent of the traffic.
[reveal: v-340]
[pause: 0.45]
C: One consumer lags, and all of downtown is thirty seconds behind.
[reveal: v-341]
[pause: 0.45]
C: A car crosses into the next cell, and its next messages land on another partition.
[reveal: v-342]
[pause: 0.45]
C: Two consumers race on one car, and it flickers.
[reveal: v-343]
[pause: 0.45]
C: A key that concentrates load, and a key that splits a vehicle's order.
[pause: 1.0]

[slide: v-344]
[pause: 1.3]
C: The fix.
[reveal: v-345]
[pause: 0.45]
C: The aggregator.
[reveal: v-346]
[pause: 0.45]
C: One level down. The log stays keyed by vehicle, for even load and per-vehicle order. The live store indexes resolution-nine cells and keeps counts at resolutions six and seven. A viewport at city zoom gets about a hundred counts a second; zoomed in to the street, it gets vehicles.
[reveal: v-347]
[pause: 0.45]
C: It covers hot areas and unreadable maps. Not two thousand vehicles in one block at street zoom; those are sent, and the browser clusters them.
[reveal: v-348]
[pause: 0.45]
C: Rejected: keying the log by geo cell. A stadium's cell becomes one hot partition, and vehicles lose their order as they move.
[pause: 1.1]

[slide: v-349]
[pause: 1.0]
C: Concretely, what a viewport receives by zoom.
[reveal: v-350]
[pause: 0.45]
C: At city zoom, resolution six: about thirty cells, sent as counts.
[reveal: v-351]
[pause: 0.45]
C: At district zoom, resolution seven: about a hundred cells, still counts.
[reveal: v-352]
[pause: 0.45]
C: At neighbourhood zoom, resolution nine: about two hundred cells of vehicles, which the browser clusters.
[reveal: v-353]
[pause: 0.45]
C: At street zoom, resolution nine or ten: about fifty cells, every vehicle. The payload stays roughly the same size at every zoom.
[pause: 1.0]

[slide: v-354]
[pause: 0.6]
I: A stadium empties: three thousand vehicles in one resolution-nine cell.
[pause: 1.5]

[slide: v-355]
[pause: 0.6]
C: The live store splits the cell, exactly as in question thirty-nine: over three hundred vehicles, it's indexed at resolution ten as well, and street zoom reads the finer cells.
[reveal: v-356]
[pause: 0.45]
C: And the log doesn't care: three thousand vehicles are three thousand keys spread over five hundred and twelve partitions. That's the point of keying by vehicle.
[pause: 0.8]

[slide: v-357]
[pause: 0.7]
V: If asked, I'd say: key by what must stay in order, and index by what you query. The log is keyed by vehicle, so load is even and each vehicle stays in order. The live store indexes cells, splits hot ones, and keeps coarse counts, so a zoomed-out map gets a hundred numbers, not two hundred thousand dots.
[pause: 1.0]
N: That fix creates the next question: five thousand people are looking at once.
[pause: 1.6]

[pause: 1.4]

## 7.3 Challenge 3: Five thousand viewers

[slide: v-358]
[pause: 1.2]
N: Challenge three: fan-out to the people watching.
[pause: 1.8]

[slide: v-359]
[pause: 0.6]
I: Five thousand operators keep the map open all day. How does each one stay within two seconds without melting the live store?
[pause: 2.0]

[slide: v-360]
[pause: 1.3]
C: Inside the map A-P-I.
[reveal: v-361]
[pause: 0.45]
C: The pusher is marked.
[reveal: v-362]
[pause: 0.45]
C: The naive answer: each browser polls its bounding box every second.
[reveal: v-363]
[pause: 0.45]
C: Then there's nothing to push: five thousand polls a second scan the hottest cells, mostly to find nothing changed.
[pause: 1.1]

[slide: v-364]
[pause: 1.0]
C: The trace.
[reveal: v-365]
[pause: 0.45]
C: Five thousand operators open the map, three thousand on the same three cities.
[reveal: v-366]
[pause: 0.45]
C: Each polls a bounding box every second.
[reveal: v-367]
[pause: 0.45]
C: The same downtown cells are scanned two thousand times a second.
[reveal: v-368]
[pause: 0.45]
C: The live store's C-P-U climbs, its own updates slow, and the map falls behind.
[reveal: v-369]
[pause: 0.45]
C: And at night most cells don't change in a second; the polls still run.
[pause: 1.0]

[slide: v-370]
[pause: 1.3]
C: The fix.
[reveal: v-371]
[pause: 0.45]
C: Subscriptions.
[reveal: v-372]
[pause: 0.45]
C: And the pusher.
[reveal: v-373]
[pause: 0.45]
C: One level down. A viewport becomes a set of cells at its zoom's resolution. The map pod subscribes to those cells' change feed from the live store, once per pod, however many viewers share a cell. Each second it pushes each viewer only what changed in their cells. A pan subscribes the new cells and sends their snapshot first.
[reveal: v-374]
[pause: 0.45]
C: It covers any number of viewers per cell: one feed, many sockets. Not a single viewer panning wildly, which costs a snapshot each time.
[reveal: v-375]
[pause: 0.45]
C: Rejected: clients polling a bounding box. Five thousand viewers scan the hottest cells every second.
[pause: 1.1]

[slide: v-376]
[pause: 1.0]
C: The same five thousand viewers, two ways.
[reveal: v-377]
[pause: 0.45]
C: Polling: five thousand scans of the live store a second. Subscriptions: one change feed per pod and cell.
[reveal: v-378]
[pause: 0.45]
C: Downtown, with three thousand viewers: three thousand scans of the same cells, against one feed fanned out to three thousand sockets.
[reveal: v-379]
[pause: 0.45]
C: And on a quiet night: five thousand scans finding nothing, against almost nothing sent.
[pause: 1.0]

[slide: v-380]
[pause: 0.6]
I: A map pod dies with eight hundred viewers.
[pause: 1.5]

[slide: v-381]
[pause: 0.6]
C: The browser resends its viewport to any pod, which rebuilds the subscriptions and sends a snapshot.
[reveal: v-382]
[pause: 0.45]
C: Eight hundred browsers reconnect with jitter over five seconds, not in one burst. The same lesson as the reconnect storm in question twenty-nine.
[pause: 0.8]

[slide: v-383]
[pause: 0.7]
V: If asked, I'd say: a viewport is a set of cells at its zoom. Map pods subscribe once per cell to the live store's change feed and push each viewer only what changed, every second. No browser polls, and a busy cell costs one feed however many people watch it.
[pause: 1.0]
N: That fix creates the next question: the map is fresh as long as vehicles can send. What if a whole city couldn't?
[pause: 1.6]

[pause: 1.4]

## 7.4 Challenge 4: A city comes back

[slide: v-384]
[pause: 1.2]
N: Challenge four: backpressure, decided on the vehicle.
[pause: 1.8]

[slide: v-385]
[pause: 0.6]
I: A city's cellular network was down for three minutes. A hundred thousand vehicles reconnect at once with full buffers. What happens to the map, and to a crash that happens right now?
[pause: 2.0]

[slide: v-386]
[pause: 1.3]
C: Inside the uplink.
[reveal: v-387]
[pause: 0.45]
C: The scheduler is marked.
[reveal: v-388]
[pause: 0.45]
C: The naive answer: send the buffer in order, as fast as possible.
[reveal: v-389]
[pause: 0.45]
C: Then every vehicle sends its oldest positions first. The map stays three minutes behind for the whole flush, and a crash that happens now waits behind ninety old positions.
[pause: 1.1]

[slide: v-390]
[pause: 1.0]
C: The trace.
[reveal: v-391]
[pause: 0.45]
C: The network returns, and a hundred thousand vehicles flush ninety positions each.
[reveal: v-392]
[pause: 0.45]
C: Nine million messages, oldest first, as fast as each vehicle can.
[reveal: v-393]
[pause: 0.45]
C: Twenty seconds later the city's map still shows three minutes ago.
[reveal: v-394]
[pause: 0.45]
C: A vehicle crashes; its event waits behind sixty queued positions, and dispatch hears thirty seconds late.
[reveal: v-395]
[pause: 0.45]
C: The present waits behind the past, and the urgent waits behind the routine.
[pause: 1.0]

[slide: v-396]
[pause: 1.3]
C: The fix.
[reveal: v-397]
[pause: 0.45]
C: The scheduler.
[reveal: v-398]
[pause: 0.45]
C: One level down. On reconnect, the scheduler sends safety events first, on their own topic. Then the newest position, on the latest lane, so the map is current within seconds. Then the backlog, oldest first, at no more than fifty messages a second per vehicle, and the cap halves if the broker answers retry-after. That's question twenty-nine's backoff, applied to data.
[reveal: v-399]
[pause: 0.45]
C: It covers outages, tunnels and a city-wide flush. Not a buffer that overflowed: past six hours the oldest positions are dropped, and the drop is counted and reported.
[reveal: v-400]
[pause: 0.45]
C: Rejected: flushing the buffer oldest first. The map stays three minutes behind for the whole flush, and safety events queue behind history.
[pause: 1.1]

[slide: v-401]
[pause: 1.0]
C: The flush, in numbers.
[reveal: v-402]
[pause: 0.45]
C: Safety: a handful, within a second of reconnecting.
[reveal: v-403]
[pause: 0.45]
C: Latest: one per vehicle, a hundred thousand, within a few seconds. The city's map is current almost at once.
[reveal: v-404]
[pause: 0.45]
C: Backfill: nine million, capped at fifty a second per vehicle, over about two minutes, into history only. The live path never sees it.
[pause: 1.0]

[slide: v-405]
[pause: 1.0]
C: The scheduler in pseudocode. Line two: safety first. Line three: the newest position, so the map catches up at once. Line six: the backlog at a capped rate. Line eight: a new safety event during the backfill jumps the queue again.
[pause: 1.0]

[slide: v-406]
[pause: 0.6]
I: And on the server side?
[pause: 1.5]

[slide: v-407]
[pause: 0.6]
C: The lanes continue on the server. Safety and positions are different topics with different consumers, so one can lag while the other can't.
[reveal: v-408]
[pause: 0.45]
C: And backfilled positions fail the sequence filter, so they go to history only. Nine million old messages cost the live store nothing.
[pause: 0.8]

[slide: v-409]
[pause: 0.7]
V: If asked, I'd say: the vehicle decides what goes first. Safety events, then the newest position, then the backlog, oldest first, at a capped rate that backs off when the broker asks. Backfill fails the sequence filter and goes only to history, so a city coming back online never delays the map or a crash.
[pause: 1.0]
N: That fix creates the next question: all of that backfill lands in history. Can you find it again?
[pause: 1.6]

[pause: 1.4]

## 7.5 Challenge 5: One vehicle, one hour

[slide: v-410]
[pause: 1.2]
N: Challenge five: history laid out for the question it will be asked.
[pause: 1.8]

[slide: v-411]
[pause: 0.6]
I: An incident review needs vehicle three-eleven's exact positions from two to three p.m. on the third of November, including what it buffered in a tunnel. How fast, and how sure?
[pause: 2.0]

[slide: v-412]
[pause: 1.3]
C: The lake and the replay A-P-I.
[reveal: v-413]
[pause: 0.45]
C: The lake is marked.
[reveal: v-414]
[pause: 0.45]
C: The naive answer: history is files by arrival hour; query them.
[reveal: v-415]
[pause: 0.45]
C: Then one vehicle's hour, including buffered fixes that arrived later, is spread over every file of two days, mixed with two million other vehicles.
[pause: 1.1]

[slide: v-416]
[pause: 1.0]
C: The trace.
[reveal: v-417]
[pause: 0.45]
C: Vehicle three-eleven drives, twenty minutes of it in a tunnel: six hundred positions buffered.
[reveal: v-418]
[pause: 0.45]
C: The buffer lands at twelve past three, in the three o'clock arrival files.
[reveal: v-419]
[pause: 0.45]
C: The reviewer queries two to three: twelve hundred positions, and a twenty-minute gap.
[reveal: v-420]
[pause: 0.45]
C: Finding the rest means scanning two days, about three and a half terabytes.
[reveal: v-421]
[pause: 0.45]
C: Two needs: find one vehicle cheaply, and include what arrived late.
[pause: 1.0]

[slide: v-422]
[pause: 1.3]
C: The fix.
[reveal: v-423]
[pause: 0.45]
C: The lake.
[reveal: v-424]
[pause: 0.45]
C: And replay.
[reveal: v-425]
[pause: 0.45]
C: One level down. Iceberg partitions by the event's day and by the vehicle's hash modulo two hundred and fifty-six, and files are sorted by vehicle and sequence. A late position is a new file in its event day, not in its arrival hour. A replay prunes to one day and one bucket, about two hundred and seventy gigabytes a month divided by thirty, and range-reads one vehicle, at a pinned snapshot so the answer can't change.
[reveal: v-426]
[pause: 0.45]
C: It covers late arrivals and one-vehicle audits in seconds. Not a whole-day training read; that scans all buckets, which is what it wants anyway.
[reveal: v-427]
[pause: 0.45]
C: Rejected: partitioning history by arrival time. A vehicle's hour is spread over every file that arrived late, and one replay scans everyone.
[pause: 1.1]

[slide: v-428]
[pause: 1.0]
C: The same lake has two kinds of reader.
[reveal: v-429]
[pause: 0.45]
C: An audit asks for one vehicle and one hour; training asks for every vehicle over a day or a week.
[reveal: v-430]
[pause: 0.45]
C: The audit reads one bucket and a range; training reads all two hundred and fifty-six buckets and only the columns it needs.
[reveal: v-431]
[pause: 0.45]
C: The audit cares about exactness, late fixes and a pinned snapshot; training cares about throughput and cost.
[reveal: v-432]
[pause: 0.45]
C: The bucket and sort order serve the audit; the columnar files and day partitions serve training. One layout, chosen so neither has to scan for the other.
[pause: 1.0]

[slide: v-433]
[pause: 1.0]
C: What the layout buys, in bytes.
[reveal: v-434]
[pause: 0.45]
C: By arrival hour, scanning: two days of everything, three and a half terabytes, an hour of cluster time.
[reveal: v-435]
[pause: 0.45]
C: By event day only: one day, one point seven terabytes. Minutes.
[reveal: v-436]
[pause: 0.45]
C: By day and one of two hundred and fifty-six buckets, sorted: one bucket of about seven gigabytes, and because it's sorted by vehicle, a range of about fifty megabytes inside it. About ten seconds.
[pause: 1.0]

[slide: v-437]
[pause: 1.0]
C: As pseudocode. Line one: pin a snapshot, so the auditor and a second reviewer see the same rows. Line three: one bucket out of two hundred and fifty-six. Line six: deduplicate by epoch and sequence. About ten seconds, and the same answer every time.
[pause: 1.0]

[slide: v-438]
[pause: 0.6]
I: A buffered position arrives after the audit ran.
[pause: 1.5]

[slide: v-439]
[pause: 0.6]
C: Re-running at a newer snapshot includes it, and the report records which snapshot each answer used. What we knew, and when, is part of the audit.
[reveal: v-440]
[pause: 0.45]
C: The honest limit: a vehicle offline longer than its six-hour buffer has gaps forever. The gap is reported, never interpolated into something that looks like data.
[pause: 0.8]

[slide: v-441]
[pause: 0.7]
V: If asked, I'd say: history is laid out for its question. It's partitioned by event day and a vehicle bucket, sorted by vehicle and sequence, and late positions are filed under the day they happened. One vehicle's hour is one bucket and a range read at a pinned snapshot: about ten seconds, and the same answer every time.
[pause: 1.0]
N: That fix creates the last question: how would you know the map itself is stale?
[pause: 1.6]

[pause: 1.4]

## 7.6 Challenge 6: Forty seconds stale

[slide: v-442]
[pause: 1.2]
N: Challenge six is observability, measured on the map.
[pause: 1.8]

[slide: v-443]
[pause: 0.6]
I: An operator notices a vehicle on the map is forty seconds behind its driver's phone. Every dashboard is green. How would you have known first?
[pause: 2.0]

[slide: v-444]
[pause: 1.3]
C: The log, the updater, the live store and the map.
[reveal: v-445]
[pause: 0.45]
C: The map A-P-I is marked.
[reveal: v-446]
[pause: 0.45]
C: The naive answer: consumer lag is zero.
[reveal: v-447]
[pause: 0.45]
C: It is. The live store is current. One map pod's change-feed subscription silently stopped, and its viewers see a frozen city.
[pause: 1.1]

[slide: v-448]
[pause: 1.0]
C: The trace.
[reveal: v-449]
[pause: 0.45]
C: A map pod's change-feed connection drops, and a reconnect bug leaves it unsubscribed.
[reveal: v-450]
[pause: 0.45]
C: Its eight hundred viewers keep their sockets; the pushes contain nothing new.
[reveal: v-451]
[pause: 0.45]
C: Forty minutes later, Kafka lag is zero, the live store is current, the pod's C-P-U is low. All green.
[reveal: v-452]
[pause: 0.45]
C: An operator compares the map with a driver's phone.
[reveal: v-453]
[pause: 0.45]
C: Every stage was healthy, measured from the inside. Nobody measured the map.
[pause: 1.0]

[slide: v-454]
[pause: 1.3]
C: The fix changes the design: version four. Version three, carried.
[reveal: v-455]
[pause: 0.45]
C: New: a freshness probe. Canary vehicles, simulated in every city, publish through the gateway, and the probe reads them back through the map, like a viewer.
[pause: 1.1]

[slide: v-456]
[pause: 0.6]
C: One level down, four signals.
[reveal: v-457]
[pause: 0.45]
C: Canary vehicles: a simulated vehicle in every city moves every two seconds, and a probe viewer subscribed on every map pod must see it within two seconds. That one would have paged at ten o'clock and two seconds.
[reveal: v-458]
[pause: 0.45]
C: Age on screen: every push carries the position's receipt time, and the browser reports the age it actually displays.
[reveal: v-459]
[pause: 0.45]
C: Per-pod freshness: the share of a pod's viewers receiving changes. Zero for a busy city pages.
[reveal: v-460]
[pause: 0.45]
C: And canary safety events, end to end, to a test dispatch endpoint.
[reveal: v-461]
[pause: 0.45]
C: Rejected: consumer-lag dashboards. Lag can be zero while a vehicle on the map is forty seconds stale.
[pause: 0.8]

[slide: v-462]
[pause: 1.0]
C: The canary, in detail, because its value is that it behaves like a real vehicle.
[reveal: v-463]
[pause: 0.45]
C: It publishes a position every two seconds with its own sequence, through the real gateway: identity, sessions and the log.
[reveal: v-464]
[pause: 0.45]
C: It drives a fixed route in every city, so it changes cells: the updater and the live store.
[reveal: v-465]
[pause: 0.45]
C: A probe viewer on every map pod subscribes to its cell: subscriptions and pushes, pod by pod.
[reveal: v-466]
[pause: 0.45]
C: Every ten minutes it raises a safety event to a test endpoint.
[reveal: v-467]
[pause: 0.45]
C: And every hour its history is replayed: the lake and the replay A-P-I. One fake vehicle exercises every path in this video.
[pause: 1.0]

[slide: v-468]
[pause: 1.0]
C: And read them in pairs.
[reveal: v-469]
[pause: 0.45]
C: A canary stale on one pod while others are fresh: that pod's subscription. Our case.
[reveal: v-470]
[pause: 0.45]
C: Canaries stale everywhere with Kafka lag rising: the updater or the log.
[reveal: v-471]
[pause: 0.45]
C: Age on screen high while canaries are fresh: real vehicles in a coverage hole, not us.
[reveal: v-472]
[pause: 0.45]
C: The share of backfill rising on one carrier: that carrier is recovering from an outage.
[reveal: v-473]
[pause: 0.45]
C: And a late safety canary with normal position lag: the safety lane itself.
[pause: 1.0]

[slide: v-474]
[pause: 1.0]
C: And the service levels.
[reveal: v-475]
[pause: 0.45]
C: The canary visible on every pod within two seconds.
[reveal: v-476]
[pause: 0.45]
C: The safety canary at dispatch within a second.
[reveal: v-477]
[pause: 0.45]
C: Every received position in history, checked by a daily reconciliation of counts, question three's conservation check.
[reveal: v-478]
[pause: 0.45]
C: One vehicle's hour replayed within ten seconds.
[reveal: v-479]
[pause: 0.45]
C: And positions dropped on vehicles because a buffer filled: counted and reported, never hidden.
[pause: 1.0]

[slide: v-480]
[pause: 0.7]
V: If asked, I'd say: I'd measure freshness where the operator sees it. A canary vehicle in every city, read back through every map pod within two seconds; the age each browser actually displays; and canary safety events end to end. Lag measures the pipeline. Canaries measure the map.
[pause: 1.6]

[pause: 1.4]

## 8 Recap

[slide: v-481]
[pause: 1.2]
C: The recap.
[pause: 1.8]

[slide: v-482]
[pause: 1.3]
C: Version four.
[reveal: v-483]
[pause: 0.45]
C: The uplink: lanes and a capped backfill.
[reveal: v-484]
[pause: 0.45]
C: The log: keyed by vehicle, so order holds.
[reveal: v-485]
[pause: 0.45]
C: The updater: one log, two views, and sequence numbers.
[reveal: v-486]
[pause: 0.45]
C: The live store: cells at several resolutions.
[reveal: v-487]
[pause: 0.45]
C: The map: cells, and subscriptions.
[reveal: v-488]
[pause: 0.45]
C: The lake: everything, by vehicle.
[reveal: v-489]
[pause: 0.45]
C: And the probe: canaries, read back like a viewer.
[pause: 1.1]

[slide: v-490]
[pause: 0.6]
C: One sentence per path.
[reveal: v-491]
[pause: 0.45]
C: Report: positions carry a sequence, the log is keyed by vehicle, and safety has its own lane.
[reveal: v-492]
[pause: 0.45]
C: Watch: the live view overwrites only with newer positions, and viewports subscribe to cells, counts when far.
[reveal: v-493]
[pause: 0.45]
C: Replay: history by event day and vehicle bucket, sorted by sequence, read at a snapshot.
[reveal: v-494]
[pause: 0.45]
C: Alert: safety events skip every queue, on the vehicle and on the server.
[pause: 0.8]

[slide: v-495]
[pause: 1.0]
N: The mistakes that cost most.
[reveal: v-496]
[pause: 0.45]
N: One table for the map and the history. Instead, one log, two views.
[reveal: v-497]
[pause: 0.45]
N: Latest arrival wins. Instead, latest sequence wins.
[reveal: v-498]
[pause: 0.45]
N: Keying the log by geo cell. Instead, key by vehicle and index by cell.
[reveal: v-499]
[pause: 0.45]
N: Every dot at every zoom, polled. Instead, counts when far and subscriptions to cells.
[reveal: v-500]
[pause: 0.45]
N: Flushing buffers oldest first. Instead, safety, latest, then capped backfill.
[reveal: v-501]
[pause: 0.45]
N: Watching consumer lag. Instead, canaries read through the map.
[pause: 1.0]

[slide: v-502]
[pause: 0.7]
V: One log keyed by vehicle, read twice: latest by cell for the map, everything by vehicle for history. The vehicle orders its own data and decides what goes first. And most of it, you've already built, in three other questions.
[pause: 1.0]
C: Thanks for watching. The written design, and the three questions it builds on, are linked below.
[pause: 1.6]
