from dsl import *
P = "[+]"

# ───────────────────────── 1 · prompt, clarifying questions, C4 context ─────────────────────────
chapter(1, "Prompt, questions and context", 0, "A limit on every request, enforced by five hundred servers", [
 "C: A rate limiter sounds like a counter and an if statement. It is one of the most asked questions at Google and Meta, because the counter has to live somewhere, and wherever it lives, it sits on the path of every single request."])

qs("Interviewer · the prompt", "“Design a rate limiter for our API. Every customer has a quota, and we need to enforce it across a fleet of servers.”", [
 "I: Design a rate limiter for our API. Every customer has a quota, and we need to enforce it across a fleet of servers.", "[pause: 1.5]"])

S(dia("Why it is harder than it looks", "One quota, five hundred servers, three answers", "tension",
      chip=chips("exact and slow", "fast and wrong", "fast and bounded"), cap="One customer, 1,000 a minute, 500 servers: three ways for each server to know"), [
 "C: Here is the hook, as one picture. One customer may send a thousand requests a minute, and those requests land on five hundred servers. How does each server know whether to say yes?",
 "C: One central counter is exact, and every request waits on it. Dividing the limit by five hundred gives each server two a minute. The third answer leases the budget to wherever the traffic lands: at most five percent over, decided in microseconds.",
 "C: The whole round is choosing that trade on purpose, and being able to say exactly how wrong it can be."])

S(plain("Before the design", "What this question grades", table(["Axis", "Weak signal", "Strong signal"], [
  ["<b>Requirements</b>", "“Count requests”; the limiter as a billing meter", "A protection limit; billing is a separate, exact pipeline"],
  ["<b>Correctness</b>", "A fixed window; read, then write", "Algorithms compared; the boundary burst; one atomic step"],
  ["<b>Trade-offs</b>", "“Use Redis”, or “be exact”", "Exact costs a round trip per request; the error is stated as a number"],
  ["<b>Depth</b>", "Stops at a counter in a cache", "Leases sized by demand, the cold-start bound, regional budgets"],
  ["<b>Operations</b>", "Fail closed without noticing", "A failure mode per limit; a false-limit rate; “why was I limited?”"]], "bt xs sig") +
  grade("The limiter's own availability and latency matter more than its accuracy.")), [
 "N: What this question grades.", P,
 "N: Requirements: is this a protection limit or a billing meter? They are different systems.", P,
 "N: Correctness: algorithms compared, not listed, and a check-and-take that is one atomic step.", P,
 "N: Trade-offs: exact costs a round trip on every request. Strong answers say what they give up, as a number.", P,
 "N: Depth: how the budget is split across servers, what happens to a brand-new key, and what happens across regions.", P,
 "N: Operations: what the limiter does when its dependency fails, and how you answer 'why was I limited?'", P,
 "C: And the rule I keep all round: the limiter sits on every request, so its own availability and latency matter more than its accuracy."])

S(plain("Requirements · the scale line", "Four numbers every estimate starts from", '<div class="tiles" style="--n:4">'
  '<div class="tile blue"><b>1 M/s · 2.6 T</b><span>requests: average a second · a month</span></div>'
  '<div class="tile"><b>500 · 3</b><span>API servers · regions</span></div>'
  '<div class="tile"><b>2 M · 30 days</b><span>limit keys · decisions kept</span></div>'
  '<div class="tile red"><b>3 M/s</b><span>at the top of the hour; one customer at 100 k/s</span></div></div>' +
  line("Every number later in this video starts from one of these, and I'll say which.", "a")), [
 "C: The interviewer gives me the scale, and I write it down first.", P,
 "C: A million requests a second on average. That's two point six trillion a month.", P,
 "C: Spread over five hundred API servers in three regions.", P,
 "C: Two million limit keys: a hundred thousand customers, times about twenty endpoints each. And thirty days of decisions kept, so support can answer questions about last week.", P,
 "C: And the peak: three million a second at the top of every hour, when customers' batch jobs start. Inside it, one customer alone sends a hundred thousand a second.", P,
 "C: Every number I use later starts from one of these, and I'll say which."])

