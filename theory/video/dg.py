#!/usr/bin/env python3
"""Shared drawing helpers for the course figures (diagrams_pNN.py). Plain SVG strings, stdlib only.

Primitives: text, mtext, line, arrow, box, panel, cross, tick, bracket, hatch, svg, catmull.
Sequence diagrams: Seq — participants, messages (solid, dashed, lost-with-cross, highlighted), notes,
titles; every text at 21 px or more, so a figure stays legible on a 1080p slide.
"""
import html, math, pathlib

OUT = pathlib.Path(__file__).resolve().parent / "svg"
FONT = "Inter, Helvetica, Arial, sans-serif"
BLUE, RED, GREEN, AMBER, GREY, INK, MUTED = "#1f6feb", "#cf222e", "#1a7f37", "#bf8700", "#8c959f", "#1f2328", "#57606a"
BLUEGREY = "#6e8fb5"
FILL = {BLUE: "#ddeaf8", RED: "#fde7e9", GREEN: "#dff3e4", AMBER: "#fff4d6", GREY: "#eef1f4", INK: "#ffffff"}
LIGHT = {"blue": "#eaf2fc", "amber": "#fff6e0", "red": "#fdeef0", "green": "#e9f6ec", "grey": "#f3f5f7"}


def esc(s): return html.escape(str(s))


def rich(s):
    """**bold** segments become tspans; everything else is escaped."""
    parts = str(s).split("**")
    if len(parts) == 1:
        return esc(s)
    return "".join(f'<tspan font-weight="800">{esc(p)}</tspan>' if i % 2 else esc(p) for i, p in enumerate(parts))


def text(x, y, s, size=22, fill=INK, anchor="start", weight=400, halo=False, italic=False, extra=""):
    h = ' stroke="#fff" stroke-width="7" stroke-linejoin="round" paint-order="stroke"' if halo else ""
    it = ' font-style="italic"' if italic else ""
    return (f'<text x="{x:.1f}" y="{y:.1f}" font-family="{FONT}" font-size="{size}" fill="{fill}" '
            f'text-anchor="{anchor}" font-weight="{weight}"{h}{it}{extra}>{rich(s)}</text>')


def mtext(x, y, lines, size=22, fill=INK, anchor="start", weight=400, lh=1.28, halo=False):
    """Several lines, the first baseline at y."""
    if isinstance(lines, str):
        lines = [lines]
    return "".join(text(x, y + i * size * lh, l, size, fill, anchor, weight, halo) for i, l in enumerate(lines))


def svg(w, h, body):
    marks = "".join(
        f'<marker id="ah{c[1:]}" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="8" markerHeight="8" '
        f'orient="auto-start-reverse"><path d="M0,0 L10,5 L0,10 z" fill="{c}"/></marker>'
        for c in (INK, BLUE, RED, GREEN, AMBER, GREY, MUTED, BLUEGREY))
    pat = ('<pattern id="hatch" width="12" height="12" patternUnits="userSpaceOnUse" patternTransform="rotate(45)">'
           '<rect width="12" height="12" fill="#eef1f4"/><line x1="0" y1="0" x2="0" y2="12" stroke="#a7b0ba" stroke-width="5"/></pattern>'
           '<pattern id="hatchred" width="12" height="12" patternUnits="userSpaceOnUse" patternTransform="rotate(45)">'
           '<rect width="12" height="12" fill="#fdeef0"/><line x1="0" y1="0" x2="0" y2="12" stroke="#e8a0a8" stroke-width="5"/></pattern>'
           '<pattern id="hatchamber" width="12" height="12" patternUnits="userSpaceOnUse" patternTransform="rotate(45)">'
           '<rect width="12" height="12" fill="#fff6e0"/><line x1="0" y1="0" x2="0" y2="12" stroke="#e5c56b" stroke-width="5"/></pattern>')
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}">'
            f'<defs>{marks}{pat}</defs><rect width="{w}" height="{h}" fill="#fff"/>' + "".join(body) + "</svg>\n")


