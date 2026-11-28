#!/usr/bin/env python3
"""Layout and fit gate for HTML video slides (2026-11-22). Measures every slide in Chromium, as it will be rendered,
and fails before any frame is drawn when a slide would look wrong at 1080p.

    check_layout.py --html video-slides.html [--svg-dir svg] [--css-dir .] [--warn-only] [--json report.json]
    (run with the pdf-kit venv: <repo>/pdf-kit/.venv/bin/python)

render_slides.py calls check(page, html) on the same page before printing, so every build of a reference-solution deck is gated;
LAYOUT_CHECK=warn reports without failing (older videos during a retrofit), LAYOUT_CHECK=off skips it.

What fails (FAIL) — each line names the slide number (data-n, the number in the corner) and the element:
  overflow     text or a box past the slide's content area (the bottom padding, the right padding) or clipped inside a cell
  overlap      two text runs drawn over each other (HTML or inside a diagram); text over the slide number
  box          a diagram label wider or taller than the box it sits in
  small        text below the minimum size at 1080p: MIN_PX for slide text, MIN_SVG_PX for diagram labels
  code         a code line longer than CODE_COLS characters, or more than CODE_LINES lines
What warns (WARN) — split the slide or move the detail to the narration:
  dense        more than MAX_WORDS words on screen (diagram labels not counted), or a table with more than MAX_ROWS rows
  redraw       the same canonical picture drawn in full on more than one slide (GUIDELINES §7.5: one canonical diagram per
               level, then deltas); read from the <name>.meta.json the generators write beside each SVG
Every slide is checked at its last reveal step (everything visible); earlier steps only hide units, they never move them.
"""
import argparse, json, os, pathlib, re, sys

FRAME_SCALE = 1.5        # 13.333 in slide = 1280 CSS px → 1920 frame px
MIN_PX = 22              # DESIGN-TOKENS §2: minimum on-screen text at 1080p (frame px) — slide text
MIN_SVG_PX = 18          # diagram labels (type lines, legends, captions inside a figure); main labels should stay ≥ 22
CODE_COLS, CODE_LINES = 56, 12
MAX_WORDS, MAX_ROWS = 95, 7