def clar(n, q, a, ask, ans, so):
    S(f'<div class="who">Clarifying question {n} of 5</div><div class="qq">{q}</div><div class="ans">{a}</div>',
      ["C: " + ask, P, "I: " + ans, "C: " + so], cls="qs")

clar(1, "What exactly is limited?", "Per customer and per endpoint, for example 1,000 a minute. Some customers have a hundred times the limit of others.",
     "What exactly is a limit keyed by?", "Per customer and per endpoint. For example, a thousand requests a minute on search. Some customers have a hundred times the limit of others.",
     "So the key is customer and endpoint, two million of them, and the big ones will be hot keys.")
clar(2, "How exact must it be?", "“How accurate can you be, and what does exact cost?”",
     "How exact does it have to be?", "How accurate can you be, and what does exact cost?",
     "That's the question of the round, handed back to me. I'll treat this as a protection limit, not a billing meter. If billing needs exact counts, that's a separate pipeline from the request logs. Here I'll name an error bound and defend it.")
clar(3, "What latency can the limiter add?", "Under one millisecond at p99.",
     "How much latency may the limiter add?", "Under one millisecond, at p99.",
     "One millisecond at p99 is about the p99 of one network round trip inside a zone. So the default decision cannot make a network call.")
clar(4, "What happens at the limit, and if the limiter fails?", "A 429 with Retry-After. Fail open or closed: “your call — defend it.”",
     "What does a rejected client get, and what if the limiter itself fails?", "A 429, with a Retry-After header. What else it carries is up to you. Fail open or fail closed: your call. Defend it.",
     "I'll come back to both. The response should let a client plan. And the failure mode is a decision per limit, not a library default.")
clar(5, "Bursts? One region or global?", "Customers burst legitimately. Most limits are per region; some contracts are global.",
     "Do customers burst, and is a limit per region or worldwide?", "They burst legitimately; a hard per-second cap would break them. Most limits are per region, and some contracts say global.",
     "Bursts mean the algorithm needs a burst knob separate from the rate. And global contracts mean regions have to talk, which can't be on the request path.")

S(plain("Requirements · functional", "Four things the limiter must do", cards(
  ("", "FR1 · Decide", "For every request, allow or reject by customer and endpoint, before the backend sees it."),
  ("grn", "FR2 · Tell", "Every response says limit, remaining and reset; a 429 adds Retry-After and a decision ID."),
  ("amb", "FR3 · Configure", "Limits, tiers, bursts, schedules, scope and mode; changes staged, live in seconds."),
  ("red", "FR4 · Explain", "For any 429: the policy version, the server, the lease, the global count."))), [
 "C: Four functional requirements.", P,
 "C: One, decide: for every request, allow or reject by customer and endpoint, before the backend sees it.", P,
 "C: Two, tell: every response says the limit, what remains and when it resets. A 429 adds Retry-After and a decision ID.", P,
 "C: Three, configure: limits, tiers, bursts, schedules, scope and mode. Changes are staged, and live within seconds.", P,
 "C: Four, explain: for any 429, what produced it. Usually forgotten, and the first thing a big customer asks for."])

S(plain("Requirements · non-functional", "The numbers, and what each is for", '<p class="chips">all initial targets, not measurements</p><div class="tiles" style="--n:4">'
  '<div class="tile blue"><b>≤ 1 ms</b><span>added at p99, at 3 M requests/s</span></div>'
  '<div class="tile red"><b>99.99 %</b><span>API availability: the limiter never lowers it</span></div>'
  '<div class="tile"><b>≤ 5 %</b><span>over the limit per minute; exact keys never</span></div>'
  '<div class="tile"><b>≤ 10 s</b><span>a policy change everywhere</span></div></div>' +
  line("False limits, a customer under its limit rejected: under 0.1 % of its requests.", "a")), [
 "C: The numbers, and they are initial targets.", P,
 "C: At most one millisecond added at p99, at three million requests a second.", P,
 "C: The API's availability is four nines, and the limiter must never be the reason it drops.", P,
 "C: Accuracy: at most five percent over the limit in any minute for ordinary keys, and never over for the few keys that must be exact, like login attempts.", P,
 "C: A policy change reaches every server within ten seconds.", P,
 "C: And false limits, a customer under its limit being rejected, stay under a tenth of a percent of its requests."])

