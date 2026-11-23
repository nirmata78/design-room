from dsl import *

# ───────────────────────── 6 · bridge ─────────────────────────
chapter(6, "Bridge", 4, "It works. Where does it break first?", [
 "V: It works. The question now is where it breaks first.", "[pause: 1.0]"])

S(dia("Challenge map", "Seven attack points on the same baseline", "map", chip=chips("each fix creates the next question")), [
 "C: Here is the baseline with seven attack points. A paused holder, at the resource. A resource that cannot check tokens. Clocks, in the library. The leader and the partition, in the group. Peak load, at the gateway and the group. A hot name, in the group. And finally: how would we know any of it was broken? I'll take them in an order where each fix creates the next question."], cls="dia")

chapter(7, "Challenges", 5, "Seven ways to break it, and what survives", [
 "C: Seven challenges. Each one runs the same way: the question, the naive answer, a case with numbers, where it breaks, the fix, why it works, then the interviewer pushes on the fix itself, and I answer what I'd say in the room."])

K = lambda n, t: f"Challenge {n} of 7 · {t}"

# ───────── Challenge 1 · the paused holder ─────────
subchapter("7.1", "Challenge 1: The paused holder")
qs("Interviewer · challenge 1 of 7", "“A holder is stopped by a fifteen-second garbage-collection pause. Its lease expires, another process acquires, and then the first one wakes up. Both now write. What saves you?”", [
 "I: A holder is stopped by a fifteen-second garbage collection pause. Its lease expires, another process acquires, and then the first one wakes up. Both now write. What saves you?", "[pause: 2.0]"])

S(dia(K(1, "the paused holder"), "What saves you when the holder wakes up?", "ch1-attack", q=True, red=True,
      extra=strip(("case", "Naive answer", "“Make the lease longer, and check the lease is still valid just before every write.”"),
                  ("case", "Why it fails", "Between the check and the write, the lease can still expire. The check and the write are not atomic."))), [
 "C: The first answer most people give: make the lease longer, and check the lease is valid just before writing. Look where it breaks. The red arrow, from the client to the resource. The lock service did everything right, and the resource still accepts both writes. A check before a write is not atomic with the write. Between them, the lease can expire. That is the pause, exactly."], cls="dia")

S(plain(K(1, "the trace"), "What does the resource see?", '<pre class="trace"><span class="t">t = 0.0 s   </span>A acquires invoice-17: token 41, lease 10 s\n<span class="t">t = 0.2 s   </span>A reads the invoice\n<span class="t">t = 0.3 s   </span>A checks "still held": yes. <span class="bad">Then A pauses.</span>\n<span class="t">t = 10.0 s  </span>lease expires\n<span class="t">t = 10.4 s  </span>B acquires: token 42\n<span class="t">t = 10.5 s  </span>B writes\n<span class="t">t = 15.3 s  </span><span class="bad">A resumes and writes</span></pre>' +
  '<div class="hedge"><b class="t">Raising the lease</b>At 60 s a 70 s pause still wins, and every real crash now stalls its name for a minute. It moves the failure. It does not remove it.</div>', q=True, red=True), [
 "C: The trace with numbers. A gets token forty-one at zero, reads, checks that it still holds the lock, and pauses at point three. The lease expires at ten. B acquires at ten point four, token forty-two, and writes at ten point five. At fifteen point three A resumes and writes. It checked. It was right to check. It was just too early.",
 "C: Raising the lease to sixty seconds moves the line, and a seventy-second pause still beats it, while every real crash stalls its name for a minute. These numbers are illustrative. The shape is what matters."])

S(dia(K(1, "the fix"), "A fencing token, checked at the resource", "ch1-fix",
      extra=strip(("fixb", "Mechanism", "Each grant carries a token bigger than every earlier one. The resource keeps the highest it accepted and rejects any write with a smaller one."),
                  ("whyb", "Property", "Safety, enforced where the effect happens. The check and the write are one atomic step at the resource."))), [
 "C: The fix is the fencing token, checked at the resource. The new green box is the check. The grant already carries a token, which is the log index. The resource keeps the highest token it has accepted for that row, and rejects any write that carries a smaller one."], cls="dia")

