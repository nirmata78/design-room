from dsl import *
import stack
P = "[+]"
B = lambda x: f'<span class="bad">{x}</span>'
ST = stack.load(pathlib.Path(__file__).resolve().parents[2])
T = 6   # challenges

# ───────────────────────── 4 · C4 evolution through interviewer challenges ─────────────────────────
chapter(4, "Design, driven by challenges", 3, "V1 is the C4 container view; every challenge changes it", [
 "C: The design. I start directly with the container view, version one: the simplest thing that is correct. Then the interviewer breaks it, six times, and each fix is a change to this one picture, or a zoom into one of its boxes."])

stage("C4 level 2 · containers", "The simplest exact design: a log, a lake, an hourly job", "v1", [
 "C: Version one, in the order an event travels.", P,
 "C: Ad clients send batches of events.", P, "C: A collector validates them, stamps the server time, and appends them.", P,
 "C: To a partitioned, replicated event log. This is the one copy everything else is derived from.", P,
 "C: Every five minutes the log is loaded into an event lake, partitioned by the hour the event happened.", P,
 "C: A billing job reads one closed hour, removes duplicates and counts.", P,
 "C: And writes billing tables, one version of each hour.", P, "C: A reporting API serves them.", P,
 "C: To the advertiser. It is exact and replayable, because every number is derived from the log."],
 vtag="V1", cap="V1: the C4 container view, exact and hourly")

stage("Flow · FR1 and FR3 on V1", "An event, from the phone to the bill", "flow-v1", [
 "C: The happy path, numbered, once.", P,
 "C: One: the SDK posts a batch to the collector.", P, "C: Two: the collector appends it, all replicas acknowledging, then answers 202.", P,
 "C: Three: the lake loads it every five minutes into the partition of each event's hour.", P,
 "C: Four: at the cutoff, the billing job reads that hour at a pinned snapshot.", P,
 "C: Five: it writes the hour as a version.", P, "C: Six: the advertiser asks.", P,
 "C: Seven: the API reads the final hour. FR1 and FR3, end to end."], cap="V1 happy path: record, then bill")

S(tech(**ST.tech("log")), ST.say("log"))

# ───────── Challenge 1 · freshness ─────────
challenge(1, T, "An hour is too late", "Advertisers want to see a campaign's spend within ten seconds, and budget pacing needs it to stop campaigns. Your V1 answers in two days. Now what?",
          ["N: Challenge one is the freshness requirement, held back on purpose. It decides the shape of the whole design."])

stage("Challenge 1 of 6 · the break", "V1 cannot answer in ten seconds", "v1-break", [
 "C: Version one, with the problem marked.", P,
 f"C: The billing job only runs when an hour is closed. That protects {ps('S3')}, but it can never meet {ps('L2')}: ten seconds."],
 cap="V1: the billing job is hourly by design")

mech_slide(1, 4, "One aggregation, run twice", pid("L2") + " fresh, without giving up " + pid("S3"),
           "The same aggregation code runs twice over the same immutable log: streaming for the dashboard, then bounded over each closed hour for the bill.",
           "A fast number that disagrees with the bill forever; two codebases that drift.",
           "Computing twice; the bill still waits 48 hours.", [
 "C: The mechanism, just in time.", P,
 f"C: It protects {ps('L2')}, without giving up {ps('S3')}.", P,
 "C: The same aggregation code runs twice over the same immutable log. Streaming for the dashboard, and then, in batch mode, over each closed hour for the bill.", P,
 "C: It rules out a fast number that disagrees with the bill forever, and two codebases that drift apart.", P,
 "C: It costs computing twice, and the bill still waits forty-eight hours."], part="Mechanism")

S(plain("Challenge 1 of 6 · the options", "Five ways to count, one picked", table(["Approach", "Fresh", "Exact, replayable", "Fails when"], [
  ["A · a counter per event in a database", "yes", "no", "30 M writes a second; hot rows; every retry counts"],
  ["B · batch only, over the lake (V1)", "no", "yes", "the dashboard is two days behind"],
  ["C · stream only: the stream result is the bill", "yes", "partly", "late events past the state lifetime are lost; a fix means replaying months"],
  ["D · Lambda: a stream job and a batch job, two codebases", "yes", "yes", "two implementations drift; every difference is a mystery"],
  ("pick", ["<b>E · one aggregation code, run twice</b>", "yes", "yes", "compute twice; the bill waits 48 h"])], "bt xs mx") +
  line("Kappa in code, Lambda in time: one codebase, two runs over the same log.", "a")), [
 "C: Five ways to do it.", P,
 "C: A, a counter per event in a database: the estimates already ruled it out.", P,
 "C: B is version one: exact, but two days behind.", P,
 "C: C, stream only: late events past the state's lifetime are lost, and a fix means replaying months.", P,
 "C: D, Lambda written twice: it works until the two codebases drift.", P,
 "C: E, which I pick: one aggregation code, run twice.", P,
 "V: Kappa in code, Lambda in time. I give up computing twice, and a bill that waits forty-eight hours."])

