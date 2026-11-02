#!/usr/bin/env python3
"""C4, sequence, state and follow-up diagrams for the SD-47 ticket-booking video → ./svg/*.svg.
Generators: ~/.claude/skills/slide-video-kit/scripts/{c4svg,seqsvg}.py.  Run: python3 diagrams.py"""
import pathlib, sys
sys.path.insert(0, str(pathlib.Path.home() / ".claude/skills/slide-video-kit/scripts"))
import c4svg as c4, seqsvg as sq
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

# ── Follow-up 1: fairness ────────────────────────────────────────────────────────────────────────
d = c4.Diagram(1600, 540)
d.text(40, 40, "THREE OPTIONS, WITH THEIR CONSEQUENCES — THE PROMOTER DECIDES", 17, "#8c959f", True)
d.node("fifo", 40, 70, 480, 220, "ext", "Strict FIFO at T0", "Option A",
       "Rewards the lowest latency and the best bots. Looks fair, isn't.", size=27)
d.node("lot", 560, 70, 480, 220, "focus", "Lottery among the lobby", "Option B · recommended",
       "Everyone present at T0 has the same chance. Then FIFO for late arrivals.", size=27)
d.node("reg", 1080, 70, 480, 220, "container", "Verified pre-registration", "Option C · flagship events",
       "Fans screened days ahead. Slower, the strongest against bots.", size=27)
d.note(40, 330, 1520, "What I bring: the data from the last on-sale (bot share, latency spread), the rules written "
       "in plain words, and how each fan learns their position early. What I don't do: decide fairness alone.", size=19)
d.note(40, 440, 1520, "Then: publish the rules before the sale, measure complaints and bot cancellations after, "
       "and revisit with the promoter.", size=19, colour="#2d8a4e", bg="#e7f4ec")
d.save(OUT / "fu-fairness.svg")

# ── Follow-up 2: the primary fails mid-sale ──────────────────────────────────────────────────────
d = c4.Diagram(1600, 640)
steps = [("t0", "0–5 s", "Detect", "hold p99 and errors spike; on-call paged"),
         ("t1", "5–30 s", "Queue absorbs it", "controller cuts R to the floor; the line pauses"),
         ("t2", "~30 s", "Failover", "synchronous replica promoted; nothing acknowledged is lost"),
         ("t3", "1–5 min", "Slow restart", "R ramps again from slow start; shoppers retry with jitter"),
         ("t4", "same day", "Verify", "invariant monitor clean; PAYMENT_PENDING ages normal")]
for i, (nid, t, h, desc) in enumerate(steps):
    d.node(nid, 30 + i * 314, 80, 280, 220, "focus" if i == 1 else "container", h, t, desc, size=25)
for a, b in zip([s_[0] for s_ in steps], [s_[0] for s_ in steps][1:]):
    d.edge(a, b, "", src="r", dst="l", dashed=False)
d.note(30, 360, 1540, "Comms: a status line on the waiting page ('the line has paused'), the promoter told within "
       "minutes, support given the script. Nobody is told 'sold out' because of our outage.", size=19)
d.note(30, 470, 1540, "Week after: blameless review; game day before the next big sale — kill the primary, stop the "
       "sweeper, slow the PSP, kill the controller's leader.", size=19, colour="#2d8a4e", bg="#e7f4ec")
d.save(OUT / "fu-failover.svg")

# ── Follow-up 3: three teams, twelve weeks ───────────────────────────────────────────────────────
d = c4.Diagram(1600, 660)
cols = ["Weeks 1–4", "Weeks 5–8", "Weeks 9–12"]
for i, c in enumerate(cols):
    d.text(420 + i * 390, 40, c.upper(), 17, "#8c959f", True, "middle")
rows = [("Edge & waiting room", ["FIFO queue, admission JWT", "lobby + lottery, CDN state", "bot defence, load test 1M"]),
        ("Inventory & orders", ["claim, holds, lazy expiry", "freeze, authorize → capture", "invariant monitor, game day"]),
        ("Payments", ["PSP adapter, idempotency", "unknown outcome, reconciler", "second PSP for failover"])]
for r, (team, cells) in enumerate(rows):
    y = 70 + r * 160
    d.text(30, y + 70, team, 20, "#24292f", True)
    for i, c in enumerate(cells):
        kind = "focus" if (r == 1 and i == 2) else ("component" if i == 0 else "container")
        d.node(f"c{r}{i}", 240 + i * 390, y, 360, 120, kind, c, "", size=20)
d.note(240, 560, 1140, "Contracts between teams: the event stream and the admission token. Never cut: the invariant "
       "monitor.", size=19)
d.save(OUT / "fu-roadmap.svg")

# ── Follow-up 4: the CDN bill ────────────────────────────────────────────────────────────────────
d = c4.Diagram(1600, 620)
d.text(40, 40, "\"THE CDN BILL FOR ONE ON-SALE WAS 3× THE FORECAST\": SLICE BEFORE YOU GUESS", 17, "#8c959f", True)
sl = [("p", "By path", "queue/state, layout, availability"), ("v", "By client version", "a release polling every 1 s?"),
      ("b", "By bot score", "headless clients polling flat out"), ("c", "Cause", "polling rate × size × audience")]
for i, (nid, h, desc) in enumerate(sl):
    d.node(nid, 40 + i * 390, 70, 340, 160, "focus" if i == 3 else "container", h, "", desc, size=26)
for a, b in zip("pvb", "vbc"):
    d.edge(a, b, "", src="r", dst="l", dashed=False)
d.note(40, 290, 740, "Contain: block flagged bots at the WAF, raise the poll interval server-side "
       "(it travels in the state JSON), roll back the client.", size=19, colour="#c8341f", bg="#fdecea")
d.note(820, 290, 740, "Fix: adaptive polling — fans far back poll every 60 s; a cost forecast per on-sale "
       "reviewed with finance; an alert on edge requests per waiting fan.", size=19, colour="#2d8a4e", bg="#e7f4ec")
d.save(OUT / "fu-cdn-cost.svg")

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
