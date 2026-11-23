from dsl import *
from stack import REJ
P = "[+]"
B = lambda x: f'<span class="bad">{x}</span>'

# ───────────────────────── 6 · bridge ─────────────────────────
chapter(6, "Bridge", 5, "It works. Where does it break first?", [
 "V: It works. The question now is where it breaks first.", "[pause: 1.0]"])

S(dia("Challenge map", "Six challenges, five places on the same picture", "map", chip=chips("each fix creates the next question")), [
 P, "C: Version three, with the places it will break marked one at a time.", P,
 "C: The collector, where a retry arrives as a second copy. Challenge one.", P,
 "C: The live aggregator: late events and skewed clocks, one ad at two million a second, and a crash with a replay. Challenges two, three and four.", P,
 "C: The billing job, where the hour has to close at the right moment and re-run safely.", P,
 "C: The billing tables, when fraud changes its mind after the invoice. Challenge five.", P,
 "C: And the reporting A-P-I, where an advertiser says our number is wrong. Challenge six: how would we know first?"], cls="dia")

chapter(7, "Challenges", 5, "Six ways to break it, and what survives", [
 "C: Six challenges, each the same way: the question, the naive answer, a case with numbers, where it breaks inside the container, the fix one level down, then the push on the fix itself, and what I'd say in the room."])

K = lambda n, t: f"Challenge {n} of 6 · {t}"

# ───────── Challenge 1 · the same click, three times ─────────
subchapter("7.1", "Challenge 1: The same click, three times", ["N: Challenge one is the crux of this question: a retry. Most answers name a guarantee here. The grade is for the mechanism."])
qs("Interviewer · challenge 1 of 6", "“A retrying client sends the same click three times, two seconds apart. Walk me through it.”", [
 "I: A retrying client sends the same click three times, two seconds apart. Walk me through it.", "[pause: 2.0]"])

S(dia(K(1, "three copies"), "Who notices that a click is a repeat?", "ch1-attack", q=True, red=True,
      extra=strip(("case", "Naive answer", "“Kafka is exactly-once, so duplicates can't happen.”"),
                  ("case", "Break", "Nothing in the live aggregator remembers an ID: three copies, three counts."))), [
 P, "C: The live aggregator, opened up.", P, "C: Marked: where a deduplicator should be, and in the naive design there isn't one.", P,
 "C: The naive answer: Kafka is exactly-once, so duplicates can't happen.", P,
 "C: But the duplicates were made before Kafka. Three copies arrive, and nothing remembers an I-D, so three are counted, on the dashboard and on the bill."], cls="dia")

S(trace(K(1, "the trace"), "One click, a lost answer, two retries", [
  ("10:00:00.000", "the SDK sends batch B17 with click <code>e7f3…</code>"),
  ("10:00:00.040", "the collector appends it at offset 81,220; Kafka acknowledges"),
  ("10:00:00.900", "the 202 is lost on the cell network"),
  ("10:00:02.900", "the SDK retries B17: offset 81,977, " + B("a second copy")),
  ("10:00:04.900", "and again: offset 82,610, " + B("a third"))],
  hedge=("At scale", "0.3 % of batches retried is about 750 million duplicate clicks a month: about $375 M billed twice, illustrative.")), [
 "C: The trace.", P, "C: At ten o'clock the S-D-K sends batch B-seventeen, with click e-seven-f-three.", P,
 "C: Forty milliseconds later it is at offset eighty-one thousand two hundred and twenty, acknowledged.", P,
 "C: The two-oh-two is lost on the cell network.", P, "C: Two seconds later the S-D-K retries: a second copy.", P, "C: And again: a third.", P,
 "C: Nobody did anything wrong. And at three tenths of a percent of batches, it's three hundred and seventy-five million dollars a month, billed twice."])

