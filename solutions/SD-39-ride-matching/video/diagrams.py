#!/usr/bin/env python3
"""SD-39 nearby drivers and ride matching: every picture for the video and the written design -> ./svg/*.svg.
One canonical container view (V1 -> V4), two component views (matcher, location index), sequences, data models, figures.
Run: python3 diagrams.py"""
import html, pathlib, sys
sys.path.insert(0, str(pathlib.Path.home() / ".claude/skills/slide-video-kit/scripts"))
import basesvg as bs
import c4svg as c4
import seqsvg as sq
import erdsvg as er
from gtheme import ink

OUT = pathlib.Path(__file__).resolve().parent / "svg"; OUT.mkdir(exist_ok=True)
for old in OUT.glob("*"): old.unlink()
FONT = "Inter, Roboto, sans-serif"
INK, RED, GREEN, BLUE, GREY, AMBER = "#202124", "#ea4335", "#34a853", "#4285f4", "#5f6368", "#fbbc05"
def esc(s): return html.escape(str(s))
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent / "src"))
import stack

# ───────────────────────────── 1 · the canonical container view ─────────────────────────────────────
X = dict(A=20, B=400, C=780, D=1160, E=1540); Y = dict(R0=100, R1=360, R2=620); W, H, SZ = 250, 140, 26
def P(cell): return X[cell[0]], Y[cell[1:]]
BOX = {
    "rider": ("AR0", "person", "Rider", "Person", "Taps “request”.", 1),
    "driver": ("AR1", "person", "Driver", "Person", "Location every 4 s.", 1),
    "api":   ("BR0", "container", "Ride API", "Service", "Requests, trips.", 1),
    "gw":    ("BR1", "container", "Driver gateway", "Service", "Locations in, offers out.", 1),
    "probe": ("BR2", "container", "Probe riders", "Service", "Fake trips, every city.", 4),
    "match": ("CR0", "container", "Matcher", "Service", "Shortlist, rank, claim.", 3),
    "geo":   ("CR1", "db", "Location index", "In memory", "Cells → drivers.", 2),
    "log":   ("CR2", "queue", "Location log", "Partitioned log", "History, batched.", 3),
    "trips": ("DR0", "db", "Trip store", "Database", "Trips, drivers.", 1),
    "eta":   ("ER0", "ext", "Routing / ETA", "External", "Travel times.", 3),
    "hist":  ("ER2", "ext", "Analytics", "External", "ETA training.", 3),
}

