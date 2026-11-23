from dsl import *

# ───────────────────────── 6 · bridge ─────────────────────────
chapter(6, "Bridge", 4, "It works. Where does it break first?", [
 "V: It works. The question now is where it breaks first.", "[pause: 1.0]"])

S(dia("Challenge map", "Eight attack points on the same baseline", "map", chip=chips("each fix creates the next question")), [
 "C: The baseline with its attack points marked. The dispatcher and the rails, where a charge can time out, and where a whole morning has to fit under a contract. File ingest, where settled payments come back. The schedule service and the A-P-I, where refunds and payoffs change a live loan. Reconciliation, where the bank disagrees. Then the processor down on the busiest morning, and silence. Eight challenges, each fix creating the next question."], cls="dia")

chapter(7, "Challenges", 5, "Eight ways to break it, and what survives", [
 "C: Each challenge runs the same way: the question, the naive answer, a case with numbers, where it breaks, the fix and why it works. Then the interviewer pushes on the fix itself, and I say what I'd say in the room."])

K = lambda n, t: f"Challenge {n} of 8 · {t}"

# ───────── Challenge 1 · the processor timed out ─────────
subchapter("7.1", "Challenge 1: The processor timed out", ["N: Challenge one, the crux. A card charge times out, and the worker wants to retry."])
qs("Interviewer · challenge 1 of 8", "“The processor times out on a card charge. Your worker retries. Was the customer charged twice?”", [
 "I: The processor times out on a card charge. Your worker retries. Was the customer charged twice?", "[pause: 2.0]"])

S(dia(K(1, "the timeout"), "What does a timeout mean?", "ch1-attack", q=True, red=True,
      extra=strip(("case", "Naive answer", "“Mark it failed and retry.” The retry is a new attempt, with a new key."),
                  ("case", "Why it fails", "A timeout is not an answer. The first charge may have gone through. A new key lets the processor charge again."))), [
 "C: The naive answer: mark it failed and retry. Look at the red arrows between the dispatcher and the rails. A timeout is not an answer. The request may have arrived and been approved, and we simply never heard. If the retry goes out as a new attempt, with a new key, the processor has every reason to charge again."], cls="dia")

S(plain(K(1, "the trace"), "$300 for one $150 instalment", '<pre class="trace"><span class="t">08:00:00.000  </span>ln-5531 instalment 2, $150, key coll:ln-5531:2:1 sent\n<span class="t">08:00:03.200  </span>the processor approves it\n<span class="t">08:00:10.000  </span>worker timeout: no answer; naive design marks it <span class="bad">FAILED</span>\n<span class="t">08:00:12.000  </span>retry as attempt 2, key coll:ln-5531:2:2: approved\n<span class="t">08:00:12.000  </span><span class="bad">the customer has paid $300 for one $150 instalment</span></pre>' +
  '<div class="hedge"><b class="t">Label the numbers</b>Illustrative. The shape is real: an approval that lands after the caller gave up, and a retry that the processor cannot recognise.</div>', q=True, red=True), [
 "C: The trace. At eight, instalment two of loan fifty-five thirty-one, a hundred and fifty dollars, goes out with key attempt one. At three point two seconds the processor approves it. At ten seconds the worker gives up and the naive design marks it failed. At twelve seconds a retry goes out as attempt two, with a new key, and it is approved too. Three hundred dollars for a hundred and fifty dollar instalment.",
 "C: The numbers are illustrative, but approvals really do land after the caller has given up."])

S(dia(K(1, "the fix"), "Unknown is a state, and the resolver ends it", "ch1-fix",
      extra=strip(("fixb", "Mechanism", "Timeout → UNKNOWN. The resolver queries by the same key at 30 s, 2 min, 10 min. Only a definite decline allows attempt 2."), cols="one")), [
 "C: The fix. At the timeout the intent goes to unknown, not failed. Then the new green box: the resolver asks the processor about the same key, after thirty seconds, two minutes and ten minutes. And the rule: resending the same attempt reuses its key, so the processor returns the first result. Only a definite decline lets us open attempt two."], cls="dia")

