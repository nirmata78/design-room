#!/usr/bin/env python3
"""Part 5 figures (diagrams/p05.md). Run: python3 diagrams_p05.py [name …] → svg/p5-*.svg"""
import math, sys
from dg import *


def strip(x, y, labels, w=110, h=64, fills=None, dashes=None, size=21):
    out = []
    for i, lab in enumerate(labels):
        f = fills[i] if fills else "#ddeaf8"
        d = dashes[i] if dashes else False
        out.append(rect(x + i * w, y, w, h, f if not d else "#fff", BLUE if not d else GREY, 2, 3, "6 5" if d else ""))
        if lab:
            out.append(text(x + i * w + w / 2, y + h / 2 + 8, lab, size, INK, "middle", 600))
    return "".join(out)


# ---------------------------------------------------------------- p5-async-tail
def async_tail():
    W, H = 1600, 640
    x0, w = 190, 110
    cells = [str(i) for i in range(90, 101)]
    b = [text(40, 196, "Leader log", 22, INK, "start", 700), text(40, 446, "Follower log", 22, INK, "start", 700)]
    b.append(strip(x0, 160, cells))
    b.append(rect(x0 + 6 * w, 160, 5 * w, 64, "none", RED, 4, 4))
    b.append(bracket(x0 + 6 * w + 4, x0 + 11 * w - 4, 140, "acknowledged to clients · not yet shipped", RED))
    b.append(strip(x0, 410, cells[:6] + [""] * 5, dashes=[False] * 6 + [True] * 5))
    b.append(arrow(x0 + 330, 228, x0 + 330, 404, colour=BLUE, w=3, lines=["async shipping"], weight=600))
    b.append(cross(x0 + 11 * w + 50, 192, 22, RED, 7))
    b.append(text(x0 + 11 * w + 50, 262, "leader dies", 22, RED, "middle", 700))
    b.append(mtext(800, 540, ["promote follower → writes 96–100 are gone ·", "the lag is your recovery point"], 24, RED, "middle", 700))
    return svg(W, H, b)


# ---------------------------------------------------------------- p5-lag-curve
def lag_curve():
    W, H = 1600, 640
    L, R, T, B = 170, 1520, 60, 520
    lo, hi = math.log10(0.004), math.log10(300)
    def X(h): return L + (R - L) * h / 24
    def Y(v): return B - (B - T) * (math.log10(v) - lo) / (hi - lo)
    b = [line(L, B, R, B, INK, 2), line(L, B, L, T - 10, INK, 2)]
    for v, lab in ((0.01, "0.01"), (0.1, "0.1"), (1, "1"), (10, "10"), (100, "100"), (300, "300")):
        b.append(line(L - 8, Y(v), R, Y(v), "#e6e9ec", 1.5)); b.append(text(L - 14, Y(v) + 8, lab, 21, INK, "end"))
    for h in range(0, 25, 3):
        b.append(line(X(h), B, X(h), B + 8, INK, 2)); b.append(text(X(h), B + 34, f"{h:02d}:00", 21, INK, "middle"))
    b.append(text((L + R) / 2, B + 70, "time of day", 22, MUTED, "middle", 600))
    b.append(f'<text transform="translate(44,{(T + B) / 2}) rotate(-90)" font-family="{FONT}" font-size="22" fill="{MUTED}" text-anchor="middle" font-weight="600">lag, seconds</text>')
    spikes = [(2, 240), (12, 40), (18, 15)]
    pts = []
    for i in range(0, 24 * 40 + 1):
        h = i / 40
        base = 0.01 * (1 + 0.55 * math.sin(h * 2.1) * math.cos(h * 0.7))
        lv = math.log10(base)
        for h0, pk in spikes:
            lv = max(lv, math.log10(base) + (math.log10(pk) - math.log10(base)) * math.exp(-((h - h0) / 0.32) ** 2))
        pts.append((X(h), Y(10 ** lv)))
    b.append(poly(pts, GREY, 3.5))
    labs = [(2, 240, "4 minutes · one long batch transaction"), (12, 40, "40 s · schema change rewrites a table"),
            (18, 15, "15 s · slow disk during backup")]
    for h, v, lab in labs:
        b.append(dot(X(h), Y(v), 8, RED))
        b.append(text(X(h) + 18, Y(v) + 8, lab, 21, RED, "start", 700, True))
    b.append(text(W / 2, 628, "lag is a distribution with causes, not one number", 24, INK, "middle", 700))
    return svg(W, H, b)


