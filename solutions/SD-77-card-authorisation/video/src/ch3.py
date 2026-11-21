from dsl import *
import dsl

def th(): dsl.SL[-1]["cls"] = (dsl.SL[-1]["cls"] + " theory").strip()

chapter(3, "Theory", 2, "What makes this problem hard, in words that outlive any product name", [
 "C: A short theory chapter before the design, so the design can lean on it. What this system is and is not, the properties, the central tension, seven mechanisms, an options matrix, and the failure catalogue."]); th()

key("Theory · 1 of 6 · what it is", "An issuer's authorisation system answers the network <em>before its deadline</em>, reserves the amount as a <em>hold</em> against the <em>available balance</em>, and <em>later settles the real amount</em> from the clearing file.", [
 "V: An issuer's authorisation system answers the network before its deadline, reserves the amount as a hold against the available balance, and later settles the real amount from the clearing file.", "[pause: 1.0]",
 "C: Every clause is load-bearing. Before its deadline: miss it, and the network decides for us. A hold: no money moves at the till. Available balance: posted balance minus the holds. And later settles the real amount: clearing can differ, or never come."], cls="theory")

S(plain("Theory · 1 of 6 · what it is not", "Four things it is confused with", '<div class="cards c2">'
  '<div class="cd"><h3>Not a payment</h3><p>No money moves at authorisation. Clearing and settlement move it, days later.</p></div>'
  '<div class="cd amb"><h3>Not a debit</h3><p>A hold can grow, shrink, be reversed, clear for a different amount, or expire.</p></div>'
  '<div class="cd red"><h3>Not the fraud model</h3><p>The model is one input, with a budget. The decision is ours, with or without it.</p></div>'
  '<div class="cd"><h3>Not the core ledger</h3><p>Holds live next to the decision. Posted money lives in the ledger. The two are reconciled.</p></div></div>'), [
 "C: Four neighbours it is confused with. It is not a payment: no money moves at authorisation. It is not a debit: a hold can grow with a tip, shrink, be reversed, clear for a different amount, or simply expire.",
 "C: It is not the fraud model: the model is one input with a budget, and the decision happens with or without it. And it is not the core ledger: holds live next to the decision, posted money lives in the ledger, and the two are reconciled every day."], cls="theory")

S(plain("Theory · 2 of 6 · the two properties", "State safety and liveness separately",
  '<div class="prop safe"><div class="lbl">Safety · must never happen</div><p><b>S1</b> Our own approvals take an account\'s available balance below zero.<br><b>S2</b> A network message takes effect twice: two holds, two postings.<br><b>S3</b> A decision cannot be reproduced: its inputs and versions are lost.</p></div>'
  '<div class="prop live"><div class="lbl">Liveness · must eventually happen</div><p><b>L1</b> Every authorisation gets an answer inside the deadline: ours, degraded if need be, never silence.<br><b>L2</b> Every hold ends: cleared, reversed or expired.<br><b>L3</b> A rule change takes effect within minutes.</p></div>'), [
 "C: Safety, what must never happen. S-one: our own approvals never take an account below zero. Note the word own: the network's decisions will, and that is challenge seven. S-two: no network message takes effect twice. S-three: no decision we cannot reproduce.",
 "C: Liveness, what must eventually happen. L-one: every authorisation gets an answer inside the deadline, degraded if need be, never silence. L-two: every hold ends. L-three: a rule change takes effect within minutes. Every fix from here names which one it serves."], cls="theory")

S(dia("Theory · 3 of 6 · the central tension", "Decision quality against the deadline", "tension"), [
 "C: The central tension. Each signal buys quality and costs time. Rules are ten milliseconds. The model adds tens more. Rich aggregates on request would add hundreds. The curve flattens: past our three-hundred millisecond target, the gain is small.",
 "C: And past the network's deadline, on the right, the network decides with far less information than we have. So the design spends the deadline deliberately, and writes down in advance what happens when a step is late."], cls="dia theory")

def mech(n, name, protects, how, rules, costs, say, live=True):
    S(plain(f"Theory · 4 of 6 · mechanism {n} of 7", name,
        f'<div class="prop {"live" if live else "safe"}"><div class="lbl">Property it protects</div><p>{protects}</p></div>'
        f'<div class="prop"><div class="lbl">How it works</div><p>{how}</p></div>'
        f'<div class="prop safe"><div class="lbl">Failure it rules out</div><p>{rules}</p></div>'
        f'<div class="prop" style="border-left-color:#d18f1c"><div class="lbl" style="color:#a86a12">What it costs</div><p>{costs}</p></div>'), say, cls="theory")

