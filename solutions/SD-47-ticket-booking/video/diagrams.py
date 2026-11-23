#!/usr/bin/env python3
"""C4, sequence, state and follow-up diagrams for the SD-47 ticket-booking video → ./svg/*.svg.
Generators: ~/.claude/skills/slide-video-kit/scripts/{c4svg,seqsvg}.py.  Run: python3 diagrams.py"""
import pathlib, sys
sys.path.insert(0, str(pathlib.Path.home() / ".claude/skills/slide-video-kit/scripts"))
import c4svg as c4, seqsvg as sq
import basesvg as bs
from erdsvg import ERD

OUT = pathlib.Path(__file__).resolve().parent / "svg"
OUT.mkdir(exist_ok=True)

def seq(size=22, row=50):
    return sq.Seq(1500, size=size, row=row, head=66)

# ── C4 level 1: system context ───────────────────────────────────────────────────────────────────
d = c4.Diagram(1600, 800)
d.node("fan", 40, 70, 320, 150, "person", "Fans · 1,000,000", "Person",
       "Arrive in the same minute for 50,000 seats.")
d.node("prom", 40, 560, 320, 150, "person", "Promoter and ops", "Person",
       "Set the on-sale, the fairness policy, add inventory.")
d.node("edge", 640, 60, 340, 150, "ext", "CDN and WAF", "External System",
       "Absorbs the million: static app, cached queue state, bot challenge.")
d.node("ts", 620, 330, 380, 210, "focus", "Ticket booking system", "Software System",
       "Meters fans in, sells each seat exactly once, tells the rest early.")
d.node("psp", 1240, 250, 320, 150, "ext", "Payment provider", "External System",
       "2–10 s, sometimes silent.")
d.node("notif", 1240, 520, 320, 140, "ext", "Email and push", "External System", "Tickets, waitlist offers")
d.edge("fan", "edge", "Join, poll, shop", "HTTPS", src="r:0.5", dst="l:0.5", at=(500, 125))
d.edge("edge", "ts", "~200 req/s, not 100,000", "", src="b:0.5", dst="t:0.5", at=(810, 270), width=280)
d.edge("prom", "ts", "Schedule, fairness, seats", "", src="r:0.5", dst="l:0.75", at=(495, 590), width=200)
d.edge("ts", "psp", "Authorize, capture, query", "API", src="r:0.25", dst="l:0.5", both=True, at=(1120, 330), width=180)
d.edge("ts", "notif", "Send tickets", "", src="r:0.8", dst="l:0.5", at=(1120, 560))
d.legend(40, 770, ("person", "focus", "ext"))
d.save(OUT / "c4-context.svg")

# ── C4 level 2: the waiting path and the read path ───────────────────────────────────────────────
d = c4.Diagram(1600, 820)
d.boundary(230, 20, 1090, 780, "Ticket booking system")
d.node("fan", 20, 110, 170, 140, "person", "Fans", "Person")
d.node("cdn", 20, 450, 170, 140, "ext", "CDN / WAF", "External")
d.node("wr", 270, 100, 200, 130, "container", "Waiting room", "Container", "join, queue/me, admit")
d.node("redis", 550, 100, 200, 130, "db", "Queue store", "Redis", "lobby set, pointer")
d.node("ac", 830, 100, 200, 130, "focus", "Admission controller", "Container", "turns the R dial")
d.node("gw", 270, 440, 200, 130, "container", "API gateway", "Container", "checks admission JWT")
d.node("map", 550, 440, 200, 130, "container", "Seat-map service", "Container", "bitmap by version")
d.node("snap", 830, 440, 200, 130, "db", "Snapshot cache", "Redis", "6.25 KB per event")
d.node("kafka", 1110, 440, 190, 130, "queue", "Seat events", "Kafka")
d.edge("fan", "wr", "join", "", src="r:0.5", dst="l:0.5", at=(230, 150))
d.edge("cdn", "wr", "queue/state, 1 s TTL", "", src="t:0.6", dst="b:0.3", via=[(122, 330), (330, 330)], at=(225, 315), width=200)
d.edge("wr", "redis", "ZADD, ZRANK", "", src="r", dst="l", at=(510, 150), width=80)
d.edge("ac", "redis", "advance pointer", "Lua", src="l", dst="r", at=(790, 150), width=80)
d.edge("cdn", "gw", "shop calls", "", src="r:0.5", dst="l:0.5", at=(230, 495))
d.edge("gw", "map", "map", "", src="r", dst="l", at=(510, 490))
d.edge("map", "snap", "read", "", src="r", dst="l", at=(790, 490))
d.edge("kafka", "snap", "rebuild ≤ 1/s", "", src="l", dst="r", at=(1070, 470), width=90)
d.edge("ac", "snap", "shop health", "", src="b:0.5", dst="t:0.5", at=(930, 320))
d.note(270, 650, 760, "Losing a second of queue state is survivable; losing a seat isn't. So the queue lives in Redis "
       "and the seats never do.", size=18)
d.save(OUT / "c4-containers-wait.svg")

# the same container view with the technologies (labels from ../stack.json)
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent / 'src')); import stack
c4.Diagram.OVERRIDE = {k: (v[1], v[2]) for k, v in stack.C4.items()}
d = c4.Diagram(1600, 820)
d.boundary(230, 20, 1090, 780, "Ticket booking system")
d.node("fan", 20, 110, 170, 140, "person", "Fans", "Person")
d.node("cdn", 20, 450, 170, 140, "ext", "CDN / WAF", "External")
d.node("wr", 270, 100, 200, 130, "container", "Waiting room", "Container", "join, queue/me, admit")
d.node("redis", 550, 100, 200, 130, "db", "Queue store", "Redis", "lobby set, pointer")
d.node("ac", 830, 100, 200, 130, "focus", "Admission controller", "Container", "turns the R dial")
d.node("gw", 270, 440, 200, 130, "container", "API gateway", "Container", "checks admission JWT")
d.node("map", 550, 440, 200, 130, "container", "Seat-map service", "Container", "bitmap by version")
d.node("snap", 830, 440, 200, 130, "db", "Snapshot cache", "Redis", "6.25 KB per event")
d.node("kafka", 1110, 440, 190, 130, "queue", "Seat events", "Kafka")
d.edge("fan", "wr", "join", "", src="r:0.5", dst="l:0.5", at=(230, 150))
d.edge("cdn", "wr", "queue/state, 1 s TTL", "", src="t:0.6", dst="b:0.3", via=[(122, 330), (330, 330)], at=(225, 315), width=200)
d.edge("wr", "redis", "ZADD, ZRANK", "", src="r", dst="l", at=(510, 150), width=80)
d.edge("ac", "redis", "advance pointer", "Lua", src="l", dst="r", at=(790, 150), width=80)
d.edge("cdn", "gw", "shop calls", "", src="r:0.5", dst="l:0.5", at=(230, 495))
d.edge("gw", "map", "map", "", src="r", dst="l", at=(510, 490))
d.edge("map", "snap", "read", "", src="r", dst="l", at=(790, 490))
d.edge("kafka", "snap", "rebuild ≤ 1/s", "", src="l", dst="r", at=(1070, 470), width=90)
d.edge("ac", "snap", "shop health", "", src="b:0.5", dst="t:0.5", at=(930, 320))
d.note(270, 650, 760, "Losing a second of queue state is survivable; losing a seat isn't. So the queue lives in Redis "
       "and the seats never do.", size=18)
