#!/usr/bin/env python3
"""Part 12 figures (diagrams/p12.md). Run: python3 diagrams_p12.py [name …] → svg/p12-*.svg"""
import sys
from dg import *


# ---------------------------------------------------------------- p12-boundary
def boundary():
    W, H = 1600, 620
    L, R = 120, 1500
    def X(s): return L + (R - L) * s / 120
    ya = 470
    b = [line(L, ya, R, ya, INK, 2, arrow=True)]
    for s, lab in ((0, "0:00"), (30, "0:30"), (60, "1:00"), (90, "1:30"), (120, "2:00")):
        b.append(line(X(s), ya, X(s), ya + 10, INK, 2)); b.append(text(X(s), ya + 38, lab, 22, INK, "middle"))
    b.append(line(X(60), 90, X(60), ya + 14, INK, 4))
    b.append(text(X(60), ya + 76, "window boundary", 22, INK, "middle", 700))
    # fixed windows as brackets
    b.append(bracket(X(0) + 4, X(60) - 8, 120, "window 1: 100 ✓", GREEN))
    b.append(bracket(X(60) + 8, X(120) - 4, 120, "window 2: 100 ✓", GREEN))
    # bars: 100 requests in 0:59-1:00 and 1:00-1:01
    for s in (59, 60):
        b.append(f'<rect x="{X(s) + (2 if s == 60 else 0):.1f}" y="{ya - 220}" width="{X(1) - X(0) - 2:.1f}" height="220" fill="{RED}"/>')
    b.append(text(X(59) - 14, ya - 190, "100 requests", 22, RED, "end", 800, True))
    b.append(text(X(61) + 14, ya - 190, "100 requests", 22, RED, "start", 800, True))
    b.append(bracket(X(59) - 30, X(61) + 30, ya - 250, "", RED))
    b.append(text(X(60), ya - 268, "200 requests in 2 seconds · limit 100/min", 26, RED, "middle", 800, True))
    return svg(W, H, b)


# ---------------------------------------------------------------- p12-local-limit
def local_limit():
    W, H = 1600, 700
    b = [box(40, 270, 300, 120, ["customer", "limit 1,000/s"], BLUE)]
    labels = ["gw 1", "gw 2", "gw 3", "gw 4", "gw 5", "…", "gw 50"]
    for i, g in enumerate(labels):
        y = 60 + i * 80
        if g == "…":
            b.append(text(560, y + 40, "…", 30, MUTED, "middle", 700))
            continue
        b.append(box(470, y, 180, 60, [g], GREY, size=22))
        b.append(arrow(340, 330, 466, y + 30, "", BLUEGREY, 2))
    b.append(box(760, 110, 800, 150, ["each enforces 1,000/s", "→ customer can send 50,000/s"], RED, size=24))
    b.append(box(760, 300, 800, 150, ["each enforces 20/s", "→ traffic landing on 3 gateways throttled at 60/s"], AMBER, size=24))
    b.append(box(760, 520, 800, 110, ["the limit is global", "→ some state must be shared"], BLUE, size=24, sw=4))
    return svg(W, H, b)


# ---------------------------------------------------------------- p12-queue
def queue():
    W, H = 1600, 640
    b = [rect(320, 220, 820, 140, "#f6f8fa", INK, 3, 14), text(320, 205, "bounded queue · capacity 8 · full", 22, INK, "start", 700)]
    reqs = ["r3", "r4", "r5", "r6", "r8", "r9", "r10", "r11"]   # head (left) to tail (right)
    for i, r in enumerate(reqs):
        b.append(box(340 + i * 100, 240, 90, 100, [r, "dl ✓"], BLUE, size=21))
    # r7 at the head: deadline passed, dropped at dequeue
    b.append(box(40, 230, 240, 120, ["r7", "deadline passed"], RED, size=22))
    b.append(cross(255, 245, 16))
    b.append(arrow(336, 290, 284, 290, "", RED, 3))
    b.append(text(160, 400, "dropped at dequeue", 22, RED, "middle", 800))
    b.append(text(160, 428, "(never served)", 22, RED, "middle", 700))
    # server, fed from the tail under overload
    b.append(box(1300, 380, 240, 110, ["server"], GREEN, size=26))
    b.append(path("M1100,360 C1150,430 1200,435 1296,435", GREEN, 3.5, arrow=True))
    b.append(text(1200, 520, "overload: serve newest first (LIFO)", 22, GREEN, "middle", 800))
    # new arrival rejected
    b.append(box(1300, 110, 220, 80, ["r12 arrives"], GREY, size=22))
    b.append(arrow(1296, 150, 1150, 228, "", AMBER, 3))
    b.append(cross(1180, 212, 14, AMBER))
    b.append(text(1410, 230, "queue full → reject fast", 22, AMBER, "middle", 800))
    b.append(text(720, 600, "head (oldest) on the left · tail (newest) on the right", 21, MUTED, "middle", 600))
    return svg(W, H, b)



