from dsl import *

K = lambda n, t: f"Challenge {n} of 7 · {t}"

# ───────── Challenge 4 · stale, partitioned, no control plane ─────────
subchapter("7.4", "Challenge 4: Stale or no control plane", ["N: Challenge four. The control plane is stale, partitioned or gone: what does a node do, and who decided that?"])
qs("Interviewer · challenge 4 of 7", "“A node cannot reach any relay for three hours. Or the whole distribution plane is down. What does the node do, and who decided?”", [
 "I: A node cannot reach any relay for three hours. Or the whole distribution plane is down. What does the node do, and who decided?", "[pause: 2.0]"])

S(dia(K(4, "stale or no control plane"), "Fail closed, or fail open?", "ch4-attack", q=True, red=True,
      extra=strip(("case", "Naive answer", "“Fail closed: deny everything if the list is old. Or fail open: serve everything.”"),
                  ("case", "Break", "Nobody chose. Both defaults are an outage, in opposite directions."))), [
 "C: The naive answer is a binary: fail closed, deny everything if the list is old, or fail open, serve everything. Look at the node under attack. It has stopped hearing from the relays, and its staleness clock has no action attached to it. Nobody chose what happens. Both defaults are bad, in opposite directions."], cls="dia")

S(plain(K(4, "the trace"), "Both defaults hurt", '<pre class="trace"><span class="t">09:00  </span>node eu-3-0099 applies the last update. Then it loses all relays\n<span class="t">12:00  </span>3 h × 3,600 × 5 / s = <span class="bad">54,000 changes missed</span>, including one urgent ban\n<span class="t">fail closed  </span>10 req/s × 10,800 s = <span class="bad">108,000 legitimate requests refused</span> by this node alone\n<span class="t">whole fleet  </span>the plane is down: <span class="bad">every node fails closed together: a global outage</span>\n<span class="t">fail open    </span>serves everything, including the <span class="bad">urgent ban it never heard about</span></pre>' +
  '<div class="hedge"><b class="t">Label the numbers</b>Illustrative: a 5-a-second average change rate and 10 requests a second per node.</div>', q=True, red=True), [
 "C: The trace. A node applied its last update at nine and lost all relays. By noon it has missed fifty-four thousand changes, including one ban the policy team called urgent. Fail closed would refuse a hundred and eight thousand legitimate requests from this node alone, and if the whole plane is down, every node fails closed together: a global outage caused by the system built to protect you. Fail open serves everything, including the ban it never heard about.",
 "C: Illustrative numbers. The point is that neither default is a policy. Both are what happens when nobody decided."])

S(dia(K(4, "the key sentence"), "Stale is not open", "stale",
      chip=chips("a node keeps enforcing its last list", "only the newest bans are missing")), [
 "C: The first move is to separate two things people merge. Stale is not open. A node with an old list keeps blocking every ban it knew about. Only the newest bans are missing. So the question is never block everything or allow everything. It is what to do about the missing new bans, and how long that is acceptable. On the line: fresh, then past a bound an alert, then past a longer bound a stronger action."], cls="dia")

S(dia(K(4, "the fix"), "A bound and an action, signed by the owner", "ch4-fix",
      extra=strip(("fixb", "Mechanism", "Each list has a maximum age and an action. Keep serving and alert, or drain the node out of rotation. A last known good copy on disk survives a restart."),
                  ("whyb", "Property", "Liveness made visible (L3) without turning a control-plane outage into a global outage."))), [
 "C: The fix. The node persists its last known good copy, so a restart with no network still enforces. It exposes its list age on its health endpoint, and the load balancer reads it. Each list has a maximum age and an action, chosen by the policy owner. The action is either alert and keep serving, or drain the node out of the load-balancer rotation. Drain, instead of failing each request. The node keeps its last list while it waits for the plane to return."], cls="dia")

S(plain(K(4, "who signs what"), "A table the owners agree before the incident", table(["List class", "Bound", "Action past the bound", "Owner"], [
  ["Abuse bans", "15 min", "alert, keep serving", "security"],
  ["General list", "60 min", "drain the node, capped", "platform, agreed with policy"],
  ["Legal list with a hard deadline", "per the legal term", "drain the node; escalate to legal", "legal"],
  ["A node with no list on disk", "—", "stay out of rotation until it bootstraps", "platform"]], "bt sm") +
  '<div class="hedge"><b class="t">Label the numbers</b>Initial targets, for the exercise. The structure is the point: per class, a number, an action and a named owner.</div>'), [
 "C: Who signs what. Per list class, a bound, an action and an owner, agreed before the incident. Abuse bans: fifteen minutes, alert and keep serving, owned by security. The general list: sixty minutes, drain the node, capped. A legal list: whatever the legal term says, drain and escalate. A node with no list on disk stays out of rotation until it bootstraps. This table is what the interviewer signs."])

S(dia(K(4, "sequence"), "Past the bound, drained, recovered", "seq-ch4-drain"), [
 "C: As a sequence. The node sees fifteen minutes with no update, past the bound for the abuse list. It reports stale, with its age, to the load balancer. The balancer checks its drain budget, five percent per region, not used up. The node is taken out of rotation but keeps enforcing its last list. When the node reaches a relay again, it applies the delta, reports current, and goes back into rotation."], cls="dia")

