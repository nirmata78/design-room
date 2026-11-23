from dsl import *
from stack import TECH, SUMMARY, DRILL
P = "[+]"

# ───────────────────────── 4 · API and entities ─────────────────────────
chapter(4, "API and entities", 3, "Each call tagged with the requirement it serves and the data it touches", [
 "C: Four public calls, one internal. Each tagged with the requirement it serves and the data it reads or writes."])

S(plain("API · the calls", "Four public calls, one internal", table(["Call", "Serves", "Touches", "Note"], [
  ["<code>POST /v1/links {url, alias?, expiresAt?}</code> + Idempotency-Key → <code>201 {code, shortUrl}</code>", "FR1", "writes Link", "409 alias taken · aliases ≥ 8 characters · 422 blocked URL · rate limit per key"],
  ["<code>GET /{code}</code> → <code>302</code> · <code>404</code> · <code>410</code>", "FR2", "reads Link, cache first", "410 Gone for a withdrawn code, so crawlers stop"],
  ["<code>GET /v1/links/{code}/stats?from&amp;to&amp;by=day,country</code>", "FR3", "reads DailyCount", "says how fresh: <code>asOf</code>"],
  ["<code>DELETE /v1/links/{code}</code> · <code>POST /v1/takedowns {code, reason}</code>", "FR4", "writes Link.status, Takedown", "invalidation event, audit row"],
  ["internal <code>LeaseRange()</code> → <code>{start, end}</code>", "FR1", "writes RangeLease", "1,000 IDs a lease"]])), [
 "C: The calls, one row at a time.", P,
 "C: Create is a post with the long U-R-L, an optional alias and expiry, and an idempotency key, so a bulk integrator's retry gets the same code back. It answers two-oh-one, or four-oh-nine if the alias is taken, or four-twenty-two if the U-R-L is known-bad. Aliases must be eight characters or more, so they never collide with a generated seven-character code. Each key has a rate limit: that's failure nine.", P,
 "C: The redirect is a get on the code: three-oh-two, four-oh-four, or four-ten Gone for a withdrawn code, so search crawlers stop asking.", P,
 "C: Stats return counts by day and country with an as-of time, so the owner knows how fresh they are.", P,
 "C: Delete and takedown write the status and emit an invalidation, with an audit row.", P,
 "C: And internally, lease range hands a create server a thousand I-Ds."])

S(plain("API · the redirect on the wire", "What the browser actually receives",
  '<pre class="wire"><span class="cm"># request</span>\nGET /aZ3kQ9x HTTP/1.1\nHost: sho.rt\n\n<span class="cm"># response</span>\nHTTP/1.1 302 Found\nLocation: https://example.com/spring-sale?utm=news\nCache-Control: private, max-age=0\nCDN-Cache-Control: max-age=60\nSurrogate-Key: c/aZ3kQ9x</pre>' +
  strip(("whyb", "Why these headers", "The browser must ask again every time (so we count and can recall). The edge may keep it for 60 s (so a viral link is cheap), tagged with a surrogate key so one purge call finds every copy. Both lifetimes are in the takedown budget."), cols="one")), [
 "C: The redirect on the wire. A get on the code. The answer is a three-oh-two Found with a Location header. The cache headers are the design decision: private, max age zero for the browser, so it asks us again every time, which means we count the click and can withdraw the link. And sixty seconds for the edge, so a viral link is cheap.", P,
 "C: The surrogate key tags every edge copy of this code, so one purge call finds them all. Both lifetimes are in the takedown budget. That is why the headers are on a slide."])

S(dia("Entities · conceptual", "Links, clicks, counts, takedowns, leases", "erd-chen"), [
 "C: The conceptual model. An owner creates links. A link has one code and one long U-R-L, a status and an optional expiry. Clicks are weak entities: they only exist as clicks of a link, and they roll up into daily counts. A takedown withdraws a link. And range leases record which server holds which block of I-Ds.",
 "C: One sentence on the bottom matters most: a code has exactly one live long U-R-L, but the same U-R-L may have many codes. So a hash of the U-R-L is not a key."])

