from dsl import *

# ───────────────────────── 6 · bridge ─────────────────────────
chapter(6, "Bridge", 4, "It works. Where does it break first?", [
 "V: It works. The question now is where it breaks first.", "[pause: 1.0]"])

S(dia("Challenge map", "Eight attack points on the same baseline", "map", chip=chips("each fix creates the next question")), [
 "C: The baseline with its attack points marked. The adapter, where a call can time out. The A-P-I, where retries arrive together. The service and the database, where a crash can split a commit from its event, where a hot merchant queues, and where refunds race. Reconciliation, where the outside world disagrees. And then a bad release, and silence. Eight challenges, in an order where each fix creates the next question."], cls="dia")

chapter(7, "Challenges", 5, "Eight ways to break it, and what survives", [
 "C: Each challenge runs the same way: the question, the naive answer, a case with numbers, where it breaks, the fix and why it works, then the interviewer pushes on the fix itself, and I say what I'd say in the room."])

K = lambda n, t: f"Challenge {n} of 8 · {t}"

# ───────── Challenge 1 · the bank timed out ─────────
subchapter("7.1", "Challenge 1: The bank timed out", ["N: Challenge one, the crux. The processor does not answer, and we do not know whether the customer paid."])
qs("Interviewer · challenge 1 of 8", "“You call the processor. It times out. You don't know whether the customer was charged. Walk me through the next ten minutes, and the next ten days.”", [
 "I: You call the processor. It times out. You don't know whether the customer was charged. Walk me through the next ten minutes, and the next ten days.", "[pause: 2.0]"])

S(dia(K(1, "the timeout"), "What does a timeout mean?", "ch1-attack", q=True, red=True,
      extra=strip(("case", "Naive answer", "“Mark it failed and let the client retry.” Or: “Retry it ourselves until it works.”"),
                  ("case", "Why it fails", "A timeout is not an answer. Either guess is wrong half the time, and one of the wrong halves is a double charge."))), [
 "C: The naive answers: mark it failed and let the client retry, or retry it ourselves until it works. Look at the red arrows between the adapter and the processor. A timeout is not an answer. It means the request may or may not have arrived, and may or may not have been approved. Either guess is wrong some of the time."], cls="dia")

S(plain(K(1, "the trace"), "Two holds for one purchase", '<pre class="trace"><span class="t">10:00:00.000  </span>attempt p-7731/1 sent, 1,050\n<span class="t">10:00:01.900  </span>client deadline: no answer\n<span class="t">10:00:01.900  </span>naive design marks it <span class="bad">failed</span>\n<span class="t">10:00:02.400  </span>the processor approves p-7731/1\n<span class="t">10:00:05.000  </span>checkout retries as p-7744: approved\n<span class="t">10:00:05.000  </span><span class="bad">two holds of 1,050 on one card</span></pre>' +
  '<div class="hedge"><b class="t">Label the numbers</b>Illustrative. The shape is real: an approval that arrives after the deadline, and a retry that is a new payment.</div>', q=True, red=True), [
 "C: The trace. The attempt is sent at ten o'clock. At one point nine seconds, the client deadline, there is no answer, and the naive design marks it failed. Half a second later the processor approves it. At five seconds the checkout retries, as a new payment, which is approved. Two holds on one card for one purchase.",
 "C: Illustrative numbers, but the shape is real: approvals do arrive after deadlines."])

S(dia(K(1, "the fix"), "Unknown is a state, and an inquiry ends it", "ch1-fix",
      extra=strip(("fixb", "Mechanism", "The attempt is committed before the call. At the deadline: UNKNOWN, answer pending. An inquiry job asks by our reference after 5 s, 30 s, 2 min."),
                  ("whyb", "Property", "S1: every retry carries the same key or the same reference. L1: every unknown has a bounded way out."))), [
 "C: The fix. The attempt was committed before the call, with our reference. At the deadline the payment moves to unknown, and the client gets pending. The merchant's retry, with the same idempotency key, gets the same pending, not a new payment. Then the new green box: the inquiry job asks the processor about our reference after five seconds, thirty seconds, two minutes."], cls="dia")

