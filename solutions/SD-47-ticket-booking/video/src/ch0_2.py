from dsl import *

# ───────────────────────── 0 · cold open ─────────────────────────
chapter(0, "Cold open", -1, "Design ticket booking for a stadium", [
 "C: A seat looks like a row with a boolean. Available, or taken. Anyone can write that in an afternoon. This question is not testing the boolean. It is testing what happens around it: a million people reaching it in the same second, a human who needs three minutes to pay, and a payment provider that sometimes does not answer."])

qs("Interviewer · the prompt", "“Design ticket booking for a stadium: fifty thousand seats, and a million people trying to buy them the moment sales open.”", [
 "I: Design ticket booking for a stadium. Fifty thousand seats, and a million people trying to buy them the moment sales open.", "[pause: 1.5]"])

S(dia("Why it is harder than it looks", "Twenty fans for every seat", "load-funnel", chip=chips("1,000,000 at the door", "50,000 seats", "2 % get a ticket")), [
 "C: Here is the hook. Fifty thousand seats at about two and a half a purchase is twenty thousand orders. Twenty thousand winners out of a million fans: two percent. Ninety-eight percent of the people who show up leave without a ticket, whatever we build.",
 "C: The picture shows the load at each layer, which I derive in the estimates: it shrinks from a hundred thousand polls a second at the door to a few hundred writes at the database. So this is mostly a system for saying no, quickly and fairly. The cheap, honest no is a first-class feature. A design that only works well for the two percent has failed the other ninety-eight."], cls="dia")

S(plain("Before the design", "What this question grades", table(["Axis", "Weak signal", "Strong signal"], [
  ["<b>Requirements</b>", "Starts drawing. Never asks what fair means", "Asks about oversell, seats, checkout time, fairness, payment, freshness; cuts scope aloud"],
  ["<b>Correctness</b>", "Check availability, then insert a booking", "One atomic claim, a third state, expiry that needs no job, an unknown payment state"],
  ["<b>Trade-offs</b>", "Names a product or a distributed lock", "Options, each with the failure that rules it out; says what the pick gives up"],
  ["<b>Depth</b>", "A queue in front, and stops", "Admission rate from first principles, a controller driven by shop health, why the poll is cacheable"],
  ["<b>Operations</b>", "Watches CPU", "Age of the oldest expired hold, seats frozen by unknown payments, a load test, a plan for the failure day"]], "bt sm sig") +
  grade("Two ways to be wrong run through this question: a seat sold twice, and a seat nobody can ever buy. Keep both in view.")), [
 "N: Five axes. The weak signal is always the same shape: a clean claim on a seat, and nothing about the million, the payment, or the day it fails.",
 "C: I'll keep two failures in mind the whole way. A seat sold twice, and a seat stuck so nobody can buy it. Most designs defend the first and forget the second."])

key("The thesis", "This is not a booking system, it is a <em>rejection</em> system. Convert a <em>stampede</em> into a <em>stream</em>, and give every seat one place where its state lives and one atomic way to change it.", [
 "V: This is not a booking system. It is a rejection system. Fifty thousand seats cannot be shared with a million people, so the design converts a stampede into a stream. Every seat has exactly one place where its state lives, and exactly one atomic way to change it.", "[pause: 1.0]",
 "C: Concretely: a waiting room at the edge that admits people at a rate the shop can serve. A seat with three states, not two. A claim that is one statement, not two. And a payment path that treats silence as a state of its own."])

S(plain("The order I will follow", "Scope, numbers, theory, a simple design, then I break it",
  '<div class="ribbon" style="margin-top:14pt">' + "".join(f"<span>{x}</span>" for x in STAGES) + '</div>' +
  '<div class="cards c3" style="margin-top:18pt"><div class="cd"><h3>First</h3><p>Requirements and scope. Numbers. A short theory chapter.</p></div>'
  '<div class="cd grn"><h3>Then</h3><p>API and data. A high-level design in three versions, each answering the one before.</p></div>'
  '<div class="cd red"><h3>Most of the time</h3><p>Eight challenges that break the design. A build cost. A recap.</p></div></div>'), [
 "C: The order I'll follow. Requirements and scope, then numbers, then a short theory chapter the design can lean on. Then the A-P-I and data, and a high-level design in three versions, each answering the objection to the one before.",
 "C: Then the part I care about most: eight challenges that break the design, where each fix creates the next question. A build cost, because someone has to own this. And a recap."])

