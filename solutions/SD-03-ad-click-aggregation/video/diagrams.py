#!/usr/bin/env python3
"""SD-03 event counting and billing rollups: every picture for the video and the written design -> ./svg/*.svg.
One canonical container view (c4svg, since= per box and edge), saved as views: V1 -> V4, flows, the challenge map, badges.
Two component views (the live aggregator, the billing job) carry the challenges. Sequences, both data models, figures.
Run: python3 diagrams.py"""
import html, json, pathlib, sys
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
import stack                       # technology type lines come from ../stack.json

# ───────────────────────────── 1 · the canonical container view ─────────────────────────────────────
# A 5 × 3 grid. Middle row: the intake (clients → collector → log → API ← advertiser). Top row: the live path.
# Bottom row: the billing path. Columns B–D are the system; A and E are outside it.
X = dict(A=20, B=400, C=780, D=1160, E=1540); Y = dict(R0=100, R1=360, R2=620); W, H, SZ = 250, 140, 26
def P(cell): return X[cell[0]], Y[cell[1:]]
BOX = {  # id: (cell, kind, title, type, description, since)
    "src":    ("AR1", "ext", "Ad clients", "SDKs, browsers", "Mint the event ID.", 1),
    "fraud":  ("AR2", "ext", "Fraud system", "External", "Invalidates later.", 3),
    "recon":  ("BR0", "container", "Reconciler", "Service", "Checks the counts.", 4),
    "col":    ("BR1", "container", "Collector", "Service", "Validate, append.", 1),
    "lake":   ("BR2", "db", "Event lake", "Object storage", "By event hour.", 1),
    "stream": ("CR0", "container", "Live aggregator", "Stream job", "Counts by the minute.", 2),
    "log":    ("CR1", "queue", "Event log", "Partitioned log", "The one copy.", 1),
    "batch":  ("CR2", "container", "Billing job", "Batch job", "Exact, per hour.", 1),
    "live":   ("DR0", "db", "Live store", "Columnar store", "Minute rows.", 2),
    "api":    ("DR1", "container", "Reporting API", "Service", "Dashboards, exports.", 1),
    "bill":   ("DR2", "db", "Billing tables", "Versioned table", "The record.", 1),
    "adv":    ("ER1", "person", "Advertiser", "Person", "Watches, is billed.", 1),
    "invo":   ("ER2", "ext", "Invoicing", "External", "Sends the invoices.", 3),
}

def canon(labels=None):
    """The one container diagram. labels: id -> (type, description) to show technologies (5.1) instead."""
    d = c4.Diagram(1810, 830, canon="containers")
    d.boundary(375, 20, 1060, 790, "Ad event counting", "Software System", top="right")
    for k, (cell, kind, t, typ, desc, since) in BOX.items():
        if labels and k in labels: typ, desc = labels[k][1], labels[k][2]
        x, y = P(cell)
        d.node(k, x, y, W, H, kind, t, typ, desc, size=SZ, since=since)
    E = d.edge
    E("src", "col", "events", "HTTPS", src="r", dst="l", at=(335, 412), size=21, eid="s-c")
    E("col", "log", "append", "acks=all", src="r", dst="l", at=(715, 412), size=21, eid="c-l")
    E("log", "stream", "consume", "", src="t", dst="b", at=(960, 300), size=21, eid="l-s", since=2)
    E("stream", "live", "minute rows", "", src="r:0.3", dst="l:0.3", at=(1095, 128), size=21, eid="s-v", since=2)
    E("log", "lake", "files, 5 min", "", src="b:0.3", dst="t:0.7", via=[(855, 560), (575, 560)], at=(715, 548), size=21, eid="l-k")
    E("lake", "batch", "hour H", "", src="r:0.4", dst="l:0.4", at=(715, 660), size=21, eid="k-b")
    E("batch", "bill", "replace, v+1", "", src="r:0.6", dst="l:0.6", at=(1095, 690), size=21, eid="b-i")
    E("batch", "live", "final hours", "", src="r:0.2", dst="l:0.8", via=[(1095, 648), (1095, 212)], at=(1095, 290), size=21, eid="b-v", since=2)
    E("api", "bill", "billed hours", "", src="b", dst="t", at=(1350, 560), size=21, eid="a-i", until=1)
    E("api", "live", "query", "", src="t", dst="b", at=(1330, 300), size=21, eid="a-v", since=2)
    E("adv", "api", "dashboards", "HTTPS", src="l", dst="r", at=(1475, 412), size=21, eid="d-a")
    E("bill", "invo", "final", "", src="r", dst="l", at=(1475, 670), size=21, eid="i-v", since=3)
    E("fraud", "batch", "invalidations", "", src="b", dst="b", via=[(145, 785), (905, 785)], at=(520, 785), size=21, width=400, eid="f-b", since=3)
    E("recon", "live", "live against final, per hour", "", src="t", dst="t", via=[(525, 70), (1285, 70)], at=(905, 66), size=21, width=420, eid="r-v", since=4)
    E("recon", "col", "accepted", "", src="b", dst="t", at=(585, 300), size=21, eid="r-c", since=4)
    d.legend(30, 120, ("person", "container", "db", "queue", "ext"), vertical=True)
    return d