qs("Interviewer · the second-level push", "“Every node passes the bound at once because the control plane is down. You just drained the fleet.”", [
 "I: Every node passes the bound at once because the control plane is down. You just drained the fleet.", "[pause: 2.0]"])

S(plain(K(4, "the second fix, and the honest limit"), "A drain budget, and a risk someone accepts in writing", '<div class="cards c2">'
  '<div class="cd grn"><h3>A drain budget</h3><p>Automatic draining never removes more than a fixed share of the fleet: say 5 % per region. Past that, nodes keep serving and the page goes to a human.</p></div>'
  '<div class="cd amb"><h3>The risk is named</h3><p>While the plane is down beyond the bound, some nodes serve a stale list. The owner of the list accepts that, in writing, as the price of not causing a global outage.</p></div></div>' +
  line("Nothing makes a partitioned node learn a ban it cannot hear. The cures are a plane that is not a single point, and a bound short enough to matter.", "r")), [
 "C: A drain budget. Automatic draining never removes more than a fixed share of the fleet, say five percent per region. Past that, nodes keep serving and the page goes to a human. The cost is stated: while the plane is down beyond the bound, some nodes serve a stale list, and the owner of the list accepts that in writing.",
 "C: The honest limit: nothing makes a partitioned node learn a ban it cannot hear. The cures are a plane that is not a single point of failure, and a bound short enough to matter. That is a staffing and design question, not something a node can solve alone."])

say_slide("“Stale is not open: a node keeps enforcing what it has. For each list, the owner signs a maximum age and an action: alert and keep serving, or pull the node out of rotation. Automatic draining has a cap, so a control-plane outage cannot become a fleet outage. The risk of a late ban is a named decision, not an accident.”", [
 "V: If asked, I'd say: stale is not open. A node keeps enforcing what it has. For each list, the owner signs a maximum age and an action: alert and keep serving, or pull the node out of rotation. Automatic draining has a cap, so a control-plane outage cannot become a fleet outage. The risk of a late ban is a named decision, not an accident.", "[pause: 1.0]",
 "N: Next: what if the list no longer fits on a node?"])

# ───────── Challenge 5 · the list does not fit ─────────
subchapter("7.5", "Challenge 5: The list does not fit", ["N: Challenge five. The list grows past a node's memory: what do we keep locally, and what does a false positive cost?"])
qs("Interviewer · challenge 5 of 7", "“A hundred million IPv6 prefixes. Why not one shared cache lookup per request? And a Bloom filter says maybe. Then what?”", [
 "I: A hundred million I-P-v-six prefixes. Why not one shared cache lookup per request? And a Bloom filter says maybe. Then what?", "[pause: 2.0]"])

S(dia(K(5, "the list does not fit"), "One point seven gigabytes on every node?", "ch5-attack", q=True, red=True,
      extra=strip(("case", "Naive answer", "“Put it all in a shared cache and call it from every node. Or use a Bloom filter and block on a yes.”"),
                  ("case", "Break", "The exact set no longer fits. The filter, used alone, turns its error into a block."))), [
 "C: The naive answers. Put everything in a shared cache and call it from every node, or use a Bloom filter and block on a yes. Look at the node box and the request arrow. The exact set no longer fits in memory, and a filter used alone turns its error into a block."], cls="dia")

S(plain(K(5, "the numbers"), "Memory, and what a false positive costs", '<pre class="trace"><span class="t">exact set    </span>100 M × 17 B = <span class="bad">1.7 GB</span> per node. The budget is 512 MB\n<span class="t">shared lookup </span>1 M / s × 1 ms: <span class="bad">a hard dependency on every request</span>\n<span class="t">filter alone </span>1 M / s × 1 % false positives = <span class="bad">10,000 real users blocked every second</span>\n<span class="t">filter size   </span>100 M × 10 bits = 125 MB: fits</pre>' +
  '<div class="hedge"><b class="t">Label the numbers</b>Derived from stated inputs. A false-positive rate is a property of the filter, so it is a design parameter, not a measurement.</div>', q=True, red=True), [
 "C: The numbers. The exact set is a hundred million times seventeen bytes: one point seven gigabytes, against a budget of five hundred and twelve megabytes. A shared lookup is a hard dependency on every request. And a filter used alone, at one percent false positives, blocks ten thousand real users every second at a million requests a second. The filter itself, at ten bits an entry, is a hundred and twenty-five megabytes: it fits.",
 "C: The false-positive rate is a property of the filter's size, a design parameter I choose. It is not something I measure."])

S(dia(K(5, "the shape"), "A filter says no with certainty. A maybe needs a check.", "bloom"), [
 "C: The shape of the fix. A request goes to the local filter. For about ninety-nine percent of traffic it says definitely not listed: allow, with no network call. For the rest, a maybe, the request goes to an exact lookup tier, sharded by key prefix, which returns the verdict. Listed: deny. Not listed, which is a false positive: allow, and cache the answer. Used this way, a false positive costs a lookup, not a wrong block."], cls="dia")

