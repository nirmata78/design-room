#!/usr/bin/env python3
"""SD-95 instalment loan servicing: every picture for the reference video and the written design -> ./svg/*.svg.
One carried baseline (declared once), numbered flows, challenge overlays, C4, sequences, ERDs, figures.
Run: python3 diagrams.py"""
import html, pathlib, sys
sys.path.insert(0, str(pathlib.Path.home() / ".claude/skills/slide-video-kit/scripts"))
import basesvg as bs
import c4svg as c4
import seqsvg as sq
import erdsvg as er

OUT = pathlib.Path(__file__).resolve().parent / "svg"; OUT.mkdir(exist_ok=True)
FONT = "Inter, Helvetica, Arial, sans-serif"
INK, RED, GREEN, BLUE, PURPLE, GREY, AMBER = "#24292f", "#c8341f", "#1f8a4c", "#2f6fb5", "#6b4fc4", "#8c959f", "#d18f1c"
def esc(s): return html.escape(str(s))

# ───────────────────────────── 1 · the carried baseline ──────────────────────────────────────────────
X = [20, 360, 700, 1040, 1380]; W = 200
b = bs.Baseline(1600, 740)
b.node("cus", X[0], 210, W, 130, "client", "Customer, merchant", "pay · payoff")
b.node("org", X[0], 60, W, 110, "ext", "Origination", "loan booked")
b.node("api", X[1], 210, W, 130, "edge", "Servicing API", "keys · quotes")
b.node("svc", X[2], 210, W, 130, "service", "Schedule + collect", "state machine")
b.node("dsp", X[3], 210, W, 130, "service", "Dispatcher", "budget per rail", since=2)
b.node("rail", X[4], 210, W, 130, "ext", "Rails", "card · bank")
b.node("db1", X[2], 420, W, 110, "data", "Loans DB", "balance column", shape="db", until=1)
b.node("db", X[2], 420, W, 110, "data", "Servicing DB", "ledger · intents", shape="db", since=2)
b.node("pol", X[1], 420, W, 110, "service", "Policy", "terms · rules", since=3)
b.node("ing", X[4], 420, W, 110, "service", "File ingest", "returns · files", since=3)
b.node("res", X[3], 420, W, 110, "service", "Resolver", "UNKNOWN → final", since=3)
b.node("ntc", X[0], 420, W, 110, "service", "Notices", "receipts", since=3)
b.node("rec", X[4], 590, W, 100, "service", "Reconciliation", "three-way", since=3)
b.node("ops", X[3], 590, W, 100, "client", "Finance ops", "owned breaks", since=3)
# tags: shown only inside a challenge, a flow or the recap
b.node("plan", X[2], 60, W, 110, "service", "Day plan", "back from cut-off", tag="ch2")
b.node("met", X[3], 60, W, 110, "ext", "Probes", "SLIs on money", tag="ch8")
b.node("sw", X[4], 60, W, 110, "client", "Rail switch", "pause · lower limit", tag="ch7")
b.node("quo", X[1], 60, W, 110, "service", "Payoff quote", "lists in-flight", tag="ch5")

REQ = dict(src="r:0.3", dst="l:0.3")
RSP = dict(src="l:0.72", dst="r:0.72", kind="resp")
b.edge("cus-api", "cus", "api", "pay · refund", **REQ)
b.edge("api-cus", "api", "cus", "receipt", **RSP)
b.edge("org-api", "org", "api", "loan booked", src="r:0.5", dst="t:0.25", kind="async", at=(300, 150))
b.edge("api-svc", "api", "svc", "commands", **REQ)
b.edge("svc-api", "svc", "api", "state", **RSP)
b.edge("svc-rail", "svc", "rail", "charge everyone at 00:00", src="r:0.3", dst="l:0.3", until=1, at=(1140, 236))
b.edge("svc-db1", "svc", "db1", "update balance", src="b:0.5", dst="t:0.5", until=1)
b.edge("svc-db", "svc", "db", "", src="b:0.5", dst="t:0.5", since=2)
b.edge("db-dsp", "db", "dsp", "drain outbox", src="t:0.85", dst="b:0.2", via=[(870, 372), (1080, 372)], since=2, at=(975, 362))
b.edge("dsp-db", "dsp", "db", "post result", src="b:0.5", dst="t:0.97", via=[(1140, 400), (894, 400)], since=2, kind="resp", at=(960, 414))
b.edge("dsp-rail", "dsp", "rail", "charge · file", since=2, **REQ)
b.edge("rail-dsp", "rail", "dsp", "result", since=2, **RSP)
b.edge("svc-pol", "svc", "pol", "terms", src="b:0.12", dst="t:0.85", since=3, at=(610, 392))
b.edge("rail-ing", "rail", "ing", "files", src="b:0.5", dst="t:0.5", kind="async", since=3, at=(1520, 392))
b.edge("ing-db", "ing", "db", "reversals", src="b:0.2", dst="b:0.8", via=[(1420, 558), (860, 558)], since=3, at=(1150, 548))
b.edge("res-rail", "res", "rail", "query", src="t:0.85", dst="b:0.15", since=3, at=(1330, 392))
b.edge("res-dsp", "res", "dsp", "resolved", src="t:0.6", dst="b:0.6", since=3, at=(1175, 392))
b.edge("ing-rec", "ing", "rec", "", src="b:0.5", dst="t:0.5", kind="async", since=3)
b.edge("rec-db", "rec", "db", "expectations", src="b:0.5", dst="b:0.5", via=[(1480, 716), (800, 716)], since=3, at=(900, 704))
b.edge("rec-ops", "rec", "ops", "breaks", src="l:0.5", dst="r:0.5", since=3)
b.edge("db-ntc", "db", "ntc", "", src="b:0.15", dst="b:0.5", via=[(730, 566), (120, 566)], kind="async", since=3, at=(600, 552))
b.edge("ntc-cus", "ntc", "cus", "notices", src="t:0.5", dst="b:0.5", kind="async", since=3)
b.edge("plan-dsp", "plan", "dsp", "rail budgets", src="r:0.5", dst="t:0.15", tag="ch2", at=(990, 150))
b.edge("met-dsp", "met", "dsp", "", src="b:0.5", dst="t:0.5", tag="ch8")
b.edge("sw-dsp", "sw", "dsp", "pause", src="l:0.5", dst="t:0.88", tag="ch7", at=(1300, 150))
b.edge("api-quo", "api", "quo", "", src="t:0.5", dst="b:0.5", tag="ch5")

