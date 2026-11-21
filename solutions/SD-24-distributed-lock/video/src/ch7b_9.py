from dsl import *
K = lambda n, t: f"Challenge {n} of 7 · {t}"

# ───────── Challenge 4 · leader, partition, losing the group ─────────
subchapter("7.4", "Challenge 4: Leader loss, partition, group loss")
qs("Interviewer · challenge 4 of 7", "“The leader dies mid-grant, and a partition leaves two of the five replicas talking to some clients. What do those clients see?”", [
 "I: The leader dies mid-grant, and a partition leaves two of the five replicas talking to some clients. What do those clients see?", "[pause: 2.0]"])

S(dia(K(4, "leader, partition, group loss"), "What do the clients on the small side see?", "ch4-attack", q=True, red=True,
      extra=strip(("case", "Naive answer", "“Promote a follower quickly, and let the minority side keep serving so we stay available.”"),
                  ("case", "Break", "The group box. Two replicas must not grant on their own."))), [
 "C: The naive answer: promote a follower fast, and let the minority side keep serving, to stay available. Look where it breaks, the consensus group. Serving on the small side means two sides can each grant the same name."], cls="dia")

S(dia(K(4, "the case"), "Five replicas, one partition", "partition"), [
 "C: The case. Replicas one to five. R-one leads in term seven. A partition isolates R-one and R-two from R-three, four and five. The big side hears no leader for a second and a half and elects R-three in term eight. R-one still believes it leads, but it can reach only one other replica out of five. It cannot get a majority. So it cannot commit, and cannot grant."], cls="dia")

S(dia(K(4, "sequence"), "Both sides ask for the same name", "seq-ch4-election"), [
 "C: As a sequence. Client Y, on the majority side, asks for x. R-three commits it with a majority: granted, token nine thousand and one. Client X, on the minority side, asks R-one for x. R-one cannot reach a majority, so it answers unavailable. No grant. When the partition heals, R-one sees term eight, steps down, and discards anything uncommitted. The small side got an honest no."], cls="dia")

S(dia(K(4, "the fix"), "Majority commit, terms, a leader lease, a grace period", "ch4-fix",
      extra=strip(("fixb", "Mechanism", "Only the majority commits. A stale leader steps down on a higher term. A new leader treats every session as alive for one lease."),
                  ("whyb", "Property", "Safety unconditional. Liveness given up on the minority side."))), [
 "C: The fix is mostly what version two already had, plus two details. Only the majority side commits. A stale leader steps down when it sees a higher term. Heartbeats are answered by the leader under a short leader lease, so no log entry per beat. And a new leader treats every session as alive for one full lease after election, called a grace period. Otherwise a failover would see every heartbeat gap as a death and evict every lock at once."], cls="dia")

S(plain(K(4, "why it works"), "The honest CP position", '<div class="prop safe"><div class="lbl">Safety · kept</div><p>Two replicas cannot commit. So a name never has two holders because of a partition.</p></div>'
  '<div class="prop live"><div class="lbl">Liveness · given up, on the small side only</div><p>The minority gets “unavailable”. A failover takes about 2 s. Tokens stay monotonic, because they are log indexes.</p></div>' +
  line("There is no clever third option. Interviewers listen for candidates who try to invent one.", "a")), [
 "C: Why it works. Safety is kept: two replicas cannot commit, so a partition cannot create two holders. Liveness is given up, on the small side only. A failover costs about two seconds. And tokens stay monotonic across terms, because they are log indexes.",
 "C: There is no clever third option here, and I won't pretend there is. I'd rather say the position plainly: for a correctness lock, unavailability of the lock service must become unavailability of the protected operation. If the business cannot accept that, the requirement is really an efficiency lock, and I'd make the resource idempotent."])

qs("Interviewer · the second-level push", "“Three of the five replicas are gone. Or someone restores last night's snapshot. What happens to the tokens?”", [
 "I: Three of the five replicas are gone. Or someone restores last night's snapshot. What happens to the tokens?", "[pause: 2.0]"])

