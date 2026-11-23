from dsl import *
import dsl

def th(): dsl.SL[-1]["cls"] = (dsl.SL[-1]["cls"] + " theory").strip()

chapter(3, "Theory", 2, "What makes this problem hard, in words that outlive any product name", [
 "C: A short theory chapter before any design, so the design can lean on it. Six parts: what loan servicing is and is not, the properties, the central tension, seven mechanisms, an options matrix, and the failure catalogue. Every slide here carries a theory badge."]); th()

key("Theory · 1 of 6 · what it is", "Turn each loan's <em>terms</em> into a schedule, collect each amount <em>once</em> through rails that answer in days and <em>reverse weeks later</em>, record every movement as <em>balanced, immutable</em> lines, and <em>prove daily</em> the books agree with the bank.", [
 "V: A loan servicing system turns each loan's terms into a schedule, collects each amount once through rails that answer in days and can reverse weeks later, records every movement as balanced, immutable lines, and proves every day that its books agree with the bank.", "[pause: 1.0]",
 "C: Every clause does work. Terms into a schedule: the rules are versioned data, not code paths. Once: idempotency, not exactly-once delivery, which does not exist across a network. Answer in days and reverse weeks later: pending, unknown and returned are states. Balanced and immutable: double entry, corrections by reversal. And proves daily: reconciliation is a component, not an audit at year end."], cls="theory")

S(plain("Theory · 1 of 6 · what it is not", "Four things it is confused with", '<div class="cards c2">'
  '<div class="cd"><h3>Not a payment gateway</h3><p>A gateway turns one intent into one payment in seconds (SD-44). Servicing drives many payments over months, against a schedule that changes.</p></div>'
  '<div class="cd"><h3>Not a cron job</h3><p>A cron job fires work. It does not know what was attempted, what is pending, or what came back.</p></div>'
  '<div class="cd amb"><h3>A ledger is not a balance table</h3><p>A balance is a sum of lines. A number updated in place cannot explain itself to an auditor.</p></div>'
  '<div class="cd red"><h3>Settled is not final</h3><p>A bank debit can be returned after it settles. Final is a later, rule-defined point.</p></div></div>'), [
 "C: Four confusions. It is not a payment gateway: a gateway turns one intent into one payment in seconds. Servicing drives many payments over months, against a schedule that keeps changing. It is not a cron job: a cron job fires work, but it does not know what was attempted, what is pending, or what came back.",
 "C: A ledger is not a balance table: a balance is a sum, and a number updated in place cannot explain itself. And settled is not final: a bank debit can be returned after it settles, so final is a later point, defined by the network's rules."], cls="theory")

S(plain("Theory · 2 of 6 · the two properties", "State safety and liveness separately",
  '<div class="prop safe"><div class="lbl">Safety · must never happen</div><p><b>S1</b> One instalment collected twice.<br><b>S2</b> A ledger transaction that does not sum to zero in integer cents, or a line that is edited.<br><b>S3</b> A customer penalised beyond policy, or for our failure: fees, re-presentments, late marks.</p></div>'
  '<div class="prop live"><div class="lbl">Liveness · must eventually happen</div><p><b>L1</b> Every due instalment is attempted on its due date, before the rail’s cut-off.<br><b>L2</b> Every payment leaves UNKNOWN and PENDING for SETTLED or RETURNED, within a bound.<br><b>L3</b> Every difference between ledger, processor and bank becomes an owned break within a day.</p></div>'), [
 "C: Three safety properties, things that must never happen. S-one: one instalment collected twice. S-two: a ledger transaction that doesn't sum to zero in whole cents, or a line that gets edited. S-three: a customer penalised beyond policy, or for our own failure.",
 "C: And three liveness properties, things that must eventually happen. L-one: every due instalment is attempted on its due date, before the cut-off. L-two: every payment leaves unknown and pending, within a bound. L-three: every difference with the outside becomes a break with an owner, within a day. Every fix from here on says which one it serves. Most designs are silent on liveness."], cls="theory")

S(plain("Theory · 3 of 6 · the central tension", "When is money final, and who decides?", table(["When", "What we know", "Mechanism that lives there"], [
  ["<b>seconds</b>", "a card answer, or nothing", "UNKNOWN and the resolver; a key on every send"],
  ["<b>1–2 days</b>", "the debit settled", "PENDING to SETTLED, posted from the settlement file"],
  ["<b>2 bank days</b>", "insufficient funds", "RETURNED, a reversal, a re-presentment by policy"],
  ["<b>60 days</b>", "unauthorised", "RETURNED, never retried; exposure reported by age"],
  ["<b>months</b>", "refunds, card disputes", "a new schedule version; a reversal dated now"],
  ["<b>every day</b>", "the bank's view", "three-way reconciliation"]], "bt sm") +
  line("Finance wants cash recognised early; risk wants to wait. Post at settlement, and age the exposure.", "a")), [
 "C: The central tension is when money is final, and who decides. In seconds, a card answer, or nothing. In a day or two, the debit settles. Two banking days, an insufficient-funds return. Sixty days, an unauthorised return. Months, refunds and card disputes. And every day, the bank's own view, which we must match.",
 "C: Finance wants cash recognised as early as possible. Risk would rather wait sixty days. The design that serves both posts the cash at settlement, and reports the exposure by age. Instant payment rails, spreading since twenty twenty-three, remove some pending states, but not returns, and not reconciliation."], cls="theory")

