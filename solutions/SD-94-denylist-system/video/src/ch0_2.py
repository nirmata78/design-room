from dsl import *

# ───────────────────────── 0 · cold open ─────────────────────────
chapter(0, "Cold open", -1, "Design a distributed denylist system", [
 "C: A denylist sounds like the easy question. A set of banned addresses and a lookup. Anyone can write that lookup in an afternoon. This question is not testing the lookup. It is testing what happens around it: how a ban reaches a hundred thousand servers, what a server does when it cannot hear about new bans, and what stops one wrong line from taking everyone offline."])

qs("Interviewer · the prompt", "“Design a distributed system that stops requests from banned sources, such as IP addresses, from being served on every one of our servers.”", [
 "I: Design a distributed system that stops requests from banned sources, such as I-P addresses, from being served, on every one of our servers.", "[pause: 1.5]"])

S(dia("Why it is harder than it looks", "The same pipe delivers a ban and a mistake", "badpush",
      chip=chips("100,000 nodes", "18 s to reach all", "one typo")), [
 "C: Here is the hook. An operator means to ban a small range and types a wide one. The change compiles in three seconds, crosses two tiers of relays, and by about eighteen seconds every server in the fleet is running it. Eight percent of real requests are now denied.",
 "C: No deployment failed. Every component did what it was told. The pipeline that can deliver an urgent ban in ten seconds delivers a mistake in the same ten seconds. The lookup was never the hard part. The pipe, and what it is allowed to carry, is."])

S(plain("Before the design", "What this question grades", table(["Axis", "Weak signal", "Strong signal"], [
  ["<b>Requirements</b>", "A table of addresses and a cache", "Asks how fast a ban must land, what a wrong block costs, who owns the failure policy"],
  ["<b>Correctness</b>", "“Eventually consistent”, no number", "States the staleness bound, versions every update, handles out-of-order changes"],
  ["<b>Trade-offs</b>", "Names a product", "Options with the failure that rules each out; checks the edge provider's own feature first"],
  ["<b>Depth</b>", "Stops at “push the list to the nodes”", "Delta window against snapshot size, why a rollback is a new version, why a filter hit needs a check"],
  ["<b>Operations</b>", "Watches CPU", "Propagation lag as the SLI, a synthetic banned probe, staged pushes, two owners with a contract"]], "bt sm sig") +
  grade("Two ways to be wrong run through this question: a ban that is missing, and a block that should not exist. Keep both in view.")), [
 "N: Five axes. The weak signal is always the same shape: a fast lookup, drawn well. The strong signal is what the candidate says about the distance between the list and the lookup.",
 "C: I'll keep two failures in mind the whole way. A ban that is missing, and a block that should not exist. Most designs worry about the first and forget the second."])

key("The thesis", "The check must be <em>local</em> and the list cannot be. The design is the distance between them: a <em>version</em>, a stated <em>bound</em>, and the discipline of a <em>release</em>.", [
 "V: The check must be local and the list cannot be. So the design is the distance between them: a version every node can verify, a stated bound on how stale a node may be, and the discipline of a release.", "[pause: 1.0]",
 "C: Concretely, a check in the server's own memory with no network call. A list compiled once, versioned, and copied everywhere through a path that can be verified and resumed. And pushes treated as carefully as a binary."])

S(plain("The order I will follow", "Scope, numbers, theory, a simple design, then I break it",
  '<div class="ribbon" style="margin-top:14pt">' + "".join(f"<span>{x}</span>" for x in STAGES) + '</div>' +
  '<div class="cards c3" style="margin-top:18pt"><div class="cd"><h3>First</h3><p>Requirements and scope. Numbers. A short theory chapter.</p></div>'
  '<div class="cd grn"><h3>Then</h3><p>API and data. A high-level design in three versions, each answering the one before.</p></div>'
  '<div class="cd red"><h3>Most of the time</h3><p>Seven challenges that break the design. A build cost. A recap.</p></div></div>'), [
 "C: The order I'll follow. Requirements and scope, then numbers, then a short theory chapter that the design can lean on. Then the A-P-I and data, and a high-level design in three versions, each answering the objection to the one before.",
 "C: Then the part I care about most: seven challenges that break the design, where each fix creates the next question. A build cost, because someone has to own this. And a recap."])

