#!/usr/bin/env python3
"""SD-44 payments and the double-entry ledger: every picture for the video and the written design -> ./svg/*.svg.
One canonical container view (c4svg, since= per box and edge), saved as views: V1 -> V4, flows, the challenge map, badges.
Three component views (payment service, ledger database, reconciliation) carry the challenges. Sequences, both data models,
the state machine (built up state by state), figures.   Run: python3 diagrams.py"""
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
# 5 × 3 grid. Middle row: the spine (merchant → API → service → adapter → processor). Top row: the event path.
# Bottom row: the books and their checks. Columns B–D are the system; A and E are outside it.
X = dict(A=20, B=400, C=780, D=1160, E=1540); Y = dict(R0=100, R1=360, R2=620); W, H, SZ = 250, 140, 26
def P(cell): return X[cell[0]], Y[cell[1:]]
BOX = {  # id: (cell, kind, title, type, description, since)
    "mer":  ("AR1", "person", "Merchant", "Person", "Checkout, retries.", 1),
    "fin":  ("AR2", "person", "Finance ops", "Person", "Owns the breaks.", 3),
    "proc": ("ER1", "ext", "Processor", "Card network, bank", "Answers late, or never.", 1),
    "api":  ("BR1", "container", "Payments API", "Service", "Key first, deadline.", 1),
    "svc":  ("CR1", "container", "Payment service", "Service", "State machine.", 1),
    "adp":  ("DR1", "container", "Processor adapter", "Service", "Our reference.", 2),
    "db":   ("CR2", "db", "Ledger database", "Relational", "State and books.", 1),
    "rly":  ("CR0", "queue", "Outbox relay + log", "Debezium, Kafka", "Commit order.", 3),
    "wh":   ("BR0", "container", "Webhook sender", "Service", "Signed, retried.", 3),
    "inq":  ("DR0", "container", "Inquiry job", "Worker", "Ends an UNKNOWN.", 3),
    "rec":  ("BR2", "container", "Reconciliation", "Batch", "Line by line.", 3),
    "bal":  ("DR2", "container", "Balance projector", "Worker", "From the entries.", 4),
}

def canon(labels=None):
    """The one container diagram. labels: id -> (title, type, description) to show technologies (5.1) instead."""
    d = c4.Diagram(1810, 830, canon="containers")
    d.boundary(375, 20, 1060, 790, "Payments and ledger", "Software System", top="right")
    for k, (cell, kind, t, typ, desc, since) in BOX.items():
        if labels and k in labels: typ, desc = labels[k][1], labels[k][2]
        x, y = P(cell)
        d.node(k, x, y, W, H, kind, t, typ, desc, size=SZ, since=since)
    E = d.edge
    E("mer", "api", "pay, refund", "", src="r", dst="l", at=(335, 412), size=21, eid="m-a")
    E("api", "svc", "key, 2 s", "", src="r", dst="l", at=(715, 412), size=21, eid="a-s")
    E("svc", "db", "one transaction", "", src="b", dst="t", at=(905, 560), size=21, eid="s-d")
    E("svc", "proc", "charge, synchronous", "", src="r", dst="l", at=(1285, 412), size=21, eid="s-p", until=1, width=330)
    E("svc", "adp", "authorise", "", src="r", dst="l", at=(1095, 412), size=21, eid="s-a", since=2)
    E("adp", "proc", "call", "", src="r", dst="l", at=(1475, 412), size=21, eid="a-p", since=2)
    E("db", "rly", "write-ahead log", "", src="l:0.3", dst="b:0.3", via=[(715, 662), (715, 300), (857, 300)], at=(585, 585), size=21, eid="d-r", since=3, width=210)
    E("rly", "wh", "events", "", src="l", dst="r", at=(715, 145), size=21, eid="r-w", since=3)
    E("wh", "mer", "webhooks", "", src="l", dst="t", via=[(145, 170)], at=(272, 150), size=21, eid="w-m", since=3)
    E("inq", "adp", "ask by ref.", "", src="b:0.8", dst="t:0.8", at=(1290, 275), size=21, eid="i-a", since=3)
    E("inq", "svc", "resolve", "", src="b:0.15", dst="t:0.8", via=[(1197, 300), (980, 300)], at=(1090, 285), size=21, eid="i-s", since=3)
    E("rec", "db", "expectations", "", src="r:0.7", dst="l:0.7", at=(715, 748), size=21, eid="c-d", since=3)
    E("rec", "fin", "breaks", "", src="l", dst="r", at=(335, 672), size=21, eid="c-f", since=3)
    E("proc", "rec", "settlement file, daily", "", src="b", dst="b", via=[(1665, 800), (525, 800)], at=(1100, 796), size=21, eid="p-c", since=3, width=360)
    E("db", "bal", "entries", "", src="r:0.3", dst="l:0.3", at=(1095, 640), size=21, eid="d-b", since=4)
    E("bal", "db", "balances", "", src="l:0.7", dst="r:0.7", at=(1095, 735), size=21, eid="b-d", since=4)
    d.legend(30, 120, ("person", "container", "db", "queue", "ext"), vertical=True)
    return d

