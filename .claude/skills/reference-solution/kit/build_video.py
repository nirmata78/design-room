#!/usr/bin/env python3
"""Render a slide-video script to an MP4 (1080p by default): Kokoro voices (the audio-version skill's stack and
pacing), one still frame per slide, a speaker chip, burned-in captions under the slide, chapters.

    build_video.py SCRIPT.script.md --frames DIR [--out FILE.mp4] [--res 1080|720] [--captions burn|soft]
                   [--gap-scale 1.0] [--max-minutes N] [--srt] [--dissolve 0.3] [--chapter-gap S] [--reveal-fade 0.8]

Script format = the audio-version format plus picture and pause cues:
    # Title
    <!-- voices: N=af_heart@0.92 I=bf_emma -->   optional voice overrides (code=voice[@speed]); lower speed = slower
    <!-- labels: N=COACH V=KEY_LINE -->           optional chip labels (underscore = space)
    <!-- say: Kafka=Kaf-ka -->                     optional spoken-only respellings (defaults: Redis, dedup)
    ## Chapter                                    chapter marker (and a 1.8 s pause)
    [slide: NAME]                                 show DIR/NAME.png (any 16:9 size; 1920x1080 is ideal) from here on
    [pause: 1.2]                                  silence, in seconds — after a thesis line, before a reveal
    [reveal: NAME]                                crossfade (0.8 s) from the current frame to NAME, the SAME slide with more
                                                  content visible: the answer under a question, a card, the takeaway bar
    X: spoken text                                one paragraph; X = speaker code
Speaker codes: N narrator/coach · I interviewer · C you · V you, slower (key lines) · Q second interviewer ·
E an aside voice (traps, "then and now", stories): up to five distinct voices, set them in the voices comment.
Transitions (2026-11-12): --dissolve S crossfades consecutive slides (default 0 = hard cut); [reveal: NAME] crossfades to
a richer version of the same slide; --chapter-gap S overrides the silence before a "## chapter" marker (use 0 when the
script itself shows a title card and a [pause: 1.0] there).

Captions — ONE caption source per video, never two, so nothing overlaps on screen:
  --captions burn (default): slide at the top, caption band below it with the speaker chip and two lines.
      NO subtitle track is muxed and no .srt is written next to the video (players auto-load a same-named .srt
      and draw it over the burned band). Pass --srt to write NAME.captions.srt into a captions/ subfolder.
  --captions soft: slide full-frame with a chip overlay; captions only as a selectable mov_text track + .srt.
  --captions sidecar (2026-11-21, reference solutions): slide full-frame, NOTHING drawn over it (no band, no chip),
      no subtitle stream in the MP4; NAME.srt and NAME.vtt are written next to it, cues of at most two 42-character
      lines, for upload to YouTube (viewers toggle and auto-translate them). <!-- names: C=Candidate --> sets the
      speaker names. The SRT (upload this one to YouTube, which shows no voice spans) starts a cue with "Name: " when the
      speaker changes, inside the 42-character budget. The VTT puts the name in a voice span on every cue
      (<v Candidate>text), so web players can style or label speakers and the lines stay text only.
Captions show written forms ('SMS', 'P0') even where the script spells them for the voice ('S-M-S', 'P-zero').

Timing is frame-exact. Encode (2026-11-28, issue #7): the timeline is cut into one segment per logical slide; every cue is
placed on the 25 fps grid relative to its chapter's first frame (chapters are anchored to round(t × 25) globally, so nothing
drifts). Each segment is one ffmpeg run that decodes each PNG once (the loop filter holds it), crossfades with blend, and
encodes with libx264 (--encoder videotoolbox exists, but measured slower and larger on slide video). Segments encode in parallel and are cached by
a hash of their pieces (PNG contents, frame counts, fades, encoder settings) under $SD_CACHE/segments, so a re-cut re-encodes
only the slides it touched; the MP4 is a stream-copy concat of the segments muxed with the master audio and the chapters.
Per-line audio (trimmed + levelled) and the mastered track are cached the same way. REF_ENCODE=pipe restores the previous
encoder (every frame piped as a PNG at 20 fps, resampled to 25) for comparison. Every step prints "[time] step: N s";
REF_VERBOSE=1 adds one line per segment, line and cache decision. (The concat-demuxer-of-stills approach used before
2026-10-28 drifted ~9 s by minute 8; segments here are whole frames, so concat is exact.)
"""
import os as _os, pathlib as _pl
_os.environ.setdefault("PANGOCAIRO_BACKEND", "fc")   # rsvg-convert: use fontconfig so the bundled Google Fonts resolve
import sys as _sys; _sys.path.insert(0, str(_pl.Path(__file__).resolve().parent)); import paths as _paths
_os.environ.setdefault("FONTCONFIG_FILE", str(_paths.FONTS_CONF))
import argparse, hashlib, html, json, math, os, pathlib, re, shutil, struct, subprocess, sys, tempfile, time
from concurrent.futures import ThreadPoolExecutor

