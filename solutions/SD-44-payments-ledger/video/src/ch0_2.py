from dsl import *

# ───────────────────────── 0 · cold open ─────────────────────────
chapter(0, "Cold open", -1, "Design payment processing and the double-entry ledger", [
 "C: The happy path of a payment is three boxes and a database. A merchant asks, we call the bank, we write it down. This question is not about the happy path. It is about the other paths: a bank call that times out and leaves you not knowing whether the customer paid, a client that retries the same payment three times at once, and a statement that disagrees with your books."])

qs("Interviewer · the prompt", "“Design the system that takes a payment and records it: the ledger the company's money is accounted for in.”", [
 "I: Design the system that takes a payment and records it. The ledger the company's money is accounted for in.", "[pause: 1.5]"])

S(dia("Why it is harder than it looks", "The truth arrives over months; the answer is due in two seconds", "truth",
      chip=chips("2 s", "minutes", "next day", "months")), [
 "C: Here is the hook, as a timeline. The merchant wants an answer in two seconds. But the truth about a payment arrives over months. The processor's answer comes in about a second, or not at all. An inquiry can settle an unknown outcome in minutes. The settlement file with the processor's own books arrives the next day. And a dispute can still arrive months later.",
 "C: Every strong answer to this question is a design for not knowing yet. The rest of this video puts one mechanism at each point on this line."], cls="dia")

S(plain("Before the design", "What this question grades", table(["Axis", "Weak signal", "Strong signal"], [
  ["<b>Requirements</b>", "“Charge the card and store it”", "Asks what must never happen, in order; how the outside parties fail; refunds, disputes, audit"],
  ["<b>Correctness</b>", "A balance column, “retries are safe”, floats", "Double entry, derived balances, an idempotency key inserted first, integer minor units"],
  ["<b>Trade-offs</b>", "“A distributed transaction with the bank”", "Says why that is unavailable; picks a state machine with an unknown state and says what it costs"],
  ["<b>Depth</b>", "“Retry with backoff”", "Timeout walk: unknown, inquiry by our reference, reversal, settlement file; outbox; hot account"],
  ["<b>Operations</b>", "API uptime", "Unknown count and age, approval rate per processor, a ledger that must sum to zero, breaks by age"]], "bt sm sig") +
  grade("The one sentence that separates candidates: exactly-once does not exist across the bank boundary. Say it, then design around it.")), [
 "N: Five axes. The weak signal is a balance column and a retry loop. The strong signal is a precise statement of what cannot be guaranteed, and a design that is honest about it.",
 "C: I'll keep one sentence in front of everything: exactly-once does not exist across a network boundary. Everything I build is a way of living with that."])

key("The thesis", "At-least-once delivery, <em>one effect per intent</em>, a state for <em>not knowing yet</em>, and a <em>reconciliation</em> that finds what the rest missed, on an append-only double-entry journal.", [
 "V: Exactly-once does not exist across a network boundary. So the design is at-least-once delivery, one effect per intent, a state for we don't know yet, and a reconciliation that finds what the rest missed. All of it written to an append-only double-entry journal, where a balance is a sum, never a field.", "[pause: 1.0]",
 "C: Concretely: an idempotency key that is inserted before anything happens. An explicit state machine with an unknown state. Immutable journal entries. And a daily match against the processor's books, with owners for every difference."])

S(plain("The order I will follow", "Scope, numbers, theory, a simple design, then I break it",
  '<div class="ribbon" style="margin-top:14pt">' + "".join(f"<span>{x}</span>" for x in STAGES) + '</div>' +
  '<div class="cards c3" style="margin-top:18pt"><div class="cd"><h3>First</h3><p>Requirements and scope. Numbers. A short theory chapter.</p></div>'
  '<div class="cd grn"><h3>Then</h3><p>API and data. A high-level design in three versions, each answering the one before.</p></div>'
  '<div class="cd red"><h3>Most of the time</h3><p>Eight challenges that break the design. A build cost. A recap.</p></div></div>'), [
 "C: The order. Requirements and scope, then numbers, then a short theory chapter the design can lean on. Then the A-P-I and data model, and a design in three versions, each answering the objection to the one before.",
 "C: Then most of the time goes to eight challenges that break the design, where each fix creates the next question. A build cost, and a recap."])