S(dia(K(1, "sequence"), "The next ten minutes", "seq-timeout"), [
 "C: As a sequence. One: authorise, with reference p-seventy-seven thirty-one slash one. The deadline passes. Two: the payment becomes unknown, and pending is the answer, to this request and to any retry with the same key. Three: the inquiry asks for the status of that reference. Approved at two point four seconds. Four: the job moves it to authorised, posts the entries and the outbox event.",
 "C: The two other exits, in the notes. Not found after the processor's safe window: declined, and now a new attempt is safe. An approval we no longer want: a reversal by the same reference."], cls="dia")

S(plain(K(1, "the next ten days"), "The settlement file is the final arbiter", table(["When", "What closes it"], [
  ["seconds", "the response, or <b>pending</b> and UNKNOWN"],
  ["minutes", "the inquiry, by our reference: approved, declined, or reversed"],
  ["next day", "the settlement file: anything the inquiry missed becomes a <b>break</b>"],
  ["days", "an adjusting transaction, and the merchant told"]], "bt") +
  strip(("whyb", "Why it works", "No path creates a second movement for one intent, and no unknown can last past the next settlement file."), cols="one")), [
 "C: And the next ten days. If the inquiry never got an answer, the settlement file is the final arbiter: a capture we did not record shows up there, becomes a break, and is fixed with an adjusting transaction and a message to the merchant. So no path creates a second movement for one intent, and no unknown can outlive the next settlement file."])

qs("Interviewer · the second-level push", "“The processor's inquiry endpoint is down too. Actually, the whole processor is down for an hour.”", [
 "I: The processor's inquiry endpoint is down too. Actually, the whole processor is down for an hour.", "[pause: 2.0]"])

S(plain(K(1, "the second fix, and the honest limit"), "Fail over only what definitely failed", '<div class="cards c2">'
  '<div class="cd grn"><h3>A breaker per processor</h3><p>Stop sending new attempts to a processor that is down. New payments go to a second processor, if the contract allows.</p></div>'
  '<div class="cd red"><h3>Never fail over an unknown</h3><p>An unknown sent again elsewhere is two possible charges. Unknowns wait, age, and show on a dashboard; the merchant sees pending.</p></div></div>' +
  line("Honest limit: a processor with neither inquiry nor idempotent references can only be resolved by the file, a day late. That is a reason to choose processors.", "r")), [
 "C: A circuit breaker per processor stops new attempts going to one that is down, and new payments go to a second processor, if the contracts allow it. But never an unknown. An unknown sent to a second processor is two possible charges. Unknowns wait, age, and show on a dashboard, and the merchant sees pending.",
 "C: The honest limit: a processor that supports neither inquiry nor idempotent references can only be resolved by the settlement file, a day late. That is a reason to choose processors, and I'd say so to whoever negotiates the contracts."])

say_slide("“A timeout is an unknown, not a failure. I commit the attempt before calling out, move the payment to unknown, answer pending, and an inquiry job asks the processor by our own reference until it knows. Retries carry the same reference, so they can't become a second charge, and the settlement file is the final arbiter.”", [
 "V: If asked, I'd say: a timeout is an unknown, not a failure. I commit the attempt before calling out, move the payment to unknown, answer pending, and an inquiry job asks the processor by our own reference until it knows. Retries carry the same reference, so they can't become a second charge, and the settlement file is the final arbiter.", "[pause: 1.0]",
 "N: That fix leans on retries being harmless. Are they?"])

# ───────── Challenge 2 · three retries at once ─────────
subchapter("7.2", "Challenge 2: Three retries at once", ["N: Challenge two. The same payment arrives three times in three milliseconds: how does only one of them count?"])
qs("Interviewer · challenge 2 of 8", "“The client sends the same payment three times, concurrently, with the same idempotency key. Then once more, same key, different amount. What happens?”", [
 "I: The client sends the same payment three times, concurrently, with the same idempotency key. Then once more, same key, different amount. What happens?", "[pause: 2.0]"])

