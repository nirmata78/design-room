from dsl import *

# ───────────────────────── 6 · bridge ─────────────────────────
chapter(6, "Bridge", 4, "It works. Where does it break first?", [
 "V: It works. The question now is where it breaks first.", "[pause: 1.0]"])

S(dia("Challenge map", "Seven attack points on the same baseline", "map", chip=chips("each fix creates the next question")), [
 "C: Here is the baseline with seven attack points. A node that fell behind, on the relay-to-node arrow. Changes out of order and overlapping, in the node's apply step. A wrong rule, from the rule store onward. No updates at all. A list too big for a node. A slow external source, at the rule store. And finally: how would we know any of it was broken? I'll take them in an order where each fix creates the next question."], cls="dia")

chapter(7, "Challenges", 5, "Seven ways to break it, and what survives", [
 "C: Seven challenges. Each runs the same way: the question, the naive answer, a case with numbers, where it breaks, the fix, why it works, then the interviewer pushes on the fix itself, and I answer what I'd say in the room."])

K = lambda n, t: f"Challenge {n} of 7 · {t}"

# ───────── Challenge 1 · the node that was offline ─────────
subchapter("7.1", "Challenge 1: The node that was offline", ["N: Challenge one. A node comes back after two hours offline: what should it fetch, and how do we prove it got all of it?"])
qs("Interviewer · challenge 1 of 7", "“A node was offline for two hours. How does it catch up? And how do you know all one hundred thousand nodes run version N?”", [
 "I: A node was offline for two hours. How does it catch up? And how do you know all one hundred thousand nodes run version N?", "[pause: 2.0]"])

S(dia(K(1, "the node that was offline"), "What should the node fetch, and is it whole?", "ch1-attack", q=True, red=True,
      extra=strip(("case", "Naive answer", "“On reconnect it downloads the whole list again, and we check each node's file.”"),
                  ("case", "Why it fails", "Nothing tells the node what it needs, and nothing proves what arrived is complete."))), [
 "C: The first answer most people give: on reconnect, download the whole list again, and check each node's file somehow. Look at the red arrows between the relay and the node. Nothing says what the node should fetch, and nothing proves that what it received is whole. And the file is forty megabytes."], cls="dia")

S(plain(K(1, "the trace"), "A node two hours behind, in numbers", '<pre class="trace"><span class="t">02:00  </span>node z7-0412 applies version 8,000,000. Then it loses its uplink\n<span class="t">04:00  </span>the list is at 8,360,000: <span class="bad">360,000 changes missed</span> ≈ 11 MB of deltas\n<span class="t">04:01  </span>50 nodes in the zone reconnect together: 50 × 40 MB = <span class="bad">2 GB from one relay</span>\n<span class="t">04:01  </span>a power cut mid-download leaves <span class="bad">a truncated file the node would load</span></pre>' +
  '<div class="hedge"><b class="t">Label the numbers</b>Illustrative. The shape matters: a small difference, a large naive transfer, and no integrity check.</div>', q=True, red=True), [
 "C: The trace. A node applied version eight million at two o'clock and lost its uplink. By four the list is at eight million three hundred sixty thousand: three hundred sixty thousand changes missed, about eleven megabytes. Fifty nodes in the zone reconnect together: fifty times forty megabytes, two gigabytes from one relay. And a power cut in the middle of a download leaves a truncated file that the node might load.",
 "C: These numbers are illustrative. The shape is the point: a small difference, a large naive transfer, and no integrity check."])

S(dia(K(1, "the fix"), "A manifest, a delta window, a snapshot fallback", "ch1-fix",
      extra=strip(("fixb", "Mechanism", "The node sends the version it has. The manifest says: take the delta, or take the snapshot. Every artifact is verified against a chained checksum before anything is applied."),
                  ("whyb", "Property", "Convergence (L1) and integrity (S2): a node can always reach the present, and never serves a state it has not verified."))), [
 "C: The fix. The new green box is the manifest. The node sends the version it has. The manifest answers: you are inside the window, take the delta, or you are not, take the snapshot. Every artifact is verified against the chained checksum before anything is applied, and the apply is the atomic swap from before."], cls="dia")

