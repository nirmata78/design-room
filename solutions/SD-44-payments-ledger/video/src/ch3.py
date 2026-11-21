from dsl import *
import dsl

def th(): dsl.SL[-1]["cls"] = (dsl.SL[-1]["cls"] + " theory").strip()

chapter(3, "Theory", 2, "What makes this problem hard, in words that outlive any product name", [
 "C: A short theory chapter before any design, so the design can lean on it. Six parts: what a payment system is and is not, the properties, the central tension, seven mechanisms, an options matrix, and the failure catalogue. Every slide here carries a theory badge."]); th()

key("Theory · 1 of 6 · what it is", "One customer intent becomes <em>one movement</em> of money, recorded as <em>balanced, immutable</em> entries, and kept in <em>agreement</em> with the parties that actually move it.", [
 "V: A payment system turns a customer's intent to pay into exactly one movement of money between accounts, records every movement as balanced, immutable journal entries, and keeps its books in agreement with the outside parties that actually move the money.", "[pause: 1.0]",
 "C: Every clause is load-bearing. One intent, one movement: that is idempotency, not exactly-once delivery. Balanced: double entry, per currency, in integer minor units. Immutable: a correction is a new entry. And in agreement with the outside: reconciliation is a component, not a safety net."], cls="theory")

S(plain("Theory · 1 of 6 · what it is not", "Four things it is confused with", '<div class="cards c2">'
  '<div class="cd"><h3>The payment system is not the ledger</h3><p>One orchestrates an intent across outside parties. The other is the book of record. They fail differently.</p></div>'
  '<div class="cd"><h3>A ledger is not a balance table</h3><p>A balance is a sum over entries. A number that is updated in place cannot explain itself.</p></div>'
  '<div class="cd amb"><h3>Idempotency is not message de-duplication</h3><p>It is one effect per intent, with the original answer returned to every retry.</p></div>'
  '<div class="cd red"><h3>Exactly-once delivery is not exactly-once effect</h3><p>Across a network we can have the second. Never the first.</p></div></div>'), [
 "C: Four confusions. The payment system is not the ledger. One orchestrates an intent across outside parties, the other is the book of record, and they fail differently. A ledger is not a balance table: a balance is a sum, and a number updated in place cannot explain itself.",
 "C: Idempotency is not de-duplicating messages. It is one effect per intent, with the original answer returned to every retry. And here is the precision statement for this whole video: exactly-once delivery is impossible across a network. What we can build is at-least-once delivery with an effect that happens once."], cls="theory")

S(plain("Theory · 2 of 6 · the two properties", "State safety and liveness separately",
  '<div class="prop safe"><div class="lbl">Safety · must never happen</div><p><b>S1</b> One intent moves money twice.<br><b>S2</b> A journal transaction that does not balance, per currency, in integer minor units.<br><b>S3</b> History rewritten: a correction must be a new transaction.</p></div>'
  '<div class="prop live"><div class="lbl">Liveness · must eventually happen</div><p><b>L1</b> Every payment leaves “unknown” for a final state: in minutes by inquiry, at the latest at settlement.<br><b>L2</b> Every difference with the outside world becomes an owned break within a day.<br><b>L3</b> Every state change reaches the merchant.</p></div>'), [
 "V: Safety: one intent never moves money twice, every journal transaction balances, and history is never rewritten. Liveness: every payment leaves unknown for a final state, every difference with the outside world becomes an owned break within a day, and every change reaches the merchant.", "[pause: 0.8]",
 "C: Three safety properties and three liveness properties. Every fix from here on says which one it serves. Notice that liveness is where most designs are silent: they never say how an unknown ends."], cls="theory")

S(plain("Theory · 3 of 6 · the central tension", "Speed of the answer against certainty about the truth", table(["When", "What we know", "Mechanism that lives there"], [
  ["<b>2 seconds</b>", "approved, declined, or nothing", "idempotency key · the unknown state · answer pending"],
  ["<b>minutes</b>", "the processor's answer to our question", "the inquiry job, by our own reference"],
  ["<b>next day</b>", "the processor's books", "reconciliation against the settlement file"],
  ["<b>months</b>", "a dispute", "a new, adjusting transaction, dated now"]], "bt") +
  line("No mechanism replaces another. Each one closes what the earlier ones left open.", "a")), [
 "C: The central tension: the client wants an answer in two seconds, and the truth arrives over months. Back to that timeline as a table. At two seconds we know approved, declined, or nothing, and the tools are the idempotency key and the unknown state. In minutes, the inquiry. The next day, reconciliation. Months later, an adjusting transaction.",
 "C: The point is that no mechanism replaces another. A design that has idempotency but no reconciliation, or reconciliation but no unknown state, has a hole at one point on this line."], cls="theory")