S(plain(K(4, "why a restore is wrong"), "Restoring an old snapshot reissues tokens", '<pre class="trace"><span class="t">Mon 23:00  </span>snapshot taken. Highest token for invoice-17: 41\n<span class="t">Tue 09:00  </span>grants continue: tokens 42, 43 ... 9,000 issued. Resource stores 9,000\n<span class="t">Tue 11:00  </span><span class="bad">all replicas lost. Restore Monday\'s snapshot</span>\n<span class="t">Tue 11:05  </span>next grant of invoice-17: <span class="bad">token 42 again</span>\n<span class="t">Tue 11:05  </span>resource holds 9,000: <span class="bad">rejects every new holder as stale</span></pre>' +
  '<div class="hedge"><b class="t">Both directions</b>Tokens reused means the check wrongly rejects. Tokens that restart low can also let a stale holder through.</div>', q=True, red=True), [
 "C: Without a majority, the service fails closed: libraries reach their local deadlines, get LockLost, and stop. That part is fine. The dangerous part is the restore. Restore Monday's snapshot, and the log index goes back. The next grant of that name reuses a token that was already issued. The resource has stored a much higher number, so it rejects every new holder as stale. And in the other direction, a stale holder from before the loss could slip through. Tokens must never go backwards, even across a disaster."])

S(dia(K(4, "the second fix"), "Start empty, higher epoch, wait one maximum lease", "seq-ch4-recovery"), [
 "C: So disaster recovery is not restore. It is start empty with a higher epoch. One: the operator bumps the durable epoch, six to seven, in the epoch store. Two: the new group starts empty, with its token floor at epoch seven, shifted left forty-eight bits. Three: a quiet period of one maximum lease, sixty seconds, in which the group refuses grants, so every old holder has stopped on its own deadline. Four: libraries open sessions again, and grants resume with tokens above everything ever issued."], cls="dia")

S(plain(K(4, "the cost, and the arithmetic"), "A minute of outage against a double grant", '<div class="tiles" style="--n:3"><div class="tile blue"><b>60 s</b><span>quiet period: the cap on a lease</span></div>'
  '<div class="tile blue"><b>16 + 48</b><span>bits: epoch and index</span></div><div class="tile"><b>65,536</b><span>rebuilds before the epoch runs out</span></div></div>' +
  line("An outage of a minute is cheap. The alternative is two holders.", "a")), [
 "C: The cost is a minute of outage during a rebuild. The quiet period equals the longest lease we allow. The epoch is sixteen bits, so sixty-five thousand rebuilds, far more than will ever happen. All of that is derived, not measured. A minute of outage is cheap, next to the alternative of two holders."])

say_slide("“Under partition I choose safety: the minority side refuses, it does not guess. After the loss of a whole group I start empty with a higher epoch, so every new token exceeds every old one, and I wait out the longest possible lease before granting. The outage is a minute. The alternative is two holders.”", [
 "V: If asked, I'd say: under partition I choose safety. The minority side refuses, it does not guess. After the loss of a whole group I start empty with a higher epoch, so every new token exceeds every old one, and I wait out the longest possible lease before granting. The outage is a minute. The alternative is two holders.", "[pause: 1.0]",
 "N: Now the failure is not a fault. It is success: too much traffic."])

# ───────── Challenge 5 · overload ─────────
subchapter("7.5", "Challenge 5: The top of the hour")
qs("Interviewer · challenge 5 of 7", "“At the top of the hour traffic triples, and two thousand clients retry at once after a network blip. What happens, and what do you do?”", [
 "I: At the top of the hour traffic triples, and two thousand clients retry at once after a network blip. What happens, and what do you do?", "[pause: 2.0]"])

S(dia(K(5, "the top of the hour"), "What happens to one group at three times the load?", "ch5-attack", q=True, red=True,
      extra=strip(("case", "Naive answer", "“Add replicas, or shorten the lease so dead holders clear faster.”"),
                  ("case", "Break", "One group: about 30,000 writes a second against about 15,000."))), [
 "C: The naive answers: add replicas, or shorten the lease. Neither touches the problem. One group carries about fifteen thousand committed writes a second, and the peak is thirty thousand. The group box is the bottleneck."], cls="dia")

