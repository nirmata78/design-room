from dsl import *
import dsl

chapter(3, "Theory", 2, "What makes this problem hard, in words that outlive any product name", [
 "C: A short theory chapter before any design, in six parts: what this system is and is not, its properties, the central tension, six mechanisms, an options matrix, and the failure catalogue that becomes the challenge list."])

key("Theory · 1 of 6 · what it is", "A platform that turns <em>committed</em> state changes into <em>signed</em> HTTP calls to endpoints <em>we do not control</em>, retries them for days, and never lets one endpoint take <em>capacity</em> from another.", [
 "V: A webhook platform turns committed state changes into signed H-T-T-P calls to endpoints we do not control, retries them for days, and never lets one endpoint take capacity from another.", "[pause: 0.8]",
 "C: Every clause does work. Committed: the event exists only if the change does. Signed: the receiver can tell it is us. Endpoints we do not control: they are slow, down, wrong, or hostile. For days: the backlog is durable. And capacity: isolation is the product."], cls="theory")

S(plain("Theory · 1 of 6 · what it is not", "Four things it is confused with", cards(
  ("", "Not a message broker", "A broker lets consumers pull at their pace (SD-07). Here we push into servers that set no pace and give no back-pressure."),
  ("", "Not push notifications", "Pushing to our own app (SD-12) goes to a platform we trust. Here every receiver is a stranger's server."),
  ("amb", "Not webhooks we receive", "Receiving (SD-45) is about verifying others. Sending is about isolating others from each other."),
  ("red", "Not exactly-once", "Across a network into a system we do not control, the best honest promise is at-least-once plus an ID."))), [
 "C: Four confusions. It is not a message broker: a broker lets consumers pull at their own pace. Here we push into servers that give no back-pressure at all.",
 "C: It is not push notifications to our own app, which go to a platform we trust. It is not webhooks we receive, which is about verifying others. And it is not exactly-once: into a system we don't control, the honest promise is at-least-once, plus an I-D."], cls="theory")

S(plain("Theory · 2 of 6 · the properties", "State safety and liveness separately",
  '<div class="prop safe"><div class="lbl">Safety · must never happen</div><p><b>S1</b> An event lost after its commit, or sent for a change that rolled back.<br><b>S2</b> A call to a private or internal address.<br><b>S3</b> An unsigned call, or one a third party could replay.</p></div>'
  '<div class="prop live"><div class="lbl">Liveness · must eventually happen</div><p><b>L1</b> Every event is delivered, or visibly dead, within 72 hours.<br><b>L2</b> A healthy endpoint is served within its p99 while others fail.<br><b>L3</b> A recovered endpoint drains its backlog without falling over again.</p></div>'), [
 "C: Three safety properties. S-one: no event lost after its commit, and none for a change that rolled back. S-two: no call to a private address. S-three: no unsigned call, and none a third party could replay.",
 "C: Three liveness properties. L-one: every event delivered, or visibly dead, within seventy-two hours. L-two: a healthy endpoint is served within its p ninety-nine while others fail. L-three: a recovered endpoint drains its backlog without falling over again."], cls="theory")

S(plain("Theory · 3 of 6 · the central tension", "Retry hard, or stay fair?", table(["Pull", "What it wants", "What it costs the others"], [
  ["<b>Reliability</b> for one endpoint", "retry soon, retry often, keep connections open", "workers and sockets the healthy endpoints need"],
  ["<b>Isolation</b> for everyone", "a hard cap per endpoint, then wait", "a failing endpoint drains slower"],
  ["<b>Recovery</b> for the endpoint itself", "send the backlog now", "the endpoint falls over again; a retry storm"]], "bt sm") +
  line("Resolve it with budgets: each endpoint spends its own concurrency, its own retries and its own ramp.", "a")), [
 "C: The central tension is reliability against isolation. Retrying hard for one endpoint spends workers and sockets the healthy endpoints need. A hard cap per endpoint keeps everyone else safe, but a failing endpoint drains slower. And recovery wants to send the backlog now, which knocks the endpoint over again.",
 "C: The resolution is a budget per endpoint: its own concurrency, its own retries, its own ramp. Everything else in the design serves that."], cls="theory")

def mech(n, name, protects, how, rules, costs, say, live=False):
    S(plain(f"Theory · 4 of 6 · mechanism {n} of 6", name,
        f'<div class="prop {"live" if live else "safe"}"><div class="lbl">Property it protects</div><p>{protects}</p></div>'
        f'<div class="prop"><div class="lbl">How it works</div><p>{how}</p></div>'
        f'<div class="prop safe"><div class="lbl">Failure it rules out</div><p>{rules}</p></div>'
        f'<div class="prop" style="border-left-color:#FBBC05"><div class="lbl" style="color:#B06000">What it costs</div><p>{costs}</p></div>'), say, cls="theory")

