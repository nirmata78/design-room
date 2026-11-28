"""Where things are, resolved from this file: no path outside the repository is hard-coded in the kit (issue #5).

The kit lives at <repo>/.claude/skills/reference-solution/kit. Two things live outside the repository by nature and are
found through environment variables, with the conventional defaults:
  KOKORO_PYTHON     the Kokoro TTS virtualenv's python   (default ~/.cache/kokoro-tts/.venv/bin/python)
  AUDIO_SKILL_DIR   the audio-version skill's scripts/   (default: <repo>/.claude/skills/audio-version/scripts if present,
                                                         else ~/.claude/skills/audio-version/scripts) — voices and loudness
Everything else (pdf-kit, its fonts and venv, the KaTeX/highlight.js helpers in theory/video) is inside the repo.
scripts/ref_runtime.sh resolves the same values for shell callers; keep the two in step.
"""
import os, pathlib

KIT = pathlib.Path(__file__).resolve().parent
SKILL = KIT.parent
REPO = KIT.parents[3]
PDFKIT = REPO / "pdf-kit"
PY = PDFKIT / ".venv" / "bin" / "python"                 # Playwright, lxml, pydantic: slides, frames, layout gate, C4
FONTS_CONF = PDFKIT / "fonts" / "fonts.conf"
THEORY_VIDEO = REPO / "theory" / "video"                  # tex.js, hl.js (node) and say.py, the course pronunciation map
C4_SKILL = REPO / ".claude" / "skills" / "c4-structurizr"


def kokoro_python() -> pathlib.Path:
    return pathlib.Path(os.environ.get("KOKORO_PYTHON", pathlib.Path.home() / ".cache/kokoro-tts/.venv/bin/python")).expanduser()


def audio_skill_dir() -> pathlib.Path:
    if os.environ.get("AUDIO_SKILL_DIR"):
        return pathlib.Path(os.environ["AUDIO_SKILL_DIR"]).expanduser()
    local = REPO / ".claude" / "skills" / "audio-version" / "scripts"
    return local if local.exists() else pathlib.Path.home() / ".claude/skills/audio-version/scripts"