S(plain(K(5, "the trace"), "A queue that outlives the lease", '<pre class="trace"><span class="t">t = 0 s    </span>peak: 30,000 writes/s arrive, group commits 15,000/s\n<span class="t">t = 1 s    </span>backlog 15,000 writes. p99 acquire: <span class="bad">1 s</span>\n<span class="t">t = 10 s   </span>backlog <span class="bad">150,000</span>. Latency now exceeds the 10 s lease\n<span class="t">t = 10+ s  </span>leases expire while grants are in flight; clients retry\n<span class="t">t = 11 s   </span><span class="bad">retries add load: metastable collapse</span></pre>' +
  '<div class="hedge"><b class="t">More replicas?</b>Every write must reach a majority. Replicas add fault tolerance, not write throughput.</div>', q=True, red=True), [
 "C: Trace it. Thirty thousand writes a second arrive and the group commits fifteen. The backlog grows by fifteen thousand a second. After ten seconds it is a hundred and fifty thousand deep, and latency is longer than the ten-second lease itself. Grants that were in flight have already expired. Clients retry, which adds load. A metastable collapse: the system cannot recover even if the peak passes.",
 "C: And more replicas do not help. Every write must reach a majority. Replicas add fault tolerance, not write throughput. These figures are illustrative, from the estimates."])

S(dia(K(5, "the fix"), "Partition by name, admit at the edge", "ch5-fix",
      extra=strip(("fixb", "Mechanism", "slot = hash(name) mod 64, mapped to 4 groups. Gateway quotas shed with retry-after. Library backoff with jitter. Sessions. Batched syncs."),
                  ("whyb", "Property", "Liveness inside capacity. Locks are independent per name, so partitioning costs nothing."))), [
 "C: The fix. Hash the name into sixty-four slots, and map slots to four groups. Thirty thousand over fifteen thousand times half is four. The gateway applies per-tenant quotas, and answers overloaded with a retry-after, instead of queueing. The library retries with jittered backoff. Sessions keep renewal at about a hundred and twenty a second, not four hundred and eighty. And the leader batches many entries into one disk sync.",
 "C: This works because locks are independent per name. There are no cross-group transactions, so the partition is free."], cls="dia")

S(dia(K(5, "sequence"), "Shed at the edge, retry with jitter", "seq-ch5-admission"), [
 "C: As a sequence. The library asks. The gateway sees the tenant over quota, or the group's queue deep, and answers overloaded, retry after two hundred milliseconds. The library waits that long plus a random jitter, so two thousand clients do not return in the same instant. It retries, and this time it is admitted, routed to the leader, and granted."], cls="dia")

qs("Interviewer · the second-level push", "“One group goes bad. Or you need to move a slot while its locks are held.”", [
 "I: One group goes bad. Or you need to move a slot while its locks are held.", "[pause: 2.0]"])

S(dia(K(5, "the honest limit"), "A quarter fails closed. A move freezes, drains, bumps the epoch", "slots"), [
 "C: A bad group takes a quarter of the names with it and fails closed. The other three are untouched. That is the blast radius, and it is why I shard even though the data is tiny. Moving a slot is the dangerous part. A name moving while it is held is a correctness hazard. So: freeze the slot, drain its held locks, which takes at most one maximum lease, bump the slot's epoch so the new group's token floor sits above the old group's, then unfreeze in the new group.",
 "C: Skip the epoch bump and a name that moves to a group with a lower log index would see its tokens go backwards. Same rule as before: tokens never go back."], cls="dia")

say_slide("“I size for the peak: thirty thousand writes a second against a fifteen thousand ceiling means four groups with headroom. Replicas do not add write throughput. I shed load at the gateway with a retry-after, make clients back off with jitter, and shard by name because locks are independent. A bad shard fails closed for a quarter of the names.”", [
 "V: If asked, I'd say: I size for the peak. Thirty thousand writes a second against a fifteen thousand ceiling means four groups with headroom. Replicas do not add write throughput. I shed load at the gateway with a retry-after, make clients back off with jitter, and shard by name because locks are independent. A bad shard fails closed for a quarter of the names.", "[pause: 1.0]",
 "N: Spreading across groups does not help one name."])

# ───────── Challenge 6 · hot name ─────────
subchapter("7.6", "Challenge 6: A hot name, several locks")
qs("Interviewer · challenge 6 of 7", "“One name gets forty attempts a second, and each hold lasts a hundred milliseconds. What happens?”", [
 "I: One name gets forty attempts a second, and each hold lasts a hundred milliseconds. What happens?", "[pause: 2.0]"])

