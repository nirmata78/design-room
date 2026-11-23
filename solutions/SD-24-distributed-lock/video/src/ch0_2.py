from dsl import *

# ───────────────────────── 0 · cold open ─────────────────────────
chapter(0, "Cold open", -1, "Design a distributed lock service", [
 "C: A lock service sounds like a small problem. A key, an owner, an expiry. This question is not testing whether you can draw that. It is testing whether you notice what a lock cannot promise, and what you do about it."])

qs("Interviewer · the prompt", "“Design a distributed lock service that other teams use to make sure only one process does a thing at a time.”", [
 "I: Design a distributed lock service that other teams use to make sure only one process does a thing at a time.", "[pause: 1.5]"])

S(dia("Why it is harder than it looks", "The lock service did everything right, and it still failed", "pause-unfenced",
      chip=chips("lease 10 s", "pause 15 s", "two writers")), [
 "C: Here is the hook. Holder A takes a lock and gets token forty-one. Then A freezes, for fifteen seconds. A garbage collection pause is enough.",
 "C: At ten seconds the lease expires. The lock service is correct to expire it. Holder B asks, and gets token forty-two. B writes.",
 "C: At fifteen seconds A wakes up. It has no idea time passed. It writes too. Two writers. The network was fine and no component misbehaved. The lock service's idea of who holds the lock and the resource's idea of who may write are different things, and nothing connects them."])

S(plain("Before the design", "What this question grades", table(["Axis", "Weak signal", "Strong signal"], [
  ["<b>Requirements</b>", "A key in a cache with an expiry", "Asks what a double hold costs: efficiency lock or correctness lock"],
  ["<b>Correctness</b>", "“Tune the lease length”", "Names the pause, puts a token at the resource"],
  ["<b>Trade-offs</b>", "Picks a product", "Options with the failure that rules each out"],
  ["<b>Depth</b>", "Stops at “uses Raft”", "Why the token is the log index; what a new leader assumes"],
  ["<b>Operations</b>", "Watches CPU and uptime", "Fenced-out writes, error budget, people and months"]], "bt sm sig") +
  grade("The signal is in the gap between the lock and the resource. Draw the consensus group quickly and spend the time there.")), [
 "N: Five axes. The weak signal on each is the same shape: the happy path, drawn well. The strong signal is what happens when the happy path fails.",
 "C: I will keep that table in mind. Correctness and operations are where I plan to spend the most time."], cls="")

key("The thesis", "A lock service says who <em>should</em> be working. Only the <em>resource</em> says who is <em>allowed</em> to write.", [
 "V: A lock service says who should be working. Only the resource says who is allowed to write.", "[pause: 1.0]",
 "C: So my design has three layers. A lease, so a dead holder frees its lock. Consensus, so the record of who holds it survives failures and gives an order. And a fencing token, checked at the resource, which is what actually makes it safe."])

S(plain("The order I will follow", "Scope, numbers, theory, a simple design, then I break it",
  '<div class="ribbon" style="margin-top:14pt">' + "".join(f"<span>{x}</span>" for x in STAGES) + '</div>' +
  '<div class="cards c3" style="margin-top:18pt"><div class="cd"><h3>First</h3><p>Requirements and scope. Numbers. A short theory chapter.</p></div>'
  '<div class="cd grn"><h3>Then</h3><p>API and data. A high-level design in three versions, each answering the one before.</p></div>'
  '<div class="cd red"><h3>Most of the time</h3><p>Seven challenges that break the design. A build cost. A recap.</p></div></div>'), [
 "C: I'll go in this order. Requirements and scope. Then numbers. Then a short theory chapter, because the design leans on it. Then API and data, and a high-level design in three versions, each answering the objection to the one before.",
 "C: Then the part I care most about: seven challenges that break the design, one at a time, where each fix creates the next question. A build cost, because someone has to own this. And a recap."])

# ───────────────────────── 1 · requirements ─────────────────────────
chapter(1, "Requirements and scope", 0, "Ask first. Cut on purpose. Put numbers on it.", [
 "C: Before I draw anything, I want to ask six questions. Each answer will change the design."])

def clar(n, q, a, say):
    S(f'<div class="who">Clarifying question {n} of 6</div><div class="qq">{q}</div><div class="ans">{a}</div>', say, cls="qs")

clar(1, "Who calls this, and for what?", "Internal teams. Background workers electing a leader, per-entity exclusion before a write, and some “run this job once” schedulers.", [
 "C: Who calls this, and for what?",
 "I: Internal teams. Background workers electing a leader. Per-entity exclusion before a write. And some run-this-job-once schedulers.",
 "C: Three different uses. Leader election wants a long hold. Exclusion before a write wants a short one. Run-once wants no waiting at all. One API has to serve all three."])
