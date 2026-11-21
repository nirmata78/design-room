# SD-82 Instant credit at the point of sale: reference solution (Staff L6/L7)

<!-- Video script for slide-video-kit/scripts/build_video.py. [slide: v-NNN] = frames/v-NNN.png, the number printed on every slide.
     Speakers: C candidate · I interviewer · V key line (slower) · N coach. Generated from src/*.py: edit the sources, not this file. -->
<!-- voices: N=af_heart@0.92 I=bf_emma@0.95 C=am_michael@0.9 V=am_michael@0.84 -->
<!-- labels: N=COACH -->
<!-- say: POS=P-O-S SSN=S-S-N APR=A-P-R API=A-P-I APIs=A-P-Is ID=I-D IDs=I-Ds SLO=S-L-O SLOs=S-L-Os SLI=S-L-I SLIs=S-L-Is SQL=S-Q-L EM=E-M AUX=aux QR=Q-R KB=kilobytes GB=gigabytes TB=terabytes p95=P-ninety-five p99=P-ninety-nine p50=P-fifty C4=C-four CI=C-I -->


## 0 Cold open

[slide: v-001]
[pause: 1.2]
C: Eight applications a second at the busiest moment of the week. Any database takes that. And yet this question fails strong engineers, because the hard parts here are not load.
[pause: 1.8]

[slide: v-002]
[pause: 0.6]
I: A customer at a merchant's counter scans a Q-R code to pay a twelve hundred dollar bill in instalments. Design the system that decides within a few seconds whether to lend, shows the offers, and creates the loan when the customer accepts.
[pause: 1.5]

[slide: v-003]
[pause: 1.3]
C: Here is the hook. A credit bureau answers in about six tenths of a second, and one time in ten it takes four seconds, while a customer stands at the counter. Every call to it costs about a dollar and may show on the customer's credit file. So we can't wait, and we can't race two bureaus either.
C: Then a phone drops between accept and the answer, and the customer taps again on the merchant's tablet. And fourteen months later a regulator asks why someone was declined. None of that is throughput. It is time, evidence and money pulling three ways, and that picture is the whole tension.
[pause: 1.1]

[slide: v-004]
[pause: 1.0]
N: Five axes. The weak answer shards a database that sees eight writes a second. The strong answer knows a credit pull cannot be undone, and that a timeout is a credit decision someone has to own.
C: One rule I'll keep for the whole round: every degraded path is a credit decision with an owner and a cap, never an engineering default.
[pause: 1.0]

[slide: v-005]
[pause: 0.7]
V: Instant credit at the counter is a regulated decision under a deadline set by slow, paid vendors, followed by one atomic step. The load is tiny. The grade is on the slow edges.
[pause: 1.6]

[slide: v-006]
[pause: 0.6]
C: The order. Requirements, numbers and a short theory chapter. Then the A-P-I and the data, and a design in three versions, each answering the objection to the one before.
C: Then most of the time goes to eight challenges that break it, where each fix creates the next question. A build cost, and a recap.
[pause: 0.8]

[pause: 1.4]

## 1 Requirements and scope

[slide: v-007]
[pause: 1.2]
C: Six questions before I draw anything. Each answer moves the design, and two of them only make sense if you know how lending works.
[pause: 1.8]

[slide: v-008]
[pause: 0.6]
C: How many applications?
I: Two million a month. The Saturday peak is about ten times the average.
C: That is under one a second on average and about eight at the peak. I'll do the arithmetic in a minute, but I can already say the load is not the problem.
[pause: 0.6]

[slide: v-009]
[pause: 0.6]
C: How long can the customer wait at the counter?
I: Offers on screen in under three seconds for ninety-five percent of applications. Ten seconds is a lost sale.
C: Three seconds from submit to offers, at the ninety-fifth percentile. That number will set one deadline for every vendor call.
[pause: 0.6]

[slide: v-010]
[pause: 0.6]
C: Who is the lender of record? Us, or a partner bank?
I: We decide, on the partner bank's credit policy, and we service the loan. The bank is the lender of record.
C: That matters. Every credit policy version needs the bank's approval, our decision records are the bank's records too, and the money to pay the merchant flows through the bank.
[pause: 0.6]

[slide: v-011]
[pause: 0.6]
C: Which vendors do we call, and how fast are they?
I: Two credit bureaus. Median six tenths of a second, the ninety-ninth percentile several seconds, about one percent errors. An identity and fraud vendor, four hundred milliseconds at the ninety-ninth. And optional bank-account data, seconds to minutes.
C: So the bureau's tail sets the deadline, and the bank data is never something we wait for at the counter.
[pause: 0.6]

[slide: v-012]
[pause: 0.6]
C: What do those calls cost?
I: About a dollar a bureau pull. Identity checks, about five cents.
C: Then we never race two bureaus. Every pull is paid, and it may show on the customer's credit file as an inquiry.
[pause: 0.6]

[slide: v-013]
[pause: 0.6]
C: Which rules shape the system?
I: Cost disclosures before the customer signs. The principal reasons for every decline. Records kept about seven years. And fairness testing of models.
C: Three architecture decisions in one answer. Decisions must carry reasons about the applicant, so our vendor being slow can never be a reason. The disclosure version is part of the loan. And a decision must replay years after the model that made it is gone.
[pause: 0.6]

[slide: v-014]
[pause: 0.6]
C: Four functional requirements. One, apply: the customer scans the merchant's code, identity goes into a vault, and an application exists. A retry returns the same application. Two, decide: identity, fraud and credit data under one deadline, and the answer is offers, a refer, or a decline with reasons.
C: Three, accept and book: the customer accepts one disclosed offer, and exactly one loan is booked. Four, fund and hand off: the merchant is paid net of fees, the loan goes to servicing, and decline notices go out. Each of these gets a numbered flow later.
[pause: 0.8]

[slide: v-015]
[pause: 0.6]
C: The numbers, all initial targets. Offers on screen in three seconds at the ninety-fifth percentile. Zero loans booked twice, or booked without acceptance of the exact disclosure shown. Every decision replayable for seven years. And raw identity data nowhere except a vault.
C: Plus three more: three nines in merchant hours, the merchant funded within one business day, and every degraded path under a cap that someone signed.
[pause: 0.8]

[slide: v-016]
[pause: 0.6]
C: In scope: apply, identity, decide, offers, refer, accept, book, the funding instruction, the handoff to servicing, and decline notices.
C: Out, on purpose, and I'll say it aloud. Repayments and the ledger: that's a servicing system with its own hard problems. Card authorisation. Merchant onboarding and merchant fraud, which is a merchant-risk system. Model training: I'll treat a model as a versioned artefact we load. Collections, and the payment rail itself.
[pause: 0.8]

[slide: v-017]
[pause: 0.7]
V: The core is three things. An orchestrator that decides under one deadline. A state machine whose only atomic step is accept to book. And a record and a vault.
[pause: 0.8]
N: The candidate named the core before drawing. That is the scoping signal: what the system is in a sentence, and what it is not.
[pause: 1.6]

[pause: 1.4]

## 2 Estimates

[slide: v-018]
[pause: 1.2]
C: Numbers next. Three of them really matter, and each one changes a decision. I'll label them: given, derived or illustrative.
[pause: 1.8]

[slide: v-019]
[pause: 1.0]
C: The load. Two million a month, divided by about two point six million seconds, is about eight tenths of an application a second. Ten times that at the Saturday peak: eight a second. Each application moves through about six states, so about fifty committed writes a second. One relational database takes that without noticing.
C: Each application fans out to about four vendor calls: thirty-two calls a second, and with a two-second deadline about sixty-four in flight. So the pressure is on the vendors, their latency and their contract limits, not on our servers.
[pause: 1.0]

[slide: v-020]
[pause: 1.0]
C: The money. If every application pulls a bureau report at about a dollar, that's two million dollars a month, far more than the computers. If a fifth of applicants re-apply within a month, and the contract and the rules let us reuse a recent report, that saves about four hundred thousand a month. So the report store and its retention rule are part of the design.
C: Identity checks add about a hundred thousand. And with sixty percent approved and seventy percent of those accepted, that is about eight hundred and forty thousand loans a month, about a billion dollars at twelve hundred each. Illustrative, but it tells me the merchant is paid in a daily batch, not per request.
[pause: 1.0]

[slide: v-021]
[pause: 1.0]
C: The third number is the one that shapes the design. If about two percent of bureau calls miss the deadline and about one percent fail, about three percent of applications reach the deadline with no bureau answer. Sixty thousand a month, fourteen a minute at the peak. That is a weekly volume, so what we do then is a policy with counters, not an exception handler.
C: And a twenty-minute bureau outage at the peak is nine thousand six hundred applications. Approve them all and we lend eleven and a half million dollars nobody scored. Decline them all and we lose about four thousand loans. Neither extreme. That's challenge two.
[pause: 1.0]

[slide: v-022]
[pause: 1.0]
C: Records. Each decision with its inputs, mostly the bureau report, is about fifty kilobytes. A hundred gigabytes a month, about eight terabytes over seven years. So the full record goes to encrypted object storage with a retention lock, and the database keeps a reference and the hot fields.
[pause: 1.0]

[slide: v-023]
[pause: 1.3]
C: The latency budget, from submit to offers on screen. The phone to our A-P-I and the first state write, about two hundred milliseconds. The vendors, two seconds: one deadline for all of them. Model, policy and pricing, about two hundred and fifty. Writing the record and pushing the offers to the phone, about two hundred and fifty. That is two point seven seconds, with three hundred to spare.
C: So the deadline is derived from the promise, not picked from experience. And nothing optional, like bank data, can ever sit on this path.
[pause: 1.1]

[slide: v-024]
[pause: 0.6]
C: So, before I draw a single box, the numbers have already decided four things. One relational database, because the load is tiny. No races between bureaus, because every pull is paid and the bill is already the largest line. A signed policy for missing data, because it happens fourteen times a minute at the peak. And object storage for decision records, because they're large, written once, and rarely read.
C: Notice what the numbers did not ask for: a cache, a queue in front of the database, or a sharding scheme. Saying that out loud is part of the answer.
[pause: 0.8]

[pause: 1.4]

## 3 Theory

[slide: v-025]
[pause: 1.2]
C: A short theory chapter before the design, so the design can lean on it. What this system is and is not, its properties, the central tension, six mechanisms, an options matrix, and the failure catalogue.
[pause: 1.8]

[slide: v-026]
[pause: 0.7]
V: A credit decisioning system gathers data from paid vendors under one deadline, returns an explainable decision with priced offers, and books exactly one loan when the customer accepts an offer they were shown.
[pause: 1.0]
C: Every clause is load-bearing. Paid vendors: every call costs money and may be recorded, so we never race them. One deadline: the customer is at a counter. Explainable: a decline carries reasons about the applicant, and they replay years later. Exactly one loan: one atomic step. And an offer they were shown: the disclosure version is part of the contract.
[pause: 1.6]

[slide: v-027]
[pause: 0.6]
C: Four neighbours it gets confused with. It is not a scoring model: the model is one input, the policy rules decide, and pricing prices, each with its own version. It is not a payment: no money moves when the customer accepts. The merchant is funded later.
C: It is not a saga: only one step has to be atomic, and a credit pull cannot be compensated, because it happened. And it is not an underwriting queue: refer means we finish in minutes, by text.
[pause: 0.8]

[slide: v-028]
[pause: 0.6]
C: The properties, stated separately. Safety, what must never happen. S-one: a loan booked twice, or without acceptance of the exact offer shown. S-two: a decline or a price without reasons about the applicant that we can reproduce. S-three: raw identity outside the vault. S-four: more than one pull per bureau per application.
C: Liveness, what must eventually happen. L-one: every application gets an answer within the deadline. L-two: every booked loan is funded and handed to servicing, with one effect. L-three: every referred application is finished within ten minutes. Every fix from here names the property it serves.
[pause: 0.8]

[slide: v-029]
[pause: 1.3]
C: The central tension. Identity answers in four tenths of a second, fraud in about the same, the bureau usually in six tenths. One time in ten the bureau takes four seconds. The deadline line is at two seconds, and the sale is lost at ten.
C: Waiting longer adds evidence and loses sales. Deciding early keeps the sale and adds risk. Asking a second bureau adds evidence, another dollar and another inquiry. Every choice from here is a point in that triangle, and the important ones belong to credit risk, not to a timeout setting.
[pause: 1.1]

[slide: v-030]
[pause: 0.6]
C: Mechanism one, scatter-gather under one deadline, with a circuit breaker per vendor. It protects L-one and S-four. All vendor calls go out at once, and we decide at the deadline with what has arrived. A breaker stops calls to a vendor that is failing for everyone. It rules out one slow vendor setting the customer's wait. It costs decisions with data missing, which mechanism two has to decide.
[pause: 0.8]

[slide: v-031]
[pause: 0.6]
C: Mechanism two, a missing-data policy table. It protects S-two and L-one. A versioned table inside the credit policy: ask the second bureau, decide small and known customers under a cap, refer, or decline with a real reason. Each row has a counter and a dashboard. It rules out approve with partial data as a code default, and declines whose real reason is our own outage. It costs a refer path, an exposure counter, and an owner in credit risk who signs it.
[pause: 0.8]

[slide: v-032]
[pause: 0.6]
C: Mechanism three, the application as a state machine in the database. It protects S-one and L-one. Every transition is one committed row, with a version number used as an optimistic lock, and idempotency keys on create and accept. It rules out two workers moving one application, and lost progress when a phone drops. It costs a write per transition, which at fifty a second is nothing.
[pause: 0.8]

[slide: v-033]
[pause: 0.6]
C: Mechanism four, one local transaction for booking. It protects S-one and L-two. Move the status at a version, insert the loan under a unique constraint on the application, insert an outbox row, and commit. A relay then publishes the row. It rules out two loans for one application, and a loan that funding never hears about. It costs a relay, and consumers that de-duplicate.
[pause: 0.8]

[slide: v-034]
[pause: 0.6]
C: Mechanism five, an immutable decision record. It protects S-two. Written once: the frozen inputs, including the report by reference, the feature vector and which calls were missing; every version; and the outputs with ranked reasons. Old models stay loadable. It rules out declines nobody can explain, and a re-run that contradicts the notice we sent. It costs eight terabytes over seven years and a model registry kept just as long.
[pause: 0.8]

[slide: v-035]
[pause: 0.6]
C: Mechanism six, an identity vault. It protects S-three. Identity is tokenised at apply, and only the vault and the vendor adapters, which must send real values, ever see them. Every detokenise is logged with its purpose. It rules out identity spreading into rows, logs, exports and training sets. It costs a small, critical service and a hop at each vendor call.
[pause: 0.8]

[slide: v-036]
[pause: 1.0]
C: The options matrix. A, sequential calls in the request: the bureau's tail alone breaks three seconds. B, parallel with hedging, racing two bureaus: fast, but every race is two paid pulls and two inquiries. C, a saga with a compensation for every step: a credit pull cannot be undone, so the compensations do nothing but add code. F, a manual queue: ten seconds is already a lost sale.
C: D, a durable workflow engine, is the honest equal: it works, and I'd choose it when steps last hours or days, like document upload or manual review. I pick E: a database state machine, one deadline, the policy table, and an atomic booking with an outbox. What it gives up: the timers, retries and relay that a workflow engine would give us for free.
[pause: 1.0]

[slide: v-037]
[pause: 1.0]
C: The failure catalogue, which becomes the challenge list. The bureau slow, then down for everyone. The phone drops, then funding fails after booking. A decision nobody can explain. A new model that approves more. Identity data spreading. And a silent approval drop.
C: One more I'll name and leave: merchant fraud, a merchant ringing up fake sales. That's a merchant-risk system, and it plugs in at onboarding and at funding.
[pause: 1.0]

[pause: 1.4]

## 4 API and entities

[slide: v-038]
[pause: 1.2]
C: The A-P-I next, because writing the contract forces the hard semantics into the open: retries, expiry, and what the customer actually agreed to.
[pause: 1.8]

[slide: v-039]
[pause: 1.0]
C: Apply returns at once, two-oh-two, with an application I-D, because the decision takes seconds and the phone may drop. It carries an idempotency key, so a retry from the point of sale returns the same application instead of pulling the bureau again. And it carries a vault token, never the identity itself.
C: The phone polls or receives a push. The answer is offers with an expiry, fifteen minutes, because prices and credit files go stale. Or referred, with a promise time, or declined. This serves FR-one and FR-two, and writes the application entity.
[pause: 1.0]

[slide: v-040]
[pause: 1.0]
C: Accept names the offer and the version of the disclosure the customer saw, because that version is part of the contract, and it returns the loan. A second accept, from any device, returns the same loan.
C: Then the event, loan booked, with the loan, the merchant, the principal and the merchant fee. It is delivered at least once, so funding and servicing de-duplicate by event I-D. FR-three and FR-four.
[pause: 1.0]

[slide: v-041]
[pause: 1.0]
C: Inside, the decision interface is the contract between the applications team and the decisioning platform. Outcome, offers, ranked reasons, the three versions, and two fields people forget: which inputs were missing, and which degraded path was taken.
C: Without those two, the applications team can't show pending for a refer, and nobody can prove that the caps credit risk signed actually hold.
[pause: 1.0]

[slide: v-042]
[pause: 1.3]
C: The conceptual model, in one breath. An applicant, known only by a token, submits applications. Each application makes paid vendor calls. Each is decided once. A decision holds offers. An application books at most one loan. And a loan is paid out by funding transfers.
[pause: 1.1]

[slide: v-043]
[pause: 1.3]
C: The physical tables. The application row is the state machine, with a version for the optimistic lock and a token instead of identity. The decision row is written once, never updated, with the versions and a link to the full record. The loan has a unique constraint on the application: that one constraint makes a double tap harmless.
C: The outbox commits with the loan. Every vendor call is a row with its cost, because the bureau bill is the largest line. And the vault is a separate store that only two components can read.
[pause: 1.1]

[slide: v-044]
[pause: 1.0]
C: Five stores, and whether we can lose them. The application database, no: a synchronous standby in another zone. Decision records, no: a retention lock for seven years. The vault, no: it is the only copy. The event log can be rebuilt from the outbox. And the report store can be lost: a miss costs a dollar, not correctness.
[pause: 1.0]

[pause: 1.4]

## 5 High-level design

[slide: v-045]
[pause: 1.2]
C: The design in three versions. Before each new one, I'll say the objection it answers.
[pause: 1.8]

[slide: v-046]
[pause: 1.3]
C: Version one, so we have something to break. The phone and the point of sale call an A-P-I edge, which calls one application service. It calls the identity vendor, then the bureau, in turn, scores, and writes the application and the loan to one database.
C: Three objections. The latencies add up, so the bureau's slow tail alone breaks three seconds. A dropped phone retried on another device can book twice. And nothing records why we decided.
[pause: 1.1]

[slide: v-047]
[pause: 1.3]
C: Version two answers latency and correctness. A decision orchestrator, outlined blue, calls all vendors at once under one deadline, with a breaker per vendor. The application becomes a state machine in the database. Booking is one transaction that also writes an outbox row, and a relay publishes it to an event log. And scoring becomes a versioned policy engine: model, policy, pricing.
C: What it leaves: what we do when the bureau is missing at the deadline, identity data in every row and log, no record that survives a model change, and nobody paying the merchant.
[pause: 1.1]

[slide: v-048]
[pause: 1.3]
C: Version three. The identity vault, top left, tokenises at apply, and only the vendor adapters inside the orchestrator detokenise. Decision records go to encrypted object storage, written once. The missing-data policy table lives in the policy engine, versioned with the credit policy. And funding consumes loan booked from the log, then hands the loan to servicing.
C: The objection it answers: this must be regulated, explainable and owned. What it leaves are the details, and those are the challenges.
[pause: 1.1]

[slide: v-049]
[pause: 1.3]
C: FR-one, apply, by the numbers. One, the phone posts the application with an idempotency key. Two, the A-P-I edge tokenises identity in the vault. Three, the application service creates the row. Four, the row commits, status started. Five and six, the answer goes back: two-oh-two with the application I-D. From step two on, nothing but the vault sees the identity.
[pause: 1.1]

[slide: v-050]
[pause: 1.3]
C: FR-two, decide. One, the application service asks the orchestrator. Two, the vendor adapters detokenise in the vault, only for the calls that need it. Three, identity, fraud and bureau go out at once. Four, the answers come back, or the deadline passes and the miss is recorded.
C: Five, the policy engine computes features, runs the model, the policy rules and pricing. Six, the decision record is written once. Seven, the decision goes back and the row becomes offered, referred or declined. Eight, the offers reach the phone.
[pause: 1.1]

[slide: v-051]
[pause: 1.3]
C: FR-three, accept and book. One, the phone posts accept with the offer, the disclosure version and a key. Two, the edge passes it on. Three, one transaction: the status moves to booked at a version, the loan is inserted under its unique constraint, and the outbox row is inserted. Four and five, two-oh-one with the loan I-D.
[pause: 1.1]

[slide: v-052]
[pause: 1.3]
C: FR-four, fund and hand off. One, the booking transaction wrote the outbox row. Two, the relay publishes loan booked to the event log. Three, funding adds the loan to tonight's batch for the merchant, and servicing opens the repayment schedule. None of it is in the customer's wait.
[pause: 1.1]

[slide: v-053]
[pause: 1.3]
C: The context view. On the left, the customer at the counter and the merchant. In the middle, us: apply, decide, book, fund. On the right, the credit vendors, slow and paid; the partner bank, the lender of record, which pays merchants; and servicing, which takes the loan after booking.
[pause: 1.1]

[slide: v-054]
[pause: 1.3]
C: The containers. The A-P-I edge: merchant authentication and idempotency keys. The application service owns the state machine and booking, and has no vendor code in it. The orchestrator owns time: deadlines, breakers and rate limits. The policy engine is a pure function of inputs and versions, so it can replay.
C: The vault is the regulated part, kept small. The database holds correctness in its constraints. The event log decouples the counter from funding, servicing and notices. Funding is the only container that moves money. And decision records sit in object storage with a retention lock.
[pause: 1.1]

[slide: v-055]
[pause: 1.3]
C: Apply and decide as a sequence. The phone posts; it gets two-oh-two, started. The application service asks the orchestrator to decide with a deadline two seconds out. Identity, fraud and bureau go out at once and come back at four tenths, three and a half tenths and six tenths of a second. Features, model version nine, policy thirty-one, pricing twelve: approve, three offers, reasons. The record is written once, and offers are pushed to the phone.
[pause: 1.1]

[slide: v-056]
[pause: 1.3]
C: Accept and book. The accept arrives with the offer and the disclosure version. Begin. Update the application where it is still offered and at version seven. Insert the loan, insert the outbox row, commit. One row changed, committed, two-oh-one. Later, the relay polls unpublished outbox rows, publishes loan booked, and only then marks them published. At least once, by design.
[pause: 1.1]

[slide: v-057]
[pause: 1.0]
C: One usual application in time. Submit at zero. By two hundred milliseconds the identity is a token and the row is committed. The three vendor calls go out together, and the deadline is set for two point two seconds. Fraud answers at five fifty, identity at six hundred, the bureau at eight twenty.
C: At that moment every required answer is in, so the orchestrator moves on without waiting for the deadline. The deadline is a ceiling, not a wait. Model, policy and pricing finish around eleven hundred, the record is written, and the offers are on the phone at about one point three seconds. The slow case is the one the challenges are about.
[pause: 1.0]

[slide: v-058]
[pause: 0.7]
V: The core is small and boring on purpose: one database, one atomic step. The design lives at the slow edges.
[pause: 0.8]
N: Every box had a reason before it was drawn.
[pause: 1.6]

[pause: 1.4]

## 6 Bridge

[slide: v-059]
[pause: 1.2]
V: It works. Where does it break first?
[pause: 1.8]

[slide: v-060]
[pause: 1.3]
C: The baseline with eight attack points. The credit vendors: first slow, then down for everyone. The application service and its database: a phone that drops between accept and the answer. Funding: a transfer that fails after booking. The policy engine: a decision nobody can explain, then a new model. The vault: where identity lives. And the orchestrator: how we would know any of it is broken. I'll take them in an order where each fix creates the next question.
[pause: 1.1]

[pause: 1.4]

## 7 Challenges

[slide: v-061]
[pause: 1.2]
C: Eight challenges, each the same way: the question, the naive answer, a case with numbers, where it breaks, the fix, why it works, the push on the fix itself, and what I'd say in the room.
[pause: 1.8]

[pause: 1.4]

## 7.1 Challenge 1: The bureau is slow

[slide: v-062]
[pause: 1.2]
N: Challenge one. One bureau call in ten takes four seconds: what does the customer at the counter see, and what does it cost?
[pause: 1.8]

[slide: v-063]
[pause: 0.6]
I: One bureau call in ten takes four seconds today. What does the customer at the counter see?
[pause: 2.0]

[slide: v-064]
[pause: 1.3]
C: The naive answer: wait, and if the bureau is slow, send the same request to the second bureau and take whichever answers first. That's a hedged request, and for an internal read it's a fine idea. Here, look at the red vendors box. Waiting misses the promise. Racing pays twice.
[pause: 1.1]

[slide: v-065]
[pause: 1.0]
C: The trace. Submit at ten o'clock. At fifty milliseconds, identity, fraud and bureau A go out. Identity and fraud are back by four tenths. At one second, the hedge sends the same pull to bureau B, which answers at one point seven, so offers appear at about two seconds. Good, until bureau A answers at four point one: a second paid pull, and a second inquiry on the customer's credit file.
C: Without the hedge, the offers appear at about four point four seconds, past the three-second promise. So both answers are wrong, and they are wrong in different currencies: time, and money.
[pause: 1.0]

[slide: v-066]
[pause: 1.3]
C: The fix lives in the orchestrator, outlined green. All required calls go out at once, and it decides at a two-second deadline with what has arrived. If everything arrives earlier, it decides earlier. A circuit breaker per vendor stops calling a vendor that is failing for everyone, so nobody waits on a known outage.
C: And the second bureau is called only after an error or an open breaker, never as a race against a slow but healthy first call. L-one is bounded by the deadline. S-four holds, because a second pull happens only when the first has failed.
[pause: 1.1]

[slide: v-067]
[pause: 1.3]
C: As a sequence. Check and pull go out at time zero. Identity is back at four tenths. At two seconds, the deadline: bureau A is silent and its breaker is still closed, so this is one slow call, not an outage. The orchestrator decides with what arrived, through the missing-data policy, and does not race bureau B. Bureau A's report lands at four point one, and it is recorded.
[pause: 1.1]

[slide: v-068]
[pause: 1.0]
C: In code. Start a task per required vendor. Wait for all of them, with one timeout. Anything still pending is not cancelled: a callback records its answer when it lands, because it was billed anyway. Then the code hands the features and the list of what is missing to the policy. The code never decides what missing means. The signed policy does.
[pause: 1.0]

[slide: v-069]
[pause: 0.6]
I: The bureau's answer arrives at four point one seconds, after you decided. You paid for it. What do you do with it?
[pause: 2.0]

[slide: v-070]
[pause: 0.6]
C: Three things. Record it: the call happened and was billed, so it's a row with its cost. Use it: if the application was referred because the bureau was missing, the late answer finishes it, and the customer gets a text with offers. And never rewrite the past: an offer already shown stays as shown, because the decision record says what we knew at the time. Where the contract allows, the report is kept for a re-application.
C: The honest limit: a deadline means about three percent of applications reach the missing-data path every day. Which is the next question.
[pause: 0.8]

[slide: v-071]
[pause: 0.7]
V: If asked, I'd say: all vendors at once, one deadline, a breaker per vendor. I never race two bureaus, because each pull is paid. A late answer is recorded and finishes a refer.
[pause: 1.0]
N: That fix creates the next question: what if the bureau is missing for everyone?
[pause: 1.6]

[pause: 1.4]

## 7.2 Challenge 2: The bureau is down for everyone

[slide: v-072]
[pause: 1.2]
N: Challenge two. Bureau A is down for twenty minutes at the Saturday peak: who decides what happens at the counter, and how much can it cost?
[pause: 1.8]

[slide: v-073]
[pause: 0.6]
I: Bureau A is down for everyone for twenty minutes on a Saturday. What happens at the counter?
[pause: 2.0]

[slide: v-074]
[pause: 1.3]
C: Two naive answers, and they're opposites. Approve with whatever data we have, or decline until it's back. Both are credit-risk decisions made by an engineer in a catch block. The red boxes: the vendor is gone, and the policy engine has no rule for it.
[pause: 1.1]

[slide: v-075]
[pause: 1.0]
C: The trace. Eleven o'clock on Saturday, bureau A starts timing out for everyone. Twenty minutes at eight a second is nine thousand six hundred applications. Approve them all, and we offer about eleven and a half million dollars of credit nobody scored.
C: Decline them all, and we lose about four thousand loans, and we owe nine thousand six hundred decline notices whose only true reason is that our vendor was down. That is not a reason about the applicant.
[pause: 1.0]

[slide: v-076]
[pause: 1.3]
C: The fix is in the policy engine, outlined green. A missing-data table, versioned with the credit policy, signed by credit risk and approved by the partner bank. Engineering builds the mechanism, with a counter, a cap and a dashboard per row. Credit risk owns the numbers in it.
[pause: 1.1]

[slide: v-077]
[pause: 1.3]
C: Four rows, in order. One, the second bureau, after the first one's breaker has opened. Not a race: the first is known to be failing. Two, decide without a bureau, only for returning customers in good standing, at most five hundred dollars, under a daily cap of two hundred and fifty thousand. At most five hundred such loans a day.
C: Three, refer: we'll finish in about two minutes by text, and the merchant sees pending, not declined. Four, decline, but only with a reason about the applicant. Everyone gets an answer, nobody is declined for our outage, and the worst case is the cap.
[pause: 1.1]

[slide: v-078]
[pause: 1.3]
C: A refer as a sequence. Bureau A's breaker is open, and bureau B's bucket is empty this second. The customer is told: referred, we'll finish in two minutes by text. The application waits in the refer queue, oldest first. When a token frees up, bureau B is pulled, the report arrives, and the customer gets a text: your offers are ready.
[pause: 1.1]

[slide: v-079]
[pause: 0.6]
I: Bureau B's contract allows five calls a second. You're sending eight.
[pause: 2.0]

[slide: v-080]
[pause: 0.6]
C: A token bucket per vendor at the contract rate: five tokens a second for bureau B. A call without a token is not sent; that application is referred. Three a second over the limit for twenty minutes is about three thousand six hundred referred. The queue drains oldest first, when tokens free up or bureau A's breaker half-opens, inside the ten-minute promise. And the cap for row two is split per merchant, so one busy merchant can't spend the whole day's cap in an hour.
C: The honest limit: some referred customers walk away. So we measure refer completion and the sales lost per minute of outage, and give those numbers to credit risk when they set the caps.
[pause: 0.8]

[slide: v-081]
[pause: 0.7]
V: If asked, I'd say: every timeout is a credit decision with an owner. Credit risk signs the table. Engineering makes each row a setting with a counter, a cap and a dashboard.
[pause: 1.0]
N: The decision is settled. Next, the one step that must be atomic.
[pause: 1.6]

[pause: 1.4]

## 7.3 Challenge 3: The phone drops

[slide: v-082]
[pause: 1.2]
N: Challenge three. The customer taps accept, loses signal, and taps again on another device: how many loans?
[pause: 1.8]

[slide: v-083]
[pause: 0.6]
I: The customer taps accept, the phone loses signal, and they tap again on the merchant's tablet. How many loans?
[pause: 2.0]

[slide: v-084]
[pause: 1.3]
C: The naive answer: check whether a loan exists, and create one if it doesn't. Or the saga answer: an orchestrated saga with a compensation for each step. The red boxes are the application service and its database, where two workers each see no loan.
[pause: 1.1]

[slide: v-085]
[pause: 1.0]
C: The trace. The phone posts accept with key k-one. The response is lost in the shop's dead zone. A hundred and fifty milliseconds later the tablet posts accept with key k-two: another device, another key. Worker one reads the application: offered, version seven, no loan. Worker two reads the same. Both insert. Two loans, two transfers to the merchant tonight, and a customer billed twice.
C: Idempotency keys don't save this: two devices, two keys. And check-then-insert doesn't either: both checks ran before either insert.
[pause: 1.0]

[slide: v-086]
[pause: 1.3]
C: The fix is one local transaction, in the database outlined green. A conditional update moves the application to booked only if it is still offered and at version seven. Insert the loan under a unique constraint on the application. Insert the outbox row. Commit. If the update changed zero rows, someone else booked, so return the existing loan. S-one is enforced by the one place that sees both writers.
[pause: 1.1]

[slide: v-087]
[pause: 1.0]
C: In code. The update has two conditions: still offered, and still version seven. The second worker's update matches zero rows, because the first already changed both. The unique constraint on the loan's application is a second wall, in case some code path forgets the update. And the outbox row commits with the loan, so the loan existing and the world hearing about it are one fact. The tablet's request reads the application, finds it booked, and shows the same loan.
[pause: 1.0]

[slide: v-088]
[pause: 1.0]
C: So where does the word saga fit? Walk the steps. The identity check and the credit pull can't be undone: they happened and were paid. Record them. An offer expires by itself. Booking must be atomic, one local transaction. Only funding the merchant, after booking, can really be undone, by a reversal. A saga is a fine tool when several steps can be undone. Here only one can, and it comes after.
[pause: 1.0]

[slide: v-089]
[pause: 0.6]
I: The commit succeeded, but the relay crashed before publishing. Or it published twice.
[pause: 2.0]

[slide: v-090]
[pause: 0.6]
C: The relay is at least once by design. It reads unpublished rows, publishes, and only then marks them published, so a crash in between publishes again. Nothing is lost. Funding and servicing de-duplicate by event I-D, and funding uses the loan I-D as its idempotency key at the bank, so even a duplicate that slips through can't pay twice.
C: The honest limit, said precisely: at-least-once delivery with idempotent consumers. Not exactly once.
[pause: 0.8]

[slide: v-091]
[pause: 0.7]
V: If asked, I'd say: only one step is atomic, accept to book. A conditional update at a version, a unique loan, and the outbox row in the same commit. A second tap finds the loan.
[pause: 1.0]
N: The loan is booked once. Next, the money that moves after it.
[pause: 1.6]

[pause: 1.4]

## 7.4 Challenge 4: Funding fails after booking

[slide: v-092]
[pause: 1.2]
N: Challenge four. The loan is booked, and paying the merchant fails or goes silent: what do we undo, and what do we never resend?
[pause: 1.8]

[slide: v-093]
[pause: 0.6]
I: The loan is booked. The transfer to the merchant is rejected, or the bank times out. What do you undo?
[pause: 2.0]

[slide: v-094]
[pause: 1.3]
C: The naive answer: roll back the saga. Cancel the loan, reverse the credit check, delete the application. We've just seen that two of those can't be undone. The red box is funding, and by now the customer has left the shop.
[pause: 1.1]

[slide: v-095]
[pause: 1.0]
C: The trace. The loan is booked at two thirty-one. At six, the daily batch sends eleven hundred and sixty-four dollars to the merchant: the twelve hundred less a three percent fee. At two past six the bank says: account closed. At three past, another merchant's transfer times out with no answer at all.
C: Re-sending both to be safe would pay the second merchant twice, if the first attempt actually went through. A timeout tells you nothing about whether money moved.
[pause: 1.0]

[slide: v-096]
[pause: 1.3]
C: The fix: funding is its own state machine, after booking, outlined green. Pending, sent, settled. Or returned: merchant operations fixes the account, and a new attempt goes out with a new attempt number. A timeout becomes a state of its own, unknown, and the only action allowed on unknown is to ask the bank, by our idempotency key. Never resend.
C: The loan itself is cancelled only if the goods weren't delivered, and that's a business decision with the merchant, not a rollback. L-two, with one effect: the loan I-D is the key end to end.
[pause: 1.1]

[slide: v-097]
[pause: 1.3]
C: As a sequence. Funding sends the transfer with the loan I-D as its key. Timeout: state unknown. It asks the bank: status, for this key? Not found, yet. So it waits for the reconciliation window. The next day's file from the bank shows the transfer settled at three past six. Unknown becomes settled, and nothing was resent.
[pause: 1.1]

[slide: v-098]
[pause: 0.6]
I: The bank's status A-P-I says not found for the timed-out transfer, and tomorrow's file shows it paid.
[pause: 2.0]

[slide: v-099]
[pause: 0.6]
C: Not found, minutes after a timeout, does not mean not sent: many bank interfaces index instructions late. So no resend before the reconciliation window closes. Every day we compare three things: our funding records, the bank's settlement file, and the loans booked. Every difference is a break, with an owner and an age, and a break older than two days pages someone.
C: The honest limit: some outcomes are only known the next day. The merchant's portal says in progress, not a guess.
[pause: 0.8]

[slide: v-100]
[pause: 0.7]
V: If asked, I'd say: the credit pull and the booking happened. The one real undo is funding, so it's its own state machine, with unknown as a state. Query, never resend.
[pause: 1.0]
N: Money is settled. Next, a question about the past: why did we decide what we decided?
[pause: 1.6]

[pause: 1.4]

## 7.5 Challenge 5: Explain a decision fourteen months later

[slide: v-101]
[pause: 1.2]
N: Challenge five. A regulator asks why a customer was declined more than a year ago: can we show what we knew, and what we decided, then?
[pause: 1.8]

[slide: v-102]
[pause: 0.6]
I: A regulator asks why a customer was declined fourteen months ago. Reproduce it.
[pause: 2.0]

[slide: v-103]
[pause: 1.3]
C: The naive answer: re-run the model on the customer's data. The red box is the policy engine, and it only knows today: today's model, today's rules, and today's credit file.
[pause: 1.1]

[slide: v-104]
[pause: 1.0]
C: The trace. In January twenty twenty-six, application two-oh-four is declined by model version nine under policy thirty-one, and the customer is sent a notice: high utilisation, short history. During the year, five model versions ship. In March twenty twenty-seven the regulator asks why. Someone re-runs today's model on today's credit file, and it approves.
C: Now we hold a notice that says one thing and a replay that says another, and neither shows the regulator what actually happened.
[pause: 1.0]

[slide: v-105]
[pause: 1.3]
C: The fix: an immutable decision record, outlined green, written once by the orchestrator for every decision. Old model artefacts stay loadable in a registry. And a replay job runs every night on a sample of records and alarms on any difference. S-two: the same inputs and the same versions give the same answer, and we prove it every night rather than on the day we're asked.
[pause: 1.1]

[slide: v-106]
[pause: 1.3]
C: What a record holds. Inputs, frozen: the bureau report stored encrypted and referenced, the identity and fraud results, our own history as of that moment, the exact feature vector, and which calls were missing. Versions: model, policy including the missing-data table, pricing, disclosure, and the orchestrator build.
C: Outputs: the outcome and offers, the ranked reasons, the degraded path taken, the timings, and who signed the policy. About fifty kilobytes, written once.
[pause: 1.1]

[slide: v-107]
[pause: 1.3]
C: The replay as a sequence. The request: explain two-oh-four from January. Load the record: the features, the report reference, model nine, policy thirty-one. Load those versions from the registry. Re-score the frozen features. Decline: high utilisation, short history. It matches the notice, because it is what we knew and how we decided then.
[pause: 1.1]

[slide: v-108]
[pause: 0.6]
I: The customer asks us to delete their data. The record holds their bureau report.
[pause: 2.0]

[slide: v-109]
[pause: 0.6]
C: Who decides comes first. Retention duties for credit records generally take precedence for their period, and that call belongs to compliance, not engineering. Within the period, the record holds tokens rather than identity, and the report is encrypted under a key per record, with use restricted to the purposes the rules allow.
C: At the end of retention we destroy the record's key. That makes every copy unreadable at once, backups included, without hunting for them. That's called crypto-shredding. The honest limit: a deletion request inside the period is answered by restricting use, and the customer is told so.
[pause: 0.8]

[slide: v-110]
[pause: 0.7]
V: If asked, I'd say: I never re-run today's model to explain yesterday. Every decision freezes its inputs, versions and reasons, and a nightly replay proves they still reproduce.
[pause: 1.0]
N: Records make the past safe. The next question changes the future: a new model.
[pause: 1.6]

[pause: 1.4]

## 7.6 Challenge 6: A new model approves six percent more

[slide: v-111]
[pause: 1.2]
N: Challenge six. Data science has a model that approves more people: how do we learn whether they repay without betting a hundred million dollars?
[pause: 1.8]

[slide: v-112]
[pause: 0.6]
I: Data science has a new model. It approves six percent more people at the same predicted loss. Roll it out.
[pause: 2.0]

[slide: v-113]
[pause: 1.3]
C: The naive answers: shadow mode for a week, it looks good, switch it on. Or a fifty-fifty test. The red box is the policy engine, and a switch there changes about a hundred million dollars of exposure a month.
[pause: 1.1]

[slide: v-114]
[pause: 1.0]
C: The trace. Six percent of two million is a hundred and twenty thousand more approvals a month. At seventy percent take-up, about eighty-four thousand more loans, about a hundred million dollars a month of new exposure. The first payments fall due in two to four weeks, and losses only become visible at ninety to a hundred and twenty days.
C: A week of shadow shows the approval rate. It shows nothing about whether the newly approved people repay. And a fifty-fifty test bets fifty million a month to find out.
[pause: 1.0]

[slide: v-115]
[pause: 1.3]
C: The fix: champion and challenger, outlined green. The challenger sits beside the champion, and decides only a capped slice. Every record says which model decided, so S-two holds, and the cost of learning is bounded by the cap.
[pause: 1.1]

[slide: v-116]
[pause: 1.3]
C: The steps. A backtest on labelled history. Then shadow: both models score every application, the champion acts, and we compare approval rates and reasons by segment and by protected group. Then a challenger slice: five percent of traffic, under its own cap. Five percent of the extra approvals is about six thousand a month, four thousand two hundred loans, about five million dollars, signed by credit risk and the partner bank.
C: Then early signals at thirty to forty-five days: a first payment missed, compared between similar people approved by each model. And widening only through a policy version change, with a kill switch per version.
[pause: 1.1]

[slide: v-117]
[pause: 0.6]
I: Shadow looked great. Why isn't that enough?
[pause: 2.0]

[slide: v-118]
[pause: 0.6]
C: Because shadow cannot see loss. The people only the challenger would approve were declined by the champion. They never got a loan, so there's no repayment to observe. Only a slice where the challenger actually decides gives them loans, and gives us labels. Fairness checks run twice: on shadow, for who would be approved, and on the slice, for who repays.
C: The honest limit: a slice is real money at risk. The cap is the price of learning, and credit risk owns that price.
[pause: 0.8]

[slide: v-119]
[pause: 0.7]
V: If asked, I'd say: shadow tells you who a new model would approve, not whether they repay. So: backtest, shadow, a capped slice, early signals at thirty days, and a kill switch.
[pause: 1.0]
N: Training the next model needs data. Which data is the next question.
[pause: 1.6]

[pause: 1.4]

## 7.7 Challenge 7: Where identity data lives

[slide: v-120]
[pause: 1.2]
N: Challenge seven. Analytics wants the application data to train a model: what do they get, and where does identity actually live?
[pause: 1.8]

[slide: v-121]
[pause: 0.6]
I: The analytics team wants application data to train the next model. What do they get?
[pause: 2.0]

[slide: v-122]
[pause: 1.3]
C: The naive answers: give them a copy of the database, it's encrypted at rest. Or drop the name column. The red boxes are the application service, its database, and the export to analytics, and identity goes wherever they go.
[pause: 1.1]

[slide: v-123]
[pause: 1.0]
C: The trace, in version two. The application table holds the social security number, the date of birth and the address. The bureau adapter's debug log prints the full request. Every support agent sees the full number. The training extract drops names but keeps date of birth and postcode, which together re-identify most people. One leaked extract is two million identities a month.
C: And encryption at rest protects a stolen disk. It does nothing for a query, a log line or an export.
[pause: 1.0]

[slide: v-124]
[pause: 1.3]
C: The fix: an identity vault, outlined green. Identity is tokenised at apply. Only two things sit inside the boundary: the vault, and the vendor adapters, which must send real values to the bureau. Every detokenise is logged with its caller and purpose, and adapter logs are scrubbed at the source. So analytics gets tokens and derived features, like utilisation and history length, never identity. S-three, by construction.
[pause: 1.1]

[slide: v-125]
[pause: 1.3]
C: The boundary, drawn small on purpose. Inside: the vault with keys per field, and the adapters. Outside, everything else: the application service and database, decision records, support tools with masked values, and analytics with features. They all carry tokens.
C: And know the rulebook, because interviewers test it. Card numbers fall under the card industry's security standard. A social security number doesn't: it falls under privacy and lending law.
[pause: 1.1]

[slide: v-126]
[pause: 0.6]
I: The vault is down.
[pause: 2.0]

[slide: v-127]
[pause: 0.6]
C: The vault is a tier-zero dependency, so it's kept small, with no business logic, replicated across zones, with its own objective of ninety-nine point nine five percent and its own on-call. When it's down, nothing new can start: applications refer, and the merchant sees pending. Loans already booked carry on. And nothing raw is ever cached outside it to help.
C: The honest limit: the vault is reliable because it is small. Resist every feature request that would grow it.
[pause: 0.8]

[slide: v-128]
[pause: 0.7]
V: If asked, I'd say: analytics gets tokens and features, never identity. Only the vault and the adapters see real values, and every access is logged.
[pause: 1.0]
N: Last challenge: with all of this in place, how would we know it is broken?
[pause: 1.6]

[pause: 1.4]

## 7.8 Challenge 8: How would you know it is broken?

[slide: v-129]
[pause: 1.2]
N: Challenge eight. The dashboards are green: how would we know decisions are going wrong, before merchants tell us?
[pause: 1.8]

[slide: v-130]
[pause: 0.6]
I: Your dashboards are green. How would you know decisions are going wrong?
[pause: 2.0]

[slide: v-131]
[pause: 1.3]
C: The naive answer: error rate, latency and CPU. The red box is the policy engine, which can return perfectly valid, perfectly wrong decisions.
[pause: 1.1]

[slide: v-132]
[pause: 1.0]
C: The trace. At six on Friday evening, a pricing-table change maps one bureau field wrongly. No errors, latency fine, C-P-U flat. The approval rate across all merchants drops from sixty-two to forty-one percent. At about two applications a second, that's seven thousand two hundred an hour, about fifteen hundred wrongly declined every hour, each with a notice.
C: It's found at nine on Saturday morning, when merchants start calling. About twenty-two thousand customers, if the evening rate held.
[pause: 1.0]

[slide: v-133]
[pause: 1.3]
C: The fix: measure the decision, not the servers, outlined green across the orchestrator, the policy engine and funding. And ship every policy and pricing change as a canary on a small slice, with the approval-rate alarm armed. This change would have been caught in minutes, on a few hundred applications.
[pause: 1.1]

[slide: v-134]
[pause: 1.0]
C: Six signals. Offers within three seconds: the promise itself. Approval rate per merchant per hour against its own baseline: a sudden drop is almost never the customers. The fallback rate per policy row against its cap, because credit risk was promised a cap. Loans booked and not funded, which is money owed. Vendor errors, latency and spend. And the mix of decline reasons: a new dominant reason is a change, not a population.
[pause: 1.0]

[slide: v-135]
[pause: 1.0]
C: Then read them in pairs. Approval down with vendor errors flat and a deploy at the same time: our change. Refer rate up with a breaker open: an outage being handled as designed. Offer latency up with breakers closed: a vendor slow, but under the threshold. Booked up and funded flat: funding stuck. And one decline reason jumping while one bureau's fields shift: the vendor changed a field.
[pause: 1.0]

[slide: v-136]
[pause: 0.6]
I: Approval drops at one merchant only.
[pause: 2.0]

[slide: v-137]
[pause: 0.6]
C: Per-merchant baselines, by hour of the week. A drop at one merchant is usually an integration bug, like amounts sent in dollars instead of cents, or a fraud ring testing stolen identities. So it goes to merchant operations or fraud, not to credit risk.
C: The honest limit: small merchants have noisy baselines. Alarm on totals over a window, not on a single hour.
[pause: 0.8]

[slide: v-138]
[pause: 0.7]
V: If asked, I'd say: I watch the decision, not the servers. Offers in three seconds, approval per merchant, fallback against its cap, and two metrics together for the cause.
[pause: 1.6]

[pause: 1.4]

## 8 Build cost

[slide: v-139]
[pause: 1.2]
C: Build cost. This is the manager layer, marked aux: skip it in a pure Staff round, use it in a manager round.
[pause: 1.8]

[slide: v-140]
[pause: 1.0]
C: Three releases. Version one, sequential calls and one table: three engineers, two months, mostly to learn the vendors. Version two, the orchestrator, state machine, outbox and policy engine: a team of six for two quarters. Version three, the vault, records, policy table, funding and the challenger: two teams for two more quarters, plus security and compliance time. Riskiest work first: the vendor adapters and the policy table, because they decide whether the counter promise holds.
[pause: 1.0]

[slide: v-141]
[pause: 1.3]
C: Six owners. Applications and origination own the state machine and booking. The decisioning platform owns the orchestrator, the policy engine and serving. Vendor integrations own the adapters, contracts and spend. Security owns the vault. Credit risk and data science own the models and every degraded path. Compliance owns disclosures, notices and retention.
C: The contracts between them are three: the decision interface, the decision record, and the loan booked event.
[pause: 1.1]

[slide: v-142]
[pause: 0.6]
C: Buy, build, or defer. Buy the data: bureaus, identity and bank data, and a tokenisation vault is a reasonable buy. Build what is the decision: the orchestrator, the policy engine and the records, because a regulator asks us, not a vendor, why someone was declined. With half the team, keep the deadline, the policy table, the atomic booking and the records, buy the vault, and defer the challenger and bank data.
[pause: 0.8]

[slide: v-143]
[pause: 0.6]
C: The bill, illustrative: bureau pulls about two million a month, identity about a hundred thousand, compute a small fraction. The levers are report reuse, no races, and pulling only when the policy needs it.
C: The top risks: a degraded path without an owner or a cap. A model change without a replayable record. Identity leaking into logs. And funding retries without an unknown state.
[pause: 0.8]

[pause: 1.4]

## 9 Recap

[slide: v-144]
[pause: 1.2]
C: The recap: one picture, a sentence per path, the common mistakes, and the thesis.
[pause: 1.8]

[slide: v-145]
[pause: 1.3]
C: The whole design. Across the middle, the counter path: phone, edge, application service, orchestrator, vendors. Above, the vault. Below, what happens after booking, and what we keep: the database with its outbox, the event log, funding, the policy engine and the decision records.
[pause: 1.1]

[slide: v-146]
[pause: 1.0]
C: Apply: tokenise, create the row, answer at once. Decide: all vendors at once, one deadline, a signed policy for whatever is missing, and a record. Book: one transaction, a conditional update, a unique loan and the outbox row. Fund: its own state machine, with unknown as a state, reconciled every day.
[pause: 1.0]

[slide: v-147]
[pause: 1.0]
C: How it degrades, in priority order. A slow bureau changes nothing: the deadline decides. A bureau down uses the table: second bureau, small known customers, refer. If the policy engine is down, applications are still recorded, and they wait in the refer queue. If the vault is down, nothing new starts, but booked loans carry on.
C: And if the event log or funding is down, the counter doesn't notice at all: booking continues, the outbox holds the events, and merchants are paid in the next batch. The customer at the counter is protected first, the merchant's money second, and everything else can wait.
[pause: 1.0]

[slide: v-148]
[pause: 0.6]
N: The mistakes that cost points. In the design: treating it as a throughput problem, sequential calls, hedging paid pulls, a saga that compensates a credit pull, and check-then-insert on the loan.
N: In judgement: approve with partial data as a default, re-running today's model to explain yesterday, encrypt the database as the identity answer, the card standard quoted for identity data, and no owner for any degraded path.
[pause: 0.8]

[slide: v-149]
[pause: 0.7]
V: The core is small and boring on purpose. The design lives at the slow edges and in what we keep: one deadline with a signed policy, a record that replays, and identity in a vault.
[pause: 1.6]
