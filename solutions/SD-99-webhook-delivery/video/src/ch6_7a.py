from dsl import *

# ───────────────────────── 6 · bridge ─────────────────────────
chapter(6, "Bridge", 4, "It works. Where does it break first?", [
 "V: It works. Where does it break first?", "[pause: 1.0]"])

S(dia("Challenge map", "Seven attack points on the same baseline", "map", chip=chips("each fix creates the next question")), [
 "C: The baseline, with seven attack points. The producers: what if delivery happens inside their request. The dispatcher: one slow endpoint, then a dead one. Endpoint health: the recovery. Fan-out: duplicates and order. The egress path: hostile U-R-Ls and forged calls. The renderer: a producer changing the payload. And the attempt log: how we'd know. I'll take them in an order where each fix creates the next question."], cls="dia")

chapter(7, "Challenges", 5, "Seven ways to break it, and what survives", [
 "C: Seven challenges, each the same way: the question, the naive answer, a case with numbers, where it breaks, the fix one level down, why it works, the push on the fix itself, and what I'd say in the room."])

K = lambda n, t: f"Challenge {n} of 7 · {t}"

# ───────── Challenge 1 · delivery inside the request ─────────
subchapter("7.1", "Challenge 1: Why not publish after the commit?", ["N: Challenge one. The interviewer pokes at the outbox: is it really needed, or is it ceremony?"])
qs("Interviewer · challenge 1 of 7", "“Why an outbox table? Commit the loan, then publish to Kafka. Simpler.”", [
 "I: Why an outbox table? Commit the loan, then publish to Kafka. It's simpler.", "[pause: 2.0]"])

S(dia(K(1, "a dual write"), "Two systems, two commits, no atomicity", "ch1-attack", q=True, red=True,
      extra=strip(("case", "Naive answer", "“Commit, then publish. If the publish fails, retry it.”"), cols="one")), [
 "C: The naive answer: commit, then publish, and retry the publish if it fails. Look at the producer, marked red. It is the same flaw as calling the merchant inside the request: two systems, two commits, and nothing that makes them one."], cls="dia")

S(trace(K(1, "the trace"), "A booked loan that nobody hears about", [
  ("09:14:02.100", "ln_7781 committed: BOOKED"),
  ("09:14:02.104", "<span class='bad'>the process is killed by a deploy before the publish</span>"),
  ("09:14:05.000", "the customer is told “approved”; the till waits for loan.booked"),
  ("09:16:00.000", "<span class='bad'>no event: the merchant voids the sale; a loan exists with no purchase</span>"),
  ("other order", "<span class='bad'>publish first, then the commit fails: the till hands over goods for a loan that never existed</span>")],
  hedge=("Label the numbers", "Times illustrative; the window is milliseconds, and at 800 events a second it is hit every deploy.")), [
 "C: The trace.", "[+]", "C: The loan is committed as booked.",
 "[+]", "C: Four milliseconds later a deploy kills the process, before the publish.",
 "[+]", "C: The customer sees approved, and the till waits for the event.",
 "[+]", "C: It never comes. The merchant voids the sale, and we hold a loan with no purchase behind it.",
 "[+]", "C: Publish first instead, and when the commit fails, the till hands over goods for a loan that never existed.",
 "[+]", "C: The window is milliseconds, but at eight hundred events a second, every deploy hits it."])

S(dia(K(1, "the fix"), "The event is a row in the same commit", "ch1-fix",
      extra=strip(("fixb", "Mechanism", "INSERT outbox(event_id, loan_id, seq, type, body) in the loan's transaction; the relay reads unsent rows by ID, publishes keyed by loan, marks sent after the ack."), cols="one")), [
 "C: The fix, one level down. The producer inserts an outbox row in the loan's own transaction: the event I-D, the loan, its sequence number, the type and the body.",
 "C: The relay, outlined green, reads unsent rows in I-D order, publishes each keyed by loan, and marks it sent only after the log acknowledges. S-one holds: the event exists exactly when the commit does.",
 "C: What it does not cover: a relay that dies between the acknowledgement and the mark publishes twice. That's why every consumer de-duplicates by event I-D. And it's not the tool under it, a distributed transaction across the database and the log, which neither supports well and which would couple their availability."], cls="dia")