d = canon()
d.save(OUT / "base-v1.svg", upto=1, order=["mer", "api", "svc", "db", "proc"])
d.save(OUT / "base-v2.svg", upto=2, new=2, order=["adp"])
d.save(OUT / "base-v3.svg", upto=3, new=3, order=[("rly", "wh"), "inq", "rec", "fin"])
d.save(OUT / "base-v4.svg", upto=4, new=4, order=["bal"])
d.save(OUT / "flow-pay.svg", upto=3, flow=["m-a", "a-s", "s-d", "s-a", "a-p"])
d.save(OUT / "flow-recon.svg", upto=3, flow=["p-c", "c-d", "c-f"])
d.save(OUT / "map.svg", upto=4, attack=["adp", "api", "rly", "bal", "rec", "fin"], keep=None)
d.save(OUT / "ch3-attack.svg", upto=3, attack=["svc"], keep=["svc", "db", "rly"])
d.save(OUT / "ch6-attack.svg", upto=4, attack=["fin"], keep=["api", "svc", "db", "rec", "fin"])
d.save(OUT / "ch6-fix.svg", upto=4, fix=["api", "db", "rec"], keep=["api", "svc", "db", "rec", "fin"])
d.save(OUT / "recap.svg", upto=4, badges={"api": "M1", "svc": "M2", "db": "M3 M4", "adp": "M2",
                                          "rly": "M4", "inq": "M2", "rec": "M5", "bal": "M3"})
d.save(OUT / "alt.svg", upto=4, focus=["rly", "adp", "db"], keep=["svc", "adp", "proc", "db", "rly"])
dt = canon(stack.C4)
dt.save(OUT / "c4-containers-tech.svg", upto=4, focus=["api", "svc", "adp", "db", "rly", "rec"], keep=None)

# ───────────────────────────── 2 · C4 context ────────────────────────────────────────────────────────
x = c4.Diagram(1600, 700)
x.node("cus", 40, 80, 320, 150, "person", "Customer", "Person", "Pays at a merchant.", size=26)
x.node("mer", 40, 440, 320, 150, "ext", "Merchant system", "External system", "Creates payments, gets webhooks.", size=26)
x.node("sys", 620, 250, 380, 190, "system", "Payments and ledger", "Software System", "Authorises, captures, keeps the books.", size=28)
x.node("proc", 1240, 80, 320, 150, "ext", "Processor", "External system", "Moves the money; has its own books.", size=26)
x.node("fin", 1240, 440, 320, 150, "person", "Finance ops", "Person", "Owns breaks and corrections.", size=26)
x.edge("cus", "mer", "pays", "", src="b", dst="t", at=(200, 340), size=22)
x.edge("mer", "sys", "payments, webhooks", "HTTPS", src="r", dst="l:0.75", at=(490, 520), size=22, width=250)
x.edge("sys", "proc", "authorise; settlement files", "", src="r:0.25", dst="l", at=(1120, 160), size=22, width=300)
x.edge("sys", "fin", "breaks", "", src="r:0.75", dst="l", at=(1120, 520), size=22)
x.legend(40, 660, ("person", "system", "ext"))
x.save(OUT / "c4-context.svg", order=["cus", "mer", "sys", "proc", "fin"])

# ───────────────────────────── 3 · component views (C4 level 3) ──────────────────────────────────────
CX = [20, 300, 560, 820, 1080, 1340, 1600]; CW, CH, CS = 210, 150, 25
def comp(name_box, techline):
    d = c4.Diagram(1830, 770, canon="comp:" + name_box)
    d.boundary(275, 40, 1030, 700, name_box, techline, top="left")
    return d

s = comp("Payment service", "Container: Go")
s.node("api", CX[0], 330, 200, CH, "container", "Payments API", "Go", "Deadline 2 s.", size=CS)
s.node("idem", CX[1], 330, CW, CH, "component", "Idempotency guard", "Unique insert", "Key first, with a hash.", size=CS)
s.node("sm", CX[2], 330, CW, CH, "component", "State machine", "Conditional updates", "Legal edges only.", size=CS)
s.node("att", CX[3], 330, CW, CH, "component", "Attempt writer", "Our reference", "Committed before the call.", size=CS)
s.node("port", CX[4], 330, CW, CH, "component", "Processor port", "Deadline 1.9 s", "Three error classes.", size=CS)
s.node("adp", CX[5], 330, CW, CH, "container", "Adapter", "Go, per processor", "", size=CS)
s.node("proc", CX[6], 330, 210, CH, "ext", "Processor", "External", "", size=CS)
s.node("inq", CX[5], 90, CW, CH, "container", "Inquiry job", "Worker", "Backoff, by reference.", size=CS)
s.node("db", 300, 570, 760, 130, "db", "Ledger database", "PostgreSQL", "Key row · payment · journal · outbox", size=CS)
s.edge("api", "idem", "", "", src="r", dst="l")
s.edge("idem", "sm", "", "", src="r", dst="l")
s.edge("sm", "att", "", "", src="r", dst="l")
s.edge("att", "port", "", "", src="r", dst="l")
s.edge("port", "adp", "", "", src="r", dst="l")
s.edge("adp", "proc", "", "", src="r", dst="l")
s.edge("idem", "db", "key row", "", src="b", dst="t:0.14", at=(405, 530), size=21)
s.edge("sm", "db", "state, entries, outbox", "", src="b", dst="t:0.38", at=(665, 530), size=21, width=250)
s.edge("att", "db", "attempt, first", "", src="b", dst="t:0.62", at=(925, 530), size=21)
s.edge("inq", "adp", "inquire", "", src="b", dst="t", at=(1445, 280), size=21)
s.edge("inq", "sm", "resolve", "", src="l", dst="t", via=[(665, 165)], at=(1000, 150), size=21)
s.legend(40, 120, ("component", "db", "container", "ext"), vertical=True)
SO = ["api", "idem", "sm", "att", "port", "db", "adp", "proc", "inq"]
s.save(OUT / "c4-comp-service.svg", order=SO)
s.save(OUT / "ch1-attack.svg", keep=["att", "port", "adp", "proc"], attack=["port"])
s.save(OUT / "ch1-fix.svg", keep=["sm", "att", "port", "inq", "adp"], fix=["sm", "att", "inq"])
s.save(OUT / "ch2-attack.svg", keep=["api", "idem", "sm", "db"], attack=["idem"])
s.save(OUT / "ch2-fix.svg", keep=["idem", "sm", "db"], fix=["idem", "db"])