S(dia(K(5, "the fix"), "A filter in front, an exact tier behind, a cache", "ch5-fix",
      extra=strip(("fixb", "Mechanism", "A 125 MB filter answers “not listed” locally. A maybe is confirmed by a sharded exact tier, and the verdict is cached with a TTL bounded by the staleness bound."),
                  ("whyb", "Property", "Correct verdicts at scale (S2): the filter's error is one-sided, so a false positive costs a lookup, never a wrong block."))), [
 "C: The fix, on the baseline. The new box is the lookup tier. The node's filter answers not listed locally. A maybe goes to the tier, and the answer is cached on the node with a lifetime no longer than the staleness bound. I'd also keep the hottest, most-matched ranges exact and local, so the busiest keys never leave the node. Memory stays within budget, and the path stays local for nearly all traffic."], cls="dia")

S(dia(K(5, "sequence"), "Maybe, lookup, cache", "seq-ch5-lookup"), [
 "C: As a sequence. A check for an I-P-v-six address arrives. The local filter says maybe. The agent asks the exact tier, and identical concurrent requests are coalesced into one lookup. The answer: not listed, a false positive. Allow, and cache it for sixty seconds. And a per-node lookup budget protects the tier during an attack, which is the next question."], cls="dia")

S(plain(K(5, "where each key is enforced"), "The right enforcement point per entity", table(["Key", "Where it is known", "Enforced at", "Structure"], [
  ["Single address, range", "at the connection", "the edge or gateway, in the agent", "sorted array, prefix trie"],
  ["User id", "after authentication", "the application layer, in the same agent library", "hash set or filter + lookup"],
  ["Email, device", "after login", "the service that sees it", "hash set"],
  ["A rotating address per request", "never stable", "<b>not a denylist problem</b>", "an identity key or an abuse model (SD-43)"]], "bt sm") +
  grade("Saying that the right place to enforce depends on where the key first becomes known is a depth signal. Do not stretch one structure over every key.")), [
 "C: Where each key is enforced. An address or a range is known at the connection, so the edge enforces it, with a sorted array and a trie. A user I-D is known only after authentication, so it is enforced in the application layer, with the same agent library. A user who arrives from a new address on every request is not a denylist problem: that needs an identity key or an abuse model."])

qs("Interviewer · the second-level push", "“During an attack nearly every request is a true hit, so every request goes to the lookup tier. What now?”", [
 "I: During an attack nearly every request is a true hit, so every request goes to the lookup tier. What now?", "[pause: 2.0]"])

S(plain(K(5, "the second fix, and the honest limit"), "Cache positives, coalesce, cap per node", '<div class="cards c3">'
  '<div class="cd grn"><h3>Cache the verdict</h3><p>A positive verdict is cached on the node with a bounded lifetime. Repeated hits from one source cost one lookup.</p></div>'
  '<div class="cd grn"><h3>Coalesce and shard</h3><p>Concurrent lookups for one key become one. The tier is sharded by prefix and sized for the hit rate it will see.</p></div>'
  '<div class="cd amb"><h3>A per-node budget</h3><p>Past it, a node uses cached verdicts and, for an unknown key, its stated policy. The tier cannot be flooded by the very attack it is there to stop.</p></div></div>' +
  line("A very large list costs a tier on the path for hits. We pay that only for keys likely to be banned.", "r")), [
 "C: Three moves. Cache the positive verdict on the node, so repeated hits from one source cost one lookup. Coalesce concurrent lookups for one key, and shard the tier by prefix. And cap lookups per node: past the cap, a node uses cached verdicts and, for an unknown key, its stated policy, so the tier cannot be flooded by the attack it exists to stop.",
 "C: The honest limit: a very large list costs a tier on the request path for hits. We pay that cost only for keys that are likely to be banned, and the rest of the traffic stays fully local."])

say_slide("“A shared lookup per request puts the list service in everyone's availability, and a millisecond on every call. When the set does not fit, I keep a filter locally, which can say definitely not listed, and confirm a maybe with an exact tier, because a false positive blocks a real user. I cache the verdicts, coalesce lookups, and cap the load per node, so an attack does not take down the confirmation tier.”", [
 "V: If asked, I'd say: a shared lookup per request puts the list service in everyone's availability, and a millisecond on every call. When the set does not fit, I keep a filter locally, which can say definitely not listed, and confirm a maybe with an exact tier, because a false positive blocks a real user. I cache the verdicts, coalesce lookups, and cap the load per node, so an attack does not take down the confirmation tier.", "[pause: 1.0]",
 "N: One more source of trouble: when the list comes from someone slow."])

# ───────── Challenge 6 · slow external source ─────────
subchapter("7.6", "Challenge 6: A slow external source", ["N: Challenge six. One verdict depends on a slow outside source: how do we answer fast without lying about what we know?"])
qs("Interviewer · challenge 6 of 7", "“The authority gives you only a lookup API: one second a call, a hundred calls a second. It is down for two days. And a new ban covers a slash-sixteen you already cached verdicts for.”", [
 "I: The authority gives you only a lookup A-P-I: one second a call, a hundred calls a second. It is down for two days. And a new ban covers a slash sixteen you already cached verdicts for.", "[pause: 2.0]"])

S(dia(K(6, "a slow external source"), "A hundred calls a second against twenty thousand addresses", "ch6-attack", q=True, red=True,
      extra=strip(("case", "Naive answer", "“Call the API on each new address and cache the answer.”"),
                  ("case", "Break", "The adapter cannot keep up, and a per-address cache outlives a wider ban."))), [
 "C: The naive answer: call the A-P-I on each new address and cache the answer. Look at the adapter and the authority, outlined red. The adapter cannot keep up, and a cache of per-address answers will outlive a wider ban."], cls="dia")

