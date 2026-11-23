#!/usr/bin/env python3
"""SD-97 device telemetry and live location map: every picture for the video and the written design -> ./svg/*.svg.
One canonical container view (V1 -> V4), three component views (vehicle uplink, state updater, map API), sequences,
data models, figures. Run: python3 diagrams.py"""
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

X = dict(A=20, B=400, C=780, D=1160, E=1540); Y = dict(R0=100, R1=360, R2=620); W, H, SZ = 250, 140, 26
def P(cell): return X[cell[0]], Y[cell[1:]]
BOX = {
    "uplink": ("AR1", "container", "Vehicle uplink", "On 2 M vehicles", "Buffer, priorities.", 1),
    "gw":     ("BR1", "container", "Telemetry gateway", "Broker", "Identity, sessions.", 1),
    "safety": ("BR0", "queue", "Safety lane", "Priority log", "Never waits.", 3),
    "fresh":  ("BR2", "container", "Freshness probe", "Service", "Canary vehicles.", 4),
    "log":    ("CR1", "queue", "Telemetry log", "Partitioned log", "By vehicle.", 1),
    "upd":    ("CR0", "container", "State updater", "Stream job", "Newer seq only.", 2),
    "lake":   ("CR2", "db", "History lake", "Object storage", "Every position.", 1),
    "live":   ("DR0", "db", "Live store", "In memory", "Latest, by cell.", 2),
    "map":    ("DR1", "container", "Map API", "Service", "Viewports, pushes.", 1),
    "replay": ("DR2", "container", "Replay API", "Query engine", "One vehicle, one hour.", 3),
    "disp":   ("ER0", "ext", "Dispatch / on-call", "External", "Acts on alerts.", 3),
    "ops":    ("ER1", "person", "Fleet operator", "Person", "Watches the map.", 1),
    "ml":     ("ER2", "ext", "Analysts, ML", "External", "Replays, training.", 3),
}

def canon(labels=None):
    d = c4.Diagram(1830, 830, canon="containers")
    d.boundary(5, 20, 1430, 790, "Fleet telemetry", "Software System", top="left")
    for k, (cell, kind, t, typ, desc, since) in BOX.items():
        if labels and k in labels: typ, desc = labels[k][1], labels[k][2]
        x, y = P(cell)
        d.node(k, x, y, W, H, kind, t, typ, desc, size=SZ, since=since)
    E = d.edge
    E("uplink", "gw", "positions", "MQTT", src="r", dst="l", at=(335, 412), size=21, eid="u-g")
    E("gw", "log", "append", "by vehicle", src="r", dst="l", at=(715, 412), size=21, eid="g-l")
    E("log", "lake", "files, 5 min", "", src="b:0.5", dst="t:0.5", at=(970, 560), size=21, eid="l-k")
    E("map", "lake", "query (slow)", "", src="b:0.2", dst="r:0.3", via=[(1210, 662)], at=(1110, 600), size=21, eid="m-k", until=1)
    E("log", "upd", "consume", "", src="t:0.5", dst="b:0.5", at=(960, 300), size=21, eid="l-u", since=2)
    E("upd", "live", "if newer", "", src="r:0.5", dst="l:0.5", at=(1095, 152), size=21, eid="u-v", since=2)
    E("map", "live", "cells", "", src="t:0.5", dst="b:0.5", at=(1330, 300), size=21, eid="m-v", since=2)
    E("ops", "map", "viewport", "WebSocket", src="l", dst="r", at=(1475, 412), size=21, eid="o-m")
    E("gw", "safety", "safety events", "", src="t:0.5", dst="b:0.5", at=(600, 300), size=21, eid="g-s", since=3)
    E("safety", "disp", "≤ 1 s", "", src="t:0.5", dst="t:0.5", via=[(525, 60), (1665, 60)], at=(1095, 54), size=21, eid="s-d", since=3)
    E("replay", "lake", "one vehicle", "", src="l:0.5", dst="r:0.5", at=(1095, 690), size=21, eid="r-k", since=3)
    E("ml", "replay", "replays", "", src="l:0.5", dst="r:0.5", at=(1475, 670), size=21, eid="ml-r", since=3)
    E("fresh", "gw", "canary", "", src="t:0.5", dst="b:0.5", at=(590, 560), size=21, eid="f-g", since=4)
    E("fresh", "map", "read back", "", src="r:0.15", dst="b:0.2", via=[(715, 641), (715, 575), (1210, 575)], at=(1100, 598), size=21, eid="f-m", since=4)
    d.legend(30, 640, ("person", "container", "db", "queue", "ext"), vertical=True)
    return d