def mech(n, name, protects, how, rules, costs, say, live=True):
    S(plain(f"Theory · 4 of 6 · mechanism {n} of 7", name,
        f'<div class="prop {"live" if live else "safe"}"><div class="lbl">Property it protects</div><p>{protects}</p></div>'
        f'<div class="prop"><div class="lbl">How it works</div><p>{how}</p></div>'
        f'<div class="prop safe"><div class="lbl">Failure it rules out</div><p>{rules}</p></div>'
        f'<div class="prop" style="border-left-color:#d18f1c"><div class="lbl" style="color:#a86a12">What it costs</div><p>{costs}</p></div>'), say, cls="theory")

mech(1, "An idempotency key, inserted first", "S1: one intent, one effect.", "The client sends a key. We insert it, unique per client, with a hash of the request, in the same transaction that creates the payment. The final response is stored on the same row.",
     "A retry or a concurrent duplicate creating a second payment; a changed retry silently accepted.", "A table with a retention window; an “in progress” answer the client must handle.", [
 "C: Mechanism one, the idempotency key, inserted first. It protects S-one. The client sends a key, and we insert it, unique per client, with a hash of the request, in the same transaction that creates the payment. The final response is stored on that row. It rules out a retry or a concurrent duplicate becoming a second payment. It costs a table with a retention window, and an in-progress answer clients must handle."], live=False)
mech(2, "An explicit state machine with “unknown”", "S1 and L1.", "Every payment moves through named states. A timeout or an ambiguous answer moves it to UNKNOWN, a real state with its own exits. The attempt is committed before the call goes out.",
     "A timeout treated as failure, which double-charges on retry; or as success, which loses money.", "More states and transitions to test. Clients see “pending”.", [
 "C: Mechanism two, a state machine with an unknown state. It protects S-one and L-one. A timeout or an ambiguous answer moves the payment to unknown: a real state with its own exits. And the attempt is committed before the call goes out, so a crash leaves evidence. It rules out treating a timeout as a failure, which double-charges on retry, or as a success, which loses money. It costs more states to test, and pending answers."], live=False)
mech(3, "An immutable double-entry journal", "S2, S3, and the audit.", "Every movement is a transaction of entries whose debits equal its credits, per currency. Entries are inserted, never updated. A balance is a projection.",
     "Unexplainable balances, lost cents, a hot row lock on a balance.", "Storage that grows forever. Reads need projections.", [
 "C: Mechanism three, the immutable double-entry journal. It protects S-two, S-three and the audit. Every movement is a set of entries whose debits equal its credits, per currency. Entries are inserted, never updated, and a balance is a projection over them. It rules out balances nobody can explain, lost cents, and a hot lock on a balance row. It costs storage that only grows, and projections for reads."], live=False)
mech(4, "A transactional outbox", "L3.", "The event is a row written in the same transaction as the state change. A relay reads committed rows and publishes them, at least once.",
     "A state committed with no event, or an event for a state that rolled back.", "A relay to run. Events at least once, so consumers de-duplicate by event ID.", [
 "C: Mechanism four, the transactional outbox. It protects L-three. The event is a row in the same transaction as the state change, and a relay publishes committed rows, at least once. It rules out a committed state with no event, and an event for a change that rolled back. It costs a relay to run, and consumers that de-duplicate by event I-D."])
mech(5, "Inquiry and reversal by our own reference", "L1, and S1 on retry.", "Each attempt carries a reference we generate. An inquiry asks the processor for that reference's status; an unwanted approval is reversed by the same reference.",
     "An unknown that stays unknown; a retry the processor cannot recognise as the same attempt.", "A job per processor, rate-limited. Processors differ in what they support.", [
 "C: Mechanism five, inquiry and reversal by our own reference. It protects L-one, and S-one on retry. Every attempt carries a reference we generate, so we can ask the processor what happened to it, and reverse it by the same reference. It rules out an unknown that never ends. It costs a job per processor, and processors differ in what they support."])
mech(6, "Reconciliation with expectations and owned breaks", "L2, and S2 against the outside world.", "The ledger produces what it expects each processor to settle. The raw settlement file is matched line by line. Every unmatched line is a break with a type, an owner and an age.",
     "Silent divergence from the counterparty's books.", "A pipeline, a finance-operations workflow, and people.", [
 "C: Mechanism six, reconciliation. It protects L-two, and correctness against the outside world. The ledger produces what it expects each processor to settle, the raw file is matched line by line, and every unmatched line becomes a break with a type, an owner and an age. It rules out silent divergence. It costs a pipeline, a workflow, and people."])