S(dia(K(1, "sequence"), "Reconnect, manifest, delta, verify, swap", "seq-ch1-catchup"), [
 "C: As a sequence. The node, offline for two hours, asks the manifest with its version. The relay answers: current is eight million three hundred sixty thousand, you are inside the window, deltas, about eleven megabytes. Suppose the checksum fails on the last delta. The node discards it and asks again, this time for the snapshot, which the zone relay serves from its cache, one origin fetch for fifty nodes. It verifies, builds beside, swaps, and reports the applied version."], cls="dia")

S(plain(K(1, "the decision, as code"), "Three branches, each safe",
  '<pre class="code">m = manifest(have = v)\n<span class="kw">if</span> m.current == v:            <span class="kw">return</span>                 <span class="cm">// up to date</span>\n<span class="kw">if</span> v &gt;= m.minDelta:            art = delta(v)         <span class="cm">// recent: small</span>\n<span class="kw">else</span>:                          art = snapshot(m.current)  <span class="cm">// too old</span>\n<span class="kw">if</span> !verifyChain(art):         discard(); art = snapshot(m.current)\n<span class="kw">if</span> !verifyChain(art):         keepLastGood(); report(apply_failed)</pre>' +
  strip(("whyb", "Why it works", "A node can always reach the current version: by a small delta if it is recent, by a snapshot if it is not. It verifies before it applies. The fleet answer to “is everyone on N” is the reported version, not a hope."), cols="one")), [
 "C: In code, three branches. Current: nothing to do. Inside the window: take the delta. Outside, or bootstrapping: take the snapshot. If verification fails, discard and try the snapshot, and if that fails too, keep the last good list and report apply-failed. The property is convergence and integrity. And I know the fleet runs version N because every node reports the version it runs. Skew is a metric, not a hope."])

qs("Interviewer · the second-level push", "“The delta window is twenty-four hours and the node was down for three days. Or the checksum fails again on the snapshot.”", [
 "I: The delta window is twenty-four hours and the node was down for three days. Or the checksum fails again on the snapshot.", "[pause: 2.0]"])

S(plain(K(1, "the second fix, and the honest limit"), "Beyond the window, take a snapshot. If that fails, stop and say so", '<div class="cards c2">'
  '<div class="cd grn"><h3>Beyond the window</h3><p>The manifest points to the snapshot, whatever the node\'s age. The zone relay caches it: fifty nodes cost one origin fetch.</p></div>'
  '<div class="cd amb"><h3>A checksum that keeps failing</h3><p>A corrupt artifact at the origin. The node keeps its last known good, reports <b>apply_failed</b>, and the control plane halts that version.</p></div></div>' +
  line("A node that can reach nothing keeps an old list. That is challenge four.", "r")), [
 "C: Beyond the window, the manifest simply points to the snapshot, whatever the node's age, and the zone relay's cache makes fifty nodes cost one origin fetch. A checksum that keeps failing means a corrupt artifact at the origin. The node keeps its last known good list, reports apply-failed, and the control plane halts that version.",
 "C: The honest limit: a node that cannot reach anything keeps an old list. That is challenge four."])

say_slide("“Every version has a number and a checksum chained to the one before. A node says what it has, and the manifest says whether a small delta or a full snapshot gets it to the present. It verifies before it applies and swaps atomically, so it never serves a half-built list. And I know the fleet is converged because every node reports the version it runs.”", [
 "V: If asked, I'd say: every version has a number and a checksum chained to the one before. A node says what it has, and the manifest says whether a small delta or a full snapshot gets it to the present. It verifies before it applies and swaps atomically, so it never serves a half-built list. And I know the fleet is converged because every node reports the version it runs.", "[pause: 1.0]",
 "N: That fix creates the next question: in what order do changes apply?"])

