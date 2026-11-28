#!/usr/bin/env python3
"""The scenario card: fresh numbers and an unpredictable interviewer for every round.

Cue sheets carry one fixed set of figures (2M applications a month, peak 10x, $1 a pull …). A
candidate who studies the reference solution memorises them, and a round that hands back the same
figures tests recall instead of reasoning. This script draws a *variation* of the question once per
round, stores it in .scenario.json (gitignored), and prints a brief the interviewer follows:

  * every volume figure in the sheet scaled by one random factor (ratios between them hold),
    money, durations and percentages jittered independently, derived figures ("≈ 8/s") removed;
  * an answer style per fact — precise, rough, or "you pick" — the way real interviewers answer;
  * an interviewer persona, the probes to use (sampled and shuffled), the curveball and its timing,
    and sometimes one twist constraint that changes the design;
  * an arithmetic key, so the interviewer can check the candidate's order of magnitude without
    reaching for the sheet's figures.

    scripts/scenario.py new SD-82 [--mode blitz|full|hld|framing|wrap|deep-dive|grill|review]
                                  [--session certifying|practice] [--difficulty gentle|standard|brutal]
                                  [--numbers varied|sheet] [--seed N]
    scripts/scenario.py show            # the whole interviewer brief again
    scripts/scenario.py facts           # only the clarification answers (prompt + fact table)
    scripts/scenario.py prompt          # only the read-aloud prompt for this round
    scripts/scenario.py clear           # delete .scenario.json (archive time)

Stdlib only. The card is for the interviewer: never paste it, or its existence, to the candidate.
"""
import argparse
import json
import math
import pathlib
import random
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
STATE = ROOT / ".scenario.json"
QUESTIONS = ROOT / "questions"

# ── variation ranges ─────────────────────────────────────────────────────────────────────────────
VOLUME_FACTORS = [0.05, 0.1, 0.2, 0.3, 0.5, 3, 5, 10, 20, 50]     # never 1: the sheet's scale is the one they studied
MONEY_FACTORS = [0.4, 0.5, 0.7, 1.5, 2, 3]
TIME_FACTORS = [0.5, 0.6, 0.75, 1.5, 2]
PERCENT_FACTORS = [0.3, 0.5, 2, 3]
PEAK_RATIOS = [2, 3, 4, 5, 8, 15, 20, 30]

PERSONAS = {
    "terse": "Short sentences, few words, long silences. Answers in five words or fewer. Never fills a pause. "
             "Says 'Okay.' and waits.",
    "curious": "Asks 'why' about small details the candidate mentions in passing — a field name, a timeout, a "
               "default — then returns to the main line. Pick one such detail per phase.",
    "skeptical": "Questions one confident claim per phase: 'How sure are you about that?' / 'What makes you "
                 "think that holds?' Even when the claim is right. Holding ground with reasons is the good answer.",
    "hurried": "Visibly short on time. Moves the candidate on early (at ~80% of a phase budget), asks for the "
               "short version, interrupts a long explanation once: 'Let me stop you there — what's the decision?'",
    "product-minded": "Frames probes through the user and the business: 'What does the customer see?', 'What does "
                      "that cost us?', 'Would the product owner accept that?'",
    "quiet-then-sharp": "Lets the candidate run through requirements and design almost without comment, then in "
                        "deep dives asks the hardest probe first and goes two levels down fast.",
}

GENERIC_CURVEBALLS = [
    "Traffic is ten times what you sized for, starting next month. What changes first?",
    "Legal says data about users in one region must now stay in that region. What moves?",
    "Your most critical dependency is down for thirty minutes at peak. Walk me through those thirty minutes.",
    "Finance wants the running cost cut in half this year. What do you give up?",
    "We need this in a second region for availability. What changes, and what does it cost?",
    "A bad deploy has been writing wrong data for two hours before anyone noticed. What now?",
    "Half the team is moved to another project. What do you still ship, and what do you drop?",
]

