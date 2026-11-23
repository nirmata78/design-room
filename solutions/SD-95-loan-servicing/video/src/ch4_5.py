from dsl import *

# ───────────────────────── 4 · API and entities ─────────────────────────
chapter(4, "API and entities", 3, "The contract first. It forces the semantics into the open.", [
 "C: The A-P-I and the data model before the boxes. Every call carries a tag: the requirement it serves and the entity it reads or writes."])

def wire(l, r): return f'<div class="cols2"><pre class="wire">{l}</pre><pre class="wire">{r}</pre></div>'

S(plain("API · schedule", "Event LoanBooked", tr(("fr", "serves FR1"), ("api", "event LoanBooked"), ("ent", "writes Loan · ScheduleVersion · Instalment · LedgerTxn"), ("nfr", "idempotent by loanId")) +
  wire('<span class="cm">// from origination</span>\nLoanBooked {\n  loanId: "ln-5531",\n  principalCents: 120000,\n  termsVersion: "bnpl-8m-v3",\n  firstDue: "2026-12-01",\n  rail: "bank_debit",\n  mandateId: "md-204" }',
       '<span class="cm">// what it creates</span>\nschedule v1: 8 × 15000 cents\ndue dates: business days only\nledger txn: loan booked\n\n<span class="cm">// the same event twice\n// → the same loan, no new rows</span>')), [
 "C: Schedule. Origination emits loan booked: the loan I-D, the principal in cents, the terms version, the first due date, and the rail with the customer's debit mandate. Twelve hundred dollars, eight instalments of a hundred and fifty.",
 "C: It creates the first schedule version, with due dates moved to business days, because a bank debit can't take effect on a weekend or a bank holiday. And the booking transaction in the ledger. The event is idempotent by loan I-D: delivered twice, it creates nothing new."])

S(plain("API · pay, refund, payoff", "Three calls that change a live loan", tr(("fr", "serves FR2 · FR3"), ("api", "payments · refunds · payoff-quote"), ("ent", "writes Intent · LedgerTxn · ScheduleVersion"), ("nfr", "idempotent")) +
  wire('POST /loans/ln-5531/payments\nIdempotency-Key: k-31\n{ amountCents: 15000,\n  kind: "extra" }\n\nPOST /loans/ln-9100/refunds\n{ merchantRefundId: "mr-77",\n  amountCents: 30000 }',
       'GET /loans/ln-5531/payoff-quote\n-> { quoteId: "q-31",\n     amountCents: 75000,\n     inFlight: [ 15000 debit ],\n     validUntil: "2026-12-05" }\n\n<span class="cm">// paying it: key = quoteId</span>')), [
 "C: Three calls change a live loan. A payment from the customer, with an idempotency key. A refund from the merchant, where the merchant's own refund I-D is the key, so a merchant retry can't refund twice.",
 "C: And the payoff quote, which returns a quote I-D, an amount, a validity date, and, importantly, a list of payments still in flight. Challenge five is about why that list is there."])

S(dia("API · the collection's states", "Unknown and returned are states, not exceptions", "states", chip=chips("UNKNOWN", "RETURNED", "SETTLED is not final")), [
 "C: Behind every collection is this state machine. Scheduled, submitted, pending, settled. From submitted, a timeout goes to unknown, and from unknown we query by the same key, never resend. From pending, a decline. And the dashed red arrow: settled to returned, up to sixty days later for a bank debit.",
 "C: From returned, an insufficient-funds return can become retry due, at most twice more, by the network's rules. Any transition not drawn here is rejected by the code."], cls="dia")

S(plain("API · rails", "What crosses to the outside", tr(("fr", "serves FR2 · FR4 · FR5"), ("api", "Charge · Query · files"), ("ent", "Attempt · ReturnRecord · SettlementLine")) +
  wire('<span class="cm">// card: one call per attempt</span>\nCharge(token, 15000,\n  key="coll:ln-5531:2:1")\nQuery(key="coll:ln-5531:2:1")\n -> approved | declined\n  | not_found',
       '<span class="cm">// bank: files, stored raw first</span>\nSubmitDebitFile(batch-1201)\n -> acknowledgement\nImportReturns(file)\nImportSettlement(file)\nImportStatement(file)')), [
 "C: What crosses to the outside. For cards, one call per attempt, carrying our key: loan, instalment, attempt. And a query by that same key. For the bank, files: we submit a debit file and wait for its acknowledgement, and we import returns, settlement reports and statements. Every file is stored unchanged before anything reads it, so a bug in parsing can be replayed."])

