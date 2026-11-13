#!/usr/bin/env python3
"""Part 8 figures (diagrams/p08.md). Run: python3 diagrams_p08.py [name …] → svg/p8-*.svg"""
import math, sys
from dg import *


def seqfig(s, h):
    body = s.body()
    return svg(1600, max(h, int(s.y + 20)), [body])


# ---------------------------------------------------------------- p8-lost-update
def lost_update():
    s = Seq(1600, y0=20, row=74, headh=64)
    s.part("a", "T1", GREY); s.part("d", "Database (counter = 42)"); s.part("b", "T2", GREY)
    s.msg("a", "d", "read → 42"); s.msg("b", "d", "read → 42")
    s.msg("a", "d", "write 43 · commit"); s.msg("b", "d", "write 43 · commit", hl=True)
    s.note("a", "b", "two increments · counter moved by one", "red")
    return seqfig(s, 640)


# ---------------------------------------------------------------- p8-two-editors
def two_editors():
    s = Seq(1600, y0=20, row=74, headh=64)
    s.part("a", "Ana", GREY); s.part("d", "Docs service (v7)"); s.part("b", "Ben", GREY)
    s.msg("a", "d", "load v7"); s.msg("b", "d", "load v7")
    s.msg("a", "d", "save → v8"); s.msg("b", "d", "save (based on v7)", hl=True)
    s.note("d", "b", "overwrites Ana's change silently", "red")
    return seqfig(s, 640)


# ---------------------------------------------------------------- p8-deadlock
def deadlock():
    W, H = 1600, 640
    T1, T2, RA, RB = (300, 310), (1300, 310), (800, 120), (800, 500)
    b = []
    def circ(c, lab):
        return (f'<circle cx="{c[0]}" cy="{c[1]}" r="100" fill="#ddeaf8" stroke="{BLUE}" stroke-width="3"/>'
                + text(c[0], c[1] + 9, lab, 26, INK, "middle", 800))
    def edge(a, bx, col, dash, lab, off=(0, 0), anchor="middle"):
        x1, y1 = a; x2, y2 = bx
        L = math.hypot(x2 - x1, y2 - y1); ux, uy = (x2 - x1) / L, (y2 - y1) / L
        o = line(x1 + ux * 104, y1 + uy * 104, x2 - ux * 150, y2 - uy * 60, col, 4, dash, True)
        mx, my = (x1 + x2) / 2 + off[0], (y1 + y2) / 2 + off[1]
        return o + text(mx, my, lab, 22, col, anchor, 800, True)
    b.append(edge(T1, RA, BLUE, "", "holds", (-20, -18), "end"))
    b.append(edge(T2, RB, BLUE, "", "holds", (24, 34), "start"))
    b.append(edge(T1, RB, RED, "12 8", "waits for", (-20, 40), "end"))
    b.append(edge(T2, RA, RED, "12 8", "waits for", (24, -18), "start"))
    b.append(circ(T1, "T1: A → B")); b.append(circ(T2, "T2: B → A"))
    b.append(box(RA[0] - 150, RA[1] - 50, 300, 100, "row A", GREY, size=26))
    b.append(box(RB[0] - 150, RB[1] - 50, 300, 100, "row B", GREY, size=26))
    b.append(text(W / 2, 612, "database aborts one · fix: lock lower id first", 26, RED, "middle", 800))
    return svg(W, H, b)


# ---------------------------------------------------------------- p8-partial-commit
def partial_commit():
    s = Seq(1600, y0=20, row=80, headh=64)
    s.part("t", "Transfer service"); s.part("a", "Shard 1 (account A)", GREY); s.part("b", "Shard 2 (account B)", GREY)
    s.msg("t", "a", "debit 30 · commit ✓")
    s.note("t", "t", "crash", "red")
    s.lost("t", "b", "credit 30", "")
    s.note("t", "b", "30 left A, arrived nowhere", "red")
    return seqfig(s, 640)


# ---------------------------------------------------------------- p8-2pc
def two_pc(blocked=False):
    s = Seq(1600, y0=20, row=58, headh=60)
    s.part("c", "Coordinator", AMBER); s.part("a", "Shard 1"); s.part("b", "Shard 2")
    if blocked:
        s.part("x", "Client", GREY)
    s.note("c", "b" if not blocked else "x", "phase 1 · prepare", "grey")
    s.msg("c", "a", "prepare"); s.msg("c", "b", "prepare")
    s.note("a", "b", "write prepared state durably · keep locks", "blue")
    s.msg("a", "c", "yes", dash=True, colour=GREEN); s.msg("b", "c", "yes", dash=True, colour=GREEN)
    if not blocked:
        s.note("c", "b", "phase 2 · commit", "grey")
        s.note("c", "c", "log COMMIT ← decision point", "red")
        s.msg("c", "a", "commit"); s.msg("c", "b", "commit")
        s.note("a", "b", "release locks", "green")
        return seqfig(s, 820)
    s.note("c", "c", "", "red", lines=["✗ crashes before", "sending decision"])
    s.note("a", "b", "", "amber", lines=["in doubt · locks held ·", "cannot decide alone", "· · ·", "still in doubt · still locked"])
    s.note("x", "x", "waits on the locked rows", "grey")
    return seqfig(s, 720)