TWISTS = [
    "Team: {n} engineers, first version live in {m} months.",
    "Budget: finance will ask what this costs per month; the target is half of the obvious design. Say what you give up.",
    "Traffic shape: about {p}% of each day's volume arrives in a single two-hour window.",
    "Availability: the business wants {nines} for the core path, and says it is non-negotiable.",
    "Geography: users are split across {r} regions, each must keep working if another one is down.",
    "Existing estate: one relational database and a small ops team already run everything else; adding a new "
    "kind of datastore needs a strong reason.",
]

WRAP_QUESTIONS = [
    "What breaks first as this grows?",
    "How would you know, in production, before a customer tells you?",
    "What does this cost to run, roughly, and what's the biggest line item?",
    "What did you trade away that you're least comfortable with?",
]

# probes per mode: (requirements, deep-dive targets, wrap questions besides the summary)
PROBE_BUDGET = {
    "blitz": (1, 2, 1), "full": (2, 3, 4), "hld": (2, 0, 0), "framing": (1, 0, 0),
    "wrap": (0, 0, 4), "deep-dive": (0, 4, 0), "grill": (0, 8, 0), "review": (0, 0, 0),
}

# ── cue-sheet parsing ────────────────────────────────────────────────────────────────────────────


def find_section(qid):
    pat = re.compile(rf"^### {re.escape(qid)} · ")
    for f in sorted(QUESTIONS.glob("*.md")):
        lines = f.read_text().splitlines()
        for i, l in enumerate(lines):
            if pat.match(l):
                out = [l]
                for l2 in lines[i + 1:]:
                    if l2.startswith("### ") or l2.startswith("## "):
                        break
                    out.append(l2)
                return f, "\n".join(out)
    sys.exit(f"scenario: {qid} not found in questions/*.md")


def block(section, label):
    """Text after a bold label (e.g. '**Crux.**') up to the next bold label or rule."""
    m = re.search(rf"^\*\*{re.escape(label)}[^\n]*", section, re.M)
    if not m:
        return ""
    rest = section[m.start():].split("\n")
    out = [rest[0]]
    for l in rest[1:]:
        if re.match(r"^\*\*[A-Z]", l) or l.startswith("---"):
            break
        out.append(l)
    text = "\n".join(out)
    return re.sub(rf"^\*\*{re.escape(label)}[^*]*\*\*:?\s*", "", text).strip()


def facts_of(section):
    """[(question, answer)] from 'If they ask' / 'Context if asked' tables, or a 'Numbers if asked' paragraph."""
    for label in ("If they ask", "Context if asked", "Numbers if asked"):
        b = block(section, label)
        if not b:
            continue
        rows = [l for l in b.splitlines() if l.startswith("|") and not re.match(r"^\|[-\s|:]+\|$", l)]
        if rows:
            pairs = []
            for r in rows[1:]:  # skip header
                cells = [c.strip() for c in r.strip("|").split("|")]
                if len(cells) >= 2:
                    pairs.append((cells[0], " | ".join(cells[1:])))
            return pairs
        text = " ".join(b.split())
        parts = [p.strip() for p in re.split(r",\s+(?![^()]*\))|;\s+", text.rstrip(".")) if p.strip()]
        return [("(numbers if asked)", p) for p in parts]
    return []


def split_dots(text):
    return [p.strip(" .") for p in re.split(r"\s+·\s+", " ".join(text.split())) if p.strip(" .")]


