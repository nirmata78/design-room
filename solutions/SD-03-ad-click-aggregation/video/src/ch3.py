from dsl import *
P = "[+]"

chapter(3, "Theory", 2, "What makes counting money hard, in terms that outlive the products", [
 "C: Before any design, the theory: what makes this hard, in terms that will outlive any product name. Five mechanisms, then the options, then what will go wrong."])

S(plain("Theory · what it is", "Counting events that are money", cards(
  ("", "It is", "Counting each event once, in the hour it happened, and being able to reproduce and trace every billed number."),
  ("amb", "Not monitoring", "Metrics can be approximate and can drop a sample. A bill cannot."),
  ("amb", "Not analytics uniques", "“About 2 % off” is fine for reach on a dashboard; never on an invoice."),
  ("amb", "Not a ledger", "A ledger moves balances with double entry. We produce counts that a ledger later charges."), cols=2)), [
 "C: What it is, and what it is not.", P,
 "V: Counting events that are money: each one counted once, in the hour it happened, with every billed number reproducible and traceable to its events.", P,
 "C: It is not monitoring. Metrics can be approximate and can drop a sample. A bill cannot.", P,
 "C: It is not analytics uniques. Two percent off is fine for reach on a dashboard, never on an invoice.", P,
 "C: And it is not a ledger. A ledger moves balances with double entry. We produce the counts that a ledger later charges."])

S(plain("Theory · properties", "Safety and liveness, stated separately", cards(
  ("red", "S1 · once", "An accepted event is never lost and never billed twice."),
  ("red", "S2 · right hour, right version", "Billed in the hour it happened; not at all once invalidated; a sent invoice is never edited."),
  ("red", "S3 · reproducible", "Every billed number can be recomputed and traced to its events."),
  ("grn", "L1 · final", "Every accepted event reaches a final hour, or an adjustment, within 48 hours plus the run."),
  ("grn", "L2 · fresh", "Live counts reflect an event within 10 seconds."), cols=3)), [
 "C: The properties, safety and liveness separately. Safety is what must never happen.", P,
 "V: S-one: an accepted event is never lost, and never billed twice.", P,
 "V: S-two: it is billed in the hour it happened, not at all once invalidated, and a sent invoice is never edited.", P,
 "V: S-three: every billed number can be recomputed and traced to its events.", P,
 "C: Liveness is what must eventually happen. L-one: every accepted event reaches a final hour, or an adjustment, within forty-eight hours plus the run.", P,
 "C: L-two: the live counts reflect an event within ten seconds. Notice L-two is the only one with seconds in it. That's the tension."])

S(plain("Theory · the central tension", "Answer sooner, or answer right", cards(
  ("", "Answer sooner", "Count as events arrive: fresh, but duplicates and late events are still coming. Provisional."),
  ("grn", "Answer right", "Wait until the hour is complete and count everything once: exact, but two days late."),
  ("amb", "Do both, from one log", "The same code, run twice over the same immutable events. The fast run converges to the right one."), cols=3)), [
 "C: The tension, which the cold open drew as one hour with three numbers.", P,
 "C: Answer sooner: count as events arrive. Fresh, but duplicates and late events are still coming, so the number is provisional.", P,
 "C: Answer right: wait until the hour is complete, and count everything once. Exact, but two days late.", P,
 "C: The way out is not to pick one. It is to do both from one immutable log, with the same code, so the fast number converges to the right one and any difference has a name."])

def mech(n, name, prot, how, rules, cost, say):
    S(plain(f"Theory · mechanism M{n}", name, cards(("", "Protects", prot), ("grn", "How it works", how), ("red", "Rules out", rules), ("amb", "Costs", cost), cols=2), ), say)

mech(1, "Idempotency by event ID", "S1: once.", "The SDK or ad server mints an ID when the event happens. Every later stage keeps the first copy of each ID and drops the rest.",
     "A retry, a redelivery or a replay counted twice.", "An ID minted upstream; state per ID for the dedup window.", [
 "C: Mechanism one: idempotency by event I-D.", P, "C: It protects S-one, counting once.", P,
 "C: The S-D-K or the ad server mints an I-D at the moment the event happens, not when it is sent. Every later stage keeps the first copy of each I-D and drops the rest.", P,
 "C: It rules out a retry, a redelivery or a replay being counted twice.", P,
 "C: It costs an I-D minted upstream, which we do not control, and state per I-D for as long as the dedup window lasts. We sized that: point seven terabytes for ten minutes."])

