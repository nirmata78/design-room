from dsl import *

# ───────────────────────── 0 · cold open ─────────────────────────
chapter(0, "Cold open", -1, "Instant credit at the point of sale", [
 "C: Eight applications a second at the busiest moment of the week. Any database takes that. And yet this question fails strong engineers, because the hard parts here are not load."])

qs("Interviewer · the prompt", "“A customer at a merchant's counter scans a QR code to pay a $1,200 bill in instalments. Design the system that decides within a few seconds whether to lend, shows the offers, and creates the loan when the customer accepts.”", [
 "I: A customer at a merchant's counter scans a Q-R code to pay a twelve hundred dollar bill in instalments. Design the system that decides within a few seconds whether to lend, shows the offers, and creates the loan when the customer accepts.", "[pause: 1.5]"])

S(dia("Why it is harder than it looks", "Time, evidence and money pull three ways", "tension",
      chip=chips("a slow bureau, one call in ten", "a dropped phone", "a regulator, 14 months later")), [
 "C: Here is the hook. A credit bureau answers in about six tenths of a second, and one time in ten it takes four seconds, while a customer stands at the counter. Every call to it costs about a dollar and may show on the customer's credit file. So we can't wait, and we can't race two bureaus either.",
 "C: Then a phone drops between accept and the answer, and the customer taps again on the merchant's tablet. And fourteen months later a regulator asks why someone was declined. None of that is throughput. It is time, evidence and money pulling three ways, and that picture is the whole tension."])

S(plain("Before the design", "What this question grades", table(["Axis", "Weak signal", "Strong signal"], [
  ["<b>Requirements</b>", "“Score the customer and create a loan”", "The lender of record, the counter deadline, vendor latency and cost, decline reasons, retention: asked first"],
  ["<b>Correctness</b>", "A saga that “compensates” every step", "A state machine with one atomic step, accept to book, with an outbox"],
  ["<b>Trade-offs</b>", "Hedged bureau calls; “approve with partial data”", "One deadline; a missing-data policy owned by credit risk, capped"],
  ["<b>Depth</b>", "“The model returns a score”", "Frozen inputs and versions; a capped challenger; a vault with tokens"],
  ["<b>Operations</b>", "CPU and error rate", "Offers in 3 s, approval per merchant per hour, fallback against cap, owners"]], "bt sm sig") +
  grade("Every degraded path is a credit decision with an owner and a cap, not an engineering default.")), [
 "N: Five axes. The weak answer shards a database that sees eight writes a second. The strong answer knows a credit pull cannot be undone, and that a timeout is a credit decision someone has to own.",
 "C: One rule I'll keep for the whole round: every degraded path is a credit decision with an owner and a cap, never an engineering default."])

key("The thesis", "A <em>regulated decision</em> under a deadline set by <em>slow, paid vendors</em>, then <em>one atomic step</em>. The load is tiny; the grade is on the slow edges, one loan, a decision you can replay, and identity in a small box.", [
 "V: Instant credit at the counter is a regulated decision under a deadline set by slow, paid vendors, followed by one atomic step. The load is tiny. The grade is on the slow edges.", "[pause: 1.0]"])

S(plain("The order I will follow", "Scope, numbers, theory, a simple design, then I break it",
  '<div class="ribbon" style="margin-top:14pt">' + "".join(f"<span>{x}</span>" for x in STAGES) + '</div>' +
  '<div class="cards c3" style="margin-top:18pt"><div class="cd"><h3>First</h3><p>Requirements and scope. Numbers. A short theory chapter.</p></div>'
  '<div class="cd grn"><h3>Then</h3><p>API and data. A design in three versions, each answering the one before.</p></div>'
  '<div class="cd red"><h3>Most of the time</h3><p>Eight challenges that break the design. A build cost. A recap.</p></div></div>'), [
 "C: The order. Requirements, numbers and a short theory chapter. Then the A-P-I and the data, and a design in three versions, each answering the objection to the one before.",
 "C: Then most of the time goes to eight challenges that break it, where each fix creates the next question. A build cost, and a recap."])

# ───────────────────────── 1 · requirements ─────────────────────────
chapter(1, "Requirements and scope", 0, "Ask first. Cut on purpose. Put numbers on it.", [
 "C: Six questions before I draw anything. Each answer moves the design, and two of them only make sense if you know how lending works."])

