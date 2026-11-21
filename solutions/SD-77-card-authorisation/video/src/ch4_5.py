from dsl import *

# ───────────────────────── 4 · API and entities ─────────────────────────
chapter(4, "API and entities", 3, "Each message tagged with the requirement it serves and the data it touches", [
 "C: Four message families from the network, one file, and one internal call. Each tagged with the requirement it serves and the data it reads or writes."])

S(plain("API · the messages", "What crosses the gateway", table(["Message", "Serves", "Touches", "Note"], [
  ["<code>Authorise {networkRef, token, amount, mcc, entryMode, …}</code> → <code>approve | decline, reason</code>", "FR1", "reads Card, Account, Counters; writes Hold, Message", "inside the budget"],
  ["<code>IncrementalAuth {networkRef, originalRef, delta}</code>", "FR1", "writes Hold", "the same hold, larger"],
  ["<code>Reversal {networkRef, originalRef, amount}</code> → ack", "FR2", "writes Hold, Message", "may arrive before its original"],
  ["<code>Advice {networkRef, decidedBy, decision, amount}</code> → ack", "FR2", "writes Hold, Message", "always acknowledged, always recorded"],
  ["<code>ClearingFile {fileId, records[]}</code>", "FR3", "reads Hold; writes Posting", "each record has its own ID"],
  ["internal <code>POST /rulesets</code> · <code>/promote {mode, slice}</code>", "FR4", "writes RuleSet", "reviewed by a second analyst"]], "bt sm")), [
 "C: The network speaks a message standard called I-S-O eighty-five eighty-three, with numbered fields. Our gateway maps it to our own messages, so nothing behind the gateway knows the wire format.",
 "C: Authorise carries the network reference, the card token, the amount, the merchant category code and the entry mode, and gets back approve or decline with a reason. The incremental raises an existing hold. A reversal releases one, and may arrive before its original. An advice tells us what the network decided for us, and is always acknowledged.",
 "C: The clearing file comes once a day, and every record has its own I-D. And internally, analysts post rule sets and promote them through modes."])

S(plain("API · two fields that matter", "Merchant category and entry mode", '<div class="cards c2">'
  '<div class="cd"><h3>Merchant category code</h3><p>Restaurant, fuel, hotel, electronics. It sets the hold\'s lifetime, and it is the strongest single fraud feature.</p></div>'
  '<div class="cd amb"><h3>Entry mode</h3><p>Card present (chip, contactless) or not (online, phone). Most fraud is card-not-present, so almost every rule branches on it.</p></div></div>' +
  line("The decline reason matters too: “suspected fraud” sends the customer a text, and their “it was me” reply is the fastest false-positive signal we have.", "a")), [
 "C: Two fields matter more than the rest. The merchant category code says what kind of merchant it is: restaurant, fuel, hotel, electronics. It sets how long a hold lives, and it is the strongest single fraud feature. The entry mode says whether the card was present. Most fraud is card-not-present, so almost every rule branches on it.",
 "C: And the decline reason matters. Suspected fraud sends the customer a text, and their reply, it was me, is the fastest false-positive signal there is. That comes back in challenge six."])

S(plain("API · one authorisation, both ways", "What the decision service sees and answers", table(["Field", "Request", "Answer"], [
  ["networkRef", "R-4410", "the same: it keys everything"],
  ["token → account", "T-91… → A-12", "—"],
  ["amount · currency", "6000 · USD (minor units)", "—"],
  ["mcc · entryMode", "5812 restaurant · contactless", "—"],
  ["decision", "—", "approve · authCode 83F2Q1"],
  ["reason · versions", "—", "00 · rule set 212 · model 41 (logged, not sent)"]], "bt sm") +
  line("Amounts travel as integers in minor units. The versions are not sent to the network; they go to the decision record.", "a")), [
 "C: One authorisation, both ways. The network reference, R-forty-four-ten, keys everything that follows. The token resolves to account A-twelve. The amount travels as an integer in minor units, six thousand cents, never a floating-point number. The merchant category says restaurant, and the entry mode says contactless.",
 "C: The answer is approve with an authorisation code. The rule-set and model versions are not sent to the network. They go into the decision record, which is how we reproduce this decision in seven years."])

S(dia("Entities · conceptual", "Accounts, cards, holds, messages, decisions, clearing", "erd-chen"), [
 "C: The conceptual model. An account has many cards. An account reserves many holds. A hold is created by a message and changed by later messages with the same reference: the incremental, the reversal.",
 "C: Each message is recorded as a decision, a weak entity carrying the features, the rule-set version and the model version. And a hold is settled by clearing records: usually one, several for a split shipment, none for a hold that expires."])

S(dia("Entities · physical", "One partition holds an account, its holds and its messages", "erd-physical"), [
 "C: The physical tables in the authorisation store. The account row: posted balance, holds total, a version, and a state that includes over-limit. Holds keyed by account and hold, with the network reference unique. And the message table keyed by the network reference, for idempotency.",
 "C: The point is the partition key. Account, holds and messages all live in the account's partition, so one local transaction can reserve a hold and record its message together. Cards map tokens to accounts. Clearing records have their own I-Ds. And rule sets are versioned rows every decision service reads."], cls="dia")

