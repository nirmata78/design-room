#!/usr/bin/env python3
"""Small non-C4 figures in the Google theme: the latency/freshness budget bar and a few drawing primitives.

    from figsvg import budget_bar, svgdoc, T, R, L
    budget_bar("svg/budget.svg", [("SDK batching", 1.0, "client"), ("query", 1.0, "data")], total=10, unit="s", title="…")

Ported from the retired slide-video-kit basesvg.py (2026-11-28, issue #5); C4 boxes are drawn by c4-structurizr, never here.
"""
import html, pathlib, sys
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from gtheme import ink, FONT, DISPLAY, INK, RED, GREEN, GREY  # noqa: E402

ROLE = {  # fill, stroke, text
    "client":  ("#ffffff", "#4285f4", "#202124"),
    "edge":    ("#e8f0fe", "#4285f4", "#202124"),
    "service": ("#d2e3fc", "#1967d2", "#202124"),
    "data":    ("#e6f4ea", "#34a853", "#202124"),
    "cache":   ("#fef7e0", "#fbbc05", "#202124"),
    "queue":   ("#f1f3f4", "#5f6368", "#202124"),
    "ext":     ("#f8f9fa", "#5f6368", "#3c4043"),
}


def esc(s): return html.escape(str(s))


def svgdoc(w, h, body):
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" width="{w}" height="{h}">'
            f'<rect width="{w}" height="{h}" fill="#ffffff"/>{body}</svg>')


def T(x, y, s, size=24, fill=INK, w=500, anchor="start"):
    return (f'<text x="{x}" y="{y}" text-anchor="{anchor}" font-family="{FONT}" font-size="{size}" font-weight="{w}" '
            f'fill="{ink(fill)}">{esc(s)}</text>')


def R(x, y, w, h, fill, stroke, rx=10, sw=2.2):
    return f'<rect x="{x:.1f}" y="{y:.1f}" width="{w:.1f}" height="{h:.1f}" rx="{rx}" fill="{fill}" stroke="{stroke}" stroke-width="{sw}"/>'


def L(x1, y1, x2, y2, col=INK, sw=2.4, dash=False):
    return f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="{col}" stroke-width="{sw}"{" stroke-dasharray=\"8 6\"" if dash else ""}/>'


def budget_bar(path, stages, total, unit="ms", spare="spare", title=None, w=1600, h=420):
    """One horizontal bar whose segments sum to the SLO, with the leftover drawn as an explicit spare segment.
    stages: [(label, value)] or [(label, value, role)] — role picks the colour (ROLE keys). Labels of narrow
    segments are staggered on two rows, so neighbours never overlap."""
    used = sum(s[1] for s in stages)
    rest = total - used
    segs = [(s[0], s[1], s[2] if len(s) > 2 else "service", False) for s in stages]
    if rest > 0:
        segs.append((spare, rest, None, True))
    x0, bw, by, bh, fs = 40, w - 80, 190, 110, 25
    out, x, row = [], x0, 0
    if title:
        out.append(f'<text x="{x0}" y="46" font-family="{DISPLAY}" font-size="30" font-weight="800" fill="{INK}">{esc(title)}</text>')
    scale = bw / max(total, used)
    for label, v, role, is_spare in segs:
        fill, stroke, fg = ("#e6f4ea", GREEN, "#202124") if is_spare else ROLE[role]
        sw_ = v * scale
        dash = ' stroke-dasharray="10 6"' if is_spare else ""
        out.append(f'<rect x="{x:.1f}" y="{by}" width="{sw_:.1f}" height="{bh}" fill="{fill}" stroke="{stroke}" stroke-width="2.2"{dash}/>'
                   f'<text x="{x+sw_/2:.1f}" y="{by+bh/2+12}" text-anchor="middle" font-family="{FONT}" font-size="34" '
                   f'font-weight="800" fill="{fg}">{v:g}</text>')
        narrow = len(label) * fs * 0.56 > sw_ - 10
        row = (row + 1) % 2 if narrow else 0
        ly = by - 20 - row * 42
        if row:
            out.append(f'<line x1="{x+sw_/2:.1f}" y1="{ly+8}" x2="{x+sw_/2:.1f}" y2="{by}" stroke="{GREY}" stroke-width="1.6"/>')
        out.append(f'<text x="{x+sw_/2:.1f}" y="{ly}" text-anchor="middle" font-family="{FONT}" font-size="{fs}" font-weight="700" '
                   f'fill="{GREEN if is_spare else INK}" paint-order="stroke" stroke="#ffffff" stroke-width="5">{esc(label)}</text>')
        x += sw_
    verdict, colour = (f"{used:g} used + {rest:g} {spare} = {total:g} {unit} budget", INK) if rest >= 0 else \
                      (f"{used:g} {unit} needed against a {total:g} {unit} budget: over by {-rest:g}", RED)
    ty, tx = by + bh + 30, x0 + total * scale
    out.append(f'<line x1="{x0}" y1="{ty}" x2="{tx:.1f}" y2="{ty}" stroke="{colour}" stroke-width="3"/>'
               f'<line x1="{x0}" y1="{ty-11}" x2="{x0}" y2="{ty+11}" stroke="{colour}" stroke-width="3"/>'
               f'<line x1="{tx:.1f}" y1="{ty-11}" x2="{tx:.1f}" y2="{ty+11}" stroke="{colour}" stroke-width="3"/>'
               f'<text x="{x0}" y="{ty+50}" font-family="{FONT}" font-size="29" font-weight="700" fill="{ink(colour)}">{esc(verdict)}</text>')
    svg = (f'<svg xmlns="http://www.w3.org/2000/svg" class="budget" viewBox="0 0 {w} {h}" width="{w}" height="{h}">'
           f'<rect width="{w}" height="{h}" fill="#ffffff"/>{"".join(out)}</svg>')
    pathlib.Path(path).write_text(svg, encoding="utf-8")
    return path
