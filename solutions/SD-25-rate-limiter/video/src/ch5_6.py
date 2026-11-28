from dsl import *
import stack
P = "[+]"
ST = stack.load(pathlib.Path(__file__).resolve().parents[2])

# ───────────────────────── 5 · when you don't need all this ─────────────────────────
chapter(5, "When you don't need all this", 4, "The simpler design, and the number where it stops being enough", [
 "C: Before the recap: a much smaller design is correct at a smaller scale, and I should say where the line is."])

zoom("Alternate path", "One Redis, one script, a config file", "alt", strip(("fixb", "How it works", "Each request runs challenge one's token-bucket script on one Redis primary with a replica; limits come from a config file deployed with the API."),
                  ("case", "What it gives up", "A round trip on every request; Redis on the critical path, so it must fail open; a hot key on one thread; no global scope.")), [
 "C: The alternate path: no quota service, no policy service, no decision store.", P,
 "C: One Redis, marked alternate. Each request runs challenge one's script on one primary, with a replica.", P,
 "C: Limits come from a config file deployed with the API. It's exact, and it's version one with the right algorithm.", P,
 "C: What it gives up, precisely: a round trip on every request. Redis on the critical path, so it must fail open, explicitly. A hot customer on one thread. And no global scope across regions."], cap="The alternate: every request runs one script on one Redis")

key("Alternate · the crossover", "One shard runs about <em>100,000 scripts a second</em>. We peak at <em>3 million</em>, with a 1 ms budget. Below about <em>50,000 requests a second</em> in one region, with a couple of milliseconds to spare, I'd ship one Redis and one script.", [
 "C: Where is the line? One shard runs about a hundred thousand scripts a second. We peak at three million, with a budget of one millisecond. That's sixty times past what one shard does comfortably, and the budget is under the round trip.",
 "V: Below about fifty thousand requests a second at peak, in one region, with a couple of milliseconds to spare, I'd ship one Redis and one script, and say out loud the number where I'd switch.", "[pause: 0.8]"])

# ───────────────────────── 6 · recap ─────────────────────────
chapter(6, "Recap", 5, "The final design, the trade-offs, and what comes next", [
 "C: The recap. One picture with the mechanisms on it, the stack against its rivals, and the mistakes that cost most."])

stage("Recap · the final container view", "Where each mechanism ended up", "recap", [
 "C: Version four, the final design: the same picture as version one, with four boxes more. The mechanisms go on it one at a time.", P,
 "C: The API server decides in memory: a leased token bucket, and a floor when the lease is old.", P,
 "C: The limit store holds only the exact keys, one atomic script each.", P,
 "C: The quota service leases each key's budget by demand, every hundred milliseconds.", P,
 "C: The regions re-split global budgets every two seconds.", P,
 "C: The policy service ships every limit change as a staged version.", P,
 "C: And the decision store turns every 429 into an answer, and into a false-limit rate."], vtag="V4", cap="The final design with its mechanisms")

S(plain("Recap · the trade-offs", "The stack, against its rivals", table(["Container", "Choice", "Rejected", "The deciding reason"], ST.summary(), "bt xs mx") +
  grade("Naming a product is not the signal. Naming the property that rules out its rival is.")), ST.summary_say() + [P,
 "N: Naming a product is not the signal. Naming the property that rules out its rival is. Interviewers go one level down on whichever box you name, so name only what you can defend."])

S(plain("Recap · the mistakes", "What costs most in this round", table(["Mistake", "Instead"], [
  ["A Redis increment per request, per fixed window", "a token bucket, decided in memory, leased"],
  ["Read the counter, then write it", "one atomic script, timed by the store's clock"],
  ["The limit divided by the number of servers", "leases that follow demand"],
  ["Fail closed by default", "a failure mode per limit, to a bounded floor"],
  ["“Exactly global” across regions", "regional budgets re-split every 2 s, the bound stated"],
  ["No answer to “why was I limited?”", "a decision ID on every 429; a false-limit SLO"]], "bt sm")), [
 "N: The mistakes that cost most in this round.", P,
 "N: A Redis increment per request, per fixed window. Instead, a token bucket, decided in memory, from a lease.", P,
 "N: Reading the counter, then writing it. Instead, one atomic script, timed by the store's clock.", P,
 "N: Dividing the limit by the number of servers. Instead, leases that follow demand.", P,
 "N: Failing closed by default. Instead, a failure mode per limit, to a bounded floor.", P,
 "N: Promising exactly global across regions. Instead, regional budgets re-split every two seconds, and the bound stated.", P,
 "N: And no answer to 'why was I limited'. Instead, a decision ID on every 429, and a false-limit SLO."])

followups([
  ("Billing wants the limiter's counts", "no: metering reads the request logs, exactly"),
  ("An export costs 50 times a search", "a cost per endpoint; take(cost), same bucket"),
  ("A slow backend needs concurrency limits", "an in-flight count per key (part 12.4)"),
  ("All within quota, and the backend melts", "shedding by criticality (part 12.5)"),
  ("Build or buy?", "a gateway's limiter is V1; build leases for 1 ms"),
  ("What would you ship in week one?", "local buckets, static share, shadow mode, 429s logged")], [
 "C: The follow-up questions an interviewer asks next, and where I'd start.", P,
 "C: Billing wants the limiter's counts: no. Metering reads the request logs, exactly. The limiter is allowed to be five percent off.", P,
 "C: An export costs fifty times a search: a cost per endpoint in the policy, taken from the same bucket.", P,
 "C: A slow backend needs concurrency limits: an in-flight count per key, released on completion. A different limiter.", P,
 "C: Everyone is within quota and the backend still melts: that's load shedding by criticality, not quotas.", P,
 "C: Build or buy: a gateway's global rate-limit service is version one. I'd build the lease layer only for a one-millisecond budget or global scope.", P,
 "C: And week one, at the manager layer: in-process buckets with a conservative static share, in shadow mode, with every 429 logged. Leases in week four, global scope when a contract asks for it."])

key("The close", "A rate limiter sits on every request, so its <em>availability and latency</em> matter more than its accuracy: decide <em>in memory</em>, lease the budget to <em>where the traffic lands</em>, and know exactly how wrong you can be.", [
 "V: A rate limiter sits on every request, so its availability and latency matter more than its accuracy. Decide in memory, lease the budget to where the traffic lands, and know exactly how wrong you can be.", "[pause: 1.0]",
 "C: Thanks for watching. The written design, generated from this same script, is linked below."])
