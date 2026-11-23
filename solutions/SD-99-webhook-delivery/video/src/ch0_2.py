from dsl import *

# ───────────────────────── 0 · cold open ─────────────────────────
chapter(0, "Cold open", -1, "Tell twenty thousand systems we do not control what happened to their loans", [
 "C: A point-of-sale lender approves a loan at a merchant's counter. The merchant's till has to hear about it in seconds, their accounting system has to hear about the refund a month later, and the partner bank wants every payment, loan by loan. The first version of that is one line of code: a POST to the merchant's URL, inside the booking request. It fails the first time a merchant's server takes thirty seconds to answer."])

qs("Interviewer · the prompt", "“Merchants and partners subscribe to our loan and payment events. Design the platform that delivers them as webhooks.”", [
 "I: Merchants and partners subscribe to our loan and payment events: approved, booked, funded, refunded, paid. Design the platform that delivers them as webhooks.", "[pause: 1.5]"])

S(plain("Before the design", "What this question grades", table(["Axis", "Weak signal", "Strong signal"], [
  ["<b>Requirements</b>", "“Send a webhook”", "Asks who subscribes, ordering, the retry window, latency, and what a merchant does with the event"],
  ["<b>Correctness</b>", "A call inside the business transaction; promises exactly-once", "An outbox; at-least-once said out loud; event IDs and a sequence per loan"],
  ["<b>Trade-offs</b>", "One shared queue, a fixed retry count", "Isolation per endpoint; backoff with jitter; a disable policy; buy against build"],
  ["<b>Depth</b>", "“A queue with retries”", "What row is claimed, what the timer is, how a recovering endpoint is ramped"],
  ["<b>Operations</b>", "Uptime of the API", "Lag we own, success to healthy endpoints, SSRF and secrets owned, the contract versioned"]], "bt xs sig") +
  grade("The sentence that separates candidates: one bad endpoint must never spend another endpoint's capacity.")), [
 "N: Five axes. The weak answer is a queue with retries. The strong answer isolates every endpoint, says at-least-once and means it, and treats the payload as a public contract.",
 "C: One sentence I'll keep in front of everything: one bad endpoint must never spend another endpoint's capacity."])

key("The thesis", "We promise <em>at-least-once</em> and give every endpoint its <em>own failure budget</em>. Exactly-once is the <em>consumer's</em> job, and the <em>contract</em> that makes it possible is the product.", [
 "V: We promise at-least-once delivery, and we give every endpoint its own failure budget. Exactly-once is the consumer's job, and the contract that makes it possible is the product.", "[pause: 1.0]",
 "C: Concretely: an outbox, so no event exists without its commit. A delivery row per endpoint, so a slow endpoint queues in its own rows. Backoff with jitter and a slow ramp, so a recovering endpoint is not knocked over again. Signatures, an egress proxy and a versioned contract, so merchants can trust and keep parsing what we send."])

S(plain("The order I will follow", "Scope, numbers, theory, a simple design, then I break it",
  '<div class="ribbon" style="margin-top:14pt">' + "".join(f"<span>{x}</span>" for x in STAGES) + '</div>' +
  cards(("", "First", "Requirements and scope. Numbers from one scale line. A short theory chapter."),
        ("grn", "Then", "API and data. A design in three versions; a simpler alternative and where it stops."),
        ("red", "Most of the time", "Seven challenges that break it, carrying it to version six. A build cost with the team seams. A recap."), cols=3)), [
 "C: The order. Requirements, numbers from one scale line, and a short theory chapter. Then the A-P-I, the data, and a design in three versions, with a simpler alternative and the number where it stops being enough.",
 "C: Most of the time goes to seven challenges, each one carrying the design forward, to version six. Then the build cost, with the team seams and the contracts between them, and a recap."])

# ───────────────────────── 1 · requirements ─────────────────────────
chapter(1, "Requirements and scope", 0, "Ask first. Cut on purpose. Put numbers on it.", [
 "C: Before I draw anything, one scale line and six questions. Each answer changes the design."])