def sv(name, h, **view):
    b.h = h
    b.save(OUT / name, **view)
ALL = ["ch2", "ch5", "ch7", "ch8"]
sv("base-v1.svg", 560, upto=1, legend=True)
sv("base-v2.svg", 560, upto=2, new=2, legend=True)
sv("base-v3.svg", 740, upto=3, new=3, legend=True)
sv("base-final.svg", 740, upto=3, show=ALL, legend=True)
# 5.2 the alternate path: one box changes (one scheduled job, no per-rail budget)
sv("alt.svg", 560, upto=3, keep=["svc", "db", "dsp", "rail"], alt=["dsp"])
sv("map.svg", 740, upto=3, show=[], legend=True, attack=["dsp", "svc", "ing", "api", "rec", "rail"], keep=None)
sv("flow-fr1.svg", 740, upto=3, flow=["org-api", "api-svc", "svc-pol", "svc-db"])
sv("flow-fr2.svg", 740, upto=3, flow=["svc-db", "db-dsp", "dsp-rail", "rail-dsp", "dsp-db"])
sv("flow-fr3.svg", 740, upto=3, flow=["cus-api", "api-svc", "svc-pol", "svc-db", "svc-api", "api-cus"])
sv("flow-fr4.svg", 740, upto=3, flow=["rail-ing", "ing-db", "db-ntc", "ntc-cus"])
sv("flow-fr5.svg", 740, upto=3, flow=["rail-ing", "ing-rec", "rec-db", "rec-ops"])
sv("ch1-attack.svg", 560, upto=3, attack=["dsp"], keep=["svc", "db", "dsp", "rail"], hot=["dsp-rail", "rail-dsp"])
sv("ch1-fix.svg", 560, upto=3, fix=["res"], keep=["db", "dsp", "rail", "res"], ok=["res-rail", "res-dsp", "dsp-db"])
sv("ch2-attack.svg", 560, upto=3, attack=["svc", "dsp"], keep=["svc", "db", "dsp", "rail"], hot=["dsp-rail"])
sv("ch2-fix.svg", 560, upto=3, show=["ch2"], fix=["plan", "dsp"], keep=["svc", "db", "dsp", "rail", "plan"], ok=["plan-dsp", "db-dsp", "dsp-rail"])
sv("ch3-attack.svg", 740, upto=3, attack=["ing"], keep=["rail", "ing", "db", "dsp"], hot=["rail-ing"])
sv("ch3-fix.svg", 740, upto=3, fix=["ing", "pol"], keep=["rail", "ing", "db", "pol", "svc", "ntc", "cus"], ok=["ing-db", "svc-pol", "db-ntc", "ntc-cus"])
sv("ch4-attack.svg", 560, upto=3, attack=["svc"], keep=["cus", "api", "svc", "db"], hot=["api-svc"])
sv("ch4-fix.svg", 560, upto=3, fix=["pol", "svc"], keep=["cus", "api", "svc", "db", "pol"], ok=["svc-pol", "svc-db"])
sv("ch5-attack.svg", 560, upto=3, attack=["api"], keep=["cus", "api", "svc", "db", "dsp"], hot=["cus-api"])
sv("ch5-fix.svg", 560, upto=3, show=["ch5"], fix=["quo"], keep=["cus", "api", "svc", "db", "quo"], ok=["api-quo", "svc-db"])
sv("ch6-attack.svg", 740, upto=3, attack=["rec"], keep=["rail", "ing", "rec", "db", "ops"], hot=["ing-rec"])
sv("ch6-fix.svg", 740, upto=3, fix=["rec", "ops"], keep=["rail", "ing", "rec", "db", "ops"], ok=["ing-rec", "rec-db", "rec-ops"])
sv("ch7-attack.svg", 560, upto=3, attack=["rail"], keep=["svc", "dsp", "rail", "db"], hot=["dsp-rail", "rail-dsp"])
sv("ch7-fix.svg", 560, upto=3, show=["ch7"], fix=["sw", "res"], keep=["dsp", "rail", "sw", "res", "db"], ok=["sw-dsp", "res-rail", "res-dsp"])
sv("ch8-attack.svg", 740, upto=3, attack=["dsp", "ing"], keep=["svc", "dsp", "rail", "ing", "db"])
sv("ch8-fix.svg", 740, upto=3, show=["ch8"], fix=["met", "rec"], keep=["svc", "dsp", "rail", "ing", "db", "met", "rec", "ops"], ok=["met-dsp", "rec-ops"])