S(dia("Data · conceptual model", "Entities and relationships, in Chen notation", "erd-chen"), [
 "C: The conceptual model. A loan has schedule versions; a refund or a payoff creates a new one. A schedule version contains instalments. An instalment is collected by payment intents, at most one open at a time. A loan posts ledger transactions, each containing lines. And an intent posts the transactions for its result.",
 "C: The double borders are weak entities: a schedule version only exists inside its loan, and a line only inside its transaction."], cls="dia")

S(dia("Data · physical model", "Tables, keys, and what may change", "erd-physical"), [
 "C: The physical model. Ledger lines, partitioned by month, insert only. Ledger transactions with a unique idempotency key and the policy version they used. The account balance row, with a version, updated in the same commit. Due items indexed by date, shard and status, which is the work queue. Payment intents with a partial unique index: one open intent per instalment. And the outbox."], cls="dia")

S(dia("Data · a worked example", "One loan booked, one instalment collected", "entries", chip=chips("integer cents", "each transaction sums to zero")), [
 "C: A worked example. Booking a twelve-hundred dollar loan: we are owed twelve hundred of principal, we owe the merchant eleven sixty-four, and we earned thirty-six of discount fee. An instalment collected by bank debit first moves a hundred and fifty into cash clearing, while it is pending. When it settles, clearing moves to cash at the bank.",
 "C: A return is a new transaction reversing those last lines. Nothing here is ever edited."], cls="dia")

S(plain("Data · posting", "Lines and the balance in one transaction",
  '<pre class="code" data-lang="sql"><span class="kw">BEGIN</span>;\n<span class="kw">INSERT INTO</span> ledger_txn (id, idem_key, kind, policy_ver)\n<span class="kw">VALUES</span> (<span class="st">\'tx-9\'</span>, <span class="st">\'coll:ln-5531:2:1\'</span>, <span class="st">\'COLLECTION\'</span>, <span class="st">\'v3\'</span>);\n<span class="kw">INSERT INTO</span> ledger_line (txn_id, account, amount_cents)\n  <span class="kw">VALUES</span> (<span class="st">\'tx-9\'</span>, <span class="st">\'cash_clearing\'</span>, 15000),\n         (<span class="st">\'tx-9\'</span>, <span class="st">\'loan:ln-5531:principal\'</span>, -15000);\n<span class="kw">UPDATE</span> account_balance\n   <span class="kw">SET</span> balance_cents = balance_cents - 15000,\n       version = version + 1\n <span class="kw">WHERE</span> account = <span class="st">\'loan:ln-5531:principal\'</span>\n   <span class="kw">AND</span> version = 41;\n<span class="kw">COMMIT</span>;      <span class="cm">-- deferred check: lines sum to zero</span></pre>'), [
 "C: Posting, in code. The transaction row carries the key, with a unique constraint, so a retry fails at the first insert and the first result is returned. Two lines that sum to zero. And the balance row updated in the same commit, at the version we read, so two postings to one loan cannot interleave. A deferred check rejects the commit unless the lines sum to zero.",
 "C: Lines are facts, and never change. The balance is a projection, and provable from them."])

S(plain("Data · money and dates", "Three rules that are cheap to state", '<div class="cards c3">'
  '<div class="cd red"><h3>Never a float</h3><p>Integer cents. Rounding of an instalment is a rule: the remainder goes to the last one.</p></div>'
  '<div class="cd"><h3>Business days</h3><p>A due date on a weekend or bank holiday takes effect the next business day; late fees count from there.</p></div>'
  '<div class="cd amb"><h3>Two dates per line</h3><p>When it happened, and when we booked it. A return dated today never edits last month.</p></div></div>'), [
 "C: Three rules that are cheap to say and expensive to forget. Never a float: integer cents, and how an instalment rounds is a rule, with the remainder on the last payment. Business days: a due date on a weekend or a bank holiday takes effect the next business day, and late fees count from there. And two dates on every line: when it happened, and when we booked it, so a return that arrives today never edits last month."])

# ───────────────────────── 5 · high-level design ─────────────────────────
chapter(5, "High-level design", 4, "Three versions, each answering the objection to the one before", [
 "C: Now the design, in three versions, each introduced by the objection to the one before. The boxes never move: every later picture is a view of the same baseline."])

S(dia("High-level design · version 1 of 3", "The simplest thing that works", "base-v1", vtag="V1",
      chip=chips("a cron at 00:00", "a balance column", "a direct call")), [
 "C: Version one. Origination books a loan through the servicing A-P-I. At midnight, a job in the schedule service loops over every loan due today, charges each at the rails, and updates the loan's balance column. It is the simplest thing that works, and many first versions look exactly like this."], cls="dia")