S(plain(K(1, "the relay, as code"), "Publish, then mark; never the other way round",
  '<pre class="code" data-lang="pseudocode"><span class="kw">loop</span> every 200 ms, holding the lease:\n  rows = db.query(<span class="st">"SELECT … FROM outbox</span>\n         <span class="st">WHERE sent_at IS NULL</span>\n         <span class="st">ORDER BY id LIMIT 500"</span>)\n  <span class="kw">for</span> r <span class="kw">in</span> rows:\n    log.send(topic(r.type), key=r.loan_id,\n             value=r.body, id=r.event_id)\n  log.flush()              <span class="cm"># wait for acks</span>\n  db.mark_sent(rows)       <span class="cm"># after, never before</span></pre>'), [
 "C: The relay in pseudocode. Every two hundred milliseconds, holding its lease, read up to five hundred unsent rows in I-D order. Send each to its topic, keyed by loan, carrying the event I-D. Wait for every acknowledgement. Only then mark them sent.",
 "C: Mark before publishing and a crash loses events. Mark after, and a crash repeats them. We choose repeats, because the I-D makes them harmless."])

qs("Interviewer · the second-level push", "“It's the morning of the 2nd. 480,000 payment events in ten minutes. Is the relay the bottleneck?”", [
 "I: It's the morning of the second. Four hundred and eighty thousand payment events land in ten minutes. Is the relay the bottleneck?", "[pause: 2.0]"])

S(plain(K(1, "the second fix, and the honest limit"), "Batch, measure the oldest row, keep the table small", cards(
  ("grn", "Batch", "500 rows a round, sends pipelined: one relay does several thousand a second; the peak is 800."),
  ("", "Measure", "Alert on the age of the oldest unsent row over 30 s, not on a count."),
  ("amb", "Keep it small", "Delete sent rows after a day; a bloated outbox slows the producer's own writes.")) +
  line("Honest limit: a second relay needs the lease split by ID range. Not needed until several thousand a second.", "r")), [
 "C: Not at this scale, if it batches. Five hundred rows a round with pipelined sends is several thousand a second for one relay. The peak is eight hundred.",
 "C: Measure it by the age of the oldest unsent row, alerting over thirty seconds, not by a count. And delete sent rows after a day, because a bloated outbox slows the producer's own writes.",
 "C: The honest limit: past several thousand a second, the lease has to be split by I-D range across relays. Not needed here."])

say_slide("“No event without its commit, and none for a rollback. The outbox row is in the same transaction, the relay publishes at least once, and consumers de-duplicate by event ID.”", [
 "V: If asked, I'd say: no event without its commit, and none for a rollback. The outbox row is in the same transaction, the relay publishes at least once, and consumers de-duplicate by event I-D.", "[pause: 1.0]",
 "N: The events are now safe. The next question is whether one merchant can hurt the others."])

# ───────── Challenge 2 · one slow endpoint ─────────
subchapter("7.2", "Challenge 2: One slow endpoint", ["N: Challenge two, the first half of the crux. One merchant's server slows down at the worst moment."])
qs("Interviewer · challenge 2 of 7", "“At nine on the 2nd, one till vendor's server starts taking ten seconds. What happens to the partner bank's deliveries?”", [
 "I: At nine on the second, one till vendor's server starts taking ten seconds to answer. What happens to the partner bank's deliveries?", "[pause: 2.0]"])

S(dia(K(2, "a shared pool"), "The slow endpoint takes whatever you give it", "ch2-attack", q=True, red=True,
      extra=strip(("case", "Naive answer", "“Autoscale the dispatcher pool.”"), cols="one")), [
 "C: The naive answer: autoscale the pool. Look inside the dispatcher: the limiter and the client, marked red. Without a cap per endpoint, a slow endpoint takes whatever capacity you add. At ten seconds a call, it will hold every socket you give it."], cls="dia")

