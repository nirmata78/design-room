#!/usr/bin/env python3
"""Native C4 drawer (2026-11-28): the Structurizr workspace is the model, this module draws it.

Why: Structurizr's browser export lays boxes out with dagre and styles them with JointJS. At 1080p that gave cramped boxes, text
spilling out of shapes, crossing routes and holes in derived views. The diagrams that read best in this repository were drawn on
a grid (the SD-09 set), and the reference look is c4model.com: white boxes with a coloured outline, a [Type: technology] line,
a person drawn as a head and a body, cylinders for stores, the component icon, dashed labelled arrows. This module keeps
Structurizr DSL as the single source (elements, technologies, descriptions, tags, the include set of every view; validated and
exported to JSON by the Structurizr CLI) and draws every view itself:

  layout     views.json "grid": ["cli . adv", ". ac .", ...] — rows of DSL identifiers (last segment), "." for an empty cell.
             Without a grid, a layered layout is computed from the relationships (rank = longest path, order = barycentre).
  canvas     the slot the view is shown in, in frame px (stage 1800 × 860, full 1704 × 780 …): 1 svg px = 1 px on a 1080p frame,
             so the legibility gate is exact and every derived view of one source has the same viewBox (nothing moves).
  shapes     c4model.com, Google palette (DESIGN-TOKENS.md): person = head + body; software system and container = rounded box;
             tag Database = cylinder, Queue = box with a log icon, Bucket = bucket, Folder = folder, Browser = browser window,
             App = box with a ">_" icon; component = box with the component icon. Blue outline for what is in scope, grey for
             what is external. Red, green and yellow appear only as overlays (BREAKS, FIX, NEW / ALTERNATE).
  edges      straight when nothing is in the way, else an orthogonal route through the gaps between rows and columns; dashed
             grey with a filled arrowhead; the description on a white plate, the technology beneath it in [brackets].
  overlays   hide · new · breaks · fix · focus · alternate · badges · keep (+ crop) · flow — the views.json vocabulary of
             svg_normalizer.Overlay, unchanged.

Output per view: <key>.svg, <key>.steps.json (reveal plan: e:<alias>, l:<a>-<b>, p:<kind>:<alias>, f:<n>), <key>.meta.json (ViewMeta).
"""
from __future__ import annotations

import html
import json
import math
import pathlib
import re
from dataclasses import dataclass, field
from typing import Any

from svg_normalizer import SLOTS, Overlay, ViewMeta

FONT = "Inter, Roboto, sans-serif"

# ── palette (DESIGN-TOKENS.md) ────────────────────────────────────────────────────────────────────────────────────────
#            stroke     fill       title      type line  description
INTERNAL = ("#1A73E8", "#FFFFFF", "#174EA6", "#1967D2", "#3C4043")
PERSON = ("#174EA6", "#E8F0FE", "#174EA6", "#1967D2", "#3C4043")
EXTERNAL = ("#80868B", "#F1F3F4", "#3C4043", "#5F6368", "#3C4043")
EDGE, EDGE_TEXT, EDGE_TECH = "#5F6368", "#3C4043", "#5F6368"
BOUNDARY = ("#1A73E8", "#F8FAFF", "#174EA6", "#1967D2")
STATUS = {  # kind -> (stroke, fill, pill fill, pill text, label, dashed)
    "breaks": ("#EA4335", "#FCE8E6", "#C5221F", "#FFFFFF", "BREAKS", False),
    "fix": ("#34A853", "#E6F4EA", "#188038", "#FFFFFF", "FIX", False),
    "focus": ("#1A73E8", "#E8F0FE", "#1967D2", "#FFFFFF", "IN FOCUS", False),
    "new": ("#F9AB00", "#FEF7E0", "#F9AB00", "#202124", "NEW", False),
    "alternate": ("#F9AB00", "#FEF7E0", "#F9AB00", "#202124", "ALTERNATE", True),
}
FLOW = "#1A73E8"

# ── type scale (svg px = frame px) ────────────────────────────────────────────────────────────────────────────────────
TITLE, TYPE, DESC, LABEL, TECH, PILL, BLABEL = 25.0, 18.0, 19.0, 18.0, 18.0, 18.0, 22.0
MARGIN = 22.0


# ── text measurement (Inter, approximate advance widths in em) ────────────────────────────────────────────────────────
_NARROW, _SEMI, _WIDE = set("il.,:;'|!·()[]"), set("fjtrI1 -/"), set("mwMW@%")


def text_w(s: str, size: float, bold: bool = False) -> float:
    w = 0.0
    for ch in s:
        if ch in _NARROW:
            w += 0.27
        elif ch in _SEMI:
            w += 0.36
        elif ch in _WIDE:
            w += 0.84
        elif ch.isupper():
            w += 0.66
        elif ch.isdigit():
            w += 0.58
        else:
            w += 0.54
    return w * size * (1.07 if bold else 1.0)


def wrap(text: str, width: float, size: float, bold: bool = False) -> list[str]:
    lines, cur = [], ""
    for word in str(text).split():
        cand = f"{cur} {word}".strip()
        if cur and text_w(cand, size, bold) > width:
            lines.append(cur)
            cur = word
        else:
            cur = cand
    if cur:
        lines.append(cur)
    return lines


def esc(s: Any) -> str:
    return html.escape(str(s), quote=True)


# ── model ─────────────────────────────────────────────────────────────────────────────────────────────────────────────
@dataclass
class El:
    id: str
    alias: str
    name: str
    kind: str                      # person · system · container · component
    desc: str = ""
    tech: str = ""
    tags: set[str] = field(default_factory=set)
    parent: str = ""               # alias of the enclosing system / container

    @property
    def external(self) -> bool:
        return "External" in self.tags

    @property
    def shape(self) -> str:
        if self.kind == "person":
            return "person"
        for t in ("Database", "Queue", "Bucket", "Folder", "Browser", "App"):
            if t in self.tags:
                return t.lower()
        return "component" if self.kind == "component" else "box"

    def type_line(self) -> str:
        label = {"person": "Person", "system": "Software System", "container": "Container", "component": "Component"}[self.kind]
        if self.kind == "system" and self.external:
            label = "External System"
        return f"[{label}: {self.tech}]" if self.tech else f"[{label}]"