SKILL = _paths.audio_skill_dir()
VENV_PY = _paths.kokoro_python()
if pathlib.Path(sys.executable).resolve() != VENV_PY.resolve() and not os.environ.get("KOKORO_REEXEC"):
    os.environ["KOKORO_REEXEC"] = "1"
    os.execv(str(VENV_PY), [str(VENV_PY), __file__, *sys.argv[1:]])
sys.path.insert(0, str(SKILL))
import build_audio as ba                      # voices, pacing, loudness filters: one pattern with the audio skill
import soundfile as sf
from kokoro_onnx import Kokoro

VERBOSE = os.environ.get("REF_VERBOSE") == "1"
CACHE_ROOT = pathlib.Path(os.environ.get("SD_CACHE", pathlib.Path.home() / ".cache/sd-course")).expanduser()
JOBS = int(os.environ.get("REF_JOBS", "0")) or max(2, (os.cpu_count() or 4) // 2)
SEG_CACHE_GB = float(os.environ.get("REF_SEGMENT_CACHE_GB", "6"))
ENCODERS = {   # libx264 is the master. videotoolbox measured on SD-03 (2026-11-28): 259 s vs 110 s and 512 MB vs 128 MB — slide video is
               # mostly skipped still frames, which x264 encodes almost free; the hardware encoder is one engine shared by every job
    "x264": ["-c:v", "libx264", "-preset", "medium", "-tune", "stillimage", "-crf", "18", "-pix_fmt", "yuv420p"],
    "videotoolbox": ["-c:v", "h264_videotoolbox", "-profile:v", "high", "-b:v", "8M", "-maxrate", "12M", "-bufsize", "24M",
                     "-pix_fmt", "yuv420p"],
}

def tlog(step, t0, **kw):
    """One timing line per step; ref_solution.py collects them into the render log's summary and the stage's JSON."""
    extra = "".join(f" · {k}={v}" for k, v in kw.items())
    print(f"[time] {step}: {time.time() - t0:.1f} s{extra}", flush=True)

def vlog(msg):
    if VERBOSE:
        print(f"  · {msg}", flush=True)

def dur(path):
    """Duration of a WAV from its header (the old ffprobe call per line cost about 30 ms × ~1,000 calls)."""
    i = sf.info(str(path)); return i.frames / i.samplerate

_SHA = {}
def file_sha(p):
    p = str(p)
    if p not in _SHA:
        h = hashlib.sha1()
        with open(p, "rb") as f:
            for b in iter(lambda: f.read(1 << 20), b""):
                h.update(b)
        _SHA[p] = h.hexdigest()
    return _SHA[p]

def png_size(p):
    with open(p, "rb") as f:
        head = f.read(24)
    return struct.unpack(">II", head[16:24]) if head[:8] == b"\x89PNG\r\n\x1a\n" else (0, 0)

def cache_put(src, dst):
    """Atomic publish into the cache (parallel builds may race on the same key)."""
    dst.parent.mkdir(parents=True, exist_ok=True)
    tmp = dst.with_name(f".{dst.name}.{os.getpid()}.{time.time_ns()}")
    shutil.copyfile(src, tmp); tmp.replace(dst)

def prune(d, max_gb):
    files = sorted((p for p in d.glob("*") if p.is_file()), key=lambda p: p.stat().st_mtime)
    total = sum(p.stat().st_size for p in files); removed = 0
    while files and total > max_gb * 1e9:
        p = files.pop(0); total -= p.stat().st_size; p.unlink(); removed += 1
    if removed:
        vlog(f"segment cache pruned: {removed} oldest files, {total / 1e9:.1f} GB kept")

CHIP = {"I": ("INTERVIEWER", "#4285f4"), "Q": ("INTERVIEWER 2", "#1967d2"), "C": ("YOU", "#188038"),
        "V": ("YOU · KEY LINE", "#174ea6"), "N": ("NARRATOR", "#5f6368"), "E": ("ASIDE", "#b06000")}
NAMES = {"I": "Interviewer", "Q": "Interviewer 2", "C": "You", "V": "You", "N": "Narrator", "E": "Aside"}
FONT = "Inter, Roboto, sans-serif"
FPS_IN, FPS_OUT = 10, 25      # FPS_IN becomes 20 inside build() when the script has fades
# W, H, slide W, slide H, caption band, scale for chip/caption type
RES = {1080: (1920, 1080, 1680, 945, 135, 1.5), 720: (1280, 720, 1120, 630, 90, 1.0)}

def parse(text, frames):
    voices = dict(ba.DEFAULT_VOICES)
    m = re.search(r"<!--\s*voices:(.*?)-->", text, flags=re.S)
    if m:
        for tok in m.group(1).split():
            code, v = tok.split("="); name, _, spd = v.partition("@")
            voices[code] = (name, float(spd) if spd else voices.get(code, (None, 1.0))[1])
    say = dict(SAY)
    m = re.search(r"<!--\s*say:(.*?)-->", text, flags=re.S)
    if m:
        for tok in m.group(1).split():
            w, r = tok.split("="); say[w.replace("_", " ")] = r.replace("_", " ")
    names = {}
    m = re.search(r"<!--\s*names:(.*?)-->", text, flags=re.S)
    if m:
        for tok in m.group(1).split():
            code, nm = tok.split("="); names[code] = nm.replace("_", " ")
    labels = {"__names__": names}
    m = re.search(r"<!--\s*labels:(.*?)-->", text, flags=re.S)
    if m:
        for tok in m.group(1).split():
            code, lab = tok.split("="); labels[code] = lab.replace("_", " ")
    text = re.sub(r"<!--.*?-->", "", text, flags=re.S)
    items, title = [], None
    for raw in text.splitlines():
        line = raw.strip()
        if not line:
            continue
        if line.startswith("# "):
            title = title or line[2:]; continue
        if line.startswith("## "):
            items.append(("chapter", line[3:])); continue
        mm = re.match(r"^\[slide:\s*([\w./-]+)\]$", line)
        if mm:
            if not (frames / f"{mm.group(1)}.png").exists():
                sys.exit(f"missing frame {frames / (mm.group(1) + '.png')}")
            items.append(("slide", mm.group(1))); continue
        mm = re.match(r"^\[reveal:\s*([\w./-]+)\]$", line)
        if mm:
            if not (frames / f"{mm.group(1)}.png").exists():
                sys.exit(f"missing frame {frames / (mm.group(1) + '.png')}")
            items.append(("reveal", mm.group(1))); continue
        mm = re.match(r"^\[pause:\s*([\d.]+)\]$", line)
        if mm:
            items.append(("pause", float(mm.group(1)))); continue
        mm = re.match(r"^([A-Z]):\s*(.+)$", line)
        if not mm or mm.group(1) not in voices:
            sys.exit(f"unparsed line: {line[:80]}")
        items.append(("line", mm.group(1), mm.group(2)))
    return title, voices, labels, items, say

def chunks(text, limit=150):
    """Caption chunks: whole sentences where possible, at most ~two caption lines each."""
    out, cur = [], ""
    for sent in re.split(r"(?<=[.?!])\s+", text):
        if cur and len(cur) + 1 + len(sent) > limit:
            out.append(cur); cur = ""
        while len(sent) > limit:
            cut = max(sent.rfind(", ", 0, limit), sent.rfind(" ", 0, limit))
            out.append((cur + " " + sent[:cut + 1]).strip()); cur = ""; sent = sent[cut + 1:].strip()
        cur = f"{cur} {sent}".strip()
    if cur:
        out.append(cur)
    return out

def cue_groups(text, width=42):
    """Greedy wrap at width, then groups of at most two lines: one group per cue."""
    words, lines, cur = text.split(), [], ""
    for w in words:
        if cur and len(cur) + 1 + len(w) > width: lines.append(cur); cur = w
        else: cur = f"{cur} {w}".strip()
    lines.append(cur)
    return [lines[i:i + 2] for i in range(0, len(lines), 2)]

def vtt_esc(s): return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

def wrap2(text, width=78):
    words, lines, cur = text.split(), [], ""
    for w in words:
        if cur and len(cur) + 1 + len(w) > width:
            lines.append(cur); cur = w
        else:
            cur = f"{cur} {w}".strip()
    lines.append(cur)
    if len(lines) > 2:
        half = len(text) // 2; cut = text.rfind(" ", 0, half + 10)
        lines = [text[:cut], text[cut + 1:]]
    return lines

def written(text):
    """Captions and chapter titles use written forms: 'S-M-S' → 'SMS', 'P-zero' → 'P0'."""
    # a plural or possessive stays attached: 'S-L-Os' → 'SLOs' (the old pattern stopped before the s: 'SL-Os')
    text = re.sub(r"\b[A-Z](?:-[A-Z])+(?:'?s)?\b", lambda m: m.group(0).replace("-", ""), text)
    for w, d in (("zero", "0"), ("one", "1"), ("two", "2")):
        text = re.sub(rf"\bP-{w}\b", f"P{d}", text)
    return text

# Spoken-only respellings: the caption keeps the real word, the voice gets the respelling. Each was verified with
# faster-whisper (2026-10-28). Add per script with <!-- say: Word=Respelling Other=Thing -->.
SAY = {"Redis": "Reh-diss", "dedup": "dee-dupe", "Dedup": "Dee-dupe"}

def spoken(text, say):
    for w, r in say.items():
        text = re.sub(rf"\b{re.escape(w)}\b", r, text)
    return text

def svg_png(svg, out):
    p = out.with_suffix(".svg"); p.write_text(svg, encoding="utf-8")
    ba.run("rsvg-convert", "-o", str(out), str(p))

def chip_svg(label, colour, w, s):
    h = 30 * s
    return (f'<rect x="0.5" y="0.5" width="{w-1}" height="{h-1}" rx="{h/2}" fill="{colour}"/>'
            f'<text x="{w/2}" y="{20*s}" text-anchor="middle" font-family="{FONT}" font-size="{13*s}" font-weight="700" '
            f'letter-spacing="{1.5*s}" fill="#fff">{html.escape(label)}</text>')

def build(script, frames, out, mode, max_minutes, res, gap_scale, want_srt, dissolve=0.0, chapter_gap=None, reveal_fade=0.8,
          encoder="x264"):
    t_all = time.time()
    W, H, SW, SH, BAND, S = RES[res]
    title, voices, labels, items, say = parse(script.read_text(encoding="utf-8"), frames)
    names = {**NAMES, **labels.pop("__names__", {})}
    chip_text = {c: (labels.get(c, CHIP[c][0]), CHIP[c][1]) for c in CHIP}
    k = Kokoro(str(ba.HOME / "kokoro-v1.0.onnx"), str(ba.HOME / "voices-v1.0.bin"))
    with tempfile.TemporaryDirectory() as td:
        td = pathlib.Path(td)
        t_step = time.time()
        wavs, n = {}, sum(1 for it in items if it[0] == "line")
        line_dir = CACHE_ROOT / "lines"; line_dir.mkdir(parents=True, exist_ok=True)
        pool, jobs, hits = ThreadPoolExecutor(max_workers=os.cpu_count() or 4), [], 0
        def level(i, audio, sr, dst):
            raw = td / f"{i:04d}.raw.wav"; sf.write(raw, audio, sr)
            tmp = td / f"{i:04d}.lvl.wav"
            ba.run("ffmpeg", "-y", "-i", str(raw), "-af", ba.LINE_FILTER, "-ar", str(ba.RATE_HZ), "-ac", "1",
                   "-c:a", "pcm_s16le", str(tmp))
            cache_put(tmp, dst); raw.unlink(); tmp.unlink()
        t_syn = 0.0
        for i, it in enumerate(items):
            if it[0] != "line":
                continue
            voice, speed = voices[it[1]]
            t1 = time.time()
            audio, sr = k.create(spoken(it[2], say), voice=voice, speed=speed, lang="en-us")
            t_syn += time.time() - t1
            # the levelled line is cached by the synthesized samples themselves plus the filter, so any change to the voice,
            # the respelling, the beats or the filter misses the cache, and nothing else does
            key = hashlib.sha1(audio.astype("float32").tobytes() + f"|{sr}|{ba.LINE_FILTER}|{ba.RATE_HZ}".encode()).hexdigest()
            wavs[i] = line_dir / f"{key}.wav"
            if wavs[i].exists():
                hits += 1; os.utime(wavs[i]); vlog(f"line {i:04d} {it[1]} cached")
            else:
                jobs.append(pool.submit(level, i, audio, sr, wavs[i])); vlog(f"line {i:04d} {it[1]} levelling: {it[2][:60]}")
            if len(wavs) % 50 == 0:
                print(f"  voice {len(wavs)}/{n}", flush=True)
        for j in jobs:
            j.result()
        pool.shutdown()
        tlog("voices", t_step, lines=n, synth_s=round(t_syn, 1), levelled=len(jobs), level_cache_hits=hits)
        t_step = time.time()

        def silence(sec):
            sec = round(sec, 3)
            p = td / f"sil-{sec}.wav"
            if not p.exists():
                import numpy as np
                sf.write(p, np.zeros(int(round(sec * ba.RATE_HZ)), dtype="int16"), ba.RATE_HZ, subtype="PCM_16")
            return p

        seq, chapters, subs, segs = [], [], [], []      # segs: (start, slide, speaker, caption-or-None)
        last_who = {}
        t, prev, slide = 0.0, None, None
        for i, it in enumerate(items):
            if it[0] == "chapter":
                g = (ba.GAP_CHAPTER if chapter_gap is None else chapter_gap) * gap_scale
                if seq and g > 0:
                    seq.append(silence(g)); t += dur(silence(g))
                chapters.append((t, it[1])); prev = None; continue
            if it[0] == "slide":
                slide = it[1]; segs.append((t, slide, None, None, "dissolve")); continue
            if it[0] == "reveal":
                slide = it[1]; segs.append((t, slide, None, None, "reveal")); continue
            if it[0] == "pause":
                seq.append(silence(it[1])); t += dur(silence(it[1])); continue
            if slide is None:
                sys.exit("the script must show a [slide: …] before the first spoken line")
            if prev is not None:
                g = (ba.GAP_SAME if prev == it[1] else ba.GAP_TURN) * gap_scale
                seq.append(silence(g)); t += dur(silence(g))
            limit = 78 if mode == "sidecar" else (170 if res == 1080 else 150)
            # sidecar: the SRT names the speaker in the text when the speaker changes ("Coach: …"); that prefix counts against
            # the 2 × 42 budget, so the first chunk of such a line is cut shorter. The VTT carries the speaker as a voice span
            # (<v Coach>) on every cue instead, so its lines are text only.
            who = f"{names[it[1]]}: " if mode == "sidecar" and names[it[1]] != last_who.get("n") else ""
            d = dur(wavs[i]); parts = chunks(written(it[2]), limit - len(who)); total = sum(len(p) for p in parts); s0 = t
            for j, p in enumerate(parts):
                s1 = s0 + d * len(p) / total
                if mode == "sidecar":
                    if j == 0: last_who["n"] = names[it[1]]
                    # never a line over 42: a chunk that does not fit two lines becomes several cues, timed by length
                    groups = cue_groups((who if j == 0 else "") + p, 42); n0 = len(who) if j == 0 else 0
                    g0, glen = s0, sum(len(" ".join(g)) for g in groups)
                    for gi, g in enumerate(groups):
                        g1 = s1 if gi == len(groups) - 1 else g0 + (s1 - s0) * len(" ".join(g)) / glen
                        plain = "\n".join(g)
                        vt = plain[n0:].lstrip() if gi == 0 and n0 else plain
                        subs.append((g0, g1, plain, f"<v {names[it[1]]}>" + vtt_esc(vt)))
                        g0 = g1
                else:
                    subs.append((s0, s1, (f"{names[it[1]]}: " if j == 0 else "") + p))
                segs.append((s0, slide, it[1], p, None)); s0 = s1
            seq.append(wavs[i]); t += d; prev = it[1]
        seq.append(silence(1.5)); t += dur(silence(1.5))
        if max_minutes and t > max_minutes * 60:
            sys.exit(f"script runs {t/60:.1f} min, over the {max_minutes}-minute limit — cut it")

        (td / "list.txt").write_text("".join(f"file '{p}'\n" for p in seq))
        joined = td / "joined.wav"
        ba.run("ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", str(td / "list.txt"), "-c", "copy", str(joined))
        drift = dur(joined) - t
        if abs(drift) > 0.5:
            print(f"  warning: audio and timeline differ by {drift:.2f} s", flush=True)
        tlog("audio join", t_step, minutes=round(t / 60, 2)); t_step = time.time()
        # the master (loudnorm over the whole track) runs in the background while frames are composed and encoded
        mkey = hashlib.sha1(f"{file_sha(joined)}|{ba.MASTER_FILTER}|aac160k48k|f32pipe".encode()).hexdigest()
        voice_m4a = CACHE_ROOT / "master" / f"{mkey}.m4a"
        master = None
        if voice_m4a.exists():
            os.utime(voice_m4a); vlog("master audio cached")
        else:
            master_tmp = td / "voice.m4a"
            # two processes on two cores, same samples as one: loudnorm (+ resample) → PCM pipe → the AAC encoder
            norm_p = subprocess.Popen(["ffmpeg", "-v", "error", "-i", str(joined), "-af", ba.MASTER_FILTER, "-ar", "48000",
                                       "-c:a", "pcm_f32le", "-f", "wav", "pipe:1"], stdout=subprocess.PIPE)
            aac_p = subprocess.Popen(["ffmpeg", "-y", "-v", "error", "-f", "wav", "-i", "pipe:0", "-c:a", "aac", "-b:a", "160k",
                                      str(master_tmp)], stdin=norm_p.stdout)
            norm_p.stdout.close()
            master = (aac_p, master_tmp, time.time(), norm_p)

        # compose one PNG per (slide, speaker, caption)
        merged = []
        for s in segs:
            if merged and abs(merged[-1][0] - s[0]) < 1e-6:
                merged[-1] = s[:4] + (s[4] or merged[-1][4],)      # a fade cue keeps its kind when a line starts at once
            else:
                merged.append(s)
        bases, cache, timeline = {}, {}, []
        def base(sl):
            if sl not in bases:
                f = td / f"base-{len(bases):03d}.png"
                if mode == "burn":
                    ba.run("ffmpeg", "-y", "-i", str(frames / f"{sl}.png"), "-vf",
                           f"scale={SW}:{SH}:flags=lanczos,pad={W}:{H}:{(W-SW)//2}:0:color=0x15181c", str(f))
                elif png_size(frames / f"{sl}.png") == (W, H):
                    f = frames / f"{sl}.png"                      # already 1920x1080: used as is
                else:
                    ba.run("ffmpeg", "-y", "-i", str(frames / f"{sl}.png"), "-vf", f"scale={W}:{H}:flags=lanczos", str(f))
                bases[sl] = f
            return bases[sl]
        prev_sl = None
        for start, sl, sp, cap, kind in merged:
            key = (sl, sp, cap if mode == "burn" else None) if mode != "sidecar" else (sl,)
            if key not in cache:
                f = td / f"frame-{len(cache):05d}.png"
                if sp is None or mode == "sidecar":
                    f = base(sl)
                else:
                    label, colour = chip_text[sp]; cw = (30 + 11 * len(label)) * S
                    if mode == "burn":
                        lines = wrap2(cap or "", 90 if res == 1080 else 78)
                        x0 = (W - SW) // 2 + cw + 22 * S
                        txt = "".join(f'<text x="{x0}" y="{(34 + 30*k_)*S}" font-family="{FONT}" font-size="{22*S}" '
                                      f'fill="#f8f9fa">{html.escape(l)}</text>' for k_, l in enumerate(lines))
                        svg = (f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{BAND}">'
                               f'<g transform="translate({(W-SW)//2},{14*S})">{chip_svg(label, colour, cw, S)}</g>{txt}</svg>')
                        ov = td / f"cap-{len(cache):05d}.png"; svg_png(svg, ov)
                        ba.run("ffmpeg", "-y", "-i", str(base(sl)), "-i", str(ov), "-filter_complex",
                               f"overlay=0:{H-BAND}", str(f))
                    else:
                        svg = (f'<svg xmlns="http://www.w3.org/2000/svg" width="{cw}" height="{30*S}">'
                               f'{chip_svg(label, colour, cw, S)}</svg>')
                        ov = td / f"chip-{sp}.png"
                        if not ov.exists():
                            svg_png(svg, ov)
                        ba.run("ffmpeg", "-y", "-i", str(base(sl)), "-i", str(ov), "-filter_complex",
                               f"overlay=(W-w)/2:H-h-{14*S}", str(f))
                cache[key] = f
            fade = 0.0
            if prev_sl is not None and sl != prev_sl:
                fade = reveal_fade if kind == "reveal" else dissolve if kind == "dissolve" else 0.0
            prev_sl = sl
            timeline.append((start, cache[key], fade, kind))

        def ts(x):
            ms = int(round(x * 1000)); h, ms = divmod(ms, 3600000); m, ms = divmod(ms, 60000); s, ms = divmod(ms, 1000)
            return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"
        srt_text = "".join(f"{k_+1}\n{ts(a)} --> {ts(b)}\n{x}\n\n" for k_, (a, b, x, *_) in enumerate(subs))
        srt_tmp = td / "subs.srt"; srt_tmp.write_text(srt_text, encoding="utf-8")
        meta = [";FFMETADATA1", f"title={title or script.stem}"]
        for n_, (start, name) in enumerate(chapters):
            end = chapters[n_ + 1][0] if n_ + 1 < len(chapters) else t
            meta += ["[CHAPTER]", "TIMEBASE=1/1000", f"START={int(start*1000)}", f"END={int(end*1000)}",
                     f"title={written(name)}"]
        (td / "meta.txt").write_text("\n".join(meta) + "\n", encoding="utf-8")

        tlog("compose", t_step, pictures=len(cache)); t_step = time.time()
        if os.environ.get("REF_ENCODE") == "pipe":
            if master is not None:
                master[0].wait(); master[3].wait(); voice_m4a = master[1]; master = None
            encode_pipe(timeline, t, td, voice_m4a, srt_tmp, mode, out)
        else:
            segs_out = encode_segments(timeline, [c for c, _ in chapters], t, td, encoder, W, H)
            tlog("encode", t_step, segments=len(segs_out)); t_step = time.time()
            if master is not None:
                rc = master[0].wait() or master[3].wait()
                if rc:
                    sys.exit("ffmpeg failed on the audio master")
                cache_put(master[1], voice_m4a)
                tlog("audio master (background, from its start)", master[2])
                tlog("wait for the audio master", t_step); t_step = time.time()
            (td / "segs.txt").write_text("".join(f"file '{p}'\n" for p in segs_out))
            cmd = ["ffmpeg", "-y", "-v", "error", "-f", "concat", "-safe", "0", "-i", str(td / "segs.txt"), "-i", str(voice_m4a)]
            maps = ["-map", "0:v", "-map", "1:a"]
            if mode == "soft":
                cmd += ["-i", str(srt_tmp)]; maps += ["-map", "2:s"]
            mi = 3 if mode == "soft" else 2
            cmd += ["-i", str(td / "meta.txt")] + maps + ["-map_metadata", str(mi), "-map_chapters", str(mi), "-c:v", "copy",
                                                         "-c:a", "copy"]
            if mode == "soft":
                cmd += ["-c:s", "mov_text", "-metadata:s:s:0", "language=eng"]
            cmd += ["-shortest", "-movflags", "+faststart", str(out)]
            if subprocess.run(cmd).returncode:
                sys.exit("ffmpeg failed on the final mux")
            tlog("mux", t_step)
        stale = out.with_suffix(".srt")
        if mode == "sidecar":
            stale.write_text(srt_text, encoding="utf-8")
            out.with_suffix(".vtt").write_text("WEBVTT\n\n" + "".join(
                f"{ts(a).replace(',', '.')} --> {ts(b).replace(',', '.')}\n{v}\n\n" for a, b, _, v in subs), encoding="utf-8")
        elif mode == "soft":
            stale.write_text(srt_text, encoding="utf-8")
        else:
            if stale.exists():                       # a same-named .srt would be auto-loaded over the burned band
                stale.unlink()
            if want_srt:
                d = out.parent / "captions"; d.mkdir(exist_ok=True)
                (d / f"{out.stem}.captions.srt").write_text(srt_text, encoding="utf-8")
    tlog("build total", t_all)
    m, s = divmod(int(t), 60)
    print(f"{out}  {res}p  {m}:{s:02d}  {len(chapters)} chapters  {len(cache)} frames", flush=True)
    for start, name in chapters:
        print(f"  {int(start)//60:02d}:{int(start)%60:02d}  {written(name)}")

def encode_pipe(timeline, t, td, voice_m4a, srt_tmp, mode, out):
    """The encoder before issue #7: every output frame piped to one ffmpeg as a PNG (REF_ENCODE=pipe)."""
    t_step = time.time()
    fps_in = 20 if any(x[2] for x in timeline) else FPS_IN
    fades = {}
    def fade_frames(a, b, dur):
        """Crossfade a→b as PNG bytes, fps_in frames a second, made by ffmpeg's blend filter."""
        k = (a, b, dur)
        if k not in fades:
            d = td / f"fade-{len(fades):04d}"; d.mkdir()
            n = max(2, round(dur * fps_in))
            ba.run("ffmpeg", "-y", "-loop", "1", "-framerate", str(fps_in), "-t", str(dur + 0.2), "-i", str(a),
                   "-loop", "1", "-framerate", str(fps_in), "-t", str(dur + 0.2), "-i", str(b), "-filter_complex",
                   f"[0:v][1:v]blend=all_expr='A*(1-min(T/{dur},1))+B*min(T/{dur},1)'", "-frames:v", str(n), str(d / "%03d.png"))
            fades[k] = [p.read_bytes() for p in sorted(d.glob("*.png"))]
        return fades[k]
    cmd = ["ffmpeg", "-y", "-v", "error", "-f", "image2pipe", "-framerate", str(fps_in), "-c:v", "png", "-i", "-",
           "-i", str(voice_m4a)]
    maps = ["-map", "0:v", "-map", "1:a"]
    if mode == "soft":
        cmd += ["-i", str(srt_tmp)]; maps += ["-map", "2:s"]
    mi = 3 if mode == "soft" else 2
    cmd += ["-i", str(td / "meta.txt")] + maps + ["-map_metadata", str(mi), "-map_chapters", str(mi),
           "-vf", f"fps={FPS_OUT},format=yuv420p", "-c:v", "libx264", "-preset", "medium",
           "-tune", "stillimage", "-crf", "18", "-c:a", "copy"]
    if mode == "soft":
        cmd += ["-c:s", "mov_text", "-metadata:s:s:0", "language=eng"]
    cmd += ["-shortest", "-movflags", "+faststart", str(out)]
    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    nframes, ti, cur_path, cur_bytes = int(t * fps_in) + 1, 0, None, b""
    for fi in range(nframes):
        now = fi / fps_in
        while ti + 1 < len(timeline) and timeline[ti + 1][0] <= now:
            ti += 1
        if timeline[ti][1] != cur_path:
            cur_path = timeline[ti][1]; cur_bytes = cur_path.read_bytes()
        st, fd = timeline[ti][0], timeline[ti][2]
        if ti > 0 and fd and now < st + fd:
            seq_f = fade_frames(timeline[ti - 1][1], cur_path, fd)
            proc.stdin.write(seq_f[min(int((now - st) * fps_in), len(seq_f) - 1)]); continue
        proc.stdin.write(cur_bytes)
    proc.stdin.close()
    if proc.wait():
        sys.exit("ffmpeg failed")
    tlog("encode (pipe)", t_step)


def plan_segments(timeline, chapter_starts, t_end, fps=FPS_OUT):
    """Cut the timeline into segments, one per logical slide (a [slide:] cue), each a list of pieces on the frame grid:
    ("still", png, n) or ("fade", from_png, to_png, seconds, n). A cue's frame is its chapter's frame round(chapter × fps)
    plus round((cue − chapter) × fps): frame-exact against the chapter times, and a segment's content does not depend on
    where its chapter starts, so an edit in one chapter leaves the other chapters' segments cached (only a chapter's last
    segment can gain or lose one frame)."""
    chs = sorted(chapter_starts) or [0.0]
    F, anchor, ci, starts = [], 0.0, 0, []
    for i, (st, png, fd, kind) in enumerate(timeline):
        new_ch = False
        while ci < len(chs) and chs[ci] <= st + 1e-6:
            anchor = chs[ci]; ci += 1; new_ch = True
        f = round(anchor * fps) + round((st - anchor) * fps)
        F.append(max(f, F[-1] if F else 0))
        if i == 0 or new_ch or kind == "dissolve":
            starts.append(i)
    total = max(F[-1] + 1, math.ceil(t_end * fps))
    F.append(total)
    segs = []
    for si, i0 in enumerate(starts):
        i1 = starts[si + 1] if si + 1 < len(starts) else len(timeline)
        pieces = []
        for i in range(i0, i1):
            n = F[i + 1] - F[i]
            if n <= 0:
                continue
            _, png, fd, _ = timeline[i]
            if fd and i > 0:
                nf = min(n, math.ceil(fd * fps - 1e-9))
                pieces.append(("fade", str(timeline[i - 1][1]), str(png), fd, nf)); n -= nf
            if n > 0:
                if pieces and pieces[-1][0] == "still" and pieces[-1][1] == str(png):
                    pieces[-1] = ("still", str(png), pieces[-1][2] + n)
                else:
                    pieces.append(("still", str(png), n))
        if pieces:
            segs.append((F[i0], pieces))
    return segs, total


def encode_segments(timeline, chapter_starts, t_end, td, encoder, W, H, fps=FPS_OUT):
    segs, total = plan_segments(timeline, chapter_starts, t_end, fps)
    seg_dir = CACHE_ROOT / "segments"; seg_dir.mkdir(parents=True, exist_ok=True)
    enc = ENCODERS[encoder]
    norm = f"scale={W}:{H}:flags=lanczos,setsar=1,format=gbrp"

    def key(pieces):
        desc = [(p[0], *[file_sha(x) if isinstance(x, str) and x.endswith(".png") else x for x in p[1:]]) for p in pieces]
        return hashlib.sha1(json.dumps(["seg-v3", W, H, fps, enc, desc]).encode()).hexdigest()

    def one(job):
        idx, (f0, pieces) = job
        k = key(pieces); dst = seg_dir / f"{k}.mp4"; n = sum(p[-1] for p in pieces)
        if dst.exists():
            os.utime(dst); vlog(f"segment {idx:03d} @{f0 / fps:7.1f}s {n:5d} frames cached"); return dst, True, 0.0
        t0 = time.time()
        args, fl, k_in = ["ffmpeg", "-y", "-v", "error"], [], 0
        for j, p in enumerate(pieces):
            if p[0] == "still":
                args += ["-i", p[1]]
                # convert to yuv420p once, then hold the frame: the colour conversion is not repeated per output frame
                fl.append(f"[{k_in}:v]{norm},format=yuv420p,loop=loop={p[2] - 1}:size=1:start=0,setpts=N/{fps}/TB[p{j}]")
                k_in += 1
            else:
                _, a, b, fd, nf = p
                args += ["-i", a, "-i", b]
                # xfade's linear fade is the same A·(1 − t/d) + B·t/d as the old blend expression (PSNR ≥ 73 dB frame by
                # frame) at 1/28 of the CPU: blend's all_expr is evaluated per pixel
                fl.append(f"[{k_in}:v]{norm},loop=loop={nf - 1}:size=1:start=0,setpts=N/{fps}/TB,fps={fps}[a{j}];"
                          f"[{k_in + 1}:v]{norm},loop=loop={nf - 1}:size=1:start=0,setpts=N/{fps}/TB,fps={fps}[b{j}];"
                          f"[a{j}][b{j}]xfade=transition=fade:duration={fd}:offset=0,trim=end_frame={nf},format=yuv420p[p{j}]")
                k_in += 2
        fl.append("".join(f"[p{j}]" for j in range(len(pieces))) + f"concat=n={len(pieces)}:v=1:a=0,setpts=N/{fps}/TB[v]")
        tmp = td / f"seg-{idx:04d}.mp4"
        args += ["-filter_complex", ";".join(fl), "-map", "[v]", "-frames:v", str(n), "-r", str(fps), *enc,
                 "-threads", os.environ.get("REF_ENC_THREADS", "2"), "-an", str(tmp)]
        # niced, so the audio master (one single-threaded loudnorm, started first) keeps a core while segments encode
        r = subprocess.run(args, capture_output=True, text=True, preexec_fn=lambda: os.nice(10))
        if r.returncode:
            sys.exit(f"segment {idx} failed: {r.stderr[-800:]}")
        cache_put(tmp, dst); tmp.unlink()
        vlog(f"segment {idx:03d} @{f0 / fps:7.1f}s {n:5d} frames encoded in {time.time() - t0:.1f} s")
        return dst, False, time.time() - t0

    with ThreadPoolExecutor(max_workers=JOBS) as ex:
        res = list(ex.map(one, enumerate(segs)))
    hits = sum(1 for _, h, _ in res if h)
    print(f"  encode: {len(segs)} segments, {hits} cached, {len(segs) - hits} encoded ({encoder}, {JOBS} jobs), "
          f"{total} frames = {total / fps:.2f} s", flush=True)
    prune(seg_dir, SEG_CACHE_GB)
    return [p for p, _, _ in res]


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("script"); ap.add_argument("--frames", required=True); ap.add_argument("--out")
    ap.add_argument("--captions", choices=["burn", "soft", "sidecar"], default="burn")
    ap.add_argument("--res", type=int, choices=[1080, 720], default=1080)
    ap.add_argument("--gap-scale", type=float, default=1.0, help="stretch the pauses between lines (1.3 = calmer)")
    ap.add_argument("--max-minutes", type=float, default=0)
    ap.add_argument("--srt", action="store_true", help="burn mode: also write captions/NAME.captions.srt")
    ap.add_argument("--dissolve", type=float, default=0.0, help="crossfade seconds between consecutive slides (0 = hard cut)")
    ap.add_argument("--chapter-gap", type=float, default=None, help="silence before a ## chapter marker (default 1.8)")
    ap.add_argument("--reveal-fade", type=float, default=0.8, help="crossfade seconds for [reveal: NAME]")
    ap.add_argument("--encoder", choices=list(ENCODERS), default="x264", help="videotoolbox: hardware encoder (measured slower and larger on slide video)")
    a = ap.parse_args()
    sc = pathlib.Path(a.script).resolve()
    out = pathlib.Path(a.out).resolve() if a.out else sc.parent / (sc.name.removesuffix(".script.md") + ".mp4")
    build(sc, pathlib.Path(a.frames).resolve(), out, a.captions, a.max_minutes, a.res, a.gap_scale, a.srt,
          a.dissolve, a.chapter_gap, a.reveal_fade, a.encoder)