stage("Challenge 1 of 6 · the fix", "A live aggregator and a live store, on the same log", "v2", [
 "C: Version two. Everything from version one stays exactly where it was.", P,
 "C: New: a live aggregator. A stream job on the same log, with the same aggregation code. It counts by the minute and emits early results.", P,
 "C: New: a live store, holding live minutes. The API now reads open hours from it, and closed hours from the billing tables, and always says which."],
 vtag="V2", cap="V2: the live path added; V1's boxes do not move")

stage("Flow · FR2 on V2", "An impression, from the phone to the dashboard", "flow-live", [
 "C: The live path, numbered.", P,
 "C: One: the SDK posts a batch.", P, "C: Two: the collector appends it and answers 202.", P,
 "C: Three: the live aggregator consumes it.", P, "C: Four: it upserts minute rows, early every two seconds, final when the watermark passes.", P,
 "C: Five: the advertiser opens a dashboard.", P, "C: Six: the API queries the live store. About five seconds end to end, inside the budget."],
 cap="V2 live path: about five seconds end to end")

S(tech(**ST.tech("stream")), ST.say("stream"))

push("Why not make the stream job's numbers the bill, and drop the billing job?")
S(plain("Challenge 1 of 6 · one level deeper", "The stream is a preview; the bill is a pure function", cards(
  ("amb", "State has a lifetime", "Dedup keeps 10 minutes of IDs; a retry at minute eleven is counted twice live. The hour-wide batch dedup is not."),
  ("amb", "Late events have a cutoff", "The stream accepts an hour of lateness; phones deliver for two days. The bill waits for them."),
  ("grn", "Reproducible by construction", "A billing run is a function of a pinned snapshot; a stream's output depends on arrival order and timing."), cols=3)), [
 "C: Three reasons.", P,
 "C: The stream's state has a lifetime. Dedup keeps ten minutes of IDs, so a retry at minute eleven is counted twice on the live path. The billing run deduplicates the whole hour.", P,
 "C: Late events have a cutoff. The stream accepts an hour of lateness, and phones deliver for two days. The bill waits for them.", P,
 f"C: And {ps('S3')}: a billing run is a function of a pinned snapshot. A stream's output depends on arrival order and timing, so it cannot be re-run bit for bit."])

say_slide("“One aggregation, run twice over one log: streaming for a provisional dashboard within ten seconds, and the same code over each closed hour for an exact, reproducible bill. The dashboard says which one you are looking at, and the fast number converges to the final one.”", [
 "V: If asked, I'd say: one aggregation, run twice over one log. Streaming for a provisional dashboard within ten seconds, and the same code over each closed hour for an exact, reproducible bill. The dashboard says which one you are looking at, and the fast number converges to the final one.", "[pause: 1.0]",
 "N: That fix creates the next question: two runs over a log that contains repeats. Who removes them?"])

# ───────── Challenge 2 · the same click, three times ─────────
challenge(2, T, "The same click, three times", "A retrying client sends the same click three times, two seconds apart. Walk me through it.",
          ["N: Challenge two is the crux of this question. Most answers name a guarantee here. The grade is for the mechanism."])

S(trace("Challenge 2 of 6 · the trace", "One click, a lost answer, two retries", [
  ("10:00:00.000", "the SDK sends batch B17 with click <code>e7f3…</code>"),
  ("10:00:00.040", "the collector appends it at offset 81,220; Kafka acknowledges"),
  ("10:00:00.900", "the 202 is lost on the cell network"),
  ("10:00:02.900", "the SDK retries B17: offset 81,977, " + B("a second copy")),
  ("10:00:04.900", "and again: offset 82,610, " + B("a third"))],
  hedge=("At scale", "0.3 % of batches retried is about 750 million duplicate clicks a month: about $375 M billed twice, illustrative.")), [
 "C: The trace.", P, "C: At ten o'clock the SDK sends batch B17, with click e7f3.", P,
 "C: Forty milliseconds later it is at offset eighty-one thousand two hundred and twenty, acknowledged.", P,
 "C: The 202 is lost on the cell network.", P, "C: Two seconds later the SDK retries: a second copy.", P, "C: And again: a third.", P,
 "C: Nobody did anything wrong. At three tenths of a percent of batches, that's three hundred and seventy-five million dollars a month, billed twice."])

stage("C4 level 3 · the live aggregator", "Inside the live aggregator: seven components", "comp-stream", [
 "C: Before the fix, one level down: the live aggregator's components. It is one Flink job.", P,
 "C: A Kafka source reads the event log's partitions; its offsets are kept in the checkpoint.", P,
 "C: A time assigner gives every event its event time.", P,
 "C: A deduplicator remembers the IDs it has seen, and the checkpoints keep that state, with the offsets, every thirty seconds.", P,
 "C: A combiner sums per ad for one second, and the window counter counts per ad and minute.", P,
 "C: And a store sink writes versioned rows into the live store. The next challenges each mark two or three of these boxes."],
 cap="C4 component view: the live aggregator, from the event log to the live store")

zoom("Challenge 2 of 6 · the break", "Inside the live aggregator: who notices a repeat?", "dd-break", strip(("case", "Naive answer", "“Kafka is exactly-once, so duplicates can't happen.”"),
                  ("case", "Break", "The copies were made before Kafka: nothing remembers an ID, so three are counted.")), [
 "C: The same picture, with the source, the time assigner and the deduplicator in play. The deduplicator is marked.", P,
 "C: In the naive design it isn't there, because of the naive answer.", P,
 "C: Kafka is exactly-once, so duplicates can't happen.", P,
 "C: But the duplicates were made before Kafka. Three copies arrive, nothing remembers an ID, and three are counted, on the dashboard and on the bill."], q=True, red=True, cap="C4 component zoom: the live aggregator's first three components")