def line(x1, y1, x2, y2, stroke=INK, w=2, dash="", arrow=False, start=False):
    d = f' stroke-dasharray="{dash}"' if dash else ""
    a = f' marker-end="url(#ah{stroke[1:]})"' if arrow else ""
    s = f' marker-start="url(#ah{stroke[1:]})"' if start else ""
    return f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" stroke="{stroke}" stroke-width="{w}"{d}{a}{s}/>'


def path(d, stroke=INK, w=2, dash="", arrow=False, fill="none"):
    ds = f' stroke-dasharray="{dash}"' if dash else ""
    a = f' marker-end="url(#ah{stroke[1:]})"' if arrow else ""
    return f'<path d="{d}" fill="{fill}" stroke="{stroke}" stroke-width="{w}"{ds}{a}/>'


def poly(pts, stroke=INK, w=3, fill="none", dash=""):
    ds = f' stroke-dasharray="{dash}"' if dash else ""
    return (f'<polyline points="{" ".join(f"{x:.1f},{y:.1f}" for x, y in pts)}" fill="{fill}" stroke="{stroke}" '
            f'stroke-width="{w}" stroke-linejoin="round"{ds}/>')


def arrow(x1, y1, x2, y2, label="", colour=INK, w=2.5, dash="", size=21, above=12, lines=None, weight=400, side=0):
    """A straight arrow with its label centred above the line (or beside it, for a near-vertical arrow)."""
    out = [line(x1, y1, x2, y2, colour, w, dash, True)]
    labs = lines or ([label] if label else [])
    if labs:
        mx, my = (x1 + x2) / 2, (y1 + y2) / 2
        if abs(x2 - x1) < abs(y2 - y1) * 0.6:       # mostly vertical: label to the side
            sx = side or 1
            out.append(mtext(mx + 14 * sx, my - (len(labs) - 1) * size * 0.64 + size * 0.35, labs, size,
                             colour if colour != INK else INK, "start" if sx > 0 else "end", weight, halo=True))
        else:
            out.append(mtext(mx, my - above - (len(labs) - 1) * size * 1.28, labs, size,
                             colour if colour != INK else INK, "middle", weight, halo=True))
    return "".join(out)


def rect(x, y, w, h, fill="#fff", stroke=INK, sw=2.5, rx=10, dash=""):
    ds = f' stroke-dasharray="{dash}"' if dash else ""
    return f'<rect x="{x:.1f}" y="{y:.1f}" width="{w:.1f}" height="{h:.1f}" rx="{rx}" fill="{fill}" stroke="{stroke}" stroke-width="{sw}"{ds}/>'


def box(x, y, w, h, lines, colour=BLUE, fill=None, size=22, weight=600, txt=INK, sw=2.5, dash="", first_bold=True):
    if isinstance(lines, str):
        lines = [lines]
    out = [rect(x, y, w, h, fill or FILL.get(colour, "#fff"), colour, sw, 10, dash)]
    n = len(lines); lh = size * 1.27
    y0 = y + h / 2 - (n - 1) * lh / 2 + size * 0.35
    for i, s in enumerate(lines):
        out.append(text(x + w / 2, y0 + i * lh, s, size, txt, "middle", weight if (i == 0 and first_bold) else 400))
    return "".join(out)


def panel(x, y, w, h, colour="blue", label="", size=21, at="top", lcol=MUTED):
    out = [rect(x, y, w, h, LIGHT[colour], "none", 0, 14)]
    if label:
        ly = y + size + 10 if at == "top" else y + h - 14
        out.append(text(x + 16, ly, label, size, lcol, "start", 600))
    return "".join(out)


def cross(x, y, r=13, colour=RED, w=5):
    return line(x - r, y - r, x + r, y + r, colour, w) + line(x - r, y + r, x + r, y - r, colour, w)


def tick(x, y, r=12, colour=GREEN, w=5):
    return poly([(x - r, y), (x - r * 0.3, y + r * 0.7), (x + r, y - r * 0.8)], colour, w)


def dot(x, y, r=9, fill=INK, stroke="none"):
    return f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{r}" fill="{fill}" stroke="{stroke}" stroke-width="2"/>'