# ───────────────────────── 1 · requirements ─────────────────────────
chapter(1, "Requirements and scope", 0, "Ask first. Cut on purpose. Put numbers on it.", [
 "C: Before I draw anything, seven questions. Each answer changes the design."])

def clar(n, q, a, say):
    S(f'<div class="who">Clarifying question {n} of 7</div><div class="qq">{q}</div><div class="ans">{a}</div>', say, cls="qs")

clar(1, "What volume?", "10,000 payments a second at peak, in 50 currencies.", [
 "C: What volume are we designing for?",
 "I: Ten thousand payments a second at peak, in fifty currencies.",
 "C: Ten thousand a second is a lot of journal writes, and fifty currencies means every amount carries its currency. I'll size both."])
clar(2, "How fast must the client get an answer?", "An authorisation decision within 2 seconds.", [
 "C: How fast must the client get an answer?",
 "I: An authorisation decision within two seconds.",
 "C: And most of those two seconds belong to the processor, not to us. So our own part has to be small, and we need a plan for when the processor uses all of it."])
clar(3, "Who actually moves the money?", "Card networks and banks, through processors. They time out, return ambiguous results, and sometimes go down for hours.", [
 "C: Who actually moves the money?",
 "I: Card networks and banks, through processors. They time out, return ambiguous results, and sometimes go down for hours.",
 "C: That is the most important answer. Ambiguous results mean a state for not knowing. Hours of outage mean a second processor and rules for when it is safe to use it."])
clar(4, "What is the ledger's rule?", "It must always balance. No exceptions.", [
 "C: What is the ledger's rule?",
 "I: It must always balance. No exceptions.",
 "C: Then every movement is written as entries that sum to zero, in one transaction, and a check that it still sums to zero runs all the time."])
clar(5, "How long must it be auditable?", "Every balance explainable from immutable records for seven years.", [
 "C: How long must the books be explainable?",
 "I: Every balance explainable from immutable records, for seven years.",
 "C: Immutable and explainable rules out a balance column that is updated in place. A balance becomes a sum over records."])
clar(6, "Refunds and disputes?", "Partial refunds, full refunds and chargebacks, arriving days or months later.", [
 "C: Refunds and disputes?",
 "I: Partial and full refunds, and chargebacks, arriving days or months later.",
 "C: Months later means the original period may be closed. So corrections are new records dated when they happen, never edits."])
clar(7, "What must never happen, in order?", "Your call. I'll tell you if I disagree.", [
 "C: What must never happen, in priority order? I'd propose: first, charging a customer twice or losing money. Second, an unbalanced ledger. Third, a slow payment.",
 "I: Your call. I agree with that order.",
 "C: That order settles a lot. When I have to choose between a fast answer and a correct one, I answer pending."])

S(plain("Requirements · functional", "Five things the system must do", '<div class="cards c3">'
  '<div class="cd"><h3>FR1 · Pay</h3><p>Authorise and capture a payment, automatic or manual capture. Idempotent per client key.</p></div>'
  '<div class="cd"><h3>FR2 · Adjust</h3><p>Void, partial or full refund, chargeback. Each references the original payment.</p></div>'
  '<div class="cd amb"><h3>FR3 · Notify</h3><p>Every state change reaches the merchant, as a signed webhook, and internal consumers.</p></div>'
  '<div class="cd"><h3>FR4 · Reconcile</h3><p>Match our books against each processor’s settlement file daily. Every difference becomes an owned break.</p></div>'
  '<div class="cd grn"><h3>FR5 · Explain</h3><p>Any account’s balance at any time, from the journal.</p></div></div>'), [
 "C: Functionally, five things. One, pay: authorise and capture, idempotent per client key. Two, adjust: void, refund, and chargeback, each referencing the original payment. Three, notify: every state change reaches the merchant as a signed webhook.",
 "C: Four, reconcile: match our books against each processor's settlement file every day, and turn every difference into a break with an owner. Five, explain: any account's balance at any time, from the journal. Each of these gets a numbered flow later."])