S(plain("Requirements · the scale line", "Sixty million events a month, and one morning that is thirty-four times busier",
  table(["", "Number", "Where it comes from"], [
   ["<b>Volume</b>", "60 M events a month → 180 M deliveries", "origination, funding and servicing events; about 3 subscriptions each"],
   ["<b>Over retention</b>", "≈ 216 M attempt rows; ≈ 120 GB of payloads", "30 days of attempts (1.2 per delivery); one payload per event"],
   ["<b>Peak, and its cause</b>", "800 events a second → 2,400 deliveries a second", "the bank's settlement file posts 480,000 payments in ten minutes"],
   ["<b>Endpoints</b>", "20,000; about 3 % failing at any moment", "merchant tills, accounting systems, the partner bank"]], "bt xs") +
  line("All illustrative; every later number starts here.", "g")), [
 "C: The scale line, said once.",
 "[+]", "C: Sixty million events a month, from origination, funding and servicing. Each matches about three subscriptions, so a hundred and eighty million deliveries a month. That's about seventy a second on average.",
 "[+]", "C: Over thirty days of retention: about two hundred and sixteen million attempt rows, at one point two attempts per delivery, and about a hundred and twenty gigabytes of payloads, one per event.",
 "[+]", "C: The peak has a cause. On the morning after a collection day, the bank's settlement file posts four hundred and eighty thousand payments in about ten minutes. That's eight hundred events a second, and two thousand four hundred deliveries a second: thirty-four times the average.",
 "[+]", "C: And twenty thousand endpoints, of which about three percent are failing at any moment: six hundred.",
 "[+]", "C: All illustrative. Every number from here starts from one of these rows."])

def clar(n, q, a, say):
    S(f'<div class="who">Clarifying question {n} of 6</div><div class="qq">{q}</div><div class="ans">{a}</div>', say, cls="qs")

clar(1, "Who subscribes, and what do they do with an event?", "Merchant tills and accounting systems, through self-service registration; the partner bank, by contract.", [
 "C: Who subscribes, and what do they do with an event?",
 "I: Merchant tills and accounting systems, which register their own URLs. And the partner bank, by contract.",
 "C: So a merchant may release goods on an approval event. That makes a forged event a fraud problem, not a nuisance. And self-service URLs mean the URL is untrusted input that my servers will call."])
clar(2, "Must events for one loan arrive in order?", "Not guaranteed across events. Merchants may fetch the loan's current state.", [
 "C: Must events for one loan arrive in order?",
 "I: We don't promise it. Merchants can always fetch the loan's current state.",
 "C: Good. Then I'll give them what they need to order it themselves, a sequence per loan, rather than promise something a retry will break."])
clar(3, "How fast, and for how long?", "First attempt within 5 s at p99 for a healthy endpoint. Retry for 72 hours.", [
 "C: How fast must the first attempt go, and how long do we keep trying?",
 "I: First attempt within five seconds at the ninety-ninth percentile, for a healthy endpoint. Retry for seventy-two hours.",
 "C: Seventy-two hours means a backlog of days has to live somewhere durable, not in memory."])
clar(4, "Is delivery exactly once?", "At least once. Say so in the contract.", [
 "C: Do we promise exactly once?",
 "I: At least once. Say it in the contract.",
 "C: Then the event I-D is part of the product: merchants de-duplicate by it."])
clar(5, "Payload size, and one region?", "About 2 KB. One region first.", [
 "C: Payload size, and how many regions?",
 "I: About two kilobytes. One region to start.",
 "C: Small payloads: storage is not the problem. I'll name the second region as an extension, not design for it now."])
clar(6, "Who owns the event schema?", "Producers own their events. Merchants must not break when producers change.", [
 "C: Who owns what goes inside an event?",
 "I: The producing teams own their events. Merchants must not break when those teams change things.",
 "C: Then the public contract cannot be the internal event. That will be a challenge on its own, and a team seam."])