S(trace(K(2, "the trace"), "Twelve hundred sockets for one till vendor", [
  ("09:00:00", "settlement file posted: 2,400 deliveries a second"),
  ("09:00:05", "till vendor (5 %, 120 a second) slows to the 10 s timeout"),
  ("09:00:10", "<span class='bad'>1,200 calls in flight for one endpoint; the pool has 600</span>"),
  ("09:00:30", "<span class='bad'>partner bank p99: 0.3 s → 4 min; approvals at other tills wait too</span>"),
  ("09:02:00", "<span class='bad'>autoscaling doubles the pool: the slow endpoint now holds 1,200 of 1,200</span>")]), [
 "C: The trace.", "[+]", "C: At nine, the settlement file lands: two thousand four hundred deliveries a second.",
 "[+]", "C: Five seconds later, the till vendor, with five percent of the traffic, slows to our ten-second timeout.",
 "[+]", "C: By ten past, it holds twelve hundred calls in flight. The pool has six hundred.",
 "[+]", "C: The partner bank's p ninety-nine goes from a third of a second to four minutes, and approvals at every other till wait too.",
 "[+]", "C: Autoscaling doubles the pool, and the slow endpoint simply holds all of it."])

S(dia(K(2, "the fix"), "A cap per endpoint, pools per tier, a breaker", "ch2-fix",
      extra=strip(("fixb", "Mechanism", "Claim only where in_flight < cap (10 by default); in_flight changes in the claim and the result commits. Bank, large and long-tail pools never share. Breaker after 5 failures."), cols="one")), [
 "C: The fix, inside the dispatcher, with no new container. The claim query only takes rows for endpoints whose in-flight count is below their cap, ten by default. The count goes up in the claim's commit and down in the result's commit, so it lives in the same database as the rows and can't drift.",
 "C: Tier pools are bulkheads: the bank, large merchants and the long tail run on separate workers. And a breaker per endpoint opens after five failures in a row. L-two holds: the slow endpoint queues in its own rows, and everyone else's p ninety-nine doesn't move.",
 "C: What it doesn't cover: a flood of events from one merchant's own activity, which fills rows, not sockets. That's a fair-share limit at fan-out. And it's not the tool under it: a thread pool per endpoint would be twenty thousand mostly idle pools for the same isolation."], cls="dia")

S(plain(K(2, "the arithmetic"), "Little's law sets every cap", table(["Endpoint", "Rate at the peak", "× answer time", "In flight needed", "Cap"], [
  ["Till vendor, healthy", "120/s", "0.25 s", "30", "40, its own large-merchant pool"],
  ["Till vendor, slow", "120/s", "10 s", "1,200", "40: the rest wait in rows"],
  ["Partner bank", "800/s", "0.2 s", "160", "200, by contract, its own pool"],
  ["Long-tail merchant", "≤ 1/s", "0.3 s", "< 1", "10 (default)"]], "bt sm")), [
 "C: Every cap comes from Little's law.",
 "[+]", "C: The till vendor, healthy: a hundred and twenty a second times a quarter of a second is thirty in flight. A cap of forty, in the large-merchant pool.",
 "[+]", "C: The same vendor, slow: it would need twelve hundred. It gets forty, and the rest wait in rows.",
 "[+]", "C: The partner bank: eight hundred a second times a fifth of a second is a hundred and sixty. A cap of two hundred, set by contract, in its own pool.",
 "[+]", "C: And the long tail, under one a second: less than one in flight. The default of ten is generous."])

qs("Interviewer · the second-level push", "“The bank says your cap is throttling them. They want everything in real time.”", [
 "I: The partner bank says your cap is throttling them. They want everything in real time.", "[pause: 2.0]"])

S(plain(K(2, "the second fix, and the honest limit"), "Raise their cap by contract, or batch", cards(
  ("grn", "A contract, not a constant", "Caps are per endpoint and per tier. The bank's lag has its own target; raise its cap when its endpoint proves it can take it."),
  ("grn", "Batch for machines", "Offer the bank up to 100 events per POST: 800 a second becomes 8 calls a second."),
  ("amb", "Their capacity, not ours", "If their endpoint slows when we send faster, the cap protects them from us.")) +
  line("Honest limit: batching makes one failure cover 100 events; partial acceptance needs a per-event result list.", "r")), [
 "C: Two answers. Caps are a contract, not a constant. The bank's lag gets its own target, and we raise its cap when its endpoint proves it can take more.",
 "C: Better still, for a machine consumer, batch: up to a hundred events per POST, so eight hundred a second becomes eight calls a second. And if their endpoint slows when we send faster, the cap is protecting them from us.",
 "C: The honest limit: a batch makes one failure cover a hundred events, so the answer must list results per event, and that's a contract change for them."])

