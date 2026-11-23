from dsl import *

# ───────────────────────── 6 · bridge ─────────────────────────
chapter(6, "Bridge", 4, "It works. Where does it break first?", [
 "V: It works. The question now is where it breaks first.", "[pause: 1.0]"])

S(dia("Challenge map", "Eight attack points on the same baseline", "map", chip=chips("each fix creates the next question")), [
 "C: Here is the baseline with the attack points. Two fans on one seat, at the database. A hold that outlives its owner, at the sweeper. A payment that arrives late, at the order service. A million at the door, at the waiting room. Bots, in the same line. A stale map, at the seat-map cache. A promoter who changes the plan, at the layout and the flag. And finally: how would we know any of it was broken? I'll take them in an order where each fix creates the next question."], cls="dia")

chapter(7, "Challenges", 5, "Eight ways to break it, and what survives", [
 "C: Eight challenges. Each runs the same way: the question, the naive answer, a case with numbers, where it breaks, the fix, why it works, then the interviewer pushes on the fix itself, and I answer what I'd say in the room."])

K = lambda n, t: f"Challenge {n} of 8 · {t}"

# ───────── Challenge 1 · two fans, one seat ─────────
subchapter("7.1", "Challenge 1: Two fans, one seat", ["N: Challenge one. Two fans click the same seat in the same millisecond: what happens, mechanically?"])
qs("Interviewer · challenge 1 of 8", "“Two users click the same seat in the same millisecond. Walk me through it, mechanically.”", [
 "I: Two users click the same seat in the same millisecond. Walk me through it, mechanically.", "[pause: 2.0]"])

S(dia(K(1, "two fans, one seat"), "What stops both from winning?", "ch1-attack", q=True, red=True,
      extra=strip(("case", "Naive answer", "“Read the seat. If it is available, write the hold.”"),
                  ("case", "Break", "The check and the change are two steps. Another writer slips in between."))), [
 "C: Look at the arrow from the booking API to the seat database. The check and the change are two separate steps, and another writer can slip in between them."], cls="dia")

S(plain(K(1, "the trace"), "Two writers, one gap", '<pre class="trace"><span class="t">10:00:01.120  </span>Fan A reads seat 102: AVAILABLE\n<span class="t">10:00:01.121  </span>Fan B reads seat 102: AVAILABLE\n<span class="t">10:00:01.130  </span>Fan A writes: held by A\n<span class="t">10:00:01.131  </span><span class="bad">Fan B writes: held by B. Both are told they hold seat 102</span>\n<span class="t">10:03:10      </span><span class="bad">Both pay. Two tickets for one seat: S1 is broken</span></pre>' +
  '<div class="hedge"><b class="t">Label the numbers</b>Illustrative times. The gap between the read and the write is milliseconds, and at thirty-three thousand attempts a second it is hit constantly.</div>', q=True, red=True), [
 "C: The trace. At ten o'clock and one point one two zero seconds, Fan A reads seat one hundred two: available. A millisecond later Fan B reads it: available. A writes, then B writes, and both are told they hold the seat. Three minutes later both pay. Two tickets for one seat. That breaks safety property one.",
 "C: the gap is milliseconds wide, and under this load it is hit constantly."])

S(dia(K(1, "the fix"), "One statement is the check and the change", "ch1-fix",
      extra=strip(("fixb", "Mechanism", "A conditional update: the condition in the WHERE clause is the availability check. Rows locked in ascending order, with no waiting. All seats or none."),
                  ("whyb", "Property", "S1: whoever commits first wins. The other's condition is false and it changes zero rows."))), [
 "C: The fix. The arrow from the API to the database is now one conditional update. The condition is the availability check, so there is no gap. The rows are locked in ascending order, so two fans asking for the same pair can never deadlock, and the lock fails at once instead of queueing. Then the update changes the seats only if they are still available."], cls="dia")

