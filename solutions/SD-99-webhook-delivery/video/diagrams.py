#!/usr/bin/env python3
"""SD-99 outbound webhook and partner event-delivery platform: every picture for the video and the written design -> ./svg/*.svg.
One carried baseline (declared once, V1 -> V6), numbered flows, C4 context / containers / two component views (the challenges
are drawn on them), sequences (one per functional requirement, one theory, two challenge fixes), Chen and physical models.
Run: python3 diagrams.py"""
import pathlib, sys
sys.path.insert(0, str(pathlib.Path.home() / ".claude/skills/slide-video-kit/scripts"))
import basesvg as bs
import c4svg as c4
import seqsvg as sq
import erdsvg as er

OUT = pathlib.Path(__file__).resolve().parent / "svg"; OUT.mkdir(exist_ok=True)

# ───────────────────────────── 1 · the carried baseline (container level) ─────────────────────────────
# A U-shaped spine: events travel left to right along the top row (producer -> relay -> log -> fan-out),
# drop into the delivery store, and travel right to left along the middle row (store -> dispatcher -> egress
# -> the merchant's endpoint). What we keep and what controls the loop sit in the bottom row.
X = [15, 357, 699, 1041, 1383]; W = 190; YA, YB, YC, H = 50, 320, 580, 130
b = bs.Baseline(1600, 740)
b.node("pro", X[0], YA, W, H, "service", "Producers", "origination · servicing")
b.node("mer", X[0], YB, W, H, "client", "Merchant endpoint", "POS, ERP, bank")
b.node("rel", X[1], YA, W, H, "service", "Outbox relay", "row → log", since=2)
b.node("log", X[2], YA, W, H, "queue", "Event log", "by loan", since=2, shape="queue")
b.node("dsp", X[2], YB, W, H, "service", "Dispatcher", "workers", since=2)
b.node("fan", X[3], YA, W, H, "service", "Fan-out", "match, write rows", since=3)
b.node("dst", X[3], YB, W, H, "data", "Delivery store", "a row each", since=3, shape="db")
b.node("att", X[2], YC, W, H, "data", "Attempt log", "every try", since=3, shape="db")
b.node("api", X[1], YC, W, H, "edge", "Webhooks API", "logs · replay", since=3)
b.node("hl", X[3], YC, W, H, "service", "Endpoint health", "breaker · ramp", since=4)
b.node("egr", X[1], YB, W, H, "edge", "Egress proxy", "public IPs only", since=5)
b.node("reg", X[4], YA, W, H, "service", "Contract renderer", "pinned versions", since=6)

mid = lambda i: (X[i] + W + X[i + 1]) / 2
b.edge("p-m", "pro", "mer", "POST", src="b:0.5", dst="t:0.5", until=1, at=(170, 285))
b.edge("p-r", "pro", "rel", "rows", src="r:0.5", dst="l:0.5", since=2, at=(mid(0), 103))
b.edge("r-l", "rel", "log", "publish", src="r:0.5", dst="l:0.5", since=2, at=(mid(1), 103))
b.edge("l-d", "log", "dsp", "consume, retry", src="b:0.5", dst="t:0.5", since=2, until=2, at=(880, 285))
b.edge("d-m", "dsp", "mer", "POST, retries", src="l:0.5", dst="r:0.5", since=2, until=4, at=(450, 373))
b.edge("l-f", "log", "fan", "consume", src="r:0.5", dst="l:0.5", since=3, at=(mid(2), 103))
b.edge("f-s", "fan", "dst", "rows", src="b:0.5", dst="t:0.5", since=3, at=(1220, 285))
b.edge("s-d", "dst", "dsp", "claim", src="l:0.5", dst="r:0.5", since=3, at=(mid(2), 373))
b.edge("d-a", "dsp", "att", "every try", src="b:0.5", dst="t:0.5", since=3, at=(880, 545))
b.edge("api-a", "api", "att", "logs", src="r:0.5", dst="l:0.5", since=3, at=(mid(1), 633))
b.edge("api-s", "api", "dst", "replay", src="t:0.85", dst="b:0.2", via=[(518, 520), (1079, 520)], since=3, at=(640, 508))
b.edge("a-h", "att", "hl", "outcomes", src="r:0.5", dst="l:0.5", since=4, at=(mid(2), 633))
b.edge("h-s", "hl", "dst", "pause", src="t:0.5", dst="b:0.5", since=4, at=(1200, 545))
b.edge("d-e", "dsp", "egr", "signed", src="l:0.5", dst="r:0.5", since=5, at=(mid(1), 373))
b.edge("e-m", "egr", "mer", "POST", src="l:0.5", dst="r:0.5", since=5, at=(mid(0), 373))
b.edge("f-g", "fan", "reg", "render", src="r:0.5", dst="l:0.5", since=6, at=(mid(3), 103))

