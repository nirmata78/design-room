#!/usr/bin/env python3
"""Part 6 figures (diagrams/p06.md). Run: python3 diagrams_p06.py [name …] → svg/p6-*.svg"""
import math, sys
from dg import *

SH = [BLUE, GREEN, AMBER, BLUEGREY]


# ---------------------------------------------------------------- p6-hash-range
def hash_range():
    W, H = 1600, 700
    b = [panel(20, 20, 760, 660, "grey"), panel(820, 20, 760, 660, "grey")]
    b.append(title(400, 70, "Range", 28, INK, "middle")); b.append(title(1200, 70, "Hash", 28, INK, "middle"))
    x0, lw = 70, 26
    def LX(i): return x0 + i * lw
    segs = [(0, 6, "shard 1", "A–F"), (6, 13, "shard 2", "G–M"), (13, 19, "shard 3", "N–S"), (19, 26, "shard 4", "T–Z")]
    for k, (a, z, n, r) in enumerate(segs):
        b.append(bar(LX(a) + 2, 320, LX(z) - LX(a) - 4, 50, "", SH[k]))
        b.append(mtext((LX(a) + LX(z)) / 2, 410, [n, r], 22, SH[k], "middle", 700))
    for i, ch in enumerate("ABCDEFGHIJKLMNOPQRSTUVWXYZ"):
        b.append(text(LX(i) + lw / 2, 352, ch, 18 if False else 21, "#fff", "middle", 700))
    b.append(bracket(LX(2) + 2, LX(5) - 2, 300, "", INK))
    b.append(text((LX(2) + LX(5)) / 2, 270, "C … E", 22, INK, "middle", 700))
    b.append(text((LX(2) + LX(5)) / 2 + 30, 560, "scan → one shard", 24, GREEN, "middle", 800))
    b.append(line((LX(2) + LX(5)) / 2, 470, (LX(2) + LX(5)) / 2, 530, GREEN, 2.5, "4 4"))
    # right
    keys = ["ann", "bob", "cat", "dan"]
    dest = [2, 0, 3, 1]
    for i, k in enumerate(keys):
        y = 150 + i * 105
        b.append(text(880, y + 8, k, 24, INK, "start", 700))
        b.append(box(960, y - 24, 110, 48, "hash()", GREY, size=21))
    b.append(text(905, 150 + 4 * 105 - 10, "…", 30, INK, "middle", 700))
    for s in range(4):
        b.append(box(1330, 120 + s * 110, 190, 66, f"shard {s + 1}", SH[s], size=22))
    for i, d in enumerate(dest):
        y = 150 + i * 105
        b.append(line(1072, y, 1326, 153 + d * 110, SH[d], 3, "", True))
    b.append(vbracket(1545, 120, 120 + 3 * 110 + 66, RED, True, 14))
    b.append(text(1200, 610, "scan C … E → every shard", 26, RED, "middle", 800))
    return svg(W, H, b)


# ---------------------------------------------------------------- p6-mod-n
def mod_n():
    W, H = 1600, 640
    x0, cw = 330, 60
    b = [text(40, 168, "key hash h", 22, MUTED, "start", 700)]
    rows = [("4 nodes: h mod 4", 4, 240), ("5 nodes: h mod 5", 5, 340)]
    for h in range(20):
        same = h % 4 == h % 5
        col = GREEN if same else RED
        x = x0 + h * cw
        b.append(rect(x + 3, 200, cw - 6, 210, "#dff3e4" if same else "#fde7e9", col, 2, 6))
        b.append(text(x + cw / 2, 168, str(h), 22, INK, "middle", 700))
        for _, m, y in rows:
            b.append(text(x + cw / 2, y + 22, str(h % m), 26, col, "middle", 800))
    for lab, _, y in rows:
        b.append(text(40, y + 22, lab, 22, INK, "start", 700))
    b.append(text(x0, 450, "green: same node under both · red: the key moves", 21, MUTED, "start", 600))
    b.append(text(W / 2, 560, "4 of 20 stay · 80% move to add 20% capacity", 30, RED, "middle", 800))
    return svg(W, H, b)


