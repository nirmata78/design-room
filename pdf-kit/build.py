#!/usr/bin/env python3
"""Build an A4 PDF in the reference-guide style from one HTML source.

    python build.py my-guide.html                  # → my-guide.pdf next to it
    python build.py my-guide.html -o out/guide.pdf --footer "Kafka · interview companion"

What it does
  1. Replaces every <!--SVG:name--> with the contents of svg/name.svg
     (looked up next to the HTML, or in --svg-dir).
  2. Inlines <link rel="stylesheet" href="style.css">. The CSS is taken from the
     HTML's folder if present, otherwise from this kit, and its relative url()s
     (the bundled fonts) are rewritten to absolute file URIs.
  3. Prints with headless Chromium (Playwright): A4, backgrounds on, page-number footer.

Setup (once):  pip install playwright pypdf  &&  python -m playwright install chromium
"""
import argparse
import html as htmllib
import pathlib
import re
import sys

from playwright.sync_api import sync_playwright

KIT = pathlib.Path(__file__).resolve().parent

FOOTER = """<div style="font-family:Inter,Helvetica,Arial,sans-serif;font-size:7pt;color:#8c959f;width:100%;
padding:0 13mm;display:flex;justify-content:space-between;">
<span>{text}</span><span><span class="pageNumber"></span> / <span class="totalPages"></span></span></div>"""


def inline_svgs(html: str, svg_dir: pathlib.Path) -> str:
    def repl(m):
        path = svg_dir / f"{m.group(1)}.svg"
        if not path.exists():
            sys.exit(f"build.py: missing diagram {path}")
        svg = path.read_text(encoding="utf-8")
        # the xmlns is only needed when the SVG is opened on its own
        return svg.replace(' xmlns="http://www.w3.org/2000/svg"', "")
    return re.sub(r"<!--SVG:([\w.-]+)-->", repl, html)


def inline_css(html: str, src_dir: pathlib.Path) -> str:
    def repl(m):
        href = m.group(1)
        css_path = src_dir / href if (src_dir / href).exists() else KIT / pathlib.Path(href).name
        if not css_path.exists():
            sys.exit(f"build.py: stylesheet not found: {href}")
        css = css_path.read_text(encoding="utf-8")
        base = css_path.parent

        def absolutize(u):
            target = (base / u.group(1)).resolve()
            return f'url("{target.as_uri()}")'
        # leave data:, http(s):, file: and fragment refs such as url(#ah) (SVG arrowheads) untouched
        css = re.sub(r'url\(["\']?(?!data:|https?:|file:|#)([^"\')]+)["\']?\)', absolutize, css)
        return f"<style>\n{css}\n</style>"
    return re.sub(r'<link rel="stylesheet" href="([^"]+)"\s*/?>', repl, html)


def main():
    ap = argparse.ArgumentParser(description="Build a reference-guide PDF from HTML.")
    ap.add_argument("html", help="source HTML file")
    ap.add_argument("-o", "--out", help="output PDF (default: next to the HTML)")
    ap.add_argument("--footer", help="left footer text (default: the <title>)")
    ap.add_argument("--svg-dir", help="folder with the diagrams (default: ./svg next to the HTML)")
    ap.add_argument("--keep-html", action="store_true", help="keep the intermediate *.built.html")
    a = ap.parse_args()

    src = pathlib.Path(a.html).resolve()
    html = src.read_text(encoding="utf-8")
    html = inline_svgs(html, pathlib.Path(a.svg_dir).resolve() if a.svg_dir else src.parent / "svg")
    html = inline_css(html, src.parent)

    title = re.search(r"<title>(.*?)</title>", re.sub(r"<!--.*?-->", "", html, flags=re.S), re.S)
    footer = a.footer or (title.group(1).strip() if title else src.stem)

    built = src.with_name(src.stem + ".built.html")
    built.write_text(html, encoding="utf-8")
    out = pathlib.Path(a.out).resolve() if a.out else src.with_suffix(".pdf")
    out.parent.mkdir(parents=True, exist_ok=True)

    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()
        page.goto(built.as_uri(), wait_until="load")
        page.evaluate("document.fonts.ready.then(() => true)")  # bundled fonts must be loaded
        page.pdf(path=str(out), format="A4", print_background=True, prefer_css_page_size=True,
                 display_header_footer=True, header_template="<span></span>",
                 footer_template=FOOTER.format(text=htmllib.escape(footer)))
        browser.close()

    if not a.keep_html:
        built.unlink()
    try:
        from pypdf import PdfReader
        pages = len(PdfReader(str(out)).pages)
    except Exception:
        pages = "?"
    print(f"{out}  ({pages} pages)")


if __name__ == "__main__":
    main()
