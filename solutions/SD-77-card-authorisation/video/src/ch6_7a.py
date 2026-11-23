from dsl import *

# ───────────────────────── 6 · bridge ─────────────────────────
chapter(6, "Bridge", 4, "It works. Where does it break first?", [
 "V: It works. Where does it break first?", "[pause: 1.0]"])

S(dia("Challenge map", "Eight attack points on the same baseline", "map", chip=chips("each fix creates the next question")), [
 "C: The baseline with its attack points. The authorisation store: the tip, two swipes on one balance, and messages twice or out of order. The model scorer: slow tonight. The feature store: a burst seconds apart. The rule service: a new attack at two in the morning. The gateway: twenty minutes down, and the network standing in. And the alerts: declines doubled, with green dashboards. I'll take them in an order where each fix creates the next question."], cls="dia")

chapter(7, "Challenges", 5, "Eight ways to break it, and what survives", [
 "C: Eight challenges, each the same way: the question, the naive answer, a case with numbers, where it breaks, the fix, why it works, then the interviewer pushes on the fix itself, and what I'd say in the room."])

K = lambda n, t: f"Challenge {n} of 8 · {t}"

# ───────── Challenge 1 · the tip ─────────
subchapter("7.1", "Challenge 1: The tip", ["N: Challenge one. A restaurant bill is authorised at one amount and clears at another: where is the money in between?"])
qs("Interviewer · challenge 1 of 8", "“A sixty-dollar restaurant authorisation clears three days later at seventy-two, with the tip. Walk me through the money.”", [
 "I: A sixty-dollar restaurant authorisation clears three days later at seventy-two, with the tip. Walk me through the money.", "[pause: 2.0]"])

S(dia(K(1, "the tip"), "Who moved the money at the till?", "ch1-attack", q=True, red=True,
      extra=strip(("case", "Naive answer", "“Approve and debit sixty. Clearing is a formality.”"),
                  ("case", "Break", "The decision service writes money to the ledger at the till."))), [
 "C: The naive answer: approve and debit sixty dollars; clearing is a formality. Look at the red decision service writing straight to the ledger. It just moved money that has not moved."], cls="dia")

S(plain(K(1, "the trace"), "Debit at the till, and Thursday arrives", '<pre class="trace"><span class="t">Mon 20:14</span>authorise $60: debit; balance $500 → $440\n<span class="t">Mon 20:16</span>the waiter adds a $12 tip: nothing, or a second debit\n<span class="t">Thu 06:00</span>clearing $72 → <span class="bad">a second debit: balance $368</span>\n<span class="t">or</span><span class="bad">ignored: the restaurant is $12 short, and nobody owns it</span></pre>' +
  '<div class="hedge"><b class="t">The same shape everywhere</b>A hotel pre-authorises $300 and checks out at $180. A fuel pump authorises $1 and clears at $64. A split shipment clears twice.</div>', q=True, red=True), [
 "C: The trace. Monday, quarter past eight: authorise sixty dollars, and debit it: five hundred becomes four hundred and forty. Two minutes later, the waiter adds a twelve dollar tip. Thursday morning, clearing says seventy-two. Either that is a second debit, and the customer has paid a hundred and thirty-two, or it is ignored, and the restaurant is twelve dollars short with nobody owning it.",
 "C: And this is everywhere amounts differ. A hotel pre-authorises three hundred and checks out at one eighty. A fuel pump authorises one dollar and clears at sixty-four. A split shipment clears twice."])

S(dia(K(1, "the fix"), "A hold, not a debit; clearing moves the money", "ch1-fix", chip=chips("fix: hold $60 → $72", "clearing moves it to posted", "property: S1, L2")), [
 "C: The fix, outlined green. An approval inserts a hold of sixty dollars in the authorisation store. The incremental raises the same hold to seventy-two. On Thursday, the clearing matcher finds the hold by the network reference and, in one write, moves seventy-two dollars from the hold to the posted balance. Then it posts seventy-two in the ledger."], cls="dia")

S(dia(K(1, "the money, line by line"), "Available moved at the till; posted moved on Thursday", "holds"), [
 "C: Line by line. Monday: authorise sixty, hold sixty. Posted five hundred, available four hundred and forty. The tip: the hold becomes seventy-two, available four hundred and twenty-eight. Thursday: clearing seventy-two, matched by reference. Posted becomes four hundred and twenty-eight, the hold is released, and available stays four hundred and twenty-eight.",
 "C: Available moved at the till. Posted moved on Thursday, when the money really moved. And if Thursday never comes, the hold expires, after about seven days for most merchants and thirty for hotels and car hire."], cls="dia")