S(plain("Requirements · functional", "Four things the platform does",
  table(["#", "Requirement", "Notes"], [
   ["FR1", "Register an endpoint and subscribe to event types", "URL verified; a signing secret shown once; a pinned API version"],
   ["FR2", "Emit an event atomically with the state change", "no event without a commit; none for a rollback"],
   ["FR3", "Deliver to every matching endpoint, signed, with retries", "72 h of retries; then dead, visibly"],
   ["FR4", "See every attempt, and redeliver or replay", "one delivery, or everything since a time, at a chosen rate"]], "bt sm")), [
 "C: Four functional requirements.",
 "[+]", "C: F-R-one: register an endpoint and subscribe it to event types. The URL is verified, a signing secret is shown once, and the endpoint is pinned to an A-P-I version.",
 "[+]", "C: F-R-two: emit an event atomically with the state change. No event without its commit, and none for a change that rolled back.",
 "[+]", "C: F-R-three: deliver to every matching endpoint, signed, with retries for seventy-two hours, and then dead, visibly.",
 "[+]", "C: F-R-four: see every attempt, and redeliver one delivery or replay everything since a time, at a rate the merchant chooses."])

S(plain("Requirements · non-functional", "The numbers the design must hold",
  table(["Requirement", "Target (initial)", "Why this number"], [
   ["Event loss after commit", "zero", "a lost approval stops a sale"],
   ["First attempt, healthy endpoint", "p99 under 5 s", "the till is waiting"],
   ["One endpoint's failure", "adds under 1 s to anyone else's p99", "isolation is the product"],
   ["Retry window", "72 h, then dead and visible", "a weekend outage at a merchant"],
   ["Ingest availability", "99.95 %", "producers must never block on us"],
   ["Calls to private addresses", "never", "SSRF into our own network"]], "bt sm")), [
 "C: The non-functional requirements, all initial targets.",
 "[+]", "C: Zero events lost after commit: a lost approval stops a sale.",
 "[+]", "C: The first attempt to a healthy endpoint within five seconds at p ninety-nine, because a till is waiting.",
 "[+]", "C: One endpoint's failure adds less than a second to anyone else's p ninety-nine. That's the isolation requirement, written as a number.",
 "[+]", "C: Seventy-two hours of retries, then dead and visible: long enough for a weekend outage at a merchant.",
 "[+]", "C: Ingest at ninety-nine point nine five percent, because producers must never block on us.",
 "[+]", "C: And never a call to a private address."])

S(plain("Requirements · scope", "In, and out on purpose", cards(
  ("grn", "In", "Outbox and relay, fan-out, delivery and retries, signing, egress control, the attempt log, replay, the public contract and its versions."),
  ("", "Out, named", "Partner-side SDKs, a schema design tool, webhooks we receive (SD-45), push to customers' phones (SD-12), a second region."))), [
 "C: In scope: the outbox and relay, fan-out, delivery with retries, signing, egress control, the attempt log, replay, and the public contract with its versions.",
 "C: Out, on purpose: partner-side S-D-Ks, a schema design tool, webhooks we receive from others, push notifications to customers' phones, and a second region, which I'll name as an extension."])

key("The core is three things", "A <em>durable event</em> before any delivery. <em>Isolation</em> per endpoint. And the <em>consumer contract</em>: IDs, sequence, signature, versions.", [
 "V: The core is three things. A durable event before any delivery. Isolation per endpoint. And the consumer contract: I-Ds, a sequence, a signature, and versions.", "[pause: 0.8]"])

S(dia("Requirements · C4 level 1", "The platform in its context", "c4-context"), [
 "C: The context.", "[+]", "C: Origination produces loan events.",
 "[+]", "C: The servicing system adds the payments and refunds.",
 "[+]", "C: The webhook platform sits in the middle.",
 "[+]", "C: It sends signed POSTs to twenty thousand merchant tills and accounting systems,",
 "[+]", "C: and loan-level events to the partner bank, over mutual T-L-S.",
 "[+]", "C: Merchant developers register endpoints and replay deliveries.",
 "[+]", "C: And a key service holds the signing secrets."], cls="dia")

# ───────────────────────── 2 · estimates ─────────────────────────
chapter(2, "Estimates", 1, "Every number starts from the scale line and changes something", [
 "C: Five numbers, each from the scale line, each with the decision it drives. All illustrative."])