mech(7, "Sub-accounts or one writer for a hot account", "Throughput where a check needs a current balance.", "Split a hot account into N sub-accounts that receive writes in turn and are summed; or send the rare balance-checked operation through one writer per account.",
     "A merchant serialising on one row; a payout larger than the funds.", "Summing N rows; routing writes; a second place to be wrong.", [
 "C: Mechanism seven, for the hot account: sub-accounts, or one writer for the rare checked operation. It protects throughput where a check needs a current balance. It rules out a merchant serialising on one row, and a payout larger than the available funds. It costs a sum over several rows and a routing rule."])

S(plain("Theory · 5 of 6 · the options, part one", "Three ways that look reasonable", table(["Approach", "One effect per intent", "Explainable", "Fails when"], [
  ("rej", ["A · A balance column updated in a transaction; retries assumed safe", "no", "no", "the first timeout and retry: a double charge; the hot merchant's row lock"]),
  ("rej", ["B · A distributed transaction (two-phase commit) across our database and the processor", "would be", "would be", "always: the processor is not a participant in our transaction and will not hold a prepare for us"]),
  ("rej", ["C · An orchestrated saga with compensations, no ledger invariants", "partly", "no", "a compensation that itself times out; nothing says what the books should be"])], "bt sm mx")), [
 "C: Now the options, each with the failure that rules it out. Three that look reasonable first.",
 "C: A, a balance column updated in a transaction, with retries assumed safe. It fails at the first timeout and retry: a double charge. B, a distributed transaction across our database and the processor. It fails always: the processor is not a participant in our transaction, and it will not hold a prepared state while we decide. C, a saga with compensations and no ledger rules. It fails when a compensation itself times out, and it never says what the books should be."], cls="theory")

S(plain("Theory · 5 of 6 · the options, part two", "The pick, and two honest alternatives", table(["Approach", "One effect per intent", "Explainable", "Fails when"], [
  ("pick", ["D · State machine with unknown + idempotency key + immutable journal + outbox + inquiry + reconciliation", "yes", "yes", "a processor with no way to query by our reference: then the settlement file is the only arbiter, a day late"]),
  ("rej", ["E · An event-sourced ledger in a log, balances in stream processors", "with keys", "yes", "a synchronous check (refund ≤ captured, payout ≤ available) needs a current balance now"]),
  ("rej", ["F · Buy: the processor's own records, or a ledger service", "yes", "theirs", "more than one processor, or the company must keep its own books of record"])], "bt sm mx")), [
 "C: Part two. D is the pick: the state machine with unknown, the idempotency key, the immutable journal, the outbox, the inquiry and reconciliation. It fails only when a processor gives no way to ask about our reference, and then the settlement file is the arbiter, a day late.",
 "C: E, an event-sourced ledger in a log. It is how I would build the projections inside D, but on its own it fails when a refund or a payout needs a current balance right now. F, buy: the processor's own records. That is the honest first version for a small company with one processor. It fails at the second processor, or when we must keep our own books."], cls="theory")

S(plain("Theory · 5 of 6 · the pick", "D, and what it gives up", '<div class="cards c2">'
  '<div class="cd grn"><h3>What D buys</h3><p>Never guessing. A retry is harmless, an unknown has an exit, every balance is a sum, and the outside world is checked daily.</p></div>'
  '<div class="cd red"><h3>What D gives up</h3><p>More states to test. A reconciliation team. “Pending” answers that every merchant integration must handle.</p></div></div>' +
  line("F is the right V0 for one processor. E is how projections are built inside D.", "a")), [
 "C: So, D. What it buys is never guessing. A retry is harmless, an unknown has an exit, every balance is a sum of facts, and the outside world is checked daily. What it gives up: more states to test, a reconciliation function with people in it, and pending answers that every merchant integration has to handle. I'd say that cost out loud, because it lands on other teams."], cls="theory")

S(plain("Theory · 6 of 6 · the failure catalogue", "What will go wrong, which becomes the challenge list", table(["Failure", "Challenge"], [
  ["A timeout, an ambiguous result, a processor down", "<b>1</b> · the crux, part one"],
  ["Concurrent retries; a retry with a changed amount", "<b>2</b>"],
  ["A crash between commit and event", "<b>3</b>"],
  ["The hot merchant", "<b>4</b>"],
  ["Partial refunds; a chargeback months later", "<b>5</b>"],
  ["Our books and the processor's disagree", "<b>6</b> · the crux, part two"],
  ["A bug posted wrong entries; money already paid out", "<b>7</b>"],
  ["Nobody notices", "<b>8</b> · observability"]], "bt sm") +
  line("Floats and currencies: covered on the API slides, not a challenge.", "a")), [
 "C: Last, the failure catalogue, which becomes the challenge list. A timeout, the crux. Concurrent retries. A crash between commit and event. The hot merchant. Refunds and late chargebacks. Books that disagree with the processor's, the second half of the crux. A bug that posted wrong entries. And nobody noticing. Floating-point money is a real failure too, but it is settled on the A-P-I slides: integer minor units and a currency on every amount."], cls="theory")