say_slide("“Every endpoint spends its own budget: a cap on in-flight calls from Little's law, pools per tier, a breaker. A slow endpoint queues in its own rows; nobody else's latency moves.”", [
 "V: If asked, I'd say: every endpoint spends its own budget. A cap on in-flight calls set by Little's law, pools per tier, and a breaker. A slow endpoint queues in its own rows, and nobody else's latency moves.", "[pause: 1.0]",
 "N: Slow is the easy half. The next question is an endpoint that is gone for days, and then comes back."])

# ───────── Challenge 3 · down for two days ─────────
subchapter("7.3", "Challenge 3: Down for two days, then back", ["N: Challenge three, the second half of the crux. Recovery is where most designs knock the endpoint over again."])
qs("Interviewer · challenge 3 of 7", "“A merchant's accounting system is down from Friday evening to Sunday evening. What happens, and what happens when it comes back?”", [
 "I: A merchant's accounting system is down from Friday evening to Sunday evening. What happens, and what happens when it comes back?", "[pause: 2.0]"])

S(dia(K(3, "fixed retries"), "Retry every ten seconds, then dump the backlog", "ch3-attack", q=True, red=True,
      extra=strip(("case", "Naive answer", "“Retry every 10 s, five times, then a dead-letter queue. Send the backlog when it's back.”"), cols="one")), [
 "C: The naive answer: retry every ten seconds, five times, then a dead-letter queue, and send the backlog when it's back. The result writer, marked red, is where that policy lives."], cls="dia")

S(trace(K(3, "the trace"), "Dead in a minute, or knocked over on Monday", [
  ("Fri 18:00", "the accounting system goes down (2 % of deliveries, 1.4 a second)"),
  ("Fri 18:01", "<span class='bad'>five retries at 10 s: the first deliveries are already dead</span>"),
  ("Sun 18:00", "240,000 deliveries waiting (1.4/s × 172,800 s)"),
  ("Sun 18:00:30", "<span class='bad'>all sent at once: 1,700 × its normal load; it falls over again</span>"),
  ("Mon 09:00", "<span class='bad'>the merchant finds 240,000 dead letters and no way to replay them</span>")]), [
 "C: The trace.", "[+]", "C: Friday at six the accounting system goes down. It takes two percent of deliveries, one point four a second.",
 "[+]", "C: A minute later, five retries at ten seconds have already killed the first deliveries.",
 "[+]", "C: By Sunday evening, two hundred and forty thousand deliveries are waiting.",
 "[+]", "C: It comes back, and we send everything at once: seventeen hundred times its normal load. It falls over again.",
 "[+]", "C: And on Monday the merchant finds a quarter of a million dead letters, and no way to replay them."])

S(dia(K(3, "the fix"), "Time is spread, recovery is earned", "ch3-fix", vtag="V4",
      extra=strip(("fixb", "Mechanism", "next = now + random(0, min(1 h, 10 s × 2ⁿ)); dead after 72 h. A breaker pauses the endpoint; one probe a minute; on success 1/s, doubling each clean minute to the cap; over 5 % errors halves it."), cols="one")), [
 "C: The fix, version four: a new container, endpoint health, a control loop beside the dispatcher.",
 "C: One level down. The result writer sets the next attempt to now plus a random time below a ceiling that doubles each attempt, capped at an hour. That's full jitter, so a quarter of a million rows don't retry in step. After seventy-two hours a delivery is dead, visibly.",
 "C: The breaker pauses the whole endpoint after five failures, so its rows stop being claimed at all, and health probes one oldest delivery a minute. On success it opens at one a second and doubles each clean minute up to the cap. Over five percent errors, it halves. L-three holds: recovery is earned, not dumped.",
 "C: What it doesn't cover: an endpoint that is up but answers four hundred to everything, a bug on their side. Those die per delivery after the window, and the dashboard says why. And it's not a fixed retry count, which a weekend outlasts."], cls="dia")

S(dia(K(3, "version 4"), "Endpoint health joins the baseline", "base-v4", vtag="V4"), [
 "[+]", "C: On the baseline: the dispatcher, the delivery store and the attempt log are carried.",
 "[+]", "C: Endpoint health is new. It reads outcomes from the attempt log, and pauses, probes and ramps each endpoint by writing to the delivery store."], cls="dia")

