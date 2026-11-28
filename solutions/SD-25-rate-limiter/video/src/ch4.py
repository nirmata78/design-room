from dsl import *
import stack
P = "[+]"
B = lambda x: f'<span class="bad">{x}</span>'
ST = stack.load(pathlib.Path(__file__).resolve().parents[2])
T = 6   # challenges

# ───────────────────────── 4 · C4 evolution through interviewer challenges ─────────────────────────
chapter(4, "Design, driven by challenges", 3, "V1 is the C4 container view; every challenge changes it", [
 "C: The design. I start directly with the container view, version one: the simplest thing that is correct. Then the interviewer breaks it, six times, and each fix is a change to this one picture, or a zoom into one of its boxes."])

stage("C4 level 2 · containers", "The simplest exact limiter: one shared bucket per key", "v1", [
 "C: Version one, in the order a request travels.", P,
 "C: API clients call the API.", P,
 "C: The API server authenticates the request, and its limiter library makes the decision.", P,
 "C: By running a script against a shared limit store, Redis, which holds one bucket per customer and endpoint.", P,
 "C: Admitted requests go on to the backend services.", P,
 "C: The limits themselves come from a policy service, which every API server watches.", P,
 "C: Stored as versions in a policy store.", P,
 "C: And the account team edits them. One shared count per key: exact, and simple."],
 vtag="V1", cap="V1: the C4 container view, one shared bucket per key")

stage("Flow · FR1 and FR3 on V1", "A request, and a limit change", "flow-v1", [
 "C: The happy path, numbered, once.", P,
 "C: One: a client calls the API.", P,
 "C: Two: the limiter runs the bucket script on the store for that customer and endpoint, and gets allowed and remaining.", P,
 "C: Three: admitted, the request goes to the backend, and the response carries the headers.", P,
 "C: Four: separately, the account team changes a limit.", P,
 "C: Five: the policy service writes it as a new version.", P,
 "C: Six: every API server is watching, and has it within seconds. FR1 and FR3, end to end."], cap="V1 happy path: decide, admit, and change a limit")

S(tech(**ST.tech("lib")), ST.say("lib"))
S(tech(**ST.tech("store")), ST.say("store"))

# ───────── Challenge 1 · the boundary burst ─────────
challenge(1, T, "1,000 at 11:59:59, 1,000 at 12:00:00", "Your counter is per minute. A customer sends a thousand requests at 11:59:59 and a thousand more at 12:00:00. Is that within the limit?",
          ["N: Challenge one is the algorithm. It is the detail that shows whether a candidate has actually thought about windows."])

S(trace("Challenge 1 of 6 · the trace", "Two thousand requests in one second, on a limit of a thousand a minute", [
  ("11:59:00", "customer 42, limit 1,000 a minute on <code>/search</code>: quiet, counter 0"),
  ("11:59:59.0", "1,000 requests: window 11:59 counts 1,000; all admitted"),
  ("12:00:00.0", "a new window: the counter starts at 0; " + B("1,000 more admitted")),
  ("12:00:01.0", B("2,000 requests in one second against a backend sized for about 17 a second"))],
  hedge=("Not a corner case", "Batch jobs start on the minute and on the hour. The boundary is exactly where real traffic lands.")), [
 "C: The trace.", P, "C: Customer forty-two has a thousand a minute on search, and has been quiet.", P,
 "C: At eleven fifty-nine fifty-nine it sends a thousand requests. The counter for the eleven fifty-nine window reaches a thousand. All admitted.", P,
 "C: One second later a new window starts at zero, and a thousand more are admitted.", P,
 "C: Two thousand in one second, against a backend sized for about seventeen a second.", P,
 "C: Not a corner case: batch jobs start on the minute, exactly at the boundary."])

S(dia("Challenge 1 of 6 · the break", "A window resets; a bucket remembers", "boundary",
      cap="The same 2,000 requests through a fixed window and through a token bucket"), [
 "C: The same two thousand requests, through two algorithms. The fixed window admits a thousand on each side of the boundary: two thousand in one second. A token bucket with a rate of sixteen point seven a second and a burst of two hundred admits two hundred at eleven fifty-nine fifty-nine, and seventeen one second later. In any interval of t seconds it admits at most b plus r times t."])

S(plain("Challenge 1 of 6 · the options", "Five algorithms, compared, one picked", table(["Algorithm", "State per key", "Bursts", "Fails when"], [
  ["A · Fixed window counter", "one counter", "2× at the boundary", "traffic lands on the edge of a window"],
  ["B · Sliding-window log", "a timestamp per request", "exact", "16 GB of timestamps; a trim on every check"],
  ["C · Sliding-window counter", "two counters", "smoothed, approximate", "traffic in the last window was uneven"],
  ("pick", ["<b>D · Token bucket</b>", "two numbers", "up to b, then the rate r", "a burst of b is allowed, by design"]),
  ["E · Leaky bucket, as a queue", "a queue", "none: output smoothed", "every burst waits in line: shaping, not quotas"]], "bt xs mx") +
  line("Rate and burst are two knobs, and customers asked for both.", "a")), [
 "C: Five algorithms, compared.", P,
 "C: A, the fixed window: one counter, and twice the limit at the boundary. We just saw it.", P,
 "C: B, the sliding-window log: exact, and a timestamp per request, sixteen gigabytes in all.", P,
 "C: C, the sliding-window counter: a cheap compromise that assumes the last window was even.", P,
 "C: D, which I pick: the token bucket. Two numbers per key, a burst of up to b, then the rate r.", P,
 "C: E, the leaky bucket as a queue: it makes every burst wait. That's shaping, not quotas.", P,
 "V: Rate and burst are two knobs, and customers burst legitimately. The token bucket gives me both."])

