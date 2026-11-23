#!/usr/bin/env python3
"""SD-96 URL shortener: every picture for the video and the written design -> ./svg/*.svg.
One carried baseline (declared once), numbered flows, challenge overlays, C4, sequences, ERDs, figures.
Run: python3 diagrams.py"""
import html, pathlib, sys
sys.path.insert(0, str(pathlib.Path.home() / ".claude/skills/slide-video-kit/scripts"))
import basesvg as bs
import c4svg as c4
import seqsvg as sq
import erdsvg as er
from gtheme import ink

OUT = pathlib.Path(__file__).resolve().parent / "svg"; OUT.mkdir(exist_ok=True)
FONT = "Inter, Roboto, sans-serif"
INK, RED, GREEN, BLUE, PURPLE, GREY, AMBER = "#202124", "#ea4335", "#34a853", "#4285f4", "#1967d2", "#5f6368", "#fbbc05"
def esc(s): return html.escape(str(s))

# ───────────────────────────── 1 · the carried baseline ──────────────────────────────────────────────
# Three rows: create path on top, redirect path in the middle (the product), side paths along the bottom.
b = bs.Baseline(1600, 760)
b.node("user", 20, 300, 200, 130, "client", "Browser / API", "clicks · creates")
b.node("edge", 350, 300, 200, 130, "edge", "Edge (CDN)", "302 cached 60 s", since=3)
b.node("redir", 680, 300, 200, 130, "service", "Redirect service", "stateless, many")
b.node("cache", 1010, 300, 200, 130, "cache", "Shared cache", "hot codes", since=2)
b.node("store", 1340, 300, 200, 130, "data", "Link store", "code → URL", shape="db")
b.node("create", 680, 70, 200, 100, "service", "Create service", "codes · aliases", since=2)
b.node("alloc", 1010, 60, 200, 110, "data", "Allocator", "ID ranges", since=2, shape="db")
b.node("safety", 350, 70, 200, 100, "ext", "Safety check", "known-bad URLs", since=3)
b.node("clog", 680, 560, 200, 100, "queue", "Click log", "by code", since=3, shape="queue")
b.node("agg", 1010, 560, 200, 100, "service", "Aggregator", "per minute", since=3)
b.node("stats", 1340, 560, 200, 100, "data", "Stats store", "day · country", since=3, shape="db")
b.node("take", 20, 560, 200, 100, "service", "Takedown", "owner · trust", since=3)
b.node("inval", 350, 560, 200, 100, "queue", "Invalidation", "channel", since=3, shape="queue")
# tags: only inside a challenge, a flow or the recap
b.node("probe", 20, 70, 200, 100, "ext", "Probes", "every region", tag="ch8")
b.node("replica", 1340, 60, 200, 110, "data", "Replica", "other region", shape="db", tag="ch7")

REQ = dict(src="r:0.25", dst="l:0.25"); RSP = dict(src="l:0.75", dst="r:0.75", kind="resp")
# V1: one service does both, straight to the table
b.edge("u-r1", "user", "redir", "GET /code · POST", until=1, **REQ, at=(450, 322))
b.edge("u-r2", "user", "redir", "GET /code", since=2, until=2, **REQ, at=(450, 322))
b.edge("r-u1", "redir", "user", "302", until=2, **RSP, at=(450, 420))
b.edge("r-s1", "redir", "store", "SELECT", until=1, **REQ, at=(1110, 322))
b.edge("s-r1", "store", "redir", "URL", until=1, **RSP, at=(1110, 420))
# V2+: split paths, cache-aside
b.edge("r-c", "redir", "cache", "get", since=2, **REQ, at=(945, 322))
b.edge("c-r", "cache", "redir", "URL", since=2, **RSP, at=(945, 420))
b.edge("c-s", "cache", "store", "miss", since=2, **REQ, at=(1275, 322))
b.edge("s-c", "store", "cache", "fill", since=2, **RSP, at=(1275, 420))
b.edge("u-cr", "user", "create", "POST /links", src="t:0.8", dst="b:0.1", via=[(180, 236), (700, 236)], since=2, at=(440, 224))
b.edge("cr-a", "create", "alloc", "lease", src="r:0.3", dst="l:0.3", since=2, at=(945, 88))
b.edge("cr-s", "create", "store", "INSERT, unique", src="b:0.8", dst="t:0.5", via=[(840, 262), (1440, 262)], since=2, at=(1180, 250))
# V3: edge in front, side paths
b.edge("u-e", "user", "edge", "GET /code", since=3, **REQ, at=(285, 322))
b.edge("e-u", "edge", "user", "302", since=3, **RSP, at=(285, 420))
b.edge("e-r", "edge", "redir", "miss", since=3, **REQ, at=(615, 322))
b.edge("r-e", "redir", "edge", "302", since=3, **RSP, at=(615, 420))
b.edge("cr-sf", "create", "safety", "check URL", src="l:0.3", dst="r:0.3", since=3, at=(615, 88))
b.edge("r-cl", "redir", "clog", "click, after", src="b:0.5", dst="t:0.5", kind="async", since=3, at=(845, 500))
b.edge("cl-ag", "clog", "agg", "batches", src="r:0.5", dst="l:0.5", kind="async", since=3, at=(945, 588))
b.edge("ag-st", "agg", "stats", "counts", src="r:0.5", dst="l:0.5", since=3, at=(1275, 588))
b.edge("t-i", "take", "inval", "publish", src="r:0.5", dst="l:0.5", kind="async", since=3, at=(285, 588))
b.edge("i-e", "inval", "edge", "purge", src="t:0.5", dst="b:0.5", kind="async", since=3, at=(495, 500))
b.edge("i-r", "inval", "redir", "drop", src="t:0.85", dst="b:0.1", via=[(520, 490), (700, 490)], kind="async", since=3, at=(610, 478))
b.edge("i-c", "inval", "cache", "delete", src="b:0.5", dst="b:0.5", via=[(450, 700), (945, 700), (945, 470), (1110, 470)], kind="async", since=3, at=(700, 712))
b.edge("t-s", "take", "store", "status = blocked", src="b:0.5", dst="r:0.5", via=[(120, 740), (1575, 740), (1575, 365)], since=3, at=(1180, 728))
b.edge("s-rep", "store", "replica", "replicate", src="t:0.5", dst="b:0.5", kind="async", tag="ch7", at=(1505, 236))
b.edge("p-u", "probe", "user", "create, follow", src="b:0.3", dst="t:0.3", tag="ch8", at=(140, 236))