mech(1, "M1 · A transactional outbox", "S1.", "The event is a row written in the same transaction as the change. A relay publishes unsent rows and marks them sent after the log acknowledges.",
     "A lost event after a crash; an event for a rolled-back change.", "A table and a relay per producer; at-least-once into the log.", [
 "C: Mechanism one, the transactional outbox. It protects S-one. The event is a row written in the same transaction as the change, and a relay publishes unsent rows, marking them sent only after the log acknowledges.",
 "C: It rules out the lost event and the event for a rolled-back change. It costs a table and a relay per producer, and it publishes at least once."])
mech(2, "M2 · A durable, replayable log", "S1 and L1.", "Events are appended once, keyed by loan, kept for days, and read by many consumer groups, each with its own offset.",
     "One consumer's bug losing events for everyone; no way to rewind after a bad deploy.", "A cluster to run; ordering only within a key.", [
 "C: Mechanism two, a durable, replayable log. It protects S-one and L-one. Events are appended once, keyed by loan, kept for days, and read by many consumer groups, each with its own offset. A bad deploy can rewind. Ordering holds only within a key."])
mech(3, "M3 · A queue per endpoint, with a concurrency cap", "L2.", "Deliveries are rows keyed by endpoint. A worker claims only for endpoints below their in-flight cap; pools are split by tier, as bulkheads.",
     "Head-of-line blocking; one slow endpoint holding every worker.", "A failing endpoint drains slower; caps to tune per tier.", [
 "C: Mechanism three, a queue per endpoint with a concurrency cap. It protects L-two. Deliveries are rows keyed by endpoint, and a worker claims only for endpoints below their in-flight cap. Pools are split by tier, like bulkheads in a ship.",
 "C: It rules out head-of-line blocking and one slow endpoint holding every worker. The cost: a failing endpoint drains slower, and caps to tune."], live=True)
mech(4, "M4 · Backoff with full jitter, a breaker, a ramp", "L3.", "Retry at a random time up to a doubling ceiling, capped at an hour. After five failures the breaker opens; one probe a minute; on success the rate doubles each minute up to the cap.",
     "A retry storm; synchronised retries knocking a recovering endpoint over.", "Slower recovery for an endpoint that was only briefly down.", [
 "C: Mechanism four: backoff with full jitter, a circuit breaker and a ramp. It protects L-three. A retry goes at a random time below a ceiling that doubles each attempt, up to an hour. Full jitter means the whole interval is random, so retries from many deliveries don't synchronise.",
 "C: After five failures the breaker opens and we probe once a minute. On success, the rate doubles each minute up to the cap. The cost is slower recovery for an endpoint that was only down for a moment."], live=True)
mech(5, "M5 · The consumer contract", "S3, and correctness on the merchant's side.", "Every call carries an event ID, a per-loan sequence number, a timestamp and an HMAC signature; events are versioned and thin enough to say “fetch current state”.",
     "Double-processing a retry; a stale state overwriting a newer one; a forged approval.", "Merchants must store IDs and verify signatures: documentation and SDK work.", [
 "C: Mechanism five, the consumer contract. It protects S-three, and correctness on the merchant's side. Every call carries an event I-D, a sequence number per loan, a timestamp and an H-MAC signature. Events are versioned, and thin enough to say: fetch current state.",
 "C: It rules out double-processing a retry, an old state overwriting a newer one, and a forged approval. It costs merchants work: they store I-Ds and verify signatures, so we owe them documentation and S-D-Ks."])
mech(6, "M6 · An egress proxy", "S2.", "Every call leaves through one proxy that resolves the name itself, refuses private ranges, and connects to the address it checked.",
     "Server-side request forgery, including DNS rebinding after validation.", "One more hop and one more thing to keep up.", [
 "C: Mechanism six, an egress proxy. It protects S-two. Every call leaves through one proxy that resolves the name itself, refuses private address ranges, and connects to exactly the address it checked.",
 "C: It rules out server-side request forgery, including a name that changes its address after we validated it. The cost: one more hop to run."])