def sv(name, **view):
    b.save(OUT / name, **view)

sv("base-v1.svg", upto=1, legend=True)
sv("base-v2.svg", upto=2, new=2, legend=True)
sv("base-v3.svg", upto=3, new=3, legend=True, order=["fan", "dst", "att", "api"])
sv("base-v4.svg", upto=4, new=4, keep=["att", "hl", "dst", "dsp"])
sv("base-v5.svg", upto=5, new=5, keep=["dsp", "egr", "mer"])
sv("base-v6.svg", upto=6, new=6, keep=["log", "fan", "reg", "dst"])
sv("base-final.svg", upto=6, legend=True, flow=["p-r", "r-l", "l-f", "f-g", "f-s", "s-d", "d-e", "e-m"])
sv("map.svg", upto=6, attack=["pro", "dsp", "hl", "fan", "egr", "reg", "att"])
sv("alt.svg", upto=6, keep=["dst", "dsp", "egr", "mer"], alt=["dsp"])
sv("flow-fr2.svg", upto=3, flow=["p-r", "r-l", "l-f", "f-s"], keep=["pro", "rel", "log", "fan", "dst"])
sv("flow-fr3.svg", upto=5, flow=["f-s", "s-d", "d-e", "e-m", "d-a"], keep=["fan", "dst", "dsp", "egr", "mer", "att"])
sv("ch1-attack.svg", upto=1, attack=["pro"], keep=["pro", "mer"], hot=["p-m"])
sv("ch1-fix.svg", upto=2, fix=["rel"], keep=["pro", "rel", "log"], ok=["p-r", "r-l"])
sv("ch7-attack.svg", upto=6, attack=["att"], keep=["dsp", "att", "api", "hl"])
sv("ch7-fix.svg", upto=6, fix=["att", "hl", "api"], keep=["dsp", "att", "api", "hl"], ok=["d-a", "api-a", "a-h"])

# ───────────────────────────── 2 · C4 context and containers ─────────────────────────────────────────
d = c4.Diagram(1830, 780)
d.node("org", 40, 40, 360, 160, "ext", "Origination (SD-82)", "Internal system", "Applications, loans.", size=26)
d.node("svc", 40, 300, 360, 160, "ext", "Servicing (SD-95)", "Internal system", "Payments, refunds.", size=26)
d.node("dev", 40, 570, 360, 160, "person", "Merchant developer", "Person", "Registers, replays.", size=26)
d.node("sys", 720, 290, 420, 200, "system", "Webhook platform", "Software System", "Signed events, retried.", size=28)
d.node("pos", 1460, 40, 350, 160, "ext", "Merchant POS / ERP", "External", "20,000 endpoints.", size=26)
d.node("bnk", 1460, 300, 350, 160, "ext", "Partner bank", "External", "Loan-level events.", size=26)
d.node("kms", 1460, 570, 350, 160, "ext", "Key service", "External", "Signing secrets.", size=26)
d.edge("org", "sys", "Loan events", "outbox, log", src="r:0.7", dst="l:0.2", at=(560, 245), size=22)
d.edge("svc", "sys", "Payment events", "outbox, log", src="r:0.5", dst="l:0.5", at=(560, 365), size=22)
d.edge("dev", "sys", "Endpoints, replay", "HTTPS", src="r:0.3", dst="l:0.8", at=(560, 560), size=22)
d.edge("sys", "pos", "Signed POST", "HTTPS", src="r:0.2", dst="l:0.7", at=(1300, 240), size=22)
d.edge("sys", "bnk", "Signed POST", "HTTPS, mTLS", src="r:0.5", dst="l:0.5", at=(1300, 365), size=22)
d.edge("sys", "kms", "Secrets", "API", src="r:0.8", dst="l:0.4", at=(1300, 560), size=22)
d.save(OUT / "c4-context.svg", order=["org", "svc", "sys", "pos", "bnk", "dev", "kms"])

