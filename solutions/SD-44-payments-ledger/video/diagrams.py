#!/usr/bin/env python3
"""C4, state, sequence and follow-up diagrams for the SD-44 payments-ledger video → ./svg/*.svg.
Generators: ~/.claude/skills/slide-video-kit/scripts/{c4svg,seqsvg}.py.  Run: python3 diagrams.py
Content follows ../../SD-44-payments-ledger.md; the follow-up diagrams (fu-*) are new for this video."""
import pathlib, sys
sys.path.insert(0, str(pathlib.Path.home() / ".claude/skills/slide-video-kit/scripts"))
import c4svg as c4, seqsvg as sq

OUT = pathlib.Path(__file__).resolve().parent / "svg"
OUT.mkdir(exist_ok=True)
GREEN, GREEN_BG, RED, RED_BG, BLUE, BLUE_BG = "#2d8a4e", "#e7f4ec", "#c8341f", "#fdecea", "#2f6fb5", "#e8f0fa"

def seq(size=22, row=50):
    return sq.Seq(1500, size=size, row=row, head=66)

def row_of(name, items, note=None, tone=(BLUE, BLUE_BG), arrows=False, focus=None, h=560):
    d = c4.Diagram(1600, h)
    n = len(items); w = (1520 - (n - 1) * 40) // n
    for i, (t, ty, desc) in enumerate(items):
        k = "focus" if (i == focus or (isinstance(focus, tuple) and i in focus)) else "container"
        d.node(f"n{i}", 40 + i * (w + 40), 70, w, 240, k, t, ty, desc, size=25 if n > 3 else 27)
    if arrows:
        for i in range(n - 1):
            d.edge(f"n{i}", f"n{i+1}", "", src="r", dst="l", dashed=False)
    if note:
        d.note(40, 370, 1520, note, size=21, colour=tone[0], bg=tone[1])
    d.save(OUT / f"{name}.svg")

# ── C4 level 1: system context ───────────────────────────────────────────────────────────────────
d = c4.Diagram(1600, 780)
d.node("m", 40, 60, 330, 160, "person", "Merchants", "Person", "10 k payments a second at peak; 50 currencies")
d.node("fo", 40, 500, 330, 160, "person", "Finance operations", "Person", "reconciliation breaks, audit")
d.node("pay", 620, 250, 380, 220, "focus", "Payments and ledger", "Software System",
       "takes a payment, records it in a balanced, immutable journal")
d.node("proc", 1240, 40, 320, 160, "ext", "Processor / card network", "External System", "slow, ambiguous, sometimes down")
d.node("bank", 1240, 290, 320, 160, "ext", "Banks", "External System", "settlement files, days later")
d.node("fraud", 1240, 540, 320, 160, "ext", "Fraud scoring", "External System", "assumed; out of scope")
d.edge("m", "pay", "POST /payments", "Idempotency-Key", src="r:0.5", dst="l:0.25", at=(490, 150), width=170)
d.edge("fo", "pay", "breaks, reports", "", src="r:0.5", dst="l:0.8", at=(490, 560), width=150)
d.edge("pay", "proc", "authorise, capture", "our reference", src="r:0.15", dst="l:0.5", at=(1120, 120), width=170)
d.edge("bank", "pay", "settlement file", "", src="l:0.5", dst="r:0.5", at=(1120, 360), width=150)
d.edge("pay", "fraud", "score", "", src="r:0.85", dst="l:0.5", at=(1120, 610), width=60)
d.legend(40, 755, ("person", "focus", "ext"))
d.save(OUT / "c4-context.svg")

