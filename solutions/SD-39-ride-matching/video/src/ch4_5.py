from dsl import *
from stack import TECH, STACK, SUMMARY, SUMMARY_SAY, say_text
import re
P = "[+]"

chapter(4, "API and entities", 3, "What crosses the wire, and what is stored", [
 "C: The A-P-I, then the data. Every endpoint is tagged with its requirement."])

S(plain("API · request a ride (FR2)", "One request, idempotent, answered by a push",
  chips("serves FR2", "writes REQUEST", "the offer arrives on a stream") +
  code('POST /v1/rides\nIdempotency-Key: 7c1e…\n{"pickup": {"lat": 40.7484, "lng": -73.9857},\n "dropoff": {"lat": 40.7306, "lng": -73.9866},\n "product": "standard"}\n\n202 Accepted\n{"ride_id": "r77", "state": "matching"}', "json", hl=(2, 7, 8))), [
 "C: Requesting a ride, for F-R-two. An idempotency key, because a rider who taps twice in a tunnel must not get two cars. Pickup, drop-off and product.",
 "C: The answer is immediate and says matching. The driver arrives later, pushed to the rider's app, because matching takes seconds and nobody should hold a request open for it."])

S(plain("API · the driver's stream and the rest", "Three more, each tagged", table(["Interface", "Serves", "Touches", "Carries"], [
  ["<code>Stream Locations</code> (gRPC, driver → us)", "FR1", "LOCATION (memory)", "lat, lng, heading, <code>seq</code>, every 4 s"],
  ["<code>Offer</code> / <code>Accept(offer_id)</code> (same stream)", "FR3", "OFFER, TRIP", "an offer that expires; an idempotent accept"],
  ["<code>GET /v1/rides/{id}/car</code> (stream to the rider)", "FR4", "TRIP", "the assigned car's position, smoothed"]], "bt xs mx")), [
 "C: Three more.", P,
 "C: The driver's stream, for F-R-one: position, heading and a sequence number every four seconds. The sequence number lets the server drop an old position that arrives late.", P,
 "C: Offers and accepts, on the same stream, for F-R-three. An offer expires; an accept names the offer, so a retried accept is the same accept.", P,
 "C: And the rider's car position, for F-R-four."])

S(plain("API · the offer on the wire (FR3)", "What a driver receives, and what an accept must carry",
  code('{"offer": {"offer_id": "o-901", "ride_id": "r77",\n  "pickup": {"lat": 40.7484, "lng": -73.9857},\n  "eta_s": 240, "expires_at": "18:00:15.300Z"}}\n\n{"accept": {"offer_id": "o-901",\n            "driver_version": 19}}', "json", hl=(1, 3, 5, 6))), [
 "C: The offer on the wire, down the driver's stream, for F-R-three. It names itself, offer nine-oh-one, says where and how far, and says when it expires: fifteen seconds after it was made.",
 "C: The accept carries the offer I-D and the driver-state version the claim produced. A retried accept with the same offer I-D returns the same trip, and an accept for an offer that has expired, or for an older version, is refused. Both halves of S-two are in those two fields."])

S(dia("Data · conceptual model", "Requests, offers, trips, drivers, and where a driver was last seen", "erd-chen"), [
 "C: The conceptual model.", P, "C: A rider.", P, "C: A rider makes requests.", P, "C: A request becomes at most one trip.", P,
 "C: A driver drives many trips over time, one at a time.", P,
 "C: An offer exists only for a request: a weak entity, identified by the request and an offer I-D, with an expiry. A driver receives many offers.", P,
 "C: And a driver's location: the last place they were seen, a cell and a sequence number. Only the latest."], cls="dia")

S(dia("Data · physical model", "Durable rows for claims; memory for locations", "erd-physical"), [
 "C: The physical tables.", P, "C: Driver state: available, offered or on a trip, with a version and a lease. Claims are one conditional update here.", P,
 "C: Trips, in the regional PostgreSQL.", P, "C: Offers, one row each, with an expiry and an outcome.", P,
 "C: The city lease, mirroring etcd's epoch, so claims can be fenced.", P,
 "C: In memory, per city shard: driver to cell, and cell to drivers. Never written to disk.", P,
 "C: And the location log, batched, for history only. Matching never reads it."], cls="dia")