d = canon()
REQ_ORDER = ["src", "col", "log", "stream", "live", "lake", "batch", "bill", "api", "adv", "fraud", "invo", "recon"]
d.save(OUT / "base-v1.svg", upto=1, order=["src", "col", "log", "lake", "batch", "bill", "api", "adv"])   # the one full drawing
d.save(OUT / "base-v2.svg", upto=2, new=2, order=["stream", "live"])
d.save(OUT / "base-v3.svg", upto=3, new=3, order=["fraud", "invo"])
d.save(OUT / "base-v4.svg", upto=4, new=4, order=["recon"])
d.save(OUT / "flow-live.svg", upto=3, flow=["s-c", "c-l", "l-s", "s-v", "d-a", "a-v"])
d.save(OUT / "flow-bill.svg", upto=3, flow=["l-k", "k-b", "b-i", "b-v", "i-v"])
d.save(OUT / "map.svg", upto=3, attack=["col", "stream", "batch", "bill", "api"], keep=None)
d.save(OUT / "ch6-attack.svg", upto=3, attack=["api"], keep=["stream", "live", "api", "adv"])
d.save(OUT / "recap.svg", upto=4, badges={"col": "ID kept", "stream": "M1 M2 M4 M5", "live": "M3 replace",
                                          "batch": "M1 M2 M3", "bill": "versions", "recon": "canaries"})
d.save(OUT / "alt.svg", upto=1, attack=["lake", "batch", "bill"], keep=["src", "col", "api", "adv", "lake", "batch", "bill"])
# 5.1: the same picture, the type lines naming the products (labels from stack.json), shown as a badge-free delta
dt = canon(stack.C4)
dt.save(OUT / "c4-containers-tech.svg", upto=3, focus=["col", "log", "stream", "live", "lake", "batch", "bill"], keep=None)

# ───────────────────────────── 2 · C4 context ────────────────────────────────────────────────────────
x = c4.Diagram(1600, 700)
x.node("cli", 40, 80, 320, 150, "ext", "Ad clients", "SDKs, browsers, ad servers", "Report impressions and clicks.", size=26)
x.node("adv", 40, 440, 320, 150, "person", "Advertiser", "Person", "Watches campaigns; is billed.", size=26)
x.node("sys", 620, 250, 380, 190, "system", "Ad event counting", "Software System", "Live counts; exact hourly totals.", size=28)
x.node("fr", 1240, 80, 320, 150, "ext", "Fraud system", "External system", "Flags invalid traffic, even late.", size=26)
x.node("inv", 1240, 440, 320, 150, "ext", "Invoicing", "External system", "Turns final hours into invoices.", size=26)
x.edge("cli", "sys", "events, batched", "HTTPS", src="r", dst="l:0.25", at=(490, 160), size=22)
x.edge("adv", "sys", "dashboards", "HTTPS", src="r", dst="l:0.75", at=(490, 520), size=22)
x.edge("fr", "sys", "invalidations", "events", src="l", dst="r:0.25", at=(1120, 160), size=22)
x.edge("sys", "inv", "final hours", "batch export", src="r:0.75", dst="l", at=(1120, 520), size=22)
x.legend(40, 660, ("person", "system", "ext"))
x.save(OUT / "c4-context.svg", order=["cli", "sys", "adv", "fr", "inv"])