def probes_of(section):
    """{'requirements': [...], 'estimation': [...], 'design': [...], 'deep': [...], 'bar': [...]}."""
    out = {k: [] for k in ("requirements", "estimation", "design", "deep", "bar")}
    ladder = block(section, "Probe ladder")
    if ladder:
        cur = None
        for l in ladder.splitlines():
            m = re.match(r"^-\s*\*([^*:]+):?\*:?\s*(.*)", l.strip())
            if m:
                name = m.group(1).lower()
                cur = ("requirements" if name.startswith("req") else "estimation" if name.startswith("est")
                       else "design" if name.startswith("design") else "deep" if name.startswith("deep")
                       else "bar")
                out[cur].append(m.group(2))
            elif cur and l.strip():
                out[cur][-1] += " " + l.strip()
        for k in out:
            out[k] = [p for chunk in out[k] for p in split_dots(chunk)]
    else:
        for p in split_dots(block(section, "Probes")):
            (out["bar"] if "EM bar" in p or "Staff bar" in p else out["deep"]).append(p)
    def clean(p):
        p = re.sub(r"\s+", " ", p.replace("**", "")).strip()
        p = re.sub(r"\s*\((?!EM|Staff)[^)]*\)\s*$", "", p)          # trailing answer hints: the numbers changed
        p = re.sub(r"^\*?\((?:EM|Staff)[^)]*\)\*?\s*", "", p)
        return p.strip(" *").strip('"').strip()
    return {k: [clean(p) for p in v] for k, v in out.items()}


def curveball_of(section):
    b = block(section, "Curveball")
    m = re.search(r"\*\"?(.+?)\"?\*", b)
    return (m.group(1) if m else b.split("\n")[0]).strip(' "*').strip('"') if b else ""


def drips_of(section):
    b = block(section, "Drips")
    return [re.sub(r"^\s*[-\d.]+\s*", "", l).strip() for l in b.splitlines() if l.strip().startswith(("-", "1", "2", "3"))]


# ── number transformation ────────────────────────────────────────────────────────────────────────

SUFFIX = {"k": 1e3, "K": 1e3, "M": 1e6, "m": 1e6, "B": 1e9, "bn": 1e9, "billion": 1e9, "million": 1e6,
          "thousand": 1e3, "T": 1e12, "trillion": 1e12}
SIZE = {"B": 1, "KB": 1e3, "MB": 1e6, "GB": 1e9, "TB": 1e12, "PB": 1e15, "EB": 1e18}
TIME_UNITS = r"(?:ms|milliseconds?|µs|us|s|sec|secs|seconds?|min|mins|minutes?|h|hrs?|hours?|days?|weeks?|months?|years?|yrs?)"
RATE_TAIL = r"(?:\s*(?:/|per\s+|a\s+|an\s+|each\s+)(?:s\b|sec|second|min|minute|hour|h\b|day|week|month|year))"

NUM = r"(\d[\d,]*(?:\.\d+)?)"
TOKEN = re.compile(
    rf"(?P<money>\$)?{NUM}\s?(?P<suf>bn|billion|million|thousand|trillion|[kKMBT](?![a-zA-Z]))?"
    rf"(?P<size>\s?(?:[KMGTPE]B|B)(?![a-zA-Z]))?(?P<pct>\s?%)?"
    rf"(?P<mult>\s?[×x](?![a-zA-Z]))?"
    rf"(?P<time>[\s-]?{TIME_UNITS}(?![a-zA-Z]))?"
    rf"(?P<rate>{RATE_TAIL})?")


def nice(v):
    """Round to a figure a person would say: 1–2 significant digits."""
    if v == 0:
        return 0
    e = math.floor(math.log10(abs(v)))
    lead = v / 10 ** e
    lead = round(lead) if lead >= 3 else round(lead * 2) / 2
    return lead * 10 ** e


WORDS = {"thousand": 1e3, "million": 1e6, "billion": 1e9, "trillion": 1e12}


def fmt_count(v, word=None):
    v = nice(v)
    table = ((" billion", 1e9), (" million", 1e6), (" thousand", 1e3)) if word else (("B", 1e9), ("M", 1e6), ("k", 1e3))
    for s, f in table:
        if v >= f:
            return f"{v / f:g}{s}"
    return f"{v:,.0f}" if v >= 1 else f"{v:.2g}"


