# SD-44 Payment processing and the double-entry ledger: reference solution (Staff L6/L7, compact cut)

<!-- Video script for slide-video-kit/scripts/build_video.py. [slide: v-NNN] = frames/v-NNN.png; [reveal: v-NNN] = the next
     reveal step of the same slide. Generated from src/*.py: edit the sources, not this file. -->
<!-- voices: N=af_heart@0.92 I=bf_emma@0.95 C=am_michael@0.9 V=am_michael@0.84 -->
<!-- names: C=Candidate V=Candidate N=Coach I=Interviewer -->
<!-- say: API=A-P-I APIs=A-P-Is SLO=S-L-O SLOs=S-L-Os SLI=S-L-I TTL=T-T-L HTTP=H-T-T-P HTTPS=H-T-T-P-S SQL=S-Q-L ID=I-D IDs=I-Ds EM=E-M UUID=U-U-I-D CDC=C-D-C KYC=K-Y-C FX=F-X PCI=P-C-I PSP=P-S-P TB=terabytes GB=gigabytes MB=megabytes KB=kilobytes p99=P-ninety-nine UNKNOWN=unknown AUTH_PENDING=auth-pending PostgreSQL=Postgres-Q-L Debezium=Deb-ee-zee-um Kafka=Kaf-ka TigerBeetle=Tiger-Beetle WebFlux=Web-Flux Quarkus=Kwar-kus GraalVM=Graal-V-M JVM=J-V-M GIL=G-I-L JDBC=J-D-B-C gRPC=g-R-P-C REST=rest Rust=Rust Spark=Spark Stripe=Stripe Adyen=Eye-den WAL=W-A-L ISO=I-S-O NOTIFY=notify -->


## 0 Cold open

[slide: v-001]
[pause: 1.2]
C: The happy path of a payment is three boxes and a database. A merchant asks, we call the bank, we write it down. This question is not about the happy path. It is about a bank call that times out and leaves you not knowing whether the customer paid, a client that retries three times at once, and a statement that disagrees with your books.
[pause: 1.8]

[slide: v-002]
[pause: 0.6]
I: Design the system that takes a payment and records it. The ledger the company's money is accounted for in.
[pause: 1.5]

[slide: v-003]
[pause: 1.3]
C: The hook, as a timeline. The merchant wants an answer in two seconds.
[reveal: v-004]
[pause: 0.45]
C: The processor's answer comes in about a second, or not at all.
[reveal: v-005]
[pause: 0.45]
C: An inquiry can settle an unknown outcome within minutes.
[reveal: v-006]
[pause: 0.45]
C: The settlement file, with the processor's own books, arrives the next day.
[reveal: v-007]
[pause: 0.45]
C: And a dispute can still arrive months later. Every strong answer is a design for not knowing yet. The rest of this video puts one mechanism at each point on this line.
[pause: 1.1]

[slide: v-008]
[pause: 1.0]
N: Five axes, one at a time.
[reveal: v-009]
[pause: 0.45]
N: Requirements. Weak: charge the card and store it. Strong: what must never happen, in order, and how the outside parties fail.
[reveal: v-010]
[pause: 0.45]
N: Correctness. Weak: a balance column and floats. Strong: double entry, balances derived, a key inserted first.
[reveal: v-011]
[pause: 0.45]
N: Trade-offs. Weak: a distributed transaction with the bank. Strong: why that is unavailable, and the cost of an unknown state.
[reveal: v-012]
[pause: 0.45]
N: Depth. Retry with backoff is a phrase; the timeout walk, the partition key and the hot account are the level down.
[reveal: v-013]
[pause: 0.45]
N: Operations. Uptime stays green while the money is wrong; unknown age and a zero-sum ledger do not.
[reveal: v-014]
[pause: 0.45]
C: I'll keep one sentence in front of everything: exactly-once does not exist across a network boundary.
[pause: 1.0]

[slide: v-015]
[pause: 0.7]
V: Exactly-once does not exist across a network boundary. So the design is at-least-once delivery, one effect per intent, a state for not knowing yet, and a reconciliation that finds what the rest missed. All of it written to an append-only double-entry journal, where a balance is a sum, never a field.
[pause: 1.6]

[pause: 1.4]

## 1 Requirements and scope

[slide: v-016]
[pause: 1.2]
C: The scale first, then six questions. Each answer moves the design.
[pause: 1.8]

[slide: v-017]
[pause: 0.6]
C: The interviewer gives me the scale, and I write it down first.
[reveal: v-018]
[pause: 0.45]
C: Nine billion payments a month: two hundred and ninety million a day, thirty-three hundred a second on average.
[reveal: v-019]
[pause: 0.45]
C: The peak is ten thousand a second, a sale-day evening at three times the average. Inside it, one large merchant takes five thousand a second on its own.
[reveal: v-020]
[pause: 0.45]
C: And the books are kept seven years, about two point nine trillion entries.
[reveal: v-021]
[pause: 0.45]
C: Every number I use later starts from one of these three, and I'll say which. They are illustrative.
[pause: 0.8]

[slide: v-022]
[pause: 0.6]
C: How fast must the client get an answer?
[reveal: v-023]
[pause: 0.45]
I: An authorisation decision within two seconds.
C: Most of those two seconds belong to the processor, not to us. So our own part has to be small, and we need a plan for when the processor uses all of it.
[pause: 0.6]

[slide: v-024]
[pause: 0.6]
C: Who moves the money, and do we reach them directly or through a gateway?
[reveal: v-025]
[pause: 0.45]
I: Networks and banks, through processors. They time out, give ambiguous results, and sometimes go down for hours. Gateway or direct is your call.
C: Ambiguous results mean a state for not knowing. At this volume I'd go direct to processors, and I'll show where a gateway wins, because below some volume it does.
[pause: 0.6]

[slide: v-026]
[pause: 0.6]
C: What is the ledger's rule?
[reveal: v-027]
[pause: 0.45]
I: It must always balance. No exceptions.
C: Then every movement is entries that sum to zero, written in one transaction, and a check that it still sums to zero runs all the time.
[pause: 0.6]

[slide: v-028]
[pause: 0.6]
C: How long must the books be explainable?
[reveal: v-029]
[pause: 0.45]
I: Every balance explainable from immutable records, for seven years.
C: Immutable and explainable rule out a balance column updated in place. A balance becomes a sum over records.
[pause: 0.6]

[slide: v-030]
[pause: 0.6]
C: Refunds and disputes?
[reveal: v-031]
[pause: 0.45]
I: Partial and full refunds, and chargebacks, arriving days or months later.
C: Months later means the original period may be closed. So corrections are new records dated when they happen, never edits.
[pause: 0.6]

[slide: v-032]
[pause: 0.6]
C: What must never happen, in priority order? I'd propose: charging twice or losing money, then an unbalanced ledger, then a slow payment.
[reveal: v-033]
[pause: 0.45]
I: Your call. I agree with that order.
C: That order settles a lot. When I must choose between a fast answer and a correct one, I answer pending.
[pause: 0.6]

[slide: v-034]
[pause: 0.6]
C: Five functional requirements.
[reveal: v-035]
[pause: 0.45]
C: One, pay: authorise and capture, idempotent per client key.
[reveal: v-036]
[pause: 0.45]
C: Two, adjust: void, refund, chargeback, each referencing the original payment.
[reveal: v-037]
[pause: 0.45]
C: Three, notify: every state change reaches the merchant as a signed webhook.
[reveal: v-038]
[pause: 0.45]
C: Four, reconcile: match our books against each processor's settlement file every day, and make every difference a break with an owner.
[reveal: v-039]
[pause: 0.45]
C: Five, explain: any balance at any time, from the journal. Each gets a sequence later.
[pause: 0.8]

[slide: v-040]
[pause: 0.6]
C: The numbers, all initial targets.
[reveal: v-041]
[pause: 0.45]
C: Zero double charges.
[reveal: v-042]
[pause: 0.45]
C: A decision within two seconds at the ninety-ninth percentile, or an honest pending.
[reveal: v-043]
[pause: 0.45]
C: Ninety-nine percent of unknown outcomes resolved within fifteen minutes.
[reveal: v-044]
[pause: 0.45]
C: Every difference with the processor found and owned within a day. And every journal transaction balanced at commit.
[pause: 0.8]

[slide: v-045]
[pause: 0.6]
C: In scope: authorise, capture, void, refund, chargeback, webhooks, the ledger, reconciliation, and fifty currencies without conversion.
[reveal: v-046]
[pause: 0.45]
C: Out, on purpose: fraud scoring is a service I call. Card numbers live in a token vault, which keeps most card-data compliance away from us. Conversion, onboarding and payouts are their own questions.
[reveal: v-047]
[pause: 0.45]
C: Payouts will come back once, in challenge four, because a payout needs a current balance.
[pause: 0.8]

[slide: v-048]
[pause: 1.3]
C: Before any boxes inside it, the system in its context.
[reveal: v-049]
[pause: 0.45]
C: A customer pays at a merchant.
[reveal: v-050]
[pause: 0.45]
C: The merchant's system creates payments and receives webhooks.
[reveal: v-051]
[pause: 0.45]
C: In the middle, our system: it authorises, captures, and keeps the books.
[reveal: v-052]
[pause: 0.45]
C: The processor moves the money, and keeps its own books of it. It sends us a settlement file every day.
[reveal: v-053]
[pause: 0.45]
C: And finance operations owns breaks and corrections. Two of the four neighbours keep their own books of the same money, which is why reconciliation is a component and not a safety net.
[pause: 1.1]

[slide: v-054]
[pause: 0.7]
V: The core is four things. A state machine that admits unknown. An idempotent A-P-I. An immutable double-entry journal. And reconciliation against the outside world.
[pause: 0.8]
N: Notice the candidate fixed the scale, named the core and drew the context before any internals. That is the scoping signal.
[pause: 1.6]

[pause: 1.4]

## 2 Estimates

[slide: v-055]
[pause: 1.2]
C: Numbers next. Each starts from the scale line, and each ends in a decision. They are illustrative, not measured.
[pause: 1.8]

[slide: v-056]
[pause: 1.0]
C: The write rate, from the peak.
[reveal: v-057]
[pause: 0.45]
C: Ten thousand payments a second, four entries each: forty thousand entries a second. One primary will not take that.
[reveal: v-058]
[pause: 0.45]
C: One payment is about eight rows, the key, the payment, the attempt, a transaction, three entries and an outbox row, written in one commit. So one transaction per payment.
[reveal: v-059]
[pause: 0.45]
C: A primary with a synchronous standby commits about twelve hundred of those a second. Ten thousand divided by that is nine primaries, so sixty-four logical partitions on about ten primaries.
[reveal: v-060]
[pause: 0.45]
C: And the decision I'll defend: the key is the merchant, not the account. A capture touches three accounts. Keyed by account, every capture would span partitions. Keyed by merchant, it stays in one. I'll come back to that, including what happens with a million one-time accounts.
[pause: 1.0]

[slide: v-061]
[pause: 1.0]
C: Volume and storage, from the monthly count.
[reveal: v-062]
[pause: 0.45]
C: Thirty-three hundred a second times eighty-six thousand four hundred seconds: about two hundred and ninety million payments a day. The settlement files will have hundreds of millions of lines.
[reveal: v-063]
[pause: 0.45]
C: Seven years: two point nine trillion entries at two hundred bytes is about five hundred and eighty terabytes. Recent partitions stay hot and older ones move to a cold archive. Entries never change, so archiving is a copy, not a migration.
[reveal: v-064]
[pause: 0.45]
C: And the idempotency keys: seven days of them is about six hundred gigabytes. So keys expire, and the A-P-I contract says a retry after seven days is a new payment.
[pause: 1.0]

[slide: v-065]
[pause: 1.3]
C: The number that shapes the data model, from the peak.
[reveal: v-066]
[pause: 0.45]
C: One large merchant receives five thousand payments a second.
[reveal: v-067]
[pause: 0.45]
C: If each payment updates that merchant's balance row, each update holds a row lock for about one and a half milliseconds. That allows about six hundred and seventy a second on one row.
[reveal: v-068]
[pause: 0.45]
C: Append-only entries have no shared row at all.
[reveal: v-069]
[pause: 0.45]
C: And sixteen sub-accounts would carry about ten thousand seven hundred a second, twice this merchant's peak.
[reveal: v-070]
[pause: 0.45]
C: The shared row's queue grows by over four thousand a second, and within a second the merchant is past two seconds. Decision: payments append entries and the balance is derived. That is challenge four.
[pause: 1.1]

[slide: v-071]
[pause: 1.3]
C: The two-second budget. Our own work is the idempotency insert, a fraud call, and two commits: about ninety milliseconds.
C: The processor, at its ninety-ninth percentile, about one and a half seconds. That leaves about four hundred spare.
C: Decision: everything we own stays under a hundred milliseconds, and at one point nine seconds, if the processor has not answered, we answer pending and keep waiting. This is also why the language is not the bottleneck: our code is microseconds inside a second-long call.
[pause: 1.1]

[slide: v-072]
[pause: 1.0]
C: Three more.
[reveal: v-073]
[pause: 0.45]
C: Unknown outcomes: one in a thousand times the peak is ten a second, thirty-six thousand an hour. Resolving them is a service with its own throughput and the processor's rate limits, not a cron script.
[reveal: v-074]
[pause: 0.45]
C: Settlement: about two hundred and ninety million lines a day, at a million lines a second is five minutes. Reconciliation is a batch join, and its useful output is the breaks.
[reveal: v-075]
[pause: 0.45]
C: And cost. Processor fees are a percentage of the money that moves, so one basis point of better routing outweighs the whole database cluster. Servers are not the lever.
N: That is the cost judgement this round looks for. Next, theory.
[pause: 1.0]

[pause: 1.4]

## 3 Theory

[slide: v-076]
[pause: 1.2]
C: A short theory chapter before any design, so the design can lean on it. What a payment system is and is not, the properties, the central tension, five mechanisms, an options matrix, and the failure catalogue.
[pause: 1.8]

[slide: v-077]
[pause: 0.7]
V: A payment system turns a customer's intent to pay into exactly one movement of money, records every movement as balanced, immutable entries, and keeps its books in agreement with the outside parties that actually move the money.
[pause: 1.6]

[slide: v-078]
[pause: 0.6]
C: Four confusions.
[reveal: v-079]
[pause: 0.45]
C: The payment system is not the ledger. One orchestrates an intent across outside parties, the other is the book of record, and they fail differently.
[reveal: v-080]
[pause: 0.45]
C: A ledger is not a balance table. A balance is a sum, and a number updated in place cannot explain itself.
[reveal: v-081]
[pause: 0.45]
C: Idempotency is not de-duplicating messages. It is one effect per intent, with the original answer returned to every retry.
[reveal: v-082]
[pause: 0.45]
C: And the precision statement for this video: exactly-once delivery is impossible across a network. What we can build is at-least-once delivery with an effect that happens once.
[pause: 0.8]

[slide: v-083]
[pause: 0.6]
V: Safety: one intent never moves money twice, every journal transaction balances, and history is never rewritten.
[reveal: v-084]
[pause: 0.45]
V: Liveness: every payment leaves unknown for a final state, every difference with the outside world becomes an owned break within a day, and every change reaches the merchant.
C: Every fix from here on says which of the six it serves. Liveness is where most designs are silent: they never say how an unknown ends.
[pause: 0.8]

[slide: v-085]
[pause: 1.0]
C: The central tension: an answer in two seconds, and a truth that arrives over months. Back to the timeline as a table.
[reveal: v-086]
[pause: 0.45]
C: At two seconds we know approved, declined, or nothing. The tools are the idempotency key and the unknown state.
[reveal: v-087]
[pause: 0.45]
C: In minutes, the inquiry by our own reference.
[reveal: v-088]
[pause: 0.45]
C: The next day, reconciliation.
[reveal: v-089]
[pause: 0.45]
C: Months later, a new transaction dated now. No mechanism replaces another. A design with idempotency and no reconciliation has a hole at one point on this line.
[pause: 1.0]

[slide: v-090]
[pause: 0.6]
C: Mechanism one, the idempotency key, inserted first. It protects S-one.
[reveal: v-091]
[pause: 0.45]
C: The client sends a key. We insert it, unique per client, with a hash of the request, in the transaction that creates the payment. The final response is stored on the row.
[reveal: v-092]
[pause: 0.45]
C: It rules out a retry or a concurrent duplicate becoming a second payment, and a changed retry silently accepted.
[reveal: v-093]
[pause: 0.45]
C: It costs a table with a retention window, and an in-progress answer clients must handle.
[pause: 0.8]

[slide: v-094]
[pause: 0.6]
C: Mechanism two, a state machine with an unknown state, and an inquiry. It protects S-one and L-one.
[reveal: v-095]
[pause: 0.45]
C: Named states and legal edges only. A timeout moves the payment to unknown, which has its own exits. The attempt is committed, with our own reference, before the call goes out, and an inquiry by that reference ends the unknown.
[reveal: v-096]
[pause: 0.45]
C: It rules out treating a timeout as a failure, which double-charges on retry, or as a success, which loses money.
[reveal: v-097]
[pause: 0.45]
C: It costs more states to test, pending answers, and an inquiry job per processor.
[pause: 0.8]

[slide: v-098]
[pause: 0.6]
C: Mechanism three, the immutable double-entry journal. It protects S-two, S-three and the audit.
[reveal: v-099]
[pause: 0.45]
C: Every movement is a transaction whose debits equal its credits, per currency, checked at commit. Entries are inserted, never updated, and a balance is a projection over them. The partition key is the owner, the merchant.
[reveal: v-100]
[pause: 0.45]
C: It rules out balances nobody can explain, lost cents, and a hot lock on a balance row.
[reveal: v-101]
[pause: 0.45]
C: It costs storage that only grows, and projections for reads.
[pause: 0.8]

[slide: v-102]
[pause: 0.6]
C: Mechanism four, the transactional outbox. It protects L-three.
[reveal: v-103]
[pause: 0.45]
C: The event is a row in the same transaction as the state change. Change capture reads the database's write-ahead log and publishes committed rows in order, at least once.
[reveal: v-104]
[pause: 0.45]
C: It rules out a committed state with no event, and an event for a change that rolled back.
[reveal: v-105]
[pause: 0.45]
C: It costs a pipeline to run, and consumers that de-duplicate by event I-D.
[pause: 0.8]

[slide: v-106]
[pause: 0.6]
C: Mechanism five, reconciliation. It protects L-two, and correctness against the outside world.
[reveal: v-107]
[pause: 0.45]
C: The ledger produces what it expects each processor to settle. The raw file is matched line by line, by reference, and every unmatched line becomes a break with a type, an owner and an age.
[reveal: v-108]
[pause: 0.45]
C: It rules out silent divergence from the counterparty's books.
[reveal: v-109]
[pause: 0.45]
C: It costs a pipeline, a workflow, and people.
[pause: 0.8]

[slide: v-110]
[pause: 1.0]
C: Where each mechanism will live. The system itself is drawn once, in chapter five; here only the labels.
[reveal: v-111]
[pause: 0.45]
C: M-one, the key, in the A-P-I and the ledger database: a unique insert decides which request counts.
[reveal: v-112]
[pause: 0.45]
C: M-two in the payment service and the inquiry job.
[reveal: v-113]
[pause: 0.45]
C: M-three in the ledger database and the balance projector.
[reveal: v-114]
[pause: 0.45]
C: M-four in the database and the outbox relay.
[reveal: v-115]
[pause: 0.45]
C: M-five in reconciliation and finance operations. These labels come back as badges on the container view.
[pause: 1.0]

[slide: v-116]
[pause: 1.3]
C: The hardest mechanism, operating. The payment service opens a transaction.
[reveal: v-117]
[pause: 0.45]
C: The state moves from auth pending to captured, in a conditional update that names the state it expects.
[reveal: v-118]
[pause: 0.45]
C: One row changed: the edge was legal.
[reveal: v-119]
[pause: 0.45]
C: Then the journal transaction and its three entries: debit one thousand and fifty, credit one thousand and twenty, credit thirty.
[reveal: v-120]
[pause: 0.45]
C: And the outbox row.
[reveal: v-121]
[pause: 0.45]
C: A deferred check at commit: debits one thousand and fifty equal credits one thousand and fifty.
[reveal: v-122]
[pause: 0.45]
C: Commit.
[reveal: v-123]
[pause: 0.45]
C: Had the entries been unbalanced, the whole transaction would be rejected. There is never a moment where the state says captured and the books do not.
[pause: 1.1]

[slide: v-124]
[pause: 1.0]
C: Six approaches, each with the failure that rules it out.
[reveal: v-125]
[pause: 0.45]
C: A, a balance column with retries assumed safe: it fails at the first timeout and retry, a double charge.
[reveal: v-126]
[pause: 0.45]
C: B, a distributed transaction with the processor: it fails always, because the processor is not a participant and will not hold a prepared state.
[reveal: v-127]
[pause: 0.45]
C: C, a saga without ledger rules: a compensation can itself time out, and nothing says what the books should be.
[reveal: v-128]
[pause: 0.45]
C: D is the pick. It fails only when a processor gives no way to ask about our reference, and then the settlement file is the arbiter, a day late.
[reveal: v-129]
[pause: 0.45]
C: E, an event-sourced ledger: how I'd build projections inside D, but alone it fails where a refund needs a current balance right now.
[reveal: v-130]
[pause: 0.45]
C: F, buy. That is the honest first version for a small company with one processor. It fails at the second processor, or when we must keep our own books.
[pause: 1.0]

[slide: v-131]
[pause: 0.6]
C: What D buys is never guessing: a retry is harmless, an unknown has an exit, every balance is a sum of facts, and the outside world is checked daily.
[reveal: v-132]
[pause: 0.45]
C: What it gives up: more states to test, a reconciliation function with people in it, and pending answers that every merchant integration has to handle. I'd say that cost aloud, because it lands on other teams.
[pause: 0.8]

[slide: v-133]
[pause: 1.0]
C: Last, the failure catalogue, which becomes the challenge list.
[reveal: v-134]
[pause: 0.45]
C: A timeout, the crux.
[reveal: v-135]
[pause: 0.45]
C: Concurrent retries.
[reveal: v-136]
[pause: 0.45]
C: A crash between commit and event.
[reveal: v-137]
[pause: 0.45]
C: The hot merchant, and the opposite problem, a million one-time accounts.
[reveal: v-138]
[pause: 0.45]
C: Books that disagree with the processor's, the second half of the crux, and a bug that posted wrong entries.
[reveal: v-139]
[pause: 0.45]
C: And nobody noticing. Refunds and late chargebacks are covered on the A-P-I and flow slides and in the written design; floating-point money by integer minor units.
[pause: 1.0]

[pause: 1.4]

## 4 API and entities

[slide: v-140]
[pause: 1.2]
C: The A-P-I before the boxes. It is the contract with every merchant, and it shows whether I have thought about failure. Every call carries a tag: the requirement it serves and the entity it touches.
[pause: 1.8]

[slide: v-141]
[pause: 1.0]
C: Pay. The client sends an idempotency key in a header, and a body with the merchant, the amount and a token for the card.
C: The amount is an integer in minor units with its currency: one thousand and fifty cents, never ten point five as a float. The card number never reaches us: a token does.
C: The answer is the payment I-D and a status, and the status can honestly be pending. The same key with a different body is a four twenty-two. The same key while the first is in flight is a four-oh-nine.
[pause: 1.0]

[slide: v-142]
[pause: 1.3]
C: Behind that status is a state machine, drawn one state at a time. A payment is created.
[reveal: v-143]
[pause: 0.45]
C: It becomes auth pending when we send it.
[reveal: v-144]
[pause: 0.45]
C: From there, authorised when the processor approves.
[reveal: v-145]
[pause: 0.45]
C: Declined, when it declines.
[reveal: v-146]
[pause: 0.45]
C: Or the red one: unknown, on a timeout or an ambiguous answer.
[reveal: v-147]
[pause: 0.45]
C: Unknown has two exits. The inquiry says approved, and the payment becomes authorised.
[reveal: v-148]
[pause: 0.45]
C: Or the processor says not found after its safe window, and it becomes declined.
[reveal: v-149]
[pause: 0.45]
C: Authorised becomes captured.
[reveal: v-150]
[pause: 0.45]
C: Captured becomes settled when the file matches.
[reveal: v-151]
[pause: 0.45]
C: Captured can be partly refunded.
[reveal: v-152]
[pause: 0.45]
C: And then refunded in full.
[reveal: v-153]
[pause: 0.45]
C: And a settled payment can be disputed: a chargeback. Any transition not drawn here is rejected by the code. A capture on a declined payment is not a bug to handle later: it cannot happen.
[pause: 1.1]

[slide: v-154]
[pause: 1.0]
C: The rest of the surface, each tagged.
[reveal: v-155]
[pause: 0.45]
C: Capture and void, each with its own key, each a new transaction that references the payment. Nothing is edited.
[reveal: v-156]
[pause: 0.45]
C: Refunds. The limit is one conditional update on the payment row: add the amount only if the total stays within what was captured.
[reveal: v-157]
[pause: 0.45]
C: Webhooks, signed, retried with backoff for days. A merchant may see an event twice and de-duplicates by event I-D.
[reveal: v-158]
[pause: 0.45]
C: A get on the payment: the backstop. A merchant who missed every webhook can still find the state.
[reveal: v-159]
[pause: 0.45]
C: Inquire asks a processor about our own reference for one attempt.
[reveal: v-160]
[pause: 0.45]
C: And a balance, from the projection, which says which entry it is current to.
[pause: 1.0]

[slide: v-161]
[pause: 1.3]
C: The conceptual model, one entity at a time.
[reveal: v-162]
[pause: 0.45]
C: A payment, with its state and its merchant.
[reveal: v-163]
[pause: 0.45]
C: It has attempts: one per call to a processor, each with our reference. An attempt only exists inside its payment.
[reveal: v-164]
[pause: 0.45]
C: A payment posts journal transactions.
[reveal: v-165]
[pause: 0.45]
C: A transaction contains entries, at least two, and an entry exists only inside its transaction.
[reveal: v-166]
[pause: 0.45]
C: Each entry is on one account, which also belongs to a merchant. A balance is a derived attribute of an account: the sum of its entries.
[reveal: v-167]
[pause: 0.45]
C: And a break, from reconciliation, may explain one transaction.
[pause: 1.1]

[slide: v-168]
[pause: 1.3]
C: The physical tables, one at a time.
[reveal: v-169]
[pause: 0.45]
C: Journal entries, keyed by merchant, account and entry, hashed into sixty-four partitions by merchant, and only ever inserted.
[reveal: v-170]
[pause: 0.45]
C: Journal transactions carry the payment and the type, with a check at commit that debits equal credits.
[reveal: v-171]
[pause: 0.45]
C: The payment row is the only mutable row, changed only by conditional updates.
[reveal: v-172]
[pause: 0.45]
C: Idempotency keys, with their request hash and stored response, kept seven days.
[reveal: v-173]
[pause: 0.45]
C: The outbox, written in the same transaction as the state.
[reveal: v-174]
[pause: 0.45]
C: And a balance projection that can be rebuilt from the entries at any time.
[pause: 1.1]

[slide: v-175]
[pause: 1.3]
C: A worked example. A capture of one thousand and fifty, with a fee of thirty.
[reveal: v-176]
[pause: 0.45]
C: The processor receivable is debited one thousand and fifty: the processor owes us that.
[reveal: v-177]
[pause: 0.45]
C: The merchant payable is credited one thousand and twenty: we owe the merchant that.
[reveal: v-178]
[pause: 0.45]
C: Fee revenue is credited thirty.
[reveal: v-179]
[pause: 0.45]
C: Debits one thousand and fifty, credits one thousand and fifty: balanced.
[reveal: v-180]
[pause: 0.45]
C: A refund is a new transaction that mirrors these lines. Three rules about amounts, cheap to state and expensive to forget: never a float, a currency on every amount, and a conversion is its own transaction with the rate it used.
[pause: 1.1]

[pause: 1.4]

## 5 High-level design

[slide: v-181]
[pause: 1.2]
C: The design in three versions. Each answers the objection to the one before, and it is one picture from here to the end: later slides only show what changes on it.
[pause: 1.8]

[slide: v-182]
[pause: 1.3]
C: Version one, drawn in the order a payment travels.
[reveal: v-183]
[pause: 0.45]
C: The merchant.
[reveal: v-184]
[pause: 0.45]
C: Calls the payments A-P-I.
[reveal: v-185]
[pause: 0.45]
C: Which hands it to the payment service.
[reveal: v-186]
[pause: 0.45]
C: The service records the payment in one database: a status, and a balance column.
[reveal: v-187]
[pause: 0.45]
C: And charges the card at the processor, synchronously. It is the simplest thing that works. The objection comes next.
[pause: 1.1]

[slide: v-188]
[pause: 1.0]
C: The objection, as a trace.
[reveal: v-189]
[pause: 0.45]
C: The payment goes to the processor.
[reveal: v-190]
[pause: 0.45]
C: At one point nine seconds, no answer, so version one marks it failed.
[reveal: v-191]
[pause: 0.45]
C: Half a second later the processor approves it anyway.
[reveal: v-192]
[pause: 0.45]
C: The checkout retries as a new payment, which is approved. The customer has two holds.
[reveal: v-193]
[pause: 0.45]
C: And next month an auditor asks why a balance is what it is, and the answer is a number that was updated in place.
[pause: 1.0]

[slide: v-194]
[pause: 1.3]
C: Version two. Everything from version one stays where it was.
[reveal: v-195]
[pause: 0.45]
C: New: a processor adapter. The A-P-I now inserts the idempotency key first. The payment service commits the payment as auth pending, with an attempt and our own reference, before it calls out, and the adapter calls the processor with that reference. The database holds a journal: balanced, immutable entries, with balances as a projection. A timeout now moves the payment to unknown instead of failed, and a retry with the same key gets the same answer.
[pause: 1.1]

[slide: v-196]
[pause: 0.6]
C: The objection to version two. Inside the database it is correct. But:
[reveal: v-197]
[pause: 0.45]
C: Merchants hear about a change through a second write after the commit, so a crash in between means they never hear.
[reveal: v-198]
[pause: 0.45]
C: Nothing ends an unknown: ten a second at peak, pending forever.
[reveal: v-199]
[pause: 0.45]
C: And our books can still disagree with the processor's, and nothing would notice.
[pause: 0.8]

[slide: v-200]
[pause: 1.3]
C: Version three closes those loops. Version two, carried as it was.
[reveal: v-201]
[pause: 0.45]
C: New: an outbox relay feeds an event log, and a webhook sender posts signed events to the merchant.
[reveal: v-202]
[pause: 0.45]
C: An inquiry job reads unknown payments, asks the adapter by reference, and resolves them in the database.
[reveal: v-203]
[pause: 0.45]
C: And reconciliation takes the processor's settlement file, compares it with expectations from the ledger,
[reveal: v-204]
[pause: 0.45]
C: and hands the breaks to finance operations. This is the baseline. It stays, and every picture from here on is a view of it.
[pause: 1.1]

[slide: v-205]
[pause: 1.0]
C: The containers, one at a time, with what each owns and its number.
[reveal: v-206]
[pause: 0.45]
C: The payments A-P-I owns the key, the request hash and the two-second deadline. It never owns the state, so it stays stateless at ten thousand a second.
[reveal: v-207]
[pause: 0.45]
C: The payment service owns the state machine and the postings. Only legal edges, one commit per payment.
[reveal: v-208]
[pause: 0.45]
C: The processor adapter puts our reference on every call and maps the processor's codes into three classes. About one and a half seconds at the processor, at the ninety-ninth percentile.
[reveal: v-209]
[pause: 0.45]
C: The ledger database holds payments, journal, outbox and keys: sixty-four partitions on about ten primaries, one merchant slice per partition.
[reveal: v-210]
[pause: 0.45]
C: The outbox relay and log publish committed rows in commit order, and the webhook sender signs and retries them. At the peak that is forty thousand rows a second.
[reveal: v-211]
[pause: 0.45]
C: The inquiry job ends every unknown by our reference, with backoff: about ten a second at the peak.
[reveal: v-212]
[pause: 0.45]
C: And reconciliation: expectations, the file match and owned breaks. Two hundred and ninety million lines, about five minutes.
[pause: 1.0]

[slide: v-213]
[pause: 1.0]
C: One decision on the database deserves its own slide, because it is the one an interviewer asks about: why this partition key?
[reveal: v-214]
[pause: 0.45]
C: By account: all of one account's entries are together, so a balance read is one partition. But a capture touches three accounts, the receivable, the payable and the fee, so it spans partitions every time, and I would need a distributed transaction for every payment.
[reveal: v-215]
[pause: 0.45]
C: By payment: a capture is local, but a balance is a scatter across every partition.
[reveal: v-216]
[pause: 0.45]
C: By merchant: a capture is one partition, a balance read is one partition, and the cost is that a hot merchant is a hot partition. That is the cost I can handle, in challenge four.
[reveal: v-217]
[pause: 0.45]
C: By time: all writers hit the newest partition. No.
[reveal: v-218]
[pause: 0.45]
C: And shared accounts, fee revenue or the processor receivable, would be hot and cross-partition, so each partition has its own, and the company view sums them.
[pause: 1.0]

[slide: v-219]
[pause: 1.3]
C: The pay path, numbered.
[reveal: v-220]
[pause: 0.45]
C: One: the merchant posts the payment with its key.
[reveal: v-221]
[pause: 0.45]
C: Two: the A-P-I inserts the key and hands over to the service.
[reveal: v-222]
[pause: 0.45]
C: Three: one transaction commits the payment as auth pending, with its attempt.
[reveal: v-223]
[pause: 0.45]
C: Four: the adapter is asked to authorise.
[reveal: v-224]
[pause: 0.45]
C: Five: it calls the processor with our reference. The answer comes back along the same path, and a second transaction commits the state, the entries, the outbox row and the key marked done.
[pause: 1.1]

[slide: v-225]
[pause: 1.3]
C: The same payment as a sequence.
[reveal: v-226]
[pause: 0.45]
C: The merchant posts with key k-ninety-one.
[reveal: v-227]
[pause: 0.45]
C: One transaction: the key as processing, the payment as auth pending, the attempt with its reference.
[reveal: v-228]
[pause: 0.45]
C: Authorise, through the adapter.
[reveal: v-229]
[pause: 0.45]
C: With reference p-seventy-seven thirty-one, slash one.
[reveal: v-230]
[pause: 0.45]
C: Approved in three hundred and forty milliseconds.
[reveal: v-231]
[pause: 0.45]
C: The second transaction, highlighted: captured, entries, outbox, key done.
[reveal: v-232]
[pause: 0.45]
C: Then two-oh-one, captured.
[pause: 1.1]

[slide: v-233]
[pause: 1.3]
C: Requirement two, a refund, as a sequence.
[reveal: v-234]
[pause: 0.45]
C: A refund of twenty-five hundred on a payment that has already been refunded part-way.
[reveal: v-235]
[pause: 0.45]
C: A second one, two milliseconds later, with another key.
[reveal: v-236]
[pause: 0.45]
C: The conditional update: add the amount only if the total stays within what was captured. One row.
[reveal: v-237]
[pause: 0.45]
C: The same statement for the second: zero rows.
[reveal: v-238]
[pause: 0.45]
C: So the second gets four twenty-two.
[reveal: v-239]
[pause: 0.45]
C: The winner goes to the processor with its own reference.
[reveal: v-240]
[pause: 0.45]
C: And a new journal transaction is posted, dated now. Three months later a chargeback is posted the same way, dated now, and the closed month is untouched.
[pause: 1.1]

[slide: v-241]
[pause: 1.3]
C: Requirement five, explain.
[reveal: v-242]
[pause: 0.45]
C: An auditor asks for a merchant's payable balance as of the end of October.
[reveal: v-243]
[pause: 0.45]
C: The service sums the entries on that account, up to that date. One partition, because the key is the merchant.
[reveal: v-244]
[pause: 0.45]
C: The answer says which entry it is current to.
[reveal: v-245]
[pause: 0.45]
C: And for every unit of it, the entries joined to their transactions and payments: every number explained by the records that produced it.
[pause: 1.1]

[pause: 1.4]

## 5.1 Components and technologies

[slide: v-246]
[pause: 1.2]
C: Now one level down. The same picture with what each box runs on, three containers opened up, and for each choice, what I rejected and why.
[pause: 1.8]

[slide: v-247]
[pause: 1.3]
C: The same container view; only the type lines changed. The six boxes in scope, one at a time.
[reveal: v-248]
[pause: 0.45]
[reveal: v-249]
[pause: 0.45]
C: The payments A-P-I: Go, gRPC inside, REST outside.
[reveal: v-250]
[pause: 0.45]
C: The payment service: Go, with the state machine.
[reveal: v-251]
[pause: 0.45]
C: The processor adapter: Go, one per processor.
[reveal: v-252]
[pause: 0.45]
C: The ledger database: PostgreSQL, partitioned by merchant.
[reveal: v-253]
[pause: 0.45]
C: The outbox relay: Debezium on Kafka Connect, publishing to Kafka.
[reveal: v-254]
[pause: 0.45]
C: And reconciliation: a Spark batch, with expectations in PostgreSQL.
[pause: 1.1]

[slide: v-255]
[pause: 1.3]
C: Inside the payment service, in the order a payment meets it.
[reveal: v-256]
[pause: 0.45]
C: The A-P-I hands over.
[reveal: v-257]
[pause: 0.45]
C: The idempotency guard: a unique insert, with a request hash.
[reveal: v-258]
[pause: 0.45]
C: The state machine: conditional updates, legal edges only.
[reveal: v-259]
[pause: 0.45]
C: The attempt writer: our reference, committed before the call.
[reveal: v-260]
[pause: 0.45]
C: The processor port: a deadline of one point nine seconds, and three error classes.
[reveal: v-261]
[pause: 0.45]
C: Below, the ledger database: the key row, the state, entries and outbox, and the attempt row first.
[reveal: v-262]
[pause: 0.45]
C: The adapter.
[reveal: v-263]
[pause: 0.45]
C: The processor.
[reveal: v-264]
[pause: 0.45]
C: And the inquiry job, which asks the adapter by reference and resolves through the state machine. Challenges one and two happen in this picture.
[pause: 1.1]

[slide: v-265]
[pause: 1.3]
C: Inside one partition of the ledger database.
[reveal: v-266]
[pause: 0.45]
C: The payment service issues one transaction.
[reveal: v-267]
[pause: 0.45]
C: One transaction: the state, the entries and the outbox row, together.
[reveal: v-268]
[pause: 0.45]
C: It writes the payment row, the only mutable one.
[reveal: v-269]
[pause: 0.45]
C: The journal entries, insert only, with sixteen sub-accounts for a hot merchant.
[reveal: v-270]
[pause: 0.45]
C: And the outbox table, in the same transaction.
[reveal: v-271]
[pause: 0.45]
C: A balance projection is derived from the journal, seconds behind.
[reveal: v-272]
[pause: 0.45]
C: And a payout writer, one per merchant, checks the sum.
[reveal: v-273]
[pause: 0.45]
C: The outbox row reaches the write-ahead log, in commit order.
[reveal: v-274]
[pause: 0.45]
C: A replication slot holds the log for the reader.
[reveal: v-275]
[pause: 0.45]
C: Debezium reads the slot.
[reveal: v-276]
[pause: 0.45]
C: And publishes to Kafka, by merchant. Challenges three and four happen here.
[pause: 1.1]

[slide: v-277]
[pause: 1.3]
C: Inside reconciliation.
[reveal: v-278]
[pause: 0.45]
C: The processor's file.
[reveal: v-279]
[pause: 0.45]
C: Stored unchanged, before anything reads it.
[reveal: v-280]
[pause: 0.45]
C: The expectation builder asks the ledger what it expects to settle, by reference and net of fees.
[reveal: v-281]
[pause: 0.45]
C: The matcher joins file to expectations by reference, and checks amount, fee and state.
[reveal: v-282]
[pause: 0.45]
C: Matches become settled, with settlement entries in the ledger.
[reveal: v-283]
[pause: 0.45]
C: Everything else goes to the break writer: a type, an owner and an age.
[reveal: v-284]
[pause: 0.45]
C: Into a queue that finance operations works.
[reveal: v-285]
[pause: 0.45]
C: Finance approves a correction.
[reveal: v-286]
[pause: 0.45]
C: The corrector posts reversing entries, tagged with the incident. Challenge five happens in this picture.
[pause: 1.1]

[slide: v-287]
[pause: 1.0]
C: The key is the owner, the merchant, not the account: a capture touches three accounts and would span partitions. Shared accounts, like fee revenue, exist once per partition and are summed for the company view.
[reveal: v-288]
[pause: 0.45]
C: Why: State, journal and outbox commit together or not at all.
[reveal: v-289]
[pause: 0.45]
C: Rejected: Partitioning by account. Every capture becomes a cross-partition transaction.
[reveal: v-290]
[pause: 0.45]
C: TigerBeetle, a ledger database. Fastest at debits and credits, but state, keys and outbox need a database anyway.
[reveal: v-291]
[pause: 0.45]
C: A key-value store, or a log as the truth. No multi-row transaction, no synchronous refund limit.
[pause: 1.0]

[slide: v-292]
[pause: 1.0]
C: The outbox row commits with the payment. Debezium, in Kafka Connect, reads the write-ahead log through a replication slot and publishes rows to Kafka in commit order, at least once. The risk: a stalled reader makes the database keep log.
[reveal: v-293]
[pause: 0.45]
C: Why: Reading the write-ahead log costs the database nothing extra and keeps commit order.
[reveal: v-294]
[pause: 0.45]
C: Rejected: A polling relay. Right below about 1,000 events a second.
[reveal: v-295]
[pause: 0.45]
C: Own consumer of logical decoding. We would own slots, restarts and schema changes.
[reveal: v-296]
[pause: 0.45]
C: Managed capture (DMS, Datastream). Built for analytics copies.
[pause: 1.0]

[slide: v-297]
[pause: 1.0]
C: Why Go everywhere? Because the language is not where the two seconds go.
[reveal: v-298]
[pause: 0.45]
C: Go. Our own code costs a fraction of a millisecond a request, a replica is thirty to eighty megabytes, and a context deadline cancels a whole call chain. That is a flat tail and cheap replicas. The processor takes a second; the commit, a few milliseconds.
[reveal: v-299]
[pause: 0.45]
C: Java twenty-one and later, with virtual threads, in Spring Boot or Quarkus, is within a small factor of Go and an equal choice for a Java team. It costs more memory per instance, unless compiled native.
[reveal: v-300]
[pause: 0.45]
C: Spring WebFlux, the reactive stack. It was the answer to blocking threads. Virtual threads now give the same concurrency with plain blocking code, and a JDBC driver blocks anyway. I would not choose it for a payments service.
[reveal: v-301]
[pause: 0.45]
C: Python with async: a core per process under the interpreter lock, several times less throughput per core, and a fatter tail.
[reveal: v-302]
[pause: 0.45]
C: Rust is the fastest and leanest. It pays where microseconds matter, a matching engine, not in a service whose time is a bank call and a commit. The cost is hiring and build speed.
[reveal: v-303]
[pause: 0.45]
N: The numbers are illustrative and the public benchmarks disagree. The signal is saying where the time goes, and what would change the answer.
[pause: 1.0]

[slide: v-304]
[pause: 1.0]
C: The question every interviewer eventually asks: why not just use a gateway? Often you should.
[reveal: v-305]
[pause: 0.45]
C: A gateway gives one A-P-I in days. Direct means underwriting and certification: months.
[reveal: v-306]
[pause: 0.45]
C: Card data. Tokens and hosted fields keep it out of our scope. Direct puts us in the highest compliance level.
[reveal: v-307]
[pause: 0.45]
C: Price, illustrative: a gateway is about two point nine percent plus thirty cents at list. A direct processor is interchange plus a margin, about one point eight to two point four percent.
[reveal: v-308]
[pause: 0.45]
C: A gateway also brings payment methods, fraud tools, disputes and payouts. Direct gives only what we build.
[reveal: v-309]
[pause: 0.45]
C: Control: with a gateway their routing and their outage are ours. Direct, we route across several processors.
[reveal: v-310]
[pause: 0.45]
C: And what is ours either way: the ledger, the keys, the unknown state, and reconciliation. A gateway's balance is not our books, and a timeout to a gateway is still an unknown.
[reveal: v-311]
[pause: 0.45]
C: Break-even: a premium of seven tenths of a percent against a team and audits of about eighty thousand dollars a month is about ten million dollars of card volume a month. We are far past it, so direct, behind one interface, and a gateway is one more adapter.
[pause: 1.0]

[slide: v-312]
[pause: 1.0]
C: The port has authorise, capture, void, refund, inquire and read settlement. Each adapter maps the processor's codes into three classes; only the ambiguous one becomes UNKNOWN.
[reveal: v-313]
[pause: 0.45]
C: Why: The processor is where unknowns are born.
[reveal: v-314]
[pause: 0.45]
C: Rejected: A shared generic client. The ambiguous class gets lost in the lowest common denominator.
[reveal: v-315]
[pause: 0.45]
C: A gateway only, at this volume. About 0.7 % of volume above interchange.
[reveal: v-316]
[pause: 0.45]
C: Retrying every timeout. If the first call landed, the retry charges twice.
[pause: 1.0]

[slide: v-317]
[pause: 1.0]
C: The stack on one slide, as I would leave it on the whiteboard.
[reveal: v-318]
[pause: 0.45]
C: Ledger database: PostgreSQL, by merchant. Not Partition by account; TigerBeetle. A posting stays in one partition.
[reveal: v-319]
[pause: 0.45]
C: Services: Go. Not Java virtual threads; Rust. Memory, tail and deadlines, not speed.
[reveal: v-320]
[pause: 0.45]
C: Outbox and log: Debezium into Kafka. Not Polling relay; publish after commit. Commit order, no extra load.
[reveal: v-321]
[pause: 0.45]
C: Processor adapter: Go per processor; gateway too. Not One generic client; gateway only. Own reference; price at our volume.
[reveal: v-322]
[pause: 0.45]
C: Reconciliation: Spark batch, breaks queue. Not Match by amount and time; totals. Reference match, owned breaks.
[reveal: v-323]
[pause: 0.45]
N: Naming a product is not the signal. Naming the property that rules out its rival is. Interviewers go one level down on whichever box you name, so name only what you can defend.
[pause: 1.0]

[pause: 1.4]

## 5.2 When you don't need all this

[slide: v-324]
[pause: 1.2]
C: Before I break it: a much smaller design is correct at a smaller scale, and I should say where the line is. This is the one I would build for a small business.
[pause: 1.8]

[slide: v-325]
[pause: 1.3]
C: The alternate path. The spine stays: the key, the state machine, the journal, reconciliation.
[reveal: v-326]
[pause: 0.45]
C: What changes is marked. The adapter is the gateway.
[reveal: v-327]
[pause: 0.45]
C: The database is one primary with a synchronous standby.
[reveal: v-328]
[pause: 0.45]
C: And the outbox relay is a poll every two hundred milliseconds, not change capture. No Kafka, no Debezium, no partitions.
C: What it gives up, precisely: one writer, about twelve hundred commits a second. No replayable log. The gateway's fee premium and its outages, which are ours. And a failover can lose what the standby had not yet received, if it is asynchronous.
[pause: 1.1]

[slide: v-329]
[pause: 0.7]
C: Where is the line? One primary commits about twelve hundred of our transactions a second. Our peak, from the scale line, is ten thousand: eight times past it. And at ten million dollars a month the gateway's premium pays for a payments team. We are nine billion payments a month past that.
V: Below about three hundred payments a second, with room to spare, and ten million dollars a month, I'd ship the one-primary gateway version, and I'd say out loud when I'd switch.
[pause: 1.6]

[pause: 1.4]

## 6 Bridge

[slide: v-330]
[pause: 1.2]
V: It works. The question now is where it breaks first.
[pause: 1.8]

[slide: v-331]
[pause: 1.3]
C: Version four, with the places it will break marked one at a time.
[reveal: v-332]
[pause: 0.45]
C: The adapter, where a call times out. Challenge one.
[reveal: v-333]
[pause: 0.45]
C: The A-P-I, where retries arrive together. Challenge two.
[reveal: v-334]
[pause: 0.45]
C: The outbox relay, where a crash splits a commit from its event. Challenge three.
[reveal: v-335]
[pause: 0.45]
C: The balance projector, and the database behind it: the hot merchant, and a million one-time accounts. Challenge four.
[reveal: v-336]
[pause: 0.45]
C: Reconciliation, where the outside world disagrees with us, and a bad release. Challenge five.
[reveal: v-337]
[pause: 0.45]
C: And finance operations, who find out last. Challenge six: how would we know first?
[pause: 1.1]

[pause: 1.4]

## 7 Challenges

[slide: v-338]
[pause: 1.2]
C: Six challenges, each the same way: the question, the naive answer, a case with numbers, where it breaks inside the container, the fix one level down, the push on the fix itself, and what I'd say in the room.
[pause: 1.8]

[pause: 1.4]

## 7.1 Challenge 1: The bank timed out

[slide: v-339]
[pause: 1.2]
N: Challenge one, the crux. The processor does not answer, and we do not know whether the customer paid.
[pause: 1.8]

[slide: v-340]
[pause: 0.6]
I: You call the processor. It times out. You don't know whether the customer was charged. Walk me through the next ten minutes, and the next ten days.
[pause: 2.0]

[slide: v-341]
[pause: 1.3]
C: The payment service, opened up: the attempt, the port, the adapter and the processor.
[reveal: v-342]
[pause: 0.45]
C: The processor port is marked.
[reveal: v-343]
[pause: 0.45]
C: The naive answers: mark it failed and let the client retry, or retry it ourselves until it works.
[reveal: v-344]
[pause: 0.45]
C: Then the port maps a timeout to a decline. But a timeout is not an answer. It means the request may or may not have arrived, and may or may not have been approved.
[pause: 1.1]

[slide: v-345]
[pause: 1.0]
C: The trace.
[reveal: v-346]
[pause: 0.45]
C: The attempt is sent at ten o'clock.
[reveal: v-347]
[pause: 0.45]
C: At one point nine seconds there is no answer, and the naive design marks it failed.
[reveal: v-348]
[pause: 0.45]
C: Half a second later the processor approves it.
[reveal: v-349]
[pause: 0.45]
C: At five seconds the checkout retries, as a new payment, which is approved. Two holds on one card for one purchase.
[reveal: v-350]
[pause: 0.45]
C: The numbers are illustrative. The shape is real: approvals do arrive after deadlines.
[pause: 1.0]

[slide: v-351]
[pause: 1.3]
C: The fix, on the same view.
[reveal: v-352]
[pause: 0.45]
C: The state machine.
[reveal: v-353]
[pause: 0.45]
C: The attempt writer.
[reveal: v-354]
[pause: 0.45]
C: And the inquiry job.
[reveal: v-355]
[pause: 0.45]
C: One level down. The attempt row, with our reference, commits before the call. At the deadline the state moves from auth pending to unknown, in a conditional update that names the state it expects, and the client gets pending. The inquiry asks the processor about that reference after five seconds, thirty seconds, two minutes.
C: It covers every retry: the same key gets the same pending, and the same reference is one movement at the processor. It does not cover a processor that has no inquiry. Then the settlement file is the arbiter, a day late.
[reveal: v-356]
[pause: 0.45]
C: Rejected: Treating a timeout as a decline. The bank may have charged; a retry double-charges.
[pause: 1.1]

[slide: v-357]
[pause: 1.3]
C: As a sequence.
[reveal: v-358]
[pause: 0.45]
C: Authorise, with reference p-seventy-seven thirty-one, slash one.
[reveal: v-359]
[pause: 0.45]
C: The deadline passes.
[reveal: v-360]
[pause: 0.45]
C: The payment becomes unknown, and pending is the answer, to this request and to any retry with the same key.
[reveal: v-361]
[pause: 0.45]
C: The inquiry asks for the status of that reference.
[reveal: v-362]
[pause: 0.45]
C: Approved, at two point four seconds.
[reveal: v-363]
[pause: 0.45]
C: The job moves it to authorised, posts the entries and the outbox event.
[reveal: v-364]
[pause: 0.45]
C: The two other exits: not found after the processor's safe window means declined, and a new attempt is safe. And an approval we no longer want is reversed by the same reference.
[pause: 1.1]

[slide: v-365]
[pause: 0.6]
I: The processor's inquiry endpoint is down too. Actually, the whole processor is down for an hour.
[pause: 2.0]

[slide: v-366]
[pause: 0.6]
C: A circuit breaker per processor stops new attempts going to one that is down, and new payments go to a second processor, if the contracts allow.
[reveal: v-367]
[pause: 0.45]
C: But never an unknown. An unknown sent to a second processor is two possible charges. Unknowns wait, age, and show on a dashboard, and the merchant sees pending.
[reveal: v-368]
[pause: 0.45]
C: The honest limit: a processor with neither inquiry nor idempotent references can only be resolved by the settlement file, a day late. That is a reason to choose processors, and I'd say so to whoever negotiates the contracts.
[pause: 0.8]

[slide: v-369]
[pause: 0.7]
V: If asked, I'd say: a timeout is an unknown, not a failure. I commit the attempt before calling out, move the payment to unknown, answer pending, and an inquiry job asks the processor by our own reference until it knows. Retries carry the same reference, so they can't become a second charge, and the settlement file is the final arbiter.
[pause: 1.0]
N: That fix leans on retries being harmless. Are they?
[pause: 1.6]

[pause: 1.4]

## 7.2 Challenge 2: Three retries at once

[slide: v-370]
[pause: 1.2]
N: Challenge two. The same payment arrives three times in three milliseconds: how does only one of them count?
[pause: 1.8]

[slide: v-371]
[pause: 0.6]
I: The client sends the same payment three times, concurrently, with the same idempotency key. Then once more, same key, different amount. What happens?
[pause: 2.0]

[slide: v-372]
[pause: 1.3]
C: The payments A-P-I, the idempotency guard, the state machine, and the database.
[reveal: v-373]
[pause: 0.45]
C: The guard is marked.
[reveal: v-374]
[pause: 0.45]
C: The naive answer: check whether the key exists before processing.
[reveal: v-375]
[pause: 0.45]
C: Three requests land on three servers, and each one checks, finds nothing, and charges. A check followed by an act is a race, however fast the check is.
[pause: 1.1]

[slide: v-376]
[pause: 1.0]
C: The trace.
[reveal: v-377]
[pause: 0.45]
C: Request one, key k-ninety-one, server A: it selects, and finds none.
[reveal: v-378]
[pause: 0.45]
C: Request two, one millisecond later, server B: none.
[reveal: v-379]
[pause: 0.45]
C: Request three, server C: none. Three authorisations go out.
[reveal: v-380]
[pause: 0.45]
C: Five minutes later a fourth request arrives with the same key and a different amount. Returning the stored answer would hide the client's bug. Executing it would charge again. Neither is right.
[pause: 1.0]

[slide: v-381]
[pause: 1.3]
C: The fix, on the same view.
[reveal: v-382]
[pause: 0.45]
C: The guard.
[reveal: v-383]
[pause: 0.45]
C: And the key row it writes.
[reveal: v-384]
[pause: 0.45]
C: Insert the key first, unique per client, with a hash of the request, in the same transaction that creates the payment. Only one insert can win. The others fail the constraint and read the row: processing gets a four-oh-nine, done gets the stored response, and a different hash gets a four twenty-two.
C: It covers concurrent and later retries for seven days. It does not cover a client that mints a new key per retry. That is a client bug.
[reveal: v-385]
[pause: 0.45]
C: Rejected: Check, then insert, for the idempotency key. Two concurrent requests both pass the check; a unique constraint decides.
[pause: 1.1]

[slide: v-386]
[pause: 1.0]
C: In pseudocode. Inside one transaction, try to insert the key and create the payment.
C: On a unique violation, read the row. A different hash is a reused key: four twenty-two. Processing: four-oh-nine. Otherwise return the stored response, never re-executed.
[reveal: v-387]
[pause: 0.45]
C: The result is returned, not re-executed, and a changed request under an old key is reported, not hidden.
[pause: 1.0]

[slide: v-388]
[pause: 1.3]
C: As a sequence.
[reveal: v-389]
[pause: 0.45]
C: Request one and request two, two milliseconds apart.
[reveal: v-390]
[pause: 0.45]
C: Request one's insert succeeds: processing, with payment p-seventy-seven thirty-one.
[reveal: v-391]
[pause: 0.45]
C: Request two's insert hits the unique violation.
[reveal: v-392]
[pause: 0.45]
C: It reads the row: processing, hash h-one.
[reveal: v-393]
[pause: 0.45]
C: So it gets four-oh-nine.
[reveal: v-394]
[pause: 0.45]
C: Later the same request finds done, and the same hash, and gets the stored response.
[reveal: v-395]
[pause: 0.45]
C: And the changed amount has a different hash: four twenty-two.
[pause: 1.1]

[slide: v-396]
[pause: 0.6]
I: The server that won crashes after the processor approved, but before it wrote done.
[pause: 2.0]

[slide: v-397]
[pause: 0.6]
C: The rows say exactly how far it got. The key says processing, with the payment I-D. The payment says auth pending, with the attempt's reference. That is an unknown outcome.
[reveal: v-398]
[pause: 0.45]
C: Challenge one already handles it: a sweeper sends any processing row older than a minute to the inquiry.
[reveal: v-399]
[pause: 0.45]
C: One contract term: keys live seven days, and a retry after that is a new payment.
[pause: 0.8]

[slide: v-400]
[pause: 0.7]
V: If asked, I'd say: the idempotency key is inserted first, with a unique constraint, in the same transaction that creates the payment. One request wins; the others get in progress or the stored answer. A different body under the same key is a client bug, so I reject it instead of hiding it. And a crash in the middle is just an unknown outcome, which I already handle.
[pause: 1.0]
N: Inside the database it is now safe. What about everything outside it?
[pause: 1.6]

[pause: 1.4]

## 7.3 Challenge 3: A crash between the ledger and the event

[slide: v-401]
[pause: 1.2]
N: Challenge three. The payment is committed, and the process dies before anyone is told.
[pause: 1.8]

[slide: v-402]
[pause: 0.6]
I: Your service commits the payment, then crashes before telling the merchant. What state are you in?
[pause: 2.0]

[slide: v-403]
[pause: 1.3]
C: The container view: the service, the database, the relay and the webhook sender.
[reveal: v-404]
[pause: 0.45]
C: The service is marked: it writes to the database, then publishes.
[reveal: v-405]
[pause: 0.45]
C: The naive answer: publish right after the commit, crashes are rare.
[reveal: v-406]
[pause: 0.45]
C: But that is a second write, to a second system, with no shared transaction. Whichever order you choose, a crash between them loses something.
[pause: 1.1]

[slide: v-407]
[pause: 1.0]
C: The trace.
[reveal: v-408]
[pause: 0.45]
C: The capture commits.
[reveal: v-409]
[pause: 0.45]
C: Two milliseconds later a deploy kills the process, and no event is sent.
[reveal: v-410]
[pause: 0.45]
C: The merchant's order system waits, and nothing ships: the customer has paid for nothing.
[reveal: v-411]
[pause: 0.45]
C: Reverse the order, publish first, and a failed commit ships goods for an unpaid order. Rare is not the same as never, at ten thousand a second.
[pause: 1.0]

[slide: v-412]
[pause: 1.3]
C: The fix, on the ledger database's component view.
[reveal: v-413]
[pause: 0.45]
C: The outbox table, in the same transaction.
[reveal: v-414]
[pause: 0.45]
C: And the replication slot.
[reveal: v-415]
[pause: 0.45]
C: One level down. The outbox row commits with the state and the entries. Debezium reads the write-ahead log through a replication slot, so it sees only committed rows, in commit order, and publishes each to Kafka keyed by merchant. Delivery is at least once.
C: It covers a crash between the commit and the publish. It does not remove duplicates, so consumers deduplicate by event I-D.
[reveal: v-416]
[pause: 0.45]
C: Rejected: Publishing to the broker after the commit. A crash between the two loses the event for good.
[pause: 1.1]

[slide: v-417]
[pause: 1.3]
C: As a sequence. This is also requirement three, notify.
[reveal: v-418]
[pause: 0.45]
C: One transaction: captured, entries, the outbox row e-five-five-one.
[reveal: v-419]
[pause: 0.45]
C: The process is killed right there. Nothing is lost: the row is committed.
[reveal: v-420]
[pause: 0.45]
C: Debezium reads the log from its slot position, in commit order.
[reveal: v-421]
[pause: 0.45]
C: It publishes e-five-five-one, keyed by merchant.
[reveal: v-422]
[pause: 0.45]
C: Kafka delivers it to the webhook sender.
[reveal: v-423]
[pause: 0.45]
C: Which posts it, signed, retried with backoff.
[reveal: v-424]
[pause: 0.45]
C: If the merchant sees it twice, it has already seen that event I-D and ignores the second.
[pause: 1.1]

[slide: v-425]
[pause: 0.6]
I: Debezium has been stopped for a day. Or the connector is stuck on one bad record.
[pause: 2.0]

[slide: v-426]
[pause: 0.6]
C: The cost of reading the log is that the slot keeps log for the reader. A reader stopped for a day can fill the primary's disk. That is the one new way this design can hurt the database.
[reveal: v-427]
[pause: 0.45]
C: So: alert on slot lag in bytes and on outbox age, and cap how much log the database keeps. If a slot is invalidated, it is rebuilt from the outbox table itself, which still holds the unpublished rows.
[reveal: v-428]
[pause: 0.45]
C: And below about a thousand events a second I would not run change capture at all. A polling relay has no slot to look after. That was the alternate path.
[pause: 0.8]

[slide: v-429]
[pause: 0.7]
V: If asked, I'd say: I never write to two systems and hope. The event is a row in the same transaction as the state change, and change capture publishes it at least once, in commit order. Consumers de-duplicate by event I-D, and the merchant can always ask us for the state directly. The cost I watch is the replication slot.
[pause: 1.0]
N: One transaction per payment works. Until a thousand of them want the same row.
[pause: 1.6]

[pause: 1.4]

## 7.4 Challenge 4: The hot merchant, and a million one-time accounts

[slide: v-430]
[pause: 1.2]
N: Challenge four. One merchant takes five thousand payments a second, and all of them touch one account. Then the opposite problem.
[pause: 1.8]

[slide: v-431]
[pause: 0.6]
I: One merchant receives five thousand payments a second. Where does that land?
[pause: 2.0]

[slide: v-432]
[pause: 1.3]
C: Inside one partition: the transaction, the journal, and the balance.
[reveal: v-433]
[pause: 0.45]
C: The shared row is marked.
[reveal: v-434]
[pause: 0.45]
C: The naive answer: update the merchant's balance inside each payment's transaction.
[reveal: v-435]
[pause: 0.45]
C: Every one of those transactions takes the same row lock, so they run one after another.
[pause: 1.1]

[slide: v-436]
[pause: 1.0]
C: The trace.
[reveal: v-437]
[pause: 0.45]
C: Five thousand a second at one merchant.
[reveal: v-438]
[pause: 0.45]
C: Each holds the balance row for about one and a half milliseconds: the row allows about six hundred and seventy a second.
[reveal: v-439]
[pause: 0.45]
C: The queue grows by more than four thousand a second, and the merchant's latency passes two seconds within a second.
[reveal: v-440]
[pause: 0.45]
C: Its payments time out and become unknowns. This challenge feeds challenge one. The lock time must be measured; the ratio is the point.
[pause: 1.0]

[slide: v-441]
[pause: 1.3]
C: The fix, on the same view.
[reveal: v-442]
[pause: 0.45]
C: The journal entries, insert only.
[reveal: v-443]
[pause: 0.45]
C: A balance projection, derived.
[reveal: v-444]
[pause: 0.45]
C: And a payout writer.
[reveal: v-445]
[pause: 0.45]
C: One level down. A payment only inserts its own entries into the merchant's partition, so there is no shared row to queue on. A projector tails the journal and keeps the balance a few seconds behind, which is fine for a dashboard. Where a check needs the balance now, a payout must not exceed available funds, a payout writer, one per merchant, reads the sum of the sixteen sub-accounts and posts the payout only if it fits.
C: It covers the hot row and the payout check. A refund's limit never needed this: it is a conditional update on one payment's row, and one payment is never hot. It does not cover a merchant larger than one primary. Then I split it into several sub-ledgers, which is a decision for that day.
[reveal: v-446]
[pause: 0.45]
C: Rejected: One balance row updated on every payment. It serialises the hot merchant on one lock; post journal lines and derive balances.
[pause: 1.1]

[slide: v-447]
[pause: 1.3]
C: This fix changes the design, so this is version four. Version three, carried.
[reveal: v-448]
[pause: 0.45]
C: New: a balance projector. It reads entries and writes balances back, so reads of a balance never touch the hot path.
[pause: 1.1]

[slide: v-449]
[pause: 1.3]
C: As a sequence.
[reveal: v-450]
[pause: 0.45]
C: Five thousand payments a second, each inserting its own entries.
[reveal: v-451]
[pause: 0.45]
C: The projector tails the journal.
[reveal: v-452]
[pause: 0.45]
C: A balance current to entry nine hundred and ninety-one million, about two seconds behind.
[reveal: v-453]
[pause: 0.45]
C: A payout of fifty thousand: the payout writer reads the sum of the sixteen sub-accounts.
[reveal: v-454]
[pause: 0.45]
C: Available, one point nine million.
[reveal: v-455]
[pause: 0.45]
C: It posts the payout only if fifty thousand fits.
[reveal: v-456]
[pause: 0.45]
C: A second payout waits its turn: one writer per merchant.
[pause: 1.1]

[slide: v-457]
[pause: 0.6]
I: Now the opposite. A million one-time virtual cards a day, each with its own account, none of them ever hot. Do you partition by account now?
[pause: 2.0]

[slide: v-458]
[pause: 0.6]
C: No. Partitioning by account would solve a problem we do not have, and bring back the one we avoided: every posting between a card and its funding account would span partitions.
[reveal: v-459]
[pause: 0.45]
C: An account is a row, not a partition. A million accounts is about a hundred megabytes. They hash with their merchant, so they spread evenly, and each is created by an upsert on first use.
[reveal: v-460]
[pause: 0.45]
C: And I would ask whether the card needs a ledger account at all. The card is an instrument, and its limit is a hold in authorisation. The ledger needs accounts for who owes whom, and the card I-D can be a tag on the entries.
[reveal: v-461]
[pause: 0.45]
C: The honest limits. Empty accounts get closed and archived. A funding account shared across many merchants is the cross-partition case, and there the posting is two steps, pending and then confirm. And past what one primary can do, a purpose-built ledger database such as TigerBeetle takes the core, for debits and credits only: it batches thousands of transfers in one request on a single leader, so a hot account is not a lock.
[pause: 0.8]

[slide: v-462]
[pause: 0.7]
V: If asked, I'd say: payments only append entries into the merchant's partition, so there is no balance row to fight over. The balance is derived, and the rare checked operation, a payout, goes through one writer per merchant. The partition key is the owner, not the account, so a million cold accounts are just rows.
[pause: 1.0]
N: The books are now fast and correct inside. What about when they disagree with the outside?
[pause: 1.6]

[pause: 1.4]

## 7.5 Challenge 5: 999,998 against 1,000,000

[slide: v-463]
[pause: 1.2]
N: Challenge five, the second half of the crux. The processor's books and ours disagree by two, and later, so does a release.
[pause: 1.8]

[slide: v-464]
[pause: 0.6]
I: The processor's settlement statement says 999,998. Your books say 1,000,000. What now?
[pause: 2.0]

[slide: v-465]
[pause: 1.3]
C: Inside reconciliation: the file, the matcher, and the break writer.
[reveal: v-466]
[pause: 0.45]
C: The matcher is marked.
[reveal: v-467]
[pause: 0.45]
C: The naive answer: compare the daily totals, and investigate if they differ.
[reveal: v-468]
[pause: 0.45]
C: A total that differs does not say which line is wrong, and a total that matches can hide two offsetting errors.
[pause: 1.1]

[slide: v-469]
[pause: 1.0]
C: The case. The difference of two is made of three breaks.
[reveal: v-470]
[pause: 0.45]
C: One line is a timing difference: captured by us, not in today's file, and it closes itself when tomorrow's file arrives.
[reveal: v-471]
[pause: 0.45]
C: One is missing at the processor, two days on. That is a claim against them, with an owner.
[reveal: v-472]
[pause: 0.45]
C: And one is settled by them for the same amount with a different fee: it does not change the count, but it is five cents wrong, times every payment like it.
[pause: 1.0]

[slide: v-473]
[pause: 1.3]
C: The fix, on the same view.
[reveal: v-474]
[pause: 0.45]
C: The expectation builder.
[reveal: v-475]
[pause: 0.45]
C: The matcher, by reference.
[reveal: v-476]
[pause: 0.45]
C: And the break writer.
[reveal: v-477]
[pause: 0.45]
C: One level down. The ledger writes what it expects to settle that day, by reference and net of fees. The raw file is stored unchanged, then joined to the expectations by reference. A match moves the payment to settled, with settlement entries. Anything else becomes a break with a type, an owner and an age.
C: It covers every line, not a total. It does not cover a processor that changes its reference format: the adapter owns that mapping.
[reveal: v-478]
[pause: 0.45]
C: Rejected: Matching on amount and time alone. Two same-amount payments in a minute are indistinguishable; match by reference.
[pause: 1.1]

[slide: v-479]
[pause: 1.3]
C: As a sequence. This is requirement four, reconcile.
[reveal: v-480]
[pause: 0.45]
C: The settlement file arrives, two point nine times ten to the eight lines, stored unchanged.
[reveal: v-481]
[pause: 0.45]
C: Expectations for the day, by reference, net of fees.
[reveal: v-482]
[pause: 0.45]
C: Matched line by line.
[reveal: v-483]
[pause: 0.45]
C: Matched lines become settled, with settlement entries.
[reveal: v-484]
[pause: 0.45]
C: A break goes to finance operations: settled by them, declined by us, ten fifty, with an owner and an age.
[reveal: v-485]
[pause: 0.45]
C: A timing break closes itself when tomorrow's file matches.
[pause: 1.1]

[slide: v-486]
[pause: 0.6]
I: There are forty thousand breaks this morning, not forty. And money has already gone out.
[pause: 2.0]

[slide: v-487]
[pause: 1.3]
C: A spike in breaks is an incident, not a backlog.
[reveal: v-488]
[pause: 0.45]
C: Finance approves, and the corrector posts.
[reveal: v-489]
[pause: 0.45]
C: Stop, find, reverse. Kill the release and hold payouts for the affected merchants. Because the journal is immutable, I can find the duplicates exactly, and post one reversing transaction each, tagged with the incident, so the audit trail shows both the error and the correction. Money already paid out is a receivable, recovered from future settlements.
C: And why the idempotency key did not stop it: it guards requests, not code paths. A unique constraint on payment and type, for types that may occur once, closes this one.
[pause: 1.1]

[slide: v-490]
[pause: 0.7]
V: If asked, I'd say: reconciliation isn't a safety net for a buggy system. It's a permanent component, because the processor's truth and ours diverge even when our code is right. I match line by line against expectations from the ledger, every difference becomes a break with an owner and an age, and a bad release is fixed by reversing entries, never by deleting history.
[pause: 1.0]
N: That fix creates the last question. Every part can now be right. How would you know when one of them isn't?
[pause: 1.6]

[pause: 1.4]

## 7.6 Challenge 6: How would you know before finance does?

[slide: v-491]
[pause: 1.2]
N: Challenge six is observability, and in this question it is about money, not about servers.
[pause: 1.8]

[slide: v-492]
[pause: 0.6]
I: What do you watch, and what alert fires before finance notices that something is wrong?
[pause: 2.0]

[slide: v-493]
[pause: 1.3]
C: Back to the container view, version four.
[reveal: v-494]
[pause: 0.45]
C: Finance operations is marked: they find out last.
[reveal: v-495]
[pause: 0.45]
C: The naive answer: error rate and latency alerts on every service.
[reveal: v-496]
[pause: 0.45]
C: And they are green. Every container is healthy, and fewer payments are being approved.
[pause: 1.1]

[slide: v-497]
[pause: 1.0]
C: The trace.
[reveal: v-498]
[pause: 0.45]
C: At two a.m. a change at one processor adds six points of declines for one country.
[reveal: v-499]
[pause: 0.45]
C: API errors zero percent, latency normal, every dashboard green.
[reveal: v-500]
[pause: 0.45]
C: At five, merchants' conversion drops, and nobody is paged.
[reveal: v-501]
[pause: 0.45]
C: At nine, finance sees fewer settlements than expected.
[reveal: v-502]
[pause: 0.45]
C: And at nine thirty the first merchant ticket. Declines are a valid answer from the processor, so no service was unhealthy.
[pause: 1.0]

[slide: v-503]
[pause: 1.3]
C: The fix changes no box. It adds checks on the boxes we have.
[reveal: v-504]
[pause: 0.45]
C: At the A-P-I: a synthetic payment, a test card, every minute per processor.
[reveal: v-505]
[pause: 0.45]
C: In the database: debits minus credits equal zero, checked continuously, and it pages the moment it is not.
[reveal: v-506]
[pause: 0.45]
C: In reconciliation: unmatched amount by age.
[reveal: v-507]
[pause: 0.45]
C: One level down. Approval rate per processor and country against its baseline. The count and age of unknown outcomes. Slot lag and outbox age. Unmatched amount by age. And the ledger sum. It covers a silent decline, a stuck unknown, a stalled relay and a growing break. It does not cover a slow drift.
[reveal: v-508]
[pause: 0.45]
C: Rejected: Alerting on the error rate. Finance finds the break before the dashboard does; measure unmatched count and age.
[pause: 1.1]

[slide: v-509]
[pause: 1.3]
C: As a sequence.
[reveal: v-510]
[pause: 0.45]
C: A synthetic payment, a test card, every minute per processor.
[reveal: v-511]
[pause: 0.45]
C: Through the same A-P-I and the same reference.
[reveal: v-512]
[pause: 0.45]
C: Captured in four hundred and ten milliseconds.
[reveal: v-513]
[pause: 0.45]
C: Success and latency, per processor, go to monitoring.
[reveal: v-514]
[pause: 0.45]
C: Where approval rate per processor and country is compared with its baseline: minus six points. That alert fires at two oh five, not nine.
[reveal: v-515]
[pause: 0.45]
C: And the ledger sum, checked continuously.
[pause: 1.1]

[slide: v-516]
[pause: 1.0]
C: One more habit: read symptoms in pairs. A number alone is not a diagnosis.
[reveal: v-517]
[pause: 0.45]
C: Approval down at one processor with errors flat: a processor change.
[reveal: v-518]
[pause: 0.45]
C: Approval down everywhere with fraud declines up: our fraud service.
[reveal: v-519]
[pause: 0.45]
C: Unknowns up with the inquiry still succeeding: the processor is slow, and the machinery works.
[reveal: v-520]
[pause: 0.45]
C: Outbox age and slot lag both up: the relay has stalled.
[reveal: v-521]
[pause: 0.45]
C: And unmatched amount up for one reference prefix: a format change in one adapter.
[pause: 1.0]

[slide: v-522]
[pause: 0.6]
I: The approval rate drops slowly: half a point a week.
[pause: 1.5]

[slide: v-523]
[pause: 0.6]
C: A slow drift hides under any threshold. So compare like with like: week over week by processor, country and card type, and look at the mix of decline codes, not only the total.
[reveal: v-524]
[pause: 0.45]
C: And alert on the slope. A drift of two tenths of a point a week for three weeks goes to a person, not to a pager.
[pause: 0.8]

[slide: v-525]
[pause: 0.7]
V: If asked, I'd say: I watch the money, not the servers. Approval rate per processor and country against baseline, the count and age of unknown outcomes, outbox and slot lag, unmatched amount by age, and a continuous check that the ledger sums to zero, which pages immediately. A synthetic payment per processor tells me before a merchant does.
[pause: 1.6]

[pause: 1.4]

## 8 Recap

[slide: v-526]
[pause: 1.2]
C: The recap. One picture, one sentence per path, the mistakes that cost most, and the thesis.
[pause: 1.8]

[slide: v-527]
[pause: 1.3]
C: Version four, the final design. The same picture as version one, with the mechanism labels from the theory chapter.
[reveal: v-528]
[pause: 0.45]
C: The A-P-I: the key, inserted first.
[reveal: v-529]
[pause: 0.45]
C: The payment service: the state machine, with unknown.
[reveal: v-530]
[pause: 0.45]
C: The ledger database: the journal and the outbox, partitioned by merchant.
[reveal: v-531]
[pause: 0.45]
C: The adapter: our reference on every call.
[reveal: v-532]
[pause: 0.45]
C: The relay: change capture, in commit order.
[reveal: v-533]
[pause: 0.45]
C: The inquiry job, which ends every unknown.
[reveal: v-534]
[pause: 0.45]
C: Reconciliation, with owned breaks.
[reveal: v-535]
[pause: 0.45]
C: And the balance projector, derived and never incremented.
[pause: 1.1]

[slide: v-536]
[pause: 1.0]
C: One sentence per path.
[reveal: v-537]
[pause: 0.45]
C: Pay: key first, attempt committed, call by reference, one transaction for state, entries and event.
[reveal: v-538]
[pause: 0.45]
C: Adjust: a new transaction, dated now, with the limit in one conditional update.
[reveal: v-539]
[pause: 0.45]
C: Notify: an outbox row, read from the log, published at least once, de-duplicated by event I-D.
[reveal: v-540]
[pause: 0.45]
C: Reconcile: expectations from the ledger, matched by reference, every break owned.
[reveal: v-541]
[pause: 0.45]
C: Explain: a sum over immutable entries, in one partition.
[pause: 1.0]

[slide: v-542]
[pause: 0.6]
N: The common mistakes.
[reveal: v-543]
[pause: 0.45]
N: On correctness: a distributed transaction with the bank, a balance column as the truth, a timeout treated as a failure, floats, keys that are checked instead of inserted, and partitioning by account.
[reveal: v-544]
[pause: 0.45]
N: On operations: events published outside the transaction, history edited, reconciliation by totals, no owner for breaks, and dashboards with no money on them.
[pause: 0.8]

[slide: v-545]
[pause: 0.6]
C: What it is: a state machine per payment, an idempotent A-P-I, an immutable double-entry journal partitioned by merchant, and reconciliation.
[reveal: v-546]
[pause: 0.45]
C: The trade: pending answers and a reconciliation team, in exchange for never guessing.
[reveal: v-547]
[pause: 0.45]
C: The risk: the unknown path runs rarely, so I'd test it every day, and I'd watch the replication slot.
[reveal: v-548]
[pause: 0.45]
C: Next: a gateway first, if the company is small; harden the inquiry per processor; and make breaks an owned, aged workflow.
[pause: 0.8]

[slide: v-549]
[pause: 0.7]
V: I can't get exactly-once across the boundary, so I get one effect per intent: a key inserted first, a reference on every call, a state for not knowing, and an inquiry that ends it. Every movement is a balanced, immutable entry, so any balance is a sum I can explain. And because the outside world's books will disagree with mine anyway, reconciliation is part of the design, with owners.
[pause: 1.5]
C: Thanks for watching. The written design, with every number, the technology comparisons and the internals of each tool, is linked below.
[pause: 1.6]
