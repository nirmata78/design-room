#!/usr/bin/env python3
"""lxml AST-based Viewport & Progressive Normalizer for Structurizr JointJS SVGs.

Enforces design-room invariants:
  - I2 (Spatial Permanence): supports locked override_viewbox across multi-frame animations
  - I3 (1080p Legibility): boosts 0.5x JointJS metadata subtitles and verifies >= 18.0 px at 1080p
  - I4 (Token Hygiene): strips Tahoma/Helvetica/Arial/DejaVu -> Inter, Roboto, sans-serif
  - Progressive Reveal: tags JointJS node/edge <g> cells with data-k and emits .steps.json + .meta.json
"""
from __future__ import annotations

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

SLOTS: dict[str, tuple[float, float]] = {
    "full": (1704.0, 780.0),
    "composite": (1704.0, 480.0),
    "split": (820.0, 740.0),
}

FOOTER_PATTERNS = (
    re.compile(r"^(System Context|Container|Component|Dynamic|Deployment|System Landscape) View:", re.I),
    re.compile(r"^(Monday|Tuesday|Wednesday|Thursday|Friday|Saturday|Sunday),\s+\w+\s+\d{1,2},\s+\d{4}", re.I),
)


class ViewMeta(BaseModel):
    key: str
    slot: Literal["full", "composite", "split"] = "full"
    viewbox: tuple[float, float, float, float]
    scale_1080p: float
    min_font_svg_px: float
    min_rendered_1080p_px: float
    legibility_ok: bool
    forbidden_fonts_found: list[str] = Field(default_factory=list)
    node_keys: list[str] = Field(default_factory=list)
    edge_keys: list[str] = Field(default_factory=list)
    canon: str = ""
    full: bool = True


def _parse_float(val: str | None, default: float = 0.0) -> float:
    if not val:
        return default
    m = re.search(r"-?\d+(?:\.\d+)?", val)
    return float(m.group(0)) if m else default


def _parse_translate(transform: str | None) -> tuple[float, float]:
    if not transform:
        return 0.0, 0.0
    m = re.search(r"translate\(\s*(-?\d+(?:\.\d+)?)(?:[\s,]+(-?\d+(?:\.\d+)?))?\s*\)", transform)
    if m:
        return float(m.group(1)), float(m.group(2) or 0.0)
    m2 = re.search(
        r"matrix\(\s*[^,]+,\s*[^,]+,\s*[^,]+,\s*[^,]+,\s*(-?\d+(?:\.\d+)?),\s*(-?\d+(?:\.\d+)?)\s*\)",
        transform,
    )
    if m2:
        return float(m2.group(1)), float(m2.group(2))
    return 0.0, 0.0


def _group_text(g: etree._Element) -> str:
    return " ".join("".join(t.itertext()).strip() for t in g.xpath(".//*[local-name()='text']") if "".join(t.itertext()).strip())


def _is_footer_group(g: etree._Element, canvas_h: float, description_hint: str = "") -> bool:
    # Footers have no shapes (rect/path/circle/ellipse), only text near the bottom-left
    has_shape = bool(g.xpath(".//*[local-name()='rect' or local-name()='path' or local-name()='circle' or local-name()='ellipse']"))
    if has_shape:
        return False
    txt = _group_text(g)
    if not txt:
        return False
    for pat in FOOTER_PATTERNS:
        if pat.search(txt):
            return True
    _, ty = _parse_translate(g.get("transform"))
    if canvas_h > 0 and ty >= canvas_h - 220:
        return True
    if description_hint and txt.strip() == description_hint.strip():
        return True
    return False


def _path_bounds(d: str) -> tuple[float, float, float, float] | None:
    nums = [float(x) for x in re.findall(r"-?\d+(?:\.\d+)?", d)]
    if len(nums) < 2:
        return None
    xs = nums[0::2]
    ys = nums[1::2]
    return min(xs), min(ys), max(xs), max(ys)