def clar(n, q, a, say):
    S(f'<div class="who">Clarifying question {n} of 6</div><div class="qq">{q}</div><div class="ans">{a}</div>', say, cls="qs")

clar(1, "How many applications?", "2 million a month. The Saturday peak is about ten times the average.", [
 "C: How many applications?",
 "I: Two million a month. The Saturday peak is about ten times the average.",
 "C: That is under one a second on average and about eight at the peak. I'll do the arithmetic in a minute, but I can already say the load is not the problem."])
clar(2, "How long can the customer wait?", "Offers on screen in under 3 s for 95 % of applications. 10 s is a lost sale.", [
 "C: How long can the customer wait at the counter?",
 "I: Offers on screen in under three seconds for ninety-five percent of applications. Ten seconds is a lost sale.",
 "C: Three seconds from submit to offers, at the ninety-fifth percentile. That number will set one deadline for every vendor call."])
clar(3, "Who is the lender of record?", "We decide on the partner bank's credit policy and service the loan. The bank is the lender of record.", [
 "C: Who is the lender of record? Us, or a partner bank?",
 "I: We decide, on the partner bank's credit policy, and we service the loan. The bank is the lender of record.",
 "C: That matters. Every credit policy version needs the bank's approval, our decision records are the bank's records too, and the money to pay the merchant flows through the bank."])
clar(4, "Which vendors, and how fast?", "Two credit bureaus: p50 0.6 s, p99 several seconds, about 1 % errors. An identity and fraud vendor, p99 400 ms. Optional bank-account data: seconds to minutes.", [
 "C: Which vendors do we call, and how fast are they?",
 "I: Two credit bureaus. Median six tenths of a second, the ninety-ninth percentile several seconds, about one percent errors. An identity and fraud vendor, four hundred milliseconds at the ninety-ninth. And optional bank-account data, seconds to minutes.",
 "C: So the bureau's tail sets the deadline, and the bank data is never something we wait for at the counter."])
clar(5, "What do the calls cost?", "About $1 a bureau pull. Identity checks about 5 cents.", [
 "C: What do those calls cost?",
 "I: About a dollar a bureau pull. Identity checks, about five cents.",
 "C: Then we never race two bureaus. Every pull is paid, and it may show on the customer's credit file as an inquiry."])
clar(6, "Which rules apply?", "Disclosures before signing. The principal reasons for every decline. Records kept about seven years. Fairness testing of models.", [
 "C: Which rules shape the system?",
 "I: Cost disclosures before the customer signs. The principal reasons for every decline. Records kept about seven years. And fairness testing of models.",
 "C: Three architecture decisions in one answer. Decisions must carry reasons about the applicant, so our vendor being slow can never be a reason. The disclosure version is part of the loan. And a decision must replay years after the model that made it is gone."])

S(plain("Requirements · functional", "Four things the system must do", '<div class="cards c2">'
  '<div class="cd"><h3>FR1 · Apply</h3><p>The customer scans the merchant\'s code. Identity goes into a vault. An application exists, and a retry returns the same one.</p></div>'
  '<div class="cd grn"><h3>FR2 · Decide</h3><p>Identity, fraud and credit data under one deadline. Offers, a refer, or a decline with reasons.</p></div>'
  '<div class="cd amb"><h3>FR3 · Accept and book</h3><p>The customer accepts one disclosed offer. Exactly one loan is booked.</p></div>'
  '<div class="cd red"><h3>FR4 · Fund and hand off</h3><p>The merchant is paid net of fees. The loan goes to servicing. Decline notices go out.</p></div></div>'), [
 "C: Four functional requirements. One, apply: the customer scans the merchant's code, identity goes into a vault, and an application exists. A retry returns the same application. Two, decide: identity, fraud and credit data under one deadline, and the answer is offers, a refer, or a decline with reasons.",
 "C: Three, accept and book: the customer accepts one disclosed offer, and exactly one loan is booked. Four, fund and hand off: the merchant is paid net of fees, the loan goes to servicing, and decline notices go out. Each of these gets a numbered flow later."])