S(dia(K(1, "sequence"), "The next ten minutes", "seq-unknown"), [
 "C: As a sequence. One: the charge with key attempt one. No answer at ten seconds. Two, highlighted: the intent goes to unknown. Three: the resolver queries by the same key, and four, the processor says approved at three point two seconds. The resolver posts it as settled, through the same ledger key, so it can only be posted once. In the note: if the processor says not found after its safe window, we resend, with the same key."], cls="dia")

S(plain(K(1, "the resolver"), "End every unknown by asking",
  '<pre class="code" data-lang="pseudocode"><span class="kw">def</span> resolve(i):            <span class="cm"># +30 s, +2 min, +10 min</span>\n  r = rail.query(key=i.key)\n  <span class="kw">if</span> r == "approved":\n    <span class="kw">return</span> ledger.post(i, r, key=i.key)  <span class="cm"># idempotent</span>\n  <span class="kw">if</span> r == "declined":\n    <span class="kw">return</span> db.set(i, "DECLINED")    <span class="cm"># attempt 2 allowed</span>\n  <span class="kw">if</span> r == "not_found" and i.age &gt; rail.safe_window:\n    <span class="kw">return</span> rail.charge(i.token, i.amount, key=i.key)\n                                    <span class="cm"># the SAME key</span>\n  schedule_again(i)                 <span class="cm"># still unknown</span></pre>' +
  strip(("whyb", "Why it works", "No path creates a second decision for one attempt. Even a wrong guess resends the same key, which the processor de-duplicates."), cols="one")), [
 "C: The resolver in code. Query by key. Approved: post it, idempotently. Declined: mark it declined, and now a second attempt is allowed. Not found, and older than the processor's safe window: send again, still with the same key. Anything else: ask again later. No path creates a second decision for one attempt, and even a wrong guess resends a key the processor will de-duplicate."])

qs("Interviewer · the second-level push", "“The query says ‘not found’. You resend. Tomorrow's settlement file shows the first charge went through after all.”", [
 "I: The query says not found. You resend. Tomorrow's settlement file shows the first charge went through after all.", "[pause: 2.0]"])

S(plain(K(1, "the second fix, and the honest limit"), "The file is the final arbiter", '<div class="cards c2">'
  '<div class="cd grn"><h3>Same key, so usually no harm</h3><p>A processor that honours keys returns the first result. Not found is only final after its documented window.</p></div>'
  '<div class="cd red"><h3>If it still happened</h3><p>Reconciliation finds two settled charges for one instalment. The duplicate is refunded automatically the same day, and counted as an incident.</p></div></div>' +
  line("Honest limit: a processor that neither honours keys nor answers queries can only be checked by its file, a day late. That is a reason to choose processors.", "r")), [
 "C: With the same key, a processor that honours keys returns the first result, so usually there is no harm. And not found should only count as final after the processor's documented window. If it still happened, reconciliation finds two settled charges for one instalment the next morning, refunds the duplicate automatically, and counts it as an incident.",
 "C: The honest limit: a processor that neither honours keys nor answers queries can only be checked by its file, a day late. That is a reason to choose processors, and I'd say so to whoever negotiates the contract."])

say_slide("“A timeout is not a failure. The intent goes to unknown, the resolver queries by the same key, and a resend of the same attempt reuses that key. The settlement file is the final arbiter.”", [
 "V: If asked, I'd say: a timeout is not a failure. The intent goes to unknown, the resolver queries by the same key, and a resend reuses that key. The settlement file is the final arbiter.", "[pause: 1.0]",
 "N: Next: there are six hundred thousand of these on one morning."])