# ───────────────────────────── 3 · component views (C4 level 3) ──────────────────────────────────────
CX = [20, 300, 560, 820, 1080, 1340, 1600]; CW, CH, CS = 210, 150, 25
def comp(name_box, techline):
    d = c4.Diagram(1830, 770, canon="comp:" + name_box)
    d.boundary(275, 40, 1300, 700, name_box, techline, top="left")
    return d

s = comp("Live aggregator", "Container: Flink, streaming")
s.node("log", CX[0], 330, 200, CH, "queue", "Event log", "Kafka", "By event ID.", size=CS)
s.node("srcop", CX[1], 330, CW, CH, "component", "Kafka source", "Component", "Offsets in the checkpoint.", size=CS)
s.node("time", CX[2], 330, CW, CH, "component", "Time assigner", "Component", "Clamp; watermark.", size=CS)
s.node("dedup", CX[3], 330, CW, CH, "component", "Deduplicator", "Keyed by ID", "TTL 10 minutes.", size=CS)
s.node("comb", CX[4], 330, CW, CH, "component", "Combiner", "Per subtask", "Sums every 1 s.", size=CS)
s.node("win", CX[5], 330, CW, CH, "component", "Window counter", "Event time", "Ad × minute.", size=CS)
s.node("late", CX[4], 90, CW, CH, "component", "Late output", "Side output", "Counted, not added.", size=CS)
s.node("hll", CX[5], 90, CW, CH, "component", "Reach sketch", "HyperLogLog", "Per campaign-minute.", size=CS)
s.node("ckpt", 560, 570, 470, 130, "db", "Checkpoints", "Object storage", "State + offsets, every 30 s.", size=CS)
s.node("sink", CX[5], 570, CW, CH, "component", "Store sink", "Component", "Versioned rows.", size=CS)
s.node("live", CX[6], 570, 210, CH, "db", "Live store", "ClickHouse", "", size=CS)
s.edge("log", "srcop", "", "", src="r", dst="l")
s.edge("srcop", "time", "", "", src="r", dst="l")
s.edge("time", "dedup", "", "", src="r", dst="l")
s.edge("dedup", "comb", "", "", src="r", dst="l")
s.edge("comb", "win", "", "", src="r", dst="l")
s.edge("win", "hll", "", "", src="t", dst="b")
s.edge("win", "late", "", "", src="t:0.15", dst="b:0.85", via=[(1371, 280), (1258, 280)])
s.edge("win", "sink", "", "", src="b", dst="t")
s.edge("sink", "live", "", "", src="r", dst="l")
s.edge("dedup", "ckpt", "state", "", src="b", dst="t:0.55", at=(870, 532), size=21)
s.edge("srcop", "ckpt", "offsets", "", src="b", dst="l:0.5", via=[(405, 635)], at=(470, 620), size=21)
s.legend(40, 120, ("component", "db", "queue"), vertical=True)
SO = ["log", "srcop", "time", "dedup", "comb", "win", "hll", "late", "sink", "live", "ckpt"]
s.save(OUT / "c4-comp-stream.svg", order=SO)                                         # its one full drawing
s.save(OUT / "ch1-attack.svg", keep=["log", "srcop", "time", "dedup", "comb", "win"], attack=["dedup"])
s.save(OUT / "ch1-fix.svg", keep=["log", "srcop", "dedup", "ckpt"], fix=["dedup", "ckpt"])
s.save(OUT / "ch2-attack.svg", keep=["srcop", "time", "win"], attack=["time"])
s.save(OUT / "ch2-fix.svg", keep=["time", "dedup", "comb", "win"], fix=["time", "win"])
s.save(OUT / "ch3-attack.svg", keep=["dedup", "comb", "win", "sink"], attack=["win"])
s.save(OUT / "ch3-fix.svg", keep=["comb", "win"], fix=["comb", "win"])
s.save(OUT / "ch4-attack.svg", keep=["srcop", "win", "sink", "live", "ckpt"], attack=["sink"])
s.save(OUT / "ch4-fix.svg", keep=["srcop", "win", "sink", "live", "ckpt"], fix=["sink", "live"])

