# SD-82 Instant credit at the point of sale: reference solution (Staff L6/L7)

<!-- Video script for slide-video-kit/scripts/build_video.py. [slide: v-NNN] = frames/v-NNN.png; [reveal: v-NNN] = the next
     reveal step of the same slide. Generated from src/*.py: edit the sources, not this file. -->
<!-- voices: N=af_heart@0.92 I=bf_emma@0.95 C=am_michael@0.9 V=am_michael@0.84 -->
<!-- names: C=Candidate V=Candidate N=Coach I=Interviewer -->
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
N: Five axes.
[reveal: v-005]
[pause: 0.45]
N: The weak answer shards a database that sees eight writes a second.
[reveal: v-006]
[pause: 0.45]
N: The strong answer knows a credit pull cannot be undone,
[reveal: v-007]
[pause: 0.45]
N: and that a timeout is a credit decision someone has to own.
[reveal: v-008]
[pause: 0.45]
C: One rule I'll keep for the whole round:
[reveal: v-009]
[pause: 0.45]
C: every degraded path is a credit decision with an owner and a cap, never an engineering default.
[pause: 1.0]

[slide: v-010]
[pause: 0.7]
V: Instant credit at the counter is a regulated decision under a deadline set by slow, paid vendors, followed by one atomic step. The load is tiny. The grade is on the slow edges.
[pause: 1.6]

[slide: v-011]
[pause: 0.6]
C: The order.
C: Requirements, numbers and a short theory chapter.
[reveal: v-012]
[pause: 0.45]
C: Then the A-P-I and the data, and a design in three versions, each answering the objection to the one before.
[reveal: v-013]
[pause: 0.45]
C: Then most of the time goes to eight challenges that break it, where each fix creates the next question.
C: A build cost, and a recap.
[pause: 0.8]

[pause: 1.4]

## 1 Requirements and scope

[slide: v-014]
[pause: 1.2]
C: Six questions before I draw anything. Each answer moves the design, and two of them only make sense if you know how lending works.
[pause: 1.8]

[slide: v-015]
[pause: 0.6]
C: How many applications?
I: Two million a month.
I: The Saturday peak is about ten times the average.
C: That is under one a second on average and about eight at the peak.
C: I'll do the arithmetic in a minute, but I can already say the load is not the problem.
[pause: 0.6]

[slide: v-016]
[pause: 0.6]
C: How long can the customer wait at the counter?
I: Offers on screen in under three seconds for ninety-five percent of applications.
I: Ten seconds is a lost sale.
C: Three seconds from submit to offers, at the ninety-fifth percentile.
C: That number will set one deadline for every vendor call.
[pause: 0.6]

[slide: v-017]
[pause: 0.6]
C: Who is the lender of record?
C: Us, or a partner bank?
I: We decide, on the partner bank's credit policy, and we service the loan.
I: The bank is the lender of record.
C: That matters.
C: Every credit policy version needs the bank's approval, our decision records are the bank's records too, and the money to pay the merchant flows through the bank.
[pause: 0.6]

[slide: v-018]
[pause: 0.6]
C: Which vendors do we call, and how fast are they?
I: Two credit bureaus.
I: Median six tenths of a second, the ninety-ninth percentile several seconds, about one percent errors.
I: An identity and fraud vendor, four hundred milliseconds at the ninety-ninth.
I: And optional bank-account data, seconds to minutes.
C: So the bureau's tail sets the deadline, and the bank data is never something we wait for at the counter.
[pause: 0.6]

[slide: v-019]
[pause: 0.6]
C: What do those calls cost?
I: About a dollar a bureau pull.
I: Identity checks, about five cents.
C: Then we never race two bureaus.
C: Every pull is paid, and it may show on the customer's credit file as an inquiry.
[pause: 0.6]

[slide: v-020]
[pause: 0.6]
C: Which rules shape the system?
I: Cost disclosures before the customer signs.
I: The principal reasons for every decline.
I: Records kept about seven years.
I: And fairness testing of models.
C: Three architecture decisions in one answer.
C: Decisions must carry reasons about the applicant, so our vendor being slow can never be a reason.
C: The disclosure version is part of the loan.
C: And a decision must replay years after the model that made it is gone.
[pause: 0.6]

[slide: v-021]
[pause: 0.6]
C: Four functional requirements.
C: One, apply: the customer scans the merchant's code, identity goes into a vault, and an application exists.
[reveal: v-022]
[pause: 0.45]
C: A retry returns the same application.
C: Two, decide: identity, fraud and credit data under one deadline, and the answer is offers, a refer, or a decline with reasons.
[reveal: v-023]
[pause: 0.45]
C: Three, accept and book: the customer accepts one disclosed offer, and exactly one loan is booked.
[reveal: v-024]
[pause: 0.45]
C: Four, fund and hand off: the merchant is paid net of fees, the loan goes to servicing, and decline notices go out.
C: Each of these gets a numbered flow later.
[pause: 0.8]

[slide: v-025]
[pause: 0.6]
C: The numbers, all initial targets.
C: Offers on screen in three seconds at the ninety-fifth percentile.
[reveal: v-026]
[pause: 0.45]
C: Zero loans booked twice, or booked without acceptance of the exact disclosure shown.
[reveal: v-027]
[pause: 0.45]
C: Every decision replayable for seven years.
[reveal: v-028]
[pause: 0.45]
C: And raw identity data nowhere except a vault.
[reveal: v-029]
[pause: 0.45]
C: Plus three more: three nines in merchant hours, the merchant funded within one business day, and every degraded path under a cap that someone signed.
[pause: 0.8]

[slide: v-030]
[pause: 0.6]
C: In scope: apply, identity, decide, offers, refer, accept, book, the funding instruction, the handoff to servicing, and decline notices.
C: Out, on purpose, and I'll say it aloud.
C: Repayments and the ledger: that's a servicing system with its own hard problems.
[reveal: v-031]
[pause: 0.45]
C: Card authorisation.
C: Merchant onboarding and merchant fraud, which is a merchant-risk system.
C: Model training: I'll treat a model as a versioned artefact we load.
C: Collections, and the payment rail itself.
[pause: 0.8]

[slide: v-032]
[pause: 0.7]
V: The core is three things. An orchestrator that decides under one deadline. A state machine whose only atomic step is accept to book. And a record and a vault.
[pause: 0.8]
N: The candidate named the core before drawing. That is the scoping signal: what the system is in a sentence, and what it is not.
[pause: 1.6]

[pause: 1.4]

## 2 Estimates

[slide: v-033]
[pause: 1.2]
C: Numbers next. Three of them really matter, and each one changes a decision. I'll label them: given, derived or illustrative.
[pause: 1.8]

[slide: v-034]
[pause: 1.0]
C: The load.
C: Two million a month, divided by about two point six million seconds, is about eight tenths of an application a second.
C: Ten times that at the Saturday peak: eight a second.
[reveal: v-035]
[pause: 0.45]
C: Each application moves through about six states, so about fifty committed writes a second.
C: One relational database takes that without noticing.
[reveal: v-036]
[pause: 0.45]
C: Each application fans out to about four vendor calls: thirty-two calls a second, and with a two-second deadline about sixty-four in flight.
C: So the pressure is on the vendors, their latency and their contract limits, not on our servers.
[pause: 1.0]

[slide: v-037]
[pause: 1.0]
C: The money.
C: If every application pulls a bureau report at about a dollar, that's two million dollars a month, far more than the computers.
[reveal: v-038]
[pause: 0.45]
C: If a fifth of applicants re-apply within a month, and the contract and the rules let us reuse a recent report, that saves about four hundred thousand a month.
C: So the report store and its retention rule are part of the design.
[reveal: v-039]
[pause: 0.45]
C: Identity checks add about a hundred thousand.
[reveal: v-040]
[pause: 0.45]
C: And with sixty percent approved and seventy percent of those accepted, that is about eight hundred and forty thousand loans a month, about a billion dollars at twelve hundred each.
C: Illustrative, but it tells me the merchant is paid in a daily batch, not per request.
[pause: 1.0]

[slide: v-041]
[pause: 1.0]
C: The third number is the one that shapes the design.
C: If about two percent of bureau calls miss the deadline and about one percent fail, about three percent of applications reach the deadline with no bureau answer.
C: Sixty thousand a month, fourteen a minute at the peak.
[reveal: v-042]
[pause: 0.45]
C: That is a weekly volume, so what we do then is a policy with counters, not an exception handler.
C: And a twenty-minute bureau outage at the peak is nine thousand six hundred applications.
C: Approve them all and we lend eleven and a half million dollars nobody scored.
[reveal: v-043]
[pause: 0.45]
C: Decline them all and we lose about four thousand loans.
C: Neither extreme.
C: That's challenge two.
[pause: 1.0]

[slide: v-044]
[pause: 1.0]
C: Records.
C: Each decision with its inputs, mostly the bureau report, is about fifty kilobytes.
[reveal: v-045]
[pause: 0.45]
C: A hundred gigabytes a month, about eight terabytes over seven years.
[reveal: v-046]
[pause: 0.45]
C: So the full record goes to encrypted object storage with a retention lock, and the database keeps a reference and the hot fields.
[pause: 1.0]

[slide: v-047]
[pause: 1.3]
C: The latency budget, from submit to offers on screen. The phone to our A-P-I and the first state write, about two hundred milliseconds. The vendors, two seconds: one deadline for all of them. Model, policy and pricing, about two hundred and fifty. Writing the record and pushing the offers to the phone, about two hundred and fifty. That is two point seven seconds, with three hundred to spare.
C: So the deadline is derived from the promise, not picked from experience. And nothing optional, like bank data, can ever sit on this path.
[pause: 1.1]

[slide: v-048]
[pause: 0.6]
C: So, before I draw a single box, the numbers have already decided four things.
C: One relational database, because the load is tiny.
[reveal: v-049]
[pause: 0.45]
C: No races between bureaus, because every pull is paid and the bill is already the largest line.
[reveal: v-050]
[pause: 0.45]
C: A signed policy for missing data, because it happens fourteen times a minute at the peak.
[reveal: v-051]
[pause: 0.45]
C: And object storage for decision records, because they're large, written once, and rarely read.
C: Notice what the numbers did not ask for: a cache, a queue in front of the database, or a sharding scheme.
C: Saying that out loud is part of the answer.
[pause: 0.8]

[pause: 1.4]

## 3 Theory

[slide: v-052]
[pause: 1.2]
C: A short theory chapter before the design, so the design can lean on it. What this system is and is not, its properties, the central tension, six mechanisms, an options matrix, and the failure catalogue.
[pause: 1.8]

[slide: v-053]
[pause: 0.7]
V: A credit decisioning system gathers data from paid vendors under one deadline, returns an explainable decision with priced offers, and books exactly one loan when the customer accepts an offer they were shown.
[pause: 1.0]
C: Every clause is load-bearing. Paid vendors: every call costs money and may be recorded, so we never race them. One deadline: the customer is at a counter. Explainable: a decline carries reasons about the applicant, and they replay years later. Exactly one loan: one atomic step. And an offer they were shown: the disclosure version is part of the contract.
[pause: 1.6]

[slide: v-054]
[pause: 0.6]
C: Four neighbours it gets confused with.
C: It is not a scoring model: the model is one input, the policy rules decide, and pricing prices, each with its own version.
[reveal: v-055]
[pause: 0.45]
C: It is not a payment: no money moves when the customer accepts.
C: The merchant is funded later.
[reveal: v-056]
[pause: 0.45]
C: It is not a saga: only one step has to be atomic, and a credit pull cannot be compensated, because it happened.
[reveal: v-057]
[pause: 0.45]
C: And it is not an underwriting queue: refer means we finish in minutes, by text.
[pause: 0.8]

[slide: v-058]
[pause: 0.6]
C: The properties, stated separately.
C: Safety, what must never happen.
C: S-one: a loan booked twice, or without acceptance of the exact offer shown.
C: S-two: a decline or a price without reasons about the applicant that we can reproduce.
C: S-three: raw identity outside the vault.
C: S-four: more than one pull per bureau per application.
[reveal: v-059]
[pause: 0.45]
C: Liveness, what must eventually happen.
C: L-one: every application gets an answer within the deadline.
C: L-two: every booked loan is funded and handed to servicing, with one effect.
C: L-three: every referred application is finished within ten minutes.
C: Every fix from here names the property it serves.
[pause: 0.8]

[slide: v-060]
[pause: 1.3]
C: The central tension. Identity answers in four tenths of a second, fraud in about the same, the bureau usually in six tenths. One time in ten the bureau takes four seconds. The deadline line is at two seconds, and the sale is lost at ten.
C: Waiting longer adds evidence and loses sales. Deciding early keeps the sale and adds risk. Asking a second bureau adds evidence, another dollar and another inquiry. Every choice from here is a point in that triangle, and the important ones belong to credit risk, not to a timeout setting.
[pause: 1.1]

[slide: v-061]
[pause: 0.6]
C: Mechanism one, scatter-gather under one deadline, with a circuit breaker per vendor.
C: It protects L-one and S-four.
[reveal: v-062]
[pause: 0.45]
C: All vendor calls go out at once, and we decide at the deadline with what has arrived.
C: A breaker stops calls to a vendor that is failing for everyone.
[reveal: v-063]
[pause: 0.45]
C: It rules out one slow vendor setting the customer's wait.
[reveal: v-064]
[pause: 0.45]
C: It costs decisions with data missing, which mechanism two has to decide.
[pause: 0.8]

[slide: v-065]
[pause: 0.6]
C: Mechanism two, a missing-data policy table.
C: It protects S-two and L-one.
[reveal: v-066]
[pause: 0.45]
C: A versioned table inside the credit policy: ask the second bureau, decide small and known customers under a cap, refer, or decline with a real reason.
C: Each row has a counter and a dashboard.
[reveal: v-067]
[pause: 0.45]
C: It rules out approve with partial data as a code default, and declines whose real reason is our own outage.
[reveal: v-068]
[pause: 0.45]
C: It costs a refer path, an exposure counter, and an owner in credit risk who signs it.
[pause: 0.8]

[slide: v-069]
[pause: 0.6]
C: Mechanism three, the application as a state machine in the database.
C: It protects S-one and L-one.
[reveal: v-070]
[pause: 0.45]
C: Every transition is one committed row, with a version number used as an optimistic lock, and idempotency keys on create and accept.
[reveal: v-071]
[pause: 0.45]
C: It rules out two workers moving one application, and lost progress when a phone drops.
[reveal: v-072]
[pause: 0.45]
C: It costs a write per transition, which at fifty a second is nothing.
[pause: 0.8]

[slide: v-073]
[pause: 0.6]
C: Mechanism four, one local transaction for booking.
C: It protects S-one and L-two.
[reveal: v-074]
[pause: 0.45]
C: Move the status at a version, insert the loan under a unique constraint on the application, insert an outbox row, and commit.
C: A relay then publishes the row.
[reveal: v-075]
[pause: 0.45]
C: It rules out two loans for one application, and a loan that funding never hears about.
[reveal: v-076]
[pause: 0.45]
C: It costs a relay, and consumers that de-duplicate.
[pause: 0.8]

[slide: v-077]
[pause: 0.6]
C: Mechanism five, an immutable decision record.
C: It protects S-two.
[reveal: v-078]
[pause: 0.45]
C: Written once: the frozen inputs, including the report by reference, the feature vector and which calls were missing; every version; and the outputs with ranked reasons.
C: Old models stay loadable.
[reveal: v-079]
[pause: 0.45]
C: It rules out declines nobody can explain, and a re-run that contradicts the notice we sent.
[reveal: v-080]
[pause: 0.45]
C: It costs eight terabytes over seven years and a model registry kept just as long.
[pause: 0.8]

[slide: v-081]
[pause: 0.6]
C: Mechanism six, an identity vault.
C: It protects S-three.
[reveal: v-082]
[pause: 0.45]
C: Identity is tokenised at apply, and only the vault and the vendor adapters, which must send real values, ever see them.
C: Every detokenise is logged with its purpose.
[reveal: v-083]
[pause: 0.45]
C: It rules out identity spreading into rows, logs, exports and training sets.
[reveal: v-084]
[pause: 0.45]
C: It costs a small, critical service and a hop at each vendor call.
[pause: 0.8]

[slide: v-085]
[pause: 1.0]
C: The options matrix.
C: A, sequential calls in the request: the bureau's tail alone breaks three seconds.
[reveal: v-086]
[pause: 0.45]
C: B, parallel with hedging, racing two bureaus: fast, but every race is two paid pulls and two inquiries.
[reveal: v-087]
[pause: 0.45]
C: C, a saga with a compensation for every step: a credit pull cannot be undone, so the compensations do nothing but add code.
[reveal: v-088]
[pause: 0.45]
C: F, a manual queue: ten seconds is already a lost sale.
C: D, a durable workflow engine, is the honest equal: it works, and I'd choose it when steps last hours or days, like document upload or manual review.
[reveal: v-089]
[pause: 0.45]
C: I pick E: a database state machine, one deadline, the policy table, and an atomic booking with an outbox.
[reveal: v-090]
[pause: 0.45]
C: What it gives up: the timers, retries and relay that a workflow engine would give us for free.
[pause: 1.0]

[slide: v-091]
[pause: 1.0]
C: The failure catalogue, which becomes the challenge list.
[reveal: v-092]
[pause: 0.45]
C: The bureau slow, then down for everyone.
[reveal: v-093]
[pause: 0.45]
C: The phone drops, then funding fails after booking.
[reveal: v-094]
[pause: 0.45]
C: A decision nobody can explain.
[reveal: v-095]
[pause: 0.45]
C: A new model that approves more.
[reveal: v-096]
[pause: 0.45]
C: Identity data spreading.
[reveal: v-097]
[pause: 0.45]
C: And a silent approval drop.
[reveal: v-098]
[pause: 0.45]
C: One more I'll name and leave: merchant fraud, a merchant ringing up fake sales.
[reveal: v-099]
[pause: 0.45]
C: That's a merchant-risk system, and it plugs in at onboarding and at funding.
[pause: 1.0]

[pause: 1.4]

## 4 API and entities

[slide: v-100]
[pause: 1.2]
C: The A-P-I next, because writing the contract forces the hard semantics into the open: retries, expiry, and what the customer actually agreed to.
[pause: 1.8]

[slide: v-101]
[pause: 1.0]
C: Apply returns at once, two-oh-two, with an application I-D, because the decision takes seconds and the phone may drop.
C: It carries an idempotency key, so a retry from the point of sale returns the same application instead of pulling the bureau again.
C: And it carries a vault token, never the identity itself.
C: The phone polls or receives a push.
C: The answer is offers with an expiry, fifteen minutes, because prices and credit files go stale.
C: Or referred, with a promise time, or declined.
C: This serves FR-one and FR-two, and writes the application entity.
[pause: 1.0]

[slide: v-102]
[pause: 1.0]
C: Accept names the offer and the version of the disclosure the customer saw, because that version is part of the contract, and it returns the loan.
C: A second accept, from any device, returns the same loan.
C: Then the event, loan booked, with the loan, the merchant, the principal and the merchant fee.
C: It is delivered at least once, so funding and servicing de-duplicate by event I-D.
C: FR-three and FR-four.
[pause: 1.0]

[slide: v-103]
[pause: 1.0]
C: Inside, the decision interface is the contract between the applications team and the decisioning platform.
C: Outcome, offers, ranked reasons, the three versions, and two fields people forget: which inputs were missing, and which degraded path was taken.
C: Without those two, the applications team can't show pending for a refer, and nobody can prove that the caps credit risk signed actually hold.
[pause: 1.0]

[slide: v-104]
[pause: 1.3]
C: The conceptual model,
[reveal: v-105]
[pause: 0.45]
C: in one breath.
[reveal: v-106]
[pause: 0.45]
C: An applicant,
[reveal: v-107]
[pause: 0.45]
C: known only by a token,
[reveal: v-108]
[pause: 0.45]
C: submits applications.
[reveal: v-109]
[pause: 0.45]
C: Each application makes paid vendor calls.
[reveal: v-110]
[pause: 0.45]
C: Each is decided once.
[reveal: v-111]
[pause: 0.45]
C: A decision holds offers.
[reveal: v-112]
[pause: 0.45]
C: An application books at most one loan.
[reveal: v-113]
[pause: 0.45]
C: And a loan is paid out by funding transfers.
[pause: 1.1]

[slide: v-114]
[pause: 1.3]
C: The physical tables.
[reveal: v-115]
[pause: 0.45]
C: The application row is the state machine, with a version for the optimistic lock and a token instead of identity.
[reveal: v-116]
[pause: 0.45]
C: The decision row is written once, never updated, with the versions and a link to the full record.
[reveal: v-117]
[pause: 0.45]
C: The loan has a unique constraint on the application: that one constraint makes a double tap harmless.
[reveal: v-118]
[pause: 0.45]
C: The outbox commits with the loan.
[reveal: v-119]
[pause: 0.45]
C: Every vendor call is a row with its cost, because the bureau bill is the largest line.
[reveal: v-120]
[pause: 0.45]
C: And the vault is a separate store that only two components can read.
[pause: 1.1]

[slide: v-121]
[pause: 1.0]
C: Five stores, and whether we can lose them.
C: The application database, no: a synchronous standby in another zone.
[reveal: v-122]
[pause: 0.45]
C: Decision records, no: a retention lock for seven years.
[reveal: v-123]
[pause: 0.45]
C: The vault, no: it is the only copy.
[reveal: v-124]
[pause: 0.45]
C: The event log can be rebuilt from the outbox.
[reveal: v-125]
[pause: 0.45]
C: And the report store can be lost: a miss costs a dollar, not correctness.
[pause: 1.0]

[pause: 1.4]

## 5 High-level design

[slide: v-126]
[pause: 1.2]
C: The design in three versions. Before each new one, I'll say the objection it answers.
[pause: 1.8]

[slide: v-127]
[pause: 1.3]
C: Version one, so we have something to break.
[reveal: v-128]
[pause: 0.45]
C: The phone and the point of sale call an A-P-I edge, which calls one application service.
[reveal: v-129]
[pause: 0.45]
C: It calls the identity vendor, then the bureau, in turn, scores, and writes the application and the loan to one database.
[reveal: v-130]
[pause: 0.45]
C: Three objections.
C: The latencies add up, so the bureau's slow tail alone breaks three seconds.
[reveal: v-131]
[pause: 0.45]
C: A dropped phone retried on another device can book twice.
C: And nothing records why we decided.
[pause: 1.1]

[slide: v-132]
[pause: 1.3]
C: Version two answers latency and correctness.
[reveal: v-133]
[pause: 0.45]
C: A decision orchestrator, outlined blue, calls all vendors at once under one deadline, with a breaker per vendor.
[reveal: v-134]
[pause: 0.45]
C: The application becomes a state machine in the database.
C: Booking is one transaction that also writes an outbox row, and a relay publishes it to an event log.
[reveal: v-135]
[pause: 0.45]
C: And scoring becomes a versioned policy engine: model, policy, pricing.
C: What it leaves: what we do when the bureau is missing at the deadline, identity data in every row and log, no record that survives a model change, and nobody paying the merchant.
[pause: 1.1]

[slide: v-136]
[pause: 1.3]
C: Version three.
[reveal: v-137]
[pause: 0.45]
C: The identity vault, top left, tokenises at apply, and only the vendor adapters inside the orchestrator detokenise.
C: Decision records go to encrypted object storage, written once.
[reveal: v-138]
[pause: 0.45]
C: The missing-data policy table lives in the policy engine, versioned with the credit policy.
C: And funding consumes loan booked from the log, then hands the loan to servicing.
[reveal: v-139]
[pause: 0.45]
C: The objection it answers: this must be regulated, explainable and owned.
C: What it leaves are the details, and those are the challenges.
[pause: 1.1]

[slide: v-140]
[pause: 1.3]
C: FR-one, apply, by the numbers.
[reveal: v-141]
[pause: 0.45]
C: One, the phone posts the application with an idempotency key.
[reveal: v-142]
[pause: 0.45]
C: Two, the A-P-I edge tokenises identity in the vault.
[reveal: v-143]
[pause: 0.45]
C: Three, the application service creates the row.
[reveal: v-144]
[pause: 0.45]
C: Four, the row commits, status started.
[reveal: v-145]
[pause: 0.45]
C: Five and six, the answer goes back: two-oh-two with the application I-D.
[reveal: v-146]
[pause: 0.45]
C: From step two on, nothing but the vault sees the identity.
[pause: 1.1]

[slide: v-147]
[pause: 1.3]
C: FR-two, decide.
[reveal: v-148]
[pause: 0.45]
C: One, the application service asks the orchestrator.
[reveal: v-149]
[pause: 0.45]
C: Two, the vendor adapters detokenise in the vault, only for the calls that need it.
[reveal: v-150]
[pause: 0.45]
C: Three, identity, fraud and bureau go out at once.
[reveal: v-151]
[pause: 0.45]
C: Four, the answers come back, or the deadline passes and the miss is recorded.
[reveal: v-152]
[pause: 0.45]
C: Five, the policy engine computes features, runs the model, the policy rules and pricing.
[reveal: v-153]
[pause: 0.45]
C: Six, the decision record is written once.
[reveal: v-154]
[pause: 0.45]
C: Seven, the decision goes back and the row becomes offered, referred or declined.
[reveal: v-155]
[pause: 0.45]
C: Eight, the offers reach the phone.
[pause: 1.1]

[slide: v-156]
[pause: 1.3]
C: FR-three, accept and book.
[reveal: v-157]
[pause: 0.45]
C: One, the phone posts accept with the offer, the disclosure version and a key.
[reveal: v-158]
[pause: 0.45]
C: Two, the edge passes it on.
[reveal: v-159]
[pause: 0.45]
C: Three,
[reveal: v-160]
[pause: 0.45]
C: one transaction: the status moves to booked at a version, the loan is inserted under its unique constraint, and the outbox row is inserted.
[reveal: v-161]
[pause: 0.45]
C: Four and five, two-oh-one with the loan I-D.
[pause: 1.1]

[slide: v-162]
[pause: 1.3]
C: FR-four, fund and hand off.
[reveal: v-163]
[pause: 0.45]
C: One, the booking transaction wrote the outbox row.
[reveal: v-164]
[pause: 0.45]
C: Two, the relay publishes loan booked to the event log.
[reveal: v-165]
[pause: 0.45]
C: Three, funding adds the loan to tonight's batch for the merchant, and servicing opens the repayment schedule.
C: None of it is in the customer's wait.
[pause: 1.1]

[slide: v-166]
[pause: 1.3]
C: The context view.
[reveal: v-167]
[pause: 0.45]
C: On the left, the customer at the counter and the merchant.
[reveal: v-168]
[pause: 0.45]
C: In the middle, us: apply, decide, book, fund.
[reveal: v-169]
[pause: 0.45]
C: On the right,
[reveal: v-170]
[pause: 0.45]
C: the credit vendors,
[reveal: v-171]
[pause: 0.45]
C: slow and paid; the partner bank, the lender of record, which pays merchants; and servicing, which takes the loan after booking.
[pause: 1.1]

[slide: v-172]
[pause: 1.3]
C: The containers.
[reveal: v-173]
[pause: 0.45]
C: The A-P-I edge: merchant authentication and idempotency keys.
[reveal: v-174]
[pause: 0.45]
C: The application service owns the state machine and booking,
[reveal: v-175]
[pause: 0.45]
C: and has no vendor code in it.
[reveal: v-176]
[pause: 0.45]
C: The orchestrator owns time: deadlines, breakers and rate limits.
[reveal: v-177]
[pause: 0.45]
C: The policy engine is a pure function of inputs and versions, so it can replay.
[reveal: v-178]
[pause: 0.45]
C: The vault is the regulated part, kept small.
[reveal: v-179]
[pause: 0.45]
C: The database holds correctness in its constraints.
[reveal: v-180]
[pause: 0.45]
C: The event log decouples the counter from funding, servicing and notices.
[reveal: v-181]
[pause: 0.45]
C: Funding is the only container that moves money.
[reveal: v-182]
[pause: 0.45]
C: And decision records sit in object storage with a retention lock.
[pause: 1.1]

[slide: v-183]
[pause: 1.3]
C: Apply and decide as a sequence.
[reveal: v-184]
[pause: 0.45]
C: The phone posts; it gets two-oh-two, started.
[reveal: v-185]
[pause: 0.45]
C: The application service asks the orchestrator to decide with a deadline two seconds out.
[reveal: v-186]
[pause: 0.45]
C: Identity,
[reveal: v-187]
[pause: 0.45]
C: fraud and bureau go out at once and come back at four tenths,
[reveal: v-188]
[pause: 0.45]
C: three and a half tenths and six tenths of a second.
[reveal: v-189]
[pause: 0.45]
C: Features,
[reveal: v-190]
[pause: 0.45]
C: model version nine, policy thirty-one, pricing twelve: approve, three offers, reasons.
[reveal: v-191]
[pause: 0.45]
C: The record is written once, and offers are pushed to the phone.
[pause: 1.1]

[slide: v-192]
[pause: 1.3]
C: Accept and book.
[reveal: v-193]
[pause: 0.45]
C: The accept arrives with the offer and the disclosure version.
[reveal: v-194]
[pause: 0.45]
C: Begin.
[reveal: v-195]
[pause: 0.45]
C: Update the application where it is still offered and at version seven.
[reveal: v-196]
[pause: 0.45]
C: Insert the loan, insert the outbox row, commit.
[reveal: v-197]
[pause: 0.45]
C: One row changed, committed, two-oh-one.
[reveal: v-198]
[pause: 0.45]
C: Later, the relay polls unpublished outbox rows, publishes loan booked, and only then marks them published.
C: At least once, by design.
[pause: 1.1]

[slide: v-199]
[pause: 1.0]
C: One usual application in time.
C: Submit at zero.
[reveal: v-200]
[pause: 0.45]
C: By two hundred milliseconds the identity is a token and the row is committed.
[reveal: v-201]
[pause: 0.45]
C: The three vendor calls go out together, and the deadline is set for two point two seconds.
[reveal: v-202]
[pause: 0.45]
C: Fraud answers at five fifty, identity at six hundred, the bureau at eight twenty.
[reveal: v-203]
[pause: 0.45]
C: At that moment every required answer is in, so the orchestrator moves on without waiting for the deadline.
C: The deadline is a ceiling, not a wait.
[reveal: v-204]
[pause: 0.45]
C: Model, policy and pricing finish around eleven hundred, the record is written, and the offers are on the phone at about one point three seconds.
[reveal: v-205]
[pause: 0.45]
C: The slow case is the one the challenges are about.
[pause: 1.0]

[slide: v-206]
[pause: 0.7]
V: The core is small and boring on purpose: one database, one atomic step. The design lives at the slow edges.
[pause: 0.8]
N: Every box had a reason before it was drawn.
[pause: 1.6]

[pause: 1.4]

## 5.1 Components and technologies

[slide: v-207]
[pause: 1.2]
C: Now one level down. Every container, with the technology I would run it on, and for each choice, the alternatives I rejected and why.
[pause: 1.8]

[slide: v-208]
[pause: 1.3]
C: The container view again, with one change: the type line now names the technology. I will walk it once, then defend each choice on its own slide.
[reveal: v-209]
[pause: 0.45]
C: Identity vault is Tokenisation, HSM keys.
[reveal: v-210]
[pause: 0.45]
C: API edge is API gateway.
[reveal: v-211]
[pause: 0.45]
C: Event log is Kafka via outbox.
[reveal: v-212]
[pause: 0.45]
C: Application service is Go, state machine.
[reveal: v-213]
[pause: 0.45]
C: Application DB is PostgreSQL.
[reveal: v-214]
[pause: 0.45]
C: Funding is Go, own state machine.
[reveal: v-215]
[pause: 0.45]
C: Decision orchestrator is Go, deadlines, breakers.
[reveal: v-216]
[pause: 0.45]
C: Policy engine is Versioned rules and model.
[reveal: v-217]
[pause: 0.45]
C: Decision records is Object storage, locked.
[reveal: v-218]
[pause: 0.45]
C: The path between them..
[reveal: v-219]
[pause: 0.45]
C: The path between them..
[pause: 1.1]

[slide: v-220]
[pause: 1.3]
C: One level further down, inside the box the challenges will drill most: the decision orchestrator.
[reveal: v-221]
[pause: 0.45]
C: The application service asks for a decision.
[reveal: v-222]
[pause: 0.45]
C: The gather owns one two-second deadline for every call, a Go error group under a context deadline.
[reveal: v-223]
[pause: 0.45]
C: First, the tier-zero checks, in process and free: eligibility, the blocklist and velocity, our own loan book.
[reveal: v-224]
[pause: 0.45]
C: Then the vendor adapters, one per vendor, called at once. Each holds a circuit breaker and a token bucket at the contract rate.
[reveal: v-225]
[pause: 0.45]
C: They call the bureau, identity and fraud vendors over mutual TLS.
[reveal: v-226]
[pause: 0.45]
C: At the deadline, the policy client sends the features and the list of what is missing,
[reveal: v-227]
[pause: 0.45]
C: and the policy engine scores it.
[reveal: v-228]
[pause: 0.45]
C: The record writer writes one record per decision,
[reveal: v-229]
[pause: 0.45]
C: into the decision records store, write once.
[reveal: v-230]
[pause: 0.45]
C: And the late-answer recorder keeps whatever arrives after two seconds, because it was paid for.
[pause: 1.1]

[slide: v-231]
[pause: 1.0]
C: A unique constraint on the application ID means a second booking cannot exist. State changes are conditional updates that name the state they expect. The loan row and the outbox row are written in the same transaction. A synchronous standby in another zone keeps a committed booking through a failover.
[reveal: v-232]
[pause: 0.45]
C: Why PostgreSQL 16, one primary, a synchronous standby, point-in-time recovery: Fifty transitions a second is small. The correctness lives in constraints and conditional updates, which a relational database does in one transaction with the outbox row.
[reveal: v-233]
[pause: 0.45]
C: Rejected: A distributed SQL database. Correct and unneeded at this scale, and more to run.
[reveal: v-234]
[pause: 0.45]
C: A key-value store. No multi-row transaction for the loan and its outbox row.
[pause: 1.0]

[slide: v-235]
[pause: 1.0]
C: The orchestrator runs the free in-house checks first (about 50 ms), then starts one deadline and calls one bureau, identity and fraud in parallel; bank data is never awaited. Each vendor has a breaker that opens on an error rate or a latency percentile and half-opens with a trickle of probes, and a token bucket at the contracted rate. Whatever has arrived at the deadline is what the policy engine decides with.
[reveal: v-236]
[pause: 0.45]
C: Why A Go service: scatter-gather, per-vendor breakers and token buckets: The customer's wait is set by the slowest vendor unless something owns the time. The three-second promise needs an owner.
[reveal: v-237]
[pause: 0.45]
C: Rejected: A durable workflow engine. Right when steps last hours or days. An honest equal here, with more machinery for a three-second flow.
[reveal: v-238]
[pause: 0.45]
C: A service mesh's timeouts. They cut calls but do not decide what happens next.
[pause: 1.0]

[slide: v-239]
[pause: 1.0]
C: The engine holds versioned policy, model and pricing. The champion decides; a challenger runs beside it on a capped share of traffic and is logged, not acted on, until it is promoted. Every decision stores the inputs it saw, the versions it used and the outcome, so it can be shown again exactly.
[reveal: v-240]
[pause: 0.45]
C: Why A rules and model service, every decision stamped with the versions: A decision must be explainable fourteen months later and a new model must be introducible without a leap of faith.
[reveal: v-241]
[pause: 0.45]
C: Rejected: Rules and model baked into the service. A release per policy change and no way to replay a decision.
[reveal: v-242]
[pause: 0.45]
C: Switching the model for everyone. An approval-rate jump is a risk jump.
[pause: 1.0]

[slide: v-243]
[pause: 1.0]
C: The outbox row is written in the booking transaction. A relay publishes it to Kafka at least once, and funding and the alert consumers deduplicate by event ID. Funding listens for LoanBooked and does its own work, with its own state machine.
[reveal: v-244]
[pause: 0.45]
C: Why Outbox row, Kafka, consumers deduplicating by event ID: Booking and the event must be one fact without a distributed transaction.
[reveal: v-245]
[pause: 0.45]
C: Rejected: Publishing directly after the commit. A crash between the two loses the event.
[reveal: v-246]
[pause: 0.45]
C: Two-phase commit with the broker. Slow, rarely supported, and unnecessary.
[pause: 1.0]

[slide: v-247]
[pause: 1.0]
C: Each decision's inputs, versions and outcome are written as one versioned object under a retention lock, so it cannot be deleted early. Each record is encrypted with its own key, so destroying the key at the end of retention makes every copy unreadable. An index in the database points to it.
[reveal: v-248]
[pause: 0.45]
C: Why Object storage with a retention lock, a key per record: About eight terabytes over seven years, written once, read rarely, deleted on a schedule.
[reveal: v-249]
[pause: 0.45]
C: Rejected: The application database. Expensive, and every backup multiplies copies of identity-adjacent data.
[reveal: v-250]
[pause: 0.45]
C: A data warehouse. Fine for analytics, wrong as the record of truth.
[pause: 1.0]

[slide: v-251]
[pause: 1.0]
C: The vault replaces identity values with random tokens and stores the mapping with field-level encryption, with keys in a hardware-backed key service. Every read is logged with who and why. Vendors that need real values receive them from the vault directly; every other service handles only tokens.
[reveal: v-252]
[pause: 0.45]
C: Why A tokenisation vault, keys in a hardware-backed key service, an access log: Regulated data should exist in one small place. Everything else sees tokens.
[reveal: v-253]
[pause: 0.45]
C: Rejected: Raw identity in every service. Every copy is regulated, every log a risk.
[reveal: v-254]
[pause: 0.45]
C: Encrypting columns in each database. Keys spread across teams, and every service can decrypt.
[pause: 1.0]

[slide: v-255]
[pause: 1.0]
C: The edge authenticates the merchant, rate limits per merchant and requires an idempotency key on every create. The key is recorded with the application under a unique constraint, and a repeat returns the stored response. When a decision exceeds three seconds the response is a pending one and a text message follows when it is ready.
[reveal: v-256]
[pause: 0.45]
C: Why An API gateway, merchant keys, an idempotency key on every create: Merchants and networks retry. The same request must give the same application and the same answer.
[reveal: v-257]
[pause: 0.45]
C: Rejected: No idempotency, retry on the client. A flaky phone creates two applications and pulls two bureau reports.
[reveal: v-258]
[pause: 0.45]
C: Long polling on the connection. The customer's wait is held on one connection that can drop.
[pause: 1.0]

[slide: v-259]
[pause: 1.0]
C: The stack on one slide, as I would leave it on the whiteboard.
C: Application DB: PostgreSQL, constraints.
C: Not Distributed SQL; key-value.
C: One transaction books once.
[reveal: v-260]
[pause: 0.45]
C: Orchestrator: Go, deadline, breakers.
C: Not Workflow engine; mesh timeouts.
C: One owner of time.
[reveal: v-261]
[pause: 0.45]
C: Policy engine: Versioned; champion, challenger.
C: Not In-code rules; flip.
C: Explainable; capped change.
[reveal: v-262]
[pause: 0.45]
C: Event log: Outbox into Kafka.
C: Not Publish after; 2PC.
C: One fact, no distributed commit.
[reveal: v-263]
[pause: 0.45]
C: Decision records: Object storage, lock, key each.
C: Not Database; warehouse.
C: Immutable, deletable by key.
[reveal: v-264]
[pause: 0.45]
C: Identity vault: Tokenisation, HSM keys.
C: Not Raw identity; per-DB crypto.
C: Two readers only.
[reveal: v-265]
[pause: 0.45]
C: API edge: Gateway, idempotency key.
C: Not No key; long polling.
C: Same request, same answer.
[reveal: v-266]
[pause: 0.45]
N: Naming a product is not the signal.
N: Naming the property that rules out its rival is.
N: Interviewers go one level down on whichever box you name, so name only what you can defend.
[pause: 1.0]

[slide: v-267]
[pause: 0.6]
N: Before the challenges, swap seats. You are the interviewer now. Of everything on the last slide, which box would you push on, and what is the one question you would ask? Pause the video and pick one.
[pause: 3.0]

[slide: v-268]
[pause: 1.0]
N: Here is where interviewers usually go.
I: The customer's phone drops and the app retries the booking.
I: How many loans exist?
[pause: 1.2]
N: One.
N: The unique constraint on the application ID decides; the retry reads the existing loan.
[reveal: v-269]
[pause: 0.45]
N: The trap is a check-then-insert in the service.
I: The bureau is slow for everyone tonight.
I: What does an applicant see at three seconds?
[pause: 1.2]
N: The orchestrator's deadline fires and the policy engine decides with what it has.
N: If that is not enough for a safe decision, a text follows when the data arrives.
[reveal: v-270]
[pause: 0.45]
N: The trap is waiting.
I: A new model approves six percent more applicants.
I: Do you ship it?
[pause: 1.2]
N: Not to everyone.
N: It runs as a capped challenger, its approvals are watched against loss, and a promotion needs the risk team's sign-off.
[reveal: v-271]
[pause: 0.45]
N: The trap is treating a higher approval rate as a win.
I: Funding fails after the loan was booked.
I: What does the customer have, and what happens next?
[pause: 1.2]
N: A booked loan.
N: Funding is its own state machine, with retries and an alert at a deadline; the booking is not undone.
[reveal: v-272]
[pause: 0.45]
N: The trap is putting booking and funding in one transaction.
N: If you picked a box that is not on this list, good.
N: Write its probe down and answer it before you watch on.
[pause: 1.2]

[pause: 1.4]

## 5.2 When you don't need all this

[slide: v-273]
[pause: 1.2]
C: Before I break it, the simpler design. Not every lender needs a second bureau and a signed missing-data table, and saying where the line is counts as judgement.
[pause: 1.8]

[slide: v-274]
[pause: 1.3]
C: The alternate path changes one box.
[reveal: v-275]
[pause: 0.45]
C: The orchestrator, the deadline and the state machine stay.
C: The credit vendors box, marked alternate, becomes one bureau, and the policy has one rule for anything missing at the deadline: refer.
[reveal: v-276]
[pause: 0.45]
C: What it gives up, precisely: about three percent of applications are referred, and about one in five of those customers walks away before the text arrives.
C: There is no small-known-customer row and no second bureau to fall back on.
C: The crossover, from the scale line.
[reveal: v-277]
[pause: 0.45]
C: Lost loans cost about A times three percent, times one in five walking away, times forty-two percent who would have taken a loan, times about seventy dollars of margin: eighteen cents an application a month.
C: A second bureau costs about sixty thousand dollars a month in minimums and integration.
C: The two meet at about three hundred and thirty thousand applications a month.
C: Illustrative numbers.
[pause: 1.1]

[slide: v-278]
[pause: 0.7]
V: Below about three hundred thousand applications a month, I would ship one bureau and refer. At two million a month, the refer path costs more than the second bureau does.
[pause: 1.6]

[pause: 1.4]

## 6 Bridge

[slide: v-279]
[pause: 1.2]
V: It works. Where does it break first?
[pause: 1.8]

[slide: v-280]
[pause: 1.3]
C: The baseline with eight attack points.
C: The credit vendors: first slow, then down for everyone.
C: The application service and its database: a phone that drops between accept and the answer.
C: Funding: a transfer that fails after booking.
[reveal: v-281]
[pause: 0.45]
C: The policy engine: a decision nobody can explain, then a new model.
C: The vault: where identity lives.
C: And the orchestrator: how we would know any of it is broken.
C: I'll take them in an order where each fix creates the next question.
[pause: 1.1]

[pause: 1.4]

## 7 Challenges

[slide: v-282]
[pause: 1.2]
C: Eight challenges, each the same way: the question, the naive answer, a case with numbers, where it breaks, the fix, why it works, the push on the fix itself, and what I'd say in the room.
[pause: 1.8]

[pause: 1.4]

## 7.1 Challenge 1: The bureau is slow

[slide: v-283]
[pause: 1.2]
N: Challenge one. One bureau call in ten takes four seconds: what does the customer at the counter see, and what does it cost?
[pause: 1.8]

[slide: v-284]
[pause: 0.6]
I: One bureau call in ten takes four seconds today. What does the customer at the counter see?
[pause: 2.0]

[slide: v-285]
[pause: 1.3]
C: The naive answer: wait, and if the bureau is slow, send the same request to the second bureau and take whichever answers first.
[reveal: v-286]
[pause: 0.45]
C: That's a hedged request, and for an internal read it's a fine idea.
[reveal: v-287]
[pause: 0.45]
C: Here, look at the red vendors box.
[reveal: v-288]
[pause: 0.45]
C: Waiting misses the promise.
C: Racing pays twice.
[pause: 1.1]

[slide: v-289]
[pause: 1.0]
C: The trace.
[reveal: v-290]
[pause: 0.45]
C: Submit at ten o'clock.
[reveal: v-291]
[pause: 0.45]
C: At fifty milliseconds, identity, fraud and bureau A go out.
[reveal: v-292]
[pause: 0.45]
C: Identity and fraud are back by four tenths.
[reveal: v-293]
[pause: 0.45]
C: At one second, the hedge sends the same pull to bureau B, which answers at one point seven, so offers appear at about two seconds.
[reveal: v-294]
[pause: 0.45]
C: Good, until bureau A answers at four point one: a second paid pull, and a second inquiry on the customer's credit file.
[reveal: v-295]
[pause: 0.45]
C: Without the hedge, the offers appear at about four point four seconds, past the three-second promise.
C: So both answers are wrong, and they are wrong in different currencies: time, and money.
[pause: 1.0]

[slide: v-296]
[pause: 1.3]
C: The fix lives in the orchestrator, outlined green.
[reveal: v-297]
[pause: 0.45]
C: All required calls go out at once, and it decides at a two-second deadline with what has arrived.
C: If everything arrives earlier, it decides earlier.
[reveal: v-298]
[pause: 0.45]
C: A circuit breaker per vendor stops calling a vendor that is failing for everyone, so nobody waits on a known outage.
C: And the second bureau is called only after an error or an open breaker, never as a race against a slow but healthy first call.
[reveal: v-299]
[pause: 0.45]
C: L-one is bounded by the deadline.
C: S-four holds, because a second pull happens only when the first has failed.
[reveal: v-300]
[pause: 0.45]
C: Rejected: Waiting for the slowest vendor.
C: The customer's wait becomes the slowest vendor's; one deadline decides with what arrived.
[pause: 1.1]

[slide: v-301]
[pause: 1.3]
C: As a sequence.
[reveal: v-302]
[pause: 0.45]
C: Check and pull go out at time zero.
[reveal: v-303]
[pause: 0.45]
C: Identity is back at four tenths.
[reveal: v-304]
[pause: 0.45]
C: At two seconds, the deadline: bureau A is silent and its breaker is still closed, so this is one slow call, not an outage.
[reveal: v-305]
[pause: 0.45]
C: The orchestrator decides with what arrived, through the missing-data policy, and does not race bureau B.
[reveal: v-306]
[pause: 0.45]
C: Bureau A's report lands at four point one, and it is recorded.
[pause: 1.1]

[slide: v-307]
[pause: 1.0]
C: In pseudocode; the service itself is Go.
C: Start a task per required vendor.
C: Wait for all of them, with one timeout.
C: Anything still pending is not cancelled: a callback records its answer when it lands, because it was billed anyway.
C: Then the code hands the features and the list of what is missing to the policy.
C: The code never decides what missing means.
C: The signed policy does.
[pause: 1.0]

[slide: v-308]
[pause: 1.0]
C: One more cost question hides in the gather. Why pay the bureau for an applicant a free check would have stopped? There are three shapes.
[reveal: v-309]
[pause: 0.45]
C: Everything in parallel saves nothing: we pay a dollar for people we were going to decline anyway.
[reveal: v-310]
[pause: 0.45]
C: A full waterfall, identity and fraud first and the bureau only on a pass, saves about four percent of two million pulls, around eighty thousand dollars a month. But it puts the identity vendor's tail, about four hundred milliseconds, in front of the bureau: three point one seconds, past the promise. So not at the counter. It is the right shape for the pre-approval at home, where nobody waits.
[reveal: v-311]
[pause: 0.45]
C: The pick is a tier zero of our own checks, about fifty milliseconds, then one parallel gather. It stops about six percent of applications before any paid call, about a hundred and twenty-six thousand dollars a month, and it spends fifty of the three hundred milliseconds of spare.
[reveal: v-312]
[pause: 0.45]
C: Tier zero is free and ours: eligibility, the blocklist and velocity checks, our own loan book, and a stored report that is still fresh. And the pull itself is a soft inquiry, recorded as such, so checking does not mark the customer's file.
[pause: 1.0]

[slide: v-313]
[pause: 0.6]
I: The bureau's answer arrives at four point one seconds, after you decided. You paid for it. What do you do with it?
[pause: 2.0]

[slide: v-314]
[pause: 0.6]
C: Three things.
C: Record it: the call happened and was billed, so it's a row with its cost.
[reveal: v-315]
[pause: 0.45]
C: Use it: if the application was referred because the bureau was missing, the late answer finishes it, and the customer gets a text with offers.
[reveal: v-316]
[pause: 0.45]
C: And never rewrite the past: an offer already shown stays as shown, because the decision record says what we knew at the time.
C: Where the contract allows, the report is kept for a re-application.
[reveal: v-317]
[pause: 0.45]
C: The honest limit: a deadline means about three percent of applications reach the missing-data path every day.
C: Which is the next question.
[pause: 0.8]

[slide: v-318]
[pause: 0.7]
V: If asked, I'd say: all vendors at once, one deadline, a breaker per vendor. I never race two bureaus, because each pull is paid. A late answer is recorded and finishes a refer.
[pause: 1.0]
N: That fix creates the next question: what if the bureau is missing for everyone?
[pause: 1.6]

[pause: 1.4]

## 7.2 Challenge 2: The bureau is down for everyone

[slide: v-319]
[pause: 1.2]
N: Challenge two. Bureau A is down for twenty minutes at the Saturday peak: who decides what happens at the counter, and how much can it cost?
[pause: 1.8]

[slide: v-320]
[pause: 0.6]
I: Bureau A is down for everyone for twenty minutes on a Saturday. What happens at the counter?
[pause: 2.0]

[slide: v-321]
[pause: 1.3]
C: Two naive answers, and they're opposites.
[reveal: v-322]
[pause: 0.45]
C: Approve with whatever data we have, or decline until it's back.
[reveal: v-323]
[pause: 0.45]
C: Both are credit-risk decisions made by an engineer in a catch block.
[reveal: v-324]
[pause: 0.45]
C: The red boxes: the vendor is gone, and the policy engine has no rule for it.
[pause: 1.1]

[slide: v-325]
[pause: 1.0]
C: The trace.
[reveal: v-326]
[pause: 0.45]
C: Eleven o'clock on Saturday, bureau A starts timing out for everyone.
[reveal: v-327]
[pause: 0.45]
C: Twenty minutes at eight a second is nine thousand six hundred applications.
[reveal: v-328]
[pause: 0.45]
C: Approve them all, and we offer about eleven and a half million dollars of credit nobody scored.
[reveal: v-329]
[pause: 0.45]
C: Decline them all, and we lose about four thousand loans, and we owe nine thousand six hundred decline notices whose only true reason is that our vendor was down.
[reveal: v-330]
[pause: 0.45]
C: That is not a reason about the applicant.
[pause: 1.0]

[slide: v-331]
[pause: 1.3]
C: The fix is in the policy engine, outlined green.
[reveal: v-332]
[pause: 0.45]
C: A missing-data table, versioned with the credit policy, signed by credit risk and approved by the partner bank.
[reveal: v-333]
[pause: 0.45]
C: Engineering builds the mechanism, with a counter, a cap and a dashboard per row.
[reveal: v-334]
[pause: 0.45]
C: Credit risk owns the numbers in it.
[reveal: v-335]
[pause: 0.45]
C: Rejected: A hard dependency on one bureau.
C: Its outage declines every applicant; a signed fallback table inside credit policy keeps deciding.
[pause: 1.1]

[slide: v-336]
[pause: 1.3]
C: Four rows, in order. One, the second bureau, after the first one's breaker has opened. Not a race: the first is known to be failing. Two, decide without a bureau, only for returning customers in good standing, at most five hundred dollars, under a daily cap of two hundred and fifty thousand. At most five hundred such loans a day.
C: Three, refer: we'll finish in about two minutes by text, and the merchant sees pending, not declined. Four, decline, but only with a reason about the applicant. Everyone gets an answer, nobody is declined for our outage, and the worst case is the cap.
[pause: 1.1]

[slide: v-337]
[pause: 1.3]
C: A refer as a sequence.
[reveal: v-338]
[pause: 0.45]
C: Bureau A's breaker is open, and bureau B's bucket is empty this second.
[reveal: v-339]
[pause: 0.45]
C: The customer is told: referred, we'll finish in two minutes by text.
[reveal: v-340]
[pause: 0.45]
C: The application waits in the refer queue, oldest first.
[reveal: v-341]
[pause: 0.45]
C: When a token frees up,
[reveal: v-342]
[pause: 0.45]
C: bureau B is pulled, the report arrives, and the customer gets a text: your offers are ready.
[pause: 1.1]

[slide: v-343]
[pause: 0.6]
I: Bureau B's contract allows five calls a second. You're sending eight.
[pause: 2.0]

[slide: v-344]
[pause: 0.6]
C: A token bucket per vendor at the contract rate: five tokens a second for bureau B.
C: A call without a token is not sent; that application is referred.
[reveal: v-345]
[pause: 0.45]
C: Three a second over the limit for twenty minutes is about three thousand six hundred referred.
C: The queue drains oldest first, when tokens free up or bureau A's breaker half-opens, inside the ten-minute promise.
[reveal: v-346]
[pause: 0.45]
C: And the cap for row two is split per merchant, so one busy merchant can't spend the whole day's cap in an hour.
[reveal: v-347]
[pause: 0.45]
C: The honest limit: some referred customers walk away.
C: So we measure refer completion and the sales lost per minute of outage, and give those numbers to credit risk when they set the caps.
[pause: 0.8]

[slide: v-348]
[pause: 0.7]
V: If asked, I'd say: every timeout is a credit decision with an owner. Credit risk signs the table. Engineering makes each row a setting with a counter, a cap and a dashboard.
[pause: 1.0]
N: The decision is settled. Next, the one step that must be atomic.
[pause: 1.6]

[pause: 1.4]

## 7.3 Challenge 3: The phone drops

[slide: v-349]
[pause: 1.2]
N: Challenge three. The customer taps accept, loses signal, and taps again on another device: how many loans?
[pause: 1.8]

[slide: v-350]
[pause: 0.6]
I: The customer taps accept, the phone loses signal, and they tap again on the merchant's tablet. How many loans?
[pause: 2.0]

[slide: v-351]
[pause: 1.3]
C: The naive answer: check whether a loan exists, and create one if it doesn't.
[reveal: v-352]
[pause: 0.45]
C: Or the saga answer: an orchestrated saga with a compensation for each step.
[reveal: v-353]
[pause: 0.45]
C: The red boxes are the application service and its database,
[reveal: v-354]
[pause: 0.45]
C: where two workers each see no loan.
[pause: 1.1]

[slide: v-355]
[pause: 1.0]
C: The trace.
C: The phone posts accept with key k-one.
[reveal: v-356]
[pause: 0.45]
C: The response is lost in the shop's dead zone.
[reveal: v-357]
[pause: 0.45]
C: A hundred and fifty milliseconds later the tablet posts accept with key k-two: another device, another key.
[reveal: v-358]
[pause: 0.45]
C: Worker one reads the application: offered, version seven, no loan.
[reveal: v-359]
[pause: 0.45]
C: Worker two reads the same.
[reveal: v-360]
[pause: 0.45]
C: Both insert.
C: Two loans, two transfers to the merchant tonight, and a customer billed twice.
[reveal: v-361]
[pause: 0.45]
C: Idempotency keys don't save this: two devices, two keys.
C: And check-then-insert doesn't either: both checks ran before either insert.
[pause: 1.0]

[slide: v-362]
[pause: 1.3]
C: The fix is one local transaction, in the database outlined green.
C: A conditional update moves the application to booked only if it is still offered and at version seven.
[reveal: v-363]
[pause: 0.45]
C: Insert the loan under a unique constraint on the application.
C: Insert the outbox row.
[reveal: v-364]
[pause: 0.45]
C: Commit.
C: If the update changed zero rows, someone else booked, so return the existing loan.
[reveal: v-365]
[pause: 0.45]
C: S-one is enforced by the one place that sees both writers.
[reveal: v-366]
[pause: 0.45]
C: Rejected: Check, then book, in the service.
C: Two retries can both pass the check; the database decides in one transaction.
[pause: 1.1]

[slide: v-367]
[pause: 1.0]
C: In code.
C: The update has two conditions: still offered, and still version seven.
C: The second worker's update matches zero rows, because the first already changed both.
C: The unique constraint on the loan's application is a second wall, in case some code path forgets the update.
C: And the outbox row commits with the loan, so the loan existing and the world hearing about it are one fact.
C: The tablet's request reads the application, finds it booked, and shows the same loan.
[pause: 1.0]

[slide: v-368]
[pause: 1.0]
C: So where does the word saga fit?
C: Walk the steps.
C: The identity check and the credit pull can't be undone: they happened and were paid.
[reveal: v-369]
[pause: 0.45]
C: Record them.
C: An offer expires by itself.
[reveal: v-370]
[pause: 0.45]
C: Booking must be atomic, one local transaction.
C: Only funding the merchant, after booking, can really be undone, by a reversal.
[reveal: v-371]
[pause: 0.45]
C: A saga is a fine tool when several steps can be undone.
C: Here only one can, and it comes after.
[pause: 1.0]

[slide: v-372]
[pause: 0.6]
I: The commit succeeded, but the relay crashed before publishing. Or it published twice.
[pause: 2.0]

[slide: v-373]
[pause: 0.6]
C: The relay is at least once by design.
C: It reads unpublished rows, publishes, and only then marks them published, so a crash in between publishes again.
[reveal: v-374]
[pause: 0.45]
C: Nothing is lost.
[reveal: v-375]
[pause: 0.45]
C: Funding and servicing de-duplicate by event I-D, and funding uses the loan I-D as its idempotency key at the bank, so even a duplicate that slips through can't pay twice.
[reveal: v-376]
[pause: 0.45]
C: The honest limit, said precisely: at-least-once delivery with idempotent consumers.
C: Not exactly once.
[pause: 0.8]

[slide: v-377]
[pause: 0.7]
V: If asked, I'd say: only one step is atomic, accept to book. A conditional update at a version, a unique loan, and the outbox row in the same commit. A second tap finds the loan.
[pause: 1.0]
N: The loan is booked once. Next, the money that moves after it.
[pause: 1.6]

[pause: 1.4]

## 7.4 Challenge 4: Funding fails after booking

[slide: v-378]
[pause: 1.2]
N: Challenge four. The loan is booked, and paying the merchant fails or goes silent: what do we undo, and what do we never resend?
[pause: 1.8]

[slide: v-379]
[pause: 0.6]
I: The loan is booked. The transfer to the merchant is rejected, or the bank times out. What do you undo?
[pause: 2.0]

[slide: v-380]
[pause: 1.3]
C: The naive answer: roll back the saga.
[reveal: v-381]
[pause: 0.45]
C: Cancel the loan, reverse the credit check, delete the application.
[reveal: v-382]
[pause: 0.45]
C: We've just seen that two of those can't be undone.
[reveal: v-383]
[pause: 0.45]
C: The red box is funding, and by now the customer has left the shop.
[pause: 1.1]

[slide: v-384]
[pause: 1.0]
C: The trace.
C: The loan is booked at two thirty-one.
[reveal: v-385]
[pause: 0.45]
C: At six, the daily batch sends eleven hundred and sixty-four dollars to the merchant: the twelve hundred less a three percent fee.
[reveal: v-386]
[pause: 0.45]
C: At two past six the bank says: account closed.
[reveal: v-387]
[pause: 0.45]
C: At three past, another merchant's transfer times out with no answer at all.
[reveal: v-388]
[pause: 0.45]
C: Re-sending both to be safe would pay the second merchant twice, if the first attempt actually went through.
[reveal: v-389]
[pause: 0.45]
C: A timeout tells you nothing about whether money moved.
[pause: 1.0]

[slide: v-390]
[pause: 1.3]
C: The fix: funding is its own state machine, after booking, outlined green.
[reveal: v-391]
[pause: 0.45]
C: Pending, sent, settled.
C: Or returned: merchant operations fixes the account, and a new attempt goes out with a new attempt number.
[reveal: v-392]
[pause: 0.45]
C: A timeout becomes a state of its own, unknown, and the only action allowed on unknown is to ask the bank, by our idempotency key.
C: Never resend.
[reveal: v-393]
[pause: 0.45]
C: The loan itself is cancelled only if the goods weren't delivered, and that's a business decision with the merchant, not a rollback.
C: L-two, with one effect: the loan I-D is the key end to end.
[reveal: v-394]
[pause: 0.45]
C: Rejected: Booking and funding in one transaction.
C: The partner bank cannot join it; funding is its own state machine.
[pause: 1.1]

[slide: v-395]
[pause: 1.3]
C: As a sequence.
[reveal: v-396]
[pause: 0.45]
C: Funding sends the transfer with the loan I-D as its key.
[reveal: v-397]
[pause: 0.45]
C: Timeout: state unknown.
[reveal: v-398]
[pause: 0.45]
C: It asks the bank: status, for this key?
[reveal: v-399]
[pause: 0.45]
C: Not found, yet.
[reveal: v-400]
[pause: 0.45]
C: So it waits for the reconciliation window.
[reveal: v-401]
[pause: 0.45]
C: The next day's file from the bank shows the transfer settled at three past six.
[reveal: v-402]
[pause: 0.45]
C: Unknown becomes settled, and nothing was resent.
[pause: 1.1]

[slide: v-403]
[pause: 0.6]
I: The bank's status A-P-I says not found for the timed-out transfer, and tomorrow's file shows it paid.
[pause: 2.0]

[slide: v-404]
[pause: 0.6]
C: Not found, minutes after a timeout, does not mean not sent: many bank interfaces index instructions late.
C: So no resend before the reconciliation window closes.
[reveal: v-405]
[pause: 0.45]
C: Every day we compare three things: our funding records, the bank's settlement file, and the loans booked.
[reveal: v-406]
[pause: 0.45]
C: Every difference is a break, with an owner and an age, and a break older than two days pages someone.
[reveal: v-407]
[pause: 0.45]
C: The honest limit: some outcomes are only known the next day.
C: The merchant's portal says in progress, not a guess.
[pause: 0.8]

[slide: v-408]
[pause: 0.7]
V: If asked, I'd say: the credit pull and the booking happened. The one real undo is funding, so it's its own state machine, with unknown as a state. Query, never resend.
[pause: 1.0]
N: Money is settled. Next, a question about the past: why did we decide what we decided?
[pause: 1.6]

[pause: 1.4]

## 7.5 Challenge 5: Explain a decision fourteen months later

[slide: v-409]
[pause: 1.2]
N: Challenge five. A regulator asks why a customer was declined more than a year ago: can we show what we knew, and what we decided, then?
[pause: 1.8]

[slide: v-410]
[pause: 0.6]
I: A regulator asks why a customer was declined fourteen months ago. Reproduce it.
[pause: 2.0]

[slide: v-411]
[pause: 1.3]
C: The naive answer: re-run the model on the customer's data.
[reveal: v-412]
[pause: 0.45]
C: The red box is the policy engine,
[reveal: v-413]
[pause: 0.45]
C: and it only knows today:
[reveal: v-414]
[pause: 0.45]
C: today's model, today's rules, and today's credit file.
[pause: 1.1]

[slide: v-415]
[pause: 1.0]
C: The trace.
[reveal: v-416]
[pause: 0.45]
C: In January twenty twenty-six, application two-oh-four is declined by model version nine under policy thirty-one, and the customer is sent a notice: high utilisation, short history.
[reveal: v-417]
[pause: 0.45]
C: During the year, five model versions ship.
[reveal: v-418]
[pause: 0.45]
C: In March twenty twenty-seven the regulator asks why.
[reveal: v-419]
[pause: 0.45]
C: Someone re-runs today's model on today's credit file, and it approves.
[reveal: v-420]
[pause: 0.45]
C: Now we hold a notice that says one thing and a replay that says another, and neither shows the regulator what actually happened.
[pause: 1.0]

[slide: v-421]
[pause: 1.3]
C: The fix: an immutable decision record, outlined green, written once by the orchestrator for every decision.
[reveal: v-422]
[pause: 0.45]
C: Old model artefacts stay loadable in a registry.
[reveal: v-423]
[pause: 0.45]
C: And a replay job runs every night on a sample of records and alarms on any difference.
[reveal: v-424]
[pause: 0.45]
C: S-two: the same inputs and the same versions give the same answer, and we prove it every night rather than on the day we're asked.
[reveal: v-425]
[pause: 0.45]
C: Rejected: Rebuilding a decision from today's data.
C: The bureau data and the model have moved on; record what we knew, once.
[pause: 1.1]

[slide: v-426]
[pause: 1.3]
C: What a record holds. Inputs, frozen: the bureau report stored encrypted and referenced, the identity and fraud results, our own history as of that moment, the exact feature vector, and which calls were missing. Versions: model, policy including the missing-data table, pricing, disclosure, and the orchestrator build.
C: Outputs: the outcome and offers, the ranked reasons, the degraded path taken, the timings, and who signed the policy. About fifty kilobytes, written once.
[pause: 1.1]

[slide: v-427]
[pause: 1.0]
C: Why a record, and not a log line? Because each rule reads a specific part of it, so name them.
[reveal: v-428]
[pause: 0.45]
C: The Equal Credit Opportunity Act and its Regulation B: a notice within thirty days of a complete application, with the specific principal reasons. Four at most is the usual practice. Those are the ranked reasons, from the model and from every rule that fired.
[reveal: v-429]
[pause: 0.45]
C: The Fair Credit Reporting Act: when a credit report was used, the notice names the bureau, gives the score and its key factors, and tells the customer they can get a free report and dispute it. So the record keeps the bureau, the report reference, the score and factors, whether the inquiry was soft or hard, and the permissible purpose for the pull.
[reveal: v-430]
[pause: 0.45]
C: Fair lending: no decision on a prohibited basis, tested for disparate impact. The fairness tests need the exact feature vector and the model version.
[reveal: v-431]
[pause: 0.45]
C: And model risk management at the partner bank: a model that is validated, documented and monitored. The registry holds each version with its validation record.
[reveal: v-432]
[pause: 0.45]
C: This is general, not legal advice. Compliance owns the reading of each rule. Engineering's job is to make each answer a field that is written once.
[pause: 1.0]

[slide: v-433]
[pause: 1.3]
C: The replay as a sequence.
C: The request: explain two-oh-four from January.
[reveal: v-434]
[pause: 0.45]
C: Load the record: the features, the report reference, model nine, policy thirty-one.
[reveal: v-435]
[pause: 0.45]
C: Load those versions from the registry.
[reveal: v-436]
[pause: 0.45]
C: Re-score the frozen features.
[reveal: v-437]
[pause: 0.45]
C: Decline: high utilisation, short history.
[reveal: v-438]
[pause: 0.45]
C: It matches the notice, because it is what we knew and how we decided then.
[pause: 1.1]

[slide: v-439]
[pause: 0.6]
I: The customer asks us to delete their data. The record holds their bureau report.
[pause: 2.0]

[slide: v-440]
[pause: 0.6]
C: Who decides comes first.
C: Retention duties for credit records generally take precedence for their period, and that call belongs to compliance, not engineering.
[reveal: v-441]
[pause: 0.45]
C: Within the period, the record holds tokens rather than identity, and the report is encrypted under a key per record, with use restricted to the purposes the rules allow.
[reveal: v-442]
[pause: 0.45]
C: At the end of retention we destroy the record's key.
C: That makes every copy unreadable at once, backups included, without hunting for them.
[reveal: v-443]
[pause: 0.45]
C: That's called crypto-shredding.
C: The honest limit: a deletion request inside the period is answered by restricting use, and the customer is told so.
[pause: 0.8]

[slide: v-444]
[pause: 0.7]
V: If asked, I'd say: I never re-run today's model to explain yesterday. Every decision freezes its inputs, versions and reasons, and a nightly replay proves they still reproduce.
[pause: 1.0]
N: Records make the past safe. The next question changes the future: a new model.
[pause: 1.6]

[pause: 1.4]

## 7.6 Challenge 6: A new model approves six percent more

[slide: v-445]
[pause: 1.2]
N: Challenge six. Data science has a model that approves more people: how do we learn whether they repay without betting a hundred million dollars?
[pause: 1.8]

[slide: v-446]
[pause: 0.6]
I: Data science has a new model. It approves six percent more people at the same predicted loss. Roll it out.
[pause: 2.0]

[slide: v-447]
[pause: 1.3]
C: The naive answers: shadow mode for a week, it looks good, switch it on.
[reveal: v-448]
[pause: 0.45]
C: Or a fifty-fifty test.
[reveal: v-449]
[pause: 0.45]
C: The red box is the policy engine,
[reveal: v-450]
[pause: 0.45]
C: and a switch there changes about a hundred million dollars of exposure a month.
[pause: 1.1]

[slide: v-451]
[pause: 1.0]
C: The trace.
C: Six percent of two million is a hundred and twenty thousand more approvals a month.
[reveal: v-452]
[pause: 0.45]
C: At seventy percent take-up, about eighty-four thousand more loans, about a hundred million dollars a month of new exposure.
[reveal: v-453]
[pause: 0.45]
C: The first payments fall due in two to four weeks, and losses only become visible at ninety to a hundred and twenty days.
[reveal: v-454]
[pause: 0.45]
C: A week of shadow shows the approval rate.
[reveal: v-455]
[pause: 0.45]
C: It shows nothing about whether the newly approved people repay.
[reveal: v-456]
[pause: 0.45]
C: And a fifty-fifty test bets fifty million a month to find out.
[pause: 1.0]

[slide: v-457]
[pause: 1.3]
C: The fix: champion and challenger, outlined green.
[reveal: v-458]
[pause: 0.45]
C: The challenger sits beside the champion, and decides only a capped slice.
[reveal: v-459]
[pause: 0.45]
C: Every record says which model decided, so S-two holds, and the cost of learning is bounded by the cap.
[reveal: v-460]
[pause: 0.45]
C: Rejected: Switching to the new model for everyone.
C: An approval-rate jump is a risk jump; run a capped challenger.
[pause: 1.1]

[slide: v-461]
[pause: 1.3]
C: The steps. A backtest on labelled history. Then shadow: both models score every application, the champion acts, and we compare approval rates and reasons by segment and by protected group. Then a challenger slice: five percent of traffic, under its own cap. Five percent of the extra approvals is about six thousand a month, four thousand two hundred loans, about five million dollars, signed by credit risk and the partner bank.
C: Then early signals at thirty to forty-five days: a first payment missed, compared between similar people approved by each model. And widening only through a policy version change, with a kill switch per version.
[pause: 1.1]

[slide: v-462]
[pause: 0.6]
I: Shadow looked great. Why isn't that enough?
[pause: 2.0]

[slide: v-463]
[pause: 0.6]
C: Because shadow cannot see loss.
C: The people only the challenger would approve were declined by the champion.
C: They never got a loan, so there's no repayment to observe.
[reveal: v-464]
[pause: 0.45]
C: Only a slice where the challenger actually decides gives them loans, and gives us labels.
[reveal: v-465]
[pause: 0.45]
C: Fairness checks run twice: on shadow, for who would be approved, and on the slice, for who repays.
[reveal: v-466]
[pause: 0.45]
C: The honest limit: a slice is real money at risk.
C: The cap is the price of learning, and credit risk owns that price.
[pause: 0.8]

[slide: v-467]
[pause: 0.7]
V: If asked, I'd say: shadow tells you who a new model would approve, not whether they repay. So: backtest, shadow, a capped slice, early signals at thirty days, and a kill switch.
[pause: 1.0]
N: Training the next model needs data. Which data is the next question.
[pause: 1.6]

[pause: 1.4]

## 7.7 Challenge 7: Where identity data lives

[slide: v-468]
[pause: 1.2]
N: Challenge seven. Analytics wants the application data to train a model: what do they get, and where does identity actually live?
[pause: 1.8]

[slide: v-469]
[pause: 0.6]
I: The analytics team wants application data to train the next model. What do they get?
[pause: 2.0]

[slide: v-470]
[pause: 1.3]
C: The naive answers: give them a copy of the database, it's encrypted at rest.
[reveal: v-471]
[pause: 0.45]
C: Or drop the name column.
[reveal: v-472]
[pause: 0.45]
C: The red boxes are the application service,
[reveal: v-473]
[pause: 0.45]
C: its database, and the export to analytics, and identity goes wherever they go.
[pause: 1.1]

[slide: v-474]
[pause: 1.0]
C: The trace, in version two.
C: The application table holds the social security number, the date of birth and the address.
[reveal: v-475]
[pause: 0.45]
C: The bureau adapter's debug log prints the full request.
[reveal: v-476]
[pause: 0.45]
C: Every support agent sees the full number.
[reveal: v-477]
[pause: 0.45]
C: The training extract drops names but keeps date of birth and postcode, which together re-identify most people.
[reveal: v-478]
[pause: 0.45]
C: One leaked extract is two million identities a month.
[reveal: v-479]
[pause: 0.45]
C: And encryption at rest protects a stolen disk.
C: It does nothing for a query, a log line or an export.
[pause: 1.0]

[slide: v-480]
[pause: 1.3]
C: The fix: an identity vault, outlined green.
[reveal: v-481]
[pause: 0.45]
C: Identity is tokenised at apply.
[reveal: v-482]
[pause: 0.45]
C: Only two things sit inside the boundary: the vault, and the vendor adapters, which must send real values to the bureau.
C: Every detokenise is logged with its caller and purpose, and adapter logs are scrubbed at the source.
[reveal: v-483]
[pause: 0.45]
C: So analytics gets tokens and derived features, like utilisation and history length, never identity.
C: S-three, by construction.
[reveal: v-484]
[pause: 0.45]
C: Rejected: Raw identity in every service.
C: Every copy is regulated; only the vault and the vendors see real values.
[pause: 1.1]

[slide: v-485]
[pause: 1.3]
C: The boundary, drawn small on purpose. Inside: the vault with keys per field, and the adapters. Outside, everything else: the application service and database, decision records, support tools with masked values, and analytics with features. They all carry tokens.
C: And know the rulebook, because interviewers test it. Card numbers fall under the card industry's security standard. A social security number doesn't: it falls under privacy and lending law.
[pause: 1.1]

[slide: v-486]
[pause: 0.6]
I: The vault is down.
[pause: 2.0]

[slide: v-487]
[pause: 0.6]
C: The vault is a tier-zero dependency, so it's kept small, with no business logic, replicated across zones, with its own objective of ninety-nine point nine five percent and its own on-call.
[reveal: v-488]
[pause: 0.45]
C: When it's down, nothing new can start: applications refer, and the merchant sees pending.
C: Loans already booked carry on.
[reveal: v-489]
[pause: 0.45]
C: And nothing raw is ever cached outside it to help.
[reveal: v-490]
[pause: 0.45]
C: The honest limit: the vault is reliable because it is small.
C: Resist every feature request that would grow it.
[pause: 0.8]

[slide: v-491]
[pause: 0.7]
V: If asked, I'd say: analytics gets tokens and features, never identity. Only the vault and the adapters see real values, and every access is logged.
[pause: 1.0]
N: Last challenge: with all of this in place, how would we know it is broken?
[pause: 1.6]

[pause: 1.4]

## 7.8 Challenge 8: How would you know it is broken?

[slide: v-492]
[pause: 1.2]
N: Challenge eight. The dashboards are green: how would we know decisions are going wrong, before merchants tell us?
[pause: 1.8]

[slide: v-493]
[pause: 0.6]
I: Your dashboards are green. How would you know decisions are going wrong?
[pause: 2.0]

[slide: v-494]
[pause: 1.3]
C: The naive answer:
[reveal: v-495]
[pause: 0.45]
C: error rate, latency and CPU.
[reveal: v-496]
[pause: 0.45]
C: The red box is the policy engine,
[reveal: v-497]
[pause: 0.45]
C: which can return perfectly valid, perfectly wrong decisions.
[pause: 1.1]

[slide: v-498]
[pause: 1.0]
C: The trace.
C: At six on Friday evening, a pricing-table change maps one bureau field wrongly.
[reveal: v-499]
[pause: 0.45]
C: No errors, latency fine, C-P-U flat.
[reveal: v-500]
[pause: 0.45]
C: The approval rate across all merchants drops from sixty-two to forty-one percent.
[reveal: v-501]
[pause: 0.45]
C: At about two applications a second, that's seven thousand two hundred an hour, about fifteen hundred wrongly declined every hour, each with a notice.
[reveal: v-502]
[pause: 0.45]
C: It's found at nine on Saturday morning, when merchants start calling.
[reveal: v-503]
[pause: 0.45]
C: About twenty-two thousand customers, if the evening rate held.
[pause: 1.0]

[slide: v-504]
[pause: 1.3]
C: The fix: measure the decision, not the servers, outlined green across the orchestrator, the policy engine and funding.
[reveal: v-505]
[pause: 0.45]
C: And ship every policy and pricing change as a canary on a small slice, with the approval-rate alarm armed.
[reveal: v-506]
[pause: 0.45]
C: This change would have been caught in minutes, on a few hundred applications.
[reveal: v-507]
[pause: 0.45]
C: Rejected: Dashboards of server health.
[reveal: v-508]
[pause: 0.45]
C: The servers are fine while approvals fall; watch the decision itself.
[pause: 1.1]

[slide: v-509]
[pause: 1.0]
C: Six signals.
C: Offers within three seconds: the promise itself.
[reveal: v-510]
[pause: 0.45]
C: Approval rate per merchant per hour against its own baseline: a sudden drop is almost never the customers.
[reveal: v-511]
[pause: 0.45]
C: The fallback rate per policy row against its cap, because credit risk was promised a cap.
[reveal: v-512]
[pause: 0.45]
C: Loans booked and not funded, which is money owed.
[reveal: v-513]
[pause: 0.45]
C: Vendor errors, latency and spend.
[reveal: v-514]
[pause: 0.45]
C: And the mix of decline reasons: a new dominant reason is a change, not a population.
[pause: 1.0]

[slide: v-515]
[pause: 1.0]
C: Then read them in pairs.
C: Approval down with vendor errors flat and a deploy at the same time: our change.
[reveal: v-516]
[pause: 0.45]
C: Refer rate up with a breaker open: an outage being handled as designed.
[reveal: v-517]
[pause: 0.45]
C: Offer latency up with breakers closed: a vendor slow, but under the threshold.
[reveal: v-518]
[pause: 0.45]
C: Booked up and funded flat: funding stuck.
[reveal: v-519]
[pause: 0.45]
C: And one decline reason jumping while one bureau's fields shift: the vendor changed a field.
[pause: 1.0]

[slide: v-520]
[pause: 0.6]
I: Approval drops at one merchant only.
[pause: 2.0]

[slide: v-521]
[pause: 0.6]
C: Per-merchant baselines, by hour of the week.
[reveal: v-522]
[pause: 0.45]
C: A drop at one merchant is usually an integration bug, like amounts sent in dollars instead of cents, or a fraud ring testing stolen identities.
[reveal: v-523]
[pause: 0.45]
C: So it goes to merchant operations or fraud, not to credit risk.
[reveal: v-524]
[pause: 0.45]
C: The honest limit: small merchants have noisy baselines.
C: Alarm on totals over a window, not on a single hour.
[pause: 0.8]

[slide: v-525]
[pause: 0.7]
V: If asked, I'd say: I watch the decision, not the servers. Offers in three seconds, approval per merchant, fallback against its cap, and two metrics together for the cause.
[pause: 1.6]

[pause: 1.4]

## 8 Build cost

[slide: v-526]
[pause: 1.2]
C: Build cost. This is the manager layer, marked aux: skip it in a pure Staff round, use it in a manager round.
[pause: 1.8]

[slide: v-527]
[pause: 1.0]
C: Three releases.
C: Version one, sequential calls and one table: three engineers, two months, mostly to learn the vendors.
[reveal: v-528]
[pause: 0.45]
C: Version two, the orchestrator, state machine, outbox and policy engine: a team of six for two quarters.
[reveal: v-529]
[pause: 0.45]
C: Version three, the vault, records, policy table, funding and the challenger: two teams for two more quarters, plus security and compliance time.
[reveal: v-530]
[pause: 0.45]
C: Riskiest work first: the vendor adapters and the policy table, because they decide whether the counter promise holds.
[pause: 1.0]

[slide: v-531]
[pause: 1.3]
C: Six owners. Applications and origination own the state machine and booking. The decisioning platform owns the orchestrator, the policy engine and serving. Vendor integrations own the adapters, contracts and spend. Security owns the vault. Credit risk and data science own the models and every degraded path. Compliance owns disclosures, notices and retention.
C: The contracts between them are three: the decision interface, the decision record, and the loan booked event.
[pause: 1.1]

[slide: v-532]
[pause: 1.0]
C: The seams are only real if each contract has one owner and a rule for change.
[reveal: v-533]
[pause: 0.45]
C: The decision interface: decisioning owns it, origination consumes it. Versioned, additive changes only, and the two-second deadline is part of the contract, not a hope.
[reveal: v-534]
[pause: 0.45]
C: The loan booked event: origination produces it, and the servicing ledger, funding and the merchant webhooks consume it. It sits in a schema registry, backward compatible, and each consumer's contract tests run in the producer's build, so origination cannot break servicing by accident.
[reveal: v-535]
[pause: 0.45]
C: The decision record: written once, read by compliance and model risk. A new field is a new schema version, and the nightly replay must still pass.
[reveal: v-536]
[pause: 0.45]
C: The vendor adapter: one normalised answer plus what it cost. A new vendor is a new adapter, not a change to the orchestrator.
[reveal: v-537]
[pause: 0.45]
C: And the policy version: credit risk signs it, with two people and the bank, and it ships as data behind a canary.
[reveal: v-538]
[pause: 0.45]
N: That's Conway's law used on purpose. Draw the contracts first, give each team one side, and make a contract change need both sides' review.
[pause: 1.0]

[slide: v-539]
[pause: 0.6]
C: Buy, build, or defer.
C: Buy the data: bureaus, identity and bank data, and a tokenisation vault is a reasonable buy.
[reveal: v-540]
[pause: 0.45]
C: Build what is the decision: the orchestrator, the policy engine and the records, because a regulator asks us, not a vendor, why someone was declined.
[reveal: v-541]
[pause: 0.45]
C: With half the team, keep the deadline, the policy table, the atomic booking and the records, buy the vault, and defer the challenger and bank data.
[pause: 0.8]

[slide: v-542]
[pause: 0.6]
C: The bill, illustrative: bureau pulls about two million a month, identity about a hundred thousand, compute a small fraction.
C: The levers are report reuse, no races, and pulling only when the policy needs it.
C: The top risks: a degraded path without an owner or a cap.
[reveal: v-543]
[pause: 0.45]
C: A model change without a replayable record.
C: Identity leaking into logs.
C: And funding retries without an unknown state.
[pause: 0.8]

[pause: 1.4]

## 9 Recap

[slide: v-544]
[pause: 1.2]
C: The recap: one picture, a sentence per path, the common mistakes, and the thesis.
[pause: 1.8]

[slide: v-545]
[pause: 1.3]
C: The whole design.
[reveal: v-546]
[pause: 0.45]
C: Across the middle,
[reveal: v-547]
[pause: 0.45]
C: the counter path:
[reveal: v-548]
[pause: 0.45]
C: phone, edge, application service, orchestrator, vendors.
[reveal: v-549]
[pause: 0.45]
C: Above, the vault.
[reveal: v-550]
[pause: 0.45]
C: Below,
[reveal: v-551]
[pause: 0.45]
C: what happens after booking,
[reveal: v-552]
[pause: 0.45]
C: and what we keep:
[reveal: v-553]
[pause: 0.45]
C: the database with its outbox,
[reveal: v-554]
[pause: 0.45]
C: the event log,
[reveal: v-555]
[pause: 0.45]
C: funding, the policy engine and the decision records.
[pause: 1.1]

[slide: v-556]
[pause: 1.0]
C: Apply: tokenise, create the row, answer at once.
[reveal: v-557]
[pause: 0.45]
C: Decide: all vendors at once, one deadline, a signed policy for whatever is missing, and a record.
[reveal: v-558]
[pause: 0.45]
C: Book: one transaction, a conditional update, a unique loan and the outbox row.
[reveal: v-559]
[pause: 0.45]
C: Fund: its own state machine, with unknown as a state, reconciled every day.
[pause: 1.0]

[slide: v-560]
[pause: 1.0]
C: How it degrades, in priority order.
C: A slow bureau changes nothing: the deadline decides.
[reveal: v-561]
[pause: 0.45]
C: A bureau down uses the table: second bureau, small known customers, refer.
[reveal: v-562]
[pause: 0.45]
C: If the policy engine is down, applications are still recorded, and they wait in the refer queue.
[reveal: v-563]
[pause: 0.45]
C: If the vault is down, nothing new starts, but booked loans carry on.
[reveal: v-564]
[pause: 0.45]
C: And if the event log or funding is down, the counter doesn't notice at all: booking continues, the outbox holds the events, and merchants are paid in the next batch.
C: The customer at the counter is protected first, the merchant's money second, and everything else can wait.
[pause: 1.0]

[slide: v-565]
[pause: 0.6]
N: The mistakes that cost points.
N: In the design: treating it as a throughput problem, sequential calls, hedging paid pulls, a saga that compensates a credit pull, and check-then-insert on the loan.
[reveal: v-566]
[pause: 0.45]
N: In judgement: approve with partial data as a default, re-running today's model to explain yesterday, encrypt the database as the identity answer, the card standard quoted for identity data, and no owner for any degraded path.
[pause: 0.8]

[slide: v-567]
[pause: 0.7]
V: The core is small and boring on purpose. The design lives at the slow edges and in what we keep: one deadline with a signed policy, a record that replays, and identity in a vault.
[pause: 1.6]
