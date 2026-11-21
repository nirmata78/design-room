from dsl import *

K = lambda n, t: f"Challenge {n} of 8 · {t}"

# ───────── Challenge 5 · payoff with a debit in flight ─────────
subchapter("7.5", "Challenge 5: Paying off with a debit in flight", ["N: Challenge five. The customer pays off early, but a debit from two days ago hasn't cleared."])
qs("Interviewer · challenge 5 of 8", "“On the third, the customer pays off the loan early. Instalment three's debit from the first is still pending. What do you quote?”", [
 "I: On the third, the customer pays off the loan early. Instalment three's debit from the first is still pending. What do you quote?", "[pause: 2.0]"])

S(dia(K(5, "the quote"), "Is the pending $150 paid or not?", "ch5-attack", q=True, red=True,
      extra=strip(("case", "Naive answer", "“Quote the balance.” Either the balance counts the pending debit, or it doesn't."),
                  ("case", "Break", "Both choices are wrong some of the time: one over-collects when the debit settles, the other closes a loan that is still owed money."))), [
 "C: The naive answer: quote the balance. But the balance either counts the pending debit as paid, or it doesn't. Look at the A-P-I. Both choices are wrong some of the time. One over-collects when the debit settles. The other closes a loan that still owes money."], cls="dia")

S(plain(K(5, "the trace"), "Two quotes, two different mistakes", '<pre class="trace"><span class="t">Dec 1   </span>ln-5531 instalment 3, $150, in the debit file; $900 outstanding before it\n<span class="t">Dec 3   </span>quote A: $900 (ignores the pending debit); paid by card\n<span class="t">Dec 3   </span>the debit settles: <span class="bad">$150 over-collected</span>\n<span class="t">Dec 3   </span>quote B: $750 (counts it as paid); loan CLOSED, lien released\n<span class="t">Dec 4   </span>the $150 returns R01: <span class="bad">a closed loan that owes $150</span></pre>', q=True, red=True), [
 "C: The trace. On the first, instalment three, a hundred and fifty dollars, goes in the debit file, with nine hundred outstanding before it. On the third, quote A says nine hundred, ignoring the pending debit. The customer pays by card, the debit settles too, and we've over-collected a hundred and fifty.",
 "C: Quote B says seven hundred and fifty, counting the debit as paid. The loan is closed and the merchant told. On the fourth, the debit returns for insufficient funds. Now a closed loan owes a hundred and fifty, and nobody has a process for that."])

S(dia(K(5, "the fix"), "The quote lists what is in flight", "ch5-fix",
      extra=strip(("fixb", "Mechanism", "q-31: $750 now, conditional on the $150 debit. Loan → PAID_PENDING, not CLOSED. A return reopens $150, no late mark."),
                  ("whyb", "Property", "S1: nothing twice. S3: no penalty for timing. L2: a defined exit."))), [
 "C: The fix: a payoff quote is a statement about the future, so it lists what is in flight. Quote q-thirty-one: seven hundred and fifty now, conditional on the hundred and fifty dollar debit clearing, valid until the fifth. Paying it moves the loan to paid-pending, not closed. If the debit clears, the loan closes. If it returns, a hundred and fifty reopens as a single due item, with no late mark."], cls="dia")

S(dia(K(5, "sequence"), "The payoff, as a sequence", "seq-payoff"), [
 "C: As a sequence. One: the customer asks for a quote. The answer: seven hundred and fifty now, the hundred and fifty debit listed, valid to the fifth. Two: they pay against q-thirty-one, and the quote I-D is the idempotency key, so a double tap pays once. Three, highlighted: the lines post, and the loan is paid-pending. Four: if the return arrives, one due item of a hundred and fifty. And if nothing comes back by the fifth, closed, lien released, and a notice."], cls="dia")