mech_slide(1, 5, "A token bucket, refilled lazily", pid("S1") + " without blocking legitimate bursts",
           "Two numbers per key: tokens and the last refill time. On each request, add r × elapsed, capped at b; take the cost if it is there.",
           "The boundary double: at most b + r × t in any t seconds.",
           "A burst of b is always allowed; one clock per key must do the refill.", [
 "C: The mechanism, just in time.", P,
 f"C: It protects {ps('S1')}, without blocking a legitimate burst.", P,
 "C: Two numbers per key: how many tokens, and when it was last refilled. Nothing runs in the background. On each request, add the rate times the time elapsed, capped at the burst, then take the cost if it's there.", P,
 "C: It rules out the boundary double. In any t seconds it admits at most b plus r times t.", P,
 "C: It costs a burst of b, always allowed, so b is a decision. And the refill needs one clock per key."], part="Mechanism")

zoom("Challenge 1 of 6 · the fix", "A token bucket, in one script, on the key's shard", "v1-fix", strip(("fixb", "Mechanism", "The bucket is a hash <code>{tokens, ts}</code>. One script refills with the shard's clock, compares, takes and writes, and returns allowed, remaining and retry-after."),
                  ("whyb", "Covers, and does not", "The boundary burst, and every race on one key. Not the round trip: every request still waits on the store.")) + rejl(*ST.rej(1)), [
 "C: The fix, on the container view.", P, "C: The limit store, marked.", P,
 "C: One level down: the bucket is a hash with tokens and a timestamp. One script refills it using the shard's own clock, compares, takes and writes, and returns allowed, what remains, and the retry-after.", P,
 "C: It covers the boundary burst, and any race on one key. It does not cover the round trip: every request still waits on the store.", P,
 "C: Rejected: the sliding-window log. Exact, but a timestamp per request: sixteen gigabytes, and a trim on every check."], cap="V1: the limit store runs a token bucket")

S(plain("Challenge 1 of 6 · the script, as pseudocode", "Refill, compare, take: one step, one clock",
  pseudo("now = shard_time_ms()             # TIME, inside\ntokens, ts = HMGET(key) or (b, now)\ntokens = min(b, tokens + (now - ts) * r)\nif tokens >= cost:\n    tokens = tokens - cost; ok = true\nelse:\n    ok = false\nHSET(key, tokens, now)\nPEXPIRE(key, 2 * b / r)\nreturn ok, floor(tokens), (cost - tokens) / r", hl=(1, 3, 8))), [
 "C: As pseudocode, the key lines marked.",
 "C: Line one: the time comes from the shard, inside the script, not from the caller. Line three: the lazy refill, capped at the burst. Line eight: the write happens in the same script as the read.",
 "C: Why it works: the script runs to completion on the thread that owns the key, so nothing happens between the read and the write. And idle keys expire."])

push("Two API servers check the same key at the same microsecond, with one token left.")
S(plain("Challenge 1 of 6 · one level deeper", "One step on one thread, and one clock per key", cards(
  ("grn", "One script, one thread", "The shard runs scripts one at a time: one server gets the token, the other a 429."),
  ("amb", "The store's clock", "500 servers have 500 clocks. A server a second fast would mint a second of tokens per call."),
  ("red", "Honest limit", "One key is one shard's thread: about 100,000 a second. The hot customer is right at it.")) + rejl(*ST.rej(2))), [
 P, "C: The shard runs scripts one at a time, so exactly one server gets the last token, and the other gets a 429.", P,
 "C: And the refill uses the store's clock. Five hundred servers have five hundred clocks. If the caller supplied the time, a server running a second fast would mint a second of tokens on every call.", P,
 "C: The honest limit: one key is one shard's thread, about a hundred thousand operations a second. The hot customer is right at it.", P,
 "C: Rejected: get, compare, then set, from the API server. Both servers read one token and both admit. A real production bug."])

say_slide("“A token bucket per customer and endpoint, refilled lazily: rate and burst are separate knobs, and the boundary can't double the limit. Check and take are one atomic script on the key's shard, timed by its clock.”", [
 "V: If asked, I'd say: a token bucket per customer and endpoint, refilled lazily. Rate and burst are separate knobs, and the boundary can't double the limit. Check and take are one atomic script on the key's shard, timed by its clock.", "[pause: 1.0]",
 "N: That fix creates the next question: a round trip on every request, at three million a second."])

# ───────── Challenge 2 · the round trip (the crux) ─────────
challenge(2, T, "Take the round trip off the hot path", "At the top of the hour that's three million scripts a second, and every API call waits on Redis. You have one millisecond. Take the round trip off the hot path. What do you lose?",
          ["N: Challenge two is the crux of this question. Most answers either keep the shared counter or divide the limit. The grade is for what comes between."])

S(trace("Challenge 2 of 6 · the trace", "The top of the hour, on V1", [
  ("12:00:00", "batch jobs start: 3 M requests/s, 3 M scripts/s over 30 shards"),
  ("12:00:01", "customer 42 at 300 k/s: its shard at 100 % CPU, p99 4 ms"),
  ("12:00:02", B("every key on that shard waits: API p99 up by 4 ms, for customers who did nothing")),
  ("12:00:40", B("that shard fails over: 8 s without a primary; the API must guess"))],
  hedge=("What V1 became", "The API's slowest and least available dependency, sized by its busiest customer.")), [
 "C: The trace.", P, "C: At noon the batch jobs start: three million requests a second, three million scripts over thirty shards.", P,
 "C: Customer forty-two goes to three hundred thousand a second. Its shard is at a hundred percent, and its p99 is four milliseconds.", P,
 "C: Every other key on that shard waits too. The API's p99 rises by four milliseconds for customers who did nothing.", P,
 "C: Forty seconds later that shard fails over. Eight seconds without a primary, and the API has to guess.", P,
 "C: The limiter became the API's slowest dependency, sized by its busiest customer."])

stage("Challenge 2 of 6 · the break", "Every request waits on the limit store", "v1-break", [
 "C: Version one, with the problem marked.", P,
 f"C: The limit store is on every request. That gives exact counts, but it breaks {ps('L2')} at p99, and with every failover it threatens {ps('S2')}."],
 cap="V1: the limit store is on the path of every request")