# ---------------------------------------------------------------- p6-ring
def ring():
    W, H = 1600, 820
    cx, cy, R = 800, 390, 300
    nodes = {"A": -90, "B": 0, "E": 45, "C": 90, "D": 180}
    col = {"A": BLUE, "B": GREEN, "C": AMBER, "D": BLUEGREY, "E": RED}
    def P(a, r=R): return cx + r * math.cos(math.radians(a)), cy + r * math.sin(math.radians(a))
    b = [f'<circle cx="{cx}" cy="{cy}" r="{R}" fill="none" stroke="#d0d7de" stroke-width="6"/>']
    # highlighted arc B → E
    x1, y1 = P(0); x2, y2 = P(45)
    b.append(f'<path d="M{x1:.1f},{y1:.1f} A{R},{R} 0 0 1 {x2:.1f},{y2:.1f}" fill="none" stroke="{RED}" stroke-width="14" stroke-opacity="0.35"/>')
    order = sorted(nodes.items(), key=lambda kv: kv[1] % 360)
    def owner(a):
        a %= 360
        for n, na in order:
            if na % 360 >= a:
                return n
        return order[0][0]
    for k in range(26):
        a = -84 + k * 13.6 + (5 if k % 3 == 0 else 0)
        if any(abs(((a - na) + 180) % 360 - 180) < 6 for na in nodes.values()):
            continue
        x, y = P(a)
        b.append(dot(x, y, 10, col[owner(a)]))
    for n, a in nodes.items():
        x, y = P(a)
        new = n == "E"
        b.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="40" fill="#fff" stroke="{col[n]}" stroke-width="{6 if new else 4}"/>')
        b.append(text(x, y + 11, n, 32, col[n], "middle", 800))
    lx, ly = P(22, R + 70)
    b.append(text(lx + 10, ly + 8, "only these keys move: C → E", 24, RED, "start", 800, True))
    ex, ey = P(45, R + 64)
    b.append(text(ex + 10, ey + 26, "new node E", 22, RED, "start", 700, True))
    b.append(text(60, 120, "a key belongs to the next node clockwise", 22, MUTED, "start", 600))
    b.append(text(W / 2, 790, "add 1 node to 4 → about 1/5 of keys move", 28, INK, "middle", 800))
    return svg(W, H, b)


# ---------------------------------------------------------------- p6-split
def split():
    W, H = 1600, 680
    b = [text(40, 146, "server 3", 22, MUTED, "start", 700)]
    b.append(bar(200, 100, 900, 70, "", BLUE)); b.append(text(222, 144, "range A–M · 520 MB · 9k req/s", 24, "#fff", "start", 700))
    b.append(line(650, 80, 650, 190, RED, 4, "8 6"))
    b.append(text(650, 70, "cut at G", 22, RED, "middle", 700))
    b.append(arrow(650, 200, 650, 296, colour=INK, w=3, lines=["split = metadata only"], weight=700))
    b.append(rect(170, 300, 960, 120, "#f6f8fa", GREY, 2, 12))
    b.append(text(40, 368, "server 3", 22, MUTED, "start", 700))
    b.append(bar(200, 325, 440, 70, "A–G", BLUE, 24)); b.append(bar(660, 325, 440, 70, "G–M", BLUE, 24))
    b.append(rect(1180, 90, 380, 330, "#fff", INK, 2, 10))
    b.append(text(1370, 130, "shard map v21 → v22", 22, INK, "middle", 700))
    b.append(text(1200, 185, "v21", 21, MUTED, "start", 700))
    b.append(text(1260, 185, "A–M → server 3", 22, RED, "start", 600)); b.append(line(1256, 178, 1440, 178, RED, 2.5))
    b.append(text(1200, 260, "v22", 21, MUTED, "start", 700))
    b.append(text(1260, 260, "A–G → server 3", 22, GREEN, "start", 600))
    b.append(text(1260, 300, "G–M → server 3", 22, GREEN, "start", 600))
    b.append(box(1000, 560, 260, 80, "server 8", GREY))
    b.append(path("M880,397 L880,600 L996,600", MUTED, 2.5, "9 7", True))
    b.append(text(870, 520, "later: balancer moves it", 21, MUTED, "end", 600, True))
    return svg(W, H, b)