def canon(labels=None):
    d = c4.Diagram(1830, 830, canon="containers")
    d.boundary(375, 20, 1060, 790, "Ride matching", "Software System", top="left")
    for k, (cell, kind, t, typ, desc, since) in BOX.items():
        if labels and k in labels: typ, desc = labels[k][1], labels[k][2]
        x, y = P(cell)
        d.node(k, x, y, W, H, kind, t, typ, desc, size=SZ, since=since)
    E = d.edge
    E("rider", "api", "request", "HTTPS", src="r", dst="l:0.5", at=(335, 152), size=21, eid="r-a")
    E("driver", "gw", "location", "gRPC", src="r", dst="l", at=(335, 412), size=21, eid="d-g")
    E("api", "trips", "trip; nearest (SQL)", "", src="r:0.3", dst="l:0.3", at=(970, 128), size=21, width=300, eid="a-t1", until=1)
    E("gw", "trips", "UPDATE location", "", src="r:0.2", dst="b:0.3", via=[(1235, 388)], at=(970, 376), size=21, eid="g-t", until=1)
    E("api", "trips", "trip row", "", src="r:0.3", dst="l:0.3", at=(970, 128), size=21, eid="a-t", since=2, until=2)
    E("gw", "geo", "latest", "", src="r:0.5", dst="l:0.5", at=(715, 412), size=21, eid="g-g", since=2)
    E("api", "geo", "nearby", "", src="b:0.8", dst="t:0.2", via=[(600, 300), (830, 300)], at=(715, 300), size=21, eid="a-g", since=2, until=2)
    E("api", "match", "request", "", src="r:0.7", dst="l:0.7", at=(715, 214), size=21, eid="a-m", since=3)
    E("match", "geo", "k-ring", "", src="b:0.5", dst="t:0.5", at=(960, 300), size=21, eid="m-g", since=3)
    E("match", "trips", "claim, trip", "", src="r:0.7", dst="l:0.7", at=(1095, 214), size=21, eid="m-t", since=3)
    E("match", "eta", "ETA matrix", "", src="t:0.5", dst="t:0.5", via=[(905, 60), (1665, 60)], at=(1285, 54), size=21, eid="m-e", since=3)
    E("match", "gw", "offer", "", src="l:0.95", dst="t:0.85", via=[(612, 233)], at=(640, 270), size=21, eid="m-w", since=3)
    E("gw", "log", "batches", "", src="b:0.7", dst="l:0.5", via=[(575, 690)], at=(690, 668), size=21, eid="g-l", since=3)
    E("log", "hist", "history", "", src="r:0.5", dst="l:0.5", at=(1285, 668), size=21, eid="l-h", since=3)
    E("probe", "gw", "fake driver", "", src="t:0.5", dst="b:0.5", at=(460, 560), size=21, eid="p-g", since=4)
    E("probe", "api", "fake rider", "", src="l:0.5", dst="l:0.85", via=[(360, 690), (360, 219)], at=(300, 560), size=21, eid="p-a", since=4)
    d.legend(30, 640, ("person", "container", "db", "queue", "ext"), vertical=True)
    return d

d = canon()
d.save(OUT / "base-v1.svg", upto=1, order=["rider", "api", "trips", "driver", "gw"])
d.save(OUT / "base-v2.svg", upto=2, new=2, order=["geo"])
d.save(OUT / "base-v3.svg", upto=3, new=3, order=["match", "eta", "log", "hist"])
d.save(OUT / "base-v4.svg", upto=4, new=4, order=["probe"])
d.save(OUT / "flow-location.svg", upto=3, flow=["d-g", "g-g", "g-l", "l-h"])
d.save(OUT / "flow-match.svg", upto=3, flow=["r-a", "a-m", "m-g", "m-e", "m-t", "m-w"])
d.save(OUT / "map.svg", upto=3, attack=["match", "geo", "gw"], keep=None)
d.save(OUT / "ch6-attack.svg", upto=3, attack=["match"], keep=["api", "match", "geo", "trips"])
d.save(OUT / "recap.svg", upto=4, badges={"geo": "M1 M2", "match": "M3 M5", "trips": "M3 CAS", "gw": "M4 leases", "probe": "probes"})
d.save(OUT / "alt.svg", upto=3, attack=["match", "geo"], keep=["api", "match", "geo", "trips", "gw"])
dt = canon(stack.C4)
dt.save(OUT / "c4-containers-tech.svg", upto=3, focus=["api", "gw", "geo", "match", "trips", "log"], keep=None)

# ───────────────────────────── 2 · C4 context ────────────────────────────────────────────────────────
x = c4.Diagram(1600, 700)
x.node("rider", 40, 80, 320, 150, "person", "Riders", "Person", "Request rides; watch the car arrive.", size=26)
x.node("driver", 40, 440, 320, 150, "person", "Drivers", "5 M active at peak", "Report location; accept offers.", size=26)
x.node("sys", 620, 250, 380, 190, "system", "Ride matching", "Software System", "Finds, offers, claims a driver.", size=28)
x.node("eta", 1240, 80, 320, 150, "ext", "Routing / ETA", "External system", "Travel time between points.", size=26)
x.node("pay", 1240, 440, 320, 150, "ext", "Trip lifecycle", "External system", "Pricing, payment, ratings.", size=26)
x.edge("rider", "sys", "request, track", "HTTPS", src="r", dst="l:0.25", at=(490, 160), size=22)
x.edge("driver", "sys", "location, offers", "gRPC stream", src="r", dst="l:0.75", at=(490, 520), size=22)
x.edge("sys", "eta", "ETA matrix", "RPC", src="r:0.25", dst="l", at=(1120, 160), size=22)
x.edge("sys", "pay", "trip started", "events", src="r:0.75", dst="l", at=(1120, 520), size=22)
x.legend(40, 660, ("person", "system", "ext"))
x.save(OUT / "c4-context.svg", order=["rider", "sys", "driver", "eta", "pay"])

