from dsl import *
from stack import TECH, SUMMARY, SUMMARY_SAY, STACK, say_text
import re
P = "[+]"

# ───────────────────────── 4 · API and entities ─────────────────────────
chapter(4, "API and entities", 3, "The contract first. It forces the semantics into the open.", [
 "C: The A-P-I before the boxes. It is the contract with every merchant, and it shows whether I have thought about failure. Every call carries a tag: the requirement it serves and the entity it touches."])

S(plain("API · pay (FR1)", "POST /v1/payments: a key, minor units, an honest pending",
  tr(("fr", "serves FR1"), ("api", "POST /payments"), ("ent", "writes Payment · Attempt · JournalTxn"), ("nfr", "idempotent")) +
  code('POST /v1/payments\nIdempotency-Key: k-91\n{"merchantId": "m-42",\n "amount": {"value": 1050,\n            "currency": "EUR"},\n "methodToken": "tok_7c1…",\n "capture": "auto"}\n201 {"paymentId": "p-7731", "status": "captured"}\n202 {"paymentId": "p-7731", "status": "pending"}', "http", hl=(2, 4, 8, 9))), [
 "C: Pay. The client sends an idempotency key in a header, and a body with the merchant, the amount and a token for the card.",
 "C: The amount is an integer in minor units with its currency: one thousand and fifty cents, never ten point five as a float. The card number never reaches us: a token does.",
 "C: The answer is the payment I-D and a status, and the status can honestly be pending. The same key with a different body is a four twenty-two. The same key while the first is in flight is a four-oh-nine."])

S(dia("API · the payment's states", "A state machine with an exit from “unknown”", "states", chip=chips("UNKNOWN is a state", "illegal transitions rejected")), [
 P, "C: Behind that status is a state machine, drawn one state at a time. A payment is created.", P,
 "C: It becomes auth pending when we send it.", P,
 "C: From there, authorised when the processor approves.", P,
 "C: Declined, when it declines.", P,
 "C: Or the red one: unknown, on a timeout or an ambiguous answer.", P,
 "C: Unknown has two exits. The inquiry says approved, and the payment becomes authorised.", P,
 "C: Or the processor says not found after its safe window, and it becomes declined.", P,
 "C: Authorised becomes captured.", P,
 "C: Captured becomes settled when the file matches.", P,
 "C: Captured can be partly refunded.", P,
 "C: And then refunded in full.", P,
 "C: And a settled payment can be disputed: a chargeback. Any transition not drawn here is rejected by the code. A capture on a declined payment is not a bug to handle later: it cannot happen."], cls="dia")

S(plain("API · the rest of the surface", "Every endpoint, tagged", table(["Endpoint", "Serves", "Touches", "The point"], [
  ["<code>POST …/capture · …/void</code>", "FR1 · FR2", "Payment, JournalTxn", "its own key; a new transaction, nothing edited"],
  ["<code>POST …/refunds</code>", "FR2", "Payment, JournalTxn", "limit: one conditional update on the payment row"],
  ["<code>webhook</code> to the merchant", "FR3", "Outbox", "signed, retried for days, at least once"],
  ["<code>GET /v1/payments/{id}</code>", "FR3", "Payment", "the backstop: always the database's state"],
  ["<code>Inquire(processor, ref)</code>", "FR1 · FR4", "Attempt", "our reference: payment ID, slash, attempt number"],
  ["<code>GET /v1/accounts/{id}/balance</code>", "FR5", "Balance projection", "says the entry it is current to"]], "bt xs mx")), [
 "C: The rest of the surface, each tagged.", P,
 "C: Capture and void, each with its own key, each a new transaction that references the payment. Nothing is edited.", P,
 "C: Refunds. The limit is one conditional update on the payment row: add the amount only if the total stays within what was captured.", P,
 "C: Webhooks, signed, retried with backoff for days. A merchant may see an event twice and de-duplicates by event I-D.", P,
 "C: A get on the payment: the backstop. A merchant who missed every webhook can still find the state.", P,
 "C: Inquire asks a processor about our own reference for one attempt.", P,
 "C: And a balance, from the projection, which says which entry it is current to."])

