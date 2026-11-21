from dsl import *

# ───────────────────────── 6 · bridge ─────────────────────────
chapter(6, "Bridge", 4, "It works. Where does it break first?", [
 "V: It works. Where does it break first?", "[pause: 1.0]"])

S(dia("Challenge map", "Eight attack points on the same baseline", "map", chip=chips("each fix creates the next question")), [
 "C: The baseline with eight attack points. The credit vendors: first slow, then down for everyone. The application service and its database: a phone that drops between accept and the answer. Funding: a transfer that fails after booking. The policy engine: a decision nobody can explain, then a new model. The vault: where identity lives. And the orchestrator: how we would know any of it is broken. I'll take them in an order where each fix creates the next question."], cls="dia")

chapter(7, "Challenges", 5, "Eight ways to break it, and what survives", [
 "C: Eight challenges, each the same way: the question, the naive answer, a case with numbers, where it breaks, the fix, why it works, the push on the fix itself, and what I'd say in the room."])

K = lambda n, t: f"Challenge {n} of 8 · {t}"

# ───────── Challenge 1 · the bureau is slow ─────────
subchapter("7.1", "Challenge 1: The bureau is slow", ["N: Challenge one. One bureau call in ten takes four seconds: what does the customer at the counter see, and what does it cost?"])
qs("Interviewer · challenge 1 of 8", "“One bureau call in ten takes four seconds today. What does the customer at the counter see?”", [
 "I: One bureau call in ten takes four seconds today. What does the customer at the counter see?", "[pause: 2.0]"])

S(dia(K(1, "the bureau is slow"), "Wait, or race a second bureau?", "ch1-attack", q=True, red=True,
      extra=strip(("case", "Naive answer", "“Wait for it; if it's slow, send the same request to the second bureau and take whichever answers first.”"),
                  ("case", "Break", "The calls to the vendors: waiting misses 3 s; racing pays twice."))), [
 "C: The naive answer: wait, and if the bureau is slow, send the same request to the second bureau and take whichever answers first. That's a hedged request, and for an internal read it's a fine idea. Here, look at the red vendors box. Waiting misses the promise. Racing pays twice."], cls="dia")

S(plain(K(1, "the trace"), "Two pulls, two inquiries, or a lost promise", '<pre class="trace"><span class="t">10:00:00.000</span>submit from the phone\n<span class="t">.050</span>identity, fraud and bureau A called\n<span class="t">.400</span>identity and fraud are back\n<span class="t">01.000</span>hedge: the same pull sent to bureau B\n<span class="t">01.700</span>bureau B answers; offers at about 2.0 s\n<span class="t">04.100</span>bureau A answers: <span class="bad">a second paid pull, a second inquiry on the file</span>\n<span class="t">no hedge</span><span class="bad">offers at about 4.4 s: past the 3 s promise</span></pre>' +
  '<div class="hedge"><b class="t">Label the numbers</b>Illustrative: about $1 a pull, one slow call in ten. The shape is the point.</div>', q=True, red=True), [
 "C: The trace. Submit at ten o'clock. At fifty milliseconds, identity, fraud and bureau A go out. Identity and fraud are back by four tenths. At one second, the hedge sends the same pull to bureau B, which answers at one point seven, so offers appear at about two seconds. Good, until bureau A answers at four point one: a second paid pull, and a second inquiry on the customer's credit file.",
 "C: Without the hedge, the offers appear at about four point four seconds, past the three-second promise. So both answers are wrong, and they are wrong in different currencies: time, and money."])

