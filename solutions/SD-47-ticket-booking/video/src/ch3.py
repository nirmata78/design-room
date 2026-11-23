from dsl import *
import dsl

def th(): dsl.SL[-1]["cls"] = (dsl.SL[-1]["cls"] + " theory").strip()

chapter(3, "Theory", 2, "What makes this problem hard, in words that outlive any product name", [
 "C: A short theory chapter before any design, so the design can lean on it. Six parts: what a booking system is and is not, the properties, the central tension, seven mechanisms, an options matrix, and the failure catalogue. Every slide here has a theory badge."]); th()

key("Theory · 1 of 6 · what it is", "A <em>fixed set</em> of individually identified seats, sold to <em>many more buyers</em>, with a <em>time-limited hold</em> between free and sold, so no seat is sold twice or stuck.", [
 "V: A ticket booking system sells a fixed set of individually identified seats to many more buyers than seats, with a time-limited hold between free and sold, so that no seat is ever sold twice and no seat is ever stuck in limbo.", "[pause: 1.0]",
 "C: Each clause carries weight. A fixed set: inventory does not grow by accident. Individually identified: contention is per seat. Many more buyers: twenty to one turns most requests into refusals. A time-limited hold: a third state, data and not a lock. And never twice, never stuck: safety and liveness."], cls="theory")

S(plain("Theory · 1 of 6 · what it is not", "Four things it is confused with", '<div class="cards c2">'
  '<div class="cd"><h3>Not a lock</h3><p>A lock belongs to a process and goes with it. A hold is data with an expiry: it survives a crashed server and needs no open transaction.</p></div>'
  '<div class="cd"><h3>Not a shopping cart</h3><p>A cart promises nothing. A hold promises nobody else can take this seat until a time you can read.</p></div>'
  '<div class="cd amb"><h3>Not an auction</h3><p>Price does not move with demand. The contest is who gets there first, not who pays most.</p></div>'
  '<div class="cd red"><h3>Not a queue, as a data structure</h3><p>The line is a product experience: a position, an estimated wait, an honest likely sold out. It is also a way to shed load.</p></div></div>'), [
 "C: Four neighbours. It is not a lock: a lock belongs to a process and goes with it, but a hold is data with an expiry, so it survives a crashed server. It is not a shopping cart: a cart promises nothing. It is not an auction: price does not move, the contest is who gets there first. And it is not a queue as a data structure: the line is a product experience with a position and an honest estimate, and it is also how we shed load."], cls="theory")

S(plain("Theory · 2 of 6 · the properties", "State safety and liveness separately",
  '<div class="prop safe"><div class="lbl">Safety · must never happen</div><p><b>S1</b> One seat belongs to two orders.<br><b>S2</b> Money is taken for seats we do not deliver, or seats are delivered with no money.</p></div>'
  '<div class="prop live"><div class="lbl">Liveness · must eventually happen</div><p><b>L1</b> Every seat is eventually sold or free again: nothing stuck in limbo.<br><b>L2</b> Every fan learns where they stand: a position, sold out, an order result.<br><b>L3</b> The sale-opening minute does not take the system down.</p></div>'
  '<div class="whyb"><b class="t">Why two safety properties</b>A seat can be wrong in two directions: sold twice, and paid for but not delivered. Most designs defend S1 and forget S2.</div>'), [
 "V: Safety: one seat never belongs to two orders, and money is never taken for seats we do not deliver. Liveness: every seat is eventually sold or free again, every fan eventually learns where they stand, and the sale-opening minute does not take the system down.", "[pause: 0.8]",
 "C: Two safety properties, because there are two ways to be wrong. S-one is the seat sold twice. S-two is the payment and the seat disagreeing. And three liveness properties, of which L-one is the one weak designs forget: a seat stuck in limbo is lost revenue. Every fix from here says which property it serves."], cls="theory")

S(dia("Theory · 3 of 6 · the central tension", "Demand is unbounded. Capacity is not.", "tension"), [
 "C: Here is the central tension. Demand is unbounded, supply and checkout capacity are not. The picture is a funnel. A million fans at the door, about ten thousand in the shop, about fifty holds a second, twenty thousand orders. Everything left of the shop is cheap and served at the edge. Everything right of it is expensive and protected.",
 "C: And the trade the problem forces is fairness against load. The fairest line, strict first-come, rewards bots and low latency and invites refresh storms. The cheapest line, random admission, needs a product decision. Not consistency against availability: the inventory is a single-writer set of rows, so there is no replica disagreement to resolve. Hold that picture. Challenges four and five live on it."], cls="dia theory")