CX, CW, CY, CH, CS = [40, 400, 760, 1120], 290, [50, 315, 580], 170, 25
def containers(name, upto=6, **view):
    d = c4.Diagram(1830, 790, canon="containers")
    d.boundary(15, 20, 1440, 760, "Webhook platform", "Software System", top="left")
    d.node("rel", CX[0], CY[0], CW, CH, "container", "Outbox relay", "Worker", "Outbox to the log.", size=CS)
    d.node("log", CX[1], CY[0], CW, CH, "queue", "Event log", "Log", "Domain events, by loan.", size=CS)
    d.node("fan", CX[2], CY[0], CW, CH, "container", "Fan-out", "Consumer", "Match subscriptions.", size=CS)
    d.node("reg", CX[3], CY[0], CW, CH, "container", "Contract renderer", "Registry", "Public versions.", size=CS, since=6)
    d.node("egr", CX[0], CY[1], CW, CH, "container", "Egress proxy", "Proxy", "Public addresses only.", size=CS, since=5)
    d.node("dsp", CX[1], CY[1], CW, CH, "container", "Dispatcher", "Workers", "Claim, sign, send.", size=CS)
    d.node("dst", CX[2], CY[1], CW, CH, "db", "Delivery store", "Relational", "One row per delivery.", size=CS)
    d.node("api", CX[0], CY[2], CW, CH, "container", "Webhooks API", "Service", "Endpoints, logs, replay.", size=CS)
    d.node("att", CX[1], CY[2], CW, CH, "db", "Attempt log", "Relational", "Every try, 30 days.", size=CS)
    d.node("hl", CX[2], CY[2], CW, CH, "container", "Endpoint health", "Control loop", "Breaker, ramp, disable.", size=CS, since=4)
    d.node("mer", 1530, CY[1], 290, CH, "ext", "Merchant endpoints", "External", "POS, ERP, bank.", size=CS)
    d.edge("rel", "log", "", "", src="r", dst="l")
    d.edge("log", "fan", "", "", src="r", dst="l")
    d.edge("fan", "reg", "", "", src="r", dst="l")
    d.edge("fan", "dst", "rows", "SQL", src="b", dst="t", at=(990, 280), size=22)
    d.edge("dst", "dsp", "claim", "", src="l", dst="r", at=(725, 300), size=22)
    d.edge("dsp", "egr", "POST", "", src="l", dst="r", at=(365, 300), size=22)
    d.edge("egr", "mer", "HTTPS", "", src="b:0.5", dst="b:0.5", via=[(185, 520), (1675, 520)], at=(1300, 510), size=22)
    d.edge("dsp", "mer", "", "", src="b:0.15", dst="b:0.5", via=[(443, 520), (1675, 520)], until=4)
    d.edge("dsp", "att", "tries", "", src="b:0.6", dst="t:0.6", at=(640, 545), size=22)
    d.edge("api", "att", "", "", src="r", dst="l")
    d.edge("att", "hl", "", "", src="r", dst="l")
    d.edge("hl", "dst", "pause", "", src="t", dst="b", at=(985, 545), size=22)
    order = [n for n in ["rel", "log", "fan", "reg", "dst", "dsp", "egr", "mer", "att", "api", "hl"] if n in d.nmeta and d.nmeta[n].get("since", 1) <= upto]
    d.save(OUT / name, order=order, upto=upto, **view)