# ── C4 level 2: containers ───────────────────────────────────────────────────────────────────────
d = c4.Diagram(1600, 820)
d.boundary(250, 20, 1330, 780, "Payments and ledger")
d.node("m", 20, 90, 200, 140, "person", "Merchant", "")
d.node("api", 300, 80, 260, 160, "container", "Payments API", "Container", "idempotency keys, validation")
d.node("ps", 660, 80, 320, 160, "focus", "Payment service", "state machine", "one transaction per transition")
d.node("db", 660, 340, 320, 170, "db", "Payments DB + ledger", "relational, by account", "state, journal, outbox, idempotency")
d.node("ad", 1080, 80, 260, 160, "container", "Processor adapter", "per processor", "our reference on every call")
d.node("proc", 1400, 80, 170, 160, "ext", "Processor", "")
d.node("log", 300, 340, 260, 170, "queue", "Payment events", "via outbox relay", "at least once")
d.node("wh", 300, 600, 260, 150, "container", "Webhook sender", "signed, retried")
d.node("inq", 1080, 340, 260, 170, "container", "Inquiry job", "Container", "resolves UNKNOWN by reference")
d.node("rec", 660, 600, 320, 150, "container", "Reconciliation", "daily", "files vs expectations; breaks owned")
d.node("bank", 1400, 600, 170, 150, "ext", "Bank files", "")
d.edge("m", "api", "", src="r:0.5", dst="l:0.5")
d.edge("api", "ps", "", src="r:0.5", dst="l:0.5")
d.edge("ps", "db", "state + entries + outbox", "", src="b:0.5", dst="t:0.5", at=(820, 290), width=230)
d.edge("ps", "ad", "", src="r:0.5", dst="l:0.5")
d.edge("ad", "proc", "", src="r:0.5", dst="l:0.5")
d.edge("db", "log", "relay", "", src="l:0.5", dst="r:0.5", at=(610, 425), width=60)
d.edge("log", "wh", "", src="b:0.5", dst="t:0.5")
d.edge("inq", "ad", "status?", "", src="t:0.5", dst="b:0.5", at=(1210, 290), width=80)
d.edge("inq", "db", "", src="l:0.5", dst="r:0.5")
d.edge("rec", "db", "", src="t:0.5", dst="b:0.5")
d.edge("bank", "rec", "", src="l:0.5", dst="r:0.5")
d.save(OUT / "c4-containers.svg")

# ── C4 level 3: inside the payment service ───────────────────────────────────────────────────────
d = c4.Diagram(1600, 760)
d.boundary(240, 20, 1000, 720, "Payment service", "Container")
d.node("api", 20, 80, 190, 140, "container", "Payments API", "")
d.node("ig", 300, 70, 420, 150, "component", "Idempotency guard", "Component", "unique (client, key); hash the payload")
d.node("sm", 820, 70, 380, 150, "focus", "State machine", "Component", "allowed transitions only")
d.node("pb", 300, 300, 420, 150, "component", "Posting builder", "Component", "entries in integer minor units")
d.node("inv", 820, 300, 380, 150, "focus", "Invariant check", "Component", "Σ debits = Σ credits, per currency")
d.node("ob", 300, 520, 420, 150, "component", "Outbox writer", "Component", "the event, same transaction")
d.node("bp", 820, 520, 380, 150, "component", "Balance projector", "async", "derived balances, rebuildable")
d.node("db", 1340, 300, 230, 150, "db", "Ledger DB", "")
d.edge("api", "ig", "", src="r:0.5", dst="l:0.5")
d.edge("ig", "sm", "", src="r:0.5", dst="l:0.5")
d.edge("sm", "pb", "", src="b:0.3", dst="t:0.7", via=[(934, 260), (594, 260)])
d.edge("pb", "inv", "", src="r:0.5", dst="l:0.5")
d.edge("inv", "db", "one commit", "", src="r:0.5", dst="l:0.5", at=(1270, 355), width=110)
d.edge("pb", "ob", "", src="b:0.5", dst="t:0.5")
d.edge("db", "bp", "", src="b:0.5", dst="r:0.5", via=[(1455, 595)])
d.save(OUT / "c4-component-payment.svg")

# ── Payment state machine ────────────────────────────────────────────────────────────────────────
d = c4.Diagram(1600, 700)
def st(nid, x, y, label, kind="container", w=230):
    d.node(nid, x, y, w, 100, kind, label, "", "", size=21)
st("cr", 40, 60, "CREATED")
st("ap", 330, 60, "AUTH_PENDING")
st("au", 660, 60, "AUTHORIZED")
st("ca", 990, 60, "CAPTURED")
st("se", 1320, 60, "SETTLED")
st("un", 330, 300, "UNKNOWN", "focus")
st("de", 40, 300, "DECLINED", "ext")
st("vo", 660, 500, "VOIDED", "ext")
st("pr", 990, 300, "PARTIALLY_REFUNDED", w=260)
st("rf", 990, 520, "REFUNDED")
st("cb", 1320, 300, "CHARGEBACK", "ext")
for a, b in [("cr", "ap"), ("ap", "au"), ("au", "ca"), ("ca", "se")]:
    d.edge(a, b, "", src="r", dst="l", dashed=False)