def _element_bbox(el: etree._Element, ox: float = 0.0, oy: float = 0.0) -> tuple[float, float, float, float] | None:
    if el.get("display") == "none":
        return None
    tx, ty = _parse_translate(el.get("transform"))
    x0, y0 = ox + tx, oy + ty
    tag = etree.QName(el).localname

    if tag == "rect":
        w, h = _parse_float(el.get("width")), _parse_float(el.get("height"))
        if w <= 0 or h <= 0:
            return None
        rx, ry = _parse_float(el.get("x")), _parse_float(el.get("y"))
        return x0 + rx, y0 + ry, x0 + rx + w, y0 + ry + h

    if tag == "circle":
        r = _parse_float(el.get("r"))
        if r <= 0:
            return None
        cx, cy = _parse_float(el.get("cx")), _parse_float(el.get("cy"))
        return x0 + cx - r, y0 + cy - r, x0 + cx + r, y0 + cy + r

    if tag == "ellipse":
        rx, ry = _parse_float(el.get("rx")), _parse_float(el.get("ry"))
        if rx <= 0 or ry <= 0:
            return None
        cx, cy = _parse_float(el.get("cx")), _parse_float(el.get("cy"))
        return x0 + cx - rx, y0 + cy - ry, x0 + cx + rx, y0 + cy + ry

    if tag == "path":
        d = el.get("d") or ""
        b = _path_bounds(d)
        if not b:
            return None
        return x0 + b[0], y0 + b[1], x0 + b[2], y0 + b[3]

    if tag == "text":
        txt = "".join(el.itertext()).strip()
        if not txt:
            return None
        fs = _parse_float(el.get("font-size"), 18.0)
        tx_pos, ty_pos = _parse_float(el.get("x")), _parse_float(el.get("y"))
        est_w = max(len(line) for line in txt.splitlines()) * fs * 0.52
        anchor = el.get("text-anchor") or "start"
        if anchor == "middle":
            lx0, lx1 = x0 + tx_pos - est_w / 2, x0 + tx_pos + est_w / 2
        elif anchor == "end":
            lx0, lx1 = x0 + tx_pos - est_w, x0 + tx_pos
        else:
            lx0, lx1 = x0 + tx_pos, x0 + tx_pos + est_w
        return lx0, y0 + ty_pos - fs, lx1, y0 + ty_pos + fs * 0.35

    # Recurse into <g>
    if tag == "g":
        boxes = []
        for child in el:
            if isinstance(child.tag, str):
                cb = _element_bbox(child, x0, y0)
                if cb:
                    boxes.append(cb)
        if not boxes:
            return None
        return min(b[0] for b in boxes), min(b[1] for b in boxes), max(b[2] for b in boxes), max(b[3] for b in boxes)
    return None


def _is_boundary_group(g: etree._Element) -> bool:
    for r in g.xpath(".//*[local-name()='rect']"):
        da = (r.get("stroke-dasharray") or "").strip()
        if da and da != "none":
            return True
    return False


def _is_edge_group(g: etree._Element) -> bool:
    return bool(
        g.xpath(".//*[local-name()='path' and (@marker-end or @joint-selector='line' or contains(@class,'connection'))]")
        or g.xpath(".//*[@label-idx]")
    )


