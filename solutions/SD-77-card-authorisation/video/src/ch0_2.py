from dsl import *

# ───────────────────────── 0 · cold open ─────────────────────────
chapter(0, "Cold open", -1, "Design card authorisation for a debit-card issuer", [
 "C: Card authorisation looks like the easiest question in a fintech loop. A request arrives, you check the balance, you say yes. It is asked at every level, because that answer is wrong in three places at once."])

qs("Interviewer · the prompt", "“You're building a card issuer, a company that issues debit cards to its customers. Design the system that receives authorisation requests from the card network and approves or declines them.”", [
 "I: You're building a card issuer, a company that issues debit cards to its customers. Design the system that receives authorisation requests from the card network, and approves or declines them.", "[pause: 1.5]"])

S(dia("Why it is harder than it looks", "Three places where the simple answer fails", "swipe-path",
      chip=chips("a deadline we do not set", "money that moves days later", "rules that change daily")), [
 "C: Here is the hook. First, the deadline is not ours. The card network waits about two seconds, and if we are late it does not fail. It decides for us, with limits we set months ago, and tells us afterwards.",
 "C: Second, no money moves at the till. An approval is a promise, recorded as a hold. The real amount arrives days later in a file, often different, sometimes never.",
 "C: Third, the fraud decision. Analysts change the rules several times a day, and we only learn whether a decision was right two months later, when the chargebacks arrive."])

S(plain("Before the design", "What this question grades", table(["Axis", "Weak signal", "Strong signal"], [
  ["<b>Requirements</b>", "“Approve if the balance is enough”", "The deadline and who sets it; incremental, reversal, advice; clearing; label delay, asked first"],
  ["<b>Correctness</b>", "Debit at authorisation; one auth, one clearing", "Holds; available = posted − holds; network reference in any order; one write per account"],
  ["<b>Trade-offs</b>", "“Call the fraud service”", "A budget per step; a fail-policy table with a cap and owners; rules as versioned data"],
  ["<b>Depth</b>", "Stops at “add a cache”", "Stand-in advices that overdraw; inline burst counters; shadow cannot measure false positives"],
  ["<b>Operations</b>", "CPU and error rate", "Approval rate by merchant type; stand-in count; a runbook for “declines doubled”"]], "bt sm sig") +
  grade("The money is a hold, and the deadline is someone else's. Everything else follows from those two.")), [
 "N: Five axes. The weak answer debits the balance and calls a fraud service. The strong answer places a hold, keys every message by the network's reference, gives the model a budget, and says what happens when it is late.",
 "C: Two facts I'll keep for the whole round. The money is a hold. And the deadline belongs to someone else."])

key("The thesis", "A promise made inside someone else's deadline: a <em>hold, not a debit</em>; every message <em>once, in any order</em>; a <em>written answer</em> for when a step is late; and a ledger that <em>absorbs what we did not decide</em>.", [
 "V: Card authorisation is a promise made inside someone else's deadline. A hold, not a debit. Every message once, in any order. A written answer for when a step is late. And a ledger that absorbs what we did not decide.", "[pause: 1.0]"])

S(plain("The order I will follow", "Scope, numbers, theory, a simple design, then I break it",
  '<div class="ribbon" style="margin-top:14pt">' + "".join(f"<span>{x}</span>" for x in STAGES) + '</div>' +
  '<div class="cards c3" style="margin-top:18pt"><div class="cd"><h3>First</h3><p>Requirements and scope. Numbers. A short theory chapter.</p></div>'
  '<div class="cd grn"><h3>Then</h3><p>The messages and the data. A design in three versions, each answering the one before.</p></div>'
  '<div class="cd red"><h3>Most of the time</h3><p>Eight challenges that break the design. A build cost. A recap.</p></div></div>'), [
 "C: The order. Requirements, numbers, and a short theory chapter. Then the messages and the data, and a design in three versions, each answering the objection to the one before.",
 "C: Then most of the time goes to eight challenges that break it, where each fix creates the next question. A build cost, and a recap."])

# ───────────────────────── 1 · requirements ─────────────────────────
chapter(1, "Requirements and scope", 0, "Ask first. Cut on purpose. Put numbers on it.", [
 "C: Six questions before I draw anything. Each answer moves the design."])

def clar(n, q, a, say):
    S(f'<div class="who">Clarifying question {n} of 6</div><div class="qq">{q}</div><div class="ans">{a}</div>', say, cls="qs")

