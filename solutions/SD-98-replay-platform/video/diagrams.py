#!/usr/bin/env python3
"""SD-98 reproducible replay and regression-gate platform: every picture for the video and the written design -> ./svg/*.svg.
One canonical container view (c4svg, since= per box and edge) saved as views (V1 -> V4, flows, the challenge map, badges);
three component views (sim worker, DAG planner, gate service) carry the challenges. Sequences, data models, figures.
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
    "ingest": ("AR0", "ext", "Log ingest", "External", "Fleet uploads.", 1),
    "eng":    ("AR1", "person", "Engineer", "Person", "Runs a build on a set.", 1),
    "ci":     ("AR2", "ext", "Release pipeline", "External", "Asks: may it ship?", 3),
    "logs":   ("BR0", "db", "Log store", "Object storage", "Immutable chunks.", 1),
    "api":    ("BR1", "container", "Run API", "Service", "Runs, manifests.", 1),
    "gate":   ("BR2", "container", "Gate service", "Service", "Diff, policy, verdict.", 3),
    "cat":    ("CR0", "db", "Scenario catalog", "Database", "Versioned sets.", 1),
    "plan":   ("CR1", "container", "DAG planner", "Service", "Stages, keys.", 2),
    "res":    ("CR2", "db", "Results store", "Columnar store", "Metrics per run.", 1),
    "cache":  ("DR0", "db", "Artifact cache", "Blob store + index", "Outputs by key.", 2),
    "sched":  ("DR1", "container", "Scheduler", "Batch scheduler", "Quotas, priority.", 1),
    "audit":  ("DR2", "container", "Gate auditor", "Service", "Checks the checker.", 4),
    "work":   ("ER1", "container", "Sim workers", "GPU, CPU pool", "Replay harness.", 1),
}

def canon(labels=None):
    d = c4.Diagram(1830, 830, canon="containers")
    d.boundary(375, 20, 1440, 790, "Replay platform", "Software System", top="right")
    for k, (cell, kind, t, typ, desc, since) in BOX.items():
        if labels and k in labels: typ, desc = labels[k][1], labels[k][2]
        x, y = P(cell)
        d.node(k, x, y, W, H, kind, t, typ, desc, size=SZ, since=since)
    E = d.edge
    E("ingest", "logs", "chunks", "", src="r", dst="l", at=(335, 152), size=21, eid="i-l")
    E("eng", "api", "runs", "HTTPS", src="r", dst="l", at=(335, 412), size=21, eid="e-a")
    E("api", "cat", "resolve set", "", src="r:0.2", dst="l:0.5", via=[(715, 388), (715, 170)], at=(715, 300), size=21, eid="a-c", until=1)
    E("api", "sched", "every stage", "", src="r:0.5", dst="l:0.5", at=(905, 412), size=21, eid="a-s", until=1)
    E("api", "plan", "run", "", src="r:0.5", dst="l:0.5", at=(715, 412), size=21, eid="a-p", since=2)
    E("plan", "cat", "set", "", src="t:0.5", dst="b:0.5", at=(940, 300), size=21, eid="p-c", since=2)
    E("plan", "sched", "misses", "", src="r:0.5", dst="l:0.5", at=(1095, 412), size=21, eid="p-s", since=2)
    E("plan", "cache", "lookups", "", src="t:0.9", dst="l:0.85", at=(1100, 262), size=21, eid="p-k", since=2)
    E("sched", "work", "pods", "", src="r:0.5", dst="l:0.5", at=(1475, 412), size=21, eid="s-w")
    E("work", "logs", "byte ranges", "", src="t:0.5", dst="b:0.5", via=[(1665, 300), (525, 300)], at=(1300, 300), size=21, eid="w-l")
    E("work", "cache", "get, put", "", src="t:0.15", dst="r:0.75", via=[(1577, 205)], at=(1480, 180), size=21, eid="w-k", since=2)
    E("work", "res", "metrics", "", src="b:0.5", dst="t:0.5", via=[(1665, 565), (905, 565)], at=(1480, 565), size=21, eid="w-r")
    E("gate", "res", "pairs", "", src="r:0.5", dst="l:0.5", at=(715, 690), size=21, eid="g-r", since=3)
    E("ci", "gate", "build", "", src="r:0.3", dst="l:0.3", at=(335, 645), size=21, eid="c-g", since=3)
    E("gate", "ci", "pass, block", "", src="l:0.7", dst="r:0.7", at=(335, 735), size=21, eid="g-c", since=3)
    E("gate", "api", "gate set", "", src="t:0.5", dst="b:0.5", at=(590, 560), size=21, eid="g-a", since=3)
    E("audit", "sched", "canaries", "", src="t:0.5", dst="b:0.5", at=(1350, 590), size=21, eid="u-s", since=4)
    E("audit", "res", "agreement", "", src="l:0.5", dst="r:0.5", at=(1095, 690), size=21, eid="u-r", since=4)
    d.legend(1560, 630, ("person", "container", "db", "ext"), vertical=True)
    return d

d = canon()
d.save(OUT / "base-v1.svg", upto=1, order=["ingest", "logs", "eng", "api", "cat", "sched", "work", "res"])
d.save(OUT / "base-v2.svg", upto=2, new=2, order=["plan", "cache"])
d.save(OUT / "base-v3.svg", upto=3, new=3, order=["ci", "gate"])
d.save(OUT / "base-v4.svg", upto=4, new=4, order=["audit"])
d.save(OUT / "flow-run.svg", upto=3, flow=["e-a", "a-p", "p-c", "p-k", "p-s", "s-w", "w-l", "w-r"])
d.save(OUT / "flow-gate.svg", upto=3, flow=["c-g", "g-a", "a-p", "p-s", "s-w", "w-r", "g-r", "g-c"])
d.save(OUT / "map.svg", upto=3, attack=["work", "plan", "sched", "gate"], keep=None)
d.save(OUT / "ch3-attack.svg", upto=3, attack=["sched"], keep=["plan", "sched", "work", "cache"])
d.save(OUT / "ch6-attack.svg", upto=3, attack=["gate"], keep=["ci", "gate", "res"])
d.save(OUT / "recap.svg", upto=4, badges={"logs": "M1 hashed", "plan": "M1 M3", "cache": "M3", "sched": "M5",
                                          "work": "M2", "gate": "M4", "audit": "canaries"})
d.save(OUT / "alt.svg", upto=2, attack=["plan", "cache"], keep=["eng", "api", "plan", "cache", "sched", "work"])
dt = canon(stack.C4)
dt.save(OUT / "c4-containers-tech.svg", upto=3, focus=["logs", "cat", "plan", "cache", "sched", "work", "res", "gate"], keep=None)

# ───────────────────────────── 2 · C4 context ────────────────────────────────────────────────────────
x = c4.Diagram(1600, 700)
x.node("eng", 40, 80, 320, 150, "person", "Engineers", "3,000 people", "Run builds against recorded logs.", size=26)
x.node("ci", 40, 440, 320, 150, "ext", "Release pipeline", "External system", "Asks whether a build may ship.", size=26)
x.node("sys", 620, 250, 380, 190, "system", "Replay platform", "Software System", "Replays, caches, compares, gates.", size=28)
x.node("ing", 1240, 80, 320, 150, "ext", "Log ingest", "External system", "Uploads fleet logs, 1 PB a month.", size=26)
x.node("gpu", 1240, 440, 320, 150, "ext", "Compute cluster", "Kubernetes, GPUs", "Shared with training.", size=26)
x.edge("eng", "sys", "runs, results", "HTTPS", src="r", dst="l:0.25", at=(490, 160), size=22)
x.edge("ci", "sys", "gate this build", "HTTPS", src="r", dst="l:0.75", at=(490, 520), size=22)
x.edge("ing", "sys", "log chunks", "object storage", src="l", dst="r:0.25", at=(1120, 160), size=22)
x.edge("sys", "gpu", "pods", "Kubernetes API", src="r:0.75", dst="l", at=(1120, 520), size=22)
x.legend(40, 660, ("person", "system", "ext"))
x.save(OUT / "c4-context.svg", order=["eng", "sys", "ci", "ing", "gpu"])

# ───────────────────────────── 3 · component views ───────────────────────────────────────────────────
CX = [20, 300, 560, 820, 1080, 1340, 1600]; CW, CH, CS = 210, 150, 25
def comp(name, tech):
    d = c4.Diagram(1830, 770, canon="comp:" + name)
    d.boundary(275, 40, 1300, 700, name, tech, top="left")
    return d

w = comp("Sim worker", "Container: replay harness")
w.node("logs", CX[0], 330, 200, CH, "db", "Log store", "GCS", "Chunks.", size=CS)
w.node("fetch", CX[1], 330, CW, CH, "component", "Chunk fetcher", "Component", "Ranges; hash check.", size=CS)
w.node("bus", CX[2], 330, CW, CH, "component", "Sim clock + bus", "Component", "Ordered delivery.", size=CS)
w.node("stage", CX[3], 330, CW, CH, "component", "Stage runner", "Sandbox", "Pinned images.", size=CS)
w.node("met", CX[4], 330, CW, CH, "component", "Metric extractor", "Component", "Per scenario.", size=CS)
w.node("wr", CX[5], 330, CW, CH, "component", "Result writer", "Component", "With the manifest.", size=CS)
w.node("res", CX[6], 330, 210, CH, "db", "Results store", "ClickHouse", "", size=CS)
w.node("agents", CX[2], 90, CW, CH, "component", "Agent models", "Component", "Road users react.", size=CS)
w.node("cc", CX[3], 570, CW, CH, "component", "Cache client", "Component", "Get, then put.", size=CS)
w.node("cache", CX[6], 570, 210, CH, "db", "Artifact cache", "GCS + Bigtable", "", size=CS)
for a_, b_ in (("logs", "fetch"), ("fetch", "bus"), ("bus", "stage"), ("stage", "met"), ("met", "wr"), ("wr", "res")):
    w.edge(a_, b_, "", "", src="r", dst="l")
w.edge("agents", "bus", "", "", src="b", dst="t")
w.edge("stage", "cc", "", "", src="b", dst="t")
w.edge("cc", "cache", "key", "", src="r", dst="l", at=(1310, 625), size=21)
w.legend(40, 120, ("component", "db"), vertical=True)
w.save(OUT / "c4-comp-worker.svg", order=["logs", "fetch", "bus", "agents", "stage", "cc", "cache", "met", "wr", "res"])
w.save(OUT / "ch1-attack.svg", keep=["fetch", "bus", "stage"], attack=["bus", "stage"])
w.save(OUT / "ch1-fix.svg", keep=["fetch", "bus", "stage"], fix=["bus", "stage"])
w.save(OUT / "ch4-attack.svg", keep=["bus", "stage", "met"], attack=["met"])
w.save(OUT / "ch4-fix.svg", keep=["agents", "bus", "stage"], fix=["agents"])

p = comp("DAG planner", "Container: Go service")
p.node("api", CX[0], 330, 200, CH, "container", "Run API", "Service", "A run request.", size=CS)
p.node("man", CX[1], 330, CW, CH, "component", "Manifest builder", "Component", "Pins digests.", size=CS)
p.node("graph", CX[2], 330, CW, CH, "component", "Stage graph", "Component", "From the build.", size=CS)
p.node("keys", CX[3], 330, CW, CH, "component", "Key hasher", "Merkle chain", "Stage after stage.", size=CS)
p.node("look", CX[4], 330, CW, CH, "component", "Index lookup", "Batched", "Hit or miss.", size=CS)
p.node("emit", CX[5], 330, CW, CH, "component", "Job emitter", "Component", "Misses only.", size=CS)
p.node("sched", CX[6], 330, 210, CH, "container", "Scheduler", "Kueue", "", size=CS)
p.node("cat", CX[1], 90, CW, CH, "db", "Scenario catalog", "PostgreSQL", "", size=CS)
p.node("reg", CX[2], 90, CW, CH, "db", "Image registry", "By digest", "", size=CS)
p.node("idx", CX[4], 570, CW, CH, "db", "Cache index", "Bigtable", "", size=CS)
for a_, b_ in (("api", "man"), ("man", "graph"), ("graph", "keys"), ("keys", "look"), ("look", "emit"), ("emit", "sched")):
    p.edge(a_, b_, "", "", src="r", dst="l")
p.edge("cat", "man", "", "", src="b", dst="t")
p.edge("reg", "graph", "", "", src="b", dst="t")
p.edge("look", "idx", "", "", src="b", dst="t")
p.legend(40, 120, ("component", "container", "db"), vertical=True)
p.save(OUT / "c4-comp-planner.svg", order=["api", ("man", "cat"), ("graph", "reg"), "keys", ("look", "idx"), "emit", "sched"])
p.save(OUT / "ch2-attack.svg", keep=["graph", "keys", "look"], attack=["keys"])
p.save(OUT / "ch2-fix.svg", keep=["graph", "keys", "look"], fix=["keys"])

g = comp("Gate service", "Container: Go service")
g.node("ci", CX[0], 330, 200, CH, "ext", "Release pipeline", "External", "", size=CS)
g.node("req", CX[1], 330, CW, CH, "component", "Gate request", "Component", "Build, set version.", size=CS)
g.node("base", CX[2], 330, CW, CH, "component", "Baseline resolver", "Component", "Last release.", size=CS)
g.node("pair", CX[3], 330, CW, CH, "component", "Paired differ", "Component", "Same scenario, both.", size=CS)
g.node("stat", CX[4], 330, CW, CH, "component", "Statistics", "Bootstrap", "An interval, not a point.", size=CS)
g.node("pol", CX[5], 330, CW, CH, "component", "Policy evaluator", "Rules as code", "Versioned.", size=CS)
g.node("rec", CX[6], 330, 210, CH, "db", "Decisions", "PostgreSQL", "", size=CS)
g.node("res", CX[3], 90, CW, CH, "db", "Results store", "ClickHouse", "", size=CS)
g.node("flake", CX[3], 570, CW, CH, "component", "Flake list", "Component", "Quarantined.", size=CS)
g.node("repo", CX[5], 90, CW, CH, "db", "Policy repo", "Reviewed", "", size=CS)
for a_, b_ in (("ci", "req"), ("req", "base"), ("base", "pair"), ("pair", "stat"), ("stat", "pol"), ("pol", "rec")):
    g.edge(a_, b_, "", "", src="r", dst="l")
g.edge("res", "pair", "", "", src="b", dst="t")
g.edge("flake", "pair", "", "", src="t", dst="b")
g.edge("repo", "pol", "", "", src="b", dst="t")
g.legend(40, 120, ("component", "db", "ext"), vertical=True)
g.save(OUT / "c4-comp-gate.svg", order=["ci", "req", "base", ("pair", "res"), "flake", "stat", ("pol", "repo"), "rec"])
g.save(OUT / "ch5-attack.svg", keep=["pair", "stat", "pol"], attack=["pol"])
g.save(OUT / "ch5-fix.svg", keep=["pair", "stat", "pol"], fix=["stat", "pol"])

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

seq("seq-find",
    [("eng", "Engineer", "person"), ("api", "Run API", "container"), ("cat", "Scenario catalog", "db")],
    [("m", "eng", "api", "find: unprotected left turn, rain"),
     ("m", "api", "cat", "query tags and chunk ranges"),
     ("r", "cat", "api", "1,840 scenarios"),
     ("m", "api", "cat", "save as set left-rain, version 1"),
     ("r", "api", "eng", "set left-rain@1: a list of chunk hashes", dict(hl=True))])

seq("seq-run",
    [("eng", "Engineer", "person"), ("pl", "DAG planner", "container"), ("ix", "Cache index", "db"), ("sc", "Scheduler", "container"), ("wk", "Sim worker", "container")],
    [("m", "eng", "pl", "run build 7f3c on left-rain@1"),
     ("n", "pl", "pl", "manifest: digests, set version, seeds", "amber"),
     ("m", "pl", "ix", "look up 1,840 × 3 stage keys"),
     ("r", "ix", "pl", "perception: all hit; planning: all miss"),
     ("m", "pl", "sc", "1,840 planning jobs"),
     ("m", "sc", "wk", "pods, within the team's quota"),
     ("r", "wk", "eng", "metrics in the results store, run 9921", dict(hl=True))])

seq("seq-repro",
    [("eng", "Engineer", "person"), ("pl", "DAG planner", "container"), ("ix", "Cache index", "db"), ("wk", "Sim worker", "container")],
    [("m", "eng", "pl", "reproduce run 4410 (an incident, March)"),
     ("n", "pl", "pl", "load manifest m-4410: same keys", "amber"),
     ("m", "pl", "ix", "look up every key"),
     ("r", "ix", "pl", "all hit: identical outputs"),
     ("m", "eng", "wk", "verify: re-execute without the cache"),
     ("r", "wk", "eng", "output hashes equal to March", dict(hl=True))])

seq("seq-gate",
    [("ci", "Release pipeline", "ext"), ("gt", "Gate service", "container"), ("pl", "Planner + workers", "container"), ("rs", "Results store", "db")],
    [("m", "ci", "gt", "gate build 7f3c"),
     ("m", "gt", "pl", "run gate-set@57 on 7f3c"),
     ("n", "pl", "pl", "50,000 scenarios; 70 % of stages hit", "amber"),
     ("m", "pl", "rs", "metrics for run 9930"),
     ("m", "gt", "rs", "pair 9930 with released run 9811"),
     ("n", "gt", "gt", "intervals per metric; policy v14", "blue"),
     ("r", "gt", "ci", "block: hard-brake rate +0.4 %, interval excludes 0", dict(hl=True))])

seq("seq-th-keys",
    [("pl", "Planner", "container"), ("ix", "Cache index", "db"), ("wk", "Worker", "container")],
    [("n", "pl", "pl", "k1 = H(perception digest, chunk hashes, params)", "blue"),
     ("n", "pl", "pl", "k2 = H(planning digest, k1, map v31, seed)", "blue"),
     ("m", "pl", "ix", "get k1, k2"),
     ("r", "ix", "pl", "k1 hit; k2 miss"),
     ("m", "pl", "wk", "run planning only, input = blob of k1"),
     ("m", "wk", "ix", "put k2 after the blob is written", dict(hl=True))])

seq("seq-ch1-double",
    [("au", "Auditor", "container"), ("w1", "Run A", "container"), ("w2", "Run B", "container")],
    [("m", "au", "w1", "same manifest, run 1"),
     ("m", "au", "w2", "same manifest, run 2, other node"),
     ("r", "w1", "au", "message hashes, step by step"),
     ("r", "w2", "au", "message hashes, step by step"),
     ("n", "au", "au", "first difference: message 41,207, tracker output", "amber"),
     ("n", "au", "au", "cause: a GPU reduction with atomic adds", "green")])

# ───────────────────────────── 5 · data models ───────────────────────────────────────────────────────
c = er.Chen(1960, 900, size=27)
c.entity("set", 200, 140, "SCENARIO SET"); c.entity("sc", 700, 140, "SCENARIO"); c.entity("ch", 1200, 140, "LOG CHUNK")
c.entity("run", 700, 560, "RUN"); c.entity("man", 200, 560, "MANIFEST"); c.entity("art", 1200, 560, "ARTIFACT")
c.entity("gd", 700, 830, "GATE DECISION")
c.rel("has", 450, 140, "LISTS"); c.rel("sp", 950, 140, "SPANS"); c.rel("on", 700, 350, "REPLAYS")
c.rel("pin", 450, 560, "PINNED BY"); c.rel("pr", 950, 560, "PRODUCES"); c.rel("cmp", 700, 700, "COMPARES")
c.attr("sv", 200, 50, "name, version", of="set", key=True)
c.attr("sid", 700, 50, "scenario_id", of="sc", key=True)
c.attr("hash", 1200, 50, "sha256", of="ch", key=True)
c.attr("rid", 960, 650, "run_id", of="run", key=True)
c.attr("mid", 200, 680, "manifest_id", of="man", key=True)
c.attr("key", 1460, 560, "key", of="art", key=True)
c.attr("ver", 1000, 830, "verdict", of="gd")
c.link("set", "has", "M"); c.link("has", "sc", "N")
c.link("sc", "sp", "M"); c.link("sp", "ch", "N")
c.link("sc", "on", "M", src="b", dst="t"); c.link("on", "run", "N", src="b", dst="t")
c.link("man", "pin", "1"); c.link("pin", "run", "N", total=True)
c.link("run", "pr", "M"); c.link("pr", "art", "N")
c.link("run", "cmp", "2", src="b", dst="t"); c.link("cmp", "gd", "N", src="b", dst="t")
c.legend(1660, 70, size=23, gap=36, rows=["rect", "dia", "oval", "key", "dbl"])
c.save(OUT / "erd-chen.svg", order=[("set", "sc", "has"), ("ch", "sp"), ("run", "on"), ("man", "pin"), ("art", "pr"), ("gd", "cmp")])

e = er.ERD(1600, 820, size=22)
e.entity("man", 30, 40, 470, "manifest", [("manifest_id", "uuid", "PK"), ("set", "name@version", ""), ("images", "digests", ""),
         ("models", "sha256s", ""), ("map_version", "int", ""), ("seed", "bigint", "")], kind="focus", caption="immutable once written")
e.entity("run", 570, 40, 470, "run", [("run_id", "bigint", "PK"), ("manifest_id", "uuid", "FK"), ("build", "text", ""),
         ("kind", "gate | explore", ""), ("status", "text", "")], caption="PostgreSQL")
e.entity("art", 1110, 40, 460, "artifact_index", [("key", "sha256", "PK"), ("blob", "gs:// path", ""), ("producer_run", "bigint", ""),
         ("bytes", "bigint", ""), ("last_used", "date", "")], kind="ext", caption="Bigtable; blob written first")
e.entity("met", 30, 470, 470, "metric", [("run_id", "bigint", "PK"), ("scenario_id", "bigint", "PK"), ("name", "text", "PK"),
         ("value", "float64", "")], kind="redis", caption="ClickHouse; 6 B rows a month")
e.entity("gd", 570, 470, 470, "gate_decision", [("decision_id", "uuid", "PK"), ("candidate_run", "bigint", "FK"), ("baseline_run", "bigint", "FK"),
         ("policy_version", "int", ""), ("verdict", "pass | block", "")], caption="append-only")
e.entity("set", 1110, 470, 460, "scenario_set", [("name", "text", "PK"), ("version", "int", "PK"), ("scenarios", "list", ""), ("chunks", "sha256 list", "")],
         caption="a version never changes")
e.rel("run", "man", "N", "1", src="l:0.4", dst="r:0.3", label="")
e.rel("gd", "run", "N", "2", src="t:0.5", dst="b:0.5", label="")
e.save(OUT / "erd-physical.svg", order=["man", "run", "art", "met", "gd", "set"])

# ───────────────────────────── 6 · figures ───────────────────────────────────────────────────────────
def svgdoc(w, h, body): return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" width="{w}" height="{h}">'
                               f'<rect width="{w}" height="{h}" fill="#ffffff"/>{body}</svg>')
def T(x, y, s, size=24, fill=INK, w=500, anchor="start"):
    return f'<text x="{x}" y="{y}" text-anchor="{anchor}" font-family="{FONT}" font-size="{size}" font-weight="{w}" fill="{ink(fill)}">{esc(s)}</text>'
def R(x, y, w, h, fill, stroke, rx=10, sw=2.2):
    return f'<rect x="{x:.1f}" y="{y:.1f}" width="{w:.1f}" height="{h:.1f}" rx="{rx}" fill="{fill}" stroke="{stroke}" stroke-width="{sw}"/>'
def L(x1, y1, x2, y2, col=INK, sw=2.4, dash=False):
    return f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="{col}" stroke-width="{sw}"{" stroke-dasharray=\"8 6\"" if dash else ""}/>'
def wrapT(x, y, text, size, fill, per):
    out, line, yy = [], "", y
    for w_ in text.split():
        if len(line) + len(w_) > per: out.append(T(x, yy, line, size, fill, 500)); line, yy = w_, yy + size * 1.3
        else: line = (line + " " + w_).strip()
    return out + [T(x, yy, line, size, fill, 500)]

def tension():
    p = [T(40, 50, "Recompute for trust, or reuse for speed: content keys give both, if every input is in the key", 28, INK, 800)]
    cards = [("Recompute everything", "trustworthy, but 1,040 GPUs for a 4-hour gate", "≈ $8,300 a gate", BLUE, "#e8f0fe"),
             ("Reuse by name", "build 412's output reused for build 413", "cheap, and silently stale", RED, "#fce8e6"),
             ("Reuse by content", "key = hash of code, inputs, seed: a hit equals a recompute", "≈ 300 GPUs; trustworthy if hermetic", GREEN, "#e6f4ea")]
    for i, (t, s, n, col, fill) in enumerate(cards):
        x = 60 + i * 510
        p += [R(x, 110, 470, 260, fill, col, rx=14), T(x + 24, 160, t, 27, INK, 800)] + wrapT(x + 24, 205, s, 22, INK, 36) + [T(x + 24, 340, n, 23, col, 800)]
    p += [L(60, 420, 1540, 420, BLUE, 4), T(60, 462, "← cost", 24, BLUE, 800), T(1540, 462, "trust →", 24, GREEN, 800, "end")]
    (OUT / "tension.svg").write_text(svgdoc(1600, 490, "".join(p)))
tension()

def divergence():
    p = [T(40, 48, "Open-loop replay: once the new planner acts differently, the log stops being what would have happened", 27, INK, 800)]
    x0, x1, y = 120, 1500, 300
    p += [L(x0, y, x1, y, GREY, 2), T(x0, y + 36, "t = 0 s", 20, GREY, 600), T(x1, y + 36, "12 s", 20, GREY, 600, "end")]
    p += [f'<path d="M{x0},{y-60} L{x1},{y-60}" stroke="{GREY}" stroke-width="5" fill="none" stroke-dasharray="12 8"/>',
          T(x0, y - 78, "logged ego: brakes at 7.0 s", 22, GREY, 700)]
    p += [f'<path d="M{x0},{y-60} L700,{y-60} C 800,{y-60} 850,{y-140} 950,{y-150} L{x1},{y-150}" stroke="{BLUE}" stroke-width="5" fill="none"/>',
          T(960, y - 168, "new planner: brakes at 5.4 s", 22, "#1967d2", 800)]
    xd = 830
    p += [L(xd, 90, xd, y + 10, RED, 3, True), T(xd - 12, 120, "divergence > 1 m at 6.2 s", 22, "#c5221f", 800, "end")]
    p += [R(120, 360, 650, 110, "#fce8e6", RED), T(140, 400, "Logged follower keeps its speed:", 22, INK, 700), T(140, 435, "a “collision” that the real follower would avoid", 22, "#c5221f", 700)]
    p += [R(850, 360, 650, 110, "#e6f4ea", GREEN), T(870, 400, "Score only up to the divergence, or", 22, INK, 700), T(870, 435, "replace the follower with a reactive agent", 22, "#188038", 700)]
    (OUT / "divergence.svg").write_text(svgdoc(1600, 500, "".join(p)))
divergence()

bs.budget_bar(OUT / "budget.svg", [("plan", 15, "edge"), ("compute the misses", 165, "service"), ("decide", 15, "data")],
              total=240, unit="min", title="A release gate, from the request to the verdict (initial target: 4 hours)")
print(sorted(pp.name for pp in OUT.glob("*.svg")))