S(plain("Entities · stores, and can we lose them?", "Decide this before choosing products", table(["Store", "Lose it?", "Because"], [
  ["Authorisation store", "<b>no</b>", "holds are money; messages are idempotency"],
  ["Feature store (counters)", "yes, ten minutes of it", "rebuilt from the event log; a row of the fail table covers the gap"],
  ["Event log", "no, until consumed", "it carries every decision to the archive and alerts"],
  ["Decision archive", "<b>no</b>", "seven-year reproducibility"],
  ["Rule sets", "no", "every decision names one"],
  ["Core ledger", "<b>no</b>", "the bank's books"]], "bt sm")), [
 "C: Before choosing products, I decide which stores we may lose. The authorisation store, never: holds are money, and messages are how we stay idempotent. The counters, yes: ten minutes of buckets, rebuilt from the event log, and the fail table covers the gap. The event log, not until it is consumed. The archive and the ledger, never."])

# ───────────────────────── 5 · high-level design ─────────────────────────
chapter(5, "High-level design", 4, "Three versions, each answering the objection to the one before", [
 "C: The design in three versions, drawn on the same baseline. Each answers the objection to the one before."])

S(dia("Design · V1", "The simplest thing that works", "base-v1", vtag="V1", chip=chips("one service", "holds in the ledger", "rules in code")), [
 "C: Version one. A gateway and one decision service. To authorise, it reads the balance from the core ledger and inserts a hold row there, in one transaction. Rules are if-statements in the code. A nightly job reads the clearing file, posts and releases.",
 "C: For a small issuer at a hundred a second, it might be enough. The objection: the core ledger's tail latency and its nightly batch window now sit on the authorisation path. Every rule change is a deploy. There is no fraud score. And nothing answers a retried or out-of-order message."])

S(dia("Design · V2", "Split the decision from the ledger", "base-v2", vtag="V2", chip=chips("answers: the ledger off the hot path", "rules without a deploy")), [
 "C: Version two answers that. The decision service becomes stateless, and its state moves to an authorisation store: balances, holds and messages, partitioned by account, with one atomic reserve. Rules move into the decision service's own process, pushed as versioned data by a rule service that analysts use. A model scorer answers under a sixty millisecond cut-off.",
 "C: Every decision goes to an outbox in the same write as the hold, and on to an event log. A clearing matcher posts to the core ledger and releases holds, and the ledger's other balance changes, a salary in, a direct debit out, flow back to the authorisation store. The new boxes are outlined in blue.",
 "C: The objection it leaves: where do features come from? What do we decide when something is late? What about stand-in advices? And how do two copies of the balance stay in agreement?"])

S(dia("Design · V3", "Protect the deadline; close the loops", "base-v3", vtag="V3", chip=chips("feature store", "stream aggregator", "fail table", "alerts and archive")), [
 "C: Version three. A feature store with burst counters the decision reads and increments inline, and pattern features a stream aggregator computes from the event log. The fail-policy table and its exposure counters live in the decision service. Advices take the same path as authorisations.",
 "C: The rule service gains backtest and shadow. Alerts, cases and the decision archive consume the event log. And a daily job reconciles the authorisation store against the ledger. The objection it leaves is the details. Those are the challenges."])

S(plain("Design · the three versions", "Each answers the one before", table(["Version", "Adds", "Answers", "Leaves"], [
  ["V1", "One service; holds in the ledger; rules in code; a nightly clearing job", "—", "the ledger on the hot path; deploys for rules; no score; no idempotency"],
  ["V2", "Auth store and atomic reserve; rules as data; model with a cut-off; outbox and log; clearing matcher", "the ledger off the hot path; rules without a deploy", "features; lateness; advices; two balances"],
  ["V3", "Feature store and aggregator; fail table; advices; rule lifecycle; consumers; reconciliation", "every step budgeted, with a written fallback; nothing we did not decide is lost", "the details: challenges 1 to 8"]], "bt sm")), [
 "C: The three versions in one table. Version one: one service on the ledger. Version two: split the decision from the ledger, and make rules data. Version three: protect the deadline and close every loop. Each answers the objection to the one before."])

S(dia("Flow · FR1 authorise", "Eight numbered steps", "flow-fr1"), [
 "C: Flow one, authorise. One: the network sends the request through the processor. Two: the gateway maps it and passes it to a decision service. Three: the decision service increments this card's counter for the current minute and reads the nine before it, in one round trip.",
 "C: Four: it sends the request to the model with a sixty millisecond cut-off, while the rules run in its own process. Five: to approve, it reserves the hold in the account's partition: check available, insert the hold, record the message, in one conditional write.",
 "C: Six: the decision, with its inputs and versions, goes to the outbox in that same write, and on to the event log. Seven and eight: the answer goes back through the gateway to the network."], cls="dia")