JS = r"""(o) => {
  const S = o.scale, res = [];
  const last = {};
  for (const s of document.querySelectorAll('.slide')) last[s.dataset.n || s.id] = s;
  const vis = el => { for (let e = el; e && e.nodeType === 1; e = e.parentElement || e.parentNode) {
      const c = getComputedStyle(e); if (c.visibility === 'hidden' || c.display === 'none' || +c.opacity === 0) return false; } return true; };
  const inter = (a, b) => Math.max(0, Math.min(a.right, b.right) - Math.max(a.left, b.left)) * Math.max(0, Math.min(a.bottom, b.bottom) - Math.max(a.top, b.top));
  const area = r => Math.max(0, r.width) * Math.max(0, r.height);
  const txt = (el, n = 48) => (el.textContent || '').replace(/\s+/g, ' ').trim().slice(0, n);
  for (const [n, s] of Object.entries(last)) {
    const out = [], add = (sev, kind, msg) => out.push({sev, kind, msg});
    const sr = s.getBoundingClientRect(), cs = getComputedStyle(s);
    const lim = {b: sr.bottom - parseFloat(cs.paddingBottom) * 0.55, r: sr.right - parseFloat(cs.paddingRight) * 0.5, t: sr.top, l: sr.left};
    // the slide-number zone (.slide::after, bottom right): 1.6 in × 0.3 in
    const num = {left: sr.right - 1.9 * 96, right: sr.right, top: sr.bottom - 0.5 * 96, bottom: sr.bottom};
    // ── HTML text runs ──
    const runs = [], small = [];
    const walker = document.createTreeWalker(s, NodeFilter.SHOW_TEXT);
    for (let t = walker.nextNode(); t; t = walker.nextNode()) {
      if (!t.textContent.trim()) continue;
      const el = t.parentElement; if (!el || el.closest('svg') || el.closest('style')) continue;
      if (!vis(el)) continue;
      const r = document.createRange(); r.selectNodeContents(t);
      const px = parseFloat(getComputedStyle(el).fontSize) * S;
      if (px + 0.01 < o.min_px) small.push([px, txt(el, 30)]);
      for (const q of r.getClientRects()) {
        if (q.width < 1 || q.height < 1) continue;
        runs.push({q, el});
        if (q.bottom > lim.b + 1) add('FAIL', 'overflow', `past the bottom by ${Math.round((q.bottom - lim.b) * S)} px: "${txt(el)}"`);
        if (q.right > lim.r + 1) add('FAIL', 'overflow', `past the right edge by ${Math.round((q.right - lim.r) * S)} px: "${txt(el)}"`);
        if (inter(q, num) > 4) add('FAIL', 'overlap', `text over the slide number: "${txt(el)}"`);
      }
    }
    if (small.length) { const m = Math.min(...small.map(x => x[0]));
      add('FAIL', 'small', `${small.length} text runs below ${o.min_px} px (smallest ${m.toFixed(1)} px): "${small.find(x => x[0] === m)[1]}"`); }
    for (let i = 0; i < runs.length; i++) for (let j = i + 1; j < runs.length; j++) {
      const a = runs[i], b = runs[j]; if (a.el === b.el || a.el.contains(b.el) || b.el.contains(a.el)) continue;
      const x = inter(a.q, b.q); if (x > 0.25 * Math.min(area(a.q), area(b.q)) && x > 20)
        add('FAIL', 'overlap', `"${txt(a.el, 30)}" over "${txt(b.el, 30)}"`);
    }
    // boxes clipped inside (a cell, a code block, a card)
    for (const el of s.querySelectorAll('pre, td, th, .cd, .case, .fixb, .whyb, .hedge, .techhow, .rejb, .grade, .line, .qq, .s')) {
      if (!vis(el)) continue;
      if (el.scrollWidth > el.clientWidth + 3 && getComputedStyle(el).whiteSpace.startsWith('pre') || el.scrollHeight > el.clientHeight + 3 && getComputedStyle(el).overflowY !== 'visible')
        add('FAIL', 'overflow', `clipped inside ${el.tagName.toLowerCase()}.${el.className}: "${txt(el)}"`);
      const b = el.getBoundingClientRect();
      if (b.bottom > lim.b + 2 && b.height) add('FAIL', 'overflow', `${el.tagName.toLowerCase()}.${el.className} ends ${Math.round((b.bottom - lim.b) * S)} px below the content area`);
    }
    if (s.scrollHeight > s.clientHeight + 2) add('FAIL', 'overflow', `slide content is ${Math.round((s.scrollHeight - s.clientHeight) * S)} px taller than the slide`);
    // code: columns and lines
    for (const p of s.querySelectorAll('pre.code, pre.wire')) {
      const spans = p.querySelectorAll('.ln');      // highlighted code: one block span per line
      const lines = spans.length ? [...spans].map(x => x.textContent.replace(/\s+$/, '')) : p.textContent.replace(/\n$/, '').split('\n');
      const w = Math.max(...lines.map(l => l.length));
      if (w > o.code_cols) add('FAIL', 'code', `a code line of ${w} characters (max ${o.code_cols}): "${lines.find(l => l.length === w).trim().slice(0, 40)}"`);
      if (lines.length > o.code_lines) add('FAIL', 'code', `${lines.length} code lines (max ${o.code_lines}): split, or show the key lines only`);
    }
    // density
    const clone = s.cloneNode(true); clone.querySelectorAll('svg, style').forEach(e => e.remove());
    const nw = (clone.textContent.match(/[A-Za-z0-9][\w'’.,%-]*/g) || []).length;
    if (nw > o.max_words) add('WARN', 'dense', `${nw} words on screen (cap ${o.max_words})`);
    for (const t of s.querySelectorAll('table')) { const rows = t.querySelectorAll('tr').length - (t.classList.contains('tl') ? 0 : 1);
      if (rows > o.max_rows) add('WARN', 'dense', `a table of ${rows} rows (cap ${o.max_rows})`); }
    // ── diagrams ──
    for (const svg of s.querySelectorAll('svg')) {
      const vr = svg.getBoundingClientRect(); if (!vr.width) continue;
      const texts = [...svg.querySelectorAll('text')].filter(t => vis(t) && t.textContent.trim());
      const shapes = [...svg.querySelectorAll('rect, ellipse, path, circle')].filter(e => {
        if (!vis(e)) return false; const r = e.getBoundingClientRect();
        const f = e.getAttribute('fill'); if (e.tagName === 'path' && (!f || f === 'none')) return false;
        if (f === 'none' && e.tagName === 'rect') return false;
        return r.width > 8 && r.height > 8 && r.width < vr.width * 0.92; });
      // a label wholly outside the viewBox is cropped away on purpose (a view of a taller canvas): not drawn, not checked
      const T = texts.map(t => ({t, q: t.getBoundingClientRect(), px: parseFloat(getComputedStyle(t).fontSize) * (t.getScreenCTM() ? t.getScreenCTM().a : 1) * S}))
                     .filter(a => inter(a.q, vr) > 0);
      const fname = (svg.closest('figure') || {dataset: {}}).dataset.f || 'inline svg';
      // dimmed context (effective opacity < 0.5: the boxes a delta view fades) is exempt from the size floor, not from overlap
      const alpha = el => { let a = 1; for (let e = el; e && e !== svg; e = e.parentNode) a *= +(getComputedStyle(e).opacity || 1) * +(e.getAttribute && e.getAttribute('opacity') || 1); return a; };
      const tiny = T.filter(a => a.px + 0.01 < o.min_svg_px && alpha(a.t) >= 0.5);
      if (tiny.length) { const m = tiny.reduce((x, y) => x.px < y.px ? x : y);
        add('FAIL', 'small', `${fname}: ${tiny.length} of ${T.length} labels below ${o.min_svg_px} px (smallest ${m.px.toFixed(1)} px: "${txt(m.t, 30)}")`); }
      for (const a of T) {
        if (a.q.right > vr.right + 2 || a.q.left < vr.left - 2 || a.q.bottom > vr.bottom + 2 || a.q.top < vr.top - 2)
          add('FAIL', 'overflow', `diagram label outside its figure: "${txt(a.t, 40)}"`);
        // the box the label sits in: the smallest filled shape containing the label's centre
        const cx = (a.q.left + a.q.right) / 2, cy = (a.q.top + a.q.bottom) / 2;
        let box = null, ba = Infinity;
        for (const sh of shapes) { const r = sh.getBoundingClientRect();
          if (cx > r.left && cx < r.right && cy > r.top && cy < r.bottom && area(r) < ba && area(r) > area(a.q) * 0.6) { box = r; ba = area(r); } }
        if (box && (a.q.left < box.left - 3 || a.q.right > box.right + 3))
          add('FAIL', 'box', `label wider than its box by ${Math.round((Math.max(box.left - a.q.left, a.q.right - box.right)) * S)} px: "${txt(a.t, 40)}"`);
      }
      for (let i = 0; i < T.length; i++) for (let j = i + 1; j < T.length; j++) {
        const a = T[i], b = T[j], x = inter(a.q, b.q);
        if (x > 0.18 * Math.min(area(a.q), area(b.q)) && x > 12) add('FAIL', 'overlap', `diagram labels collide: "${txt(a.t, 28)}" × "${txt(b.t, 28)}"`);
      }
    }
    const figs = [...s.querySelectorAll('figure[data-f]')].map(f => f.dataset.f);
    // de-duplicate messages
    const seen = new Set(), uniq = out.filter(x => { const k = x.kind + x.msg; if (seen.has(k)) return false; seen.add(k); return true; });
    res.push({n, title: txt(s.querySelector('h1, .s, .qq') || s, 60), figs, issues: uniq});
  }
  return res;
}"""


