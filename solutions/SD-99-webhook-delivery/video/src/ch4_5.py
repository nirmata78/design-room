from dsl import *

# ───────────────────────── 4 · API and entities ─────────────────────────
chapter(4, "API and entities", 3, "The contract first. It forces the semantics into the open.", [
 "C: The A-P-I next, then the data. Each endpoint is tagged with the requirement it serves and the entity it touches."])

S(plain("API · register", "An endpoint is verified before it gets a single event  <span class=vtag>FR1</span>",
  '<pre class="code" data-lang="http">POST /v1/webhook-endpoints\n{ <span class="st">"url"</span>: <span class="st">"https://pos.example/hooks"</span>,\n  <span class="st">"events"</span>: [<span class="st">"loan.approved"</span>, <span class="st">"loan.refunded"</span>],\n  <span class="st">"api_version"</span>: <span class="st">"2026-06-01"</span> }\n→ 201 { <span class="st">"id"</span>: <span class="st">"ep_42"</span>,\n        <span class="st">"secret"</span>: <span class="st">"whsec_…"</span> }   <span class="cm"># shown once</span></pre>' +
  strip(("whyb", "Writes Endpoint, Subscription", "A verification ping must be answered before the endpoint is active. The version is pinned at creation."), cols="one")), [
 "C: Register. A U-R-L, the event types, and an A-P-I version, which is pinned at creation. The answer carries the endpoint I-D and the signing secret, shown once.",
 "C: Before the endpoint is active, we send a verification ping it must answer. F-R-one; it writes the endpoint and its subscriptions."])

S(plain("API · the delivery itself", "What crosses the wire to the merchant  <span class=vtag>FR3</span>",
  '<pre class="code" data-lang="http">POST https://pos.example/hooks\nWebhook-Id: ev_8841\nWebhook-Timestamp: 1795075200\nWebhook-Signature: v1=5f2c…\n{ <span class="st">"id"</span>: <span class="st">"ev_8841"</span>, <span class="st">"type"</span>: <span class="st">"loan.refunded"</span>,\n  <span class="st">"loan_id"</span>: <span class="st">"ln_5531"</span>, <span class="st">"sequence"</span>: 7,\n  <span class="st">"api_version"</span>: <span class="st">"2026-06-01"</span>,\n  <span class="st">"data"</span>: { <span class="st">"refund_cents"</span>: 30000 } }\n→ 2xx: done · 410: unsubscribe · else: retry</pre>' +
  strip(("whyb", "Reads Delivery, Event", "The ID de-duplicates, the sequence orders, the timestamp and signature prove it is us and recent."), cols="one")), [
 "C: The delivery itself, the most important contract in the system. Three headers: the event I-D, a timestamp, and a signature over both and the body. The body carries the type, the loan, a sequence number for that loan, the pinned version, and the data.",
 "C: The answer codes are part of the contract too: any two hundred means done, four ten means stop sending, and anything else, including a timeout, means we retry. F-R-three."])

S(plain("API · logs and replay", "The merchant can see and fix it without calling support  <span class=vtag>FR4</span>",
  '<pre class="code" data-lang="http">GET /v1/deliveries?endpoint=ep_42&amp;status=dead\n→ 200 { <span class="st">"data"</span>: [ … attempts … ], <span class="st">"next"</span>: … }\n\nPOST /v1/deliveries/dl_77/redeliver\nPOST /v1/webhook-endpoints/ep_42/replay\n{ <span class="st">"since"</span>: <span class="st">"2026-12-02T09:00Z"</span>, <span class="st">"rate"</span>: 20 }\n→ 202 { <span class="st">"replay_id"</span>: <span class="st">"rp_3"</span> }</pre>' +
  strip(("whyb", "Reads Attempt; writes Delivery", "Replay is a write to the same rows the dispatcher claims, at a rate the merchant chooses."), cols="one")), [
 "C: Logs and replay. The merchant lists deliveries by endpoint and state, with every attempt. They can redeliver one, or replay everything since a time, at a rate they choose.",
 "C: Replay is just a write to the same rows the dispatcher already claims, so it needs no second delivery path. F-R-four."])

