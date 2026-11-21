from dsl import *

K = lambda n, t: f"Challenge {n} of 8 · {t}"

# ───────── Challenge 5 · refunds and chargebacks ─────────
subchapter("7.5", "Challenge 5: Refunds, and a chargeback months later", ["N: Challenge five. Money comes back: twice at once, and then again three months later, into a month that is already closed."])
qs("Interviewer · challenge 5 of 8", "“A payment was partially refunded twice. Two more refunds arrive at once. Then, three months later, a chargeback. How does the ledger stay right?”", [
 "I: A payment was partially refunded twice. Two more refunds arrive at once. Then, three months later, a chargeback. How does the ledger stay right?", "[pause: 2.0]"])

S(dia(K(5, "adjustments"), "Read, check, write: a race again", "ch5-attack", q=True, red=True,
      extra=strip(("case", "Naive answer", "“Update the payment's amount and the merchant's balance.”"),
                  ("case", "Break", "Two refunds read the same total; a chargeback edits a closed period."))), [
 "C: The naive answer: update the payment's amount and the merchant's balance. Look at the database, dashed red. Two refunds that read before they write are the same race as challenge two. And a chargeback that edits the original record rewrites a month that has already been reported."], cls="dia")

S(plain(K(5, "the trace"), "Twelve thousand refunded on ten thousand", '<pre class="trace"><span class="t">day 1        </span>p-5520 captured 10,000\n<span class="t">day 3, 9     </span>refunds of 3,000 and 4,000: refunded = 7,000\n<span class="t">day 12 +0 ms </span>refund 2,500 reads 7,000; 9,500 ≤ 10,000: ok\n<span class="t">day 12 +2 ms </span>refund 2,500 reads 7,000; 9,500 ≤ 10,000: ok\n<span class="t">day 12       </span><span class="bad">12,000 refunded on a 10,000 payment</span>\n<span class="t">day 92       </span>chargeback for the rest; <span class="bad">month 1 is closed and reported</span></pre>', q=True, red=True), [
 "C: The trace. A payment of ten thousand, refunds of three thousand and four thousand already done: seven thousand refunded. Two refunds of two thousand five hundred arrive two milliseconds apart. Each reads seven thousand, each checks that nine thousand five hundred is within ten thousand, and each passes. Twelve thousand refunded on a ten thousand payment.",
 "C: Then on day ninety-two, a chargeback, for a month that is closed and already reported."])

S(dia(K(5, "the fix"), "New transactions, and a limit in one statement", "ch5-fix",
      extra=strip(("fixb", "Mechanism", "Each adjustment is a new journal transaction referencing the payment. The limit is one conditional update on the payment row. A chargeback posts entries dated now, to a disputes account."),
                  ("whyb", "Property", "S2 and S3: history is append-only, so the closed month still adds up, and a correction is visible as a correction."))), [
 "C: The fix. Each adjustment is a new journal transaction that references the payment. The refund limit is one conditional update: add the amount only where the new total stays within captured. Exactly one of the two refunds updates a row; the other updates zero rows and is refused. The chargeback posts entries dated now, to a disputes account, and the closed month is never touched."], cls="dia")

S(dia(K(5, "sequence"), "One refund wins; the month stays closed", "seq-refund"), [
 "C: As a sequence. Refunds r-one and r-two arrive two milliseconds apart. Three, highlighted: the conditional update for r-one changes one row. Four: the same for r-two changes zero rows, and r-two gets a four twenty-two. Five: the refund goes to the processor with reference p-fifty-five twenty slash r-one. Six: a new journal transaction, dated now. And on day ninety-two the chargeback is posted the same way."], cls="dia")

qs("Interviewer · the second-level push", "“The merchant wins the dispute, so the chargeback is reversed. Or the refund is in a different currency.”", [
 "I: The merchant wins the dispute, so the chargeback is reversed. Or the refund is in a different currency.", "[pause: 2.0]"])