d.edge("ap", "un", "timeout", "", src="b:0.5", dst="t:0.5", dashed=False, colour=RED, at=(445, 230), width=90)
d.edge("un", "au", "inquiry: approved", "", src="r:0.5", dst="b:0.3", via=[(729, 350)], dashed=False, at=(640, 440), width=170)
d.edge("un", "de", "not found", "", src="l:0.5", dst="r:0.5", dashed=False, at=(290, 440), width=90)
d.edge("ap", "de", "", src="b:0.15", dst="t:0.5", via=[(364, 220), (155, 220)], dashed=False)
d.edge("au", "vo", "void", "", src="b:0.8", dst="t:0.8", dashed=False, at=(880, 300), width=50)
d.edge("ca", "pr", "refund", "", src="b:0.5", dst="t:0.4", dashed=False, at=(1160, 230), width=70)
d.edge("pr", "rf", "", src="b:0.4", dst="t:0.4", dashed=False)
d.edge("se", "cb", "dispute", "", src="b:0.5", dst="t:0.5", dashed=False, at=(1470, 230), width=80)
d.note(40, 600, 560, "UNKNOWN is a real state: never failed, never succeeded, until the processor says.", size=20,
       colour=RED, bg=RED_BG)
d.save(OUT / "states.svg")

# ── Sequence: one successful payment ─────────────────────────────────────────────────────────────
s = seq()
for pid, lab, k in [("m", "Merchant", "person"), ("api", "Payments API", "container"), ("ps", "Payment service", "focus"),
                    ("db", "Ledger DB", "db"), ("ad", "Processor adapter", "container"), ("pr", "Processor", "ext")]:
    s.part(pid, lab, k)
s.msg("m", "api", "POST /payments, Idempotency-Key")
s.msg("api", "db", "insert idempotency row: processing")
s.msg("ps", "db", "CREATED → AUTH_PENDING, commit BEFORE the call", hl=True)
s.msg("ps", "ad", "authorise")
s.msg("ad", "pr", "with our reference")
s.ret("pr", "ps", "approved")
s.msg("ps", "db", "AUTHORIZED + entries + outbox + response: one txn", hl=True)
s.ret("api", "m", "201 authorized")
s.save(OUT / "seq-pay.svg")

# ── Sequence: the timeout ────────────────────────────────────────────────────────────────────────
s = seq()
for pid, lab, k in [("m", "Merchant", "person"), ("ps", "Payment service", "container"), ("rec", "Reconciliation", "container"),
                    ("pr", "Processor", "ext"), ("inq", "Inquiry job", "focus")]:
    s.part(pid, lab, k)
s.msg("ps", "pr", "authorise, reference R")
s.note("ps", "pr", "10 seconds, no answer. The customer may or may not be charged.", "red")
s.msg("ps", "ps", "→ UNKNOWN, never FAILED", hl=True)
s.ret("ps", "m", "pending")
s.msg("inq", "pr", "status of R?")
s.ret("pr", "inq", "approved → AUTHORIZED · not found → DECLINED", hl=True)
s.msg("rec", "rec", "days later: the settlement file is the final word")
s.save(OUT / "seq-timeout.svg")

# ── Sequence: idempotency ────────────────────────────────────────────────────────────────────────
s = seq()
for pid, lab, k in [("a", "Retry A", "person"), ("b", "Retry B", "person"), ("c", "Retry C, new amount", "person"),
                    ("api", "Payments API", "focus"), ("db", "Idempotency table", "db")]:
    s.part(pid, lab, k)
s.msg("a", "api", "key K, €10.50")
s.msg("api", "db", "insert (client, K): wins", hl=True)
s.msg("b", "api", "key K, €10.50")
s.ret("api", "b", "409: in progress, retry later")
s.ret("api", "a", "201, response stored")
s.msg("b", "api", "key K again")
s.ret("api", "b", "the stored response")
s.msg("c", "api", "key K, €12.00")
s.ret("api", "c", "422: same key, different payload", hl=True)
s.save(OUT / "seq-idem.svg")

# ── Sequence: crash between ledger and publish ───────────────────────────────────────────────────
s = seq()
for pid, lab, k in [("ps", "Payment service", "container"), ("db", "Ledger DB + outbox", "focus"),
                    ("rl", "Outbox relay", "container"), ("c", "Consumers", "container"), ("log", "Payment events", "queue")]:
    s.part(pid, lab, k)