S(plain("Entities · physical", "The keys follow the hot path", table(["Table", "Key", "Columns", "Note"], [
  ["<b>link</b>", "<code>code</code> PK, sharded by code", "long_url, owner_id, created_at, expires_at, status", "12 billion rows in ten years; the only hot key"],
  ["link_by_owner", "<code>(owner_id, created_at)</code>", "code", "the owner's dashboard; never on the hot path"],
  ["range_lease", "<code>/alloc/{region}/next</code>", "next ID, revision", "a consensus store; 0.4 leases a second"],
  ["daily_count", "<code>(code, day, country)</code>", "n", "written by the aggregator"],
  ["in each redirect server", "code", "url, status; 30–60 s lifetime; in-flight map", "single flight: one lookup per code per server"]]) +
  line("A hash of the URL is not a key: one URL may have many links. A click never updates the link row.", "a")), [
 "C: The physical model.", P,
 "C: The link table's primary key is the code, and it is sharded by code, because the code is the only key the redirect ever uses.", P,
 "C: The owner's dashboard gets its own table, keyed by owner and time, never on the hot path.", P,
 "C: The allocator holds one key per region: the next I-D, with its revision.", P,
 "C: Daily counts are written by the aggregator.", P,
 "C: And in each redirect server's memory: a map from code to U-R-L and status, a lifetime of thirty to sixty seconds, and an in-flight map for single flight.", P,
 "C: A hash of the U-R-L is not a key, and a click never updates the link row."])

S(plain("Entities · two rules", "What I would defend in review", cards(
  ("grn", "The code is the only hot key", "Shard by code. Every redirect is one key lookup. Owner queries go to a second table, written on create."),
  ("red", "No counter on the link row", "A click never writes to the link. A viral link would make that row the hottest lock in the system."))), [
 "C: Two rules I'd defend in a review.", P,
 "C: The code is the only hot key: shard by code, every redirect is one key lookup, and owner queries go to a second table written on create.", P,
 "C: And no counter on the link row: a click never writes to it, because a viral link would make that row the hottest lock in the system."])

# ───────────────────────── 5 · high-level design ─────────────────────────
chapter(5, "High-level design", 4, "Three versions, the container view, every flow as a sequence", [
 "C: The design in three versions, drawn on one baseline, each answering the objection to the one before. Then the container view, and every flow as a numbered picture and a sequence."])

S(dia("Design · V1", "The simplest thing that works", "base-v1", vtag="V1", chip=chips("one service", "one table", "random codes")), [
 "C: Version one, drawn from the left, the way a request travels.", P,
 "C: A browser, or an A-P-I client.", P,
 "C: One service that does everything: it creates, and it redirects.", P,
 "C: And one relational table from code to U-R-L. Create picks a random seven-character code and inserts it, retrying on a conflict. Redirect reads the table and answers three-oh-two.",
 "C: It works, and at a thousand clicks a second it would be fine. Here is the objection: four thousand reads a second on one table, with a forty-thousand peak on one row. Analytics would be an update per click. And nothing scales out, because creating and redirecting are one process with one failure mode."])

S(dia("Design · V2", "Split the paths; cache the read", "base-v2", vtag="V2", chip=chips("answers: different loads, different tolerances")), [
 P, "C: Version two answers that objection. The two paths have different loads and different tolerances, so they become two services. What stays from version one is now the redirect service, stateless, many copies, in front of a link store that is now sharded by code.", P,
 "C: New, in blue: a shared cache between them. Cache-aside: a miss reads the store and fills the cache.", P,
 "C: New on top: the create service, a separate deployment with its own scaling and its own failure mode. It inserts with a unique constraint.", P,
 "C: And the allocator it leases I-D ranges from.",
 "C: The objection it leaves: one viral code is one hot cache key. Clicks still have nowhere to go. And a takedown sits behind every cache."])