S(plain("Requirements · non-functional", "The numbers, and what each is for", '<p class="chips">all initial targets, not measurements</p><div class="tiles" style="--n:4">'
  '<div class="tile blue"><b>3 s</b><span>offers on screen, p95</span></div>'
  '<div class="tile red"><b>0</b><span>loans booked twice or unaccepted</span></div>'
  '<div class="tile"><b>7 years</b><span>every decision replayable</span></div>'
  '<div class="tile blue"><b>vault</b><span>raw identity nowhere else</span></div></div>' +
  line("Plus: 99.9 % in merchant hours · merchant funded within one business day · every degraded path under a cap.", "a")), [
 "C: The numbers, all initial targets. Offers on screen in three seconds at the ninety-fifth percentile. Zero loans booked twice, or booked without acceptance of the exact disclosure shown. Every decision replayable for seven years. And raw identity data nowhere except a vault.",
 "C: Plus three more: three nines in merchant hours, the merchant funded within one business day, and every degraded path under a cap that someone signed."])

S(plain("Requirements · scope", "In, and out on purpose", '<div class="cards c2">'
  '<div class="cd grn"><h3>In scope</h3><p>Apply, identity, decide, offers, refer, accept, book, the funding instruction, the servicing handoff, decline notices.</p></div>'
  '<div class="cd red"><h3>Out, on purpose</h3><p>Repayments and the ledger (SD-95). Card authorisation (SD-77). Merchant onboarding and merchant fraud. Model training: we load a versioned model. Collections. The payment rail.</p></div></div>'), [
 "C: In scope: apply, identity, decide, offers, refer, accept, book, the funding instruction, the handoff to servicing, and decline notices.",
 "C: Out, on purpose, and I'll say it aloud. Repayments and the ledger: that's a servicing system with its own hard problems. Card authorisation. Merchant onboarding and merchant fraud, which is a merchant-risk system. Model training: I'll treat a model as a versioned artefact we load. Collections, and the payment rail itself."])

key("The core", "The core is three things: an <em>orchestrator</em> that decides under one deadline with a policy for what is missing; a <em>state machine</em> whose only atomic step is accept to book; and a <em>record and a vault</em>.", [
 "V: The core is three things. An orchestrator that decides under one deadline. A state machine whose only atomic step is accept to book. And a record and a vault.", "[pause: 0.8]",
 "N: The candidate named the core before drawing. That is the scoping signal: what the system is in a sentence, and what it is not."])

# ───────────────────────── 2 · estimates ─────────────────────────
chapter(2, "Estimates", 1, "Three numbers, each with the decision it drives", [
 "C: Numbers next. Three of them really matter, and each one changes a decision. I'll label them: given, derived or illustrative."])

S(plain("Estimates · the load", "Eight a second at the peak", table(["Number", "Arithmetic", "Label", "Decides"], [
  ["Applications", "2 × 10⁶ ÷ (30 × 86,400 s) ≈ <b>0.8/s</b>; peak × 10 ≈ <b>8/s</b>", "given → derived", "One relational primary"],
  ["Transitions", "8/s × about 6 ≈ <b>50 writes/s</b>", "derived", "Every transition can be a committed row"],
  ["Vendor calls", "8/s × 4 ≈ <b>32/s</b>; in flight 32 × 2 s ≈ <b>64</b>", "derived", "Per-vendor limits matter more than our servers"]], "bt sm")), [
 "C: The load. Two million a month, divided by about two point six million seconds, is about eight tenths of an application a second. Ten times that at the Saturday peak: eight a second. Each application moves through about six states, so about fifty committed writes a second. One relational database takes that without noticing.",
 "C: Each application fans out to about four vendor calls: thirty-two calls a second, and with a two-second deadline about sixty-four in flight. So the pressure is on the vendors, their latency and their contract limits, not on our servers."])

S(plain("Estimates · the money", "The largest line on the bill is not servers", table(["Number", "Arithmetic", "Label", "Decides"], [
  ["Bureau pulls", "2 × 10⁶ × $1 ≈ <b>$2M a month</b>", "illustrative", "Never race two bureaus"],
  ["Report reuse", "20 % re-apply in 30 days: 4 × 10⁵ × $1 ≈ <b>$400k a month</b>", "illustrative", "A report store with a reuse rule"],
  ["Identity checks", "2 × 10⁶ × $0.05 ≈ <b>$100k a month</b>", "illustrative", "Also paid per call"],
  ["Loans", "2 × 10⁶ × 60 % × 70 % ≈ <b>840,000 a month</b> ≈ $1.0B", "illustrative", "Funding is a daily batch per merchant"]], "bt sm")), [
 "C: The money. If every application pulls a bureau report at about a dollar, that's two million dollars a month, far more than the computers. If a fifth of applicants re-apply within a month, and the contract and the rules let us reuse a recent report, that saves about four hundred thousand a month. So the report store and its retention rule are part of the design.",
 "C: Identity checks add about a hundred thousand. And with sixty percent approved and seventy percent of those accepted, that is about eight hundred and forty thousand loans a month, about a billion dollars at twelve hundred each. Illustrative, but it tells me the merchant is paid in a daily batch, not per request."])