S(dia(K(2, "concurrent retries"), "Who decides which request counts?", "ch2-attack", q=True, red=True,
      extra=strip(("case", "Naive answer", "“We check whether the key exists before processing.”"),
                  ("case", "Break", "Check-then-act on three servers: each check sees nothing, each acts."))), [
 "C: The naive answer: check whether the key exists before processing. Look at the A-P-I box. Three requests land on three servers, and each one checks, finds nothing, and charges. A check followed by an act is a race, however fast the check is."], cls="dia")

S(plain(K(2, "the trace"), "Three authorisations, and a changed amount", '<pre class="trace"><span class="t">10:00:00.001  </span>R1, key k-91, 1,050, server A: SELECT → none\n<span class="t">10:00:00.002  </span>R2, key k-91, 1,050, server B: SELECT → none\n<span class="t">10:00:00.003  </span>R3, key k-91, 1,050, server C: SELECT → none\n<span class="t">10:00:00.004  </span><span class="bad">three authorisations of 1,050</span>\n<span class="t">10:05:00      </span>R4, key k-91, <span class="bad">2,050</span>: return the old answer, or charge again?</pre>', q=True, red=True), [
 "C: The trace. Three requests with key k-ninety-one, one millisecond apart, on servers A, B and C. Each selects, each finds nothing, and three authorisations go out.",
 "C: Five minutes later a fourth request arrives with the same key and a different amount. Returning the stored answer would hide the client's bug. Executing it would charge again. Neither is right."])

S(dia(K(2, "the fix"), "Insert the key first, and let the constraint decide", "ch2-fix",
      extra=strip(("fixb", "Mechanism", "INSERT the key, unique per client, with a request hash, in the same transaction that creates the payment. The loser reads the row: in progress → 409; done → the stored response; different hash → 422."),
                  ("whyb", "Property", "S1, decided by the database's constraint: the one place every request passes."))), [
 "C: The fix: insert the key first, unique per client, with a hash of the request, in the same transaction that creates the payment. Only one insert can win. The others fail the constraint and read the row. If it says processing, they get a four-oh-nine, retry later. If it says done, they get the stored response. And if the hash differs, a four twenty-two: nothing executes."], cls="dia")

S(dia(K(2, "sequence"), "One wins; the others read", "seq-idem"), [
 "C: As a sequence. Request one and request two arrive two milliseconds apart. Request one's insert succeeds: processing, with payment p-seventy-seven thirty-one. Request two's insert hits the unique violation, highlighted, and reads the row: processing, hash h-one. So it gets four-oh-nine. Later the same request again finds done and the same hash, and gets the stored response. And the changed amount has a different hash: four twenty-two."], cls="dia")

S(plain(K(2, "the code"), "Insert or read, in twelve lines",
  '<pre class="code"><span class="kw">def</span> insert_or_get(client, key, req_hash, create):\n    <span class="kw">with</span> db.transaction():\n        <span class="kw">try</span>:\n            db.insert(<span class="kw">"idempotency"</span>, client, key, req_hash, status=<span class="kw">"processing"</span>)\n            <span class="kw">return</span> New(create())            <span class="cm"># the payment, same transaction</span>\n        <span class="kw">except</span> UniqueViolation:\n            row = db.get(<span class="kw">"idempotency"</span>, client, key)\n    <span class="kw">if</span> row.req_hash != req_hash: <span class="kw">return</span> Error(422, <span class="kw">"key reused"</span>)\n    <span class="kw">if</span> row.status == <span class="kw">"processing"</span>: <span class="kw">return</span> Error(409, <span class="kw">"in progress"</span>)\n    <span class="kw">return</span> Stored(row.response)</pre>' +
  strip(("whyb", "Why it works", "The result is returned, not re-executed. A changed request under an old key is a client bug, so it is reported, not hidden."), cols="one")), [
 "C: In code. Inside one transaction, try to insert the key as processing and create the payment. On a unique violation, read the row. A different hash is a reused key: four twenty-two. Processing: four-oh-nine. Otherwise return the stored response. The result is returned, never re-executed, and a changed request under an old key is reported, not hidden."])

