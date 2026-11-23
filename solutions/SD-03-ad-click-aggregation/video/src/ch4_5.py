from dsl import *
from stack import TECH, SAY, SUMMARY, SUMMARY_SAY
P = "[+]"

# ───────────────────────── 4 · API and entities ─────────────────────────
chapter(4, "API and entities", 3, "What crosses the wire, and what is stored", [
 "C: The A-P-I next, then the data. Every endpoint is tagged with the requirement it serves."])

S(plain("API · record events (FR1)", "One write endpoint: a batch, IDs minted at the source",
  chips("serves FR1", "writes EVENT", "202 only after the log has it") +
  code('POST /v1/events\n{"events": [{\n  "event_id": "0190f3c2-7d1e-7a4b-9c2e-…",\n  "type": "click",\n  "impression_id": "0190f3c1-0b9a-7f10-…",\n  "ad_id": 77,\n  "client_ts": "2026-11-22T14:05:07.312Z"\n}, …]}\n\n202 Accepted  {"accepted": 500}', "json", hl=(2, 4, 10))), [
 "C: One write endpoint, and it serves F-R-one. A batch of up to five hundred events.",
 "C: Three fields matter. The event I-D is a U-U-I-D version seven, minted by the S-D-K at the moment the event happens, not when it is sent, so a retry carries the same I-D. A click names the impression it came from, so a double-click is two click events but one billable click. And the client time is kept as the client said it; we decide later how much to trust it.",
 "C: The answer is two-oh-two, and only after the log has acknowledged the batch. The I-D makes retries harmless, and the impression I-D makes clicks billable once."])

S(plain("API · reads and corrections", "Three more endpoints, each tagged", table(["Endpoint", "Serves", "Touches", "What the response says"], [
  ["<code>GET /v1/campaigns/{id}/live?step=1m</code>", "FR2", "live minutes", "<code>asOf</code>, <code>provisional: true</code>"],
  ["<code>GET /v1/billing/hours?advertiser=&amp;month=</code>", "FR3", "HOUR TOTAL", "<code>version</code>, <code>manifest_id</code>, <code>final: true</code>"],
  ["<code>POST /v1/invalidations</code> (fraud)", "FR4", "INVALIDATION", "event IDs with their hours, a reason, the rule version"]], "bt xs mx")), [
 "C: Three more endpoints.", P,
 "C: The live read, for F-R-two. Every response carries an as-of time and the word provisional. The dashboard says what it is.", P,
 "C: The billing read, for F-R-three: each hour with its version and the I-D of the manifest that produced it. That I-D is how we answer a dispute.", P,
 "C: And corrections, for F-R-four: the fraud system posts invalidated event I-Ds with their hours, a reason and the version of the rule that flagged them. Append only."])

S(dia("Data · conceptual model", "Six entities; an hour total is a weak entity with a version", "erd-chen"), [
 "C: The conceptual model, entity by entity.", P,
 "C: An advertiser.", P, "C: An advertiser runs many campaigns.", P, "C: A campaign has many ads.", P,
 "C: An ad receives many events, each with its event I-D, its event time and, for a click, the impression it came from.", P,
 "C: Events are counted in an hour total. The hour total is a weak entity: it exists only for a campaign, and its key includes the hour and a version, because a correction creates a new version rather than changing the old one.", P,
 "C: And an invalidation voids an event, with a reason.", P,
 "C: An hour is never edited. That one rule removes a whole class of disputes."], cls="dia")

S(dia("Data · physical model", "Where each entity lives, and its key", "erd-physical"), [
 "C: The physical tables, one at a time.", P,
 "C: Events, in an Iceberg table on object storage, partitioned by event hour. Point six petabytes a month.", P,
 "C: Billing hour: the primary key is campaign, ad, hour and version. A correction adds a row; none is updated. It points to a manifest.", P,
 "C: The manifest records what one billing run read: the events snapshot, the rate-card version, the invalidation snapshot, and the job's image digest.", P,
 "C: Live minute, in ClickHouse: keyed by campaign, ad, minute and a shard number, with a version column. A newer version replaces an older one.", P,
 "C: Invalidations, append only.", P, "C: And adjustments: per campaign, hour and version, the difference that invoicing applies."], cls="dia")

# ───────────────────────── 5 · high-level design ─────────────────────────
chapter(5, "High-level design", 4, "Three versions on one picture, then every path", [
 "C: The design in three versions. Each answers the objection to the one before, and it is one picture from here to the end: later slides only show what changes on it."])