S(plain(K(5, "the rule"), "Close only when nothing can come back", table(["In flight at payoff", "Quote", "Loan state", "Closes when"], [
  ["nothing", "full balance", "CLOSED", "at payment"],
  ["a card charge", "balance − charge", "PAID_PENDING", "the charge settles (minutes)"],
  ["a bank debit", "balance − debit, conditional", "PAID_PENDING", "the debit is past its insufficient-funds window"],
  ["a debit not yet sent", "full balance; cancel it", "CLOSED", "at payment"]], "bt sm") +
  strip(("whyb", "Why it works", "The only uncertainty left is the 60-day unauthorised window, which is handled as a dispute, not by holding loans open."), cols="one")), [
 "C: The rule as a table. Nothing in flight: quote the full balance and close. A card charge in flight: minutes, then close. A bank debit in flight: a conditional quote, and close when the debit is past its insufficient-funds window. A debit not yet sent: cancel it, quote the full balance, and close. What is left is the sixty-day unauthorised window, and that is handled as a dispute, not by holding every loan open for two months."])

qs("Interviewer · the second-level push", "“The day after the payoff, a merchant refund arrives on the same loan.”", [
 "I: The day after the payoff, a merchant refund arrives on the same loan.", "[pause: 2.0]"])

S(plain(K(5, "the second fix"), "Overpayment is a liability with a deadline", '<div class="cards c2">'
  '<div class="cd grn"><h3>Customer payable</h3><p>The refund reduces principal below zero; the excess moves to customer payable and is paid back automatically, to the original method.</p></div>'
  '<div class="cd amb"><h3>A deadline and an alert</h3><p>Every customer payable older than the policy days pages its owner. Money we owe is never left as a quiet credit.</p></div></div>'), [
 "C: The refund takes principal below zero. The excess becomes customer payable, money we owe, and it is paid back automatically to the original method. And every customer payable older than the policy's limit pages its owner. Money we owe is never left sitting as a quiet credit."])

say_slide("“A payoff quote is a statement about the future: it lists what's in flight. The loan goes to paid-pending and closes only when nothing can still come back; any overpayment is refunded automatically.”", [
 "V: If asked, I'd say: a payoff quote lists what's in flight. The loan goes to paid-pending and closes only when nothing can still come back, and any overpayment is refunded automatically.", "[pause: 1.0]",
 "N: All these moving parts meet at month-end, when the bank sends its statement."])

# ───────── Challenge 6 · $400 more than the bank ─────────
subchapter("7.6", "Challenge 6: Four hundred dollars more than the bank", ["N: Challenge six. Month-end, and the ledger and the bank disagree."])
qs("Interviewer · challenge 6 of 8", "“Month-end. The ledger says we collected four hundred dollars more than the bank received. Find it.”", [
 "I: Month-end. The ledger says we collected four hundred dollars more than the bank received. Find it.", "[pause: 2.0]"])

S(dia(K(6, "the gap"), "Four hundred dollars, or four problems?", "ch6-attack", q=True, red=True,
      extra=strip(("case", "Naive answer", "“Compare the totals, and post a $400 adjustment to close.”"),
                  ("case", "Break", "A total is a sum of differences. Some cancel each other, and one of those may be a customer charged twice."))), [
 "C: The naive answer: compare the totals, and post a four-hundred dollar adjustment so the month can close. Look at reconciliation. A total is a sum of differences, and some of them cancel each other out. One of the hidden ones may be a customer charged twice."], cls="dia")