# ───────── Challenge 2 · order, duplicates, overlap ─────────
subchapter("7.2", "Challenge 2: Order, duplicates, overlap", ["N: Challenge two. Changes arrive late, twice, and overlapping each other: how does every node still end at the same answer?"])
qs("Interviewer · challenge 2 of 7", "“An add and a remove for the same key arrive in the wrong order. Or the same delta arrives twice. And an operator adds a slash-sixteen and allows a slash-twenty-six inside it.”", [
 "I: An add and a remove for the same key arrive in the wrong order. Or the same delta arrives twice. And an operator adds a slash sixteen, and allows a slash twenty-six inside it.", "[pause: 2.0]"])

S(dia(K(2, "order and overlap"), "What does the node believe?", "ch2-attack", q=True, red=True,
      extra=strip(("case", "Naive answer", "“Apply changes in the order they arrive. The network is mostly in order.”"),
                  ("case", "Break", "The node's apply step treats arrival order as intent order."))), [
 "C: The naive answer: apply changes in the order they arrive, because the network is mostly in order. Mostly. Look at the node: its apply step believes that arrival order is intent order. Through two relay tiers, with a push and a poll both delivering, that is not true."], cls="dia")

S(plain(K(2, "the trace"), "The key ends up banned, and the last intent was to remove it", '<pre class="trace"><span class="t">v100  </span>add 203.0.113.9 (a mistake)\n<span class="t">v101  </span>remove 203.0.113.9 (the correction)\n<span class="t">node  </span>receives <span class="bad">v101 then v100</span> by two paths\n<span class="t">node  </span>applies in arrival order: remove, then add. <span class="bad">Final state: banned</span>\n<span class="t">also  </span>v101 arrives twice: harmless here, wrong for a counter</pre>' +
  '<div class="hedge"><b class="t">Overlap</b>v90 deny 198.51.0.0/16 · v97 allow 198.51.100.64/26 (a partner). Verdict for 198.51.100.70? A node that stops at the first range it finds says deny.</div>', q=True, red=True), [
 "C: The trace. Version one hundred adds a key by mistake. Version one hundred and one removes it, the correction. The node receives one-oh-one first and one hundred second, by two paths. Applied in arrival order: remove, then add. The final state is banned, though the last intent was remove.",
 "C: Overlap is the second half. Version ninety denies a slash sixteen. Version ninety-seven allows a partner's slash twenty-six inside it. A node that stops at the first range it finds says deny. And two sources can disagree about one key: that needs a written precedence."])

S(dia(K(2, "the fix"), "One total order, and a version on every key", "ch2-fix",
      extra=strip(("fixb", "Mechanism", "The rule store assigns one version order. Each key remembers the version of its last change. A change applies only if its version is higher."),
                  ("whyb", "Property", "Convergence to the intended state: S1, S2, L1. The result depends on the set of changes, not on their order or count."))), [
 "C: The fix lives in the same node box, outlined green. One: the rule store's transaction assigns the version, so there is a single order to begin with. Two: each key remembers the version of its last change, and a change applies only if its version is higher. A late message, or a duplicate, is a no-op. The result depends on the set of changes, not their order or number."], cls="dia")

S(dia(K(2, "sequence"), "Late and duplicate changes are ignored", "seq-ch2-merge"), [
 "C: As a sequence. Version one-oh-one, remove, arrives first. The node records the key as removed at one-oh-one. Version one hundred, add, arrives late: one hundred is not higher than one-oh-one, ignore. The final state is removed. Version one-oh-one arrives again, a duplicate: not higher than itself, a no-op. The node converges to the intended state whatever the arrival order."], cls="dia")