S(dia("Design · version 1", "The simplest thing that is exact: a log, a lake, an hourly job", "base-v1", vtag="V1"), [
 "C: Version one is the simplest thing that is exact, and I'll draw it in the order an event travels.", P,
 "C: Ad clients send batches of events.", P, "C: A collector validates them, stamps the server time, and appends them.", P,
 "C: To a partitioned, replicated event log. This is the one copy everything else is derived from.", P,
 "C: Every five minutes the log is landed as files in an event lake, partitioned by the hour the event happened.", P,
 "C: A billing job reads one closed hour, removes duplicates and counts.", P,
 "C: And writes billing tables.", P, "C: A reporting A-P-I serves them.", P,
 "C: To the advertiser. It is exact and replayable. The objection: the dashboard is an hour or a day behind, and budget pacing can't run on that."], cls="dia")

S(dia("Design · version 2", "Freshness: a live aggregator and a live store", "base-v2", vtag="V2"), [
 "C: Version two answers that.", P, "C: Everything from version one stays where it was.", P,
 "C: New, a live aggregator: a stream job on the same log, with the same aggregation code. It counts by the minute and emits early results.", P,
 "C: New, a live store, which holds the live minutes, and also gets the final hours loaded from the billing job. So the A-P-I now reads one store for both. The objection: a bill has to be final, yet late events and fraud corrections keep arriving after the hour."], cls="dia")

S(dia("Design · version 3", "Corrections: invalidations in, final hours out, versions in between", "base-v3", vtag="V3"), [
 "C: Version three answers that.", P, "C: Version two, carried as it was.", P,
 "C: New, the fraud system. Its invalidations arrive on an append-only topic, and the billing job re-runs the affected hours as new versions.", P,
 "C: New, invoicing, which receives final hours and, when a version changes after an invoice, an adjustment line. This is the baseline. From here it only changes by deltas."], cls="dia")

S(plain("Design · the containers", "Each container, what it owns, and its number", table(["Container", "Owns", "Its number"], [
  ["Collector", "Validation, the server time, the append; never an ID, never dedup", "30 M events/s, stateless"],
  ["Event log", "The one copy, keyed by event ID, three days", "1,024 partitions, 390 TB"],
  ["Live aggregator", "Dedup for 10 minutes, partial sums, minute windows, reach", "0.7 TB of keyed state"],
  ["Live store", "Live minutes, and final hours loaded from the bill", "~100,000 rows/s"],
  ["Event lake", "Every event, six months, by event hour", "0.6 PB a month"],
  ["Billing job + tables", "The exact hour, as versions, with a manifest", "H + 48 h; 7 years"],
  ["Reporting API", "Dashboards and exports; says provisional or final", "query p99 1 s"]], "bt xs mx")), [
 "C: The containers, one line each, in the order an event meets them.", P,
 "C: The collector: validation, the server time and the append. No I-Ds, no dedup, so it stays stateless at thirty million a second. Go on Kubernetes, with a disk spool if the log is unreachable.", P,
 "C: The event log: the one copy, keyed by event I-D, for three days.", P,
 "C: The live aggregator: dedup for ten minutes, partial sums, minute windows and reach.", P,
 "C: The live store: live minutes, and a copy of the final hours.", P,
 "C: The event lake: every event for six months, by event hour.", P,
 "C: The billing job and its tables: the exact hour, as versions, each with a manifest.", P,
 "C: And the reporting A-P-I, which always says provisional or final. On the ingest path: the collector and the log. Nothing else."])

S(dia("Flow · FR1 and FR2", "An impression, from the phone to the dashboard", "flow-live"), [
 P, "C: The live path, numbered.", P,
 "C: One: the S-D-K posts a batch to the collector.", P, "C: Two: the collector appends it with all replicas acknowledging, then answers two-oh-two.", P,
 "C: Three: the live aggregator consumes it.", P, "C: Four: it writes minute rows, early every two seconds, final when the watermark passes.", P,
 "C: Five: the advertiser opens a dashboard.", P, "C: Six: the A-P-I queries the live store. About five seconds end to end."], cls="dia")