d = canon()
d.save(OUT / "base-v1.svg", upto=1, order=["uplink", "gw", "log", "lake", "map", "ops"])
d.save(OUT / "base-v2.svg", upto=2, new=2, order=["upd", "live"])
d.save(OUT / "base-v3.svg", upto=3, new=3, order=["safety", "disp", "replay", "ml"])
d.save(OUT / "base-v4.svg", upto=4, new=4, order=["fresh"])
d.save(OUT / "flow-live.svg", upto=3, flow=["u-g", "g-l", "l-u", "u-v", "o-m", "m-v"])
d.save(OUT / "flow-history.svg", upto=3, flow=["u-g", "g-l", "l-k", "ml-r", "r-k"])
d.save(OUT / "map.svg", upto=3, attack=["upd", "log", "map", "uplink", "lake"], keep=None)
d.save(OUT / "ch5-attack.svg", upto=3, attack=["lake"], keep=["lake", "replay"])
d.save(OUT / "ch5-fix.svg", upto=3, fix=["lake", "replay"], keep=["lake", "replay"])
d.save(OUT / "ch6-attack.svg", upto=3, attack=["map"], keep=["log", "upd", "live", "map"])
d.save(OUT / "recap.svg", upto=4, badges={"uplink": "M4", "log": "M2", "upd": "M1 M2", "live": "M3", "map": "M3 M5", "lake": "M1", "fresh": "probes"})
d.save(OUT / "alt.svg", upto=2, attack=["log", "upd", "live"], keep=["uplink", "gw", "log", "upd", "live", "map"])
d.save(OUT / "seams.svg", upto=3, badges={"uplink": "SD-29", "gw": "SD-29", "upd": "SD-03", "live": "SD-39", "lake": "SD-03"})
dt = canon(stack.C4)
dt.save(OUT / "c4-containers-tech.svg", upto=3, focus=["uplink", "gw", "log", "upd", "live", "map", "lake", "replay"], keep=None)

x = c4.Diagram(1600, 700)
x.node("veh", 40, 80, 320, 150, "ext", "Vehicles", "2 M, often in tunnels", "Send positions and health.", size=26)
x.node("ops", 40, 440, 320, 150, "person", "Fleet operators", "5,000 at once", "Watch the live map.", size=26)
x.node("sys", 620, 250, 380, 190, "system", "Fleet telemetry", "Software System", "Live map; two years of history.", size=28)
x.node("disp", 1240, 80, 320, 150, "ext", "Dispatch / on-call", "External system", "Acts on safety events.", size=26)
x.node("ml", 1240, 440, 320, 150, "ext", "Analysts, ML", "External system", "Replay, audit, training.", size=26)
x.edge("veh", "sys", "positions, health", "MQTT, mTLS", src="r", dst="l:0.25", at=(490, 160), size=22)
x.edge("ops", "sys", "live map", "WebSocket", src="r", dst="l:0.75", at=(490, 520), size=22)
x.edge("sys", "disp", "safety events", "≤ 1 s", src="r:0.25", dst="l", at=(1120, 160), size=22)
x.edge("ml", "sys", "replays, exports", "SQL", src="l", dst="r:0.75", at=(1120, 520), size=22)
x.legend(40, 660, ("person", "system", "ext"))
x.save(OUT / "c4-context.svg", order=["veh", "sys", "ops", "disp", "ml"])

