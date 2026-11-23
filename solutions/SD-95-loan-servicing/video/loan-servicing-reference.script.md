# SD-95 Instalment loan servicing: ledger and collections scheduler: reference solution (Staff L6/L7)

<!-- Video script for slide-video-kit/scripts/build_video.py. [slide: v-NNN] = frames/v-NNN.png; [reveal: v-NNN] = the next
     reveal step of the same slide. Generated from src/*.py: edit the sources, not this file. -->
<!-- voices: N=af_heart@0.92 I=bf_emma@0.95 C=am_michael@0.9 V=am_michael@0.84 -->
<!-- names: C=Candidate V=Candidate N=Coach I=Interviewer -->
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
N: Five axes.
[reveal: v-005]
[pause: 0.45]
N: The weak answer is a cron job, a balance column and a retry loop.
[reveal: v-006]
[pause: 0.45]
N: The strong answer names where the real limits are,
[reveal: v-007]
[pause: 0.45]
N: and treats unknown and returned as ordinary states.
[reveal: v-008]
[pause: 0.45]
C: I'll keep one sentence in front of everything: settled is not final for a bank debit.
[reveal: v-009]
[pause: 0.45]
C: Most of the design follows from taking that seriously.
[pause: 1.0]

[slide: v-010]
[pause: 0.7]
V: In loan servicing, throughput is never the problem; correctness over months is. So the design is an immutable double-entry ledger, a payment state machine that admits unknown and returned, a scheduler bounded by the rail, and a daily three-way reconciliation.
[pause: 1.0]
C: Concretely: ledger lines that are never edited, with balances as a projection. Idempotency keys at three layers. A day planned backwards from the bank's cut-off. And every morning, a check that our books agree with the processor's and the bank's, with an owner for every difference.
[pause: 1.6]

[slide: v-011]
[pause: 0.6]
C: The order.
C: Requirements and scope, then the numbers, then a short theory chapter the design can lean on.
[reveal: v-012]
[pause: 0.45]
C: Then the A-P-I and the data model, and a design in three versions, each one answering the objection to the one before.
[reveal: v-013]
[pause: 0.45]
C: Most of the time goes to eight challenges that break the design, in an order where each fix creates the next question.
C: Then a build cost, and a recap.
[pause: 0.8]

[pause: 1.4]

## 1 Requirements and scope

[slide: v-014]
[pause: 1.2]
C: Before I draw anything, seven questions. Each answer changes the design, and I'll say how.
[pause: 1.8]

[slide: v-015]
[pause: 0.6]
C: How big is the portfolio?
I: Five million active loans, with three to twelve monthly instalments each.
C: So about five million collections a month, and each loan lives up to a year.
C: Long enough for every slow failure in this domain to happen.
[pause: 0.6]

[slide: v-016]
[pause: 0.6]
C: Which payment rails do we collect on?
I: Bank debit for eighty percent, card for twenty.
I: Card numbers are stored as tokens at the processor.
C: Two rails that behave very differently.
C: A card answers in seconds.
C: A bank debit answers in days and can be returned weeks later.
C: And because the tokens live at the processor, I can't move card customers to another processor in a hurry.
C: That will matter on the worst day.
[pause: 0.6]

[slide: v-017]
[pause: 0.6]
C: Are due dates spread across the month?
I: No.
I: They cluster.
I: Six hundred thousand collections fall on the first.
C: Then I need to plan one day very carefully.
C: I'll size it in a minute, and I suspect it is smaller than it sounds.
[pause: 0.6]

[slide: v-018]
[pause: 0.6]
C: What limits do the rails put on us?
I: The card processor's contract allows a hundred requests a second.
I: Bank debit files have a daily cut-off.
I: Take two in the afternoon.
C: That is the most important answer so far.
C: The limit is not my database.
C: It is a contract, and a clock on the bank's side.
[pause: 0.6]

[slide: v-019]
[pause: 0.6]
C: How do refunds work?
I: Merchants refund in full or in part, at any point during the loan.
C: So a refund changes a schedule under a live loan, possibly while a payment is in flight.
C: The terms have to say what happens.
[pause: 0.6]

[slide: v-020]
[pause: 0.6]
C: What are the audit requirements?
I: Every cent explained for seven years, and the month-end close done in two days.
C: Explained means a balance is a sum of records nobody edits.
C: And a two-day close means differences have to be found daily, not at the end of the month.
[pause: 0.6]

[slide: v-021]
[pause: 0.6]
C: What must never happen, in priority order?
C: I'd propose: first, charging a customer twice for one instalment.
C: Second, a cent we can't explain.
C: Third, penalising a customer for our own failure.
C: Lateness comes after all three.
I: Your call.
I: I agree with that order.
C: That order settles arguments later.
C: When speed and correctness conflict, correctness wins, and a collection can wait a day.
[pause: 0.6]

[slide: v-022]
[pause: 0.6]
C: Functionally, five things.
C: One, schedule: a booked loan becomes a schedule of instalments, from a versioned set of terms.
[reveal: v-023]
[pause: 0.45]
C: Two, collect: on each due date, by bank debit or card, with retries and late fees as policy says.
[reveal: v-024]
[pause: 0.45]
C: Three, adjust: refunds, extra payments and early payoff, which re-amortise the loan or shorten it, as the terms say.
[reveal: v-025]
[pause: 0.45]
C: Four, absorb returns: a debit that comes back days or weeks later reverses a collection.
[reveal: v-026]
[pause: 0.45]
C: Five, reconcile: our ledger against the processor and the bank, every day.
C: Each of these gets a numbered flow later.
[pause: 0.8]

[slide: v-027]
[pause: 0.6]
C: The promises, all initial targets.
C: Zero customers charged twice for one instalment.
[reveal: v-028]
[pause: 0.45]
C: Zero unexplained differences at month-end.
[reveal: v-029]
[pause: 0.45]
C: The day's debit file submitted by half past ten, with the cut-off at two, so a failed submission still has time to be fixed.
[reveal: v-030]
[pause: 0.45]
C: Ninety-nine percent of unknown outcomes resolved within an hour.
C: And every ledger line kept, and explainable, for seven years.
[pause: 0.8]

[slide: v-031]
[pause: 0.6]
C: In scope: schedules, both rails with their retries and returns, refunds, late fees, early payoff, the ledger, reconciliation, and notices to customers as events.
C: Out of scope, said aloud. Origination and underwriting, which is its own question. Outside collections agencies, and hardship programmes beyond a simple pause flag. Statement design and tax reporting. Paying merchants. And how the loans are funded or sold. Each of those consumes our events, but none of them changes the core.
[pause: 0.8]

[slide: v-032]
[pause: 0.7]
C: So the core is four things. A ledger that is never edited. A payment state machine with unknown and returned in it. A scheduler whose limit is the rail. And reconciliation against the outside world. Everything else serves those four.
[pause: 1.6]

[pause: 1.4]

## 2 Estimates

[slide: v-033]
[pause: 1.2]
C: Numbers next. Each is arithmetic from what the interviewer said, carries a label, and ends with the decision it drives. I'll say it once for the chapter: the rates and amounts are illustrative, not any company's figures.
[pause: 1.8]

[slide: v-034]
[pause: 1.0]
C: Six hundred thousand collections, spread over four hours: six hundred thousand divided by fourteen thousand four hundred seconds.
[reveal: v-035]
[pause: 0.45]
C: About forty-two a second.
[reveal: v-036]
[pause: 0.45]
C: Decision: that is nothing for one relational database.
[reveal: v-037]
[pause: 0.45]
C: The database can be the work queue, and a message broker is not needed for load.
C: If I add one later, it is for another reason.
[pause: 1.0]

[slide: v-038]
[pause: 1.0]
C: Twenty percent of six hundred thousand is a hundred and twenty thousand card charges.
[reveal: v-039]
[pause: 0.45]
C: At the contract's hundred a second, twenty minutes at the very least.
[reveal: v-040]
[pause: 0.45]
C: I'd run at ninety a second, to leave headroom for retries and queries: about twenty-two minutes.
[reveal: v-041]
[pause: 0.45]
C: Decision: a token bucket per rail, set below the contract.
C: The card window is something we plan, not a burst we hope survives.
[pause: 1.0]

[slide: v-042]
[pause: 1.0]
C: The other four hundred and eighty thousand are bank debits.
[reveal: v-043]
[pause: 0.45]
C: They don't go one by one: they go in a file.
[reveal: v-044]
[pause: 0.45]
C: At about ninety-four bytes a record, forty-five megabytes.
[reveal: v-045]
[pause: 0.45]
C: Decision: the file is a batch, built hours before the cut-off, validated, submitted, and only done when the bank acknowledges it.
C: A missed cut-off moves half a million collections by a day.
[pause: 1.0]

[slide: v-046]
[pause: 1.0]
C: Money.
C: Say the average instalment is a hundred and fifty dollars: a twelve-hundred dollar loan in eight payments.
[reveal: v-047]
[pause: 0.45]
C: Six hundred thousand of them is about ninety million dollars on the first.
[reveal: v-048]
[pause: 0.45]
C: A tenth of a percent wrong is ninety thousand dollars, and a lot of angry customers.
C: Decision: correctness beats speed.
[reveal: v-049]
[pause: 0.45]
C: Being a day late is cheap.
C: Being wrong is not.
[pause: 1.0]

[slide: v-050]
[pause: 1.0]
C: Returns.
C: Say three percent of bank debits come back for insufficient funds.
[reveal: v-051]
[pause: 0.45]
C: That is fourteen thousand four hundred returns from the first alone, arriving on the second and third days.
[reveal: v-052]
[pause: 0.45]
C: Plus a trickle of unauthorised returns for sixty days after that.
[reveal: v-053]
[pause: 0.45]
C: Decision: returns are a daily workload with their own pipeline and owner, not an exception handler.
[pause: 1.0]

[slide: v-054]
[pause: 1.0]
C: Unknown outcomes.
C: Say two in a thousand card charges time out.
[reveal: v-055]
[pause: 0.45]
C: On the first that is about two hundred and forty.
C: Small, but every one of them is a customer who might have been charged, and might be charged again if we guess.
[reveal: v-056]
[pause: 0.45]
C: Decision: a resolver service that ends every unknown by asking the processor, never by guessing.
[pause: 1.0]

[slide: v-057]
[pause: 1.0]
C: The ledger's size.
C: About four lines per loan per month: two for the collection, two for the interest accrued at month-end.
[reveal: v-058]
[pause: 0.45]
C: Five million loans: twenty million lines a month.
[reveal: v-059]
[pause: 0.45]
C: Over eighty-four months, at two hundred bytes a line, about three hundred and forty gigabytes.
[reveal: v-060]
[pause: 0.45]
C: Decision: that fits one well-run relational database, partitioned by month.
C: No sharding.
C: I keep real transactions and real constraints, which is exactly what a ledger needs.
[pause: 1.0]

[slide: v-061]
[pause: 1.0]
C: One trap.
C: Posting interest every day would be five million loans, times thirty days, times two lines: three hundred million lines a month.
[reveal: v-062]
[pause: 0.45]
C: Fifteen times the ledger, for no information.
C: So interest is accrued by calculation, from the balance and the rate, and posted when something happens: a payment, a payoff, a refund, and month-end.
[reveal: v-063]
[pause: 0.45]
N: Noticing that, unprompted, is the kind of depth this round looks for.
C: That is the numbers.
C: Next, theory.
[pause: 1.0]

[pause: 1.4]

## 3 Theory

[slide: v-064]
[pause: 1.2]
C: A short theory chapter before any design, so the design can lean on it. Six parts: what loan servicing is and is not, the properties, the central tension, seven mechanisms, an options matrix, and the failure catalogue. Every slide here carries a theory badge.
[pause: 1.8]

[slide: v-065]
[pause: 0.7]
V: A loan servicing system turns each loan's terms into a schedule, collects each amount once through rails that answer in days and can reverse weeks later, records every movement as balanced, immutable lines, and proves every day that its books agree with the bank.
[pause: 1.0]
C: Every clause does work. Terms into a schedule: the rules are versioned data, not code paths. Once: idempotency, not exactly-once delivery, which does not exist across a network. Answer in days and reverse weeks later: pending, unknown and returned are states. Balanced and immutable: double entry, corrections by reversal. And proves daily: reconciliation is a component, not an audit at year end.
[pause: 1.6]

[slide: v-066]
[pause: 0.6]
C: Four confusions.
C: It is not a payment gateway: a gateway turns one intent into one payment in seconds.
C: Servicing drives many payments over months, against a schedule that keeps changing.
[reveal: v-067]
[pause: 0.45]
C: It is not a cron job: a cron job fires work, but it does not know what was attempted, what is pending, or what came back.
[reveal: v-068]
[pause: 0.45]
C: A ledger is not a balance table: a balance is a sum, and a number updated in place cannot explain itself.
[reveal: v-069]
[pause: 0.45]
C: And settled is not final: a bank debit can be returned after it settles, so final is a later point, defined by the network's rules.
[pause: 0.8]

[slide: v-070]
[pause: 0.6]
C: Three safety properties, things that must never happen.
C: S-one: one instalment collected twice.
C: S-two: a ledger transaction that doesn't sum to zero in whole cents, or a line that gets edited.
C: S-three: a customer penalised beyond policy, or for our own failure.
C: And three liveness properties, things that must eventually happen.
[reveal: v-071]
[pause: 0.45]
C: L-one: every due instalment is attempted on its due date, before the cut-off.
C: L-two: every payment leaves unknown and pending, within a bound.
C: L-three: every difference with the outside becomes a break with an owner, within a day.
C: Every fix from here on says which one it serves.
C: Most designs are silent on liveness.
[pause: 0.8]

[slide: v-072]
[pause: 1.0]
C: The central tension is when money is final, and who decides.
C: In seconds, a card answer, or nothing.
[reveal: v-073]
[pause: 0.45]
C: In a day or two, the debit settles.
[reveal: v-074]
[pause: 0.45]
C: Two banking days, an insufficient-funds return.
[reveal: v-075]
[pause: 0.45]
C: Sixty days, an unauthorised return.
[reveal: v-076]
[pause: 0.45]
C: Months, refunds and card disputes.
[reveal: v-077]
[pause: 0.45]
C: And every day, the bank's own view, which we must match.
[reveal: v-078]
[pause: 0.45]
C: Finance wants cash recognised as early as possible.
C: Risk would rather wait sixty days.
C: The design that serves both posts the cash at settlement, and reports the exposure by age.
C: Instant payment rails, spreading since twenty twenty-three, remove some pending states, but not returns, and not reconciliation.
[pause: 1.0]

[slide: v-079]
[pause: 0.6]
C: Mechanism one, the immutable double-entry ledger.
C: It protects S-two and the audit.
[reveal: v-080]
[pause: 0.45]
C: Every movement is two or more lines that sum to zero in whole cents, inserted and never updated.
C: And here I correct a common line: never store a balance is too strict.
C: I keep a balance row, updated in the same commit, at a version, so it is fast to read and always provable from the lines.
[reveal: v-081]
[pause: 0.45]
C: It rules out balances nobody can explain.
[reveal: v-082]
[pause: 0.45]
C: It costs storage that only grows, and a reversing transaction for every mistake.
[pause: 0.8]

[slide: v-083]
[pause: 0.6]
C: Mechanism two, the payment state machine, with unknown and returned in it.
C: It protects S-one and L-two.
[reveal: v-084]
[pause: 0.45]
C: A timeout goes to unknown, which has its own exits.
C: A return moves a settled payment to returned and posts a reversal.
[reveal: v-085]
[pause: 0.45]
C: It rules out the double charge that follows treating a timeout as a failure, and a return that has nowhere to go.
[reveal: v-086]
[pause: 0.45]
C: It costs more states to test, and pending shown to customers for days.
[pause: 0.8]

[slide: v-087]
[pause: 0.6]
C: Mechanism three, idempotency at three layers.
C: It protects S-one.
[reveal: v-088]
[pause: 0.45]
C: The ledger transaction carries a unique key built from the loan, the instalment and the attempt.
C: The same key goes to the processor, so a resend returns the first result.
[reveal: v-089]
[pause: 0.45]
C: And a unique index allows one open intent per instalment.
C: Three layers, three different duplicates ruled out.
[reveal: v-090]
[pause: 0.45]
C: It costs one discipline: retrying the same attempt reuses its key.
C: Only a new decision to try again gets a new attempt number.
[pause: 0.8]

[slide: v-091]
[pause: 0.6]
C: Mechanism four, the database as the queue.
C: It protects L-one.
[reveal: v-092]
[pause: 0.45]
C: Due items are rows.
C: Workers claim batches with a skip-locked query, so no two workers take the same row, and write the payment intent and an outbox row in the same commit.
[reveal: v-093]
[pause: 0.45]
C: A sweeper returns claims that went stale.
C: It rules out lost work and work done twice.
[reveal: v-094]
[pause: 0.45]
C: It costs some polling, and a sweeper.
[pause: 0.8]

[slide: v-095]
[pause: 0.6]
C: Mechanism five, a rail budget.
C: It protects L-one, and S-three, because declines caused by our own throttling would be our fault.
[reveal: v-096]
[pause: 0.45]
C: A token bucket per rail set below the contract, a day plan worked backwards from the cut-off, and a pause switch per rail.
[reveal: v-097]
[pause: 0.45]
C: It rules out a midnight burst that the processor throttles into declines, and a missed cut-off.
[reveal: v-098]
[pause: 0.45]
C: It costs planning, and some product work to spread due dates.
[pause: 0.8]

[slide: v-099]
[pause: 0.6]
C: Mechanism six, policy as versioned data.
C: It protects S-three and the audit.
[reveal: v-100]
[pause: 0.45]
C: The allocation order, the retry schedule, late fees and how refunds land are rules with versions and named owners, and every posting records the version it used.
[reveal: v-101]
[pause: 0.45]
C: It rules out behaviour nobody can explain.
[reveal: v-102]
[pause: 0.45]
C: It costs a rules component, and owners in risk and legal who sign off changes.
[pause: 0.8]

[slide: v-103]
[pause: 0.6]
C: Mechanism seven, three-way reconciliation.
C: It protects L-three.
[reveal: v-104]
[pause: 0.45]
C: The ledger says what it expects.
C: The processor's report and the bank statement are matched to it, line by line, by reference first.
C: Every difference becomes a typed break with an owner and an age.
[reveal: v-105]
[pause: 0.45]
C: It rules out silent divergence, and the plug at month-end that makes totals agree.
[reveal: v-106]
[pause: 0.45]
C: It costs a pipeline, a console, and people.
[pause: 0.8]

[slide: v-107]
[pause: 1.0]
C: Now the options, each with the failure that rules it out.
C: Three that look reasonable.
C: A, a cron job at midnight, a balance column, retry on any error.
C: It fails at the first timeout and retry, and the processor throttles the midnight burst.
[reveal: v-108]
[pause: 0.45]
C: B, a message broker: six hundred thousand messages fanned out to workers, no state machine.
C: A crash and redelivery charges again, unknown and returned have nowhere to live, and it solved a load problem we don't have.
[reveal: v-109]
[pause: 0.45]
C: C, an event-sourced loan in a log.
C: It explains every cent, but a refund or payoff needs a current balance right now, and every correction becomes a replay.
[pause: 1.0]

[slide: v-110]
[pause: 1.0]
C: D is the pick: a relational ledger, the state machine, the database as the queue, a rail budget, policy as data, and three-way reconciliation.
C: It only fails when a processor gives us no way to ask about our own key, and then the settlement file decides, a day late.
[reveal: v-111]
[pause: 0.45]
C: E, buy a servicing platform.
C: For a small book with standard products, that is the honest first version.
C: It fails when the product needs its own refund rules, or the company must keep its own books of record.
[pause: 1.0]

[slide: v-112]
[pause: 0.6]
C: What D buys is never guessing.
C: A retry is harmless, an unknown has an exit, a return has a place to land, every balance is a sum, and the bank is checked daily.
[reveal: v-113]
[pause: 0.45]
C: What it gives up: more states to test, a reconciliation team, pending on customer statements for days, and every product change becomes a policy version someone must own.
[reveal: v-114]
[pause: 0.45]
C: I'd say that cost out loud, because it lands on product and finance.
[pause: 0.8]

[slide: v-115]
[pause: 1.0]
C: Last, the failure catalogue, which becomes the challenge list.
C: A card charge times out, the first half of the crux.
[reveal: v-116]
[pause: 0.45]
C: Six hundred thousand on one morning.
[reveal: v-117]
[pause: 0.45]
C: A settled debit that comes back, the second half.
[reveal: v-118]
[pause: 0.45]
C: A refund that changes the schedule.
[reveal: v-119]
[pause: 0.45]
C: A payoff while a debit is in flight.
[reveal: v-120]
[pause: 0.45]
C: A month-end that doesn't match.
[reveal: v-121]
[pause: 0.45]
C: The card processor down on the first.
[reveal: v-122]
[pause: 0.45]
C: And nobody noticing until close.
[pause: 1.0]

[pause: 1.4]

## 4 API and entities

[slide: v-123]
[pause: 1.2]
C: The A-P-I and the data model before the boxes. Every call carries a tag: the requirement it serves and the entity it reads or writes.
[pause: 1.8]

[slide: v-124]
[pause: 1.0]
C: Schedule. Origination emits loan booked: the loan I-D, the principal in cents, the terms version, the first due date, and the rail with the customer's debit mandate. Twelve hundred dollars, eight instalments of a hundred and fifty.
C: It creates the first schedule version, with due dates moved to business days, because a bank debit can't take effect on a weekend or a bank holiday. And the booking transaction in the ledger. The event is idempotent by loan I-D: delivered twice, it creates nothing new.
[pause: 1.0]

[slide: v-125]
[pause: 1.0]
C: Three calls change a live loan. A payment from the customer, with an idempotency key. A refund from the merchant, where the merchant's own refund I-D is the key, so a merchant retry can't refund twice.
C: And the payoff quote, which returns a quote I-D, an amount, a validity date, and, importantly, a list of payments still in flight. Challenge five is about why that list is there.
[pause: 1.0]

[slide: v-126]
[pause: 1.3]
C: Behind every collection is this state machine. Scheduled, submitted, pending, settled. From submitted, a timeout goes to unknown, and from unknown we query by the same key, never resend. From pending, a decline. And the dashed red arrow: settled to returned, up to sixty days later for a bank debit.
C: From returned, an insufficient-funds return can become retry due, at most twice more, by the network's rules. Any transition not drawn here is rejected by the code.
[pause: 1.1]

[slide: v-127]
[pause: 1.0]
C: What crosses to the outside. For cards, one call per attempt, carrying our key: loan, instalment, attempt. And a query by that same key. For the bank, files: we submit a debit file and wait for its acknowledgement, and we import returns, settlement reports and statements. Every file is stored unchanged before anything reads it, so a bug in parsing can be replayed.
[pause: 1.0]

[slide: v-128]
[pause: 1.3]
C: The conceptual model.
[reveal: v-129]
[pause: 0.45]
C: A loan has schedule versions;
[reveal: v-130]
[pause: 0.45]
C: a refund or a payoff creates a new one.
[reveal: v-131]
[pause: 0.45]
C: A schedule version contains instalments.
[reveal: v-132]
[pause: 0.45]
C: An instalment is collected by payment intents,
[reveal: v-133]
[pause: 0.45]
C: at most one open at a time.
[reveal: v-134]
[pause: 0.45]
C: A loan posts ledger transactions,
[reveal: v-135]
[pause: 0.45]
C: each containing lines.
[reveal: v-136]
[pause: 0.45]
C: And an intent posts the transactions for its result.
[reveal: v-137]
[pause: 0.45]
C: The double borders are weak entities:
[reveal: v-138]
[pause: 0.45]
C: a schedule version only exists inside its loan,
[reveal: v-139]
[pause: 0.45]
C: and a line only inside its transaction.
[pause: 1.1]

[slide: v-140]
[pause: 1.3]
C: The physical model.
[reveal: v-141]
[pause: 0.45]
C: Ledger lines, partitioned by month, insert only.
[reveal: v-142]
[pause: 0.45]
C: Ledger transactions with a unique idempotency key and the policy version they used.
[reveal: v-143]
[pause: 0.45]
C: The account balance row, with a version, updated in the same commit.
[reveal: v-144]
[pause: 0.45]
C: Due items indexed by date, shard and status, which is the work queue.
[reveal: v-145]
[pause: 0.45]
C: Payment intents with a partial unique index: one open intent per instalment.
[reveal: v-146]
[pause: 0.45]
C: And the outbox.
[pause: 1.1]

[slide: v-147]
[pause: 1.3]
C: A worked example. Booking a twelve-hundred dollar loan: we are owed twelve hundred of principal, we owe the merchant eleven sixty-four, and we earned thirty-six of discount fee. An instalment collected by bank debit first moves a hundred and fifty into cash clearing, while it is pending. When it settles, clearing moves to cash at the bank.
C: A return is a new transaction reversing those last lines. Nothing here is ever edited.
[pause: 1.1]

[slide: v-148]
[pause: 1.0]
C: Posting, in code. The transaction row carries the key, with a unique constraint, so a retry fails at the first insert and the first result is returned. Two lines that sum to zero. And the balance row updated in the same commit, at the version we read, so two postings to one loan cannot interleave. A deferred check rejects the commit unless the lines sum to zero.
C: Lines are facts, and never change. The balance is a projection, and provable from them.
[pause: 1.0]

[slide: v-149]
[pause: 0.6]
C: Three rules that are cheap to say and expensive to forget.
C: Never a float: integer cents, and how an instalment rounds is a rule, with the remainder on the last payment.
[reveal: v-150]
[pause: 0.45]
C: Business days: a due date on a weekend or a bank holiday takes effect the next business day, and late fees count from there.
[reveal: v-151]
[pause: 0.45]
C: And two dates on every line: when it happened, and when we booked it, so a return that arrives today never edits last month.
[pause: 0.8]

[pause: 1.4]

## 5 High-level design

[slide: v-152]
[pause: 1.2]
C: Now the design, in three versions, each introduced by the objection to the one before. The boxes never move: every later picture is a view of the same baseline.
[pause: 1.8]

[slide: v-153]
[pause: 1.3]
C: Version one.
[reveal: v-154]
[pause: 0.45]
C: Origination books a loan through the servicing A-P-I.
[reveal: v-155]
[pause: 0.45]
C: At midnight,
[reveal: v-156]
[pause: 0.45]
C: a job in the schedule service loops over every loan due today,
[reveal: v-157]
[pause: 0.45]
C: charges each at the rails, and updates the loan's balance column.
[reveal: v-158]
[pause: 0.45]
C: It is the simplest thing that works, and many first versions look exactly like this.
[pause: 1.1]

[slide: v-159]
[pause: 1.0]
C: The objection, as a trace.
C: At midnight the job sends two thousand card charges a second against a contract of a hundred.
[reveal: v-160]
[pause: 0.45]
C: Three seconds later the processor throttles ninety-five percent, and the job retries them at once.
[reveal: v-161]
[pause: 0.45]
C: At eight, one charge times out and is retried as a new charge: charged twice.
[reveal: v-162]
[pause: 0.45]
C: On the third, a debit comes back, and the balance column was already reduced: there is nowhere to post it.
[reveal: v-163]
[pause: 0.45]
C: And at year end, an auditor asks why a balance is what it is, and there is no history.
[pause: 1.0]

[slide: v-164]
[pause: 1.3]
C: Version two.
[reveal: v-165]
[pause: 0.45]
C: The database becomes the servicing database: the ledger with its projection, due items, payment intents and an outbox.
C: The schedule service claims due items and writes intents and outbox rows in one commit.
[reveal: v-166]
[pause: 0.45]
C: A new dispatcher drains the outbox under a budget per rail, sends each charge with its key, and posts the result.
C: A timeout now leaves the intent unknown instead of failed, and the rail sets the pace instead of a midnight burst.
[pause: 1.1]

[slide: v-167]
[pause: 0.6]
C: The objection to version two.
C: Inside the database it is correct.
C: But settlements and returns arrive as files days later, and nothing reads them.
[reveal: v-168]
[pause: 0.45]
C: Nothing ends an unknown: two hundred and forty on the first, pending forever.
[reveal: v-169]
[pause: 0.45]
C: Refunds and payoffs change schedules, while allocation and fees are buried in code.
[reveal: v-170]
[pause: 0.45]
C: And our books can differ from the bank's without anyone noticing.
[pause: 0.8]

[slide: v-171]
[pause: 1.3]
C: Version three closes those loops.
[reveal: v-172]
[pause: 0.45]
C: File ingest takes the bank's and processor's files and posts settlements and reversals.
[reveal: v-173]
[pause: 0.45]
C: A resolver asks the processor about every unknown, by the same key, and hands the answer to the dispatcher.
[reveal: v-174]
[pause: 0.45]
C: A policy service holds terms, allocation, retry and fee rules as versioned data.
[reveal: v-175]
[pause: 0.45]
C: Reconciliation matches all three views and gives breaks to finance operations.
[reveal: v-176]
[pause: 0.45]
C: And an outbox relay feeds customer notices.
[reveal: v-177]
[pause: 0.45]
C: This is the baseline.
C: Every picture from here on is a view of it.
[pause: 1.1]

[slide: v-178]
[pause: 1.0]
C: The collect path in code.
C: In one transaction: claim up to five hundred due rows with skip locked, open an intent for each, unique while open, and add an outbox row.
C: Then the dispatcher, under the rail's bucket, charges with the intent's key.
C: On a timeout it sets unknown and stops: the resolver takes over.
C: Otherwise it posts lines, balance and state in one commit, under the same key.
C: No branch guesses.
C: A crash at any line leaves a row that says how far we got.
[pause: 1.0]

[slide: v-179]
[pause: 1.3]
C: Requirement one, schedule, by the numbers.
[reveal: v-180]
[pause: 0.45]
C: One: origination emits loan booked to the servicing A-P-I.
[reveal: v-181]
[pause: 0.45]
C: Two: the A-P-I hands it to the schedule service.
[reveal: v-182]
[pause: 0.45]
C: Three: the schedule service asks policy for the terms version: how many instalments, the rounding rule, the allocation order.
[reveal: v-183]
[pause: 0.45]
C: Four: one transaction writes the schedule version, the due items and the booking lines.
[pause: 1.1]

[slide: v-184]
[pause: 1.3]
C: Requirement two, collect.
[reveal: v-185]
[pause: 0.45]
C: One: on the due date, the schedule service claims the row and commits the intent and its outbox row.
[reveal: v-186]
[pause: 0.45]
C: Two: the dispatcher drains the outbox, under the rail's budget.
[reveal: v-187]
[pause: 0.45]
C: Three: it sends the charge with its key, or puts the debit in the day's file.
[reveal: v-188]
[pause: 0.45]
C: Four: the result comes back.
[reveal: v-189]
[pause: 0.45]
C: Five: it posts the result: lines, the balance and the state, in one commit.
[pause: 1.1]

[slide: v-190]
[pause: 1.3]
C: Requirement three, adjust.
[reveal: v-191]
[pause: 0.45]
C: One: the merchant's refund, or the customer's payoff, reaches the A-P-I.
[reveal: v-192]
[pause: 0.45]
C: Two: it goes to the schedule service.
[reveal: v-193]
[pause: 0.45]
C: Three:
[reveal: v-194]
[pause: 0.45]
C: policy says how it lands: re-amortise or shorten, and the allocation order.
[reveal: v-195]
[pause: 0.45]
C: Four: one transaction writes the ledger lines and the new schedule version.
[reveal: v-196]
[pause: 0.45]
C: Five and six: the answer goes back.
[pause: 1.1]

[slide: v-197]
[pause: 1.3]
C: Requirement four, returns.
[reveal: v-198]
[pause: 0.45]
C: One: the bank's return file arrives and is stored raw.
[reveal: v-199]
[pause: 0.45]
C: Two: file ingest matches each return to its attempt and posts a reversing transaction, dated the day it arrived, and moves the instalment back to due.
[reveal: v-200]
[pause: 0.45]
C: Three: the outbox relay emits the event.
[reveal: v-201]
[pause: 0.45]
C: Four: the customer gets a notice saying what happens next.
[pause: 1.1]

[slide: v-202]
[pause: 1.3]
C: Requirement five, reconcile.
[reveal: v-203]
[pause: 0.45]
C: One: the processor's report and the bank's statement arrive and are stored raw.
[reveal: v-204]
[pause: 0.45]
C: Two: file ingest passes their lines to reconciliation.
[reveal: v-205]
[pause: 0.45]
C: Three: reconciliation reads the ledger's expectations for the day and matches line by line.
[reveal: v-206]
[pause: 0.45]
C: Four: every line that doesn't match becomes a break, with an owner, in front of finance operations.
[pause: 1.1]

[slide: v-207]
[pause: 1.3]
C: The C4 context.
[reveal: v-208]
[pause: 0.45]
C: The customer repays and asks for payoffs.
[reveal: v-209]
[pause: 0.45]
C: Merchants send refunds.
[reveal: v-210]
[pause: 0.45]
C: Origination books loans.
[reveal: v-211]
[pause: 0.45]
C: Our servicing system charges and queries at the card processor, sends debit files to the bank, and receives returns and statements from it.
[reveal: v-212]
[pause: 0.45]
C: Finance operations own the breaks and the close.
[reveal: v-213]
[pause: 0.45]
C: Notice that the processor and the bank each keep their own books of the same money.
[pause: 1.1]

[slide: v-214]
[pause: 1.3]
C: The containers.
[reveal: v-215]
[pause: 0.45]
C: The servicing A-P-I owns keys, refunds and quotes.
[reveal: v-216]
[pause: 0.45]
C: Schedule and collect owns due items and the state machine.
[reveal: v-217]
[pause: 0.45]
C: The servicing database holds the ledger,
[reveal: v-218]
[pause: 0.45]
C: intents and outbox, partitioned by month.
[reveal: v-219]
[pause: 0.45]
C: The dispatcher owns the rail budgets.
[reveal: v-220]
[pause: 0.45]
C: Below:
[reveal: v-221]
[pause: 0.45]
C: policy,
[reveal: v-222]
[pause: 0.45]
C: file ingest,
[reveal: v-223]
[pause: 0.45]
C: the resolver, and reconciliation, which reads expectations from the ledger.
[pause: 1.1]

[slide: v-224]
[pause: 1.3]
C: One card instalment as a sequence.
C: One, highlighted: the claim, the intent and the outbox row in one commit.
[reveal: v-225]
[pause: 0.45]
C: Two: the dispatcher drains the outbox at ninety a second.
[reveal: v-226]
[pause: 0.45]
C: Three: charge a hundred and fifty dollars with key coll, loan fifty-five thirty-one, instalment two, attempt one.
[reveal: v-227]
[pause: 0.45]
C: Approved in one point four seconds.
[reveal: v-228]
[pause: 0.45]
C: Four: one transaction sets settled, posts the lines and the balance.
[reveal: v-229]
[pause: 0.45]
C: A retry with the same key stops at the ledger's unique key.
[pause: 1.1]

[pause: 1.4]

## 5.1 Components and technologies

[slide: v-230]
[pause: 1.2]
C: Now one level down. Every container, with the technology I would run it on, and for each choice, the alternatives I rejected and why.
[pause: 1.8]

[slide: v-231]
[pause: 1.3]
C: The container view again, with one change: the type line now names the technology. I will walk it once, then defend each choice on its own slide.
[reveal: v-232]
[pause: 0.45]
C: Servicing API is Go, idempotency keys.
[reveal: v-233]
[pause: 0.45]
C: Schedule + collect is Go, state machine.
[reveal: v-234]
[pause: 0.45]
C: Policy is Versioned rules.
[reveal: v-235]
[pause: 0.45]
C: Servicing DB is PostgreSQL, by month.
[reveal: v-236]
[pause: 0.45]
C: File ingest is Batch, raw first.
[reveal: v-237]
[pause: 0.45]
C: Resolver is Scheduled worker.
[reveal: v-238]
[pause: 0.45]
C: Dispatcher is Go worker, token bucket.
[reveal: v-239]
[pause: 0.45]
C: Reconciliation is Batch, three-way.
[reveal: v-240]
[pause: 0.45]
C: The path between them..
[reveal: v-241]
[pause: 0.45]
C: The path between them..
[pause: 1.1]

[slide: v-242]
[pause: 1.3]
C: One level further down, inside the box the challenges drill most: the dispatcher, a Go worker.
[reveal: v-243]
[pause: 0.45]
C: The servicing database holds the intents and the outbox.
[reveal: v-244]
[pause: 0.45]
C: The outbox poller claims sends by shard, with skip locked, so two workers never take the same row.
[reveal: v-245]
[pause: 0.45]
C: Every send passes the rail budgets: a token bucket per rail, with a live rate that halves the moment the rail throttles us.
[reveal: v-246]
[pause: 0.45]
C: The day plan sets those rates: windows planned backwards from each rail's cut-off.
[reveal: v-247]
[pause: 0.45]
C: Card sends go through the card client, with our idempotency key on every call. A timeout becomes unknown, never failed.
[reveal: v-248]
[pause: 0.45]
C: It calls the card processor's A-P-I.
[reveal: v-249]
[pause: 0.45]
C: Bank debits go through the file builder, which checks counts and totals before anything leaves,
[reveal: v-250]
[pause: 0.45]
C: and sends the file to the bank before the cut-off.
[reveal: v-251]
[pause: 0.45]
C: The result poster writes the outcome to the ledger by key, in one commit,
[reveal: v-252]
[pause: 0.45]
C: and hands every unknown to the resolver, a separate worker.
[pause: 1.1]

[slide: v-253]
[pause: 1.0]
C: Ledger entries are double entry: each transaction's lines sum to zero, checked by a deferred constraint at commit. Payment intents are rows with a state, changed by conditional updates. The due-item queue is a table selected with row locks that skip rows already taken. The outbox row commits with the entry. Tables are partitioned by month, so old months become read-only and cheap.
[reveal: v-254]
[pause: 0.45]
C: Why PostgreSQL 16, partitioned by month, one writer to the ledger: A collection is a state change, a pair of balanced ledger entries and an event. They must commit together, and one writer to the ledger keeps the order simple.
[reveal: v-255]
[pause: 0.45]
C: Rejected: A message broker as the queue. A second system to keep consistent with the ledger. The table queue commits with the entry.
[reveal: v-256]
[pause: 0.45]
C: Multiple ledger writers. Ordering, locking and deadlock handling for no throughput we need.
[reveal: v-257]
[pause: 0.45]
C: A key-value store. No multi-row transaction, so balance and intent could disagree.
[pause: 1.0]

[slide: v-258]
[pause: 1.0]
C: The dispatcher takes due intents and spends tokens from the rail's bucket. The day is planned backwards from each rail's cut-off, with the largest and riskiest items first and a jittered spread. Each call carries our reference. If a rail is down the bucket stops, and intents wait instead of retrying in a storm.
[reveal: v-259]
[pause: 0.45]
C: Why Go worker, a token bucket per rail, a plan of the day: A bank-debit rail and a card processor have limits, cut-offs and a cost. Firing everything at midnight on the first would break them.
[reveal: v-260]
[pause: 0.45]
C: Rejected: Firing every due item at once. The first of the month would breach the bank limit and the processor's rate.
[reveal: v-261]
[pause: 0.45]
C: Retrying every failure immediately. A retry storm on a rail that is already struggling.
[pause: 1.0]

[slide: v-262]
[pause: 1.0]
C: The resolver selects unknown intents past a minimum age and asks the rail by our reference. It applies the answer with a conditional update from unknown. Backoff stretches from seconds to hours, and an intent that stays unknown for a day pages a person. The age of the unknown queue is a metric.
[reveal: v-263]
[pause: 0.45]
C: Why Scheduled worker, inquiry by reference, backoff, an alert at a deadline: A call that timed out may have moved money. Unknown is a state with an owner, and only an inquiry can end it.
[reveal: v-264]
[pause: 0.45]
C: Rejected: Retrying the original call. If it landed, the customer is charged twice.
[reveal: v-265]
[pause: 0.45]
C: Marking a timeout as failed. A debit that succeeded is shown as failed, and the loan is wrong.
[pause: 1.0]

[slide: v-266]
[pause: 1.0]
C: Each file is stored raw in object storage with a hash, then parsed by a batch job. Counts and totals are checked against the file's trailer before any line is applied. Each line is matched to an intent by reference, and applying a return is an idempotent ledger transaction. A file that fails a check is quarantined, not half applied.
[reveal: v-267]
[pause: 0.45]
C: Why Object storage for raw files, a batch parser, counts and totals checked first: Returns arrive weeks later, in files. A parse bug must never lose the original.
[reveal: v-268]
[pause: 0.45]
C: Rejected: Parsing on arrival. A bug loses the original, and a half-applied file is hard to unwind.
[reveal: v-269]
[pause: 0.45]
C: Streaming each line as it comes. Files are daily; a stream adds state for no freshness gain.
[pause: 1.0]

[slide: v-270]
[pause: 1.0]
C: A daily job matches every ledger entry to the rail's settlement line and to the bank statement by reference. Two-way agreement is a match; a line missing on one side, a different amount or a duplicate is a break. Breaks carry an age and an owner, and each resolution is a new ledger entry. A total that differs from the bank's by four hundred dollars is explained line by line, not plugged.
[reveal: v-271]
[pause: 0.45]
C: Why Batch pipeline over the ledger, the rail's file and the bank's statement, by reference: The ledger, the rail and the bank are three versions of the truth. Differences are breaks, and each break has an owner.
[reveal: v-272]
[pause: 0.45]
C: Rejected: Matching on amount and date alone. Equal payments on the same day are ambiguous.
[reveal: v-273]
[pause: 0.45]
C: A monthly reconciliation. Breaks age for weeks and the month-end close becomes an investigation.
[pause: 1.0]

[slide: v-274]
[pause: 1.0]
C: The policy service holds versioned terms: the schedule rules, the waterfall of interest, fees and principal, and the fee table. Every ledger entry records the policy version used. A refund in the middle of a loan is a transaction plus a new schedule version computed from the policy at that date.
[reveal: v-275]
[pause: 0.45]
C: Why A rules service, versioned terms, a payment waterfall, a fee table: Terms, the order in which a payment is applied and fees change with law and product. They must change without a deploy and be reproducible later.
[reveal: v-276]
[pause: 0.45]
C: Rejected: Terms in code. A deploy per change, and no way to reproduce what applied on a past date.
[reveal: v-277]
[pause: 0.45]
C: Terms in each service. Two services would apply different rules to one payment.
[pause: 1.0]

[slide: v-278]
[pause: 1.0]
C: Every write carries an idempotency key under a unique constraint. A payoff quote lists the principal, accrued interest and every intent in flight, with the quote's expiry. A payoff with a debit in flight either waits for the debit to resolve or nets it, and says which. A refund is a ledger transaction with a new schedule version, never an edit.
[reveal: v-279]
[pause: 0.45]
C: Why Go service, an idempotency key on every write, payoff quotes that list what is in flight: Customers and agents retry. A payoff quote that ignores a debit in flight is wrong the moment it is paid.
[reveal: v-280]
[pause: 0.45]
C: Rejected: Quoting from the ledger balance only. An in-flight debit changes the answer after the customer pays.
[reveal: v-281]
[pause: 0.45]
C: Editing the schedule in place. History must be append-only, or a dispute cannot be reproduced.
[pause: 1.0]

[slide: v-282]
[pause: 1.0]
C: The stack on one slide, as I would leave it on the whiteboard.
C: Servicing DB: PostgreSQL, one ledger writer.
C: Not Broker as queue; many writers.
C: State, entries and queue commit together.
[reveal: v-283]
[pause: 0.45]
C: Dispatcher: Token bucket per rail.
C: Not Fire at once; retry storm.
C: The day is planned, not fired.
[reveal: v-284]
[pause: 0.45]
C: Resolver: Inquiry by reference, backoff.
C: Not Retry call; mark failed.
C: Unknown has an owner and an age.
[reveal: v-285]
[pause: 0.45]
C: File ingest: Raw first; batch parse.
C: Not Parse on arrival; stream.
C: Replayable; checked first.
[reveal: v-286]
[pause: 0.45]
C: Reconciliation: Daily, three-way, by reference.
C: Not Amount and date; monthly.
C: Every break has an owner.
[reveal: v-287]
[pause: 0.45]
C: Policy: Versioned data, one service.
C: Not Terms in code.
C: Reproducible; no deploy.
[reveal: v-288]
[pause: 0.45]
C: Servicing API: Idempotent; quotes list in-flight.
C: Not Balance-only quote; in-place edit.
C: Retries safe; quote true.
[reveal: v-289]
[pause: 0.45]
N: Naming a product is not the signal.
N: Naming the property that rules out its rival is.
N: Interviewers go one level down on whichever box you name, so name only what you can defend.
[pause: 1.0]

[slide: v-290]
[pause: 0.6]
N: Before the challenges, swap seats. You are the interviewer now. Of everything on the last slide, which box would you push on, and what is the one question you would ask? Pause the video and pick one.
[pause: 3.0]

[slide: v-291]
[pause: 1.0]
N: Here is where interviewers usually go.
I: A worker takes a due item and crashes before finishing.
I: What happens to it?
[pause: 1.2]
N: The row lock is released with the transaction; the item is still due and another worker takes it.
N: The idempotent intent key makes a second attempt harmless.
[reveal: v-292]
[pause: 0.45]
N: The trap is marking taken before doing the work.
I: It is the first of the month and the card processor is down.
I: What does the dispatcher do?
[pause: 1.2]
N: Stop spending that rail's tokens, keep intents waiting, protect the customer from late fees, and resume slowly when it returns.
[reveal: v-293]
[pause: 0.45]
N: The trap is retrying in a storm.
I: A debit times out.
I: What is the state and what moves money next?
[pause: 1.2]
N: Unknown.
N: The resolver asks the rail by reference until it answers, and only that answer moves money.
[reveal: v-294]
[pause: 0.45]
N: The trap is a retry or a failed mark.
I: Our ledger says four hundred dollars more than the bank.
I: How do you find it?
[pause: 1.2]
N: Match line by line by reference across ledger, rail and bank; the break is a line missing or doubled on one side.
[reveal: v-295]
[pause: 0.45]
N: Fix it with a new entry.
N: The trap is a plug figure.
N: If you picked a box that is not on this list, good.
N: Write its probe down and answer it before you watch on.
[pause: 1.2]

[pause: 1.4]

## 5.2 When you don't need all this

[slide: v-296]
[pause: 1.2]
C: Before I break it, the simpler design, and the number where it stops being enough.
[pause: 1.8]

[slide: v-297]
[pause: 1.3]
C: The alternate path changes one box.
[reveal: v-298]
[pause: 0.45]
C: The ledger, the state machine with unknown and returned, and reconciliation all stay.
C: The dispatcher, marked alternate, becomes one scheduled job that walks the due items in order, one call at a time, and builds the file once a day.
[reveal: v-299]
[pause: 0.45]
C: What it gives up: there is no rate control, so the processor's throttling decides how fast we go, and there is no day plan, so a late file or a storm of retries costs a whole day.
C: What it keeps matters more: unknown and returned are still states, and reconciliation still runs.
C: The crossover, from the scale line.
[reveal: v-300]
[pause: 0.45]
C: One job at about ten card charges a second clears thirty-six thousand in an hour.
C: At twenty percent on card, that is about a hundred and eighty thousand collections due on the first.
C: The scale line has six hundred thousand, so this design would need three hours of card window and has no margin before the cut-off.
C: Illustrative numbers.
[pause: 1.1]

[slide: v-301]
[pause: 0.7]
V: Below about two hundred thousand collections on the busiest day, I'd ship one scheduled job. I would never ship without unknown, returned and reconciliation.
[pause: 1.6]

[pause: 1.4]

## 6 Bridge

[slide: v-302]
[pause: 1.2]
V: It works. The question now is where it breaks first.
[pause: 1.8]

[slide: v-303]
[pause: 1.3]
C: The baseline with its attack points marked.
C: The dispatcher and the rails, where a charge can time out, and where a whole morning has to fit under a contract.
C: File ingest, where settled payments come back.
[reveal: v-304]
[pause: 0.45]
C: The schedule service and the A-P-I, where refunds and payoffs change a live loan.
C: Reconciliation, where the bank disagrees.
C: Then the processor down on the busiest morning, and silence.
C: Eight challenges, each fix creating the next question.
[pause: 1.1]

[pause: 1.4]

## 7 Challenges

[slide: v-305]
[pause: 1.2]
C: Each challenge runs the same way: the question, the naive answer, a case with numbers, where it breaks, the fix and why it works. Then the interviewer pushes on the fix itself, and I say what I'd say in the room.
[pause: 1.8]

[pause: 1.4]

## 7.1 Challenge 1: The processor timed out

[slide: v-306]
[pause: 1.2]
N: Challenge one, the crux. A card charge times out, and the worker wants to retry.
[pause: 1.8]

[slide: v-307]
[pause: 0.6]
I: The processor times out on a card charge. Your worker retries. Was the customer charged twice?
[pause: 2.0]

[slide: v-308]
[pause: 1.3]
C: The naive answer: mark it failed and retry.
[reveal: v-309]
[pause: 0.45]
C: Look at the red arrows between the dispatcher and the rails.
[reveal: v-310]
[pause: 0.45]
C: A timeout is not an answer.
[reveal: v-311]
[pause: 0.45]
C: The request may have arrived and been approved, and we simply never heard.
C: If the retry goes out as a new attempt, with a new key, the processor has every reason to charge again.
[pause: 1.1]

[slide: v-312]
[pause: 1.0]
C: The trace.
C: At eight, instalment two of loan fifty-five thirty-one, a hundred and fifty dollars, goes out with key attempt one.
[reveal: v-313]
[pause: 0.45]
C: At three point two seconds the processor approves it.
[reveal: v-314]
[pause: 0.45]
C: At ten seconds the worker gives up and the naive design marks it failed.
[reveal: v-315]
[pause: 0.45]
C: At twelve seconds a retry goes out as attempt two, with a new key, and it is approved too.
[reveal: v-316]
[pause: 0.45]
C: Three hundred dollars for a hundred and fifty dollar instalment.
[reveal: v-317]
[pause: 0.45]
C: The numbers are illustrative, but approvals really do land after the caller has given up.
[pause: 1.0]

[slide: v-318]
[pause: 1.3]
C: The fix.
[reveal: v-319]
[pause: 0.45]
C: At the timeout the intent goes to unknown, not failed.
C: Then the new green box: the resolver asks the processor about the same key, after thirty seconds, two minutes and ten minutes.
[reveal: v-320]
[pause: 0.45]
C: And the rule: resending the same attempt reuses its key, so the processor returns the first result.
C: Only a definite decline lets us open attempt two.
[reveal: v-321]
[pause: 0.45]
C: Rejected: Treating a timeout as a failure.
C: The debit may have landed; unknown is a state and an inquiry ends it.
[pause: 1.1]

[slide: v-322]
[pause: 1.3]
C: As a sequence.
[reveal: v-323]
[pause: 0.45]
C: One: the charge with key attempt one.
[reveal: v-324]
[pause: 0.45]
C: No answer at ten seconds.
[reveal: v-325]
[pause: 0.45]
C: Two, highlighted: the intent goes to unknown.
[reveal: v-326]
[pause: 0.45]
C: Three: the resolver queries by the same key, and four, the processor says approved at three point two seconds.
[reveal: v-327]
[pause: 0.45]
C: The resolver posts it as settled, through the same ledger key, so it can only be posted once.
[reveal: v-328]
[pause: 0.45]
C: In the note: if the processor says not found after its safe window, we resend, with the same key.
[pause: 1.1]

[slide: v-329]
[pause: 1.0]
C: The resolver in code.
C: Query by key.
C: Approved: post it, idempotently.
C: Declined: mark it declined, and now a second attempt is allowed.
C: Not found, and older than the processor's safe window: send again, still with the same key.
C: Anything else: ask again later.
C: No path creates a second decision for one attempt, and even a wrong guess resends a key the processor will de-duplicate.
[pause: 1.0]

[slide: v-330]
[pause: 0.6]
I: The query says not found. You resend. Tomorrow's settlement file shows the first charge went through after all.
[pause: 2.0]

[slide: v-331]
[pause: 0.6]
C: With the same key, a processor that honours keys returns the first result, so usually there is no harm.
C: And not found should only count as final after the processor's documented window.
[reveal: v-332]
[pause: 0.45]
C: If it still happened, reconciliation finds two settled charges for one instalment the next morning, refunds the duplicate automatically, and counts it as an incident.
[reveal: v-333]
[pause: 0.45]
C: The honest limit: a processor that neither honours keys nor answers queries can only be checked by its file, a day late.
C: That is a reason to choose processors, and I'd say so to whoever negotiates the contract.
[pause: 0.8]

[slide: v-334]
[pause: 0.7]
V: If asked, I'd say: a timeout is not a failure. The intent goes to unknown, the resolver queries by the same key, and a resend reuses that key. The settlement file is the final arbiter.
[pause: 1.0]
N: Next: there are six hundred thousand of these on one morning.
[pause: 1.6]

[pause: 1.4]

## 7.2 Challenge 2: The morning of the 1st

[slide: v-335]
[pause: 1.2]
N: Challenge two. Six hundred thousand payments due on one day: where is the real limit?
[pause: 1.8]

[slide: v-336]
[pause: 0.6]
I: Six hundred thousand payments are due on the first. Walk me through that morning.
[pause: 2.0]

[slide: v-337]
[pause: 1.3]
C: Two naive answers.
[reveal: v-338]
[pause: 0.45]
C: A cron job at midnight, or, it's a thundering herd, so put a message broker in front.
[reveal: v-339]
[pause: 0.45]
C: Look where the red is: the schedule service and the dispatcher, and the arrow to the rails.
[reveal: v-340]
[pause: 0.45]
C: Forty-two a second never hurt the database.
C: The burst hits the processor's contract, and a file that has to reach the bank by two.
[pause: 1.1]

[slide: v-341]
[pause: 1.0]
C: The trace.
C: At midnight, two thousand card charges a second against a contract of a hundred.
[reveal: v-342]
[pause: 0.45]
C: Three seconds in, the processor throttles ninety-five percent, and the workers retry at once, which makes it worse.
[reveal: v-343]
[pause: 0.45]
C: Twenty minutes later, eighteen thousand charges are marked failed, and late fees are due tomorrow, for a failure that was ours.
[reveal: v-344]
[pause: 0.45]
C: And the debit file, built at five to two, fails validation on one bad record.
[reveal: v-345]
[pause: 0.45]
C: The cut-off passes.
C: Four hundred and eighty thousand collections slip a day.
[pause: 1.0]

[slide: v-346]
[pause: 1.3]
C: The fix: plan the day backwards from the cut-off.
[reveal: v-347]
[pause: 0.45]
C: The new green box, the day plan, hands each rail its budget.
[reveal: v-348]
[pause: 0.45]
C: The debit file is built at nine, validated, submitted by half past ten, and acknowledged by eleven, three hours before the cut-off, so a rejected file can be fixed and resent.
C: The card window opens at six, at ninety a second.
[reveal: v-349]
[pause: 0.45]
C: Rejected: Firing every due item at midnight on the first.
C: The bank-debit limit and the rail rate break; plan the day backwards from the cut-off.
[pause: 1.1]

[slide: v-350]
[pause: 1.3]
C: The day on one line. Card charges from six, a hundred and twenty thousand in twenty-two minutes. Soft declines retried around seven. The debit file built from nine and submitted by half past ten. The bank's acknowledgement by eleven. And the red line at two, with three hours of margin in front of it.
[pause: 1.1]

[slide: v-351]
[pause: 1.0]
C: The claim in code. Select up to five hundred due rows in one shard, lock them, and skip rows another worker has locked. Mark them claimed in the same statement, and in the same transaction open the intents and outbox rows. A worker that dies before the commit releases its locks. One that dies after is found by the sweeper, which returns claims with no intent. No distributed lock, and no broker.
[pause: 1.0]

[slide: v-352]
[pause: 1.3]
C: As a sequence.
[reveal: v-353]
[pause: 0.45]
C: Worker one claims five hundred rows in shard seven.
[reveal: v-354]
[pause: 0.45]
C: Worker two asks for the same shard and skips the locked rows.
[reveal: v-355]
[pause: 0.45]
C: Three, highlighted: per row, an intent and an outbox row, and commit.
[reveal: v-356]
[pause: 0.45]
C: If worker two dies before its commit, its rows are due again.
[reveal: v-357]
[pause: 0.45]
C: Four: the dispatcher drains the outbox, cards at ninety a second, debits into the nine o'clock file.
[pause: 1.1]

[slide: v-358]
[pause: 0.6]
I: At ten past six, the processor lowers your limit to fifty a second.
[pause: 2.0]

[slide: v-359]
[pause: 0.6]
C: The bucket's rate is live: a throttle response halves it at once.
C: By ten past six, fifty-four thousand are done, and the other sixty-six thousand at fifty a second take twenty-two minutes.
C: Done by six thirty-two, still hours before anything matters.
[reveal: v-360]
[pause: 0.45]
C: And the better fix is upstream: spread due dates when loans are created.
C: Let the customer choose a day, and default to the day of booking.
C: The peak shrinks at the source.
[pause: 0.8]

[slide: v-361]
[pause: 0.7]
V: If asked, I'd say: forty-two a second is nothing for a database. The limits are the processor's contract and the bank's cut-off, so I plan backwards from the cut-off, with a budget per rail.
[pause: 1.0]
N: The debits go out on time. A few days later, some come back.
[pause: 1.6]

[pause: 1.4]

## 7.3 Challenge 3: It settled, then it came back

[slide: v-362]
[pause: 1.2]
N: Challenge three, the second half of the crux. A debit that settled comes back.
[pause: 1.8]

[slide: v-363]
[pause: 0.6]
I: A bank debit settled on the second. On the third it comes back for insufficient funds. Another one comes back forty days later, as unauthorised.
[pause: 2.0]

[slide: v-364]
[pause: 1.3]
C: The naive answer: settled means paid, close the instalment, and retry anything that fails.
[reveal: v-365]
[pause: 0.45]
C: Look at file ingest.
[reveal: v-366]
[pause: 0.45]
C: The return has no state to land in,
[reveal: v-367]
[pause: 0.45]
C: the balance was already reduced, and automatically retrying an unauthorised debit breaks the bank network's rules.
[pause: 1.1]

[slide: v-368]
[pause: 1.0]
C: The trace.
C: On the first, instalment three of loan seventy-seven oh two goes in the debit file.
[reveal: v-369]
[pause: 0.45]
C: On the second it settles, and the naive design closes the instalment.
[reveal: v-370]
[pause: 0.45]
C: On the third, a return with code R-zero-one, insufficient funds.
C: There is no state for it, and the balance was already reduced.
[reveal: v-371]
[pause: 0.45]
C: Another loan's debit settled on the second.
C: On the eleventh of January, day forty, it returns as R-ten, unauthorised: the customer says they never agreed to it.
[reveal: v-372]
[pause: 0.45]
C: The naive design retries it automatically.
C: That breaks the rules, and turns a dispute into a complaint.
[pause: 1.0]

[slide: v-373]
[pause: 1.3]
C: The fix.
C: Settled moves to returned, a normal state.
[reveal: v-374]
[pause: 0.45]
C: File ingest posts a reversing transaction, dated the day the return arrived, never editing the original.
C: The instalment goes from paid back to due, with the reason.
[reveal: v-375]
[pause: 0.45]
C: Then policy decides: insufficient funds may be presented again at most twice, typically timed after payday.
C: Unauthorised is never retried: the customer is contacted, and a new authorisation is needed.
[reveal: v-376]
[pause: 0.45]
C: Rejected: Treating settled as final.
C: Returns arrive weeks later; RETURNED is a state and a reversal is a transaction.
[pause: 1.1]

[slide: v-377]
[pause: 1.3]
C: As a sequence.
C: One: the bank's return file, loan seventy-seven oh two, a hundred and fifty, code R-zero-one.
[reveal: v-378]
[pause: 0.45]
C: Two, highlighted: ingest matches it to the attempt by the trace number, and moves settled to returned.
[reveal: v-379]
[pause: 0.45]
C: Three: the reversing transaction dated the third, and the instalment back to due.
[reveal: v-380]
[pause: 0.45]
C: Four: policy says re-present, attempt two of at most three, after payday.
[reveal: v-381]
[pause: 0.45]
C: Five: a notice to the customer.
[reveal: v-382]
[pause: 0.45]
C: And in red: an R-ten on day forty is never re-presented.
[pause: 1.1]

[slide: v-383]
[pause: 1.0]
C: The rules as a table, because they are data.
C: Insufficient funds: back within two banking days, and may be presented again at most twice within a hundred and eighty days.
[reveal: v-384]
[pause: 0.45]
C: Account closed or not found: stop, and ask for a new payment method.
[reveal: v-385]
[pause: 0.45]
C: Unauthorised: up to sixty days, never retried.
[reveal: v-386]
[pause: 0.45]
C: And late fees, which are capped by law where the customer lives, and never charged for our own failures.
[reveal: v-387]
[pause: 0.45]
C: Engineering owns the mechanism.
C: Risk and legal own this table.
[pause: 1.0]

[slide: v-388]
[pause: 1.0]
C: The card rail has its own version of it came back: a dispute. Same mechanism, different clock.
[reveal: v-389]
[pause: 0.45]
C: The notice arrives, sometimes months after the charge, and the processor has already netted the money from our payout. The payment moves from settled to disputed.
[reveal: v-390]
[pause: 0.45]
C: The ledger gets a reversal dated today: the loan receivable goes back up, processor clearing goes down. Nothing is edited, and the instalment is due again.
[reveal: v-391]
[pause: 0.45]
C: The customer gets no late fee and no automatic re-collection on that instalment while it is disputed. A disputed amount is not a missed payment.
[reveal: v-392]
[pause: 0.45]
C: We send evidence by the network's deadline: the agreement, the schedule, the authorisation, the receipt. If we win, we re-post. If we lose, the instalment stays due and follows normal collections.
[reveal: v-393]
[pause: 0.45]
C: And reconciliation matches the payout's dispute line by dispute I-D, or it becomes the break in challenge six.
[reveal: v-394]
[pause: 0.45]
C: The scale, illustrative: one in a thousand of the hundred and twenty thousand card charges on the first is about a hundred and twenty disputes from that one day.
[pause: 1.0]

[slide: v-395]
[pause: 0.6]
I: Finance wants to recognise the cash on settlement day. Risk wants to wait sixty days. Who wins?
[pause: 2.0]

[slide: v-396]
[pause: 0.6]
C: Both, with the exposure on a report.
C: Cash is posted at settlement, because that is when the bank says it is cash, and a return is a later reversal, in the month it arrives.
[reveal: v-397]
[pause: 0.45]
C: And a daily report shows everything settled in the last sixty days, by age, against the observed return rate.
C: Risk prices that exposure.
C: Nobody's process waits on it.
[pause: 0.8]

[slide: v-398]
[pause: 0.7]
V: If asked, I'd say: settled is not final for a bank debit. A return is a state and a reversal dated when it arrives, and whether we retry is policy: never for unauthorised.
[pause: 1.0]
N: Returns move money backwards. So do refunds, but they also change the schedule.
[pause: 1.6]

[pause: 1.4]

## 7.4 Challenge 4: A refund in the middle of the loan

[slide: v-399]
[pause: 1.2]
N: Challenge four. A merchant refunds part of a purchase two payments in.
[pause: 1.8]

[slide: v-400]
[pause: 0.6]
I: After two instalments, the merchant refunds three hundred dollars of the twelve hundred. What changes?
[pause: 2.0]

[slide: v-401]
[pause: 1.3]
C: The naive answer: subtract three hundred from the balance.
[reveal: v-402]
[pause: 0.45]
C: Look at the schedule service.
[reveal: v-403]
[pause: 0.45]
C: The balance changed, but the schedule still says six more payments of a hundred and fifty.
[reveal: v-404]
[pause: 0.45]
C: The customer would pay nine hundred dollars on a six-hundred dollar debt.
[pause: 1.1]

[slide: v-405]
[pause: 1.0]
C: The trace.
C: Loan ninety-one hundred is booked in October: twelve hundred dollars in eight payments of a hundred and fifty.
[reveal: v-406]
[pause: 0.45]
C: Two are paid by November: nine hundred outstanding.
[reveal: v-407]
[pause: 0.45]
C: On the fourteenth the merchant refunds three hundred, and the balance column drops to six hundred.
[reveal: v-408]
[pause: 0.45]
C: But the schedule is untouched, and from December to May it collects six times a hundred and fifty: nine hundred dollars.
[reveal: v-409]
[pause: 0.45]
C: The customer overpaid three hundred, and the customer noticed before we did.
[pause: 1.0]

[slide: v-410]
[pause: 1.3]
C: The fix.
C: In the ledger, the merchant now owes us three hundred, and the loan's principal drops by three hundred, keyed by the merchant's refund I-D.
[reveal: v-411]
[pause: 0.45]
C: Then policy, the green box, applies the terms.
C: Re-amortise: the six remaining payments become a hundred each.
[reveal: v-412]
[pause: 0.45]
C: Or shorten: they stay at a hundred and fifty, and the loan ends after four.
C: Which one is a product and legal decision, written in the terms before any code.
[reveal: v-413]
[pause: 0.45]
C: Rejected: Editing the schedule in place for a refund.
C: History must be append-only; a refund is a transaction and a new schedule version.
[pause: 1.1]

[slide: v-414]
[pause: 1.0]
C: Every payment is also allocated, in an order policy sets.
[reveal: v-415]
[pause: 0.45]
C: Typically fees due, then interest due, then this instalment's principal, and anything extra reduces future principal.
[reveal: v-416]
[pause: 0.45]
C: It is one versioned rule,
[reveal: v-417]
[pause: 0.45]
C: applied by one piece of code, and every posting records the version.
[reveal: v-418]
[pause: 0.45]
C: So the ledger can always say why each cent went where it did.
[pause: 1.0]

[slide: v-419]
[pause: 1.3]
C: As a sequence.
[reveal: v-420]
[pause: 0.45]
C: One: the merchant refunds three hundred on loan ninety-one hundred, with its refund I-D.
[reveal: v-421]
[pause: 0.45]
C: Two: the terms, version three, say re-amortise.
[reveal: v-422]
[pause: 0.45]
C: Three, highlighted: the ledger transaction, keyed by that I-D, so a merchant retry posts nothing new.
[reveal: v-423]
[pause: 0.45]
C: Four: schedule version two, six payments of a hundred, from instalment three.
[reveal: v-424]
[pause: 0.45]
C: And the note: if instalment three is already in flight, it stays in flight, and allocation sorts it out when it settles.
[pause: 1.1]

[slide: v-425]
[pause: 0.6]
I: The customer has paid nine hundred. Now the merchant refunds the full twelve hundred.
[pause: 2.0]

[slide: v-426]
[pause: 0.6]
C: Then the loan's principal goes to zero, and the nine hundred the customer paid becomes money we owe them, in a customer payable account.
C: It is refunded to the original payment method within the days policy sets, and never held silently as credit.
[reveal: v-427]
[pause: 0.45]
C: On the merchant side, they owe us the twelve hundred back, and whether we return the thirty-six dollar discount fee is the merchant contract, also versioned.
[pause: 0.8]

[slide: v-428]
[pause: 0.7]
V: If asked, I'd say: a refund is a ledger transaction and a new schedule version. Re-amortise or shorten is a decision in the terms, and any overpayment goes back to the customer.
[pause: 1.0]
N: That one changed the future. The next one changes the loan while money is still moving.
[pause: 1.6]

[pause: 1.4]

## 7.5 Challenge 5: Paying off with a debit in flight

[slide: v-429]
[pause: 1.2]
N: Challenge five. The customer pays off early, but a debit from two days ago hasn't cleared.
[pause: 1.8]

[slide: v-430]
[pause: 0.6]
I: On the third, the customer pays off the loan early. Instalment three's debit from the first is still pending. What do you quote?
[pause: 2.0]

[slide: v-431]
[pause: 1.3]
C: The naive answer: quote the balance.
[reveal: v-432]
[pause: 0.45]
C: But the balance either counts the pending debit as paid, or it doesn't.
[reveal: v-433]
[pause: 0.45]
C: Look at the A-P-I.
[reveal: v-434]
[pause: 0.45]
C: Both choices are wrong some of the time.
C: One over-collects when the debit settles.
C: The other closes a loan that still owes money.
[pause: 1.1]

[slide: v-435]
[pause: 1.0]
C: The trace.
C: On the first, instalment three, a hundred and fifty dollars, goes in the debit file, with nine hundred outstanding before it.
[reveal: v-436]
[pause: 0.45]
C: On the third, quote A says nine hundred, ignoring the pending debit.
[reveal: v-437]
[pause: 0.45]
C: The customer pays by card, the debit settles too, and we've over-collected a hundred and fifty.
[reveal: v-438]
[pause: 0.45]
C: Quote B says seven hundred and fifty, counting the debit as paid.
C: The loan is closed and the merchant told.
[reveal: v-439]
[pause: 0.45]
C: On the fourth, the debit returns for insufficient funds.
C: Now a closed loan owes a hundred and fifty, and nobody has a process for that.
[pause: 1.0]

[slide: v-440]
[pause: 1.3]
C: The fix: a payoff quote is a statement about the future, so it lists what is in flight.
[reveal: v-441]
[pause: 0.45]
C: Quote q-thirty-one: seven hundred and fifty now, conditional on the hundred and fifty dollar debit clearing, valid until the fifth.
[reveal: v-442]
[pause: 0.45]
C: Paying it moves the loan to paid-pending, not closed.
C: If the debit clears, the loan closes.
C: If it returns, a hundred and fifty reopens as a single due item, with no late mark.
[reveal: v-443]
[pause: 0.45]
C: Rejected: Quoting the payoff from the ledger balance alone.
C: An in-flight debit changes it; the quote lists what is in flight.
[pause: 1.1]

[slide: v-444]
[pause: 1.3]
C: As a sequence.
C: One: the customer asks for a quote.
[reveal: v-445]
[pause: 0.45]
C: The answer: seven hundred and fifty now, the hundred and fifty debit listed, valid to the fifth.
[reveal: v-446]
[pause: 0.45]
C: Two: they pay against q-thirty-one, and the quote I-D is the idempotency key, so a double tap pays once.
[reveal: v-447]
[pause: 0.45]
C: Three, highlighted: the lines post, and the loan is paid-pending.
[reveal: v-448]
[pause: 0.45]
C: Four: if the return arrives, one due item of a hundred and fifty.
[reveal: v-449]
[pause: 0.45]
C: And if nothing comes back by the fifth, closed, lien released, and a notice.
[pause: 1.1]

[slide: v-450]
[pause: 1.0]
C: The rule as a table.
C: Nothing in flight: quote the full balance and close.
[reveal: v-451]
[pause: 0.45]
C: A card charge in flight: minutes, then close.
[reveal: v-452]
[pause: 0.45]
C: A bank debit in flight: a conditional quote, and close when the debit is past its insufficient-funds window.
[reveal: v-453]
[pause: 0.45]
C: A debit not yet sent: cancel it, quote the full balance, and close.
[reveal: v-454]
[pause: 0.45]
C: What is left is the sixty-day unauthorised window, and that is handled as a dispute, not by holding every loan open for two months.
[pause: 1.0]

[slide: v-455]
[pause: 0.6]
I: The day after the payoff, a merchant refund arrives on the same loan.
[pause: 2.0]

[slide: v-456]
[pause: 0.6]
C: The refund takes principal below zero.
C: The excess becomes customer payable, money we owe, and it is paid back automatically to the original method.
[reveal: v-457]
[pause: 0.45]
C: And every customer payable older than the policy's limit pages its owner.
C: Money we owe is never left sitting as a quiet credit.
[pause: 0.8]

[slide: v-458]
[pause: 0.7]
V: If asked, I'd say: a payoff quote lists what's in flight. The loan goes to paid-pending and closes only when nothing can still come back, and any overpayment is refunded automatically.
[pause: 1.0]
N: All these moving parts meet at month-end, when the bank sends its statement.
[pause: 1.6]

[pause: 1.4]

## 7.6 Challenge 6: Four hundred dollars more than the bank

[slide: v-459]
[pause: 1.2]
N: Challenge six. Month-end, and the ledger and the bank disagree.
[pause: 1.8]

[slide: v-460]
[pause: 0.6]
I: Month-end. The ledger says we collected four hundred dollars more than the bank received. Find it.
[pause: 2.0]

[slide: v-461]
[pause: 1.3]
C: The naive answer: compare the totals, and post a four-hundred dollar adjustment so the month can close.
[reveal: v-462]
[pause: 0.45]
C: Look at reconciliation.
[reveal: v-463]
[pause: 0.45]
C: A total is a sum of differences, and some of them cancel each other out.
[reveal: v-464]
[pause: 0.45]
C: One of the hidden ones may be a customer charged twice.
[pause: 1.1]

[slide: v-465]
[pause: 1.0]
C: The trace.
C: The ledger says ninety million and four hundred dollars collected in November.
[reveal: v-466]
[pause: 0.45]
C: The bank says ninety million.
[reveal: v-467]
[pause: 0.45]
C: Inside the four hundred: plus three hundred, two insufficient-funds returns on the bank statement for the thirtieth, whose return file only arrives on the first.
C: That is timing.
[reveal: v-468]
[pause: 0.45]
C: Plus a hundred, a card dispute the processor deducted from its payout, and we have no record of it.
[reveal: v-469]
[pause: 0.45]
C: And a pair that hides itself: plus a hundred and fifty, a card payment we think settled and the processor never settled.
[reveal: v-470]
[pause: 0.45]
C: Minus a hundred and fifty, a charge the processor did settle that we hold as declined.
C: That one is a customer charged twice.
C: In the total, those two cancel to zero.
[pause: 1.0]

[slide: v-471]
[pause: 1.3]
C: The fix: match every line, three ways, by reference.
[reveal: v-472]
[pause: 0.45]
C: The ledger produces what it expects.
[reveal: v-473]
[pause: 0.45]
C: The processor's report and the bank statement are matched to it by our reference, then by amount within a three-day window.
C: Every difference becomes a typed break: timing, missing in our ledger, missing at the processor, or a wrong amount.
[reveal: v-474]
[pause: 0.45]
C: Each one gets an owner and an age.
C: Rejected: Plugging the difference to the bank.
C: The break is a line missing or doubled; match every line three ways by reference.
[pause: 1.1]

[slide: v-475]
[pause: 1.3]
C: As a sequence.
[reveal: v-476]
[pause: 0.45]
C: One: the expectations for the thirtieth, by reference.
[reveal: v-477]
[pause: 0.45]
C: Two and three: the processor's report and the bank statement.
[reveal: v-478]
[pause: 0.45]
C: Then the match, by reference first.
[reveal: v-479]
[pause: 0.45]
C: Four, highlighted: four breaks go to finance operations, one timing and three real, each with an owner.
[reveal: v-480]
[pause: 0.45]
C: The timing break closes itself when the return file posts on the first.
[pause: 1.1]

[slide: v-481]
[pause: 1.0]
C: Four breaks, four owners.
C: The three hundred is timing, and closes itself.
[reveal: v-482]
[pause: 0.45]
C: The hundred is a dispute missing from our ledger: the disputes team posts it and decides whether to contest.
[reveal: v-483]
[pause: 0.45]
C: The hundred and fifty that never settled: payments queries it and reverses our posting.
[reveal: v-484]
[pause: 0.45]
C: And the double charge: payments posts it and refunds the customer today.
[reveal: v-485]
[pause: 0.45]
N: Reconciling by totals is the most common silent failure in this round.
[pause: 1.0]

[slide: v-486]
[pause: 0.6]
I: It's month-end, and the processor's report is two days late. Close is in two days.
[pause: 2.0]

[slide: v-487]
[pause: 0.6]
C: Close on what is known.
C: The bank statement still reconciles against the ledger two ways, and the card items wait as open timing breaks, listed with amounts and ages, signed off by finance.
[reveal: v-488]
[pause: 0.45]
C: The honest limit: a late file delays certainty, not the close.
C: And a file that is late three months running is a vendor problem, for whoever owns that contract.
[pause: 0.8]

[slide: v-489]
[pause: 0.7]
V: If asked, I'd say: I never reconcile by totals. I match the ledger, the processor and the bank line by line, by reference, and every difference is a typed break with an owner and an age.
[pause: 1.0]
N: Reconciliation catches a bad day after it happens. Next, the bad day itself.
[pause: 1.6]

[pause: 1.4]

## 7.7 Challenge 7: The card processor is down on the 1st

[slide: v-490]
[pause: 1.2]
N: Challenge seven. The worst morning: the card processor fails halfway through the window.
[pause: 1.8]

[slide: v-491]
[pause: 0.6]
I: Eleven minutes past six on the first, the card processor goes down, with sixty thousand charges left. What do you do?
[pause: 2.0]

[slide: v-492]
[pause: 1.3]
C: The naive answer: keep retrying until it comes back, and whatever failed is late tomorrow.
[reveal: v-493]
[pause: 0.45]
C: Look at the rails.
[reveal: v-494]
[pause: 0.45]
C: Blind retries turn an outage into thousands of unknown outcomes,
[reveal: v-495]
[pause: 0.45]
C: and the late fees turn our outage into the customer's cost.
[pause: 1.1]

[slide: v-496]
[pause: 1.0]
C: The trace.
C: From six to eleven past, fifty-nine thousand four hundred charged at ninety a second.
[reveal: v-497]
[pause: 0.45]
C: Then the processor goes down with a hundred and eighty in flight, all unknown.
[reveal: v-498]
[pause: 0.45]
C: Blind retries for nine minutes add nine thousand more timeouts, all unknown.
[reveal: v-499]
[pause: 0.45]
C: At nine the processor is back, and the workers send everything at once and get throttled again.
[reveal: v-500]
[pause: 0.45]
C: And on the second, sixty thousand late fees at ten dollars: six hundred thousand dollars charged to customers for our outage.
[pause: 1.0]

[slide: v-501]
[pause: 1.3]
C: The fix, in order.
[reveal: v-502]
[pause: 0.45]
C: A breaker opens and the rail switch pauses the card rail: no new attempts.
C: The resolver clears the hundred and eighty unknowns first, before anything is sent again.
[reveal: v-503]
[pause: 0.45]
C: Policy, agreed in advance: our outage is not your late fee, so the late clock runs from our attempt window, not from the due date.
C: Then resume at fifty a second, and ramp up.
[reveal: v-504]
[pause: 0.45]
C: Rejected: Retrying a down rail until it returns.
C: A retry storm; pause, resolve, protect the customer, resume slowly.
[pause: 1.1]

[slide: v-505]
[pause: 1.0]
C: As a runbook.
C: Pause the card rail, with one switch, to stop creating unknowns.
[reveal: v-506]
[pause: 0.45]
C: Resolve every unknown before resending anything.
[reveal: v-507]
[pause: 0.45]
C: Suppress late marks and fees, under a policy agreed before the outage, not during it.
[reveal: v-508]
[pause: 0.45]
C: Resume at fifty, and ramp to ninety.
[reveal: v-509]
[pause: 0.45]
C: And tell customers what happens next, before they ask.
C: Note what is missing: failover.
[reveal: v-510]
[pause: 0.45]
C: The card tokens live at this processor, so I can't move card customers to another one this morning.
C: Bank debit is a fallback only for customers with a debit mandate.
[pause: 1.0]

[slide: v-511]
[pause: 0.6]
I: It stays down until three in the afternoon, past the bank's cut-off for any fallback.
[pause: 2.0]

[slide: v-512]
[pause: 0.6]
C: Then collect tomorrow.
C: The day plan re-runs, the sixty thousand join tomorrow’s card window, and the grace period extends automatically for everyone affected.
[reveal: v-513]
[pause: 0.45]
C: Longer term, network tokens that work across processors, and a second processor in the contract.
C: That is a quarter of work, and I'd price it against what a day like this costs.
[pause: 0.8]

[slide: v-514]
[pause: 0.7]
V: If asked, I'd say: pause the rail, resolve every unknown before sending anything, never charge a late fee for our outage, and resume under a lower limit.
[pause: 1.0]
N: Every fix so far assumed someone noticed. Last, how you would know.
[pause: 1.6]

[pause: 1.4]

## 7.8 Challenge 8: How would you know before month-end?

[slide: v-515]
[pause: 1.2]
N: Challenge eight, observability. Finding the problem before finance finds it at close.
[pause: 1.8]

[slide: v-516]
[pause: 0.6]
I: How would you know any of this is going wrong, before finance finds it at month-end close?
[pause: 2.0]

[slide: v-517]
[pause: 1.3]
C: The naive answer: error rate and latency.
[reveal: v-518]
[pause: 0.45]
C: Look at the dispatcher and file ingest.
[reveal: v-519]
[pause: 0.45]
C: A debit file that the bank half-rejects is still a successful upload.
[reveal: v-520]
[pause: 0.45]
C: Nothing on a server dashboard moves.
[pause: 1.1]

[slide: v-521]
[pause: 1.0]
C: The trace.
C: At half past ten on the first, the debit file goes out with four hundred and eighty thousand entries.
C: Zero errors.
[reveal: v-522]
[pause: 0.45]
C: At eleven the bank's acknowledgement says twelve thousand were rejected, after a change in an account-number format, and nobody reads it.
[reveal: v-523]
[pause: 0.45]
C: On the second, twelve thousand customers get late notices for payments we never sent.
[reveal: v-524]
[pause: 0.45]
C: Finance finds it at close.
[pause: 1.0]

[slide: v-525]
[pause: 1.3]
C: The fix: indicators on the money.
C: A funnel per rail per day: due, claimed, sent, acknowledged, settled, returned.
[reveal: v-526]
[pause: 0.45]
C: A page if the file isn't acknowledged by eleven.
C: Unknown count and age.
[reveal: v-527]
[pause: 0.45]
C: Returns by reason code, against their baseline.
C: Breaks by age and amount.
[reveal: v-528]
[pause: 0.45]
C: And every night, a check that every transaction sums to zero, and every balance equals the sum of its lines.
C: Rejected: A month-end report.
C: Breaks age for weeks; watch the money funnel and the files daily.
[pause: 1.1]

[slide: v-529]
[pause: 1.3]
C: As a sequence.
[reveal: v-530]
[pause: 0.45]
C: One: the file goes out with four hundred and eighty thousand entries.
[reveal: v-531]
[pause: 0.45]
C: The acknowledgement, highlighted: twelve thousand rejected.
[reveal: v-532]
[pause: 0.45]
C: Two: the probe feeds the funnel to monitoring.
[reveal: v-533]
[pause: 0.45]
C: In red: acknowledged over sent is ninety-seven and a half percent, against a baseline of ninety-nine point nine.
C: Page, at eleven, with three hours left before the cut-off to fix and resend.
[pause: 1.1]

[slide: v-534]
[pause: 1.0]
C: Then read them in pairs.
C: Sent normal, acknowledged down: the bank rejected entries, so read the file.
[reveal: v-535]
[pause: 0.45]
C: Unknowns up with latency at the timeout: the processor is slow.
[reveal: v-536]
[pause: 0.45]
C: Unauthorised returns up, concentrated on one merchant: we are capturing authorisations badly there.
[reveal: v-537]
[pause: 0.45]
C: Breaks up today with return ingest lagging: ingest is stuck, not the money.
[reveal: v-538]
[pause: 0.45]
C: And any transaction that doesn't sum to zero: stop posting and page.
[reveal: v-539]
[pause: 0.45]
N: Pairs like these are the start of a real runbook.
[pause: 1.0]

[slide: v-540]
[pause: 1.0]
C: One more family of indicators, because the rails watch us too.
[reveal: v-541]
[pause: 0.45]
C: Unauthorised bank-debit returns: the rules' threshold is half a percent over sixty days. We alert at a quarter. A rise usually means weak authorisation capture at one merchant or channel.
[reveal: v-542]
[pause: 0.45]
C: Administrative returns, account closed or not found: the threshold is three percent; we alert at one and a half. It means account details weren't verified at origination.
[reveal: v-543]
[pause: 0.45]
C: All debit returns: fifteen percent; we alert at eight. Usually collection dates set before payday, or a drift in risk policy.
[reveal: v-544]
[pause: 0.45]
C: And card disputes, against each card network's monitoring programme; we alert at three tenths of a percent.
[reveal: v-545]
[pause: 0.45]
N: Cross one of these lines and the bank can stop you collecting at all. That is an outage no server dashboard shows.
[pause: 1.0]

[slide: v-546]
[pause: 0.6]
I: A policy change misallocates four dollars on thirty thousand loans. Every transaction still sums to zero.
[pause: 2.0]

[slide: v-547]
[pause: 0.6]
C: Balanced but wrong needs two more checks.
C: Shadow every new policy version over yesterday's postings and diff the allocations before it goes live; because policy is data, that is a query, not a project.
[reveal: v-548]
[pause: 0.45]
C: And a per-loan invariant, every night: the remaining schedule sums to the outstanding principal.
C: A misallocation that still balances fails right there.
[pause: 0.8]

[slide: v-549]
[pause: 0.7]
V: If asked, I'd say: I watch the money, not the servers. A funnel from due to settled per rail, the file acknowledged by eleven, unknowns and breaks by age, and nightly invariants on the ledger and every loan.
[pause: 1.6]

[pause: 1.4]

## 8 Build cost

[slide: v-550]
[pause: 1.2]
N: This chapter is marked auxiliary. It is the engineering-manager layer, optional in a Staff round.
C: Servicing is three releases, and the order matters more than the size.
[pause: 1.8]

[slide: v-551]
[pause: 1.0]
C: Version one: the ledger with projections, schedules, the state machine, the card rail and the resolver.
C: Four engineers for two quarters.
[reveal: v-552]
[pause: 0.45]
C: Version two: the bank-file rail, returns, policy as data, refunds and payoff.
C: Six engineers for two quarters.
[reveal: v-553]
[pause: 0.45]
C: Version three: three-way reconciliation, the finance console, runbooks and due-date spreading.
C: Two teams for two quarters, plus a finance operations function.
[reveal: v-554]
[pause: 0.45]
C: All illustrative.
C: And for a small book with standard products, buying a servicing platform is the honest version zero.
[pause: 1.0]

[slide: v-555]
[pause: 0.6]
C: Three one-way doors.
C: The chart of accounts and the ledger schema: seven years of lines and every auditor depend on them.
[reveal: v-556]
[pause: 0.45]
C: Terms versioning: contracts cite it, and old loans keep old rules forever.
C: And the idempotency key format, which the processor shares.
[reveal: v-557]
[pause: 0.45]
C: These get the most review.
C: Everything else can change in a quarter.
[pause: 0.8]

[slide: v-558]
[pause: 1.0]
C: Six owners, and one writer to the ledger.
C: The ledger team owns accounts, the posting interface, the invariants and the close, and nobody else writes lines.
[reveal: v-559]
[pause: 0.45]
C: Collections and payments own the scheduler, rails, resolver and returns.
[reveal: v-560]
[pause: 0.45]
C: Servicing product owns refunds, payoff and hardship.
[reveal: v-561]
[pause: 0.45]
C: Finance operations own reconciliation.
[reveal: v-562]
[pause: 0.45]
C: Risk and legal own retry rules, fees and allocation, as policy versions they approve.
[reveal: v-563]
[pause: 0.45]
C: And compliance owns debit authorisations and fee caps.
[pause: 1.0]

[slide: v-564]
[pause: 0.6]
C: Three risks.
C: The return path runs rarely, so it breaks quietly: replay a month of real return files in staging before every release.
[reveal: v-565]
[pause: 0.45]
C: Reconciliation built last, so the first closes are done by hand.
[reveal: v-566]
[pause: 0.45]
C: And one processor holding all the card tokens, so there is no failover until network tokens arrive.
[pause: 0.8]

[pause: 1.4]

## 9 Recap

[slide: v-567]
[pause: 1.2]
C: To close: one picture, one sentence per path, the mistakes to avoid, and the thesis.
[pause: 1.8]

[slide: v-568]
[pause: 1.3]
C: The whole design on one baseline.
[reveal: v-569]
[pause: 0.45]
C: The servicing database with the ledger,
[reveal: v-570]
[pause: 0.45]
C: intents and the outbox.
[reveal: v-571]
[pause: 0.45]
C: The dispatcher with its rail budget,
[reveal: v-572]
[pause: 0.45]
C: the day plan above it,
[reveal: v-573]
[pause: 0.45]
C: and the rail switch.
[reveal: v-574]
[pause: 0.45]
C: The resolver and file ingest beside the rails.
[reveal: v-575]
[pause: 0.45]
C: Policy for terms and rules,
[reveal: v-576]
[pause: 0.45]
C: the payoff quote at the A-P-I,
[reveal: v-577]
[pause: 0.45]
C: reconciliation and finance operations at the bottom,
[reveal: v-578]
[pause: 0.45]
C: and probes watching the funnel.
[pause: 1.1]

[slide: v-579]
[pause: 1.0]
C: One sentence per path.
C: Schedule: a terms version in, a schedule version and booking lines out.
[reveal: v-580]
[pause: 0.45]
C: Collect: claim, intent and outbox in one commit, then send under the rail budget with the key, and unknown on a timeout.
[reveal: v-581]
[pause: 0.45]
C: Adjust: a transaction and a new schedule version, and quotes that list what is in flight.
[reveal: v-582]
[pause: 0.45]
C: Returns: a state, a reversal dated now, and policy decides any retry.
[reveal: v-583]
[pause: 0.45]
C: Reconcile: line by line, three ways, every break owned.
[pause: 1.0]

[slide: v-584]
[pause: 0.6]
C: The common mistakes.
C: On correctness: a balance column, retrying with a new key, treating settled as final, refunds that leave the schedule alone, and floats.
[reveal: v-585]
[pause: 0.45]
C: On operations: calling forty-two a second a thundering herd, a midnight burst, reconciling by totals, charging late fees for our own outages, and nobody owning the policy.
C: The same shapes appear in subscription billing, wallets and payroll, under other names.
[pause: 0.8]

[slide: v-586]
[pause: 0.6]
C: If I had thirty seconds.
C: Money lives in a double-entry ledger with immutable lines, and each payment is a state machine with unknown and returned, with keys at three layers.
[reveal: v-587]
[pause: 0.45]
C: The database is the queue, and a budget per rail and the bank's cut-off shape the day.
[reveal: v-588]
[pause: 0.45]
C: Returns and unknowns are rare paths, so I test them with real files.
[reveal: v-589]
[pause: 0.45]
C: And every day the books are reconciled three ways, with an owner for every break.
[pause: 0.8]

[slide: v-590]
[pause: 0.7]
V: Loan servicing is about correctness over months, not throughput. Lines that never change, unknown and returned as ordinary states, the rail as the limit, and a three-way proof every day that our books match the bank's.
[pause: 1.6]