S(dia(K(6, "a hot name"), "Who gets the lock, and who pays?", "ch6-attack", q=True, red=True,
      extra=strip(("case", "Naive answer", "“Everyone polls until they get it, or we keep a queue that grows.”"),
                  ("case", "Break", "The leader of the group that owns this one name."))), [
 "C: The naive answers: everyone polls until they get it, or we keep a queue that just grows. The pain lands on one box: the leader of the one group that owns this name. Sharding does not help, because one name lives in one group."], cls="dia")

S(dia(K(6, "the case"), "A name can grant at most one over the hold time", "hot-key"), [
 "C: The arithmetic. A hold of a hundred milliseconds means this name can grant at most ten a second. Forty attempts a second is four times over. If waiters poll every fifty milliseconds, thirty waiters make six hundred polls a second on this one name. Each release wakes all of them and twenty-nine lose: a herd. With an unbounded queue, it grows by thirty a second. After ten seconds a new waiter is three hundred deep and waits about thirty seconds, longer than its own lease. Illustrative numbers, but the shape is real."], cls="dia")

S(dia(K(6, "the fix"), "A bounded queue with directed hand-off", "ch6-fix",
      extra=strip(("fixb", "Mechanism", "Waiters queue per name, capped, session-scoped. Release grants to the head waiter in the same step. Beyond the cap: contended, retry-after."),
                  ("whyb", "Property", "Liveness and fairness without burning consensus. Waiting costs no writes."))), [
 "C: The fix. The new orange box: a waiter queue per name, with a cap, scoped to sessions so a dead waiter is reaped. A release grants directly to the head waiter in the same committed step. One write, one waiter woken. Beyond the cap, or the wait budget, the answer is contended with a retry-after. Waiting costs no writes. The herd is gone. Every wait is bounded."], cls="dia")

S(dia(K(6, "sequence"), "Release hands over in one step", "seq-ch6-queue"), [
 "C: As a sequence. Waiter one asks and is queued at position one. Waiter two asks and is queued at position two. Holder A releases with token seven. The leader commits, and the same step grants to waiter one, token eight. Waiter two keeps waiting, and if the cap or its maximum wait is exceeded, it gets contended with a retry-after instead of waiting forever."], cls="dia")

qs("Interviewer · the second-level push", "“A team now asks to acquire three locks atomically.”", [
 "I: A team now asks to acquire three locks atomically.", "[pause: 2.0]"])

S(plain(K(6, "several locks"), "Push back, and make deadlock heal itself", table(["Move", "What it does", "Cost"], [
  ["Push back first", "Atomic multi-name acquire across groups is a distributed transaction", "a rework of the caller, or two-phase commit"],
  ["Canonical order", "SDK sorts names and acquires in that order", "discipline, enforced in the library"],
  ["Try with timeout, release all", "back off and retry if the full set is not got in budget", "some wasted work"],
  ["Bounded leases", "any deadlock heals within one lease", "up to one lease of stall"]], "bt sm") +
  line("Detecting deadlock cycles is rarely worth it. Saying so is a better answer than describing the algorithm.", "a")), [
 "C: First I push back. Acquiring several names atomically across groups is a distributed transaction, and I would not offer it. If it must be done: a canonical order, with the library sorting names and acquiring in that order, so two callers cannot wait on each other in a cycle. Try with a timeout and release everything on failure. And bounded leases mean any deadlock that still happens heals within one lease. Building a wait-for graph to detect cycles is rarely worth it, and saying so is a better answer than describing the algorithm."])

S(plain(K(6, "the honest limit"), "A lock caps a name. A hot name is the wrong tool.", '<div class="cards c2"><div class="cd red"><h3>The limit</h3><p>A name grants at most one over the hold time. No design makes that bigger.</p></div>'
  '<div class="cd grn"><h3>Go back to the requirement</h3><p>Forty a second on one name means the caller wants a queue, or a single writer per partition, not a lock.</p></div></div>'), [
 "C: And an honest limit. A lock serialises. A name can grant at most one over the hold time, and no design makes that bigger. If one name is asked forty times a second, the caller does not want a lock. They want a queue, or a single writer per partition. That is a conversation to have with the team, not a feature to add."])

say_slide("“A lock serialises. If the name is hot, the lock is the wrong tool. I bound the queue, hand the lock directly to the next waiter so a release is one write, and return an explicit rejection beyond the limit. For several locks I fix the order, bound every wait, and rely on leases so a deadlock heals in one lease. I would not offer atomic multi-lock.”", [
 "V: If asked, I'd say: a lock serialises. If the name is hot, the lock is the wrong tool. I bound the queue, hand the lock directly to the next waiter so a release is one write, and return an explicit rejection beyond the limit. For several locks I fix the order, bound every wait, and rely on leases so a deadlock heals in one lease. I would not offer atomic multi-lock.", "[pause: 1.0]",
 "N: Everything so far assumed we would notice a failure. Would we?"])