S(plain("V1 · the objection", "A midnight burst, a retry, and a return with nowhere to go",
  '<pre class="trace"><span class="t">00:00:00  </span>job sends 2,000 card charges a second; the contract allows 100\n<span class="t">00:00:03  </span>processor throttles: <span class="bad">95 % rejected</span>, retried at once\n<span class="t">08:00:10  </span>ln-5531 times out; retried as new; <span class="bad">charged twice</span>\n<span class="t">Dec 3     </span>a debit returns; the balance column was already reduced: <span class="bad">nowhere to post it</span>\n<span class="t">Dec 31    </span>auditor: “why is this balance 75,000?” <span class="bad">no history</span></pre>', red=True), [
 "C: The objection, as a trace. At midnight the job sends two thousand card charges a second against a contract of a hundred. Three seconds later the processor throttles ninety-five percent, and the job retries them at once. At eight, one charge times out and is retried as a new charge: charged twice.",
 "C: On the third, a debit comes back, and the balance column was already reduced: there is nowhere to post it. And at year end, an auditor asks why a balance is what it is, and there is no history."])

S(dia("High-level design · version 2 of 3", "One collection per instalment, at the rail's pace, with books", "base-v2", vtag="V2",
      chip=chips("ledger + projection", "claim with SKIP LOCKED", "intent + outbox", "budget per rail")), [
 "C: Version two. The database becomes the servicing database: the ledger with its projection, due items, payment intents and an outbox. The schedule service claims due items and writes intents and outbox rows in one commit. A new dispatcher drains the outbox under a budget per rail, sends each charge with its key, and posts the result.",
 "C: A timeout now leaves the intent unknown instead of failed, and the rail sets the pace instead of a midnight burst."], cls="dia")

S(plain("V2 · the objection", "Correct inside, and still four holes", '<div class="cards c2">'
  '<div class="cd red"><h3>Later news</h3><p>Settlements and returns arrive as files, days later. Nothing reads them.</p></div>'
  '<div class="cd red"><h3>Unknowns pile up</h3><p>Nothing ends an unknown: 240 on the 1st, pending forever.</p></div>'
  '<div class="cd red"><h3>Changing terms</h3><p>Refunds and payoff change schedules. Allocation and fees live in code.</p></div>'
  '<div class="cd red"><h3>Nobody checks</h3><p>Our books can differ from the bank’s, and nothing would notice.</p></div></div>'), [
 "C: The objection to version two. Inside the database it is correct. But settlements and returns arrive as files days later, and nothing reads them. Nothing ends an unknown: two hundred and forty on the first, pending forever. Refunds and payoffs change schedules, while allocation and fees are buried in code. And our books can differ from the bank's without anyone noticing."])

S(dia("High-level design · version 3 of 3", "Close every loop", "base-v3", vtag="V3",
      chip=chips("file ingest", "resolver", "policy", "reconciliation", "notices")), [
 "C: Version three closes those loops. File ingest takes the bank's and processor's files and posts settlements and reversals. A resolver asks the processor about every unknown, by the same key, and hands the answer to the dispatcher. A policy service holds terms, allocation, retry and fee rules as versioned data. Reconciliation matches all three views and gives breaks to finance operations. And an outbox relay feeds customer notices.",
 "C: This is the baseline. Every picture from here on is a view of it."], cls="dia")

S(plain("V3 · the collect path", "Claim, commit, send, post",
  '<pre class="code" data-lang="pseudocode"><span class="kw">def</span> collect(shard):\n  <span class="kw">with</span> db.transaction():\n    rows = db.claim_due(today, shard, 500) <span class="cm"># SKIP LOCKED</span>\n    <span class="kw">for</span> r <span class="kw">in</span> rows:\n      i = intents.open(r.instalment)       <span class="cm"># one open</span>\n      outbox.add("send", i.id, key=i.key)  <span class="cm"># same commit</span>\n\n<span class="kw">def</span> dispatch(i):                           <span class="cm"># rail bucket</span>\n  <span class="kw">try</span>: r = rail.charge(i.token, i.amount, key=i.key)\n  <span class="kw">except</span> Timeout: <span class="kw">return</span> db.set(i, "UNKNOWN")\n  ledger.post(i, r, key=i.key)             <span class="cm"># one commit</span></pre>' +
  line("No branch guesses. A crash anywhere leaves a row that says how far we got.", "a")), [
 "C: The collect path in code. In one transaction: claim up to five hundred due rows with skip locked, open an intent for each, unique while open, and add an outbox row. Then the dispatcher, under the rail's bucket, charges with the intent's key. On a timeout it sets unknown and stops: the resolver takes over. Otherwise it posts lines, balance and state in one commit, under the same key.",
 "C: No branch guesses. A crash at any line leaves a row that says how far we got."])

