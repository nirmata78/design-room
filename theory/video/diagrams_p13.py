#!/usr/bin/env python3
"""Part 13 figures (diagrams/p13.md). Run: python3 diagrams_p13.py [name …] → svg/p13-*.svg"""
import math, sys
from dg import *


# ---------------------------------------------------------------- p13-no-breaker
def no_breaker():
    W, H = 1600, 620
    b = [box(60, 80, 420, 120, ["Caller", "1,000 calls/s"], BLUE, size=26)]
    b.append(box(1060, 80, 480, 120, ["Dependency", "(down, restarting)"], RED, size=26, sw=4))
    b.append(line(484, 140, 1052, 140, RED, 14, "", False))
    b.append(f'<polygon points="1056,140 1020,116 1020,164" fill="{RED}"/>')
    for i in range(40):
        x = 60 + (i % 20) * 21; y = 260 + (i // 20) * 34
        b.append(rect(x, y, 17, 28, "#fff4d6", AMBER, 1.5, 3))
    b.append(text(60, 360, "… 200 thread slots", 22, AMBER, "start", 800))
    b.append(text(60, 396, "all waiting 200 ms each", 22, AMBER, "start", 800))
    b.append(mtext(1300, 270, ["1,000/s of calls that cannot", "succeed slow its recovery"], 26, RED, "middle", 800))
    return svg(W, H, b)


# ---------------------------------------------------------------- p13-breaker
def breaker():
    W, H = 1600, 700
    C, O, HO = (260, 300), (1340, 300), (800, 560)
    def node(c, lab, col, r=130):
        return (f'<circle cx="{c[0]}" cy="{c[1]}" r="{r}" fill="{FILL[col]}" stroke="{col}" stroke-width="4"/>'
                + text(c[0], c[1] - 20 if lab == "Open" else c[1] + 10, lab, 32, INK, "middle", 800))
    b = []
    b.append(path(f"M{C[0] + 110},{C[1] - 70} Q800,40 {O[0] - 110},{O[1] - 70}", RED, 3.5, "", True))
    b.append(text(800, 100, "failure rate > 50% over ≥ 20 calls in 10 s", 23, RED, "middle", 800, True))
    b.append(path(f"M{O[0] - 60},{O[1] + 120} Q1150,560 {HO[0] + 132},{HO[1]}", INK, 3, "", True))
    b.append(text(1170, 520, "after 30 s cool-down", 22, INK, "start", 700, True))
    b.append(path(f"M{HO[0] - 132},{HO[1] - 10} Q450,560 {C[0] + 60},{C[1] + 120}", GREEN, 3.5, "", True))
    b.append(text(420, 545, "trial calls succeed", 22, GREEN, "end", 800, True))
    b.append(path(f"M{HO[0] + 90},{HO[1] - 100} Q1000,380 {O[0] - 132},{O[1] + 20}", RED, 3, "9 6", True))
    b.append(text(1000, 400, "trial fails", 22, RED, "middle", 800, True))
    b.append(node(C, "Closed", GREEN)); b.append(node(O, "Open", RED)); b.append(node(HO, "Half-open", AMBER, 120))
    b.append(mtext(O[0], O[1] + 22, ["fail fast ·", "serve fallback"], 22, RED, "middle", 800))
    return svg(W, H, b)


# ---------------------------------------------------------------- p13-shared-pool
def shared_pool():
    W, H = 1600, 640
    b = [rect(40, 100, 560, 440, "#f6f8fa", INK, 2.5, 14), text(320, 145, "Service", 26, INK, "middle", 800)]
    b.append(rect(80, 180, 480, 300, "#fff", AMBER, 2.5, 10))
    b.append(text(320, 216, "one pool · 200 threads", 22, INK, "middle", 700))
    for i in range(60):
        x = 104 + (i % 15) * 29; y = 240 + (i // 15) * 40
        b.append(rect(x, y, 22, 32, "#fff4d6", AMBER, 1.5, 3))
    b.append(text(320, 430, "all waiting on recommendations", 22, AMBER, "middle", 800))
    b.append(box(1050, 70, 440, 100, ["Recommendations", "(slow)"], AMBER, size=24))
    b.append(box(1050, 270, 440, 100, ["Inventory", "(healthy)"], GREEN, size=24))
    b.append(box(1050, 470, 440, 100, ["Payments", "(healthy)"], GREEN, size=24))
    b.append(line(602, 220, 1046, 120, AMBER, 5, "", True))
    b.append(line(602, 330, 1046, 320, RED, 3, "10 7", True)); b.append(cross(830, 326, 16, RED, 5))
    b.append(line(602, 440, 1046, 520, RED, 3, "10 7", True)); b.append(cross(830, 480, 16, RED, 5))
    b.append(text(830, 400, "no thread available", 24, RED, "middle", 800, True))
    return svg(W, H, b)


# ---------------------------------------------------------------- p13-cells
def cells():
    W, H = 1600, 760
    b = [panel(20, 20, 600, 720, "grey"), panel(650, 20, 930, 720, "grey")]
    b.append(title(320, 64, "Bulkheads in a process", 26, INK, "middle")); b.append(title(1115, 64, "Cells across the fleet", 26, INK, "middle"))
    b.append(rect(60, 110, 520, 560, "#fff", INK, 2.5, 12)); b.append(text(320, 150, "service", 24, INK, "middle", 800))
    for i, (lab, n, col, st) in enumerate((("recs: 40", 40, AMBER, "exhausted"), ("inventory: 80", 80, GREEN, ""), ("payments: 80", 80, GREEN, ""))):
        y = 180 + i * 160
        b.append(rect(90, y, 460, 130, FILL[col], col, 3, 10))
        b.append(text(110, y + 36, lab, 23, INK, "start", 800))
        if st:
            b.append(text(530, y + 36, st, 22, AMBER, "end", 800))
        for k in range(min(n, 40) // 2):
            b.append(rect(110 + k * 21, y + 62, 16, 44, "#fff" if col == GREEN else "#f6d58a", col, 1.2, 3))
    b.append(box(800, 100, 630, 80, "Cell router (customer → cell table)", BLUE, size=23))
    for i in range(8):
        x = 680 + (i % 4) * 222; y = 260 + (i // 4) * 220
        bad = i == 2
        b.append(rect(x, y, 200, 190, "#fde7e9" if bad else "#fff", RED if bad else BLUE, 4 if bad else 2.5, 10))
        b.append(text(x + 100, y + 32, f"cell {i + 1}", 22, INK, "middle", 800))
        for j, t in enumerate(("LB", "app", "cache", "DB")):
            b.append(rect(x + 14 + (j % 2) * 90, y + 50 + (j // 2) * 54, 82, 44, "#eef1f4", GREY, 1.5, 6))
            b.append(text(x + 55 + (j % 2) * 90, y + 79 + (j // 2) * 54, t, 20 if False else 21, INK, "middle", 600))
        b.append(line(1115, 182, x + 100, y - 2, GREY, 1.5, "", True))
    b.append(text(902 - 222 + 222 * 2 + 100, 476, "bad deploy", 22, RED, "middle", 800))
    b.append(text(1115, 715, "1/8 of customers affected", 26, RED, "middle", 800))
    return svg(W, H, b)


# ---------------------------------------------------------------- p13-static
def static():
    W, H = 1600, 700
    b = []
    for k, (ttl, stable) in enumerate((("Not statically stable", False), ("Statically stable", True))):
        ox = 20 + k * 800
        b.append(panel(ox, 20, 760, 660, "grey"))
        b.append(title(ox + 380, 64, ttl, 26, INK, "middle"))
        b.append(box(ox + 200, 100, 360, 80, "Control plane", GREY, size=24))
        b.append(cross(ox + 380, 140, 30, RED, 7)); b.append(text(ox + 580, 148, "outage", 22, RED, "start", 800))
        for i in range(4):
            x = ox + 40 + i * 180
            col = GREEN if stable else GREY
            b.append(box(x, 300, 160, 90, "server", col, size=22))
            b.append(line(ox + 380, 182, x + 80, 296, GREY, 1.5, "6 5"))
        if stable:
            b.append(mtext(ox + 380, 450, ["serving on last known good (disk)"], 23, GREEN, "middle", 800))
            b.append(box(ox + 60, 520, 640, 100, ["no changes until", "control plane returns"], GREEN, size=24, sw=4))
        else:
            b.append(text(ox + 380, 450, "refresh failed → stop serving", 23, RED, "middle", 800))
            b.append(box(ox + 200, 520, 360, 100, ["Autoscaler", "cannot launch"], RED, size=24))
    return svg(W, H, b)


# ---------------------------------------------------------------- p13-metastable
def metastable():
    W, H = 1600, 760
    cx, cy, R = 900, 390, 260
    names = ["latency ↑", "timeouts", "retries", "load ↑"]
    ang = [-90, 0, 90, 180]
    P = [(cx + R * math.cos(math.radians(a)), cy + R * math.sin(math.radians(a))) for a in ang]
    b = []
    for i in range(4):
        (x1, y1), (x2, y2) = P[i], P[(i + 1) % 4]
        a1, a2 = math.radians(ang[i] + 22), math.radians(ang[(i + 1) % 4] - 22 + (360 if i == 3 else 0))
        sx, sy = cx + R * math.cos(a1), cy + R * math.sin(a1)
        ex, ey = cx + R * math.cos(a2), cy + R * math.sin(a2)
        b.append(f'<path d="M{sx:.1f},{sy:.1f} A{R},{R} 0 0 1 {ex:.1f},{ey:.1f}" fill="none" stroke="{RED}" stroke-width="5" marker-end="url(#ah{RED[1:]})"/>')
    for (x, y), n in zip(P, names):
        b.append(box(x - 110, y - 40, 220, 80, n, RED, size=26))
    b.append(box(40, 40, 360, 90, ["trigger", "(spike, slow backup)"], GREY, size=23))
    b.append(path(f"M402,85 L{P[0][0] - 114},{P[0][1]}", GREY, 3, "10 7", True))
    b.append(cross(600, 70, 18, RED, 5)); b.append(text(600, 150, "trigger gone", 22, MUTED, "middle", 800))
    def brk(x, y, lab, anchor):
        o = rect(x - 30, y - 22, 60, 44, "#dff3e4", GREEN, 3, 8) + line(x - 16, y, x + 16, y, GREEN, 4) + line(x, y - 12, x, y + 12, "#dff3e4", 6)
        return o + text(x + (44 if anchor == "start" else -44), y + 8, lab, 24, GREEN, anchor, 800, True)
    m1 = math.radians(225); m2 = math.radians(45)
    b.append(brk(cx + R * math.cos(m1), cy + R * math.sin(m1), "shed load", "end"))
    b.append(brk(cx + R * math.cos(m2), cy + R * math.sin(m2), "cut retries", "start"))
    b.append(text(cx, cy + 10, "the loop sustains itself", 24, RED, "middle", 700))
    return svg(W, H, b)


# ---------------------------------------------------------------- p13-cycle
def cycle():
    W, H = 1600, 600
    b = [box(120, 200, 420, 140, "Auth service", BLUE, size=30), box(1060, 200, 420, 140, "Config service", BLUE, size=30)]
    b.append(path("M540,230 Q800,120 1056,230", RED, 4, "", True))
    b.append(text(800, 150, "keys stored in", 24, RED, "middle", 800, True))
    b.append(path("M1060,310 Q800,420 544,310", RED, 4, "", True))
    b.append(text(800, 420, "authenticates callers with", 24, RED, "middle", 800, True))
    b.append(text(800, 540, "normal day: both run · cold start: each waits for the other", 28, INK, "middle", 800))
    return svg(W, H, b)


FIGS = {"p13-no-breaker": no_breaker, "p13-breaker": breaker, "p13-shared-pool": shared_pool, "p13-cells": cells,
        "p13-static": static, "p13-metastable": metastable, "p13-cycle": cycle}

if __name__ == "__main__":
    save(FIGS, sys.argv[1:])