S(plain(K(5, "the second fix, and the honest limit"), "One more transaction, and a rate that is recorded", '<div class="cards c2">'
  '<div class="cd grn"><h3>Dispute won</h3><p>A reversal is one more transaction: from the disputes account back to the merchant. The state machine records it.</p></div>'
  '<div class="cd grn"><h3>Another currency</h3><p>Amounts stay in the original currency. A conversion is its own transaction, with the rate it used, versioned.</p></div></div>' +
  line("Honest limit: who bears the loss in a dispute is a contract, not code. Finance owns those rules.", "r")), [
 "C: A won dispute is one more transaction, from the disputes account back to the merchant. A refund in another currency: the amounts stay in the original currency, and any conversion is its own transaction with the rate it used. The honest limit: who bears a loss in a dispute is decided by contracts, not by code, and finance owns those rules."])

say_slide("“Nothing is edited. A refund, a chargeback or a reversal is a new balanced transaction that references the payment and is dated when it happened, so closed months still add up. The refund limit is one conditional update on the payment row, so two concurrent refunds can't both pass.”", [
 "V: If asked, I'd say: nothing is edited. A refund, a chargeback or a reversal is a new balanced transaction that references the payment and is dated when it happened, so closed months still add up. The refund limit is one conditional update on the payment row, so two concurrent refunds can't both pass.", "[pause: 1.0]",
 "N: Our books are now right by construction. Are they right compared with the processor's?"])

# ───────── Challenge 6 · 999,998 against 1,000,000 ─────────
subchapter("7.6", "Challenge 6: 999,998 against 1,000,000", ["N: Challenge six, the second half of the crux. The processor's books and ours disagree by two."])
qs("Interviewer · challenge 6 of 8", "“The processor's settlement statement says 999,998. Your books say 1,000,000. What now?”", [
 "I: The processor's settlement statement says nine hundred ninety-nine thousand nine hundred ninety-eight. Your books say one million. What now?", "[pause: 2.0]"])

S(dia(K(6, "the outside truth"), "Who is right, and how would you know?", "ch6-attack", q=True, red=True,
      extra=strip(("case", "Naive answer", "“We'd look into it. Our system is correct by construction.”"),
                  ("case", "Break", "Correct inside is not the same as agreeing with the outside. Totals hide the cause."))), [
 "C: The naive answer: we'd look into it, our system is correct by construction. Look at reconciliation, dashed red, and the settlement file arriving from the processor. Being correct inside our database is not the same as agreeing with the party that actually moved the money. And a difference in totals hides its causes."], cls="dia")

S(plain(K(6, "the case"), "A difference of two, made of three breaks", table(["Line", "Ours", "Theirs", "Kind"], [
  ["Capture booked at 23:58, settles tomorrow", "1,050", "—", "timing: closes by itself"],
  ["An UNKNOWN we resolved as declined", "—", "1,050", "<b class=\"bad\">real: the customer paid</b>"],
  ["A fee 2 higher than the contract", "30", "32", "real: the processor's error"],
  ["<b>Net</b>", "", "<b>−2</b>", ""]], "bt sm") +
  line("The total differs by 2. The break that matters most, a real charge we think was declined, is invisible in the total.", "r")), [
 "C: The case. Three differences. A capture we booked at two minutes to midnight that settles tomorrow: timing, it closes by itself. An unknown we resolved as declined, which the processor actually settled: a real break, the customer paid and we think they did not. And a fee two higher than the contract.",
 "C: Net, minus two. The most important break, a real charge we think was declined, is invisible in the total. That is why reconciliation is never done on totals."])

S(dia(K(6, "the fix"), "Expectations, matched line by line, every break owned", "ch6-fix",
      extra=strip(("fixb", "Mechanism", "Store the raw file unchanged. The ledger generates expectations by reference, net of fees. Match line by line. Every unmatched line is a break with a type, an owner and an age."),
                  ("whyb", "Property", "L2: every difference becomes a named, owned item. S2 holds against the outside world, not only inside our database."))), [
 "C: The fix: reconciliation as a permanent component. The raw file is stored unchanged first. The ledger generates expectations: what each processor should settle, by reference, net of fees. The match is line by line. Every unmatched line becomes a break with a type, missing on their side, missing on ours, amount, or timing, plus an owner and an age, in front of finance operations."], cls="dia")

