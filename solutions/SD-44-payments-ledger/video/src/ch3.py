from dsl import *
import dsl
P = "[+]"

def th(): dsl.SL[-1]["cls"] = (dsl.SL[-1]["cls"] + " theory").strip()

chapter(3, "Theory", 2, "What makes this problem hard, in words that outlive any product name", [
 "C: A short theory chapter before any design, so the design can lean on it. What a payment system is and is not, the properties, the central tension, five mechanisms, an options matrix, and the failure catalogue."]); th()

key("Theory · 1 of 6 · what it is", "One customer intent becomes <em>one movement</em> of money, recorded as <em>balanced, immutable</em> entries, and kept in <em>agreement</em> with the parties that actually move it.", [
 "V: A payment system turns a customer's intent to pay into exactly one movement of money, records every movement as balanced, immutable entries, and keeps its books in agreement with the outside parties that actually move the money.", "[pause: 1.0]"], cls="theory")

S(plain("Theory · 1 of 6 · what it is not", "Four things it is confused with", cards(
  ("", "The payment system is not the ledger", "One orchestrates an intent across outside parties. The other is the book of record. They fail differently."),
  ("", "A ledger is not a balance table", "A balance is a sum over entries. A number updated in place cannot explain itself."),
  ("amb", "Idempotency is not message de-duplication", "It is one effect per intent, with the original answer returned to every retry."),
  ("red", "Exactly-once delivery is not exactly-once effect", "Across a network we can have the second, never the first."))), [
 "C: Four confusions.", P,
 "C: The payment system is not the ledger. One orchestrates an intent across outside parties, the other is the book of record, and they fail differently.", P,
 "C: A ledger is not a balance table. A balance is a sum, and a number updated in place cannot explain itself.", P,
 "C: Idempotency is not de-duplicating messages. It is one effect per intent, with the original answer returned to every retry.", P,
 "C: And the precision statement for this video: exactly-once delivery is impossible across a network. What we can build is at-least-once delivery with an effect that happens once."], cls="theory")

S(plain("Theory · 2 of 6 · the two properties", "Safety and liveness, separately",
  '<div class="prop safe"><div class="lbl">Safety · must never happen</div><p><b>S1</b> One intent moves money twice.<br><b>S2</b> A journal transaction that does not balance.<br><b>S3</b> History rewritten: a correction is a new transaction.</p></div>'
  '<div class="prop live"><div class="lbl">Liveness · must eventually happen</div><p><b>L1</b> Every payment leaves “unknown” for a final state.<br><b>L2</b> Every difference with the outside world becomes an owned break within a day.<br><b>L3</b> Every state change reaches the merchant.</p></div>'), [
 P, "V: Safety: one intent never moves money twice, every journal transaction balances, and history is never rewritten.", P,
 "V: Liveness: every payment leaves unknown for a final state, every difference with the outside world becomes an owned break within a day, and every change reaches the merchant.",
 "C: Every fix from here on says which of the six it serves. Liveness is where most designs are silent: they never say how an unknown ends."], cls="theory")

S(plain("Theory · 3 of 6 · the central tension", "Speed of the answer against certainty about the truth", table(["When", "What we know", "Mechanism that lives there"], [
  ["<b>2 seconds</b>", "approved, declined, or nothing", "idempotency key · the unknown state · pending"],
  ["<b>minutes</b>", "the processor's answer to our question", "the inquiry, by our own reference"],
  ["<b>next day</b>", "the processor's books", "reconciliation against the settlement file"],
  ["<b>months</b>", "a dispute", "a new transaction, dated now"]], "bt")), [
 "C: The central tension: an answer in two seconds, and a truth that arrives over months. Back to the timeline as a table.", P,
 "C: At two seconds we know approved, declined, or nothing. The tools are the idempotency key and the unknown state.", P,
 "C: In minutes, the inquiry by our own reference.", P,
 "C: The next day, reconciliation.", P,
 "C: Months later, a new transaction dated now. No mechanism replaces another. A design with idempotency and no reconciliation has a hole at one point on this line."], cls="theory")

def mech(n, name, protects, how, rules, costs, say, live=False):
    S(plain(f"Theory · 4 of 6 · mechanism {n} of 5", name,
        f'<div class="prop {"live" if live else "safe"}"><div class="lbl">Property it protects</div><p>{protects}</p></div>'
        f'<div class="prop"><div class="lbl">How it works</div><p>{how}</p></div>'
        f'<div class="prop safe"><div class="lbl">Failure it rules out</div><p>{rules}</p></div>'
        f'<div class="prop" style="border-left-color:#fbbc05"><div class="lbl" style="color:#b06000">What it costs</div><p>{costs}</p></div>'), say, cls="theory")