def sv(name, h, order=None, **view):
    b.h = h
    b.save(OUT / name, order=order, **view)

import json
def restep(name, units):
    """Override a figure's default reveal plan (svg/<name>.steps.json): a list of key lists."""
    (OUT / name).with_suffix(".steps.json").write_text(json.dumps(units))
FLOW_ORDER = ["user", "edge", "redir", "cache", "store", "replica", "safety", "create", "alloc", "clog", "agg", "stats", "take", "inval", "probe"]

ALL = ["ch7", "ch8"]
sv("base-v1.svg", 470, upto=1, legend=True)
sv("base-v2.svg", 470, upto=2, new=2, legend=True, order=["cache", "create", "alloc"])
sv("base-v3.svg", 790, upto=3, new=3, legend=True, order=["edge", "safety", "clog", "agg", "stats", "take", "inval"])
sv("base-final.svg", 790, upto=3, show=ALL, legend=True, order=FLOW_ORDER)
sv("map.svg", 790, upto=3, show=ALL, legend=True, attack=["create", "cache", "edge", "clog", "store", "redir"], keep=None)
_m = json.loads((OUT / "map.steps.json").read_text())
restep("map.svg", [_m[0], ["m:create"], ["m:cache"], ["m:edge"], ["m:redir"], ["m:clog"], ["m:store"]])
sv("flow-fr1.svg", 470, upto=3, flow=["u-cr", "cr-sf", "cr-a", "cr-s"], keep=["user", "create", "safety", "alloc", "store"],
   )
sv("flow-fr2.svg", 470, upto=3, flow=["u-e", "e-r", "r-c", "c-s", "s-c", "c-r", "r-e", "e-u"], keep=["user", "edge", "redir", "cache", "store"])
sv("flow-fr3.svg", 680, upto=3, flow=["u-e", "e-r", "r-cl", "cl-ag", "ag-st"], keep=["user", "edge", "redir", "clog", "agg", "stats"])
sv("flow-fr4.svg", 790, upto=3, flow=["t-s", "t-i", "i-c", "i-r", "i-e"], keep=["take", "inval", "edge", "redir", "cache", "store"])
# challenge overlays
sv("ch1-attack.svg", 540, upto=3, attack=["create"], keep=["user", "create", "alloc", "store"], hot=["u-cr", "cr-s"],
   notes=[(40, 470, 1000, "Two servers draw the same code. SELECT says free to both; the second INSERT overwrites.", "red")])
sv("ch1-fix.svg", 540, upto=3, fix=["alloc", "store"], keep=["user", "create", "alloc", "store"], ok=["cr-a", "cr-s"],
   notes=[(40, 470, 1000, "Disjoint leased ranges; UNIQUE(code) decides an alias race: one 201, one 409.", "green")])
sv("ch2-attack.svg", 540, upto=3, attack=["create"], keep=["user", "create", "alloc"], hot=["cr-a"],
   notes=[(40, 470, 1000, "base-62 of a counter is a counter: neighbours are guessable, volume leaks.", "red")])
sv("ch2-fix.svg", 540, upto=3, fix=["create"], keep=["user", "create", "alloc", "store"], ok=["cr-a", "cr-s"],
   notes=[(40, 470, 1000, "ID → keyed permutation → base-62: still unique, neighbours unrelated.", "green")])
sv("ch3-attack.svg", 540, upto=3, attack=["cache", "store"], keep=["user", "edge", "redir", "cache", "store"], hot=["r-c", "c-s"],
   notes=[(40, 470, 1000, "40,000 clicks a second on one code: one shard's tail; a restart sends 8,000 queries to one row.", "red")])
sv("ch3-fix.svg", 540, upto=3, fix=["redir"], keep=["user", "edge", "redir", "cache", "store"], ok=["r-c", "c-r"],
   notes=[(40, 470, 1000, "In-process cache on every server; single flight: one miss per server, not one per click.", "green")])
sv("ch4-attack.svg", 540, upto=3, attack=["user"], keep=["user", "edge", "redir"], hot=["u-e", "e-u"],
   notes=[(40, 470, 1000, "301: the browser answers forever. No click is counted, no takedown can reach it.", "red")])
sv("ch4-fix.svg", 540, upto=3, fix=["edge"], keep=["user", "edge", "redir"], ok=["e-r", "r-e"],
   notes=[(40, 470, 1000, "302 by default; the edge caches 60 s and can be purged; 301 only as an opt-in.", "green")])
sv("ch5-attack.svg", 790, upto=3, attack=["edge", "redir", "cache"], keep=["user", "edge", "redir", "cache", "store", "take"], hot=["t-s"])
sv("ch5-fix.svg", 790, upto=3, fix=["inval"], keep=["take", "inval", "edge", "redir", "cache", "store"], ok=["t-i", "i-e", "i-r", "i-c", "t-s"])
sv("ch6-attack.svg", 540, upto=2, attack=["store"], keep=["user", "redir", "cache", "store"], hot=["r-c", "c-s"],
   notes=[(40, 470, 1000, "UPDATE clicks = clicks + 1 on every redirect: one row, 40,000 a second.", "red")])
sv("ch6-fix.svg", 680, upto=3, fix=["clog", "agg"], keep=["user", "edge", "redir", "clog", "agg", "stats"], ok=["r-cl", "cl-ag", "ag-st"])
sv("ch7-attack.svg", 540, upto=3, attack=["store", "alloc"], keep=["redir", "cache", "store", "create", "alloc"],
   notes=[(40, 470, 1000, "The primary's region is gone: creates fail, misses hit a read-only store.", "red")])