mech_slide(2, 4, "Idempotency by event ID", pid("S1"),
           "The SDK or ad server mints an ID when the event happens. Every later stage keeps the first copy of each ID and drops the rest.",
           "A retry, a redelivery or a replay counted twice.",
           "An ID minted upstream; state per ID for the dedup window: 0.7 TB for ten minutes.", [
 "C: The mechanism: idempotency by event ID.", P, f"C: It protects {ps('S1')}.", P,
 "C: The SDK or the ad server mints an ID at the moment the event happens, not when it is sent. Every later stage keeps the first copy of each ID and drops the rest.", P,
 "C: It rules out a retry, a redelivery or a replay being counted twice.", P,
 "C: It costs an ID minted upstream, which we do not control, and state per ID for the dedup window. We sized that: point seven terabytes for ten minutes."], part="Mechanism")

S(dia("Mechanism 2 · as a sequence", "Three copies in, one count out", "seq-retry", cap="The retry as a sequence: the deduplicator drops the second copy"), [
 "C: As a sequence.", P, "C: Batch B17.", P, "C: Appended.", P, "C: Acknowledged.", P,
 "C: The answer is lost.", P, "C: The retry, same IDs.", P, "C: Appended again, on the same partition, because the log is keyed by event ID.", P,
 "C: Both reach the deduplicator.", P, "C: e7f3 is already in state: the second copy is dropped.", P,
 "C: And the billing run keeps the first row per ID in the hour. Once, by construction."])

zoom("Challenge 2 of 6 · the fix", "Drop a repeat by the ID minted at the source", "dd-fix", strip(("fixb", "Mechanism", "Keyed state by event ID in RocksDB, TTL 10 min, checkpointed with the offsets. The billing run keeps the first row per ID over the whole hour."),
                  ("whyb", "Covers, and does not", "Every retry, redelivery and replay of one event. Not a client minting new IDs per click: that is fraud's job.")) + rejl(*ST.rej(1)), [
 "C: The fix, on the same zoom.", P, "C: The deduplicator.", P, "C: And the checkpoints that keep its state.", P,
 "C: One level down: state keyed by event ID, in RocksDB, with a ten-minute lifetime. A record whose ID is already there is dropped. The state is checkpointed together with the Kafka offsets. The log is keyed by event ID, so all three copies land on the same partition and meet the same state.", P,
 "C: It covers every retry, redelivery and replay of one event. Not a client that mints a new ID per click: that's fraud's job.", P,
 "C: Rejected: Kafka's exactly-once, with transactions. It removes a producer's own retry inside one session. An SDK retry over HTTPS is a new request, and only dedup on the event ID removes it."], cap="C4 component zoom: the deduplicator and its checkpointed state")

push("You find a bug, redeploy, and replay the stream from four hours ago. Is anyone billed twice?")
zoom("Challenge 2 of 6 · one level deeper", "Replace by key and version", "replay-fix", strip(("fixb", "Mechanism", "Live rows are keyed (ad, minute, shard) with a version: a newer version replaces, never adds. A billing hour is committed as a whole partition, a pure function of its manifest."),
                  ("whyb", "Covers, and does not", "Replays, restarts and re-runs with new code. It does not make a buggy run right: it makes the next run safe.")) + rejl(*ST.rej(4)), [
 "C: The engine's exactly-once is about one run; a replay is a second run. So the fix is at the end of the job.", P,
 "C: The store sink.", P, "C: And the live store.", P,
 "C: A live row is keyed by ad, minute and shard, with a version; ClickHouse keeps the highest. A re-emitted minute replaces the old row. A billing hour is committed whole, a pure function of its manifest.", P,
 "C: It covers replays, restarts and re-runs with new code. It doesn't make a buggy run right; it makes the next one safe.", P,
 "C: Rejected: Flink's two-phase-commit sink on its own. It makes one run's output atomic. A second run from four hours earlier still adds on top, unless the write replaces by key."], cap="C4 component zoom: the store sink and the live store")

say_slide("“Every event carries an ID minted where it happened, so a retry is recognisable. The live path drops repeats in keyed state for ten minutes; the billing run drops them over the whole hour. And I never increment a number I can recompute: rows are replaced by key and version, so a replay rewrites the same rows.”", [
 "V: If asked, I'd say: every event carries an ID minted where it happened, so a retry is recognisable. The live path drops repeats in keyed state for ten minutes, and the billing run drops them over the whole hour. And I never increment a number I can recompute: rows are replaced by key and version, so a replay rewrites the same rows.", "[pause: 1.0]",
 "N: That fix creates the next question: the ID says which event it is. It doesn't say when it happened."])

# ───────── Challenge 3 · late events and skewed clocks ─────────
challenge(3, T, "Yesterday's events at 6 a.m.", "A phone was offline overnight. Three hundred impressions from Tuesday evening arrive on Wednesday at six. Which hour gets billed?",
          ["N: Challenge three: time. Which clock decides the hour an event is billed in?"])

