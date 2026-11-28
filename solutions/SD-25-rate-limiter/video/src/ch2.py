from dsl import *
P = "[+]"

# ───────────────────────── 2 · back-of-the-envelope ─────────────────────────
chapter(2, "Estimates", 1, "Each number from the scale line, and the constraint it forces", [
 "C: Numbers next. Each starts from the scale line, and each ends in a constraint on the design: what it rules out, and what it forces. They are illustrative, not anyone's real figures."])

S(plain("Estimates · traffic and the fleet", "Three million decisions a second, six thousand per server", table(["Number", "From", "Arithmetic", "Forces"], [
  ["Requests", "average", "1 M/s × 2.6 × 10⁶ s = <b>2.6 T</b> a month; × 3 = <b>3 M/s</b> at peak", "a decision per request: in memory, in microseconds"],
  ["Per server", "peak, fleet", "3 M/s ÷ 500 = <b>6,000/s</b>; × 2 µs = 1.2 % of a core", "in process is cheap; a sharded map, no global lock"],
  ["Central store", "peak", "3 M scripts/s ÷ ~100 k per shard ≈ <b>30 primaries</b>", "feasible, but a dependency on every request"]])), [
 "C: Traffic, from the average.", P,
 "C: A million a second over two point six million seconds is two point six trillion a month, and three times the average at the top of the hour: three million a second. Every one of them needs a decision, so the decision has to be cheap: in memory, in microseconds.", P,
 "C: Per server, three million over five hundred is six thousand a second. At about two microseconds a decision, that's just over one percent of a core. Doing it in process is cheap, as long as the map is sharded and there's no global lock.", P,
 "C: And if instead every request ran a script in a central store: three million scripts a second, at roughly a hundred thousand per shard, is about thirty primaries. Feasible. But it puts a network hop and a dependency on every API call. Keep that number; challenge two prices it."])

S(plain("Estimates · the two numbers that decide the design", "Two per server per minute, and one round trip", table(["Number", "From", "Arithmetic", "Forces"], [
  ["Static split", "limit, fleet", "1,000/min ÷ 500 = <b>2 per server per minute</b>; on 3 servers: 6/min = <b>0.6 %</b> of the quota", "rules out dividing the limit; the share must follow demand"],
  ["Round trip", "latency NFR", "in-zone ~0.3 ms median, <b>~1.2 ms p99</b>; cross-region <b>70–150 ms</b>", "no call on the default path; no exact global limit"]])), [
 "C: Two numbers decide this design.", P,
 "C: The static split. A thousand a minute divided by five hundred servers is two per server per minute. Connections are sticky, so a customer's traffic may land on just three servers, and then it gets six a minute: zero point six percent of its quota. Dividing the limit statically is ruled out. Whatever each server holds has to follow where the traffic actually is.", P,
 "C: And the round trip. Inside a zone a network call is about a third of a millisecond at the median, and over a millisecond at p99 under load. Across regions it's seventy to a hundred and fifty. So the default path makes no network call at all, and an exact global limit across regions is out of the question on the request path."])

S(plain("Estimates · state, the hot customer, the sync", "Memory is small; the hot key and the sync are what to size", table(["Number", "From", "Arithmetic", "Forces"], [
  ["State", "keys", "2 M × 64 B = <b>128 MB</b>; ~20 k active per server ≈ 1.3 MB", "memory is not the problem"],
  ["Hot customer", "peak", "100 k/s on one key vs ~100 k ops/s per shard; leased: 500 × 10 = <b>5,000 updates/s</b>", "aggregate locally, never a counter per request"],
  ["Sync", "fleet", "167 servers × 10/s ≈ 1,700 batches/s a region; ≤ 600 keys each ≤ <b>1 M key-updates/s</b>", "batched, sharded by key, off the request path"],
  ["Decisions", "average", "1 % 429s + 1 % of allows = 20 k/s × 150 B = 3 MB/s ≈ <b>1.6 TB</b> / 30 days compressed", "a columnar store, not a search index"]])), [
 "C: Where the bytes and the load go.", P,
 "C: State: two million keys at sixty-four bytes is a hundred and twenty-eight megabytes for everything. One server's active keys are a megabyte or so. Memory is not the problem.", P,
 "C: The hot customer: a hundred thousand a second on one key. A central counter for it would be one shard's whole thread. If each server aggregates locally and reports ten times a second, the coordinator sees five hundred times ten: five thousand updates a second for that key. So: aggregate locally.", P,
 "C: The sync itself: a hundred and sixty-seven servers per region, ten batches a second each, about seventeen hundred batches a second. At peak a batch carries at most six hundred keys, so up to a million key updates a second per region. That's real, so it's batched, sharded by key, and off the request path.", P,
 "C: And the decisions we keep: every 429, about one percent of requests, and a one-percent sample of the allows. Twenty thousand records a second, three megabytes a second, about one point six terabytes compressed for thirty days. A columnar store."])

S(dia("Estimates · the latency budget", "One millisecond, if every request asked a store", "budget", chip=chips("illustrative", "p99"),
      cap="The exact path against the 1 ms budget: over before the backend is even called"), [
 "C: The latency budget, on the exact path. The policy lookup and the script together, about a tenth of a millisecond. A round trip to the store at p99, about one point two. One point three milliseconds against a budget of one. Over.",
 "C: The local path, a map lookup and a token take, is about three hundredths of a millisecond. That gap is the whole design. And it forces one more rule: an exact check is allowed only where a limit's owner accepts paying for it."])