b = comp("Ledger database", "Container: PostgreSQL, one partition of 64")
b.node("svc", CX[0], 330, 200, CH, "container", "Payment service", "Go", "One transaction.", size=CS)
b.node("tx", CX[1], 330, CW, CH, "component", "One transaction", "BEGIN … COMMIT", "State, entries, outbox.", size=CS)
b.node("pay", CX[2], 90, CW, CH, "component", "Payment row", "Mutable", "Conditional updates.", size=CS)
b.node("jr", CX[2], 330, CW, CH, "component", "Journal entries", "By merchant, ×16", "Insert only.", size=CS)
b.node("ob", CX[2], 570, CW, CH, "component", "Outbox table", "Same transaction", "One row per event.", size=CS)
b.node("bal", CX[3], 330, CW, CH, "component", "Balance projection", "Derived", "Seconds behind.", size=CS)
b.node("pw", CX[4], 330, CW, CH, "component", "Payout writer", "One per merchant", "Checks the sum.", size=CS)
b.node("wal", CX[3], 570, CW, CH, "component", "Write-ahead log", "WAL", "Commit order.", size=CS)
b.node("slot", CX[4], 570, CW, CH, "component", "Replication slot", "Logical decoding", "Holds log for Debezium.", size=CS)
b.node("deb", CX[5], 570, CW, CH, "container", "Debezium", "Kafka Connect", "Reads the slot.", size=CS)
b.node("kf", CX[6], 570, 210, CH, "queue", "Kafka", "By merchant", "", size=CS)
b.edge("svc", "tx", "", "", src="r", dst="l")
b.edge("tx", "pay", "", "", src="t", dst="l", via=[(405, 165)])
b.edge("tx", "jr", "", "", src="r", dst="l")
b.edge("tx", "ob", "", "", src="b", dst="l", via=[(405, 645)])
b.edge("jr", "bal", "", "", src="r", dst="l")
b.edge("bal", "pw", "", "", src="r", dst="l")
b.edge("ob", "wal", "", "", src="r", dst="l")
b.edge("wal", "slot", "", "", src="r", dst="l")
b.edge("slot", "deb", "", "", src="r", dst="l")
b.edge("deb", "kf", "", "", src="r", dst="l")
b.legend(40, 120, ("component", "db", "container", "queue"), vertical=True)
BO = ["svc", "tx", "pay", "jr", "ob", "bal", "pw", "wal", "slot", "deb", "kf"]
b.save(OUT / "c4-comp-db.svg", order=BO)
b.save(OUT / "ch3-fix.svg", keep=["tx", "ob", "wal", "slot", "deb", "kf"], fix=["ob", "slot"])
b.save(OUT / "ch4-attack.svg", keep=["svc", "tx", "jr", "bal"], attack=["jr"])
b.save(OUT / "ch4-fix.svg", keep=["tx", "jr", "bal", "pw"], fix=["jr", "bal", "pw"])