sv("ch7-fix.svg", 540, upto=3, show=["ch7"], fix=["replica"], keep=["redir", "cache", "store", "replica", "create", "alloc"], ok=["s-rep", "c-s"],
   notes=[(40, 470, 1000, "Each region: its replica, its caches, its slice of the ID space.", "green")])
sv("ch8-attack.svg", 540, upto=3, attack=["cache"], keep=["redir", "cache", "store"],
   notes=[(40, 470, 1000, "Shared-cache TTL set to 0: no errors; store reads 40/s → 4,000/s at 02:00.", "red")])
sv("ch8-fix.svg", 540, upto=3, show=["ch8"], fix=["probe"], keep=["probe", "user", "edge", "redir", "cache", "store"], ok=["p-u", "u-e"],
   notes=[(40, 470, 1000, "Probe the path: create, then follow, every minute, every region; read metrics in pairs.", "green")])
bs.budget_bar(OUT / "budget.svg", [("cache", 1, "cache"), ("link store, on a miss", 5, "data"), ("rest", 1.1, "service")],
              total=20, unit="ms", title="One redirect at the server, worst case with a miss (initial target p99 20 ms)")

# ───────────────────────────── 2 · C4 ────────────────────────────────────────────────────────────────
d = c4.Diagram(1600, 820)
d.node("vis", 60, 90, 300, 150, "person", "Visitor", "Person", "Follows a short link from anywhere.")
d.node("own", 60, 520, 300, 150, "person", "Link owner", "Person", "Creates links, reads click stats.")
d.node("sys", 620, 290, 360, 200, "system", "URL shortener", "Software System", "Codes, redirects, counts, takedowns.")
d.node("ts", 1230, 90, 320, 150, "person", "Trust and safety", "Person", "Blocks phishing and malware links.")
d.node("cls", 1230, 520, 320, 150, "ext", "URL classifier", "External system", "Says whether a URL is known-bad.")
d.edge("vis", "sys", "GET /code, gets a 302", "HTTPS", src="r:0.8", dst="l:0.25", at=(480, 255))
d.edge("own", "sys", "Create links, stats", "HTTPS API", src="r:0.2", dst="l:0.8", at=(480, 560))
d.edge("ts", "sys", "Takedown", "console, API", src="l:0.5", dst="t:0.7", at=(1120, 170))
d.edge("sys", "cls", "Is this URL bad?", "HTTPS", src="r:0.7", dst="l:0.3", at=(1110, 440))
d.legend(40, 780, ("person", "system", "ext"))
d.save(OUT / "c4-context.svg", order=["vis", "sys", "own", "ts", "cls"])

d = c4.Diagram(1600, 950)
d.boundary(30, 60, 1180, 780, "URL shortener", "Software System")
d.node("cdn", 60, 330, 230, 160, "container", "Edge", "CDN, bought", "Caches 302s for 60 s; purge API.", size=21)
d.node("rd", 340, 330, 230, 160, "container", "Redirect service", "Stateless service", "In-process cache, single flight.", size=21)
d.node("ca", 620, 330, 230, 160, "container", "Shared cache", "In-memory cache", "Hot codes, cache-aside.", size=21)
d.node("db", 900, 330, 260, 160, "db", "Link store", "Sharded key-value", "code → URL, status. UNIQUE(code).", size=21)
d.node("cs", 620, 90, 230, 150, "container", "Create service", "Service", "Ranges, permutation, aliases.", size=21)
d.node("al", 900, 90, 260, 150, "db", "Range allocator", "Consensus store", "Leases of 1,000 IDs.", size=21)
d.node("pipe", 340, 620, 230, 160, "queue", "Click pipeline", "Log + aggregator", "Per code, per minute.", size=21)
d.node("tk", 620, 620, 230, 160, "container", "Takedown service", "Service", "Status, invalidation, purge.", size=21)
d.node("cl", 1270, 90, 290, 150, "ext", "URL classifier", "External", "Known-bad URLs.")
d.node("vis", 1270, 520, 290, 150, "person", "Visitor", "Person", "Opens a short link.")
d.edge("cdn", "rd", "miss", "HTTPS", src="r", dst="l", at=(315, 310))
d.edge("rd", "ca", "get", "", src="r", dst="l", at=(595, 310))
d.edge("ca", "db", "miss", "", src="r", dst="l", at=(875, 310))
d.edge("cs", "al", "lease", "", src="r", dst="l", at=(875, 140))
d.edge("cs", "db", "INSERT", "", src="b", dst="t:0.2", at=(780, 285))
d.edge("rd", "pipe", "click event", "async", src="b", dst="t", at=(475, 570))
d.edge("tk", "db", "status", "", src="r", dst="b:0.5", via=[(1030, 700)], at=(960, 690))
d.edge("cs", "cl", "check", "HTTPS", src="t:0.7", dst="t:0.5", via=[(781, 50), (1415, 50)], at=(1100, 40))
d.edge("vis", "cdn", "GET /code", "HTTPS", src="b:0.5", dst="b:0.5", via=[(1415, 860), (175, 860)], at=(800, 850))
d.legend(40, 915, ("person", "container", "db", "ext"))
C4_ORDER = ["vis", "cdn", "rd", "ca", "db", "cs", "al", "cl", "pipe", "tk"]
d.save(OUT / "c4-containers.svg", order=C4_ORDER)