def mech(n, name, protects, how, rules, costs, say, live=True):
    S(plain(f"Theory · 4 of 6 · mechanism {n} of 7", name,
        f'<div class="prop {"live" if live else "safe"}"><div class="lbl">Property it protects</div><p>{protects}</p></div>'
        f'<div class="prop"><div class="lbl">How it works</div><p>{how}</p></div>'
        f'<div class="prop safe"><div class="lbl">Failure it rules out</div><p>{rules}</p></div>'
        f'<div class="prop" style="border-left-color:#d18f1c"><div class="lbl" style="color:#a86a12">What it costs</div><p>{costs}</p></div>'), say, cls="theory")

mech(1, "An immutable double-entry ledger, with a projection", "S2 and the audit.", "Every movement is a transaction of two or more lines that sum to zero in integer cents. Lines are inserted, never updated. A balance row is updated in the same commit, at a version, and is provable from the lines.",
     "Unexplainable balances, lost cents, two postings interleaving on one loan.", "Storage that only grows. Every correction is a reversing transaction.", [
 "C: Mechanism one, the immutable double-entry ledger. It protects S-two and the audit. Every movement is two or more lines that sum to zero in whole cents, inserted and never updated. And here I correct a common line: never store a balance is too strict. I keep a balance row, updated in the same commit, at a version, so it is fast to read and always provable from the lines. It rules out balances nobody can explain. It costs storage that only grows, and a reversing transaction for every mistake."], live=False)
mech(2, "A payment state machine with UNKNOWN and RETURNED", "S1 and L2.", "Scheduled, submitted, pending, settled. A timeout goes to UNKNOWN, a real state with exits. A return moves SETTLED to RETURNED and posts a reversal.",
     "A timeout treated as failure, then charged again. A return with nowhere to go.", "More states and transitions to test. Statements show “pending” for days.", [
 "C: Mechanism two, the payment state machine, with unknown and returned in it. It protects S-one and L-two. A timeout goes to unknown, which has its own exits. A return moves a settled payment to returned and posts a reversal. It rules out the double charge that follows treating a timeout as a failure, and a return that has nowhere to go. It costs more states to test, and pending shown to customers for days."], live=False)
mech(3, "Idempotency at three layers", "S1.", "The ledger transaction has a unique key: loan, instalment, attempt. The same key goes to the processor. And only one open intent may exist per instalment.",
     "A duplicate posting, a duplicate charge, two workers creating two intents.", "Key discipline. The rule that only a new decision gets a new attempt number.", [
 "C: Mechanism three, idempotency at three layers. It protects S-one. The ledger transaction carries a unique key built from the loan, the instalment and the attempt. The same key goes to the processor, so a resend returns the first result. And a unique index allows one open intent per instalment. Three layers, three different duplicates ruled out. It costs one discipline: retrying the same attempt reuses its key. Only a new decision to try again gets a new attempt number."], live=False)
mech(4, "The database as the queue", "L1.", "Due items are rows. Workers claim batches with FOR UPDATE SKIP LOCKED, and write the intent and an outbox row in the same commit. A sweeper returns stale claims.",
     "Lost or doubly claimed due items; a commit with no send, or a send with no record.", "Polling, and a sweeper to run.", [
 "C: Mechanism four, the database as the queue. It protects L-one. Due items are rows. Workers claim batches with a skip-locked query, so no two workers take the same row, and write the payment intent and an outbox row in the same commit. A sweeper returns claims that went stale. It rules out lost work and work done twice. It costs some polling, and a sweeper."])
mech(5, "A rail budget", "L1 and S3.", "A token bucket per rail, set below the contract. A day plan back-scheduled from the cut-off. A pause switch per rail. Live limits from the adapter.",
     "Self-inflicted throttling that turns into declines; a missed cut-off.", "Planning the day; spreading due dates at origination.", [
 "C: Mechanism five, a rail budget. It protects L-one, and S-three, because declines caused by our own throttling would be our fault. A token bucket per rail set below the contract, a day plan worked backwards from the cut-off, and a pause switch per rail. It rules out a midnight burst that the processor throttles into declines, and a missed cut-off. It costs planning, and some product work to spread due dates."])
mech(6, "Policy as versioned data", "S3 and the audit.", "The allocation waterfall, retry schedule, late fees and refund treatment are rules with versions and owners. Every posting records the version it used.",
     "Behaviour nobody can explain; a rule change applied to old loans by accident.", "A rules component. Owners in risk and legal who must approve changes.", [
 "C: Mechanism six, policy as versioned data. It protects S-three and the audit. The allocation order, the retry schedule, late fees and how refunds land are rules with versions and named owners, and every posting records the version it used. It rules out behaviour nobody can explain. It costs a rules component, and owners in risk and legal who sign off changes."], live=False)
