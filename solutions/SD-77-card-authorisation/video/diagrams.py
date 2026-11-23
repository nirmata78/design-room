#!/usr/bin/env python3
"""SD-77 card authorisation and issuer processing: every picture for the video and the written design -> ./svg/*.svg.
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
# Middle row: the authorisation path (the product). Top: what the decision reads. Bottom: what happens after the answer.
b = bs.Baseline(1600, 760)
b.node("net", 20, 300, 200, 130, "client", "Card network", "via the processor")
b.node("gw", 350, 300, 200, 130, "edge", "Auth gateway", "ISO 8583 ↔ ours")
b.node("dec", 680, 300, 200, 130, "service", "Decision service", "rules in process")
b.node("ast", 1010, 300, 200, 130, "data", "Auth store", "balances · holds · messages", since=2, shape="db")
b.node("led", 1340, 300, 200, 130, "data", "Core ledger", "posted money", shape="db")
b.node("ana", 20, 60, 200, 110, "client", "Analysts", "fraud operations", since=2)
b.node("rules", 350, 60, 200, 110, "service", "Rule service", "versioned rules", since=2)
b.node("model", 680, 60, 200, 110, "service", "Model scorer", "60 ms cut-off", since=2)
b.node("feat", 1010, 60, 200, 110, "cache", "Feature store", "burst counters", since=3)
b.node("agg", 1340, 60, 200, 110, "service", "Stream aggregator", "pattern features", since=3)
b.node("log", 680, 560, 200, 100, "queue", "Event log", "every decision", since=2, shape="queue")
b.node("cons", 350, 560, 200, 100, "service", "Alerts · cases", "archive · alarms", since=3)
b.node("match", 1340, 560, 200, 100, "service", "Clearing matcher", "daily files")
b.node("probe", 20, 560, 200, 100, "ext", "Probes", "test cards", tag="ch8")

REQ = dict(src="r:0.25", dst="l:0.25"); RSP = dict(src="l:0.75", dst="r:0.75", kind="resp")
b.edge("n-g", "net", "gw", "authorise", **REQ, at=(285, 322))
b.edge("g-n", "gw", "net", "approve", **RSP, at=(285, 420))
b.edge("g-d", "gw", "dec", "decide", **REQ, at=(615, 322))
b.edge("d-g", "dec", "gw", "answer", **RSP, at=(615, 420))
# V1: the decision reads and writes the core ledger directly
b.edge("d-l1", "dec", "led", "read balance, insert hold", until=1, **REQ, at=(1110, 322))
b.edge("l-d1", "led", "dec", "ok", until=1, **RSP, at=(1110, 420))
b.edge("m-l", "match", "led", "post real amount", src="t:0.5", dst="b:0.5", at=(1440, 495))
# V2: split the decision from the ledger
b.edge("d-a", "dec", "ast", "reserve", since=2, **REQ, at=(945, 322))
b.edge("a-d", "ast", "dec", "ok", since=2, **RSP, at=(945, 420))
b.edge("d-m", "dec", "model", "score", src="t:0.45", dst="b:0.45", since=2, at=(738, 236))
b.edge("m-d", "model", "dec", "risk", src="b:0.8", dst="t:0.8", kind="resp", since=2, at=(850, 236))
b.edge("a-r", "ana", "rules", "rule v15", src="r:0.5", dst="l:0.5", since=2, at=(285, 92))
b.edge("r-d", "rules", "dec", "push version", src="b:0.5", dst="t:0.1", via=[(450, 262), (700, 262)], since=2, at=(560, 250))
b.edge("d-lg", "dec", "log", "outbox", src="b:0.5", dst="t:0.5", kind="async", since=2, at=(830, 500))
b.edge("l-a", "led", "ast", "posted", src="l:0.5", dst="r:0.5", kind="async", since=2, at=(1275, 352))
b.edge("mt-a", "match", "ast", "post + release", src="l:0.5", dst="b:0.5", via=[(1110, 610)], since=2, at=(1200, 520))
# V3: features, consumers
b.edge("d-f", "dec", "feat", "count, read", src="t:0.95", dst="b:0.1", via=[(870, 250), (1030, 250)], since=3, at=(955, 238))
b.edge("ag-f", "agg", "feat", "patterns", src="l:0.5", dst="r:0.5", kind="async", since=3, at=(1275, 92))
b.edge("lg-ag", "log", "agg", "stream", src="b:0.5", dst="r:0.5", via=[(780, 705), (1585, 705), (1585, 115)], kind="async", since=3, at=(1180, 694))
b.edge("lg-c", "log", "cons", "events", src="l:0.5", dst="r:0.5", kind="async", since=3, at=(615, 588))
b.edge("p-n", "probe", "net", "test auths", src="t:0.5", dst="b:0.5", tag="ch8", at=(170, 500))

def sv(name, h, **view):
    b.h = h
    b.save(OUT / name, **view)

ALL = ["ch8"]
sv("base-v1.svg", 470, upto=1, legend=True)
sv("base-v2.svg", 760, upto=2, new=2, legend=True)
sv("base-v3.svg", 760, upto=3, new=3, legend=True)
sv("base-final.svg", 760, upto=3, show=ALL, legend=True)
sv("map.svg", 760, upto=3, show=ALL, legend=True, attack=["ast", "model", "feat", "rules", "gw", "match", "cons"], keep=None)
sv("flow-fr1.svg", 760, upto=3, flow=["n-g", "g-d", "d-f", "d-m", "d-a", "d-lg", "d-g", "g-n"],
   keep=["net", "gw", "dec", "feat", "model", "ast", "log"])
sv("flow-fr2.svg", 760, upto=3, flow=["n-g", "g-d", "d-a", "d-lg", "g-n"], keep=["net", "gw", "dec", "ast", "log"])
sv("flow-fr3.svg", 800, upto=3, flow=["mt-a", "m-l", "l-a"], keep=["match", "ast", "led"],
   notes=[(40, 728, 1100, "Before step 1: load the day's file; skip record IDs already seen.", "blue")])
sv("flow-fr4.svg", 760, upto=3, flow=["a-r", "r-d", "d-lg", "lg-c"], keep=["ana", "rules", "dec", "log", "cons"])
# challenge overlays
sv("ch1-attack.svg", 540, upto=1, attack=["dec"], keep=["net", "gw", "dec", "led"], hot=["d-l1"],
   notes=[(40, 470, 1100, "Debit $60 at the till; clearing says $72 three days later.", "red")])
sv("ch1-fix.svg", 800, upto=3, fix=["ast", "match"], keep=["dec", "ast", "led", "match"], ok=["d-a", "mt-a", "m-l"],
   notes=[(40, 728, 1100, "Hold $60 → $72; clearing posts $72 and releases it.", "green")])
sv("ch2-attack.svg", 540, upto=2, attack=["ast"], keep=["gw", "dec", "ast"], hot=["d-a", "a-d"],
   notes=[(40, 470, 1100, "Two reads of $100 two ms apart; both holds land: −$40.", "red")])
sv("ch2-fix.svg", 540, upto=2, fix=["ast"], keep=["gw", "dec", "ast"], ok=["d-a", "a-d"],
   notes=[(40, 470, 1100, "One conditional write in the account's partition: check, hold, message.", "green")])
sv("ch3-attack.svg", 540, upto=2, attack=["gw", "ast"], keep=["net", "gw", "dec", "ast"], hot=["n-g", "g-d"],
   notes=[(40, 470, 1100, "A retry places a second hold; a reversal before its original is lost.", "red")])
sv("ch3-fix.svg", 540, upto=2, fix=["ast"], keep=["net", "gw", "dec", "ast"], ok=["d-a", "a-d"],
   notes=[(40, 470, 1100, "Keyed by network reference, written with the hold; early reversals wait.", "green")])
sv("ch4-attack.svg", 540, upto=3, attack=["model"], keep=["net", "gw", "dec", "model"], hot=["d-m", "m-d"],
   notes=[(40, 470, 1100, "Model p99 1.8 s: wait, and the network stands in for us.", "red")])
sv("ch4-fix.svg", 540, upto=3, fix=["dec"], keep=["net", "gw", "dec", "model"], ok=["d-g", "g-n"],
   notes=[(40, 470, 1100, "60 ms cut-off; a fail-policy table decides; an exposure cap.", "green")])
sv("ch5-attack.svg", 540, upto=3, attack=["agg", "feat"], keep=["dec", "feat", "agg"], hot=["ag-f"],
   notes=[(40, 470, 1100, "Counters from the stream lag 5–8 s; four swipes in 8 s read 0, 1, 1, 2.", "red")])
sv("ch5-fix.svg", 540, upto=3, fix=["feat"], keep=["dec", "feat", "agg"], ok=["d-f"],
   notes=[(40, 470, 1100, "Burst counters read and incremented inline; patterns from the stream.", "green")])
sv("ch6-attack.svg", 540, upto=2, attack=["rules"], keep=["ana", "rules", "dec"], hot=["r-d"],
   notes=[(40, 470, 1100, "A hotfix takes 50 minutes; a rule pushed live declines 9 % of good buyers.", "red")])
sv("ch6-fix.svg", 800, upto=3, fix=["rules", "cons"], keep=["ana", "rules", "dec", "log", "cons"], ok=["a-r", "r-d", "d-lg", "lg-c"],
   notes=[(40, 728, 1100, "Backtest → shadow → slice → enforce; version on every decision.", "green")])
sv("ch7-attack.svg", 540, upto=3, attack=["gw", "dec", "ast"], keep=["net", "gw", "dec", "ast"], hot=["n-g"],
   notes=[(40, 470, 1100, "Down 20 min: 360,000 stand-in approvals; a no-negative check refuses advices.", "red")])
sv("ch7-fix.svg", 800, upto=3, fix=["ast", "match"], keep=["net", "gw", "dec", "ast", "led", "match"], ok=["n-g", "g-d", "d-a", "mt-a", "m-l"],
   notes=[(40, 728, 1100, "Record every advice once, even over the balance.", "green")])
sv("ch8-attack.svg", 800, upto=3, attack=["rules", "dec"], keep=["rules", "dec", "log", "cons"], hot=["r-d"],
   notes=[(40, 728, 1100, "Rule set v212: grocery approvals 96 % → 71 %; no errors.", "red")])
sv("ch8-fix.svg", 800, upto=3, show=["ch8"], fix=["cons", "probe"], keep=["probe", "net", "gw", "dec", "log", "cons"], ok=["p-n", "lg-c"],
   notes=[(40, 728, 1100, "Watch decisions: approval rate by merchant type.", "green")])
bs.budget_bar(OUT / "budget.svg", [("checks", 23, "data"),
                                   ("model (cut-off)", 60, "service"), ("hold + reply", 15, "edge")],
              total=300, unit="ms", title="One authorisation, worst case at the cut-off (initial target p99 300 ms at our gateway)")

# ───────────────────────────── 2 · C4 ────────────────────────────────────────────────────────────────
d = c4.Diagram(1600, 840)
d.node("ch", 60, 90, 300, 150, "person", "Cardholder", "Person", "Pays at a till or online; gets alerts.")
d.node("mer", 60, 540, 300, 150, "ext", "Merchant + acquirer", "External system", "Sends the purchase to the network.")
d.node("netp", 620, 540, 360, 150, "ext", "Card network + processor", "External system", "Routes the request; stands in if we are late.")
d.node("sys", 620, 250, 360, 190, "system", "Issuer authorisation", "Software System", "Decides, holds, clears, rules.")
d.node("fo", 1230, 90, 320, 150, "person", "Fraud operations", "Person", "Write rules; contact customers.")
d.node("cb", 1230, 540, 320, 150, "ext", "Core banking ledger", "Internal system", "Posted balances; statements.")
d.edge("ch", "mer", "pays", "card, wallet", src="b:0.5", dst="t:0.5", at=(225, 395))
d.edge("mer", "netp", "purchase", "acquirer link", src="r:0.5", dst="l:0.5", at=(490, 600))
d.edge("netp", "sys", "authorise, advise, clearing file", "ISO 8583, files", src="t:0.5", dst="b:0.5", at=(800, 495))
d.edge("sys", "ch", "alerts", "push, text", src="l:0.3", dst="r:0.6", at=(470, 220))
d.edge("fo", "sys", "rules, cases", "console", src="l:0.5", dst="r:0.3", at=(1100, 170))
d.edge("sys", "cb", "postings", "events", src="r:0.7", dst="t:0.5", via=[(1390, 383)], at=(1250, 370))
d.legend(40, 800, ("person", "system", "ext"))
d.save(OUT / "c4-context.svg")

d = c4.Diagram(1600, 950)
d.boundary(330, 50, 1240, 820, "Issuer authorisation", "Software System")
d.node("np", 30, 330, 270, 160, "ext", "Network + processor", "External", "Requests, advices, files.")
d.node("cl", 30, 640, 270, 160, "ext", "Core ledger", "Internal", "Posted money.")
d.node("gwc", 360, 330, 260, 160, "container", "Auth gateway", "Service", "Maps messages; mutual TLS to the processor.", size=21)
d.node("dc", 660, 330, 260, 160, "container", "Decision service", "Stateless service", "Rules in process; budget; fail table.", size=21)
d.node("as", 960, 330, 260, 160, "db", "Auth store", "Partitioned by account", "Balances, holds, messages.", size=21)
d.node("ms", 660, 90, 260, 150, "container", "Model scorer", "Service", "Scores under a cut-off.", size=21)
d.node("fs", 960, 90, 260, 150, "db", "Feature store", "In-memory", "Burst counters, aggregates.", size=21)
d.node("rs", 1260, 90, 280, 150, "container", "Rule service", "Service", "Versions, backtest, shadow.", size=21)
d.node("cm", 360, 640, 260, 160, "container", "Clearing matcher", "Batch service", "Match, post, release, expire.", size=21)
d.node("el", 660, 640, 260, 160, "queue", "Event log", "Partitioned log", "Every decision, via outbox.", size=21)
d.node("cs", 960, 640, 260, 160, "container", "Alerts and cases", "Consumers", "Texts, cases, archive.", size=21)
d.edge("np", "gwc", "ISO 8583", "TLS", src="r", dst="l", at=(330, 310))
d.edge("gwc", "dc", "decide", "", src="r", dst="l", at=(640, 310))
d.edge("dc", "as", "reserve", "", src="r", dst="l", at=(940, 310))
d.edge("dc", "ms", "score", "", src="t", dst="b", at=(745, 285))
d.edge("dc", "fs", "counters", "", src="t:0.9", dst="b:0.2", at=(930, 270))
d.edge("rs", "dc", "rule set", "push", src="b:0.3", dst="t:0.97", at=(1290, 285))
d.edge("dc", "el", "outbox", "async", src="b", dst="t", at=(780, 605))
d.edge("cm", "as", "release", "", src="t:0.5", dst="b:0.5", via=[(490, 530), (1090, 530)], at=(560, 518))
d.edge("el", "cs", "events", "async", src="r", dst="l", at=(940, 700))
d.edge("cm", "cl", "postings", "", src="l", dst="r", at=(330, 700))
d.legend(40, 915, ("person", "container", "db", "ext"))
d.save(OUT / "c4-containers.svg")

# the same container view with the technologies (labels from ../stack.json)
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent / 'src')); import stack
c4.Diagram.OVERRIDE = {k: (v[1], v[2]) for k, v in stack.C4.items()}
d = c4.Diagram(1600, 950)
d.boundary(330, 50, 1240, 820, "Issuer authorisation", "Software System")
d.node("np", 30, 330, 270, 160, "ext", "Network + processor", "External", "Requests, advices, files.")
d.node("cl", 30, 640, 270, 160, "ext", "Core ledger", "Internal", "Posted money.")
d.node("gwc", 360, 330, 260, 160, "container", "Auth gateway", "Service", "Maps messages; mutual TLS to the processor.", size=21)
d.node("dc", 660, 330, 260, 160, "container", "Decision service", "Stateless service", "Rules in process; budget; fail table.", size=21)
d.node("as", 960, 330, 260, 160, "db", "Auth store", "Partitioned by account", "Balances, holds, messages.", size=21)
d.node("ms", 660, 90, 260, 150, "container", "Model scorer", "Service", "Scores under a cut-off.", size=21)
d.node("fs", 960, 90, 260, 150, "db", "Feature store", "In-memory", "Burst counters, aggregates.", size=21)
d.node("rs", 1260, 90, 280, 150, "container", "Rule service", "Service", "Versions, backtest, shadow.", size=21)
d.node("cm", 360, 640, 260, 160, "container", "Clearing matcher", "Batch service", "Match, post, release, expire.", size=21)
d.node("el", 660, 640, 260, 160, "queue", "Event log", "Partitioned log", "Every decision, via outbox.", size=21)
d.node("cs", 960, 640, 260, 160, "container", "Alerts and cases", "Consumers", "Texts, cases, archive.", size=21)
d.edge("np", "gwc", "ISO 8583", "TLS", src="r", dst="l", at=(330, 310))
d.edge("gwc", "dc", "decide", "", src="r", dst="l", at=(640, 310))
d.edge("dc", "as", "reserve", "", src="r", dst="l", at=(940, 310))
d.edge("dc", "ms", "score", "", src="t", dst="b", at=(745, 285))
d.edge("dc", "fs", "counters", "", src="t:0.9", dst="b:0.2", at=(930, 270))
d.edge("rs", "dc", "rule set", "push", src="b:0.3", dst="t:0.97", at=(1290, 285))
d.edge("dc", "el", "outbox", "async", src="b", dst="t", at=(780, 605))
d.edge("cm", "as", "release", "", src="t:0.5", dst="b:0.5", via=[(490, 530), (1090, 530)], at=(560, 518))
d.edge("el", "cs", "events", "async", src="r", dst="l", at=(940, 700))
d.edge("cm", "cl", "postings", "", src="l", dst="r", at=(330, 700))
d.legend(40, 915, ("person", "container", "db", "ext"))
d.save(OUT / "c4-containers-tech.svg")
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

seq("seq-authorise",
    [("nw", "Network", "ext"), ("gw", "Auth gateway", "container"), ("dc", "Decision service", "container"), ("fs", "Feature store", "db"),
     ("ms", "Model scorer", "container"), ("as", "Auth store", "db")],
    [("m", "nw", "gw", "authorise R-4410 · $60 · restaurant"),
     ("m", "gw", "dc", "decide"),
     ("m", "dc", "fs", "count this swipe; read 10 min (1 ms)"),
     ("m", "dc", "ms", "score, cut-off 60 ms", dict(kind="async")),
     ("n", "dc", "dc", "rules in process, in parallel (10 ms)", "blue"),
     ("r", "ms", "dc", "risk 0.04 (38 ms)"),
     ("m", "dc", "as", "reserve: hold $60 if available, record R-4410"),
     ("r", "as", "dc", "ok · available $440"),
     ("n", "dc", "dc", "decision + inputs + versions → outbox", "green"),
     ("r", "gw", "nw", "approve · 91 ms", dict(hl=True))])

seq("seq-reversal",
    [("nw", "Network", "ext"), ("dc", "Decision service", "container"), ("as", "Auth store", "db")],
    [("m", "nw", "dc", "reversal of R-8840 (original not seen yet)"),
     ("m", "dc", "as", "message R-8840: none → store tombstone 'reversed'"),
     ("r", "dc", "nw", "ack"),
     ("m", "nw", "dc", "authorise R-8840 · $45 (60 ms later)"),
     ("m", "dc", "as", "reserve R-8840?"),
     ("r", "as", "dc", "already reversed: no hold"),
     ("r", "dc", "nw", "approve, as the network expects; nothing held", dict(hl=True)),
     ("m", "nw", "dc", "retry of R-8840"),
     ("r", "dc", "nw", "the stored answer, again", dict(hl=False))])

seq("seq-clearing",
    [("nf", "Network file", "ext"), ("cm", "Clearing matcher", "container"), ("as", "Auth store", "db"), ("cl", "Core ledger", "db")],
    [("m", "nf", "cm", "file F-1121: 10 M records (record IDs, refs)"),
     ("n", "cm", "cm", "skip record IDs already seen", "blue"),
     ("m", "cm", "as", "find hold for R-4410"),
     ("r", "as", "cm", "hold $72 (after the tip)"),
     ("m", "cm", "as", "one write: posted −$72, release hold"),
     ("r", "as", "cm", "available unchanged ($428)"),
     ("m", "cm", "cl", "post $72 · record C-9001"),
     ("n", "cm", "cm", "no ref? match card + merchant + amount ±20 % + 7 days", "amber"),
     ("n", "cm", "cm", "unmatched clearing still posts → review queue", "amber")])

seq("seq-ch2-reserve",
    [("a", "Auth for $80", "container"), ("as", "Account A-12 partition", "db"), ("b", "Auth for $60", "container")],
    [("m", "a", "as", "reserve 80 if holds + 80 ≤ posted, version 41"),
     ("m", "b", "as", "reserve 60 if holds + 60 ≤ posted, version 41"),
     ("r", "as", "a", "ok: hold placed, version 42", dict(hl=True)),
     ("r", "as", "b", "conflict: version is 42"),
     ("m", "b", "as", "re-read: available $20; 60 > 20"),
     ("n", "b", "b", "decline: insufficient funds", "red")])

seq("seq-ch4-cutoff",
    [("dc", "Decision service", "container"), ("ms", "Model scorer", "container"), ("fp", "Fail-policy table", "db")],
    [("m", "dc", "ms", "score (cut-off 60 ms)", dict(kind="async")),
     ("n", "dc", "dc", "rules done at 18 ms", "blue"),
     ("n", "dc", "dc", "60 ms: no score → proceed without it", "amber"),
     ("m", "dc", "fp", "row: model late · $60 · restaurant"),
     ("r", "fp", "dc", "rules only; cap $50k/h; used $7.2k"),
     ("n", "dc", "dc", "approve, flagged degraded; counted against the cap", "green"),
     ("r", "ms", "dc", "score at 1.8 s: logged, ignored")])

seq("seq-ch6-rollout",
    [("an", "Analyst", "person"), ("rs", "Rule service", "container"), ("dc", "Decision services", "container"), ("al", "Alarms", "container")],
    [("m", "an", "rs", "rule v15: $1 test then > $300 electronics"),
     ("n", "rs", "rs", "backtest 90 days: catches 71 % of the ring; declines 0.2 % of good", "blue"),
     ("m", "rs", "dc", "push rule set 213, v15 in shadow"),
     ("n", "dc", "dc", "would-decline logged with version 213", "blue"),
     ("m", "an", "rs", "promote: enforce on 5 %"),
     ("m", "dc", "al", "decline rate by merchant type, per minute"),
     ("m", "an", "rs", "enforce 100 %, expiry in 14 days"),
     ("n", "rs", "rs", "rollback = re-point to 212, seconds", "green")])

seq("seq-ch7-advices",
    [("nw", "Network", "ext"), ("dc", "Decision service", "container"), ("as", "Auth store", "db"), ("cl", "Core ledger", "db")],
    [("n", "nw", "nw", "02:00–02:20 stand-in: 360,000 approvals", "amber"),
     ("m", "nw", "dc", "advice R-5102 · $80 · approved by stand-in"),
     ("m", "dc", "as", "record R-5102 as a hold, even past available"),
     ("r", "as", "dc", "A-19 available −$105 → state over-limit"),
     ("r", "dc", "nw", "ack"),
     ("m", "dc", "cl", "event: over-limit A-19", dict(kind="async")),
     ("n", "dc", "dc", "new auths on A-19 decline until it is paid back", "green")])

# ───────────────────────────── 4 · data models ───────────────────────────────────────────────────────
c = er.Chen(1600, 900, size=26)
c.entity("a", 200, 140, "ACCOUNT"); c.entity("cd", 200, 620, "CARD"); c.entity("h", 760, 140, "HOLD")
c.entity("m", 760, 620, "MESSAGE"); c.entity("cr", 1300, 140, "CLEARING RECORD"); c.entity("dn", 1300, 620, "DECISION", weak=True)
c.rel("hs", 480, 140, "RESERVES"); c.rel("ow", 200, 380, "HAS"); c.rel("cr2", 760, 380, "CREATES"); c.rel("mt", 1030, 140, "SETTLES")
c.rel("rec", 1030, 620, "RECORDED AS", identifying=True)
c.attr("aid", 120, 50, "account_id", of="a", key=True); c.attr("pb", 320, 50, "posted", of="a"); c.attr("st", 60, 230, "state", of="a")
c.attr("tok", 70, 720, "token", of="cd", key=True); c.attr("cs", 330, 720, "status", of="cd")
c.attr("hid", 700, 50, "hold_id", of="h", key=True); c.attr("amt", 900, 50, "amount", of="h"); c.attr("exp", 900, 230, "expires_at", of="h")
c.attr("ref", 640, 720, "network_ref", of="m", key=True); c.attr("ty", 880, 720, "type", of="m")
c.attr("rid", 1240, 50, "record_id", of="cr", key=True); c.attr("ca", 1460, 230, "amount", of="cr")
c.attr("rv", 1420, 760, "rule version", of="dn"); c.attr("ft", 1200, 720, "features", of="dn")
c.link("a", "hs", "1"); c.link("hs", "h", "N")
c.link("a", "ow", "1", src="b", dst="t"); c.link("ow", "cd", "N", src="b", dst="t")
c.link("m", "cr2", "N", src="t", dst="b"); c.link("cr2", "h", "1", src="t", dst="b")
c.link("h", "mt", "1"); c.link("mt", "cr", "N")
c.link("m", "rec", "1"); c.link("rec", "dn", "1", total=True)
c.legend(40, 800)
c.note(330, 800, 1240, "One hold, many messages (auth, incremental, reversal); usually one clearing record, sometimes several or none.")
c.save(OUT / "erd-chen.svg")

e = er.ERD(1600, 860, size=22)
e.entity("acct", 30, 40, 470, "account", [("account_id", "bigint", "PK"), ("posted_balance", "cents", ""), ("holds_total", "cents", ""),
         ("version", "int", ""), ("state", "text", "")], kind="focus", caption="auth store; partitioned by account_id")
e.entity("hold", 560, 40, 480, "hold", [("account_id", "bigint", "PK"), ("hold_id", "bigint", "PK"), ("network_ref", "text", "UQ"),
         ("amount", "cents", ""), ("mcc", "char(4)", ""), ("expires_at", "ts", ""), ("state", "text", "")], kind="focus", caption="same partition as its account")
e.entity("msg", 1100, 40, 470, "message", [("network_ref", "text", "PK"), ("account_id", "bigint", ""), ("type", "text", ""),
         ("result", "text", ""), ("at", "ts", "")], kind="focus", caption="idempotency; kept past the retry window")
e.entity("card", 30, 470, 470, "card", [("token", "text", "PK"), ("account_id", "bigint", "IX"), ("status", "text", ""), ("limits", "json", "")],
         caption="tokens only: the processor holds card numbers")
e.entity("clr", 560, 470, 480, "clearing_record", [("record_id", "text", "PK"), ("file_id", "text", "IX"), ("network_ref", "text", "IX"),
         ("amount", "cents", ""), ("hold_id", "bigint", "")], caption="the financial truth")
e.entity("rs", 1100, 470, 470, "ruleset", [("version", "int", "PK"), ("parent", "int", ""), ("rules", "json", ""), ("mode", "text", ""),
         ("owner", "text", "")], kind="ext", caption="read by every decision service")
e.rel("hold", "acct", "N", "1", src="l:0.3", dst="r:0.3", label="", at=(530, 90))
e.note(30, 760, 1540, "The reserve writes account, hold and message in one transaction, in one partition.")
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
FILL = {BLUE: "#dbeafe", AMBER: "#fdf3e1", GREEN: "#d3f3e6", RED: "#fdecea", PURPLE: "#e6dcfb", GREY: "#eceff2"}

def tension():
    p = [T(40, 44, "Decision quality against the deadline: every signal costs milliseconds", 28, INK, 800)]
    x0, x1, y0, y1 = 120, 1500, 420, 90
    p += [L(x0, y0, x1, y0, GREY, 2.5), L(x0, y0, x0, y1, GREY, 2.5), T(x1, y0 + 40, "time to answer →", 22, "#57606a", 600, "end"),
          T(x0 - 14, y1 + 10, "quality", 22, "#57606a", 600, "end")]
    pts = [(0, 330), (10, 250), (60, 165), (120, 140), (300, 128), (2000, 120)]
    X = lambda ms: x0 + (ms ** 0.5) / (2000 ** 0.5) * (x1 - x0) * 0.82
    path = " ".join(f"{'M' if i == 0 else 'L'}{X(ms):.1f},{y:.1f}" for i, (ms, y) in enumerate(pts))
    p.append(f'<path d="{path}" fill="none" stroke="{BLUE}" stroke-width="4"/>')
    for ms, lab in ((10, "rules"), (60, "+ model"), (120, "+ aggregates")):
        y = dict(pts)[ms]
        p += [f'<circle cx="{X(ms):.1f}" cy="{y}" r="8" fill="{BLUE}"/>', T(X(ms) + 16, y + 34, lab, 21, BLUE, 700)]
    for ms, lab, col in ((300, "our target 300 ms", GREEN), (2000, "network deadline ≈ 2 s", RED)):
        p += [L(X(ms), y1 - 10, X(ms), y0, col, 3, True), T(X(ms), y0 + 70, lab, 22, col, 800, "middle")]
    p += [R(X(2000) + 20, 160, 150, 120, FILL[RED], RED, rx=10), T(X(2000) + 95, 210, "stand-in:", 21, RED, 800, "middle"),
          T(X(2000) + 95, 245, "they decide", 21, RED, 700, "middle")]
    p += [T(40, 545, "Past the target the gain is small; past the deadline the network decides with far less information.", 23, "#173d24", 700)]
    (OUT / "tension.svg").write_text(svgdoc(1600, 580, "".join(p)))
tension()

def path_of_swipe():
    p = [T(40, 44, "The path of a swipe: who is in the chain, and who decides when we are late", 28, INK, 800)]
    hops = [("Till", "card, wallet", BLUE), ("Acquirer", "merchant's bank", GREY), ("Card network", "routes, times out ≈ 2 s", GREY),
            ("Processor", "card vault, link", GREY), ("Us: issuer", "decide in 300 ms", PURPLE)]
    for i, (n, s, col) in enumerate(hops):
        x = 40 + i * 312
        p += [R(x, 110, 270, 120, FILL[col], col, rx=12), T(x + 135, 160, n, 25, INK, 800, "middle"), T(x + 135, 198, s, 20, INK, 600, "middle")]
        if i: p.append(L(x - 40, 170, x - 4, 170, INK, 3))
    p += [R(664, 290, 560, 90, FILL[RED], RED, rx=10), T(944, 330, "We are late or down: the network stands in", 22, RED, 800, "middle"),
          T(944, 362, "within our pre-set limits, then sends us an advice", 20, "#5a1308", 600, "middle")]
    p += [R(40, 430, 1520, 90, FILL[GREEN], GREEN, rx=10), T(800, 470, "Days later, by file: clearing with the real amount, then settlement between banks", 23, "#173d24", 800, "middle"),
          T(800, 502, "The money does not move at the till. It moves on the clearing file.", 20, "#173d24", 600, "middle")]
    (OUT / "swipe-path.svg").write_text(svgdoc(1600, 550, "".join(p)))
path_of_swipe()

def holds():
    p = [T(40, 44, "One restaurant bill: a hold, not a debit", 28, INK, 800)]
    ev = [("Mon 20:14", "authorise $60", "hold 60", "500", "440"), ("Mon 20:16", "incremental + $12 (tip)", "hold 72", "500", "428"),
          ("Thu 06:00", "clearing $72, matched by reference", "post 72; release hold", "428", "428")]
    p += [T(60, 110, "when", 21, "#57606a", 700), T(260, 110, "message", 21, "#57606a", 700), T(760, 110, "effect", 21, "#57606a", 700),
          T(1170, 110, "posted", 21, "#57606a", 700), T(1370, 110, "available", 21, "#57606a", 700)]
    for i, (t, m, ef, pb, av) in enumerate(ev):
        y = 140 + i * 100
        col = GREEN if i == 2 else BLUE
        p += [R(40, y, 1520, 80, FILL[col], col, rx=10), T(60, y + 50, t, 23, INK, 800), T(260, y + 50, m, 23, INK, 600),
              T(760, y + 50, ef, 23, col, 800), T(1170, y + 50, "$" + pb, 23, INK, 700), T(1370, y + 50, "$" + av, 23, INK, 800)]
    p += [T(40, 480, "available = posted − active holds.   If Thursday never comes: the hold expires (7 days; 30 for hotels and car hire).", 22, "#173d24", 700)]
    (OUT / "holds.svg").write_text(svgdoc(1600, 510, "".join(p)))
holds()

def features():
    p = [T(40, 44, "Two kinds of features: exact now, or richer and seconds late", 28, INK, 800)]
    p += [R(40, 90, 740, 360, FILL[GREEN], GREEN, rx=14), T(410, 135, "Inline, on the request path", 25, "#173d24", 800, "middle")]
    for i, s in enumerate(["swipes on this card, last 10 min", "card-not-present amount, last hour", "declines on this card, last hour",
                           "read and increment: one round trip, ~1 ms"]):
        p.append(T(70, 190 + i * 55, ("• " if i < 3 else "→ ") + s, 22, INK, 600 if i < 3 else 800))
    p += [R(820, 90, 740, 360, FILL[PURPLE], PURPLE, rx=14), T(1190, 135, "From the stream, seconds late", 25, "#2a1d66", 800, "middle")]
    for i, s in enumerate(["distinct merchants for this card, today", "merchant's decline rate, last hour", "device seen on other cards, 30 days",
                           "computed off the path; read in the same call"]):
        p.append(T(850, 190 + i * 55, ("• " if i < 3 else "→ ") + s, 22, INK, 600 if i < 3 else 800))
    p += [T(40, 500, "A burst of fraud is seconds apart; a stream lags by seconds. Log every value with the decision: train on what the model saw.", 22, "#173d24", 700)]
    (OUT / "features.svg").write_text(svgdoc(1600, 530, "".join(p)))
features()

def rule_life():
    p = [T(40, 44, "A rule's lifecycle: fast, measured, and undoable", 28, INK, 800)]
    st = [("Write", "an expression, an owner, an expiry", BLUE), ("Backtest", "90 days of the archive, with labels", BLUE),
          ("Shadow", "live, logged, not enforced", AMBER), ("Slice", "5 %, decline-rate alarm", AMBER), ("Enforce", "everywhere, kill switch", GREEN)]
    for i, (n, s, col) in enumerate(st):
        x = 40 + i * 312
        p += [R(x, 100, 280, 150, FILL[col], col, rx=12), T(x + 140, 160, n, 26, INK, 800, "middle"), T(x + 140, 200, s.split(",")[0], 19, INK, 600, "middle"),
              T(x + 140, 228, s.split(",")[1].strip() if "," in s else "", 19, INK, 600, "middle")]
        if i: p.append(L(x - 32, 175, x - 4, 175, INK, 3))
    p += [R(40, 300, 1520, 80, "#f6f8fa", GREY, rx=10), T(800, 350, "Every decision records the rule-set version. Rollback = re-point to the previous version: seconds, no deploy.", 22, INK, 700, "middle")]
    p += [R(40, 410, 1520, 80, FILL[RED], RED, rx=10), T(800, 460, "Shadow shows how many it would decline, not which were fraud: labels arrive in 30–90 days.", 22, "#5a1308", 800, "middle")]
    (OUT / "rule-life.svg").write_text(svgdoc(1600, 520, "".join(p)))
rule_life()

def escrow():
    p = [T(40, 44, "A shared business account: sub-limits carved per card", 28, INK, 800)]
    p += [R(40, 100, 420, 150, FILL[GREEN], GREEN, rx=14), T(250, 160, "Account B-7", 26, INK, 800, "middle"), T(250, 200, "posted $200,000", 22, "#173d24", 700, "middle")]
    for i, (n, s) in enumerate((("card 1 slice", "$400 left"), ("card 2 slice", "$150 left"), ("card 2,000 slice", "$0: refill"))):
        y = 80 + i * 110
        col = RED if i == 2 else BLUE
        p += [L(462, 175, 740, y + 45, GREY, 2.5), R(740, y, 360, 90, FILL[col], col, rx=10), T(920, y + 40, n, 23, INK, 800, "middle"), T(920, y + 72, s, 20, col, 700, "middle")]
    p += [R(1160, 120, 400, 210, "#f6f8fa", GREY, rx=12), T(1360, 170, "Most auths touch only", 21, INK, 700, "middle"), T(1360, 200, "the card's slice", 21, INK, 700, "middle"),
          T(1360, 250, "refills move budget", 21, INK, 600, "middle"), T(1360, 280, "from the account, async", 21, INK, 600, "middle")]
    p += [T(40, 410, "2,000 cards × 1 auth per 10 min ≈ 3.3/s on one key: fine for one partition. Slices matter at hundreds a second.", 22, "#173d24", 700)]
    (OUT / "escrow.svg").write_text(svgdoc(1600, 440, "".join(p)))
escrow()

print(sorted(p.name for p in OUT.glob("*.svg")))