S(dia("Data · conceptual model", "Entities and relationships, in Chen notation", "erd-chen"), [
 "C: The conceptual model, one entity at a time.", P,
 "C: A payment, with its state and its merchant.", P,
 "C: It has attempts: one per call to a processor, each with our reference. An attempt only exists inside its payment.", P,
 "C: A payment posts journal transactions.", P,
 "C: A transaction contains entries, at least two, and an entry exists only inside its transaction.", P,
 "C: Each entry is on one account, which also belongs to a merchant. A balance is a derived attribute of an account: the sum of its entries.", "[+2]",
 "C: And a break, from reconciliation, may explain one transaction."], cls="dia")

S(dia("Data · physical model", "Tables, keys, and what is allowed to change", "erd-physical"), [
 "C: The physical tables, one at a time.", P,
 "C: Journal entries, keyed by merchant, account and entry, hashed into sixty-four partitions by merchant, and only ever inserted.", P,
 "C: Journal transactions carry the payment and the type, with a check at commit that debits equal credits.", P,
 "C: The payment row is the only mutable row, changed only by conditional updates.", P,
 "C: Idempotency keys, with their request hash and stored response, kept seven days.", P,
 "C: The outbox, written in the same transaction as the state.", "[+2]",
 "C: And a balance projection that can be rebuilt from the entries at any time."], cls="dia")

S(dia("Data · a worked example", "One capture, as balanced entries", "entries", chip=chips("integer minor units", "debits = credits")), [
 "C: A worked example. A capture of one thousand and fifty, with a fee of thirty.", P,
 "C: The processor receivable is debited one thousand and fifty: the processor owes us that.", P,
 "C: The merchant payable is credited one thousand and twenty: we owe the merchant that.", P,
 "C: Fee revenue is credited thirty.", P,
 "C: Debits one thousand and fifty, credits one thousand and fifty: balanced.", P,
 "C: A refund is a new transaction that mirrors these lines. Three rules about amounts, cheap to state and expensive to forget: never a float, a currency on every amount, and a conversion is its own transaction with the rate it used."], cls="dia")

# ───────────────────────── 5 · high-level design ─────────────────────────
chapter(5, "High-level design", 4, "Three versions on one picture, then every path", [
 "C: The design in three versions. Each answers the objection to the one before, and it is one picture from here to the end: later slides only show what changes on it."])

S(dia("Design · version 1", "The simplest thing that works", "base-v1", vtag="V1", chip=chips("one service", "one database", "a synchronous call")), [
 "C: Version one, drawn in the order a payment travels.", P,
 "C: The merchant.", P, "C: Calls the payments A-P-I.", P, "C: Which hands it to the payment service.", P,
 "C: The service records the payment in one database: a status, and a balance column.", P,
 "C: And charges the card at the processor, synchronously. It is the simplest thing that works. The objection comes next."], cls="dia")

S(trace("V1 · the objection", "A timeout, a retry, and two charges", [
  ("10:00:00.000", "p-7731 is sent to the processor for 1,050"),
  ("10:00:01.900", "no answer: marked <span class='bad'>failed</span>"),
  ("10:00:02.400", "the processor approves it"),
  ("10:00:05.000", "the checkout retries as a new payment p-7744: approved; <span class='bad'>two holds of 1,050</span>"),
  ("next month", "an auditor asks why this balance is 18,204,400: <span class='bad'>there is no history</span>")]), [
 "C: The objection, as a trace.", P, "C: The payment goes to the processor.", P,
 "C: At one point nine seconds, no answer, so version one marks it failed.", P, "C: Half a second later the processor approves it anyway.", P,
 "C: The checkout retries as a new payment, which is approved. The customer has two holds.", P,
 "C: And next month an auditor asks why a balance is what it is, and the answer is a number that was updated in place."])

S(dia("Design · version 2", "One effect per intent, and books that prove themselves", "base-v2", vtag="V2",
      chip=chips("key inserted first", "attempt committed before the call", "UNKNOWN", "journal")), [
 P, "C: Version two. Everything from version one stays where it was.", P,
 "C: New: a processor adapter. The A-P-I now inserts the idempotency key first. The payment service commits the payment as auth pending, with an attempt and our own reference, before it calls out, and the adapter calls the processor with that reference. The database holds a journal: balanced, immutable entries, with balances as a projection. A timeout now moves the payment to unknown instead of failed, and a retry with the same key gets the same answer."], cls="dia")