@dataclass
class Rel:
    id: str
    src: str
    dst: str
    desc: str = ""
    tech: str = ""
    tags: set[str] = field(default_factory=set)

    @property
    def key(self) -> str:
        return f"l:{self.src}-{self.dst}"


@dataclass
class View:
    key: str
    kind: str                      # context · container · component
    scope: str                     # alias of the system / container in scope
    elements: list[str]
    rels: list[str]
    rank_dir: str = "lr"


class Model:
    def __init__(self, ws: dict):
        self.els: dict[str, El] = {}
        self.by_id: dict[str, str] = {}
        self.rels: dict[str, Rel] = {}
        raw_rels: list[dict] = []

        def alias_of(e: dict) -> str:
            ident = (e.get("properties") or {}).get("structurizr.dsl.identifier") or e["name"]
            return re.sub(r"\W+", "_", ident.split(".")[-1])

        def add(e: dict, kind: str, parent: str = "") -> str:
            a = alias_of(e)
            self.els[a] = El(e["id"], a, e["name"], kind, e.get("description", ""), e.get("technology", ""),
                             set((e.get("tags") or "").split(",")), parent)
            self.by_id[e["id"]] = a
            raw_rels.extend(e.get("relationships") or [])
            return a

        m = ws["model"]
        for p in m.get("people", []):
            add(p, "person")
        for s in m.get("softwareSystems", []):
            sa = add(s, "system")
            for c in s.get("containers", []):
                ca = add(c, "container", sa)
                for k in c.get("components", []):
                    add(k, "component", ca)
        for r in raw_rels:
            if r["sourceId"] in self.by_id and r["destinationId"] in self.by_id:
                self.rels[r["id"]] = Rel(r["id"], self.by_id[r["sourceId"]], self.by_id[r["destinationId"]],
                                         r.get("description", ""), r.get("technology", ""), set((r.get("tags") or "").split(",")))
        self.views: dict[str, View] = {}
        vs = ws.get("views", {})
        for group, kind, scope_key in (("systemContextViews", "context", "softwareSystemId"),
                                       ("containerViews", "container", "softwareSystemId"),
                                       ("componentViews", "component", "containerId")):
            for v in vs.get(group, []):
                al = v.get("automaticLayout") or {}
                self.views[v["key"]] = View(
                    v["key"], kind, self.by_id.get(v.get(scope_key, ""), ""),
                    [self.by_id[e["id"]] for e in v.get("elements", []) if e["id"] in self.by_id],
                    [r["id"] for r in v.get("relationships", []) if r["id"] in self.rels],
                    "tb" if al.get("rankDirection") == "TopBottom" else "lr")

    def internal(self, view: View, alias: str) -> bool:
        """Drawn inside the view's boundary: the containers of the system in scope, or the components of the container in scope."""
        return view.kind != "context" and self.els[alias].parent == view.scope


# ── layout ────────────────────────────────────────────────────────────────────────────────────────────────────────────
def parse_grid(rows: list[str]) -> dict[str, tuple[int, int]]:
    cells: dict[str, tuple[int, int]] = {}
    for r, line in enumerate(rows):
        for c, tok in enumerate(line.split()):
            if tok not in (".", "-", "_"):
                cells[tok] = (r, c)
    return cells


def auto_grid(model: Model, view: View) -> dict[str, tuple[int, int]]:
    """Layered fallback: rank = longest path along the relationships, order within a rank by barycentre of predecessors."""
    els = view.elements
    succ = {a: [] for a in els}
    for rid in view.rels:
        r = model.rels[rid]
        if r.src in succ and r.dst in succ and r.src != r.dst:
            succ[r.src].append(r.dst)
    rank = {a: 0 for a in els}
    for _ in range(len(els)):
        changed = False
        for a in els:
            for b in succ[a]:
                if rank[b] < rank[a] + 1 and rank[a] + 1 < len(els):
                    rank[b] = rank[a] + 1
                    changed = True
        if not changed:
            break
    layers: dict[int, list[str]] = {}
    for a in els:
        layers.setdefault(rank[a], []).append(a)
    pos: dict[str, float] = {}
    out: dict[str, tuple[int, int]] = {}
    for r in sorted(layers):
        layer = layers[r]
        if r:
            preds = {a: [pos[p] for p in els if a in succ[p] and p in pos] for a in layer}
            layer.sort(key=lambda a: sum(preds[a]) / len(preds[a]) if preds[a] else 1e9)
        for i, a in enumerate(layer):
            pos[a] = i
            out[a] = (i, r) if view.rank_dir == "lr" else (r, i)
    return out


@dataclass
class Box:
    x: float
    y: float
    w: float
    h: float

    @property
    def cx(self) -> float:
        return self.x + self.w / 2

    @property
    def cy(self) -> float:
        return self.y + self.h / 2

    def grow(self, d: float) -> "Box":
        return Box(self.x - d, self.y - d, self.w + 2 * d, self.h + 2 * d)

    def hits_seg(self, a: tuple[float, float], b: tuple[float, float]) -> bool:
        """Liang–Barsky: does segment a-b pass through this box?"""
        x0, y0 = a
        dx, dy = b[0] - a[0], b[1] - a[1]
        t0, t1 = 0.0, 1.0
        for p, q in ((-dx, x0 - self.x), (dx, self.x + self.w - x0), (-dy, y0 - self.y), (dy, self.y + self.h - y0)):
            if p == 0:
                if q < 0:
                    return False
            else:
                t = q / p
                if p < 0:
                    t0 = max(t0, t)
                else:
                    t1 = min(t1, t)
                if t0 > t1:
                    return False
        return True

    def overlap(self, o: "Box") -> float:
        w = min(self.x + self.w, o.x + o.w) - max(self.x, o.x)
        h = min(self.y + self.h, o.y + o.h) - max(self.y, o.y)
        return w * h if w > 0 and h > 0 else 0.0


def clip_to_box(box: Box, inside: tuple[float, float], outside: tuple[float, float], pad: float = 2.0) -> tuple[float, float]:
    """The point where the ray inside → outside leaves the box (plus pad)."""
    dx, dy = outside[0] - inside[0], outside[1] - inside[1]
    ts = []
    if dx:
        ts += [((box.x - pad) - inside[0]) / dx, ((box.x + box.w + pad) - inside[0]) / dx]
    if dy:
        ts += [((box.y - pad) - inside[1]) / dy, ((box.y + box.h + pad) - inside[1]) / dy]
    t = min((t for t in ts if t > 0), default=1.0)
    return inside[0] + dx * t, inside[1] + dy * t