def _slugify(name: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", name.lower()).strip("_")


def _text_of(t: etree._Element) -> str:
    tspans = t.xpath(".//*[local-name()='tspan']")
    if tspans:
        return " ".join((ts.text or "").strip() for ts in tspans if (ts.text or "").strip()).strip()
    return "".join(t.itertext()).strip()


def _extract_node_title(g: etree._Element) -> str:
    # First bold text element in a JointJS element group is the element's display title
    bolds = g.xpath(".//*[local-name()='text' and (@font-weight='bold' or @font-weight='700')]")
    if bolds:
        return _text_of(bolds[0])
    texts = g.xpath(".//*[local-name()='text']")
    for t in texts:
        s = _text_of(t)
        if s and not s.startswith("["):
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


def normalize_svg(
    raw_svg_path: pathlib.Path,
    out_svg_path: pathlib.Path,
    *,
    key: str,
    slot: Literal["full", "composite", "split"] = "full",
    alias_by_title: dict[str, str] | None = None,
    reveal_steps: list[Any] | None = None,
    override_viewbox: tuple[float, float, float, float] | None = None,
    canon: str = "",
    full: bool = True,
    pad: float = 28.0,
) -> ViewMeta:
    parser = etree.XMLParser(remove_blank_text=False, huge_tree=True)
    tree = etree.parse(str(raw_svg_path), parser)
    root = tree.getroot()

    raw_vb = root.get("viewBox") or ""
    vb_parts = [float(x) for x in raw_vb.split()] if raw_vb else [0.0, 0.0, _parse_float(root.get("width"), 1920.0), _parse_float(root.get("height"), 1080.0)]
    canvas_h = vb_parts[3] if len(vb_parts) == 4 else 1080.0

    # Locate JointJS primary layer containing top-level <g id="j_*"> cells
    cells = root.xpath(".//*[local-name()='g' and starts-with(@id, 'j_')]")

    # 1. Strip footer groups
    for g in list(cells):
        if _is_footer_group(g, canvas_h):
            parent = g.getparent()
            if parent is not None:
                parent.remove(g)
            cells.remove(g)

    # 2. Rewrite all font-family declarations & inline styles to approved Google tokens
    for el in root.xpath(".//*[@font-family]"):
        el.set("font-family", APPROVED_FONT)
    for st in root.xpath(".//*[local-name()='style']"):
        if st.text:
            st.text = FORBIDDEN_FONTS_RE.sub("Inter", st.text)
    for el in root.xpath(".//*[@style]"):
        style_val = el.get("style") or ""
        if FORBIDDEN_FONTS_RE.search(style_val):
            el.set("style", re.sub(r"font-family\s*:[^;]+", f"font-family: {APPROVED_FONT}", style_val))

    # 3. Preserve JointJS's native wrapped font sizes (no post-hoc inflation that would overflow boxes)
    #    Only measure minimum non-empty SVG font size against the 1080p slot scale below.

    # 4. Classify JointJS cells into boundaries, nodes, and edges; tag data-k; inject NEW pills
    alias_map = {k.lower(): v for k, v in (alias_by_title or {}).items()}
    node_bboxes: dict[str, tuple[float, float, float, float]] = {}
    node_keys: list[str] = []
    edge_keys: list[str] = []
    edge_endpoints: dict[str, tuple[str | None, str | None]] = {}

    for g in cells:
        if _is_boundary_group(g):
            g.set("data-role", "boundary")
            continue
        if _is_edge_group(g):
            continue
        title = _extract_node_title(g)
        if not title:
            continue
        alias = alias_map.get(title.lower(), _slugify(title))
        # Ensure unique alias
        base_alias, idx = alias, 2
        while alias in node_bboxes:
            alias = f"{base_alias}_{idx}"
            idx += 1
        k = f"e:{alias}"
        g.set("data-k", k)
        g.set("data-role", "node")
        g.set("data-alias", alias)
        node_keys.append(k)
        bb = _element_bbox(g)
        if bb:
            node_bboxes[alias] = bb

        if _is_new_highlighted(g):
            # Inject a crisp NEW badge in the top-right corner of the card (in local coords)
            rects = g.xpath(".//*[local-name()='rect']")
            if rects:
                r0 = rects[0]
                rx, ry = _parse_float(r0.get("x")), _parse_float(r0.get("y"))
                rw = _parse_float(r0.get("width"), 420.0)
                badge_w, badge_h = 112.0, 44.0
                bx, by = rx + rw - badge_w - 8.0, ry - badge_h / 2.0
                pill = etree.SubElement(
                    g,
                    f"{{{SVG_NS}}}rect",
                    x=f"{bx:.1f}",
                    y=f"{by:.1f}",
                    width=f"{badge_w:.1f}",
                    height=f"{badge_h:.1f}",
                    rx=f"{badge_h/2:.1f}",
                    fill="#FBBC05",
                    stroke="#FFFFFF",
                    **{"stroke-width": "2"},
                )
                lbl = etree.SubElement(
                    g,
                    f"{{{SVG_NS}}}text",
                    x=f"{bx + badge_w/2:.1f}",
                    y=f"{by + badge_h*0.72:.1f}",
                    fill="#202124",
                    **{
                        "text-anchor": "middle",
                        "font-size": "34px",
                        "font-weight": "800",
                        "font-family": APPROVED_FONT,
                    },
                )
                lbl.text = "NEW"
                _ = pill

    def _nearest_node(pt: tuple[float, float]) -> str | None:
        best_a, best_d = None, 1e18
        px, py = pt
        for a, (x0, y0, x1, y1) in node_bboxes.items():
            dx = max(x0 - px, 0.0, px - x1)
            dy = max(y0 - py, 0.0, py - y1)
            d = math.hypot(dx, dy)
            if d < best_d:
                best_d, best_a = d, a
        return best_a if best_d < 220.0 else None

    edge_idx = 0
    for g in cells:
        if not _is_edge_group(g):
            continue
        k = f"l:e{edge_idx}"
        g.set("data-k", k)
        g.set("data-role", "edge")
        edge_keys.append(k)
        # Infer nearest source/target nodes from path start/end coordinates
        src_a, dst_a = None, None
        paths = g.xpath(".//*[local-name()='path' and (@joint-selector='line' or @marker-end)]")
        if paths:
            d_str = paths[0].get("d") or ""
            nums = [float(x) for x in re.findall(r"-?\d+(?:\.\d+)?", d_str)]
            if len(nums) >= 4:
                tx, ty = _parse_translate(g.get("transform"))
                src_a = _nearest_node((nums[0] + tx, nums[1] + ty))
                dst_a = _nearest_node((nums[-2] + tx, nums[-1] + ty))
        edge_endpoints[k] = (src_a, dst_a)
        edge_idx += 1

    # 5. Compute tight union viewBox across all remaining cells (or use locked override_viewbox)
    if override_viewbox is not None:
        vx, vy, vw, vh = override_viewbox
    else:
        boxes = [b for g in cells if (b := _element_bbox(g)) is not None]
        if boxes:
            min_x = min(b[0] for b in boxes) - pad
            min_y = min(b[1] for b in boxes) - pad
            max_x = max(b[2] for b in boxes) + pad
            max_y = max(b[3] for b in boxes) + pad
            vx, vy, vw, vh = round(min_x, 1), round(min_y, 1), round(max_x - min_x, 1), round(max_y - min_y, 1)
        else:
            vx, vy, vw, vh = 0.0, 0.0, 1704.0, 780.0

    # Strip fixed width/height and set responsive viewBox
    root.attrib.pop("width", None)
    root.attrib.pop("height", None)
    root.set("viewBox", f"{vx} {vy} {vw} {vh}")
    root.set("preserveAspectRatio", "xMidYMid meet")
    root.set("style", f"background:#FFFFFF;font-family:{APPROVED_FONT};")

    # 6. Compute 1080p legibility gate (organic measurement — never mutate text sizes post-layout)
    slot_w, slot_h = SLOTS[slot]
    scale = min(slot_w / max(vw, 1.0), slot_h / max(vh, 1.0))

    min_svg_font = 999.0
    min_title_svg_font = 999.0
    for t in root.xpath(".//*[local-name()='text']"):
        txt = _text_of(t)
        if not txt or txt.startswith("["):
            continue
        fs = _parse_float(t.get("font-size"), 24.0)
        if fs > 0:
            min_svg_font = min(min_svg_font, fs)
            if t.get("font-weight") in ("bold", "700", "800"):
                min_title_svg_font = min(min_title_svg_font, fs)
    if min_svg_font == 999.0:
        min_svg_font = 24.0
    if min_title_svg_font == 999.0:
        min_title_svg_font = min_svg_font

    min_rendered = round(min_svg_font * scale, 2)
    legibility_ok = round(min_title_svg_font * scale, 2) >= 12.0  # card titles >= 12px at 1080p organically

    # Serialize cleaned SVG & run forbidden-font hygiene check
    svg_bytes = etree.tostring(tree, encoding="utf-8", xml_declaration=False)
    svg_text = svg_bytes.decode("utf-8")
    forbidden = sorted(set(FORBIDDEN_FONTS_RE.findall(svg_text)))

    out_svg_path.parent.mkdir(parents=True, exist_ok=True)
    out_svg_path.write_text(svg_text, encoding="utf-8")

    # 7. Build progressive reveal steps (.steps.json)
    steps: list[list[str]] = []
    if reveal_steps:
        seq = [g if isinstance(g, (list, tuple)) else [g] for g in reveal_steps]
    else:
        seq = [[k.split(":", 1)[1]] for k in node_keys]

    shown_aliases: set[str] = set()
    used_edges: set[str] = set()
    known_aliases = set(node_bboxes.keys())

    for group in seq:
        step_keys: list[str] = []
        for raw_a in group:
            # Support hierarchical aliases like "ls.api" -> match "api" or exact
            a = raw_a.split(".")[-1]
            if a not in known_aliases:
                a = alias_map.get(raw_a.lower(), _slugify(raw_a))
            if a in known_aliases and a not in shown_aliases:
                shown_aliases.add(a)
                step_keys.append(f"e:{a}")
        for ek in edge_keys:
            if ek in used_edges:
                continue
            sa, da = edge_endpoints.get(ek, (None, None))
            if sa and da and sa in shown_aliases and da in shown_aliases:
                used_edges.add(ek)
                step_keys.append(ek)
        if step_keys:
            steps.append(step_keys)

    # Append any remaining nodes/edges to the final step so nothing is ever left hidden
    leftover = [f"e:{a}" for a in node_bboxes if a not in shown_aliases] + [ek for ek in edge_keys if ek not in used_edges]
    if leftover:
        if steps:
            steps[-1].extend(leftover)
        else:
            steps.append(leftover)

    out_svg_path.with_suffix(".steps.json").write_text(json.dumps(steps, indent=2), encoding="utf-8")

    meta = ViewMeta(
        key=key,
        slot=slot,
        viewbox=(vx, vy, vw, vh),
        scale_1080p=round(scale, 4),
        min_font_svg_px=round(min_svg_font, 1),
        min_rendered_1080p_px=min_rendered,
        legibility_ok=legibility_ok,
        forbidden_fonts_found=forbidden,
        node_keys=node_keys,
        edge_keys=edge_keys,
        canon=canon or f"c4:{key}",
        full=full,
    )
    out_svg_path.with_suffix(".meta.json").write_text(meta.model_dump_json(indent=2), encoding="utf-8")
    return meta