# ───────────────────────────── 3 · component views ───────────────────────────────────────────────────
CX = [20, 300, 560, 820, 1080, 1340, 1600]; CW, CH, CS = 210, 150, 25
def comp(name, tech):
    d = c4.Diagram(1830, 770, canon="comp:" + name)
    d.boundary(275, 40, 1300, 700, name, tech, top="left")
    return d

m = comp("Matcher", "Container: Go, leader per city")
m.node("api", CX[0], 330, 200, CH, "container", "Ride API", "Service", "Requests.", size=CS)
m.node("batch", CX[1], 330, CW, CH, "component", "Batcher", "2 s tick", "Pending requests.", size=CS)
m.node("cand", CX[2], 330, CW, CH, "component", "Candidates", "k-ring", "Top 20 by distance.", size=CS)
m.node("rank", CX[3], 330, CW, CH, "component", "ETA ranker", "Matrix call", "Cached per cell pair.", size=CS)
m.node("assign", CX[4], 330, CW, CH, "component", "Assigner", "Min-cost", "All requests at once.", size=CS)
m.node("claim", CX[5], 330, CW, CH, "component", "Claimer", "Conditional write", "Version and epoch.", size=CS)
m.node("trips", CX[6], 330, 210, CH, "db", "Trip store", "PostgreSQL", "", size=CS)
m.node("geo", CX[2], 90, CW, CH, "db", "Location index", "In memory", "", size=CS)
m.node("eta", CX[3], 90, CW, CH, "ext", "Routing / ETA", "External", "", size=CS)
m.node("lease", CX[5], 90, CW, CH, "db", "City lease", "etcd", "Epoch 7.", size=CS)
m.node("offer", CX[5], 570, CW, CH, "component", "Offer manager", "State machine", "Timers, leases.", size=CS)
m.node("gw", CX[6], 570, 210, CH, "container", "Driver gateway", "Service", "", size=CS)
for a_, b_ in (("api", "batch"), ("batch", "cand"), ("cand", "rank"), ("rank", "assign"), ("assign", "claim"), ("claim", "trips")):
    m.edge(a_, b_, "", "", src="r", dst="l")
m.edge("geo", "cand", "", "", src="b", dst="t"); m.edge("eta", "rank", "", "", src="b", dst="t")
m.edge("lease", "claim", "", "", src="b", dst="t"); m.edge("claim", "offer", "", "", src="b", dst="t")
m.edge("offer", "gw", "", "", src="r", dst="l")
m.legend(40, 120, ("component", "container", "db", "ext"), vertical=True)
m.save(OUT / "c4-comp-matcher.svg", order=["api", "batch", ("cand", "geo"), ("rank", "eta"), "assign", ("claim", "lease"), "trips", ("offer", "gw")])
m.save(OUT / "ch1-attack.svg", keep=["assign", "claim", "trips"], attack=["claim"])
m.save(OUT / "ch1-fix.svg", keep=["assign", "claim", "trips"], fix=["claim", "trips"])
m.save(OUT / "ch2-attack.svg", keep=["offer", "gw"], attack=["offer"])
m.save(OUT / "ch2-fix.svg", keep=["offer", "gw"], fix=["offer"])
m.save(OUT / "ch5-attack.svg", keep=["cand", "rank", "assign"], attack=["cand"])
m.save(OUT / "ch5-fix.svg", keep=["cand", "rank", "assign"], fix=["rank", "assign"])