r = comp("Reconciliation", "Container: Spark batch")
r.node("proc", CX[0], 330, 200, CH, "ext", "Processor", "External", "Settlement file.", size=CS)
r.node("file", CX[1], 330, CW, CH, "db", "Raw file store", "Object storage", "Unchanged.", size=CS)
r.node("match", CX[2], 330, CW, CH, "component", "Matcher", "Join by reference", "Amount, fee, state.", size=CS)
r.node("brk", CX[3], 330, CW, CH, "component", "Break writer", "Type, owner, age", "One row per line.", size=CS)
r.node("q", CX[4], 330, CW, CH, "queue", "Break queue", "Work queue", "Aged, owned.", size=CS)
r.node("fin", CX[5], 330, CW, CH, "person", "Finance ops", "Person", "", size=CS)
r.node("exp", CX[2], 570, CW, CH, "component", "Expectation builder", "SQL on the ledger", "By reference, net of fees.", size=CS)
r.node("fix", CX[4], 90, CW, CH, "component", "Corrector", "Reversing entries", "Tagged with the incident.", size=CS)
r.node("led", CX[3], 90, CW, CH, "db", "Ledger database", "PostgreSQL", "", size=CS)
r.edge("proc", "file", "", "", src="r", dst="l")
r.edge("file", "match", "", "", src="r", dst="l")
r.edge("match", "brk", "", "", src="r", dst="l")
r.edge("brk", "q", "", "", src="r", dst="l")
r.edge("q", "fin", "", "", src="r", dst="l")
r.edge("exp", "match", "expected", "", src="t", dst="b", at=(665, 530), size=21)
r.edge("match", "led", "settled", "", src="t", dst="l", via=[(665, 165)], at=(740, 150), size=21)
r.edge("fin", "fix", "approve", "", src="t", dst="r", via=[(1445, 165)], at=(1380, 150), size=21)
r.edge("fix", "led", "", "", src="l", dst="r")
r.legend(40, 120, ("component", "db", "queue", "person"), vertical=True)
RO = ["proc", "file", "exp", "match", "led", "brk", "q", "fin", "fix"]
r.save(OUT / "c4-comp-rec.svg", order=RO)
r.save(OUT / "ch5-attack.svg", keep=["proc", "file", "match", "brk"], attack=["match"])
r.save(OUT / "ch5-fix.svg", keep=["exp", "match", "brk", "q"], fix=["exp", "match", "brk"])
r.save(OUT / "ch5-fix2.svg", keep=["q", "fin", "fix", "led"], fix=["fix"])

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

seq("seq-th-post",
    [("sv", "Payment service", "container"), ("db", "Ledger partition", "db")],
    [("m", "sv", "db", "BEGIN"),
     ("m", "sv", "db", "UPDATE payment SET state = CAPTURED WHERE id = p-7731 AND state = AUTH_PENDING"),
     ("r", "db", "sv", "1 row: the edge was legal"),
     ("m", "sv", "db", "INSERT txn; INSERT 3 entries: D 1,050 · C 1,020 · C 30"),
     ("m", "sv", "db", "INSERT outbox row: payment.captured"),
     ("n", "db", "db", "deferred check at COMMIT: debits 1,050 = credits 1,050", "green"),
     ("m", "sv", "db", "COMMIT", dict(hl=True)),
     ("n", "db", "db", "unbalanced? the whole transaction is rejected", "red")])

seq("seq-pay",
    [("mr", "Merchant", "person"), ("api", "Payments API", "container"), ("db", "Ledger database", "db"), ("ad", "Adapter", "container"), ("pr", "Processor", "ext")],
    [("m", "mr", "api", "POST /payments, Idempotency-Key k-91, 1,050"),
     ("m", "api", "db", "insert key k-91 processing; payment AUTH_PENDING; attempt p-7731/1; commit"),
     ("m", "api", "ad", "authorise p-7731/1"),
     ("m", "ad", "pr", "authorise, reference p-7731/1"),
     ("r", "pr", "ad", "approved, 340 ms"),
     ("m", "api", "db", "one transaction: CAPTURED, journal entries, outbox row, key done", dict(hl=True)),
     ("r", "api", "mr", "201 captured")])

seq("seq-refund",
    [("mr", "Merchant", "person"), ("sv", "Payment service", "container"), ("db", "Ledger database", "db"), ("pr", "Processor", "ext")],
    [("m", "mr", "sv", "refund 2,500 on p-5520 (key r-1)"), ("m", "mr", "sv", "refund 2,500 on p-5520 (key r-2, 2 ms later)"),
     ("m", "sv", "db", "UPDATE refunded = refunded + 2,500 WHERE refunded + 2,500 <= captured (r-1): 1 row", dict(hl=True)),
     ("m", "sv", "db", "the same for r-2: 0 rows"),
     ("r", "sv", "mr", "r-2: 422 exceeds captured"),
     ("m", "sv", "pr", "refund 2,500, reference p-5520/r-1"),
     ("m", "sv", "db", "new journal transaction, dated now, referencing p-5520"),
     ("n", "sv", "sv", "day 92: a chargeback posts dated now; the closed month is untouched", "green")])

seq("seq-explain",
    [("au", "Auditor", "person"), ("sv", "Payment service", "container"), ("db", "Ledger database", "db")],
    [("m", "au", "sv", "balance of merchant payable acc-9, as of 31 Oct"),
     ("m", "sv", "db", "sum of entries on acc-9 up to that date, in one partition"),
     ("r", "db", "sv", "18,204,400 EUR, current to entry 991,200,731"),
     ("m", "sv", "db", "the entries, joined to their transactions and payments"),
     ("r", "sv", "au", "every unit of it, with the payment that produced it", dict(hl=True))])

seq("seq-timeout",
    [("api", "Payments API", "container"), ("db", "Ledger database", "db"), ("ad", "Adapter", "container"), ("pr", "Processor", "ext"), ("iq", "Inquiry job", "container")],
    [("m", "ad", "pr", "authorise, reference p-7731/1"),
     ("n", "api", "api", "1.9 s, no answer: our deadline", "red"),
     ("m", "api", "db", "payment UNKNOWN; answer pending (and pending to any retry with k-91)", dict(hl=True)),
     ("m", "iq", "pr", "status of p-7731/1? (after 5 s, 30 s, 2 min)"),
     ("r", "pr", "iq", "approved at 10:00:02.4"),
     ("m", "iq", "db", "AUTHORISED; entries; outbox: payment.authorised"),
     ("n", "iq", "iq", "'not found' after the window: DECLINED; an unwanted approval: reversed by reference", "green")])