d.save(OUT / "c4-containers-wait-tech.svg")
c4.Diagram.OVERRIDE = {}


# ── C4 level 2: the write path ───────────────────────────────────────────────────────────────────
d = c4.Diagram(1600, 820)
d.boundary(230, 20, 1100, 780, "Ticket booking system")
d.node("gw", 20, 110, 170, 140, "container", "API gateway", "Container")
d.node("psp", 20, 600, 170, 140, "ext", "Payment provider", "External")
d.node("inv", 270, 100, 220, 130, "focus", "Inventory & holds", "Container", "the atomic claim")
d.node("idb", 570, 100, 220, 130, "db", "Inventory DB", "PostgreSQL", "event_seat, hold, outbox")
d.node("kafka", 870, 100, 180, 130, "queue", "Seat events", "Kafka", "outbox relay")
d.node("noti", 1120, 100, 180, 130, "container", "Notifications", "Container", "tickets by email")
d.node("ord", 270, 440, 220, 130, "container", "Order service", "Container", "checkout saga")
d.node("odb", 570, 440, 220, 130, "db", "Order DB", "PostgreSQL", "orders, tickets")
d.node("exp", 870, 440, 220, 130, "container", "Hold expirer", "Container", "sweeper")
d.edge("gw", "inv", "hold", "JWT", src="r:0.5", dst="l:0.5", at=(230, 150))
d.edge("inv", "idb", "claim + outbox", "1 txn", src="r", dst="l", at=(530, 145), width=80)
d.edge("idb", "kafka", "relay", "", src="r", dst="l", at=(830, 150))
d.edge("kafka", "noti", "events", "", src="r", dst="l", at=(1085, 150))
d.edge("gw", "ord", "order", "", src="b:0.5", dst="l:0.5", via=[(105, 505)], at=(150, 470))
d.edge("ord", "inv", "freeze, sell", "", src="t:0.5", dst="b:0.5", at=(380, 330))
d.edge("ord", "odb", "order, tickets", "", src="r", dst="l", at=(530, 485), width=80)
d.edge("exp", "idb", "release expired, SKIP LOCKED", "", src="t:0.5", dst="b:0.5", via=[(980, 330), (680, 330)],
       at=(830, 315), width=300)
d.edge("ord", "psp", "authorize, query, capture", "", src="b:0.4", dst="r:0.5", via=[(358, 670)], at=(290, 700), width=150)
d.note(570, 620, 520, "ticket UNIQUE (event, seat): the last line of defence against oversell.", size=18)
d.save(OUT / "c4-containers-write.svg")

# the same container view with the technologies (labels from ../stack.json)
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent / 'src')); import stack
c4.Diagram.OVERRIDE = {k: (v[1], v[2]) for k, v in stack.C4.items()}
d = c4.Diagram(1600, 820)
d.boundary(230, 20, 1100, 780, "Ticket booking system")
d.node("gw", 20, 110, 170, 140, "container", "API gateway", "Container")
d.node("psp", 20, 600, 170, 140, "ext", "Payment provider", "External")
d.node("inv", 270, 100, 220, 130, "focus", "Inventory & holds", "Container", "the atomic claim")
d.node("idb", 570, 100, 220, 130, "db", "Inventory DB", "PostgreSQL", "event_seat, hold, outbox")
d.node("kafka", 870, 100, 180, 130, "queue", "Seat events", "Kafka", "outbox relay")
d.node("noti", 1120, 100, 180, 130, "container", "Notifications", "Container", "tickets by email")
d.node("ord", 270, 440, 220, 130, "container", "Order service", "Container", "checkout saga")
d.node("odb", 570, 440, 220, 130, "db", "Order DB", "PostgreSQL", "orders, tickets")
d.node("exp", 870, 440, 220, 130, "container", "Hold expirer", "Container", "sweeper")
d.edge("gw", "inv", "hold", "JWT", src="r:0.5", dst="l:0.5", at=(230, 150))
d.edge("inv", "idb", "claim + outbox", "1 txn", src="r", dst="l", at=(530, 145), width=80)
d.edge("idb", "kafka", "relay", "", src="r", dst="l", at=(830, 150))
d.edge("kafka", "noti", "events", "", src="r", dst="l", at=(1085, 150))
d.edge("gw", "ord", "order", "", src="b:0.5", dst="l:0.5", via=[(105, 505)], at=(150, 470))
d.edge("ord", "inv", "freeze, sell", "", src="t:0.5", dst="b:0.5", at=(380, 330))
d.edge("ord", "odb", "order, tickets", "", src="r", dst="l", at=(530, 485), width=80)
d.edge("exp", "idb", "release expired, SKIP LOCKED", "", src="t:0.5", dst="b:0.5", via=[(980, 330), (680, 330)],
       at=(830, 315), width=300)
d.edge("ord", "psp", "authorize, query, capture", "", src="b:0.4", dst="r:0.5", via=[(358, 670)], at=(290, 700), width=150)
d.note(570, 620, 520, "ticket UNIQUE (event, seat): the last line of defence against oversell.", size=18)
d.save(OUT / "c4-containers-write-tech.svg")
c4.Diagram.OVERRIDE = {}


# ── C4 level 3: inside the inventory service ─────────────────────────────────────────────────────
d = c4.Diagram(1600, 780)
d.boundary(240, 20, 1060, 580, "Inventory & holds", "Container")
d.node("gw", 20, 180, 190, 120, "container", "API gateway", "Container")
d.node("ord", 20, 380, 190, 120, "container", "Order service", "Container")
d.node("api", 280, 180, 220, 130, "component", "Hold API", "Component", "idempotency, limits")
d.node("claim", 570, 90, 240, 130, "focus", "Claim engine", "Component", "sorted locks, NOWAIT, all-or-nothing")
d.node("out", 570, 290, 240, 130, "component", "Outbox writer", "Component", "same transaction")
d.node("frz", 280, 380, 220, 130, "component", "Freeze / sell", "Component", "for checkout")
d.node("sw", 1000, 290, 260, 130, "component", "Sweeper", "Component", "SKIP LOCKED, batches of 500")
d.node("db", 560, 650, 520, 110, "db", "Inventory DB", "PostgreSQL · partitioned by event")
d.edge("gw", "api", "", src="r", dst="l")
d.edge("ord", "frz", "", src="r", dst="l")
d.edge("api", "claim", "", src="r:0.3", dst="l:0.5")
d.edge("claim", "out", "one txn", "", src="b:0.5", dst="t:0.5", at=(690, 255))
d.edge("claim", "db", "conditional UPDATE", "", src="r:0.5", dst="t:0.7", via=[(900, 155), (900, 620), (924, 620)],
       at=(960, 200), width=170)
d.edge("out", "db", "", src="b:0.5", dst="t:0.25")
d.edge("frz", "db", "", src="b:0.5", dst="t:0.05", via=[(390, 620), (586, 620)])
d.edge("sw", "db", "release expired", "", src="b:0.5", dst="t:0.95", via=[(1130, 620), (1054, 620)], at=(1150, 470))
d.note(1000, 100, 280, "Lazy expiry lives in the claim predicate; the sweeper only makes the map catch up.", size=17)
d.save(OUT / "c4-component-inventory.svg")