S(dia(K(6, "sequence"), "From the file to an owned break", "seq-recon"), [
 "C: As a sequence. One: the file arrives, about two hundred ninety million lines, stored unchanged. Two: expectations for the day from the ledger. Then the match. Three: matched lines move payments to settled, with settlement entries. Four, highlighted: the break, settled by them and declined by us, one thousand and fifty, with an owner and age zero. Timing breaks close themselves when tomorrow's file matches."], cls="dia")

qs("Interviewer · the second-level push", "“There are forty thousand breaks this morning, not forty.”", [
 "I: There are forty thousand breaks this morning, not forty.", "[pause: 2.0]"])

S(plain(K(6, "the second fix"), "A spike in breaks is an incident, not a backlog", '<div class="cards c3">'
  '<div class="cd amb"><h3>Classify first</h3><p>By type and processor. One cause usually explains thousands of lines.</p></div>'
  '<div class="cd red"><h3>Protect money</h3><p>Hold payouts if the break amount crosses a threshold. Money not yet sent can still be protected.</p></div>'
  '<div class="cd grn"><h3>Fix the cause</h3><p>Then the lines. Breaks by age is a dashboard with a target; finance ops is a team with tooling.</p></div></div>'), [
 "C: Forty thousand breaks is an incident, not a backlog. Classify first, by type and processor: one cause usually explains thousands of lines. Protect the money: hold payouts if the break amount crosses a threshold, because money not yet sent can still be protected. Fix the cause before the lines. And say it out loud: breaks by age is a dashboard with a target, and finance operations is a team that needs tooling."])

say_slide("“Reconciliation isn't a safety net for a buggy system; it's a permanent component, because the processor's truth and ours diverge even when our code is right. I match line by line against expectations from the ledger, every difference becomes a break with an owner and an age, and a spike in breaks is treated as an incident.”", [
 "V: If asked, I'd say: reconciliation isn't a safety net for a buggy system. It's a permanent component, because the processor's truth and ours diverge even when our code is right. I match line by line against expectations from the ledger, every difference becomes a break with an owner and an age, and a spike in breaks is treated as an incident.", "[pause: 1.0]",
 "N: And when the cause of the spike is our own code?"])

# ───────── Challenge 7 · a bug double-posted 40,000 entries ─────────
subchapter("7.7", "Challenge 7: A bug double-posted forty thousand entries", ["N: Challenge seven. Our own release wrote wrong entries overnight, and some of the money has already left."])
qs("Interviewer · challenge 7 of 8", "“A bug double-posted forty thousand entries last night, and some merchants have already been paid out. What do you do?”", [
 "I: A bug double-posted forty thousand entries last night, and some merchants have already been paid out. What do you do?", "[pause: 2.0]"])

S(dia(K(7, "wrong entries"), "The books are wrong, and money has moved", "ch7-attack", q=True, red=True,
      extra=strip(("case", "Naive answer", "“Write a script to delete the duplicates.”"),
                  ("case", "Break", "A DELETE destroys the evidence and breaks S3. The paid-out money is not in the database at all."))), [
 "C: The naive answer: write a script to delete the duplicates. Look at the ledger, dashed red. A delete destroys the evidence of what happened, breaks the rule that history is never rewritten, and does nothing about the money that has already been paid out, because that money is no longer in our database."], cls="dia")

S(plain(K(7, "the trace"), "Ninety minutes of a bad release", '<pre class="trace"><span class="t">22:10  </span>release 2026.11.19 starts posting the fee leg twice\n<span class="t">23:40  </span>40,000 captures affected; <span class="bad">1,200 merchants’ payables too high by the fee</span>\n<span class="t">00:00  </span>nightly payouts run: <span class="bad">180 of them paid the excess</span>\n<span class="t">07:30  </span>reconciliation: fee breaks up sharply; incident opened</pre>', q=True, red=True), [
 "C: The trace. At ten past ten at night a release starts posting the fee leg twice. By twenty to midnight, forty thousand captures are affected, and twelve hundred merchants' payables are too high by the fee. At midnight the payouts run, and a hundred and eighty of them are paid the excess. At half past seven, reconciliation's fee breaks jump, and an incident is opened."])