def flow(n, fr, title, svg, tags, say):
    S(dia(f"High-level design · requirement {n} · {fr}", title, svg, trs=tr(*tags)), say, cls="dia")

flow(1, "schedule", "FR1: a booked loan becomes a schedule", "flow-fr1",
     [("fr", "serves FR1"), ("api", "event LoanBooked"), ("ent", "writes ScheduleVersion · Instalment · LedgerTxn"), ("nfr", "idempotent by loanId")], [
 "C: Requirement one, schedule, by the numbers. One: origination emits loan booked to the servicing A-P-I. Two: the A-P-I hands it to the schedule service. Three: the schedule service asks policy for the terms version: how many instalments, the rounding rule, the allocation order. Four: one transaction writes the schedule version, the due items and the booking lines."])
flow(2, "collect", "FR2: one instalment collected", "flow-fr2",
     [("fr", "serves FR2"), ("api", "Charge · debit file"), ("ent", "writes Intent · Attempt · LedgerTxn"), ("nfr", "under the rail budget")], [
 "C: Requirement two, collect. One: on the due date, the schedule service claims the row and commits the intent and its outbox row. Two: the dispatcher drains the outbox, under the rail's budget. Three: it sends the charge with its key, or puts the debit in the day's file. Four: the result comes back. Five: it posts the result: lines, the balance and the state, in one commit."])
flow(3, "adjust", "FR3: a refund or a payoff", "flow-fr3",
     [("fr", "serves FR3"), ("api", "POST /refunds · payoff-quote"), ("ent", "writes LedgerTxn · ScheduleVersion"), ("nfr", "idempotent")], [
 "C: Requirement three, adjust. One: the merchant's refund, or the customer's payoff, reaches the A-P-I. Two: it goes to the schedule service. Three: policy says how it lands: re-amortise or shorten, and the allocation order. Four: one transaction writes the ledger lines and the new schedule version. Five and six: the answer goes back."])
flow(4, "returns", "FR4: a return reverses a collection", "flow-fr4",
     [("fr", "serves FR4"), ("api", "ImportReturns"), ("ent", "writes ReturnRecord · LedgerTxn"), ("nfr", "dated the day it arrives")], [
 "C: Requirement four, returns. One: the bank's return file arrives and is stored raw. Two: file ingest matches each return to its attempt and posts a reversing transaction, dated the day it arrived, and moves the instalment back to due. Three: the outbox relay emits the event. Four: the customer gets a notice saying what happens next."])
flow(5, "reconcile", "FR5: our books against theirs, every day", "flow-fr5",
     [("fr", "serves FR5"), ("api", "ImportSettlement · ImportStatement"), ("ent", "writes Break"), ("nfr", "owned within a day")], [
 "C: Requirement five, reconcile. One: the processor's report and the bank's statement arrive and are stored raw. Two: file ingest passes their lines to reconciliation. Three: reconciliation reads the ledger's expectations for the day and matches line by line. Four: every line that doesn't match becomes a break, with an owner, in front of finance operations."])

S(dia("Design · C4 level 1", "The system in its context", "c4-context"), [
 "C: The C4 context. The customer repays and asks for payoffs. Merchants send refunds. Origination books loans. Our servicing system charges and queries at the card processor, sends debit files to the bank, and receives returns and statements from it. Finance operations own the breaks and the close. Notice that the processor and the bank each keep their own books of the same money."], cls="dia")

S(dia("Design · C4 level 2", "The containers", "c4-containers"), [
 "C: The containers. The servicing A-P-I owns keys, refunds and quotes. Schedule and collect owns due items and the state machine. The servicing database holds the ledger, intents and outbox, partitioned by month. The dispatcher owns the rail budgets. Below: policy, file ingest, the resolver, and reconciliation, which reads expectations from the ledger."], cls="dia")

S(dia("Design · sequence", "One card instalment, as a sequence", "seq-collect"), [
 "C: One card instalment as a sequence. One, highlighted: the claim, the intent and the outbox row in one commit. Two: the dispatcher drains the outbox at ninety a second. Three: charge a hundred and fifty dollars with key coll, loan fifty-five thirty-one, instalment two, attempt one. Approved in one point four seconds. Four: one transaction sets settled, posts the lines and the balance. A retry with the same key stops at the ledger's unique key."], cls="dia")
