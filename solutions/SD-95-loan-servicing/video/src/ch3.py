from dsl import *
import dsl

def th(): dsl.SL[-1]["cls"] = (dsl.SL[-1]["cls"] + " theory").strip()

chapter(3, "Theory", 2, "What makes this problem hard, in words that outlive any product name", [
 "C: A short theory chapter before any design, so the design can lean on it. Five parts: what loan servicing is and is not, the properties, the central tension, seven mechanisms each with the picture that fits it, and the options, one slide each. The failures come later, as the challenges. Every slide here carries a theory badge."]); th()

key("Theory · 1 of 5 · what it is", "Turn each loan's <em>terms</em> into a schedule, collect each amount <em>once</em> through rails that answer in days and <em>reverse weeks later</em>, record every movement as <em>balanced, immutable</em> lines, and <em>prove daily</em> the books agree with the bank.", [
 "V: A loan servicing system turns each loan's terms into a schedule, collects each amount once through rails that answer in days and can reverse weeks later, records every movement as balanced, immutable lines, and proves every day that its books agree with the bank.", "[pause: 1.0]",
 "C: Every clause does work. Terms into a schedule: the rules are versioned data, not code paths. Once: idempotency, not exactly-once delivery, which does not exist across a network. Answer in days and reverse weeks later: pending, unknown and returned are states. Balanced and immutable: double entry, corrections by reversal. And proves daily: reconciliation is a component, not an audit at year end."], cls="theory")

S(plain("Theory · 1 of 5 · what it is not", "Four things it is confused with", '<div class="cards c2">'
  '<div class="cd"><h3>Not a payment gateway</h3><p>A gateway turns one intent into one payment in seconds (SD-44). Servicing drives many payments over months, against a schedule that changes.</p></div>'
  '<div class="cd"><h3>Not a cron job</h3><p>A cron job fires work. It does not know what was attempted, what is pending, or what came back.</p></div>'
  '<div class="cd amb"><h3>A ledger is not a balance table</h3><p>A balance is a sum of lines. A number updated in place cannot explain itself to an auditor.</p></div>'
  '<div class="cd red"><h3>Settled is not final</h3><p>A bank debit can be returned after it settles. Final is a later, rule-defined point.</p></div></div>'), [
 "C: Four confusions. It is not a payment gateway: a gateway turns one intent into one payment in seconds. Servicing drives many payments over months, against a schedule that keeps changing. It is not a cron job: a cron job fires work, but it does not know what was attempted, what is pending, or what came back.",
 "C: A ledger is not a balance table: a balance is a sum, and a number updated in place cannot explain itself. And settled is not final: a bank debit can be returned after it settles, so final is a later point, defined by the network's rules."], cls="theory")

props(S1="no-twice-collect", S2="ledger-balanced-immutable", S3="no-unfair-penalty", L1="attempt-by-cutoff", L2="every-unknown-ends", L3="every-break-owned")
S(plain("Theory · 2 of 5 · the two properties", "State safety and liveness separately",
  '<div class="prop safe"><div class="lbl">Safety · must never happen</div><p>' + pid("S1") + ' One instalment collected twice.<br>' + pid("S2") + ' A ledger transaction that does not sum to zero in integer cents, or a line that is edited.<br>' + pid("S3") + ' A customer penalised beyond policy, or for our failure.</p></div>'
  '<div class="prop live"><div class="lbl">Liveness · must eventually happen</div><p>' + pid("L1") + ' Every due instalment is attempted on its due date, before the cut-off.<br>' + pid("L2") + ' Every payment leaves UNKNOWN and PENDING for SETTLED or RETURNED, within a bound.<br>' + pid("L3") + ' Every difference between ledger, processor and bank becomes an owned break within a day.</p></div>'), [
 "[+]", "C: Three safety properties, things that must never happen. " + ps("S1") + ": one instalment collected twice. " + ps("S2") + ": a ledger transaction that doesn't sum to zero in whole cents, or a line that gets edited. " + ps("S3") + ": a customer penalised beyond policy, or for our own failure.", "[+]",
 "C: And three liveness properties, things that must eventually happen. " + ps("L1") + ": every due instalment is attempted on its due date, before the cut-off. " + ps("L2") + ": every payment leaves unknown and pending, within a bound. " + ps("L3") + ": every difference with the outside becomes a break with an owner, within a day.",
 "C: Every fix from here on names the tag of the property it serves. Most designs are silent on liveness."], cls="theory")

