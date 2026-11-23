from dsl import *

# ───────────────────────── 4 · API and entities ─────────────────────────
chapter(4, "API and entities", 3, "The contract first. It forces the semantics into the open.", [
 "C: The A-P-I before the boxes. It is the contract, and it shows whether I have thought about failure. Every call carries a tag: which requirement it serves, and which entity it reads or writes. Every call that changes something takes an idempotency key."])

def wire(l, r): return f'<div class="cols2"><pre class="wire">&nbsp;\n{l}</pre><pre class="wire">&nbsp;\n{r}</pre></div>'

S(plain("API · the line", "Join, and the one cached answer", tr(("fr", "serves FR1"), ("api", "join · state"), ("ent", "writes QueueEntry · reads Pointer"), ("nfr", "state: same bytes for all")) +
  wire('<span class="cm">// join: one in-memory step</span>\nPOST /events/{id}/queue\n -> { queueToken: "…signed…",\n      serverTime: 1792130400 }\n\n<span class="cm">// the token says: user U is in line\n// for event E, lobby or number N</span>',
       '<span class="cm">// the poll: cached at the edge, 1 s</span>\nGET /events/{id}/queue/state\n -> { admittedUpTo: 41200,\n      ratePerMin: 2000,\n      soldOut: false }\n\n<span class="cm">// no user identity: every fan gets\n// the same bytes, so a CDN can hold\n// it. The fan computes their own\n// position from the token</span>')), [
 "C: The line. Join is one call that returns a signed queue token and the server's clock, so the countdown is the same for everyone. The token says: this user is in line for this event, either in the lobby or at number N. A join is one in-memory step, never a database row.",
 "C: The poll returns three fields: how far the line has moved, the current admission rate, and whether it is sold out. There is no user identity in it. Every fan gets the same bytes, which is exactly why a C-D-N can hold it. The fan computes their own position from the number in their token."])

S(plain("API · admission", "Exchange a place for a ten-minute pass", tr(("fr", "serves FR1"), ("api", "admit"), ("ent", "writes Admission"), ("nfr", "first admission wins")) +
  wire('<span class="cm">// when admittedUpTo >= my number</span>\nPOST /events/{id}/admit { queueToken }\n -> { admissionToken: "…JWT…" }\n\n<span class="cm">// asking again returns the SAME\n// token, never a fresh ten minutes</span>',
       '<span class="cm">// the admission token, decoded</span>\n{ sub: "user-48213",\n  evt: "evt-7731",\n  scope: "shop",\n  exp: iat + 600,   <span class="cm">// 10 min</span>\n  jti: "adm-5f1c2b" }\n\n<span class="cm">// checked at the gateway: one\n// signature check, no lookup</span>')), [
 "C: Admission. When the pointer has reached the fan's number, they exchange the queue token for an admission token, a signed pass valid ten minutes for this event. The server checks the condition, and the number is inside a token we signed, so a client cannot admit itself early.",
 "C: Asking again returns the same token, never a fresh ten minutes. Otherwise a fan could refresh their window forever and occupy a shopping slot. The gateway checks the signature on every shop call: one check, no lookup, no network. And the token has an identifier, so a detected bot can be revoked."])

S(plain("API · the map", "An immutable layout and a versioned bitmap", tr(("fr", "serves FR2"), ("api", "layout · availability"), ("ent", "reads Layout · Availability"), ("nfr", "304 when unchanged")) +
  wire('<span class="cm">// immutable: CDN, cached a year</span>\nGET /events/{id}/layout/v7\n -> venue drawing + seat ids\n\n<span class="cm">// the live part: one bit per seat</span>\nGET /events/{id}/availability?v=812',
       '<span class="cm">// changed:</span>\n200  X-Map-Version: 815\n     6.25 KB bitmap\n\n<span class="cm">// nothing changed since v=812:</span>\n304  (no body, a few hundred bytes)\n\n<span class="cm">// admitted fans only; the claim is\n// the authority, the map a hint</span>')), [
 "C: The map. The layout is the venue drawing and the seat identifiers. It never changes during a sale, so it comes from the C-D-N under a versioned address and is cached for a year. The availability is the live part: one bit per seat, six and a quarter kilobytes. The client sends the version it has. If nothing changed, the answer is a not-modified with no body.",
 "C: Only admitted fans read it. And one point worth saying aloud: the map is a hint for the fan's eye. The claim is the authority."])