S(dia("Flow · FR3 and FR4", "An hour, from the log to the invoice", "flow-bill"), [
 P, "C: The billing path, numbered.", P,
 "C: One: the log lands files in the lake every five minutes, in the partition of each event's hour.", P,
 "C: Two: at forty-eight hours, the billing job reads that hour at a snapshot.", P,
 "C: Three: it replaces the hour in the billing tables as the next version.", P,
 "C: Four: it loads the final hour into the live store, so the dashboard switches from provisional to final.", P,
 "C: Five: invoicing receives the final hour."], cls="dia")

S(dia("Sequence · FR1 record", "A batch, durable before the yes", "seq-ingest"), [
 "C: Record, as a sequence.", P, "C: The S-D-K posts five hundred events, each with its I-D minted at creation.", P,
 "C: The collector validates, stamps the server time, and clamps a client time that is too far off.", P,
 "C: It produces to Kafka keyed by event I-D, with acks equals all.", P, "C: Two of three replicas have it.", P,
 "C: Only now: two-oh-two.", P, "C: If that answer is lost, the S-D-K retries the same batch with the same I-Ds. That's challenge one."], cls="dia")

S(dia("Sequence · FR2 live", "From the log to a provisional number", "seq-live"), [
 "C: Live, as a sequence.", P, "C: Flink consumes events, partitioned by event I-D.", P,
 "C: It drops any I-D it has seen in ten minutes, and sums per ad per second.", P,
 "C: Each ad-and-minute window emits an early result every two seconds.", P,
 "C: As rows with a version into ClickHouse.", P, "C: The advertiser asks for campaign forty-two, by minute.", P,
 "C: The A-P-I takes the latest version of each row and sums the shards.", P, "C: Sixty rows back.", P,
 "C: As of fourteen oh five and seven seconds, marked provisional."], cls="dia")

S(dia("Sequence · FR3 bill", "Closing an hour, pinned", "seq-bill"), [
 "C: The bill, as a sequence.", P, "C: The hour starting at fourteen hundred closes forty-eight hours later.", P,
 "C: The closer asks the lake for a snapshot of that hour as of the cutoff.", P, "C: Snapshot seven million three hundred and forty-two thousand.", P,
 "C: It starts the run with a manifest: that snapshot, rate card eighteen, invalidation list nine-oh-three, and the job's image.", P,
 "C: The job removes every duplicate, drops invalid events, prices in integer micro-dollars and sums.", P,
 "C: It replaces the hour as version one, with its manifest.", P, "C: And the final hour goes to invoicing."], cls="dia")

S(dia("Sequence · FR4 correct", "A correction, without editing an invoice", "seq-correct"), [
 "C: Correct, as a sequence.", P, "C: The fraud system invalidates three point one million clicks from botnet seventeen, with their hours.", P,
 "C: The hours are marked dirty.", P, "C: The closer re-runs each one with a new manifest.", P,
 "C: Version two of each hour is written. Version one stays.", P, "C: The difference to what was invoiced: minus one point five five million dollars.", P,
 "C: It goes on the next invoice as adjustment lines. Challenge five drills into this."], cls="dia")

# ───────────────────────── 5.1 · components and technologies ─────────────────────────
subchapter("5.1", "Components and technologies", ["C: Now one level down. The same picture with what each box runs on, the two containers that matter most opened up, and for each choice, what I rejected and why."])

S(dia("Architecture · C4 containers · technologies", "The same containers, now with what they run on", "c4-containers-tech"), [
 P, "C: The same container view; only the type lines changed. The seven boxes in scope, one at a time.", P,
 "C: The collector: Go on Kubernetes, acks equals all, with a disk spool.", P, "C: The event log: Kafka, a thousand and twenty-four partitions, keyed by event I-D.", P,
 "C: The live aggregator: Flink, streaming.", P, "C: The live store: ClickHouse, replacing rows by version.", P,
 "C: The event lake: Iceberg tables on Google Cloud Storage, Parquet by event hour.", P,
 "C: The billing job: Flink again, in batch mode. The same code, at the close.", P,
 "C: And the billing tables: Iceberg, versioned, hour by campaign by version."], cls="dia")

