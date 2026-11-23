from dsl import *
P = "[+]"

# ───────────────────────── 0 · cold open ─────────────────────────
chapter(0, "Cold open", -1, "Count ad events that are money", [
 "C: Counting clicks sounds like n equals n plus one. It is one of the most asked questions at Google and Meta, because at thirty million events a second the hard part is not counting fast. It is counting once, in the right hour, and being able to prove it."])

qs("Interviewer · the prompt", "“Design the system that counts ad impressions and clicks. Advertisers watch their numbers live on a dashboard, and they are billed on the hourly totals.”", [
 "I: Design the system that counts ad impressions and clicks. Advertisers watch their numbers live on a dashboard, and they are billed on the hourly totals.", "[pause: 1.5]"])

S(dia("Why it is harder than it looks", "One hour's number, three times", "tension",
      chip=chips("fast and provisional", "exact and billed", "corrected, never edited")), [
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
 "N: Five axes, one at a time.", P,
 "N: Requirements. Weak: one number for everything. Strong: which numbers are money, how late events arrive, who can take them back.", P,
 "N: Correctness. Weak: n equals n plus one, or exactly-once as a name. Strong: an I-D minted at the source, event time, and numbers replaced rather than incremented.", P,
 "N: Trade-offs. Reciting Lambda and Kappa is not one. Saying what you run twice, and what each run gives up, is.", P,
 "N: Depth. Kafka and Flink are names; watermarks, keyed state and pinned re-runs are the level down.", P,
 "N: Operations. Lag and C-P-U stay green while the count is wrong; conservation checks and canaries don't.", P,
 "C: And the rule I'll keep for the whole round: the bill is the product. The dashboard is a preview of it, and must say so."])

key("The thesis", "Count once, from <em>one log</em>, with <em>one piece of code run twice</em>: fast and provisional for the dashboard, exact and pinned for the bill. Never increment a number you can recompute: <em>replace</em> it.", [
 "V: Count once, from one log, with one piece of code run twice: fast and provisional for the dashboard, exact and pinned for the bill. Never increment a number you can recompute. Replace it.", "[pause: 1.0]"])

# ───────────────────────── 1 · requirements ─────────────────────────
chapter(1, "Requirements and scope", 0, "The scale first, then six questions", [
 "C: The scale first, then six questions. Each answer moves the design."])

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
    S(f'<div class="who">Clarifying question {n} of 5</div><div class="qq">{q}</div><div class="ans">{a}</div>',
      ["C: " + ask, P, "I: " + ans, "C: " + so], cls="qs")

clar(1, "How fresh must the dashboard be?", "Within about 10 seconds. The bill: hourly totals, final within two days.",
     "How fresh does the dashboard have to be, and the bill?", "Within about ten seconds for the dashboard. The bill is hourly totals, final within two days.",
     "So two clocks. And if someone asks for sub-second, I'd ask back: for one headline number, maybe; for slicing by country and hour, it costs a different system.")
clar(2, "Which numbers have to be exact?", "The bill: exact and auditable. The dashboard may be slightly off, but it must converge to the bill.",
     "Which numbers have to be exact?", "The bill: exact, and auditable. The dashboard can be slightly off, but it has to converge to the bill.",
     "That sentence is the design. One exact run for money, one fast run for people, and the fast one never disagrees for long.")
clar(3, "Do events arrive twice, or late?", "SDKs retry. Phones buffer offline for hours, sometimes days. Client clocks are skewed.",
     "Can the same event arrive twice, or late?", "Yes. S-D-Ks retry on network errors. Phones buffer offline for hours, sometimes days. And client clocks are skewed.",
     "Duplicates mean an I-D per event. Late means event time, not arrival time. Skewed means I can't trust that time blindly. Three challenges.")
clar(4, "What about fraud?", "A separate system. It can invalidate events after invoices have gone out.",
     "Who decides that a click was fraud, and when?", "A separate system. It can invalidate events after the invoices have gone out.",
     "So a closed hour can change. I need versions of an hour, and a way to bill the difference without editing an invoice.")
clar(5, "How long do we keep things, and why?", "Raw events 6 months; the dispute window is 90 days. Aggregates 7 years. A re-run must give the same numbers.",
     "How long do we keep events and totals?", "Raw events six months; the dispute window is ninety days. Aggregates seven years. And Finance wants a re-run of any day to give the same numbers.",
     "Same numbers on a re-run means the aggregation is a pure function of inputs I can pin. I'll hold myself to that.")

