#!/usr/bin/env python3
"""Split a text-layer PDF book into chapter-level Markdown plus figure pages and video briefs.

    python3 scripts/book_to_md.py <book.pdf> <slug> "<Book title>" [--out private/books] [--dpi 90]

Needs `pypdf` (outline) and poppler's `pdftotext` / `pdftoppm`. Output is a COPY of copyrighted text:
it must stay under a gitignored path (default `private/books/`). Nothing here is ever committed.

Per book it writes  <out>/<slug>/
    README.md            book map: chapters, page ranges, word counts, figure counts
    chapters/NN-*.md     one chapter, headings recovered from the PDF outline, paragraphs re-flowed
    figures/pNNNN.jpg    a render of every page that carries a captioned figure/table (redraw reference)
    figures.tsv          chapter, page, label, caption
    briefs/NN-*.brief.md per-chapter video-brief skeleton, pre-filled from the extraction
"""
import argparse, re, subprocess, sys, unicodedata
from pathlib import Path
from pypdf import PdfReader

CHAPTER_RE = re.compile(r"^((?i:Chapter)\s+\d+[.:]|Appendix\s+[A-Z]\.|\d{1,2}\s+[A-Z][A-Z ,&:/\-]+$)")
PART_RE = re.compile(r"^Part\s+[IVX]+\.")
KEEP_RE = re.compile(r"^(Foreword|Preface|Bibliography|Glossary|Afterword|Epilogue|Conclusion)", re.I)
FIG_RE = re.compile(r"^(Figure|Table|Example|Listing)\s+(\d+[\-\.]\d+|[A-Z]\-\d+)\.?\s*(.*)$")
HY = "‐‑­"
FOOT_RE = re.compile(r"\d*An early version.*$")


def norm(s):
    s = unicodedata.normalize("NFKC", s)
    return re.sub(r"\s+", " ", s).strip().lower()


def slugify(s):
    return re.sub(r"[^a-z0-9]+", "-", norm(s)).strip("-")[:48].rstrip("-")


def flatten(reader):
    out = []

    def walk(items, depth):
        for it in items:
            if isinstance(it, list):
                walk(it, depth + 1)
            else:
                try:
                    pg = reader.get_destination_page_number(it) + 1
                except Exception:
                    continue
                out.append((depth, re.sub(r"\s+", " ", it.title).strip(), pg))

    walk(reader.outline, 0)
    return out


def page_texts(pdf):
    raw = subprocess.run(["pdftotext", str(pdf), "-"], capture_output=True, text=True, check=True).stdout
    return [""] + raw.split("\f")  # 1-based


def find_title_line(lines, title, start=0):
    """(index, lines consumed) where `title` starts (it may wrap over two lines), else (-1, 0)."""
    t = norm(FOOT_RE.sub("", title))
    for i in range(start, len(lines)):
        a = norm(lines[i])
        if not a:
            continue
        if a == t or (len(t) > 18 and len(a) >= 10 and a.startswith(t[:18])):
            return i, 1
        if i + 1 < len(lines) and norm(lines[i] + " " + lines[i + 1]) == t:
            return i, 2
    return -1, 0


RUNHEAD_RE = re.compile(r"^(\d+\s*\|\s*)?((?i:Chapter)\s+\d+\s*[:|.]\s*.*|CHAPTER\s+\d+(\s+[A-Z ,&:/\-]+)?|\|)(\s*\|\s*\d+)?$|^\d+\s*\|\s*\S.*|^.*\s\|\s*\d+$")


def drop_running(seg, label, subs, p, first_page):
    """Remove running heads/feet: 'Chapter N: Title', 'CHAPTER N', stray '|', and section titles repeated off their own page."""
    short = norm(re.sub(r"^(Chapter|Appendix)\s+\w+\.\s*", "", label))
    own = {norm(FOOT_RE.sub("", st)) for _, st, sp in subs if sp == p}
    other = {norm(FOOT_RE.sub("", st)) for _, st, sp in subs if sp != p}
    out, skip_title = [], False
    for ln in seg:
        s = ln.strip()
        n_ = norm(s)
        if re.fullmatch(r"CHAPTER\s+\d+", s) and first_page:
            skip_title = True
            continue
        if skip_title and s:
            skip_title = False
            if n_ == short:
                continue
        if s and (RUNHEAD_RE.match(s) and len(s) < 90):
            continue
        if n_ and n_ not in own and (n_ in other or n_ == short) and len(s) < 90:
            continue
        out.append(ln)
    return out