qs("Interviewer · the second-level push", "“The server that won crashes after the processor approved, but before it wrote ‘done’.”", [
 "I: The server that won crashes after the processor approved, but before it wrote done.", "[pause: 2.0]"])

S(plain(K(2, "the second fix"), "A stuck “processing” row is just an unknown", '<div class="cards c2">'
  '<div class="cd grn"><h3>The rows say how far it got</h3><p>Key: processing, with the payment ID. Payment: AUTH_PENDING, with the attempt reference. That is exactly an unknown outcome.</p></div>'
  '<div class="cd grn"><h3>Sweep, then inquire</h3><p>A processing row older than a minute goes to recovery: challenge one\'s inquiry, by reference.</p></div></div>' +
  line("Retention: keys live seven days. The contract says a retry after that is a new payment.", "a")), [
 "C: Then the rows say exactly how far it got. The key says processing, with the payment I-D. The payment says auth pending, with the attempt's reference. That is an unknown outcome, and challenge one already handles it: a sweeper sends any processing row older than a minute to the inquiry.",
 "C: One more contract term: keys live seven days. A retry after that is a new payment, and the A-P-I documentation says so."])

say_slide("“The idempotency key is inserted first, with a unique constraint, in the same transaction that creates the payment. One request wins; the others get ‘in progress’ or the stored answer. A different body under the same key is a client bug, so I reject it instead of hiding it. And a crash in the middle is just an unknown outcome, which I already handle.”", [
 "V: If asked, I'd say: the idempotency key is inserted first, with a unique constraint, in the same transaction that creates the payment. One request wins; the others get in progress or the stored answer. A different body under the same key is a client bug, so I reject it instead of hiding it. And a crash in the middle is just an unknown outcome, which I already handle.", "[pause: 1.0]",
 "N: Inside the database it is now safe. What about everything outside it?"])

# ───────── Challenge 3 · crash between ledger and event ─────────
subchapter("7.3", "Challenge 3: A crash between the ledger and the event", ["N: Challenge three. The payment is committed, and the process dies before anyone is told."])
qs("Interviewer · challenge 3 of 8", "“Your service commits the payment, then crashes before telling the merchant. What state are you in?”", [
 "I: Your service commits the payment, then crashes before telling the merchant. What state are you in?", "[pause: 2.0]"])

S(dia(K(3, "two writes"), "Commit, then publish", "ch3-attack", q=True, red=True,
      extra=strip(("case", "Naive answer", "“We publish the event right after the commit. Crashes are rare.”"),
                  ("case", "Break", "Two writes to two systems with no shared transaction. Either order loses something."))), [
 "C: The naive answer: publish the event right after the commit, crashes are rare. Look at the red arrow from the service straight to the event log. That is a second write, to a second system, with no shared transaction. Whichever order you choose, a crash between them loses something."], cls="dia")

S(plain(K(3, "the trace"), "Charged, and nothing shipped", '<pre class="trace"><span class="t">11:20:00.010  </span>commit: p-8102 CAPTURED, entries written\n<span class="t">11:20:00.012  </span><span class="bad">process killed by a deploy</span>: no event\n<span class="t">11:20 onward  </span>merchant\'s order system waits; <span class="bad">nothing ships</span>\n<span class="t">reverse order </span>publish first, then the commit fails: <span class="bad">goods ship for an unpaid order</span></pre>', q=True, red=True), [
 "C: The trace. The capture commits. Two milliseconds later a deploy kills the process, and no event is sent. The merchant's order system waits, and nothing ships: the customer has paid for nothing. Reverse the order, publish first and then commit, and a failed commit ships goods for an unpaid order. Rare is not the same as never, at ten thousand a second."])

