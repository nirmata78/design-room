#!/usr/bin/env python3
"""ref_solution.py — the deterministic, staged runner for a reference solution (issue #5, Workstream 1).

    ref_solution.py <stage> <SD-NN | solution dir> [--keep-intermediates] [--no-video] [--encoder x264|videotoolbox]
                    [--verbose] [--log [FILE|off]]

Stages (each prints one JSON object on stdout and exits 0 on "ok"):
    doctor     what is installed (ref_runtime.sh doctor)
    outline    video/OUTLINE.md exists and states the scale line; creates it from the template if missing
    diagrams   video/svg/ from workspace.dsl + views.json (c4-structurizr) and video/diagrams.py (sequences, ERDs, figures)
    deck       video/src/gen.py → slides + narration (build intermediates), then the 1080p layout gate
    markdown   video/src/gen.py → SD-NN_<Title>_Reference_Design.md, then the GitHub lint (md_github.py)
    video      gen.py → frames (one Chromium pass: the layout gate, then element screenshots, cached by slide HTML) →
               narrated <stem>.mp4 + .srt + .vtt (TTS pool for uncached sentences, per-slide segments encoded in parallel
               and cached); cleans intermediates. --encoder videotoolbox for a fast draft; the published master is x264.
    publish    video/publish/* from video/publish/meta.json (publish_kit.py)
    clean      removes every build intermediate (frames, slides HTML, scripts, layout reports, PDFs)
    all        diagrams → deck → markdown → video → publish → clean   (--no-video stops after markdown)

Status values: ok · outline_created · solution_not_found · diagram_gate_failed · dsl_error · missing_reveal_markers ·
layout_gate_failed · markdown_lint_failed · render_failed · publish_failed · missing_dependency.
Every non-ok result carries a "remedy" an agent can act on, and "log" with the tail of the failing tool's output.
Exit codes: 0 ok · 1 a stage failed · 2 usage or missing solution.

Timings (issue #7): every tool prints "[time] <step>: <s> s · key=value …"; each stage's JSON carries them as "timings"
and the render log (video/logs/) ends each stage with a timing table. --verbose (REF_VERBOSE=1) adds one log line per
frame, sentence, audio line and segment with its cache decision. Caches live in $SD_CACHE (default ~/.cache/sd-course):
tts/ lines/ master/ frames/ segments/ — deleting the folder only costs time.
"""
from __future__ import annotations

import argparse, json, os, pathlib, re, shutil, subprocess, sys, time

HERE = pathlib.Path(__file__).resolve().parent
SKILL = HERE.parent
KIT = SKILL / "kit"
sys.path.insert(0, str(KIT))
import paths  # noqa: E402

REPO = paths.REPO
PY = str(paths.PY)
INTERMEDIATES = ["frames", "frames-theory", "video-slides.html", "video-theory.html", "layout-report.txt",
                 "layout-report-theory.txt", "build.log", "__pycache__", "src/__pycache__"]
INTERMEDIATE_GLOBS = ["*.script.md", "*.built.html", "*.pdf", ".v1-retrofit-*"]


def out(status: str, stage: str, **kw) -> dict:
    return {"status": status, "stage": stage, **kw}


LOG: dict = {"fh": None}       # --log: every tool's output, line by line, with wall-clock stamps and per-step timings


def log_line(msg: str) -> None:
    if LOG["fh"]:
        LOG["fh"].write(f"{time.strftime('%H:%M:%S')}  {msg}\n")
        LOG["fh"].flush()


def run(cmd: list[str], cwd: pathlib.Path | None = None, env: dict | None = None) -> tuple[int, str]:
    e = os.environ.copy()
    e.update(env or {})
    if not LOG["fh"]:
        t0 = time.time()
        p = subprocess.run(cmd, cwd=str(cwd) if cwd else None, env=e, capture_output=True, text=True)
        o = (p.stdout or "") + (p.stderr or "")
        collect_timings(o)
        TIMINGS.append({"step": "$ " + pathlib.Path(cmd[1] if len(cmd) > 1 else cmd[0]).name, "s": round(time.time() - t0, 1)})
        return p.returncode, o
    t0 = time.time()
    log_line("$ " + " ".join(pathlib.Path(c).name if i < 2 else c for i, c in enumerate(cmd)))
    p = subprocess.Popen(cmd, cwd=str(cwd) if cwd else None, env=e, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, bufsize=1)
    buf = []
    for line in p.stdout:
        buf.append(line)
        log_line("  " + line.rstrip("\n"))
    rc = p.wait()
    log_line(f"  → exit {rc} in {time.time() - t0:.1f} s")
    o = "".join(buf)
    collect_timings(o)
    TIMINGS.append({"step": "$ " + pathlib.Path(cmd[1] if len(cmd) > 1 else cmd[0]).name, "s": round(time.time() - t0, 1)})
    return rc, o