S(plain(K(1, "hold lifetimes"), "How long a promise lasts depends on the merchant", table(["Merchant type", "Typical final amount", "Hold lifetime (illustrative)"], [
  ["Restaurant, bar", "plus a tip, within a day or two", "7 days"],
  ["Fuel pump", "a small pre-authorisation, then the real fill", "7 days"],
  ["Hotel, car hire", "the stay or the rental, weeks later", "30 days"],
  ["Online, split shipment", "two or more clearings", "7 days after the last"]], "bt") +
  line("Release too early, and the customer spends money that is about to leave. Release too late, and they see less for a few days. Err late.", "a")), [
 "C: How long should a hold live? It depends on the merchant. A restaurant adds a tip within a day or two. A fuel pump authorises a small amount and clears the real fill. A hotel or a car hire clears weeks later. A split shipment clears more than once. So the lifetime comes from the merchant category, and these numbers are illustrative.",
 "C: The asymmetry decides the direction. Release too early, and the customer spends money that is about to leave. Release too late, and they see a little less for a few days. Err late."])

qs("Interviewer · the second-level push", "“The clearing record has no matching authorisation. Or it arrives after the hold expired.”", [
 "I: The clearing record has no matching authorisation. Or it arrives after the hold expired.", "[pause: 2.0]"])

S(plain(K(1, "the second fix"), "The file is the financial truth", '<div class="cards c3">'
  '<div class="cd grn"><h3>Reference, then fuzzy</h3><p>No reference? Match card, merchant, amount within ±20 %, within 7 days.</p></div>'
  '<div class="cd amb"><h3>No match: post anyway</h3><p>The network has already paid the merchant from our settlement account. Post, and queue it for review.</p></div>'
  '<div class="cd red"><h3>After expiry: post anyway</h3><p>It may take the account below zero: a modelled state, challenge 7. Expiry waits for the day\'s file.</p></div></div>' +
  line("Trap: one authorisation, one clearing record. Split shipments clear twice; some never clear; offline purchases clear with no authorisation.", "r")), [
 "C: Match by reference first. With no reference, fall back to the card, the merchant, an amount within twenty percent, and a seven-day window. And if nothing matches, the record still posts. The network has already paid the merchant from our settlement account, so the file is the financial truth. It goes to a review queue.",
 "C: A clearing that arrives after its hold expired posts too, and may take the account below zero. That is a modelled state, in challenge seven. And expiry waits for the day's file, so a hold is never released an hour before its own clearing arrives."])

say_slide("“Approval is a hold, not a debit. Available is posted minus holds, and clearing moves the real amount from hold to posted, matched by the network's reference. Holds that never clear expire; late clearing still posts.”", [
 "V: If asked, I'd say: approval is a hold, not a debit. Available is posted minus holds, and clearing moves the real amount from hold to posted. Holds that never clear expire, and late clearing still posts.", "[pause: 1.0]",
 "N: That fix creates the next question. A hold is a read and a write, and two can race."])

# ───────── Challenge 2 · two swipes, one balance ─────────
subchapter("7.2", "Challenge 2: Two swipes, one balance", ["N: Challenge two. Two authorisations for one account arrive at the same moment, and the money covers one: who decides?"])
qs("Interviewer · challenge 2 of 8", "“Two authorisations for one account arrive two milliseconds apart. The balance covers one of them. What happens?”", [
 "I: Two authorisations for one account arrive two milliseconds apart. The balance covers one of them. What happens?", "[pause: 2.0]"])

S(dia(K(2, "two swipes"), "Read, then write, is a race", "ch2-attack", q=True, red=True,
      extra=strip(("case", "Naive answer", "“Read the available balance, check it, insert the hold.”"),
                  ("case", "Break", "Between the read and the write, another decision reads the same balance."))), [
 "C: The naive answer: read the available balance, check it, insert the hold. The red authorisation store is read by two decisions before either writes."], cls="dia")

