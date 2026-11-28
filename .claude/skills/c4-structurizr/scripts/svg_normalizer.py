#!/usr/bin/env python3
"""lxml AST-based viewport, overlay and progressive-reveal normalizer for Structurizr (JointJS) SVG exports.

Enforces design-room invariants:
  - I2 (Spatial Permanence): a derived view can lock its viewBox to another view's (version deltas V1 → Vn keep every box
    in the same pixel position; hidden boxes leave a hole, they never pull the layout)
  - I3 (1080p Legibility): measures the smallest visible text against the slot it is shown in, never mutates text sizes
  - I4 (Token Hygiene): rewrites every font family to Inter, Roboto, sans-serif
  - Progressive Reveal: tags node/edge <g> cells with data-k and writes .steps.json + .meta.json beside the SVG

Overlays (2026-11-28, issue #5), all declared per view in views.json and applied by alias:
  hide       remove nodes (and every edge that touches them) or single edges "a->b"  — how V1 … Vn are cut from one master
  new        Google Yellow border + NEW pill; carried boxes show on frame 0, new ones reveal one per step
  breaks     Google Red border + BREAKS pill        fix   Google Green border + FIX pill
  focus      Google Blue border + IN FOCUS pill     alternate  dashed yellow border + ALTERNATE pill
  badges     {"alias": "M1 · Dedup"}: a pill on the bottom edge of the box (mechanism or technology)
  keep       dim every other box and edge to 0.25 opacity; with crop, the viewBox shrinks to the kept boxes
  flow       ["a->b", ...]: a numbered #1967D2 disc and a highlighted copy of each edge, one reveal step per arrow
"""
from __future__ import annotations

import copy
import json
import math
import pathlib
import re
from typing import Any, Literal

from lxml import etree
from pydantic import BaseModel, Field

SVG_NS = "http://www.w3.org/2000/svg"
FORBIDDEN_FONTS_RE = re.compile(r"\b(Charter|Georgia|Helvetica|Arial|DejaVu|Tahoma|Verdana|STIX)\b", re.I)
APPROVED_FONT = "Inter, Roboto, sans-serif"

# Area a figure gets on a 1920×1080 frame (frame px). "stage" is a diagram-only slide with a one-line header.
SLOTS: dict[str, tuple[float, float]] = {
    "full": (1704.0, 780.0),
    "stage": (1800.0, 860.0),
    "composite": (1704.0, 480.0),
    "split": (820.0, 740.0),
}
Slot = Literal["full", "stage", "composite", "split"]

# Google palette for overlays (DESIGN-TOKENS.md)
YELLOW, RED, GREEN, BLUE, BLUE_INK, INK = "#FBBC05", "#EA4335", "#34A853", "#4285F4", "#1967D2", "#202124"
STATUS = {  # overlay -> (stroke, pill fill, pill text colour, label, dashed)
    "new": (YELLOW, YELLOW, INK, "NEW", False),
    "breaks": (RED, RED, "#FFFFFF", "BREAKS", False),
    "fix": (GREEN, GREEN, "#FFFFFF", "FIX", False),
    "focus": (BLUE, BLUE, "#FFFFFF", "IN FOCUS", False),
    "alternate": (YELLOW, YELLOW, INK, "ALTERNATE", True),
}

FOOTER_PATTERNS = (
    re.compile(r"^(System Context|Container|Component|Dynamic|Deployment|System Landscape) View:", re.I),
    re.compile(r"^(Monday|Tuesday|Wednesday|Thursday|Friday|Saturday|Sunday),\s+\w+\s+\d{1,2},\s+\d{4}", re.I),
)


class Overlay(BaseModel):
    hide: list[str] = Field(default_factory=list)
    new: list[str] = Field(default_factory=list)
    breaks: list[str] = Field(default_factory=list)
    fix: list[str] = Field(default_factory=list)
    focus: list[str] = Field(default_factory=list)
    alternate: list[str] = Field(default_factory=list)
    badges: dict[str, str] = Field(default_factory=dict)
    keep: list[str] = Field(default_factory=list)
    crop: bool = False
    flow: list[str] = Field(default_factory=list)
    dim: float = 0.25

    def marked(self) -> list[str]:
        return [*self.breaks, *self.fix, *self.focus, *self.alternate, *self.new]

    def is_empty(self) -> bool:
        return not any([self.hide, self.new, self.breaks, self.fix, self.focus, self.alternate, self.badges, self.keep, self.flow])