def mech(n, name, protects, how, rules, costs, say, live=True):
    S(plain(f"Theory · 4 of 6 · mechanism {n} of 7", name,
        f'<div class="prop {"live" if live else "safe"}"><div class="lbl">Property it protects</div><p>{protects}</p></div>'
        f'<div class="prop"><div class="lbl">How it works</div><p>{how}</p></div>'
        f'<div class="prop safe"><div class="lbl">Failure it rules out</div><p>{rules}</p></div>'
        f'<div class="prop" style="border-left-color:#d18f1c"><div class="lbl" style="color:#a86a12">What it costs</div><p>{costs}</p></div>'), say, cls="theory")

mech(1, "A conditional claim in one statement", "S1: a seat is never sold twice.", "One statement whose condition is the availability check. Rows are locked in a stable order, and the change is all or nothing.",
     "A read-then-write race: two fans read free and both write.", "Contended rows on one primary. The loser gets a quick no.", [
 "C: Mechanism one, the conditional claim. It protects S-one. One statement whose condition is the availability check, with rows locked in a stable order, and all or nothing across the seats. It rules out the read-then-write race. It costs contended rows on a single primary, and the loser gets a quick no.",
 ], live=False)
mech(2, "A hold as data, with an expiry", "L1, and no lock held across a human.", "The seat row says held, carries a hold identifier and an expiry time. No transaction stays open.",
     "A database transaction open for minutes, pinning a connection and a row lock.", "A clock to trust, and a way to free seats nobody revisits.", [
 "C: Mechanism two, the hold as data. It protects liveness without holding a lock across a human. The seat row says held, with a hold identifier and an expiry time, and nothing stays open. It rules out a transaction open for minutes. It costs a clock to trust, and a way to free seats nobody comes back to."])
mech(3, "Two expiry paths", "L1: nothing stays stuck.", "Lazy: the claim treats an expired hold as free. A sweeper releases in small batches and announces the release, so the map catches up.",
     "Seats stuck forever, and correctness that depends on a background job.", "Staleness on the map while the sweeper is down.", [
 "C: Mechanism three, two expiry paths. It protects liveness. The claim itself treats an expired hold as free, so correctness never depends on a job. A sweeper releases in small batches and announces it, so the map catches up. It rules out seats stuck forever. It costs staleness on the map while the sweeper is down."])
mech(4, "Admission control at the edge", "L3: the sale-opening minute survives.", "A line, a pointer, and a rate chosen from shop health: increase slowly, cut fast.",
     "A stampede on fifty thousand rows.", "Most fans wait. A rate to tune, and an honest estimate to show.", [
 "C: Mechanism four, admission control. It protects the sale-opening minute. A line, a pointer, and a rate chosen from the shop's health: increase slowly, cut fast. It rules out a stampede on fifty thousand rows. It costs the fans' time, a rate to tune, and an honest estimate to show."])
mech(5, "Freeze, authorize then capture, unknown as a state", "S2: money and seats agree.", "Move held to payment-pending before calling the provider. Reserve money first, take it last. A silent provider means unknown, so ask again with the same key.",
     "A double charge, and a seat sold twice after a late approval.", "Seats frozen for up to ten minutes. A reconciler to run.", [
 "C: Mechanism five, freeze, authorize then capture, and unknown as a state. It protects S-two. Move the seats to payment-pending before the provider call. Reserve the money first and take it last. A silent provider means unknown, so ask again with the same idempotency key. It rules out a double charge and a seat sold twice after a late approval. It costs seats frozen for up to ten minutes, and a reconciler to run."], live=False)
mech(6, "Split reads: immutable layout, versioned bitmap, cached state", "L2 and L3: fans see the state, the database is not read.", "The layout is immutable on the edge. Availability is a versioned bitmap built from the event stream. The queue state is one cached answer for everyone.",
     "A live map read from the claims database.", "A click on a stale seat fails. It fails gracefully, with a fresh map.", [
 "C: Mechanism six, split reads. It protects the fan's view and the database. The layout is immutable on the edge. Availability is a versioned bitmap built from the event stream. The queue state is one cached answer for everyone. It rules out a live map read from the claims database. It costs a click on a stale seat, which fails gracefully with a fresh map."])