S(dia("Design · V3", "Protect the redirect; make every copy withdrawable", "base-v3", vtag="V3", chip=chips("edge", "click log", "takedown channel", "safety check")), [
 P, "C: Version three. Version two is carried as it is; I add seven boxes, in the order a request meets them.", P,
 "C: First, an edge in front of the redirect, which may keep a three-oh-two for sixty seconds. Each redirect server also gets an in-process cache with single flight, inside its box.", P,
 "C: On the create path, a safety check on the U-R-L before any code is issued.", P,
 "C: Below the redirect, the click path. After the answer, the redirect server sends a click event into a click log.", P,
 "C: An aggregator reads it in batches and counts per minute.", P,
 "C: And writes counts into a stats store, by day and country.", P,
 "C: Bottom left, the takedown service, which writes status blocked straight to the link store.", P,
 "C: And publishes on an invalidation channel that reaches the edge, every redirect server and the shared cache.",
 "C: The objection it leaves is the details. Those are the challenges."])

S(dia("Architecture · C4 level 2 · containers", "Eight containers, each a separate deployment", "c4-containers",
      cap="Figure 5.1 — C4 container view: the deployable units, their responsibilities, and how they talk"), [
 "C: Now the same design in C-four, level two: containers. A container here means a separately deployed and separately scaled thing, a service or a data store. This is the picture the rest of the video hangs on, so I'll take it slowly, in the order a click travels.", P,
 "C: The visitor, outside the boundary, opens a short link over H-T-T-P-S. The request does not come to us first.", P,
 "C: It reaches the edge, a content delivery network that we buy. The edge may answer a hot code itself for up to sixty seconds. On a miss, it forwards the request. The edge is ours to configure and to purge, but not ours to run.", P,
 "C: Next, the redirect service: stateless, many copies in every region, each with a small in-process cache and single flight. It owns the twenty-millisecond objective. Everything it needs to answer is in memory, one network hop away at most.", P,
 "C: Behind it, the shared cache: an in-memory, sharded cache, read cache-aside. It holds the hot set, about a hundred gigabytes, so that a cold redirect server does not mean a cold store.", P,
 "C: Then the link store: the truth. A sharded store keyed by code, with a unique constraint on the code. On the redirect path it sees only misses, about forty reads a second.", P,
 "C: Above, the create service. It is not on the redirect path at all. It leases I-D ranges, permutes I-Ds into codes, and inserts under the constraint, writing straight to the link store.", P,
 "C: The range allocator: a small consensus-backed store. Point four leases a second. It is the only place where create servers coordinate, and they do it once per thousand links.", P,
 "C: To the right, outside the boundary, the U-R-L classifier we call on create. Bought, or another team's service.", P,
 "C: Below the redirect service, the click pipeline: a log and an aggregator. Note the arrow: click events go asynchronously, after the answer.", P,
 "C: And the takedown service, which writes status to the store and drives the invalidation of every copy.",
 "C: Read it as a layout: the redirect path is four boxes in a row, left to right. Create is above it, counting and takedown are below it. Nothing crosses the row. That layout is the thesis, drawn."], cls="dia")

S(plain("Design · the three versions", "Each answers the one before", table(["Version", "Adds", "Answers", "Leaves"], [
  ["V1", "One service, one table, random codes", "—", "one hot row; a write per click; nothing scales out"],
  ["V2", "Split paths; shared cache; sharded store; ranges", "different loads, different tolerances", "one hot cache key; no click path; takedown behind caches"],
  ["V3", "Edge; in-process cache; click log; takedown channel; safety check", "nothing in front of the redirect; every copy withdrawable", "the details: challenges 1 to 8"]])), [
 "C: The three versions in one table.", P, "C: Version one: one service, one table.", P, "C: Version two: split the paths, cache the read, lease ranges.", P,
 "C: Version three: protect the redirect and make every copy withdrawable. Each answers the objection to the one before."])