S(plain("API · holds and orders", "Hold: created or conflict. Order: accepted, then poll", tr(("fr", "serves FR3 · FR4"), ("api", "holds · orders"), ("ent", "writes Seat · Hold · Order"), ("nfr", "idempotency key on both")) +
  wire('<span class="cm">// FR3: the only contended write</span>\nPOST /events/{id}/holds\n  { seatIds: [101, 102] }\n -> 201 { holdId, expiresAt }\n -> 409 { bitmap: "…fresh…" }\n\n<span class="cm">// all seats or none; the 409\n// carries the fresh map</span>',
       '<span class="cm">// FR4: payment takes seconds, so 202</span>\nPOST /orders { holdId, paymentToken }\n -> 202 { orderId, status: "PENDING" }\n\nGET /orders/{orderId}\n -> PENDING | CONFIRMED | FAILED\n\nPOST /psp/webhooks\n<span class="cm">// signed; deduplicated by event id</span>')), [
 "C: Holds and orders. A hold takes a list of seats and answers two-oh-one with an identifier and an expiry, or four-oh-nine with a fresh bitmap. All the seats or none. The four-oh-nine carries the current map so the fan's next click lands on a free seat without an extra request.",
 "C: An order answers two-oh-two accepted, not two-hundred, because payment takes seconds. The fan polls for the result. And a webhook endpoint, signed by the provider and deduplicated by event identifier, is how we hear an outcome we might have missed. The idempotency key on both calls is what makes a double click harmless."])

S(dia("Data · conceptual model", "Entities and relationships, in Chen notation", "erd-chen"), [
 "C: The conceptual model. An event has seats. A seat is held by at most one hold at a time, and a hold may cover several seats. A hold becomes an order, one to one. An order has payment attempts, a weak entity: it only exists in the context of an order. An order issues tickets, and each ticket is for exactly one seat. Fans join an event through the line.",
 "C: One fact matters most. A seat has at most one live hold, and the seat row is the truth. The hold row is bookkeeping. That is what makes the claim in challenge one safe."], cls="dia")

S(dia("Data · physical model", "The hot database: seats, holds, the outbox", "erd-inventory"), [
 "C: Physically, the inventory database, the hot one. The seat table is keyed by event and seat, partitioned by event. The seat identifier is dense, zero to forty-nine thousand nine hundred ninety-nine, so seat eight hundred twelve is bit eight hundred twelve in the availability map. The state is one of four values. A partial index covers only held rows, so the sweeper's query reads a few thousand rows, not fifty thousand.",
 "C: The hold table carries the user, the seats, the expiry and the idempotency key, unique per user. And the outbox: a change to a seat and the event announcing it commit in one transaction, so they cannot disagree."], cls="dia")

S(dia("Data · physical model", "Orders live in a different database", "erd-orders"), [
 "C: The order database is separate, owned by the order service, because the inventory database is the hottest resource in the sale and I keep everything else off it. Orders carry the hold they came from, unique, so there is one order per hold, ever. Money is a decimal type. Each payment attempt carries the key we send to the provider.",
 "C: And tickets, with a unique constraint on event and seat. The state machine and the conditional claim should make a double sale impossible. This constraint is the independent check. Two guards are far less likely to fail together."], cls="dia")

S(dia("Data · the line's state", "One hash slot per event, in Redis", "redis-keys"), [
 "C: The line's state lives in Redis, not the database. Losing a second of queue state is survivable. Losing a seat is not. The curly braces around the event identifier in every key make Redis hash only that part, so every key of one event lands on the same node, and one script can touch all of them atomically. Different events land on different nodes, which is how many simultaneous sales spread out."], cls="dia")

S(dia("Data · the seat", "Three states, plus one the weak designs miss", "seat-states"), [
 "C: The seat's state machine. Available, claimed to held with a five-minute expiry. Held, when an order is placed, to payment-pending, which is frozen. Payment-pending to sold on an authorization. And back to available on a decline, or a definite failure.",
 "C: Payment-pending is the state weak designs miss. The expiry paths only touch held. A seat whose payment is in flight is frozen by design, and only the order service can release it, once the outcome is definite."], cls="dia")

# ───────────────────────── 5 · high-level design ─────────────────────────
chapter(5, "High-level design", 4, "Simple first. Each version answers the objection to the one before.", [
 "C: Three versions. Each is introduced by the objection it answers. The system stays on screen from here, and later pictures are views of it. Boxes never move."])

S(dia("High-level design · version 1 of 3", "The simplest thing that works", "base-v1", vtag="V1",
      chip=chips("one API", "one table", "read the seat, then write it")), [
 "C: Version one. Fans call a booking API. The API reads the seat row. If it is available, it writes the fan's name. One API, one table. For a small venue with a quiet sale this is enough, and saying so is part of the answer. No objection yet: it is the simplest thing that works."], cls="dia")

