#!/usr/bin/env python3
"""Run the C3-03 Progressive Video Bake-Off: 4 C4 diagram types x Modes A, B, C + 2x2 comparisons."""
from __future__ import annotations

import pathlib
import subprocess
import sys

HERE = pathlib.Path(__file__).resolve().parent
SCRIPTS = HERE.parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS))

from progressive_video import build_comparison_grid, render_mode_a, render_mode_b, render_mode_c  # noqa: E402
from render_c4 import run_render  # noqa: E402

VIEWS = [
    ("01-system-context", "L1 · System Context", "Customer & Merchant -> Loan Servicing -> Card & Bank Rails", 11.0),
    ("02-container-view", "L2 · Container Architecture", "Sync HTTPS -> Atomic SQL Outbox -> Async Event -> External Rails", 14.0),
    ("03-component-view", "L3 · Dispatcher Component View", "Inside Rail Dispatcher: SKIP LOCKED Poller, Day Plan, Token Bucket", 12.0),
    ("04-version-delta",  "Evolution · V1 to V2 Delta", "Carried V1 boxes + NEW amber-badged Servicing DB & Dispatcher", 11.0),
]


def _probe(mp4: pathlib.Path) -> str:
    res = subprocess.run(
        ["ffprobe", "-v", "error", "-select_streams", "v:0",
         "-show_entries", "stream=width,height:format=duration",
         "-of", "default=noprint_wrappers=1:nokey=1", str(mp4)],
        capture_output=True, text=True, check=True,
    )
    parts = res.stdout.strip().splitlines()
    return f"{parts[0]}x{parts[1]} ({float(parts[2]):.1f}s)" if len(parts) >= 3 else res.stdout.strip()


def main() -> None:
    out_svg = HERE / "out" / "svg"
    out_mp4 = HERE / "out" / "mp4"
    out_mp4.mkdir(parents=True, exist_ok=True)

    rc, _ = run_render(
        HERE / "workspace.dsl",
        out_svg,
        HERE / "views.json",
        export_png=True,
        export_animation=True,
    )
    if rc != 0:
        raise SystemExit(f"render_c4 failed with exit code {rc}")

    print("\n=== Generating 12 Bake-Off MP4s + 4 Side-by-Side 2x2 Comparisons ===")
    for key, title, caption, dur in VIEWS:
        svg = out_svg / f"{key}.svg"
        png = out_svg / f"{key}.png"
        anim = out_svg / "anim" / key

        ma = out_mp4 / f"{key}_modeA_crossfade.mp4"
        mb = out_mp4 / f"{key}_modeB_native.mp4"
        mc = out_mp4 / f"{key}_modeC_livedraw.mp4"
        mg = out_mp4 / f"{key}_compare_2x2.mp4"

        render_mode_a(svg, ma, title=title, caption=caption, target_duration=dur)
        render_mode_b(anim, mb, title=title, caption=caption, target_duration=dur)
        render_mode_c(svg, mc, title=title, caption=caption, target_duration=dur)
        build_comparison_grid(ma, mb, mc, png, mg)
        print(f"  {key}: A={_probe(ma)} | B={_probe(mb)} | C={_probe(mc)} | 2x2={_probe(mg)}")


if __name__ == "__main__":
    main()