mech(2, "Event time, with watermarks", "S2: the right hour. L2: fresh.", "Count by the time in the event. A watermark says “nothing older is still coming”; a window fires when it passes, early results before.",
     "A late or replayed event landing in the hour it arrived.", "Waiting; state for open windows; a cutoff, after which late events become corrections.", [
 "C: Mechanism two: event time, with watermarks.", P, "C: It protects S-two, the right hour, and with early results, L-two.", P,
 "C: I count by the time in the event, not the time it arrived. A watermark is the job's claim that nothing older is still coming; a window's final result fires when it passes, early results before.", P,
 "C: It rules out a late or replayed event landing in the hour it happened to arrive in.", P,
 "C: It costs waiting, state for every window still open, and a cutoff. After the cutoff, a late event becomes a correction, not a count."])

mech(3, "Re-run over an immutable log; replace, never increment", "S1 on replay; S3: reproducible.", "The output is a pure function of pinned inputs, written as a replacement keyed by what it counts.",
     "A replay doubling a number; an invoice nobody can reproduce.", "Keeping raw events for the retention; computing twice.", [
 "C: Mechanism three, the one this whole design leans on: a deterministic re-run over an immutable log, where outputs replace, never increment.", P,
 "C: It protects S-one under replay, and S-three, reproducibility.", P,
 "C: The output is a pure function of pinned inputs, written as a replacement keyed by what it counts: this ad and minute, or this campaign, hour and version. Running it again writes the same row again.", P,
 "C: It rules out a replay doubling a number, and an invoice nobody can reproduce.", P,
 "C: It costs keeping raw events for the whole retention, and computing twice."])

mech(4, "Two-stage aggregation: sharded counters", "L2 under skew.", "Sum locally where events already are, for a second; then merge the partial sums by key. Store a counter as N shard rows; sum on read.",
     "One hot key stalling one task, and with it the whole job.", "One more stage; a sum on read; a second of delay.", [
 "C: Mechanism four: two-stage aggregation, which is the sharded counter idea applied in time.", P, "C: It protects L-two when the load is skewed.", P,
 "C: Each task sums the events it already has, for one second, and only then sends a partial sum to be merged by key. In the store, a hot counter is N shard rows, summed on read.", P,
 "C: It rules out one hot key stalling one task, and with it the whole job.", P,
 "C: It costs one more stage, a sum on every read, and a second of delay."])

mech(5, "Mergeable sketches: HyperLogLog", "L2 for unique reach.", "Hash each user into 4,096 registers that keep the longest run of leading zeros. Sketches merge by taking the maximum.",
     "Exact distinct counts per campaign and minute, which do not fit.", "About 1.6 % error; no deletes. Never on the bill.", [
 "C: Mechanism five, small but asked about: HyperLogLog, for unique reach.", P, "C: It protects L-two for one number advertisers love: how many distinct people saw the ad.", P,
 "C: Each user I-D is hashed into one of four thousand and ninety-six registers, each keeping the longest run of leading zeros it has seen. Sketches merge by taking the maximum per register, so minutes merge into hours.", P,
 "C: It rules out exact distinct counts per campaign and minute, which would not fit in memory.", P,
 "C: It costs about one point six percent error, and it cannot remove a user. So it is never on the bill."])

S(plain("Theory · the options", "Five ways to count, one picked", table(["Approach", "Fresh", "Exact, replayable", "Fails when"], [
  ["A · a counter per event in a database", "yes", "no", "30 M writes a second; hot rows; every retry counts"],
  ["B · batch only, over the lake", "no", "yes", "the dashboard is a day behind"],
  ["C · stream only: the stream result is the bill", "yes", "partly", "late events past the state lifetime are lost; a fix means replaying months"],
  ["D · Lambda: a stream job and a batch job, two codebases", "yes", "yes", "two implementations drift; every difference is a mystery"],
  ("pick", ["<b>E · one aggregation code, run twice</b>: streaming, then bounded at the cutoff", "yes", "yes", "compute twice; the bill waits 48 h"])], "bt xs mx") +
  line("Kappa in code, Lambda in time: one codebase, two runs over the same log.", "a")), [
 "C: Five ways to do it.", P,
 "C: A, a counter per event in a database: thirty million writes a second, hot rows, and every retry counts.", P,
 "C: B, batch only: exact, but the dashboard is a day behind.", P,
 "C: C, stream only, where the stream's result is the bill: a late event past the state's lifetime is lost, and a bug fix means replaying months.", P,
 "C: D, Lambda, written twice: it works until the two implementations drift.", P,
 "C: E, which I pick: one aggregation code, run twice. Streaming for the dashboard, then the same operators in batch mode over each closed hour.", P,
 "V: Kappa in code, Lambda in time. I give up computing twice, and a bill that waits forty-eight hours.", "[pause: 0.8]"])

