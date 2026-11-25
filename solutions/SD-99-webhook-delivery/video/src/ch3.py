from dsl import *
import dsl

chapter(3, "Theory", 2, "What makes this problem hard, in words that outlive any product name", [
 "C: A short theory chapter before any design, in five parts: what this system is and is not, its properties, the central tension, six mechanisms each with the picture that fits it, and the options, one slide each. The failures come later, as the challenges."])

key("Theory · 1 of 5 · what it is", "A platform that turns <em>committed</em> state changes into <em>signed</em> HTTP calls to endpoints <em>we do not control</em>, retries them for days, and never lets one endpoint take <em>capacity</em> from another.", [
 "V: A webhook platform turns committed state changes into signed H-T-T-P calls to endpoints we do not control, retries them for days, and never lets one endpoint take capacity from another.", "[pause: 0.8]",
 "C: Every clause does work. Committed: the event exists only if the change does. Signed: the receiver can tell it is us. Endpoints we do not control: they are slow, down, wrong, or hostile. For days: the backlog is durable. And capacity: isolation is the product."], cls="theory")

S(plain("Theory · 1 of 5 · what it is not", "Four things it is confused with", cards(
  ("", "Not a message broker", "A broker lets consumers pull at their pace (SD-07). Here we push into servers that set no pace and give no back-pressure."),
  ("", "Not push notifications", "Pushing to our own app (SD-12) goes to a platform we trust. Here every receiver is a stranger's server."),
  ("amb", "Not webhooks we receive", "Receiving (SD-45) is about verifying others. Sending is about isolating others from each other."),
  ("red", "Not exactly-once", "Across a network into a system we do not control, the best honest promise is at-least-once plus an ID."))), [
 "C: Four confusions. It is not a message broker: a broker lets consumers pull at their own pace. Here we push into servers that give no back-pressure at all.",
 "C: It is not push notifications to our own app, which go to a platform we trust. It is not webhooks we receive, which is about verifying others. And it is not exactly-once: into a system we don't control, the honest promise is at-least-once, plus an I-D."], cls="theory")

props(S1="no-event-lost", S2="no-private-address", S3="signed-no-replay", L1="delivered-or-dead-72h", L2="healthy-stays-fast", L3="recovery-no-relapse")
S(plain("Theory · 2 of 5 · the properties", "State safety and liveness separately",
  '<div class="prop safe"><div class="lbl">Safety · must never happen</div><p>' + pid("S1") + ' An event lost after its commit, or sent for a change that rolled back.<br>' + pid("S2") + ' A call to a private or internal address.<br>' + pid("S3") + ' An unsigned call, or one a third party could replay.</p></div>'
  '<div class="prop live"><div class="lbl">Liveness · must eventually happen</div><p>' + pid("L1") + ' Every event is delivered, or visibly dead, within 72 hours.<br>' + pid("L2") + ' A healthy endpoint is served within its p99 while others fail.<br>' + pid("L3") + ' A recovered endpoint drains its backlog without falling over again.</p></div>'), [
 "[+]", "C: Three safety properties. " + ps("S1") + ": no event lost after its commit, and none for a change that rolled back. " + ps("S2") + ": no call to a private address. " + ps("S3") + ": no unsigned call, and none a third party could replay.",
 "[+]", "C: Three liveness properties. " + ps("L1") + ": every event delivered, or visibly dead, within seventy-two hours. " + ps("L2") + ": a healthy endpoint is served within its p ninety-nine while others fail. " + ps("L3") + ": a recovered endpoint drains its backlog without falling over again.",
 "C: Every fix from here names the tag of the property it serves."], cls="theory")

S(plain("Theory · 3 of 5 · the central tension", "Retry hard, or stay fair?", table(["Pull", "What it wants", "What it costs the others"], [
  ["<b>Reliability</b> for one endpoint", "retry soon, retry often, keep connections open", "workers and sockets the healthy endpoints need"],
  ["<b>Isolation</b> for everyone", "a hard cap per endpoint, then wait", "a failing endpoint drains slower"],
  ["<b>Recovery</b> for the endpoint itself", "send the backlog now", "the endpoint falls over again; a retry storm"]], "bt sm") +
  line("Resolve it with budgets: each endpoint spends its own concurrency, its own retries and its own ramp.", "a")), [
 "C: The central tension is reliability against isolation. Retrying hard for one endpoint spends workers and sockets the healthy endpoints need. A hard cap per endpoint keeps everyone else safe, but a failing endpoint drains slower. And recovery wants to send the backlog now, which knocks the endpoint over again.",
 "C: The resolution is a budget per endpoint: its own concurrency, its own retries, its own ramp. Everything else in the design serves that."], cls="theory")