S(dia("Flow · FR1 create", "Four numbered steps", "flow-fr1"), [
 P, "C: Flow one, create, on the baseline, with numbered arrows.", P,
 "C: One: the client posts the long U-R-L with an idempotency key.", P,
 "C: Two: the create service asks the safety check whether the U-R-L is known-bad.", P,
 "C: Three: it takes the next I-D from its leased range, leasing a new one at half-used.", P,
 "C: Four: it permutes the I-D, encodes it in base sixty-two, and inserts it with the unique constraint on the code. For a custom alias, the alias is the code, and the constraint decides who gets it. Then two-oh-one with the short U-R-L."], cls="dia")

S(dia("Sequence · create", "Check, number, permute, insert", "seq-create"), [
 "C: The same flow as a sequence, message by message.", P,
 "C: Post with an idempotency key.", P, "C: Is this U-R-L known-bad?", P, "C: No.", P,
 "C: Locally, no network: next I-D from the range, keyed permutation, base sixty-two: a-Z-three-k-Q-nine-x.", P,
 "C: Insert with the unique constraint.", P, "C: Okay.", P,
 "C: Two-oh-one with the short link. One write on the store, no lock across servers."], cls="dia")

S(dia("Flow · FR2 redirect", "Eight numbered steps, almost all in memory", "flow-fr2"), [
 P, "C: Flow two, the redirect, the product.", P,
 "C: One: the browser asks the edge for the code.", P,
 "C: Two: on an edge miss, the request reaches a redirect server, which checks its in-process cache.", P,
 "C: Three: on a miss, the shared cache.", P,
 "C: Four: on a miss there too, the link store.", P,
 "C: Five: the store's answer fills the shared cache.", P,
 "C: Six: the U-R-L comes back to the redirect server, which checks the status and the expiry.", P,
 "C: Seven: the three-oh-two goes back to the edge.", P,
 "C: Eight: the edge returns it, and may keep it for sixty seconds. For a hot code, steps three to six never happen: the answer is in memory."], cls="dia")

S(dia("Sequence · redirect", "The click is recorded after the answer", "seq-redirect"), [
 "C: As a sequence.", P, "C: Get the code.", P, "C: In-process miss.", P, "C: Shared cache, about a millisecond.", P, "C: Miss.", P,
 "C: Select from the link store by primary key.", P, "C: Live. Fill both caches.", P, "C: Three-oh-two with the Location.", P,
 "C: And only then, the click event to the log, fire and forget. Nothing after the answer can delay the answer."], cls="dia")

S(dia("Flow · FR3 count", "Five numbered steps, none on the redirect's clock", "flow-fr3"), [
 P, "C: Flow three, counting.", P, "C: One: the click arrives at the edge.", P, "C: Two: the edge forwards it, as before.", P,
 "C: Three: after answering, the redirect server appends a click event to a local buffer, which flushes a batch every second into the click log, partitioned by code.", P,
 "C: Four: the aggregator reads batches and counts per code per minute, then per day per country.", P,
 "C: Five: the counts land in the stats store. If the buffer is full, events are dropped and the drops are counted."], cls="dia")

S(dia("Sequence · count", "From the 302 to the owner's dashboard", "seq-count"), [
 "C: Counting as a sequence, end to end.", P, "C: The three-oh-two is already sent.", P,
 "C: The server appends the code, the country and the minute to a local buffer.", P,
 "C: The buffer pre-aggregates: per code and country, each second. A viral link becomes forty small counters a second, one per server, not forty thousand events.", P,
 "C: Once a second, a batch goes to the click log, keyed by code.", P,
 "C: The stream job consumes it.", P,
 "C: It counts in one-minute windows of event time, and accepts data up to thirty seconds late.", P,
 "C: It inserts counts by code, minute and country into the stats store.", P,
 "C: The owner's dashboard asks for this code's counts by day.", P,
 "C: And gets them with an as-of time: fourteen-oh-five. Fresh within minutes, and it says so."], cls="dia")