S(dia(K(1, "the fix"), "The orchestrator owns time", "ch1-fix",
      extra=strip(("fixb", "Mechanism", "All calls at once; decide at a 2.0 s deadline with what has arrived. A breaker per vendor. Bureau B only after an error or an open breaker, never as a race."),
                  ("whyb", "Property", "L1: the wait is bounded by the deadline, not the slowest vendor. S4: a second pull only when the first has failed, not when it is slow."))), [
 "C: The fix lives in the orchestrator, outlined green. All required calls go out at once, and it decides at a two-second deadline with what has arrived. If everything arrives earlier, it decides earlier. A circuit breaker per vendor stops calling a vendor that is failing for everyone, so nobody waits on a known outage.",
 "C: And the second bureau is called only after an error or an open breaker, never as a race against a slow but healthy first call. L-one is bounded by the deadline. S-four holds, because a second pull happens only when the first has failed."], cls="dia")

S(dia(K(1, "sequence"), "The late answer is kept, not thrown away", "seq-ch1-gather"), [
 "C: As a sequence. Check and pull go out at time zero. Identity is back at four tenths. At two seconds, the deadline: bureau A is silent and its breaker is still closed, so this is one slow call, not an outage. The orchestrator decides with what arrived, through the missing-data policy, and does not race bureau B. Bureau A's report lands at four point one, and it is recorded."], cls="dia")

S(plain(K(1, "the gather, as code"), "One deadline; late calls are recorded, not cancelled",
  '<pre class="code" data-lang="python"><span class="kw">async def</span> decide(app, deadline_s=2.0):\n    calls = {v: create_task(adapter[v].call(app)) <span class="kw">for</span> v <span class="kw">in</span> required(app)}\n    done, pending = <span class="kw">await</span> wait(calls.values(), timeout=deadline_s)\n    <span class="kw">for</span> t <span class="kw">in</span> pending:\n        t.add_done_callback(record_late_answer)   <span class="cm"># paid for: keep it</span>\n    got = {v: t.result() <span class="kw">for</span> v, t <span class="kw">in</span> calls.items() <span class="kw">if</span> t <span class="kw">in</span> done}\n    missing = [v <span class="kw">for</span> v <span class="kw">in</span> calls <span class="kw">if</span> v <span class="kw">not in</span> got]\n    <span class="kw">return</span> policy.decide(features(app, got), missing)  <span class="cm"># the table decides</span></pre>' +
  strip(("whyb", "Why it works", "The deadline is one point in time for the whole decision. The code never decides what missing means: it hands the list to the signed policy."), cols="one")), [
 "C: In code. Start a task per required vendor. Wait for all of them, with one timeout. Anything still pending is not cancelled: a callback records its answer when it lands, because it was billed anyway. Then the code hands the features and the list of what is missing to the policy. The code never decides what missing means. The signed policy does."])

qs("Interviewer · the second-level push", "“The bureau's answer arrives at 4.1 seconds, after you decided. You paid for it. What do you do with it?”", [
 "I: The bureau's answer arrives at four point one seconds, after you decided. You paid for it. What do you do with it?", "[pause: 2.0]"])

S(plain(K(1, "the second fix, and the honest limit"), "Record it, use it, never rewrite the past", '<div class="cards c3">'
  '<div class="cd grn"><h3>Record it</h3><p>The call happened and was billed: a row in vendor_call, with its cost.</p></div>'
  '<div class="cd"><h3>Use it</h3><p>A referred application is finished with it: the customer gets a text with offers.</p></div>'
  '<div class="cd amb"><h3>Never rewrite</h3><p>An offer already shown stays as shown. Keep the report for reuse where the contract allows.</p></div></div>' +
  line("Honest limit: a deadline means about 3 % of applications reach the missing-data path every day. That is the next question.", "r")), [
 "C: Three things. Record it: the call happened and was billed, so it's a row with its cost. Use it: if the application was referred because the bureau was missing, the late answer finishes it, and the customer gets a text with offers. And never rewrite the past: an offer already shown stays as shown, because the decision record says what we knew at the time. Where the contract allows, the report is kept for a re-application.",
 "C: The honest limit: a deadline means about three percent of applications reach the missing-data path every day. Which is the next question."])