def M(n, name, kind, svg, cap, prot, how, rules, costs, say, steps_say, live=False):
    lines = ["C: " + say[0]]
    for s in say[1:]: lines += ["[+]", "C: " + s]
    for s in steps_say: lines += ["[+]", "C: " + s]
    mech_slide(n, 6, name, prot, how, rules, costs, lines, diagram=(kind, svg, cap), live=live)

M(1, "A transactional outbox", "seq", "m-outbox", "Figure 3.1 — the event is a row in the same commit; the relay marks it sent only after the log acknowledges",
  pid("S1") + ".", "The event is a row written in the same transaction as the change. A relay publishes unsent rows and marks them sent after the log acknowledges.",
  "A lost event after a crash; an event for a rolled-back change.", "A table and a relay per producer; at-least-once into the log.",
  ["Mechanism one, the transactional outbox, as a message sequence.", "It protects " + ps("S1") + ".",
   "The event is a row written in the same transaction as the change, and a relay publishes unsent rows, marking them sent only after the log acknowledges.",
   "It rules out the lost event, and the event for a rolled-back change.", "It costs a table and a relay per producer, and it publishes at least once."],
  ["The producer writes the loan row and the outbox row in one transaction.", "The commit succeeds, or neither exists.", "The relay reads the unsent rows.", "It publishes each one to the log, keyed by loan.",
   "The log acknowledges.", "Only then does the relay mark the row sent. A crash before that republishes it, which is safe, because the event I-D travels with it."])
M(2, "A durable, replayable log", "c4", "m-log", "Figure 3.2 — C4 container view: appended once, read by many groups, each with its own offset",
  pid("S1") + " and " + pid("L1") + ".", "Events are appended once, keyed by loan, kept for days, and read by many consumer groups, each with its own offset.",
  "One consumer's bug losing events for everyone; no way to rewind after a bad deploy.", "A cluster to run; ordering only within a key.",
  ["Mechanism two, a durable, replayable log, drawn as who reads it.", "It protects " + ps("S1") + " and " + ps("L1") + ".",
   "Events are appended once, keyed by loan, kept for days, and read by many consumer groups, each with its own offset. A bad deploy can rewind.",
   "It rules out one consumer's bug losing events for everyone.", "It costs a cluster to run, and ordering only within a key."],
  ["The relay appends once.", "The log keeps it, keyed by loan, for seven days.", "The fan-out group reads at its own offset.", "And so does the audit group, without disturbing the first."], live=True)
M(3, "A queue per endpoint, with a concurrency cap", "erd", "m-queue", "Figure 3.3 — the queue is rows keyed by endpoint; the cap lives on the endpoint",
  pid("L2") + ".", "Deliveries are rows keyed by endpoint. A worker claims only for endpoints below their in-flight cap; pools are split by tier, as bulkheads.",
  "Head-of-line blocking; one slow endpoint holding every worker.", "A failing endpoint drains slower; caps to tune per tier.",
  ["Mechanism three, a queue per endpoint with a concurrency cap, drawn as the tables and their keys.", "It protects " + ps("L2") + ".",
   "Deliveries are rows keyed by endpoint, and a worker claims only for endpoints below their in-flight cap. Pools are split by tier, like bulkheads in a ship.",
   "It rules out head-of-line blocking, and one slow endpoint holding every worker.", "It costs a failing endpoint draining slower, and caps to tune."],
  ["The endpoint holds its tier, its cap and its state.", "A delivery row belongs to one endpoint, with its next attempt time and a lease. That row is the queue.", "Every try is an attempt row."], live=True)
