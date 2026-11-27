#!/usr/bin/env python3
"""Render 10-15s 1920x1080@30fps progressive C4 videos in Modes A, B, and C, plus 2x2 comparison reels.

Modes:
  A: Master SVG + CSS visibility:hidden (or --ghost opacity) + FFmpeg 0.35s cross-dissolve
  B: Structurizr native -animation true SVG sequence (locked viewBox) + FFmpeg 0.35s cross-dissolve
  C: Directional Vector "Live Draw" — 30fps card ease-in + stroke-dashoffset edge drawing from source to target
"""
from __future__ import annotations

import argparse
import json
import pathlib
import shutil
import subprocess
import tempfile
from typing import Literal

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


def render_mode_a(
    svg_path: pathlib.Path,
    out_mp4: pathlib.Path,
    *,
    title: str,
    caption: str,
    kicker: str = "C4 · MODE A (MASTER SVG CROSS-DISSOLVE)",
    ghost_opacity: float = 0.0,
    target_duration: float = 12.0,
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
                html = _stage_html(svg_txt, kicker, title, caption, f"Mode A · Step {idx}/{len(steps)}", css)
                page.set_content(html, wait_until="load")
                page.evaluate("document.fonts.ready.then(() => true)")
                fp = tdir / f"step_{idx:02d}.png"
                page.screenshot(path=str(fp))
                pngs.append(fp)
            browser.close()
        _stitch_crossfade(pngs, out_mp4, hold_s=hold_s, fade_s=0.35)


def render_mode_b(
    anim_dir: pathlib.Path,
    out_mp4: pathlib.Path,
    *,
    title: str,
    caption: str,
    kicker: str = "C4 · MODE B (STRUCTURIZR NATIVE ANIMATION)",
    target_duration: float = 12.0,
) -> None:
    frames = sorted(anim_dir.glob("*.svg"))
    if not frames:
        raise FileNotFoundError(f"No native animation SVGs found in {anim_dir}")
    hold_s = max(2.2, min(3.4, target_duration / len(frames)))

    with tempfile.TemporaryDirectory() as td:
        tdir = pathlib.Path(td)
        pngs: list[pathlib.Path] = []
        with sync_playwright() as p:
            browser = p.chromium.launch()
            page = browser.new_page(viewport={"width": 1920, "height": 1080})
            for idx, sf in enumerate(frames, 1):
                html = _stage_html(sf.read_text(encoding="utf-8"), kicker, title, caption, f"Mode B · Frame {idx}/{len(frames)}")
                page.set_content(html, wait_until="load")
                page.evaluate("document.fonts.ready.then(() => true)")
                fp = tdir / f"frame_{idx:02d}.png"
                page.screenshot(path=str(fp))
                pngs.append(fp)
            browser.close()
        _stitch_crossfade(pngs, out_mp4, hold_s=hold_s, fade_s=0.35)


def render_mode_c(
    svg_path: pathlib.Path,
    out_mp4: pathlib.Path,
    *,
    title: str,
    caption: str,
    kicker: str = "C4 · MODE C (DIRECTIONAL VECTOR LIVE-DRAW)",
    target_duration: float = 12.0,
) -> None:
    svg_txt = svg_path.read_text(encoding="utf-8")
    steps: list[list[str]] = json.loads(svg_path.with_suffix(".steps.json").read_text(encoding="utf-8"))
    n_steps = max(len(steps), 1)
    anim_frames = 18  # 0.60s at 30fps per reveal beat
    hold_s = max(1.6, min(2.8, (target_duration - n_steps * (anim_frames / 30.0)) / n_steps))

    with tempfile.TemporaryDirectory() as td:
        tdir = pathlib.Path(td)
        concat_lines: list[str] = []
        frame_no = 0
        with sync_playwright() as p:
            browser = p.chromium.launch()
            page = browser.new_page(viewport={"width": 1920, "height": 1080})
            html = _stage_html(svg_txt, kicker, title, caption, f"Mode C · 0/{n_steps}")
            page.set_content(html, wait_until="load")
            page.evaluate("document.fonts.ready.then(() => true)")

            # Precompute exact path lengths for every edge <path>
            page.evaluate("""() => {
                document.querySelectorAll('[data-role="edge"] path').forEach(p => {
                    try {
                        const L = p.getTotalLength();
                        if (L > 0) p.dataset.plen = String(L);
                    } catch (e) {}
                });
            }""")

            prev_keys: list[str] = []
            for s_idx, cur_keys in enumerate(steps, 1):
                future_keys = [k for st in steps[s_idx:] for k in st]
                page.evaluate(
                    "(txt) => { const b = document.querySelector('.badge'); if (b) b.textContent = txt; }",
                    f"Mode C · Step {s_idx}/{n_steps}",
                )
                for f in range(anim_frames + 1):
                    prog = f / anim_frames
                    page.evaluate(
                        """([prevK, curK, futK, p]) => {
                            const ease = x => 1 - Math.pow(1 - Math.max(0, Math.min(1, x)), 3);
                            const setVis = (k, op) => {
                                const el = document.querySelector(`[data-k="${k}"]`);
                                if (!el) return;
                                el.style.opacity = String(op);
                                el.style.visibility = op <= 0.001 ? 'hidden' : 'visible';
                            };
                            prevK.forEach(k => {
                                setVis(k, 1);
                                const el = document.querySelector(`[data-k="${k}"]`);
                                if (el) {
                                    el.querySelectorAll('path[data-plen]').forEach(pt => {
                                        pt.style.strokeDashoffset = '0';
                                    });
                                    el.querySelectorAll('text, rect').forEach(ch => { ch.style.opacity = '1'; });
                                }
                            });
                            futK.forEach(k => setVis(k, 0));

                            curK.forEach(k => {
                                const el = document.querySelector(`[data-k="${k}"]`);
                                if (!el) return;
                                const role = el.getAttribute('data-role');
                                if (role === 'node') {
                                    const np = ease(p / 0.50);
                                    setVis(k, np);
                                } else {
                                    // Directional edge draw from source to target
                                    const ep = ease((p - 0.22) / 0.62);
                                    setVis(k, ep > 0.01 ? 1 : 0);
                                    el.querySelectorAll('path[data-plen]').forEach(pt => {
                                        const L = parseFloat(pt.dataset.plen || '0');
                                        if (L > 0) {
                                            if (!pt.dataset.origDash) pt.dataset.origDash = pt.getAttribute('stroke-dasharray') || '';
                                            if (ep >= 0.99) {
                                                pt.style.strokeDasharray = pt.dataset.origDash;
                                                pt.style.strokeDashoffset = '0';
                                            } else {
                                                pt.style.strokeDasharray = String(L);
                                                pt.style.strokeDashoffset = String(L * (1 - ep));
                                            }
                                        }
                                    });
                                    const lp = ease((p - 0.68) / 0.32);
                                    el.querySelectorAll('text, rect').forEach(ch => { ch.style.opacity = String(lp); });
                                }
                            });
                        }""",
                        [prev_keys, cur_keys, future_keys, prog],
                    )
                    fp = tdir / f"f_{frame_no:04d}.png"
                    page.screenshot(path=str(fp))
                    dur = (hold_s + (0.8 if s_idx == n_steps else 0.0)) if f == anim_frames else (1.0 / 30.0)
                    concat_lines.append(f"file '{fp.name}'\nduration {dur:.4f}\n")
                    frame_no += 1
                prev_keys.extend(cur_keys)
            browser.close()

        # FFmpeg concat demuxer requires repeating the last file once
        concat_lines.append(f"file 'f_{frame_no - 1:04d}.png'\n")
        list_file = tdir / "frames.txt"
        list_file.write_text("".join(concat_lines), encoding="utf-8")
        out_mp4.parent.mkdir(parents=True, exist_ok=True)
        subprocess.run(
            [
                "ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", str(list_file),
                "-vf", "fps=30,scale=1920:1080,format=yuv420p",
                "-c:v", "libx264", "-crf", "18", "-pix_fmt", "yuv420p", "-movflags", "+faststart",
                str(out_mp4),
            ],
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )


def build_comparison_grid(mp4_a: pathlib.Path, mp4_b: pathlib.Path, mp4_c: pathlib.Path, static_png: pathlib.Path, out_mp4: pathlib.Path) -> None:
    """Create a 1920x1080 2x2 side-by-side comparison MP4 (A | B / C | Static Reference)."""
    out_mp4.parent.mkdir(parents=True, exist_ok=True)
    # Match duration to the longest of A/B/C
    durs = []
    for p in (mp4_a, mp4_b, mp4_c):
        res = subprocess.run(
            ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(p)],
            capture_output=True, text=True, check=True,
        )
        durs.append(float(res.stdout.strip()))
    max_d = max(durs)

    cmd = [
        "ffmpeg", "-y",
        "-i", str(mp4_a),
        "-i", str(mp4_b),
        "-i", str(mp4_c),
        "-loop", "1", "-t", f"{max_d:.2f}", "-i", str(static_png),
        "-filter_complex",
        (
            "[0:v]scale=960:540,tpad=stop_mode=clone:stop_duration=5[tl];"
            "[1:v]scale=960:540,tpad=stop_mode=clone:stop_duration=5[tr];"
            "[2:v]scale=960:540,tpad=stop_mode=clone:stop_duration=5[bl];"
            "[3:v]scale=960:540:force_original_aspect_ratio=decrease,pad=960:540:(ow-iw)/2:(oh-ih)/2:white[br];"
            "[tl][tr][bl][br]xstack=inputs=4:layout=0_0|960_0|0_540|960_540[v]"
        ),
        "-map", "[v]", "-t", f"{max_d:.2f}",
        "-c:v", "libx264", "-crf", "18", "-pix_fmt", "yuv420p", "-movflags", "+faststart",
        str(out_mp4),
    ]
    subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