# ───────── Challenge 2 · the morning of the 1st ─────────
subchapter("7.2", "Challenge 2: The morning of the 1st", ["N: Challenge two. Six hundred thousand payments due on one day: where is the real limit?"])
qs("Interviewer · challenge 2 of 8", "“Six hundred thousand payments are due on the first. Walk me through that morning.”", [
 "I: Six hundred thousand payments are due on the first. Walk me through that morning.", "[pause: 2.0]"])

S(dia(K(2, "the herd"), "Where is the limit?", "ch2-attack", q=True, red=True,
      extra=strip(("case", "Naive answer", "“A cron job at midnight.” Or: “It's a thundering herd, so put a message broker in front.”"),
                  ("case", "Break", "Forty-two a second never hurt the database. The burst hits the processor's contract and the bank's cut-off."))), [
 "C: Two naive answers. A cron job at midnight, or, it's a thundering herd, so put a message broker in front. Look where the red is: the schedule service and the dispatcher, and the arrow to the rails. Forty-two a second never hurt the database. The burst hits the processor's contract, and a file that has to reach the bank by two."], cls="dia")

S(plain(K(2, "the trace"), "A busy night, and a missed cut-off", '<pre class="trace"><span class="t">00:00:00  </span>workers send 2,000 card charges a second; the contract is 100\n<span class="t">00:00:03  </span>the processor throttles: <span class="bad">95 % rejected</span>; workers retry at once\n<span class="t">00:20:00  </span><span class="bad">18,000 card charges marked failed</span>; late fees due tomorrow\n<span class="t">13:55:00  </span>the debit file is built; validation fails on one bad record\n<span class="t">14:00:00  </span><span class="bad">cut-off missed: 480,000 collections slip a day</span></pre>', q=True, red=True), [
 "C: The trace. At midnight, two thousand card charges a second against a contract of a hundred. Three seconds in, the processor throttles ninety-five percent, and the workers retry at once, which makes it worse. Twenty minutes later, eighteen thousand charges are marked failed, and late fees are due tomorrow, for a failure that was ours.",
 "C: And the debit file, built at five to two, fails validation on one bad record. The cut-off passes. Four hundred and eighty thousand collections slip a day."])

S(dia(K(2, "the fix"), "Plan the day backwards from the cut-off", "ch2-fix",
      extra=strip(("fixb", "Mechanism", "A day plan from the cut-off: debit file submitted 10:30, acknowledged by 11:00. Cards from 06:00 at 90 a second."), cols="one")), [
 "C: The fix: plan the day backwards from the cut-off. The new green box, the day plan, hands each rail its budget. The debit file is built at nine, validated, submitted by half past ten, and acknowledged by eleven, three hours before the cut-off, so a rejected file can be fixed and resent. The card window opens at six, at ninety a second."], cls="dia")

S(dia(K(2, "the day"), "The 1st, on one line", "dayplan"), [
 "C: The day on one line. Card charges from six, a hundred and twenty thousand in twenty-two minutes. Soft declines retried around seven. The debit file built from nine and submitted by half past ten. The bank's acknowledgement by eleven. And the red line at two, with three hours of margin in front of it."], cls="dia")

S(plain(K(2, "the claim"), "Workers never collide",
  '<pre class="code" data-lang="sql"><span class="kw">WITH</span> due <span class="kw">AS</span> (\n  <span class="kw">SELECT</span> id <span class="kw">FROM</span> due_item\n   <span class="kw">WHERE</span> due_date = current_date\n     <span class="kw">AND</span> status = <span class="st">\'DUE\'</span> <span class="kw">AND</span> shard = $1\n   <span class="kw">ORDER BY</span> id <span class="kw">LIMIT</span> 500\n   <span class="kw">FOR UPDATE SKIP LOCKED</span>)\n<span class="kw">UPDATE</span> due_item d\n   <span class="kw">SET</span> status = <span class="st">\'CLAIMED\'</span>, claimed_by = $2,\n       claimed_at = now()\n  <span class="kw">FROM</span> due <span class="kw">WHERE</span> d.id = due.id\n<span class="kw">RETURNING</span> d.id, d.loan_id, d.amount_cents, d.rail;\n<span class="cm">-- same commit: one intent + one outbox row each</span></pre>'), [
 "C: The claim in code. Select up to five hundred due rows in one shard, lock them, and skip rows another worker has locked. Mark them claimed in the same statement, and in the same transaction open the intents and outbox rows. A worker that dies before the commit releases its locks. One that dies after is found by the sweeper, which returns claims with no intent. No distributed lock, and no broker."])

