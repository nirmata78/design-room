# Payments and ledger mock round (video)

<!-- Video script for ~/.claude/skills/slide-video-kit/scripts/build_video.py. [slide: v-NN] = video/frames/v-NN.png.
     Speakers: I interviewer · C candidate · V candidate, key line (slower) · N coach. [pause: s] = silence.
     Content follows ../../SD-44-payments-ledger.md. Level: em (L6 / M1), per levels.md.
     The four follow-ups and their diagrams (svg/fu-*.svg) are new for this video. Target ~25 min. -->
<!-- voices: N=af_heart@0.92 I=bf_emma@0.95 C=am_michael@0.9 V=am_michael@0.84 -->
<!-- labels: N=COACH -->
<!-- say: UNKNOWN=unknown -->

## Before you start

[slide: v-01]
N: This is a mock system design round, for an engineering manager loop at level six. The prompt is payments and a double-entry ledger. You'll hear the interviewer, the candidate as they should sound, and me, between the stages. After the design, four manager follow-ups. Listen once, straight through. On the second pass, pause after every question, and answer it yourself first.

[slide: v-02]
N: Know what's being weighed. At this level, operations and cost count most, then leadership. Depth once: here, the bank timeout, over the next ten minutes and the next ten days. And expect the manager's curveball. Product wanting to approve offline. A processor outage on the busiest day. A second processor. The fee bill.

## Requirements

[slide: v-03]
I: Design the system that takes a payment and records it. The ledger the company's money is accounted for in.

C: A few questions, and the last one sets the priorities for everything else.

[slide: v-04]
C: Volume?

I: Ten thousand payments a second at peak, in fifty currencies.

C: Latency?

I: An authorisation decision within two seconds.

C: The processor call will use most of that. Who's outside our boundary, and how do they behave?

I: Card networks and banks. They time out, return ambiguous results, and sometimes go down for hours.

C: Then unknown outcomes are the core problem, not throughput. And the ledger?

I: It must always balance. No exceptions.

C: Double entry, with atomic posting.

[slide: v-05]
C: Audit?

I: Every balance must be explainable from immutable records, for seven years.

C: So an append-only journal, and no updates. Refunds?

I: Yes, partial, days or months later. And chargebacks.

C: Adjusting entries, and a state machine. And retries?

I: Clients retry. What do you require of them?

C: An idempotency key on every call that changes something. Last question. What must never happen, in order?

I: You tell me.

C: First, never lose money or double-charge. Second, never an unbalanced ledger. Third, a slow payment. In that order.

N: Ranking the failures out loud tells the interviewer how every later trade-off will be decided.

[slide: v-06]
C: In scope: authorise, capture, refund, the state machine, the ledger, webhooks and reconciliation. Out of scope, said aloud: fraud scoring, card vaulting, F-X pricing, merchant onboarding, and payouts.

## The thesis

[slide: v-07]
C: Before boxes, the framing.

V: Exactly-once does not exist across the bank boundary.

[pause: 1.0]

C: So the design is at-least-once delivery, idempotent operations, an explicit pending state for unknown outcomes, and reconciliation that finds the discrepancies anyway. All on top of an immutable, append-only, double-entry journal, where balances are derived, never stored as the truth.

[slide: v-08]
C: The commitments. Zero double charges. The ledger balanced at every commit. A payment decision under two seconds at p ninety-nine. And reconciliation every day, with every break owned.

## Back of the envelope

[slide: v-09]
C: Ten thousand payments a second, about four entries each, is about forty thousand journal entries a second at peak. So the journal is partitioned by account. Seven years of entries is roughly five or six hundred terabytes: hot recent partitions, and a cold archive. Immutable data makes archiving easy. And the processor takes three hundred to fifteen hundred milliseconds, so everything we own must fit in about two hundred.

[slide: v-10]
C: But the number that shapes the data model is the hot merchant.

V: One large merchant, five thousand updates a second to one balance row.

[pause: 0.8]

C: That serialises on the row lock. So entries are appended, and the balance is derived. Which is also exactly what auditors want.

I: Mm-hm.