# ───────────────────────── 1 · requirements ─────────────────────────
chapter(1, "Requirements and scope", 0, "Ask first. Cut on purpose. Put numbers on it.", [
 "C: Before I draw anything I want to ask six questions. Each answer will change the design."])

def clar(n, q, a, say):
    S(f'<div class="who">Clarifying question {n} of 6</div><div class="qq">{q}</div><div class="ans">{a}</div>', say, cls="qs")

clar(1, "Can we ever oversell?", "Never. Two people must not hold tickets for the same seat.", [
 "C: Can we ever oversell?",
 "I: Never. Two people must not hold tickets for the same seat.",
 "C: Then every seat has exactly one place where its state lives, and changing it has to be atomic. If the answer had been a little is fine, I could use an eventually consistent counter and skip all of that."])
clar(2, "Do users pick specific seats, or ask for the best available?", "Specific seats, from a map.", [
 "C: Do fans pick specific seats, or ask for best available?",
 "I: Specific seats, from a map.",
 "C: That makes each seat a row of its own, and contention per seat, not on one counter. With best available the server chooses, and could avoid collisions entirely. Here two fans can aim at the same seat, so I must resolve it."])
clar(3, "How long does checkout take?", "Users need about three minutes to enter payment details.", [
 "C: How long does checkout take?",
 "I: Users need about three minutes to enter payment details.",
 "C: A human typing a card number. I cannot keep a database transaction open for minutes: it would pin a connection and a row lock the whole time. So the reservation has to be data, a row with an expiry, and not a lock."])
clar(4, "What does fair mean, and who decided?", "You tell me. First-come is expected, but a queue or a lottery is acceptable if you argue for it.", [
 "C: What does fair mean here, and who decided?",
 "I: You tell me. First-come is expected, but a queue or a lottery is acceptable if you argue for it.",
 "C: Then it is a product decision, and I will surface it to the promoter and not quietly assume one. I'll bring it back in challenge five."])
clar(5, "How does payment behave?", "An external provider. Two to ten seconds, and it can time out ambiguously.", [
 "C: How does the payment provider behave?",
 "I: An external provider. Two to ten seconds, and it can time out ambiguously.",
 "C: Ambiguously means a timeout is not a decline. The customer may have been charged. So the outcome of a payment can be unknown, and seats must not be released while it is. That one answer produces a whole state in challenge three."])
clar(6, "How fresh must the seat map be?", "Within a couple of seconds.", [
 "C: How fresh must the seat map be?",
 "I: Within a couple of seconds.",
 "C: Good. If it had to be exact, every fan would need a live read of the database. A couple of seconds stale means I can build a snapshot once a second and serve it from cache to everyone."])

S(plain("Requirements · functional", "Five things the system must do", '<div class="cards c3">'
  '<div class="cd"><h3>FR1 · Join</h3><p>Enter the sale: a lobby before it opens, a place in line after.</p></div>'
  '<div class="cd"><h3>FR2 · Browse</h3><p>See a seat map that is fresh to within a couple of seconds.</p></div>'
  '<div class="cd amb"><h3>FR3 · Hold</h3><p>Hold specific seats for a limited time, atomically, never twice.</p></div>'
  '<div class="cd"><h3>FR4 · Pay</h3><p>Pay once, get tickets once, whatever the provider does.</p></div>'
  '<div class="cd grn"><h3>FR5 · Release</h3><p>Seats come back on expiry or failure. The promoter can add inventory.</p></div></div>'), [
 "C: Functionally, five things. One, join the sale: a lobby before it opens and a place in line after. Two, browse a seat map that is fresh to within a couple of seconds. Three, hold specific seats for a limited time, atomically, never twice.",
 "C: Four, pay once and get tickets once, whatever the provider does. Five, release: seats come back on expiry or failure, and the promoter can add inventory. Each of these gets a numbered flow later."])

