#!/usr/bin/env python3
"""State machines (lifecycles) as SVG in the Google theme, with a build-up reveal plan — the PlantUML-free replacement
for `pumlsvg kind="state"` (issue #5).

    from statesvg import States
    m = States(1600, 520)
    m.state("open", 60, 200, "Open", "accepting late events")
    m.state("closed", 620, 200, "Closed v1", "invoiced", kind="final")
    m.state("dirty", 1180, 200, "Dirty", "re-run pending", kind="warn")
    m.start("open")
    m.go("open", "closed", "H + 48 h: snapshot pinned")
    m.go("closed", "dirty", "invalidation for hour H")
    m.go("dirty", "closed", "re-run as v + 1", bend=-160)
    m.save("svg/state-hour.svg")         # + state-hour.steps.json (one state or transition per step) + .meta.json

Kinds: "state" (blue), "final" (green), "warn" (amber), "bad" (red). Transitions are straight or bent (bend = the
control point's offset from the midpoint, in px, perpendicular to the line). Labels sit on a white plate.
"""
import html, json, math, pathlib, sys
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from gtheme import FONT, INK, MUTED  # noqa: E402

KIND = {  # fill, stroke, text
    "state": ("#e8f0fe", "#1967d2", "#202124"),
    "final": ("#e6f4ea", "#188038", "#202124"),
    "warn": ("#fef7e0", "#b06000", "#202124"),
    "bad": ("#fce8e6", "#c5221f", "#202124"),
}


def esc(s): return html.escape(str(s))


class States:
    def __init__(self, w=1600, h=520, box=(380, 140), size=30):
        self.w, self.h, (self.bw, self.bh), self.size = w, h, box, size
        self.states, self.edges, self.order, self.initial = {}, [], [], None

    def state(self, sid, x, y, title, sub="", kind="state"):
        self.states[sid] = (x, y, title, sub, kind)
        self.order.append(("s", sid))

    def start(self, sid):
        self.initial = sid

    def go(self, a, b, label="", bend=0):
        self.edges.append((a, b, label, bend))
        self.order.append(("t", len(self.edges) - 1))

    def _anchor(self, sid, toward):
        x, y, *_ = self.states[sid]
        cx, cy = x + self.bw / 2, y + self.bh / 2
        dx, dy = toward[0] - cx, toward[1] - cy
        if dx == 0 and dy == 0:
            return cx, cy
        sx = (self.bw / 2) / abs(dx) if dx else 1e9
        sy = (self.bh / 2) / abs(dy) if dy else 1e9
        s = min(sx, sy)
        return cx + dx * s, cy + dy * s

    def _centre(self, sid):
        x, y, *_ = self.states[sid]
        return x + self.bw / 2, y + self.bh / 2

    def save(self, path):
        p = pathlib.Path(path)
        out = [f'<defs><marker id="st-ar" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="9" markerHeight="9" orient="auto">'
               f'<path d="M0,1 L10,5 L0,9 z" fill="{INK}"/></marker></defs>']
        if self.initial:
            x, y, *_ = self.states[self.initial]
            out.append(f'<g data-k="init"><circle cx="{x - 50}" cy="{y + self.bh / 2}" r="14" fill="{INK}"/>'
                       f'<line x1="{x - 36}" y1="{y + self.bh / 2}" x2="{x - 4}" y2="{y + self.bh / 2}" stroke="{INK}" '
                       f'stroke-width="3" marker-end="url(#st-ar)"/></g>')
        for sid, (x, y, title, sub, kind) in self.states.items():
            fill, stroke, fg = KIND[kind]
            g = [f'<rect x="{x}" y="{y}" width="{self.bw}" height="{self.bh}" rx="{self.bh / 2.6:.0f}" fill="{fill}" stroke="{stroke}" stroke-width="3"/>',
                 f'<text x="{x + self.bw / 2}" y="{y + self.bh / 2 - (6 if sub else -10)}" text-anchor="middle" font-family="{FONT}" '
                 f'font-size="{self.size}" font-weight="800" fill="{fg}">{esc(title)}</text>']
            if sub:
                g.append(f'<text x="{x + self.bw / 2}" y="{y + self.bh / 2 + 34}" text-anchor="middle" font-family="{FONT}" '
                         f'font-size="{self.size * 0.8:.0f}" fill="{MUTED}">{esc(sub)}</text>')
            out.append(f'<g data-k="s:{sid}">' + "".join(g) + "</g>")
        for i, (a, b, label, bend) in enumerate(self.edges):
            ca, cb = self._centre(a), self._centre(b)
            mx, my = (ca[0] + cb[0]) / 2, (ca[1] + cb[1]) / 2
            nx, ny = -(cb[1] - ca[1]), cb[0] - ca[0]
            n = math.hypot(nx, ny) or 1
            ctrl = (mx + nx / n * bend, my + ny / n * bend)
            pa, pb = self._anchor(a, ctrl if bend else cb), self._anchor(b, ctrl if bend else ca)
            d = f"M{pa[0]:.1f},{pa[1]:.1f} Q{ctrl[0]:.1f},{ctrl[1]:.1f} {pb[0]:.1f},{pb[1]:.1f}" if bend else \
                f"M{pa[0]:.1f},{pa[1]:.1f} L{pb[0]:.1f},{pb[1]:.1f}"
            lx, ly = ((pa[0] + 2 * ctrl[0] + pb[0]) / 4, (pa[1] + 2 * ctrl[1] + pb[1]) / 4) if bend else (mx, my)
            lw = len(label) * self.size * 0.5 + 24
            g = f'<path d="{d}" fill="none" stroke="{INK}" stroke-width="3" marker-end="url(#st-ar)"/>'
            if label:
                g += (f'<rect x="{lx - lw / 2:.1f}" y="{ly - 40:.1f}" width="{lw:.1f}" height="38" rx="6" fill="#ffffff"/>'
                      f'<text x="{lx:.1f}" y="{ly - 12:.1f}" text-anchor="middle" font-family="{FONT}" font-size="{self.size * 0.8:.0f}" '
                      f'font-weight="600" fill="{INK}">{esc(label)}</text>')
            out.append(f'<g data-k="t:{i}">{g}</g>')
        svg = (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {self.w} {self.h}" width="{self.w}" height="{self.h}">'
               f'<rect width="{self.w}" height="{self.h}" fill="#ffffff"/>{"".join(out)}</svg>')
        p.write_text(svg, encoding="utf-8")
        steps = []
        for k, ref in self.order:
            if k == "s":
                steps.append([f"s:{ref}"] + (["init"] if ref == self.initial else []))
            else:
                steps.append([f"t:{ref}"])
        p.with_suffix(".steps.json").write_text(json.dumps(steps), encoding="utf-8")
        p.with_suffix(".meta.json").write_text(json.dumps({"canon": f"state:{p.stem}", "full": True}), encoding="utf-8")
        return p