# ───────────────────────────── 2 · C4 ────────────────────────────────────────────────────────────────
d = c4.Diagram(1830, 780)
d.node("cus", 40, 60, 340, 160, "person", "Customer", "Person", "Repays; pays off early.", size=26)
d.node("mer", 40, 530, 340, 160, "ext", "Merchant", "External", "Sends refunds.", size=26)
d.node("org", 700, 20, 400, 150, "ext", "Origination (SD-82)", "External", "Books loans.", size=26)
d.node("ls", 700, 300, 400, 200, "system", "Loan servicing", "Software System", "Schedules, collects, ledger.", size=28)
d.node("proc", 1460, 40, 350, 160, "ext", "Card processor", "External", "Charges tokens; reports.", size=26)
d.node("bank", 1460, 300, 350, 160, "ext", "Bank", "External", "Debit files, returns.", size=26)
d.node("fin", 1460, 570, 350, 160, "person", "Finance ops", "Person", "Owns breaks and the close.", size=26)
d.edge("cus", "ls", "Pays, payoff", "app, web", src="r:0.7", dst="l:0.25", at=(540, 270), size=22)
d.edge("mer", "ls", "Refunds", "API", src="r:0.3", dst="l:0.8", at=(540, 530), size=22)
d.edge("org", "ls", "Loan booked", "event", src="b", dst="t", at=(990, 245), size=22)
d.edge("ls", "proc", "Charge, query", "API, key", src="r:0.2", dst="l:0.7", at=(1280, 250), size=22)
d.edge("ls", "bank", "Debit file", "file, cut-off", src="r:0.55", dst="l:0.5", at=(1280, 360), size=22)
d.edge("bank", "ls", "Returns, statement", "files, daily", src="b:0.3", dst="b:0.8", via=[(1565, 560), (1020, 560)], at=(1300, 590), size=22)
d.edge("fin", "ls", "Breaks, close", "console", src="l:0.5", dst="b:0.3", via=[(820, 650)], at=(1080, 680), size=22)
d.save(OUT / "c4-context.svg")

CX, CW, CY, CH, CS = [50, 420, 790, 1160], 280, [50, 320, 590], 170, 25
def containers(name):
    d = c4.Diagram(1830, 800)
    d.boundary(20, 20, 1450, 770, "Loan servicing", "Software System", top="left")
    d.node("res", CX[3], CY[0], CW, CH, "container", "Resolver", "Worker", "UNKNOWN to final.", size=CS)
    d.node("api", CX[0], CY[1], CW, CH, "container", "Servicing API", "Service", "Keys, refunds, quotes.", size=CS)
    d.node("svc", CX[1], CY[1], CW, CH, "container", "Schedule + collect", "Service", "Due items, states.", size=CS)
    d.node("db", CX[2], CY[1], CW, CH, "db", "Servicing DB", "Relational, by month", "Ledger, intents, outbox.", size=CS)
    d.node("dsp", CX[3], CY[1], CW, CH, "container", "Dispatcher", "Worker", "Token bucket per rail.", size=CS)
    d.node("pol", CX[1], CY[2], CW, CH, "container", "Policy", "Service + rules", "Terms, waterfall, fees.", size=CS)
    d.node("ing", CX[2], CY[2], CW, CH, "container", "File ingest", "Batch", "Returns, settlement.", size=CS)
    d.node("rec", CX[3], CY[2], CW, CH, "container", "Reconciliation", "Batch pipeline", "Three-way, breaks.", size=CS)
    d.node("cu", 1540, CY[0], 280, CH, "ext", "Customer, merchant", "External", "App, refund API.", size=CS)
    d.node("rl", 1540, CY[1], 280, CH, "ext", "Rails", "External", "Card processor, bank.", size=CS)
    d.edge("cu", "api", "HTTPS", "", src="b:0.3", dst="t:0.5", via=[(1624, 270), (190, 270)], at=(800, 262), size=22)
    d.edge("api", "svc", "", "", src="r", dst="l")
    d.edge("svc", "db", "one commit", "", src="r", dst="l", at=(745, 305), size=22)
    d.edge("db", "dsp", "outbox", "", src="r", dst="l", at=(1115, 305), size=22)
    d.edge("dsp", "rl", "charge, file", "", src="r", dst="l", at=(1495, 300), size=22)
    d.edge("res", "dsp", "resolved", "", src="b", dst="t", at=(1365, 300), size=22)
    d.edge("svc", "pol", "terms", "gRPC", src="b", dst="t", at=(625, 545), size=22)
    d.edge("ing", "db", "reversals", "SQL", src="t", dst="b", at=(855, 545), size=22)
    d.edge("ing", "rec", "", "", src="r", dst="l")
    d.edge("rec", "db", "expectations", "", src="t:0.2", dst="b:0.85", via=[(1216, 545), (1028, 545)], at=(1125, 530), size=22)
    d.save(OUT / name)