say_slide("“All vendors at once, one deadline, a breaker per vendor. I never race two bureaus: each pull is paid and may show on the customer's file. A late answer is recorded and finishes a refer.”", [
 "V: If asked, I'd say: all vendors at once, one deadline, a breaker per vendor. I never race two bureaus, because each pull is paid. A late answer is recorded and finishes a refer.", "[pause: 1.0]",
 "N: That fix creates the next question: what if the bureau is missing for everyone?"])

# ───────── Challenge 2 · the bureau is down ─────────
subchapter("7.2", "Challenge 2: The bureau is down for everyone", ["N: Challenge two. Bureau A is down for twenty minutes at the Saturday peak: who decides what happens at the counter, and how much can it cost?"])
qs("Interviewer · challenge 2 of 8", "“Bureau A is down for everyone for twenty minutes on a Saturday. What happens at the counter?”", [
 "I: Bureau A is down for everyone for twenty minutes on a Saturday. What happens at the counter?", "[pause: 2.0]"])

S(dia(K(2, "the bureau is down"), "Approve everyone, or decline everyone?", "ch2-attack", q=True, red=True,
      extra=strip(("case", "Naive answer", "“Approve with whatever data we have.” Or: “decline until it's back.”"),
                  ("case", "Break", "The vendors are gone, and the policy engine has no rule for it: a catch block decides credit risk."))), [
 "C: Two naive answers, and they're opposites. Approve with whatever data we have, or decline until it's back. Both are credit-risk decisions made by an engineer in a catch block. The red boxes: the vendor is gone, and the policy engine has no rule for it."], cls="dia")

S(plain(K(2, "the trace"), "Twenty minutes at eight a second", '<pre class="trace"><span class="t">Sat 11:00</span>bureau A starts timing out for everyone\n<span class="t">11:00–11:20</span>8 applications a second × 1,200 s = 9,600 applications\n<span class="t">approve all</span><span class="bad">9,600 × $1,200 ≈ $11.5M offered with no credit file</span>\n<span class="t">decline all</span><span class="bad">9,600 × 60 % × 70 % ≈ 4,000 lost loans</span>\n<span class="t">and</span><span class="bad">9,600 notices whose real reason is “our vendor was down”</span></pre>' +
  '<div class="hedge"><b class="t">Label the numbers</b>Derived from the given peak; approval and take-up are illustrative.</div>', q=True, red=True), [
 "C: The trace. Eleven o'clock on Saturday, bureau A starts timing out for everyone. Twenty minutes at eight a second is nine thousand six hundred applications. Approve them all, and we offer about eleven and a half million dollars of credit nobody scored.",
 "C: Decline them all, and we lose about four thousand loans, and we owe nine thousand six hundred decline notices whose only true reason is that our vendor was down. That is not a reason about the applicant."])

S(dia(K(2, "the fix"), "A signed table, inside the credit policy", "ch2-fix",
      extra=strip(("fixb", "Mechanism", "The missing-data policy table: versioned with the credit policy, signed by credit risk, approved by the partner bank. A counter, a cap and a dashboard per row."),
                  ("whyb", "Property", "S2: nobody is declined for our outage. L1: everyone gets an answer. Exposure bounded by arithmetic: the cap is the worst case."))), [
 "C: The fix is in the policy engine, outlined green. A missing-data table, versioned with the credit policy, signed by credit risk and approved by the partner bank. Engineering builds the mechanism, with a counter, a cap and a dashboard per row. Credit risk owns the numbers in it."], cls="dia")

S(dia(K(2, "the table"), "Four answers, in order", "policy"), [
 "C: Four rows, in order. One, the second bureau, after the first one's breaker has opened. Not a race: the first is known to be failing. Two, decide without a bureau, only for returning customers in good standing, at most five hundred dollars, under a daily cap of two hundred and fifty thousand. At most five hundred such loans a day.",
 "C: Three, refer: we'll finish in about two minutes by text, and the merchant sees pending, not declined. Four, decline, but only with a reason about the applicant. Everyone gets an answer, nobody is declined for our outage, and the worst case is the cap."], cls="dia")