S(plain(K(2, "the trace"), "Both approved, by us", '<pre class="trace"><span class="t">12:00:00.000</span>fuel $80 reads available $100\n<span class="t">12:00:00.002</span>online $60 reads available $100\n<span class="t">12:00:00.004</span>80 within 100: hold $80\n<span class="t">12:00:00.006</span>60 within 100: hold $60 → <span class="bad">available −$40, both approved by us</span></pre>' +
  '<div class="hedge"><b class="t">Who does this</b>A joint account. A phone wallet and a physical card. A subscription renewing while the customer pays at a till. Rare per account; daily across eight million.</div>', q=True, red=True), [
 "C: The trace. Available is one hundred dollars. At noon exactly, a fuel pump for eighty reads one hundred. Two milliseconds later, an online order for sixty reads one hundred. Eighty fits: hold. Sixty fits: hold. Available is minus forty, and we approved both.",
 "C: A joint account does this. So does a phone wallet next to a physical card, or a subscription renewing while the customer pays at a till. Rare per account; daily across eight million."])

S(dia(K(2, "the fix"), "One conditional write in the account's partition", "ch2-fix",
      extra=strip(("fixb", "Mechanism", "If holds + amount fit within posted and the version is unchanged: insert the hold, record the message, add to holds total, bump the version. Else re-read and decide again."),
                  ("whyb", "Property", "S1 is decided in the one partition that owns the account. Per-account traffic is a few a minute, so a conflict is rare and cheap."))), [
 "C: The fix is one conditional write in the partition that owns the account. If the holds plus this amount still fit within posted, and the account's version is the one I read, then insert the hold, record the message, add to the holds total and bump the version, all at once. Otherwise nothing is written, and the decision reads again."], cls="dia")

S(dia(K(2, "sequence"), "One wins; the other re-reads and declines", "seq-ch2-reserve"), [
 "C: As a sequence. Both reserves carry version forty-one. The eighty dollar one commits first: hold placed, version forty-two. The sixty dollar one finds version forty-two and is refused. It re-reads: available twenty dollars, and sixty is more than twenty. Decline, insufficient funds. Exactly one place answered: is there enough?"], cls="dia")

S(plain(K(2, "the reserve, as code"), "The check and the write are one operation",
  '<pre class="code" data-lang="python"><span class="kw">def</span> reserve(store, acct, ref, amount):\n    <span class="kw">while</span> True:\n        a = store.get(<span class="st">"account"</span>, acct)\n        <span class="kw">if</span> a.holds + amount &gt; a.posted:\n            <span class="kw">return</span> <span class="st">"decline"</span>\n        <span class="kw">if</span> store.transact(acct, [cond(version=a.version),\n                put_hold(ref, amount), put_message(ref),\n                set(holds=a.holds + amount, version=a.version + 1)]):\n            <span class="kw">return</span> <span class="st">"approve"</span>   <span class="cm"># else: lost the race, read again</span></pre>' +
  strip(("whyb", "Why not a lock", "A lock gives the same safety with a lock service on the hot path and a lease to expire. The conditional write is the lock and the write in one step, in the store that owns the data."), cols="one")), [
 "C: In code. Read the account. If the holds plus the amount exceed posted, decline. Otherwise, one transaction in the account's partition: on condition that the version is unchanged, put the hold, put the message, and update the total and the version. If someone else won, read again.",
 "C: Why not a distributed lock? It gives the same safety, with a lock service on the hot path and a lease to expire when a server dies holding it. The conditional write is the lock and the write in one step."])

qs("Interviewer · the second-level push", "“A business account has 2,000 fleet cards on one balance, and on the busiest day they all buy fuel at 7 a.m.”", [
 "I: A business account has two thousand fleet cards on one balance, and on the busiest day they all buy fuel at seven in the morning.", "[pause: 2.0]"])

S(dia(K(2, "the second fix"), "Do the arithmetic first; then carve sub-limits", "escrow"), [
 "C: The arithmetic first. Two thousand cards, each one authorisation in ten minutes, is three point three a second on one key. One partition handles that easily, with a conflict now and then. So the honest first answer is: nothing changes.",
 "C: If it grows to hundreds a second, say a marketplace with virtual cards, carve sub-limits per card from the account. The account reserves budget to each card in blocks, refilled in the background, and most authorisations touch only the card's slice. The limit: a slice can run dry while the account still has money, so refill at half-used and fall back to the account-level reserve before declining."], cls="dia")

say_slide("“Check-and-reserve is one conditional write in the partition that owns the account, so two swipes can't both spend the same money. Per-account traffic is tiny, so it costs nothing; a big shared account gets sub-limits per card.”", [
 "V: If asked, I'd say: check-and-reserve is one conditional write in the account's partition, so two swipes can't spend the same money. It costs nothing, and a big shared account gets sub-limits per card.", "[pause: 1.0]",
 "N: That fix writes the message with the hold. The next question is what a message is, when it comes twice."])

