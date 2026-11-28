#!/usr/bin/env python3
"""Run the kit's build_video.build() with Kokoro wrapped in a content-addressed cache and the course pronunciation map.
Editing one sentence re-synthesises one sentence; the shared kit script stays untouched.

Cold cache (issue #7, 2026-11-28): before the build, every sentence the script will speak is checked against the cache and
the missing ones are synthesized by a pool of Kokoro workers (REF_TTS_WORKERS, default 6, each with an equal share of the
cores; measured on an M2 Max: 1.9x a single session). The build itself then only reads the cache.
Cache: $SD_CACHE/tts (default ~/.cache/sd-course/tts). Timing lines: "[time] tts prewarm: N s"; REF_VERBOSE=1 lists misses."""
import argparse, hashlib, os, pathlib, re, sys, time
os.environ["KOKORO_REEXEC"] = "1"
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent)); import paths
sys.path.insert(0, str(paths.THEORY_VIDEO))
import numpy as np
import build_video as bv
from say import SAY

CACHE = pathlib.Path(os.environ.get("SD_CACHE", pathlib.Path.home() / ".cache/sd-course")).expanduser() / "tts"
CACHE.mkdir(parents=True, exist_ok=True)
MODEL, VOICES = str(bv.ba.HOME / "kokoro-v1.0.onnx"), str(bv.ba.HOME / "voices-v1.0.bin")
RealKokoro = bv.Kokoro
# A beat between sentences inside one spoken line (2026-11-17): a statement gets a short breath, a question or a colon
# that sets up an answer gets a longer one, so the listener can follow a chain of reasoning. Seconds of silence.
BEAT = {".": 0.38, "!": 0.38, "?": 0.75, ":": 0.55}
SPLIT = re.compile(r"(?<=[.?!:])\s+(?=[A-Z0-9\"'])")


def cache_path(text, voice, speed, lang):
    return CACHE / (hashlib.sha1(f"{voice}|{speed}|{lang}|{text}".encode()).hexdigest() + ".npz")


def save(p, audio, sr):
    tmp = p.with_suffix(f".{os.getpid()}.tmp.npz"); np.savez_compressed(tmp, a=audio.astype(np.float32), sr=sr); tmp.replace(p)


class Cached:
    def __init__(self, *a): self.a, self.k = a, None
    def create(self, text, voice, speed, lang):
        parts = [x for x in SPLIT.split(text.strip()) if x]
        if len(parts) < 2: return self.one(text, voice, speed, lang)
        out, sr = [], 24000
        for j, x in enumerate(parts):
            a, sr = self.one(x, voice, speed, lang); out.append(a)
            if j + 1 < len(parts): out.append(np.zeros(int(sr * BEAT.get(x.rstrip()[-1:], 0.38)), dtype=np.float32))
        return np.concatenate(out), sr
    def one(self, text, voice, speed, lang):
        p = cache_path(text, voice, speed, lang)
        if p.exists():
            z = np.load(p); return z["a"], int(z["sr"])
        if self.k is None: self.k = RealKokoro(*self.a)
        audio, sr = self.k.create(text, voice=voice, speed=speed, lang=lang)
        save(p, audio, sr)
        return audio, sr


# ── the cold-cache pool ──────────────────────────────────────────────────────────────────────────────────────────────
_K = None


def _init(threads):
    global _K
    import onnxruntime as ort
    from kokoro_onnx import Kokoro
    o = ort.SessionOptions(); o.intra_op_num_threads = threads; o.inter_op_num_threads = 1
    _K = Kokoro.from_session(ort.InferenceSession(MODEL, o, providers=["CPUExecutionProvider"]), VOICES)


def _synth(job):
    text, voice, speed, lang = job
    p = cache_path(text, voice, speed, lang)
    if not p.exists():
        t0 = time.time(); audio, sr = _K.create(text, voice=voice, speed=speed, lang=lang); save(p, audio, sr)
        return time.time() - t0
    return 0.0


def prewarm(script, frames):
    """Synthesize every uncached sentence of the script in parallel; returns (sentences, misses)."""
    t0 = time.time()
    _, voices, _, items, say = bv.parse(script.read_text(encoding="utf-8"), frames)
    jobs, seen = [], set()
    for it in items:
        if it[0] != "line":
            continue
        voice, speed = voices[it[1]]
        text = bv.spoken(it[2], say)
        parts = [x for x in SPLIT.split(text.strip()) if x]
        for x in (parts if len(parts) >= 2 else [text]):
            j = (x, voice, speed, "en-us")
            if j not in seen:
                seen.add(j)
                if not cache_path(*j).exists():
                    jobs.append(j)
    if jobs:
        import multiprocessing as mp
        from concurrent.futures import ProcessPoolExecutor
        workers = min(len(jobs), int(os.environ.get("REF_TTS_WORKERS", "6")))
        threads = max(1, (os.cpu_count() or 4) // max(1, workers))
        print(f"  tts: {len(jobs)} of {len(seen)} sentences to synthesize, {workers} workers × {threads} threads", flush=True)
        jobs.sort(key=lambda j: -len(j[0]))          # longest first: the pool finishes evenly
        with ProcessPoolExecutor(workers, mp_context=mp.get_context("spawn"), initializer=_init, initargs=(threads,)) as ex:
            for n, (j, s) in enumerate(zip(jobs, ex.map(_synth, jobs, chunksize=1)), 1):
                bv.vlog(f"tts {n}/{len(jobs)} {j[1]} {s:.1f} s: {j[0][:70]}")
                if n % 100 == 0:
                    print(f"  tts {n}/{len(jobs)}", flush=True)
    bv.tlog("tts prewarm", t0, sentences=len(seen), synthesized=len(jobs))
    return len(seen), len(jobs)


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("script"); ap.add_argument("--frames"); ap.add_argument("--out")
    ap.add_argument("--dissolve", type=float, default=0.0); ap.add_argument("--chapter-gap", type=float, default=None)
    # --captions sidecar (2026-11-21, reference solutions): nothing burned in; NAME.srt + NAME.vtt beside the MP4 for YouTube.
    ap.add_argument("--captions", choices=["burn", "soft", "sidecar"], default="burn"); ap.add_argument("--reveal-fade", type=float, default=0.8)
    ap.add_argument("--max-minutes", type=float, default=0)
    ap.add_argument("--encoder", choices=list(bv.ENCODERS), default="x264")
    ap.add_argument("--no-prewarm", action="store_true", help="synthesize misses one by one inside the build (the old path)")
    a = ap.parse_args()
    bv.Kokoro = Cached
    bv.SAY = {**bv.SAY, **SAY}
    if not a.no_prewarm:
        prewarm(pathlib.Path(a.script), pathlib.Path(a.frames))
    bv.build(pathlib.Path(a.script), pathlib.Path(a.frames), pathlib.Path(a.out), a.captions, a.max_minutes, 1080, 1.3, False,
             dissolve=a.dissolve, chapter_gap=a.chapter_gap, reveal_fade=a.reveal_fade, encoder=a.encoder)


if __name__ == "__main__":
    main()