b = comp("Billing job", "Container: Flink, batch mode")
b.node("lake", CX[0], 330, 200, CH, "db", "Event lake", "Iceberg", "By event hour.", size=CS)
b.node("close", CX[1], 90, CW, CH, "component", "Hour closer", "Scheduler", "At H + 48 h; dirty hours.", size=CS)
b.node("read", CX[1], 330, CW, CH, "component", "Reader", "Component", "Hour H, pinned.", size=CS)
b.node("dedup", CX[2], 330, CW, CH, "component", "Exact dedup", "Component", "First per ID.", size=CS)
b.node("filt", CX[3], 330, CW, CH, "component", "Invalid filter", "Anti-join", "Pinned list.", size=CS)
b.node("inval", CX[3], 90, CW, CH, "queue", "Invalidations", "Kafka topic", "Append-only.", size=CS)
b.node("agg", CX[4], 330, CW, CH, "component", "Price + sum", "Component", "Integer micros.", size=CS)
b.node("rates", CX[4], 90, CW, CH, "db", "Rate cards", "Versioned", "", size=CS)
b.node("write", CX[5], 330, CW, CH, "component", "Writer", "Iceberg commit", "Writes v + 1.", size=CS)
b.node("adj", CX[5], 570, CW, CH, "component", "Adjuster", "Component", "New − invoiced.", size=CS)
b.node("bill", CX[6], 330, 210, CH, "db", "Billing tables", "Iceberg", "", size=CS)
b.node("invo", CX[6], 570, 210, CH, "ext", "Invoicing", "External", "", size=CS)
b.edge("close", "read", "manifest", "", src="b", dst="t", at=(470, 280), size=21)
b.edge("lake", "read", "", "", src="r", dst="l")
b.edge("read", "dedup", "", "", src="r", dst="l")
b.edge("dedup", "filt", "", "", src="r", dst="l")
b.edge("inval", "filt", "", "", src="b", dst="t")
b.edge("inval", "close", "dirty hours", "", src="l", dst="r", at=(665, 140), size=21)
b.edge("filt", "agg", "", "", src="r", dst="l")
b.edge("rates", "agg", "", "", src="b", dst="t")
b.edge("agg", "write", "", "", src="r", dst="l")
b.edge("write", "bill", "", "", src="r", dst="l")
b.edge("write", "adj", "", "", src="b", dst="t")
b.edge("adj", "invo", "", "", src="r", dst="l")
b.legend(40, 120, ("component", "db", "queue", "ext"), vertical=True)
BO = ["lake", "close", "read", "dedup", ("inval", "filt"), ("rates", "agg"), "write", "bill", "adj", "invo"]
b.save(OUT / "c4-comp-billing.svg", order=BO)                                          # its one full drawing
b.save(OUT / "ch2-close.svg", keep=["close", "read", "lake"], fix=["close"])
b.save(OUT / "ch4-rerun.svg", keep=["close", "read", "write", "bill"], fix=["close", "write"])
b.save(OUT / "ch5-attack.svg", keep=["inval", "filt", "write", "bill", "invo"], attack=["write"])
b.save(OUT / "ch5-fix.svg", keep=["adj", "invo"], fix=["adj"])

# ───────────────────────────── 4 · sequences ─────────────────────────────────────────────────────────
def seq(name, parts, steps, size=24, row=54, width=1500):
    q = sq.Seq(width, size=size, row=row)
    for p in parts: q.part(*p)
    for st in steps:
        k = st[0]
        if k == "m": q.msg(st[1], st[2], st[3], **(st[4] if len(st) > 4 else {}))
        elif k == "r": q.ret(st[1], st[2], st[3], **(st[4] if len(st) > 4 else {}))
        elif k == "n": q.note(st[1], st[2], st[3], *(st[4:5]))
    q.save(OUT / f"{name}.svg")