S(plain("Requirements · non-functional", "The numbers, and what each is for", '<p class="chips">all initial targets, not measurements</p><div class="tiles" style="--n:4">'
  '<div class="tile"><b>0</b><span>double charges, ever</span></div>'
  '<div class="tile blue"><b>&lt; 2 s</b><span>decision at p99, or an honest “pending”</span></div>'
  '<div class="tile blue"><b>15 min</b><span>an unknown outcome resolved, for 99 %</span></div>'
  '<div class="tile"><b>1 day</b><span>every break found and owned</span></div></div>'), [
 "C: The numbers, all initial targets. Zero double charges. A decision within two seconds at the ninety-ninth percentile, or an honest pending. Ninety-nine percent of unknown outcomes resolved within fifteen minutes. Every difference with the processor found and owned within a day. Plus: every journal transaction balanced at commit, and seven years of retention."])

S(plain("Requirements · scope", "In scope, out of scope", chips("authorise", "capture", "refund", "chargeback", "reconcile") +
  '<div class="scope2"><div class="in"><h3>In scope</h3><ul><li>Authorise, capture, void, refund, chargeback</li><li>Webhooks to merchants</li><li>The double-entry ledger</li><li>Daily reconciliation</li><li>Amounts in 50 currencies, no conversion</li></ul></div>'
  '<div class="out"><h3>Out of scope, on purpose</h3><ul><li>Fraud scoring: a service we call (SD-43)</li><li>Card data: a tokenisation service</li><li>FX pricing (SD-80)</li><li>Merchant onboarding and KYC (SD-78)</li><li>Payouts to merchants (SD-81)</li></ul></div></div>'), [
 "C: In scope: authorise, capture, void, refund and chargeback, webhooks, the ledger, reconciliation, and amounts in fifty currencies without conversion.",
 "C: Out of scope, on purpose. Fraud scoring is a service I call. Card numbers live in a tokenisation service, which keeps most of the card-data compliance scope away from us. Currency conversion, merchant onboarding and payouts are their own questions, though payouts will come back twice, because they need a balance check."])

key("The core is four things", "A <em>state machine</em> that admits “unknown”, an <em>idempotent</em> API, an <em>immutable</em> double-entry journal, and <em>reconciliation</em> against the outside world.", [
 "C: So the core is four things. A state machine for each payment that admits unknown. An idempotent A-P-I. An immutable double-entry journal. And reconciliation against the outside world. Everything else is in service of those four."])

# ───────────────────────── 2 · estimates ─────────────────────────
chapter(2, "Estimates", 1, "Every number is arithmetic, and every number changes something", [
 "C: Numbers next. Each one is arithmetic from what the interviewer said, carries a label, and ends with the decision it drives. I'll say it once for this chapter: these are illustrative, not measured."])

S(plain("Estimates · 1 of 8 · write rate", "Forty thousand journal entries a second", table(["Quantity", "Arithmetic", "Label"], [
  ["Payments at peak", "<b>10,000 / s</b>", "given"],
  ["Entries per payment", "about 4: the capture legs and the fee", "illustrative"],
  ["Journal writes", "10,000 × 4 = <b>40,000 entries / s</b>", "derived"]], "bt") +
  line("One database primary will not take it at peak: partition the journal by account.", "a")), [
 "C: Ten thousand payments a second, and each capture writes about four journal entries: the receivable, the merchant's share, the fee. Forty thousand entries a second at peak.",
 "C: Decision: one database primary will not take that at peak. The journal is partitioned by account, and a payment's entries go to the partitions of the accounts they touch."])

S(plain("Estimates · 2 of 8 · daily volume", "Three hundred million payments a day", table(["Quantity", "Arithmetic", "Label"], [
  ["Average rate", "peak ÷ 3 ≈ <b>3,300 / s</b>", "illustrative"],
  ["Per day", "3,300 × 86,400 ≈ <b>2.9 × 10⁸</b>", "derived"]], "bt") +
  line("This sizes the settlement files and the reconciliation job.", "a")), [
 "C: The average is lower. Say a third of the peak: about three thousand three hundred a second. Times eighty-six thousand four hundred seconds, that is about two hundred and ninety million payments a day.",
 "C: Decision: the daily settlement files will have hundreds of millions of lines. Reconciliation is a batch job sized for that, not a spreadsheet."])

