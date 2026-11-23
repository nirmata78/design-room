#!/usr/bin/env python3
"""SRE course diagrams: one function per figure, `main()` writes svg/<name>.svg. Standard library only.

Rules (same as theory/video/diagrams/README.md): 1600 px wide, text >= 21 px, blue = normal path, red = failure or the
thing the slide is about, green = repaired path, amber = warning, grey = background. Numbers marked 'illustrative' in the
transcript are illustrative. Run:  python3 theory/sre-video/diagrams_sre.py
"""
import math, pathlib, html

OUT = pathlib.Path(__file__).resolve().parent / "svg"
C = {  # name: (fill, stroke)
    "blue": ("#dbeafe", "#1d4ed8"), "red": ("#fee2e2", "#b91c1c"), "green": ("#dcfce7", "#15803d"),
    "amber": ("#fef3c7", "#b45309"), "grey": ("#f3f4f6", "#4b5563"), "white": ("#ffffff", "#4b5563"),
}
INK = "#111827"
FONT = "font-family=\"Helvetica, Arial, sans-serif\""


def esc(s):
    return html.escape(str(s), quote=False)


class S:
    def __init__(self, h=720, w=1600):
        self.w, self.h, self.b = w, h, []

    def add(self, s):
        self.b.append(s)

    def text(self, x, y, s, size=24, anchor="middle", weight="normal", fill=INK, italic=False):
        lines = str(s).split("\n")
        y0 = y - (len(lines) - 1) * size * 0.6
        t = "".join(f'<tspan x="{x}" dy="{0 if i == 0 else size * 1.2:.0f}">{esc(l)}</tspan>' for i, l in enumerate(lines))
        st = ' font-style="italic"' if italic else ""
        self.add(f'<text x="{x}" y="{y0:.0f}" font-size="{size}" text-anchor="{anchor}" font-weight="{weight}" fill="{fill}" {FONT}{st} dominant-baseline="middle">{t}</text>')

    def box(self, x, y, w, h, label, col="blue", size=24, weight="normal", dash=False, sub=None, r=14):
        f, s = C[col]
        d = ' stroke-dasharray="10 6"' if dash else ""
        self.add(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{r}" fill="{f}" stroke="{s}" stroke-width="3"{d}/>')
        if sub:
            self.text(x + w / 2, y + h / 2 - size * 0.7, label, size, weight=weight or "bold")
            self.text(x + w / 2, y + h / 2 + size * 0.9, sub, size - 3, fill="#374151")
        else:
            self.text(x + w / 2, y + h / 2, label, size, weight=weight)

    def arrow(self, x1, y1, x2, y2, label=None, col="blue", size=21, dash=False, lx=None, ly=None, width=4, above=True):
        s = C[col][1]
        d = ' stroke-dasharray="10 7"' if dash else ""
        self.add(f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="{s}" stroke-width="{width}"{d} marker-end="url(#a-{col})"/>')
        if label:
            mx = lx if lx is not None else (x1 + x2) / 2
            my = ly if ly is not None else (y1 + y2) / 2 - (22 if above else -22)
            self.text(mx, my, label, size, fill=s, weight="bold")

    def line(self, x1, y1, x2, y2, col="grey", width=3, dash=False):
        s = C[col][1]
        d = ' stroke-dasharray="10 7"' if dash else ""
        self.add(f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="{s}" stroke-width="{width}"{d}/>')

    def poly(self, pts, col="blue", width=5, fill="none", dash=False):
        s = C[col][1]
        d = ' stroke-dasharray="10 7"' if dash else ""
        self.add(f'<polyline points="{" ".join(f"{x:.1f},{y:.1f}" for x, y in pts)}" fill="{fill}" stroke="{s}" stroke-width="{width}" stroke-linejoin="round"{d}/>')

    def dot(self, x, y, col="red", r=9):
        f, s = C[col]
        self.add(f'<circle cx="{x}" cy="{y}" r="{r}" fill="{s}"/>')

    def cross(self, x, y, size=18, col="red"):
        s = C[col][1]
        self.add(f'<line x1="{x-size}" y1="{y-size}" x2="{x+size}" y2="{y+size}" stroke="{s}" stroke-width="7"/><line x1="{x-size}" y1="{y+size}" x2="{x+size}" y2="{y-size}" stroke="{s}" stroke-width="7"/>')

    def axes(self, x0, y0, x1, y1, xl="", yl="", size=22):
        self.line(x0, y0, x1, y0, "grey", 3)
        self.line(x0, y0, x0, y1, "grey", 3)
        if xl:
            self.text((x0 + x1) / 2, y0 + 62, xl, size, fill="#374151")
        if yl:
            self.add(f'<text transform="translate({x0-110},{(y0+y1)/2}) rotate(-90)" font-size="{size}" text-anchor="middle" fill="#374151" {FONT}>{esc(yl)}</text>')

    def save(self, name):
        defs = "".join(
            f'<marker id="a-{k}" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse"><path d="M0,0 L10,5 L0,10 z" fill="{v[1]}"/></marker>'
            for k, v in C.items())
        svg = (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {self.w} {self.h}" width="{self.w}" height="{self.h}">'
               f'<defs>{defs}</defs><rect width="100%" height="100%" fill="#ffffff"/>' + "".join(self.b) + "</svg>")
        (OUT / f"{name}.svg").write_text(svg, encoding="utf-8")


# ---------------------------------------------------------------- episode 1
def e01_ops_scaling():
    s = S(720)
    x0, y0, x1, y1 = 180, 600, 1500, 90
    s.axes(x0, y0, x1, y1, "Size of the service and its traffic  →", "People needed to run it")
    pts_r = [(x0 + t * (x1 - x0 - 40), y0 - t * (y0 - y1 - 30)) for t in (0, 0.25, 0.5, 0.75, 1)]
    s.poly(pts_r, "red", 6)
    pts_g = [(x0 + t * (x1 - x0 - 40), y0 - (0.32 * math.sqrt(t) + 0.0) * (y0 - y1 - 30) * 0.9) for t in [i / 20 for i in range(21)]]
    s.poly(pts_g, "green", 6)
    s.text(640, 170, "Traditional operations: work grows with load,\nso headcount grows with it", 24, fill=C["red"][1], weight="bold")
    s.text(1130, 565, "SRE: operations capped, the rest is automation,\nso headcount grows sublinearly", 24, fill=C["green"][1], weight="bold")
    xm = x0 + 0.8 * (x1 - x0 - 40)
    s.line(xm, y0 - 0.8 * (y0 - y1 - 30), xm, y0 - 0.32 * math.sqrt(0.8) * (y0 - y1 - 30) * 0.9, "amber", 4, True)
    s.text(xm + 175, 400, "the gap is the budget\nfor the whole idea", 23, fill=C["amber"][1], weight="bold")
    s.save("e01-ops-scaling")


def e01_request_life():
    s = S(640)
    names = [("User's\nbrowser", "grey"), ("DNS and\nglobal load\nbalancer", "blue"), ("Front-end\nproxy", "blue"), ("Application\nfront end", "blue"), ("Application\nbackend", "blue"), ("Storage\nsystem", "green")]
    w, g, x, y, h = 190, 70, 50, 200, 150
    for i, (n, c) in enumerate(names):
        s.box(x + i * (w + g), y, w, h, n, c, 24)
    labels = ["1 look up name", "2 connect", "3 RPC", "4 RPC", "5 read"]
    for i in range(5):
        xa = x + i * (w + g) + w
        s.arrow(xa, y + h / 2, xa + g, y + h / 2, None)
        s.text(xa + g / 2, y - 25 - (0 if i % 2 == 0 else 35), labels[i], 21, fill=C["blue"][1], weight="bold")
    s.arrow(x + 5 * (w + g) + w / 2, y + h + 30, x + w / 2, y + h + 30, "the answer returns the same way", "green", 23, dash=True, ly=y + h + 70)
    s.text(800, 80, "Life of a request in an example service", 28, weight="bold")
    s.text(800, 560, "Each hop is chosen by a different component, with different information", 24, fill="#374151", italic=True)
    s.save("e01-request-life")


# ---------------------------------------------------------------- episode 2
def e02_budget_burndown():
    s = S(720)
    x0, y0, x1, y1 = 170, 600, 1520, 90
    s.axes(x0, y0, x1, y1, "Days in the quarter", "Error budget remaining")
    def X(d): return x0 + d / 90 * (x1 - x0)
    def Y(p): return y0 - p / 100 * (y0 - y1)
    for p in (0, 25, 50, 75, 100):
        s.text(x0 - 25, Y(p), f"{p}%", 21, anchor="end", fill="#374151")
    for d in (0, 30, 60, 90):
        s.text(X(d), y0 + 28, str(d), 21, fill="#374151")
    pts = [(0, 100), (12, 98), (12, 83), (30, 78), (30, 52), (58, 44), (58, 24), (75, 18), (90, 14)]
    s.poly([(X(d), Y(p)) for d, p in pts], "blue", 6)
    s.line(x0, Y(25), x1, Y(25), "amber", 4, True)
    s.text(x0 + 20, Y(25) - 24, "under a quarter left: smaller changes, canaries only", 22, anchor="start", fill=C["amber"][1], weight="bold")
    s.line(x0, Y(0), x1, Y(0), "red", 4, True)
    s.text(x1 - 10, Y(0) - 24, "exhausted: freeze, except security and critical fixes", 22, anchor="end", fill=C["red"][1], weight="bold")
    s.text(X(12) + 15, Y(90) - 36, "bad release", 22, anchor="start", fill=C["red"][1], weight="bold")
    s.text(X(30) + 15, Y(65) - 30, "network incident", 22, anchor="start", fill=C["red"][1], weight="bold")
    s.text(X(58) + 15, Y(34) - 30, "slow dependency", 22, anchor="start", fill=C["red"][1], weight="bold")
    s.text(X(88), Y(60), "next quarter\nthe budget refills", 22, anchor="end", fill=C["green"][1], weight="bold")
    s.save("e02-budget-burndown")


# ---------------------------------------------------------------- episode 3
def e03_automation_ladder():
    s = S(720)
    steps = [("1  No automation", "Master failed\nover by hand", "red"),
             ("2  One person's script", "A failover script in a\nhome directory", "amber"),
             ("3  Shared script", "Everyone uses one\ngeneric failover", "amber"),
             ("4  System ships it", "The database ships\nits own failover", "blue"),
             ("5  Needs none", "It notices a problem\nand fails over itself", "green")]
    w, h, x0 = 280, 150, 40
    for i, (t, d, c) in enumerate(steps):
        x, y = x0 + i * (w + 25), 500 - i * 90
        s.box(x, y, w, h, t, c, 24, sub=d)
    s.text(800, 60, "Move the intelligence into the system", 28, weight="bold")
    s.text(800, 690, "Why climb: external automation rots when the system changes, and rarely-run automation (failover) is the most fragile", 22, fill="#374151", italic=True)
    s.save("e03-automation-ladder")


def e03_empty_set():
    s = S(700)
    s.box(40, 90, 330, 110, "Decommission\nthe rack", "grey")
    s.box(430, 90, 330, 110, "Step 1: erase disks\nsucceeds", "green")
    s.box(820, 90, 330, 110, "A later step fails.\nJob is restarted", "amber")
    s.box(1210, 90, 330, 110, "Machines still needing\nerase: none (empty)", "blue")
    for xa in (370, 760, 1150):
        s.arrow(xa, 145, xa + 60, 145)
    s.box(1210, 330, 330, 130, "The tool reads an empty\nlist as \"everything\"", "red", weight="bold")
    s.arrow(1375, 200, 1375, 330, None, "red")
    s.box(700, 330, 440, 130, "Nearly the whole fleet is\nsent to be wiped", "red", weight="bold")
    s.arrow(1210, 395, 1140, 395, None, "red")
    s.text(700, 520, "Content delivery machines lost their disks within minutes.\nUsers were still served from the datacenters.", 22, anchor="start", fill="#374151", italic=True)
    s.box(40, 330, 590, 270, "", "green", dash=True)
    s.text(335, 365, "Guardrails that bound the blast radius", 24, fill=C["green"][1], weight="bold")
    for i, t in enumerate(["rate limit: N machines per hour", "fraction limit: a few percent of a pool", "input check: empty or unusually large stops", "human gate for large actions", "dry run first"]):
        s.text(70, 415 + i * 38, "•  " + t, 23, anchor="start")
    s.save("e03-empty-set")


# ---------------------------------------------------------------- episode 4
def e04_alert_path():
    s = S(560)
    items = [("Service\nexposes counters", "grey", "0"), ("Collector\nscrapes\nevery 15 s", "blue", "up to 15 s"), ("Time-series\nstore", "blue", ""),
             ("Rule engine\nevaluates\nevery 15 s", "blue", "up to 15 s"), ("Hold time\n2 minutes", "amber", "120 s"), ("Alert manager\ngroups, routes", "blue", "30 s"), ("Page on\na phone", "red", "")]
    w, g, x, y, h = 190, 38, 30, 160, 140
    for i, (n, c, d) in enumerate(items):
        s.box(x + i * (w + g), y, w, h, n, c, 22)
        if d:
            s.text(x + i * (w + g) + w / 2, y + h + 38, d, 23, fill=C[c][1], weight="bold")
        if i:
            s.arrow(x + (i - 1) * (w + g) + w, y + h / 2, x + i * (w + g), y + h / 2)
    s.text(800, 70, "Every arrow adds delay. Their sum is your time to detect.", 28, weight="bold")
    s.text(800, 440, "worst case: 15 + 15 + 120 + 30 = 180 seconds", 28, fill=C["red"][1], weight="bold")
    s.text(800, 495, "illustrative values", 21, fill="#6b7280", italic=True)
    s.save("e04-alert-path")


def e04_hierarchy():
    s = S(720)
    s.box(560, 40, 480, 90, "Global collectors (a pair)", "red", 24)
    clusters = [200, 800, 1400]
    for i, cx in enumerate(clusters):
        s.box(cx - 190, 230, 380, 80, f"Cluster collector {i+1}", "blue", 23)
        s.arrow(cx, 230, 800 + (cx - 800) * 0.25, 130, None, "blue")
        for j, dx in enumerate((-130, 0, 130)):
            s.box(cx + dx - 55, 400, 110, 70, "scraper", "grey", 20)
            s.arrow(cx + dx, 400, cx + dx * 0.3, 310, None, "grey")
            for k in (-30, 0, 30):
                s.dot(cx + dx + k, 540, "grey", 8)
                s.line(cx + dx + k, 532, cx + dx, 470, "grey", 2)
    s.text(800, 620, "tasks (thousands)", 22, fill="#374151")
    s.text(800, 680, "Each level aggregates, and discards detail it no longer needs. Alert rules live where the decision makes sense.", 22, fill="#374151", italic=True)
    s.save("e04-hierarchy")


# ---------------------------------------------------------------- episode 5
def e05_pipeline():
    s = S(640)
    items = [("Commit", "grey"), ("Hermetic\nbuild", "blue"), ("Tests", "blue"), ("Package:\nversion +\nchecksum", "blue"), ("Canary\n1 to 5%", "amber"), ("Wave 2\n25%", "amber"), ("Whole\nfleet", "green")]
    w, g, x, y, h = 170, 62, 40, 180, 140
    for i, (n, c) in enumerate(items):
        s.box(x + i * (w + g), y, w, h, n, c, 23)
        if i:
            s.arrow(x + (i - 1) * (w + g) + w, y + h / 2, x + i * (w + g), y + h / 2)
    for i in (4, 5):
        gx = x + (i) * (w + g) - g / 2 - 6
        s.text(gx + 10, y - 40, "health\ngate", 20, fill=C["red"][1], weight="bold")
        s.add(f'<polygon points="{gx},{y+h/2-22} {gx+22},{y+h/2} {gx},{y+h/2+22} {gx-22},{y+h/2}" fill="#fee2e2" stroke="{C["red"][1]}" stroke-width="3"/>')
    s.box(250, 400, 480, 90, "Last known good version", "green", 24)
    s.line(1285, y + h, 1285, 445, "red", 4, True)
    s.line(1053, y + h, 1053, 445, "red", 4, True)
    s.arrow(1285, 445, 730, 445, "any gate fails: stop and roll back,\nthrough the normal pipeline path", "red", 22, dash=True, lx=1000, ly=520)
    s.text(800, 70, "Small, reproducible, staged, reversible", 28, weight="bold")
    s.save("e05-pipeline")


# ---------------------------------------------------------------- episode 6
def e06_troubleshoot_loop():
    s = S(700)
    items = [("Problem\nreport", "grey"), ("Triage:\nstop the bleeding", "red"), ("Examine:\nmetrics, logs, traces", "blue"), ("Hypothesise\na cause", "blue"), ("Test it:\nchange one thing", "amber")]
    w, g, x, y, h = 260, 40, 60, 190, 120
    for i, (n, c) in enumerate(items):
        s.box(x + i * (w + g), y, w, h, n, c, 24)
        if i:
            s.arrow(x + (i - 1) * (w + g) + w, y + h / 2, x + i * (w + g), y + h / 2)
    ex = x + 2 * (w + g) + w / 2
    tx = x + 4 * (w + g) + w
    s.line(tx - 60, y, tx - 60, 110, "red", 4, True)
    s.line(tx - 60, 110, ex, 110, "red", 4, True)
    s.arrow(ex, 110, ex, y, None, "red", dash=True)
    s.text((ex + tx - 60) / 2, 70, "no: that is a result. Learn from it, go round again", 24, fill=C["red"][1], weight="bold")
    s.box(1100, 490, 440, 100, "Treat the cause", "green", 25)
    s.arrow(tx - 130, y + h, 1320, 490, "yes", "green", 24, lx=1360, ly=385)
    s.box(560, 490, 440, 100, "Cure: make sure it cannot\nhappen the same way", "green", 23)
    s.arrow(1100, 540, 1000, 540, None, "green")
    s.text(300, 540, "A negative result is knowledge.\nWrite it down.", 24, fill=C["red"][1], weight="bold")
    s.save("e06-troubleshoot-loop")


# ---------------------------------------------------------------- episode 7
def e07_incident_roles():
    s = S(640)
    s.box(560, 40, 480, 120, "Incident commander", "red", 27, sub="holds the high-level state;\nholds every role not delegated")
    cols = [(120, "Operations lead", "the only role that\nchanges the system", "blue"), (620, "Communications lead", "the single voice to\nstakeholders and customers", "green"), (1120, "Planning lead", "bugs, handoffs, logistics,\nthe longer-running work", "amber")]
    for x, t, d, c in cols:
        s.box(x, 280, 360, 130, t, c, 25, sub=d)
        s.arrow(800, 160, x + 180, 280, None, "grey")
    s.box(120, 490, 360, 90, "delegates, sub-incidents", "grey", 22, dash=True)
    s.arrow(300, 410, 300, 490, None, "grey")
    s.text(800, 610, "A command post, a live state document, and a clear live handoff go with the roles", 23, fill="#374151", italic=True)
    s.save("e07-incident-roles")


def e07_incident_timeline():
    s = S(640)
    y = 260
    s.arrow(60, y, 1540, y, None, "grey", width=6)
    ev = [(140, "Starts", "red"), (480, "Detected", "amber"), (760, "Engaged,\ndeclared", "blue"), (1060, "Mitigated", "green"), (1300, "Resolved", "green"), (1470, "Postmortem,\nactions", "grey")]
    for x, t, c in ev:
        s.dot(x, y, c, 14)
        s.text(x, y - 70, t, 23, weight="bold", fill=C[c][1])
    def brace(x1, x2, label, c, yy):
        s.line(x1, yy, x2, yy, c, 6)
        s.text((x1 + x2) / 2, yy + 36, label, 23, fill=C[c][1], weight="bold")
    brace(140, 480, "time to detect", "amber", 360)
    brace(480, 760, "time to engage", "blue", 440)
    brace(140, 1060, "time to mitigate: what users feel", "red", 520)
    s.text(800, 60, "Most improvement comes from shorter detect and mitigate, not from perfect root causes", 26, weight="bold")
    s.save("e07-incident-timeline")


# ---------------------------------------------------------------- episode 8
def e08_intent():
    s = S(640)
    s.box(40, 130, 440, 300, "", "blue")
    s.text(260, 175, "Intent (what the service needs)", 24, weight="bold", fill=C["blue"][1])
    for i, t in enumerate(["forecast load", "availability target", "spread across failure domains", "latency limits", "dependencies"]):
        s.text(70, 235 + i * 38, "•  " + t, 23, anchor="start")
    s.box(620, 210, 300, 140, "Solver", "amber", 28)
    s.box(1060, 130, 480, 300, "", "green")
    s.text(1300, 175, "Allocation", 24, weight="bold", fill=C["green"][1])
    for i, t in enumerate(["resources per cluster", "each one with a reason", "cost shown against availability"]):
        s.text(1090, 245 + i * 42, "•  " + t, 23, anchor="start")
    s.arrow(480, 280, 620, 280)
    s.arrow(920, 280, 1060, 280)
    s.arrow(1300, 430, 260, 430, None, "grey", dash=True)
    s.text(780, 490, "demand, hardware or dependencies change: edit the intent and recompute", 24, fill="#374151", weight="bold")
    s.save("e08-intent")


def e08_test_ladder():
    s = S(700)
    items = [("Unit", "blue"), ("Integration", "blue"), ("System tests\n(smoke, perf.,\nregression)", "blue"), ("Configuration\ntest", "amber"), ("Stress test", "amber"), ("Canary test", "amber"), ("Production\nprobe", "red")]
    w, g, x = 190, 28, 40
    for i, (n, c) in enumerate(items):
        y = 380 - i * 38
        s.box(x + i * (w + g), y, w, 120, n, c, 22)
    s.text(380, 150, "Traditional tests: before release", 25, fill=C["blue"][1], weight="bold")
    s.text(1150, 90, "Production tests", 25, fill=C["amber"][1], weight="bold")
    s.arrow(60, 560, 1540, 560, "more realistic, slower, costlier, finds failures that matter most", "grey", 23, ly=535)
    s.text(380, 630, "bug found: never ships", 23, fill=C["green"][1], weight="bold")
    s.text(1150, 630, "bug found: minutes, small slice", 23, fill=C["amber"][1], weight="bold")
    s.text(1450, 600, "after rollout:\nas fast as the alert", 21, fill=C["red"][1], weight="bold")
    s.save("e08-test-ladder")


# ---------------------------------------------------------------- episode 9
def e09_lb_layers():
    s = S(640)
    items = [("1  DNS", "picks a datacenter", "near the user, not full or down", "blue"), ("2  Virtual IP", "picks a front end", "shared address, network balancer", "blue"),
             ("3  Front end", "picks a service", "terminates the connection, makes the RPC", "blue"), ("4  Client library", "picks a backend", "from its subset, by policy", "green")]
    w, g, x, y, h = 340, 60, 40, 150, 230
    for i, (t, d, e, c) in enumerate(items):
        s.box(x + i * (w + g), y, w, h, t, c, 28, sub=d)
        s.text(x + i * (w + g) + w / 2, y + h + 55, e, 21, fill="#374151")
        if i:
            s.arrow(x + (i - 1) * (w + g) + w, y + h / 2, x + i * (w + g), y + h / 2)
    s.text(800, 70, "Each layer decides with different information, at a different speed", 27, weight="bold")
    s.text(800, 520, "slow to change (cached)  →  →  →  fast per request", 24, fill=C["amber"][1], weight="bold")
    s.save("e09-lb-layers")


def e09_subset_load():
    s = S(700)
    x0, y0 = 300, 600
    s.axes(x0, y0, 1450, 100, "", "Load on a backend, as a share of the average")
    for p in (0, 50, 100, 150):
        yy = y0 - p / 150 * 440
        s.text(x0 - 20, yy, f"{p}%", 21, anchor="end", fill="#374151")
        s.line(x0, yy, 1450, yy, "grey", 1, True)
    bars = [("least loaded\n57 connections", 63, "green"), ("average\n90 connections", 100, "blue"), ("most loaded\n109 connections", 121, "red")]
    for i, (n, p, c) in enumerate(bars):
        bx = 420 + i * 330
        hh = p / 150 * 440
        s.box(bx, y0 - hh, 230, hh, f"{p}%", c, 34, "bold", r=6)
        s.text(bx + 115, y0 + 45, n, 22)
    s.text(870, 60, "300 clients, 300 backends, each client takes a random 30% subset (90 backends)", 25, weight="bold")
    s.save("e09-subset-load")


def e09_lame_duck():
    s = S(640)
    lanes = [("Task", 130), ("Clients", 300)]
    s.text(80, 150, "Task", 26, weight="bold", anchor="middle")
    s.text(80, 330, "Clients", 26, weight="bold", anchor="middle")
    phases = [(160, 520, "Serving", "green"), (520, 880, "Lame duck:\nstill working, asks\nfor no new requests", "amber"), (880, 1200, "Draining:\nfinishing in-flight", "amber"), (1200, 1500, "Stopped", "red")]
    for a, b, t, c in phases:
        s.box(a, 90, b - a - 8, 130, t, c, 21)
    s.box(160, 270, 360, 110, "Send to this task", "blue", 23)
    s.box(520, 270, 980, 110, "Shift new requests to other tasks; no request is dropped", "green", 24)
    s.text(800, 480, "Flow control reacts to trouble (a limit near 100 active requests).\nThe lame duck state avoids the trouble.", 24, fill="#374151")
    s.text(800, 570, "The drain time must exceed the longest request in flight", 23, fill=C["red"][1], weight="bold")
    s.save("e09-lame-duck")


# ---------------------------------------------------------------- episode 10
def e10_goodput():
    s = S(720)
    x0, y0, x1, y1 = 180, 600, 1500, 90
    s.axes(x0, y0, x1, y1, "Load offered to the service  →", "Useful work completed (goodput)")
    cap = x0 + 0.42 * (x1 - x0)
    top = y0 - 0.55 * (y0 - y1)
    s.poly([(x0, y0), (cap, top), (x1 - 40, top)], "green", 6)
    pts = [(cap, top)] + [(cap + t * (x1 - 40 - cap), top + (math.sin(t * 1.15) ** 1.0) * 0.8 * (y0 - top) * t ** 0.6) for t in [i / 12 for i in range(1, 13)]]
    s.poly(pts, "red", 6)
    s.line(cap, y0, cap, y1 + 20, "grey", 3, True)
    s.text(cap, y0 + 28, "capacity", 22, fill="#374151")
    s.text(1150, top - 38, "Designed to shed: holds steady, excess is rejected cheaply", 23, fill=C["green"][1], weight="bold")
    s.text(1000, 530, "Not designed: queues, timeouts and retries\nburn effort on work nobody waits for", 23, fill=C["red"][1], weight="bold")
    s.save("e10-goodput")


def e10_retry_amp():
    s = S(640)
    names = [("Client", "grey"), ("Front end", "blue"), ("Service", "blue"), ("Database", "red")]
    w, g, x, y, h = 250, 170, 45, 230, 130
    cnt = ["1", "3", "9", "27"]
    for i, (n, c) in enumerate(names):
        s.box(x + i * (w + g), y, w, h, n, c, 28, sub=f"attempts seen: {cnt[i]}")
        if i:
            s.arrow(x + (i - 1) * (w + g) + w, y + h / 2, x + i * (w + g), y + h / 2, "3 tries", "red", 24)
    s.text(800, 90, "Three layers, each trying up to three times", 28, weight="bold")
    s.text(800, 470, "3 × 3 × 3 = 27 requests reach the database for one user action,\nat the moment it needs relief", 27, fill=C["red"][1], weight="bold")
    s.text(800, 580, "With a retry budget of 10 percent, the worst-case growth falls from nearly 3x to about 1.1x", 23, fill=C["green"][1], weight="bold")
    s.save("e10-retry-amp")


def e10_throttle():
    s = S(720)
    x0, y0, x1, y1 = 200, 600, 1480, 110
    s.axes(x0, y0, x1, y1, "Requests the backend accepted, out of the last 100 attempted  →", "Chance the client rejects locally")
    def X(a): return x0 + a / 100 * (x1 - x0)
    def Y(p): return y0 - p * (y0 - y1)
    for p in (0, 0.5, 1):
        s.text(x0 - 20, Y(p), f"{int(p*100)}%", 21, anchor="end", fill="#374151")
    for a in (0, 25, 50, 75, 100):
        s.text(X(a), y0 + 28, str(a), 21, fill="#374151")
    for K, col, lab, ly in ((2.0, "blue", "blue: K = 2", 190), (1.1, "red", "red: K = 1.1, more aggressive", 140)):
        pts = [(X(a), Y(max(0, (100 - K * a) / 101))) for a in range(100, -1, -2)]
        s.poly(pts, col, 6)
        s.text(1000, ly, lab, 24, anchor="start", fill=C[col][1], weight="bold")
    s.text(870, 60, "reject probability = max(0, (requests − K × accepts) ÷ (requests + 1)), with 100 requests", 24, weight="bold")
    s.text(1100, 300, "nothing is rejected locally while the backend\naccepts more than 1 ÷ K of the requests", 23, fill="#374151")
    s.save("e10-throttle")


def e10_deadline():
    s = S(560)
    x0, x1 = 160, 1480
    def X(t): return x0 + t / 30 * (x1 - x0)
    for t in (0, 5, 10, 15, 20, 25, 30):
        s.line(X(t), 90, X(t), 440, "grey", 1, True)
        s.text(X(t), 470, f"{t} s", 21, fill="#374151")
    rows = [("Server A", 0, 7, 30, "A spends 7 s", "blue"), ("Server B", 7, 11, 30, "B has 23 s left, spends 4 s", "blue"), ("Server C", 11, 30, 30, "C has 19 s left", "green")]
    for i, (n, a, b, dl, lab, c) in enumerate(rows):
        y = 120 + i * 105
        s.text(90, y + 30, n, 24, weight="bold")
        s.box(X(a), y, X(b) - X(a), 60, "", c, r=6)
        s.line(X(b), y + 30, X(30), y + 30, "grey", 3, True)
        s.text((X(b) if i < 2 else X(a)) + 12, y + 80, lab, 22, anchor="start", fill=C[c][1], weight="bold")
    s.line(X(30), 90, X(30), 440, "red", 5)
    s.text(X(30) - 8, 75, "same absolute deadline for the whole call tree", 23, anchor="end", fill=C["red"][1], weight="bold")
    s.text(800, 530, "If no time is left, stop: work nobody will wait for is pure waste", 24, fill="#374151", italic=True)
    s.save("e10-deadline")


def e10_metastable():
    s = S(780)
    cx, cy = 800, 360
    nodes = [("A short spike\noverloads the service", "amber"), ("Requests slow;\nclients time out", "red"), ("Clients retry:\nmore load", "red"), ("Queues grow;\ncaches go cold", "red")]
    pos = [(cx - 330, cy - 200), (cx + 330, cy - 200), (cx + 330, cy + 190), (cx - 330, cy + 190)]
    for (n, c), (x, y) in zip(nodes, pos):
        s.box(x - 190, y - 60, 380, 120, n, c, 24)
    s.arrow(pos[0][0] + 190, pos[0][1], pos[1][0] - 190, pos[1][1])
    s.arrow(pos[1][0], pos[1][1] + 60, pos[2][0], pos[2][1] - 60)
    s.arrow(pos[2][0] - 190, pos[2][1], pos[3][0] + 190, pos[3][1])
    s.arrow(pos[3][0], pos[3][1] - 60, pos[0][0], pos[0][1] + 60, "load stays\nabove capacity", "red", 22, lx=pos[3][0] - 110, ly=cy)
    s.text(cx, cy - 10, "The trigger is gone.\nThe loop sustains the outage.", 26, fill=C["red"][1], weight="bold")
    s.box(580, 670, 440, 80, "Break it: shed load, cut retries", "green", 23)
    s.save("e10-metastable")


# ---------------------------------------------------------------- episode 11
def e11_split_brain():
    s = S(720)
    s.box(260, 40, 280, 80, "Server A (leader)", "blue", 24)
    s.box(1060, 40, 280, 80, "Server B (follower)", "blue", 24)
    s.line(400, 120, 400, 690, "grey", 3, True)
    s.line(1200, 120, 1200, 690, "grey", 3, True)
    s.arrow(400, 190, 1200, 230, "heartbeats, delayed by a slow network", "amber", 22, lx=800, ly=180)
    s.text(1215, 270, "B: timeout, A is dead", 22, anchor="start", fill=C["red"][1], weight="bold")
    s.arrow(1200, 330, 400, 370, "\"power off\"", "red", 22, dash=True, lx=800, ly=305)
    s.cross(800, 352, 16)
    s.text(385, 410, "A: timeout, B is dead", 22, anchor="end", fill=C["red"][1], weight="bold")
    s.arrow(400, 470, 1200, 510, "\"power off\"", "red", 22, dash=True, lx=800, ly=445)
    s.cross(800, 490, 16)
    s.text(385, 565, "A believes it is the leader", 23, anchor="end", fill=C["red"][1], weight="bold")
    s.text(1215, 565, "B believes it is the leader", 23, anchor="start", fill=C["red"][1], weight="bold")
    s.box(560, 600, 480, 80, "Both accept writes: corruption", "red", 25, weight="bold")
    s.save("e11-split-brain")


def e11_rsm():
    s = S(700)
    s.box(40, 270, 220, 110, "Client", "grey", 26)
    reps = [("Replica 1  (leader)", 90, "blue"), ("Replica 2", 280, "blue"), ("Replica 3", 470, "blue")]
    for t, y, c in reps:
        s.box(480, y, 900, 150, "", c)
        s.text(520, y + 30, t, 24, anchor="start", weight="bold", fill=C[c][1])
        for i in range(5):
            f = "green" if i < 3 else "amber"
            s.box(540 + i * 90, y + 55, 80, 70, f"{i+1}", f, 24, r=6)
        s.box(1020, y + 55, 330, 70, "state machine", "white", 22)
        s.arrow(990, y + 90, 1020, y + 90, None, "grey", width=3)
    s.arrow(260, 325, 480, 165, "1 command", "blue", 22, lx=360, ly=215)
    s.arrow(930, 240, 930, 280, None, "blue")
    s.arrow(930, 430, 930, 470, None, "blue")
    s.text(960, 262, "2 replicate", 20, anchor="start", fill=C["blue"][1], weight="bold")
    s.text(800, 40, "Same operations, same order, on every replica", 28, weight="bold")
    s.text(800, 660, "3 committed when a majority holds the entry (green), then applied and acknowledged", 23, fill=C["green"][1], weight="bold")
    s.save("e11-rsm")


def e11_write_latency():
    s = S(700)
    regs = [(40, "Region 1", ["L", "R"], "green"), (570, "Region 2  (30 ms away)", ["R", "R"], "blue"), (1100, "Region 3  (80 ms away)", ["R"], "grey")]
    for x, t, rs, c in regs:
        s.box(x, 110, 460, 280, "", c)
        s.text(x + 230, 145, t, 25, weight="bold")
        for i, r in enumerate(rs):
            hl = (r == "L") or (x == 40) or (x == 570 and i == 0)
            col = "green" if hl else "white"
            s.box(x + 40 + i * 190, 210, 160, 120, "Leader" if r == "L" else "Replica", col, 24, weight="bold" if hl else "normal")
    s.arrow(250, 400, 640, 400, None, "green", width=6)
    s.text(450, 440, "30 ms round trip", 23, fill=C["green"][1], weight="bold")
    s.arrow(250, 520, 1180, 520, None, "grey", dash=True)
    s.text(720, 560, "80 ms: not on the critical path", 23, fill="#4b5563", weight="bold")
    s.text(800, 50, "Five replicas, three regions. A commit needs three acknowledgements.", 28, weight="bold")
    s.text(800, 630, "Commit waits for: leader + local replica + the nearest remote replica  ≈  30 ms + disk write", 25, fill=C["green"][1], weight="bold")
    s.text(800, 675, "illustrative round-trip times", 21, fill="#6b7280", italic=True)
    s.save("e11-write-latency")


def _lifelines(s, cols, top=40, bottom=690):
    for x, name, col in cols:
        s.box(x - 130, top, 260, 70, name, col, 24, weight="bold")
        s.line(x, top + 70, x, bottom, "grey", 3, True)


def e11_paxos_phases():
    s = S(760)
    X = {"P": 200, "A1": 620, "A2": 1020, "A3": 1420}
    _lifelines(s, [(X["P"], "Proposer P1", "blue"), (X["A1"], "Acceptor 1", "grey"), (X["A2"], "Acceptor 2", "grey"), (X["A3"], "Acceptor 3", "grey")])
    s.text(60, 175, "Phase 1", 26, anchor="start", weight="bold", fill=C["blue"][1])
    for k, a in enumerate(("A1", "A2", "A3")):
        s.arrow(X["P"], 160 + k * 24, X[a], 160 + k * 24, None, "blue", width=3)
    s.text(410, 150, "1a  Prepare(1)", 23, fill=C["blue"][1], weight="bold")
    for k, a in enumerate(("A1", "A2", "A3")):
        s.arrow(X[a], 280 + k * 24, X["P"], 280 + k * 24, None, "green", width=3, dash=True)
    s.text(410, 270, "1b  Promise(1): nothing accepted yet", 23, fill=C["green"][1], weight="bold")
    s.text(60, 400, "Phase 2", 26, anchor="start", weight="bold", fill=C["blue"][1])
    for k, a in enumerate(("A1", "A2", "A3")):
        s.arrow(X["P"], 400 + k * 24, X[a], 400 + k * 24, None, "blue", width=3)
    s.text(410, 385, "2a  Accept(1, value X)", 23, fill=C["blue"][1], weight="bold")
    s.arrow(X["A1"], 540, X["P"], 540, None, "green", width=3, dash=True)
    s.arrow(X["A2"], 564, X["P"], 564, None, "green", width=3, dash=True)
    s.text(410, 530, "2b  Accepted(1, X) from a majority", 23, fill=C["green"][1], weight="bold")
    s.box(1180, 500, 360, 90, "Acceptor 3: slow, no reply", "amber", 22)
    s.box(420, 630, 760, 90, "X is chosen: a majority (1 and 2) has accepted it", "green", 25, weight="bold")
    s.save("e11-paxos-phases")


def e11_paxos_recovery():
    s = S(760)
    X = {"P": 220, "A2": 700, "A3": 1180}
    _lifelines(s, [(X["P"], "Proposer P2", "blue"), (X["A2"], "Acceptor 2", "grey"), (X["A3"], "Acceptor 3", "grey")])
    s.text(60, 175, "Later", 26, anchor="start", weight="bold", fill=C["blue"][1])
    s.text(800, 150, "P2 wants value Y, and does not know X was chosen", 24, fill="#374151", italic=True)
    s.arrow(X["P"], 220, X["A2"], 220, "Prepare(2)", "blue", 23, lx=460, ly=195)
    s.arrow(X["P"], 270, X["A3"], 270, None, "blue", width=3)
    s.text(930, 250, "Prepare(2)", 23, fill=C["blue"][1], weight="bold")
    s.arrow(X["A2"], 360, X["P"], 360, "Promise(2): I already accepted (1, X)", "red", 23, lx=460, ly=335, dash=True)
    s.arrow(X["A3"], 430, X["P"], 430, None, "green", width=3, dash=True)
    s.text(960, 410, "Promise(2): nothing accepted", 23, fill=C["green"][1], weight="bold")
    s.box(120, 490, 1360, 90, "A majority answered. One reply carries an accepted value, so P2 must propose X, not Y", "red", 25, weight="bold")
    s.arrow(X["P"], 640, X["A2"], 640, "Accept(2, X)", "blue", 23, lx=460, ly=615)
    s.arrow(X["P"], 690, X["A3"], 690, None, "blue", width=3)
    s.text(930, 670, "Accept(2, X)", 23, fill=C["blue"][1], weight="bold")
    s.save("e11-paxos-recovery")


def e11_paxos_slots():
    s = S(620)
    s.text(800, 40, "Multi-Paxos: one election, then one round trip per log slot", 28, weight="bold")
    s.box(60, 110, 300, 150, "Leader elected\nonce\nPhase 1 for all\nfuture slots", "amber", 24)
    for i in range(6):
        f = "green" if i < 4 else ("amber" if i == 4 else "grey")
        s.box(430 + i * 175, 110, 155, 150, f"slot {i+1}", f, 24)
    s.text(430 + 2 * 175 + 78, 300, "each slot needs only Phase 2: Accept, then Accepted", 23, fill=C["green"][1], weight="bold")
    s.text(430 + 5 * 175 + 78, 360, "empty: a no-op fills\nit on recovery", 22, fill=C["amber"][1], weight="bold")
    s.arrow(210, 262, 210, 330, None, "amber", width=3)
    s.box(60, 340, 1040, 100, "Leader dies: a new leader runs Phase 1 once, learns what any majority accepted, and carries on", "red", 24)
    s.box(60, 480, 1480, 100, "Cost in steady state: the same as the replicated state machine, one round trip to a majority per command", "green", 24, weight="bold")
    s.save("e11-paxos-slots")


# ---------------------------------------------------------------- episode 12
def e12_cron_launch():
    s = S(720)
    s.box(120, 40, 300, 80, "Cron leader", "blue", 25)
    s.box(650, 40, 320, 80, "Replicated log", "green", 25)
    s.box(1180, 40, 300, 80, "Datacenter scheduler", "grey", 23)
    for x in (270, 810, 1330):
        s.line(x, 120, x, 690, "grey", 3, True)
    s.arrow(270, 190, 810, 190, "1  record: about to launch job J", "green", 22, ly=165)
    s.arrow(270, 270, 1330, 270, "2  launch request", "blue", 22, ly=245)
    s.cross(270, 345, 20)
    s.text(300, 345, "leader dies here", 23, anchor="start", fill=C["red"][1], weight="bold")
    s.box(120, 400, 300, 70, "New leader", "amber", 24)
    s.arrow(270, 500, 810, 500, "3  read log: started, not finished", "amber", 22, lx=640, ly=478)
    s.box(430, 560, 950, 120, "", "amber", dash=True)
    s.text(905, 590, "Idempotent steps: repeat.   State can be looked up: check, then act.", 23, weight="bold")
    s.text(905, 635, "Neither: the owner chose in advance, skip or launch again.", 23, weight="bold")
    s.text(1350, 330, "if no crash:\n4  record: finished", 22, anchor="start", fill=C["green"][1], weight="bold")
    s.save("e12-cron-launch")


def e12_moire():
    s = S(720)
    x0, y0, x1, y1 = 170, 600, 1500, 110
    s.axes(x0, y0, x1, y1, "Time  →", "Load on a shared resource")
    def pulse(t, period, width, phase):
        k = (t - phase) / period
        d = (k - round(k)) * period
        return math.exp(-(d / width) ** 2)
    T = [i * 0.5 for i in range(0, 261)]
    series = [(60, 5, 0, "blue"), (90, 6, 20, "amber"), (120, 6, 20, "green")]
    tot = []
    for t in T:
        tot.append(sum(pulse(t, p, w, ph) for p, w, ph, _ in series))
    def X(t): return x0 + t / 130 * (x1 - x0)
    def Y(v): return y0 - v * (y0 - y1) / 3.3
    for p, w, ph, c in series:
        s.poly([(X(t), Y(pulse(t, p, w, ph))) for t in T], c, 3)
    s.poly([(X(t), Y(v)) for t, v in zip(T, tot)], "red", 6)
    s.line(x0, Y(1.6), x1, Y(1.6), "red", 3, True)
    s.text(x1 - 10, Y(1.6) - 22, "capacity of the shared resource", 22, anchor="end", fill=C["red"][1], weight="bold")
    peak = max(range(len(T)), key=lambda i: tot[i] if T[i] > 20 else 0)
    s.text(X(T[peak]), Y(tot[peak]) - 30, "peaks align", 23, fill=C["red"][1], weight="bold")
    s.text(870, 60, "Three periodic pipelines, each fine alone. The shared resource sees the sum.", 26, weight="bold")
    s.text(870, 685, "illustrative", 21, fill="#6b7280", italic=True)
    s.save("e12-moire")


def e12_workflow():
    s = S(720)
    s.box(560, 40, 480, 190, "", "blue")
    s.text(800, 75, "Coordinator (task master)", 25, weight="bold")
    s.text(800, 150, "state of every unit of work,\nas pointers to uniquely\nnamed data, plus leases", 22)
    s.box(120, 330, 380, 120, "Worker 1\nlease expired: orphan", "red", 23)
    s.box(1100, 330, 380, 120, "Worker 2\nholds the valid lease", "green", 23)
    s.arrow(1290, 330, 1040, 190, "commit: accepted", "green", 22, lx=1250, ly=250)
    s.arrow(310, 330, 560, 190, "commit: refused", "red", 22, lx=330, ly=250)
    s.box(120, 560, 380, 90, "out-w1-7f3  (unique name)", "grey", 21)
    s.box(1100, 560, 380, 90, "out-w2-a91  (unique name)", "grey", 21)
    s.arrow(310, 450, 310, 560, None, "red", dash=True)
    s.arrow(1290, 450, 1290, 560, None, "green")
    s.text(800, 400, "Double guarantee:\nunique outputs, and state\ncontrolled by leases", 24, fill="#374151", weight="bold")
    s.text(800, 620, "An orphan can keep writing, but only to its own file", 23, fill=C["red"][1], weight="bold")
    s.save("e12-workflow")


# ---------------------------------------------------------------- episode 13
def e13_layers():
    s = S(720)
    x0 = 220
    s.arrow(x0, 90, 1540, 90, None, "grey", width=5)
    for x, t, c in ((x0 + 20, "Live", "green"), (620, "Deleted by a bug", "red"), (1060, "Destroyed", "grey")):
        s.dot(x, 90, c, 12)
        s.text(x, 48, t, 23, weight="bold", fill=C[c][1])
    lanes = [("Layer 1  Soft deletion", 170, 620, 1060, "green", "hidden, recoverable for a window"),
             ("Layer 2  Backups", 290, x0, 1540, "blue", "an older, separate copy to restore from"),
             ("Layer 3  Early detection", 410, x0, 1540, "amber", "out-of-band validators: counts, checksums, references"),
             ("Replication", 530, x0, 1540, "red", "copies the mistake to every replica within seconds")]
    for t, y, a, b, c, d in lanes:
        s.text(110, y + 40, t.replace("  ", "\n", 1), 21, weight="bold", fill=C[c][1])
        s.box(a, y, b - a, 80, d, c, 23, r=10)
    s.text(900, 660, "Early detection is what makes the other layers usable: a restore point only helps if you notice in time", 23, fill="#374151", italic=True)
    s.save("e13-layers")


def e13_restore_time():
    s = S(700)
    x0, y0 = 300, 600
    s.axes(x0, y0, 1450, 100, "", "Restore time at 10 GB/s (log scale)")
    ticks = [(0.01, "36 s"), (1, "1 h"), (24, "1 day"), (720, "1 month"), (8760, "1 year")]
    def Y(h): return y0 - (math.log10(h) + 2) / 7.0 * 490
    for h, l in ticks:
        s.text(x0 - 20, Y(h), l, 21, anchor="end", fill="#374151")
        s.line(x0, Y(h), 1450, Y(h), "grey", 1, True)
    bars = [("1 TB", 1e3 / 10 / 3600, "1.7 minutes", "green"), ("1 PB", 1e6 / 10 / 3600, "27.8 hours", "amber"), ("1 EB", 1e9 / 10 / 3600, "1,157 days  (3.2 years)", "red")]
    for i, (n, h, lab, c) in enumerate(bars):
        bx = 420 + i * 330
        top = Y(h)
        s.box(bx, top, 230, y0 - top, "", c, r=6)
        s.text(bx + 115, top - 28, lab, 22, weight="bold", fill=C[c][1])
        s.text(bx + 115, y0 + 40, n, 26, weight="bold")
    s.line(x0, Y(24), 1450, Y(24), "red", 4, True)
    s.text(x0 + 15, Y(24) - 22, "24-hour objective", 23, anchor="start", fill=C["red"][1], weight="bold")
    s.text(870, 40, "A bigger backup is not a faster restore", 28, weight="bold")
    s.text(870, 685, "arithmetic: size ÷ bandwidth. Illustrative bandwidth", 21, fill="#6b7280", italic=True)
    s.save("e13-restore-time")


# ---------------------------------------------------------------- episode 14
def e14_santa():
    s = S(640)
    x0, y0 = 300, 540
    s.axes(x0, y0, 1000, 90, "", "Requests per second, as a multiple of normal peak")
    for m in (0, 5, 10, 15, 20, 25):
        yy = y0 - m / 27 * 440
        s.text(x0 - 20, yy, f"{m}x", 21, anchor="end", fill="#374151")
    s.box(380, y0 - 440 / 27 * 1, 200, 440 / 27, "", "blue", r=4)
    s.text(480, y0 + 40, "a normal day's peak", 22, weight="bold")
    s.box(720, y0 - 440 / 27 * 25, 200, 440 / 27 * 25, "", "red", r=4)
    s.text(820, y0 + 40, "Christmas Eve 2011", 22, weight="bold")
    s.text(820, y0 - 440 / 27 * 25 - 28, "25x: over a million a second", 23, fill=C["red"][1], weight="bold")
    s.box(1080, 120, 480, 330, "", "amber")
    s.text(1320, 155, "What made it a hard launch", 24, weight="bold", fill=C["amber"][1])
    for i, t in enumerate(["a hard deadline", "huge publicity", "an audience of millions", "a very steep ramp-up"]):
        s.text(1110, 230 + i * 55, "•  " + t, 25, anchor="start")
    s.save("e14-santa")


# ---------------------------------------------------------------- episode 15
def e15_engagement():
    s = S(700)
    cols = [("Late review (PRR)", "amber", "after launch", "Several SREs, weeks to months, per service", "Low reach", "Finds design flaws late"),
            ("Early engagement", "blue", "from design", "Fewer people, earlier", "Medium reach", "Needs capacity at design time"),
            ("Frameworks and platform", "green", "by construction", "Low cost per service after the upfront build", "High reach", "Teams must adopt it")]
    for i, (t, c, when, cost, reach, weak) in enumerate(cols):
        x = 40 + i * 520
        s.box(x, 60, 480, 90, t, c, 27, weight="bold")
        s.text(x + 240, 195, "engages: " + when, 24, weight="bold", fill=C[c][1])
        s.box(x, 240, 480, 90, cost, "white", 22)
        s.box(x, 350, 480, 70, reach, "white", 24, weight="bold")
        s.box(x, 440, 480, 90, "Weakness: " + weak, "white", 22)
    s.save("e15-engagement")


# ---------------------------------------------------------------- episode 16
def e16_ai_serving():
    s = S(700)
    items = [("Client", "grey", 40, 150), ("Gateway:\nadmission control\nby tokens or compute", "amber", 310, 230), ("Bounded queue\nwith deadlines", "amber", 640, 220), ("Model servers on\naccelerators\n(scarce, slow to scale)", "red", 960, 260), ("Response", "green", 1330, 200)]
    y, h = 150, 150
    prev = None
    for n, c, x, w in items:
        s.box(x, y, w, h, n, c, 22)
        if prev is not None:
            s.arrow(prev, y + h / 2, x, y + h / 2)
        prev = x + w
    s.box(960, 360, 260, 80, "Cache of answers", "blue", 22)
    s.arrow(1090, 360, 1090, 300, None, "blue")
    s.box(1260, 360, 280, 80, "Smaller model:\ndegraded mode", "green", 21)
    s.arrow(1400, 360, 1400, 300, None, "green")
    s.box(40, 540, 1500, 110, "", "grey", dash=True)
    s.text(790, 575, "Changes that can fail: model version, prompt, retrieval data", 24, weight="bold")
    s.text(790, 620, "→ staged rollout, with evaluation as the health gate and an instant revert", 24, fill=C["green"][1], weight="bold")
    s.text(800, 60, "Admission control counts work in tokens, not requests: one request can cost 100x another", 25, weight="bold")
    s.save("e16-ai-serving")


def e16_course_map():
    s = S(740)
    rows = [("People", "amber", [("15 Training, interrupts,\nengagement", 15), ("16 Lessons and the close", 16)]),
            ("Operations", "blue", [("3 Toil and\nautomation", 3), ("6 On-call and\ntroubleshooting", 6), ("7 Incidents and\npostmortems", 7), ("12 Cron and\npipelines", 12)]),
            ("Failure", "red", [("9 Load\nbalancing", 9), ("10 Overload and\ncascades", 10), ("11 Consensus", 11), ("13 Data\nintegrity", 13)]),
            ("Change", "green", [("5 Releases and\nsimplicity", 5), ("8 Testing and\nSRE software", 8), ("14 Launches", 14)]),
            ("Foundations", "grey", [("1 What SRE is", 1), ("2 Risk, SLOs,\nerror budgets", 2), ("4 Monitoring\nand alerting", 4)])]
    for r, (name, c, bx) in enumerate(rows):
        y = 30 + r * 140
        s.text(110, y + 55, name, 27, weight="bold", fill=C[c][1])
        n = len(bx)
        w = (1320 - (n - 1) * 20) / n
        for i, (t, _) in enumerate(bx):
            s.box(220 + i * (w + 20), y, w, 110, t, c, 23)
    s.save("e16-course-map")


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    for name, fn in sorted(globals().items()):
        if name.startswith("e") and name[1:3].isdigit() and callable(fn):
            fn()
    print(len(list(OUT.glob("*.svg"))), "figures written to", OUT)


if __name__ == "__main__":
    main()