S(dia("Flow · FR4 withdraw", "Five numbered steps to every copy", "flow-fr4"), [
 P, "C: Flow four, withdrawal.", P, "C: One: the takedown service writes status blocked in the link store.", P,
 "C: Two: it publishes on the invalidation channel.", P,
 "C: Three: the shared cache deletes the key; the takedown also deletes it directly and retries until confirmed.", P,
 "C: Four: every redirect server drops the code from its in-process cache.", P,
 "C: Five: the edge is purged. The next request reads blocked from the store and answers four-ten Gone, with a warning page."], cls="dia")

S(dia("Sequence · takedown", "Status first, then every copy", "seq-takedown"), [
 "C: As a sequence.", P, "C: Trust and safety posts the takedown with a reason.", P, "C: The status is set and audited.", P,
 "C: The shared cache key is deleted directly, retried until confirmed.", P, "C: The invalidation is published.", P,
 "C: It reaches every server and the edge.", P,
 "C: If that event is lost, the in-process and edge lifetimes are sixty seconds each, so the worst case is about two minutes.", P,
 "C: The next request reads blocked: four-ten."], cls="dia")

# ───────────────────────── 5.1 · components and technologies ─────────────────────────
subchapter("5.1", "Components and technologies", ["C: Now one level down. Every container, with the technology I would run it on, the components inside the two services, and for each choice, the alternatives I rejected and why."])

S(dia("Architecture · C4 containers · technologies", "The same containers, now with what they run on", "c4-containers-tech",
      cap="Figure 5.2 — the container view with technologies; every choice has a rejected alternative on a later slide"), [
 "C: The container view again, with one change: the type line now names the technology. I'll walk it once quickly, then defend each choice on its own slide.", P,
 "C: The visitor.", P, "C: The edge is a bought C-D-N with purge by surrogate key.", P,
 "C: The redirect service is Go on Kubernetes, with an in-process cache and single flight.", P,
 "C: The shared cache is Redis Cluster, with a replica per shard.", P,
 "C: The link store is PostgreSQL, sharded by code, with a primary per shard in the region that creates its links.", P,
 "C: The create service is Go as well.", P,
 "C: The range allocator is etcd: three nodes, Raft, one compare-and-set transaction per lease.", P,
 "C: The classifier is a bought web-risk A-P-I.", P,
 "C: The click pipeline is Kafka into a Flink job into ClickHouse.", P,
 "C: And the takedown service is a small Go service that publishes to a Kafka topic. Six technologies in total, and three of them we would buy managed."], cls="dia")

S(dia("Architecture · C4 level 3 · redirect service", "Inside the redirect service", "c4-comp-redirect",
      cap="Figure 5.3 — components of the redirect service; every miss path has its own timeout"), [
 "C: C-four level three, components, for the container that matters most. Inside the redirect service, in the order a request meets them.", P,
 "C: The edge forwards a miss.", P,
 "C: The H-T-T-P handler parses the code, rejects anything that is not seven to thirty characters of the alphabet before it touches a cache, and writes the three-oh-two, four-oh-four or four-ten with the cache headers.", P,
 "C: The resolver owns single flight: one in-flight lookup per code per process, everyone else waits on it. In Go that is the singleflight package.", P,
 "C: It asks the in-process cache first. That's ristretto: a bounded cache with TinyLFU admission, so a scan of random codes cannot evict the hot set. Three hundred thousand codes, sixty seconds, about a hundred megabytes.", P,
 "C: On a miss, the cache client: a cluster-aware Redis client that keeps the slot map and has a two-millisecond timeout.", P,
 "C: It talks to Redis Cluster.", P,
 "C: On a second miss, the store client: a connection pool that maps the code to its shard, with a twenty-millisecond timeout.", P,
 "C: And PostgreSQL, read by primary key.", P,
 "C: After the answer, the handler hands the click to the click emitter: an in-memory ring buffer that pre-aggregates and flushes every second.", P,
 "C: Into the Kafka click topic, asynchronously.", P,
 "C: And on the left: an invalidation listener reads the invalidation topic with its own consumer group, and drops codes from the in-process cache. On restart it rewinds five minutes, so it cannot miss a recent takedown."], cls="dia")