S(plain(K(1, "the claim, in pseudocode"), "Lock in order, claim if free, all or nothing",
  '<pre class="code"><span class="kw">BEGIN</span>\n<span class="cm">-- 1. lock the rows, in a stable order; fail now, do not queue</span>\n<span class="kw">SELECT</span> seat_id <span class="kw">FROM</span> event_seat <span class="kw">WHERE</span> seat_id = ANY(:seats)\n  <span class="kw">ORDER BY</span> seat_id <span class="kw">FOR UPDATE NOWAIT</span>\n<span class="cm">-- 2. the WHERE clause IS the availability check</span>\n<span class="kw">UPDATE</span> event_seat <span class="kw">SET</span> state = \'HELD\', hold_id = :h, expires_at = now() + 5 min\n  <span class="kw">WHERE</span> seat_id = ANY(:seats) <span class="kw">AND</span> (state = \'AVAILABLE\'\n        <span class="kw">OR</span> (state = \'HELD\' <span class="kw">AND</span> expires_at &lt; now()))\n  <span class="kw">RETURNING</span> seat_id\n<span class="cm">-- fewer rows than asked: ROLLBACK, answer 409 with a fresh bitmap</span>\n<span class="kw">INSERT</span> hold ... ;  <span class="kw">INSERT</span> outbox \'SeatsHeld\' ... ;  <span class="kw">COMMIT</span></pre>' +
  grade("Naming the lock order unprompted shows the candidate has met a deadlock. Naming the 409 payload shows they have thought about the next click.")), [
 "C: In pseudocode. Begin. Lock the requested rows in sorted order, failing at once if another buyer holds one. Then update those seats to held, with a five-minute expiry, only where the seat is available, or its old hold has expired. The condition is the check. If fewer rows came back than were asked for, roll back and answer four-oh-nine with a fresh bitmap. Otherwise insert the hold and the outbox row and commit. All or nothing: a partial hold would leave an orphan seat held for five minutes."])

S(dia(K(1, "sequence"), "Fan A wins. Fan B fails fast and gets a fresh map", "seq-hold-race"), [
 "C: As a sequence. Fan A asks for seats one-oh-one and one-oh-two. The inventory service locks the rows in order. Fan B asks for one-oh-two and one-oh-three. It tries to lock one-oh-two, which is taken: the database answers immediately that the row is locked, and Fan B gets a four-oh-nine with a fresh bitmap. Fan A's update claims two rows, the hold and outbox row are inserted, commit, and A gets a two-oh-one with an expiry."], cls="dia")

qs("Interviewer · the second-level push", "“What if your code has a bug and issues a second ticket anyway? Or the primary fails over in the middle of a claim?”", [
 "I: What if your code has a bug and issues a second ticket anyway? Or the primary fails over in the middle of a claim?", "[pause: 2.0]"])

S(plain(K(1, "the second fix, and the honest limit"), "A second, independent guard, and a replica that agrees", '<div class="cards c2">'
  '<div class="cd grn"><h3>A constraint the code cannot skip</h3><p>The ticket table has a unique constraint on event and seat. If a bug ever issues a second ticket for seat 102, the database rejects the insert.</p></div>'
  '<div class="cd amb"><h3>Failover mid-claim</h3><p>The claim is one transaction. A synchronous replica means an acknowledged hold is never lost; an unacknowledged one never became a hold.</p></div></div>' +
  line("Two independent guards are far less likely to fail together. Failover costs a few seconds of refused holds, not a wrong sale.", "a")), [
 "C: A second guard the code cannot skip. The ticket table has a unique constraint on event and seat, so if a bug ever tries to issue a second ticket for seat one hundred two, the database rejects the insert. Two independent guards are far less likely to fail together.",
 "C: And failover in the middle of a claim: the claim is one transaction, and with a synchronous replica an acknowledged hold is never lost. An unacknowledged one never became a hold. The cost is a few seconds of refused holds, not a wrong sale."])

say_slide("“One conditional update is the check and the change, all or nothing, with rows locked in a stable order. The loser fails in milliseconds and gets a fresh map. And the ticket table has a unique constraint on event and seat as a second, independent guard.”", [
 "V: If asked, I'd say: one conditional update is the check and the change, all or nothing, with rows locked in a stable order. The loser fails in milliseconds and gets a fresh map. And the ticket table has a unique constraint on event and seat as a second, independent guard.", "[pause: 1.0]",
 "N: That fix creates the next question: the hold needs an end."])