S(dia(K(2, "sequence"), "Two workers, one shard", "seq-claim"), [
 "C: As a sequence. Worker one claims five hundred rows in shard seven. Worker two asks for the same shard and skips the locked rows. Three, highlighted: per row, an intent and an outbox row, and commit. If worker two dies before its commit, its rows are due again. Four: the dispatcher drains the outbox, cards at ninety a second, debits into the nine o'clock file."], cls="dia")

qs("Interviewer · the second-level push", "“At ten past six, the processor lowers your limit to fifty a second.”", [
 "I: At ten past six, the processor lowers your limit to fifty a second.", "[pause: 2.0]"])

S(plain(K(2, "the second fix"), "A live budget, and fewer peaks at the source", '<div class="cards c2">'
  '<div class="cd grn"><h3>The bucket listens</h3><p>Throttle responses halve the rate at once. By 06:10, 54,000 are done; the other 66,000 at 50 a second take 22 min: done by 06:32.</p></div>'
  '<div class="cd grn"><h3>Spread due dates</h3><p>Let the customer pick a day, default to the booking day. The peak shrinks at origination, not in the dispatcher.</p></div></div>'), [
 "C: The bucket's rate is live: a throttle response halves it at once. By ten past six, fifty-four thousand are done, and the other sixty-six thousand at fifty a second take twenty-two minutes. Done by six thirty-two, still hours before anything matters.",
 "C: And the better fix is upstream: spread due dates when loans are created. Let the customer choose a day, and default to the day of booking. The peak shrinks at the source."])

say_slide("“Forty-two a second is nothing for a database. The limits are the processor's contract and the bank's cut-off, so I plan the day backwards from the cut-off and run a token bucket per rail below the contract.”", [
 "V: If asked, I'd say: forty-two a second is nothing for a database. The limits are the processor's contract and the bank's cut-off, so I plan backwards from the cut-off, with a budget per rail.", "[pause: 1.0]",
 "N: The debits go out on time. A few days later, some come back."])

# ───────── Challenge 3 · settled, then returned ─────────
subchapter("7.3", "Challenge 3: It settled, then it came back", ["N: Challenge three, the second half of the crux. A debit that settled comes back."])
qs("Interviewer · challenge 3 of 8", "“A bank debit settled on the second. On the third it comes back for insufficient funds. Another one comes back forty days later as unauthorised.”", [
 "I: A bank debit settled on the second. On the third it comes back for insufficient funds. Another one comes back forty days later, as unauthorised.", "[pause: 2.0]"])

S(dia(K(3, "the return"), "Settled was not the end", "ch3-attack", q=True, red=True,
      extra=strip(("case", "Naive answer", "“Settled means paid: close the instalment.” Then: “Retry anything that fails.”"),
                  ("case", "Break", "The return has no state to land in, the balance was already reduced, and an automatic retry of an unauthorised debit breaks the network's rules."))), [
 "C: The naive answer: settled means paid, close the instalment, and retry anything that fails. Look at file ingest. The return has no state to land in, the balance was already reduced, and automatically retrying an unauthorised debit breaks the bank network's rules."], cls="dia")