# ---------------------------------------------------------------- p5-dual-write
def dual_write():
    W, H = 1600, 800
    l = Seq(780, x0=20, y0=10, row=100, headh=70)
    l.part("s", "Service"); l.part("d", "Database", GREY); l.part("g", "Log", GREY)
    l.msg("s", "d", "", lines=["UPDATE order paid", "· COMMIT"])
    l.msg("d", "s", "ok", dash=True, colour=GREEN)
    l.note("s", "s", "crash", "red")
    l.lost("s", "g", "publish order.paid", "")
    l.note("s", "g", "paid, and nobody downstream knows", "red")
    r = Seq(780, x0=20, y0=10, row=100, headh=70)
    r.part("r1", "Request 1", GREY); r.part("r2", "Request 2", GREY); r.part("d", "Database", GREY); r.part("g", "Log", GREY)
    r.msg("r1", "d", "set A"); r.msg("r2", "d", "set B")
    r.note("d", "d", "ends with B", "grey")
    r.msg("r2", "g", "B"); r.msg("r1", "g", "A", hl=True)
    r.note("r1", "g", "database says B · index says A · for ever", "red")
    lb, rb = l.body("crash between the writes"), r.body("two requests race")
    return svg(W, H, [lb, line(800, 20, 800, H - 20, "#d0d7de", 2), f'<g transform="translate(800,0)">{rb}</g>'])


# ---------------------------------------------------------------- p5-outbox
def outbox():
    W, H = 1600, 720
    b = [box(30, 330, 180, 90, "Service")]
    b.append(rect(280, 180, 470, 440, "#f3f5f7", GREY, 2.5, 14)); b.append(text(515, 222, "Database", 24, INK, "middle", 700))
    b.append(rect(310, 270, 410, 280, "none", GREEN, 3, 10, "10 6"))
    b.append(text(515, 590, "① one transaction", 22, GREEN, "middle", 700))
    for y, head, row in ((290, "orders", "order 7 · paid"), (420, "outbox", "event e91 · key order 7 · payload")):
        b.append(rect(330, y, 370, 40, "#ddeaf8", BLUE, 2, 4)); b.append(text(345, y + 28, head, 21, INK, "start", 700))
        b.append(rect(330, y + 40, 370, 50, "#fff", BLUE, 2, 4)); b.append(text(515, y + 73, row, 21, INK, "middle"))
    b.append(arrow(212, 375, 306, 375, colour=BLUE, w=3))
    b.append(box(1010, 280, 230, 110, "Relay", AMBER))
    b.append(line(722, 310, 1006, 310, BLUE, 3, "", True)); b.append(text(864, 296, "② poll outbox", 21, BLUE, "middle", 700, True))
    b.append(line(752, 370, 1006, 370, BLUE, 3, "9 7", True)); b.append(text(880, 405, "or tail the WAL (CDC)", 21, BLUE, "middle", 600, True))
    b.append(path("M1125,278 L1125,110 L515,110 L515,176", MUTED, 2.5, "", True))
    b.append(text(820, 96, "④ mark sent / advance position", 21, MUTED, "middle", 700, True))
    b.append(box(1010, 520, 230, 90, "Log", GREY))
    b.append(arrow(1125, 392, 1125, 516, colour=BLUE, w=3, lines=["③ publish ·", "key = order 7"], weight=600))
    b.append(box(1340, 520, 220, 90, "Consumers", GREEN))
    b.append(arrow(1242, 565, 1336, 565, colour=BLUE, w=3))
    b.append(text(1450, 650, "dedup by event id", 21, GREEN, "middle", 700))
    return svg(W, H, b)


# ---------------------------------------------------------------- p5-multi-leader
def multi_leader():
    s = Seq(1600, y0=20, row=62, headh=60)
    s.part("ue", "User EU", GREY); s.part("le", "Leader EU"); s.part("lu", "Leader US"); s.part("uu", "User US", GREY)
    s.msg("ue", "le", "title = A"); s.msg("le", "ue", "ok", dash=True, colour=GREEN)
    s.msg("uu", "lu", "title = B · 80 ms later"); s.msg("lu", "uu", "ok", dash=True, colour=GREEN)
    s.cross("le", "lu", "A", "B", rows=1.6)
    s.note("le", "lu", "conflict found after both users saw success", "red")
    body = s.body()
    return svg(1600, max(720, int(s.y + 20)), [body])