S(dia(K(1, "the fix"), "Drop a repeat by the ID minted at the source", "ch1-fix",
      extra=strip(("fixb", "Mechanism", "Keyed state by event ID in RocksDB, TTL 10 min, checkpointed with the offsets. The billing run keeps the first row per ID over the whole hour."),
                  ("whyb", "Covers, and does not", "Covers every retry, redelivery and replay of one event. Not a client minting new IDs per click: that is fraud's job.")) + rejl(*REJ(1))), [
 P, "C: The fix, on the same view.", P, "C: The deduplicator.", P, "C: And the checkpoints that keep its state.", P,
 "C: One level down: state keyed by event I-D, in Rocks-D-B, with a ten-minute lifetime. A record whose I-D is already there is dropped. The state is checkpointed with the Kafka offsets, and the billing run keeps the first row per I-D over the whole hour. The log is keyed by event I-D, so all three copies meet the same state.", P,
 "C: It covers every retry, redelivery and replay of one event. Not a client that mints a new I-D per click: that's fraud's job.", P,
 "C: Rejected: Kafka's exactly-once, with transactions. It removes a producer's own retry inside one session. An S-D-K retry over H-T-T-P-S is a new request, and only dedup on the event I-D removes it."], cls="dia")

S(dia(K(1, "sequence"), "Three copies in, one count out", "seq-ch1-retry"), [
 "C: As a sequence.", P, "C: Batch B-seventeen.", P, "C: Appended.", P, "C: Acknowledged.", P,
 "C: The answer is lost.", P, "C: The retry, same I-Ds.", P, "C: Appended again, on the same partition.", P,
 "C: Both reach the deduplicator.", P, "C: e-seven-f-three is in state: the second is dropped.", P,
 "C: And the billing run keeps the first row per I-D in the hour. Once, by construction."], cls="dia")

qs("Interviewer · the second-level push", "“The job restarts and loses its state. Or the retry comes eleven minutes later.”", [
 "I: The job restarts and loses its state. Or the retry comes eleven minutes later.", "[pause: 1.5]"])

S(plain(K(1, "the second fix, and the honest limit"), "Restored with the offsets; bounded on the live path", cards(
  ("grn", "A restart", "State is restored from the checkpoint with the offsets it matches: a re-read record meets the state that saw it."),
  ("amb", "Eleven minutes late", "The live view counts it twice, until the hour closes; the bill keeps the first row per ID over the whole hour."),
  ("", "Why ten minutes", "SDK retries stop after five minutes; ten is twice that. The reconciler counts late duplicates, so it is measured."), cols=3)), [
 "C: Three answers.", P,
 "C: A restart doesn't lose state. It is restored from the checkpoint, together with the offsets it matches, so a record read again meets the state that already saw it.", P,
 "C: A retry eleven minutes later passes the live path, and the live view is two clicks high until the hour closes. The bill isn't: its dedup covers the whole hour, and the final hour replaces the live one.", P,
 "C: And why ten minutes: S-D-K retries stop after five, ten is twice that, and the reconciler counts late duplicates, so the window is a measured choice, not a guess."])

say_slide("“Every event carries an ID minted where it happened, so a retry is recognisable. The live path drops repeats in keyed state for ten minutes; the billing run drops them over the whole hour. Exactly-once isn't a broker setting: it is at-least-once delivery plus that dedup.”", [
 "V: If asked, I'd say: every event carries an I-D minted where it happened, so a retry is recognisable. The live path drops repeats in keyed state for ten minutes, and the billing run drops them over the whole hour. Exactly-once isn't a broker setting. It's at-least-once delivery plus that dedup.", "[pause: 1.0]",
 "N: That fix creates the next question: the I-D says which event it is. It doesn't say when it happened."])

# ───────── Challenge 2 · yesterday's events at 6 a.m. ─────────
subchapter("7.2", "Challenge 2: Yesterday's events at 6 a.m.", ["N: Challenge two: time. Which clock decides the hour an event is billed in?"])
qs("Interviewer · challenge 2 of 6", "“A phone was offline overnight. Three hundred impressions from Tuesday evening arrive on Wednesday at six. Which hour gets billed?”", [
 "I: A phone was offline overnight. Three hundred impressions from Tuesday evening arrive on Wednesday at six. Which hour gets billed?", "[pause: 2.0]"])