S(plain(K(2, "precedence, as rules"), "Ranges resolve by longest prefix. Allow beats deny.", table(["Situation", "Rule", "Why"], [
  ["A key matches an exact entry and a range", "the <b>exact</b> entry decides", "more specific"],
  ["Two ranges match", "the <b>longest prefix</b> decides", "more specific"],
  ["Allow and deny at equal specificity", "<b>allow wins</b>", "a wrong block is worse than a missed ban for a protected range"],
  ["An allowlist range matches", "<b>allow, always</b>, checked first", "independent of review"],
  ["Two sources disagree", "written precedence: an unexpired manual entry beats a feed", "no silent overrides"]], "bt sm") +
  grade("Saying that the compiler expands an exception inside a range into explicit entries, so the node needs no special case, is a strong depth signal.")), [
 "C: Precedence, as rules the compiler enforces. An exact entry beats a range. A longer prefix beats a shorter one. At equal specificity, allow beats deny. An allowlist range matches first and always wins. And when two sources disagree, an unexpired manual entry beats a feed. In the example, the partner's slash twenty-six is more specific than the slash sixteen, so the verdict is allow.",
 "C: One detail: the compiler expands an exception inside a range into explicit entries, so the node needs no special case. The node stays simple, and the complexity is in one place that can be tested."])

qs("Interviewer · the second-level push", "“Tombstones grow forever. And what if the version counter itself is lost or reset after a restore?”", [
 "I: Tombstones grow forever. And what if the version counter itself is lost or reset after a restore?", "[pause: 2.0]"])

S(plain(K(2, "the second fix, and the honest limit"), "Bounded tombstones, and a counter that never rewinds", '<div class="cards c2">'
  '<div class="cd grn"><h3>Tombstones</h3><p>Kept only for the delta window. A node older than the window takes a snapshot, which has none, so nothing is resurrected.</p></div>'
  '<div class="cd red"><h3>The version counter</h3><p>Lives in the rule store\'s transaction log. A restore that would rewind it is refused. After a rebuild, start with a higher <b>epoch</b>: never reuse a number.</p></div></div>' +
  '<div class="whyb"><b class="t">Expiry is a command, not a node clock</b>A ban with an expiry is turned into an explicit remove by the compiler at that time, with its own version. Every node sees the same history.</div>'), [
 "C: Tombstones are kept only for the delta window. A node older than the window takes a snapshot, which has none, so nothing is resurrected. The version counter lives in the rule store's transaction log, and a restore that would rewind it is refused. After a rebuild, start with a higher epoch. Never reuse a number.",
 "C: One more decision belongs here. Expiry is a command, not a node-side clock. A ban with an expiry becomes an explicit remove, issued by the compiler at that time with its own version. So every node sees the same history, and none depends on its own wall clock."])

say_slide("“I do not trust arrival order. One writer assigns versions, and each key remembers the version of its last change, so a late or duplicate message is ignored. Ranges resolve by longest prefix, and an exception beats a deny. The merge is idempotent, so the same history gives the same list in any order.”", [
 "V: If asked, I'd say: I do not trust arrival order. One writer assigns versions, and each key remembers the version of its last change, so a late or duplicate message is ignored. Ranges resolve by longest prefix, and an exception beats a deny. The merge is idempotent, so the same history gives the same list in any order.", "[pause: 1.0]",
 "N: Now the content itself: what if the change is wrong?"])

# ───────── Challenge 3 · the bad push ─────────
subchapter("7.3", "Challenge 3: The bad push", ["N: Challenge three. A correct pipeline delivers a wrong rule to every node in seconds: how do we stop our own speed from hurting us?"])
qs("Interviewer · challenge 3 of 7", "“Someone publishes a range that covers a large part of Europe. How fast does it break, and how do you stop it?”", [
 "I: Someone publishes a range that covers a large part of Europe. How fast does it break, and how do you stop it?", "[pause: 2.0]"])

S(dia(K(3, "the bad push"), "Everything worked, and everyone is blocked", "ch3-attack", q=True, red=True,
      extra=strip(("case", "Naive answer", "“Review the change before it goes out, and fix it quickly if it is wrong.”"),
                  ("case", "Break", "Nothing between the author's keystroke and every node asks whether the content is plausible."))), [
 "C: The naive answer: review the change before it goes out, and fix it quickly if it is wrong. Look at the arrows from the rule store through the origin to the relays, all red. Nothing between the author's keystroke and every node asks whether the content is plausible. The pipeline is working perfectly."], cls="dia")

