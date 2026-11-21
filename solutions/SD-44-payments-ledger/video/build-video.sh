#!/usr/bin/env bash
# Rebuild the SD-44 payments-ledger reference-solution video (Staff L6/L7, 1080p).
#   build-video.sh            sources -> slides -> frames -> payments-ledger-reference.mp4
#   build-video.sh --frames   stop after the frames
# The slides and the script are generated together from src/*.py (one source, so every frame has a cue).
set -euo pipefail
here="$(cd "$(dirname "$0")" && pwd)"; kit="$HOME/.claude/skills/slide-video-kit/scripts"
python3 "$here/diagrams.py" >/dev/null
python3 "$here/src/gen.py"
"$HOME/Projects/design-room/pdf-kit/.venv/bin/python" "$kit/render_slides.py" --html "$here/video-slides.html" --prefix v \
  --svg-dir "$here/svg" --css-dir "$here" --out "$here/frames" >/dev/null 2>&1
if [[ ${1:-} == --frames ]]; then exit 0; fi
# Since 2026-11-20: built through the course builder's cached wrapper, which adds sentence beats and the course
# pronunciation map and caches every synthesised line. The pacing beats are written into the script by src/dsl.py.
"$HOME/.cache/kokoro-tts/.venv/bin/python" "$HOME/Projects/design-room/theory/video/build_cached.py" "$here/payments-ledger-reference.script.md" \
  --frames "$here/frames" --out "$here/payments-ledger-reference.mp4" --dissolve 0.3 --chapter-gap 0