S(trace("Challenge 3 of 6 · the trace", "A flight, a campaign that ended, and a clock in 2031", [
  ("Tue 21:10–23:40", "300 impressions on a phone with no signal, buffered"),
  ("Tue 23:59", "the campaign's flight ends"),
  ("Wed 06:00", "the phone reconnects; " + B("counted at arrival: billed after the campaign ended")),
  ("Wed 06:01", "another phone says <code>client_ts</code> = 2031-01-01: " + B("an hour that never closes"))],
  hedge=("What it costs", "A charge outside the flight dates is a dispute. A clock in 2031 is a window held open for years.")), [
 "C: The trace.", P, "C: Tuesday evening, three hundred impressions on a phone with no signal.", P, "C: At midnight the campaign's flight ends.", P,
 "C: At six on Wednesday the phone reconnects. Counted at arrival, those impressions are billed after the campaign ended.", P,
 "C: And another phone says its clock is in twenty thirty-one. Trust that, and an hour opens that never closes.", P,
 "C: So I need event time, and I can't trust it blindly."])

zoom("Challenge 3 of 6 · the break", "Which clock decides the hour?", "late-break", strip(("case", "Naive answer", "“Count them when they arrive.”"),
                  ("case", "Break", "Arrival time bills Tuesday's impressions in Wednesday 06:00.")), [
 P, "C: The same zoom. The time assigner is marked.", P,
 "C: The naive answer: count them when they arrive.", P,
 "C: Then the time assigner uses arrival time. Tuesday's hours come up short, and Wednesday six o'clock is over."], q=True, red=True, cap="C4 component zoom: the time assigner")

mech_slide(3, 4, "Event time, with watermarks", pid("S2") + " and, with early results, " + pid("L2"),
           "Count by the time in the event. A watermark says “nothing older is still coming”; a window fires when it passes, early results before.",
           "A late or replayed event landing in the hour it arrived.",
           "Waiting; state for open windows; a cutoff, after which a late event becomes a correction.", [
 "C: The mechanism: event time, with watermarks.", P, f"C: It protects {ps('S2')}, and with early results, {ps('L2')}.", P,
 "C: I count by the time in the event, not the time it arrived. A watermark is the job's claim that nothing older is still coming; a window's final result fires when it passes, early results before.", P,
 "C: It rules out a late or replayed event landing in the hour it happened to arrive in.", P,
 "C: It costs waiting, state for every window still open, and a cutoff. After the cutoff, a late event becomes a correction, not a count."], part="Mechanism")

stage("Mechanism 3 · at protocol level", "A watermark, then early, on-time and late results", "seq-watermark", [
 "C: At protocol level: one window, ad seventy-seven, the minute starting at fourteen hundred, fed by two partitions.", P,
 "C: Partition one delivers an impression with event time fourteen hundred and fifty-eight seconds.", P,
 "C: Partition two, one at fourteen oh one thirty.", P,
 "C: The watermark is the minimum over partitions of the latest time minus two minutes: thirteen fifty-eight fifty-eight. The minute is still open.", P,
 "C: But the dashboard should not wait, so the window emits an early result: twelve hundred and twelve, version one.", "[+2]",
 "C: Later events arrive, from both partitions.", P,
 "C: Now the watermark is fourteen oh one oh five. It has passed the end of the minute.", P,
 "C: So the on-time result fires: thirteen eighteen, version two. It replaces version one; it does not add to it.", P,
 "C: Then a late event for that minute, within the allowed hour.", P,
 "C: Version three, thirteen nineteen. No lock and no wall clock: event times, a minimum, and a version."],
 cap="One window fed by two partitions: versions 1, 2 and 3 of one minute")

zoom("Challenge 3 of 6 · the fix", "Event time, clamped; a watermark for the dashboard", "late-fix", strip(("fixb", "Mechanism", "Event time = client time if within 72 h before to 5 min after server time; else server time, flagged. Watermark = min over partitions of latest − 2 min; 1 h of lateness."),
                  ("whyb", "Covers, and does not", "Late and skewed events up to the billing cutoff. After it, a new version of the hour: challenge five.")) + rejl(*ST.rej(2)), [
 "C: The fix, one level down.", P, "C: The time assigner.", P, "C: And the window counter.", P,
 "C: The event time is the client's time if it lies between seventy-two hours before and five minutes after the server's time. Otherwise it's the server time, and the event is flagged as clamped. The watermark is the minimum over partitions of the latest event time minus two minutes, and a minute window accepts an hour of lateness after that.", P,
 "C: It covers late and skewed events up to the billing cutoff. After the cutoff, an event changes a closed hour, and that's challenge five.", P,
 "C: Rejected: processing-time windows. They bill a phone's Tuesday evening in Wednesday's six a.m. hour."], cap="C4 component zoom: the time assigner and the window counter")