S(plain("Theory · 3 of 5 · the central tension", "When is money final, and who decides?", table(["When", "What we know", "Mechanism that lives there"], [
  ["<b>seconds</b>", "a card answer, or nothing", "UNKNOWN and the resolver; a key on every send"],
  ["<b>1–2 days</b>", "the debit settled", "PENDING to SETTLED, posted from the settlement file"],
  ["<b>2 bank days</b>", "insufficient funds", "RETURNED, a reversal, a re-presentment by policy"],
  ["<b>60 days</b>", "unauthorised", "RETURNED, never retried; exposure reported by age"],
  ["<b>months</b>", "refunds, card disputes", "a new schedule version; a reversal dated now"],
  ["<b>every day</b>", "the bank's view", "three-way reconciliation"]], "bt sm") +
  line("Finance wants cash recognised early; risk wants to wait. Post at settlement, and age the exposure.", "a")), [
 "C: The central tension is when money is final, and who decides. In seconds, a card answer, or nothing. In a day or two, the debit settles. Two banking days, an insufficient-funds return. Sixty days, an unauthorised return. Months, refunds and card disputes. And every day, the bank's own view, which we must match.",
 "C: Finance wants cash recognised as early as possible. Risk would rather wait sixty days. The design that serves both posts the cash at settlement, and reports the exposure by age. Instant payment rails, spreading since twenty twenty-three, remove some pending states, but not returns, and not reconciliation."], cls="theory")


def M(n, name, kind, svg, cap, prot, how, rules, costs, say, steps_say, live=False):
    """say: [intro, protects, how, rules, costs] sentences; steps_say: one sentence per reveal step of the picture."""
    lines = ["C: " + say[0]]
    for s in say[1:]: lines += ["[+]", "C: " + s]
    for s in steps_say: lines += ["[+]", "C: " + s]
    mech_slide(n, 7, name, prot, how, rules, costs, lines, diagram=(kind, svg, cap), live=live)

M(1, "An immutable double-entry ledger, with a projection", "erd", "m-ledger", "Figure 3.1 — one transaction, lines that sum to zero, a balance updated in the same commit",
  pid("S2") + " and the audit.", "Every movement is a transaction of two or more lines that sum to zero in integer cents. Lines are inserted, never updated. A balance row is updated in the same commit, at a version.",
  "Unexplainable balances, lost cents, two postings interleaving on one loan.", "Storage that only grows. Every correction is a reversing transaction.",
  ["Mechanism one, the immutable double-entry ledger, drawn as the entities and their keys.",
   "It protects " + ps("S2") + ", and the audit.",
   "Every movement is two or more lines that sum to zero in whole cents, inserted and never updated. And I correct a common line: never store a balance is too strict. I keep a balance row, at a version, provable from the lines.",
   "It rules out balances nobody can explain, and two postings interleaving on one loan.",
   "It costs storage that only grows, and a reversing transaction for every mistake."],
  ["The transaction is the unit. It carries a unique idempotency key, an effective date, the time we booked it, and the policy version used.",
   "Its lines belong to it, and they must sum to zero. An account and an amount in cents, nothing else.",
   "The balance row is updated in the same commit, at a version: fast to read, and always provable from the lines."])
M(2, "A payment state machine with UNKNOWN and RETURNED", "state", "m-states", "Figure 3.2 — the lifecycle of one payment; a timeout and a return both have exits",
  pid("S1") + " and " + pid("L2") + ".", "Due, intent open, submitted, pending, settled. A timeout goes to UNKNOWN, a real state with exits. A return moves SETTLED to RETURNED and posts a reversal.",
  "A timeout treated as failure, then charged again. A return with nowhere to go.", "More states and transitions to test. Statements show pending for days.",
  ["Mechanism two, the payment state machine, with unknown and returned in it.",
   "It protects " + ps("S1") + " and " + ps("L2") + ".",
   "A timeout goes to unknown, which has its own exits. A return moves a settled payment to returned and posts a reversal.",
   "It rules out the double charge that follows treating a timeout as a failure, and a return that has nowhere to go.",
   "It costs more states to test, and pending shown to customers for days."],
  ["A payment is due, claimed with one open intent, and submitted with its key.",
   "A timeout does not mean failure: it is unknown. One exit asks the processor by the same key.",
   "If the answer is accepted it is pending, and pending ends at the settlement file, as settled. If never seen, it is due again, safely.",
   "And settled is not final: a return file moves it to returned, and policy decides whether to try again. Every state has an exit and a date by which it must use it."])