def bracket(x1, x2, y, label="", colour=INK, up=True, size=21, depth=14):
    """A horizontal bracket over [x1, x2] at y, opening down (up=True puts the label above)."""
    s = -1 if up else 1
    out = [path(f"M{x1},{y - s * depth} L{x1},{y} L{x2},{y} L{x2},{y - s * depth}", colour, 2.5)]
    if label:
        out.append(text((x1 + x2) / 2, y + (s * (size + 6) if not up else -10), label, size, colour, "middle", 600))
    return "".join(out)


def vbracket(x, y1, y2, colour=INK, right=True, depth=14):
    s = 1 if right else -1
    return path(f"M{x - s * depth},{y1} L{x},{y1} L{x},{y2} L{x - s * depth},{y2}", colour, 2.5)


def hatchbar(x, y, w, h, kind="hatch", stroke=GREY):
    return f'<rect x="{x:.1f}" y="{y:.1f}" width="{w:.1f}" height="{h:.1f}" rx="6" fill="url(#{kind})" stroke="{stroke}" stroke-width="2"/>'


def bar(x, y, w, h, label="", colour=BLUE, size=21, txt="#fff", weight=600):
    out = [f'<rect x="{x:.1f}" y="{y:.1f}" width="{w:.1f}" height="{h:.1f}" rx="6" fill="{colour}"/>']
    if label:
        out.append(text(x + w / 2, y + h / 2 + size * 0.36, label, size, txt, "middle", weight))
    return "".join(out)


def title(x, y, s, size=26, fill=INK, anchor="start"):
    return text(x, y, s, size, fill, anchor, 700)


def cyl(x, y, w, h, lines, colour=BLUE, size=22):
    e = 14
    f = FILL.get(colour, "#fff")
    out = [f'<path d="M{x},{y + e} L{x},{y + h - e} A{w / 2},{e} 0 0 0 {x + w},{y + h - e} L{x + w},{y + e}" fill="{f}" stroke="{colour}" stroke-width="2.5"/>',
           f'<ellipse cx="{x + w / 2}" cy="{y + e}" rx="{w / 2}" ry="{e}" fill="{f}" stroke="{colour}" stroke-width="2.5"/>']
    if isinstance(lines, str):
        lines = [lines]
    out.append(mtext(x + w / 2, y + h / 2 + e / 2 - (len(lines) - 1) * size * 0.64 + size * 0.35, lines, size, INK, "middle", 600))
    return "".join(out)


def catmull(pts, steps=40):
    p = [pts[0]] + pts + [pts[-1]]; out = []
    for i in range(1, len(p) - 2):
        p0, p1, p2, p3 = p[i - 1], p[i], p[i + 1], p[i + 2]
        for s in range(steps):
            t = s / steps; t2, t3 = t * t, t * t * t
            out.append(tuple(0.5 * (2 * p1[k] + (-p0[k] + p2[k]) * t + (2 * p0[k] - 5 * p1[k] + 4 * p2[k] - p3[k]) * t2
                                    + (-p0[k] + 3 * p1[k] - 3 * p2[k] + p3[k]) * t3) for k in (0, 1)))
    out.append(pts[-1]); return out


def wrapw(s, width_px, size):
    per = max(6, int(width_px / (size * 0.52)))
    lines, cur = [], ""
    for w in str(s).split():
        if cur and len(cur) + 1 + len(w) > per:
            lines.append(cur); cur = w
        else:
            cur = f"{cur} {w}".strip()
    if cur:
        lines.append(cur)
    return lines