seq("seq-ingest",
    [("sdk", "Ad SDK", "person"), ("col", "Collector", "container"), ("kf", "Kafka: events.raw", "queue")],
    [("m", "sdk", "col", "POST /v1/events: 500 events, IDs minted at creation"),
     ("n", "col", "col", "validate; stamp server time; clamp a skewed client time", "amber"),
     ("m", "col", "kf", "produce, key = event ID, acks=all"),
     ("r", "kf", "col", "ack: 2 of 3 replicas have it"),
     ("r", "col", "sdk", "202 accepted: 500", dict(hl=True)),
     ("n", "sdk", "sdk", "no answer? retry the same batch: same IDs", "amber")])

seq("seq-live",
    [("kf", "Kafka", "queue"), ("fl", "Flink job", "container"), ("ch", "ClickHouse", "db"), ("api", "Reporting API", "container"), ("adv", "Advertiser", "person")],
    [("m", "kf", "fl", "events, partitioned by event ID", dict(kind="async")),
     ("n", "fl", "fl", "drop a seen ID; partial sums each second", "amber"),
     ("n", "fl", "fl", "ad × minute window: early result every 2 s", "blue"),
     ("m", "fl", "ch", "rows (ad, minute, n, version)"),
     ("m", "adv", "api", "GET …/campaigns/42/live"),
     ("m", "api", "ch", "argMax by version, sum the shards"),
     ("r", "ch", "api", "60 rows"),
     ("r", "api", "adv", "counts as of 14:05:07, provisional", dict(hl=True))])

seq("seq-bill",
    [("cl", "Hour closer", "container"), ("lk", "Event lake", "db"), ("job", "Billing job", "container"), ("bt", "Billing tables", "db"), ("inv", "Invoicing", "ext")],
    [("n", "cl", "cl", "hour 14:00 closes at 14:00 + 48 h", "amber"),
     ("m", "cl", "lk", "snapshot of hour 14:00 as of the cutoff"),
     ("r", "lk", "cl", "snapshot 7,342,118"),
     ("m", "cl", "job", "run(snapshot, rate card v18, invalidations v903, image)"),
     ("n", "job", "job", "exact dedup; drop invalid; price in micros; sum", "blue"),
     ("m", "job", "bt", "replace hour 14:00 as version 1, with its manifest"),
     ("m", "bt", "inv", "final hour, version 1", dict(kind="async", hl=True))])

seq("seq-correct",
    [("fr", "Fraud system", "ext"), ("iv", "Invalidations", "queue"), ("cl", "Hour closer", "container"), ("job", "Billing job", "container"), ("inv", "Invoicing", "ext")],
    [("m", "fr", "iv", "invalidate 3.1 M clicks: botnet 17, with their hours"),
     ("m", "iv", "cl", "hours from 4 Oct 13:00 marked dirty", dict(kind="async")),
     ("m", "cl", "job", "re-run each dirty hour, new manifest"),
     ("n", "job", "job", "write version 2 of each hour; v1 stays", "green"),
     ("n", "job", "job", "version 2 − invoiced version 1 = −$1.55 M", "amber"),
     ("m", "job", "inv", "adjustment lines on the next invoice", dict(hl=True))])

seq("seq-th-watermark",
    [("p1", "Partition 1", "queue"), ("p2", "Partition 2", "queue"), ("w", "Window: ad 77, 14:00", "container"), ("ch", "Live store", "db")],
    [("m", "p1", "w", "impression, event time 14:00:58", dict(kind="async")),
     ("m", "p2", "w", "impression, event time 14:01:30", dict(kind="async")),
     ("n", "w", "w", "watermark = min over partitions of (latest − 2 min) = 13:58:58", "blue"),
     ("m", "w", "ch", "early result: 1,212, version 1"),
     ("m", "p1", "w", "impression, event time 14:03:05", dict(kind="async")),
     ("m", "p2", "w", "impression, event time 14:03:40", dict(kind="async")),
     ("n", "w", "w", "watermark 14:01:05 passes 14:01: the minute is complete", "green"),
     ("m", "w", "ch", "on time: 1,318, version 2 replaces version 1", dict(hl=True)),
     ("m", "p1", "w", "late: event time 14:00:40, within the hour", dict(kind="async")),
     ("m", "w", "ch", "update: 1,319, version 3")])