S(dia("Architecture · C4 components · live aggregator", "Inside the live aggregator, in the order an event meets it", "c4-comp-stream"), [
 "C: Inside the live aggregator, in the order an event meets it.", P,
 "C: The event log feeds it.", P, "C: A Kafka source: one per partition range, its offsets saved in the checkpoint.", P,
 "C: The time assigner: it clamps a skewed client time, and emits the watermark.", P,
 "C: The deduplicator: state keyed by event I-D, ten-minute lifetime, in Rocks-D-B.", P,
 "C: The combiner: partial sums per task, flushed every second.", P,
 "C: The window counter: ad by minute, by event time.", P, "C: Reach sketches hang off it.", P,
 "C: And a late output, which counts events past the allowed lateness instead of adding them.", P,
 "C: The store sink writes rows with a version.", P, "C: Into ClickHouse.", P,
 "C: And checkpoints: state and offsets together, every thirty seconds. Challenges one to four all happen in this picture."], cls="dia")

S(dia("Architecture · C4 components · billing job", "Inside the billing job: the same counting, plus what makes it final", "c4-comp-billing"), [
 "C: Inside the billing job.", P,
 "C: It reads the event lake.", P, "C: The hour closer decides when: at forty-eight hours, or when an hour is marked dirty. It pins a manifest.", P,
 "C: The reader reads that hour at the pinned snapshot.", P, "C: Exact dedup: the first row per I-D, over the whole hour.", P,
 "C: Invalidations arrive on an append-only topic, and the invalid filter is an anti-join against a pinned snapshot of them.", P,
 "C: Rate cards are versioned. Price and sum, in integer micro-dollars, so the sum is the same in any order.", P,
 "C: The writer commits the hour as the next version.", P, "C: Into the billing tables.", P,
 "C: The adjuster takes the new version minus what was invoiced.", P, "C: And sends it to invoicing."], cls="dia")

from stack import STACK, say_text
def tsay(_id):
    """Compact cut: the slide carries the reasons; the narration reads how, why, and the first clause of each rejection."""
    s = STACK[_id]; first = lambda t: re.split(r"(?<=[.:;])\s", say_text(t))[0].rstrip(".:;") + "."
    out = [P, "C: " + say_text(s["how"]), P, "C: Why: " + first(s["why"])]
    for i, (n, w) in enumerate(s["rejected"]):
        out += [P, f"C: {'Rejected: ' if i == 0 else ''}{say_text(n)}. " + first(w)]
    return out
import re
for _id in ("log", "stream", "live", "lake"):
    S(tech(**TECH(_id)), tsay(_id))

_ss = SUMMARY_SAY()
S(plain("Technology · the stack on one slide", "The stack, against its rivals",
        table(["Container", "Choice", "Rejected", "The deciding reason"], SUMMARY(), "bt xs mx") +
        grade("Naming a product is not the signal. Naming the property that rules out its rival is.")), _ss[:-1] + [P, _ss[-1]])

# ───────────────────────── 5.2 · when you don't need all this ─────────────────────────
subchapter("5.2", "When you don't need all this", ["C: Before I break it: a much smaller design is correct at a smaller scale, and I should say where the line is."], sub="ALTERNATE")

S(dia("Alternate path · ALTERNATE", "One ClickHouse cluster: buffer, truth and dashboard", "alt",
      extra=strip(("fixb", "How it works", "Collectors insert batches with a dedup token; a materialised view keeps minutes; a nightly query bills from the deduplicated table."),
                  ("case", "What it gives up", "No independent log to replay; a heavy query slows ingest; corrections are mutations; dedup is eventual."))), [
 P, "C: The alternate path. The ingest boxes stay.", P,
 "C: What goes away is marked. The event lake.", P, "C: The separate billing job.", P, "C: And the billing tables as their own store.", P,
 "C: Instead, one ClickHouse cluster. Collectors insert batches with an insert dedup token. A materialised view keeps minute rollups for the dashboard. And a nightly query bills each hour from the events table, deduplicated by event I-D.", P,
 "C: What it gives up, precisely: there is no independent log to replay, because the table is the only copy. A heavy query slows ingest. A correction is a mutation. And dedup happens on merges, so it is eventual."], cls="dia")

key("ALTERNATE · the line", "One cluster ingests on the order of <em>1–2 million rows a second</em>. We average <em>10 million</em>. Below about <em>200,000 events a second</em>, I'd ship the one-box version, and say when I'd switch.", [
 "C: Where is the line? A cluster of about twenty ClickHouse nodes takes on the order of one to two million rows a second. Our average, from the scale line, is ten million. We are past it by an order of magnitude.",
 "V: Below about two hundred thousand events a second, with room to spare, I'd ship the one-box version, and I'd say out loud when I'd switch.", "[pause: 0.8]"])