clar(1, "How many cards, and how much traffic?", "8 million debit cards. 1,500 authorisations a second at the evening peak; 4,000 on the busiest shopping day.", [
 "C: How many cards, and how much traffic?",
 "I: Eight million debit cards. Fifteen hundred authorisations a second at the evening peak, four thousand on the busiest shopping day of the year.",
 "C: Four thousand a second is a small fleet. So throughput will not be the problem. The tail of the slowest step will be."])
clar(2, "What is the deadline?", "The network times out after about 2 seconds and stands in. Your own target is up to you.", [
 "C: What is the deadline, and what happens if we miss it?",
 "I: The network times out after about two seconds, and then it stands in. Your own target is up to you.",
 "C: Then I'll correct a common prep line out loud: the network does not give us a hundred milliseconds. Its timeout is seconds, and our target is a choice. I'll take three hundred milliseconds at the ninety-ninth percentile, measured at our gateway, and design for the case when we miss it anyway."])
clar(3, "Which messages arrive?", "Authorisation, incremental authorisation, reversal, advice, refund. Clearing comes by daily file.", [
 "C: Which messages do we receive?",
 "I: Authorisation, incremental authorisation, reversal, advice, and refund. Clearing comes in a daily file.",
 "C: So it is a message state machine, not one request type. A reversal can cancel an approval. An advice tells us what the network decided while we were away. And the file comes days later."])
clar(4, "What about fraud?", "Losses about 8 basis points of volume. Chargebacks arrive 30 to 90 days later. Analysts change rules several times a day, without a release.", [
 "C: What do fraud and rules look like?",
 "I: Losses are about eight basis points of volume. Chargebacks and customer reports arrive thirty to ninety days later. Analysts change rules several times a day, and they don't want a code release for it.",
 "C: Thirty to ninety days is the number I'll come back to. It means we cannot learn quickly whether a decline was right. Challenge six."])
clar(5, "Where is the money?", "The balance lives in the core ledger. Clearing amounts can differ from the authorisation; some never clear.", [
 "C: Where does the balance live, and does clearing always match?",
 "I: The balance lives in our core ledger. Clearing amounts can differ from the authorisation, and some authorisations never clear.",
 "C: Then an approval must not touch the ledger's balance. It places a hold, and clearing moves the real amount. That is challenge one."])
clar(6, "Do we see card numbers?", "No. The processor keeps full card numbers in its vault and sends a token. Keep it that way.", [
 "C: Do we ever see full card numbers?",
 "I: No. The processor in front of you keeps them in its vault, and sends you a token. Keep it that way.",
 "C: Good. That keeps the card-data scope at the processor. Everything I design keys on the token."])

S(plain("Requirements · functional", "Four things the system must do", '<div class="cards c2">'
  '<div class="cd"><h3>FR1 · Authorise</h3><p>Answer an authorisation or incremental authorisation, approve or decline, inside the deadline. An approval places a hold.</p></div>'
  '<div class="cd grn"><h3>FR2 · Reverse and advise</h3><p>Reversals release holds. Stand-in advices are recorded and held, even past the balance.</p></div>'
  '<div class="cd amb"><h3>FR3 · Clear</h3><p>Match each clearing record to its hold, post the real amount, release or adjust the hold. Expire holds that never clear.</p></div>'
  '<div class="cd red"><h3>FR4 · Change rules</h3><p>Analysts publish fraud rules as versioned data: backtest, shadow, slice, enforce. No deploy.</p></div></div>'), [
 "C: Four functional requirements. One, authorise: approve or decline inside the deadline, and an approval places a hold. Two, reverse and advise: reversals release holds, and stand-in advices are recorded, even past the balance.",
 "C: Three, clear: match each clearing record to its hold, post the real amount, and expire the holds that never clear. Four, change rules: analysts publish rules as versioned data, with a staged rollout, and no deploy. Each of these gets a numbered flow."])