seq("seq-idem",
    [("r1", "Request 1", "person"), ("r2", "Request 2", "person"), ("api", "Payments API", "container"), ("db", "Ledger database", "db")],
    [("m", "r1", "api", "k-91, 1,050"), ("m", "r2", "api", "k-91, 1,050 (2 ms later)"),
     ("m", "api", "db", "INSERT key k-91 (R1): ok, processing, with payment p-7731"),
     ("m", "api", "db", "INSERT key k-91 (R2): unique violation", dict(hl=True)),
     ("r", "db", "api", "row: processing, request hash h1"),
     ("r", "api", "r2", "409 in progress, retry"),
     ("n", "api", "api", "later R2 again: done, same hash: stored response returned", "green"),
     ("n", "api", "api", "k-91 with amount 2,050: hash differs: 422, nothing executed", "red")])

seq("seq-outbox",
    [("sv", "Payment service", "container"), ("db", "Ledger database", "db"), ("dz", "Debezium", "container"), ("kf", "Kafka", "queue"), ("wh", "Webhook sender", "container"), ("mr", "Merchant", "ext")],
    [("m", "sv", "db", "BEGIN; payment CAPTURED; entries; outbox row e-551; COMMIT", dict(hl=True)),
     ("n", "sv", "sv", "process killed here: nothing is lost, the row is committed", "amber"),
     ("m", "dz", "db", "read the log from the slot position: e-551, in commit order"),
     ("m", "dz", "kf", "publish e-551, key merchant m-42", dict(kind="async")),
     ("m", "kf", "wh", "e-551", dict(kind="async")),
     ("m", "wh", "mr", "webhook e-551, signed; retried with backoff", dict(kind="async")),
     ("n", "mr", "mr", "a duplicate e-551: already seen, ignored", "green")])

seq("seq-hot",
    [("pm", "5,000 payments/s", "person"), ("jr", "Journal, merchant m-42", "db"), ("pj", "Projector", "container"), ("pw", "Payout writer", "container")],
    [("m", "pm", "jr", "each payment inserts its own entries: no shared row"),
     ("m", "pj", "jr", "tail the journal; update balances"),
     ("n", "pj", "pj", "balance current to entry 991,200,731, about 2 s behind", "amber"),
     ("m", "pw", "jr", "payout 50,000: read the sum of the 16 sub-accounts, under the merchant's writer lease", dict(hl=True)),
     ("r", "jr", "pw", "available 1,900,000"),
     ("m", "pw", "jr", "post the payout transaction only if 50,000 ≤ available"),
     ("n", "pw", "pw", "a second payout waits its turn: one writer per merchant", "green")])

seq("seq-recon",
    [("pr", "Processor", "ext"), ("st", "Raw file store", "db"), ("rc", "Reconciliation", "container"), ("lg", "Ledger", "db"), ("fo", "Finance ops", "person")],
    [("m", "pr", "st", "settlement file, 2.9 × 10⁸ lines (stored unchanged)", dict(kind="async")),
     ("m", "rc", "lg", "expectations for the day, by reference, net of fees"),
     ("n", "rc", "rc", "match line by line: reference, amount, fee", "amber"),
     ("m", "rc", "lg", "matched: SETTLED, settlement entries"),
     ("m", "rc", "fo", "break: settled by them, declined by us, 1,050 (owner, age 0)", dict(hl=True)),
     ("n", "rc", "rc", "timing break: auto-closes when tomorrow's file matches", "green")])

seq("seq-correct",
    [("on", "On-call", "person"), ("sv", "Payments", "container"), ("lg", "Ledger", "db"), ("po", "Payouts", "container")],
    [("m", "on", "sv", "kill switch: release 2026.11.19 off", dict(hl=True)),
     ("m", "on", "po", "hold payouts for the 1,200 affected merchants"),
     ("m", "on", "lg", "find: same payment, type fee, two transactions: 40,000 rows"),
     ("m", "on", "lg", "post one reversing transaction per duplicate, tag INC-4471"),
     ("n", "lg", "lg", "the audit trail shows the error and the correction", "green"),
     ("m", "on", "po", "180 already paid: a receivable, recovered from future settlements"),
     ("n", "on", "on", "add a unique (payment, type) for single-occurrence types; hourly check", "amber")])

seq("seq-probe",
    [("pb", "Probe", "container"), ("api", "Payments API", "container"), ("pr", "Processor (test card)", "ext"), ("mo", "Monitoring", "container")],
    [("m", "pb", "api", "synthetic payment, test card, every minute per processor"),
     ("m", "api", "pr", "authorise with reference"),
     ("r", "api", "pb", "captured in 410 ms"),
     ("m", "pb", "mo", "success, latency, per processor"),
     ("n", "mo", "mo", "approval rate per processor and country against baseline: −6 points", "red"),
     ("n", "mo", "mo", "ledger: debits minus credits = 0, checked continuously", "green")])