# ───────── Challenge 2 · the hold that outlives its owner ─────────
subchapter("7.2", "Challenge 2: The hold that outlives its owner", ["N: Challenge two. A fan holds two seats and closes the laptop: who frees them, and what if the thing that frees them is down?"])
qs("Interviewer · challenge 2 of 8", "“A fan holds two seats and closes the laptop. Your cleanup job is down for ten minutes. What do users see?”", [
 "I: A fan holds two seats and closes the laptop. Your cleanup job is down for ten minutes. What do users see?", "[pause: 2.0]"])

S(dia(K(2, "the hold that outlives its owner"), "Who frees a seat nobody is looking at?", "ch2-attack", q=True, red=True,
      extra=strip(("case", "Naive answer", "“A cleanup job every minute releases expired holds.”"),
                  ("case", "Break", "Correctness depends on a job. If the job is slow or down, seats are neither free nor sold."))), [
 "C: The naive answer: a cleanup job every minute releases expired holds. Look at the seat database under attack. A hold has no owner left, and the seat is neither free nor sold. If the only thing that frees it is a job, then every failure of the job is a failure of the sale."], cls="dia")

S(plain(K(2, "the trace"), "Fifty seconds of invisible seats, or forever", '<pre class="trace"><span class="t">10:00:00  </span>Fan A holds seats 101 and 102, five minutes\n<span class="t">10:05:00  </span>the hold expires. Fan A is gone\n<span class="t">10:05:01  </span>Fan C clicks 101: <span class="bad">the row says HELD, so C is refused</span>\n<span class="t">10:05:50  </span>the job finally runs: <span class="bad">fifty seconds of two good seats refused</span>\n<span class="t">job down    </span>ten minutes: <span class="bad">every expired seat stays taken, sell-through stalls</span></pre>' +
  '<div class="hedge"><b class="t">Label the numbers</b>Illustrative.</div>', q=True, red=True), [
 "C: The trace. Fan A holds seats one-oh-one and one-oh-two at ten. At five past, the hold expires and Fan A is gone. A second later Fan C clicks seat one-oh-one and is refused, because the row still says held. The job runs at ten-oh-five-fifty: fifty seconds of two good seats refused. And if the job is down for ten minutes, every expired seat stays taken and sales stall. This is liveness property one: a seat stuck in limbo."])

S(dia(K(2, "the fix"), "Two paths, each covering the other's gap", "ch2-fix",
      extra=strip(("fixb", "Mechanism", "Lazy: the claim treats an expired hold as free. Sweeper: every 5 s, small batches, skipping locked rows, and it announces each release."),
                  ("whyb", "Property", "L1: correctness never depends on the job. The job only makes the map catch up."))), [
 "C: The fix, with two paths. Lazy expiry: the claim from challenge one already says a seat is claimable if it is available, or if it is held and its expiry is in the past. So an expired hold is claimable the instant it expires, whether or not any job has run. Correctness never depends on the sweeper.",
 "C: And the sweeper, the new box under the database. Every five seconds it releases expired holds and announces each release through the outbox. Without it expired seats would be claimable but invisible on everyone's map."], cls="dia")

S(plain(K(2, "the sweeper, in pseudocode"), "Small batches, and never wait for a buyer",
  '<pre class="code"><span class="cm">-- every 5 s per hot event; several instances may run in parallel</span>\n<span class="kw">WITH</span> expired <span class="kw">AS</span> (\n  <span class="kw">SELECT</span> seat_id <span class="kw">FROM</span> event_seat\n   <span class="kw">WHERE</span> state = \'HELD\' <span class="kw">AND</span> expires_at &lt; now()\n   <span class="kw">ORDER BY</span> expires_at <span class="kw">LIMIT</span> 500\n   <span class="kw">FOR UPDATE SKIP LOCKED</span>)          <span class="cm">-- skip a row a buyer is claiming</span>\n<span class="kw">UPDATE</span> event_seat s <span class="kw">SET</span> state = \'AVAILABLE\', hold_id = NULL\n  <span class="kw">FROM</span> expired x <span class="kw">WHERE</span> s.seat_id = x.seat_id <span class="kw">RETURNING</span> s.seat_id\n<span class="cm">-- same transaction: INSERT outbox \'SeatsReleased\'; COMMIT</span></pre>'), [
 "C: The sweeper in pseudocode. Select the held rows whose expiry has passed, oldest first, at most five hundred, and skip any row that is locked. Then set them available and return them. In the same transaction, write the released event to the outbox. Skip-locked, not no-wait: the sweeper needs any expired seats, so if a buyer is claiming one it moves on, and several sweepers never block each other."])

