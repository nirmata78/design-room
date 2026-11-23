#!/usr/bin/env python3
"""Part 14 figures (diagrams/p14.md). Run: python3 diagrams_p14.py [name …] → svg/p14-*.svg"""
import sys
from dg import *

BUCKETS = ["<10", "10–25", "25–50", "50–100", "100–300", "300–1000"]


def hist(x, y, w, h, counts, col, label, size=21, show_labels=True):
    o = [rect(x, y, w, h, "#fff", "#d0d7de", 2, 8)]
    o.append(text(x + w / 2, y + 30, label, 22, INK, "middle", 800))
    m = max(counts); n = len(counts); bw = (w - 40) / n; base = y + h - (40 if show_labels else 16)
    for i, c in enumerate(counts):
        bh = (h - 90) * c / m
        o.append(rect(x + 20 + i * bw + 4, base - bh, bw - 8, bh, col, "none", 0, 3))
        if show_labels:
            o.append(text(x + 20 + i * bw + bw / 2, base + 28, BUCKETS[i], size, MUTED, "middle"))
    return "".join(o)


# ---------------------------------------------------------------- p14-histograms
def histograms():
    W, H = 1600, 760
    hosts = [("host A", [40, 120, 60, 20, 6, 1]), ("host B", [30, 100, 80, 30, 10, 3]), ("host C", [50, 90, 50, 25, 12, 2])]
    b = []
    for i, (n, c) in enumerate(hosts):
        b.append(hist(40 + i * 520, 20, 480, 220, c, BLUEGREY, n, size=18 if False else 0, show_labels=False))
        b.append(arrow(280 + i * 520, 244, 800 + (i - 1) * 200, 316, colour=MUTED, w=2.5))
    tot = [sum(h[1][k] for h in hosts) for k in range(6)]
    x, y, w, h = 300, 320, 1000, 420
    b.append(hist(x, y, w, h, tot, BLUE, "fleet (sum per bucket)"))
    bw = (w - 40) / 6
    edge = x + 20 + 5 * bw
    b.append(line(edge, y + 50, edge, y + h - 40, RED, 3, "10 7"))
    b.append(text(edge - 10, y + 70, "SLO threshold · 300 ms", 21, RED, "end", 800, True))
    b.append(rect(x + 20 + 5 * bw, y + 46, bw, h - 86, "none", RED, 4, 4))
    b.append(mtext(x + w + 20, y + 170, ["99% of count", "below here →", "p99 in bucket", "300–1000"], 22, RED, "start", 800))
    b.append(text(40, 300, "buckets: <10, 10–25, 25–50, 50–100, 100–300, 300–1000 ms", 21, MUTED, "start", 600))
    return svg(W, H, b)


# ---------------------------------------------------------------- p14-logs
def logs():
    W, H = 1600, 640
    stages = [("app", GREY), ("agent", BLUE), ("queue", BLUE), ("indexers", BLUE), ("search store", GREEN), ("object storage", GREY)]
    subs = ["", "(disk buffer)", "(partitioned log)", "", "(hot)", "(cold)"]
    b = []
    for i, ((n, c), s) in enumerate(zip(stages, subs)):
        x = 20 + i * 265
        b.append(box(x, 300, 220, 100, [n] + ([s] if s else []), c, size=22))
        if i:
            b.append(arrow(x - 43, 350, x - 4, 350, colour=INK, w=3))
    b.append(rect(240, 40, 560, 190, "#fff4d6", AMBER, 3, 10))
    b.append(text(260, 78, "drop order under pressure", 22, AMBER, "start", 800))
    b.append(mtext(260, 118, ["1  debug", "2  sampled info", "never: errors, audit"], 22, INK, "start", 700))
    b.append(line(395, 232, 395, 296, AMBER, 2.5, "", True))
    b.append(box(940, 460, 360, 80, "audit store", RED, size=22))
    b.append(path("M130,402 L130,500 L936,500", RED, 3.5, "", True))
    b.append(text(520, 486, "audit → lossless path", 22, RED, "middle", 800, True))
    b.append(text(W / 2, 610, "2,000 req/s × 20 lines × 500 B = 20 MB/s ≈ 1.7 TB/day", 26, INK, "middle", 800))
    return svg(W, H, b)