S(dia(K(1, "replay"), "Same story, with the resource checking", "pause-fenced"), [
 "C: Replay it. A holds forty-one and pauses. B gets forty-two and writes: accepted, the resource stores forty-two. A wakes at fifteen point three and writes with forty-one. Forty-one is smaller than forty-two. Rejected. Notice what did not change: the pause, the lease, the lock service. Only the resource became safe."], cls="dia")

S(dia(K(1, "sequence"), "The fix, message by message", "seq-ch1-pause"), [
 "C: As a sequence. A acquires and gets forty-one. A pauses fifteen seconds. B acquires after the lease expired and gets forty-two. B writes with forty-two, accepted. A resumes and writes with forty-one at fifteen point three, and the resource rejects it: forty-one is smaller than forty-two."], cls="dia")

S(plain(K(1, "the mechanism as code"), "One conditional statement", '<pre class="code"><span class="cm">-- a database row: the token is the version</span>\n<span class="kw">UPDATE</span> invoice\n   <span class="kw">SET</span> amount = :amount, fence = :token\n <span class="kw">WHERE</span> id = :id <span class="kw">AND</span> fence &lt;= :token;\n<span class="cm">-- 0 rows: throw FencedOut(id, token). Log both tokens. Alert.\n\n// an object store: the object\'s generation is the token\n// write only if generation matches what you read</span></pre>' +
  strip(("whyb", "Why it works", "Consensus gives a correct order. The resource, which is the only place that can check and write atomically, enforces it. Equal tokens pass: one holder, several writes."), cols="one")), [
 "C: In code, on a database row it is one conditional update. Set the amount and the fence, where the fence is less than or equal to the token. Zero rows updated means fenced out: log both tokens and alert. On an object store, the object's generation number is the token, and the write is conditional on it.",
 "C: Why it works, as a property: safety, enforced where the effect happens. Consensus gives a correct order. The resource, the only place that can check and write in one atomic step, enforces it. And precisely: equal tokens pass, because one holder may write several times. Only smaller is rejected."])

qs("Interviewer · the second-level push", "“A's stale write arrives before B's first write. The resource has only seen forty-one, so it accepts A. Then B, who read the old row, writes forty-two on top. Is that fenced?”", [
 "I: A's stale write arrives before B's first write. The resource has only seen forty-one, so it accepts A. Then B, who read the old row, writes forty-two on top. Is that fenced?", "[pause: 2.0]"])

S(plain(K(1, "the honest limit"), "No. Fencing orders writes. It does not repair a stale read.", '<pre class="trace"><span class="t">t = 10.4 s  </span>B acquires: token 42. Resource has only seen 41\n<span class="t">t = 10.45 s </span>B reads the invoice\n<span class="t">t = 10.5 s  </span><span class="bad">A (stale, token 41) writes: not smaller than 41, accepted</span>\n<span class="t">t = 10.6 s  </span>B writes on its old read: <span class="bad">A\'s update is lost</span></pre>' +
  strip(("fixb", "Fix 1", "Make B's critical section one conditional write against the version it read. The token is the version."),
        ("fixb", "Fix 2", "Or B claims its token at the resource first. Then any later write by 41 is rejected."))), [
 "C: No, and that is the honest limit. Fencing rejects stale writes after a newer token has been seen. Here A's write lands first, when the resource has only seen forty-one. It is accepted. Then B, working from an older read, writes on top of it, and A's update is lost.",
 "C: Two ways to close it. One: make B's critical section a single conditional write against the version it read, so the token is the version. Two: B claims its token at the resource before it reads. After that, any write from A is rejected. The cost is one extra round trip, or a critical section that fits in one conditional write."], cls="")

S(dia(K(1, "the second fix, as a sequence"), "Claim first, then read", "seq-ch1-claim"), [
 "C: The claim as a sequence. B claims token forty-two at the resource before reading. The resource now stores forty-two. A, the stale holder, writes with forty-one: rejected. Then B reads the row and writes with forty-two, conditional on the version it read. The window is closed."], cls="dia")