S(plain("Challenge 2 of 6 · the options", "Where the count lives: five answers, one picked", table(["Approach", "Added latency", "Over-admission", "Fails when"], [
  ["A · central counter per request (V1)", "a round trip", "none", "the store is slow, hot or failing over"],
  ["B · static split: limit ÷ 500", "none", "none", "traffic is uneven: throttled at 0.6 %"],
  ["C · route each customer to one owner", "a hop, sometimes", "none", "the hot customer is one machine"],
  ["D · gossip of local counts", "none", "≈ rate × interval", "500 peers chatter; no one owns the number"],
  ("pick", ["<b>E · local buckets, leased by demand</b>", "none", "≤ 5 % + cold starts", "demand moves faster than 100 ms"])], "bt xs mx") +
  line("Exact where it is cheap, bounded where it is not.", "a")), [
 "C: Five places the count can live.", P,
 "C: A, a central counter per request: version one.", P,
 "C: B, a static split: no latency, and a customer on three servers is throttled at zero point six percent.", P,
 "C: C, route each customer to one owner server: exact, until the hot customer is one machine.", P,
 "C: D, gossip between servers: over-admission of the rate times the interval, and five hundred peers chattering.", P,
 "C: E, which I pick: local buckets, with tokens leased in proportion to demand. No added latency, at most five percent over.", P,
 "V: Exact where it's cheap, bounded where it isn't, and the bound said out loud."])

mech_slide(2, 5, "Leased tokens, sized by demand", pid("L2") + " and " + pid("S2") + ", within " + pid("S1"),
           "Every 100 ms each server reports, per key, what it admitted and was asked. The quota service takes the admitted count out of the key's global bucket and leases the next interval's tokens in proportion to what each server was asked.",
           "A network call per request; a share that ignores where the traffic lands.",
           "Up to 5 % over, plus a cold start; 100 ms to follow a shift; one more service.", [
 "C: The mechanism: leased tokens, sized by demand.", P,
 f"C: It protects {ps('L2')} and {ps('S2')}, while staying inside {ps('S1')}.", P,
 "C: Every hundred milliseconds, each server reports for each key what it admitted and what it was asked. The quota service takes the admitted count out of that key's global bucket, and leases the next interval's tokens to the servers in proportion to what each was asked. The server spends its lease locally.", P,
 "C: It rules out a network call per request, and a share that ignores where the traffic lands.", P,
 "C: It costs up to five percent over plus a cold start, a hundred milliseconds to follow a shift, and one more service."], part="Mechanism")

stage("Challenge 2 of 6 · the C4 delta", "A quota service, off the request path", "v2", [
 "C: Version two. Everything from version one stays exactly where it was.", P,
 "C: New: a quota service, per region, sharded by key, state in memory. The API servers sync with it every hundred milliseconds, in batches, never per request. The limit store stays, but only for exact-mode keys: login attempts, hard-capped paid tiers. A few percent of traffic, whose owners accepted the round trip."],
 vtag="V2", cap="V2: the quota service added; V1's boxes do not move")

stage("Flow · FR1 on V2", "A request decided without leaving the server", "flow-v2", [
 "C: The request path, numbered.", P,
 "C: One: a client calls the API, and the limiter takes a token from the local bucket. In memory, about two microseconds.", P,
 "C: Two: admitted, the request goes to the backend.", P,
 "C: Three: on its own clock, every hundred milliseconds, the server sends what it admitted and was asked, and gets its next lease. Nothing on the request path waits for three."],
 cap="V2 request path: the sync is beside it, not on it")

S(tech(**ST.tech("quota")), ST.say("quota"))

stage("C4 level 3 · the API server", "Inside the API server: the limiter's seven components", "comp-api", [
 "C: Before the fix, one level down: the API server's components. The limiter is a library inside it.", P,
 "C: A request handler authenticates, asks the limiter, and routes admitted requests to the backend.", P,
 "C: A policy cache holds the policies it watches, and keeps the last good copy on disk.", P,
 "C: Local buckets hold tokens and a lease per key, and an exact client runs the store's script for exact-mode keys, with a two-millisecond timeout.", P,
 "C: A share syncer batches the reports to the quota service, and a fallback watches how old the last sync is.", P,
 "C: And a decision recorder appends every 429, and a sample of allows, to a log. The next challenges each mark two or three of these boxes."],
 cap="C4 component view: the limiter library inside the API server")

zoom("Challenge 2 of 6 · the fix", "Spend locally, lease by demand", "share-fix", strip(("fixb", "Mechanism", "A bucket per key with rate = lease ÷ 100 ms. The sync carries (key, admitted, asked, policy version); lease = available × asked ÷ Σ asked, + 5 %."),
                  ("whyb", "Covers, and does not", "Uneven balancing, hot keys, the store's latency. Not a shift faster than 100 ms: a burst of false 429s, measured in challenge six.")) + rejl(*ST.rej(3)), [
 "C: The fix, in the API server, where the request handler takes its tokens.", P, "C: The local buckets.", P, "C: And the share syncer.", P,
 "C: One level down: each key has a local bucket whose rate is its lease divided by the interval. The sync carries, per key, admitted, asked and the policy version. The quota service's lease to a server is the tokens available times that server's asked, over the sum of everyone's asked, plus five percent headroom.", P,
 "C: It covers uneven load balancing, hot keys, and the store's latency. It doesn't cover a shift in demand faster than a hundred milliseconds. That shows up as a burst of false 429s, which challenge six measures.", P,
 "C: Rejected: a static split, the limit divided by five hundred. Two per server per minute; a customer on three servers is throttled at zero point six percent."], cap="C4 component zoom: the local buckets and the share syncer")