M(3, "Idempotency at three layers", "seq", "m-idem", "Figure 3.3 — a timeout, a query by the same key, and no second charge",
  pid("S1") + ".", "The ledger transaction has a unique key: loan, instalment, attempt. The same key goes to the processor. And only one open intent may exist per instalment.",
  "A duplicate posting, a duplicate charge, two workers creating two intents.", "Key discipline: only a new decision gets a new attempt number.",
  ["Mechanism three, idempotency at three layers, shown at protocol level.",
   "It protects " + ps("S1") + ".",
   "The ledger transaction carries a unique key built from loan, instalment and attempt. The same key goes to the processor, so a resend returns the first result. A unique index allows one open intent per instalment.",
   "It rules out a duplicate posting, a duplicate charge, and two workers creating two intents.",
   "It costs key discipline: only a new decision gets a new attempt number."],
  ["The dispatcher inserts the transaction first, with its key.", "The unique key accepts it.", "It sends the charge to the processor with the same key.", "The reply is a timeout.",
   "The intent becomes unknown. It does not retry as new.", "It queries the processor by the key.", "The processor answers with the first result, not a second charge, and posting it again with the same key is a no-op."])
M(4, "The database as the queue", "c4", "m-queue", "Figure 3.4 — C4 component view: claim, intent and outbox in one commit",
  pid("L1") + ".", "Due items are rows. Workers claim batches with FOR UPDATE SKIP LOCKED, and write the intent and an outbox row in the same commit. A sweeper returns stale claims.",
  "Lost or doubly claimed due items; a commit with no send, or a send with no record.", "Polling, and a sweeper to run.",
  ["Mechanism four, the database as the queue, drawn as the components inside the schedule service.",
   "It protects " + ps("L1") + ".",
   "Due items are rows. Workers claim batches with a skip-locked query, and write the payment intent and an outbox row in the same commit. A sweeper returns claims that went stale.",
   "It rules out lost or doubly claimed due items, a commit with no send, and a send with no record.",
   "It costs polling, and a sweeper to run."],
  ["The claimer takes five hundred rows at a time from the servicing database.", "Per row, the intent writer opens one intent, enforced by a unique index.", "And adds the outbox row in the same commit.",
   "The sweeper releases claims that went stale after five minutes, and the dispatcher drains the outbox."], live=True)
M(5, "A rail budget", "c4", "m-budget", "Figure 3.5 — C4 component view: the day plan sets the rate, the bucket enforces it",
  pid("L1") + " and " + pid("S3") + ".", "A token bucket per rail, set below the contract. A day plan back-scheduled from the cut-off. A pause switch per rail. Live limits from the adapter.",
  "Self-inflicted throttling that turns into declines; a missed cut-off.", "Planning the day; spreading due dates at origination.",
  ["Mechanism five, a rail budget, drawn inside the dispatcher.",
   "It protects " + ps("L1") + ", and " + ps("S3") + ", because declines caused by our own throttling would be our fault.",
   "A token bucket per rail set below the contract, a day plan worked backwards from the cut-off, and a pause switch per rail.",
   "It rules out self-inflicted throttling that turns into declines, and a missed cut-off.",
   "It costs planning the day, and spreading due dates at origination."],
  ["The day plan is worked back from the fourteen hundred cut-off.", "The token bucket sets the rate: ninety a second against a contract of a hundred.", "The pause switch closes it by hand or automatically.",
   "Live limits from the adapter lower it.", "Charges leave only at that rate, toward the card processor."])