# ── Seat state machine (drawn with the C4 boxes) ─────────────────────────────────────────────────
d = c4.Diagram(1600, 560)
d.node("av", 60, 200, 260, 120, "container", "AVAILABLE", "")
d.node("held", 460, 200, 260, 120, "component", "HELD", "", "5-minute expiry")
d.node("pp", 860, 200, 300, 120, "focus", "PAYMENT_PENDING", "", "frozen; the sweeper never touches it")
d.node("sold", 1300, 200, 240, 120, "system", "SOLD", "")
d.edge("av", "held", "claim", "", src="r", dst="l", dashed=False, at=(390, 245))
d.edge("held", "pp", "order placed", "", src="r", dst="l", dashed=False, at=(790, 245), width=110)
d.edge("pp", "sold", "authorized", "", src="r", dst="l", dashed=False, at=(1230, 245), width=100)
d.edge("held", "av", "expired or released", "", src="t:0.5", dst="t:0.5", via=[(590, 110), (190, 110)], at=(390, 98), width=300)
d.edge("pp", "av", "declined, or definitely failed", "", src="b:0.5", dst="b:0.5", via=[(1010, 430), (190, 430)],
       at=(600, 445), width=400)
d.save(OUT / "seat-states.svg")

# ── Sequence: two fans, one seat ─────────────────────────────────────────────────────────────────
s = seq()
for pid, lab, k in [("a", "Fan A", "person"), ("b", "Fan B", "person"), ("inv", "Inventory service", "container"),
                    ("db", "PostgreSQL", "db")]:
    s.part(pid, lab, k)
s.msg("a", "inv", "POST /holds [101, 102]")
s.msg("inv", "db", "SELECT … ORDER BY seat_id FOR UPDATE NOWAIT")
s.msg("b", "inv", "POST /holds [102, 103]")
s.msg("inv", "db", "FOR UPDATE NOWAIT")
s.ret("db", "inv", "55P03: row is locked")
s.ret("inv", "b", "409 + fresh bitmap", hl=True)
s.msg("inv", "db", "UPDATE … WHERE state = 'AVAILABLE' → 2 rows", hl=True)
s.msg("inv", "db", "INSERT hold, INSERT outbox · COMMIT")
s.ret("inv", "a", "201 held for 5 minutes")
s.save(OUT / "seq-hold-race.svg")

# ── Sequence: the lobby and T0 ───────────────────────────────────────────────────────────────────
s = seq()
for pid, lab, k in [("fan", "Fan browser", "person"), ("cdn", "CDN / WAF", "ext"), ("wr", "Waiting room", "container"),
                    ("r", "Redis", "db")]:
    s.part(pid, lab, k)
s.msg("fan", "cdn", "open lobby page, bot challenge")
s.msg("cdn", "wr", "POST /queue")
s.msg("wr", "r", "ZADD lobby, secret random score")
s.ret("wr", "fan", "signed queue token LOBBY + server time")
s.note("fan", "r", "T0: the phase flips to QUEUE. The sorted order IS the lottery.", "blue")
s.msg("fan", "wr", "after a random 0–20 s: GET /queue/me")
s.msg("wr", "r", "ZRANK → seq")
s.ret("wr", "fan", "your number: 412,377", hl=True)
s.msg("fan", "wr", "late arrival: POST /queue")
s.msg("wr", "r", "INCR next → after the last lobby fan")
s.save(OUT / "seq-lobby.svg")

# ── Sequence: polling and admission ──────────────────────────────────────────────────────────────
s = seq()
for pid, lab, k in [("fan", "Fan browser", "person"), ("cdn", "CDN edge", "ext"), ("wr", "Waiting room", "container"),
                    ("ac", "Admission controller", "focus"), ("r", "Redis", "db")]:
    s.part(pid, lab, k)
s.frame("loop", "every ~10 s, ±20 % jitter")
s.msg("fan", "cdn", "GET /queue/state")
s.msg("cdn", "wr", "once per edge per second", hl=True)
s.ret("cdn", "fan", "{admittedUpTo, ratePerMin, soldOut}")
s.msg("fan", "fan", "position = seq − admittedUpTo")
s.end()
s.msg("ac", "r", "every second: advance pointer by R ÷ 60", "async")
s.msg("fan", "wr", "seq ≤ admittedUpTo: POST /admit")
s.msg("wr", "r", "SET admitted NX (once per fan)")
s.ret("wr", "fan", "admission JWT, 10 minutes", hl=True)
s.save(OUT / "seq-admit.svg")

# ── Sequence: hold expiry, lazy and swept ────────────────────────────────────────────────────────
s = seq()
for pid, lab, k in [("c", "Fan C", "person"), ("inv", "Inventory service", "container"), ("db", "PostgreSQL", "db"),
                    ("sw", "Sweeper", "component"), ("k", "Kafka", "queue"), ("map", "Seat map", "container")]:
    s.part(pid, lab, k)
s.frame("alt", "lazy expiry: correctness")
s.msg("c", "inv", "POST /holds [101]")
s.msg("inv", "db", "… OR (HELD AND expires_at < now())", hl=True)
s.ret("inv", "c", "201: the expired seat is claimable at once")
s.end()
s.frame("loop", "sweeper, every 5 s: freshness")
s.msg("sw", "db", "FOR UPDATE SKIP LOCKED LIMIT 500")
s.msg("sw", "db", "→ AVAILABLE + outbox SeatsReleased")
s.msg("db", "k", "relay", "async")
s.msg("k", "map", "bitmap shows the seats free", "async")
s.end()
s.save(OUT / "seq-expiry.svg")

# ── Sequence: checkout, the happy path ───────────────────────────────────────────────────────────
s = seq()
for pid, lab, k in [("fan", "Fan", "person"), ("ord", "Order service", "container"), ("inv", "Inventory", "container"),
                    ("psp", "Payment provider", "ext"), ("odb", "Order DB", "db")]:
    s.part(pid, lab, k)
s.msg("fan", "ord", "POST /orders, idempotency key")
s.ret("ord", "fan", "202 PENDING; the fan polls")
s.msg("ord", "inv", "freeze: HELD → PAYMENT_PENDING", hl=True)
s.msg("ord", "psp", "authorize, PSP key order-91-1")
s.ret("psp", "ord", "APPROVED")
s.msg("ord", "inv", "sell: PAYMENT_PENDING → SOLD")
s.msg("ord", "odb", "CONFIRMED, tickets, outbox · one txn")
s.msg("ord", "psp", "capture, asynchronously", "async")
s.note("fan", "odb", "Reserve the money, secure the seats, take the money. Each step undoes cheaply until the last.", "green")
s.save(OUT / "seq-checkout.svg")

# ── Sequence: the payment outcome is unknown ─────────────────────────────────────────────────────
s = seq()
for pid, lab, k in [("ord", "Order service", "container"), ("rec", "Reconciler", "component"),
                    ("psp", "Payment provider", "ext"), ("inv", "Inventory", "container")]:
    s.part(pid, lab, k)
