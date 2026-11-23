#!/usr/bin/env python3
"""Export reader-friendly review files from src/chNN.txt: per-episode transcripts, the list of key-thesis inserts,
the diagram index and stats.  Run:  python3 theory/sre-video/export_review.py   → theory/sre-video/review/
The sources in src/ stay the single source of truth; nothing in review/ is edited by hand."""
import json, pathlib, re

HERE = pathlib.Path(__file__).resolve().parent
SRC, OUT = HERE / "src", HERE / "review"
VOICE = {"N": "COACH", "V": "SAY THIS", "I": "INTERVIEWER", "C": "CANDIDATE", "E": "ASIDE"}
SPEECH = re.compile(r"^([NVICE]): (.+)$")


def clean(s):
    return re.sub(r"\*\*|==|`", "", s)


def parse(text):
    slides, cur, section = [], None, ""
    for raw in text.splitlines():
        line = raw.rstrip()
        if line.startswith("#!") or not line.strip():
            continue
        if line.startswith("## "):
            section = line[3:]
            continue
        if line.startswith("= "):
            parts = [p.strip() for p in re.split(r"(?<!\\)\|", line[2:])]
            head = parts[0].split()
            cur = dict(type=head[0], flags=head[1:], fields=parts[1:], body=[], speech=[], section=section)
            slides.append(cur)
            continue
        m = SPEECH.match(line)
        if m and cur is not None:
            cur["speech"].append((m.group(1), m.group(2)))
            continue
        if line.startswith("[pause") and cur is not None:
            cur["speech"].append(("P", line))
            continue
        if line.strip() == "[reveal]" and cur is not None:
            cur["speech"].append(("P", "[reveal: the rest of the slide fades in]"))
            continue
        if line.strip() == "+++":
            continue
        if line.startswith("@ "):
            continue
        if cur is not None:
            cur["body"].append(line.strip())
    return slides


def words(slide):
    return sum(len(t.split()) for v, t in slide["speech"] if v in VOICE)


def main():
    OUT.mkdir(exist_ok=True)
    stats, inserts, dia_index = [], [], []
    for p in sorted(SRC.glob("ch*.txt")):
        nn = p.stem[2:]
        text = p.read_text(encoding="utf-8")
        meta = dict(re.findall(r"^#!\s*(\w+):\s*(.+)$", text, re.M))
        slides = parse(text)
        # a probe slide speaks its question (INTERVIEWER) then the answer; the builder adds the question line
        n_words = n_pause = n_v = n_probe = n_dia = 0
        md = [f"# Episode {int(nn)} · {meta.get('title', '')}", "",
              f"Reader transcript generated from `src/ch{nn}.txt`. Voices: **COACH** narrates; **SAY THIS** is the slower key-line voice;"
              " **INTERVIEWER** and **CANDIDATE** play the probe drills; **ASIDE** is a fifth voice for traps, stories and the then-and-now panels. `[pause]` is silence in seconds; `[reveal]` is where the rest of the slide fades in. Each section also gets an automatic title card and a one-second pause. On-screen text is shown as quoted lines.", ""]
        sec = None
        k = 0
        for s in slides:
            k += 1
            if s["section"] != sec:
                sec = s["section"]
                if sec:
                    md += [f"\n## {sec}\n"]
            f = s["fields"]
            kicker = clean(f[0]) if f else ""
            title = clean(f[1]) if len(f) > 1 else ""
            tag = s["type"] + (" · " + " ".join(s["flags"]) if s["flags"] else "")
            if s["type"] == "probe":
                title, kicker = clean(f[0]), "Interviewer probe"
                n_probe += 1
            md.append(f"### Slide {k} · {kicker}" + (f" — {title}" if title else "") + f"   `[{tag}]`")
            if s["type"] == "dia":
                n_dia += 1
                name = s["body"][0].strip() if s["body"] else "?"
                md.append(f"*Diagram:* `svg/{name}.svg`")
                dia_index.append((nn, k, name, title or kicker))
            elif s["type"] == "probe":
                md.append(f"**INTERVIEWER:** {title}")
                n_words += len(title.split())
                md.append("*A strong answer on screen:*")
                md += [f"> {clean(b)}" for b in s["body"]]
            else:
                body = [b for b in s["body"] if not (s["type"] == "dia")]
                if s["type"] == "th" and len(f) > 2:
                    md.append(f"> {clean(f[2])}")
                for b in body:
                    md.append(f"> {clean(b)}")
            aside = s["type"] == "panel" and any(f in ("trap", "watch", "now", "new") for f in s["flags"])
            for v, t in s["speech"]:
                if v == "N" and (aside or re.match(r"^(A story|Here are three stories)", t)): v = "E"
                if v == "P":
                    md.append(f"*{t}*")
                    if "pause" in t: n_pause += float(re.search(r"([\d.]+)", t).group(1))
                    continue
                md.append(f"**{VOICE[v]}:** {clean(t)}")
                n_words += len(t.split())
                if v == "V":
                    n_v += 1
                    inserts.append((int(nn), meta.get("title", ""), k, kicker, clean(t)))
            md.append("")
        est = round((n_words * 0.43 + n_pause * 0.6) / 60, 1)
        (OUT / f"Ep{int(nn):02d}-transcript.md").write_text("\n".join(md) + "\n", encoding="utf-8")
        stats.append(dict(ep=int(nn), title=meta.get("title", ""), slides=len(slides), words=n_words, est_min=est,
                          thesis_inserts=n_v, probes=n_probe, diagrams=n_dia))
    (OUT / "stats.json").write_text(json.dumps(stats, indent=1), encoding="utf-8")
    ti = ["# Key-thesis inserts", "",
          "Every line below is spoken by the **SAY THIS** voice (slower, a different voice from the narrator), which breaks up long",
          "stretches of one voice and gives the viewer the sentence to repeat in an interview. Review these first: if a thesis is",
          "wrong or weak, the episode is wrong or weak.", ""]
    cur = None
    for ep, title, k, kicker, t in inserts:
        if ep != cur:
            ti += [f"\n## Episode {ep} · {title}\n"]
            cur = ep
        ti.append(f"- **{kicker}** (slide {k}): {t}")
    (OUT / "THESIS-INSERTS.md").write_text("\n".join(ti) + "\n", encoding="utf-8")
    di = ["# Diagram index", "", "Drawn by `diagrams_sre.py` into `svg/`. Illustrative numbers are labelled on the figure.", "",
          "| Episode | Slide | Figure | Slide title |", "|---|---|---|---|"]
    di += [f"| {int(e)} | {k} | `{n}.svg` | {t} |" for e, k, n, t in dia_index]
    (OUT / "DIAGRAMS.md").write_text("\n".join(di) + "\n", encoding="utf-8")
    tot = sum(s["words"] for s in stats)
    print(f"{len(stats)} episodes, {tot} words, {sum(s['est_min'] for s in stats):.0f} min, {len(inserts)} thesis inserts, {len(dia_index)} diagrams")


if __name__ == "__main__":
    main()