chapter(5, "High-level design", 4, "Three versions on one picture, then every path", [
 "C: The design in three versions, on one picture that only changes by deltas."])

S(dia("Design · version 1", "The simplest thing that works: everything in one database", "base-v1", vtag="V1"), [
 "C: Version one, the simplest thing that works.", P, "C: A rider requests.", P, "C: The ride A-P-I writes a trip.", P,
 "C: Into a trip store, which also holds every driver's location. It asks it for the nearest available driver.", P,
 "C: A driver reports a location.", P,
 "C: The driver gateway updates the driver's row. The objection: one point two five million durable updates a second, and a distance scan per request."], cls="dia")

S(dia("Design · version 2", "Locations move to memory: a cell index", "base-v2", vtag="V2"), [
 "C: Version two answers that.", P, "C: Version one, carried; the location update no longer goes to the trip store.", P,
 "C: New, a location index: in memory, cells to drivers, overwrite-only, sharded by city. The A-P-I asks it for nearby drivers. The objection: two riders asking at once get the same nearest driver."], cls="dia")

S(dia("Design · version 3", "Matching becomes a single writer per city, with claims", "base-v3", vtag="V3"), [
 "C: Version three answers that.", P, "C: Version two, carried.", P,
 "C: New, a matcher: one leader per city. It batches requests, takes candidates from the index, and claims drivers with a conditional write.", P,
 "C: New, routing for E-T-A: candidates are ranked by time, not distance.", P,
 "C: New, a location log: the gateway appends history in batches, for analytics.", P,
 "C: Which feeds E-T-A training, outside the system. This is the baseline."], cls="dia")

S(plain("Design · the containers", "Each container, what it owns, and its number", table(["Container", "Owns", "Its number"], [
  ["Ride API", "Requests, idempotency, the rider's view", "~2,100 requests/s at peak"],
  ["Driver gateway", "5 M streams; locations in, offers out", "100 pods"],
  ["Location index", "The latest position, per city, in memory", "1.25 M updates/s; ~1 GB"],
  ["Matcher", "The city's only writer of assignments", "a tick every 2 s"],
  ["Trip store", "Trips, offers, driver state, claims", "~2,100 claims/s"],
  ["Location log", "History, batched; never read to match", "125 MB/s"]], "bt xs mx")), [
 "C: The containers.", P, "C: The ride A-P-I: requests, idempotency, and what the rider sees.", P,
 "C: The driver gateway: five million streams, locations in and offers out.", P,
 "C: The location index: the latest position, per city, in memory. A million and a quarter updates a second in about a gigabyte.", P,
 "C: The matcher: the only writer of assignments in its city, ticking every two seconds.", P,
 "C: The trip store: trips, offers, driver state and claims.", P,
 "C: And the location log: history only. Matching never reads it."])

S(plain("Design · the trip state machine", "Every state has an owner and a way out", table(["State", "Entered when", "Leaves by", "Timer"], [
  ["matching", "a request is accepted", "a claim, or “no drivers”", "5 s target"],
  ["offered", "the claim succeeds", "accept, decline, or expiry", "15 s"],
  ["accepted", "the driver accepts", "arrival, or a lapsed lease", "30 s lease, renewed"],
  ["arriving", "the driver is moving", "pickup, cancel, or a lapsed lease", "30 s lease, renewed"],
  ["on trip", "pickup", "drop-off; hands over to the trip lifecycle", "—"]], "bt xs mx")), [
 "C: Before the flows, the trip's state machine, because every failure later is a missing exit from one of these states.", P,
 "C: Matching: entered on a request, left by a claim or a clear no, within five seconds.", P,
 "C: Offered: entered by the claim, left by accept, decline or a fifteen-second expiry. The expiry is what returns the driver to the pool.", P,
 "C: Accepted: left by arriving, or by a lapsed thirty-second lease if the driver vanishes.", P,
 "C: Arriving: the same lease, renewed by heartbeats, and the rider may cancel.", P,
 "C: On trip: from pickup to drop-off, handed over to the trip lifecycle. Every state has an owner, and every state has a timer or an event that ends it."])