M(6, "Policy as versioned data", "erd", "m-policy", "Figure 3.6 — every posting and every schedule names the policy version it used",
  pid("S3") + " and the audit.", "Allocation waterfall, retry schedule, late fees and refund treatment are rules with versions and owners. Every posting records the version it used.",
  "Behaviour nobody can explain; a rule change applied to old loans by accident.", "A rules component. Owners in risk and legal who must approve changes.",
  ["Mechanism six, policy as versioned data, drawn as the keys that tie it to the books.",
   "It protects " + ps("S3") + " and the audit.",
   "The allocation order, the retry schedule, late fees and how refunds land are rules with versions and named owners, and every posting records the version it used.",
   "It rules out behaviour nobody can explain, and a rule change applied to old loans by accident.",
   "It costs a rules component, and owners in risk and legal who must approve changes."],
  ["A policy version holds the product, the allocation order, the retry schedule and the fee rule, with an owner and an approver.", "Each schedule version points at the policy it was built from.",
   "And each ledger transaction points at the rule it applied."])
M(7, "Three-way reconciliation", "seq", "m-recon", "Figure 3.7 — the ledger's expectations against the processor and the bank",
  pid("L3") + ".", "The ledger produces expectations. The processor's report and the bank's statement are matched to them by reference, then by amount and a date window. Every difference is a typed break with an owner and an age.",
  "Silent divergence; a plug posted at month-end to make totals agree.", "A pipeline, a console, and people.",
  ["Mechanism seven, three-way reconciliation, as a message sequence.",
   "It protects " + ps("L3") + ".",
   "The ledger says what it expects. The processor's report and the bank statement are matched to it line by line, by reference first. Every difference becomes a typed break with an owner and an age.",
   "It rules out silent divergence, and a plug posted at month-end to make totals agree.",
   "It costs a pipeline, a console, and people."],
  ["The ledger sends its expected lines for the day.", "The processor reports card settlements.", "The bank sends debits and returns.",
   "Reconciliation matches by reference first, then by amount and a date window.", "Anything left becomes a typed break with an owner and an age."], live=True)

def O(letter, name, verdict, pros, cons, pits, svg, say, pick=False):
    """say[0] is spoken with nothing revealed; then one line per unit: pros, cons, pitfalls, picture steps."""
    lines = ["C: " + say[0]]
    for s in say[1:]: lines += ["[+]", "C: " + s]
    option_slide(letter, name, verdict, pros, cons, pits, svg, lines, pick=pick)

O("A", "A midnight cron and a balance column", "Rejected · fails at the first timeout",
  ["Trivially simple", "Fine for a handful of loans"], ["No state for unknown or returned", "A balance in place: no history"],
  ["2,000 charges a second against a contract of 100", "The first timeout and retry charges twice"], "opt-a", [
  "Option A, the first thing most people draw: a cron job at midnight, a balance column, retry on any error.",
  "It is trivially simple.", "And fine for a handful of loans.", "But it has no state for unknown or returned.", "And a balance updated in place cannot explain itself.",
  "The pitfall: two thousand charges a second against a contract of a hundred.", "And the first timeout, retried as new, charges the customer twice.",
  "The job loops over everything due today.", "It updates the balance in place.", "And hits a card processor that throttles."])
O("B", "A message broker with 600,000 messages", "Rejected · solves a load that is not the problem",
  ["Absorbs bursts", "Familiar fan-out to workers"], ["Redelivery is the default", "Still needs its own state and ledger"],
  ["A redelivery after a crash charges again", "Unknown and returned have no home", "Built for a peak of 42 a second that a database handles"], "opt-b", [
  "Option B, a message broker: every instalment becomes a message and workers charge per message.",
  "It absorbs bursts.", "And fan-out to workers is familiar.", "But redelivery is the default behaviour.", "And we would still need our own state and ledger.",
  "The pitfall: a redelivery after a crash charges again.", "Unknown and returned have no place to live.", "And it solves a load that is not the problem: forty-two a second.",
  "The scheduler publishes six hundred thousand messages.", "The broker delivers, and may deliver twice.", "Workers charge per message, with no state machine.", "Toward the same processor."])
O("C", "An event-sourced loan aggregate", "Rejected · heavier than the need",
  ["Full history by construction"], ["A payoff needs the current balance now", "Corrections mean replays", "Heavier operations"],
  ["A stale view quotes the wrong payoff", "A replay re-triggers side effects"], "opt-c", [
  "Option C, an event-sourced loan: balances come from stream processors over a log.",
  "Full history comes by construction.", "But a payoff needs the current balance now.", "Corrections mean replays.", "And the operations are heavier.",
  "The pitfall: an eventually consistent view can quote a stale payoff.", "And a replay can re-trigger side effects.",
  "Each loan is an aggregate.", "Its events go to a log, the source of truth.", "Stream processors consume them.", "And update the balance views."])