S(plain(K(3, "the trace"), "Forty seconds, and a review that saw one line", '<pre class="trace"><span class="t">14:00:00  </span>operator adds /8 instead of /28. One line. Reviewed by one person\n<span class="t">14:00:03  </span>compiled as version 8,361,001\n<span class="t">14:00:12  </span>the push reaches the relays\n<span class="t">14:00:21  </span><span class="bad">all 100,000 nodes serve the new list</span>\n<span class="t">14:00:30  </span><span class="bad">8 % of requests denied</span>\n<span class="t">14:00:40  </span>on-call is paged; the fix is a new version that takes another 18 s</pre>' +
  '<div class="hedge"><b class="t">Label the numbers</b>Illustrative timings. The share denied depends on the range. The structure holds: speed in, speed out, and a human in the loop.</div>', q=True, red=True), [
 "C: The trace. At two o'clock an operator means a slash twenty-eight and types a slash eight. One line, reviewed by one person, who saw one line added. Three seconds to compile. Twelve to reach the relays. At twenty-one seconds every node serves it. At thirty, eight percent of requests are denied. At forty the on-call is paged, and the fix is another version that takes another eighteen seconds.",
 "C: Illustrative timings, and the share depends on the range. The structure holds: fast in, fast out, and a human in the loop."])

S(plain(K(3, "the first line of defence"), "Validate at ingest, and an allowlist that always wins", '<div class="cards c3">'
  '<div class="cd"><h3>Limits</h3><p>Shape and size checks. A cap on how much address space one change may cover. A change over the cap needs a second approver.</p></div>'
  '<div class="cd grn"><h3>Allowlist</h3><p>Ranges that must never be blocked: the company\'s own, key partners, health checks. Checked at compile time <b>and</b> at enforcement.</p></div>'
  '<div class="cd amb"><h3>Two-person approval</h3><p>Above a threshold. A review sees the effect, not just the line: “this change covers 16 M addresses”.</p></div></div>'), [
 "C: The first line of defence is at ingest. Limits: shape and size, and a cap on how much address space one change may cover, with a second approver above it. An allowlist of ranges that must never be blocked, the company's own, key partners, health checks, checked at compile time and again at enforcement, so it works even if a bad version gets through. And a review that sees the effect, not just the line: this change covers sixteen million addresses."])

S(dia(K(3, "the fix"), "Treat the list like code: stages, a gate, a kill flag", "ch3-fix",
      extra=strip(("fixb", "Mechanism", "Staged rollout 5 % → 25 % → 100 %, gated on block rate per node against its baseline. A kill flag in the manifest. Rollback is a new, higher version."),
                  ("whyb", "Property", "Safety against over-block (S2), at the cost of time. The blast radius of a mistake becomes the canary."))), [
 "C: The fix. The new green boxes are the validation step, the controller doing staged rollout, and the kill flag carried by the manifest. A stage goes to five percent of nodes, then twenty-five, then everyone, with a five-minute bake each. The controller compares each node's block rate to its own baseline, and a rise of more than a few points trips the gate, freezes the stage and alerts. Rollback is a new, higher version."], cls="dia")

S(dia(K(3, "replay"), "The same mistake with a canary", "badpush"), [
 "C: Replay it. Top row, without gates: eighteen seconds to everyone, then eight percent denied for as long as it takes someone to act. Bottom row, with a canary: only five thousand nodes see the bad version. The gate trips within one metrics window, the stage freezes, and a rollback lands as a new version. The exposure is five thousand nodes for about a minute, not a hundred thousand for however long the on-call takes."], cls="dia")