N: The hot merchant number turned a performance problem into a data-model decision. That's the estimation bar.

## The A-P-I

[slide: v-11]
C: Create a payment, with an idempotency key header. The amount is an integer in minor units, with a currency. Never floats: floats lose cents. Capture can be automatic or manual. It returns authorized, captured, declined, or pending. Capture and refund are separate calls, each with its own key. And merchants get signed webhooks with event I-Ds, retried with backoff, so merchants deduplicate by event I-D.

[slide: v-12]
C: The payment state machine. Created, then auth pending, then authorized, captured and settled. Declined on a decline. Voided if it's cancelled or expires. Refunds go through partially refunded to refunded. Chargebacks after settlement. And one state that matters most: unknown. A timeout goes there. It is never failed, and never succeeded, until the processor tells us.

[slide: v-13]
C: The ledger. Accounts: merchant payable, processor receivable, fee revenue, and so on. Journal transactions and journal entries, both immutable. Balances are a projection, derived and rebuildable. Plus the idempotency table with stored responses, and an outbox for events.

[slide: v-14]
C: An example. Ten euros fifty captured, with a thirty-cent fee. Debit processor receivable, one thousand and fifty. Credit merchant payable, one thousand and twenty. Credit fee revenue, thirty. Debits equal credits. That invariant is enforced in the posting code, and checked by the database, in the same transaction.

## High-level design

[slide: v-15]
C: The context. Merchants post payments. Finance operations works the reconciliation breaks. Outside: the processor or card network, slow and ambiguous; the banks, sending settlement files days later; and a fraud-scoring service we call.

[slide: v-16]
C: Inside. The payments A-P-I handles idempotency keys. The payment service runs the state machine, with one database transaction per transition: the new state, the journal entries and an outbox row. A processor adapter per processor puts our reference on every call. The outbox relay publishes payment events, which feed the webhook sender. An inquiry job resolves unknown outcomes. And reconciliation matches the daily files.

[slide: v-17]
C: One successful payment. The A-P-I inserts the idempotency row as processing. The payment service moves the payment from created to auth pending, and commits, before calling out. That way, a crash leaves evidence the call may have been made. The adapter calls the processor with our own reference. When it's approved, one transaction: authorized, the entries, the outbox event, and the stored response. Then the merchant gets two-oh-one.

[slide: v-18]
C: Technology. A relational database, partitioned by account, because postings must be atomic across rows, with constraints. A transactional outbox, so there are no dual writes between the database and a broker. An adapter per processor, retrying only where the processor supports idempotent references. Reconciliation as a batch over raw files. And money as integer minor units with a currency on every amount.

[slide: v-19]
C: Inside the payment service: an idempotency guard, which also hashes the payload. The state machine, which allows only legal transitions. A posting builder. An invariant check: debits equal credits, per currency. An outbox writer in the same transaction. And an asynchronous balance projector.

## Deep dive one: the timeout

[slide: v-20]
I: The authorisation call to the bank timed out. Was the customer charged?

[slide: v-21]
C: We don't know, and the design has to admit that. So I don't mark it failed, because the merchant would retry, and the customer could be charged twice. And I don't mark it succeeded. The payment moves to unknown, and the client gets pending. Within seconds to minutes, the inquiry job asks the processor for the status, by our reference. Approved: it moves to authorized and continues. Not found, after the processor's safe window: declined, and a new attempt is safe. If we no longer want an authorisation we're unsure about, we send a reversal, which is idempotent by reference. And days later, the settlement file is the final word. Reconciliation catches anything the inquiry missed.

[slide: v-22]
V: A timeout is an unknown, not a failure.

[pause: 1.0]

C: And no retry ever creates a second charge, because every call carries the same reference.

N: The next ten minutes and the next ten days, in one answer. That's the depth this round is decided on.

## Deep dive two: idempotency

[slide: v-23]
I: Three retries of the same payment arrive at once. Then a fourth, with the same key and a different amount.