S(dia("Flow · FR1", "A location, from the phone to the index", "flow-location"), [
 P, "C: A location, numbered.", P, "C: One: the driver's app sends it on its stream.", P, "C: Two: the gateway forwards it to the city's index shard: latest wins.", P,
 "C: Three: and appends it to the log in a batch.", P, "C: Four: history flows to analytics."], cls="dia")

S(dia("Flow · FR2 and FR3", "A request, from the rider to an offer", "flow-match"), [
 P, "C: A request, numbered.", P, "C: One: the rider asks.", P, "C: Two: the request joins the city matcher's queue.", P,
 "C: Three: candidates from two rings of cells.", P, "C: Four: an E-T-A matrix for the shortlist.", P,
 "C: Five: one conditional claim per assignment.", P, "C: Six: the offer, pushed down the driver's stream."], cls="dia")

S(dia("Sequence · FR1 report", "Latest wins, and silence expires", "seq-location"), [
 "C: Report, as a sequence.", P, "C: Driver forty-two sends sequence four thousand eight hundred and twelve.", P,
 "C: The gateway updates the shard.", P, "C: It's newer than what the shard holds, so it overwrites.", P,
 "C: A batch of two thousand updates goes to the log every second.", P,
 "C: And if driver forty-two goes silent for twelve seconds, they expire from the index: no longer offered rides."], cls="dia")

S(dia("Sequence · FR2 match", "A batch, candidates, a matrix, an assignment", "seq-request"), [
 "C: Match, as a sequence.", P, "C: The rider posts a request with an idempotency key.", P, "C: It joins the matcher's pending set.", P,
 "C: On the tick, forty requests are pending in this city.", P, "C: Two rings of cells around each pickup.", P,
 "C: Twenty candidates each, by distance.", P, "C: One E-T-A matrix, forty by twenty.", P,
 "C: A minimum-cost assignment: rider seventy-seven to driver forty-two."], cls="dia")

S(dia("Sequence · FR3 accept", "A claim, an offer, an idempotent accept", "seq-offer"), [
 "C: Accept, as a sequence.", P, "C: The matcher claims driver forty-two: if available, at version eighteen, with epoch seven.", P,
 "C: One row: claimed.", P, "C: The offer, valid for fifteen seconds.", P, "C: Pushed to the driver.", P,
 "C: The driver accepts, naming the offer: a retry would be the same accept.", P,
 "C: The rider sees driver forty-two, four minutes away."], cls="dia")

S(dia("Sequence · FR4 track", "The car, on the rider's map", "seq-track"), [
 "C: Track, as a sequence.", P, "C: The driver's location, every four seconds.", P,
 "C: Driver forty-two is on trip fifty-five twelve, so the gateway forwards it to that trip's rider.", P,
 "C: Smoothed.", P, "C: And the rider's map animates between points. No polling, no database read."], cls="dia")

subchapter("5.1", "Components and technologies", ["C: One level down: what each box runs on, the two containers the challenges open, and what I rejected."])

S(dia("Architecture · C4 containers · technologies", "The same containers, now with what they run on", "c4-containers-tech"), [
 P, "C: The same container view, with technologies.", P, "C: The ride A-P-I: Go on Kubernetes.", P,
 "C: The gateway: Go, gRPC streams, fifty thousand per pod.", P, "C: The location index: Go, in memory, H3, sharded by city.", P,
 "C: The matcher: Go, one leader per city through an etcd lease.", P, "C: The trip store: regional PostgreSQL with conditional claims.", P,
 "C: And the location log: Kafka."], cls="dia")