M(4, "Backoff with full jitter, a breaker, a ramp", "state", "m-breaker", "Figure 3.4 — an endpoint's life: closed, open, probing, ramping",
  pid("L3") + ".", "Retry at a random time up to a doubling ceiling, capped at an hour. After five failures the breaker opens; one probe a minute; on success the rate doubles each minute up to the cap.",
  "A retry storm; synchronised retries knocking a recovering endpoint over.", "Slower recovery for an endpoint that was only briefly down.",
  ["Mechanism four, backoff with full jitter, a breaker and a ramp, drawn as a state machine of one endpoint.", "It protects " + ps("L3") + ".",
   "A retry goes at a random time below a ceiling that doubles each attempt, up to an hour. After five failures the breaker opens, and we probe once a minute. On success the rate doubles each minute up to the cap.",
   "It rules out a retry storm, and synchronised retries knocking a recovering endpoint over.", "It costs slower recovery for an endpoint that was only down for a moment."],
  ["An endpoint starts closed: deliveries flow.", "Five failures open the breaker.", "One probe a minute decides. A failed probe stays open.", "A success starts the ramp: the rate doubles each minute, and more failures reopen it, until the cap is reached."], live=True)
M(5, "The consumer contract", "seq", "m-contract", "Figure 3.5 — an ID, a sequence number and a signature make a retry harmless and a replay visible",
  pid("S3") + ", and correctness on the merchant's side.", "Every call carries an event ID, a per-loan sequence number, a timestamp and an HMAC signature; events are versioned and thin enough to say “fetch current state”.",
  "Double-processing a retry; a stale state overwriting a newer one; a forged approval.", "Merchants must store IDs and verify signatures: documentation and SDK work.",
  ["Mechanism five, the consumer contract, as the conversation with the merchant.", "It protects " + ps("S3") + ", and correctness on the merchant's side.",
   "Every call carries an event I-D, a sequence number per loan, a timestamp and an H-MAC signature. Events are versioned, and thin enough to say: fetch current state.",
   "It rules out double-processing a retry, an old state overwriting a newer one, and a forged approval.", "It costs merchants work: they store I-Ds and verify signatures, so we owe them documentation and S-D-Ks."],
  ["We send event ninety-one, sequence seven, signed.", "The merchant verifies the signature and the timestamp.", "It answers two hundred: processed.", "We retry with the same I-D.",
   "It answers two hundred again, because it has seen that I-D: not applied twice.", "Event six arrives late.", "It is older than the stored state, so it is ignored, and still answered two hundred."])
M(6, "An egress proxy", "c4", "m-egress", "Figure 3.6 — C4 container view: the proxy resolves, checks, and connects to the address it checked",
  pid("S2") + ".", "Every call leaves through one proxy that resolves the name itself, refuses private ranges, and connects to the address it checked.",
  "Server-side request forgery, including DNS rebinding after validation.", "One more hop and one more thing to keep up.",
  ["Mechanism six, an egress proxy, drawn as the path out.", "It protects " + ps("S2") + ".",
   "Every call leaves through one proxy that resolves the name itself, refuses private address ranges, and connects to exactly the address it checked.",
   "It rules out server-side request forgery, including a name that changes its address after we validated it.", "It costs one more hop to run."],
  ["The dispatcher hands over a signed request.", "The proxy resolves the name itself.", "A range check refuses private addresses.", "And it connects to that address, never to a second lookup."])

def O(letter, name, verdict, pros, cons, pits, svg, say, pick=False):
    lines = ["C: " + say[0]]
    for s in say[1:]: lines += ["[+]", "C: " + s]
    option_slide(letter, name, verdict, pros, cons, pits, svg, lines, pick=pick)

O("A", "Call the URL inside the request", "Rejected · the till sets your latency", ["No moving parts"], ["The booking waits for the till"],
  ["A till takes 30 s and holds a worker", "A crash loses the event; a rollback still sends it"], "opt-a", [
  "Option A, the first thing most people draw: call the merchant's U-R-L inside the booking request.",
  "It has no moving parts.", "But the booking waits for the till.",
  "The pitfall: a till takes thirty seconds and holds a worker.", "And a crash loses the event, while a rollback still sends it.",
  "The booking request holds a worker.", "While it waits on a merchant's till."])
O("B", "One shared queue and a worker pool", "Rejected · one slow endpoint holds the pool", ["Simple to build", "Cheap"], ["No isolation", "No replay"],
  ["One slow endpoint holds the pool", "Events for healthy merchants wait behind it"], "opt-b", [
  "Option B, one shared queue and a pool of workers.",
  "It is simple to build.", "And cheap.", "But it has no isolation.", "And no replay.",
  "The pitfall: one slow endpoint holds the whole pool.", "And events for healthy merchants wait behind it.",
  "Producers enqueue into one queue.", "All workers get stuck on the slow endpoint.", "While the healthy one waits behind it."])