S(plain("Theory · the mechanisms at work", "Where each mechanism will live", table(["Mechanism", "Where", "In one clause"], [
  ["M1 · event ID", "SDK, live aggregator, billing job", "minted at the source; dropped if seen, for 10 minutes live and the whole hour billed"],
  ["M2 · event time", "live aggregator, hour closer", "watermark minus 2 minutes; the bill closes at 48 hours"],
  ["M3 · replace, never increment", "live store, billing tables", "rows keyed by what they count, with a version"],
  ["M4 · two-stage sums", "live aggregator, live store", "512 partial sums a second; shard rows summed on read"],
  ["M5 · sketches", "live aggregator", "reach per campaign-minute, merged on read"]], "bt xs mx")), [
 "C: Where each one will live. I'll draw the system once, in the design chapter, and these labels come back on it at the end.", P,
 "C: M-one, the event I-D: minted in the S-D-K, dropped if seen, for ten minutes on the live path and for the whole hour on the billing run.", P,
 "C: M-two, event time: a watermark two minutes behind the latest event, and a billing cutoff at forty-eight hours.", P,
 "C: M-three, replace, never increment: in the live store and the billing tables, rows keyed by what they count, with a version.", P,
 "C: M-four, two-stage sums: five hundred and twelve partial sums a second, and shard rows summed on read.", P,
 "C: M-five, sketches: reach per campaign and minute, merged when the dashboard asks."])

S(dia("Theory · mechanism M2 at work", "A watermark, an early result, an on-time result, a late update", "seq-th-watermark"), [
 "C: Mechanism two at protocol level: one window, ad seventy-seven, the minute starting at fourteen hundred, fed by two partitions.", P,
 "C: Partition one delivers an impression with event time fourteen hundred and fifty-eight seconds.", P,
 "C: Partition two, one at fourteen oh one thirty.", P,
 "C: The watermark is the minimum over partitions of the latest time minus two minutes: thirteen fifty-eight fifty-eight. The minute is still open.", P,
 "C: But the dashboard should not wait, so the window emits an early result: twelve hundred and twelve, version one.", "[+2]",
 "C: Later events arrive, from both partitions.", P,
 "C: Now the watermark is fourteen oh one oh five. It has passed the end of the minute.", P,
 "C: So the on-time result fires: thirteen eighteen, version two, and it replaces version one. It does not add to it.", P,
 "C: Then a late event for that minute, within the allowed hour.", P,
 "C: Version three, thirteen nineteen. No lock and no wall clock: event times, a minimum, and a version."], cls="dia")

S(plain("Theory · the failure catalogue", "What will go wrong, in the order I'll take it", table(["#", "Failure", "Property at risk"], [
  ["1", "The same event arrives three times", "S1"],
  ["2", "Events arrive a day late, with skewed clocks", "S2"],
  ["3", "One ad takes 2 million impressions a second", "L2"],
  ["4", "A job crashes, or a bug forces a four-hour replay", "S1, S3"],
  ["5", "Fraud invalidates clicks after the invoice", "S2, S3"],
  ["6", "A number is wrong and nobody notices", "all of them"]], "bt sm")), [
 "C: The failure catalogue. It becomes the challenge list.", P, "C: One: the same event arrives three times.", P, "C: Two: events arrive a day late, with skewed clocks.", P,
 "C: Three: one ad takes two million impressions a second.", P, "C: Four: a job crashes, or a bug forces a four-hour replay.", P,
 "C: Five: fraud invalidates clicks after the invoice.", P, "C: And six: a number is wrong, and nobody notices. I'll come back to each."])
