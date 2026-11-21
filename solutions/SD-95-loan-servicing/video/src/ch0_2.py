from dsl import *

# ───────────────────────── 0 · cold open ─────────────────────────
chapter(0, "Cold open", -1, "Design the system that services instalment loans for their whole life", [
 "C: Six hundred thousand repayments are due on the first of the month. Most people hear that and reach for a message broker, because it sounds like a thundering herd. It isn't. It is about forty a second, and any database absorbs that. This question is hard somewhere else entirely: in money that moves in days, and can come back weeks after everyone thought it was done."])

qs("Interviewer · the prompt", "“Loans are created elsewhere. Design the system that services them for their whole life: it schedules repayments, collects them by bank debit or card, handles refunds, late fees and early payoff, and reconciles with the bank.”", [
 "I: Loans are created elsewhere. Design the system that services them for their whole life. It schedules repayments, collects them by bank debit or card, handles refunds, late fees and early payoff, and reconciles with the bank.", "[pause: 1.5]"])

S(dia("Why it is harder than it looks", "When is a collection final? Later than the dashboard thinks", "truth",
      chip=chips("seconds", "1–2 days", "2 bank days", "60 days", "months", "7 years")), [
 "C: Here is the hook as a timeline. A card charge answers in seconds, or not at all. A bank debit settles in a day or two, and the dashboard calls it settled. But a debit can come back for insufficient funds two banking days later, and as unauthorised up to sixty days later. Merchants refund months into a loan. And every cent has to be explained for seven years.",
 "C: So the design is not about speed. It is about being correct over months, while the truth about each payment keeps arriving. I'll put one mechanism at each point on this line."], cls="dia")

S(plain("Before the design", "What this question grades", table(["Axis", "Weak signal", "Strong signal"], [
  ["<b>Requirements</b>", "“Charge everyone on the due date”", "Asks the rails, their limits and cut-offs, refunds, returns and audit length; says what must never happen"],
  ["<b>Correctness</b>", "A balance column; retry on any error; settled means done", "Double entry with reversals; idempotency at three layers; UNKNOWN and RETURNED as states"],
  ["<b>Trade-offs</b>", "“A message broker for the thundering herd”", "42 a second is nothing; the processor contract and the bank cut-off bind; the broker is optional"],
  ["<b>Depth</b>", "Stops at “retry with backoff”", "Claim with SKIP LOCKED, intent and outbox in one commit; a budget per rail; re-presentment limits; the allocation waterfall"],
  ["<b>Operations</b>", "API uptime", "UNKNOWN age, the debit file acknowledged, returns by reason code, breaks by age and amount, a ledger that sums to zero"]], "bt sm sig") +
  grade("The sentence that separates candidates: settled is not final for a bank debit. Say it before the interviewer does.")), [
 "N: Five axes. The weak answer is a cron job, a balance column and a retry loop. The strong answer names where the real limits are, and treats unknown and returned as ordinary states.",
 "C: I'll keep one sentence in front of everything: settled is not final for a bank debit. Most of the design follows from taking that seriously."])

key("The thesis", "Throughput is never the problem here; <em>correctness over months</em> is. An <em>immutable</em> double-entry ledger, a state machine that admits <em>unknown</em> and <em>returned</em>, a scheduler bounded by the <em>rail</em>, and a daily <em>three-way reconciliation</em>.", [
 "V: In loan servicing, throughput is never the problem; correctness over months is. So the design is an immutable double-entry ledger, a payment state machine that admits unknown and returned, a scheduler bounded by the rail, and a daily three-way reconciliation.", "[pause: 1.0]",
 "C: Concretely: ledger lines that are never edited, with balances as a projection. Idempotency keys at three layers. A day planned backwards from the bank's cut-off. And every morning, a check that our books agree with the processor's and the bank's, with an owner for every difference."])

S(plain("The order I will follow", "Scope, numbers, theory, a simple design, then I break it",
  '<div class="ribbon" style="margin-top:14pt">' + "".join(f"<span>{x}</span>" for x in STAGES) + '</div>' +
  '<div class="cards c3" style="margin-top:18pt"><div class="cd"><h3>First</h3><p>Requirements and scope. Numbers. A short theory chapter.</p></div>'
  '<div class="cd grn"><h3>Then</h3><p>API and data. A design in three versions, each answering the one before.</p></div>'
  '<div class="cd red"><h3>Most of the time</h3><p>Eight challenges that break the design. A build cost. A recap.</p></div></div>'), [
 "C: The order. Requirements and scope, then the numbers, then a short theory chapter the design can lean on. Then the A-P-I and the data model, and a design in three versions, each one answering the objection to the one before.",
 "C: Most of the time goes to eight challenges that break the design, in an order where each fix creates the next question. Then a build cost, and a recap."])