say_slide("“A lease cannot guarantee exclusion at the resource, because the holder cannot know it still holds the lock when its write lands. So the grant carries a token that only increases, and the resource rejects anything older than it has accepted. Safety lives at the resource. The lock service only has to give a correct order.”", [
 "V: If asked, I'd say: a lease cannot guarantee exclusion at the resource, because the holder cannot know it still holds the lock when its write lands. So the grant carries a token that only increases, and the resource rejects anything older than it has accepted. Safety lives at the resource. The lock service only has to give a correct order.", "[pause: 1.0]",
 "N: That fix creates the next question: what if the resource cannot check?"])

# ───────── Challenge 2 · the resource cannot check ─────────
subchapter("7.2", "Challenge 2: The resource cannot check")
qs("Interviewer · challenge 2 of 7", "“The thing you are protecting is a partner's HTTP API, or a cron job. There is no conditional write. Now what?”", [
 "I: The thing you are protecting is a partner's H-T-T-P A-P-I, or a cron job. There is no conditional write. Now what?", "[pause: 2.0]"])

S(dia(K(2, "the resource cannot check"), "What if there is nowhere to put the check?", "ch2-attack", q=True, red=True,
      extra=strip(("case", "Naive answer", "“Use a long lease, trust the client library, and call it correct.”"),
                  ("case", "Case", "A payment call with no idempotency key, paused after the lock check, charges twice."))), [
 "C: The naive answer: use a long lease, trust the library, and call it correct. It is not. Here is a payment call to a partner with no idempotency key. The holder pauses after its lock check, and the call happens twice. The grey box has nowhere to put a fence."], cls="dia")

S(plain(K(2, "a survey, illustrative"), "Before building anything, sort the callers", table(["Callers (of 100)", "What they really need", "Right tool"], [
  ["55", "only to avoid duplicate work", "<b>efficiency lock</b>: no token needed"],
  ["30", "the resource has a conditional write or version column", "<b>the resource's own version is the token</b>"],
  ["10", "a resource with neither", "a <b>validating proxy</b>"],
  ["5", "truly non-idempotent, no check possible", "change the contract, or accept the risk in writing"]], "bt sm") +
  '<div class="hedge"><b class="t">Label the numbers</b>Illustrative: a made-up survey to show the shape. The method is the point: classify before you build.</div>', q=True, red=True), [
 "C: Before building, sort the callers. An illustrative survey of a hundred. Fifty-five only want to avoid duplicate work: that is an efficiency lock, and no token is needed. Thirty write to a store with a conditional write or a version column: the resource's own version is the token, and the lock service is just an optimisation.",
 "C: Ten call something with neither: for those I build a validating proxy. And five are truly non-idempotent, with no check possible. For those, no lock can make them safe. The answer is to change the contract, or accept the risk in writing, with a named owner."])

S(plain(K(2, "the order of questions"), "Ask first, then pick the cheapest place to enforce", '<div class="cards c4">'
  '<div class="cd"><h3>1 · Is it idempotent?</h3><p>Give it a key: lock name plus job instance. A double hold becomes harmless.</p></div>'
  '<div class="cd grn"><h3>2 · Conditional write?</h3><p>Use its version as the token.</p></div>'
  '<div class="cd amb"><h3>3 · Proxy</h3><p>Put a checker in front. It keeps the highest token per resource.</p></div>'
  '<div class="cd red"><h3>4 · None fit</h3><p>Ship an efficiency lock and say so in the contract.</p></div></div>'), [
 "C: So the order of questions. One: is the operation idempotent? If so, give it a key, the lock name plus the job instance, and a double hold becomes harmless. Two: does the resource have a conditional write? Use its version as the token. Three: otherwise put a validating proxy in front of it. Four: if none of these fit, ship an efficiency lock, and say so plainly in the contract. Each option moves safety to a place that can check and act atomically."])