S(plain(K(6, "the trace"), "Inside the four hundred", '<pre class="trace"><span class="t">ledger    </span>cash collected in November: $90,000,400\n<span class="t">bank      </span>deposits net of returns:    $90,000,000\n<span class="t">+300      </span>two R01 returns on the bank statement Nov 30; the return file arrives Dec 1 (timing)\n<span class="t">+100      </span>a card dispute the processor netted from its payout; <span class="bad">none in the ledger</span>\n<span class="t">+150      </span>a card payment we hold as settled; <span class="bad">the processor never settled it</span>\n<span class="t">−150      </span>a charge the processor settled that we hold as declined: <span class="bad">a double charge</span></pre>', q=True, red=True), [
 "C: The trace. The ledger says ninety million and four hundred dollars collected in November. The bank says ninety million. Inside the four hundred: plus three hundred, two insufficient-funds returns on the bank statement for the thirtieth, whose return file only arrives on the first. That is timing. Plus a hundred, a card dispute the processor deducted from its payout, and we have no record of it.",
 "C: And a pair that hides itself: plus a hundred and fifty, a card payment we think settled and the processor never settled. Minus a hundred and fifty, a charge the processor did settle that we hold as declined. That one is a customer charged twice. In the total, those two cancel to zero."])

S(dia(K(6, "the fix"), "Match every line, three ways, by reference", "ch6-fix",
      extra=strip(("fixb", "Mechanism", "Ledger expectations matched to the processor and the bank by reference, then amount and a 3-day window. Typed breaks, owned and aged."),
                  ("whyb", "Property", "L3: owned within a day. Nothing is matched by total."))), [
 "C: The fix: match every line, three ways, by reference. The ledger produces what it expects. The processor's report and the bank statement are matched to it by our reference, then by amount within a three-day window. Every difference becomes a typed break: timing, missing in our ledger, missing at the processor, or a wrong amount. Each one gets an owner and an age."], cls="dia")

S(dia(K(6, "sequence"), "Reconciliation, as a sequence", "seq-recon"), [
 "C: As a sequence. One: the expectations for the thirtieth, by reference. Two and three: the processor's report and the bank statement. Then the match, by reference first. Four, highlighted: four breaks go to finance operations, one timing and three real, each with an owner. The timing break closes itself when the return file posts on the first."], cls="dia")

S(plain(K(6, "the breaks"), "Four breaks, four owners", table(["Break", "Type", "Owner", "Action"], [
  ["+$300, two returns", "timing", "auto", "closes when the Dec 1 return file posts"],
  ["+$100, card dispute", "missing in ledger", "disputes team", "post the dispute; contest or accept"],
  ["+$150, never settled", "missing at processor", "payments team", "query; reverse our posting"],
  ["−$150, settled, held declined", "double charge", "payments team", "post it; refund the customer today"]], "bt sm") +
  grade("Reconciling by totals is the most common silent failure in this round. Saying “I never reconcile by totals” earns the point.")), [
 "C: Four breaks, four owners. The three hundred is timing, and closes itself. The hundred is a dispute missing from our ledger: the disputes team posts it and decides whether to contest. The hundred and fifty that never settled: payments queries it and reverses our posting. And the double charge: payments posts it and refunds the customer today.",
 "N: Reconciling by totals is the most common silent failure in this round."])

qs("Interviewer · the second-level push", "“It's month-end, and the processor's report is two days late. Close is in two days.”", [
 "I: It's month-end, and the processor's report is two days late. Close is in two days.", "[pause: 2.0]"])

S(plain(K(6, "the second fix, and the honest limit"), "Close with documented open items", '<div class="cards c2">'
  '<div class="cd grn"><h3>Close on what is known</h3><p>The bank statement still reconciles against the ledger two ways. Card items wait as open timing breaks, listed with amounts and ages.</p></div>'
  '<div class="cd red"><h3>The honest limit</h3><p>A late file delays certainty, not the close. A file late three months running is a vendor problem for the contract owner.</p></div></div>'), [
 "C: Close on what is known. The bank statement still reconciles against the ledger two ways, and the card items wait as open timing breaks, listed with amounts and ages, signed off by finance. The honest limit: a late file delays certainty, not the close. And a file that is late three months running is a vendor problem, for whoever owns that contract."])