S(plain("V2 · the objection", "Correct inside, and still three holes", cards(
  ("red", "Telling others", "Merchants hear about a change by a second write after the commit. A crash in between, and they never hear."),
  ("red", "Unknowns pile up", "Nothing ends an unknown. Ten a second at peak, forever pending."),
  ("red", "The outside disagrees", "Our books can still differ from the processor's, and nobody would know."), cols=3)), [
 "C: The objection to version two. Inside the database it is correct. But:", P,
 "C: Merchants hear about a change through a second write after the commit, so a crash in between means they never hear.", P,
 "C: Nothing ends an unknown: ten a second at peak, pending forever.", P,
 "C: And our books can still disagree with the processor's, and nothing would notice."])

S(dia("Design · version 3", "Close every loop", "base-v3", vtag="V3", chip=chips("outbox → log → webhooks", "inquiry job", "reconciliation", "finance ops")), [
 P, "C: Version three closes those loops. Version two, carried as it was.", P,
 "C: New: an outbox relay feeds an event log, and a webhook sender posts signed events to the merchant.", P,
 "C: An inquiry job reads unknown payments, asks the adapter by reference, and resolves them in the database.", P,
 "C: And reconciliation takes the processor's settlement file, compares it with expectations from the ledger,", P,
 "C: and hands the breaks to finance operations. This is the baseline. It stays, and every picture from here on is a view of it."], cls="dia")

S(plain("Design · the containers", "Each container, what it owns, and its number", table(["Container", "Owns", "Its number"], [
  ["Payments API", "The key, the request hash, the 2-second deadline; never the state", "10,000/s peak, stateless"],
  ["Payment service", "The state machine and the postings: legal edges only", "one commit per payment"],
  ["Processor adapter", "The reference on every call and the processor's error codes", "~1.5 s p99 at the processor"],
  ["Ledger database", "Payments, journal, outbox, keys; one partition per merchant slice", "64 partitions, ~10 primaries"],
  ["Outbox relay + log, webhooks", "Committed rows in commit order; signed, retried webhooks", "40,000 rows/s at peak"],
  ["Inquiry job", "Ends every UNKNOWN by our reference, with backoff", "10 a second at peak"],
  ["Reconciliation", "Expectations, the file match, owned breaks", "2.9 × 10⁸ lines, 5 min"]], "bt xs mx")), [
 "C: The containers, one at a time, with what each owns and its number.", P,
 "C: The payments A-P-I owns the key, the request hash and the two-second deadline. It never owns the state, so it stays stateless at ten thousand a second.", P,
 "C: The payment service owns the state machine and the postings. Only legal edges, one commit per payment.", P,
 "C: The processor adapter puts our reference on every call and maps the processor's codes into three classes. About one and a half seconds at the processor, at the ninety-ninth percentile.", P,
 "C: The ledger database holds payments, journal, outbox and keys: sixty-four partitions on about ten primaries, one merchant slice per partition.", P,
 "C: The outbox relay and log publish committed rows in commit order, and the webhook sender signs and retries them. At the peak that is forty thousand rows a second.", P,
 "C: The inquiry job ends every unknown by our reference, with backoff: about ten a second at the peak.", P,
 "C: And reconciliation: expectations, the file match and owned breaks. Two hundred and ninety million lines, about five minutes."])

S(plain("Design · the ledger database", "The partition key: the owner, not the account", table(["Key", "Co-locates", "A capture (3 accounts)", "A balance read", "A hot merchant"], [
  ["Account", "one account's entries", "cross-partition, every time", "one partition", "one hot row"],
  ["Payment", "one payment's entries", "one partition", "scatter over all", "spread; balance is a sum of all"],
  ("pick", ["<b>Merchant</b>", "everything one owner has", "<b>one partition</b>", "<b>one partition</b>", "one partition: sub-accounts, challenge 4"]),
  ["Time", "the same period", "one partition, all writers", "scatter", "all writers on the newest"]], "bt xs mx") +
  line("Shared accounts, such as fee revenue, exist once per partition and are summed for the company view.", "a")), [
 "C: One decision on the database deserves its own slide, because it is the one an interviewer asks about: why this partition key?", P,
 "C: By account: all of one account's entries are together, so a balance read is one partition. But a capture touches three accounts, the receivable, the payable and the fee, so it spans partitions every time, and I would need a distributed transaction for every payment.", P,
 "C: By payment: a capture is local, but a balance is a scatter across every partition.", P,
 "C: By merchant: a capture is one partition, a balance read is one partition, and the cost is that a hot merchant is a hot partition. That is the cost I can handle, in challenge four.", P,
 "C: By time: all writers hit the newest partition. No.", P,
 "C: And shared accounts, fee revenue or the processor receivable, would be hot and cross-partition, so each partition has its own, and the company view sums them."])