clar(2, "What happens if two holders act at once?", "Depends on the team. For some it corrupts records. For some it wastes an hour of compute. Tell me how you would find out.", [
 "C: What happens if two holders act at once?",
 "I: It depends on the team. For some it corrupts records. For some it wastes an hour of compute. I'd like you to tell me how you would find out.",
 "C: That is the most important answer so far. It splits locks into two kinds. If a double hold only wastes work, I call it an efficiency lock. If it corrupts data, it is a correctness lock. They need very different designs, and I'll ask every team which one they have."])
clar(3, "What is the scale?", "About 10,000 acquisition attempts a second, around 5,000 lock names, holds from 100 ms to 30 s, default lease 10 s.", [
 "C: And the scale?",
 "I: About ten thousand acquisition attempts a second. Around five thousand lock names. Holds from a hundred milliseconds to thirty seconds. Default lease, ten seconds.",
 "C: Attempts, not grants. I'll use that difference in the estimates."])
clar(4, "Latency, availability, failure?", "p99 acquisition under 20 ms. Survive the loss of a minority of nodes. One region, three zones. Multi-region is a later question.", [
 "C: Latency, availability and failure?",
 "I: p99 acquisition under twenty milliseconds. It must survive the loss of a minority of nodes. One region, three zones. Multi-region is a later question.",
 "C: Twenty milliseconds in one region is a quorum round trip, not a cross-region one. That rules out stretching one group across regions."])
clar(5, "What are the protected resources?", "Mostly SQL databases and an object store. A few call partner HTTP APIs. Callers are JVM services. Assume pauses up to 15 s in the tail: a fact, not a tuning problem.", [
 "C: What are the resources being protected, and who calls?",
 "I: Mostly SQL databases and an object store. A few call partner H-T-T-P A-P-Is. Callers are J-V-M services. Assume stop-the-world pauses up to fifteen seconds in the tail. That is a fact, not a tuning problem.",
 "C: Good. Two things. The pause is now a requirement, so the design must be safe when a holder stops for fifteen seconds. And partner A-P-Is are a problem I will come back to."])
clar(6, "Several locks at once? Shared mode? Strict order?", "Several at once: some callers do, tell me what you would say. Shared mode: no. Strict first-come order: not required.", [
 "C: Do callers need several locks at once, shared read locks, or strict order?",
 "I: Several at once, some do. Tell me what you'd say. Shared mode, no. Strict first-come order is not required.",
 "C: I'll scope out shared mode. I'll push back on several at once, and explain why in challenge six."])

S(plain("Requirements · functional", "Five things the service must do", '<div class="cards c3">'
  '<div class="cd"><h3>FR1 · Acquire</h3><p>An exclusive lock on a name. Bounded wait. Try-once is a wait of zero.</p></div>'
  '<div class="cd"><h3>FR2 · Hold and renew</h3><p>Keep the lease alive while working. Learn quickly if it is lost.</p></div>'
  '<div class="cd"><h3>FR3 · Release</h3><p>Release, and free a dead holder\'s locks automatically.</p></div>'
  '<div class="cd amb"><h3>FR4 · Fence</h3><p>Every grant carries a strictly increasing token for the resource.</p></div>'
  '<div class="cd grn"><h3>FR5 · Inspect and revoke</h3><p>Operators see who holds a name and can force-revoke, audited.</p></div></div>'), [
 "C: Functionally, five things. One, acquire an exclusive lock on a name, with a bounded wait. Two, hold it and renew it, and find out fast if it is lost. Three, release it, and have a dead holder's locks freed automatically.",
 "C: Four, and this is the one people forget: every grant carries a strictly increasing token that the caller can hand to the resource. And five, operators can inspect a name and force-revoke it, with an audit trail. Each of these gets its own numbered flow later."])

S(plain("Requirements · non-functional", "The numbers, and what each is for", '<p class="chips">all initial targets, not measurements</p><div class="tiles" style="--n:4">'
  '<div class="tile"><b>&lt; 20 ms</b><span>acquire p99, because locks sit in a request path</span></div>'
  '<div class="tile"><b>99.99%</b><span>acquire availability: about 4.3 minutes a month</span></div>'
  '<div class="tile blue"><b>10 s</b><span>default lease, capped at 60 s</span></div>'
  '<div class="tile blue"><b>2 of 5</b><span>replicas can be lost with no manual action</span></div></div>'), [
 "C: The numbers. They are initial targets, and I'll say so once for this chapter: none of these is a measurement.",
 "C: Acquire p99 under twenty milliseconds, because a lock sits inside someone's request. Availability of ninety-nine point nine nine percent, about four point three minutes a month. A default lease of ten seconds, capped at sixty. And survive the loss of two of five replicas without anyone being paged to fix it."])