# ───────────────────────────── 5 · data models ───────────────────────────────────────────────────────
c = er.Chen(1800, 960, size=27)
c.entity("pay", 200, 140, "PAYMENT"); c.entity("att", 200, 600, "ATTEMPT", weak=True); c.entity("tx", 800, 140, "JOURNAL TXN")
c.entity("en", 1400, 140, "ENTRY", weak=True); c.entity("ac", 1400, 600, "ACCOUNT"); c.entity("br", 800, 760, "BREAK")
c.rel("ha", 200, 370, "HAS", identifying=True); c.rel("po", 500, 140, "POSTS"); c.rel("co", 1100, 140, "CONTAINS", identifying=True)
c.rel("to", 1400, 370, "ON"); c.rel("ex", 800, 450, "EXPLAINS")
c.attr("pid", 170, 50, "payment_id", of="pay", key=True); c.attr("st", 330, 50, "state", of="pay"); c.attr("mid", 80, 235, "merchant_id", of="pay")
c.attr("ref", 110, 700, "reference", of="att", partial=True); c.attr("res", 320, 700, "result", of="att")
c.attr("tid", 800, 50, "txn_id", of="tx", key=True); c.attr("ty", 960, 235, "type", of="tx")
c.attr("dir", 1320, 50, "direction", of="en"); c.attr("amt", 1530, 50, "amount_minor", of="en"); c.attr("cur", 1620, 200, "currency", of="en")
c.attr("aid", 1400, 700, "account_id", of="ac", key=True); c.attr("amid", 1660, 600, "merchant_id", of="ac"); c.attr("bal", 1620, 480, "balance", of="ac", derived=True)
c.attr("ow", 640, 860, "owner", of="br"); c.attr("ag", 960, 860, "age", of="br", derived=True)
c.link("pay", "ha", "1", src="b", dst="t"); c.link("ha", "att", "N", src="b", dst="t", total=True)
c.link("pay", "po", "1"); c.link("po", "tx", "N")
c.link("tx", "co", "1"); c.link("co", "en", "N", total=True)
c.link("en", "to", "N", src="b", dst="t"); c.link("to", "ac", "1", src="b", dst="t")
c.link("br", "ex", "N", src="t", dst="b"); c.link("ex", "tx", "0..1", src="t", dst="b")
c.legend(1000, 560, size=23, gap=34, rows=["rect", "rect2", "dia", "dia2", "oval", "key", "ovald", "dbl"])
c.note(60, 895, 1000, "A balance is derived: the sum of its entries.")
c.save(OUT / "erd-chen.svg", order=["pay", ("att", "ha"), ("tx", "po"), ("en", "co"), ("ac", "to"), ("br", "ex")])

e = er.ERD(1600, 820, size=23)
e.entity("en", 30, 40, 520, "journal_entry", [("merchant_id", "bigint", "PK"), ("account_id", "bigint", "PK"), ("entry_id", "bigint", "PK"), ("txn_id", "bigint", "FK"),
         ("direction", "debit|credit", ""), ("amount_minor", "bigint", ""), ("currency", "char(3)", "")],
         kind="focus", caption="hash(merchant_id) → 64 partitions; insert only")
e.entity("tx", 650, 40, 450, "journal_txn", [("txn_id", "bigint", "PK"), ("payment_id", "bigint", "FK,IX"), ("type", "text", ""),
         ("created_at", "ts", ""), ("incident", "text", "")], caption="debits = credits per currency, at commit")
e.entity("pay", 1180, 40, 400, "payment", [("payment_id", "bigint", "PK"), ("merchant_id", "bigint", "IX"), ("state", "text", ""), ("captured_minor", "bigint", ""),
         ("refunded_minor", "bigint", "")], caption="the only mutable row")
e.entity("idem", 30, 500, 520, "idempotency", [("client_id", "text", "PK"), ("key", "text", "PK"), ("request_hash", "bytea", ""),
         ("status", "text", ""), ("response", "json", "")], kind="ext", caption="7-day retention")
e.entity("ob", 650, 500, 450, "outbox", [("id", "bigint", "PK"), ("payload", "json", ""), ("created_at", "ts", "")],
         caption="same transaction as the state")
e.entity("bp", 1180, 500, 400, "balance_projection", [("account_id", "bigint", "PK"), ("balance", "bigint", ""), ("as_of_entry", "bigint", "")],
         kind="redis", caption="derived; rebuildable")
e.rel("en", "tx", "N", "1", src="r:0.6", dst="l:0.6", label="")
e.rel("tx", "pay", "N", "1", src="r:0.6", dst="l:0.6", label="")
e.note(30, 770, 1540, "No UPDATE and no DELETE on journal rows. A correction is a new transaction; integer minor units, never floats.")
e.save(OUT / "erd-physical.svg", order=["en", "tx", "pay", "idem", "ob", "bp"])

# ───────────────────────────── 6 · figures ───────────────────────────────────────────────────────────
def svgdoc(w, h, body): return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" width="{w}" height="{h}">'
                               f'<rect width="{w}" height="{h}" fill="#ffffff"/>{body}</svg>')
def T(x, y, s, size=24, fill=INK, w=500, anchor="start"):
    return f'<text x="{x}" y="{y}" text-anchor="{anchor}" font-family="{FONT}" font-size="{size}" font-weight="{w}" fill="{ink(fill)}">{esc(s)}</text>'