containers("c4-containers.svg")
# the same container view with the technologies (labels from ../stack.json)
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent / 'src')); import stack
c4.Diagram.OVERRIDE = {k: (v[1], v[2]) for k, v in stack.C4.items()}
containers("c4-containers-tech.svg")
c4.Diagram.OVERRIDE = {}


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

seq("seq-collect",
    [("sv", "Schedule + collect", "container"), ("db", "Servicing DB", "db"), ("ds", "Dispatcher", "container"), ("pr", "Card processor", "ext")],
    [("m", "sv", "db", "claim ln-5531 #2; intent int-88 attempt 1; outbox row; commit", dict(hl=True)),
     ("m", "ds", "db", "drain outbox, under 90 / s"),
     ("m", "ds", "pr", "charge $150, key coll:ln-5531:2:1"),
     ("r", "pr", "ds", "approved, 1.4 s"),
     ("m", "ds", "db", "one transaction: SETTLED, ledger lines, balance v42, outbox"),
     ("n", "db", "db", "a retry with the same key fails at the ledger key: first result returned", "green")])

seq("seq-unknown",
    [("ds", "Dispatcher", "container"), ("db", "Servicing DB", "db"), ("pr", "Card processor", "ext"), ("rs", "Resolver", "container")],
    [("m", "ds", "pr", "charge $150, key coll:ln-5531:2:1"),
     ("n", "ds", "ds", "08:00:10 no answer: worker timeout", "red"),
     ("m", "ds", "db", "intent int-88: UNKNOWN (not FAILED)", dict(hl=True)),
     ("m", "rs", "pr", "query key coll:ln-5531:2:1 (after 30 s, 2 min, 10 min)"),
     ("r", "pr", "rs", "approved at 08:00:03.2"),
     ("m", "rs", "db", "SETTLED; lines posted once, by the same key"),
     ("n", "rs", "rs", "not found after the safe window: resend with the SAME key", "amber")])

seq("seq-claim",
    [("w1", "Worker 1", "container"), ("w2", "Worker 2", "container"), ("db", "Servicing DB", "db"), ("ds", "Dispatcher", "container")],
    [("m", "w1", "db", "claim 500 due rows, shard 7, FOR UPDATE SKIP LOCKED"),
     ("m", "w2", "db", "claim 500 due rows, shard 7: skips the locked ones"),
     ("m", "w1", "db", "per row: intent + outbox row; mark CLAIMED; commit", dict(hl=True)),
     ("n", "w2", "w2", "worker 2 dies before commit: locks released, rows due again", "amber"),
     ("m", "ds", "db", "drain outbox: card at 90 / s; debit rows into the 09:00 file"),
     ("n", "ds", "ds", "sweeper: CLAIMED with no intent for 15 min goes back to DUE", "green")])

seq("seq-return",
    [("bk", "Bank", "ext"), ("ig", "File ingest", "container"), ("db", "Servicing DB", "db"), ("po", "Policy", "container"), ("nt", "Notices", "container")],
    [("m", "bk", "ig", "return file: ln-7702 #3, $150, code R01, Dec 3", dict(kind="async")),
     ("m", "ig", "db", "match by trace number to the attempt; SETTLED to RETURNED", dict(hl=True)),
     ("m", "ig", "db", "reversing transaction dated Dec 3; instalment PAID to DUE, reason R01"),
     ("m", "db", "po", "which rule? R01: re-present, attempt 2 of max 3, after payday"),
     ("m", "db", "nt", "outbox: payment returned, next try Dec 8", dict(kind="async")),
     ("n", "po", "po", "R10 on day 40: never re-present; ask for a new authorisation", "red")])

seq("seq-refund",
    [("mr", "Merchant", "ext"), ("api", "Servicing API", "container"), ("po", "Policy", "container"), ("db", "Servicing DB", "db")],
    [("m", "mr", "api", "refund $300 on ln-9100, merchantRefundId mr-77"),
     ("m", "api", "po", "terms v3: refund shortens or re-amortises? re-amortise"),
     ("m", "api", "db", "txn: merchant receivable 300 / loan principal 300 (key mr-77)", dict(hl=True)),
     ("m", "api", "db", "schedule v2: 6 × $100, replaces v1 from instalment 3"),
     ("n", "db", "db", "instalment 3 already in flight: it stays; allocation applies on settle", "amber"),
     ("r", "api", "mr", "201, refund applied")])

