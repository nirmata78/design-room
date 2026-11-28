#!/usr/bin/env python3
"""Sequence diagrams as standalone SVG, in the Google theme of the c4-structurizr C4 views (same palette and font).
Numbered messages, lifelines, notes, and alt/loop/opt frames. Layout is automatic: one row per step.

    import seqsvg as sq
    s = sq.Seq(width=1600)
    s.part("auth", "Auth service", "ext"); s.part("in", "Intake API", "container"); s.part("k", "Kafka P0", "queue")
    s.msg("auth", "in", "POST /notifications (P0, dedupKey)")
    s.msg("in", "k", "produce, acks=all")
    s.ret("in", "auth", "202 Accepted")
    s.note("k", "k", "lag ≈ 0 — the campaign is on another topic")
    s.frame("alt", "token unregistered (410)"); s.msg(...); s.end()
    s.save("svg/seq-p0.svg")

Kinds for participants: person · system · container · queue · db · component · ext · focus (red highlight).
msg(kind=…): "sync" solid + filled arrow (default) · "async" solid + open arrow · "ret" dashed + open arrow.
A message from a participant to itself draws a small loop.  hl=True draws the message in red (the point of the slide).
"""
import html

# Participant kinds: fill, stroke, text, type-line colour — the C4 palette of c4-structurizr's c4-google-tokens.dsl
# (blue ramp for the software, green for stores, grey for the outside, red for the one in focus).
KIND = {
    "person":     ("#174ea6", "#174ea6", "#ffffff", "#e8f0fe"),
    "system":     ("#4285f4", "#1967d2", "#ffffff", "#e8f0fe"),
    "container":  ("#8ab4f8", "#4285f4", "#202124", "#202124"),
    "db":         ("#188038", "#188038", "#ffffff", "#e6f4ea"),
    "queue":      ("#f8f9fa", "#202124", "#202124", "#5f6368"),
    "component":  ("#e8f0fe", "#4285f4", "#202124", "#5f6368"),
    "ext":        ("#5f6368", "#3c4043", "#ffffff", "#f8f9fa"),
    "ext_person": ("#3c4043", "#202124", "#ffffff", "#f8f9fa"),
    "focus":      ("#ea4335", "#c5221f", "#ffffff", "#fce8e6"),
}
FONT = "Inter, Roboto, sans-serif"


def wrap(text, width_px, size):
    per = max(6, int(width_px / (size * 0.53)))
    lines, cur = [], ""
    for w in str(text).split():
        if cur and len(cur) + 1 + len(w) > per:
            lines.append(cur); cur = w
        else:
            cur = f"{cur} {w}".strip()
    if cur:
        lines.append(cur)
    return lines

INK, RED, GREEN = "#202124", "#ea4335", "#34a853"

def esc(s): return html.escape(str(s))