s.msg("ord", "psp", "authorize, key order-91-1")
s.msg("ord", "ord", "10 s timeout → UNKNOWN, not FAILED", hl=True)
s.note("inv", "inv", "seats stay PAYMENT_PENDING", "red")
s.frame("alt", "first definite answer wins")
s.msg("rec", "psp", "every 2 s: lookup order-91-1")
s.ret("psp", "rec", "AUTHORIZED")
s.msg("psp", "ord", "signed webhook: AUTHORIZED", "async")
s.msg("ord", "inv", "confirm: conditional transition, only once")
s.end()
s.msg("rec", "psp", "past the deadline: cancel, release seats")
s.save(OUT / "seq-unknown.svg")

# ════════ v2 (2026-10-29): Staff L6/L7 depth — calculations, wire formats, ERDs, alternatives ════════
GREEN, GREEN_BG, RED, RED_BG, BLUE, BLUE_BG = "#2d8a4e", "#e7f4ec", "#c8341f", "#fdecea", "#2f6fb5", "#e8f0fa"

# ── The load funnel, with the arithmetic on every layer ──────────────────────────────────────────
d = c4.Diagram(1600, 760)
L = [("f1", "100,000 req/s", "at the CDN", "1,000,000 fans ÷ 10 s poll"),
     ("f2", "~200 req/s", "at the origin", "~200 edges ÷ 1 s TTL (shield: ~1/s)"),
     ("f3", "33 admits/s", "into the shop", "10,000 shoppers ÷ 300 s each (Little's law)"),
     ("f4", "5,000 reads/s", "seat map, Redis", "10,000 shoppers ÷ 2 s poll; 304 if unchanged"),
     ("f5", "50–500 holds/s", "PostgreSQL", "33/s × 1.5 attempts; × 10 bursts"),
     ("f6", "~25 payments/s", "to the PSP", "20,000 orders ÷ ~900 s; × 10 s = 250 in flight")]