S(dia(K(6, "the case"), "Two hundred times over, and seventeen percent coverage", "authority"), [
 "C: The case. Twenty thousand first-seen addresses a second against a limit of a hundred calls a second. Two hundred times over. Even running all day, a hundred a second gives eight point six million lookups against about fifty million distinct addresses: seventeen percent. These are illustrative numbers. And a request cannot wait a second on a call that is rate limited anyway."], cls="dia")

S(plain(K(6, "the cache that lies"), "A per-address verdict outlives a wider ban", '<pre class="trace"><span class="t">day 0  </span>192.0.2.7 checked: allowed. Cached for 24 h as an <span class="bad">address verdict</span>\n<span class="t">day 0  </span>the authority bans 192.0.0.0/16 (it includes 192.0.2.7)\n<span class="t">day 0 + 1 h  </span>192.0.2.7 is served from cache: <span class="bad">allowed, for 23 more hours</span>\n<span class="t">fix  </span>store the <span class="good">range rule</span> with a version; it supersedes address verdicts by version</pre>' +
  '<div class="hedge"><b class="t">Label the numbers</b>Illustrative. The point is the key: a cache of verdicts must be keyed by the rule the authority returns, not by the address that was asked.</div>', q=True, red=True), [
 "C: The cache that lies. An address is checked and allowed, and cached for a day as an address verdict. Later the authority bans the whole slash sixteen that contains it. An hour on, that address is served from the cache: allowed, for another twenty-three hours. The fix is to cache by the rule the authority returns, as a range rule with a version, so a wider ban supersedes address verdicts by version."])

S(dia(K(6, "the fix"), "Prefer a bulk list; otherwise a bounded cache and a budget", "ch6-fix",
      extra=strip(("fixb", "Mechanism", "Mirror a bulk list if one exists. Otherwise: a range-keyed verdict cache with a bounded lifetime, single-flight lookups, a token bucket spent on the busiest addresses, a stated first-seen policy."),
                  ("whyb", "Property", "Bounded exposure instead of unbounded wait (L2, S1): the request path never waits for the authority."))), [
 "C: The fix, on the baseline. The new adapter box mirrors into the rule store. First: if there is any bulk list or change feed, mirror it and use the same pipeline as every other list, and use the lookup only to verify. Second, with only a lookup: a cache keyed by range, with a lifetime no longer than the allowed staleness or the legal grace period. Single-flight lookups per key. And a token bucket of a hundred a second, spent on the highest-volume addresses first."], cls="dia")

S(dia(K(6, "sequence"), "One lookup, one range rule", "seq-ch6-authority"), [
 "C: As a sequence. The agent asks for a verdict on an address. The adapter has no entry, has tokens in its budget, and sends one lookup. The authority answers: banned, covers the slash sixteen, valid for twenty-four hours. The adapter stores a range rule with a version, which supersedes any address verdicts. The agent gets deny. And if the authority is down, the adapter serves expired entries inside a grace period, flags the decisions it made on expired data, and alerts."], cls="dia")

qs("Interviewer · the second-level push", "“The API is down for two days, and your cache lifetime is one day.”", [
 "I: The API is down for two days, and your cache lifetime is one day.", "[pause: 2.0]"])

S(plain(K(6, "the second fix, and the honest limit"), "A grace period, flagged, with a named owner", '<div class="cards c2">'
  '<div class="cd grn"><h3>Grace</h3><p>Serve expired verdicts for a stated number of days. Every decision made on expired data is flagged in the log. The legal owner decides how many days.</p></div>'
  '<div class="cd amb"><h3>The exposure</h3><p>First-seen addresses during the outage. Reduce it by spending the budget on the highest-volume ones first, and by asking for a bulk feed.</p></div></div>' +
  line("With only a slow lookup, full coverage is not possible. Say so, and ask for a better source.", "r")), [
 "C: A grace period. Serve expired verdicts for a stated number of days, flag every decision made on expired data in the log, and alert. The legal owner decides how many days. The exposure is first-seen addresses during the outage, which I reduce by spending the budget on the highest-volume ones first and by asking for a bulk feed.",
 "C: The honest limit: with only a slow lookup, full coverage is not possible. I say so, and I ask for a better source."])

say_slide("“I never call a slow authority on the request path. If there is a bulk list, I mirror it. If there is only a lookup, I cache verdicts for no longer than the allowed staleness, coalesce lookups, spend the rate budget on the highest-volume addresses, and write down what happens on a first-seen address and on an outage. Full coverage is not possible, so I say how much we have, and I ask for a better feed.”", [
 "V: If asked, I'd say: I never call a slow authority on the request path. If there is a bulk list, I mirror it. If there is only a lookup, I cache verdicts for no longer than the allowed staleness, coalesce lookups, spend the rate budget on the highest-volume addresses, and write down what happens on a first-seen address and on an outage. Full coverage is not possible, so I say how much we have, and I ask for a better feed.", "[pause: 1.0]",
 "N: Last question: how would you know?"])