CX = [20, 300, 560, 820, 1080, 1340, 1600]; CW, CH, CS = 210, 150, 25
def comp(name, tech):
    d = c4.Diagram(1830, 770, canon="comp:" + name)
    d.boundary(275, 40, 1300, 700, name, tech, top="left")
    return d

u = comp("Vehicle uplink", "Container: C++, on the vehicle")
u.node("gps", CX[0], 330, 200, CH, "ext", "GPS, sensors", "On board", "", size=CS)
u.node("samp", CX[1], 330, CW, CH, "component", "Sampler", "2 s moving", "30 s parked.", size=CS)
u.node("buf", CX[2], 330, CW, CH, "component", "Ring buffer", "6 h, in flash", "seq per message.", size=CS)
u.node("prio", CX[3], 330, CW, CH, "component", "Scheduler", "Three lanes", "Safety, latest, backfill.", size=CS)
u.node("cli", CX[4], 330, CW, CH, "component", "MQTT client", "Jittered backoff", "Resumes a session.", size=CS)
u.node("gw", CX[5], 330, 210, CH, "container", "Gateway", "Broker", "", size=CS)
u.node("safe", CX[2], 90, CW, CH, "component", "Safety detector", "Hard brake, crash", "Skips the queue.", size=CS)
u.node("bp", CX[4], 570, CW, CH, "component", "Rate cap", "Backfill", "≤ 50 messages/s.", size=CS)
for a_, b_ in (("gps", "samp"), ("samp", "buf"), ("buf", "prio"), ("prio", "cli"), ("cli", "gw")):
    u.edge(a_, b_, "", "", src="r", dst="l")
u.edge("samp", "safe", "", "", src="t", dst="l:0.5", via=[(405, 165)]); u.edge("safe", "prio", "", "", src="r", dst="t", via=[(925, 165)])
u.edge("prio", "bp", "", "", src="b", dst="l:0.5", via=[(925, 645)]); u.edge("bp", "cli", "", "", src="t", dst="b")
u.legend(40, 120, ("component", "container", "ext"), vertical=True)
u.save(OUT / "c4-comp-uplink.svg", order=["gps", "samp", "safe", "buf", "prio", "bp", "cli", "gw"])
u.save(OUT / "ch4-attack.svg", keep=["buf", "prio", "cli"], attack=["prio"])
u.save(OUT / "ch4-fix.svg", keep=["buf", "prio", "cli"], fix=["prio"])

s = comp("State updater", "Container: Flink, keyed by vehicle")
s.node("log", CX[0], 330, 200, CH, "queue", "Telemetry log", "Kafka", "By vehicle.", size=CS)
s.node("src", CX[1], 330, CW, CH, "component", "Source", "Per partition", "In order.", size=CS)
s.node("seq", CX[2], 330, CW, CH, "component", "Seq filter", "Keyed state", "Last seq per vehicle.", size=CS)
s.node("cell", CX[3], 330, CW, CH, "component", "Cell mapper", "H3 res 9", "Moved cell?", size=CS)
s.node("wr", CX[4], 330, CW, CH, "component", "Live writer", "Conditional", "Only if newer.", size=CS)
s.node("live", CX[5], 330, 210, CH, "db", "Live store", "In memory", "", size=CS)
s.node("old", CX[2], 570, CW, CH, "component", "Old positions", "Side output", "History only.", size=CS)
for a_, b_ in (("log", "src"), ("src", "seq"), ("seq", "cell"), ("cell", "wr"), ("wr", "live")):
    s.edge(a_, b_, "", "", src="r", dst="l")
s.edge("seq", "old", "", "", src="b", dst="t")
s.legend(40, 120, ("component", "db", "queue"), vertical=True)
s.save(OUT / "c4-comp-updater.svg", order=["log", "src", "seq", "old", "cell", "wr", "live"])
s.save(OUT / "ch1-attack.svg", keep=["src", "seq", "cell", "wr"], attack=["wr"])
s.save(OUT / "ch1-fix.svg", keep=["src", "seq", "cell", "wr"], fix=["seq", "wr"])

