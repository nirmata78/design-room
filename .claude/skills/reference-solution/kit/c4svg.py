#!/usr/bin/env python3
"""C4 diagrams (context, container, component) as standalone SVG, in the classic C4 palette:
dark-blue person and system boxes, mid-blue containers, light-blue components, grey externals, dashed labelled
relationships, dashed system boundaries. Hand-placed on a grid: you give x/y/w/h, it does the styling, wrapping,
anchors and labels. No PlantUML, no include files, legible at 1080p.

    import c4svg as c4
    d = c4.Diagram(1600, 860)
    d.node("tenants", 40, 300, 300, 150, "system", "Product teams (20)", "Software System",
           "Send notification intents over mTLS.", stack=True)
    d.node("np", 640, 300, 320, 170, "system", "Notification platform", "Software System", "…")
    d.edge("tenants", "np", "Send intent", "HTTPS / JSON", src="r", dst="l")
    d.save("svg/c4-context.svg")

Kinds: person · system · container · component · db (cylinder) · queue (horizontal pipe) · ext (grey system)
       · ext_person · webapp (container drawn as a browser/phone frame is NOT done: keep it a box).
Edge sides: l r t b, or a fraction along the side: "r:0.3". via=[(x, y), …] for elbows. at=(x, y) pins a label.

One canonical picture, many views (2026-11-22; GUIDELINES §7.5 of the reference-solution skill). Declare the container view
once, with since=1|2|3… and tag= on boxes and edges, then save views of it instead of redrawing the system:
    d = c4.Diagram(1600, 900, canon="containers")
    d.node("rd", …, since=1); d.node("ca", …, since=2); d.edge("rd", "ca", "get", since=2)
    d.save("svg/v1.svg", upto=1)                         # the first drawing (the only full one)
    d.save("svg/v2.svg", upto=2, new=2)                  # carried boxes at once, then only what V2 adds, marked NEW
    d.save("svg/ch3-focus.svg", keep=["rd", "ca"], attack=["ca"])           # a delta: the rest dimmed, BREAKS on one box
    d.save("svg/th-where.svg", badges={"rd": "M4 · M5", "al": "M1"})      # labels hung on the same boxes
    d.edge("rd", "ca", "get", eid="r-c"); d.save("svg/flow.svg", upto=3, flow=["e-r", "r-c"])  # numbered arrows, one per step
A component view (level 3) for a challenge: the same Diagram of the container's components with focus=["res"] (IN FOCUS),
attack=[…] or fix=[…]; the rest is dimmed when keep= is given. Every save writes <name>.steps.json (reveal plan) and
<name>.meta.json ({"canon": …, "full": …}): check_layout.py warns when one canonical picture is drawn in full twice.
"""
import html, pathlib, sys
sys.path.insert(0, str(pathlib.Path(__file__).parent))
from gtheme import ink

KIND = {  # fill, stroke, text, type-line colour  (Google theme: blue ramp for the software, grey for the outside)
    "person":     ("#174ea6", "#174ea6", "#ffffff", "#e8f0fe"),
    "system":     ("#4285f4", "#1967d2", "#ffffff", "#e8f0fe"),
    "container":  ("#8ab4f8", "#4285f4", "#202124", "#202124"),
    "db":         ("#8ab4f8", "#4285f4", "#202124", "#202124"),
    "queue":      ("#8ab4f8", "#4285f4", "#202124", "#202124"),
    "component":  ("#e8f0fe", "#4285f4", "#202124", "#5f6368"),
    "ext":        ("#5f6368", "#3c4043", "#ffffff", "#f8f9fa"),
    "ext_person": ("#3c4043", "#202124", "#ffffff", "#f8f9fa"),
    "focus":      ("#ea4335", "#c5221f", "#ffffff", "#fce8e6"),   # highlight one box on a slide
}
FONT = "Inter, Roboto, sans-serif"
EDGE = "#5f6368"
RED_, GREEN_, BLUE_, AMBER_ = "#ea4335", "#34a853", "#4285f4", "#fbbc05"
TYPE_DESC = (0.8, 0.84)      # type line and description, as a fraction of the title size (were 0.68 / 0.78: under 18 px at 1080p)