S(dia("Mechanism 2 · as a sequence", "The lease follows the traffic", "seq-share", cap="One key, two servers, two intervals: the lease moves to where the demand is"), [
 "C: As a sequence: one key with a budget of a thousand per hundred milliseconds, and two servers.", P,
 "C: Server A admitted seven hundred and was asked seven hundred.", P, "C: Server B, three hundred.", P,
 "C: The quota service splits the next thousand by what was asked, plus five percent.", P,
 "C: A gets seven hundred and thirty-five.", P, "C: B gets three hundred and fifteen.", P,
 "C: Now the traffic moves to B. It's asked seven hundred, has three hundred and fifteen, and three hundred and eighty-five get a 429, although the customer is under its limit. That's the cost, and it lasts one interval.", P,
 "C: B reports it.", P, "C: A reports its drop.", P,
 "C: And B's next lease is eight hundred and fifteen. The share followed the demand. No server ever needed to know how the load balancer works."])

push("One customer is a tenth of all traffic, and a load-balancer change puts forty percent of it on four servers. And a customer you've never seen sends its first request to every server at once.")
S(plain("Challenge 2 of 6 · one level deeper", "Shares follow demand; a cold start is bounded", cards(
  ("grn", "Uneven balancing", "Four servers asked for 40 %, so they get 40 % of the lease. Nothing assumes even balancing."),
  ("grn", "The hot customer", "100 k/s on one key is 500 × 10 = 5,000 updates/s for the quota service, aggregated locally."),
  ("amb", "A cold key", "No lease yet: 2 provisional tokens per server. Worst case 500 × 2 = 1,000 extra, once."),
  ("red", "Honest limit", "One interval of false 429s after a fast shift; exact keys pay the round trip instead."), cols=2)), [
 P, "C: Uneven balancing: the four servers asked for forty percent of the traffic, so they get forty percent of the lease. Nothing in this design assumes the load balancer is even.", P,
 "C: The hot customer: a hundred thousand a second on one key is five hundred servers reporting ten times a second, five thousand updates a second. It's aggregated where it lands, so the hot key costs nothing special.", P,
 "C: A cold key: a server with no lease starts with two provisional tokens. Worst case, all five hundred servers at once: a thousand extra requests, once. That's the cold-start bound.", P,
 "C: The honest limit: one interval of false 429s after a fast shift. And for the few keys that must never be over, exact mode pays the round trip instead."])

say_slide("“Each server decides in memory, spending a lease of the key's global budget. Every 100 ms the quota service re-splits it by what each server was asked, so the lease follows the traffic. At most 5 % over plus a bounded cold start; exact keys pay a round trip.”", [
 "V: If asked, I'd say: each server decides in memory, spending a lease of the key's global budget. Every hundred milliseconds the quota service re-splits it by what each server was asked, so the lease follows the traffic. At most five percent over plus a bounded cold start, and exact keys pay a round trip.", "[pause: 1.0]",
 "N: That fix creates the next question. Every server now depends on the quota service. What if it's gone?"])

# ───────── Challenge 3 · the quota service is down ─────────
challenge(3, T, "The quota service is down", "At 14:02 the quota shard that owns a tenth of your keys stops answering. What does the API do, for those customers, for the next minute?",
          ["N: Challenge three is failure. The interviewer said fail open or closed is your call. This is where you defend it."])

S(trace("Challenge 3 of 6 · the trace", "One shard gone, and two wrong defaults", [
  ("14:02:00.0", "quota shard 3 in us-east loses its primary; the standby needs 20 s"),
  ("14:02:00.05", "syncs to shard 3 time out after 50 ms"),
  ("14:02:10", "fail closed: " + B("leases expire; one customer in eight gets only 429s")),
  ("14:02:10", "fail open, blindly: " + B("customer 42 sends 300 k/s straight at search"))],
  hedge=("Two wrong defaults", "One is an outage the limiter caused; the other is no protection when it is most needed.")), [
 "C: The trace.", P, "C: At two minutes past two, quota shard three in us-east loses its primary. The standby needs twenty seconds.", P,
 "C: Fifty milliseconds later, syncs to that shard time out.", P,
 "C: Fail closed, and one customer in eight gets nothing but 429s. The limiter caused an outage.", P,
 "C: Fail open blindly, and customer forty-two sends three hundred thousand a second at search.", P,
 "C: Neither default is an answer."])

zoom("Challenge 3 of 6 · the break", "Inside the API server: who notices the silence?", "down-break", strip(("case", "Naive answer", "“Fail open: the limiter must never take the API down.”"),
                  ("case", "Break", "Half right. With no lease and no bound, the one customer the limit exists for goes straight through.")), [
 "C: The same component view. The local buckets, the share syncer and the fallback are in play. The syncer is marked.", P,
 "C: The naive answer.", P, "C: Fail open: the limiter must never take the API down.", P,
 "C: It's half right. With no lease and no bound, the one customer the limit exists for goes straight through to the backend."], q=True, red=True, cap="C4 component zoom: the share syncer has lost the quota service")

mech_slide(3, 5, "Static stability, to a bounded floor", pid("S2") + ", keeping " + pid("S1") + " bounded",
           "Keep spending the last lease for its lifetime, 10 s. Then fall back to a local floor: 3 × the regional limit ÷ the region's servers. Decided per limit: product limits fail open to the floor, security limits fail closed.",
           "The limiter as the outage; and no limit at all.",
           "During the outage, a customer can reach up to 3× its limit; concentrated traffic gets less.", [
 "C: The mechanism: static stability, to a bounded floor.", P,
 f"C: It protects {ps('S2')}, and keeps {ps('S1')} bounded even then.", P,
 "C: A server keeps spending its last lease for the lease's lifetime, ten seconds. After that it falls back to a local floor: three times the regional limit, divided by the servers in the region. And it's decided per limit: product limits fail open to that floor, security limits fail closed.", P,
 "C: It rules out the limiter being the outage, and it rules out having no limit at all.", P,
 "C: It costs accuracy while the quota service is gone: a customer spread evenly can reach three times its limit, and one concentrated on a few servers gets less."], part="Mechanism")

