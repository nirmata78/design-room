from dsl import *
import stack
P = "[+]"
ST = stack.load(pathlib.Path(__file__).resolve().parents[2])

# ───────────────────────── 5 · when you don't need all this ─────────────────────────
chapter(5, "When you don't need all this", 4, "The simpler design, and the number where it stops being enough", [
 "C: Before the recap: a much smaller design is correct at a smaller scale, and I should say where the line is."])

zoom("Alternate path", "One ClickHouse cluster: buffer, truth and dashboard", "alt", strip(("fixb", "How it works", "Collectors insert batches with a dedup token; a materialised view keeps minutes; a nightly query bills each hour from the deduplicated table."),
                  ("case", "What it gives up", "No independent log to replay; a heavy query slows ingest; corrections are mutations; dedup is eventual.")), [
 "C: The alternate path: no log, no lake, no stream job, no billing job.", P,
 "C: One ClickHouse cluster does everything, marked alternate.", P,
 "C: Collectors insert batches with an insert dedup token. A materialised view keeps minute rollups for the dashboard. And a nightly query bills each hour from the events table, deduplicated by event ID.", P,
 "C: What it gives up, precisely: there is no independent log to replay, because the table is the only copy. A heavy query slows ingest. A correction is a mutation. And dedup happens on merges, so it is eventual."], cap="The alternate: collectors insert straight into one ClickHouse cluster")

key("Alternate · the crossover", "One cluster ingests on the order of <em>1–2 million rows a second</em>. We average <em>10 million</em>. Below about <em>200,000 events a second</em>, I'd ship the one-cluster version, and say when I'd switch.", [
 "C: Where is the line? From chapter two, our average is ten million events a second. A cluster of about twenty ClickHouse nodes takes on the order of one to two million rows a second. We are past it by an order of magnitude.",
 "V: Below about two hundred thousand events a second, with room to spare, I'd ship the one-cluster version, and I'd say out loud the number where I'd switch.", "[pause: 0.8]"])

# ───────────────────────── 6 · recap ─────────────────────────
chapter(6, "Recap", 5, "The final design, the trade-offs, and what comes next", [
 "C: The recap. One picture with the mechanisms on it, the stack against its rivals, and the mistakes that cost most."])

stage("Recap · the final container view", "Where each mechanism ended up", "recap", [
 "C: Version three, the final design: the same picture as version one, with three boxes more. The collector keeps the ID the SDK minted; it never makes one up. The mechanisms go back on the rest, one at a time.", P,
 "C: The live aggregator runs dedup, event time and two-stage sums.", P,
 "C: The live store replaces by version. It never increments.", P,
 "C: The billing job runs the same code at the close, over a pinned snapshot, with the reconciler inside it.", P,
 "C: The billing tables hold versions, so a correction is a new row and an adjustment, never an edit.", P,
 "C: And the reporting API always says provisional or final."], vtag="V3", cap="The final design with its mechanisms")

S(plain("Recap · the trade-offs", "The stack, against its rivals", table(["Container", "Choice", "Rejected", "The deciding reason"], ST.summary(), "bt xs mx") +
  grade("Naming a product is not the signal. Naming the property that rules out its rival is.")), ST.summary_say() + [P,
 "N: Naming a product is not the signal. Naming the property that rules out its rival is. Interviewers go one level down on whichever box you name, so name only what you can defend."])

S(plain("Recap · the mistakes", "What costs most in this round", table(["Mistake", "Instead"], [
  ["<code>n = n + 1</code> per event, in a database", "a log first; counts derived from it"],
  ["“Exactly-once” said as a name", "at-least-once plus dedup on an ID minted at the source"],
  ["Counting by arrival time", "event time, clamped; a watermark; a cutoff"],
  ["One run for the dashboard and the bill", "one code, run twice: provisional, then final"],
  ["Editing billed rows", "versions and adjustment lines"],
  ["No way to show the events behind a line", "a manifest per hour; canaries; conservation checks"]], "bt sm")), [
 "N: The mistakes that cost most in this round.", P,
 "N: n equals n plus one, per event, in a database. Instead, a log first, and counts derived from it.", P,
 "N: Exactly-once said as a name. Instead, at-least-once plus dedup on an ID minted at the source.", P,
 "N: Counting by arrival time. Instead, event time, clamped, with a watermark and a cutoff.", P,
 "N: One run for both the dashboard and the bill. Instead, one code, run twice.", P,
 "N: Editing billed rows. Instead, versions and adjustment lines.", P,
 "N: And no way to show the events behind an invoice line. Instead, a manifest per hour, canaries and conservation checks."])

followups([
  ("Unique reach per campaign, live: how, and how wrong?", "HyperLogLog per campaign-minute, ~1.6 % error, merged on read; never on the bill"),
  ("A second region: where does each box go?", "one log per region, billing per region of the event; invoicing merges finals"),
  ("An advertiser wants hourly totals by country", "a dimension in the window key: state and rows × countries; check the 10 s budget"),
  ("Retention drops to 30 days for privacy", "the bill is reproducible from billing rows after that, not from events — say so"),
  ("Budget pacing needs 1-second numbers for one campaign", "a dedicated fast path for one headline number, not the whole pipeline")], [
 "C: The follow-up questions an interviewer asks next, and where I'd start.", P,
 "C: Unique reach: a HyperLogLog sketch per campaign-minute, about one and a half percent off, never on the bill.", P,
 "C: A second region: a log per region, billing by the event's region.", P,
 "C: Totals by country: a dimension in the window key; re-check the budget.", P,
 "C: Thirty-day retention: the bill is then reproducible from billing rows, not events.", P,
 "C: One-second pacing numbers: a fast path for one headline number, not the whole pipeline."])

key("The close", "Count once, from <em>one log</em>, with <em>one piece of code run twice</em>. Never increment what you can recompute: <em>replace</em> it, and keep every version you billed.", [
 "V: Count once, from one log, with one piece of code run twice. Never increment what you can recompute. Replace it, and keep every version you billed.", "[pause: 1.0]",
 "C: Thanks for watching. The written design, generated from this same script, is linked below."])