S(dia(K(2, "sequence"), "Lazy expiry claims an expired seat; the sweeper catches the rest", "seq-expiry"), [
 "C: As a sequence. Fan C claims seat one-oh-one, whose hold expired two seconds ago: the lazy predicate lets it through at once. Later, the sweeper finds seat one-oh-two, which nobody tried. It releases it and writes the event, the snapshot builder hears it, and the map shows seat one-oh-two free on the next version."], cls="dia")

qs("Interviewer · the second-level push", "“Your sweeper releases a seat while its owner is entering a card number. Or it is simply down.”", [
 "I: Your sweeper releases a seat while its owner is entering a card number. Or it is simply down.", "[pause: 2.0]"])

S(plain(K(2, "the second fix, and the honest limit"), "Only held seats expire; a dead sweeper costs staleness, not a sale", '<div class="cards c2">'
  '<div class="cd grn"><h3>Frozen seats are never touched</h3><p>The predicate says state equals held. A seat in payment-pending is not eligible. Only the order service, on a definite outcome, can release it. That is challenge three.</p></div>'
  '<div class="cd amb"><h3>A dead sweeper</h3><p>Expired seats are still claimable lazily. The map shows them taken, so sell-through slows. <b>Alert on the age of the oldest expired hold above 30 seconds.</b></p></div></div>' +
  line("Staleness, not oversell. And an alert that tells you before the fans do.", "a")), [
 "C: Two answers. First, the sweeper only touches held seats. A seat whose payment is in flight is in payment-pending, a different state, so it is simply not eligible. Only the order service, on a definite outcome, can release it.",
 "C: Second, a dead sweeper costs staleness, not oversell. Expired seats are still claimable through the lazy path, but the map shows them as taken, so fans do not click them and sell-through slows. I alert on the age of the oldest expired hold: anything above thirty seconds means the sweeper is not keeping up."])

say_slide("“Two expiry paths, each covering the other's gap. The claim treats an expired hold as free, so correctness does not depend on a job. A sweeper releases in small batches and announces it, so the map catches up. If it dies, we get staleness, not oversell, and an alert on the oldest expired hold.”", [
 "V: If asked, I'd say: two expiry paths, each covering the other's gap. The claim treats an expired hold as free, so correctness does not depend on a job. A sweeper releases in small batches and announces it, so the map catches up. If it dies, we get staleness, not oversell, and an alert on the oldest expired hold.", "[pause: 1.0]",
 "N: That fix creates the next question: what if the seat expires while the fan is paying?"])

# ───────── Challenge 3 · the hold expires, then the payment succeeds ─────────
subchapter("7.3", "Challenge 3: The hold expires, then the payment succeeds", ["N: Challenge three. The best probe in the round: the hold expires while the payment provider is thinking, then the payment succeeds."])
qs("Interviewer · challenge 3 of 8", "“The hold expires while the payment provider is still thinking, then the payment succeeds. What do you do?”", [
 "I: The hold expires while the payment provider is still thinking, then the payment succeeds. What do you do?", "[pause: 2.0]"])

S(dia(K(3, "expiry meets payment"), "Two people paid for one seat", "ch3-attack", q=True, red=True,
      extra=strip(("case", "Naive answer", "“The hold expired, so release the seat. If the payment arrives later, refund.”"),
                  ("case", "Break", "Nothing stops the seat being sold to someone else while a payment is in flight."))), [
 "C: The naive answer: the hold expired, so release the seat, and if the payment arrives later, refund. Look at the order service and the arrow into the database. Nothing stops the seat from being claimed by someone else while the first fan's payment is still in flight. There is no perfectly clean answer here, so I take a position and defend it."], cls="dia")