class ViewMeta(BaseModel):
    key: str
    slot: Slot = "full"
    viewbox: tuple[float, float, float, float]
    scale_1080p: float
    min_font_svg_px: float
    min_rendered_1080p_px: float
    min_px: float = 18.0
    legibility_ok: bool
    forbidden_fonts_found: list[str] = Field(default_factory=list)
    node_keys: list[str] = Field(default_factory=list)
    edge_keys: list[str] = Field(default_factory=list)
    unknown_aliases: list[str] = Field(default_factory=list)
    canon: str = ""
    full: bool = True
    source: str = ""


# ── geometry ─────────────────────────────────────────────────────────────────────────────────────────────────────────
def _parse_float(val: str | None, default: float = 0.0) -> float:
    if not val:
        return default
    m = re.search(r"-?\d+(?:\.\d+)?(?:e-?\d+)?", val)
    return float(m.group(0)) if m else default


def _parse_translate(transform: str | None) -> tuple[float, float]:
    if not transform:
        return 0.0, 0.0
    m = re.search(r"translate\(\s*(-?\d+(?:\.\d+)?)(?:[\s,]+(-?\d+(?:\.\d+)?))?\s*\)", transform)
    if m:
        return float(m.group(1)), float(m.group(2) or 0.0)
    m2 = re.search(r"matrix\(\s*[^,]+,\s*[^,]+,\s*[^,]+,\s*[^,]+,\s*(-?[\d.e-]+),\s*(-?[\d.e-]+)\s*\)", transform)
    if m2:
        return float(m2.group(1)), float(m2.group(2))
    return 0.0, 0.0


def _path_points(d: str) -> list[tuple[float, float]]:
    """Absolute points of a JointJS path (M/L/C/Q with absolute coordinates; arcs of cylinders are relative and skipped)."""
    if re.search(r"[a-z]", d.replace("e-", "")):
        nums = [float(x) for x in re.findall(r"-?\d+(?:\.\d+)?", d)]
        return [(nums[0], nums[1])] if len(nums) >= 2 else []
    nums = [float(x) for x in re.findall(r"-?\d+(?:\.\d+)?(?:e-?\d+)?", d)]
    return list(zip(nums[0::2], nums[1::2]))


def _hidden(el: etree._Element) -> bool:
    style = (el.get("style") or "").replace(" ", "")
    if "display:none" in style:
        return True
    return el.get("display") == "none" and "display:block" not in style