O("C", "A topic or retry topic per endpoint", "Rejected · head-of-line inside a partition", ["Replayable", "Familiar"], ["Fixed retry steps", "Only partial isolation"],
  ["Head-of-line blocking inside a partition", "Topic count grows with endpoints"], "opt-c", [
  "Option C, a topic, or a retry topic per delay, for each endpoint.",
  "It is replayable.", "And familiar.", "But retries come in fixed steps.", "And isolation is only partial.",
  "The pitfall: head-of-line blocking inside a partition.", "And the number of topics grows with the number of endpoints.",
  "Producers publish.", "To topics partitioned by endpoint, with retry topics by delay.", "Consumers work them in fixed steps."])
O("D", "A log for events, delivery rows by endpoint, claimed under a cap", "The pick · with F as the honest equal",
  ["Isolation per endpoint, any delay", "Replay and an audit trail"], ["About four writes per delivery", "A few shards to run"],
  ["A claim without a lease strands rows", "Caps must be tuned per tier"], "opt-d", [
  "Option D, the pick: a log for events, then delivery rows keyed by endpoint, claimed under a cap.",
  "Isolation per endpoint, with any delay.", "And replay, with an audit trail.", "It costs about four writes per delivery.", "And a few shards to run.",
  "The pitfall: a claim without a lease strands rows.", "And caps must be tuned per tier.",
  "The log holds events, replayable.", "Fan-out writes rows by endpoint.", "The delivery rows are the queue.", "And the dispatcher claims under the cap."], pick=True)
O("E", "Managed pub/sub with push subscriptions", "Rejected · no caps, no signing, no egress control", ["Nothing to run"], ["No per-endpoint caps", "No control of signing or egress"],
  ["A slow endpoint still piles up", "Private addresses cannot be refused"], "opt-e", [
  "Option E, managed publish-subscribe with push subscriptions.",
  "There is nothing to run.", "But no per-endpoint caps.", "And no control of signing or the egress check.",
  "The pitfall: a slow endpoint still piles up.", "And private addresses cannot be refused.",
  "Producers publish.", "The service pushes to the merchant.", "On its own terms."])
O("F", "Buy a webhook service", "The honest equal · the alternate path", ["Fastest to production", "Isolation and replay included"], ["Data leaves our boundary", "A cost per message"],
  ["Their retry policy, not ours", "Lock-in on payload shapes"], "opt-f", [
  "Option F, buy a webhook service. It works.",
  "It is the fastest to production.", "And isolation and replay come included.", "But the data leaves our boundary.", "And there is a cost per message.",
  "The pitfall: their retry policy, not ours.", "And lock-in on payload shapes.",
  "Producers emit events.", "To a vendor.", "Who delivers to the merchants."])

S(plain("Theory · 5 of 5 · the options, side by side", "The matrix, as a summary", table(["Approach", "Isolation", "Replay", "Fails when"], [
  ("rej", ["A · inside the request", "none", "none", "a till takes 30 s"]),
  ("rej", ["B · one shared queue", "no", "no", "one slow endpoint holds the pool"]),
  ("rej", ["C · a topic per endpoint", "partial", "yes", "head-of-line inside a partition"]),
  ("pick", ["D · log, rows by endpoint, a cap", "yes", "yes", "write volume past a few shards"]),
  ("rej", ["E · managed pub/sub", "partial", "some", "no per-endpoint caps, signing or egress control"]),
  ("", ["F · buy a service", "yes", "yes", "not a failure: data leaves, cost per message"])], "bt xs mx")), [
 "C: The six side by side, as a summary only.", "[+]", "C: A fails the first time a till takes thirty seconds.", "[+]", "C: B fails when one slow endpoint holds the pool.", "[+]",
 "C: C has head-of-line blocking inside a partition.", "[+]", "V: D is the pick. What it gives up: about four writes per delivery, and a few shards to run.", "[+]",
 "C: E has no per-endpoint caps, no signing and no egress control.", "[+]", "C: And F, buy a service, is the honest equal. I come back to it as the alternate path."], cls="theory")