S(dia(K(2, "the fix"), "A proxy that remembers the highest token", "ch2-fix",
      extra=strip(("fixb", "Mechanism", "The proxy stores the highest token per resource in a consistent store and forwards only fresh calls."),
                  ("whyb", "Property", "Matching the guarantee to the cost of a double hold: safety where a check can be atomic."))), [
 "C: The proxy, for the ten. It sits in front of the partner's A-P-I and keeps the highest token per resource in a consistent store. A call with a fresh token is forwarded. A stale one is rejected, and the partner never sees it. The property: safety, moved to a place where a check can be made atomic."], cls="dia")

S(dia(K(2, "sequence"), "The proxy, accept and reject", "seq-ch2-proxy"), [
 "C: As a sequence. The app calls through the proxy with token forty-two. The proxy sets the maximum to forty-two with a conditional update, which applies, then forwards the call, and the response comes back. A stale holder calls with forty-one. The conditional update does not apply, because the maximum is forty-two, so the proxy rejects it, and the partner never sees the call."], cls="dia")

qs("Interviewer · the second-level push", "“The proxy is now a single point of failure, and a new thing that must itself be consistent. And your idempotency records: how long do you keep them?”", [
 "I: The proxy is now a single point of failure, and a new thing that must itself be consistent. And your idempotency records: how long do you keep them?", "[pause: 2.0]"])

S(plain(K(2, "the second fix, and the honest limit"), "Fail closed, and keep records long enough", '<div class="cards c2">'
  '<div class="cd grn"><h3>The proxy</h3><p>Fails closed. Its token table lives in a consensus-backed store. Scoped per resource class, so one failure does not take all.</p></div>'
  '<div class="cd amb"><h3>Idempotency records</h3><p>Keep at least: <b>max lease + max pause + retry horizon</b>. Illustrative: 24 h for a 60 s lease.</p></div></div>' +
  line("A non-idempotent call to a system with no check cannot be made safe by any lock. Change the contract.", "r")), [
 "C: The proxy fails closed, keeps its table in a consensus-backed store, and is scoped per resource class, so one failure does not take everyone. Idempotency records live at least as long as the maximum lease plus the maximum pause plus the retry horizon. For a sixty-second lease, an illustrative twenty-four hours.",
 "C: And the honest limit. A non-idempotent call to a system with no check cannot be made safe by any lock. The answer is to change the contract, or accept the risk with an owner."])

say_slide("“Before I build a lock for a team I ask what a double hold costs and whether the operation can be made idempotent. If the resource supports a conditional write, the resource enforces exclusion and the lock is an optimisation. I only claim a correctness lock where something downstream checks the token.”", [
 "V: If asked, I'd say: before I build a lock for a team I ask what a double hold costs, and whether the operation can be made idempotent. If the resource supports a conditional write, the resource enforces exclusion and the lock is an optimisation. I only claim a correctness lock where something downstream checks the token.", "[pause: 1.0]",
 "N: Next: if safety rests on the token, how much does it rest on the lease clock?"])

# ───────── Challenge 3 · time ─────────
subchapter("7.3", "Challenge 3: Clocks and leases")
qs("Interviewer · challenge 3 of 7", "“A client's clock is five seconds slow. Or time is stepped back eight seconds in the middle of a lease. What happens to the lease?”", [
 "I: A client's clock is five seconds slow. Or time is stepped back eight seconds in the middle of a lease. What happens to the lease?", "[pause: 2.0]"])

S(dia(K(3, "time"), "What does the client believe?", "ch3-attack", q=True, red=True,
      extra=strip(("case", "Naive answer", "“The server returns an expiry timestamp and the client compares it with its own clock.”"),
                  ("case", "Break", "The library's deadline logic trusts a timestamp from a machine whose clock it cannot trust."))), [
 "C: The naive design: the server returns an expiry timestamp, and the client compares it with its own clock. Look at the box under attack, the library. It trusts a time from a machine whose clock it has no reason to trust."], cls="dia")

S(dia(K(3, "the case"), "A slow clock: two holders for five seconds", "clock-skew"), [
 "C: The case. The server grants at its time zero, expiry at ten. The client's clock is five seconds slow, so it believes it holds until its own ten, which is server time fifteen. From server time ten to fifteen, B has been granted the name and A still believes it holds it. Two holders, for five seconds. A fast clock is merely wasteful. A step back of eight seconds mid-lease does the same to a perfectly good client. And a timestamp is no good as the token either, for the same reason."], cls="dia")