S(plain("Requirements · properties", "What must never happen, and what must eventually happen", cards(
  ("red", pid("S1"), "Never more than 5 % over the limit in a minute; exact keys never over."),
  ("red", pid("S2"), "A limiter failure never fails a request the limit would admit."),
  ("red", pid("S3"), "A customer under its limit is almost never rejected: under 0.1 %."),
  ("grn", pid("L1"), "A policy change is enforced everywhere within 10 s."),
  ("grn", pid("L2"), "Every decision within 1 ms at p99."), cols=3)), [
 "C: As properties, so every fix can say which one it protects. Safety first.", P,
 f"V: {ps('S1')}: never more than five percent over the limit in a minute, and the exact keys never over.", P,
 f"V: {ps('S2')}: a failure of the limiter never fails a request that the limit would have admitted.", P,
 f"V: {ps('S3')}: a customer under its limit is almost never rejected.", P,
 f"C: Liveness. {ps('L1')}: a policy change is enforced everywhere within ten seconds.", P,
 f"C: {ps('L2')}: every decision within a millisecond. Notice the tension: the first property wants a shared count, the last one forbids waiting for it."])

S(plain("Requirements · scope", "In, and out on purpose", cards(
  ("grn", "In scope", "Per-customer, per-endpoint quotas; enforcement across the fleet and regions; the client contract; policies with staged rollout; decision observability."),
  ("red", "Out, on purpose", "DDoS at the network edge. Billing and metering. Abuse detection. Load shedding by criticality. Authentication.")) +
  line("Billing reads the request logs, exactly, later. The limiter is allowed to be five percent wrong; an invoice is not.", "")), [
 P, "C: In scope: quotas per customer and endpoint, enforced across the fleet and across regions, the contract with clients, policies with a staged rollout, and observability of every decision.", P,
 "C: Out, on purpose: DDoS protection at the network edge, a different layer. Billing and metering. Abuse detection. Load shedding by criticality. And authentication.", P,
 "C: One I'd say aloud: billing. Metering reads the request logs, exactly, later. The limiter may be five percent wrong; an invoice may not. Mixing them forces exactness onto the hot path."])

stage("C4 level 1 · system context", "The limiter in its context, before any boxes inside it", "c4-context", [
 "C: Before any boxes inside it, the system in its context. I draw this first, in every round.", P,
 "C: API clients: customers' apps and batch jobs, calling over HTTPS. All of the traffic.", P,
 "C: In the middle, the rate limiting system, one box for now. It runs inside the API tier.", P,
 "C: Behind it, the backend services. They only ever see admitted requests, over gRPC.", P,
 "C: The account team sets limits, and asks why a customer was limited.", P,
 "C: And usage metering reads the request logs as a Kafka topic, asynchronously. It never reads the limiter's counts. Nothing on the request path waits for it."],
 cap="C4 system context: who calls, who is protected, who sets the limits, and the metering kept apart")

key("The core", "The core is three things: a <em>decision in memory</em> from a token bucket; <em>leases of the global budget</em> that follow demand; and a <em>failure mode chosen per limit</em>.", [
 "V: The core is three things. A decision made in memory, from a token bucket. Leases of the global budget that follow demand. And a failure mode chosen per limit.", "[pause: 0.8]",
 "N: Notice the candidate separated the limiter from billing, fixed the scale and named the properties before any internals. That is the scoping signal."])
