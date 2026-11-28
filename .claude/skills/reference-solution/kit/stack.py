"""stack.json — the single source of each container's technology, how it is built one level down, the rivals rejected and
why, and each challenge's fix-slide rejection. Read by the slides (tech cards in chapter 4, the matrix in chapter 6), by
diagrams through workspace.dsl's technology lines, and — via the slides — by the generated Markdown.

    import stack; S = stack.load(ROOT)           # ROOT = the solution folder (holds stack.json)
    tech(**S.tech("log"))                       # dsl.tech() arguments: kicker, title, pick, how, rejected, cite
    S.say("log")                                # narration for that card, one reveal marker per row
    S.summary()                                 # rows: Container · Choice · Rejected · The deciding reason
    S.rej(2)                                    # (tool, why) for challenge 2's fix slide

Text is Markdown-lite: `code` and **bold**. Replaces the per-solution video/src/stack.py and its marker-region sync
(issue #5: the Markdown is generated, so no region is ever rewritten in place).
"""
import html as _h, json, pathlib, re


def html(s):
    s = _h.escape(s, quote=False)
    s = re.sub(r"`([^`]+)`", r"<code>\1</code>", s)
    return re.sub(r"\*\*([^*]+)\*\*", r"<b>\1</b>", s)


def say_text(s):
    s = re.sub(r"[`*]", "", s)
    for a, b in (("→", " to "), ("≈", "about "), ("×", " times "), ("≥", " at least "), ("≤", " at most "), (" / ", " or "), ("&", " and ")):
        s = s.replace(a, b)
    return re.sub(r"\s+", " ", s).strip()


class Stack:
    def __init__(self, root):
        self.root = pathlib.Path(root)
        self.data = json.loads((self.root / "stack.json").read_text(encoding="utf-8"))
        self.by_id = {s["id"]: s for s in self.data["stack"]}

    def tech(self, id_):
        s = self.by_id[id_]
        return dict(kicker=s["kicker"], title=html(s["title"]), pick=(html(s["pick"]), html(s["why"])), how=html(s["how"]),
                    rejected=[(html(n), html(w)) for n, w in s["rejected"]], cite=s.get("course"))

    def say(self, id_, P="[+]", full=False):
        """How it is built, why, then each rejected rival — the first clause of each unless full=True."""
        s = self.by_id[id_]
        cut = (lambda t: say_text(t)) if full else (lambda t: re.split(r"(?<=[.:;])\s", say_text(t))[0].rstrip(".:;") + ".")
        out = [P, "C: " + say_text(s["how"]), P, "C: Why: " + cut(s["why"])]
        for i, (n, w) in enumerate(s["rejected"]):
            out += [P, f"C: {'Rejected: ' if i == 0 else ''}{say_text(n)}. " + cut(w)]
        return out

    def summary(self):
        return [[html(c) for c in s["summary"]] for s in self.data["stack"] if s.get("summary")]

    def summary_say(self, P="[+]"):
        out = ["C: The stack on one slide, as I would leave it on the whiteboard."]
        for s in self.data["stack"]:
            if s.get("summary"):
                c, ch, rej, why = (say_text(x) for x in s["summary"])
                out += [P, f"C: {c}: {ch}. Not {rej}. {why[0].upper() + why[1:]}."]
        return out

    def rej(self, n):
        t, w = self.data["challenges"][str(n)]
        return html(t), html(w)


def load(root):
    return Stack(root)