S(plain("Requirements · behaviour", "Three promises that are not numbers", '<div class="cards c3">'
  '<div class="cd red"><h3>Fail closed</h3><p>If the service cannot decide, the protected operation does not proceed.</p></div>'
  '<div class="cd amb"><h3>Free within one lease</h3><p>A dead holder\'s name is available again within one lease.</p></div>'
  '<div class="cd"><h3>Tokens never go back</h3><p>Strictly increasing per name, even after a disaster-recovery rebuild.</p></div></div>'), [
 "C: Three promises that are not numbers. If the service cannot decide, the protected operation does not proceed. That is failing closed, and it is a choice I'm making now, not later.",
 "C: A dead holder's name frees within one lease. And tokens never go backwards, including after a disaster recovery. That last one sounds obscure. It will matter in challenge four."])

S(plain("Requirements · scope", "In scope, out of scope", chips("exclusive named leases", "sessions", "tokens", "operator tools") +
  '<div class="scope2"><div class="in"><h3>In scope</h3><ul><li>Exclusive named leases, bounded wait</li><li>Sessions and heartbeats</li><li>Fencing tokens</li><li>Operator inspect and revoke</li><li>One region, per-tenant quotas</li></ul></div>'
  '<div class="out"><h3>Out of scope, on purpose</h3><ul><li>Shared and read-write modes</li><li>Atomic multi-name acquire</li><li>Cross-region consensus</li><li>A general key-value store</li></ul></div></div>'), [
 "C: In scope: exclusive named leases with a bounded wait, sessions, tokens, operator tools, one region, and per-tenant quotas.",
 "C: Out of scope, and I'm saying so on purpose. Shared and read-write modes: I'll add them behind the same A-P-I if someone needs them. Atomic multi-name acquire: that needs a transaction across groups, and I'll push back. Cross-region consensus: a quorum across regions cannot meet twenty milliseconds. And a general-purpose key-value store. That last one I'll write down as a non-goal, because it is how lock services get ruined."])

S(plain("Requirements · the split that runs through everything", "Two kinds of lock", '<div class="cards c2">'
  '<div class="cd grn"><h3>Efficiency lock</h3><p>A double hold wastes work: a job runs twice, an email is sent twice.</p><p><b>Needs:</b> usually avoids it. Occasional failure is acceptable.</p></div>'
  '<div class="cd red"><h3>Correctness lock</h3><p>A double hold corrupts data: two writers, a lost update, a double charge.</p><p><b>Needs:</b> a token checked at the resource. No exceptions.</p></div></div>' +
  line("Most lock requests are idempotency problems in disguise. I ask which kind first.", "a")), [
 "C: This split runs through everything that follows. An efficiency lock avoids duplicate work. If it fails once in a while, you waste some compute. A correctness lock protects data. If it fails, you corrupt something.",
 "C: I treat them differently, and I ask every team which they have. Many say correctness and mean efficiency. Some say efficiency and mean correctness. Most of what people call a lock problem is really an idempotency problem, and I'll come back to that."])

key("The core", "The core is four things: a <em>lease</em>, a <em>replicated record</em>, a <em>token</em>, and a <em>check at the resource</em>.", [
 "V: The core is four things. A lease that frees itself. A consensus-replicated record of who holds it. A token that orders the grants. And a check at the resource.", "[pause: 0.8]",
 "N: Notice what the candidate did in six minutes. They asked what a double hold costs, cut four things out loud, and attached numbers. That is the framing signal."])

# ───────────────────────── 2 · estimates ─────────────────────────
chapter(2, "Estimates", 1, "Every number is arithmetic, with a label. Each one changes a decision.", [
 "C: Now the numbers. Every one is arithmetic from the inputs, and carries a label: given, illustrative, or an initial target. Each one has to change a decision, or I'll drop it."])

