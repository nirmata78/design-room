#!/usr/bin/env python3
"""ERD and data-structure diagrams as SVG, in the slide-video-kit palette (same fonts and colours as c4svg).

    from erdsvg import ERD
    d = ERD(1600, 820)
    d.entity("seat", 40, 60, 460, "event_seat", [("event_id", "bigint", "PK"), ("seat_id", "int", "PK"),
             ("state", "text", ""), ("hold_id", "uuid", "FK")], kind="focus", caption="50,000 rows / event")
    d.entity("hold", 640, 60, 400, "hold", [...])
    d.rel("seat", "hold", "N", "1", src="r:0.6", dst="l:0.3", label="hold_id")
    d.note(40, 700, 1520, "Partition by HASH(event_id)")
    d.save("svg/erd.svg")

Chen notation (conceptual model; the Lucid ERD tutorial's convention): see class Chen below.

kind: "table" (blue header), "focus" (red header), "redis" (dark header, for key-value structures), "ext" (grey).
flag: "PK", "FK", "UK", "PK,FK", "IX" or "" — shown as a small badge before the column name.
Anchors as in c4svg: "l", "r", "t", "b" with an optional fraction ("r:0.3").
"""
import html, pathlib, sys
sys.path.insert(0, str(pathlib.Path(__file__).parent))
from gtheme import ink

FONT = "Inter, Roboto, sans-serif"
MONO = "'Roboto Mono', monospace"
HEAD = {"table": "#4285f4", "focus": "#ea4335", "redis": "#202124", "ext": "#5f6368"}
BADGE = {"PK": ("#ea4335", "#fce8e6"), "FK": ("#4285f4", "#e8f0fe"), "UK": ("#34a853", "#e6f4ea"),
         "IX": ("#b06000", "#fef7e0")}
EDGE = "#5f6368"


def esc(s): return html.escape(str(s))