S(dia(K(2, "sequence"), "A refer, finished by text", "seq-ch2-refer"), [
 "C: A refer as a sequence. Bureau A's breaker is open, and bureau B's bucket is empty this second. The customer is told: referred, we'll finish in two minutes by text. The application waits in the refer queue, oldest first. When a token frees up, bureau B is pulled, the report arrives, and the customer gets a text: your offers are ready."], cls="dia")

qs("Interviewer · the second-level push", "“Bureau B's contract allows five calls a second. You're sending eight.”", [
 "I: Bureau B's contract allows five calls a second. You're sending eight.", "[pause: 2.0]"])

S(plain(K(2, "the second fix, and the honest limit"), "A bucket per vendor; a cap per merchant", '<div class="cards c3">'
  '<div class="cd grn"><h3>Token bucket</h3><p>Five tokens a second for bureau B. A call without a token is not sent: refer. About 3 a second overflow: ≈ 3,600 referred in 20 minutes.</p></div>'
  '<div class="cd"><h3>Drain in order</h3><p>Oldest first, when a token frees up or A\'s breaker half-opens, inside the 10-minute promise.</p></div>'
  '<div class="cd amb"><h3>Cap per merchant</h3><p>Row 2\'s daily cap is split, so one busy merchant cannot spend it in an hour.</p></div></div>' +
  line("Honest limit: referred customers walk away. Measure refer completion and lost sales per minute of outage, and give them to credit risk.", "r")), [
 "C: A token bucket per vendor at the contract rate: five tokens a second for bureau B. A call without a token is not sent; that application is referred. Three a second over the limit for twenty minutes is about three thousand six hundred referred. The queue drains oldest first, when tokens free up or bureau A's breaker half-opens, inside the ten-minute promise. And the cap for row two is split per merchant, so one busy merchant can't spend the whole day's cap in an hour.",
 "C: The honest limit: some referred customers walk away. So we measure refer completion and the sales lost per minute of outage, and give those numbers to credit risk when they set the caps."])

say_slide("“Every timeout is a credit decision with an owner. Credit risk signs a table: second bureau, small known customers under a cap, refer, or decline with a real reason. Engineering makes it a setting with a counter and a dashboard.”", [
 "V: If asked, I'd say: every timeout is a credit decision with an owner. Credit risk signs the table. Engineering makes each row a setting with a counter, a cap and a dashboard.", "[pause: 1.0]",
 "N: The decision is settled. Next, the one step that must be atomic."])

# ───────── Challenge 3 · the phone drops ─────────
subchapter("7.3", "Challenge 3: The phone drops", ["N: Challenge three. The customer taps accept, loses signal, and taps again on another device: how many loans?"])
qs("Interviewer · challenge 3 of 8", "“The customer taps accept, the phone loses signal, and they tap again on the merchant's tablet. How many loans?”", [
 "I: The customer taps accept, the phone loses signal, and they tap again on the merchant's tablet. How many loans?", "[pause: 2.0]"])

S(dia(K(3, "the phone drops"), "Two devices, two keys, one application", "ch3-attack", q=True, red=True,
      extra=strip(("case", "Naive answer", "“Check whether a loan exists, and create one if it doesn't.” Or: “an orchestrated saga, with a compensation for each step.”"),
                  ("case", "Break", "The application service and its database: two workers both see no loan."))), [
 "C: The naive answer: check whether a loan exists, and create one if it doesn't. Or the saga answer: an orchestrated saga with a compensation for each step. The red boxes are the application service and its database, where two workers each see no loan."], cls="dia")