S(dia(K(2, "late events"), "Which clock decides the hour?", "ch2-attack", q=True, red=True,
      extra=strip(("case", "Naive answer", "“Count them when they arrive.”"),
                  ("case", "Break", "The time assigner uses arrival time: Tuesday's hours come up short, Wednesday 06:00 over."))), [
 P, "C: Three components of the live aggregator.", P, "C: The time assigner is marked.", P,
 "C: The naive answer: count them when they arrive.", P,
 "C: Then the time assigner uses arrival time. Tuesday's hours come up short, and Wednesday six o'clock is over."], cls="dia")

S(trace(K(2, "the trace"), "A flight, a campaign that ended, and a clock in 2031", [
  ("Tue 21:10–23:40", "300 impressions on a phone with no signal, buffered"),
  ("Tue 23:59", "the campaign's flight ends"),
  ("Wed 06:00", "the phone reconnects; the batch arrives"),
  ("Wed 06:00", B("counted in Wednesday 06:00: billed after the campaign ended")),
  ("Wed 06:01", "another phone says <code>client_ts</code> = 2031-01-01: " + B("an hour that never closes"))],
  hedge=("What it costs", "A charge outside the flight dates is a dispute. A clock in 2031 is a window held open for years.")), [
 "C: The trace.", P, "C: Tuesday evening, three hundred impressions on a phone with no signal.", P, "C: At midnight the campaign's flight ends.", P,
 "C: At six on Wednesday the phone reconnects.", P, "C: Counted at arrival, those impressions are billed after the campaign ended.", P,
 "C: And another phone says its clock is in twenty thirty-one. Trust that, and an hour opens that never closes.", P,
 "C: So I need event time, and I can't trust it blindly."])

S(dia(K(2, "the fix"), "Event time, clamped; a watermark for the dashboard", "ch2-fix",
      extra=strip(("fixb", "Mechanism", "Event time = client time if within 72 h before to 5 min after the server time; else server time, flagged. Watermark = min over partitions of latest − 2 min; 1 h of lateness."),
                  ("whyb", "Covers, and does not", "Late and skewed events up to the billing cutoff. After it, a new version of the hour: challenge five.")) + rejl(*REJ(2))), [
 P, "C: The fix, on the same components.", P, "C: The time assigner.", P, "C: And the window counter.", P,
 "C: One level down. The event time is the client's time if it lies between seventy-two hours before and five minutes after the server's time. Otherwise it's the server time, and the event is flagged as clamped. The watermark is the minimum, over partitions, of the latest event time minus two minutes. And a minute window accepts an hour of lateness after that.", P,
 "C: It covers late and skewed events up to the billing cutoff. After the cutoff, an event changes a closed hour, and that's challenge five.", P,
 "C: Rejected: processing-time windows. They bill a phone's Tuesday evening in Wednesday's six a.m. hour."], cls="dia")

S(plain(K(2, "the rule, as pseudocode"), "Clamp, then let the slowest partition set the pace",
  pseudo("t = e.client_ts\nif t < e.server_ts - 72h or t > e.server_ts + 5m:\n    t, e.clamped = e.server_ts, true\ne.event_time = t\n\nwatermark = min(latest(p) - 2m for p in active)\nwhen watermark >= w.end: emit(w, version + 1)\nwhen e is late and watermark < w.end + 1h:\n    add(w, e); emit(w, version + 1)\nelse: count_late(e)       # the lake still has it", hl=(2, 6, 8))), [
 "C: As pseudocode. The key lines are marked.",
 "C: Line two: a client time outside the window is replaced by the server time. Line six: the watermark is a minimum over active partitions, two minutes behind. Line eight: a late event inside the hour of allowed lateness updates its window, which is emitted again with a higher version. Anything later is only counted as late. The lake still has it, so the bill still will.",
 "C: Why it works: a minimum means one fast partition can't close a minute that a slow one is still filling, and the clamp bounds what a bad clock can do."])