# ───────── Challenge 7 · observability ─────────
subchapter("7.7", "Challenge 7: How would you know?")
qs("Interviewer · challenge 7 of 7", "“It is three in the morning. A team says duplicates are happening, and your dashboard is green. How would you have known?”", [
 "I: It is three in the morning. A team says duplicates are happening, and your dashboard is green. How would you have known?", "[pause: 2.0]"])

S(dia(K(7, "how would you know"), "Green dashboard, broken promise", "ch7-attack", q=True, red=True,
      extra=strip(("case", "Naive answer", "“Watch CPU, memory and uptime of the service.”"),
                  ("case", "Case", "Availability 99.99%, p99 8 ms: green. But one service has 12 FencedOut rejections a minute, and one name's hold time grew from 0.5 s to 9 s."))), [
 "C: The naive answer: watch the service's CPU, memory and uptime. Here is the case. Availability is ninety-nine point nine nine percent, p99 is eight milliseconds. Everything is green. And yet one service has twelve fenced-out rejections a minute, its renewal failures are rising, and on one name the hold time went from half a second to nine. The dashboard watches the machine. The promise is broken somewhere it does not look."], cls="dia")

S(plain(K(7, "the SLIs"), "Measure the guarantee, not the machine", table(["SLI", "Target (initial)", "Why"], [
  ["Acquire availability", "99.99%", "the headline contract"],
  ["Acquire latency p50 / p99", "3 ms / 20 ms", "locks sit in a request path"],
  ["Session-loss rate", "< 0.01% of sessions an hour", "every loss may abort work"],
  ["<b>Fenced-out writes</b>", "<b>alert on any</b>", "a stale holder reached a resource"],
  ["Elections per group per day", "< 1", "an unhealthy group, and the error budget"],
  ["Time to leader after failure", "< 2 s p99", "bounds the unavailable window"]], "bt sm")), [
 "C: So measure the guarantee. Acquire availability and latency, the headline contract. Session-loss rate, because every loss may abort someone's work. Fenced-out writes: alert on any. A fenced-out write means a stale holder reached a resource. It is either the safety net working, or the first symptom of a real problem, and I want to know which. Elections per group per day, under one. Time to a new leader under two seconds. All initial targets."])

S(plain(K(7, "symptom pairs"), "Which two numbers tell you what broke?", table(["Symptom", "Together with", "Conclusion"], [
  ["<span class='up'>Fenced-out writes</span>", "<span class='up'>renewal failures</span> on one client", "That client is pausing. The net worked. Fix the client"],
  ["<span class='up'>Elections</span>", "<span class='up'>acquire p99</span>", "An unhealthy group or disk"],
  ["<span class='up'>Hold-time tail</span>", "<span class='up'>waiter depth</span>", "Someone holds across a network call, or a hot name"],
  ["<span class='up'>Token gaps</span>", "<span class='up'>attempts</span>", "A retry storm"]], "bt sm sym") +
  line("One metric tells you something is wrong. Two tell you where.", "a")), [
 "C: Read metrics in pairs, so each page names a cause. Fenced-out writes rising together with one client's renewal failures: that client is pausing. The safety net worked. Fix the client. Elections rising with acquire p99: an unhealthy group or its disk. Hold-time tail up with waiter depth up: someone is holding a lock across a network call, or it is a hot name. Token gaps growing with attempts: a retry storm. One metric tells you something is wrong. Two tell you where."])

S(dia(K(7, "the fix"), "A canary, and the guarantee on a page", "ch7-fix",
      extra=strip(("fixb", "Mechanism", "SLIs on the guarantee, symptom pairs, a canary lock acquired continuously, an offline checker that replays the log for overlapping holds."),
                  ("whyb", "Property", "It turns the safety argument into something you can watch."))), [
 "C: The fix: a metrics and canary box fed by the groups and the resource checks. A canary lock acquired continuously, so a quiet failure still shows up as a missed acquire. And an offline checker that replays the grant log for overlapping holds. The property: it turns the safety argument into something you can watch."], cls="dia")