S(dia(K(7, "the fix"), "Stop, identify, reverse, recover, learn", "ch7-fix",
      extra=strip(("fixb", "Mechanism", "Kill the release; hold payouts for the affected merchants. Find the duplicates exactly in the immutable journal. Post one reversing transaction per duplicate, tagged with the incident."),
                  ("whyb", "Property", "S3 makes the correction tractable and provable: nothing was overwritten, so the duplicates can be found and reversed exactly."))), [
 "C: The fix, in order. Stop the bleeding: switch the release off and hold payouts for the affected merchants. Identify: the journal is immutable, so the duplicates are exactly the payments with two fee transactions. Reverse: the correction tool, in green, posts one reversing transaction per duplicate, tagged with the incident. The audit trail now shows the error and its correction."], cls="dia")

S(dia(K(7, "sequence"), "The correction, step by step", "seq-correct"), [
 "C: As a sequence. One, highlighted: the kill switch. Two: hold payouts for the twelve hundred merchants. Three: find forty thousand duplicate rows. Four: post one reversing transaction each, tagged with the incident number. Five: the hundred and eighty already paid become a receivable, recovered from their future settlements. That last step is a business decision with a message to each merchant, not a database operation."], cls="dia")

qs("Interviewer · the second-level push", "“Idempotency should have stopped this. Why didn't it?”", [
 "I: Idempotency should have stopped this. Why didn't it?", "[pause: 2.0]"])

S(plain(K(7, "the second fix"), "Idempotency guards requests, not code paths", '<div class="cards c2">'
  '<div class="cd amb"><h3>Why it got through</h3><p>One request, one key: the bug was a second posting <b>inside</b> it, with a new transaction ID. No retry was involved.</p></div>'
  '<div class="cd grn"><h3>The invariant that stops the class</h3><p>A unique constraint on <b>(payment_id, type)</b> for single-occurrence types, such as the fee. And an hourly reconciliation check.</p></div></div>' +
  line("Then a postmortem on the class: why tests and canaries let a double posting through.", "a")), [
 "C: Because idempotency guards requests, not code paths. There was one request with one key. The bug posted twice inside it, with a new transaction I-D each time. The invariant that stops the whole class is a unique constraint on payment and type for types that may occur only once, like the fee. Plus an hourly check that would have caught it at eleven instead of half past seven. Then a postmortem on why tests and the canary let it through."])

say_slide("“Stop the bleeding first: kill the release and hold payouts. Because the journal is immutable I can find the duplicates exactly and post reversing entries tagged with the incident, so the audit trail shows both. Money already paid out is a receivable and a conversation with those merchants. Then a constraint and an hourly check, so this class can't repeat silently.”", [
 "V: If asked, I'd say: stop the bleeding first. Kill the release and hold payouts. Because the journal is immutable I can find the duplicates exactly and post reversing entries tagged with the incident, so the audit trail shows both. Money already paid out is a receivable and a conversation with those merchants. Then a constraint and an hourly check, so this class can't repeat silently.", "[pause: 1.0]",
 "N: An hourly check. Which raises the last question: what would have told us at all?"])

# ───────── Challenge 8 · observability ─────────
subchapter("7.8", "Challenge 8: How would you know before finance does?", ["N: Challenge eight. Every dashboard is green, and merchants are losing sales."])
qs("Interviewer · challenge 8 of 8", "“What do you watch, and what alert fires before finance notices that something is wrong?”", [
 "I: What do you watch, and what alert fires before finance notices that something is wrong?", "[pause: 2.0]"])

S(dia(K(8, "silence"), "Green dashboards, fewer sales", "ch8-attack", q=True, red=True,
      extra=strip(("case", "Naive answer", "“API error rate and latency.”"),
                  ("case", "Break", "A decline is a successful API call. Nothing on the dashboard measures money."))), [
 "C: The naive answer: error rate and latency. Look at the adapter and the processor, dashed red. A decline is a successful A-P-I call: it returns quickly and without an error. So if approvals fall, nothing on a server dashboard moves."], cls="dia")

S(plain(K(8, "the trace"), "Seven hours of quiet losses", '<pre class="trace"><span class="t">02:00  </span>a change at one processor: <span class="bad">6 points more declines</span> for one country\n<span class="t">02:00  </span>API errors 0 %; latency normal; every check green\n<span class="t">09:00  </span>merchants report sales are down\n<span class="t">09:20  </span><span class="bad">first alert is a customer complaint</span></pre>', q=True, red=True), [
 "C: The trace. At two in the morning, a change on one processor's side declines six more percentage points of cards from one country. Errors: zero. Latency: normal. Every check green. At nine, merchants report that sales are down. The first alert is a customer."])