TIMINGS: list = []          # (tool step, seconds, details) parsed from "[time]" lines, per stage


def collect_timings(log: str) -> None:
    for m in re.finditer(r"^\s*\[time\] ([^:]+): ([\d.]+) s(.*)$", log, flags=re.M):
        TIMINGS.append({"step": m.group(1).strip(), "s": float(m.group(2)),
                        **({"detail": m.group(3).strip(" ·")} if m.group(3).strip() else {})})


def tail(s: str, n: int = 25) -> str:
    return "\n".join(s.strip().splitlines()[-n:])


def find_solution(arg: str) -> pathlib.Path | None:
    p = pathlib.Path(arg)
    if p.is_dir():
        return p.resolve()
    m = re.fullmatch(r"(?i)sd-?(\d+)", arg)
    if m:
        hits = sorted((REPO / "solutions").glob(f"SD-{int(m.group(1)):02d}-*/"))
        return hits[0].resolve() if hits else None
    hits = sorted((REPO / "solutions").glob(f"*{arg}*/"))
    return hits[0].resolve() if hits else None


def stem_of(sol: pathlib.Path) -> str:
    m = re.search(r"stem=['\"]([^'\"]+)", (sol / "video/src/gen.py").read_text(encoding="utf-8"))
    return m.group(1) if m else "reference"


# ── stages ─────────────────────────────────────────────────────────────────────────────────────────────────────────
def st_doctor(sol, a):
    rc, log = run(["bash", str(HERE / "ref_runtime.sh"), "doctor"])
    try:
        return out("ok", "doctor", runtime=json.loads(log))
    except json.JSONDecodeError:
        return out("missing_dependency", "doctor", log=tail(log), remedy="Run scripts/ref_runtime.sh doctor and fix what it reports.")


def st_outline(sol, a):
    o = sol / "video" / "OUTLINE.md"
    if not o.exists():
        o.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy(SKILL / "templates" / "outline.template.md", o)
        return out("outline_created", "outline", path=str(o),
                   remedy="Fill in OUTLINE.md (scale line, FRs/NFRs, versions, the challenge list), then run the diagrams stage.")
    t = o.read_text(encoding="utf-8")
    missing = [h for h in ("Scale line", "Challenges") if h.lower() not in t.lower()]
    if missing:
        return out("dsl_error", "outline", path=str(o), missing=missing,
                   remedy=f"OUTLINE.md must have sections: {missing} (templates/outline.template.md).")
    return out("ok", "outline", path=str(o))


def st_diagrams(sol, a):
    svg = sol / "video" / "svg"
    if svg.exists():
        shutil.rmtree(svg)
    svg.mkdir(parents=True)
    res = {}
    if (sol / "workspace.dsl").exists():
        cmd = [PY, str(paths.C4_SKILL / "scripts/render_c4.py"), "--dsl", str(sol / "workspace.dsl"), "--out", str(svg)]
        if (sol / "views.json").exists():
            cmd += ["--spec", str(sol / "views.json")]
        rc, log = run(cmd)
        try:
            j = json.loads(log[log.index("{"):])
        except (ValueError, json.JSONDecodeError):
            j = {}
        if rc != 0:
            return out("diagram_gate_failed" if rc == 3 else "dsl_error", "diagrams", log="" if j else tail(log, 40),
                       failures=j.get("failures", []), missing_sources=j.get("missing_sources", []),
                       remedy=(j.get("failures") or [{}])[0].get("remedy") or "Fix the DSL error reported by Structurizr (line and token in log).")
        res["c4_views"] = j.get("views_rendered", 0)
    d = sol / "video" / "diagrams.py"
    if d.exists():
        rc, log = run([PY, str(d)])
        if rc != 0:
            return out("dsl_error", "diagrams", log=tail(log), remedy="video/diagrams.py raised: fix the generator call named in the traceback.")
    res["svgs"] = len(list(svg.glob("*.svg")))
    return out("ok", "diagrams", **res)