S(dia(K(3, "sequence"), "The ramp, step by step", "seq-ch3-ramp"), [
 "C: The ramp as a sequence.", "[+]", "C: The breaker has been open since Friday; health probes once a minute.",
 "[+]", "C: The dispatcher sends one oldest delivery.", "[+]", "C: It answers two hundred.",
 "[+]", "C: Half-open: one a second.", "[+]", "C: No errors for a minute: double, up to the cap.",
 "[+]", "C: And if errors pass five percent, halve the rate. At the cap of ten in flight, the backlog drains in under two hours."], cls="dia")

S(plain(K(3, "the merchant's side"), "Disable, tell them, and let them replay", table(["When", "What we do"], [
  ["breaker open 1 h", "email the endpoint's technical contact; a banner in the dashboard"],
  ["failing 72 h", "deliveries dead; the endpoint disabled; email again"],
  ["they fix it", "replay since a time, at a rate they choose; oldest first per loan"],
  ["a 410", "unsubscribe that endpoint at once: they told us to stop"]], "bt sm")), [
 "C: The merchant's side.", "[+]", "C: After an hour with the breaker open, we email the endpoint's technical contact and put a banner in their dashboard.",
 "[+]", "C: After seventy-two hours, the deliveries are dead and the endpoint is disabled, with another email.",
 "[+]", "C: When they fix it, they replay since a time, at a rate they choose, oldest first per loan.",
 "[+]", "C: And a four-ten means stop: we unsubscribe at once."])

qs("Interviewer · the second-level push", "“They replay 240,000 events. Their till only cares about the current status of each loan. Do you send all of them?”", [
 "I: They replay two hundred and forty thousand events. Their till only cares about the current status of each loan. Do you send all of them?", "[pause: 2.0]"])

S(plain(K(3, "the second fix, and the honest limit"), "Offer a latest-state replay", cards(
  ("grn", "Latest per loan", "Collapse the backlog to the newest event per loan: 240,000 events for about 60,000 loans become 60,000 calls."),
  ("", "Full history", "Accounting systems need every refund and payment: replay all, oldest first per loan."),
  ("amb", "Their choice", "The replay request names the mode; the dashboard says which one they used.")) +
  line("Honest limit: a collapsed replay hides intermediate states; anything that books money must take the full history.", "r")), [
 "C: Offer both. A latest-state replay collapses the backlog to the newest event per loan: two hundred and forty thousand events for about sixty thousand loans become sixty thousand calls. A till wants that.",
 "C: An accounting system needs every refund and payment, so it replays the full history, oldest first per loan. The replay request names the mode.",
 "C: The honest limit: a collapsed replay hides intermediate states, so anything that books money must take the full history."])

say_slide("“Retries spread with full jitter, capped at an hour, for 72 hours. A breaker pauses the endpoint, probes, and ramps it back. The merchant is told, and replays at a rate they choose.”", [
 "V: If asked, I'd say: retries spread with full jitter, capped at an hour, for seventy-two hours. A breaker pauses the endpoint, probes it, and ramps it back. The merchant is told, and replays at a rate they choose.", "[pause: 1.0]",
 "N: Replays and retries mean the same event can arrive twice, and late. That's the next question."])

# ───────── Challenge 4 · duplicates and order ─────────
subchapter("7.4", "Challenge 4: Twice, and out of order", ["N: Challenge four. What the merchant sees when at-least-once meets a retry."])
qs("Interviewer · challenge 4 of 7", "“A till shows a loan as refunded after it was paid off, and it processed one refund twice. Fix it.”", [
 "I: A merchant's till shows a loan as refunded after it was paid off, and it processed one refund twice. Fix it.", "[pause: 2.0]"])

S(dia(K(4, "promise more"), "Exactly once, in order: the promise we cannot keep", "ch4-attack", q=True, red=True,
      extra=strip(("case", "Naive answer", "“Guarantee exactly-once, in-order delivery.”"), cols="one")), [
 "C: The naive answer: guarantee exactly-once delivery, in order. The delivery writer, marked red, can't keep that promise, because what breaks it happens on the other side of the network."], cls="dia")