S(plain(K(3, "the trace"), "Two returns, two different rules", '<pre class="trace"><span class="t">Dec 1   </span>ln-7702 instalment 3, $150, in the debit file\n<span class="t">Dec 2   </span>settled; naive design closes the instalment\n<span class="t">Dec 3   </span>return R01, insufficient funds: <span class="bad">no state for it; balance already reduced</span>\n<span class="t">Dec 2   </span>ln-4410 instalment 2, $150, settled\n<span class="t">Jan 11  </span>return R10, unauthorised, day 40; naive retry: <span class="bad">a rule breach, and a complaint</span></pre>', q=True, red=True), [
 "C: The trace. On the first, instalment three of loan seventy-seven oh two goes in the debit file. On the second it settles, and the naive design closes the instalment. On the third, a return with code R-zero-one, insufficient funds. There is no state for it, and the balance was already reduced.",
 "C: Another loan's debit settled on the second. On the eleventh of January, day forty, it returns as R-ten, unauthorised: the customer says they never agreed to it. The naive design retries it automatically. That breaks the rules, and turns a dispute into a complaint."])

S(dia(K(3, "the fix"), "RETURNED is a state, and a reversal is a transaction", "ch3-fix",
      extra=strip(("fixb", "Mechanism", "SETTLED → RETURNED; a reversal dated the day it arrives; PAID → DUE. Policy decides any retry."), cols="one")), [
 "C: The fix. Settled moves to returned, a normal state. File ingest posts a reversing transaction, dated the day the return arrived, never editing the original. The instalment goes from paid back to due, with the reason. Then policy decides: insufficient funds may be presented again at most twice, typically timed after payday. Unauthorised is never retried: the customer is contacted, and a new authorisation is needed."], cls="dia")

S(dia(K(3, "sequence"), "One return, end to end", "seq-return"), [
 "C: As a sequence. One: the bank's return file, loan seventy-seven oh two, a hundred and fifty, code R-zero-one. Two, highlighted: ingest matches it to the attempt by the trace number, and moves settled to returned. Three: the reversing transaction dated the third, and the instalment back to due. Four: policy says re-present, attempt two of at most three, after payday. Five: a notice to the customer. And in red: an R-ten on day forty is never re-presented."], cls="dia")

S(plain(K(3, "the rules"), "Return codes are policy, owned outside engineering", table(["Code", "Means", "Window", "Policy"], [
  ["R01", "insufficient funds", "2 banking days", "re-present at most twice, within 180 days; after payday"],
  ["R02, R03", "account closed, not found", "2 banking days", "stop; ask for a new method"],
  ["R10 and similar", "unauthorised", "up to 60 days", "never retry; new authorisation; dispute review"],
  ["late fee", "after the grace period", "—", "capped by law where the customer lives; never for our failures"]], "bt xs") +
  strip(("whyb", "Why it works", "Engineering owns the mechanism; risk and legal own the table. A rule change is a new policy version, not a deploy."), cols="one")), [
 "C: The rules as a table, because they are data. Insufficient funds: back within two banking days, and may be presented again at most twice within a hundred and eighty days. Account closed or not found: stop, and ask for a new payment method. Unauthorised: up to sixty days, never retried. And late fees, which are capped by law where the customer lives, and never charged for our own failures. Engineering owns the mechanism. Risk and legal own this table."])

S(plain(K(3, "the card rail"), "The card version of “it came back”: a dispute", table(["Step", "What we write", "Why"], [
  ["Notice", "payment SETTLED → DISPUTED; the processor nets it from our payout", "the money already left; months after the charge"],
  ["Ledger", "a reversal dated today: receivable up, processor clearing down", "nothing edited; the instalment is due again"],
  ["Customer", "no late fee and no automatic re-collection while disputed", "a disputed amount is not a missed payment"],
  ["Evidence", "agreement, schedule, authorisation, receipt, by the network's deadline", "win: re-post; lose: stays due, normal collections"],
  ["Reconcile", "the payout's dispute line matched by dispute ID", "otherwise it is challenge six's break"]], "bt xs") +
  line("Illustrative: 0.1 % of the 1st's 120,000 card charges is about 120 disputes from one day.", "g")), [
 "C: The card rail has its own version of it came back: a dispute. Same mechanism, different clock.",
 "[+]", "C: The notice arrives, sometimes months after the charge, and the processor has already netted the money from our payout. The payment moves from settled to disputed.",
 "[+]", "C: The ledger gets a reversal dated today: the loan receivable goes back up, processor clearing goes down. Nothing is edited, and the instalment is due again.",
 "[+]", "C: The customer gets no late fee and no automatic re-collection on that instalment while it is disputed. A disputed amount is not a missed payment.",
 "[+]", "C: We send evidence by the network's deadline: the agreement, the schedule, the authorisation, the receipt. If we win, we re-post. If we lose, the instalment stays due and follows normal collections.",
 "[+]", "C: And reconciliation matches the payout's dispute line by dispute I-D, or it becomes the break in challenge six.",
 "[+]", "C: The scale, illustrative: one in a thousand of the hundred and twenty thousand card charges on the first is about a hundred and twenty disputes from that one day."])