S(dia("Flow · FR1 pay · POST /payments · writes Payment, Attempt, JournalTxn, Outbox", "A payment, end to end", "flow-pay"), [
 P, "C: The pay path, numbered.", P,
 "C: One: the merchant posts the payment with its key.", P,
 "C: Two: the A-P-I inserts the key and hands over to the service.", P,
 "C: Three: one transaction commits the payment as auth pending, with its attempt.", P,
 "C: Four: the adapter is asked to authorise.", P,
 "C: Five: it calls the processor with our reference. The answer comes back along the same path, and a second transaction commits the state, the entries, the outbox row and the key marked done."], cls="dia")

S(dia("Sequence · FR1 pay", "One payment, as a sequence", "seq-pay"), [
 "C: The same payment as a sequence.", P, "C: The merchant posts with key k-ninety-one.", P,
 "C: One transaction: the key as processing, the payment as auth pending, the attempt with its reference.", P,
 "C: Authorise, through the adapter.", P, "C: With reference p-seventy-seven thirty-one, slash one.", P,
 "C: Approved in three hundred and forty milliseconds.", P,
 "C: The second transaction, highlighted: captured, entries, outbox, key done.", P, "C: Then two-oh-one, captured."], cls="dia")

S(dia("Sequence · FR2 adjust", "A refund, with the limit in one statement", "seq-refund"), [
 "C: Requirement two, a refund, as a sequence.", P, "C: A refund of twenty-five hundred on a payment that has already been refunded part-way.", P,
 "C: A second one, two milliseconds later, with another key.", P,
 "C: The conditional update: add the amount only if the total stays within what was captured. One row.", P,
 "C: The same statement for the second: zero rows.", P, "C: So the second gets four twenty-two.", P,
 "C: The winner goes to the processor with its own reference.", "[+2]",
 "C: And a new journal transaction is posted, dated now. Three months later a chargeback is posted the same way, dated now, and the closed month is untouched."], cls="dia")

S(dia("Sequence · FR5 explain", "Any balance, from the journal", "seq-explain"), [
 "C: Requirement five, explain.", P, "C: An auditor asks for a merchant's payable balance as of the end of October.", P,
 "C: The service sums the entries on that account, up to that date. One partition, because the key is the merchant.", P,
 "C: The answer says which entry it is current to.", "[+2]",
 "C: And for every unit of it, the entries joined to their transactions and payments: every number explained by the records that produced it."], cls="dia")

# ───────────────────────── 5.1 · components and technologies ─────────────────────────
subchapter("5.1", "Components and technologies", ["C: Now one level down. The same picture with what each box runs on, three containers opened up, and for each choice, what I rejected and why."])

S(dia("Architecture · C4 containers · technologies", "The same containers, now with what they run on", "c4-containers-tech"), [
 "C: The same container view; only the type lines changed. The six boxes in scope, one at a time.", P,
 P, "C: The payments A-P-I: Go, gRPC inside, REST outside.", P,
 "C: The payment service: Go, with the state machine.", P,
 "C: The processor adapter: Go, one per processor.", P,
 "C: The ledger database: PostgreSQL, partitioned by merchant.", P,
 "C: The outbox relay: Debezium on Kafka Connect, publishing to Kafka.", P,
 "C: And reconciliation: a Spark batch, with expectations in PostgreSQL."], cls="dia")

S(dia("Architecture · C4 components · payment service", "Inside the payment service, in the order a payment meets it", "c4-comp-service"), [
 "C: Inside the payment service, in the order a payment meets it.", P,
 "C: The A-P-I hands over.", P, "C: The idempotency guard: a unique insert, with a request hash.", P,
 "C: The state machine: conditional updates, legal edges only.", P,
 "C: The attempt writer: our reference, committed before the call.", P,
 "C: The processor port: a deadline of one point nine seconds, and three error classes.", P,
 "C: Below, the ledger database: the key row, the state, entries and outbox, and the attempt row first.", P,
 "C: The adapter.", P, "C: The processor.", P,
 "C: And the inquiry job, which asks the adapter by reference and resolves through the state machine. Challenges one and two happen in this picture."], cls="dia")