def _shape_bbox(el: etree._Element, ox: float = 0.0, oy: float = 0.0) -> tuple[float, float, float, float] | None:
    """Bounding box from shapes only (rect, circle, ellipse, path, line). Text is ignored: in a Structurizr export every
    label sits inside a shape (a box, or an edge label's white rect), and estimating text width only inflates the box."""
    if _hidden(el):
        return None
    tx, ty = _parse_translate(el.get("transform"))
    x0, y0 = ox + tx, oy + ty
    tag = etree.QName(el).localname if isinstance(el.tag, str) else ""
    if tag == "rect":
        w, h = _parse_float(el.get("width")), _parse_float(el.get("height"))
        if w <= 0 or h <= 0 or (el.get("stroke") == "transparent" and el.get("fill") in (None, "none")):
            return None
        rx, ry = _parse_float(el.get("x")), _parse_float(el.get("y"))
        return x0 + rx, y0 + ry, x0 + rx + w, y0 + ry + h
    if tag == "circle":
        r = _parse_float(el.get("r"))
        cx, cy = _parse_float(el.get("cx")), _parse_float(el.get("cy"))
        return (x0 + cx - r, y0 + cy - r, x0 + cx + r, y0 + cy + r) if r > 0 else None
    if tag == "ellipse":
        rx, ry = _parse_float(el.get("rx")), _parse_float(el.get("ry"))
        cx, cy = _parse_float(el.get("cx")), _parse_float(el.get("cy"))
        return (x0 + cx - rx, y0 + cy - ry, x0 + cx + rx, y0 + cy + ry) if rx > 0 and ry > 0 else None
    if tag == "line":
        xs = [_parse_float(el.get("x1")), _parse_float(el.get("x2"))]
        ys = [_parse_float(el.get("y1")), _parse_float(el.get("y2"))]
        return x0 + min(xs), y0 + min(ys), x0 + max(xs), y0 + max(ys)
    if tag == "path":
        if el.get("joint-selector") == "wrapper":
            return None
        d = el.get("d") or ""
        if re.search(r"[a-z]", d.replace("e-", "")):          # relative path (cylinder): its group's rect carries the box
            return None
        pts = _path_points(d)
        if not pts:
            return None
        return x0 + min(p[0] for p in pts), y0 + min(p[1] for p in pts), x0 + max(p[0] for p in pts), y0 + max(p[1] for p in pts)
    if tag == "g":
        boxes = [b for c in el if isinstance(c.tag, str) and (b := _shape_bbox(c, x0, y0))]
        if not boxes:
            return None
        return min(b[0] for b in boxes), min(b[1] for b in boxes), max(b[2] for b in boxes), max(b[3] for b in boxes)
    return None


_element_bbox = _shape_bbox   # backwards-compatible name


def _union(boxes: list[tuple[float, float, float, float]]) -> tuple[float, float, float, float] | None:
    boxes = [b for b in boxes if b]
    if not boxes:
        return None
    return min(b[0] for b in boxes), min(b[1] for b in boxes), max(b[2] for b in boxes), max(b[3] for b in boxes)


# ── classification ───────────────────────────────────────────────────────────────────────────────────────────────────
def _text_of(t: etree._Element) -> str:
    tspans = t.xpath(".//*[local-name()='tspan']")
    if tspans:
        return " ".join((ts.text or "").strip() for ts in tspans if (ts.text or "").strip()).strip()
    return "".join(t.itertext()).strip()


def _visible_text(t: etree._Element) -> bool:
    txt = _text_of(t)
    if not txt or txt == "-":
        return False
    for anc in [t, *t.iterancestors()]:
        if _hidden(anc):
            return False
    for ts in t.xpath(".//*[local-name()='tspan']"):
        if "fill-opacity: 0" in (ts.get("style") or "") or "fill-opacity:0" in (ts.get("style") or ""):
            return False
    return True


def _group_text(g: etree._Element) -> str:
    return " ".join(_text_of(t) for t in g.xpath(".//*[local-name()='text']") if _text_of(t))


def _is_footer_group(g: etree._Element, canvas_h: float) -> bool:
    if g.xpath(".//*[local-name()='rect' or local-name()='path' or local-name()='circle' or local-name()='ellipse']"):
        return False
    txt = _group_text(g)
    if not txt:
        return False
    if any(p.search(txt) for p in FOOTER_PATTERNS):
        return True
    _, ty = _parse_translate(g.get("transform"))
    return canvas_h > 0 and ty >= canvas_h - 220


def _is_boundary_group(g: etree._Element) -> bool:
    for r in g.xpath(".//*[local-name()='rect']"):
        da = (r.get("stroke-dasharray") or "").strip()
        if da and da != "none" and _parse_float(r.get("width")) > 0:
            return True
    return False


def _is_edge_group(g: etree._Element) -> bool:
    return bool(g.xpath(".//*[local-name()='path' and (@marker-end or @joint-selector='line' or contains(@class,'connection'))]")
                or g.xpath(".//*[@label-idx]"))