S(plain("Estimates · 1 of 10 · rate", "Peak, not average", '<div class="tiles" style="--n:3"><div class="tile blue"><b>10,000</b><span>attempts a second, given</span></div>'
  '<div class="tile"><b>× 3</b><span>peak factor, illustrative: top-of-hour storms</span></div><div class="tile"><b>30,000</b><span>attempts a second at peak</span></div></div>' +
  line("Size for the peak. A lock service that fails at the top of the hour fails when it matters.", "r")), [
 "C: Ten thousand attempts a second, given. Multiply by a peak factor of three, which I'm assuming, because work tends to start at the top of the hour. That is thirty thousand at peak.",
 "C: Decision: I size for the peak, not the average."])

S(plain("Estimates · 2 of 10 · the ceiling nobody states", "One holder per name caps the whole system", table(["Quantity", "Arithmetic", "Label"], [
  ["Held at once, at most", "1 holder × 5,000 names = <b>5,000</b>", "derived"],
  ["Grants a second, at most", "5,000 ÷ 0.5 s mean hold = <b>10,000</b>, only if every name is always held", "derived"],
  ["So most attempts…", "cannot succeed: they fail, or wait", "consequence"]], "bt") +
  line("The lock, not the service, is the limit.", "a")), [
 "C: Here is a number the prompt hides. One holder per name, around five thousand names. So at most five thousand locks can be held at any instant.",
 "C: With a mean hold of half a second, that caps grants at ten thousand a second, and only if every name is always held. So most of the ten thousand attempts cannot succeed. They fail, or wait.",
 "C: Decision: the A-P-I needs a bounded wait and an explicit try-once, because failure is the normal case on a busy name."])

S(plain("Estimates · 3 of 10 · Little's law", "What is held at once", table(["Quantity", "Arithmetic", "Label"], [
  ["Grants a second", "40% of 10,000 attempts = <b>4,000</b>", "illustrative"],
  ["Held at once", "4,000 × 0.5 s = <b>2,000 locks</b>", "Little's law: L = λ × W"],
  ["Long holds", "2% × 4,000 = 80 a second × 20 s = 1,600 locks", "illustrative"],
  ["Short holds", "3,920 × 0.1 s ≈ 392 locks", "illustrative"]], "bt")), [
 "C: Assume forty percent of attempts succeed: four thousand grants a second. Little's law says the number held at once is the arrival rate times the time held: four thousand times half a second, two thousand locks.",
 "C: Split that. Two percent of grants are long holds, about twenty seconds, think leader election: eighty a second times twenty is sixteen hundred. The short ones are about four hundred. Almost all the held locks are the long ones. Remember that for renewals."])

S(plain("Estimates · 4 of 10 · state size", "The state is tiny", chips("5,000 entries", "× 200 B", "≈ 1 MB") + '<div class="tiles" style="--n:3">'
  '<div class="tile blue"><b>~1 MB</b><span>held and waiting, illustrative</span></div><div class="tile blue"><b>memory</b><span>the whole state, with a log and snapshots on disk</span></div><div class="tile"><b>ms</b><span>to snapshot</span></div></div>' +
  line("So we shard for throughput and blast radius. Never for capacity.")), [
 "C: Five thousand entries at about two hundred bytes each is one megabyte. The whole state fits in memory and snapshots in milliseconds.",
 "C: Decision, and a common mistake to avoid: we shard for write throughput and for blast radius. We never shard because the data is big. It is not."])

S(plain("Estimates · 5 of 10 · writes", "What goes through consensus", table(["Quantity", "Arithmetic", "Label"], [
  ["Grant + release", "2 × 4,000 = <b>8,000 / s</b> average", "illustrative"],
  ["At peak", "× 3 = <b>24,000 / s</b>", "illustrative"],
  ["All-in", "+ waiter enqueues and expiries ≈ <b>30,000 / s</b>", "illustrative"],
  ["Failed try-once attempts", "answered by the leader under its lease: no log entry", "design choice"]], "bt")), [
 "C: Each grant is one committed write, and so is each release. Two times four thousand is eight thousand writes a second on average. Times three is twenty-four thousand at peak. Add waiter enqueues and expiries and I call it thirty thousand all-in.",
 "C: Failed try-once attempts don't write. The leader answers them from memory under its leader lease. That is why the attempts number is so much larger than the writes number."])