# ───────── Challenge 3 · the same message twice, in the wrong order ─────────
subchapter("7.3", "Challenge 3: The same message twice, and in the wrong order", ["N: Challenge three. The network retries, and a reversal overtakes its original: how does each message take effect exactly once?"])
qs("Interviewer · challenge 3 of 8", "“The network retries an authorisation we already approved. And a reversal arrives before the authorisation it reverses. What happens?”", [
 "I: The network retries an authorisation we already approved. And a reversal arrives before the authorisation it reverses. What happens?", "[pause: 2.0]"])

S(dia(K(3, "twice, and out of order"), "Every arrival treated as new", "ch3-attack", q=True, red=True,
      extra=strip(("case", "Naive answer", "“Process messages as they arrive; a retry is a new request.”"),
                  ("case", "Break", "The gateway and the store key effects on arrival, not on the network's reference."))), [
 "C: The naive answer: process messages as they arrive, and a retry is a new request. The red gateway and store treat every arrival as new."], cls="dia")

S(plain(K(3, "the trace"), "A double hold, and a hold for a cancelled purchase", '<pre class="trace"><span class="t">18:30:00.000</span>authorise R-7731 $45: approved, hold placed\n<span class="t">18:30:00.090</span>our answer is lost on the link\n<span class="t">18:30:01.900</span>the network retries R-7731 → <span class="bad">a second hold: available down $90</span>\n<span class="t">19:02:10.120</span>reversal of R-8840 arrives first: <span class="bad">nothing to reverse, dropped</span>\n<span class="t">19:02:10.180</span>authorise R-8840 $45 → <span class="bad">a hold for a cancelled purchase, for seven days</span></pre>', q=True, red=True), [
 "C: Two traces. At half past six, R-seventy-seven-thirty-one for forty-five dollars is approved and its hold placed, but the answer is lost on the link. Almost two seconds later the network retries it, and the naive system places a second hold: available is down ninety.",
 "C: Then at two minutes past seven, a reversal of R-eighty-eight-forty arrives first: the merchant cancelled at once. Nothing to reverse, so it is dropped. Sixty milliseconds later the authorisation itself arrives and is approved: a hold for a purchase that was cancelled, for seven days."])

S(dia(K(3, "the fix"), "Keyed by the network's reference, written with the hold", "ch3-fix",
      extra=strip(("fixb", "Mechanism", "The message table is keyed by the network reference. A retry gets the stored answer. A reversal with no original is kept as a tombstone. The record is written in the same transaction as the hold."),
                  ("whyb", "Property", "S2: the effect is keyed by what the network calls the message, not by when it arrives. No crash can separate a hold from its record."))), [
 "C: The fix. The message table is keyed by the network's reference. Before acting, the decision looks the reference up. A retry gets the stored answer. A reversal whose original has not arrived is kept as a tombstone. And the message record is written in the same transaction as the hold, so no crash can leave one without the other."], cls="dia")

S(dia(K(3, "sequence"), "A reversal that arrives first", "seq-reversal"), [
 "C: As a sequence. The reversal of R-eighty-eight-forty arrives; the message table has nothing, so we store a tombstone and acknowledge. Sixty milliseconds later the authorisation arrives. Reserve? The store says: already reversed, no hold. We answer as the network expects, and nothing is held. And when the network retries it, it gets the stored answer again."], cls="dia")

S(plain(K(3, "what not to key on"), "Three keys that look right and are not", '<div class="cards c3">'
  '<div class="cd red"><h3>Arrival time</h3><p>A retry arrives later; a reversal arrives earlier. Time is exactly what varies.</p></div>'
  '<div class="cd red"><h3>Amount and merchant</h3><p>Two genuine coffees five minutes apart look identical. One would be swallowed.</p></div>'
  '<div class="cd red"><h3>Our own ID</h3><p>The network does not know it, so its retry cannot carry it.</p></div></div>' +
  line("The only key both sides share is the network's reference.", "a")), [
 "C: Three keys that look right and are not. Arrival time: a retry arrives later and a reversal earlier, so time is exactly what varies. A hash of the amount and the merchant: two genuine coffees five minutes apart look identical, and one would be swallowed. And our own generated I-D: the network does not know it, so its retry cannot carry it. The only key both sides share is the network's reference."])