S(plain("Estimates · 3 of 8 · seven years", "About six hundred terabytes, and it never shrinks", table(["Quantity", "Arithmetic", "Label"], [
  ["Seconds in a year", "≈ 3.15 × 10⁷", "fact"],
  ["Entries in 7 years", "3,300 × 3.15 × 10⁷ × 7 × 4 ≈ <b>2.9 × 10¹²</b>", "derived"],
  ["At ~200 B each", "≈ <b>580 TB</b>", "illustrative"]], "bt") +
  line("Hot recent partitions plus a cold archive. Immutability makes archiving a copy, not a migration.", "a")), [
 "C: Seven years. Three thousand three hundred a second, times seconds in a year, times seven, times four entries: about two point nine trillion entries. At two hundred bytes each, about five hundred and eighty terabytes.",
 "C: Decision: recent partitions stay hot, older ones move to a cold archive. Because entries never change, archiving is a copy, not a migration."])

S(dia("Estimates · 4 of 8 · the hot account", "One merchant, one balance row", "hot", chip=chips("5,000 / s", "≈ 670 / s per row lock", "illustrative")), [
 "C: The number that shapes the data model. One large merchant receives five thousand payments a second. If each payment updates that merchant's balance row, each update holds a row lock for about one and a half milliseconds. That allows about six hundred and seventy updates a second on one row.",
 "C: The queue grows by over four thousand a second, and within a second that merchant's payments are past two seconds. Decision: payments append entries, and the balance is derived. Where a check needs the balance now, I'll split the account. That is challenge four."], cls="dia")

S(dia("Estimates · 5 of 8 · the latency budget", "Two seconds, and the processor has most of them", "budget", chip=chips("initial targets")), [
 "C: The two-second budget. Our own work: the idempotency insert, a fraud call of about fifty milliseconds, two commits, and the post-commit write. About ninety milliseconds together. The processor, at its ninety-ninth percentile, about one and a half seconds. That leaves about four hundred spare.",
 "C: Decision: everything we own stays under a hundred milliseconds. And at one point nine seconds, if the processor has not answered, we answer pending and keep waiting."], cls="dia")

S(plain("Estimates · 6 of 8 · unknown outcomes", "Ten unknowns a second is a real workload", table(["Quantity", "Arithmetic", "Label"], [
  ["Timeouts", "say 0.1 % of authorisations", "illustrative"],
  ["At peak", "0.001 × 10,000 = <b>10 / s</b>", "derived"],
  ["Per hour", "10 × 3,600 = <b>36,000</b>", "derived"]], "bt") +
  line("The inquiry job is a service, with throughput and rate limits at the processor.", "a")), [
 "C: Unknown outcomes. Say one in a thousand authorisations times out. At peak that is ten a second, thirty-six thousand an hour.",
 "C: Decision: resolving them is not a cron script. The inquiry job is a real service, with its own throughput, and it must respect the processor's rate limits."])

S(plain("Estimates · 7 of 8 · idempotency and reconciliation", "Two tables that are bigger than they look", table(["Quantity", "Arithmetic", "Label"], [
  ["Idempotency keys", "2.9 × 10⁸ / day × 7 days × ~300 B ≈ <b>600 GB</b>", "illustrative"],
  ["Settlement lines", "~2.9 × 10⁸ / day", "derived"],
  ["Matching time", "at 1 M lines / s ≈ <b>5 min</b>", "illustrative"]], "bt") +
  line("Keys expire after seven days, said in the contract. Reconciliation is a batch join; its output is the breaks.", "a")), [
 "C: Two tables that are bigger than they look. Idempotency keys for seven days: two hundred ninety million a day, times seven, times three hundred bytes: about six hundred gigabytes. So keys expire, and the A-P-I contract says a retry after seven days is a new payment.",
 "C: And the settlement file: about two hundred ninety million lines. Matched at a million lines a second, about five minutes. Decision: reconciliation is a batch join. Its useful output is not the matches. It is the breaks."])

S(plain("Estimates · 8 of 8 · where the money is", "Fees dwarf servers", table(["Quantity", "Arithmetic", "Label"], [
  ["Processor fees", "a percentage of every payment's value", "fact"],
  ["One basis point", "0.01 % of the yearly volume", "illustrative"],
  ["Infrastructure", "a database cluster, some services", "illustrative"]], "bt") +
  grade("A candidate who says that one basis point of better routing outweighs the whole database cluster is showing the cost judgement this round looks for.")), [
 "C: Last, cost. Processor fees are a percentage of the money that moves. One basis point, one hundredth of a percent of a year's volume, outweighs the whole database cluster.",
 "N: That is the cost judgement this round looks for. The engineering levers on cost are routing and false declines, not servers.",
 "C: That is the numbers. Next, theory."])