s.msg("ps", "db", "state + entries + outbox row: one commit", hl=True)
s.note("ps", "db", "Crash here? Before commit: nothing. After: the event will go out.", "amber")
s.msg("rl", "db", "read unpublished rows")
s.msg("rl", "log", "publish, at least once")
s.msg("log", "c", "deliver")
s.msg("c", "c", "dedupe by event ID", hl=True)
s.save(OUT / "seq-outbox.svg")

# ── Sequence: reconciliation ─────────────────────────────────────────────────────────────────────
s = seq()
for pid, lab, k in [("bank", "Bank / processor", "ext"), ("rec", "Reconciliation", "focus"), ("db", "Ledger", "db"),
                    ("fo", "Finance ops", "person")]:
    s.part(pid, lab, k)
s.msg("bank", "rec", "daily settlement file (kept raw, immutable)")
s.msg("db", "rec", "expectations: what should settle, net of fees")
s.msg("rec", "rec", "match")
s.msg("rec", "db", "matched → SETTLED + settlement entries")
s.msg("rec", "fo", "breaks: missing, mismatched, unexpected", hl=True)
s.note("rec", "fo", "Unreconciled amount by age is a monitored metric, with an owner.", "green")
s.save(OUT / "seq-recon.svg")

# ── Hot merchant ─────────────────────────────────────────────────────────────────────────────────
row_of("hot-account", [("Append entries", "no balance lock", "5 k writes a second scale"),
                       ("Derive balance", "async projection", "seconds behind; fine for dashboards"),
                       ("Where checked", "payouts", "N sub-accounts summed, or one worker per merchant")],
       note="A balance row updated 5,000 times a second serialises on its lock. Auditors want entries anyway.",
       focus=0)

# ── Mid-round: 40,000 double postings ────────────────────────────────────────────────────────────
row_of("midround-fix", [("Stop", "kill switch", "and halt payouts for affected merchants"),
                        ("Find", "from the journal", "same payment, same type, twice"),
                        ("Reverse", "new entries", "one correction per duplicate, incident ID"),
                        ("Recover", "already paid out", "a receivable: a business decision")],
       note="Never DELETE or UPDATE. The audit trail shows the error and the correction.",
       tone=(RED, RED_BG), arrows=True, focus=2)

# ── EM phasing ───────────────────────────────────────────────────────────────────────────────────
row_of("em-phases", [("MVP", "one processor", "auto-capture; daily reconciliation"),
                     ("Then", "manual capture, refunds", "partial refunds, chargebacks"),
                     ("Later", "second processor", "routing for cost and resilience")],
       note="The one-way doors get the most review: the ledger schema and the idempotency contract.",
       tone=(GREEN, GREEN_BG), arrows=True, focus=0)

# ── Follow-ups ───────────────────────────────────────────────────────────────────────────────────
row_of("fu-offline", [("The ask", "approve offline", "when the processor is down"),
                      ("The risk", "unfunded money", "we pay the merchant; the card may decline"),
                      ("The option", "a risk policy", "small amounts, trusted buyers, capped exposure"),
                      ("Who decides", "risk and finance", "engineering prices it")],
       note="Never 'approve offline' by default. With a written risk policy and a cap, it can be a product choice.",
       focus=3)
row_of("fu-outage", [("Detect", "minutes", "approval rate per processor; UNKNOWN rising"),
                     ("Contain", "route or degrade", "secondary processor where contracts allow"),
                     ("Resolve", "the unknowns", "inquiry drains them; no blind retries"),
                     ("Learn", "next week", "per-processor game day; merchant comms")],
       note="Nobody is double-charged, because every retry carries the same reference. Say that first.",
       tone=(RED, RED_BG), arrows=True, focus=2)
row_of("fu-processor", [("Contract", "adapter interface", "auth, capture, refund, inquiry"),
                        ("Shadow", "small traffic", "1% of one merchant segment"),
                        ("Reconcile", "both files", "breaks by processor"),
                        ("Ramp", "by route", "reversible per merchant")],
       note="Three teams: API and state machine, processor integrations, reconciliation. The ledger doesn't change.",
       arrows=True, focus=0)
row_of("fu-fees", [("Slice", "by route", "card type, region, processor"),
                   ("Route", "least-cost", "where approval rates hold"),
                   ("False declines", "recover revenue", "retries with a new reference, safely"),
                   ("Report", "per payment", "fees and approval rate together")],
       note="Processor fees dwarf infrastructure. The engineering levers are routing and declines, not servers.",
       tone=(GREEN, GREEN_BG), focus=1)
print("diagrams →", OUT)