def _gen(sol):
    rc, log = run([PY, str(sol / "video/src/gen.py")])
    if rc != 0:
        if re.search(r"units revealed|reveal marker|reveals but only", log):
            return out("missing_reveal_markers", "deck", log=tail(log),
                       remedy="The slide named in the log has more reveal units than [+] markers (or a marker on a steps=False slide). "
                              "Add [+]/[+N]/[+*] lines to its narration, or pass steps=False.")
        return out("dsl_error", "deck", log=tail(log), remedy="gen.py raised: the file:line in the traceback is the slide source to fix.")
    return out("ok", "deck", log=tail(log, 4))


def st_deck(sol, a):
    r = _gen(sol)
    if r["status"] != "ok":
        return r
    v = sol / "video"
    rc, log = run([PY, str(KIT / "check_layout.py"), "--html", str(v / "video-slides.html"), "--svg-dir", str(v / "svg"),
                   "--css-dir", str(KIT)])
    (v / "layout-report.txt").write_text(log, encoding="utf-8")
    last = log.strip().splitlines()[-1] if log.strip() else ""
    if rc != 0:
        fails = [l.strip() for l in log.splitlines() if " FAIL " in l][:15]
        return out("layout_gate_failed", "deck", summary=last, failures=fails, report=str(v / "layout-report.txt"),
                   remedy="Each FAIL names slide data-n and the element: shorten text, split the slide, crop the figure "
                          "(views.json keep+crop) or use dsl.stage() for a C4 view. Re-run the deck stage.")
    warns = [l for l in log.splitlines() if " WARN " in l]
    return out("ok", "deck", summary=last, warnings=len(warns), gen=r.get("log"))


def st_markdown(sol, a):
    r = _gen(sol)
    if r["status"] != "ok":
        return {**r, "stage": "markdown"}
    mds = sorted(sol.glob("SD-*_Reference_Design.md"))
    if not mds:
        return out("dsl_error", "markdown", remedy="gen.py must call dsl.write_reference_markdown(ROOT / 'SD-NN_<Title>_Reference_Design.md').")
    rc, log = run([sys.executable, str(KIT / "md_github.py"), str(mds[0])])
    if rc != 0:
        return out("markdown_lint_failed", "markdown", path=str(mds[0]), log=tail(log),
                   remedy="Fix the slide or narration the lint line points to (missing figure: add it to views.json or diagrams.py).")
    return out("ok", "markdown", path=str(mds[0].relative_to(REPO)), words=len(mds[0].read_text(encoding="utf-8").split()))


def st_video(sol, a):
    # one Chromium pass (issue #7): the layout gate runs inside the frame render, on the page the frames are shot from
    r = _gen(sol)
    if r["status"] != "ok":
        return {**r, "stage": "video"}
    v, stem = sol / "video", stem_of(sol)
    frames = v / "frames"
    shutil.rmtree(frames, ignore_errors=True)
    frames.mkdir()
    rc, log = run([PY, str(KIT / "render_slides.py"), "--html", str(v / "video-slides.html"), "--prefix", "v", "--svg-dir", str(v / "svg"),
                   "--css-dir", str(KIT), "--out", str(frames)], env={"LAYOUT_CHECK": "fail"})
    gate = next((l.strip() for l in log.splitlines() if re.search(r"\bslides?\b.*\bfail", l, re.I)), "")
    if rc != 0:
        if "layout check failed" in log:
            rep = v / "layout-report.txt"
            fails = [l.strip() for l in rep.read_text(encoding="utf-8").splitlines() if " FAIL " in l][:15] if rep.exists() else []
            return out("layout_gate_failed", "video", summary=gate, failures=fails, report=str(rep),
                       remedy="Each FAIL names slide data-n and the element: shorten text, split the slide, crop the figure "
                              "or use dsl.stage() for a C4 view. Re-run the video stage.")
        return out("render_failed", "video", log=tail(log), remedy="Frame rendering failed: see the Playwright error in log.")
    tts = str(paths.kokoro_python())
    if not pathlib.Path(tts).exists():
        return out("missing_dependency", "video", remedy="Set KOKORO_PYTHON to the Kokoro TTS venv python (see ref_runtime.sh doctor).")
    rc, log = run([tts, str(KIT / "tts_cached.py"), str(v / f"{stem}.script.md"), "--frames", str(frames), "--out", str(v / f"{stem}.mp4"),
                   "--dissolve", "0.3", "--chapter-gap", "0", "--captions", "sidecar", "--reveal-fade", "0.4", "--max-minutes", "90",
                   "--encoder", a.encoder])
    (v / "build.log").write_text(log, encoding="utf-8")
    if rc != 0:
        return out("render_failed", "video", log=tail(log), remedy="The narrated build failed: see build.log (missing frame names a [slide:] cue).")
    if not a.keep_intermediates:
        st_clean(sol, a)
    return out("ok", "video", mp4=str((v / f"{stem}.mp4").relative_to(REPO)), layout=gate, encoder=a.encoder, log=tail(log, 6))