mech(1, "Holds as ledger entries, with expiry", "S1 and L2.", "An approval inserts a hold; available = posted − active holds. Incrementals raise it, reversals release it, clearing moves it to posted, a lifetime by merchant type ends it.",
     "Debiting at the till; tip and currency differences; money stuck forever.", "A hold lifecycle and an expiry job; a “pending” amount the customer must understand.", [
 "C: Mechanism one, holds with expiry. It protects S-one and L-two. An approval inserts a hold, and available is posted minus active holds. Incrementals raise it, reversals release it, clearing moves it to posted, and a lifetime by merchant type ends it. It rules out debiting at the till, and money stuck forever. It costs a lifecycle, an expiry job, and a pending amount the customer must understand."], live=False)
mech(2, "Idempotency on the network reference, in any order", "S2.", "A message table keyed by the network's reference. A retry returns the stored answer. A reversal that arrives first is kept as a tombstone for its original.",
     "A retried request placing two holds; an early reversal lost.", "A message store kept for longer than the network's retry window: days, not minutes.", [
 "C: Mechanism two, idempotency on the network reference. It protects S-two. A message table keyed by the reference the network gives us. A retry returns the stored answer. A reversal that arrives before its original is kept as a tombstone. It rules out a retry placing two holds, and an early reversal being lost. It costs a message store kept for days."], live=False)
mech(3, "A per-account atomic reserve", "S1, and S2 with mechanism 2.", "One conditional write in the partition that owns the account: check available, insert the hold, record the message, bump the version.",
     "Two concurrent swipes both seeing the same balance.", "A store partitioned by account; a shared business account becomes a hot key.", [
 "C: Mechanism three, the per-account atomic reserve. One conditional write, in the partition that owns the account: check available, insert the hold, record the message, bump the version. It rules out two concurrent swipes both spending the same money. It costs a store partitioned by account, and a shared business account becomes a hot key."], live=False)
mech(4, "A latency budget with a fail-policy table", "L1.", "Each step gets a slice; rules run in process; the model has a 60 ms cut-off; a table says what to decide when a step is late, with an hourly exposure cap.",
     "A slow dependency making us miss the deadline.", "Degraded decisions with real exposure; a policy that risk and finance must own.", [
 "C: Mechanism four, a latency budget with a fail-policy table. It protects L-one. Each step gets a slice, rules run in process, the model has a sixty millisecond cut-off, and a table says what we decide when something is late, with an hourly exposure cap. It rules out a slow dependency making us miss the deadline. It costs degraded decisions with real money attached, and a policy that risk and finance must own."])
mech(5, "Two-speed features", "Decision quality, and S3.", "Burst counters read and incremented inline, in one round trip; richer aggregates from the stream, seconds late; every feature value logged with the decision.",
     "A stream that lags behind a burst; training on values the model never saw.", "A counter store on the hot path, and a second pipeline.", [
 "C: Mechanism five, two-speed features. Burst counters are read and incremented inline, in one round trip. Richer aggregates come from the stream, seconds late. And every feature value is logged with the decision. It rules out a stream lagging behind a burst of fraud, and training on values the model never saw. It costs a counter store on the hot path."])
mech(6, "Rules as versioned data", "L3 and S3.", "A sandboxed expression language. Backtest, shadow, slice, enforce. A kill switch, an expiry, and the rule-set version recorded on every decision.",
     "A deploy to block an attack; one bad rule declining everyone.", "Tooling. And labels arrive in 30 to 90 days, so shadow cannot measure false positives.", [
 "C: Mechanism six, rules as versioned data. A sandboxed expression language, a staged rollout of backtest, shadow, slice and enforce, a kill switch, an expiry, and the version on every decision. It rules out a deploy to block an attack, and one bad rule declining everyone. It costs tooling, and an honest limit: labels arrive months later."])
mech(7, "The clearing file as financial truth", "L2, and books that agree.", "Match by reference, then fuzzy. Move the amount from hold to posted. Post what has no match. Record stand-in decisions even when they overdraw.",
     "Holds that never end; refusing advices or late clearing.", "An unmatched queue both ways; over-limit handling and collections.", [
 "C: Mechanism seven, the clearing file as financial truth. Match by reference, then fuzzy. Move the amount from hold to posted. Post what has no match. And record the network's stand-in decisions even when they overdraw. It rules out holds that never end, and books that disagree with the network's. It costs an unmatched queue, and over-limit handling."], live=False)