# ───────────────────────── 1 · requirements ─────────────────────────
chapter(1, "Requirements and scope", 0, "Ask first. Cut on purpose. Put numbers on it.", [
 "C: Before I draw anything, seven questions. Each answer changes the design, and I'll say how."])

def clar(n, q, a, say):
    S(f'<div class="who">Clarifying question {n} of 7</div><div class="qq">{q}</div><div class="ans">{a}</div>', say, cls="qs")

clar(1, "How big is the portfolio?", "5 million active loans, 3 to 12 monthly instalments each.", [
 "C: How big is the portfolio?",
 "I: Five million active loans, with three to twelve monthly instalments each.",
 "C: So about five million collections a month, and each loan lives up to a year. Long enough for every slow failure in this domain to happen."])
clar(2, "Which rails do we collect on?", "Bank debit for 80 %, card for 20 %. Card numbers are tokens at the processor.", [
 "C: Which payment rails do we collect on?",
 "I: Bank debit for eighty percent, card for twenty. Card numbers are stored as tokens at the processor.",
 "C: Two rails that behave very differently. A card answers in seconds. A bank debit answers in days and can be returned weeks later. And because the tokens live at the processor, I can't move card customers to another processor in a hurry. That will matter on the worst day."])
clar(3, "When are payments due?", "Due dates cluster. 600,000 collections fall on the 1st.", [
 "C: Are due dates spread across the month?",
 "I: No. They cluster. Six hundred thousand collections fall on the first.",
 "C: Then I need to plan one day very carefully. I'll size it in a minute, and I suspect it is smaller than it sounds."])
clar(4, "What limits do the rails impose?", "The card processor's contract allows 100 a second. Bank debit files have a daily cut-off: take 14:00.", [
 "C: What limits do the rails put on us?",
 "I: The card processor's contract allows a hundred requests a second. Bank debit files have a daily cut-off. Take two in the afternoon.",
 "C: That is the most important answer so far. The limit is not my database. It is a contract, and a clock on the bank's side."])
clar(5, "Refunds?", "Merchants refund in full or in part, at any point in the loan.", [
 "C: How do refunds work?",
 "I: Merchants refund in full or in part, at any point during the loan.",
 "C: So a refund changes a schedule under a live loan, possibly while a payment is in flight. The terms have to say what happens."])
clar(6, "Audit and close?", "Every cent explained for seven years. Month-end close in two days.", [
 "C: What are the audit requirements?",
 "I: Every cent explained for seven years, and the month-end close done in two days.",
 "C: Explained means a balance is a sum of records nobody edits. And a two-day close means differences have to be found daily, not at the end of the month."])
clar(7, "What must never happen, in order?", "Your call. I'll tell you if I disagree.", [
 "C: What must never happen, in priority order? I'd propose: first, charging a customer twice for one instalment. Second, a cent we can't explain. Third, penalising a customer for our own failure. Lateness comes after all three.",
 "I: Your call. I agree with that order.",
 "C: That order settles arguments later. When speed and correctness conflict, correctness wins, and a collection can wait a day."])

S(plain("Requirements · functional", "Five things the system must do", '<div class="cards c3">'
  '<div class="cd"><h3>FR1 · Schedule</h3><p>A booked loan becomes a schedule of instalments, from its terms version.</p></div>'
  '<div class="cd"><h3>FR2 · Collect</h3><p>On each due date, collect by bank debit or card. Retries and late fees follow policy.</p></div>'
  '<div class="cd amb"><h3>FR3 · Adjust</h3><p>Refunds, extra payments, early payoff. Re-amortise or shorten, per the terms.</p></div>'
  '<div class="cd red"><h3>FR4 · Absorb returns</h3><p>A debit returned days or weeks later reverses a collection.</p></div>'
  '<div class="cd grn"><h3>FR5 · Reconcile</h3><p>Ledger against processor against bank, every day. Month-end close in two days.</p></div></div>'), [
 "C: Functionally, five things. One, schedule: a booked loan becomes a schedule of instalments, from a versioned set of terms. Two, collect: on each due date, by bank debit or card, with retries and late fees as policy says. Three, adjust: refunds, extra payments and early payoff, which re-amortise the loan or shorten it, as the terms say.",
 "C: Four, absorb returns: a debit that comes back days or weeks later reverses a collection. Five, reconcile: our ledger against the processor and the bank, every day. Each of these gets a numbered flow later."])