S(dia("Architecture · C4 components · matcher", "Inside the matcher, in the order a request meets it", "c4-comp-matcher"), [
 "C: Inside the matcher.", P, "C: Requests arrive from the ride A-P-I.", P, "C: The batcher collects them for a two-second tick.", P,
 "C: Candidates: two rings of cells from the location index, top twenty by distance.", P,
 "C: The E-T-A ranker: one matrix call to routing, cached per cell pair.", P, "C: The assigner solves min-cost over the whole batch.", P,
 "C: The claimer writes conditionally, carrying the epoch from the city lease in etcd.", P, "C: Into the trip store.", P,
 "C: And the offer manager runs the state machine and its timers, pushing offers through the gateway. Challenges one, two and five live here."], cls="dia")

S(dia("Architecture · C4 components · location index", "Inside the location index, in the order an update meets it", "c4-comp-geo"), [
 "C: Inside the location index.", P, "C: Updates arrive from the gateway.", P, "C: Ingest drops anything older than the sequence it holds.", P,
 "C: The cell mapper turns latitude and longitude into an H3 resolution-eight cell.", P, "C: The driver table: driver to cell and sequence.", P,
 "C: Expiry removes drivers silent for twelve seconds.", P, "C: The cell table: cell to drivers.", P,
 "C: A hot cell, over three hundred drivers, is indexed again at resolution nine.", P, "C: The query reads rings, nearest first.", P,
 "C: For the matcher. Challenges three and four live here."], cls="dia")

def tsay(_id):
    s = STACK[_id]; first = lambda t: re.split(r"(?<=[.:;])\s", say_text(t))[0].rstrip(".:;") + "."
    out = [P, "C: " + say_text(s["how"]), P, "C: Why: " + first(s["why"])]
    for i, (n, w) in enumerate(s["rejected"]):
        out += [P, f"C: {'Rejected: ' if i == 0 else ''}{say_text(n)}. " + first(w)]
    return out
for _id in ("geo", "trips", "gw", "match"):
    S(tech(**TECH(_id)), tsay(_id))

_ss = SUMMARY_SAY()
S(plain("Technology · the stack on one slide", "The stack, against its rivals",
        table(["Container", "Choice", "Rejected", "The deciding reason"], SUMMARY(), "bt xs mx") +
        grade("Naming a product is not the signal. Naming the property that rules out its rival is.")), _ss[:-1] + [P, _ss[-1]])

subchapter("5.2", "When you don't need all this", ["C: Before I break it: for one city, a much smaller design is right."], sub="ALTERNATE")

S(dia("Alternate path · ALTERNATE", "One PostgreSQL with PostGIS, and SKIP LOCKED", "alt",
      extra=strip(("fixb", "How it works", "Drivers update a PostGIS row every 15 s; a request runs a radius query and claims with SELECT … FOR UPDATE SKIP LOCKED."),
                  ("case", "What it gives up", "Durable writes for soft data; no batching; one database for every city."))), [
 P, "C: The alternate path, on version three.", P, "C: The matcher goes away.", P, "C: And the in-memory index.", P,
 "C: Instead, drivers update a PostGIS row every fifteen seconds. A request runs a radius query with a spatial index, and claims a driver with select for update skip locked, so two requests never take the same row.", P,
 "C: What it gives up: durable writes for data that's stale in seconds, no batching, and one database for every city."], cls="dia")

key("ALTERNATE · the line", "20,000 drivers every 15 s is <em>1,300 updates a second</em>: one database, easily. Our 5 M every 4 s is <em>1.25 M</em>. Below about <em>20,000 drivers</em>, I'd ship PostGIS.", [
 "C: Where's the line? Twenty thousand drivers every fifteen seconds is thirteen hundred updates a second. One database does that easily. Five million every four seconds is a million and a quarter.",
 "V: Below about twenty thousand drivers, a city or two, I'd ship PostGIS and skip locked, and say when I'd switch.", "[pause: 0.8]"])