m = comp("Map API", "Container: Go, WebSockets")
m.node("ops", CX[0], 330, 200, CH, "person", "Operator", "Browser", "", size=CS)
m.node("vp", CX[1], 330, CW, CH, "component", "Viewport tracker", "Zoom → resolution", "Cells in view.", size=CS)
m.node("sub", CX[2], 330, CW, CH, "component", "Cell subscriptions", "Per viewer", "Only cells in view.", size=CS)
m.node("agg", CX[3], 330, CW, CH, "component", "Aggregator", "Res 6 / 7", "Counts when far.", size=CS)
m.node("push", CX[4], 330, CW, CH, "component", "Delta pusher", "1 s tick", "What changed.", size=CS)
m.node("live", CX[5], 330, 210, CH, "db", "Live store", "Change feed", "", size=CS)
m.node("snap", CX[2], 570, CW, CH, "component", "Snapshot loader", "On pan", "Then deltas.", size=CS)
for a_, b_ in (("ops", "vp"), ("vp", "sub"), ("sub", "agg"), ("agg", "push")):
    m.edge(a_, b_, "", "", src="r", dst="l")
m.edge("live", "push", "", "", src="l", dst="r")
m.edge("sub", "snap", "", "", src="b", dst="t")
m.legend(40, 120, ("component", "db"), vertical=True)
m.save(OUT / "c4-comp-map.svg", order=["ops", "vp", "sub", "snap", "agg", "push", "live"])
m.save(OUT / "ch2-attack.svg", keep=["vp", "sub", "agg"], attack=["agg"])
m.save(OUT / "ch2-fix.svg", keep=["vp", "sub", "agg"], fix=["agg"])
m.save(OUT / "ch3-attack.svg", keep=["sub", "agg", "push"], attack=["push"])
m.save(OUT / "ch3-fix.svg", keep=["sub", "agg", "push"], fix=["sub", "push"])

def seq(name, parts, steps, size=24, row=54, width=1500):
    q = sq.Seq(width, size=size, row=row)
    for pp in parts: q.part(*pp)
    for st in steps:
        k = st[0]
        if k == "m": q.msg(st[1], st[2], st[3], **(st[4] if len(st) > 4 else {}))
        elif k == "r": q.ret(st[1], st[2], st[3], **(st[4] if len(st) > 4 else {}))
        elif k == "n": q.note(st[1], st[2], st[3], *(st[4:5]))
    q.save(OUT / f"{name}.svg")

seq("seq-report",
    [("up", "Uplink", "container"), ("gw", "Gateway", "container"), ("lg", "Kafka", "queue"), ("st", "State updater", "container"), ("lv", "Live store", "db")],
    [("m", "up", "gw", "position, v-311, seq 9,402"),
     ("m", "gw", "lg", "append, key = v-311"),
     ("m", "lg", "st", "in order for v-311", dict(kind="async")),
     ("n", "st", "st", "seq 9,402 > 9,401: newer", "green"),
     ("m", "st", "lv", "v-311 → cell 8928…, seq 9,402")])

seq("seq-watch",
    [("op", "Operator", "person"), ("mp", "Map API", "container"), ("lv", "Live store", "db")],
    [("m", "op", "mp", "viewport: downtown, zoom 15"),
     ("n", "mp", "mp", "zoom 15 → res 9: 48 cells", "blue"),
     ("m", "mp", "lv", "snapshot of 48 cells"),
     ("r", "mp", "op", "1,930 vehicles"),
     ("m", "lv", "mp", "changes in those cells", dict(kind="async")),
     ("r", "mp", "op", "every second: 410 moved", dict(hl=True))])

seq("seq-replay",
    [("an", "Analyst", "ext"), ("rp", "Replay API", "container"), ("lk", "History lake", "db")],
    [("m", "an", "rp", "v-311, 14:00 – 15:00, 3 Nov"),
     ("n", "rp", "rp", "day 3 Nov, bucket hash(v-311) mod 256 = 77", "blue"),
     ("m", "rp", "lk", "read one bucket at a snapshot; vehicle, seq range"),
     ("r", "lk", "rp", "1,800 positions, sorted by seq"),
     ("r", "rp", "an", "the hour, with every buffered fix", dict(hl=True))])