# ───────── Challenge 7 · observability ─────────
subchapter("7.7", "Challenge 7: How would you know?", ["N: Challenge seven. Every machine is green and the promise is broken: how would we know?"])
qs("Interviewer · challenge 7 of 7", "“A ban was published an hour ago and one region is still serving the banned source. The dashboard is green. How would you have known?”", [
 "I: A ban was published an hour ago and one region is still serving the banned source. The dashboard is green. How would you have known?", "[pause: 2.0]"])

S(dia(K(7, "how would you know"), "The relays are healthy. The promise is broken.", "ch7-attack", q=True, red=True,
      extra=strip(("case", "Naive answer", "“Watch the CPU and the error rate of the relays.”"),
                  ("case", "Break", "The dashboard watches the machines. The promise is somewhere else."))), [
 "C: The naive answer: watch the C-P-U and the error rate of the relays. Look at the picture: the relay box is outlined, and it is the box the dashboard watches. It is green. The promise is broken somewhere that dashboard does not look."], cls="dia")

S(plain(K(7, "the case"), "Green on the machines, red on the promise", '<pre class="trace"><span class="t">relay health  </span>100 %, origin latency 40 ms: <span class="good">green</span>\n<span class="t">region ap-2   </span><span class="bad">4 % of nodes on 8,360,990; the rest on 8,361,004</span>\n<span class="t">why           </span>the push to one zone fails quietly; polls hit a relay cache that is stale\n<span class="t">block rate    </span>0.2 % in ap-2 against 0.5 % elsewhere: <span class="bad">a ban that did not land</span></pre>' +
  '<div class="hedge"><b class="t">Label the numbers</b>Illustrative. The shape holds: every machine metric is fine, and one pair of numbers says otherwise.</div>', q=True, red=True), [
 "C: The case. The relays report a hundred percent healthy, origin latency forty milliseconds: green. But in one region, four percent of nodes are a version behind. The push to one zone fails quietly, and polls hit a relay cache that is stale. Meanwhile the block rate in that region is point two percent against point five elsewhere. A ban did not land.",
 "C: Illustrative numbers. The shape holds: every machine metric is fine, and one pair of numbers says otherwise."])

S(dia(K(7, "the fix"), "Measure the promise, with a probe", "ch7-fix",
      extra=strip(("fixb", "Mechanism", "SLIs on the promise: version skew, propagation lag, snapshot age, apply failures, block-rate against baseline. A synthetic banned key per region. Decisions logged with their version."),
                  ("whyb", "Property", "It turns the propagation promise into something you can watch."))), [
 "C: The fix: a metrics and probe box fed by the controller. The service level indicators describe the promise, not the machines. And a synthetic probe: a banned key published on a schedule, with a request sent through the real path to check that it is denied within thirty seconds, in every region. Decisions are logged with their rule version, so an audit has an answer."], cls="dia")

S(plain(K(7, "the SLIs"), "Indicators on the promise", table(["SLI", "Target (initial)", "Why"], [
  ["Version skew: nodes on the current version within 30 s", "≥ 99.9 % per region", "the propagation SLO, directly"],
  ["Propagation lag", "p99.9 under 30 s", "per publish, end to end"],
  ["List age per node against its bound", "no node past its bound", "the stale policy, watched"],
  ["Apply failures, checksum mismatches", "≈ 0", "a corrupt artifact or a bad relay"],
  ["Block rate against baseline, per version", "within a few points", "the gate, and the bad-rule alarm"],
  ["Lookup-tier hit rate", "within capacity", "the filter and the attack"]], "bt sm")), [
 "C: The indicators, on the promise. Version skew: the share of nodes on the current version within thirty seconds, at least ninety-nine point nine percent per region. Propagation lag, at the ninety-nine point ninth percentile. List age per node against its bound. Apply failures and checksum mismatches, near zero. Block rate against its baseline, per version. And the lookup tier's hit rate. All initial targets."])

S(plain(K(7, "symptom pairs"), "Two metrics, one conclusion", table(["Metric A", "Metric B", "Conclusion"], [
  ["skew up", "one zone's relay cache age up", "a stale relay cache, not the nodes"],
  ["block rate down in one region", "that region's applied version behind", "<b>a ban that did not land</b>"],
  ["block rate up", "a new version just applied", "a bad rule: the gate, not the relay"],
  ["apply failures up", "checksum mismatches up", "a corrupt artifact at the origin"],
  ["lookup-tier load up", "hit rate up", "an attack, or a filter that is too small"]], "bt sm") +
  grade("One metric tells you something is wrong. Two tell you where, and who gets the page.")), [
 "C: Read metrics in pairs, so each page names a cause. Skew up with one zone's relay cache age up: a stale relay cache. Block rate down in one region with that region's version behind: a ban that did not land, tonight's case. Block rate up with a new version: a bad rule, so the gate, not the relay. Apply failures with checksum mismatches: a corrupt artifact at the origin. One metric says something is wrong. Two say where."])

S(dia(K(7, "sequence"), "The probe, end to end", "seq-ch7-probe"), [
 "C: The probe as a sequence. Every five minutes the probe publishes a synthetic banned key as a new version. Normal distribution carries it. Then the probe sends a request from the synthetic key through the real path, in each region. In a healthy region the answer is deny within thirty seconds. If a region still allows it after thirty seconds, the probe pages, with that node's applied version attached. This tests the whole chain every time, not each part."], cls="dia")

