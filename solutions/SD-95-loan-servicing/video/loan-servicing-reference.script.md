# SD-95 Instalment loan servicing: ledger and collections scheduler: reference solution (Staff L6/L7)

<!-- Video script for slide-video-kit/scripts/build_video.py. [slide: v-NNN] = frames/v-NNN.png, the number printed on every slide.
     Speakers: C candidate · I interviewer · V key line (slower) · N coach. Generated from src/*.py: edit the sources, not this file. -->
<!-- voices: N=af_heart@0.92 I=bf_emma@0.95 C=am_michael@0.9 V=am_michael@0.84 -->
<!-- labels: N=COACH -->
<!-- say: API=A-P-I APIs=A-P-Is SLO=S-L-O SLOs=S-L-Os SLI=S-L-I SLIs=S-L-Is HTTP=H-T-T-P SQL=S-Q-L ID=I-D IDs=I-Ds EM=E-M AUX=aux SRE=S-R-E UUID=U-U-I-D ACH=A-C-H NSF=N-S-F BNPL=B-N-P-L APR=A-P-R TB=terabytes GB=gigabytes MB=megabytes KB=kilobytes UNKNOWN=unknown RETURNED=returned SETTLED=settled PENDING=pending PAID_PENDING=paid-pending SFTP=S-F-T-P -->


## 0 Cold open

[slide: v-001]
[pause: 1.2]
C: Six hundred thousand repayments are due on the first of the month. Most people hear that and reach for a message broker, because it sounds like a thundering herd. It isn't. It is about forty a second, and any database absorbs that. This question is hard somewhere else entirely: in money that moves in days, and can come back weeks after everyone thought it was done.
[pause: 1.8]

[slide: v-002]
[pause: 0.6]
I: Loans are created elsewhere. Design the system that services them for their whole life. It schedules repayments, collects them by bank debit or card, handles refunds, late fees and early payoff, and reconciles with the bank.
[pause: 1.5]

[slide: v-003]
[pause: 1.3]
C: Here is the hook as a timeline. A card charge answers in seconds, or not at all. A bank debit settles in a day or two, and the dashboard calls it settled. But a debit can come back for insufficient funds two banking days later, and as unauthorised up to sixty days later. Merchants refund months into a loan. And every cent has to be explained for seven years.
C: So the design is not about speed. It is about being correct over months, while the truth about each payment keeps arriving. I'll put one mechanism at each point on this line.
[pause: 1.1]

[slide: v-004]
[pause: 1.0]
N: Five axes. The weak answer is a cron job, a balance column and a retry loop. The strong answer names where the real limits are, and treats unknown and returned as ordinary states.
C: I'll keep one sentence in front of everything: settled is not final for a bank debit. Most of the design follows from taking that seriously.
[pause: 1.0]

[slide: v-005]
[pause: 0.7]
V: In loan servicing, throughput is never the problem; correctness over months is. So the design is an immutable double-entry ledger, a payment state machine that admits unknown and returned, a scheduler bounded by the rail, and a daily three-way reconciliation.
[pause: 1.0]
C: Concretely: ledger lines that are never edited, with balances as a projection. Idempotency keys at three layers. A day planned backwards from the bank's cut-off. And every morning, a check that our books agree with the processor's and the bank's, with an owner for every difference.
[pause: 1.6]

[slide: v-006]
[pause: 0.6]
C: The order. Requirements and scope, then the numbers, then a short theory chapter the design can lean on. Then the A-P-I and the data model, and a design in three versions, each one answering the objection to the one before.
C: Most of the time goes to eight challenges that break the design, in an order where each fix creates the next question. Then a build cost, and a recap.
[pause: 0.8]

[pause: 1.4]

## 1 Requirements and scope

[slide: v-007]
[pause: 1.2]
C: Before I draw anything, seven questions. Each answer changes the design, and I'll say how.
[pause: 1.8]

[slide: v-008]
[pause: 0.6]
C: How big is the portfolio?
I: Five million active loans, with three to twelve monthly instalments each.
C: So about five million collections a month, and each loan lives up to a year. Long enough for every slow failure in this domain to happen.
[pause: 0.6]

[slide: v-009]
[pause: 0.6]
C: Which payment rails do we collect on?
I: Bank debit for eighty percent, card for twenty. Card numbers are stored as tokens at the processor.
C: Two rails that behave very differently. A card answers in seconds. A bank debit answers in days and can be returned weeks later. And because the tokens live at the processor, I can't move card customers to another processor in a hurry. That will matter on the worst day.
[pause: 0.6]

[slide: v-010]
[pause: 0.6]
C: Are due dates spread across the month?
I: No. They cluster. Six hundred thousand collections fall on the first.
C: Then I need to plan one day very carefully. I'll size it in a minute, and I suspect it is smaller than it sounds.
[pause: 0.6]

[slide: v-011]
[pause: 0.6]
C: What limits do the rails put on us?
I: The card processor's contract allows a hundred requests a second. Bank debit files have a daily cut-off. Take two in the afternoon.
C: That is the most important answer so far. The limit is not my database. It is a contract, and a clock on the bank's side.
[pause: 0.6]

[slide: v-012]
[pause: 0.6]
C: How do refunds work?
I: Merchants refund in full or in part, at any point during the loan.
C: So a refund changes a schedule under a live loan, possibly while a payment is in flight. The terms have to say what happens.
[pause: 0.6]

[slide: v-013]
[pause: 0.6]
C: What are the audit requirements?
I: Every cent explained for seven years, and the month-end close done in two days.
C: Explained means a balance is a sum of records nobody edits. And a two-day close means differences have to be found daily, not at the end of the month.
[pause: 0.6]

[slide: v-014]
[pause: 0.6]
C: What must never happen, in priority order? I'd propose: first, charging a customer twice for one instalment. Second, a cent we can't explain. Third, penalising a customer for our own failure. Lateness comes after all three.
I: Your call. I agree with that order.
C: That order settles arguments later. When speed and correctness conflict, correctness wins, and a collection can wait a day.
[pause: 0.6]

[slide: v-015]
[pause: 0.6]
C: Functionally, five things. One, schedule: a booked loan becomes a schedule of instalments, from a versioned set of terms. Two, collect: on each due date, by bank debit or card, with retries and late fees as policy says. Three, adjust: refunds, extra payments and early payoff, which re-amortise the loan or shorten it, as the terms say.
C: Four, absorb returns: a debit that comes back days or weeks later reverses a collection. Five, reconcile: our ledger against the processor and the bank, every day. Each of these gets a numbered flow later.
[pause: 0.8]

[slide: v-016]
[pause: 0.6]
C: The promises, all initial targets. Zero customers charged twice for one instalment. Zero unexplained differences at month-end. The day's debit file submitted by half past ten, with the cut-off at two, so a failed submission still has time to be fixed. Ninety-nine percent of unknown outcomes resolved within an hour. And every ledger line kept, and explainable, for seven years.
[pause: 0.8]

[slide: v-017]
[pause: 0.6]
C: In scope: schedules, both rails with their retries and returns, refunds, late fees, early payoff, the ledger, reconciliation, and notices to customers as events.
C: Out of scope, said aloud. Origination and underwriting, which is its own question. Outside collections agencies, and hardship programmes beyond a simple pause flag. Statement design and tax reporting. Paying merchants. And how the loans are funded or sold. Each of those consumes our events, but none of them changes the core.
[pause: 0.8]

[slide: v-018]
[pause: 0.7]
C: So the core is four things. A ledger that is never edited. A payment state machine with unknown and returned in it. A scheduler whose limit is the rail. And reconciliation against the outside world. Everything else serves those four.
[pause: 1.6]

[pause: 1.4]

## 2 Estimates

[slide: v-019]
[pause: 1.2]
C: Numbers next. Each is arithmetic from what the interviewer said, carries a label, and ends with the decision it drives. I'll say it once for the chapter: the rates and amounts are illustrative, not any company's figures.
[pause: 1.8]

[slide: v-020]
[pause: 1.0]
C: Six hundred thousand collections, spread over four hours: six hundred thousand divided by fourteen thousand four hundred seconds. About forty-two a second.
C: Decision: that is nothing for one relational database. The database can be the work queue, and a message broker is not needed for load. If I add one later, it is for another reason.
[pause: 1.0]

[slide: v-021]
[pause: 1.0]
C: Twenty percent of six hundred thousand is a hundred and twenty thousand card charges. At the contract's hundred a second, twenty minutes at the very least. I'd run at ninety a second, to leave headroom for retries and queries: about twenty-two minutes.
C: Decision: a token bucket per rail, set below the contract. The card window is something we plan, not a burst we hope survives.
[pause: 1.0]

[slide: v-022]
[pause: 1.0]
C: The other four hundred and eighty thousand are bank debits. They don't go one by one: they go in a file. At about ninety-four bytes a record, forty-five megabytes.
C: Decision: the file is a batch, built hours before the cut-off, validated, submitted, and only done when the bank acknowledges it. A missed cut-off moves half a million collections by a day.
[pause: 1.0]

[slide: v-023]
[pause: 1.0]
C: Money. Say the average instalment is a hundred and fifty dollars: a twelve-hundred dollar loan in eight payments. Six hundred thousand of them is about ninety million dollars on the first. A tenth of a percent wrong is ninety thousand dollars, and a lot of angry customers.
C: Decision: correctness beats speed. Being a day late is cheap. Being wrong is not.
[pause: 1.0]

[slide: v-024]
[pause: 1.0]
C: Returns. Say three percent of bank debits come back for insufficient funds. That is fourteen thousand four hundred returns from the first alone, arriving on the second and third days. Plus a trickle of unauthorised returns for sixty days after that.
C: Decision: returns are a daily workload with their own pipeline and owner, not an exception handler.
[pause: 1.0]

[slide: v-025]
[pause: 1.0]
C: Unknown outcomes. Say two in a thousand card charges time out. On the first that is about two hundred and forty. Small, but every one of them is a customer who might have been charged, and might be charged again if we guess.
C: Decision: a resolver service that ends every unknown by asking the processor, never by guessing.
[pause: 1.0]

[slide: v-026]
[pause: 1.0]
C: The ledger's size. About four lines per loan per month: two for the collection, two for the interest accrued at month-end. Five million loans: twenty million lines a month. Over eighty-four months, at two hundred bytes a line, about three hundred and forty gigabytes.
C: Decision: that fits one well-run relational database, partitioned by month. No sharding. I keep real transactions and real constraints, which is exactly what a ledger needs.
[pause: 1.0]

[slide: v-027]
[pause: 1.0]
C: One trap. Posting interest every day would be five million loans, times thirty days, times two lines: three hundred million lines a month. Fifteen times the ledger, for no information.
C: So interest is accrued by calculation, from the balance and the rate, and posted when something happens: a payment, a payoff, a refund, and month-end.
N: Noticing that, unprompted, is the kind of depth this round looks for.
C: That is the numbers. Next, theory.
[pause: 1.0]

[pause: 1.4]

## 3 Theory

[slide: v-028]
[pause: 1.2]
C: A short theory chapter before any design, so the design can lean on it. Six parts: what loan servicing is and is not, the properties, the central tension, seven mechanisms, an options matrix, and the failure catalogue. Every slide here carries a theory badge.
[pause: 1.8]

[slide: v-029]
[pause: 0.7]
V: A loan servicing system turns each loan's terms into a schedule, collects each amount once through rails that answer in days and can reverse weeks later, records every movement as balanced, immutable lines, and proves every day that its books agree with the bank.
[pause: 1.0]
C: Every clause does work. Terms into a schedule: the rules are versioned data, not code paths. Once: idempotency, not exactly-once delivery, which does not exist across a network. Answer in days and reverse weeks later: pending, unknown and returned are states. Balanced and immutable: double entry, corrections by reversal. And proves daily: reconciliation is a component, not an audit at year end.
[pause: 1.6]

[slide: v-030]
[pause: 0.6]
C: Four confusions. It is not a payment gateway: a gateway turns one intent into one payment in seconds. Servicing drives many payments over months, against a schedule that keeps changing. It is not a cron job: a cron job fires work, but it does not know what was attempted, what is pending, or what came back.
C: A ledger is not a balance table: a balance is a sum, and a number updated in place cannot explain itself. And settled is not final: a bank debit can be returned after it settles, so final is a later point, defined by the network's rules.
[pause: 0.8]

[slide: v-031]
[pause: 0.6]
C: Three safety properties, things that must never happen. S-one: one instalment collected twice. S-two: a ledger transaction that doesn't sum to zero in whole cents, or a line that gets edited. S-three: a customer penalised beyond policy, or for our own failure.
C: And three liveness properties, things that must eventually happen. L-one: every due instalment is attempted on its due date, before the cut-off. L-two: every payment leaves unknown and pending, within a bound. L-three: every difference with the outside becomes a break with an owner, within a day. Every fix from here on says which one it serves. Most designs are silent on liveness.
[pause: 0.8]

[slide: v-032]
[pause: 1.0]
C: The central tension is when money is final, and who decides. In seconds, a card answer, or nothing. In a day or two, the debit settles. Two banking days, an insufficient-funds return. Sixty days, an unauthorised return. Months, refunds and card disputes. And every day, the bank's own view, which we must match.
C: Finance wants cash recognised as early as possible. Risk would rather wait sixty days. The design that serves both posts the cash at settlement, and reports the exposure by age. Instant payment rails, spreading since twenty twenty-three, remove some pending states, but not returns, and not reconciliation.
[pause: 1.0]

[slide: v-033]
[pause: 0.6]
C: Mechanism one, the immutable double-entry ledger. It protects S-two and the audit. Every movement is two or more lines that sum to zero in whole cents, inserted and never updated. And here I correct a common line: never store a balance is too strict. I keep a balance row, updated in the same commit, at a version, so it is fast to read and always provable from the lines. It rules out balances nobody can explain. It costs storage that only grows, and a reversing transaction for every mistake.
[pause: 0.8]

[slide: v-034]
[pause: 0.6]
C: Mechanism two, the payment state machine, with unknown and returned in it. It protects S-one and L-two. A timeout goes to unknown, which has its own exits. A return moves a settled payment to returned and posts a reversal. It rules out the double charge that follows treating a timeout as a failure, and a return that has nowhere to go. It costs more states to test, and pending shown to customers for days.
[pause: 0.8]

[slide: v-035]
[pause: 0.6]
C: Mechanism three, idempotency at three layers. It protects S-one. The ledger transaction carries a unique key built from the loan, the instalment and the attempt. The same key goes to the processor, so a resend returns the first result. And a unique index allows one open intent per instalment. Three layers, three different duplicates ruled out. It costs one discipline: retrying the same attempt reuses its key. Only a new decision to try again gets a new attempt number.
[pause: 0.8]

[slide: v-036]
[pause: 0.6]
C: Mechanism four, the database as the queue. It protects L-one. Due items are rows. Workers claim batches with a skip-locked query, so no two workers take the same row, and write the payment intent and an outbox row in the same commit. A sweeper returns claims that went stale. It rules out lost work and work done twice. It costs some polling, and a sweeper.
[pause: 0.8]

[slide: v-037]
[pause: 0.6]
C: Mechanism five, a rail budget. It protects L-one, and S-three, because declines caused by our own throttling would be our fault. A token bucket per rail set below the contract, a day plan worked backwards from the cut-off, and a pause switch per rail. It rules out a midnight burst that the processor throttles into declines, and a missed cut-off. It costs planning, and some product work to spread due dates.
[pause: 0.8]

[slide: v-038]
[pause: 0.6]
C: Mechanism six, policy as versioned data. It protects S-three and the audit. The allocation order, the retry schedule, late fees and how refunds land are rules with versions and named owners, and every posting records the version it used. It rules out behaviour nobody can explain. It costs a rules component, and owners in risk and legal who sign off changes.
[pause: 0.8]

[slide: v-039]
[pause: 0.6]
C: Mechanism seven, three-way reconciliation. It protects L-three. The ledger says what it expects. The processor's report and the bank statement are matched to it, line by line, by reference first. Every difference becomes a typed break with an owner and an age. It rules out silent divergence, and the plug at month-end that makes totals agree. It costs a pipeline, a console, and people.
[pause: 0.8]

[slide: v-040]
[pause: 1.0]
C: Now the options, each with the failure that rules it out. Three that look reasonable.
C: A, a cron job at midnight, a balance column, retry on any error. It fails at the first timeout and retry, and the processor throttles the midnight burst. B, a message broker: six hundred thousand messages fanned out to workers, no state machine. A crash and redelivery charges again, unknown and returned have nowhere to live, and it solved a load problem we don't have. C, an event-sourced loan in a log. It explains every cent, but a refund or payoff needs a current balance right now, and every correction becomes a replay.
[pause: 1.0]

[slide: v-041]
[pause: 1.0]
C: D is the pick: a relational ledger, the state machine, the database as the queue, a rail budget, policy as data, and three-way reconciliation. It only fails when a processor gives us no way to ask about our own key, and then the settlement file decides, a day late.
C: E, buy a servicing platform. For a small book with standard products, that is the honest first version. It fails when the product needs its own refund rules, or the company must keep its own books of record.
[pause: 1.0]

[slide: v-042]
[pause: 0.6]
C: What D buys is never guessing. A retry is harmless, an unknown has an exit, a return has a place to land, every balance is a sum, and the bank is checked daily. What it gives up: more states to test, a reconciliation team, pending on customer statements for days, and every product change becomes a policy version someone must own. I'd say that cost out loud, because it lands on product and finance.
[pause: 0.8]

[slide: v-043]
[pause: 1.0]
C: Last, the failure catalogue, which becomes the challenge list. A card charge times out, the first half of the crux. Six hundred thousand on one morning. A settled debit that comes back, the second half. A refund that changes the schedule. A payoff while a debit is in flight. A month-end that doesn't match. The card processor down on the first. And nobody noticing until close.
[pause: 1.0]

[pause: 1.4]

## 4 API and entities

[slide: v-044]
[pause: 1.2]
C: The A-P-I and the data model before the boxes. Every call carries a tag: the requirement it serves and the entity it reads or writes.
[pause: 1.8]

[slide: v-045]
[pause: 1.0]
C: Schedule. Origination emits loan booked: the loan I-D, the principal in cents, the terms version, the first due date, and the rail with the customer's debit mandate. Twelve hundred dollars, eight instalments of a hundred and fifty.
C: It creates the first schedule version, with due dates moved to business days, because a bank debit can't take effect on a weekend or a bank holiday. And the booking transaction in the ledger. The event is idempotent by loan I-D: delivered twice, it creates nothing new.
[pause: 1.0]

[slide: v-046]
[pause: 1.0]
C: Three calls change a live loan. A payment from the customer, with an idempotency key. A refund from the merchant, where the merchant's own refund I-D is the key, so a merchant retry can't refund twice.
C: And the payoff quote, which returns a quote I-D, an amount, a validity date, and, importantly, a list of payments still in flight. Challenge five is about why that list is there.
[pause: 1.0]

[slide: v-047]
[pause: 1.3]
C: Behind every collection is this state machine. Scheduled, submitted, pending, settled. From submitted, a timeout goes to unknown, and from unknown we query by the same key, never resend. From pending, a decline. And the dashed red arrow: settled to returned, up to sixty days later for a bank debit.
C: From returned, an insufficient-funds return can become retry due, at most twice more, by the network's rules. Any transition not drawn here is rejected by the code.
[pause: 1.1]

[slide: v-048]
[pause: 1.0]
C: What crosses to the outside. For cards, one call per attempt, carrying our key: loan, instalment, attempt. And a query by that same key. For the bank, files: we submit a debit file and wait for its acknowledgement, and we import returns, settlement reports and statements. Every file is stored unchanged before anything reads it, so a bug in parsing can be replayed.
[pause: 1.0]

[slide: v-049]
[pause: 1.3]
C: The conceptual model. A loan has schedule versions; a refund or a payoff creates a new one. A schedule version contains instalments. An instalment is collected by payment intents, at most one open at a time. A loan posts ledger transactions, each containing lines. And an intent posts the transactions for its result.
C: The double borders are weak entities: a schedule version only exists inside its loan, and a line only inside its transaction.
[pause: 1.1]

[slide: v-050]
[pause: 1.3]
C: The physical model. Ledger lines, partitioned by month, insert only. Ledger transactions with a unique idempotency key and the policy version they used. The account balance row, with a version, updated in the same commit. Due items indexed by date, shard and status, which is the work queue. Payment intents with a partial unique index: one open intent per instalment. And the outbox.
[pause: 1.1]

[slide: v-051]
[pause: 1.3]
C: A worked example. Booking a twelve-hundred dollar loan: we are owed twelve hundred of principal, we owe the merchant eleven sixty-four, and we earned thirty-six of discount fee. An instalment collected by bank debit first moves a hundred and fifty into cash clearing, while it is pending. When it settles, clearing moves to cash at the bank.
C: A return is a new transaction reversing those last lines. Nothing here is ever edited.
[pause: 1.1]

[slide: v-052]
[pause: 1.0]
C: Posting, in code. The transaction row carries the key, with a unique constraint, so a retry fails at the first insert and the first result is returned. Two lines that sum to zero. And the balance row updated in the same commit, at the version we read, so two postings to one loan cannot interleave. A deferred check rejects the commit unless the lines sum to zero.
C: Lines are facts, and never change. The balance is a projection, and provable from them.
[pause: 1.0]

[slide: v-053]
[pause: 0.6]
C: Three rules that are cheap to say and expensive to forget. Never a float: integer cents, and how an instalment rounds is a rule, with the remainder on the last payment. Business days: a due date on a weekend or a bank holiday takes effect the next business day, and late fees count from there. And two dates on every line: when it happened, and when we booked it, so a return that arrives today never edits last month.
[pause: 0.8]

[pause: 1.4]

## 5 High-level design

[slide: v-054]
[pause: 1.2]
C: Now the design, in three versions, each introduced by the objection to the one before. The boxes never move: every later picture is a view of the same baseline.
[pause: 1.8]

[slide: v-055]
[pause: 1.3]
C: Version one. Origination books a loan through the servicing A-P-I. At midnight, a job in the schedule service loops over every loan due today, charges each at the rails, and updates the loan's balance column. It is the simplest thing that works, and many first versions look exactly like this.
[pause: 1.1]

[slide: v-056]
[pause: 1.0]
C: The objection, as a trace. At midnight the job sends two thousand card charges a second against a contract of a hundred. Three seconds later the processor throttles ninety-five percent, and the job retries them at once. At eight, one charge times out and is retried as a new charge: charged twice.
C: On the third, a debit comes back, and the balance column was already reduced: there is nowhere to post it. And at year end, an auditor asks why a balance is what it is, and there is no history.
[pause: 1.0]

[slide: v-057]
[pause: 1.3]
C: Version two. The database becomes the servicing database: the ledger with its projection, due items, payment intents and an outbox. The schedule service claims due items and writes intents and outbox rows in one commit. A new dispatcher drains the outbox under a budget per rail, sends each charge with its key, and posts the result.
C: A timeout now leaves the intent unknown instead of failed, and the rail sets the pace instead of a midnight burst.
[pause: 1.1]

[slide: v-058]
[pause: 0.6]
C: The objection to version two. Inside the database it is correct. But settlements and returns arrive as files days later, and nothing reads them. Nothing ends an unknown: two hundred and forty on the first, pending forever. Refunds and payoffs change schedules, while allocation and fees are buried in code. And our books can differ from the bank's without anyone noticing.
[pause: 0.8]

[slide: v-059]
[pause: 1.3]
C: Version three closes those loops. File ingest takes the bank's and processor's files and posts settlements and reversals. A resolver asks the processor about every unknown, by the same key, and hands the answer to the dispatcher. A policy service holds terms, allocation, retry and fee rules as versioned data. Reconciliation matches all three views and gives breaks to finance operations. And an outbox relay feeds customer notices.
C: This is the baseline. Every picture from here on is a view of it.
[pause: 1.1]

[slide: v-060]
[pause: 1.0]
C: The collect path in code. In one transaction: claim up to five hundred due rows with skip locked, open an intent for each, unique while open, and add an outbox row. Then the dispatcher, under the rail's bucket, charges with the intent's key. On a timeout it sets unknown and stops: the resolver takes over. Otherwise it posts lines, balance and state in one commit, under the same key.
C: No branch guesses. A crash at any line leaves a row that says how far we got.
[pause: 1.0]

[slide: v-061]
[pause: 1.3]
C: Requirement one, schedule, by the numbers. One: origination emits loan booked to the servicing A-P-I. Two: the A-P-I hands it to the schedule service. Three: the schedule service asks policy for the terms version: how many instalments, the rounding rule, the allocation order. Four: one transaction writes the schedule version, the due items and the booking lines.
[pause: 1.1]

[slide: v-062]
[pause: 1.3]
C: Requirement two, collect. One: on the due date, the schedule service claims the row and commits the intent and its outbox row. Two: the dispatcher drains the outbox, under the rail's budget. Three: it sends the charge with its key, or puts the debit in the day's file. Four: the result comes back. Five: it posts the result: lines, the balance and the state, in one commit.
[pause: 1.1]

[slide: v-063]
[pause: 1.3]
C: Requirement three, adjust. One: the merchant's refund, or the customer's payoff, reaches the A-P-I. Two: it goes to the schedule service. Three: policy says how it lands: re-amortise or shorten, and the allocation order. Four: one transaction writes the ledger lines and the new schedule version. Five and six: the answer goes back.
[pause: 1.1]

[slide: v-064]
[pause: 1.3]
C: Requirement four, returns. One: the bank's return file arrives and is stored raw. Two: file ingest matches each return to its attempt and posts a reversing transaction, dated the day it arrived, and moves the instalment back to due. Three: the outbox relay emits the event. Four: the customer gets a notice saying what happens next.
[pause: 1.1]

[slide: v-065]
[pause: 1.3]
C: Requirement five, reconcile. One: the processor's report and the bank's statement arrive and are stored raw. Two: file ingest passes their lines to reconciliation. Three: reconciliation reads the ledger's expectations for the day and matches line by line. Four: every line that doesn't match becomes a break, with an owner, in front of finance operations.
[pause: 1.1]

[slide: v-066]
[pause: 1.3]
C: The C4 context. The customer repays and asks for payoffs. Merchants send refunds. Origination books loans. Our servicing system charges and queries at the card processor, sends debit files to the bank, and receives returns and statements from it. Finance operations own the breaks and the close. Notice that the processor and the bank each keep their own books of the same money.
[pause: 1.1]

[slide: v-067]
[pause: 1.3]
C: The containers. The servicing A-P-I owns keys, refunds and quotes. Schedule and collect owns due items and the state machine. The servicing database holds the ledger, intents and outbox, partitioned by month. The dispatcher owns the rail budgets. Below: policy, file ingest, the resolver, and reconciliation, which reads expectations from the ledger.
[pause: 1.1]

[slide: v-068]
[pause: 1.3]
C: One card instalment as a sequence. One, highlighted: the claim, the intent and the outbox row in one commit. Two: the dispatcher drains the outbox at ninety a second. Three: charge a hundred and fifty dollars with key coll, loan fifty-five thirty-one, instalment two, attempt one. Approved in one point four seconds. Four: one transaction sets settled, posts the lines and the balance. A retry with the same key stops at the ledger's unique key.
[pause: 1.1]

[pause: 1.4]

## 6 Bridge

[slide: v-069]
[pause: 1.2]
V: It works. The question now is where it breaks first.
[pause: 1.8]

[slide: v-070]
[pause: 1.3]
C: The baseline with its attack points marked. The dispatcher and the rails, where a charge can time out, and where a whole morning has to fit under a contract. File ingest, where settled payments come back. The schedule service and the A-P-I, where refunds and payoffs change a live loan. Reconciliation, where the bank disagrees. Then the processor down on the busiest morning, and silence. Eight challenges, each fix creating the next question.
[pause: 1.1]

[pause: 1.4]

## 7 Challenges

[slide: v-071]
[pause: 1.2]
C: Each challenge runs the same way: the question, the naive answer, a case with numbers, where it breaks, the fix and why it works. Then the interviewer pushes on the fix itself, and I say what I'd say in the room.
[pause: 1.8]

[pause: 1.4]

## 7.1 Challenge 1: The processor timed out

[slide: v-072]
[pause: 1.2]
N: Challenge one, the crux. A card charge times out, and the worker wants to retry.
[pause: 1.8]

[slide: v-073]
[pause: 0.6]
I: The processor times out on a card charge. Your worker retries. Was the customer charged twice?
[pause: 2.0]

[slide: v-074]
[pause: 1.3]
C: The naive answer: mark it failed and retry. Look at the red arrows between the dispatcher and the rails. A timeout is not an answer. The request may have arrived and been approved, and we simply never heard. If the retry goes out as a new attempt, with a new key, the processor has every reason to charge again.
[pause: 1.1]

[slide: v-075]
[pause: 1.0]
C: The trace. At eight, instalment two of loan fifty-five thirty-one, a hundred and fifty dollars, goes out with key attempt one. At three point two seconds the processor approves it. At ten seconds the worker gives up and the naive design marks it failed. At twelve seconds a retry goes out as attempt two, with a new key, and it is approved too. Three hundred dollars for a hundred and fifty dollar instalment.
C: The numbers are illustrative, but approvals really do land after the caller has given up.
[pause: 1.0]

[slide: v-076]
[pause: 1.3]
C: The fix. At the timeout the intent goes to unknown, not failed. Then the new green box: the resolver asks the processor about the same key, after thirty seconds, two minutes and ten minutes. And the rule: resending the same attempt reuses its key, so the processor returns the first result. Only a definite decline lets us open attempt two.
[pause: 1.1]

[slide: v-077]
[pause: 1.3]
C: As a sequence. One: the charge with key attempt one. No answer at ten seconds. Two, highlighted: the intent goes to unknown. Three: the resolver queries by the same key, and four, the processor says approved at three point two seconds. The resolver posts it as settled, through the same ledger key, so it can only be posted once. In the note: if the processor says not found after its safe window, we resend, with the same key.
[pause: 1.1]

[slide: v-078]
[pause: 1.0]
C: The resolver in code. Query by key. Approved: post it, idempotently. Declined: mark it declined, and now a second attempt is allowed. Not found, and older than the processor's safe window: send again, still with the same key. Anything else: ask again later. No path creates a second decision for one attempt, and even a wrong guess resends a key the processor will de-duplicate.
[pause: 1.0]

[slide: v-079]
[pause: 0.6]
I: The query says not found. You resend. Tomorrow's settlement file shows the first charge went through after all.
[pause: 2.0]

[slide: v-080]
[pause: 0.6]
C: With the same key, a processor that honours keys returns the first result, so usually there is no harm. And not found should only count as final after the processor's documented window. If it still happened, reconciliation finds two settled charges for one instalment the next morning, refunds the duplicate automatically, and counts it as an incident.
C: The honest limit: a processor that neither honours keys nor answers queries can only be checked by its file, a day late. That is a reason to choose processors, and I'd say so to whoever negotiates the contract.
[pause: 0.8]

[slide: v-081]
[pause: 0.7]
V: If asked, I'd say: a timeout is not a failure. The intent goes to unknown, the resolver queries by the same key, and a resend reuses that key. The settlement file is the final arbiter.
[pause: 1.0]
N: Next: there are six hundred thousand of these on one morning.
[pause: 1.6]

[pause: 1.4]

## 7.2 Challenge 2: The morning of the 1st

[slide: v-082]
[pause: 1.2]
N: Challenge two. Six hundred thousand payments due on one day: where is the real limit?
[pause: 1.8]

[slide: v-083]
[pause: 0.6]
I: Six hundred thousand payments are due on the first. Walk me through that morning.
[pause: 2.0]

[slide: v-084]
[pause: 1.3]
C: Two naive answers. A cron job at midnight, or, it's a thundering herd, so put a message broker in front. Look where the red is: the schedule service and the dispatcher, and the arrow to the rails. Forty-two a second never hurt the database. The burst hits the processor's contract, and a file that has to reach the bank by two.
[pause: 1.1]

[slide: v-085]
[pause: 1.0]
C: The trace. At midnight, two thousand card charges a second against a contract of a hundred. Three seconds in, the processor throttles ninety-five percent, and the workers retry at once, which makes it worse. Twenty minutes later, eighteen thousand charges are marked failed, and late fees are due tomorrow, for a failure that was ours.
C: And the debit file, built at five to two, fails validation on one bad record. The cut-off passes. Four hundred and eighty thousand collections slip a day.
[pause: 1.0]

[slide: v-086]
[pause: 1.3]
C: The fix: plan the day backwards from the cut-off. The new green box, the day plan, hands each rail its budget. The debit file is built at nine, validated, submitted by half past ten, and acknowledged by eleven, three hours before the cut-off, so a rejected file can be fixed and resent. The card window opens at six, at ninety a second.
[pause: 1.1]

[slide: v-087]
[pause: 1.3]
C: The day on one line. Card charges from six, a hundred and twenty thousand in twenty-two minutes. Soft declines retried around seven. The debit file built from nine and submitted by half past ten. The bank's acknowledgement by eleven. And the red line at two, with three hours of margin in front of it.
[pause: 1.1]

[slide: v-088]
[pause: 1.0]
C: The claim in code. Select up to five hundred due rows in one shard, lock them, and skip rows another worker has locked. Mark them claimed in the same statement, and in the same transaction open the intents and outbox rows. A worker that dies before the commit releases its locks. One that dies after is found by the sweeper, which returns claims with no intent. No distributed lock, and no broker.
[pause: 1.0]

[slide: v-089]
[pause: 1.3]
C: As a sequence. Worker one claims five hundred rows in shard seven. Worker two asks for the same shard and skips the locked rows. Three, highlighted: per row, an intent and an outbox row, and commit. If worker two dies before its commit, its rows are due again. Four: the dispatcher drains the outbox, cards at ninety a second, debits into the nine o'clock file.
[pause: 1.1]

[slide: v-090]
[pause: 0.6]
I: At ten past six, the processor lowers your limit to fifty a second.
[pause: 2.0]

[slide: v-091]
[pause: 0.6]
C: The bucket's rate is live: a throttle response halves it at once. By ten past six, fifty-four thousand are done, and the other sixty-six thousand at fifty a second take twenty-two minutes. Done by six thirty-two, still hours before anything matters.
C: And the better fix is upstream: spread due dates when loans are created. Let the customer choose a day, and default to the day of booking. The peak shrinks at the source.
[pause: 0.8]

[slide: v-092]
[pause: 0.7]
V: If asked, I'd say: forty-two a second is nothing for a database. The limits are the processor's contract and the bank's cut-off, so I plan backwards from the cut-off, with a budget per rail.
[pause: 1.0]
N: The debits go out on time. A few days later, some come back.
[pause: 1.6]

[pause: 1.4]

## 7.3 Challenge 3: It settled, then it came back

[slide: v-093]
[pause: 1.2]
N: Challenge three, the second half of the crux. A debit that settled comes back.
[pause: 1.8]

[slide: v-094]
[pause: 0.6]
I: A bank debit settled on the second. On the third it comes back for insufficient funds. Another one comes back forty days later, as unauthorised.
[pause: 2.0]

[slide: v-095]
[pause: 1.3]
C: The naive answer: settled means paid, close the instalment, and retry anything that fails. Look at file ingest. The return has no state to land in, the balance was already reduced, and automatically retrying an unauthorised debit breaks the bank network's rules.
[pause: 1.1]

[slide: v-096]
[pause: 1.0]
C: The trace. On the first, instalment three of loan seventy-seven oh two goes in the debit file. On the second it settles, and the naive design closes the instalment. On the third, a return with code R-zero-one, insufficient funds. There is no state for it, and the balance was already reduced.
C: Another loan's debit settled on the second. On the eleventh of January, day forty, it returns as R-ten, unauthorised: the customer says they never agreed to it. The naive design retries it automatically. That breaks the rules, and turns a dispute into a complaint.
[pause: 1.0]

[slide: v-097]
[pause: 1.3]
C: The fix. Settled moves to returned, a normal state. File ingest posts a reversing transaction, dated the day the return arrived, never editing the original. The instalment goes from paid back to due, with the reason. Then policy decides: insufficient funds may be presented again at most twice, typically timed after payday. Unauthorised is never retried: the customer is contacted, and a new authorisation is needed.
[pause: 1.1]

[slide: v-098]
[pause: 1.3]
C: As a sequence. One: the bank's return file, loan seventy-seven oh two, a hundred and fifty, code R-zero-one. Two, highlighted: ingest matches it to the attempt by the trace number, and moves settled to returned. Three: the reversing transaction dated the third, and the instalment back to due. Four: policy says re-present, attempt two of at most three, after payday. Five: a notice to the customer. And in red: an R-ten on day forty is never re-presented.
[pause: 1.1]

[slide: v-099]
[pause: 1.0]
C: The rules as a table, because they are data. Insufficient funds: back within two banking days, and may be presented again at most twice within a hundred and eighty days. Account closed or not found: stop, and ask for a new payment method. Unauthorised: up to sixty days, never retried. And late fees, which are capped by law where the customer lives, and never charged for our own failures. Engineering owns the mechanism. Risk and legal own this table.
[pause: 1.0]

[slide: v-100]
[pause: 0.6]
I: Finance wants to recognise the cash on settlement day. Risk wants to wait sixty days. Who wins?
[pause: 2.0]

[slide: v-101]
[pause: 0.6]
C: Both, with the exposure on a report. Cash is posted at settlement, because that is when the bank says it is cash, and a return is a later reversal, in the month it arrives. And a daily report shows everything settled in the last sixty days, by age, against the observed return rate. Risk prices that exposure. Nobody's process waits on it.
[pause: 0.8]

[slide: v-102]
[pause: 0.7]
V: If asked, I'd say: settled is not final for a bank debit. A return is a state and a reversal dated when it arrives, and whether we retry is policy: never for unauthorised.
[pause: 1.0]
N: Returns move money backwards. So do refunds, but they also change the schedule.
[pause: 1.6]

[pause: 1.4]

## 7.4 Challenge 4: A refund in the middle of the loan

[slide: v-103]
[pause: 1.2]
N: Challenge four. A merchant refunds part of a purchase two payments in.
[pause: 1.8]

[slide: v-104]
[pause: 0.6]
I: After two instalments, the merchant refunds three hundred dollars of the twelve hundred. What changes?
[pause: 2.0]

[slide: v-105]
[pause: 1.3]
C: The naive answer: subtract three hundred from the balance. Look at the schedule service. The balance changed, but the schedule still says six more payments of a hundred and fifty. The customer would pay nine hundred dollars on a six-hundred dollar debt.
[pause: 1.1]

[slide: v-106]
[pause: 1.0]
C: The trace. Loan ninety-one hundred is booked in October: twelve hundred dollars in eight payments of a hundred and fifty. Two are paid by November: nine hundred outstanding. On the fourteenth the merchant refunds three hundred, and the balance column drops to six hundred. But the schedule is untouched, and from December to May it collects six times a hundred and fifty: nine hundred dollars. The customer overpaid three hundred, and the customer noticed before we did.
[pause: 1.0]

[slide: v-107]
[pause: 1.3]
C: The fix. In the ledger, the merchant now owes us three hundred, and the loan's principal drops by three hundred, keyed by the merchant's refund I-D. Then policy, the green box, applies the terms. Re-amortise: the six remaining payments become a hundred each. Or shorten: they stay at a hundred and fifty, and the loan ends after four. Which one is a product and legal decision, written in the terms before any code.
[pause: 1.1]

[slide: v-108]
[pause: 1.0]
C: Every payment is also allocated, in an order policy sets. Typically fees due, then interest due, then this instalment's principal, and anything extra reduces future principal. It is one versioned rule, applied by one piece of code, and every posting records the version. So the ledger can always say why each cent went where it did.
[pause: 1.0]

[slide: v-109]
[pause: 1.3]
C: As a sequence. One: the merchant refunds three hundred on loan ninety-one hundred, with its refund I-D. Two: the terms, version three, say re-amortise. Three, highlighted: the ledger transaction, keyed by that I-D, so a merchant retry posts nothing new. Four: schedule version two, six payments of a hundred, from instalment three. And the note: if instalment three is already in flight, it stays in flight, and allocation sorts it out when it settles.
[pause: 1.1]

[slide: v-110]
[pause: 0.6]
I: The customer has paid nine hundred. Now the merchant refunds the full twelve hundred.
[pause: 2.0]

[slide: v-111]
[pause: 0.6]
C: Then the loan's principal goes to zero, and the nine hundred the customer paid becomes money we owe them, in a customer payable account. It is refunded to the original payment method within the days policy sets, and never held silently as credit. On the merchant side, they owe us the twelve hundred back, and whether we return the thirty-six dollar discount fee is the merchant contract, also versioned.
[pause: 0.8]

[slide: v-112]
[pause: 0.7]
V: If asked, I'd say: a refund is a ledger transaction and a new schedule version. Re-amortise or shorten is a decision in the terms, and any overpayment goes back to the customer.
[pause: 1.0]
N: That one changed the future. The next one changes the loan while money is still moving.
[pause: 1.6]

[pause: 1.4]

## 7.5 Challenge 5: Paying off with a debit in flight

[slide: v-113]
[pause: 1.2]
N: Challenge five. The customer pays off early, but a debit from two days ago hasn't cleared.
[pause: 1.8]

[slide: v-114]
[pause: 0.6]
I: On the third, the customer pays off the loan early. Instalment three's debit from the first is still pending. What do you quote?
[pause: 2.0]

[slide: v-115]
[pause: 1.3]
C: The naive answer: quote the balance. But the balance either counts the pending debit as paid, or it doesn't. Look at the A-P-I. Both choices are wrong some of the time. One over-collects when the debit settles. The other closes a loan that still owes money.
[pause: 1.1]

[slide: v-116]
[pause: 1.0]
C: The trace. On the first, instalment three, a hundred and fifty dollars, goes in the debit file, with nine hundred outstanding before it. On the third, quote A says nine hundred, ignoring the pending debit. The customer pays by card, the debit settles too, and we've over-collected a hundred and fifty.
C: Quote B says seven hundred and fifty, counting the debit as paid. The loan is closed and the merchant told. On the fourth, the debit returns for insufficient funds. Now a closed loan owes a hundred and fifty, and nobody has a process for that.
[pause: 1.0]

[slide: v-117]
[pause: 1.3]
C: The fix: a payoff quote is a statement about the future, so it lists what is in flight. Quote q-thirty-one: seven hundred and fifty now, conditional on the hundred and fifty dollar debit clearing, valid until the fifth. Paying it moves the loan to paid-pending, not closed. If the debit clears, the loan closes. If it returns, a hundred and fifty reopens as a single due item, with no late mark.
[pause: 1.1]

[slide: v-118]
[pause: 1.3]
C: As a sequence. One: the customer asks for a quote. The answer: seven hundred and fifty now, the hundred and fifty debit listed, valid to the fifth. Two: they pay against q-thirty-one, and the quote I-D is the idempotency key, so a double tap pays once. Three, highlighted: the lines post, and the loan is paid-pending. Four: if the return arrives, one due item of a hundred and fifty. And if nothing comes back by the fifth, closed, lien released, and a notice.
[pause: 1.1]

[slide: v-119]
[pause: 1.0]
C: The rule as a table. Nothing in flight: quote the full balance and close. A card charge in flight: minutes, then close. A bank debit in flight: a conditional quote, and close when the debit is past its insufficient-funds window. A debit not yet sent: cancel it, quote the full balance, and close. What is left is the sixty-day unauthorised window, and that is handled as a dispute, not by holding every loan open for two months.
[pause: 1.0]

[slide: v-120]
[pause: 0.6]
I: The day after the payoff, a merchant refund arrives on the same loan.
[pause: 2.0]

[slide: v-121]
[pause: 0.6]
C: The refund takes principal below zero. The excess becomes customer payable, money we owe, and it is paid back automatically to the original method. And every customer payable older than the policy's limit pages its owner. Money we owe is never left sitting as a quiet credit.
[pause: 0.8]

[slide: v-122]
[pause: 0.7]
V: If asked, I'd say: a payoff quote lists what's in flight. The loan goes to paid-pending and closes only when nothing can still come back, and any overpayment is refunded automatically.
[pause: 1.0]
N: All these moving parts meet at month-end, when the bank sends its statement.
[pause: 1.6]

[pause: 1.4]

## 7.6 Challenge 6: Four hundred dollars more than the bank

[slide: v-123]
[pause: 1.2]
N: Challenge six. Month-end, and the ledger and the bank disagree.
[pause: 1.8]

[slide: v-124]
[pause: 0.6]
I: Month-end. The ledger says we collected four hundred dollars more than the bank received. Find it.
[pause: 2.0]

[slide: v-125]
[pause: 1.3]
C: The naive answer: compare the totals, and post a four-hundred dollar adjustment so the month can close. Look at reconciliation. A total is a sum of differences, and some of them cancel each other out. One of the hidden ones may be a customer charged twice.
[pause: 1.1]

[slide: v-126]
[pause: 1.0]
C: The trace. The ledger says ninety million and four hundred dollars collected in November. The bank says ninety million. Inside the four hundred: plus three hundred, two insufficient-funds returns on the bank statement for the thirtieth, whose return file only arrives on the first. That is timing. Plus a hundred, a card dispute the processor deducted from its payout, and we have no record of it.
C: And a pair that hides itself: plus a hundred and fifty, a card payment we think settled and the processor never settled. Minus a hundred and fifty, a charge the processor did settle that we hold as declined. That one is a customer charged twice. In the total, those two cancel to zero.
[pause: 1.0]

[slide: v-127]
[pause: 1.3]
C: The fix: match every line, three ways, by reference. The ledger produces what it expects. The processor's report and the bank statement are matched to it by our reference, then by amount within a three-day window. Every difference becomes a typed break: timing, missing in our ledger, missing at the processor, or a wrong amount. Each one gets an owner and an age.
[pause: 1.1]

[slide: v-128]
[pause: 1.3]
C: As a sequence. One: the expectations for the thirtieth, by reference. Two and three: the processor's report and the bank statement. Then the match, by reference first. Four, highlighted: four breaks go to finance operations, one timing and three real, each with an owner. The timing break closes itself when the return file posts on the first.
[pause: 1.1]

[slide: v-129]
[pause: 1.0]
C: Four breaks, four owners. The three hundred is timing, and closes itself. The hundred is a dispute missing from our ledger: the disputes team posts it and decides whether to contest. The hundred and fifty that never settled: payments queries it and reverses our posting. And the double charge: payments posts it and refunds the customer today.
N: Reconciling by totals is the most common silent failure in this round.
[pause: 1.0]

[slide: v-130]
[pause: 0.6]
I: It's month-end, and the processor's report is two days late. Close is in two days.
[pause: 2.0]

[slide: v-131]
[pause: 0.6]
C: Close on what is known. The bank statement still reconciles against the ledger two ways, and the card items wait as open timing breaks, listed with amounts and ages, signed off by finance. The honest limit: a late file delays certainty, not the close. And a file that is late three months running is a vendor problem, for whoever owns that contract.
[pause: 0.8]

[slide: v-132]
[pause: 0.7]
V: If asked, I'd say: I never reconcile by totals. I match the ledger, the processor and the bank line by line, by reference, and every difference is a typed break with an owner and an age.
[pause: 1.0]
N: Reconciliation catches a bad day after it happens. Next, the bad day itself.
[pause: 1.6]

[pause: 1.4]

## 7.7 Challenge 7: The card processor is down on the 1st

[slide: v-133]
[pause: 1.2]
N: Challenge seven. The worst morning: the card processor fails halfway through the window.
[pause: 1.8]

[slide: v-134]
[pause: 0.6]
I: Eleven minutes past six on the first, the card processor goes down, with sixty thousand charges left. What do you do?
[pause: 2.0]

[slide: v-135]
[pause: 1.3]
C: The naive answer: keep retrying until it comes back, and whatever failed is late tomorrow. Look at the rails. Blind retries turn an outage into thousands of unknown outcomes, and the late fees turn our outage into the customer's cost.
[pause: 1.1]

[slide: v-136]
[pause: 1.0]
C: The trace. From six to eleven past, fifty-nine thousand four hundred charged at ninety a second. Then the processor goes down with a hundred and eighty in flight, all unknown. Blind retries for nine minutes add nine thousand more timeouts, all unknown. At nine the processor is back, and the workers send everything at once and get throttled again. And on the second, sixty thousand late fees at ten dollars: six hundred thousand dollars charged to customers for our outage.
[pause: 1.0]

[slide: v-137]
[pause: 1.3]
C: The fix, in order. A breaker opens and the rail switch pauses the card rail: no new attempts. The resolver clears the hundred and eighty unknowns first, before anything is sent again. Policy, agreed in advance: our outage is not your late fee, so the late clock runs from our attempt window, not from the due date. Then resume at fifty a second, and ramp up.
[pause: 1.1]

[slide: v-138]
[pause: 1.0]
C: As a runbook. Pause the card rail, with one switch, to stop creating unknowns. Resolve every unknown before resending anything. Suppress late marks and fees, under a policy agreed before the outage, not during it. Resume at fifty, and ramp to ninety. And tell customers what happens next, before they ask.
C: Note what is missing: failover. The card tokens live at this processor, so I can't move card customers to another one this morning. Bank debit is a fallback only for customers with a debit mandate.
[pause: 1.0]

[slide: v-139]
[pause: 0.6]
I: It stays down until three in the afternoon, past the bank's cut-off for any fallback.
[pause: 2.0]

[slide: v-140]
[pause: 0.6]
C: Then collect tomorrow. The day plan re-runs, the sixty thousand join tomorrow’s card window, and the grace period extends automatically for everyone affected. Longer term, network tokens that work across processors, and a second processor in the contract. That is a quarter of work, and I'd price it against what a day like this costs.
[pause: 0.8]

[slide: v-141]
[pause: 0.7]
V: If asked, I'd say: pause the rail, resolve every unknown before sending anything, never charge a late fee for our outage, and resume under a lower limit.
[pause: 1.0]
N: Every fix so far assumed someone noticed. Last, how you would know.
[pause: 1.6]

[pause: 1.4]

## 7.8 Challenge 8: How would you know before month-end?

[slide: v-142]
[pause: 1.2]
N: Challenge eight, observability. Finding the problem before finance finds it at close.
[pause: 1.8]

[slide: v-143]
[pause: 0.6]
I: How would you know any of this is going wrong, before finance finds it at month-end close?
[pause: 2.0]

[slide: v-144]
[pause: 1.3]
C: The naive answer: error rate and latency. Look at the dispatcher and file ingest. A debit file that the bank half-rejects is still a successful upload. Nothing on a server dashboard moves.
[pause: 1.1]

[slide: v-145]
[pause: 1.0]
C: The trace. At half past ten on the first, the debit file goes out with four hundred and eighty thousand entries. Zero errors. At eleven the bank's acknowledgement says twelve thousand were rejected, after a change in an account-number format, and nobody reads it. On the second, twelve thousand customers get late notices for payments we never sent. Finance finds it at close.
[pause: 1.0]

[slide: v-146]
[pause: 1.3]
C: The fix: indicators on the money. A funnel per rail per day: due, claimed, sent, acknowledged, settled, returned. A page if the file isn't acknowledged by eleven. Unknown count and age. Returns by reason code, against their baseline. Breaks by age and amount. And every night, a check that every transaction sums to zero, and every balance equals the sum of its lines.
[pause: 1.1]

[slide: v-147]
[pause: 1.3]
C: As a sequence. One: the file goes out with four hundred and eighty thousand entries. The acknowledgement, highlighted: twelve thousand rejected. Two: the probe feeds the funnel to monitoring. In red: acknowledged over sent is ninety-seven and a half percent, against a baseline of ninety-nine point nine. Page, at eleven, with three hours left before the cut-off to fix and resend.
[pause: 1.1]

[slide: v-148]
[pause: 1.0]
C: Then read them in pairs. Sent normal, acknowledged down: the bank rejected entries, so read the file. Unknowns up with latency at the timeout: the processor is slow. Unauthorised returns up, concentrated on one merchant: we are capturing authorisations badly there. Breaks up today with return ingest lagging: ingest is stuck, not the money. And any transaction that doesn't sum to zero: stop posting and page.
N: Pairs like these are the start of a real runbook.
[pause: 1.0]

[slide: v-149]
[pause: 0.6]
I: A policy change misallocates four dollars on thirty thousand loans. Every transaction still sums to zero.
[pause: 2.0]

[slide: v-150]
[pause: 0.6]
C: Balanced but wrong needs two more checks. Shadow every new policy version over yesterday's postings and diff the allocations before it goes live; because policy is data, that is a query, not a project. And a per-loan invariant, every night: the remaining schedule sums to the outstanding principal. A misallocation that still balances fails right there.
[pause: 0.8]

[slide: v-151]
[pause: 0.7]
V: If asked, I'd say: I watch the money, not the servers. A funnel from due to settled per rail, the file acknowledged by eleven, unknowns and breaks by age, and nightly invariants on the ledger and every loan.
[pause: 1.6]

[pause: 1.4]

## 8 Build cost

[slide: v-152]
[pause: 1.2]
N: This chapter is marked auxiliary. It is the engineering-manager layer, optional in a Staff round.
C: Servicing is three releases, and the order matters more than the size.
[pause: 1.8]

[slide: v-153]
[pause: 1.0]
C: Version one: the ledger with projections, schedules, the state machine, the card rail and the resolver. Four engineers for two quarters. Version two: the bank-file rail, returns, policy as data, refunds and payoff. Six engineers for two quarters. Version three: three-way reconciliation, the finance console, runbooks and due-date spreading. Two teams for two quarters, plus a finance operations function. All illustrative. And for a small book with standard products, buying a servicing platform is the honest version zero.
[pause: 1.0]

[slide: v-154]
[pause: 0.6]
C: Three one-way doors. The chart of accounts and the ledger schema: seven years of lines and every auditor depend on them. Terms versioning: contracts cite it, and old loans keep old rules forever. And the idempotency key format, which the processor shares. These get the most review. Everything else can change in a quarter.
[pause: 0.8]

[slide: v-155]
[pause: 1.0]
C: Six owners, and one writer to the ledger. The ledger team owns accounts, the posting interface, the invariants and the close, and nobody else writes lines. Collections and payments own the scheduler, rails, resolver and returns. Servicing product owns refunds, payoff and hardship. Finance operations own reconciliation. Risk and legal own retry rules, fees and allocation, as policy versions they approve. And compliance owns debit authorisations and fee caps.
[pause: 1.0]

[slide: v-156]
[pause: 0.6]
C: Three risks. The return path runs rarely, so it breaks quietly: replay a month of real return files in staging before every release. Reconciliation built last, so the first closes are done by hand. And one processor holding all the card tokens, so there is no failover until network tokens arrive.
[pause: 0.8]

[pause: 1.4]

## 9 Recap

[slide: v-157]
[pause: 1.2]
C: To close: one picture, one sentence per path, the mistakes to avoid, and the thesis.
[pause: 1.8]

[slide: v-158]
[pause: 1.3]
C: The whole design on one baseline. The servicing database with the ledger, intents and the outbox. The dispatcher with its rail budget, the day plan above it, and the rail switch. The resolver and file ingest beside the rails. Policy for terms and rules, the payoff quote at the A-P-I, reconciliation and finance operations at the bottom, and probes watching the funnel.
[pause: 1.1]

[slide: v-159]
[pause: 1.0]
C: One sentence per path. Schedule: a terms version in, a schedule version and booking lines out. Collect: claim, intent and outbox in one commit, then send under the rail budget with the key, and unknown on a timeout. Adjust: a transaction and a new schedule version, and quotes that list what is in flight. Returns: a state, a reversal dated now, and policy decides any retry. Reconcile: line by line, three ways, every break owned.
[pause: 1.0]

[slide: v-160]
[pause: 0.6]
C: The common mistakes. On correctness: a balance column, retrying with a new key, treating settled as final, refunds that leave the schedule alone, and floats. On operations: calling forty-two a second a thundering herd, a midnight burst, reconciling by totals, charging late fees for our own outages, and nobody owning the policy. The same shapes appear in subscription billing, wallets and payroll, under other names.
[pause: 0.8]

[slide: v-161]
[pause: 0.6]
C: If I had thirty seconds. Money lives in a double-entry ledger with immutable lines, and each payment is a state machine with unknown and returned, with keys at three layers. The database is the queue, and a budget per rail and the bank's cut-off shape the day. Returns and unknowns are rare paths, so I test them with real files. And every day the books are reconciled three ways, with an owner for every break.
[pause: 0.8]

[slide: v-162]
[pause: 0.7]
V: Loan servicing is about correctness over months, not throughput. Lines that never change, unknown and returned as ordinary states, the rail as the limit, and a three-way proof every day that our books match the bank's.
[pause: 1.6]
