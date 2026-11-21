from dsl import *

# ───────────────────────── 4 · API and entities ─────────────────────────
chapter(4, "API and entities", 3, "Each call tagged with the requirement it serves and the data it touches", [
 "C: Four public calls, one internal. Each tagged with the requirement it serves and the data it reads or writes."])

S(plain("API · the calls", "Four public calls, one internal", table(["Call", "Serves", "Touches", "Note"], [
  ["<code>POST /v1/links {url, alias?, expiresAt?}</code> + Idempotency-Key → <code>201 {code, shortUrl}</code>", "FR1", "writes Link", "409 alias taken · aliases ≥ 8 characters · 422 blocked URL · rate limit per key"],
  ["<code>GET /{code}</code> → <code>302</code> · <code>404</code> · <code>410</code>", "FR2", "reads Link, cache first", "410 Gone for a withdrawn code, so crawlers stop"],
  ["<code>GET /v1/links/{code}/stats?from&amp;to&amp;by=day,country</code>", "FR3", "reads DailyCount", "says how fresh: <code>asOf</code>"],
  ["<code>DELETE /v1/links/{code}</code> · <code>POST /v1/takedowns {code, reason}</code>", "FR4", "writes Link.status, Takedown", "invalidation event, audit row"],
  ["internal <code>LeaseRange()</code> → <code>{start, end}</code>", "FR1", "writes RangeLease", "1,000 IDs a lease"]], "bt sm")), [
 "C: Create is a post with the long U-R-L, an optional alias and expiry, and an idempotency key, so a bulk integrator's retry gets the same code back. It answers two-oh-one, or four-oh-nine if the alias is taken, or four-twenty-two if the U-R-L is known-bad. Aliases must be eight characters or more, so they never collide with a generated seven-character code. Each key has a rate limit: that's failure nine.",
 "C: The redirect is a get on the code: three-oh-two, four-oh-four, or four-ten Gone for a withdrawn code, so search crawlers stop asking. Stats return counts by day and country with an as-of time, so the owner knows how fresh they are. Delete and takedown write the status and emit an invalidation. And internally, lease range hands a create server a thousand I-Ds."])

S(plain("API · the redirect on the wire", "What the browser actually receives",
  '<pre class="wire"><span class="cm"># request</span>\nGET /aZ3kQ9x HTTP/1.1\nHost: sho.rt\n\n<span class="cm"># response</span>\nHTTP/1.1 302 Found\nLocation: https://example.com/spring-sale?utm=news\nCache-Control: private, max-age=0\nCDN-Cache-Control: max-age=60</pre>' +
  strip(("whyb", "Why these headers", "The browser must ask again every time (so we count and can recall). The edge may keep it for 60 s (so a viral link is cheap). Both lifetimes are in the takedown budget."), cols="one")), [
 "C: The redirect on the wire. A get on the code. The answer is a three-oh-two Found with a Location header. The cache headers are the design decision: private, max age zero for the browser, so it asks us again every time, which means we count the click and can withdraw the link. And sixty seconds for the edge, so a viral link is cheap.",
 "C: Both lifetimes are in the takedown budget. That is why the headers are on a slide."])

S(dia("Entities · conceptual", "Links, clicks, counts, takedowns, leases", "erd-chen"), [
 "C: The conceptual model. An owner creates links. A link has one code and one long U-R-L, a status and an optional expiry. Clicks are weak entities: they only exist as clicks of a link, and they roll up into daily counts. A takedown withdraws a link. And range leases record which server holds which block of I-Ds.",
 "C: One sentence on the bottom matters most: a code has exactly one live long U-R-L, but the same U-R-L may have many codes. So a hash of the U-R-L is not a key."])

S(plain("Entities · physical", "The keys follow the hot path", table(["Table", "Key", "Columns", "Note"], [
  ["<b>link</b>", "<code>code</code> PK, sharded by code", "long_url, owner_id, created_at, expires_at, status", "12 billion rows in ten years; the only hot key"],
  ["link_by_owner", "<code>(owner_id, created_at)</code>", "code", "the owner's dashboard; never on the hot path"],
  ["range_lease", "<code>server_id</code>", "start, end, leased_at", "a consensus store; 0.4 leases a second"],
  ["daily_count", "<code>(code, day, country)</code>", "n", "written by the aggregator"],
  ["in each redirect server", "code", "url, status; 30–60 s lifetime; in-flight map", "single flight: one lookup per code per server"]], "bt sm") +
  line("A hash of the URL is not a key: one URL may have many links. A click never updates the link row.", "a")), [
 "C: The physical model. The link table's primary key is the code, and it is sharded by code, because the code is the only key the redirect ever uses. The owner's dashboard gets its own table, keyed by owner and time, never on the hot path. Range leases live in a small consensus store. Daily counts are written by the aggregator.",
 "C: And in each redirect server's memory: a map from code to U-R-L and status, a lifetime of thirty to sixty seconds, and an in-flight map for single flight. A hash of the U-R-L is not a key, and a click never updates the link row."])