# ───────────────────────── 1 · requirements ─────────────────────────
chapter(1, "Requirements and scope", 0, "Ask first. Cut on purpose. Put numbers on it.", [
 "C: Before I draw anything I want to ask six questions. Each answer will change the design."])

def clar(n, q, a, say):
    S(f'<div class="who">Clarifying question {n} of 6</div><div class="qq">{q}</div><div class="ans">{a}</div>', say, cls="qs")

clar(1, "Who owns the list, and who calls the check?", "A policy team, security and legal, owns the content. The platform team owns the mechanism. The check runs on every serving node: about 100,000 nodes in 20 regions.", [
 "C: Who owns the list, and who calls the check?",
 "I: A policy team, security and legal, owns the content. The platform team owns the mechanism. The check runs on every serving node, on the request path. About a hundred thousand nodes in twenty regions.",
 "C: Two owners. That matters later, because the contract between them has to be a number. And the check is on the request path of a hundred thousand servers, so it cannot be slow and it cannot depend on much."])
clar(2, "What is banned?", "Addresses first: single IPv4 and IPv6 addresses and ranges. A second key type, a user id, will come. Do not design it out.", [
 "C: What exactly is banned?",
 "I: Network addresses first. Single I-P-v-four and I-P-v-six addresses, and ranges, written as C-I-D-R blocks. A second key type, a user I-D, will come later. Do not design it out.",
 "C: Ranges change the data structure, because a range needs longest-prefix matching and a single address does not. And a second key type means the key kind must be a field, not an assumption."])
clar(3, "How big, and how fast does it change?", "10 million entries today, perhaps 100 million later. About 5 changes a second, 50 in a burst. 1 million requests a second at peak across the fleet.", [
 "C: How big, and how fast does it change?",
 "I: Ten million entries today, perhaps a hundred million later. About five changes a second on average, fifty in a burst. A million requests a second at peak, across the whole fleet.",
 "C: The list is large but changes slowly. A million requests against five changes. That ratio is the whole shape of the design: read everywhere, write rarely."])
clar(4, "How fast must a ban take effect?", "Within 30 seconds for 99.9 % of nodes. Removals follow the same rule.", [
 "C: How fast must a new ban take effect?",
 "I: Within thirty seconds, for ninety-nine point nine percent of nodes. Removals follow the same rule.",
 "C: Thirty seconds is generous enough to avoid a constant stream and tight enough to rule out a once-a-minute timer. And it is stated as a share of nodes, which tells me some nodes are allowed to be late. I'll have to say what happens to those."])
clar(5, "What if a node cannot get updates?", "That is yours to propose. I will decide who signs it.", [
 "C: What should a node do if it cannot get updates?",
 "I: That is yours to propose. I will decide who signs it.",
 "C: That answer is the second half of this question. Failing open and failing closed are both bad for a denylist, and the choice belongs to the policy owner, not to me. I'll make it explicit and bring it back in challenge four."])
clar(6, "Where does the list come from?", "Mostly an internal tool. One list is mirrored from an external authority that publishes a daily bulk file. A variant has only a slow lookup API.", [
 "C: And where does the list come from?",
 "I: Mostly an internal tool. One list is mirrored from an external authority that publishes a daily bulk file. A variant has only a slow lookup A-P-I. Tell me what you would say.",
 "C: Two sources with different speeds. I'll treat the bulk file as an input to the same pipeline, and I'll answer the slow lookup in challenge six."])