S(plain("Challenge 3 of 6 · the rule, as pseudocode", "Clamp, then let the slowest partition set the pace",
  pseudo("t = e.client_ts\nif t < e.server_ts - 72h or t > e.server_ts + 5m:\n    t, e.clamped = e.server_ts, true\ne.event_time = t\n\nwatermark = min(latest(p) - 2m for p in active)\nwhen watermark >= w.end: emit(w, version + 1)\nwhen e is late and watermark < w.end + 1h:\n    add(w, e); emit(w, version + 1)\nelse: count_late(e)       # the lake still has it", hl=(2, 6, 8))), [
 "C: As pseudocode, the key lines marked.",
 "C: Line two: a client time outside the window is replaced by the server time. Line six: the watermark is a minimum over active partitions, two minutes behind. Line eight: a late event inside the hour of allowed lateness updates its window, emitted again with a higher version. Anything later is only counted as late. The lake still has it, so the bill still will.",
 "C: Why it works: a minimum means one fast partition can't close a minute that a slow one is still filling, and the clamp bounds what a bad clock can do."])

stage("C4 level 3 · the billing job", "Inside the billing job: eight components", "comp-billing", [
 "C: The live path is one half. The bill is the other, so one level down into the billing job: the same Flink code, in batch mode.", P,
 "C: An hour closer decides when hour H is complete, and a reader scans exactly that hour from the lake.", P,
 "C: Exact dedup keeps the first copy of each ID over the whole hour, and the invalid filter drops what the fraud system flagged.", P,
 "C: Price and sum turns events into money, in integer micros, and the writer commits the hour to the billing tables as a new version.", P,
 "C: An adjuster turns a new version into an adjustment line for invoicing, and a reconciler checks the live numbers against the final ones."],
 cap="C4 component view: the billing job, from the event lake to the billing tables")

zoom("Challenge 3 of 6 · the bill's half", "The bill waits for the hour to be complete", "close-fix", strip(("fixb", "At H + 48 h", "The hour closer pins a snapshot of hour H's partition: every file landed so far, late ones included. The run reads exactly that."),
                  ("whyb", "Why 48 hours", "An initial target, to measure: if 99.99 % of events arrive within 36 h, the rest become version 2 at the cost of one adjustment.")), [
 "C: For late events, the hour closer is the box in play.", P,
 "C: The hour closer.", P,
 "C: At forty-eight hours it pins a snapshot of that hour's partition: every file landed so far, the late ones included, because the lake is partitioned by event hour, not by arrival. The run reads exactly that snapshot, and nothing that lands later.", P,
 "C: Why forty-eight hours: it's an initial target, to be measured. If ninety-nine point nine nine percent of events arrive within thirty-six hours, the rest become a version two, at the cost of one adjustment."], cap="C4 component zoom: the billing job's hour closer")

push("One partition goes quiet. Or a bad SDK release sends every clock a day off.")
S(plain("Challenge 3 of 6 · one level deeper", "An idle timeout, a flag, and versions", cards(
  ("grn", "A quiet partition", "Excluded from the watermark after 30 s of silence, so one idle partition cannot freeze every dashboard."),
  ("amb", "A bad SDK clock", "Clamped to server time and flagged; an alert when the clamped share passes 0.1 %, by SDK version."),
  ("red", "Honest limit", "An event past the cutoff changes a closed hour: version 2 and an adjustment, never a silent edit."), cols=3)), [
 P, "C: A quiet partition would hold the minimum back forever, so it is excluded from the watermark after thirty seconds of silence.", P,
 "C: A bad SDK clock is clamped to server time and flagged, and an alert fires when the clamped share passes a tenth of a percent, broken down by SDK version, so the release is found in minutes.", P,
 "C: And the honest limit: an event past the cutoff does change a closed hour. It becomes version two and an adjustment, never a silent edit."])

say_slide("“The event's own time decides its hour, clamped against server time so a broken or hostile clock can't move it far. The dashboard waits two minutes and accepts an hour of lateness; the bill closes at forty-eight hours from a snapshot of everything that landed for that hour, and anything later becomes a new version.”", [
 "V: If asked, I'd say: the event's own time decides its hour, clamped against server time so a broken or hostile clock can't move it far. The dashboard waits two minutes and accepts an hour of lateness. The bill closes at forty-eight hours from a snapshot of everything that landed for that hour, and anything later becomes a new version.", "[pause: 1.0]",
 "N: That fix creates the next question: the windows are keyed by ad. What if one ad is the whole stream?"])

# ───────── Challenge 4 · one ad at two million a second ─────────
challenge(4, T, "One ad at 2 million a second", "A sports break puts one ad on every screen: two million impressions a second. What happens to your job?",
          ["N: Challenge four: overload, but not the kind more machines fix."])

S(trace("Challenge 4 of 6 · the trace", "Ninety seconds of one ad", [
  ("20:14:00", "the break starts; ad 77 jumps from 3,000 to 2,000,000 impressions a second"),
  ("20:14:05", "the window task holding ad 77 at 100 % CPU; its input buffer fills"),
  ("20:14:20", B("backpressure: every source slows; lag grows on all 1,024 partitions")),
  ("20:15:30", B("every advertiser's dashboard is 90 s stale; budget pacing flies blind"))],
  hedge=("Not a hot partition", "The log is keyed by event ID, so its partitions are even. The hot spot is one thread.")), [
 "C: The trace.", P, "C: At twenty fourteen, ad seventy-seven goes from three thousand to two million impressions a second.", P,
 "C: Five seconds later, the one window task holding it is at a hundred percent.", P,
 "C: Backpressure. Every source slows, and lag grows on all thousand and twenty-four partitions.", P,
 "C: Ninety seconds later every advertiser's dashboard is stale, and budget pacing is flying blind, not just for ad seventy-seven.", P,
 "C: Note what is not hot: the log is keyed by event ID, so its partitions are even. The hot spot is one thread."])