S(plain(K(3, "three kinds of time"), "Use each kind for one job", table(["Kind", "Property", "Use it for"], [
  ["Wall clock", "can jump forwards and backwards: steps, leap seconds, migration", "<b>never</b> for lease arithmetic"],
  ["Monotonic clock", "never goes backwards on one machine. Meaningless across machines", "<b>durations</b>"],
  ["Logical order", "log index, term. Says nothing about duration", "<b>the token, and correctness</b>"]], "bt sm") +
  line("Durations on monotonic clocks, correctness on logical order, and nothing that depends on two machines agreeing what time it is.")), [
 "C: The discipline is to use each kind of time for one job. A wall clock can jump either way: clock steps, leap seconds, virtual machine migration. Never use it for a lease. A monotonic clock never goes backwards on one machine, but means nothing across machines. Use it for durations. And logical order, the log index and the term, says nothing about duration but is totally ordered. Use it for the token."])

S(dia(K(3, "the fix"), "Durations, not timestamps", "ch3-fix",
      extra=strip(("fixb", "Mechanism", "deadline = send time + 0.7 × lease, on the monotonic clock. The server counts its own lease from its own commit. No timestamp crosses the wire."),
                  ("whyb", "Property", "Safety of the lease arithmetic: it depends on how fast two clocks tick, not on what they read."))), [
 "C: The fix. The library measures its deadline as the monotonic time when it sent the request, plus seventy percent of the lease. The server counts the lease from its own commit, on its own monotonic clock. And inside the replicated machine, the leader writes the apply time into the log entry, so replicas never read their own clocks. No timestamp crosses the wire."], cls="dia")

S(dia(K(3, "replay"), "The client stops first", "clock-fixed"), [
 "C: Replay it. The client counts from when it sent: seven seconds. At seven it stops. The server waits the full ten. Between them, a three-second margin. The client always stops first, so there is never a window where it believes it holds a lock the server has given away. And drift? Two hundred parts per million over ten seconds is two milliseconds. The margin is for round trips and scheduling, not for drift."], cls="dia")

qs("Interviewer · the second-level push", "“What if the process pauses between reading the monotonic clock and doing the write? Or drift is far above your assumption, as on a throttled virtual machine?”", [
 "I: What if the process pauses between reading the monotonic clock and doing the write? Or drift is far above your assumption, as on a throttled virtual machine?", "[pause: 2.0]"])

S(plain(K(3, "the honest limit"), "The margin cannot see a pause. The token can.", '<div class="cards c2">'
  '<div class="cd red"><h3>Pause between check and write</h3><p>The margin does nothing. That is challenge one again, and the token is the backstop.</p></div>'
  '<div class="cd amb"><h3>Drift above the assumption</h3><p>Bounded drift is an assumption. With fencing it is no longer load-bearing for safety. We still monitor clock health and the rate of missed local deadlines.</p></div></div>'), [
 "C: Two honest answers. A pause between the clock read and the write: the margin cannot see it. That is challenge one again, and the token is the backstop. And drift beyond the assumption: bounded drift is an assumption, and I'll say so. But once fencing is in, it is no longer load-bearing for safety. It only affects how often a holder is fenced. So I monitor clock health and the rate of missed deadlines, and keep the margin configurable per tenant."])

say_slide("“I use monotonic clocks for durations and logical order for correctness. The client gives up before the server does, so there is never a window where it believes it holds a lock the server has given away. And because that still assumes bounded drift, the token at the resource is what the safety argument rests on.”", [
 "V: If asked, I'd say: I use monotonic clocks for durations and logical order for correctness. The client gives up before the server does, so there is never a window where it believes it holds a lock the server has given away. And because that still assumes bounded drift, the token at the resource is what the safety argument rests on.", "[pause: 1.0]",
 "N: So far, every failure was at the edges. What if the middle fails?"])