seq("seq-payoff",
    [("cu", "Customer", "person"), ("api", "Servicing API", "container"), ("db", "Servicing DB", "db"), ("ig", "File ingest", "container")],
    [("m", "cu", "api", "payoff quote for ln-5531, Dec 3"),
     ("r", "api", "cu", "q-31: $750 now; $150 debit in flight; valid to Dec 5"),
     ("m", "cu", "api", "pay $750 against q-31 (key = quote ID)"),
     ("m", "api", "db", "lines posted; loan PAID_PENDING, not CLOSED", dict(hl=True)),
     ("m", "ig", "db", "Dec 4: the $150 returns R01: one due item of $150, no late mark"),
     ("n", "db", "db", "no return by Dec 5: CLOSED, lien release, notice", "green")])

seq("seq-recon",
    [("pr", "Processor report", "ext"), ("bk", "Bank statement", "ext"), ("rc", "Reconciliation", "container"), ("lg", "Ledger", "db"), ("fo", "Finance ops", "person")],
    [("m", "rc", "lg", "expectations for Nov 30 by reference"),
     ("m", "pr", "rc", "report: settled, refunds, chargebacks", dict(kind="async")),
     ("m", "bk", "rc", "statement: deposits, returns", dict(kind="async")),
     ("n", "rc", "rc", "match by reference, then amount and a 3-day window", "amber"),
     ("m", "rc", "fo", "4 breaks: 1 timing (2 returns), 3 real, owners set", dict(hl=True)),
     ("n", "rc", "rc", "timing break closes itself when the Dec 1 return file posts", "green")])

seq("seq-probe",
    [("pb", "Probe", "container"), ("ds", "Dispatcher", "container"), ("bk", "Bank", "ext"), ("mo", "Monitoring", "container")],
    [("m", "ds", "bk", "Dec 1 debit file, 480,000 entries, 10:30"),
     ("r", "bk", "ds", "acknowledgement: 468,000 accepted, 12,000 rejected", dict(hl=True)),
     ("m", "pb", "mo", "funnel: due, claimed, sent, acknowledged, settled, per rail"),
     ("n", "mo", "mo", "acknowledged / sent = 97.5 % against 99.9 % baseline: page", "red"),
     ("n", "mo", "mo", "nightly: every transaction sums to zero; projection = sum of lines", "green")])

# ───────────────────────────── 4 · data models ───────────────────────────────────────────────────────
c = er.Chen(1930, 720, size=27)
c.entity("ln", 200, 130, "LOAN"); c.entity("sch", 200, 460, "SCHEDULE VER", weak=True); c.entity("ins", 760, 460, "INSTALMENT", weak=True)
c.entity("it", 1300, 460, "INTENT"); c.entity("tx", 760, 130, "LEDGER TXN"); c.entity("li", 1300, 130, "LINE", weak=True)
c.rel("hs", 200, 295, "HAS", identifying=True); c.rel("ct", 480, 460, "CONTAINS", identifying=True); c.rel("cl", 1030, 460, "COLLECTED BY")
c.rel("po", 480, 130, "POSTS"); c.rel("co", 1030, 130, "CONTAINS", identifying=True); c.rel("ps", 1300, 295, "POSTS")
c.attr("lid", 80, 40, "loan_id", of="ln", key=True); c.attr("tv", 340, 40, "terms_version", of="ln"); c.attr("lst", 90, 205, "state", of="ln")
c.attr("ver", 120, 555, "version", of="sch", partial=True)
c.attr("dd", 640, 560, "due_date", of="ins"); c.attr("am", 900, 560, "amount_cents", of="ins")
c.attr("key", 1240, 555, "idem_key", of="it", key=True); c.attr("ist", 1460, 555, "state", of="it")
c.attr("tid", 760, 40, "txn_id", of="tx", key=True); c.attr("kd", 600, 215, "kind", of="tx")
c.attr("acc", 1220, 40, "account", of="li"); c.attr("amt", 1450, 40, "amount_cents", of="li")
c.link("ln", "hs", "1", src="b", dst="t"); c.link("hs", "sch", "N", src="b", dst="t", total=True)
c.link("sch", "ct", "1"); c.link("ct", "ins", "N", total=True)
c.link("ins", "cl", "1"); c.link("cl", "it", "N")
c.link("ln", "po", "1"); c.link("po", "tx", "N")
c.link("tx", "co", "1"); c.link("co", "li", "N", total=True)
c.link("it", "ps", "1", src="t", dst="b"); c.link("ps", "tx", "0..N", src="t", dst="b")
c.legend(1620, 60, size=22, rows=["rect", "rect2", "dia", "dia2", "oval", "key", "dbl"])
c.note(60, 640, 900, "A balance is a sum of lines. One open intent per instalment.")
c.save(OUT / "erd-chen.svg")