for i, (nid, h, t, desc) in enumerate(L):
    x = 40 + (i % 3) * 520; y = 60 + (i // 3) * 330
    d.node(nid, x, y, 460, 230, "focus" if i in (2, 4) else "container", h, t, desc, size=25)
d.edge("f1", "f2", "", src="r", dst="l", dashed=False)
d.edge("f2", "f3", "", src="r", dst="l", dashed=False)
d.edge("f3", "f4", "", src="b:0.5", dst="t:0.5", via=[(1310, 330), (270, 330)], dashed=False)
d.edge("f4", "f5", "", src="r", dst="l", dashed=False)
d.edge("f5", "f6", "", src="r", dst="l", dashed=False)
d.note(40, 680, 1520, "Each layer shrinks the number below it. After the queue, the write path is a few hundred "
       "transactions a second: not a big-data problem.", size=20, colour=GREEN, bg=GREEN_BG)
d.save(OUT / "load-funnel.svg")

# ── What a waiting fan gets from the CDN ─────────────────────────────────────────────────────────
d = c4.Diagram(1600, 720)
d.node("fans", 40, 70, 300, 170, "person", "1,000,000 fans", "poll every 3–30 s", "seq is in their signed token")
d.node("edge", 460, 70, 320, 170, "ext", "~200 CDN edges", "max-age=1", "collapse concurrent misses")
d.node("sh", 900, 70, 300, 170, "ext", "Origin shield", "one fetch per second", "")
d.node("wr", 1320, 70, 240, 170, "focus", "Waiting room", "reads Redis", "4 keys, one GET each")
d.edge("fans", "edge", "100 k/s", "", src="r", dst="l", at=(400, 130), width=90)
d.edge("edge", "sh", "~200/s", "", src="r", dst="l", at=(840, 130), width=80)
d.edge("sh", "wr", "~1/s", "", src="r", dst="l", at=(1260, 130), width=60)
d.note(40, 300, 1520, "HTTP/1.1 200 · Content-Type: application/json · Cache-Control: public, max-age=1, "
       "stale-while-revalidate=2, stale-if-error=30 · ~90 bytes", size=19, colour=BLUE, bg=BLUE_BG)
d.note(40, 390, 1000, '{"admittedUpTo": 31800, "ratePerMin": 2000, "admissionPaused": false, '
       '"soldOut": false, "serverTime": 1792131002}', size=21, colour="#1f2328", bg="#f6f8fa")
d.note(1080, 390, 480, "No user in the body: one cached object serves everyone. The client computes "
       "ahead = mySeq − admittedUpTo.", size=19, colour=GREEN, bg=GREEN_BG)
d.note(40, 560, 1520, "ETA = ahead ÷ ratePerMin. Fan 380,577 at pointer 31,800: 348,777 ÷ 2,000 ≈ 174 min, "
       "past the ~15 min sell-out, so we say 'likely sold out' early.", size=19)
d.save(OUT / "cdn-state.svg")

# ── The availability bitmap, bit by bit ──────────────────────────────────────────────────────────
d = ERD(1600, 760, size=20)
d.text(40, 50, "GET /events/evt-7731/availability?v=811   →   200 · X-Map-Version: 812 · Content-Type: "
       "application/octet-stream · 6,250 bytes", 20, "#1f2328", mono=True)
cells = []
bits = [1,1,0,1,0,0,1,1, 1,1,1,1,0,1,1,1, 0,0,0,0,1,1,0,1]
for i, b in enumerate(bits):
    byte, bit = divmod(i, 8)
    x = 60 + byte * 500 + bit * 58; y = 130
    fill = "#e7f4ec" if b else "#eef1f4"; stroke = "#2d8a4e" if b else "#8c959f"
    cells.append(f'<rect x="{x}" y="{y}" width="54" height="64" rx="5" fill="{fill}" stroke="{stroke}" stroke-width="1.4"/>'
                 f'<text x="{x+27}" y="{y+42}" text-anchor="middle" font-family="DejaVu Sans Mono, Menlo, monospace" font-size="26" font-weight="700" fill="#1f2328">{b}</text>'
                 f'<text x="{x+27}" y="{y+90}" text-anchor="middle" font-family="Inter, sans-serif" font-size="15" fill="#57606a">{i}</text>')
for byte in range(3):
    x = 60 + byte * 500
    cells.append(f'<text x="{x}" y="{118}" font-family="Inter, sans-serif" font-size="17" font-weight="700" fill="#57606a">byte {byte}</text>')
cells.append('<text x="1560" y="118" text-anchor="end" font-family="Inter, sans-serif" font-size="17" font-weight="700" fill="#57606a">… up to byte 6,249</text>')
d.raw("\n".join(cells))
d.text(60, 270, "bit i = seat_id i (dense 0…49,999) · 1 = free · 0 = held, pending or sold · LSB-first per byte (Java BitSet.toByteArray)", 18, "#57606a")
d.note(40, 310, 740, "Size: 50,000 seats ÷ 8 = 6,250 bytes; gzip ~1–3 KB when mostly sold.", size=19, colour=BLUE, bg=BLUE_BG)
d.note(820, 310, 740, "Version = the Kafka offset of the last applied seat event: only grows, survives restarts.", size=19, colour=BLUE, bg=BLUE_BG)
d.note(40, 420, 740, "Unchanged since v? → 304 Not Modified, no body: 5,000 req/s × ~200 B ≈ 1 MB/s instead of ~31 MB/s.",
       size=19, colour=GREEN, bg=GREEN_BG)
d.note(820, 420, 740, "Layout (positions, sections, prices) is separate: immutable, versioned URL, CDN-cached for a year.",
       size=19, colour=GREEN, bg=GREEN_BG)
d.note(40, 540, 1520, "A stale bit is a hint, not a promise: the hold in PostgreSQL decides. A stale click gets 409 with "
       "this same structure as the body, so the next click lands on a free seat.", size=19, colour=RED, bg=RED_BG)
d.save(OUT / "bitmap.svg")

# ── ERD: the inventory database (the hot one) ────────────────────────────────────────────────────
d = ERD(1600, 860, size=23)
d.entity("ev", 20, 30, 400, "event", [("event_id", "bigint", "PK"), ("venue_id", "bigint", "FK"),
         ("on_sale_at", "timestamptz", ""), ("layout_ver", "int", ""), ("max_per_acct", "smallint", "")],
         kind="table", caption="thousands of rows")
d.entity("seat", 520, 30, 560, "event_seat", [("event_id", "bigint", "PK,FK"), ("seat_id", "int 0…N-1", "PK"),
         ("section", "text", ""), ("state", "text CHECK(4)", ""), ("hold_id", "uuid", "FK"),
         ("hold_expires_at", "timestamptz", "IX"), ("order_id", "uuid", ""), ("version", "int", "")],
         kind="focus", caption="50,000 rows · PARTITION BY HASH(event_id)")
d.entity("hold", 1160, 30, 430, "hold", [("hold_id", "uuid", "PK"), ("event_id", "bigint", ""),
         ("user_id", "bigint", ""), ("seat_ids", "int[]", ""), ("status", "text", ""), ("expires_at", "timestamptz", ""),
         ("idem_key", "text", "UK")], caption="UNIQUE (user_id, idem_key)")
d.entity("ob", 520, 560, 560, "outbox", [("id", "bigserial", "PK"), ("event_id", "bigint", ""),
         ("event_type", "text", ""), ("payload", "jsonb", "")],
         kind="ext", caption="tailed from the WAL by Debezium → Kafka")
d.rel("ev", "seat", "1", "N", src="r:0.3", dst="l:0.2", label="event_id", at=(470, 110))
d.rel("hold", "seat", "1", "N", src="l:0.3", dst="r:0.6", label="hold_id", at=(1120, 230))
d.rel("seat", "ob", "", "", src="b:0.5", dst="t:0.5", label="same commit", dashed=True)
d.note(20, 330, 440, "Partial index (event_id, hold_expires_at) WHERE state = 'HELD': only the few thousand held rows.",
       size=20)
d.note(1160, 470, 430, "The seat row is the truth; the hold row is bookkeeping.", size=20, colour=RED, bg=RED_BG)
d.save(OUT / "erd-inventory.svg")

# ── ERD: the order database (separate, owned by the order service) ───────────────────────────────
d = ERD(1600, 820, size=23)
d.entity("o", 20, 30, 500, "orders", [("order_id", "uuid", "PK"), ("user_id", "bigint", ""),
         ("event_id", "bigint", ""), ("hold_id", "uuid", "UK"), ("amount", "numeric(12,2)", ""),
         ("currency", "char(3)", ""), ("status", "text", ""), ("psp_ref", "text", ""), ("idem_key", "text", "UK")],
         kind="focus", caption="UNIQUE hold_id: one order per hold")
d.entity("pa", 640, 30, 450, "payment_attempt", [("order_id", "uuid", "PK,FK"), ("attempt", "int", "PK"),
         ("psp_idem_key", "text", "UK"), ("status", "text", ""), ("last_checked", "timestamptz", "")],
         caption="SENT · AUTHORIZED · UNKNOWN · VOIDED")
d.entity("t", 1180, 30, 410, "ticket", [("ticket_id", "uuid", "PK"), ("event_id", "bigint", "UK"),
         ("seat_id", "int", "UK"), ("order_id", "uuid", "FK"), ("barcode", "bytea", "")],
         caption="UNIQUE (event_id, seat_id)")
d.rel("o", "pa", "1", "N", src="r:0.2", dst="l:0.3", label="order_id", at=(580, 70))
d.rel("o", "t", "1", "N", src="r:0.75", dst="b:0.5", via=[(1385, 395)], label="order_id", at=(900, 395))
d.note(20, 560, 1570, "Money is numeric(12,2), never a float. psp_idem_key is what the PSP deduplicates on, so a retried "
       "authorisation is never a second charge. The ticket's UNIQUE (event_id, seat_id) is the last line against oversell, "
       "independent of our code.", size=21)
d.save(OUT / "erd-orders.svg")

# ── Redis keyspace for one event (one hash slot via {e}) ─────────────────────────────────────────
d = ERD(1600, 800, size=22)
d.entity("ph", 20, 20, 500, "phase:{e}  STRING", [("value", "LOBBY | QUEUE", "")], kind="redis")
d.entity("lb", 20, 170, 500, "lobby:{e}  ZSET", [("member", "user-48213", ""), ("score", "0.73195 (secret)", ""),
         ("size", "~1 M · ~100 MB", "")], kind="redis", caption="ZADD NX at join · ZRANK + 1 = seq")
d.entity("nx", 560, 20, 480, "next:{e}  INT", [("value", "1,000,412 (last seq)", "")], kind="redis")
d.entity("ad", 560, 170, 480, "admittedUpTo:{e}  INT", [("value", "31,800", "")], kind="focus",
         caption="advance.lua, once a second")
d.entity("rt", 560, 340, 480, "rate:{e} · soldOut:{e}", [("rate", "2000 per minute", ""), ("soldOut", "false", "")], kind="redis")
d.entity("am", 1080, 20, 510, "admitted:{e}:{user}", [("value", "admission JWT", ""), ("ttl", "6 h", "")], kind="redis",
         caption="SET NX: a re-admit returns the same token")
d.entity("mp", 1080, 240, 510, "map:{e}:{v} · map:{e}:v", [("map:{e}:812", "6,250-byte bitmap", ""), ("map:{e}:v", "812", "")],
         kind="redis", caption="pointer flipped last; old versions TTL 2 min")
d.note(20, 560, 1570, "{e} is a Redis Cluster hash tag: only the part in braces is hashed, so every key of one event "
       "sits on one node and one Lua script can touch them atomically. Different events land on different nodes.",
       size=21, colour=BLUE, bg=BLUE_BG)
d.save(OUT / "redis-keys.svg")

# ── Sequence: from a committed hold to a fan's map ───────────────────────────────────────────────
s = seq(size=21)
for pid, lab, k in [("inv", "Inventory service", "container"), ("pg", "PostgreSQL + outbox", "db"),
                    ("dbz", "Debezium (WAL)", "container"), ("kf", "Kafka seat-events", "queue"),
                    ("sb", "Snapshot builder", "focus"), ("rd", "Redis map:{e}", "db"), ("fan", "Shopper", "person")]:
    s.part(pid, lab, k)
s.msg("inv", "pg", "UPDATE seats + INSERT outbox: one commit", hl=True)
s.msg("dbz", "pg", "tail the write-ahead log")
s.msg("dbz", "kf", "SeatsHeld, key = event_id", "async")
s.msg("kf", "sb", "consume in order; set bits")
s.msg("sb", "rd", "≤ 1/s: SET map:{e}:{offset}, then flip map:{e}:v", hl=True)
s.msg("fan", "rd", "GET /availability?v=811 (via API)")
s.ret("rd", "fan", "200 v812 bitmap · or 304 if still 811")
s.save(OUT / "seq-seatmap.svg")

# ── The admission controller (AIMD) ──────────────────────────────────────────────────────────────
d = c4.Diagram(1600, 620)
d.node("m", 40, 70, 340, 200, "container", "Read signals", "every 1 s", "shoppers, hold p99, DB CPU, PSP errors, 409 ratio")
d.node("u", 460, 70, 340, 200, "focus", "Healthy?", "AIMD", "yes: R += step · no: R × 0.7")
d.node("a", 880, 70, 340, 200, "container", "Advance pointer", "advance.lua", "min(cur + R/60, next)")
d.node("p", 1300, 70, 260, 200, "ext", "Publish", "CDN state", "rate, flags")
for a_, b_ in [("m", "u"), ("u", "a"), ("a", "p")]:
    d.edge(a_, b_, "", src="r", dst="l", dashed=False)
d.edge("p", "m", "next tick", "", src="b:0.5", dst="b:0.5", via=[(1430, 330), (210, 330)], dashed=False, at=(820, 330), width=120)
d.note(40, 400, 760, "Thresholds: hold p99 > 300 ms, DB CPU > 70%, PSP errors > 5% → cut. Below 10,000 shoppers → ramp.",
       size=19)
d.note(840, 400, 720, "One leader per event (Redis lease, renewed every second). Two controllers would admit double.",
       size=19, colour=RED, bg=RED_BG)
d.save(OUT / "controller.svg")

# ── Follow-up: twenty dates on sale at once ──────────────────────────────────────────────────────
d = c4.Diagram(1600, 560)
mo = [("a", "Keyed by event_id", "everything", "Redis slot, DB partition, Kafka key, JWT evt, CDN key"),
      ("b", "Spread", "across nodes", "hash tags place each event's keys on its own Redis node"),
      ("c", "Shared limits", "the PSP, the CDN", "a global admission budget split across events"),
      ("d", "Hot event", "its own primary", "a big on-sale gets a dedicated PostgreSQL partition host")]
for i, (nid, h, t, desc) in enumerate(mo):
    d.node(nid, 40 + i * 390, 70, 350, 250, "focus" if i == 2 else "container", h, t, desc, size=24)
d.note(40, 380, 1520, "Many events are an isolation problem, not a coordination problem. The only shared resources "
       "are the PSP pool and edge capacity, so those get explicit budgets.", size=21, colour=BLUE, bg=BLUE_BG)
d.save(OUT / "fu-multi-event.svg")
print("diagrams →", OUT)


# ───────────────────────────── The carried baseline (2026-11-21 reference-solution format) ─────────────────────
b = bs.Baseline(1600, 900)
b.node("fans", 20, 300, 170, 130, "client", "Fans", "browsers · apps")
b.node("edge", 355, 300, 170, 130, "edge", "CDN · gateway", "token check · cache", since=3)
b.node("api", 690, 300, 170, 130, "service", "Booking API", "claim · hold")
b.node("db", 1025, 300, 170, 130, "data", "Seat DB", "one row per seat", shape="db")
b.node("log", 1360, 300, 170, 130, "queue", "Event log", "seats changed", shape="queue", since=3)
b.node("wr", 355, 70, 170, 120, "service", "Waiting room", "lobby · pointer", since=3)
b.node("bm", 690, 70, 170, 120, "cache", "Seat map", "versioned bitmap", since=3)
b.node("sb", 1025, 70, 170, 120, "service", "Snapshot builder", "1 version / s", since=3)
b.node("ord", 690, 560, 170, 120, "service", "Order service", "orders", since=2)
b.node("psp", 1360, 560, 170, 120, "ext", "Payment provider", "2 to 10 s", since=2)
b.node("ctrl", 20, 70, 170, 120, "service", "Admission controller", "sets the rate", tag="ch4")
b.node("sweep", 1025, 745, 170, 90, "service", "Sweeper", "every 5 s", tag="ch2")
b.node("recon", 355, 560, 170, 120, "service", "Reconciler", "unknown orders", tag="ch3")
b.node("wl", 1360, 70, 170, 120, "service", "Waitlist", "new consumer", tag="ch7")
b.node("mon", 20, 560, 170, 120, "ext", "Probes", "a synthetic fan", tag="ch8")

REQ = dict(src="r:0.25", dst="l:0.25")
b.edge("f-a", "fans", "api", "buy a seat", until=2, **REQ)
b.edge("a-f", "api", "fans", "result", until=2, kind="resp", src="l:0.75", dst="r:0.75")
b.edge("a-d1", "api", "db", "check, write", until=1, **REQ)
b.edge("a-d", "api", "db", "claim", since=2, **REQ)
b.edge("d-a", "db", "api", "won or lost", since=2, kind="resp", src="l:0.75", dst="r:0.75")
b.edge("a-o", "api", "ord", "pay", since=2, src="b:0.5", dst="t:0.5")
b.edge("o-d", "ord", "db", "freeze · sell", since=2, src="r:0.2", dst="b:0.2", via=[(1059, 582)])
b.edge("o-p", "ord", "psp", "authorize", since=2, src="r:0.65", dst="l:0.65", at=(1010, 608))
b.edge("p-o", "psp", "ord", "answer or silence", since=2, kind="resp", src="l:0.9", dst="r:0.9", at=(1010, 696))
b.edge("f-e", "fans", "edge", "request", since=3, **REQ)
b.edge("e-f", "edge", "fans", "response", since=3, kind="resp", src="l:0.75", dst="r:0.75")
b.edge("e-a", "edge", "api", "admitted only", since=3, **REQ)
b.edge("a-e", "api", "edge", "result", since=3, kind="resp", src="l:0.75", dst="r:0.75")
b.edge("e-w", "edge", "wr", "join · poll", since=3, src="t:0.5", dst="b:0.5")
b.edge("e-b", "edge", "bm", "map", since=3, src="t:0.92", dst="l:0.5", via=[(516, 250), (620, 250), (620, 130)])
b.edge("d-l", "db", "log", "outbox", since=3, kind="async", src="r:0.5", dst="l:0.5")
b.edge("l-s", "log", "sb", "events", since=3, kind="async", src="t:0.2", dst="b:0.5", via=[(1394, 245), (1110, 245)])
b.edge("s-b", "sb", "bm", "publish", since=3, src="l:0.5", dst="r:0.5")
b.edge("c-w", "ctrl", "wr", "rate", tag="ch4", src="r:0.5", dst="l:0.5")
b.edge("sw-d", "sweep", "db", "release expired", tag="ch2", src="t:0.8", dst="b:0.8", at=(1262, 520))
b.edge("r-o", "recon", "ord", "unknown?", tag="ch3", src="r:0.5", dst="l:0.5")
b.edge("r-p", "recon", "psp", "status", tag="ch3", src="b:0.5", dst="b:0.5", via=[(440, 860), (1445, 860)])
b.edge("l-wl", "log", "wl", "released", tag="ch7", kind="async", src="t:0.75", dst="b:0.75")

b.edge("m-f", "mon", "fans", "probe", tag="ch8", src="t:0.5", dst="b:0.5")

def sv(name, h, **view):
    b.h = h
    b.save(OUT / name, **view)
ALL = ["ch2", "ch3", "ch4", "ch7", "ch8"]
sv("base-v1.svg", 470, upto=1, legend=True)
sv("base-v2.svg", 760, upto=2, new=2, legend=True)
sv("base-v3.svg", 760, upto=3, new=3, legend=True)
sv("base-final.svg", 900, upto=3, show=ALL, legend=True)
sv("map.svg", 900, upto=3, show=ALL, legend=True, attack=["db", "sweep", "ord", "wr", "bm", "edge", "wl"], keep=None)

sv("flow-fr1.svg", 545, upto=3, flow=["f-e", "e-w", "e-a"],
   notes=[(560, 440, 760, "Join the lobby, get a signed place in line, exchange it for an admission token when the pointer reaches you.", "blue")])
sv("flow-fr2.svg", 545, upto=3, flow=["f-e", "e-b", "e-f"],
   notes=[(560, 440, 760, "Layout from the CDN, availability as a versioned bitmap. A 304 when nothing changed.", "blue")])
sv("flow-fr3.svg", 545, upto=3, flow=["f-e", "e-a", "a-d", "d-a", "a-e", "e-f"],
   notes=[(560, 440, 760, "Admission token checked at the gateway; one conditional claim; 201 with an expiry, or 409 with a fresh map.", "blue")])
sv("flow-fr4.svg", 700, upto=3, show=["ch3"], flow=["a-o", "o-d", "o-p", "p-o", "r-o"],
   notes=[(900, 440, 640, "Freeze, authorize, sell on approval. A silent provider leaves the order unknown, not failed.", "blue")])
sv("flow-fr5.svg", 900, upto=3, show=["ch2", "ch7"], flow=["sw-d", "d-l", "l-wl"],
   notes=[(40, 440, 700, "Expired holds return to available and are announced. A released seat can go to the next fan waiting.", "blue")])
sv("ch1-attack.svg", 545, upto=3, attack=["db"], keep=["edge", "api", "db"], hot=["a-d", "e-a"],
   notes=[(560, 470, 760, "Two fans read free, both write: seat 102 is sold twice.", "red")])
sv("ch1-fix.svg", 545, upto=3, fix=["api"], keep=["edge", "api", "db"], ok=["a-d", "d-a"],
   notes=[(560, 470, 760, "One conditional update is the check and the change. The loser changes zero rows and gets a 409.", "green")])
sv("ch2-attack.svg", 545, upto=3, attack=["db"], keep=["api", "db"], hot=["a-d"],
   notes=[(560, 470, 760, "A hold with no owner left: the seat is neither free nor sold, and nothing ever frees it.", "red")])
sv("ch2-fix.svg", 900, upto=3, show=["ch2"], fix=["sweep", "db"], keep=["api", "db", "sweep", "log"], ok=["sw-d", "d-l", "a-d"],
   notes=[(40, 480, 640, "Lazy expiry inside the claim; a sweeper every 5 s makes the map catch up.", "green")])
sv("ch3-attack.svg", 700, upto=3, attack=["ord"], keep=["api", "db", "ord", "psp"], hot=["o-d", "p-o"],
   notes=[(40, 470, 640, "The hold expired at 5:00; at 5:05 the provider says approved. Two paid, one seat.", "red")])
sv("ch3-fix.svg", 900, upto=3, show=["ch3"], fix=["ord", "recon"], keep=["api", "db", "ord", "psp", "recon"], ok=["o-d", "o-p", "r-o", "r-p"],
   notes=[(900, 440, 640, "Freeze before calling the provider. Authorize, then capture. Silence is unknown, not failed.", "green")])
sv("ch4-attack.svg", 545, upto=3, attack=["db"], keep=["fans", "edge", "api", "db"], hot=["f-e", "e-a", "a-d"],
   notes=[(560, 470, 760, "33,000 contended writes a second on 50,000 rows. The pool empties; retries make it worse.", "red")])
sv("ch4-fix.svg", 545, upto=3, show=["ch4"], fix=["wr", "ctrl"], keep=["fans", "edge", "wr", "ctrl", "api", "db"], ok=["e-w", "c-w", "e-a"],
   notes=[(560, 470, 760, "A line in front, admitted at a rate chosen from shop health. The core sees only what it admits.", "green")])
sv("ch5-attack.svg", 545, upto=3, attack=["wr"], keep=["fans", "edge", "wr"], hot=["f-e", "e-w"],
   notes=[(560, 470, 760, "Strict first-come at T0: data-centre bots with 5 ms latency take the first places.", "red")])
sv("ch5-fix.svg", 545, upto=3, fix=["wr", "edge"], keep=["fans", "edge", "wr"], ok=["f-e", "e-w"],
   notes=[(560, 470, 760, "A lottery for everyone present at T0; one entry per verified account; signed, short-lived tokens.", "green")])
sv("ch6-attack.svg", 545, upto=3, attack=["db"], keep=["fans", "edge", "api", "db"], hot=["a-d", "e-a"],
   notes=[(560, 470, 760, "5,000 map reads a second hit the same rows the claims are locking.", "red")])
sv("ch6-fix.svg", 545, upto=3, fix=["bm", "sb"], keep=["edge", "bm", "sb", "log", "db"], ok=["e-b", "s-b", "l-s", "d-l"],
   notes=[(560, 470, 760, "Layout on the CDN; availability as a bitmap built from the event log, served by version.", "green")])
sv("ch7-attack.svg", 545, upto=3, show=["ch7"], attack=["bm", "wr", "edge"], keep=["db", "edge", "bm", "wr"], hot=["e-b", "e-w"],
   notes=[(560, 470, 760, "5,000 seats appear while the map is cached and 970,000 fans have been told it is sold out.", "red")])
sv("ch7-fix.svg", 545, upto=3, show=["ch7"], fix=["wl", "db"], keep=["api", "db", "log", "wl"], ok=["l-wl", "d-l"],
   notes=[(40, 470, 700, "New rows in one transaction, a new layout version, the flag cleared. A new consumer.", "green")])
sv("ch8-attack.svg", 545, upto=3, attack=["api"], keep=["edge", "api", "db"], hot=[],
   notes=[(560, 470, 760, "The dashboard is green. Two thousand seats sit frozen on unknown payments and the line has stopped.", "red")])
sv("ch8-fix.svg", 700, upto=3, show=["ch8"], fix=["mon"], keep=["fans", "mon", "edge", "api", "db"], ok=["m-f"],
   notes=[(560, 470, 760, "Measure the promise: a synthetic fan, seats frozen and their age, hold latency against admission.", "green")])
bs.budget_bar(OUT / "budget.svg", [("gateway", 20, "edge"), ("token + limits", 10, "service"), ("lock + claim", 40, "data"), ("outbox", 10, "queue"), ("return", 20, "edge")],
              total=300, unit="ms", title="One hold request, p99 planning budget (initial target 300 ms)")

# ───────────────────────────── conceptual model (Chen) and the central-tension funnel ─────────────────────────
import erdsvg as er
c = er.Chen(1600, 900, size=26)
c.entity("ev", 140, 120, "EVENT"); c.entity("se", 640, 120, "SEAT"); c.entity("ho", 1140, 120, "HOLD")
c.entity("fa", 140, 540, "FAN"); c.entity("ti", 640, 540, "TICKET"); c.entity("or", 1140, 540, "ORDER")
c.entity("pa", 1140, 780, "PAYMENT ATTEMPT", weak=True)
c.rel("has", 390, 120, "HAS"); c.rel("hb", 890, 120, "HELD BY"); c.rel("bc", 1140, 330, "BECOMES")
c.rel("jn", 140, 330, "JOINS"); c.rel("is", 890, 540, "ISSUES"); c.rel("fo", 640, 330, "FOR")
c.rel("tr", 1140, 660, "TRIED AS", identifying=True)
c.attr("eid", 140, 40, "event_id", of="ev", key=True)
c.attr("sid", 640, 40, "seat_id", of="se", key=True); c.attr("st", 500, 200, "state", of="se")
c.attr("hid", 1140, 40, "hold_id", of="ho", key=True); c.attr("ex", 1350, 120, "expires_at", of="ho")
c.attr("oid", 1370, 540, "order_id", of="or", key=True)
c.attr("bar", 640, 620, "barcode", of="ti")
c.link("ev", "has", "1"); c.link("has", "se", "N", total=True)
c.link("se", "hb", "N"); c.link("hb", "ho", "1")
c.link("ho", "bc", "1", src="b", dst="t"); c.link("bc", "or", "1", src="b", dst="t")
c.link("fa", "jn", "N", src="t", dst="b"); c.link("jn", "ev", "M", src="t", dst="b")
c.link("or", "is", "1"); c.link("is", "ti", "N")
c.link("ti", "fo", "1", src="t", dst="b"); c.link("fo", "se", "1", src="t", dst="b")
c.link("or", "tr", "1", src="b", dst="t"); c.link("tr", "pa", "N", src="b", dst="t")
c.legend(1380, 700)
c.note(180, 800, 800, "A seat has at most one live hold; the seat row is the truth, the hold row is bookkeeping.")
c.save(OUT / "erd-chen.svg")

import html
FONT = "Inter, Helvetica, Arial, sans-serif"
def esc(t): return html.escape(str(t))
def tension():
    W, H = 1600, 640
    def tx(x, y, t, sz=30, w=700, fill="#0b2540", anchor="middle"):
        return f'<text x="{x}" y="{y}" font-family="{FONT}" font-size="{sz}" font-weight="{w}" fill="{fill}" text-anchor="{anchor}">{esc(t)}</text>'
    stages = [("At the door", "1,000,000 fans", "edge · cached · cheap", 420, "#cfe3fb", "#215a9a"),
              ("In the shop", "10,000 shoppers", "map · hold · pay", 250, "#e6dcfb", "#6b4fc4"),
              ("Hold writes", "~50 / s", "one primary", 140, "#d3f3e6", "#1f8a63"),
              ("Orders", "20,000", "2 % of the door", 70, "#fde3cf", "#c26a1b")]
    x0, gap, w = 40, 14, 360
    out = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}">', f'<rect width="{W}" height="{H}" fill="#fff"/>']
    cy = 270
    for i, (t, n, s, hh, fill, stroke) in enumerate(stages):
        x = x0 + i * (w + gap); nxt = stages[i + 1][3] if i + 1 < len(stages) else hh * 0.6
        pts = f"{x},{cy-hh/2} {x+w},{cy-nxt/2} {x+w},{cy+nxt/2} {x},{cy+hh/2}"
        out.append(f'<polygon points="{pts}" fill="{fill}" stroke="{stroke}" stroke-width="3"/>')
        if i == 3: out.append(tx(x + w / 2, cy - hh / 2 - 22, n, 34)); out.append(tx(x + w / 2, cy + hh / 2 + 34, s, 24, 500, "#3a424a"))
        else: out.append(tx(x + w / 2, cy - 6, n, 34)); out.append(tx(x + w / 2, cy + 34, s, 24, 500, "#3a424a"))
        out.append(tx(x + w / 2, 520 if False else 60, t, 30, 700, stroke))
    out.append(f'<line x1="60" y1="590" x2="{W-60}" y2="590" stroke="#c8341f" stroke-width="3" marker-start="url(#a)" marker-end="url(#a)"/>')
    out.append('<defs><marker id="a" viewBox="0 0 10 10" refX="5" refY="5" markerWidth="9" markerHeight="9" orient="auto-start-reverse"><path d="M0,0 L10,5 L0,10 z" fill="#c8341f"/></marker></defs>')
    out.append(tx(70, 570, "fairer, costlier to run", 24, 600, "#24292f", "start")); out.append(tx(W - 70, 570, "cheaper, needs a product rule", 24, 600, "#24292f", "end"))
    out.append(tx(W / 2, 626, "strict first-come  ←  how the line is ordered  →  random among early arrivals", 26, 700, "#c8341f"))
    out.append(tx(W / 2, 450, "Admitted at a rate the shop chooses. The rest wait, or are told early.", 26, 500, "#24292f"))
    out.append("</svg>")
    (OUT / "tension.svg").write_text("\n".join(out))