S(plain("Requirements · functional", "Five things the system must do", '<div class="cards c3">'
  '<div class="cd"><h3>FR1 · Publish</h3><p>Add or remove a key or range, with a reason, a source and an optional expiry. Validated. Audited.</p></div>'
  '<div class="cd"><h3>FR2 · Distribute</h3><p>Every change reaches every node within the bound. A node that was offline catches up on its own.</p></div>'
  '<div class="cd amb"><h3>FR3 · Enforce</h3><p>A verdict for each request, inside the request path, in microseconds.</p></div>'
  '<div class="cd"><h3>FR4 · Inspect and explain</h3><p>Which version each node runs, and how old. Why was this key denied or served on that day.</p></div>'
  '<div class="cd grn"><h3>FR5 · Roll back and stop</h3><p>Halt a rollout, kill a list, revert. An emergency fast path. Audited.</p></div></div>'), [
 "C: Functionally, five things. One, publish a change: add or remove a key or range, with a reason, a source and an optional expiry, validated and audited. Two, distribute: every change reaches every node within the bound, and a node that was offline catches up without help.",
 "C: Three, enforce: a verdict for each request, in the request path, in microseconds. Four, inspect and explain: which version each node runs and how old it is, and why a key was denied or served on a given day. Five, roll back and stop: halt a rollout, kill a list, revert, with an emergency path. Each of these gets a numbered flow later."])

S(plain("Requirements · non-functional", "The numbers, and what each is for", '<p class="chips">all initial targets, not measurements</p><div class="tiles" style="--n:4">'
  '<div class="tile"><b>&lt; 10 µs</b><span>check p99, in process, no network call</span></div>'
  '<div class="tile blue"><b>30 s</b><span>for 99.9 % of nodes: about 100 nodes may be late</span></div>'
  '<div class="tile blue"><b>0</b><span>network calls on the request path</span></div>'
  '<div class="tile"><b>1 version</b><span>on every decision, for audit</span></div></div>'), [
 "C: The numbers. They are initial targets, and I'll say so once for this chapter: none is a measurement.",
 "C: The check takes under ten microseconds at the ninety-ninth percentile, in process, with no network call. A new version reaches ninety-nine point nine percent of nodes in thirty seconds, which means about a hundred of a hundred thousand may be late, and each of those must be listed, not silent. And every decision carries the version of the list that made it, so an auditor can reconstruct a verdict."])

S(plain("Requirements · behaviour", "Three promises that are not numbers", '<div class="cards c3">'
  '<div class="cd red"><h3>Keep enforcing</h3><p>A node holds its last known list through any outage of the distribution plane. Stale is not open.</p></div>'
  '<div class="cd amb"><h3>The bound is signed</h3><p>Each list has a maximum age and an action when it is exceeded, chosen by the owner.</p></div>'
  '<div class="cd"><h3>A bad push is caught by the pipeline</h3><p>Not by customers, and not by whoever happens to be on call.</p></div></div>'), [
 "C: Three promises that are not numbers. A node keeps enforcing its last known list through any outage of the distribution plane. Stale does not mean open.",
 "C: The staleness bound is signed: every list has a maximum age and an action when it is exceeded, chosen by its owner. And a bad push is caught by the pipeline itself, not by customers. Notice the pair of failures again: the first two promises are about a missing ban, the third is about a block that should not exist."])

S(plain("Requirements · polling, stated once", "A poll asks for the manifest. It does not download the list.",
  '<div class="cards c3"><div class="cd"><h3>Every 10 s</h3><p>A node asks the <b>manifest</b>: about 100 bytes with the current version, the delta window and a checksum.</p></div>'
  '<div class="cd grn"><h3>If behind, inside the window</h3><p>It fetches <b>deltas</b>: the changes between its version and now.</p></div>'
  '<div class="cd amb"><h3>Snapshot only to bootstrap</h3><p>Or after falling outside the window, or when a check fails. Never on a routine poll.</p></div></div>' +
  line("“Pull every ten seconds” never means “download the file every ten seconds”.", "a")), [
 "C: One definition, stated once, because it is easy to misread. Every ten seconds a node asks the manifest, about a hundred bytes: the current version, the delta window and a checksum. If current, that is the whole exchange. If behind, inside the window, it fetches deltas. A full snapshot only to bootstrap, after falling outside the window, or when verification fails. Never on a routine poll."])