O("D", "Relational ledger, state machine, database as the queue", "The pick · with an honest alternative in B-simple",
  ["Intent and outbox commit atomically", "Every cent explained, every break owned"], ["More states to test", "A reconciliation team"],
  ["A processor that cannot be queried by our key: the settlement file decides, a day late", "A claim with no sweeper strands rows"], "opt-d", [
  "Option D, the pick: a relational ledger, the state machine, the database as the queue, a rail budget, policy as data, three-way reconciliation.",
  "The intent and the outbox row commit atomically.", "Every cent is explained and every break is owned.", "It costs more states to test.", "And a reconciliation team.",
  "The pitfall: a processor that cannot be queried by our key. Then the settlement file decides, a day late.", "And a claim without a sweeper strands rows.",
  "Schedule and collect claim and commit in one transaction, against the servicing database that holds the ledger, the intents and the outbox.", "The dispatcher charges with the key.",
  "Toward the rails.", "The resolver and file ingest take the answers and the files back and post them, and reconciliation checks the books against the bank every day."], pick=True)
O("E", "Buy a servicing platform", "Rejected · for this scope; the honest first version for a small book",
  ["Fastest to a first version", "Standard products are covered"], ["Their refund rules, not ours", "We must own the books of record"],
  ["Product-specific refunds cannot be expressed", "The daily export is a reconciliation job by another name"], "opt-e", [
  "Option E, buy a servicing platform. For a small book with standard products, that is the honest first version.",
  "It is the fastest way to a first version.", "And standard products are covered.", "But the refund rules are theirs, not ours.", "And the company must own its books of record.",
  "The pitfall: a product-specific refund cannot be expressed.", "And the daily export is a reconciliation job by another name.",
  "Origination sends them the booked loan.", "Their platform keeps the schedule, the ledger and the rules.", "We get a daily export."])

S(plain("Theory · 5 of 5 · the options, side by side", "The matrix, as a summary", table(["Approach", "Once per instalment", "Explains every cent", "Fails when"], [
  ("rej", ["A · midnight cron, balance column", "no", "no", "the first timeout and retry"]),
  ("rej", ["B · a message broker", "no", "no", "redelivery after a crash"]),
  ("rej", ["C · an event-sourced aggregate", "with keys", "yes", "a payoff needs a balance now"]),
  ("pick", ["D · ledger, state machine, database as the queue", "yes", "yes", "a processor we cannot query by our key"]),
  ("rej", ["E · buy a platform", "yes", "theirs", "product-specific refunds, books of record"])], "bt sm mx")), [
 "C: The five side by side, as a summary only.", "[+]", "C: A fails at the first timeout and retry.", "[+]", "C: B fails on redelivery after a crash.", "[+]",
 "C: C fails when a payoff needs a balance now.", "[+]", "V: D is the pick.", "[+]", "C: E is the honest first version for a small book, and fails on product-specific refunds."], cls="theory")

S(plain("Theory · 5 of 5 · the pick", "D, and what it gives up", '<div class="cards c2">'
  '<div class="cd grn"><h3>What D buys</h3><p>Never guessing. A retry is harmless, an unknown has an exit, a return has a place, every balance is a sum, and the bank is checked daily.</p></div>'
  '<div class="cd red"><h3>What D gives up</h3><p>More states to test. A reconciliation team. “Pending” on statements for days. Every product change becomes a policy version with an owner.</p></div></div>' +
  line("A broker can still be added later for fan-out to other consumers. It is a choice, not a requirement.", "a")), [
 "C: What D buys is never guessing. A retry is harmless, an unknown has an exit, a return has a place to land, every balance is a sum, and the bank is checked daily.", "[+]",
 "C: What it gives up: more states to test, a reconciliation team, pending on customer statements for days, and a policy owner for every product change.", "[+]",
 "C: A broker can still be added later for fan-out to other consumers. It is a choice, not a requirement."], cls="theory")