qs("Interviewer · the second-level push", "“Finance wants to recognise the cash on settlement day. Risk wants to wait sixty days. Who wins?”", [
 "I: Finance wants to recognise the cash on settlement day. Risk wants to wait sixty days. Who wins?", "[pause: 2.0]"])

S(plain(K(3, "the second fix"), "Both, with the exposure on a report", '<div class="cards c2">'
  '<div class="cd grn"><h3>Post at settlement</h3><p>Cash is cash when the bank says so. A return is a later reversal, in the month it arrives.</p></div>'
  '<div class="cd amb"><h3>Report the exposure</h3><p>Settled in the last 60 days, by age, against the observed return rate. Risk prices it; nobody waits on it.</p></div></div>'), [
 "C: Both, with the exposure on a report. Cash is posted at settlement, because that is when the bank says it is cash, and a return is a later reversal, in the month it arrives. And a daily report shows everything settled in the last sixty days, by age, against the observed return rate. Risk prices that exposure. Nobody's process waits on it."])

say_slide("“Settled is not final for a bank debit. A return is a state and a reversing transaction dated when it arrives; the instalment goes back to due, and whether we retry is policy: never for unauthorised.”", [
 "V: If asked, I'd say: settled is not final for a bank debit. A return is a state and a reversal dated when it arrives, and whether we retry is policy: never for unauthorised.", "[pause: 1.0]",
 "N: Returns move money backwards. So do refunds, but they also change the schedule."])

# ───────── Challenge 4 · a refund mid-loan ─────────
subchapter("7.4", "Challenge 4: A refund in the middle of the loan", ["N: Challenge four. A merchant refunds part of a purchase two payments in."])
qs("Interviewer · challenge 4 of 8", "“After two instalments, the merchant refunds three hundred dollars of the twelve hundred. What changes?”", [
 "I: After two instalments, the merchant refunds three hundred dollars of the twelve hundred. What changes?", "[pause: 2.0]"])

S(dia(K(4, "the refund"), "Where does three hundred dollars go?", "ch4-attack", q=True, red=True,
      extra=strip(("case", "Naive answer", "“Subtract three hundred from the balance.”"),
                  ("case", "Break", "The schedule still says six more payments of $150. The customer pays $900 on a $600 debt."))), [
 "C: The naive answer: subtract three hundred from the balance. Look at the schedule service. The balance changed, but the schedule still says six more payments of a hundred and fifty. The customer would pay nine hundred dollars on a six-hundred dollar debt."], cls="dia")

S(plain(K(4, "the trace"), "Three hundred dollars over-collected", '<pre class="trace"><span class="t">Oct 1   </span>ln-9100 booked: $1,200 in 8 × $150\n<span class="t">Nov 1   </span>instalment 2 paid; $900 outstanding\n<span class="t">Nov 14  </span>merchant refunds $300: balance column → $600\n<span class="t">Dec–May </span>schedule untouched: 6 × $150 = $900 collected\n<span class="t">May 1   </span><span class="bad">customer overpaid $300; noticed by the customer, not by us</span></pre>', q=True, red=True), [
 "C: The trace. Loan ninety-one hundred is booked in October: twelve hundred dollars in eight payments of a hundred and fifty. Two are paid by November: nine hundred outstanding. On the fourteenth the merchant refunds three hundred, and the balance column drops to six hundred. But the schedule is untouched, and from December to May it collects six times a hundred and fifty: nine hundred dollars. The customer overpaid three hundred, and the customer noticed before we did."])