say_slide("“I never reconcile by totals. The ledger produces expectations, and the processor's report and the bank statement are matched line by line by reference; every difference is a typed break with an owner and an age.”", [
 "V: If asked, I'd say: I never reconcile by totals. I match the ledger, the processor and the bank line by line, by reference, and every difference is a typed break with an owner and an age.", "[pause: 1.0]",
 "N: Reconciliation catches a bad day after it happens. Next, the bad day itself."])

# ───────── Challenge 7 · processor down on the 1st ─────────
subchapter("7.7", "Challenge 7: The card processor is down on the 1st", ["N: Challenge seven. The worst morning: the card processor fails halfway through the window."])
qs("Interviewer · challenge 7 of 8", "“Eleven minutes past six on the first, the card processor goes down with sixty thousand charges left. What do you do?”", [
 "I: Eleven minutes past six on the first, the card processor goes down, with sixty thousand charges left. What do you do?", "[pause: 2.0]"])

S(dia(K(7, "the outage"), "Retry harder, or stop?", "ch7-attack", q=True, red=True,
      extra=strip(("case", "Naive answer", "“Keep retrying until it comes back.” Then: “Whatever failed is late tomorrow.”"),
                  ("case", "Break", "Blind retries turn an outage into thousands of unknowns, and late fees turn our outage into the customer's cost."))), [
 "C: The naive answer: keep retrying until it comes back, and whatever failed is late tomorrow. Look at the rails. Blind retries turn an outage into thousands of unknown outcomes, and the late fees turn our outage into the customer's cost."], cls="dia")

S(plain(K(7, "the trace"), "Our outage, their late fees", '<pre class="trace"><span class="t">06:00-06:11  </span>59,400 charged at 90 a second\n<span class="t">06:11        </span>processor down; 180 in flight: UNKNOWN\n<span class="t">06:11-06:20  </span>blind retries: <span class="bad">9,000 more timeouts, all UNKNOWN</span>\n<span class="t">09:00        </span>processor back; workers send everything at once: throttled again\n<span class="t">Dec 2        </span><span class="bad">60,000 late fees at $10 = $600,000 charged for our outage</span></pre>', q=True, red=True), [
 "C: The trace. From six to eleven past, fifty-nine thousand four hundred charged at ninety a second. Then the processor goes down with a hundred and eighty in flight, all unknown. Blind retries for nine minutes add nine thousand more timeouts, all unknown. At nine the processor is back, and the workers send everything at once and get throttled again. And on the second, sixty thousand late fees at ten dollars: six hundred thousand dollars charged to customers for our outage."])

S(dia(K(7, "the fix"), "Pause, resolve, protect the customer, resume slowly", "ch7-fix",
      extra=strip(("fixb", "Mechanism", "Pause the card rail. Resolve the 180 unknowns first. No late fee for our outage. Resume at 50 a second, then ramp."),
                  ("whyb", "Property", "S1: no blind resend. S3: no fee for our failure. L1: same-day resume."))), [
 "C: The fix, in order. A breaker opens and the rail switch pauses the card rail: no new attempts. The resolver clears the hundred and eighty unknowns first, before anything is sent again. Policy, agreed in advance: our outage is not your late fee, so the late clock runs from our attempt window, not from the due date. Then resume at fifty a second, and ramp up."], cls="dia")

S(plain(K(7, "the runbook"), "The worst morning, as a runbook", table(["Step", "Who", "Why"], [
  ["Pause the card rail", "on-call, one switch", "stop creating unknowns"],
  ["Resolve every UNKNOWN", "resolver, then payments", "know before resending anything"],
  ["Suppress late marks and fees", "policy, pre-agreed", "our outage is not the customer's fault"],
  ["Resume at 50 / s, ramp to 90", "on-call", "avoid a second throttle"],
  ["Tell customers", "notices", "say what happens next, before they ask"]], "bt sm") +
  line("Card tokens live at this processor: there is no quick failover for card customers.", "r")), [
 "C: As a runbook. Pause the card rail, with one switch, to stop creating unknowns. Resolve every unknown before resending anything. Suppress late marks and fees, under a policy agreed before the outage, not during it. Resume at fifty, and ramp to ninety. And tell customers what happens next, before they ask.",
 "C: Note what is missing: failover. The card tokens live at this processor, so I can't move card customers to another one this morning. Bank debit is a fallback only for customers with a debit mandate."])