seq("seq-ch1-retry",
    [("sdk", "Ad SDK", "person"), ("col", "Collector", "container"), ("kf", "Kafka partition 311", "queue"), ("fl", "Deduplicator", "container")],
    [("m", "sdk", "col", "batch B17 (click e7f3…)"),
     ("m", "col", "kf", "append: offset 81,220"),
     ("r", "kf", "col", "ack"),
     ("n", "col", "sdk", "202 lost on the cell network", "amber"),
     ("m", "sdk", "col", "retry B17: the same IDs"),
     ("m", "col", "kf", "append: offset 81,977 (same key, same partition)"),
     ("m", "kf", "fl", "both records", dict(kind="async")),
     ("n", "fl", "fl", "e7f3 is in state since 81,220: drop the second", "green"),
     ("n", "fl", "fl", "billing job: first row per event ID in hour 10:00", "green")])

seq("seq-ch4-replay",
    [("op", "On-call", "person"), ("fl", "Flink, new build", "container"), ("ch", "ClickHouse", "db"), ("job", "Billing job", "container"), ("bt", "Billing tables", "db")],
    [("m", "op", "fl", "redeploy; rewind offsets to 10:00"),
     ("m", "fl", "ch", "minutes 10:00 – 14:00 again, higher versions"),
     ("n", "ch", "ch", "same key, higher version: replaces, does not add", "green"),
     ("m", "op", "job", "re-run hour 10:00 with its manifest"),
     ("m", "job", "bt", "identical rows: the commit changes nothing", dict(hl=True))])

# ───────────────────────────── 5 · data models ───────────────────────────────────────────────────────
c = er.Chen(1960, 900, size=27)
c.entity("adv", 200, 140, "ADVERTISER"); c.entity("cmp", 700, 140, "CAMPAIGN"); c.entity("ad", 1200, 140, "AD")
c.entity("ev", 1200, 560, "EVENT"); c.entity("hr", 700, 560, "HOUR TOTAL", weak=True); c.entity("inv", 1200, 830, "INVALIDATION")
c.rel("runs", 450, 140, "RUNS"); c.rel("has", 950, 140, "HAS"); c.rel("rec", 1200, 350, "RECEIVES")
c.rel("cnt", 950, 560, "COUNTED IN"); c.rel("tot", 700, 350, "BILLED AS", identifying=True); c.rel("voids", 1200, 700, "VOIDS")
c.attr("aid", 200, 50, "advertiser_id", of="adv", key=True)
c.attr("cid", 700, 50, "campaign_id", of="cmp", key=True)
c.attr("adid", 1200, 50, "ad_id", of="ad", key=True)
c.attr("eid", 1440, 480, "event_id", of="ev", key=True); c.attr("et", 1460, 580, "event_time", of="ev"); c.attr("imp", 1500, 650, "impression_id", of="ev")
c.attr("hh", 560, 700, "hour", of="hr", partial=True); c.attr("ver", 840, 700, "version", of="hr", partial=True); c.attr("n", 700, 790, "n, cost", of="hr", derived=True)
c.attr("why", 1460, 830, "reason", of="inv")
c.link("adv", "runs", "1"); c.link("runs", "cmp", "N")
c.link("cmp", "has", "1"); c.link("has", "ad", "N")
c.link("ad", "rec", "1", src="b", dst="t"); c.link("rec", "ev", "N", src="b", dst="t")
c.link("ev", "cnt", "N"); c.link("cnt", "hr", "1")
c.link("cmp", "tot", "1", src="b", dst="t"); c.link("tot", "hr", "N", src="b", dst="t", total=True)
c.link("inv", "voids", "1", src="t", dst="b"); c.link("voids", "ev", "N", src="t", dst="b")
c.legend(1660, 70, size=23, gap=36, rows=["rect", "rect2", "dia", "dia2", "oval", "key", "ovald", "dbl"])
c.note(1580, 420, 360, "An hour is never edited: a correction is a new version.")
c.save(OUT / "erd-chen.svg", order=["adv", ("cmp", "runs"), ("ad", "has"), ("ev", "rec"), ("hr", "cnt", "tot"), ("inv", "voids")])