S(dia(K(4, "the fix"), "A refund is a transaction and a new schedule version", "ch4-fix",
      extra=strip(("fixb", "Mechanism", "A transaction keyed by the refund ID, and a new schedule version: re-amortise (6 × $100) or shorten (4 × $150)."), cols="one")), [
 "C: The fix. In the ledger, the merchant now owes us three hundred, and the loan's principal drops by three hundred, keyed by the merchant's refund I-D. Then policy, the green box, applies the terms. Re-amortise: the six remaining payments become a hundred each. Or shorten: they stay at a hundred and fifty, and the loan ends after four. Which one is a product and legal decision, written in the terms before any code."], cls="dia")

S(plain(K(4, "allocation"), "Where each payment goes, in order", table(["Order", "Bucket", "Why"], [
  ["1", "fees due", "usually first, but rules differ by state"],
  ["2", "interest due", "accrued daily, by calculation"],
  ["3", "principal due", "this instalment's share"],
  ["4", "future principal", "extra or early: shortens the loan"]], "bt") +
  strip(("whyb", "Why it works", "One versioned rule, applied by one piece of code, recorded on every posting: the ledger can always say why each cent went where it did."), cols="one")), [
 "C: Every payment is also allocated, in an order policy sets. Typically fees due, then interest due, then this instalment's principal, and anything extra reduces future principal. It is one versioned rule, applied by one piece of code, and every posting records the version. So the ledger can always say why each cent went where it did."])

S(dia(K(4, "sequence"), "The refund, as a sequence", "seq-refund"), [
 "C: As a sequence. One: the merchant refunds three hundred on loan ninety-one hundred, with its refund I-D. Two: the terms, version three, say re-amortise. Three, highlighted: the ledger transaction, keyed by that I-D, so a merchant retry posts nothing new. Four: schedule version two, six payments of a hundred, from instalment three. And the note: if instalment three is already in flight, it stays in flight, and allocation sorts it out when it settles."], cls="dia")

qs("Interviewer · the second-level push", "“The customer has paid nine hundred. Now the merchant refunds the full twelve hundred.”", [
 "I: The customer has paid nine hundred. Now the merchant refunds the full twelve hundred.", "[pause: 2.0]"])

S(plain(K(4, "the second fix"), "An overpayment is money we owe", '<div class="cards c2">'
  '<div class="cd grn"><h3>Principal to zero, the rest to the customer</h3><p>$900 moves to customer payable, refunded to the original method within the days policy sets. Never held silently as credit.</p></div>'
  '<div class="cd amb"><h3>The merchant side</h3><p>The merchant owes $1,200 back; whether the $36 discount fee is returned is the merchant contract, also versioned.</p></div></div>'), [
 "C: Then the loan's principal goes to zero, and the nine hundred the customer paid becomes money we owe them, in a customer payable account. It is refunded to the original payment method within the days policy sets, and never held silently as credit. On the merchant side, they owe us the twelve hundred back, and whether we return the thirty-six dollar discount fee is the merchant contract, also versioned."])

say_slide("“A refund is a ledger transaction and a new schedule version. Whether it re-amortises or shortens the loan is a decision in the terms, and any overpayment goes back to the customer.”", [
 "V: If asked, I'd say: a refund is a ledger transaction and a new schedule version. Re-amortise or shorten is a decision in the terms, and any overpayment goes back to the customer.", "[pause: 1.0]",
 "N: That one changed the future. The next one changes the loan while money is still moving."])