qs("Interviewer · the second-level push", "“It stays down until three in the afternoon, past the bank's cut-off for any fallback.”", [
 "I: It stays down until three in the afternoon, past the bank's cut-off for any fallback.", "[pause: 2.0]"])

S(plain(K(7, "the second fix"), "Tomorrow is fine, if it's planned", '<div class="cards c2">'
  '<div class="cd grn"><h3>Collect tomorrow</h3><p>The day plan re-runs: the 60,000 join tomorrow’s card window. The grace period extends automatically for everyone affected.</p></div>'
  '<div class="cd amb"><h3>Longer term</h3><p>Network tokens that work across processors, and a second processor in the contract: a quarter of work, priced against a day like this.</p></div></div>'), [
 "C: Then collect tomorrow. The day plan re-runs, the sixty thousand join tomorrow’s card window, and the grace period extends automatically for everyone affected. Longer term, network tokens that work across processors, and a second processor in the contract. That is a quarter of work, and I'd price it against what a day like this costs."])

say_slide("“Pause the rail, resolve every unknown before sending anything, never charge a late fee for our outage, and resume under a lower limit. Then collect tomorrow if we must.”", [
 "V: If asked, I'd say: pause the rail, resolve every unknown before sending anything, never charge a late fee for our outage, and resume under a lower limit.", "[pause: 1.0]",
 "N: Every fix so far assumed someone noticed. Last, how you would know."])

# ───────── Challenge 8 · how would you know ─────────
subchapter("7.8", "Challenge 8: How would you know before month-end?", ["N: Challenge eight, observability. Finding the problem before finance finds it at close."])
qs("Interviewer · challenge 8 of 8", "“How would you know any of this is going wrong before finance finds it at month-end close?”", [
 "I: How would you know any of this is going wrong, before finance finds it at month-end close?", "[pause: 2.0]"])

S(dia(K(8, "silence"), "Green dashboards, missing money", "ch8-attack", q=True, red=True,
      extra=strip(("case", "Naive answer", "“API error rate and latency.”"),
                  ("case", "Break", "A file the bank half-rejects is a successful upload. Nothing on a server dashboard moves."))), [
 "C: The naive answer: error rate and latency. Look at the dispatcher and file ingest. A debit file that the bank half-rejects is still a successful upload. Nothing on a server dashboard moves."], cls="dia")

S(plain(K(8, "the trace"), "Twelve thousand debits that never left", '<pre class="trace"><span class="t">Dec 1 10:30  </span>debit file submitted, 480,000 entries; API errors 0 %\n<span class="t">Dec 1 11:00  </span>acknowledgement: <span class="bad">12,000 rejected</span> after an account-format change; nobody reads it\n<span class="t">Dec 2        </span>12,000 customers get late notices for payments we never sent\n<span class="t">Dec 30       </span><span class="bad">found by finance at close</span></pre>', q=True, red=True), [
 "C: The trace. At half past ten on the first, the debit file goes out with four hundred and eighty thousand entries. Zero errors. At eleven the bank's acknowledgement says twelve thousand were rejected, after a change in an account-number format, and nobody reads it. On the second, twelve thousand customers get late notices for payments we never sent. Finance finds it at close."])

