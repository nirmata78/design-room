from dsl import *
P = "[+]"

# ───────────────────────── 0 · cold open ─────────────────────────
chapter(0, "Cold open", -1, "Design payment processing and the double-entry ledger", [
 "C: The happy path of a payment is three boxes and a database. A merchant asks, we call the bank, we write it down. This question is not about the happy path. It is about a bank call that times out and leaves you not knowing whether the customer paid, a client that retries three times at once, and a statement that disagrees with your books."])

qs("Interviewer · the prompt", "“Design the system that takes a payment and records it: the ledger the company's money is accounted for in.”", [
 "I: Design the system that takes a payment and records it. The ledger the company's money is accounted for in.", "[pause: 1.5]"])

S(dia("Why it is harder than it looks", "The truth arrives over months; the answer is due in two seconds", "truth",
      chip=chips("2 s", "minutes", "next day", "months")), [
 "C: The hook, as a timeline. The merchant wants an answer in two seconds.", P,
 "C: The processor's answer comes in about a second, or not at all.", P,
 "C: An inquiry can settle an unknown outcome within minutes.", P,
 "C: The settlement file, with the processor's own books, arrives the next day.", "[+2]",
 "C: And a dispute can still arrive months later. Every strong answer is a design for not knowing yet. The rest of this video puts one mechanism at each point on this line."], cls="dia")

S(plain("Before the design", "What this question grades", table(["Axis", "Weak signal", "Strong signal"], [
  ["<b>Requirements</b>", "“Charge the card and store it”", "Asks what must never happen, in order; how the outside parties fail"],
  ["<b>Correctness</b>", "A balance column, floats, “retries are safe”", "Double entry, derived balances, an idempotency key inserted first"],
  ["<b>Trade-offs</b>", "“A distributed transaction with the bank”", "Says why that is unavailable; picks a state for “unknown” and its cost"],
  ["<b>Depth</b>", "“Retry with backoff”", "Timeout walk, outbox, the partition key, the hot account"],
  ["<b>Operations</b>", "API uptime", "Unknown count and age, a ledger that sums to zero, owned breaks"]], "bt xs sig") +
  grade("One sentence separates candidates: exactly-once does not exist across the bank boundary. Say it, then design around it.")), [
 "N: Five axes, one at a time.", P,
 "N: Requirements. Weak: charge the card and store it. Strong: what must never happen, in order, and how the outside parties fail.", P,
 "N: Correctness. Weak: a balance column and floats. Strong: double entry, balances derived, a key inserted first.", P,
 "N: Trade-offs. Weak: a distributed transaction with the bank. Strong: why that is unavailable, and the cost of an unknown state.", P,
 "N: Depth. Retry with backoff is a phrase; the timeout walk, the partition key and the hot account are the level down.", P,
 "N: Operations. Uptime stays green while the money is wrong; unknown age and a zero-sum ledger do not.", P,
 "C: I'll keep one sentence in front of everything: exactly-once does not exist across a network boundary."])

key("The thesis", "At-least-once delivery, <em>one effect per intent</em>, a state for <em>not knowing yet</em>, and a <em>reconciliation</em> that finds what the rest missed, on an append-only double-entry journal.", [
 "V: Exactly-once does not exist across a network boundary. So the design is at-least-once delivery, one effect per intent, a state for not knowing yet, and a reconciliation that finds what the rest missed. All of it written to an append-only double-entry journal, where a balance is a sum, never a field.", "[pause: 1.0]"])

# ───────────────────────── 1 · requirements ─────────────────────────
chapter(1, "Requirements and scope", 0, "The scale first, then six questions", [
 "C: The scale first, then six questions. Each answer moves the design."])