def containers(name, labels, order=C4_ORDER, title=None):
    """The same container layout, with other type and description lines (technologies, mechanisms)."""
    d = c4.Diagram(1600, 950)
    d.boundary(30, 60, 1180, 780, "URL shortener", "Software System")
    pos = dict(cdn=(60, 330, 230, 160, "container"), rd=(340, 330, 230, 160, "container"), ca=(620, 330, 230, 160, "container"),
               db=(900, 330, 260, 160, "db"), cs=(620, 90, 230, 150, "container"), al=(900, 90, 260, 150, "db"),
               pipe=(340, 620, 230, 160, "queue"), tk=(620, 620, 230, 160, "container"))
    for k, (x, y, w, h, kind) in pos.items():
        t, typ, desc = labels[k]
        d.node(k, x, y, w, h, kind, t, typ, desc, size=20)
    d.node("cl", 1270, 90, 290, 150, "ext", *labels["cl"])
    d.node("vis", 1270, 520, 290, 150, "person", "Visitor", "Person", "Opens a short link.")
    d.edge("cdn", "rd", "miss", "HTTPS", src="r", dst="l", at=(315, 310))
    d.edge("rd", "ca", "get", "", src="r", dst="l", at=(595, 310))
    d.edge("ca", "db", "miss", "", src="r", dst="l", at=(875, 310))
    d.edge("cs", "al", "lease", "", src="r", dst="l", at=(875, 140))
    d.edge("cs", "db", "INSERT", "", src="b", dst="t:0.2", at=(780, 285))
    d.edge("rd", "pipe", "click event", "async", src="b", dst="t", at=(475, 570))
    d.edge("tk", "db", "status", "", src="r", dst="b:0.5", via=[(1030, 700)], at=(960, 690))
    d.edge("cs", "cl", "check", "HTTPS", src="t:0.7", dst="t:0.5", via=[(781, 50), (1415, 50)], at=(1100, 40))
    d.edge("vis", "cdn", "GET /code", "HTTPS", src="b:0.5", dst="b:0.5", via=[(1415, 860), (175, 860)], at=(800, 850))
    d.legend(40, 915, ("person", "container", "db", "ext"))
    d.save(OUT / name, order=order)

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent / "src"))
import stack                      # labels come from ../stack.json, with the 5.1 slides and the booklet
containers("c4-containers-tech.svg", stack.C4)
containers("th-map.svg", dict(
    cdn=("Edge", "M6 · lifetime", "60 s cache, purgeable."),
    rd=("Redirect service", "M4 · M5", "Layered cache; click after."),
    ca=("Shared cache", "M4 · M6", "Cache-aside; deleted directly."),
    db=("Link store", "M3 · authority", "UNIQUE(code) decides."),
    cs=("Create service", "M1 · M2", "Ranges; keyed permutation."),
    al=("Range allocator", "M1 · consensus", "One CAS per 1,000 IDs."),
    pipe=("Click pipeline", "M5 · async log", "Counted per minute."),
    tk=("Takedown service", "M6 · invalidation", "Status, events, purge."),
    cl=("URL classifier", "External", "Checked on create.")),
    order=[("vis", "cdn", "cl"), "cs", "al", "db", "rd", "ca", "pipe", "tk"])

# component views (C4 level 3): every in-scope block one level deep, with the technology inside it
d = c4.Diagram(1600, 880)
d.boundary(260, 60, 920, 780, "Redirect service", "Container: Go")
d.node("edge", 30, 360, 200, 140, "ext", "Edge", "CDN", "Forwards misses.")
d.node("kinv", 30, 110, 200, 140, "queue", "Invalidations", "Kafka topic", "Codes to drop.")
d.node("inv", 300, 110, 240, 150, "component", "Invalidation listener", "Component", "Own consumer group; rewinds 5 min.")
d.node("lc", 610, 110, 240, 150, "component", "In-process cache", "ristretto", "TinyLFU; 300k codes; 60 s.")
d.node("h", 300, 360, 240, 150, "component", "HTTP handler", "Component", "302 · 404 · 410; headers.")
d.node("res", 610, 360, 240, 150, "component", "Resolver", "singleflight", "One lookup per code.")
d.node("scl", 920, 250, 230, 140, "component", "Cache client", "go-redis cluster", "Slot map; 2 ms timeout.")
d.node("stc", 920, 470, 230, 140, "component", "Store client", "pgx pool", "Code → shard; 20 ms.")
d.node("em", 300, 620, 240, 150, "component", "Click emitter", "Component", "Ring buffer; 1 s batches.")
d.node("redis", 1250, 250, 320, 140, "db", "Shared cache", "Redis Cluster", "")
d.node("pg", 1250, 470, 320, 140, "db", "Link store", "PostgreSQL shards", "")
d.node("kcl", 1250, 680, 320, 130, "queue", "Click log", "Kafka topic", "")
d.edge("edge", "h", "", "", src="r", dst="l")
d.edge("h", "res", "resolve", "", src="r", dst="l", at=(575, 415))
d.edge("res", "lc", "get · put", "", src="t", dst="b", at=(780, 315))
d.edge("res", "scl", "miss", "", src="r:0.3", dst="l:0.5", at=(885, 380))
d.edge("scl", "redis", "", "", src="r", dst="l")
d.edge("res", "stc", "miss", "", src="r:0.75", dst="l:0.5", at=(885, 500))
d.edge("stc", "pg", "", "", src="r", dst="l")
d.edge("h", "em", "after the 302", "", src="b", dst="t", at=(445, 580))
d.edge("em", "kcl", "batch, async", "", src="r", dst="l", at=(900, 725))
d.edge("kinv", "inv", "", "", src="r", dst="l")
d.edge("inv", "lc", "", "", src="r", dst="l")
d.legend(40, 850, ("component", "db", "queue", "ext"))
d.save(OUT / "c4-comp-redirect.svg", order=["edge", "h", "res", "lc", "scl", "redis", "stc", "pg", "em", "kcl", ("kinv", "inv")])