def two_pc_plain(): return two_pc(False)
def two_pc_blocked(): return two_pc(True)


# ---------------------------------------------------------------- p8-2pc-paxos
def two_pc_paxos():
    W, H = 1600, 760
    b = []
    groups = [("Group A (coordinator)", 40), ("Group B (participant)", 570), ("Group C (participant)", 1100)]
    leaders = []
    for k, (lab, x) in enumerate(groups):
        b.append(rect(x, 140, 460, 470, "#f6f8fa", MUTED, 2.5, 16, "10 7"))
        b.append(text(x + 230, 178, lab, 23, INK, "middle", 700))
        lx, ly = x + 230, 290
        leaders.append((lx, ly))
        reps = [(x + 110, 500), (x + 350, 500)]
        for rx, ry in reps:
            b.append(line(lx, ly + 48, rx, ry - 48, RED if k == 0 else BLUE, 3, "", True))
        for rx, ry in reps:
            b.append(f'<circle cx="{rx}" cy="{ry}" r="44" fill="#fff" stroke="{BLUE}" stroke-width="3"/>' + text(rx, ry + 7, "replica", 19 if False else 20, INK, "middle", 600))
        b.append(f'<circle cx="{lx}" cy="{ly}" r="48" fill="#ddeaf8" stroke="{BLUE}" stroke-width="4"/>' + text(lx, ly + 8, "leader", 21, INK, "middle", 800))
        cap = "commit record via consensus" if k == 0 else "prepare record via consensus"
        b.append(text(lx, 420, cap, 21, RED if k == 0 else BLUE, "middle", 800 if k == 0 else 600, True))
    (ax, ay), (bx, by), (cx, cy) = leaders
    b.append(arrow(ax + 52, ay, bx - 52, by, colour=INK, w=3, lines=["prepare"], weight=700))
    b.append(path(f"M{ax + 30},{ay - 46} C{ax + 300},{60} {cx - 300},{60} {cx - 30},{cy - 46}", INK, 3, "", True))
    b.append(text(1065, 100, "prepare", 22, INK, "middle", 700, True))
    b.append(cross(ax, ay, 40, RED, 7))
    b.append(mtext(270, 670, ["leader lost → new leader", "reads decision from log"], 23, RED, "middle", 800))
    return svg(W, H, b)


# ---------------------------------------------------------------- p8-saga-fail
def saga_fail():
    W, H = 1600, 560
    b = [box(100, 150, 380, 150, ["Flight", "✓ booked"], GREEN, size=30),
         box(610, 150, 380, 150, ["Hotel", "✓ booked"], GREEN, size=30),
         box(1120, 150, 380, 150, ["Car", "✗ failed"], RED, size=30, sw=4)]
    b.append(arrow(482, 225, 606, 225, colour=INK, w=3)); b.append(arrow(992, 225, 1116, 225, colour=INK, w=3))
    b.append(text(W / 2, 430, "no shared transaction · two real bookings to undo", 30, RED, "middle", 800))
    return svg(W, H, b)


# ---------------------------------------------------------------- p8-saga
def saga():
    W, H = 1600, 780
    b = [box(500, 30, 600, 74, "Orchestrator", AMBER, size=26)]
    b.append(rect(420, 116, 760, 60, "#fff", AMBER, 2, 6))
    b.append(text(800, 155, "saga s-81: step 1 done, step 2 done, step 3 failed", 22, INK, "middle", 600))
    xs = [80, 610, 1140]
    fw = [("① book flight", GREEN), ("② book hotel", GREEN), ("③ book car ✗", RED)]
    for x, (lab, c) in zip(xs, fw):
        b.append(box(x, 300, 380, 100, lab, c, size=26))
        b.append(line(800, 178, x + 190, 296, GREY, 2, "6 6"))
    b.append(arrow(462, 350, 606, 350, colour=INK, w=3)); b.append(arrow(992, 350, 1136, 350, colour=INK, w=3))
    b.append(text(40, 280, "forward", 22, MUTED, "start", 700))
    b.append(text(40, 490, "compensate", 22, RED, "start", 700))
    b.append(box(80, 510, 380, 100, "cancel flight", RED, size=26))
    b.append(box(610, 510, 380, 100, "cancel hotel", RED, size=26))
    b.append(path("M1330,402 L1330,560 L994,560", RED, 4, "", True))
    b.append(arrow(606, 560, 464, 560, colour=RED, w=4))
    b.append(text(W / 2, 700, "every step and compensation idempotent, keyed by saga id", 26, INK, "middle", 700))
    return svg(W, H, b)


