#!/usr/bin/env bash
# Rebuild the SD-96 URL shortener reference-solution video (Staff L6/L7, 1080p).
#   build-video.sh            sources -> slides -> frames -> url-shortener-reference.mp4 (+ .srt and .vtt beside it)
#   build-video.sh --frames   stop after the frames
# Slides and script come from src/*.py (one source, so every frame has a cue). Each logical slide is rendered as one
# frame per reveal step (progressive disclosure, 2026-11-21); [reveal: …] crossfades between the steps.
# Captions: --captions sidecar — nothing burned into the picture; upload the .srt (or .vtt) to YouTube as a caption track.
set -euo pipefail
here="$(cd "$(dirname "$0")" && pwd)"; kit="$HOME/.claude/skills/slide-video-kit/scripts"; root="$HOME/Projects/design-room"
python3 "$here/src/stack.py" sync          # ../stack.json → booklet Stage 5 and OUTLINE regions
python3 "$here/diagrams.py" >/dev/null
python3 "$here/src/gen.py"
# layout gate (2026-11-22): overflow, overlapping text, text under the 1080p minimum, over-long code, redraws of one picture.
# Fails before any frame is drawn; the report is $here/layout-report.txt. LAYOUT_CHECK=warn to report only.
lc=0; "$HOME/Projects/design-room/pdf-kit/.venv/bin/python" "$kit/check_layout.py" --html "$here/video-slides.html" \
  --svg-dir "$here/svg" --css-dir "$here" > "$here/layout-report.txt" || lc=$?
tail -1 "$here/layout-report.txt"
[[ $lc == 0 || ${LAYOUT_CHECK:-} == warn ]] || { echo "layout check failed: see $here/layout-report.txt"; exit 1; }
rm -rf "$here/frames"
"$root/pdf-kit/.venv/bin/python" "$kit/render_slides.py" --html "$here/video-slides.html" --prefix v \
  --svg-dir "$here/svg" --css-dir "$here" --out "$here/frames" >/dev/null 2>&1
if [[ ${1:-} == --frames ]]; then exit 0; fi
"$HOME/.cache/kokoro-tts/.venv/bin/python" "$root/theory/video/build_cached.py" "$here/url-shortener-reference.script.md" \
  --frames "$here/frames" --out "$here/url-shortener-reference.mp4" --dissolve 0.3 --chapter-gap 0 \
  --captions sidecar --reveal-fade 0.6 --max-minutes 180