def reflow(lines):
    """Join hard-wrapped lines into paragraphs; keep headings, bullets and caption lines as their own blocks."""
    lens = sorted(len(l) for l in lines if len(l) > 40)
    full = lens[int(len(lens) * 0.8)] if lens else 80
    paras, cur = [], ""

    def flush():
        nonlocal cur
        if cur.strip():
            paras.append(cur.strip())
        cur = ""

    for l in lines:
        s = l.strip()
        if not s:
            flush()
            continue
        if re.fullmatch(r"\d{1,4}", s):
            continue  # stray page number
        if s.startswith("#"):
            flush()
            paras.append(s)
            continue
        if re.match(r"^(•|\*|\d+\.\s)", s) or FIG_RE.match(s):
            flush()
            cur = s
            continue
        if cur and cur[-1] in HY:
            cur = cur[:-1] + s
        elif cur.endswith("-") and s[:1].islower():
            cur = cur[:-1] + s
        elif cur:
            cur += " " + s
        else:
            cur = s
        if len(l) < full * 0.6 and re.search(r"[.!?:)”\"]$", s):
            flush()
    flush()
    return re.sub(r"\n{3,}", "\n\n", "\n\n".join(paras)).strip()


def build(pdf, slug, title, out, dpi):
    reader = PdfReader(str(pdf))
    ents = flatten(reader)
    pages = page_texts(pdf)
    npages = len(pages) - 1

    marks = []  # (index into ents, kind, label)
    for i, (d, t, p) in enumerate(ents):
        if PART_RE.match(t):
            marks.append((i, "part", t))
        elif CHAPTER_RE.match(t) or (d == 0 and KEEP_RE.match(t)):
            marks.append((i, "chapter", t))
        elif d == 0:
            marks.append((i, "skip", t))  # cover, copyright, contents, index: closes the previous chapter
    mark_idx = [m[0] for m in marks]
    root = Path(out) / slug
    for sub in ("chapters", "figures", "briefs"):
        (root / sub).mkdir(parents=True, exist_ok=True)

    rows, fig_rows, part, n = [], [], "", 0
    for ei, kind, label in marks:
        if kind == "skip":
            continue
        if kind == "part":
            part = label  # a Part is also emitted: its intro pages carry real text
        d0, _, p0 = ents[ei]
        end_ei = next((j for j in mark_idx if j > ei), None)
        if end_ei is None:
            p1, next_title = npages, None
        else:
            p1, next_title = ents[end_ei][2], ents[end_ei][1]
        if p1 < p0:
            p1 = p0
        subs = [(d - d0, t, p) for (d, t, p) in ents[ei + 1:(end_ei if end_ei else len(ents))]]
        n += 1
        lines, fig_pages = [], []
        for p in range(p0, p1 + 1):
            pl = pages[p].split("\n")
            lo, hi = 0, len(pl)
            if p == p0:
                k, c = find_title_line(pl, label)
                lo = k + c if k >= 0 else 0
            if p == p1 and next_title:
                k, _ = find_title_line(pl, next_title, lo)
                if k >= 0:
                    hi = k
            seg = drop_running(pl[lo:hi], label, subs, p, p == p0)
            for sd, st, sp in subs:
                if sp != p:
                    continue
                k, c = find_title_line(seg, st)
                if k >= 0:
                    seg[k:k + c] = ["", "#" * min(sd + 1, 4) + " " + FOOT_RE.sub("", st), ""]
            for ln in seg:
                m = FIG_RE.match(ln.strip())
                if m:
                    fig_rows.append((n, p, f"{m.group(1)} {m.group(2)}", m.group(3).strip()))
                    if p not in fig_pages:
                        fig_pages.append(p)
            while seg and not seg[-1].strip():
                seg.pop()
            while seg and not seg[0].strip():
                seg.pop(0)
            if lines and lines[-1].strip() and not re.search(r"[.!?:;)\u201d\"]$", lines[-1].strip()):
                pass  # sentence continues across the page break: no blank line
            elif lines:
                lines.append("")
            lines.extend(seg)
        body = reflow(lines)
        words = len(body.split())
        name = f"{n:02d}-{slugify(label)}"
        fm = (f'---\nbook: "{title}"\nchapter: "{label}"\npart: "{part}"\npdf_pages: [{p0}, {p1}]\n'
              f"words: {words}\nsource: private copy for study; do not publish\n---\n\n")
        (root / "chapters" / f"{name}.md").write_text(fm + f"# {label}\n\n" + body + "\n", encoding="utf-8")
        for p in fig_pages:
            jpg = root / "figures" / f"p{p:04d}.jpg"
            if not jpg.exists():
                subprocess.run(["pdftoppm", "-jpeg", "-jpegopt", "quality=70", "-r", str(dpi), "-f", str(p), "-l", str(p),
                                "-singlefile", str(pdf), str(jpg.with_suffix(""))], check=True)
        figs = [f for f in fig_rows if f[0] == n]
        sect = [(sd, st, sp) for sd, st, sp in subs if sd <= 2]
        lo_min, hi_min = max(4, round(words / 900)), max(6, round(words / 600))
        brief = [f"# Video brief · {label}", "", f"- Book: {title}", f"- Part: {part or '-'}",
                 f"- Source: `../chapters/{name}.md` (PDF pages {p0}-{p1}, {words} words)",
                 f"- Target length: {lo_min}-{hi_min} min narrated (rule of thumb: 1 min per 600-900 source words)",
                 "", "## Sections (from the book's outline)", ""]
        brief += [f"{'  ' * (sd - 1)}- {FOOT_RE.sub('', st)} (p.{sp})" for sd, st, sp in sect] or ["- (single block)"]
        brief += ["", "## Figures and tables to redraw", ""]
        brief += [f"- p.{p} · {lab}: {cap}  → `../figures/p{p:04d}.jpg`" for _, p, lab, cap in figs] or ["- none captioned"]
        brief += ["", "## One-sentence thesis", "", "TODO", "", "## Story beats (5-8, one idea each)", "", "1. TODO", "",
                  "## Modern update (what changed since publication)", "", "TODO", "",
                  "## New diagrams to author (not in the book)", "", "- TODO", "",
                  "## Questions the viewer should be able to answer afterwards", "", "- TODO", ""]
        (root / "briefs" / f"{name}.brief.md").write_text("\n".join(brief), encoding="utf-8")
        rows.append((n, label, part, p0, p1, words, len(figs), name))
        print(f"{n:02d} {label[:60]:60s} p{p0}-{p1} {words}w {len(figs)}fig", file=sys.stderr)

    with open(root / "figures.tsv", "w", encoding="utf-8") as f:
        f.write("chapter\tpage\tlabel\tcaption\n")
        for r in fig_rows:
            f.write("\t".join(str(x) for x in r) + "\n")
    md = [f"# {title}", "", f"Private study extraction of `{pdf.name}` ({npages} PDF pages). Not for publication.", "",
          "| # | Chapter | Part | PDF pages | Words | Figures | File |", "|---|---|---|---|---|---|---|"]
    md += [f"| {a} | {b} | {c} | {d}-{e} | {w} | {g} | [{h}](chapters/{h}.md) |" for a, b, c, d, e, w, g, h in rows]
    md += ["", f"Total words: {sum(r[5] for r in rows)}"]
    (root / "README.md").write_text("\n".join(md) + "\n", encoding="utf-8")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("pdf", type=Path)
    ap.add_argument("slug")
    ap.add_argument("title")
    ap.add_argument("--out", default="private/books")
    ap.add_argument("--dpi", type=int, default=90)
    a = ap.parse_args()
    build(a.pdf, a.slug, a.title, a.out, a.dpi)