def fmt_size(v, sp=" "):
    v = nice(v)
    for s in ("EB", "PB", "TB", "GB", "MB", "KB"):
        if v >= SIZE[s]:
            return f"{v / SIZE[s]:g}{sp}{s}"
    return f"{v:g}{sp}B"


def fmt_money(v):
    v = nice(v)
    if v >= 1e9:
        return f"${v / 1e9:g}B"
    if v >= 1e6:
        return f"${v / 1e6:g}M"
    if v >= 1e4:
        return f"${v / 1e3:g}k"
    if v >= 100:
        return f"${v:,.0f}"
    return f"${v:g}" if v >= 1 else f"${v:.2f}"


def fmt_plain(v, decimals):
    v = nice(v)
    return f"{v:,.{decimals}f}" if decimals else f"{v:,.0f}" if v >= 10 else f"{v:g}"


def largest_count(texts):
    best = 0
    for t in texts:
        for m in re.finditer(r"(\d[\d,]*(?:\.\d+)?)\s?(thousand|million|billion|[kMB])\b(?!\s?B)", words_to_digits(t)):
            best = max(best, float(m.group(1).replace(",", "")) * MULT[m.group(2)])
    return best


class Varier:
    def __init__(self, rng, enabled, biggest=0):
        self.rng, self.enabled = rng, enabled
        # keep the round plausible: a sheet already at a billion users is scaled down or sideways, not 50× up
        ok = [f for f in VOLUME_FACTORS if biggest * f <= 3e9] or [0.1, 0.3, 0.5]
        self.volume = rng.choice(ok)
        self.peak = None
        self.changes = []          # (original, new, kind)
        self.rates = []            # (new value per unit, unit)

    def factor(self, kind):
        return {"money": MONEY_FACTORS, "time": TIME_FACTORS, "pct": PERCENT_FACTORS}[kind]

    def sub(self, m):
        tok = m.group(0)
        raw = m.group(2)
        try:
            base = float(raw.replace(",", ""))
        except ValueError:
            return tok
        g = m.groupdict()
        decimals = len(raw.split(".")[1]) if "." in raw else 0
        sufw = (g["suf"] or "").strip()
        val = base * SUFFIX.get(sufw, 1)
        s0 = m.start()
        rest_from = lambda grp: tok[m.end(grp) - s0:] if m.group(grp) else None
        core_end = "suf" if g["suf"] else 2
        if g["mult"]:                                   # "~10×" peak ratios
            kind = "ratio"
            r = self.rng.choice(PEAK_RATIOS)
            self.peak = self.peak or r
            new = tok[: m.start(2) - s0] + str(r) + tok[m.end(2) - s0:]
        elif g["pct"]:
            kind = "pct"
            nv = (self.rng.choice(["99.9", "99.95", "99.99", "99.999"]) if base >= 99
                  else f"{min(95, nice(base * self.rng.choice(PERCENT_FACTORS))):g}")
            new = tok[: m.start(2) - s0] + nv + tok[m.end(2) - s0:]
        elif g["money"]:
            kind = "money"
            new = fmt_money(val * self.rng.choice(MONEY_FACTORS)) + tok[m.end(core_end) - s0:]
        elif g["size"]:
            unit = g["size"].strip()
            bytes_ = val * SIZE[unit]
            f = self.volume if (g["rate"] or bytes_ >= 1e12) else self.rng.choice(TIME_FACTORS)
            kind = "volume" if f == self.volume else "size"
            sp = " " if g["size"].startswith(" ") or (g["suf"] or "").endswith(" ") else ""
            new = fmt_size(bytes_ * f, sp) + tok[m.end("size") - s0:]
        elif g["time"]:
            if g["rate"]:
                return tok
            kind = "time"
            new = fmt_plain(base * self.rng.choice(TIME_FACTORS), decimals) + tok[m.end(2) - s0:]
        elif g["suf"] or g["rate"] or val >= 1000:
            kind = "volume"
            nv = val * self.volume
            if re.match(r"\s*(?:\w+\s)?(?:users|people|customers|members|subscribers|accounts|devices|drivers|riders)",
                        m.string[m.end():m.end() + 30]):
                nv = min(nv, 3e9)                       # nobody has more users than there are people online
            new = fmt_count(nv, sufw if sufw in WORDS else None) + tok[m.end(core_end) - s0:]
            if g["rate"]:
                self.rates.append((nice(nv), g["rate"].strip()))
        else:
            return tok                                  # small plain integers (2 bureaus, 30 holdings) stay
        if new != tok:
            self.changes.append((tok.strip(), new.strip(), kind))
        return new

    def vary(self, text):
        if not self.enabled:
            return text
        text = words_to_digits(text)
        text = re.sub(r"\s*\((?:≈|~|about|roughly)[^)]*\d[^)]*\)", "", text)   # derived figures: candidate computes
        text = re.sub(r"\s*\(≈[^)]*\)", "", text)
        return TOKEN.sub(self.sub, text)