def seg_cross(a, b, c, d) -> bool:
    def ccw(p, q, r):
        return (r[1] - p[1]) * (q[0] - p[0]) - (q[1] - p[1]) * (r[0] - p[0])
    d1, d2, d3, d4 = ccw(c, d, a), ccw(c, d, b), ccw(a, b, c), ccw(a, b, d)
    return (d1 * d2 < 0) and (d3 * d4 < 0)


def path_len(pts) -> float:
    return sum(math.dist(p, q) for p, q in zip(pts, pts[1:]))


def point_at(pts, frac: float) -> tuple[float, float, int]:
    total, goal, run = path_len(pts) or 1.0, 0.0, 0.0
    goal = total * frac
    for i, (p, q) in enumerate(zip(pts, pts[1:])):
        d = math.dist(p, q)
        if run + d >= goal and d > 0:
            t = (goal - run) / d
            return p[0] + (q[0] - p[0]) * t, p[1] + (q[1] - p[1]) * t, i
        run += d
    return pts[-1][0], pts[-1][1], len(pts) - 2


@dataclass
class Layout:
    W: float
    H: float
    boxes: dict[str, Box]
    rows: int
    cols: int
    gx: list[float]                # x of the middle of every vertical channel (between columns, and the outer margins)
    gy: list[float]                # y of the middle of every horizontal channel


def _label_need(r: Rel, horizontal: bool) -> float:
    """Space a label needs across the gap it sits in: width for a horizontal edge, height for a vertical one."""
    if not r.desc and not r.tech:
        return 0.0
    tech = text_w(f"[{r.tech}]", TECH) if r.tech else 0.0
    if horizontal:
        words = r.desc.split()
        longest = max([text_w(w, LABEL) for w in words] + [tech])
        half = text_w(r.desc, LABEL) / 2 + 8
        return min(190.0, max(longest, half if len(words) > 1 else longest)) + 30
    lines = len(wrap(r.desc, 230, LABEL)) if r.desc else 0
    return lines * LABEL * 1.22 + (TECH * 1.25 if r.tech else 0) + 24


def make_layout(model: Model, view: View, cells: dict[str, tuple[int, int]], W: float, H: float,
                box_w: float | None = None, box_h: float | None = None) -> Layout:
    """Columns and rows sized from their content: each gap is as wide as the labels that cross it (and the boundary that runs
    through it) need; boxes shrink to fit the canvas; the whole drawing is centred on it."""
    rows = 1 + max(r for r, _ in cells.values())
    cols = 1 + max(c for _, c in cells.values())
    inner = [rc for a, rc in cells.items() if view.kind != "context" and model.internal(view, a)]
    r0, r1 = (min(r for r, _ in inner), max(r for r, _ in inner)) if inner else (-9, -9)
    c0, c1 = (min(c for _, c in inner), max(c for _, c in inner)) if inner else (-9, -9)
    hgap = [64.0] * (cols + 1)                               # hgap[i]: left of column i (hgap[cols]: right margin)
    vgap = [46.0] * (rows + 1)
    hgap[0] = hgap[cols] = 20.0
    vgap[0], vgap[rows] = 30.0, 20.0
    for rid in view.rels:
        r = model.rels[rid]
        if r.src not in cells or r.dst not in cells:
            continue
        (ra, ca), (rb, cb) = cells[r.src], cells[r.dst]
        if ra == rb and abs(ca - cb) == 1:
            i = max(ca, cb)
            hgap[i] = max(hgap[i], _label_need(r, True))
        elif ca == cb and abs(ra - rb) == 1:
            j = max(ra, rb)
            vgap[j] = max(vgap[j], _label_need(r, False))
    if inner:                                                # the boundary runs through these gaps: room for its line and label
        hgap[c0] += 34
        hgap[c1 + 1] += 34
        vgap[r0] += 30
        vgap[r1 + 1] += 54
    person_rows = {r for a, (r, _) in cells.items() if model.els[a].shape == "person"}
    bw = box_w or 300.0
    bh = box_h or 160.0

    def total_w(bw_):
        return cols * bw_ + sum(hgap)

    def total_h(bh_):
        return rows * bh_ + sum(vgap) + 30 * len(person_rows)
    if total_w(bw) > W - 2 * MARGIN:
        bw = max(200.0, (W - 2 * MARGIN - sum(hgap)) / cols)
    if total_h(bh) > H - 2 * MARGIN:
        bh = max(118.0, (H - 2 * MARGIN - sum(vgap) - 30 * len(person_rows)) / rows)
    # whatever is left over is shared out evenly between the inner gaps, then the drawing is centred
    spare_w = W - 2 * MARGIN - total_w(bw)
    spare_h = H - 2 * MARGIN - total_h(bh)
    if spare_w > 0 and cols > 1:
        add = min(spare_w / (cols + 1), 140.0)
        hgap = [g + add for g in hgap]
    if spare_h > 0 and rows > 1:
        add = min(spare_h / (rows + 1), 90.0)
        vgap = [g + add for g in vgap]
    ox = (W - total_w(bw)) / 2
    oy = (H - total_h(bh)) / 2
    xs, x = [], ox
    gx = []
    for i in range(cols):
        gx.append(x + hgap[i] / 2)
        x += hgap[i]
        xs.append(x)
        x += bw
    gx.append(x + hgap[cols] / 2)
    ys, y = [], oy
    gy = []
    for j in range(rows):
        gy.append(y + vgap[j] / 2)
        y += vgap[j] + (30 if j in person_rows else 0)
        ys.append(y)
        y += bh
    gy.append(y + vgap[rows] / 2)
    boxes = {}
    for a, (r, c) in cells.items():
        extra = 30 if model.els[a].shape == "person" else 0
        boxes[a] = Box(xs[c], ys[r] - extra, bw, bh + extra)
    return Layout(W, H, boxes, rows, cols, gx, gy)


