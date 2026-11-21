# SD-44 Payment processing and the double-entry ledger: reference solution (Staff L6/L7)

<!-- Video script for slide-video-kit/scripts/build_video.py. [slide: v-NNN] = frames/v-NNN.png, the number printed on every slide.
     Speakers: C candidate · I interviewer · V key line (slower) · N coach. Generated from src/*.py: edit the sources, not this file. -->
<!-- voices: N=af_heart@0.92 I=bf_emma@0.95 C=am_michael@0.9 V=am_michael@0.84 -->
<!-- labels: N=COACH -->
<!-- say: API=A-P-I APIs=A-P-Is SLO=S-L-O SLOs=S-L-Os SLI=S-L-I SLIs=S-L-Is TTL=T-T-L HTTP=H-T-T-P HTTPS=H-T-T-P-S SQL=S-Q-L ID=I-D IDs=I-Ds EM=E-M AUX=aux SRE=S-R-E RFC=R-F-C UUID=U-U-I-D CDC=C-D-C KYC=K-Y-C FX=F-X PCI=P-C-I PSP=P-S-P TB=terabytes GB=gigabytes MB=megabytes KB=kilobytes p99=p-ninety-nine UNKNOWN=unknown AUTH_PENDING=auth-pending -->


## 0 Cold open

[slide: v-001]
[pause: 1.2]
C: The happy path of a payment is three boxes and a database. A merchant asks, we call the bank, we write it down. This question is not about the happy path. It is about the other paths: a bank call that times out and leaves you not knowing whether the customer paid, a client that retries the same payment three times at once, and a statement that disagrees with your books.
[pause: 1.8]

[slide: v-002]
[pause: 0.6]
I: Design the system that takes a payment and records it. The ledger the company's money is accounted for in.
[pause: 1.5]

[slide: v-003]
[pause: 1.3]
C: Here is the hook, as a timeline. The merchant wants an answer in two seconds. But the truth about a payment arrives over months. The processor's answer comes in about a second, or not at all. An inquiry can settle an unknown outcome in minutes. The settlement file with the processor's own books arrives the next day. And a dispute can still arrive months later.
C: Every strong answer to this question is a design for not knowing yet. The rest of this video puts one mechanism at each point on this line.
[pause: 1.1]

[slide: v-004]
[pause: 1.0]
N: Five axes. The weak signal is a balance column and a retry loop. The strong signal is a precise statement of what cannot be guaranteed, and a design that is honest about it.
C: I'll keep one sentence in front of everything: exactly-once does not exist across a network boundary. Everything I build is a way of living with that.
[pause: 1.0]

[slide: v-005]
[pause: 0.7]
V: Exactly-once does not exist across a network boundary. So the design is at-least-once delivery, one effect per intent, a state for we don't know yet, and a reconciliation that finds what the rest missed. All of it written to an append-only double-entry journal, where a balance is a sum, never a field.
[pause: 1.0]
C: Concretely: an idempotency key that is inserted before anything happens. An explicit state machine with an unknown state. Immutable journal entries. And a daily match against the processor's books, with owners for every difference.
[pause: 1.6]

[slide: v-006]
[pause: 0.6]
C: The order. Requirements and scope, then numbers, then a short theory chapter the design can lean on. Then the A-P-I and data model, and a design in three versions, each answering the objection to the one before.
C: Then most of the time goes to eight challenges that break the design, where each fix creates the next question. A build cost, and a recap.
[pause: 0.8]

[pause: 1.4]

## 1 Requirements and scope

[slide: v-007]
[pause: 1.2]
C: Before I draw anything, seven questions. Each answer changes the design.
[pause: 1.8]

[slide: v-008]
[pause: 0.6]
C: What volume are we designing for?
I: Ten thousand payments a second at peak, in fifty currencies.
C: Ten thousand a second is a lot of journal writes, and fifty currencies means every amount carries its currency. I'll size both.
[pause: 0.6]

[slide: v-009]
[pause: 0.6]
C: How fast must the client get an answer?
I: An authorisation decision within two seconds.
C: And most of those two seconds belong to the processor, not to us. So our own part has to be small, and we need a plan for when the processor uses all of it.
[pause: 0.6]

[slide: v-010]
[pause: 0.6]
C: Who actually moves the money?
I: Card networks and banks, through processors. They time out, return ambiguous results, and sometimes go down for hours.
C: That is the most important answer. Ambiguous results mean a state for not knowing. Hours of outage mean a second processor and rules for when it is safe to use it.
[pause: 0.6]

[slide: v-011]
[pause: 0.6]
C: What is the ledger's rule?
I: It must always balance. No exceptions.
C: Then every movement is written as entries that sum to zero, in one transaction, and a check that it still sums to zero runs all the time.
[pause: 0.6]

[slide: v-012]
[pause: 0.6]
C: How long must the books be explainable?
I: Every balance explainable from immutable records, for seven years.
C: Immutable and explainable rules out a balance column that is updated in place. A balance becomes a sum over records.
[pause: 0.6]

[slide: v-013]
[pause: 0.6]
C: Refunds and disputes?
I: Partial and full refunds, and chargebacks, arriving days or months later.
C: Months later means the original period may be closed. So corrections are new records dated when they happen, never edits.
[pause: 0.6]

[slide: v-014]
[pause: 0.6]
C: What must never happen, in priority order? I'd propose: first, charging a customer twice or losing money. Second, an unbalanced ledger. Third, a slow payment.
I: Your call. I agree with that order.
C: That order settles a lot. When I have to choose between a fast answer and a correct one, I answer pending.
[pause: 0.6]

[slide: v-015]
[pause: 0.6]
C: Functionally, five things. One, pay: authorise and capture, idempotent per client key. Two, adjust: void, refund, and chargeback, each referencing the original payment. Three, notify: every state change reaches the merchant as a signed webhook.
C: Four, reconcile: match our books against each processor's settlement file every day, and turn every difference into a break with an owner. Five, explain: any account's balance at any time, from the journal. Each of these gets a numbered flow later.
[pause: 0.8]

[slide: v-016]
[pause: 0.6]
C: The numbers, all initial targets. Zero double charges. A decision within two seconds at the ninety-ninth percentile, or an honest pending. Ninety-nine percent of unknown outcomes resolved within fifteen minutes. Every difference with the processor found and owned within a day. Plus: every journal transaction balanced at commit, and seven years of retention.
[pause: 0.8]

[slide: v-017]
[pause: 0.6]
C: In scope: authorise, capture, void, refund and chargeback, webhooks, the ledger, reconciliation, and amounts in fifty currencies without conversion.
C: Out of scope, on purpose. Fraud scoring is a service I call. Card numbers live in a tokenisation service, which keeps most of the card-data compliance scope away from us. Currency conversion, merchant onboarding and payouts are their own questions, though payouts will come back twice, because they need a balance check.
[pause: 0.8]

[slide: v-018]
[pause: 0.7]
C: So the core is four things. A state machine for each payment that admits unknown. An idempotent A-P-I. An immutable double-entry journal. And reconciliation against the outside world. Everything else is in service of those four.
[pause: 1.6]

[pause: 1.4]

## 2 Estimates

[slide: v-019]
[pause: 1.2]
C: Numbers next. Each one is arithmetic from what the interviewer said, carries a label, and ends with the decision it drives. I'll say it once for this chapter: these are illustrative, not measured.
[pause: 1.8]

[slide: v-020]
[pause: 1.0]
C: Ten thousand payments a second, and each capture writes about four journal entries: the receivable, the merchant's share, the fee. Forty thousand entries a second at peak.
C: Decision: one database primary will not take that at peak. The journal is partitioned by account, and a payment's entries go to the partitions of the accounts they touch.
[pause: 1.0]

[slide: v-021]
[pause: 1.0]
C: The average is lower. Say a third of the peak: about three thousand three hundred a second. Times eighty-six thousand four hundred seconds, that is about two hundred and ninety million payments a day.
C: Decision: the daily settlement files will have hundreds of millions of lines. Reconciliation is a batch job sized for that, not a spreadsheet.
[pause: 1.0]

[slide: v-022]
[pause: 1.0]
C: Seven years. Three thousand three hundred a second, times seconds in a year, times seven, times four entries: about two point nine trillion entries. At two hundred bytes each, about five hundred and eighty terabytes.
C: Decision: recent partitions stay hot, older ones move to a cold archive. Because entries never change, archiving is a copy, not a migration.
[pause: 1.0]

[slide: v-023]
[pause: 1.3]
C: The number that shapes the data model. One large merchant receives five thousand payments a second. If each payment updates that merchant's balance row, each update holds a row lock for about one and a half milliseconds. That allows about six hundred and seventy updates a second on one row.
C: The queue grows by over four thousand a second, and within a second that merchant's payments are past two seconds. Decision: payments append entries, and the balance is derived. Where a check needs the balance now, I'll split the account. That is challenge four.
[pause: 1.1]

[slide: v-024]
[pause: 1.3]
C: The two-second budget. Our own work: the idempotency insert, a fraud call of about fifty milliseconds, two commits, and the post-commit write. About ninety milliseconds together. The processor, at its ninety-ninth percentile, about one and a half seconds. That leaves about four hundred spare.
C: Decision: everything we own stays under a hundred milliseconds. And at one point nine seconds, if the processor has not answered, we answer pending and keep waiting.
[pause: 1.1]

[slide: v-025]
[pause: 1.0]
C: Unknown outcomes. Say one in a thousand authorisations times out. At peak that is ten a second, thirty-six thousand an hour.
C: Decision: resolving them is not a cron script. The inquiry job is a real service, with its own throughput, and it must respect the processor's rate limits.
[pause: 1.0]

[slide: v-026]
[pause: 1.0]
C: Two tables that are bigger than they look. Idempotency keys for seven days: two hundred ninety million a day, times seven, times three hundred bytes: about six hundred gigabytes. So keys expire, and the A-P-I contract says a retry after seven days is a new payment.
C: And the settlement file: about two hundred ninety million lines. Matched at a million lines a second, about five minutes. Decision: reconciliation is a batch join. Its useful output is not the matches. It is the breaks.
[pause: 1.0]

[slide: v-027]
[pause: 1.0]
C: Last, cost. Processor fees are a percentage of the money that moves. One basis point, one hundredth of a percent of a year's volume, outweighs the whole database cluster.
N: That is the cost judgement this round looks for. The engineering levers on cost are routing and false declines, not servers.
C: That is the numbers. Next, theory.
[pause: 1.0]

[pause: 1.4]

## 3 Theory

[slide: v-028]
[pause: 1.2]
C: A short theory chapter before any design, so the design can lean on it. Six parts: what a payment system is and is not, the properties, the central tension, seven mechanisms, an options matrix, and the failure catalogue. Every slide here carries a theory badge.
[pause: 1.8]

[slide: v-029]
[pause: 0.7]
V: A payment system turns a customer's intent to pay into exactly one movement of money between accounts, records every movement as balanced, immutable journal entries, and keeps its books in agreement with the outside parties that actually move the money.
[pause: 1.0]
C: Every clause is load-bearing. One intent, one movement: that is idempotency, not exactly-once delivery. Balanced: double entry, per currency, in integer minor units. Immutable: a correction is a new entry. And in agreement with the outside: reconciliation is a component, not a safety net.
[pause: 1.6]

[slide: v-030]
[pause: 0.6]
C: Four confusions. The payment system is not the ledger. One orchestrates an intent across outside parties, the other is the book of record, and they fail differently. A ledger is not a balance table: a balance is a sum, and a number updated in place cannot explain itself.
C: Idempotency is not de-duplicating messages. It is one effect per intent, with the original answer returned to every retry. And here is the precision statement for this whole video: exactly-once delivery is impossible across a network. What we can build is at-least-once delivery with an effect that happens once.
[pause: 0.8]

[slide: v-031]
[pause: 0.6]
V: Safety: one intent never moves money twice, every journal transaction balances, and history is never rewritten. Liveness: every payment leaves unknown for a final state, every difference with the outside world becomes an owned break within a day, and every change reaches the merchant.
[pause: 0.8]
C: Three safety properties and three liveness properties. Every fix from here on says which one it serves. Notice that liveness is where most designs are silent: they never say how an unknown ends.
[pause: 0.8]

[slide: v-032]
[pause: 1.0]
C: The central tension: the client wants an answer in two seconds, and the truth arrives over months. Back to that timeline as a table. At two seconds we know approved, declined, or nothing, and the tools are the idempotency key and the unknown state. In minutes, the inquiry. The next day, reconciliation. Months later, an adjusting transaction.
C: The point is that no mechanism replaces another. A design that has idempotency but no reconciliation, or reconciliation but no unknown state, has a hole at one point on this line.
[pause: 1.0]

[slide: v-033]
[pause: 0.6]
C: Mechanism one, the idempotency key, inserted first. It protects S-one. The client sends a key, and we insert it, unique per client, with a hash of the request, in the same transaction that creates the payment. The final response is stored on that row. It rules out a retry or a concurrent duplicate becoming a second payment. It costs a table with a retention window, and an in-progress answer clients must handle.
[pause: 0.8]

[slide: v-034]
[pause: 0.6]
C: Mechanism two, a state machine with an unknown state. It protects S-one and L-one. A timeout or an ambiguous answer moves the payment to unknown: a real state with its own exits. And the attempt is committed before the call goes out, so a crash leaves evidence. It rules out treating a timeout as a failure, which double-charges on retry, or as a success, which loses money. It costs more states to test, and pending answers.
[pause: 0.8]

[slide: v-035]
[pause: 0.6]
C: Mechanism three, the immutable double-entry journal. It protects S-two, S-three and the audit. Every movement is a set of entries whose debits equal its credits, per currency. Entries are inserted, never updated, and a balance is a projection over them. It rules out balances nobody can explain, lost cents, and a hot lock on a balance row. It costs storage that only grows, and projections for reads.
[pause: 0.8]

[slide: v-036]
[pause: 0.6]
C: Mechanism four, the transactional outbox. It protects L-three. The event is a row in the same transaction as the state change, and a relay publishes committed rows, at least once. It rules out a committed state with no event, and an event for a change that rolled back. It costs a relay to run, and consumers that de-duplicate by event I-D.
[pause: 0.8]

[slide: v-037]
[pause: 0.6]
C: Mechanism five, inquiry and reversal by our own reference. It protects L-one, and S-one on retry. Every attempt carries a reference we generate, so we can ask the processor what happened to it, and reverse it by the same reference. It rules out an unknown that never ends. It costs a job per processor, and processors differ in what they support.
[pause: 0.8]

[slide: v-038]
[pause: 0.6]
C: Mechanism six, reconciliation. It protects L-two, and correctness against the outside world. The ledger produces what it expects each processor to settle, the raw file is matched line by line, and every unmatched line becomes a break with a type, an owner and an age. It rules out silent divergence. It costs a pipeline, a workflow, and people.
[pause: 0.8]

[slide: v-039]
[pause: 0.6]
C: Mechanism seven, for the hot account: sub-accounts, or one writer for the rare checked operation. It protects throughput where a check needs a current balance. It rules out a merchant serialising on one row, and a payout larger than the available funds. It costs a sum over several rows and a routing rule.
[pause: 0.8]

[slide: v-040]
[pause: 1.0]
C: Now the options, each with the failure that rules it out. Three that look reasonable first.
C: A, a balance column updated in a transaction, with retries assumed safe. It fails at the first timeout and retry: a double charge. B, a distributed transaction across our database and the processor. It fails always: the processor is not a participant in our transaction, and it will not hold a prepared state while we decide. C, a saga with compensations and no ledger rules. It fails when a compensation itself times out, and it never says what the books should be.
[pause: 1.0]

[slide: v-041]
[pause: 1.0]
C: Part two. D is the pick: the state machine with unknown, the idempotency key, the immutable journal, the outbox, the inquiry and reconciliation. It fails only when a processor gives no way to ask about our reference, and then the settlement file is the arbiter, a day late.
C: E, an event-sourced ledger in a log. It is how I would build the projections inside D, but on its own it fails when a refund or a payout needs a current balance right now. F, buy: the processor's own records. That is the honest first version for a small company with one processor. It fails at the second processor, or when we must keep our own books.
[pause: 1.0]

[slide: v-042]
[pause: 0.6]
C: So, D. What it buys is never guessing. A retry is harmless, an unknown has an exit, every balance is a sum of facts, and the outside world is checked daily. What it gives up: more states to test, a reconciliation function with people in it, and pending answers that every merchant integration has to handle. I'd say that cost out loud, because it lands on other teams.
[pause: 0.8]

[slide: v-043]
[pause: 1.0]
C: Last, the failure catalogue, which becomes the challenge list. A timeout, the crux. Concurrent retries. A crash between commit and event. The hot merchant. Refunds and late chargebacks. Books that disagree with the processor's, the second half of the crux. A bug that posted wrong entries. And nobody noticing. Floating-point money is a real failure too, but it is settled on the A-P-I slides: integer minor units and a currency on every amount.
[pause: 1.0]

[pause: 1.4]

## 4 API and entities

[slide: v-044]
[pause: 1.2]
C: The A-P-I before the boxes. It is the contract with every merchant, and it shows whether I have thought about failure. Every call carries a tag: the requirement it serves and the entity it reads or writes.
[pause: 1.8]

[slide: v-045]
[pause: 1.0]
C: Pay. The client sends an idempotency key in a header, and a body with the merchant, the amount and a token for the card. The amount is an integer in minor units with its currency: one thousand and fifty cents, never ten point five as a float. The card number never reaches us: a token does.
C: The response is the payment I-D and a status, and the status can honestly be pending. The same key with a different body is rejected with a four twenty-two. The same key while the first is still in flight gets a four-oh-nine: retry later.
[pause: 1.0]

[slide: v-046]
[pause: 1.3]
C: Behind that status is an explicit state machine. Created, then auth pending when we send it. From there, authorised or declined, or the red one: unknown, on a timeout or an ambiguous answer. Unknown has exactly two exits: the inquiry says approved, or the processor says not found after its safe window.
C: Then captured, settled when the file matches, partially refunded, refunded, and chargeback. Any transition not drawn here is rejected by the code. A capture on a declined payment is not a bug to handle later: it cannot happen.
[pause: 1.1]

[slide: v-047]
[pause: 1.0]
C: Capture, void and refund are separate calls, each with its own idempotency key. Each one creates a new journal transaction that references the payment. Nothing is edited.
C: The refund limit is enforced by one conditional update on the payment row: add the amount only if the total stays within what was captured. Zero rows updated means the refund is refused. That one statement will matter in challenge five.
[pause: 1.0]

[slide: v-048]
[pause: 1.0]
C: Notify. Every state change becomes a signed webhook with an event I-D. It is retried with backoff, for days if necessary, so a merchant may see the same event twice and de-duplicates by event I-D.
C: And the backstop: a get on the payment always returns the state from our database. A merchant who missed every webhook can still find out.
[pause: 1.0]

[slide: v-049]
[pause: 1.0]
C: Three internal calls. Inquire asks a processor about our own reference for one attempt: payment I-D, slash, attempt number. Import settlement stores the processor's file unchanged before anything reads it. And breaks are listed by status and age.
C: A balance comes from the projection, and says which entry it is current to. For an audit, the answer is the sum over entries for the period, joined to their transactions and payments.
[pause: 1.0]

[slide: v-050]
[pause: 1.3]
C: The conceptual model. A payment has attempts: one per call to a processor, each with our reference. A payment posts journal transactions. A transaction contains entries, at least two, and each entry is on one account. A balance is a derived attribute of an account: the sum of its entries.
C: A break, from reconciliation, may explain one transaction. The double borders are weak entities: an attempt only exists inside its payment, and an entry only inside its transaction.
[pause: 1.1]

[slide: v-051]
[pause: 1.3]
C: The physical model. Journal entries are partitioned by account and only ever inserted. Journal transactions carry the payment and the type, and a check at commit that debits equal credits per currency. The payment row is the only mutable row, and it is changed only by conditional updates.
C: Idempotency keys with their request hash and stored response, kept seven days. The outbox, written in the same transaction as the state. And a balance projection that can be rebuilt from the entries at any time.
[pause: 1.1]

[slide: v-052]
[pause: 1.3]
C: A worked example. A capture of one thousand and fifty, with a fee of thirty. The processor receivable is debited one thousand and fifty: the processor owes us that. The merchant payable is credited one thousand and twenty: we owe the merchant that. And fee revenue is credited thirty. Debits, one thousand and fifty. Credits, one thousand and fifty. Balanced.
C: A refund is a new transaction that mirrors these lines. Nothing in this one ever changes.
[pause: 1.1]

[slide: v-053]
[pause: 0.6]
C: Three rules about amounts, because they are cheap to state and expensive to forget. Never a float: in binary floating point, point one plus point two is not point three, and the error ends up in someone's balance. A currency on every amount. And conversion, if it ever happens, is its own transaction, with the rate it used, versioned.
[pause: 0.8]

[pause: 1.4]

## 5 High-level design

[slide: v-054]
[pause: 1.2]
C: Now the design, in three versions. Each version is introduced by the objection to the one before. The boxes never move: every later picture is a view of the same baseline.
[pause: 1.8]

[slide: v-055]
[pause: 1.3]
C: Version one. The merchant calls the payments A-P-I. The payment service charges the card at the processor, synchronously. When the answer comes back, it updates the payment's status and the merchant's balance column in one transaction, and answers. It is the simplest thing that works, and many first versions look exactly like this.
[pause: 1.1]

[slide: v-056]
[pause: 1.0]
C: The objection, as a trace. At ten o'clock the payment goes to the processor. At one point nine seconds, no answer, so version one marks it failed. At two point four seconds the processor approves it anyway. At five seconds the checkout retries as a new payment, which is approved. The customer now has two holds.
C: And next month an auditor asks why a balance is what it is, and the answer is a number that was updated in place. There is no history to show.
[pause: 1.0]

[slide: v-057]
[pause: 1.3]
C: Version two. The A-P-I inserts the idempotency key first. The payment service commits the payment as auth pending, with an attempt and our reference, before it calls out. A new adapter calls the processor with that reference. And the database now holds a journal: balanced, immutable entries, with balances as a projection.
C: A timeout now moves the payment to unknown instead of failed, and a retry with the same key gets the same answer instead of a new payment.
[pause: 1.1]

[slide: v-058]
[pause: 1.0]
C: The heart of version two is this one transaction. Move the state from auth pending to captured, and only along a legal edge. Insert the journal transaction and its three entries. Insert the outbox row. Mark the idempotency key done, with the response. Commit, and a deferred check rejects the whole thing unless debits equal credits.
C: All or nothing. There is never a moment where the state says captured and the books do not.
[pause: 1.0]

[slide: v-059]
[pause: 0.6]
C: The objection to version two. Inside the database it is correct. But merchants hear about a change through a second write after the commit, so a crash in between means they never hear. Nothing ends an unknown: ten a second at peak, pending forever. And our books can still disagree with the processor's, and nothing would notice.
[pause: 0.8]

[slide: v-060]
[pause: 1.3]
C: Version three closes those loops. From the database, an outbox relay feeds an event log, and a webhook sender posts signed events to the merchant. An inquiry job reads unknown payments, asks the adapter by reference, and resolves them in the database. And reconciliation takes the processor's settlement file, compares it with expectations from the ledger, and hands breaks to finance operations.
C: This is the baseline. It stays on screen, and every picture from here on is a view of it.
[pause: 1.1]

[slide: v-061]
[pause: 1.0]
C: The pay path in code. Insert or read the idempotency key; if it already exists, return the stored response or say in progress. Commit the payment as auth pending with attempt one: evidence first. Call the adapter with our reference and a deadline of one point nine seconds. On a timeout, commit unknown and answer pending: the inquiry job takes over. Otherwise one transaction: state, entries, outbox, key done.
C: No branch guesses. A crash at any line leaves a row that says how far we got.
[pause: 1.0]

[slide: v-062]
[pause: 0.6]
C: What version three leaves open. It has every mechanism from the theory chapter. It has not yet been tested against a real timeout, three retries at once, a crash in the middle, a hot merchant, late refunds, a statement that disagrees, a bad release, or a silent drop in approvals. Those are the eight challenges, after the flows.
[pause: 0.8]

[slide: v-063]
[pause: 1.3]
C: Requirement one, pay, by the numbers. One: the merchant posts the payment with its key. Two: the A-P-I hands it to the payment service. Three: one transaction inserts the key and commits the payment as auth pending, with its attempt. Four: the service asks the adapter to authorise. Five: the adapter calls the processor with our reference.
C: Six: approved comes back. The service then commits the second transaction: the state, the entries, the outbox row and the key marked done. Seven: the status goes back to the A-P-I. Eight: the merchant gets its answer.
[pause: 1.1]

[slide: v-064]
[pause: 1.3]
C: Requirement two, a refund. One and two: the merchant's refund call, with its own key, reaches the service. Three: the conditional update on the payment row, which refuses anything that would exceed the captured amount. Four and five: the refund goes to the processor with a reference made from the payment and the refund key. Six: the result comes back, and a new journal transaction is posted, dated now, referencing the payment.
[pause: 1.1]

[slide: v-065]
[pause: 1.3]
C: Requirement three, notify. One: the outbox row is committed in the same transaction as the state. Two: the relay reads committed rows and publishes them to the event log. Three: the webhook sender reads the log. Four: it signs and posts to the merchant, retrying with backoff. The merchant de-duplicates by event I-D, and can always fall back to asking for the payment.
[pause: 1.1]

[slide: v-066]
[pause: 1.3]
C: Requirement four, reconcile. One: the processor's settlement file arrives and is stored unchanged. Two: the reconciliation job asks the ledger for the day's expectations, by reference and net of fees, and matches line by line. Matches move payments to settled, with settlement entries. Three: every line that does not match becomes a break, with an owner, in front of finance operations.
[pause: 1.1]

[slide: v-067]
[pause: 1.3]
C: Requirement five, explain. One and two: a balance request reaches the service. Three: it reads the projection, which says the entry it is current to. Four and five: the answer goes back. For an audit, the same path sums the entries for the period and joins them to their transactions and payments: every number explained by the records that produced it.
[pause: 1.1]

[slide: v-068]
[pause: 1.3]
C: The C4 context. A customer pays at a merchant. The merchant's system creates payments and receives webhooks. Our payments and ledger system authorises, captures and inquires at the processor, and receives its settlement files every day. And finance operations owns breaks and corrections. Notice that two of the four neighbours keep their own books of the same money.
[pause: 1.1]

[slide: v-069]
[pause: 1.3]
C: The containers. The payments A-P-I owns keys and the deadline. The payment service owns the state machine and the postings. The database holds payments, the journal and the outbox, partitioned by account. The adapter owns references and the processor's error codes. Below: the outbox relay and log, the webhook sender, the inquiry job, and the reconciliation pipeline, which writes expectations and adjustments back into the ledger.
[pause: 1.1]

[slide: v-070]
[pause: 1.3]
C: The same payment as a sequence. One: the merchant posts with key k-ninety-one. Two: the A-P-I inserts the key as processing, commits the payment as auth pending, and the attempt with reference p-seventy-seven thirty-one slash one. Three and four: authorise, through the adapter, with that reference. Approved in three hundred and forty milliseconds. Five, highlighted: the one transaction. Then two-oh-one, captured.
[pause: 1.1]

[pause: 1.4]

## 6 Bridge

[slide: v-071]
[pause: 1.2]
V: It works. The question now is where it breaks first.
[pause: 1.8]

[slide: v-072]
[pause: 1.3]
C: The baseline with its attack points marked. The adapter, where a call can time out. The A-P-I, where retries arrive together. The service and the database, where a crash can split a commit from its event, where a hot merchant queues, and where refunds race. Reconciliation, where the outside world disagrees. And then a bad release, and silence. Eight challenges, in an order where each fix creates the next question.
[pause: 1.1]

[pause: 1.4]

## 7 Challenges

[slide: v-073]
[pause: 1.2]
C: Each challenge runs the same way: the question, the naive answer, a case with numbers, where it breaks, the fix and why it works, then the interviewer pushes on the fix itself, and I say what I'd say in the room.
[pause: 1.8]

[pause: 1.4]

## 7.1 Challenge 1: The bank timed out

[slide: v-074]
[pause: 1.2]
N: Challenge one, the crux. The processor does not answer, and we do not know whether the customer paid.
[pause: 1.8]

[slide: v-075]
[pause: 0.6]
I: You call the processor. It times out. You don't know whether the customer was charged. Walk me through the next ten minutes, and the next ten days.
[pause: 2.0]

[slide: v-076]
[pause: 1.3]
C: The naive answers: mark it failed and let the client retry, or retry it ourselves until it works. Look at the red arrows between the adapter and the processor. A timeout is not an answer. It means the request may or may not have arrived, and may or may not have been approved. Either guess is wrong some of the time.
[pause: 1.1]

[slide: v-077]
[pause: 1.0]
C: The trace. The attempt is sent at ten o'clock. At one point nine seconds, the client deadline, there is no answer, and the naive design marks it failed. Half a second later the processor approves it. At five seconds the checkout retries, as a new payment, which is approved. Two holds on one card for one purchase.
C: Illustrative numbers, but the shape is real: approvals do arrive after deadlines.
[pause: 1.0]

[slide: v-078]
[pause: 1.3]
C: The fix. The attempt was committed before the call, with our reference. At the deadline the payment moves to unknown, and the client gets pending. The merchant's retry, with the same idempotency key, gets the same pending, not a new payment. Then the new green box: the inquiry job asks the processor about our reference after five seconds, thirty seconds, two minutes.
[pause: 1.1]

[slide: v-079]
[pause: 1.3]
C: As a sequence. One: authorise, with reference p-seventy-seven thirty-one slash one. The deadline passes. Two: the payment becomes unknown, and pending is the answer, to this request and to any retry with the same key. Three: the inquiry asks for the status of that reference. Approved at two point four seconds. Four: the job moves it to authorised, posts the entries and the outbox event.
C: The two other exits, in the notes. Not found after the processor's safe window: declined, and now a new attempt is safe. An approval we no longer want: a reversal by the same reference.
[pause: 1.1]

[slide: v-080]
[pause: 1.0]
C: And the next ten days. If the inquiry never got an answer, the settlement file is the final arbiter: a capture we did not record shows up there, becomes a break, and is fixed with an adjusting transaction and a message to the merchant. So no path creates a second movement for one intent, and no unknown can outlive the next settlement file.
[pause: 1.0]

[slide: v-081]
[pause: 0.6]
I: The processor's inquiry endpoint is down too. Actually, the whole processor is down for an hour.
[pause: 2.0]

[slide: v-082]
[pause: 0.6]
C: A circuit breaker per processor stops new attempts going to one that is down, and new payments go to a second processor, if the contracts allow it. But never an unknown. An unknown sent to a second processor is two possible charges. Unknowns wait, age, and show on a dashboard, and the merchant sees pending.
C: The honest limit: a processor that supports neither inquiry nor idempotent references can only be resolved by the settlement file, a day late. That is a reason to choose processors, and I'd say so to whoever negotiates the contracts.
[pause: 0.8]

[slide: v-083]
[pause: 0.7]
V: If asked, I'd say: a timeout is an unknown, not a failure. I commit the attempt before calling out, move the payment to unknown, answer pending, and an inquiry job asks the processor by our own reference until it knows. Retries carry the same reference, so they can't become a second charge, and the settlement file is the final arbiter.
[pause: 1.0]
N: That fix leans on retries being harmless. Are they?
[pause: 1.6]

[pause: 1.4]

## 7.2 Challenge 2: Three retries at once

[slide: v-084]
[pause: 1.2]
N: Challenge two. The same payment arrives three times in three milliseconds: how does only one of them count?
[pause: 1.8]

[slide: v-085]
[pause: 0.6]
I: The client sends the same payment three times, concurrently, with the same idempotency key. Then once more, same key, different amount. What happens?
[pause: 2.0]

[slide: v-086]
[pause: 1.3]
C: The naive answer: check whether the key exists before processing. Look at the A-P-I box. Three requests land on three servers, and each one checks, finds nothing, and charges. A check followed by an act is a race, however fast the check is.
[pause: 1.1]

[slide: v-087]
[pause: 1.0]
C: The trace. Three requests with key k-ninety-one, one millisecond apart, on servers A, B and C. Each selects, each finds nothing, and three authorisations go out.
C: Five minutes later a fourth request arrives with the same key and a different amount. Returning the stored answer would hide the client's bug. Executing it would charge again. Neither is right.
[pause: 1.0]

[slide: v-088]
[pause: 1.3]
C: The fix: insert the key first, unique per client, with a hash of the request, in the same transaction that creates the payment. Only one insert can win. The others fail the constraint and read the row. If it says processing, they get a four-oh-nine, retry later. If it says done, they get the stored response. And if the hash differs, a four twenty-two: nothing executes.
[pause: 1.1]

[slide: v-089]
[pause: 1.3]
C: As a sequence. Request one and request two arrive two milliseconds apart. Request one's insert succeeds: processing, with payment p-seventy-seven thirty-one. Request two's insert hits the unique violation, highlighted, and reads the row: processing, hash h-one. So it gets four-oh-nine. Later the same request again finds done and the same hash, and gets the stored response. And the changed amount has a different hash: four twenty-two.
[pause: 1.1]

[slide: v-090]
[pause: 1.0]
C: In code. Inside one transaction, try to insert the key as processing and create the payment. On a unique violation, read the row. A different hash is a reused key: four twenty-two. Processing: four-oh-nine. Otherwise return the stored response. The result is returned, never re-executed, and a changed request under an old key is reported, not hidden.
[pause: 1.0]

[slide: v-091]
[pause: 0.6]
I: The server that won crashes after the processor approved, but before it wrote done.
[pause: 2.0]

[slide: v-092]
[pause: 0.6]
C: Then the rows say exactly how far it got. The key says processing, with the payment I-D. The payment says auth pending, with the attempt's reference. That is an unknown outcome, and challenge one already handles it: a sweeper sends any processing row older than a minute to the inquiry.
C: One more contract term: keys live seven days. A retry after that is a new payment, and the A-P-I documentation says so.
[pause: 0.8]

[slide: v-093]
[pause: 0.7]
V: If asked, I'd say: the idempotency key is inserted first, with a unique constraint, in the same transaction that creates the payment. One request wins; the others get in progress or the stored answer. A different body under the same key is a client bug, so I reject it instead of hiding it. And a crash in the middle is just an unknown outcome, which I already handle.
[pause: 1.0]
N: Inside the database it is now safe. What about everything outside it?
[pause: 1.6]

[pause: 1.4]

## 7.3 Challenge 3: A crash between the ledger and the event

[slide: v-094]
[pause: 1.2]
N: Challenge three. The payment is committed, and the process dies before anyone is told.
[pause: 1.8]

[slide: v-095]
[pause: 0.6]
I: Your service commits the payment, then crashes before telling the merchant. What state are you in?
[pause: 2.0]

[slide: v-096]
[pause: 1.3]
C: The naive answer: publish the event right after the commit, crashes are rare. Look at the red arrow from the service straight to the event log. That is a second write, to a second system, with no shared transaction. Whichever order you choose, a crash between them loses something.
[pause: 1.1]

[slide: v-097]
[pause: 1.0]
C: The trace. The capture commits. Two milliseconds later a deploy kills the process, and no event is sent. The merchant's order system waits, and nothing ships: the customer has paid for nothing. Reverse the order, publish first and then commit, and a failed commit ships goods for an unpaid order. Rare is not the same as never, at ten thousand a second.
[pause: 1.0]

[slide: v-098]
[pause: 1.3]
C: The fix is the outbox, now outlined green. The event is a row written in the same transaction as the state and the entries. A relay reads committed rows, in order, and publishes them to the log, at least once. From there the webhook sender takes over. The event exists if and only if the state committed, and delivery is retried until it is acknowledged.
[pause: 1.1]

[slide: v-099]
[pause: 1.3]
C: As a sequence. One: begin, captured, entries, outbox row e-five-five-one, commit. The process is killed right there: nothing is lost, the row is committed. Two: the relay reads committed rows. Three: it publishes e-five-five-one. Four: the webhook goes to the merchant, signed and retried. If the merchant receives it twice, it has already seen that event I-D and ignores the second.
[pause: 1.1]

[slide: v-100]
[pause: 0.6]
I: The relay is twenty minutes behind. Or a merchant's endpoint is down for a day.
[pause: 2.0]

[slide: v-101]
[pause: 0.6]
C: Outbox age is a metric with an alert, so twenty minutes behind pages someone. The relay is partitioned by account, so one slow partition does not hold up the rest. And for the merchant who is down for a day: webhooks retry with backoff for days, then the merchant is told to reconcile with a get, and their dashboard reads our database, not the event stream.
[pause: 0.8]

[slide: v-102]
[pause: 0.7]
V: If asked, I'd say: I never write to two systems and hope. The event is a row in the same transaction as the state change, and a relay publishes it at least once. Consumers de-duplicate by event I-D, and the merchant can always ask us for the state directly.
[pause: 1.0]
N: One transaction per payment works. Until a thousand of them want the same row.
[pause: 1.6]

[pause: 1.4]

## 7.4 Challenge 4: The hot merchant

[slide: v-103]
[pause: 1.2]
N: Challenge four. One merchant receives five thousand payments a second, and they all touch one account.
[pause: 1.8]

[slide: v-104]
[pause: 0.6]
I: One merchant receives five thousand payments a second. Where does that land?
[pause: 2.0]

[slide: v-105]
[pause: 1.3]
C: The naive answer: update the merchant's balance inside each payment's transaction. Look at the database, dashed red. Every one of those transactions takes the same row lock, so they run one after another.
[pause: 1.1]

[slide: v-106]
[pause: 1.0]
C: The trace. Five thousand a second, each holding the balance row for about one and a half milliseconds: the row allows about six hundred and seventy a second. The queue grows by more than four thousand a second, the merchant's latency passes two seconds within a second, and its payments start timing out. They become unknowns: this challenge feeds challenge one.
C: The lock time is illustrative and must be measured. The ratio is the point.
[pause: 1.0]

[slide: v-107]
[pause: 1.3]
C: The fix. Payments only insert their own entries, and nothing shared is updated, so there is no lock to queue on. A projection updates the balance a few seconds behind, which is fine for a dashboard. Where a check needs the balance right now, a payout must not exceed available funds, the green box: the account is split into sixteen sub-accounts that take writes in turn and are summed, or the rare payout goes through one writer per merchant.
[pause: 1.1]

[slide: v-108]
[pause: 1.3]
C: Why sixteen. Each sub-account row allows about six hundred and seventy a second, so sixteen allow about ten thousand seven hundred: twice this merchant's peak. And with append-only entries there is no shared row at all on the payment path. The sub-accounts are only for the operations that must read a current balance.
[pause: 1.1]

[slide: v-109]
[pause: 0.6]
I: A refund needs refunded to be at most captured, per payment. A payout needs paid out to be at most available, right now.
[pause: 2.0]

[slide: v-110]
[pause: 0.6]
C: Per payment, the check is a conditional update on that payment's row, and one payment is never hot. Per merchant, the payout check goes through a single payout writer, which reads the sum of the sub-accounts and then posts the payout. Payouts are rare next to payments, so serialising them costs nothing.
C: The honest limit: the projection lag must be measured and stated to the team that owns payouts.
[pause: 0.8]

[slide: v-111]
[pause: 0.7]
V: If asked, I'd say: five thousand updates a second to one balance row would serialise on its lock. So payments only append entries and the balance is derived. Where a check needs the balance now, like a payout, I split the account into sub-accounts or serialise just that rare operation through one writer.
[pause: 1.0]
N: The refund check just appeared. Let's push on it.
[pause: 1.6]

[pause: 1.4]

## 7.5 Challenge 5: Refunds, and a chargeback months later

[slide: v-112]
[pause: 1.2]
N: Challenge five. Money comes back: twice at once, and then again three months later, into a month that is already closed.
[pause: 1.8]

[slide: v-113]
[pause: 0.6]
I: A payment was partially refunded twice. Two more refunds arrive at once. Then, three months later, a chargeback. How does the ledger stay right?
[pause: 2.0]

[slide: v-114]
[pause: 1.3]
C: The naive answer: update the payment's amount and the merchant's balance. Look at the database, dashed red. Two refunds that read before they write are the same race as challenge two. And a chargeback that edits the original record rewrites a month that has already been reported.
[pause: 1.1]

[slide: v-115]
[pause: 1.0]
C: The trace. A payment of ten thousand, refunds of three thousand and four thousand already done: seven thousand refunded. Two refunds of two thousand five hundred arrive two milliseconds apart. Each reads seven thousand, each checks that nine thousand five hundred is within ten thousand, and each passes. Twelve thousand refunded on a ten thousand payment.
C: Then on day ninety-two, a chargeback, for a month that is closed and already reported.
[pause: 1.0]

[slide: v-116]
[pause: 1.3]
C: The fix. Each adjustment is a new journal transaction that references the payment. The refund limit is one conditional update: add the amount only where the new total stays within captured. Exactly one of the two refunds updates a row; the other updates zero rows and is refused. The chargeback posts entries dated now, to a disputes account, and the closed month is never touched.
[pause: 1.1]

[slide: v-117]
[pause: 1.3]
C: As a sequence. Refunds r-one and r-two arrive two milliseconds apart. Three, highlighted: the conditional update for r-one changes one row. Four: the same for r-two changes zero rows, and r-two gets a four twenty-two. Five: the refund goes to the processor with reference p-fifty-five twenty slash r-one. Six: a new journal transaction, dated now. And on day ninety-two the chargeback is posted the same way.
[pause: 1.1]

[slide: v-118]
[pause: 0.6]
I: The merchant wins the dispute, so the chargeback is reversed. Or the refund is in a different currency.
[pause: 2.0]

[slide: v-119]
[pause: 0.6]
C: A won dispute is one more transaction, from the disputes account back to the merchant. A refund in another currency: the amounts stay in the original currency, and any conversion is its own transaction with the rate it used. The honest limit: who bears a loss in a dispute is decided by contracts, not by code, and finance owns those rules.
[pause: 0.8]

[slide: v-120]
[pause: 0.7]
V: If asked, I'd say: nothing is edited. A refund, a chargeback or a reversal is a new balanced transaction that references the payment and is dated when it happened, so closed months still add up. The refund limit is one conditional update on the payment row, so two concurrent refunds can't both pass.
[pause: 1.0]
N: Our books are now right by construction. Are they right compared with the processor's?
[pause: 1.6]

[pause: 1.4]

## 7.6 Challenge 6: 999,998 against 1,000,000

[slide: v-121]
[pause: 1.2]
N: Challenge six, the second half of the crux. The processor's books and ours disagree by two.
[pause: 1.8]

[slide: v-122]
[pause: 0.6]
I: The processor's settlement statement says nine hundred ninety-nine thousand nine hundred ninety-eight. Your books say one million. What now?
[pause: 2.0]

[slide: v-123]
[pause: 1.3]
C: The naive answer: we'd look into it, our system is correct by construction. Look at reconciliation, dashed red, and the settlement file arriving from the processor. Being correct inside our database is not the same as agreeing with the party that actually moved the money. And a difference in totals hides its causes.
[pause: 1.1]

[slide: v-124]
[pause: 1.0]
C: The case. Three differences. A capture we booked at two minutes to midnight that settles tomorrow: timing, it closes by itself. An unknown we resolved as declined, which the processor actually settled: a real break, the customer paid and we think they did not. And a fee two higher than the contract.
C: Net, minus two. The most important break, a real charge we think was declined, is invisible in the total. That is why reconciliation is never done on totals.
[pause: 1.0]

[slide: v-125]
[pause: 1.3]
C: The fix: reconciliation as a permanent component. The raw file is stored unchanged first. The ledger generates expectations: what each processor should settle, by reference, net of fees. The match is line by line. Every unmatched line becomes a break with a type, missing on their side, missing on ours, amount, or timing, plus an owner and an age, in front of finance operations.
[pause: 1.1]

[slide: v-126]
[pause: 1.3]
C: As a sequence. One: the file arrives, about two hundred ninety million lines, stored unchanged. Two: expectations for the day from the ledger. Then the match. Three: matched lines move payments to settled, with settlement entries. Four, highlighted: the break, settled by them and declined by us, one thousand and fifty, with an owner and age zero. Timing breaks close themselves when tomorrow's file matches.
[pause: 1.1]

[slide: v-127]
[pause: 0.6]
I: There are forty thousand breaks this morning, not forty.
[pause: 2.0]

[slide: v-128]
[pause: 0.6]
C: Forty thousand breaks is an incident, not a backlog. Classify first, by type and processor: one cause usually explains thousands of lines. Protect the money: hold payouts if the break amount crosses a threshold, because money not yet sent can still be protected. Fix the cause before the lines. And say it out loud: breaks by age is a dashboard with a target, and finance operations is a team that needs tooling.
[pause: 0.8]

[slide: v-129]
[pause: 0.7]
V: If asked, I'd say: reconciliation isn't a safety net for a buggy system. It's a permanent component, because the processor's truth and ours diverge even when our code is right. I match line by line against expectations from the ledger, every difference becomes a break with an owner and an age, and a spike in breaks is treated as an incident.
[pause: 1.0]
N: And when the cause of the spike is our own code?
[pause: 1.6]

[pause: 1.4]

## 7.7 Challenge 7: A bug double-posted forty thousand entries

[slide: v-130]
[pause: 1.2]
N: Challenge seven. Our own release wrote wrong entries overnight, and some of the money has already left.
[pause: 1.8]

[slide: v-131]
[pause: 0.6]
I: A bug double-posted forty thousand entries last night, and some merchants have already been paid out. What do you do?
[pause: 2.0]

[slide: v-132]
[pause: 1.3]
C: The naive answer: write a script to delete the duplicates. Look at the ledger, dashed red. A delete destroys the evidence of what happened, breaks the rule that history is never rewritten, and does nothing about the money that has already been paid out, because that money is no longer in our database.
[pause: 1.1]

[slide: v-133]
[pause: 1.0]
C: The trace. At ten past ten at night a release starts posting the fee leg twice. By twenty to midnight, forty thousand captures are affected, and twelve hundred merchants' payables are too high by the fee. At midnight the payouts run, and a hundred and eighty of them are paid the excess. At half past seven, reconciliation's fee breaks jump, and an incident is opened.
[pause: 1.0]

[slide: v-134]
[pause: 1.3]
C: The fix, in order. Stop the bleeding: switch the release off and hold payouts for the affected merchants. Identify: the journal is immutable, so the duplicates are exactly the payments with two fee transactions. Reverse: the correction tool, in green, posts one reversing transaction per duplicate, tagged with the incident. The audit trail now shows the error and its correction.
[pause: 1.1]

[slide: v-135]
[pause: 1.3]
C: As a sequence. One, highlighted: the kill switch. Two: hold payouts for the twelve hundred merchants. Three: find forty thousand duplicate rows. Four: post one reversing transaction each, tagged with the incident number. Five: the hundred and eighty already paid become a receivable, recovered from their future settlements. That last step is a business decision with a message to each merchant, not a database operation.
[pause: 1.1]

[slide: v-136]
[pause: 0.6]
I: Idempotency should have stopped this. Why didn't it?
[pause: 2.0]

[slide: v-137]
[pause: 0.6]
C: Because idempotency guards requests, not code paths. There was one request with one key. The bug posted twice inside it, with a new transaction I-D each time. The invariant that stops the whole class is a unique constraint on payment and type for types that may occur only once, like the fee. Plus an hourly check that would have caught it at eleven instead of half past seven. Then a postmortem on why tests and the canary let it through.
[pause: 0.8]

[slide: v-138]
[pause: 0.7]
V: If asked, I'd say: stop the bleeding first. Kill the release and hold payouts. Because the journal is immutable I can find the duplicates exactly and post reversing entries tagged with the incident, so the audit trail shows both. Money already paid out is a receivable and a conversation with those merchants. Then a constraint and an hourly check, so this class can't repeat silently.
[pause: 1.0]
N: An hourly check. Which raises the last question: what would have told us at all?
[pause: 1.6]

[pause: 1.4]

## 7.8 Challenge 8: How would you know before finance does?

[slide: v-139]
[pause: 1.2]
N: Challenge eight. Every dashboard is green, and merchants are losing sales.
[pause: 1.8]

[slide: v-140]
[pause: 0.6]
I: What do you watch, and what alert fires before finance notices that something is wrong?
[pause: 2.0]

[slide: v-141]
[pause: 1.3]
C: The naive answer: error rate and latency. Look at the adapter and the processor, dashed red. A decline is a successful A-P-I call: it returns quickly and without an error. So if approvals fall, nothing on a server dashboard moves.
[pause: 1.1]

[slide: v-142]
[pause: 1.0]
C: The trace. At two in the morning, a change on one processor's side declines six more percentage points of cards from one country. Errors: zero. Latency: normal. Every check green. At nine, merchants report that sales are down. The first alert is a customer.
[pause: 1.0]

[slide: v-143]
[pause: 1.3]
C: The fix: service level indicators on the money. Approval rate per processor, per country, per card type, against its own baseline. Unknown count and age. Outbox age. Debits minus credits equal to zero, checked continuously, and any non-zero value pages immediately. Unreconciled amount by age. And the green probe: a synthetic payment with a test card through each processor every minute.
[pause: 1.1]

[slide: v-144]
[pause: 1.3]
C: The probe as a sequence. One: a synthetic payment with a test card. Two: authorised through the real path, with a reference. Captured in four hundred and ten milliseconds. Three: success and latency per processor go to monitoring. In red, the alert that would have fired at two in the morning: approval rate for one processor and country, six points under its baseline. In green, the ledger check: debits minus credits is zero.
[pause: 1.1]

[slide: v-145]
[pause: 1.0]
C: Then read them in pairs. Approvals down with latency normal: a processor or issuer change, not us. Unknowns up with latency at the timeout: the processor is slow. Outbox age up with commits normal: the relay is stuck. Breaks up today after unknowns rose yesterday: the inquiry is not resolving. And a ledger that does not sum to zero: stop and page, whatever else is true.
N: Pairs like these are what an on-call runbook for payments failing at three in the morning starts from.
[pause: 1.0]

[slide: v-146]
[pause: 0.6]
I: The approval rate drops slowly. Half a point a week.
[pause: 2.0]

[slide: v-147]
[pause: 0.6]
C: A slow drift needs a slow comparison: weekly, per segment, against a seasonal baseline, because half a point a week is invisible minute by minute. And the approval rate needs an owner, in payments operations, who reviews it with the processor every week. A metric with no owner is a decoration.
[pause: 0.8]

[slide: v-148]
[pause: 0.7]
V: If asked, I'd say: I watch the money, not the servers. Approval rate per processor and segment against its baseline, the count and age of unknown outcomes, outbox age, unreconciled amount by age, and a continuous check that the ledger sums to zero, which pages immediately. Then I read metrics in pairs to tell the processor changed from we broke.
[pause: 1.6]

[pause: 1.4]

## 8 Build cost

[slide: v-149]
[pause: 1.2]
N: This chapter is marked auxiliary. It is the engineering-manager layer, optional in a Staff round.
C: Payments are not one project. They are three releases, and the first one should mostly be bought.
[pause: 1.8]

[slide: v-150]
[pause: 1.0]
C: Version one is bought: a processor with its hosted payment page and token vault, so card numbers never touch us. Three engineers for a quarter. Version two is built: idempotency, the state machine, the journal. Five or six engineers for two quarters. Version three is run: outbox, inquiry, reconciliation and a second processor. Two teams for two or three quarters, plus a finance operations function. All illustrative.
[pause: 1.0]

[slide: v-151]
[pause: 0.6]
C: Two decisions are one-way doors. The ledger schema: seven years of records and every auditor depend on it. And the idempotency contract: every merchant integration has encoded it, so changing it breaks clients we do not control. Those get the most review. Everything else can change in a quarter.
[pause: 0.8]

[slide: v-152]
[pause: 1.0]
C: Four team seams. Payments A-P-I and state machine. The ledger, owned centrally, with a posting interface, and it reviews every new transaction type, because everyone touches it. Processor integrations, one adapter per processor behind one internal interface. And reconciliation and finance tooling, whose contract is the break types and their ageing targets.
[pause: 1.0]

[slide: v-153]
[pause: 0.6]
C: Three risks. An unknown path that is never tested, because it runs rarely: inject timeouts in staging every day. Reconciliation built last, so the first months of breaks are found by hand. And a second processor added without its own inquiry semantics, whose unknowns can only be resolved a day late.
[pause: 0.8]

[slide: v-154]
[pause: 1.0]
C: Cost. The infrastructure is real: a journal that grows to hundreds of terabytes. But processor fees dwarf it. So the engineering levers on cost are routing between processors and reducing false declines, each worth basis points on the whole volume.
[pause: 1.0]

[pause: 1.4]

## 9 Recap

[slide: v-155]
[pause: 1.2]
C: To close: one picture, one sentence per path, the mistakes to avoid, and the thesis.
[pause: 1.8]

[slide: v-156]
[pause: 1.3]
C: The whole design on one baseline. The key inserted first, in front of the A-P-I. The state machine with unknown in the payment service. The journal, the outbox and sub-accounts in the database. The inquiry job beside the adapter. Reconciliation and finance operations on the right. The correction tool, and probes that watch the money.
[pause: 1.1]

[slide: v-157]
[pause: 1.0]
C: One sentence per path. Pay: key first, attempt committed, call by reference, one transaction for state, entries and event. Adjust: a new transaction, dated now, with the limit in one conditional update. Notify: an outbox row, published at least once. Reconcile: expectations, matched line by line, every break owned. Explain: a sum over immutable entries.
[pause: 1.0]

[slide: v-158]
[pause: 0.6]
C: The common mistakes. On correctness: a distributed transaction with the bank, a balance column as the truth, a timeout treated as a failure, floats, keys that are checked instead of inserted, and a changed retry silently accepted. On operations: events published outside the transaction, history edited, no reconciliation or reconciliation by totals, no owner for breaks, and dashboards with no money on them.
[pause: 0.8]

[slide: v-159]
[pause: 0.6]
C: If I had thirty seconds: what it is, a state machine per payment, an idempotent A-P-I, an immutable double-entry journal and reconciliation. The trade: pending answers and a reconciliation team, in exchange for never guessing. The risk: the unknown path runs rarely, so I'd test it every day. Next: harden the inquiry per processor, and make breaks an owned, aged workflow.
[pause: 0.8]

[slide: v-160]
[pause: 0.7]
V: I can't get exactly-once across the boundary, so I get one effect per intent: a key inserted first, a reference on every call, a state for not knowing, and an inquiry that ends it. Every movement is a balanced, immutable entry, so any balance is a sum I can explain. And because the outside world's books will disagree with mine anyway, reconciliation is part of the design, with owners.
[pause: 1.6]