# ---------------------------------------------------------------- p6-move
def move():
    s = Seq(1600, y0=20, row=60, headh=60)
    s.part("a", "Server 1 (owner)"); s.part("b", "Server 2 (target)", GREEN); s.part("m", "Shard map", GREY); s.part("c", "Client", GREY)
    s.msg("a", "b", "① snapshot of range (throttled)")
    s.msg("a", "b", "② stream new writes")
    s.msg("c", "a", "write (continues to succeed)")
    s.note("a", "a", "③ pause writes · drain last ones", "red")
    s.msg("a", "m", "owner = S2 · v23")
    s.msg("c", "a", "write")
    s.msg("a", "c", "moved, v23", dash=True, colour=AMBER)
    s.msg("c", "b", "write ✓", colour=GREEN)
    s.note("a", "a", "④ delete copy later", "grey")
    body = s.body()
    return svg(1600, max(760, int(s.y + 20)), [body])


# ---------------------------------------------------------------- p6-routing
def routing():
    W, H = 1600, 700
    b = []
    specs = [("any node forwards", [("Client", GREY), ("node B", BLUE), ("node D (owner)", GREEN)], 1, ["", "forward"]),
             ("routing tier", [("Router (holds map)", AMBER), ("node D", GREEN)], 0, [""]),
             ("smart client", [("Client (holds map)", AMBER), ("node D", GREEN)], 0, [""])]
    holders_y = []
    for k, (ttl, boxes, holder, labs) in enumerate(specs):
        px = 20 + k * 530
        b.append(panel(px, 20, 510, 540, "grey"))
        b.append(title(px + 255, 64, ttl, 26, INK, "middle"))
        if k == 1:
            boxes = [("Client", GREY)] + boxes; holder = 1; labs = ["", ""]
        n = len(boxes); ys = [100 + i * (420 / n + (30 if n == 2 else 0)) for i in range(n)]
        if n == 2:
            ys = [120, 400]
        else:
            ys = [100, 250, 420]
        for i, (lab, c) in enumerate(boxes):
            b.append(box(px + 130, ys[i], 300, 80, lab, c, size=22))
            if i:
                b.append(arrow(px + 280, ys[i - 1] + 82, px + 280, ys[i] - 4, colour=INK, w=3,
                               lines=[labs[i - 1]] if labs[i - 1] else None, weight=600))
        hy = ys[holder] + 40
        b.append(path(f"M{px + 70},600 L{px + 70},{hy} L{px + 126},{hy}", MUTED, 2.5, "9 7", True))
        b.append(text(px + 62, (600 + hy) / 2 + 60, "push map", 21, MUTED, "end" if False else "start", 700, True,
                      extra=f' transform="rotate(-90 {px + 62} {(600 + hy) / 2 + 60})"'))
    b.append(box(40, 600, 1520, 80, "Coordination service · shard map", GREY, size=24))
    return svg(W, H, b)