SMALL = {w: i for i, w in enumerate("zero one two three four five six seven eight nine ten eleven twelve".split())}
SMALL.update({"twenty": 20, "thirty": 30, "forty": 40, "fifty": 50, "hundred": 100, "a": 1, "one hundred": 100,
              "a hundred": 100, "a few hundred": 300, "several hundred": 500})


def words_to_digits(text):
    """'ten thousand services' → '10 thousand services', so the prompt's figures vary with the facts."""
    keys = sorted(SMALL, key=len, reverse=True)
    pat = re.compile(rf"\b({'|'.join(map(re.escape, keys))})\s+(thousand|million|billion)\b", re.I)
    return pat.sub(lambda m: f"{SMALL[m.group(1).lower()]:g} {m.group(2).lower()}", text)


PER_SECOND = {"s": 1, "sec": 1, "second": 1, "min": 60, "minute": 60, "h": 3600, "hour": 3600,
              "day": 86400, "week": 604800, "month": 2.6e6, "year": 3.15e7}


def fmt_rate(x):
    return fmt_count(x) if x >= 10 else f"{x:.2g}"


RATE_IN_TEXT = re.compile(
    r"(\d[\d,]*(?:\.\d+)?)\s?(thousand|million|billion|[kMB])?\b\s*([a-zA-Z][\w\- ]{0,30}?)?\s*"
    r"(?:/|per\s+|a\s+|an\s+|each\s+)(s|sec|second|min|minute|hour|h|day|week|month|year)\b")
MULT = {"k": 1e3, "M": 1e6, "B": 1e9, "thousand": 1e3, "million": 1e6, "billion": 1e9, None: 1}


def arithmetic_key(texts, peak):
    """Every '<count> <thing>/<period>' in the round's facts, as an average and a peak per second."""
    out, seen = [], set()
    for t in texts:
        for m in RATE_IN_TEXT.finditer(t):
            n = float(m.group(1).replace(",", "")) * MULT[m.group(2)]
            if n < 10 and m.group(4) in ("s", "sec", "second"):
                continue
            what, per = (m.group(3) or "").strip(), m.group(4)
            sec = {"s": 1, "sec": 1, "h": 3600}.get(per) or PER_SECOND[per]
            key = (n, what, sec)
            if key in seen:
                continue
            seen.add(key)
            avg = n / sec
            line = f"{fmt_count(n)} {what} per {per} ≈ {fmt_rate(avg)}/s average".replace("  ", " ")
            if peak and sec > 1:
                line += f" → ≈ {fmt_rate(avg * peak)}/s at the {peak:g}× peak"
            out.append(line)
    return out


# ── answer styles ────────────────────────────────────────────────────────────────────────────────