# ---------------------------------------------------------------- p5-sloppy
def sloppy():
    W, H = 1600, 760
    cx, cy, R = 860, 360, 240
    pos = {f"n{i + 1}": (cx + R * math.cos(math.radians(-90 + 60 * i)), cy + R * math.sin(math.radians(-90 + 60 * i))) for i in range(6)}
    b = [f'<circle cx="{cx}" cy="{cy}" r="{R}" fill="none" stroke="#d0d7de" stroke-width="3"/>']
    co = (40, 40, 240, 90)
    b.append(box(*co, "Coordinator", GREY))
    def to(n, col, w=3, dash=""):
        x, y = pos[n]; sx, sy = co[0] + co[2], co[1] + co[3] / 2
        L = math.hypot(x - sx, y - sy); ux, uy = (x - sx) / L, (y - sy) / L
        return line(sx, sy, x - ux * 58, y - uy * 58, col, w, dash, True), (x - ux * 58, y - uy * 58)
    a1, e1 = to("n1", BLUE); a2, e2 = to("n2", BLUE)
    b += [a1, a2, path("M280,85 Q760,300 842,545", AMBER, 4.5, "", True)]
    for n, (x, y) in pos.items():
        home = n in ("n1", "n2", "n3")
        b.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="50" fill="{"#ddeaf8" if home else "#fff"}" stroke="{BLUE if home else GREY}" stroke-width="3"/>')
        b.append(text(x, y + 9, n, 24, INK, "middle", 700))
    b.append(tick(e1[0] - 30, e1[1] + 6)); b.append(tick(e2[0] - 34, e2[1] + 18))
    x3, y3 = pos["n3"]
    b.append(cross(x3, y3, 34, RED, 6)); b.append(text(x3 + 64, y3 + 8, "down", 22, RED, "start", 700))
    b.append(text(636, 322, "write + hint: belongs to n3", 22, AMBER, "end", 700, True))
    x4, y4 = pos["n4"]
    b.append(path(f"M{x4 + 50},{y4 - 4} Q{x3 + 120},{y4 + 30} {x3 + 30},{y3 + 44}", GREEN, 3, "10 7", True))
    b.append(text(1110, 650, "hinted handoff when n3 returns", 22, GREEN, "start", 700, True))
    b.append(text(cx, 740, "W = 2 met · a read of n2, n3 before handoff can miss it", 24, INK, "middle", 700))
    b.append(text(cx + R + 60, 70, "home set of the key: n1, n2, n3", 21, BLUE, "start", 600))
    return svg(W, H, b)


# ---------------------------------------------------------------- p5-merkle
def merkle():
    W, H = 1600, 820
    def tree(ox, red_vals):
        o = []
        rx, ry = ox + 380, 90
        cxs = [ox + 110 + i * 180 for i in range(4)]
        gxs = [ox + 110 + i * 180 for i in range(4)]
        cy, gy = 260, 440
        hashes = {"root": "a1f…", "c": ["3b0…", "9e2…", "d47…", "61c…"], "g": ["0fa…", "c8e…", "57d…", "b19…"]}
        hashes["root"] = red_vals[0]; hashes["c"][1] = red_vals[1]; hashes["g"][2] = red_vals[2]
        for x in cxs:
            o.append(line(rx, ry + 56, x, cy, GREY, 2))
        for x in gxs:
            o.append(line(cxs[1], cy + 56, x, gy, GREY, 2))
        o.append(box(rx - 80, ry, 160, 56, hashes["root"], RED, size=22))
        for i, x in enumerate(cxs):
            o.append(box(x - 70, cy, 140, 56, hashes["c"][i], RED if i == 1 else BLUE, size=22))
        for i, x in enumerate(gxs):
            o.append(box(x - 80, gy, 160, 80, [hashes["g"][i], f"bucket {4 * i}–{4 * i + 3}"], RED if i == 2 else BLUE, size=21))
        return o, (rx, ry), cxs[1], gxs[2]
    a, ra, ca, ga = tree(20, ["a1f…", "9e2…", "57d…"])
    bb, rb, cb, gb = tree(820, ["e07…", "4c9…", "2ab…"])
    b = [title(400, 50, "Replica A", 28, INK, "middle"), title(1200, 50, "Replica B", 28, INK, "middle")]
    b.append(line(800, 70, 800, 640, "#d0d7de", 2))
    b.append(line(ra[0] + 84, ra[1] + 28, rb[0] - 84, rb[1] + 28, RED, 2.5, "9 7", True, True))
    b.append(text(800, ra[1] + 16, "compare", 21, RED, "middle", 700, True))
    b.append(path(f"M{ca},{258} C{ca + 150},{200} {cb - 150},{200} {cb},{258}", RED, 2.5, "9 7", True))
    b.append(text(800, 200, "compare", 21, RED, "middle", 700, True))
    b.append(path(f"M{ga},{522} C{ga + 150},{610} {gb - 150},{610} {gb},{522}", RED, 2.5, "9 7", True))
    b.append(text(800, 610, "compare", 21, RED, "middle", 700, True))
    b += a + bb
    b.append(text(W / 2, 730, "equal roots → identical · otherwise descend only into the child that differs", 24, INK, "middle", 700))
    return svg(W, H, b)