zoom("Challenge 4 of 6 · the break", "One key is one task", "hot-break", strip(("case", "Naive answer", "“Key by ad, and add machines.”"),
                  ("case", "Break", "A key lives on exactly one task: it gets all 2 M/s, and its backpressure slows every partition.")), [
 P, "C: The middle of the live aggregator. The window counter is marked.", P,
 "C: The naive answer: key by ad, and add machines.", P,
 "C: But a key lives on exactly one task. Machines don't help it. That one task gets all two million a second, and its backpressure slows every partition."], q=True, red=True, cap="C4 component zoom: the window counter")

mech_slide(4, 4, "Two-stage aggregation: sharded counters", pid("L2") + " under skew",
           "Sum locally where events already are, for a second; then merge the partial sums by key. Store a hot counter as N shard rows; sum on read.",
           "One hot key stalling one task, and with it the whole job.",
           "One more stage; a sum on every read; a second of delay.", [
 "C: The mechanism: two-stage aggregation, the sharded counter applied in time.", P, f"C: It protects {ps('L2')} when the load is skewed.", P,
 "C: Each task sums the events it already has, for one second, and only then sends a partial sum to be merged by key. In the store, a hot counter is N shard rows, summed on read.", P,
 "C: It rules out one hot key stalling one task, and with it the whole job.", P,
 "C: It costs one more stage, a sum on every read, and a second of delay."], part="Mechanism")


zoom("Challenge 4 of 6 · the fix", "Sum where the events are, then merge", "hot-fix", strip(("fixb", "Mechanism", "Each of 512 subtasks sums per (ad, minute) for 1 s, then sends one partial; the merge sees 512 updates a second. The store keeps up to 16 shard rows per ad-minute, summed on read."),
                  ("whyb", "Covers, and does not", "Any number of hot ads: the cost follows active keys, not events. It adds 1 s of delay, inside the 10 s budget.")) + rejl(*ST.rej(3)), [
 "C: The fix, in the middle of the job.", P, "C: The combiner.", P, "C: And the window counter, which now merges partial sums.", P,
 "C: One level down. Each of the five hundred and twelve subtasks sums its own events per ad and minute for one second, then sends one partial sum. The window task for ad seventy-seven sees five hundred and twelve updates a second instead of two million. And the store keeps up to sixteen shard rows per ad and minute, summed when the dashboard reads.", P,
 "C: It covers any number of hot ads, because the cost now follows active keys, not events. It adds a second of delay, inside the ten-second budget.", P,
 "C: Rejected: Redis increment-by on one counter key. One key is one shard's thread, about a hundred thousand operations a second against two million. And a replay increments again."], cap="C4 component zoom: the combiner and the window counter")

S(tech(**ST.tech("live")), ST.say("live"))

push("Now five hundred ads are hot at once, in every break.")
S(plain("Challenge 4 of 6 · one level deeper", "Bounded by active keys, not by events", cards(
  ("grn", "Partial maps stay small", "One entry per active ad and minute per subtask: 500 hot ads are 500 entries, flushed every second."),
  ("amb", "The merge scales by key", "500 hot ads × 512 partials = 256,000 updates a second, spread over the merge subtasks by key."),
  ("red", "Honest limit", "Every count arrives a second later. Worth it: the budget has the room."), cols=3)), [
 "C: Five hundred hot ads.", P,
 "C: Each subtask's partial map holds one entry per active ad and minute: five hundred entries, flushed every second. Small.", P,
 "C: The merge sees five hundred ads times five hundred and twelve partials: about two hundred and fifty-six thousand updates a second, spread over its subtasks by key. That scales with machines, because now there are many keys.", P,
 "C: The honest limit: every count arrives a second later. The budget has the room."])

say_slide("“A hot key is a hot thread, not a hot partition: my log is keyed by event ID. So I sum where the events already are, once a second, and merge 512 partial sums instead of two million updates. On the read side, a hot counter is sixteen shard rows, summed on read.”", [
 "V: If asked, I'd say: a hot key is a hot thread, not a hot partition, because my log is keyed by event ID. So I sum where the events already are, once a second, and merge five hundred and twelve partial sums instead of two million updates. On the read side, a hot counter is sixteen shard rows, summed on read.", "[pause: 1.0]",
 "N: That fix creates the next question: if an hour can be re-run, what happens when its inputs change after it was billed?"])

# ───────── Challenge 5 · fraud after the invoice ─────────
challenge(5, T, "Fraud after the invoice", "Nine days after the invoices go out, fraud invalidates two percent of October's clicks for one advertiser. What happens?",
          ["N: Challenge five: the past changes. How you record that is the grade."])