S(dia("Data · conceptual model", "Merchants, endpoints, events, deliveries, attempts", "erd-chen"), [
 "C: The conceptual model.", "C: A merchant", "C: owns endpoints.", "C: An endpoint", "C: listens to subscriptions, one per event type.",
 "C: An event", "C: fans out to deliveries:", "C: one delivery is one event to one endpoint,", "C: going to that endpoint,",
 "C: and tried by attempts.", "C: The delivery, not the event, is the unit of state."], cls="dia")

S(dia("Data · physical model", "Tables, keys, and the timer as a column", "erd-physical"), [
 "C: The physical model. The endpoint: U-R-L, pinned version, tier and cap, and its state. The secret lives in the key service, not here. The event payload, stored once per event, with the loan and its sequence. Subscriptions, cached in fan-out.",
 "C: The delivery: sharded by endpoint, unique on endpoint and event, with its state, attempt number, next attempt time and lease. The attempt table, partitioned by day. And the note: the timer is a column, with a partial index on the next attempt time for pending rows."], cls="dia")

# ───────────────────────── 5 · high-level design ─────────────────────────
chapter(5, "High-level design", 4, "Three versions, each answering the objection to the one before", [
 "C: Now the design, in three versions, each introduced by the objection to the one before. The boxes never move: every later picture is a view of the same baseline."])

S(dia("High-level design · version 1 of 3", "The simplest thing that works", "base-v1", vtag="V1",
      chip=chips("a POST inside the request", "no queue", "no retry")), [
 "C: Version one. The producer, say origination, books the loan, and in the same request it POSTs to every subscribed merchant U-R-L. It is the simplest thing that works, and for a handful of merchants on a good day, it does."], cls="dia")

S(trace("V1 · the objection", "A thirty-second till, a crash, and a rollback", [
  ("14:31:07.200", "ln_5531 booked; the request POSTs loan.booked to the merchant's till"),
  ("14:31:37.200", "<span class='bad'>the till answers after 30 s: the booking request has held a worker for 30 s</span>"),
  ("14:32:00.000", "a retry inside the request; the process is restarted by a deploy"),
  ("14:32:00.050", "<span class='bad'>the loan exists; the event is gone</span>"),
  ("14:40:00.000", "<span class='bad'>another booking POSTs first, then its transaction rolls back: the merchant hears of a loan that does not exist</span>")]), [
 "C: The objection as a trace.",
 "[+]", "C: The loan is booked, and the request POSTs to the merchant's till.",
 "[+]", "C: The till answers after thirty seconds. The booking request held a worker for all of it.",
 "[+]", "C: A retry inside the request, and a deploy restarts the process.",
 "[+]", "C: The loan exists, and the event is gone.",
 "[+]", "C: And another booking POSTs first and then rolls back: the merchant hears of a loan that doesn't exist."])

S(dia("High-level design · version 2 of 3", "No event without its commit", "base-v2", vtag="V2",
      chip=chips("outbox rows", "a relay", "a log", "dispatcher workers")), [
 "[+]", "C: Version two answers that. The producer writes an outbox row in the same transaction as the loan.",
 "[+]", "C: An outbox relay publishes the rows to the event log, keyed by loan,",
 "[+]", "C: and the log keeps them for seven days.",
 "[+]", "C: Dispatcher workers consume the log and POST to the merchants, retrying in process on failure. The booking request no longer waits for anyone."], cls="dia")