qs("Interviewer · the second-level push", "“The probe passes and a real ban is still missing. Or the block rate is flat because traffic bypasses the enforcement point.”", [
 "I: The probe passes and a real ban is still missing. Or the block rate is flat because traffic bypasses the enforcement point.", "[pause: 2.0]"])

S(plain(K(7, "the second fix, and the honest limit"), "Per-node reports, and coverage", '<div class="cards c2">'
  '<div class="cd grn"><h3>Skew from reports, not only probes</h3><p>A probe tests one key. Every node reports the version it runs, so a node that is behind shows up even if the probe passes.</p></div>'
  '<div class="cd amb"><h3>Coverage is a metric</h3><p>The share of traffic that passes through an enforcement point, and a counter of requests that skipped the check.</p></div></div>' +
  line("You can detect a late ban after the fact and alarm on its precursors. You cannot observe an absence of risk.", "r")), [
 "C: Two answers. Skew is measured per node, from reports, not only from probes: a node that is behind shows up even when the probe's key got through. And coverage is a metric: the share of traffic that passes through an enforcement point, and a counter of requests that skipped the check, so a flat block rate cannot hide a bypass.",
 "C: The honest limit: we can detect a late ban after the fact and alarm on its precursors. We cannot observe an absence of risk."])

say_slide("“I alert on the promise: the share of nodes on the current version within thirty seconds, per region, plus a synthetic banned key sent through the real path. I read metrics in pairs so each page names a cause, and every decision logs the rule version so an auditor gets an answer. A green relay dashboard says nothing about whether a ban landed.”", [
 "V: If asked, I'd say: I alert on the promise. The share of nodes on the current version within thirty seconds, per region, plus a synthetic banned key sent through the real path. I read metrics in pairs so each page names a cause, and every decision logs the rule version so an auditor gets an answer. A green relay dashboard says nothing about whether a ban landed.", "[pause: 1.0]"])

# ───────────────────────── 8 · build cost (AUX) ─────────────────────────
chapter(8, "Build cost", 6, "The manager layer: people, months, buy against build", [
 "N: This chapter is marked auxiliary. It is the engineering-manager layer, optional in a Staff round.",
 "C: A denylist system is not one project. It is three, and they differ by an order of magnitude."], aux=True)

S(plain("Build cost · three releases", "R0, R1, R2: not one project", table(["", "R0 · Prototype", "R1 · Production", "R2 · Platform"], [
  ["Goal", "Prove the model with one list", "One or two lists, the full fleet, safe to depend on", "Several key types, regional layers, very large lists, streaming push"],
  ["Scope", "Rule store, compiler, snapshot to object storage, 10 s manifest poll, atomic swap", "Versions and deltas, relay tree, checksums, validation, allowlist, staged rollout and gates, kill flag, reports, decision log, console, audit", "Push streams, layered rules, filter + lookup tier, external mirror adapter, per-key-type enforcement"],
  ["SLO · on-call", "none", "99.9 % in 30 s · business hours", "error budgets · 24/7, shared rotation"],
  ["Effort, engineer-months", "1–2", "18–24", "50–90"]], "bt sm"), ), [
 "C: Three releases, called R-zero, R-one and R-two so nobody confuses them with design versions. A prototype with one list: a rule store, a compiler, a snapshot in object storage, a ten-second manifest poll and an atomic swap. About a month or two.",
 "C: Production is R-one: versions and deltas, the relay tree, checksums, validation, staged rollout, a kill flag, reports, a console and audit. Four engineers for five or six months: eighteen to twenty-four engineer-months. A platform is R-two: push streams, layered rules, the lookup tier. Fifty to ninety. The best question is which of these we are asked for, and who owns the first list."], cls="aux")

S(plain("Build cost · R1 in detail", "Who, and how long", table(["Role", "FTE", "Owns"], [
  ["Tech lead", "1.0", "the version and ordering model, the merge, design reviews"],
  ["Senior backend", "1.0", "rule store, compiler, relays, rollout"],
  ["Backend", "1.0", "the agent library, the console, the first list's migration"],
  ["SRE", "1.0", "the controller, SLIs, probes, runbooks: the rollout is operations"],
  ["Manager · policy liaison", "0.3 · 0.2", "roadmap, adoption, the contract with policy"]], "bt sm") + chips("RFC with policy 3 wk", "skeleton 4", "correctness 6", "safety 5", "operations 4", "shadow then cutover 4")), [
 "C: R-one in detail. A tech lead for the version model and the merge. A senior backend engineer for the rule store, compiler and relays. A backend engineer for the agent, the console and the first migration. A full-time S-R-E, because the rollout is operations. Phases: three weeks of design review with the policy owner, four for a walking skeleton, six for correctness with a convergence harness under injected faults, five for safety, four for operations, and four for shadow mode, then cutover.",
 "C: One assumption to state: if there is no named owner and first list, the right decision is not to build."], cls="aux")