containers("c4-containers.svg", upto=3)
containers("th-where.svg", badges={"rel": "M1", "log": "M2", "dst": "M3", "dsp": "M3 · M4", "hl": "M4", "fan": "M5", "egr": "M6"})
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent / "src")); import stack
c4.Diagram.OVERRIDE = {k: (v[1], v[2]) for k, v in stack.C4.items()}
containers("c4-containers-tech.svg", upto=6, new=[4, 5, 6])
c4.Diagram.OVERRIDE = {}

# ───────────── C4 level 3: the dispatcher (challenges 2, 3 and 5 are drawn on it) ─────────────
def dispatcher():
    d = c4.Diagram(1830, 770, canon="comp-dsp")
    d.boundary(275, 30, 1250, 720, "Dispatcher", "Container: Go workers", top="left")
    d.node("dst", 20, 300, 220, 160, "db", "Delivery store", "PostgreSQL", "Due rows.", size=25)
    d.node("clm", 310, 300, 290, 160, "component", "Claimer", "SKIP LOCKED + lease", "Only endpoints under cap.", size=25)
    d.node("pool", 310, 80, 290, 160, "component", "Tier pools", "bulkheads", "Bank · large · long tail.", size=25)
    d.node("lim", 700, 300, 300, 160, "component", "Endpoint limiter", "semaphore", "10 in flight by default.", size=25)
    d.node("brk", 700, 80, 300, 160, "component", "Breaker", "per endpoint", "Open after 5 failures.", size=25)
    d.node("sgn", 1100, 80, 300, 160, "component", "Signer", "HMAC-SHA256", "id.timestamp.body", size=25)
    d.node("cli", 1100, 300, 300, 160, "component", "HTTP client", "2 s / 10 s", "Keep-alive; 4 KB read.", size=25)
    d.node("res", 700, 540, 300, 160, "component", "Result writer", "Component", "Delivered, or next try.", size=25)
    d.node("egr", 1580, 300, 240, 160, "container", "Egress proxy", "Smokescreen", "", size=25)
    d.node("kms", 1580, 80, 240, 160, "ext", "Key service", "KMS", "", size=25)
    d.node("hl", 1580, 540, 240, 160, "container", "Endpoint health", "control loop", "", size=25)
    d.edge("dst", "clm", "", "", src="r", dst="l")
    d.edge("pool", "clm", "", "", src="b", dst="t")
    d.edge("clm", "lim", "", "", src="r", dst="l")
    d.edge("brk", "lim", "", "", src="b", dst="t")
    d.edge("lim", "cli", "", "", src="r", dst="l")
    d.edge("sgn", "cli", "", "", src="b", dst="t")
    d.edge("kms", "sgn", "", "", src="l", dst="r")
    d.edge("cli", "egr", "", "", src="r", dst="l")
    d.edge("cli", "res", "answer", "", src="b", dst="r", via=[(1250, 620)], at=(1170, 605), size=22)
    d.edge("res", "dst", "", "", src="l", dst="b", via=[(130, 620)])
    d.edge("res", "hl", "", "", src="r:0.8", dst="l:0.8", via=[(1290, 668)])
    return d
DO = ["dst", "clm", "pool", "lim", "brk", "cli", "sgn", "kms", "egr", "res", "hl"]
dp = dispatcher(); dp.save(OUT / "c4-comp-dsp.svg", order=DO)
dispatcher().save(OUT / "ch2-attack.svg", keep=["dst", "clm", "lim", "cli", "egr"], attack=["lim", "cli"])
dispatcher().save(OUT / "ch2-fix.svg", keep=["clm", "pool", "lim", "brk", "cli"], fix=["pool", "lim", "brk"])
dispatcher().save(OUT / "ch3-attack.svg", keep=["clm", "cli", "res", "dst"], attack=["res"])
dispatcher().save(OUT / "ch3-fix.svg", keep=["res", "hl"], fix=["res", "hl"])
dispatcher().save(OUT / "ch5-attack.svg", keep=["lim", "cli", "egr", "sgn"], attack=["cli", "egr"])
dispatcher().save(OUT / "ch5-fix.svg", keep=["lim", "cli", "egr", "sgn", "kms"], fix=["egr", "sgn"])

