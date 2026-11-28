from dsl import *
P = "[+]"

# ───────────────────────── 3 · API contracts and the data model ─────────────────────────
chapter(3, "API and data model", 2, "What crosses the wire, and what is stored", [
 "C: The API next, then the data. Every contract is tagged with the requirement it serves."])

S(plain("API · the decision (FR1) and the client contract (FR2)", "What the client sees when it is over",
  chips("serves FR1 and FR2", "every response carries the headers") +
  code('GET /v1/search?q=…            (customer 42)\n\n429 Too Many Requests\nRateLimit-Limit: 1000\nRateLimit-Remaining: 0\nRateLimit-Reset: 7\nRetry-After: 7\n{"error": "rate_limited",\n "decision_id": "d-7f3c…", "policy": "42:/search@v19"}', "http", hl=(3, 7, 9))), [
 "C: The decision itself is a function call inside the API server: allow, for a customer, an endpoint and a cost, usually one. It returns allowed, what remains, when it resets, and a decision ID. FR1.",
 "C: What the client sees is FR2. Every response carries the limit, what remains and the seconds to reset, not only the rejections, so a well-behaved client slows down before it hits the wall. A rejection is a 429 with Retry-After: seven seconds. Clients are expected to back off with jitter, or the top of the hour becomes a retry storm.",
 "C: And the body carries a decision ID and the policy version. That ID is how support answers 'why was I limited' in challenge six."])

S(plain("API · configuration, sync and explain", "Three more contracts, each tagged", table(["Contract", "Serves", "Key fields", "What it returns"], [
  ["<code>PUT /v1/policies/{customer}/{endpoint}</code>", "FR3", "<code>If-Match</code> version; tier, burst, schedule, scope, mode, on_failure", "<code>202</code>: the new version, in <code>shadow</code>"],
  ["<code>Sync</code> RPC, server → quota service", "FR1 at scale", "per key: admitted, asked, policy version", "per key: lease, valid until, global remaining"],
  ["<code>GET /v1/decisions/{id}</code>", "FR4", "the decision ID from the 429", "policy version, server, mode, lease, global count"]], "bt xs mx")), [
 "C: Three more contracts.", P,
 "C: Configuration, for FR3: a PUT per customer and endpoint, with If-Match on the current version so two edits can't overwrite each other. It sets a tier, burst, schedule, scope, mode, and what to do on failure. It answers 202 with a new version, and that version starts in shadow, not enforced.", P,
 "C: The sync, between an API server and the quota service: for each key, what it admitted and what it was asked. Back comes a lease for the next interval. This is what makes FR1 work at this scale; it's internal, and batched.", P,
 "C: And explain, for FR4: give it the decision ID from a 429, and it returns the policy version, server, mode, lease and the global count behind it."])

S(dia("Data · physical model", "Where each piece of state lives, and its key", "erd-physical", cap="The physical model: two durable tables, three kinds of bucket, one decision log"), [
 "C: The physical model, one piece at a time.", P,
 "C: Tiers, in PostgreSQL. About twenty: a rate, a burst, and optional time windows. Most customers inherit one.", P,
 "C: Policy: keyed by customer, endpoint and version. It names a tier, a scope, region or global, a mode, local or exact, and a failure mode, open or closed. A change is a new version, with an owner and an expiry.", P,
 "C: A local bucket, in each API server's memory: tokens, last refill on the monotonic clock, and the current lease with its expiry.", P,
 "C: A global bucket, in the quota service's memory: tokens, and what each server asked for in the last interval.", P,
 "C: An exact bucket, a Redis hash, only for exact-mode keys, refilled using the shard's own clock.", P,
 "C: And decisions, in ClickHouse: every 429 and a sample of allows, keyed by customer, endpoint and time. Notice that nothing on the request path is durable. The durable things are the policy, and the record of what was decided."])

S(dia("Data · the life of one policy version", "A limit change is a production change", "state-policy",
      cap="The lifecycle of one policy version: draft, shadow, canary, enforced, superseded or rolled back"), [
 "C: And the lifecycle of one policy version, because a limit change can take the API down as surely as a bad deploy.", P,
 "C: It starts as a draft, validated.", "[+2]",
 "C: In shadow, every server evaluates it beside the enforced version, and logs what it would have done, without doing it.", "[+2]",
 "C: In canary, one percent of servers enforce it for five minutes.", "[+2]",
 "C: Then it's enforced, everywhere.", "[+3]",
 "C: If the canaries' 429 rate doubles, or someone says so, it's rolled back to the previous version, from canary or from enforced.", "[+2]",
 "C: And an enforced version is eventually superseded by the next. Servers keep the last three, so a rollback is a pointer move. Challenge five lives on this diagram."])