S(dia("Architecture · C4 components · ledger database", "Inside one partition of the ledger database", "c4-comp-db"), [
 "C: Inside one partition of the ledger database.", P,
 "C: The payment service issues one transaction.", P, "C: One transaction: the state, the entries and the outbox row, together.", P,
 "C: It writes the payment row, the only mutable one.", P,
 "C: The journal entries, insert only, with sixteen sub-accounts for a hot merchant.", P,
 "C: And the outbox table, in the same transaction.", P,
 "C: A balance projection is derived from the journal, seconds behind.", P, "C: And a payout writer, one per merchant, checks the sum.", P,
 "C: The outbox row reaches the write-ahead log, in commit order.", P, "C: A replication slot holds the log for the reader.", P,
 "C: Debezium reads the slot.", P, "C: And publishes to Kafka, by merchant. Challenges three and four happen here."], cls="dia")

S(dia("Architecture · C4 components · reconciliation", "Inside reconciliation, from the file to an owned break", "c4-comp-rec"), [
 "C: Inside reconciliation.", P,
 "C: The processor's file.", P, "C: Stored unchanged, before anything reads it.", P,
 "C: The expectation builder asks the ledger what it expects to settle, by reference and net of fees.", P,
 "C: The matcher joins file to expectations by reference, and checks amount, fee and state.", P,
 "C: Matches become settled, with settlement entries in the ledger.", P,
 "C: Everything else goes to the break writer: a type, an owner and an age.", P,
 "C: Into a queue that finance operations works.", P,
 "C: Finance approves a correction.", P, "C: The corrector posts reversing entries, tagged with the incident. Challenge five happens in this picture."], cls="dia")

def tsay(_id):
    """Compact cut: the slide carries the reasons; the narration reads how, why, and the first clause of each rejection."""
    s = STACK[_id]; first = lambda t: re.split(r"(?<=[.:;])\s", say_text(t))[0].rstrip(".:;") + "."
    out = [P, "C: " + say_text(s["how"]), P, "C: Why: " + first(s["why"])]
    for i, (n, w) in enumerate(s["rejected"]):
        out += [P, f"C: {'Rejected: ' if i == 0 else ''}{say_text(n)}. " + first(w)]
    return out
for _id in ("payments-db", "outbox-log"):
    S(tech(**TECH(_id)), tsay(_id))

S(plain("Technology · language and runtime", "Why Go: the services wait for a bank, not for the CPU", table(["Runtime", "Overhead per request", "Memory per instance", "In this design"], [
  ("pick", ["<b>Go</b>", "0.1 – 0.5 ms", "30 – 80 MB", "Flat tail, small replicas, deadlines in every call"]),
  ["Java 21+, virtual threads (Spring Boot, Quarkus)", "0.2 – 1 ms warm", "200 – 500 MB; native 50 – 100", "An equal choice for a Java team"],
  ["Spring WebFlux (reactive)", "like virtual threads", "like virtual threads", "Harder code for what virtual threads now give"],
  ["Python, async", "1 – 3 ms", "60 – 150 MB", "One core per process; a fatter tail"],
  ["Rust", "0.05 – 0.3 ms", "10 – 40 MB", "Fastest and leanest; not where our time goes"]], "bt xs mx") +
  grade("Illustrative orders of magnitude from public benchmarks that disagree with each other. Measure on your own load.")), [
 "C: Why Go everywhere? Because the language is not where the two seconds go.", P,
 "C: Go. Our own code costs a fraction of a millisecond a request, a replica is thirty to eighty megabytes, and a context deadline cancels a whole call chain. That is a flat tail and cheap replicas. The processor takes a second; the commit, a few milliseconds.", P,
 "C: Java twenty-one and later, with virtual threads, in Spring Boot or Quarkus, is within a small factor of Go and an equal choice for a Java team. It costs more memory per instance, unless compiled native.", P,
 "C: Spring WebFlux, the reactive stack. It was the answer to blocking threads. Virtual threads now give the same concurrency with plain blocking code, and a JDBC driver blocks anyway. I would not choose it for a payments service.", P,
 "C: Python with async: a core per process under the interpreter lock, several times less throughput per core, and a fatter tail.", P,
 "C: Rust is the fastest and leanest. It pays where microseconds matter, a matching engine, not in a service whose time is a bank call and a commit. The cost is hiring and build speed.", P,
 "N: The numbers are illustrative and the public benchmarks disagree. The signal is saying where the time goes, and what would change the answer."])