S(plain("Requirements · functional", "Four things the system must do", cards(
  ("", "FR1 · Record", "Accept impression and click events; acknowledge once durable; a retry changes nothing."),
  ("grn", "FR2 · Live", "Per ad and campaign: impressions, clicks, spend and approximate reach, within 10 seconds."),
  ("amb", "FR3 · Bill", "Exact hourly totals per campaign and ad, final at a cutoff, versioned, exported."),
  ("red", "FR4 · Correct", "Late events and invalidations reach closed hours as new versions and adjustment lines."))), [
 "C: Four functional requirements.", P,
 "C: One, record: accept the events, acknowledge only once they are durable, and a retry changes nothing.", P,
 "C: Two, live: impressions, clicks, spend and an approximate unique reach per ad and campaign, within ten seconds.", P,
 "C: Three, bill: exact hourly totals, final at a cutoff, versioned, and exported to invoicing.", P,
 "C: Four, correct: late events and invalidations reach a closed hour as a new version and an adjustment line. A sent invoice is never edited. Each of these gets a sequence later."])

S(plain("Requirements · non-functional", "The numbers, and what each is for", '<p class="chips">all initial targets, not measurements</p><div class="tiles" style="--n:4">'
  '<div class="tile blue"><b>30 M/s</b><span>ingest at peak; ack p99 50 ms</span></div>'
  '<div class="tile blue"><b>10 s</b><span>live freshness, p99</span></div>'
  '<div class="tile"><b>H + 48 h</b><span>bill final; re-run bit for bit</span></div>'
  '<div class="tile red"><b>99.99 %</b><span>ingest: a dropped event is lost money</span></div></div>' +
  line("An acknowledged event survives the loss of a zone.", "a")), [
 "C: The numbers, and they are initial targets.", P,
 "C: Thirty million events a second at peak, acknowledged within fifty milliseconds at the ninety-ninth percentile.", P,
 "C: Live counts within ten seconds.", P,
 "C: The bill final forty-eight hours after the hour, and reproducible bit for bit.", P,
 "C: Four nines on ingest, because an event we drop is revenue we cannot bill.", P,
 "C: And an acknowledged event survives losing a whole zone."])

S(plain("Requirements · scope", "In, and out on purpose", cards(
  ("grn", "In scope", "Ingest, dedup, live counts, approximate reach, hourly billing totals, versions, corrections, an audit trail, reconciliation."),
  ("red", "Out, on purpose", "Fraud detection itself. Ad serving and auctions. Budget pacing. Invoicing and payment. Attribution.")) +
  line("Budget pacing is a consumer of the live counts: it is why they must be fast.", "")), [
 P, "C: In scope: ingest, dedup, live counts, approximate reach, the hourly billing totals with versions and corrections, an audit trail and reconciliation.", P,
 "C: Out, on purpose: fraud detection itself, ad serving and the auction, budget pacing, invoicing and payment, and conversion attribution.", P,
 "C: One of those I'd say aloud: budget pacing reads the live counts to stop a campaign that has spent its budget. That is why the live numbers must be fast, even though they are not the bill."])

S(dia("Architecture · C4 level 1 · context", "The system in its context, before any boxes inside it", "c4-context",
      cap="Figure 1.1 — C4 system context: who sends events, who reads them, and the two systems around the bill"), [
 "C: Before any boxes inside it, the system in its context.", P,
 "C: Ad clients: S-D-Ks in apps, browsers, and ad servers. They report every impression and click, in batches. Ninety-nine percent of the traffic.", P,
 "C: In the middle, the system, one box for now: live counts and exact hourly totals.", P,
 "C: Advertisers read dashboards and are billed.", P,
 "C: A fraud system flags invalid traffic, and it can do that late, after the bill.", P,
 "C: And invoicing turns our final hours into invoices. Nothing on the ingest path waits for any of them."], cls="dia")

key("The core", "The core is three things: an <em>idempotent, durable intake</em>; <em>one aggregation, run twice</em>; and <em>versioned final hours</em> with a correction path.", [
 "V: The core is three things. An idempotent, durable intake. One aggregation, run twice. And versioned final hours, with a correction path.", "[pause: 0.8]",
 "N: Notice the candidate fixed the scale, named the core and drew the context before any internals. That is the scoping signal."])

# ───────────────────────── 2 · estimates ─────────────────────────
chapter(2, "Estimates", 1, "Each number from the scale line, with what it decides", [
 "C: Numbers next. Each starts from the scale line, and each ends in a decision. They are illustrative, not anyone's real figures."])