# ---------------------------------------------------------------- p5-tombstone
def tombstone():
    W, H = 1600, 720
    def X(d): return 260 + d * 88
    ys = {"Replica A": 230, "Replica B": 350, "Replica C": 470}
    AX = 560
    b = []
    for n, y in ys.items():
        b.append(text(40, y + 8, n, 22, INK, "start", 700)); b.append(line(X(0), y, X(14.3), y, "#d0d7de", 2))
        b.append(text(X(0) + 6, y - 16, "x = v", 21, BLUE, "start", 700))
    for n in ("Replica A", "Replica B"):
        y = ys[n]
        b.append(bar(X(1), y - 16, X(11) - X(1), 32, "tombstone", GREY, 21))
    b.append(text(X(1), ys["Replica A"] - 40, "delete x → tombstone", 21, INK, "start", 700, True))
    b.append(line(X(11), ys["Replica A"] - 70, X(11), ys["Replica B"] + 20, MUTED, 2, "4 5"))
    b.append(mtext(X(11) + 14, 120, ["grace period (10 days) over", "→ tombstone purged"], 21, MUTED, "start", 700, halo=True))
    yc = ys["Replica C"]
    b.append(bar(X(1), yc - 16, X(13) - X(1), 32, "down", RED, 21))
    b.append(text(X(13) + 10, yc + 44, "returns, still x = v", 21, RED, "middle", 700, True))
    for n in ("Replica A", "Replica B"):
        b.append(line(X(13.2), yc - 20, X(13.7), ys[n] + 18, RED, 3.5, "", True))
    b.append(mtext(X(12.9), 410, ["x = v", "copied back"], 21, RED, "end", 800, halo=True))
    b.append(line(X(0), AX, X(14.3), AX, MUTED, 2, arrow=True))
    for d in range(0, 15):
        b.append(line(X(d), AX - 6, X(d), AX + 6, MUTED, 2))
        if d in (0, 1, 11, 13, 14) or d % 2 == 0:
            b.append(text(X(d), AX + 32, str(d), 21, MUTED, "middle"))
    b.append(text(X(14.3), AX + 60, "day", 21, MUTED, "end", 600))
    b.append(text(W / 2, 680, "deleted data resurrected", 28, RED, "middle", 800))
    return svg(W, H, b)


# ---------------------------------------------------------------- p5-seed
def seed():
    W, H = 1600, 640
    b = [rect(40, 40, 1080, 300, "#f6f8fa", BLUE, 2.5, 14), text(64, 82, "Leader", 24, INK, "start", 700)]
    cells = ["880", "…", "900", "901", "…", "1000"]
    xs = [80, 230, 330, 480, 630, 730]; ws = [150, 100, 150, 150, 100, 150]
    for x, w, c in zip(xs, ws, cells):
        b.append(rect(x, 160, w, 66, "#ddeaf8" if c != "…" else "#fff", BLUE, 2, 3))
        b.append(text(x + w / 2, 202, c, 22, INK, "middle", 700))
    b.append(f'<polygon points="{405 - 12},{132} {405 + 12},{132} {405},{152}" fill="{AMBER}"/>')
    b.append(text(405, 122, "snapshot taken here", 21, AMBER, "middle", 700))
    b.append(bracket(334, 876, 244, "", RED, up=False))
    b.append(text(605, 300, "log must still be retained back to 900", 22, RED, "middle", 800))
    b.append(box(1200, 380, 360, 180, ["New replica", "replay →", "caught up at 1000"], GREEN, size=23))
    b.append(path("M405,342 L405,520 L1194,520", BLUE, 3.5, "", True))
    b.append(text(800, 506, "① snapshot @ 900", 22, BLUE, "middle", 700, True))
    b.append(path("M555,342 L555,430 L1194,430", BLUE, 3.5, "", True))
    b.append(text(880, 416, "② log from 901", 22, BLUE, "middle", 700, True))
    return svg(W, H, b)


FIGS = {"p5-async-tail": async_tail, "p5-lag-curve": lag_curve, "p5-dual-write": dual_write, "p5-outbox": outbox,
        "p5-multi-leader": multi_leader, "p5-sloppy": sloppy, "p5-merkle": merkle, "p5-tombstone": tombstone,
        "p5-seed": seed}

if __name__ == "__main__":
    save(FIGS, sys.argv[1:])
