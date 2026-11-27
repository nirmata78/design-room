#!/usr/bin/env python3
"""Main CLI for the c4-structurizr skill (Mode A: single master SVG + .steps.json):
  1. Validates Structurizr DSL inside the warm Docker container (c4_runtime.sh)
  2. Batch-exports all views to raw SVG
  3. Normalizes every view with svg_normalizer.py (DESIGN-TOKENS.md + 1080p legibility gate)
  4. Optionally renders @2x PNG previews via Playwright Chromium
  5. Emits structured JSON report; exits 0 (OK), 2 (DSL error), or 3 (legibility/token gate fail)
"""
from __future__ import annotations

import argparse
import json
import os
import pathlib
import re
import shutil
import subprocess
import sys
from typing import Any, Literal

from pydantic import BaseModel, Field

SCRIPT_DIR = pathlib.Path(__file__).resolve().parent
SKILL_DIR = SCRIPT_DIR.parent
sys.path.insert(0, str(SCRIPT_DIR))

from svg_normalizer import ViewMeta, normalize_svg  # noqa: E402


class ViewSpec(BaseModel):
    slot: Literal["full", "composite", "split"] = "full"
    steps: list[Any] = Field(default_factory=list)
    canon: str = ""
    full: bool = True


class WorkspaceSpec(BaseModel):
    views: dict[str, ViewSpec] = Field(default_factory=dict)


def _extract_dsl_aliases(dsl_text: str) -> dict[str, str]:
    """Map element display title -> DSL alias from workspace.dsl for accurate data-k tagging."""
    mapping: dict[str, str] = {}
    pat = re.compile(
        r'^\s*([A-Za-z_]\w*)\s*=\s*(?:person|softwareSystem|container|component)\s+"([^"]+)"',
        re.M,
    )
    for m in pat.finditer(dsl_text):
        alias, title = m.group(1), m.group(2)
        mapping[title.lower()] = alias
    return mapping


def _container_path(host_path: pathlib.Path, workspace_root: pathlib.Path) -> str:
    rel = host_path.resolve().relative_to(workspace_root.resolve())
    return "/workspace/" + rel.as_posix()


def _render_pngs(svg_paths: list[pathlib.Path], width: int = 1920) -> None:
    from playwright.sync_api import sync_playwright

    fonts_dir = SKILL_DIR / "resources" / "fonts"
    inter_uri = (fonts_dir / "Inter-Variable.ttf").resolve().as_uri()
    font_css = f"@font-face {{ font-family: 'Inter'; src: url('{inter_uri}') format('truetype'); font-weight: 100 900; }}"

    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": width, "height": 1080}, device_scale_factor=2)
        for sp in svg_paths:
            svg_txt = sp.read_text(encoding="utf-8")
            html_doc = f"""<!doctype html><html><head><style>
            {font_css}
            html, body {{ margin:0; padding:0; background:#fff; width:100%; height:100%; display:flex; align-items:center; justify-content:center; }}
            svg {{ max-width:100%; max-height:100%; width:100%; height:auto; }}
            </style></head><body>{svg_txt}</body></html>"""
            page.set_content(html_doc, wait_until="load")
            page.evaluate("document.fonts.ready.then(() => true)")
            page.locator("svg").first.screenshot(path=str(sp.with_suffix(".png")))
        browser.close()