S(plain("Requirements · non-functional", "The numbers, and what each is for", '<p class="chips">all initial targets, not measurements</p><div class="tiles" style="--n:4">'
  '<div class="tile"><b>0</b><span>oversell: an invariant, not a rate</span></div>'
  '<div class="tile blue"><b>&lt; 300 ms</b><span>hold request, p99</span></div>'
  '<div class="tile blue"><b>≈ 2 s</b><span>seat map staleness at most</span></div>'
  '<div class="tile"><b>&lt; 30 s</b><span>oldest expired hold still unreleased</span></div></div>'), [
 "C: The numbers. They are initial targets, and I'll say so once for this chapter: none is a measurement.",
 "C: Zero oversell. That is an invariant, not a rate. A hold answers in under three hundred milliseconds at the ninety-ninth percentile. The seat map is stale by about two seconds at most. And no expired hold goes unreleased for more than thirty seconds, so no seat sits in limbo. Plus one that is not a number: the sale-opening minute must not fall over."])

S(plain("Requirements · scope", "In scope, out of scope", chips("lobby and queue", "seat map", "holds", "checkout", "release") +
  '<div class="scope2"><div class="in"><h3>In scope</h3><ul><li>A lobby and a line in front of the sale</li><li>A seat map and holds on specific seats</li><li>Checkout with one external payment provider</li><li>Expiry, release, and the promoter adding seats</li><li>Bot controls, in the first version</li></ul></div>'
  '<div class="out"><h3>Out of scope, on purpose</h3><ul><li>Event search and discovery</li><li>Pricing and dynamic pricing</li><li>The resale marketplace</li><li>The refunds interface</li><li>The mobile app itself</li></ul></div></div>'), [
 "C: In scope: a lobby and a line in front of the sale, the seat map, holds on specific seats, checkout with one external payment provider, expiry and release, the promoter adding seats, and bot controls from the first version.",
 "C: Out of scope, on purpose. Event search and discovery. Pricing and dynamic pricing. The resale marketplace. The refunds interface. And the mobile app itself. Happy to pull any of these in, but I will spend the time on the contention path."])

key("The core", "The core is four things: an atomic <em>claim</em> on a three-state seat, a hold with <em>two expiry paths</em>, a <em>waiting room</em> at the edge, and a payment path that treats <em>unknown</em> as a state.", [
 "V: The core is four things. An atomic claim on a three-state seat. A hold with two expiry paths. A waiting room that sheds load at the edge. And a payment path that treats unknown as a state.", "[pause: 0.8]",
 "N: Notice what the candidate did in six minutes. They asked what fair means and who owns it, they cut five things out loud, and every answer changed a box on the board. That is the framing signal."])

# ───────────────────────── 2 · estimates ─────────────────────────
chapter(2, "Estimates", 1, "Every number is arithmetic, with a label. Each one changes a decision.", [
 "C: Now the numbers. Every one is arithmetic from the inputs and carries a label: given, illustrative, derived or an initial target. Each has to change a decision, or I drop it."])

S(plain("Estimates · 1 of 9 · who wins", "About two percent of fans get a ticket", table(["Quantity", "Arithmetic", "Label"], [
  ["Orders", "50,000 seats ÷ 2.5 per order = <b>20,000 orders</b>", "derived"],
  ["Share who succeed", "20,000 ÷ 1,000,000 = <b>2 %</b>", "derived"]], "bt") +
  line("Mostly a rejection system. Tell the 98 % early and cheaply.", "a")), [
 "C: First number. Fifty thousand seats divided by two and a half per order is twenty thousand orders. Twenty thousand out of a million is two percent. This is the number that reframes the design as a rejection system.",
 "C: Decision: the no path gets as much design as the yes path. Losers must not reach the database to learn they lost. They wait in a line that costs almost nothing per person, and we tell them early."])