S(plain("Requirements · the scale line", "Three numbers every estimate starts from", '<div class="tiles" style="--n:3">'
  '<div class="tile blue"><b>9 B a month</b><span>payments: 290 M a day, 3,300 a second on average</span></div>'
  '<div class="tile red"><b>10,000/s</b><span>peak, a sale-day evening; one merchant at 5,000/s</span></div>'
  '<div class="tile"><b>7 years</b><span>of balanced entries kept: about 2.9 trillion</span></div></div>' +
  line("Every number later in this video starts from one of these three, and I'll say which. All are illustrative.", "a")), [
 "C: The interviewer gives me the scale, and I write it down first.", P,
 "C: Nine billion payments a month: two hundred and ninety million a day, thirty-three hundred a second on average.", P,
 "C: The peak is ten thousand a second, a sale-day evening at three times the average. Inside it, one large merchant takes five thousand a second on its own.", P,
 "C: And the books are kept seven years, about two point nine trillion entries.", P,
 "C: Every number I use later starts from one of these three, and I'll say which. They are illustrative."])

def clar(n, q, a, ask, ans, so):
    S(f'<div class="who">Clarifying question {n} of 6</div><div class="qq">{q}</div><div class="ans">{a}</div>',
      ["C: " + ask, P, "I: " + ans, "C: " + so], cls="qs")

clar(1, "How fast must the client get an answer?", "An authorisation decision within 2 seconds.",
     "How fast must the client get an answer?", "An authorisation decision within two seconds.",
     "Most of those two seconds belong to the processor, not to us. So our own part has to be small, and we need a plan for when the processor uses all of it.")
clar(2, "Who actually moves the money?", "Card networks and banks, through processors. They time out, return ambiguous results, and sometimes go down for hours. Your call: a gateway or direct?",
     "Who moves the money, and do we reach them directly or through a gateway?", "Networks and banks, through processors. They time out, give ambiguous results, and sometimes go down for hours. Gateway or direct is your call.",
     "Ambiguous results mean a state for not knowing. At this volume I'd go direct to processors, and I'll show where a gateway wins, because below some volume it does.")
clar(3, "What is the ledger's rule?", "It must always balance. No exceptions.",
     "What is the ledger's rule?", "It must always balance. No exceptions.",
     "Then every movement is entries that sum to zero, written in one transaction, and a check that it still sums to zero runs all the time.")
clar(4, "How long must it be auditable?", "Every balance explainable from immutable records for seven years.",
     "How long must the books be explainable?", "Every balance explainable from immutable records, for seven years.",
     "Immutable and explainable rule out a balance column updated in place. A balance becomes a sum over records.")
clar(5, "Refunds and disputes?", "Partial and full refunds, and chargebacks, arriving days or months later.",
     "Refunds and disputes?", "Partial and full refunds, and chargebacks, arriving days or months later.",
     "Months later means the original period may be closed. So corrections are new records dated when they happen, never edits.")
clar(6, "What must never happen, in order?", "Your call. I'll tell you if I disagree.",
     "What must never happen, in priority order? I'd propose: charging twice or losing money, then an unbalanced ledger, then a slow payment.", "Your call. I agree with that order.",
     "That order settles a lot. When I must choose between a fast answer and a correct one, I answer pending.")

S(plain("Requirements · functional", "Five things the system must do", cards(
  ("", "FR1 · Pay", "Authorise and capture, idempotent per client key."),
  ("", "FR2 · Adjust", "Void, partial or full refund, chargeback; each references the payment."),
  ("amb", "FR3 · Notify", "Every state change reaches the merchant as a signed webhook."),
  ("", "FR4 · Reconcile", "Match our books to each processor's settlement file daily; every difference is an owned break."),
  ("grn", "FR5 · Explain", "Any account's balance at any time, from the journal."), cols=3)), [
 "C: Five functional requirements.", P,
 "C: One, pay: authorise and capture, idempotent per client key.", P,
 "C: Two, adjust: void, refund, chargeback, each referencing the original payment.", P,
 "C: Three, notify: every state change reaches the merchant as a signed webhook.", P,
 "C: Four, reconcile: match our books against each processor's settlement file every day, and make every difference a break with an owner.", P,
 "C: Five, explain: any balance at any time, from the journal. Each gets a sequence later."])