S(plain("V1 · the objection", "Two fans both read free, and there is no state for paying",
  '<pre class="trace"><span class="t">10:00:01.120  </span>Fan A reads seat 102: AVAILABLE\n<span class="t">10:00:01.121  </span>Fan B reads seat 102: AVAILABLE\n<span class="t">10:00:01.130  </span>Fan A writes: seat 102 is A\'s\n<span class="t">10:00:01.131  </span><span class="bad">Fan B writes: seat 102 is B\'s. A is overwritten, or both pay</span>\n<span class="t">10:03:00      </span>A is still typing a card. <span class="bad">There is no state for that, so a lock would have to be held for three minutes</span></pre>' +
  '<div class="hedge"><b class="t">Also</b>A million requests land straight on the table, and the map is read from the same rows.</div>', red=True), [
 "C: The objection. Two fans read the seat at the same moment and both see free. Both write. Either one overwrites the other, or both pay. And there is no state for a fan who is still typing a card, so the only way to protect their seat is a lock held for three minutes. A million requests land on that table, and the map reads from the same rows."])

S(dia("High-level design · version 2 of 3", "A third state, a conditional claim, and a separate order path", "base-v2", vtag="V2",
      chip=chips("conditional claim", "hold with an expiry", "order service", "payment provider")), [
 "C: Version two answers that. The seat gets a third state and an expiry, and the claim becomes one conditional update, the green arrow. Checkout moves to its own order service, the new box below. It freezes the seats, calls the payment provider, and only then sells. The two paths are separate because the provider is slow and sometimes silent, and the inventory database must never wait for it.",
 "C: The dashed line from the provider carries either an answer or silence. Version two is correct. It is not yet survivable."], cls="dia")

S(plain("V2 · the objection", "Correct, but a million fans still reach fifty thousand rows", '<div class="cards c2">'
  '<div class="cd red"><h3>The front is open</h3><p>Every fan can call the claim. The hottest seats take every click.</p></div>'
  '<div class="cd amb"><h3>The map competes</h3><p>Ten thousand shoppers reading the seat table lock against the claims.</p></div></div>' +
  line("The claim is right. What is missing is a way to keep the million away from it. That is version three.", "a")), [
 "C: The objection to version two. The claim is right, and checkout is right. But every fan can call the claim, so the hottest seats take every click. And the seat map is still read from the table that the claims lock. What is missing is a way to keep a million people away from fifty thousand rows."])

S(dia("High-level design · version 3 of 3", "An edge, a waiting room, a seat-map pipeline", "base-v3", vtag="V3",
      chip=chips("CDN and gateway", "waiting room", "event log", "seat map", "token check")), [
 "C: Version three. The gateway and C-D-N absorb the million, and check an admission token on every shop call. The waiting room holds the lobby, the pointer and the tokens. And a pipeline for the map: the database writes a change and an outbox row in one transaction, the event log carries it, a snapshot builder publishes at most one bitmap a second to the seat-map cache, and the edge serves it by version.",
 "C: This is the baseline. It stays on screen, and every later picture is a view of it."], cls="dia")

S(plain("V3 · what it leaves open", "The details are where it breaks", '<div class="cards c2">'
  '<div class="cd red"><h3>What V3 has</h3><p>An atomic claim, a hold with an expiry, a line in front, a map off the database, a payment path that expects silence.</p></div>'
  '<div class="cd red"><h3>What it has not been tested against</h3><p>Two fans on one seat. A fan who leaves. A late payment. A million at the door. Bots. A stale map. A promoter who changes the plan. A failure nobody sees.</p></div></div>' +
  line("Eight questions. Each fix creates the next. These are the challenges.", "r")), [
 "C: What version three leaves open. It has an atomic claim, a hold with an expiry, a line, a map off the database and a payment path that expects silence. It has not been tested against two fans on one seat, a fan who leaves, a late payment, a million at the door, bots, a stale map, a promoter who changes the plan, or a failure nobody sees. Those are the eight challenges, after the flows."])

def flow(n, fr, title, svg, tags, say):
    S(dia(f"High-level design · requirement {n} · {fr}", title, svg, trs=tr(*tags)), say, cls="dia")

flow(1, "join and admission", "FR1: from the door to a ten-minute pass", "flow-fr1",
     [("fr", "serves FR1"), ("api", "join · state · admit"), ("ent", "writes QueueEntry · Admission"), ("nfr", "one cached answer")], [
 "C: Requirement one, join. Step one: a fan requests the sale page and the join from the C-D-N. Step two: the gateway sends the join to the waiting room, which draws a random score, one in-memory step, and returns a signed queue token. Step three: after the sale opens, the fan polls the one cached answer, computes their position, and when the pointer reaches them, the admit call exchanges the queue token for a ten-minute admission token."])