S(plain("V2 · the objection", "Correct at the source, and one slow till takes everyone down", cards(
  ("red", "One shared pool", "120 calls a second to one slow till at 10 s holds 1,200 workers; the fleet has 600."),
  ("red", "Retries in memory", "A restart forgets every pending retry; a two-day outage cannot live in a process."),
  ("red", "Head of line", "Events for healthy merchants queue behind the slow one in the same partition."),
  ("red", "Nobody can see", "No record of what was sent, so “you never sent it” cannot be answered."))), [
 "C: The objection to version two. It is correct at the source, but one slow till takes everyone down. A hundred and twenty calls a second at ten seconds each hold twelve hundred workers, and we have six hundred. Retries live in memory, so a restart forgets them, and a two-day outage cannot live in a process.",
 "C: Events for healthy merchants queue behind the slow one in the same partition. And there is no record of what was sent, so when a merchant says we never sent it, we can't answer."])

S(dia("High-level design · version 3 of 3", "A queue per endpoint, as rows", "base-v3", vtag="V3",
      chip=chips("fan-out", "delivery store", "claim under a cap", "attempt log", "API")), [
 "[+]", "C: Version three keeps everything from version two.", "[+]", "C: Fan-out consumes the log and matches each event to its subscriptions.",
 "[+]", "C: It writes one row per delivery into the delivery store, keyed by endpoint. That row is the queue, and its next-attempt column is the timer.",
 "C: The dispatcher now claims rows, only for endpoints below their in-flight cap, under a lease.",
 "[+]", "C: Every attempt goes to the attempt log,",
 "[+]", "C: and the webhooks A-P-I reads that log and replays by writing rows.",
 "C: This is the baseline. Every picture from here is a view of it."], cls="dia")

S(plain("V3 · the claim, as code", "Only endpoints under their cap; the lease is the lock",
  '<pre class="code" data-lang="sql"><span class="kw">WITH</span> due <span class="kw">AS</span> (\n  <span class="kw">SELECT</span> d.id <span class="kw">FROM</span> delivery d <span class="kw">JOIN</span> endpoint e\n    <span class="kw">ON</span> e.id = d.endpoint_id\n   <span class="kw">WHERE</span> d.state = <span class="st">\'PENDING\'</span>\n     <span class="kw">AND</span> d.next_attempt_at &lt;= now()\n     <span class="kw">AND</span> e.in_flight &lt; e.cap\n   <span class="kw">LIMIT</span> 200 <span class="kw">FOR UPDATE OF</span> d <span class="kw">SKIP LOCKED</span>)\n<span class="kw">UPDATE</span> delivery <span class="kw">SET</span> state = <span class="st">\'IN_FLIGHT\'</span>,\n       lease_until = now() + <span class="st">\'30 s\'</span>\n  <span class="kw">FROM</span> due <span class="kw">WHERE</span> delivery.id = due.id\n<span class="kw">RETURNING</span> delivery.id;</pre>'), [
 "C: The claim, in S-Q-L. Pending rows whose next attempt time has passed, only for endpoints whose in-flight count is under their cap, two hundred at a time, with skip locked so two dispatchers never take the same row. They move to in-flight with a thirty-second lease.",
 "C: The lease is the lock. If a dispatcher dies, the lease expires and another one claims the row. That resend is safe because the event I-D travels with it."])

def flow(n, fr, title, svg, tags, say):
    S(dia(f"High-level design · requirement {n} · {fr}", title, svg, trs=tr(*tags)), say, cls="dia")

flow(2, "emit", "FR2: an event leaves only with its commit", "flow-fr2",
     [("fr", "serves FR2"), ("api", "outbox → log"), ("ent", "writes Event"), ("nfr", "zero loss after commit")], [
 "[+]", "C: Requirement two, emit, by the numbers.", "[+]", "C: One: the producer commits the loan and the outbox row together.",
 "[+]", "C: Two: the relay publishes the row to the log, keyed by loan.", "[+]", "C: Three: fan-out consumes it.",
 "[+]", "C: Four: fan-out writes one delivery row per matching endpoint. The event now exists durably, three times over: the outbox, the log, and the rows."])
