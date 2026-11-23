#!/usr/bin/env python3
"""Run the kit's build_video.build() unchanged, with Kokoro wrapped in a content-addressed cache and the course pronunciation map.
Editing one sentence re-synthesises one line; the shared kit script stays untouched."""
import argparse, hashlib, os, pathlib, sys
os.environ["KOKORO_REEXEC"] = "1"
sys.path.insert(0, str(pathlib.Path.home() / ".claude/skills/slide-video-kit/scripts"))
import numpy as np
import build_video as bv
from say import SAY
CACHE = pathlib.Path.home() / ".cache/sd-course/tts"; CACHE.mkdir(parents=True, exist_ok=True)
RealKokoro = bv.Kokoro
# A beat between sentences inside one spoken line (2026-11-17): a statement gets a short breath, a question or a colon
# that sets up an answer gets a longer one, so the listener can follow a chain of reasoning. Seconds of silence.
import re
BEAT = {".": 0.38, "!": 0.38, "?": 0.75, ":": 0.55}
SPLIT = re.compile(r"(?<=[.?!:])\s+(?=[A-Z0-9\"'])")
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
        h = hashlib.sha1(f"{voice}|{speed}|{lang}|{text}".encode()).hexdigest()
        p = CACHE / f"{h}.npz"
        if p.exists():
            z = np.load(p); return z["a"], int(z["sr"])
        if self.k is None: self.k = RealKokoro(*self.a)
        audio, sr = self.k.create(text, voice=voice, speed=speed, lang=lang)
        tmp = p.with_suffix(f".{os.getpid()}.tmp.npz"); np.savez_compressed(tmp, a=audio.astype(np.float32), sr=sr); tmp.replace(p)
        return audio, sr
bv.Kokoro = Cached
bv.SAY = {**bv.SAY, **SAY}
ap = argparse.ArgumentParser(); ap.add_argument("script"); ap.add_argument("--frames"); ap.add_argument("--out"); ap.add_argument("--dissolve", type=float, default=0.0); ap.add_argument("--chapter-gap", type=float, default=None)
# --captions sidecar (2026-11-21, reference solutions): nothing burned in; NAME.srt + NAME.vtt beside the MP4 for YouTube.
ap.add_argument("--captions", choices=["burn", "soft", "sidecar"], default="burn"); ap.add_argument("--reveal-fade", type=float, default=0.8)
ap.add_argument("--max-minutes", type=float, default=0)
a = ap.parse_args()
bv.build(pathlib.Path(a.script), pathlib.Path(a.frames), pathlib.Path(a.out), a.captions, a.max_minutes, 1080, 1.3, False,
         dissolve=a.dissolve, chapter_gap=a.chapter_gap, reveal_fade=a.reveal_fade)
