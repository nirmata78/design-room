from dsl import *
P = "[+]"

# ───────────────────────── 1 · prompt, clarifying questions, C4 context ─────────────────────────
chapter(1, "Prompt, questions and context", 0, "Count ad events that are money", [
 "C: Counting clicks sounds like n equals n plus one. It is one of the most asked questions at Google and Meta, because at thirty million events a second the hard part is not counting fast. It is counting once, in the right hour, and being able to prove it."])

qs("Interviewer · the prompt", "“Design the system that counts ad impressions and clicks. Advertisers watch their numbers live on a dashboard, and they are billed on the hourly totals.”", [
 "I: Design the system that counts ad impressions and clicks. Advertisers watch their numbers live on a dashboard, and they are billed on the hourly totals.", "[pause: 1.5]"])

S(dia("Why it is harder than it looks", "One hour's number, three times", "tension",
      chip=chips("fast and provisional", "exact and billed", "corrected, never edited"), cap="One hour of one campaign: live, final, corrected"), [
 "C: Here is the hook, as one picture: the same hour of one campaign has three numbers.",
 "C: Ten seconds in, the live number: fast and provisional, because duplicates and late events are still arriving. At forty-eight hours, the final number: exact, and invoiced. Nine days later fraud invalidates two percent, and a third number must become an adjustment, never an edit.",
 "C: The whole design is about producing all three from one source, and saying which one you are looking at."])

S(plain("Before the design", "What this question grades", table(["Axis", "Weak signal", "Strong signal"], [
  ["<b>Requirements</b>", "“Count clicks”, one number for everything", "Asks which numbers are money, how late events arrive, who can invalidate them"],
  ["<b>Correctness</b>", "<code>n = n + 1</code>; “exactly-once” by name", "IDs minted at the source; dedup; event time; replace, never increment"],
  ["<b>Trade-offs</b>", "Lambda or Kappa, recited", "One aggregation code run twice, and what each run gives up"],
  ["<b>Depth</b>", "Stops at “Kafka and Flink”", "Watermarks, keyed state with a TTL, two-stage sums, pinned re-runs"],
  ["<b>Operations</b>", "CPU and consumer lag", "Conservation checks, live against final, canaries, an audit trail"]], "bt xs sig") +
  grade("The bill is the product; the dashboard is a preview of it.")), [
 "N: What this question grades.", P,
 "N: Requirements: which numbers are money, and who can take them back.", P,
 "N: Correctness: an ID minted at the source, event time, numbers replaced rather than incremented.", P,
 "N: Trade-offs: what you run twice, and what each run gives up.", P,
 "N: Depth: watermarks, keyed state and pinned re-runs, not just Kafka and Flink.", P,
 "N: Operations: checks on the numbers, because lag and CPU stay green while the count is wrong.", P,
 "C: And the rule I'll keep for the whole round: the bill is the product. The dashboard is a preview of it, and must say so."])

S(plain("Requirements · the scale line", "Three numbers every estimate starts from", '<div class="tiles" style="--n:3">'
  '<div class="tile blue"><b>25 T · 250 B</b><span>impressions · clicks a month</span></div>'
  '<div class="tile"><b>6 months</b><span>of raw events kept: ~150 trillion</span></div>'
  '<div class="tile red"><b>30 M/s</b><span>evening peak; one ad at 2 M/s</span></div></div>' +
  line("Every number later in this video starts from one of these three, and I'll say which.", "a")), [
 "C: The interviewer gives me the scale, and I write it down first.", P,
 "C: Twenty-five trillion impressions and two hundred and fifty billion clicks a month. A one percent click-through rate.", P,
 "C: Raw events are kept six months, about a hundred and fifty trillion of them.", P,
 "C: And the peak: thirty million events a second in the evening, three times the average. Inside it, one prime-time ad during a sports break takes two million impressions a second on its own.", P,
 "C: Every number I use later starts from one of these three, and I'll say which."])

def clar(n, q, a, ask, ans, so):
    S(f'<div class="who">Clarifying question {n} of 4</div><div class="qq">{q}</div><div class="ans">{a}</div>',
      ["C: " + ask, P, "I: " + ans, "C: " + so], cls="qs")

clar(1, "How fresh must the dashboard be?", "Within about 10 seconds. The bill: hourly totals, final within two days.",
     "How fresh does the dashboard have to be, and the bill?", "Within about ten seconds for the dashboard. The bill is hourly totals, final within two days.",
     "So two clocks. If someone asks for sub-second, I'd ask back: for one headline number, maybe; for slicing by country and hour, it costs a different system.")
clar(2, "Which numbers have to be exact?", "The bill: exact and auditable. The dashboard may be slightly off, but it must converge to the bill.",
     "Which numbers have to be exact?", "The bill: exact, and auditable. The dashboard can be slightly off, but it has to converge to the bill.",
     "That sentence is the design. One exact run for money, one fast run for people, and the fast one never disagrees for long.")
clar(3, "Do events arrive twice, or late?", "SDKs retry. Phones buffer offline for hours, sometimes days. Client clocks are skewed.",
     "Can the same event arrive twice, or late?", "Yes. SDKs retry on network errors. Phones buffer offline for hours, sometimes days. And client clocks are skewed.",
     "Duplicates mean an ID per event. Late means event time, not arrival time. Skewed means I can't trust that time blindly. Three challenges already.")
clar(4, "What about fraud?", "A separate system. It can invalidate events after invoices have gone out.",
     "Who decides that a click was fraud, and when?", "A separate system. It can invalidate events after the invoices have gone out.",
     "So a closed hour can change. I need versions of an hour, and a way to bill the difference without editing an invoice.")