S(dia("Mechanism 3 · as a sequence", "A lease, then a floor, then the standby", "seq-down", cap="The quota shard fails: the server keeps its lease, drops to the floor, and resumes on the standby"), [
 "C: As a sequence.", P, "C: The server syncs.", P, "C: No answer in fifty milliseconds.", P,
 "C: It keeps spending its last lease, valid for ten seconds.", P,
 "C: After ten seconds, the floor: three times the regional limit over a hundred and sixty-seven servers.", P,
 "C: Twenty seconds in, the standby is promoted, and the next sync goes to it.", P,
 "C: Leases again, one interval later. Nobody got a 503, and nobody got unlimited traffic."])

zoom("Challenge 3 of 6 · the fix", "A fallback that is decided, not defaulted", "down-fix", strip(("fixb", "Mechanism", "The fallback watches the sync age: under 10 s the lease stands; then a floor of 3 × limit ÷ servers. <code>on_failure</code> in the policy picks open-to-floor or closed."),
                  ("whyb", "Covers, and does not", "A dead shard, a slow one, a partition from it. Not a wrong policy: that is challenge five.")) + rejl(*ST.rej(4)), [
 "C: The fix, in the API server.", P, "C: The fallback, marked.", P,
 "C: One level down: the fallback watches the age of the last sync. Under ten seconds, the lease stands; then the floor. The policy's on-failure field picks open-to-the-floor or closed, chosen by the limit's owner, and tested in a game day.", P,
 "C: It covers a dead shard, a slow one, and a partition from it. It doesn't cover a wrong policy. That's challenge five.", P,
 "C: Rejected: fail closed everywhere. It makes the limiter the single point of failure of the whole API."], cap="C4 component zoom: the fallback beside the buckets and the syncer")

S(plain("Challenge 3 of 6 · the decision, as pseudocode", "Exact, leased, floored, or closed: in that order",
  pseudo("p = policy(key)                # last-known-good\nif p.mode == EXACT:\n    return exact_or(p.on_failure)  # 2 ms timeout\nb = buckets[key]\nif b.lease_until > now:\n    return b.take(cost)\nif p.on_failure == CLOSED:\n    return deny(key, \"no lease\")\nb.rate = 3 * p.region_rate / servers\nreturn b.take(cost)            # bounded, local", hl=(5, 7, 9))), [
 "C: The whole decision, as pseudocode, key lines marked.",
 "C: Line five: a valid lease is spent locally, which is almost every request. Line seven: a limit whose owner chose closed rejects when there's no lease. Line nine: everything else drops to the floor, still a token bucket, still local.",
 "C: Why it works: there's no path through this function that waits on the network, except exact mode, which has its own timeout and its own failure mode."])

push("And an hour later the policy service is down too, while fifty API servers restart.")
zoom("Challenge 3 of 6 · one level deeper", "Never block startup on a dependency", "lkg-fix", cards(
  ("grn", "Last-known-good on disk", "Every snapshot is written locally with its version; a restart loads it, then watches."),
  ("amb", "Start conservative", "No leases after a restart: provisional tokens and the floor until the first sync, 100 ms."),
  ("red", "Honest limit", "Policy changes made during the outage wait for it; the floor bounds the rest."), cols=3), [
 "C: The policy cache is the box in play.", P, "C: The policy cache, marked.", P,
 "C: Every policy snapshot is written to local disk with its version. A restarting server loads it, and starts serving before it reconnects. Even with no file at all, the release carries tier defaults, so a server never refuses to start.", P,
 "C: A restarted server has no leases: provisional tokens and the floor, until its first sync a hundred milliseconds later.", P,
 "C: The honest limit: a change made while the policy service is down waits for it. Everything else keeps working."], cap="C4 component zoom: the policy cache and its last-known-good copy")

say_slide("“The limiter keeps working on what it has: the last lease for ten seconds, then a local floor, and a last-known-good policy on disk. Open-to-the-floor or closed is decided per limit by its owner, and tested, so the limiter is never the outage.”", [
 "V: If asked, I'd say: the limiter keeps working on what it has. The last lease for ten seconds, then a local floor, and a last-known-good policy on disk. Open-to-the-floor or closed is decided per limit by its owner, and tested, so the limiter is never the outage.", "[pause: 1.0]",
 "N: That fix keeps one region standing. The next question: one customer, one quota, three regions."])

# ───────── Challenge 4 · one quota, three regions ─────────
challenge(4, T, "One quota, three regions", "A customer's contract says sixty thousand requests a minute, worldwide. Their traffic moves from Europe to the US during the day. How exact can you be?",
          ["N: Challenge four is geography. The honest answer has a number in it."])

S(trace("Challenge 4 of 6 · the trace", "A global contract against two naive answers", [
  ("08:00 UTC", "customer 7: 1,000/s worldwide; 80 % in eu-west, 15 % us-east, 5 % ap-south"),
  ("08:00", "split statically, a third each: " + B("eu gets 333/s, asks 800: 467/s rejected while under the contract")),
  ("08:00", "one global counter in us-east: " + B("every eu decision crosses the Atlantic: +80 ms")),
  ("16:00", "the traffic moves: 70 % in us-east")],
  hedge=("The number that decides it", "An exact global limit needs a 70–150 ms round trip per decision: a hundred times the budget.")), [
 "C: The trace.", P, "C: Customer seven: a thousand a second worldwide. At eight in the morning, eighty percent in Europe, fifteen in the US, five in Asia.", P,
 "C: Split statically, a third each, Europe gets three hundred and thirty-three and asks for eight hundred. Four hundred and sixty-seven a second rejected, while the customer is under its contract.", P,
 "C: One global counter in us-east instead: every European decision crosses the Atlantic. Eighty milliseconds.", P,
 "C: And at four in the afternoon the traffic moves: seventy percent in the US.", P,
 "C: Exact across regions needs a round trip of up to a hundred and fifty milliseconds per decision."])