mech(1, "M1 · An idempotency key, inserted first", "S1: one intent, one effect.", "The client sends a key. We insert it, unique per client, with a hash of the request, in the transaction that creates the payment. The final response is stored on the row.",
     "A retry or a concurrent duplicate becoming a second payment; a changed retry silently accepted.", "A table with a retention window; an “in progress” answer clients must handle.", [
 P, "C: Mechanism one, the idempotency key, inserted first. It protects S-one.", P,
 "C: The client sends a key. We insert it, unique per client, with a hash of the request, in the transaction that creates the payment. The final response is stored on the row.", P,
 "C: It rules out a retry or a concurrent duplicate becoming a second payment, and a changed retry silently accepted.", P,
 "C: It costs a table with a retention window, and an in-progress answer clients must handle."])
mech(2, "M2 · A state machine with “unknown”, and an inquiry", "S1 and L1.", "Named states, legal edges only. A timeout or an ambiguous answer moves the payment to UNKNOWN, with its own exits. The attempt is committed, with our reference, before the call goes out. An inquiry by that reference ends the unknown.",
     "A timeout treated as a failure, which double-charges on retry; or as a success, which loses money.", "More states to test. Clients see “pending”. A job per processor, rate-limited.", [
 P, "C: Mechanism two, a state machine with an unknown state, and an inquiry. It protects S-one and L-one.", P,
 "C: Named states and legal edges only. A timeout moves the payment to unknown, which has its own exits. The attempt is committed, with our own reference, before the call goes out, and an inquiry by that reference ends the unknown.", P,
 "C: It rules out treating a timeout as a failure, which double-charges on retry, or as a success, which loses money.", P,
 "C: It costs more states to test, pending answers, and an inquiry job per processor."], live=True)
mech(3, "M3 · An immutable double-entry journal", "S2, S3, and the audit.", "Every movement is a transaction of entries whose debits equal its credits, per currency, checked at commit. Entries are inserted, never updated. A balance is a projection. The partition key is the owner.",
     "Unexplainable balances, lost cents, and a hot lock on a balance row.", "Storage that only grows. Reads need projections.", [
 P, "C: Mechanism three, the immutable double-entry journal. It protects S-two, S-three and the audit.", P,
 "C: Every movement is a transaction whose debits equal its credits, per currency, checked at commit. Entries are inserted, never updated, and a balance is a projection over them. The partition key is the owner, the merchant.", P,
 "C: It rules out balances nobody can explain, lost cents, and a hot lock on a balance row.", P,
 "C: It costs storage that only grows, and projections for reads."])
mech(4, "M4 · A transactional outbox, read from the log", "L3.", "The event is a row written in the same transaction as the state change. Change capture reads the database's write-ahead log and publishes committed rows in order, at least once.",
     "A state committed with no event, or an event for a state that rolled back.", "A capture pipeline to run. Delivery is at least once, so consumers de-duplicate by event ID.", [
 P, "C: Mechanism four, the transactional outbox. It protects L-three.", P,
 "C: The event is a row in the same transaction as the state change. Change capture reads the database's write-ahead log and publishes committed rows in order, at least once.", P,
 "C: It rules out a committed state with no event, and an event for a change that rolled back.", P,
 "C: It costs a pipeline to run, and consumers that de-duplicate by event I-D."], live=True)
mech(5, "M5 · Reconciliation with expectations and owned breaks", "L2, and S2 against the outside world.", "The ledger produces what it expects each processor to settle. The raw file is matched line by line, by reference. Every unmatched line is a break with a type, an owner and an age.",
     "Silent divergence from the counterparty's books.", "A pipeline, a finance-operations workflow, and people.", [
 P, "C: Mechanism five, reconciliation. It protects L-two, and correctness against the outside world.", P,
 "C: The ledger produces what it expects each processor to settle. The raw file is matched line by line, by reference, and every unmatched line becomes a break with a type, an owner and an age.", P,
 "C: It rules out silent divergence from the counterparty's books.", P,
 "C: It costs a pipeline, a workflow, and people."], live=True)

S(plain("Theory · 4 of 6 · mechanisms at work", "Where each mechanism will live", table(["Mechanism", "Container", "In one clause"], [
  ["<b>M1</b> idempotency key", "Payments API, ledger database", "a unique insert decides which request counts"],
  ["<b>M2</b> state machine, inquiry", "Payment service, inquiry job", "legal edges; UNKNOWN has two exits"],
  ["<b>M3</b> journal", "Ledger database, balance projector", "insert-only entries, partitioned by merchant"],
  ["<b>M4</b> outbox, change capture", "Ledger database, outbox relay", "the event commits with the state"],
  ["<b>M5</b> reconciliation", "Reconciliation, finance ops", "expectations matched by reference"]], "bt xs mx")), [
 "C: Where each mechanism will live. The system itself is drawn once, in chapter five; here only the labels.", P,
 "C: M-one, the key, in the A-P-I and the ledger database: a unique insert decides which request counts.", P,
 "C: M-two in the payment service and the inquiry job.", P,
 "C: M-three in the ledger database and the balance projector.", P,
 "C: M-four in the database and the outbox relay.", P,
 "C: M-five in reconciliation and finance operations. These labels come back as badges on the container view."], cls="theory")