d = c4.Diagram(1600, 880)
d.boundary(260, 60, 920, 780, "Create service", "Container: Go")
d.node("cli", 30, 380, 200, 140, "person", "Integrator", "API client", "Bulk creates.")
d.node("rl", 30, 110, 200, 140, "db", "Rate limits", "Redis", "Token buckets.")
d.node("lim", 300, 110, 240, 150, "component", "Rate limiter", "Component", "Per API key.")
d.node("h", 300, 375, 240, 150, "component", "API handler", "Component", "Idempotency key; 201 · 409 · 422.")
d.node("sf", 300, 640, 240, 150, "component", "Safety client", "Component", "150 ms timeout; breaker.")
d.node("rh", 610, 110, 240, 150, "component", "Range holder", "etcd client", "Next ID; re-lease at half.")
d.node("enc", 610, 375, 240, 150, "component", "Encoder", "Component", "Feistel, then base-62.")
d.node("wr", 920, 375, 230, 150, "component", "Store writer", "pgx", "ON CONFLICT DO NOTHING.")
d.node("etcd", 1250, 110, 320, 140, "db", "Range allocator", "etcd cluster", "")
d.node("pg", 1250, 375, 320, 150, "db", "Link store", "PostgreSQL shard", "")
d.node("wrk", 1250, 650, 320, 130, "ext", "URL classifier", "Web risk API", "")
d.edge("cli", "h", "", "", src="r", dst="l")
d.edge("h", "lim", "allow?", "", src="t", dst="b", at=(470, 320))
d.edge("lim", "rl", "", "", src="l", dst="r")
d.edge("h", "sf", "known-bad?", "", src="b", dst="t", at=(475, 590))
d.edge("sf", "wrk", "lookup", "HTTPS", src="r", dst="l", at=(900, 700))
d.edge("h", "enc", "", "", src="r", dst="l")
d.edge("enc", "rh", "next ID", "", src="t", dst="b", at=(780, 320))
d.edge("rh", "etcd", "Txn: lease 1,000", "gRPC", src="r", dst="l", at=(1010, 160))
d.edge("enc", "wr", "", "", src="r", dst="l")
d.edge("wr", "pg", "", "", src="r", dst="l")
d.legend(40, 850, ("person", "component", "db", "ext"))
d.save(OUT / "c4-comp-create.svg", order=["cli", "h", ("lim", "rl"), ("sf", "wrk"), "enc", ("rh", "etcd"), ("wr", "pg")])

# ───────────────────────────── 3 · sequences ─────────────────────────────────────────────────────────
def seq(name, parts, steps, **kw):
    s = sq.Seq(1500, size=24, row=54, **kw)
    for p in parts: s.part(*p)
    for st in steps:
        k = st[0]
        if k == "m": s.msg(st[1], st[2], st[3], **(st[4] if len(st) > 4 else {}))
        elif k == "r": s.ret(st[1], st[2], st[3], **(st[4] if len(st) > 4 else {}))
        elif k == "n": s.note(st[1], st[2], st[3], *(st[4:5]))
    s.save(OUT / f"{name}.svg")

seq("seq-create",
    [("cl", "Client", "person"), ("cs", "Create service", "container"), ("sf", "Safety check", "ext"), ("db", "Link store", "db")],
    [("m", "cl", "cs", "POST /links {url}, Idempotency-Key"),
     ("m", "cs", "sf", "is this URL known-bad?"),
     ("r", "sf", "cs", "no"),
     ("n", "cs", "cs", "next ID from the leased range; keyed permutation; base-62 → aZ3kQ9x", "green"),
     ("m", "cs", "db", "INSERT (aZ3kQ9x, url)  UNIQUE(code)"),
     ("r", "db", "cs", "ok"),
     ("r", "cs", "cl", "201 · https://sho.rt/aZ3kQ9x", dict(hl=True))])

seq("seq-redirect",
    [("br", "Browser", "person"), ("rd", "Redirect service", "container"), ("ca", "Shared cache", "container"), ("db", "Link store", "db"), ("lg", "Click log", "queue")],
    [("m", "br", "rd", "GET /aZ3kQ9x"),
     ("n", "rd", "rd", "in-process cache: miss", "amber"),
     ("m", "rd", "ca", "get aZ3kQ9x  (~1 ms)"),
     ("r", "ca", "rd", "miss"),
     ("m", "rd", "db", "SELECT url, status WHERE code = aZ3kQ9x"),
     ("r", "db", "rd", "url, live; fill both caches"),
     ("r", "rd", "br", "302 Location: long URL", dict(hl=True)),
     ("m", "rd", "lg", "click event, after the answer", dict(kind="async"))])

seq("seq-count",
    [("rd", "Redirect server", "container"), ("bf", "Local buffer", "db"), ("lg", "Kafka: clicks", "queue"), ("fl", "Flink job", "container"),
     ("ch", "ClickHouse", "db"), ("ow", "Owner's dashboard", "person")],
    [("n", "rd", "rd", "302 already sent", "green"),
     ("m", "rd", "bf", "append {code, country, minute}"),
     ("n", "bf", "bf", "pre-aggregate per code and country each second", "amber"),
     ("m", "bf", "lg", "one batch a second, keyed by code", dict(kind="async")),
     ("m", "lg", "fl", "consume; partitions by code", dict(kind="async")),
     ("n", "fl", "fl", "1-minute windows; 30 s late data allowed", "blue"),
     ("m", "fl", "ch", "INSERT counts (code, minute, country)"),
     ("m", "ow", "ch", "stats for aZ3kQ9x by day"),
     ("r", "ch", "ow", "counts, asOf 14:05", dict(hl=True))])

seq("seq-th-lease",
    [("a", "Create server A", "container"), ("ld", "etcd leader", "db"), ("f1", "etcd follower 1", "db"), ("f2", "etcd follower 2", "db"), ("b", "Create server B", "container")],
    [("m", "a", "ld", "Txn: if mod_rev(next) = 17, put next = 41,000"),
     ("m", "ld", "f1", "append entry 18", dict(kind="async")),
     ("m", "ld", "f2", "append entry 18", dict(kind="async")),
     ("r", "f1", "ld", "ack"),
     ("n", "ld", "ld", "2 of 3 have it: committed", "green"),
     ("r", "ld", "a", "ok: you own 40,000 – 40,999"),
     ("m", "b", "ld", "Txn: if mod_rev(next) = 17, put next = 41,000"),
     ("r", "ld", "b", "fails: mod_rev is now 18", dict(hl=True)),
     ("n", "b", "b", "read again; next Txn wins 41,000 – 41,999", "amber")])