def check(page, svg_dir=None, warn_only=False, report=None, limits=None):
    """Run on a loaded Playwright page (screen or print media, viewport 1280 × 720). Returns (fails, warns, lines)."""
    o = dict(scale=FRAME_SCALE, min_px=MIN_PX, min_svg_px=MIN_SVG_PX, code_cols=CODE_COLS, code_lines=CODE_LINES,
             max_words=MAX_WORDS, max_rows=MAX_ROWS)
    o.update(limits or {})
    res = page.evaluate(JS, o)
    # redraws of one canonical picture: generators write <name>.meta.json = {"canon": id, "full": true|false}
    if svg_dir:
        full = {}
        for r in res:
            for f in r["figs"]:
                m = pathlib.Path(svg_dir) / f"{f}.meta.json"
                if m.exists():
                    meta = json.loads(m.read_text())
                    if meta.get("full"):
                        full.setdefault(meta["canon"], []).append((r["n"], f))
        for canon, uses in full.items():
            if len(uses) > 1:
                for n, f in uses[1:]:
                    r = next(x for x in res if x["n"] == n)
                    r["issues"].append(dict(sev="WARN", kind="redraw", msg=f"'{f}' redraws the whole '{canon}' picture again "
                                            f"(first drawn on slide {uses[0][0]}): show a delta (new=, keep=, focus=, badges=)"))
    lines, fails, warns = [], 0, 0
    for r in res:
        for i in r["issues"]:
            lines.append(f"slide {r['n']:>4} {i['sev']:<4} {i['kind']:<8} {i['msg']}   [{r['title']}]")
            fails += i["sev"] == "FAIL"; warns += i["sev"] == "WARN"
    summary = (f"layout check: {len(res)} slides, {fails} failures, {warns} warnings "
               f"(min text {o['min_px']} px, min diagram label {o['min_svg_px']} px at 1080p)")
    if report:
        pathlib.Path(report).write_text(json.dumps(res, indent=1) if str(report).endswith(".json") else "\n".join(lines + [summary]) + "\n")
    return fails, warns, lines + [summary]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--html", required=True); ap.add_argument("--svg-dir"); ap.add_argument("--css-dir")
    ap.add_argument("--warn-only", action="store_true"); ap.add_argument("--json"); ap.add_argument("--only", help="slide numbers, e.g. 4,48")
    ap.add_argument("--shots", help="write a 1920×1080 PNG of the last step of each --only slide (or every failing slide) here")
    a = ap.parse_args()
    src = pathlib.Path(a.html).resolve(); svg_dir = pathlib.Path(a.svg_dir) if a.svg_dir else src.parent / "svg"
    sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent)); import paths
    sys.path.insert(0, str(paths.PDFKIT))
    from build import inline_svgs, inline_css
    from playwright.sync_api import sync_playwright
    page = inline_css(inline_svgs(src.read_text(encoding="utf-8"), svg_dir), pathlib.Path(a.css_dir) if a.css_dir else src.parent)
    built = src.with_suffix(".check.html"); built.write_text(page, encoding="utf-8")
    try:
        with sync_playwright() as p:
            b = p.chromium.launch(); pg = b.new_page(viewport={"width": 1280, "height": 720}, device_scale_factor=FRAME_SCALE)
            pg.emulate_media(media="print"); pg.goto(built.as_uri(), wait_until="load"); pg.evaluate("document.fonts.ready.then(() => true)")
            fails, warns, lines = check(pg, svg_dir, report=a.json)
            if a.shots:
                out = pathlib.Path(a.shots); out.mkdir(parents=True, exist_ok=True)
                want = [int(x) for x in a.only.split(",")] if a.only else sorted({int(l.split()[1]) for l in lines[:-1]})
                for n in want:
                    els = pg.query_selector_all(f'.slide[data-n="{n}"]')
                    if els: els[-1].screenshot(path=str(out / f"slide-{n:03d}.png"))
            b.close()
    finally:
        built.unlink(missing_ok=True)
    if a.only:
        keep = {f"slide {int(x):>4}" for x in a.only.split(",")}
        lines = [l for l in lines if l[:10] in keep] + lines[-1:]
    print("\n".join(lines))
    if fails and not (a.warn_only or os.environ.get("LAYOUT_CHECK") == "warn"):
        sys.exit(1)


if __name__ == "__main__":
    main()