e = er.ERD(1800, 880, size=24)
e.entity("li", 30, 40, 520, "ledger_line", [("txn_id", "bigint", "PK,FK"), ("line_no", "smallint", "PK"), ("account", "text", "IX"),
         ("amount_cents", "bigint", ""), ("effective_date", "date", "")], kind="focus", caption="partitioned by month; insert only")
e.entity("tx", 680, 40, 470, "ledger_txn", [("txn_id", "bigint", "PK"), ("idem_key", "text", "UQ"), ("kind", "text", ""),
         ("loan_id", "bigint", "IX"), ("policy_ver", "text", "")], caption="lines sum to zero, checked at commit")
e.entity("bal", 1300, 40, 470, "account_balance", [("account", "text", "PK"), ("balance_cents", "bigint", ""), ("version", "bigint", "")],
         kind="redis", caption="same commit; provable from lines")
e.entity("due", 30, 440, 520, "due_item", [("id", "bigint", "PK"), ("loan_id", "id", ""), ("due_date", "date", "IX"),
         ("shard", "smallint", "IX"), ("status", "text", "IX"), ("rail", "text", "")], caption="index (due_date, shard, status)")
e.entity("int", 680, 440, 470, "payment_intent", [("id", "bigint", "PK"), ("instalment_id", "bigint", "UQ*"), ("attempt_no", "int", ""),
         ("state", "text", ""), ("idem_key", "text", "UQ")], kind="ext", caption="* unique while state is open")
e.entity("ob", 1300, 440, 470, "outbox", [("id", "bigint", "PK"), ("payload", "json", ""), ("created_at", "ts", "")],
         caption="same transaction as the state")
e.rel("li", "tx", "N", "1", src="r:0.5", dst="l:0.5", label="txn_id", at=(615, 95))
e.rel("tx", "bal", "N", "N", src="r:0.5", dst="l:0.5", label="account", at=(1225, 95))
e.rel("due", "int", "1", "N", src="r:0.5", dst="l:0.5", label="instalment", at=(615, 418))
e.note(30, 825, 1740, "No UPDATE or DELETE on ledger rows. Integer cents. A correction is a reversing transaction, dated when it happens.")
e.save(OUT / "erd-physical.svg")

# ───────────────────────────── 5 · figures ───────────────────────────────────────────────────────────
def svgdoc(w, h, body): return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" width="{w}" height="{h}">'
                               f'<rect width="{w}" height="{h}" fill="#ffffff"/>{body}</svg>')
def T(x, y, s, size=24, fill=INK, w=500, anchor="start"):
    return f'<text x="{x}" y="{y}" text-anchor="{anchor}" font-family="{FONT}" font-size="{size}" font-weight="{w}" fill="{fill}">{esc(s)}</text>'
def R(x, y, w, h, fill, stroke, dash=False, rx=8, sw=2.2):
    return (f'<rect x="{x:.1f}" y="{y:.1f}" width="{w:.1f}" height="{h:.1f}" rx="{rx}" fill="{fill}" stroke="{stroke}" '
            f'stroke-width="{sw}"{" stroke-dasharray=\"10 6\"" if dash else ""}/>')
def L(x1, y1, x2, y2, col=INK, sw=2.4, dash=False):
    return f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" stroke="{col}" stroke-width="{sw}"{" stroke-dasharray=\"8 6\"" if dash else ""}/>'
def ARW(x1, y1, x2, y2, col=INK, dash=False):
    import math
    a = math.atan2(y2 - y1, x2 - x1); hx, hy = x2 - 16 * math.cos(a), y2 - 16 * math.sin(a)
    p1 = (hx + 8 * math.sin(a), hy - 8 * math.cos(a)); p2 = (hx - 8 * math.sin(a), hy + 8 * math.cos(a))
    return L(x1, y1, hx, hy, col, 2.6, dash) + f'<polygon points="{x2},{y2} {p1[0]:.1f},{p1[1]:.1f} {p2[0]:.1f},{p2[1]:.1f}" fill="{col}"/>'

def truth():
    p = [T(40, 44, "When is a collection final? Later than the dashboard thinks", 28, INK, 800)]
    pts = [(130, "seconds", "card answer", "or nothing at all", BLUE),
           (390, "1–2 days", "debit settles", "SETTLED, not final", GREEN),
           (650, "2 bank days", "NSF return", "insufficient funds", AMBER),
           (910, "60 days", "unauthorised return", "customer disputes it", RED),
           (1170, "months", "refunds, disputes", "merchant or card", PURPLE),
           (1430, "7 years", "audit", "every cent explained", GREY)]
    p.append(L(80, 200, 1520, 200, GREY, 4))
    for x, when, what, sub, col in pts:
        p += [f'<circle cx="{x}" cy="200" r="15" fill="{col}"/>', T(x, 150, when, 27, col, 800, "middle"),
              T(x, 258, what, 23, INK, 800, "middle"), T(x, 292, sub, 20, "#57606a", 600, "middle")]
    p += [T(800, 370, "Each point has its own mechanism: UNKNOWN and the resolver, PENDING to SETTLED, RETURNED with a reversal,", 23, INK, 700, "middle"),
          T(800, 406, "schedule versions for refunds, and three-way reconciliation every day. None replaces another.", 23, INK, 700, "middle")]
    (OUT / "truth.svg").write_text(svgdoc(1600, 450, "".join(p)))