seq("seq-th-cache",
    [("br", "3 browsers", "person"), ("rd", "Redirect server", "container"), ("rc", "Redis Cluster", "db"), ("pg", "PostgreSQL", "db"), ("tk", "Takedown", "container")],
    [("m", "br", "rd", "GET /k7Pq2mZ, three at once"),
     ("n", "rd", "rd", "in-process miss: the first leads, two wait", "amber"),
     ("m", "rd", "rc", "GET k7Pq2mZ"),
     ("r", "rc", "rd", "miss"),
     ("m", "rd", "pg", "SELECT url, status WHERE code = $1"),
     ("r", "pg", "rd", "url, live"),
     ("m", "rd", "rc", "SET EX 3600 ± 10 %", dict(kind="async")),
     ("r", "rd", "br", "3 × 302 from one lookup", dict(hl=True)),
     ("m", "tk", "rd", "invalidate k7Pq2mZ", dict(kind="async")),
     ("n", "rd", "rd", "dropped now; if lost, the 60 s lifetime ends it", "green")])

seq("seq-takedown",
    [("ts", "Trust and safety", "person"), ("tk", "Takedown", "container"), ("db", "Link store", "db"), ("iv", "Invalidation", "queue"), ("ly", "Caches + edge", "container")],
    [("m", "ts", "tk", "POST /takedowns {code, reason}"),
     ("m", "tk", "db", "status = blocked; audit row"),
     ("m", "tk", "ly", "delete the shared-cache key (retried until confirmed)"),
     ("m", "tk", "iv", "invalidate aZ3kQ9x", dict(kind="async")),
     ("m", "iv", "ly", "shared cache delete; every server drops it; edge purge", dict(kind="async")),
     ("n", "ly", "ly", "event lost? in-process and edge TTLs are 60 s: worst case about 2 min", "amber"),
     ("r", "ly", "ts", "next request reads blocked: 410 Gone", dict(hl=True))])

seq("seq-ch1-lease",
    [("a", "Create server A", "container"), ("al", "Range allocator", "db"), ("db", "Link store", "db")],
    [("m", "a", "al", "lease: compare-and-set next 40,000 → 41,000"),
     ("r", "al", "a", "ok: you own 40,000 – 40,999"),
     ("n", "a", "a", "hand out IDs locally; at 40,500 lease the next range early", "green"),
     ("m", "a", "db", "INSERT alias 'sale'  UNIQUE(code)"),
     ("r", "db", "a", "conflict: 'sale' exists", dict(hl=True)),
     ("n", "a", "a", "answer 409 to the second customer; the first keeps it", "green")])

seq("seq-ch3-flight",
    [("br", "1,000 requests", "person"), ("rd", "Redirect server", "container"), ("ca", "Shared cache", "container"), ("db", "Link store", "db")],
    [("m", "br", "rd", "GET /k7Pq2mZ  (1,000 in 20 ms)"),
     ("n", "rd", "rd", "in-process miss: the first request leads; 999 wait on it", "amber"),
     ("m", "rd", "ca", "one get"),
     ("r", "ca", "rd", "miss (shard restarting)"),
     ("m", "rd", "db", "one SELECT"),
     ("r", "db", "rd", "url"),
     ("r", "rd", "br", "1,000 × 302 from one lookup; cached 30 s in process", dict(hl=True))])

seq("seq-ch6-billed",
    [("rd", "Redirect server", "container"), ("bf", "Local disk buffer", "db"), ("lg", "Click log", "queue"), ("ag", "Aggregator", "container")],
    [("n", "rd", "rd", "302 already sent", "green"),
     ("m", "rd", "bf", "append {eventId, code, time, country}"),
     ("m", "bf", "lg", "flush a batch every second", dict(kind="async")),
     ("r", "lg", "bf", "ack: trim the buffer"),
     ("m", "lg", "ag", "at-least-once delivery", dict(kind="async")),
     ("n", "ag", "ag", "de-duplicate by eventId, filter bots, count per minute", "green")])

seq("seq-ch7-region",
    [("br", "Browser in Europe", "person"), ("eu", "Redirect, Europe", "container"), ("ap", "Link store, Asia", "db")],
    [("n", "eu", "eu", "code 9Hc… created in Asia 200 ms ago; not yet replicated", "amber"),
     ("m", "br", "eu", "GET /9Hc2…"),
     ("n", "eu", "eu", "local miss; invert the permutation: the ID's slice says Asia", "amber"),
     ("m", "eu", "ap", "one cross-region lookup"),
     ("r", "ap", "eu", "url, live; cache it here"),
     ("r", "eu", "br", "302, one round trip slower, no error", dict(hl=True))])

seq("seq-ch8-probe",
    [("pb", "Probe, each region", "container"), ("cs", "Create service", "container"), ("rd", "Redirect path", "container")],
    [("m", "pb", "cs", "create a test link (every minute)"),
     ("r", "cs", "pb", "201 code"),
     ("m", "pb", "rd", "follow it through the edge"),
     ("r", "rd", "pb", "302 in 6 ms: create-to-first-redirect 0.4 s", dict(hl=False)),
     ("m", "pb", "cs", "hourly: block a test link"),
     ("n", "pb", "pb", "poll every layer until 410: takedown latency 74 s", "green")])