g = comp("Location index", "Container: Go, in memory, per city")
g.node("gw", CX[0], 330, 200, CH, "container", "Driver gateway", "Service", "Updates.", size=CS)
g.node("ing", CX[1], 330, CW, CH, "component", "Ingest", "Sequence check", "Latest wins.", size=CS)
g.node("cell", CX[2], 330, CW, CH, "component", "Cell mapper", "H3 res 8", "lat, lng → cell.", size=CS)
g.node("dtab", CX[3], 330, CW, CH, "component", "Driver table", "Map", "driver → cell, seq.", size=CS)
g.node("ctab", CX[4], 330, CW, CH, "component", "Cell table", "Map", "cell → drivers.", size=CS)
g.node("query", CX[5], 330, CW, CH, "component", "Query", "k-ring", "Nearest first.", size=CS)
g.node("match", CX[6], 330, 210, CH, "container", "Matcher", "Service", "", size=CS)
g.node("exp", CX[3], 90, CW, CH, "component", "Expiry", "Sweeper", "Silent 12 s: gone.", size=CS)
g.node("split", CX[4], 570, CW, CH, "component", "Hot-cell split", "H3 res 9", "Over 300 drivers.", size=CS)
for a_, b_ in (("gw", "ing"), ("ing", "cell"), ("cell", "dtab"), ("dtab", "ctab"), ("ctab", "query"), ("query", "match")):
    g.edge(a_, b_, "", "", src="r", dst="l")
g.edge("exp", "dtab", "", "", src="b", dst="t"); g.edge("ctab", "split", "", "", src="b", dst="t")
g.legend(40, 120, ("component", "container"), vertical=True)
g.save(OUT / "c4-comp-geo.svg", order=["gw", "ing", "cell", "dtab", "exp", "ctab", "split", "query", "match"])
g.save(OUT / "ch3-attack.svg", keep=["cell", "ctab", "query"], attack=["query"])
g.save(OUT / "ch3-fix.svg", keep=["cell", "ctab", "query"], fix=["query", "ctab"])
g.save(OUT / "ch4-attack.svg", keep=["ing", "cell", "dtab"], attack=["dtab"])
g.save(OUT / "ch4-fix.svg", keep=["ing", "cell", "dtab"], fix=["ing"])

# ───────────────────────────── 4 · sequences ─────────────────────────────────────────────────────────
def seq(name, parts, steps, size=24, row=54, width=1500):
    q = sq.Seq(width, size=size, row=row)
    for pp in parts: q.part(*pp)
    for st in steps:
        k = st[0]
        if k == "m": q.msg(st[1], st[2], st[3], **(st[4] if len(st) > 4 else {}))
        elif k == "r": q.ret(st[1], st[2], st[3], **(st[4] if len(st) > 4 else {}))
        elif k == "n": q.note(st[1], st[2], st[3], *(st[4:5]))
    q.save(OUT / f"{name}.svg")

seq("seq-location",
    [("dr", "Driver app", "person"), ("gw", "Gateway", "container"), ("ix", "Index shard", "db"), ("lg", "Location log", "queue")],
    [("m", "dr", "gw", "location, seq 4,812 (every 4 s)"),
     ("m", "gw", "ix", "update d42: cell 8828…, seq 4,812"),
     ("n", "ix", "ix", "seq newer than 4,811: overwrite", "green"),
     ("m", "gw", "lg", "batch of 2,000 updates, every second", dict(kind="async")),
     ("n", "ix", "ix", "no update for 12 s: d42 expires", "amber")])

seq("seq-request",
    [("rd", "Rider app", "person"), ("api", "Ride API", "container"), ("mt", "Matcher", "container"), ("ix", "Index", "db"), ("et", "ETA", "ext")],
    [("m", "rd", "api", "POST /rides, pickup, request id"),
     ("m", "api", "mt", "pending request r77"),
     ("n", "mt", "mt", "tick: 40 pending in this city", "amber"),
     ("m", "mt", "ix", "k-ring 2 around each pickup"),
     ("r", "ix", "mt", "top 20 by distance each"),
     ("m", "mt", "et", "ETA matrix 40 × 20"),
     ("n", "mt", "mt", "min-cost assignment: r77 → d42", "blue")])