S(plain(K(3, "the gate, with numbers"), "What exactly trips it", table(["Signal", "Baseline", "Trip", "Action"], [
  ["Block rate per node, 10 s window", "0.5 % of requests", "more than +3 points on the canary", "freeze the stage, alert, no further stage"],
  ["Block rate by region", "per region", "a region doubles", "halt and page the platform on-call"],
  ["Apply failures", "~0", "any checksum failure on a stage", "halt that version"],
  ["Urgent ban", "—", "fast path: one region, 60 s bake", "logged as an exception, reviewed after"]], "bt sm") +
  '<div class="hedge"><b class="t">Label the numbers</b>Initial targets, tuned from measured baselines. The principle: the gate is a number, not a person watching a graph.</div>'), [
 "C: What exactly trips the gate? Block rate per node in a ten-second window against its baseline: more than three points on the canary freezes the stage and alerts. A region's block rate doubling halts and pages. Any checksum failure halts that version. An urgent ban uses a fast path, one region and a sixty-second bake, logged as an exception. Initial targets: the gate is a number, not a person watching a graph."])

S(plain(K(3, "the action is part of the rule"), "Shadow first, then enforce", '<div class="cards c3">'
  '<div class="cd grn"><h3>Log only</h3><p>A new or widened rule ships in shadow mode. Nodes record “would have denied” with the rule id. No user is affected.</p></div>'
  '<div class="cd amb"><h3>Challenge</h3><p>For shared addresses, a softer response than a hard block: a challenge instead of a deny.</p></div>'
  '<div class="cd red"><h3>Deny</h3><p>Promoted after the owner reads the shadow counts. The promotion is itself a version.</p></div></div>'), [
 "C: One more tool. The action is part of the rule: log only, challenge, or deny. A new or widened rule can ship in shadow mode: nodes record that they would have denied, with the rule id, and no user is affected. The owner reads the counts and promotes it to deny, which is itself a version. For shared addresses, a challenge is a softer answer than a hard block."])

qs("Interviewer · the second-level push", "“The rule is legitimate-looking and wrong: a real customer's range. Block rate does not move. Or the kill switch rides the same pipe that is broken.”", [
 "I: The rule is legitimate-looking and wrong: a real customer's range. The block rate does not move. Or the kill switch rides the same pipe that is broken.", "[pause: 2.0]"])

S(plain(K(3, "the second fix, and the honest limit"), "Nodes protect themselves; the kill flag is on its own channel", '<div class="cards c2">'
  '<div class="cd grn"><h3>A local circuit breaker</h3><p>If a node\'s block rate jumps by a multiple of its baseline for N seconds right after an update, it reverts to the previous version on its own, reports, and pages. No central decision needed.</p></div>'
  '<div class="cd grn"><h3>A separate, tiny channel</h3><p>The kill flag is one field in the manifest every poll reads. Not a new snapshot. It works even if the artifact path is the broken one.</p></div></div>' +
  line("A precise, plausible, wrong rule cannot be found by statistics. Only the allowlist, review of high-impact changes, audit and a fast removal path find it.", "r")), [
 "C: Two answers. Nodes protect themselves: if a node's block rate jumps by a multiple of its own baseline right after an update, it reverts to the previous version on its own, reports, and pages. And the kill flag is a separate, tiny channel: one field in the manifest that every poll reads, not a new snapshot, so it works even when the artifact path is the broken part.",
 "C: The honest limit: a precise, plausible, wrong rule, such as a real customer's range added by mistake, cannot be found by statistics. It is found by the allowlist, by review of high-impact changes, by the audit trail and a fast removal path. Policy, not mechanism, owns that risk, and I say so."])

say_slide("“The same pipe that delivers a ban in ten seconds delivers a mistake in ten seconds, so a push gets the same discipline as a binary: validation, an allowlist that always wins, a canary gated on block rate, a kill flag on its own channel, and a rollback that is just a new version. Nodes also protect themselves: if the block rate jumps right after an update, they revert on their own.”", [
 "V: If asked, I'd say: the same pipe that delivers a ban in ten seconds delivers a mistake in ten seconds, so a push gets the same discipline as a binary. Validation, an allowlist that always wins, a canary gated on block rate, a kill flag on its own channel, and a rollback that is just a new version. Nodes also protect themselves: if the block rate jumps right after an update, they revert on their own.", "[pause: 1.0]",
 "N: So far, updates arrived. What if they stop arriving?"])