def esc(s): return html.escape(str(s))

def wrap(text, width_px, size):
    per = max(6, int(width_px / (size * 0.53)))
    lines, cur = [], ""
    for w in str(text).split():
        if cur and len(cur) + 1 + len(w) > per:
            lines.append(cur); cur = w
        else:
            cur = f"{cur} {w}".strip()
    if cur:
        lines.append(cur)
    return lines

class Diagram:
    def __init__(self, w, h, scale=1.0, canon=None):
        self.w, self.h, self.s, self.canon = w, h, scale, canon
        self.nodes, self.parts, self.edges, self.under = {}, [], [], []
        self.ends, self.nnotes = [], 0          # (a, b) per edge; notes count — for the reveal plan (units)
        self.nmeta, self.emeta, self.boundary_label = {}, [], None    # since / tag per box and edge (views)
        self.ext = []        # drawn extents; svg() trims the viewBox to them (the same box for every view: nothing moves)

    # ---- boxes -----------------------------------------------------------------------------------
    def boundary(self, x, y, w, h, label, kind="Software System", colour="#4285f4", top=None, size=23):
        """top=None: label and [kind] bottom-left (classic C4); top="left"/"right": one line along the top edge, for a
        layout whose bottom corridor carries an arrow."""
        self.boundary_label = self.boundary_label or label; self.ext.append((x, y, x + w, y + h))
        rect = (f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="10" fill="{colour}" fill-opacity="0.04" '
                f'stroke="{colour}" stroke-width="2" stroke-dasharray="9 6"/>')
        if top:
            tx, anc = (x + 16, "start") if top == "left" else (x + w - 16, "end")
            self.under.append(rect + f'<text x="{tx}" y="{y+size+6}" text-anchor="{anc}" font-family="{FONT}" font-size="{size}" '
                              f'font-weight="700" fill="{ink(colour)}">{esc(label)}<tspan font-weight="400" font-size="{size*0.9:.1f}"> · [{esc(kind)}]</tspan></text>')
            return
        self.under.append(rect +
            f'<text x="{x+16}" y="{y+h-34}" font-family="{FONT}" font-size="{size}" font-weight="700" fill="{ink(colour)}">{esc(label)}</text>'
            f'<text x="{x+16}" y="{y+h-11}" font-family="{FONT}" font-size="{size*0.9:.1f}" fill="{ink(colour)}">[{esc(kind)}]</text>')

    OVERRIDE = {}      # node id -> (type line, description line): redraw a view with technologies or mechanisms (set, build, clear)

    def node(self, nid, x, y, w, h, kind, title, typ="", desc="", stack=False, size=21, since=1, tag=None):
        if nid in Diagram.OVERRIDE: typ, desc = Diagram.OVERRIDE[nid]
        self.nmeta[nid] = dict(since=since, tag=tag)
        self.ext.append((x, y - (32 if kind in ("person", "ext_person") else 40), x + w, y + h))
        fill, stroke, fg, sub = KIND[kind]
        self.nodes[nid] = (x, y, w, h)
        out = []
        if stack:
            for d in (16, 8):
                out.append(f'<rect x="{x+d}" y="{y-d}" width="{w}" height="{h}" rx="9" fill="{fill}" '
                           f'fill-opacity="0.55" stroke="{stroke}" stroke-width="1.5"/>')
        if kind == "db":
            e = 14
            out.append(f'<path d="M{x},{y+e} a{w/2},{e} 0 0,0 {w},0 v{h-2*e} a{w/2},{e} 0 0,1 {-w},0 z" '
                       f'fill="{fill}" stroke="{stroke}" stroke-width="1.6"/>'
                       f'<ellipse cx="{x+w/2}" cy="{y+e}" rx="{w/2}" ry="{e}" fill="{fill}" stroke="{stroke}" stroke-width="1.6"/>')
            top = y + 2 * e + 4
        elif kind == "queue":
            e = 16
            out.append(f'<path d="M{x+e},{y} h{w-2*e} a{e},{h/2} 0 0,1 0,{h} h{-(w-2*e)} a{e},{h/2} 0 0,1 0,{-h} z" '
                       f'fill="{fill}" stroke="{stroke}" stroke-width="1.6"/>'
                       f'<ellipse cx="{x+w-e}" cy="{y+h/2}" rx="{e}" ry="{h/2}" fill="none" stroke="{stroke}" stroke-width="1.6"/>')
            top = y + 12
        else:
            out.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="9" fill="{fill}" stroke="{stroke}" stroke-width="1.6"/>')
            top = y + 12
        if kind in ("person", "ext_person"):                       # small head glyph, top-centre
            out.append(f'<circle cx="{x+w/2}" cy="{y-14}" r="15" fill="{fill}" stroke="{stroke}" stroke-width="1.6"/>')
        cx, inner = x + w / 2, w - 24
        tl = wrap(title, inner, size)
        dl = wrap(desc, inner, size * TYPE_DESC[1]) if desc else []
        block = len(tl) * size * 1.18 + (size * 0.98 if typ else 0) + len(dl) * size * 1.02 + (6 if dl else 0)
        cy = max(top, y + (h - block) / 2) + size * 0.85
        if typ:
            out.append(f'<text x="{cx}" y="{cy - size*0.1}" text-anchor="middle" font-family="{FONT}" font-size="{size*TYPE_DESC[0]:.1f}" '
                       f'fill="{sub}">[{esc(typ)}]</text>')
            cy += size * 0.98
        for l in tl:
            out.append(f'<text x="{cx}" y="{cy}" text-anchor="middle" font-family="{FONT}" font-size="{size}" '
                       f'font-weight="700" fill="{fg}">{esc(l)}</text>')
            cy += size * 1.18
        cy += 6
        for l in dl:
            out.append(f'<text x="{cx}" y="{cy}" text-anchor="middle" font-family="{FONT}" font-size="{size*TYPE_DESC[1]:.1f}" '
                       f'fill="{fg}" fill-opacity="0.93">{esc(l)}</text>')
            cy += size * 1.02
        self.parts.append(("n", nid, "".join(out)))

    def note(self, x, y, w, text, size=19, colour="#b06000", bg="#fef7e0"):
        lines = wrap(text, w - 24, size)
        h = len(lines) * size * 1.3 + 18; self.ext.append((x, y, x + w, y + h))
        t = "".join(f'<text x="{x+12}" y="{y+12+size*(1+1.3*i)-2}" font-family="{FONT}" font-size="{size}" fill="#3b2a07">'
                    f'{esc(l)}</text>' for i, l in enumerate(lines))
        self.parts.append(f'<g data-k="note:{self.nnotes}"><rect x="{x}" y="{y}" width="{w}" height="{h}" rx="6" fill="{bg}" '
                          f'stroke="{colour}" stroke-width="1.4"/>{t}</g>')
        self.nnotes += 1

    def text(self, x, y, s, size=16, colour="#5f6368", bold=False, anchor="start"):
        self.parts.append(f'<text x="{x}" y="{y}" text-anchor="{anchor}" font-family="{FONT}" font-size="{size}" '
                          f'font-weight="{700 if bold else 400}" fill="{colour}">{esc(s)}</text>')

    # ---- edges -----------------------------------------------------------------------------------
    def anchor(self, nid, side):
        x, y, w, h = self.nodes[nid]
        side, _, frac = side.partition(":")
        f = float(frac) if frac else 0.5
        return {"l": (x, y + h * f), "r": (x + w, y + h * f), "t": (x + w * f, y), "b": (x + w * f, y + h)}[side]

    def edge(self, a, b, label="", tech="", src="r", dst="l", via=(), at=None, colour=EDGE, dashed=True,
             both=False, size=20, width=None, since=None, until=None, tag=None, eid=None, proto=None):
        """proto="event" | "https" (2026-11-25): draws the boundary — an event is dashed deep blue and tagged [event], HTTPS is solid dark
        and tagged [HTTPS]; an explicit tech= wins. Use it wherever an event (Loan Booked) and a synchronous API call meet."""
        if proto == "event": colour, dashed, tech = "#1967d2", True, tech or "event"
        elif proto == "https": dashed, tech = False, tech or "HTTPS"
        p = [self.anchor(a, src), *via, self.anchor(b, dst)]
        self.emeta.append(dict(since=since, until=until, tag=tag, eid=eid or str(len(self.edges))))
        for px, py in p: self.ext.append((px, py, px, py))
        if at: self.ext.append((at[0] - 110, at[1] - size * 1.4, at[0] + 110, at[1] + size * 1.6))
        self.edges.append((p, label, tech, at, colour, dashed, both, size, width))
        self.ends.append((a, b))

    def _edge_svg(self, p, label, tech, at, colour, dashed, both, size, width, num=None):
        d = "M" + " L".join(f"{x:.1f},{y:.1f}" for x, y in p)
        dash = ' stroke-dasharray="8 5"' if dashed and num is None else ""
        ms = ' marker-start="url(#c4a-s)"' if both else ""
        sw, mk = ("3.2", "c4n") if num is not None else ("1.9", "c4a")
        col = "#202124" if num is not None else colour
        out = [f'<path d="{d}" fill="none" stroke="{col}" stroke-width="{sw}"{dash} marker-end="url(#{mk})"{ms}/>']
        if label:
            if at is None:                                            # midpoint of the longest segment
                segs = [(abs(p[i+1][0]-p[i][0]) + abs(p[i+1][1]-p[i][1]), i) for i in range(len(p)-1)]
                _, i = max(segs)
                at = ((p[i][0] + p[i+1][0]) / 2, (p[i][1] + p[i+1][1]) / 2)
            lines = wrap(label, width or 240, size)
            if tech:
                lines.append(f"[{tech}]")
            y0 = at[1] - (len(lines) - 1) * size * 0.6
            for k, l in enumerate(lines):
                is_t = tech and k == len(lines) - 1
                out.append(f'<text x="{at[0]:.1f}" y="{y0 + k*size*1.2:.1f}" text-anchor="middle" font-family="{FONT}" '
                           f'font-size="{size*0.95 if is_t else size:.1f}" fill="{"#5f6368" if is_t else "#202124"}" '
                           f'font-style="{"italic" if is_t else "normal"}" paint-order="stroke" stroke="#ffffff" '
                           f'stroke-width="5" stroke-linejoin="round">{esc(l)}</text>')
        if num is not None:                                           # numbered flow step: a dark disc left of the label
            if at is None:
                segs = [(abs(p[i+1][0]-p[i][0]) + abs(p[i+1][1]-p[i][1]), i) for i in range(len(p)-1)]
                _, i = max(segs); at = ((p[i][0] + p[i+1][0]) / 2, (p[i][1] + p[i+1][1]) / 2)
            lw = max((len(l) for l in wrap(label, width or 240, size)), default=0) * size * 0.27 if label else 0
            cx, cy, r = at[0] - lw - 24, at[1] - size * 0.35, 17
            out.append(f'<circle cx="{cx:.1f}" cy="{cy:.1f}" r="{r}" fill="#1967d2"/>'
                       f'<text x="{cx:.1f}" y="{cy+7:.1f}" text-anchor="middle" font-family="{FONT}" font-size="21" '
                       f'font-weight="800" fill="#ffffff">{num}</text>')
        return "".join(out)

    # ---- views --------------------------------------------------------------------------------------
    def _nvis(self, nid, upto, show):
        m = self.nmeta.get(nid, {}); tag = m.get("tag")
        return (tag is None or tag in show) and (upto is None or m.get("since", 1) <= upto)

    def _evis(self, i, upto, show, vis):
        a, b = self.ends[i]; m = self.emeta[i]
        since = m["since"] if m["since"] is not None else max(self.nmeta.get(a, {}).get("since", 1), self.nmeta.get(b, {}).get("since", 1))
        return (a in vis and b in vis and (m["tag"] is None or m["tag"] in show) and (upto is None or since <= upto)
                and (m["until"] is None or upto is None or upto <= m["until"]))

    def _isnew(self, nid, new):
        m = self.nmeta.get(nid, {})
        return (m.get("tag") in new) if m.get("tag") is not None else (m.get("since", 1) in new)

    def _mark(self, nid, colour, label, dashed):
        x, y, w, h = self.nodes[nid]; p = 9; fs = 20; pw = len(label) * fs * 0.72 + 22; ph = fs * 1.6
        dash = ' stroke-dasharray="13 8"' if dashed else ""
        return (f'<rect x="{x-p}" y="{y-p}" width="{w+2*p}" height="{h+2*p}" rx="14" fill="none" stroke="{colour}" stroke-width="4.5"{dash}/>'
                f'<rect x="{x-p}" y="{y-p-ph-2:.1f}" width="{pw:.1f}" height="{ph:.1f}" rx="6" fill="{colour}"/>'
                f'<text x="{x-p+pw/2:.1f}" y="{y-p-2-ph*0.3:.1f}" text-anchor="middle" font-family="{FONT}" font-size="{fs}" '
                f'font-weight="800" letter-spacing="1" fill="#ffffff">{esc(label)}</text>')

    def _badge(self, nid, text):
        x, y, w, h = self.nodes[nid]; fs = 21; pw = len(text) * fs * 0.6 + 22; ph = fs * 1.55
        bx, by = x + w - pw + 10, y + h - ph / 2
        return (f'<rect x="{bx:.1f}" y="{by:.1f}" width="{pw:.1f}" height="{ph:.1f}" rx="{ph/2:.1f}" fill="#fef7e0" stroke="#fbbc05" stroke-width="1.6"/>'
                f'<text x="{bx+pw/2:.1f}" y="{by+ph*0.68:.1f}" text-anchor="middle" font-family="{FONT}" font-size="{fs}" font-weight="700" fill="#b06000">{esc(text)}</text>')

    def _view(self, upto=None, show=(), new=None, keep=None, focus=(), attack=(), fix=(), badges=None, flow=None, alt=(), **_):
        show = set(show); new = {new} if isinstance(new, (int, str)) else set(new or ())
        vis = [n for n in self.nodes if self._nvis(n, upto, show)]
        evis = [i for i in range(len(self.edges)) if self._evis(i, upto, show, set(vis))]
        ids = {m["eid"]: i for i, m in enumerate(self.emeta)}
        num = {ids[f]: k + 1 for k, f in enumerate(flow or ()) if f in ids and ids[f] in evis}
        if flow and len(num) != len(flow):
            raise SystemExit(f"c4svg flow: unknown or hidden edge ids {[f for f in flow if f not in ids or ids[f] not in evis]}")
        lit = None if keep is None else set(keep) | set(focus) | set(attack) | set(fix) | set(alt)
        if num and lit is None: lit = {n for i in num for n in self.ends[i]}
        marks = [(n, RED_, "BREAKS", True) for n in attack if n in vis] + [(n, GREEN_, "FIX", False) for n in fix if n in vis] \
              + [(n, BLUE_, "IN FOCUS", False) for n in focus if n in vis] + [(n, AMBER_, "ALTERNATE", True) for n in alt if n in vis] \
              + [(n, BLUE_, "NEW", False) for n in vis if new and self._isnew(n, new) and n not in set(attack) | set(fix) | set(focus)]
        return dict(vis=vis, evis=evis, lit=lit, marks=marks, badges=dict(badges or {}), new=new, num=num)

    def svg(self, **view):
        v = self._view(**view)
        crop = None
        dim = lambda ok, svg: svg if ok else f'<g opacity="0.28">{svg}</g>'
        elit = lambda i: (i in v["num"]) if v["num"] else (v["lit"] is None or set(self.ends[i]) <= v["lit"])
        edges = "".join(f'<g data-k="e:{i}">' + dim(elit(i), self._edge_svg(*self.edges[i], num=v["num"].get(i))) + "</g>"
                        for i in v["evis"])
        parts = []
        for x in self.parts:
            if isinstance(x, tuple):
                _, nid, body = x
                if nid in v["vis"]:
                    parts.append(f'<g data-k="n:{nid}">' + dim(v["lit"] is None or nid in v["lit"], body) + "</g>")
            else:
                parts.append(x)
        parts += [f'<g data-k="m:{n}">{self._mark(n, c, lab, d)}</g>' for n, c, lab, d in v["marks"]]
        parts += [f'<g data-k="b:{n}">{self._badge(n, t)}</g>' for n, t in v["badges"].items() if n in v["vis"]]
        defs = (f'<defs><marker id="c4a" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="9" markerHeight="9" '
                f'orient="auto"><path d="M0,1 L10,5 L0,9 z" fill="{EDGE}"/></marker>'
                f'<marker id="c4a-s" viewBox="0 0 10 10" refX="1" refY="5" markerWidth="9" markerHeight="9" '
                f'orient="auto"><path d="M10,1 L0,5 L10,9 z" fill="{EDGE}"/></marker>'
                f'<marker id="c4n" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" '
                f'orient="auto"><path d="M0,1 L10,5 L0,9 z" fill="#202124"/></marker></defs>')
        body = "".join(self.under) + edges + "".join(parts)
        crop = self._crop(v) if (v["lit"] is not None and view.get("keep") is not None and view.get("crop", True)) else None
        if crop:
            # a delta view (keep=) is cropped to the boxes it is about (2026-11-22): they get the slide, not a whole system
            # drawn small. Boxes not fully inside the crop are not drawn; the boundary is left out (the slide title names it).
            x0, y0, x1, y1 = crop
            inside = lambda n: (lambda x, y, w, h: x >= x0 and y >= y0 and x + w <= x1 and y + h <= y1)(*self.nodes[n])
            keepn = {n for n in v["vis"] if n in v["lit"] or inside(n)}
            edges = "".join(f'<g data-k="e:{i}">' + dim(elit(i), self._edge_svg(*self.edges[i], num=v["num"].get(i))) + "</g>"
                            for i in v["evis"] if set(self.ends[i]) <= keepn)
            parts = [x for x in parts if not x.startswith('<g data-k="legend"') and
                     (not x.startswith('<g data-k="n:') or x.split('"')[1][2:] in keepn)]
            body = edges + "".join(parts)
        elif self.ext:
            m = 16
            x0 = max(0, min(e[0] for e in self.ext) - m); y0 = max(0, min(e[1] for e in self.ext) - m)
            x1 = min(self.w, max(e[2] for e in self.ext) + m); y1 = min(self.h, max(e[3] for e in self.ext) + m)
        else:
            x0, y0, x1, y1 = 0, 0, self.w, self.h
        w, h = x1 - x0, y1 - y0
        return (f'<svg xmlns="http://www.w3.org/2000/svg" class="c4" viewBox="{x0:.0f} {y0:.0f} {w:.0f} {h:.0f}" '
                f'width="{w*self.s:.0f}" height="{h*self.s:.0f}">{defs}'
                f'<rect x="{x0:.0f}" y="{y0:.0f}" width="{w:.0f}" height="{h:.0f}" fill="#ffffff"/>{body}</svg>')

    def _crop(self, v, m=24):
        """Bounding box of the lit boxes, their marks (pills above), the edges between them and their labels."""
        lit = [n for n in v["vis"] if n in v["lit"]]
        if not lit: return None
        xs0, ys0, xs1, ys1 = [], [], [], []
        for n in lit:
            x, y, w, h = self.nodes[n]
            top = y - (52 if any(n == k for k, *_ in v["marks"]) else 0)
            xs0.append(x); ys0.append(top); xs1.append(x + w); ys1.append(y + h)
        for i in v["evis"]:
            if set(self.ends[i]) <= set(lit):
                p, label, tech, at, *_ = self.edges[i]
                for px, py in p: xs0.append(px); xs1.append(px); ys0.append(py); ys1.append(py)
                if label and at: xs0.append(at[0] - 100); xs1.append(at[0] + 100); ys0.append(at[1] - 30); ys1.append(at[1] + 30)
        return (max(0, min(xs0) - m), max(0, min(ys0) - m), min(self.w, max(xs1) + m), min(self.h, max(ys1) + m))

    def legend(self, x, y, kinds=("person", "system", "container", "component", "ext"), vertical=False):
        names = {"person": "Person", "system": "Software system", "container": "Container", "db": "Data store",
                 "queue": "Queue / log", "component": "Component", "ext": "External system", "focus": "In focus"}
        cx, cy = x, y
        for k in kinds:
            fill, stroke, *_ = KIND[k]
            self.parts.append(f'<g data-k="legend"><rect x="{cx}" y="{cy-2}" width="22" height="22" rx="4" fill="{fill}" stroke="{stroke}"/>'
                              f'<text x="{cx+30}" y="{cy+16}" font-family="{FONT}" font-size="20" fill="#5f6368">'
                              f'{names[k]}</text></g>')
            self.ext.append((cx, cy - 2, cx + 34 + len(names[k]) * 10.6, cy + 22))
            if vertical: cy += 32
            else: cx += 44 + len(names[k]) * 10.6

    def units(self, order=None, **view):
        """Default reveal order (2026-11-21): boxes in `order` (a node id or a tuple of ids per step; default left to
        right, then top to bottom), each edge with the step that draws its second end, notes last.
        A delta view (2026-11-22): with new=, the carried boxes come at once, then only the new ones; with marks or
        badges, the picture comes at once, then each mark, then each badge, then the notes."""
        v = self._view(**view)
        notes = [[f"note:{i}"] for i in range(self.nnotes)]
        if v["num"]:                      # a numbered flow: the picture, then one arrow per step in number order
            flow = sorted(v["num"], key=v["num"].get)
            return ([[f"n:{n}" for n in v["vis"]] + [f"e:{i}" for i in v["evis"] if i not in v["num"]]]
                    + [[f"e:{i}"] for i in flow] + [[f"m:{n}"] for n, *_ in v["marks"]] + notes)
        if v["new"]:
            carried = [n for n in v["vis"] if not self._isnew(n, v["new"])]
            ecar = [i for i in v["evis"] if set(self.ends[i]) <= set(carried)]
            fresh = [n for n in v["vis"] if n not in carried]
            seq = [g if isinstance(g, (tuple, list)) else (g,) for g in (order or sorted(fresh, key=lambda n: self.nodes[n][:2]))]
            shown, done, out = set(carried), set(ecar), [[f"n:{n}" for n in carried] + [f"e:{i}" for i in ecar]]
            for g in seq:
                g = [n for n in g if n in fresh]
                if not g: continue
                shown |= set(g); keys = [k for n in g for k in (f"n:{n}", f"m:{n}")]
                for i in v["evis"]:
                    if i not in done and set(self.ends[i]) <= shown: done.add(i); keys.append(f"e:{i}")
                out.append(keys)
            return out + [[f"b:{n}"] for n in v["badges"] if n in v["vis"]] + notes
        if v["marks"] or v["badges"]:
            return ([[f"n:{n}" for n in v["vis"]] + [f"e:{i}" for i in v["evis"]]] + [[f"m:{n}"] for n, *_ in v["marks"]]
                    + [[f"b:{n}"] for n in v["badges"] if n in v["vis"]] + notes)
        if order is None:
            order = sorted(v["vis"], key=lambda n: (self.nodes[n][0], self.nodes[n][1]))
        order = [g if isinstance(g, (tuple, list)) else (g,) for g in order]
        order = [tuple(n for n in g if n in v["vis"]) for g in order]
        order = [g for g in order if g]
        named = {n for g in order for n in g}
        shown, done, out = set(n for n in v["vis"] if n not in named), set(), []
        for g in order:
            shown |= set(g)
            keys = [f"n:{n}" for n in g]
            for i in v["evis"]:
                a, b = self.ends[i]
                if i not in done and a in shown and b in shown:
                    done.add(i); keys.append(f"e:{i}")
            out.append(keys)
        if out and shown - named:
            out[0] = [f"n:{n}" for n in sorted(shown - named)] + out[0]
        out += notes
        return out

    def save(self, path, order=None, canon=None, **view):
        """view: upto, show, new, keep, focus, attack, fix, badges (see the module docstring). Writes the SVG, its reveal
        plan and its meta sidecar ({"canon": id, "full": no delta, no marks, no badges, no dimming})."""
        import json, pathlib
        p = pathlib.Path(path)
        p.write_text(self.svg(**view), encoding="utf-8")
        p.with_suffix(".steps.json").write_text(json.dumps(self.units(order, **view)), encoding="utf-8")
        full = not any(view.get(k) for k in ("new", "keep", "focus", "attack", "fix", "badges", "flow", "alt"))
        p.with_suffix(".meta.json").write_text(json.dumps({"canon": canon or self.canon or ("c4:" + (self.boundary_label or p.stem)),
                                                           "full": full}), encoding="utf-8")
        return path