S(trace(K(4, "the trace"), "The till did the work; the answer was lost", [
  ("10:00:00", "loan.refunded (seq 7) sent; the till applies it"),
  ("10:00:10", "<span class='bad'>the till's answer is lost: we see a timeout</span>"),
  ("10:01:00", "loan.paid_off (seq 8) delivered; the till shows PAID OFF"),
  ("10:05:20", "<span class='bad'>seq 7 retried: the till applies the refund twice and shows REFUNDED</span>")]), [
 "C: The trace.", "[+]", "C: At ten, the refund event, sequence seven, is sent, and the till applies it.",
 "[+]", "C: Its answer is lost. We see a timeout.",
 "[+]", "C: A minute later, paid off, sequence eight, is delivered.",
 "[+]", "C: Then our retry of sequence seven arrives. The till applies the refund twice and shows refunded. Only the till knew the first one had worked."])

S(dia(K(4, "the fix"), "An ID to de-duplicate, a sequence to order", "ch4-fix",
      extra=strip(("fixb", "Mechanism", "Webhook-Id for de-duplication (keep IDs 7 days, past our 72 h); a per-loan sequence assigned in the producer's commit; thin events and GET /loans/{id} for current state."), cols="one")), [
 "C: The fix is the contract, with no version change. At-least-once, said out loud, and every call carries the event I-D. The till keeps the I-Ds it has processed for seven days, longer than our seventy-two-hour window, so a retry is ignored.",
 "C: One level down: the sequence. It is the loan's version, incremented in the same transaction as the change and written into the outbox row, so it is monotonic and gap-free per loan. The till applies an event only if its sequence is higher than the last one it saw. Sequence seven after eight is dropped.",
 "C: And events are thin enough that a till can always fetch the loan's current state instead. What it doesn't cover: a merchant who ignores the contract. That's documentation, an S-D-K, and a test tool."], cls="dia")

S(plain(K(4, "the receiver, as code"), "What we ask every merchant to do",
  '<pre class="code" data-lang="pseudocode"><span class="kw">def</span> on_webhook(req):\n  verify_signature(req)              <span class="cm"># challenge 5</span>\n  e = parse(req.body)\n  <span class="kw">if</span> seen(e.id): <span class="kw">return</span> 200          <span class="cm"># duplicate</span>\n  <span class="kw">with</span> db.transaction():\n    last = loan_seq(e.loan_id)\n    <span class="kw">if</span> e.sequence &gt; last:\n      apply(e); set_seq(e.loan_id, e.sequence)\n    mark_seen(e.id)\n  <span class="kw">return</span> 200                         <span class="cm"># fast</span></pre>'), [
 "C: What we ask every merchant to do, in pseudocode, and ship in the S-D-K. Verify the signature. If the I-D was seen, answer two hundred and stop. Otherwise, in one transaction, apply the event only if its sequence is newer than the last one for that loan, and record the I-D.",
 "C: And answer fast. A receiver that does slow work before answering turns its own latency into our retries."])

qs("Interviewer · the second-level push", "“Why not just deliver in strict order per endpoint?”", [
 "I: Why not deliver in strict order per endpoint?", "[pause: 2.0]"])

S(plain(K(4, "the second fix, and the honest limit"), "Ordered mode exists, and it costs throughput", cards(
  ("", "Ordered mode", "One in flight per endpoint: at 0.25 s a call, at most 4 a second for that endpoint."),
  ("red", "Head of line, again", "One failing event blocks every later event for that endpoint until it is dead."),
  ("grn", "The default", "Parallel delivery plus sequence numbers: order is restored where it matters, by the receiver.")) +
  line("Honest limit: a merchant who needs ordering and cannot store a sequence pays in throughput.", "r")), [
 "C: We can offer it, and say what it costs. Strict order means one call in flight per endpoint: at a quarter of a second, four a second at most. And one failing event blocks everything behind it until it dies, which is the head-of-line problem from challenge two, chosen on purpose.",
 "C: So the default is parallel delivery plus sequence numbers, with order restored by the receiver. The honest limit: a merchant who needs order and can't store a sequence pays for it in throughput."])

say_slide("“We deliver at least once; you make the effect once. Every event carries an ID to de-duplicate and a per-loan sequence to order, and is thin enough to fetch current state.”", [
 "V: If asked, I'd say: we deliver at least once; you make the effect once. Every event carries an I-D to de-duplicate, a per-loan sequence to order, and is thin enough to fetch current state.", "[pause: 1.0]",
 "N: The till now trusts the content. The next question is whether it can trust the sender, and whether we can trust the U-R-L."])