def st_publish(sol, a):
    meta = sol / "video" / "publish" / "meta.json"
    if not meta.exists():
        return out("publish_failed", "publish", remedy="Create video/publish/meta.json (templates/publish.meta.example.json).")
    rc, log = run([sys.executable, str(KIT / "publish_kit.py"), str(meta)])
    if rc != 0:
        return out("publish_failed", "publish", log=tail(log), remedy="publish_kit.py reported a platform limit or a missing MP4: see log.")
    return out("ok", "publish", log=tail(log, 6))


def st_clean(sol, a):
    v, gone = sol / "video", []
    for name in INTERMEDIATES:
        p = v / name
        if p.exists():
            shutil.rmtree(p) if p.is_dir() else p.unlink()
            gone.append(name)
    for g in INTERMEDIATE_GLOBS:
        for p in v.glob(g):
            shutil.rmtree(p) if p.is_dir() else p.unlink()
            gone.append(p.name)
    return out("ok", "clean", removed=gone)


STAGES = {"doctor": st_doctor, "outline": st_outline, "diagrams": st_diagrams, "deck": st_deck, "markdown": st_markdown,
          "video": st_video, "publish": st_publish, "clean": st_clean}


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("stage", choices=[*STAGES, "all"])
    ap.add_argument("solution", nargs="?", default="")
    ap.add_argument("--keep-intermediates", action="store_true", help="keep frames, slides HTML and scripts after the video stage")
    ap.add_argument("--no-video", action="store_true", help="all: stop after the markdown stage")
    ap.add_argument("--encoder", choices=["x264", "videotoolbox"], default="x264",
                    help="video: x264 (the published master, default) or videotoolbox (hardware, for drafts)")
    ap.add_argument("--verbose", "-v", action="store_true", help="one log line per frame, sentence, audio line and segment")
    ap.add_argument("--log", nargs="?", const="auto", default=None,
                    help="write every tool's output with timestamps and step timings to a file (default for 'video' and 'all': "
                         "<solution>/video/logs/<stage>-<date-time>.log, kept by clean, gitignored); --log off disables it")
    a = ap.parse_args()
    if a.verbose:
        os.environ["REF_VERBOSE"] = "1"
    if a.stage == "doctor":
        print(json.dumps(st_doctor(None, a), indent=2)); return 0
    sol = find_solution(a.solution) if a.solution else None
    if not sol:
        print(json.dumps(out("solution_not_found", a.stage, remedy="Pass SD-NN or a path to solutions/SD-NN-<slug>/.")))
        return 2
    seq = ["diagrams", "deck", "markdown"] + ([] if a.no_video else ["video", "publish"]) + ["clean"] if a.stage == "all" else [a.stage]
    if a.log != "off" and (a.log or ("video" in seq)):
        lp = pathlib.Path(a.log) if a.log and a.log != "auto" else sol / "video" / "logs" / f"{a.stage}-{time.strftime('%Y%m%d-%H%M%S')}.log"
        lp.parent.mkdir(parents=True, exist_ok=True)
        LOG["fh"] = open(lp, "w", encoding="utf-8")
        LOG["path"] = lp
        log_line(f"ref_solution {a.stage} {sol.name}")
    results = []
    for s in seq:
        t0 = time.time()
        log_line(f"== stage {s}")
        TIMINGS.clear()
        r = STAGES[s](sol, a)
        el = time.time() - t0
        r["seconds"] = round(el, 1)
        if TIMINGS:
            r["timings"] = list(TIMINGS)
            log_line(f"== timings, stage {s}")
            for tm in TIMINGS:
                log_line(f"   {tm['s']:8.1f} s  {tm['step']}" + (f"  ({tm['detail']})" if tm.get("detail") else ""))
        log_line(f"== stage {s}: {r['status']} in {el:.1f} s")
        results.append(r)
        if r["status"] != "ok":
            break
    if LOG["fh"]:
        results[-1]["render_log"] = str(LOG["path"].relative_to(REPO)) if LOG["path"].is_relative_to(REPO) else str(LOG["path"])
        LOG["fh"].close()
    final = results[-1] if len(results) == 1 else {"status": results[-1]["status"], "stage": "all", "solution": sol.name, "stages": results}
    print(json.dumps(final, indent=2))
    return 0 if final["status"] == "ok" else 1


if __name__ == "__main__":
    sys.exit(main())