class ERD:
    def __init__(self, w, h, size=19):
        self.w, self.h, self.size = w, h, size
        self.ents, self.parts = {}, []
        self.keys, self.rels, self.nnotes = [], [], 0     # reveal plan (2026-11-22): tables, relations, notes

    def entity(self, eid, x, y, w, title, fields, kind="table", caption=""):
        s = self.size; rh = round(s * 1.75); hh = round(s * 2.1)
        h = hh + rh * len(fields) + (round(s * 1.5) if caption else 0) + 6
        self.ents[eid] = (x, y, w, h)
        p = [f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="8" fill="#ffffff" stroke="#5f6368" stroke-width="1.4"/>',
             f'<path d="M{x},{y + 8} a8,8 0 0 1 8,-8 h{w - 16} a8,8 0 0 1 8,8 v{hh - 8} h-{w} z" fill="{HEAD[kind]}"/>',
             f'<text x="{x + 14}" y="{y + hh * 0.68}" font-family="{MONO}" font-size="{s * 1.05:.1f}" font-weight="700" fill="#fff">{esc(title)}</text>']
        cy = y + hh
        for i, (name, typ, flag) in enumerate(fields):
            if i % 2:
                p.append(f'<rect x="{x + 1}" y="{cy}" width="{w - 2}" height="{rh}" fill="#f8f9fa"/>')
            tx = x + 14
            for f in [f for f in flag.split(",") if f]:
                fg, bg = BADGE.get(f, ("#5f6368", "#f8f9fa"))
                bw = max(s * 1.9, len(f) * s * 0.84 * 0.62 + 12)     # sized to the flag ("PK desc" fits)
                p.append(f'<rect x="{tx}" y="{cy + rh * 0.2:.1f}" width="{bw:.1f}" height="{rh * 0.6:.1f}" rx="3" fill="{bg}" stroke="{fg}" stroke-width="0.8"/>')
                p.append(f'<text x="{tx + bw / 2:.1f}" y="{cy + rh * 0.66:.1f}" text-anchor="middle" font-family="{FONT}" font-size="{s * 0.84:.1f}" font-weight="700" fill="{ink(fg)}">{esc(f)}</text>')
                tx += bw + 5
            bold = ' font-weight="700"' if "PK" in flag else ""
            p.append(f'<text x="{max(tx, x + 14 + s * 1.9 + 5) + 4:.1f}" y="{cy + rh * 0.68:.1f}" font-family="{MONO}" font-size="{s * 0.86:.1f}" fill="#202124"{bold}>{esc(name)}</text>')
            p.append(f'<text x="{x + w - 14}" y="{cy + rh * 0.68:.1f}" text-anchor="end" font-family="{MONO}" font-size="{s * 0.84:.1f}" fill="#5f6368">{esc(typ)}</text>')
            cy += rh
        if caption:
            p.append(f'<text x="{x + 14}" y="{cy + s * 1.05:.1f}" font-family="{FONT}" font-size="{s * 0.86:.1f}" font-style="italic" fill="#5f6368">{esc(caption)}</text>')
        self.parts.append(f'<g data-k="t:{eid}">' + "\n".join(p) + "</g>"); self.keys.append(eid)

    def anchor(self, eid, side):
        x, y, w, h = self.ents[eid]
        sd, _, fr = side.partition(":"); f = float(fr) if fr else 0.5
        return {"l": (x, y + h * f), "r": (x + w, y + h * f), "t": (x + w * f, y), "b": (x + w * f, y + h)}[sd]

    def rel(self, a, b, card_a="1", card_b="N", src="r", dst="l", via=(), label="", at=None, dashed=False):
        pts = [self.anchor(a, src), *via, self.anchor(b, dst)]
        d = "M" + " L".join(f"{px:.1f},{py:.1f}" for px, py in pts)
        dash = ' stroke-dasharray="7 5"' if dashed else ""
        p = [f'<path d="{d}" fill="none" stroke="{EDGE}" stroke-width="1.8"{dash}/>']
        s = self.size
        for (px, py), (qx, qy), c in ((pts[0], pts[1], card_a), (pts[-1], pts[-2], card_b)):
            dx, dy = qx - px, qy - py; n = max((dx * dx + dy * dy) ** 0.5, 1)
            ox, oy = px + dx / n * 16, py + dy / n * 16
            ox += -dy / n * 13; oy += dx / n * 13
            p.append(f'<circle cx="{px:.1f}" cy="{py:.1f}" r="4" fill="{EDGE}"/>')
            p.append(f'<text x="{ox:.1f}" y="{oy + s * 0.35:.1f}" text-anchor="middle" font-family="{FONT}" font-size="{s * 0.9:.1f}" font-weight="700" fill="#ea4335">{esc(c)}</text>')
        if label:
            mx, my = at or ((pts[0][0] + pts[-1][0]) / 2, (pts[0][1] + pts[-1][1]) / 2)
            tw = len(label) * s * 0.58 + 16
            p.append(f'<rect x="{mx - tw / 2:.1f}" y="{my - s * 0.8:.1f}" width="{tw:.1f}" height="{s * 1.45:.1f}" rx="4" fill="#ffffff"/>')
            p.append(f'<text x="{mx:.1f}" y="{my + s * 0.3:.1f}" text-anchor="middle" font-family="{MONO}" font-size="{s * 0.82:.1f}" fill="#202124">{esc(label)}</text>')
        self.parts.append(f'<g data-k="r:{len(self.rels)}">' + "\n".join(p) + "</g>"); self.rels.append((a, b))

    def note(self, x, y, w, text, size=None, colour="#b06000", bg="#fef7e0", mono=False):
        s = size or self.size * 0.95
        words, lines, cur = text.split(), [], ""
        cpl = max(int(w / (s * (0.6 if mono else 0.53))), 10)
        for wd in words:
            if len(cur) + len(wd) + 1 > cpl and cur: lines.append(cur); cur = wd
            else: cur = (cur + " " + wd).strip()
        lines.append(cur)
        h = len(lines) * s * 1.35 + s * 0.9
        fam = MONO if mono else FONT
        p = [f'<rect x="{x}" y="{y}" width="{w}" height="{h:.1f}" rx="6" fill="{bg}" stroke="{colour}" stroke-width="1.2"/>']
        for i, ln in enumerate(lines):
            p.append(f'<text x="{x + 14}" y="{y + s * 1.25 + i * s * 1.35:.1f}" font-family="{fam}" font-size="{s:.1f}" fill="#202124">{esc(ln)}</text>')
        self.parts.append(f'<g data-k="note:{self.nnotes}">' + "\n".join(p) + "</g>"); self.nnotes += 1

    def text(self, x, y, s, size=16, colour="#5f6368", bold=False, mono=False, anchor="start"):
        fw = ' font-weight="700"' if bold else ""
        self.parts.append(f'<text x="{x}" y="{y}" text-anchor="{anchor}" font-family="{MONO if mono else FONT}" font-size="{size}" fill="{ink(colour)}"{fw}>{esc(s)}</text>')

    def raw(self, svg):
        """Escape hatch for one-off shapes (bit cells, byte rulers): raw SVG elements in this canvas."""
        self.parts.append(svg)

    def units(self, order=None):
        """Reveal plan: one table per step (declaration order, or `order`: ids or tuples of ids drawn together), each
        relation with the step that draws its second table, notes last. The model builds up as it is narrated."""
        return _plan(order or self.keys, self.keys, [(f"r:{i}", a, b) for i, (a, b) in enumerate(self.rels)],
                     lambda k: f"t:{k}", self.nnotes)

    def save(self, path, order=None, canon=None):
        body = "\n".join(self.parts)
        svg = (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {self.w} {self.h}" width="{self.w}" '
               f'height="{self.h}">\n<rect width="100%" height="100%" fill="#ffffff"/>\n{body}\n</svg>\n')
        open(path, "w", encoding="utf-8").write(svg)
        _sidecars(path, self.units(order), canon or "erd-physical")