truth()

def states():
    p = [T(40, 44, "A collection is a state machine. SETTLED is not the end for a bank debit", 28, INK, 800)]
    S_ = {"SCH": (40, 140, "SCHEDULED", "#dbeafe", BLUE), "SUB": (360, 140, "SUBMITTED", "#dbeafe", BLUE),
          "PEN": (680, 140, "PENDING", "#fdf3e1", AMBER), "SET": (1000, 140, "SETTLED", "#e7f4ec", GREEN),
          "RET": (1320, 140, "RETURNED", "#fdecea", RED), "UNK": (360, 380, "UNKNOWN", "#fdecea", RED),
          "DEC": (680, 380, "DECLINED", "#eef1f4", GREY), "RTY": (1320, 380, "RETRY DUE", "#fdf3e1", AMBER)}
    w, h = 240, 90
    for k, (x, y, t, f, c) in S_.items():
        p += [R(x, y, w, h, f, c, rx=12, sw=2.6), T(x + w / 2, y + 50, t, 25, INK, 800, "middle")]
    def mid(k, side):
        x, y = S_[k][0], S_[k][1]
        return {"r": (x + w, y + h / 2), "l": (x, y + h / 2), "b": (x + w / 2, y + h), "t": (x + w / 2, y)}[side]
    def ar(a, sa, bb, sb, lab, col=INK, dash=False, lx=0, ly=-10, anchor="middle"):
        (x1, y1), (x2, y2) = mid(a, sa), mid(bb, sb)
        return ARW(x1, y1, x2, y2, col, dash) + T((x1 + x2) / 2 + lx, (y1 + y2) / 2 + ly, lab, 20, col, 700, anchor)
    p += [ar("SCH", "r", "SUB", "l", "claimed", ly=-14), ar("SUB", "r", "PEN", "l", "sent", ly=-14), ar("PEN", "r", "SET", "l", "1–2 days", GREEN, ly=-14),
          ar("SET", "r", "RET", "l", "≤ 60 days", RED, True, ly=-14),
          ar("SUB", "b", "UNK", "t", "timeout", RED, False, 14, 0, "start"),
          ar("PEN", "b", "DEC", "t", "declined", GREY, False, 14, 0, "start"),
          ar("RET", "b", "RTY", "t", "NSF, ≤ 2 more", AMBER, False, 14, 0, "start")]
    x1, y1 = mid("UNK", "r"); x2, y2 = mid("PEN", "b")
    p += [ARW(x1, y1, x2 - 70, y2, BLUE, True), T(x1 - 240, y1 + 90, "from UNKNOWN: query by the same key, never resend", 21, BLUE, 700)]
    p += [T(40, 580, "A return posts a reversing transaction dated the day it arrives. An unauthorised return is never retried.", 23, "#5a1308", 700),
          T(40, 620, "A card charge settles in seconds; a card dispute arrives months later as its own reversal.", 22, "#57606a", 600)]
    (OUT / "states.svg").write_text(svgdoc(1600, 660, "".join(p)))
states()

def entries():
    p = [T(40, 44, "A $1,200 loan booked, then one $150 instalment collected", 28, INK, 800)]
    cols = [("Transaction", 40, 300), ("Account", 360, 520), ("Debit", 900, 260), ("Credit", 1180, 260)]
    for lab, x, w in cols:
        p += [R(x, 80, w, 54, "#eef1f4", GREY, rx=6), T(x + 16, 116, lab, 23, INK, 800)]
    rows = [("Loan booked", "Loan principal receivable", "1,200", ""), ("", "Merchant payable", "", "1,164"), ("", "Merchant discount income", "", "36"),
            ("Instalment, pending", "Cash clearing", "150", ""), ("", "Loan principal receivable", "", "150"),
            ("Debit settles", "Cash at bank", "150", ""), ("", "Cash clearing", "", "150")]
    for i, (t, a, d_, cr) in enumerate(rows):
        y = 146 + i * 52
        p += [T(56, y + 33, t, 21, INK, 800), R(360, y, 520, 46, "#fff", "#d0d7de", rx=6), T(376, y + 31, a, 21, INK, 600),
              R(900, y, 260, 46, "#e7f4ec" if d_ else "#fff", "#d0d7de", rx=6), T(1140, y + 32, d_, 23, GREEN, 800, "end"),
              R(1180, y, 260, 46, "#dbeafe" if cr else "#fff", "#d0d7de", rx=6), T(1420, y + 32, cr, 23, BLUE, 800, "end")]
        if t and i: p.append(L(40, y - 3, 1440, y - 3, "#d0d7de", 1.5))
    p += [T(40, 545, "Each transaction sums to zero in integer cents. A return is a new transaction reversing the last two lines.", 22, "#57606a", 700)]
    (OUT / "entries.svg").write_text(svgdoc(1600, 580, "".join(p)))