# ───────────────────────────── 4 · data models ───────────────────────────────────────────────────────
c = er.Chen(1600, 900, size=26)
c.entity("o", 200, 120, "OWNER"); c.entity("l", 680, 120, "LINK"); c.entity("k", 1200, 120, "CLICK EVENT", weak=True)
c.entity("t", 200, 560, "TAKEDOWN", weak=True); c.entity("d", 1200, 560, "DAILY COUNT"); c.entity("r", 680, 700, "RANGE LEASE")
c.rel("cr", 440, 120, "CREATES"); c.rel("cl", 940, 120, "CLICKED AS", identifying=True); c.rel("wd", 440, 400, "WITHDRAWS", identifying=True)
c.rel("ag", 1200, 340, "COUNTED IN")
c.attr("oid", 200, 40, "owner_id", of="o", key=True)
c.attr("cd", 600, 40, "code", of="l", key=True); c.attr("u", 780, 40, "long_url", of="l"); c.attr("st", 860, 200, "status", of="l"); c.attr("ex", 520, 220, "expires_at", of="l")
c.attr("tm", 1400, 120, "time", of="k", partial=True); c.attr("ct", 1300, 40, "country", of="k")
c.attr("n", 1400, 560, "n", of="d", derived=True); c.attr("day", 1200, 660, "day", of="d", key=True)
c.attr("rs", 80, 640, "reason", of="t")
c.attr("srv", 680, 800, "server", of="r", key=True); c.attr("rg", 880, 760, "start, end", of="r")
c.link("o", "cr", "1"); c.link("cr", "l", "N", total=True)
c.link("l", "cl", "1"); c.link("cl", "k", "N")
c.link("l", "wd", "1", src="b", dst="r"); c.link("wd", "t", "N", src="l", dst="t")
c.link("k", "ag", "N", src="b", dst="t"); c.link("ag", "d", "1", src="b", dst="t")
c.legend(1380, 760)
c.note(300, 820, 1000, "A code has exactly one live long URL; the same URL may have many codes.")
c.save(OUT / "erd-chen.svg")

e = er.ERD(1600, 800, size=22)
e.entity("link", 30, 40, 520, "link", [("code", "char(7)", "PK"), ("long_url", "text", ""), ("owner_id", "bigint", "IX"),
         ("created_at", "ts", ""), ("expires_at", "ts", ""), ("status", "text", "")],
         kind="focus", caption="12 B rows in ten years; sharded by code")
e.entity("byo", 690, 40, 420, "link_by_owner", [("owner_id", "bigint", "PK"), ("created_at", "ts", "PK"), ("code", "char(7)", "")],
         caption="the owner's dashboard; never on the hot path")
e.entity("rl", 1250, 40, 330, "range_lease", [("server_id", "text", "PK"), ("start", "bigint", ""), ("end", "bigint", ""), ("leased_at", "ts", "")],
         kind="ext", caption="consensus store; 0.4 leases a second")
e.entity("dc", 30, 470, 520, "daily_count", [("code", "char(7)", "PK"), ("day", "date", "PK"), ("country", "char(2)", "PK"), ("n", "bigint", "")],
         caption="written by the aggregator; read by the owner")
e.entity("mem", 690, 470, 520, "in the redirect server (memory)", [("lru: code → url, status", "map", ""), ("ttl", "30–60 s", ""), ("in_flight", "map", "")],
         kind="redis", caption="single flight: one lookup per code per server")
e.rel("byo", "link", "N", "1", src="l:0.5", dst="r:0.3", label="code", at=(620, 120))
e.note(1250, 330, 330, "A URL hash is not a key: one URL may have many links.")
e.note(30, 745, 1540, "Clicks are a log partitioned by code, then counts per minute and per day. The link row is never updated by a click.")
e.save(OUT / "erd-physical.svg")

# ───────────────────────────── 5 · figures ───────────────────────────────────────────────────────────
def svgdoc(w, h, body): return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" width="{w}" height="{h}">'
                               f'<rect width="{w}" height="{h}" fill="#ffffff"/>{body}</svg>')
def T(x, y, s, size=24, fill=INK, w=500, anchor="start"):
    return f'<text x="{x}" y="{y}" text-anchor="{anchor}" font-family="{FONT}" font-size="{size}" font-weight="{w}" fill="{ink(fill)}">{esc(s)}</text>'
def R(x, y, w, h, fill, stroke, dash=False, rx=8, sw=2.2):
    return (f'<rect x="{x:.1f}" y="{y:.1f}" width="{w:.1f}" height="{h:.1f}" rx="{rx}" fill="{fill}" stroke="{stroke}" '
            f'stroke-width="{sw}"{" stroke-dasharray=\"10 6\"" if dash else ""}/>')
def L(x1, y1, x2, y2, col=INK, sw=2.4, dash=False):
    return f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" stroke="{col}" stroke-width="{sw}"{" stroke-dasharray=\"8 6\"" if dash else ""}/>'

def codespace():
    import math
    p = [T(40, 44, "How many codes, against how many links (log scale)", 28, INK, 800)]
    x0, W = 420, 900
    lg = lambda v: (math.log10(v) - 9) / (13 - 9) * W
    rows = [("links in ten years", 1.2e10, BLUE, "1.2 × 10¹⁰"), ("6 characters: 62⁶", 5.7e10, AMBER, "5.7 × 10¹⁰ · only 4.7×"),
            ("7 characters: 62⁷", 3.5e12, GREEN, "3.5 × 10¹² · about 290×")]
    for i, (lab, v, col, txt) in enumerate(rows):
        y = 100 + i * 90
        fill = {BLUE: "#e8f0fe", AMBER: "#fef7e0", GREEN: "#e6f4ea"}[col]
        p += [T(40, y + 36, lab, 25, INK, 700), R(x0, y, lg(v), 54, fill, col), T(x0 + lg(v) + 14, y + 37, txt, 24, col, 800)]
    for v, lab in ((1e9, "10⁹"), (1e10, "10¹⁰"), (1e11, "10¹¹"), (1e12, "10¹²"), (1e13, "10¹³")):
        x = x0 + lg(v); p += [L(x, 375, x, 388, GREY, 2), T(x, 414, lab, 20, "#5f6368", 600, "middle")]
    p.append(L(x0, 381, x0 + W, 381, GREY, 2))
    p += [T(40, 470, "Random 7-character codes: a new code collides with probability 1.2 × 10¹⁰ ÷ 3.5 × 10¹² ≈ 0.34 % at the end of year ten.", 23, "#202124", 700)]
    (OUT / "codespace.svg").write_text(svgdoc(1600, 510, "".join(p)))
codespace()