S(dia(K(7, "the error budget"), "Turn a target into a constraint", "error-budget"), [
 "C: And turn the target into a constraint. Ninety-nine point nine nine percent of a thirty-day month is two hundred and fifty-nine seconds. At about two seconds an election, roughly a hundred and thirty elections a group a month spend all of it. So elections per day is an SLI with a target under one. A constraint like that is what a manager uses to decide what to fix first."], cls="dia")

qs("Interviewer · the second-level push", "“Fenced-out is zero this week. Does that mean you are safe?”", [
 "I: Fenced-out is zero this week. Does that mean you are safe?", "[pause: 2.0]"])

S(plain(K(7, "the honest limit"), "Zero can mean nobody is sending tokens", '<div class="cards c2"><div class="cd red"><h3>Coverage</h3><p>Track the share of protected writes that carry a token, and count writes that arrive without one. A zero with no coverage is a blind spot.</p></div>'
  '<div class="cd amb"><h3>The invisible double hold</h3><p>A double hold that causes no stale write is invisible to the resource. The log audit finds overlapping holds, from the server\'s durations.</p></div></div>' +
  line("You can observe a violation after the fact and alarm on precursors. You cannot observe an absence of risk.", "r")), [
 "C: No. Zero fenced-out writes could just mean nobody is sending tokens. So I track coverage: the share of protected writes that carry a token, and a counter of writes that arrive without one. And a double hold that causes no stale write is invisible to the resource. The log audit finds overlapping holds from the server's durations.",
 "C: The honest limit: you can observe a violation after the fact, and you can alarm on its precursors. You cannot observe an absence of risk."])

say_slide("“I alert on the guarantee. Any fenced-out write pages someone, because it is either the safety net working or the first sign of a problem. I read metrics in pairs so each page names a cause. I track how many protected writes carry a token at all, and I audit the grant log for overlapping holds. A green dashboard about the service says nothing about the promise.”", [
 "V: If asked, I'd say: I alert on the guarantee. Any fenced-out write pages someone, because it is either the safety net working or the first sign of a problem. I read metrics in pairs so each page names a cause. I track how many protected writes carry a token at all, and I audit the grant log for overlapping holds. A green dashboard about the service says nothing about the promise."])

# ───────────────────────── 8 · build cost (AUX) ─────────────────────────
chapter(8, "Build cost", 6, "The manager layer: people, months, buy against build", [
 "N: This chapter is marked auxiliary. It is the engineering-manager layer, optional in a Staff round.",
 "C: A distributed lock service is not one project. It is three, and they differ by an order of magnitude."], aux=True)

S(plain("Build cost · three releases", "R0, R1, R2: not one project", table(["", "R0 · Prototype", "R1 · One region, production", "R2 · Platform"], [
  ["Goal", "Prove the model", "One or two teams' correctness locks", "Company-wide, multi-tenant"],
  ["Substrate", "Coordination store, or a row", "Coordination store, sharded", "Custom service, or managed global store"],
  ["Fencing", "Demonstrated", "Enforced for one resource type", "Every type; proxy for legacy"],
  ["Availability · on-call", "none", "99.9% · business hours", "99.99% · 24/7 with a budget"],
  ["Effort, engineer-months", "1–1.5", "20–24", "70–140"]], "bt sm"), ), [
 "C: Three releases, called R-zero, R-one and R-two so nobody confuses them with design versions. A prototype to prove the model: about a month. Production in one region for one or two teams: four engineers for five or six months, twenty to twenty-four engineer-months. A company platform: seventy to a hundred and forty. The best question available is: which of these are we actually being asked for, and who is the first customer?"], cls="aux")

S(plain("Build cost · R1 in detail", "Who, and how long", table(["Role", "FTE", "Owns"], [
  ["Tech lead", "1.0", "protocol correctness, the fencing contract, design reviews"],
  ["Senior backend", "1.0", "service, sharding, gateway, admin tools"],
  ["Mid backend", "1.0", "client libraries, first two customers, migration"],
  ["SRE", "1.0", "deployment, SLOs, load and chaos tests: half the build is operations"],
  ["Manager · programme", "0.3 · 0.2", "roadmap, adoption, hiring"]], "bt sm") + chips("discovery 3 wk", "skeleton 4", "correctness 6", "hardening 6", "operations 4", "first customer 3")), [
 "C: R-one, in detail. A tech lead for protocol correctness. A senior and a mid backend engineer. A full-time S-R-E, because half of an infrastructure service is operations. Plus fractions of a manager and a programme manager. Phases: three weeks of discovery, four for a walking skeleton, six for correctness, including a linearizability test harness under injected faults, six for hardening, four for operations, and three for the first customer, in shadow mode and then cutover.",
 "C: One assumption to state: if there is no committed first customer, the right decision is not to build."], cls="aux")