e = er.ERD(1600, 820, size=22)
e.entity("ev", 30, 40, 470, "events  (Iceberg)", [("event_id", "uuid", "PK"), ("type", "imp | click", ""), ("impression_id", "uuid", "IX"),
         ("ad_id", "bigint", ""), ("event_time", "ts", ""), ("server_ts", "ts", ""), ("clamped", "bool", "")],
         kind="focus", caption="partitioned by event hour; 0.6 PB a month")
e.entity("bh", 570, 40, 470, "billing_hour  (Iceberg)", [("campaign_id", "bigint", "PK"), ("ad_id", "bigint", "PK"), ("hour", "ts", "PK"),
         ("version", "int", "PK"), ("clicks", "bigint", ""), ("cost_micros", "bigint", ""), ("manifest_id", "uuid", "FK")],
         caption="a correction adds a version; none is edited")
e.entity("mf", 1110, 40, 460, "manifest", [("manifest_id", "uuid", "PK"), ("events_snapshot", "bigint", ""), ("rate_card_v", "int", ""),
         ("invalid_snapshot", "bigint", ""), ("image_digest", "text", "")], kind="ext", caption="what one run read")
e.entity("lm", 30, 470, 470, "live_minute  (ClickHouse)", [("campaign_id, ad_id", "bigint", "PK"), ("minute", "ts", "PK"), ("shard", "uint8", "PK"),
         ("impressions, clicks", "uint64", ""), ("version", "uint64", "")], kind="redis", caption="ReplacingMergeTree by version")
e.entity("iv", 570, 470, 470, "invalidation", [("event_id", "uuid", "PK"), ("hour", "ts", "IX"), ("reason", "text", ""), ("detected_at", "ts", "")],
         caption="append-only")
e.entity("aj", 1110, 470, 460, "adjustment", [("campaign_id", "bigint", "PK"), ("hour", "ts", "PK"), ("to_version", "int", "PK"), ("delta_micros", "bigint", "")],
         caption="what invoicing applies")
e.rel("bh", "mf", "N", "1", src="r:0.8", dst="l:0.5", label="")
e.rel("iv", "ev", "N", "1", src="l:0.25", dst="b:0.87", via=[(439, 530)], label="")
e.rel("aj", "bh", "N", "1", src="t:0.3", dst="b:0.6", label="")
e.save(OUT / "erd-physical.svg", order=["ev", "bh", "mf", "lm", "iv", "aj"])

# ───────────────────────────── 6 · figures ───────────────────────────────────────────────────────────
def svgdoc(w, h, body): return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" width="{w}" height="{h}">'
                               f'<rect width="{w}" height="{h}" fill="#ffffff"/>{body}</svg>')
def T(x, y, s, size=24, fill=INK, w=500, anchor="start"):
    return f'<text x="{x}" y="{y}" text-anchor="{anchor}" font-family="{FONT}" font-size="{size}" font-weight="{w}" fill="{ink(fill)}">{esc(s)}</text>'
def R(x, y, w, h, fill, stroke, rx=10, sw=2.2):
    return f'<rect x="{x:.1f}" y="{y:.1f}" width="{w:.1f}" height="{h:.1f}" rx="{rx}" fill="{fill}" stroke="{stroke}" stroke-width="{sw}"/>'
def L(x1, y1, x2, y2, col=INK, sw=2.4, dash=False):
    return f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="{col}" stroke-width="{sw}"{" stroke-dasharray=\"8 6\"" if dash else ""}/>'

