#!/usr/bin/env python3
"""Part 11 figures (diagrams/p11.md). Run: python3 diagrams_p11.py [name …] → svg/p11-*.svg"""
import math, sys
from dg import *


# ---------------------------------------------------------------- p11-dns-anycast
def dns_anycast():
    W, H = 1600, 820
    b = []
    for k, t in enumerate(("DNS", "Geo DNS", "Anycast")):
        y = 20 + k * 270
        b.append(panel(20, y, 1560, 250, "grey"))
        b.append(title(40, y + 40, t, 26))
    y = 90
    b.append(box(60, y, 180, 70, "client", GREY, size=22))
    b.append(box(380, y, 360, 70, "resolver (caches for TTL)", BLUE, size=22))
    b.append(box(880, y, 300, 70, "authoritative DNS", BLUE, size=22))
    b.append(arrow(242, y + 35, 376, y + 35, colour=INK, w=3)); b.append(arrow(742, y + 35, 876, y + 35, colour=INK, w=3))
    b.append(arrow(1182, y + 35, 1300, y + 35, colour=GREEN, w=3))
    b.append(text(1310, y + 43, "203.0.113.10", 24, GREEN, "start", 800))
    y = 340
    b.append(box(60, y, 260, 70, "resolver EU", BLUE, size=22)); b.append(box(60, y + 100, 260, 70, "resolver US", BLUE, size=22))
    b.append(box(620, y + 50, 300, 70, "geo authoritative DNS", BLUE, size=22))
    b.append(line(322, y + 35, 616, y + 70, INK, 2.5, "", True)); b.append(line(322, y + 135, 616, y + 100, INK, 2.5, "", True))
    b.append(text(1000, y + 42, "EU resolver → EU site", 23, GREEN, "start", 800))
    b.append(text(1000, y + 142, "US resolver → US site", 23, GREEN, "start", 800))
    b.append(line(922, y + 70, 990, y + 35, GREEN, 2.5, "", True)); b.append(line(922, y + 100, 990, y + 135, GREEN, 2.5, "", True))
    y = 610
    sites = [("EU", 300), ("US", 700), ("Asia", 1100)]
    for n, x in sites:
        c = RED if n == "EU" else BLUE
        b.append(box(x, y, 200, 70, [f"{n} · 198.51.100.1"], c, size=21))
        b.append(line(x + 100, y - 4, x + 100, y - 40, c, 2.5, "6 4", True))
    b.append(text(700, y - 48, "BGP: every site announces 198.51.100.1", 21, MUTED, "middle", 700, True))
    b.append(cross(400, y + 35, 30, RED, 7))
    b.append(box(60, y + 10, 180, 60, "client", GREY, size=22))
    b.append(path(f"M240,{y + 60} C450,{y + 120} 650,{y + 120} 760,{y + 74}", GREEN, 3.5, "", True))
    b.append(mtext(1325, y + 6, ["EU: withdraw route", "→ traffic moves", "in seconds"], 22, RED, "start", 800))
    b.append(line(1336, y + 30, 510, y + 30, RED, 0))
    return svg(W, H, b)


# ---------------------------------------------------------------- p11-l4-l7
def l4_l7():
    W, H = 1600, 700
    b = [panel(20, 20, 760, 660, "grey"), panel(820, 20, 760, 660, "grey")]
    b.append(title(400, 64, "Layer 4: per connection", 26, INK, "middle")); b.append(title(1200, 64, "Layer 7: per request", 26, INK, "middle"))
    for side in (0, 1):
        ox = side * 800
        b.append(box(ox + 50, 180, 160, 70, "client 1", GREY, size=22)); b.append(box(ox + 50, 420, 160, 70, "client 2", GREY, size=22))
        for i in range(4):
            y = 130 + i * 120
            hot = side == 0 and i == 0
            b.append(box(ox + 560, y, 180, 70, f"backend {i + 1}", RED if hot else BLUE, size=21))
    b.append(line(212, 215, 556, 165, BLUE, 12)); b.append(line(212, 455, 556, 405, BLUE, 12))
    b.append(mtext(400, 610, ["backend 1: all requests of", "a long gRPC connection"], 22, RED, "middle", 800))
    b.append(box(1100, 280, 150, 110, ["L7", "proxy"], AMBER, size=24))
    b.append(line(1012, 215, 1096, 310, BLUE, 12)); b.append(line(1012, 455, 1096, 360, BLUE, 12))
    for i in range(4):
        y = 165 + i * 120
        for d in (-12, 0, 12):
            b.append(line(1252, 335 + d / 2, 1356, y + d, BLUE, 2, "", True))
    b.append(text(1200, 640, "requests spread evenly", 22, GREEN, "middle", 800))
    return svg(W, H, b)