S(dia(K(8, "the fix"), "Watch the money and the truth", "ch8-fix",
      extra=strip(("fixb", "Mechanism", "Approval rate per processor, country and card type against its own baseline. UNKNOWN count and age. Outbox age. Debits minus credits = 0, checked continuously. Unreconciled amount by age. A synthetic payment per processor every minute."),
                  ("whyb", "Property", "The alerts measure what finance and merchants measure, a day earlier."))), [
 "C: The fix: service level indicators on the money. Approval rate per processor, per country, per card type, against its own baseline. Unknown count and age. Outbox age. Debits minus credits equal to zero, checked continuously, and any non-zero value pages immediately. Unreconciled amount by age. And the green probe: a synthetic payment with a test card through each processor every minute."], cls="dia")

S(dia(K(8, "sequence"), "The probe, end to end", "seq-probe"), [
 "C: The probe as a sequence. One: a synthetic payment with a test card. Two: authorised through the real path, with a reference. Captured in four hundred and ten milliseconds. Three: success and latency per processor go to monitoring. In red, the alert that would have fired at two in the morning: approval rate for one processor and country, six points under its baseline. In green, the ledger check: debits minus credits is zero."], cls="dia")

S(plain(K(8, "symptom pairs"), "Two metrics, one conclusion", table(["Metric A", "Metric B", "Conclusion"], [
  ["approvals down", "latency normal", "a processor or issuer change, not us"],
  ["UNKNOWN up", "latency at the timeout", "the processor is slow"],
  ["outbox age up", "commits normal", "the relay is stuck"],
  ["breaks up today", "UNKNOWN up yesterday", "the inquiry is not resolving"],
  ["debits − credits ≠ 0", "anything", "stop and page: a posting bug"]], "bt sm") +
  grade("Reading metrics in pairs turns two numbers into one cause. It is what a runbook for “payments failing at 3 a.m.” starts from.")), [
 "C: Then read them in pairs. Approvals down with latency normal: a processor or issuer change, not us. Unknowns up with latency at the timeout: the processor is slow. Outbox age up with commits normal: the relay is stuck. Breaks up today after unknowns rose yesterday: the inquiry is not resolving. And a ledger that does not sum to zero: stop and page, whatever else is true.",
 "N: Pairs like these are what an on-call runbook for payments failing at three in the morning starts from."])

qs("Interviewer · the second-level push", "“The approval rate drops slowly: half a point a week.”", [
 "I: The approval rate drops slowly. Half a point a week.", "[pause: 2.0]"])

S(plain(K(8, "the second fix"), "A slow drift needs a slow comparison", '<div class="cards c2">'
  '<div class="cd grn"><h3>Weekly, against a seasonal baseline</h3><p>Per segment: processor, country, card type, merchant category. Drift is only visible against the same week last year or a stable control.</p></div>'
  '<div class="cd grn"><h3>An owner for the number</h3><p>Approval rate is a business metric with an owner in payments operations, reviewed weekly with the processor.</p></div></div>'), [
 "C: A slow drift needs a slow comparison: weekly, per segment, against a seasonal baseline, because half a point a week is invisible minute by minute. And the approval rate needs an owner, in payments operations, who reviews it with the processor every week. A metric with no owner is a decoration."])

say_slide("“I watch the money, not the servers: approval rate per processor and segment against its baseline, the count and age of unknown outcomes, outbox age, unreconciled amount by age, and a continuous check that the ledger sums to zero, which pages immediately. Then I read metrics in pairs to tell ‘the processor changed’ from ‘we broke’.”", [
 "V: If asked, I'd say: I watch the money, not the servers. Approval rate per processor and segment against its baseline, the count and age of unknown outcomes, outbox age, unreconciled amount by age, and a continuous check that the ledger sums to zero, which pages immediately. Then I read metrics in pairs to tell the processor changed from we broke.", "[pause: 1.0]"])