S(plain("Build cost · ownership", "People dominate the five years", chips("illustrative", "engineer-months") + '<div class="tiles" style="--n:3"><div class="tile blue"><b>22</b><span>to build R1</span></div>'
  '<div class="tile blue"><b>1.5 × 60</b><span>= 90 to run it for five years</span></div><div class="tile"><b>≈ 112</b><span>≈ 9 engineer-years; infrastructure is a small share</span></div></div>' +
  line("A pipeline with no owner becomes an incident with no owner.", "a")), [
 "C: Ownership. Twenty-two engineer-months to build. Then about one and a half people for five years, which is ninety. A hundred and twelve in total, about nine engineer-years, and infrastructure is a small share of it. All illustrative. People dominate. And a pipeline with no owner becomes an incident with no owner."], cls="aux")

S(plain("Build cost · build, adopt, buy, or don't", "Four options, one table", table(["Option", "To a pilot", "5-year, eng-months (illustrative)", "When it wins"], [
  ["<b>Don't</b>: the edge provider's managed IP sets", "~2 weeks", "~15", "the limits fit; check first, every time"],
  ["<b>Adopt</b>: a configuration-distribution fabric for transport; our compiler, gates and audit", "~8 weeks", "~70", "a distribution fabric is already run"],
  ("pick", ["<b>Hybrid</b>: build compiler, gates and audit; buy the transport", "~3 months", "~85", "<b>R1 pick, if a transport exists</b>"]),
  ["<b>Build</b>: this design, end to end", "~5 months, 4 people", "~112", "lists beyond managed limits, custom keys, layered rules, audit"]], "bt sm mx")), [
 "C: Build, adopt, buy, or don't. Don't: use the edge provider's managed I-P sets. Two weeks to a pilot. Check first, every time. Adopt a configuration-distribution fabric for transport, with our own compiler, gates and audit: about eight weeks. The hybrid, build the compiler, the gates and the audit and buy the transport, is my R-one pick if a transport exists. Build everything: about a hundred and twelve engineer-months, justified for lists beyond managed limits, custom keys, layered rules and audit.",
 "C: I would write the buy-versus-build memo before any code, with the first list owner's commitment in it."], cls="aux")

S(plain("Build cost · risks, cuts, people", "What I would never cut", '<div class="cards c3">'
  '<div class="cd red"><h3>Never cut</h3><p>Versions with checksums. Staged rollout with a gate. The allowlist. A kill flag. Last known good on disk. The version in the decision log.</p></div>'
  '<div class="cd amb"><h3>Cut first</h3><p>Push streams: the 10 s poll meets the target. Regional layers. The second key type. The lookup tier. The console UI.</p></div>'
  '<div class="cd"><h3>Top risks</h3><p>A bad rule. Owner ambiguity. The control plane as a single point. No adopter. Scope creep into a general config platform.</p></div></div>'), [
 "C: What I would never cut: versions with checksums, a staged rollout with a gate, the allowlist, a kill flag, last known good on disk, and the version in the decision log. What I'd cut first: push streams, because the ten-second poll meets the target, regional layers, the second key type, the lookup tier and the console.",
 "C: Top risks. A bad rule: gates, the allowlist, and a game day that practises one. Owner ambiguity: policy writes the list, platform owns the pipe, and the propagation target is the contract between them. The control plane as a single point: a drain budget, and nodes that work without it. No adopter: a named first list before any code. And scope creep into a general configuration platform."], cls="aux")

S(plain("Build cost · staffing, and the question to ask", "Small first. Do not add people in stabilisation.", '<div class="cards c2">'
  '<div class="cd"><h3>Over time</h3><p>Two people for the design and skeleton. Grow to four in the middle, where the agent, compiler and console parallelise. Hold steady while stabilising. Share on-call with the team that runs the sibling rollout system.</p></div>'
  '<div class="cd grn"><h3>The question before saying yes</h3><p>“What does a wrong block cost, who decides, and how fast must a ban land?”</p></div></div>'), [
 "C: Staffing. Start small, because design by committee is slow. Grow in the middle where the work parallelises: the agent, the compiler and the console. Do not add people while stabilising. Share the on-call with the team that runs the sibling rollout system.",
 "V: The question I ask before saying yes: what does a wrong block cost, who decides, and how fast must a ban land?", "[pause: 1.0]"], cls="aux")

# ───────────────────────── 9 · recap ─────────────────────────
chapter(9, "Recap", 7, "One picture, five paths, the mistakes, the thesis", [
 "C: Four minutes to close. One picture, one sentence per path, the contract between the owners, the mistakes to avoid, and the thesis."])

S(dia("Recap", "The whole design on one baseline", "base-final", chip=chips("validate", "versions", "relay tree", "atomic swap", "gates", "probes")), [
 "C: The final picture. The policy tool, and ingest with validation and an allowlist. The rule store with one version order. The origin and the relay tree with push and a ten-second manifest poll. The enforcement node with an atomic swap, a last known good copy and a lookup tier behind a filter. A controller with gates and a kill flag, a load balancer that drains stale nodes, a mirror for a slow source, and metrics with probes. Every box was added to answer one question the design raised."], cls="dia")

