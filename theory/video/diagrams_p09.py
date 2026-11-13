#!/usr/bin/env python3
"""Part 9 figures (diagrams/p09.md). Run: python3 diagrams_p09.py [name …] → svg/p9-*.svg"""
import math, sys
from dg import *


def seqfig(s, h):
    body = s.body()
    return svg(1600, max(h, int(s.y + 20)), [body])


# ---------------------------------------------------------------- p9-hit-curve
def hit_curve():
    W, H = 1600, 680
    L, R, T, B = 230, 1520, 60, 560
    def X(h): return L + (R - L) * (h - 80) / 20
    def Y(v): return B - (B - T) * v / 200000
    b = [line(L, B, R, B, INK, 2), line(L, B, L, T - 10, INK, 2)]
    for v in range(0, 200001, 50000):
        b.append(line(L - 8, Y(v), R, Y(v), "#e6e9ec", 1.5)); b.append(text(L - 14, Y(v) + 8, f"{v:,}", 21, INK, "end"))
    for h in range(80, 101, 2):
        b.append(line(X(h), B, X(h), B + 8, INK, 2)); b.append(text(X(h), B + 34, f"{h}%", 21, INK, "middle"))
    b.append(text((L + R) / 2, B + 72, "hit ratio", 22, MUTED, "middle", 600))
    b.append(f'<text transform="translate(40,{(T + B) / 2}) rotate(-90)" font-family="{FONT}" font-size="22" fill="{MUTED}" text-anchor="middle" font-weight="600">database reads/s</text>')
    b.append(line(X(80), Y(200000), X(100), Y(0), BLUE, 5))
    b.append(line(L, Y(20000), R, Y(20000), RED, 3, "12 8"))
    b.append(text(L + 20, Y(20000) + 32, "database capacity · 20,000", 22, RED, "start", 700, True))
    b.append(f'<rect x="{X(80)}" y="{T}" width="{X(98) - X(80)}" height="{Y(20000) - T}" fill="{RED}" fill-opacity="0.06"/>')
    for h, lab in ((99, "99% → 10k"), (95, "95% → 50k"), (90, "90% → 100k")):
        v = (1 - h / 100) * 1_000_000
        b.append(dot(X(h), Y(v), 9, BLUE))
        b.append(text(X(h) + (-16 if h == 99 else 16), Y(v) + (36 if h == 99 else -12), lab, 22, BLUE, "end" if h == 99 else "start", 700, True))
    b.append(dot(X(98), Y(20000), 12, RED))
    b.append(line(X(98), Y(20000), X(98), B, RED, 2.5, "4 5"))
    b.append(text(X(98) - 16, Y(20000) - 120, "overloaded below 98%", 24, RED, "end", 800, True))
    b.append(text(X(80) + 20, T + 20, "load = (1 − h) × 1,000,000", 22, INK, "start", 600, True))
    return svg(W, H, b)


# ---------------------------------------------------------------- p9-ttl-sync
def ttl_sync():
    W, H = 1600, 600
    L, R, T, B = 120, 1520, 80, 500
    def X(m): return L + (R - L) * m / 180
    def Y(v): return B - (B - T) * v / 10000
    b = [line(L, B, R, B, INK, 2)]
    for m, lab in ((0, "09:00"), (60, "10:00"), (120, "11:00"), (180, "12:00")):
        b.append(line(X(m), B, X(m), B + 8, INK, 2)); b.append(text(X(m), B + 34, lab, 21, INK, "middle"))
    b.append(text(L, T - 30, "cache misses a second", 21, MUTED, "start", 600))
    b.append(rect(L, Y(300), R - L, B - Y(300), "#c9d1d9", "none", 0, 0))
    b.append(text(L + 10, Y(300) - 10, "baseline misses", 21, MUTED, "start", 600))
    for m in (60, 120):
        b.append(f'<rect x="{X(m) - 4:.1f}" y="{Y(10000):.1f}" width="8" height="{B - Y(10000):.1f}" fill="{RED}"/>')
    pts = []
    for i in range(0, 241):
        m = 106 + 28 * i / 240
        v = 300 + 2600 * math.exp(-((m - 120) / 4.2) ** 2)
        pts.append((X(m), Y(v)))
    b.append(poly([(X(106), B)] + pts + [(X(134), B)], GREEN, 3, "#dff3e4"))
    b.append(text(X(60) + 14, Y(10000) + 22, "10,000 keys expire in one second", 22, RED, "start", 700, True))
    b.append(text(X(120) + 14, Y(10000) + 22, "10,000 keys expire in one second", 22, RED, "start", 700, True))
    b.append(text(X(120), Y(2900) - 16, "10:54–11:06", 21, GREEN, "middle", 700, True))
    b.append(rect(1300, 230, 28, 28, RED, "none", 0, 4)); b.append(text(1340, 252, "no jitter", 22, INK, "start", 600))
    b.append(rect(1300, 274, 28, 28, "#dff3e4", GREEN, 2.5, 4)); b.append(text(1340, 296, "jitter ±10%", 22, INK, "start", 600))
    return svg(W, H, b)