S(plain(K(3, "the trace"), "A late approval for a seat already sold", '<pre class="trace"><span class="t">4:50  </span>Fan A submits payment. The provider is slow\n<span class="t">5:00  </span>A\'s hold expires\n<span class="t">5:01  </span><span class="bad">Fan C claims seat 101: held by C</span>\n<span class="t">5:05  </span><span class="bad">the provider answers: approved, for A</span>\n<span class="t">5:05  </span>two people have paid for one seat, or one has paid for nothing</pre>' +
  '<div class="hedge"><b class="t">Label the numbers</b>Illustrative. The provider takes two to ten seconds normally; this is the tail where it takes fifteen.</div>', q=True, red=True), [
 "C: The trace. At four-fifty Fan A submits and the provider is slow. At five the hold expires. At five-oh-one Fan C claims the seat. At five-oh-five the provider answers: approved, for A. Now two people paid for one seat, or one person paid for nothing. That breaks safety property two."])

S(plain(K(3, "the position"), "Four parts. Prevent it, reserve before taking, unknown is not failure, own the residue", '<div class="cards c2">'
  '<div class="cd grn"><h3>1 · Prevent: freeze first</h3><p>Before calling the provider, move the seats from held to payment-pending, with ten more minutes. The expiry paths only touch held.</p></div>'
  '<div class="cd grn"><h3>2 · Authorize, then capture</h3><p>Authorize reserves the money. Sell the seats on approval. Capture last. Backing out is a void the fan never sees.</p></div>'
  '<div class="cd amb"><h3>3 · Unknown is not failed</h3><p>On a timeout, query by our idempotency key and accept the webhook. Seats stay frozen until the outcome is definite.</p></div>'
  '<div class="cd red"><h3>4 · The residual case</h3><p>If the provider reports success after we gave up, refund, apologise, and give the fan priority on the waitlist. Rare, measured, owned.</p></div></div>'), [
 "C: My position has four parts. One: prevent it. Before I call the provider, I freeze the seats: held becomes payment-pending, with ten more minutes. The expiry paths only touch held.",
 "C: Two: authorize, then capture. Authorize only reserves the money; I sell on approval and capture last, and backing out is a void the customer never sees. Three: unknown is not failure. A timeout means we did not hear the answer, not that there was none. I ask again with our idempotency key, and accept the webhook. Four: the residual. If the provider reports success after we gave up, we refund, apologise and give priority on the waitlist."])

S(dia(K(3, "the fix"), "Freeze before the call. A reconciler for silence", "ch3-fix",
      extra=strip(("fixb", "Mechanism", "Freeze, authorize, sell on approval, capture last. A reconciler asks the provider about unknown orders by key, with backoff, and cancels past a deadline."),
                  ("whyb", "Property", "S2: money is reserved before seats are sold, and every step is cheap to undo until the last."))), [
 "C: On the baseline. The new box is the reconciler, next to the order service. The freeze is the arrow from the order service to the database. The order service authorizes with the provider, and the provider's answer, or silence, comes back on the dashed line. A silent order becomes unknown, and the reconciler asks the provider about it, by key, with backoff."], cls="dia")