mech(7, "Random admission among early arrivals, and signed tokens", "Fairness, and a line nobody can forge.", "Draw a random score at join time for everyone present at the start. Late arrivals go first-come behind. Tokens are signed, short-lived and bound to the account.",
     "Bots winning the first millisecond. Forged or traded positions.", "A product rule that has to be stated on the page.", [
 "C: Mechanism seven, random admission and signed tokens. It protects fairness. Draw a random score at join time for everyone present at the start; late arrivals go first-come behind them. Tokens are signed, short-lived and bound to the account. It rules out bots winning the first millisecond, and forged positions. It costs a product rule that has to be stated on the page."])

S(plain("Theory · 5 of 6 · the options, part one", "Three ways that look cheap", table(["Approach", "Atomic?", "Survives a crash?", "Holds a connection through checkout?", "Fails when"], [
  ("rej", ["<b>a</b> · read the seat, then write it", "no", "yes", "no", "two readers both see free"]),
  ("rej", ["<b>b</b> · a row lock held through checkout", "yes", "<b>no</b>", "<b>yes, for minutes</b>", "the pool empties; the database falls over"]),
  ("rej", ["<b>c</b> · a distributed lock per seat, with a lease", "mostly", "partly", "no", "the lease expires mid-transaction; a second system to fail"])], "bt sm mx") +
  line("The first answers to reach for, and the first to rule out aloud.", "r")), [
 "C: The options for the central decision: how do I stop two fans taking one seat across a three-minute checkout. Three look cheap. A: read the seat then write it. Not atomic, so two readers both see free. B: a row lock held through checkout. Atomic, but a crashed server loses it, and it holds a connection for minutes: the pool empties and the database falls over.",
 "C: C: a distributed lock per seat with a lease. It sounds right. But it is a second system whose failures I now own, and a lease can expire in the middle of the transaction, leaving two fans who both believe they hold the seat."], cls="theory")

S(plain("Theory · 5 of 6 · the options, part two", "Three that work, and the pick", table(["Approach", "Atomic?", "Survives a crash?", "Holds a connection through checkout?", "Fails when"], [
  ("rej", ["<b>d</b> · serializable transactions", "yes", "yes", "no", "under contention most transactions abort and retry"]),
  ("rej", ["<b>e</b> · an optimistic version on each seat", "per seat", "yes", "no", "a multi-seat claim still ends in one conditional update"]),
  ("pick", ["<b>f</b> · one conditional update; the hold is data with an expiry", "<b>yes</b>", "<b>yes</b>", "<b>no</b>", "a slow fan loses the hold; hot seats contend on one primary"])], "bt sm mx") +
  '<div class="hedge"><b class="t">What the pick gives up</b>The hold can expire on a slow fan. The hottest seats are contended rows on one primary, which is why the waiting room exists. And there must be a sweeper.</div>'), [
 "C: Three that work. D: serializable transactions. Correct, but under contention most of them abort and retry. E: an optimistic version column on each seat. Fine for one seat, but a multi-seat all-or-nothing claim still ends in one conditional update, so I just write that. F: one conditional update, with the hold as data and an expiry. That is the pick.",
 "C: What it gives up. The hold can expire on a slow fan. The hottest seats are contended rows on one primary, which is exactly why the waiting room exists. And there must be a sweeper. I take those costs knowingly."], cls="theory")

S(plain("Theory · 6 of 6 · the failure catalogue", "What will go wrong, in the order I will break it", table(["#", "What goes wrong", "The question it becomes", "Protects"], [
  ["1", "Two fans on one seat", "Walk me through it, mechanically", "S1"],
  ["2", "Holds that outlive their owner", "What if the sweeper is down?", "L1"],
  ["3", "A hold expires while a payment is in flight", "Then the payment succeeds. What now?", "S2"],
  ["4", "A stampede at the door", "A million hit the database. What breaks?", "L3"],
  ["5", "Bots and an unfair line", "What does fair mean?", "fairness"],
  ["6", "A stale seat map", "Can a fan click a taken seat?", "L2, L3"],
  ["7", "Requirements that arrive mid-sale", "Release 5,000 seats. A waitlist. A tour.", "extension"],
  ["8", "A failure nobody can see", "How would you know it is broken?", "all"]], "bt sm")), [
 "C: The failure catalogue, and it becomes the challenge list. One: two fans on one seat. Two: holds that outlive their owner. Three: a hold expires while a payment is in flight. Four: a stampede at the door. Five: bots and an unfair line. Six: a stale seat map. Seven: requirements that arrive in the middle of the sale. Eight: a failure nobody can see.",
 "N: The order matters. Each fix creates the next question, and the last one is always: how would you know?"], cls="theory")