S(plain("Estimate 1 · Little's law", "Six hundred calls in flight at the peak", table(["", ""], [
  ["From", "the peak: 2,400 deliveries a second"],
  ["Arithmetic", "2,400/s × 0.25 s mean answer time ≈ <b>600 calls in flight</b>"],
  ["Decision", "the fleet is small; capacity is not the risk. The slow endpoint is."]], "bt sm")), [
 "C: Estimate one, from the peak. Two thousand four hundred deliveries a second, times a quarter of a second for a typical answer: about six hundred calls in flight, by Little's law.",
 "C: That's a small fleet. Raw capacity is not the risk. What happens when one endpoint stops answering in a quarter of a second is."])

S(plain("Estimate 2 · one slow endpoint", "One till vendor at ten seconds needs twice the whole fleet", table(["", ""], [
  ["From", "the peak, and one till vendor with 5 % of deliveries"],
  ["Arithmetic", "2,400 × 5 % = 120/s; × 10 s timeout = <b>1,200 calls in flight</b>"],
  ["Decision", "a cap on in-flight calls per endpoint, and pools per tier: mandatory, not tuning"]], "bt sm")), [
 "C: Estimate two. One till vendor gets five percent of the deliveries: a hundred and twenty a second at the peak. If its server slows to our ten-second timeout, it needs twelve hundred calls in flight. Twice the whole fleet.",
 "C: So a cap on in-flight calls per endpoint, and separate pools per tier, are mandatory. Not tuning."])

S(plain("Estimate 3 · a two-day outage", "A quarter of a million deliveries waiting for one accounting system", table(["", ""], [
  ["From", "the average: 70 deliveries a second; an accounting system with 2 %"],
  ["Arithmetic", "1.4/s × 172,800 s ≈ <b>240,000 deliveries</b> × 2 KB ≈ 480 MB"],
  ["Decision", "the backlog lives in rows, not memory; recovery is ramped: at full speed it would be 1,700 × its normal load"]], "bt sm")), [
 "C: Estimate three. An accounting system that takes two percent of deliveries, one point four a second, is down for two days. That's two hundred and forty thousand deliveries, about half a gigabyte.",
 "C: The backlog lives in durable rows, not in memory. And when it comes back, sending all of it at our peak rate would be seventeen hundred times its normal load. So recovery has to be ramped."])

S(plain("Estimate 4 · storage", "Small, and partitioned by day", table(["What", "Arithmetic", "Decision"], [
  ["Attempt log", "180 M × 1.2 × 500 B ≈ <b>108 GB a month</b>", "daily partitions, dropped after 30 days"],
  ["Payloads", "60 M × 2 KB ≈ <b>120 GB a month</b>", "one copy per event, not per delivery: saves two thirds"],
  ["Delivery writes at the peak", "2,400 × about 4 writes ≈ <b>10,000 a second</b>", "four PostgreSQL shards by endpoint"]], "bt sm")), [
 "C: Estimate four, storage.",
 "[+]", "C: The attempt log: a hundred and eighty million deliveries, times one point two attempts, times five hundred bytes: about a hundred and eight gigabytes a month, in daily partitions we drop after thirty days.",
 "[+]", "C: Payloads: sixty million events times two kilobytes: a hundred and twenty gigabytes a month, stored once per event. Stored per delivery it would be three times that.",
 "[+]", "C: And delivery writes at the peak: about four writes per delivery, insert, claim, finish and the attempt, so about ten thousand a second. Four PostgreSQL shards by endpoint carry it with headroom."])

S(plain("Estimate 5 · the latency budget", "Five seconds, most of it ours to spend on purpose", table(["Step", "Budget (p99)"], [
  ["Outbox relay poll", "0.5 s"], ["Log and fan-out", "0.5 s"], ["Claim poll", "0.5 s"], ["Send and answer, healthy endpoint", "up to 2 s"], ["Spare", "1.5 s"]], "bt sm")), [
 "C: Estimate five, the latency budget for the first attempt. Half a second for the relay to poll, half a second through the log and fan-out, half a second for a dispatcher to claim, up to two seconds for a healthy endpoint to answer, and a second and a half spare.",
 "C: Polling intervals are the dial. If the five-second promise tightens, I shorten the polls before I add machinery."])