entries()

def dayplan():
    p = [T(40, 44, "The 1st, planned backwards from the bank's 14:00 cut-off (initial targets)", 28, INK, 800)]
    x0, x1, h0, h1 = 240, 1540, 5, 15
    sx = lambda hh: x0 + (hh - h0) / (h1 - h0) * (x1 - x0)
    for hh in range(5, 16, 1):
        p += [L(sx(hh), 90, sx(hh), 420, "#eef0f2", 1.5), T(sx(hh), 450, f"{hh:02d}:00", 19, "#57606a", 600, "middle")]
    lanes = [("Card, 90 / s", 120, [(6.0, 6.37, BLUE, "120,000 in 22 min")]),
             ("Debit file", 200, [(9.0, 10.5, PURPLE, "build, validate, submit")]),
             ("Bank", 280, [(10.5, 11.0, GREEN, "ack"), (14.0, 14.05, RED, "")]),
             ("Retries", 360, [(7.0, 7.5, AMBER, "soft declines")])]
    for lab, y, bars in lanes:
        p.append(T(40, y + 36, lab, 22, INK, 800))
        for a, z, col, txt in bars:
            fill = {BLUE: "#dbeafe", PURPLE: "#ede7fb", GREEN: "#e7f4ec", RED: "#fdecea", AMBER: "#fdf3e1"}[col]
            p += [R(sx(a), y + 8, max(sx(z) - sx(a), 8), 46, fill, col), T(sx(z) + 12, y + 40, txt, 20, col, 700)]
    p += [L(sx(14), 90, sx(14), 420, RED, 3.5, True), T(sx(14) - 10, 84, "cut-off 14:00", 21, RED, 800, "end")]
    p += [T(40, 500, "42 a second is nothing for a database. The limits are 100 card charges a second and the 14:00 cut-off.", 23, INK, 700)]
    (OUT / "dayplan.svg").write_text(svgdoc(1600, 530, "".join(p)))
dayplan()

print(sorted(q.name for q in OUT.glob("*.svg")))

# ───────────── C4 level 3: the dispatcher, one level down (5.1; the box challenges 1, 2 and 7 open) ─────────────
CS = 25
d = c4.Diagram(1830, 770, canon="comp-dsp")
d.boundary(275, 30, 1250, 720, "Dispatcher", "Container: Go worker", top="left")
d.node("db", 20, 300, 220, 160, "db", "Servicing DB", "PostgreSQL", "Intents, outbox.", size=CS)
d.node("poll", 310, 300, 300, 160, "component", "Outbox poller", "SKIP LOCKED", "Claims sends by shard.", size=CS)
d.node("plan", 720, 80, 300, 160, "component", "Day plan", "per rail", "Windows back from cut-off.", size=CS)
d.node("bkt", 720, 300, 300, 160, "component", "Rail budgets", "token bucket", "Live rate; halves on throttle.", size=CS)
d.node("file", 1150, 80, 300, 160, "component", "File builder", "batch", "Counts and totals checked.", size=CS)
d.node("card", 1150, 300, 300, 160, "component", "Card client", "HTTP, key", "Timeout → UNKNOWN.", size=CS)
d.node("post", 1150, 540, 300, 160, "component", "Result poster", "Component", "Ledger post by key.", size=CS)
d.node("bank", 1580, 80, 240, 160, "ext", "Bank", "SFTP, cut-off", "", size=CS)
d.node("proc", 1580, 300, 240, 160, "ext", "Card processor", "API", "", size=CS)
d.node("res", 1580, 540, 240, 160, "container", "Resolver", "Worker", "", size=CS)
d.edge("db", "poll", "", "", src="r", dst="l")
d.edge("poll", "bkt", "", "", src="r", dst="l")
d.edge("plan", "bkt", "rates", "", src="b", dst="t", at=(910, 275), size=22)
d.edge("bkt", "file", "", "", src="r:0.2", dst="l:0.7")
d.edge("bkt", "card", "", "", src="r", dst="l")
d.edge("file", "bank", "", "", src="r", dst="l")
d.edge("card", "proc", "", "", src="r", dst="l")
d.edge("card", "post", "result", "", src="b", dst="t", at=(1340, 505), size=22)
d.edge("post", "db", "one commit", "", src="l", dst="b", via=[(130, 620)], at=(700, 605), size=22)
d.edge("post", "res", "", "", src="r", dst="l")
d.save(OUT / "c4-comp-dsp.svg", order=["db", "poll", "bkt", "plan", "card", "proc", "file", "bank", "post", "res"])
import diagrams_puml  # PlantUML diagrams (2026-11-25): mechanisms, options, objections, boundary