S(plain(K(3, "the trace"), "Two loans, one purchase", '<pre class="trace"><span class="t">14:31:07.200</span>phone posts accept, idempotency key k1\n<span class="t">07.900</span>the response is lost in the shop\'s dead zone\n<span class="t">08.050</span>tablet posts accept, key k2: another device, another key\n<span class="t">08.060</span>worker 1 reads ap_91: OFFERED, version 7, no loan\n<span class="t">08.070</span>worker 2 reads ap_91: OFFERED, version 7, no loan\n<span class="t">08.090</span><span class="bad">both insert: two loans, two transfers of $1,200, the customer billed twice</span></pre>' +
  '<div class="hedge"><b class="t">Why keys alone fail</b>Two devices, two idempotency keys. Check-then-insert fails because both checks ran before either insert.</div>', q=True, red=True), [
 "C: The trace. The phone posts accept with key k-one. The response is lost in the shop's dead zone. A hundred and fifty milliseconds later the tablet posts accept with key k-two: another device, another key. Worker one reads the application: offered, version seven, no loan. Worker two reads the same. Both insert. Two loans, two transfers to the merchant tonight, and a customer billed twice.",
 "C: Idempotency keys don't save this: two devices, two keys. And check-then-insert doesn't either: both checks ran before either insert."])

S(dia(K(3, "the fix"), "The database decides, in one transaction", "ch3-fix",
      extra=strip(("fixb", "Mechanism", "UPDATE … WHERE status = OFFERED AND version = 7; INSERT loan with UNIQUE(application_id); INSERT outbox; COMMIT. Zero rows updated: return the existing loan."),
                  ("whyb", "Property", "S1, enforced by the one place that sees both writers. No lock across a network call; no distributed coordination."))), [
 "C: The fix is one local transaction, in the database outlined green. A conditional update moves the application to booked only if it is still offered and at version seven. Insert the loan under a unique constraint on the application. Insert the outbox row. Commit. If the update changed zero rows, someone else booked, so return the existing loan. S-one is enforced by the one place that sees both writers."], cls="dia")

S(plain(K(3, "the transaction, as code"), "Book once, publish once",
  '<pre class="code" data-lang="sql"><span class="kw">BEGIN</span>;\n<span class="kw">UPDATE</span> application <span class="kw">SET</span> status = <span class="st">\'BOOKED\'</span>, version = 8\n <span class="kw">WHERE</span> id = <span class="st">\'ap_91\'</span> <span class="kw">AND</span> status = <span class="st">\'OFFERED\'</span> <span class="kw">AND</span> version = 7;\n<span class="cm">-- 0 rows: someone booked, or the offer expired → return the existing loan</span>\n<span class="kw">INSERT INTO</span> loan (id, application_id, offer_id, disclosure_v, terms)\n<span class="kw">VALUES</span> (<span class="st">\'ln_5531\'</span>, <span class="st">\'ap_91\'</span>, <span class="st">\'of_3\'</span>, <span class="st">\'v7\'</span>, <span class="st">\'{"months": 6}\'</span>);\n<span class="kw">INSERT INTO</span> outbox (event_id, type, payload)\n<span class="kw">VALUES</span> (<span class="st">\'ev_77\'</span>, <span class="st">\'LoanBooked\'</span>, <span class="st">\'{"loan_id": "ln_5531"}\'</span>);\n<span class="kw">COMMIT</span>;</pre>' +
  strip(("whyb", "Why it works", "The second worker's update matches zero rows: the first changed the status and the version. The unique constraint is a second wall. The outbox makes “the loan exists” and “the world will hear” one fact."), cols="one")), [
 "C: In code. The update has two conditions: still offered, and still version seven. The second worker's update matches zero rows, because the first already changed both. The unique constraint on the loan's application is a second wall, in case some code path forgets the update. And the outbox row commits with the loan, so the loan existing and the world hearing about it are one fact. The tablet's request reads the application, finds it booked, and shows the same loan."])