qs("Interviewer · the second-level push", "“The partition fails over mid-write. Or the message table is purged, and a retry arrives a day later.”", [
 "I: The partition fails over mid-write. Or the message table is purged, and a retry arrives a day later.", "[pause: 2.0]"])

S(plain(K(3, "the second fix"), "One commit, and a long enough memory", '<div class="cards c3">'
  '<div class="cd grn"><h3>Failover</h3><p>The transaction commits on a quorum of replicas before the answer leaves: a new primary has both writes, or neither.</p></div>'
  '<div class="cd"><h3>Retention</h3><p>Keep message records longer than the network\'s retry and reversal windows: days. 20 M a day × 100 B × 30 days ≈ 60 GB.</p></div>'
  '<div class="cd amb"><h3>The backstop</h3><p>Past the window, clearing is the truth: a hold that should not exist expires; a clearing that should exist posts.</p></div></div>'), [
 "C: The transaction commits on a quorum of replicas before the answer leaves, so a new primary has both writes or neither. Message records are kept for longer than the network's retry and reversal windows, which are days. Twenty million a day, a hundred bytes each, for thirty days, is about sixty gigabytes. Cheap.",
 "C: And past that window, clearing is the backstop: a hold that should not exist expires, and a clearing that should exist posts."])

say_slide("“Every message is keyed by the network's reference, and its record is written in the same atomic step as the hold. A retry gets the stored answer; a reversal that arrives first waits as a tombstone for its original.”", [
 "V: If asked, I'd say: every message is keyed by the network's reference, and recorded in the same atomic step as the hold. A retry gets the stored answer, and an early reversal waits as a tombstone.", "[pause: 1.0]",
 "N: The money is now correct. The next question is about time: what if the answer itself is late?"])

# ───────── Challenge 4 · the model is slow tonight ─────────
subchapter("7.4", "Challenge 4: The model is slow tonight", ["N: Challenge four. The fraud model's tail jumps to almost two seconds: do we wait for it, ignore it, or something better?"])
qs("Interviewer · challenge 4 of 8", "“Your fraud model is at 1.8 seconds p99 tonight. What does the authorisation path do?”", [
 "I: Your fraud model is at one point eight seconds, at the ninety-ninth percentile, tonight. What does the authorisation path do?", "[pause: 2.0]"])

S(dia(K(4, "the slow model"), "Its tail becomes our tail", "ch4-attack", q=True, red=True,
      extra=strip(("case", "Naive answers", "“Wait for it: fraud matters more than latency.” Or: “Fail open.”"),
                  ("case", "Break", "The model scorer, on the critical path with no slice of its own."))), [
 "C: Two naive answers. Wait for it, because fraud matters more than latency. Or fail open. The red model scorer sits on the critical path with no limit of its own."], cls="dia")

S(plain(K(4, "the trace"), "Waiting hands the decision away; failing open hands it to the fraudster", '<pre class="trace"><span class="t">20:00</span>a model release doubles its feature fetches: p99 1.8 s\n<span class="t">wait</span>by 20:01, 30 % of answers pass 2 s → <span class="bad">stand-in for 450 a second, with no score at all</span>\n<span class="t">fail open</span>1,500 × 60 = <span class="bad">90,000 unscored decisions a minute</span>, and a fraud ring that notices</pre>' +
  '<div class="hedge"><b class="t">Label the numbers</b>Illustrative: the release, the 30 %, and the ring are a scenario, not a measurement.</div>', q=True, red=True), [
 "C: The trace. At eight in the evening, a model release doubles its feature fetches, and its tail goes to one point eight seconds. If we wait, by one minute past eight, thirty percent of our answers pass two seconds. The network stands in for four hundred and fifty authorisations a second, with limits we set months ago and no score at all.",
 "C: If we fail open, every decision is unscored: fifteen hundred a second, ninety thousand a minute, and a fraud ring probing with small purchases notices within minutes. These numbers are a scenario, illustrative."])

S(dia(K(4, "the fix"), "A slice of the budget, and a table for when it runs out", "ch4-fix",
      extra=strip(("fixb", "Mechanism", "Rules always run, in process. The model gets 60 ms; then the decision proceeds without it, by a fail-policy table with an hourly exposure cap per cell."),
                  ("whyb", "Property", "L1: the answer leaves inside 300 ms whatever the model does. The quality loss is bounded by the cap, priced, and owned."))), [
 "C: The fix. Rules always run, in process, in about ten milliseconds. The model gets a sixty millisecond slice, and at sixty the decision proceeds without it. What without it means is not an if-statement. It is a table, agreed in advance, with an hourly exposure cap on every cell."], cls="dia")