S(plain("Requirements · non-functional", "The numbers, and what each is for", '<p class="chips">all initial targets, not measurements</p><div class="tiles" style="--n:4">'
  '<div class="tile blue"><b>300 ms</b><span>p99 at our gateway</span></div>'
  '<div class="tile blue"><b>99.99 %</b><span>the authorisation path</span></div>'
  '<div class="tile"><b>once</b><span>every network message takes effect once</span></div>'
  '<div class="tile red"><b>5 min</b><span>a rule change goes live</span></div></div>' +
  line("Our own approvals never take an account below zero. Every decision reproducible for 7 years. Clearing posted by 09:00. Degraded decisions inside an hourly cap.", "a")), [
 "C: The numbers, and they are initial targets. Three hundred milliseconds at the ninety-ninth percentile at our gateway. Four nines for the authorisation path, because every minute we are down is a minute of stand-in for every card. Every network message takes effect once. A rule change live within five minutes.",
 "C: And four more. Our own approvals never take an account below zero. Every decision reproducible for seven years, for disputes. Clearing posted by nine in the morning. And degraded decisions inside an hourly exposure cap that risk and finance sign."])

S(plain("Requirements · scope", "In, and out on purpose", '<div class="cards c2">'
  '<div class="cd grn"><h3>In scope</h3><p>The decision, holds, reversals and advices, rules and model scoring, online features, the fail policy, clearing match and posting, decision events.</p></div>'
  '<div class="cd red"><h3>Out, on purpose</h3><p>Issuing cards. The network and the processor. Disputes and chargebacks (we only read their labels). Statements. Model training. Credit products. The 3-D Secure challenge (its result is an input).</p></div></div>'), [
 "C: In scope: the decision, holds, reversals and advices, rules and the model score, online features, the fail policy, clearing, and the decision events.",
 "C: Out, on purpose. Issuing the cards. The network and the processor themselves. The disputes workflow: I only read its labels. Statements, model training, credit products. And the three-D Secure challenge flow, whose result simply arrives as one more input field."])

key("The core", "The core is three things: a <em>decision path</em> that always answers inside the deadline, a <em>hold ledger</em> where each message takes effect once, and a <em>clearing path</em> that turns promises into posted money.", [
 "V: The core is three things. A decision path that always answers inside the deadline. A hold ledger where each message takes effect once. And a clearing path that turns promises into posted money.", "[pause: 0.8]",
 "N: The candidate named the core before drawing a box. That is the scoping signal the interviewer is waiting for."])

# ───────────────────────── 2 · estimates ─────────────────────────
chapter(2, "Estimates", 1, "Each number as arithmetic, with what it decides", [
 "C: Numbers next, each as arithmetic, each with the decision it drives. I'll label them: given, derived or illustrative."])

S(plain("Estimates · traffic and concurrency", "A small fleet, with every read on the critical path", table(["Number", "Arithmetic", "Label", "Decides"], [
  ["Peak", "<b>1,500/s</b> evening · <b>4,000/s</b> busiest day", "given", "size for 4,000 with headroom"],
  ["Daily messages", "assume 20 M a day ≈ 230/s average; ≈ 2.5 a card a day", "illustrative", "sizes logs and files, not servers"],
  ["In flight", "4,000/s × 0.3 s = <b>1,200</b>; × 0.1 s typical = 400", "derived", "small; the tail is the problem"],
  ["State reads", "4,000/s × 3 reads = <b>12,000/s</b>, a few ms each", "derived", "state next to the decision, never the ledger"]], "bt sm")), [
 "C: Traffic. Four thousand a second on the busiest day. Say twenty million messages a day, which is about two hundred and thirty a second on average and two and a half per card per day. That number is illustrative, and it sizes logs and files, not servers.",
 "C: Concurrency. Four thousand a second, times three hundred milliseconds, is twelve hundred requests in flight at worst, about four hundred at a typical hundred milliseconds. Small. Each reads three things: the account and its holds, the card, and the counters. Twelve thousand reads a second, each budgeted at a few milliseconds.",
 "C: The decision this drives: the state a decision needs lives next to the decision, in a store built for millisecond reads. Never the core ledger, on the hot path."])

S(plain("Estimates · the hold book", "Thirty-six million holds fit in memory", table(["Number", "Arithmetic", "Label", "Decides"], [
  ["Open holds", "12 M approvals a day × ~3 days open = <b>36 M</b>", "illustrative", "the hold book is not big"],
  ["Its size", "36 M × ~200 B ≈ <b>7 GB</b>", "illustrative", "in memory, partitioned by account"],
  ["Per account", "a busy card: a few authorisations a minute", "derived", "serialising per account is free"],
  ["A fleet account", "2,000 cards × 1 per 10 min ≈ <b>3.3/s</b> on one key", "illustrative", "still fine; challenge 2"]], "bt sm")), [
 "C: The hold book. Say twelve million approvals a day, each open about three days until it clears. That's thirty-six million open holds, and at about two hundred bytes each, seven gigabytes. The whole book fits in memory, partitioned by account.",
 "C: Per account, the rate is tiny: a busy card does a few authorisations a minute. So serialising every write for one account costs nothing. The exception is a business account with two thousand cards on one balance. Even that is about three a second on one key. I'll keep it for challenge two."])