S(plain("Entities · two rules", "What I would defend in review", '<div class="cards c2">'
  '<div class="cd grn"><h3>The code is the only hot key</h3><p>Shard by code. Every redirect is one key lookup. Owner queries go to a second table, written on create.</p></div>'
  '<div class="cd red"><h3>No counter on the link row</h3><p>A click never writes to the link. A viral link would make that row the hottest lock in the system.</p></div></div>'), [
 "C: Two rules I'd defend in a review. The code is the only hot key: shard by code, every redirect is one key lookup, and owner queries go to a second table written on create. And no counter on the link row: a click never writes to it, because a viral link would make that row the hottest lock in the system."])

# ───────────────────────── 5 · high-level design ─────────────────────────
chapter(5, "High-level design", 4, "Three versions, each answering the objection to the one before", [
 "C: The design in three versions. Each is drawn on the same baseline, and each answers the objection to the one before."])

S(dia("Design · V1", "The simplest thing that works", "base-v1", vtag="V1", chip=chips("one service", "one table", "random codes")), [
 "C: Version one. One service, one relational table from code to U-R-L. Create picks a random seven-character code and inserts it, retrying on a conflict. Redirect reads the table and answers three-oh-two.",
 "C: It works, and at a thousand clicks a second it would be fine. Here is the objection: four thousand reads a second on one table, with a forty-thousand peak on one row. Analytics would be an update per click. And nothing scales out, because creating and redirecting are one process with one failure mode."])

S(dia("Design · V2", "Split the paths; cache the read", "base-v2", vtag="V2", chip=chips("answers: different loads, different tolerances")), [
 "C: Version two answers that objection. The two paths have different loads and different tolerances, so they become two services. The redirect service is stateless, many copies, with a shared cache in front of a sharded link store: cache-aside, so a miss reads the store and fills the cache.",
 "C: The create service leases I-D ranges from the allocator and inserts with a unique constraint. The new boxes are outlined in blue.",
 "C: The objection it leaves: one viral code is one hot cache key. Clicks still have nowhere to go. And a takedown sits behind every cache."])

S(dia("Design · V3", "Protect the redirect; make every copy withdrawable", "base-v3", vtag="V3", chip=chips("edge", "click log", "takedown channel", "safety check")), [
 "C: Version three protects the redirect. An edge in front caches three-oh-twos for sixty seconds. Each redirect server has an in-process cache with single flight. Clicks go after the answer into a click log, an aggregator and a stats store along the bottom.",
 "C: The takedown service writes the status and publishes on an invalidation channel that reaches the edge, every redirect server, and the shared cache. And create calls a safety check on the U-R-L before issuing a code.",
 "C: The objection it leaves is the details. Those are the challenges."])

S(plain("Design · the three versions", "Each answers the one before", table(["Version", "Adds", "Answers", "Leaves"], [
  ["V1", "One service, one table, random codes", "—", "one hot row; a write per click; nothing scales out"],
  ["V2", "Split paths; shared cache; sharded store; ranges", "different loads, different tolerances", "one hot cache key; no click path; takedown behind caches"],
  ["V3", "Edge; in-process cache; click log; takedown channel; safety check", "nothing in front of the redirect; every copy withdrawable", "the details: challenges 1 to 8"]], "bt sm")), [
 "C: The three versions in one table. Version one: one service, one table. Version two: split the paths, cache the read, lease ranges. Version three: protect the redirect and make every copy withdrawable. Each answers the objection to the one before."])

S(dia("Flow · FR1 create", "Four numbered steps", "flow-fr1"), [
 "C: Flow one, create, with numbered arrows. One: the client posts the long U-R-L with an idempotency key. Two: the create service asks the safety check whether the U-R-L is known-bad. Three: it takes the next I-D from its leased range, leasing a new one at half-used.",
 "C: Four: it permutes the I-D, encodes it in base sixty-two, and inserts it with the unique constraint on the code. For a custom alias, the alias is the code, and the constraint decides who gets it. Then two-oh-one with the short U-R-L."], cls="dia")

S(dia("Sequence · create", "Check, number, permute, insert", "seq-create"), [
 "C: The same flow as a sequence. Post with an idempotency key. Known-bad? No. Next I-D from the range, keyed permutation, base sixty-two: a-Z-three-k-Q-nine-x. Insert with the unique constraint. Okay. Two-oh-one with the short link. One write on the store, no lock across servers."], cls="dia")