S(trace("Challenge 5 of 6 · the trace", "An invoice that no longer matches anything", [
  ("1 Nov", "October invoiced: advertiser A, 155 M clicks, $77.5 M"),
  ("9 Nov", "fraud flags botnet 17: 3.1 M of A's October clicks, 2 %"),
  ("9 Nov", B("naive: billed rows updated in place")),
  ("15 Nov", B("A disputes a line; no stored version matches the invoice they hold"))],
  hedge=("Two needs at once", "A credit for the invalid clicks, and an untouched record of what was invoiced.")), [
 "C: The trace.", P, "C: On the first of November, advertiser A is invoiced: a hundred and fifty-five million clicks, seventy-seven and a half million dollars.", P,
 "C: On the ninth, fraud flags botnet seventeen: three point one million of those clicks, two percent.", P,
 "C: The naive fix updates the billed rows in place.", P,
 "C: A week later A disputes a line, and we have no stored version that matches the invoice in their hand.", P,
 "C: So I need two things at once: a credit for the invalid clicks, and an untouched record of what was invoiced."])

stage("Challenge 5 of 6 · the C4 delta", "Invalidations arrive as events, into the billing job", "v3", [
 "C: This one changes the container view, so it is version three. Version two, carried, with one box new.", P,
 "C: The fraud system. Its invalidations arrive on an append-only topic, each with its event's hour, and only the billing job consumes them. Nothing on the live path changes."],
 vtag="V3", cap="V3: the fraud system's invalidations reach the billing job")

zoom("Challenge 5 of 6 · the break", "Edit the past, or add to it?", "fraud-break", strip(("case", "Naive answer", "“Delete the invalid rows and re-send the invoice.”"),
                  ("case", "Break", "The writer edits billed hours: the invoice already sent now matches nothing stored.")), [
 P, "C: Inside the billing job: the invalid filter, the pricing step, the writer. The writer is marked.", P,
 "C: The naive answer: delete the invalid rows and re-send the invoice.", P,
 "C: Then the writer edits hours that were billed, and the invoice already sent matches nothing we have stored."], q=True, red=True, cap="C4 component zoom: the billing job's writer")

zoom("Challenge 5 of 6 · the fix", "A new version, and an adjustment line", "fraud-fix", strip(("fixb", "Mechanism", "The closer marks invalidated hours dirty and re-runs each as version n + 1; version n stays. The adjuster sends v(n + 1) − invoiced as a credit line."),
                  ("whyb", "Covers, and does not", "Fraud, events past the cutoff and rate-card fixes: one path. Every invoice line still matches a stored row.")) + rejl(*ST.rej(5)), [
 "C: The fix, at the end of the billing job.", P, "C: The adjuster, between the writer and invoicing.", P,
 f"C: One level down. The closer marks the invalidated hours dirty and re-runs each as the next version, with a manifest pinning the new invalidation snapshot. Version one stays. The adjuster sends the new version minus what was invoiced as a credit line: minus one point five five million dollars. That protects {ps('S2')}: a sent invoice is never edited.", P,
 "C: One path covers fraud, events past the cutoff, and rate-card fixes. And because the invoiced version is never touched, every invoice line still matches a stored row.", P,
 "C: Rejected: updating billed rows in place. The invoice then matches no stored version, and the audit trail ends at the edit."], cap="C4 component zoom: the writer, the adjuster and invoicing")

S(plain("Challenge 5 of 6 · the re-run, as pseudocode", "Dirty hours become new versions; differences become lines",
  pseudo("on invalidations(b): mark_dirty(hours(b))\nrerun(h):\n    m = manifest(h, events_snap, rates_v, invalid_snap)\n    v = latest_version(h) + 1\n    rows = price(dedup(read(h, m)) - invalid(m))\n    commit(h, v, rows, m)          # version v - 1 stays\n    for r in rows:\n        d = r.cost - invoiced(r.key)\n        if d != 0: adjustment(r.key, v, d)", hl=(3, 6, 9))), [
 "C: As pseudocode, key lines marked.",
 "C: Line three: a new manifest pins the new invalidation snapshot. Line six: the commit writes version v, and version v minus one stays. Line nine: any difference from what was invoiced becomes an adjustment.",
 f"C: Why it works, and why it protects {ps('S3')}: a correction is the billing job with a newer manifest. There's no second code path, so a correction can't be computed differently from a bill."])

push("Fraud invalidates an event from seven months ago.")
S(plain("Challenge 5 of 6 · one level deeper", "A contract, not a mechanism", cards(
  ("amb", "Past the raw retention", "Events are kept six months; the dispute window is 90 days. Older invalidations are refused, and the refusal is logged."),
  ("grn", "Inside the window", "Any hour, any number of versions; the adjustment is always against what was invoiced."),
  ("", "Who may do it", "Only the fraud system, with a rule version on every invalidation; the manifest pins the list."), cols=3)), [
 P, "C: Seven months is past the raw retention. Events are kept six months and the dispute window is ninety days, so an older invalidation is refused, and the refusal is logged. That's a contract, not a mechanism, and I'd say so.", P,
 "C: Inside the window: any hour, any number of versions, and the adjustment is always computed against what was actually invoiced.", P,
 "C: And only the fraud system may invalidate, with a rule version on every record, so a manifest can say which rules a version used."])

say_slide("“Nothing billed is ever edited. A correction re-runs the hour as a new version, and the difference from what was invoiced becomes an adjustment line on the next invoice. The same path carries fraud, events past the cutoff and rate-card fixes, so every invoice still matches a stored version.”", [
 "V: If asked, I'd say: nothing billed is ever edited. A correction re-runs the hour as a new version, and the difference from what was invoiced becomes an adjustment line on the next invoice. The same path carries fraud, events past the cutoff and rate-card fixes, so every invoice still matches a stored version.", "[pause: 1.0]",
 "N: That fix creates the last question. Every part can now be right. How would you know when one of them isn't?"])