seq("seq-offer",
    [("mt", "Matcher", "container"), ("ts", "Trip store", "db"), ("gw", "Gateway", "container"), ("dr", "Driver d42", "person"), ("rd", "Rider", "person")],
    [("m", "mt", "ts", "claim d42 if available, version 18, epoch 7"),
     ("r", "ts", "mt", "1 row: claimed"),
     ("m", "mt", "gw", "offer o-901 to d42, expires in 15 s"),
     ("m", "gw", "dr", "offer o-901"),
     ("m", "dr", "ts", "accept o-901 (idempotent)"),
     ("r", "ts", "rd", "driver d42, ETA 4 min", dict(hl=True))])

seq("seq-track",
    [("dr", "Driver d42", "person"), ("gw", "Gateway", "container"), ("api", "Ride API", "container"), ("rd", "Rider", "person")],
    [("m", "dr", "gw", "location every 4 s"),
     ("m", "gw", "api", "d42 is on trip t-5512: forward", dict(kind="async")),
     ("m", "api", "rd", "car position, smoothed", dict(kind="async")),
     ("n", "rd", "rd", "the map animates between points", "green")])

seq("seq-th-claim",
    [("a", "Matcher, epoch 7", "container"), ("ts", "Trip store", "db"), ("b", "Old leader, epoch 6", "container")],
    [("m", "a", "ts", "claim d42 if available, version 18, epoch ≥ 7"),
     ("m", "b", "ts", "claim d42 if available, version 18, epoch ≥ 6"),
     ("r", "ts", "a", "1 row: version 19, offered to r77", dict(hl=True)),
     ("r", "ts", "b", "0 rows: version is 19 and city epoch is 7"),
     ("n", "b", "b", "the deposed leader learns it lost", "amber")])

seq("seq-ch2-vanish",
    [("mt", "Offer manager", "container"), ("dr", "Driver d42", "person"), ("ts", "Trip store", "db"), ("rd", "Rider", "person")],
    [("m", "dr", "ts", "accept o-901"),
     ("n", "dr", "dr", "the app crashes; no heartbeat", "amber"),
     ("n", "mt", "mt", "lease on d42 for t-5512: 30 s, renewed by heartbeats", "blue"),
     ("m", "mt", "ts", "lease expired: d42 unavailable, t-5512 back to matching"),
     ("m", "mt", "rd", "finding you a new driver (no charge)", dict(hl=True))])

# ───────────────────────────── 5 · data models ───────────────────────────────────────────────────────
c = er.Chen(1960, 900, size=27)
c.entity("rider", 200, 140, "RIDER"); c.entity("req", 700, 140, "REQUEST"); c.entity("trip", 1200, 140, "TRIP")
c.entity("driver", 1200, 560, "DRIVER"); c.entity("offer", 700, 560, "OFFER", weak=True); c.entity("loc", 1200, 830, "LOCATION")
c.rel("makes", 450, 140, "MAKES"); c.rel("becomes", 950, 140, "BECOMES"); c.rel("drives", 1200, 350, "DRIVES")
c.rel("gets", 950, 560, "RECEIVES"); c.rel("for", 700, 350, "FOR", identifying=True); c.rel("at", 1200, 700, "LAST SEEN AT")
c.attr("rid", 200, 50, "rider_id", of="rider", key=True)
c.attr("pick", 700, 50, "pickup", of="req"); c.attr("tid", 1200, 50, "trip_id", of="trip", key=True); c.attr("st", 1440, 140, "state", of="trip")
c.attr("did", 1440, 560, "driver_id", of="driver", key=True); c.attr("ver", 1460, 650, "version", of="driver")
c.attr("oid", 700, 690, "offer_id", of="offer", partial=True); c.attr("exp", 900, 700, "expires", of="offer")
c.attr("cell", 1460, 830, "cell, seq", of="loc")
c.link("rider", "makes", "1"); c.link("makes", "req", "N")
c.link("req", "becomes", "1"); c.link("becomes", "trip", "1")
c.link("driver", "drives", "1", src="t", dst="b"); c.link("drives", "trip", "N", src="t", dst="b")
c.link("driver", "gets", "1"); c.link("gets", "offer", "N")
c.link("req", "for", "1", src="b", dst="t"); c.link("for", "offer", "N", src="b", dst="t", total=True)
c.link("loc", "at", "1", src="t", dst="b"); c.link("at", "driver", "1", src="t", dst="b")
c.legend(1660, 70, size=23, gap=36, rows=["rect", "rect2", "dia", "dia2", "oval", "key", "dbl"])
c.save(OUT / "erd-chen.svg", order=["rider", ("req", "makes"), ("trip", "becomes"), ("driver", "drives"), ("offer", "gets", "for"), ("loc", "at")])