S(dia(K(2, "the close"), "The bill waits for the hour to be complete", "ch2-close",
      extra=strip(("fixb", "At H + 48 h", "The hour closer pins a snapshot of hour H's partition: every file landed so far, late ones included. The run reads exactly that."),
                  ("whyb", "Why 48 hours", "An initial target, to measure: if 99.99 % of events arrive within 36 h, the rest become version 2 at a cost of one adjustment."))), [
 P, "C: The live view is one half. The bill is the other, inside the billing job.", P, "C: The hour closer.", P,
 "C: At forty-eight hours it pins a snapshot of that hour's partition: every file landed so far, the late ones included, because files are partitioned by event hour, not by arrival. The run reads exactly that snapshot, and nothing that lands later.", P,
 "C: Why forty-eight hours: it's an initial target, to be measured. If ninety-nine point nine nine percent of events arrive within thirty-six hours, the rest become a version two, at the cost of one adjustment."], cls="dia")

qs("Interviewer · the second-level push", "“One partition goes quiet. Or a bad SDK release sends every clock a day off.”", [
 "I: One partition goes quiet. Or a bad S-D-K release sends every clock a day off.", "[pause: 1.5]"])

S(plain(K(2, "the second fix, and the honest limit"), "An idle timeout, a flag, and versions", cards(
  ("grn", "A quiet partition", "Excluded from the watermark after 30 s of silence, so one idle partition cannot freeze every dashboard."),
  ("amb", "A bad SDK clock", "Clamped to server time and flagged; an alert when the clamped share passes 0.1 %, by SDK version."),
  ("red", "Honest limit", "An event past the cutoff changes a closed hour: version 2 and an adjustment, never a silent edit."), cols=3)), [
 P, "C: A quiet partition would hold the minimum back forever, so it is excluded from the watermark after thirty seconds of silence.", P,
 "C: A bad S-D-K clock is clamped to server time and flagged, and an alert fires when the clamped share passes a tenth of a percent, broken down by S-D-K version, so the release is found in minutes.", P,
 "C: And the honest limit: an event past the cutoff does change a closed hour. It becomes version two and an adjustment, never a silent edit."])

say_slide("“The event's own time decides its hour, clamped against server time so a broken or hostile clock can't move it far. The dashboard waits two minutes and accepts an hour of lateness; the bill closes at forty-eight hours from a snapshot of everything that landed for that hour, and anything later becomes a new version.”", [
 "V: If asked, I'd say: the event's own time decides its hour, clamped against server time so a broken or hostile clock can't move it far. The dashboard waits two minutes and accepts an hour of lateness. The bill closes at forty-eight hours from a snapshot of everything that landed for that hour, and anything later becomes a new version.", "[pause: 1.0]",
 "N: That fix creates the next question: the windows are keyed by ad. What if one ad is the whole stream?"])

# ───────── Challenge 3 · one ad at two million a second ─────────
subchapter("7.3", "Challenge 3: One ad at 2 million a second", ["N: Challenge three: overload, but not the kind more machines fix."])
qs("Interviewer · challenge 3 of 6", "“A sports break puts one ad on every screen: two million impressions a second. What happens to your job?”", [
 "I: A sports break puts one ad on every screen: two million impressions a second. What happens to your job?", "[pause: 2.0]"])

S(dia(K(3, "a hot ad"), "One key is one task", "ch3-attack", q=True, red=True,
      extra=strip(("case", "Naive answer", "“Key by ad, and add machines.”"),
                  ("case", "Break", "Keyed by ad, one window task gets all 2 M/s; its backpressure slows every partition."))), [
 P, "C: The middle of the live aggregator.", P, "C: The window counter is marked.", P,
 "C: The naive answer: key by ad, and add machines.", P,
 "C: But a key lives on exactly one task. Machines don't help it. That one task gets all two million a second, and its backpressure slows every partition."], cls="dia")