def styles(rng, n, difficulty):
    w = {"gentle": (1, 0, 0), "standard": (0.6, 0.25, 0.15), "brutal": (0.35, 0.3, 0.35)}[difficulty]
    return rng.choices(["precise", "rough", "you-pick"], weights=w, k=n)


def rough_words(n):
    """300000 → 'a few hundred thousand'; 6e6 → 'a few million'; 3e7 → 'tens of millions'."""
    if n < 100:
        return None
    e = int(math.floor(math.log10(n)))
    unit_e = min(9, (e // 3) * 3)
    unit = {0: "", 3: "thousand", 6: "million", 9: "billion"}[unit_e]
    d, lead = e - unit_e, n / 10 ** e
    if d == 0:
        w = f"about a {unit}" if lead < 1.5 else f"a couple of {unit}" if lead < 2.5 else f"a few {unit}"
    elif d == 1:
        w = f"tens of {unit}s" if unit else "tens"
    else:
        w = f"a few hundred {unit}" if lead < 5 else f"several hundred {unit}"
    return w.strip()


def roughen(ans):
    """'6M applications/month' → 'a few million applications/month'; returns None if nothing to roughen."""
    m = re.search(r"(~|≈|about\s+)?(\$)?(\d[\d,]*(?:\.\d+)?)\s?(thousand|million|billion|[kMB])\b", ans)
    if not m:
        return None
    n = float(m.group(3).replace(",", "")) * {"k": 1e3, "M": 1e6, "B": 1e9, "thousand": 1e3,
                                              "million": 1e6, "billion": 1e9}[m.group(4)]
    w = rough_words(n)
    if not w:
        return None
    w = ("some " if m.group(2) else "") + w + (" dollars" if m.group(2) else "")
    return ans[: m.start()] + w + ans[m.end():]


# ── the card ─────────────────────────────────────────────────────────────────────────────────────


def build(a):
    seed = a.seed if a.seed is not None else random.SystemRandom().randrange(10 ** 6)
    rng = random.Random(seed)
    path, sec = find_section(a.qid)
    title = sec.splitlines()[0][4:].split("[")[0].split(" · ", 1)[-1].strip()
    v = Varier(rng, a.numbers == "varied",
               largest_count([block(sec, "Read aloud")] + [ans for _, ans in facts_of(sec)]))

    prompt = v.vary(" ".join(block(sec, "Read aloud").split()).strip("*\" "))
    raw_facts = facts_of(sec)
    facts = [(q.replace("**", ""), v.vary(ans).replace("**", "")) for q, ans in raw_facts]
    st = styles(rng, len(facts), a.difficulty)
    fact_rows = []
    for (q, ans), s in zip(facts, st):
        has_num = bool(re.search(r"\d", ans))
        if s == "you-pick" and has_num:
            say = "Not pinned down yet — pick a number you can defend and tell me why."
        elif s == "rough" and roughen(ans):
            say = roughen(ans)
        else:
            s, say = "precise", ans
        fact_rows.append({"q": q, "truth": ans, "style": s, "say": say})

    probes = {k: [v.vary(x) for x in xs] for k, xs in probes_of(sec).items()}
    nreq, ndeep, nwrap = PROBE_BUDGET[a.mode]
    pick = lambda xs, k: rng.sample(xs, min(k, len(xs))) if xs else []
    req = pick(probes["requirements"], nreq)
    deep_pool = probes["deep"] + (probes["bar"] if a.mode in ("grill", "deep-dive") else [])
    deep = pick(deep_pool, ndeep)
    bar = pick(probes["bar"], 1 if a.mode in ("blitz", "full", "wrap") else 0)
    wrap = (rng.sample(WRAP_QUESTIONS, min(nwrap, 4)) if nwrap < 4 else list(WRAP_QUESTIONS)) if nwrap else []

    sheet_cb = curveball_of(sec)
    roll = rng.random()
    if a.difficulty == "gentle" or a.mode in ("framing", "hld", "wrap", "review"):
        curveball = None
    elif sheet_cb and roll < 0.45:
        curveball = {"text": v.vary(sheet_cb), "source": "sheet"}
    elif roll < 0.75 and probes["deep"]:
        rest = [p for p in probes["deep"] if p not in deep] or probes["deep"]
        curveball = {"text": rng.choice(rest), "source": "sheet probe used as curveball"}
    else:
        curveball = {"text": rng.choice(GENERIC_CURVEBALLS), "source": "generic"}
    if curveball:
        curveball["at"] = f"{rng.randint(35, 80)}% through the deep-dive phase"
    curveballs = [curveball] if curveball else []
    if a.difficulty == "brutal" and curveball:
        curveballs.append({"text": rng.choice(GENERIC_CURVEBALLS), "source": "generic (brutal: second)",
                           "at": "in the wrap, before the summary"})

    twist = None
    if a.numbers == "varied" and a.mode not in ("framing",) and rng.random() < (0.5 if a.difficulty != "gentle" else 0):
        t = rng.choice(TWISTS)
        twist = t.format(n=rng.choice([3, 4, 6, 8, 12]), m=rng.choice([2, 3, 4, 6]), b=rng.choice([5, 10, 20, 50, 150]),
                         p=rng.choice([30, 40, 60]), nines=rng.choice(["99.9%", "99.95%", "99.99%"]),
                         r=rng.choice([2, 3]))

    persona = rng.choice(list(PERSONAS))
    if a.mode == "grill":
        persona = "skeptical"

    card = {
        "seed": seed, "qid": a.qid, "title": title, "sheet": str(path.relative_to(ROOT)),
        "session": a.session, "mode": a.mode, "difficulty": a.difficulty, "numbers": a.numbers,
        "volume_factor": v.volume if a.numbers == "varied" else 1,
        "prompt": prompt, "twist": twist, "facts": fact_rows,
        "changes": v.changes, "arithmetic_key": arithmetic_key([f[1] for f in facts] + [prompt], v.peak or sheet_peak(facts)),
        "persona": persona, "persona_rules": PERSONAS[persona],
        "probes": {"requirements": req, "deep_dive_targets": deep, "em_bar": bar, "wrap": wrap,
                   "estimation": pick(probes["estimation"], 1), "design": pick(probes["design"], 1)},
        "curveballs": curveballs, "drips": [v.vary(d) for d in drips_of(sec)],
        "moves": unpredictable_moves(rng, a.mode),
    }
    STATE.write_text(json.dumps(card, indent=2, ensure_ascii=False))
    return card


def sheet_peak(facts):
    for _, ans in facts:
        m = re.search(r"(\d+(?:\.\d+)?)\s?[×x]\b", ans)
        if m:
            return float(m.group(1))
    return None


def unpredictable_moves(rng, mode):
    """Small, realistic deviations so two rounds of the same question never run the same way."""
    pool = [
        "Let one gate pass with only 'Okay, keep going.' — no probe — and spend the saved probe in deep dives.",
        "Once, ask the candidate to choose the next deep-dive target themselves: 'Where would you go next?'",
        "Once, ask about a detail they mentioned in passing (a timeout, a key, a default) instead of the planned probe.",
        "Start deep dives with the last target on your list, not the first.",
        "Once, interrupt a long explanation: 'Let me stop you — what's the decision?'",
        "Once, ask for a number the candidate has not computed: 'Roughly how many of those per second at peak?'",
        "Ask the walk-through for an unhappy path (a retry, a failure) instead of the happy one.",
    ]
    k = {"blitz": 2, "full": 3}.get(mode, 1)
    return rng.sample(pool, k)


def render(card, only=None):
    p = []
    say = lambda *x: p.append(" ".join(str(i) for i in x))
    if only in (None, "prompt", "facts"):
        say(f"PROMPT — read aloud verbatim:\n  \"{card['prompt']}\"")
        if card["twist"]:
            say(f"  + add as the last sentence of the prompt: \"{card['twist']}\"")
        if only == "prompt":
            return "\n".join(p)
        say("\nFACTS — answer clarifying questions with the 'say' column, in the persona's voice:")
        for f in card["facts"]:
            say(f"  [{f['style']:>8}] {f['q']}\n             say:   {f['say']}")
            if f["style"] != "precise":
                say(f"             truth: {f['truth']}   (use if they push, or for your own arithmetic)")
        say("  Anything not listed: invent a plain answer, consistent with the figures above, and write it in §0.")
        if only == "facts":
            return "\n".join(p)
    head = (f"SCENARIO {card['qid']} · {card['title']}\n"
            f"  seed {card['seed']} · {card['session']} · {card['mode']} · {card['difficulty']} · numbers "
            f"{card['numbers']}" + (f" (volume ×{card['volume_factor']:g})" if card['numbers'] == 'varied' else ""))
    p.insert(0, head + "\n")
    if card["changes"]:
        say("\nWHAT MOVED vs the cue sheet (yours only — the sheet's conclusions may no longer hold):")
        for o, n, k in card["changes"]:
            say(f"  {o:>22}  →  {n:<22} [{k}]")
    if card["arithmetic_key"]:
        say("\nARITHMETIC KEY (orders of magnitude to check theirs against; never read it out):")
        for l in card["arithmetic_key"]:
            say("  " + l)
    say(f"\nPERSONA: {card['persona']} — {card['persona_rules']}")
    pr = card["probes"]
    say("\nPROBES — use these, in this order; one per message:")
    for k in ("requirements", "estimation", "design", "deep_dive_targets", "em_bar", "wrap"):
        for x in pr.get(k, []):
            say(f"  {k:<18} {x}")
    say("  wrap (always)      Summarise the design in four sentences.")
    for c in card["curveballs"]:
        say(f"\nCURVEBALL ({c['source']}; {c['at']}):\n  \"{c['text']}\"")
    if card["drips"]:
        say("\nDRIPS (format drip only; #2 at ~40% of the clock, #3 at ~55%):")
        for i, d in enumerate(card["drips"], 2):
            say(f"  #{i} {d}")
    say("\nUNPREDICTABLE MOVES — do each once, at a moment of your choosing:")
    for m in card["moves"]:
        say("  - " + m)
    say("\nRULE: never state a figure from the cue sheet that is not in this card. Judge the candidate's "
        "decisions against THESE numbers.")
    return "\n".join(p)


def main():
    ap = argparse.ArgumentParser(description="design-room scenario card")
    sub = ap.add_subparsers(dest="cmd", required=True)
    n = sub.add_parser("new")
    n.add_argument("qid", help="bank ID, e.g. SD-82")
    n.add_argument("--mode", default="full", choices=list(PROBE_BUDGET))
    n.add_argument("--session", default="certifying", choices=["certifying", "practice"])
    n.add_argument("--difficulty", default="standard", choices=["gentle", "standard", "brutal"])
    n.add_argument("--numbers", default="varied", choices=["varied", "sheet"])
    n.add_argument("--seed", type=int)
    for c in ("show", "facts", "prompt", "clear"):
        sub.add_parser(c)
    a = ap.parse_args()
    if a.cmd == "new":
        a.qid = a.qid.upper()
        print(render(build(a)))
        return
    if a.cmd == "clear":
        STATE.unlink(missing_ok=True)
        print("scenario cleared")
        return
    if not STATE.exists():
        sys.exit("scenario: none — run `scripts/scenario.py new SD-nn`")
    card = json.loads(STATE.read_text())
    print(render(card, None if a.cmd == "show" else a.cmd))


if __name__ == "__main__":
    main()
