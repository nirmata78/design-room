#!/usr/bin/env python3
"""Render a PDF's pages to PNG so you can review the layout, and flag weak pages.

    python check.py my-guide.pdf            # → my-guide_pages/  (p-01.png …, sheet.png, pair-01.png …)
    python check.py my-guide.pdf --dpi 120

Outputs
  p-NN.png     every page at --dpi (default 100)
  pair-NN.png  two pages side by side, the size that is comfortable to inspect
  sheet.png    a contact sheet of all pages, to spot orphans and half-empty pages at a glance
It also prints how much of each page's height is used and warns about pages that are
mostly empty (usually a heading or a box that got pushed onto its own page).

Setup (once):  pip install pypdfium2 pillow
"""
import argparse
import pathlib

import pypdfium2 as pdfium
from PIL import Image, ImageOps


def used_height(img: Image.Image, footer_px: int) -> float:
    """Share of the page height above the footer that contains ink."""
    g = ImageOps.invert(img.convert("L"))
    body = g.crop((0, 0, g.width, g.height - footer_px))
    box = body.point(lambda v: 255 if v > 24 else 0).getbbox()
    return 0.0 if box is None else box[3] / body.height


def main():
    ap = argparse.ArgumentParser(description="Rasterize a PDF for layout review.")
    ap.add_argument("pdf")
    ap.add_argument("--dpi", type=int, default=100)
    ap.add_argument("--out", help="output folder (default: <pdf>_pages)")
    ap.add_argument("--cols", type=int, default=6, help="pages per row on the contact sheet")
    a = ap.parse_args()

    src = pathlib.Path(a.pdf).resolve()
    out = pathlib.Path(a.out) if a.out else src.with_name(src.stem + "_pages")
    out.mkdir(parents=True, exist_ok=True)

    pdf = pdfium.PdfDocument(str(src))
    pages = []
    for i in range(len(pdf)):
        img = pdf[i].render(scale=a.dpi / 72).to_pil().convert("RGB")
        img.save(out / f"p-{i + 1:02d}.png")
        pages.append(img)

    for i in range(0, len(pages), 2):
        left = pages[i]
        right = pages[i + 1] if i + 1 < len(pages) else Image.new("RGB", left.size, "white")
        pair = Image.new("RGB", (left.width * 2 + 12, left.height), "#888888")
        pair.paste(left, (0, 0))
        pair.paste(right, (left.width + 12, 0))
        pair.save(out / f"pair-{i + 1:02d}.png")

    thumb_w = 300
    thumbs = [p.resize((thumb_w, int(p.height * thumb_w / p.width))) for p in pages]
    rows = (len(thumbs) + a.cols - 1) // a.cols
    sheet = Image.new("RGB", (a.cols * (thumb_w + 8), rows * (thumbs[0].height + 8)), "#cccccc")
    for i, t in enumerate(thumbs):
        sheet.paste(t, ((i % a.cols) * (thumb_w + 8), (i // a.cols) * (t.height + 8)))
    sheet.save(out / "sheet.png")

    footer_px = int(16 / 25.4 * a.dpi)  # ignore the footer band (~16 mm)
    print(f"{len(pages)} pages → {out}")
    for i, p in enumerate(pages, 1):
        u = used_height(p, footer_px)
        flag = "   ← mostly empty: something was pushed onto its own page?" if u < 0.35 and i not in (1, len(pages)) else ""
        print(f"  page {i:2d}: {u:4.0%} of the height used{flag}")


if __name__ == "__main__":
    main()