flow(2, "browse", "FR2: the layout from the edge, the map by version", "flow-fr2",
     [("fr", "serves FR2"), ("api", "layout · availability"), ("ent", "reads Layout · Availability"), ("nfr", "304 when unchanged")], [
 "C: Requirement two, browse. Step one: the request reaches the edge. Step two: the layout comes from the C-D-N, immutable, and the availability comes from the seat-map cache by version, with a not-modified when nothing changed. Step three: the response goes back. The claims database is not touched."])
flow(3, "hold", "FR3: one conditional claim", "flow-fr3",
     [("fr", "serves FR3"), ("api", "holds"), ("ent", "writes Seat · Hold"), ("nfr", "p99 under 300 ms")], [
 "C: Requirement three, hold. One: the request arrives with an admission token and an idempotency key. Two: the gateway checks the token. Three: the booking API sends one conditional claim, all the seats or none. Four: the database answers won or lost. Five: the API answers two-oh-one with an expiry, or four-oh-nine with a fresh bitmap. Six: the response. The outbox row is written in the same transaction as the claim."])
flow(4, "pay and ticket", "FR4: freeze, authorize, sell on approval", "flow-fr4",
     [("fr", "serves FR4"), ("api", "orders · webhook"), ("ent", "writes Order · PaymentAttempt · Ticket"), ("nfr", "unknown is a state")], [
 "C: Requirement four, pay. One: the order reaches the order service. Two: it freezes the seats in the inventory database before it calls the provider. Three: it asks the provider to authorize. Four: the provider answers approved, or declined, or nothing. Five: silence becomes unknown, not failed, and the reconciler asks again. The seats are sold only on an approved authorization, and the money is captured last."])
flow(5, "expiry and release", "FR5: an expired hold comes back, and is announced", "flow-fr5",
     [("fr", "serves FR5"), ("api", "sweeper · outbox"), ("ent", "writes Seat · Outbox"), ("nfr", "oldest expired < 30 s")], [
 "C: Requirement five, release. One: the sweeper finds expired holds in small batches and returns the seats to available. Two: the same transaction writes an outbox row, and the event log carries it. Three: the released seat is announced, so the map shows it free, and a fan on the waitlist can be offered it. Nothing in this path is on a fan's critical path."])

S(dia("Design · C4 level 1", "The system in its context", "c4-context"), [
 "C: The C4 context. A million fans arrive through the C-D-N and the web application firewall, which absorb the crowd. The promoter and operations set the sale, the fairness policy and the seats. The payment provider is slow and sometimes silent. Email and push carry the tickets. Two outside dependencies decide the shape of the design: the payment provider, and the edge, where bots are stopped."], cls="dia")
S(dia("Design · C4 level 2", "The waiting room and the read path", "c4-containers-wait"), [
 "C: The containers on the waiting side. The waiting room does the join, the position and the admit, backed by a Redis queue store. The admission controller turns the rate dial every second from shop health. The seat-map service serves the bitmap, built by a snapshot cache from the seat events in Kafka. The gateway checks the admission token. Three separate paths: the queue, the read, and the write."], cls="dia")
S(dia("Design · C4 level 2", "The write path", "c4-containers-write"), [
 "C: The containers on the write side. The inventory service holds the atomic claim, over its PostgreSQL database with the outbox. The order service, with its own database, talks to the slow provider and must never hold inventory connections while it waits. A hold expirer releases expired holds. Kafka carries the events. The ticket constraint is the last line of defence against oversell."], cls="dia")
S(dia("Design · C4 level 3", "Inside the inventory service", "c4-component-inventory"), [
 "C: Level three, inside the inventory service. The hold interface takes the request with its idempotency key and limits. The claim engine runs the conditional update. The outbox writer shares its transaction. The freeze-and-sell component serves the order service. And the sweeper, with its skip-locked batches. Lazy expiry lives in the claim predicate; the sweeper only makes the map catch up."], cls="dia")
S(dia("Design · sequence · join", "From the lobby to the draw", "seq-lobby"), [
 "C: Join as a sequence. A fan enters the lobby before the sale opens. The waiting room draws a random score on the server, writes it to the lobby set with a no-overwrite flag, and returns a signed token. At the start moment, the phase flips. Fans in the lobby ask once for their number, with a jitter, and the answer is their rank by score. Late arrivals take the next number behind them."], cls="dia")
S(dia("Design · sequence · checkout", "The happy path through the order service", "seq-checkout"), [
 "C: Checkout, the happy path. The fan submits the order with a payment token and an idempotency key. The order service inserts the order, freezes the seats in the inventory database, and answers accepted at once. In the background it asks the provider to authorize with a ten-second timeout. On approval it sells the seats, writes the tickets and an outbox row in one local transaction, and capture happens later, off the fan's path."], cls="dia")