# ───────────── C4 level 3: fan-out (challenges 4 and 6 are drawn on it) ─────────────
def fanout():
    d = c4.Diagram(1830, 770, canon="comp-fan")
    d.boundary(275, 30, 1250, 720, "Fan-out", "Container: Go consumer group", top="left")
    d.node("log", 20, 300, 220, 160, "queue", "Event log", "Kafka", "By loan.", size=25)
    d.node("con", 310, 300, 290, 160, "component", "Log consumer", "offsets after write", "Repeats a batch on crash.", size=25)
    d.node("sub", 310, 80, 290, 160, "component", "Subscription cache", "in memory", "Refreshed by changes.", size=25)
    d.node("mat", 700, 300, 300, 160, "component", "Matcher", "type × merchant", "One event, N endpoints.", size=25)
    d.node("ren", 700, 80, 300, 160, "component", "Renderer", "per pinned version", "Internal → public.", size=25)
    d.node("pay", 700, 540, 300, 160, "component", "Payload writer", "once per event", "Not once per delivery.", size=25)
    d.node("wr", 1100, 300, 300, 160, "component", "Delivery writer", "batch insert", "UNIQUE(endpoint, event).", size=25)
    d.node("seq", 1100, 540, 300, 160, "component", "Sequence check", "per loan", "Carries the producer's seq.", size=25)
    d.node("dst", 1580, 300, 240, 160, "db", "Delivery store", "PostgreSQL", "", size=25)
    d.node("reg", 1580, 80, 240, 160, "container", "Schema registry", "public versions", "", size=25)
    d.node("api", 20, 80, 220, 160, "container", "Webhooks API", "subscriptions", "", size=25)
    d.edge("log", "con", "", "", src="r", dst="l")
    d.edge("api", "sub", "", "", src="r", dst="l")
    d.edge("con", "mat", "", "", src="r", dst="l")
    d.edge("sub", "mat", "", "", src="r:0.7", dst="l:0.2")
    d.edge("mat", "ren", "", "", src="t", dst="b")
    d.edge("reg", "ren", "", "", src="l", dst="r")
    d.edge("mat", "wr", "", "", src="r", dst="l")
    d.edge("mat", "pay", "", "", src="b", dst="t")
    d.edge("pay", "seq", "", "", src="r", dst="l")
    d.edge("seq", "wr", "", "", src="t", dst="b")
    d.edge("wr", "dst", "", "", src="r", dst="l")
    return d
FO = ["log", "con", "api", "sub", "mat", "ren", "reg", "pay", "seq", "wr", "dst"]
fanout().save(OUT / "c4-comp-fan.svg", order=FO)
fanout().save(OUT / "ch4-attack.svg", keep=["con", "mat", "wr", "dst"], attack=["wr"])
fanout().save(OUT / "ch4-fix.svg", keep=["con", "mat", "pay", "seq", "wr"], fix=["seq", "wr"])
fanout().save(OUT / "ch6-attack.svg", keep=["con", "mat", "wr", "ren"], attack=["mat"])
fanout().save(OUT / "ch6-fix.svg", keep=["mat", "ren", "reg", "wr"], fix=["ren", "reg"])

# ───────────────────────────── 3 · sequences ─────────────────────────────────────────────────────────
def seq(name, parts, steps, **kw):
    s = sq.Seq(1500, size=22, row=50, **kw)
    for p in parts: s.part(*p)
    for st in steps:
        k = st[0]
        if k == "m": s.msg(st[1], st[2], st[3], **(st[4] if len(st) > 4 else {}))
        elif k == "r": s.ret(st[1], st[2], st[3], **(st[4] if len(st) > 4 else {}))
        elif k == "n": s.note(st[1], st[2], st[3], *(st[4:5]))
    s.save(OUT / f"{name}.svg")

seq("seq-th-claim",
    [("ds", "Dispatcher", "container"), ("st", "Delivery store", "db"), ("mp", "Merchant", "ext")],
    [("m", "ds", "st", "claim due rows under the cap; lease 30 s"),
     ("m", "ds", "mp", "POST, signed, timeout 10 s"),
     ("n", "mp", "mp", "no answer in 10 s", "red"),
     ("m", "ds", "st", "attempt 3 failed: next = now + random(0, 40 s)", dict(hl=True)),
     ("n", "st", "st", "row is due again later; nothing held in memory")])