class Seq:
    """A sequence diagram. Participants left to right; one row per step.

    s = Seq(1600, y0=40); s.part("c", "Client"); s.msg("c", "s", "POST /pay"); s.lost("s", "c", "200 OK", "reply lost")
    s.note("c", "c", "timeout"); s.title("…"); body = s.body(); height = s.y
    """
    def __init__(self, width=1600, x0=40, y0=30, size=22, row=62, headh=62, boxw=None):
        self.W, self.x0, self.size, self.row, self.headh = width, x0, size, row, headh
        self.parts, self.items, self.top, self.n, self.boxw = [], [], y0, 0, boxw
        self.titles = []

    def part(self, pid, label, colour=BLUE):
        self.parts.append((pid, label, colour))

    def msg(self, a, b, label, hl=False, dash=False, colour=None, num=True, lines=None):
        self.items.append(("msg", a, b, lines or [label], hl, dash, colour, num, None))

    def lost(self, a, b, label, lostlabel="", num=True):
        self.items.append(("msg", a, b, [label], True, False, RED, num, lostlabel or "lost"))

    def fan(self, a, bs, label, hl=False, dash=False, colour=None, num=True):
        """One arrow from a to several participants on the same row (or, with a in bs reversed, several to one)."""
        self.items.append(("fan", a, bs, [label], hl, dash, colour, num))

    def gather(self, srcs, b, label, hl=False, dash=False, colour=None, num=True):
        self.items.append(("gather", b, srcs, [label], hl, dash, colour, num))

    def note(self, a, b, s, tone="amber", lines=None):
        self.items.append(("note", a, b, lines or [s], tone))

    def cross(self, a, b, la, lb, dash=True, colour=None, rows=1.8):
        """Two messages sent at the same moment in opposite directions, drawn as crossing diagonals."""
        self.items.append(("cross", a, b, la, lb, dash, colour, rows))

    def gap(self, k=0.5):
        self.items.append(("gap", k))

    def xs(self):
        n = len(self.parts); colw = (self.W - 2 * self.x0) / n
        return {p[0]: self.x0 + colw * (i + 0.5) for i, p in enumerate(self.parts)}, colw

    def body(self, title_txt=""):
        xs, colw = self.xs(); bw = self.boxw or min(colw - 30, 330)
        out, y = [], self.top
        if title_txt:
            out.append(title(self.x0, y + 26, title_txt)); y += 48
        head_y = y
        y += self.headh + 50
        msgs = []
        for it in self.items:
            if it[0] == "msg":
                _, a, b, labs, hl, dash, colour, num, lost = it
                col = colour or (RED if hl else INK)
                xa, xb = xs[a], xs[b]
                y += (len(labs) - 1) * self.size * 1.25
                if a == b:
                    msgs.append(path(f"M{xa},{y - 14} h56 v30 h-50", col, 2.5, "8 6" if dash else "", True))
                    msgs.append(mtext(xa + 68, y + 4 - (len(labs) - 1) * self.size * 1.25, labs, self.size, col, "start",
                                      700 if hl else 400, halo=True))
                    y += 20
                else:
                    sgn = 1 if xb > xa else -1
                    if lost:
                        xm = (xa + xb) / 2
                        msgs.append(line(xa, y, xm, y, col, 3))
                        msgs.append(cross(xm + sgn * 14, y, 13, RED, 5))
                        msgs.append(text(xm + sgn * 40, y + 8, lost, self.size, RED, "start" if sgn > 0 else "end", 700, True))
                        tx = (xa + xm) / 2
                        if len(labs[0]) * self.size * 0.52 > abs(xm - xa) - 50:
                            msgs.append(mtext(xa + sgn * 40, y - 12, labs, self.size, col, "start" if sgn > 0 else "end", 700, halo=True))
                            labs = []
                    else:
                        msgs.append(line(xa, y, xb - sgn * 4, y, col, 3 if hl else 2.5, "9 7" if dash else "", True))
                        tx = (xa + xb) / 2
                    msgs.append(mtext(tx, y - 12 - (len(labs) - 1) * self.size * 1.25, labs, self.size, col, "middle",
                                      700 if hl else 400, halo=True))
                if num:
                    self.n += 1
                    cx = xa + (18 if xb >= xa else -18) * (1 if a != b else 0) - (0 if a != b else 22)
                    msgs.append(f'<circle cx="{cx:.1f}" cy="{y:.1f}" r="14" fill="#fff" stroke="{col}" stroke-width="2"/>')
                    msgs.append(text(cx, y + 7, str(self.n), 18, col, "middle", 700))
                y += self.row
            elif it[0] in ("fan", "gather"):
                kind, a, bs, labs, hl, dash, colour, num = it
                col = colour or (RED if hl else INK)
                xa = xs[a]; far = max(bs, key=lambda q: abs(xs[q] - xa)); near = min(bs, key=lambda q: abs(xs[q] - xa))
                xf = xs[far]; sgn = 1 if xf > xa else -1
                if kind == "fan":
                    msgs.append(line(xa, y, xf - sgn * 4, y, col, 3 if hl else 2.5, "9 7" if dash else "", True))
                    for q in bs:
                        if q != far:
                            x = xs[q] - sgn * 4
                            msgs.append(f'<path d="M{x - sgn * 14},{y - 7} L{x},{y} L{x - sgn * 14},{y + 7} z" fill="{col}"/>')
                else:
                    msgs.append(line(xf, y, xa + sgn * 4, y, col, 3 if hl else 2.5, "9 7" if dash else "", True))
                    for q in bs:
                        msgs.append(dot(xs[q], y, 6, col))
                if abs(xs[near] - xa) - 40 > len(labs[0]) * self.size * 0.5 or not labs[0]:
                    msgs.append(mtext((xa + xs[near]) / 2, y - 12, labs, self.size, col, "middle", 700 if hl else 400, halo=True))
                else:
                    msgs.append(mtext(xa + sgn * 40, y - 12, labs, self.size, col, "start" if sgn > 0 else "end", 700 if hl else 400, halo=True))
                if num:
                    self.n += 1
                    cx = xa + sgn * 18 if kind == "fan" else xf - sgn * 18
                    msgs.append(f'<circle cx="{cx:.1f}" cy="{y:.1f}" r="14" fill="#fff" stroke="{col}" stroke-width="2"/>')
                    msgs.append(text(cx, y + 7, str(self.n), 18, col, "middle", 700))
                y += self.row
            elif it[0] == "note":
                _, a, b, labs, tone = it
                bg, bd = {"amber": ("#fff6e0", AMBER), "red": ("#fdeef0", RED), "green": ("#e9f6ec", GREEN),
                          "blue": ("#eaf2fc", BLUE), "grey": ("#f3f5f7", GREY)}[tone]
                x1 = min(xs[a], xs[b]) - bw / 2; x2 = max(xs[a], xs[b]) + bw / 2
                h = len(labs) * self.size * 1.28 + 22
                y -= self.row * 0.45
                msgs.append(rect(x1, y, x2 - x1, h, bg, bd, 2, 8))
                msgs.append(mtext((x1 + x2) / 2, y + 11 + self.size * 0.95, labs, self.size, INK, "middle", 600))
                y += h + self.row * 0.8
            elif it[0] == "cross":
                _, a, b, la, lb, dash, colour, rows = it
                col = colour or MUTED; xa, xb = xs[a], xs[b]; dy = self.row * rows
                for (x1, x2, lab) in ((xa, xb, la), (xb, xa, lb)):
                    sg = 1 if x2 > x1 else -1
                    msgs.append(line(x1, y, x2 - sg * 4, y + dy, col, 2.5, "9 7" if dash else "", True))
                    self.n += 1
                    msgs.append(f'<circle cx="{x1 + sg * 18:.1f}" cy="{y:.1f}" r="14" fill="#fff" stroke="{col}" stroke-width="2"/>')
                    msgs.append(text(x1 + sg * 18, y + 7, str(self.n), 18, col, "middle", 700))
                    msgs.append(text(x1 + sg * 44, y - 10, lab, self.size, col, "start" if sg > 0 else "end", 600, True))
                y += dy + self.row
            elif it[0] == "gap":
                y += self.row * it[1]
        bottom = y - self.row * 0.5
        for pid, label, colour in self.parts:
            x = xs[pid]
            out.append(line(x, head_y + self.headh, x, bottom, "#aab3bd", 2, "6 6"))
            labs = label if isinstance(label, list) else [label]
            out.append(box(x - bw / 2, head_y, bw, self.headh, labs, colour, size=self.size))
        self.y = bottom
        return "".join(out + msgs)


def save(figs, only=None):
    OUT.mkdir(exist_ok=True)
    for name, fn in figs.items():
        if only and name not in only:
            continue
        (OUT / f"{name}.svg").write_text(fn(), encoding="utf-8")
        print("wrote", name)