S(dia(K(3, "the fix"), "The event is a row in the same transaction", "ch3-fix",
      extra=strip(("fixb", "Mechanism", "Transactional outbox: the event row commits with the state and the entries. A relay reads committed rows in order and publishes them, at least once."),
                  ("whyb", "Property", "L3: the event exists if and only if the state committed, and delivery is retried until acknowledged."))), [
 "C: The fix is the outbox, now outlined green. The event is a row written in the same transaction as the state and the entries. A relay reads committed rows, in order, and publishes them to the log, at least once. From there the webhook sender takes over. The event exists if and only if the state committed, and delivery is retried until it is acknowledged."], cls="dia")

S(dia(K(3, "sequence"), "Nothing is lost at the crash", "seq-outbox"), [
 "C: As a sequence. One: begin, captured, entries, outbox row e-five-five-one, commit. The process is killed right there: nothing is lost, the row is committed. Two: the relay reads committed rows. Three: it publishes e-five-five-one. Four: the webhook goes to the merchant, signed and retried. If the merchant receives it twice, it has already seen that event I-D and ignores the second."], cls="dia")

qs("Interviewer · the second-level push", "“The relay is twenty minutes behind. Or a merchant's endpoint is down for a day.”", [
 "I: The relay is twenty minutes behind. Or a merchant's endpoint is down for a day.", "[pause: 2.0]"])

S(plain(K(3, "the second fix"), "Lag is a metric; the database is the backstop", '<div class="cards c2">'
  '<div class="cd grn"><h3>The relay</h3><p>Outbox age is a metric with an alert. The relay is partitioned by account, so one slow partition does not hold the rest.</p></div>'
  '<div class="cd grn"><h3>The merchant</h3><p>Webhooks retry with backoff for days. After that, the merchant is told to reconcile with GET. Their dashboard reads our database, not the stream.</p></div></div>'), [
 "C: Outbox age is a metric with an alert, so twenty minutes behind pages someone. The relay is partitioned by account, so one slow partition does not hold up the rest. And for the merchant who is down for a day: webhooks retry with backoff for days, then the merchant is told to reconcile with a get, and their dashboard reads our database, not the event stream."])

say_slide("“I never write to two systems and hope. The event is a row in the same transaction as the state change, and a relay publishes it at least once. Consumers de-duplicate by event ID, and the merchant can always ask us for the state directly.”", [
 "V: If asked, I'd say: I never write to two systems and hope. The event is a row in the same transaction as the state change, and a relay publishes it at least once. Consumers de-duplicate by event I-D, and the merchant can always ask us for the state directly.", "[pause: 1.0]",
 "N: One transaction per payment works. Until a thousand of them want the same row."])

# ───────── Challenge 4 · the hot merchant ─────────
subchapter("7.4", "Challenge 4: The hot merchant", ["N: Challenge four. One merchant receives five thousand payments a second, and they all touch one account."])
qs("Interviewer · challenge 4 of 8", "“One merchant receives five thousand payments a second. Where does that land?”", [
 "I: One merchant receives five thousand payments a second. Where does that land?", "[pause: 2.0]"])

S(dia(K(4, "one row"), "Five thousand writers, one lock", "ch4-attack", q=True, red=True,
      extra=strip(("case", "Naive answer", "“Update the merchant's balance in each payment's transaction.”"),
                  ("case", "Break", "Every transaction takes the same row lock; they serialise."))), [
 "C: The naive answer: update the merchant's balance inside each payment's transaction. Look at the database, dashed red. Every one of those transactions takes the same row lock, so they run one after another."], cls="dia")