S(plain("Estimates · 2 of 9 · without a queue", "What the database would see", table(["Quantity", "Arithmetic", "Label"], [
  ["Attempts", "1,000,000 fans × 2 clicks = 2,000,000", "illustrative"],
  ["Rate", "2,000,000 ÷ 60 s = <b>33,000 contended writes / s</b> on 50,000 rows", "illustrative"],
  ["With a line at R", "~33 admissions / s × 1.5 = <b>~50 holds / s</b>: 600 times less", "derived"]], "bt") +
  line("Each write waits for a row lock while holding a connection. The pool empties in milliseconds.", "r")), [
 "C: Second number. Suppose everyone could reach the inventory database directly. A million fans, two clicks each in the first minute, is two million attempts over sixty seconds: about thirty-three thousand writes a second, all aimed at the same fifty thousand rows, and really at the best few thousand seats.",
 "C: That is not big, it is fatal. Each write waits for a row lock while holding a connection, and there are only a few hundred connections. The pool empties in milliseconds. Decision: a waiting room that admits fans at a rate I choose. At about thirty-three a second, the database sees roughly fifty holds a second, six hundred times less."])

S(plain("Estimates · 3 of 9 · arrivals", "Joining must be one in-memory step", table(["Quantity", "Arithmetic", "Label"], [
  ["Average join rate", "1,000,000 ÷ 60 s = <b>16,700 / s</b>", "illustrative"],
  ["First seconds", "× 3 ≈ <b>50,000 / s</b>", "illustrative"],
  ["With a 30-minute lobby", "1,000,000 ÷ 1,800 s = <b>556 / s</b>", "derived"]], "bt") +
  line("A join is never a database row. A lobby flattens the spike at T zero.", "a")), [
 "C: Arrivals. A million joins in the first minute is seventeen thousand a second on average, and about three times that in the first seconds: fifty thousand a second. So a join is one in-memory operation, never a database insert.",
 "C: And it argues for a lobby. If the waiting room opens thirty minutes early, the same million joins arrive over eighteen hundred seconds: about five hundred and fifty a second. The sale opening itself then carries no join spike at all."])

S(plain("Estimates · 4 of 9 · polling", "A hundred thousand polls a second, if the answer differs per fan", table(["Quantity", "Arithmetic", "Label"], [
  ["Poll rate", "1,000,000 ÷ 10 s = <b>100,000 / s</b>", "illustrative"],
  ["Same answer for all", "one cached body, 1 s lifetime, ~200 edge locations → <b>~200 / s</b> at the origin", "illustrative"]], "bt") +
  line("Instead of where am I, ask how far has the line moved. One number for everyone.", "a")), [
 "C: Polling. A million waiting fans each asking where am I every ten seconds is a hundred thousand requests a second for as long as the line exists. Too much for my origin, so the answer must be identical for every fan and cacheable at the edge.",
 "C: The trick: not where am I, which differs per fan, but how far has the line moved, one number per event. Each fan computes their own position locally from a number inside their signed token. With a one-second lifetime and about two hundred edge locations, the origin sees two hundred requests a second instead of a hundred thousand."])

S(plain("Estimates · 5 of 9 · admission rate", "Sized by checkout capacity, not by demand", table(["Quantity", "Arithmetic", "Label"], [
  ["Shoppers inside", "10,000 at once: a comfortable load for one event", "initial target"],
  ["Time inside", "~5 minutes: pick, type a card, wait", "illustrative"],
  ["Admission rate R", "Little's law: 10,000 ÷ 5 min = <b>2,000 / min ≈ 33 / s</b>", "derived"],
  ["Time to sell out", "20,000 ÷ 0.7 conversion = 28,600 admissions ÷ 2,000 / min ≈ <b>14 min</b>", "derived"]], "bt") +
  line("Demand is a million. Capacity is ten thousand at a time.", "a")), [
 "C: Admission rate. Little's law: items in a system equal the arrival rate times the time each spends in it. The shop is the system. I decide ten thousand shoppers is comfortable. A shopper spends about five minutes inside. So the arrival rate that keeps ten thousand inside is ten thousand over five minutes: two thousand a minute, about thirty-three a second.",
 "C: At seventy percent conversion, twenty thousand orders need about twenty-eight thousand six hundred admissions, which at two thousand a minute is about fourteen minutes. So a fan at position four hundred thousand can be told honestly that they are unlikely to get in. Decision: R is a dial sized by the shop, and the line shows an honest estimate."])