S(dia("Architecture · C4 level 3 · create service", "Inside the create service", "c4-comp-create",
      cap="Figure 5.4 — components of the create service; nothing here is on the redirect path"), [
 "C: And the create service, components.", P,
 "C: An integrator posts a batch of links.", P,
 "C: The A-P-I handler looks up the idempotency key first: a repeat returns the stored response. It answers two-oh-one, four-oh-nine or four-twenty-two.", P,
 "C: The rate limiter takes a token from a bucket per A-P-I key, kept in Redis.", P,
 "C: The safety client asks the web-risk A-P-I, with a hundred-and-fifty-millisecond timeout and a circuit breaker. If the classifier is down: anonymous creates are refused with a retry, trusted keys are accepted and rescanned later.", P,
 "C: The encoder runs the Feistel permutation and base sixty-two. Its round key comes from a key-management service at start-up.", P,
 "C: It takes the next I-D from the range holder, an etcd client that leases a thousand I-Ds and leases the next block at half-used.", P,
 "C: And the store writer inserts on conflict do nothing. No row back means the code was taken: four-oh-nine for an alias. The idempotency row is written in the same transaction, so a crash can never leave a link without its idempotency record."], cls="dia")

S(tech(**TECH("link-store")), [
 P, "C: The link store. I'd run PostgreSQL, sharded by code: sixteen shards per region to start. Each region is the primary for the links it creates, its slice of the I-D space, and holds asynchronous replicas of the other regions. Each primary has a synchronous standby in another zone. The insert is on conflict do nothing: no row back means the code was taken. A custom alias has no I-D, so its home region is fixed by a hash of the alias, and both creates of the same alias land on one primary.", P,
 "C: Why: the primary key is the unique constraint I need. Six terabytes is boring for it, and we know exactly how it fails.", P,
 "C: Rejected: Cassandra or Scylla. Good at reads, but uniqueness needs a lightweight transaction, a Paxos round per insert, and its multi-region serial modes are easy to get wrong. Its strength, leaderless writes everywhere, buys nothing at four hundred writes a second.", P,
 "C: DynamoDB: a conditional put is exactly the constraint, in one region. But global tables resolve concurrent writes by last writer wins, so an alias created in two regions at once could succeed twice.", P,
 "C: And one big PostgreSQL: the writes fit, but eighteen terabytes on one primary is one failure domain, and vacuum on a twelve-billion-row table is its own project."])

S(tech(**TECH("allocator")), [
 P, "C: The range allocator: etcd, three nodes per region, one in each zone. A lease is one transaction: if the next key's revision is still what I read, put next plus a thousand. It commits when a majority of the Raft group has it. There is no expiring lock, so no clock assumption and no fencing token. A crashed server just leaves a gap.", P,
 "C: Why etcd: a linearizable compare-and-set by revision, it survives losing one node, and the load is point four leases a second. And it's often already running under Kubernetes.", P,
 "C: Rejected: ZooKeeper. The same guarantee, a conditional write on a version, replicated by its own atomic broadcast protocol. An honest equal. I'd reject it only because it is a Java ensemble we would run for this alone.", P,
 "C: Redis increment-by: fast, but replication is asynchronous. After a fail-over the new primary may not have seen the last increment, and it hands out the same range twice. That breaks S-one silently, which is the worst way to break it.", P,
 "C: A Cassandra counter cannot compare-and-set and is not idempotent; a lightweight transaction would work but ties create to the busiest data store.", P,
 "C: And a PostgreSQL sequence that increments by a thousand is durable and simple, a defensible choice. I'd reject it because create would then depend on one shard's fail-over."])