S(plain("Technology · gateway or processor", "Why most companies use a gateway, and when we would not", table(["", "A gateway (Stripe, Adyen)", "Direct to a processor or acquirer"], [
  ["<b>Time to first payment</b>", "days: one API", "months: underwriting, certification"],
  ["<b>Card-data scope</b>", "tokens and hosted fields keep it out of ours", "the highest compliance level, audited yearly"],
  ["<b>Price, illustrative</b>", "about 2.9 % + 30 ¢ blended at list", "interchange plus a margin, about 1.8 – 2.4 %"],
  ["<b>You also get</b>", "methods, fraud tools, disputes, payouts", "only what you build"],
  ["<b>Control</b>", "their routing, their outage is yours", "your routing, several processors"],
  ["<b>Still ours either way</b>", "the ledger, keys, UNKNOWN, reconciliation", "the same"]], "bt xs mx") +
  line("Break-even, illustrative: a 0.7 % premium against a team and audits of $80,000 a month is about $10 million of card volume a month.", "a")), [
 "C: The question every interviewer eventually asks: why not just use a gateway? Often you should.", P,
 "C: A gateway gives one A-P-I in days. Direct means underwriting and certification: months.", P,
 "C: Card data. Tokens and hosted fields keep it out of our scope. Direct puts us in the highest compliance level.", P,
 "C: Price, illustrative: a gateway is about two point nine percent plus thirty cents at list. A direct processor is interchange plus a margin, about one point eight to two point four percent.", P,
 "C: A gateway also brings payment methods, fraud tools, disputes and payouts. Direct gives only what we build.", P,
 "C: Control: with a gateway their routing and their outage are ours. Direct, we route across several processors.", P,
 "C: And what is ours either way: the ledger, the keys, the unknown state, and reconciliation. A gateway's balance is not our books, and a timeout to a gateway is still an unknown.", P,
 "C: Break-even: a premium of seven tenths of a percent against a team and audits of about eighty thousand dollars a month is about ten million dollars of card volume a month. We are far past it, so direct, behind one interface, and a gateway is one more adapter."])

S(tech(**TECH("adapter")), tsay("adapter"))

_ss = SUMMARY_SAY()
S(plain("Technology · the stack on one slide", "The stack, against its rivals",
        table(["Container", "Choice", "Rejected", "The deciding reason"], SUMMARY(), "bt xs mx") +
        grade("Naming a product is not the signal. Naming the property that rules out its rival is.")), _ss[:-1] + [P, _ss[-1]])

# ───────────────────────── 5.2 · when you don't need all this ─────────────────────────
subchapter("5.2", "When you don't need all this", ["C: Before I break it: a much smaller design is correct at a smaller scale, and I should say where the line is. This is the one I would build for a small business."], sub="ALTERNATE")

S(dia("Alternate path · ALTERNATE", "A gateway, one PostgreSQL primary, a polled outbox", "alt",
      cap="One adapter (the gateway), one primary, a polled outbox; no Kafka, no Debezium, no partitions"), [
 P, "C: The alternate path. The spine stays: the key, the state machine, the journal, reconciliation.", P,
 "C: What changes is marked. The adapter is the gateway.", P, "C: The database is one primary with a synchronous standby.", P, "C: And the outbox relay is a poll every two hundred milliseconds, not change capture. No Kafka, no Debezium, no partitions.",
 "C: What it gives up, precisely: one writer, about twelve hundred commits a second. No replayable log. The gateway's fee premium and its outages, which are ours. And a failover can lose what the standby had not yet received, if it is asynchronous."], cls="dia")

key("ALTERNATE · the line", "Below about <em>300 payments a second</em> and <em>$10 million a month</em>, I'd ship the one-primary, gateway version, and say when I'd switch.", [
 "C: Where is the line? One primary commits about twelve hundred of our transactions a second. Our peak, from the scale line, is ten thousand: eight times past it. And at ten million dollars a month the gateway's premium pays for a payments team. We are nine billion payments a month past that.",
 "V: Below about three hundred payments a second, with room to spare, and ten million dollars a month, I'd ship the one-primary gateway version, and I'd say out loud when I'd switch.", "[pause: 0.8]"])