S(plain("Requirements · non-functional", "The numbers, and what each is for", '<p class="chips">all initial targets, not measurements</p><div class="tiles" style="--n:4">'
  '<div class="tile red"><b>0</b><span>double charges, ever</span></div>'
  '<div class="tile blue"><b>&lt; 2 s</b><span>decision at p99, or an honest “pending”</span></div>'
  '<div class="tile blue"><b>15 min</b><span>an unknown resolved, for 99 %</span></div>'
  '<div class="tile"><b>1 day</b><span>every break found and owned</span></div></div>'), [
 "C: The numbers, all initial targets.", P,
 "C: Zero double charges.", P,
 "C: A decision within two seconds at the ninety-ninth percentile, or an honest pending.", P,
 "C: Ninety-nine percent of unknown outcomes resolved within fifteen minutes.", P,
 "C: Every difference with the processor found and owned within a day. And every journal transaction balanced at commit."])

S(plain("Requirements · scope", "In, and out on purpose", cards(
  ("grn", "In scope", "Authorise, capture, void, refund, chargeback; webhooks; the ledger; reconciliation; 50 currencies, no conversion."),
  ("red", "Out, on purpose", "Fraud scoring (a service we call). Card numbers (a token vault). FX pricing. Merchant onboarding and KYC. Payouts to merchants.")) +
  line("Payouts come back once, because a payout needs a balance check.", "")), [
 P, "C: In scope: authorise, capture, void, refund, chargeback, webhooks, the ledger, reconciliation, and fifty currencies without conversion.", P,
 "C: Out, on purpose: fraud scoring is a service I call. Card numbers live in a token vault, which keeps most card-data compliance away from us. Conversion, onboarding and payouts are their own questions.", P,
 "C: Payouts will come back once, in challenge four, because a payout needs a current balance."])

S(dia("Architecture · C4 level 1 · context", "The system in its context, before any boxes inside it", "c4-context",
      cap="Figure 1.1 — C4 system context: who pays, who integrates, and the two parties that keep their own books of the same money"), [
 "C: Before any boxes inside it, the system in its context.", P,
 "C: A customer pays at a merchant.", P,
 "C: The merchant's system creates payments and receives webhooks.", P,
 "C: In the middle, our system: it authorises, captures, and keeps the books.", P,
 "C: The processor moves the money, and keeps its own books of it. It sends us a settlement file every day.", P,
 "C: And finance operations owns breaks and corrections. Two of the four neighbours keep their own books of the same money, which is why reconciliation is a component and not a safety net."], cls="dia")

key("The core", "The core is four things: a <em>state machine</em> that admits “unknown”, an <em>idempotent</em> API, an <em>immutable</em> double-entry journal, and <em>reconciliation</em> against the outside world.", [
 "V: The core is four things. A state machine that admits unknown. An idempotent A-P-I. An immutable double-entry journal. And reconciliation against the outside world.", "[pause: 0.8]",
 "N: Notice the candidate fixed the scale, named the core and drew the context before any internals. That is the scoping signal."])

# ───────────────────────── 2 · estimates ─────────────────────────
chapter(2, "Estimates", 1, "Each number from the scale line, with what it decides", [
 "C: Numbers next. Each starts from the scale line, and each ends in a decision. They are illustrative, not measured."])

S(plain("Estimates · write rate and the partition key", "Forty thousand entries a second, on ten primaries", table(["Number", "From", "Arithmetic", "Decides"], [
  ["Entries", "peak", "10,000 payments × 4 entries = <b>40,000 entries/s</b>", "One primary will not take it"],
  ["One payment", "design", "key, payment, attempt, txn, 3 entries, outbox ≈ <b>8 rows</b>, one commit", "One transaction per payment"],
  ["Primaries", "peak", "10,000 ÷ ~1,200 commits/s with a synchronous standby ≈ <b>9</b>", "64 logical partitions on about 10 primaries"],
  ["Partition key", "the posting", "a capture touches 3 accounts: receivable, payable, fee", "<b>Key by merchant</b>, not by account"]], "bt xs mx")), [
 "C: The write rate, from the peak.", P,
 "C: Ten thousand payments a second, four entries each: forty thousand entries a second. One primary will not take that.", P,
 "C: One payment is about eight rows, the key, the payment, the attempt, a transaction, three entries and an outbox row, written in one commit. So one transaction per payment.", P,
 "C: A primary with a synchronous standby commits about twelve hundred of those a second. Ten thousand divided by that is nine primaries, so sixty-four logical partitions on about ten primaries.", P,
 "C: And the decision I'll defend: the key is the merchant, not the account. A capture touches three accounts. Keyed by account, every capture would span partitions. Keyed by merchant, it stays in one. I'll come back to that, including what happens with a million one-time accounts."])