S(plain(K(3, "the freeze, in pseudocode"), "Only a still-valid hold can be frozen",
  '<pre class="code"><span class="cm">-- on POST /orders, before any call to the provider</span>\n<span class="kw">UPDATE</span> event_seat\n   <span class="kw">SET</span> state = \'PAYMENT_PENDING\', expires_at = now() + 10 min, order_id = :o\n <span class="kw">WHERE</span> hold_id = :h <span class="kw">AND</span> state = \'HELD\' <span class="kw">AND</span> expires_at &gt; now()\n<span class="kw">RETURNING</span> seat_id\n<span class="cm">-- fewer rows than in the hold: ROLLBACK, tell the fan "your hold expired"</span>\n\n<span class="cm">-- when ANY of three callers reaches a definite answer (call, reconciler, webhook)</span>\n<span class="kw">if</span> !order.transition(from = [AUTHORIZING, UNKNOWN], to = CONFIRMING): <span class="kw">return</span>\ninventory.sell(order)          <span class="cm">// PAYMENT_PENDING -> SOLD, idempotent</span>\n<span class="cm">// then, in one local transaction: confirm order, issue tickets, outbox</span></pre>'), [
 "C: In pseudocode. The freeze is one conditional update: move to payment-pending only the seats still held by this hold, and only if the hold has not expired. If fewer rows come back than the hold covers, the fan is told the hold expired, before any money moves.",
 "C: And the confirm step. Three callers may race to it: the original call, the reconciler and the webhook. A conditional status change makes it idempotent: only the first caller proceeds, and the rest return. Then sell the seats, and in one transaction confirm the order, issue the tickets and write the outbox row."])

S(plain(K(3, "the reconciler"), "What each answer from the provider means", table(["The provider says", "We do", "Why"], [
  ["<b>authorized</b>", "confirm: sell the seats, issue the tickets", "the money is reserved; capture follows"],
  ["<b>declined</b>", "fail: release the seats", "a definite no"],
  ["<b>not found</b>", "wait, then fail after two minutes", "the request may never have reached the provider"],
  ["<b>still processing</b>", "back off 2 s, 4 s, 8 s, up to 60 s; past the freeze deadline, cancel at the provider, then release", "unknown stays frozen, but not forever"]], "bt sm")), [
 "C: The reconciler asks the provider about unknown orders, by our key. Authorized: confirm. Declined: fail and release. Not found: the request may never have arrived, so wait, and fail after two minutes. Still processing: back off up to sixty seconds, and past the freeze deadline cancel at the provider, then release. Unknown stays frozen, but not forever."])

S(dia(K(3, "sequence"), "The provider goes silent: the first definite answer wins", "seq-unknown"), [
 "C: As a sequence. The order service authorizes with a ten-second timeout and gets nothing back. It marks the order unknown, not failed, and schedules a check. Two things now race: the reconciler's status query, and the provider's webhook, verified by signature and deduplicated by event identifier. Whichever brings a definite answer first calls confirm, and because confirm is idempotent it does not matter if both arrive."], cls="dia")

qs("Interviewer · the second-level push", "“The provider stays silent for an hour. Your seats are frozen for an hour.”", [
 "I: The provider stays silent for an hour. Your seats are frozen for an hour.", "[pause: 2.0]"])

S(plain(K(3, "the second fix, and the honest limit"), "A deadline, a cancel, and a trade-off I show to the product owner", '<div class="cards c2">'
  '<div class="cd grn"><h3>A deadline, not forever</h3><p>The freeze lasts ten minutes. Past it, cancel with the provider, so a late authorization is voided, then release the seats.</p></div>'
  '<div class="cd amb"><h3>The cost is explicit</h3><p>Slightly slower sell-through at the very end of the sale, because some seats sit frozen. <b>I would show that to the product owner as the trade-off.</b></p></div></div>' +
  line("Traps: a timeout treated as a decline; no idempotency key on the provider call; a transaction held open across the call; a sweeper that releases frozen seats.", "r")), [
 "C: A deadline. The freeze lasts ten minutes, and past it the reconciler cancels with the provider, so a late authorization is voided and the customer is never charged, and then it releases the seats. The cost is explicit: slightly slower sell-through at the very end of the sale. I would show that to the product owner as the trade-off.",
 "C: The traps. A timeout treated as a decline charges people for nothing. A retry without an idempotency key reserves the money twice. A transaction held open across the provider call is, at two hundred and fifty in flight, the whole connection pool. And a sweeper that releases frozen seats is the race we started with."])