S(plain("Theory · 4 of 6 · the mechanisms at work", "Where each mechanism will live", table(["Mechanism", "Container", "One clause"], [
  ["M1 outbox", "outbox relay, in each producer", "the event is part of the commit"],
  ["M2 log", "event log", "one copy, many readers, rewind"],
  ["M3 queue per endpoint", "delivery store, dispatcher", "rows by endpoint, claimed under a cap"],
  ["M4 backoff, breaker, ramp", "dispatcher, endpoint health", "time is spread; recovery is earned"],
  ["M5 contract", "fan-out, renderer", "ID, sequence, signature, version"],
  ["M6 egress", "egress proxy", "check the address you connect to"]], "bt sm")), [
 "C: Where each mechanism lives.",
 "[+]", "C: The outbox, inside each producer, drained by the relay.",
 "[+]", "C: The log, as the event log.",
 "[+]", "C: The queue per endpoint, in the delivery store and the dispatcher.",
 "[+]", "C: Backoff, the breaker and the ramp, in the dispatcher and the endpoint health loop.",
 "[+]", "C: The contract, in fan-out and its renderer.",
 "[+]", "C: And the egress check in the proxy."], cls="theory")

S(dia("Theory · the mechanisms on the containers", "The same labels, hung on the containers I will draw next", "th-where"), [
 "C: The same labels, on the container view I'll build in chapter five. I'll walk it properly there; for now, notice that every mechanism has exactly one home.",
 "[+*]", "C: M-one on the relay, M-two on the log, M-three on the store and the dispatcher, M-four on the dispatcher and the health loop, M-five on fan-out, and M-six on the proxy."], cls="dia theory")

S(dia("Theory · a mechanism at protocol level", "Claim, send, time out, reschedule", "seq-th-claim"), [
 "C: Mechanism three and four at protocol level.",
 "[+]", "C: The dispatcher claims due rows for endpoints under their cap, with a thirty-second lease.",
 "[+]", "C: It sends a signed POST with a ten-second timeout.",
 "[+]", "C: The endpoint doesn't answer.",
 "[+]", "C: So the dispatcher writes the next attempt time: now, plus a random time up to a ceiling that doubles each attempt. Forty seconds, at attempt three.",
 "[+]", "C: The row is simply due again later. Nothing is held in memory, and no worker waits."], cls="dia theory")

S(plain("Theory · 5 of 6 · the options", "Six ways to deliver webhooks", table(["Approach", "Isolation", "Per-message delay", "Replay", "Fails when"], [
  ("rej", ["A · Call the URL inside the request", "none", "none", "none", "a till takes 30 s"]),
  ("rej", ["B · One shared queue, a worker pool", "no", "fixed", "no", "one slow endpoint holds the pool"]),
  ("rej", ["C · Kafka partition or retry topic per endpoint", "partial", "fixed steps", "yes", "head-of-line inside a partition"]),
  ("pick", ["<b>D · Log for events, delivery rows by endpoint, claimed under a cap</b>", "yes", "any", "yes", "write volume past a few shards"]),
  ("rej", ["E · Managed pub/sub with push subscriptions", "partial", "limited", "some", "no per-endpoint caps, signing or SSRF control"]),
  ("", ["F · Buy a webhook service", "yes", "any", "yes", "not a failure: data leaves, cost per message"])], "bt xs mx")), [
 "C: The options.", "[+]", "C: A: call the U-R-L inside the request: it fails the first time a till takes thirty seconds.",
 "[+]", "C: B: one shared queue and a worker pool: one slow endpoint holds the pool.",
 "[+]", "C: C: a Kafka partition or a retry topic per endpoint: partial isolation, fixed retry steps, and head-of-line blocking inside each partition.",
 "[+]", "C: D, the pick: a log for events, then delivery rows keyed by endpoint, claimed under a cap. Isolation, any delay, replay. What it gives up: write amplification, about four writes per delivery, and a few shards to run.",
 "[+]", "C: E: managed publish-subscribe with push subscriptions: no per-endpoint caps, no control over signing or the egress check.",
 "[+]", "C: And F, buy a webhook service: the honest equal. It works. I'll come back to it as the alternate path."], cls="theory")

S(plain("Theory · 6 of 6 · the failure catalogue", "What will go wrong, in the order I will take it", table(["#", "Failure", "Kind"], [
  ["1", "Delivery inside the business request", "correctness"], ["2", "One slow endpoint starves everyone", "overload · crux"],
  ["3", "An endpoint is down for two days, then returns", "recovery · crux"], ["4", "Duplicates and events out of order", "correctness"],
  ["5", "Hostile URLs and forged calls", "security"], ["6", "A producer changes the payload", "contract · teams"],
  ["7", "“You never sent it”", "observability"]], "bt xs")), [
 "C: The failure catalogue, which becomes the challenge list. Delivery inside the request. One slow endpoint starving everyone, and an endpoint down for two days that then returns: those two are the crux. Duplicates and reordering. Hostile U-R-Ls and forged calls. A producer changing the payload, which is a contract problem and a team problem. And the merchant who says we never sent it."], cls="theory")