# ---------------------------------------------------------------- p6-indexes
def indexes():
    W, H = 1600, 760
    b = [panel(20, 20, 760, 720, "grey"), panel(820, 20, 760, 720, "grey")]
    b.append(title(400, 64, "Local index", 26, INK, "middle")); b.append(title(1200, 64, "Global index (by colour)", 26, INK, "middle"))
    b.append(box(260, 100, 280, 64, "colour = red", RED, size=22))
    shards = [["p3 red · p5 blue", "p9 red", "red → 3, 9"], ["p7 red · p8 green", "", "red → 7"], ["p12 blue · p15 red", "", "red → 15"]]
    for i, (d1, d2, ix) in enumerate(shards):
        x = 40 + i * 245
        b.append(rect(x, 260, 230, 220, "#ddeaf8", BLUE, 2.5))
        b.append(text(x + 115, 296, f"shard {i + 1}", 22, INK, "middle", 700))
        b.append(mtext(x + 115, 334, [d1] + ([d2] if d2 else []), 20 if False else 21, INK, "middle"))
        b.append(rect(x + 15, 400, 200, 56, "#fff", AMBER, 2, 6))
        b.append(text(x + 115, 436, ix, 21, INK, "middle", 700))
        b.append(line(400, 166, x + 115, 256, RED, 3, "", True))
        b.append(line(x + 115, 482, 400, 576, MUTED, 2.5, "", True))
    b.append(box(260, 580, 280, 70, "merge", GREY, size=22))
    b.append(text(400, 700, "every query visits every shard", 22, RED, "middle", 700))
    # global
    for i in range(3):
        x = 850 + i * 240
        b.append(box(x, 230, 220, 90, [f"shard {i + 1}"] + (["product 7"] if i == 1 else []), BLUE, size=22))
    b.append(box(870, 490, 280, 80, "colours a–m", AMBER, size=22))
    b.append(box(1270, 490, 280, 80, "colours n–z", AMBER, size=22))
    b.append(arrow(1200, 120, 1200, 226, colour=BLUE, w=3, lines=["write product 7 (red)"], weight=600))
    b.append(line(1250, 322, 1380, 486, MUTED, 3, "10 7", True))
    b.append(text(1330, 400, "async update", 21, MUTED, "start", 700, True))
    b.append(box(1270, 640, 280, 64, "colour = red", BLUE, size=22))
    b.append(line(1410, 638, 1410, 574, BLUE, 3, "", True))
    b.append(text(1010, 680, "one index shard", 22, BLUE, "middle", 700))
    return svg(W, H, b)


# ---------------------------------------------------------------- p6-domains
def domains():
    W, H = 1600, 760
    b = []
    for k, ttl in enumerate(("random", "domain-aware")):
        px = 20 + k * 800
        b.append(title(px + 380, 56, ttl, 28, INK, "middle"))
        for r in range(3):
            x = px + 20 + r * 250
            if k == 1:
                b.append(rect(x - 8, 90, 236, 470, "none", MUTED, 2.5, 14, "10 7"))
                b.append(text(x + 110, 548, f"zone {'abc'[r]}", 22, MUTED, "middle", 700))
            b.append(rect(x, 120, 220, 390, "#f6f8fa", GREY, 2.5, 10))
            b.append(text(x + 110, 152, f"rack {r + 1}", 22, INK, "middle", 700))
            b.append(bar(x + 20, 170, 180, 34, "switch", GREY, 20))
            for m in range(4):
                mx, my = x + 25 + (m % 2) * 90, 240 + (m // 2) * 120
                has = (k == 0 and r == 0 and m < 3) or (k == 1 and m == (r % 2))
                b.append(rect(mx, my, 80, 90, "#fde7e9" if (has and r == 0) else ("#ddeaf8" if has else "#fff"),
                              RED if (has and r == 0) else (BLUE if has else GREY), 2.5, 6))
                if has:
                    b.append(text(mx + 40, my + 54, "r42", 22, RED if r == 0 else BLUE, "middle", 800))
        b.append(cross(px + 130, 187, 22, RED, 7))
        cap = "one switch → range 42 lost" if k == 0 else "two copies remain"
        b.append(text(px + 380, 650, cap, 28, RED if k == 0 else GREEN, "middle", 800))
    b.append(line(800, 40, 800, 720, "#d0d7de", 2))
    return svg(W, H, b)


FIGS = {"p6-hash-range": hash_range, "p6-mod-n": mod_n, "p6-ring": ring, "p6-split": split, "p6-move": move,
        "p6-routing": routing, "p6-indexes": indexes, "p6-domains": domains}

if __name__ == "__main__":
    save(FIGS, sys.argv[1:])