S(trace(K(3, "the trace"), "Ninety seconds of one ad", [
  ("20:14:00", "the break starts; ad 77 jumps from 3,000 to 2,000,000 impressions a second"),
  ("20:14:05", "the window task holding ad 77 at 100 % CPU; its input buffer fills"),
  ("20:14:20", B("backpressure: every source slows; lag grows on all 1,024 partitions")),
  ("20:15:30", B("every advertiser's dashboard is 90 s stale; budget pacing flies blind"))],
  hedge=("Not a hot partition", "The log is keyed by event ID, so its partitions are even. The hot spot is one thread.")), [
 "C: The trace.", P, "C: At twenty fourteen, ad seventy-seven goes from three thousand to two million impressions a second.", P,
 "C: Five seconds later, the one window task holding it is at a hundred percent.", P,
 "C: Backpressure. Every source slows, and lag grows on all thousand and twenty-four partitions.", P,
 "C: Ninety seconds later every advertiser's dashboard is stale, and budget pacing is flying blind, not just for ad seventy-seven.", P,
 "C: Note what is not hot: the log is keyed by event I-D, so its partitions are even. The hot spot is one thread."])

S(dia(K(3, "the fix"), "Sum where the events are, then merge", "ch3-fix",
      extra=strip(("fixb", "Mechanism", "Each of 512 subtasks sums per (ad, minute) for 1 s, then sends one partial; the merge sees 512 updates a second. The store keeps up to 16 shard rows per ad-minute, summed on read."),
                  ("whyb", "Covers, and does not", "Any number of hot ads: the cost follows active keys, not events. It adds 1 s of delay, inside the 10 s budget.")) + rejl(*REJ(3))), [
 P, "C: The fix, in the middle of the job.", P, "C: The combiner.", P, "C: And the window counter, which now merges partial sums.", P,
 "C: One level down. Each of the five hundred and twelve subtasks sums its own events per ad and minute for one second, then sends one partial sum. The window task for ad seventy-seven now sees five hundred and twelve updates a second instead of two million. And the store keeps up to sixteen shard rows per ad and minute, summed when the dashboard reads. That's the sharded counter.", P,
 "C: It covers any number of hot ads, because the cost now follows active keys, not events. It adds a second of delay, inside the ten-second budget.", P,
 "C: Rejected: Redis increment-by on one counter key. One key is one shard's thread, about a hundred thousand operations a second against two million. And a replay increments again."], cls="dia")

qs("Interviewer · the second-level push", "“Now five hundred ads are hot at once, in every break.”", [
 "I: Now five hundred ads are hot at once, in every break.", "[pause: 1.5]"])

S(plain(K(3, "the second fix, and the honest limit"), "Bounded by active keys, not by events", cards(
  ("grn", "Partial maps stay small", "One entry per active ad and minute per subtask: 500 hot ads are 500 entries, flushed every second."),
  ("amb", "The merge scales by key", "500 hot ads × 512 partials = 256,000 updates a second, spread over the merge subtasks by key."),
  ("red", "Honest limit", "Every count arrives a second later. Worth it: the budget has the room."), cols=3)), [
 "C: Five hundred hot ads.", P,
 "C: Each subtask's partial map holds one entry per active ad and minute: five hundred entries, flushed every second. Small.", P,
 "C: The merge stage sees five hundred ads times five hundred and twelve partials: about two hundred and fifty-six thousand updates a second, spread over its subtasks by key. That scales with machines, because now there are many keys.", P,
 "C: The honest limit: every count arrives a second later. The budget has the room."])

say_slide("“A hot key is a hot thread, not a hot partition: my log is keyed by event ID. So I sum where the events already are, once a second, and merge 512 partial sums instead of two million updates. On the read side, a hot counter is sixteen shard rows, summed on read.”", [
 "V: If asked, I'd say: a hot key is a hot thread, not a hot partition, because my log is keyed by event I-D. So I sum where the events already are, once a second, and merge five hundred and twelve partial sums instead of two million updates. On the read side, a hot counter is sixteen shard rows, summed on read.", "[pause: 1.0]",
 "N: That fix creates the next question: the job holds a lot of state now. What happens when it crashes, or when you have to run it again?"])