seq("seq-fr1",
    [("dv", "Developer", "person"), ("ap", "Webhooks API", "container"), ("eg", "Egress proxy", "container"), ("ep", "Endpoint", "ext")],
    [("m", "dv", "ap", "POST /v1/webhook-endpoints {url, events, version}"),
     ("m", "ap", "eg", "verification ping with a challenge"),
     ("m", "eg", "ep", "resolve, check public IP, POST"),
     ("r", "ep", "ap", "200, echoes the challenge"),
     ("r", "ap", "dv", "201 {id, secret shown once}")])
seq("seq-fr2",
    [("pr", "Producer", "container"), ("db", "Producer DB", "db"), ("rl", "Outbox relay", "container"), ("lg", "Event log", "queue")],
    [("m", "pr", "db", "BEGIN; book loan; INSERT outbox; COMMIT"),
     ("m", "rl", "db", "read unsent rows in ID order"),
     ("m", "rl", "lg", "publish, key = loan ID"),
     ("r", "lg", "rl", "ack"),
     ("m", "rl", "db", "mark sent")])
seq("seq-fr3",
    [("fo", "Fan-out", "container"), ("st", "Delivery store", "db"), ("ds", "Dispatcher", "container"), ("eg", "Egress", "container"), ("ep", "Endpoint", "ext")],
    [("m", "fo", "st", "INSERT delivery (endpoint, event) unique"),
     ("m", "ds", "st", "claim under cap, lease"),
     ("m", "ds", "eg", "POST + Webhook-Signature"),
     ("m", "eg", "ep", "to the checked address"),
     ("r", "ep", "ds", "200 in 180 ms"),
     ("m", "ds", "st", "DELIVERED; attempt row written")])
seq("seq-fr4",
    [("dv", "Developer", "person"), ("ap", "Webhooks API", "container"), ("st", "Delivery store", "db"), ("ds", "Dispatcher", "container")],
    [("m", "dv", "ap", "POST replay {since: Dec 2 09:00, rate: 20/s}"),
     ("m", "ap", "st", "DEAD rows since then: PENDING, oldest first"),
     ("m", "ap", "st", "endpoint rate limit 20/s until drained"),
     ("m", "ds", "st", "claims as usual, under the cap and the rate"),
     ("r", "ap", "dv", "202 {replay_id, 240,000 queued}")])
seq("seq-ch3-ramp",
    [("hl", "Endpoint health", "container"), ("ds", "Dispatcher", "container"), ("ep", "ERP endpoint", "ext")],
    [("n", "hl", "hl", "breaker open since Dec 1; probe every minute"),
     ("m", "ds", "ep", "probe: one oldest delivery"),
     ("r", "ep", "ds", "200"),
     ("m", "hl", "ds", "half-open: 1 a second"),
     ("m", "hl", "ds", "no errors for 60 s: double, up to the cap"),
     ("n", "ep", "ep", "error rate over 5 %: halve the rate", "red")])
seq("seq-ch5-verify",
    [("ds", "Dispatcher", "container"), ("km", "Key service", "ext"), ("ep", "Merchant endpoint", "ext")],
    [("m", "ds", "km", "secret for endpoint ep_42 (cached 5 min)"),
     ("m", "ds", "ep", "POST; Webhook-Signature: t=…, v1=HMAC(id.t.body)"),
     ("n", "ep", "ep", "|now − t| ≤ 5 min, else reject", "red"),
     ("n", "ep", "ep", "constant-time compare against v1, v1-old"),
     ("r", "ep", "ds", "200, after storing the event ID")])