def run_render(
    dsl_path: pathlib.Path,
    out_dir: pathlib.Path,
    spec_path: pathlib.Path | None = None,
    *,
    export_png: bool = False,
    workspace_root: pathlib.Path | None = None,
) -> tuple[int, list[ViewMeta]]:
    runtime = SCRIPT_DIR / "c4_runtime.sh"
    dsl_path = dsl_path.resolve()
    out_dir = out_dir.resolve()
    out_dir.mkdir(parents=True, exist_ok=True)

    if workspace_root is None:
        git_root = subprocess.run(
            ["git", "rev-parse", "--show-toplevel"],
            cwd=str(dsl_path.parent),
            capture_output=True,
            text=True,
        )
        workspace_root = pathlib.Path(git_root.stdout.strip()) if git_root.returncode == 0 else dsl_path.parent
    workspace_root = workspace_root.resolve()

    env = os.environ.copy()
    env["C4_WORKSPACE_ROOT"] = str(workspace_root)

    subprocess.run([str(runtime), "ensure"], env=env, check=True, stdout=subprocess.DEVNULL)

    spec = WorkspaceSpec()
    if spec_path and spec_path.exists():
        spec = WorkspaceSpec.model_validate_json(spec_path.read_text(encoding="utf-8"))

    alias_by_title = _extract_dsl_aliases(dsl_path.read_text(encoding="utf-8"))

    tmp_stage = workspace_root / f".c4-export-{os.getpid()}"
    raw_dir = tmp_stage / "raw"
    raw_dir.mkdir(parents=True, exist_ok=True)

    try:
        c_dsl = _container_path(dsl_path, workspace_root)
        val = subprocess.run(
            [str(runtime), "exec", "validate", "-w", c_dsl],
            env=env,
            capture_output=True,
            text=True,
        )
        if val.returncode != 0:
            print(json.dumps({"status": "dsl_error", "stderr": val.stderr, "stdout": val.stdout}, indent=2), file=sys.stderr)
            return 2, []

        c_raw = _container_path(raw_dir, workspace_root)
        exp = subprocess.run(
            [str(runtime), "exec", "export", "-w", c_dsl, "-f", "svg", "-o", c_raw],
            env=env,
            capture_output=True,
            text=True,
        )
        if exp.returncode != 0:
            print(json.dumps({"status": "export_error", "stderr": exp.stderr, "stdout": exp.stdout}, indent=2), file=sys.stderr)
            return 2, []

        metas: list[ViewMeta] = []
        out_svgs: list[pathlib.Path] = []
        for raw_svg in sorted(raw_dir.glob("*.svg")):
            if raw_svg.stem.endswith("-key"):
                continue
            key = raw_svg.stem
            vspec = spec.views.get(key, ViewSpec())
            dest = out_dir / f"{key}.svg"
            meta = normalize_svg(
                raw_svg,
                dest,
                key=key,
                slot=vspec.slot,
                alias_by_title=alias_by_title,
                reveal_steps=vspec.steps or None,
                canon=vspec.canon,
                full=vspec.full,
            )
            metas.append(meta)
            out_svgs.append(dest)

        if export_png and out_svgs:
            _render_pngs(out_svgs)

    finally:
        shutil.rmtree(tmp_stage, ignore_errors=True)

    failures = [m for m in metas if (not m.legibility_ok) or m.forbidden_fonts_found]
    summary = {
        "status": "ok" if not failures else "gate_failed",
        "views_rendered": len(metas),
        "failures": [
            {
                "key": m.key,
                "min_rendered_1080p_px": m.min_rendered_1080p_px,
                "forbidden_fonts": m.forbidden_fonts_found,
                "remedy": "Switch autoLayout lr <-> tb, reduce nodes per view, or shorten descriptions.",
            }
            for m in failures
        ],
        "views": [m.model_dump() for m in metas],
    }
    print(json.dumps(summary, indent=2))
    return (0 if not failures else 3), metas


def main() -> None:
    ap = argparse.ArgumentParser(description="Containerized Structurizr C4 renderer + 1080p normalizer (Mode A)")
    ap.add_argument("--dsl", type=pathlib.Path, required=True, help="Path to Structurizr workspace.dsl")
    ap.add_argument("--spec", type=pathlib.Path, help="Optional views.json spec")
    ap.add_argument("--out", type=pathlib.Path, required=True, help="Output directory for normalized SVGs/PNGs")
    ap.add_argument("--png", action="store_true", help="Also render @2x PNG previews via Playwright")
    args = ap.parse_args()

    rc, _ = run_render(args.dsl, args.out, args.spec, export_png=args.png)
    sys.exit(rc)


if __name__ == "__main__":
    main()