S(plain("Requirements · non-functional", "The promises, as numbers", '<p class="chips">initial targets, not measurements</p><div class="tiles" style="--n:4">'
  '<div class="tile"><b>0</b><span>customers charged twice for one instalment</span></div>'
  '<div class="tile"><b>0</b><span>unexplained differences at close</span></div>'
  '<div class="tile blue"><b>10:30</b><span>debit file submitted, cut-off 14:00</span></div>'
  '<div class="tile blue"><b>1 h</b><span>an unknown outcome resolved, for 99 %</span></div></div>'), [
 "C: The promises, all initial targets. Zero customers charged twice for one instalment. Zero unexplained differences at month-end. The day's debit file submitted by half past ten, with the cut-off at two, so a failed submission still has time to be fixed. Ninety-nine percent of unknown outcomes resolved within an hour. And every ledger line kept, and explainable, for seven years."])

S(plain("Requirements · scope", "In scope, out of scope", chips("schedule", "collect", "adjust", "returns", "reconcile") +
  '<div class="scope2"><div class="in"><h3>In scope</h3><ul><li>Schedules and terms versions</li><li>Bank debit and card collections, retries, returns</li><li>Refunds, late fees, early payoff</li><li>The ledger and reconciliation</li><li>Customer notices, as events</li></ul></div>'
  '<div class="out"><h3>Out of scope, on purpose</h3><ul><li>Origination and underwriting (SD-82)</li><li>Collections agencies; hardship beyond a pause flag</li><li>Statement design, tax reporting</li><li>Payouts to merchants (SD-81)</li><li>Funding and selling loans</li></ul></div></div>'), [
 "C: In scope: schedules, both rails with their retries and returns, refunds, late fees, early payoff, the ledger, reconciliation, and notices to customers as events.",
 "C: Out of scope, said aloud. Origination and underwriting, which is its own question. Outside collections agencies, and hardship programmes beyond a simple pause flag. Statement design and tax reporting. Paying merchants. And how the loans are funded or sold. Each of those consumes our events, but none of them changes the core."])

key("The core is four things", "A ledger that is <em>never edited</em>, a payment state machine with <em>UNKNOWN</em> and <em>RETURNED</em>, a scheduler bounded by the <em>rail</em>, and <em>reconciliation</em> against the outside.", [
 "C: So the core is four things. A ledger that is never edited. A payment state machine with unknown and returned in it. A scheduler whose limit is the rail. And reconciliation against the outside world. Everything else serves those four."])

# ───────────────────────── 2 · estimates ─────────────────────────
chapter(2, "Estimates", 1, "Every number is arithmetic, and every number changes something", [
 "C: Numbers next. Each is arithmetic from what the interviewer said, carries a label, and ends with the decision it drives. I'll say it once for the chapter: the rates and amounts are illustrative, not any company's figures."])

S(plain("Estimates · 1 of 8 · the busy day", "Six hundred thousand is forty-two a second", table(["Quantity", "Arithmetic", "Label"], [
  ["Collections on the 1st", "<b>600,000</b>", "given"],
  ["Spread over four hours", "600,000 ÷ (4 × 3,600 s) ≈ <b>42 / s</b>", "derived"],
  ["One relational primary", "thousands of small transactions a second", "fact"]], "bt") +
  line("The database can be the queue. A message broker is not needed for load.", "a")), [
 "C: Six hundred thousand collections, spread over four hours: six hundred thousand divided by fourteen thousand four hundred seconds. About forty-two a second.",
 "C: Decision: that is nothing for one relational database. The database can be the work queue, and a message broker is not needed for load. If I add one later, it is for another reason."])

S(plain("Estimates · 2 of 8 · the card rail", "The contract, not the database, sets the pace", table(["Quantity", "Arithmetic", "Label"], [
  ["Card share", "600,000 × 20 % = <b>120,000</b>", "derived"],
  ["At the contract limit", "120,000 ÷ 100 / s = 1,200 s = <b>20 min</b>", "derived"],
  ["At 90 % of it", "120,000 ÷ 90 / s ≈ <b>22 min</b>", "initial target"]], "bt") +
  line("A token bucket per rail, below the contract. The card window is a plan, not a burst.", "a")), [
 "C: Twenty percent of six hundred thousand is a hundred and twenty thousand card charges. At the contract's hundred a second, twenty minutes at the very least. I'd run at ninety a second, to leave headroom for retries and queries: about twenty-two minutes.",
 "C: Decision: a token bucket per rail, set below the contract. The card window is something we plan, not a burst we hope survives."])

S(plain("Estimates · 3 of 8 · the bank rail", "One file, one cut-off", table(["Quantity", "Arithmetic", "Label"], [
  ["Bank debits", "600,000 × 80 % = <b>480,000</b>", "derived"],
  ["File size", "480,000 × 94 B ≈ <b>45 MB</b>", "illustrative fixed-width record"],
  ["Cut-off", "<b>14:00</b>", "given"]], "bt") +
  line("A batch built hours early, validated, submitted, and acknowledged before anyone relaxes.", "a")), [
 "C: The other four hundred and eighty thousand are bank debits. They don't go one by one: they go in a file. At about ninety-four bytes a record, forty-five megabytes.",
 "C: Decision: the file is a batch, built hours before the cut-off, validated, submitted, and only done when the bank acknowledges it. A missed cut-off moves half a million collections by a day."])