# ── routing ───────────────────────────────────────────────────────────────────────────────────────────────────────────
def route(lay: Layout, a: str, b: str, placed: list[list[tuple[float, float]]], avoid: dict[str, Box]) -> list[tuple[float, float]]:
    A, B = lay.boxes[a], lay.boxes[b]
    others = [bx.grow(12) for k, bx in avoid.items() if k not in (a, b)]

    def clean(pts) -> bool:
        return not any(o.hits_seg(p, q) for o in others for p, q in zip(pts, pts[1:]))

    def crossings(pts) -> int:
        return sum(seg_cross(p, q, r, s) for other in placed for p, q in zip(pts, pts[1:]) for r, s in zip(other, other[1:]))

    cands: list[list[tuple[float, float]]] = []
    ca, cb = (A.cx, A.cy), (B.cx, B.cy)
    if abs(A.cy - B.cy) < 1:                                   # same row: horizontal
        y = A.cy
        cands.append([(A.x + A.w if B.cx > A.cx else A.x, y), (B.x if B.cx > A.cx else B.x + B.w, y)])
    elif abs(A.cx - B.cx) < 1:                                 # same column: vertical
        x = A.cx
        cands.append([(x, A.y + A.h if B.cy > A.cy else A.y), (x, B.y if B.cy > A.cy else B.y + B.h)])
    else:
        cands.append([clip_to_box(A, ca, cb), clip_to_box(B, cb, ca)])
    # orthogonal alternatives through the channels between rows and columns
    gy, gx = lay.gy, lay.gx
    sx, sy = (1 if B.cx > A.cx else -1), (1 if B.cy > A.cy else -1)
    # L: leave A horizontally, enter B vertically (and the mirror)
    cands.append([(A.cx + sx * A.w / 2, A.cy), (B.cx, A.cy), (B.cx, B.cy - sy * B.h / 2)])
    cands.append([(A.cx, A.cy + sy * A.h / 2), (A.cx, B.cy), (B.cx - sx * B.w / 2, B.cy)])
    # Z through a horizontal channel (between rows), and through a vertical channel (between columns)
    for y in sorted(gy, key=lambda y: abs(y - (A.cy + B.cy) / 2)):
        ya = A.cy + (A.h / 2 if y > A.cy else -A.h / 2)
        yb = B.cy + (B.h / 2 if y > B.cy else -B.h / 2)
        cands.append([(A.cx, ya), (A.cx, y), (B.cx, y), (B.cx, yb)])
    for x in sorted(gx, key=lambda x: abs(x - (A.cx + B.cx) / 2)):
        xa = A.cx + (A.w / 2 if x > A.cx else -A.w / 2)
        xb = B.cx + (B.w / 2 if x > B.cx else -B.w / 2)
        cands.append([(xa, A.cy), (x, A.cy), (x, B.cy), (xb, B.cy)])

    def score(pts):
        return (0 if clean(pts) else 1, crossings(pts), len(pts), path_len(pts))
    best = min(cands, key=score)
    return [(round(x, 1), round(y, 1)) for x, y in best]


def spread_ports(paths: dict[str, list[tuple[float, float]]], rels: list[Rel], boxes: dict[str, Box]) -> None:
    """Edges that leave or enter the same side of a box at the same point are spread along that side."""
    ends: dict[tuple[float, float], list[tuple[str, int]]] = {}
    for r in rels:
        pts = paths.get(r.key)
        if pts:
            ends.setdefault((round(pts[0][0]), round(pts[0][1])), []).append((r.key, 0))
            ends.setdefault((round(pts[-1][0]), round(pts[-1][1])), []).append((r.key, -1))
    for (x, y), users in ends.items():
        if len(users) < 2:
            continue
        n = len(users)
        for i, (k, idx) in enumerate(sorted(users)):
            off = (i - (n - 1) / 2) * 26
            pts = paths[k]
            j = 1 if idx == 0 else -2
            horizontal_first = abs(pts[idx][1] - pts[j][1]) < 1      # first segment horizontal → shift vertically
            if horizontal_first:
                pts[idx] = (pts[idx][0], pts[idx][1] + off)
                if len(pts) > 2:
                    pts[j] = (pts[j][0], pts[j][1] + off)
                else:
                    pts[j] = (pts[j][0], pts[j][1] + off) if abs(pts[j][1] - y) < 1 else pts[j]
            else:
                pts[idx] = (pts[idx][0] + off, pts[idx][1])
                if len(pts) > 2:
                    pts[j] = (pts[j][0] + off, pts[j][1])


# ── drawing ───────────────────────────────────────────────────────────────────────────────────────────────────────────
def _txt(x, y, s, size, fill, weight=400, anchor="middle", italic=False, cls="") -> str:
    st = ' font-style="italic"' if italic else ""
    c = f' class="{cls}"' if cls else ""
    return (f'<text{c} x="{x:.1f}" y="{y:.1f}" font-family="{FONT}" font-size="{size:g}" font-weight="{weight}" '
            f'fill="{fill}" text-anchor="{anchor}"{st}>{esc(s)}</text>')