[slide: v-24]
C: The idempotency row is a unique insert, in the same transaction that creates the payment. One retry wins. The others see processing, and get a four-oh-nine, retry later. Once the winner finishes, a retry gets the stored response. The fourth request has the same key and a different amount. The payload hash doesn't match, so it gets a four twenty-two. Returning the original would hide a client bug. Executing it would double-charge.

[slide: v-25]
I: What if the service crashes between writing the ledger and publishing the event?

C: It can't end up inconsistent. The state, the entries and the outbox row commit in one transaction. If the crash is before the commit, nothing happened. If it's after, the relay will publish the event later, at least once, and consumers deduplicate by event I-D.

## Deep dive three: the hot merchant

[slide: v-26]
C: Appending entries scales, because nothing locks a balance row. The balance is derived by an asynchronous projection, a few seconds behind, which is fine for dashboards. Where a check really needs the balance, like a payout that can't exceed available funds, I split the account into sub-accounts and sum them, or serialise payout checks through one worker per merchant. Payouts are rare compared to incoming payments.

[slide: v-27]
C: Refunds and chargebacks are new journal transactions that reference the original payment. Never edits. A refund is allowed only if the refunds so far, plus this one, don't exceed what was captured, checked with a conditional update on the payment row. A chargeback ninety days later is posted dated now, with the original reference, so closed accounting periods are never rewritten.

## Deep dive four: reconciliation

[slide: v-28]
C: Reconciliation is a permanent component, not a script. Every day, the processor's settlement file arrives, and we keep the raw copy, immutable. The ledger produces expectations: what should settle, net of fees. We match them. Matched payments become settled, with settlement entries. Everything else is a break: missing, mismatched, or unexpected. Breaks go to finance operations as an owned, aged workflow. And the unreconciled amount, by age, is a monitored metric.

## A requirement added mid-round

[slide: v-29]
I: A bug double-posted forty thousand entries last night. Some of that money has already been paid out to merchants.

[slide: v-30]
C: Stop the bleeding first. Kill-switch the faulty code path, and halt payouts for the affected merchants, because money not yet sent can still be protected. Then find the duplicates exactly, from the immutable journal: same payment, same type, twice. Correct them with reversing entries, one correction per duplicate, tagged with an incident I-D.

V: Never delete, never update. The audit trail shows the error and the correction.

[pause: 0.8]

C: For merchants already paid the excess, that's a receivable, recovered from future settlements. That's a business decision with communication, not a database operation. And the postmortem asks why idempotency didn't catch it, and adds a reconciliation check that would have flagged it within the hour.

N: Stop, find, correct, recover. And the line between an engineering fix and a business decision, drawn out loud.

## Failures and operations

[slide: v-31]
C: The failures. A processor outage: route to a secondary processor where contracts allow, degrade gracefully, and never approve offline without a risk policy. A slow processor: timeouts go to unknown and inquiry, never retries in a loop. A database failover: clients retry with the same key, which is safe. Outbox lag: alert on the outbox age; merchants can poll. And growing reconciliation breaks: an ageing S-L-O, owners, and escalation.

[slide: v-32]
C: The alerts that fire before finance notices. Payment success, excluding legitimate declines, and decision latency. The unknown rate and age: a spike means a processor problem. The ledger balance check: debits minus credits must be zero, and if it isn't, it pages immediately. The approval rate per processor against its baseline. And the unreconciled amount by age.

[slide: v-33]
V: Processor fees dwarf the servers. The engineering levers on cost are routing, and reducing false declines.

[pause: 0.8]

N: A balance check that pages, and the honest statement about where the money goes. That's the operations signal.

## The manager layer

[slide: v-34]
I: How would you build it?

C: The M-V-P is one processor, automatic capture, and daily reconciliation. Then manual capture, partial refunds and chargebacks. Then a second processor, for cost and resilience. The one-way doors get the most review: the ledger schema, and the idempotency contract. Everything else can change.

[slide: v-35]
C: Four teams. Payments A-P-I and the state machine, who own the idempotency contract. The ledger, owned centrally, as a contract for everyone else. Processor integrations: adapters, inquiry and routing. And reconciliation and finance tooling. Plus a runbook for "payments failing at three in the morning", with a named owner.

[slide: v-36]
C: To close.