# ───────────────────────── 8 · build cost ─────────────────────────
chapter(8, "Build cost", 6, "The manager layer: people, quarters, buy against build", [
 "N: This chapter is marked auxiliary. It is the engineering-manager layer, optional in a Staff round.",
 "C: Payments are not one project. They are three releases, and the first one should mostly be bought."], aux=True)

S(plain("Build cost · the releases", "V1 bought, V2 built, V3 run", table(["Release", "Scope", "People × time", "Label"], [
  ["<b>V1</b>", "a processor with its hosted payment page and token vault; our orders, their records", "3 engineers × 1 quarter", "illustrative"],
  ["<b>V2</b>", "idempotency, the state machine, the journal", "5–6 engineers × 2 quarters", "illustrative"],
  ["<b>V3</b>", "outbox, inquiry, reconciliation, a second processor", "two teams × 2–3 quarters, plus finance ops", "illustrative"]], "bt sm") +
  line("V1 keeps card data out of our scope entirely. That is worth more than any of our code.", "a")), [
 "C: Version one is bought: a processor with its hosted payment page and token vault, so card numbers never touch us. Three engineers for a quarter. Version two is built: idempotency, the state machine, the journal. Five or six engineers for two quarters. Version three is run: outbox, inquiry, reconciliation and a second processor. Two teams for two or three quarters, plus a finance operations function. All illustrative."], cls="aux")

S(plain("Build cost · the one-way doors", "Two decisions that outlive everyone in the room", '<div class="cards c2">'
  '<div class="cd red"><h3>The ledger schema</h3><p>Seven years of records and every auditor depend on it. Changing it is a migration of history.</p></div>'
  '<div class="cd red"><h3>The idempotency contract</h3><p>Every merchant integration encodes it. Changing retention or semantics breaks clients you do not control.</p></div></div>' +
  line("These get the most review. Everything else can be changed in a quarter.", "a")), [
 "C: Two decisions are one-way doors. The ledger schema: seven years of records and every auditor depend on it. And the idempotency contract: every merchant integration has encoded it, so changing it breaks clients we do not control. Those get the most review. Everything else can change in a quarter."], cls="aux")

S(plain("Build cost · team seams", "Four teams, and one of them owns the ledger", table(["Team", "Owns", "Contract with the others"], [
  ["Payments API and state machine", "keys, states, the deadline", "the public API and webhook schema"],
  ["<b>Ledger</b>", "accounts, postings, projections", "posting API; reviews every new transaction type"],
  ["Processor integrations", "adapters, references, error taxonomy", "one internal interface per processor"],
  ["Reconciliation and finance tooling", "expectations, breaks, the console", "break types and ageing targets"]], "bt sm")), [
 "C: Four team seams. Payments A-P-I and state machine. The ledger, owned centrally, with a posting interface, and it reviews every new transaction type, because everyone touches it. Processor integrations, one adapter per processor behind one internal interface. And reconciliation and finance tooling, whose contract is the break types and their ageing targets."], cls="aux")

S(plain("Build cost · risks", "What would make this late or wrong", '<div class="cards c3">'
  '<div class="cd red"><h3>An untested unknown path</h3><p>It runs rarely, so it breaks quietly. Inject timeouts in staging every day.</p></div>'
  '<div class="cd amb"><h3>Reconciliation built last</h3><p>Then the first months of breaks are found by finance, by hand.</p></div>'
  '<div class="cd amb"><h3>A second processor without inquiry</h3><p>Its unknowns can only be resolved a day late.</p></div></div>'), [
 "C: Three risks. An unknown path that is never tested, because it runs rarely: inject timeouts in staging every day. Reconciliation built last, so the first months of breaks are found by hand. And a second processor added without its own inquiry semantics, whose unknowns can only be resolved a day late."], cls="aux")

S(plain("Build cost · cost", "Fees, not servers", table(["Item", "Size", "Label"], [
  ["Processor fees", "a percentage of every payment's value", "dominant"],
  ["Database cluster for the journal", "~580 TB over seven years, hot and cold", "illustrative"],
  ["People", "two teams plus finance operations", "illustrative"]], "bt sm") +
  line("The engineering levers on cost: routing between processors, and fewer false declines.", "a")), [
 "C: Cost. The infrastructure is real: a journal that grows to hundreds of terabytes. But processor fees dwarf it. So the engineering levers on cost are routing between processors and reducing false declines, each worth basis points on the whole volume."], cls="aux")

