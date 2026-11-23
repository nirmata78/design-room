# SD-77 Card authorisation and issuer processing: reference solution (Staff L6/L7)

<!-- Video script for slide-video-kit/scripts/build_video.py. [slide: v-NNN] = frames/v-NNN.png; [reveal: v-NNN] = the next
     reveal step of the same slide. Generated from src/*.py: edit the sources, not this file. -->
<!-- voices: N=af_heart@0.92 I=bf_emma@0.95 C=am_michael@0.9 V=am_michael@0.84 -->
<!-- names: C=Candidate V=Candidate N=Coach I=Interviewer -->
<!-- say: API=A-P-I APIs=A-P-Is SLO=S-L-O SLOs=S-L-Os SLI=S-L-I SLIs=S-L-Is ID=I-D IDs=I-Ds EM=E-M AUX=aux SRE=S-R-E ISO=I-S-O MCC=M-C-C PAN=P-A-N BIN=B-I-N CEL=C-E-L TB=terabytes GB=gigabytes MB=megabytes KB=kilobytes p99=P-ninety-nine p50=P-fifty TLS=T-L-S YAML=yammel -->


## 0 Cold open

[slide: v-001]
[pause: 1.2]
C: Card authorisation looks like the easiest question in a fintech loop. A request arrives, you check the balance, you say yes. It is asked at every level, because that answer is wrong in three places at once.
[pause: 1.8]

[slide: v-002]
[pause: 0.6]
I: You're building a card issuer, a company that issues debit cards to its customers. Design the system that receives authorisation requests from the card network, and approves or declines them.
[pause: 1.5]

[slide: v-003]
[pause: 1.3]
C: Here is the hook. First, the deadline is not ours. The card network waits about two seconds, and if we are late it does not fail. It decides for us, with limits we set months ago, and tells us afterwards.
C: Second, no money moves at the till. An approval is a promise, recorded as a hold. The real amount arrives days later in a file, often different, sometimes never.
C: Third, the fraud decision. Analysts change the rules several times a day, and we only learn whether a decision was right two months later, when the chargebacks arrive.
[pause: 1.1]

[slide: v-004]
[pause: 1.0]
N: Five axes.
[reveal: v-005]
[pause: 0.45]
N: The weak answer debits the balance and calls a fraud service.
[reveal: v-006]
[pause: 0.45]
N: The strong answer places a hold, keys every message by the network's reference, gives the model a budget, and says what happens when it is late.
[reveal: v-007]
[pause: 0.45]
C: Two facts I'll keep for the whole round.
[reveal: v-008]
[pause: 0.45]
C: The money is a hold.
[reveal: v-009]
[pause: 0.45]
C: And the deadline belongs to someone else.
[pause: 1.0]

[slide: v-010]
[pause: 0.7]
V: Card authorisation is a promise made inside someone else's deadline. A hold, not a debit. Every message once, in any order. A written answer for when a step is late. And a ledger that absorbs what we did not decide.
[pause: 1.6]

[slide: v-011]
[pause: 0.6]
C: The order.
C: Requirements, numbers, and a short theory chapter.
[reveal: v-012]
[pause: 0.45]
C: Then the messages and the data, and a design in three versions, each answering the objection to the one before.
[reveal: v-013]
[pause: 0.45]
C: Then most of the time goes to eight challenges that break it, where each fix creates the next question.
C: A build cost, and a recap.
[pause: 0.8]

[pause: 1.4]

## 1 Requirements and scope

[slide: v-014]
[pause: 1.2]
C: Six questions before I draw anything. Each answer moves the design.
[pause: 1.8]

[slide: v-015]
[pause: 0.6]
C: How many cards, and how much traffic?
I: Eight million debit cards.
I: Fifteen hundred authorisations a second at the evening peak, four thousand on the busiest shopping day of the year.
C: Four thousand a second is a small fleet.
C: So throughput will not be the problem.
C: The tail of the slowest step will be.
[pause: 0.6]

[slide: v-016]
[pause: 0.6]
C: What is the deadline, and what happens if we miss it?
I: The network times out after about two seconds, and then it stands in.
I: Your own target is up to you.
C: Then I'll correct a common prep line out loud: the network does not give us a hundred milliseconds.
C: Its timeout is seconds, and our target is a choice.
C: I'll take three hundred milliseconds at the ninety-ninth percentile, measured at our gateway, and design for the case when we miss it anyway.
[pause: 0.6]

[slide: v-017]
[pause: 0.6]
C: Which messages do we receive?
I: Authorisation, incremental authorisation, reversal, advice, and refund.
I: Clearing comes in a daily file.
C: So it is a message state machine, not one request type.
C: A reversal can cancel an approval.
C: An advice tells us what the network decided while we were away.
C: And the file comes days later.
[pause: 0.6]

[slide: v-018]
[pause: 0.6]
C: What do fraud and rules look like?
I: Losses are about eight basis points of volume.
I: Chargebacks and customer reports arrive thirty to ninety days later.
I: Analysts change rules several times a day, and they don't want a code release for it.
C: Thirty to ninety days is the number I'll come back to.
C: It means we cannot learn quickly whether a decline was right.
C: Challenge six.
[pause: 0.6]

[slide: v-019]
[pause: 0.6]
C: Where does the balance live, and does clearing always match?
I: The balance lives in our core ledger.
I: Clearing amounts can differ from the authorisation, and some authorisations never clear.
C: Then an approval must not touch the ledger's balance.
C: It places a hold, and clearing moves the real amount.
C: That is challenge one.
[pause: 0.6]

[slide: v-020]
[pause: 0.6]
C: Do we ever see full card numbers?
I: No.
I: The processor in front of you keeps them in its vault, and sends you a token.
I: Keep it that way.
C: Good.
C: That keeps the card-data scope at the processor.
C: Everything I design keys on the token.
[pause: 0.6]

[slide: v-021]
[pause: 0.6]
C: Four functional requirements.
C: One, authorise: approve or decline inside the deadline, and an approval places a hold.
[reveal: v-022]
[pause: 0.45]
C: Two, reverse and advise: reversals release holds, and stand-in advices are recorded, even past the balance.
[reveal: v-023]
[pause: 0.45]
C: Three, clear: match each clearing record to its hold, post the real amount, and expire the holds that never clear.
[reveal: v-024]
[pause: 0.45]
C: Four, change rules: analysts publish rules as versioned data, with a staged rollout, and no deploy.
C: Each of these gets a numbered flow.
[pause: 0.8]

[slide: v-025]
[pause: 0.6]
C: The numbers, and they are initial targets.
C: Three hundred milliseconds at the ninety-ninth percentile at our gateway.
[reveal: v-026]
[pause: 0.45]
C: Four nines for the authorisation path, because every minute we are down is a minute of stand-in for every card.
[reveal: v-027]
[pause: 0.45]
C: Every network message takes effect once.
[reveal: v-028]
[pause: 0.45]
C: A rule change live within five minutes.
C: And four more.
[reveal: v-029]
[pause: 0.45]
C: Our own approvals never take an account below zero.
C: Every decision reproducible for seven years, for disputes.
C: Clearing posted by nine in the morning.
C: And degraded decisions inside an hourly exposure cap that risk and finance sign.
[pause: 0.8]

[slide: v-030]
[pause: 0.6]
C: In scope: the decision, holds, reversals and advices, rules and the model score, online features, the fail policy, clearing, and the decision events.
C: Out, on purpose.
C: Issuing the cards.
[reveal: v-031]
[pause: 0.45]
C: The network and the processor themselves.
C: The disputes workflow: I only read its labels.
C: Statements, model training, credit products.
C: And the three-D Secure challenge flow, whose result simply arrives as one more input field.
[pause: 0.8]

[slide: v-032]
[pause: 0.7]
V: The core is three things. A decision path that always answers inside the deadline. A hold ledger where each message takes effect once. And a clearing path that turns promises into posted money.
[pause: 0.8]
N: The candidate named the core before drawing a box. That is the scoping signal the interviewer is waiting for.
[pause: 1.6]

[pause: 1.4]

## 2 Estimates

[slide: v-033]
[pause: 1.2]
C: Numbers next, each as arithmetic, each with the decision it drives. I'll label them: given, derived or illustrative.
[pause: 1.8]

[slide: v-034]
[pause: 1.0]
C: Traffic.
C: Four thousand a second on the busiest day.
[reveal: v-035]
[pause: 0.45]
C: Say twenty million messages a day, which is about two hundred and thirty a second on average and two and a half per card per day.
C: That number is illustrative, and it sizes logs and files, not servers.
C: Concurrency.
[reveal: v-036]
[pause: 0.45]
C: Four thousand a second, times three hundred milliseconds, is twelve hundred requests in flight at worst, about four hundred at a typical hundred milliseconds.
C: Small.
C: Each reads three things: the account and its holds, the card, and the counters.
[reveal: v-037]
[pause: 0.45]
C: Twelve thousand reads a second, each budgeted at a few milliseconds.
C: The decision this drives: the state a decision needs lives next to the decision, in a store built for millisecond reads.
C: Never the core ledger, on the hot path.
[pause: 1.0]

[slide: v-038]
[pause: 1.0]
C: The hold book.
C: Say twelve million approvals a day, each open about three days until it clears.
[reveal: v-039]
[pause: 0.45]
C: That's thirty-six million open holds, and at about two hundred bytes each, seven gigabytes.
C: The whole book fits in memory, partitioned by account.
[reveal: v-040]
[pause: 0.45]
C: Per account, the rate is tiny: a busy card does a few authorisations a minute.
C: So serialising every write for one account costs nothing.
[reveal: v-041]
[pause: 0.45]
C: The exception is a business account with two thousand cards on one balance.
C: Even that is about three a second on one key.
C: I'll keep it for challenge two.
[pause: 1.0]

[slide: v-042]
[pause: 1.0]
C: What a slow model costs.
C: If two percent of decisions at the peak miss the model's slot, that's four thousand a second, times sixty seconds, times two percent: forty-eight hundred decisions a minute decided on rules alone.
[reveal: v-043]
[pause: 0.45]
C: At an average of sixty dollars and our base fraud rate of eight basis points, that is about two hundred and thirty dollars a minute of expected loss.
C: Small.
[reveal: v-044]
[pause: 0.45]
C: But fraud concentrates exactly where the model is blind, so the real number is several times higher.
C: Falling back is a money decision, so it gets a cap and an owner.
C: Challenge four.
[pause: 1.0]

[slide: v-045]
[pause: 1.0]
C: The batch side.
C: The clearing file: about ten million records of five hundred bytes, five gigabytes a day.
C: Minutes of work.
[reveal: v-046]
[pause: 0.45]
C: The hard part is matching, not volume.
C: A bad file with three percent duplicated is three hundred thousand records that must do nothing.
[reveal: v-047]
[pause: 0.45]
C: The decision log: twenty million decisions of about two kilobytes, forty gigabytes a day, fifteen terabytes a year, kept seven years in object storage.
[reveal: v-048]
[pause: 0.45]
C: And an outage: twenty minutes at night at three hundred a second is three hundred and sixty thousand decisions the network made for us.
C: Challenge seven.
[pause: 1.0]

[slide: v-049]
[pause: 1.0]
C: Before the budget, what the numbers decide, in one table.
C: Twelve thousand reads a second means a dedicated authorisation store.
[reveal: v-050]
[pause: 0.45]
C: Seven gigabytes of holds means it lives in memory, partitioned by account.
[reveal: v-051]
[pause: 0.45]
C: A few authorisations a minute per account means serialising each account costs nothing.
[reveal: v-052]
[pause: 0.45]
C: Two hundred and thirty dollars a minute, at least, for a slow model means the fallback needs a cap and an owner.
[reveal: v-053]
[pause: 0.45]
C: And three hundred and sixty thousand advices after an outage means we record every one, once, whatever it does to the balance.
C: An estimate that changes nothing is decoration.
[pause: 1.0]

[slide: v-054]
[pause: 1.3]
C: The budget. Checks first: parse the message and look up its reference, read the account and the card, read and increment the counters, run the rules. About twenty-three milliseconds. The model gets sixty, and then a cut-off. Reserving the hold and replying, about fifteen.
C: Ninety-eight milliseconds at the cut-off, two hundred spare. The spare is not waste. It is room for a pause, a failover and a slow hop at the same time, before the network's own clock is in danger. And the budget says the model is the only step allowed to be slow, and only up to its cut-off.
[pause: 1.1]

[pause: 1.4]

## 3 Theory

[slide: v-055]
[pause: 1.2]
C: A short theory chapter before the design, so the design can lean on it. What this system is and is not, the properties, the central tension, seven mechanisms, an options matrix, and the failure catalogue.
[pause: 1.8]

[slide: v-056]
[pause: 0.7]
V: An issuer's authorisation system answers the network before its deadline, reserves the amount as a hold against the available balance, and later settles the real amount from the clearing file.
[pause: 1.0]
C: Every clause is load-bearing. Before its deadline: miss it, and the network decides for us. A hold: no money moves at the till. Available balance: posted balance minus the holds. And later settles the real amount: clearing can differ, or never come.
[pause: 1.6]

[slide: v-057]
[pause: 0.6]
C: Four neighbours it is confused with.
C: It is not a payment: no money moves at authorisation.
[reveal: v-058]
[pause: 0.45]
C: It is not a debit: a hold can grow with a tip, shrink, be reversed, clear for a different amount, or simply expire.
[reveal: v-059]
[pause: 0.45]
C: It is not the fraud model: the model is one input with a budget, and the decision happens with or without it.
[reveal: v-060]
[pause: 0.45]
C: And it is not the core ledger: holds live next to the decision, posted money lives in the ledger, and the two are reconciled every day.
[pause: 0.8]

[slide: v-061]
[pause: 0.6]
C: Safety, what must never happen.
C: S-one: our own approvals never take an account below zero.
C: Note the word own: the network's decisions will, and that is challenge seven.
C: S-two: no network message takes effect twice.
C: S-three: no decision we cannot reproduce.
[reveal: v-062]
[pause: 0.45]
C: Liveness, what must eventually happen.
C: L-one: every authorisation gets an answer inside the deadline, degraded if need be, never silence.
C: L-two: every hold ends.
C: L-three: a rule change takes effect within minutes.
C: Every fix from here names which one it serves.
[pause: 0.8]

[slide: v-063]
[pause: 1.3]
C: The central tension. Each signal buys quality and costs time. Rules are ten milliseconds. The model adds tens more. Rich aggregates on request would add hundreds. The curve flattens: past our three-hundred millisecond target, the gain is small.
C: And past the network's deadline, on the right, the network decides with far less information than we have. So the design spends the deadline deliberately, and writes down in advance what happens when a step is late.
[pause: 1.1]

[slide: v-064]
[pause: 0.6]
C: Mechanism one, holds with expiry.
C: It protects S-one and L-two.
[reveal: v-065]
[pause: 0.45]
C: An approval inserts a hold, and available is posted minus active holds.
C: Incrementals raise it, reversals release it, clearing moves it to posted, and a lifetime by merchant type ends it.
[reveal: v-066]
[pause: 0.45]
C: It rules out debiting at the till, and money stuck forever.
[reveal: v-067]
[pause: 0.45]
C: It costs a lifecycle, an expiry job, and a pending amount the customer must understand.
[pause: 0.8]

[slide: v-068]
[pause: 0.6]
C: Mechanism two, idempotency on the network reference.
C: It protects S-two.
[reveal: v-069]
[pause: 0.45]
C: A message table keyed by the reference the network gives us.
C: A retry returns the stored answer.
C: A reversal that arrives before its original is kept as a tombstone.
[reveal: v-070]
[pause: 0.45]
C: It rules out a retry placing two holds, and an early reversal being lost.
[reveal: v-071]
[pause: 0.45]
C: It costs a message store kept for days.
[pause: 0.8]

[slide: v-072]
[pause: 0.6]
C: Mechanism three, the per-account atomic reserve.
[reveal: v-073]
[pause: 0.45]
C: One conditional write, in the partition that owns the account: check available, insert the hold, record the message, bump the version.
[reveal: v-074]
[pause: 0.45]
C: It rules out two concurrent swipes both spending the same money.
[reveal: v-075]
[pause: 0.45]
C: It costs a store partitioned by account, and a shared business account becomes a hot key.
[pause: 0.8]

[slide: v-076]
[pause: 0.6]
C: Mechanism four, a latency budget with a fail-policy table.
C: It protects L-one.
[reveal: v-077]
[pause: 0.45]
C: Each step gets a slice, rules run in process, the model has a sixty millisecond cut-off, and a table says what we decide when something is late, with an hourly exposure cap.
[reveal: v-078]
[pause: 0.45]
C: It rules out a slow dependency making us miss the deadline.
[reveal: v-079]
[pause: 0.45]
C: It costs degraded decisions with real money attached, and a policy that risk and finance must own.
[pause: 0.8]

[slide: v-080]
[pause: 0.6]
C: Mechanism five, two-speed features.
[reveal: v-081]
[pause: 0.45]
C: Burst counters are read and incremented inline, in one round trip.
C: Richer aggregates come from the stream, seconds late.
C: And every feature value is logged with the decision.
[reveal: v-082]
[pause: 0.45]
C: It rules out a stream lagging behind a burst of fraud, and training on values the model never saw.
[reveal: v-083]
[pause: 0.45]
C: It costs a counter store on the hot path.
[pause: 0.8]

[slide: v-084]
[pause: 0.6]
C: Mechanism six, rules as versioned data.
[reveal: v-085]
[pause: 0.45]
C: A sandboxed expression language, a staged rollout of backtest, shadow, slice and enforce, a kill switch, an expiry, and the version on every decision.
[reveal: v-086]
[pause: 0.45]
C: It rules out a deploy to block an attack, and one bad rule declining everyone.
[reveal: v-087]
[pause: 0.45]
C: It costs tooling, and an honest limit: labels arrive months later.
[pause: 0.8]

[slide: v-088]
[pause: 0.6]
C: Mechanism seven, the clearing file as financial truth.
C: Match by reference, then fuzzy.
[reveal: v-089]
[pause: 0.45]
C: Move the amount from hold to posted.
C: Post what has no match.
C: And record the network's stand-in decisions even when they overdraw.
[reveal: v-090]
[pause: 0.45]
C: It rules out holds that never end, and books that disagree with the network's.
[reveal: v-091]
[pause: 0.45]
C: It costs an unmatched queue, and over-limit handling.
[pause: 0.8]

[slide: v-092]
[pause: 1.0]
C: Five ways to place the decision and the money.
C: A, debit the core ledger at authorisation: wrong the moment clearing differs, and the ledger's batch window sits on our path.
[reveal: v-093]
[pause: 0.45]
C: B, a chain of synchronous remote calls: correct, but the tails add up, and any slow link means stand-in.
[reveal: v-094]
[pause: 0.45]
C: C, holds in the core ledger with a budget for scoring: mostly works, but the ledger's nightly posting and maintenance still sit on the authorisation path.
[reveal: v-095]
[pause: 0.45]
C: E, let the processor decide with rules we upload: fine for a launch, until our fraud needs outgrow its rule language.
[reveal: v-096]
[pause: 0.45]
V: I pick D: our own authorisation store, next to a stateless decision service.
[pause: 1.0]

[slide: v-097]
[pause: 0.6]
C: Why D.
C: The ledger is off the hot path.
C: Holds and messages are reserved in one write.
[reveal: v-098]
[pause: 0.45]
C: Rules change as data.
C: And the model can be late without making us late.
C: What it gives up: a second copy of balances, which must be reconciled with the ledger every day.
[reveal: v-099]
[pause: 0.45]
C: And I'd say plainly: for the first months of a new card programme, E is the right answer, and it appears in the build cost.
C: Move to D when fraud needs our own model.
[pause: 0.8]

[slide: v-100]
[pause: 1.0]
C: The failure catalogue, which becomes the challenge list.
C: A tip, and a hold that never clears.
[reveal: v-101]
[pause: 0.45]
C: Two swipes on one balance.
[reveal: v-102]
[pause: 0.45]
C: A retry, and a reversal before its original.
[reveal: v-103]
[pause: 0.45]
C: The model slow tonight.
[reveal: v-104]
[pause: 0.45]
C: A burst seconds apart.
[reveal: v-105]
[pause: 0.45]
C: A new attack at two in the morning.
[reveal: v-106]
[pause: 0.45]
C: Stand-in, and a late clearing file.
[reveal: v-107]
[pause: 0.45]
C: And declines doubling while the dashboards stay green.
[reveal: v-108]
[pause: 0.45]
C: The ninth, card numbers in our systems, I dismiss: we only ever see tokens.
[pause: 1.0]

[slide: v-109]
[pause: 1.0]
N: Good theory has a consequence for the design.
[reveal: v-110]
[pause: 0.45]
N: Every mechanism here names the property it serves and where it comes back.
[reveal: v-111]
[pause: 0.45]
C: That is the vocabulary.
[reveal: v-112]
[pause: 0.45]
C: On to the messages and the data.
[pause: 1.0]

[pause: 1.4]

## 4 API and entities

[slide: v-113]
[pause: 1.2]
C: Four message families from the network, one file, and one internal call. Each tagged with the requirement it serves and the data it reads or writes.
[pause: 1.8]

[slide: v-114]
[pause: 1.0]
C: The network speaks a message standard called I-S-O eighty-five eighty-three, with numbered fields.
C: Our gateway maps it to our own messages, so nothing behind the gateway knows the wire format.
C: Authorise carries the network reference, the card token, the amount, the merchant category code and the entry mode, and gets back approve or decline with a reason.
[reveal: v-115]
[pause: 0.45]
C: The incremental raises an existing hold.
[reveal: v-116]
[pause: 0.45]
C: A reversal releases one, and may arrive before its original.
[reveal: v-117]
[pause: 0.45]
C: An advice tells us what the network decided for us, and is always acknowledged.
[reveal: v-118]
[pause: 0.45]
C: The clearing file comes once a day, and every record has its own I-D.
[reveal: v-119]
[pause: 0.45]
C: And internally, analysts post rule sets and promote them through modes.
[pause: 1.0]

[slide: v-120]
[pause: 0.6]
C: Two fields matter more than the rest.
C: The merchant category code says what kind of merchant it is: restaurant, fuel, hotel, electronics.
C: It sets how long a hold lives, and it is the strongest single fraud feature.
[reveal: v-121]
[pause: 0.45]
C: The entry mode says whether the card was present.
C: Most fraud is card-not-present, so almost every rule branches on it.
[reveal: v-122]
[pause: 0.45]
C: And the decline reason matters.
C: Suspected fraud sends the customer a text, and their reply, it was me, is the fastest false-positive signal there is.
C: That comes back in challenge six.
[pause: 0.8]

[slide: v-123]
[pause: 1.0]
C: One authorisation, both ways.
C: The network reference, R-forty-four-ten, keys everything that follows.
[reveal: v-124]
[pause: 0.45]
C: The token resolves to account A-twelve.
[reveal: v-125]
[pause: 0.45]
C: The amount travels as an integer in minor units, six thousand cents, never a floating-point number.
[reveal: v-126]
[pause: 0.45]
C: The merchant category says restaurant, and the entry mode says contactless.
[reveal: v-127]
[pause: 0.45]
C: The answer is approve with an authorisation code.
[reveal: v-128]
[pause: 0.45]
C: The rule-set and model versions are not sent to the network.
[reveal: v-129]
[pause: 0.45]
C: They go into the decision record, which is how we reproduce this decision in seven years.
[pause: 1.0]

[slide: v-130]
[pause: 1.3]
C: The conceptual model. An account has many cards. An account reserves many holds. A hold is created by a message and changed by later messages with the same reference: the incremental, the reversal.
C: Each message is recorded as a decision, a weak entity carrying the features, the rule-set version and the model version. And a hold is settled by clearing records: usually one, several for a split shipment, none for a hold that expires.
[pause: 1.1]

[slide: v-131]
[pause: 1.3]
C: The physical tables in the authorisation store. The account row: posted balance, holds total, a version, and a state that includes over-limit. Holds keyed by account and hold, with the network reference unique. And the message table keyed by the network reference, for idempotency.
C: The point is the partition key. Account, holds and messages all live in the account's partition, so one local transaction can reserve a hold and record its message together. Cards map tokens to accounts. Clearing records have their own I-Ds. And rule sets are versioned rows every decision service reads.
[pause: 1.1]

[slide: v-132]
[pause: 1.0]
C: Before choosing products, I decide which stores we may lose.
[reveal: v-133]
[pause: 0.45]
C: The authorisation store, never: holds are money, and messages are how we stay idempotent.
[reveal: v-134]
[pause: 0.45]
C: The counters,
[reveal: v-135]
[pause: 0.45]
C: yes: ten minutes of buckets, rebuilt from the event log, and the fail table covers the gap.
[reveal: v-136]
[pause: 0.45]
C: The event log, not until it is consumed.
[reveal: v-137]
[pause: 0.45]
C: The archive and the ledger, never.
[pause: 1.0]

[pause: 1.4]

## 5 High-level design

[slide: v-138]
[pause: 1.2]
C: The design in three versions, drawn on the same baseline. Each answers the objection to the one before.
[pause: 1.8]

[slide: v-139]
[pause: 1.3]
C: Version one.
C: A gateway and one decision service.
[reveal: v-140]
[pause: 0.45]
C: To authorise, it reads the balance from the core ledger and inserts a hold row there, in one transaction.
C: Rules are if-statements in the code.
[reveal: v-141]
[pause: 0.45]
C: A nightly job reads the clearing file, posts and releases.
C: For a small issuer at a hundred a second, it might be enough.
[reveal: v-142]
[pause: 0.45]
C: The objection: the core ledger's tail latency and its nightly batch window now sit on the authorisation path.
C: Every rule change is a deploy.
[reveal: v-143]
[pause: 0.45]
C: There is no fraud score.
C: And nothing answers a retried or out-of-order message.
[pause: 1.1]

[slide: v-144]
[pause: 1.3]
C: Version two answers that.
[reveal: v-145]
[pause: 0.45]
C: The decision service becomes stateless, and its state moves to an authorisation store: balances, holds and messages, partitioned by account, with one atomic reserve.
C: Rules move into the decision service's own process, pushed as versioned data by a rule service that analysts use.
[reveal: v-146]
[pause: 0.45]
C: A model scorer answers under a sixty millisecond cut-off.
C: Every decision goes to an outbox in the same write as the hold, and on to an event log.
[reveal: v-147]
[pause: 0.45]
C: A clearing matcher posts to the core ledger and releases holds, and the ledger's other balance changes, a salary in, a direct debit out, flow back to the authorisation store.
C: The new boxes are outlined in blue.
[reveal: v-148]
[pause: 0.45]
C: The objection it leaves: where do features come from?
C: What do we decide when something is late?
[reveal: v-149]
[pause: 0.45]
C: What about stand-in advices?
C: And how do two copies of the balance stay in agreement?
[pause: 1.1]

[slide: v-150]
[pause: 1.3]
C: Version three.
C: A feature store with burst counters the decision reads and increments inline, and pattern features a stream aggregator computes from the event log.
[reveal: v-151]
[pause: 0.45]
C: The fail-policy table and its exposure counters live in the decision service.
C: Advices take the same path as authorisations.
[reveal: v-152]
[pause: 0.45]
C: The rule service gains backtest and shadow.
C: Alerts, cases and the decision archive consume the event log.
[reveal: v-153]
[pause: 0.45]
C: And a daily job reconciles the authorisation store against the ledger.
C: The objection it leaves is the details.
C: Those are the challenges.
[pause: 1.1]

[slide: v-154]
[pause: 1.0]
C: The three versions in one table.
C: Version one: one service on the ledger.
[reveal: v-155]
[pause: 0.45]
C: Version two: split the decision from the ledger, and make rules data.
[reveal: v-156]
[pause: 0.45]
C: Version three: protect the deadline and close every loop.
C: Each answers the objection to the one before.
[pause: 1.0]

[slide: v-157]
[pause: 1.3]
C: Flow one, authorise.
[reveal: v-158]
[pause: 0.45]
C: One: the network sends the request through the processor.
[reveal: v-159]
[pause: 0.45]
C: Two: the gateway maps it and passes it to a decision service.
[reveal: v-160]
[pause: 0.45]
C: Three: the decision service increments this card's counter for the current minute and reads the nine before it, in one round trip.
[reveal: v-161]
[pause: 0.45]
C: Four: it sends the request to the model with a sixty millisecond cut-off, while the rules run in its own process.
[reveal: v-162]
[pause: 0.45]
C: Five:
[reveal: v-163]
[pause: 0.45]
C: to approve, it reserves the hold in the account's partition: check available, insert the hold, record the message, in one conditional write.
[reveal: v-164]
[pause: 0.45]
C: Six: the decision, with its inputs and versions, goes to the outbox in that same write, and on to the event log.
[reveal: v-165]
[pause: 0.45]
C: Seven and eight: the answer goes back through the gateway to the network.
[pause: 1.1]

[slide: v-166]
[pause: 1.3]
C: As a sequence.
[reveal: v-167]
[pause: 0.45]
C: Authorise R-forty-four-ten, sixty dollars, at a restaurant.
[reveal: v-168]
[pause: 0.45]
C: Count this swipe and read ten minutes: one millisecond.
[reveal: v-169]
[pause: 0.45]
C: The model is asked with a cut-off,
[reveal: v-170]
[pause: 0.45]
C: while rules run in process.
[reveal: v-171]
[pause: 0.45]
C: The model answers in thirty-eight milliseconds: low risk.
[reveal: v-172]
[pause: 0.45]
C: Reserve: hold sixty if available, record the message.
[reveal: v-173]
[pause: 0.45]
C: Okay, available four hundred and forty.
[reveal: v-174]
[pause: 0.45]
C: The decision goes to the outbox,
[reveal: v-175]
[pause: 0.45]
C: and the network gets approve, in ninety-one milliseconds.
[pause: 1.1]

[slide: v-176]
[pause: 1.3]
C: Flow two, reversals and advices.
[reveal: v-177]
[pause: 0.45]
C: One: the message arrives from the network.
[reveal: v-178]
[pause: 0.45]
C: Two: the gateway passes it on.
C: Three: the decision service applies it by network reference in the authorisation store.
[reveal: v-179]
[pause: 0.45]
C: A reversal releases all or part of a hold, or waits as a tombstone if its original has not arrived.
C: An advice is recorded as a hold, even if it takes the account below zero.
[reveal: v-180]
[pause: 0.45]
C: Four: the event goes to the log.
C: Five: the acknowledgement goes back.
[reveal: v-181]
[pause: 0.45]
C: Nothing here is a decision.
C: It is recording.
[pause: 1.1]

[slide: v-182]
[pause: 1.3]
C: Flow three, clearing.
[reveal: v-183]
[pause: 0.45]
C: Before step one, the matcher loads the day's file and skips record I-Ds it has already applied.
[reveal: v-184]
[pause: 0.45]
C: One: in the authorisation store, in one write, it moves the amount from the hold to the posted balance.
C: Posted goes down by seventy-two, the seventy-two dollar hold is released, and available does not move at all.
[reveal: v-185]
[pause: 0.45]
C: Two: it posts the same amount to the core ledger, keyed by the clearing record's I-D.
C: Three: the ledger's other balance changes flow back, and clearing postings already applied are recognised by record I-D and skipped.
[reveal: v-186]
[pause: 0.45]
C: Why this order?
C: If we released the hold first and waited for the ledger to lower the balance, available would jump up for a moment, and a purchase in that moment could spend money that is already gone.
[pause: 1.1]

[slide: v-187]
[pause: 1.3]
C: As a sequence.
[reveal: v-188]
[pause: 0.45]
C: File F-eleven-twenty-one, ten million records.
[reveal: v-189]
[pause: 0.45]
C: Skip record I-Ds already seen.
[reveal: v-190]
[pause: 0.45]
C: Find the hold for R-forty-four-ten: seventy-two dollars, after the tip.
[reveal: v-191]
[pause: 0.45]
C: One write: posted down seventy-two, hold released, available unchanged.
[reveal: v-192]
[pause: 0.45]
C: Then post seventy-two in the ledger.
[reveal: v-193]
[pause: 0.45]
C: A record with no reference falls back to card,
[reveal: v-194]
[pause: 0.45]
C: merchant, amount within twenty percent, and seven days.
[reveal: v-195]
[pause: 0.45]
C: And a record with no match at all still posts, and goes to a review queue.
[pause: 1.1]

[slide: v-196]
[pause: 1.3]
C: Flow four, changing rules.
[reveal: v-197]
[pause: 0.45]
C: One: an analyst writes rule version fifteen in the rule service, which backtests it on the decision archive.
[reveal: v-198]
[pause: 0.45]
C: Two: the rule service pushes a new rule-set version to every decision service, in shadow.
[reveal: v-199]
[pause: 0.45]
C: Three: every decision records the rule-set version, and what the shadow rule would have done.
C: Four: the event log feeds the alarms on decline rate by merchant type.
[reveal: v-200]
[pause: 0.45]
C: Then a slice, then enforcement.
C: And rollback is re-pointing to the previous version.
[pause: 1.1]

[slide: v-201]
[pause: 1.3]
C: The C-four context view.
[reveal: v-202]
[pause: 0.45]
C: The cardholder pays a merchant, whose acquirer sends the purchase through the card network and the processor to us.
[reveal: v-203]
[pause: 0.45]
C: We send the cardholder alerts.
[reveal: v-204]
[pause: 0.45]
C: Fraud operations write rules and work cases.
[reveal: v-205]
[pause: 0.45]
C: And we send postings to the core banking ledger.
[reveal: v-206]
[pause: 0.45]
C: Nothing else sits on the authorisation path.
[pause: 1.1]

[slide: v-207]
[pause: 1.3]
C: The container view.
[reveal: v-208]
[pause: 0.45]
C: The network and processor on the left.
[reveal: v-209]
[pause: 0.45]
C: The gateway,
[reveal: v-210]
[pause: 0.45]
C: the decision service and the authorisation store in a row:
[reveal: v-211]
[pause: 0.45]
C: that is the whole authorisation path.
[reveal: v-212]
[pause: 0.45]
C: Above it,
[reveal: v-213]
[pause: 0.45]
C: what the decision reads: the model scorer, the feature store, the rule service.
[reveal: v-214]
[pause: 0.45]
C: Below it,
[reveal: v-215]
[pause: 0.45]
C: what happens after the answer:
[reveal: v-216]
[pause: 0.45]
C: the clearing matcher, the event log, alerts and cases.
[reveal: v-217]
[pause: 0.45]
C: That layout is the thesis, drawn.
[pause: 1.1]

[slide: v-218]
[pause: 1.0]
C: Technology, mechanism first.
C: The authorisation store is an in-memory-backed store partitioned by account, with a durable replicated log.
C: Not the core ledger, whose tail would be ours, and not a cache over it, because a cache cannot reserve: two readers of one cached balance both approve.
[reveal: v-219]
[pause: 0.45]
C: Rules run in process, as data, rather than code or a remote engine.
[reveal: v-220]
[pause: 0.45]
C: The model sits behind a cut-off.
[reveal: v-221]
[pause: 0.45]
C: Counters are one key per card per minute in memory, not from the stream.
[reveal: v-222]
[pause: 0.45]
C: And events leave through an outbox in the same transaction as the hold, because publishing after the write loses the event on a crash.
[pause: 1.0]

[pause: 1.4]

## 5.1 Components and technologies

[slide: v-223]
[pause: 1.2]
C: Now one level down. Every container, with the technology I would run it on, and for each choice, the alternatives I rejected and why.
[pause: 1.8]

[slide: v-224]
[pause: 1.3]
C: The container view again, with one change: the type line now names the technology. I will walk it once, then defend each choice on its own slide.
[reveal: v-225]
[pause: 0.45]
C: The path between them..
[reveal: v-226]
[pause: 0.45]
C: The path between them..
[reveal: v-227]
[pause: 0.45]
C: Auth gateway is Go, mutual TLS.
[reveal: v-228]
[pause: 0.45]
C: Clearing matcher is Spark batch.
[reveal: v-229]
[pause: 0.45]
C: Model scorer is gRPC, 60 ms cut-off.
[reveal: v-230]
[pause: 0.45]
C: Decision service is Go, stateless.
[reveal: v-231]
[pause: 0.45]
C: Event log is Kafka via outbox.
[reveal: v-232]
[pause: 0.45]
C: Feature store is Redis Cluster.
[reveal: v-233]
[pause: 0.45]
C: Auth store is PostgreSQL, by account.
[reveal: v-234]
[pause: 0.45]
C: Alerts and cases is Kafka consumers.
[reveal: v-235]
[pause: 0.45]
C: Rule service is Go, versioned data.
[pause: 1.1]

[slide: v-236]
[pause: 1.0]
C: Accounts are partitioned by account ID, so the balance, the holds and the network message a decision touches live together. A decision is one conditional update: a version column on the account makes the second of two simultaneous swipes fail and re-read. The network's reference is a unique key, written with the hold. The hot set fits in memory, and each primary has a synchronous standby in another zone.
[reveal: v-237]
[pause: 0.45]
C: Why PostgreSQL 16, partitioned by account, hot set in memory, synchronous standby: The decision must reserve atomically, in milliseconds, twelve thousand times a second. Everything it writes belongs to one account, so one partition and one transaction hold it.
[reveal: v-238]
[pause: 0.45]
C: Rejected: Holds in the core ledger. Correct, but its batch windows and tail latency would sit on the authorisation path.
[reveal: v-239]
[pause: 0.45]
C: A cache in front of the ledger. A cache cannot reserve: two readers of the same cached balance both approve.
[reveal: v-240]
[pause: 0.45]
C: An event log as the source of truth. The synchronous check needs the current balance, not a replay.
[pause: 1.0]

[slide: v-241]
[pause: 1.0]
C: The rule service holds versions of the rule set. Each decision server fetches a new version, compiles it once and swaps it in atomically. Every evaluation has a time and memory limit, and the version number is written on the decision. A new rule goes through a backtest on yesterday's traffic, then a shadow period where it decides but does not act, then a slice of live traffic.
[reveal: v-242]
[pause: 0.45]
C: Why A sandboxed expression language in the decision service, a rule set per version: Rules are cheap to evaluate and must change without a deploy. A remote rules service would add a hop and a failure mode to every decision.
[reveal: v-243]
[pause: 0.45]
C: Rejected: Rules as code. A deploy per change, at two in the morning.
[reveal: v-244]
[pause: 0.45]
C: A remote rules engine. A network hop and a dependency inside a hundred-millisecond budget.
[pause: 1.0]

[slide: v-245]
[pause: 1.0]
C: The decision service sends the request asynchronously and waits at most sixty milliseconds. A late score is logged and ignored. A fail-policy table decides without it, by merchant category and amount. Model releases are independent of decision releases. A small model can be embedded, with the same cut-off around it.
[reveal: v-246]
[pause: 0.45]
C: Why A separate gRPC service, a 60 millisecond cut-off, a fail table: The model is the only step that can be slow. Its slowness must not become ours.
[reveal: v-247]
[pause: 0.45]
C: Rejected: Embedding a large model in the decision service. Model releases become decision releases, and a heavy model competes for the same CPU.
[reveal: v-248]
[pause: 0.45]
C: Waiting for the model. The slowest score sets every customer's wait.
[pause: 1.0]

[slide: v-249]
[pause: 1.0]
C: One key per card per minute. A decision increments the current bucket and reads the previous nine in one pipelined round trip, and keys expire on their own. Slower pattern features come from the stream processor and are written back in batches.
[reveal: v-250]
[pause: 0.45]
C: Why Redis Cluster, one key per card per minute, one pipelined round trip: Velocity rules need the count of the last few minutes, exact, inside the request path.
[reveal: v-251]
[pause: 0.45]
C: Rejected: Counters from a stream processor. Seconds late: the burst is over before the count lands.
[reveal: v-252]
[pause: 0.45]
C: A SQL count over recent transactions. A millisecond becomes tens.
[pause: 1.0]

[slide: v-253]
[pause: 1.0]
C: The decision is written to an outbox row in the same transaction as the hold. A relay publishes it to Kafka, keyed by account, at least once. The archive, the alert service and case management are separate consumer groups, each deduplicating by decision ID.
[reveal: v-254]
[pause: 0.45]
C: Why Outbox row in the same transaction, Kafka partitioned by account: Consumers must not slow the answer, and none may miss a decision.
[reveal: v-255]
[pause: 0.45]
C: Rejected: Publishing after the commit. A crash between the two loses the decision for the audit trail.
[reveal: v-256]
[pause: 0.45]
C: Synchronous calls to each consumer. Every consumer's slowness joins the answer.
[pause: 1.0]

[slide: v-257]
[pause: 1.0]
C: The gateway terminates mutual TLS from the processor, maps each message to our request and keys it by the network's reference. A repeat of an authorisation is answered from the stored decision. An advice, which is the network telling us a fact, is recorded once even when it would overdraw the account.
[reveal: v-258]
[pause: 0.45]
C: Why Go service, mutual TLS to the processor, message mapping, deduplication: The card network's messages are not our domain model. One place maps them and takes care of repeats and order.
[reveal: v-259]
[pause: 0.45]
C: Rejected: The processor's format through our services. Every service would need to know the network's quirks.
[reveal: v-260]
[pause: 0.45]
C: Treating each message as new. A repeated message double-holds the balance.
[pause: 1.0]

[slide: v-261]
[pause: 1.0]
C: The matcher reads the clearing file and matches each line to its hold by the network's reference. A match posts the final amount to the core ledger and releases the difference, which handles the tip. An unmatched hold expires after its lifetime. An unmatched clearing line becomes a break with an owner.
[reveal: v-262]
[pause: 0.45]
C: Why Spark batch over clearing files, matching by network reference: Money moves at clearing, not at authorisation. The files arrive daily and the join is a batch job.
[reveal: v-263]
[pause: 0.45]
C: Rejected: Debiting at authorisation. The final amount is not known: a tip or a fuel pre-authorisation differs.
[reveal: v-264]
[pause: 0.45]
C: Matching on amount and time. Two equal amounts at a cafe in a minute are ambiguous.
[pause: 1.0]

[slide: v-265]
[pause: 1.0]
C: The stack on one slide, as I would leave it on the whiteboard.
C: Auth store: PostgreSQL, by account.
C: Not Core ledger; cache.
C: One conditional write per decision.
[reveal: v-266]
[pause: 0.45]
C: Rules: In process, versioned data.
C: Not Rules as code; remote engine.
C: Change without a deploy.
[reveal: v-267]
[pause: 0.45]
C: Model scorer: Separate service, 60 ms.
C: Not Embedded; wait.
C: Slow model, fast answer.
[reveal: v-268]
[pause: 0.45]
C: Feature store: Redis, per-minute keys.
C: Not Stream counters; SQL count.
C: Exact, in one round trip.
[reveal: v-269]
[pause: 0.45]
C: Event log: Outbox into Kafka.
C: Not Publish after; sync calls.
C: None can slow the answer.
[reveal: v-270]
[pause: 0.45]
C: Auth gateway: Go, mutual TLS, mapping.
C: Not Raw format; treat as new.
C: Repeats and order handled once.
[reveal: v-271]
[pause: 0.45]
C: Clearing matcher: Spark batch.
C: Not Debit at auth.
C: Hold now, money at clearing.
[reveal: v-272]
[pause: 0.45]
N: Naming a product is not the signal.
N: Naming the property that rules out its rival is.
N: Interviewers go one level down on whichever box you name, so name only what you can defend.
[pause: 1.0]

[slide: v-273]
[pause: 0.6]
N: Before the challenges, swap seats. You are the interviewer now. Of everything on the last slide, which box would you push on, and what is the one question you would ask? Pause the video and pick one.
[pause: 3.0]

[slide: v-274]
[pause: 1.0]
N: Here is where interviewers usually go.
I: Two swipes on one card hit two decision servers in the same millisecond.
I: How many approvals?
[pause: 1.2]
N: At most what the balance covers.
N: Both write to the account's partition, and the conditional update on the version lets only one succeed; the other re-reads and decides again.
[reveal: v-275]
[pause: 0.45]
N: The trap is read, decide, then write.
I: A new rule blocks ten percent of good transactions in the first minute.
I: What happens?
[pause: 1.2]
N: The slice stage caps it to a small share of traffic, a gate sees the decline rate move and the rollout halts.
N: The version is switched back.
[reveal: v-276]
[pause: 0.45]
N: Backtest and shadow come first so it rarely gets here.
I: The model is slow tonight.
I: What does a cardholder at a till experience?
[pause: 1.2]
N: Nothing worse: at sixty milliseconds the decision proceeds with the fail table and the rules.
[reveal: v-277]
[pause: 0.45]
N: Approvals continue, with slightly looser or tighter policy by category.
I: A card is used four times in ten seconds, at four merchants.
I: Which counter sees it, and when?
[pause: 1.2]
N: The inline per-minute counter, in the same decision: the fourth swipe reads the count of the previous three.
[reveal: v-278]
[pause: 0.45]
N: A stream aggregate would be seconds late.
N: If you picked a box that is not on this list, good.
N: Write its probe down and answer it before you watch on.
[pause: 1.2]

[pause: 1.4]

## 6 Bridge

[slide: v-279]
[pause: 1.2]
V: It works. Where does it break first?
[pause: 1.8]

[slide: v-280]
[pause: 1.3]
C: The baseline with its attack points.
C: The authorisation store: the tip, two swipes on one balance, and messages twice or out of order.
C: The model scorer: slow tonight.
C: The feature store: a burst seconds apart.
[reveal: v-281]
[pause: 0.45]
C: The rule service: a new attack at two in the morning.
C: The gateway: twenty minutes down, and the network standing in.
C: And the alerts: declines doubled, with green dashboards.
C: I'll take them in an order where each fix creates the next question.
[pause: 1.1]

[pause: 1.4]

## 7 Challenges

[slide: v-282]
[pause: 1.2]
C: Eight challenges, each the same way: the question, the naive answer, a case with numbers, where it breaks, the fix, why it works, then the interviewer pushes on the fix itself, and what I'd say in the room.
[pause: 1.8]

[pause: 1.4]

## 7.1 Challenge 1: The tip

[slide: v-283]
[pause: 1.2]
N: Challenge one. A restaurant bill is authorised at one amount and clears at another: where is the money in between?
[pause: 1.8]

[slide: v-284]
[pause: 0.6]
I: A sixty-dollar restaurant authorisation clears three days later at seventy-two, with the tip. Walk me through the money.
[pause: 2.0]

[slide: v-285]
[pause: 1.3]
C: The naive answer:
[reveal: v-286]
[pause: 0.45]
C: approve and debit sixty dollars;
[reveal: v-287]
[pause: 0.45]
C: clearing is a formality.
[reveal: v-288]
[pause: 0.45]
C: Look at the red decision service writing straight to the ledger.
[reveal: v-289]
[pause: 0.45]
C: It just moved money that has not moved.
[pause: 1.1]

[slide: v-290]
[pause: 1.0]
C: The trace.
C: Monday, quarter past eight: authorise sixty dollars, and debit it: five hundred becomes four hundred and forty.
[reveal: v-291]
[pause: 0.45]
C: Two minutes later, the waiter adds a twelve dollar tip.
[reveal: v-292]
[pause: 0.45]
C: Thursday morning, clearing says seventy-two.
[reveal: v-293]
[pause: 0.45]
C: Either that is a second debit, and the customer has paid a hundred and thirty-two, or it is ignored, and the restaurant is twelve dollars short with nobody owning it.
C: And this is everywhere amounts differ.
[reveal: v-294]
[pause: 0.45]
C: A hotel pre-authorises three hundred and checks out at one eighty.
C: A fuel pump authorises one dollar and clears at sixty-four.
C: A split shipment clears twice.
[pause: 1.0]

[slide: v-295]
[pause: 1.3]
C: The fix, outlined green.
[reveal: v-296]
[pause: 0.45]
C: An approval inserts a hold of sixty dollars in the authorisation store.
C: The incremental raises the same hold to seventy-two.
[reveal: v-297]
[pause: 0.45]
C: On Thursday, the clearing matcher finds the hold by the network reference and, in one write, moves seventy-two dollars from the hold to the posted balance.
C: Then it posts seventy-two in the ledger.
[reveal: v-298]
[pause: 0.45]
C: Rejected: Debiting the balance at authorisation.
C: The final amount differs by the tip; a hold is placed and clearing moves the money.
[pause: 1.1]

[slide: v-299]
[pause: 1.3]
C: Line by line. Monday: authorise sixty, hold sixty. Posted five hundred, available four hundred and forty. The tip: the hold becomes seventy-two, available four hundred and twenty-eight. Thursday: clearing seventy-two, matched by reference. Posted becomes four hundred and twenty-eight, the hold is released, and available stays four hundred and twenty-eight.
C: Available moved at the till. Posted moved on Thursday, when the money really moved. And if Thursday never comes, the hold expires, after about seven days for most merchants and thirty for hotels and car hire.
[pause: 1.1]

[slide: v-300]
[pause: 1.0]
C: How long should a hold live?
C: It depends on the merchant.
C: A restaurant adds a tip within a day or two.
[reveal: v-301]
[pause: 0.45]
C: A fuel pump authorises a small amount and clears the real fill.
[reveal: v-302]
[pause: 0.45]
C: A hotel or a car hire clears weeks later.
[reveal: v-303]
[pause: 0.45]
C: A split shipment clears more than once.
C: So the lifetime comes from the merchant category, and these numbers are illustrative.
C: The asymmetry decides the direction.
[reveal: v-304]
[pause: 0.45]
C: Release too early, and the customer spends money that is about to leave.
C: Release too late, and they see a little less for a few days.
C: Err late.
[pause: 1.0]

[slide: v-305]
[pause: 0.6]
I: The clearing record has no matching authorisation. Or it arrives after the hold expired.
[pause: 2.0]

[slide: v-306]
[pause: 0.6]
C: Match by reference first.
C: With no reference, fall back to the card, the merchant, an amount within twenty percent, and a seven-day window.
[reveal: v-307]
[pause: 0.45]
C: And if nothing matches, the record still posts.
C: The network has already paid the merchant from our settlement account, so the file is the financial truth.
C: It goes to a review queue.
[reveal: v-308]
[pause: 0.45]
C: A clearing that arrives after its hold expired posts too, and may take the account below zero.
C: That is a modelled state, in challenge seven.
[reveal: v-309]
[pause: 0.45]
C: And expiry waits for the day's file, so a hold is never released an hour before its own clearing arrives.
[pause: 0.8]

[slide: v-310]
[pause: 0.7]
V: If asked, I'd say: approval is a hold, not a debit. Available is posted minus holds, and clearing moves the real amount from hold to posted. Holds that never clear expire, and late clearing still posts.
[pause: 1.0]
N: That fix creates the next question. A hold is a read and a write, and two can race.
[pause: 1.6]

[pause: 1.4]

## 7.2 Challenge 2: Two swipes, one balance

[slide: v-311]
[pause: 1.2]
N: Challenge two. Two authorisations for one account arrive at the same moment, and the money covers one: who decides?
[pause: 1.8]

[slide: v-312]
[pause: 0.6]
I: Two authorisations for one account arrive two milliseconds apart. The balance covers one of them. What happens?
[pause: 2.0]

[slide: v-313]
[pause: 1.3]
C: The naive answer:
[reveal: v-314]
[pause: 0.45]
C: read the available balance,
[reveal: v-315]
[pause: 0.45]
C: check it,
[reveal: v-316]
[pause: 0.45]
C: insert the hold.
[reveal: v-317]
[pause: 0.45]
C: The red authorisation store is read by two decisions before either writes.
[pause: 1.1]

[slide: v-318]
[pause: 1.0]
C: The trace.
C: Available is one hundred dollars.
C: At noon exactly, a fuel pump for eighty reads one hundred.
[reveal: v-319]
[pause: 0.45]
C: Two milliseconds later, an online order for sixty reads one hundred.
[reveal: v-320]
[pause: 0.45]
C: Eighty fits: hold.
C: Sixty fits: hold.
[reveal: v-321]
[pause: 0.45]
C: Available is minus forty, and we approved both.
C: A joint account does this.
[reveal: v-322]
[pause: 0.45]
C: So does a phone wallet next to a physical card, or a subscription renewing while the customer pays at a till.
C: Rare per account; daily across eight million.
[pause: 1.0]

[slide: v-323]
[pause: 1.3]
C: The fix is one conditional write in the partition that owns the account.
[reveal: v-324]
[pause: 0.45]
C: If the holds plus this amount still fit within posted,
[reveal: v-325]
[pause: 0.45]
C: and the account's version is the one I read, then insert the hold, record the message, add to the holds total and bump the version, all at once.
[reveal: v-326]
[pause: 0.45]
C: Otherwise nothing is written, and the decision reads again.
[reveal: v-327]
[pause: 0.45]
C: Rejected: Reading the balance, then writing it.
[reveal: v-328]
[pause: 0.45]
C: Two readers both approve; a conditional write in one partition decides.
[pause: 1.1]

[slide: v-329]
[pause: 1.3]
C: As a sequence.
C: Both reserves carry version forty-one.
[reveal: v-330]
[pause: 0.45]
C: The eighty dollar one commits first: hold placed, version forty-two.
[reveal: v-331]
[pause: 0.45]
C: The sixty dollar one finds version forty-two and is refused.
[reveal: v-332]
[pause: 0.45]
C: It re-reads: available twenty dollars, and sixty is more than twenty.
[reveal: v-333]
[pause: 0.45]
C: Decline, insufficient funds.
[reveal: v-334]
[pause: 0.45]
C: Exactly one place answered: is there enough?
[pause: 1.1]

[slide: v-335]
[pause: 1.0]
C: In code.
C: Read the account.
C: If the holds plus the amount exceed posted, decline.
C: Otherwise, one transaction in the account's partition: on condition that the version is unchanged, put the hold, put the message, and update the total and the version.
C: If someone else won, read again.
C: Why not a distributed lock?
C: It gives the same safety, with a lock service on the hot path and a lease to expire when a server dies holding it.
C: The conditional write is the lock and the write in one step.
[pause: 1.0]

[slide: v-336]
[pause: 0.6]
I: A business account has two thousand fleet cards on one balance, and on the busiest day they all buy fuel at seven in the morning.
[pause: 2.0]

[slide: v-337]
[pause: 1.3]
C: The arithmetic first. Two thousand cards, each one authorisation in ten minutes, is three point three a second on one key. One partition handles that easily, with a conflict now and then. So the honest first answer is: nothing changes.
C: If it grows to hundreds a second, say a marketplace with virtual cards, carve sub-limits per card from the account. The account reserves budget to each card in blocks, refilled in the background, and most authorisations touch only the card's slice. The limit: a slice can run dry while the account still has money, so refill at half-used and fall back to the account-level reserve before declining.
[pause: 1.1]

[slide: v-338]
[pause: 0.7]
V: If asked, I'd say: check-and-reserve is one conditional write in the account's partition, so two swipes can't spend the same money. It costs nothing, and a big shared account gets sub-limits per card.
[pause: 1.0]
N: That fix writes the message with the hold. The next question is what a message is, when it comes twice.
[pause: 1.6]

[pause: 1.4]

## 7.3 Challenge 3: The same message twice, and in the wrong order

[slide: v-339]
[pause: 1.2]
N: Challenge three. The network retries, and a reversal overtakes its original: how does each message take effect exactly once?
[pause: 1.8]

[slide: v-340]
[pause: 0.6]
I: The network retries an authorisation we already approved. And a reversal arrives before the authorisation it reverses. What happens?
[pause: 2.0]

[slide: v-341]
[pause: 1.3]
C: The naive answer:
[reveal: v-342]
[pause: 0.45]
C: process messages as they arrive,
[reveal: v-343]
[pause: 0.45]
C: and a retry is a new request.
[reveal: v-344]
[pause: 0.45]
C: The red gateway and store treat every arrival as new.
[pause: 1.1]

[slide: v-345]
[pause: 1.0]
C: Two traces.
[reveal: v-346]
[pause: 0.45]
C: At half past six, R-seventy-seven-thirty-one for forty-five dollars is approved and its hold placed, but the answer is lost on the link.
[reveal: v-347]
[pause: 0.45]
C: Almost two seconds later the network retries it, and the naive system places a second hold: available is down ninety.
[reveal: v-348]
[pause: 0.45]
C: Then at two minutes past seven, a reversal of R-eighty-eight-forty arrives first: the merchant cancelled at once.
C: Nothing to reverse, so it is dropped.
[reveal: v-349]
[pause: 0.45]
C: Sixty milliseconds later the authorisation itself arrives and is approved: a hold for a purchase that was cancelled, for seven days.
[pause: 1.0]

[slide: v-350]
[pause: 1.3]
C: The fix.
[reveal: v-351]
[pause: 0.45]
C: The message table is keyed by the network's reference.
[reveal: v-352]
[pause: 0.45]
C: Before acting, the decision looks the reference up.
[reveal: v-353]
[pause: 0.45]
C: A retry gets the stored answer.
C: A reversal whose original has not arrived is kept as a tombstone.
[reveal: v-354]
[pause: 0.45]
C: And the message record is written in the same transaction as the hold, so no crash can leave one without the other.
[reveal: v-355]
[pause: 0.45]
C: Rejected: Treating every network message as new.
C: A repeat double-holds the balance; key by the network's reference.
[pause: 1.1]

[slide: v-356]
[pause: 1.3]
C: As a sequence.
[reveal: v-357]
[pause: 0.45]
C: The reversal of R-eighty-eight-forty arrives;
[reveal: v-358]
[pause: 0.45]
C: the message table has nothing,
[reveal: v-359]
[pause: 0.45]
C: so we store a tombstone and acknowledge.
[reveal: v-360]
[pause: 0.45]
C: Sixty milliseconds later the authorisation arrives.
[reveal: v-361]
[pause: 0.45]
C: Reserve?
[reveal: v-362]
[pause: 0.45]
C: The store says: already reversed, no hold.
[reveal: v-363]
[pause: 0.45]
C: We answer as the network expects, and nothing is held.
[reveal: v-364]
[pause: 0.45]
C: And when the network retries it, it gets the stored answer again.
[pause: 1.1]

[slide: v-365]
[pause: 0.6]
C: Three keys that look right and are not.
C: Arrival time: a retry arrives later and a reversal earlier, so time is exactly what varies.
[reveal: v-366]
[pause: 0.45]
C: A hash of the amount and the merchant: two genuine coffees five minutes apart look identical, and one would be swallowed.
[reveal: v-367]
[pause: 0.45]
C: And our own generated I-D: the network does not know it, so its retry cannot carry it.
[reveal: v-368]
[pause: 0.45]
C: The only key both sides share is the network's reference.
[pause: 0.8]

[slide: v-369]
[pause: 0.6]
I: The partition fails over mid-write. Or the message table is purged, and a retry arrives a day later.
[pause: 2.0]

[slide: v-370]
[pause: 0.6]
C: The transaction commits on a quorum of replicas before the answer leaves, so a new primary has both writes or neither.
[reveal: v-371]
[pause: 0.45]
C: Message records are kept for longer than the network's retry and reversal windows, which are days.
C: Twenty million a day, a hundred bytes each, for thirty days, is about sixty gigabytes.
[reveal: v-372]
[pause: 0.45]
C: Cheap.
C: And past that window, clearing is the backstop: a hold that should not exist expires, and a clearing that should exist posts.
[pause: 0.8]

[slide: v-373]
[pause: 0.7]
V: If asked, I'd say: every message is keyed by the network's reference, and recorded in the same atomic step as the hold. A retry gets the stored answer, and an early reversal waits as a tombstone.
[pause: 1.0]
N: The money is now correct. The next question is about time: what if the answer itself is late?
[pause: 1.6]

[pause: 1.4]

## 7.4 Challenge 4: The model is slow tonight

[slide: v-374]
[pause: 1.2]
N: Challenge four. The fraud model's tail jumps to almost two seconds: do we wait for it, ignore it, or something better?
[pause: 1.8]

[slide: v-375]
[pause: 0.6]
I: Your fraud model is at one point eight seconds, at the ninety-ninth percentile, tonight. What does the authorisation path do?
[pause: 2.0]

[slide: v-376]
[pause: 1.3]
C: Two naive answers.
[reveal: v-377]
[pause: 0.45]
C: Wait for it,
[reveal: v-378]
[pause: 0.45]
C: because fraud matters more than latency.
[reveal: v-379]
[pause: 0.45]
C: Or fail open.
[reveal: v-380]
[pause: 0.45]
C: The red model scorer sits on the critical path with no limit of its own.
[pause: 1.1]

[slide: v-381]
[pause: 1.0]
C: The trace.
C: At eight in the evening, a model release doubles its feature fetches, and its tail goes to one point eight seconds.
[reveal: v-382]
[pause: 0.45]
C: If we wait, by one minute past eight, thirty percent of our answers pass two seconds.
C: The network stands in for four hundred and fifty authorisations a second, with limits we set months ago and no score at all.
[reveal: v-383]
[pause: 0.45]
C: If we fail open, every decision is unscored: fifteen hundred a second, ninety thousand a minute, and a fraud ring probing with small purchases notices within minutes.
[reveal: v-384]
[pause: 0.45]
C: These numbers are a scenario, illustrative.
[pause: 1.0]

[slide: v-385]
[pause: 1.3]
C: The fix.
[reveal: v-386]
[pause: 0.45]
C: Rules always run, in process, in about ten milliseconds.
[reveal: v-387]
[pause: 0.45]
C: The model gets a sixty millisecond slice, and at sixty the decision proceeds without it.
[reveal: v-388]
[pause: 0.45]
C: What without it means is not an if-statement.
C: It is a table, agreed in advance, with an hourly exposure cap on every cell.
[reveal: v-389]
[pause: 0.45]
C: Rejected: Waiting for the model.
[reveal: v-390]
[pause: 0.45]
C: Its slowness becomes ours; a budget slice and a fail table cap it.
[pause: 1.1]

[slide: v-391]
[pause: 1.0]
C: The table.
C: Model late, small amount at a low-risk merchant: decide on rules alone.
C: Large amount or a risky merchant type: rules with stricter limits.
[reveal: v-392]
[pause: 0.45]
C: Counters missing: conservative limits for card-not-present.
[reveal: v-393]
[pause: 0.45]
C: Rules engine failing: approve small amounts within stand-in-like limits, decline or step up the rest.
[reveal: v-394]
[pause: 0.45]
C: And if we miss the deadline entirely, the network stands in.
[reveal: v-395]
[pause: 0.45]
C: Every cell has an hourly exposure cap, and the decision service counts degraded approvals against it as they happen.
[pause: 1.0]

[slide: v-396]
[pause: 1.3]
C: As a sequence.
[reveal: v-397]
[pause: 0.45]
C: Ask the model, with a cut-off of sixty.
[reveal: v-398]
[pause: 0.45]
C: Rules are done at eighteen milliseconds.
[reveal: v-399]
[pause: 0.45]
C: At sixty, no score: proceed.
[reveal: v-400]
[pause: 0.45]
C: The table row: model late, sixty dollars, restaurant.
[reveal: v-401]
[pause: 0.45]
C: Rules only, the cap is fifty thousand dollars an hour, seven thousand two hundred used.
[reveal: v-402]
[pause: 0.45]
C: Approve, flagged degraded, counted.
C: And when the score arrives at one point eight seconds, it is logged and ignored.
[pause: 1.1]

[slide: v-403]
[pause: 0.6]
C: Someone usually suggests hedging: send the model call to two scorers and take the first answer.
C: It trims a random tail, one slow machine among many.
[reveal: v-404]
[pause: 0.45]
C: Tonight the slowness is the model itself, so every copy is slow, and hedging doubles its load exactly when it is struggling.
[reveal: v-405]
[pause: 0.45]
C: A cut-off bounds our latency whatever the cause.
[pause: 0.8]

[slide: v-406]
[pause: 0.6]
I: It lasts all evening, and the cap runs out. And who decided those numbers?
[pause: 2.0]

[slide: v-407]
[pause: 0.6]
C: When a cell's cap is used up, that cell tightens: first a step-up, asking the cardholder to confirm in the app, then lower limits, then decline.
C: And the first runbook step is rolling the model back by re-pointing its version.
C: Who decided?
C: Risk sets the limits in each cell from loss data.
[reveal: v-408]
[pause: 0.45]
C: Finance signs the cap.
[reveal: v-409]
[pause: 0.45]
C: Engineering makes each cell a setting, counts every degraded decision, and pages at half the cap.
[reveal: v-410]
[pause: 0.45]
C: At the manager bar, the point is that this conversation happens before the incident, not during it.
[pause: 0.8]

[slide: v-411]
[pause: 0.7]
V: If asked, I'd say: the model gets a fixed slice of the budget, and we never wait past it. When it's late, a table owned by risk and finance decides, under an hourly cap.
[pause: 1.0]
N: Features are the model's other input. The next question is how fresh they are.
[pause: 1.6]

[pause: 1.4]

## 7.5 Challenge 5: A burst, seconds apart

[slide: v-412]
[pause: 1.2]
N: Challenge five. A rule counts swipes in ten minutes: where does that count come from, and how old is it when we read it?
[pause: 1.8]

[slide: v-413]
[pause: 0.6]
I: Your rule is more than three swipes in ten minutes on one card. Where does that number come from, in time?
[pause: 2.0]

[slide: v-414]
[pause: 1.3]
C: The naive answer:
[reveal: v-415]
[pause: 0.45]
C: a stream processor counts swipes and writes them to a key-value store.
[reveal: v-416]
[pause: 0.45]
C: The red stream aggregator is correct,
[reveal: v-417]
[pause: 0.45]
C: and seconds late.
[pause: 1.1]

[slide: v-418]
[pause: 1.0]
C: The trace.
[reveal: v-419]
[pause: 0.45]
C: At twelve minutes past three in the morning, four card-not-present purchases of two hundred and forty dollars on one token, within eight seconds.
[reveal: v-420]
[pause: 0.45]
C: The stream's counter is five to eight seconds behind, so the four decisions read zero, one, one and two.
[reveal: v-421]
[pause: 0.45]
C: All approved.
[reveal: v-422]
[pause: 0.45]
C: Six seconds later the counter reads four, and nine hundred and sixty dollars are gone.
[reveal: v-423]
[pause: 0.45]
C: A burst on one stolen card is a script, seconds apart.
C: A stream is seconds behind.
C: That's what streams are.
[pause: 1.0]

[slide: v-424]
[pause: 1.3]
C: The fix.
[reveal: v-425]
[pause: 0.45]
C: Burst counters are updated inline, by the decision service itself: per card, one-minute buckets.
[reveal: v-426]
[pause: 0.45]
C: Before deciding, increment this minute and read the nine before it, in one pipelined round trip, about a millisecond.
[reveal: v-427]
[pause: 0.45]
C: The counter now reads one, two, three, four, and the fourth swipe is declined.
[reveal: v-428]
[pause: 0.45]
C: Rejected: Burst counters from a stream processor.
[reveal: v-429]
[pause: 0.45]
C: They land seconds late, after the burst is over.
[pause: 1.1]

[slide: v-430]
[pause: 1.3]
C: Two kinds of features. Inline, on the request path: swipes on this card in ten minutes, card-not-present spend in the last hour, declines in the last hour. From the stream, seconds late, which is fine for them: distinct merchants for this card today, a merchant's decline rate in the last hour, a device seen on other cards in thirty days. The decision reads both in the same call.
[pause: 1.1]

[slide: v-431]
[pause: 1.0]
C: In code.
C: One key per card per minute, with an expiry of eleven minutes so the buckets clean themselves up.
C: In one pipelined round trip: increment this minute, read the nine before, and sum.
C: Two details.
C: The swipe is counted before the decision, so declined attempts count too, and a script that keeps trying after a decline is the strongest signal there is.
C: And every feature value goes into the decision record, so the model is trained on exactly what it saw, not on values recomputed later by a different pipeline.
[pause: 1.0]

[slide: v-432]
[pause: 0.6]
I: The counter store is slow, or down.
[pause: 2.0]

[slide: v-433]
[pause: 0.6]
C: It is already a row in the fail table: counters missing, so rules apply conservative limits for card-not-present, inside the cap.
C: Card-present purchases barely change.
[reveal: v-434]
[pause: 0.45]
C: And the store is partitioned by card with a replica.
C: Losing a partition loses at most ten minutes of buckets, which are rebuilt from the event log for the cards that transact next.
[pause: 0.8]

[slide: v-435]
[pause: 0.7]
V: If asked, I'd say: burst features are counted inline, in one round trip, because a stream lags behind a burst. Patterns come from the stream, and every value is logged with the decision.
[pause: 1.0]
N: A counter is only useful if a rule reads it. The next question is how a rule gets there, at two in the morning.
[pause: 1.6]

[pause: 1.4]

## 7.6 Challenge 6: A new attack at 2 a.m.

[slide: v-436]
[pause: 1.2]
N: Challenge six. An attack starts in the middle of the night: how fast can an analyst block it, and what stops them blocking everyone?
[pause: 1.8]

[slide: v-437]
[pause: 0.6]
I: A new attack appears at two in the morning. How fast can an analyst block it, and what stops them from blocking everyone?
[pause: 2.0]

[slide: v-438]
[pause: 1.3]
C: Two naive answers.
[reveal: v-439]
[pause: 0.45]
C: Add an if-statement and hotfix the decision service.
[reveal: v-440]
[pause: 0.45]
C: Or: shadow-test the rule to measure its false positives.
[reveal: v-441]
[pause: 0.45]
C: The red rule path is either a deploy,
[reveal: v-442]
[pause: 0.45]
C: or a live change with nothing in between.
[pause: 1.1]

[slide: v-443]
[pause: 1.0]
C: The trace.
C: Five past two: fraud operations see a pattern.
C: A one-dollar test charge, then four hundred at electronics merchants, on cards from one breach.
[reveal: v-444]
[pause: 0.45]
C: A hotfix goes through review, build and deploy, and is live at five to three: fifty minutes of losses.
[reveal: v-445]
[pause: 0.45]
C: The other way: at twenty past two an analyst pushes amount over three hundred at electronics, decline, straight to production.
[reveal: v-446]
[pause: 0.45]
C: A minute later, nine percent of all electronics purchases are declined, almost all of them good customers.
[pause: 1.0]

[slide: v-447]
[pause: 1.3]
C: The fix: rules are versioned data.
[reveal: v-448]
[pause: 0.45]
C: A rule is an expression in a small sandboxed language, with an owner and an expiry.
[reveal: v-449]
[pause: 0.45]
C: It goes through four stages, and every decision records the rule-set version it ran.
[reveal: v-450]
[pause: 0.45]
C: Rejected: Rules as code, deployed.
C: A deploy per change at two in the morning; versioned data swaps in atomically.
[pause: 1.1]

[slide: v-451]
[pause: 1.3]
C: The stages. Write the expression. Backtest it on ninety days of the decision archive, with known labels: how much of this ring it catches, how many good purchases it declines. Shadow: it runs on live traffic and logs what it would have done. A slice: enforce on five percent, with an alarm on the decline rate by merchant type. Then enforce everywhere, with a kill switch.
C: Rollback is re-pointing every decision service to the previous rule-set version: seconds, no deploy.
[pause: 1.1]

[slide: v-452]
[pause: 1.0]
C: A rule, as data. An identifier and a version. The condition: card-not-present, at electronics merchant categories, over three hundred dollars, and at least one small charge on the card in the last day. That last clause is what makes it narrow. An action, a mode, a slice, an expiry two weeks out, and an owner. The language has no loops and no input or output, and each evaluation has a time limit, so a bad rule cannot hang the decision.
[pause: 1.0]

[slide: v-453]
[pause: 0.6]
I: Shadow says the rule would decline four thousand transactions a day. How many were fraud?
[pause: 2.0]

[slide: v-454]
[pause: 0.6]
C: Shadow cannot say.
C: It shows how many it would decline, not which were fraud, because the labels, chargebacks and customer reports, arrive thirty to ninety days later.
C: And most declined good customers never complain at all; they use another card.
C: So the evidence comes from elsewhere.
[reveal: v-455]
[pause: 0.45]
C: Backtests on labelled history.
C: Fast proxies: the share of customers who reply it was me to a decline text, or who pass a step-up.
C: The slice with its alarm.
C: And the expiry, so an emergency rule is reviewed with real labels instead of living forever.
[pause: 0.8]

[slide: v-456]
[pause: 0.7]
V: If asked, I'd say: rules are versioned data: backtest, shadow, a small slice with an alarm, then enforce, with the version on every decision. Shadow can't measure false positives; labels arrive months later.
[pause: 1.0]
N: Everything so far assumed we were up to answer. The next question is what happens when we were not.
[pause: 1.6]

[pause: 1.4]

## 7.7 Challenge 7: We were down for twenty minutes

[slide: v-457]
[pause: 1.2]
N: Challenge seven. The network decided for us during an outage: what does the next morning look like, and what if the clearing file is bad too?
[pause: 1.8]

[slide: v-458]
[pause: 0.6]
I: You were down for twenty minutes at two in the morning. The network approved three hundred and sixty thousand transactions in stand-in. Walk me through the next morning.
[pause: 2.0]

[slide: v-459]
[pause: 1.3]
C: Two naive answers.
[reveal: v-460]
[pause: 0.45]
C: The network declined everything while we were down.
[reveal: v-461]
[pause: 0.45]
C: It didn't: it approved, within our limits.
[reveal: v-462]
[pause: 0.45]
C: Or: replay them and decline the ones we would not have approved.
[reveal: v-463]
[pause: 0.45]
C: Too late: the purchases happened.
C: The red path refuses advices that break a never-below-zero rule.
[pause: 1.1]

[slide: v-464]
[pause: 1.0]
C: The trace.
C: From two to twenty past, stand-in approves within our limits: say up to a hundred and fifty dollars a purchase, four hundred a day a card.
[reveal: v-465]
[pause: 0.45]
C: Twenty minutes, at three hundred a second, is three hundred and sixty thousand approvals.
C: At twenty-one minutes past, we are back, and the advices arrive.
[reveal: v-466]
[pause: 0.45]
C: Account A-nineteen had thirty-five dollars available, and stand-in approved sixty and eighty.
C: Available is minus one hundred and five.
[reveal: v-467]
[pause: 0.45]
C: A check that refuses any write below zero rejects both advices.
C: No holds.
[reveal: v-468]
[pause: 0.45]
C: On Thursday clearing posts both anyway, and our books disagree with the network's.
[pause: 1.0]

[slide: v-469]
[pause: 1.3]
C: The fix: the ledger absorbs the decisions we did not make.
[reveal: v-470]
[pause: 0.45]
C: Every advice is acknowledged and recorded once, by its network reference, as a hold, even when it takes the account below zero.
[reveal: v-471]
[pause: 0.45]
C: Over-limit is a modelled account state.
C: New authorisations on that account decline until it is back above zero, the customer is told, and collections take over if it persists.
[reveal: v-472]
[pause: 0.45]
C: Rejected: Dropping advices received while we were down.
C: The network already approved; every advice is recorded once, even if it overdraws.
[pause: 1.1]

[slide: v-473]
[pause: 1.3]
C: As a sequence.
[reveal: v-474]
[pause: 0.45]
C: Advice R-fifty-one-oh-two, eighty dollars, approved by stand-in.
C: Record it as a hold, even past available.
[reveal: v-475]
[pause: 0.45]
C: Account A-nineteen: available minus one hundred and five, state over-limit.
C: Acknowledge.
[reveal: v-476]
[pause: 0.45]
C: An event goes to the ledger.
C: And new authorisations on A-nineteen decline until it is paid back.
[reveal: v-477]
[pause: 0.45]
C: Then, in the morning, replay the three hundred and sixty thousand through our rules offline.
[reveal: v-478]
[pause: 0.45]
C: Not to reverse them.
[reveal: v-479]
[pause: 0.45]
C: To see which we would have declined, and to tune the stand-in limits with risk.
[pause: 1.1]

[slide: v-480]
[pause: 1.0]
C: The morning after, the replay.
C: Run the three hundred and sixty thousand through our rules and model offline, and ask which we would have declined.
[reveal: v-481]
[pause: 0.45]
C: Say two percent, an illustrative number.
C: How much of that was fraud, we only learn as labels arrive.
[reveal: v-482]
[pause: 0.45]
C: And then, with risk, decide whether the stand-in limits were too high or too low: fewer good customers declined during an outage, against more fraud let through.
[reveal: v-483]
[pause: 0.45]
C: The replay never reverses a purchase.
C: It is simply the only data that says whether last night's limits were right.
[pause: 1.0]

[slide: v-484]
[pause: 0.6]
I: And the next day's clearing file arrives six hours late, with three percent of its records duplicated.
[pause: 2.0]

[slide: v-485]
[pause: 0.6]
C: Ingest files idempotently: a checksum per file, so a resent file is recognised, and a unique I-D per record, so the three hundred thousand duplicates are no-ops.
[reveal: v-486]
[pause: 0.45]
C: Hold expiry waits for the day's file, so a file six hours late still finds its holds open.
[reveal: v-487]
[pause: 0.45]
C: The nine o'clock posting target slips, with a note to finance and support, not silently.
C: And every day after clearing, the authorisation store is reconciled with the ledger, account by account.
C: Any difference is a break with an owner.
[pause: 0.8]

[slide: v-488]
[pause: 0.7]
V: If asked, I'd say: stand-in decisions are facts, not requests. We record every advice once, even when it overdraws, and model over-limit as a state. Files are idempotent, and expiry waits for them.
[pause: 1.0]
N: Last question, and the one every challenge depends on: how would we know any of this was happening?
[pause: 1.6]

[pause: 1.4]

## 7.8 Challenge 8: Declines doubled in ten minutes

[slide: v-489]
[pause: 1.2]
N: Challenge eight. The decline rate doubles and every dashboard is green: how do we find out, and what do we do first?
[pause: 1.8]

[slide: v-490]
[pause: 0.6]
I: The decline rate doubled in ten minutes. Your dashboards are green. How do you know what is wrong, and what is on the runbook?
[pause: 2.0]

[slide: v-491]
[pause: 1.3]
C: The naive answer: C-P-U, error rate and latency.
[reveal: v-492]
[pause: 0.45]
C: Those watch boxes.
[reveal: v-493]
[pause: 0.45]
C: The red rule service and decision service are perfectly healthy, and wrong.
[pause: 1.1]

[slide: v-494]
[pause: 1.0]
C: The trace.
C: Twenty to eight: rule set two hundred and twelve is enforced, and a typo widens a merchant list to include groceries.
[reveal: v-495]
[pause: 0.45]
C: A minute later, grocery approvals fall from ninety-six percent to seventy-one.
C: No errors.
[reveal: v-496]
[pause: 0.45]
C: Latency ninety-two milliseconds.
C: At five to eight, the first complaints on social media.
[reveal: v-497]
[pause: 0.45]
C: At ten past, the first page, from support call volume.
C: Half an hour, and nothing failed.
[pause: 1.0]

[slide: v-498]
[pause: 1.3]
C: The fix: indicators on decisions, not machines.
C: Approval rate by merchant type and region, every minute, against the same hour last week, because card traffic is strongly weekly.
[reveal: v-499]
[pause: 0.45]
C: The stand-in count.
C: Degraded decisions against each cap.
[reveal: v-500]
[pause: 0.45]
C: And synthetic test cards in every region that authorise and reverse every minute, end to end.
C: This one pages at nineteen forty-two.
[reveal: v-501]
[pause: 0.45]
C: Rejected: Dashboards of CPU and memory.
C: The machines are fine while declines double; watch decisions by reason.
[pause: 1.1]

[slide: v-502]
[pause: 1.0]
C: Symptom pairs: two metrics, one cause.
C: Declines up with a rule-set change in the same minute: a rule, this trace.
[reveal: v-503]
[pause: 0.45]
C: Declines up at one merchant only: that merchant's terminal.
[reveal: v-504]
[pause: 0.45]
C: Stand-in up while our latency is flat: the link to the processor, not us.
[reveal: v-505]
[pause: 0.45]
C: Model cut-offs up with flat latency: the model, and the cut-off is doing its job.
[reveal: v-506]
[pause: 0.45]
C: And the pair that settles the argument: declines up with it-was-me replies up means false positives, roll back.
[reveal: v-507]
[pause: 0.45]
C: Declines up with it-was-me flat and step-ups failing means a real attack: keep the rule.
[pause: 1.0]

[slide: v-508]
[pause: 1.0]
C: The runbook.
C: First, rule-set and release changes in the last hour: the most common cause and the fastest to undo.
[reveal: v-509]
[pause: 0.45]
C: Second, re-point to the previous version, in seconds.
[reveal: v-510]
[pause: 0.45]
C: Third, compare by merchant type and region, to tell an attack from one broken terminal.
[reveal: v-511]
[pause: 0.45]
C: Fourth, the model and its features, because a stale feature looks like risk.
[reveal: v-512]
[pause: 0.45]
C: And fifth, tell support, because otherwise the complaints arrive before the alerts.
[pause: 1.0]

[slide: v-513]
[pause: 0.6]
I: It's real fraud this time. An attack, and the rule is right.
[pause: 2.0]

[slide: v-514]
[pause: 0.6]
C: Then the it-was-me rate and the step-up pass rate separate good customers from fraud within minutes.
C: If few declined customers say it was them, and few pass a step-up, the rule is right.
[reveal: v-515]
[pause: 0.45]
C: Keep it, tell support what customers will hear, and let the expiry bring it back for review.
[pause: 0.8]

[slide: v-516]
[pause: 0.7]
V: If asked, I'd say: I watch decisions, not boxes. Approval rate by merchant type against last week, and stand-in count. The runbook starts with what changed, the usual cause and the fastest to undo.
[pause: 1.6]

[pause: 1.4]

## 8 Build cost

[slide: v-517]
[pause: 1.2]
C: Build cost. This is the manager layer, marked aux: skip it in a pure Staff round, use it in a manager round.
[pause: 1.8]

[slide: v-518]
[pause: 1.0]
C: Four releases, starting by buying.
C: Version zero: the processor decides, with rules and stand-in limits we upload.
[reveal: v-519]
[pause: 0.45]
C: Three engineers, eight weeks, and fine for a launch.
C: Version one: our own decision service on the core ledger, four engineers, three months.
[reveal: v-520]
[pause: 0.45]
C: Version two: the authorisation store, rules as data, the model behind a cut-off and the clearing matcher, a team of six to eight for two quarters.
C: Version three: features, the fail table, advices, lifecycle tooling and reconciliation, two teams for two more quarters.
[pause: 1.0]

[slide: v-521]
[pause: 0.6]
C: Team seams.
C: The authorisation platform owns the gateway, the decision service and the store, and their latency.
[reveal: v-522]
[pause: 0.45]
C: The risk platform owns the rules engine, features and the shadow tooling.
C: Data science owns models.
[reveal: v-523]
[pause: 0.45]
C: Fraud operations own the content of the rules and customer contact.
C: Ledger and clearing own posting and reconciliation.
[reveal: v-524]
[pause: 0.45]
C: The contracts between them are three: the decision event schema, the rule-set format, and the fail-policy table.
[pause: 0.8]

[slide: v-525]
[pause: 0.6]
C: Buy against build.
C: We buy the processor and its card vault, and perhaps the model platform; the network's own risk score arrives as an input.
C: We build the decision path, holds and the clearing match, because they are the product.
C: Cost, illustrative.
[reveal: v-526]
[pause: 0.45]
C: The largest lines are per-transaction fees and fraud losses, eight basis points of volume.
C: Then the archive and model serving.
C: The fleet is small.
C: A basis point of fraud is worth more than all the servers, so the cost lever is the quality of the decision.
[pause: 0.8]

[slide: v-527]
[pause: 1.0]
C: Top risks.
C: A fail policy nobody signed: review the table and caps monthly.
[reveal: v-528]
[pause: 0.45]
C: The store and the ledger drifting: reconcile daily.
[reveal: v-529]
[pause: 0.45]
C: Emergency rules living forever: an expiry on every rule.
[reveal: v-530]
[pause: 0.45]
C: And card data creeping into scope: tokens only, enforced at the gateway.
[pause: 1.0]

[pause: 1.4]

## 9 Recap

[slide: v-531]
[pause: 1.2]
C: To close: one picture, one sentence per path, the mistakes to avoid, and the thesis.
[pause: 1.8]

[slide: v-532]
[pause: 1.3]
C: The final picture.
[reveal: v-533]
[pause: 0.45]
C: Across the middle:
[reveal: v-534]
[pause: 0.45]
C: the network,
[reveal: v-535]
[pause: 0.45]
C: the gateway,
[reveal: v-536]
[pause: 0.45]
C: the decision service with rules in process,
[reveal: v-537]
[pause: 0.45]
C: and the authorisation store with its one atomic reserve.
[reveal: v-538]
[pause: 0.45]
C: Above:
[reveal: v-539]
[pause: 0.45]
C: the model behind a cut-off,
[reveal: v-540]
[pause: 0.45]
C: the feature store with inline counters,
[reveal: v-541]
[pause: 0.45]
C: the stream aggregator, and the rule service.
[reveal: v-542]
[pause: 0.45]
C: Below:
[reveal: v-543]
[pause: 0.45]
C: the event log,
[reveal: v-544]
[pause: 0.45]
C: alerts and the archive,
[reveal: v-545]
[pause: 0.45]
C: the clearing matcher feeding the ledger, and probes with test cards.
[pause: 1.1]

[slide: v-546]
[pause: 1.0]
C: Four paths, one sentence each.
C: Authorise: counters, rules and the model under a budget, one atomic reserve, an answer in time.
[reveal: v-547]
[pause: 0.45]
C: Reverse and advise: by reference, in any order, and record what the network decided.
[reveal: v-548]
[pause: 0.45]
C: Clear: the file is the truth.
[reveal: v-549]
[pause: 0.45]
C: Change rules: data, versioned, staged, recorded on every decision.
[pause: 1.0]

[slide: v-550]
[pause: 1.0]
C: Eight fixes, each with its property.
C: Holds for the tip.
[reveal: v-551]
[pause: 0.45]
C: One conditional write per account.
[reveal: v-552]
[pause: 0.45]
C: The network reference, with tombstones.
[reveal: v-553]
[pause: 0.45]
C: A cut-off and a fail table with caps.
[reveal: v-554]
[pause: 0.45]
C: Inline counters.
[reveal: v-555]
[pause: 0.45]
C: Rules as staged data.
[reveal: v-556]
[pause: 0.45]
C: Recording every advice.
[reveal: v-557]
[pause: 0.45]
C: And watching decisions, not boxes.
[pause: 1.0]

[slide: v-558]
[pause: 0.6]
C: Ten mistakes.
C: In the design: debiting at authorisation.
C: Assuming one authorisation means one clearing record.
C: Read, then write.
C: Ignoring retries and early reversals.
C: Velocity only from a stream.
[reveal: v-559]
[pause: 0.45]
C: In judgment: the network gives us a hundred milliseconds.
C: Waiting for the model, or fail open as the whole answer.
C: Shadow mode to measure false positives.
C: Refusing advices because they overdraw.
C: And no owner for the fail policy.
[pause: 0.8]

[slide: v-560]
[pause: 0.7]
V: Answer in time with a hold, not a debit. Make every message count once, whatever the order. Spend the budget on what matters, and write down what happens when something is late. And record what the network decided for us, even when it hurts.
[pause: 1.2]
C: Thank you. I'll stop there.
[pause: 1.6]