say_slide("“I would rather hold a seat ten extra minutes than sell it twice or charge someone for nothing. Seats are frozen before I call the provider, sold only on an approved authorization, and an unknown outcome stays frozen until a status check or the webhook gives a definite answer. The cost is slower sell-through at the end, and I would show that trade-off to the product owner.”", [
 "V: If asked, I'd say: I would rather hold a seat ten extra minutes than sell it twice or charge someone for nothing. Seats are frozen before I call the provider, sold only on an approved authorization, and an unknown outcome stays frozen until a status check or the webhook gives a definite answer. The cost is slower sell-through at the end, and I would show that trade-off to the product owner.", "[pause: 1.0]",
 "N: That fix creates the next question: the whole system works, so how do we protect it from a million people?"])

# ───────── Challenge 4 · a million at the door ─────────
subchapter("7.4", "Challenge 4: A million at the door", ["N: Challenge four. The correctness is right; now a million people arrive in the same minute."])
qs("Interviewer · challenge 4 of 8", "“A million users hit your inventory database at once. What breaks?”", [
 "I: A million users hit your inventory database at once. What breaks?", "[pause: 2.0]"])

S(dia(K(4, "a million at the door"), "What does the database see?", "ch4-attack", q=True, red=True,
      extra=strip(("case", "Naive answer", "“Autoscale the database and the API fleet.”"),
                  ("case", "Break", "The load is on fifty thousand rows, not on a fleet. More machines do not make a row lock shorter."))), [
 "C: The naive answer: autoscale the database and the A-P-I fleet. Look at the red path from the fans to the seat database. The load is concentrated on fifty thousand rows, and really on the best few thousand. More machines do not make a row lock shorter."], cls="dia")

S(plain(K(4, "the trace"), "A pool that empties in milliseconds", '<pre class="trace"><span class="t">10:00:00.0  </span>1,000,000 fans × 2 clicks ÷ 60 s = <span class="bad">33,000 contended writes / s</span>\n<span class="t">10:00:00.1  </span>each write waits for a row lock <span class="bad">while holding a connection</span>\n<span class="t">10:00:00.3  </span>the pool of a few hundred is empty; new requests <span class="bad">time out</span>\n<span class="t">10:00:01.0  </span>clients retry: <span class="bad">the retries are the next wave</span>\n<span class="t">10:00:03.0  </span>a retry storm. The database does not slow down gracefully; it stops</pre>' +
  '<div class="hedge"><b class="t">Label the numbers</b>Illustrative. A primary does thousands of short writes a second on different rows; the same rows are the problem.</div>', q=True, red=True), [
 "C: The trace. A million fans, two clicks each in sixty seconds, is thirty-three thousand contended writes a second. Each waits for a row lock while holding a connection. The pool of a few hundred empties in a fraction of a second, new requests time out, and clients retry, so the retries are the next wave. A retry storm. The database does not slow down gracefully. It stops. These figures are illustrative: the point is that the same rows are the problem."])

S(dia(K(4, "the fix"), "A line in front, and a dial behind it", "ch4-fix",
      extra=strip(("fixb", "Mechanism", "A waiting room admits fans at a rate R chosen from shop capacity. A controller adjusts R by health. The gateway checks an admission token."),
                  ("whyb", "Property", "L3: the core only sees what it chose to admit. The demand is absorbed at the edge."))), [
 "C: The fix, on the baseline. The new boxes are the waiting room and the admission controller. A fan joins and waits at the edge. The controller sets a rate, the dotted green arrow to the waiting room, and the waiting room moves a pointer at that rate. The gateway lets in only fans carrying an admission token. By Little's law, ten thousand shoppers over five minutes is two thousand admissions a minute: that is R."], cls="dia")

S(dia(K(4, "the controller"), "Increase slowly, cut fast", "controller"), [
 "C: The controller is a feedback loop, once a second per event. It reads hold latency, database load and the provider's error rate. If any is bad it cuts the rate by thirty percent. If all is well and fewer than ten thousand shoppers are inside, it adds a small step: the same idea as congestion control, increase gently, cut sharply. Why not a fixed rate? Ten thousand is a guess until the sale is running, and real capacity depends on how slow the provider is today. It starts at a quarter of the target, because at the first second every cache is cold."], cls="dia")