# ───────────────────────────── 4 · data models ───────────────────────────────────────────────────────
c = er.Chen(1930, 720, size=27)
c.entity("me", 200, 130, "MERCHANT"); c.entity("ep", 760, 130, "ENDPOINT"); c.entity("su", 1300, 130, "SUBSCRIPTION", weak=True)
c.entity("ev", 200, 460, "EVENT"); c.entity("dl", 760, 460, "DELIVERY"); c.entity("at", 1300, 460, "ATTEMPT", weak=True)
c.rel("ow", 480, 130, "OWNS"); c.rel("ls", 1030, 130, "LISTENS", identifying=True)
c.rel("fo", 480, 460, "FANS OUT"); c.rel("tr", 1030, 460, "TRIED BY", identifying=True); c.rel("to", 760, 295, "TO")
c.attr("mid", 120, 40, "merchant_id", of="me", key=True)
c.attr("eid", 700, 40, "endpoint_id", of="ep", key=True); c.attr("url", 900, 40, "url", of="ep"); c.attr("ver", 600, 215, "api_version", of="ep")
c.attr("et", 1460, 40, "event_type", of="su", partial=True)
c.attr("evid", 90, 560, "event_id", of="ev", key=True); c.attr("sq", 330, 560, "loan seq", of="ev")
c.attr("st", 640, 560, "state", of="dl"); c.attr("nx", 900, 560, "next_attempt_at", of="dl")
c.attr("an", 1240, 560, "attempt_no", of="at", partial=True); c.attr("sc", 1460, 560, "status", of="at")
c.link("me", "ow", "1"); c.link("ow", "ep", "N", total=True)
c.link("ep", "ls", "1"); c.link("ls", "su", "N", total=True)
c.link("ev", "fo", "1"); c.link("fo", "dl", "N", total=True)
c.link("dl", "tr", "1"); c.link("tr", "at", "N", total=True)
c.link("dl", "to", "N", src="t", dst="b"); c.link("to", "ep", "1", src="t", dst="b")
c.legend(1620, 60, size=22, rows=["rect", "rect2", "dia", "dia2", "oval", "key", "dbl"])
c.note(60, 640, 900, "A delivery is one event to one endpoint; attempts belong to it.")
c.save(OUT / "erd-chen.svg", order=["me", "ow", "ep", "ls", "su", "ev", "fo", "dl", "to", "tr", "at"])

e = er.ERD(1800, 880, size=24)
e.entity("ep", 30, 40, 520, "endpoint", [("id", "text", "PK"), ("merchant_id", "text", "IX"), ("url", "text", ""), ("api_version", "date", ""),
         ("tier · cap", "int", ""), ("state", "text", "")], kind="focus", caption="secret lives in the key service")
e.entity("ev", 680, 40, 470, "event_payload", [("event_id", "text", "PK"), ("type", "text", ""), ("loan_id · seq", "text", "IX"),
         ("body", "jsonb", ""), ("created_at", "ts", "")], caption="one copy per event")
e.entity("su", 1300, 40, 470, "subscription", [("endpoint_id", "text", "PK"), ("event_type", "text", "PK")], caption="cached in fan-out")
e.entity("dl", 30, 470, 520, "delivery", [("id", "bigint", "PK"), ("endpoint_id", "text", "SK"), ("event_id", "text", "UQ*"), ("state", "text", ""),
         ("attempt_no", "int", ""), ("next_attempt_at", "ts", "IX"), ("lease_until", "ts", "")], caption="* unique with endpoint_id; sharded by it")
e.entity("at", 680, 470, 470, "attempt", [("delivery_id", "bigint", "PK"), ("attempt_no", "int", "PK"), ("status", "int", ""), ("latency_ms", "int", ""),
         ("error", "text", "")], kind="ext", caption="partitioned by day; 30 days")
e.rel("dl", "ep", "N", "1", src="t:0.5", dst="b:0.5", label="endpoint_id", at=(330, 430))
e.rel("dl", "at", "1", "N", src="r:0.3", dst="l:0.3", label="delivery_id", at=(615, 495))
e.rel("dl", "ev", "N", "1", src="r:0.1", dst="b:0.3", via=[(820, 500)], label="", at=(700, 460))
e.note(1220, 470, 550, "The timer is a column: a partial index on next_attempt_at WHERE state = 'PENDING'.")
e.save(OUT / "erd-physical.svg")
print("ok")
