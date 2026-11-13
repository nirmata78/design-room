#!/usr/bin/env python3
"""Part 1 figures (diagrams/p01.md) as plain SVG strings. Run: python3 diagrams_p01.py → svg/p1-*.svg"""
import html, math, pathlib

OUT = pathlib.Path(__file__).resolve().parent / "svg"
FONT = "Inter, Helvetica, Arial, sans-serif"
BLUE, RED, GREEN, AMBER, GREY, INK, MUTED = "#1f6feb", "#cf222e", "#1a7f37", "#bf8700", "#8c959f", "#1f2328", "#57606a"
BLUEGREY = "#6e8fb5"

def esc(s): return html.escape(str(s))

def text(x, y, s, size=22, fill=INK, anchor="start", weight=400, halo=False, extra=""):
    h = ' stroke="#fff" stroke-width="7" stroke-linejoin="round" paint-order="stroke"' if halo else ""
    return (f'<text x="{x:.1f}" y="{y:.1f}" font-family="{FONT}" font-size="{size}" fill="{fill}" '
            f'text-anchor="{anchor}" font-weight="{weight}"{h}{extra}>{s if s.startswith("<tspan") else esc(s)}</text>')

def svg(w, h, body):
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}">'
            f'<defs><marker id="ah" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="9" markerHeight="9" orient="auto-start-reverse">'
            f'<path d="M0,0 L10,5 L0,10 z" fill="#5b6672"/></marker></defs>'
            f'<rect width="{w}" height="{h}" fill="#fff"/>' + "".join(body) + "</svg>\n")

def line(x1, y1, x2, y2, stroke=INK, w=2, dash="", arrow=False):
    d = f' stroke-dasharray="{dash}"' if dash else ""
    a = ' marker-end="url(#ah)"' if arrow else ""
    return f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" stroke="{stroke}" stroke-width="{w}"{d}{a}/>'

