from dsl import *

# ───────────────────────── 4 · API and entities ─────────────────────────
chapter(4, "API and entities", 3, "The contract first. It forces the semantics into the open.", [
 "C: The A-P-I before the boxes. It is the contract with every merchant, and it shows whether I have thought about failure. Every call carries a tag: the requirement it serves and the entity it reads or writes."])

def wire(l, r): return f'<div class="cols2"><pre class="wire">{l}</pre><pre class="wire">{r}</pre></div>'

S(plain("API · pay", "POST /v1/payments", tr(("fr", "serves FR1"), ("api", "POST /payments"), ("ent", "writes Idempotency · Payment · Attempt · JournalTxn"), ("nfr", "idempotent")) +
  wire('<span class="cm">// request</span>\nPOST /v1/payments\nIdempotency-Key: k-91\n{ merchantId: "m-42",\n  amount: { value: 1050,\n            currency: "EUR" },\n  methodToken: "tok_7c1…",\n  capture: "auto" }',
       '<span class="cm">// response</span>\n201 { paymentId: "p-7731",\n      status: "captured" }\n\n<span class="cm">// or, honestly</span>\n202 { paymentId: "p-7731",\n      status: "pending" }\n\n<span class="cm">// same key, other body → 422\n// same key, in flight  → 409</span>')), [
 "C: Pay. The client sends an idempotency key in a header, and a body with the merchant, the amount and a token for the card. The amount is an integer in minor units with its currency: one thousand and fifty cents, never ten point five as a float. The card number never reaches us: a token does.",
 "C: The response is the payment I-D and a status, and the status can honestly be pending. The same key with a different body is rejected with a four twenty-two. The same key while the first is still in flight gets a four-oh-nine: retry later."])

S(dia("API · the payment's states", "A state machine with an exit from “unknown”", "states", chip=chips("UNKNOWN is a state", "illegal transitions rejected")), [
 "C: Behind that status is an explicit state machine. Created, then auth pending when we send it. From there, authorised or declined, or the red one: unknown, on a timeout or an ambiguous answer. Unknown has exactly two exits: the inquiry says approved, or the processor says not found after its safe window.",
 "C: Then captured, settled when the file matches, partially refunded, refunded, and chargeback. Any transition not drawn here is rejected by the code. A capture on a declined payment is not a bug to handle later: it cannot happen."], cls="dia")

S(plain("API · capture, void, refund", "Adjustments are new operations, never edits", tr(("fr", "serves FR1 · FR2"), ("api", "capture · void · refunds"), ("ent", "writes Payment · JournalTxn"), ("nfr", "idempotent")) +
  wire('<span class="cm">// each with its own Idempotency-Key</span>\nPOST /v1/payments/p-7731/capture\n     { amount: 1050 }\nPOST /v1/payments/p-7731/void\nPOST /v1/payments/p-7731/refunds\n     { amount: 2500 }',
       '<span class="cm">// the refund limit, one statement</span>\nUPDATE payment\n SET refunded = refunded + :amt\n WHERE id = :p\n   AND refunded + :amt &lt;= captured\n<span class="cm">// 0 rows → 422 exceeds captured</span>')), [
 "C: Capture, void and refund are separate calls, each with its own idempotency key. Each one creates a new journal transaction that references the payment. Nothing is edited.",
 "C: The refund limit is enforced by one conditional update on the payment row: add the amount only if the total stays within what was captured. Zero rows updated means the refund is refused. That one statement will matter in challenge five."])

S(plain("API · notify", "Webhooks, and the poll that backs them up", tr(("fr", "serves FR3"), ("api", "webhook · GET /payments/{id}"), ("ent", "reads Outbox · Payment")) +
  wire('<span class="cm">// to the merchant, signed</span>\nPOST https://merchant/hooks\nSignature: t=…, v1=…\n{ eventId: "e-551",\n  type: "payment.captured",\n  paymentId: "p-7731",\n  status: "captured" }',
       '<span class="cm">// retried with backoff for days\n// merchants de-duplicate by eventId</span>\n\n<span class="cm">// the backstop: always correct</span>\nGET /v1/payments/p-7731\n -> { status: "captured", … }')), [
 "C: Notify. Every state change becomes a signed webhook with an event I-D. It is retried with backoff, for days if necessary, so a merchant may see the same event twice and de-duplicates by event I-D.",
 "C: And the backstop: a get on the payment always returns the state from our database. A merchant who missed every webhook can still find out."])