e = er.ERD(1600, 820, size=22)
e.entity("drv", 30, 40, 470, "driver_state", [("driver_id", "bigint", "PK"), ("city", "int", "IX"), ("state", "available | offered | on_trip", ""),
         ("trip_id", "bigint", ""), ("version", "bigint", ""), ("lease_until", "ts", "")], kind="focus", caption="claims: one conditional update")
e.entity("trip", 570, 40, 470, "trip", [("trip_id", "bigint", "PK"), ("rider_id", "bigint", "IX"), ("driver_id", "bigint", "IX"),
         ("state", "requested … completed", ""), ("pickup", "lat, lng", "")], caption="PostgreSQL, regional")
e.entity("off", 1110, 40, 460, "offer", [("offer_id", "uuid", "PK"), ("trip_id", "bigint", "FK"), ("driver_id", "bigint", ""),
         ("expires_at", "ts", ""), ("outcome", "text", "")], caption="one row per offer")
e.entity("city", 30, 470, 470, "city_lease", [("city", "int", "PK"), ("epoch", "bigint", ""), ("leader", "text", "")], kind="ext",
         caption="mirrors the etcd lease")
e.entity("mem", 570, 470, 470, "in memory, per city shard", [("driver → cell, lat, lng, seq, t", "map", ""), ("cell → driver set", "map", ""),
         ("expiry", "12 s", "")], kind="redis", caption="never written to disk")
e.entity("hist", 1110, 470, 460, "location log", [("driver_id", "key", ""), ("t, lat, lng", "", ""), ("seq", "bigint", "")], kind="ext",
         caption="Kafka, batched; history only")
e.rel("off", "trip", "N", "1", src="l:0.5", dst="r:0.5", label="")
e.rel("trip", "drv", "N", "1", src="l:0.6", dst="r:0.6", label="")
e.save(OUT / "erd-physical.svg", order=["drv", "trip", "off", "city", "mem", "hist"])

# ───────────────────────────── 6 · figures ───────────────────────────────────────────────────────────
def svgdoc(w, h, body): return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" width="{w}" height="{h}">'
                               f'<rect width="{w}" height="{h}" fill="#ffffff"/>{body}</svg>')
def T(x, y, s, size=24, fill=INK, w=500, anchor="start"):
    return f'<text x="{x}" y="{y}" text-anchor="{anchor}" font-family="{FONT}" font-size="{size}" font-weight="{w}" fill="{ink(fill)}">{esc(s)}</text>'
def R(x, y, w, h, fill, stroke, rx=10, sw=2.2):
    return f'<rect x="{x:.1f}" y="{y:.1f}" width="{w:.1f}" height="{h:.1f}" rx="{rx}" fill="{fill}" stroke="{stroke}" stroke-width="{sw}"/>'
import math
def hexagon(cx, cy, r, fill, stroke, sw=2):
    pts = " ".join(f"{cx + r*math.cos(math.radians(60*i+30)):.1f},{cy + r*math.sin(math.radians(60*i+30)):.1f}" for i in range(6))
    return f'<polygon points="{pts}" fill="{fill}" stroke="{stroke}" stroke-width="{sw}"/>'