S(plain("Estimates · the missing-data path", "Not an edge case: fourteen a minute", table(["Number", "Arithmetic", "Label", "Decides"], [
  ["Bureau missing at the deadline", "≈ 2 % late + ≈ 1 % errors ≈ <b>3 %</b> ≈ 60,000 a month", "illustrative, to measure", "A signed, versioned policy, not a catch block"],
  ["At the peak", "8/s × 3 % × 60 s ≈ <b>14 a minute</b>", "derived", "Counters and caps on every row"],
  ["A 20-minute outage", "8 × 1,200 ≈ <b>9,600</b>; approve all ≈ $11.5M unscored; decline all ≈ <b>4,000</b> lost loans", "derived", "Neither extreme: challenge two"]], "bt sm")), [
 "C: The third number is the one that shapes the design. If about two percent of bureau calls miss the deadline and about one percent fail, about three percent of applications reach the deadline with no bureau answer. Sixty thousand a month, fourteen a minute at the peak. That is a weekly volume, so what we do then is a policy with counters, not an exception handler.",
 "C: And a twenty-minute bureau outage at the peak is nine thousand six hundred applications. Approve them all and we lend eleven and a half million dollars nobody scored. Decline them all and we lose about four thousand loans. Neither extreme. That's challenge two."])

S(plain("Estimates · records", "Kept for years, rarely read", table(["Number", "Arithmetic", "Label", "Decides"], [
  ["Decision records", "2 × 10⁶ × 50 KB ≈ <b>100 GB a month</b>", "illustrative", "Object storage, not the database"],
  ["Seven years", "100 GB × 84 months ≈ <b>8.4 TB</b>", "derived", "Encrypted, a retention lock, a key per record"]], "bt sm") +
  line("The database keeps a reference and the hot fields: outcome, reasons, versions.", "")), [
 "C: Records. Each decision with its inputs, mostly the bureau report, is about fifty kilobytes. A hundred gigabytes a month, about eight terabytes over seven years. So the full record goes to encrypted object storage with a retention lock, and the database keeps a reference and the hot fields."])

S(dia("Estimates · the latency budget", "Three seconds, and where they go", "budget", chip=chips("initial target", "p95, submit to offers on screen")), [
 "C: The latency budget, from submit to offers on screen. The phone to our A-P-I and the first state write, about two hundred milliseconds. The vendors, two seconds: one deadline for all of them. Model, policy and pricing, about two hundred and fifty. Writing the record and pushing the offers to the phone, about two hundred and fifty. That is two point seven seconds, with three hundred to spare.",
 "C: So the deadline is derived from the promise, not picked from experience. And nothing optional, like bank data, can ever sit on this path."])

S(plain("Estimates · what the numbers decided", "Four decisions, before any box is drawn", '<div class="cards c2">'
  '<div class="cd"><h3>One database</h3><p>Eight applications and about fifty writes a second: one replicated relational primary. No sharding.</p></div>'
  '<div class="cd red"><h3>No races</h3><p>About $1 a pull and $2M a month: a second bureau only on failure, never on slowness.</p></div>'
  '<div class="cd amb"><h3>A policy, not a catch block</h3><p>About 3 % reach the deadline without a bureau: fourteen a minute at the peak.</p></div>'
  '<div class="cd grn"><h3>Object storage for records</h3><p>8.4 TB over seven years, written once, rarely read.</p></div></div>'), [
 "C: So, before I draw a single box, the numbers have already decided four things. One relational database, because the load is tiny. No races between bureaus, because every pull is paid and the bill is already the largest line. A signed policy for missing data, because it happens fourteen times a minute at the peak. And object storage for decision records, because they're large, written once, and rarely read.",
 "C: Notice what the numbers did not ask for: a cache, a queue in front of the database, or a sharding scheme. Saying that out loud is part of the answer."])