S(plain("Estimates · 6 of 9 · the seat map", "Ten thousand shoppers refreshing a bitmap", table(["Quantity", "Arithmetic", "Label"], [
  ["Reads", "10,000 shoppers ÷ 2 s = <b>5,000 / s</b>", "derived"],
  ["Body", "50,000 bits ÷ 8 = <b>6.25 KB</b>", "derived"],
  ["Bandwidth", "5,000 × 6.25 KB ≈ 31 MB/s; as 304s (~300 B) ≈ <b>1.5 MB/s</b>", "derived"]], "bt") +
  line("One bit per seat, served by version, never read from the claims database.", "a")), [
 "C: The seat map. Ten thousand shoppers refreshing every two seconds is five thousand reads a second. One bit per seat: fifty thousand bits is six and a quarter kilobytes. At five thousand a second that is thirty-one megabytes a second as full bodies, but if clients send the version they have and get a not-modified answer when nothing changed, about one and a half.",
 "C: Decision: the map is a bitmap served by version from a cache, and it never competes with the claims for the same rows."])

S(plain("Estimates · 7 of 9 · writes", "Holds and payments are small after the line", table(["Quantity", "Arithmetic", "Label"], [
  ["Hold writes", "33 / s × 1.5 attempts ≈ <b>50 / s</b>; bursts × 10 = <b>500 / s</b>", "illustrative"],
  ["Payments", "20,000 orders ÷ 900 s ≈ 25 / s; × up to 10 s = <b>250 in flight</b> (Little)", "illustrative"],
  ["Storage", "~120 GB seats + ~300 GB orders ≈ <b>420 GB a year</b>", "illustrative"]], "bt") +
  line("One primary per event is enough. Storage is not the problem.", "a")), [
 "C: Writes after the line. Each admitted fan tries about one and a half holds: fifty a second, with bursts ten times that, five hundred. One PostgreSQL primary does thousands of short transactions a second, so even the burst fits with room.",
 "C: Payments: twenty thousand orders over fifteen minutes is about twenty-five a second, each taking up to ten seconds, so about two hundred and fifty requests in flight. That means checkout must be asynchronous, with a bounded pool to the provider. And storage: about four hundred and twenty gigabytes a year. I say it aloud to show I know it is not the problem."])

S(dia("Estimates · 8 of 9 · the hold budget", "Where three hundred milliseconds go", "budget", chip=chips("initial target")), [
 "C: The hold request has a budget. Twenty milliseconds at the gateway, ten for the token and limits, forty for the lock and the claim, ten for the outbox write, twenty to return: a hundred used, two hundred spare, against three hundred. The spare is what the controller spends when a burst arrives. If hold latency eats it, that is the signal to cut the admission rate. Decision: latency is the dial's feedback."], cls="dia")

S(plain("Estimates · 9 of 9 · the headline", "After the line, a few hundred transactions a second", '<div class="cards c3">'
  '<div class="cd red"><h3>Before the line</h3><p>A million fans. A hundred thousand polls a second. Fifty thousand joins a second.</p></div>'
  '<div class="cd grn"><h3>After the line</h3><p>Ten thousand shoppers. About fifty holds a second, five hundred in a burst. Two hundred and fifty payments in flight.</p></div>'
  '<div class="cd"><h3>So</h3><p>This is not a big-data problem. All the scale is in the waiting room and the read path.</p></div></div>' +
  grade("A candidate who computes ten numbers and draws no conclusion from any of them has lost the phase. The conclusion is what is scored.")), [
 "C: The headline. This is not a big-data problem. After the queue, the write path is a few hundred transactions a second. All the scale is in the waiting room and the read path, so that is where I spend the design budget.",
 "N: Each number above ended in a decision. That is what the interviewer is writing down.",
 "C: That is the numbers. Next, theory."])