# ---------------------------------------------------------------- p8-double-click
def double_click():
    s = Seq(1600, y0=20, row=66, headh=62)
    s.part("w", "Browser", GREY); s.part("r1", "API (req 1)"); s.part("r2", "API (req 2)"); s.part("k", "Key table", GREY)
    s.part("n", "Card network", GREY)
    s.msg("w", "r1", "POST /pay · key k1")
    s.msg("w", "r2", "POST /pay · key k1 (+50 ms)")
    s.msg("r1", "k", "k1? → absent")
    s.msg("r2", "k", "k1? → absent", hl=True)
    s.msg("r1", "n", "charge")
    s.msg("r2", "n", "charge", hl=True)
    s.note("r1", "n", "check then act, in two steps", "red")
    return seqfig(s, 720)


# ---------------------------------------------------------------- p8-oversell
def oversell():
    W, H = 1600, 560
    b = []
    for i in range(12):
        x, y = 80 + (i % 4) * 70, 120 + (i // 4) * 90
        b.append(f'<circle cx="{x}" cy="{y}" r="16" fill="{BLUEGREY}"/><path d="M{x - 24},{y + 46} Q{x},{y + 4} {x + 24},{y + 46} z" fill="{BLUEGREY}"/>')
        b.append(line(x + 26, y + 20, 690, 250, "#b9c4d0", 1.6, "", False))
    b.append(text(185, 440, "100 users", 24, INK, "middle", 700))
    b.append(box(700, 190, 240, 120, "seat 12", BLUE, size=28))
    for dy in (-30, 0, 30):
        b.append(line(942, 250 + dy, 1146, 250 + dy * 1.6, RED, 3.5, "", True))
    b.append(box(1150, 160, 330, 180, ["payments", "paid ×3"], RED, size=30, sw=4))
    b.append(text(W / 2, 500, "two systems, no shared transaction", 30, RED, "middle", 800))
    return svg(W, H, b)


# ---------------------------------------------------------------- p8-reservation
def reservation():
    s = Seq(1600, y0=20, row=64, headh=62)
    s.part("u", "User", GREY); s.part("b", "Booking"); s.part("i", "Inventory", GREY); s.part("p", "Payments", GREY)
    s.msg("b", "i", "", lines=["① hold seat 12 · hold h7 ·", "until +10 min · if available"])
    s.msg("i", "b", "ok", dash=True, colour=GREEN, num=False)
    s.msg("b", "p", "② charge · idempotency key h7")
    s.msg("p", "b", "ok", dash=True, colour=GREEN, num=False)
    s.msg("b", "i", "③ confirm: sold if held by h7")
    s.msg("i", "b", "1 row ✓", dash=True, colour=GREEN, num=False, lines=["**1 row ✓**"])
    s.gap(0.2)
    s.note("u", "p", "else: hold expired → 0 rows → refund (key h7) · tell user", "amber")
    return seqfig(s, 820)


# ---------------------------------------------------------------- p8-escrow
def escrow():
    W, H = 1600, 720
    b = [box(300, 30, 1000, 100, ["Ledger · budget 10,000 · granted 9,200 · remaining 800"], BLUE, size=26)]
    used = [0.7, 0.55, 0.96, 0.4, 0.8, 0.62, 1.0, 0.5, 0.75, 0.3]
    for i, u in enumerate(used):
        x = 30 + i * 155
        empty = i == 6
        b.append(rect(x, 330, 140, 280, "#fff", RED if empty else GREY, 4 if empty else 2.5, 10))
        b.append(text(x + 70, 364, f"shard {i + 1}", 21, INK, "middle", 700))
        b.append(mtext(x + 70, 398, ["allowance", "1,000"], 20 if False else 21, MUTED, "middle"))
        b.append(rect(x + 50, 460, 40, 120, "#eef1f4", GREY, 1.5, 4))
        b.append(rect(x + 50, 460 + 120 * (1 - u), 40, 120 * u, "#9ec5f4", "none", 0, 4))
        if i == 2:
            b.append(text(x + 70, 640, "40 left", 21, AMBER, "middle", 800))
        if empty:
            b.append(mtext(x + 70, 640, ["0 · asks", "for more"], 21, RED, "middle", 800))
    ex = 30 + 6 * 155 + 70
    b.append(line(ex - 20, 326, ex - 20, 134, RED, 4, "", True))
    b.append(line(ex + 24, 134, ex + 24, 326, GREEN, 4, "", True))
    b.append(text(ex - 34, 240, "request more", 22, RED, "end", 800, True))
    b.append(text(ex + 38, 240, "grant ≤ remaining", 22, GREEN, "start", 800, True))
    b.append(text(40, 300, "bar = allowance used", 21, MUTED, "start", 600))
    return svg(W, H, b)


FIGS = {"p8-lost-update": lost_update, "p8-two-editors": two_editors, "p8-deadlock": deadlock,
        "p8-partial-commit": partial_commit, "p8-2pc": two_pc_plain, "p8-2pc-blocked": two_pc_blocked,
        "p8-2pc-paxos": two_pc_paxos, "p8-saga-fail": saga_fail, "p8-saga": saga, "p8-double-click": double_click,
        "p8-oversell": oversell, "p8-reservation": reservation, "p8-escrow": escrow}

if __name__ == "__main__":
    save(FIGS, sys.argv[1:])
