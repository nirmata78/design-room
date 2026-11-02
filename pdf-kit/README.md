# Reference-guide PDF kit

Everything needed to produce A4 PDFs in the style of the *Redis, owned* and *URL Shortener, passed* guides:
dark cover band, numbered sections, coloured callout boxes, dense tables, inline SVG diagrams, monospace code,
a one-page cheat sheet, and a page-number footer.

You write one HTML file using a handful of CSS classes, draw diagrams as small SVG files, and run one command.
Headless Chromium does the typesetting, so what you see in a browser is what you get on paper.

> **In design-room.** Set it up once (below, from inside `pdf-kit/`; `.venv/` is gitignored). After that
> `scripts/build-report.sh` renders every session report through this kit automatically, using
> `templates/report-kit.html`. For a new reference guide, start from `template.html` and keep the
> document in `pdf-kit/examples/<topic>/` with its `svg/`. Built PDFs and `*_pages/` review images are
> gitignored. `START-HERE.md` is the notes for the notification-platform example.

```
pdf-style-kit/
├── style.css            the whole look: page size, palette, typography, boxes, tables, diagram classes
├── fonts/               Inter + DejaVu Sans Mono, bundled so output is identical on every machine
├── build.py             HTML (+ svg/) → PDF
├── check.py             PDF → page PNGs, contact sheet, "half-empty page" warnings
├── template.html        every component, commented; start new documents from here
├── template.pdf         what the template renders to
├── svg/example.svg      diagram conventions, commented
├── examples/
│   ├── redis-ticketing/ the Redis recap (18 pages, 14 diagrams) — the SD-47 companion
│   ├── url-shortener/   the URL shortener reference interview (13 pages, 10 diagrams)
│   └── notification-platform/  the SD-12 reference interview (11 pages, 11 diagrams; see START-HERE.md)
├── build-examples.sh    rebuilds the template and both examples
└── requirements.txt
```

## Setup (once)

macOS / Linux, Python 3.10+:

```bash
cd pdf-style-kit
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python -m playwright install chromium        # downloads a private Chromium (~150 MB)
```

No system fonts are needed: `build.py` points the stylesheet at `fonts/`.

## Use

```bash
python build.py template.html                                  # → template.pdf
python build.py notes/kafka.html -o out/kafka.pdf --footer "Kafka · interview companion"
python check.py out/kafka.pdf                                  # → out/kafka_pages/
./build-examples.sh                                            # sanity check: rebuilds everything
```

`build.py` options: `-o/--out` output path (default: next to the HTML), `--footer` left footer text
(default: the page `<title>`), `--svg-dir` (default: `svg/` next to the HTML), `--keep-html` to keep the
intermediate file for debugging in a browser.

`check.py` writes `p-NN.png` per page, `pair-NN.png` (two pages side by side, best for reviewing) and
`sheet.png` (all pages), and prints how much of each page is used. A page under ~35% usually means a heading,
a figure or a box got pushed onto its own page.

## How a document is put together

1. **Start from `template.html`.** Keep the `<svg>` block with the three `<marker>` definitions at the top of the
   body: every arrowhead in every diagram refers to them.
2. **Stylesheet:** `<link rel="stylesheet" href="style.css">`. If there's no `style.css` next to your HTML,
   the kit's one is used, so documents can live anywhere.
3. **Diagrams:** put `<!--SVG:name-->` inside a `<figure>`; at build time it's replaced by `svg/name.svg`.
4. **Page breaks:** `class="section pb"` forces a new page. Use it only for the first section after the cover
   and for the cheat sheet; let everything else flow so pages stay full.

### Components

| You want | Markup |
|---|---|
| Cover | `<div class="cover-band">` with `.tag`, `<h0>`, `.sub`, `.meta`, optional `<svg class="icon">` |
| Section heading | `<h1><span class="n">3</span>Title<span class="slot">STAGE 2 · MIN 5–10</span></h1>` |
| Sub-headings | `<h2>`, `<h3>` |
| Callouts | `<div class="box say\|why\|trap\|key\|probe"><span class="t">Label</span><p>…</p></div>` |
| — meaning | **say** green: a line to say out loud · **why** blue: theory · **trap** amber · **key** red: must-know · **probe** purple: interviewer follow-ups |
| Two / three columns | `<div class="cols">…</div>` / `<div class="cols3">` |
| Table | `<table><thead><tr><th>…` (use `<thead>` so the header repeats across pages) |
| Command table | `<table class="api">`, group rows `<tr class="grp"><td colspan="3">Group</td></tr>` |
| Code | `<pre>` with `<span class="k">` keyword, `<span class="c">` comment, `<span class="s">` string |
| Figure | `<figure><!--SVG:name--><figcaption><b>Figure N. Title.</b> What to notice.</figcaption></figure>` |
| Numbered steps | `<ol class="steps">` |
| Q&A drill | `<div class="qa"><div class="q">Question?</div><div class="a">Answer.</div></div>` |
| Table of contents | `<ul class="toc"><li><b>1</b>Title <span>hint</span></li>…</ul>` |
| Cheat sheet | `<div class="section pb cheat">` (add `roomy` for larger text); `td.m` for monospace cells |

### Diagrams (`svg/*.svg`)

* Root: `<svg class="d" viewBox="0 0 720 H" xmlns="http://www.w3.org/2000/svg">`. Width 720 always equals the
  text width; choose the height you need.
* Boxes: `<rect … rx="5" class="b|w|r|bl|g|a|g2"/>` (grey, white, red, blue, green, amber, dark grey).
* Text: default 11.5 px; `tb` bold, `ts` small, `tm` mono, `lab` small-caps label, `c` centred;
  colours `tr` red, `tg` green, `sp` blue.
* Lines: `ln` grey arrow, `ln-r` red, `ln-g` green; add `dash` for async; `life` for sequence lifelines.
* Budget text width before you draw: ~6.2 px per character at normal size, ~5.4 px small, ~5.8 px mono.
  Most layout bugs are labels wider than their box.
* The SVG files carry no styles of their own (opened alone, boxes render black). Preview by building, or run
  `build.py --keep-html` and open the `.built.html` in a browser, which reloads faster than a PDF viewer.

### Layout rules learned the hard way

* **Code width:** keep lines ≤ 50 characters inside two columns and ≤ 110 at full width, or they wrap mid-token.
* **Half-empty pages:** run `check.py` after every build. Fix by moving a box, trimming a paragraph, or
  removing a `.pb` break, not by shrinking fonts.
* **Boxes and figures never split** across pages (`break-inside: avoid`); a very tall box therefore leaves a gap.
  Split long boxes into two.
* **A two-column block can split** across pages; if one column spills alone onto the next page, move that
  box out of the columns.
* Escape `<`, `>` and `&` inside `<pre>`; use Unicode for superscripts and arrows (`62⁷`, `→`, `≤`).
* Numbers in examples should be real. The URL shortener's codes (`fN7J2J9`…) are actual outputs of its
  Feistel code with demo keys.

## Using it with Claude

Attach or connect this folder and ask, for example:

> Using the PDF kit in this folder, write a reference guide on **Kafka for system design interviews** in the
> same style: start from template.html, put diagrams in svg/, build with build.py, review every page with
> check.py, and fix half-empty pages, wrapped code and overflowing diagram labels before sending the PDF.

## Licences

Inter: SIL Open Font License 1.1 (`fonts/Inter-LICENSE.txt`). DejaVu Sans Mono: Bitstream Vera / DejaVu
licence (`fonts/DejaVu-LICENSE.txt`). Both allow bundling. The kit's own code and styles are yours to use and change.