S(plain("Requirements · scope", "In scope, out of scope", chips("addresses and ranges", "allowlist", "regional layers", "audit") +
  '<div class="scope2"><div class="in"><h3>In scope</h3><ul><li>Single addresses and ranges, IPv4 and IPv6</li><li>A second key type as an extension</li><li>An allowlist of ranges never blocked</li><li>Internal and mirrored sources</li><li>Staged rollout, audit, operator console</li></ul></div>'
  '<div class="out"><h3>Out of scope, on purpose</h3><ul><li>Detecting abuse: a model or rules engine (SD-43)</li><li>Rate limiting (SD-25)</li><li>Absorbing a volumetric attack: scrubbing upstream</li><li>Content rules inside requests: a web firewall</li><li>An appeals product: an owner and a workflow</li></ul></div></div>'), [
 "C: In scope: single addresses and ranges in both address families, a second key type as an extension, an allowlist of ranges never blocked, internal and mirrored sources, staged rollout, audit and a console.",
 "C: Out of scope, on purpose. Detecting abuse, which is a different question about models. Rate limiting, which has counters and windows. Absorbing a volumetric attack, which happens upstream. Content rules inside requests. And an appeals product, which needs an owner and a workflow: I'll name it, not draw it."])

S(plain("Requirements · say it aloud", "An address is not a person", '<div class="cards c2">'
  '<div class="cd red"><h3>Shared and carrier-grade addresses</h3><p>One address can hold thousands of legitimate users. A single wrong range blocks all of them.</p></div>'
  '<div class="cd grn"><h3>Why it shapes the design</h3><p>An allowlist that always wins. Removals as carefully handled as adds. A softer action than a hard block where it fits.</p></div></div>'), [
 "C: Something to say aloud. An address is not a person. Many users share one address behind a carrier-grade translator. One wrong range blocks thousands of legitimate people at once.",
 "C: That is why I want an allowlist that always wins, why removals matter as much as additions, and why the action on a match is part of the rule: deny, challenge or log only. It is also why a block that should not exist belongs next to a ban that is missing."])

key("The core", "The core is four things: a <em>versioned list</em>, a <em>distribution path</em> that can be verified, a <em>local check</em>, and a <em>release discipline</em>.", [
 "V: The core is four things. A versioned list, compiled in one place. A distribution path that can be verified and resumed. A local check with no network call. And a release discipline that treats the list as code.", "[pause: 0.8]",
 "N: Notice what the candidate did in six minutes. They asked who owns the failure policy, cut five things out loud, and said an address is not a person. That is the framing signal."])

# ───────────────────────── 2 · estimates ─────────────────────────
chapter(2, "Estimates", 1, "Every number is arithmetic, with a label. Each one changes a decision.", [
 "C: Now the numbers. Every one is arithmetic from the inputs and carries a label: given, illustrative, derived or an initial target. Each has to change a decision, or I drop it."])

S(plain("Estimates · 1 of 10 · why local", "A remote check on every request", table(["Quantity", "Arithmetic", "Label"], [
  ["Rate per node", "1,000,000 / s ÷ 100,000 nodes = <b>10 / s</b>", "given"],
  ["A remote check", "~1 ms of network added to every request; <b>1 M lookups / s</b> on one service", "illustrative"],
  ["Availability", "99.99 % × 99.99 % ≈ <b>99.98 %</b>", "derived"]], "bt") +
  line("The reason to stay local is latency and independence, not throughput.", "a")), [
 "C: A million requests a second over a hundred thousand nodes is ten a second per node. So CPU is not the argument for a local check. The argument is latency and independence.",
 "C: A remote check adds about a millisecond to every request, and makes one service answer a million lookups a second. And availability multiplies: a list service at four nines on the request path of a service at four nines gives about three point nine nines. Decision: the check is local, with no network call."])