def shape_svg(e: El, b: Box, stroke: str, fill: str, sw: float, dash: str) -> tuple[str, Box]:
    """The outline of one element; returns (svg, text area)."""
    d = f' stroke-dasharray="{dash}"' if dash else ""
    s = f'fill="{fill}" stroke="{stroke}" stroke-width="{sw:g}"{d}'
    x, y, w, h = b.x, b.y, b.w, b.h
    sh = e.shape
    if sh == "person":
        r = 30.0
        top = y + r * 1.55
        body = (f'<rect x="{x:.1f}" y="{top:.1f}" width="{w:.1f}" height="{y + h - top:.1f}" rx="{min(46, (y + h - top) * 0.3):.1f}" {s}/>'
                f'<circle cx="{x + w / 2:.1f}" cy="{y + r:.1f}" r="{r:.1f}" {s}/>')
        return body, Box(x + 14, top + r * 0.5, w - 28, y + h - top - r * 0.5 - 10)
    if sh == "database":
        ry = min(16.0, h * 0.09)
        p = (f'<path d="M{x:.1f},{y + ry:.1f} L{x:.1f},{y + h - ry:.1f} A{w / 2:.1f},{ry:.1f} 0 0 0 {x + w:.1f},{y + h - ry:.1f} '
             f'L{x + w:.1f},{y + ry:.1f} A{w / 2:.1f},{ry:.1f} 0 0 0 {x:.1f},{y + ry:.1f} Z" {s}/>'
             f'<ellipse cx="{x + w / 2:.1f}" cy="{y + ry:.1f}" rx="{w / 2:.1f}" ry="{ry:.1f}" {s}/>')
        return p, Box(x + 14, y + 2 * ry + 4, w - 28, h - 3 * ry - 8)
    if sh == "bucket":
        ry, inset = min(16.0, h * 0.09), w * 0.09
        p = (f'<path d="M{x:.1f},{y + ry:.1f} L{x + inset:.1f},{y + h - ry:.1f} A{w / 2 - inset:.1f},{ry:.1f} 0 0 0 {x + w - inset:.1f},{y + h - ry:.1f} '
             f'L{x + w:.1f},{y + ry:.1f}" {s}/>'
             f'<ellipse cx="{x + w / 2:.1f}" cy="{y + ry:.1f}" rx="{w / 2:.1f}" ry="{ry:.1f}" {s}/>')
        return p, Box(x + inset + 8, y + 2 * ry + 4, w - 2 * inset - 16, h - 3 * ry - 8)
    if sh == "folder":
        tab = 22.0
        p = (f'<path d="M{x:.1f},{y + tab:.1f} L{x:.1f},{y + 8:.1f} Q{x:.1f},{y:.1f} {x + 8:.1f},{y:.1f} L{x + w * 0.32:.1f},{y:.1f} '
             f'Q{x + w * 0.34:.1f},{y:.1f} {x + w * 0.34:.1f},{y + 8:.1f} L{x + w * 0.34:.1f},{y + tab:.1f}" {s}/>'
             f'<rect x="{x:.1f}" y="{y + tab:.1f}" width="{w:.1f}" height="{h - tab:.1f}" rx="6" {s}/>')
        return p, Box(x + 14, y + tab + 6, w - 28, h - tab - 12)
    p = f'<rect x="{x:.1f}" y="{y:.1f}" width="{w:.1f}" height="{h:.1f}" rx="14" {s}/>'
    area = Box(x + 16, y + 10, w - 32, h - 20)
    if sh == "browser":
        p += (f'<path d="M{x:.1f},{y + 26:.1f} L{x + w:.1f},{y + 26:.1f}" stroke="{stroke}" stroke-width="{sw:g}"/>' +
              "".join(f'<circle cx="{x + 18 + i * 16:.1f}" cy="{y + 13:.1f}" r="4.5" fill="{stroke}"/>' for i in range(3)))
        area = Box(x + 16, y + 32, w - 32, h - 40)
    elif sh == "app":
        p += (f'<path d="M{x + 16:.1f},{y + 14:.1f} l10,7 l-10,7 M{x + 31:.1f},{y + 30:.1f} l13,0" fill="none" stroke="{stroke}" '
              f'stroke-width="3" stroke-linecap="round" stroke-linejoin="round"/>')
        area = Box(x + 16, y + 30, w - 32, h - 38)
    elif sh == "queue":
        p += "".join(f'<rect x="{x + 14 + i * 11:.1f}" y="{y + 14:.1f}" width="9" height="16" rx="1.5" fill="{stroke}" '
                     f'opacity="{0.35 + i * 0.2:.2f}"/>' for i in range(4))
        area = Box(x + 16, y + 30, w - 32, h - 38)
    elif sh == "component":
        p += "".join(f'<rect x="{x - 11:.1f}" y="{y + yy:.1f}" width="26" height="13" rx="2" {s}/>' for yy in (16, 36))
        area = Box(x + 22, y + 10, w - 44, h - 20)
    return p, area


def text_block(e: El, area: Box, ink: tuple[str, str, str]) -> tuple[str, bool, float]:
    """Title, [Type: technology], description, centred in the area. Returns (svg, fits, smallest size used)."""
    title_c, type_c, desc_c = ink
    for t, d in ((TITLE, DESC), (TITLE - 1, DESC - 1), (TITLE - 2, DESC - 1)):
        tl = wrap(e.name, area.w, t, bold=True)
        ty = wrap(e.type_line(), area.w, TYPE)
        dl = wrap(e.desc, area.w, d) if e.desc else []
        lh_t, lh_ty, lh_d = t * 1.18, TYPE * 1.3, d * 1.3
        total = len(tl) * lh_t + 4 + len(ty) * lh_ty + (8 + len(dl) * lh_d if dl else 0)
        if total <= area.h:
            break
    y = area.y + (area.h - total) / 2
    out = []
    for ln in tl:
        y += lh_t
        out.append(_txt(area.cx, y - t * 0.24, ln, t, title_c, 700))
    y += 4
    for ln in ty:
        y += lh_ty
        out.append(_txt(area.cx, y - TYPE * 0.3, ln, TYPE, type_c, 500))
    if dl:
        y += 8
        for ln in dl:
            y += lh_d
            out.append(_txt(area.cx, y - d * 0.3, ln, d, desc_c))
    return "".join(out), total <= area.h + 1, min(t, d)


def pill(x: float, y: float, text: str, fill: str, fg: str, anchor: str = "end", stroke: str = "#FFFFFF") -> tuple[str, Box]:
    w = text_w(text, PILL, bold=True) * 1.08 + 22
    h = PILL * 1.75
    left = x - w if anchor == "end" else (x if anchor == "start" else x - w / 2)
    svg = (f'<rect x="{left:.1f}" y="{y - h / 2:.1f}" width="{w:.1f}" height="{h:.1f}" rx="{h / 2:.1f}" fill="{fill}" stroke="{stroke}" '
           f'stroke-width="2.5"/>' + _txt(left + w / 2, y + PILL * 0.36, text, PILL, fg, 800) .replace("<text ", '<text letter-spacing="0.6" ', 1))
    return svg, Box(left, y - h / 2, w, h)


@dataclass
class Label:
    lines: list[str]
    tech: str
    box: Box

    def svg(self) -> str:
        b = self.box
        out = [f'<rect x="{b.x:.1f}" y="{b.y:.1f}" width="{b.w:.1f}" height="{b.h:.1f}" rx="6" fill="#FFFFFF" fill-opacity="0.94"/>']
        y = b.y + 4
        for ln in self.lines:
            y += LABEL * 1.22
            out.append(_txt(b.cx, y - LABEL * 0.26, ln, LABEL, EDGE_TEXT, 500))
        if self.tech:
            y += TECH * 1.25
            out.append(_txt(b.cx, y - TECH * 0.28, f"[{self.tech}]", TECH, EDGE_TECH, 400, italic=True))
        return "".join(out)