def main() -> None:
    ap = argparse.ArgumentParser(description="Render 10-15s progressive C4 videos (Modes A, B, C)")
    ap.add_argument("--svg", type=pathlib.Path, required=True, help="Normalized master .svg path")
    ap.add_argument("--mode", choices=("A", "B", "C"), required=True)
    ap.add_argument("--anim-dir", type=pathlib.Path, help="Directory of native animation SVGs (required for Mode B)")
    ap.add_argument("--out", type=pathlib.Path, required=True, help="Output .mp4 path")
    ap.add_argument("--title", required=True)
    ap.add_argument("--caption", default="")
    ap.add_argument("--duration", type=float, default=12.0)
    ap.add_argument("--ghost", type=float, default=0.0, help="Ghost opacity for unrevealed elements in Mode A")
    args = ap.parse_args()

    if args.mode == "A":
        render_mode_a(args.svg, args.out, title=args.title, caption=args.caption, ghost_opacity=args.ghost, target_duration=args.duration)
    elif args.mode == "B":
        if not args.anim_dir:
            ap.error("--anim-dir is required for Mode B")
        render_mode_b(args.anim_dir, args.out, title=args.title, caption=args.caption, target_duration=args.duration)
    else:
        render_mode_c(args.svg, args.out, title=args.title, caption=args.caption, target_duration=args.duration)
    print(f"Wrote {args.out}")


if __name__ == "__main__":
    main()