S(dia(K(4, "the shared answer"), "One cached answer for a million fans", "cdn-state"), [
 "C: And the poll. Every waiting fan asks how far the line has moved, and the answer is the same bytes for everyone: the pointer, the rate, and the sold-out flag. The edge holds it for one second. So the origin sees about two hundred requests instead of a hundred thousand. The fan works out their own position from the number in their signed token."], cls="dia")

S(plain(K(4, "the pointer, in pseudocode"), "One script moves the line, and never past the last person",
  '<pre class="code"><span class="cm">-- once a second per event; one controller (a lease)</span>\nn = whole fans due this second (rate / 60, fractions carried over)\n<span class="cm">-- advance.lua, atomic in Redis</span>\ncur  = GET admittedUpTo:{e}\nlast = GET next:{e}\nnew  = min(cur + n, last)          <span class="cm">-- never admit past the last person in line</span>\nSET admittedUpTo:{e} = new ;  SET rate:{e} ;  SET soldOut:{e}\n\n<span class="cm">-- POST /admit: allowed only if my number &lt;= admittedUpTo;</span>\n<span class="cm">-- the first admission wins; asking again returns the same token</span></pre>'), [
 "C: The pointer in pseudocode. Once a second, per event, one controller chosen by a lease, so there is no double admission. Compute how many whole fans are due, carrying fractions over. Then one atomic script: set the pointer to the smaller of the pointer plus that count and the last issued number, so we never admit past the last person in line. Admit allows a fan in only when their number is at or below the pointer, and the first admission wins."])

S(dia(K(4, "sequence"), "Poll, compute, admit", "seq-admit"), [
 "C: As a sequence. The fan polls the edge, which fetches from the origin at most once a second. The browser compares the pointer to the number in its token. When it is reached, it calls admit. The waiting room checks the signature and the pointer, and returns the token. From here every shop call carries the token and the gateway verifies it, with no lookup."], cls="dia")

qs("Interviewer · the second-level push", "“What if the controller dies mid-sale? Or the edge cannot reach your origin? Or twice the people show up?”", [
 "I: What if the controller dies mid-sale? Or the edge cannot reach your origin? Or twice the people show up?", "[pause: 2.0]"])

S(plain(K(4, "the second fix, and the honest limit"), "The line pauses, it does not break", '<div class="cards c3">'
  '<div class="cd grn"><h3>A dead controller</h3><p>One leader per event by a short lease. If it dies another takes over in seconds, and the pointer simply pauses.</p></div>'
  '<div class="cd grn"><h3>An unreachable origin</h3><p>The edge keeps serving the last answer for thirty seconds. The line stalls; no one is hurt.</p></div>'
  '<div class="cd amb"><h3>Double the fans</h3><p>The database does not notice: R is set by shop health, not demand. The lobby doubles to about 200 MB of Redis.</p></div></div>' +
  line("Retries and herds are spread with jitter on every synchronised action. Admission is steady: 33 a second, not 2,000 at the top of each minute.", "a")), [
 "C: Three answers. A dead controller: one leader per event by a short lease; if it dies another takes over in seconds, and the pointer simply pauses. An unreachable origin: the edge keeps serving the last answer for thirty seconds, so the line stalls and nobody is hurt. Twice the people: the database does not notice, because the rate is set by shop health, not by demand. What doubles is the lobby, about two hundred megabytes of Redis.",
 "C: And a random delay on every synchronised action, so herds spread out. Demand is absorbed at the edge, and the core only ever sees what it chose to admit."])

say_slide("“I convert a stampede into a stream. A million people wait at the edge for almost nothing each, and a controller admits them at a rate the shop can serve, cutting it when hold latency or the payment error rate rises. The database only ever sees what I chose to admit.”", [
 "V: If asked, I'd say: I convert a stampede into a stream. A million people wait at the edge for almost nothing each, and a controller admits them at a rate the shop can serve, cutting it when hold latency or the payment error rate rises. The database only ever sees what I chose to admit.", "[pause: 1.0]",
 "N: That fix creates the next question: in what order do we admit them, and who gets in first?"])