V: Every transition commits together with balanced, immutable entries, and its event.

[pause: 0.8]

C: Payments are an explicit state machine. Exactly-once across the bank boundary is impossible, so every call is idempotent by key, timeouts go to a pending state resolved by inquiry, and daily reconciliation catches what's left. Balances are derived, so the hot merchant scales and every number is explainable for seven years. Next, I'd harden the inquiry protocol per processor, and make reconciliation breaks an owned, aged workflow.

I: Thanks. Some questions on the management side.

## Follow-up 1: approve offline

[slide: v-37]
I: Product wants us to approve payments offline when the processor is down. We lose sales otherwise.

[slide: v-38]
C: I understand the pressure, and the sales are real. But approving offline means we tell the merchant the money is coming, and the card may decline later. That's unfunded money, and it's ours. So I wouldn't do it by default. As a product choice, it can work with a written risk policy: small amounts, trusted buyers, and a cap on total exposure per hour.

V: Who decides is risk and finance. Engineering prices the options.

[pause: 0.8]

C: I'd bring the numbers: how often the processor is down, the sales lost, and the expected loss under each cap. Then the right owners decide, in writing.

N: The risk priced, the owner named, and no unilateral yes or no. That's leadership without overreach.

## Follow-up 2: Black Friday

[slide: v-39]
I: Black Friday. Our main processor starts timing out. Unknown climbs to fifteen percent.

[slide: v-40]
C: The first thing I'd say, to the incident channel and to leadership: nobody is being double-charged, because every retry carries the same reference. Then detect: the approval rate per processor and the unknown count have already paged. Contain: route new payments to the secondary processor, where contracts allow, and degrade gracefully everywhere else. Resolve: the inquiry job drains the unknowns as the processor recovers, with no blind retries. Merchants see pending, not failed.

C: Afterwards: a blameless review, a per-processor game day before the next peak, and a merchant communication template ready to send.

N: Lead with what's safe, then contain, then drain. Calm, in that order.

## Follow-up 3: a second processor

[slide: v-41]
I: We're adding a second processor next quarter, for cost and resilience. Three teams. How?

[slide: v-42]
C: First, the contract: an adapter interface with authorise, capture, refund and inquiry, agreed in week one. The ledger doesn't change at all. Then shadow: a small slice of traffic, one percent of one merchant segment. Reconciliation runs on both settlement files, with breaks reported per processor. When the breaks are clean, ramp by route, reversible per merchant.

V: The ledger is the contract. A new processor is a new adapter, not a new ledger.

[pause: 0.8]

C: Three teams: the A-P-I and state machine, processor integrations, and reconciliation. Each has a clear deliverable, and the contracts between them are the adapter interface and the ledger.

N: Contract first, measured ramp, and nothing in the core moves. That's the delivery signal.

## Follow-up 4: the fee bill

[slide: v-43]
I: Last one. The C-F-O asks why processing fees grew faster than volume this year.

[slide: v-44]
C: I slice by route: card type, region, and processor. Usually the mix shifted: more international cards, or more expensive card types. Then the levers. Least-cost routing, where the approval rate holds. And recovering false declines: a declined payment that should have been approved is lost revenue, and a retry with a new reference can be safe. I'd report fees and approval rate together, per payment, because cheaper routing that declines more customers isn't cheaper.

N: The diagnosis order is the answer, and the cost was measured against revenue, not on its own.

## Debrief

[slide: v-45]
N: Here's where the round lands. Strong candidates say "we'll use transactions". Exceptional ones say exactly-once doesn't exist across the boundary. Strong ones keep a balance column. Exceptional ones use immutable double entry, with derived balances. Strong ones retry on timeout. Exceptional ones walk unknown, inquiry, reversal and the settlement file. And on idempotency, exceptional ones put the key in the same transaction, and reject a changed payload.

[slide: v-46]
N: Five checks, before the real round. "Exactly-once doesn't exist across the boundary." Double entry, derived balances, integer minor units. The idempotency key in the same transaction. The timeout walk: unknown, inquiry, settlement. And corrections are new entries, never edits. Good luck.