# ───────────────────────── 9 · recap ─────────────────────────
chapter(9, "Recap", 7, "One picture, five paths, the mistakes, the thesis", [
 "C: To close: one picture, one sentence per path, the mistakes to avoid, and the thesis."])

S(dia("Recap", "The whole design on one baseline", "base-final", chip=chips("key first", "UNKNOWN", "journal", "outbox", "inquiry", "reconciliation")), [
 "C: The whole design on one baseline. The key inserted first, in front of the A-P-I. The state machine with unknown in the payment service. The journal, the outbox and sub-accounts in the database. The inquiry job beside the adapter. Reconciliation and finance operations on the right. The correction tool, and probes that watch the money."], cls="dia")

S(plain("Recap · one sentence per path", "Five paths", table(["Path", "In one sentence"], [
  ["<b>Pay</b>", "key first, attempt committed, call by reference, one transaction for state, entries and event"],
  ["<b>Adjust</b>", "a new transaction, dated now, with the limit in one conditional update"],
  ["<b>Notify</b>", "an outbox row, published at least once, de-duplicated by event ID"],
  ["<b>Reconcile</b>", "expectations from the ledger, matched line by line, every break owned"],
  ["<b>Explain</b>", "a sum over immutable entries"]], "bt")), [
 "C: One sentence per path. Pay: key first, attempt committed, call by reference, one transaction for state, entries and event. Adjust: a new transaction, dated now, with the limit in one conditional update. Notify: an outbox row, published at least once. Reconcile: expectations, matched line by line, every break owned. Explain: a sum over immutable entries."])

S(plain("Recap · common mistakes in this round", "What costs candidates the most", '<div class="cards c2">'
  '<div class="cd red"><h3>On correctness</h3><p>“A distributed transaction with the bank.” A balance column as the truth. A timeout treated as a failure. Floats. Keys checked instead of inserted. A changed retry silently accepted.</p></div>'
  '<div class="cd red"><h3>On operations</h3><p>Events published outside the transaction. History edited. No reconciliation, or reconciliation by totals. No owner for breaks. Dashboards with no money on them.</p></div></div>'), [
 "C: The common mistakes. On correctness: a distributed transaction with the bank, a balance column as the truth, a timeout treated as a failure, floats, keys that are checked instead of inserted, and a changed retry silently accepted. On operations: events published outside the transaction, history edited, no reconciliation or reconciliation by totals, no owner for breaks, and dashboards with no money on them."])

S(plain("Recap · the four sentences", "If you have thirty seconds", '<div class="cards c2">'
  '<div class="cd"><h3>What</h3><p>A state machine per payment, an idempotent API, an immutable double-entry journal, reconciliation.</p></div>'
  '<div class="cd amb"><h3>The trade</h3><p>Pending answers and a reconciliation team, in exchange for never guessing.</p></div>'
  '<div class="cd red"><h3>The risk</h3><p>The unknown path runs rarely; test it daily.</p></div>'
  '<div class="cd grn"><h3>Next</h3><p>Harden inquiry per processor; make breaks an owned, aged workflow.</p></div></div>'), [
 "C: If I had thirty seconds: what it is, a state machine per payment, an idempotent A-P-I, an immutable double-entry journal and reconciliation. The trade: pending answers and a reconciliation team, in exchange for never guessing. The risk: the unknown path runs rarely, so I'd test it every day. Next: harden the inquiry per processor, and make breaks an owned, aged workflow."])

key("The thesis, again", "I can't get exactly-once across the boundary, so I get <em>one effect per intent</em>, a state for <em>not knowing</em>, and books I can <em>explain</em> and <em>reconcile</em>.", [
 "V: I can't get exactly-once across the boundary, so I get one effect per intent: a key inserted first, a reference on every call, a state for not knowing, and an inquiry that ends it. Every movement is a balanced, immutable entry, so any balance is a sum I can explain. And because the outside world's books will disagree with mine anyway, reconciliation is part of the design, with owners.", "[pause: 1.5]"])