def R(x, y, w, h, fill, stroke, rx=10, sw=2.2, dash=False):
    return (f'<rect x="{x:.1f}" y="{y:.1f}" width="{w:.1f}" height="{h:.1f}" rx="{rx}" fill="{fill}" stroke="{stroke}" stroke-width="{sw}"'
            f'{" stroke-dasharray=\"9 6\"" if dash else ""}/>')
def L(x1, y1, x2, y2, col=INK, sw=2.4, dash=False):
    return f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="{col}" stroke-width="{sw}"{" stroke-dasharray=\"8 6\"" if dash else ""}/>'
def G(k, s): return f'<g data-k="{k}">{s}</g>'
def steps(name, units): (OUT / f"{name}.steps.json").write_text(json.dumps(units))

def truth():
    p = [T(40, 50, "The truth arrives over months; the client wants an answer in two seconds", 28, INK, 800), L(120, 210, 1500, 210, GREY, 4)]
    pts = [(170, "2 s", "the response", "approved, declined, or pending", BLUE),
           (540, "minutes", "the inquiry", "UNKNOWN becomes final", BLUE),
           (910, "next day", "the settlement file", "the processor's books", AMBER),
           (1280, "up to months", "the chargeback window", "a dispute can still arrive", RED)]
    for i, (x_, when, what, sub, col) in enumerate(pts):
        p.append(G(f"t{i}", f'<circle cx="{x_}" cy="210" r="16" fill="{col}"/>' + T(x_, 160, when, 30, col, 800, "middle") +
                   T(x_, 270, what, 25, INK, 800, "middle") + T(x_, 306, sub, 21, GREY, 600, "middle")))
    p.append(G("t4", T(800, 400, "Each mechanism lives at one point; none replaces another.", 25, INK, 700, "middle")))
    (OUT / "truth.svg").write_text(svgdoc(1600, 440, "".join(p))); steps("truth", [["t0"], ["t1"], ["t2"], ["t3"], ["t4"]])
truth()

def hot():
    p = [T(40, 50, "One balance row against one merchant's payment rate", 28, INK, 800)]
    x0, Wd = 480, 1060; sc = Wd / 11000; us = []
    rows = [("Arriving payments", 5000, RED, "5,000 / s"), ("One row lock, ~1.5 ms each", 670, AMBER, "≈ 670 / s"),
            ("Append only: no shared row", 5000, GREEN, "5,000 / s and more"), ("16 sub-accounts × 670", 10700, BLUE, "≈ 10,700 / s")]
    for i, (lab, v, col, txt) in enumerate(rows):
        y = 100 + i * 85; fill = {RED: "#fce8e6", AMBER: "#fef7e0", GREEN: "#e6f4ea", BLUE: "#e8f0fe"}[col]
        big = v * sc > 300
        p.append(G(f"h{i}", T(40, y + 36, lab, 24, INK, 700) + R(x0, y, v * sc, 54, fill, col) +
                   T(x0 + v * sc - 12 if big else x0 + v * sc + 14, y + 37, txt, 24, col, 800, "end" if big else "start")))
        us.append([f"h{i}"])
    p.append(G("h4", T(40, 490, "On the shared row the queue grows by 4,330 a second: p99 passes 2 s within a second.", 24, INK, 700) +
               T(40, 530, "Illustrative lock time, to be measured. The fix takes the shared row off the hot path.", 22, GREY, 600)))
    us.append(["h4"])
    (OUT / "hot.svg").write_text(svgdoc(1600, 560, "".join(p))); steps("hot", us)
hot()

def entries():
    p = [T(40, 50, "One capture of 1,050 with a 30 fee, as balanced entries", 28, INK, 800)]
    for lab, x_, w in [("Account", 60, 520), ("Debit", 620, 300), ("Credit", 960, 300)]:
        p += [R(x_, 84, w, 56, "#f1f3f4", GREY, rx=6), T(x_ + 18, 121, lab, 24, INK, 800)]
    us = []
    rows = [("Processor receivable (asset)", "1,050", ""), ("Merchant payable (liability)", "", "1,020"), ("Fee revenue", "", "30")]
    for i, (a, d_, cr) in enumerate(rows):
        y = 154 + i * 66
        p.append(G(f"r{i}", R(60, y, 520, 56, "#fff", "#dadce0", rx=6) + T(78, y + 37, a, 23, INK, 600) +
                   R(620, y, 300, 56, "#e8f0fe" if d_ else "#fff", "#dadce0", rx=6) + T(900, y + 37, d_, 26, BLUE, 800, "end") +
                   R(960, y, 300, 56, "#e8f0fe" if cr else "#fff", "#dadce0", rx=6) + T(1240, y + 37, cr, 26, BLUE, 800, "end")))
        us.append([f"r{i}"])
    y = 154 + 3 * 66
    p.append(G("sum", L(620, y + 4, 1260, y + 4, INK, 3) + T(900, y + 44, "1,050", 28, INK, 800, "end") + T(1240, y + 44, "1,050", 28, INK, 800, "end") +
               T(1300, y + 44, "balanced", 26, "#188038", 800)))
    us.append(["sum"])
    p.append(G("note", T(60, 480, "Integer minor units with a currency on every amount. A refund is a new transaction that mirrors these lines.", 23, GREY, 700)))
    us.append(["note"])
    (OUT / "entries.svg").write_text(svgdoc(1600, 520, "".join(p))); steps("entries", us)