mech(7, "Three-way reconciliation", "L3.", "The ledger produces expectations. The processor's report and the bank's statement are matched to them by reference, then by amount and a date window. Every difference is a typed break with an owner and an age.",
     "Silent divergence; a plug posted at month-end to make totals agree.", "A pipeline, a console, and people.", [
 "C: Mechanism seven, three-way reconciliation. It protects L-three. The ledger says what it expects. The processor's report and the bank statement are matched to it, line by line, by reference first. Every difference becomes a typed break with an owner and an age. It rules out silent divergence, and the plug at month-end that makes totals agree. It costs a pipeline, a console, and people."])

S(plain("Theory · 5 of 6 · the options, part one", "Three that look reasonable", table(["Approach", "Once per instalment", "Explains every cent", "Fails when"], [
  ("rej", ["A · A cron at midnight; a balance column; retry on any error", "no", "no", "the first timeout and retry; the processor throttles the midnight burst"]),
  ("rej", ["B · A message broker: 600,000 messages fanned out to workers, no state machine", "no", "no", "redelivery after a crash charges again; unknown and returned have no state; it solved load that wasn't a problem"]),
  ("rej", ["C · An event-sourced loan aggregate in a log, balances in stream processors", "with keys", "yes", "a refund or payoff needs a current balance now; corrections mean replays; heavier operations"])], "bt sm mx")), [
 "C: Now the options, each with the failure that rules it out. Three that look reasonable.",
 "C: A, a cron job at midnight, a balance column, retry on any error. It fails at the first timeout and retry, and the processor throttles the midnight burst. B, a message broker: six hundred thousand messages fanned out to workers, no state machine. A crash and redelivery charges again, unknown and returned have nowhere to live, and it solved a load problem we don't have. C, an event-sourced loan in a log. It explains every cent, but a refund or payoff needs a current balance right now, and every correction becomes a replay."], cls="theory")

S(plain("Theory · 5 of 6 · the options, part two", "The pick, and an honest alternative", table(["Approach", "Once per instalment", "Explains every cent", "Fails when"], [
  ("pick", ["D · Relational ledger + state machine + database as the queue + rail budget + policy as data + three-way reconciliation", "yes", "yes", "a processor that can't be queried by our key: then the settlement file decides, a day late"]),
  ("rej", ["E · Buy a servicing platform", "yes", "theirs", "product-specific refunds and terms; we must own the books of record"])], "bt sm mx")), [
 "C: D is the pick: a relational ledger, the state machine, the database as the queue, a rail budget, policy as data, and three-way reconciliation. It only fails when a processor gives us no way to ask about our own key, and then the settlement file decides, a day late.",
 "C: E, buy a servicing platform. For a small book with standard products, that is the honest first version. It fails when the product needs its own refund rules, or the company must keep its own books of record."], cls="theory")

S(plain("Theory · 5 of 6 · the pick", "D, and what it gives up", '<div class="cards c2">'
  '<div class="cd grn"><h3>What D buys</h3><p>Never guessing. A retry is harmless, an unknown has an exit, a return has a place, every balance is a sum, and the bank is checked daily.</p></div>'
  '<div class="cd red"><h3>What D gives up</h3><p>More states to test. A reconciliation team. “Pending” on statements for days. Every product change becomes a policy version with an owner.</p></div></div>' +
  line("A broker can still be added later for fan-out to other consumers. It is a choice, not a requirement.", "a")), [
 "C: What D buys is never guessing. A retry is harmless, an unknown has an exit, a return has a place to land, every balance is a sum, and the bank is checked daily. What it gives up: more states to test, a reconciliation team, pending on customer statements for days, and every product change becomes a policy version someone must own. I'd say that cost out loud, because it lands on product and finance."], cls="theory")

S(plain("Theory · 6 of 6 · the failure catalogue", "What will go wrong, which becomes the challenge list", table(["Failure", "Challenge"], [
  ["A card charge times out", "<b>1</b> · the crux, part one"],
  ["Six hundred thousand on one morning", "<b>2</b>"],
  ["A settled debit comes back, days or weeks later", "<b>3</b> · the crux, part two"],
  ["A refund changes the schedule mid-loan", "<b>4</b>"],
  ["A payoff while a debit is in flight", "<b>5</b>"],
  ["Month-end: our books and the bank's disagree", "<b>6</b>"],
  ["The card processor is down on the 1st", "<b>7</b>"],
  ["Nobody notices until close", "<b>8</b> · observability"]], "bt sm")), [
 "C: Last, the failure catalogue, which becomes the challenge list. A card charge times out, the first half of the crux. Six hundred thousand on one morning. A settled debit that comes back, the second half. A refund that changes the schedule. A payoff while a debit is in flight. A month-end that doesn't match. The card processor down on the first. And nobody noticing until close."], cls="theory")