S(plain("Theory · 5 of 6 · the options", "Where the decision and the money live", table(["Approach", "In time?", "Clearing differs?", "Concurrent swipes?", "Rules, no deploy?", "Fails when"], [
  ("rej", ["A · Debit the core ledger at authorisation", "ledger's tail", "<b>no</b>", "yes", "no", "tips, reversals; the ledger's batch window"]),
  ("rej", ["B · A synchronous chain of remote calls", "<b>no</b>", "yes", "yes", "yes", "any one slow call means stand-in"]),
  ("rej", ["C · Holds in the core ledger, scoring with a budget", "mostly", "yes", "yes", "yes", "the ledger's nightly batch on our path"]),
  ("pick", ["D · Own authorisation store; stateless decision; rules in process; model with a cut-off; events to the ledger", "<b>yes</b>", "<b>yes</b>", "<b>yes</b>", "<b>yes</b>", "the store and the ledger drift apart"]),
  ("rej", ["E · Let the processor decide with uploaded rules", "yes", "theirs", "theirs", "limited", "our fraud needs outgrow its language"])], "bt sm mx")), [
 "C: Five ways to place the decision and the money. A, debit the core ledger at authorisation: wrong the moment clearing differs, and the ledger's batch window sits on our path. B, a chain of synchronous remote calls: correct, but the tails add up, and any slow link means stand-in.",
 "C: C, holds in the core ledger with a budget for scoring: mostly works, but the ledger's nightly posting and maintenance still sit on the authorisation path. E, let the processor decide with rules we upload: fine for a launch, until our fraud needs outgrow its rule language.",
 "V: I pick D: our own authorisation store, next to a stateless decision service.", "[pause: 0.8]"], cls="theory")

S(plain("Theory · 5 of 6 · the pick, and what it gives up", "D, with E as the honest launch answer", '<div class="cards c2">'
  '<div class="cd grn"><h3>Why D</h3><p>The ledger is off the hot path. Holds and messages are reserved in one write. Rules change as data. The model can be late without making us late.</p></div>'
  '<div class="cd red"><h3>What it gives up</h3><p>A second copy of balances, which must be reconciled with the ledger every day. E needs none of this, and fits a launch.</p></div></div>' +
  line("Pick E for the first months of a new card programme; move to D when fraud needs its own model.", "a")), [
 "C: Why D. The ledger is off the hot path. Holds and messages are reserved in one write. Rules change as data. And the model can be late without making us late. What it gives up: a second copy of balances, which must be reconciled with the ledger every day.",
 "C: And I'd say plainly: for the first months of a new card programme, E is the right answer, and it appears in the build cost. Move to D when fraud needs our own model."], cls="theory")

S(plain("Theory · 6 of 6 · the failure catalogue", "What will go wrong", table(["#", "Failure", "Becomes"], [
  ["F1", "A tip, a currency difference, a hold that never clears", "<b>Challenge 1</b>"],
  ["F2", "Two swipes on one balance; a fleet account", "<b>Challenge 2</b>"],
  ["F3", "A retried request; a reversal before its original", "<b>Challenge 3</b>"],
  ["F4", "The model slow tonight", "<b>Challenge 4</b>"],
  ["F5", "A burst of fraud seconds apart", "<b>Challenge 5</b>"],
  ["F6", "A new attack at 2 a.m.; a bad rule", "<b>Challenge 6</b>"],
  ["F7", "We are down; stand-in; a late, duplicated clearing file", "<b>Challenge 7</b>"],
  ["F8", "Declines doubled and nobody knows why", "<b>Challenge 8</b>"],
  ["F9", "Card numbers in our systems", "dismissed: tokens only, from requirement 6"]], "bt sm")), [
 "C: The failure catalogue, which becomes the challenge list. A tip, and a hold that never clears. Two swipes on one balance. A retry, and a reversal before its original. The model slow tonight. A burst seconds apart. A new attack at two in the morning. Stand-in, and a late clearing file. And declines doubling while the dashboards stay green.",
 "C: The ninth, card numbers in our systems, I dismiss: we only ever see tokens."], cls="theory")

S(plain("Theory · what each mechanism serves", "Every mechanism names its property", table(["Mechanism", "Serves", "Where it returns"], [
  ["M1 Holds with expiry", "S1, L2", "challenges 1 and 7"],
  ["M2 Network reference", "<b>S2</b>", "challenges 3 and 7"],
  ["M3 Per-account reserve", "<b>S1</b>", "challenge 2"],
  ["M4 Budget and fail table", "<b>L1</b>", "challenge 4"],
  ["M5 Two-speed features", "quality, S3", "challenge 5"],
  ["M6 Rules as data", "L3, S3", "challenges 6 and 8"],
  ["M7 Clearing as truth", "L2", "challenges 1 and 7"]], "bt sm") +
  grade("A mechanism with no stated property is decoration. Say which one each fix serves.")), [
 "N: Good theory has a consequence for the design. Every mechanism here names the property it serves and where it comes back.",
 "C: That is the vocabulary. On to the messages and the data."], cls="theory")