def kring():
    p = [T(40, 48, "A 2-D question as a lookup: the pickup's cell and two rings of neighbours, 19 cells", 28, INK, 800)]
    r = 52; dx = r * math.sqrt(3); cx0, cy0 = 520, 300
    axial = [(q, s) for q in range(-2, 3) for s in range(-2, 3) if abs(q + s) <= 2]
    for q, s in axial:
        x = cx0 + dx * (q + s / 2); y = cy0 + 1.5 * r * s
        ring = max(abs(q), abs(s), abs(q + s))
        fill = ["#fef7e0", "#e8f0fe", "#f8f9fa"][ring]; stroke = [AMBER, BLUE, GREY][ring]
        p.append(hexagon(x, y, r - 2, fill, stroke))
    p += [f'<circle cx="{cx0}" cy="{cy0}" r="9" fill="{RED}"/>', T(cx0 + 14, cy0 - 12, "pickup", 20, "#c5221f", 700)]
    for (fx, fy) in [(cx0 + 60, cy0 + 40), (cx0 - 120, cy0 - 70), (cx0 + 170, cy0 - 120), (cx0 - 40, cy0 + 150), (cx0 + 220, cy0 + 90)]:
        p.append(f'<circle cx="{fx}" cy="{fy}" r="7" fill="{BLUE}"/>')
    p += [f'<circle cx="{cx0 - dx*0.5 - 40}" cy="{cy0 + 1.5*r - 4}" r="7" fill="{GREEN}"/>',
          T(cx0 - dx * 0.5 - 30, cy0 + 1.5 * r + 50, "50 m away, next cell", 20, "#188038", 700)]
    p += [T(960, 160, "Ring 0: the pickup's cell", 24, "#b06000", 800), T(960, 210, "Ring 1: 6 neighbours", 24, "#1967d2", 800),
          T(960, 260, "Ring 2: 12 more: 19 cells ≈ 14 km²", 24, GREY, 800),
          T(960, 340, "Each cell ID is a 64-bit integer:", 22, INK, 600), T(960, 375, "the query is 19 map lookups,", 22, INK, 600),
          T(960, 410, "not a distance over every driver.", 22, INK, 600)]
    (OUT / "kring.svg").write_text(svgdoc(1600, 520, "".join(p)))
kring()

def tension():
    p = [T(40, 50, "Two problems that look like one: where are the drivers, and who gets which one", 28, INK, 800)]
    cards = [("A geo problem", "1.25 M location writes a second; a lookup by area in milliseconds", "fast, overwrite-only, lossy is fine", BLUE, "#e8f0fe"),
             ("A contention problem", "two riders, one driver, the same second", "exact: one claim wins, the other retries", RED, "#fce8e6"),
             ("Kept apart", "the index can be stale and lose data; the claim cannot", "different stores, different guarantees", GREEN, "#e6f4ea")]
    for i, (t, s, n, col, fill) in enumerate(cards):
        x = 60 + i * 510
        p += [R(x, 110, 470, 250, fill, col, rx=14), T(x + 24, 160, t, 27, INK, 800)]
        line, yy = "", 205
        for w_ in s.split():
            if len(line) + len(w_) > 34: p.append(T(x + 24, yy, line, 22, INK, 500)); line, yy = w_, yy + 30
            else: line = (line + " " + w_).strip()
        p += [T(x + 24, yy, line, 22, INK, 500), T(x + 24, 330, n, 22, col, 800)]
    (OUT / "tension.svg").write_text(svgdoc(1600, 400, "".join(p)))
tension()

bs.budget_bar(OUT / "budget.svg", [("batch wait", 2.0, "service"), ("index, ETA, claim", 0.7, "data"), ("push to driver", 0.5, "edge")], total=5, unit="s", title="From a request to an offer on the driver's phone (initial target p95 5 s)")
print(sorted(pp.name for pp in OUT.glob("*.svg")))