S(tech(**TECH("shared-cache")), [
 P, "C: The shared cache: Redis Cluster, six primaries and six replicas per region, bought managed. Sixteen thousand three hundred and eighty-four hash slots over six shards, about seventeen gigabytes of the hot set each. A miss sets the key with an hour's lifetime and jitter; a takedown deletes the key directly. Least-frequently-used eviction.", P,
 "C: Why: a replica per shard, so losing a shard is a promotion, not a cold slice of the key space.", P,
 "C: Rejected: Memcached, an honest equal, simpler and multi-threaded. But a node's loss is a cold slice with no replica, which is exactly the stampede of challenge three.", P,
 "C: Hazelcast: an in-memory data grid with a near cache. Its near cache duplicates the in-process cache we already have, its clients are Java-first, and its split-brain merge policies solve a problem a cache-aside copy does not have.", P,
 "C: And no shared cache at all, just store replicas: it works at four thousand a second, until a region's redirect servers restart together and every miss lands on the store."])

S(tech(**TECH("local-cache")), [
 P, "C: Inside each redirect server: ristretto and singleflight in Go, or Caffeine in Java, which does both. Three hundred thousand entries, about a hundred megabytes per server, sixty seconds, and ten seconds for a not-found.", P,
 "C: Why: TinyLFU admission. A new key gets in only if it is more frequent than the one it would evict, so a storm of random codes cannot push out the hot set. And singleflight turns concurrent misses into one lookup.", P,
 "C: Rejected: a plain least-recently-used map, which admits everything, so a scan evicts exactly the hot set.", P,
 "C: A sidecar cache per host: one more hop and one more process, for a job a library does.", P,
 "C: And no local cache: every viral click becomes a network call to one Redis shard. That's challenge three."])

S(tech(**TECH("click-log")), [
 P, "C: The click log: Kafka, three brokers per region, replication factor three. Topic clicks, thirty-two partitions keyed by code, a week's retention. Today the producer waits for one acknowledgement and pre-aggregates per code and country each second; when clicks are billed it waits for all replicas, is idempotent, and every click carries an I-D.", P,
 "C: Why: a replayable log. A bug in counting is fixed by replaying a week, which is the feature that matters here. And pre-aggregation means a viral code is forty small messages a second, not a hot partition.", P,
 "C: Rejected: RabbitMQ. It's a queue: once acknowledged, a message is gone, so there is nothing to replay.", P,
 "C: Kinesis or Pub-Sub: honest equals if we are on that cloud. Buy, not build.", P,
 "C: And writing straight into the stats store: no buffer against a spike, and the redirect's health would depend on the analytics database."])

S(tech(**TECH("counting")), [
 P, "C: Counting: a Flink job into ClickHouse. The job is keyed by code, counts in one-minute windows of event time, and allows thirty seconds of lateness. When billed, it removes duplicates by event I-D, kept for a day. ClickHouse stores counts ordered by code, day and country, and sums rows with the same key in the background.", P,
 "C: Why: event-time windows with a stated lateness, exactly-once state through checkpoints, and a column store that answers by code and day in milliseconds.", P,
 "C: Rejected: Spark Structured Streaming is an honest equal; its micro-batches add seconds, which is fine.", P,
 "C: A nightly batch job: the requirement says minutes.", P,
 "C: Cassandra counters: a retried increment counts twice. Wrong for anything that may be billed.", P,
 "C: And a PostgreSQL table is fine on day one, but counts by code, day and country grow into billions of rows, which a column store compresses far better."])

S(tech(**TECH("invalidation")), [
 P, "C: Invalidation: a Kafka topic for the servers and a surrogate-key purge for the edge. Each redirect server reads the topic with its own consumer group, and rewinds five minutes when it starts. The takedown service calls the C-D-N's purge A-P-I with the surrogate key, and retries; the sixty-second edge lifetime is the backstop.", P,
 "C: Why: we already run Kafka, and a reconnecting server replays what it missed instead of silently missing it.", P,
 "C: Rejected: Redis Pub-Sub. It is at most once: a server disconnected for one second misses the message and never knows. It would only be acceptable because the lifetime backstops it, and Kafka's replay costs nothing extra.", P,
 "C: Polling the store: forty servers asking every second adds load, and a slow store makes takedowns slower exactly when it hurts.", P,
 "C: And purge by U-R-L works, but every variant must be listed. One surrogate key names them all."])