seq("seq-safety",
    [("up", "Uplink", "container"), ("gw", "Gateway", "container"), ("sf", "Safety lane", "queue"), ("dp", "Dispatch", "ext")],
    [("n", "up", "up", "hard brake detected: skip the queue", "amber"),
     ("m", "up", "gw", "safety event, QoS 1"),
     ("m", "gw", "sf", "append to the safety topic"),
     ("m", "sf", "dp", "page within 1 s", dict(kind="async", hl=True))])

seq("seq-th-split",
    [("lg", "Kafka", "queue"), ("st", "State updater", "container"), ("lv", "Live store", "db"), ("lk", "History lake", "db")],
    [("m", "lg", "lk", "every position, appended in 5-minute files", dict(kind="async")),
     ("m", "lg", "st", "the same positions", dict(kind="async")),
     ("n", "st", "st", "keep only the newest per vehicle", "green"),
     ("m", "st", "lv", "overwrite: latest wins"),
     ("n", "lk", "lk", "nothing is ever overwritten here", "blue")])

seq("seq-ch1-tunnel",
    [("up", "Uplink v-311", "container"), ("st", "State updater", "container"), ("lv", "Live store", "db"), ("lk", "History lake", "db")],
    [("n", "up", "up", "leaves the tunnel: 90 buffered, seq 9,312 – 9,401", "amber"),
     ("m", "up", "st", "latest first: seq 9,402 (now)"),
     ("m", "st", "lv", "seq 9,402: the car jumps to its real place", dict(hl=True)),
     ("m", "up", "st", "backfill: seq 9,312 … 9,401"),
     ("n", "st", "st", "older than 9,402: not live", "green"),
     ("m", "st", "lk", "all 90 into history, in their own minutes", dict(kind="async"))])

c = er.Chen(1960, 900, size=27)
c.entity("veh", 200, 140, "VEHICLE"); c.entity("pos", 700, 140, "POSITION", weak=True); c.entity("cell", 1200, 140, "CELL")
c.entity("ev", 200, 560, "SAFETY EVENT", weak=True); c.entity("trip", 700, 560, "TRIP"); c.entity("view", 1200, 560, "VIEWPORT")
c.rel("rep", 450, 140, "REPORTS", identifying=True); c.rel("in", 950, 140, "IN"); c.rel("raises", 200, 350, "RAISES", identifying=True)
c.rel("on", 700, 350, "ON"); c.rel("covers", 1200, 350, "COVERS")
c.attr("vid", 200, 50, "vehicle_id", of="veh", key=True); c.attr("seq", 600, 50, "seq", of="pos", partial=True); c.attr("t", 800, 50, "t, lat, lng", of="pos")
c.attr("h3", 1200, 50, "h3_id", of="cell", key=True); c.attr("kind", 60, 680, "kind", of="ev")
c.attr("tid", 700, 680, "trip_id", of="trip", key=True); c.attr("z", 1460, 560, "zoom", of="view")
c.link("veh", "rep", "1"); c.link("rep", "pos", "N", total=True)
c.link("pos", "in", "N"); c.link("in", "cell", "1")
c.link("veh", "raises", "1", src="b", dst="t"); c.link("raises", "ev", "N", src="b", dst="t", total=True)
c.link("pos", "on", "N", src="b", dst="t"); c.link("on", "trip", "1", src="b", dst="t")
c.link("view", "covers", "N", src="t", dst="b"); c.link("covers", "cell", "M", src="t", dst="b")
c.legend(1660, 300, size=23, gap=36, rows=["rect", "rect2", "dia", "dia2", "oval", "key", "dbl"])
c.save(OUT / "erd-chen.svg", order=["veh", ("pos", "rep"), ("cell", "in"), ("ev", "raises"), ("trip", "on"), ("view", "covers")])