S(plain("Estimates · 4 of 8 · money at stake", "Why correctness beats speed", table(["Quantity", "Arithmetic", "Label"], [
  ["Average instalment", "$1,200 loan ÷ 8 = <b>$150</b>", "illustrative"],
  ["Collected on the 1st", "600,000 × $150 ≈ <b>$90 M</b>", "derived"],
  ["A 0.1 % error", "$90 M × 0.001 = <b>$90 k</b>", "derived"]], "bt") +
  line("Being a day late costs a little. Being wrong by a tenth of a percent costs ninety thousand dollars and trust.", "a")), [
 "C: Money. Say the average instalment is a hundred and fifty dollars: a twelve-hundred dollar loan in eight payments. Six hundred thousand of them is about ninety million dollars on the first. A tenth of a percent wrong is ninety thousand dollars, and a lot of angry customers.",
 "C: Decision: correctness beats speed. Being a day late is cheap. Being wrong is not."])

S(plain("Estimates · 5 of 8 · returns", "Returns are a workload, not an exception", table(["Quantity", "Arithmetic", "Label"], [
  ["Insufficient-funds rate", "say 3 % of debits", "illustrative"],
  ["Returns from the 1st", "480,000 × 0.03 ≈ <b>14,400</b>, on days 2 and 3", "derived"],
  ["Unauthorised returns", "a trickle, for 60 days", "illustrative"]], "bt") +
  line("A return file pipeline with its own owner, states and dashboards.", "a")), [
 "C: Returns. Say three percent of bank debits come back for insufficient funds. That is fourteen thousand four hundred returns from the first alone, arriving on the second and third days. Plus a trickle of unauthorised returns for sixty days after that.",
 "C: Decision: returns are a daily workload with their own pipeline and owner, not an exception handler."])

S(plain("Estimates · 6 of 8 · unknown outcomes", "Small in number, each one a possible double charge", table(["Quantity", "Arithmetic", "Label"], [
  ["Card timeouts", "say 0.2 % of charges", "illustrative"],
  ["On the 1st", "120,000 × 0.002 ≈ <b>240</b>", "derived"]], "bt") +
  line("A resolver that ends every unknown by asking, never by guessing.", "a")), [
 "C: Unknown outcomes. Say two in a thousand card charges time out. On the first that is about two hundred and forty. Small, but every one of them is a customer who might have been charged, and might be charged again if we guess.",
 "C: Decision: a resolver service that ends every unknown by asking the processor, never by guessing."])

S(plain("Estimates · 7 of 8 · ledger size", "Hundreds of gigabytes, not petabytes", table(["Quantity", "Arithmetic", "Label"], [
  ["Lines per loan per month", "collection 2 + month-end accrual 2 = <b>4</b>", "illustrative"],
  ["Lines a month", "5 M × 4 = <b>2 × 10⁷</b>", "derived"],
  ["Seven years", "2 × 10⁷ × 84 × 200 B ≈ <b>340 GB</b>", "derived"]], "bt") +
  line("One relational database, partitioned by month. No sharding. Old partitions archived read-only.", "a")), [
 "C: The ledger's size. About four lines per loan per month: two for the collection, two for the interest accrued at month-end. Five million loans: twenty million lines a month. Over eighty-four months, at two hundred bytes a line, about three hundred and forty gigabytes.",
 "C: Decision: that fits one well-run relational database, partitioned by month. No sharding. I keep real transactions and real constraints, which is exactly what a ledger needs."])

S(plain("Estimates · 8 of 8 · interest", "Accrue by calculation, not by daily lines", table(["Quantity", "Arithmetic", "Label"], [
  ["Daily accrual lines", "5 M × 30 days × 2 = <b>3 × 10⁸ a month</b>", "derived"],
  ["Posted at events and month-end", "5 M × 2 = <b>10⁷ a month</b>", "derived"]], "bt") +
  grade("A candidate who notices that daily accrual lines would multiply the ledger by fifteen, and computes accrual instead, is showing the depth this round looks for.")), [
 "C: One trap. Posting interest every day would be five million loans, times thirty days, times two lines: three hundred million lines a month. Fifteen times the ledger, for no information.",
 "C: So interest is accrued by calculation, from the balance and the rate, and posted when something happens: a payment, a payoff, a refund, and month-end.",
 "N: Noticing that, unprompted, is the kind of depth this round looks for.",
 "C: That is the numbers. Next, theory."])