S(dia(K(8, "the fix"), "Watch the money funnel and the files", "ch8-fix",
      extra=strip(("fixb", "Mechanism", "A funnel per rail: due → sent → acknowledged → settled. File acked by 11:00. UNKNOWN and breaks by age. Nightly invariants."),
                  ("whyb", "Property", "Alerts on what finance measures, four weeks earlier."))), [
 "C: The fix: indicators on the money. A funnel per rail per day: due, claimed, sent, acknowledged, settled, returned. A page if the file isn't acknowledged by eleven. Unknown count and age. Returns by reason code, against their baseline. Breaks by age and amount. And every night, a check that every transaction sums to zero, and every balance equals the sum of its lines."], cls="dia")

S(dia(K(8, "sequence"), "The funnel catches it at eleven", "seq-probe"), [
 "C: As a sequence. One: the file goes out with four hundred and eighty thousand entries. The acknowledgement, highlighted: twelve thousand rejected. Two: the probe feeds the funnel to monitoring. In red: acknowledged over sent is ninety-seven and a half percent, against a baseline of ninety-nine point nine. Page, at eleven, with three hours left before the cut-off to fix and resend."], cls="dia")

S(plain(K(8, "symptom pairs"), "Two metrics, one conclusion", table(["Metric A", "Metric B", "Conclusion"], [
  ["sent normal", "acknowledged down", "the bank rejected entries: read the file"],
  ["UNKNOWN up", "latency at the timeout", "the processor is slow"],
  ["unauthorised returns up", "one merchant or channel", "an authorisation-capture bug"],
  ["breaks up today", "returns ingest lagging", "ingest is stuck, not the money"],
  ["a transaction ≠ 0", "anything", "stop posting and page"]], "bt sm") +
  grade("Reading metrics in pairs is what turns a dashboard into a diagnosis. It is the start of the runbook for “collections look wrong”.")), [
 "C: Then read them in pairs. Sent normal, acknowledged down: the bank rejected entries, so read the file. Unknowns up with latency at the timeout: the processor is slow. Unauthorised returns up, concentrated on one merchant: we are capturing authorisations badly there. Breaks up today with return ingest lagging: ingest is stuck, not the money. And any transaction that doesn't sum to zero: stop posting and page.",
 "N: Pairs like these are the start of a real runbook."])

qs("Interviewer · the second-level push", "“A policy change misallocates four dollars on thirty thousand loans. Every transaction still sums to zero.”", [
 "I: A policy change misallocates four dollars on thirty thousand loans. Every transaction still sums to zero.", "[pause: 2.0]"])

S(plain(K(8, "the second fix"), "Test policy like code, and check the loan, not just the ledger", '<div class="cards c2">'
  '<div class="cd grn"><h3>Shadow a new policy version</h3><p>Run it over yesterday’s postings and diff the allocations before it goes live. Policy as data makes this a query, not a project.</p></div>'
  '<div class="cd grn"><h3>A per-loan invariant</h3><p>The remaining schedule sums to the outstanding principal, for every loan, every night. Balanced but wrong fails here.</p></div></div>'), [
 "C: Balanced but wrong needs two more checks. Shadow every new policy version over yesterday's postings and diff the allocations before it goes live; because policy is data, that is a query, not a project. And a per-loan invariant, every night: the remaining schedule sums to the outstanding principal. A misallocation that still balances fails right there."])

say_slide("“I watch the money, not the servers: a funnel from due to settled per rail, the file acknowledged by eleven, unknowns by age, returns by reason code, and breaks by age, plus nightly invariants on the ledger and on every loan.”", [
 "V: If asked, I'd say: I watch the money, not the servers. A funnel from due to settled per rail, the file acknowledged by eleven, unknowns and breaks by age, and nightly invariants on the ledger and every loan.", "[pause: 1.0]"])

# ───────────────────────── 8 · build cost ─────────────────────────
chapter(8, "Build cost", 6, "The manager layer: people, quarters, buy against build", [
 "N: This chapter is marked auxiliary. It is the engineering-manager layer, optional in a Staff round.",
 "C: Servicing is three releases, and the order matters more than the size."], aux=True)