tension()


# crop a saved view to a band (the boxes do not move; only the window does)
def crop(name, y0, h=None, w=None):
    p = OUT / name; t = p.read_text()
    m = re.search(r'viewBox="0 0 (\d+) (\d+)" width="\d+" height="\d+"', t)
    w0, hh = int(m.group(1)), int(m.group(2)); h = h or hh - y0; w = w or w0
    t = t.replace(m.group(0), f'viewBox="0 {y0} {w} {h}" width="{w}" height="{h}"', 1)
    p.write_text(t)
import re
crop("base-v1.svg", 255, 215, w=1240)
crop("base-v2.svg", 255, 505)
crop("ch2-fix.svg", 250, 650)
crop("ch3-fix.svg", 240, 660)

# the view box is a window, not a clip: draw nothing outside it (a dimmed node below the crop must not show)
def clipview(p):
    t = p.read_text()
    m = re.search(r'viewBox="(\d+) (\d+) (\d+) (\d+)"', t)
    if not m or "vbclip-" in t: return
    x, y, w, h = m.groups()
    cid = "vbclip-" + p.stem
    t = t.replace("</defs>", f'<clipPath id="{cid}"><rect x="{x}" y="{y}" width="{w}" height="{h}"/></clipPath></defs><g clip-path="url(#{cid})">', 1)
    t = t[:t.rindex("</svg>")] + "</g></svg>"
    p.write_text(t)
for p in sorted(OUT.glob("base-*.svg")) + sorted(OUT.glob("flow-fr*.svg")) + sorted(OUT.glob("ch[1-8]-*.svg")) + [OUT / "map.svg"]:
    clipview(p)