class Chen:
    """Chen-notation ERD, for the conceptual model (entities, relationships, attributes, cardinality).

        d = Chen(1600, 840)
        d.entity("u", 480, 380, "USER")                       # rectangle, centred at (cx, cy)
        d.entity("t", 1180, 720, "TIMELINE ENTRY", weak=True)  # double rectangle: weak entity
        d.rel("au", 830, 380, "AUTHORS")                      # diamond
        d.rel("in", 850, 720, "IN FEED OF", identifying=True)  # double diamond: identifying relationship
        d.attr("uid", 170, 250, "user_id", of="u", key=True)  # oval; key = underlined
        d.attr("m", 1320, 220, "media_ids", of="p", multi=True)     # double oval: multivalued
        d.attr("fc", 700, 230, "follower_count", of="u", derived=True)  # dashed oval: derived
        d.attr("pk", 1450, 690, "post_id", of="t", partial=True)   # dashed underline: partial key of a weak entity
        d.link("u", "au", "1")                                # line + cardinality (1, N, M)
        d.link("au", "p", "N", total=True)                    # double line: total participation
        d.link("u", "fo", "M", src="b:0.2", role="follower")  # recursive relationships: anchor each line
        d.legend(20, 600); d.note(...); d.save("svg/erd-chen.svg")

    Best practice (lucid.co/diagram/erd/tutorial): entities are singular nouns, relationships verbs; label every
    relationship's cardinality; one notation per diagram; split conceptual (Chen) from the physical (ERD tables).
    Lines are drawn under shapes and clipped to each shape's outline.
    """

    def __init__(self, w, h, size=22):
        self.w, self.h, self.size = w, h, size
        self.shapes, self.lines, self.top = {}, [], []
        self.owner, self.order0, self.links, self.nnotes, self._k = {}, [], [], 0, None   # reveal plan (2026-11-22)

    # ── shapes ───────────────────────────────────────────────────────────────────────────────────
    def entity(self, eid, cx, cy, label, w=None, h=None, weak=False, kind="table"):
        s = self.size; w = w or max(len(label) * s * 0.66 + 50, 200); h = h or s * 3.6
        self.shapes[eid] = ("rect", cx, cy, w, h); self.owner[eid] = eid; self.order0.append(eid); self._k = f"n:{eid}"
        col = {"table": "#4285f4", "focus": "#ea4335", "ext": "#5f6368"}[kind]
        bg = {"table": "#e8f0fe", "focus": "#fce8e6", "ext": "#f8f9fa"}[kind]
        x, y = cx - w / 2, cy - h / 2
        p = [f'<rect x="{x:.1f}" y="{y:.1f}" width="{w:.1f}" height="{h:.1f}" fill="{bg}" stroke="{col}" stroke-width="2.4"/>']
        if weak:
            p.append(f'<rect x="{x + 6:.1f}" y="{y + 6:.1f}" width="{w - 12:.1f}" height="{h - 12:.1f}" fill="none" stroke="{col}" stroke-width="1.8"/>')
        p.append(f'<text x="{cx:.1f}" y="{cy + s * 0.38:.1f}" text-anchor="middle" font-family="{FONT}" font-size="{s * 1.05:.1f}" font-weight="700" fill="#202124">{esc(label)}</text>')
        self.top.append(self._g("\n".join(p)))

    def _g(self, svg, key=None):
        return f'<g data-k="{key or self._k}">{svg}</g>'

    def rel(self, rid, cx, cy, label, w=None, h=None, identifying=False):
        s = self.size; w = w or max(len(label) * s * 0.62 + 80, 190); h = h or s * 4.4
        self.shapes[rid] = ("diamond", cx, cy, w, h); self.owner[rid] = rid; self.order0.append(rid); self._k = f"n:{rid}"
        def dia(k):
            hw, hh = w / 2 - k, h / 2 - k * h / w
            return f'M{cx:.1f},{cy - hh:.1f} L{cx + hw:.1f},{cy:.1f} L{cx:.1f},{cy + hh:.1f} L{cx - hw:.1f},{cy:.1f} Z'
        p = [f'<path d="{dia(0)}" fill="#fef7e0" stroke="#b06000" stroke-width="2.4"/>']
        if identifying:
            p.append(f'<path d="{dia(9)}" fill="none" stroke="#b06000" stroke-width="1.8"/>')
        p.append(f'<text x="{cx:.1f}" y="{cy + s * 0.33:.1f}" text-anchor="middle" font-family="{FONT}" font-size="{s * 0.86:.1f}" font-weight="700" fill="#202124">{esc(label)}</text>')
        self.top.append(self._g("\n".join(p)))

    def attr(self, aid, cx, cy, label, of=None, key=False, partial=False, multi=False, derived=False, w=None, h=None):
        s = self.size; w = w or len(label) * s * 0.58 + 44; h = h or s * 2.3
        self.shapes[aid] = ("oval", cx, cy, w, h); self.owner[aid] = of or aid; self._k = f"n:{of or aid}"
        if not of: self.order0.append(aid)
        dash = ' stroke-dasharray="7 5"' if derived else ""
        p = [f'<ellipse cx="{cx:.1f}" cy="{cy:.1f}" rx="{w / 2:.1f}" ry="{h / 2:.1f}" fill="#ffffff" stroke="#5f6368" stroke-width="1.8"{dash}/>']
        if multi:
            p.append(f'<ellipse cx="{cx:.1f}" cy="{cy:.1f}" rx="{w / 2 - 6:.1f}" ry="{h / 2 - 6:.1f}" fill="none" stroke="#5f6368" stroke-width="1.4"/>')
        fs = s * 0.8
        p.append(f'<text x="{cx:.1f}" y="{cy + fs * 0.36:.1f}" text-anchor="middle" font-family="{MONO}" font-size="{fs:.1f}" fill="#202124"'
                 f'{" font-weight=\"700\"" if key or partial else ""}>{esc(label)}</text>')
        if key or partial:
            tw = len(label) * fs * 0.6; ud = ' stroke-dasharray="5 4"' if partial else ""
            p.append(f'<line x1="{cx - tw / 2:.1f}" y1="{cy + fs * 0.62:.1f}" x2="{cx + tw / 2:.1f}" y2="{cy + fs * 0.62:.1f}" stroke="#202124" stroke-width="1.6"{ud}/>')
        self.top.append(self._g("\n".join(p)))
        if of:
            self.link(of, aid)

    # ── geometry ─────────────────────────────────────────────────────────────────────────────────
    def _anchor(self, sid, side):
        k, cx, cy, w, h = self.shapes[sid]
        sd, _, fr = side.partition(":"); f = float(fr) if fr else 0.5
        if k == "diamond":
            return {"l": (cx - w / 2, cy), "r": (cx + w / 2, cy), "t": (cx, cy - h / 2), "b": (cx, cy + h / 2)}[sd]
        x, y = cx - w / 2, cy - h / 2
        return {"l": (x, y + h * f), "r": (x + w, y + h * f), "t": (x + w * f, y), "b": (x + w * f, y + h)}[sd]

    def _clip(self, sid, tx, ty):
        """Point on shape sid's outline on the ray from its centre towards (tx, ty)."""
        k, cx, cy, w, h = self.shapes[sid]
        dx, dy = tx - cx, ty - cy
        if not dx and not dy: return cx, cy
        if k == "rect": t = 1 / max(abs(dx) / (w / 2), abs(dy) / (h / 2))
        elif k == "diamond": t = 1 / (abs(dx) / (w / 2) + abs(dy) / (h / 2))
        else: t = 1 / ((dx / (w / 2)) ** 2 + (dy / (h / 2)) ** 2) ** 0.5
        return cx + dx * t, cy + dy * t

    def link(self, a, b, card="", src=None, dst=None, via=(), total=False, role="", card_at=0.5, role_at=None):
        """Line from a to b (entity↔relationship, or owner→attribute). card: "1" | "N" | "M", printed beside the line."""
        ka, kb = self.shapes[a], self.shapes[b]
        # a line belongs to its relationship (drawn with it) or to the attribute's owner (drawn with the entity)
        rel = a if ka[0] == "diamond" else b if kb[0] == "diamond" else None
        key = f"n:{rel}" if rel else f"n:{self.owner.get(b if kb[0] == 'oval' else a, a)}"
        if rel: self.links.append((rel, self.owner[a if rel == b else b]))
        first = via[0] if via else (self._anchor(b, dst) if dst else (kb[1], kb[2]))
        last = via[-1] if via else (self._anchor(a, src) if src else (ka[1], ka[2]))
        p0 = self._anchor(a, src) if src else self._clip(a, *first)
        p1 = self._anchor(b, dst) if dst else self._clip(b, *last)
        pts = [p0, *via, p1]
        d = "M" + " L".join(f"{x:.1f},{y:.1f}" for x, y in pts)
        attr_line = kb[0] == "oval" or ka[0] == "oval"
        sw, col = (1.5, "#5f6368") if attr_line else (2.2, "#3c4043")
        if total:
            self.lines.append(self._g(f'<path d="{d}" fill="none" stroke="{col}" stroke-width="7"/>'
                                      f'<path d="{d}" fill="none" stroke="#ffffff" stroke-width="3"/>', key))
        else:
            self.lines.append(self._g(f'<path d="{d}" fill="none" stroke="{col}" stroke-width="{sw}"/>', key))
        s = self.size
        def along(fr):
            segs = list(zip(pts, pts[1:])); L = [((q[0] - p[0]) ** 2 + (q[1] - p[1]) ** 2) ** 0.5 for p, q in segs]
            tgt = sum(L) * fr
            for (p, q), l in zip(segs, L):
                if tgt <= l or (p, q) == segs[-1]:
                    t = tgt / l if l else 0; n = max(l, 1)
                    return p[0] + (q[0] - p[0]) * t, p[1] + (q[1] - p[1]) * t, -(q[1] - p[1]) / n, (q[0] - p[0]) / n
                tgt -= l
        if card:
            x, y, nx, ny = along(card_at); x += nx * 20; y += ny * 20
            self.top.append(self._g(f'<text x="{x:.1f}" y="{y + s * 0.38:.1f}" text-anchor="middle" font-family="{FONT}" font-size="{s * 1.0:.1f}" font-weight="700" fill="#ea4335">{esc(card)}</text>', key))
        if role:
            x, y, nx, ny = along(role_at if role_at is not None else max(card_at - 0.28, 0.12)); x -= nx * 22; y -= ny * 22
            self.top.append(self._g(f'<text x="{x:.1f}" y="{y + s * 0.3:.1f}" text-anchor="middle" font-family="{FONT}" font-size="{s * 0.84:.1f}" font-style="italic" fill="#5f6368">{esc(role)}</text>', key))

    # ── extras ───────────────────────────────────────────────────────────────────────────────────
    def legend(self, x, y, size=19, gap=32, rows=None):
        """Chen key, stacked vertically from (x, y): ~300 px wide, up to 9 rows (rows=[…] keeps only the kinds used)."""
        allrows = [("rect", "entity"), ("rect2", "weak entity"), ("dia", "relationship"), ("dia2", "identifying relationship"),
                ("oval", "attribute"), ("key", "key attribute"), ("oval2", "multivalued attribute"),
                ("ovald", "derived attribute"), ("dbl", "total participation")]
        rows = [r for r in allrows if rows is None or r[0] in rows]
        p = []
        for i, (k, t) in enumerate(rows):
            cy = y + i * gap; sx = x + 22
            if k.startswith("rect"):
                p.append(f'<rect x="{sx - 18}" y="{cy - 8}" width="36" height="16" fill="#e8f0fe" stroke="#4285f4" stroke-width="1.6"/>')
                if k == "rect2": p.append(f'<rect x="{sx - 14}" y="{cy - 4}" width="28" height="8" fill="none" stroke="#4285f4" stroke-width="1.2"/>')
            elif k.startswith("dia"):
                p.append(f'<path d="M{sx},{cy - 10} L{sx + 20},{cy} L{sx},{cy + 10} L{sx - 20},{cy} Z" fill="#fef7e0" stroke="#b06000" stroke-width="1.6"/>')
                if k == "dia2": p.append(f'<path d="M{sx},{cy - 5} L{sx + 10},{cy} L{sx},{cy + 5} L{sx - 10},{cy} Z" fill="none" stroke="#b06000" stroke-width="1.2"/>')
            elif k == "dbl":
                p.append(f'<line x1="{sx - 20}" y1="{cy}" x2="{sx + 20}" y2="{cy}" stroke="#3c4043" stroke-width="6"/><line x1="{sx - 20}" y1="{cy}" x2="{sx + 20}" y2="{cy}" stroke="#fff" stroke-width="2.4"/>')
            else:
                dash = ' stroke-dasharray="4 3"' if k == "ovald" else ""
                p.append(f'<ellipse cx="{sx}" cy="{cy}" rx="20" ry="9" fill="#fff" stroke="#5f6368" stroke-width="1.4"{dash}/>')
                if k == "oval2": p.append(f'<ellipse cx="{sx}" cy="{cy}" rx="15" ry="5" fill="none" stroke="#5f6368" stroke-width="1"/>')
                if k == "key": p.append(f'<line x1="{sx - 9}" y1="{cy + 3}" x2="{sx + 9}" y2="{cy + 3}" stroke="#202124" stroke-width="1.4"/>')
            p.append(f'<text x="{x + 54}" y="{cy + size * 0.35:.1f}" font-family="{FONT}" font-size="{size}" fill="#202124">{esc(t)}</text>')
        self.top.append(self._g("\n".join(p), "legend"))

    def note(self, x, y, w, text, size=None, colour="#b06000", bg="#fef7e0"):
        tmp = ERD(self.w, self.h, self.size); tmp.nnotes = self.nnotes; tmp.note(x, y, w, text, size, colour, bg)
        self.top.extend(tmp.parts); self.nnotes += 1

    def text(self, x, y, s, size=16, colour="#5f6368", bold=False, anchor="start"):
        tmp = ERD(self.w, self.h, self.size); tmp.text(x, y, s, size, colour, bold, False, anchor); self.top.extend(tmp.parts)

    def units(self, order=None):
        """Reveal plan (2026-11-22): one entity (with its attributes) or one relationship (with its lines and
        cardinalities) per step, in declaration order or `order` — the conceptual model builds up as it is narrated,
        never all at once. A relationship listed before both its entities waits until they are drawn."""
        ents = [k for k in self.order0 if self.shapes[k][0] != "diamond"]
        rels = [k for k in self.order0 if self.shapes[k][0] == "diamond"]
        # default: the entities in declaration order; each relationship gets its own step as soon as both ends are drawn
        order = list(order or ents)
        listed = {k for g in order for k in (g if isinstance(g, (tuple, list)) else (g,))}
        pending = [r for r in rels if r not in listed]
        out, shown = [["legend"]] if any('data-k="legend"' in t for t in self.top) else [[]], set()
        ends = {r: {e for rr, e in self.links if rr == r} for r in rels}
        for g in order:
            g = g if isinstance(g, (tuple, list)) else (g,)
            step = []
            for k in g:
                if k in rels and not ends[k] <= shown | set(g): pending.append(k); continue
                step.append(f"n:{k}"); shown.add(k)
            if step: out.append(step)
            for r in list(pending):
                if ends[r] <= shown: out.append([f"n:{r}"]); shown.add(r); pending.remove(r)
        out[0] = out[0] + (out.pop(1) if len(out) > 1 and out[0] == ["legend"] else [])
        out += [[f"n:{r}"] for r in pending]
        return out + [[f"note:{i}"] for i in range(self.nnotes)]

    def save(self, path, order=None, canon=None):
        body = "\n".join(self.lines + self.top)
        open(path, "w", encoding="utf-8").write(
            f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {self.w} {self.h}" width="{self.w}" height="{self.h}">\n'
            f'<rect width="100%" height="100%" fill="#ffffff"/>\n{body}\n</svg>\n')
        _sidecars(path, self.units(order), canon or "erd-conceptual")


def _plan(order, keys, rels, key, nnotes):
    """Boxes in `order` (tuples drawn together), each relation with the step that shows its second end, notes last."""
    listed = {k for g in order for k in (g if isinstance(g, (tuple, list)) else (g,))}
    order = list(order) + [k for k in keys if k not in listed]
    shown, done, out = set(), set(), []
    for g in order:
        g = g if isinstance(g, (tuple, list)) else (g,)
        shown |= set(g); step = [key(k) for k in g]
        for rk, a, b in rels:
            if rk not in done and a in shown and b in shown: done.add(rk); step.append(rk)
        out.append(step)
    return out + [[f"note:{i}"] for i in range(nnotes)]


def _sidecars(path, units, canon):
    """<name>.steps.json (reveal plan) and <name>.meta.json (which canonical picture this is; check_layout.py counts full redraws)."""
    import json
    p = pathlib.Path(path)
    p.with_suffix(".steps.json").write_text(json.dumps(units), encoding="utf-8")
    p.with_suffix(".meta.json").write_text(json.dumps({"canon": canon, "full": True}), encoding="utf-8")