def tension():
    p = [T(40, 44, "Speed of the answer against control over it: every layer closer to the user", 28, INK, 800)]
    layers = [("Browser (301)", RED, "#fce8e6", "0 ms", "never seen again"), ("Edge (302, 60 s)", AMBER, "#fef7e0", "~5 ms near the user", "counted from logs; purgeable"),
              ("Redirect + caches", GREEN, "#e6f4ea", "~1 ms at the server", "every click; recallable"), ("Link store", BLUE, "#e8f0fe", "~5 ms, misses only", "the truth")]
    for i, (lab, col, fill, sp, ctl) in enumerate(layers):
        x = 60 + i * 385
        p += [R(x, 110, 345, 120, fill, col, rx=12), T(x + 172, 165, lab, 25, INK, 800, "middle"), T(x + 172, 205, sp, 21, col, 700, "middle"),
              T(x + 172, 270, ctl, 21, INK, 600, "middle")]
    p += [L(80, 330, 1520, 330, BLUE, 4), T(80, 370, "← faster and cheaper", 24, BLUE, 800), T(1520, 370, "more control: counting, takedown →", 24, GREEN, 800, "end")]
    p += [R(60, 410, 1480, 70, "#fef7e0", AMBER), T(800, 455, "301 against 302 is where on this line you let the answer live. A product decision, not a tweak.", 25, "#202124", 800, "middle")]
    (OUT / "tension.svg").write_text(svgdoc(1600, 510, "".join(p)))
tension()

def ranges():
    p = [T(40, 44, "Counter ranges: coordination once per thousand links, not once per link", 28, INK, 800)]
    p += [R(60, 170, 300, 160, "#e6f4ea", GREEN, rx=14), T(210, 235, "Range allocator", 25, INK, 800, "middle"), T(210, 275, "next = 41,000", 23, "#202124", 700, "middle")]
    srv = [("Server A", "40,000 – 40,999", "40,017"), ("Server B", "39,000 – 39,999", "39,522"), ("Server C", "38,000 – 38,999", "38,904")]
    for i, (n, r, nx) in enumerate(srv):
        y = 90 + i * 140
        p += [R(560, y, 380, 110, "#d2e3fc", PURPLE, rx=12), T(750, y + 45, n, 24, INK, 800, "middle"), T(750, y + 82, "holds " + r, 21, "#202124", 600, "middle"),
              L(362, 250, 556, y + 55, GREEN, 3), R(1100, y, 440, 110, "#e8f0fe", BLUE, rx=12), T(1320, y + 45, "next ID " + nx, 24, INK, 800, "middle"),
              T(1320, y + 82, "→ permute → base-62", 21, "#202124", 600, "middle"), L(942, y + 55, 1096, y + 55, BLUE, 3)]
    p += [T(40, 540, "A server that crashes wastes the rest of its range: a gap, never a collision. There are 290 times more codes than links.", 23, "#202124", 700)]
    (OUT / "ranges.svg").write_text(svgdoc(1600, 580, "".join(p)))
ranges()

def regions():
    p = [T(40, 44, "Every region answers its own redirects and creates in its own slice of the ID space", 28, INK, 800)]
    regs = [("Europe", "IDs 0 – 1.1 × 10¹²"), ("Americas", "IDs 1.1 – 2.3 × 10¹²"), ("Asia", "IDs 2.3 – 3.5 × 10¹²")]
    for i, (n, sl) in enumerate(regs):
        x = 60 + i * 510
        bad = n == "Americas"
        p += [R(x, 100, 460, 330, "#fce8e6" if bad else "#f8f9fa", RED if bad else GREY, dash=True, rx=16), T(x + 230, 140, n + ("  (primary lost)" if bad else ""), 25, RED if bad else INK, 800, "middle"),
              R(x + 30, 170, 400, 70, "#d2e3fc", PURPLE), T(x + 230, 214, "redirect servers + caches", 22, INK, 700, "middle"),
              R(x + 30, 260, 400, 70, "#e6f4ea", GREEN), T(x + 230, 304, "link store replica", 22, INK, 700, "middle"),
              R(x + 30, 350, 400, 60, "#e8f0fe", BLUE), T(x + 230, 388, sl, 21, "#202124", 700, "middle")]
    p += [T(40, 490, "Redirects never cross regions. A brand-new code clicked elsewhere before it replicates costs one cross-region lookup, not an error.", 22, "#202124", 700)]
    (OUT / "regions.svg").write_text(svgdoc(1600, 530, "".join(p)))
regions()

def feistel():
    p = [T(40, 44, "A keyed permutation: unique in, unique out, neighbours unrelated", 28, INK, 800)]
    ins = ["40,017", "40,018", "40,019"]; outs = ["aZ3kQ9x", "Pq07mWd", "3fLx9Tb"]
    for i, (a, o) in enumerate(zip(ins, outs)):
        y = 110 + i * 110
        p += [R(60, y, 260, 80, "#e8f0fe", BLUE, rx=10), T(190, y + 50, "ID " + a, 25, INK, 800, "middle"), L(322, y + 40, 556, 250, GREY, 2.5),
              L(1044, 250, 1276, y + 40, GREY, 2.5), R(1280, y, 260, 80, "#e6f4ea", GREEN, rx=10), T(1410, y + 50, o, 26, "#202124", 800, "middle")]
    p += [R(560, 170, 480, 160, "#d2e3fc", PURPLE, rx=16), T(800, 225, "4-round Feistel over 42 bits", 24, INK, 800, "middle"),
          T(800, 262, "secret round key · cycle-walk below 62⁷", 21, "#202124", 600, "middle"), T(800, 298, "then base-62, 7 characters", 21, "#202124", 600, "middle")]
    p += [T(40, 480, "A bijection: two different IDs can never give the same code. The counter gives uniqueness; the key gives unpredictability.", 23, "#202124", 700)]
    (OUT / "feistel.svg").write_text(svgdoc(1600, 520, "".join(p)))
feistel()

def ttlbudget():
    bs.budget_bar(OUT / "takedown-budget.svg", [("status + cache delete", 2, "data"), ("in-process TTL", 60, "service"),
                                               ("edge TTL", 60, "edge"), ("purge", 5, "ext")],
                  total=300, unit="s", title="Takedown, worst case if the invalidation event is lost (target 5 min)")
ttlbudget()

print(sorted(p.name for p in OUT.glob("*.svg")))