def place_label(r: Rel, pts, boxes: list[Box], labels: list[Box]) -> Label | None:
    if not r.desc and not r.tech:
        return None
    segs = list(zip(pts, pts[1:]))
    longest = max(segs, key=lambda s: math.dist(*s))
    horizontal = abs(longest[0][1] - longest[1][1]) < 1
    maxw = max(70.0, min(260.0, math.dist(*longest) - 26)) if horizontal else 230.0
    lines = wrap(r.desc, maxw, LABEL, bold=False) if r.desc else []
    w = max([text_w(ln, LABEL) for ln in lines] + [text_w(f"[{r.tech}]", TECH) if r.tech else 0]) + 16
    h = len(lines) * LABEL * 1.22 + (TECH * 1.25 if r.tech else 0) + 10
    best, best_cost = None, 1e18
    li = segs.index(longest)
    total = path_len(pts)
    # the middle of the longest segment first, then fractions along the whole path, then beside a vertical segment
    run = sum(math.dist(*s) for s in segs[:li])
    mid = (run + math.dist(*longest) / 2) / (total or 1)
    for frac in (mid, 0.5, 0.4, 0.6, 0.3, 0.7, 0.25, 0.75):
        x, y, _ = point_at(pts, frac)
        for dx in (0.0, w / 2 + 10, -(w / 2 + 10)):
            cand = Box(x + dx - w / 2, y - h / 2, w, h)
            cost = sum(cand.overlap(b.grow(6)) for b in boxes) * 10 + sum(cand.overlap(l.grow(4)) for l in labels) * 10 + abs(dx) * 2 + abs(frac - mid) * 200
            if cost < best_cost:
                best, best_cost = cand, cost
        if best_cost < 1:
            break
    return Label(lines, r.tech, best)


# ── one view ──────────────────────────────────────────────────────────────────────────────────────────────────────────
@dataclass
class Spec:
    """What render_c4.py hands over for one output SVG."""
    key: str
    source: str
    slot: str = "full"
    grid: list[str] = field(default_factory=list)
    box: tuple[float, float] | None = None
    overlay: Overlay = field(default_factory=Overlay)
    steps: list[Any] = field(default_factory=list)
    min_px: float = 18.0
    canon: str = ""
    full: bool = True
    legend: bool = False
    canvas: str = ""               # slot of the source view: the layout canvas (a derived view keeps its source's pixels)


def _resolve(model: Model, raw: str) -> str | None:
    raw = raw.strip()
    if raw in model.els:
        return raw
    seg = raw.split(".")[-1]
    if seg in model.els:
        return seg
    for a, e in model.els.items():
        if e.name.lower() == raw.lower():
            return a
    return None