e = er.ERD(1600, 820, size=22)
e.entity("pos", 30, 40, 470, "positions  (Iceberg)", [("day", "date", "PK"), ("bucket", "0..255", "PK"), ("vehicle_id", "text", "PK"),
         ("seq", "bigint", "PK"), ("t, lat, lng", "ts, float", ""), ("speed, heading", "float", "")], kind="focus", caption="sorted by (vehicle, seq); 52 TB a month")
e.entity("ev", 570, 40, 470, "safety_event", [("vehicle_id", "text", "PK"), ("seq", "bigint", "PK"), ("kind", "text", ""), ("t, lat, lng", "", "")],
         caption="its own topic and table")
e.entity("live", 1110, 40, 460, "live (in memory)", [("vehicle → cell, pos, seq, t", "map", ""), ("cell → vehicles", "map", ""),
         ("cell counts res 6, 7", "map", "")], kind="redis", caption="never written to disk")
e.entity("last", 30, 470, 470, "updater state", [("vehicle_id", "key", "PK"), ("last_seq", "bigint", "")], kind="ext",
         caption="Flink keyed state, checkpointed")
e.entity("sub", 570, 470, 470, "subscription (memory)", [("viewer", "conn", "PK"), ("cells", "set", ""), ("resolution", "6 | 7 | 9", "")], kind="redis",
         caption="per Map API pod")
e.entity("veh", 1110, 470, 460, "vehicle", [("vehicle_id", "text", "PK"), ("city", "int", ""), ("cert", "text", ""), ("fleet", "text", "")],
         caption="registry: from SD-29")
e.save(OUT / "erd-physical.svg", order=["pos", "ev", "live", "last", "sub", "veh"])

def svgdoc(w, h, body): return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" width="{w}" height="{h}">'
                               f'<rect width="{w}" height="{h}" fill="#ffffff"/>{body}</svg>')
def T(x, y, s_, size=24, fill=INK, w=500, anchor="start"):
    return f'<text x="{x}" y="{y}" text-anchor="{anchor}" font-family="{FONT}" font-size="{size}" font-weight="{w}" fill="{ink(fill)}">{esc(s_)}</text>'
def R(x, y, w, h, fill, stroke, rx=10, sw=2.2):
    return f'<rect x="{x:.1f}" y="{y:.1f}" width="{w:.1f}" height="{h:.1f}" rx="{rx}" fill="{fill}" stroke="{stroke}" stroke-width="{sw}"/>'

def tension():
    p = [T(40, 50, "Two products from one stream: the latest position, and every position ever", 28, INK, 800)]
    cards = [("The live map", "where is each vehicle now? overwrite, in memory, by cell", "2 s fresh; loss is fine", BLUE, "#e8f0fe"),
             ("The history", "where was it, every 2 s, for two years? append, columnar", "complete; minutes late is fine", GREEN, "#e6f4ea"),
             ("One table for both", "a database row per position", "slow for one, wrong for the other", RED, "#fce8e6")]
    for i, (t, s_, n, col, fill) in enumerate(cards):
        x = 60 + i * 510
        p += [R(x, 110, 470, 250, fill, col, rx=14), T(x + 24, 160, t, 27, INK, 800)]
        line, yy = "", 205
        for w_ in s_.split():
            if len(line) + len(w_) > 34: p.append(T(x + 24, yy, line, 22, INK, 500)); line, yy = w_, yy + 30
            else: line = (line + " " + w_).strip()
        p += [T(x + 24, yy, line, 22, INK, 500), T(x + 24, 330, n, 22, col, 800)]
    (OUT / "tension.svg").write_text(svgdoc(1600, 400, "".join(p)))
tension()

bs.budget_bar(OUT / "budget.svg", [("gateway + log", 0.3, "edge"), ("updater", 0.3, "service"), ("push tick", 1.0, "data")],
              total=2, unit="s", title="From the server receiving a position to the map showing it (initial target p99 2 s)")
print(sorted(pp.name for pp in OUT.glob("*.svg")))
