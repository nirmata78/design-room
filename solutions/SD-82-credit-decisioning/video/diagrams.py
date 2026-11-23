#!/usr/bin/env python3
"""SD-82 credit decisioning and origination: every picture for the video and the written design -> ./svg/*.svg.
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
# Five columns, 152 px between joined boxes. The counter path runs left to right through the middle row;
# what we keep (vault, records) and what happens after booking (log, funding) sit above and below.
X = [15, 357, 699, 1041, 1383]; W = 190
b = bs.Baseline(1600, 760)
b.node("pos", X[0], 300, W, 130, "client", "Phone / POS", "customer, merchant")
b.node("api", X[1], 300, W, 130, "edge", "API edge", "auth · keys")
b.node("app", X[2], 300, W, 130, "service", "Application service", "state machine")
b.node("orch", X[3], 300, W, 130, "service", "Decision orchestrator", "one deadline · breakers", since=2)
b.node("ven", X[4], 300, W, 130, "ext", "Credit vendors", "bureaus · identity")
b.node("vault", X[1], 50, W, 130, "data", "Identity vault", "tokens out", since=3, shape="db")
b.node("db", X[2], 550, W, 130, "data", "Application DB", "loans · outbox", shape="db")
b.node("log", X[1], 550, W, 130, "queue", "Event log", "LoanBooked", since=2, shape="queue")
b.node("fund", X[0], 550, W, 130, "service", "Funding", "then servicing", since=3)
b.node("model", X[3], 550, W, 130, "service", "Policy engine", "model · policy · pricing", since=2)
b.node("rec", X[4], 550, W, 130, "data", "Decision records", "7 years", since=3, shape="db")
# tags: only inside a challenge
b.node("chal", X[3], 50, W, 130, "service", "Challenger", "shadow · 5 %", tag="ch6")
b.node("ana", X[2], 50, W, 130, "ext", "Analytics", "wants the data", tag="ch7")

REQ = dict(src="r:0.25", dst="l:0.25"); RSP = dict(src="l:0.75", dst="r:0.75", kind="resp")
mid = lambda i: (X[i] + W + X[i + 1]) / 2          # label position between column i and i+1
b.edge("p-a", "pos", "api", "submit", **REQ, at=(mid(0), 322))
b.edge("a-p", "api", "pos", "offers · loan", **RSP, at=(mid(0), 420))
b.edge("a-ap", "api", "app", "create", **REQ, at=(mid(1), 322))
b.edge("ap-a", "app", "api", "status", **RSP, at=(mid(1), 420))
# V1: the application service calls the vendors itself, one after another
b.edge("ap-v1", "app", "ven", "identity, then bureau", until=1, **REQ, at=(1136, 322))
b.edge("v-ap1", "ven", "app", "answers, in turn", until=1, **RSP, at=(1136, 420))
b.edge("ap-db", "app", "db", "state", src="b:0.5", dst="t:0.5", at=(870, 500))
# V2: the orchestrator, the model step, the outbox relay
b.edge("ap-o", "app", "orch", "decide", since=2, **REQ, at=(mid(2), 322))
b.edge("o-ap", "orch", "app", "decision", since=2, **RSP, at=(mid(2), 420))
b.edge("o-v", "orch", "ven", "all at once", since=2, **REQ, at=(mid(3), 322))
b.edge("v-o", "ven", "orch", "answers", since=2, **RSP, at=(mid(3), 420))
b.edge("o-m", "orch", "model", "score", src="b:0.5", dst="t:0.5", since=2, at=(1100, 500))
b.edge("db-l", "db", "log", "outbox relay", src="l:0.5", dst="r:0.5", kind="async", since=2, at=(mid(1), 588))
# V3: vault, records, funding
b.edge("a-vt", "api", "vault", "tokenise", src="t:0.5", dst="b:0.5", since=3, at=(530, 236))
b.edge("o-vt", "orch", "vault", "detokenise in adapter", src="t:0.2", dst="r:0.6", via=[(1079, 236), (600, 236), (600, 128)],
       since=3, at=(1000, 224))
b.edge("o-r", "orch", "rec", "decision record", src="b:0.85", dst="t:0.5", via=[(1202, 470), (1478, 470)], kind="async",
       since=3, at=(1340, 458))
b.edge("l-f", "log", "fund", "LoanBooked", src="l:0.5", dst="r:0.5", kind="async", since=3, at=(mid(0), 588))
# tagged edges
b.edge("o-c", "orch", "chal", "shadow score", src="t:0.7", dst="b:0.5", tag="ch6", at=(1210, 236))
b.edge("ap-an", "app", "ana", "export", src="t:0.8", dst="b:0.8", tag="ch7", at=(780, 250))

TOP = {"chal", "ana", "vault"}
def sv(name, h, **view):
    """Save one view. Views that show nothing in the top row are cropped to start below it, so the
    picture keeps its height on a slide that also carries text strips."""
    b.h = h
    b.save(OUT / name, **view)
    keep = view.get("keep")
    if name.startswith("ch") and keep and not (TOP & set(keep)):
        f = OUT / name; t = f.read_text(); y0 = 205
        t = t.replace(f'viewBox="0 0 1600 {h}" width="1600" height="{h}"',
                      f'viewBox="0 {y0} 1600 {h - y0}" width="1600" height="{h - y0}"', 1)
        f.write_text(t)

ALL = ["ch6", "ch7"]
sv("base-v1.svg", 780, upto=1, legend=True)
sv("base-v2.svg", 780, upto=2, new=2, legend=True)
sv("base-v3.svg", 780, upto=3, new=3, legend=True)
sv("base-final.svg", 780, upto=3, legend=True)
# 5.2 the alternate path: one box changes (one bureau, refer whatever is missing)
sv("alt.svg", 800, upto=3, keep=["app", "orch", "ven", "model"], alt=["ven"])
sv("map.svg", 780, upto=3, legend=True, attack=["ven", "model", "app", "fund", "rec", "vault", "orch"], keep=None)
sv("flow-fr1.svg", 700, upto=3, flow=["p-a", "a-vt", "a-ap", "ap-db", "ap-a", "a-p"], keep=["pos", "api", "vault", "app", "db"])
sv("flow-fr2.svg", 700, upto=3, flow=["ap-o", "o-vt", "o-v", "v-o", "o-m", "o-r", "o-ap", "a-p"],
   keep=["pos", "api", "app", "orch", "ven", "vault", "model", "rec"])
sv("flow-fr3.svg", 700, upto=3, flow=["p-a", "a-ap", "ap-db", "ap-a", "a-p"], keep=["pos", "api", "app", "db"])
sv("flow-fr4.svg", 700, upto=3, flow=["ap-db", "db-l", "l-f"], keep=["app", "db", "log", "fund"])
# challenge overlays
N = 640  # note row for the 700-high views
sv("ch1-attack.svg", 800, upto=2, attack=["ven"], keep=["pos", "api", "app", "orch", "ven"], hot=["o-v", "v-o"])
sv("ch1-fix.svg", 800, upto=2, fix=["orch"], keep=["pos", "api", "app", "orch", "ven"], ok=["o-v", "v-o"])
sv("ch2-attack.svg", 800, upto=3, attack=["ven", "model"], keep=["app", "orch", "ven", "model"], hot=["o-v"])
sv("ch2-fix.svg", 800, upto=3, fix=["model"], keep=["app", "orch", "ven", "model"], ok=["o-m"])
sv("ch3-attack.svg", 800, upto=2, attack=["app", "db"], keep=["pos", "api", "app", "db"], hot=["p-a", "a-ap", "ap-db"])
sv("ch3-fix.svg", 800, upto=2, fix=["db"], keep=["pos", "api", "app", "db", "log"], ok=["ap-db", "db-l"])
sv("ch4-attack.svg", 800, upto=3, attack=["fund"], keep=["app", "db", "log", "fund"], hot=["l-f"])
sv("ch4-fix.svg", 800, upto=3, fix=["fund"], keep=["app", "db", "log", "fund"], ok=["db-l", "l-f"])
sv("ch5-attack.svg", 800, upto=2, attack=["model"], keep=["app", "orch", "model"], hot=["o-m"])
sv("ch5-fix.svg", 800, upto=3, fix=["rec"], keep=["app", "orch", "model", "rec"], ok=["o-r", "o-m"])
sv("ch6-attack.svg", 800, upto=3, attack=["model"], keep=["app", "orch", "model", "rec"], hot=["o-m"])
b.size = 32
sv("ch6-fix.svg", 800, upto=3, show=["ch6"], fix=["chal"], keep=["orch", "model", "rec", "chal"], ok=["o-c", "o-m"])
b.size = 27
sv("ch7-attack.svg", 800, upto=2, show=["ch7"], attack=["app", "db", "ana"], keep=["pos", "api", "app", "db", "ana", "orch", "ven"], hot=["ap-an", "ap-db"])
sv("ch7-fix.svg", 800, upto=3, show=["ch7"], fix=["vault"], keep=["api", "app", "ana", "vault", "orch", "ven"], ok=["a-vt", "o-vt", "ap-an"])
sv("ch8-attack.svg", 800, upto=3, attack=["model"], keep=["pos", "api", "app", "orch", "model"])
sv("ch8-fix.svg", 800, upto=3, fix=["orch", "model", "fund"], keep=["pos", "api", "app", "orch", "model", "fund", "log", "db"])
bs.budget_bar(OUT / "budget.svg", [("phone, state", 200, "client"), ("vendors, one deadline", 2000, "ext"),
                                   ("model, policy, price", 250, "service"), ("record, push", 250, "edge")],
              total=3000, unit="ms", title="Submit to offers on screen, p95 (initial target 3 s)")

# ───────────────────────────── 2 · C4 ────────────────────────────────────────────────────────────────
d = c4.Diagram(1830, 760)
d.node("cus", 40, 80, 340, 170, "person", "Customer", "Person", "At the counter, on a phone.", size=26)
d.node("mer", 40, 500, 340, 170, "person", "Merchant", "Person", "Point of sale; gets paid.", size=26)
d.node("sys", 700, 280, 420, 200, "system", "Credit decisioning", "Software System", "Apply, decide, book, fund.", size=28)
d.node("ven", 1450, 40, 360, 160, "ext", "Credit vendors", "External", "Bureau, identity, bank data.", size=26)
d.node("bank", 1450, 300, 360, 160, "ext", "Partner bank", "External", "Lender of record.", size=26)
d.node("svc", 1450, 560, 360, 160, "ext", "Servicing (SD-95)", "Internal system", "Schedule, repayments.", size=26)
d.edge("cus", "sys", "Apply, accept", "HTTPS", src="r:0.8", dst="l:0.25", at=(540, 250), size=22)
d.edge("mer", "sys", "Start a sale, status", "HTTPS API", src="r:0.2", dst="l:0.8", at=(540, 545), size=22)
d.edge("sys", "ven", "Reports, checks", "HTTPS, paid", src="r:0.2", dst="l:0.6", at=(1285, 205), size=22)
d.edge("sys", "bank", "Funding, loan sale", "files, API", src="r:0.5", dst="l:0.5", at=(1285, 360), size=22)
d.edge("sys", "svc", "LoanBooked", "event", src="r:0.8", dst="l:0.4", at=(1285, 555), size=22)
d.save(OUT / "c4-context.svg")

CX, CW, CY, CH, CS = [50, 420, 790, 1160], 280, [90, 340, 590], 170, 25
def containers(name):
    d = c4.Diagram(1830, 800)
    d.boundary(20, 30, 1450, 750, "Credit decisioning", "Software System", top="left")
    d.node("vlt", CX[0], CY[0], CW, CH, "db", "Identity vault", "Tokenisation", "The only raw identity.", size=CS)
    d.node("lg", CX[1], CY[0], CW, CH, "queue", "Event log", "Log", "LoanBooked, decisions.", size=CS)
    d.node("fnd", CX[2], CY[0], CW, CH, "container", "Funding", "Service", "Transfers, reconcile.", size=CS)
    d.node("api", CX[0], CY[1], CW, CH, "container", "API edge", "Gateway", "Merchant auth, keys.", size=CS)
    d.node("app", CX[1], CY[1], CW, CH, "container", "Application service", "Service", "State machine, outbox.", size=CS)
    d.node("orc", CX[2], CY[1], CW, CH, "container", "Decision orchestrator", "Service", "Deadline, breakers.", size=CS)
    d.node("db", CX[1], CY[2], CW, CH, "db", "Application DB", "Relational", "Apps, loans, outbox.", size=CS)
    d.node("pol", CX[2], CY[2], CW, CH, "container", "Policy engine", "Service", "Model, policy, pricing.", size=CS)
    d.node("rec", CX[3], CY[2], CW, CH, "db", "Decision records", "Object storage", "Encrypted, 7 years.", size=CS)
    d.node("bank", 1540, CY[0], 280, CH, "ext", "Partner bank", "External", "Pays merchants.", size=CS)
    d.node("ven", 1540, CY[1], 280, CH, "ext", "Credit vendors", "External", "Bureau, identity, fraud.", size=CS)
    d.edge("api", "app", "", "", src="r", dst="l")
    d.edge("app", "orc", "", "", src="r", dst="l")
    d.edge("orc", "ven", "all at once, one deadline", "HTTPS", src="r", dst="l", at=(1305, 405), size=22)
    d.edge("api", "vlt", "tokenise", "", src="t", dst="b", at=(260, 302), size=22)
    d.edge("app", "db", "one commit", "SQL", src="b", dst="t", at=(640, 552), size=22)
    d.edge("orc", "pol", "score", "", src="b", dst="t", at=(990, 552), size=22)
    d.edge("orc", "rec", "record", "async", src="r:0.8", dst="t", via=[(1300, 476)], at=(1360, 552), size=22)
    d.edge("db", "lg", "outbox relay", "async", src="l", dst="l", via=[(380, 675), (380, 175)], at=(300, 552), size=22)
    d.edge("lg", "fnd", "", "", src="r", dst="l")
    d.edge("fnd", "bank", "transfers", "files, API", src="r", dst="l", at=(1305, 155), size=22)
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

seq("seq-decide",
    [("ph", "Phone", "person"), ("ap", "Application svc", "container"), ("or", "Orchestrator", "container"), ("vd", "Vendors", "ext"), ("pl", "Policy", "container")],
    [("m", "ph", "ap", "POST /applications, Idempotency-Key"),
     ("r", "ap", "ph", "202 ap_91 STARTED"),
     ("m", "ap", "or", "decide(ap_91), deadline now + 2.0 s"),
     ("m", "or", "vd", "identity · fraud · bureau A, all at once", dict(kind="async")),
     ("r", "vd", "or", "identity 0.40 s · fraud 0.35 s · bureau 0.62 s"),
     ("m", "or", "pl", "features → model v9 → policy v31 → pricing v12"),
     ("r", "pl", "or", "APPROVE, 3 offers, reasons"),
     ("n", "or", "or", "write the decision record once", "green"),
     ("r", "or", "ap", "OFFERED; push offers to the phone", dict(hl=True))])

seq("seq-book",
    [("ph", "Phone or tablet", "person"), ("ap", "Application svc", "container"), ("db", "Application DB", "db"), ("rl", "Relay → log", "queue")],
    [("m", "ph", "ap", "POST accept {of_3, disclosure v7}, Idempotency-Key"),
     ("m", "ap", "db", "BEGIN; UPDATE … WHERE status = OFFERED AND version = 7"),
     ("m", "ap", "db", "INSERT loan (application_id UNIQUE); INSERT outbox; COMMIT"),
     ("r", "db", "ap", "1 row · committed"),
     ("r", "ap", "ph", "201 ln_5531", dict(hl=True)),
     ("m", "rl", "db", "poll unpublished outbox rows", dict(kind="async")),
     ("n", "rl", "rl", "publish LoanBooked, then mark published (at least once)", "amber")])

seq("seq-ch1-gather",
    [("or", "Orchestrator", "container"), ("id", "Identity", "ext"), ("ba", "Bureau A", "ext"), ("bb", "Bureau B", "ext")],
    [("m", "or", "id", "check (t = 0)", dict(kind="async")),
     ("m", "or", "ba", "pull (t = 0)", dict(kind="async")),
     ("r", "id", "or", "ok at 0.40 s"),
     ("n", "or", "or", "t = 2.0 s: deadline. Bureau A silent; breaker closed", "amber"),
     ("n", "or", "or", "decide with what arrived: missing-data policy (no race to B)", "green"),
     ("r", "ba", "or", "report at 4.1 s: record it, use it to finish a refer", dict(hl=True))])

seq("seq-ch2-refer",
    [("ph", "Customer", "person"), ("or", "Orchestrator", "container"), ("bb", "Bureau B (5/s)", "ext"), ("ba", "Bureau A", "ext")],
    [("n", "or", "or", "breaker on A open; bucket for B empty this second", "amber"),
     ("r", "or", "ph", "REFERRED: we'll finish in two minutes by text"),
     ("n", "or", "or", "refer queue, oldest first", "blue"),
     ("m", "or", "bb", "pull when a token frees up"),
     ("r", "bb", "or", "report at 11:03:40"),
     ("r", "or", "ph", "text: your offers are ready", dict(hl=True))])

seq("seq-ch4-fund",
    [("fn", "Funding", "container"), ("bk", "Partner bank", "ext"), ("rc", "Reconciliation", "container")],
    [("m", "fn", "bk", "transfer ln_5531 $1,164, key = ln_5531"),
     ("n", "fn", "fn", "timeout: state UNKNOWN (never resend)", "amber"),
     ("m", "fn", "bk", "status? key = ln_5531"),
     ("r", "bk", "fn", "not found (yet)"),
     ("n", "fn", "fn", "wait for the reconciliation window", "amber"),
     ("m", "rc", "bk", "next-day file"),
     ("r", "bk", "rc", "ln_5531 settled 18:03"),
     ("r", "rc", "fn", "UNKNOWN → SETTLED; no resend", dict(hl=True))])

seq("seq-ch5-replay",
    [("rg", "Regulator request", "person"), ("rp", "Replay job", "container"), ("rs", "Record store", "db"), ("md", "Model registry", "container")],
    [("m", "rg", "rp", "explain ap_204 (Jan 2026)"),
     ("m", "rp", "rs", "load record: inputs, versions, reasons"),
     ("r", "rs", "rp", "features, report ref, model v9, policy v31"),
     ("m", "rp", "md", "load model v9, policy v31"),
     ("n", "rp", "rp", "re-score the frozen features", "blue"),
     ("r", "rp", "rg", "DECLINE: high utilisation, short history (match)", dict(hl=True))])

# ───────────────────────────── 4 · data models ───────────────────────────────────────────────────────
c = er.Chen(1600, 900, size=29)
c.entity("ap", 200, 120, "APPLICANT"); c.entity("a", 680, 120, "APPLICATION"); c.entity("vc", 1200, 120, "VENDOR CALL", weak=True)
c.entity("dc", 680, 470, "DECISION"); c.entity("of", 1200, 470, "OFFER", weak=True); c.entity("ln", 200, 470, "LOAN")
c.entity("ft", 200, 780, "FUNDING TRANSFER", weak=True)
c.rel("sb", 440, 120, "SUBMITS"); c.rel("ca", 940, 120, "CALLS", identifying=True); c.rel("dd", 680, 300, "DECIDED BY")
c.rel("ho", 940, 470, "HOLDS", identifying=True); c.rel("bk", 440, 470, "BOOKS"); c.rel("pd", 200, 630, "PAID BY", identifying=True)
c.attr("tk", 200, 40, "vault_token", of="ap", key=True)
c.attr("id", 600, 40, "id", of="a", key=True); c.attr("st", 800, 40, "status", of="a"); c.attr("vv", 860, 200, "version", of="a")
c.attr("ct", 1400, 120, "cost", of="vc"); c.attr("vn", 1300, 40, "vendor", of="vc", partial=True)
c.attr("rs", 520, 560, "reasons", of="dc"); c.attr("vs", 840, 560, "versions", of="dc")
c.attr("ex", 1400, 470, "expires_at", of="of"); c.attr("ap2", 1300, 560, "APR", of="of")
c.attr("dv", 140, 380, "disclosure_v", of="ln")
c.attr("sta", 420, 780, "state", of="ft")
c.link("ap", "sb", "1"); c.link("sb", "a", "N", total=True)
c.link("a", "ca", "1"); c.link("ca", "vc", "N")
c.link("a", "dd", "1", src="b", dst="t"); c.link("dd", "dc", "1", src="b", dst="t")
c.link("dc", "ho", "1"); c.link("ho", "of", "N")
c.link("a", "bk", "1", src="b", dst="t"); c.link("bk", "ln", "0..1")
c.link("ln", "pd", "1", src="b", dst="t"); c.link("pd", "ft", "N", src="b", dst="t")
c.legend(1260, 700, size=22, rows=["rect", "rect2", "dia", "dia2", "oval", "key"])
c.note(470, 820, 740, "One application books at most one loan; the decision is written once.")
c.save(OUT / "erd-chen.svg")

e = er.ERD(1600, 860, size=24)
e.entity("app", 30, 40, 470, "application", [("id", "text", "PK"), ("merchant_id", "text", "IX"), ("applicant_tok", "text", ""),
         ("amount_cents", "int", ""), ("status", "text", ""), ("version", "int", "")],
         kind="focus", caption="the state machine; optimistic version")
e.entity("dec", 570, 40, 470, "decision", [("application_id", "text", "PK"), ("outcome", "text", ""), ("reasons", "text[]", ""),
         ("versions", "jsonb", ""), ("record_uri", "text", "")],
         caption="written once, never updated")
e.entity("ln", 1110, 40, 460, "loan", [("id", "text", "PK"), ("application_id", "text", "UQ"), ("offer_id", "text", ""),
         ("disclosure_v", "text", ""), ("terms", "jsonb", "")],
         caption="UNIQUE(application_id): one loan")
e.entity("ob", 30, 480, 470, "outbox", [("event_id", "text", "PK"), ("type", "text", ""), ("payload", "jsonb", ""), ("published_at", "ts", "")],
         kind="ext", caption="same commit as the loan")
e.entity("vc", 570, 480, 470, "vendor_call", [("application_id", "text", "PK"), ("vendor · seq", "text", "PK"), ("outcome", "text", ""),
         ("cost_cents · ms", "int", "")],
         caption="every paid call, with its cost")
e.entity("vl", 1110, 480, 460, "vault (separate)", [("token", "text", "PK"), ("ssn · dob · address", "enc", ""), ("key_id", "text", "")],
         kind="redis", caption="only the vault and adapters")
e.rel("dec", "app", "1", "1", src="l:0.3", dst="r:0.3", label="", at=(535, 100))
e.rel("ln", "dec", "0..1", "1", src="l:0.3", dst="r:0.3", label="", at=(1075, 100))
e.note(30, 800, 1540, "The record body (report by reference, feature vector, missing calls) lives in encrypted object storage under record_uri.")
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
def ARR(x1, y1, x2, y2, col=INK, sw=2.6):
    import math
    a = math.atan2(y2 - y1, x2 - x1); h = 14
    p1 = (x2 - h * math.cos(a - 0.4), y2 - h * math.sin(a - 0.4)); p2 = (x2 - h * math.cos(a + 0.4), y2 - h * math.sin(a + 0.4))
    return L(x1, y1, x2, y2, col, sw) + f'<polygon points="{x2},{y2} {p1[0]:.1f},{p1[1]:.1f} {p2[0]:.1f},{p2[1]:.1f}" fill="{col}"/>'
FILL = {BLUE: "#dbeafe", AMBER: "#fdf3e1", GREEN: "#d3f3e6", RED: "#fdecea", PURPLE: "#e6dcfb", GREY: "#eceff2"}

def tension():
    p = [T(40, 44, "Time against evidence against money: what waiting buys, and what it costs", 28, INK, 800)]
    x0, W_ = 380, 1140; sx = lambda t: x0 + t / 10 * W_
    p += [L(x0, 390, x0 + W_, 390, GREY, 2)]
    for t in range(0, 11, 2):
        p += [L(sx(t), 384, sx(t), 396, GREY, 2), T(sx(t), 424, f"{t} s", 20, "#57606a", 600, "middle")]
    rows = [("Identity", 0.40, GREEN), ("Fraud", 0.35, GREEN), ("Bureau A, usual", 0.62, BLUE), ("Bureau A, slow (1 in 10)", 4.1, RED)]
    for i, (lab, t, col) in enumerate(rows):
        y = 100 + i * 66
        p += [T(40, y + 30, lab, 22, INK, 700), R(x0, y, sx(t) - x0, 40, FILL[col], col), T(sx(t) + 12, y + 29, f"{t:.2f} s", 21, col, 800)]
    p += [L(sx(2), 80, sx(2), 380, AMBER, 4, True), T(sx(2) + 10, 78, "deadline 2.0 s: decide with what arrived", 21, "#a86a12", 800)]
    p += [L(sx(10), 80, sx(10), 380, RED, 4, True), T(sx(10) - 10, 78, "lost sale", 21, RED, 800, "end")]
    p += [R(40, 450, 1520, 70, "#fdf3e1", AMBER), T(800, 495, "Wait: more evidence, lost sales. Decide early: risk. Ask a second bureau: another $1 and another inquiry.", 23, "#4a3207", 800, "middle")]
    (OUT / "tension.svg").write_text(svgdoc(1600, 540, "".join(p)))
tension()

def policy():
    p = [T(40, 44, "When the bureau is missing at the deadline: four answers, in order, signed by credit risk", 28, INK, 800)]
    rows = [("1 · Second bureau", "only after an error or an open breaker; never a race", BLUE, "rate-limited to its contract"),
            ("2 · Decide without a bureau", "returning customer in good standing, ≤ $500", GREEN, "daily exposure cap $250,000"),
            ("3 · Refer", "“we'll finish in two minutes by text”; merchant sees pending", AMBER, "finish within 10 minutes"),
            ("4 · Decline", "only with a reason about the applicant", RED, "never “our vendor was slow”")]
    for i, (a, bdesc, col, cap) in enumerate(rows):
        y = 90 + i * 100
        p += [R(40, y, 420, 80, FILL[col], col, rx=12), T(60, y + 50, a, 26, INK, 800),
              R(480, y, 700, 80, "#ffffff", col, rx=12), T(500, y + 50, bdesc, 22, INK, 600),
              R(1200, y, 360, 80, "#f6f8fa", GREY, rx=12), T(1380, y + 50, cap, 21, "#3a424a", 700, "middle")]
        if i < 3: p.append(ARR(250, y + 80, 250, y + 100, GREY, 2.2))
    p += [T(40, 520, "Every row is a versioned setting with a counter, a cap and a dashboard. Engineering builds it; credit risk owns it.", 23, "#173d24", 700)]
    (OUT / "policy.svg").write_text(svgdoc(1600, 550, "".join(p)))
policy()

def states():
    p = [T(40, 44, "The application as a state machine: one committed row per transition", 28, INK, 800)]
    S = {"STARTED": (60, 200, BLUE), "CHECKING": (330, 200, BLUE), "OFFERED": (640, 110, GREEN), "REFERRED": (640, 290, AMBER),
         "DECLINED": (640, 430, RED), "BOOKED": (950, 110, GREEN), "EXPIRED": (950, 250, GREY), "FUNDED": (1260, 110, GREEN)}
    for n, (x, y, col) in S.items():
        p += [R(x, y, 200, 70, FILL[col], col, rx=35), T(x + 100, y + 45, n, 24, INK, 800, "middle")]
    def a(f, t, lab="", dy=0):
        (x1, y1, _), (x2, y2, _) = S[f], S[t]
        sx_, sy = x1 + 200, y1 + 35; ex, ey = x2, y2 + 35
        out = ARR(sx_, sy, ex - 4, ey, INK, 2.4)
        if lab: out += T((sx_ + ex) / 2, (sy + ey) / 2 - 14 + dy, lab, 18, "#57606a", 600, "middle")
        return out
    p += [a("STARTED", "CHECKING", "vendors called"), a("CHECKING", "OFFERED", "approve"), a("CHECKING", "REFERRED", "missing data", 30),
          a("CHECKING", "DECLINED", "reasons", 40), a("OFFERED", "BOOKED", "accept"), a("OFFERED", "EXPIRED", "15 min", 30),
          a("BOOKED", "FUNDED", "merchant paid")]
    p += [ARR(740, 290, 740, 184, AMBER, 2.4), T(752, 245, "finished", 18, "#a86a12", 700)]
    p += [R(900, 400, 660, 110, "#e7f4ec", GREEN, rx=12), T(920, 440, "The one atomic step: OFFERED → BOOKED", 23, "#173d24", 800),
          T(920, 478, "loan + outbox row in the same commit, at a version", 21, "#173d24", 600)]
    p += [T(40, 560, "A credit pull is never “compensated”: it happened, and the row records it. Only funding, after BOOKED, has a real undo.", 22, INK, 700)]
    (OUT / "states.svg").write_text(svgdoc(1600, 590, "".join(p)))
states()

def record():
    p = [T(40, 44, "The decision record: same inputs + same versions = the same answer, years later", 28, INK, 800)]
    cols = [("Inputs, frozen", BLUE, ["bureau report (encrypted, by reference)", "identity and fraud results", "internal history as of then",
                                      "the feature vector", "which calls were missing"]),
            ("Versions", PURPLE, ["model v9", "policy v31 (incl. missing-data table)", "pricing v12", "disclosure v7", "orchestrator build"]),
            ("Outputs", GREEN, ["outcome and offers", "ranked reasons", "the degraded path taken", "the deadline and timings", "who signed the policy"])]
    for i, (h, col, items) in enumerate(cols):
        x = 40 + i * 515
        p += [R(x, 80, 490, 380, FILL[col], col, rx=14), T(x + 245, 125, h, 26, INK, 800, "middle")]
        for j, it in enumerate(items):
            p += [T(x + 26, 180 + j * 56, "· " + it, 22, INK, 600)]
    p += [T(40, 510, "About 50 KB each, written once: 100 GB a month, 8.4 TB over seven years, in encrypted object storage.", 23, "#173d24", 700)]
    (OUT / "record.svg").write_text(svgdoc(1600, 540, "".join(p)))
record()

def vault():
    p = [T(40, 44, "The identity boundary: real values inside, tokens everywhere else", 28, INK, 800)]
    p += [R(40, 90, 600, 380, "#fdecea", RED, dash=True, rx=18), T(340, 130, "Inside the boundary", 25, RED, 800, "middle"),
          R(80, 160, 520, 110, FILL[GREEN], GREEN, rx=12), T(340, 205, "Identity vault", 25, INK, 800, "middle"),
          T(340, 243, "SSN · date of birth · address, keys per field", 20, "#173d24", 600, "middle"),
          R(80, 310, 520, 110, FILL[GREY], GREY, rx=12), T(340, 355, "Vendor adapters", 25, INK, 800, "middle"),
          T(340, 393, "detokenise for the call; logs scrubbed", 20, "#3a424a", 600, "middle")]
    outs = ["Application service and DB", "Decision records", "Support tools (masked)", "Analytics and training (features)"]
    for i, o in enumerate(outs):
        y = 100 + i * 92
        p += [R(900, y, 640, 72, FILL[BLUE], BLUE, rx=12), T(1220, y + 46, o, 23, INK, 700, "middle"), ARR(642, 280, 896, y + 36, GREY, 2.2)]
    p += [T(660, 330, "tokens", 22, PURPLE, 800, "start")]
    p += [T(40, 520, "Card numbers fall under the card industry's standard; a social security number under privacy and lending law.", 22, INK, 700)]
    (OUT / "vault.svg").write_text(svgdoc(1600, 550, "".join(p)))
vault()

def rollout():
    p = [T(40, 44, "Changing the model: each step can only see what the one before cannot", 28, INK, 800)]
    steps = [("Backtest", "on labelled history", "approval, loss on past loans", BLUE),
             ("Shadow", "both score, champion acts", "approval and reasons by segment", PURPLE),
             ("Challenger 5 %", "challenger decides, capped", "real labels, first payments", AMBER),
             ("Widen", "a policy version change", "kill switch per version", GREEN)]
    for i, (h, s1, s2, col) in enumerate(steps):
        x = 40 + i * 390
        p += [R(x, 100, 350, 200, FILL[col], col, rx=14), T(x + 175, 150, h, 27, INK, 800, "middle"),
              T(x + 175, 200, s1, 21, INK, 600, "middle"), T(x + 175, 250, s2, 20, "#3a424a", 600, "middle")]
        if i < 3: p.append(ARR(x + 352, 200, x + 386, 200, GREY, 2.4))
    p += [R(40, 340, 1520, 80, "#fdecea", RED, rx=12), T(800, 390, "Shadow cannot measure loss: people the champion declined never got a loan, so they have no label.", 23, "#5a1308", 800, "middle")]
    p += [T(40, 470, "Signals: first payment missed at 30–45 days, approval parity by group, decline-reason mix. Losses arrive at 90–120 days.", 22, INK, 700)]
    (OUT / "rollout.svg").write_text(svgdoc(1600, 500, "".join(p)))
rollout()

def teams():
    p = [T(40, 44, "Six owners, three contracts", 28, INK, 800)]
    ts = [("Applications and origination", "state machine · booking", BLUE), ("Decisioning platform", "orchestrator · policy engine · serving", PURPLE),
          ("Vendor integrations", "adapters · contracts · spend", GREY), ("Security", "the vault", RED),
          ("Credit risk and data science", "models · every degraded path · caps", AMBER), ("Compliance", "disclosures · notices · retention", GREEN)]
    for i, (n, s, col) in enumerate(ts):
        x = 40 + (i % 3) * 515; y = 90 + (i // 3) * 170
        p += [R(x, y, 490, 140, FILL[col], col, rx=14), T(x + 245, y + 60, n, 24, INK, 800, "middle"), T(x + 245, y + 100, s, 20, "#3a424a", 600, "middle")]
    p += [R(40, 450, 1520, 70, "#f6f8fa", GREY, rx=12),
          T(800, 495, "Contracts: the decision interface · the decision record · the LoanBooked event", 24, INK, 800, "middle")]
    (OUT / "teams.svg").write_text(svgdoc(1600, 540, "".join(p)))
teams()

print(sorted(p.name for p in OUT.glob("*.svg")))

# ───────────── C4 level 3: the decision orchestrator, one level down (5.1; the box challenges 1, 2 and 8 open) ─────────────
CS = 25
d = c4.Diagram(1830, 770, canon="comp-orch")
d.boundary(275, 30, 1250, 720, "Decision orchestrator", "Container: Go", top="left")
d.node("app", 20, 300, 220, 160, "container", "Application service", "Go", "Asks for a decision.", size=CS)
d.node("pre", 310, 80, 300, 160, "component", "Tier-0 checks", "in-process", "Eligibility, blocklist, own book.", size=CS)
d.node("gat", 310, 300, 300, 160, "component", "Gather", "errgroup + deadline", "One 2.0 s deadline.", size=CS)
d.node("late", 310, 540, 300, 160, "component", "Late answers", "Component", "Kept after 2.0 s.", size=CS)
d.node("ad", 720, 80, 320, 160, "component", "Vendor adapters", "one per vendor", "Breaker; token bucket.", size=CS)
d.node("pc", 720, 300, 320, 160, "component", "Policy client", "gRPC", "Features + what is missing.", size=CS)
d.node("rw", 1150, 540, 320, 160, "component", "Record writer", "Component", "One per decision.", size=CS)
d.node("ven", 1580, 80, 240, 160, "ext", "Credit vendors", "bureau, ID, fraud", "", size=CS)
d.node("pol", 1580, 300, 240, 160, "container", "Policy engine", "rules + models", "", size=CS)
d.node("rec", 1580, 540, 240, 160, "db", "Decision records", "write once", "", size=CS)
d.edge("app", "gat", "", "", src="r", dst="l")
d.edge("gat", "pre", "first", "", src="t", dst="b", at=(500, 275), size=22)
d.edge("gat", "ad", "", "", src="r:0.2", dst="l:0.8")
d.edge("ad", "ven", "HTTPS, mTLS", "", src="r", dst="l", at=(1300, 145), size=22)
d.edge("gat", "pc", "", "", src="r", dst="l")
d.edge("pc", "pol", "score", "", src="r", dst="l", at=(1300, 365), size=22)
d.edge("pc", "rw", "", "", src="b:0.7", dst="l:0.5", via=[(944, 620)])
d.edge("rw", "rec", "", "", src="r", dst="l")
d.edge("gat", "late", "after 2.0 s", "", src="b", dst="t", at=(530, 505), size=22)
d.save(OUT / "c4-comp-orch.svg", order=["app", "gat", "pre", "ad", "ven", "pc", "pol", "rw", "rec", "late"])