S(dia("Estimates · 2 of 10 · memory", "Does the list fit on a node?", "sizes", chip=chips("budget 512 MB per node", "derived")), [
 "C: Memory. Ten million single I-P-v-four addresses at four bytes is forty megabytes as a sorted array. Two million ranges in a prefix trie is about eighty. All of that fits on every node. Now a hundred million I-P-v-six prefixes at seventeen bytes: one point seven gigabytes, over a budget of five hundred and twelve megabytes. A filter at ten bits an entry is a hundred and twenty-five. Challenge five will deal with it.",
 "C: Now the later case: a hundred million I-P-v-six prefixes. Seventeen bytes each is one point seven gigabytes, over a budget of five hundred and twelve megabytes. A filter at ten bits an entry is a hundred and twenty-five. Decision: ten million fits exactly, a hundred million does not, and challenge five will deal with it."], cls="dia")

S(plain("Estimates · 3 of 10 · one lookup", "The check is cheap", table(["Quantity", "Arithmetic", "Label"], [
  ["Sorted array of 10 M", "log₂(10⁷) ≈ 24 comparisons ≈ <b>0.3 to 1 µs</b> with cache misses", "illustrative, to be measured"],
  ["Prefix trie", "up to 32 steps for IPv4 and 128 for IPv6, but typically a handful of cache lines", "illustrative"],
  ["The budget", "p99 under 10 µs", "initial target"]], "bt") +
  line("The check fits its budget with room to spare. The risk is elsewhere.", "a")), [
 "C: The check itself. Binary search over ten million entries is about twenty-four comparisons: under a microsecond even with cache misses. A prefix trie is a little more. Against a budget of ten microseconds, the lookup has room to spare. Both numbers are illustrative, and I'd measure them.",
 "C: Decision: I will not spend design effort making the lookup faster. The risk is in getting the list there and in what it contains."])

S(plain("Estimates · 4 of 10 · change volume", "Deltas are tiny, so catch-up is cheap", table(["Quantity", "Arithmetic", "Label"], [
  ["Delta rate", "50 / s × 30 B ≈ <b>1.5 KB / s</b>", "illustrative"],
  ["Two hours offline", "7,200 s × 50 × 30 B ≈ <b>11 MB</b> of deltas, against a 40 MB snapshot", "illustrative"],
  ["Break-even", "40 MB ÷ 30 B ≈ 1.33 M changes ≈ <b>7.4 h</b> at the burst rate", "derived"],
  ["Retention", "keep <b>24 h</b>: 86,400 × 50 × 30 B ≈ 130 MB", "illustrative"]], "bt")), [
 "C: Change volume. Fifty changes a second at about thirty bytes is one and a half kilobytes a second. A node that was offline for two hours misses about eleven megabytes of deltas, against a forty megabyte snapshot. So catching up by deltas wins.",
 "C: The break-even is when the deltas would exceed a snapshot: about seven and a half hours at the burst rate. So I keep twenty-four hours of deltas, about a hundred and thirty megabytes. Decision: a delta window of twenty-four hours. A node older than that takes a snapshot."])

S(dia("Estimates · 5 of 10 · fan-out", "Four terabytes, or eight hundred megabytes", "fanout", chip=chips("derived")), [
 "C: Fan-out. If every node pulled a forty megabyte snapshot from one origin, that is a hundred thousand times forty megabytes: four terabytes. So I build a relay tree. The origin serves twenty regional relays, each serves ten zone relays, each zone relay serves five hundred nodes. The origin now serves twenty snapshots: eight hundred megabytes.",
 "C: Snapshots are immutable and addressed by content, so a zone relay caches them forever: five hundred nodes cost one fetch. Decision: the tree is not optional, and it also bounds the load on the origin."], cls="dia")

S(plain("Estimates · 6 of 10 · polling", "Ten thousand polls a second is cheap", table(["Quantity", "Arithmetic", "Label"], [
  ["Poll rate", "100,000 nodes ÷ 10 s = <b>10,000 manifest polls / s</b>", "derived"],
  ["Bytes", "~100 B each ≈ <b>1 MB / s</b> across the fleet", "illustrative"],
  ["Per zone relay", "500 ÷ 10 s = <b>50 polls / s</b>", "derived"],
  ["What a poll fetches", "the manifest only. Deltas when behind inside the window. A snapshot to bootstrap or beyond the window", "design choice"]], "bt")), [
 "C: Polling. A hundred thousand nodes every ten seconds is ten thousand manifest polls a second. Each is about a hundred bytes: one megabyte a second across the fleet, and fifty a second on each zone relay. Trivial.",
 "C: And to repeat the definition: a poll fetches the manifest and nothing else, unless the manifest shows the node is behind. Decision: a ten-second poll is cheap enough to be the backstop to push, and by itself it is a valid first release."])

