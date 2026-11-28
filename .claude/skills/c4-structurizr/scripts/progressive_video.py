#!/usr/bin/env python3
"""Render progressive 1920x1080@30fps C4 videos using Mode A (Master SVG + Cross-Dissolve).

Mode A locks layout in a single normalized .svg, hides unrevealed data-k groups via CSS
(visibility:hidden by default, or optional --ghost opacity), and cross-dissolves steps (0.35s)
via FFmpeg. Zero layout jitter, minimal Playwright captures (1 PNG per narration beat).
"""
from __future__ import annotations

import argparse
import json
import pathlib
import subprocess
import tempfile

from playwright.sync_api import sync_playwright

SCRIPT_DIR = pathlib.Path(__file__).resolve().parent
SKILL_DIR = SCRIPT_DIR.parent
FONTS_DIR = SKILL_DIR / "resources" / "fonts"


def _font_face_css() -> str:
    inter = (FONTS_DIR / "Inter-Variable.ttf").resolve().as_uri()
    jakarta = (FONTS_DIR / "PlusJakartaSans-Variable.ttf").resolve().as_uri()
    return f"""
    @font-face {{ font-family: 'Inter'; src: url('{inter}') format('truetype'); font-weight: 100 900; }}
    @font-face {{ font-family: 'Plus Jakarta Sans'; src: url('{jakarta}') format('truetype'); font-weight: 100 900; }}
    """


def _stage_html(svg_markup: str, kicker: str, title: str, caption: str, step_badge: str, extra_css: str = "") -> str:
    return f"""<!doctype html>
<html><head><meta charset="utf-8"><style>
{_font_face_css()}
* {{ box-sizing: border-box; margin: 0; padding: 0; }}
html, body {{
    width: 1920px; height: 1080px; overflow: hidden; background: #FFFFFF;
    font-family: 'Inter', Roboto, sans-serif; color: #202124;
}}
.slide {{
    width: 1920px; height: 1080px; padding: 54px 108px 54px;
    display: flex; flex-direction: column;
}}
.kicker {{
    font-size: 20px; font-weight: 700; letter-spacing: 2.2px; text-transform: uppercase;
    color: #1967D2; margin-bottom: 10px;
}}
h1 {{
    font-family: 'Plus Jakarta Sans', 'Inter', sans-serif;
    font-size: 46px; font-weight: 700; letter-spacing: -0.4px; color: #202124;
    padding-bottom: 14px; border-bottom: 2px solid #DADCE0; margin-bottom: 18px;
}}
.canvas {{
    flex: 1; min-height: 0; display: flex; align-items: center; justify-content: center;
}}
.canvas svg {{
    width: 100%; height: 100%; max-width: 1704px; max-height: 780px;
}}
.footer {{
    display: flex; justify-content: space-between; align-items: center;
    padding-top: 12px; font-size: 22px; color: #5F6368;
}}
.badge {{
    font-weight: 600; color: #1967D2; background: #E8F0FE;
    padding: 4px 14px; border-radius: 999px; font-size: 20px;
}}
{extra_css}
</style></head>
<body>
<div class="slide">
  <div class="kicker">{kicker}</div>
  <h1>{title}</h1>
  <div class="canvas">{svg_markup}</div>
  <div class="footer">
    <span>{caption}</span>
    <span class="badge">{step_badge}</span>
  </div>
</div>
</body></html>"""