S(tech(**TECH("services")), [
 P, "C: Services and the edge: Go on Kubernetes across three zones per region, behind a bought C-D-N. Redirect pods scale on requests per second, and a pod warms its cache from the last hour's top codes before it reports ready. Rollouts go one zone at a time. The C-D-N caches only links over a click-rate threshold, chosen by a response header.", P,
 "C: Why: small binaries and short, predictable pauses for a twenty-millisecond p ninety-nine. And points of presence are not our business.", P,
 "C: Rejected: Java with Caffeine is an honest equal. If the team is a J-V-M team, pick it and tune the collector.", P,
 "C: Serverless functions for the redirect: cold starts break the target, and per-invocation pricing at ten billion a month is the most expensive way to run a loop.", P,
 "C: And building our own edge: hundreds of points of presence, for a product whose core is a map lookup."])

S(plain("Technology · the stack on one slide", "Each choice, against the alternative an interviewer will name", table(["Container", "Choice", "Rejected", "The deciding reason"], SUMMARY(), "bt xs mx") +
  grade("Naming a product is not the signal. Naming the property that rules out its rival is.")), [
 "C: The stack on one slide, as I'd leave it on the whiteboard.", P, "C: Link store: PostgreSQL, because the primary key is the authority.", P,
 "C: Allocator: etcd, because asynchronous replication could reissue a range.", P, "C: Shared cache: Redis Cluster, a replica per shard.", P,
 "C: Local cache: TinyLFU admission.", P, "C: Click log: Kafka, for replay.", P, "C: Counting: Flink into ClickHouse.", P,
 "C: Invalidation: a replayable topic and a surrogate-key purge.", P,
 "N: Naming a product is not the signal. Naming the property that rules out its rival is. Interviewers go one level down on whichever box you name, so name only what you can defend."])

# ── the drill interlude: the viewer plays the interviewer (2026-11-21) ──
qs("Coach · your turn", "You are the interviewer. Which box would you drill, and what is your one question?", [
 "N: Before the challenges, swap seats. You are the interviewer now. Of everything on the last slide, which box would you push on, and what is the one question you would ask? Pause the video and pick one.", "[pause: 3.0]"])

S(plain("Drill · one level down", "The question each box invites, and what a strong answer names", table(["Box", "The probe", "A strong answer names"], DRILL(), "bt xs mx") +
  grade("The probe lands on the box you named. The score is set where your answer runs out, so the stack you name is the stack you must defend.")), [
 "N: Here is where interviewers usually go.", P,
 "I: Link store. Two regions accept the same alias in the same second. Which write wins?", "[pause: 1.2]",
 "N: Neither region decides alone. The alias has a home region, fixed by its hash, so both creates reach one primary and the key rejects the second. The trap is saying last writer wins.", P,
 "I: Allocator. The etcd leader dies mid-lease. Can two servers hold the same thousand I-Ds?", "[pause: 1.2]",
 "N: No. A lease commits only on a majority, the new leader has every committed entry, and an unfinished one is retried against the new revision. The worst case is a gap.", P,
 "I: Shared cache. A Redis primary fails over. What does a redirect see in the next two seconds?", "[pause: 1.2]",
 "N: Timeouts at two milliseconds, then the store, already shielded by the in-process cache and single flight. The client refreshes its slot map, and a takedown's delete is retried until it is confirmed.", P,
 "I: Click log. Counting had a bug for three days. How do you fix the numbers?", "[pause: 1.2]",
 "N: Reset the counting job's consumer group three days back, recount into a new table, and switch the reads. That is why it is a log and why it keeps a week.", P,
 "I: Invalidation. One redirect server was cut off for ten minutes during a takedown. Is it still serving the link?", "[pause: 1.2]",
 "N: For at most sixty seconds after the event it missed. Ten minutes is past the five-minute rewind, so here the lifetime, not the topic, is what keeps the promise.", P,
 "N: If you picked a box that is not on this list, good. Write its probe down and answer it before you watch on."])
