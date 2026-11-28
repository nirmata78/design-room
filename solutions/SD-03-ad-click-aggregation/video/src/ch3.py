from dsl import *
P = "[+]"

# ───────────────────────── 3 · API contracts and the data model ─────────────────────────
chapter(3, "API and data model", 2, "What crosses the wire, and what is stored", [
 "C: The API next, then the data. Every endpoint is tagged with the requirement it serves."])

S(plain("API · record events (FR1)", "One write endpoint: a batch, IDs minted at the source",
  chips("serves FR1", "202 only after the log has it") +
  code('POST /v1/events\n{"events": [{\n  "event_id": "0190f3c2-7d1e-7a4b-…",\n  "type": "click",\n  "impression_id": "0190f3c1-0b9a-…",\n  "ad_id": 77,\n  "client_ts": "2026-11-22T14:05:07Z"\n}, …]}\n\n202 Accepted  {"accepted": 500}', "json", hl=(3, 5, 10))), [
 "C: One write endpoint, and it serves FR1. A batch of up to five hundred events.",
 "C: Three fields matter. The event ID is a UUIDv7, minted by the SDK at the moment the event happens, not when it is sent, so a retry carries the same ID. A click names the impression it came from, so a double-click is two click events but one billable click. And the client time is kept as the client said it; the pipeline decides later how much to trust it.",
 "C: The answer is 202, and only after the log has acknowledged the batch. The ID makes retries harmless, and the impression ID makes clicks billable once."])

S(plain("API · reads and corrections", "Three more endpoints, each tagged", table(["Endpoint", "Serves", "Touches", "What the response says"], [
  ["<code>GET /v1/campaigns/{id}/live?step=1m</code>", "FR2", "live minutes", "<code>asOf</code>, <code>provisional: true</code>"],
  ["<code>GET /v1/billing/hours?advertiser=&amp;month=</code>", "FR3", "billing hours", "<code>version</code>, <code>manifest_id</code>, <code>final: true</code>"],
  ["<code>POST /v1/invalidations</code> (fraud)", "FR4", "invalidations", "event IDs with their hours, a reason, the rule version"]], "bt xs mx")), [
 "C: Three more endpoints.", P,
 "C: The live read, for FR2. Every response carries an as-of time and the word provisional. The dashboard says what it is.", P,
 "C: The billing read, for FR3: each hour with its version and the ID of the manifest that produced it. That ID is how we answer a dispute.", P,
 "C: And corrections, for FR4: the fraud system posts invalidated event IDs with their hours, a reason and the version of the rule that flagged them. Append only."])

S(dia("Data · physical model", "Where each entity lives, and its key", "erd-physical", cap="The physical model: six tables, keyed by what they count"), [
 "C: The physical tables, one at a time.", P,
 "C: Events, in an Iceberg table on object storage, partitioned by event hour. Point six petabytes a month.", P,
 "C: Billing hour: the primary key is campaign, ad, hour and version. A correction adds a row; none is updated. It points to a manifest.", P,
 "C: The manifest records what one billing run read: the events snapshot, the rate-card version, the invalidation snapshot, and the job's image digest.", P,
 "C: Live minute, in ClickHouse: keyed by campaign, ad, minute and a shard number, with a version column. A newer version replaces an older one.", P,
 "C: Invalidations, append only.", P,
 "C: And adjustments: per campaign, hour and version, the difference that invoicing applies. Notice that no table is ever incremented. Every number is keyed by what it counts."])

S(dia("Data · the life of one billing hour", "An hour is opened, closed, and only ever re-versioned", "state-hour",
      cap="The lifecycle of one billing hour: open, final, dirty, final again"), [
 "C: And the lifecycle of one billing hour, because it is the thing we bill.", P,
 "C: It starts open: live counts only, marked provisional.", "[+2]",
 "C: At forty-eight hours a snapshot is pinned and it becomes final, version one. That is what gets invoiced.", "[+2]",
 "C: If fraud flags events in it, it becomes dirty.", "[+2]",
 "C: And a re-run makes it final again, as the next version, with an adjustment sent.", P,
 "C: It can loop: another invalidation, another version. It never goes back to open, and it is never edited. Challenge five lives on this diagram."])