def tension():
    """One hour's number, three times: fast and provisional, exact and final, corrected."""
    p = [T(40, 50, "One hour's number, three times: each later one is slower, more exact, and the one that counts", 28, INK, 800)]
    stages = [("+10 s", "Live", "1,319,402", "provisional: duplicates within 10 min removed; late events still coming", BLUE, "#e8f0fe"),
              ("+48 h", "Final, version 1", "1,318,977", "exact: every duplicate removed, late events in; invoiced", GREEN, "#e6f4ea"),
              ("+9 days", "Version 2", "1,291,045", "fraud invalidated 2 %: an adjustment line, never an edit", AMBER, "#fef7e0")]
    for i, (t, name, n, note, col, fill) in enumerate(stages):
        x = 60 + i * 510
        p += [R(x, 110, 470, 250, fill, col, rx=14), T(x + 24, 160, t, 30, col, 800), T(x + 24, 205, name, 26, INK, 800),
              T(x + 24, 258, n, 34, INK, 800)]
        words, line, ys = note.split(), "", 300
        for w_ in words:
            if len(line) + len(w_) > 36: p.append(T(x + 24, ys, line, 21, INK, 500)); line, ys = w_, ys + 28
            else: line = (line + " " + w_).strip()
        p.append(T(x + 24, ys, line, 21, INK, 500))
        if i < 2: p.append(f'<path d="M{x+480},235 l22,0" stroke="{GREY}" stroke-width="3" marker-end="url(#ar)"/>')
    p.insert(0, f'<defs><marker id="ar" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="8" markerHeight="8" orient="auto"><path d="M0,1 L10,5 L0,9 z" fill="{GREY}"/></marker></defs>')
    p += [L(60, 420, 1540, 420, BLUE, 4), T(60, 462, "← faster, cheaper, provisional", 24, BLUE, 800),
          T(1540, 462, "exact, auditable, billed →", 24, GREEN, 800, "end")]
    (OUT / "tension.svg").write_text(svgdoc(1600, 490, "".join(p)))
tension()

def combiner():
    """Two-stage aggregation for the hot ad: 512 partial sums a second instead of 2 million updates on one key."""
    p = [T(40, 48, "One ad at 2,000,000 impressions a second: combine where the events are, then merge 512 partial sums", 27, INK, 800)]
    for i in range(4):
        y = 100 + i * 105
        lab = f"subtask {i*170+1 if i < 3 else 512}"
        p += [R(60, y, 330, 80, "#e8f0fe", BLUE), T(225, y + 50, ("…  " if i == 3 else "") + lab, 23, INK, 700, "middle"),
              L(392, y + 40, 640, y + 40, GREY, 2.4), T(516, y + 30, "~3,900 events/s", 20, GREY, 600, "middle"),
              R(640, y, 330, 80, "#fef7e0", AMBER), T(805, y + 35, "partial sum, 1 s", 22, INK, 700, "middle"),
              T(805, y + 63, "ad 77 · 14:05 · +3,906", 20, "#b06000", 600, "middle"), L(972, y + 40, 1180, 260, GREY, 2.4)]
    p += [R(1180, 200, 360, 120, "#e6f4ea", GREEN, rx=14), T(1360, 250, "merge by (ad, minute)", 24, INK, 800, "middle"),
          T(1360, 288, "512 updates a second", 22, "#188038", 700, "middle")]
    p += [T(40, 545, "The hot key's cost moves from 2 million updates on one thread to 512 small messages. No event waits for another.", 23, INK, 700)]
    (OUT / "combiner.svg").write_text(svgdoc(1600, 580, "".join(p)))
combiner()

bs.budget_bar(OUT / "budget.svg", [("SDK batching", 1.0, "client"), ("collector + log", 0.5, "edge"), ("early firing", 2.0, "service"),
                                   ("store insert", 1.0, "data"), ("query", 1.0, "cache")],
              total=10, unit="s", title="From an impression to the dashboard, worst case (initial target p99 10 s)")

print(sorted(p.name for p in OUT.glob("*.svg")))