S(plain("Requirements · functional", "Four things the system must do", cards(
  ("", "FR1 · Record", "Accept impression and click events; acknowledge once durable; a retry changes nothing."),
  ("grn", "FR2 · Live", "Per ad and campaign: impressions, clicks, spend and approximate reach, within 10 seconds."),
  ("amb", "FR3 · Bill", "Exact hourly totals per campaign and ad, final at a cutoff, versioned, exported."),
  ("red", "FR4 · Correct", "Late events and invalidations reach closed hours as new versions and adjustment lines."))), [
 "C: Four functional requirements.", P,
 "C: One, record: accept the events, acknowledge only once they are durable, and a retry changes nothing.", P,
 "C: Two, live: impressions, clicks, spend and an approximate unique reach per ad and campaign, within ten seconds.", P,
 "C: Three, bill: exact hourly totals, final at a cutoff, versioned, and exported to invoicing.", P,
 "C: Four, correct: late events and invalidations reach a closed hour as a new version and an adjustment line. A sent invoice is never edited."])

S(plain("Requirements · non-functional", "The numbers, and what each is for", '<p class="chips">all initial targets, not measurements</p><div class="tiles" style="--n:4">'
  '<div class="tile blue"><b>30 M/s</b><span>ingest at peak; ack p99 50 ms</span></div>'
  '<div class="tile blue"><b>10 s</b><span>live freshness, p99</span></div>'
  '<div class="tile"><b>H + 48 h</b><span>bill final; re-run bit for bit</span></div>'
  '<div class="tile red"><b>99.99 %</b><span>ingest: a dropped event is lost money</span></div></div>' +
  line("An acknowledged event survives the loss of a zone.", "a")), [
 "C: The numbers, and they are initial targets.", P,
 "C: Thirty million events a second at peak, acknowledged within fifty milliseconds at the ninety-ninth percentile.", P,
 "C: Live counts within ten seconds.", P,
 "C: The bill final forty-eight hours after the hour, and a re-run of any day gives the same numbers, bit for bit. Raw events are kept six months; disputes run ninety days.", P,
 "C: Four nines on ingest, because an event we drop is revenue we cannot bill.", P,
 "C: And an acknowledged event survives losing a whole zone."])

S(plain("Requirements · properties", "What must never happen, and what must eventually happen", cards(
  ("red", pid("S1"), "Never lost, never billed twice."),
  ("red", pid("S2"), "Billed in its hour; not at all once invalid; an invoice is never edited."),
  ("red", pid("S3"), "Every billed number recomputed and traced to its events."),
  ("grn", pid("L1"), "Every event reaches a final hour or an adjustment within 48 h."),
  ("grn", pid("L2"), "Live counts reflect an event within 10 s."), cols=3)), [
 "C: As properties, so every fix can say which one it protects. Safety first.", P,
 f"V: {ps('S1')}: an accepted event is never lost, and never billed twice.", P,
 f"V: {ps('S2')}: billed in the hour it happened, not at all once invalidated, and a sent invoice is never edited.", P,
 f"V: {ps('S3')}: every billed number can be recomputed and traced to its events.", P,
 f"C: Liveness. {ps('L1')}: every event reaches a final hour or an adjustment within forty-eight hours.", P,
 f"C: {ps('L2')}: live counts within ten seconds. The only one with seconds in it: that is the tension."])

S(plain("Requirements · scope", "In, and out on purpose", cards(
  ("grn", "In scope", "Ingest, dedup, live counts, approximate reach, hourly billing totals, versions, corrections, an audit trail, reconciliation."),
  ("red", "Out, on purpose", "Fraud detection itself. Ad serving and auctions. Budget pacing. Invoicing and payment. Attribution.")) +
  line("Budget pacing is a consumer of the live counts: it is why they must be fast.", "")), [
 P, "C: In scope: ingest, dedup, live counts, approximate reach, the hourly billing totals with versions and corrections, an audit trail and reconciliation.", P,
 "C: Out, on purpose: fraud detection itself, ad serving and the auction, budget pacing, invoicing and payment, and conversion attribution.", P,
 "C: One of those I'd say aloud: budget pacing reads the live counts to stop a campaign that has spent its budget. That is why the live numbers must be fast, even though they are not the bill."])

stage("C4 level 1 · system context", "The system in its context, before any boxes inside it", "c4-context", [
 "C: Before any boxes inside it, the system in its context. I draw this first, in every round.", P,
 "C: Ad clients: SDKs in apps, browsers, and ad servers. They send every impression and click, in batches, over HTTPS. Ninety-nine percent of the traffic.", P,
 "C: In the middle, the system, one box for now: live counts and exact hourly totals.", P,
 "C: Advertisers read dashboards, and are billed.", P,
 "C: A fraud system invalidates events, and it can do that late, after the bill. That arrives as events, not calls.", P,
 "C: And invoicing reads our final hours as a batch export. Nothing on the ingest path waits for any of them."],
 cap="C4 system context: who sends events, who reads them, and the two systems around the bill")

key("The core", "The core is three things: an <em>idempotent, durable intake</em>; <em>one aggregation, run twice</em>; and <em>versioned final hours</em> with a correction path.", [
 "V: The core is three things. An idempotent, durable intake. One aggregation, run twice. And versioned final hours, with a correction path.", "[pause: 0.8]",
 "N: Notice the candidate fixed the scale, named the properties and drew the context before any internals. That is the scoping signal."])
