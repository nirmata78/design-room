#!/usr/bin/env python3
"""Port an old slide-video-kit mock video (video-slides.html + <name>.script.md) to a course-builder source draft.

  port_mock.py VIDEO_DIR SCRIPT.md OUT.txt --title "..." --short "..." --n 1

Every numbered slide becomes one `= type` block with its narration underneath; `## Section` headings become
`## n.m Section` with a placeholder intro line (`N: TODO intro`) that must be rewritten by hand. Unknown layouts fall
back to a `list`. The draft is a starting point: read it, fix it, then compile."""
import argparse, html, pathlib, re
from html.parser import HTMLParser


class Node:
    def __init__(self, tag, attrs, parent=None):
        self.tag, self.attrs, self.parent, self.kids = tag, dict(attrs), parent, []
    @property
    def cls(self): return (self.attrs.get("class") or "").split()
    def find_all(self, pred):
        for k in self.kids:
            if isinstance(k, Node):
                if pred(k): yield k
                yield from k.find_all(pred)
    def first(self, pred): return next(self.find_all(pred), None)


class P(HTMLParser):
    VOID = {"br", "img", "meta", "link", "hr", "input"}
    def __init__(self):
        super().__init__(convert_charrefs=True); self.root = Node("root", []); self.cur = self.root
    def handle_starttag(self, t, a):
        n = Node(t, a, self.cur); self.cur.kids.append(n)
        if t not in self.VOID: self.cur = n
    def handle_endtag(self, t):
        c = self.cur
        while c is not self.root and c.tag != t: c = c.parent
        if c is not self.root: self.cur = c.parent
    def handle_data(self, d): self.cur.kids.append(d)
    def handle_comment(self, d):
        m = re.match(r"SVG:([\w.-]+)", d.strip())
        if m: self.cur.kids.append(("SVG", m.group(1)))


def md(n, pre=False):
    """Inline markdown of a node: <b>/<strong> → **, <em>/<i> → *, <code> → `."""
    if isinstance(n, str): return n if pre else re.sub(r"\s+", " ", n)
    if isinstance(n, tuple): return ""
    inner = "".join(md(k, pre or n.tag == "pre") for k in n.kids)
    if n.tag in ("b", "strong"): return f"**{inner.strip()}**" if inner.strip() else ""
    if n.tag in ("em",): return f"*{inner.strip()}*" if inner.strip() else ""
    if n.tag == "code": return f"`{inner}`"
    if n.tag == "br": return " "
    return inner


def txt(n): return md(n).strip() if n else ""


def svgs(n):
    out = []
    for k in n.kids:
        if isinstance(k, tuple): out.append(k[1])
        elif isinstance(k, Node): out += svgs(k)
    return out


PREFIX = ""

def convert(slide):
    c = slide.cls
    by = lambda cl: slide.first(lambda x: cl in x.cls)
    k, h1 = txt(by("k")), txt(slide.first(lambda x: x.tag == "h1"))
    line = by("line")
    take = [f"> {txt(line)}"] if line else []
    flags = " aux" if "aux" in c else ""
    if "th" in c:
        return [f"= th{flags} | {txt(by('lbl'))} | {txt(by('s'))} | {txt(by('sub'))}".rstrip(" |")]
    if "qs" in c:
        return [f"= th | {txt(by('who'))} | {txt(by('qq'))} | {txt(by('hint'))}".rstrip(" |")]
    s = svgs(slide)
    if s:
        return [f"= dia{flags} | {k} | {h1}", PREFIX + s[0]] + take
    tab = slide.first(lambda x: x.tag == "table")
    if tab:
        rows = []
        for tr in tab.find_all(lambda x: x.tag == "tr"):
            cells = [txt(td).replace("|", "/") for td in tr.kids if isinstance(td, Node) and td.tag in ("td", "th")]
            rows.append(" | ".join(cells))
        return [f"= table{flags} | {k} | {h1}"] + rows + take
    pre = slide.first(lambda x: x.tag == "pre")
    if pre:
        pres = list(slide.find_all(lambda x: x.tag == "pre"))
        code = "\n\n".join("".join(md(x, True) for x in q.kids).strip("\n").replace("**", "") for q in pres)
        lang = "sql" if re.search(r"\b(SELECT|INSERT|UPDATE|CREATE TABLE)\b", code) else "http" if re.match(r"\s*(GET|POST|PUT|DELETE) /", code) else "python"
        return [f"= code {lang}{flags} | {k} | {h1}"] + code.splitlines() + take
    tiles = slide.first(lambda x: "tiles" in x.cls)
    if tiles:
        out = [f"= tiles{flags} | {k} | {h1}"]
        for t in tiles.find_all(lambda x: "tile" in x.cls):
            b = t.first(lambda x: x.tag == "b"); sp = t.first(lambda x: x.tag == "span")
            out.append(f"{txt(b)} | {txt(sp)}")
        return out + take
    cards = slide.first(lambda x: "cards" in x.cls)
    if cards:
        cols = next((x for x in cards.cls if re.fullmatch(r"c\d", x)), "c3")
        out = [f"= cards {cols}{flags} | {k} | {h1}"]
        for cd in cards.find_all(lambda x: "cd" in x.cls):
            t = cd.first(lambda x: x.tag in ("h3", "b")); p = [txt(x) for x in cd.find_all(lambda x: x.tag in ("p", "li"))]
            out.append(f"{txt(t)} :: {' '.join(p)}")
        return out + take
    items = [txt(x) for x in slide.find_all(lambda x: x.tag in ("li", "p"))]
    return [f"= list{flags} | {k} | {h1}"] + [f"- {i}" for i in items if i] + take


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("video"); ap.add_argument("script"); ap.add_argument("out")
    ap.add_argument("--title"); ap.add_argument("--short"); ap.add_argument("--n", type=int, default=1); ap.add_argument("--svg-prefix", default="")
    a = ap.parse_args()
    global PREFIX; PREFIX = a.svg_prefix
    p = P(); p.feed(pathlib.Path(a.video, "video-slides.html").read_text(encoding="utf-8"))
    slides = list(p.root.find_all(lambda x: x.tag == "div" and "slide" in x.cls))
    body = {}
    cur, sec, out, n = None, 0, [f"#! title: {a.title}", f"#! short: {a.short}", ""], 0
    for ln in pathlib.Path(a.script).read_text(encoding="utf-8").splitlines():
        m = re.match(r"^\[slide:\s*v-(\d+)\]", ln)
        if m:
            i = int(m.group(1)); out += [""] + convert(slides[i - 1]); continue
        if ln.startswith("## "):
            sec += 1; out += ["", f"## {a.n}.{sec} {ln[3:].strip()}", "N: TODO intro"]; continue
        if re.match(r"^[NICVE]: ", ln) or re.match(r"^\[pause: [\d.]+\]$", ln):
            out.append(ln)
    pathlib.Path(a.out).write_text("\n".join(out) + "\n", encoding="utf-8")
    print(f"{len(slides)} slides, {sec} sections → {a.out}")


if __name__ == "__main__":
    main()
