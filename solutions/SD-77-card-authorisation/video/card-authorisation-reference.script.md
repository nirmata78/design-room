# SD-77 Card authorisation and issuer processing: reference solution (Staff L6/L7)

<!-- Video script for slide-video-kit/scripts/build_video.py. [slide: v-NNN] = frames/v-NNN.png, the number printed on every slide.
     Speakers: C candidate · I interviewer · V key line (slower) · N coach. Generated from src/*.py: edit the sources, not this file. -->
<!-- voices: N=af_heart@0.92 I=bf_emma@0.95 C=am_michael@0.9 V=am_michael@0.84 -->
<!-- labels: N=COACH -->
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
N: Five axes. The weak answer debits the balance and calls a fraud service. The strong answer places a hold, keys every message by the network's reference, gives the model a budget, and says what happens when it is late.
C: Two facts I'll keep for the whole round. The money is a hold. And the deadline belongs to someone else.
[pause: 1.0]

[slide: v-005]
[pause: 0.7]
V: Card authorisation is a promise made inside someone else's deadline. A hold, not a debit. Every message once, in any order. A written answer for when a step is late. And a ledger that absorbs what we did not decide.
[pause: 1.6]

[slide: v-006]
[pause: 0.6]
C: The order. Requirements, numbers, and a short theory chapter. Then the messages and the data, and a design in three versions, each answering the objection to the one before.
C: Then most of the time goes to eight challenges that break it, where each fix creates the next question. A build cost, and a recap.
[pause: 0.8]

[pause: 1.4]

## 1 Requirements and scope

[slide: v-007]
[pause: 1.2]
C: Six questions before I draw anything. Each answer moves the design.
[pause: 1.8]

[slide: v-008]
[pause: 0.6]
C: How many cards, and how much traffic?
I: Eight million debit cards. Fifteen hundred authorisations a second at the evening peak, four thousand on the busiest shopping day of the year.
C: Four thousand a second is a small fleet. So throughput will not be the problem. The tail of the slowest step will be.
[pause: 0.6]

[slide: v-009]
[pause: 0.6]
C: What is the deadline, and what happens if we miss it?
I: The network times out after about two seconds, and then it stands in. Your own target is up to you.
C: Then I'll correct a common prep line out loud: the network does not give us a hundred milliseconds. Its timeout is seconds, and our target is a choice. I'll take three hundred milliseconds at the ninety-ninth percentile, measured at our gateway, and design for the case when we miss it anyway.
[pause: 0.6]

[slide: v-010]
[pause: 0.6]
C: Which messages do we receive?
I: Authorisation, incremental authorisation, reversal, advice, and refund. Clearing comes in a daily file.
C: So it is a message state machine, not one request type. A reversal can cancel an approval. An advice tells us what the network decided while we were away. And the file comes days later.
[pause: 0.6]

[slide: v-011]
[pause: 0.6]
C: What do fraud and rules look like?
I: Losses are about eight basis points of volume. Chargebacks and customer reports arrive thirty to ninety days later. Analysts change rules several times a day, and they don't want a code release for it.
C: Thirty to ninety days is the number I'll come back to. It means we cannot learn quickly whether a decline was right. Challenge six.
[pause: 0.6]

[slide: v-012]
[pause: 0.6]
C: Where does the balance live, and does clearing always match?
I: The balance lives in our core ledger. Clearing amounts can differ from the authorisation, and some authorisations never clear.
C: Then an approval must not touch the ledger's balance. It places a hold, and clearing moves the real amount. That is challenge one.
[pause: 0.6]

[slide: v-013]
[pause: 0.6]
C: Do we ever see full card numbers?
I: No. The processor in front of you keeps them in its vault, and sends you a token. Keep it that way.
C: Good. That keeps the card-data scope at the processor. Everything I design keys on the token.
[pause: 0.6]

[slide: v-014]
[pause: 0.6]
C: Four functional requirements. One, authorise: approve or decline inside the deadline, and an approval places a hold. Two, reverse and advise: reversals release holds, and stand-in advices are recorded, even past the balance.
C: Three, clear: match each clearing record to its hold, post the real amount, and expire the holds that never clear. Four, change rules: analysts publish rules as versioned data, with a staged rollout, and no deploy. Each of these gets a numbered flow.
[pause: 0.8]

[slide: v-015]
[pause: 0.6]
C: The numbers, and they are initial targets. Three hundred milliseconds at the ninety-ninth percentile at our gateway. Four nines for the authorisation path, because every minute we are down is a minute of stand-in for every card. Every network message takes effect once. A rule change live within five minutes.
C: And four more. Our own approvals never take an account below zero. Every decision reproducible for seven years, for disputes. Clearing posted by nine in the morning. And degraded decisions inside an hourly exposure cap that risk and finance sign.
[pause: 0.8]

[slide: v-016]
[pause: 0.6]
C: In scope: the decision, holds, reversals and advices, rules and the model score, online features, the fail policy, clearing, and the decision events.
C: Out, on purpose. Issuing the cards. The network and the processor themselves. The disputes workflow: I only read its labels. Statements, model training, credit products. And the three-D Secure challenge flow, whose result simply arrives as one more input field.
[pause: 0.8]

[slide: v-017]
[pause: 0.7]
V: The core is three things. A decision path that always answers inside the deadline. A hold ledger where each message takes effect once. And a clearing path that turns promises into posted money.
[pause: 0.8]
N: The candidate named the core before drawing a box. That is the scoping signal the interviewer is waiting for.
[pause: 1.6]

[pause: 1.4]

## 2 Estimates

[slide: v-018]
[pause: 1.2]
C: Numbers next, each as arithmetic, each with the decision it drives. I'll label them: given, derived or illustrative.
[pause: 1.8]

[slide: v-019]
[pause: 1.0]
C: Traffic. Four thousand a second on the busiest day. Say twenty million messages a day, which is about two hundred and thirty a second on average and two and a half per card per day. That number is illustrative, and it sizes logs and files, not servers.
C: Concurrency. Four thousand a second, times three hundred milliseconds, is twelve hundred requests in flight at worst, about four hundred at a typical hundred milliseconds. Small. Each reads three things: the account and its holds, the card, and the counters. Twelve thousand reads a second, each budgeted at a few milliseconds.
C: The decision this drives: the state a decision needs lives next to the decision, in a store built for millisecond reads. Never the core ledger, on the hot path.
[pause: 1.0]

[slide: v-020]
[pause: 1.0]
C: The hold book. Say twelve million approvals a day, each open about three days until it clears. That's thirty-six million open holds, and at about two hundred bytes each, seven gigabytes. The whole book fits in memory, partitioned by account.
C: Per account, the rate is tiny: a busy card does a few authorisations a minute. So serialising every write for one account costs nothing. The exception is a business account with two thousand cards on one balance. Even that is about three a second on one key. I'll keep it for challenge two.
[pause: 1.0]

[slide: v-021]
[pause: 1.0]
C: What a slow model costs. If two percent of decisions at the peak miss the model's slot, that's four thousand a second, times sixty seconds, times two percent: forty-eight hundred decisions a minute decided on rules alone.
C: At an average of sixty dollars and our base fraud rate of eight basis points, that is about two hundred and thirty dollars a minute of expected loss. Small. But fraud concentrates exactly where the model is blind, so the real number is several times higher. Falling back is a money decision, so it gets a cap and an owner. Challenge four.
[pause: 1.0]

[slide: v-022]
[pause: 1.0]
C: The batch side. The clearing file: about ten million records of five hundred bytes, five gigabytes a day. Minutes of work. The hard part is matching, not volume. A bad file with three percent duplicated is three hundred thousand records that must do nothing.
C: The decision log: twenty million decisions of about two kilobytes, forty gigabytes a day, fifteen terabytes a year, kept seven years in object storage. And an outage: twenty minutes at night at three hundred a second is three hundred and sixty thousand decisions the network made for us. Challenge seven.
[pause: 1.0]

[slide: v-023]
[pause: 1.0]
C: Before the budget, what the numbers decide, in one table. Twelve thousand reads a second means a dedicated authorisation store. Seven gigabytes of holds means it lives in memory, partitioned by account. A few authorisations a minute per account means serialising each account costs nothing.
C: Two hundred and thirty dollars a minute, at least, for a slow model means the fallback needs a cap and an owner. And three hundred and sixty thousand advices after an outage means we record every one, once, whatever it does to the balance. An estimate that changes nothing is decoration.
[pause: 1.0]

[slide: v-024]
[pause: 1.3]
C: The budget. Checks first: parse the message and look up its reference, read the account and the card, read and increment the counters, run the rules. About twenty-three milliseconds. The model gets sixty, and then a cut-off. Reserving the hold and replying, about fifteen.
C: Ninety-eight milliseconds at the cut-off, two hundred spare. The spare is not waste. It is room for a pause, a failover and a slow hop at the same time, before the network's own clock is in danger. And the budget says the model is the only step allowed to be slow, and only up to its cut-off.
[pause: 1.1]

[pause: 1.4]

## 3 Theory

[slide: v-025]
[pause: 1.2]
C: A short theory chapter before the design, so the design can lean on it. What this system is and is not, the properties, the central tension, seven mechanisms, an options matrix, and the failure catalogue.
[pause: 1.8]

[slide: v-026]
[pause: 0.7]
V: An issuer's authorisation system answers the network before its deadline, reserves the amount as a hold against the available balance, and later settles the real amount from the clearing file.
[pause: 1.0]
C: Every clause is load-bearing. Before its deadline: miss it, and the network decides for us. A hold: no money moves at the till. Available balance: posted balance minus the holds. And later settles the real amount: clearing can differ, or never come.
[pause: 1.6]

[slide: v-027]
[pause: 0.6]
C: Four neighbours it is confused with. It is not a payment: no money moves at authorisation. It is not a debit: a hold can grow with a tip, shrink, be reversed, clear for a different amount, or simply expire.
C: It is not the fraud model: the model is one input with a budget, and the decision happens with or without it. And it is not the core ledger: holds live next to the decision, posted money lives in the ledger, and the two are reconciled every day.
[pause: 0.8]

[slide: v-028]
[pause: 0.6]
C: Safety, what must never happen. S-one: our own approvals never take an account below zero. Note the word own: the network's decisions will, and that is challenge seven. S-two: no network message takes effect twice. S-three: no decision we cannot reproduce.
C: Liveness, what must eventually happen. L-one: every authorisation gets an answer inside the deadline, degraded if need be, never silence. L-two: every hold ends. L-three: a rule change takes effect within minutes. Every fix from here names which one it serves.
[pause: 0.8]

[slide: v-029]
[pause: 1.3]
C: The central tension. Each signal buys quality and costs time. Rules are ten milliseconds. The model adds tens more. Rich aggregates on request would add hundreds. The curve flattens: past our three-hundred millisecond target, the gain is small.
C: And past the network's deadline, on the right, the network decides with far less information than we have. So the design spends the deadline deliberately, and writes down in advance what happens when a step is late.
[pause: 1.1]

[slide: v-030]
[pause: 0.6]
C: Mechanism one, holds with expiry. It protects S-one and L-two. An approval inserts a hold, and available is posted minus active holds. Incrementals raise it, reversals release it, clearing moves it to posted, and a lifetime by merchant type ends it. It rules out debiting at the till, and money stuck forever. It costs a lifecycle, an expiry job, and a pending amount the customer must understand.
[pause: 0.8]

[slide: v-031]
[pause: 0.6]
C: Mechanism two, idempotency on the network reference. It protects S-two. A message table keyed by the reference the network gives us. A retry returns the stored answer. A reversal that arrives before its original is kept as a tombstone. It rules out a retry placing two holds, and an early reversal being lost. It costs a message store kept for days.
[pause: 0.8]

[slide: v-032]
[pause: 0.6]
C: Mechanism three, the per-account atomic reserve. One conditional write, in the partition that owns the account: check available, insert the hold, record the message, bump the version. It rules out two concurrent swipes both spending the same money. It costs a store partitioned by account, and a shared business account becomes a hot key.
[pause: 0.8]

[slide: v-033]
[pause: 0.6]
C: Mechanism four, a latency budget with a fail-policy table. It protects L-one. Each step gets a slice, rules run in process, the model has a sixty millisecond cut-off, and a table says what we decide when something is late, with an hourly exposure cap. It rules out a slow dependency making us miss the deadline. It costs degraded decisions with real money attached, and a policy that risk and finance must own.
[pause: 0.8]

[slide: v-034]
[pause: 0.6]
C: Mechanism five, two-speed features. Burst counters are read and incremented inline, in one round trip. Richer aggregates come from the stream, seconds late. And every feature value is logged with the decision. It rules out a stream lagging behind a burst of fraud, and training on values the model never saw. It costs a counter store on the hot path.
[pause: 0.8]

[slide: v-035]
[pause: 0.6]
C: Mechanism six, rules as versioned data. A sandboxed expression language, a staged rollout of backtest, shadow, slice and enforce, a kill switch, an expiry, and the version on every decision. It rules out a deploy to block an attack, and one bad rule declining everyone. It costs tooling, and an honest limit: labels arrive months later.
[pause: 0.8]

[slide: v-036]
[pause: 0.6]
C: Mechanism seven, the clearing file as financial truth. Match by reference, then fuzzy. Move the amount from hold to posted. Post what has no match. And record the network's stand-in decisions even when they overdraw. It rules out holds that never end, and books that disagree with the network's. It costs an unmatched queue, and over-limit handling.
[pause: 0.8]

[slide: v-037]
[pause: 1.0]
C: Five ways to place the decision and the money. A, debit the core ledger at authorisation: wrong the moment clearing differs, and the ledger's batch window sits on our path. B, a chain of synchronous remote calls: correct, but the tails add up, and any slow link means stand-in.
C: C, holds in the core ledger with a budget for scoring: mostly works, but the ledger's nightly posting and maintenance still sit on the authorisation path. E, let the processor decide with rules we upload: fine for a launch, until our fraud needs outgrow its rule language.
V: I pick D: our own authorisation store, next to a stateless decision service.
[pause: 1.0]

[slide: v-038]
[pause: 0.6]
C: Why D. The ledger is off the hot path. Holds and messages are reserved in one write. Rules change as data. And the model can be late without making us late. What it gives up: a second copy of balances, which must be reconciled with the ledger every day.
C: And I'd say plainly: for the first months of a new card programme, E is the right answer, and it appears in the build cost. Move to D when fraud needs our own model.
[pause: 0.8]

[slide: v-039]
[pause: 1.0]
C: The failure catalogue, which becomes the challenge list. A tip, and a hold that never clears. Two swipes on one balance. A retry, and a reversal before its original. The model slow tonight. A burst seconds apart. A new attack at two in the morning. Stand-in, and a late clearing file. And declines doubling while the dashboards stay green.
C: The ninth, card numbers in our systems, I dismiss: we only ever see tokens.
[pause: 1.0]

[slide: v-040]
[pause: 1.0]
N: Good theory has a consequence for the design. Every mechanism here names the property it serves and where it comes back.
C: That is the vocabulary. On to the messages and the data.
[pause: 1.0]

[pause: 1.4]

## 4 API and entities

[slide: v-041]
[pause: 1.2]
C: Four message families from the network, one file, and one internal call. Each tagged with the requirement it serves and the data it reads or writes.
[pause: 1.8]

[slide: v-042]
[pause: 1.0]
C: The network speaks a message standard called I-S-O eighty-five eighty-three, with numbered fields. Our gateway maps it to our own messages, so nothing behind the gateway knows the wire format.
C: Authorise carries the network reference, the card token, the amount, the merchant category code and the entry mode, and gets back approve or decline with a reason. The incremental raises an existing hold. A reversal releases one, and may arrive before its original. An advice tells us what the network decided for us, and is always acknowledged.
C: The clearing file comes once a day, and every record has its own I-D. And internally, analysts post rule sets and promote them through modes.
[pause: 1.0]

[slide: v-043]
[pause: 0.6]
C: Two fields matter more than the rest. The merchant category code says what kind of merchant it is: restaurant, fuel, hotel, electronics. It sets how long a hold lives, and it is the strongest single fraud feature. The entry mode says whether the card was present. Most fraud is card-not-present, so almost every rule branches on it.
C: And the decline reason matters. Suspected fraud sends the customer a text, and their reply, it was me, is the fastest false-positive signal there is. That comes back in challenge six.
[pause: 0.8]

[slide: v-044]
[pause: 1.0]
C: One authorisation, both ways. The network reference, R-forty-four-ten, keys everything that follows. The token resolves to account A-twelve. The amount travels as an integer in minor units, six thousand cents, never a floating-point number. The merchant category says restaurant, and the entry mode says contactless.
C: The answer is approve with an authorisation code. The rule-set and model versions are not sent to the network. They go into the decision record, which is how we reproduce this decision in seven years.
[pause: 1.0]

[slide: v-045]
[pause: 1.3]
C: The conceptual model. An account has many cards. An account reserves many holds. A hold is created by a message and changed by later messages with the same reference: the incremental, the reversal.
C: Each message is recorded as a decision, a weak entity carrying the features, the rule-set version and the model version. And a hold is settled by clearing records: usually one, several for a split shipment, none for a hold that expires.
[pause: 1.1]

[slide: v-046]
[pause: 1.3]
C: The physical tables in the authorisation store. The account row: posted balance, holds total, a version, and a state that includes over-limit. Holds keyed by account and hold, with the network reference unique. And the message table keyed by the network reference, for idempotency.
C: The point is the partition key. Account, holds and messages all live in the account's partition, so one local transaction can reserve a hold and record its message together. Cards map tokens to accounts. Clearing records have their own I-Ds. And rule sets are versioned rows every decision service reads.
[pause: 1.1]

[slide: v-047]
[pause: 1.0]
C: Before choosing products, I decide which stores we may lose. The authorisation store, never: holds are money, and messages are how we stay idempotent. The counters, yes: ten minutes of buckets, rebuilt from the event log, and the fail table covers the gap. The event log, not until it is consumed. The archive and the ledger, never.
[pause: 1.0]

[pause: 1.4]

## 5 High-level design

[slide: v-048]
[pause: 1.2]
C: The design in three versions, drawn on the same baseline. Each answers the objection to the one before.
[pause: 1.8]

[slide: v-049]
[pause: 1.3]
C: Version one. A gateway and one decision service. To authorise, it reads the balance from the core ledger and inserts a hold row there, in one transaction. Rules are if-statements in the code. A nightly job reads the clearing file, posts and releases.
C: For a small issuer at a hundred a second, it might be enough. The objection: the core ledger's tail latency and its nightly batch window now sit on the authorisation path. Every rule change is a deploy. There is no fraud score. And nothing answers a retried or out-of-order message.
[pause: 1.1]

[slide: v-050]
[pause: 1.3]
C: Version two answers that. The decision service becomes stateless, and its state moves to an authorisation store: balances, holds and messages, partitioned by account, with one atomic reserve. Rules move into the decision service's own process, pushed as versioned data by a rule service that analysts use. A model scorer answers under a sixty millisecond cut-off.
C: Every decision goes to an outbox in the same write as the hold, and on to an event log. A clearing matcher posts to the core ledger and releases holds, and the ledger's other balance changes, a salary in, a direct debit out, flow back to the authorisation store. The new boxes are outlined in blue.
C: The objection it leaves: where do features come from? What do we decide when something is late? What about stand-in advices? And how do two copies of the balance stay in agreement?
[pause: 1.1]

[slide: v-051]
[pause: 1.3]
C: Version three. A feature store with burst counters the decision reads and increments inline, and pattern features a stream aggregator computes from the event log. The fail-policy table and its exposure counters live in the decision service. Advices take the same path as authorisations.
C: The rule service gains backtest and shadow. Alerts, cases and the decision archive consume the event log. And a daily job reconciles the authorisation store against the ledger. The objection it leaves is the details. Those are the challenges.
[pause: 1.1]

[slide: v-052]
[pause: 1.0]
C: The three versions in one table. Version one: one service on the ledger. Version two: split the decision from the ledger, and make rules data. Version three: protect the deadline and close every loop. Each answers the objection to the one before.
[pause: 1.0]

[slide: v-053]
[pause: 1.3]
C: Flow one, authorise. One: the network sends the request through the processor. Two: the gateway maps it and passes it to a decision service. Three: the decision service increments this card's counter for the current minute and reads the nine before it, in one round trip.
C: Four: it sends the request to the model with a sixty millisecond cut-off, while the rules run in its own process. Five: to approve, it reserves the hold in the account's partition: check available, insert the hold, record the message, in one conditional write.
C: Six: the decision, with its inputs and versions, goes to the outbox in that same write, and on to the event log. Seven and eight: the answer goes back through the gateway to the network.
[pause: 1.1]

[slide: v-054]
[pause: 1.3]
C: As a sequence. Authorise R-forty-four-ten, sixty dollars, at a restaurant. Count this swipe and read ten minutes: one millisecond. The model is asked with a cut-off, while rules run in process. The model answers in thirty-eight milliseconds: low risk. Reserve: hold sixty if available, record the message. Okay, available four hundred and forty. The decision goes to the outbox, and the network gets approve, in ninety-one milliseconds.
[pause: 1.1]

[slide: v-055]
[pause: 1.3]
C: Flow two, reversals and advices. One: the message arrives from the network. Two: the gateway passes it on. Three: the decision service applies it by network reference in the authorisation store. A reversal releases all or part of a hold, or waits as a tombstone if its original has not arrived. An advice is recorded as a hold, even if it takes the account below zero.
C: Four: the event goes to the log. Five: the acknowledgement goes back. Nothing here is a decision. It is recording.
[pause: 1.1]

[slide: v-056]
[pause: 1.3]
C: Flow three, clearing. Before step one, the matcher loads the day's file and skips record I-Ds it has already applied. One: in the authorisation store, in one write, it moves the amount from the hold to the posted balance. Posted goes down by seventy-two, the seventy-two dollar hold is released, and available does not move at all.
C: Two: it posts the same amount to the core ledger, keyed by the clearing record's I-D. Three: the ledger's other balance changes flow back, and clearing postings already applied are recognised by record I-D and skipped.
C: Why this order? If we released the hold first and waited for the ledger to lower the balance, available would jump up for a moment, and a purchase in that moment could spend money that is already gone.
[pause: 1.1]

[slide: v-057]
[pause: 1.3]
C: As a sequence. File F-eleven-twenty-one, ten million records. Skip record I-Ds already seen. Find the hold for R-forty-four-ten: seventy-two dollars, after the tip. One write: posted down seventy-two, hold released, available unchanged. Then post seventy-two in the ledger. A record with no reference falls back to card, merchant, amount within twenty percent, and seven days. And a record with no match at all still posts, and goes to a review queue.
[pause: 1.1]

[slide: v-058]
[pause: 1.3]
C: Flow four, changing rules. One: an analyst writes rule version fifteen in the rule service, which backtests it on the decision archive. Two: the rule service pushes a new rule-set version to every decision service, in shadow. Three: every decision records the rule-set version, and what the shadow rule would have done.
C: Four: the event log feeds the alarms on decline rate by merchant type. Then a slice, then enforcement. And rollback is re-pointing to the previous version.
[pause: 1.1]

[slide: v-059]
[pause: 1.3]
C: The C-four context view. The cardholder pays a merchant, whose acquirer sends the purchase through the card network and the processor to us. We send the cardholder alerts. Fraud operations write rules and work cases. And we send postings to the core banking ledger. Nothing else sits on the authorisation path.
[pause: 1.1]

[slide: v-060]
[pause: 1.3]
C: The container view. The network and processor on the left. The gateway, the decision service and the authorisation store in a row: that is the whole authorisation path. Above it, what the decision reads: the model scorer, the feature store, the rule service. Below it, what happens after the answer: the clearing matcher, the event log, alerts and cases. That layout is the thesis, drawn.
[pause: 1.1]

[slide: v-061]
[pause: 1.0]
C: Technology, mechanism first. The authorisation store is an in-memory-backed store partitioned by account, with a durable replicated log. Not the core ledger, whose tail would be ours, and not a cache over it, because a cache cannot reserve: two readers of one cached balance both approve.
C: Rules run in process, as data, rather than code or a remote engine. The model sits behind a cut-off. Counters are one key per card per minute in memory, not from the stream. And events leave through an outbox in the same transaction as the hold, because publishing after the write loses the event on a crash.
[pause: 1.0]

[pause: 1.4]

## 6 Bridge

[slide: v-062]
[pause: 1.2]
V: It works. Where does it break first?
[pause: 1.8]

[slide: v-063]
[pause: 1.3]
C: The baseline with its attack points. The authorisation store: the tip, two swipes on one balance, and messages twice or out of order. The model scorer: slow tonight. The feature store: a burst seconds apart. The rule service: a new attack at two in the morning. The gateway: twenty minutes down, and the network standing in. And the alerts: declines doubled, with green dashboards. I'll take them in an order where each fix creates the next question.
[pause: 1.1]

[pause: 1.4]

## 7 Challenges

[slide: v-064]
[pause: 1.2]
C: Eight challenges, each the same way: the question, the naive answer, a case with numbers, where it breaks, the fix, why it works, then the interviewer pushes on the fix itself, and what I'd say in the room.
[pause: 1.8]

[pause: 1.4]

## 7.1 Challenge 1: The tip

[slide: v-065]
[pause: 1.2]
N: Challenge one. A restaurant bill is authorised at one amount and clears at another: where is the money in between?
[pause: 1.8]

[slide: v-066]
[pause: 0.6]
I: A sixty-dollar restaurant authorisation clears three days later at seventy-two, with the tip. Walk me through the money.
[pause: 2.0]

[slide: v-067]
[pause: 1.3]
C: The naive answer: approve and debit sixty dollars; clearing is a formality. Look at the red decision service writing straight to the ledger. It just moved money that has not moved.
[pause: 1.1]

[slide: v-068]
[pause: 1.0]
C: The trace. Monday, quarter past eight: authorise sixty dollars, and debit it: five hundred becomes four hundred and forty. Two minutes later, the waiter adds a twelve dollar tip. Thursday morning, clearing says seventy-two. Either that is a second debit, and the customer has paid a hundred and thirty-two, or it is ignored, and the restaurant is twelve dollars short with nobody owning it.
C: And this is everywhere amounts differ. A hotel pre-authorises three hundred and checks out at one eighty. A fuel pump authorises one dollar and clears at sixty-four. A split shipment clears twice.
[pause: 1.0]

[slide: v-069]
[pause: 1.3]
C: The fix, outlined green. An approval inserts a hold of sixty dollars in the authorisation store. The incremental raises the same hold to seventy-two. On Thursday, the clearing matcher finds the hold by the network reference and, in one write, moves seventy-two dollars from the hold to the posted balance. Then it posts seventy-two in the ledger.
[pause: 1.1]

[slide: v-070]
[pause: 1.3]
C: Line by line. Monday: authorise sixty, hold sixty. Posted five hundred, available four hundred and forty. The tip: the hold becomes seventy-two, available four hundred and twenty-eight. Thursday: clearing seventy-two, matched by reference. Posted becomes four hundred and twenty-eight, the hold is released, and available stays four hundred and twenty-eight.
C: Available moved at the till. Posted moved on Thursday, when the money really moved. And if Thursday never comes, the hold expires, after about seven days for most merchants and thirty for hotels and car hire.
[pause: 1.1]

[slide: v-071]
[pause: 1.0]
C: How long should a hold live? It depends on the merchant. A restaurant adds a tip within a day or two. A fuel pump authorises a small amount and clears the real fill. A hotel or a car hire clears weeks later. A split shipment clears more than once. So the lifetime comes from the merchant category, and these numbers are illustrative.
C: The asymmetry decides the direction. Release too early, and the customer spends money that is about to leave. Release too late, and they see a little less for a few days. Err late.
[pause: 1.0]

[slide: v-072]
[pause: 0.6]
I: The clearing record has no matching authorisation. Or it arrives after the hold expired.
[pause: 2.0]

[slide: v-073]
[pause: 0.6]
C: Match by reference first. With no reference, fall back to the card, the merchant, an amount within twenty percent, and a seven-day window. And if nothing matches, the record still posts. The network has already paid the merchant from our settlement account, so the file is the financial truth. It goes to a review queue.
C: A clearing that arrives after its hold expired posts too, and may take the account below zero. That is a modelled state, in challenge seven. And expiry waits for the day's file, so a hold is never released an hour before its own clearing arrives.
[pause: 0.8]

[slide: v-074]
[pause: 0.7]
V: If asked, I'd say: approval is a hold, not a debit. Available is posted minus holds, and clearing moves the real amount from hold to posted. Holds that never clear expire, and late clearing still posts.
[pause: 1.0]
N: That fix creates the next question. A hold is a read and a write, and two can race.
[pause: 1.6]

[pause: 1.4]

## 7.2 Challenge 2: Two swipes, one balance

[slide: v-075]
[pause: 1.2]
N: Challenge two. Two authorisations for one account arrive at the same moment, and the money covers one: who decides?
[pause: 1.8]

[slide: v-076]
[pause: 0.6]
I: Two authorisations for one account arrive two milliseconds apart. The balance covers one of them. What happens?
[pause: 2.0]

[slide: v-077]
[pause: 1.3]
C: The naive answer: read the available balance, check it, insert the hold. The red authorisation store is read by two decisions before either writes.
[pause: 1.1]

[slide: v-078]
[pause: 1.0]
C: The trace. Available is one hundred dollars. At noon exactly, a fuel pump for eighty reads one hundred. Two milliseconds later, an online order for sixty reads one hundred. Eighty fits: hold. Sixty fits: hold. Available is minus forty, and we approved both.
C: A joint account does this. So does a phone wallet next to a physical card, or a subscription renewing while the customer pays at a till. Rare per account; daily across eight million.
[pause: 1.0]

[slide: v-079]
[pause: 1.3]
C: The fix is one conditional write in the partition that owns the account. If the holds plus this amount still fit within posted, and the account's version is the one I read, then insert the hold, record the message, add to the holds total and bump the version, all at once. Otherwise nothing is written, and the decision reads again.
[pause: 1.1]

[slide: v-080]
[pause: 1.3]
C: As a sequence. Both reserves carry version forty-one. The eighty dollar one commits first: hold placed, version forty-two. The sixty dollar one finds version forty-two and is refused. It re-reads: available twenty dollars, and sixty is more than twenty. Decline, insufficient funds. Exactly one place answered: is there enough?
[pause: 1.1]

[slide: v-081]
[pause: 1.0]
C: In code. Read the account. If the holds plus the amount exceed posted, decline. Otherwise, one transaction in the account's partition: on condition that the version is unchanged, put the hold, put the message, and update the total and the version. If someone else won, read again.
C: Why not a distributed lock? It gives the same safety, with a lock service on the hot path and a lease to expire when a server dies holding it. The conditional write is the lock and the write in one step.
[pause: 1.0]

[slide: v-082]
[pause: 0.6]
I: A business account has two thousand fleet cards on one balance, and on the busiest day they all buy fuel at seven in the morning.
[pause: 2.0]

[slide: v-083]
[pause: 1.3]
C: The arithmetic first. Two thousand cards, each one authorisation in ten minutes, is three point three a second on one key. One partition handles that easily, with a conflict now and then. So the honest first answer is: nothing changes.
C: If it grows to hundreds a second, say a marketplace with virtual cards, carve sub-limits per card from the account. The account reserves budget to each card in blocks, refilled in the background, and most authorisations touch only the card's slice. The limit: a slice can run dry while the account still has money, so refill at half-used and fall back to the account-level reserve before declining.
[pause: 1.1]

[slide: v-084]
[pause: 0.7]
V: If asked, I'd say: check-and-reserve is one conditional write in the account's partition, so two swipes can't spend the same money. It costs nothing, and a big shared account gets sub-limits per card.
[pause: 1.0]
N: That fix writes the message with the hold. The next question is what a message is, when it comes twice.
[pause: 1.6]

[pause: 1.4]

## 7.3 Challenge 3: The same message twice, and in the wrong order

[slide: v-085]
[pause: 1.2]
N: Challenge three. The network retries, and a reversal overtakes its original: how does each message take effect exactly once?
[pause: 1.8]

[slide: v-086]
[pause: 0.6]
I: The network retries an authorisation we already approved. And a reversal arrives before the authorisation it reverses. What happens?
[pause: 2.0]

[slide: v-087]
[pause: 1.3]
C: The naive answer: process messages as they arrive, and a retry is a new request. The red gateway and store treat every arrival as new.
[pause: 1.1]

[slide: v-088]
[pause: 1.0]
C: Two traces. At half past six, R-seventy-seven-thirty-one for forty-five dollars is approved and its hold placed, but the answer is lost on the link. Almost two seconds later the network retries it, and the naive system places a second hold: available is down ninety.
C: Then at two minutes past seven, a reversal of R-eighty-eight-forty arrives first: the merchant cancelled at once. Nothing to reverse, so it is dropped. Sixty milliseconds later the authorisation itself arrives and is approved: a hold for a purchase that was cancelled, for seven days.
[pause: 1.0]

[slide: v-089]
[pause: 1.3]
C: The fix. The message table is keyed by the network's reference. Before acting, the decision looks the reference up. A retry gets the stored answer. A reversal whose original has not arrived is kept as a tombstone. And the message record is written in the same transaction as the hold, so no crash can leave one without the other.
[pause: 1.1]

[slide: v-090]
[pause: 1.3]
C: As a sequence. The reversal of R-eighty-eight-forty arrives; the message table has nothing, so we store a tombstone and acknowledge. Sixty milliseconds later the authorisation arrives. Reserve? The store says: already reversed, no hold. We answer as the network expects, and nothing is held. And when the network retries it, it gets the stored answer again.
[pause: 1.1]

[slide: v-091]
[pause: 0.6]
C: Three keys that look right and are not. Arrival time: a retry arrives later and a reversal earlier, so time is exactly what varies. A hash of the amount and the merchant: two genuine coffees five minutes apart look identical, and one would be swallowed. And our own generated I-D: the network does not know it, so its retry cannot carry it. The only key both sides share is the network's reference.
[pause: 0.8]

[slide: v-092]
[pause: 0.6]
I: The partition fails over mid-write. Or the message table is purged, and a retry arrives a day later.
[pause: 2.0]

[slide: v-093]
[pause: 0.6]
C: The transaction commits on a quorum of replicas before the answer leaves, so a new primary has both writes or neither. Message records are kept for longer than the network's retry and reversal windows, which are days. Twenty million a day, a hundred bytes each, for thirty days, is about sixty gigabytes. Cheap.
C: And past that window, clearing is the backstop: a hold that should not exist expires, and a clearing that should exist posts.
[pause: 0.8]

[slide: v-094]
[pause: 0.7]
V: If asked, I'd say: every message is keyed by the network's reference, and recorded in the same atomic step as the hold. A retry gets the stored answer, and an early reversal waits as a tombstone.
[pause: 1.0]
N: The money is now correct. The next question is about time: what if the answer itself is late?
[pause: 1.6]

[pause: 1.4]

## 7.4 Challenge 4: The model is slow tonight

[slide: v-095]
[pause: 1.2]
N: Challenge four. The fraud model's tail jumps to almost two seconds: do we wait for it, ignore it, or something better?
[pause: 1.8]

[slide: v-096]
[pause: 0.6]
I: Your fraud model is at one point eight seconds, at the ninety-ninth percentile, tonight. What does the authorisation path do?
[pause: 2.0]

[slide: v-097]
[pause: 1.3]
C: Two naive answers. Wait for it, because fraud matters more than latency. Or fail open. The red model scorer sits on the critical path with no limit of its own.
[pause: 1.1]

[slide: v-098]
[pause: 1.0]
C: The trace. At eight in the evening, a model release doubles its feature fetches, and its tail goes to one point eight seconds. If we wait, by one minute past eight, thirty percent of our answers pass two seconds. The network stands in for four hundred and fifty authorisations a second, with limits we set months ago and no score at all.
C: If we fail open, every decision is unscored: fifteen hundred a second, ninety thousand a minute, and a fraud ring probing with small purchases notices within minutes. These numbers are a scenario, illustrative.
[pause: 1.0]

[slide: v-099]
[pause: 1.3]
C: The fix. Rules always run, in process, in about ten milliseconds. The model gets a sixty millisecond slice, and at sixty the decision proceeds without it. What without it means is not an if-statement. It is a table, agreed in advance, with an hourly exposure cap on every cell.
[pause: 1.1]

[slide: v-100]
[pause: 1.0]
C: The table. Model late, small amount at a low-risk merchant: decide on rules alone. Large amount or a risky merchant type: rules with stricter limits. Counters missing: conservative limits for card-not-present. Rules engine failing: approve small amounts within stand-in-like limits, decline or step up the rest. And if we miss the deadline entirely, the network stands in.
C: Every cell has an hourly exposure cap, and the decision service counts degraded approvals against it as they happen.
[pause: 1.0]

[slide: v-101]
[pause: 1.3]
C: As a sequence. Ask the model, with a cut-off of sixty. Rules are done at eighteen milliseconds. At sixty, no score: proceed. The table row: model late, sixty dollars, restaurant. Rules only, the cap is fifty thousand dollars an hour, seven thousand two hundred used. Approve, flagged degraded, counted. And when the score arrives at one point eight seconds, it is logged and ignored.
[pause: 1.1]

[slide: v-102]
[pause: 0.6]
C: Someone usually suggests hedging: send the model call to two scorers and take the first answer. It trims a random tail, one slow machine among many. Tonight the slowness is the model itself, so every copy is slow, and hedging doubles its load exactly when it is struggling. A cut-off bounds our latency whatever the cause.
[pause: 0.8]

[slide: v-103]
[pause: 0.6]
I: It lasts all evening, and the cap runs out. And who decided those numbers?
[pause: 2.0]

[slide: v-104]
[pause: 0.6]
C: When a cell's cap is used up, that cell tightens: first a step-up, asking the cardholder to confirm in the app, then lower limits, then decline. And the first runbook step is rolling the model back by re-pointing its version.
C: Who decided? Risk sets the limits in each cell from loss data. Finance signs the cap. Engineering makes each cell a setting, counts every degraded decision, and pages at half the cap. At the manager bar, the point is that this conversation happens before the incident, not during it.
[pause: 0.8]

[slide: v-105]
[pause: 0.7]
V: If asked, I'd say: the model gets a fixed slice of the budget, and we never wait past it. When it's late, a table owned by risk and finance decides, under an hourly cap.
[pause: 1.0]
N: Features are the model's other input. The next question is how fresh they are.
[pause: 1.6]

[pause: 1.4]

## 7.5 Challenge 5: A burst, seconds apart

[slide: v-106]
[pause: 1.2]
N: Challenge five. A rule counts swipes in ten minutes: where does that count come from, and how old is it when we read it?
[pause: 1.8]

[slide: v-107]
[pause: 0.6]
I: Your rule is more than three swipes in ten minutes on one card. Where does that number come from, in time?
[pause: 2.0]

[slide: v-108]
[pause: 1.3]
C: The naive answer: a stream processor counts swipes and writes them to a key-value store. The red stream aggregator is correct, and seconds late.
[pause: 1.1]

[slide: v-109]
[pause: 1.0]
C: The trace. At twelve minutes past three in the morning, four card-not-present purchases of two hundred and forty dollars on one token, within eight seconds. The stream's counter is five to eight seconds behind, so the four decisions read zero, one, one and two. All approved. Six seconds later the counter reads four, and nine hundred and sixty dollars are gone.
C: A burst on one stolen card is a script, seconds apart. A stream is seconds behind. That's what streams are.
[pause: 1.0]

[slide: v-110]
[pause: 1.3]
C: The fix. Burst counters are updated inline, by the decision service itself: per card, one-minute buckets. Before deciding, increment this minute and read the nine before it, in one pipelined round trip, about a millisecond. The counter now reads one, two, three, four, and the fourth swipe is declined.
[pause: 1.1]

[slide: v-111]
[pause: 1.3]
C: Two kinds of features. Inline, on the request path: swipes on this card in ten minutes, card-not-present spend in the last hour, declines in the last hour. From the stream, seconds late, which is fine for them: distinct merchants for this card today, a merchant's decline rate in the last hour, a device seen on other cards in thirty days. The decision reads both in the same call.
[pause: 1.1]

[slide: v-112]
[pause: 1.0]
C: In code. One key per card per minute, with an expiry of eleven minutes so the buckets clean themselves up. In one pipelined round trip: increment this minute, read the nine before, and sum.
C: Two details. The swipe is counted before the decision, so declined attempts count too, and a script that keeps trying after a decline is the strongest signal there is. And every feature value goes into the decision record, so the model is trained on exactly what it saw, not on values recomputed later by a different pipeline.
[pause: 1.0]

[slide: v-113]
[pause: 0.6]
I: The counter store is slow, or down.
[pause: 2.0]

[slide: v-114]
[pause: 0.6]
C: It is already a row in the fail table: counters missing, so rules apply conservative limits for card-not-present, inside the cap. Card-present purchases barely change.
C: And the store is partitioned by card with a replica. Losing a partition loses at most ten minutes of buckets, which are rebuilt from the event log for the cards that transact next.
[pause: 0.8]

[slide: v-115]
[pause: 0.7]
V: If asked, I'd say: burst features are counted inline, in one round trip, because a stream lags behind a burst. Patterns come from the stream, and every value is logged with the decision.
[pause: 1.0]
N: A counter is only useful if a rule reads it. The next question is how a rule gets there, at two in the morning.
[pause: 1.6]

[pause: 1.4]

## 7.6 Challenge 6: A new attack at 2 a.m.

[slide: v-116]
[pause: 1.2]
N: Challenge six. An attack starts in the middle of the night: how fast can an analyst block it, and what stops them blocking everyone?
[pause: 1.8]

[slide: v-117]
[pause: 0.6]
I: A new attack appears at two in the morning. How fast can an analyst block it, and what stops them from blocking everyone?
[pause: 2.0]

[slide: v-118]
[pause: 1.3]
C: Two naive answers. Add an if-statement and hotfix the decision service. Or: shadow-test the rule to measure its false positives. The red rule path is either a deploy, or a live change with nothing in between.
[pause: 1.1]

[slide: v-119]
[pause: 1.0]
C: The trace. Five past two: fraud operations see a pattern. A one-dollar test charge, then four hundred at electronics merchants, on cards from one breach. A hotfix goes through review, build and deploy, and is live at five to three: fifty minutes of losses.
C: The other way: at twenty past two an analyst pushes amount over three hundred at electronics, decline, straight to production. A minute later, nine percent of all electronics purchases are declined, almost all of them good customers.
[pause: 1.0]

[slide: v-120]
[pause: 1.3]
C: The fix: rules are versioned data. A rule is an expression in a small sandboxed language, with an owner and an expiry. It goes through four stages, and every decision records the rule-set version it ran.
[pause: 1.1]

[slide: v-121]
[pause: 1.3]
C: The stages. Write the expression. Backtest it on ninety days of the decision archive, with known labels: how much of this ring it catches, how many good purchases it declines. Shadow: it runs on live traffic and logs what it would have done. A slice: enforce on five percent, with an alarm on the decline rate by merchant type. Then enforce everywhere, with a kill switch.
C: Rollback is re-pointing every decision service to the previous rule-set version: seconds, no deploy.
[pause: 1.1]

[slide: v-122]
[pause: 1.0]
C: A rule, as data. An identifier and a version. The condition: card-not-present, at electronics merchant categories, over three hundred dollars, and at least one small charge on the card in the last day. That last clause is what makes it narrow. An action, a mode, a slice, an expiry two weeks out, and an owner. The language has no loops and no input or output, and each evaluation has a time limit, so a bad rule cannot hang the decision.
[pause: 1.0]

[slide: v-123]
[pause: 0.6]
I: Shadow says the rule would decline four thousand transactions a day. How many were fraud?
[pause: 2.0]

[slide: v-124]
[pause: 0.6]
C: Shadow cannot say. It shows how many it would decline, not which were fraud, because the labels, chargebacks and customer reports, arrive thirty to ninety days later. And most declined good customers never complain at all; they use another card.
C: So the evidence comes from elsewhere. Backtests on labelled history. Fast proxies: the share of customers who reply it was me to a decline text, or who pass a step-up. The slice with its alarm. And the expiry, so an emergency rule is reviewed with real labels instead of living forever.
[pause: 0.8]

[slide: v-125]
[pause: 0.7]
V: If asked, I'd say: rules are versioned data: backtest, shadow, a small slice with an alarm, then enforce, with the version on every decision. Shadow can't measure false positives; labels arrive months later.
[pause: 1.0]
N: Everything so far assumed we were up to answer. The next question is what happens when we were not.
[pause: 1.6]

[pause: 1.4]

## 7.7 Challenge 7: We were down for twenty minutes

[slide: v-126]
[pause: 1.2]
N: Challenge seven. The network decided for us during an outage: what does the next morning look like, and what if the clearing file is bad too?
[pause: 1.8]

[slide: v-127]
[pause: 0.6]
I: You were down for twenty minutes at two in the morning. The network approved three hundred and sixty thousand transactions in stand-in. Walk me through the next morning.
[pause: 2.0]

[slide: v-128]
[pause: 1.3]
C: Two naive answers. The network declined everything while we were down. It didn't: it approved, within our limits. Or: replay them and decline the ones we would not have approved. Too late: the purchases happened. The red path refuses advices that break a never-below-zero rule.
[pause: 1.1]

[slide: v-129]
[pause: 1.0]
C: The trace. From two to twenty past, stand-in approves within our limits: say up to a hundred and fifty dollars a purchase, four hundred a day a card. Twenty minutes, at three hundred a second, is three hundred and sixty thousand approvals.
C: At twenty-one minutes past, we are back, and the advices arrive. Account A-nineteen had thirty-five dollars available, and stand-in approved sixty and eighty. Available is minus one hundred and five. A check that refuses any write below zero rejects both advices. No holds. On Thursday clearing posts both anyway, and our books disagree with the network's.
[pause: 1.0]

[slide: v-130]
[pause: 1.3]
C: The fix: the ledger absorbs the decisions we did not make. Every advice is acknowledged and recorded once, by its network reference, as a hold, even when it takes the account below zero. Over-limit is a modelled account state. New authorisations on that account decline until it is back above zero, the customer is told, and collections take over if it persists.
[pause: 1.1]

[slide: v-131]
[pause: 1.3]
C: As a sequence. Advice R-fifty-one-oh-two, eighty dollars, approved by stand-in. Record it as a hold, even past available. Account A-nineteen: available minus one hundred and five, state over-limit. Acknowledge. An event goes to the ledger. And new authorisations on A-nineteen decline until it is paid back.
C: Then, in the morning, replay the three hundred and sixty thousand through our rules offline. Not to reverse them. To see which we would have declined, and to tune the stand-in limits with risk.
[pause: 1.1]

[slide: v-132]
[pause: 1.0]
C: The morning after, the replay. Run the three hundred and sixty thousand through our rules and model offline, and ask which we would have declined. Say two percent, an illustrative number. How much of that was fraud, we only learn as labels arrive. And then, with risk, decide whether the stand-in limits were too high or too low: fewer good customers declined during an outage, against more fraud let through.
C: The replay never reverses a purchase. It is simply the only data that says whether last night's limits were right.
[pause: 1.0]

[slide: v-133]
[pause: 0.6]
I: And the next day's clearing file arrives six hours late, with three percent of its records duplicated.
[pause: 2.0]

[slide: v-134]
[pause: 0.6]
C: Ingest files idempotently: a checksum per file, so a resent file is recognised, and a unique I-D per record, so the three hundred thousand duplicates are no-ops. Hold expiry waits for the day's file, so a file six hours late still finds its holds open.
C: The nine o'clock posting target slips, with a note to finance and support, not silently. And every day after clearing, the authorisation store is reconciled with the ledger, account by account. Any difference is a break with an owner.
[pause: 0.8]

[slide: v-135]
[pause: 0.7]
V: If asked, I'd say: stand-in decisions are facts, not requests. We record every advice once, even when it overdraws, and model over-limit as a state. Files are idempotent, and expiry waits for them.
[pause: 1.0]
N: Last question, and the one every challenge depends on: how would we know any of this was happening?
[pause: 1.6]

[pause: 1.4]

## 7.8 Challenge 8: Declines doubled in ten minutes

[slide: v-136]
[pause: 1.2]
N: Challenge eight. The decline rate doubles and every dashboard is green: how do we find out, and what do we do first?
[pause: 1.8]

[slide: v-137]
[pause: 0.6]
I: The decline rate doubled in ten minutes. Your dashboards are green. How do you know what is wrong, and what is on the runbook?
[pause: 2.0]

[slide: v-138]
[pause: 1.3]
C: The naive answer: C-P-U, error rate and latency. Those watch boxes. The red rule service and decision service are perfectly healthy, and wrong.
[pause: 1.1]

[slide: v-139]
[pause: 1.0]
C: The trace. Twenty to eight: rule set two hundred and twelve is enforced, and a typo widens a merchant list to include groceries. A minute later, grocery approvals fall from ninety-six percent to seventy-one. No errors. Latency ninety-two milliseconds. At five to eight, the first complaints on social media. At ten past, the first page, from support call volume. Half an hour, and nothing failed.
[pause: 1.0]

[slide: v-140]
[pause: 1.3]
C: The fix: indicators on decisions, not machines. Approval rate by merchant type and region, every minute, against the same hour last week, because card traffic is strongly weekly. The stand-in count. Degraded decisions against each cap. And synthetic test cards in every region that authorise and reverse every minute, end to end. This one pages at nineteen forty-two.
[pause: 1.1]

[slide: v-141]
[pause: 1.0]
C: Symptom pairs: two metrics, one cause. Declines up with a rule-set change in the same minute: a rule, this trace. Declines up at one merchant only: that merchant's terminal. Stand-in up while our latency is flat: the link to the processor, not us. Model cut-offs up with flat latency: the model, and the cut-off is doing its job.
C: And the pair that settles the argument: declines up with it-was-me replies up means false positives, roll back. Declines up with it-was-me flat and step-ups failing means a real attack: keep the rule.
[pause: 1.0]

[slide: v-142]
[pause: 1.0]
C: The runbook. First, rule-set and release changes in the last hour: the most common cause and the fastest to undo. Second, re-point to the previous version, in seconds. Third, compare by merchant type and region, to tell an attack from one broken terminal. Fourth, the model and its features, because a stale feature looks like risk. And fifth, tell support, because otherwise the complaints arrive before the alerts.
[pause: 1.0]

[slide: v-143]
[pause: 0.6]
I: It's real fraud this time. An attack, and the rule is right.
[pause: 2.0]

[slide: v-144]
[pause: 0.6]
C: Then the it-was-me rate and the step-up pass rate separate good customers from fraud within minutes. If few declined customers say it was them, and few pass a step-up, the rule is right. Keep it, tell support what customers will hear, and let the expiry bring it back for review.
[pause: 0.8]

[slide: v-145]
[pause: 0.7]
V: If asked, I'd say: I watch decisions, not boxes. Approval rate by merchant type against last week, and stand-in count. The runbook starts with what changed, the usual cause and the fastest to undo.
[pause: 1.6]

[pause: 1.4]

## 8 Build cost

[slide: v-146]
[pause: 1.2]
C: Build cost. This is the manager layer, marked aux: skip it in a pure Staff round, use it in a manager round.
[pause: 1.8]

[slide: v-147]
[pause: 1.0]
C: Four releases, starting by buying. Version zero: the processor decides, with rules and stand-in limits we upload. Three engineers, eight weeks, and fine for a launch. Version one: our own decision service on the core ledger, four engineers, three months.
C: Version two: the authorisation store, rules as data, the model behind a cut-off and the clearing matcher, a team of six to eight for two quarters. Version three: features, the fail table, advices, lifecycle tooling and reconciliation, two teams for two more quarters.
[pause: 1.0]

[slide: v-148]
[pause: 0.6]
C: Team seams. The authorisation platform owns the gateway, the decision service and the store, and their latency. The risk platform owns the rules engine, features and the shadow tooling. Data science owns models. Fraud operations own the content of the rules and customer contact. Ledger and clearing own posting and reconciliation.
C: The contracts between them are three: the decision event schema, the rule-set format, and the fail-policy table.
[pause: 0.8]

[slide: v-149]
[pause: 0.6]
C: Buy against build. We buy the processor and its card vault, and perhaps the model platform; the network's own risk score arrives as an input. We build the decision path, holds and the clearing match, because they are the product.
C: Cost, illustrative. The largest lines are per-transaction fees and fraud losses, eight basis points of volume. Then the archive and model serving. The fleet is small. A basis point of fraud is worth more than all the servers, so the cost lever is the quality of the decision.
[pause: 0.8]

[slide: v-150]
[pause: 1.0]
C: Top risks. A fail policy nobody signed: review the table and caps monthly. The store and the ledger drifting: reconcile daily. Emergency rules living forever: an expiry on every rule. And card data creeping into scope: tokens only, enforced at the gateway.
[pause: 1.0]

[pause: 1.4]

## 9 Recap

[slide: v-151]
[pause: 1.2]
C: To close: one picture, one sentence per path, the mistakes to avoid, and the thesis.
[pause: 1.8]

[slide: v-152]
[pause: 1.3]
C: The final picture. Across the middle: the network, the gateway, the decision service with rules in process, and the authorisation store with its one atomic reserve. Above: the model behind a cut-off, the feature store with inline counters, the stream aggregator, and the rule service. Below: the event log, alerts and the archive, the clearing matcher feeding the ledger, and probes with test cards.
[pause: 1.1]

[slide: v-153]
[pause: 1.0]
C: Four paths, one sentence each. Authorise: counters, rules and the model under a budget, one atomic reserve, an answer in time. Reverse and advise: by reference, in any order, and record what the network decided. Clear: the file is the truth. Change rules: data, versioned, staged, recorded on every decision.
[pause: 1.0]

[slide: v-154]
[pause: 1.0]
C: Eight fixes, each with its property. Holds for the tip. One conditional write per account. The network reference, with tombstones. A cut-off and a fail table with caps. Inline counters. Rules as staged data. Recording every advice. And watching decisions, not boxes.
[pause: 1.0]

[slide: v-155]
[pause: 0.6]
C: Ten mistakes. In the design: debiting at authorisation. Assuming one authorisation means one clearing record. Read, then write. Ignoring retries and early reversals. Velocity only from a stream.
C: In judgment: the network gives us a hundred milliseconds. Waiting for the model, or fail open as the whole answer. Shadow mode to measure false positives. Refusing advices because they overdraw. And no owner for the fail policy.
[pause: 0.8]

[slide: v-156]
[pause: 0.7]
V: Answer in time with a hold, not a debit. Make every message count once, whatever the order. Spend the budget on what matters, and write down what happens when something is late. And record what the network decided for us, even when it hurts.
[pause: 1.2]
C: Thank you. I'll stop there.
[pause: 1.6]