S(plain("Build cost · the releases", "Card first, then the bank, then the proof", table(["Release", "Scope", "People × time", "Label"], [
  ["<b>V1</b>", "ledger with projections, schedules, the state machine, the card rail, resolver", "4 engineers × 2 quarters", "illustrative"],
  ["<b>V2</b>", "the bank-file rail, returns, policy as data, refunds and payoff", "6 engineers × 2 quarters", "illustrative"],
  ["<b>V3</b>", "three-way reconciliation, finance console, runbooks, due-date spreading", "two teams × 2 quarters, plus finance ops", "illustrative"]], "bt sm") +
  line("Buy against build: a servicing platform is the honest V0 for a small book with standard products.", "a")), [
 "C: Version one: the ledger with projections, schedules, the state machine, the card rail and the resolver. Four engineers for two quarters. Version two: the bank-file rail, returns, policy as data, refunds and payoff. Six engineers for two quarters. Version three: three-way reconciliation, the finance console, runbooks and due-date spreading. Two teams for two quarters, plus a finance operations function. All illustrative. And for a small book with standard products, buying a servicing platform is the honest version zero."], cls="aux")

S(plain("Build cost · the one-way doors", "Three decisions that outlive everyone in the room", '<div class="cards c3">'
  '<div class="cd red"><h3>The chart of accounts</h3><p>Seven years of lines and every auditor depend on it.</p></div>'
  '<div class="cd red"><h3>Terms versioning</h3><p>Loan contracts cite it. Old loans keep old rules forever.</p></div>'
  '<div class="cd red"><h3>The key format</h3><p>Shared with the processor; changing it breaks de-duplication.</p></div></div>'), [
 "C: Three one-way doors. The chart of accounts and the ledger schema: seven years of lines and every auditor depend on them. Terms versioning: contracts cite it, and old loans keep old rules forever. And the idempotency key format, which the processor shares. These get the most review. Everything else can change in a quarter."], cls="aux")

S(plain("Build cost · team seams", "Six owners, one writer to the ledger", table(["Team", "Owns", "Contract with the others"], [
  ["<b>Ledger</b>", "accounts, posting interface, invariants, close", "nobody else writes lines"],
  ["Collections and payments", "scheduler, rails, resolver, returns", "intents and the key format"],
  ["Servicing product", "refunds, payoff, hardship", "schedule versions"],
  ["Finance operations", "reconciliation tools, breaks", "break types and ageing"],
  ["Risk and legal", "retry rules, fees, allocation", "policy versions they approve"],
  ["Compliance", "debit authorisations, fee caps", "rules by state"]], "bt sm")), [
 "C: Six owners, and one writer to the ledger. The ledger team owns accounts, the posting interface, the invariants and the close, and nobody else writes lines. Collections and payments own the scheduler, rails, resolver and returns. Servicing product owns refunds, payoff and hardship. Finance operations own reconciliation. Risk and legal own retry rules, fees and allocation, as policy versions they approve. And compliance owns debit authorisations and fee caps."], cls="aux")

S(plain("Build cost · risks", "What would make this late or wrong", '<div class="cards c3">'
  '<div class="cd red"><h3>The return path is rarely tested</h3><p>Replay a month of real return files in staging before every release.</p></div>'
  '<div class="cd amb"><h3>Reconciliation built last</h3><p>Then the first close is done by hand, and breaks age unseen.</p></div>'
  '<div class="cd amb"><h3>One processor holds the tokens</h3><p>No failover for cards until network tokens are in place.</p></div></div>'), [
 "C: Three risks. The return path runs rarely, so it breaks quietly: replay a month of real return files in staging before every release. Reconciliation built last, so the first closes are done by hand. And one processor holding all the card tokens, so there is no failover until network tokens arrive."], cls="aux")

# ───────────────────────── 9 · recap ─────────────────────────
chapter(9, "Recap", 7, "One picture, five paths, the mistakes, the thesis", [
 "C: To close: one picture, one sentence per path, the mistakes to avoid, and the thesis."])