S(dia("Flow · FR2 redirect", "Eight numbered steps, almost all in memory", "flow-fr2"), [
 "C: Flow two, the redirect. One: the browser asks the edge for the code. Two: on an edge miss, the request reaches a redirect server, which checks its in-process cache. Three: on a miss, the shared cache. Four: on a miss there too, the link store.",
 "C: Five and six: the store fills the shared cache and the U-R-L comes back. The server checks the status and the expiry. Seven and eight: the three-oh-two goes back through the edge, which may keep it for sixty seconds. For a hot code, steps three to six never happen: the answer is in memory."], cls="dia")

S(dia("Sequence · redirect", "The click is recorded after the answer", "seq-redirect"), [
 "C: As a sequence. Get the code. In-process miss. Shared cache, about a millisecond: miss. Select from the link store: live. Fill both caches. Three-oh-two with the Location. And only then, the click event to the log, fire and forget. Nothing after the answer can delay the answer."], cls="dia")

S(dia("Flow · FR3 count", "Five numbered steps, none on the redirect's clock", "flow-fr3"), [
 "C: Flow three, counting. One and two: the click arrives through the edge as before. Three: after answering, the redirect server appends a click event to a local buffer, which flushes a batch every second or every thousand events into the click log, partitioned by code.",
 "C: Four: the aggregator reads batches and counts per code per minute, then per day per country. Five: the counts land in the stats store, and the owner's dashboard reads them with an as-of time. If the buffer is full, events are dropped and the drops are counted."], cls="dia")

S(dia("Flow · FR4 withdraw", "Five numbered steps to every copy", "flow-fr4"), [
 "C: Flow four, withdrawal. One: the takedown service writes status blocked in the link store. Two: it publishes on the invalidation channel. Three: the shared cache deletes the key; the takedown also deletes it directly and retries until confirmed. Four: every redirect server drops the code from its in-process cache.",
 "C: Five: the edge is purged. The next request for that code reads blocked from the store and answers four-ten Gone, with a warning page. And every step is audited."], cls="dia")

S(dia("Sequence · takedown", "Status first, then every copy", "seq-takedown"), [
 "C: As a sequence. Trust and safety posts the takedown with a reason. The status is set and audited. The shared cache key is deleted, retried until confirmed. The invalidation goes out to every server and the edge. If that event is lost, the in-process and edge lifetimes are sixty seconds each, so the worst case is about two minutes. The next request reads blocked: four-ten."], cls="dia")

S(dia("Architecture · C4 context", "Who uses the system, and what it depends on", "c4-context"), [
 "C: The C-four context view. Visitors follow short links. Link owners create links and read stats. Trust and safety blocks bad links. And the system calls one external dependency on create: a U-R-L classifier that says whether a U-R-L is known-bad. Nothing external sits on the redirect path."], cls="dia")

S(dia("Architecture · C4 containers", "Eight containers inside the boundary", "c4-containers"), [
 "C: The container view. The edge, which we buy. The redirect service, stateless, with its in-process cache. The shared cache. The link store, a sharded key-value store with a unique code. The create service and the range allocator, a small consensus store. The click pipeline: a log and an aggregator. And the takedown service.",
 "C: The redirect path is four boxes in a row, left to right. Everything else is above it or below it. That layout is the thesis, drawn."], cls="dia")

S(plain("Design · technology, against the alternatives", "Mechanism first, then a product class", table(["Need", "Choice", "Rejected", "Because"], [
  ["Link store", "sharded key-value or relational, keyed by code", "one relational primary", "fine for writes; reads and storage outgrow it, and it is one failure domain"],
  ["Shared cache", "in-memory cache, cache-aside", "read-through in the store", "the cache must survive the store being slow"],
  ["Allocator", "small consensus-backed store", "a counter row in the link store", "couples create to the busiest store; no lease semantics"],
  ["Click path", "local buffer → partitioned log → aggregator", "a counter per link", "a hot row per viral link"],
  ["Edge", "bought CDN with a purge API", "build our own", "points of presence are not our business"]], "bt sm mx")), [
 "C: Technology, mechanism first. The link store is a sharded key-value or relational store keyed by code, not one primary: writes would fit, but reads and storage outgrow it, and it would be one failure domain. The shared cache is cache-aside, so it survives the store being slow.",
 "C: The allocator is a small consensus-backed store, not a counter row in the link store, which would couple create to the busiest store. Clicks go to a buffer, a log and an aggregator, not a counter per link. And the edge is bought, with a purge A-P-I. Points of presence are not our business."])