def box(x, y, w, h, lines, fill="#ddeaf8", stroke=BLUE, color=INK, size=22, weight=600):
    out = [f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="10" fill="{fill}" stroke="{stroke}" stroke-width="2.5"/>']
    n = len(lines); lh = size * 1.25
    y0 = y + h / 2 - (n - 1) * lh / 2 + size * 0.35
    for i, s in enumerate(lines):
        out.append(text(x + w / 2, y0 + i * lh, s, size, color, "middle", weight if i == 0 else 400))
    return "".join(out)

def catmull(pts, steps=40):
    """Centripetal-free uniform Catmull-Rom through the points, returned as a dense polyline."""
    p = [pts[0]] + pts + [pts[-1]]; out = []
    for i in range(1, len(p) - 2):
        p0, p1, p2, p3 = p[i - 1], p[i], p[i + 1], p[i + 2]
        for s in range(steps):
            t = s / steps; t2, t3 = t * t, t * t * t
            out.append(tuple(0.5 * (2 * p1[k] + (-p0[k] + p2[k]) * t + (2 * p0[k] - 5 * p1[k] + 4 * p2[k] - p3[k]) * t2
                                    + (-p0[k] + 3 * p1[k] - 3 * p2[k] + p3[k]) * t3) for k in (0, 1)))
    out.append(pts[-1]); return out

# ---------------------------------------------------------------- p1-load-curve
def load_curve():
    W, H = 1600, 760
    L, R = 170, 1500
    LOW_TOP, LOW_BOT, HI_TOP, HI_BOT = 250, 680, 80, 190        # lower band 0..4,000; upper band 4,000..12,000 compressed
    def X(h): return L + (R - L) * h / 24
    def Y(v):
        if v <= 4000: return LOW_BOT - (LOW_BOT - LOW_TOP) * v / 4000
        return HI_BOT - (HI_BOT - HI_TOP) * (v - 4000) / 8000
    b = []
    pts = [(0, 600), (4, 350), (8, 700), (12, 1050), (16, 1150), (18, 1300), (19, 2400), (21, 3600), (23, 1200), (24, 600)]
    curve = catmull(pts)
    # shaded band above the average
    run = []
    def flush():
        if len(run) > 1:
            poly = [(X(run[0][0]), Y(1200))] + [(X(h), Y(v)) for h, v in run] + [(X(run[-1][0]), Y(1200))]
            b.append('<polygon points="' + " ".join(f"{x:.1f},{y:.1f}" for x, y in poly) + '" fill="#cf222e" fill-opacity="0.13"/>')
    for h, v in curve:
        if v > 1200: run.append((h, v))
        else: flush(); run = []
    flush()
    # axes
    b.append(line(L, LOW_BOT, R, LOW_BOT, INK, 2))
    b.append(line(L, LOW_BOT, L, LOW_TOP - 14, INK, 2)); b.append(line(L, HI_BOT + 14, L, HI_TOP, INK, 2))
    for yy in (LOW_TOP - 14, HI_BOT + 14):                    # break marks
        b.append(line(L - 14, yy + 6, L + 14, yy - 6, INK, 2))
    b.append(text(L + 22, (LOW_TOP + HI_BOT) / 2 + 8, "axis break · top band compressed", 20, MUTED, "start", 400, True))
    for h in (0, 4, 8, 12, 16, 20, 24):
        b.append(line(X(h), LOW_BOT, X(h), LOW_BOT + 10, INK, 2))
        b.append(text(X(h), LOW_BOT + 38, f"{h}", 22, INK, "middle"))
    b.append(text((L + R) / 2, LOW_BOT + 72, "hour of day", 22, MUTED, "middle"))
    for v in (0, 1200, 3600, 12000):
        b.append(line(L - 10, Y(v), L, Y(v), INK, 2))
        b.append(text(L - 16, Y(v) + 8, f"{v:,}", 22, INK, "end"))
    b.append(f'<text transform="translate(40,{(HI_TOP + LOW_BOT) / 2}) rotate(-90)" font-family="{FONT}" font-size="22" fill="{MUTED}" text-anchor="middle">requests a second</text>')
    # reference lines
    b.append(line(L, Y(1200), R, Y(1200), GREY, 3, "14 10"))
    b.append(line(L, Y(3600), R, Y(3600), RED, 3, "3 8"))
    # curve and spike
    b.append('<polyline points="' + " ".join(f"{X(h):.1f},{Y(v):.1f}" for h, v in curve) + f'" fill="none" stroke="{BLUE}" stroke-width="5" stroke-linejoin="round"/>')
    base = min(curve, key=lambda p: abs(p[0] - 14))[1]
    b.append(f'<polyline points="{X(14 - 1/6):.1f},{Y(base):.1f} {X(14):.1f},{Y(12000):.1f} {X(14 + 1/6):.1f},{Y(base):.1f}" '
             f'fill="none" stroke="{RED}" stroke-width="5" stroke-linejoin="round"/>')
    # labels
    b.append(text(L + 20, Y(1200) + 32, "average · 1,200 /s", 22, MUTED, "start", 600, True))
    b.append(text(L + 20, Y(3600) - 14, "daily peak · 3× average", 22, RED, "start", 600, True))
    b.append(text(X(14) + 22, Y(12000) + 22, "burst · 10× for minutes", 22, RED, "start", 600, True))
    b.append(text(X(19.9), Y(1200) + (Y(1900) - Y(1200)), "over the average for", 21, RED, "middle", 400, True))
    b.append(text(X(19.9), Y(1200) + (Y(1900) - Y(1200)) + 26, "about six hours a day", 21, RED, "middle", 400, True))
    return svg(W, H, b)

# ---------------------------------------------------------------- p1-latency-ladder
def latency_ladder():
    W, H = 1600, 760
    L, R = 600, 1330
    lo, hi = -8, -1                       # 10 ns … 100 ms (log10 seconds)
    def X(sec): return L + (R - L) * (math.log10(sec) - lo) / (hi - lo)
    rows = [("Memory access", 100e-9, "100 ns", BLUEGREY),
            ("Read from a flash drive", 100e-6, "100 µs", BLUEGREY),
            ("Round trip in one datacentre", 0.5e-3, "0.5 ms", BLUEGREY),
            ("Seek on a spinning disk", 10e-3, "10 ms", AMBER),
            ("Round trip between regions, one continent", 30e-3, "30 ms", RED),
            ("Round trip across an ocean", 120e-3, "100–150 ms", RED)]
    b = []; top, step, bh = 60, 82, 50
    AX = top + step * len(rows) + 10
    for lab, t in (("100 ns", 1e-7), ("1 µs", 1e-6), ("10 µs", 1e-5), ("100 µs", 1e-4), ("1 ms", 1e-3), ("10 ms", 1e-2), ("100 ms", 1e-1)):
        b.append(line(X(t), top - 10, X(t), AX, "#d0d7de", 1.5, "4 6"))
        b.append(line(X(t), AX, X(t), AX + 10, INK, 2))
        b.append(text(X(t), AX + 38, lab, 22, INK, "middle"))
    b.append(line(L, AX, X(0.2), AX, INK, 2))
    b.append(text((L + R) / 2, AX + 72, "time, log scale: each gridline is ten times the one before", 21, MUTED, "middle"))
    for i, (name, sec, val, col) in enumerate(rows):
        y = top + i * step
        b.append(text(L - 18, y + bh / 2 + 8, name, 22, INK, "end", 600))
        b.append(f'<rect x="{L}" y="{y}" width="{X(sec) - L:.1f}" height="{bh}" rx="4" fill="{col}"/>')
        b.append(text(X(sec) + 12, y + bh / 2 + 8, val, 22, col if col != BLUEGREY else INK, "start", 700))
    b.append(line(L, top - 10, L, AX, INK, 2))
    bx, by, bw, bhh = 960, H - 76, 600, 56
    b.append(f'<rect x="{bx}" y="{by}" width="{bw}" height="{bhh}" rx="10" fill="#fff8e6" stroke="{AMBER}" stroke-width="2.5"/>')
    b.append(text(bx + bw / 2, by + 36, "one ocean crossing = 240 datacentre round trips", 22, INK, "middle", 600))
    return svg(W, H, b)

# ---------------------------------------------------------------- p1-series-parallel
def series_parallel():
    W, H = 1600, 700
    b = [line(800, 30, 800, H - 30, "#d0d7de", 2.5)]
    b.append(text(400, 70, "In series: multiply availabilities", 28, INK, "middle", 700))
    b.append(text(1200, 70, "In parallel: multiply unavailabilities", 28, INK, "middle", 700))
    # left: Request → A → B → C → Response
    cy = 270
    b.append(text(20, cy + 8, "Request", 22, MUTED, "start", 600))
    xs = [140, 330, 520]
    for x, n in zip(xs, "ABC"):
        b.append(box(x, cy - 50, 130, 100, [n, "99.9%"]))
    b.append(line(115, cy, xs[0] - 4, cy, "#5b6672", 2.5, arrow=True))
    for a, c in zip(xs, xs[1:]):
        b.append(line(a + 130, cy, c - 4, cy, "#5b6672", 2.5, arrow=True))
    b.append(line(xs[-1] + 130, cy, 680, cy, "#5b6672", 2.5, arrow=True))
    b.append(text(686, cy + 8, "Response", 22, MUTED, "start", 600))
    b.append(text(400, 470, "0.999 × 0.999 × 0.999 = 99.7%", 36, RED, "middle", 700))
    b.append(text(400, 520, "26 hours down a year", 24, INK, "middle"))
    # right: Request → fork → two replicas → join → Response
    b.append(text(830, cy + 8, "Request", 22, MUTED, "start", 600))
    fx, jx = 960, 1400
    b.append(line(925, cy, fx, cy, "#5b6672", 2.5))
    for yy, name in ((cy - 95, "Replica 1"), (cy + 95, "Replica 2")):
        b.append(f'<polyline points="{fx},{cy} {fx},{yy} {1036},{yy}" fill="none" stroke="#5b6672" stroke-width="2.5" marker-end="url(#ah)"/>')
        b.append(box(1040, yy - 42, 240, 84, [name, "99%"], "#e6f4ea", GREEN))
        b.append(f'<polyline points="1280,{yy} {jx},{yy} {jx},{cy}" fill="none" stroke="#5b6672" stroke-width="2.5"/>')
    b.append(line(jx, cy, 1446, cy, "#5b6672", 2.5, arrow=True))
    b.append(text(1452, cy + 8, "Response", 22, MUTED, "start", 600))
    b.append(text(1200, 470, "1 − (0.01 × 0.01) = 99.99%", 36, GREEN, "middle", 700))
    b.append(text(1200, 520, f'<tspan>53 minutes down a year ·&#160;</tspan><tspan fill="{RED}" font-weight="700">if they fail independently</tspan>', 24, INK, "middle"))
    return svg(W, H, b)

# ---------------------------------------------------------------- p1-utilisation-curve
def utilisation_curve():
    W, H = 1600, 760
    L, R, T, B = 190, 1500, 110, 650
    ymax = math.log10(25)
    def X(u): return L + (R - L) * u
    def Y(m): return B - (B - T) * math.log10(m) / ymax
    b = []
    b.append(f'<rect x="{X(.5):.1f}" y="{T}" width="{X(.7) - X(.5):.1f}" height="{B - T}" fill="{GREEN}" fill-opacity="0.12"/>')
    b.append(f'<rect x="{X(.9):.1f}" y="{T}" width="{X(1) - X(.9):.1f}" height="{B - T}" fill="{RED}" fill-opacity="0.13"/>')
    b.append(text((X(.5) + X(.7)) / 2, T - 18, "size for this at peak", 22, GREEN, "middle", 700))
    b.append(text(X(1), T - 18, "no room for a surprise", 22, RED, "end", 700))
    for m in (1, 2, 5, 10, 20):
        b.append(line(L, Y(m), R, Y(m), "#e6e9ed", 1.5))
        b.append(line(L - 10, Y(m), L, Y(m), INK, 2))
        b.append(text(L - 16, Y(m) + 8, f"{m}×", 22, INK, "end"))
    for u in (0, .5, .7, .8, .9, .95, 1):
        b.append(line(X(u), B, X(u), B + 10, INK, 2))
        b.append(text(X(u), B + 38, f"{round(u * 100)}%" if u else "0", 22, INK, "middle"))
    b.append(line(L, B, R, B, INK, 2)); b.append(line(L, B, L, T, INK, 2))
    b.append(text((L + R) / 2, B + 76, "utilisation: the fraction of time the server is busy", 22, MUTED, "middle"))
    b.append(f'<text transform="translate(52,{(T + B) / 2}) rotate(-90)" font-family="{FONT}" font-size="22" fill="{MUTED}" text-anchor="middle">time in system, as a multiple of service time</text>')
    pts = [(u / 1000, 1 / (1 - u / 1000)) for u in range(0, 961, 4)]
    b.append('<polyline points="' + " ".join(f"{X(u):.1f},{Y(m):.1f}" for u, m in pts) + f'" fill="none" stroke="{BLUE}" stroke-width="5" stroke-linejoin="round"/>')
    for u, m in ((.5, 2), (.8, 5), (.9, 10), (.95, 20)):
        b.append(f'<circle cx="{X(u):.1f}" cy="{Y(m):.1f}" r="9" fill="{INK}" stroke="#fff" stroke-width="3"/>')
        b.append(text(X(u) - 16, Y(m) - 10, f"{round(u * 100)}% → {m}×", 22, INK, "end", 700, True))
    return svg(W, H, b)

# ---------------------------------------------------------------- p1-fanout
def fanout():
    W, H = 1600, 720
    b = []
    cx = 540
    b.append(box(cx - 120, 40, 240, 76, ["Client"], "#eef1f4", GREY))
    b.append(box(cx - 140, 200, 280, 80, ["Root server"]))
    b.append(line(cx, 116, cx, 196, "#5b6672", 2.5, arrow=True))
    lw, gap, ell, x0, ly = 68, 12, 70, 40, 500
    xs, x = [], x0
    for i in range(12):
        xs.append(x); x += lw + gap
        if i == 5: ell_x = x; x += ell
    red_i = 8
    for i, lx in enumerate(xs):
        b.append(line(cx, 280, lx + lw / 2, ly - 4, "#9aa4ae", 2, arrow=True))
    b.append(text(ell_x + ell / 2 - 6, ly + 48, "…", 36, MUTED, "middle", 700))
    for i, lx in enumerate(xs):
        red = i == red_i
        lab = ["1 s"] if red else (["10 ms"] if i in (0, 4, 10) else [""])
        b.append(box(lx, ly, lw, 80, lab, "#fde3de" if red else "#e6f4ea", RED if red else GREEN, RED if red else INK, 20, 700))
    b.append(text(x0, ly - 180, "100 leaves, asked in parallel", 24, INK, "start", 700, True))
    b.append(text(x0, ly + 130, "the root answers only when the slowest leaf has answered", 22, MUTED, "start"))
    nx, ny, nw, nh = 1130, 230, 440, 230
    b.append(f'<rect x="{nx}" y="{ny}" width="{nw}" height="{nh}" rx="12" fill="#f6f8fa" stroke="#d0d7de" stroke-width="2.5"/>')
    b.append(text(nx + 30, ny + 60, "each leaf: slow 1 time in 100", 24, INK))
    b.append(text(nx + 30, ny + 120, "all fast: 0.99¹⁰⁰ = 37%", 24, INK))
    b.append(text(nx + 30, ny + 180, "at least one slow: 63%", 28, RED, "start", 800))
    return svg(W, H, b)

FIGS = {"p1-load-curve": load_curve, "p1-latency-ladder": latency_ladder, "p1-series-parallel": series_parallel,
        "p1-utilisation-curve": utilisation_curve, "p1-fanout": fanout}

def main():
    OUT.mkdir(exist_ok=True)
    for name, f in FIGS.items():
        (OUT / f"{name}.svg").write_text(f(), encoding="utf-8"); print("wrote", name)

if __name__ == "__main__":
    main()