S(plain("Estimates · volume and storage", "Three hundred million a day, six hundred terabytes in seven years", table(["Number", "From", "Arithmetic", "Decides"], [
  ["Per day", "monthly volume", "3,300 × 86,400 s ≈ <b>2.9 × 10⁸</b> payments", "Settlement files of hundreds of millions of lines"],
  ["Seven years", "retention", "3,300 × 3.15 × 10⁷ × 7 × 4 ≈ <b>2.9 × 10¹²</b> entries × 200 B ≈ <b>580 TB</b>", "Recent partitions hot, older ones to a cold archive"],
  ["Idempotency keys", "daily volume", "2.9 × 10⁸ × 7 days × 300 B ≈ <b>600 GB</b>", "Keys expire after seven days, by contract"]], "bt xs mx")), [
 "C: Volume and storage, from the monthly count.", P,
 "C: Thirty-three hundred a second times eighty-six thousand four hundred seconds: about two hundred and ninety million payments a day. The settlement files will have hundreds of millions of lines.", P,
 "C: Seven years: two point nine trillion entries at two hundred bytes is about five hundred and eighty terabytes. Recent partitions stay hot and older ones move to a cold archive. Entries never change, so archiving is a copy, not a migration.", P,
 "C: And the idempotency keys: seven days of them is about six hundred gigabytes. So keys expire, and the A-P-I contract says a retry after seven days is a new payment."])

S(dia("Estimates · the hot account", "One merchant, one balance row", "hot", chip=chips("5,000 / s", "≈ 670 / s per row lock", "initial estimate")), [
 "C: The number that shapes the data model, from the peak.", P,
 "C: One large merchant receives five thousand payments a second.", P,
 "C: If each payment updates that merchant's balance row, each update holds a row lock for about one and a half milliseconds. That allows about six hundred and seventy a second on one row.", P,
 "C: Append-only entries have no shared row at all.", P,
 "C: And sixteen sub-accounts would carry about ten thousand seven hundred a second, twice this merchant's peak.", P,
 "C: The shared row's queue grows by over four thousand a second, and within a second the merchant is past two seconds. Decision: payments append entries and the balance is derived. That is challenge four."], cls="dia")

S(dia("Estimates · the latency budget", "Two seconds, and the processor has most of them", "budget", chip=chips("initial targets")), [
 "C: The two-second budget. Our own work is the idempotency insert, a fraud call, and two commits: about ninety milliseconds.", "C: The processor, at its ninety-ninth percentile, about one and a half seconds. That leaves about four hundred spare.",
 "C: Decision: everything we own stays under a hundred milliseconds, and at one point nine seconds, if the processor has not answered, we answer pending and keep waiting. This is also why the language is not the bottleneck: our code is microseconds inside a second-long call."], cls="dia")

S(plain("Estimates · unknowns, reconciliation and cost", "Three more numbers, each with a decision", table(["Number", "From", "Arithmetic", "Decides"], [
  ["Unknowns", "peak", "0.1 % × 10,000 = <b>10/s</b>, 36,000 an hour", "The inquiry job is a service with rate limits"],
  ["Settlement", "daily volume", "2.9 × 10⁸ lines at 1 M/s ≈ <b>5 min</b>", "A batch join; its output is the breaks"],
  ["Cost", "volume", "one basis point of volume outweighs the database cluster", "Routing and false declines are the cost levers"]], "bt xs mx")), [
 "C: Three more.", P,
 "C: Unknown outcomes: one in a thousand times the peak is ten a second, thirty-six thousand an hour. Resolving them is a service with its own throughput and the processor's rate limits, not a cron script.", P,
 "C: Settlement: about two hundred and ninety million lines a day, at a million lines a second is five minutes. Reconciliation is a batch join, and its useful output is the breaks.", P,
 "C: And cost. Processor fees are a percentage of the money that moves, so one basis point of better routing outweighs the whole database cluster. Servers are not the lever.",
 "N: That is the cost judgement this round looks for. Next, theory."])