S(plain("Estimates · the cost of a slow model", "A finance question, not an engineering default",
  table(["Step", "Arithmetic", "Result"], [
    ["Decisions without the model", "4,000/s × 60 s × 2 %", "<b>4,800 a minute</b>"],
    ["Expected loss on rules alone", "4,800 × $60 × 0.08 %", "<b>≈ $230 a minute</b>, at the base rate"]], "bt") +
  line("Fraud concentrates where the model is blind, so the real number is higher. That is why the fallback has a cap and an owner.", "r")), [
 "C: What a slow model costs. If two percent of decisions at the peak miss the model's slot, that's four thousand a second, times sixty seconds, times two percent: forty-eight hundred decisions a minute decided on rules alone.",
 "C: At an average of sixty dollars and our base fraud rate of eight basis points, that is about two hundred and thirty dollars a minute of expected loss. Small. But fraud concentrates exactly where the model is blind, so the real number is several times higher. Falling back is a money decision, so it gets a cap and an owner. Challenge four."])

S(plain("Estimates · the batch side", "Large, but it has hours", table(["Number", "Arithmetic", "Label", "Decides"], [
  ["Clearing file", "~10 M records × ~500 B ≈ <b>5 GB</b> a day", "illustrative", "minutes of batch; matching is the hard part"],
  ["A bad file", "3 % duplicated × 10 M = <b>300,000</b>", "illustrative", "record-level idempotency"],
  ["Decision log", "20 M × ~2 KB ≈ <b>40 GB</b> a day ≈ 15 TB a year", "illustrative", "object storage by day, seven years"],
  ["An outage", "20 min × 60 s × 300/s = <b>360,000</b> stand-in decisions", "illustrative", "a burst of advices to post, once each"]], "bt sm")), [
 "C: The batch side. The clearing file: about ten million records of five hundred bytes, five gigabytes a day. Minutes of work. The hard part is matching, not volume. A bad file with three percent duplicated is three hundred thousand records that must do nothing.",
 "C: The decision log: twenty million decisions of about two kilobytes, forty gigabytes a day, fifteen terabytes a year, kept seven years in object storage. And an outage: twenty minutes at night at three hundred a second is three hundred and sixty thousand decisions the network made for us. Challenge seven."])

S(plain("Estimates · what the numbers decide", "Five numbers, five decisions", table(["Number", "Decision"], [
  ["12,000 state reads a second", "a dedicated authorisation store, never the ledger on the hot path"],
  ["7 GB of holds", "in memory, partitioned by account"],
  ["a few authorisations a minute per account", "serialise per account; it costs nothing"],
  ["$230 a minute, at least, for a slow model", "a fail policy with a cap and an owner"],
  ["360,000 advices after an outage", "record them once each, at any balance"]], "bt")), [
 "C: Before the budget, what the numbers decide, in one table. Twelve thousand reads a second means a dedicated authorisation store. Seven gigabytes of holds means it lives in memory, partitioned by account. A few authorisations a minute per account means serialising each account costs nothing.",
 "C: Two hundred and thirty dollars a minute, at least, for a slow model means the fallback needs a cap and an owner. And three hundred and sixty thousand advices after an outage means we record every one, once, whatever it does to the balance. An estimate that changes nothing is decoration."])

S(dia("Estimates · the latency budget", "Three hundred milliseconds, and one step allowed to be slow", "budget", chip=chips("initial target", "at our gateway")), [
 "C: The budget. Checks first: parse the message and look up its reference, read the account and the card, read and increment the counters, run the rules. About twenty-three milliseconds. The model gets sixty, and then a cut-off. Reserving the hold and replying, about fifteen.",
 "C: Ninety-eight milliseconds at the cut-off, two hundred spare. The spare is not waste. It is room for a pause, a failover and a slow hop at the same time, before the network's own clock is in danger. And the budget says the model is the only step allowed to be slow, and only up to its cut-off."])