def _slugify(name: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", name.lower()).strip("_")


def _extract_node_title(g: etree._Element) -> str:
    bolds = g.xpath(".//*[local-name()='text' and (@font-weight='bold' or @font-weight='700')]")
    for b in bolds:
        if _visible_text(b):
            return _text_of(b)
    for t in g.xpath(".//*[local-name()='text']"):
        s = _text_of(t)
        if s and s != "-" and not s.startswith("["):
            return s
    return ""


def _is_new_highlighted(g: etree._Element) -> bool:
    for shape in g.xpath(".//*[local-name()='rect' or local-name()='path' or local-name()='ellipse']"):
        stroke = (shape.get("stroke") or "").upper()
        style = (shape.get("style") or "").upper()
        sw = _parse_float(shape.get("stroke-width"), 0.0)
        if ("FBBC05" in stroke or "F9AB00" in stroke or "RGB(251, 188, 5)" in style or "RGB(249, 171, 0)" in style) and sw >= 5:
            return True
    return False


def _primary_shapes(g: etree._Element) -> list[etree._Element]:
    """The visible outline(s) of a node: the box, the cylinder path, or the person's body and head."""
    out = []
    for s in g.xpath(".//*[local-name()='rect' or local-name()='path' or local-name()='circle' or local-name()='ellipse']"):
        if (s.get("stroke") or "none") in ("none", "transparent") or _parse_float(s.get("stroke-width"), 1) == 0:
            continue
        out.append(s)
    return out


def _title_font(g: etree._Element) -> float:
    for b in g.xpath(".//*[local-name()='text' and (@font-weight='bold' or @font-weight='700')]"):
        if _visible_text(b):
            return _parse_float(b.get("font-size"), 40.0)
    return 40.0


# ── overlay drawing ──────────────────────────────────────────────────────────────────────────────────────────────────
def _svg(tag: str, parent: etree._Element | None = None, **attrs: Any) -> etree._Element:
    a = {k.replace("_", "-"): str(v) for k, v in attrs.items()}
    return etree.SubElement(parent, f"{{{SVG_NS}}}{tag}", a) if parent is not None else etree.Element(f"{{{SVG_NS}}}{tag}", a)


def _pill(parent: etree._Element, x: float, y: float, text: str, fill: str, fg: str, size: float, anchor: str = "end") -> etree._Element:
    """A rounded label. (x, y) is the right end (anchor="end") or the centre (anchor="middle") of the pill's baseline row."""
    h = size * 1.45
    w = len(text) * size * 0.64 + size * 1.1
    left = x - w if anchor == "end" else x - w / 2
    g = _svg("g", parent, **{"class": "c4-pill"})
    _svg("rect", g, x=f"{left:.1f}", y=f"{y - h / 2:.1f}", width=f"{w:.1f}", height=f"{h:.1f}", rx=f"{h / 2:.1f}",
         fill=fill, stroke="#FFFFFF", stroke_width="3")
    t = _svg("text", g, x=f"{left + w / 2:.1f}", y=f"{y + size * 0.36:.1f}", fill=fg, text_anchor="middle",
             font_size=f"{size:.0f}px", font_weight="800", font_family=APPROVED_FONT, letter_spacing="0.5")
    t.text = text
    return g


def _restroke(g: etree._Element, colour: str, width: float = 7.0, dashed: bool = False) -> None:
    for s in _primary_shapes(g):
        s.set("stroke", colour)
        s.set("stroke-width", f"{width:g}")
        st = re.sub(r"stroke\s*:[^;]+;?", "", s.get("style") or "")
        s.set("style", st + f"stroke: {colour};")
        if dashed:
            s.set("stroke-dasharray", "18,10")


def _point_on_path(pts: list[tuple[float, float]], frac: float = 0.5) -> tuple[float, float]:
    segs = list(zip(pts, pts[1:]))
    total = sum(math.dist(a, b) for a, b in segs) or 1.0
    goal, run = total * frac, 0.0
    for a, b in segs:
        d = math.dist(a, b)
        if run + d >= goal and d > 0:
            t = (goal - run) / d
            return a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t
        run += d
    return pts[-1]


def _namespace_ids(root: etree._Element, key: str) -> None:
    """Prefix every id with the view key and rewrite its references (url(#…), href="#…"). Many views are inlined into one
    HTML deck; Structurizr numbers its ids (v-12, j_3) the same way in every export, so unprefixed ids collide and an
    arrow can pick up another figure's marker."""
    ns = re.sub(r"[^A-Za-z0-9_-]+", "-", key)
    ids = {el.get("id") for el in root.iter() if isinstance(el.tag, str) and el.get("id")}
    if not ids:
        return
    ref = re.compile(r"url\(\s*['\"]?#([^)'\"]+)['\"]?\s*\)")
    for el in root.iter():
        if not isinstance(el.tag, str):
            continue
        if el.get("id"):
            el.set("id", f"{ns}--{el.get('id')}")
        for name, val in list(el.attrib.items()):
            if name == "id":
                continue
            if "url(" in val:
                el.set(name, ref.sub(lambda m: f"url(#{ns}--{m.group(1)})" if m.group(1) in ids else m.group(0), val))
            elif name.endswith("href") and val.startswith("#") and val[1:] in ids:
                el.set(name, f"#{ns}--{val[1:]}")
        if etree.QName(el).localname == "style" and el.text:
            el.text = ref.sub(lambda m: f"url(#{ns}--{m.group(1)})" if m.group(1) in ids else m.group(0), el.text)


# ── the normalizer ───────────────────────────────────────────────────────────────────────────────────────────────────
def normalize_svg(
    raw_svg_path: pathlib.Path,
    out_svg_path: pathlib.Path,
    *,
    key: str,
    slot: Slot = "full",
    alias_by_title: dict[str, str] | None = None,
    reveal_steps: list[Any] | None = None,
    override_viewbox: tuple[float, float, float, float] | None = None,
    canon: str = "",
    full: bool = True,
    pad: float = 28.0,
    overlay: Overlay | None = None,
    min_px: float = 18.0,
    source: str = "",
) -> ViewMeta:
    ov = overlay or Overlay()
    parser = etree.XMLParser(remove_blank_text=False, huge_tree=True)
    tree = etree.parse(str(raw_svg_path), parser)
    root = tree.getroot()

    raw_vb = root.get("viewBox") or ""
    vb_parts = [float(x) for x in raw_vb.split()] if raw_vb else [0.0, 0.0, _parse_float(root.get("width"), 1920.0), _parse_float(root.get("height"), 1080.0)]
    canvas_h = vb_parts[3] if len(vb_parts) == 4 else 1080.0

    cells = root.xpath(".//*[local-name()='g' and starts-with(@id, 'j_')]")

    # 1. strip footers (view title and date)
    for g in list(cells):
        if _is_footer_group(g, canvas_h):
            if (p := g.getparent()) is not None:
                p.remove(g)
            cells.remove(g)

    # 2. fonts → approved Google tokens
    for el in root.xpath(".//*[@font-family]"):
        el.set("font-family", APPROVED_FONT)
    for st in root.xpath(".//*[local-name()='style']"):
        if st.text:
            st.text = FORBIDDEN_FONTS_RE.sub("Inter", st.text)
    for el in root.xpath(".//*[@style]"):
        sv = el.get("style") or ""
        if FORBIDDEN_FONTS_RE.search(sv):
            el.set("style", re.sub(r"font-family\s*:[^;]+", f"font-family: {APPROVED_FONT}", sv))

    # 3. classify cells and tag data-k
    alias_map = {k.lower(): v for k, v in (alias_by_title or {}).items()}
    nodes: dict[str, etree._Element] = {}
    node_bboxes: dict[str, tuple[float, float, float, float]] = {}
    boundaries: list[etree._Element] = []
    edge_cells: list[etree._Element] = []
    for g in cells:
        if _is_boundary_group(g):
            g.set("data-role", "boundary")
            boundaries.append(g)
            continue
        if _is_edge_group(g):
            edge_cells.append(g)
            continue
        title = _extract_node_title(g)
        if not title:
            continue
        alias = alias_map.get(title.lower(), _slugify(title))
        base, i = alias, 2
        while alias in nodes:
            alias, i = f"{base}_{i}", i + 1
        g.set("data-k", f"e:{alias}")
        g.set("data-role", "node")
        g.set("data-alias", alias)
        nodes[alias] = g
        if bb := _shape_bbox(g):
            node_bboxes[alias] = bb

    def _nearest(pt: tuple[float, float]) -> str | None:
        best, best_d = None, 1e18
        for a, (x0, y0, x1, y1) in node_bboxes.items():
            d = math.hypot(max(x0 - pt[0], 0.0, pt[0] - x1), max(y0 - pt[1], 0.0, pt[1] - y1))
            if d < best_d:
                best, best_d = a, d
        return best if best_d < 220.0 else None

    edges: dict[str, etree._Element] = {}
    ends: dict[str, tuple[str | None, str | None]] = {}
    edge_pts: dict[str, list[tuple[float, float]]] = {}
    for i, g in enumerate(edge_cells):
        k = f"l:e{i}"
        g.set("data-k", k)
        g.set("data-role", "edge")
        edges[k] = g
        line = g.xpath(".//*[local-name()='path' and (@joint-selector='line' or @marker-end)]")
        pts = _path_points(line[0].get("d") or "") if line else []
        tx, ty = _parse_translate(g.get("transform"))
        pts = [(x + tx, y + ty) for x, y in pts]
        edge_pts[k] = pts
        ends[k] = (_nearest(pts[0]), _nearest(pts[-1])) if len(pts) >= 2 else (None, None)
        g.set("data-src", ends[k][0] or "")
        g.set("data-dst", ends[k][1] or "")

    def _edge(spec: str) -> str | None:
        a, _, b = (x.strip().split(".")[-1] for x in spec.partition("->"))
        for k, (s, d) in ends.items():
            if (s, d) == (a, b):
                return k
        for k, (s, d) in ends.items():
            if (s, d) == (b, a):
                return k
        return None

    def _resolve(raw_a: str) -> str | None:
        a = raw_a.split(".")[-1]
        if a in nodes:
            return a
        a2 = alias_map.get(raw_a.lower(), _slugify(raw_a))
        return a2 if a2 in nodes else None

    referenced = [*ov.hide, *ov.marked(), *ov.badges.keys(), *ov.keep]
    unknown = sorted({r for r in referenced if "->" not in r and _resolve(r) is None}
                     | {f for f in [*ov.flow, *[h for h in ov.hide if "->" in h]] if _edge(f) is None})

    # 4. hide (version cuts): nodes, their edges, and single edges
    hidden_nodes = {a for r in ov.hide if "->" not in r and (a := _resolve(r))}
    hidden_edges = {k for r in ov.hide if "->" in r and (k := _edge(r))}
    hidden_edges |= {k for k, (s, d) in ends.items() if s in hidden_nodes or d in hidden_nodes}
    for a in hidden_nodes:
        nodes[a].getparent().remove(nodes[a])
        del nodes[a]
    for k in hidden_edges:
        edges[k].getparent().remove(edges[k])
        del edges[k]

    # 5. viewBox: locked, cropped to the kept boxes, or the union of what is left (boundaries included)
    focus_set = {a for r in [*ov.keep, *ov.marked()] if (a := _resolve(r))}
    if override_viewbox is not None and not ov.crop:
        vx, vy, vw, vh = override_viewbox
    else:
        if ov.crop and focus_set:
            boxes = [node_bboxes[a] for a in focus_set if a in node_bboxes]
            boxes += [_shape_bbox(edges[k]) for k, (s, d) in ends.items() if k in edges and s in focus_set and d in focus_set]
            u = _union([b for b in boxes if b])
            pad_c = pad + 60.0                                        # room for the pills above the boxes
        else:
            u = _union([b for g in [*nodes.values(), *edges.values(), *boundaries] if (b := _shape_bbox(g))])
            pad_c = pad + (60.0 if ov.marked() else 0.0)
        if u:
            vx, vy = round(u[0] - pad_c, 1), round(u[1] - pad_c, 1)
            vw, vh = round(u[2] - u[0] + 2 * pad_c, 1), round(u[3] - u[1] + 2 * pad_c, 1)
        else:
            vx, vy, vw, vh = 0.0, 0.0, 1704.0, 780.0

    root.attrib.pop("width", None)
    root.attrib.pop("height", None)
    root.set("viewBox", f"{vx} {vy} {vw} {vh}")
    root.set("preserveAspectRatio", "xMidYMid meet")
    root.set("style", f"background:#FFFFFF;font-family:{APPROVED_FONT};")

    # 6. overlays: dim, status borders and pills, badges, flow discs
    layer = root.xpath(".//*[@joint-selector='layers']") or [root]
    top = _svg("g", layer[0] if layer[0] is not root else root, **{"class": "c4-overlays"})
    pill_keys: list[str] = []

    if ov.keep:
        keep = {a for r in ov.keep if (a := _resolve(r))} | focus_set
        for a, g in nodes.items():
            if a not in keep:
                g.set("opacity", f"{ov.dim:g}")
        for k, g in edges.items():
            s, d = ends[k]
            if not (s in keep and d in keep):
                g.set("opacity", f"{ov.dim:g}")

    auto_new = [a for a, g in nodes.items() if _is_new_highlighted(g) and a not in {_resolve(x) for x in ov.new}]
    for kind in ("alternate", "new", "focus", "fix", "breaks"):
        names = getattr(ov, kind) + (auto_new if kind == "new" else [])
        stroke, fill, fg, label, dashed = STATUS[kind]
        for raw in names:
            a = _resolve(raw)
            if not a or a not in nodes or a not in node_bboxes:
                continue
            g = nodes[a]
            if raw in getattr(ov, kind):
                _restroke(g, stroke, dashed=dashed)
            x0, y0, x1, _ = node_bboxes[a]
            size = max(30.0, _title_font(g) * 0.72)
            p = _pill(top, x1 - 6, y0, label, fill, fg, size)
            p.set("data-k", f"p:{kind}:{a}")
            if kind != "new":                                         # NEW pills arrive with their box
                pill_keys.append(f"p:{kind}:{a}")
            else:
                p.set("data-for", f"e:{a}")
    for raw, text in ov.badges.items():
        a = _resolve(raw)
        if not a or a not in node_bboxes:
            continue
        x0, _, x1, y1 = node_bboxes[a]
        size = max(28.0, _title_font(nodes[a]) * 0.62)
        p = _pill(top, (x0 + x1) / 2, y1, text, "#FFFFFF", BLUE_INK, size, anchor="middle")
        p[0].set("stroke", BLUE_INK)
        p.set("data-k", f"p:badge:{a}")

    flow_keys: list[str] = []
    for n, spec in enumerate(ov.flow, 1):
        k = _edge(spec)
        if not k or k not in edges or len(edge_pts[k]) < 2:
            continue
        g = _svg("g", top, **{"class": "c4-flow", "data-k": f"f:{n}"})
        hl = copy.deepcopy(edges[k].xpath(".//*[local-name()='path' and @joint-selector='line']")[0])
        hl.set("stroke", BLUE_INK)
        hl.set("stroke-width", "9")
        hl.set("stroke-dasharray", "")
        hl.attrib.pop("marker-end", None)
        tx, ty = _parse_translate(edges[k].get("transform"))
        if tx or ty:
            hl.set("transform", f"translate({tx},{ty})")
        g.append(hl)
        cx, cy = _point_on_path(edge_pts[k], 0.32)
        r = 30.0
        _svg("circle", g, cx=f"{cx:.1f}", cy=f"{cy:.1f}", r=f"{r:g}", fill=BLUE_INK, stroke="#FFFFFF", stroke_width="4")
        t = _svg("text", g, x=f"{cx:.1f}", y=f"{cy + r * 0.38:.1f}", fill="#FFFFFF", text_anchor="middle", font_size="36px",
                 font_weight="800", font_family=APPROVED_FONT)
        t.text = str(n)
        flow_keys.append(f"f:{n}")

    # 7. legibility: the smallest visible text inside the viewBox, at the slot's scale
    slot_w, slot_h = SLOTS[slot]
    scale = min(slot_w / max(vw, 1.0), slot_h / max(vh, 1.0))
    sizes = []
    for t in root.xpath(".//*[local-name()='text']"):
        if not _visible_text(t):
            continue
        txt = _text_of(t)
        if txt.startswith("["):
            continue
        if any(a.get("opacity") == f"{ov.dim:g}" for a in t.iterancestors()):
            continue
        fs = _parse_float(t.get("font-size"), 24.0)
        if fs > 0:
            sizes.append(fs)
    min_svg_font = min(sizes) if sizes else 24.0
    min_rendered = round(min_svg_font * scale, 2)
    legibility_ok = min_px <= 0 or min_rendered >= min_px

    _namespace_ids(root, key)
    svg_text = etree.tostring(tree, encoding="utf-8", xml_declaration=False).decode("utf-8")
    forbidden = sorted(set(FORBIDDEN_FONTS_RE.findall(svg_text)))
    out_svg_path.parent.mkdir(parents=True, exist_ok=True)
    out_svg_path.write_text(svg_text, encoding="utf-8")

    # 8. reveal plan
    edge_keys = list(edges)
    node_keys = [f"e:{a}" for a in nodes]
    steps: list[list[str]] = []
    if flow_keys:
        steps = [[k] for k in flow_keys]
    elif ov.new and not reveal_steps:
        shown = {a for a in nodes if a not in {_resolve(x) for x in ov.new}}
        used = {k for k, (s, d) in ends.items() if k in edges and s in shown and d in shown}
        for raw in ov.new:
            a = _resolve(raw)
            if not a or a not in nodes:
                continue
            shown.add(a)
            st = [f"e:{a}", f"p:new:{a}"]
            for k, (s, d) in ends.items():
                if k in edges and k not in used and s in shown and d in shown:
                    used.add(k)
                    st.append(k)
            steps.append(st)
    elif pill_keys and not reveal_steps:
        steps = [[k] for k in pill_keys] + ([[f"p:badge:{_resolve(b)}" for b in ov.badges if _resolve(b)]] if ov.badges else [])
    elif ov.badges and not reveal_steps:
        steps = [[f"p:badge:{a}"] for b in ov.badges if (a := _resolve(b))]
    else:
        seq = [g if isinstance(g, (list, tuple)) else [g] for g in reveal_steps] if reveal_steps else [[k[2:]] for k in node_keys]
        shown: set[str] = set()
        used: set[str] = set()
        for group in seq:
            st: list[str] = []
            for raw in group:
                a = _resolve(raw)
                if a and a not in shown:
                    shown.add(a)
                    st.append(f"e:{a}")
                    if a in auto_new:
                        st.append(f"p:new:{a}")
            for k in edge_keys:
                s, d = ends[k]
                if k not in used and s in shown and d in shown:
                    used.add(k)
                    st.append(k)
            if st:
                steps.append(st)
        leftover = [f"e:{a}" for a in nodes if a not in shown] + [k for k in edge_keys if k not in used]
        if leftover:
            (steps[-1] if steps else steps.append([]) or steps[-1]).extend(leftover)
        if pill_keys:
            steps += [[k] for k in pill_keys]
    out_svg_path.with_suffix(".steps.json").write_text(json.dumps(steps, indent=2), encoding="utf-8")

    meta = ViewMeta(
        key=key, slot=slot, viewbox=(vx, vy, vw, vh), scale_1080p=round(scale, 4), min_font_svg_px=round(min_svg_font, 1),
        min_rendered_1080p_px=min_rendered, min_px=min_px, legibility_ok=legibility_ok, forbidden_fonts_found=forbidden,
        node_keys=node_keys, edge_keys=edge_keys, unknown_aliases=unknown, canon=canon or f"c4:{key}",
        full=full and ov.is_empty(), source=source or key,
    )
    out_svg_path.with_suffix(".meta.json").write_text(meta.model_dump_json(indent=2), encoding="utf-8")
    return meta