S(dia("Sequence · authorise", "Ninety-one milliseconds, with the model on time", "seq-authorise"), [
 "C: As a sequence. Authorise R-forty-four-ten, sixty dollars, at a restaurant. Count this swipe and read ten minutes: one millisecond. The model is asked with a cut-off, while rules run in process. The model answers in thirty-eight milliseconds: low risk. Reserve: hold sixty if available, record the message. Okay, available four hundred and forty. The decision goes to the outbox, and the network gets approve, in ninety-one milliseconds."], cls="dia")

S(dia("Flow · FR2 reverse and advise", "Five numbered steps, in any order", "flow-fr2"), [
 "C: Flow two, reversals and advices. One: the message arrives from the network. Two: the gateway passes it on. Three: the decision service applies it by network reference in the authorisation store. A reversal releases all or part of a hold, or waits as a tombstone if its original has not arrived. An advice is recorded as a hold, even if it takes the account below zero.",
 "C: Four: the event goes to the log. Five: the acknowledgement goes back. Nothing here is a decision. It is recording."], cls="dia")

S(dia("Flow · FR3 clear", "Three numbered steps, and available never jumps", "flow-fr3"), [
 "C: Flow three, clearing. Before step one, the matcher loads the day's file and skips record I-Ds it has already applied. One: in the authorisation store, in one write, it moves the amount from the hold to the posted balance. Posted goes down by seventy-two, the seventy-two dollar hold is released, and available does not move at all.",
 "C: Two: it posts the same amount to the core ledger, keyed by the clearing record's I-D. Three: the ledger's other balance changes flow back, and clearing postings already applied are recognised by record I-D and skipped.",
 "C: Why this order? If we released the hold first and waited for the ledger to lower the balance, available would jump up for a moment, and a purchase in that moment could spend money that is already gone."], cls="dia")

S(dia("Sequence · clearing", "Reference first, then fuzzy, then post anyway", "seq-clearing"), [
 "C: As a sequence. File F-eleven-twenty-one, ten million records. Skip record I-Ds already seen. Find the hold for R-forty-four-ten: seventy-two dollars, after the tip. One write: posted down seventy-two, hold released, available unchanged. Then post seventy-two in the ledger. A record with no reference falls back to card, merchant, amount within twenty percent, and seven days. And a record with no match at all still posts, and goes to a review queue."], cls="dia")

S(dia("Flow · FR4 change rules", "Four numbered steps, no deploy", "flow-fr4"), [
 "C: Flow four, changing rules. One: an analyst writes rule version fifteen in the rule service, which backtests it on the decision archive. Two: the rule service pushes a new rule-set version to every decision service, in shadow. Three: every decision records the rule-set version, and what the shadow rule would have done.",
 "C: Four: the event log feeds the alarms on decline rate by merchant type. Then a slice, then enforcement. And rollback is re-pointing to the previous version."], cls="dia")

S(dia("Architecture · C4 context", "Who is in the chain, and who uses the system", "c4-context"), [
 "C: The C-four context view. The cardholder pays a merchant, whose acquirer sends the purchase through the card network and the processor to us. We send the cardholder alerts. Fraud operations write rules and work cases. And we send postings to the core banking ledger. Nothing else sits on the authorisation path."], cls="dia")

S(dia("Architecture · C4 containers", "The authorisation path is three boxes in a row", "c4-containers"), [
 "C: The container view. The network and processor on the left. The gateway, the decision service and the authorisation store in a row: that is the whole authorisation path. Above it, what the decision reads: the model scorer, the feature store, the rule service. Below it, what happens after the answer: the clearing matcher, the event log, alerts and cases. That layout is the thesis, drawn."], cls="dia")

S(plain("Design · technology, against the alternatives", "Mechanism first, then a product class", table(["Need", "Choice", "Rejected", "Because"], [
  ["Authorisation store", "in-memory-backed store, partitioned by account, durable replicated log", "holds in the core ledger · a cache over the ledger", "the ledger's tail on our path · a cache cannot reserve"],
  ["Rules", "in process, as versioned data", "rules as code · a remote rules engine", "a deploy per change · a hop and a dependency"],
  ["Model", "separate scorer behind a 60 ms cut-off", "wait for it", "its tail becomes ours"],
  ["Counters", "in-memory store, one key per card per minute", "counters from the stream", "seconds behind a burst"],
  ["Events", "outbox in the hold's transaction, then a partitioned log", "publish after the write", "a crash in between loses the event"]], "bt sm mx")), [
 "C: Technology, mechanism first. The authorisation store is an in-memory-backed store partitioned by account, with a durable replicated log. Not the core ledger, whose tail would be ours, and not a cache over it, because a cache cannot reserve: two readers of one cached balance both approve.",
 "C: Rules run in process, as data, rather than code or a remote engine. The model sits behind a cut-off. Counters are one key per card per minute in memory, not from the stream. And events leave through an outbox in the same transaction as the hold, because publishing after the write loses the event on a crash."])