# ───────── Challenge 6 · a wrong number nobody notices ─────────
challenge(6, T, "“Your numbers are 3 % high”", "An advertiser says our clicks are three percent higher than their own logs. What do you do, and how would you have known first?",
          ["N: Challenge six is observability, and in this question it is about a wrong number, not a down server."])

S(trace("Challenge 6 of 6 · the trace", "A units typo, three days of green", [
  ("Mon 09:00", "a config push sets the dedup lifetime to 10 seconds instead of 10 minutes"),
  ("Mon 09:00 →", "lag, CPU, errors: green; live clicks 3 % above their usual ratio to impressions"),
  ("Wed 09:00", "Monday's final hours are right: the billing run dedups the whole hour"),
  ("Thu", B("an advertiser compares live screenshots with their logs: +3 %"))],
  hedge=("What the dashboards saw", "Nothing. Every system was healthy; one number was wrong for three days.")), [
 "C: The trace.", P, "C: Monday at nine, a config push sets the dedup lifetime to ten seconds instead of ten minutes. A units typo.", P,
 "C: Lag, CPU and errors stay green. Live clicks run three percent above their usual ratio to impressions, and nothing watches that.", P,
 "C: On Wednesday, Monday's final hours are right, because the billing run deduplicates the whole hour.", P,
 "C: On Thursday an advertiser compares their screenshots with their logs and calls.", P,
 "C: Every system was healthy. One number was wrong for three days."])

zoom("Challenge 6 of 6 · the fix", "A reconciler that checks numbers, not machines", "recon-fix", rejl(*ST.rej(6)), [
 P, "C: The fix is a component in the billing job, because that is where the final number is known. The reconciler.", P,
 "C: Rejected: lag and CPU dashboards. They stay green while the pipeline counts wrong. Only checks on the numbers themselves see a wrong number."], cap="C4 component zoom: the reconciler inside the billing job")

S(plain("Challenge 6 of 6 · the fix, one level down", "Three checks on the numbers, and a trail for every line", cards(
  ("grn", "Conservation per hop", "Per minute: accepted = appended = landed − duplicates."),
  ("grn", "Live against final", "Every closed hour, per campaign: alert above 0.5 %."),
  ("grn", "Canaries", "Events with known IDs every minute: exactly once in both."), cols=3) +
  strip(("whyb", "Answering the advertiser", "Invoice line → hour version → manifest → the event IDs, exportable for their line."), cols="one")), [
 "C: One level down, three checks on the numbers themselves.", P,
 "C: Conservation at every hop, per minute: accepted equals appended equals landed, minus duplicates.", P,
 "C: Live against final for every closed hour, alerting above half a percent. That one would have fired on Wednesday.", P,
 "C: And canary events with known IDs every minute, each expected exactly once in the live store and in the final hour.", P,
 "C: And to answer the advertiser: the invoice line points to an hour version, the version to its manifest, the manifest to the event IDs. We can export the IDs behind their line and compare."])

S(plain("Challenge 6 of 6 · reading the signals", "Symptoms in pairs: what each one means", table(["Symptom", "Paired with", "Means"], [
  ["Live clicks up 3 %", "final for the same hour flat", "duplicates on the live path"],
  ["Live and final both up", "impressions up too", "real traffic"],
  ["Accepted above landed", "log lag flat", "the lake loader is losing files"],
  ["A canary seen twice", "—", "a duplicate path, wherever it is"],
  ["Clamped share above 0.1 %", "one SDK version", "a client clock bug"]], "bt sm")), [
 "C: Read symptoms in pairs; a number alone is not a diagnosis.", P,
 "C: Live up three percent, final flat: duplicates on the live path. Our case.", P,
 "C: Both up, impressions too: real traffic.", P,
 "C: Accepted above landed, lag flat: the lake loader is losing files.", P,
 "C: A canary seen twice: a duplicate path.", P,
 "C: A clamped share above a tenth of a percent from one SDK version: a client clock bug."])

push("And if the reconciler itself is wrong?")
S(plain("Challenge 6 of 6 · one level deeper", "Check the checker", cards(
  ("grn", "Canaries check the checker", "A known number of canaries a minute: the reconciler must count exactly that many, or it pages about itself."),
  ("amb", "Silence is a failure", "No comparison for 15 minutes pages: an alert that cannot fire is not an alert."), cols=2)), [
 P, "C: The canaries check the checker. A known number of them a minute, so the reconciler must count exactly that many, or it pages about itself.", P,
 "C: And silence is a failure. If no comparison has run for fifteen minutes, that pages too. An alert that cannot fire is not an alert."])

say_slide("“I'd answer the advertiser with the event IDs behind their line: invoice line, hour version, manifest, events. And I'd want to have seen it first: conservation at every hop, live against final every hour, and canary events whose count I know, so a wrong number pages even when every system is healthy.”", [
 "V: If asked, I'd say: I'd answer the advertiser with the event IDs behind their line: invoice line, hour version, manifest, events. And I'd want to have seen it first: conservation at every hop, live against final every hour, and canary events whose count I know, so a wrong number pages even when every system is healthy.", "[pause: 1.0]"])