S(plain("API · internal calls", "Inquiry, settlement import, balance", tr(("fr", "serves FR1 · FR4 · FR5"), ("api", "Inquire · ImportSettlement · balance"), ("ent", "Attempt · SettlementLine · Break · BalanceProjection")) +
  wire('<span class="cm">// our reference per attempt</span>\nInquire(processor, "p-7731/1")\n -> approved | declined | not_found\n\n<span class="cm">// the raw file is stored unchanged</span>\nImportSettlement(file)\nGET /breaks?status=open&amp;age&gt;1d',
       '<span class="cm">// balance, from the projection</span>\nGET /v1/accounts/acc-9/balance\n -> { balance: 18204400,\n      currency: "EUR",\n      asOfEntry: 991200731 }\n\n<span class="cm">// for audit: the sum over entries\n// for the period, joined to txns</span>')), [
 "C: Three internal calls. Inquire asks a processor about our own reference for one attempt: payment I-D, slash, attempt number. Import settlement stores the processor's file unchanged before anything reads it. And breaks are listed by status and age.",
 "C: A balance comes from the projection, and says which entry it is current to. For an audit, the answer is the sum over entries for the period, joined to their transactions and payments."])

S(dia("Data · conceptual model", "Entities and relationships, in Chen notation", "erd-chen"), [
 "C: The conceptual model. A payment has attempts: one per call to a processor, each with our reference. A payment posts journal transactions. A transaction contains entries, at least two, and each entry is on one account. A balance is a derived attribute of an account: the sum of its entries.",
 "C: A break, from reconciliation, may explain one transaction. The double borders are weak entities: an attempt only exists inside its payment, and an entry only inside its transaction."], cls="dia")

S(dia("Data · physical model", "Tables, keys, and what is allowed to change", "erd-physical"), [
 "C: The physical model. Journal entries are partitioned by account and only ever inserted. Journal transactions carry the payment and the type, and a check at commit that debits equal credits per currency. The payment row is the only mutable row, and it is changed only by conditional updates.",
 "C: Idempotency keys with their request hash and stored response, kept seven days. The outbox, written in the same transaction as the state. And a balance projection that can be rebuilt from the entries at any time."], cls="dia")

S(dia("Data · a worked example", "One capture, as balanced entries", "entries", chip=chips("integer minor units", "debits = credits")), [
 "C: A worked example. A capture of one thousand and fifty, with a fee of thirty. The processor receivable is debited one thousand and fifty: the processor owes us that. The merchant payable is credited one thousand and twenty: we owe the merchant that. And fee revenue is credited thirty. Debits, one thousand and fifty. Credits, one thousand and fifty. Balanced.",
 "C: A refund is a new transaction that mirrors these lines. Nothing in this one ever changes."], cls="dia")

S(plain("Data · money", "Three rules about amounts", '<div class="cards c3">'
  '<div class="cd red"><h3>Never a float</h3><p>0.1 + 0.2 is not 0.3 in binary floating point. Integer minor units only.</p></div>'
  '<div class="cd"><h3>A currency on every amount</h3><p>An amount without its currency is a bug waiting for the second currency.</p></div>'
  '<div class="cd amb"><h3>Conversion is a transaction</h3><p>With the rate it used, versioned. Never a silent multiply.</p></div></div>'), [
 "C: Three rules about amounts, because they are cheap to state and expensive to forget. Never a float: in binary floating point, point one plus point two is not point three, and the error ends up in someone's balance. A currency on every amount. And conversion, if it ever happens, is its own transaction, with the rate it used, versioned."])

