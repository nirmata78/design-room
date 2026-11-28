#!/usr/bin/env python3
"""Turn slide sources into 1920x1080 PNG frames (--width 1280 for 720p) for build_video.py.

    render_slides.py --html slides.html --prefix v --out FRAMES_DIR [--svg-dir DIR] [--css-dir DIR]   # HTML 16:9 slides (element screenshots)
    render_slides.py --pdf deck.pdf --prefix deck --out FRAMES_DIR                    # an existing 16:9 PDF
    render_slides.py --image fig.svg|fig.png --name NAME --out FRAMES_DIR [--title "…"]  # one diagram, letterboxed

HTML slides use the design-room pdf-kit (style.css, <!--SVG:name--> inlining) and must set
@page { size: 13.333in 7.5in } — copy templates/slides.html. Frames are named PREFIX-1.png, PREFIX-2.png …
(PDF pages keep pdftoppm's zero padding, e.g. deck-01.png).
Run with the pdf-kit venv for --html:  <repo>/pdf-kit/.venv/bin/python render_slides.py …
"""
import os as _os, pathlib as _pl
_os.environ.setdefault("PANGOCAIRO_BACKEND", "fc")   # rsvg-convert: use fontconfig so the bundled Google Fonts resolve
import sys as _sys; _sys.path.insert(0, str(_pl.Path(__file__).resolve().parent)); import paths as _paths
_os.environ.setdefault("FONTCONFIG_FILE", str(_paths.FONTS_CONF))
import argparse, html, pathlib, subprocess, sys

KIT = _paths.PDFKIT

WIDTH = 1920                                   # 1080p frames; --width 1280 for the old 720p size

def from_pdf(pdf, prefix, out):
    subprocess.run(["pdftoppm", "-png", "-scale-to-x", str(WIDTH), "-scale-to-y", str(WIDTH * 9 // 16), str(pdf), str(out / prefix)],
                   check=True, stderr=subprocess.DEVNULL)

def from_html(src, prefix, out, svg_dir, css_dir=None):
    """Screenshot every .slide element straight to a 1920x1080 PNG (2026-11-28, issue #5): no slides PDF, no pdftoppm.
    The page is laid out at 1280x720 CSS px (13.333 in x 7.5 in) and captured at device scale 1.5. A frame is named by its
    slide's data-frame attribute (written by dsl.write, e.g. v-017), else PREFIX-<n> with the dsl's zero padding.
    The built page lives in a temporary directory and is removed; nothing but PNGs is left in OUT."""
    import tempfile
    sys.path.insert(0, str(KIT))
    from build import inline_svgs, inline_css
    from playwright.sync_api import sync_playwright
    page = inline_css(inline_svgs(src.read_text(encoding="utf-8"), svg_dir or src.parent / "svg"), css_dir or src.parent)
    scale = WIDTH / 1280
    with tempfile.TemporaryDirectory(prefix="slides-") as tmp:
        built = pathlib.Path(tmp) / "built.html"; built.write_text(page, encoding="utf-8")
        with sync_playwright() as p:
            b = p.chromium.launch()
            pg = b.new_page(viewport={"width": 1280, "height": 720}, device_scale_factor=scale)
            pg.emulate_media(media="print")
            pg.goto(built.as_uri(), wait_until="load"); pg.evaluate("document.fonts.ready.then(() => true)")
            # layout gate (2026-11-22): reference-solution decks (slides carry data-n) are measured before any frame is drawn —
            # overflow, overlapping text, text under the 1080p minimum, over-long code. LAYOUT_CHECK=warn reports only; =off skips.
            mode = _os.environ.get("LAYOUT_CHECK", "fail")
            if mode != "off" and 'data-n="' in page:
                import check_layout
                report = src.with_name("layout-report.txt")
                fails, warns, lines = check_layout.check(pg, svg_dir or src.parent / "svg", report=report)
                print(lines[-1], file=sys.stderr)
                if fails and mode != "warn":
                    b.close()
                    raise SystemExit(f"render_slides: layout check failed ({fails} failures) — no frames rendered; see {report}")
            slides = pg.locator(".slide")
            n = slides.count(); w = max(2, len(str(n)))
            for i in range(n):
                el = slides.nth(i)
                name = el.get_attribute("data-frame") or f"{prefix}-{i + 1:0{w}d}"
                el.screenshot(path=str(out / f"{name}.png"), animations="disabled")
            b.close()
    return out

def from_image(img, name, out, title):
    """Letterbox one diagram onto a white 1280x720 frame, optional title strip."""
    tmp = out / f".{name}.png"
    if img.suffix == ".svg":
        subprocess.run(["rsvg-convert", "-w", "2400", "-b", "white", "-o", str(tmp), str(img)], check=True)
    else:
        tmp = img
    W, H, k = WIDTH, WIDTH * 9 // 16, WIDTH / 1280
    top = int((64 if title else 16) * k); m = int(16 * k)
    vf = (f"scale={W-2*m}:{H-m-top}:force_original_aspect_ratio=decrease:flags=lanczos,"
          f"pad={W}:{H}:(ow-iw)/2:{top}+({H-m-top}-ih)/2:color=white")
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(tmp), "-vf", vf, str(out / f"{name}.png")], check=True)
    if title:
        svg = (f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{60*k}"><rect width="{W}" height="{60*k}" fill="white"/>'
               f'<text x="{40*k}" y="{42*k}" font-family="Inter, Helvetica" font-size="{28*k}" font-weight="700" fill="#202124">'
               f'{html.escape(title)}</text><rect x="{40*k}" y="{56*k}" width="{W-80*k}" height="{2*k}" fill="#202124"/></svg>')
        t = out / f".{name}-title.svg"; t.write_text(svg)
        tp = out / f".{name}-title.png"
        subprocess.run(["rsvg-convert", "-o", str(tp), str(t)], check=True)
        f = out / f"{name}.png"
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(f), "-i", str(tp), "-filter_complex", "overlay=0:0",
                        str(out / f".{name}-x.png")], check=True)
        (out / f".{name}-x.png").replace(f)
    for junk in out.glob(f".{name}*"):
        junk.unlink()

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--html"); g.add_argument("--pdf"); g.add_argument("--image")
    ap.add_argument("--prefix", default="s"); ap.add_argument("--name"); ap.add_argument("--title")
    ap.add_argument("--svg-dir"); ap.add_argument("--css-dir"); ap.add_argument("--out", required=True)
    ap.add_argument("--width", type=int, default=1920)
    a = ap.parse_args(); WIDTH = a.width; out = pathlib.Path(a.out); out.mkdir(parents=True, exist_ok=True)
    if a.pdf: from_pdf(pathlib.Path(a.pdf), a.prefix, out)
    elif a.html: print(from_html(pathlib.Path(a.html).resolve(), a.prefix, out, pathlib.Path(a.svg_dir) if a.svg_dir else None, pathlib.Path(a.css_dir) if a.css_dir else None))
    else: from_image(pathlib.Path(a.image), a.name or pathlib.Path(a.image).stem, out, a.title)
    print(sorted(p.name for p in out.glob("*.png")))