S(plain("Build cost · ownership", "People dominate the five years", chips("illustrative", "engineer-months") + '<div class="tiles" style="--n:3"><div class="tile blue"><b>24</b><span>to build R1</span></div>'
  '<div class="tile blue"><b>1.75 × 60</b><span>= 105 to run it for five years</span></div><div class="tile"><b>≈ 129</b><span>≈ 11 engineer-years; infrastructure is about a tenth</span></div></div>' +
  line("A service with no owner becomes an incident with no owner.", "a")), [
 "C: Ownership. Twenty-four engineer-months to build. Then about one and three-quarter people for five years, which is a hundred and five. A hundred and twenty-nine in total, about eleven engineer-years, and infrastructure is about a tenth of it. All illustrative. People dominate. And infrastructure services do not become free after launch: a service with no owner becomes an incident with no owner."], cls="aux")

S(plain("Build cost · build, adopt, buy, or don't", "Four options, one table", table(["Option", "To a pilot", "5-year, eng-months (illustrative)", "When it wins"], [
  ["<b>Don't</b>: conditional write or idempotency", "~2 weeks per resource", "~10", "the resource supports it: check first"],
  ["<b>Buy</b>: managed transactional store", "~4 weeks", "~60", "moderate volume, latency tolerant"],
  ("pick", ["<b>Adopt</b>: coordination store behind our A-P-I", "~10 weeks", "~80", "high volume, correctness-critical. <b>R1 pick</b>"]),
  ["<b>Build</b>: custom consensus service", "~6 months, 4 people", "~129", "a unique semantic, or very large scale"]], "bt sm mx")), [
 "C: Build, adopt, buy, or don't. Don't: make the resource idempotent or use its conditional write. Two weeks per resource. Check first, every time. Buy a managed transactional store: about four weeks. Adopt a coordination store behind our own A-P-I: about ten weeks. That is my R-one pick. Build a custom service: about a hundred and twenty-nine engineer-months, justified only by a semantic nothing else gives, or very large scale. I would write the buy-versus-build memo before any code, with the first customer's commitment in it. And because the A-P-I is ours from day one, replacing the substrate later is a project, not a migration."], cls="aux")

S(plain("Build cost · risks, cuts, people", "What I would never cut", '<div class="cards c3">'
  '<div class="cd red"><h3>Never cut</h3><p>Fencing end to end. The conservative client deadline. The linearizability harness. The runbook and a qualified on-call.</p></div>'
  '<div class="cd amb"><h3>Cut first</h3><p>Multi-region. Shared modes. First-come fairness. Extra-language libraries. The admin console.</p></div>'
  '<div class="cd"><h3>Top risks</h3><p>Fencing not enforceable. Adoption fails. Scope creep into a key-value store. Key-person on the protocol. A split-brain incident.</p></div></div>'), [
 "C: What I would never cut: fencing end to end, the conservative client deadline, the linearizability harness, and the runbook with a qualified on-call. What I'd cut first: multi-region, shared modes, first-come fairness, extra-language libraries, the admin console.",
 "C: Top risks. Fencing cannot be enforced at a key resource: descope that caller to an efficiency lock in writing. Adoption fails: a named pilot before any code. Scope creep into a general key-value store, which is what happened to the best-known lock service: written non-goals, with quotas enforced in code. A key person who knows the protocol: pair, write design docs, two people on-call before launch. And a split-brain incident: consensus, fencing, a harness in the pipeline, game days."], cls="aux")