S(dia("Theory · 4 of 6 · a mechanism at protocol level", "One capture, as one transaction", "seq-th-post"), [
 P, "C: The hardest mechanism, operating. The payment service opens a transaction.", P,
 "C: The state moves from auth pending to captured, in a conditional update that names the state it expects.", P,
 "C: One row changed: the edge was legal.", P,
 "C: Then the journal transaction and its three entries: debit one thousand and fifty, credit one thousand and twenty, credit thirty.", P,
 "C: And the outbox row.", P,
 "C: A deferred check at commit: debits one thousand and fifty equal credits one thousand and fifty.", P,
 "C: Commit.", P,
 "C: Had the entries been unbalanced, the whole transaction would be rejected. There is never a moment where the state says captured and the books do not."], cls="dia theory")

S(plain("Theory · 5 of 6 · the options", "Six ways to build it, and what rules each out", table(["Approach", "One effect", "Explainable", "Fails when"], [
  ("rej", ["A · A balance column, retries assumed safe", "no", "no", "the first timeout and retry; the hot row"]),
  ("rej", ["B · Two-phase commit with the processor", "would be", "would be", "always: it will not hold a prepare"]),
  ("rej", ["C · A saga with compensations, no ledger rules", "partly", "no", "a compensation that times out"]),
  ("pick", ["D · State machine, key, journal, outbox, inquiry, reconciliation", "yes", "yes", "no inquiry by our reference: the file, a day late"]),
  ("rej", ["E · An event-sourced ledger, balances in streams", "with keys", "yes", "a refund needs a current balance now"]),
  ("rej", ["F · Buy: the processor's or a gateway's records", "yes", "theirs", "a second processor; our own books"])], "bt xs mx")), [
 "C: Six approaches, each with the failure that rules it out.", P,
 "C: A, a balance column with retries assumed safe: it fails at the first timeout and retry, a double charge.", P,
 "C: B, a distributed transaction with the processor: it fails always, because the processor is not a participant and will not hold a prepared state.", P,
 "C: C, a saga without ledger rules: a compensation can itself time out, and nothing says what the books should be.", P,
 "C: D is the pick. It fails only when a processor gives no way to ask about our reference, and then the settlement file is the arbiter, a day late.", P,
 "C: E, an event-sourced ledger: how I'd build projections inside D, but alone it fails where a refund needs a current balance right now.", P,
 "C: F, buy. That is the honest first version for a small company with one processor. It fails at the second processor, or when we must keep our own books."], cls="theory")

S(plain("Theory · 5 of 6 · the pick", "D, and what it gives up", cards(
  ("grn", "What D buys", "Never guessing. A retry is harmless, an unknown has an exit, every balance is a sum, and the outside world is checked daily."),
  ("red", "What D gives up", "More states to test. A reconciliation team. “Pending” answers that every merchant integration must handle."), cols=2)), [
 P, "C: What D buys is never guessing: a retry is harmless, an unknown has an exit, every balance is a sum of facts, and the outside world is checked daily.", P,
 "C: What it gives up: more states to test, a reconciliation function with people in it, and pending answers that every merchant integration has to handle. I'd say that cost aloud, because it lands on other teams."], cls="theory")

S(plain("Theory · 6 of 6 · the failure catalogue", "What will go wrong, which becomes the challenge list", table(["Failure", "Challenge"], [
  ["A timeout, an ambiguous result, a processor down", "<b>1</b> · the crux, part one"],
  ["Concurrent retries; a retry with a changed amount", "<b>2</b>"],
  ["A crash between the commit and the event", "<b>3</b>"],
  ["The hot merchant; a million one-time accounts", "<b>4</b>"],
  ["Our books and the processor's disagree; a bad release", "<b>5</b> · the crux, part two"],
  ["Nobody notices", "<b>6</b> · observability"]], "bt sm")), [
 "C: Last, the failure catalogue, which becomes the challenge list.", P,
 "C: A timeout, the crux.", P, "C: Concurrent retries.", P, "C: A crash between commit and event.", P,
 "C: The hot merchant, and the opposite problem, a million one-time accounts.", P,
 "C: Books that disagree with the processor's, the second half of the crux, and a bug that posted wrong entries.", P,
 "C: And nobody noticing. Refunds and late chargebacks are covered on the A-P-I and flow slides and in the written design; floating-point money by integer minor units."], cls="theory")