S(plain(K(4, "the fail policy"), "A table owned by risk and finance", table(["Situation", "Low amount, low-risk merchant", "High amount or risky merchant"], [
  ["Model late", "rules-only decision", "rules only, stricter limits"],
  ["Counters missing", "conservative card-not-present limits", "decline card-not-present; step up"],
  ["Rules engine fails", "approve within stand-in-like limits", "decline, or step up the customer"],
  ["We miss the deadline", "network stand-in", "network stand-in"]], "bt") +
  line("Every cell has an hourly exposure cap. Degraded approvals are counted against it, live.", "a")), [
 "C: The table. Model late, small amount at a low-risk merchant: decide on rules alone. Large amount or a risky merchant type: rules with stricter limits. Counters missing: conservative limits for card-not-present. Rules engine failing: approve small amounts within stand-in-like limits, decline or step up the rest. And if we miss the deadline entirely, the network stands in.",
 "C: Every cell has an hourly exposure cap, and the decision service counts degraded approvals against it as they happen."])

S(dia(K(4, "sequence"), "The cut-off, then the table", "seq-ch4-cutoff"), [
 "C: As a sequence. Ask the model, with a cut-off of sixty. Rules are done at eighteen milliseconds. At sixty, no score: proceed. The table row: model late, sixty dollars, restaurant. Rules only, the cap is fifty thousand dollars an hour, seven thousand two hundred used. Approve, flagged degraded, counted. And when the score arrives at one point eight seconds, it is logged and ignored."], cls="dia")

S(plain(K(4, "why not hedge"), "Sending the model call twice is not the answer", '<div class="cards c2">'
  '<div class="cd amb"><h3>Hedged requests</h3><p>Send the call to two scorers and take the first answer. It trims a random tail.</p></div>'
  '<div class="cd red"><h3>Why not tonight</h3><p>Tonight the slowness is the model itself. Hedging doubles its load exactly when it is struggling, and every copy is slow.</p></div></div>' +
  line("A cut-off bounds our latency whatever the cause. Hedging only helps when the slowness is random.", "a")), [
 "C: Someone usually suggests hedging: send the model call to two scorers and take the first answer. It trims a random tail, one slow machine among many. Tonight the slowness is the model itself, so every copy is slow, and hedging doubles its load exactly when it is struggling. A cut-off bounds our latency whatever the cause."])

qs("Interviewer · the second-level push", "“It lasts all evening and the cap runs out. And who decided those numbers?”", [
 "I: It lasts all evening, and the cap runs out. And who decided those numbers?", "[pause: 2.0]"])

S(plain(K(4, "the second fix"), "Tighten by cell; own it before the incident", '<div class="cards c3">'
  '<div class="cd"><h3>Risk</h3><p>Sets the limits in each cell from loss data; reviews them monthly.</p></div>'
  '<div class="cd amb"><h3>Finance</h3><p>Signs the cap: the most we accept losing while degraded.</p></div>'
  '<div class="cd grn"><h3>Engineering</h3><p>Makes each cell a setting, counts every degraded decision, pages at half the cap, rolls the model back by version.</p></div></div>' +
  line("When a cell's cap is used: step-up, then lower limits, then decline. The conversation happens before the incident, not during it.", "r")), [
 "C: When a cell's cap is used up, that cell tightens: first a step-up, asking the cardholder to confirm in the app, then lower limits, then decline. And the first runbook step is rolling the model back by re-pointing its version.",
 "C: Who decided? Risk sets the limits in each cell from loss data. Finance signs the cap. Engineering makes each cell a setting, counts every degraded decision, and pages at half the cap. At the manager bar, the point is that this conversation happens before the incident, not during it."])

say_slide("“The model gets a fixed slice of the budget, and the decision never waits past it. When it's late, a table owned by risk and finance decides, under an hourly exposure cap. We answer in time, and we know what that costs.”", [
 "V: If asked, I'd say: the model gets a fixed slice of the budget, and we never wait past it. When it's late, a table owned by risk and finance decides, under an hourly cap.", "[pause: 1.0]",
 "N: Features are the model's other input. The next question is how fresh they are."])