def _stitch_crossfade(pngs: list[pathlib.Path], out_mp4: pathlib.Path, hold_s: float = 2.6, fade_s: float = 0.35) -> None:
    out_mp4.parent.mkdir(parents=True, exist_ok=True)
    if len(pngs) == 1:
        cmd = [
            "ffmpeg", "-y", "-loop", "1", "-t", f"{hold_s:.2f}", "-i", str(pngs[0]),
            "-vf", "scale=1920:1080,fps=30,format=yuv420p", "-c:v", "libx264", "-crf", "18", "-pix_fmt", "yuv420p",
            str(out_mp4),
        ]
        subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return

    cmd = ["ffmpeg", "-y"]
    for i, p in enumerate(pngs):
        dur = hold_s + (0.9 if i == len(pngs) - 1 else 0.0)
        cmd += ["-loop", "1", "-t", f"{dur:.2f}", "-i", str(p)]

    filters = [f"[{i}:v]fps=30,scale=1920:1080,format=yuv420p[v{i}]" for i in range(len(pngs))]
    cur = "v0"
    offset = hold_s - fade_s
    for i in range(1, len(pngs)):
        nxt = f"xf{i}"
        filters.append(f"[{cur}][v{i}]xfade=transition=fade:duration={fade_s:.2f}:offset={offset:.2f}[{nxt}]")
        cur = nxt
        offset += hold_s - fade_s

    cmd += [
        "-filter_complex", ";".join(filters),
        "-map", f"[{cur}]",
        "-c:v", "libx264", "-crf", "18", "-pix_fmt", "yuv420p", "-movflags", "+faststart",
        str(out_mp4),
    ]
    subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


def render_progressive_video(
    svg_path: pathlib.Path,
    out_mp4: pathlib.Path,
    *,
    title: str,
    caption: str = "",
    kicker: str = "C4 ARCHITECTURE",
    ghost_opacity: float = 0.0,
    target_duration: float = 12.0,
    fade_s: float = 0.35,
) -> None:
    svg_txt = svg_path.read_text(encoding="utf-8")
    steps: list[list[str]] = json.loads(svg_path.with_suffix(".steps.json").read_text(encoding="utf-8"))
    all_keys = [k for st in steps for k in st]
    hold_s = max(2.2, min(3.4, target_duration / max(len(steps), 1)))

    with tempfile.TemporaryDirectory() as td:
        tdir = pathlib.Path(td)
        pngs: list[pathlib.Path] = []
        with sync_playwright() as p:
            browser = p.chromium.launch()
            page = browser.new_page(viewport={"width": 1920, "height": 1080})
            revealed: set[str] = set()
            for idx, st in enumerate(steps, 1):
                revealed.update(st)
                hidden = [k for k in all_keys if k not in revealed]
                if hidden:
                    sel = ",".join(f'[data-k="{k}"]' for k in hidden)
                    css = f"{sel} {{ opacity: {ghost_opacity}; }}" if ghost_opacity > 0 else f"{sel} {{ visibility: hidden; }}"
                else:
                    css = ""
                html = _stage_html(svg_txt, kicker, title, caption, f"Step {idx}/{len(steps)}", css)
                page.set_content(html, wait_until="load")
                page.evaluate("document.fonts.ready.then(() => true)")
                fp = tdir / f"step_{idx:02d}.png"
                page.screenshot(path=str(fp))
                pngs.append(fp)
            browser.close()
        _stitch_crossfade(pngs, out_mp4, hold_s=hold_s, fade_s=fade_s)


def main() -> None:
    ap = argparse.ArgumentParser(description="Render progressive 1080p C4 video (Mode A: Master SVG + Cross-Dissolve)")
    ap.add_argument("--svg", type=pathlib.Path, required=True, help="Normalized master .svg path (with sibling .steps.json)")
    ap.add_argument("--out", type=pathlib.Path, required=True, help="Output .mp4 path")
    ap.add_argument("--title", required=True, help="Slide title")
    ap.add_argument("--kicker", default="C4 ARCHITECTURE", help="Top kicker label")
    ap.add_argument("--caption", default="", help="Bottom caption")
    ap.add_argument("--duration", type=float, default=12.0, help="Target total duration in seconds")
    ap.add_argument("--ghost", type=float, default=0.0, help="Optional opacity for unrevealed elements (default 0.0 = hidden)")
    args = ap.parse_args()

    render_progressive_video(
        args.svg,
        args.out,
        title=args.title,
        caption=args.caption,
        kicker=args.kicker,
        ghost_opacity=args.ghost,
        target_duration=args.duration,
    )
    print(f"Wrote {args.out}")


if __name__ == "__main__":
    main()