S(plain("Recap · one sentence per path", "Five paths", table(["Path", "In one sentence"], [
  ["<b>Publish</b>", "Validate, approve, one transaction, one version"],
  ["<b>Distribute</b>", "Manifest, delta or snapshot, verify the chain, swap one pointer"],
  ["<b>Enforce</b>", "Allowlist, exact key, longest prefix, the version in the verdict"],
  ["<b>Explain</b>", "The version joins the rule history"],
  ["<b>Roll back</b>", "A new, higher version, and a kill flag on its own channel"]], "bt")), [
 "C: Five paths, one sentence each. Publish: validate, approve, one transaction, one version. Distribute: manifest, then a delta or a snapshot, verify the chain, swap one pointer. Enforce: allowlist, exact key, longest prefix, with the version in the verdict. Explain: the version joins the rule history. Roll back: a new, higher version, and a kill flag on its own channel."])

S(plain("Recap · seven fixes", "Each one names the property it protects", table(["Challenge", "Fix", "Property"], [
  ["1 Offline node", "manifest, delta window, snapshot fallback, chained checksums", "L1, S2"],
  ["2 Order and overlap", "one version order, per-key version, precedence", "S1, S2, L1"],
  ["3 Bad push", "validation, allowlist, canary gates, kill flag, local breaker", "<b>S2</b>"],
  ["4 Stale", "bound + action signed by the owner, drain with a cap", "L3"],
  ["5 Does not fit", "filter, exact tier, cache, per-node budget", "S2"],
  ["6 Slow source", "mirror, range cache, budget, grace, stated policy", "L2, S1"],
  ["7 Silent failure", "skew, probes, symptom pairs, coverage", "all"]], "bt sm")), [
 "C: Seven fixes, each naming the property it protects. One: manifest, window and chained checksums, for convergence and integrity. Two: one version order and a per-key version, for the intended state. Three: validation, the allowlist, canary gates, the kill flag and a local breaker, for safety against the wrong block. Four: a signed bound and an action. Five: a filter, an exact tier and a cache. Six: a mirror, a range cache and a stated policy. Seven: skew, probes and coverage."])

S(plain("Recap · the contract between the owners", "Policy owns the list. Platform owns the pipe.", '<div class="cards c2">'
  '<div class="cd"><h3>Policy owns</h3><p>What is listed, the reason, the allowlist, the action on a match, the signed staleness bound, and the risk of a late ban.</p></div>'
  '<div class="cd grn"><h3>Platform owns</h3><p>The pipeline, the versions, the gates, the SLIs, and the propagation target: <b>99.9 % of nodes within 30 s</b>. That number is the contract between them.</p></div></div>' +
  line("A bad denylist is a global outage, so a push gets the same discipline as a binary.", "a")), [
 "C: Two owners, and a contract. Policy owns what is listed, the reason, the allowlist, the action on a match, the signed staleness bound, and the risk of a late ban. Platform owns the pipeline, the versions, the gates, the indicators, and the propagation target: ninety-nine point nine percent of nodes within thirty seconds. That number is the contract between them.",
 "C: And a bad denylist is a global outage, so a push gets the same discipline as a binary."])

S(plain("Recap · if asked about a second key type", "A user id, in three lines", '<div class="cards c3"><div class="cd grn"><h3>Same pipeline</h3><p>The rule store, the compiler, the relays, the gates and the audit. The key kind is a field.</p></div>'
  '<div class="cd amb"><h3>Different enforcement point</h3><p>After authentication, in the application layer, with the same agent library.</p></div>'
  '<div class="cd red"><h3>Different bound</h3><p>A user ban may need a shorter bound than an address ban. The owner signs it.</p></div></div>'), [
 "C: If asked about a second key type, a user I-D. Same pipeline: the rule store, compiler, relays, gates and audit, with the key kind as a field. A different enforcement point: after authentication, in the application layer, with the same agent library. And possibly a different bound, which the owner signs. Nothing about the design had to change, which is why I did not design it out."])

S(plain("Recap · common mistakes in this round", "Ten ways this round goes wrong", '<div class="cards c2"><div class="cd red"><h3>Design</h3><ul style="font-size:17pt"><li>A lookup per request on the path</li><li>“Eventually consistent” with no number</li><li>No versions or checksums</li><li>Trusting arrival order</li><li>A full download per node per change</li></ul></div>'
  '<div class="cd amb"><h3>Judgment</h3><ul style="font-size:17pt"><li>Failing closed fleet-wide, or open silently</li><li>Never asking who owns the failure policy</li><li>A Bloom filter used as a verdict</li><li>One big push, no canary, no allowlist</li><li>A green relay dashboard as proof</li></ul></div></div>'), [
 "C: Ten mistakes in this round. In the design: a lookup per request on the path. Eventually consistent with no number. No versions or checksums. Trusting arrival order. A full download per node per change.",
 "C: In judgment: failing closed fleet-wide, or open without saying so. Never asking who owns the failure policy. A Bloom filter used as a verdict. One big push with no canary and no allowlist. And a green relay dashboard as proof that a ban landed."])

key("The close", "The check is local because it must be fast and independent. The list cannot be, so I gave it <em>versions</em>, a <em>bound</em> on how old it may be, and the <em>discipline of a release</em>. So a ban lands quickly and a mistake does not.", [
 "V: The check is local because it has to be fast and independent. The list cannot be local, so I gave it versions, a bound on how old it may be, and the discipline of a release. Everything I built is there so that a ban lands quickly and a mistake does not.", "[pause: 1.2]",
 "C: Thank you. I'll stop there."])