flow(3, "deliver", "FR3: one delivery, end to end", "flow-fr3",
     [("fr", "serves FR3"), ("api", "signed POST"), ("ent", "writes Delivery · Attempt"), ("nfr", "p99 first attempt < 5 s")], [
 "[+]", "C: Requirement three, deliver.", "[+]", "C: One: fan-out writes the row.", "[+]", "C: Two: the dispatcher claims it, under the endpoint's cap.",
 "[+]", "C: Three: it signs and sends through the egress proxy, which arrives in version five.", "[+]", "C: Four: the proxy POSTs to the merchant's checked address.",
 "[+]", "C: Five: the attempt, success or failure, goes to the attempt log."])

S(dia("Design · sequence · FR1", "Register an endpoint", "seq-fr1"), [
 "C: Requirement one, register, as a sequence.", "[+]", "C: The developer POSTs the endpoint, its event types and its version.",
 "[+]", "C: The A-P-I sends a verification ping with a challenge,", "[+]", "C: through the egress proxy, which checks the address is public.",
 "[+]", "C: The endpoint echoes the challenge.", "[+]", "C: Only then is it active, and the secret is shown, once."], cls="dia")
S(dia("Design · sequence · FR2", "Emit with the commit", "seq-fr2"), [
 "C: Requirement two.", "[+]", "C: One transaction: book the loan, insert the outbox row, commit.",
 "[+]", "C: The relay reads unsent rows in I-D order,", "[+]", "C: publishes each, keyed by loan,", "[+]", "C: waits for the log's acknowledgement,",
 "[+]", "C: and only then marks the row sent. A crash in between publishes it twice, never zero times."], cls="dia")
S(dia("Design · sequence · FR3", "Deliver one event", "seq-fr3"), [
 "C: Requirement three.", "[+]", "C: Fan-out inserts the delivery, unique on endpoint and event, so a repeated batch is absorbed.",
 "[+]", "C: The dispatcher claims it under the cap, with a lease.", "[+]", "C: It sends the signed POST to the proxy,",
 "[+]", "C: which forwards it to the checked address.", "[+]", "C: Two hundred, in a hundred and eighty milliseconds.",
 "[+]", "C: The row is delivered, and the attempt is written."], cls="dia")
S(dia("Design · sequence · FR4", "Replay since a time, at the merchant's rate", "seq-fr4"), [
 "C: Requirement four.", "[+]", "C: The developer asks to replay everything since nine on the second, at twenty a second.",
 "[+]", "C: The A-P-I turns those dead rows back to pending, oldest first.", "[+]", "C: It sets a rate limit on the endpoint until the replay drains.",
 "[+]", "C: The dispatcher claims as usual, under the cap and the rate.", "[+]", "C: And the developer gets a replay I-D for two hundred and forty thousand deliveries."], cls="dia")

S(dia("Design · C4 level 2", "The containers, one by one", "c4-containers"), [
 "C: The C4 container view of version three, one container at a time.",
 "[+]", "C: The outbox relay is a small worker per producer database. It drains outbox rows in I-D order into the log, and holds a lease so only one copy drains each database.",
 "[+]", "C: The event log holds domain events keyed by loan for seven days. Funding, servicing and analytics read it too; webhooks are one more consumer group.",
 "[+]", "C: Fan-out turns an order by loan into isolation by endpoint. It matches subscriptions from a cache and writes delivery rows in batches, committing its offset only after the write.",
 "[+]", "C: The delivery store holds one row per delivery, sharded by endpoint. The row is the queue, the next-attempt column is the timer, and the lease is the lock.",
 "[+]", "C: The dispatcher is a pool of workers that claim rows under each endpoint's cap, sign each call, send it with hard timeouts, and write the result.",
 "[+]", "C: The merchant endpoints are outside our control: tills, accounting systems and the partner bank. We assume any of them is slow, down, or hostile.",
 "[+]", "C: The attempt log keeps every try, with its status, latency and the first bytes of the answer, for thirty days in daily partitions.",
 "[+]", "C: And the webhooks A-P-I is where merchants register endpoints, read the log, and replay. It is the only container a merchant ever touches directly."], cls="dia")