# ---------------------------------------------------------------- p12-goodput  (the cost of a reject, as goodput curves)
def goodput():
    W, H = 1600, 720
    L, R, B, T = 150, 1360, 600, 80
    C = 10000
    def X(load): return L + (R - L) * load / 12
    def Y(v): return B - (B - T) * v / 1.1
    b = [line(L, B, R + 20, B, MUTED, 2, arrow=True), line(L, B, L, T - 20, MUTED, 2, arrow=True)]
    for k in range(0, 13, 2):
        b.append(line(X(k), B - 6, X(k), B + 6, MUTED, 2)); b.append(text(X(k), B + 34, f"{k}×", 21, MUTED, "middle"))
    b.append(text((L + R) / 2, B + 76, "offered load, as a multiple of capacity", 22, MUTED, "middle"))
    for v, lab in ((0, "0"), (0.5, "5,000"), (1.0, "10,000")):
        b.append(text(L - 14, Y(v) + 7, lab, 21, MUTED, "end"))
    b.append(text(L - 14, T - 30, "served a second", 21, MUTED, "start"))
    b.append(line(L, Y(1.0), R, Y(1.0), "#d0d7de", 2, "8 6"))
    for r, col, lab in ((0.01, GREEN, "reject costs 1%"), (0.10, AMBER, "reject costs 10%"), (0.50, RED, "reject costs 50%")):
        pts = []
        for i in range(0, 241):
            load = i / 20
            s = load if load <= 1 else max(0.0, min(1.0, (1 - r * load) / (1 - r)))
            pts.append((X(load), Y(s)))
        b.append(poly(pts, col, 5))
        lx, ly = {0.01: (X(9), Y(0.93) - 26), 0.10: (X(5.6), Y(0.5)), 0.50: (X(1.75), Y(0.55))}[r]
        b.append(text(lx, ly, lab, 22, col, "start", 800, True))
    b.append(text(X(2.6), Y(0.08), "at 2× and beyond: all capacity spent saying no", 21, RED, "start", 700, True))
    return svg(W, H, b)


# ---------------------------------------------------------------- p12-maxmin  (max-min fairness as water-filling)
def maxmin():
    W, H = 1600, 640
    B, PX = 540, 4.6
    def Y(v): return B - v * PX
    b = [title(40, 50, "Capacity 100. Tenants want 10, 30 and 80.")]
    tenants = [("A", 10, 10), ("B", 30, 30), ("C", 80, 60)]
    for i, (name, want, got) in enumerate(tenants):
        x = 260 + i * 380
        b.append(rect(x, Y(want), 220, want * PX, "#fff", MUTED, 2.5, 6, "8 6"))
        b.append(bar(x, Y(got), 220, got * PX, f"gets {got}" if want > got else f"wants {want}, gets {got}", GREEN, 22))
        if want > got: b.append(text(x + 110, Y(want) - 14, f"wants {want}", 22, MUTED, "middle", 700))
        b.append(text(x + 110, B + 40, f"tenant {name}", 24, INK, "middle", 700))
    b.append(line(200, Y(33.3), 1250, Y(33.3), AMBER, 3, "12 8"))
    b.append(text(1262, Y(33.3) + 8, "equal split: 33 each", 22, AMBER, "start", 700))
    b.append(line(200, B, 1400, B, MUTED, 2))
    b.append(text(800, 620, "Fill the smallest demands first; share what is left equally. Nobody can gain without taking from someone smaller.", 22, INK, "middle"))
    return svg(W, H, b)

FIGS = {"p12-goodput": goodput, "p12-maxmin": maxmin, "p12-boundary": boundary, "p12-local-limit": local_limit, "p12-queue": queue}

if __name__ == "__main__":
    save(FIGS, set(sys.argv[1:]) or None)
