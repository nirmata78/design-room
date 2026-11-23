#!/usr/bin/env bash
# Rebuild the SD-24 distributed-lock reference-solution video (Staff L6/L7, 1080p).
#   build-video.sh            sources -> slides -> frames -> distributed-lock-reference.mp4
#   build-video.sh --frames   stop after the frames
# The slides and the script are generated together from src/*.py (one source, so every frame has a cue).
set -euo pipefail
here="$(cd "$(dirname "$0")" && pwd)"; kit="$HOME/.claude/skills/slide-video-kit/scripts"
python3 "$here/src/stack.py" sync
python3 "$here/diagrams.py" >/dev/null
python3 "$here/src/gen.py"
rm -rf "$here/frames"
"$HOME/Projects/design-room/pdf-kit/.venv/bin/python" "$kit/render_slides.py" --html "$here/video-slides.html" --prefix v \
  --svg-dir "$here/svg" --css-dir "$here" --out "$here/frames" >/dev/null 2>&1
if [[ ${1:-} == --frames ]]; then exit 0; fi
"$kit/build_video.py" "$here/distributed-lock-reference.script.md" --frames "$here/frames" --out "$here/distributed-lock-reference.mp4" \
  --gap-scale 1.3 --max-minutes 180 --dissolve 0.3 --chapter-gap 0 \
  --captions sidecar --reveal-fade 0.6 --max-minutes 180