S(plain("Build cost · staffing, and the question to ask", "Small first. Do not add people in stabilisation.", '<div class="cards c2">'
  '<div class="cd"><h3>Over time</h3><p>Two people to design and build the skeleton. Grow to four in the middle, where work parallelises. Hold steady while stabilising. Share on-call with a sibling team.</p></div>'
  '<div class="cd grn"><h3>The question before saying yes</h3><p>“What happens if two of you hold this at once, and could the operation be made idempotent?”</p></div></div>'), [
 "C: Staffing. Start small, because design by committee is slow. Grow in the middle where the work parallelises. Do not add people while stabilising. Share the on-call rotation with a sibling team, so four people do not carry a twenty-four-seven pager.",
 "V: The question I ask before saying yes: what happens if two of you hold this at once, and could the operation be made idempotent?", "[pause: 1.0]"], cls="aux")

# ───────────────────────── 9 · recap ─────────────────────────
chapter(9, "Recap", 7, "One picture, five paths, the mistakes, the thesis", [
 "C: Four minutes to close. One picture, one sentence per path, the mistakes to avoid, and the thesis."])

S(dia("Recap", "The whole design on one baseline", "base-final", chip=chips("library", "gateway", "4 groups", "epoch store", "resource with the check")), [
 "C: The final picture. The library with sessions and a local deadline. The gateway with quotas and the slot map. Four consensus groups with leaders and a waiter queue. The epoch store. Metrics and a canary. And at the resource, the token check, with a proxy where a resource cannot check. Every box on it was added to answer one question the design raised."], cls="dia")

S(plain("Recap · one sentence per path", "Five paths", table(["Path", "In one sentence"], [
  ["<b>Acquire</b>", "One committed write, and a token out"],
  ["<b>Renew</b>", "One heartbeat per client, measured from send time"],
  ["<b>Release and expiry</b>", "Compare by token, hand off to the head waiter; a dead session is one command"],
  ["<b>Fence</b>", "The resource rejects anything older than it has seen"],
  ["<b>Revoke</b>", "Audited, and the next token is higher"]], "bt")), [
 "C: Five paths, one sentence each. Acquire: one committed write and a token out. Renew: one heartbeat per client, measured from send time. Release and expiry: compare by token, hand off to the head waiter, and a dead session is one command. Fence: the resource rejects anything older than it has seen. Revoke: audited, and the next token is higher."])

S(plain("Recap · if asked about regions", "Multi-region, in three lines", '<div class="cards c3"><div class="cd grn"><h3>Preferred</h3><p>Region-local lock services over region-owned resources.</p></div>'
  '<div class="cd amb"><h3>Sparingly</h3><p>A global lock only for rare, coarse locks: a global leader, a schema change.</p></div>'
  '<div class="cd red"><h3>Never</h3><p>Asynchronous replication of lock state. It is split brain with extra steps.</p></div></div>'), [
 "C: If asked about multi-region. Preferred: region-local lock services over region-owned resources, so there is no cross-region consensus at all. Sparingly: a global lock for rare, coarse locks, accepting the latency. Never: asynchronous replication of lock state. That is split brain with extra steps. A cross-region quorum costs thirty to two hundred and fifty milliseconds, which breaks the twenty-millisecond target."])

S(plain("Recap · common mistakes in this round", "Ten ways this round goes wrong", '<div class="cards c2"><div class="cd red"><h3>Design</h3><ul style="font-size:17pt"><li>A cache key with an expiry presented as a correctness lock</li><li>“Tune the lease” as the answer to a pause</li><li>No token, or a token nobody checks</li><li>Timestamps compared across machines</li><li>Failing open without saying so</li></ul></div>'
  '<div class="cd amb"><h3>Judgment</h3><ul style="font-size:17pt"><li>A beautiful consensus group and no word about the resource</li><li>Never asking whether a lock is needed</li><li>Offering atomic multi-lock</li><li>Restoring an old snapshot</li><li>Hiding the token in a thread-local</li></ul></div></div>'), [
 "C: Ten mistakes in this round. In the design: a cache key with an expiry presented as a correctness lock. Tune the lease as the answer to a pause. No token, or a token nobody checks. Timestamps compared across machines. Failing open without saying so.",
 "C: In judgment: a beautiful consensus group and no word about the resource. Never asking whether a lock is needed. Offering atomic multi-lock. Restoring an old snapshot. And hiding the token in a thread-local."])

key("The close", "The lock service decides who should be working. The resource decides who is allowed to write. Everything I built is there so those two answers can <em>disagree safely</em>.", [
 "V: The lock service decides who should be working. The resource decides who is allowed to write. Everything I built is there so that those two answers can disagree safely.", "[pause: 1.2]",
 "C: Thank you. I'll stop there."])