S(plain(K(4, "the trace"), "A queue that grows by four thousand a second", '<pre class="trace"><span class="t">12:00:00  </span>merchant-42 at 5,000 payments / s\n<span class="t">12:00:00  </span>each holds balance(merchant-42) for ~1.5 ms → <span class="bad">≈ 670 / s</span>\n<span class="t">12:00:01  </span>queue + 4,330; that merchant\'s p99 <span class="bad">past 2 s</span>\n<span class="t">12:00:02  </span>its payments time out → <span class="bad">they become UNKNOWNs</span></pre>' +
  '<div class="hedge"><b class="t">Label the numbers</b>The lock time is illustrative and must be measured. The ratio is the point: five thousand against hundreds.</div>', q=True, red=True), [
 "C: The trace. Five thousand a second, each holding the balance row for about one and a half milliseconds: the row allows about six hundred and seventy a second. The queue grows by more than four thousand a second, the merchant's latency passes two seconds within a second, and its payments start timing out. They become unknowns: this challenge feeds challenge one.",
 "C: The lock time is illustrative and must be measured. The ratio is the point."])

S(dia(K(4, "the fix"), "Append entries; the balance is a projection", "ch4-fix",
      extra=strip(("fixb", "Mechanism", "Payments only insert their own entries: no shared row. A projection updates balances seconds behind. Where a check needs a current balance: 16 sub-accounts, summed, or one writer per merchant for that rare operation."),
                  ("whyb", "Property", "Throughput from removing the shared row from the hot path; correctness of the rare check from serialising only that check."))), [
 "C: The fix. Payments only insert their own entries, and nothing shared is updated, so there is no lock to queue on. A projection updates the balance a few seconds behind, which is fine for a dashboard. Where a check needs the balance right now, a payout must not exceed available funds, the green box: the account is split into sixteen sub-accounts that take writes in turn and are summed, or the rare payout goes through one writer per merchant."], cls="dia")

S(dia(K(4, "the arithmetic"), "Why sixteen", "hot", chip=chips("16 × 670 ≈ 10,700 / s", "illustrative")), [
 "C: Why sixteen. Each sub-account row allows about six hundred and seventy a second, so sixteen allow about ten thousand seven hundred: twice this merchant's peak. And with append-only entries there is no shared row at all on the payment path. The sub-accounts are only for the operations that must read a current balance."], cls="dia")

qs("Interviewer · the second-level push", "“A refund needs ‘refunded is at most captured’, per payment. A payout needs ‘paid out is at most available’, right now.”", [
 "I: A refund needs refunded to be at most captured, per payment. A payout needs paid out to be at most available, right now.", "[pause: 2.0]"])

S(plain(K(4, "the second fix, and the honest limit"), "Serialise only what must be serial", '<div class="cards c2">'
  '<div class="cd grn"><h3>Per payment: a conditional update</h3><p>One payment is never hot. <b>refunded + amount ≤ captured</b> in one statement on its row.</p></div>'
  '<div class="cd grn"><h3>Per merchant: one payout writer</h3><p>Reads the sum of the sub-accounts, then posts the payout transaction. Payouts are rare next to payments.</p></div></div>' +
  line("Honest limit: the projection lag must be measured and stated to the payouts team.", "r")), [
 "C: Per payment, the check is a conditional update on that payment's row, and one payment is never hot. Per merchant, the payout check goes through a single payout writer, which reads the sum of the sub-accounts and then posts the payout. Payouts are rare next to payments, so serialising them costs nothing.",
 "C: The honest limit: the projection lag must be measured and stated to the team that owns payouts."])

say_slide("“Five thousand updates a second to one balance row would serialise on its lock. So payments only append entries and the balance is derived. Where a check needs the balance now, like a payout, I split the account into sub-accounts or serialise just that rare operation through one writer.”", [
 "V: If asked, I'd say: five thousand updates a second to one balance row would serialise on its lock. So payments only append entries and the balance is derived. Where a check needs the balance now, like a payout, I split the account into sub-accounts or serialise just that rare operation through one writer.", "[pause: 1.0]",
 "N: The refund check just appeared. Let's push on it."])