# ---------------------------------------------------------------- p11-health
def health():
    W, H = 1600, 760
    b = [box(40, 260, 280, 110, "Load balancer", BLUE, size=26)]
    specs = [("backend 1", GREEN, ""), ("backend 2", GREEN, ""), ("backend 3", GREEN, ""),
             ("backend 4", RED, "fails probes → ejected"), ("backend 5", AMBER, "errors 5× peers → outlier ejected")]
    for i, (n, c, note) in enumerate(specs):
        y = 30 + i * 100
        b.append(box(560, y, 220, 70, n, c, size=22))
        b.append(line(322, 315, 556, y + 35, c, 2.5, "8 6" if c != GREEN else "", True))
        if note:
            b.append(text(800, y + 44, note, 22, c, "start", 800))
    b.append(box(560, 540, 220, 70, "backend 6", GREY, size=22))
    b.append(mtext(800, 548, ["① readiness fails  ② no new requests", "③ finish in-flight  ④ exit"], 22, INK, "start", 600))
    b.append(text(380, 160, "probes", 22, MUTED, "middle", 700))
    b.append(box(100, 650, 1400, 80, "panic threshold: if > 50% look unhealthy, send to all", RED, size=24, sw=4))
    return svg(W, H, b)


# ---------------------------------------------------------------- p11-gateway-bloat
def gateway_bloat():
    W, H = 1600, 640
    b = []
    items = [["TLS · auth · routing"], ["TLS · auth · routing", "transform for client X"],
             ["TLS · auth · routing", "transform for client X", "orchestrate A + B"]]
    x = 40
    for k, its in enumerate(items):
        w, h = 270 + k * 60, 160 + k * 80
        y = 420 - h
        b.append(rect(x, y, w, h, "#ddeaf8", BLUE, 2.5))
        b.append(text(x + w / 2, y + 36, "gateway", 22, INK, "middle", 800))
        for j, it in enumerate(its):
            red = it.startswith("orchestrate")
            b.append(box(x + 15, y + 60 + j * 74, w - 30, 58, it, RED if red else GREY, size=21, weight=600))
        b.append(text(x + w / 2, 470, f"year {k + 1}", 24, INK, "middle", 800))
        x += w + 60
    for i in range(8):
        tx, ty = 1240 + (i % 4) * 85, 170 + (i // 4) * 110
        b.append(f'<circle cx="{tx}" cy="{ty}" r="16" fill="{BLUEGREY}"/><path d="M{tx - 26},{ty + 50} Q{tx},{ty + 6} {tx + 26},{ty + 50} z" fill="{BLUEGREY}"/>')
    b.append(text(1370, 140, "teams queued", 21, MUTED, "middle", 700))
    b.append(mtext(1370, 560, ["every change needs", "a gateway deploy"], 26, RED, "middle", 800))
    b.append(arrow(1205, 260, 1156, 260, colour=RED, w=3))
    return svg(W, H, b)


# ---------------------------------------------------------------- p11-orphan-work
def orphan_work():
    W, H = 1600, 700
    def X(t): return 220 + t * 260
    lanes = {"Front end": 130, "A": 260, "B": 370, "C": 480}
    b = []
    for n, y in lanes.items():
        b.append(text(40, y + 8, n, 24, INK, "start", 700)); b.append(line(X(0), y, X(5.2), y, "#d0d7de", 2))
    b.append(bar(X(0), 130 - 22, X(1) - X(0), 44, "", BLUE))
    b.append(cross(X(1), 130, 18, RED, 6))
    b.append(text(X(1) + 30, 138, "timeout → error to user at 1.0 s", 22, RED, "start", 800))
    for n, st in (("A", 0.05), ("B", 0.1), ("C", 0.2)):
        y = lanes[n]
        b.append(bar(X(st), y - 20, X(1) - X(st), 40, "", BLUE))
        b.append(hatchbar(X(1), y - 20, X(5) - X(1), 40, "hatchred", RED))
    b.append(line(X(1), 80, X(1), 560, RED, 2.5, "6 5"))
    b.append(text(X(3), 560, "orphan work: nobody will read the answer", 26, RED, "middle", 800))
    b.append(line(X(0), 620, X(5.2), 620, MUTED, 2, arrow=True))
    for t in range(6):
        b.append(line(X(t), 612, X(t), 628, MUTED, 2)); b.append(text(X(t), 656, f"{t} s", 21, MUTED, "middle"))
    return svg(W, H, b)


# ---------------------------------------------------------------- p11-deadline
def deadline():
    s = Seq(1600, y0=20, row=66, headh=62)
    s.part("f", "Front end", GREY); s.part("a", "A"); s.part("b", "B"); s.part("c", "C")
    s.msg("f", "a", "deadline = now + 800 ms")
    s.msg("a", "b", "deadline same · 750 ms left")
    s.msg("b", "c", "670 ms left")
    s.msg("c", "b", "result (300 ms)", dash=True, colour=GREEN)
    s.note("f", "c", "alternative: the user gives up", "grey")
    s.msg("f", "a", "cancel", hl=True, dash=True)
    s.msg("a", "b", "cancel", hl=True, dash=True)
    s.msg("b", "c", "cancel", hl=True, dash=True)
    s.note("a", "c", "every hop stops", "red")
    body = s.body()
    return svg(1600, max(720, int(s.y + 20)), [body])


# ---------------------------------------------------------------- p11-offset
def offset():
    W, H = 1600, 720
    b = [title(260, 46, "page 1 (skip 0)", 26, INK, "middle"), title(1230, 46, "page 2 (skip 20), after 3 inserts", 26, INK, "middle")]
    def col(x, items, colours):
        o = []
        for i, (it, c) in enumerate(zip(items, colours)):
            yy = 80 + i * 30.5
            o.append(rect(x, yy, 300, 28, FILL[c], c, 1.5, 4))
            o.append(text(x + 150, yy + 22, it, 20 if False else 21, INK, "middle", 600))
        return "".join(o)
    b.append(col(110, [f"item {i}" for i in range(1, 21)], [BLUE] * 20))
    b.append(text(800, 120, "underlying list, newest first", 21, MUTED, "middle", 700))
    for i, n in enumerate(("new a", "new b", "new c")):
        b.append(box(690, 150 + i * 60, 220, 48, n, GREEN, size=22))
    b.append(text(800, 360, "inserted at the top", 22, GREEN, "middle", 800))
    items = [f"item {i}" for i in (18, 19, 20)] + [f"item {i}" for i in range(21, 38)]
    b.append(col(1080, items, [RED] * 3 + [BLUE] * 17))
    b.append(vbracket(1400, 80, 170, RED, True, 14))
    b.append(text(1420, 134, "seen again", 24, RED, "start", 800))
    return svg(W, H, b)


# ---------------------------------------------------------------- p11-conn-tier
def conn_tier():
    W, H = 1600, 760
    b = []
    for i, lab in enumerate(("phone", "laptop", "phone", "phone")):
        b.append(box(30, 60 + i * 110, 150, 64, lab, GREY, size=21))
    gws = [("gateway 1", 60), ("gateway 7", 250), ("…", 400), ("gateway 30", 520)]
    for lab, y in gws:
        if lab == "…":
            b.append(text(520, y + 30, "…", 34, INK, "middle", 800)); continue
        hl = lab == "gateway 7"
        b.append(box(420, y, 200, 80, lab, RED if hl else BLUE, size=22, sw=4 if hl else 2.5))
    for i in range(4):
        b.append(line(182, 92 + i * 110, 416, [100, 290, 290, 560][i], MUTED, 2, "", True))
    b.append(box(820, 60, 380, 110, ["Routing table", "user 42 → gw 7 (lease, heartbeat)"], AMBER, size=22))
    b.append(line(622, 270, 816, 140, AMBER, 3, "", True))
    b.append(text(680, 180, "register", 21, AMBER, "start", 700, True))
    b.append(box(1330, 300, 230, 80, "Services", GREY, size=22))
    b.append(box(900, 300, 260, 80, "Dispatcher", BLUE, size=22))
    b.append(arrow(1328, 340, 1164, 340, colour=INK, w=3))
    b.append(line(1030, 298, 1030, 174, AMBER, 3, "8 6", True)); b.append(text(1044, 240, "lookup", 21, AMBER, "start", 700, True))
    b.append(line(898, 330, 624, 300, RED, 4.5, "", True))
    b.append(text(760, 380, "push to user 42's connection", 22, RED, "middle", 800, True))
    b.append(line(418, 290, 184, 202, RED, 4.5, "", True))
    b.append(cross(520, 560, 34, RED, 7))
    b.append(mtext(660, 560, ["gateway 30 dies → 500k reconnect ·", "jittered over 30 s"], 22, RED, "start", 700))
    return svg(W, H, b)


# ---------------------------------------------------------------- p11-resumable
def resumable():
    s = Seq(1600, y0=20, row=60, headh=62)
    s.part("c", "Client", GREY); s.part("u", "Upload service")
    s.msg("c", "u", "start session"); s.msg("u", "c", "session URL", dash=True, colour=GREEN, num=False)
    s.msg("c", "u", "chunk 0–8 MB ✓", colour=GREEN)
    s.msg("c", "u", "chunk 8–16 MB ✓ …", colour=GREEN)
    s.lost("c", "u", "chunk", "connection drops")
    s.msg("c", "u", "how much do you have?", hl=True)
    s.msg("u", "c", "bytes 0–419,430,399", hl=True, dash=True, num=False)
    s.msg("c", "u", "resume from 419,430,400")
    s.msg("c", "u", "final chunk · checksum")
    s.msg("u", "c", "object complete", dash=True, colour=GREEN, num=False)
    body = s.body()
    return svg(1600, max(720, int(s.y + 20)), [body])


# ---------------------------------------------------------------- p11-trie
def trie():
    W, H = 1600, 720
    N = {"/": (300, 70), "api": (300, 220), "v1": (300, 370), "orders": (120, 560), "payments": (480, 560)}
    vals = {"api": "route A", "v1": "route B", "orders": "route C", "payments": "route D"}
    b = []
    for a, c in (("/", "api"), ("api", "v1"), ("v1", "orders"), ("v1", "payments")):
        on = c in ("api", "v1")
        b.append(line(N[a][0], N[a][1] + 36, N[c][0], N[c][1] - 36, RED if on else GREY, 5 if on else 2.5))
    for n, (x, y) in N.items():
        on = n in ("/", "api", "v1")
        b.append(box(x - 110, y - 36, 220, 72, [n] + ([f"value: {vals[n]}"] if n in vals else []), RED if on else BLUE, size=21, sw=4 if on else 2.5))
    b.append(path("M410,370 L760,370 L760,520", RED, 3, "10 7"))
    b.append(box(650, 520, 220, 70, "users ?", GREY, size=22, dash="8 6"))
    b.append(cross(760, 520, 18, RED, 5))
    b.append(text(780, 470, "no 'users' child", 22, RED, "start", 800))
    b.append(text(1000, 120, "query", 22, MUTED, "start", 700))
    b.append(text(1000, 160, "/api/v1/users", 30, RED, "start", 800))
    b.append(rect(940, 300, 620, 130, "#dff3e4", GREEN, 3))
    b.append(mtext(1250, 350, ["longest match:", "**/api/v1 → route B**"], 26, INK, "middle", 600))
    return svg(W, H, b)


FIGS = {"p11-dns-anycast": dns_anycast, "p11-l4-l7": l4_l7, "p11-health": health, "p11-gateway-bloat": gateway_bloat,
        "p11-orphan-work": orphan_work, "p11-deadline": deadline, "p11-offset": offset, "p11-conn-tier": conn_tier,
        "p11-resumable": resumable, "p11-trie": trie}

if __name__ == "__main__":
    save(FIGS, sys.argv[1:])