stage("Challenge 4 of 6 · the break", "The quota service only knows its own region", "v2-break", [
 "C: Version two, with the problem marked.", P,
 f"C: The quota service is regional. It splits the budget between the servers of one region, and knows nothing of the other two, so a global contract either over-admits three times or breaks {ps('S3')}."],
 cap="V2: each region's quota service sees only its own demand")

mech_slide(4, 5, "Regional budgets, re-split every 2 s", pid("S1") + " globally, and " + pid("S3"),
           "Each region's quota service holds a budget: the global limit × its share of global demand. Every 2 s the regions exchange admitted and asked per global key and re-split. Servers still lease from their own region.",
           "A cross-region call per decision; a static split by region.",
           "2 s to follow a move; peering between regions; a partition freezes the split.", [
 "C: The mechanism: regional budgets, re-split every two seconds. The same idea one level up.", P,
 f"C: It protects {ps('S1')} across regions, and {ps('S3')}.", P,
 "C: Each region's quota service holds the global limit times its share of global demand. Every two seconds the regions exchange admitted and asked, and re-split. Servers keep leasing locally; nothing on the request path crosses an ocean.", P,
 "C: It rules out a cross-region call per decision, and a static split by region.", P,
 "C: It costs two seconds to follow a move, a peering link between regions, and when that link partitions, the split freezes."], part="Mechanism")

stage("Challenge 4 of 6 · the C4 delta", "The regions' quota services talk to each other", "v3", [
 "C: This one changes the container view, so it's version three. Version two, carried, with one box new.", P,
 "C: The other regions: their quota services. Ours exchanges regional totals with them every two seconds over gRPC, for keys whose scope is global. Most keys are regional, and never leave the region."],
 vtag="V3", cap="V3: regional quota services exchange totals every 2 s")

S(dia("Mechanism 4 · as a sequence", "Three regions re-split one budget", "seq-regions", cap="Three quota services exchange totals and re-split one global budget"), [
 "C: As a sequence, between the three regions' quota services.", P,
 "C: Every two seconds, Europe reports customer seven: admitted seven hundred and ninety a second, asked eight hundred.", P,
 "C: The US: a hundred and fifty.", P, "C: Asia: fifty.", P,
 "C: So the global thousand splits by what was asked: eight hundred, a hundred and fifty, fifty.", P,
 "C: At four in the afternoon the US asks for seven hundred. For at most two seconds it's held to a hundred and fifty.", P,
 "C: It reports.", P,
 "C: And the re-split follows: Europe two hundred and seventy, the US six hundred and eighty, Asia fifty. Two seconds to follow a move that took hours to happen."])

push("The Atlantic link partitions for ten minutes.")
S(plain("Challenge 4 of 6 · one level deeper", "A partition makes it stricter, not looser", cards(
  ("grn", "Each region keeps its last budget", "The budgets still sum to the global limit, so nobody over-admits."),
  ("amb", "A silent peer's budget is not taken", "Budgets are leased for 30 s and renewed; a region never spends one it cannot see renewed."),
  ("red", "Honest limit", "A region whose demand grows during the partition is held to its last budget: false 429s, measured.")) +
  rejl(*ST.rej(5))), [
 P, "C: Each region keeps its last budget. They still add up to the global limit, so a partition makes the limit stricter, never looser.", P,
 "C: And no region takes a silent peer's share. Budgets are leased for thirty seconds and renewed; a peer that can't be heard keeps its budget until it expires on both sides, and then both fall to their contracted regional weight.", P,
 "C: The honest limit: a region whose demand grows during the partition is held to its last budget. Those are false 429s, and challenge six counts them.", P,
 "C: Rejected: one global counter in one region: a hundred times the budget for the other two. I'd write global within two seconds and five percent into the contract."])

say_slide("“Exact across regions costs a cross-region round trip per decision, so I don't promise it. Each region holds a budget proportional to its share of global demand, re-split every two seconds; a partition freezes the split, stricter, never looser.”", [
 "V: If asked, I'd say: exact across regions costs a cross-region round trip per decision, so I don't promise it. Each region holds a budget proportional to its share of global demand, re-split every two seconds. A partition freezes the split: stricter, never looser.", "[pause: 1.0]",
 "N: That fix makes the limits right in space. The next question changes them in time."])

# ───────── Challenge 5 · the curveball: a scheduled burst ─────────
challenge(5, T, "10× burst for 30 seconds, every hour", "A large customer's batch job runs at the top of every hour. They need ten times their rate for the first thirty seconds. Can your design express that?",
          ["N: Challenge five is the curveball. It tests whether the algorithm can express real policy, and whether the candidate pushes back on special cases."])

S(trace("Challenge 5 of 6 · the trace", "A batch job against a flat bucket", [
  ("tier", "customer 9: 100/s, burst 200"),
  ("13:00:00", "the job fires: 1,000/s for 30 s, 30,000 requests"),
  ("13:00:30", B("200 + 100 × 30 = 3,200 admitted; 26,800 get 429")),
  ("13:05", "their ticket: “your limiter breaks our nightly reconciliation, every hour”")],
  hedge=("And it is not one customer", "About 200 customers have hourly jobs: they are the 3 M/s peak in the scale line.")), [
 "C: The trace.", P, "C: Customer nine has a hundred a second with a burst of two hundred.", P,
 "C: At one o'clock their job fires: a thousand a second for thirty seconds. Thirty thousand requests.", P,
 "C: The bucket admits its burst plus thirty seconds of refill: three thousand two hundred. Twenty-six thousand eight hundred get a 429.", P,
 "C: And a ticket: your limiter breaks our job, every hour.", P,
 "C: It isn't one customer. About two hundred have hourly jobs. They're the three-million-a-second peak in the scale line."])

stage("Challenge 5 of 6 · the break", "A policy is a rate and a burst, with no time in it", "pol-break", [
 "C: Version three, with the problem marked.", P,
 "C: The policy service stores a rate and a burst. There's no way to say 'ten times, for thirty seconds, every hour', so the naive answer is a hand edit at one minute to one, and someone undoing it at one past."],
 cap="V3: the policy service has no notion of time")

