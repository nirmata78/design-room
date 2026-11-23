#!/usr/bin/env bash
# Rebuild the SD-29 device fleet reference-solution video (Staff L6/L7, 1080p).
#   build-video.sh            sources -> slides -> frames -> device-fleet-reference.mp4
#   build-video.sh --frames   stop after the frames
# The slides and the script are generated together from src/*.py (one source, so every frame has a cue).
set -euo pipefail
here="$(cd "$(dirname "$0")" && pwd)"; kit="$HOME/.claude/skills/slide-video-kit/scripts"
python3 "$here/src/stack.py" sync
python3 "$here/diagrams.py" >/dev/null
python3 "$here/src/gen.py"
# layout gate (2026-11-22): overflow, overlapping text, text under the 1080p minimum, over-long code, redraws of one picture.
# Fails before any frame is drawn; the report is $here/layout-report.txt. LAYOUT_CHECK=warn to report only.
lc=0; "$HOME/Projects/design-room/pdf-kit/.venv/bin/python" "$kit/check_layout.py" --html "$here/video-slides.html" \
  --svg-dir "$here/svg" --css-dir "$here" > "$here/layout-report.txt" || lc=$?
tail -1 "$here/layout-report.txt"
[[ $lc == 0 || ${LAYOUT_CHECK:-} == warn ]] || { echo "layout check failed: see $here/layout-report.txt"; exit 1; }
rm -rf "$here/frames"
"$HOME/Projects/design-room/pdf-kit/.venv/bin/python" "$kit/render_slides.py" --html "$here/video-slides.html" --prefix v \
  --svg-dir "$here/svg" --css-dir "$here" --out "$here/frames" >/dev/null 2>&1
if [[ ${1:-} == --frames ]]; then exit 0; fi
# Since 2026-11-20: built through the course builder's cached wrapper, which adds sentence beats and the course
# pronunciation map and caches every synthesised line. The pacing beats are written into the script by src/dsl.py.
"$HOME/.cache/kokoro-tts/.venv/bin/python" "$HOME/Projects/design-room/theory/video/build_cached.py" "$here/device-fleet-reference.script.md" \
  --frames "$here/frames" --out "$here/device-fleet-reference.mp4" --dissolve 0.3 --chapter-gap 0 \
  --captions sidecar --reveal-fade 0.6 --max-minutes 180