# ───────────────────────── 5 · high-level design ─────────────────────────
chapter(5, "High-level design", 4, "Three versions, each answering the objection to the one before", [
 "C: Now the design, in three versions. Each version is introduced by the objection to the one before. The boxes never move: every later picture is a view of the same baseline."])

S(dia("High-level design · version 1 of 3", "The simplest thing that works", "base-v1", vtag="V1",
      chip=chips("one service", "one database", "a synchronous call")), [
 "C: Version one. The merchant calls the payments A-P-I. The payment service charges the card at the processor, synchronously. When the answer comes back, it updates the payment's status and the merchant's balance column in one transaction, and answers. It is the simplest thing that works, and many first versions look exactly like this."], cls="dia")

S(plain("V1 · the objection", "A timeout, a retry, and two charges",
  '<pre class="trace"><span class="t">10:00:00.000  </span>p-7731 sent to the processor, 1,050\n<span class="t">10:00:01.900  </span>no answer: marked <span class="bad">failed</span>\n<span class="t">10:00:02.400  </span>the processor approves it\n<span class="t">10:00:05.000  </span>the checkout retries as a new payment p-7744: approved\n<span class="t">10:00:05.000  </span><span class="bad">the customer has two holds of 1,050</span>\n<span class="t">next month    </span>auditor: “why is this balance 18,204,400?” <span class="bad">no history</span></pre>', red=True), [
 "C: The objection, as a trace. At ten o'clock the payment goes to the processor. At one point nine seconds, no answer, so version one marks it failed. At two point four seconds the processor approves it anyway. At five seconds the checkout retries as a new payment, which is approved. The customer now has two holds.",
 "C: And next month an auditor asks why a balance is what it is, and the answer is a number that was updated in place. There is no history to show."])

S(dia("High-level design · version 2 of 3", "One effect per intent, and books that prove themselves", "base-v2", vtag="V2",
      chip=chips("key inserted first", "attempt committed before the call", "UNKNOWN", "journal")), [
 "C: Version two. The A-P-I inserts the idempotency key first. The payment service commits the payment as auth pending, with an attempt and our reference, before it calls out. A new adapter calls the processor with that reference. And the database now holds a journal: balanced, immutable entries, with balances as a projection.",
 "C: A timeout now moves the payment to unknown instead of failed, and a retry with the same key gets the same answer instead of a new payment."], cls="dia")

S(plain("V2 · the one transaction", "State, entries, outbox row and key, together",
  '<pre class="code">BEGIN;\n  UPDATE payment SET state = <span class="kw">\'CAPTURED\'</span>, captured = 1050\n   WHERE id = <span class="kw">\'p-7731\'</span> AND state = <span class="kw">\'AUTH_PENDING\'</span>;  <span class="cm">-- legal edge only</span>\n  INSERT INTO journal_txn   (txn_id, payment_id, type) VALUES (…, <span class="kw">\'capture\'</span>);\n  INSERT INTO journal_entry (account, dir, amount_minor, currency)  <span class="cm">-- 3 rows</span>\n       VALUES (recv, <span class="kw">\'D\'</span>, 1050, …), (mpay, <span class="kw">\'C\'</span>, 1020, …), (fees, <span class="kw">\'C\'</span>, 30, …);\n  INSERT INTO outbox (payload) VALUES (<span class="kw">\'payment.captured p-7731\'</span>);\n  UPDATE idempotency SET status = <span class="kw">\'done\'</span>, response = … WHERE key = <span class="kw">\'k-91\'</span>;\nCOMMIT;  <span class="cm">-- a deferred check rejects it unless debits = credits</span></pre>' +
  line("All or nothing. There is no moment where the state says captured and the books do not.", "a")), [
 "C: The heart of version two is this one transaction. Move the state from auth pending to captured, and only along a legal edge. Insert the journal transaction and its three entries. Insert the outbox row. Mark the idempotency key done, with the response. Commit, and a deferred check rejects the whole thing unless debits equal credits.",
 "C: All or nothing. There is never a moment where the state says captured and the books do not."])