mech_slide(5, 5, "Scheduled, versioned, staged policy", pid("L1") + " and " + pid("S1"),
           "A tier carries time windows: a cron, a duration and a multiplier. Every bucket computes its rate from the active window. A change is a new version that goes shadow → canary → enforced.",
           "Hand edits at 12:59; a code path per customer; a bad change everywhere at once.",
           "A window check on every refill; minutes to roll out; the hour's peak must be paid for.", [
 "C: The mechanism: scheduled, versioned, staged policy.", P,
 f"C: It protects {ps('L1')}, and {ps('S1')} at the top of every hour.", P,
 "C: A tier carries time windows: a cron, a duration and a multiplier. Every bucket, local and global, computes its rate from the window active now. And a change is a new version that goes through shadow, canary and enforced.", P,
 "C: It rules out hand edits at one minute to the hour, a code path per customer, and a bad change reaching every server at once.", P,
 "C: It costs a window check on every refill, minutes to roll out, and the top of the hour's peak has to be paid for by someone."], part="Mechanism")

zoom("Challenge 5 of 6 · the fix", "Bursts as a tier, not an exception", "pol-fix", strip(("fixb", "Mechanism", "A tier “batch-hourly”: rate × 10 from :00:00 to :00:30, with an owner and an expiry. The quota service and every bucket evaluate the same version, so leases follow."),
                  ("whyb", "Covers, and does not", "Any scheduled burst, sold and capacity-planned. Not the backend's own limit: 200 jobs at :00 is the 3 M/s peak.")) + rejl(*ST.rej(6)), [
 "C: The fix, on the container view.", P, "C: The policy service.", P, "C: And its store.", P,
 "C: One level down: a tier called batch-hourly, ten times the rate for the first thirty seconds of the hour, with an owner and an expiry. Every bucket and the quota service evaluate the same version, so leases grow at one o'clock by themselves.", P,
 "C: It covers any scheduled burst, sold and capacity-planned. It doesn't make the backend absorb two hundred jobs at once: that's the three-million peak, and the tier is sold against it.", P,
 "C: Rejected: hand-edited per-customer exceptions. No owner, no expiry, no staged rollout. Two hundred of them, and every top of the hour is a capacity incident."], cap="V3: the policy service and its store carry scheduled tiers")

S(plain("Challenge 5 of 6 · the schedule, as pseudocode", "The rate depends on the time; nothing else changes",
  pseudo("def rate(p, t):\n    for w in p.tier.windows:     # cron, 30 s, x10\n        if w.active(t):\n            return p.rate * w.mult\n    return p.rate\n\nr = rate(p, now)\ntokens = min(cap(p, now),\n             tokens + (now - ts) * r)", hl=(3, 7, 8))), [
 "C: As pseudocode, key lines marked.",
 "C: Line three: a window is active by the time now, from a cron and a duration. Line seven: the rate for this refill. Line eight: the same lazy refill as challenge one, with a rate and a cap that depend on the time.",
 "C: Why it works: the bucket was always a function of the policy and the time; a schedule makes the policy one too."])

push("Two hundred more customers want the same. And one Friday an edit with a typo sets every limit in a tier to zero.")
S(plain("Challenge 5 of 6 · one level deeper", "A limit change is a deploy: validate, shadow, canary, roll back", cards(
  ("grn", "Validate", "A cut of more than 50 %, or a change to over 1,000 customers, needs a second approver."),
  ("grn", "Shadow", "Evaluated beside the enforced version and logged: “would have rejected 41 % of requests”."),
  ("amb", "Canary", "1 % of servers for 5 min; rolled back by itself if their 429 rate doubles."),
  ("red", "Roll back", "Servers keep the last 3 versions: back to the previous one everywhere in under 10 s."), cols=2)), [
 "C: The typo is the more important half. A limit change is a deploy, and it goes through the lifecycle from chapter three.", P,
 "C: Validate: a cut of more than half, or a change touching more than a thousand customers, needs a second approver.", P,
 "C: Shadow: every server evaluates the new version beside the enforced one and logs the difference. 'This would have rejected forty-one percent of requests' is caught before anyone is rejected.", P,
 "C: Canary: one percent of servers for five minutes, rolled back by itself if their 429 rate doubles.", P,
 f"C: And roll back: servers keep the last three versions, so going back is a pointer move, everywhere in under ten seconds. That's {ps('L1')}, used in the other direction."])

S(tech(**ST.tech("pol")), ST.say("pol"))

say_slide("“Yes: a tier carries time windows, evaluated identically by every bucket and the quota service. I'd sell it as a tier with an owner and an expiry, against planned capacity, not as an exception. And every limit change is a deploy: validated, shadowed, canaried, rolled back in seconds.”", [
 "V: If asked, I'd say: yes. A tier carries time windows, evaluated identically by every bucket and the quota service. I'd sell it as a tier with an owner and an expiry, against planned capacity, not as an exception. And every limit change is a deploy: validated, shadowed, canaried, and rolled back in seconds.", "[pause: 1.0]",
 "N: That fix creates the last question. Every part can now be right. How would you know when a customer was limited wrongly?"])

# ───────── Challenge 6 · "you limited us while we were under" ─────────
challenge(6, T, "“You limited us while we were under”", "A top customer says you rejected them last Tuesday from two to twenty past, while they were under their limit. What do you look at, and how would you have known first?",
          ["N: Challenge six is observability. In this question it is about a wrong decision, not a down server."])