S(plain("Estimates · traffic", "Ten million a second, thirty at the peak", table(["Number", "From", "Arithmetic", "Decides"], [
  ["Events", "monthly volume", "2.5 × 10¹³ ÷ 2.6 × 10⁶ s ≈ <b>10 M/s</b>; × 3 = <b>30 M/s</b>, 1.8 B a minute", "A partitioned log; no database write per event"],
  ["Clicks", "monthly volume", "2.5 × 10¹¹ ÷ 2.6 × 10⁶ s ≈ <b>100 k/s</b>; peak 300 k/s", "Same pipeline; the billable click is keyed by impression"],
  ["Bandwidth", "peak", "30 M × 200 B = <b>6 GB/s</b>; × 3 replicas = 18 GB/s", "1,024 partitions; about 80 brokers"]])), [
 "C: Traffic, from the monthly volumes.", P,
 "C: Twenty-five trillion impressions over two point six million seconds is about ten million a second. Three times that in the evening: thirty million a second, one point eight billion a minute. No database takes a write per event at that rate, so a partitioned log it is.", P,
 "C: Clicks are a hundredth of that: a hundred thousand a second, three hundred thousand at peak. They ride the same pipeline, and a billable click is keyed by the impression it came from, so a double-click bills once.", P,
 "C: At two hundred bytes an event, the peak is six gigabytes a second, eighteen with three replicas. About a thousand partitions and eighty brokers. Illustrative, but it sets the order of magnitude."])

S(plain("Estimates · storage and state", "Days in the log, months in the lake, minutes in memory", table(["Number", "From", "Arithmetic", "Decides"], [
  ["Log, 3 days", "average", "2 GB/s × 259,200 s ≈ 520 TB; ÷ 4 compressed × 3 ≈ <b>390 TB</b>", "Brokers keep 3 days; older replays read the lake"],
  ["Lake", "volume, retention", "2.5 × 10¹³ × 25 B ≈ <b>0.6 PB</b> a month; × 6 ≈ 3.8 PB", "Object storage, partitioned by event hour"],
  ["Dedup state", "peak", "30 M/s × 600 s = 1.8 × 10¹⁰ IDs × 40 B ≈ <b>0.7 TB</b>", "Keyed state over 512 subtasks, not one Redis set"]])), [
 "C: Where the bytes live.", P,
 "C: Three days of log at the two-gigabyte average is five hundred and twenty terabytes; compressed and replicated, about three hundred and ninety. So brokers keep three days, and a replay older than that reads the lake.", P,
 "C: The lake: twenty-five trillion events at about twenty-five bytes each, compressed in columns, is point six petabytes a month, three point eight for six months. Object storage, partitioned by the hour the event happened.", P,
 "C: And dedup. Ten minutes of event I-Ds at the peak is eighteen billion I-Ds, about point seven terabytes. Spread over five hundred and twelve stream tasks that is about one point four gigabytes each. In one Redis set, it would be eighteen billion keys."])

S(plain("Estimates · the hot ad and the money", "Two numbers that decide the hard parts", table(["Number", "From", "Arithmetic", "Decides"], [
  ["Hot ad", "the hot ad", "2 M/s on one key; one task does ~300 k updates/s", "Combine before the shuffle: 512 partial sums a second"],
  ["Duplicates", "monthly clicks", "0.3 % retried × 2.5 × 10¹¹ = 7.5 × 10⁸ clicks × $0.50 ≈ <b>$375 M</b> a month", "Dedup is the crux, not an optimisation"]])), [
 "C: Two numbers that decide the hard parts.", P,
 "C: The hot ad: two million impressions a second on one key, against roughly three hundred thousand updates a second for one stream task. Keyed by ad, one task drowns. So I combine before the shuffle, and challenge three is about that.", P,
 "C: And the money. If three tenths of a percent of click batches are retried, that's seven hundred and fifty million duplicate clicks a month. At fifty cents a click, about three hundred and seventy-five million dollars of overbilling. Illustrative, but it says dedup is the crux of this question, not an optimisation."])

S(dia("Estimates · the freshness budget", "Ten seconds, from an impression to the dashboard", "budget", chip=chips("initial target", "worst case")), [
 "C: The freshness budget, worst case. One second of batching in the S-D-K. Half a second through the collector and the log. Two seconds for the stream job's early results. A second to insert, a second to query. About five and a half seconds against ten.",
 "C: The spare is for a slow minute, not for a synchronous call. And it says why the stream job emits early results every two seconds rather than waiting for a minute to close."], cls="dia")