S(plain("V2 · the objection", "Correct inside, and still three holes", '<div class="cards c3">'
  '<div class="cd red"><h3>Telling others</h3><p>Merchants and other systems hear about a change by a second write after the commit. A crash in between, and they never hear.</p></div>'
  '<div class="cd red"><h3>Unknowns pile up</h3><p>Nothing ends an unknown. Ten a second at peak, forever pending.</p></div>'
  '<div class="cd red"><h3>The outside disagrees</h3><p>Our books can still differ from the processor\'s, and nobody would know.</p></div></div>'), [
 "C: The objection to version two. Inside the database it is correct. But merchants hear about a change through a second write after the commit, so a crash in between means they never hear. Nothing ends an unknown: ten a second at peak, pending forever. And our books can still disagree with the processor's, and nothing would notice."])

S(dia("High-level design · version 3 of 3", "Close every loop", "base-v3", vtag="V3",
      chip=chips("outbox → log → webhooks", "inquiry job", "reconciliation", "finance ops")), [
 "C: Version three closes those loops. From the database, an outbox relay feeds an event log, and a webhook sender posts signed events to the merchant. An inquiry job reads unknown payments, asks the adapter by reference, and resolves them in the database. And reconciliation takes the processor's settlement file, compares it with expectations from the ledger, and hands breaks to finance operations.",
 "C: This is the baseline. It stays on screen, and every picture from here on is a view of it."], cls="dia")

S(plain("V3 · the pay path", "Commit, call, commit again",
  '<pre class="code"><span class="kw">def</span> pay(req, key):\n    row = idem.insert_or_get(req.client, key, hash(req))   <span class="cm"># unique; same txn as below</span>\n    <span class="kw">if</span> row.existing: <span class="kw">return</span> row.response <span class="kw">or</span> conflict(<span class="kw">"in progress"</span>)\n    p = db.commit(new_payment(req, state=<span class="kw">"AUTH_PENDING"</span>, attempt=1))  <span class="cm"># evidence first</span>\n    <span class="kw">try</span>:\n        r = adapter.authorise(p, ref=f<span class="kw">"{p.id}/1"</span>, deadline=1.9)\n    <span class="kw">except</span> Timeout:\n        db.commit(p.to(<span class="kw">"UNKNOWN"</span>))                      <span class="cm"># the inquiry job takes over</span>\n        <span class="kw">return</span> pending(p)\n    <span class="kw">return</span> db.commit(p.apply(r), entries(r), outbox(r), idem_done(key))</pre>' +
  line("No branch guesses. A crash anywhere leaves a row that says how far we got.", "a")), [
 "C: The pay path in code. Insert or read the idempotency key; if it already exists, return the stored response or say in progress. Commit the payment as auth pending with attempt one: evidence first. Call the adapter with our reference and a deadline of one point nine seconds. On a timeout, commit unknown and answer pending: the inquiry job takes over. Otherwise one transaction: state, entries, outbox, key done.",
 "C: No branch guesses. A crash at any line leaves a row that says how far we got."])

S(plain("V3 · what it leaves open", "The details are where it breaks", '<div class="cards c2">'
  '<div class="cd grn"><h3>What V3 has</h3><p>Keys inserted first, an unknown state with an exit, one transaction for state and books, an outbox, inquiry, reconciliation.</p></div>'
  '<div class="cd red"><h3>What it has not been tested against</h3><p>A real timeout. Three retries at once. A crash mid-way. A hot merchant. Late refunds. A statement that disagrees. A bad release. A silent decline.</p></div></div>' +
  line("Eight questions. Each fix creates the next. These are the challenges.", "r")), [
 "C: What version three leaves open. It has every mechanism from the theory chapter. It has not yet been tested against a real timeout, three retries at once, a crash in the middle, a hot merchant, late refunds, a statement that disagrees, a bad release, or a silent drop in approvals. Those are the eight challenges, after the flows."])

def flow(n, fr, title, svg, tags, say):
    S(dia(f"High-level design · requirement {n} · {fr}", title, svg, trs=tr(*tags)), say, cls="dia")