S(trace("Challenge 6 of 6 · the trace", "Twenty minutes of wrong 429s, all dashboards green", [
  ("Tue 13:58", "a load-balancer change moves 60 % of customer 42's traffic onto 12 servers in one zone"),
  ("14:00–14:20", "those servers' leases lag every interval: " + B("3 % of requests get 429 at 85 % of the limit")),
  ("14:00–14:20", "decision latency, quota service, error rate: green; total 429 rate +0.1 %"),
  ("Fri", B("the customer's escalation, with request IDs and a contract number"))],
  hedge=("What nobody measured", "Rejections of a customer who was under its limit.")), [
 "C: The trace.", P, "C: Tuesday at two minutes to two, a load-balancer change moves sixty percent of customer forty-two's traffic onto twelve servers in one zone.", P,
 "C: For twenty minutes, those servers' leases lag the demand every interval. Three percent of the customer's requests get a 429, while it's at eighty-five percent of its limit.", P,
 "C: Decision latency, the quota service and the error rate are green, and the total 429 rate rose by a tenth of a percent.", P,
 "C: On Friday, an escalation with request IDs and a contract number.", P,
 "C: What nobody measured: rejections of a customer who was under its limit."])

stage("Challenge 6 of 6 · the C4 delta", "Every decision that matters, recorded and queryable", "v4", [
 "C: This changes the container view: version four. Version three, carried, with two boxes new.", P,
 "C: A decision log, in Kafka: every 429, and one allow in a hundred, appended without waiting.", P,
 "C: And a decision store, ClickHouse, loaded from it. The policy service answers 'why was I limited' by querying it."],
 vtag="V4", cap="V4: the decision log and the decision store")

zoom("Challenge 6 of 6 · the fix", "Record the decision, with everything that made it", "obs-fix", strip(("fixb", "Mechanism", "Per 429: decision ID, key, server, policy version, mode, lease, local tokens, sync age, global admitted at the last sync. Fire-and-forget; drops are counted."),
                  ("whyb", "Covers, and does not", "Any 429 explained from its ID, in minutes. Not the allows in full: a 1 % sample is enough for rates.")) + rejl(*ST.rej(7)), [
 "C: The fix, inside the API server.", P, "C: The decision recorder.", P,
 "C: One level down: for every 429 it records the decision ID sent to the client, the key, server, policy version, mode, lease, local tokens, sync age, and the global count at that sync. Appended without waiting; if Kafka is slow, records are dropped and counted.", P,
 "C: It covers any 429, explained from its ID in minutes. It doesn't record every allow. A one percent sample is enough for rates.", P,
 "C: Rejected: sampling the 429s like the allows. The rejection the customer is asking about is the one you dropped."], cap="C4 component zoom: the decision recorder")

S(plain("Challenge 6 of 6 · the fix, one level down", "Three signals about decisions, not machines", cards(
  ("grn", "False-limit rate", "429s on keys whose global admitted rate that minute was under 95 % of the limit. SLO: under 0.1 % per customer per day."),
  ("grn", "Latency and sync age", "Decision p99 under 1 ms; sync age p99 under 300 ms; share of servers on the floor."),
  ("grn", "Over-admission", "Global admitted against the limit, per key-minute: alert above 5 %."), cols=3) +
  strip(("whyb", "Answering the customer", "The decision ID on their 429 → the record → policy version, lease, global count: the false limits, minute by minute."), cols="one")), [
 "C: One level down, three signals, about decisions rather than machines.", P,
 f"C: The false-limit rate. A scheduled query joins the decisions with the quota service's global totals per key and minute, and counts 429s where the customer was under ninety-five percent of its limit. The SLO is under a tenth of a percent per customer per day. That's {ps('S3')}, made measurable, and it would have fired on Tuesday at two oh five.", P,
 "C: Latency and sync age: decision p99 under a millisecond, sync age p99 under three hundred milliseconds, and the share of servers running on the floor.", P,
 "C: And over-admission, the other direction: global admitted against the limit, alerting above five percent.", P,
 "C: To answer the customer: the decision ID on their 429 leads to the record. We can show their false limits minute by minute, and the balancer change behind them."])

S(plain("Challenge 6 of 6 · reading the signals", "Symptoms in pairs: what each one means", table(["Symptom", "Paired with", "Means"], [
  ["False limits up", "sync age normal", "demand moved faster than 100 ms: a balancer change"],
  ["False limits up", "sync age up", "the quota service is slow"],
  ["429s up", "global admitted at the limit", "a real overage: correct"],
  ["Over-admission above 5 %", "many new keys", "cold starts, or headroom too large"],
  ["Servers on the floor", "sync errors to one shard", "a quota shard is down: challenge three"]], "bt sm")), [
 "C: Read symptoms in pairs; a number alone is not a diagnosis.", P,
 "C: False limits up, sync age normal: demand moved faster than the interval. A balancer change. Our case.", P,
 "C: False limits up, sync age up: the quota service is slow.", P,
 "C: 429s up while the global count is at the limit: a real overage. The limiter is doing its job.", P,
 "C: Over-admission above five percent with many new keys: cold starts, or too much headroom.", P,
 "C: Servers on the floor, with sync errors to one shard: that shard is down, challenge three."])

S(tech(**ST.tech("dstore")), ST.say("dstore"))

push("And if the decision log itself drops records?")
S(plain("Challenge 6 of 6 · one level deeper", "Check the checker", cards(
  ("grn", "Counters reconcile the log", "Each server counts its 429s per minute as a metric; the log's count must match within 0.1 %, or it pages."),
  ("grn", "A canary customer", "A synthetic key sends 90 % of its limit from every region; any 429 to it pages."), cols=2)), [
 P, "C: Counters reconcile the log. Each server counts its 429s per minute as a plain metric, never sampled. The log's count for that minute must match within a tenth of a percent, or it pages about itself.", P,
 "C: And a canary customer: a synthetic key that sends ninety percent of its limit from every region, all day. It is never over, so any 429 to it is a false limit by construction, and it pages."])

say_slide("“I'd answer from the decision ID on their 429: its record shows their false limits minute by minute. And I'd have known first: a false-limit rate per customer with an SLO, over-admission in the other direction, and a canary customer that should never see a 429.”", [
 "V: If asked, I'd say: I'd answer from the decision ID on their 429. Its record shows their false limits, minute by minute. And I'd have known first: a false-limit rate per customer with an SLO, over-admission in the other direction, and a canary customer that should never see a 429.", "[pause: 1.0]"])