S(plain(K(3, "saga or state machine"), "Use the word only where it fits", table(["Step", "Can it be undone?", "So"], [
  ["Identity check, credit pull", "No: it happened, it was paid, it may be on the file", "Record it; never “compensate”"],
  ["Offer", "Expires by itself", "A lifetime, no action"],
  ["Accept → book", "Must be atomic", "One local transaction with the outbox"],
  ["Fund the merchant", "Yes, by a reversal or a return", "Asynchronous, retried, reconciled: challenge four"]], "bt sm")), [
 "C: So where does the word saga fit? Walk the steps. The identity check and the credit pull can't be undone: they happened and were paid. Record them. An offer expires by itself. Booking must be atomic, one local transaction. Only funding the merchant, after booking, can really be undone, by a reversal. A saga is a fine tool when several steps can be undone. Here only one can, and it comes after."])

qs("Interviewer · the second-level push", "“The commit succeeded, but the relay crashed before publishing. Or it published twice.”", [
 "I: The commit succeeded, but the relay crashed before publishing. Or it published twice.", "[pause: 2.0]"])

S(plain(K(3, "the second fix, and the honest limit"), "At least once, and every consumer de-duplicates", '<div class="cards c3">'
  '<div class="cd grn"><h3>The relay</h3><p>Reads unpublished rows, publishes, then marks them published. A crash in between publishes again: by design.</p></div>'
  '<div class="cd"><h3>Consumers</h3><p>Funding and servicing de-duplicate by event_id.</p></div>'
  '<div class="cd amb"><h3>The money</h3><p>Funding uses the loan ID as its idempotency key at the bank: a duplicate that slips through cannot pay twice.</p></div></div>' +
  line("Honest limit: at-least-once delivery with idempotent consumers. Not “exactly once”.", "r")), [
 "C: The relay is at least once by design. It reads unpublished rows, publishes, and only then marks them published, so a crash in between publishes again. Nothing is lost. Funding and servicing de-duplicate by event I-D, and funding uses the loan I-D as its idempotency key at the bank, so even a duplicate that slips through can't pay twice.",
 "C: The honest limit, said precisely: at-least-once delivery with idempotent consumers. Not exactly once."])

say_slide("“Only one step is atomic: accept to book. A conditional update at a version, a unique constraint on the application, and the outbox row in the same commit. A second tap finds the loan.”", [
 "V: If asked, I'd say: only one step is atomic, accept to book. A conditional update at a version, a unique loan, and the outbox row in the same commit. A second tap finds the loan.", "[pause: 1.0]",
 "N: The loan is booked once. Next, the money that moves after it."])

# ───────── Challenge 4 · funding fails ─────────
subchapter("7.4", "Challenge 4: Funding fails after booking", ["N: Challenge four. The loan is booked, and paying the merchant fails or goes silent: what do we undo, and what do we never resend?"])
qs("Interviewer · challenge 4 of 8", "“The loan is booked. The transfer to the merchant is rejected, or the bank times out. What do you undo?”", [
 "I: The loan is booked. The transfer to the merchant is rejected, or the bank times out. What do you undo?", "[pause: 2.0]"])

S(dia(K(4, "funding fails"), "Undo the loan? Re-send the money?", "ch4-attack", q=True, red=True,
      extra=strip(("case", "Naive answer", "“Roll back the saga: cancel the loan, reverse the credit check, delete the application.”"),
                  ("case", "Break", "Funding, after the customer has left: a rejected transfer, and one with no answer at all."))), [
 "C: The naive answer: roll back the saga. Cancel the loan, reverse the credit check, delete the application. We've just seen that two of those can't be undone. The red box is funding, and by now the customer has left the shop."], cls="dia")