# ---------------------------------------------------------------- p14-columnar
def columnar():
    W, H = 1600, 720
    b = [panel(20, 20, 760, 680, "grey"), panel(820, 20, 760, 680, "grey")]
    b.append(title(400, 64, "Row storage", 26, INK, "middle")); b.append(title(1200, 64, "Column storage", 26, INK, "middle"))
    for r in range(12):
        y = 110 + r * 34
        hl = r in (3, 4, 5, 6, 7)
        for c in range(25):
            b.append(rect(60 + c * 27, y, 24, 28, "#fde7e9" if hl else "#eef1f4", RED if hl else "#d0d7de", 1, 2))
    b.append(text(400, 560, "query reads whole rows:", 22, INK, "middle", 700))
    b.append(text(400, 600, "reads 100 of 100 columns", 26, RED, "middle", 800))
    names = {4: "region", 11: "latency", 18: "time"}
    for c in range(25):
        x = 860 + c * 27
        hl = c in names
        for r in range(12):
            b.append(rect(x, 110 + r * 34, 24, 28, "#ddeaf8" if hl else "#eef1f4", BLUE if hl else "#d0d7de", 1.5 if hl else 1, 2))
    for c, n in names.items():
        b.append(text(860 + c * 27 + 12, 100, n, 21, BLUE, "middle", 800))
    b.append(text(1200, 560, "reads 3 of 100", 26, BLUE, "middle", 800))
    b.append(mtext(1200, 610, ["region: dictionary europe-west1 → 3 ·", "run length: 3 × 40,000"], 21, INK, "middle", 600))
    return svg(W, H, b)


# ---------------------------------------------------------------- p14-postings
def postings():
    W, H = 1600, 600
    b = []
    rows = [('job="api"', [3, 7, 9, 12], 140), ('status="500"', [7, 12, 20], 300)]
    for lab, vals, y in rows:
        b.append(text(60, y + 46, lab, 26, INK, "start", 800))
        b.append(text(390, y + 46, "→", 30, INK, "middle", 800))
        for i, v in enumerate(vals):
            x = 450 + i * 140
            m = v in (7, 12)
            b.append(rect(x, y, 110, 70, "#dff3e4" if m else "#ddeaf8", GREEN if m else BLUE, 2.5, 8))
            b.append(text(x + 55, y + 46, str(v), 28, INK, "middle", 800))
            if m:
                b.append(f'<circle cx="{x + 55}" cy="{y + 35}" r="52" fill="none" stroke="{GREEN}" stroke-width="4"/>')
    for x, y, lab in ((450 + 55, 110, "cursor"), (450 + 55, 410, "cursor")):
        b.append(f'<polygon points="{x - 12},{y - 24 if y < 200 else y + 24} {x + 12},{y - 24 if y < 200 else y + 24} {x},{y}" fill="{AMBER}"/>')
        b.append(text(x, y - 32 if y < 200 else y + 52, lab, 21, AMBER, "middle", 800))
    b.append(line(990, 270, 1100, 270, GREEN, 4, "", True))
    b.append(box(1110, 220, 400, 100, "series 7, 12", GREEN, size=30, sw=4))
    b.append(text(60, 540, "intersect shortest list first · advance the cursor with the smaller value", 23, MUTED, "start", 700))
    return svg(W, H, b)


FIGS = {"p14-histograms": histograms, "p14-logs": logs, "p14-columnar": columnar, "p14-postings": postings}

if __name__ == "__main__":
    save(FIGS, sys.argv[1:])