def render_view(model: Model, spec: Spec, out_dir: pathlib.Path) -> tuple[ViewMeta, list[str]]:
    view = model.views[spec.source]
    ov = spec.overlay
    W, H = SLOTS.get(spec.canvas or spec.slot, SLOTS["full"])
    cells = parse_grid(spec.grid) if spec.grid else auto_grid(model, view)
    unknown = [a for a in cells if a not in model.els or a not in view.elements]
    cells = {a: rc for a, rc in cells.items() if a in view.elements}
    for a in view.elements:                                  # an element of the view the grid forgot: next free cell, last row
        if a not in cells:
            unknown.append(f"{a} (not in grid)")
            r = 1 + max((r for r, _ in cells.values()), default=-1)
            cells[a] = (r, 0)
    lay = make_layout(model, view, cells, W, H, *(spec.box or (None, None)))

    def res_list(xs):
        out = []
        for x in xs:
            a = _resolve(model, x)
            if a is None or a not in lay.boxes:
                unknown.append(x)
            else:
                out.append(a)
        return out

    def res_edge(spec_s: str) -> str | None:
        a, _, b = spec_s.partition("->")
        a, b = _resolve(model, a), _resolve(model, b)
        for rid in view.rels:
            r = model.rels[rid]
            if (r.src, r.dst) in ((a, b), (b, a)):
                return r.key
        unknown.append(spec_s)
        return None

    hidden_els = set(res_list([h for h in ov.hide if "->" not in h]))
    hidden_rels = {k for h in ov.hide if "->" in h and (k := res_edge(h))}
    rels = [model.rels[rid] for rid in view.rels]
    rels_all = rels                                          # routes come from the full view: identical in every derived view
    paths: dict[str, list[tuple[float, float]]] = {}
    placed: list[list[tuple[float, float]]] = []
    order = sorted(rels_all, key=lambda r: math.dist((lay.boxes[r.src].cx, lay.boxes[r.src].cy), (lay.boxes[r.dst].cx, lay.boxes[r.dst].cy)))
    for r in order:
        if r.src in lay.boxes and r.dst in lay.boxes:
            paths[r.key] = route(lay, r.src, r.dst, placed, lay.boxes)
            placed.append(paths[r.key])
    spread_ports(paths, rels_all, lay.boxes)

    vis_els = [a for a in view.elements if a in lay.boxes and a not in hidden_els]
    vis_rels = [r for r in rels if r.key in paths and r.key not in hidden_rels and r.src in vis_els and r.dst in vis_els]
    keep = set(res_list(ov.keep))
    dim = (lambda a: bool(keep) and a not in keep)
    marks: dict[str, str] = {}
    for kind in ("alternate", "new", "focus", "fix", "breaks"):
        for a in res_list(getattr(ov, kind)):
            marks[a] = kind
    flow_keys = [k for s in ov.flow if (k := res_edge(s))]

    # labels (placed against every visible box and every label placed before)
    all_boxes = [lay.boxes[a] for a in vis_els]
    labels: dict[str, Label] = {}
    for r in sorted(vis_rels, key=lambda r: -path_len(paths[r.key])):
        lb = place_label(r, paths[r.key], all_boxes, [l.box for l in labels.values()])
        if lb:
            labels[r.key] = lb

    # boundary around the visible internal elements
    inner = [a for a in vis_els if model.internal(view, a)]
    boundary = ""
    bbox_bound = None
    if inner:
        bx0 = min(lay.boxes[a].x for a in inner) - 26
        by0 = min(lay.boxes[a].y for a in inner) - 30
        bx1 = max(lay.boxes[a].x + lay.boxes[a].w for a in inner) + 26
        by1 = max(lay.boxes[a].y + lay.boxes[a].h for a in inner) + 64
        bbox_bound = Box(bx0, by0, bx1 - bx0, by1 - by0)
        sc = model.els[view.scope]
        kind = "Software System" if sc.kind == "system" else "Container"
        bdim = ' opacity="0.28"' if keep else ""
        boundary = (f'<g class="c4-boundary" data-k="b:{sc.alias}"{bdim}><rect x="{bx0:.1f}" y="{by0:.1f}" width="{bx1 - bx0:.1f}" '
                    f'height="{by1 - by0:.1f}" rx="18" fill="{BOUNDARY[1]}" stroke="{BOUNDARY[0]}" stroke-width="2" stroke-dasharray="10 6"/>'
                    + _txt(bx0 + 18, by1 - 33, sc.name, BLABEL, BOUNDARY[2], 700, "start")
                    + _txt(bx0 + 18, by1 - 11, f"[{kind}]", TECH, BOUNDARY[3], 500, "start") + "</g>")

    # elements
    node_svg, overflow, sizes = [], [], []
    pills: list[tuple[str, str]] = []
    for a in vis_els:
        e = model.els[a]
        b = lay.boxes[a]
        base = EXTERNAL if e.external else (PERSON if e.kind == "person" else INTERNAL)
        stroke, fill, sw, dash = base[0], base[1], 3.0, ""
        if a in marks:
            st = STATUS[marks[a]]
            stroke, fill, sw, dash = st[0], st[1], 5.0, ("14 8" if st[5] else "")
        shape, area = shape_svg(e, b, stroke, fill, sw, dash)
        texts, fits, smallest = text_block(e, area, base[2:])
        if not fits:
            overflow.append(a)
        if not dim(a):
            sizes.append(smallest)
        op = ' opacity="0.28"' if dim(a) else ""
        node_svg.append(f'<g class="c4-el" data-k="e:{a}"{op}>{shape}{texts}</g>')
        if a in marks:
            st = STATUS[marks[a]]
            ytop = b.y + (30.0 * 1.55 if e.shape == "person" else 0)
            ps, _ = pill(b.x + b.w - 14, ytop, st[4], st[2], st[3])
            pills.append((f"p:{marks[a]}:{a}", ps))
    for raw, text in ov.badges.items():
        a = _resolve(model, raw)
        if not a or a not in lay.boxes or a in hidden_els:
            unknown.append(raw)
            continue
        b = lay.boxes[a]
        ps, _ = pill(b.x + 14, b.y, text, "#FFFFFF", "#1967D2", anchor="start", stroke="#1A73E8")
        pills.append((f"p:badge:{a}", ps))

    # edges
    edge_svg = []
    for r in vis_rels:
        pts = paths[r.key]
        d = "M" + " L".join(f"{x:.1f},{y:.1f}" for x, y in pts)
        faded = dim(r.src) or dim(r.dst)
        op = ' opacity="0.28"' if faded else ""
        lb = labels[r.key].svg() if r.key in labels else ""
        if not faded and r.key in labels:
            sizes.append(LABEL)
        edge_svg.append(f'<g class="c4-rel" data-k="{r.key}"{op}><path d="{d}" fill="none" stroke="{EDGE}" stroke-width="2.6" '
                        f'stroke-dasharray="10 7" marker-end="url(#{spec.key}--arrow)"/>{lb}</g>')

    # flow: a blue highlight under each step's arrow and a numbered disc on it
    flow_svg, flow_under = [], []
    lab_boxes = [l.box for l in labels.values()]
    discs: list[tuple[float, float]] = []
    for n, k in enumerate(flow_keys, 1):
        if k not in paths or k not in {r.key for r in vis_rels}:
            continue
        pts = paths[k]
        d = "M" + " L".join(f"{x:.1f},{y:.1f}" for x, y in pts)
        flow_under.append(f'<path data-k="f:{n}" d="{d}" fill="none" stroke="{FLOW}" stroke-width="8" stroke-linecap="round" opacity="0.9"/>')
        rr = 19.0
        best, best_cost = None, 1e18
        for f in (0.2, 0.8, 0.35, 0.65, 0.12, 0.88, 0.5):
            x, y, i = point_at(pts, f)
            (ax, ay), (bx, by) = pts[i], pts[i + 1]
            ln = math.dist((ax, ay), (bx, by)) or 1.0
            px, py = -(by - ay) / ln, (bx - ax) / ln               # unit normal of the segment the point is on
            for off in (0.0, 27, -27, 46, -46, 70, -70, 95, -95, 120, -120):
                cx, cy = x + px * off, y + py * off
                disc = Box(cx - rr, cy - rr, 2 * rr, 2 * rr)
                cost = (sum(disc.overlap(lb.grow(4)) for lb in lab_boxes) * 1000 + sum(disc.overlap(b.grow(3)) for b in all_boxes) * 1000
                        + sum(disc.overlap(Box(fx - rr - 4, fy - rr - 4, 2 * rr + 8, 2 * rr + 8)) for fx, fy in discs) * 1000
                        + abs(off) * 0.6 + abs(f - 0.3) * 20)
                if cost < best_cost:
                    best, best_cost = (cx, cy), cost
        x, y = best
        discs.append((x, y))
        flow_svg.append(f'<g class="c4-flow" data-k="f:{n}"><circle cx="{x:.1f}" cy="{y:.1f}" r="{rr:g}" fill="#1967D2" stroke="#FFFFFF" '
                        f'stroke-width="3"/>' + _txt(x, y + 7.5, str(n), 21, "#FFFFFF", 800) + "</g>")

    # viewBox: the slot canvas; a crop shrinks it to the kept boxes (and scales them up on the frame)
    vx, vy, vw, vh = 0.0, 0.0, W, H
    if ov.crop and keep:
        ks = [lay.boxes[a] for a in keep if a in lay.boxes]
        x0, y0 = min(b.x for b in ks) - 40, min(b.y for b in ks) - 46
        x1, y1 = max(b.x + b.w for b in ks) + 40, max(b.y + b.h for b in ks) + 40
        for k in labels:
            r = next(r for r in vis_rels if r.key == k)
            if r.src in keep and r.dst in keep:
                lb = labels[k].box
                x0, y0, x1, y1 = min(x0, lb.x - 10), min(y0, lb.y - 10), max(x1, lb.x + lb.w + 10), max(y1, lb.y + lb.h + 10)
        sw_, sh_ = SLOTS.get(spec.slot, SLOTS["full"])
        bw, bh = x1 - x0, y1 - y0
        if bw / bh < sw_ / sh_:                                  # widen to the slot's aspect so it is centred, not stretched
            nw = bh * sw_ / sh_
            x0, bw = x0 - (nw - bw) / 2, nw
        else:
            nh = bw * sh_ / sw_
            y0, bh = y0 - (nh - bh) / 2, nh
        vx, vy, vw, vh = x0, y0, bw, bh
    scale = min(SLOTS.get(spec.slot, SLOTS["full"])[0] / vw, SLOTS.get(spec.slot, SLOTS["full"])[1] / vh)

    legend = legend_svg(model, view, vis_els, vx, vy + vh) if spec.legend else ""
    defs = (f'<defs><marker id="{spec.key}--arrow" viewBox="0 0 12 12" refX="11" refY="6" markerWidth="11" markerHeight="11" '
            f'markerUnits="userSpaceOnUse" orient="auto"><path d="M0,0.5 L12,6 L0,11.5 z" fill="{EDGE}"/></marker></defs>')
    svg = (f'<svg xmlns="http://www.w3.org/2000/svg" class="c4" data-view="{esc(spec.key)}" viewBox="{vx:.1f} {vy:.1f} {vw:.1f} {vh:.1f}" '
           f'width="{vw:.0f}" height="{vh:.0f}" font-family="{FONT}">{defs}'
           f'<rect x="{vx:.1f}" y="{vy:.1f}" width="{vw:.1f}" height="{vh:.1f}" fill="#FFFFFF"/>'
           + boundary + "".join(flow_under) + "".join(edge_svg) + "".join(node_svg)
           + "".join(f'<g class="c4-pill" data-k="{k}">{s}</g>' for k, s in pills) + "".join(flow_svg) + legend + "</svg>")
    out = out_dir / f"{spec.key}.svg"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(svg, encoding="utf-8")

    # reveal plan
    edge_keys = [r.key for r in vis_rels]
    ends = {r.key: (r.src, r.dst) for r in vis_rels}
    pill_keys = [k for k, _ in pills if not k.startswith("p:new:") and not k.startswith("p:badge:")]
    badge_keys = [k for k, _ in pills if k.startswith("p:badge:")]
    steps: list[list[str]] = []
    if flow_keys:
        steps = [[f"f:{n}"] for n, k in enumerate(flow_keys, 1) if k in ends]
    elif ov.new and not spec.steps:
        newl = [a for a in res_list(ov.new) if a in vis_els]
        shown = {a for a in vis_els if a not in newl}
        used = {k for k, (s, d) in ends.items() if s in shown and d in shown}
        for a in newl:
            shown.add(a)
            st = [f"e:{a}", f"p:new:{a}"] + [k for k, (s, d) in ends.items() if k not in used and s in shown and d in shown]
            used.update(st[2:])
            steps.append(st)
        steps += [[k] for k in pill_keys if not k.startswith("p:new:")]
    elif (pill_keys or badge_keys) and not spec.steps:
        steps = [[k] for k in pill_keys] + [[k] for k in badge_keys]
    else:
        seq = [g if isinstance(g, (list, tuple)) else [g] for g in spec.steps] if spec.steps else [[a] for a in vis_els]
        shown, used = set(), set()
        for group in seq:
            st = []
            for raw in group:
                a = _resolve(model, raw)
                if a and a in vis_els and a not in shown:
                    shown.add(a)
                    st.append(f"e:{a}")
            for k in edge_keys:
                s, d = ends[k]
                if k not in used and s in shown and d in shown:
                    used.add(k)
                    st.append(k)
            if st:
                steps.append(st)
        leftover = [f"e:{a}" for a in vis_els if a not in shown] + [k for k in edge_keys if k not in used]
        if leftover:
            if steps:
                steps[-1].extend(leftover)
            else:
                steps.append(leftover)
        steps += [[k] for k in pill_keys] + ([badge_keys] if badge_keys else [])
    out.with_suffix(".steps.json").write_text(json.dumps(steps, indent=2), encoding="utf-8")

    min_font = min(sizes) if sizes else TITLE
    min_rendered = round(min_font * scale, 2)
    meta = ViewMeta(key=spec.key, slot=spec.slot if spec.slot in SLOTS else "full", viewbox=(vx, vy, vw, vh), scale_1080p=round(scale, 4),
                    min_font_svg_px=round(min_font, 1), min_rendered_1080p_px=min_rendered, min_px=spec.min_px,
                    legibility_ok=(spec.min_px <= 0 or min_rendered >= spec.min_px) and not overflow,
                    node_keys=[f"e:{a}" for a in vis_els], edge_keys=edge_keys, unknown_aliases=sorted(set(unknown)),
                    canon=spec.canon or f"c4:{spec.source}", full=spec.full and ov.is_empty(), source=spec.source)
    d = meta.model_dump()
    d["overflow"] = overflow
    d["renderer"] = "native"
    out.with_suffix(".meta.json").write_text(json.dumps(d, indent=2), encoding="utf-8")
    return meta, overflow


def legend_svg(model: Model, view: View, els: list[str], x0: float, y1: float) -> str:
    kinds = []
    for a in els:
        e = model.els[a]
        k = ("Person", PERSON) if e.kind == "person" else (("External system", EXTERNAL) if e.external else None)
        if k and k not in kinds:
            kinds.append(k)
    kinds.append(("In scope", INTERNAL))
    out, x = [], x0 + 24
    for name, pal in kinds:
        out.append(f'<rect x="{x:.1f}" y="{y1 - 34:.1f}" width="22" height="16" rx="4" fill="{pal[1]}" stroke="{pal[0]}" stroke-width="2.5"/>'
                   + _txt(x + 30, y1 - 21, name, TECH, "#5F6368", 500, "start"))
        x += 44 + text_w(name, TECH) + 18
    return '<g class="c4-legend">' + "".join(out) + "</g>"