S(plain(K(4, "the trace"), "One rejected, one silent", '<pre class="trace"><span class="t">14:31</span>loan ln_5531 booked\n<span class="t">18:00</span>daily batch: $1,164 to the merchant ($1,200 less a 3 % fee)\n<span class="t">18:02</span>the bank returns: <span class="bad">account closed</span>\n<span class="t">18:03</span>another merchant\'s transfer: <span class="bad">timeout, no answer</span>\n<span class="t">“to be safe”</span><span class="bad">re-send both: the second merchant may be paid twice</span></pre>' +
  '<div class="hedge"><b class="t">Label the numbers</b>The fee is illustrative. A timeout says nothing about whether the money moved.</div>', q=True, red=True), [
 "C: The trace. The loan is booked at two thirty-one. At six, the daily batch sends eleven hundred and sixty-four dollars to the merchant: the twelve hundred less a three percent fee. At two past six the bank says: account closed. At three past, another merchant's transfer times out with no answer at all.",
 "C: Re-sending both to be safe would pay the second merchant twice, if the first attempt actually went through. A timeout tells you nothing about whether money moved."])

S(dia(K(4, "the fix"), "Funding is its own state machine", "ch4-fix",
      extra=strip(("fixb", "Mechanism", "PENDING → SENT → SETTLED, or RETURNED → fix the account → a new attempt. A timeout is UNKNOWN: query by our key, never resend. Reconcile daily against the bank's file."),
                  ("whyb", "Property", "L2 with one effect: the loan ID is the idempotency key end to end, and UNKNOWN stops “maybe paid” from becoming “paid twice”."))), [
 "C: The fix: funding is its own state machine, after booking, outlined green. Pending, sent, settled. Or returned: merchant operations fixes the account, and a new attempt goes out with a new attempt number. A timeout becomes a state of its own, unknown, and the only action allowed on unknown is to ask the bank, by our idempotency key. Never resend.",
 "C: The loan itself is cancelled only if the goods weren't delivered, and that's a business decision with the merchant, not a rollback. L-two, with one effect: the loan I-D is the key end to end."], cls="dia")

S(dia(K(4, "sequence"), "Unknown, resolved by the file, not by a resend", "seq-ch4-fund"), [
 "C: As a sequence. Funding sends the transfer with the loan I-D as its key. Timeout: state unknown. It asks the bank: status, for this key? Not found, yet. So it waits for the reconciliation window. The next day's file from the bank shows the transfer settled at three past six. Unknown becomes settled, and nothing was resent."], cls="dia")

qs("Interviewer · the second-level push", "“The bank's status API says ‘not found’ for the timed-out transfer, and tomorrow's file shows it paid.”", [
 "I: The bank's status A-P-I says not found for the timed-out transfer, and tomorrow's file shows it paid.", "[pause: 2.0]"])

S(plain(K(4, "the second fix, and the honest limit"), "Not found is not “not sent”", '<div class="cards c3">'
  '<div class="cd amb"><h3>Wait for the window</h3><p>Bank interfaces often index instructions late. No resend before the reconciliation window closes.</p></div>'
  '<div class="cd grn"><h3>Three-way reconciliation</h3><p>Our funding records, the bank\'s settlement file, the loans booked. Every difference is a break.</p></div>'
  '<div class="cd"><h3>Breaks have owners</h3><p>An owner and an age; older than two days pages someone.</p></div></div>' +
  line("Honest limit: some outcomes are known only the next day. The merchant sees “in progress”, not a guess.", "r")), [
 "C: Not found, minutes after a timeout, does not mean not sent: many bank interfaces index instructions late. So no resend before the reconciliation window closes. Every day we compare three things: our funding records, the bank's settlement file, and the loans booked. Every difference is a break, with an owner and an age, and a break older than two days pages someone.",
 "C: The honest limit: some outcomes are only known the next day. The merchant's portal says in progress, not a guess."])

say_slide("“The credit pull and the booking aren't compensated: they happened. The one step with a real undo is funding, so it's its own state machine, with UNKNOWN as a state: query, never resend.”", [
 "V: If asked, I'd say: the credit pull and the booking happened. The one real undo is funding, so it's its own state machine, with unknown as a state. Query, never resend.", "[pause: 1.0]",
 "N: Money is settled. Next, a question about the past: why did we decide what we decided?"])