class Seq:
    def __init__(self, width=1600, head=74, row=58, size=17, margin=30):
        self.W, self.head, self.row, self.size, self.m = width, head, row, size, margin
        self.parts, self.steps, self.frames = [], [], []
        self.n = 0

    def part(self, pid, label, kind="container"):
        self.parts.append((pid, label, kind))

    def msg(self, a, b, label, kind="sync", hl=False, num=True, colour=None):
        self.steps.append(("msg", a, b, label, kind, hl, num, colour))

    def ret(self, a, b, label, hl=False, colour=None):
        self.msg(a, b, label, "ret", hl, False, colour)

    def note(self, a, b, text, tone="amber"):
        self.steps.append(("note", a, b, text, tone))

    def gap(self, h=0.5):
        self.steps.append(("gap", h))

    def frame(self, kind, cond):
        self.steps.append(("frame", kind, cond))

    def end(self):
        self.steps.append(("end",))

    def svg(self):
        n = len(self.parts)
        colw = (self.W - 2 * self.m) / n
        xs = {p[0]: self.m + colw * (i + 0.5) for i, p in enumerate(self.parts)}
        boxw = min(colw - 18, 250)
        out, y = [], self.m + self.head + 48
        stack = []
        body = []
        for si, st in enumerate(self.steps):
            mark = len(body)
            if st[0] == "msg":
                _, a, b, label, kind, hl, num, colour = st
                col = colour or (RED if hl else (GREEN if kind == "ret" else INK))
                xa, xb = xs[a], xs[b]
                lines = wrap(label, max(abs(xb - xa) - 40, 260), self.size)
                lh = self.size * 1.2
                y += (len(lines) - 1) * lh
                dash = ' stroke-dasharray="7 5"' if kind == "ret" else ""
                mk = "sq-f" if kind == "sync" else "sq-o"
                if a == b:
                    body.append(f'<path d="M{xa},{y} h46 v26 h-44" fill="none" stroke="{col}" stroke-width="2"{dash} '
                                f'marker-end="url(#{mk}-{col[1:]})"/>')
                    tx, anchor = xa + 56, "start"; ty = y + 4
                    y += 26
                else:
                    body.append(f'<line x1="{xa}" y1="{y}" x2="{xb - (8 if xb > xa else -8)}" y2="{y}" stroke="{col}" '
                                f'stroke-width="2"{dash} marker-end="url(#{mk}-{col[1:]})"/>')
                    tx, anchor, ty = (xa + xb) / 2, "middle", y - 9
                if num:
                    self.n += 1
                    cx = xa + (14 if xb >= xa else -14)
                    r = max(12, self.size * 0.95); fs = max(13, self.size * 1.17)   # 2026-11-22: legible at 1080p when a tall sequence is scaled down
                    cx = xa - (r + 2) if xb >= xa else xa + r + 2   # outside the arrow start: labels sit over the arrow
                    body.append(f'<circle cx="{cx}" cy="{y}" r="{r:.1f}" fill="#ffffff" stroke="{col}" stroke-width="1.6"/>'
                                f'<text x="{cx}" y="{y+fs*0.36:.1f}" text-anchor="middle" font-family="{FONT}" font-size="{fs:.1f}" '
                                f'font-weight="700" fill="{col}">{self.n}</text>')
                for k, l in enumerate(lines):
                    body.append(f'<text x="{tx}" y="{ty - (len(lines)-1-k)*lh}" text-anchor="{anchor}" font-family="{FONT}" '
                                f'font-size="{self.size}" fill="{col}" font-weight="{600 if hl else 400}" '
                                f'paint-order="stroke" stroke="#ffffff" stroke-width="5" stroke-linejoin="round">{esc(l)}</text>')
                y += self.row
                body[mark:] = [f'<g data-k="s:{si}">' + "".join(body[mark:]) + "</g>"]
            elif st[0] == "note":
                _, a, b, text, tone = st
                bg, bd = {"amber": ("#fef7e0", "#fbbc05"), "blue": ("#e8f0fe", "#4285f4"),
                          "red": ("#fce8e6", "#ea4335"), "green": ("#e6f4ea", "#34a853")}[tone]
                x1, x2 = min(xs[a], xs[b]) - boxw / 2 + 6, max(xs[a], xs[b]) + boxw / 2 - 6
                lines = wrap(text, x2 - x1 - 24, self.size * 0.96)
                h = len(lines) * self.size * 1.22 + 16
                y -= self.row * 0.35
                body.append(f'<rect x="{x1}" y="{y}" width="{x2-x1}" height="{h}" rx="6" fill="{bg}" stroke="{bd}" stroke-width="1.4"/>')
                for k, l in enumerate(lines):
                    body.append(f'<text x="{(x1+x2)/2}" y="{y + 8 + self.size*(0.95 + 1.22*k)}" text-anchor="middle" '
                                f'font-family="{FONT}" font-size="{self.size*0.96:.1f}" fill="#202124">{esc(l)}</text>')
                y += h + self.row * 0.75
                body[mark:] = [f'<g data-k="s:{si}">' + "".join(body[mark:]) + "</g>"]
            elif st[0] == "gap":
                y += self.row * st[1]
            elif st[0] == "frame":
                stack.append((y - self.row * 0.62, st[1], st[2], len(body), si))
                y += self.row * 0.62
            elif st[0] == "end":
                y0, kind, cond, at, fi = stack.pop()
                x1, x2 = self.m + 4, self.W - self.m - 4
                lab = kind.upper(); fz = max(15, self.size * 0.95)
                body.insert(at, f'<g data-k="f:{fi}"><rect x="{x1}" y="{y0}" width="{x2-x1}" height="{y - y0 - self.row*0.45}" fill="#f8f9fa" '
                                f'fill-opacity="0.6" stroke="#5f6368" stroke-width="1.4" rx="4"/>'
                                f'<path d="M{x1},{y0} h{len(lab)*fz*0.75+26} v{fz*1.3:.0f} l-10,10 h{-(len(lab)*fz*0.75+16)} z" fill="#5f6368"/>'
                                f'<text x="{x1+10}" y="{y0+fz*1.1:.0f}" font-family="{FONT}" font-size="{fz:.1f}" font-weight="700" '
                                f'fill="#ffffff">{lab}</text>'
                                f'<text x="{x1+len(lab)*fz*0.75+40}" y="{y0+fz*1.1:.0f}" font-family="{FONT}" font-size="{fz:.1f}" '
                                f'font-style="italic" fill="#5f6368">[{esc(cond)}]</text></g>')
                y += self.row * 0.1
        H = y + self.m - self.row * 0.4
        for pid, label, kind in self.parts:
            x = xs[pid]; fill, stroke, fg, sub = KIND[kind]
            out.append(f'<g data-k="p:{pid}"><line x1="{x}" y1="{self.m + self.head}" x2="{x}" y2="{H - self.m}" stroke="#9aa0a6" '
                       f'stroke-width="1.5" stroke-dasharray="5 5"/>')
            lines = wrap(label, boxw - 20, self.size)
            out.append(f'<rect x="{x-boxw/2}" y="{self.m}" width="{boxw}" height="{self.head}" rx="8" fill="{fill}" '
                       f'stroke="{stroke}" stroke-width="1.6"/>')
            y0 = self.m + self.head / 2 - (len(lines) - 1) * self.size * 0.6 + self.size * 0.35
            for k, l in enumerate(lines):
                out.append(f'<text x="{x}" y="{y0 + k*self.size*1.2}" text-anchor="middle" font-family="{FONT}" '
                           f'font-size="{self.size}" font-weight="700" fill="{fg}">{esc(l)}</text>')
            out.append("</g>")
        cols = {RED, GREEN, INK} | {st[7] for st in self.steps if st[0] == "msg" and st[7]}
        defs = "".join(
            f'<marker id="sq-f-{c[1:]}" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="9" markerHeight="9" orient="auto">'
            f'<path d="M0,1 L10,5 L0,9 z" fill="{c}"/></marker>'
            f'<marker id="sq-o-{c[1:]}" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="9" markerHeight="9" orient="auto">'
            f'<path d="M0,1 L10,5 L0,9" fill="none" stroke="{c}" stroke-width="1.6"/></marker>' for c in cols)
        return (f'<svg xmlns="http://www.w3.org/2000/svg" class="seq" viewBox="0 0 {self.W} {H:.0f}" width="{self.W}" '
                f'height="{H:.0f}"><defs>{defs}</defs><rect width="{self.W}" height="{H:.0f}" fill="#ffffff"/>'
                + "".join(out) + "".join(body) + "</svg>")

    def units(self):
        """Default reveal order (2026-11-21, progressive disclosure): one unit per message or note, in time order.
        A participant appears with the first step that touches it; an alt/loop frame with its first inner step."""
        seen, out, pending = set(), [], []
        for si, st in enumerate(self.steps):
            if st[0] == "frame":
                pending.append(f"f:{si}"); continue
            if st[0] not in ("msg", "note"):
                continue
            keys = [f"p:{x}" for x in (st[1], st[2]) if x not in seen and not seen.add(x)] + pending + [f"s:{si}"]
            pending = []
            out.append(keys)
        rest = [f"p:{p[0]}" for p in self.parts if p[0] not in seen]
        if rest:
            out[0] = rest + out[0] if out else [rest]
        return out

    def save(self, path):
        import json, pathlib
        pathlib.Path(path).write_text(self.svg(), encoding="utf-8")
        pathlib.Path(path).with_suffix(".steps.json").write_text(json.dumps(self.units()), encoding="utf-8")
        return path