S(plain("Estimates · 6 of 10 · groups", "How many consensus groups", chips("15,000 writes/s a group", "initial target, to be measured") + table(["Quantity", "Arithmetic", "Label"], [
  ["One group's ceiling", "~15,000 committed writes/s, batched fsync on SSD", "initial target"],
  ["Groups needed", "30,000 ÷ (15,000 × 0.5 headroom) = <b>4</b>", "derived"],
  ["Hash slots", "64, so a slot can move later", "design choice"]], "bt") +
  line("One group nearly carries the average. We shard for the peak, and so a bad group takes a quarter, not everything.", "a")), [
 "C: One group's ceiling is the number I trust least, so it carries a label: fifteen thousand committed writes a second, with batched disk syncs, as an initial target I'll measure.",
 "C: Thirty thousand divided by fifteen thousand times one half headroom is four groups. I'll hash names into sixty-four slots, so I can move slots later. One group nearly carries the average. We shard for the peak, and so a bad group takes a quarter of the names, not all of them."])

S(plain("Estimates · 7 of 10 · renewals", "Renew a session, not a lock", chips("only holds > 3.3 s renew", "illustrative") + table(["Design", "Arithmetic", "Rate"], [
  ["Per lock", "1,600 long-held ÷ 3.3 s", "<b>≈ 480 / s</b>"],
  ["Per session", "400 client processes ÷ 3.3 s", "<b>≈ 120 / s</b>"],
  ["Cleanup when a client dies", "50 expiries against 1 session expiry", "50 : 1"]], "bt")), [
 "C: Renewals. A short hold, a hundred milliseconds, never renews, because the lease is ten seconds. Only holds longer than a third of the lease do, about three point three seconds.",
 "C: That is the sixteen hundred long-held locks. Renewing each one every three point three seconds is about four hundred and eighty a second. If instead each client process keeps one session alive, and locks hang off the session, with four hundred clients that is about a hundred and twenty. And a dead client is one expiry, not fifty.",
 "C: Decision: sessions."])

S(dia("Estimates · 8 of 10 · latency", "The p99 budget, with spare", "budget", chip=chips("quorum in one region", "20 ms")), [
 "C: The latency budget. Twenty milliseconds at p99 is an initial target. Two milliseconds of network in. Three of batch wait. Four for the leader to sync its disk. Five for a follower round trip and its own sync. One to apply and reply. Two of network out.",
 "C: That is seventeen, with three milliseconds spare. It only works because the quorum is in one region, across three zones. A cross-region quorum costs thirty to two hundred and fifty milliseconds by itself. Also: stage p99s don't add up to an end-to-end p99. This is a planning budget. I'd measure the whole path."])

S(plain("Estimates · 9 of 10 · pause against lease, per-key cap", "Two numbers that settle the argument", table(["Number", "Arithmetic", "Decision"], [
  ["Pause against lease", "15 s pause against a 10 s lease: the pause wins. Raise it to 60 s: a 70 s migration still wins, and every crash now stalls its name a minute", "<b>Tuning the lease cannot fix this. A token can.</b>"],
  ["Per-name ceiling", "grants ≤ 1 ÷ hold: 100 ms → 10 / s · 0.5 s → 2 / s · 30 s → 0.03 / s", "Hot names need a policy, not more machines"]], "bt")), [
 "C: Two numbers that settle arguments. A fifteen-second pause beats a ten-second lease. Raise the lease to sixty and a seventy-second migration still beats it, while every real crash now stalls its name for a minute. Tuning the lease cannot fix this. A token can.",
 "C: And one name can grant at most one over the hold time: ten a second at a hundred milliseconds. A name asked forty times a second is four times over, however many machines I add."])

S(plain("Estimates · 10 of 10 · the last three", "Margin, election budget, token space", table(["Number", "Arithmetic", "Label"], [
  ["Client clock margin", "200 ppm × 10 s = 2 ms drift. Client stops at 0.7 × lease = 7 s; server waits 10 s: <b>3 s gap</b>", "illustrative"],
  ["Election budget", "99.99% of 30 days = 259 s. At 2 s an election ≈ <b>130 a group a month</b>", "initial target"],
  ["Token space", "16-bit epoch + 48-bit index. 2<sup>48</sup> ≈ 2.8 × 10<sup>14</sup> ÷ 15,000/s ≈ <b>600 years</b> an epoch", "derived"]], "bt")), [
 "C: Three more. Clock drift of two hundred parts per million over a ten-second lease is two milliseconds. The client will stop at seven seconds and the server waits ten, so there is a three-second gap. Drift is not the risk. Pauses are.",
 "C: The availability target gives two hundred and fifty-nine seconds a month. At two seconds an election, about a hundred and thirty elections a group spend all of it. So elections per day becomes something I watch.",
 "C: And a token is sixteen bits of epoch plus forty-eight bits of log index. Forty-eight bits lasts about six hundred years at fifteen thousand a second. All of these are labelled arithmetic, not measurements."])