# ---------------------------------------------------------------- p9-lost-invalidation
def lost_invalidation():
    s = Seq(1600, y0=20, row=70, headh=62)
    s.part("w", "Writer", GREY); s.part("d", "Database"); s.part("c", "Cache", AMBER); s.part("r", "Reader", GREY)
    s.msg("w", "d", "price = 19 · commit")
    s.note("w", "w", "crash", "red")
    s.lost("w", "c", "delete price", "")
    s.msg("r", "c", "get price")
    s.msg("c", "r", "25", hl=True, dash=True, num=False)
    s.note("c", "r", "stale until TTL (1 h)", "red")
    return seqfig(s, 640)


# ---------------------------------------------------------------- p9-stale-set / p9-lease
def stale_set():
    s = Seq(1600, y0=20, row=62, headh=62)
    s.part("a", "Reader A", GREY); s.part("c", "Cache", AMBER); s.part("d", "Database"); s.part("w", "Writer", GREY)
    s.msg("a", "c", "get k → miss")
    s.msg("a", "d", "read k → v1")
    s.note("a", "a", "slow…", "grey")
    s.msg("w", "d", "k = v2")
    s.msg("w", "c", "delete k")
    s.msg("a", "c", "set k = v1", hl=True)
    s.note("a", "w", "old value cached after the invalidation", "red")
    return seqfig(s, 780)


def lease():
    s = Seq(1600, y0=20, row=60, headh=62)
    s.part("a", "Reader A", GREY); s.part("c", "Cache", AMBER); s.part("d", "Database"); s.part("w", "Writer", GREY)
    s.msg("a", "c", "get k"); s.msg("c", "a", "miss · lease 77", dash=True, colour=MUTED, num=False)
    s.msg("a", "d", "read → v1")
    s.msg("w", "d", "k = v2")
    s.msg("w", "c", "delete k (voids lease 77)")
    s.msg("a", "c", "set k = v1 · lease 77")
    s.msg("c", "a", "refused ✗", dash=True, colour=GREEN, num=False, lines=["**refused ✗**"])
    s.msg("a", "c", "Reader B: get k")
    s.msg("c", "a", "miss · lease 78 → loads v2", dash=True, colour=MUTED, num=False)
    return seqfig(s, 780)


# ---------------------------------------------------------------- p9-tiers
def tiers():
    W, H = 1600, 720
    b = []
    tiers_ = [("100k req/s", ["in-process cache", "(µs, thousands of keys)"], "60% served", 900, BLUE),
              ("40k", ["remote cache cluster", "(0.5 ms, millions)"], "98% of the rest", 700, AMBER),
              ("800/s", ["database"], "", 480, GREY)]
    y = 40
    for k, (inn, lab, served, w, c) in enumerate(tiers_):
        x = 820 - w / 2
        b.append(arrow(820, y, 820, y + 66, colour=INK, w=4, lines=[inn], weight=800, size=24))
        b.append(box(x, y + 70, w, 120, lab, c, size=24))
        if served:
            b.append(arrow(x + w + 4, y + 130, x + w + 120, y + 130, colour=GREEN, w=4))
            b.append(text(x + w + 132, y + 138, served, 24, GREEN, "start", 800))
        y += 230
    b.append(rect(20, 110, 300, 120, "#fde7e9", RED, 3, 10))
    b.append(mtext(170, 160, ["hard to invalidate", "· TTL seconds"], 22, RED, "middle", 800))
    b.append(line(322, 170, 366, 170, RED, 3, "", True))
    return svg(W, H, b)


# ---------------------------------------------------------------- p9-penetration
def penetration():
    W, H = 1600, 680
    b = [box(30, 300, 280, 110, ["Client:", "random ids, 50k/s"], GREY, size=23)]
    b.append(box(430, 300, 300, 110, ["Bloom filter of", "existing ids"], AMBER, size=23))
    b.append(box(860, 300, 230, 110, "Cache", BLUE, size=26))
    b.append(cyl(1240, 295, 300, 120, "Database", GREY))
    b.append(arrow(312, 355, 426, 355, colour=INK, w=3))
    b.append(arrow(732, 355, 856, 355, colour=GREEN, w=4, lines=["maybe"], weight=800))
    b.append(arrow(1092, 355, 1236, 355, colour=INK, w=3, lines=["miss"], weight=700))
    b.append(path("M580,298 L580,170 L170,170 L170,296", RED, 5, "", True))
    b.append(text(375, 152, "definitely absent → 404 at once", 24, RED, "middle", 800, True))
    b.append(line(975, 412, 975, 500, MUTED, 2.5, "6 5"))
    b.append(box(780, 500, 560, 110, ["negative entry: id 9931 →", "not found · TTL 30 s"], GREY, size=22))
    return svg(W, H, b)


FIGS = {"p9-hit-curve": hit_curve, "p9-ttl-sync": ttl_sync, "p9-lost-invalidation": lost_invalidation,
        "p9-stale-set": stale_set, "p9-lease": lease, "p9-tiers": tiers, "p9-penetration": penetration}

if __name__ == "__main__":
    save(FIGS, sys.argv[1:])