S(dia("Recap", "The whole design on one baseline", "base-final", chip=chips("ledger", "UNKNOWN · RETURNED", "rail budget", "policy", "three-way")), [
 "C: The whole design on one baseline. The servicing database with the ledger, intents and the outbox. The dispatcher with its rail budget, the day plan above it, and the rail switch. The resolver and file ingest beside the rails. Policy for terms and rules, the payoff quote at the A-P-I, reconciliation and finance operations at the bottom, and probes watching the funnel."], cls="dia")

S(plain("Recap · one sentence per path", "Five paths", table(["Path", "In one sentence"], [
  ["<b>Schedule</b>", "terms version in, schedule version and booking lines out, idempotent by loan"],
  ["<b>Collect</b>", "claim, intent and outbox in one commit; send under the rail budget with the key; UNKNOWN on timeout"],
  ["<b>Adjust</b>", "a transaction and a new schedule version; quotes list what is in flight"],
  ["<b>Returns</b>", "RETURNED, a reversal dated now, and policy decides any retry"],
  ["<b>Reconcile</b>", "line by line by reference, three ways, every break owned"]], "bt")), [
 "C: One sentence per path. Schedule: a terms version in, a schedule version and booking lines out. Collect: claim, intent and outbox in one commit, then send under the rail budget with the key, and unknown on a timeout. Adjust: a transaction and a new schedule version, and quotes that list what is in flight. Returns: a state, a reversal dated now, and policy decides any retry. Reconcile: line by line, three ways, every break owned."])

S(plain("Recap · common mistakes in this round", "What costs candidates the most", '<div class="cards c2">'
  '<div class="cd red"><h3>On correctness</h3><p>A balance column. Retry on any error with a new key. Settled treated as final. Refunds that leave the schedule alone. Floats.</p></div>'
  '<div class="cd red"><h3>On operations</h3><p>“Thundering herd” and a broker for 42 a second. A midnight burst. Reconciling by totals. Late fees for our outages. No owner for policy.</p></div></div>'), [
 "C: The common mistakes. On correctness: a balance column, retrying with a new key, treating settled as final, refunds that leave the schedule alone, and floats. On operations: calling forty-two a second a thundering herd, a midnight burst, reconciling by totals, charging late fees for our own outages, and nobody owning the policy. The same shapes appear in subscription billing, wallets and payroll, under other names."])

S(plain("Recap · the four sentences", "If you have thirty seconds", '<div class="cards c2">'
  '<div class="cd"><h3>What</h3><p>A double-entry ledger with immutable lines; a state machine with UNKNOWN and RETURNED; keys at three layers.</p></div>'
  '<div class="cd amb"><h3>The pace</h3><p>The database is the queue; a budget per rail and the cut-off shape the day.</p></div>'
  '<div class="cd red"><h3>The risk</h3><p>Returns and unknowns are rare paths; test them with real files.</p></div>'
  '<div class="cd grn"><h3>The proof</h3><p>Three-way reconciliation every day, an owner for every break.</p></div></div>'), [
 "C: If I had thirty seconds. Money lives in a double-entry ledger with immutable lines, and each payment is a state machine with unknown and returned, with keys at three layers. The database is the queue, and a budget per rail and the bank's cut-off shape the day. Returns and unknowns are rare paths, so I test them with real files. And every day the books are reconciled three ways, with an owner for every break."])

key("The thesis, again", "Correctness over months, not throughput: <em>immutable lines</em>, <em>unknown</em> and <em>returned</em> as states, the <em>rail</em> as the limit, and <em>three-way</em> proof every day.", [
 "V: Loan servicing is about correctness over months, not throughput. Lines that never change, unknown and returned as ordinary states, the rail as the limit, and a three-way proof every day that our books match the bank's.", "[pause: 1.5]"])