S(dia("Estimates · 7 of 10 · propagation", "Does a ban land inside thirty seconds?", "budget", chip=chips("pull-only worst case: 18 s", "initial target")), [
 "C: The propagation budget. Compile, three seconds. Origin to regional, two. Regional to zone, two. The node's own poll, up to ten seconds of waiting: the worst case with no push. Verify and apply, one. Eighteen seconds against thirty, twelve spare. Pull alone meets the target. Push shortens the wait to about one second. And a sixty-second poll would not work: sixty-eight. Decision: a ten-second poll, and a measured propagation number to alert on."], cls="dia")

S(plain("Estimates · 8 of 10 · a slow external source", "Two hundred times over budget", table(["Quantity", "Arithmetic", "Label"], [
  ["New addresses", "20,000 first-seen / s at peak", "illustrative"],
  ["API budget", "100 calls / s → <b>200× over</b>", "given in the variant"],
  ["Coverage a day", "100 × 86,400 = 8.6 M lookups ÷ ~50 M distinct addresses = <b>17 %</b>", "illustrative"]], "bt") +
  line("A lookup API cannot be the path, and cannot cover everything. Ask for a bulk list.", "r")), [
 "C: The variant with a slow external source. Say twenty thousand first-seen addresses a second at peak, against a limit of a hundred calls a second. Two hundred times over. Even running all day, a hundred calls a second buys eight point six million lookups, against about fifty million distinct addresses: seventeen percent.",
 "C: Decision: that lookup can never sit on the request path, and it cannot give full coverage. It can feed a cache for the highest-volume addresses, and I'll ask for a bulk list. Challenge six."])

S(plain("Estimates · 9 of 10 · blast radius", "How much damage can one push do?", table(["Quantity", "Arithmetic", "Label"], [
  ["All nodes apply", "within ~18 s of publish", "derived"],
  ["A bad range", "blocks 8 % of requests; visible in one 10 s metrics window", "illustrative"],
  ["On a canary", "5 % of nodes = 5,000. Staged: 5 % → 25 % → 100 %, 5 min bake each ≈ <b>10 min</b> planned", "illustrative"]], "bt") +
  line("The same speed that helps a ban hurts a mistake. A planned push can be slower than an urgent one.", "a")), [
 "C: Blast radius. Without gates, all hundred thousand nodes run a pushed change within eighteen seconds. A bad range blocking eight percent of traffic would show in a single ten-second metrics window on a canary of five thousand nodes.",
 "C: So a planned push goes five percent, twenty-five percent, then everyone, with a five-minute bake each: about ten minutes. An urgent ban can use a shorter path. Decision: speed is not free. It is a setting, and different pushes get different settings."])

S(plain("Estimates · 10 of 10 · the SLO as a budget", "A hundred nodes may be late", table(["Quantity", "Arithmetic", "Label"], [
  ["The target", "99.9 % of 100,000 nodes within 30 s", "initial target"],
  ["Allowed late", "0.1 % = <b>100 nodes</b>, each listed with its age", "derived"],
  ["The SLI", "share of nodes on the current version, per region", "design choice"]], "bt") +
  grade("Stating the SLO as a budget of late nodes, and listing them, turns an abstract target into something a person can be paged on.")), [
 "C: Last. Ninety-nine point nine percent of a hundred thousand nodes allows a hundred late nodes. Each late node is listed with its age, never hidden. The service level indicator is the share of nodes on the current version, per region.",
 "N: A hundred nodes of slack is the kind of arithmetic that turns an abstract target into a pager rule.",
 "C: That is the numbers. Next, theory."])