entries()

def states():
    """The payment state machine, built up one state or one exit at a time (12 steps)."""
    w_, h_ = 220, 76
    pos = dict(cr=(130, 300), pe=(470, 300), au=(810, 110), un=(810, 300), de=(810, 500), ca=(1150, 110), se=(1490, 110),
               pr=(1150, 300), rf=(1150, 500), cb=(1490, 300))
    names = dict(cr="CREATED", pe="AUTH_PENDING", au="AUTHORISED", un="UNKNOWN", de="DECLINED", ca="CAPTURED", se="SETTLED",
                 pr="PARTLY_REFUNDED", rf="REFUNDED", cb="CHARGEBACK")
    fills = dict(un=("#fce8e6", RED), de=("#f1f3f4", GREY))
    p = ['<defs>' + "".join(f'<marker id="a{n}" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="8" markerHeight="8" orient="auto">'
                            f'<path d="M0,1 L10,5 L0,9 z" fill="{c}"/></marker>' for n, c in (("k", INK), ("r", RED), ("g", GREEN))) + '</defs>']
    def node(k):
        x_, y_ = pos[k]; fill, st = fills.get(k, ("#e8f0fe", BLUE))
        sz = 21 if len(names[k]) > 14 else 26
        return G(f"n:{k}", R(x_ - w_ / 2, y_ - h_ / 2, w_, h_, fill, st, rx=12, sw=2.6) + T(x_, y_ + 9, names[k], sz, INK, 800, "middle"))
    def edge(key, a, b, label, lx, ly, col=INK, m="k", dash=False, ax=None, bx=None):
        (x1, y1), (x2, y2) = pos[a], pos[b]
        dx, dy = x2 - x1, y2 - y1
        def ends(x_, y_, ddx, ddy):
            if abs(ddy) < 1: return x_ + (w_ / 2 if ddx > 0 else -w_ / 2), y_
            if abs(ddx) < 1: return x_, y_ + (h_ / 2 if ddy > 0 else -h_ / 2)
            return x_ + (w_ / 2 - 20 if ddx > 0 else -(w_ / 2 - 20)), y_ + (h_ / 2 if ddy > 0 else -h_ / 2)
        sx, sy = ends(x1, y1, dx, dy); tx_, ty_ = ends(x2, y2, -dx, -dy)
        return G(f"e:{key}", f'<line x1="{sx}" y1="{sy}" x2="{tx_}" y2="{ty_}" stroke="{col}" stroke-width="3"'
                 f'{" stroke-dasharray=\"10 6\"" if dash else ""} marker-end="url(#a{m})"/>' + T(lx, ly, label, 22, col if col != INK else INK, 700, "middle"))
    parts = {}
    parts["cr"] = node("cr")
    parts["pe"] = node("pe") + edge("cr-pe", "cr", "pe", "send", 300, 280)
    parts["au"] = node("au") + edge("pe-au", "pe", "au", "approved", 600, 190)
    parts["de"] = node("de") + edge("pe-de", "pe", "de", "declined", 600, 425)
    parts["un"] = node("un") + edge("pe-un", "pe", "un", "timeout", 640, 280, RED, "r")
    parts["un-au"] = edge("un-au", "un", "au", "inquiry: approved", 960, 215, GREEN, "g", True)
    parts["un-de"] = edge("un-de", "un", "de", "not found", 960, 410, GREEN, "g", True)
    parts["ca"] = node("ca") + edge("au-ca", "au", "ca", "capture", 980, 90)
    parts["se"] = node("se") + edge("ca-se", "ca", "se", "matched", 1320, 90)
    parts["pr"] = node("pr") + edge("ca-pr", "ca", "pr", "refund", 1215, 215)
    parts["rf"] = node("rf") + edge("pr-rf", "pr", "rf", "refund the rest", 1245, 410)
    parts["cb"] = node("cb") + edge("se-cb", "se", "cb", "dispute", 1560, 215)
    order = ["cr", "pe", "au", "de", "un", "un-au", "un-de", "ca", "se", "pr", "rf", "cb"]
    keys = {"cr": ["n:cr"], "pe": ["n:pe", "e:cr-pe"], "au": ["n:au", "e:pe-au"], "de": ["n:de", "e:pe-de"], "un": ["n:un", "e:pe-un"],
            "un-au": ["e:un-au"], "un-de": ["e:un-de"], "ca": ["n:ca", "e:au-ca"], "se": ["n:se", "e:ca-se"], "pr": ["n:pr", "e:ca-pr"],
            "rf": ["n:rf", "e:pr-rf"], "cb": ["n:cb", "e:se-cb"]}
    body = "".join(parts[k] for k in order)
    (OUT / "states.svg").write_text(svgdoc(1700, 600, p[0] + body)); steps("states", [keys[k] for k in order])
states()

bs.budget_bar(OUT / "budget.svg", [("our code", 0.1, "edge"), ("processor, p99", 1.5, "ext")],
              total=2.0, unit="s", title="Two seconds, and the processor has most of them (initial target p99 2 s)")

print(sorted(p.name for p in OUT.glob("*.svg")))