flow(1, "pay", "FR1: one payment, end to end", "flow-fr1",
     [("fr", "serves FR1"), ("api", "POST /payments"), ("ent", "writes Payment · Attempt · JournalTxn · Outbox"), ("nfr", "< 2 s or pending")], [
 "C: Requirement one, pay, by the numbers. One: the merchant posts the payment with its key. Two: the A-P-I hands it to the payment service. Three: one transaction inserts the key and commits the payment as auth pending, with its attempt. Four: the service asks the adapter to authorise. Five: the adapter calls the processor with our reference.",
 "C: Six: approved comes back. The service then commits the second transaction: the state, the entries, the outbox row and the key marked done. Seven: the status goes back to the A-P-I. Eight: the merchant gets its answer."])
flow(2, "adjust", "FR2: a refund", "flow-fr2",
     [("fr", "serves FR2"), ("api", "POST /refunds"), ("ent", "writes Payment · JournalTxn"), ("nfr", "≤ captured")], [
 "C: Requirement two, a refund. One and two: the merchant's refund call, with its own key, reaches the service. Three: the conditional update on the payment row, which refuses anything that would exceed the captured amount. Four and five: the refund goes to the processor with a reference made from the payment and the refund key. Six: the result comes back, and a new journal transaction is posted, dated now, referencing the payment."])
flow(3, "notify", "FR3: every change reaches the merchant", "flow-fr3",
     [("fr", "serves FR3"), ("api", "webhook"), ("ent", "reads Outbox"), ("nfr", "at least once")], [
 "C: Requirement three, notify. One: the outbox row is committed in the same transaction as the state. Two: the relay reads committed rows and publishes them to the event log. Three: the webhook sender reads the log. Four: it signs and posts to the merchant, retrying with backoff. The merchant de-duplicates by event I-D, and can always fall back to asking for the payment."])
flow(4, "reconcile", "FR4: our books against theirs, every day", "flow-fr4",
     [("fr", "serves FR4"), ("api", "ImportSettlement"), ("ent", "writes Break"), ("nfr", "owned within a day")], [
 "C: Requirement four, reconcile. One: the processor's settlement file arrives and is stored unchanged. Two: the reconciliation job asks the ledger for the day's expectations, by reference and net of fees, and matches line by line. Matches move payments to settled, with settlement entries. Three: every line that does not match becomes a break, with an owner, in front of finance operations."])
flow(5, "explain", "FR5: any balance, from the journal", "flow-fr5",
     [("fr", "serves FR5"), ("api", "GET /balance"), ("ent", "reads BalanceProjection · JournalEntry")], [
 "C: Requirement five, explain. One and two: a balance request reaches the service. Three: it reads the projection, which says the entry it is current to. Four and five: the answer goes back. For an audit, the same path sums the entries for the period and joins them to their transactions and payments: every number explained by the records that produced it."])

S(dia("Design · C4 level 1", "The system in its context", "c4-context"), [
 "C: The C4 context. A customer pays at a merchant. The merchant's system creates payments and receives webhooks. Our payments and ledger system authorises, captures and inquires at the processor, and receives its settlement files every day. And finance operations owns breaks and corrections. Notice that two of the four neighbours keep their own books of the same money."], cls="dia")

S(dia("Design · C4 level 2", "The containers", "c4-containers"), [
 "C: The containers. The payments A-P-I owns keys and the deadline. The payment service owns the state machine and the postings. The database holds payments, the journal and the outbox, partitioned by account. The adapter owns references and the processor's error codes. Below: the outbox relay and log, the webhook sender, the inquiry job, and the reconciliation pipeline, which writes expectations and adjustments back into the ledger."], cls="dia")

S(dia("Design · sequence", "One payment, as a sequence", "seq-pay"), [
 "C: The same payment as a sequence. One: the merchant posts with key k-ninety-one. Two: the A-P-I inserts the key as processing, commits the payment as auth pending, and the attempt with reference p-seventy-seven thirty-one slash one. Three and four: authorise, through the adapter, with that reference. Approved in three hundred and forty milliseconds. Five, highlighted: the one transaction. Then two-oh-one, captured."], cls="dia")
